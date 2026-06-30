# Wiring audit — what is actually connected end-to-end (2026-06-29)

The system was built in parts; this is a deliberate trace of every subsystem from
**construction → live entry point → test**, to answer the real question: *is the work wired up,
or just present?* Each subsystem is one of:

- **WIRED** — driven by a live entry point (`scripts/palace.py` the launcher, `scripts/talk.py`,
  the watcher, a LaunchAgent) and tested.
- **DANGLING** — built + tested, but **no live driver invokes it yet**. The honest gaps.
- **FLAG-OFF** — intentionally dormant behind a switch; not a gap.

The live entry points are: **palace** (`ops/lifecycle/launcher.py` → supervisor + watcher +
housekeeping + OS-health), **talk.py** (in-process Ambassador), the **LaunchAgents** (vault,
backup), and the **scripts/**.

---

## WIRED (live, end-to-end)

| Subsystem | Driver | Notes |
|-----------|--------|-------|
| Vault ingest + watcher | palace → `vault_sync` job → supervisor | auto-ingest on change; attested; catch-up sync on start |
| Mirror (`MirrorView`) | dreamer / curator / librarian read it | authored-only firewall, structural |
| Librarian retrieval | Ambassador + the delegated-task worker | grounded, self-checked |
| Ambassador (5 paths) | palace inbox + talk.py | attested; captures dialogue as authored-dialogue |
| Scheduler / supervisor / queue / router | palace | cooperative, job-boundary; foreground gate |
| Dreamer + Curator | **palace housekeeping** (every 6h, trough-gated) | attested. *Newly wired — before palace nothing enqueued them periodically* |
| Dreams surfaced | Ambassador `DREAMS` path → `DreamsView` over `DerivedStore` | mirror-not-oracle; cites spanned notes. *Closed DANGLING #1* |
| Edge monitor (dashboard + chat) | palace child process → `edge/monitor` over the snapshot + handoff | Tailscale-bound; reads `status.json`, relays chat; no core import. *Closed DANGLING #6 + the dashboard* |
| Vault scoped-token mechanism | factory mints+binds+attests-accessor; `MintedAgent.read_secret`→`get_secret(token)` | §2 lifecycle live + tested; first consumer = the correlator (Track D). *Closed DANGLING #4 (mechanism)* |
| Attestation chain | written by vault_sync / dreamer / curator / Ambassador | read by the OpsView (Ambassador "status") |
| Sandbox (broker / podman) | `run_python` tool + `scripts/sandbox.py` | **empirically verified** (7 podman e2e); data-piping + libs image + WASM runner finalized |
| OS-health watchdog | **palace serve loop** (sense memory + report) | *Newly wired — was built but never called* |
| Self-knowledge (curated) | Ambassador EXPLAIN path | needs `scripts/ingest_self_knowledge.py` run once |
| Backups (restic→S3) | `com.mind-palace.backup` LaunchAgent | daily 03:30 |
| Vault / secrets | `get_secret(name, token)` seam | enabled; mint-capable |
| Lifecycle | `palace start/stop/status/reset` | run-ledger pins each run to its commit; graceful drain; recovery |

---

## DANGLING — the honest remaining gaps (built + tested, no live driver)

These are real: the code exists and is correct, but nothing yet *calls* it in a live path.
Ordered by value. (DANGLING #1 dreams, #4 vault tokens, #6 remote gateway were closed 2026-06-29
— see WIRED above; the three below remain.)

1. **No agent autonomously USES the sandbox.** It is reachable (the `run_python` tool +
   `scripts/sandbox.py`) and capable (data-in, libs, verified), but no live agent *writes and
   runs* analysis code in conversation. The factory (mints `data_analyst`/`coder` with
   `run_python`) is built but undriven; the Vault scoped-token mechanism (now wired) is waiting
   for its first consumer here. *Next:* the correlator / a data-analyst-in-conversation path —
   exactly the "dreamer finds patterns in IoT data, cross-checks the knowledge graph" example.
   This is **Track D** (observed + correlator), the owner's Apple Health example.
2. **The research airlock has no driver.** core→bridge→fetcher is built and applied, but nothing
   live emits de-identified criteria + polls results. *Next:* a research/advisor agent (Track D)
   that calls `librarian.research_criteria` → `ResearchAirlock` (often the back half of the
   correlator: a health pattern → a de-identified question → ranked literature).
3. **No auditor reads the attestation chain back.** Attestations are written (now including the
   `mint_token` accessor) but nothing systematically verifies them (a flight recorder no one
   plays). *Next:* **A3** auditor agent (Track A) — trough-scheduled, read-only, raises findings;
   a natural reader of the Vault denial/accessor signal too (vault-runtime-auth.md §6).

---

## FLAG-OFF (dormant by design — not gaps; don't flip without a deliberate session)

- **Dream R&D R0/R1** — `[dream_rnd] enabled=false`. Live dreaming uses the Phase-7 Dreamer.
- **Self-modification loop** — `[selfmod] enabled=false`, not in cron; nothing autonomously proposes.
- **WhatsApp adapter** — opt-in stub (Invariant 11).
- **WASM substrate** — `[sandbox] runtime="podman"`; activate with a WASI `python.wasm` (runbook).
- **Edge monitor** — `[monitor] enabled=false`. Built + supervised when on; bind `host` to the
  Tailscale IP to reach it from the phone. Off by default (network surface = opt-in).
- **Vault credential grants** — `[secrets].grant_roles=[]`. The mint→read mechanism is wired; a
  minted agent gets a token only for a role the owner lists (recommended `["correlator","advisor"]`).

---

## What this session changed

Closed/finalized (2026-06-29 sandbox session): the **podman empirical gap** (E1 — 7 live isolation
tests pass); the sandbox is now **capable** (data-piping → `/tmp/input`, scientific-libs image, the
real **WASM runner** + `RoutingRunner`) and **usable** (`scripts/sandbox.py`); **dreamer/curator are
now driven** (palace housekeeping); the **OS-health watchdog is now wired** into the palace loop.

Closed (2026-06-29 wiring session): **dreams surfaced** (Ambassador `DREAMS` path, DANGLING #1);
**Vault scoped-token mechanism** threaded into factory dispatch (DANGLING #4 — mechanism live, first
consumer is Track D); **the edge monitor** — dashboard + chat over Tailscale as a palace-supervised
child process (DANGLING #6 + the dashboard). Three DANGLING items remain (above), and they collapse
toward **one** capstone: the **Track D correlator** is the autonomous sandbox driver (#1), consumes
the Vault grant, and forms the de-identified question that drives the airlock (#2); the auditor (#3)
is the independent read-back. Each is a self-contained next step, not a half-built mess.
