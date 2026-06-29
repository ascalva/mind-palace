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
Ordered by value.

1. **Dreams / curator findings are generated but never SURFACED.** The dreamer + curator now run
   (palace housekeeping) and write `interpreted` artifacts to the `DerivedStore` — but no path
   shows them to the owner. The Ambassador's retrieve is mirror-only (authored); there is no
   "what patterns have you found lately?" read over the `DerivedStore`. *Next:* an Ambassador
   `DREAMS` read path (render mirror-not-oracle). Small, high-value — without it the whole
   dreaming layer is invisible.
2. **No agent autonomously USES the sandbox.** It is now reachable (the `run_python` tool +
   `scripts/sandbox.py`) and capable (data-in, libs, verified), but no live agent *writes and
   runs* analysis code in conversation. The factory (mints `data_analyst`/`coder` with
   `run_python`) is built but undriven. *Next:* the correlator / a data-analyst-in-conversation
   path — exactly the "dreamer finds patterns in IoT data, cross-checks the knowledge graph"
   example. This is **Track D** (observed + correlator).
3. **The research airlock has no driver.** core→bridge→fetcher is built and applied, but nothing
   live emits de-identified criteria + polls results. *Next:* a research/advisor agent (Track D)
   that calls `librarian.research_criteria` → `ResearchAirlock`.
4. **Vault scoped tokens are mintable but unthreaded.** `mint_token` works; no live agent passes
   a token through `get_secret(name, token)` for a scoped read. *Next:* thread tokens into the
   factory's agent dispatch (the "creds only via explicit scoped grant" path).
5. **No auditor reads the attestation chain back.** Attestations are written but nothing
   systematically verifies them (a flight recorder no one plays). *Next:* **A3** auditor agent
   (Track A) — trough-scheduled, read-only, raises findings.
6. **No remote interface gateway daemon.** palace drains the Ambassador inbox, but nothing writes
   to the handoff from a network adapter over Tailscale — so phone/remote chat isn't live;
   `talk.py` (in-process) is today's surface. *Next:* the stdlib HTTP gateway over Tailscale
   (runbook follow-up).

---

## FLAG-OFF (dormant by design — not gaps; don't flip without a deliberate session)

- **Dream R&D R0/R1** — `[dream_rnd] enabled=false`. Live dreaming uses the Phase-7 Dreamer.
- **Self-modification loop** — `[selfmod] enabled=false`, not in cron; nothing autonomously proposes.
- **WhatsApp adapter** — opt-in stub (Invariant 11).
- **WASM substrate** — `[sandbox] runtime="podman"`; activate with a WASI `python.wasm` (runbook).

---

## What this session changed

Closed/finalized: the **podman empirical gap** (E1 — 7 live isolation tests pass); the sandbox is
now **capable** (data-piping → `/tmp/input`, scientific-libs image, the real **WASM runner** +
`RoutingRunner`) and **usable** (`scripts/sandbox.py`); **dreamer/curator are now driven** (palace
housekeeping); the **OS-health watchdog is now wired** into the palace loop. The six DANGLING items
above are the honest frontier — each is a self-contained next step, not a half-built mess.
