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
from pathlib import Path
from typing import TYPE_CHECKING, Protocol

from ops.lifecycle.preflight import Preflight, run_preflight
from ops.lifecycle.runs import RunLedger, RunRecord, git_state

if TYPE_CHECKING:  # annotations only — the real modules stay lazily imported at runtime
    from config.loader import Config
    from core.ingest.code_corpus import CodeCorpusSync
    from scheduler.router import Flag


class SupervisorLike(Protocol):
    """`scheduler.supervisor.Supervisor`'s real surface here — structural so tests inject a bare
    `_FakeSupervisor` without subclassing the real Supervisor. Narrowed to a no-arg `run()`
    (the only call shape launcher.py uses: `c.supervisor.run()`), not the real Supervisor's
    fuller `run(*, max_ticks=...)` — a Protocol is only as wide as its actual call sites here."""

    def run(self) -> object: ...


class WatcherLike(Protocol):
    """`core.ingest.watch.DirectoryWatcher`'s real surface here (structural, same reasoning).
    `start()` narrowed to no-arg (the only call shape here: iterating `c.watchers` and calling
    `w.start()`/`w.stop()`)."""

    def start(self) -> object: ...
    def stop(self) -> None: ...


class QueueLike(Protocol):
    """`scheduler.queue.JobQueue`'s real surface here (only `.close()` is called through
    `Components.queue` — `build_components` calls `.depth()` on its own `JobQueue` directly)."""

    def close(self) -> None: ...


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


def _pid_alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)        # signal 0 = liveness probe, delivers nothing
    except ProcessLookupError:
        return False           # no such process
    except PermissionError:
        return True            # exists but owned by another user
    return True


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
    _stopping: bool = field(default=False, init=False)
    _run_id: int | None = field(default=None, init=False)
    _run: RunRecord | None = field(default=None, init=False)  # the active RunRecord (for snapshots)
    _components: Components | None = field(default=None, init=False)

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
                print("recovery mode: scheduler halted, watcher off, read-only. Inspect the "
                      "stores, then `start --force` to resume normally once the cause is cleared.")
                self._install_signal_handlers()
                self._idle(max_ticks)
            else:
                self._components = self.components_factory(self.cfg)
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
            c.supervisor.run()                            # drain runnable jobs at boundaries
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
            if self.tick_seconds:
                time.sleep(self.tick_seconds)

    def _idle(self, max_ticks: int | None) -> None:
        ticks = 0
        while not self._stopping and (max_ticks is None or ticks < max_ticks):
            ticks += 1
            if self.tick_seconds:
                time.sleep(self.tick_seconds)

    def _shutdown(self, *, clean: bool) -> None:
        if self._run_id is None:
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
        run = self.runs.last()
        if run is None or not run.active:
            print("no active run to stop.")
            return 1
        try:
            os.kill(run.pid, signal.SIGTERM)
        except ProcessLookupError:
            # the process is gone but never marked stopped — a crash; record it as unclean.
            self.runs.mark_stopped(run.id, clean=False, note="stop: process already gone")
            print(f"run #{run.id} (pid {run.pid}) was not alive — marked unclean.")
            return 1
        print(f"sent SIGTERM to run #{run.id} (pid {run.pid}); it will drain + mark clean.")
        return 0

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
        there is no KeepAlive to outlast, so fall back to a plain `stop`."""
        if not self.installed_plist.exists():
            print("down: not installed as a LaunchAgent — no KeepAlive to outlast; plain stop.")
            return self.stop()
        if not self._managed():
            print("down: already down (agent booted out).")
            return 0
        rc = self.launchctl(["bootout", self.domain.target(self.launchd_label)]).returncode
        if rc != 0:
            print(f"down: `launchctl bootout` failed (rc={rc}). The agent may still be live.")
            return rc
        print(f"down: booted out {self.launchd_label} — stays down past KeepAlive. "
              "`palace up` to bring it back.")
        return 0

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
        cycles the running code as-is (a deploy is the gated ratchet onto HEAD)."""
        rc = self.down()
        if rc != 0:
            return rc
        return self.up()

    def status(self) -> int:
        print("preflight:")
        print(self.preflight_fn(self.cfg).render())
        runs = self.runs.recent(5)
        if not runs:
            print("\nno runs recorded yet.")
            return 0
        print("\nrecent runs:")
        for r in runs:
            state = ("RUNNING" if r.active else ("clean" if r.clean_shutdown else "UNCLEAN"))
            rec = " [recovery]" if r.recovery else ""
            print(f"  #{r.id} {r.commit_sha[:12]}{' (dirty)' if r.dirty else ''} "
                  f"started {r.started_at} — {state}{rec}")
        # running-code-vs-HEAD gap: a live run pinned to a commit behind HEAD hasn't picked up the
        # latest deploy (finding-0066 lag). Only meaningful while a run is live.
        live = self.runs.last()
        head_commit, head_dirty = git_state(self.repo_root)
        if live is not None and live.active:
            if live.commit_sha != head_commit:
                print(f"\n⚠ running {live.commit_sha[:12]} — HEAD is {head_commit[:12]}"
                      f"{' (dirty)' if head_dirty else ''}: run #{live.id} is behind. "
                      "`palace deploy` to promote onto HEAD.")
            else:
                print(f"\nrunning HEAD ({head_commit[:12]}"
                      f"{' — dirty tree' if head_dirty else ''}).")
        self._report_snapshot(live)                       # the enriched read-only system snapshot
        return 0

    def _report_snapshot(self, run: RunRecord | None) -> None:
        """Pretty-print the `build_status` payload (bp-030 Item 3): queue depth, health/RAM
        headroom, drift, dream + tidy-suggestion counts, action activity. Read-only — reuses the
        same views the edge-monitor snapshot fed; every datum traces to `build_status`."""
        from core.attestation.store import open_attestation_store
        from core.dreams_view import DreamsView
        from core.ops_view import OpsView
        from core.stores.derived import open_derived_store
        from core.typedshims import psutil
        from ops.ledger import open_ledger
        from ops.lifecycle.snapshot import build_status
        from scheduler.queue import JobQueue

        ops_view = OpsView.over(open_attestation_store(self.cfg), open_ledger(self.cfg))
        dreams_view = DreamsView.over(open_derived_store(self.cfg))
        queue = JobQueue(self.cfg.paths.data_dir / "queue.sqlite")
        try:
            depth = queue.depth()
        finally:
            queue.close()
        mem_gb = round(psutil.virtual_memory().available / (1024 ** 3), 2)
        data = build_status(ops_view=ops_view, dreams_view=dreams_view, queue_depth=depth,
                            run=run, mem_available_gb=mem_gb)
        h, p, a = data["health"], data["patterns"], data["activity"]
        print("\nsystem:")
        print(f"  queue depth: {data['queue_depth']}")
        print(f"  memory available: {h['memory_available_gb']} GB")
        print(f"  drift within tolerance: {h['drift_within_tolerance']}   "
              f"constitution intact: {h['constitution_intact']}")
        print(f"  dreams: {p['dreams']}   tidy suggestions: {p['tidy_suggestions']}")
        print(f"  actions logged: {a['actions_logged']}   "
              f"pending approvals: {a['pending_approvals']}")

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
