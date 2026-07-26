"""The launcher — one supervised process for the whole mind-palace (operational lifecycle).

`start` → preflight (ensure own, verify externals, fail-closed) → record the run pinned to the
git commit → reconcile the corpus (a catch-up vault sync; rebuilds an empty cache) → run the
supervisor + watcher with a **graceful shutdown hook** (SIGTERM/SIGINT → stop claiming new work,
let the in-flight job finish at its boundary — the scheduler is already cooperative — then mark
the run CLEAN). `stop` signals the live run's pid. `status` shows preflight + the last runs.
`reset` is the surgical fresh-start wipe.

Recovery (nervous-system-and-ambassador.md §1): if the *previous* run never marked itself stopped
(crash / kill -9 / power loss), `start` comes up in **recovery mode** — scheduler halted, watcher
off, read-only — and asks the owner to inspect, then `--force` to resume. State itself lives in
the stores/files, so a clean restart just resumes; recovery is the cautious response to an
*unclean* exit, not the normal path.
"""

from __future__ import annotations

import os
import shutil
import signal
import subprocess
import time
from collections.abc import Callable, Sequence
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING, Protocol

from ops.lifecycle.lock import SupervisorLock, SupervisorLockHeld
from ops.lifecycle.preflight import Preflight, run_preflight
from ops.lifecycle.runs import RunLedger, RunRecord, git_state

# snapshot.py is stdlib-only (no store/model imports), so this is a cheap module-level import and
# there is no cycle: snapshot never imports launcher — it takes `_pid_alive` as an argument.
from ops.lifecycle.snapshot import (
    STATUS_WINDOW_MINUTES as _STATUS_WINDOW_MINUTES,
)
from ops.lifecycle.snapshot import (
    build_status,
    humanize_seconds,
    read_queue_stats,
    read_store_stats,
    run_state,
    store_idle_seconds,
)

if TYPE_CHECKING:  # annotations only — the real modules stay lazily imported at runtime
    from config.loader import Config
    from core.ingest.code_corpus import CodeCorpusSync
    from scheduler.router import Flag


class SupervisorLike(Protocol):
    """`scheduler.supervisor.Supervisor`'s real surface here — structural so tests inject a bare
    `_FakeSupervisor` without subclassing the real Supervisor.

    Widened by bp-108 Item 4 from a no-arg `run()` to the real Supervisor's
    `run(*, max_ticks=...) -> int`, because `_serve` now uses BOTH halves of that signature: it
    bounds the drain so supervisory ticks reach a job boundary, and it reads the returned dispatch
    count to decide whether to sleep. A Protocol is only as wide as its actual call sites — the
    call site grew, so this grew with it."""

    def run(self, *, max_ticks: int | None = None) -> int: ...


class WatcherLike(Protocol):
    """`core.ingest.watch.DirectoryWatcher`'s real surface here (structural, same reasoning).
    `start()` narrowed to no-arg (the only call shape here: iterating `c.watchers` and calling
    `w.start()`/`w.stop()`)."""

    def start(self) -> object: ...
    def stop(self) -> None: ...


class SweepLike(Protocol):
    """`scheduler.queue.OrphanSweep`'s surface here — structural, so `ops` keeps no import-time
    dependency on `scheduler` (the QueueLike pattern, bp-101/finding-0177)."""

    def render(self) -> str: ...


class QueueLike(Protocol):
    """`scheduler.queue.JobQueue`'s real surface here (`.close()` and, since bp-101/bp-103
    integration, `.sweep_orphans()` are called through `Components.queue` — `build_components`
    calls `.depth()` on its own `JobQueue` directly)."""

    def close(self) -> None: ...
    def sweep_orphans(self, active_run_id: int) -> SweepLike: ...  # bp-101 / findings 0173, 0177


class ChildLike(Protocol):
    """`ops.lifecycle.children.Child`'s real surface here — structural so
    `tests/integration/test_lifecycle.py`'s bare `_FakeChild` satisfies it without subclassing."""

    name: str

    @property
    def pid(self) -> int | None: ...  # read-only on the real Child (a computed property)

    def start(self) -> None: ...
    def alive(self) -> bool: ...
    def stop(self) -> None: ...

# Data files/dirs the reset wipe must NEVER touch: the production Vault Raft store, the run +
# self-mod ledgers, telemetry history, the live backup staging, and logs. The corpus targets are
# computed from cfg.paths; this guard is defense-in-depth so a path mistake can't nuke Vault.
_RESET_GUARD = ("vault", "runs.sqlite", "selfmod_ledger.sqlite", "telemetry.duckdb",
                "code_snapshots.sqlite",
                # Observation worldview HISTORY (bp-018, dn-self-sensing §2.5 split):
                # current READINGS are corpus-side and wiped (code_observations.sqlite
                # stays a reset target — rebuilt by re-projection from git); superseded
                # generations do NOT rebuild (their interpreters no longer exist at HEAD).
                "observation_history.sqlite",
                "backup-staging", "logs")

# Default cadence for the trough housekeeping passes (dream + curate). They only actually run
# when the foreground gate is clear (the supervisor's HEAVY_TIERS check), so this is a ceiling.
_HOUSEKEEPING_INTERVAL_S = 6 * 3600

# K — the drain bound (bp-108 Item 4 / §11). Public and module-level because `scripts/watch.py`
# builds its own supervisor loop and must use the SAME bound: two serve loops with two different
# duty cycles would be two answers to one question.
DEFAULT_DRAIN_MAX_TICKS = 64


def _pid_alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)        # signal 0 = liveness probe, delivers nothing
    except ProcessLookupError:
        return False           # no such process
    except PermissionError:
        return True            # exists but owned by another user
    return True


# `started_at` is written at whole-second resolution (`runs.py:106`, timespec="seconds"), so a
# supervisor that opened its row 0.3 s after spawning reads as having been created up to a second
# AFTER it. 5 s absorbs that truncation plus clock jitter; a genuine pid recycle needs the pid
# counter to wrap (~99k spawns) and is therefore never seconds away from the row it lands on.
_CLOCK_SLACK_S = 5.0


def _process_identity(pid: int) -> tuple[float | None, str | None]:
    """`(create_time_epoch, interpreter_name)` for `pid` — either component None when unreadable.

    `interpreter_name` is the basename of the binary the process is actually EXECUTING, which is
    the string D2 asks *"is this a Python interpreter?"* of. It is deliberately not "the process's
    name" — see the `exe()`/`name()` warrant below.

    warrant(finding-0198): this is a raw `psutil` touch outside `core/typedshims/psutil.py`, the
    ONE module that is supposed to own it (type-system-as-core-audit §2.5). The shim is not in
    bp-105's `write_scope`, so rather than route around the boundary the probe is quarantined here
    behind a single narrow function and the move is recorded as a hand-off on finding-0198.

    Never raises. Unreadable is reported as None, which `_supervisor_alive` treats as ambiguity —
    and ambiguity REFUSES, per the owner ruling on finding-0186."""
    try:
        import psutil  # type: ignore[import-untyped]  # noqa: PLC0415  # warrant: see finding-0198

        proc = psutil.Process(pid)
    except Exception:  # noqa: BLE001 — an unreadable process is ambiguity, never a crash
        return (None, None)
    created: float | None = None
    interpreter: str | None = None
    try:
        created = float(proc.create_time())
    except Exception:  # noqa: BLE001
        created = None
    try:
        # `name()` and not `cmdline()`: on macOS `cmdline()` raises AccessDenied for a foreign
        # owner (measured against pid 1) while `name()`/`exe()` read fine — and a foreign owner is
        # exactly the deployed case, the daemon running as the `ouroboros` principal.
        #
        # ⚑ warrant(finding-0211): and `exe()` in preference to BOTH. `name()` reports the
        # comm/argv0 basename, which depends on HOW the interpreter was invoked — under
        # `uv run pytest` on Linux it resolves to the console script, containing no "python", so
        # D2 disproved a live interpreter and CI was red for 55 consecutive pushes while the same
        # tests passed on macOS (`name()` -> 'Python'). `exe()` reports the binary actually
        # executed, which is the question D2 means to ask. The BASENAME and not the whole path:
        # an interpreter living under `~/python-projects/` would otherwise make every binary on
        # that path read as one, and D2 could never fire.
        interpreter = Path(str(proc.exe())).name or None
    except Exception:  # noqa: BLE001
        interpreter = None
    if interpreter is None:
        # `name()` is retained as the FALLBACK, and it is load-bearing rather than defensive: on
        # Linux `/proc/<pid>/exe` is unreadable for a foreign owner while `name()` reads fine, so
        # without it a stale pid recycled onto `systemd` would leave D2 unavailable, the verdict
        # ambiguous, and `start` refusing forever — finding-0186's brick trap, reopened.
        try:
            interpreter = str(proc.name())
        except Exception:  # noqa: BLE001
            interpreter = None
    return (created, interpreter)


def _supervisor_alive(run: RunRecord, *,
                      pid_alive: Callable[[int], bool] = _pid_alive,
                      identity: Callable[[int], tuple[float | None, str | None]]
                      = _process_identity) -> bool:
    """True unless `run.pid`'s current occupant is POSITIVELY DISPROVEN to be that run's supervisor.

    `_pid_alive` alone is pid-EXISTENCE, and it deliberately reports a foreign owner as ALIVE
    (`test_pid_alive_treats_a_foreign_owner_as_ALIVE`). After an unclean exit the OS may recycle
    the dead supervisor's pid to an unrelated process; a fail-closed `start` keyed on existence
    alone would then refuse FOREVER — under launchd `KeepAlive`, a self-inflicted brick, with
    `--force` (the very flag being closed) as the only escape.

    So liveness is identity-checked. The owner's ruling (finding-0186, 2026-07-25) fixes the
    default — *"on ambiguity, refuse"* — and the carve-out fires only on a positive disproof:

      **D1 — the process postdates the row.** A process created after `started_at` cannot have
      written a row that already existed. `start()` stamps `pid=os.getpid()` from inside itself,
      so the genuine supervisor always predates its own row (finding-0198 corrects the plan's
      inverted statement of this, which would have built a guard that never fires).

      **D2 — the process is not a Python interpreter.** The supervisor always is: the plist runs
      `uv run scripts/palace.py start` and the pid recorded is the python child's. D1 cannot clear
      a stale row whose pid wrapped onto a long-lived process (`launchd`, `systemd`) — such a
      process *predates* the row, so D1 stays silent and the system bricks on the very case the
      ruling's trap section is about. D2 is what closes it, and it is uptime-independent.
      ⚑ warrant(finding-0211): the premise stands, the original PROBE was wrong. `name()` reports
      an invocation-dependent basename (a console script under `uv run` on Linux) and D2 read it
      as "not an interpreter" against a live one; `_process_identity` therefore reads `exe()`
      first — the binary actually executed — and falls back to `name()` only when it is
      unreadable. `cmdline()` stays rejected for the AccessDenied reason recorded there.

    Anything else — AccessDenied, a vanished process, an unparseable `started_at`, a python
    process created before the row — refuses. Refusing wrongly is recoverable with `palace stop`;
    starting wrongly rewrites a live worker's rows (finding-0186).

    Both probes are INJECTED, the same discipline `snapshot.run_state` applies to `pid_alive`: it
    keeps the decision pure and lets a test pin a process shape the host cannot be made to have
    (a recycled pid, a denied `create_time`) without patching the OS.
    """
    if not pid_alive(run.pid):
        return False
    created, interpreter = identity(run.pid)
    if created is not None:
        try:
            opened = datetime.fromisoformat(run.started_at).replace(tzinfo=UTC).timestamp()
        except ValueError:
            opened = None                      # unparseable timestamp ⇒ D1 unavailable ⇒ ambiguous
        if opened is not None and created > opened + _CLOCK_SLACK_S:
            return False                       # D1: it postdates the row it would have written
    if interpreter is not None and "python" not in interpreter.lower():
        return False                           # D2: the supervisor is always a python process
    return True                                # not disproven ⇒ refuse (the ruling)


def _git_branch(repo_root: Path) -> str:
    """Current branch name, '' on detached HEAD or non-git (deploy refuses either)."""
    r = subprocess.run(["git", "-C", str(repo_root), "symbolic-ref", "--short", "-q", "HEAD"],
                       capture_output=True, text=True)
    return r.stdout.strip()


@dataclass(frozen=True)
class LaunchDomain:
    """Which launchd domain a Launcher drives — the dn-plane-principals §3.1/§3.2 axis.

    DEFAULT = the per-user GUI LaunchAgent (`gui/$UID`): today's path, byte-identical — no sudo,
    plist in `~/Library/LaunchAgents/`, control target `gui/$UID/<label>`. The **system-daemon**
    variant runs the palace as the `ouroboros` core principal under a LaunchDaemon
    (`UserName ouroboros`): control targets `system/<label>`, goes through `sudo launchctl`, and
    the plist installs to `/Library/LaunchDaemons/`. The domain is the ONLY thing that differs
    between the two — the `launchctl` runner stays injectable, so tests drive both with a fake and
    no real launchd domain is touched (the migration itself is owner-run, dn-plane-principals §3.5).
    """

    kind: str = "gui"   # "gui" | "system"

    @classmethod
    def gui(cls) -> LaunchDomain:
        return cls(kind="gui")

    @classmethod
    def system(cls) -> LaunchDomain:
        return cls(kind="system")

    @property
    def needs_sudo(self) -> bool:
        """System-domain control requires `sudo launchctl` (note §3.2; risk (c)); gui does not."""
        return self.kind == "system"

    def target(self, label: str) -> str:
        """The service target for `bootout`/`print` (domain + label): `system/<label>` or
        `gui/$UID/<label>`."""
        return f"system/{label}" if self.kind == "system" else f"gui/{os.getuid()}/{label}"

    def bootstrap_domain(self) -> str:
        """The DOMAIN argument for `bootstrap` (no label): `system` or `gui/$UID`."""
        return "system" if self.kind == "system" else f"gui/{os.getuid()}"

    def launchctl_argv(self, args: list[str]) -> list[str]:
        """The full argv to execute — `sudo` prepended ONLY for the system domain. The gui form is
        byte-identical to the historical `["launchctl", *args]`."""
        prefix = ["sudo", "launchctl"] if self.needs_sudo else ["launchctl"]
        return [*prefix, *args]

    def installed_plist(self) -> Path:
        """Where the installed plist lives: `/Library/LaunchDaemons/` (system — needs root to
        write, an owner-run migration step) or `~/Library/LaunchAgents/` (gui). The filename keeps
        the label (`com.mind-palace.palace.plist`) either way."""
        if self.kind == "system":
            return Path("/Library/LaunchDaemons/com.mind-palace.palace.plist")
        return _default_installed_agent_plist()

    def repo_plist(self, repo_root: Path) -> Path:
        """The committed SOURCE plist for this domain: the daemon variant (`UserName ouroboros`)
        for system, the LaunchAgent for gui."""
        name = ("com.mind-palace.palace-daemon.plist" if self.kind == "system"
                else "com.mind-palace.palace.plist")
        return repo_root / "ops/lifecycle" / name


def _default_installed_agent_plist() -> Path:
    """The gui LaunchAgent install path — the historical `installed_plist` default (unchanged)."""
    return Path.home() / "Library/LaunchAgents/com.mind-palace.palace.plist"


def _launchd_managed(label: str, domain: LaunchDomain | None = None) -> bool:
    """Is the palace agent bootstrapped in its launchd domain? Defaults to the gui domain —
    byte-identical to the historical `launchctl print gui/$UID/<label>`."""
    domain = domain or LaunchDomain.gui()
    r = subprocess.run(domain.launchctl_argv(["print", domain.target(label)]),
                       capture_output=True)
    return r.returncode == 0


def _launchd_cycle(label: str, repo_plist: Path, installed: Path,
                   domain: LaunchDomain | None = None) -> None:
    """The infra half of deploy: bootout → install the repo plist → bootstrap. Domain-aware
    (risk (a)): the system domain boots out `system/<label>` and bootstraps the `system` domain
    via `sudo launchctl`, and `installed` follows the domain. Defaults to the gui domain
    (unchanged). NB for the system daemon the `shutil.copy2` into `/Library/LaunchDaemons/` needs
    root — this cycle therefore runs under the owner's privilege at migration time, never
    ambiently (the default Launcher is gui, so this path is inert until the daemon move)."""
    domain = domain or LaunchDomain.gui()
    subprocess.run(domain.launchctl_argv(["bootout", domain.target(label)]), check=False)
    shutil.copy2(repo_plist, installed)
    subprocess.run(domain.launchctl_argv(["bootstrap", domain.bootstrap_domain(), str(installed)]),
                   check=True)


def _run_launchctl(argv: list[str]) -> subprocess.CompletedProcess[str]:
    """Run a `launchctl` subcommand in the GUI domain, capturing output — the down/up/restart
    control seam's DEFAULT runner. Injectable on the Launcher so tests drive bootout/bootstrap
    with a fake; a system-domain Launcher swaps in `_run_launchctl_sudo` (see `__post_init__`)."""
    return subprocess.run(["launchctl", *argv], capture_output=True, text=True)


def _run_launchctl_sudo(argv: list[str]) -> subprocess.CompletedProcess[str]:
    """The system-domain control runner: `sudo launchctl <subcommand>` (note §3.2). Bound as the
    Launcher's default runner when it is constructed with the system domain and no explicit
    runner override."""
    return subprocess.run(["sudo", "launchctl", *argv], capture_output=True, text=True)


@dataclass
class Components:
    """What `serve` drives. Injectable so tests exercise the lifecycle without models."""

    supervisor: SupervisorLike
    # Sequence (covariant) so a concrete list[DirectoryWatcher] conforms; one per watched dir:
    # the vault + the chat transcripts (bp-069). Only iterated (start/stop), never mutated.
    watchers: Sequence[WatcherLike]
    queue: QueueLike
    enqueue_catchup: Callable[[], None] = lambda: None     # reconcile corpus on start
    enqueue_housekeeping: Callable[[], None] = lambda: None  # dream + curate pass
    health_check: Callable[[], list[Flag]] = lambda: []    # OS-health sense (returns crossed flags)
    # The thin-master/child model: separate processes palace spawns + drains. DORMANT since the
    # edge monitor was removed (bp-030 Item 2) — kept as the seam a future dashboard redo re-wires.
    children: list[ChildLike] = field(default_factory=list)
    # Periodic status-snapshot hook (its only consumer, the edge monitor, is gone — DORMANT no-op).
    snapshot: Callable[[object, list[Flag]], None] = lambda _run, _flags: None


def _code_backfill_incomplete(cfg: Config, code_driver: CodeCorpusSync) -> bool:
    """The catch-up incompleteness probe (dn-temporal-code-corpus §3, bp-099): is the store missing
    any ledger code version? Compares DISTINCT `(path, blob_sha)` versions on BOTH sides — the
    store's embedded code versions vs the ledger's `ledger_versions` — so a COMPLETE store is
    exactly equal and the probe enqueues NOTHING (no loop). (§6's shorthand `distinct digests <
    distinct versions` would false-positive forever — 1,472 distinct blobs < 1,542 distinct
    (path,blob) pairs even when complete; the falsifier forbids that loop, so the probe is
    like-to-like — finding-0166.) Cheap scans, no embed. A missing ledger → not incomplete."""
    from core.kernel.provenance import Provenance
    from ops.code_lineage import ledger_versions
    from ops.code_snapshot import open_snapshot_db

    store_versions = {(str(r["source_path"]), str(r["digest"]))
                      for r in code_driver.store.all_rows(provenances={Provenance.CODE})}
    db = open_snapshot_db(cfg.paths.data_dir / "code_snapshots.sqlite")
    try:
        ledger = set(ledger_versions(db))
    finally:
        db.close()
    return len(store_versions) < len(ledger)


def build_components(cfg: Config) -> Components:
    """Wire the full daemon: vault_sync (+watcher), the delegating Ambassador inbox, the
    delegated-task worker, and the trough dream/curate handlers — all on one supervisor."""
    from agents.ambassador import build_ambassador
    from core.chat_events import build_chat_event_projector
    from core.curator import build_curator
    from core.dreaming import build_dreamer
    from core.ingest.code_corpus import build_code_corpus_sync
    from core.ingest.sync import build_vault_sync
    from core.integrator import build_integrator
    from core.interface import CoreInbox
    from core.librarian import build_librarian
    from core.models import Registry, TwoSlotLoader
    from core.models.ollama_client import OllamaClient
    from core.research.airlock import build_airlock
    from core.stores.telemetry import open_store
    from core.typedshims import psutil
    from ops.chat_sensor import build_chat_sensor
    from ops.gate import HumanGate
    from scheduler.chat_sync import (
        CHAT_SYNC_KIND,
        build_chat_watcher,
        chat_sync_handler,
        enqueue_chat_sync,
    )
    from scheduler.code_sync import (
        CODE_BACKFILL_KIND,
        CODE_SYNC_KIND,
        code_backfill_handler,
        code_sync_handler,
        enqueue_code_backfill,
        enqueue_code_sync,
    )
    from scheduler.cron import (
        CHAT_EVENTS_KIND,
        INTEGRATE_KIND,
        chat_events_handler,
        cron_handlers,
        enqueue_chat_events,
        enqueue_curate,
        enqueue_dream,
        enqueue_integrate,
        integrate_handler,
        research_handler,
    )
    from scheduler.interface import (
        AMBASSADOR_KIND,
        AMBASSADOR_TASK_KIND,
        ambassador_inbox_handler,
        ambassador_task_handler,
        build_task_delegation,
    )
    from scheduler.queue import JobQueue
    from scheduler.research import RESEARCH_KIND
    from scheduler.router import Router, Watchdog
    from scheduler.supervisor import Supervisor
    from scheduler.vault_sync import (
        VAULT_SYNC_KIND,
        build_vault_watcher,
        enqueue_vault_sync,
        vault_sync_handler,
    )

    queue = JobQueue(cfg.paths.data_dir / "queue.sqlite")
    router = Router(cfg)
    loader = TwoSlotLoader(config=cfg, client=OllamaClient(cfg.ollama), registry=Registry(cfg))

    # The OS-health agent: the supervisor records its own vitals (queue depth, model-load time);
    # here we also feed system memory so the deterministic Watchdog can raise a low-headroom flag
    # (sense + report; the loader already REFUSES ceiling-breaching loads — Invariant 8).
    tstore = open_store(cfg)
    telemetry = tstore.writer()
    watchdog = Watchdog(tstore.reader())

    def health_check() -> list[Flag]:
        avail_gb = psutil.virtual_memory().available / (1024 ** 3)
        telemetry.record_vital("mem.available_gb", round(avail_gb, 2), unit="GB", source="os")
        return watchdog.check()

    gate = HumanGate()
    # Build the task librarian first: it doubles as the delegate's `research_criteria`
    # (de-identify) seam, so a research-shaped TASK routes to the airlock instead of the general
    # answer path (bp-028 §16 / dn-external-grounding §2.5). Its embedder + store also drive the
    # inside-the-walls literature ranking; the airlock is the core-side one-way diode.
    task_librarian = build_librarian(cfg)
    airlock = build_airlock(cfg)
    delegate, pending = build_task_delegation(queue, router, gate=gate, librarian=task_librarian)
    ambassador = build_ambassador(cfg, delegate=delegate, pending_results=pending)
    inbox = CoreInbox(handoff=cfg.interface.handoff_dir, handler=ambassador.handler)

    code_driver = build_code_corpus_sync(cfg)   # one sync driver for both code_sync + code_backfill
    code_snapshots_db = cfg.paths.data_dir / "code_snapshots.sqlite"

    handlers = {
        VAULT_SYNC_KIND: vault_sync_handler(build_vault_sync(cfg)),
        # The chat sensor (bp-063) wired to RUN (bp-068): a model-less OBSERVED-only ingest of the
        # local Claude Code transcripts, same species as vault_sync. build_chat_sensor is bp-063's
        # (reused, not re-declared — finding-0108); the scheduler side is KIND + handler + enqueue.
        CHAT_SYNC_KIND: chat_sync_handler(build_chat_sensor(cfg)),
        # The code embed lane (bp-092/CI-1) wired to RUN (bp-098): a model-less OBSERVED ingest of
        # the HEAD `.py` blobs, same species as vault_sync/chat_sync (pinned tier, BACKGROUND). The
        # handler is registered unconditionally (like vault_sync it eagerly opens the vector store —
        # no new startup cost beyond a git rev-parse); the daemon only ENQUEUES it when
        # `code_ingest.enabled` (see _housekeeping). The deliberate seed is `palace code-seed`.
        CODE_SYNC_KIND: code_sync_handler(code_driver),
        # The history backfill (bp-099 / dn-temporal-code-corpus D1/D4): embeds every ledger
        # version + captures the first-parent commit diffs (the supersession-chain substrate).
        # Registered unconditionally (same species as code_sync); ENQUEUED only by the catch-up
        # incompleteness probe or the deliberate `palace code-backfill`. Idempotent, BACKGROUND.
        CODE_BACKFILL_KIND: code_backfill_handler(code_driver, code_snapshots_db, code_driver.repo),
        # The L1 action-log projector (bp-069 Item 3): the sensor's DELAYED rate, model-less like
        # chat_sync. Re-extracts WHAT was performed (typed events, structural refs) from the raw
        # transcripts at housekeeping cadence, incrementally by transcript_digest.
        CHAT_EVENTS_KIND: chat_events_handler(build_chat_event_projector(cfg),
                                              max_per_pass=cfg.chat.events_max_per_pass),
        # The chat↔code↔doc integrator (bp-071): the first full integrator role — model-less like
        # chat_events, one tick behind it (it reads the L1 that pass produces). Resolves L1 refs
        # against the commit ledger into witnessed C-fiber proven edges; pinned, trough cadence.
        INTEGRATE_KIND: integrate_handler(build_integrator(cfg),
                                          max_per_pass=cfg.chat.integrate_max_per_pass),
        AMBASSADOR_KIND: ambassador_inbox_handler(inbox),
        AMBASSADOR_TASK_KIND: ambassador_task_handler(task_librarian),
        RESEARCH_KIND: research_handler(airlock, task_librarian.embedder, task_librarian.store),
        **cron_handlers(build_dreamer(cfg), build_curator(cfg)),
    }
    supervisor = Supervisor(queue=queue, loader=loader, handlers=handlers, telemetry=telemetry)
    # One watcher per watched dir: the owner's vault + the Claude Code transcripts (bp-069). Both
    # are generic DirectoryWatchers; on a change each enqueues its own model-less background job.
    watchers = [build_vault_watcher(queue, router, cfg), build_chat_watcher(queue, router, cfg)]

    def _housekeeping() -> None:
        enqueue_dream(queue, router)
        enqueue_curate(queue, router)
        enqueue_chat_sync(queue, router)    # periodic chat ingest (growth-aware, bp-068/069)
        enqueue_chat_events(queue, router)  # L1 action-log projection — the delayed rate (bp-069)
        enqueue_integrate(queue, router)    # C-fiber proven edges from L1 + the ledger (bp-071)
        if cfg.code_ingest.enabled:         # code embed lane, opt-in (bp-098 / note §2.7):
            enqueue_code_sync(queue, router)  # INCREMENTAL only; the heavy SEED is `code-seed`

    def _catchup() -> None:
        enqueue_vault_sync(queue, router)   # reconcile the corpus; the Job return is discarded
        enqueue_chat_sync(queue, router)    # startup backfill of every closed chat session (bp-068)
        if cfg.code_ingest.enabled and _code_backfill_incomplete(cfg, code_driver):
            enqueue_code_backfill(queue, router)   # history not yet fully embedded (bp-099 D1)

    # The edge monitor (a supervised child PROCESS fed by a status-snapshot JSON, Invariant 2) was
    # removed with bp-030 Item 2 — it never worked and was `enabled=false`. Its data source
    # (`snapshot.build_status`) is retained and now feeds `status` directly (Item 3); the child +
    # snapshot SEAMS on Components stay dormant (their defaults: no children, no-op snapshot) for
    # the future dashboard redo.
    return Components(
        supervisor=supervisor, watchers=watchers, queue=queue,
        enqueue_catchup=_catchup,
        enqueue_housekeeping=_housekeeping,
        health_check=health_check,
    )


@dataclass
class Launcher:
    cfg: Config
    runs: RunLedger
    repo_root: Path
    components_factory: Callable[[Config], Components] = build_components
    preflight_fn: Callable[[Config], Preflight] = run_preflight   # injectable for tests
    tick_seconds: float = 1.0
    # K — how many jobs one `supervisor.run()` may dispatch before control returns to the serve
    # loop (bp-108 §11, default 64). NOT the same thing as `start(max_ticks=…)`, which bounds the
    # OUTER loop's iterations and is the test seam; conflating the two would make a test's
    # `max_ticks=1` silently mean "dispatch one job", which it does not.
    #
    # A field rather than config: `core/kernel/config/loader.py` is schema'd and drops unknown
    # sections, so a `[scheduler]` key would be inert today (bp-102 / finding-0174), and the
    # schema change belongs to bp-110, which owns that file. Re-entry for the value itself is
    # §11's: if a single job routinely exceeds the tick budget, a count bound stops helping and
    # the note's time-boxed drain becomes the right fix (it needs `scheduler/supervisor.py`,
    # deliberately out of this plan's scope).
    drain_max_ticks: int = DEFAULT_DRAIN_MAX_TICKS
    housekeeping_interval_s: float = _HOUSEKEEPING_INTERVAL_S
    health_interval_s: float = 60.0                            # OS-health sense cadence
    snapshot_interval_s: float = 5.0                           # edge-monitor snapshot cadence
    on_shutdown: Callable[[bool], None] | None = None   # ASG-style lifecycle hook (e.g. snapshot)
    # deploy (the promotion gate): the ratchet command, the successor-wait budget, and the
    # launchd label — all injectable for tests.
    gate_cmd: tuple[str, ...] = (
        "uv", "run", "pytest", "-q",
        "-m", "not live and not podman and not needs_vault and not needs_restic",
        # finding-0105 (owner decision A, 2026-07-18): deselect ONLY the one intentional-red ratchet
        # (test_core_self_containment) so the deploy gate enforces everything else throughout the
        # self-containment cleanup and regains full strength automatically when the ratchet reaches
        # zero (the node stops existing / the assertion goes green either way). Surgical, not
        # blunt: --skip-tests drops the WHOLE gate, and an xfail/skip on the test would weaken the
        # ratchet in the full suite too. The other tests in that file (scanner guards) still run,
        # so a REAL scanner/import regression still blocks the gate.
        "--deselect", "tests/unit/test_core_self_containment.py::test_core_imports_nothing_outside_core",  # noqa: E501
    )
    # remote half of the gate + release-on-deploy (ops/ci_witness.py). Subprocesses, not
    # imports: the witness talks to api.github.com and must stay outside this sealed process.
    ci_check_cmd: tuple[str, ...] | None = ("uv", "run", "scripts/ci_witness.py", "check")
    ci_release_cmd: tuple[str, ...] | None = ("uv", "run", "scripts/ci_witness.py", "release")
    deploy_wait_s: float = 60.0
    deploy_poll_s: float = 0.5
    launchd_label: str = "com.mind-palace.palace"
    # Which launchd domain this Launcher drives (dn-plane-principals §3.1/§3.2). DEFAULT = gui —
    # every control incantation, the installed-plist path, and the drift check stay byte-identical
    # to today. `LaunchDomain.system()` selects the `ouroboros` LaunchDaemon (sudo + system/<label>
    # + /Library/LaunchDaemons); the migration that makes it live is owner-run (§3.5).
    domain: LaunchDomain = field(default_factory=LaunchDomain.gui)
    # down/up/restart (KeepAlive-aware maintenance control, finding-0066): the launchctl runner
    # and the installed plist path — injectable so tests drive control with a fake. The runner
    # default is gui (`launchctl …`); a system-domain Launcher swaps in the `sudo launchctl` runner
    # in `__post_init__` unless the caller injected one. `installed_plist` follows the domain
    # unless set explicitly (risk (a)).
    launchctl: Callable[[list[str]], subprocess.CompletedProcess[str]] = _run_launchctl
    installed_plist: Path = field(default_factory=_default_installed_agent_plist)
    # How long `down` OBSERVES the process after the bootout before it reports (bp-102 Item 3 /
    # finding-0171). This is a VERIFICATION window, not an escalation deadline: nothing is
    # signalled again and nothing is killed when it elapses — the command simply stops claiming a
    # state it has not seen. A graceful drain that ends at a job boundary normally completes well
    # inside it; a wedged job never will, and that is the fact `down` must print.
    stop_verify_s: float = 5.0
    stop_poll_s: float = 0.25
    # W for the status rate block. Field, not config: `core/config/loader.py` is schema'd and
    # drops unknown sections, so a `[status]` key would be inert (bp-102 §11 / finding-0174).
    status_window_minutes: float = _STATUS_WINDOW_MINUTES
    _stopping: bool = field(default=False, init=False)
    _run_id: int | None = field(default=None, init=False)
    _run: RunRecord | None = field(default=None, init=False)  # the active RunRecord (for snapshots)
    _components: Components | None = field(default=None, init=False)
    # The supervisor lock, held for the whole serve lifetime (§2.6). Not injectable and not
    # configurable on purpose: its path is derived from `cfg.paths.data_dir` so it is always
    # beside the queue it guards, and a mutual-exclusion guarantee with a seam for tests to
    # disable it is not a guarantee. Tests get isolation from `data_dir` being a tmp_path.
    _lock: SupervisorLock | None = field(default=None, init=False)

    def __post_init__(self) -> None:
        # A system-domain Launcher controls launchd via `sudo launchctl` and installs its plist to
        # /Library/LaunchDaemons (note §3.2, risk (a)). Apply those ONLY when the caller did not
        # override the field — so an injected fake runner (tests) and an explicit installed_plist
        # are always honored, and the gui default path is untouched.
        if self.domain.needs_sudo:
            if self.launchctl is _run_launchctl:
                self.launchctl = _run_launchctl_sudo
            if self.installed_plist == _default_installed_agent_plist():
                self.installed_plist = self.domain.installed_plist()

    # --- start ------------------------------------------------------------------------------
    def start(self, *, force: bool = False, max_ticks: int | None = None) -> int:
        # SINGLE-INSTANCE **DIAGNOSTIC** — first, and NOT bypassable by --force (finding-0186,
        # owner ruling 2026-07-25: "start should refuse outright if there is any potential for an
        # issue to occur... the system deeming an unrunnable state"). `--force` overrides
        # *preflight*, not *safety*. A second supervisor over a live one is not contention:
        # `sweep_orphans` reclaims the live run's in-flight rows, so the first worker's job is
        # re-queued (double execution) or written FAILED with a fabricated cause under it (a lying
        # ledger).
        #
        # ⚑ This gate is NO LONGER what enforces exclusivity — the supervisor lock below is
        # (dn-supervision-and-liveness §2.6, bp-108). Kept, and deliberately kept FIRST, because
        # the two answer different questions: the lock is held-or-not and can only say "no", while
        # this gate can say WHICH run is live and with what pid. Guarantee and diagnostic. On the
        # note's enforcement ladder the gate is tier 5 (a runtime probe someone must remember to
        # make, with a check-then-act window between the probe and the start) and the lock is
        # tier 3 (a kernel fact, acquired atomically). Deleting the gate would lose the
        # explanation, not the exclusion — so it stays.
        #
        # Ahead of preflight deliberately — an unrunnable state should not first cost the operator
        # preflight's uncosted 120 s Ollama probe (finding-0195). Same shape as `reset()`'s guard
        # (:1124), with liveness identity-checked so a recycled pid cannot brick start forever.
        prev = self.runs.last()
        if prev is not None and prev.active and _supervisor_alive(prev):
            print(f"refusing to start — run #{prev.id} (pid {prev.pid}) is live. "
                  "`palace stop` first. (--force does not bypass this: a second supervisor over a "
                  "live one rewrites its in-flight jobs — finding-0186.)")
            return 1

        # THE GUARANTEE — the supervisor role is kernel-exclusive from here on (§2.6). Acquired
        # before `sweep_orphans` (the first thing that can rewrite another claimant's rows) and
        # before preflight (same 120 s argument as the gate). Unconditional and unflagged: §4 of
        # the note is explicit that "a mutual-exclusion guarantee behind a flag is a
        # contradiction", so there is no `--force` path past this and no config key to disable it.
        #
        # It catches precisely what the gate above cannot: a claimant with no active run row at
        # all (`scripts/watch.py` — finding-0186's open half), and the gate's own check-then-act
        # window. Recovery mode holds it too — a recovery run is a live supervisor.
        self._lock = SupervisorLock(self.cfg.paths.data_dir / "supervisor.lock")
        try:
            self._lock.acquire()
        except SupervisorLockHeld:
            path, self._lock = self._lock.path, None
            print(f"refusing to start — another process holds the supervisor lock ({path}). "
                  "Something is already supervising this data dir. `palace stop` first, or find "
                  "the holder with `lsof` on that path. (--force does not bypass this either: "
                  "exclusivity is not a preference — dn-supervision-and-liveness §2.6.)")
            return 1

        try:
            return self._start_locked(force=force, max_ticks=max_ticks)
        finally:
            # `_shutdown` is the normal release site; this covers the paths that never reach it
            # (a failed preflight returns before any run row is opened). `release()` is
            # idempotent, so the double call on the normal path is a no-op.
            self._release_lock()

    def _start_locked(self, *, force: bool, max_ticks: int | None) -> int:
        """`start`'s body, with the supervisor lock already held. Split out so the acquisition has
        exactly one paired release (`start`'s `finally`) rather than one per early return."""
        pf = self.preflight_fn(self.cfg)
        print("preflight:")
        print(pf.render())
        if not pf.ok and not force:
            print("\n✗ preflight failed — refusing to start. Fix the ✗ items, or `start --force` "
                  "to override.")
            return 1

        last_clean = self.runs.last_was_clean()
        recovery = not last_clean and not force
        commit, dirty = git_state(self.repo_root)
        run = self.runs.open_run(commit_sha=commit, dirty=dirty, pid=os.getpid(),
                                 recovery=recovery)
        self._run_id = run.id
        self._run = run
        tag = f"{commit[:12]}{' (dirty)' if dirty else ''}"
        print(f"\nrun #{run.id} on {tag}"
              + (" [RECOVERY — previous run did not exit cleanly]" if recovery else ""))

        clean = False
        try:
            if recovery:
                # The remedy is `palace stop`, NOT `start --force` (finding-0186). This recovery
                # run is itself a live supervisor, so a second `start` — force or not — now
                # refuses at the single-instance gate above; printing it as the escape would send
                # the operator into a wall. A graceful stop closes this row CLEAN, so the
                # successor comes up normally with no flag at all (under launchd KeepAlive the
                # stop IS the restart).
                print("recovery mode: scheduler halted, watcher off, read-only. Inspect the "
                      "stores, then `palace stop` once the cause is cleared — this run closes "
                      "clean and the next start is normal. (`start --force` will NOT get you out "
                      "of here: it does not bypass the single-instance gate — finding-0186.)")
                self._install_signal_handlers()
                self._idle(max_ticks)
            else:
                self._components = self.components_factory(self.cfg)
                # Reclaim rows stranded RUNNING by an unclean exit, BEFORE the first claim()
                # (bp-101, findings 0173/0177). Not cosmetic: this call is also what adopts the
                # run id, so without it `claimed_by_run` stays NULL forever and the next sweep
                # has nothing to key on.
                print(self._components.queue.sweep_orphans(run.id).render())
                self._components.enqueue_catchup()        # reconcile / rebuild an empty cache
                self._install_signal_handlers()
                self._serve(max_ticks)
            clean = True
        finally:
            self._shutdown(clean=clean)
        return 0

    def _serve(self, max_ticks: int | None) -> None:
        c = self._components
        assert c is not None
        backends = [w.start() for w in c.watchers]        # start every watched dir (vault + chat)
        print(f"watching {len(c.watchers)} dir(s) (backends={backends}); supervising. "
              "Ctrl-C or `palace stop` to drain + stop cleanly.")
        for child in c.children:                          # the supervised child processes (Inv 2)
            child.start()
            print(f"  ↳ started child {child.name!r} (pid {child.pid})")
        c.enqueue_housekeeping()                          # one pass soon after start
        last_housekeeping = last_health = last_snapshot = time.monotonic()
        flags: list[Flag] = []
        ticks = 0
        while not self._stopping and (max_ticks is None or ticks < max_ticks):
            # BOUND THE DRAIN (bp-108 Item 4, dn-supervision-and-liveness §2.5's interim fix).
            # This used to be a bare `run()`, which drains until nothing is runnable — so with a
            # backlog the health check, the snapshot refresh and housekeeping below did not run
            # until the queue emptied. The bound returns control to this loop at a job boundary.
            dispatched = c.supervisor.run(max_ticks=self.drain_max_ticks)
            now = time.monotonic()
            if now - last_health >= self.health_interval_s:
                flags = c.health_check()                  # the OS-health agent: sense + report
                for flag in flags:
                    print(f"⚠ health: {flag.note} ({flag.metric}={flag.value} < {flag.threshold})")
                for child in c.children:                  # restart a child that died
                    if not child.alive():
                        print(f"⚠ child {child.name!r} exited — restarting")
                        child.start()
                last_health = now
            if now - last_snapshot >= self.snapshot_interval_s:
                c.snapshot(self._run, flags)              # refresh the edge-monitor snapshot
                last_snapshot = now
            if now - last_housekeeping >= self.housekeeping_interval_s:
                c.enqueue_housekeeping()
                last_housekeeping = now
            ticks += 1
            # ⚑ THE OTHER HALF OF THE BOUND, and not optional. The sleep used to run every
            # iteration regardless of whether anything was dispatched. Pair that with a bounded
            # drain and a backlog of N trivial jobs costs ⌈N/K⌉ × tick_seconds of pure sleeping:
            # at the measured shape (N = 1,766 no-ops, tick_seconds = 1.0) a K of 1 would have
            # turned seconds of work into ~29 minutes. Bounding the drain WITHOUT this line trades
            # one availability defect for another — it is the note's own §2.10 falsifier.
            #
            # So: sleep only when the drain came back idle. `run()` returns its dispatch count, and
            # a non-zero count means there is more work ready right now — go straight round again.
            # This is not a spin: every no-sleep iteration dispatched up to K real jobs.
            if self.tick_seconds and not dispatched:
                time.sleep(self.tick_seconds)

    def _idle(self, max_ticks: int | None) -> None:
        # No conditional sleep here, deliberately: recovery mode runs no supervisor at all
        # ("scheduler halted, watcher off, read-only"), so there is never anything to drain and
        # the unconditional sleep IS the right duty cycle.
        ticks = 0
        while not self._stopping and (max_ticks is None or ticks < max_ticks):
            ticks += 1
            if self.tick_seconds:
                time.sleep(self.tick_seconds)

    def _release_lock(self) -> None:
        """Drop the supervisor lock if this launcher holds it. Idempotent and never raises —
        shutdown must not be the thing that crashes."""
        lock, self._lock = self._lock, None
        if lock is not None:
            lock.release()

    def _shutdown(self, *, clean: bool) -> None:
        if self._run_id is None:
            self._release_lock()     # nothing to close down, but we may still hold the lock
            return
        run_id, self._run_id = self._run_id, None        # idempotent: only once
        if self._components is not None:
            for w in self._components.watchers:            # stop every watched dir (vault + chat)
                try:
                    w.stop()
                except Exception:  # noqa: BLE001 — shutdown must not raise
                    pass
            for child in self._components.children:        # drain the child processes (SIGTERM)
                try:
                    child.stop()
                    print(f"  ↳ stopped child {child.name!r}")
                except Exception:  # noqa: BLE001
                    pass
        if self.on_shutdown is not None:
            try:
                self.on_shutdown(clean)                   # the lifecycle hook (e.g. final snapshot)
            except Exception:  # noqa: BLE001
                pass
        if self._components is not None:
            try:
                self._components.queue.close()
            except Exception:  # noqa: BLE001
                pass
        self.runs.mark_stopped(run_id, clean=clean)
        # LAST — the supervisor role is not free until the ledger says this run is over. Releasing
        # earlier would open a window in which a successor holds the lock while this run's row is
        # still active, so its `sweep_orphans` would see live rows to reclaim: the finding-0186
        # hazard, reintroduced by an ordering mistake.
        self._release_lock()
        print(f"run #{run_id} stopped ({'clean' if clean else 'UNCLEAN'}).")

    def _install_signal_handlers(self) -> None:
        def handler(_signum, _frame):
            self._stopping = True
        for sig in (signal.SIGTERM, signal.SIGINT):
            try:
                signal.signal(sig, handler)
            except ValueError:
                pass            # not on the main thread (tests) — fine; max_ticks bounds the loop

    # --- deploy (the promotion gate) ----------------------------------------------------------
    def deploy(self, *, skip_tests: bool = False) -> int:
        """Apply committed code/infra to the always-on system by a GRACEFUL cycle (owner rule
        2026-07-11) — never a kill. Gate, then drain, then verify.

        The gate: an active run exists; the working tree is clean; the branch is main; HEAD
        differs from the live run's commit; the fast ratchet is green (`--skip-tests` is the
        emergency hatch). Under launchd (KeepAlive) the graceful stop IS the restart — drain →
        exit → relaunch on the new code — so deploy just waits for the successor run and
        verifies its pinned SHA. Infra half: if the repo plist drifted from the installed
        copy, the cycle is bootout → cp → bootstrap instead, so plist changes deploy the same
        way code does. (Corollary the owner should know: under KeepAlive, `palace stop` means
        RESTART; a true stop is `launchctl bootout gui/$UID/com.mind-palace.palace`.)
        """
        run = self.runs.last()
        if run is None or not run.active or not _pid_alive(run.pid):
            print("deploy: no live run — nothing to cycle. Use `start` (or launchctl bootstrap).")
            return 1
        commit, dirty = git_state(self.repo_root)
        if dirty:
            print("deploy: REFUSED — working tree is dirty. Commit (or stash) first; "
                  "the run ledger pins runs to commits, and a dirty deploy pins a lie.")
            return 1
        if _git_branch(self.repo_root) != "main":
            print("deploy: REFUSED — not on main. main is the ingestion/deployment branch "
                  "(CONVENTIONS §Commits); merge first.")
            return 1
        if commit == run.commit_sha:
            print(f"deploy: already live on {commit[:12]} (run #{run.id}) — nothing to do.")
            return 0
        if not skip_tests:
            print(f"deploy gate: {' '.join(self.gate_cmd)}")
            if subprocess.run(list(self.gate_cmd), cwd=self.repo_root).returncode != 0:
                print("deploy: REFUSED — the ratchet is red. Fix or (emergencies only) "
                      "--skip-tests.")
                return 1
        if self.ci_check_cmd is not None and not skip_tests:
            print("deploy gate: ci-witness (remote pipeline must be green for HEAD)")
            if subprocess.run([*self.ci_check_cmd, commit], cwd=self.repo_root).returncode != 0:
                print("deploy: REFUSED — no attested green pipeline for HEAD. Push first, "
                      "wait for CI, or (emergencies only) --skip-tests.")
                return 1
        managed = _launchd_managed(self.launchd_label, self.domain)
        repo_plist = self.domain.repo_plist(self.repo_root)
        installed = self.installed_plist                       # domain-correct (risk (a))
        drift = (managed and repo_plist.exists() and installed.exists()
                 and installed.read_bytes() != repo_plist.read_bytes())
        if drift:
            print("deploy: plist drift detected — full reinstall cycle (bootout → cp → bootstrap).")
            _launchd_cycle(self.launchd_label, repo_plist, installed, self.domain)
        else:
            self.stop()                                    # SIGTERM → drain at the boundary
        if not managed:
            print("deploy: drained, but the run is NOT launchd-managed — no supervisor will "
                  "relaunch it. Start it yourself (`palace start`), or install the agent "
                  "(runbook → One-command lifecycle).")
            return 0
        deadline = time.monotonic() + self.deploy_wait_s
        while time.monotonic() < deadline:
            new = self.runs.last()
            if new is not None and new.id > run.id and new.active and _pid_alive(new.pid):
                if new.recovery:
                    print(f"deploy: FAILED — run #{new.id} came up in RECOVERY (previous run "
                          "did not close clean). Inspect, then `start --force` semantics apply.")
                    return 1
                if new.commit_sha == commit:
                    print(f"deploy: OK — {run.commit_sha[:12]} → {commit[:12]} "
                          f"(run #{run.id} → #{new.id}, pid {new.pid}).")
                    if self.ci_release_cmd is not None:
                        # release-on-deploy: best-effort, never fails a verified deploy
                        subprocess.run([*self.ci_release_cmd, commit], cwd=self.repo_root)
                    return 0
            time.sleep(self.deploy_poll_s)
        print(f"deploy: TIMED OUT after {self.deploy_wait_s:.0f}s waiting for the successor "
              "run — check `palace status` and data/logs/palace.err.log.")
        return 1

    # --- stop / status ----------------------------------------------------------------------
    def stop(self) -> int:
        """SIGTERM the live run and report **what was verified**, not what was requested.

        The old line — "it will drain + mark clean" — asserted a future the command cannot see.
        The drain finishes at the in-flight job's boundary and has no time bound (finding-0171),
        so a wedged job means the process outlives the signal indefinitely. This now says which
        of the two happened. NO escalation is added: SIGKILL / job budgets are the owner's open
        decision (finding-0171 (a)/(b)/(c)); this command only signals, observes, and reports."""
        run = self.runs.last()
        if run is None or not run.active:
            print("no active run to stop.")
            return 1
        if not _pid_alive(run.pid):
            # ledger says active, the OS says otherwise — the finding-0172 stale row. Close it.
            self.runs.mark_stopped(run.id, clean=False, note="stop: process already gone")
            print(f"run #{run.id} (pid {run.pid}) was not alive — marked unclean.")
            return 1
        try:
            os.kill(run.pid, signal.SIGTERM)
        except ProcessLookupError:
            # raced us between the liveness probe and the signal — same conclusion.
            self.runs.mark_stopped(run.id, clean=False, note="stop: process already gone")
            print(f"run #{run.id} (pid {run.pid}) was not alive — marked unclean.")
            return 1
        if self._await_exit(run.pid, self.stop_verify_s):
            print(f"stop: SIGTERM sent to run #{run.id} (pid {run.pid}) — process exited. "
                  "Under launchd KeepAlive this is a RESTART, not a down (`palace down`).")
            return 0
        print(f"stop: SIGTERM sent to run #{run.id} (pid {run.pid}) — STILL ALIVE after "
              f"{self.stop_verify_s:.0f}s. The drain ends at the in-flight job's boundary and has "
              "no time bound (finding-0171), so this may be a long job or a wedged one. Check "
              f"`ps -o pid=,stat=,etime=,%cpu= -p {run.pid}`; escalation is an owner decision, "
              "not this command's.")
        return 0

    def _await_exit(self, pid: int, seconds: float) -> bool:
        """Poll `_pid_alive` for up to `seconds`; True iff the process is gone by then.

        Observation only — it never signals and never escalates. `_pid_alive` is the ONE liveness
        primitive (reused, not re-implemented); note it reports True on `PermissionError`, so a
        process owned by another principal is correctly seen as alive rather than as exited."""
        deadline = time.monotonic() + max(0.0, seconds)
        while True:
            if not _pid_alive(pid):
                return True
            if time.monotonic() >= deadline:
                return False
            time.sleep(min(self.stop_poll_s, max(0.0, deadline - time.monotonic())) or 0.01)

    # --- ingest-chat (on-demand chat sensor run, bp-068) -------------------------------------
    def ingest_chat(self) -> int:
        """Build the bp-063 chat sensor and run one idempotent `sync()`, printing the report.

        The scheduled `chat_sync` job does this in the daemon (startup catch-up + housekeeping);
        this is the owner's MANUAL trigger — e.g. the very first ingest, before the daemon's first
        housekeeping tick. Reads local transcripts only (no network, no vault) — safe inside the
        seal. Idempotent: a session already in the store is skipped."""
        from ops.chat_sensor import build_chat_sensor
        report = build_chat_sensor(self.cfg).sync()
        print(f"chat ingest: {report}")
        return 0

    # --- code-seed (the deliberate, owner-visible code SEED, bp-098 / note §2.7) --------------
    def code_seed(self) -> int:
        """Enqueue the one-time code SEED onto the running daemon's supervisor queue — every HEAD
        `.py` blob embedded once (note §2.7 the deliberate owner-visible run).

        Unlike `ingest-chat` (a lightweight in-process `sync()`), the code seed is HEAVY, so it must
        ride the single-writer supervisor queue rather than write the store from this CLI process:
        we INSERT one `code_sync` job into the shared on-disk queue (the same queue the daemon
        drains) and the daemon runs it at BACKGROUND priority under the memory ceiling. `sync()` is
        idempotent + blob-sha keyed, so a duplicate seed re-embeds nothing. The queue is durable, so
        if the daemon is down the job simply waits until it next starts (said, not silent)."""
        from scheduler.code_sync import enqueue_code_sync
        from scheduler.queue import JobQueue
        from scheduler.router import Router
        queue = JobQueue(self.cfg.paths.data_dir / "queue.sqlite")
        try:
            job = enqueue_code_sync(queue, Router(self.cfg))
        finally:
            queue.close()
        run = self.runs.last()
        live = run is not None and run.active
        where = ("the daemon will drain it at BACKGROUND priority — `palace queue` to watch."
                 if live else
                 "no daemon is running — the job waits in the durable queue until `palace start`.")
        print(f"code seed: enqueued code_sync job #{job.id}; {where}")
        return 0

    # --- code-backfill (the deliberate history backfill, bp-099 / dn-temporal-code-corpus) ----
    def code_backfill(self) -> int:
        """Enqueue the one-time code HISTORY backfill onto the running daemon's supervisor queue —
        every distinct ledger `(path, blob_sha)` version embedded (D1) + the first-parent commit
        diffs captured (D4). Same discipline as `code_seed`: HEAVY, so it rides the single-writer
        supervisor queue (a durable job insert, never a store write from this CLI). Idempotent —
        already-embedded versions re-embed nothing, so a duplicate backfill is safe; the catch-up
        probe also enqueues one automatically when the store is incomplete. If the daemon is down
        job waits in the durable queue until `palace start`."""
        from scheduler.code_sync import enqueue_code_backfill
        from scheduler.queue import JobQueue
        from scheduler.router import Router
        queue = JobQueue(self.cfg.paths.data_dir / "queue.sqlite")
        try:
            job = enqueue_code_backfill(queue, Router(self.cfg))
        finally:
            queue.close()
        run = self.runs.last()
        live = run is not None and run.active
        where = ("the daemon will drain it at BACKGROUND priority — `palace queue` to watch."
                 if live else
                 "no daemon is running — the job waits in the durable queue until `palace start`.")
        print(f"code backfill: enqueued code_backfill job #{job.id}; {where}")
        return 0

    # --- down / up / restart (KeepAlive-aware maintenance control, finding-0066) -------------
    def _managed(self) -> bool:
        """Is the palace agent currently bootstrapped in its launchd domain (gui by default)?"""
        return self.launchctl(["print", self.domain.target(self.launchd_label)]).returncode == 0

    def down(self) -> int:
        """Maintenance-down that OUTLASTS KeepAlive (finding-0066): `launchctl bootout`. Plain
        `stop` only SIGTERMs and launchd immediately relaunches it — so a true down boots the
        agent out. Idempotent (already-out reports and returns 0); if the agent isn't installed
        there is no KeepAlive to outlast, so fall back to a plain `stop`.

        **`down` no longer claims a state it has not observed (finding-0171).** Observed
        2026-07-25: it printed its success line while pid 96950 kept running at 96% CPU and
        `launchctl print` showed `active count = 1` pending — the launchd JOB was unloaded, the
        PROCESS was not. Booting the agent out and the process exiting are two different facts, so
        this now reports them separately: it verifies the pid for `stop_verify_s` and, if the
        process outlives the bootout, says so by pid/run/elapsed and returns non-zero. The
        escalation policy (SIGTERM→SIGKILL, job budgets) remains the owner's open decision
        (finding-0171 (a)/(b)/(c)); nothing here kills anything."""
        if not self.installed_plist.exists():
            print("down: not installed as a LaunchAgent — no KeepAlive to outlast; plain stop.")
            return self.stop()
        if not self._managed():
            print("down: already down (agent booted out).")
            return 0
        run = self.runs.last()
        rc = self.launchctl(["bootout", self.domain.target(self.launchd_label)]).returncode
        if rc != 0:
            print(f"down: `launchctl bootout` failed (rc={rc}). The agent may still be live.")
            return rc
        booted = f"down: booted out {self.launchd_label}"
        if run is None or not run.active:
            print(f"{booted} — stays down past KeepAlive. (No live run in the ledger, so there "
                  "was no process to verify.) `palace up` to bring it back.")
            return 0
        if not _pid_alive(run.pid):
            print(f"{booted}; run #{run.id}'s pid {run.pid} was already gone (a stale ledger row "
                  "— it closes on the next start) — verified down. `palace up` to bring it back.")
            return 0
        if self._await_exit(run.pid, self.stop_verify_s):
            print(f"{booted} AND pid {run.pid} exited — verified down, past KeepAlive. "
                  "`palace up` to bring it back.")
            return 0
        print(f"{booted}, but pid {run.pid} (run #{run.id}, started {run.started_at}) is STILL "
              f"ALIVE {self.stop_verify_s:.0f}s later — the system is NOT down. launchd will not "
              "relaunch it, but the graceful drain waits on the in-flight job's boundary and has "
              "no time bound (finding-0171). Check "
              f"`ps -o pid=,stat=,etime=,%cpu= -p {run.pid}`; escalation is an owner decision, "
              "not this command's.")
        return 1

    def up(self) -> int:
        """Bring the agent back: `launchctl bootstrap`. Idempotent (already-up reports, returns
        0); if the agent isn't installed there is nothing to bootstrap (run `palace start`)."""
        if not self.installed_plist.exists():
            print("up: not installed as a LaunchAgent — `palace start` (foreground) or install "
                  "the agent (runbook → One-command lifecycle).")
            return 0
        if self._managed():
            print("up: already up (agent bootstrapped).")
            return 0
        rc = self.launchctl(
            ["bootstrap", self.domain.bootstrap_domain(), str(self.installed_plist)]).returncode
        if rc != 0:
            print(f"up: `launchctl bootstrap` failed (rc={rc}).")
            return rc
        print(f"up: bootstrapped {self.launchd_label} — live under KeepAlive.")
        return 0

    def restart(self) -> int:
        """A plain down→up cycle. NOT `deploy` — no HEAD promotion, no test/CI gate; this just
        cycles the running code as-is (a deploy is the gated ratchet onto HEAD).

        Because `down` is now honest, a `down` that could not verify the process exited returns
        non-zero and this refuses to bring the agent back — which is the point: bootstrapping a
        successor while the predecessor still runs is the double-instance hazard, and the old
        code would have done exactly that on the strength of a success line it had not earned."""
        rc = self.down()
        if rc != 0:
            print("restart: REFUSED to bring the agent back up — `down` did not complete. "
                  "Resolve the still-running process first (see the line above).")
            return rc
        return self.up()

    def status(self) -> int:
        """The read-only truth report. Two properties are load-bearing (finding-0172):

        (1) **Liveness is tested, never assumed.** A ledger row marked active whose pid is gone
        renders `DEAD (stale ledger row)` and suppresses the `running HEAD` banner — the exact
        false green the owner read through a 90-minute incident.

        (2) **Derivatives, not just levels.** `_report_snapshot` adds rates, budgets, failures.

        Read-only in the strict sense: it opens nothing it would have to create (previously it
        constructed a `JobQueue`, which CREATES `queue.sqlite`), enqueues nothing, and is safe to
        run with the daemon down — which is when it matters most.
        """
        pf = self.preflight_fn(self.cfg)                  # probed ONCE; reused for the embedder
        print("preflight:")
        print(pf.render())
        runs = self.runs.recent(5)
        if not runs:
            print("\nno runs recorded yet.")
            return 0
        print("\nrecent runs:")
        for r in runs:
            state, _alive = run_state(r, pid_alive=_pid_alive)
            rec = " [recovery]" if r.recovery else ""
            pid = f" (pid {r.pid})" if r.active else ""
            print(f"  #{r.id} {r.commit_sha[:12]}{' (dirty)' if r.dirty else ''} "
                  f"started {r.started_at} — {state}{rec}{pid}")
        # running-code-vs-HEAD gap: a live run pinned to a commit behind HEAD hasn't picked up the
        # latest deploy (finding-0066 lag). Only meaningful while a run is genuinely live — a
        # HEAD banner over a dead pid is the finding-0172 lie, so liveness gates it.
        live = self.runs.last()
        head_commit, head_dirty = git_state(self.repo_root)
        liveness = run_state(live, pid_alive=_pid_alive)
        if live is not None and live.active and liveness[1] is False:
            print(f"\n⚠ run #{live.id} is marked active in the run ledger but pid {live.pid} is "
                  "NOT alive — the daemon is DOWN and the row is stale (it closes on the next "
                  "start). `palace up` under launchd, or `palace start`.")
        elif live is not None and live.active:
            if live.commit_sha != head_commit:
                print(f"\n⚠ running {live.commit_sha[:12]} — HEAD is {head_commit[:12]}"
                      f"{' (dirty)' if head_dirty else ''}: run #{live.id} is behind. "
                      "`palace deploy` to promote onto HEAD.")
            else:
                print(f"\nrunning HEAD ({head_commit[:12]}"
                      f"{' — dirty tree' if head_dirty else ''}).")
        self._report_snapshot(live, liveness=liveness, preflight_ok=pf.ok)
        return 0

    def _open_vector_store_if_present(self):  # noqa: ANN201 — a `_CountableStore` (snapshot.py)
        """The vector store ONLY if its directory already exists.

        `lancedb.connect` creates its directory, and `status` must not write; an absent store is
        simply an absent figure. The returned object is used for `count()` and nothing else."""
        p = self.cfg.paths.vector_store
        if not p.exists():
            return None
        try:
            from core.stores.vectorstore import open_vector_store
            return open_vector_store(self.cfg)
        except Exception:  # noqa: BLE001 — a probe failure is a missing figure, never a crash
            return None

    def _embedder_state(self, preflight_ok: bool) -> str | None:
        """`'<model> resident'` / `'<model> NOT resident'` / None when unknown.

        The incident's "99% CPU with a 0.3% embedder" signal in the form actually available: is the
        embedding model loaded in the local Ollama? Reuses `OllamaClient.ps()` (DRY — no second
        client) and is attempted ONLY when preflight already reached Ollama, so it adds no new
        failure mode or hang class beyond the probe `status` already performs. The load-bearing
        anomaly remains `wedged` (a running job with zero terminal transitions all window) — this
        line is corroboration, not the alarm."""
        if not preflight_ok:
            return None
        try:
            from core.models.ollama_client import OllamaClient
            model = self.cfg.embedding.model
            resident = OllamaClient(self.cfg.ollama).ps()
            here = any(m == model or m.startswith(f"{model}:") for m in resident)
            return f"{model} {'resident' if here else 'NOT resident'}"
        except Exception:  # noqa: BLE001 — unknown is an honest answer; never fail status
            return None

    def _report_snapshot(self, run: RunRecord | None,
                         liveness: tuple[str, bool | None] | None = None,
                         preflight_ok: bool = False) -> None:
        """Pretty-print the `build_status` payload: queue depth, health/RAM headroom, drift,
        dream + tidy-suggestion counts, action activity — plus (bp-102) the RATE/BUDGET block:
        in-rate vs out-rate over W, windowed throughput, per-kind oldest age, running-job elapsed,
        the last failure, and the metadata-only store figures.

        Every datum traces to `build_status` — that is the single seam, so nothing is printed
        beside it. Read-only and CHEAP by construction: bounded SQL aggregates over the queue,
        `count()` (lance fragment metadata) over the vector table, one `COUNT(DISTINCT …)` over
        the code ledger. Nothing here materializes the `vector` column or scans a payload; a
        status command that repeats finding-0169 one level up has failed even if every number
        is right (bp-102 Item 2 falsifier, asserted in tests/unit/test_status_cost_bound.py)."""
        from core.attestation.store import open_attestation_store
        from core.dreams_view import DreamsView
        from core.ops_view import OpsView
        from core.stores.derived import open_derived_store
        from core.typedshims import psutil
        from ops.ledger import open_ledger

        ops_view = OpsView.over(open_attestation_store(self.cfg), open_ledger(self.cfg))
        dreams_view = DreamsView.over(open_derived_store(self.cfg))
        # The intra-job derivative (bp-105 Item 1 / finding-0188), read BEFORE the queue so the
        # anomaly predicates are computed with it rather than corrected afterwards. A directory
        # stat — 0.80 ms over the real store, O(directories) not O(rows) — so the Item-2 cost
        # falsifier still holds: nothing here grows with the corpus.
        qs = read_queue_stats(self.cfg.paths.data_dir / "queue.sqlite",
                              window_minutes=self.status_window_minutes,
                              store_idle_s=store_idle_seconds(self.cfg.paths.vector_store))
        store = read_store_stats(vector_store=self._open_vector_store_if_present())
        mem_gb = round(psutil.virtual_memory().available / (1024 ** 3), 2)
        data = build_status(ops_view=ops_view, dreams_view=dreams_view, queue_depth=qs.depth,
                            run=run, mem_available_gb=mem_gb, liveness=liveness,
                            queue_stats=qs, store_stats=store,
                            embedder=self._embedder_state(preflight_ok))
        h, p, a = data["health"], data["patterns"], data["activity"]
        rates, w = data["rates"], qs.window_minutes
        print("\nsystem:")
        drain = "  ⚠ ZERO DRAIN (0 completed)" if qs.stalled else ""
        print(f"  queue depth: {data['queue_depth']}   "
              f"(in {rates['in_rate_per_min']:.1f}/min · out {rates['out_rate_per_min']:.1f}/min "
              f"· net {rates['net_rate_per_min']:+.1f}/min over {w:.0f} min){drain}")
        thru = "  ⚠ nothing completed" if qs.stalled else ""
        print(f"  throughput: {qs.done_in_window} done, {qs.failed_in_window} failed "
              f"in the last {w:.0f} min{thru}")
        # A RUNNING row is only meaningful if a live worker owns it. With the daemon dead the row
        # is an ORPHAN (finding-0173) and its ever-growing "elapsed" would otherwise read as work
        # in progress — the same false-green shape as the RUNNING banner, one level down.
        daemon_alive = liveness is not None and liveness[1] is True
        if qs.running:
            for j in qs.running:
                if not daemon_alive:
                    flag = "  ⚠ ORPHANED — no live daemon owns this row"
                elif qs.wedged:
                    flag = "  ⚠ running while NOTHING completed this window"
                else:
                    flag = ""
                # No budget fraction: no job-level timeout exists (bp-102 Q4 / finding-0174).
                print(f"  running: #{j.id} {j.kind} — elapsed "
                      f"{humanize_seconds(j.elapsed_s)} (no enforced job budget){flag}")
            # THE LINE THAT SEPARATES A HEALTHY BACKFILL FROM A WEDGED ONE (finding-0188). Without
            # it the two states render identically and every flag above fires through a perfectly
            # healthy multi-hour backfill — the false alarm bp-102 §10 called disqualifying.
            if qs.embedding is True:
                print(f"  embedding: YES — rows last landed "
                      f"{humanize_seconds(qs.store_idle_s)} ago, inside the running job's "
                      f"{humanize_seconds(qs.youngest_running_elapsed_s)}. "
                      "The job is working, not wedged.")
            elif qs.embedding is False:
                print(f"  embedding: NO — the vector store has not been written in "
                      f"{humanize_seconds(qs.store_idle_s)}, which PREDATES the running job. "
                      "It has landed nothing since it started.  ⚠ WEDGED")
            else:
                print("  embedding: unknown (no readable vector store) — a healthy backfill and a "
                      "wedged job are indistinguishable without it.")
        else:
            print("  running: (none)")
        if qs.queued_by_kind:
            waiting = " · ".join(f"{k.kind} {k.count}, oldest {humanize_seconds(k.oldest_age_s)}"
                                 for k in qs.queued_by_kind)
            print(f"  waiting: {waiting}")
        if qs.last_failure is not None:
            f = qs.last_failure
            recent = "  ⚠" if qs.failure_in_window else ""
            print(f"  last failure: #{f.id} {f.kind} {humanize_seconds(f.age_s)} ago "
                  f"— {f.error[:160]}{recent}")
        else:
            print("  last failure: (none recorded)")
        life = " · ".join(f"{v} {k}" for k, v in sorted(qs.lifetime.items())) or "(empty queue)"
        print(f"  lifetime: {life}")
        print(f"  memory available: {h['memory_available_gb']} GB")
        print(f"  drift within tolerance: {h['drift_within_tolerance']}   "
              f"constitution intact: {h['constitution_intact']}")
        print(f"  dreams: {p['dreams']}   tidy suggestions: {p['tidy_suggestions']}")
        print(f"  actions logged: {a['actions_logged']}   "
              f"pending approvals: {a['pending_approvals']}")
        # Store: metadata-only, and only the ONE figure that is. Code-version coverage (embedded
        # vs ledger target, current/superseded split) is deliberately NOT shown: neither side has
        # a cheap reader today (the ledger side measures 3.5 s — a full scan), and paying that on
        # every `status` would be finding-0169 all over again. See snapshot.StoreStats /
        # finding-0178 for the two readers that would make it cheap.
        rows = "?" if store.vector_rows is None else f"{store.vector_rows:,}"
        print(f"  store: {rows} vector rows "
              "(code-version coverage has no metadata-only reader — not shown)")
        print(f"  embedder: {data['embedder'] or 'unknown'}")

    # --- reset (the fresh-start wipe) -------------------------------------------------------
    def reset_targets(self) -> list[Path]:
        """The corpus + its derived/chain layer + the stale queue. Computed from cfg.paths;
        each is asserted to be under data/ and outside the guard set (never the Vault Raft)."""
        p = self.cfg.paths
        candidates = [
            p.raw_store, p.vector_store, p.vault_catalog, p.derived_store, p.attestation_store,
            p.data_dir / "queue.sqlite",
            # Sibling stores opened via `derived_store.parent / <name>` (no dedicated cfg path).
            # All four are corpus/derived-chain provenance: left behind, their rows reference
            # wiped artifacts — orphaned history that would pollute a fresh graph's record.
            p.data_dir / "versions.sqlite",                 # note-version supersession history
            p.data_dir / "authored_supersessions.sqlite",   # owner-declared K₀↔K₀ (founding)
            p.data_dir / "verdicts.sqlite",                 # verdict ledger over derived artifacts
            p.data_dir / "verdict_dispositions.sqlite",     # dispositions derived from verdicts
            # Code observations are CORPUS-side (the observed stratum, ratified
            # code-observation-projection.md §2.4) — wiped with the corpus, unlike the
            # snapshot LEDGER (build history, in _RESET_GUARD above). bp-012 Item 4 / Q4.
            p.data_dir / "code_observations.sqlite",
            # Lane-1 reference edges are CORPUS-side too (cross-stratum doc↔code refs minted
            # at projection time, ratified §2.5) — their rows reference wiped corpus/code
            # endpoints, so they orphan on reset like the observations. bp-013 Q4 (parked to
            # the orchestrator; launcher.py was outside the builder's write_scope).
            p.data_dir / "reference_edges.sqlite",
            # Agent (self-sensing) observations are CORPUS-side too — the third stream's
            # READINGS (dn-self-sensing §2.5 ruling): wiped with the corpus, rebuilt by
            # re-projection from git's build-plan `cost:` history. The worldview HISTORY
            # (superseded generations) rides the guarded `observation_history.sqlite`
            # sidecar above, unaffected by this reset. bp-019 Item 8 / §6(h).
            p.data_dir / "agent_observations.sqlite",
            # Chat utterances are CORPUS-side too — the observed chat stratum's READINGS
            # (ratified dn-chat-sensor CS-2). Wiped with the corpus and rebuilt by re-ingest
            # from the IMMUTABLE rawstore (p.raw_store, above — the verbatim archive is NOT a
            # reset target; raw is sacred). bp-063 Q6 (parked to the orchestrator; launcher.py
            # was outside the builder's write_scope).
            p.data_dir / "chatlog.sqlite",
            # The L1 action log is CORPUS-side too — the dialogue stratum's DERIVED layer (bp-069
            # Item 3): wiped with the corpus and rebuilt by re-projection from the rawstore-backed
            # chatlog (the raw archive is NOT a reset target). It holds only structural refs.
            p.data_dir / "chat_events.sqlite",
            # The C-fiber causal edges are CORPUS-side too — the integrator's DERIVED output
            # (bp-071): a pure function of retained L1 + the ledger (the floor invariant), so wiped
            # with the corpus and rebuilt by re-integration. Structural refs only; no content.
            p.data_dir / "causal_edges.sqlite",
        ]
        out: list[Path] = []
        for c in candidates:
            assert p.data_dir in c.parents or c.parent == p.data_dir, f"target {c} not under data/"
            assert c.name not in _RESET_GUARD and c.name != "vault", f"refusing to wipe guarded {c}"
            out.append(c)
        return out

    def reset(self, *, confirm: bool) -> int:
        import shutil
        run = self.runs.last()
        if run is not None and run.active and _pid_alive(run.pid):
            print(f"refusing reset — run #{run.id} (pid {run.pid}) is live. `palace stop` first.")
            return 1
        targets = self.reset_targets()
        print("fresh-start reset will remove the corpus + derived layer:")
        for t in targets:
            print(f"  - {t}  (+ -wal/-shm if present)")
        vault_raft = self.cfg.paths.data_dir / "vault"
        print(f"GUARDED (never touched): production Vault Raft ({vault_raft}), "
              "run/self-mod ledgers, telemetry, backups, logs.")
        if not confirm:
            print("\nDRY RUN — nothing removed. Re-run with --confirm. Your restic snapshot is the "
                  "safety net; a fresh re-ingest re-tags everything authored-solo (mooting the "
                  "provenance migration).")
            return 0
        removed = 0
        for t in targets:
            for path in (t, Path(str(t) + "-wal"), Path(str(t) + "-shm")):
                if path.is_dir():
                    shutil.rmtree(path)
                    removed += 1
                elif path.exists():
                    path.unlink()
                    removed += 1
        print(f"\nremoved {removed} path(s). Re-export notes into the vault, then `palace start` "
              "(it will re-ingest as authored-solo).")
        return 0


def build_launcher(config: Config | None = None, **kw) -> Launcher:
    from config.loader import REPO_ROOT, get_config
    from ops.lifecycle.runs import open_run_ledger

    cfg = config or get_config()
    return Launcher(cfg=cfg, runs=open_run_ledger(cfg), repo_root=REPO_ROOT, **kw)
