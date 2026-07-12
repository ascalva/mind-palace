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
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Protocol

from ops.lifecycle.preflight import Preflight, run_preflight
from ops.lifecycle.runs import RunLedger, RunRecord, git_state

if TYPE_CHECKING:  # annotations only — the real modules stay lazily imported at runtime
    from config.loader import Config
    from scheduler.router import Flag


class SupervisorLike(Protocol):
    """`scheduler.supervisor.Supervisor`'s real surface here — structural so tests inject a bare
    `_FakeSupervisor` without subclassing the real Supervisor. Narrowed to a no-arg `run()`
    (the only call shape launcher.py uses: `c.supervisor.run()`), not the real Supervisor's
    fuller `run(*, max_ticks=...)` — a Protocol is only as wide as its actual call sites here."""

    def run(self) -> object: ...


class WatcherLike(Protocol):
    """`core.ingest.watch.VaultWatcher`'s real surface here (structural, same reasoning).
    `start()` narrowed to no-arg (the only call shape here: `c.watcher.start()`)."""

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


def _launchd_managed(label: str) -> bool:
    """Is the palace agent bootstrapped in the user's gui domain?"""
    r = subprocess.run(["launchctl", "print", f"gui/{os.getuid()}/{label}"],
                       capture_output=True)
    return r.returncode == 0


def _launchd_cycle(label: str, repo_plist: Path, installed: Path) -> None:
    """The infra half of deploy: bootout → install the repo plist → bootstrap."""
    domain = f"gui/{os.getuid()}"
    subprocess.run(["launchctl", "bootout", f"{domain}/{label}"], check=False)
    shutil.copy2(repo_plist, installed)
    subprocess.run(["launchctl", "bootstrap", domain, str(installed)], check=True)


@dataclass
class Components:
    """What `serve` drives. Injectable so tests exercise the lifecycle without models."""

    supervisor: SupervisorLike
    watcher: WatcherLike
    queue: QueueLike
    enqueue_catchup: Callable[[], None] = lambda: None     # reconcile corpus on start
    enqueue_housekeeping: Callable[[], None] = lambda: None  # dream + curate pass
    health_check: Callable[[], list[Flag]] = lambda: []    # OS-health sense (returns crossed flags)
    # The thin-master/child model: separate processes palace spawns + drains (the edge monitor).
    children: list[ChildLike] = field(default_factory=list)
    # Write the metadata snapshot the edge monitor renders (no-op when [monitor] is off).
    snapshot: Callable[[object, list[Flag]], None] = lambda _run, _flags: None


def build_components(cfg: Config) -> Components:
    """Wire the full daemon: vault_sync (+watcher), the delegating Ambassador inbox, the
    delegated-task worker, and the trough dream/curate handlers — all on one supervisor."""
    from agents.ambassador import build_ambassador
    from core.curator import build_curator
    from core.dreaming import build_dreamer
    from core.ingest.sync import build_vault_sync
    from core.interface import CoreInbox
    from core.librarian import build_librarian
    from core.models import Registry, TwoSlotLoader
    from core.models.ollama_client import OllamaClient
    from core.stores.telemetry import open_store
    from core.typedshims import psutil
    from ops.gate import HumanGate
    from scheduler.cron import cron_handlers, enqueue_curate, enqueue_dream
    from scheduler.interface import (
        AMBASSADOR_KIND,
        AMBASSADOR_TASK_KIND,
        ambassador_inbox_handler,
        ambassador_task_handler,
        build_task_delegation,
    )
    from scheduler.queue import JobQueue
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
    delegate, pending = build_task_delegation(queue, router, gate=gate)
    ambassador = build_ambassador(cfg, delegate=delegate, pending_results=pending)
    inbox = CoreInbox(handoff=cfg.interface.handoff_dir, handler=ambassador.handler)
    task_librarian = build_librarian(cfg)

    handlers = {
        VAULT_SYNC_KIND: vault_sync_handler(build_vault_sync(cfg)),
        AMBASSADOR_KIND: ambassador_inbox_handler(inbox),
        AMBASSADOR_TASK_KIND: ambassador_task_handler(task_librarian),
        **cron_handlers(build_dreamer(cfg), build_curator(cfg)),
    }
    supervisor = Supervisor(queue=queue, loader=loader, handlers=handlers, telemetry=telemetry)
    watcher = build_vault_watcher(queue, router, cfg)

    def _housekeeping() -> None:
        enqueue_dream(queue, router)
        enqueue_curate(queue, router)

    def _catchup() -> None:
        enqueue_vault_sync(queue, router)   # reconcile the corpus; the Job return is discarded

    # The edge-monitor snapshot (Invariant 2): read-only views over the same stores → a metadata
    # JSON the networked monitor renders. Built whether or not the monitor runs (cheap); the writer
    # is a no-op target unless [monitor] is enabled.
    from core.attestation.store import open_attestation_store
    from core.dreams_view import DreamsView
    from core.ops_view import OpsView
    from core.stores.derived import open_derived_store
    from ops.ledger import open_ledger
    from ops.lifecycle.snapshot import build_status, write_status

    ops_view = OpsView.over(open_attestation_store(cfg), open_ledger(cfg))
    dreams_view = DreamsView.over(open_derived_store(cfg))

    def write_snapshot(run: object, flags: list[Flag]) -> None:
        mem_gb = round(psutil.virtual_memory().available / (1024 ** 3), 2)
        data = build_status(ops_view=ops_view, dreams_view=dreams_view, queue_depth=queue.depth(),
                            run=run, mem_available_gb=mem_gb, flags=flags)
        write_status(cfg.monitor.status_path, data)

    # Network-facing components run as supervised child PROCESSES (Invariant 2): the edge monitor.
    children: list[ChildLike] = []
    if cfg.monitor.enabled:
        import sys

        from config.loader import REPO_ROOT
        from ops.lifecycle.children import Child
        children.append(Child("monitor",
                              [sys.executable, str(REPO_ROOT / "scripts" / "monitor.py")]))

    return Components(
        supervisor=supervisor, watcher=watcher, queue=queue,
        enqueue_catchup=_catchup,
        enqueue_housekeeping=_housekeeping,
        health_check=health_check,
        children=children,
        snapshot=write_snapshot if cfg.monitor.enabled else (lambda _run, _flags: None),
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
    gate_cmd: tuple[str, ...] = ("uv", "run", "pytest", "-q", "-m",
                                 "not live and not podman and not needs_vault and not needs_restic")
    # remote half of the gate + release-on-deploy (ops/ci_witness.py). Subprocesses, not
    # imports: the witness talks to gitlab.com and must stay outside this sealed process.
    ci_check_cmd: tuple[str, ...] | None = ("uv", "run", "scripts/ci_witness.py", "check")
    ci_release_cmd: tuple[str, ...] | None = ("uv", "run", "scripts/ci_witness.py", "release")
    deploy_wait_s: float = 60.0
    deploy_poll_s: float = 0.5
    launchd_label: str = "com.mind-palace.palace"
    _stopping: bool = field(default=False, init=False)
    _run_id: int | None = field(default=None, init=False)
    _run: RunRecord | None = field(default=None, init=False)  # the active RunRecord (for snapshots)
    _components: Components | None = field(default=None, init=False)

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
        backend = c.watcher.start()
        print(f"watching {self.cfg.vault.path} (backend={backend}); supervising. "
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
            try:
                self._components.watcher.stop()
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
        managed = _launchd_managed(self.launchd_label)
        repo_plist = self.repo_root / "ops/lifecycle/com.mind-palace.palace.plist"
        installed = Path.home() / "Library/LaunchAgents/com.mind-palace.palace.plist"
        drift = (managed and repo_plist.exists() and installed.exists()
                 and installed.read_bytes() != repo_plist.read_bytes())
        if drift:
            print("deploy: plist drift detected — full reinstall cycle (bootout → cp → bootstrap).")
            _launchd_cycle(self.launchd_label, repo_plist, installed)
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

    def status(self) -> int:
        print("preflight:")
        print(run_preflight(self.cfg).render())
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
        return 0

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
