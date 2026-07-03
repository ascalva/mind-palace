# Build Progress

Terse, append-only log maintained by the building agent. **One entry per phase/checkpoint:** what was built, what was verified against the gate, what's next, and any decisions made. A fresh build session resumes from this file + `CLAUDE.md` + the current phase's section of `docs/BUILD-SPEC.md` — not by replaying chat history.

Keep entries short. Cite paths, not contents.

---

**Earlier history (Phase 0 → Phase 10, the numbered-phase build, complete 2026-06-28) rotated to
`docs/archive/PROGRESS-phases-0-10.md`.** Append-only preserved — nothing rewritten, only
relocated for session-load size (docs cleanup, 2026-07-03). This file continues below with the
forward layer.

---

## Forward layer (Track items, not numbered phases)

### F9 — dreamer output-quality suite, real binding (Track F)

**Status:** COMPLETE (2026-06-28). Item spec: `design-notes/dreamer-quality-suite-evaluation.md`
(adopt) + `ROADMAP-V1.md` Track F. Bind the signal-vs-noise / apophenia suite to the LIVE
Dreamer/DerivedStore and run it. No flags flipped; no live/R&D code changed.

**Built**

- `tests/fixtures/dreamer_adapter.py` — `MindPalaceDreamerAdapter` binding the suite's
  `DreamerAdapter` protocol to the live machinery: real `Dreamer.clusters()` over a `MirrorView`
  (authored-only, structural), real `cluster_notes`/`note_centroids`/`similarity_matrix`, real
  `grounding_score` + `core.recursion`. Only the embedder + synthesizer are deterministic offline
  stand-ins (the real ones need Ollama; the quality layer grades structure, not prose). `run()` =
  fast clustering→Dreams; `persist_dreams()` = full live `dream()` into a real `DerivedStore`;
  `run_without_grounding()` = the decorative-citation negative control. NO `rate_blind` (value
  claim stays honestly open). `LexicalEmbedder` = offline, similarity-PRESERVING (the shipped
  `FakeEmbedder` hashes whole strings → useless for clustering); per-batch presence vectors,
  clustering threshold tuned to 0.50 (single-linkage is chain-prone on lexical vectors; 0.50 is
  the stable band where noise can't bridge themes AND calibration has ≥6 dreams).
- **Resolved the open `g` question (review note 2 / §4) IN THE BINDING:** confidence
  `c₀ = g·(1+λ(|Agr|−1))` with `g = grounding_score · cohesion · size_factor` — folds in support
  COUNT (`size_factor = min(1,(n−1)/4)`), so a 2-note cosine-1.0 coincidence scores weak (the
  apophenia failure in miniature). The live adjudicator's `g = grounding_score` (resolvability
  only) would make confidence flat and FAIL calibration — exactly what the suite is built to flag.
  Reports the base confidence c₀ (depth-uniform live run, d=1 = `AUTHORED_LEAF_DEPTH`); γ^d
  cross-depth decay is the recursion/drift suite's job (binding-seam note 3). **NOT changed in the
  flag-OFF `core/dreaming/adjudicator.py`** — recorded as a deferred R&D follow-up (runbook Hook 2).
- `tests/quality/test_dreamer_quality.py` (the adopted contribution) — `_load_adapter` →
  parametrized `adapter` fixture over `[ref]` + `[real]`, so the whole suite runs against BOTH the
  reference fake and the real binding; env `MIND_PALACE_DREAMER_ADAPTER` still forces one. Adopted
  ruff-clean (mechanical, behavior-preserving). `THRESH` left as the tuning surface (untouched).
- `tests/quality/test_real_dreamer_binding.py` — end-to-end proof the binding reaches the real
  Dreamer AND DerivedStore: full `dream()` persists INTERPRETED-only, `derived_from` = authored
  leaves (G2), grounded self-check passes, fast `run()` ⇄ persisted grounding agree, idempotent,
  deterministic. `tests/quality/conftest.py` + `quality` marker (pyproject).

**Verified**

- `tests/quality/`: **22 passed, 4 skipped**. Real binding `[real]`: 9 pass + 1 skip
  (`beat_decoys_under_blind_rating` — `rate_blind` unwired = value claim honestly OPEN). The 2
  drift-deferred tests skip (need A1; move to `longitudinal/` then). Calibration `[real]`: 7
  grounded dreams, top−bottom precision margin = 1.0; noise max-conf 0.25 (≤0.70); planted recall
  1.0; real ≥ TF-IDF baseline; paraphrase stability 1.0.
- Full logic suite **372 passed, 4 skipped** (non-quality unchanged at 350 — no regressions; F9
  adds +22 quality). ruff clean (incl. the adopted file); import firewall (I2) green; core reaches
  no network. Everything deterministic (fixed seeds) → green is stable.

**Owner-deferred (build/owner boundary; documented in runbook → "Dreamer output-quality suite")**

- **Hook 1:** wire `rate_blind` to a periodic blind-rating ritual — the ONLY path that validates
  the value claim. A green proxy is not a proven value-claim; keep it open until the rating runs.
- **Hook 2:** fold support count into the adjudicator's `g` when the C1/R2 R&D path is activated
  (a deliberate R&D session — not now; flag stays OFF).
- Optional full-fidelity run against the real Ollama embedder (`needs_models`) = the THRESH
  harness-tuning step.

**Next:** owner picks the next forward item. Per ROADMAP-V1 ordering, **A1 (the drift gauge)** is
the keystone — it unblocks R3/C2 recursion AND F4 drift-trajectory asserts (and would unlock F9's
two drift-deferred tests). Track B (the Ambassador) is the other high-value parallel.

### A1 — the drift gauge (Track A, the keystone)

**Status:** COMPLETE (2026-06-29, same session as F9 — owner said "continue"). Item spec:
`design-notes/alignment-subsystem.md` §2/§5 + BUILD-SPEC §15 + gap **G4**. Realize the §15 drift
metric `D(t)=d(μ(s_t),B)`. **Closes G4** (was OPEN). Detection only — alters no live behavior
(self-mod is flag-OFF).

**Two owner decisions (asked, not guessed — `AskUserQuestion`, 2026-06-29):**
- **Metric:** one-sided L2 deterioration distance — each axis contributes only its bad-direction
  deviation past baseline, normalized by a blessed per-axis tolerance, combined by L2; healthy
  improvement = 0 drift; Constitution-fingerprint mismatch = hard trip (D=∞).
- **Θ:** ship **Θ=1.0**, blessed in `baseline.json`, F4-calibrated-then-re-blessed. A human-set
  frozen fixed point — excluded from the lever set (structurally: levers only tune `[dreaming]`).

**Built**

- `eval/drift.py` — the gauge: `Profile` (μ = capability rates ⊕ Constitution conformance, G4's
  "rates ⊕ conformance vector"), `Axis` (flat + additive so A2 appends structural axes as data),
  one-sided `deterioration()`, `drift()` (L2 + the conformance hard-trip), `DriftReport`,
  `constitution_intact()` (live fingerprint vs blessed; no-blessed ⇒ intact, no false trip),
  `drift_from_report()` (reuses one golden report) + `measure_drift()` (standalone entry for the
  A2 report / F4 harness). Reuses `eval.golden` + `core.constitution.constitution_fingerprint`.
- `eval/golden/baseline.json` — extended with a blessed `drift` section (per-axis tols, Θ=1.0,
  the Constitution fingerprint `1818a46e…`). Owner-blessed/frozen, never auto-modified (I9);
  `load_baseline()`/`regressions()` untouched (backward-compatible).
- `ops/selfmod.build_golden_validator` — `drift_within_tolerance` is now the REAL gauge
  `D(Δ·s) ≤ Θ` (`drift_from_report`), the honest realization of the gate's drift conjunct (G4/G5),
  replacing the rolling-regression stand-in (now retained as advisory `metrics`). Self-mod flag-OFF
  ⇒ no live behavior change.
- `docs/WHITEPAPER-FORMAL-PROPERTIES.md` — **G4 OPEN → CLOSED** with the realization.

**Verified**

- `tests/unit/test_drift.py` (15) + `tests/property/test_drift_property.py` (3 Hypothesis:
  D≥0, within⇔D≤Θ, at-or-better⇒0, monotonic) + `tests/integration/test_selfmod.py` (+1: the gate
  conjunct is the real gauge). Gauge behaviors proven: at-baseline D=0; healthy improvement D=0
  (one-sided); one-tol drop D=1.0=Θ (within, boundary); 2-tol D=2.0 (out); L2 combine = √2;
  Constitution breach D=∞ (hard trip regardless of perfect capability).
- Full logic suite **372 → 391 passed (+19)**, 4 skipped. ruff clean (whole tree); import firewall
  (I2) green (eval may import core; core still reaches no network).

**Owner-deferred / next:** Θ is a placeholder until **F4** calibrates it on observed curves (then
re-bless in `baseline.json`); re-bless the Constitution fingerprint whenever `CONSTITUTION.md` is
amended (runbook → "Alignment drift gauge"). A1 now unblocks **R3/C2** (recursive dreaming),
**F4** (drift-trajectory asserts), and F9's two drift-deferred tests (move them to
`longitudinal/` when F4 lands). Natural next: **A2** (structural detection + the alignment report,
extends μ) or **F4** (uses the gauge), or Track B (Ambassador).

### Track B — the Ambassador (the Voice), END TO END (B0–B5 + cross-cutting)

**Status:** COMPLETE (2026-06-29; owner override: build the whole track in one session so the owner
can start talking to the system — one-item-per-checkpoint suspended for Track B only). Notes (in
precedence order): `ambassador-as-reasoning-agent.md` (authoritative), `ambassador-interpretation-and-flow.md`,
`nervous-system-and-ambassador.md` §4. **No feature flags flipped** (dream R&D OFF, self-mod fail-closed
OFF — untouched); nothing auto-activates (the CLI is the surface; the scheduled daemon is a runbook
follow-up). The Ambassador is **core-side, reaches no network** (verified: no `core/`|`agents/` → `edge`).

**Built**

- **B0 — the §1 provenance split (the structural decision already made — executed, not re-derived).**
  `core/provenance.py`: `AUTHORED` → `AUTHORED_SOLO` + `AUTHORED_DIALOGUE`, add `CURATED`;
  `MIRROR_READABLE = {AUTHORED_SOLO, AUTHORED_DIALOGUE}` (curated/observed/interpreted excluded —
  matches the formal spec). Blast radius exactly as mapped: `ingest_note` is now provenance-PARAMETRIC
  (default `AUTHORED_SOLO`); `catalog.py` DDL default + `record` default `authored-solo`; `core/mirror.py`
  unchanged (derives from `MIRROR_READABLE`). `VectorStore.relabel_provenance` + `VaultCatalog.relabel_provenance`
  (delete-then-add / UPDATE; idempotent) back `scripts/migrate_provenance_split.py` (dry-run default,
  `--apply`, same-trust-tier relabel — NOT a §8-firewall promotion, so safe + ungated).
- **B3 — `core/ops_view.py` `OpsView`** (read-only operational introspection): binds ONLY the *read*
  callables of the attestation store + proposal ledger + drift gauge — no `approve`/`deny`/`append`/
  `mark_*` on its surface (static + guard tier; honestly weaker than MirrorView's structural copy, and
  labelled so). `narrate()` renders status in plain language with NO internal nouns (tier/job/queue/
  credentials), the §4 register; `_drift` is optional (drift not computed per-chat).
- **Capture + curated.** `core/ingest/dialogue.py` `DialogueCapture.capture()` stores the owner's
  message as `AUTHORED_DIALOGUE` through the SAME pipeline as vault ingest (parametrized provenance —
  not a bespoke writer), mirror-readable + retrievable, idempotent, attested (`action=capture`).
  `core/ingest/curated.py` ingests CONSTITUTION/CONVENTIONS/`docs/**` as `CURATED` (own graph, never
  the mirror — `curated ∉ MIRROR_READABLE`); the "explain yourself" path is a deliberate, non-default
  `Librarian.retrieve(provenances={CURATED})`.
- **B2/B5 — `agents/ambassador/`** (the reasoning agent, pinned tier; persistent first-class role,
  DELIBERATE empty scope — no `run_python`, no write — expressed as a `RoleTemplate` so the §10 ceiling
  guards it). `intent.py`: deterministic floor (RETRIEVE/EXPLAIN/STATUS/TASK/CAPTURE) + model-earned
  fallback, separately testable ("floor for the obvious, mind for the rest"). `agent.py`: the five
  paths — RETRIEVE (mirror) / EXPLAIN (curated) / STATUS (ops-view, no model) / TASK (gate→queue +
  effort narration) / CAPTURE (store + ack); B5 = context assembled through the §13 `Budgeter` every
  turn (agent chooses ContextParts, budgeter enforces the window); grounding self-checked, ungrounded
  answers flagged-not-hidden; per-step attestations; in-memory recent-history (older context re-retrieved
  from `authored-dialogue`, no double-store). `policy.py`: effort narration (pure fn, no leaks) +
  earned-interruption policy (off|earned_only|verbose, default earned_only; expected updates always
  delivered, unprompted gated). `[ambassador]` config + `AmbassadorConfig`.
- **B1 — wiring + CLI.** `scheduler/router.py`: `ambassador` kind → pinned tier @ REACTIVE,
  `ambassador_task` → synthesis @ background. `scheduler/interface.py`: inbox-drain + delegated-task
  handlers, the `task→gate→queue` delegation closures (the Ambassador never imports the scheduler —
  injected), and `ConversationRuntime`/`build_conversation_runtime` (the in-process driver).
  `core/interface.build_core_inbox` rewired to the Ambassador (lazy `agents` import — no load-time
  cycle, no layering inversion). `scripts/talk.py` (REPL, `--offline` deterministic mode = the
  verification + day-one surface), `scripts/ingest_self_knowledge.py`.

**Verified**

- Full logic suite **391 → 436 passed (+45)**, 4 skipped — no regressions. New: integrity
  (`test_provenance_split` 7, `test_ops_view` 4, `test_curated_firewall` 3), unit (`test_ambassador_intent`
  9, `test_ambassador_policy` 4), integration (`test_dialogue_capture` 3, `test_ambassador` 10,
  `test_ambassador_budget` 3, `test_ambassador_conversation` 2 = the DoD as a test). Integrity gate **43**
  green; import firewall (I2) green; ruff clean tree-wide; existing split-touched tests relabeled.
- **Actually ran it** (the "interact meaningfully" bar): `scripts/talk.py --offline` drives a real
  multi-turn conversation — retrieve (grounded, cited), explain (curated), status (plain narration),
  task→deferred result on the next turn, capture → the exchange lands as `authored-dialogue` and
  surfaces on a later retrieval (capture loop confirmed live, not just unit-tested).
- Env note: the venv was rebuilt mid-session (uv.lock appeared) and lost pytest/ruff; reinstalled both
  to verify. Run tests via `.venv/bin/python -m pytest`.

**Owner-deferred (build/owner boundary)**

- ⚠️ **Run the provenance migration** — `scripts/migrate_provenance_split.py --apply` (runbook →
  "Provenance spectrum split"). The dry-run found **918 legacy `authored` vector rows + 135 catalog
  rows** in live data; until relabeled they are NOT mirror-readable, so the live mirror reads empty.
  Idempotent; restic snapshot is the safety net.
- Run `scripts/ingest_self_knowledge.py` (needs Ollama) so EXPLAIN answers from the real docs.
- Optional: the Tailscale-reachable local HTTP front end (lean: left as a runbook note — the CLI meets
  the bar without an exposure decision); the scheduled-daemon wiring (handlers exist in
  `scheduler/interface.py`, not enabled).

**Next:** owner picks. Track B done unblocks daily use. Natural neighbors: **A2** (structural detection
— extends the drift μ the ops-view can already narrate) or **F1–F3** (the harness). Per-category
interruption sensitivity is a documented future extension (single dial shipped).

### Operational lifecycle (`palace` launcher) + fresh-start (owner-requested, not a track item)

**Status:** COMPLETE (2026-06-29). Owner asked for (a) a one-command start/stop for the whole system
and (b) a clean wipe + re-point to a new Synctrain-over-Tailscale notes location. Both done.

**Built**

- `ops/lifecycle/` + `scripts/palace.py {start|stop|status|reset}` — the whole mind-palace as ONE
  supervised process (supersedes the standalone `scripts/watch.py` / `com.mind-palace.watch`).
  `runs.py` = a run ledger (`data/runs.sqlite`) pinning each run to its **git commit** + dirty flag +
  clean/unclean shutdown. `preflight.py` = ensure-own + **verify-externals fail-closed** (Ollama
  `version()`, Vault `/sys/health`, podman `which`; required ✗ refuses start, optional = warn) —
  owner's chosen scope (manage own; verify, don't manage, the external daemons). `launcher.py`:
  `start` (preflight → record run → catch-up vault sync / empty-cache rebuild → supervise queue +
  watcher, with vault_sync + dream/curate + the delegating Ambassador inbox + `ambassador_task` all on
  one supervisor) with a **graceful SIGTERM/SIGINT shutdown hook** (drain at a job boundary → mark run
  clean — the ASG-lifecycle-hook analog); `stop` (signals the live run's pid); `status`; `reset` (the
  surgical corpus wipe). **Recovery mode** on an unclean prior run (scheduler halted, read-only;
  `--force` resumes) — the boot-time half of the A4 tamper response. launchd plist
  `ops/lifecycle/com.mind-palace.palace.plist` (owner installs; `ExitTimeOut=120` drain window).
- **Self-mod persistence answered + documented** (owner's question): tuned knob value →
  `config/levers.toml` overlay (a file, not a db — `local.toml` always wins; delete = revert); the
  propose→validate→rollback history → existing SQLite `data/selfmod_ledger.sqlite`; a restart re-reads
  the overlay and resumes. The new run-ledger correlates a tuned knob to the commit/run it happened on.

**Verified**

- `tests/integration/test_lifecycle.py` (10): run-ledger clean/unclean detection (the recovery basis),
  preflight fail-closed aggregation, launcher start→serve→mark-clean (fakes, no models), recovery on
  unclean prior + `--force` resume, and **`reset` wipes the corpus but NEVER `data/vault`** (Raft) — the
  load-bearing guard. Logic suite **436 → 446 (+10)**; ruff clean; preflight green against the live box
  (Ollama 0.30.7, Vault health 200, podman present).

**Executed (operational, owner-requested)**

- `[vault] path` → `~/.mind-palace/vault/janus_notes` (config/local.toml) — ingest scoped to exactly
  the new synced subdir. Retired the old `com.mind-palace.watch` LaunchAgent (superseded). Ran
  `palace reset --confirm`: **hard-wiped the corpus** (raw + vectors + catalog + stale attestation chain
  + queue = 9 paths); **production Vault Raft, ledgers, telemetry, backups untouched** (the guard held);
  restic daily snapshot is the recovery net. A fresh re-ingest writes `authored-solo` natively → **the
  provenance-split migration is now MOOT** (no `--apply` needed).

**Owner-deferred / next**

- ⚠️ Re-export your real notes into `~/.mind-palace/vault/janus_notes/` + point Synctrain there, then
  `palace start` (re-ingests as authored-solo). `janus_notes/` still has 2 leftover 7–9 byte test stubs
  from 06-27 — delete them (or let Synctrain reconcile) so they aren't ingested as junk.
- Optional: install `com.mind-palace.palace.plist` for an always-on daemon; run
  `scripts/ingest_self_knowledge.py` so the Ambassador's EXPLAIN path has the curated docs.
- Future: a real cron cadence for dream/curate (currently a coarse in-loop interval); the full A4
  graduated tamper response (this is the boot-time recovery half); a final-snapshot shutdown hook
  (the `on_shutdown` seam is present, default off).

### Wiring audit + sandbox finalization (owner-requested, not a track item)

**Status:** COMPLETE (2026-06-29). Owner asked for a deep-dive on what's actually wired (fear of
built-but-dangling parts), to finalize the code-exec sandbox/WASM + libraries + data-piping, and to
clarify the watcher/process model.

**Deep-dive audit → `docs/WIRING-AUDIT.md`** (durable map: WIRED / DANGLING / FLAG-OFF for every
subsystem). Confirmed the fear is partly real. **DANGLING** (built+tested, no live driver):
(1) dreams/curator findings are generated but never *surfaced* to the owner; (2) no agent
autonomously *uses* the sandbox (the factory/run_python is built but undriven — Track D correlator);
(3) the research airlock has no live driver; (4) Vault scoped tokens are mintable but unthreaded;
(5) no auditor reads the attestation chain back (A3); (6) no remote gateway daemon (talk.py is the
surface). All six are self-contained next-steps, documented with recommended fixes.

**Finalized the sandbox (Track E E1/E2 + the owner's libs/data asks):**
- **E1 closed** — podman runs here (libkrun machine); `pytest -m podman` **7/7** (added data-in +
  vault-unreachable-with-inputs). Isolation now proven empirically, not just by construction. The
  stale "KNOWN ISSUE" runbook section marked RESOLVED.
- **Data-piping** — `ExecSpec.inputs` (name→text, 16 MB cap, name-safe) materialized at
  `/tmp/input/<name>` by `policy.compose_program` IN-BAND on stdin (NO host mount → the vault stays
  structurally unreachable; asserted). `run_python` tool + the new `scripts/sandbox.py` CLI thread
  it through. Verified live: a CSV piped in, summed in-sandbox → 42.
- **Libraries** — `ops/sandbox/Containerfile` (numpy/scipy/pandas/scikit-learn/cryptography) +
  `scripts/build_sandbox_image.sh`; `[sandbox] image` selects it (owner builds once; default stays
  slim so a fresh clone works). Wheels baked in → sandbox needs no network at run time.
- **WASM (E2)** — `WasmRunner` is now a REAL wasmtime/WASI implementation (was a NotImplementedError
  stub) + `RoutingRunner` (wasm for pure-compute python when available, else the verified podman);
  fail-closed `available()`. `[sandbox] runtime` ∈ {podman, wasm, routing} + `wasm_module`. wasmtime
  installed; activation needs an owner-placed `python.wasm` (documented). Isolation by absence of
  syscall imports — no preopens/sockets granted.
- **OS-health "agent" wired** — the `Watchdog` (built but never called) now runs in the palace serve
  loop: feeds `mem.available_gb` (psutil) + raises a low-headroom flag (sense + report; the loader
  already refuses ceiling-breaching loads). Closes a dangling end the owner named.

**Watcher/process-model clarification:** "retired the watcher" = booted out the *duplicate*
standalone `com.mind-palace.watch` LaunchAgent (else two watchers double-ingest). The watcher code
+ function live on, now *managed by* palace (started in serve, stopped in the graceful hook) — which
IS the thin-supervisor model the owner described. Agents (ambassador/dreamer) are in-process config
per BUILD-SPEC ("agents are config, not OS processes"), not separate daemons; Vault/Ollama are
external daemons palace verifies. No code change needed — palace already starts everything + tears
it down gracefully on stop.

**Verified:** logic suite **446 → 456 (+10)**: data-piping (`test_sandbox_policy` +6), WASM/routing
(`test_sandbox_wasm` +7), health-check wiring (`test_lifecycle`), minus overlap. podman e2e 7/7.
ruff clean tree-wide; import firewall green. Deps added to `.venv`: wasmtime (+ earlier pytest/
hypothesis/ruff after the mid-session venv rebuild). Owner command quick-reference added to the top
of `docs/runbook.md`; sandbox/WASM section added.

**Next (owner picks):** the six DANGLING items in `WIRING-AUDIT.md` — highest-value is surfacing
dreams (small) and the Track D correlator (the autonomous sandbox driver, the owner's IoT example).

---

## Forward layer — knocking out the DANGLING frontier (2026-06-29, owner override: multiple wins)

Owner steer: confirmed the thin-master/supervised-children runtime model (palace stays the master;
network-facing components become supervised child processes — forced by Invariant 2 + the model
ceiling, not a style choice); wants a small dashboard reachable over Tailscale; "knock out these
small but significant wins." Doing the self-contained core wins first, then the edge process.

**Win 1 — Surface dreams (WIRING-AUDIT DANGLING #1).** The dreamer/curator wrote `interpreted`
artifacts that nothing ever *showed*. New `core/dreams_view.py` `DreamsView` (read-only over the
`DerivedStore`, the OpsView move — binds `all`/`count`, no `add`/`reset` on its surface); a 6th
Ambassador intent `DREAMS` (`agents/ambassador/intent.py` cues + classifier line) → `_reflect_dreams`
→ `narrate_recent()`, **mirror-not-oracle** (frames dreams as the system's interpretation, cites the
spanned authored notes in [[brackets]], hands judgment back — §III.2 / §8 firewall). Wired in
`build_ambassador` (`derived=` injectable). Tests: `tests/unit/test_dreams_view.py` (+5, incl.
no-mutator guard), intent cases, `test_ambassador.py` DREAMS path (+2; deterministic, no model, not
captured, attested read). RETRIEVE stays mirror-only — firewall intact.

**Win 2 — Thread Vault scoped tokens into dispatch (DANGLING #4).** The §2 lifecycle primitives all
existed (`Supervisor.mint_token`, `get_secret(name, token)`, `Attestor.emit(vault_token_accessor=)`,
`FakeVault`); the glue did not. `MintedAgent` now carries `token` (off the prompt — `repr=False`,
never in `build_context`) + `accessor` (audit handle) + `grant()` + a **code-only** `read_secret(name)`
(the orchestration calls it; the model never sees the token — credentials are deliberately NOT a tool,
PRE_DECLARED_MAX unchanged). `AgentFactory` mints+binds+attests-the-accessor for a role in
`grant_roles` (fail-closed empty; `[secrets].grant_roles`/`token_ttl` config; `build_factory` wires
the backend+attestor only when `[secrets]` enabled). `read_secret`→`get_secret(name, token)` so the
agent holds only the token; Vault enforces scope (denied = opaque). Tests:
`tests/integration/test_factory_credential_grant.py` (+6) prove in-scope read, out-of-scope denial
(logged), ungranted/no-backend = no token, accessor-attested-not-token, token off prompt+repr.
Mechanism is now live end-to-end; its first *consumer* is the Track D correlator (Win 4) — owner
opts a role into `grant_roles` to activate (recommended `["correlator","advisor"]`).

**Verified (Wins 1–2):** logic suite **456 → 470 (+14)**; ruff clean (core/config/tests); import
firewall green (the two new core modules reach no network/edge). No flags flipped.

**Win 3 — the edge monitor process (DANGLING #6 + the dashboard).** The thin-master/child model the
owner confirmed, realized: palace stays the master and now spawns a SEPARATE child process for the
network-facing surface (forced by Invariant 2 — it can't share the sealed core). New `edge/monitor/`
(`server.py` = `MonitorApp` routing + `render_dashboard` + a `_Server` that skips `getfqdn`;
`page.py` = the HTML/CSS/JS asset): `GET /` dashboard + `GET /status.json` + `POST /chat`. It reads a
core-emitted snapshot file and relays chat over the existing interface handoff — **never imports core,
never reads a store**. Core side: `ops/lifecycle/snapshot.py` (`build_status`/`write_status` — METADATA
only: health, activity *shape*, queue depth, mem, dream counts; no note text). Supervision:
`ops/lifecycle/children.py` `Child` (injectable spawn; idempotent start; graceful SIGTERM→SIGKILL);
the launcher starts children in `_serve`, restarts a dead child, writes the snapshot every
`snapshot_interval_s` (5s), and drains children on the graceful shutdown. `scripts/monitor.py` is the
entry palace spawns (Zone B → deliberately NOT sealed). `[monitor]` config (OFF by default; bind
`host` to the Tailscale IP for the phone — the tailnet is the auth boundary). Tests: `test_children.py`
(+4), `test_monitor_server.py` (+5), `test_monitor_snapshot.py` (+2, incl. no-corpus-leak + chat
round-trip through a real handoff), `test_lifecycle.py` (+1, child start/stop + snapshot). **Real bug
found + fixed:** `HTTPServer.server_bind()` calls `socket.getfqdn(host)`, a reverse-DNS lookup that
hung **35s** on a DNS-less host — would stall `palace start`; `_Server` skips it.

**Verified (Win 3):** logic suite **470 → 482 (+12)**; **live HTTP smoke passed** (real socket: GET /
renders metrics, GET /status.json, POST /chat round-trips through the handoff → reply); ruff clean
tree-wide (asset lines isolated in `page.py` via a scoped per-file E501 ignore); import firewall green
(core still reaches no edge — the monitor is edge-only). No flags flipped (`[monitor]` off by default).

**Session total:** 456 → 482 (+26). DANGLING #1/#4/#6 closed; three remain (sandbox-driver, airlock
driver, auditor) and collapse toward the **Track D correlator** capstone.

**Next:** Win 4 — Track D correlator (autonomous sandbox driver + Apple Health `OBSERVED` ingest +
the de-identified airlock question). Owner prep: export Apple Health (`export.zip`→`export.xml`); to
use the dashboard now, set `[monitor] enabled=true` + `host=<tailscale-ip>` and `palace start`.

---

## `mind-palace` on PATH (2026-06-30, owner-requested, not a phase)

`bin/mind-palace` (new, executable): a bash shim that resolves its own real location (follows the
symlink), derives `REPO_ROOT` from that, so it works from any cwd without relying on `$PWD` (every
`scripts/*.py` already resolves its own paths from `__file__`, confirmed by tracing
`config.loader.REPO_ROOT`). Symlinked at `/opt/homebrew/bin/mind-palace` (already on PATH,
user-writable, no sudo). Initially just `start`/`stop`/`status`/`reset` → `palace.py`.

**Same day, follow-up ("I don't want to have to find those specific scripts every time"):** turned
it into a full dispatcher — a `case` statement covering every owner-facing script in `scripts/`
(`talk`, `monitor`, `sandbox`, `ingest`, `ingest-self-knowledge`, `migrate-provenance`, `purge-raw`,
`gen-attestation-keys`, `verify-attestation`, `check-imports`, `run-with-secrets`, `eval`,
`build-sandbox-image`, `keep-awake`, `watch` — `watch` prints a deprecation note pointing at `start`
before running). `start|stop|status|reset` keep the verb in argv (palace.py's own dispatch expects
it); every other verb is stripped before exec (the target script doesn't expect its own name as
argv[0]). `mind-palace help`/`-h`/`--help`/no-args prints the full table; an unknown verb exits 2 with
the same usage on stderr. **Real pre-existing bug found + fixed:** `scripts/check_imports.py` was
missing the standard `sys.path.insert(0, …)` repo-root line every sibling script has — it threw
`ModuleNotFoundError: No module named 'ops'` even run the old way (`./.venv/bin/python
scripts/check_imports.py` from the repo root, since Python puts the *script's own dir* on
`sys.path[0]`, not cwd). Fixed by adding the same path-insert line as every other script; verified
`mind-palace check-imports` now passes (`ops.import_lint`'s own `python -m` entry point, used by CI,
was never affected). **Verified:** `bash -n` syntax-clean; ruff clean (`bin/mind-palace` has no
extension so `ruff check .` correctly skips it — confirmed CI's actual invocation is unaffected);
full logic suite still 482/482; live-tested `status`/`sandbox`/`check-imports`/`verify-attestation`/
unknown-verb from `/tmp` in a fresh `zsh -l` shell. `docs/runbook.md` quick-ref + lifecycle section
updated throughout to `mind-palace <verb>`.

---

## Mathematical reframing — Prompt R0: notation wiring (2026-07-01, documentation only, zero runtime risk)

The first step of the companion-IV reframing (`docs/MATHEMATICAL-REFRAMING.md` §B.6 step 1–3, 5):
propagate the shared vocabulary. **Pure documentation — no code logic changed**; only comment
headers were added to code files. The five-families account (companion IV) now has a single glossary
and every load-bearing boundary states its object/invariant/enforcement in place.

**Built (5 deliverables):**
1. **`docs/NOTATION.md`** (new) — the one glossary: symbol ↔ code name ↔ object ↔ family, for every
   load-bearing symbol (ρ, π_MR, 𝒜, MAX, H, Σ, c, g, d, γ, λ, D(t), B, Θ, 𝔎, K_σ, ℋ, δ\*δ), grouped
   by family, plus a supporting-notation table (MR, μ, Δ/s/s′, G/G_now, |Agr|, Cit/Ret). **Referenced
   from the top of all six whitepapers** (I, technical, II, III-math, III-build, IV). Family 5 symbols
   are marked **NOT YET BUILT** honestly (`core/complex/` does not exist; `ℋ` is only *seeded* today by
   `derived_from`).
2. **Boundary docstring headers** (companion IV §B.4) — the three-line `OBJECT / INVARIANT / ENFORCED`
   comment header on each family 1–4 boundary: `core/mirror.py` (π_MR), `core/provenance.py` (ρ),
   `core/stores/derived.py` (interpreted DAG), `ops/gate.py` (the gate FSM), `scheduler/queue.py`
   (queue lifecycle), `eval/drift.py` (D(t)), `core/research/criteria.py` (π_public), and the factory
   scope `core/factory/roles.py` (𝒜/MAX). Placed above the module docstring (comments don't disturb
   `__doc__` — verified). **Honest residuals recorded inline** where enforcement is weaker than the
   invariant: G11 (mirror guards data not the handle), G9 (authored-leaf by-convention), G5 (`conforms`
   absent, not stubbed), and liveness-not-safety on the queue. Notation does not outrun enforcement.
3. **Companion II regrouped by family** — `WHITEPAPER-FORMAL-PROPERTIES.md`'s flat I1–I13 catalog is now
   read under the five family headings (A.1 labelings/flow: I1–I7,I11,I13; A.2 derivation: I9,I10;
   A.3 automata: I8,I12; A.4 metric: the D(t)/G4 obligation; A.5 complex: not-yet-built). Every row's
   formal statement, tier, and discharge is **verbatim-preserved** — only the grouping is new;
   cross-family invariants filed under their primary family with a cross-ref.
4. **Design-note family tags** — a one-line `*Family tag → …*` at the top of all **20** design notes,
   each pointing back to `NOTATION.md`; genuinely cross-cutting notes (holistic-testing, roadmap,
   test-organization) tagged "cross-cutting" honestly rather than forced into one family.

**Verified:** full logic suite **unchanged at 482 passed / 4 skipped / 19 deselected** (green before
and after — the ratchet held); ruff clean tree-wide; import firewall green (core reaches no
network/edge); all 8 module docstrings intact after the comment headers; all 18 required symbols in the
glossary; all 6 whitepapers reference it; all 20 design notes tagged. No flags flipped; no behavior
changed.

**Next (companion IV §B.6):** step 4 — **the small type moves** (each a reviewed, tested,
behavior-preserving diff): `derived_from` → the hyperedge junction, the `c`-clamp as the single
definition of confidence, and the signed-edge polarity enum. Then step 6 — **family 5** (`core/complex/`
+ Dreamer loop v2 per companions III, Track H) behind the `DreamerAdapter` seam, flag-OFF, trough-only.
The DANGLING correlator capstone (Track D) and the A3 auditor remain from the wiring frontier.

---

## Mathematical reframing — Prompt R1: the three small type moves (2026-07-01, behavior-preserving)

Companion IV §B.6 step 4: three reframings that each **delete an illegal state** (the
`MirrorView`/`ProposedChange` move, §B.1). No behavior change; each verified by tests. Full logic
suite **482 → 498 (+16)**, ruff clean, import firewall green.

**Move 1 — the hyperedge junction (`core/stores/derived.py`).** The derivation hypergraph ℋ
(companion III §1.2–§1.3) is now a normalized **junction**: `hyperedges` (one `derives` B-arc per
artifact, `DERIVES` rel_type) + `hyperedge_nodes(role ∈ {tail, head})`, with a first-class
`Hyperedge(edge_id, head, tails: frozenset, rel_type)` type. Each derivation is head κ + tail set
supp(κ); today every head-set has size 1. **Additive + behavior-preserving:** the `derived_from`
JSON column stays as the denormalized projection feeding the `Artifact` API and O(1) traversal;
`add()` writes both together via `_write_hyperedge` and they never drift; `_backfill_hyperedges`
(one-time, idempotent) migrates a pre-junction DB from the surviving column; `reset()` clears the
junction too. **Acyclicity-at-insert is unchanged** (still guards on `derived_from` before any
write). New read accessors `hyperedges()` / `tails_of(head)` are what family 5 (`core/complex/`)
will consume. Tests (+7): typed-roles populate, junction == derived_from (as a set), no-edges ⇒
no-hyperedge, exactly {tail,head} roles stored, idempotent re-add leaves no stale tails, reset
clears it, backfill from a simulated pre-junction store.

**Move 2 — the single confidence clamp (`core/recursion.py` + adjudicator).** `claim_confidence(depth,
grounding, agreement, gamma, lam)` is now **THE** definition: `c = min{1, γ^d·g·(1+λ(|Agr|−1))}`.
`decay_bound` stays the depth-decay *ceiling* γ^d·g (I10); `claim_confidence` multiplies in the
bounded corroboration bonus and applies the **min{1,·} clamp**. The adjudicator no longer assembles
the bonus itself (`core/dreaming/adjudicator.py` calls `claim_confidence`), so **no path can produce
c>1 or a depth-rising c** — closing the companion III §7.2 clamp tension. **Provably a no-op today:**
the R0 panel has 4 distinct methods (agreement ≤ 4), d=1, γ=0.5 ⇒ raw product ≤ 0.65 < 1, so the
clamp changes nothing currently produced (unit test asserts `claim_confidence == old assembly` on
those inputs; the dream-R&D and quality-determinism tests confirm end-to-end). Property tests (+2,
Hypothesis over d≤20, agreement≤50, λ≤2, γ∈(0.01,0.99)): **c ∈ [0,1]** and **c non-increasing in
depth** — the clamp bites when agreement/grounding would push the product past 1. Unit tests (+4):
equals-unclamped-today, clamps-above-one, agreement-is-a-multiplier-not-a-vote (g=0 ⇒ c=0),
rejects illegal inputs.

**Move 3 — the signed-edge enum (`core/complex_types.py`, new leaf module).** Closed value-sets are
now types, not free ints/strings: **`EdgeSign`** (`IntEnum`, SUPPORT=+1 / CONTRADICT=−1 — the value
*is* the ±1 the signed-Laplacian arithmetic and the `edges.sign` column use; deletes the illegal
`sign=3`/`0` state; a non-edge is an absent row, not sign 0) for the Prompt-H1 `edges` table, and
**`HyperedgeRole`** (`StrEnum`, tail/head) used by move 1's junction now. Leaf module, stdlib-only
imports, no network (firewall green). Tests (+3, new `tests/unit/test_complex_types.py`): ±1 values
usable in arithmetic, {tail,head} membership, out-of-set values rejected.

**Verified:** logic suite 498/498 (+16 new: derived +7, recursion +4, complex_types +3, properties
+2), ruff clean tree-wide on touched files, import firewall green (the new `core/complex_types`
reaches no network/edge), acyclicity + all prior derived-store/adjudicator behavior unchanged. No
flags flipped; dream R&D still OFF.

**Next (companion IV §B.6):** step 6 — **family 5** (`core/complex/` build.py/laplacian.py/… + the
Dreamer loop v2 per companions III, Track H, Prompt H1) behind the `DreamerAdapter` seam, flag-OFF,
trough-only; the `edges` table + `EdgeSign` land there. Then the DANGLING correlator capstone
(Track D) and the A3 auditor.

---

## Track H — Prompt H1–H3: the reasoning-complex core (2026-07-01, new code behind the seam)

The foundation of the strong Dreamer — the object, the principled clusterer, rigorous
contradiction (companions III §1–§2). All in a new **`core/complex/`** package (Zone A, model-free,
deterministic, import-firewall green). **New dependencies:** `scipy` (sparse Laplacians + partial
eigensolves) and `scikit-network` (Louvain cross-check) — the offline compute libs BUILD §2.2 adopts;
both compute-only (not networking), declared in `pyproject.toml`.

**H1 — the object.** `core/stores/edges.py` `EdgeStore`: the typed/signed **edges** table (the fiber
(t, w, s, τ), BUILD §1.2) using the R1 `EdgeSign` enum — the persistent home for polarity the cosine
graph can't carry (chiefly contradiction); idempotent content-ids; negative-strength refused; sign is
the closed ±1 set. `core/complex/build.py` `build_complex(view: MirrorView) -> ReasoningComplex`:
nodes + weighted cosine backbone A (symmetric, zero-diag, w≥0) + signed adjacency A_signed (= A until
a persisted contradiction edge overlays −w) + derivation hyperedges (from the `DerivedStore` junction,
touching these authored nodes). **The constructor takes a `MirrorView`, so a non-authored complex is
unrepresentable** (I6 structural — the firewall is the input type).

**H2 — the operator + the clusterer.** `core/complex/laplacian.py` (L = D−A, L_sym = I − D^{-1/2}AD^{-1/2},
signed L̄ = D̄ − A_signed). `core/complex/spectral.py`: `fiedler` (λ₂ + vector), `diffusion_map`
(heat-weighted bottom eigenvectors of L_sym via **`scipy.sparse.linalg.eigsh`**, fixed ARPACK start
⇒ deterministic; dense-`eigh` fallback for tiny/near-full components and on ARPACK non-convergence),
`spectral_labels` (per connected component, eigengap-selected k, NJW row-normalized `kmeans2` with a
fixed seed), and **`diffusion_cluster_notes`** — a drop-in for `cluster.cluster_notes` (same signature
+ `Cluster` return) that dissolves single-linkage chaining (§2.2). Plus `louvain_labels` (scikit-network,
deterministic `random_state=0`) — the second, modularity-based method for the §2.3 cross-check.
**The clusterer is pluggable behind the seam, not the default:** `Dreamer.clusterer` (defaults to the
Phase-7 single-linkage — **behavior unchanged**) and `MindPalaceDreamerAdapter.clusterer` +
`build_diffusion_dreamer_adapter()`. Flipping the default is a deliberate later step (like a flag), not
taken here.

**H3 — rigorous contradiction.** `core/complex/balance.py`: `signed_spectrum` (λ_min(L̄), the global
dissonance proxy — 0 ⇔ balanced, Hou/Kunegis), `frustrated_triangles` (odd-negative triangles — the
*specific* unresolved tensions, O(#△)), `frustration` → (λ_min, triangles). Replaces the 0.1 draft's
deferred contradiction judge with structure.

**Verified:** logic suite **498 → 518 (+20)** — `test_complex` (build/Laplacian/clusterer/Fiedler/Louvain,
+8), `test_edges_store` (+5), `test_complex_properties` (determinism, spectral stability, frustration
correctness, +4), `test_diffusion_clusterer` (+3). **F9 non-regression through `MindPalaceDreamerAdapter`
passes: diffusion planted-signal recall (1.00) ≥ lexical baseline (1.00) and clears the F9 bar; noise
max-confidence 0.10 ≤ 0.70 ceiling.** Balance enumerates a planted frustrated triangle. ruff clean
tree-wide; import firewall green (`core/complex/` reaches no network/edge — scipy/sknetwork are
compute-only); the default single-linkage path and the whole existing quality/binding suite are
**unchanged**. No flags flipped; dream R&D still OFF; live cron dreamer still uses single-linkage.

**Next:** flip the diffusion clusterer to the live default (a deliberate adoption step, once tuned on
the real Ollama embedder's cosine statistics — §2.2 notes σ can drop), then the deferred instruments
(curvature/topology/SBM/support = the rest of the strong-Dreamer pass, companion III §7) and the
Dreamer loop v2. Then the DANGLING correlator capstone (Track D) and the A3 auditor.

---

## Track H — Prompt H4–H7: the structural interpreters (2026-07-02, new code behind the flag)

The Dreamer now has real things to reason over: bridges, holes, alignment, themes-with-confidence —
four new `core/complex/` instruments, each surfaced as a thin `Claim`-emitter in the R0 panel
(BUILD §3.2 "each interpreter is a thin adapter over a `core/complex/` function"). All deterministic,
model-free, flag-gated (`[dream_rnd] enabled=false` — `run_panel` still refuses by default; the live
cron Dreamer is untouched). New dep: **`ripser`** (BUILD §2.2's adopted persistence backend; imported
lazily inside `topology.persistence` — it drags plotting libs never used at module import).

**H4 — `core/complex/curvature.py`.** Augmented Forman–Ricci (`Ric_F = 4 − deg(u) − deg(v) + 3·|△|`,
computed on the σ-graph's support; O(#△), exact) + `most_negative_edges` (emission rule: κ ≤ 0, or
only the minimum-κ edges when all are positive — never the whole graph; deterministic tie-break).
**The panel's `bridge` lens upgraded from the local-clustering proxy to this instrument** (companion
III §3.2's own framing: the proxy's principled replacement) — one claim per most-negative edge,
support = the two linked notes. Ollivier–Ricci stays optional/ungated-out (§3.1), NOT built. The one
pinned proxy test (`data["focus"]`) updated to assert the same planted intent (G1 carries every
bridge) against the new instrument.

**H5 — `core/complex/topology.py`.** `cosine_distance_matrix` + Vietoris–Rips persistence via ripser
(the flag complex K_σ, §4.1) + `long_lived_holes`: H₁ features with lifetime ≥ `hole_min_persistence`,
each completed into a **cycle witness** (representative cocycle edge + BFS path at the birth scale —
the notes circling the hole; documented as a witness, not the unique minimal cycle). The `hole` lens
surfaces them as **gaps, never contradictions** (§4.2 correction held in code and statement text —
dissonance stays routed through `balance.py`/signed edges).

**H6 — `core/complex/cut.py` + the A2 drift axes.** `conductance` (Φ(S) = w(∂S)/min(vol S, vol S̄)),
`min_conductance` (worst community over the deterministic spectral partition — the echo-chamber
axis), `grounding_cut` (min cut = max flow from an interpreted artifact to the authored leaves
through its derivation refs; unit-capacity per ref, fixed-point-scaled integers for scipy's
`maximum_flow`; multi-hop chains bottleneck correctly), `alignment_snapshot(K) → {frustration,
min_conductance}`. **`eval/drift.py` extended additively (A2):** `Profile` gains optional
`frustration`/`min_conductance` (default None), `DriftConfig` gains declared tolerances
(`frustration_tol=0.25`, `conductance_tol=0.10`; readable from baseline.json's `drift` section), and
`drift()` appends the axes **only when both the measured value and a blessed baseline key exist** —
a profile without them produces exactly the pre-A2 drift (proven by test). Rising frustration and
falling conductance are deterioration; improvement stays 0 (one-sided).

**H7 — `core/complex/blocks.py`.** Light degree-corrected **Poisson SBM** (mean-field VEM, ~130
lines per the BUILD §2.2 disposition): deterministic init from the diffusion embedding (fixed-seed
kmeans2), fixed iteration budget, ICL/BIC-style model selection (Karrer–Newman objective −
½·[k(k+1)/2]·ln W − ½·(k−1)·ln n; a **declared engineering penalty validated on planted graphs**,
not a derived MDL bound — stated honestly in the docstring). Returns hard labels + the n×k
**posterior** + the model-selected k. The `theme` lens emits one claim per non-singleton block with
membership confidence and the **spectral cross-check** (`k_sbm` vs `k_spectral`, `counts_agree`) —
§6.3's line held: the posterior organizes the graph, never certifies a thought.

**Wiring.** `core/dreaming/interpreters.py`: new `StructuralContext` (one shared complex at σ +
the unthresholded distance matrix, built once per pass from the MirrorView — non-authored claims
unrepresentable) + `STRUCTURAL_INTERPRETERS` registry {bridge, hole, theme} run by `run_panel`
alongside the σ-graph lenses. Three new `[dream_rnd]` tunables (declared bounds, G7):
`bridge_top_k=5`, `hole_min_persistence=0.15`, `sbm_k_max=8`. **Package-init cycle broken**: 
`core/complex/{build,spectral}` now lazy-import `core.dreaming.cluster` (the panel consumes the
instruments, not vice versa; `core.dreaming.__init__` eagerly pulls the panel).

**Verified:** logic suite **518 → 533 (+15)** — `test_structural_interpreters` property suite (+6:
planted-bridge curvature sign incl. closed form, persistence bottleneck-stability under ≤ε jitter,
grounding-cut monotonicity + chain bottleneck, SBM recovery k∈{2,3,4} at ≥0.95 co-membership +
blockless-graph k=1), `test_structural_panel` (+3: planted ring hole surfaced-as-gap-never-
contradiction, two concerns with posterior + cross-check, firewall/support-authored), drift A2
(+6: axes-absent ⇒ exactly pre-A2 D, axes appear, rising frustration/falling conductance trip,
one-sided improvement, `alignment_snapshot`→Profile→drift end to end). ruff clean tree-wide;
import firewall green; **no flags flipped** (dream R&D OFF; live path untouched).

**Next:** the remaining strong-Dreamer pieces — `support.py` (noisy-OR multi-path grounding, §6.1),
the `tension` lens (needs a contradiction detector to assert `contradicts` edges), `temporal.py`
(structural snapshots feeding the A2 axes live), then the Dreamer loop v2 assembly (BUILD §3.1).
Then the Track D correlator capstone and the A3 auditor.

---

## Track H — Prompt H8–H9: support propagation, temporal self-watching, the loop v2 (2026-07-02)

The strong Dreamer is now ASSEMBLED end to end — multi-path support, the system watching its own
structure evolve, and the BUILD §3.1 ten-step pass — all behind the existing dream-R&D hard
boundary (`[dream_rnd] enabled=false`; **the live `dream()`/cron path is byte-for-byte untouched**,
proven by test). No new flag: the loop v2 is the productionization of the R0/R1 engine that flag
already gates; flipping it live remains a deliberate owner step.

**H8 — `core/complex/support.py` (noisy-OR, §6.1).** `noisy_or` (1 − Π(1−s_p)),
`support_scores` (memoized topological sweep over the derivation map — exact on the polytree,
linear, cycle-defensive), and the adjudicator feed **`grounding_with_support`**: per evidence ref a
*path strength* (authored → 1, interpreted node → its DAG-combined noisy-OR, unresolvable → 0),
aggregated by **mean** — deliberately NOT a noisy-OR at the evidence level, so one good citation
cannot carry nine junk ones (adjudication-not-voting held; padding test proves it). **Equals the
flat `grounding_score` exactly whenever no ref is an interpreted node** — today's only live case —
so R1's clamp law and every existing adjudication are numerically untouched (Hypothesis property +
unit equality tests). `adjudicate()` gains the optional `support_of` seam (default None = flat
score, unchanged); interpreted parents earn partial credit only once recursion exists.

**H9 — `core/complex/temporal.py` (§5.4).** `compute_snapshot(K, distances=…)` → the BUILD §1.2
invariants (β₀, Fiedler λ₂, frustration, mean Forman, frac-negative-curvature, SBM count,
min-conductance, H₁ count — NULL, not a fake 0, when the distance matrix isn't supplied) +
`SnapshotStore` (DuckDB, own file beside the derived store; append-only; `trajectory(metric)` with
an allowlisted column set → the F4 time-series input; `latest_structural()` → the A2 axes dict).
Drift wiring completed additively: `drift_from_report`/`measure_drift` gain optional
`structural=…` passthrough → `Profile` → the A2 axes; snapshot→drift proven end to end.

**The loop v2 (`Dreamer.dream_v2`, BUILD §3.1).** 1 BUILD 𝔎|_MR (one shared complex, persisted
edges overlaid) → 2–5 LOCATE/THEME/TENSION/GAPS (`collect_claims` — the un-gated core factored out
of `run_panel`, now including the **tension lens**: frustrated triangles from asserted
`contradicts` edges, honestly empty on an all-support graph) → 6 SUPPORT (noisy-OR over the
DerivedStore's derivation map) → 7 ADJUDICATE (confidence-ordered; c=0/no-evidence candidates never
earn the model) → 8 SYNTHESIZE (**the only model seam** — one call per stored dream, each grounded
in its candidate's authored evidence, mirror-not-oracle; call-count == stored-dream-count asserted)
→ 9 STORE (interpreted-only, `derived_from` = authored leaves, `dream_pass_v2` attestation, data
carries confidence/methods/statement/loop=v2) → 10 MEASURE (snapshot appended when a store is
injected). `Dreamer` gains optional `edge_store`/`snapshots` fields (defaults None — every v1
construction unchanged).

**Real bug found + fixed (ARPACK):** the fixed start vector `v0 = ones/√n` IS the exact kernel
eigenvector of a balanced all-positive component's L̄ (and of L_sym on regular components) —
Lanczos breaks down on an exact-eigenvector start (ARPACK error −9, surfaced by Hypothesis).
Fixed in `balance._lambda_min` + `spectral._bottom_eigen`: a normalized *ramp* start + dense-exact
fallback on any ARPACK failure. **Semantics fix alongside:** `signed_spectrum` is now the **max
over connected components** of λ_min(L̄) — the raw global λ_min is the *min* over components
(block-diagonal L̄), so one balanced domain or a single isolated note would mask a frustrated
triangle elsewhere; a dissonance detector must register tension anywhere (docstring states it;
every prior balance property still holds).

**Verified:** logic suite **533 → 552 (+19)** — `test_support` (+7: noisy-OR math, polytree
exactness, unresolvable-refs, flat-equality, interpreted-parent partial credit, padding gate,
cycle-defensive determinism), `test_temporal` (+4: planted invariants, contradiction raises
frustration + NULL-h1 honesty, DuckDB roundtrip/trajectory/allowlist, snapshot→drift end to end),
`test_dream_v2` (+7: flag-off refuses, end-to-end store/provenance/confidence/methods, synthesis-
only-model-seam call count, confidence-ordered + earned, tension fires on an asserted
contradiction + gauge sees it, two-pass trajectory, determinism, v1-untouched), flat-equality
Hypothesis property (+1). ruff clean tree-wide; import firewall green; **F9 + the whole quality/
binding suite green and untouched**; no flags flipped.

**Next:** the owner's deliberate adoption steps — flip `[dream_rnd]` for a live v2 R&D session
(and/or wire `dream_v2` + snapshots into the cron dream job in place of v1), tune the diffusion
clusterer on the real Ollama embedder, and bless `frustration`/`min_conductance` baselines into
`eval/golden/baseline.json` once real snapshots exist. Then the Track D correlator capstone and
the A3 auditor.

**Live-model verification (same day, owner asked "real models, not mocked?").** The honest split:
the logic suite substitutes ONLY the two model seams (embedder + synthesizer — injected
deterministic stand-ins); all stores and the entire structural/reasoning layer are the real code
(model-free by design). The `-m live` tier runs real Ollama: executed now — **7 passed / 1 skipped
(3m45s)** on the real `qwen3-embedding:4b` + generation tiers (librarian/factory/scheduler/golden/
research/semantic-search/ollama). The one skip = v1 dreaming synthesis (`qwen3.6:27b` synthesis
tier not pulled; embedding/router/routine/stretch all pulled). **Gap closed:** new
`tests/e2e/test_dream_v2_live.py` — the full loop v2 with real models, same synthesis-tier skip
convention as v1 (will run the moment the 27b is pulled). **And proven today** via a one-off
stretch-tier smoke (`qwen3.6:35b-a3b`, pulled): real embedder → panel (density+theme corroborated)
→ adjudication (confidence 0.55 = the clamp law exactly) → real 35b narration, grounded [[cited]],
self-check PASSED → INTERPRETED store (loop=v2) → snapshot written (frustration 0.0,
min_conductance 1.0). To exercise both committed live dreaming gates: `ollama pull qwen3.6:27b`
(~17 GB), then `pytest -m live`.

## Forward layer — READ-ONLY AUDIT: prompt/Constitution integrity vs tamper & injection (2026-07-02)

**Audit performed, nothing built** — pure investigation per the owner's mandate; no code/test/config
changed; deliverable is `docs/audits/prompt-integrity-audit.md` (the single new file). Cited test
subset re-run this session: 94/94 pass (adversarial + integrity + constitution/budget/factory units +
attestation-store/ambassador integration). Live `CONSTITUTION.md` hash verified == blessed anchor.

**Per-gap verdicts** (evidence + minimal-missing statements in the audit file):
- **G1 CLOSED** — fingerprint = SHA-256 of raw `CONSTITUTION.md` only (`core/constitution.py:31`), lru-cached at process start; nothing else is in the hash.
- **G2 OPEN** — no call site hashes the assembled prompt (`agents/ambassador/agent.py:147` et al.); only the Constitution has an identity.
- **G3 OPEN** — no pre-dispatch gate anywhere; fingerprint recorded post-hoc in attestations; the blessed-anchor comparison runs only in the (OFF) self-mod validator/eval, not the live loop (`ops/lifecycle/launcher.py:144`, preflight has no fingerprint check).
- **G4** — assembly code / skill defs (dormant) / ambassador context output: NOT covered; scope grants: structural tool ceiling covered, `[secrets].grant_roles` config unhashed; retrieved chunks: partial (digests attested, text never re-verified against digest).
- **G5 PARTIAL** — record/store/crypto/verifier faithful to attestation-layer.md, BUT signing OFF in this deployment (records-only, unsigned); minor drifts: `signer` outside signed payload, `att_output` index never built.
- **G6 PARTIAL** — interactive Ambassador IS attested live (read/propose/capture, wired via launcher), but no prompt/output hashes; classifier + Agent/MintedAgent.respond calls unattested.
- **G7 PARTIAL** — injection-as-content + firewall + ceiling all structural, tested, passing, hash-free; missing the model-facing half (adversarial note through retrieval → non-obedience assert, holistic-testing §1c second half).
- **G8 CLOSED** — vault does no prompt hashing and nothing expects it to (capability only).
- **G9** — extra gaps: blessed check never scheduled at runtime; RAG chunks enter as role:"system"; `ContextParts.constitution` override seam; committed pubkeys are dev keys w/ seeds in repo + signing off ⇒ trail tamper-evidence nominal; role prompts have no recorded identity; A3 auditor/tripwire unbuilt.

**Bottom line:** Threat A (injection) = good today for the authored-only surface; Threat B (tamper) =
weak — one file fingerprinted, comparison dormant, no pre-dispatch gate, assembled prompts identity-free.
**Next:** owner picks remediation priorities from the audit (natural neighbor: the A3 auditor).

---

## Policy change — live verification is now routine, not opt-in (2026-07-02, owner directive)

Owner: "start running live but scoped tests, like dreamer functionality with an actual model,
moving forward." Documentation updated to make this a standing rule, not a one-off: `CLAUDE.md` →
"How to work" (new bullet), `CONVENTIONS.md` → "Testing & validation" (the policy + the sandbox
clarification), `docs/runbook.md` (new "Verifying a change" section right after the quick-reference,
with the exact commands). The offline `pytest -m 'not live and not podman and not needs_*'` suite
(552 tests) stays the fast inner-loop ratchet; `-m live` / `-m podman` are now the outer verification
step for anything touching a model tier or the sandbox, run whenever the real thing is available —
not treated as a separate optional pass.

**Corrected a premise along the way.** The owner's framing ("live tests will force us to use the
sandbox, since a lot of the computation happens there") doesn't hold for this codebase: `core/
dreaming/` and `core/complex/` have zero references to sandbox/podman/run_python (confirmed by
grep) — the Dreamer/reasoning-complex runs its own computation in-process (model-free and
deterministic except the embed/synthesize calls), never inside Podman. The sandbox (`-m podman`,
currently 7/7 passing, podman-machine confirmed running) is exclusively the `run_python` **tool**
path for agent-*authored* code (coder/data_analyst roles) — an orthogonal concern from live-model
dreaming tests. `CONVENTIONS.md` now states this explicitly so it isn't re-conflated later.

**Live-model status today:** `pytest -m live` → **7 passed / 1 skipped** (embedding + router/
routine/stretch tiers real; the one skip is dreaming's `synthesis` tier, `qwen3.6:27b`, not yet
pulled — confirmed via `ollama list` this session). The owner has started pulling it; once it
lands, both committed dreaming live gates run for real: `test_dreaming_live.py` (v1) and the H8/H9
session's new `test_dream_v2_live.py` (v2 loop) — the latter already smoke-tested end to end
against the real `qwen3.6:35b-a3b` (stretch) tier and produced a correctly-grounded, self-check-
passing narration (see the H8–H9 entry above).

## Live-tier bug fix — split Ollama socket timeout (2026-07-02)

Running the full suite with the `qwen3.6:27b` synthesis tier finally pulled surfaced a **real
production bug** (not a test artifact): 2 live failures, both `TimeoutError` on `OllamaClient.chat`
— `test_scheduler_live` (a `router` ping under full-suite model-load pressure) and
`test_dream_v2_live` (real `synthesis` narration). Root cause: `request_timeout_s = 120` was the
*single* socket timeout on every Ollama POST. Measured a realistic 27b synthesis chat at **~290s**
(2442 thinking+narration tokens) — 2.4× the ceiling; a real dream/synthesis pass would hit the
identical wall. 120s is wrong in both directions: too long for a hung health/load probe, far too
short for a heavy thinking-model generation.

**Fix:** split by operation class. New `[ollama] generation_timeout_s = 600` (`OllamaConfig`,
`.get`-defaulted so older TOMLs load); `OllamaClient._post` takes a `timeout` override; `chat()`
uses the generation timeout, all control-plane ops (health/load/embed/evict) keep the fast 120s.
Job-level liveness (a pass that never returns) is the supervisor's concern *above* the socket
layer, so a generous generation timeout here is safe. **Verified:** both previously-failing live
tests now pass (`test_dream_v2_live` = the loop v2 end to end on real 27b synthesis, grounded +
self-check-passing — the first full-fidelity v2 run); offline suite unaffected (552 green); ruff
clean. Pre-existing honest skip unchanged: `test_dreaming_live` (v1) skips when the golden fixture
doesn't cluster at its 0.45 threshold under the real embedder (a fixture-threshold matter, not a
regression).

## Track G — Prompt G1–G3: the hands (the type, the gate, read-only sensing) (2026-07-03)

Opened the outward-action boundary at its **safest end** — β = 0, read-only sensing — with the
whole surface **flag-OFF by default** (`[effectors] enabled=false`, empty upstream allowlist).
No acting classes built; the types structurally refuse them. Design: `docs/hands-and-the-
effector-layer.md` (Track G). Everything below is new code behind the flag; no existing behavior
changed (proven by the untouched 552 baseline still green inside the new 602).

**G1 — the effector types (`ops/effects.py`).** `Effect` / `EffectView` + the `ReversibilityClass`
enum (SENSING/REVERSIBLE/IRREVERSIBLE, an `IntEnum` because — unlike provenance, where G8 retired
the order — the order here is the §4 filtration index). The load-bearing move, the **dual of
`MirrorView`**: `Effect.__post_init__` **raises** unless the approval reference covers w(β) for the
class (None admissible ONLY for SENSING), so an unapproved consequential effect is *unconstructable*,
not checked-then-refused. Two more structural facts: (a) an effect carries **no confidence of its
own** — `cites` names motivating interpretation ids, but there is deliberately no `confidence`
field, holding companion III's u≠c separation at the actuator (a high-c dream earns no automatic
action; test asserts the field's absence); (b) `ScopedCapability` carries a scope NAME + a Vault
**accessor** (non-secret reference), and has **no token/secret/credential field at all** — one step
harder than `MintedAgent.token` (off-prompt/off-repr): here the field doesn't exist. `EffectView` is
**Effects_{β≤ε} as a type** — ceiling defaults to SENSING (ε=0); `admit` re-validates; a class above
ε raises `CeilingExceededError`. β (`blast_radius`) and w(β) (`required_approval`) are property-tested
monotone.

**G2 — the gate generalized (`ops/effect_gate.py`).** The Phase-10 guarded transition system (I12),
wider domain: `ProposedChange`→`ProposedEffect`, `G_now`→`G_effect(E) = proposed ∧ approved_{w(β)} ∧
scoped_cap_valid ∧ attested` (§6). `ProposedEffect` inherits the structural ceiling — an
(actuator-name, allowlisted-string-params) pair with **no path/diff/command/code/url field**, so
"run this"/"fetch that address" is unexpressable (the `ProposedChange`/`ResearchCriteria` move);
`resolve()` is fail-closed against the actuator registry (sensing-only: `sense_fetch`) + each
actuator's **closed** param-key allowlist. `effect_gate_admits` is pure data-in/bool-out (no E
handle, no apply ⇒ **E can never self-apply**, I12 inherited), the approval requirement **computed
from the class** via w(β) (no `required` field a decision could understate), the scoped-capability
check a **first-class conjunct** (the confused-deputy answer: no minted scope ⇒ no effect even
fully-approved). **FSM-verified exhaustively over all 72 states** (3×2×3×2×2), same discipline as the
8-state config gate. `capability_covers` = exact-scope-match (no glob authority) + fail-closed expiry
(unparseable⇒expired). Scope note: the durable EffectLedger (execute/validate/rollback rows) lands
with G5 (the first class with world state to roll back); β=0 has none — the guard + types +
attestation trail are the whole machine.

**G3 — read-only sensing, end to end (β = 0).** Core side `core/sensing.py`: `SenseRequest`
(outbound — de-identified, carries **no note content and no URL**: `terms` pass the SAME conservative
scrubber as airlock criteria via the new shared `core.research.criteria.clean_term` seam — one
policy, one impl; `upstream` is a short NAME into the edge allowlist, shaped so a URL/host/path is
unrepresentable → the confused-deputy answer made structural), `SensingHandoff.emit(request, effect)`
(admission **IS** `EffectView.admit(ceiling=SENSING)` — an acting-class effect raises before anything
touches the handoff), `SensedObservation.to_row()` (stamps provenance `observed` with **no
parameter** — the DerivedStore unforgeability move; result type has **no actuator field**, §3),
`ObservedView` (the assistant-tier read boundary, dual to MirrorView; the Track-D correlator's
intended seam). **Edge side** `edge/effectors/sensing.py` (Zone B): `SensingEffector` serves
`sense_fetch` from the handoff with a **powerless constrained fetch** (`UrllibTransport`: **https-only**,
**redirects refused** — 3xx off-host is an exfil vector, **size-capped/refused-not-truncated**,
timeout, no auth/cookies), resolving the request's NAME against its **own reviewed allowlist** (the
ONLY place a URL exists; empty by default ⇒ every fetch refused); **never imports core/ops/scheduler**
(AST-asserted). Refusals come back as **honest error observations**, not silent gaps. Wire shapes
mirrored, not imported — airlock/monitor pattern.

**The firewall (the §3 "done when"), structural both directions.** `MirrorView` refuses `observed`
rows while `ObservedView` refuses everything non-`observed`, so the two views **partition** the tiers
with no representable overlap: sensed exhaust provably **cannot reach the authored mirror or the §15
baselines** (a store of observed rows projects to an empty MirrorView; a sensed row into MirrorView is
a type error). Tested in `tests/integrity/test_sensing_firewall.py`.

**Config** — new `[effectors]` section + `EffectorsConfig` (`.get`-defaulted so older TOMLs load):
`enabled=false`, `handoff_dir`, `timeout_s`, `max_response_kb`, `[effectors.upstreams]` (name→https
allowlist, empty). Fail-closed twice: `build_sensing_handoff` / `build_sensing_effector` both **refuse
unless enabled**, and an empty allowlist refuses every fetch even when enabled.

**Verified.** New tests: `test_effects.py` (G1 types), `test_effect_gate_fsm.py` (G2, 72-state FSM),
`test_sensing.py` (core handoff), `test_sensing_effector.py` (edge, fake transport),
`test_sensing_firewall.py` (the partition + the edge→private-zone import check),
`test_sensing_transport.py` (non-https guard). **Offline suite 552→602 (+50), ruff clean tree-wide,
import-firewall green** (core reaches no network; effectors are edge — both directions now enforced).
**Live network smoke passed** (real `UrllibTransport` → `https://api.github.com/zen` returned a body;
non-https + unknown-upstream refusals fired) — the real egress path, not just the fake. **No flags
flipped** (effectors OFF, self-mod OFF, dream R&D OFF). Not touched: any Ollama tier or the podman
sandbox, so `-m live`/`-m podman` don't apply. **Next (Track G):** G4 (the effector catalog + the
SKILL-mining pipeline doc = the §8 audit as a repeatable process); then G5 (reversible writes) only
once its property tests are green — you do not get a class until the one below is solid (§4). The
acting classes' *value* is gated on Track H producing a deep-enough model to tailor actions (§7).


---

## Security planes — design note (docs/research/)

**Status:** DRAFT, pending ratification (2026-07-03)

**Written:** `docs/research/security-planes.md`. Three-plane security composition — types (code
plane, Threat B-adjacent), provenance (data plane, Threat A), capabilities (boundary, Threat B).
Covers: foundation file set enumeration (builder never holds write access; blocking on repo
verification pass), the Rust/PyO3 privileged-path split (parked, default recorded, rejected
Nelua/Haskell-subroutine/Coq-Agda-F*/Koka-Frank), lightweight TLA+/Alloy + Hypothesis treatment
for three invariants (label monotonicity, capability non-amplification, append-only), store
encryption as capability-hardening rather than a confidentiality silver bullet (AEAD for
integrity, key-as-capability, index-leakage caveat recorded), and the librarian/adjudicator
split — one librarian indexing external strata on ingest and derived strata on promotion only;
the adjudicator as an owner-facing clerk, not a pipeline component, writing recommendations to
the verdict store inbox with promotion spent only by the owner.

**Cross-referenced into:** `docs/audits/prompt-integrity-audit.md` (foundation-file-set gap),
`docs/design-notes/recursive-strata.md` (indexing-on-promotion policy, I1 enforcement),
`docs/design-notes/stability-adjudication.md` (adjudicator's stability-filter input).

**Blocking on:** foundation file set verification pass against the repo (§2 of the note).
**Not built:** no code changes; the note is design-only, same status class as the parked notes
it cross-references.


---

## Source-set: "a source object IS the set of its idea-vectors" as a typed relation (2026-07-03)

Owner-directed (replaced the track-item menu). Make source-set membership a **first-class typed
relation** generalizing across provenance/strata layers — **no second embedding, no re-embed**.
Purely additive; flat retrieval unchanged.

**Investigate (findings; changed nothing).**
- **Embedding is single-scale at chunk grain — confirmed.** `ingest/chunk.py` → `Chunk(index,
  text)`; `ingest/embed.py` one vector per text; `ingest/index.py::index_records` writes **one row
  per chunk** (`id=f"{digest}:{idx}"`); `stores/vectorstore.py` schema is per-chunk. **No stored
  coarse/note-level vector anywhere.**
- **Aggregation over chunk vectors exists only as a TRANSIENT, never persisted:**
  `dreaming/cluster.py::note_centroids` (group-by-`digest` → mean; consumed by the Dreamer graph,
  Curator, and Track-H `complex/{build,spectral}.py`) and `research/rank.py::_centroid` (transient
  personalization centroid, explicitly never ingested). The aggregate is read-time only and never
  a source's identity — consistent with the out-of-scope guard.
- **Membership is already stored** (rows carry `digest`, `title`, `source_path`, `provenance`,
  `chunk_index`; group-by-`digest` reconstructs a source's full chunk set; `provenance` is the
  per-row stratum) but there is **NO first-class abstraction — only implicit group-by at call
  sites** (`note_centroids`, `note_snippets`). `MirrorView` is a provenance *projection*, not a
  source grouping. That gap is what this task closes.

**Built (additive).**
- `core/stores/sourceset.py` — `SourceId(digest, provenance)` (typed identity: content-address
  `digest ∈ Σ` at stratum ρ, both first-class fields, not conventions), `SourceSet(id, title,
  members)` (`vectors()` returns the **raw** member idea-vectors — never a mean; `best_distance()`
  a read-through over `_distance`; a MirrorView-style typed view, Family-2 boundary banner).
  `group_sources(rows)` = the one grouping path (source order = first appearance so a ranked search
  stays ranked; member order = `chunk_index` so a full set reconstructs the note; a
  **mixed-provenance digest raises `MixedProvenanceError`** — a source lives at one stratum,
  fail-closed on ambiguity). `source_sets(store, provenances=…)` / `source_set(store, digest)`
  store constructors. Provenance-parametric — a CURATED item at another stratum groups through the
  SAME machinery with no bespoke path (mirrors `ingest_note`). Hypergraph home (ℋ, Family 5) named
  in the docstring, not built.
- `core/ingest/index.py::grouped_semantic_search` — the explicit opt-in to source-grained
  retrieval (a **separate entry point**, not a union-typed flag; flat `semantic_search` is
  untouched → byte-identical). Defaults MIRROR_READABLE like the flat path; returns `list[SourceSet]`
  where the flat hits are regrouped by source, ranked by each source's best hit.

**Verified.** `tests/integration/test_sourceset.py` (6, deterministic — real `VectorStore` +
hand-built vectors + a fake embedder): membership round-trip (group-by-`digest` == full chunk set,
single-source constructor agrees, every row accounted for once); `vectors()` returns N raw vectors,
not one mean (the no-coarse-vector guard at the type level); grouped retrieval regroups the flat
hits **losslessly** + **flat byte-identical to the underlying store search**; provenance scoping
filters; a non-AUTHORED (CURATED) stratum uses the same machinery; mixed-provenance raises.
**Offline suite 603→609 (+6), ruff clean, import-firewall green** (`core/stores/sourceset.py`
reaches no network). Live/podman **N/A** — touched no Ollama tier and no sandbox; `grouped_semantic_
search` is a pure wrap of the already-live-tested `semantic_search` + deterministic `group_sources`.

**Decisions (defaults, stated inline).**
- Grouped retrieval is a **separate function**, not a flag on `semantic_search`, to keep the flat
  return type + code path provably unchanged (the recursive-strata I3 floor-zero posture; the
  literal "explicit parameter" relaxed to "explicit opt-in surface, default off").
- `source_sets` defaults to **all strata** (it is a structural grouping utility, not a mirror read);
  grouped *retrieval* defaults to MIRROR_READABLE (parity with `semantic_search`).
- A source's provenance is part of its **identity** (`SourceId`), and a mixed-provenance digest
  **raises** rather than silently picking a label — the firewall's fail-closed-on-ambiguity rule.

**Left untouched (deliberate scope).** `note_centroids` / `note_snippets` are the existing implicit
group-by and the natural **first consumers** of `group_sources`, but rewiring them touches the
Dreamer/Curator/Track-H hot path — a separate, deliberate unification, not this additive task. Held
OUT OF SCOPE: no stored coarse vector (a later separately-gated DERIVED cache — centroid/medoids),
no chunk-grain change, no hypergraph wiring.

**Next:** back to the Track-G frontier — G4 (effector catalog) or G5 (reversible writes) — or the
Track D correlator; owner picks. Loose ends flagged this session: uncommitted `docs/ORIENTATION.md`
(untracked) + the `recursive-strata.md` I5 edit are finished-but-uncommitted; and `note_centroids`
could later be expressed as a mean over `group_sources`.


---

## Docs cleanup + design-note audit (2026-07-03, docs-only, no code/config logic change)

Owner-directed documentation reorg + a read-only audit of every design/audit/research note against
the codebase. **No note bodies edited; no code touched except two doc-path strings in `config/`.**

**Reorg (conservative, reversible; move-never-delete):** archived `docs/HANDOFF.md`→`archive/`
(security/attestation track complete, 0 inbound refs); moved `hands-and-the-effector-layer.md`
top-level→`design-notes/` (resolved 3 pre-existing dangling links; updated the 2 `config/`
references — `defaults.toml`, `loader.py` — the only code touched, owner-approved); rotated
`PROGRESS.md` phases 0–10 → `archive/PROGRESS-phases-0-10.md` (verbatim, append-only preserved; live
file 1962→957 lines, Forward layer now the top); trimmed `CLAUDE.md`'s "Current phase" wall → 3-line
pointer (verbatim snapshot in `archive/CLAUDE-current-phase-2026-07-03.md`; also fixed a stray
unpaired fence); removed `docs/bundle/` cruft (3 `.DS_Store`); rebuilt `docs/README.md` as the
canonical index. Every internal link verified resolving (57/57); the 4 recently-cross-linked notes
(security-planes, recursive-strata, stability-adjudication, prompt-integrity-audit) left untouched.

**Design-note audit (24 notes, verified against built code):** 9 realized, 6 partial, 9 parked/future;
none obsolete. Per-note status + evidence now live in `docs/README.md`. Two stale self-statuses the
index corrects, both **actionable**:
1. `wasm-sandbox-runtime.md` header says "design only, not implemented," but `WasmRunner` +
   `RoutingRunner` are **built** with a real wasmtime path (`core/sandbox/runner.py`); dormant only
   because no WASI `python.wasm` asset is placed (`available()=False` → fails closed to Podman).
2. `recursive-strata.md` §8's one authorized immediate action — reserve `DERIVED_STRATUM` (+ integer
   `depth`) in `core/provenance.py` *before* the provenance migration relabels rows — is **undone**;
   the enum has no such label. Cheaper to reserve now than to retrofit after `--apply`.
Absence confirmed for the future tracks: Track L (all L-series artifacts absent), Track D correlator
(`core/ingest/biometric.py` absent), R5 `CuratedView` absent. All feature flags confirmed OFF
(dream_rnd, effectors, attestation, secrets, backup, selfmod). Nothing built, nothing flipped.

**Note:** a concurrent build session was live in this tree during the reorg (added the Source-set
work above); its changes were left untouched and never staged.


---

## Threat-B hardening — two small wins from the integrity audit (2026-07-03)

Owner-directed follow-up to the design-note audit: implement the small, high-value security wins it
surfaced, before resuming the main track (hands/ingest). Two prompt-integrity gaps closed at their
choke points; behavior on the live path is unchanged (both fail-closed only on an actual anomaly).

**Built.**
1. **Constitution fingerprint checked at startup** (`ops/lifecycle/preflight.py` `check_constitution`
   + `_constitution_check`). Closes audit **G9.1/G3**: the blessed-anchor comparison existed
   (`eval/drift.py`) but ran only in the disabled self-mod validator, so a tampered/un-blessed
   `CONSTITUTION.md` would be served to every agent after the next restart with nothing noticing.
   Preflight now compares the live fingerprint (`core.constitution.constitution_fingerprint`) to the
   owner-blessed anchor in `eval/golden/baseline.json` (`eval.drift.load_drift_config`) BEFORE any
   agent is framed, and **fails closed** on mismatch (required check → refuses start; overridable
   with the existing `start --force`, per Invariant 9). A missing anchor warns; the probe never
   raises. Re-bless path in the message (`scripts/eval.py --bless`).
2. **The Constitution assembly seam closed** (`scheduler/budget.py` `Budgeter.assemble` +
   `ConstitutionFrameError`). Closes audit **G9.3**: `ContextParts.constitution` let any caller make
   arbitrary text the outermost frame with nothing validating `messages[0]`. `assemble` now REFUSES
   a non-canonical Constitution fail-closed, unless a caller sets the loud, greppable, keyword-only
   `allow_constitution_override=True` (test/tool paths only, never live). The live Ambassador path
   passes `constitution=None` → the loaded fixed point → byte-identical. (The other model-call sites
   already frame through `core.constitution.frame_context`, which hard-codes the canonical text —
   structurally safe, unchanged.)

Also corrected the **stale `wasm-sandbox-runtime.md` status header** (the runner is built, dormant
pending a `python.wasm` asset — not "design only"); design body untouched.

**Verified.** Full offline suite **610→611 (+1** G9.3 refusal regression test; budget tests updated
to pass the explicit override), ruff clean, import firewall green (core seal intact — the new code is
in `ops/`/`scheduler/`, reaches no network). Live preflight render confirmed
`✓ constitution: matches blessed anchor` on the real config. Live/podman tiers N/A (no Ollama tier,
no sandbox touched). **Not committed** (owner's role); no git actions taken.

**Deliberately deferred (flagged, not built).** `DERIVED_STRATUM` reservation (recursive-strata §8):
its "before the migration" urgency does **not** hold — `migrate_provenance_split.py` only relabels
`authored→authored-solo` and never writes `DERIVED_STRATUM`, so it is a deliberate taxonomy
commitment for the owner at Track-L unpark, not a mechanical win. Chunk-text-vs-digest re-verification
at retrieval (G9.5) folds into the coming ingest work (hot path). Attestation prod-key generation +
`[attestation] enabled` (G9.4) is owner-operational. RAG-in-`role:system` register (G9.2) needs a
behavioral eval before changing.


---

## Retrieval content-integrity — G9.5 (2026-07-03, ingest/retrieval main track)

The chunk-digest re-verification flagged for "the coming ingest work" (above), continuing the
source-set/chunk-digest thread. Closes audit **G9.5**: retrieval took the vector-store row's `text`
at face value, so a mutated LanceDB row would reach the prompt while the read attestation logged the
clean digest (false fidelity; an injection vector once lower-trust provenances become retrievable).

**Built.**
- `core/ingest/pipeline.py::derive_chunks(raw_bytes)` — the one authoritative raw→chunks derivation
  (`_decode` → `chunk_text`), exactly what `ingest_note` does (it chunks `note.text` = `_decode(raw_
  bytes)`). Factored so the check re-derives a source's chunks from the immutable raw store.
- `core/ingest/verify.py::verify_rows_against_raw(rows, raw)` → `(verified, dropped[IntegrityDrop])`
  (Family 2 boundary). A row is verified iff its `text` is one of the chunks re-derived from the raw
  blob it claims (by `digest`); raw fetched/rechunked once per digest. Missing-raw or non-reproducing
  text is dropped fail-closed. **The check is exact** — re-derivation == the ingest derivation,
  uniform across authored-solo / authored-dialogue / curated (all ride `ingest_note`) — so a
  legitimate row NEVER false-drops; only genuinely unreproducible text fails.
- `core/librarian/librarian.py` — `Librarian.raw: RawStore | None`; when wired, `retrieve()` verifies
  each hit and drops failures with a loud `logging.warning` (non-silent). Wired into the 3 production
  builds (`build_librarian`; the Ambassador reuses its `DialogueCapture` `RawStore`; the interface
  `task_librarian`). `raw=None` (tests / pure-RAG) → verification off, path byte-identical (the trust
  knob). The Ambassador's read attestation now covers only verified content as a consequence.

**Verified.** Offline **611→617 (+6)** (`tests/integration/test_verify.py`: clean-verify, tamper-drop,
missing-raw-drop, one-read-per-digest, derive_chunks==ingest, Librarian on/off; `test_ambassador_
conversation` seed made raw-backed so RETRIEVE genuinely exercises the path). ruff clean; import
firewall green (`core/ingest/verify.py` reaches no network). **LIVE SMOKE PASSED** (real
`qwen3-embedding:4b` + real raw store): legitimate embedded content retrieved (no false-drop); a
tampered row with a valid digest and a well-ranked vector was **dropped** (`text-not-in-raw`, logged)
— the injection string never reached the answer.

**Decisions.** Fail-closed drop + loud log is the default when `raw` is wired (house style; the drop
is the load-bearing guarantee, the log is observability); no config knob for v1. Chunk params are the
ingest defaults (1200/150). Stronger options (per-chunk hashes, signed-chunk attestation) named as the
natural next seam on this path — not built. **Not committed** (owner's role); no git actions taken.

**Next:** main-track frontier still open — Track G G4 (effector catalog) or the Track D correlator.
