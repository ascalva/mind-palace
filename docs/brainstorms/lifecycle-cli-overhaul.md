# Brainstorm — the lifecycle CLI overhaul (`palace` control, cleanup, status, diagnostic)

Topic home for the operational-lifecycle work the owner opened 2026-07-13. Grows from
finding-0066 (the `palace down/up/restart` gap) + an owner directive to prune dead options,
enrich `status`, and add a thorough `diagnostic` integrity check. Concrete ops/infra — no
fable-vet, no ratified design note needed; graduates directly into build plans.

## 2026-07-13 — capsule: the directive + the investigation

**Owner directive (verbatim intent).** "Start the work on start/stop, and remove any options
that are not in use at all or not needed — the dashboard never actually worked, and I would
want to completely redo it in the future. I also want `status` to show more information about
the system, or maybe a `diagnostic` subcommand that does a full integrity check." On the
diagnostic: "validate all ingestion sources are up to date, the current code is loaded, no
missing notes, no in-between state, nothing corrupt, core integrity — a thorough check."

**Investigation (grounded this session, read-only).**

- **CLI surface today** (`scripts/palace.py`): `{start | stop | status | reset | deploy}` +
  flags `--force / --confirm / --skip-tests`. Thin dispatch → `ops/lifecycle/launcher.py`
  (`build_launcher()` → `.start/.stop/.status/.reset/.deploy`). `seal()` (Inv 1) runs first.
- **KeepAlive semantics** (`com.mind-palace.palace.plist`): `KeepAlive=true`, `RunAtLoad=true`,
  `ThrottleInterval=10`, `ExitTimeOut=120`, `ProcessType=Background`, LaunchAgent (`gui/$uid`).
  So a bare `stop` under KeepAlive is *restarted by launchd* — "maintenance down" needs a
  `bootout` wrapper, "up" a `bootstrap`, distinct from the operational `stop` (finding-0066).
- **The dead dashboard footprint** (~6 files): `edge/monitor/{server,page,__init__}.py`,
  `scripts/monitor.py`, `MonitorConfig` + `[monitor]` (`config/{loader,defaults}`), and launcher
  wiring — it spawns the monitor as a supervised **child process** (`launcher.py:238-244`,
  `ops/lifecycle/children.py`) and writes a **status snapshot** JSON (`launcher.py:234`,
  `write_status`, `ops/lifecycle/snapshot.py`). `enabled=false`; never worked; owner will redo
  it later from scratch. **KEY INSIGHT:** the status snapshot the monitor *would* render
  (queue depth, run state, …) is exactly the data the enriched `status`/`diagnostic` needs —
  **repurpose the snapshot, don't delete it**; delete only the network-facing monitor + its child.
- **Run-ledger health** (`data/runs.sqlite`, 16 runs): **zero unclean shutdowns in real
  operation**; recovery mode fired exactly once (run 8, 2026-07-11 06:57), inside a cluster of
  short runs that morning — a deliberate recovery-path *test* during the lifecycle install, not a
  real power loss. Every completed run was clean. (Answers the owner's recovery-history question.)

**Sleep behaviour (context, already answered to the owner).** LaunchAgent holds no power
assertion → does not fight sleep; on lid-close/battery the process freezes in RAM and resumes on
wake (work due during sleep is deferred, not lost). A full battery-death is an unclean kill →
`RunAtLoad`/`KeepAlive` restart on next login, but it comes up in cautious **recovery mode**
(scheduler halted, watcher off, read-only) awaiting an owner `--force`.

## The shape — two session-sized plans

**bp-030 — operational control + dead-dashboard removal + richer status** (this graduates first).
1. `down` / `up` / `restart` — KeepAlive-aware `launchctl bootout`/`bootstrap` wrappers so
   maintenance-down ≠ operational-stop (finding-0066). `restart` = down→up (or a deploy-style
   cycle). Guard the LaunchAgent-not-installed case.
2. **Prune the edge monitor** — delete `edge/monitor/**`, `scripts/monitor.py`, `MonitorConfig`
   + `[monitor]`, and the launcher's monitor-child spawn. **Preserve** the status-snapshot
   writer (`snapshot.py` / `write_status`) — repoint it to feed `status`. Verify `edge/monitor`
   has no other importers; the child-supervision (`children.py`) stays if other children use it,
   else simplify.
3. **Enrich `status`** — surface the snapshot + ledger: run state (pid, commit, clean/recovery),
   running-code-vs-HEAD gap, queue depth, watcher/ingestion freshness, last dream, resident
   models/RAM headroom, drift gauge. Read-only, fast.

**bp-031 — the `diagnostic` subcommand (thorough whole-system integrity sweep)** (graduates next;
owner's priority, fully scoped here). A read-only, exit-code'd report across:
- **Fixed-point integrity** — Constitution fingerprint matches; golden set intact; attestation
  chain continuous (no gaps/tamper). The sacred fixed points are unaltered.
- **Store + firewall health** — every store opens + row counts sane; import-firewall (Inv 2)
  holds; provenance firewall (`CURATED`/`OBSERVED` ∉ mirror) intact; no dangling curated
  `store_ref` (Item-30 guard); no dangling/orphaned derived rows.
- **Ingestion freshness + completeness (owner emphasis)** — running code == HEAD (or the
  per-commit projection is caught up); vault ↔ raw store ↔ vectors are consistent (no missing
  notes, no orphaned projections); **no in-between / partial state**; content-addressing holds
  (nothing corrupt); queue not wedged.
- **Runtime + drift** — preflight (Ollama/Vault/podman), resident-model/RAM ceiling (Inv 8),
  drift gauge, last-dream/ingestion timestamps fresh.
- **`--deep` (slow) mode** — re-verify content hashes end-to-end, re-run the type-gate +
  import-lint, replay attestation signatures. Default run is fast; `--deep` is thorough.

## Parked / open for the plans

- **Split vs. one plan:** bp-030 (control+cleanup+status) and bp-031 (diagnostic) are separate
  session-sized units; the diagnostic is large enough to stand alone. `status` and `diagnostic`
  share the snapshot-reader seam — build `status` first (bp-030), reuse it in `diagnostic`.
- **`restart` semantics:** plain down→up, or a `deploy`-style cycle onto HEAD? Default: plain
  cycle; deploy stays its own owner-gated command.
- **Tier:** opus/high — touches `launcher.py` (invariant-adjacent, the seal/supervisor boundary)
  + a Zone-B deletion. Scrutinized build. **write_scope MUST list test paths** (finding-0072).
