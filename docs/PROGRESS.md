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

---

## Track G — Prompt G4–G7: the acting hands (catalog, reversible, irreversible, blast-radius drift) (2026-07-04)

Finishes Track G structurally (design note `hands-and-the-effector-layer.md` §10 table → G1–G7 ✅).
Everything is **built behind the flag**: `[effectors] enabled=false`, and the WIRED ceiling stays
ε = SENSING — the acting classes are cataloged, built, and property-tested, but a reversible or
irreversible effect raises before it reaches any handoff (`EffectView.admit(..., ceiling=SENSING)`).
Turning a class on is a separate, deliberate act (raising ε past it once its tests are green, §4).
Assembles existing machinery (the gate, the ledger idiom, the Vault mint, the attestor, `MirrorView`,
the drift `Axis`) — Track G "adds no new geometry."

**Built.**
- **G4 — catalog + pipeline.** `ops/effect_catalog.py` — the authoritative registry the gate now
  CONSUMES (`ActuatorSpec`/`ACTUATORS`/`get_actuator` moved here from `effect_gate.py`; re-exported for
  back-compat). Each hand is a `CatalogEntry` carrying the §8 audit evidence (`sandbox_profile`,
  `source`, `audited`). Added the acting-class hands (draft_reply/calendar_hold/stage_file REVERSIBLE;
  send_email IRREVERSIBLE) — cataloged but unreachable at ε=0. `ActuatorSpec.max_param_chars` (per-
  actuator cap: 256 sensing, larger for content). Doc `docs/design-notes/skill-mining-pipeline.md` —
  the §8 checklist as a repeatable process, each step tied to its code artifact.
- **G5 — reversible writes.** `ops/effect_ledger.py::EffectLedger` — the durable
  propose→approve→execute→validate/rollback FSM for effects (deferred from G2 "to where there is world
  state to roll back"); reuses `ops.ledger.LedgerStatus`; `approve()` fail-closes if the strength does
  not cover w(β). `core/effect_proposal.py::ReversibleWriteProposer` — tailors a `draft_reply` body by
  reading a `MirrorView` (authored-only; the firewall by type), emits a `ProposedEffect`, **has no
  send/stage path** (propose-never-send); refuses non-REVERSIBLE actuators. `edge/effectors/writes.py::
  ReversibleWriteEffector` (Zone B, never imports core, off by default) — STAGES a draft envelope the
  owner can delete; `rollback` unlinks; **traversal unrepresentable** (the effector picks the on-disk
  name; a `stage_file` `name` param rides inside the envelope as data).
- **G6 — irreversible / external.** `ops/effect_exec.py::IrreversibleExecutor` — refuses a non-
  irreversible / under-approved / unproposed / unattested effect BEFORE minting (a doomed effect
  causes NO mint), then mints a per-action JIT scoped Vault token at the moment of action
  (`secrets.mint_token(scope, ttl)`), re-checks `effect_gate_admits` with the fresh capability,
  performs via an injected Zone-B `EffectTransport`, and emits an attested action record with the
  token **accessor** (never the token). `ExecRecord` has no token field; the credential is never
  retained. `build_irreversible_executor` refuses unless `[secrets]` is enabled.
- **G7 — blast-radius drift.** `eval/effector_drift.py` — effector reach (mean reversibility-class
  index over proposals, β's monotone finite proxy) as a drift `Axis` against a frozen anchor, reusing
  `eval.drift.Axis`'s one-sided deterioration. **Detection only**, deliberately kept OUT of the self-
  mod gate's D(t) (effector reach ≠ golden-set capability). Reads the `EffectLedger`.
- **Config.** `[effectors]` gains `ledger_db`, `drafts_dir`, `jit_credential_ttl` (inert while off).

**Verified.** Offline **617→648 (+33, 4 skipped)**; ruff clean (repo-wide); import firewall green
(`core/effect_proposal.py` in core reaches no network). New tests: `tests/unit/test_effect_catalog.py`
(6), `tests/integration/test_effect_ledger.py` (7), `test_reversible_writes.py` (8), `test_effect_exec.py`
(6), `test_effector_drift.py` (6). Property invariants green: unconstructable-without-approval, gate-
weight monotone in β, observations observed-tier (existing G1–G3 suite), plus per-class approval-covers-
w(β), no-mint-for-a-doomed-effect, token-never-retained. **LIVE SMOKE PASSED** (real routine tier
`qwen3.5:9b`): `model_tailor` drafted a voiced reply body from an authored `MirrorView` (signed off
"Best, A", matching the seeded voice note); the seeded **observed** exhaust row was projected out and
did NOT appear in the draft (firewall held live); output was a `draft_reply` proposal, never sent.

**Decisions.** The catalog OWNS the registry; the gate consumes it (one source of truth, `get_actuator`
fail-closed). Acting classes are cataloged-but-unreachable (ε=SENSING) rather than absent — G5/G6 need
them expressible, and three independent structural facts keep them off (ceiling, unconstructable-without-
approval, no ambient capability). Reversible-write staging is a JSON draft envelope (a review surface),
not the final artifact — keeps it reversible + traversal-proof. G7 is a STANDALONE gauge, not folded
into the gate's D(t), to avoid conflating "hands reached further" with "retrieval regressed". Stronger
seams named, not built: per-chunk/per-effect signed attestation at scale (Track L), standing approvals
+ plan-batching (§9 open questions), real Zone-B send/pay transports. **Not committed** (owner's role).

**Next:** Track G's *value* is gated on Track H producing a model deep enough to tailor actions worth
proposing (design note precondition) — build the engine, then raise ε. Open main-track frontier: the
Track D correlator (the `observed`-tier consumer `core.sensing.ObservedView` is the seam it reads).

---

## Sacred-boundary build plan — Phase 0 + verdict store + amendment mechanism (2026-07-04)

Investigation + plan committed as `docs/design-notes/build-plans/sacred-boundary-build-plan.md`
(answers Q1–Q6 with citations, reconciliation diffs, phased plan). Owner said "proceed to build …
both, verdict store first." Built every safely-buildable item; the two stored-data / owner-decision
steps are gated below. Nothing rewrites the corpus; no default behavior changed (the mechanism-built-
but-not-flipped-on posture, as Track G did).

**Built.**
- **Item 1a — index-keying verification harness.** `tests/integration/test_index_keying.py`
  (read-only; real ingest/sync/vector-store path + offline `FakeEmbedder`). **CONFIRMS the Q1 gap**:
  the index is keyed by `(raw-note-digest, chunk-index)`, not chunk-content-hash
  (`core/ingest/index.py:33`), so amending ONE block re-keys EVERY chunk under a new note-digest and
  the old rows are dropped whole (`core/ingest/sync.py:99-101`) — an unchanged chunk does NOT keep
  its point. Falsifier is a live assertion that flips when a content-addressed chunk key is adopted.
- **Item 4a — verdict signing core (pure).** `core/verdict/{payload,__init__}.py`: `VerdictPayload`
  (subject id, category, **monotonic seq**, timestamp) + canonical serialization +
  `sign_verdict`/`SignedVerdict.verify`. Reuses `core/attestation/crypto.py` verbatim (signer
  `"owner"`); NOT the attestation record (`_canonical` can't express a verdict — plan R6). Content-
  bound + asymmetric (verifier holds only the public key).
- **Item 4b-store — signed append-only verdict store.** `core/stores/verdicts.py`: verify-on-append
  (a forged/wrong-key verdict is refused, nothing stored), **monotonic seq** (replay/reorder refused),
  **detectable gaps** (`gaps()` — a dropped verdict is visible, never silently lost), append-only is
  **structural** (no update/delete/reset), `verify_all` tamper-evidence, taxonomy-agnostic
  (`allowed_verdicts` hook, unset until R3 ratified). The ORDERING-FIRST deliverable (sacred-boundary
  §4). Schema-additive (new table), no stored-data rewrite.
- **Items 1b + 1c-mechanism — versioned amendment (PURE).** `core/ingest/chunk.py` `Chunk.content_hash`
  (property; additive, construction-preserving) + `core/ingest/amend.py`: `chunk_point_id` (the
  document-scoped `(doc_id, chunk_hash)` identity — resolves the §3-vs-§7 tension so distinct notes
  sharing a verbatim chunk keep BOTH points, plan R1) and `plan_amendment` (retain/add/remove diff by
  content hash). No store, no embed, no live-data touch — the mechanism the sync path will call once
  wired.

**Verified.** 23 new tests (`test_index_keying` 1, `test_verdict_signing` 9, `test_verdict_store` 7,
`test_chunk_amendment` 6); full offline suite **672 passed, 7 skipped** (`-m "not live and not
podman"`), no regressions; ruff clean; import-lint (I2 seal) green — `core/verdict/` + `core/ingest/
amend.py` reach no network. **No Ollama tier / sandbox touched** (offline embedder; the id scheme is
embedder-independent; verdict work is pure crypto/SQLite), so the live/podman outer gate is **N/A**.
**Not committed** (owner's role).

**Gated — owner decision + snapshot needed before these proceed.**
- **Item 1c WIRING (the stored-data rewrite):** switch the vector-store row id to `chunk_point_id`,
  make `sync.sync_path` a chunk-level diff (retain/embed/supersede), add a `supersedes` edge rel-type,
  + a re-index-from-raw migration (dry-run default, `--apply` opt-in like `migrate_provenance_split`).
  Needs owner ratification of the §4 versioning semantics (PD5) + a **restic snapshot** before any
  `--apply`. The pure mechanism (`amend.py`) is built + tested; only the wiring + live re-index remain.
- **Item 4b-apply:** what `promote`/`supersede` DO to the graph — blocked on the parked promotion
  mechanism (recursive-strata I1).
- **`DERIVED_STRATUM` reservation (PD6):** a semantically-loaded taxonomy commitment (mirror-readable?
  depth field on which store?) — left as an owner call, not baked in unilaterally.
- **Verdict taxonomy (R3):** the `allowed_verdicts` set the store enforces — owner to ratify
  (`live-adoption` §3 L2 candidate: novel_useful/true_known/plausible/wrong/noise + "promote insight").
- **Part-B reconciliation cross-references:** unapplied (await approval).

**Next:** owner ratifies §4 semantics + takes a snapshot → wire Item 1c + run the re-index; and/or
ratifies the verdict taxonomy → wire 4b into the Ambassador-as-transport path (a verify+apply seam
separate from the Ambassador, plan R7).

---

## Sacred-boundary build plan — 4b-apply + Ambassador verdict transport + Part B applied (2026-07-04)

Owner: "continue with 4b, the ambassador verdict transport surface, and the build-plan Part B." All
three done. (Owner will run `migrate_chunk_keys.py --apply` later, once notes are exported/embedded.)

**Built.**
- **4b-apply — the supersession half (weight-promotion I1 stays parked).** `core/verdict/dispositions.py`
  — append-only `DispositionStore` (`VerdictEffect` RETRACT/ENDORSE/RECORD; latest-wins by subject;
  `retracted()` is the active-projection filter). `core/verdict/apply.py` — `effect_of` (wrong/noise →
  RETRACT, novel_useful → ENDORSE, else RECORD) + `apply_verdict`; `build_verdict_receiver` now
  verify+store+**APPLY**. `core/dreams_view.py` — `DreamsView` is the ACTIVE projection: a dream the
  owner verdicted `wrong`/`noise` is dropped from surfacing (kept in history). Grounded in
  ingest-identity §6, NOT the parked recursive-strata I1. Backward-compatible: no dispositions →
  behavior byte-identical.
- **Ambassador verdict transport (R7).** `agents/ambassador/agent.py` — a `verdict_transport` seam +
  `transport_verdict` that CARRIES a signed verdict to the receiver and attests it, but never signs,
  verifies, or applies one (each is a write outside its read+propose scope). `scripts/verdict.py` —
  the owner CLI (`sign` via the Keychain owner seed / `submit` = verify+store+apply / `list` + gap
  report). `core/verdict/payload.py` — `to_dict`/`from_dict` (JSON transport; the signature survives
  and is re-verified). `build_ambassador` wires the disposition filter + the transport, fail-SAFE
  (no owner key placed → no verdict channel, never a broken Voice).
- **Part B reconciliation APPLIED** (owner-approved). 2 corrections + 6 cross-references, to the
  design docs (not silent): verdict-authority §8 (**R4** — `security-planes` records the verdict store
  + Ed25519-for-integrity, NOT a TOTP argument) and ingest-identity §9 (**R2** — supersession-as-edge
  is introduced here, not in `recursive-strata`); cross-refs into live-adoption §3 (L2) + control
  corpus, security-planes §6, recursive-strata I2 + §2, and hands §4.

**Verified.** Offline **686 passed, 7 skipped** (+14 this segment: dispositions/apply/transport +
serialization), ruff clean, import-lint (I2 seal) green. **Not committed** (owner is committing).
*Noted, pre-existing + unrelated:* `tests/integrity/test_attestation_signatures.py::
test_signing_does_not_change_the_content_address` is a latent flake — it compares two attestations'
ids but their `_utcnow()` timestamps can straddle a 1-second boundary; green on re-run, a 1-line
clock-freeze would harden it (owner's test, left untouched).

**Gated / remaining.**
- **1c `--apply`** — owner-operational, after notes are exported/embedded (nothing embedded yet).
- **4b-apply WEIGHT promotion** (a derived node's edge weights rising) — still parked on
  recursive-strata I1. `ENDORSE` is recorded but does not yet change weights.
- **Ambassador conversational verdict *intent*** (recognizing a verdict inside a chat turn) — not
  built; the CLI + the `transport_verdict` seam are the surface.

---

## Sacred-boundary build plan — Items 1c + verdict taxonomy/4b-wire + DERIVED_STRATUM (2026-07-04)

Owner: "proceed with all three items, one at a time." Built all three, tightest-reversible first.
No live data rewritten (the `--apply` re-index is owner-operational, below); default behavior of the
verdict channel is off until a transport is wired.

**Built.**
- **Item 1 — `DERIVED_STRATUM` reservation (PD6).** `core/provenance.py`: one enum member, reserved
  for promoted depth-carrying derived strata (recursive-strata §4/§8), **excluded from
  `MIRROR_READABLE`** (never confusable with authored K₀). No consumer yet — the cheap half of the
  action; the integer stratum `depth` lands with its consumer. Firewall/property tests green.
- **Item 2 — verdict taxonomy (R3) + wire 4b.** `core/verdict/taxonomy.py` `VERDICT_TAXONOMY` =
  the live-adoption §3 (L2) five verdicts (ratified; ≤5 review-fatigue bound). `core/verdict/apply.py`
  — `receive_verdict` (verify against the owner key + append), `load_owner_pub_b64` (reuses the
  committed `[attestation] owner_pub`; fail-closed if absent), `build_verdict_receiver`. SEPARATE
  from the Ambassador (R7). `open_verdict_store` stays taxonomy-agnostic; the receiver applies the
  ratified set. Fixed a package-init cycle (`apply` imported directly, not via `__init__`).
- **Item 3 — Item 1c: the amendment rewrite (stored-data path; CODE done, live `--apply` gated).**
  Doc-scoped chunk keys `(source_path, chunk_hash)` — `core/ingest/index.py` (`_chunk_row` single
  row-builder, `index_records` content-addressed + intra-note dedup, new `index_amendment`). The id
  VALUE changed; the vector-store SCHEMA did not (chunk-hash is derivable), so existing stores don't
  error. `core/ingest/sync.py` `sync_path` is now a chunk-level diff: reuse unchanged chunks' vectors
  (**no re-embed**), embed only changed/new, replace the projection by `source_path`, record a
  `supersedes` version edge (`core/stores/edges.py` `SUPERSEDES`; wired in `build_vault_sync`).
  `core/stores/vectorstore.py` `rows_for_source`/`delete_source`. `scripts/migrate_chunk_keys.py`
  (dry-run default; `--apply` re-keys rows in place — see the 2026-07-04 fix below; the original
  reset+re-ingest form was buggy). Behavior change: identical content at
  two paths now indexes per-document (source-scoped), not shared — consistent with §4/§7; the
  shared-content test still passes (it checks existence/searchability, not the sharing mechanism).

**Verified.** Offline **679 passed, 7 skipped** (+7: verdict-apply 6, index-keying +1), no
regressions; ruff clean; import-lint (I2 seal) green. **LIVE (owner directive — 1c touches the embed
path):** `pytest -m live` ingest/retrieval tier PASSED against real `qwen3-embedding` (Ollama 0.30.7)
— `test_semantic_search_live` + `test_librarian_live` + `test_golden_live` (3 passed, 108s): the new
doc-scoped id scheme + index changes rank/retrieve correctly and hold the golden baseline. **Not
committed** (owner is committing).

**Gated / remaining.**
- **1c `--apply` on live data NOT run** — `scripts/migrate_chunk_keys.py --apply` rebuilds the
  owner's `~/.mind-palace` derived index (raw untouched, regenerable). Owner-operational; take the
  restic snapshot first. Code + dry-run ready; new ingests already write doc-scoped keys.
- **Item 4b-apply** — what `promote`/`supersede` DO to the graph — still parked on the promotion
  mechanism (recursive-strata I1).
- **Ambassador verdict-transport surface** — the conversational path to carry a signed verdict
  inbound (a product decision) — not wired; `receive_verdict` is the ready seam.
- **Part-B reconciliation cross-references** — still unapplied (await approval).

---

## Fix — chunk-key migration was a silent no-op (2026-07-04)

Owner-flagged while reviewing the supersession-edge design: `scripts/migrate_chunk_keys.py --apply`
reset the vector store then called `rescan()` — but `rescan()` is change-detected against the catalog
(unchanged digest ⇒ `UNCHANGED` ⇒ skip), so on a populated store it would have **emptied the index
and rebuilt nothing** (`palace reset` avoids this only because it also wipes the catalog).

**Fixed** by replacing reset+re-ingest with an in-place **re-key**: `core/ingest/index.py`
`rekey_store` / `rekey_preview` recompute each row's id to `(source_path, chunk_hash)` and rewrite
the table with the **same vectors** — no re-embed, no Ollama, catalog + raw untouched, idempotent;
identical chunks within a source coalesce (§3) and distinct docs' shared text stays two points (§7).
The script is now a thin CLI over those. Moot on the owner's current empty store (fresh ingest
already writes doc-scoped keys), but correct if ever run on a populated index.

**Verified.** `tests/integration/test_rekey_migration.py` (4: migrate+preserve-vectors, coalesce,
§7-two-points, idempotent). Full offline **690 passed, 7 skipped**; ruff clean; import-lint green.
Also hardened a pre-existing flake surfaced earlier: `test_attestation_signatures::test_signing_does_
not_change_the_content_address` now freezes the clock (`attestor_with_store(clock=…)`), since the id
covers the timestamp and two `_utcnow()` emits could straddle a 1-second boundary. **Not committed.**

---

## Sacred-boundary build plan — Item 6: supersession-edge correctness (2026-07-04)

Owner-approved after the post-builder-review `ingest-identity-and-amendment.md` §4A refinement.
Q7/Q8 confirmed the shipped whole-note supersedes edge had three defects: keyed on **content
digest** (collapses on revert), sitting in the **balance-fed `EdgeStore`** read unfiltered by
`build_complex._overlay_signed`, with a placeholder **`sign=+1`** (a live hazard the instant both
endpoints are active nodes). Item 6 corrects all three.

**Built.**
- **New `core/stores/versions.py` `VersionStore`** — append-only note-version history keyed on
  `(doc_id = source_path, monotonic version_seq)`, NOT content digest (Constraint 1):
  `record`/`current`/`history`/`supersessions`. A revert (v1→v2→v1-bytes) is v3 at seq 3 — linear,
  no cycle, no node merge; no cycle-guard wanted; ordering by version_seq, never edge topology.
- **`core/ingest/sync.py`** — `sync_path` appends a version on every INDEXED (v1 on first ingest,
  v2… per amendment) and writes **no edge**; the `edge_store` field/param is removed; `build_vault_sync`
  wires `open_version_store` (Constraint 2 — the balance math has no handle to this store).
- **`core/stores/edges.py`** — dropped the `SUPERSEDES` rel-type (with a comment not to re-add it)
  and added `delete_rel_type` (the migration to retire any stray `supersedes` rows from the
  EdgeStore; a no-op on the current empty store).

**Verified.** `tests/integration/test_version_history.py` (6: monotonic chain, revert-stays-linear,
per-document, append-only, amendment-records-version-and-no-edge-handle, delete_rel_type migration);
`test_index_keying.py` trimmed (dropped the old edge test). Full offline **695 passed, 7 skipped**;
ruff clean; import-lint (I2 seal) green. No Ollama tier / sandbox touched (pure SQLite swap) → live
gate N/A. Also updated `docs/design-notes/build-plans/sacred-boundary-build-plan.md` (Q7/Q8, Item 6,
the dependency edge Item 6 → Items 2/2b per §4A C3, and PD7). **Not committed.**

**Remaining:** per-chunk supersession edges deferred (PD7 — raw-diff reconstructs that history); the
dialogue operation vocabulary (Items 2/2b) is now unblocked (§4A C3 store-separation satisfied).

---

## Sacred-boundary build plan — Items 2a + 2b: dialogue operation vocabulary (2026-07-04)

Owner-approved; unblocked by Item 6 (§4A C3 store separation). **Item 2a** ratified the starter set
`{supersede, attach_defeater, record_warrant}`; extras (retract/split/merge/confidence_adjust) are
deferred (PD2 — no cited case); warrant is a relation, not a node (PD3).

**Built (Item 2b — deterministic core).**
- **`core/recursion_ops.py`** — the operation types (`Supersede` / `AttachDefeater` /
  `RecordWarrant`), an append-only `ClaimOpStore` (DISTINCT from the version + balance-edge stores,
  §4A C3; `superseded()` is the active-projection filter), and `apply_operations`: a `Supersede`
  mints its conclusion C′ as an INTERPRETED artifact via `DerivedStore` (`derived_from=[C]` →
  depth ≥ 1 → γ^d bounds it, I10/I5 by construction), records the supersede RELATION, and never
  enters C′ as an authored peer (the §2 failure avoided). Budgets floored (PD4 — no recursive-strata
  enforcement).
- **Extraction seam.** `DialogueAnalyzer` protocol + `no_op_analyzer` default (a dialogue emits NO
  ops → document-only ingest, unchanged). The model-backed analyzer (dialogue text → operations) is
  the deferred seam a real deployment injects.

**Verified.** `tests/integration/test_dialogue_ops.py` (6: acts-on-claim-not-peer-node, γ^d-damped
conclusion, defeater/warrant recorded, distinct-store §4A C3, idempotent, no-op default). Full
offline **701 passed, 7 skipped**; ruff clean; import-lint (I2 seal) green. No Ollama tier / sandbox
touched (deterministic core) → live gate N/A. **Not committed.**

**Deferred (named seams, not built).** The model-backed `DialogueAnalyzer` (extraction is an LLM
task, owner/verdict-reviewed); wiring `superseded()` into the MirrorView / reasoning-complex active
projection (the consumer — the same shape as DreamsView honoring dispositions, a small follow-up);
I5/edge-budget enforcement (parked with recursive-strata). **Next open item:** Item 3 (founding-corpus
path, now unblocked by 1c + 2b) or the deferred 2b consumer wiring.

---

## Sacred-boundary build plan — Item 3: founding-corpus ingest path (2026-07-04)

Owner-approved (unblocked by 1c + 2b). The founding corpus is authoring the initial condition — NOT
model training and NOT steady-state ingest (founding-corpus.md §1–§2): a dated, supersession-linked
sequence that MUST share the steady-state path or the provenance model fractures at the origin (Q3).

**Built.**
- **`core/ingest/founding.py`** — `FoundingItem` (a dated musing + optional `supersedes` link) +
  `ingest_founding`: a thin batch over the ONE pipeline (`ingest_note` AUTHORED_SOLO → `index_records`
  → `catalog.record`, the curated idiom — no bespoke writer). Enforces **dated** (each reconstructed
  date recorded as a `date::` property in the raw blob — permanent; undated refused, §2.1) and
  **supersession-linked** (a later musing revising an earlier one records a claim-`supersede` in the
  `ClaimOpStore` — a RELATION between authored notes; forward references refused). AUTHORED_SOLO, never
  the control corpus (§2.3). Ingest, not fine-tuning — the weights never move (§1).
- **`core/ingest/logseq.py`** — factored `parse_text` out of `parse_note` (the path-free parse core),
  so programmatic ingest reuses the SAME tag/link/property extraction (no bespoke parser).
- **`scripts/ingest_founding.py`** — owner CLI over a JSON founding manifest.

**Verified.** `tests/integration/test_founding_corpus.py` (6: shared-path AUTHORED_SOLO + retrievable +
digest == `ingest_note`'s [no bespoke writer]; date lands in the raw blob; supersession recorded;
undated refused; forward-supersession refused; mechanically distinct from a CURATED control §2.3).
Parse-refactor dependents green (ingest / vault_sync / dialogue_capture). Full offline **707 passed,
7 skipped**; ruff clean; import-lint (I2 seal) green. No Ollama tier / sandbox touched → live gate N/A.
**Not committed.**

**Deferred seam.** The temporal *layer* reading founding dates (`build_complex` wants a `created_at`
the vector rows don't carry — that layer is dormant/parked); dates are recorded now so it can when it
wakes. **Remaining plan items:** Item 5 (effector-risk optimizer) stays parked (PD1); the 2b model
`DialogueAnalyzer` + the supersede/retract active-projection consumer wiring are named seams. With
Items 1–4 + 6 built, the sacred-boundary set's inbound + effect channels are implemented end to end
behind their gates; the frontier is Track L (verdict-labeled longitudinal study) + Track H depth.

---

## Edge & supersession build plan — Items 7 & 9 (2026-07-04)

Plan: `docs/design-notes/build-plans/edge-and-supersession-build-plan.md` (investigation + owner
ratification of R5/R3 in the same file). Notes: `the-edge-model.md`, `supersession-lifecycle.md`.
Owner-approved the first cut (7 ‖ 9); Item 9 is the highest-leverage correction (one `derived_from`
fix resolves Q10 grounding, the Q9(b) grounding-walk leak, and the R2 `hyper`-contamination at once).

**Built (Item 7 — E_geom ⊔ E_disp partition, structural + tested).**
- **`core/complex/build.py`** — stated the partition invariant at `_overlay_signed` (the sole place
  `A_signed` is assembled): the balance math sees `A_geom` from the `EdgeStore` alone; the two
  dispositional stores (`versions.py`, `recursion_ops.py`) have **no handle** into `build_complex`,
  so exclusion is structural, not a per-consumer filter. "Authority typing" realized AS the
  store-separation invariant (an edge's authority = which store it lives in); a branched-on
  `EdgeAuthority` enum deferred until a consumer needs it (no dead scaffolding).

**Built (Item 9 — revision grounds on warrant anchors, never `[C]`; grounding maintenance).**
- **`core/recursion_ops.py`** — `Supersede` gains `anchors` (the warrant's K₀ authored digests);
  `apply_operations` mints C′ with `derived_from = anchors` — or, empty, C's *surviving authored
  grounding* (`leaf_refs(C)`) — **never `[C]`** (corrects committed Item 2b; supersession-lifecycle
  §4.2). The C→C′ relation is the dispositional `ClaimOpStore` edge alone. Added `stale_closure()` =
  `Stale(C)` grounding-descendant closure (§5) surfaced in `ApplyReport.stale` — flagged for
  re-examination, never cascade-retracted. γ^{d≥1} "can't out-rank authored" guarantee preserved
  (depth ≥ 1, independent of the anchor target). Founding path untouched (it records supersedes
  directly, not via `apply_operations` — R5 routing is Item 8).

**Verified.** `tests/integration/test_edge_partition.py` (2, new): frustration + Forman + clustering
bit-identical under adding a version row AND a claim-op; `build_complex` signature admits no
dispositional store. `tests/integration/test_dialogue_ops.py` (+5): anchors-not-claim; §4.4 no-tower
falsifier (flat depth + flat `g`, with the predecessor-grounded control that towers d=2/g=0);
default-inherits-surviving-grounding; γ^{d≥1} guarantee; `Stale(C)` closure not self-generated by a
well-formed revision. Full offline **714 passed, 7 skipped**; ruff clean; `tests/integrity/test_sealing.py`
(I2 seal) green. No Ollama tier / sandbox touched (deterministic core) → live gate N/A. **Not committed.**

**Next.** Item 8 (blessing gate + proposed→certified + disposition authority + R5 founding-routing
sub-item 8f) — the remaining HARD gate (R3) before any real `DialogueAnalyzer` merges; requires the
built `VerdictStore`/`DispositionStore`. Then Item 11 (γ^d·g exclusion confirmation, now unblocked by
9). Item 10 parked on the Ollivier-Ricci gate; Item 12 = PD8 (promotion vs depth cap). **Item 8 is a
fresh session** — resume from this entry + the build plan's Item 8.

*(Items 7 & 9 above committed by owner as `a9e8423` "feat: Revision to edges" + release `1.1.0`.)*

---

## Edge & supersession — Item 9 Part-1 correction (g=0) + 8f taxonomy (2026-07-04)

Follow-up on the owner-committed Items 7 & 9 (`a9e8423`). Owner caught a latent bug in the Item 9
grounding fallback + asked to resolve one Item-8 design question before it's built.

**Part 1 — authored-revision `g=0` bug (CONFIRMED + FIXED).** Item 9's empty-anchors fallback used
`leaf_refs(C)` unconditionally. For an **authored (K₀)** `C`, `leaf_refs(C)` walks `_edges_of` which
returns `[]` for any non-artifact (`core/stores/derived.py:226,267`) ⇒ `∅` ⇒ `derived_from=[]` ⇒
`g=0` ⇒ `decay_bound=0` (scratch-confirmed: an authored-note rephrase minted **weightless**, a silent
"blessed content vanishes" with no verdict). **Fix:** scope the `[C]` prohibition to *derived* `C`
(the thing that decays / is superseded without a verdict — the real target). Empty-anchors fallback,
by `C`'s type via new `DerivedStore.is_artifact`: derived `C` → inherit `leaf_refs(C)` (never `[C]`);
authored `C` → `[C]` itself (bedrock — does not decay, so `g=1`, not weightless). If `C` is later
demoted by verdict, `C′` lands in `Stale(C)` and is re-examined — the maintenance path, not a reason
to refuse grounding. `core/recursion_ops.py` + `core/stores/derived.py`.

**Part 2 — 8f founding-supersession taxonomy (RESOLVED, design-only; PD11).** The one-line test —
*two versions of one document, or two documents?* A founding `supersede(A,B)` has `A,B` at different
`source_paths` (`core/ingest/founding.py:114-123`) → two documents. The version store's
`PRIMARY KEY (doc_id, version_seq)` (`core/stores/versions.py:57,99`) **cannot** key a
cross-`source_path` relation (confirmed), and it carries no warrant / mints no alternative → not a
claim-`supersede` either. **Decision:** its own **authored-historical `supersede`** — a third E_disp
dispositional edge type (owner-authority at authoring time, ungated for chain-establishment), its own
store keyed on the two authored digests. Rejected: reuse the version store (unkeyable); synthesize a
shared `doc_id` (fabricated identity, §4A C1 failure family). Documented `the-edge-model.md` §4a/§5;
implementation is Item 8/8f. Safe to defer — `founding.py:121`'s claim-op records are inert
(`superseded()` has no consumer; active projection filters on `DispositionStore.retracted`,
`core/dreams_view.py:56`).

**Verified.** `tests/integration/test_dialogue_ops.py`: split the default-anchors test into the
derived case (inherit leaves, never claim) + a new `test_authored_revision_grounds_on_bedrock_not_weightless`
(`g=1`, `decay_bound>0`). No-tower falsifier + all Item-9 tests still green. Full offline **715 passed,
7 skipped**; ruff clean; seal green. Deterministic core → live gate N/A. **Committed this session**
(owner-requested).

**Next unchanged:** Item 8 (now with 8f resolved to an authored-historical edge type) — fresh session,
resume from here + the build plan's Item 8 / PD11.

---

## Edge & supersession — Item 8 / 8f: the owner-declared authored-historical store (2026-07-04)

First slice of Item 8. Owner greenlit ("continue to item 8") with one build-time guardrail: the
fail-closed-by-source invariant must be **structural at the store's own boundary** (the store
CHECKS and REJECTS machine authority), verified by a **negative test** — not merely "no machine path
is wired to call it" (which decays on the next refactor).

**Built.**
- **`core/stores/authored_supersession.py`** — the third dispositional edge type (the-edge-model §4a):
  a K₀↔K₀ authored-historical `supersede` across two DOCUMENTS. `AuthoredSupersessionStore` is
  append-only, keyed on the two authored digests; `superseded()` is the active-projection filter (same
  role as `ClaimOpStore.superseded`). **Owner-declared ONLY, structurally:** `record(..., declaration)`
  requires an `OwnerDeclaration` and **verifies it at its own boundary** (isinstance + the guarded
  `_OWNER_TOKEN` via `getattr`, so a bypass-constructed instance is refused too); anything else —
  `None`, a forged object, a machine caller's fabrication — raises `MachineAuthorityRefused`.
  `OwnerDeclaration` is construction-guarded (`owner_declaration()` mints it; a direct
  `OwnerDeclaration()` raises). This is capability-dissolution (the-sacred-boundary §3): the
  machine-write capability is *removed*, not guarded with a forgeable flag. Balance math has no handle
  (dispositional, like the version store).
- **`core/ingest/founding.py`** — rerouted: founding K₀↔K₀ supersession now records to the new store
  (mints `owner_declaration()` — founding IS an owner entry point) instead of the `ClaimOpStore`.
  `ingest_founding(..., supersession_store=)` replaces `ops_store=`; `founding.py` no longer imports
  `ClaimOpStore`/`OpKind`, so it structurally cannot write a claim-op row. `scripts/ingest_founding.py`
  (owner CLI) unaffected (wires through `build_and_ingest_founding`).

**Verified.** `tests/integration/test_authored_supersession.py` (new, 8): owner-declared write +
`superseded()` filter; idempotent; **structural negative — a simulated dreamer/scheduler caller
(declaration `None`/object/str/int) is REJECTED at the boundary**; capability cannot be forged (direct
construction + `object.__new__` bypass both refused); positive control writes; append-only; no
balance-math handle. `tests/integration/test_founding_corpus.py` updated (supersession now in the
authored-historical store, not the claim-op store). Full offline **722 passed, 7 skipped**; ruff clean;
seal green. Deterministic core → live gate N/A. **Not committed.**

**Remaining in Item 8 (subsequent sessions):** the blessing gate (I1a — superseding blessed content
records defeater + alternative + verdict recommendation, stays contested); `proposed → certified`
states on claim-`supersede` + the verdict transition; disposition-authority recording
({owner-declared, owner-verdict, dialogue-op, decay}); and wiring the active-projection **consumer**
of `superseded()` (nothing demotes from retrieval yet — the store is the write side). Machine-inferred
authored↔authored supersessions route through that gate (Item 10 candidates), never this store. Then
Item 11 (γ^d·g exclusion confirmation). **Item 8-gate is a fresh session** — resume from here.

---

## Agent-workflow layer — bp-000 sealed: bootstrap the workflow machinery (2026-07-05, /triage)

First checkpoint of the **agent-workflow meta-layer** — the constitution + hook enforcement that
governs how build work moves, distinct from the domain Track A–H build above. Spec:
`docs/design-notes/agent-workflow.md`. bp-000/bp-001 were hand-minted bootstrap plans (the machinery
that would `/graduate` and gate them did not yet exist); their journals were hand-sealed, so this is
only the orchestrator's deferred single-writer PROGRESS checkpoint (out of plan write_scope by design,
finding-0002).

**Built.** `CLAUDE.md` (persona-neutral workflow constitution); `.claude/settings.json` + six
dual-mode hooks (`scope-guard`, `gate-guard`, `session-brief`, `journal-gate`, `staleness-nudge`,
`compaction-marker`) over shared `.claude/hooks/_lib.py`; six commands + five skills + four templates
(`docs/templates/`); `docs/inbox/owner-questions.md`. Full list: `docs/build-plans/bp-000/plan.md`.

**Verified.** `docs/build-plans/bp-000/acceptance/run.sh` — criteria 1–7 green (PASS=13, FAIL=0):
brief+orchestrator posture; pre-hoc scope deny + post-hoc Bash catch; fresh-agent resume;
capture→graduate status-gate; triage routing; blessing denied+caught on both Edit and Bash paths;
HOOK-FAILURE alarm + standalone recovery.

**Next.** Sealed. Enforcement contract finalized by bp-001 (A1/A2) and bp-002 (A3) below.

**Decisions.** Bootstrap exception (hand-mint at in-progress; the owner's execute-instruction is the
blessing) documented in `plan.md`. `docs/PROGRESS.md` deliberately outside bp-000 write_scope to
protect the domain log (finding-0002) — hence this orchestrator-written entry.

---

## Agent-workflow layer — bp-001 sealed: amendments A1 + A2 (2026-07-05, /triage)

**Built.** A1 + A2 landed against `docs/design-notes/agent-workflow.md` §16. `.claude/hooks/_lib.py`:
`cmd_stop_audit` (c) re-anchored to `git diff HEAD` (`_diff_text_head()`) so a *committed* blessing
self-clears while an *uncommitted* one still blocks; (b) confirmed already untracked-inclusive +
file-granular (`git status --porcelain -uall`), left unchanged. `CLAUDE.md`: the 12-item domain
non-negotiables digest re-homed into the always-loaded body (the one thing exempt from constitution
thinness, §5).

**Verified.** `docs/build-plans/bp-001/acceptance/run.sh` — 18/18 (bp-000 1–7 re-run by reference +
(c)-committed self-clears under a deliberately stale baseline, (c)-uncommitted blocks, (b)-regression,
digest-fidelity). Independently re-checked by a 4-reviewer adversarial pass (code-correctness /
harness-fidelity / digest-fidelity / discipline-state) — all resolved.

**Next.** Sealed. Surfaced finding-0004 + finding-0005 (both resolved via bp-002).

**Decisions.** finding-0003 → promoted (A1 warrant); finding-0001 → resolved + oq-0001 → answered (A2:
re-home the safety digest only — repo map / phase marker / live-verify stay pointer-only). Hand-mint
justified by authority (owner pre-ratified A1/A2 at §16), not bootstrap.

---

## Agent-workflow layer — bp-002 (A3) landed + committed; plan held at `proposed` (2026-07-05, /triage note — NOT a seal)

Recorded for completeness, **not** a completion seal. bp-002's work (amendment A3) is implemented and
committed (`0e9fc90`, merged `c17a456`) and its findings are terminal, but the plan is **deliberately
held at `status: proposed`**: the session executed under owner authority yet performed no owner-only
`proposed → ready` blessing (plan Provenance note). No seal is written until the owner rules on the
lifecycle.

**Landed.** `.claude/hooks/_lib.py`: `_untracked_under()` + `_untracked_blessing()` make Stop-gate (c)
untracked-inclusive over `docs/design-notes/**` + `docs/build-plans/**/plan.md`, closing the
Bash-minted-`ready`-plan hole (A3, §6c). finding-0004 ambient-path exclusion locked
(`.claude/settings.local.json` gitignored, `868ed17`). Verified by
`docs/build-plans/bp-002/acceptance/run.sh` — 6/6 (18 prior by reference + 0005-regression /
0005-legit / committed-blessing / (c)-uncommitted / 0004 before-after).

**Owner-pending (non-blocking).** (1) Whether to fold bp-002 into the formal
`ready → in-progress → complete` lifecycle (a hand blessing; a committed blessing now self-clears the
audits). (2) §14-parked *pre-hoc* denylist of `docs/build-plans/**/plan.md` `status: ready` writes, as
belt-and-suspenders over A3's post-hoc catch. finding-0005 → promoted; finding-0004 → resolved.

---

## Agent-workflow layer — bp-003 (A4) landed + committed; plan held at `proposed` (2026-07-05, /triage note — NOT a seal)

Recorded for completeness, **not** a completion seal (parity with the bp-002 note above; backfilled
2026-07-06 — bp-003 had no prior PROGRESS record). bp-003's work — installing amendment **A4**, the
build-plan template overhaul — is implemented and committed (`9b2431f`) and its findings are terminal,
but the plan is **deliberately held at `status: proposed`**: the session executed under owner authority
yet performed no owner-only `proposed → ready` blessing and did not flip the plan (plan Provenance note).
No seal is written until the owner rules on the lifecycle (the same open decision bp-002 carries).

**Landed.** `docs/templates/build-plan.md` upgraded to the investigate→reconcile→plan form (A4, warrant
finding-0007): §0–§12 with per-item acceptance **and** a named falsifier, `path:line`-cited Investigation
for plans touching code, banner-vs-cross-reference Reconciliation, explicit Math field-guide clauses,
blast-radius ordering, dependency/parallelizable edges, and N/A-marking discipline (one template, not two
tiers). The `graduate` skill became a grounded planning pass and `build-plan` gained the richer semantics.
Installing A4 against the §3 prose surfaced the schema contradiction filed as **finding-0008** (later
reconciled by A6/bp-004). Journal declares terminal: all five criteria closed, "In-flight. None."

**Owner-pending (non-blocking).** Whether to fold bp-003 into the formal
`ready → in-progress → complete` lifecycle (a hand blessing; a committed blessing self-clears the audits)
— the same standing decision as bp-002. finding-0007 → promoted (the template-thinness warrant A4
answers); finding-0008 → filed by this plan, later promoted via A6/bp-004.

---

## Agent-workflow layer — bp-004 sealed: A5 + A6 mechanical fixes (2026-07-06, /triage)

The mechanical consequence of amendments **A5** (finding-0006) and **A6** (finding-0008),
already ratified into `agent-workflow.md` §3/§6/§16. Unlike bp-002, bp-004 ran the **formal
lifecycle** (owner blessed `proposed → ready` at session start; builder `ready → in-progress`),
so its terminal is `complete`. This is the orchestrator's deferred single-writer act — flip
`in-progress → complete`, seal the journal, write this checkpoint — the three acts the builder
left out of its lane (§5). Work committed `1e0443f`, merged `1328ae6`; tree clean.

**Built.** `.claude/hooks/_lib.py`: `_normalize_status` (strip a trailing ` #` YAML comment from a
*status* value — cut at first space-hash, then rstrip; status-path only) applied at **all three**
status-extraction sites — `status_of`, `_status_in_text`, and `_blessing_in_diff:394` (the third
routes through neither named extractor, so without it the tracked Stop-gate path stayed unfixed).
All three blessing detectors now fire on a comment-bearing `ready`/`ratified`; `ready#x` (no space)
is deliberately not stripped (false-negative-only, the safe direction); `_scalar`/`parse_front_matter`
unchanged so a `#` survives in other fields. `docs/templates/build-plan.md`: status line comment
removed (A5), `re_entry` restored as a front-matter key (A6). `.claude/commands/{build,graduate,scribe}.md`:
the four moved fields (`objective`/`context_manifest`/`non_goals`/`stop_conditions`) now read from
the §1/§2/§9/§10 body sections, not front-matter keys (A6); `re_entry` stays a front-matter key.

**Verified.** `docs/build-plans/bp-004/acceptance/run.sh` — **21/21 (PASS=21 FAIL=0)**: bp-002's 18
prior criteria by reference (green under the A5 change — a no-op on clean status lines) + 0006-strip
(comment-bearing `ready` blocks on gate-guard hook-mode, Stop-gate tracked, Stop-gate untracked, each
beside a clean-`ready` control that also blocks) + 0006-nospace (`ready#x` does NOT over-fire) +
0006-scope (a non-status `#` survives `parse_front_matter`) + template/command/finding grep checks.

**Next.** Sealed. Two §11 parked decisions remain deliberately out of scope with re-entry conditions
(normalize `cmd_brief`'s cosmetic status render `_lib.py:533`; a belt-and-suspenders `cmd_gate_check`
normalization on the `--standalone` debug path) — neither carries a bright-line stake.

**Decisions.** finding-0006 → promoted (A5 warrant), finding-0008 → promoted (A6 warrant); both
resolutions cite the amendment + bp-004 + the harness. No design-note edit (A5/A6 pre-ratified by
the owner); no blessing flip; `complete` is the orchestrator's completion act, not a gate.

---

## Agent-workflow layer — bp-002 + bp-003 sealed: regularized to `complete` per oq-0002 (2026-07-06, /triage)

Owner ruling (`owner-questions.md` oq-0002): fold bp-002 (A3) and bp-003 (A4) into the formal
lifecycle so the board is uniform — no `proposed`-held plans whose work is already committed.
Enacted respecting the blessing gate: the **owner** hand-blessed each `proposed → ready` (owner-only,
§10 — deliberately not an agent act, since a direct `proposed → complete` edit would bypass the
readiness gate, finding-0009); the **orchestrator** then flipped each `ready → complete`, sealed both
journals, and wrote this checkpoint. Supersedes the two "NOT a seal" held-state notes above (bp-002
2026-07-05; bp-003 backfilled 2026-07-06) — append-only, so those remain as history.

**Built (already committed; full detail in the two notes above + each plan's journal).**
- **bp-002 (A3, committed `0e9fc90`, merged `c17a456`).** Made the Stop-gate (c) audit
  untracked-inclusive over `docs/design-notes/**` + `docs/build-plans/**/plan.md` (`_untracked_under`
  / `_untracked_blessing`), closing the Bash-minted-`ready`-plan hole (finding-0005 → promoted);
  locked finding-0004's ambient-path exclusion (`.gitignore`, `868ed17`; finding-0004 → resolved).
- **bp-003 (A4, committed `9b2431f`).** Installed the investigate→reconcile→plan build-plan template
  and the graduate (grounded planning pass) + build-plan (richer semantics) skill upgrades
  (finding-0007 → promoted). Installing A4 surfaced the §3-schema / command-file drift filed as
  finding-0008 (later reconciled by A6/bp-004).

**Verified.** bp-002 `acceptance/run.sh` re-run green at current HEAD — **6/6 (PASS=6 FAIL=0; 23
assertions)**, the A5 `_lib.py` change a confirmed no-op on its clean status lines. bp-003 has no
harness; its journal records all five criteria closed (required-section grep + a no-implementation
graduate dry-run) and finding-0007 terminal. Both journals now sealed; working tree clean post-commit.

**Next.** Board uniform — bp-000 / bp-001 / bp-002 / bp-003 / bp-004 all `complete`. bp-002's
§14-parked pre-hoc `status: ready` denylist stays a separate open decision; finding-0009 (the
`proposed → complete` gate hole) is a candidate amendment **A7**, owner's ratify call.

**Decisions.** oq-0002 answered → **swept** (this checkpoint is the sweep). No agent performed a
blessing — the owner supplied both `proposed → ready` blessings by hand; the orchestrator did only
the agent-legal `ready → complete` flips + seals.

---

## Reflection sweep — the 2026-07 corpus-audit findings routed (2026-07-08, /triage)

Cleared the 13-finding unswept backlog (the 2026-07 corpus audit + verification cohort). Orchestrator
single-writer actions only — no design-note edit, no blessing flip; every design change is drafted for
the owner at the blessing gate.

**Routed (12 open → `routed`; 1 `resolved`).** finding-0009 → oq-0003 (**A7**, the `proposed →
{in-progress,complete}` egress-gate hole — promotion proposed, warrant-linked). 0010 → oq-0004
(design-note status hygiene). 0013 → oq-0005 (edge/supersession note↔code reconciliations + ratify the
drafted `recursive-strata-amendment`). 0014 → oq-0006 (Invariant-2 firewall asymmetry + CI topology).
0017 → oq-0009 (planar_graphs orphan). 0019 → oq-0008 (airlock design-record + driver + ahead-of-code
Vault provisioning). 0020 → oq-0007, the **built-vs-deployed-vs-wired umbrella**, folding the accuracy
facets of 0011/0012/0015/0016/0019. Parked-pending-forward-build (no owner question; roadmap
sequencing): 0012 (Item 8), 0015 (A2), 0016 (Track D). **finding-0018 → `resolved`** — its audit-method
fix (derive source-dir scope empirically; reconcile flag-off-vs-live before a WIRED verdict) is already
captured + applied in `docs/audits/corpus-state-audit-2026-07-verification.md`; no code change.

**Batched.** 7 owner questions (oq-0003 … oq-0009) in `docs/inbox/owner-questions.md`, each
warrant-linked with a `default_if_unanswered` that degrades to the origin finding's parked state (§10) —
none blocking.

**Two accuracy corrections the orchestrator owns (recorded here, honestly, in one place — findings
0011 / 0013(5) / 0015 / 0020):** the terse tracking surfaces conflate *built/deployed* with
*wired-into-the-live-loop*. Setting the record straight for the specific code-verified overclaims:
- **Effectors (Track G):** cataloged but **NOT wired** — no live entry point constructs any effector;
  the max effector tier reachable in the live/default config is **NONE**, not SENSING
  (`[effectors] enabled=false`; "ε = SENSING" is only the `EffectView` default ctor arg, and nothing
  live constructs an `EffectView`). Supersedes the "WIRED ceiling ε = SENSING" phrasing at `:1085-1087`.
- **`DERIVED_STRATUM` (finding-0013 item 5):** the earlier note that the reservation "was undone; the
  enum has no such label" is stale — `core/provenance.py` still reserves `DERIVED_STRATUM`.
- The drift gauge (A1) and the agency substrate are **built but inert/undriven live** (findings
  0015/0016); the honest built-vs-wired distinction for the CHANGELOG/README summaries awaits the
  owner's chosen form (oq-0007). `docs/PROGRESS.md` remains the self-correcting source of truth.

**Not swept / not done here.** No plan newly `complete` → nothing sealed (bp-005 is `in-progress` —
corpus front-matter conversion; write_scope includes `docs/design-notes/**` (owner-lifted) and
`docs/findings/**`, disjoint from this sweep's already-front-mattered orchestrator-domain findings).
No owner question newly answered → nothing folded back. finding-0021 stays `routed` (its enrichments
land at the pending edge-model / supersession-lifecycle / founding-corpus ratification passes; its
`supersession-recovery-evaluation.md` draft awaits ratification).

**Book debt.** `docs/book/` is unscaffolded (no `SYNC.md`); the first `/scribe` sync plan is still
pending (§12). Many notes have ratified/superseded since — book debt is the whole book. Offered to the
owner, not auto-run.

**Next.** Owner works `owner-questions.md` (oq-0003 … oq-0009); unanswered ones stay safely parked.
Roadmap-parked findings (0012/0015/0016) re-enter with their forward builds (Item 8 / A2 / Track D).

## Reflection sweep — bp-005 sealed; stranded record recovered; A8 proposed (2026-07-09, /triage)

**Recovered (the load-bearing act of this sweep).** bp-005's `journal.md` (53 KB — including
**Appendix A, the 204-hit supersession-marker inventory** that seeds the scrub-pattern file for
`supersession-recovery-evaluation.md` §3, and Appendix B, the created-date provenance table) and
`finding-0023.md` sat **untracked in the `mp-convert-notes` worktree**: the commit the journal's final
entry requested (`66c3e6f`, merged `a33ecab`) took the 33 converted notes + `plan.md` but not the two
untracked files. One `git worktree remove/prune` away from losing a plan deliverable. Both recovered to
main and committed by this sweep. The worktree (and `mp-bp001`, clean) can now be pruned — owner's call.

**Sealed — bp-005 `in-progress → complete` (corpus front-matter conversion).**
- *Built:* 30 design + 3 research notes converted (+13/−0 prepends, prose md5-preserved), design notes
  stamped `implementation:` verbatim from the 2026-07 verification audit; mid-session addendum items 1–4
  delivered (marker inventory, stamps, date provenance, record repair). The run's shape is itself a
  finding trail: denylist collision → revert → owner temp-lift (`d6e518f`) → conversion → restore
  (`f5d435d`).
- *Verified at seal:* all 43 notes under `docs/design-notes/` + `docs/research/` carry front-matter; the
  three post-bp-005 notes (`capability-evaluation-harness`, `observed-stratum-spike`,
  `authorship-distance-axis`) self-carry it at `draft` — the convention propagates unaided.
- *Decisions recorded:* provisional `rn-*` research-note schema (unratified → oq-0010); `updated:` set
  from git last-commit, not conversion date; finding-0024 deleted owner-instructed (its substance lives
  in finding-0025 §"How it surfaced" — the dangling link is annotated there).
- *Next:* nothing in bp-005 re-enters; its two open threads are oq-0010 (schema) and oq-0011 (A8).

**Routed (1).** finding-0023 `open → routed` — no research-note template/schema exists; promotion
proposed (ratify the provisional convention: `docs/templates/research-note.md` + a spec line) → **oq-0010**.

**Promotion proposed (1).** finding-0025 → **amendment A8** (A7 is finding-0009's, oq-0003): replace the
design-notes *location* denylist with a *status*-aware guard — ratified/superseded agent-immutable
(content guard + HEAD-keyed Stop-side check, laundering-proof), drafts writable, blessing gates
untouched. Batched → **oq-0011**. The bp-005 temp-lift episode is the live warrant: the owner
hand-bypassed the global deny to land legal draft work, exactly the missing capability the finding names.

**Swept.** None — no owner question newly answered (oq-0003 … oq-0011 all open). finding-0021 unchanged
(`routed`; rides the pending edge-model / supersession-lifecycle / founding-corpus ratification passes).

**Book debt.** Unchanged: `docs/book/` unscaffolded, first `/scribe` sync plan pending (§12). Nothing
newly ratified since the last sweep (all three new notes are `draft`), so the debt is still "the whole
book," not incremental. `/scribe` on request.

**Next.** Owner works `owner-questions.md` — now **9 open** (oq-0003 … oq-0011), none blocking; every
default degrades to a parked finding with re-entry. A8 (oq-0011) is the highest-leverage answer: it
unblocks agent draft-note authoring (the graduate pipeline's mouth) and ends per-episode temp-lifts.
No plan is `in-progress`; the board is clean for the next `/graduate` or forward-layer build.

## Reflection sweep — finding-0026 routed → oq-0012 (type-checker code plane) (2026-07-10, /triage)

A short sweep: one commit since the last one (`38ccc85` — owner-authored `edge-core-handoff-protocol.md`
+ `type-system-as-core-audit.md` drafts, `biometric-sensor-agent.md` research note, finding-0026, and an
owner tidy of finding-0025's dead finding-0024 link).

**Routed (1) / promotion proposed (1).** finding-0026 `open → routed` — the code plane
(`security-planes.md`: "types enforce it") has **no enforcement**: no type checker installed or
configured, while `ops/import_lint.py` proves the project already runs on the very
promote-to-static-proof argument a checker generalizes. Remedy note `type-system-as-core-audit.md` is
already drafted and warrant-linked (`warrant: finding-0026` — the three-place P/P′/warrant is in place);
its ratification batched → **oq-0012**. On acceptance the finding flips `promoted` and the note's
B-items become graduatable.

**Convention drift noted (evidence appended to oq-0010).** `biometric-sensor-agent.md` deviates from
bp-005's provisional research-note schema on three axes (no `rn-` id prefix, novel `family:` field,
missing `created`/`updated`). Every new research note without a ratified schema mints a dialect —
the reconciliation bill grows until oq-0010 is answered.

**Sealed / swept: none.** No plan is non-terminal (bp-000 … bp-005 all `complete`, journals sealed);
no owner question answered (oq-0003 … oq-0012 all open — now **10**, none blocking). finding-0021
unchanged (`routed`; `supersession-recovery-evaluation.md` confirmed still `draft` — an earlier grep
false-positive from body prose is corrected here for the record: **nothing has been newly ratified**).

**Book debt.** Unchanged — `docs/book/` unscaffolded, first `/scribe` plan pending (§12); no new
ratifications, so still whole-book, not incremental.

**Next.** The inbox is the bottleneck: 10 open questions, all parked-safe, none blocking. Highest
leverage remain A8 (oq-0011, unblocks agent draft-note authoring) and A7 (oq-0003, closes the gate-egress
hole); oq-0012 is the newest blessing decision. Three owner drafts now sit at `draft` awaiting the gate
(`edge-core-handoff-protocol`, `type-system-as-core-audit`, `authorship-distance-axis` et al.) — each
ratification opens a `/graduate` lane.

## Ouroboros goes live — founding ingest, always-on, deploy gate, CI, delegation (2026-07-11, orchestrator checkpoint)

The day the framework became a running system. Owner-directed throughout; every gate held.
(Named this day too: **mind-palace = the framework; Ouroboros = the live system** — the name is
from the founding note itself.)

**Founding corpus (seeded, sealed, supersession-linked).** Two owner musings ingested via the
founding path (`ingested=2 chunks=8`), reconstructed dates honest (auto-timestamped creation),
owner-declared authored-historical edge `4c20a5d3… → 6e28b56b…` ("This is the founding corpus"
supersedes "Ouroboros — a study on process", owner ruling). Byte-identity established: vault files
== founding-composed bytes == catalog == edge digests, so rescans are no-ops. First dream (05:45):
grounded=true, citations pass, one cluster of both notes — and it independently surfaced the
intra-note self-supersession ("Foundation vs. Entropy"). Dream idempotency PROVEN live: second pass
produced the identical content-addressed artifact (same id, two attestations) — an unchanged corpus
cannot accumulate dream duplicates. `mind-palace supersede <old> <new>` added for the phone-capture
flow (shortcut emits new timestamped files; in-place edits take the version path instead).

**Always-on.** launchd agent (KeepAlive) owns the daemon; owner set clamshell power config; old
standalone watcher retired (was a live second ingest path); supervisor collision untangled (recovery
mode behaved exactly as designed). Corollary documented: under KeepAlive, `palace stop` = restart;
true stop is `launchctl bootout`. reset now wipes the four provenance sidecar stores it missed.

**The code stream.** Per-commit structural snapshots (`ops/code_snapshot.py`, backfilled 90 commits
in ~4s, ledger now 113+) run by a model-less `code_sensor` pipeline agent (git-read + ledger-write +
attest, the vault-watcher species) on a main-only post-commit hook. Commit house rule (CONVENTIONS
§Commits): typed headers parsed into ledger lookup columns. uv adopted everywhere (shim, plists,
backup, docs). An UNDECLARED core dependency (ripser — persistent homology) was exposed by frozen CI
envs and pinned.

**Deploy/promote gate (`palace deploy`) — the ONE owner-in-loop gate.** Clean tree + main + new SHA
+ ratchet green + ATTESTED remote-green (ci_witness polls the pipeline, emits
`ci_witness/pipeline_green` chained to the commit's ingest) → graceful cycle via KeepAlive →
successor-SHA verified → semantic-release played via Keychain PAT. Token self-rotation
(verify-before-store, attested, weekly plist available; PAT verified live: api+self_rotate scopes).
Push-to-origin is routine by owner rule; releases follow deployments.

**CI (free-tier sized).** `ratchet` job (ruff + import-firewall + 743-test model-free tier, ~54-77s,
uv-cached, docs-only pushes skip) + `vault-axis` job (dev-Vault service proves AppRole policies,
auth-paths only — green first try). Five debugging iterations, each a real fix: repo-wide lint debt,
.claude outside its own gate, py3.12 wheel floor validated, gitless slim image, the ripser gap.
Pipeline metadata is public; verification loop = push → poll API → failure_reason → `git archive
HEAD | podman run` exact-job reproduction.

**Type plane (finding-0026 → promoted).** Owner ratified `type-system-as-core-audit.md` (10c9a66,
blessing committed at the Stop-gate's demand); oq-0012 swept. B-1 bootstrap landed same day:
two-tier mypy config, baseline 463 errors/134 files (core 193) inventoried in
`docs/audits/mypy-baseline-2026-07-11.md`. /graduate produced bp-006..bp-009 (proposed→READY by
owner's hand, fbdd738): Tier-1 triage+shims+strict-green → Tier-2 floor ∥ static-shadow spike →
CI type-gate. PD-1's re-entry FIRED (CI became a pytest host today; mp-finish does not exist).

**Delegated builders (owner rule; delegate skill).** Orchestrator may spawn supervised parallel
builders in isolated worktrees for ready plans; right-size to verification complexity; merge-to-main
broadcasts to active worktrees; diff scrutiny before every merge; gates unchanged. **bp-006's builder
is running now** (full-strength, own worktree) — first delegated build in the project's history.
`.claude/worktrees/` gitignored after it tripped deploy's clean-tree gate (gate correct, infra new).

**Watching for (pre-written re-entry signatures):** PD-2 unparks if bp-006's T1s cluster at the
ingestion boundary; PD-4 (Rust split) gets evidence either way; bp-009 feeds the axis note's
tagging-grain question and forces the OwnerVerdict type (verdict-taxonomy accelerant); the delegate
mode itself needs an agent-workflow amendment (A9 candidate) once the first sequence's findings land.

**Next.** bp-006 reports → diff scrutiny → merge → spawn bp-007 ∥ bp-009 → bp-008. Owner: deploy at
will (gate armed end-to-end); the 9 open owner questions (oq-0003..0011) stand, A8 (agent draft-note
authoring) still the highest-leverage unanswered. Formal /triage on bp-006 completion (route its
findings, seal, checkpoint).

---

### Checkpoint 2026-07-11 (late) — bp-008 sealed; bp-011 in flight (supervision session)

**Type-plane build sequence landed.** bp-006/007/009/010 complete (sealed in their journals). **bp-008
COMPLETE this session** (merge `b804a49`, seals `2893c80`+`8b2b8de`): the CI `type-gate` job +
`ops/type_gate.py` (`membership()` Tier-2 import invariant + `bare_ignores()` tokenize-based scan),
11 unit tests. All three B-2 falsifiers confirmed LIVE in CI — (i) type-error `2669813352`, (ii)
membership `2669813994`, (iii) bare-ignore `2669822550` — each also locally reproduced; green baseline
`2669812161`. main's `type-gate` mirrors `ratchet` (no `needs:`).

**Delegation lesson (recorded).** bp-008's builder was assumed dead (mid-poll `.output` snapshot) but
was only slow-polling a runner-starved pipeline; it retried, completed, and cleaned up while the
orchestrator raced it to seal. Both converged; the builder's completion notification endorsed the seal
+ `finding-0032` routing. Cost (measured, post-seal): sonnet, 201741 tok / 263 tool-uses / ~37 min.
**Rule reinforced for handoffs:** a spawned builder that looks idle may be polling — inspect worktree +
journal, and if it may still be live, WAIT/poll rather than race it.

**finding-0032 (direction, routed):** should the code gates (`type-gate` AND `ratchet`) carry
`needs: []` to run independently of a red `.pre`/release stage? Builder committed `needs:[]` cleanly
(`0d843d2`, raced off, never reached main); NOT adopted at merge (direction-typed, implicates both
jobs). Owner decision.

**In flight.** bp-011 builder spawned (sonnet, worktree, background, est 350k) — B-a docstring ledger
column + V4 read-only reference inventory. Its V4 keep/no-signal verdict GATES bp-013. Then bp-012
(full-strength, SEQUENTIAL — shares `ops/code_sensor.py`; write_scope may need
`ops/lifecycle/launcher.py` added by owner for Item 4, else it parks). bp-013 gated on bp-011 verdict +
bp-012 merged.

**Next.** Scrutinize+merge bp-011 → seal → bp-012 → bp-013 (or un-bless if V4 no-signal). Closing
/triage: route findings 0027-0032, full PROGRESS catch-up, queue owner items (A9 amendment candidate;
cost-forecasting re-entry). Owner desk: oq-0003..0010.

---

### Checkpoint 2026-07-11 (evening) — trilogy 2/3 sealed, bp-013 in flight; session clearing

**bp-011 + bp-012 sealed** (code-observation trilogy, `code-observation-projection.md`):
- bp-011 (docstring ledger column + V4 inventory verdict KEEP) merged `a7d4eb0`; cost sonnet
  163k = 0.47× est. Real ledger auto-migrated on merge (doc_coverage 28.4%).
- bp-012 (code-observation store + φ_code projection seam, B-b) sealed `88cf58c`; cost fable
  157k = 0.52× est. No-provenance store + §2.6 MirrorView opacity + B-b idempotency verified.
  **φ_code now projects WRITE-SIDE on commit (`projected=N`); the daemon does NOT consume it
  (finding-0020 class) — no deploy needed to "apply" the trilogy.**

**bp-013 IN FLIGHT** — builder spawned (fable, worktree `.claude/worktrees/agent-a80bc7f9344a9a5af`,
branch `worktree-agent-a80bc7f9344a9a5af`, NO push). Last piece: reference-edge store +
precision-gated extraction + THE isolation proof (bit-identical instruments with/without edges =
B-c falsifier). **Reset-registration PARKED** (launcher.py not in its scope — a premature
amendment was reverted; builder instructed to park it). **Orchestrator OWES post-merge:** add
`data/reference_edges.sqlite` to `reset_targets()` in `ops/lifecycle/launcher.py` (owner-concurred,
oq-0013 extension).

**bp-014 READY — owner-blessed by hand 2026-07-11.** Worktree-aware ROOT resolution (finding-0031
fix, 3 manifestations today). `depends_on: [bp-012, bp-013]` — enforcement hooks must not change
while builders run; **first unit AFTER bp-013 seals**, FULL-STRENGTH (enforcement layer). Includes
an opportunistic write_scope inline-comment parser fix.

**Findings:** 0032 (needs:[] CI-topology, owner-ADOPTED → mint a small CI plan), 0033 (bp-011
builder's finding-0031 corroboration), 0034 (CI runner-minute bottleneck, owner-DIRECTED → MicroVM/
GitHub runner design note).

**Runner budget ~55/400** — every push burns next-version + security scans (no rules:changes);
deploy needs an attested-green pipeline so exhaustion blocks deploy. Builds don't push; orchestrator
batches. Snapshot at `e576c7d`; ~7 commits unpushed since (bp-012 seal) — batch-push with bp-013.

**Design-tier threads captured (for a Fable/xhigh session):** `docs/brainstorms/self-sensing.md`
(agent-as-self-sensor / proprioception / worldview-projection via §2.2 supersession — owner-directed
capture); `finding-0034` (AWS Lambda MicroVMs, real 2026-06-22, vs GitHub Actions — repo already
mirrored to github.com/ascalva/Mind-Palace); cost-forecasting report generator (2 datapoints now,
both under-estimate — the sizing runs conservative).

**Next session (supervision-tier):** inspect bp-013 worktree/journal → scrutinize+merge+seal (+
register the reset target) → batch-push → bp-014 (full-strength) → finding-0032 CI plan → /triage.

---

### Checkpoint 2026-07-11 (late evening) — trilogy COMPLETE (bp-013 sealed); CI/runner pivots to priority

**bp-013 SEALED — the code-observation trilogy is DONE.** Lane-1 reference edges (B-c),
merged `d824abc`, sealed `ef9319e`. Resume builder (opus, 54k/44 calls) finished Item 8 after
the prior session's builder landed Items 6-7; the resume-from-worktree path worked cleanly
(builder correctly refused to merge when it saw main had advanced — good discipline).
- **Item 8 isolation proof PASSES, genuinely** — plants real edges whose corpus endpoints ARE
  node digests of the complex (both directions, validated ref_types), proves the full instrument
  stack (frustration/curvature/clustering) bit-identical with/without a populated store. B-c
  falsifier now automated forever. `core/complex/**` + `core/stores/edges.py` untouched.
- **Triple-green on main:** ruff clean · mypy 0/69 (finding-0029 baseline) · firewall OK ·
  **804 passed**.
- **Item 7 both-directions accepted** (finding-0036, renumbered from a 0035 collision with the
  self-resume-practice finding) — §1's objective pins the whole bp-011 validated set incl.
  corpus→code/path-mention (rank 2, 100%, the finding-0021 direction).
- **Parked Q4 reset target REGISTERED** (`11ffc01`): `reference_edges.sqlite` joins
  `reset_targets()` + the corpus-wipe test seed; `test_lifecycle.py` 20/20.

**B-c family closes.** Lane 1 built + proven isolated; Lane 2 (semantic proposals) + B-d (the
detangling consumer) remain gated on Track D. No deploy needed (write-side; finding-0020 class).

**CI/RUNNER — the trigger fired, now PRIORITY (owner-directed 2026-07-11 eve).**
- **GitLab shared runners are EXHAUSTED (0 min)** — no working GitLab gate at all until reset.
  finding-0034's "minute floor" re-entry trigger has fired.
- **GitHub mirror confirmed PUBLIC** → unlimited free GitHub Actions. finding-0034's "cheapest
  fix of ALL" branch is now live. Push-mirror (main-only, SSH) is a platform feature (not a CI
  job), so it still mirrors; the hops are fine — the real gap is `.github/workflows/ci.yml` is
  STALE (no mypy type-gate, no SAST/secret-detection, no semantic-release, pre-uv) = a FALSE
  GREEN if trusted.
- **Owner's fork** (captured in finding-0034 evening addendum): GitHub as (a) destination, (b)
  bootstrap → AWS Lambda MicroVM runners (MicroVM tooling is GitHub-Actions-FIRST = the mature
  path), or (c) both/split (GitHub-hosted for the cheap gate; MicroVM where Firecracker isolation
  is load-bearing). Owner chose: **mint a proper design note + plan (Fable/xhigh)**, not a
  supervision hack. finding-0032's GitLab `needs:[]` is largely SUBSUMED by a GitHub migration.
- Pushing is now unconstrained (GitLab pipelines dead; owner: "doesn't matter if you push").

**bp-014 READY** (owner-blessed) — worktree-aware ROOT resolution (finding-0031). Now that the
trilogy's done, sequenced next among the BUILD units. Full-strength (enforcement layer).

**Next session — DESIGN-TIER (Fable/xhigh):** promote finding-0034 + finding-0032 → runner-strategy
design note (structured on the a/b/c fork; first gate = confirm nothing sensitive in the public
tree) → ratify (owner) → /graduate. Then supervision-tier: bp-014, then /triage (sweep findings
0027-0036, batch owner questions, promotions). Owner desk: oq-0003..0010.

### Checkpoint 2026-07-11 (night) — CI/runner design note DRAFTED (Fable/xhigh); ratification asked (oq-0014)

**`docs/design-notes/ci-platform-and-runner-strategy.md` drafted** (promotes finding-0034, folds
finding-0032). The owner's (a)/(b)/(c) fork resolves as a SEQUENCE: **(a) GitHub Actions becomes
the authoritative gate now** (unlimited free, public repo); **(b) MicroVM runners PARK on three
triggers** (CI executes untrusted/AI code · hosted limits bite · repo goes private); (c) arrives
exactly when a trigger fires. Grounding done this session:
- **Gate 0 CLEARED** — public-tree check: 669 tracked files clean (only synthetic golden corpus +
  reconciliation audits); full-history pattern scan 0 hits (AKIA/PEM/glpat/ghp/xox/sk-); PII =
  555-fixtures only. Residual: one real gitleaks full-history run → Plan A acceptance item.
- **New structural fact (P5):** `.releaserc.json` commit-back (`@semantic-release/git`) means the
  release host MUST be the origin host — "semantic-release on GitHub + GitLab origin" would fork
  main and break the mirror. So release-home = repo-host decision → **D4, the ratification ruling**
  (recommended end-state: GitHub becomes origin; interim default: GitLab origin + owner cuts
  releases locally, zero minutes).
- **Live observation:** Actions DO fire on mirror pushes, and the stale workflow is **red-at-install**
  (not false-green): `pip install -e '.[dev]'` fails in both installing jobs (run 29169533661 on
  `ef9319ea`); dep-free `import-firewall` passes. A re-pointed witness today would hard-block deploy
  → parity (Plan A) strictly precedes the witness re-point (Plan B).
- **finding-0032 → closed as SUBSUMED** (D6: GitHub jobs are independent by construction; no GitLab
  `needs:[]` plan minted). finding-0034 → promoted (resolution lines updated on both).
- **Consequences sketched for /graduate:** Plan A (parity gate: uv + ruff + check_imports + mypy
  0/69 split + pytest markers + vault service-container + semgrep/gitleaks + tombstone
  `.gitlab-ci.yml`; NO paths-filters — every main sha yields a verdict, P2) · Plan B (ci_witness
  GitHub backend, Keychain `github-api`, absent-grace) · Plan C (docs → GitHub Pages).
- **oq-0014 filed (blocking: true):** ratify the note + rule D4. Desk now oq-0003..0010 + 0014.

**Next:** if ratified → `/graduate` the note (Fable/xhigh). Else → bp-014 (opus/default,
supervision; finding-0031 fix + finding-0035 hook mechanism). Then /triage.

### Checkpoint 2026-07-11 (late night) — /graduate DONE: bp-015/016/017 minted `proposed` (Fable/xhigh)

**The ratified `dn-ci-platform-and-runner-strategy` graduated into three plans**, grounded
pass complete (every §3 claim carries a `path:line` citation; commands pinned verbatim §6):

- **bp-015 — Plan A, the parity gate** (opus est. 250k): rebuild `.github/workflows/ci.yml`
  as five independent jobs (ratchet · type-gate 0/69 · vault-axis service-container · semgrep
  · gitleaks full-history = Gate-0 residual discharge) + tombstone `.gitlab-ci.yml` + runbook
  §Verifying correction. New grounding this pass: the 4-marker pytest exclusion does NOT leak
  `longitudinal` (measured: 808/828 collected, 0 longitudinal — `tests/longitudinal` never
  enters collection); vault service resolves via `localhost:8200` port-map on GitHub (env-only
  deviation; tests read `VAULT_ADDR`); the `chore(release)` skip rule deliberately not ported
  (P2). Live wiring proof (green→red-canary→green) is orchestrator-executed — builders never push.
- **bp-016 — Plan B, witness re-point + release relocation** (fable est. 300k; depends bp-015):
  GitHub backend in `ops/ci_witness.py` (query `ci.yml` runs by head_sha; ONLY
  `completed`+`success` = green; absent-grace 300 s inside `check()`; emission keeps
  `pipeline_green|red` action names, output `pipeline:→run:`); CLI/launcher contract
  byte-frozen. **Deviation surfaced:** GitHub has no PAT self-rotation endpoint — `rotate()`
  becomes guided-manual (Item 8, owner sees it at the gate). Release relocation (Item 10) is
  **P5-guarded**: parks until the owner's origin re-point + tag-parity check (`v*` tags may
  not have mirrored — pre-check pinned). Owner-step ledger (PAT mint · re-point+tags · mirror
  retirement · scanning toggles) lives in the journal from day one. Found+repairing: the
  witness docstring's "runbook §CI witness" points at a section that doesn't exist.
- **bp-017 — Plan C, docs → GitHub Pages** (sonnet est. 100k; depends bp-015, ∥ bp-016): port
  the one-command uvx mkdocs build to a `pages.yml` workflow + re-point `mkdocs.yml` URLs
  (default `ascalva.github.io/Mind-Palace`, note parked #4). Kept separate from A: A's
  red-proof burden is already a session; C has its own crisp checker.

All three `proposed` — **`proposed → ready` is the owner's, by hand, item-by-item.** Family
item numbering 1–13 across the trio. bp-014 (ready) remains parallel-safe with bp-015
(disjoint scopes); owner priority sequences the two lanes.

**Next:** owner blesses any of bp-015/016/017 → delegate per plan tier. Meanwhile
supervision-tier: bp-014 build, then /triage (findings 0027–0036 sweep, oq-0013/0014
answer-sweep, promotions, seals).

### Checkpoint 2026-07-12 — bp-015 built (delegated opus builder); CI live 4/5 green, semgrep parked on owner (opus/default supervision)

**bp-015 flipped `ready → in-progress`; delegated one opus builder in a worktree** (delegate
skill). Builder closed Items 1–4 cleanly: `.github/workflows/ci.yml` rebuilt as five independent
jobs (commands byte-match `.gitlab-ci.yml`), `.gitlab-ci.yml` tombstoned, runbook repointed,
gitleaks full-history clean (226 commits, 0 → Gate-0 residual discharged), all five gates
red-proven locally, no code bent to the gate, no findings. Diff scrutinized in-scope, ratchet
green, merged to main (`e14be25`). Builder usage: **63,994 tokens · 55 tool calls · ~513 s · opus**
(ledger, context-economy skill).

**Item 5 (orchestrator-executed) — the live wiring exposed two things the local red-proofs
structurally couldn't:**
1. **Green-run attempt 1 FAILED** (run 29179344841): 4/5 jobs died at "Set up job" —
   `astral-sh/setup-uv@v8` doesn't resolve (the v8 series ships exact tags `v8.0.0`…`v8.3.2`,
   **no moving `v8` major alias**; `v6`/`v7` have one). Wiring defect in bp-015's own file →
   orchestrator pinned all four refs to `@v8.3.2` (`8d534a0`), actionlint 0.
2. **Green-run attempt 2 = 4/5 GREEN** (run 29179448272, sha `8d534a0`): `ratchet`, `type-gate`
   (exact-69 mypy baseline holds on GitHub), `vault-axis` (service container works under host
   networking — §10 risk cleared), `gitleaks` all pass. **`semgrep` red on 22 pre-existing
   blocking findings** (`p/default --error`, 432 rules/508 files) — an audit backlog (loopback
   urllib, internal-constant SQL f-strings, terraform.aws hardening, a `mutable-action-tag` rule
   flagging our own refs), none exploitable core vulns.

**Decision routed, not made (§9/§10):** GitLab's SAST was report-only; the plan's deliberate
`--error` made this gate stricter-than-parity and never verified green-on-clean. Filed
**finding-0037** (design) + **oq-0015** (blocking: true — keep-blocking-and-triage vs
report-only-parity vs narrow-ruleset). `semgrep` job **PARKED** (independent job; its red doesn't
stop the other four). **Item 4 falsifier PASS** — no GitLab pipeline created for the tombstoned
shas. **Canary DEFERRED** (exit-code propagation already proven by the mixed red/green run;
bundle with the semgrep re-verify at seal).

**Also this session:** bp-016 owner-step ledger **(a) PAT → DONE** — PAT stored + authed against
the workflows API (HTTP 200). SSH already done. Steps (b)/(c)/(d) still OWED.

**State:** bp-015 **stays `in-progress`** — sealing waits on the owner's oq-0015 ruling (+ the
bundled canary re-verify). 4/5 CI jobs live and green; tombstone effective; GitLab lane dead by
construction. bp-016/bp-017 correctly wait on bp-015's seal (don't build the witness until
"attestable green" is defined — oq-0015 defines it).

**Next (owner-gated):** owner answers **oq-0015** (semgrep block-vs-report). Then a DESIGN-tier
session (Fable/xhigh) sweeps the ruling, does the semgrep re-verify + ratchet canary, seals
bp-015, and the bp-016 ∥ bp-017 lane opens. Independent of oq-0015: **bp-014** (opus/default,
finding-0031 + finding-0035) may run any time no other builder is active. Also owed: /triage
(findings 0027–0037, oq-0013/0014 answer-sweep).

**SEAL (same session, 2026-07-12): oq-0015 answered live → bp-015 COMPLETE.** Owner ruled
**report-only** (GitLab-SAST parity; finding-0037 resolved). Applied (semgrep `--error` dropped),
re-verified, and the Item-5 canary ran to completion — **green→red→green** on three main shas:
GREEN [29183251392](https://github.com/ascalva/Mind-Palace/actions/runs/29183251392) (`739dc98`,
5/5) → RED [29183299956](https://github.com/ascalva/Mind-Palace/actions/runs/29183299956)
(`874afcd`, ratchet-only on a planted F401) → GREEN
[29183331779](https://github.com/ascalva/Mind-Palace/actions/runs/29183331779) (`e8eed02`, 5/5).
bp-015 flipped `in-progress → complete`; journal sealed; cost.actual ledgered (builder 64k/55/513s
opus). **CI is live on GitHub Actions** (every sha yields a verdict; GitLab tombstoned+dead;
runbook repointed). "Attestable green" now defined: 4 blocking jobs + semgrep report-only. The 22
semgrep findings persist as a finding-0037 triage backlog. **bp-016 ∥ bp-017 unblocked.**

**Next:** DESIGN (Fable/xhigh) — delegate **bp-016** (fable witness) ∥ **bp-017** (sonnet Pages),
disjoint scopes, both gated on this now-complete seal. Or **bp-014** (opus/default) if run alone
(no other builder concurrent, §12). Then /triage (findings 0027–0037 + oq-0013/0014/0015 sweeps).

---

## 2026-07-12 — bp-014 COMPLETE (worktree-aware ROOT + resume-brief auto-surface). finding-0031 + finding-0035(rec3) landed.

**The unit:** bp-014, delegated to one opus builder in an isolated worktree (solo — §12 forbids
any concurrent builder while `.claude/hooks/**` changes under enforcement). Fixes **finding-0031**
(the worktree pointer-bleed that mis-scoped every delegated builder) and folds **finding-0035**
rec-3 (auto-surface the resume-brief). Suite now **824 passed / 8 skipped**.

**What landed (5 cherry-picked commits `65825e7..d2137ef` onto main):**
- **Item 1 — worktree-aware ROOT** (`_lib.py:repo_root()` + all six wrappers, lock-step): prefer
  the CWD git-worktree toplevel over `CLAUDE_PROJECT_DIR` when they differ AND the CWD-toplevel
  carries its own `.claude/state/`; else byte-identical to before. Both sides realpath-normalized
  (`pwd -P` / `os.path.realpath`) so `/tmp`→`/private/tmp` symlink drift can't spoof the compare.
  Fail-closed: a broad main pointer never loosens a narrow worktree builder.
- **Item 2 — two-worktree regression harness** (`tests/integration/test_worktree_enforcement.py`,
  4 cases a–d). **Red→green proven**: pre-fix `3 failed, 1 passed` (the unsafe direction (c) goes
  red — the loosening slips through); post-fix `4 passed`. Case (c) is non-vacuous (flips main to
  the BROAD plan, asserts the NARROW worktree stays fail-closed).
- **Item 3 — resume-brief auto-surface** (`session-brief.sh`): emits `.claude/state/resume-brief.md`
  at the TOP of the SESSION BRIEF, under the worktree-aware ROOT, fail-open, absent-case identical.
  Verified live on main. finding-0035 annotated **partially-addressed** (recs 1+2 — the template +
  context-economy rule — route at /triage; status stays `routed`).
- **§5 fold** — `_lib.py:_scalar()` now discards a trailing inline comment on a *quoted* write_scope
  entry (`"path"  # note`→`path`); unquoted `#` untouched. Fixes the oq-0013 mis-parse.

**Merge discipline:** diff scrutinized (scope clean, 11 files all in write_scope); independently
re-ran full gate (824 passed, ruff clean, `bash -n` clean ×6); live-on-main smoke test confirmed
enforcement healthy (denylist DENY, common-case ALLOW, ROOT=main, Item 3 surfacing). One misread
corrected: the branch forked off `origin/main` (f8b3a40) before the Item-3 plan commit, so the
apparent "plan.md reversion" was pure divergence — builder exonerated. cost.actual: opus 101k tok
/ 85 calls / 764s (est. was fable/350k).

**finding-0031 significance:** the pointer-bleed that de-risks the delegate mode is now fixed — a
delegated builder is enforced against ITS OWN plan, and a bare orchestrator is never falsely
guarded by a builder's bled pointer. The bp-016 ∥ bp-017 parallel lane no longer rides on the
by-eye/diff-scrutiny backstop alone.

**Next:** push → watch the CI witness (5-job attestable green). Then the **bp-016 (fable witness)
∥ bp-017 (sonnet Pages)** parallel lane opens (disjoint scopes, both gated on bp-015's seal — now
long done). Then DESIGN-tier **/triage** (findings 0027–0037; oq-0013/0014/0015 answer-sweeps).

## Reflection sweep — findings 0027–0038 drained; oq-0013/0014/0015 swept; bp-014 + bp-015 journals sealed (2026-07-12, /triage)

**Board after the sweep** — every sweep-target finding is now terminal or parked-with-re-entry:

- **Resolved:** **0031** + **0033** (both fixed by bp-014's worktree-aware ROOT — the
  pointer-bleed and path-resolution manifestations of one root cause; two-worktree harness
  red→green + CI run 29185014622 verify); **0035** (all three resume-brief recs landed: bp-014's
  auto-surface + this sweep's `docs/templates/resume-brief.md` + the context-economy
  location/lifecycle/schema rule); **0038** (promoted into the delegate skill — "green locally"
  now means the FULL five-part gate with the argless-mypy `== 69` assertion, carried verbatim in
  every delegation prompt; rec 3's `scripts/attestable_green.sh` deferred). 0036 (builder,
  in-session) and 0037 (oq-0015's report-only ruling) were already resolved.
- **Promoted:** **0032** + **0034** — both into the ratified `ci-platform-and-runner-strategy.md`
  (owner hand-ratified 2026-07-11): D6 closes `needs:[]` as subsumed-by-construction on GitHub
  Actions; D4 ruled (i) end-state (GitHub becomes origin). Plan A = bp-015 **sealed** (5/5
  attestable green), Plan B = bp-016 ready, Plan C = bp-017 ready; MicroVM runners parked at D7.
- **Routed, parked with re-entry:** **0028** (B-3 spike verdict KEEP stands — falsifier untripped
  at 0 ignores/0 casts; the 6-core+7-test conversion item queues for the type-audit note's next
  `/graduate` wave); **0029** (injectable-dependency ⇒ Protocol — pairs with 0028's conversion
  plan, same seam family; the pinned 69 baseline is its measured footprint); **0030** (float32
  tolerance flake — parked un-silenced for whoever next owns `core/complex/topology.py`); 0027
  unchanged (T1=0 evidence annotates the parked Rust/PyO3 record at its next owner-touched
  revision).
- **Owner desk:** oq-0013 / oq-0014 / oq-0015 swept to origins (bp-012 §5 grant + bp-014 parser
  fold; finding-0034 → promoted; finding-0037). Standing: oq-0003..0010 (8 open, design-tier,
  none blocking).
- **Journals sealed:** bp-014 + bp-015 seal lines appended (their PROGRESS entries pre-existed;
  the seal-line step had been skipped in the moment).
- **Book debt (§11):** `docs/book/` still not scaffolded while FIVE design notes sit ratified —
  the first scribe plan (§12) is pending; offer `/scribe` at a design-tier slot.
- **Deliberately NOT minted this sweep** (carried as deferrals, not lost): the 0028+0029
  conversion plan (a /graduate act against `type-system-as-core-audit.md`), the finding-0037
  22-semgrep backlog plan, `scripts/attestable_green.sh` (0038 rec 3).

**Next:** Fable-first step 2 — promote `docs/brainstorms/self-sensing.md` into a design-note
draft (fable/xhigh, its own session; ratification stays owner-by-hand). Then the bp-016 (fable
builder) ∥ bp-017 (sonnet builder) lane under opus/default supervision, delegation prompts
carrying the full-gate command set per the sharpened delegate skill.

## 2026-07-12 — self-sensing promoted to design-note draft (Fable-first step 2 of 3)

One-unit Fable/xhigh design session, per the front-loaded tier order.

- **`docs/design-notes/self-sensing.md` created (`dn-self-sensing`, `status: draft`)** —
  the proprioceptive projection: φ_self as a second deterministic interpreter over the repo,
  reading the workflow-artifact layer (plan cost blocks, seals) into an OBSERVED-only
  `agent_observations` store through a `CodeSensingHandoff`-style sibling seam. Ratification
  is the owner's hand; `/graduate` refuses it until then.
- **Grounding was verified at source, not asserted:** bp-012's Q1 sibling precedent
  (`core/sensing.py`) answers the brainstorm's own-store-vs-payload question; the built store's
  `INSERT OR IGNORE` + `projections` skip-table implements only same-interpreter idempotence —
  the §2.2 versioned-supersession mechanics the worldview record needs are NOT built yet. The
  note names that gap as B-a (observation-store family; φ_code inherits) rather than assuming it.
- **Shape:** S1 = cost stream only (bp-011's 0.47× pair is the first datum; estimate/actual as a
  JOIN across two commits, not a row); safety = passive stratum + domain-excludes-codomain (φ_self
  cannot observe its own output — the regress has no fixed point) + inherited firewall verbatim;
  calibration shared with core as PATTERN never machinery (non-negotiables #2/#3). Five parked
  decisions, three open questions (a₂ cross-map deferred to the axis gate); V3 (cost-block
  inventory) can run read-only before ratification.
- Brainstorm annotated with the promotion pointer; no owner question opened.

**Next:** Fable-first step 3 — the bp-016 (fable builder) ∥ bp-017 (sonnet builder) lane under
opus/default supervision; delegation prompts carry the delegate skill's five-part gate verbatim.

## 2026-07-12 — owner design dialogue: edge dynamics & the continuum; queue re-prioritized

Same-day extension of the self-sensing session — a five-exchange owner dialogue, all captured.

- **Owner rulings landed in `dn-self-sensing` (draft):** edge/chain history is
  **ledger-class, reset-guarded** (V2's escalation candidate resolved — reset semantics split
  by re-derivability); the erasure test written into §2.4 (erasure-invariance = the operational
  smart-vs-wise line); PD-f parks utility-graded durability.
- **New consolidated brainstorm `docs/brainstorms/edge-dynamics-and-continuum.md`** (owner:
  "capture it all, in spirit and rigor") — the physics dictionary verified against
  `core/complex/` (three owner instincts hit built machinery: Fourier → spectral.py's graph
  Fourier basis; threads → topology.py persistent H₁; **Ricci → curvature.py Forman–Ricci**),
  the two-discretenesses terminology, the continuum ladder (splines/GP → Lomb–Scargle →
  Hodge-Fourier → DMD → learned action / Ricci-flow candidates), and the inversion rule (the
  discrete record is exact reality; every continuous fit is a versioned interpretation).
- **V3 probe RAN (read-only):** cost frontmatter parses deterministically; 4 complete pairs
  (bp-011 0.47×, bp-012 0.52×, bp-014 0.29×, bp-015 0.26× — systematic overestimate, no retune
  at n=4); bp-013's actual never backfilled (small annotation task); bp-000..010 pre-rule.
- **Queue re-prioritized (owner directive, §7 of the new brainstorm):** P0 owner ratifies
  dn-self-sensing (critical path) · P1 draft `dn-edge-dynamics` (two-lane: mirror-side 1-form
  lift = data today; observed-side weaving = data accumulates) · P2 bp-016∥bp-017 in parallel ·
  P3 graduate self-sensing substrate · P4 graduate Lane A · P5 data-gated continuum rungs.

**Next session (Fable/xhigh while it lives):** spawn bp-016(fable)+bp-017(sonnet) builders
first (background), draft `dn-edge-dynamics` while they run, scrutinize + merge at tail.

## 2026-07-12 — P0..P3 in one pass: ratification recorded, edge-dynamics drafted, self-sensing graduated; builders in flight

Fable/xhigh combined design+supervision session, executing the §7 queue in order.

- **P0 recorded (`8deab2a`):** the owner hand-ratified `dn-self-sensing`; committed verbatim.
  The ratifying save ran an editor markdown formatter that mangled three spans (§3.3 B-a/B-b
  falsifier emphasis, the Cross-references paragraph); A8 correctly denied agent repair
  post-flip, so the exact hand-fix is filed as **oq-0016** (non-blocking). Owner then
  **permanently removed the formatter** — future saves are safe; repair still owed.
- **P1 done (`d04378d`): `docs/design-notes/edge-dynamics.md` (`dn-edge-dynamics`, draft)** —
  the two-lane split as the central decision (Lane A mirror-side 1-form lift as dreamer
  lenses, data exists today; Lane B observed-side weaving consumer, gated on substrate +
  sample depth + a Track-D charter); the degree-1 lift pinned to buildable precision (flag
  complex forced by Rips consistency, oriented ∂₁/∂₂, L₁, Hodge decomposition, THREAD lens
  under the interpreter-panel contract, dim ker L₁ == ripser-β₁ as the built-in falsifier);
  the inversion as a standing invariant with the R1–R4 rung ladder. Ratification owner-by-hand.
- **P3 done (`5f0d92b`): /graduate `dn-self-sensing` → bp-018 (B-a, fable/250k), bp-019
  (B-b, sonnet/350k), bp-020 (B-c, sonnet/100k), all `proposed`**, serial chain. Graduation
  pinned: version identity = declared semver + source-hash ratchet test; reset mechanism =
  family-shared guarded history sidecar (`observation_history.sqlite` into `_RESET_GUARD`),
  archive-then-replace; φ_self grain = first-parent diff of plan cost blocks; bp-013's
  partial actuals (54,048 opus tokens, Items-6-7 session unrecorded) annotated at bp-020
  Item 9. `proposed → ready` is the owner's hand.
- **P2 in flight:** bp-016 (fable builder) ∥ bp-017 (sonnet builder) spawned first, in
  background worktrees, prompts carrying the five-part gate verbatim + finding-ID ranges
  (0039+/0045+). CI green on `931d977` confirmed pre-spawn (run 29205100281). Scrutiny,
  sequential merges, live CI/pages proof, and seals with measured usage are this session's
  tail (or the next session's head if context runs out first).

**Next:** merge + seal bp-016/bp-017 (bp-016 §4 owes the attestation-layer.md cross-ref at
seal; bp-017 owes the live pages proof); owner acts pending: ratify `dn-edge-dynamics`,
bless bp-018..020 `proposed → ready`, hand-repair oq-0016. Then P4 (/graduate Lane A after
ratification) and the deferred riders (second /triage, /scribe offer at six ratified notes).

## 2026-07-12 — session tail: owner gates flew, bp-017 sealed, Lane A graduated, bp-016 builder lost to the spend limit

- **Owner acts, all same-day:** ratified `dn-edge-dynamics` (`13e26bc`); flipped bp-018
  `ready`; hand-repaired the oq-0016 mangled spans (`3a873c2`) and permanently removed the
  markdown formatter. Both blessing gates exercised twice today, both by hand, both clean.
- **bp-017 SEALED (`d05e860`).** First live pages run failed — `uvx` absent on hosted
  runners; the setup-uv step was in the plan's own §6(b) comment and both builder and
  orchestrator diff-review missed it; the live-proof-at-seal discipline caught it
  (orchestrator fix `1528ffd`). Then: green run, site + `/api/core/` serve (783 rendered
  content matches), the two live-axis test timeouts re-ran green uncontended,
  finding-0045 (public/ gitignore) resolved. Usage sonnet 97,449 tok / 90 calls / 22 min
  — **0.97×, the ledger's first near-1× pair** (V3's set grows to five).
- **bp-016 builder DIED on the monthly Claude spend limit** ~91 tool calls in, before its
  gate run or report. Work preserved: orchestrator safety commit `60bd857` on
  `worktree-agent-a9ab532a788bd1549` (witness re-point, release relocation shape,
  release.yml, runbook §CI witness, finding-0039 — UNREVIEWED). Recovery is
  resume-in-worktree per the delegate skill; deploy stays blocked until the witness
  attests. **The spend-limit raise is the owner's console act and gates all builder work.**
- **P4 (`89058b6`): /graduate `dn-edge-dynamics` Lane A → bp-021** (`core/complex/hodge.py`
  — oriented flag complex, ∂₁/∂₂ with the ∂₁∂₂=0 sign catcher, L₁, Hodge decomposition,
  deterministic harmonic basis, ripser cross-check harness) **+ bp-022** (THREAD lens via
  the interpreter-panel contract, honest-seam order pinned; `dim ker L₁` + harmonic
  persistence into the temporal snapshot series with additive DuckDB heal). Both
  `proposed`; 022 depends 021.

**Next:** owner raises the spend limit → recover/scrutinize/merge/seal bp-016 → bless
bp-019..022 → spawn bp-018 (B-a, `ready`, the substrate the worldview chains ride).
Session shape: one Fable/xhigh orchestrator (design+supervision combined) + one sonnet
builder sealed 0.97× + one fable builder lost mid-flight to the limit.

## 2026-07-12 — bp-016 SEALED after spend-limit recovery: the witness attested its own merge

- **Recovery per the delegate/context-economy skills (resume-beats-restart, proven again):**
  fresh Fable/xhigh orchestrator session resumed the dead builder's worktree from plan +
  journal + safety snapshot `60bd857`. Scrutiny of the full unreviewed diff against plan §6
  line-by-line: PASS (CLI surface byte-identical; only `success` green; emission shape exact;
  grace loop in `check()` only; no secrets; launcher untouched; 11 files all in scope).
  Snapshot restructured into the planned logical commits (`f5bb116` witness+suite+shim,
  `2205057` docs, `6a4de1c` release trio + release.yml), `main` merged in clean.
- **Gate (worktree, post-merge):** ruff · mypy-scoped · argless mypy **= 69 = baseline** ·
  type_gate · pytest 850 passed, 1 environmental live-axis flake (async-unload race in
  `test_scheduler_live`'s own clean-slate step; failed 2× ~132 s then re-ran green in both
  checkouts; probes isolated the mechanism) → **finding-0046** (codebase, tests/e2e outside
  bp-016 scope). bp-017 precedent applied.
- **Merged `cd289bb`, pushed, LIVE-PROVEN:** ci run **29211747966 GREEN** for the merge sha
  and **the new witness itself attested it** (`scripts/ci_witness.py check` rc 0,
  authenticated, emission `ci_witness / pipeline_green / run:29211747966`) — live CI proof,
  Item 9's falsifier replay, and the **deploy-gate unblock in one command**. Deploy's
  attestation gate now reads GitHub; first release.yml dispatch stays owner-initiated
  (none fired; Item 10 acceptance was dry-run only).
- **Seal acts:** plan `complete` + cost actual (builder tokens unknown — died before
  reporting; recovery not separately metered); §4's attestation-layer.md cross-ref applied
  (draft note, §3 gains the ci_witness type, D3, `pipeline:→run:`); worktree removed.
  Findings owed to /triage: 0039 (falsifier-demo side-effect audit + owner PAT-rotation
  notice), 0046 (flaky live test).
- **Spawn prep:** bp-018 ∥ bp-021 write_scopes verified disjoint (only `docs/findings/**`
  shared — new files, ID ranges 018→0047+, 021→0052+); mutual `parallelizable_with`
  asserted in both front-matters (graduation-author's amendment at spawn, per brief).

**Next:** spawn bp-018 (fable) ∥ bp-021 (sonnet) builders; merge-as-they-land; then
bp-019 (after 018), bp-022 (after 021), bp-020 last (Item 11 backfill is the
orchestrator's at seal). Riders: second /triage (0039, 0046, resolved 0045, oq-0016
sweep), /scribe offer (book debt: seven ratified notes).

## 2026-07-12 — /triage (second sweep): 0039 routed → oq-0017, oq-0016 swept, journals sealed

- **Routed:** finding-0039 (discovery, bp-016) `open → routed`; its process question (side-effect
  audit before falsifier-demo runs) + the owner PAT-rotation notice batched as **oq-0017**
  (non-blocking; interim mitigation already in every delegation prompt). finding-0046 (codebase,
  flaky live e2e test) noted and LEFT for a builder whose scope covers `tests/e2e/` — stays open.
- **Sealed:** bp-016 + bp-017 journals get their /triage seal lines (both plans `complete` with
  PROGRESS checkpoints already in place). No other plan flipped since the last sweep.
- **Swept:** oq-0016 `→ swept` (owner hand-repaired `3a873c2` + permanently removed the
  formatter; self-contained). Board: oq-0003..0010 still open (design-tier, non-blocking,
  unchanged), oq-0017 new.
- **Promotions:** none this sweep (0039's amendment rides oq-0017; the routed 0009–0030 backlog
  stays design-tier-deferred). **Book debt: SEVEN ratified notes, book unscaffolded — /scribe
  offer stands** (owner keystroke away; first scribe plan would be minted `proposed`).

## 2026-07-12 — bp-021 SEALED: hodge.py lands — the degree-1 instruments exist, cross-checked exact

- **Built (sonnet builder, worktree, ~35 min wall):** `core/complex/hodge.py` (218 lines) —
  oriented flag complex (`edge_index`/`flag_triangles`), boundary operators `∂₁`/`∂₂`
  (∂₁∂₂ = 0 exact on 5 fixtures), `L₁ = ∂₁ᵀ∂₁ + ∂₂∂₂ᵀ` (PSD), the three-way Hodge
  decomposition (orthogonal < 1e-8, reconstruction exact, idempotent), deterministic dense-SVD
  harmonic basis, `l1_spectrum`, 20k-edge dense-path guard (ValueError, never a silent solver
  switch). 42 tests incl. the reusable §6(f) ripser harness. Zero findings — every §6 pin
  matched the codebase.
- **Verified:** builder gate green (892/0) + orchestrator full gate re-run post-main-merge
  green (**893 passed / 8 skipped / 0 failed**, argless 69); scrutiny PASS incl. analytic
  ∂₂-sign re-derivation and a hand-check of the 5-fixture β₁ table; **live cross-check:
  dim ker L₁ == ripser alive-H₁ on the real corpus (0 == 0 at σ=0.62)** and exact across 3 σ
  values hermetic. finding-0046's flake did NOT trip either run. Merged `cb953a9`, pushed.
- **Usage (the ledger's sixth pair):** sonnet, **173,956 tokens / 233 tool calls / ~21 min =
  0.58×** of the 300k estimate.
- **Next:** bp-022 (THREAD lens + temporal invariants) unblocked — spawning now, parallel to
  the still-running bp-018 (scopes disjoint: dreaming/temporal/config vs stores/sensor).

## 2026-07-12 — DEPLOY live-proves the GitHub gate · v1.4.0 CUT · bp-018 SEALED

- **DEPLOY (owner-fired):** run #12 → **run #13 pinned `9e2c5c5`**, graceful cycle clean; the
  deploy gate's witness leg ran as a real subprocess against GitHub Actions and attested green
  before promotion — the re-pointed attestation pipeline is proven in its actual consumer.
- **First release dispatch failed → fixed → v1.4.0 CUT.** release-on-deploy dispatched
  release.yml (owner-initiated by construction); run 29213279927 failed at semantic-release:
  node 20 pinned per the engines floor, but semantic-release 25 needs ≥22.14 (local dry-runs
  passed on node 26 — the bp-017 setup-uv class again; live-proof caught it). Orchestrator fix
  `c82b53e` (node 24), CI green, owner re-fired → **v1.4.0 tagged, CHANGELOG commit-back
  `01726dd` by semantic-release-bot**. **Q9 CONFIRMED live: zero ci runs on the commit-back**
  (GITHUB_TOKEN loop guard) — bp-016's last carried question closes.
- **bp-018 SEALED (merge `160fd2f`, redone atop the release commit):** all four items;
  scrutiny PASS (launcher grant exactly one guard entry; §6(d,e) migrations idempotent in both
  crash windows; archive-before-replace ordering can duplicate an archive attempt but never
  lose a generation; finding-0047's is_projected deviation ACCEPTED — honest semantics,
  test-guarded). Gate: argless 69; pytest 908 passed, 3 live-e2e contention flakes ALL re-ran
  green truly uncontended (2 passed / 126 s with zero other suites machine-wide). Live-copy
  migration preserved 259,813 rows; the LIVE store (now 288,091 rows) migrates at this seal
  commit's hook. Findings: 0047 (spec-defect, resolved — Q3 missed one test caller),
  0048 (second live-flake class member). **Usage (seventh pair): fable, 194,279 tok / 104
  calls / ~44 min = 0.78×.**
- **Flake-class tally for /triage:** three catalogued members in one day (0046 scheduler
  unload-race, 0048 dream_v2 embed death, research_live today) + perfect correlation with
  concurrent live suites → candidate: a cross-suite live-axis lock or serialized runner,
  one small scoped plan. Also riding: launcher.py:259 stale "talks to gitlab.com" comment;
  the gate command's step-3-exits-1 structural wrinkle (fold into attestable_green.sh, 0038).
- **Next:** bp-019 spawn (B-b, sonnet/350k — deps clear); bp-022 scrutiny when its builder
  reports (final gate re-run in flight); bp-020 last.

## 2026-07-12 — bp-019 SEALED: the third sensing stream — φ_self reads the agent's own cost ledger

- **Built (sonnet builder + one scrutiny-addendum resume):** `AgentObservationStore`
  (OBSERVED-only, interpreter-versioned from birth, family-sidecar supersession),
  `AgentSensingHandoff` (the seam's third sibling, appended to core/sensing.py — 0 deletions
  outside the block), `ops/self_sensor.py` (φ_self v1.0.0: deterministic git-subprocess-only
  reads, first-parent candidate walk + diff, §6(f) payload normalization incl. the warnings
  path), driver script, ONE hook line, ONE reset_targets entry. 47 new tests.
- **Scrutiny:** PASS after one catch — the §6(f) unparseable-non-null WARNING path was
  unimplemented; sent back via SendMessage, builder closed it (deterministic per-(path,key)
  warnings, 2 pinning tests, ratchet honestly re-pinned as a declared refactor). Findings
  0057 (IDENTITY_KEYS 'agent' entry — needs a one-line grant, OWNER ASK PENDING) and 0058
  (plan's pinned git commands lacked --first-parent/--root; fixed, empirically verified)
  both spec-fidelity, builder-resolved. One-line grants audited exact (hook + launcher).
- **Verified:** builder full gate 954/0 on a tree identical to merge result (spawn base ==
  main, zero drift); addendum re-verified fast legs + 41 targeted tests; argless 69 held
  throughout. Merged `b1040a4` atop v1.4.0. Combined-tree full gate runs once after bp-022
  lands (disjoint scopes; each branch fully gated on its own tree).
- **Usage (the ledger's eighth pair): sonnet, 236,576 tok / 210 calls / ~34 min = 0.68×**
  (incl. the scrutiny-addendum resume — the first measured resume-a-builder cycle).
- **Next:** bp-022 gate finishing → merge + final combined gate + seal; then bp-020 (last).

## 2026-07-12 — bp-022 SEALED: the threads are narratable — Lane A COMPLETE; wave closed with a combined-tree gate

- **Built (sonnet builder; died at the usage limit mid-gate with all items complete —
  orchestrator recovery per the bp-016 precedent):** the `THREAD` lens joins
  `STRUCTURAL_INTERPRETERS` (harmonic H₁ flow over bp-021's Hodge decomposition; honest seam
  FIRST — β₁=0 short-circuits before hole pairing; support ⊆ witness by construction;
  gap-family, never contradiction — pinned by test); `StructuralSnapshot` gains the two
  degree-1 exact invariants (`dim_ker_l1`, `harmonic_persistence_total`) additive/
  degrade-to-None with a DuckDB on-open heal; `structural_axes()` byte-identical (the consumed
  drift contract — pinned by test); config purely additive (`thread_min_persistence`).
- **Verified:** worktree gate green (926/0, argless 69, zero flakes uncontended); scrutiny
  PASS (no findings); merged `723fb33`; **combined-tree gate on main (018+019+021+022
  together): 970 passed + the 0046 flake re-run green isolated (117 s), argless 69** —
  the wave's last full suite. Witness-attested: bp-019 `b1040a4` run 29220719660 GREEN,
  bp-022 `723fb33` run 29220917823 GREEN. (Witness lesson: short shas silently match
  nothing on the head_sha query — burned one grace window; hardening on the triage agenda.)
- **finding-0057 CLOSED by owner grant:** the `IDENTITY_KEYS["agent"]` one-liner applied
  under the oq-0013 capability-grant precedent (`6b4daa6`) — the latent KeyError on a future
  φ_self bump is gone.
- **Usage (the ledger's ninth pair): sonnet, 210,223 tok / 155 calls / ~36 min = 0.84×.**
- **The board:** bp-016..bp-019, bp-021, bp-022 ALL COMPLETE — six seals in one day, two
  builder deaths recovered with zero work lost, v1.4.0 cut, deploy live-proven. Lane A
  (edge-dynamics) is DONE: instruments (021) + lens + temporal record (022). Self-sensing
  is two-thirds done: substrate (018) + third stream (019); **bp-020 (B-c: forecast checks
  + backfill verification report) is the queue's last plan.**
- **Next:** bp-020 (sonnet/100k), then the third /triage (agenda: live-flake lock, 0051
  hook hardening, witness short-sha guard, launcher stale comment, && -chain gate text,
  0047/0048/0057/0058 sweeps), then /scribe offer (book debt: seven ratified notes).

## 2026-07-12 — THIRD /triage: three proposed plans minted, wave-debt swept, four journals sealed

- **Ran concurrently with the bp-020 build** (opus orchestrator, default effort; the
  tier-justifying judgment was pre-ruled at the wave boundary in the closing fable session
  and executed here — no re-litigation). Board verified clean at entry: main `36906fb`,
  root `active-plan` empty, live φ_self store healthy (26 agent_observations / 59
  projections — growing per-commit from the bp-019-seal baseline of 25/57).
- **Promotions → three `proposed` plans minted (owner flips `proposed → ready`):**
  - **bp-023** (sonnet/80k) — serialize the live test axis ACROSS processes via an
    endpoint-keyed stdlib `fcntl.flock` autouse fixture. Resolves the live-flake CLASS:
    finding-0046 + finding-0048 (folded) + bp-018's research_live/semantic_search_live
    cross-suite evidence. `filelock` rejected (not installed; POSIX `fcntl` needs no dep).
  - **bp-024** (sonnet/60k) — finding-0051 fix 2: a `(d)` check in `cmd_stop_audit` that
    BLOCKS a worktree Stop when MAIN's `active-plan` names that worktree's own plan (the
    exact bleed signature; zero-false-positive predicate). Spec pinned verbatim in §6.
  - **bp-025** (sonnet/50k) — wave-debt micro-sweep, three independent items: witness
    short-sha guard (`_full_sha` expand-or-error before polling, ci_witness.py:110/165);
    launcher.py:265 `gitlab.com`→`api.github.com` comment; delegate SKILL.md gate text
    separated (the `&&`-chain short-circuits at leg 3, argless mypy exits 1 at baseline 69).
    `scripts/attestable_green.sh` (0038 rec 3) stays deferred.
- **Findings:** 0046 → carried into bp-023 (flips `→ promoted` on blessing); 0048 → folded
  into 0046 + bp-023; 0051 → fix 2 carried into bp-024 (flips `routed → promoted` on
  blessing); 0058 frontmatter reconciled (`open → resolved`, matched its recorded
  resolution); 0047 + 0057 already `resolved` (no action). No promotions beyond 1–3;
  oq-0003..0010 stay design-tier-deferred.
- **Sealed** the bp-018/019/021/022 journals (seal markers appended; durable seals already
  in PROGRESS above). **Owner questions:** 8 open (oq-0003..0010), none answered — nothing
  to sweep.
- **Next:** merge/seal bp-020 (the queue's last plan) on its builder's completion; /scribe
  offer; owner blesses bp-023/024/025 at leisure (none blocking; queue self-drains through
  bp-020).

## 2026-07-13 — bp-020 SEALED: the backfill's first live verification — self-sensing family COMPLETE, ORIGINAL QUEUE DRAINED

- **Built (sonnet builder, worktree; branch merged `42e4206`):** Item 9 — bp-013's late
  seal-fill. At the builder's HEAD bp-013's `actual` was NOT null (plan §4's premise): it
  had been seal-filled at `ef9319e` with non-conforming field names (`tokens_item8: 54k`,
  not `tokens: 54048`) that the φ_self parser silently under-parsed (no `tokens` key → not
  join-eligible). Item 9 corrected the ENCODING to the §6(a) pin — same recorded facts, no
  invented numbers. Item 10 — dry-run inventory (`:memory:` store, real repo): 11 complete
  estimate/actual pairs, 0 parse warnings, deterministic across two runs.
- **Verified (orchestrator, main checkout, Item 11 live):** merged from the main checkout
  (disjoint scope, conflict-free); ran `uv run scripts/sense_self.py`; **bp-013 is now a
  complete pair in the live store** (est 250000 / act 54048); 30 agent_observations / 62
  projections; **second run idempotent (0 rows)**; 0 warnings throughout. φ_self correctly
  keeps BOTH bp-013 `actual` observations (the mis-encoded one at `ef9319e`, the corrected
  one at `6d6bc24`) as the honest temporal record — "an edited fact is a new observation at
  its landing commit" (the design, live). Gate: ruff clean · argless mypy **69** · type_gate
  OK · pytest unchanged-by-construction (docs/frontmatter only; builder ran 970/0 green,
  live flake re-ran green isolated per the flake rule).
- **finding-0059 (spec-fidelity, builder-resolved):** V3's "11 pre-rule / zero-cost-block"
  baseline (dn-self-sensing §3.2, carried into bp-019 §3 Q4 + bp-020 §3 Q1) is STALE — only
  8 of bp-000..010 are truly cost-block-free; bp-006/007/009 carry backfilled `actual`-only
  blocks (added by `ea3d8e8`, the commit that introduced the ledger convention). Sensor was
  correct; the carried count was wrong. Correcting the ratified note's + sealed bp-019's
  phrasing is design-tier (A8-immutable) — deferred to an owner touchpoint, non-blocking.
- **Usage (the ledger's TENTH pair): sonnet, 149,834 tok / 106 calls / ~22 min = 1.50×** of
  the 100k estimate (over — the builder's grounding surfaced the mis-encoding + stale
  baseline, honest extra reads; recorded for calibration).
- **The board:** bp-000..bp-022 ALL COMPLETE. **The original graduation queue is drained.**
  Self-sensing (dn-self-sensing) is DONE: substrate (018) + third stream (019) + backfill
  (020); φ_self projects every main commit live. Three NEW `ready` plans await the owner's
  build green-light: bp-023 (live-test lock), bp-024 (finding-0051 hook fix), bp-025
  (wave-debt micro-sweep) — the third-triage promotions.
- **Next:** /scribe offer (book debt: SEVEN ratified notes, book unscaffolded); then a
  session to build bp-023/024/025 (sonnet builders, disjoint scopes — parallelizable); the
  cost-forecast report generator is now the self-sensing frontier (real substrate: the live
  agent_observations store). Deploy promotes bp-020 + the triage to the live daemon (owner,
  any time).

## 2026-07-13 — dn-core-query-protocol DRAFTED + bp-026 SEALED: the reference stratum goes symmetric, doc→doc live

- **Design session (opus, fable-guard relaxed):** a deep chat arc (agents as scoped clients of
  a core-query algebra; three retrieval modes; the deterministic single-stratum reference
  agent; the eval loop; the edge math) was captured to `docs/brainstorms/core-query-protocol.md`
  (four threads + two opus math sketches + a **fable rigorous pass** — `claude-fable-5`,
  tier-verified: the β-deformation/Maslov, the kernel-cone Mercer inversion, the bicomplex⟺
  functoriality reduction, ledger-as-Sz.-Nagy-dilation). Graduated to **draft
  `dn-core-query-protocol`** with an honest §1.3 opus/fable seam map (what's fable-grounded vs
  what a fable pass must finalize). Findings 0060/0061 (workflow smoothing) + 0062 (the
  reference-gap direction) filed en route.
- **bp-026 built + SEALED (sonnet builder, worktree `bb43bee`):** `reference_edges` generalized
  to a **symmetric v2 schema** (`source_*/target_*`, derived direction, `corpus_to_corpus`
  first-class) + a φ_doc **doc→doc extractor** (front-matter `design_ref`/`links`/… + inline
  note-citations + wikilinks). Isolation invariant (B-c) held bit-identically; grep-oracle exact
  on sampled notes/findings.
- **Scrutiny catch:** the builder **over-bumped `INTERPRETER_VERSION`** (φ_doc adds unversioned
  reference edges; it stamps only code observations → re-pin, not bump). Sent back via
  SendMessage → reverted to 1.0.0, sha re-pinned `9bd50a2a…` at seal (finding-0064). Clean
  provenance; resume-beats-restart.
- **Item 21 live migration (orchestrator, OWNER-COORDINATED daemon-down window):** the running
  v1 daemon **shares `data/`** and holds v1 code in memory → the migration is **deploy-coupled**
  (finding-0066). Owner `bootout`'d the daemon (KeepAlive means `palace stop` won't hold it);
  I wiped `reference_edges` + `code_observations` (φ_self untouched) and reprojected to v2:
  **183,458 edges (45,527 corpus→corpus / 137,931 code↔corpus), == dry-run exactly, 0 warnings,
  idempotent**; owner `bootstrap`'d it back on v2. Full gate green (984 passed, argless 69).
- **Findings:** 0063 (v1-compat properties, resolved), 0064 (the over-bump, resolved at seal),
  **0065** (corpus→corpus scan excludes build-plans — §6c said docs/**; a corpus-scope ruling
  for triage — the doc→doc capability is complete for authored notes, not build-plans yet),
  **0066** (migration deploy-coupling + the missing KeepAlive-aware `palace down/up` command),
  **0067** (daemon ownership / privilege model — service-user vs user-agent; owner's capture).
- **Usage (ledger's ELEVENTH pair): sonnet, 280,146 tok / 291 calls / ~88 min = 1.56×** of 180k
  (includes the over-bump scrutiny-catch resume — honest cost of catching it before main).
- **Next:** the corpus-scope ruling (0065) + possible re-migration; the `palace down/up` command
  (0066) + daemon-privilege design note (0067); bp-023/024/025 still `ready` (unbuilt); /scribe
  offer; dn-core-query-protocol wants a fable-vetting pass before ratification.

## 2026-07-13 — bp-023 + bp-024 + bp-025 SEALED: the third-triage wave lands (3 parallel sonnet builders)

- **First fully-parallel delegated wave:** bp-023 (live-test cross-process lock), bp-024 (Stop-gate
  `(d)` cross-checkout bleed check, finding-0051 fix 2), bp-025 (wave-debt micro-sweep: witness
  short-sha guard + launcher comment + delegate gate-text) built CONCURRENTLY as dedicated
  `builder`-type **sonnet** agents in three isolated worktrees. Disjoint code scopes; shared
  `docs/findings/**` de-conflicted by pre-assigned finding-ID ranges. All three tier-verified
  `claude-sonnet-5` (no downgrades). Pre-flight budget gate held: 34% all-models weekly headroom
  covered the ~305k padded wave.
- **Merged sequentially `--no-ff` at the wave boundary**, zero conflicts (scopes truly disjoint).
  Combined green gate on the merged tree: ruff · targeted mypy · **argless mypy == 69**
  (finding-0038 class clear) · type_gate · CI-equivalent `pytest -m "not live …"` **977 passed,
  0 failed**. (Full `pytest -q`: 1 live failure — `test_scheduler_live` — the finding-0069
  environmental class, which CI never runs.) main now at the merge tip; pushed.
- **bp-024 scrutinized hardest (enforcement blast-radius):** the `(d)` check is read-only,
  fail-open, byte-identical off-worktree, appends without touching checks (a)–(c); its falsifier
  stands up a REAL git worktree with 3 controls (empty / different-plan / not-a-worktree), each
  hitting a distinct code path. `_normalize_plan_ref` correctly normalizes without `rel()`-binding
  a foreign path. No finding needed.
- **finding-0069 (bp-023, `discovery` → orchestrator → oq-0018):** Item 12's lock is PROVEN
  correct (server-log cross-ref: one cold-load in the race window ⇒ endpoint windows disjoint),
  but Item 13's literal "both pass" flaked under a WIDER axis — whole-machine RAM pressure from the
  SIBLING builder worktrees (this session's own parallel-builder decision starved the shared
  Ollama daemon). A single write_scope can't install a machine-global lock. Item 13 closed via
  §6(b)'s alternate disjoint-window acceptance; the cross-worktree policy call (machine-global lock
  vs scheduler policy vs accept re-run fallback) is oq-0018, default (c). **Lesson for the
  delegated-parallel-builders mode: parallel builders contend on physical RAM, not just the
  endpoint — the live tier is the pinch point.**
- **Ledger — the TWELFTH/THIRTEENTH/FOURTEENTH pairs (all sonnet):** bp-024 64,929 tok / 63 calls
  / ~22 min = **1.08×** of 60k; bp-025 60,630 / 56 / ~27 min = **1.21×** of 50k; bp-023 124,620 /
  140 / ~35 min = **1.56×** of 80k (Item 13's contention forensics drove the overage). Wave total
  ~250k measured vs 190k estimate = 1.32× aggregate; the 1.6× pad held with margin.
- **Design capture (owner chat, mid-wave):** `docs/brainstorms/external-grounding.md` — two
  threads: (1) SymPy/CAS math-verification ("proves the MACHINERY we choose, not the THEORY" —
  owner) as a deterministic, sandbox-native, fable-relieving checker; (2) the CURATED strata as
  trusted external LITERATURE — a second K₀ bedrock on a provenance axis distinct from the mirror
  (author=subjective, curated=objective; Popper World 2/3, Polanyi personal knowledge), forcing a
  depth-≠-authority split in the finding-0068 gradient. Routes into the dn-core-query-protocol
  fable-vet (adds a 5th kind: `reference`/`literature`).
- **Next:** the three `ready` plans are drained. Remaining queue: fable-vet dn-core-query-protocol
  (+ the external-grounding literature kind) — GATED to Jul 17 (fable exhausted); finding-0066
  `palace down/up` command; /scribe (book still unscaffolded); the 0065 corpus-scope ruling. An
  optional redeploy aligns the daemon (`344f02c`) with main HEAD; not required.

## 2026-07-13 — EXTERNAL-GROUNDING arc: curated literature layer designed; research airlock reframed; a design note QUEUED

A long owner↔orchestrator design session (post-wave, no build) developed the **external-grounding**
arc end-to-end and grounded it against existing code. All in `docs/brainstorms/external-grounding.md`
(9 capsules, 2026-07-13). Durable summary (the resume brief holds the actionable task; this is the
portable backstop):
- **The arc.** Ouroboros as a LIVE SELF-INDEX to cut context cost (the origin motivation) → two
  grounding threads: SymPy verifies the *machinery we choose, not the theory* (a deterministic,
  sandbox-native, fable-relieving checker), and a CURATED external-literature stratum (a 2nd K₀,
  objective, provenance-distinct from the mirror; **depth ≠ authority**). Citations are free edges;
  transitive expansion makes it a graph (γ^d-damped); **ratification is the promotion gate**; the
  curated layer is cross-strata connective tissue closing an objective **warrant circuit** (authored
  intuition → dialogue → curated → code).
- **FABLE-verified formalism (tier-checked `claude-fable-5`):** the γ^d weight generalizes to
  **`w(d,a,c) = γ^{(d+μc)/a}`** — authority as a decay-RATE not a toll; naive product form is
  degenerate. Banked verbatim; routes to the Jul-17 vet.
- **`docs/reference_material/` STOOD UP** (owner design): subdir-per-reference + `manifest.md` (v0
  schema, README) + distillations; first resident `moore-aronszajn-1950/` LIVE. **Two-plane model:**
  git holds manifest+distillation (portable); the FULL SOURCE is ingested LOCALLY (embedded in
  `data/`, never git, never egress) — the pattern-finding substrate. States: asserted→verified→
  DISTILLED→EMBEDDED.
- **Literature check (§1.3 item 6 of dn-core-query-protocol) — ✅ DONE, no fable** (sonnet+web, 7
  CONFIRMED/2 PARTIAL/0 REFUTED). Caught + fixed a substantive misattribution: **Mercer →
  Moore–Aronszajn (1950)** in §2.2 (corrected inline). First DOGFOOD of verify-before-trust.
- **REFRAME — build-item-b already exists.** The Phase-8 §16 **research airlock** is a complete,
  tested, DORMANT external-research subsystem (`core/research/{criteria,airlock,rank}.py` de-id
  boundary + `cloud/fetcher/{sources,aggregate,handler}.py` OpenAlex/EuropePMC/arXiv + `librarian.
  research_criteria`). The `edge/` fetch boundary (Inv 2) is already built; sources span medical AND
  math/CS. The "fresh perspective" is ONE inverted decision: **flip transient→EMBEDDED** (embed into
  the SEPARATE curated store, keeping "never pollutes the mirror"). Common missing piece: **the live
  driver** (foreground Ambassador + background scheduler). Reviving the owner's medical-research
  feature and the design-grounding pipeline is one build.
- **Fable episode (banked in the delegate skill):** the owner bought extra-usage credits to run the
  dn-core-query-protocol fable-vet; **fable did NOT route** — 2 `model: fable` spawns both silently
  downgraded to opus (UI indicator caught it; the agent self-declaration LIED). Fable is a WEEKLY
  time-throttle, not a spendable balance — no real fable until **Jul 17**. Tier-check discipline
  corrected: trust the UI indicator + completion `<usage>`, never the agent's self-report.
- **QUEUED (owner-requested, NO FABLE):** draft the design note **`dn-external-grounding`** that
  graduates this arc (curated stratum + transient→EMBEDDED flip + two-plane model + ratification gate
  + live driver + EMBED-tail with the copyright/licence gate + invariant reconciliation + the seam to
  dn-core-query-protocol). Opus is enough; the `reference`-KIND tagging + `w(d,a,c)` are the only
  fable-gated bits (deferred to the Jul-17 vet). Full drafting spec + all context pointers are in the
  resume brief's THEN-QUEUE item 1.
- main == origin == **`49bf5f9`** at this checkpoint; all pushed; CI attesting. Session was a whale
  (build wave + this whole arc) — CLEAR recommended.

### 2026-07-13 (cont.) — external-grounding: DRAFTED → RATIFIED → GRADUATED; index-query PARKED

- **`dn-external-grounding` DRAFTED (opus, no fable) → owner-RATIFIED (hand-edit) → committed
  blessing** (`docs/design-notes/external-grounding.md`; commits `a568f34` draft, `a2c5625` ratify).
  Decides all 8: curated stratum as 2nd objective K₀; two-plane store + asserted→verified→DISTILLED→
  EMBEDDED; ratification-as-promotion-gate; the §16 airlock transient→EMBEDDED flip; the live driver;
  the EMBED tail + copyright gate; Inv 1/2/4/7/11; math-verification (Thread 1) as a plan-§8 companion.
  Taxonomy/kind/`w(d,a,c)` DEFERRED to the Jul-17 dn-core-query-protocol fable-vet (Item 0). Answers
  finding-0062.
- **Index-query slice SCOPED + PARKED → finding-0070.** The read-only surface the owner wants ALREADY
  EXISTS as read methods (`core/stores/reference_edges.py::{all,for_commit,count}`, zero-model); the
  store is payload-free by schema; the only gap is an agent-facing façade (currently code-anchored +
  agent-unreachable). Full dn-core-query-protocol NOT required for the conservative read; the SOLE
  blocker is the §2.4 boundary ruling (build-time plane → core store — the first such precedent).
  Owner ruled: **park to the Jul-17 fable-vet** (rigorous over a fast graduate under external-grounding
  §3.1). finding-0070 also clarifies (owner Q): the façade IS the algebra's Mode-1 client, not parallel
  work — fable delivers design, not running code, so a build follows either way.
- **`/graduate dn-external-grounding` → bp-027/028/029 (proposed)** (`d6196cf`): bp-027 seed fill (9
  verified refs, docs-only, §3/§4/§8 N/A, ∥ bp-028); bp-028 the live driver (grounded §3/§4; opus/300k;
  transient; §16 banner); bp-029 the EMBED tail (grounded §3/§4; opus/450k; open-access full text →
  curated store; licence gate default-DENY parked; depends_on bp-028). Index-query EXCLUDED (→ vet);
  math gate deferred. Items 22–30. `proposed→ready` stays owner-by-hand.
- main == origin == **`d6196cf`**; all pushed; CI attesting. Clean CLEAR boundary.

### 2026-07-13 (cont.) — bp-027 SEALED: the reference_material seed layer lands (first delegated build of the arc)

- **bp-027 COMPLETE** (`003a7d9`, FF-merged to main): the nine web-verified citations from the
  literature pass now have schema-valid `docs/reference_material/<slug>/{manifest.md,distillation.md}`
  cards — the curated (objective) stratum's seed set is now **VERIFIED + DISTILLED** (not yet EMBEDDED;
  every card `not_fetched`, `store_ref: null`, `provenance: agent-proposed`). Moore–Aronszajn stays the
  resident exemplar (untouched). 18 new files + journal, 590 insertions.
- **First delegated build off the external-grounding arc** — ran as a supervised **sonnet builder in a
  worktree** (the economically-correct tier: docs authoring, crisp checker). Pre-flight budget gate
  passed (week 70%, session 18% at spawn; fable 100%-capped, untouched — sonnet requested, no downgrade
  risk). Shook out the /build→review→merge flow cleanly.
- **Supervision verdict:** scope clean (only `docs/reference_material/**` + the bp-027 journal; README +
  moore-aronszajn untouched); five-leg green gate all-green with argless mypy == **69** (docs-only, no
  code moved); acceptance script confirmed all v0 keys + states + verdicts (8 CONFIRMED / 1 PARTIAL).
  All nine distillations verified faithful to `dn-core-query-protocol §2.2/§2.5` line-by-line. One
  minor non-blocking gloss in the Quillen card (names the obstruction's `d` "the ledger-compression
  operator"; §2.5's `d` is the cochain differential — reference-facing claim is correct). No findings
  filed by the builder; none warranted on review.
- **Seal / economics:** sonnet, **88,998 tokens** (0.89× the 100k estimate — UNDER, first estimate/actual
  pair of this arc), 86 tool calls, ~18 min. One env wrinkle (worktree venv needed `uv sync --extra dev`;
  no PyYAML in the project so the builder used a scratchpad nested-YAML reader for the acceptance check —
  both benign, off the write_scope).
- **Queue now:** bp-028 (the live driver — opus-class, invariant-adjacent Inv 2/7) and bp-029 (EMBED
  tail, depends_on bp-028) remain `ready`. Do NOT run concurrently (finding-0069 live-tier RAM). bp-028
  is a scrutinized `/build` session, not a cheap delegation.

### 2026-07-13 (cont.) — bp-028 SEALED: the live research driver — the dormant airlock now RUNS

- **bp-028 COMPLETE** (`97d98ca` code; sealed this commit): the airlock chain
  `research_criteria → emit → collect → rank → surface` is wired and running, transient (no mirror
  pollution — persistence is bp-029). Items 23 (driver `scheduler/research.py`), 24 (trough handler
  + `enqueue_research` in `scheduler/cron.py`), 25 (foreground TASK→airlock in `scheduler/interface.py`
  + `is_research_request` in `agents/ambassador/policy.py`), 26 (BUILD-SPEC §16 banner). **Production
  activation** in `ops/lifecycle/launcher.py`: `RESEARCH_KIND` registered in the supervisor handler
  map + the delegate wired with the `research_criteria` de-identify seam — the daemon runs it.
- **Invariant-adjacent, held**: Inv 2 (core never touches the network — only the airlock `requests/`
  file), Inv 11 (only de-identified criteria cross; PII-query test proves "March/2019" never reach the
  outbound blob), never-pollute-the-mirror (an `ExplodingStore` test guarantees zero store writes).
  Robustness: an undeidentifiable research query FAILS CLOSED (nothing emitted) → falls back to the
  general path, never crashes (§11 warrant).
- **Ran SELF-DRIVEN** (opus/high, no subagent fan-out) — the invariant-adjacent tier the resume brief
  mandated, and the budget-lean path. **Effort started at LOW by mistake**; owner caught it mid-session,
  switched to high + demanded a re-review (no correctness defects found; the re-review surfaced the
  real gate shape — `ruff format` is NOT a leg — and the async emit/collect round-trip point).
- **Plan defect caught + resolved (finding-0071)**: bp-028's `write_scope` omitted ALL §7 test paths
  (graduation oversight — every sibling code plan lists them) → the acceptance tests couldn't be
  authored. Surfaced to owner (did NOT self-widen an invariant-adjacent plan's capability). Owner
  hand-added the three test paths + `launcher.py`; reconciled the mangled YAML (quoted paths so the
  oq-0013 parser strips the inline comments). finding-0071 → **resolved** (both halves in-plan).
- **Gate — all five legs green**: ruff `All checks passed`; import-firewall (Inv 2) `OK`; model-free
  pytest **991 passed, 4 skipped**; mypy Tier-2 hard floor **0** (174 files); argless mypy pinned **69**
  (new-test fakes `cast`, baseline intact); semgrep **0** (report-only). Vault-axis 3-skipped (no local
  vault; untouched). **Live tier NOT run** — every bp-028 test is deterministic with injected fakes; the
  live model path isn't newly exercised (finding-0069/oq-0018 default (c) stands).
- **Seal / economics:** opus, **161k non-cache tokens** (21.3k in + 139.7k out; 24.8M cache-read),
  **$19.74**, **0.54× the 300k estimate — UNDER**. New calibration datum: a self-driven CODE build lands
  UNDER the ~1.6× delegated code-pad (the pad is calibrated on builders that reload context). Session
  22%→33% (+11pp); **week 71%→72% (+1pp — cache-dominated, cheap on the weekly quota)**. Fable 100% capped.
- **main == origin == (this seal)**; all pushed; CI attesting. Clean unit boundary.
- **Queue now:** bp-029 (EMBED tail, `ready`, **depends_on bp-028** — now satisfiable) is the next build,
  but do NOT run concurrently with anything live-tier (finding-0069). Lighter independent picks: /triage
  (flip finding-0062 promoted; route the backlog + 0071), finding-0066 → `palace down/up`, /scribe.

### 2026-07-13 (cont.) — bp-029 SEALED: the EMBED tail — transient becomes persisted (curated store lands)

- **bp-029 COMPLETE** (sealed this commit): the external-grounding arc's last near-term plan. The
  ranked-then-DISCARDED literature pipeline now **persists keepers** into a SEPARATE curated
  vectorstore. Items 27 (open-access full-text fetch, Zone C), 28 (the curated store), 29 (the
  licence-gated persist/embed), 30 (the manifest DISTILLED→EMBEDDED mechanism + dangling-claim guard).
- **What shipped:** `cloud/fetcher/sources.py` fetches Europe PMC OA full text (`fullTextXML`, stdlib
  JATS parse, gated on `isOpenAccess=="Y"`), fails closed; `Paper` gains `open_access`/`full_text`.
  `core/stores/curated_store.py::open_curated_store` opens `data/research_curated.lance` (gitignored,
  a SECOND store, base `VectorStore` untouched). `core/research/persist.py` chunks→embeds keepers with
  `provenance="curated"` under the default-DENY licence gate. `core/research/curate.py` flips a manifest
  to EMBEDDED (surgical, comment-preserving) + guards the dangling claim (embedded ⟹ real store_ref
  backed by real vectors).
- **Invariant-adjacent, held STRUCTURALLY:** Inv 2 (persist reads already-fetched text — core never
  fetches), never-pollute-the-mirror (separate store + `CURATED ∉ MIRROR_READABLE` — the enum class
  already existed), Inv 11 (full text under `data/`, `git check-ignore` confirms), the licence gate
  (`open_access AND full_text`, belt-and-suspenders; verified by the Item-27 falsifier test — a non-OA
  record never triggers a full-text fetch).
- **Offline-build boundary (by design):** real seed cards stay `not_fetched` — flipping one needs real
  vectors → a real fetch → Zone-C/curation-time (Inv 2 forbids a core fetch). The build delivers the
  TESTED mechanism; real flips ride a live driver run (bp-028) + `mark_manifest_embedded` (gated by
  `ingestion_errors` so a dangling claim can never land). All ≥10 real seed manifests validated against
  the v0 schema + confirmed unflipped.
- **Ran SELF-DRIVEN** (opus/high — effort set at the TOP this time, the bp-028 lesson applied). One
  owner touchpoint: the write_scope test-path gap (finding-0072, = finding-0071 class) — surfaced, NOT
  self-widened; owner authorized in-session, orchestrator added the 4 `tests/integration/*` paths.
- **Findings:** 0072 (write_scope gap — RESOLVED; /graduate check still owed), 0073 (arXiv PDF full-text
  deferred — codebase, not a blocker; Europe PMC is the working OA tail), 0074 (Item-30 real flips are
  live-time — spec-fidelity, RESOLVED: mechanism delivered).
- **Gate — all five legs green (run separately):** ruff `All checks passed`; import-firewall (Inv 2)
  `OK`; model-free pytest **1010 passed, 4 skipped** (+20 new bp-029 tests); mypy Tier-2 hard floor **0**
  (177 files); argless mypy pinned **69** (one new bare-`dict` fixed to hold the pin); type_gate OK;
  semgrep report-only. Vault axis untouched (no local vault). **Live tier NOT run** (deterministic fakes;
  finding-0069/oq-0018 default (c) stands).
- **Seal / economics:** opus, **120k non-cache tokens** (14.7k in + 105.7k out; 16.8M cache-read),
  **$13.82**, **0.27× the 450k estimate — UNDER, even leaner than bp-028's 0.54×** (fakes, no live tier,
  tight edits, item-boundary checkpointing). Session 34%→42% (+8pp); **week 72%→73% (+1pp —
  cache-dominated, cheap on the weekly quota)**. Fable 100% capped. (The 24h "85% subagent-heavy /
  80% >150k-context" advisory is the aggregate, NOT this session — this build is the lean self-driven
  counterexample.)
- **main == origin == (this seal)**; pushed; CI attesting. Clean unit boundary.
- **The external-grounding near-term arc is now COMPLETE**: bp-027 (seed layer) + bp-028 (live driver) +
  bp-029 (EMBED tail) all sealed. What remains is design-tier (the Jul-17 fable-vet: the `reference` kind,
  `w(d,a,c)`, the index-query façade) + a live deploy to activate the airlock (owner-only).
- **Queue now:** finding-0066 → `palace down/up` (small sonnet plan, budget-friendly); /triage (flip
  finding-0062 promoted; sweep 0071/0072/0074-resolved + 0073; route the backlog); /scribe (book debt,
  unscaffolded). The Jul-17 fable-vet is gated (Fable capped until then).

## 2026-07-14 — FABLE finalization: the temporal/edge frontier closed → THREE design notes drafted; bp-030 blessed+parked

- **Session shape:** owner blessed bp-030 `proposed→ready` (committed `81ab7aa`), /build started; recon
  found a write_scope gap (finding-0075) → **bp-030 PARKED** (`9abb4b4`); owner then pivoted the session
  to a **Fable pass on the edge-dynamics/temporal frontier** (the whole deferred backlog). Orchestrator
  on opus/xhigh for cross-check + composition.
- **The Fable spawn (owner-driven tier):** background `general-purpose` worker, `model: fable`. Initial
  spawn FELL BACK to opus (Fable weekly-capped — the delegate-skill prediction held); **owner manually
  switched it opus→fable and it drew on usage credits** — tier confirmed on the UI signal + the
  173k-token/19-tool `<usage>` profile. Clean single pass (~16 min). One harness oddity: switching the
  worker's model also flipped the orch session to Fable (owner reset it to Opus 4.8).
- **The warrant** — `docs/brainstorms/edge-dynamics-lane-b-fable-pass.md` (committed `b404a5b`).
  Cross-checked EXTENSIVELY (owner ask): every grounded claim spot-checked green — `hodge.py` builds on
  the *similarity* backbone (A4); **bp-026 genuinely `complete`** (the doc→doc extractor landed → the
  empirical program is unblocked, a stale premise both the note AND the prior fable capsule carried);
  `change_point` deferred seam at `interpreters.py:64,269` (Ruling B's keystone); `doc_id=source_path`
  rename-instability real (`sync.py:77` + `supersession-lifecycle §7`); `reference_edges` schema has no
  payload column + the `:61–63` vault-digest reservation (the §2.4 correction's basis). **Authentic
  fable-depth** — it *corrects* opus, doesn't restate it.
- **THREE design notes composed** (single-writer, from the warrant; all `draft`, owner ratifies):
  1. **`dn-temporal-retrieval-algebra`** (NEW) — the math successor: normalization triple pinned
     (`c=−log w` walk vs `1−sim` Rips scale; z-bound IS the γ-ceiling); `σ_*`/`π_active` operators
     (π_active is the ambient default, a correction); the five §2.5 results theorem-grade (bicomplex⟺F1∧F2;
     `[d,τ]` on severed citations; Quillen superconnection; ledger=Sz.-Nagy dilation; γ-contraction);
     the separate `X_cite` complex (home OUTSIDE `core/complex/` — isolation grep); Hodge on E_geom⊔E_disp
     (two Helmholtz sides, don't mix); **the A7 signal-vs-noise discriminator** (load-bearing apophenia
     guard); **β\* now a theorem** (finite iff `d_∞` not negative-type; RSP kernel stays PSD).
  2. **`dn-core-query-protocol`** (UPDATED draft) — folded in C1 (§2.4 **corrected to
     capability-dissolution** — a local repo-derived twin, not a sealed-store read), C2 (scope-grammar
     **bounded lattice**; join=monotone-delegation IS non-negotiable #6), C3 (operators re-ranked), C4
     (§4.5 **RULED: promotion re-anchors depth**), C5 (**three notes**), Ruling B (§2.7 the **diachronic
     interpreter** = a distinct interpreter, not a second dreamer mode). §1.3 marked FINALIZED.
  3. **`dn-weaving-consumer-charter`** (NEW) — Track D's Lane-B charter (gated, not licensed): reads
     `ObservedView`/`X_cite`, emits INTERPRETED-only, four entry gates (§2.6's three + **the A7 gate**),
     R1-first. `dn-edge-dynamics` (ratified) untouched — the algebra enters as a NEW note cross-linked as
     its Lane B math home.
- **OWNER DECISIONS pending (surfaced in-note, not baked):** (1) C1 residual — repo-derivable graph
  queryable by build context? (rec yes); (2) C4 re-anchor depth `d₀` — shallowest-derived (rec) vs K₀-0;
  (3) A6 **rename-stable identity is a hard prerequisite** for the diachronic reader (currently at risk);
  (4) magnetic-Laplacian timing; (5) evolution-study axes at ratification. **Next step is the owner
  ratifying the three drafts** (draft→ratified is owner-by-hand) after ruling these.
- **No code touched** — three markdown design notes + this checkpoint. No test gate applies to design
  notes; A8 respected (edited a draft, authored two drafts, ratified `edge-dynamics` untouched, no
  blessing flip). **bp-030 still in-progress/parked** (Items 1&3 resume anytime; Item 2 waits on the
  finding-0075 write_scope grant).
- **Owner RULED the 5 decisions in-session (2026-07-14), folded into the drafts:** (1) C1 — **YES**,
  the repo-derivable citation graph may be queried by a build/worktree context; (2) C4 — re-anchor to
  **shallowest-derived** (keeps the derived/authored firewall); (3) A6 — **rename-stable (uuid) identity
  is a HARD prerequisite, prioritized BEFORE the diachronic reader graduates** (a NEW upstream item;
  `doc_id=source_path` forks lineage on rename, at risk today); (4) magnetic-Laplacian — **defer** (TA-a);
  (5) evolution study — **YES**, adopt the phase-space (q,p) + epistemology axes. Consequence: Result 6
  (γ-contraction) is now an UNCONDITIONAL theorem. **The 3 drafts are ratification-ready; draft→ratified
  stays owner-by-hand.** Pushed `8f63758` (notes) + this rulings increment.
- **Owner RATIFIED all three by hand** (`6108dd8`, draft→ratified; orchestrator committed the blessing per
  finding-0060). **Graduation unblocked** (opus/xhigh, uuid-identity plan first per the A6 ruling).

## 2026-07-14 (cont.) — MAGNETIC LAPLACIAN: 2nd fable pass; the exciting conjecture REFUTED, a disciplined small result earned

- **Owner elevated the magnetic Laplacian** (`L^{(q)}`, the directed-diffusion upgrade named in ratified
  `dn-temporal-retrieval-algebra` §2.1 ii / TA-a) from decision-#4 DEFER → develop, as "the natural
  progression of the 'direction' physics." Framing brainstorm `docs/brainstorms/magnetic-laplacian.md`
  (`19e4955`) → a 2nd fable pass (tier owner-confirmed: UI Fable-5 switch + `<usage>` 152k tok; fable
  $10.93 cum). Warrant capsule `docs/brainstorms/magnetic-laplacian-fable-pass.md`.
- **Cross-checked green** (code citations verified): `curvature.py:30` binarizes support (`B=(A!=0)`) →
  Forman **flux-blind** (Q5); `laplacian.py:48–56` signed `L̄` balanced-iff-singular **IS** the `q=1/2`
  ℤ/2 fiber of the magnetic family (the house already built one fiber). Q2 refutation = rigorous
  double-dissociation.
- **The disciplined outcome (the pass HELD THE LINE — did not overhype):**
  - **Q2 REFUTED** — magnetic flux ≠ the `[d,τ]` diamond holonomy; it is exactly its **abelianization**
    (`Φ_q = χ_q∘w`); the TA-c defect lives in `ker(character)`. **TA-c is NOT closed, provably not by any
    abelian/spectral object** (support mismatch; balanced diamonds flux≡0/defect≠0; coherent shortcuts
    defect=0/flux≠0). The exciting conjecture dies cleanly.
  - **Q1** magnetic Hodge: operator always; Hodge theory only if 2-cell-flat — **parity-obstructed on the
    citation flag complex**, vacuous on the triangle-free Hasse DAG. Flux is a literal curvature 2-form.
  - **Q3** flux on the DAG = `2πq × arm-length imbalance`; balanced diamonds → zero flux; content = the
    **gradedness defect** (revision-effort asymmetry). Reconciled with A5.
  - **Q4** two charges (forced by A5); **retro-citations** = the measurable influence/time misalignment.
  - **Q5** flux⟷Ricci **FALSE** (gauge vs metric curvature; the real "directed Ricci" = the deferred
    Ollivier PD-c).
  - **Q6/Q7** operator earns **math not build**; a **combinatorial diagnostic census v1** earns its place
    (SCC/directed-cycle, unbalanced-diamond, retro-citation — exact, gauge-free, **no operator needed**),
    folding into the already-licensed Thread-C sweep; **DEFER the operator** behind 3 re-entry gates.
    Falsifiers F1–F5 ready-made (F4 = the magnetic `dim ker L₁ == ripser`).
- **NOT composed yet** (deferred to a FRESH session — context-economy; this session is
  9h/$37/78%-week/>150k-context, harness advising /clear): a NEW draft note from the capsule + folding
  the census into Thread-C. **3 OWNER DECISIONS:** (1) adopt the defer-operator ruling (rec yes); (2)
  census dream-narration vocabulary (taste, §5); (3) covering-only `supersedes` as a checked A6-invariant
  (rec adopt, near-zero cost).

## 2026-07-14 (cont.) — GRADUATED `dn-temporal-retrieval-algebra` → three `proposed` plans (opus/xhigh, fresh session)

- **Unit chosen by the owner** (from the resume-brief queue): `/graduate` the math successor — NOT fable
  (depth already paid; graduation is decomposition + blast-ordering + write_scope/test-path discipline).
  Budget re-checked live at session start: **week 78%, Fable 100% capped (both units were opus anyway),
  credits 81%.** Single-lane, minimal-subagent (0 spawned), ends at the graduation boundary.
- **Grounded pass (investigate → reconcile → plan; citations in each plan §3):** read `sync.py`,
  `catalog.py`, `versions.py`, `logseq.py`, `reference_edges.py`, `hodge.py`, `topology.py`,
  `test_reference_edge_isolation.py`, `supersession-lifecycle.md §7`. Two de-risking discoveries carried
  the decomposition: (1) `versions` is **already** `doc_id`-keyed (`versions.py:54`) → the uuid work needs
  NO version-schema change, only the value `sync.py:112` passes; (2) `logseq` **already** parses `id::`
  into `parsed.properties` → reading an existing page id is zero-new-code, zero-vault-mutation.
- **Three plans minted (`proposed`, blast-ordered, chained):**
  - **bp-031 — rename-stable `doc_id`** (the A6 HARD prerequisite; `depends_on: []`, the FIRST plan). Item
    1 is additive + **behavior-preserving** (`doc_id := source_path` backfill keeps ~20 `source_path`-keyed
    tests green); Items 2–3 (mechanism + rename carry-forward) **owner-gated → oq-0019**. write_scope names
    all 3 test paths (finding-0075) + the stop-and-raise for any OTHER reddened test.
  - **bp-032 — `core/temporal/` topological core** (`depends_on: bp-031`): `X_cite` assembly from
    `ReferenceEdgeStore`, `∂`/`δ_D` (+`δ_D²=0`), the `dim ker L₁ == ripser β₁` falsifier (reuses
    `hodge`/`topology` — the SAFE import direction), a new isolation twin. **Resolves TA-d: home pinned to
    `core/temporal/`.**
  - **bp-033 — `core/temporal/` transport operators** (`depends_on: bp-032`): `π_active`, `σ_*`/`σ^*`,
    `‖[d,τ]‖` (= the exact severed-citation count, Result 2). Linear-chain only; diamonds stop-and-raise
    (TA-c). Split from bp-032 because the objective carried an "and" + each half has an independent
    falsifier.
- **oq-0019 filed** — bp-031's identity mechanism (owner ruling; default (A): existing-`id::` +
  exact-content rename detection, NO mint-into-vault). Non-blocking (bp-031 Item 1 proceeds regardless).
- **Deferred downstream** (gated on the module landing, NOT graduated this session): the empirical
  **Thread-C sweep + arrow-aware census** (note §3 Consequence 2 — folds in the magnetic-Laplacian census)
  and the **`K(β)` retrieval curve** (Consequence 3, TA-b). Also NOT graduated: `dn-core-query-protocol`
  §3 consequences (its own note/session) and the `dn-weaving-consumer-charter` (GATED, its 4 gates aren't
  green).
- **Numbering note:** the resume-brief loosely earmarked "bp-031" for the diagnostic subcommand;
  graduation claimed the next three numbers (031–033), so **the diagnostic is now bp-034** (author when
  bp-030 lands its enriched `status` seam). No code touched; CI unaffected (docs-only).
- **Next:** owner blesses `proposed → ready` (item-by-item) + rules oq-0019 → then `/build bp-031`
  (FIRST). Or resume bp-030 (Items 1 & 3 unblocked). All on disk; fresh session.

## 2026-07-14 (cont.) — COMPOSED the magnetic-Laplacian DRAFT note (opus/xhigh; operator deferred, census + formalization finalized)

- **Owner corrected the resume-brief mis-file** (mine): composing the magnetic-Laplacian draft note from
  its captured capsule is an **opus/xhigh ORCHESTRATOR task, NOT fable-gated** — the fable pass is DONE
  (the capsule, `1e3591e`); only *developing the operator* would need fable, and that's deferred anyway.
  Composed in-session (context warm at 20%, not fresh) at the owner's direction.
- **New draft:** `docs/design-notes/magnetic-laplacian.md` (`dn-magnetic-laplacian`, `status: draft`) —
  companion to the ratified `dn-temporal-retrieval-algebra`/`dn-edge-dynamics` (cited, never edited).
  States Q1–Q7: Q1 conditional magnetic Hodge + the parity obstruction on `X_cite` (vacuous on the
  triangle-free Hasse DAG) + flux as a literal curvature 2-form; **Q2 REFUTED** (flux = the abelianization
  `χ_q∘w` of the `[d,τ]` diamond holonomy; **TA-c NOT closed, provably not by any abelian/spectral
  object**); Q3 the gradedness defect (`Φ_q = 2πq·arm-imbalance`; balanced diamonds → 0); Q4 two charges +
  retro-citations; Q5 flux ≠ Ricci (the 5-row curvature ledger; Forman provably flux-blind); the F1–F5
  falsifier inventory (F4 = the magnetic `dim ker L₁ == ripser` analog). House grounding: signed `L̄`
  (`laplacian.py:48–56`) = the `q=1/2` fiber the codebase already trusts.
- **The DECISION recorded (§3):** the operator BUILD is **deferred behind 3 named gates** (ML-a) with its
  build constraints pinned now (Hasse-DAG-only, two charges, `q=1/4`, gauge-invariant outputs, F1–F5); the
  **arrow-aware census folds into the ALREADY-LICENSED Thread-C sweep — no new build license** (adds
  arm-imbalance / retro-citation count / `X_cite` SCC-cycle count to §3 item 2's "diamond frequency"); the
  ledger + inventory are prophylactic vocabulary.
- **Owner decisions:** **#1 RULED in-session** (defer the operator, finalize the census/formalization —
  the owner's direction). **#2** (dream-narration vocab for the census) and **#3** (covering-only
  `supersedes` as a checked A6-invariant, rec adopt) stay OPEN — ruled at draft → ratified (owner-by-hand).
- No code touched; CI docs-only. Book debt now +4 notes (the 3 temporal + this draft). Next: owner
  ratifies this draft (+ rules #2/#3); the build queue (bp-031 first) is unchanged.

## 2026-07-14 (cont.) — OWNER BLESSINGS: bp-031/032/033 → `ready`; `dn-magnetic-laplacian` → `ratified` (all by hand)

- Owner hand-flipped, in-session: **bp-031, bp-032, bp-033 `proposed → ready`** (the whole temporal chain)
  AND **`dn-magnetic-laplacian` `draft → ratified`**. Orchestrator commits the flips (rule 0060).
- **oq-0019 remains OPEN** → building bp-031 gets **Item 1 only** (the additive `doc_id := source_path`
  foundation); **Items 2–3 park on default (A)** (existing-`id::` + exact-content rename detection, NO
  mint-into-vault) until the owner rules it. Ruling oq-0019 (default A stands) lets bp-031 complete FULLY
  in one build session.
- **Build order is STRICT (dependency-chained):** bp-031 → bp-032 → bp-033 (bp-032's D-arrows need
  bp-031's rename-stable `doc_id`; bp-033 consumes bp-032's module API). Do NOT build out of order.
- **The ratified magnetic-Laplacian note carries two STILL-OPEN owner decisions** (the owner ratified the
  formalization + the #1 defer-ruling; the note is now immutable per A8): **#2** census dream-narration
  vocab (taste — extends `dn-edge-dynamics` §5) and **#3** covering-only `supersedes` as a checked
  A6-invariant (rec adopt, near-zero cost). Route onward (not lost in the frozen note).
- No code touched; docs/blessing-flip commit only.

## 2026-07-14 (cont.) — oq-0019 RULED (B: mint `id::`) + authored bp-034 (the id-mint migration, extreme rigor)

- **Owner sided with (B)** on oq-0019 — mint a durable `id::` as the rename-stable identity (exact in
  ALL cases incl. rename+edit, where A/C fork; idiomatic to Logseq; the "front-matter uuid"
  `supersession-lifecycle.md:290` named first). Answer DRAFTED into oq-0019 at owner direction (status
  left `open` for the owner's confirm-flip). **bp-031 is unchanged** — it's the superset-compatible
  foundation; the mint is a separate follow-on.
- **The owner's sharp question resolved:** "won't ingest see the re-minted note as an update, preserving
  lineage?" — **half right.** The in-place mint IS detected as an amendment (`sync.py:89-113`), but
  `versions` is append-only and keyed by `doc_id`, so the amendment `record()`s under the NEW resolved id
  → `current(new_id)`=None → **seq 1 → fork** (`versions.py:88-94`). The digest change alone does NOT
  carry lineage across the identity switch → an **explicit version/catalog re-key** (`doc_id: source_path
  → minted id`) is the mandatory, load-bearing step.
- **Authored `bp-034` — the id-mint migration** (`proposed`, `depends_on: bp-031`, warrant = oq-0019),
  extreme rigor per owner request. Grounded findings that made it precise: the re-key surface is TINY —
  ONLY `versions.doc_id` + catalog `doc_id` (the vector store self-heals, keyed by `(source_path,
  chunk_hash)`; raw + `authored_supersession` are digest-keyed → no re-key). Shape mirrors
  `purge.py`/`scripts/purge_raw.py`: **build the tool, don't run it** — owner-gated (`confirm=True`),
  offline (daemon DOWN, deploy-coupled finding-0066), dry-runnable, idempotent (skip notes with existing
  `id::`/YAML `id:` — so repo design-notes/findings are untouched), reversible (vault + store backups),
  byte-preserving `id::` insertion. **Highest-blast plan to date** (first corpus write + first
  append-only relabel) → opus/high. Items 13–16.
- **Invariant touchpoint surfaced (owner rules at blessing):** `versions` is structurally append-only
  ("no update/delete"); the re-key is a **relabel** (preserves `(seq, digest, at)`), precedented by
  `catalog.relabel_provenance`, gated by the `authored_supersession` `OwnerDeclaration` capability — but
  invariant-adjacent, so bp-034 §11/§10 park it for the owner's ruling at `proposed → ready`.
- **Renumbering:** bp-034 = the mint migration; the diagnostic subcommand shifts to **bp-035**.
- No code touched (docs-only). Next: build bp-031 (foundation) → then, when the owner is ready, bless +
  run bp-034 (the deliberate, offline mint). bp-032/033 (temporal module) proceed in parallel to the
  identity work once bp-031 lands.

## 2026-07-14 (cont.) — bp-031 SEALED: rename-stable `doc_id` — the A6 hard prerequisite LANDS (`f002985`)

- **All 3 items built + sealed in one orchestrator-driven session (opus/high, 0 subagents).** A file
  rename no longer forks version-history lineage — proven by `tests/integration/test_rename_identity.py`
  (4 proofs: pure-rename continuous chain, `id::` identity, rename+edit fallback, ambiguous-dedup guard).
- **oq-0019 ruling B implemented as RESOLUTION only** (read existing `id::` at first bind + exact-content
  carry-forward on rescan) — the superset-compatible base. Item 2 guards on `prev is None`, so a
  historied note's identity is never switched → **no live-fork window**; the mint + append-only re-key is
  **bp-034** (owner-run, daemon down).
- **Behavior-preservation held:** additive `doc_id` (== source_path until a mechanism diverges it) →
  FULL suite **1033 passed, 8 skipped** (+7 new); the falsifier (any other test reddening) never fired.
- **Live-store migration DE-RISKED:** dry-run twice against a COPY of the live `data/vault_catalog.sqlite`
  (5 rows → 5, all `doc_id == source_path`, idempotent). **Deploy-coupled** (finding-0066): the migration
  runs when the daemon next opens the catalog on this code → optional owner `mind-palace deploy` align.
- **5-leg gate green** (ruff / mypy 0 / mypy 69 / type_gate / pytest — run separately). Cost: est 300k →
  **91k non-cache, $9.19, ratio 0.30** (self-driven band); session +21pp (14→35%), week +2pp (78→80%).
- **⭐ UNBLOCKS bp-032** (the `core/temporal/` module — δ_D/version chains need rename-stable `doc_id`).
  Owner directed: proceed to **bp-032 → bp-033** (strict dependency order). Building bp-032 next.

## 2026-07-14 (cont.) — bp-032 SEALED: `X_cite` citation complex + the `dim ker L₁ == β₁` falsifier (`07686fb`)

- **The topological half of the temporal algebra is BUILT** (dn-temporal-retrieval-algebra §3
  Consequence 1). New greenfield package `core/temporal/` — read-only sensing, structurally isolated
  from `core/complex/`'s balance math (the A4 constraint that forced it OUT of `core/complex/`).
- **Items 5–8** (opus/high, orchestrator-driven, same session as bp-031): `complex.py`
  (`build_citation_complex` → binary symmetric `A_cite`; `dim_ker_L1` reuses `hodge.harmonic_basis`;
  `citation_distance_matrix` = the ripser input), `boundary.py` (the supersession poset + simplicial
  `δ_D` with `δ_D²=0`; a cycle → `SupersessionCycleError`, stop-and-raise), and the isolation twin.
- **The load-bearing falsifier PASSES:** `dim ker L₁` (incidence algebra) == an INDEPENDENT ripser β₁
  on hand-verified fixtures (tree→0, chordless 4-cycle→1, filled-triangle→0). A5 honored: D-arrows
  (`E_disp`, directed) are NEVER symmetrized into `A_cite` (`E_geom`) — a mixed `L₁` is a type error.
- **5-leg gate green** (ruff / mypy 0 / mypy 69 / type_gate / pytest **1045 passed**). The lone
  full-suite failure was a **pre-existing timing flake** (`test_scheduler_live::test_supervisor_
  dispatches_a_real_job`) — **passed in isolation (126s)**, unrelated to a read-only math module.
  ⚠ flagged to owner as a flake to watch (finding-worthy if it recurs).
- Cost: est 400k → **~100k, ratio ~0.25** (read-only greenfield); dollars/deltas pending owner /usage.
- **⭐ UNBLOCKS bp-033** (the σ/π transport operators + `‖[d,τ]‖`, consuming this module's API).
  Building bp-033 next (strict order).

## 2026-07-14 (cont.) — bp-033 SEALED: the mode-3 operators + `‖[d,τ]‖` — THE TEMPORAL CHAIN IS CLOSED (`3379e7c`)

- **`dn-temporal-retrieval-algebra` §3 Consequence 1 is FULLY REALIZED** — the topological half (bp-032)
  + the transport half (bp-033). **bp-031 → bp-032 → bp-033 all sealed in one session** (strict order),
  the whole graduation of the ratified temporal note.
- **Items 9–12** (opus/high, orchestrator-driven): `operators.py` — `π_active` (idempotent contraction,
  NOT a chain map), `σ_*`/`σ^*` (chain map iff F1: `σ_* ∂ = ∂ σ_*` verified true under F1, false on a
  severed citation; `σ^*` a contraction), `T_active` composite (contraction); `superconnection.py` —
  `[d,τ]` with the note's Result-2 closed form (derived-verified), and **`‖[d,τ]‖` == the discrete
  severed-citation count exactly** ("not a proxy"); `[d,τ]=0` ⟺ flat/bicomplex. A merge diamond →
  `DiamondError` (§10/TA-c, linear chain only). bp-032's public API honored, not redesigned.
- **5-leg gate green** (ruff / mypy 0 / mypy 69 / type_gate / pytest **1055 passed** — a CLEAN full run;
  the bp-032-era scheduler e2e flake did not recur). Cost: est 400k → **~60k, ratio ~0.15**; dollars/deltas
  pending owner /usage (bp-032 seal read $19.02 session-total, 39%/80%).
- **⭐ DOWNSTREAM UNBLOCKED (design-tier, does NOT auto-graduate):** the empirical **Thread-C sweep +
  arrow-aware census** (note §3 Consequence 2 — folds in the magnetic census) and the **`K(β)` retrieval
  curve** (Consequence 3, TA-b) can now each graduate — separate design/graduate steps, not build work.
- **Session shape:** ONE orchestrator session did all three builds (bp-031 live-store migration + bp-032/033
  greenfield math), single-lane (0 subagents). A big unit boundary → resume brief rewritten, recommend CLEAR.

## 2026-07-14 (cont.) — bp-034 SEALED: the id-mint migration (durable id:: + version re-key) — the tool, owner runs the mint

- **oq-0019 (B) realized as a TOOL.** The highest-blast plan to date (first operation that would write
  the authored corpus + first append-only relabel) is built, green, and **not run** — mirrors
  `purge.py`: the owner runs the mint once, corpus-wide, **daemon DOWN**, after bp-031 deploys
  (deploy-coupled, finding-0066). Built against the binding **§11 journal determination**
  (ADMIT-WITH-GUARDRAILS, owner-confirmed) — not the bare plan.
- **Items 13–16** (opus/high, self-driven single-lane, 0 subagents):
  * **Item 14** — the owner-gated re-key primitive. `versions.migrate_rekey_doc_id` RELABELS a chain's
    `doc_id` (`source_path → minted id::`) preserving every `(version_seq, digest, at)` byte-for-byte —
    a relabel, never a history rewrite; the ONE admitted write to the append-only store. §3 CHECK ORDER
    verbatim (no-op cases BEFORE the merge refusal, so a partial run converges). Catalog twin +
    guardrail-5 uniqueness refusal (no unique index on `doc_id`). `verify_owner_declaration()` rider
    factors the one owner-capability check out of `authored_supersession` (no second token). §5 docstring
    amendment records the admitted path explicitly.
  * **Items 13/15/16** — `core/ingest/mint_ids.py`: `preview()` (pure read + §4a pre-state manifest),
    `mint()` (byte-preserving `id:: <uuid4>` prepend; refuses YAML front-matter §10; idempotent-skip),
    `run()` (daemon-down gate → backup → **per-note mint-then-rekey**, the §6 crash-convergence order →
    rescan → verify no fork; `restore_from_backup` reverses). `scripts/mint_ids.py` mirrors
    `scripts/purge_raw.py` (`--dry-run` default, `--confirm` runs it).
- **The load-bearing verification PASSES:** end-to-end — every note's history is ONE chain under its
  minted id, `history(source_path)` empty (no fork); a post-migration rename preserves lineage (A6);
  a second run is a no-op; without `--confirm` or with the daemon up it refuses. Plus the two the §11
  determination added: **§6 crash-convergence** (mint-without-rekey → re-run converges, no orphan/no
  fresh-uuid fork) and **§4b restore-rehearsal** (restore → byte-identical vault + version history).
- **5-leg gate green** (ruff / mypy 0 [184 files] / argless mypy **69** [baseline held] / type_gate /
  pytest **1078 passed, 8 skipped** — clean run, no flake). Suite 1055 → **1078** (+23).
- Cost: est opus/450k → **~200k est, ratio ~0.44** (self-driven single-lane); precise tokens +
  dollars/deltas pending owner /usage. Commits `a440dba` (Item 14) + `20b810f` (Items 13/15/16).
- **⭐ OWNER TOUCHPOINT (not auto):** the mint RUN — `uv run scripts/mint_ids.py --dry-run` then
  `--confirm`, **offline, daemon DOWN, after bp-031 is deployed**. Reversible from the auto-backup.
  Next build work (resume brief): `/resume bp-030` (Items 1&3; Item 2 owner-gated on finding-0075).

## 2026-07-14 (cont.) — bp-034 MINT RUN executed (owner-driven, live) — the corpus is on durable id::

- **The bp-034 migration RAN successfully on the real corpus** (owner-driven, orchestrator-guided; the
  deploy-coupled owner touchpoint). Deploy-coupled sequence per finding-0066: **deploy HEAD → bootout
  (true down) → dry-run → `--confirm` → bootstrap (up)**.
- **Deploy:** `palace deploy` promoted the live daemon `5a08cd4 → 4e1d885` (run #16 → #17; gate green
  1062 passed, ci-witness attested). bp-031→034 all went live at once.
- **Down:** `launchctl bootout gui/$UID/com.mind-palace.palace` (the `palace down` command is still
  bp-030 work; raw bootout for now — finding-0066). Verified: `launchctl print` exit 113, run #17 clean.
- **Migration:** `uv run scripts/mint_ids.py --confirm` →
  **`minted=13 rekeyed=13 verified=True rescan=(indexed=13 unchanged=0 tombstoned=0)`**. All 13 janus
  notes got a durable `id::` + their version chains re-keyed `source_path → id::`, no fork. Backup at
  `data/mint_ids_backup`.
- **Up:** `launchctl bootstrap … com.mind-palace.palace.plist` → run #18 on `4e1d885`, healthy.
  Post-migration `--dry-run` = **mint 0 / re-key 0 / skipped 13** (idempotent, it held).
- **The A6 well-foundedness conditions now hold on the REAL corpus** (`dn-temporal-retrieval-algebra`
  §2.4) — the operational prerequisite bp-034 existed to deliver. The daemon at HEAD (`4e1d885`) no longer
  lags; the deploy-lag half of finding-0066 is closed for this cycle.
- **finding-0076 filed** (`spec-defect`, non-blocking): `--dry-run` against a pre-bp-031 store runs
  bp-031's idempotent catalog `_migrate` on open — benign (named-INSERT v1 tolerates it), but the
  "dry-run mutates nothing" contract needs honest wording. Route: builder, batch at /triage.
- **Owner touchpoints now CLEAR:** the mint RUN ✅, the deploy ✅. Remaining: oq-0019 `open→answered`
  confirm-flip (the mint is now built AND run) at the next /triage.

## 2026-07-14 (cont.) — post-mint derived-layer cleanup (owner-directed, live data)

- **Integrity check after the bp-034 mint** (owner-requested, thorough) confirmed: 13/13 three-way
  identity (file id:: == catalog doc_id == version chain), 0 forks, 28/28 digests resolvable in raw,
  13/13 chains preserved byte-identical vs the backup, 9 live mirror edges / 2 theme clusters, 5 dreams
  all pointing to real notes, and a **live rename-stability proof on a copy of the migrated stores**
  (A6 holds: lineage follows a rename, no fork). No signed EdgeStore was ever touched — `edges.sqlite`
  never existed (empty by design; nothing asserts contradictions yet).
- **One real wrinkle found + fixed:** 3 older dreams' derivation-graph leaves referenced each note's
  PRE-MINT digest (the exact bytes they were generated from — accurate provenance, but a prior version).
  These would NOT self-heal (title-derived ids; their clusters are subsumed by the grown 6-note cluster,
  so they never re-emit). Applied a surgical remap (owner chose this over reset+re-dream): corrected only
  `derived_from` pre-mint→current digest (verified 1:1), re-synced the hypergraph via the store primitive,
  preserved summaries/subjects/data/created_at. Verified: 0 non-current leaves, 0 derived_from↔ℋ drift,
  5/5 dreams intact. Before-state captured (reversible). Live-data op; not a code change.

## 2026-07-14 (cont.) — MEASURED: the id:: mint changed the mirror graph (finding-0077)

- Owner demanded proof of consistency with pre-migration behavior. Empirical A/B (embed pre-mint backup
  bytes vs current bytes through the SAME pipeline + real qwen3-embedding:4b, one run): **σ=0.62 mirror
  edges 5 → 9 (+4, −0)**; per-note centroid drift cos min 0.891 / mean 0.953; max pairwise |Δcos| 0.169.
  Fresh post-embed reproduced the live store's 9 edges → the pre=5 counterfactual is trustworthy.
- **Honest verdict: NOT consistent with pre-migration behavior** — the shared `"id:: "` prefix uniformly
  lifts cosine (pushes 4 borderline pairs over σ) and the uuid adds content-free noise to short-note
  centroids. The clustering that drives dreams is denser by artifact, not by meaning. NOT a loss, NOT a
  corruption; a QUALITY regression on the semantic layer. This is why a "100% consistent" claim is false.
- **finding-0077 filed** (`direction` → orchestrator): this is bp-034 parked-decision-4's re-entry
  condition, now measured. Fix is additive (no rollback): strip id:: (and consider all `key::` page
  properties) from the DERIVED/embedded text in ingest, then re-embed from raw (§8, regenerable). Owner
  rules scope at graduation. Until then the live graph carries the +4-edge artifact; dreams stay valid.

## 2026-07-14 (cont.) — bp-036 SEALED: body-only embeddings + the dream re-embed EXPERIMENT harness

- **finding-0077 fix, built + green.** The bp-034 id:: mint fed identity metadata into the embedding,
  moving the σ-graph off note content (measured: 9 edges vs 4 body-only). bp-036 excludes ALL `key::`
  page-property lines from the embedded text — Path A (Logseq-native; id:: stays in the file, only the
  DERIVED text changes; no vault re-migration), owner-ruled scope = all props (extensible), deterministic.
- **Items 13–15** (opus/high, self-driven, offline-only in the build):
  * **Item 13** — `logseq.strip_properties()`: removes exactly the lines `_PROP` matches (the SAME object
    `parse_text` uses → parse≡strip by construction); body byte-preserved; column-0 only (§10 verified:
    0 indented block props in the corpus). 11 unit tests.
  * **Item 14** — `pipeline.derive_chunks` + `ingest_note` both chunk `strip_properties(...)`, the ONE
    shared derivation, so `verify.py` re-derives identical body chunks (no false integrity drop — the
    load-bearing constraint). Digest/`doc_id`/identity untouched (digest = sha256(raw bytes)). 4
    integration tests + the **real-embedder A/B: 9 → 4 edges, 5 removed, 0 added** (4 not 5 = `date::`
    also stripped, as predicted).
  * **Item 15** — `scripts/reembed_bodyonly.py`, the owner-run EXPERIMENT harness (scope expanded by owner
    mid-build): snapshot the pre-wipe dreams → re-embed body-only (`run_ingest(rebuild=True)`) → WIPE all
    dreams (reset-all) → trigger the dreamer on the clean graph → report. Gated (seal, daemon-down,
    confirm), reversible. 4 orchestration tests.
- **The load-bearing verifications PASS:** parse≡strip exactness; body byte-preservation; `verify.py`
  consistency (0 false drops); digest + `doc_id` invariance; the A/B reduces the artificial edges (§10
  stop-and-raise NOT triggered).
- **5-leg gate green** (ruff / mypy 0 [185] / argless mypy **69** [held] / type_gate / pytest **1097
  passed, 8 skipped**). Suite 1078 → 1097. Commits `1d731d8` (Items 13/14) + `16c4694` (Item 15).
- Cost: est 250k → **~300k est, ratio ~1.2** (owner-driven scope growth: snapshot + wipe + dreamer +
  experiment); precise dollars/deltas pending owner /usage.
- **⭐ OWNER TOUCHPOINTS (deploy-coupled, finding-0066):** (1) deploy bp-036; (2) run
  `uv run scripts/reembed_bodyonly.py --confirm` offline, daemon down → snapshots old dreams, re-embeds
  body-only, wipes + regenerates dreams. Then **I JUDGE old vs new** (better? uncovered? regressed?).
- Findings this arc: **0078** (scope-guard verbatim-matches write_scope; inline comments block writes —
  resolved by bare-path write_scope; recommend the hook strip comments).

## 2026-07-14 (cont.) — bp-036 EXPERIMENT run (owner) + JUDGED: body-only dreams are cleaner; σ needs re-tune

- **Owner ran the re-embed/re-dream experiment** (deploy `4e1d885→4500d42` run #19 → bootout → 
  `reembed_bodyonly.py --confirm` → snapshot 5 dreams, body-only vector_rows 23→21, **5 dreams → 1**).
- **Judged (orchestrator), the owner's 3-axis gauge — a clear WIN:**
  * **BETTER:** the old 5 were mostly redundant (dreams 1–4 = one recursion theme re-snapshotted 2→4→5→6
    notes as the id::-merged cluster grew). The new single dream is the true 4-note recursion core (cos
    0.64–0.72) — content-grounded, non-redundant.
  * **UNCOVERED:** a truer cluster boundary — `000928`/`130834` dropped out (best cos 0.615/0.602, i.e.
    0.005/0.018 BELOW σ): adjacent, not core.
  * **REGRESSED (honest):** the art cluster (`132225/132316/132412`) was lost — content cosines 0.46–0.57,
    all below σ (artifact-driven before; correct to drop), BUT only 0.05–0.09 below → genuine subtle theme.
- **The discovery → finding-0079:** σ=0.62 was implicitly calibrated on the id::-INFLATED graph; body-only
  dropped all cosines ~5%, so σ=0.62 is now too strict (near-misses above). Re-tune σ toward ~0.56–0.58
  ON the clean graph — but as a PROPER σ-sweep experiment (future work), not this one-off gauge. Owner-gated
  config tune; batched.
- **Two critical errors caught this arc** (owner's framing): (1) finding-0077 — id:: metadata polluting the
  semantic embeddings (would have made ALL future dream/theme results meaningless); (2) dreams clustered on
  that polluted graph (practically useless). Both fixed: bp-036 strips props from the embedded text; the
  experiment wiped + regenerated clean dreams. finding-0079 is the follow-on calibration.
- **Session close:** owner brings the daemon back up (`launchctl bootstrap …palace.plist`). Repo clean.

## 2026-07-15 — bp-037 (CQ-wire) COMPLETE: `TemporalView`, the algebra's first live consumer

- **Graduated + built + sealed in one session** (owner-directed sequence). `core/temporal` (X_cite,
  bp-032/033) was built but test-only; bp-037 wires its single-snapshot half into a live read surface.
- **Built:** `core/temporal_view.py` — `TemporalView` (frozen, commit-anchored; holds the assembled
  `CitationComplex`, no store handle) + `open_temporal_view` factory (anchor resolved identically to
  `ReferenceView`). Reads: `citation_threads()` (β₁), `boundary_composition_is_zero()` (∂₁∂₂=0),
  `n_nodes`/`n_edges`. Item 1: additive `commit` kwarg on `build_citation_complex` (default None =
  all-history union, unchanged; `<sha>` = anchored). Item 3: live β₁ cross-checked vs independent ripser.
- **LIVE RESULT:** β₁ = **24** independent citation threads over the corpus reference graph @ HEAD
  (Hodge `dim_ker_L1` == ripser H₁, cross-verified), n_nodes=110, n_edges=217, ∂₁∂₂=0.
- **Gate:** ruff ✓; mypy typed 0 (186 files); argless mypy 69 (unchanged); type_gate OK; pytest 1131
  passed / 7 skipped / 2 failed (the known-flaky live-model dream e2e, TimeoutError — the only tolerated).
- **Cost:** self-driven opus, ~96k output / ~$10.76 whole-session (graduation + build), ratio ~0.53×;
  **week held flat at 89%** (subscription-covered). No delegation, no fable.
- **Next (owner-directed):** graduate CQ-wire-2 (two-snapshot `‖[d,τ]‖` coherence), then build it. Data
  probed: 435 distinct commits carry corpus→corpus edges (~320/commit) — two-snapshot is NOT data-starved.

## 2026-07-15 — bp-038 (CQ-wire-2) COMPLETE: two-snapshot ‖[d,τ]‖ coherence — the algebra is fully wired

- **Built:** `core/temporal_view.py` — `coherence_to(other)` + `CoherenceReport` + `_restrict` (two-snapshot
  citation-coherence: σ = identity on the common node set, `‖[d,τ]‖` = severed-citation count, `is_flat`,
  node deltas) + `supersession_wellfounded`/`open_supersession_wellfounded` (poset `δ_D²=0` health) +
  `open_coherence`. Wires operators.py + superconnection.py + boundary.py — the two-snapshot half.
- **σ ruling (§3 Q1):** restrict-to-common (measure citations lost between notes present at BOTH commits;
  node add/drop is a separate axis). The dropped-node-is-not-severed falsifier guards the augment-semantics.
- **LIVE:** two-snapshot `‖[d,τ]‖` = 0 (flat, +1 node) comparing the two most-recent DISTINCT snapshots
  (`3797f8b→177b7fd`), cross-checked vs independent set arithmetic; supersession health True.
- **finding-0082** (builder-resolved): `VersionStore` has no doc_id enumerator → `supersession_wellfounded`
  requires explicit `doc_ids`; the factory scopes to the anchor's corpus nodes. A `VersionStore.doc_ids()`
  read (owner-gated store write) is the future full-corpus fix.
- **Gate:** ruff ✓; mypy typed 0 (186); argless mypy 69 (held); type_gate OK; pytest 1138 passed / 8
  skipped / 0 failed. Cost: self-driven opus, ~0.4× est. No delegation, no fable.
- **`core/temporal` FULLY WIRED** (bp-037 β₁ + bp-038 ‖[d,τ]‖) — "complete the algebra" (roadmap #1) DONE.
- Design thread captured: `docs/brainstorms/temporal-clocks-and-strata.md` (logical clock / per-stratum
  sub-clocks / relativity / the curvature convergence → a locally-clocked superconnection, fable-grade).

## 2026-07-15 — CQ-scope FORMALIZED (roadmap #2): the fable pass ran early, on usage credits

- **The lead unit, executed at tier:** the owner's directed FABLE session (`claude-fable-5`, usage
  tokens — not waiting for the Jul-17 reset). Required context honored in full: CQ §2.1 (C2 seed) +
  **`temporal-clocks-and-strata.md` read in full** (owner-directed) + the built View instances.
- **The pass:** `docs/brainstorms/cq-scope-fable-pass.md` (S1–S8, graded). Headlines: Σ = downward-closed
  sets of the stratum-refinement forest (C1/π_MR as elements; denylist an ideal off ⊤); **T = (clock,
  window)** — clocks are monotone coarsenings of the ledger's causal order (N ⪰ N_s, N ⪰ commit ⪰
  distinct-snapshot), anchor first-class, cross-clock meets pull back to a materialized common refinement
  or are a CONSTRUCTOR ERROR (T honestly a *partial* meet-semilattice until N materializes); the **SLICE
  rule** (multi-stratum "now" must carry a consistent cut; commit SHA = the cut for repo-backed strata —
  retro-explains the shared `_resolve_default_commit` discipline); **Inv vs Rate(κ)** result typing (rule
  CLOCK; all built instruments audit Inv; R1 velocity = first Rate customer); **A = {read<propose} ×
  {store-write} × {world-write ε}** (the seed's "write" rung conflated sensor projection with effector
  mutation — split; Track G's max-tier-NONE = `⊤_deployed.W_world = NONE`); firewalls-as-ideals;
  enforcement tier an annotation (min-law), never a lattice element.
- **The note:** **`dn-capability-scope`** (`docs/design-notes/capability-scope-algebra.md`, status
  `draft`) — states the decisions, Views-as-instances table, parked CS-a…CS-f. **AWAITS OWNER
  RATIFICATION** (hand edit). On ratification, `/graduate` mints ONE build plan: `core/scope.py`, a pure
  typing layer (lattice ops, ideals as data, `req()` on View constructors); falsifiers: bit-identical
  reads, lattice property tests, cross-clock-meet raises, delegation-exceeding-parent unrepresentable.
- **Desk:** bp-038 `cost.actual` reconciled from the fresh /usage (credits flat $89.59 across the build;
  week 90%→91%). External citations in the pass flagged `[FROM MEMORY — verify]` per external-grounding.
- No delegation. Docs-only session (no gate run needed — no Python surface touched).

## 2026-07-15 — SAME SESSION (owner-extended): the rigorous pass over the two open brainstorm threads

- **Owner asked in-session** for a proper rigorous pass over `edge-dynamics-vector-field.md` +
  `temporal-clocks-and-strata.md` → **`docs/brainstorms/velocity-and-clocks-fable-pass.md`** (X1–X3,
  V1–V6, T1–T5; every claim graded, several REFUTED-and-repaired). Headlines:
  - **X2 (the unlock):** exact one-step differences are MEASUREMENT-class — the R-ladder gates fits
    only (bp-038's precedent generalized). Two-snapshot velocity instruments need no R1.
  - **V1:** velocity-Hodge splits (`P_harm Δw` + `(ΔP_harm)w`); NEW buildable instrument — the
    **harmonic-subspace rotation** (principal angles; TRA R4 made measurable); the brainstorm's
    falsifier was near-tautological → replaced by the **alive/stale hole discriminator**.
  - **V2:** "Koopman-lite" REFUTED — covariance eigenmodes are POD, and the transport's
    order-upper-triangularity makes it non-normal exactly when supersession is active; legitimized
    as DMD's spatial half. **V4:** duality is half a theorem (converse refuted). **V5:** conflation
    split. **V3:** eigenSPACE (determinism) repair.
  - **V6:** prediction-residual = Kalman innovations; by TRA R6 supported on injection events;
    **provenance-decomposable (r_owner + r_dreamer) by construction** — demon-vs-source is now a
    specified experiment.
  - **T1:** proper time = N_s-increment EXACTLY (per-store total orders); the TRA §2 anchor answer.
    **T2:** locally-clocked superconnection DEFINED (clock field admissible iff target is a
    consistent cut — the SLICE rule as admissibility); REDUCTION to [d,τ] at constant field proven.
    **T3:** Φ=L⁺J auto-centers (global rate is gauge); geometry is Rate(κ)-typed (declare the clock);
    first instrument = activity-for-density in diffusion-maps α; **ẅ/radiation REFUTED** (no wave
    equation). **T4:** heat death = Banach on TRA R6; belief view has ONE injection channel (dreamer
    modulates it — two-layer skew-product); **FDT first formula: corpus temperature σ² = q/(1−γ²)**.
    **T5:** unification candidate `𝔸_Φ = d_Φ + τ` (SKETCH).
- **Ledger:** all five VF-* rows → formalized (data gates unchanged; VF-velhodge partially UNLOCKED);
  the Fable-cap external root largely discharged. The post-reset TRA revision now carries T1 + T4 +
  the owner's §2.5 erratum in one revision, opus-draftable (warrant banked). One sonnet+web
  citation-verify sweep now covers both passes' externals.
- **T6 (owner closing coda):** cosine is the LOCAL metric only (1−cos isn't a metric; arccos is the
  spherical geodesic); retrieval distance = the K(β) geodesic family at finite β (β* excludes the pure
  limit); the activity field is a refractive index (Fermat) computed by the same L⁺ that measures the
  β→0 distance; **CQ-mode1b re-warranted as the intrinsic retrieval geometry** (gates unchanged).

## 2026-07-15 — SAME SESSION (owner-extended ×2): the remaining design notes DRAFTED — the arc is concrete

- **Owner asked: "create the remaining design notes so everything can start being made concrete."**
  Done at fable, from the banked warrants (both passes):
  - **`dn-temporal-geometry`** (`docs/design-notes/temporal-geometry-and-drives.md`, draft) — the TRA
    extension home: the time-index (ledger = causal set; proper time EXACT; anchors = cuts; clock
    declarations), the corrected energy picture (**finding-0083** erratum in its sharpened one-channel/
    two-layer form; heat death = Banach; corpus temperature σ²=q/(1−γ²); demon-vs-source protocol),
    the velocity-conformal geometry (auto-centering Φ; geodesic retrieval T6; the α-instrument;
    ẅ refuted), the locally-clocked superconnection (def + reduction) + 𝔸_Φ candidate. Parked TG-a…f.
  - **`dn-velocity-instruments`** (`docs/design-notes/velocity-instruments.md`, draft) — the typing
    rules X1–X3 as binding law; **the two measurement-class instruments fully pinned** (harmonic-
    subspace rotation on X_cite, Inv-typed, extends TemporalView with a `RotationReport`; alive/stale
    hole discriminator, mirror-side, A7-bound, global-energy v1, localization joins at L-b) with
    falsifiers named; the R-gated catalog (V2–V6) pinned with repairs baked in so each later
    graduation needs zero new design. Licenses ONE build plan now. Parked VI-a…e.
  - **`finding-0083`** (PROMOTED same-day) — the TRA §2.5 gloss erratum, warrant-linked to the pass
    and resolved into `dn-temporal-geometry` (ratified TRA text untouched, A8 honored).
- **The concrete path now:** THREE draft notes await owner ratification (`dn-capability-scope`,
  `dn-temporal-geometry`, `dn-velocity-instruments`) → each ratification unlocks /graduate → the
  builds are Opus-tier (no fable needed; the design is banked). Buildable immediately on ratification:
  the scope typing layer (`core/scope.py`) + the velocity-instrument pair.

## 2026-07-15 — SAME SESSION (6): owner RATIFIED all three notes → CQ-scope GRADUATED (`bp-039` proposed)

- **Owner ratified all three fable notes by hand** (`draft→ratified`: `dn-capability-scope`,
  `dn-velocity-instruments`, `dn-temporal-geometry`) — the blessing flip committed FIRST at `3f5591d`
  (0060 discipline; no Co-Authored-By — owner blessing, not agent code). `/graduate` now unblocked.
- **Fresh /usage relayed** (prices the fable session): usage credits **$112.43/$150 = 74%** (up from
  $89.59 → the fable session drew **~$22.84**, on credits as planned; ~$37.57 headroom, resets Aug 1);
  **week 92%** (binding Opus meter, resets Jul 17 8pm ET); Fable weekly 100% (resets Jul 17).
- **`dn-capability-scope` GRADUATED → `bp-039 CQ-scope` (proposed).** The note licenses exactly ONE
  plan; this is it — `core/scope.py`, a **pure typing layer, zero behavior change** (bit-identical
  reads the whole-plan falsifier). Four blast-radius-ordered items: (1) the `Scope` lattice + `WorldReach`
  NONE-floor + partial clock T-meet + firewall ideals; (2) lattice-law/firewall/delegation property
  tests; (3) `req()` retrofit — a `SCOPE` class constant on the five Views + the ops-side
  `ReversibilityClass→WorldReach` bridge (touches existing code); (4) Inv/Rate markers (independently
  approvable, the deferrable one). Grounded in-session via ONE Explore subagent (context economy).
  Est. opus 240k, self-driven ~0.5–0.8×; no fable, no xhigh. **Awaiting owner `proposed→ready`.**
- **Reconciliation surfaced at graduation** (§4): the note's `W_world = NONE < SENSING` is NOT the
  code's `ReversibilityClass` (SENSING-floored); resolved as an EXTENSION — a new pure `WorldReach`
  enum core-side, the bridge ops-side (ops→core preserved, `core/scope.py` imports nothing from ops).
- **Still awaiting graduation** (owner picks slot): `dn-velocity-instruments` (the measurement-class
  instrument pair) + `dn-temporal-geometry` (mostly gated programs). Both ratified, Opus-buildable.

## 2026-07-15 — SAME SESSION (7): `bp-039 CQ-scope` BUILT + SEALED (the scope typing layer ships)

- Owner blessed `bp-039` `proposed→ready` by hand; self-driven build (orchestrator-as-builder, no
  delegation, no fable — week at 92%). **All four items green, 5-leg gate clean, SEALED complete.**
- **`core/scope.py` shipped** — the `(Σ,E,T,A)` capability lattice: `StratumScope` downsets (⊤_Σ=R∖𝔇),
  `EdgeScope` fibers, `TimeScope`=(clock,window) with the PARTIAL cross-clock meet (raises until N
  materializes), `Authority`=Privilege×W_Σ×`WorldReach` (the NONE-floored world-reach chain), firewall
  `Ideal`s, the SLICE rule, `Tier` as a compare=False min-annotation, and `Inv`/`Rate` result markers +
  Rule CLOCK. Pure-core (stdlib only). `req()` retrofitted as a `SCOPE` ClassVar on all five Views +
  the ops-side `world_reach` bridge — **bit-identical reads** (the whole-plan falsifier held).
- **Reconciliation delivered** (§4): the note's `W_world=NONE<SENSING` extends the code's SENSING-floored
  `ReversibilityClass` — a new `WorldReach` core-side, the bridge ops-side (ops→core preserved).
- **finding-0084 (spec-fidelity, resolved):** the public `SCOPE` constant tripped test_reference_view's
  exact-public-surface assertion (its sibling uses a robust no-mutator-leaked pattern); write_scope
  widened one file (warrant finding-0084), the assertion acknowledges SCOPE, no-mutator guarantee kept.
- **Gate (5-leg):** ruff clean · `mypy core…scripts` 0/187 (186→187) · argless mypy 69 HELD · type_gate
  OK · **pytest 1177 passed / 8 skipped** (1138→1177 = +39; even the flaky dream e2e passed). Zero fails.
- **Cost (measured, owner /usage):** whole session **$17.97**, **170.4k opus output** (~0.71× the 240k
  est; ratify+graduate+build+finding, one context, self-driven), **week 92%→93%**, **CREDITS UNCHANGED
  at 74%** ($112.43 — subscription/weekly-covered, drew zero credits). 1938 LOC added / 139 removed.
- **Note §3 Consequence 1 DISCHARGED.** Consequences 2–4 now expressible (delegation law testable —
  wiring parked; instruments declare Inv/Rate(κ) at graduation; fable geometry units consume T's clocks).
- **Still to graduate** (both ratified, Opus-buildable): `dn-velocity-instruments`, `dn-temporal-geometry`.

## 2026-07-15 — /triage sweep (8): reflection after the CQ-scope build

- **Routed 5 orchestrator findings `open → routed`:** 0065 (workflow node-kind — ruled option
  2-narrow, awaits owner concurrence + follow-up plan), 0069 (live-flake = machine-wide RAM pressure
  across sibling worktrees — already batched at oq-0018), 0077 (id:: embedding pollution), 0079 (σ
  re-tune), 0080 (`dn-core-query-protocol` stale-frontmatter erratum).
- **Batched 4 new owner-questions:** oq-0022 (finding-0065 workflow-kind concurrence + plan mint),
  oq-0023 (finding-0077 strip-props scope: id:: only vs all key::), oq-0024 (finding-0079 σ value +
  build a σ-sweep harness), oq-0025 (finding-0080 note-erratum: annotate the ratified note vs leave
  the finding). Each carries a `default_if_unanswered` with a park condition (§10). Inbox now
  oq-0001…oq-0025 (12 still open/awaiting owner incl. the new 4 + oq-0019's owner-confirm flip).
- **Resolved 1:** finding-0082 `open → resolved` (resolved-in-place in bp-038 —
  `supersession_wellfounded` takes explicit `doc_ids`; the status field merely lagged).
- **finding-0084 (this session's, spec-fidelity) already resolved** in the bp-039 build. Noted as a
  4th data point in the /graduate-foresight class (0071/0072/0075): graduation should scan the
  retrofit targets' EXISTING tests for exact-public-surface / exact-coverage assertions that an
  additive change predictably trips, and pre-widen write_scope. **Standing-fix still owed** (amend the
  /graduate skill's test-path check) — deferred (week 93%; a cheap skill edit for a calmer session).
- **Builder-owned findings stay OPEN for their plans** (not resolved here): 0046, 0059, 0064, 0073,
  0076, 0078 (codebase/spec-fidelity/spec-defect → the owning plan's session).
- **No promotions minted:** 0065/0080 await owner concurrence (batched); nothing else is ready.
- **Book debt (§12):** `docs/book/` is NOT scaffolded; three notes ratified this session
  (dn-capability-scope BUILT, dn-velocity-instruments, dn-temporal-geometry) + the CQ-scope build all
  accrue debt against the pending first scribe plan. Offer `/scribe` to scaffold when a slot opens.
- **Plan board:** complete=bp-000..bp-039; proposed/in-progress/ready = none. Active plan: none.

## 2026-07-15 — σ re-calibration scoped → bp-040 `sigma-sweep` (proposed); finding-0077 corrected

- Owner asked to tackle the σ re-calibration (finding-0079). Grounded the machinery (one Explore):
  σ affects ONLY clustering (`cluster_notes(threshold=σ)`) over FIXED centroids → a sweep is READ-ONLY,
  re-embed-free, no daemon-down. The live graph is already clean (bp-036 strip + the owner's 2026-07-14
  re-embed). So the work is a small read-only σ-sweep harness + the owner's config decision.
- **`bp-040 sigma-sweep` graduated (proposed)** — `scripts/sigma_sweep.py`: sweep σ∈[0.55,0.75] over the
  live mirror centroids, report edges/clusters/near-threshold("bubble") pairs per σ; NO re-dream per σ
  (once at the chosen σ, separately), NO config write (owner-gated hand edit), NO auto-recommended σ.
  Warrant = finding-0079 (no new design → no ratified note needed). Est. opus 90k, self-driven.
- **/triage-8 correction:** finding-0077 → **resolved** (bp-036 already stripped ALL `key::` props +
  the owner re-embedded — the strip question was answered before I batched it). **oq-0023 closed as
  moot.** So the σ work has no finding-0077 dependency.

## 2026-07-15 — ⭐ FABLE pass: `dn-evaluation-harness` written (draft) — the consolidated evaluation harness

- THE fable design pass (fable+xhigh, on usage credits, owner-directed): wrote
  `docs/design-notes/evaluation-harness.md` (`dn-evaluation-harness`, **status: draft** — owner ratifies
  by hand). Consolidates the two draft harness spines — `capability-evaluation-harness` (offline: masked
  replay, transformation algebra, r0→r8 ladder, six batteries, eval-results store) +
  `live-adoption-and-longitudinal-harness` (Track L: shadow/run ledger, verdicts/REPL, tuning manifest,
  curves, digest) — into ONE subsystem: two corpus bindings (fixture-bound | mirror-bound) of one engine
  over one substrate, unified key `(spec_hash, corpus_ref, config_fingerprint, seed)`.
- Decisions taken in-note: **SUPERSEDES both spines** (draft+not-built; stamped at ratification, EH-a),
  with 5 enumerated amendments (A-1 overnight thoroughness lifts the "3–5 values, cheap" compromises;
  A-2 bounded auto-apply exists per-lever under §14, revising Track L §7; A-3 catalog extended +
  Inv/Rate(κ)-typed; A-4 eval-results→DuckDB, run ledger→SQLite; A-5 one substrate literal).
  **Objective function decided:** no global objective — per-sweep declared registry key; guardrails
  (golden recall / drift≤Θ / grounding-defect≈0 / integrity green) lexicographically prior;
  `f9_composite` default → `precision@review` once L2 verdicts accrue (EH-c). Optimizer = deterministic
  grid code, **model-free** (the curve is the adviser).
- The novel core (§2.6): sweep spec + optimizer over the lever grid; per-lever `autonomy` field
  (`propose` default / `auto` opt-in: `auto_band ⊆ range`, max_step, cooldown; `SAFE_LEVERS` becomes
  DERIVED from the manifest); never-tunable fixed points structurally unable to express either mode
  (no `Lever` constructor → unnameable; denylist + loader hard-fail as backstops).
- Build decomposition **E1–E8** (§3): E1 eval-results store+registry (keystone) → {E2 run ledger+shadow,
  E4 reports+cost ledger} ∥; E3a propose-mode sweeps, E3b auto-apply (only after blessed propose-mode
  sets); E5 wire flag-off instruments (A2 SnapshotStore, CoherenceReport, adjudicator panel,
  effector_drift); E6 review REPL; E7 longitudinal+F4+Θ-calibration; E8 capability batteries.
  **bp-040 re-derived as the first sweep instance** (`sweep.dreamer-sigma-ab`: full σ grid ×
  {phase7, dream_v2} × {F9, A2 axes, golden, drift}; needs E1+E2+E5(A2)+E4); its report feeds bp-041.
- Disk-status verified while writing: `core/stores/verdicts.py` EXISTS (L2 store built);
  `runledger.py` / `tune.py` / `review.py` / `curves.py` / `eval/longitudinal.py` / `eval/capability/`
  NOT built; `tests/longitudinal/` empty. Track L's "Built:" headers were spec, not reality. Exact lever
  names pinned from `ops/levers.py` (dream_similarity_threshold etc.).
- Docs-only session — no gate run needed (no Python surface). No status flipped; nothing built (A4).
- **Plan board:** complete=bp-000..bp-039; bp-040 proposed (ON HOLD, subsumed — re-derive from this note
  post-ratification); ready/in-progress=none. **Next: owner ratifies `dn-evaluation-harness` →
  `/graduate` the E1–E8 decomposition** (align `dn-velocity-instruments` graduation with E5/catalog).

## 2026-07-15 — `dn-evaluation-harness` RATIFIED (owner hand edit); spines stamped superseded

- Owner ratified `dn-evaluation-harness` same-day. Blessing flip committed FIRST (`5bbdcec`, rule 0060).
- EH-a executed: both spine notes stamped `status: superseded` + `superseded_by: dn-evaluation-harness`
  (`capability-evaluation-harness.md`, `live-adoption-and-longitudinal-harness.md`) — a non-blessing
  orchestrator edit; their §5/§7/§9 and L1–L5 detail remains the protocol annex per the ratified note §1.2.
  (Process note: the stamp must be ONE atomic front-matter edit per file — scope-guard A8 reads the
  working-tree status, so flipping `status` first locks the file before `superseded_by` lands.)
- **Next: `/graduate dn-evaluation-harness` at OPUS** (design done; graduation is template work —
  fable reserved for design/gates, and fable weekly is 100%). E1 (eval-results store + registry) first.

## 2026-07-15 — `/graduate dn-evaluation-harness` → the milestone-1 tranche minted (bp-042..bp-045, proposed)

- Graduated by the orchestrator (OPUS, self-driven — no subagents; the /usage note flags subagent-heavy
  sessions as 46% of spend, and graduation is orchestrator work). Owner chose **"Graduate now"** with
  /usage in front of them (week 95%, credits 81% $122.94/$150, fable 100%; all reset Jul 17 8pm ET).
- **Decomposition judgment (transparent, not a silent cap):** graduated only the **milestone-1 critical
  path** — the four plans that compose the first overnight dual-dreamer A/B (§3 sequencing `E1 → {E2, E4}`
  + `E5(A2)`). The downstream tranche (E3a, E3b, E5-rest, E6, E7, E8) has its boundaries fixed by §3 but
  grounds far better AFTER E1/E2 land (E3a must pin against the store's *built* surface, not design-only)
  — so it graduates in a follow-up slot post-E1/E2 (and post Jul-17 reset). Honors "boundaries decided
  with the whole note in view" (they are, §3) without spending thin opus grounding plans that sit weeks.
- **Minted (all `proposed`, journals alive):**
  - **bp-042 `eval-results-store` (E1, keystone)** — DuckDB store, §2.1 key, append-only-**by-key**
    (resumability + honest comparison), the metric registry, absorbs `eval/metrics.py`, the eval-isolation
    integrity tooth. Items 1–4. Opus 200k est. `depends_on: []`. Builds FIRST.
  - **bp-043 `run-ledger-shadow` (E2 + the run-producer role)** — SQLite/WAL `dream_runs`+`dream_claims`,
    content-addressed `claim_id`, `novel`-on-insert; `ShadowRunner` (both pipelines, one snapshot) writing
    claims → ledger AND registered metric readings (guardrails + dream_v2 `structural_axes.*`) → the E1
    eval store; shadow trough job + isolation tooth. Items 5–7. Opus **260k** est. `depends_on: [bp-042]`,
    `parallelizable_with: [bp-044]`.
  - **bp-044 `harness-report` (E4)** — deterministic model-free renderer (`data/reports/`, markdown+JSON
    one-model-two-renderings, terminal sparklines, drift study, A/B tables) + the cost ledger (a
    `harness_cost` table in telemetry.duckdb, SCHEMA_VERSION 2→3, additive). Items 8–10. Opus 200k est.
    `depends_on: [bp-042, bp-043]`.
  - **bp-045 `wire-snapshot-a2` (E5(A2) slice)** — the ONE-kwarg wiring of `snapshots=open_snapshot_store`
    into `build_dreamer` so dream_v2 step-10 fires; phase7 bit-identical. Item 11. Opus 60k est.
    `depends_on: []`, `parallelizable_with: [all]`. Buildable first (a good tiny first build).
- **Key graduation decisions (documented in the plans):**
  1. **The §3-vs-§2.9 soft seam, resolved** (bp-043 §1): the milestone A/B is the **single-config**
     dual-pipeline comparison (E1+E2+E5(A2)+E4, "one snapshot"); the σ-**grid** version
     (`sweep.dreamer-sigma-ab`) is E3a's declarative sweep engine, deferred. So **E2's ShadowRunner is the
     harness's run PRODUCER** — it writes through the eval store ("everything writes through it", §2.2),
     hence bp-043 → bp-042.
  2. **A2 per-run keying WITHOUT a schema change** (bp-043 Q6): `StructuralSnapshot` has no config/run key,
     so the runner reads `SnapshotStore.latest_structural()` and writes keyed `structural_axes.*` `Reading`s
     into the eval store; `structural.duckdb` unchanged; attribution lives in the §2.1 key.
  3. **E5(A2) kept standalone (bp-045)**, not folded into bp-043 — buildable first/parallel, avoids
     renumbering. The rest of E5 (CoherenceReport caller, adjudicator panel, effector_drift → reports) is
     the deferred **E5-rest** plan (report enrichments; depends on E1+E4 built).
- **DEFERRED tranche (boundaries fixed by §3; graduate post-E1/E2, post-reset):** E3a (sweep engine
  propose-mode; needs E1) · E3b (bounded auto-apply; only after propose-mode blessed sets) · **E5-rest**
  (CoherenceReport replay-pair caller + adjudicator confidence panel + effector_drift report-only axis;
  needs E1+E4) · E6 (review REPL; verdict store already built) · E7 (longitudinal + F4 + Θ-calibration) ·
  E8 (capability batteries; instance #1 first; P1 codegraph its own plan). Also align **dn-velocity-
  instruments** graduation with E5/catalog rows 9–10 (RotationReport + alive/stale discriminator) and
  **dn-temporal-geometry** (demon-vs-source = catalog row 12, R-gated).
- **bp-041 RESERVED** (not authored) — wire dream_v2 LIVE replacing Phase-7; graduate AFTER the owner sees
  the first A/B report. bp-040 stays `proposed`/subsumed (re-derives as `sweep.dreamer-sigma-ab` under E3a).
- Docs-only session (build plans + journals) — **no gate run needed** (A4: graduation implements nothing).
  Nothing built, no status flipped. Plan board: complete=bp-000..bp-039; proposed=bp-040 (subsumed),
  **bp-042, bp-043, bp-044, bp-045**; ready/in-progress=none.
- **Next:** owner blesses `proposed→ready` (by hand) for the tranche — recommend order bp-042 → bp-045 →
  bp-043 → bp-044 (bp-042 keystone; bp-045 tiny/independent; bp-043 needs bp-042; bp-044 needs both). Then
  `/build` or delegate (pre-flight budget gate first — opus week thin at 95% until Jul 17).

## 2026-07-15 — BUILT + SEALED bp-042 (E1 keystone) + bp-045 (E5(A2)) — owner "start getting results"

- Owner blessed bp-042 + bp-045 `proposed→ready` by hand (committed FIRST, rule 0060: `d9be748`,
  `fc52eb9`); chose "bp-042 + bp-045 now, the big ones (bp-043/044) after the Jul-17 reset". Both BUILT
  self-driven (orchestrator-as-builder, no delegation), 5-leg gate green, SEALED complete.
- **bp-042 `eval-results-store` (E1 keystone) — COMPLETE** (`4bb201b` build, `aef60e1` seal). The
  append-only-BY-KEY DuckDB store (`eval/harness/store.py`: `EvalKey`/`Reading`, `put` skips a present
  cell + never overwrites/dups, `has/get/query`), the metric registry (`eval/harness/registry.py`:
  `MetricSpec`, fail-closed `get`, dup-reject, 4 built families golden/drift/f9/telemetry
  Inv/Rate(wall)-typed), `eval/metrics.py` absorbed by re-export (signatures unchanged), and the
  eval-isolation integrity tooth (transitive import-graph BFS: no path to `core.ingest`, no mirror-world
  touch ⇒ ∉ MIRROR_READABLE, with a negative control). +14 tests.
- **bp-045 `wire-snapshot-a2` (E5(A2)) — COMPLETE** (`92b8874` build, `7ff19ab` seal). `build_dreamer`
  now passes `snapshots=open_snapshot_store(cfg)` (catalog row 6 wired) → dream_v2 step-10 fires;
  phase7 `dream()` bit-identical (writes none). +2 tests (proven THROUGH the wired store).
- **5-leg gate (both, run SEPARATELY):** ruff PASS; mypy scoped 0 (190 files, 187→190); argless mypy
  **69 UNCHANGED** (the tooth HELD both builds; test-only type errors fixed — `Path|str` for `:memory:`,
  a `cast` for the `_RowSource` test double); ops.type_gate OK; pytest `-m 'not live'` **1185 passed /
  7 skipped / 9 deselected(live)** / 0 failures (+16 new). Live dream-e2e deselected (Ollama/slow,
  finding-0069; the project CI deselects `live` too) — deterministic + integration tiers fully green.
- **finding-0085 filed + handled:** write_scope inline comments break scope-guard's YAML parse (the
  0071/0072/0075/0084 lineage). bp-042's write_scope cleaned in-session (orchestrator plan-fix
  `e52151b`); bp-045's pre-cleaned before build (`749485b`). **bp-043 + bp-044 still carry inline
  comments** — pre-clean them before those builds (post-reset). Durable fix owed: scope-guard should
  strip trailing ` #…`, and/or the /graduate skill should forbid inline write_scope comments.
- **cost.actual: $/opus-output PENDING owner /usage** (both plans' seals mark `tokens: pending`,
  `ratio: pending` — backfill at session wrap). Self-driven; est bp-042 200k / bp-045 60k.
- **Plan board:** complete=bp-000..bp-039, **bp-042, bp-045**; proposed=bp-040 (subsumed), bp-043,
  bp-044; ready/in-progress=none. **Milestone-1 half-built:** E1 + E5(A2) done; **E2 (bp-043) + E4
  (bp-044) remain** for the first A/B report — build post-Jul-17-reset (owner blesses them then).

## 2026-07-16 — DELEGATE-BUILT + SEALED bp-043 (E2 run-ledger + shadow) — first supervised builder

- Owner directed delegated-builders mode (spawn supervised builders, orchestrator supervises). Week
  reset (owner /usage: week 1%, session 6%, Fable 0%) → pre-flight budget gate PASS (est 220k ×1.6 ≈
  352k ≪ open weekly allowance). Flipped bp-043 ready→in-progress FIRST (`d48068d`), spawned ONE
  full-strength opus builder in an isolated worktree (background), supervised to green.
- **bp-043 `run-ledger-shadow` (E2) — COMPLETE** (builder commits `196e5fc`/`b76150e`, merge `ef61c2b`,
  seal `dfd3223`). `core/stores/runledger.py` — SQLite/WAL append-only `dream_runs`+`dream_claims`,
  content-addressed `claim_id = sha256(kind‖sorted(set(support))‖polarity)` EXCLUDING surface/
  confidence, method→polarity map, `novel`-on-insert across ALL prior runs (indexed). `core/dreaming/
  shadow.py` — `ShadowRunner.run` drives BOTH pipelines over ONE MirrorView snapshot MODEL-FREE
  (`collect_claims`+`adjudicate`, never `synthesize`), dream_v2 enabled in-process via `replace`
  (never the disk flag), claims→ledger + guardrails(`drift_D`/`golden_recall` by registry name)+
  `structural_axes.*`(from an EPHEMERAL scratch SnapshotStore, never live `structural.duckdb`)→ the
  E1 eval store, each keyed per §2.1; not-captured fallbacks (no silent cap). `scheduler/cron.py` —
  `SHADOW_KIND`+`enqueue_shadow`+`shadow_handler` ADDITIVE beside untouched `enqueue_dream`/`dream_
  handler`/`cron_handlers`. +17 tests (7 runledger, 5 shadow, 5 AST-isolation tooth w/ 2 neg controls).
- **Whole-plan falsifier HELD:** live dream surface unchanged — shadow writes only ledger+eval store,
  live derived-store row-count unchanged, `[dream_rnd]` disk flag still False, model-free. Shadow
  machinery BUILT but NOT activated in the live loop (`cron_handlers` untouched, deliberate) —
  activation (register SHADOW_KIND→handler + call enqueue_shadow on a tick w/ a live ledger) is the
  deploy-gated RUN.
- **5-leg gate (orchestrator re-ran SEPARATELY on the MERGED tree):** ruff PASS; mypy scoped 0 (192
  files, 190→192); argless mypy **69 UNCHANGED**; ops.type_gate OK; pytest `-m 'not live'` **1202
  passed / 7 skipped / 9 deselected(live)** / 0 failures. Diff scrutinized pre-merge: 8 files ==
  write_scope+journal+finding-0086, nothing out of scope.
- **finding-0086 filed (spec-fidelity, builder-resolved):** `structural_axes.*` written per §3 Q6 but
  not registered in `eval/harness/registry.py` (out of write_scope; `put()` doesn't gate on
  registration → no runtime break). Registration follow-up owed — natural rider on E4/bp-044.
- **finding-0085 (a) LANDED:** the /graduate skill now forbids inline write_scope comments + codifies
  the retrofit test-path pre-widen discipline (`b65cc3f`); (b) the scope-guard ` #…` strip narrowed to
  optional tooling (warrants its own tiny plan — enforcement machinery, no parser test today).
- **cost.actual:** builder self-reported ~180k tokens / 89 tool-uses / ~20.5 min, ratio ~0.82× est
  (UNDER the delegated-wave 1.6× margin — fully-pinned greenfield). Dollar/session-delta backfill owed
  from owner /usage at session end.
- **Plan board:** complete=bp-000..bp-039, **bp-042, bp-043, bp-045**; proposed=bp-040 (subsumed),
  bp-044 (ready); in-progress=none. **Next:** graduate E3a(+E6) now grounded against BUILT E2, then
  delegate bp-044 (E4) — its RunLedger interface is now built, not inferred. Then milestone-1 is
  code-complete → the first dual-dreamer A/B run (ShadowRunner over the live mirror; the RUN is the
  deploy-gated step).

## 2026-07-16 — DELEGATE-BUILT + SEALED bp-044 (E4 report generator + cost ledger) — MILESTONE-1 CODE-COMPLETE

- Second supervised builder this session (SEQUENTIAL after bp-043 merged — bp-044 `depends_on
  [bp-042, bp-043]`). Delegated grounded against the NOW-BUILT E1/E2 surfaces (not inferred pins),
  briefed on finding-0086. Full-strength opus builder, isolated worktree, supervised to green.
- **bp-044 `harness-report` (E4) — COMPLETE** (builder `b0331dd`/`3185d44`/`a6a4adb`, merge `da61518`,
  seal `6a3006a`). `eval/harness/sparkline.py` — a pure deterministic Unicode-block sparkline. `eval/
  harness/report.py` — the `Figure`/`Report` model (every Figure carries its `EvalKey`), `build_report`
  (pure, READ-ONLY over E1 `query()` + E2 `runs()/claims()` + telemetry), `render_markdown`/`render_
  json` (ONE model, two renderings — cannot drift), the drift study + per-axis structural decomposition,
  the phase7-vs-dream_v2 A/B table, the cost appendix, `write_report` → `data/reports/<date>-<topic>/`.
  `scripts/report.py` — the CLI (stamps the date; renderer stays clock-free/deterministic). `core/
  stores/telemetry.py` — the ONLY existing-code touch, strictly ADDITIVE: `SCHEMA_VERSION` 2→3, a new
  `harness_cost` table + `record_harness_cost`/`harness_costs`/`harness_cost_count` (existing tables/
  readers/writers + all telemetry tests untouched). +18 tests.
- **Whole-plan falsifier HELD:** renderer READ-ONLY (no store-mutation call in report.py), every figure
  keyed (provenance), model-free deterministic (byte-identical re-render). Reconciliation (disclosed,
  journal + Item 9 commit): the A/B split is sourced from the ledger's explicit `pipeline` column
  (pipeline lives in the opaque `spec_hash`, not attributable from the shared `corpus_digest`/`config_
  fingerprint`); ledger/telemetry figures carry transparent source-tagged provenance keys — no reading
  lacks its key (not a §10 stop). finding-0086 reconciled: `structural_axes.*` rendered via `query()`
  without the fail-closed `registry.get` (registration STILL owed — a follow-up with registry.py in scope).
- **5-leg gate (orchestrator re-ran SEPARATELY on the MERGED tree):** ruff PASS; mypy scoped 0 (195
  files, 192→195); argless mypy **69 UNCHANGED**; ops.type_gate OK; pytest `-m 'not live'` **1220 passed
  / 7 skipped / 9 deselected(live)** / 0 failures. Diff scrutinized: 8 files == write_scope+journal.
- **cost.actual:** builder self-reported ~120k tokens / 75 tool-uses / ~13.4 min, ratio ~0.60× est
  (self-driven band — pure renderer over built surfaces). Dollar/session-delta backfill owed at wrap.
- **🎯 MILESTONE-1 CODE-COMPLETE:** E1 (bp-042) + E2 (bp-043) + E4 (bp-044) + E5(A2) (bp-045) ALL built.
  **Plan board:** complete=bp-000..bp-039, **bp-042, bp-043, bp-044, bp-045**; proposed=bp-040
  (subsumed); ready/in-progress=none.
- **Two open follow-ups:** finding-0086 (register the `structural_axes.*` family — a rider on the next
  registry-scoped plan) + finding-0085(b) (the optional scope-guard ` #…` strip — its own tiny plan).
- **Next:** (1) the RUN — ShadowRunner over the live mirror → the first dual-dreamer A/B report
  (`scripts/report.py`); running it live touches the daemon → the **deploy** owner-gate (not before).
  The report feeds bp-041 (wire dream_v2 live) + oq-0024 (σ). (2) graduate E3a (2-plan split: sweep
  engine + tuning-manifest/CLI; grounded against BUILT ShadowRunner + `ops/selfmod.py` proposal ledger;
  `config/levers.toml` is on-demand, not a gap) + E6 — from a FRESH context (graduate wants the whole
  note in view; this session is build-heavy).

## 2026-07-16 (session 16) — 🎯 THE RUN — the first dual-dreamer A/B report is PRODUCED

- **The harness fired end-to-end for the first time against the REAL corpus.** Owner-confirmed
  (confirm-consequential-actions: first exercise of new machinery on the live corpus), chose the
  **full** variant (golden retriever injected). **No deploy needed** — the session-15 PROGRESS entry's
  "deploy owner-gate" framing was for the *recurring* live shadow job; the one-shot data-gen is
  model-free, reads the live mirror READ-ONLY (`MirrorView`), and writes ONLY the harness stores
  (run ledger + eval DuckDB) — it touched NEITHER the daemon NOR the live derived store. Exactly as
  the resume brief predicted.
- **THE RUN** (`ShadowRunner(open_run_ledger(), retriever=<golden-fixture>).run()`): one live snapshot,
  both pipelines. corpus_digest `1b8d9d1e…`, config_fingerprint `22f6581e…`. phase7 run
  `990e2d3e…`, dream_v2 run `27f7f25a…`. The golden retriever = the `live` e2e pattern (ingest the
  frozen synthetic golden corpus into a throwaway store + real `qwen3-embedding:4b` embedder — reads
  the FIXTURE, never the vault; firewall intact) so the guardrails are captured, not logged
  not-captured.
- **THE REPORT** (`scripts/report.py` model, rendered around the daemon's telemetry write-lock via a
  fresh in-memory cost source — honest, since `harness_cost` has never been written and isn't even
  migrated into the live daemon's Jul-15 pre-bp-044 store): `data/reports/2026-07-16-dreamer-ab/`
  (gitignored — local file drop, ∉ MIRROR_READABLE).
  - **A/B (the headline):** dream_v2 = **8 claims / 6 novel**; phase7 = **1 claim / 1 novel**. The full
    interpreter panel surfaces 8× the single community lens over the identical corpus snapshot.
  - **golden_recall = 1.0** (both pipelines — the capability anchor holds; fixture retriever finds every
    golden note).
  - **drift_D = 0.13** (both) against the blessed tolerance band **Θ = 1.0** → well within tolerance,
    **no breach**. Structural axes captured for dream_v2: `frustration = 0.0`, `min_conductance = 0.0`.
  - **cost appendix:** empty — recorded in `coverage_notes` (no silent cap, §2.4). The `harness_cost`
    ledger has never been written; the live daemon hasn't restarted since bp-044 (still telemetry
    schema v2, no `harness_cost` table). Populates once a harness run logs cost / the daemon restarts.
- **Two RUN-surfaced observations (for /triage):** (1) 3 phase7 claim kinds (`bridge`, `centrality`,
  `density`) had no polarity mapping → defaulted `+` (the runner logged it, no silent cap — a
  `polarity_and_flag` coverage gap worth a finding). (2) both structural axes = 0.0 on the live
  snapshot — plausibly a small/sparse MirrorGraph, but worth a sanity check before the axes feed
  selection.
- **Feeds:** bp-041 (wire dream_v2 live — the 8-vs-1 differential is the evidence) + oq-0024 (σ:
  this run used the default `[dream_rnd].sigma`; the A/B is the substrate a σ-sweep varies).
- **Next:** graduate E3a (2-plan split) + E6 from fresh grounding (owner: this session, after the RUN).

## 2026-07-16 (session 16) — GRADUATED E3a-2 (bp-047) + E6 (bp-048); E3a-1 (bp-046) PARKED on the σ-fork (owner-decided)

- Ran /graduate over ratified `dn-evaluation-harness` §3 with the whole note in view (opus, self-driven).
  Delivered TWO of the three intended plans as `proposed`; the third surfaced a genuine design fork that
  is the owner's call, so it was filed + parked rather than built on an inferred decision (graduate A4).
- **bp-047 `tuning-manifest` (E3a-2) — PROPOSED.** `config/tuning.toml` (per-lever `autonomy`-schema
  overlay on the BUILT lever registry) + `eval/harness/tuning.py` (manifest model + resolved-manifest
  fingerprint) + `scripts/tune.py` (`show`/`set`/`history`/`--revert`, attended, driving the BUILT §14
  `SelfModLoop`). Items 15-16. `auto` mode + `apply_unattended` = E3b (out of scope). Fork-independent
  (a schema layer over whatever levers exist). Est opus/200k. `parallelizable_with: [bp-048]`.
- **bp-048 `review-repl` (E6) — PROPOSED.** `scripts/review.py` (model-free REPL: interleave the run
  ledger's phase7 vs dream_v2 claims = native A/B, keystroke owner verdicts SIGNED + stored via the
  BUILT verdict path reused verbatim from `scripts/verdict.py`, `subject_id = claim_id`) +
  `eval/harness/probes.py` (theory-probe candidate recorder; schema grounded in the Track L §3 annex at
  build, NOT invented). Items 17-18. Greenfield (`scripts/review.py` verified absent). Independent of
  everything + the σ-fork. Est opus/220k. `parallelizable_with: [bp-047]` → real parallel fan-out once
  both blessed.
- **finding-0087 (design) + the σ-fork — RESOLVED by owner.** Grounding found the note's sweep example
  (`levers = { dream_similarity_threshold = "full" }`) can't move the BUILT `ShadowRunner`: the 4
  registered levers are `[dreaming]`, but the runner computes from `[dream_rnd].sigma` (unregistered)
  and only fingerprints `[dreaming]` (`shadow.py:94-105`, a bp-043-parked placeholder). A sweep over any
  current lever → flat curves. oq-0024's σ (`dreaming.similarity_threshold`) ≠ the runner's knob
  (`dream_rnd.sigma`). **Owner chose fork option 1: register the `[dream_rnd]` knobs as levers** (the
  sweep varies what the runner reads; every swept knob stays a §14-gated registered lever). Folded into
  oq-0024 (σ VALUE still open — the sweep determines it).
- **E3a-1 (bp-046) — RESERVED, graduates next session against the resolved fork.** The complex plan (the
  sweep engine + the `ops/levers.py` widening + the `_config_fingerprint` widening touching `shadow.py`);
  banked for a fresh grounded pass per context economy. bp-046 items reserved as 12-14; bp-047=15-16,
  bp-048=17-18 (item order ≠ plan-id order here — documented). **bp-040 stays proposed/subsumed** until
  E3a-1 graduates (its superseder); NOT flipped this session.
- **Plan board:** complete=bp-000..bp-039, bp-042..bp-045; **proposed=bp-040 (subsumed), bp-047, bp-048**;
  reserved=bp-046 (E3a-1); ready/in-progress=none.
- **Next:** owner blesses bp-047 + bp-048 `proposed→ready` (by hand) → delegate as parallel supervised
  builders (disjoint write_scope). Graduate E3a-1 (bp-046) from a fresh context against the resolved fork.

### 2026-07-16 (session 17) — THE BUILD WAVE: owner blessed bp-047+bp-048 → ready; bp-047 SEALED (delegated)

- Owner blessed bp-047 + bp-048 `proposed→ready` by hand (commit `f0ab085`) — the build wave armed.
  Orchestrator flipped both `ready→in-progress` + committed FIRST (`dc4eae9`), then spawned TWO parallel
  supervised builders in isolated worktrees (disjoint write_scope; opus, inherited session tier).
- **Pre-flight budget gate cleared:** owner /usage week (all models) 4% (resets Jul 17), credits $27.06
  left (resets Aug 1). Builds draw the weekly subscription allowance (abundant), not the credit pool.
- **bp-047 `tuning-manifest` (E3a-2) — SEALED, complete.** Items 15 (`eval/harness/tuning.py` manifest
  model + loader + order-insensitive resolved fingerprint; `config/tuning.toml`) + 16 (`scripts/tune.py`
  attended `show`/`set`/`history`/`--revert` over the BUILT §14 `SelfModLoop`). POLICY-only manifest
  (range/kind DERIVED from `Lever`; never shadows local.toml); fail-closed on unregistered levers +
  `autonomy="auto"` (E3b). `--revert` reverts EXECUTED via the loop's rollback primitives, REFUSES a
  VALIDATED (terminal) proposal + offers the inverse `set` — no reimplemented gate, no faked transition.
  Falsifiers verified by orchestrator diff-read (fingerprint order-insensitive; no self-approve; no
  pre-approval overlay write). No findings; no §10 stop-and-raise. **Orchestrator re-ran the 5-leg gate
  independently: all green, argless mypy tail==69, suite 1243 passed.** Merged `--no-ff` (`351dc6d`,
  `73873eb` → merge). Cost: 104k tokens (harness-measured) = **0.52×** the opus/200k estimate — matches
  the milestone's well-pinned-delegated-lands-under calibration. Worktree removed.
- **bp-048 `review-repl` (E6) — SEALED, complete.** Items 17 (`scripts/review.py` model-free review
  REPL: joins `RunLedger.claims()` to `runs()` `run_id→pipeline` = native A/B, interleaves novel-first/
  conf-desc, keystroke→`VERDICT_TAXONOMY`, SIGNS each `VerdictPayload(subject_id=claim_id)` via the BUILT
  `sign_verdict`→`build_verdict_receiver` seam — the `ReviewDeps` injection keeps the builder on the
  in-memory/test-signer path, never the real signed store; fail-closed on missing owner key) + 18
  (`eval/harness/probes.py` append-only idempotent `ProbeStore`, `plausible`-only trigger, candidates-only
  — NO run trigger). **§3-Q4 probe schema GROUNDED in the Track L §3 annex** (`live-adoption-and-
  longitudinal-harness.md:140` `probe(probe_id, hypothesis, expectation_kind, target_hints)` + the
  `plausible→probe candidate` verdict-table row) — orchestrator verified the annex says exactly this; not
  invented; implements the plan's scoped subset (owner-initiated free-text `probe` command is a superset,
  out of scope). Falsifiers verified by diff-read (subject_id=claim_id; signed via receiver; model-free;
  probe only on plausible). No findings; no §10 stop-and-raise. **Orchestrator re-ran the 5-leg gate
  independently: green, argless mypy==69, worktree suite 1235.** Merged `--no-ff` (`33250a3`, `80c01e2`).
  Cost: 109k tokens = **0.49×** the opus/220k estimate. Worktree removed.
- **BUILD WAVE COMPLETE.** Both delegated builds landed under estimate (0.52× / 0.49×) — the well-pinned-
  delegated calibration holds a 5th time. Combined suite on main **1262 passed**, argless mypy==69, both
  features coexist green. Milestone-1's automated-tuning control surface (E3a-2) + the human-labeling
  surface (E6) now exist.
- **Session economics (owner /usage post-hoc, aggregate — 2 builds + orchestration):** $12.91 (opus),
  1866 LOC added / 152 removed. **week 4%→5% (+1pt), credits UNCHANGED $122.94/$150** — CONFIRMED: a
  delegated build wave draws the weekly subscription allowance, NOT the credit pool (credits engage only
  past the weekly cap). Standing budget-gate fact for future waves.
- **Next:** **/triage** the accrued debt (2 RUN observations — the polarity coverage gap + the 0.0 structural
  axes sanity-check; φ_conversation-sensor capture; findings 0086/0087). Then **graduate E3a-1 (bp-046)**
  — the sweep engine — from a FRESH context against the resolved σ-fork (register `[dream_rnd]` knobs as
  levers; it supersedes bp-040). Later, owner-gated: bp-041 (wire dream_v2 live).

### 2026-07-16 (session 17 cont.) — GRADUATED E3a-1: bp-046 `sweep-levers` + bp-049 `sweep-engine` (proposed); bp-040 SUPERSEDED

- Owner directed continuing the harness build in-session (opus). Ran the grounded /graduate pass over
  ratified `dn-evaluation-harness` §2.6/§2.9 against the RESOLVED σ-fork (finding-0087). **Split E3a-1 into
  TWO plans** (the fork-resolution is a distinct owner-blessable unit from the engine, and the engine
  depends on it) — fits the reserved 12-14 item band, no collision with bp-047/048's 15-18.
- **bp-046 `sweep-levers` (item 12) — PROPOSED.** The σ-fork resolution made concrete: register
  `dream_rnd_sigma` (section=`dream_rnd`, key=`sigma`, `[0.55,0.75]` FLOAT — the knob `shadow.py:139-146`
  actually reads for the dream_v2 graph, NOT `dreaming.similarity_threshold`) + widen
  `core/dreaming/shadow.py:_config_fingerprint` to hash the live value of every REGISTERED lever (derived
  from `ops.levers.LEVERS`, so bp-049 needs no second edit). write_scope: ops/levers.py, shadow.py,
  test_levers.py, test_shadow_runner.py (retrofit — carries the `config_fingerprint` assertions). Warrant:
  finding-0087. Est opus/120k. `depends_on: []`.
- **bp-049 `sweep-engine` (items 13-14) — PROPOSED.** The deterministic model-free optimizer: spec-TOML →
  grid over the swept lever → drive BUILT `ShadowRunner.run(config=modified)` per cell (resumable by the
  eval store's keying — free) → curve from `EvalResultsStore.query` → admissibility filter (guardrails
  lexicographically prior) → selection (§8 math: plateau center + least-motion tie-break) → emit
  `ProposedChange` into the §14 ledger via `SelfModLoop.propose` (PROPOSED only; honors `[selfmod] enabled`).
  Item 13 (spec+grid, writes cells) → 14 (optimizer+emit, the effect). write_scope: eval/harness/sweep.py,
  config/sweeps/dreamer-sigma-ab.toml, scripts/sweep.py + 2 tests. Est opus/240k. `depends_on: [bp-046]`,
  `supersedes: bp-040`.
- **Two grounding nuances baked into the plans (neither blocks build):** (1) `config_fingerprint` must hash
  live lever VALUES, not bp-047's manifest POLICY (static across a sweep → would collide every cell) —
  §2.1's "sha256 of the resolved tuning manifest" clarified in bp-046 §4. (2) `f9_composite` is REGISTERED
  (`registry.py:80`) but NOT written per-cell by `ShadowRunner` — so the first sweep's objective must be a
  written metric (`golden_recall`/`drift_D`/`structural_axes.*`); F9-per-cell wiring is a parked E5/E7/rider
  concern (bp-049 §3 Q3, §11).
- **bp-040 `dream-calibrate` → SUPERSEDED** (`superseded_by: bp-049`; orchestrator flip at graduation per
  §2.9, NOT a blessing). Its σ-connectivity sweep is re-derived as `config/sweeps/dreamer-sigma-ab.toml`.
  bp-040 stays inspectable.
- **Plan board:** complete=bp-000..bp-039 + bp-042..bp-048; **proposed=bp-046, bp-049**; superseded=bp-040;
  ready/in-progress=none.
- **Next:** owner blesses bp-046 → ready (by hand), builds it; THEN bp-049 → ready + build (depends on
  bp-046). /triage still owed. Once both build + the sweep RUNs → the σ curve closes oq-0024's value axis +
  feeds bp-041 (wire dream_v2 live, owner-gated).

### session-18 (2026-07-16) — the SEQUENTIAL sweep-engine build SHIPPED (bp-046 → bp-049)

Both halves of E3a-1 built, merged, sealed — sequential (bp-049 `depends_on: [bp-046]`, NOT a parallel
wave). Each a supervised worktree builder (opus), independently 5-leg-gated + scrutinized (falsifier
diffs read directly), merged `--no-ff`, worktrees removed.

- **bp-046 `sweep-levers` COMPLETE** (`03a47df` merge, `a1ebf61` seal; cost 0.67×, 80k/240k... 80k/120k,
  $4.24). Registered `dream_rnd_sigma` (section=dream_rnd — the knob dream_v2 actually reads for the mirror
  graph; distinct from the `[dreaming]` live-path σ) as a `[0.55,0.75]` FLOAT lever; widened
  `shadow.py:_config_fingerprint` to hash the live value of EVERY registered lever, derived from
  `ops.levers.LEVERS` (not a hardcoded list), keyed `<section>.<key>`. Falsifier verified: registered σ
  moves the fingerprint, unregistered dream_rnd knobs do not. **finding-0088 RESOLVED** as an orchestrator
  merge-scrutiny fix (the bp-047 shipped-manifest test made registry-faithful — a write_scope omission the
  builder correctly filed rather than routed around).
- **bp-049 `sweep-engine` COMPLETE** (`0f5f5c3` merge, `4717c77` seal; cost 0.61×, 148k/240k). The
  deterministic model-free grid optimizer: spec-TOML → grid over the swept lever → drive the BUILT
  `ShadowRunner` per cell (ONE shared eval store + ONE run ledger reused; golden-fixture retriever;
  resumability = the store's dedup, engine never re-keys) → curve from `EvalResultsStore.query` →
  admissibility filter (guardrails lexicographically prior, applied BEFORE argmax; not-captured refuses to
  emit) → §8 selection (widest near-optimal plateau center via grid-adjacency, least-motion tie-break —
  verified NOT to peak-chase a knife-edge max by an adversarial test) → emit `ProposedChange` via
  `SelfModLoop.propose` (PROPOSED only, honors `[selfmod] enabled`, never auto-executes). Supersedes bp-040.
  **finding-0089** (which per-pipeline curve `select` uses) resolved in-scope with a recorded
  `select_pipeline` default (the dream_v2 lane the σ lever drives); the design-note question left OPEN for
  /triage.
- **Suite 1264 (after bp-046) → 1287 (after bp-049)** on main; argless mypy==69 [HELD]; all 5 legs green.
- **Economics:** session-18 aggregate **$12.86** (opus; bp-046 $4.24 + bp-049/orchestration ~$8.62). Week
  6%→7% (+1pt), Fable 0%, **credits UNCHANGED $122.94/$150** — a build wave draws the WEEKLY allowance, not
  the $27 credit pool (confirmed a third time). Well-pinned delegated builds landed 0.67× / 0.61×.
- **Plan board:** complete=bp-000..bp-039 + bp-042..bp-049; superseded=bp-040; proposed/ready/in-progress=none.
- **Next:** the σ-sweep can RUN (owner/scheduler act; needs `[selfmod] enabled` to emit) → closes oq-0024's
  VALUE axis + feeds bp-041 (wire dream_v2 live, owner-gated). Owner floated a **σ-fibers / multi-strength
  design idea** (captured `brainstorms/`) — a live thread with the carried multiscale-dreamers brainstorm.
  /triage still owed (2 RUN obs + φ_conversation-sensor + findings 0086/0089).

### session-19 (2026-07-16) — 🧠 THE FABLE+xhigh DESIGN PASS: cross-strata/σ-fibers graduated into THREE drafts

- **The owner-sanctioned Fable+xhigh pass** (the one sanctioned use per context-economy; Fable pool was
  at 0%) worked `brainstorms/cross-strata-and-multiscale-dreamers.md` (all three capsules) + the two
  resonant captures into three `draft` design notes — separable because their blessing stakes differ.
  Batched as **oq-0027** for ratification review. DESIGN ONLY: nothing built, nothing blessed.
- **`dn-sigma-fibers`** (sigma-fibers-and-multiscale-dreaming.md) — Idea A concrete. The parked fiber
  object RESOLVED as (b)-sharpened: the fiber is the content-addressed CLAIM (`claim_id`,
  runledger.py:37) carrying its σ-support — bare-edge persistence proved DEGENERATE (≡ a monotone
  transform of the stored cosine), so claims are where persistence is non-trivial. `pers(χ)` =
  normalized support measure over the declared σ-range, with a convergence theorem (the pipeline is
  piecewise-constant in σ; breakpoints = sim-matrix entries ⇒ an exact grid-free oracle exists) and a
  three-clause falsifier (degeneracy anchor · ruler test · earning-its-place). Harness realization is a
  DERIVED CONSUMER, zero schema change — with a recorded capsule correction: per-claim persistence reads
  the RunLedger (claims), not EvalResultsStore alone; aggregates land in the eval store keyed by a
  fibers spec_hash carrying the grid. Strength→surfacing gate PINNED: two-axis lexicographic
  (SETTLED/HUNCH/RETAINED by pers; confidence orders within tier; NEVER one scalar; I1 untouched —
  surfacing only), F9-validated before shipping (noise-fixture SETTLED ≈ 0 ∧ planted → SETTLED ∧ beats
  best single-σ precision). Memory ceiling: zero models resident for everything licensed. Build
  decomposition FB-1..FB-4 (FB-4 parked). The owed σ-sweep RUN doubles as FB-1's first dataset.
- **`dn-resolution-result-typing`** — the algebra verdict, drafted as an ADDITIVE amendment to RATIFIED
  `dn-capability-scope` §2.3 (A8-clean: the ratified note is untouched; owner stamps a pointer on
  ratification, EH-a pattern). Ruling: Inv/Rate(κ) gains **Res(π)** + Rule SCALE — carriage (a
  resolution-graded value carries its ruler π like a Rate carries its clock) + capability-invisibility
  (PROVED: req(dream@σ) = MirrorView.SCOPE constant in σ ⇒ NO fifth scope coordinate, NO meet/join
  expression; the founding capsule's "local-vs-macro scope is meet/join" corrected). σ-persistence typed
  Res(π_σ): grid-refinement-stability is a VALIDITY property; range-dependence is a TYPE property. The
  meta-pattern ruled at the cheapest moment: the TYPING is what generalizes across σ-fibers/smear/
  conversation-layers (π_σ/π_grain/π_depth — one table); the FUSION instruments do NOT (three rules,
  three falsifiers) — no "scale framework" note; both sibling parks' evidence bars unchanged.
- **`dn-cross-strata-dreamer`** — Idea B / the firewall fork, resolved deliberately (ratification IS the
  parked human decision). Firewall stands as written; the dreamer is a correlator-family
  `interpreted`-tier client class needing an owner-declared read-exemption from ι_MR (per-client-class
  admissibility — authored⊕observed does NOT intrinsically collapse to ⊥). The pass's strongest result:
  the type system ALREADY gates it structurally — SliceError (multi-stratum point window needs a cut) +
  NoCommonClockError (no common materialized clock until CS-a) FORCE the pairwise per-stratum shape,
  re-deriving Track D's correlator from first principles. Gate chain G0–G4 recorded (fork → verdict
  taxonomy → Track D charter → cut discipline → mirror-value-first); ratification licenses NO build.
- **Economics:** run AS Fable on the untouched Fable weekly pool (was 0%); no builders spawned, no
  models resident, design-only session. Suite untouched (1287 on main; no code changed).
- **Next:** owner reviews oq-0027 (any subset may ratify). On dn-sigma-fibers ratification → /graduate
  (FB-1 first; FB-2 riders with finding-0086). /triage still owed (≈34 unswept + findings 0086/0089);
  the σ-sweep RUN still owed (oq-0024) — both for an opus/orchestrator session, NOT a Fable one.

### session-19 cont. (2026-07-16) — ⏱ the GLOBAL CLOCK finalized: `dn-global-event-clock` (draft #4, owner-extended charter)

- Owner extended the sanctioned pass to the global clock. **`dn-global-event-clock`** drafted — the
  designed RE-ENTRY of the ratified algebra's CS-a ("materialize N") + CS-b (antichain machinery) parks;
  the re-entry condition is genuinely met (dn-cross-strata-dreamer G3 is the named consumer, φ_coh the
  other). Ratifying the note IS the owner-blessed unpark; the ratified note is untouched (its §2.2
  anticipated exactly this completion).
- **The ruling:** N = (Ev, ≼), the DERIVED causal event poset — per-store total chains (g1; honest audit:
  versions/runledger/edges/derived/attestations carry order; the EVAL STORE records NO append order,
  keyed only — its events order via references alone), reads-from content-address edges (g2 — the built
  attestation auto-link `producers_of`, attestor.py:59-69, is the mechanized exemplar the spine
  generalizes), recorded program order (g3). Wall-time NEVER generates order (Law C4). Read-side
  derivation only: a write-side global sequencer is REJECTED STRUCTURALLY — it would couple sealed core
  and edge zone through a shared synchronous component when the async handoff is deliberately the only
  coupling (#1/#2). Soundness law: ≼_derived ⊆ ≼_true; derived concurrency over-approximates — hence
  cuts must be CERTIFIED: (commit ∧ trough-quiescence ∧ handoff-empty) frontier certificates (§2.4),
  typing Scope.cut and completing SLICE for non-repo strata. Clock laws C1 (monotone) / C2 (convex
  fibers — "commit is a RANGE" now a property test) / C3 (read-clocks borrow the observed write
  frontier) / C4. Proper time = maximal-chain length in N_s (causal-set frame; citations stay
  [FROM MEMORY — verify]).
- **What it completes on ratification+build (GC-1..GC-4):** T-meet totalizes over registered clocks
  (pullback intersections; NoCommonClockError narrows, never vanishes); CS-b antichain windows
  inhabited; (N,∗) the Sz.-Nagy dilation space becomes queryable (TRA R5); CS-f re-binning = possible
  as RE-MEASUREMENT only; N_s materializes = the parked prerequisite of the locally-clocked
  superconnection + DD-1. §2.6 draws the clock/Res(π) line once: a clock changes the denoted event set
  (scope-side); a resolution never does (result-side) — the capability-visibility test decides.
- Corrections recorded: temporal-clocks capsule's "op-seq is already the spine" gloss (op-seq is ONE
  store's chain — supersession-lifecycle §1); the eval-store no-order audit finding. Consumer wiring:
  dn-cross-strata-dreamer G3/XS-b updated in-draft to point here. oq-0027 updated (bundle of FOUR).
- Session-19 remains design-only: no code, no build, suite 1287 untouched, zero models resident.

### session-19 final (2026-07-16) — 🔭 THE STACK AUDIT: the temporal theory checked end-to-end against the spine; the recommended path pinned

- Owner asked for a final coherence pass (global clock × temporal algebra × local clocks × edge
  dynamics) + the recommended design/build/test path. Re-read IN FULL: dn-temporal-retrieval-algebra,
  dn-velocity-instruments, dn-temporal-geometry (all ratified), plus the built core/temporal/*. Result:
  **dn-global-event-clock §2.9** (eight audited interactions) + **§3.1** (the sequenced path).
- **Audit findings:** (1) TRA R5's Sz.-Nagy dilation scoped precisely — per-stratum chains embedding in
  (N,∗), not the global object itself; (2) the A7 apophenia discriminator's "version boundary voids the
  reading" becomes a mechanical WINDOW-PURITY spine predicate (GC-1 gives it an oracle); (3) the
  locally-clocked superconnection's admissibility (TG §2.4: clock field targets must be consistent
  cuts) = exactly GC-3's certified cuts — TG-a's prerequisite is GC-2+GC-3 + its data gate; (4)
  cut-pair windows generalize the ratified interval evaluation regime conservatively (σ-transports per
  stratum between frontiers — the same pairwise shape cross-strata forces); (5) the A-4 routing pin
  (ledgers→SQLite, analytics→DuckDB) IS the chain/chain-less g1 boundary; (6) **finding-0090 FILED**:
  dn-temporal-geometry §2.1's "proper time = per-stratum event count, exactly" holds per CHAIN not per
  stratum (DuckDB stores chain-less; version chains per-doc; strata span stores) — standing-erratum
  channel, ratified note untouched, corrected statement carried by GC-N6; (7) GC-N7 re-binning
  sharpened by velocity X2 (measurement-class iff event-exact; interpolation ⇒ a fit ⇒ R-gated); (8)
  **TRA's β-dial and TG's α-knob are Res(π) inhabitants** — five total (σ, β, α, grain, depth), two
  from RATIFIED notes; the capability-invisibility proof covers them verbatim; a β*-sweep is drivable
  by the existing sweep engine. dn-resolution-result-typing §2.5 table extended accordingly.
- **The recommended path (dn-global-event-clock §3.1):** ratify Res(π) → global-event-clock → σ-fibers
  → cross-strata (any subset safe). Build wave 1 (parallel, read-side): FB-1 + GC-1 + the ratified
  velocity measurement pair + the σ-sweep RUN (owner, any night — feeds select AND FB-1). Wave 2: GC-2
  (clock maps + N_s; C1/C2 property tests) + FB-2 (registry rows, Res-gated, 0086 riders). Wave 3:
  GC-3 (certified cuts; crossing-edge integrity) + GC-4 (T-meet completion; bit-identical-legal-meets
  falsifier) + FB-3 (the F9-validated gate). Wave 4 (each per its own gate): φ_coh clocked, R1
  velocity series, J/Φ + corpus temperature, demon-vs-source (owner-gated), β*-sweep; uuid-stable
  identity (TRA A6, owner-ruled HARD) before the diachronic reader / Track D.
- Session remains design-only; suite 1287 untouched. The four drafts + finding-0090 + the path are the
  session's complete deliverable set.

### session-19 coda (2026-07-16) — 🏛 ALL FOUR NOTES RATIFIED (owner hand-flips, in-session); oq-0027 ANSWERED

- Owner ruled in chat (2=Res(π) lean-yes with the "different processes visible at different
  resolutions" motivation; 3=cross-strata YES IN GENERALIZED FORM — dreamers grantable per-scope over
  non-authored strata combinations, bounding conditions unchanged; 4=global clock YES conditional on
  the clock-bridge preserving structure + zone separation — mapped to GC-4/GC-N1 falsifiers), the
  rulings were RECORDED into the drafts + oq-0027's answer field, and the owner then HAND-FLIPPED all
  four frontmatters draft→ratified: **dn-sigma-fibers, dn-resolution-result-typing,
  dn-cross-strata-dreamer, dn-global-event-clock — RATIFIED 2026-07-16.** All four now A8-immutable.
- Consistency check (owner asked; verdict recorded): rulings 2 and 4 are exactly the design's assumed
  strong branches (FB-2's Res-gate resolves strong; the item-4 condition IS the design's falsifier
  surface). Ruling 3 is consistent-and-BROADER: the draft's single exemption class generalizes to
  per-grant scope-parametric dreamers; folded pre-flip (the §2.1 owner-ruling block + XS-a per-grant +
  per-grant gate semantics: G1 any promotion crossing, G3 multi-stratum only, G2 the correlator, G4
  prudential). The one tension — "we can test it all" vs G4 mirror-value-first — reconciles via
  SHADOW-pipeline evaluation under eval isolation (scoped dreamers are testable as harness lanes
  without anything reaching the corpus; live grants still travel the gate chain).
- **Unlocked:** /graduate for FB-1..FB-3 (+ the Res[T]/res_under rider) and GC-1..GC-4 per
  dn-global-event-clock §3.1 (wave 1: FB-1 + GC-1 + the velocity pair; the σ-sweep RUN feeds FB-1).
  Cross-strata ratification licenses no build (G1–G4 front it). oq-0027 → ANSWERED.
- Next session (opus): /graduate wave 1 → owner blesses proposed→ready → build wave. /triage still
  owed (now incl. finding-0090).

### session-19 graduation (2026-07-16) — 📐 EIGHT PLANS MINTED (bp-050..bp-057, all `proposed`) — the ratified quartet decomposed

- /graduate performed in-session while the full design context was loaded (fresh-agent test: the next
  orchestrator proceeds from artifacts alone). All plans `proposed` — **`proposed→ready` blessing is
  the owner's, by hand, per plan.** Wave structure (disjoint write_scopes within each wave):
  - **Wave 1 (parallel):** bp-050 `fibers-consumer` (FB-1; 240k est), bp-051 `spine-skeleton` (GC-1;
    240k), bp-052 `velocity-pair` (dn-velocity-instruments §3.1; 180k).
  - **Wave 2 (parallel, after deps):** bp-053 `clock-maps` (GC-2 + N_s; dep bp-051; 200k), bp-054
    `res-typing-registry` (FB-2: Res[T]/res_under + sigma_persistence.* + structural_axes.* — RESOLVES
    finding-0086; dep bp-050; 180k).
  - **Wave 3 (parallel):** bp-055 `certified-cuts` (GC-3; dep bp-053; Scope.cut UNTOUCHED — the
    CertifiedCut rides the opaque Hashable, keeping scopes disjoint; 180k), bp-056 `tmeet-completion`
    (GC-4; dep bp-053; the ClockAtlas Protocol seam keeps core/scope.py pure-core; atlas impl in NEW
    core/temporal/atlas.py for parallel-safety; HIGHEST scrutiny — merge last, orchestrator xhigh
    line-by-line; 200k), bp-057 `sigma-gate` (FB-3; deps bp-050+bp-054; SHIPS ONLY IF the three F9
    criteria hold — park-and-record is a sanctioned outcome; 220k).
- **Test spine per wave:** every plan carries acceptance + named falsifiers; integrity teeth grow by
  spine-acyclicity (051), clock-laws-on-real-stores (053), cut-soundness (055); bp-056's cardinal
  falsifier = tests/unit/test_scope.py green WITH ZERO EDITS (bit-identical legal meets — the owner's
  ratification condition, executable). 5-leg gate after every merge; suite grows from 1287.
- **Tier ruling for the wave (owner proposed opus/xhigh; orchestrator concurs with refinement):**
  orchestrator session opus/xhigh (supervision + merge scrutiny — the 0.61-0.67× pattern); delegated
  BUILDERS opus at standard effort (well-pinned plans don't need xhigh workers); bp-056's merge review
  is the one xhigh-mandatory scrutiny point. PRE-FLIGHT: owner relays /usage; pad Σ-estimates ~1.6×;
  wave 1 ≈ 660k est ⇒ ~1.06M padded — start after the Jul-17 weekly reset for a full allowance.
- Total estimate: 8 plans, ~1.62M tokens raw (≈2.6M padded) across 3 waves — 2-3 orchestrator sessions.

### session-19 seal (2026-07-16) — 💰 economics + WAVE 1 BLESSED (bp-050/051/052 → ready, owner hand-flips)

- **Owner blessed wave 1 to `ready`** (bp-050 fibers-consumer · bp-051 spine-skeleton · bp-052
  velocity-pair — hand-flips observed on disk). Waves 2/3 (bp-053..057) remain `proposed`.
- **Session-19 cost (Fable, the sanctioned design pass, owner-relayed /usage):** **$47.19**
  (204.7k output / 27.9k input / 28.0M cache-read), wall 2h13m. Session 14%, week (all) 7%→12%
  (+5pt), **Fable 0%→9%**, **credits UNCHANGED $122.94/$150 (81%)** — the design pass drew the
  weekly pools only, fourth confirmation of the pool split. Deliverables per dollar: 4 ratified
  design notes + 1 finding + 8 build plans + oq-0027 closed + the full temporal-stack audit.
- **Pre-flight snapshot for the wave-1 orchestrator:** week 12% / Fable 9%, BOTH reset Jul 17
  8pm ET (tomorrow). Wave 1 est 660k ⇒ ~1.06M padded (1.6×) — comfortably inside a fresh week;
  starting after the reset is the clean play, before it is also viable at 12%.
- Next session: OPUS/xhigh orchestrator, delegated wave-1 builders per the resume brief.

### session-20 (2026-07-16) — WAVE 1 EXECUTION: bp-050 + bp-052 merged & sealed; bp-051 in flight

- **Pre-flight /usage (owner-relayed at start):** session 16% · week (all) **12%** · Fable 10% ·
  credits 81% ($122.94/$150). Wave draws the weekly pool (ample) — gate passed, spawned all three.
- **Spawned 3 delegated builders**, opus, each in its own isolated worktree, disjoint write_scope
  (verified: no file overlap across bp-050/051/052). Full contract inline (ratified note cite-only,
  4-file scope, 5-leg gate, journal, findings routing, no-blessing).
- **bp-050 `fibers-consumer` → COMPLETE.** Merged `8b56998` (branch had `69e673f`). Diff scope-clean
  (writes eval store only via one `put()`; no network). 5-leg green on main: ruff · mypy(203) ·
  argless mypy **69** · type_gate · pytest 1302p/9s. Actual **217k tok / 0.90×** est, 73 tools, ~23m.
  No findings (§3 grounding held).
- **bp-052 `velocity-pair` → COMPLETE.** Merged `6f02d09` (3 commits). Consumes core/complex via
  hodge public surface only (isolation intact); no store/model/network. 5-leg green: mypy(204) ·
  argless **69** · pytest 1315p/9s. Actual **175k tok / 0.97×** est, 102 tools, ~25m. Filed
  **finding-0091** (`math`, routed to design): dn-velocity-instruments §2.2(a) left the
  cross-edge-space subspace-angle construction implicit; builder resolved via union-edge-space
  embedding (standard, all falsifiers green) — note-vs-code reconciliation, batch with finding-0090.
- **bp-051 `spine-skeleton` — still running** (GC-1; the keystone for the temporal-scaling roadmap
  the owner raised this session — event-sourced snapshots vs O(N×T) materialization). Merge on land.
- **Suite 1287 → 1315** (bp-050 +14, bp-052 +13). Argless mypy baseline **69 HELD** through both.
- **Dollars/session-deltas: pending** owner end-of-session /usage relay → fill the seals' `dollars`
  fields + wave-level economics in the self-rewrite.
- Next: merge+seal bp-051 on completion; waves 2/3 (bp-053..057) await owner `proposed→ready`.

**bp-051 update — CAUGHT RED, FIXED, sealed COMPLETE.** Initial merge `0a3d468` passed 4/5 legs but
the Item-3 acyclicity tooth FAILED against the LIVE corpus (`SpineCycleError`, 1467-event SCC) — a
defect the isolated worktree structurally could not catch (no `data/`). Diagnosed on main
(scratchpad/spine_cycle_diag.py): g2 minted attestation `output_hashes` into `produced_by`, so a shared
corpus/config digest (both input & output of many attestations) created producer↔consumer edges both
ways → the whole attestation store collapsed to one SCC, violating §8 `≼_derived ⊆ ≼_true`. Re-engaged
the same builder (context intact) with the precise diagnosis + a synthetic-regression spec it could
verify in-worktree. Fix `14b3140` (merged `2c541db`): an attestation produces ONLY its own id (it is a
proof-layer record, not the minter of its outputs — the store event is); att→att order = `derived_from_ids`
(§2.8-5, acyclic); output_hashes still display as `refs`; cross-store provenance preserved. **LIVE-corpus
acyclicity re-verified PASS**; forged-cycle tooth RETARGETED to mutual `derived_from_ids` (still bites);
full 5-leg green (suite 1315→**1337**; argless 69 held). `finding-0092` filed RESOLVED (spec-fidelity;
minter mis-attribution, NOT a note errata — §2.2's "minted"=unique write-once mint; forward rule for
GC-2/GC-3: g2 fires only from an identifier's unique minter). Cost **304840 tok / 1.27×** (the rework).
- **Process lesson:** an integrity acceptance needing live `data/` cannot be verified in a builder's
  worktree — run it on main (ideally a scratch integration BEFORE the main merge). Fold into delegate skill.
- **WAVE 1 COMPLETE:** bp-050 ✅ · bp-051 ✅ (via fix) · bp-052 ✅ — all sealed, main green, suite 1337.

**Wave 2 launched** (owner blessed bp-053..057 → ready, recorded `97239b8`; brainstorm
`retrieval-and-temporal-scaling` captured `d355750`). Pre-flight: week 17%, session 63%, credits 81%
unchanged (5th pool-split confirmation).
- **bp-054 `res-typing-registry` → COMPLETE.** Merged `4ec4cdc`. `Res[T]`/`res_under`/`res_comparable`
  additive to core/scope.py (proven: test_scope.py 28 passed UNCHANGED, 2-hunk diff, no capability symbol
  moved) + sigma_persistence.* (Res(sigma)) & structural_axes.* (Inv) registry rows. 5-leg green (mypy
  205; argless 69; suite 1337→**1349**). Actual **137k / 0.76×**. RESOLVES **finding-0086** (structural_axes
  registry gap) and files+resolves **finding-0093** (the plan's "import FB-1 constants" pin closes a
  circular import registry→fibers→shadow→registry; builder registered literals + a fail-closed name-
  agreement test — same no-drift guarantee, cycle-free; optional future tidy noted, not owed).
- **bp-053 `clock-maps` — still running** (extends spine.py; its live-data integrity test I must verify on
  main myself, per the bp-051 lesson). Merge on land.
- Both wave-2 builders' worktrees were cut from the session baseline `4b3ace7` (pre-wave-1-merge), so each
  ff-merged current main to pick up its dependency (bp-054 needed bp-050's fibers.py) before building —
  clean, disjoint. bp-053 must do the same to get bp-051's merged spine.py: VERIFY at its merge.
- **bp-053 `clock-maps` → COMPLETE.** Merged `0c1ea0c` (it ff-merged main to extend bp-051's fixed
  spine.py — verified). p_κ + C-laws C1–C4 + N_s + proper_time (finding-0090 discipline). Applied the
  bp-051 lesson: verified LIVE-corpus clock-laws (7/7: commit-range/N_s/proper_time on real chains) +
  re-ran bp-051 acyclicity — ALL PASS — in the uncommitted merge state BEFORE finalizing (git-merge-abort
  was the safety net). 5-leg green (suite 1349→**1375**; argless 69). Actual **205k / 1.03×**.
  - **Finding-number collision handled:** bp-053 and bp-054 both minted `finding-0093` from the same
    `4b3ace7` baseline. bp-054's merged first (circular-import); bp-053's renumbered to **finding-0094**
    (add/add conflict resolved keep-ours; journal refs fixed).
  - **finding-0094 (spec-fidelity, RESOLVED):** the commit clock is injection-based — no spine-enumerated
    store carries a commit SHA and sealed-core forbids core/→git (non-neg #1/#2), so the "against ACTUAL
    git history" check is a named OPS-SIDE follow-up (re-entry: first Rate(commit)/commit-cut consumer),
    NOT under-delivery. p_commit is honestly PARTIAL; N_s + proper_time fully live-verified.
- **WAVE 2 COMPLETE:** bp-053 ✅ · bp-054 ✅ — sealed, main green, suite 1375, argless 69 held.
- **NEXT = WAVE 3 (fresh session, per context-economy):** bp-055 certified-cuts (dep bp-053 ✅),
  bp-056 tmeet-completion (dep bp-053 ✅; HIGHEST scrutiny — merge LAST, xhigh line-by-line; falsifier
  test_scope.py green with ZERO edits), bp-057 sigma-gate (deps bp-050✅+bp-054✅; park-and-record if the
  three F9 criteria don't hold). All deps now satisfied; all three blessed `ready` (97239b8).

### session-20 economics (2026-07-16) — 💰 waves 1+2, owner-relayed end-of-session /usage

- **Session cost: $74.07** (all opus: 58.0k in / 791.0k out / 73.7M cache-read / 2.4M cache-write),
  wall 1h54m / API 3h03m, 5150 lines added / 318 removed.
- **Week (all models) 12%→19% (+7pt)** for the whole build wave-1+2 (5 plans + the bp-051 defect rework +
  all merges/seals + the brainstorm). **Fable 10% UNCHANGED** (no fable — a pure opus build session).
  **Credits 81% UNCHANGED ($122.94/$150)** — 6th confirmation the build wave draws the WEEKLY pool only.
- **Per-plan (harness tokens / ratio):** bp-050 217k/0.90× · bp-051 305k/**1.27×** · bp-052 175k/0.97× ·
  bp-053 205k/1.03× · bp-054 137k/0.76×. **Mean ≈ 0.99×** — the wave came in essentially AT estimate:
  bp-051's rework (the live-data defect) was offset by the four well-pinned plans (0.76–1.03×). Validates
  [[seal-cost-fields]] — the ratio tracks pinning quality + rework.
- **Deliverables/dollar:** 5 plans through the full pipeline (1 defect caught on live data + fixed), 4
  findings filed (0091/0092/0093/0094) + 2 resolved (0086/0093), 1 brainstorm captured, every merge
  gated + sealed + pushed. The per-plan seals' `dollars` defer here — this block is the authoritative figure.
- **Session hit 83%** at wrap — stopped at the wave-2 boundary (context-economy); wave 3 handed to a fresh
  session via the rewritten resume brief.

### session-21 (2026-07-16) — WAVE 3 START: bp-055 merged & sealed; PAUSED (session window maxed, credits low)

- **bp-055 (certified-cuts, GC-3) MERGED `d95810f` + SEALED `complete`.** `CertifiedCut` + the three
  certificates (commit / trough-quiescent / handoff-empty) + composition + the crossing-edge soundness
  tooth, all additive on the spine; `core/scope.py` UNTOUCHED (the pin held — CertifiedCut rides the opaque
  `cut`). 5-leg green on main (ruff · mypy 205 · **argless 69** · type_gate · pytest **1398p/7s**, suite
  1375→1398). **Live-data cut-soundness ran on real `data/` in the uncommitted merge state — both
  `*_on_real_stores` legs PASSED** (the bp-051 discipline applied). **220k harness tokens / 1.22×** (a live-
  data tooth + cross-strata composition, slightly over the well-pinned band). **finding-0095**
  (spec-fidelity, RESOLVED): the stratum→certificate map (`_STRATUM_CERTIFICATES`); the §10 trough
  contingency resolved **WITHOUT a park** — the scheduler exposes readable quiescence via `JobQueue.counts()`
  (injected as `TroughState`, since core can't import scheduler — a cycle). No design/math/direction findings.
- **INCIDENT + RECOVERY (worktree corruption): bp-056/bp-057 died on transient `Connection closed
  mid-response` API drops during worktree setup.** Resuming them via `SendMessage` re-ran setup into a
  corrupted state: bp-056's branch got checked out in the MAIN dir (`main` was checked out nowhere), bp-057
  got no worktree at all. **No work lost** (both were only reading; main dir was clean, zero commits on the
  stray branch). Recovery: stopped both, `git switch main` in the main dir, deleted the tangled empty branch,
  pruned. **LESSON (recorded for the delegate skill): a worktree-isolated agent that dies DURING worktree
  setup must be RE-SPAWNED FRESH, never `SendMessage`-resumed** — resume corrupts the half-built worktree.
- **Owner directive mid-session: serialize to ONE active builder at a time** (the double-drop happened at 3
  concurrent). Re-spawned bp-056 fresh (clean worktree, verified), then stopped it to honor serial mode;
  bp-055 ran solo to completion. bp-056/bp-057 remain `ready`, unbuilt.
- **Economics (owner-relayed /usage at pause):** session cost **$21.18** (opus; incl. the aborted bp-056/057
  spawns + worktree recovery + bp-055's merge/gate/seal). **5h session window hit 100% (maxed)** → resets
  8:19pm ET. **Week (all) 19%→20% (+1pt).** Fable 10% unchanged. **Credits 81%→85% (+$5.61,
  $122.94→$128.55)** — this BREAKS session-20's "credits unchanged" pattern *precisely because* the session
  window maxed: once the 5h subscription allowance is exhausted, overflow spills to the $150 credit pool.
  A NEW economic datum — the weekly-pool-only rule holds only while the session window has headroom.
- **PAUSED after the bp-055 merge per owner** (credits low + session maxed). bp-056 (merge LAST, xhigh
  scope.py review) + bp-057 (conditional ship / park-and-record) handed to a fresh session via the rewritten
  resume brief — best resumed after the 8:19pm session reset, ONE builder at a time.

### session-21 cont. (2026-07-17) — 🏁 WAVE 3 COMPLETE: bp-057 + bp-056 merged & sealed — ALL 8 TEMPORAL-QUARTET PLANS DONE

- **Session window reset to 0% → owner said "spawn both in parallel, keep building."** Re-spawned bp-057 +
  bp-056 as PARALLEL worktree builders off `61fdedb` (disjoint scopes — eval/ vs core/scope.py+atlas.py). Both
  got clean isolated worktrees (the session-21 corruption was resume-only, not fresh-spawn). No drops this time.
- **bp-057 (sigma-gate, FB-3) MERGED `0742d09` + SEALED — SHIPS.** The conditional gate validated GENUINELY:
  (i) noise SETTLED-rate **0.0**, (ii) planted claims reach SETTLED, (iii) tiered precision **1.0 > 0.667**
  best-single-σ baseline — all three §2.5 criteria hold, no θ loosened. `assign_tiers`/`hunch_section` over
  bp-050's ClaimFiber; I1 asserted structurally (AST-proven: no store mutator, no pers×confidence fusion,
  RETAINED never surfaced). **162k / 0.74×.** No finding (reserved 0097 unused — SHIP). 2 spec-fidelity reads
  journaled (best-single-σ = max-over-σ; `sigma_gate.validation.*` registration deferred to E6). Suite →1417.
- **bp-056 (tmeet-completion, GC-4) MERGED `d467258` + SEALED — the highest-scrutiny plan, conservative.**
  Cross-clock T-meet via an injectable `ClockAtlas` Protocol in scope.py + concrete `SpineAtlas` in the NEW
  `core/temporal/atlas.py`. **Orchestrator line-by-line review at xhigh CONFIRMED conservativeness:** the
  original `meet` RAISED on EVERY cross-clock pair (scope.py:337 no-refinement + :345 comparable-but-retrieval-
  math) — so the only previously-legal meets are same-clock, and the atlas branch (inserted before the raises)
  gives values ONLY on the former-error path. **Cardinal falsifier MET: `test_scope.py` 28 passed with ZERO
  edits** on the merged state; scope.py stays pure-core (Protocol seam, imports no store/atlas); N-window =
  `interval(token,token)` avoids the SLICE rule; `Window` grammar not loosened. **200k / 1.00×** (exactly at
  estimate). No finding (reserved 0096 unused). Suite 1417→**1430**; argless mypy **69** held throughout.
- **Wave-3 economics:** 2 plans, both delegated opus, both clean-merge (no rework). Per-plan: bp-055 220k/1.22×
  (session-21) · bp-057 162k/0.74× · bp-056 200k/1.00×. **Mean over the 3 wave-3 plans ≈ 0.99×** — dead-on
  estimate, validating [[seal-cost-fields]] (well-pinned plans track ~1×). Every merge gated + sealed + pushed;
  ZERO findings from wave 3 (both plans' reserved numbers went unused — the plans were pinned tightly enough
  that no design/math/direction question arose). Dollars: `pending` in the seals → owner end-of-session /usage.
- **THE RATIFIED TEMPORAL QUARTET IS COMPLETE (bp-050..bp-057, 8 plans):** GC-1 spine → GC-2 clock maps →
  GC-3 certified cuts → GC-4 T-meet completion; FB-1 fibers → FB-2 registry → FB-3 σ-gate; + velocity-pair.
  **Next lead (per the retired resume brief's self-rewrite trigger): /triage (finding-0090/0091 → owner batch)
  + the σ-sweep RUN + (owner-gated) the wave-4 instruments** (dn-global-event-clock §3.1). The
  retrieval/temporal-scaling brainstorm (`d355750`) is now ripe to graduate into a design note.

## 2026-07-17 (session 22, FABLE/xhigh) — ⭐ THE DESIGN SESSION: two notes RATIFIED; the experiment is the next lead

- **Owner switched the session to fable/xhigh for a design arc; docs-only (zero code; suite stays 1430).**
  Products, in chain order: **3 brainstorm capsules** (`self-mapping-the-palace` — the teleology: the palace
  as the owner's self-map, his CV↔architecture correspondence; `conductivity-and-reasoning-chains` — the four
  connectivity questions + the arc addendum; the retrieval-scaling capsule stands adjacent, deliberately
  separate) → **the C1–C7 fable pass** (`conductivity-and-reasoning-chains-fable-pass.md`: σ*/MST ultrametric,
  honest (σ,t) conductance w/ the von-Luxburg protective result, metric-vs-gauge split, well-formed argument
  paths, the FORCED-HELIX theorem reconciled w/ magnetic Q3/Q4/Q5/Q6, arc search; §9 errata) → **two design
  notes drafted, adversarially passed (8 wrinkles fixed pre-ratification), and OWNER-RATIFIED** (`d932670`):
  - **dn-connectivity-instruments** (CN-1..CN-7): the 4-plan instrument tranche; CN-4 owner-refined mid-draft
    (churn = change of measure; the DEPTH BUDGET `N(W)=Σ N_s(W)` — proper time bounds chain length; D1
    RETIRED — signs by circuit law, only magnitudes sweepable); uuid-identity registered as 3-consumer.
  - **dn-sigma-sweep-experiment** (SE-1..SE-4, V1..V5): the pre-registered protocol for σ-sweep RUN 1;
    **ratification = FREEZING** (the bless commit `d932670` IS the frozen pre-registration run 1 must cite);
    V2 = certified-cut snapshot indexing (bp-055's production debut); SE-3 = the owner as BLINDED judge;
    licenses ONE thin wiring plan (~100–120k) + the owner-fired RUN (selfmod propose-only).
- **Sequencing decided (owner-confirmed): EXPERIMENT FIRST** — data before instruments; risk discovery
  (SF-a flicker, corpus-size floor) before the ~730k connectivity wave; the tranche graduates after run-1
  findings + a fresh weekly pool. **Handoff → a new OPUS/high session:** /graduate the wiring plan (bp-058),
  owner blesses, build, pre-flight V1–V5, supervise run 1, analyze per the FROZEN rules only, dispose oq-0024.
- **Economics:** dollars for wave 3 + this fable session remain `pending` in the seals — fill from the next
  owner /usage relay (weekly reset was Jul 17 ~8pm ET; credits last read 86%/$130.23). Finding numbers:
  0096/0097 reserved in wave 3 went UNUSED — **next free = 0096**. /triage (0090/0091 → owner batch) still owed.

## 2026-07-17 (session 23, OPUS/high) — THE EXPERIMENT SESSION: bp-058 graduated + blessed; /triage swept; self-build underway

- **Re-read the FROZEN pre-registration §2 in full first** (owner's standing instruction: the note at
  `d932670` is the authority, not a paraphrase). `/usage` relayed: weekly pool **27% used** (resets tonight
  ~8pm ET), credits **86% / $130.23 of $150** (resets Aug 1) — budget gate PASS for bp-058 (~150k).
- **/graduate dn-sigma-sweep-experiment → bp-058** (`sigma-sweep-experiment-wiring`, `69b5985` proposed):
  the ONE thin wiring item §3 licenses, three serial sub-items — (1) control battery (V3 as one GREEN/RED
  invocation, reuses bp-057 F9 fixtures verbatim); (2) blind-sample generator (seeded, labels SEALED to a
  separate file, SE-3); (3) composite report assembler (§2.3 contract + the V1–V5 evidence block incl. the
  certified cut). Write scope `eval/harness/experiment.py` + `scripts/experiment.py` + 3 unit tests; NO core;
  all consumed interfaces built + pinned inline §6. Est opus/150k. One grounded decision flagged (tier-
  stability partition, §3 Q6 / §11). Blast radius: all read-only sensing (writes only `data/reports/`).
- **Owner blessed bp-058 `proposed → ready` by hand** (recorded in the bless commit) AND directed
  **self-build with supervision here** (not a spawned builder — owner wants to keep tabs on the experiment).
- **/triage** (owed sweep): findings **0090 + 0091** (both `math`, ratified-note errata, non-blocking, no
  code implied) flipped `open → routed` and batched into **oq-0028** (annotate-by-hand vs standing-erratum,
  the oq-0025/26 pattern). No newly-complete plans to seal (bp-055/056/057 already sealed; their `dollars`
  stay pending — this relay is a cumulative snapshot, not a wave-3 delta, so not fabricated). Book: still
  unscaffolded (no SYNC.md) — book debt growing (harness + connectivity chapters), /scribe offered.
- **Next:** build bp-058 items 1→2→3 here; 5-leg gate; seal; then pre-flight V1–V5; owner fires run 1;
  analyze per FROZEN rules; dispose oq-0024. Next free finding = **0096** (reserve on build).

## 2026-07-17 (session 23 cont.) — bp-058 COMPLETE: the σ-sweep experiment wiring is built + sealed

- **Built + sealed bp-058** (`c1de27c`, self-build in the orchestrator session, owner-directed
  supervision). Three items, all closed: **(1) V3 control battery** — `eval/harness/experiment.py`
  `run_control_battery` lifts `test_sigma_gate._compute_validation` into the harness;
  `scripts/experiment.py controls` = one GREEN/RED invocation (non-zero exit on RED). **(2) SE-3
  blind-sample generator** — `generate_blind_sample` (seeded, stratified 8/8/8, UNLABELED
  presentation + SEALED labels file). **(3) §2.3 composite report assembler** — `assemble_composite`
  renders the V1–V5 evidence block (incl. the certified cut), SE-1 selection, SE-2 fibers, SE-3
  occupancy/stability, control outcomes, blind cross-tab; registered names only; writes only
  `data/reports/`. Model-free, deterministic, read-only over stores; no core.
- **5-leg gate GREEN:** ruff · mypy targeted 0 · argless 69 · type_gate 11 · pytest **1436p/0f** (+16
  new). End-to-end verified: `controls`→GREEN, `blind-sample`→empty-ledger guard, `report`→6-section
  composite written (V1+V3 populated pre-run; honest previews + coverage notes for V2/V4/SE-1/SE-2/E4).
- **One journaled design refinement** (not a spec change): the assembler takes a pre-built E4 `Report`
  rather than raw stores — cleaner + testable in-memory; §2.3 content identical.
- **Economics:** session $26.30, opus output 146.7k tokens (~at the 150k estimate; ratio 0.98,
  well-pinned); drew the WEEKLY allowance (→28%), NOT the $150 credit pool ($130.23 unchanged, resets
  Aug 1). Session pool 49% (resets 2:50pm ET). Finding-0096 reserved but unused (clean build).
- **NEXT (the experiment path, gated on the owner):** V1–V5 pre-flight → owner flips `[selfmod]
  enabled=true, unattended=false` (owner-by-hand, config/defaults.toml:240) → owner fires
  `uv run scripts/sweep.py config/sweeps/dreamer-sigma-ab.toml` → analyze STRICTLY per FROZEN §2.2
  (SE-1 disposes oq-0024) → assemble the composite → seal the run journal. Connectivity tranche still
  DEFERRED until run-1 findings.

## 2026-07-17 (session 23 cont.) — σ-sweep RUN 1 executed + SEALED; cross-strata direction captured

- **RAN + SEALED σ-sweep run 1** (owner-fired, pre-registration `d932670`). Quiesced the daemon
  (`palace down` — bootout outlasts KeepAlive, finding-0066 mechanism) for a valid V2 cut; brought it
  back `up` after. V1–V5 ALL hold (V2 = bp-055's debut: 13-chain mirror cut, COMMIT-certified at
  `214eaf4`; V3 controls GREEN; V4 bit-wise determinism; V5 propose-only, owner-flipped then reverted).
- **Result:** oq-0024 **RETIRED** (SE-1 rule (b): golden_recall flat=1.0 across all 21 σ-cells,
  default 0.62 stands; proposal #1 [0.62→0.65] declined). **finding-0096** = the flatness is objective
  SATURATION at 13-doc scale, not σ-invariance. SE-2 positive: dream_v2 fibers non-degenerate (n=32,
  real multiscale structure) — the instrument works. SE-3: apophenia guard holds but discrimination
  unproven at scale (**finding-0098**). **finding-0097** = SE-1 (a)/(b) flat-curve precedence wrinkle.
  Composite report: `data/reports/2026-07-17-sigma-run1/` (gitignored).
- **Owner direction → cross-strata substrate sweep** (`docs/brainstorms/cross-strata-substrate-sweep.md`):
  run 1's convergent finding (13-doc mirror too small) motivates widening to the whole substrate
  (notes+docs+code+comments+chats+observed). ARCHITECTURE pinned: this is the CROSS-STRATA CORRELATOR
  (Track D, ratified generalized), NOT the mirror dreamer (firewall/Invariant 6 preserved). Two bands:
  public (docs/code/comments — firewall-safe, near-term) vs private (chats/observed — scoped grant).
- **NEXT (owner: "build out what we've already designed"):** graduate + build the RATIFIED
  `dn-connectivity-instruments` tranche (items 1–3; item 4 gated on uuid-identity) — the phase-B
  re-analysis instruments for exactly this kind of run. Weekly pool 29%; but session pool 57% + high
  context ⇒ the tranche graduation is a FRESH-session task (context economy).

## 2026-07-17 (session 24) — GRADUATED the connectivity-instruments tranche → 4 proposed plans (bp-059..062)

- **/graduate `dn-connectivity-instruments`** (RATIFIED, CN-1..CN-7) → four `proposed`, eval-side, read-side,
  model-free build plans with disjoint write_scopes. Grounded pass (investigate→reconcile→plan) against the
  six built substrate modules (Explore-assisted); each plan pins its consumed signatures inline with
  `path:line` citations. Next plan id now **bp-063**.
  - **bp-059** (σ*/MST, the keystone; no deps) — `eval/harness/connectivity.py`; the shared CN-1 scaffolding
    (ConnIndex/ConnEvidence/latest-cut gate) the family imports. ~180k opus.
  - **bp-060** (the (σ,t) conductance profile + churn change-of-measure + reconnection) — deps bp-059.
    Signs are LAW (D1 retired); `CONDUCTANCE_THRESH` magnitudes ship at 0; χ_s + depth-budget from the spine.
    ~200k opus.
  - **bp-061** (type-checked bridges + bidirectional arc search) — deps bp-059+bp-060. Node→scope =
    MirrorView.SCOPE ⊓ spine-event TimeScope (Σ trivial, atlas T-meet is the live refusal axis). ~200k opus.
  - **bp-062** (helix detector) — **GATED on uuid-identity** (D3). Item 10 (synthetic detector) buildable now;
    item 11 (real-corpus π) waits behind the gate. ~180k opus.
- **One load-bearing grounding fact, carried in all four:** `MirrorView` has NO cut-restriction surface
  (`core/mirror.py:96-105`); `MirrorGraph.build` takes no cut. v1 pins to the LATEST certified cut
  (`spine.cut_at`), recorded in evidence; historical cut-restriction is a parked `core/` prerequisite.
- **Run-1 findings honored:** finding-0096 (golden_recall saturation) ⇒ NO recall coupling — every plan's
  falsifiers are structural (ultrametric inequality, Rayleigh monotonicity, forced-helix theorem), not recall.
- **NEXT = owner blessing gate (oq-0029):** owner blesses `proposed → ready` by hand, item-by-item, records a
  `bless(...)` commit; bp-059 is the natural first (the keystone). Then `/build` each ready plan (5-leg gate,
  seal w/ cost.actual). No agent flips readiness (gate-guard + Stop-gate audit). Cross-strata σ-sweep design
  note still DEFERRED (these instruments are its phase-B re-analysis layer — build first).

## 2026-07-17 (session 24 cont., Fable/xhigh) — graph-at-a-past-cut design pass; bp-059 BLESSED ready

- **bp-059 blessed `proposed → ready` by the owner** (by hand; recorded `a5da95f`). bp-060/061/062 remain
  `proposed` (oq-0029). Build starts next session (OPUS).
- **Design pass (owner-chartered): the graph as of a past cut** → captured
  `docs/brainstorms/graph-at-a-past-cut.md` (D1–D9, O1–O4). The headline results, all grounded/checked:
  (1) **retention is already constitutional** — frontier → versions chain (doc_id, version_seq → digest,
  append-only) → immutable rawstore (digest → bytes) → re-embed (anticipated at `core/ingest/embed.py:6`):
  retro reconstruction is a pure function of retained data, EVAL-SIDE via the `RowSource` Protocol seam
  (`core/mirror.py:54-60`) — no core change, no git archaeology; (2) **three gauges** (anchored / retro /
  archival — declare, never conflate); the ANCHORED memory curve σ*(A,B;c) needs only versions-chain
  membership + bp-059's module — the cheap follow-on; (3) **conditional monotonicity** numerically checked
  (growth ⇒ σ*/conductance non-decreasing; an edit can drop σ* .7071→0 — a drop CERTIFIES an edit/tombstone,
  attributable); (4) **note-grain identity across cuts is already solved** (doc_id; uuid-identity gates only
  claim grain); (5) **wall-clock = bookmarks, not order** (owner q): annotations already exist (versions.at,
  committer dates); only the ambiguity-widening wall-range→cut-interval RESOLVER is new; Law C4 intact.
- **Findings:** **0099** (math — CN-3's "rise requires new edges" is the unweighted shadow; attribution =
  weight-increased edges incl. edits; **bp-060 item 6/§8 amended pre-blessing** with the banner + an
  edit-rise synthetic case) · **0100** (design — corrects bp-059 §11's re-entry prerequisite from "a core/
  plan" to an eval-side adapter; no change to the blessed plan itself). Next finding = **0101**.
- **NEXT:** /clear → fresh OPUS session → `/build bp-059`. After the tranche: graduate the
  graph-at-a-past-cut capture into a design note (memory curve v1 = candidate first follow-on plan).

## 2026-07-17 (session 24 close) — dn-chat-sensor composed AND RATIFIED; README mission reframe

- **`dn-chat-sensor` composed (Fable/xhigh) and owner-RATIFIED by hand in-session** (rode into `4ce96d2`;
  provenance recorded in the empty bless commit). Decides CS-1..CS-6: verbatim rawstore retention (the
  CLI transcript source is EPHEMERAL — 103 files today, pruned by retention policy); ALL rows OBSERVED
  (never-automatic promotion; `/capture` stays the promotion path; the typed `promote`/OwnerVerdict stub
  registered as the future seam); utterance-grain extraction with structural tool-strip (anti-apophenia +
  secret hygiene); per-session g1 chains, stratum observed, session-close cut certificates;
  correlator-only reader (Invariant 6 untouched); formalization-lag designed, TRIPLE-GATED. Both warrant
  RQs decided. §3 tranche graduatable on owner sequencing; the LEAD remains /build bp-059.
- **README reframed (owner-directed, `38a499c`):** "Why it exists" — the living thought experiment;
  intuition bounded by math, made representable/constructable, self-validated (the guardrails are the
  kiln); frontier → the temporal-connectivity family entering build; recursion gains the chat-sensor turn.
- Owner memory updated: the project is art-first; excitement is the point.

## 2026-07-17 (session 25, OPUS) — bp-059 σ*/MST BUILT & sealed (the keystone of the connectivity family)

- **`/build bp-059` COMPLETE** — in-session opus self-build; `ready → in-progress → complete`.
  New `eval/harness/connectivity.py` (the CN-1 scaffolding + CN-2 σ*/MST) + unit tests + quality battery.
  Status flipped `complete`; sealed with `cost.actual` (77.9k opus output, ratio **0.43** — very
  well-pinned; $9.79 session; weekly 31%→32%, credit pool unchanged → a build wave draws the weekly).
- **The load-bearing surface for bp-060/061/062 landed:** `ConnIndex(grid, cut)` (declares σ* uses
  (grid, cut), no t), `ConnEvidence(grid, base_fingerprint, cut_fingerprint)` (FibersEvidence pattern
  verbatim), `acquire_mirror_cut(spine)` (latest-cut gate, `CutCertificateError` propagates, CN-1
  crossing-edge tooth), `build_max_spanning_tree` / `sigma_star(forest, a, b, *, grid)` (grid-snapped
  bottleneck + realizing MST chain; forest when disconnected), `run_connectivity(...)` (idempotent
  keyed `sigma_star.*` readings). Registration of the metric names deferred (fibers precedent — a
  bp-054-style companion; `registry.py` out of scope).
- **Both CN-2 falsifiers pass:** ultrametric inequality on real triples + **MST ≡ union-find** on every
  pair (independent oracle test-side). Grid-relativity observable (bridged two-cluster fixture: cross
  pair connects at loose grid, "not connected within grid" at tight). σ* kept DECOUPLED from
  golden_recall (finding-0096 honored). Module reads no clock (Law C4).
- **5-leg gate GREEN** (diff vs merge-base c14d6a4, legs run separately): ruff clean · mypy targeted 0 ·
  argless mypy **69** (baseline held) · type_gate 11p · pytest **1454p/4s/0f** (+16 new: 10 unit + 6 quality).
- **No findings filed** — clean build; 3 design decisions journaled (corpus_ref = sorted-digest hash;
  SigmaStar kept minimal per §6 pin, pre-snap bottleneck internal; `_SNAP_EPS`), none rose to a finding.
- **NEXT:** owner blesses **bp-060** (as amended per finding-0099) `proposed → ready` → build (imports
  this module's `ConnIndex`/`ConnEvidence`). Then bp-061; bp-062 gated on uuid-identity. After the
  tranche: graduate `graph-at-a-past-cut` → design note (memory curve v1). Next plan id bp-063; next
  finding 0101. oq-0029 still open (bless the rest of the tranche item-by-item).

## 2026-07-17 (session 25 cont.) — /graduate dn-chat-sensor → bp-063 + bp-064 (proposed)

- **`/graduate dn-chat-sensor`** (owner-directed) — minted the §3 tranche as `proposed`:
  **bp-063 chat-sensor-core** (CS-1/2/3: rawstore retention + the OBSERVED-only `chatlog` store +
  utterance extraction with structural tool-strip + secret guard; ~200k opus, 3 items) and
  **bp-064 chat-clock-wiring** (CS-4: enroll the store as g1 per-session chains in the `observed`
  stratum + `observed→TROUGH` cut certificate; ~150k opus, 2 items, `depends_on: bp-063`).
  **Plan 3 (formalization-lag, CS-6) deliberately NOT minted** — triple-gated (connectivity built ✓
  bp-059; sensor+clock ⇐ bp-063+064; correlator scoped grant = owner act; + uuid-identity for claim grain).
- **Grounded pass (both plans, §3):** transcript JSONL shape MEASURED on a live file (text/thinking/
  tool_use/tool_result blocks; keep `text` only); OBSERVED-only store copies `code_observations.py`
  (no provenance param — structural firewall); no reusable secret scanner exists (guard authored, a
  backstop to the tool-strip); no edge handoff (local-file sensor, vault-watcher species); bp-064 is an
  ADDITIVE extension of the pinned spine surface (`observed→TROUGH`, session-close trough-style, no
  HANDOFF — grounded vs the `eval→TROUGH` case). 105 transcripts today (note said 103 — never hard-coded).
- **NEXT (owner-gated):** owner blesses bp-063 → build (OPUS) → owner blesses bp-064 → build. These
  interleave with the connectivity tranche (bp-060/061/062) per the owner's sequencing. Next plan id
  **bp-065**; next finding **0101**. dn-chat-sensor stays ratified (unedited — graduation changes no note).

## 2026-07-17 (session 26) — EXECUTE the locked build order: Wave 1 spawned (bp-060 ∥ bp-063)

- **Orchestrator posture.** All 5 plans `ready` (owner-blessed, `552f885`); build order LOCKED
  2-wide parallel (owner, session-25), bp-062 partial. NO blessings pending. Main green at `552f885`
  (bless-only over `67b373d`; suite 1454p, argless mypy 69).
- **Budget gate PASSED.** Owner /usage relayed: session 13%, **weekly (all models) 33%** (the gate
  build waves draw; resets tonight ~8pm — ~67% headroom), credits 86% (NOT the gate). 2-wide fits.
- **Wave 1 SPAWNED** — two OPUS full-strength builders, isolated worktrees, disjoint write_scopes,
  running concurrently:
  - **bp-060** (conductance, CN-3/4) — `eval/harness/conductance.py` + 2 test files. Carries the
    weighted-Rayleigh attribution law (finding-0099); item 6 edit-rise synthetic; real-corpus scan a
    sanctioned partial.
  - **bp-063** (chat-sensor core, CS-1/2/3) — `core/stores/chatlog.py` + `ops/chat_sensor.py` + 2
    test files. OBSERVED-only structural firewall; verbatim-first; fail-closed secret guard.
    `reset_targets()` registration OWED to orchestrator post-merge (builder NAMES, does not edit).
- **Merge discipline:** integrate SERIALLY — merge builder 1, re-run FULL 5-leg gate on integrated
  tree (argless mypy == 69 tree-wide), then builder 2, re-gate. Seal each with enriched cost.actual.
- **NEXT:** await completions → review diffs (scope + real gate output + falsifiers) → serial merge +
  re-gate → seal. Then Wave 2 (bp-061 ∥ bp-064; bp-064 = spine surface, watch hardest). Next finding
  0101; next plan bp-065.

## 2026-07-17 (session 26 cont.) — bp-063 SEALED · owner ruling (A): graph math moves INTO core · dn-core-graph-instruments drafted · bp-065 staged

- **bp-063 COMPLETE + sealed** — merged `7cc0975` (ff, scope-clean: exactly write_scope + journal);
  orchestrator verified the structural firewall (to_row hardcodes OBSERVED, no provenance param) +
  fail-closed guard (whole-session refusal BEFORE add_batch, pattern NAME never value) by reading the
  diff; owed `reset_targets()` registration done (`chatlog.sqlite`, rebuilt from immutable rawstore).
  Integrated gate ALL 5 legs green on main: ruff ✓ · mypy targeted ✓ · **argless 69 ✓** · type_gate ✓ ·
  **pytest 1498p/10s (26:32)**. cost.actual: 137k opus, ratio 0.68, dollars/deltas pending /usage relay.
- **bp-060: builder STOPPED (killed by orchestrator), work preserved** — branch
  `worktree-agent-a1d5f2b78350b8586` holds items 4-6 COMMITTED (`3c7421e`, `88e73ca`; final 5-leg
  attestation never ran); artifacts snapshotted to session scratchpad `bp060-harvest/`. NOT merged.
- **OWNER RULING (in-session): (A) reconcile immediately** — the connectivity math is CORE vocabulary;
  architecture selected: new `core/graph/` reusing `core/complex` (ONE Laplacian), eval thin wrappers;
  session switched to fable/xhigh, refactor directed now. finding-0101 → **promoted**; oq-0030 answered.
- **`dn-core-graph-instruments` DRAFTED** (amendment-by-link to dn-connectivity-instruments §3:210
  "All eval-side"; warrant finding-0101). Key rulings: P1 self-containment (core never imports eval for
  math; permanent grep-tooth on core/graph), P3 one Laplacian (core/complex's; bp-060's dense
  re-derivation deleted), **P4 no-silent-metric-change** (diffusion_map is L_sym — a SIBLING geometry to
  the finite-t heat kernel over combinatorial L; Φ(S) ≠ pairwise R_eff; reuse bounded by object
  identity), P5 re-export compat (bp-059 tests must pass UNCHANGED), P6 full boundary audit →
  **finding-0102** filed (shadow.py imports eval.drift/golden LOGIC — own lane, grandfathered not licensed).
- **bp-065 (`core-graph-rehome`) STAGED** in scratchpad (files on ratification — /graduate refuses a
  draft note): harvest bp-060's branch into core/graph/conductance.py + thin eval wrappers + boundary
  and L-equivalence tests; supersedes bp-060. bp-061/062 → re-mint against core/graph AFTER it lands.
- **NEXT (owner, two hand acts):** ratify `dn-core-graph-instruments` → orchestrator files bp-065 →
  owner blesses `ready` → in-session fable build. Chat lane: bp-064 unaffected, queued behind the
  reconciliation. Next finding 0103; next plan bp-066 (after bp-065 files).

## 2026-07-17 (session 26 cont.) — dn-core-graph-instruments RATIFIED (owner hand edit) · bp-065 minted · TRACK AMENDED

- **Note RATIFIED by owner hand** (`status: draft → ratified` observed in working tree). The ruling is law.
- **bp-065 (`core-graph-rehome`) MINTED `proposed`** from the ratified note (plan + journal filed from the
  session-staged text; supersedes bp-060; fable in-session self-build, est 90k). Awaits owner `proposed → ready`.
- **Track amended (owner instruction), every artifact:** bp-060 → `superseded` (by bp-065; build DONE +
  preserved on branch, harvest banner); bp-061 → `superseded` pre-build (re-mint post-bp-065; §6–§8 carries
  verbatim); bp-062 → `superseded` pre-build (re-mint inherits item-11 uuid park); bp-059 stays `complete`
  + placement-amendment banner (history unaltered); `graph-at-a-past-cut` brainstorm → orientation note
  (future graduation must cite core.graph). All banners name the note + warrant finding-0101; /build now
  refuses every superseded plan (status is the guard).
- **OWED to owner hand (agent-immutable at ratified):** the amendment banner INSIDE
  `dn-connectivity-instruments` — paste-ready text delivered in-session. Ledger: ready=(none),
  proposed=bp-065, superseded=bp-040,bp-060,bp-061,bp-062. Next finding 0103; next plan id bp-066.
- **NEXT:** owner blesses bp-065 `proposed → ready` → in-session fable build (harvest + thin-ify + gates).

## 2026-07-17 (session 26 cont.) — bp-065 COMPLETE + SEALED: connectivity math re-homed to core, clean break, second audit

- **bp-065 (`core-graph-rehome`) COMPLETE** (`23e332f`) — the owner-directed reconciliation, done.
  `core/graph/{sigma_star,conductance}.py` own the σ*/conductance MATH on `core/complex`'s ONE
  Laplacian (P3); `eval/harness/{connectivity,conductance}.py` are PLAIN CONSUMERS — no wrappers,
  no aliases, no `__all__` (the clean break). Arrow: `eval → core.graph → core.complex`, one way.
- **Second audit (owner-directed):** AST move-fidelity (68 defs, zero unsanctioned drift — found+fixed
  2 deferred-import deviations); independent first-principles math (maximin≡MST brute-forced,
  R_eff circuit laws exact, heat-kernel ≡ scipy.expm, Rayleigh, sign law, von-Luxburg) ALL PASS;
  P1-P6 design-match; house-style (OBJECT/INVARIANT/ENFORCED headers added — owner catch).
- **Gate:** all 5 legs green on the final clean-break tree — ruff · mypy targeted 216 · **argless 69**
  · type_gate · **pytest 1536p/8s**. cost.actual mixed fable→opus; dollars/deltas pending /usage relay.
- **Ledger moves:** bp-060 → superseded (build preserved on branch `worktree-agent-a1d5f2b78350b8586`,
  shipped here behavior-frozen); bp-061/062 → superseded pre-build (re-mint against core/graph);
  bp-059 stays complete (placement banner). dn-core-graph-instruments RATIFIED; dn-connectivity-
  instruments amendment banner in place. Blessings recorded: `0d05001` (note), `7f75fa9` (bp-065),
  `4e95480` (banner).
- **finding-0102 OPEN** — `shadow.py` imports eval LOGIC (drift/golden): the remaining "core self-
  contained" reach (+ the store-sink); deferred to its own design pass. Memory: [[core-self-containment]].
- **NEXT (orchestrator):** push to origin. Then — bp-064 (chat clock, the held `ready` chat-lane plan)
  OR re-mint bp-061/062 against core/graph OR the finding-0102 self-containment pass. Next finding
  0103; next plan bp-066. /usage relay still owed to close bp-063 + bp-065 seal deltas.

## 2026-07-17 (session 26 END) — the core-sacred reconciliation; bp-066 enforcement READY

- **Session arc:** Wave 1 (bp-063 sealed, bp-060 built) → owner interrogated the connectivity
  instruments' placement → cascaded into a standing principle: **the core is SACRED and
  self-contained** (deps = stdlib + pinned side-effect-free 3p + core; NO first-party outside core;
  config included, no wiggle room) + strict **DRY** (a dup is a defect). Memory: [[core-self-containment]],
  [[owner-dry-strictness]].
- **bp-065 sealed** (`23e332f`) — reconciliation done: σ*/conductance math re-homed to `core/graph`
  on `core/complex`'s one Laplacian; eval a plain consumer (clean break, no wrappers); second audit
  (fidelity + first-principles math + P1-P6 + house style) all pass.
- **finding-0103** — full audit: core violates self-containment **106×** (config 90 / ops 8 / eval 7 /
  agents 1). Config remediation ruled = **SPLIT** (`core.config` inside core), not DI.
- **bp-066 READY** (`c385ddd`, owner-blessed) — the LOUD RED enforcement (test at 106 + CONVENTIONS
  DRY/self-containment rules + manifest-audit skill step). ⚠️ builds the suite RED-by-design; that's
  the forcing function, not a regression. **Next session: `/build bp-066`.**
- **Cleanup roadmap:** bp-067 config-split (106→16) → bp-068+ the 16 machinery inversions (→green).
- **Reset handoff:** `.claude/state/resume-brief.md` rewritten (full session-26 close). Ledger:
  complete +063+065; ready=bp-064,bp-066; superseded +060,061,062. Next finding 0104; next plan bp-067.
  OWED: /usage relay (bp-063 + bp-065 seal deltas). dn-connectivity-instruments amendment banner in place.

## 2026-07-17 (session 27) — the build wave: bp-066 (red enforcement) + bp-064 (chat clock) SEALED

- **Owner directive:** "run the hardening build and finish the other builds as well." The two `ready`
  plans (bp-066, bp-064) were the whole buildable queue; both landed and sealed in-session (OPUS).
  Everything downstream (bp-067 config-split, bp-068+ inversions, bp-061/062 re-mints) is gated on the
  owner-only `proposed→ready` blessing, so it is NOT autonomously buildable — flagged, not built.
- **bp-066 SEALED** (`748c946` deliverable + `a2f3bfd` seal) — the core-self-containment ratchet.
  `tests/unit/test_core_self_containment.py` (dynamic AST scan) fails **RED at 106 by design**; the
  two CONVENTIONS rules (DRY §Language & style; self-containment §Trust boundaries — no eval paren)
  + the build-plan §2 manifest-audit step landed. **⚠️ The suite is now RED-by-design: "green" = the
  ONLY failure is `test_core_imports_nothing_outside_core` AND its count is monotone non-increasing.**
  Pre-build defect fixed: unquoted write_scope entries with inline comments → scope-guard denied every
  write (quoted them; process note for future plans). cost ~45k opus, ratio ~1.1.
- **bp-064 SEALED** (`c3fef76` deliverable + `39375b3` seal) — CS-4 chat clock. `chatlog` enrolled in
  the spine as observed-stratum per-session g1 chains (chain-key=session_id, pos=turn_index) +
  `_STRATUM_CERTIFICATES["observed"]={TROUGH}` (local-file sensor ⇒ no HANDOFF). Additive only, no
  reshape. 9 new tests. §3 Q4 held (no atlas change, no finding). **Ratchet stayed 106** (ChatlogStore
  is intra-core). cost ~85k opus, ratio ~0.57 (tightly pinned). Opens 2 of CS-6's 3 gates.
- **State:** main at `39375b3`. Full suite **1 failed / 1547 passed / 8 skipped** (the 1 = intentional
  red). Argless mypy **69** (baseline). Ledger: complete +bp-064,bp-066; ready=(none); superseded
  bp-040,060,061,062. Next finding 0104; next plan bp-067.
- **OWED:** /usage relay now closes bp-063 + bp-065 + bp-066 + bp-064 seal dollar/session/week deltas.
- **Open owner decisions (unchanged, neither blocks anything):** pacing of the cleanup program (build
  bp-067 config-split now to drop the red 106→16, or let the 106 red sit visibly first?); whether the
  self-containment rule earns a one-line CLAUDE.md pointer (orchestrator leans NO — engineering, not a
  safety bright line). Also standing: re-mint bp-061/062 against core/graph (owner re-bless).

## 2026-07-18 (session 27 cont.) — bp-067 SEALED: config loader moved to core.config (ratchet 106→19)

- **Owner directive:** "let's now work on fixing the errors" → the 106 self-containment reds (owner
  chose them over the 69 mypy baseline). First cleanup plan = bp-067, the config split.
- **bp-067 SEALED** (`e529320` deliverable + `ce22893` seal) — the config leg of finding-0103.
  `config.loader` (stdlib-only, side-effect-free) moved to `core/config/`; 46 core files repointed
  `config.loader → core.config`; the outside `config/` is now a re-export **facade** (the ~147
  non-core importers untouched). **get_secret split at the trust boundary:** core's is ENV-ONLY (no
  token, no secrets_backend import — the network Vault path can't leak in); the token-capable form
  stays in the facade. **Security win:** core config loading now falls under `import_lint`'s network
  ban — structurally network-proven. **Ratchet 106 → 19.** Suite 1 failed (intentional) / 1552 passed
  / 8 skipped; argless mypy 69. cost ~155k opus, ratio ~1.2 (~$32).
- **finding-0104** (filed + resolved) — a build-start stop-and-raise: the facade can't preserve
  monkeypatch-of-globals across a module move, so 3 coupled tests joined scope (owner **option A** —
  keep the credential trust boundary untouched). A clean pause, zero code changes, then re-scoped +
  re-blessed. Toml-data deviation: data stays in `config/` (its `.gitignore` is out of scope), loader
  reads by path.
- **write_scope footgun fix (`4afa2d8`)** — inline comments on write_scope entries are now banned at the
  source (template + build-plan skill); memory [[write-scope-quoting]] strengthened. Owner-flagged.
- **Remaining red = 19:** 3 factory secrets/Vault reaches (the DEFERRED security inversion, bp-068
  candidate) + the 16 machinery reaches (each its own inversion plan) → green when all invert.
- **/usage relay (owed for bp-063/065/066/064/067) — CLOSED:** session 11% used, all-models week 3%,
  Fable 0%; session $53.28 (opus 258.3k output). Credits now OFF ⇒ builds draw the weekly (ample room).
- **State:** main `ce22893`→(this). Next finding 0105; next plan bp-068. Ledger: complete +bp-067.

## 2026-07-18 (session 27) — /triage reflection checkpoint (the four-tracks reflection)

Owner called a reflective checkpoint on the four tracks (chat sensor · connectivity · seal-core refactor
· triage). Reflection theme: **construction outran enforcement/validation** — the core-seal surprise is
one instance of a recurring shape (a property built but not structurally proven until forced open). The
`write_scope` footgun literally proves it: found THREE times (findings 0078, 0085, 0104) before the
source-level fix landed this session.

**Sweep results:**
- **Resolved (4):** finding-0078 + finding-0085 (the write_scope inline-comment footgun — fixed at
  source, commit 4afa2d8: bare-globs rule in template + build-plan skill); finding-0102 (shadow.py→eval,
  subsumed by finding-0103's cleanup program); finding-0104 (bp-067 obstacle — owner option A, bp-067
  sealed).
- **Routed open→routed (5):** finding-0096/0097/0098 (σ-sweep saturation at 13-doc scale) +
  finding-0099/0100 (CN-3 law refinement + bp-059 over-claim). The connectivity/sweep cluster.
- **Owner questions swept (2):** oq-0030 (reconcile connectivity → delivered by bp-065) + oq-0029
  (bless the tranche — MOOT: bp-059 complete, bp-060/061/062 superseded via bp-065).
- **New owner question (1):** **oq-0031** — the connectivity/sweep instruments are code-complete but
  can't discriminate at 13-doc corpus scale (findings 0096/0097/0098; entangles oq-0024). Direction
  fork: (A) grow the corpus first, (B) defer the validation lane (default — parked, harmless off),
  (C) shrink the sweep objective to a non-saturated metric. Owner to decide.
- **Builder-owned, left for their plans (6):** finding-0046/0059/0064/0073/0076/0089 (bp-016/020/026/
  029/034/049 — codebase/spec-fidelity, correctly builder-routed; revisit with their plans).
- **Plans sealed this session:** bp-064, bp-066, bp-067 (all checkpointed + journals sealed above).
- **Book:** unscaffolded — no sync debt.

**Findings ledger after triage:** open 16→10 (4 resolved, but the 5 routed stay "open-ish" as routed;
net open-that-need-owner = the connectivity cluster + the 6 builder-owned). Open owner questions: 11
(oq-0031 new; oq-0029/0030 swept). Standing owner-question debt worth a batch review: oq-0009/0010
(research-note convention), oq-0018–0022 (magnetic-laplacian decisions), oq-0024 (σ tune — now under
oq-0031), oq-0025/0026/0028 (ratified-note errata: annotate-by-hand vs standing-erratum), oq-0029→swept.

## 2026-07-18 (session 27 END) — wrap-up: live-state check + forward plan + lessons

- **Live-state check (owner asked whether Ouroboros is running):** it's **UP** (launchd
  `com.mind-palace.palace` PID 78713 + vault + backup; KeepAlive) and very active (code-sensor stores
  >2GB, 676 commits). The owner's "probably not running" was mistaken. BUT: **chat has NEVER been
  ingested** (`data/chatlog.sqlite` absent — the bp-063 sensor never ran), and the **vault note-corpus is
  still 13** files while the OBSERVED strata (code) are huge.
- **Forward plan (owner, 2026-07-18):** (1) **run the chat sensor** to ingest the dialogue (first
  action). (2) **continue the connectivity track** to build the **strata-access scope machinery** — a
  privileged core reader / dreamer accesses the full strata (or a subset) WITHOUT widening MirrorView —
  which unlocks the already-large observed-strata data for richer sweep/dreamer testing (the real answer
  to oq-0031's 13-doc saturation). (3) diagnostic: why the mirror corpus is stuck at 13. Parallel:
  seal-core cleanup (bp-068 factory secrets + bp-069+ the 16 reaches → green).
- **Lessons learned (saved to memory):** [[structural-enforcement]] (a property is real only when a
  ratchet proves it), [[ground-before-building]] (ground a facade/instrument against real out-of-scope
  callers first; separate mechanical moves from trust-boundary changes), [[write-scope-quoting]]
  strengthened. Process note: a greedy `resolution:` regex ate 4 findings' bodies mid-triage — restored
  via `git checkout`, re-applied line-based (prefer line-based frontmatter edits).
- Full resume handoff in `.claude/state/resume-brief.md`. Next finding 0105; next plan bp-068.

## 2026-07-18 (session 27 END+) — Ouroboros recovery incident (halted-in-recovery → clean HEAD daemon)

Correcting the earlier wrap-up ("Ouroboros UP and busy" — WRONG): the daemon had been **halted in
recovery** since 2026-07-17. Run #23 died ungracefully (no traceback — a process kill / laptop
sleep-wake), KeepAlive restarted into #24's **fail-safe recovery** (scheduler halted, watcher off,
read-only), pinned to the STALE sigma-sweep commit `c63f12f`. That halted watcher is why the vault
catalog was stuck at 13 while the vault grew to 17. (The "busy" code-sensor is a post-commit git hook,
not the daemon.)

**Resolution (this session):** owner `start --force`'d → foreground #25 on HEAD, which created a
**double-instance** beside the launchd #24. I `down`'d the stale launchd #24 (`launchctl bootout` —
outlasts KeepAlive; leaves the foreground untouched); owner Ctrl-C'd #25 clean; I `up`'d launchd →
**#26 RUNNING, background, clean, on HEAD (ec243275)** — "running HEAD", no promote warning. Tidied the
#23 zombie (false RUNNING → UNCLEAN). HEAD's refactored code is now VALIDATED LIVE (#25's foreground
run advanced dreams 1→2, clean shutdown).

**Findings filed:** 0105 (the red-by-design ratchet BLOCKS `palace deploy` for the whole cleanup period
— owner picks the gate policy, lean: deselect the one intentional test); 0106 (`mind-palace` wrapper
omits `up`/`down`/`restart`/`deploy` — they're on `scripts/palace.py`; `status` even points at the
wrapper-absent `palace deploy`). Memory saved: [[palace-lifecycle-recovery]].

**Standing:** chat still un-ingested at wrap (but #26 runs HEAD's chat sensor — should ingest next
cycle; verify); pending-approval:1 in the gate (owner review); `drift/constitution: None` right after
start (verify populated next session). Next finding 0107.

## 2026-07-18 (session 27) — the game plan settled + bp-068 minted (chat-sensor wiring)

Owner settled the forward build-plan ORDER (the "game plan"):
1. **Track 1 — Chat (owner #1):** **bp-068 chat-sensor wiring** — MINTED `proposed`. The sensor
   (bp-063) + clock (bp-064) exist but nothing invokes the sensor (no scheduler registration / entrypoint
   — that's why chat has never ingested). bp-068 mirrors `scheduler/vault_sync.py` → `chat_sync.py`
   (`CHAT_SYNC_KIND` + handler + enqueue + `build_chat_sensor`), wires it into the launcher, adds a
   `palace ingest-chat` verb, and a `chat_transcripts_dir` config path. Est opus/100k. Awaits owner bless.
2. **Track 2 — Connectivity strata-access (owner #2, the big lever):** a GRADUATE of the RATIFIED
   `cross-strata-dreamer.md` + `capability-scope-algebra.md` → scope machinery so a privileged
   reader/dreamer reads full/subset strata WITHOUT widening MirrorView. Unlocks the observed strata
   (code ~1GB, chat) for the sweep/dreamer — the real answer to oq-0031's 13-doc saturation. ⚠️ overlaps
   the seal-core inversions of sensing/ops_view/reference_view/spine — coordinate, don't invert blind.
3. **Track 3 — Seal-core cleanup (parallel, ratchet 19→0):** factory secrets/Vault inversion (3 reaches,
   security) + the 16 machinery inversions (non-overlapping ones anytime; the 4 strata-overlapping fold
   into Track 2) + re-mint bp-061/062 against core/graph.

**finding-0105 DECIDED — option A** (owner): teach the deploy gate to DESELECT only the intentional
ratchet test, so `palace deploy` works throughout the cleanup + regains full strength when green.
Implementation PENDING (small `gate_cmd` change + a marker + a falsifier; bp-069 candidate or folded).

Findings open now: 0103 (19 reaches), 0096-0100 (connectivity, under oq-0031), 0105 (decided-A,
impl pending), 0106/0107 (status/wrapper papercuts), 6 builder-owned. Next finding 0108; next plan
bp-069.

---

## 2026-07-18 (session 28) — bp-068 COMPLETE: the chat sensor RUNS (chat ingested for the first time)

Built + sealed **bp-068** (chat-sensor wiring), the game plan's Track-1 forward action. The bp-063
sensor existed but nothing invoked it; now a scheduled `chat_sync` job + a `palace ingest-chat` verb do.

**Built** (write_scope only):
- `scheduler/chat_sync.py` (NEW) — `CHAT_SYNC_KIND` + `chat_sync_handler(sensor)` + `enqueue_chat_sync`
  (pins DIRECTLY to the always-warm tier at BACKGROUND priority — a model-less file scan must not force
  a worker load). Mirrors `scheduler/vault_sync.py`.
- `ops/lifecycle/launcher.py` — registered the handler in `build_components` (reusing bp-063's
  `ops.chat_sensor.build_chat_sensor`, as vault_sync reuses `core.ingest.sync.build_vault_sync`);
  `_catchup` enqueues at startup (backfill), `_housekeeping` on the tick; added `Launcher.ingest_chat()`.
- `scripts/palace.py` — the `ingest-chat` verb (USAGE + dispatch).
- Tests: `tests/unit/test_chat_sync.py` (5) + `tests/integration/test_chat_sensor_wiring.py` (2) — real
  Supervisor drains a chat_sync job + rows land; idempotency; secret fail-close; verb in-process.

**Verified LIVE:** `palace ingest-chat` → **110 sessions / 6365 utterances** into `data/chatlog.sqlite`
(OBSERVED), 111 raw retained, **1 session fail-closed by the secret guard**; a second run = 0 new
(idempotent). Chat had NEVER ingested before. Suite: **1 failed (intentional ratchet, count HELD at 19)
/ 1543 passed / 4 skipped**; ruff + mypy clean.

**Grounding (finding-0108, spec-fidelity, resolved-in-plan):** the plan §6 was mis-grounded twice —
(G1) `build_chat_sensor` ALREADY existed (unused) in `ops/chat_sensor.py`, so it was REUSED not
duplicated ([[owner-dry-strictness]]); consequently the `chat_transcripts_dir` config field was
DEFERRED (wiring it needs an out-of-scope ops/ edit; `_default_transcripts_dir()` already resolves for
the daemon) → **core.config untouched, ratchet stayed 19** (better than the plan's "gains a Path field").
(G2) pinning `chat_sync` wanted a `router._PINNED_KINDS` edit (out of scope) → done in-scope by enqueuing
directly on the pinned tier (supervisor honours the stored `job.tier`). **Two owner/orchestrator
follow-ups parked in finding-0108:** TOML-overridable transcripts dir (esp. for worktrees) + register
`chat_sync` in `router._PINNED_KINDS`.

**Plans:** complete += bp-068. Next plan **bp-069**. Findings open: 0103 (19 reaches), 0096-0100
(connectivity/oq-0031), 0105 (decided-A, impl pending), 0106/0107 (papercuts), **0108** (bp-068 grounding,
resolved-in-plan; 2 follow-ups parked), 6 builder-owned. Next finding **0109**.

**Next:** the game plan's Track 2 (connectivity strata-access) now has its observed chat data (110
sessions) to read. Also verify the daemon auto-ingests once HEAD deploys (the `_catchup`/`_housekeeping`
wiring), and consider bp-069 for finding-0105 (deploy-gate ratchet deselect).

---

## 2026-07-18 (session 28) — bp-069 MINTED (proposed): real-time lossless chat + multi-rate projection

bp-068's live verification surfaced a v1 caveat → **finding-0109** (design, owner-DECIDED): freeze-once is
lossy — a session left open (hours/overnight, how the owner works) drops its tail. Owner standard: parity
with code ingestion (every commit → every transcript change), "the system is real-time so ingestion must
be immediate."

**Architecture (owner):** ONE agent, MULTI-RATE PROJECTION — the model-free chat sensor always accepts the
latest real-time transcripts and projects each layer at its own rate. bp-069 = *rate 0* (real-time: raw
layer 0 + dialogue-strata projection); layers 1 (summaries) + 2 (references) are lower-rate projections by
the same agent, later, on already-scrubbed text (Track 2 / CS-5). Credential removal stays the DETERMINISTIC
gate at the real-time rate (bright line #10 — a model never reads a secret).

**bp-069 (proposed, owner-directed, warrant finding-0109):** growth-aware append (drive off rawstore
`is_new` — stateless "git for transcripts"; never freeze) + torn-line tolerance + a LIVE debounced
transcript watcher (generalize `VaultWatcher`→`DirectoryWatcher`; `build_chat_watcher`; multi-watcher
launcher; `[chat]` config). AMENDS ratified dn-chat-sensor Q4. Folds finding-0108's two follow-ups.
Est opus/180k, session_budget 2. **Awaits owner `proposed → ready` bless.**

Findings open: 0103 (19 reaches), 0096-0100 (connectivity/oq-0031), 0105 (decided-A, impl pending),
0106/0107 (papercuts), 0108 (bp-068 grounding, resolved-in-plan; folded into bp-069), **0109** (chat
freeze-once, decided → bp-069). Next finding **0110**. Plans: proposed = bp-069; next id after = bp-070.

---

## 2026-07-18 (session 28, FABLE/xhigh) — design pass: `dn-agent-taxonomy` drafted

The owner's four-role agent ontology (sensor / query agent / integrator / dreamer), formalized as
scope signatures in the ratified CQ-scope algebra → **`docs/design-notes/agent-taxonomy.md`**
(`dn-agent-taxonomy`, **draft — awaits owner ratification**, warrant: the captured
`agent-type-taxonomy` brainstorm + finding-0109). Decisions drafted:
- **Roles as signatures** (Σ,E,T,A + model-class): sensor = own-stratum, multi-rate projection,
  model-free; query agent = read-only, answers, never structure; **integrator = MULTI-strata
  layer-granular read (the owner's correction), edges-only write, model-free**; dreamer = apex,
  per-owner-grant up to ⊤_Σ, model-priced (cites the ratified cross-strata-dreamer per-scope ruling).
- **Two laws:** the deterministic floor (nodes + proven edges are model-free) and the grounding law
  (interpretive edges cite proven support) + the pricing corollary (breadth is cheap iff model-free).
- **Fiber C (causal-witnessed)** proposed beside F/D — C = origin, D = lineage, F = support; C
  explains D, never as it; C∘D answers "which conversation produced this version?".
- **Witness law + SLICE:** every proven edge carries mechanical evidence and arrives cut-stamped
  (the commit SHA is the cut). **Commits as cross-clock bookmarks:** each C-edge causally
  co-registers the chat clock with the commit clock (`turn_i ≺ commit ≺ turn_{i+1}`) — the
  empirical anchor data the future global event clock N interpolates through.
- **Layer tissue is fibrational, not edge-typed** (projection fibers on the rows — the sourceset
  pattern — vs E-fiber edges beside the data).
- **The DIALOGUE stratum** drafted into R (transcripts + brainstorms/design notes/docs; code stays
  observed); stratum ≠ provenance reconciliation explicit; MIRROR_READABLE untouched.
- The abstractive model summary is typed OUT of the sensor (a later scoped model-client).

**Next (after the owner's hand-ratification of the note):** re-ground bp-069 (the dialogue sensor
agent, rates 0+1) in the note's language → owner bless → build; mint bp-070 (the first full
integrator: chat↔code↔doc, witness law, fiber C, DIALOGUE enum addition folded in).

---

## 2026-07-18 (session 28, FABLE) — the NEW game plan: the diamond (supersedes the session-27 track order)

Owner called for a full analysis across the three programs. Result: a DIAMOND, not three lanes —
`dn-agent-taxonomy` (R) is the root; the sensor (bp-069) and integrator (bp-070) are the arms;
connectivity (A2) is the sink consuming both; the dreamer grant machinery (A1) is parallel with its
own gate chain. Plus the forgotten OPS LEG: daemon runs pre-bp-068 code — 0105 impl → push → DEPLOY
(owner gate) is what makes the sensors live continuously.

**Sequence:** 0) OWNER ratifies dn-agent-taxonomy → 1) re-ground bp-069 → OWNER bless →
2) build 69 items 1-2 (lossless L0 + watcher; TIME-BOUNDED — frozen tails recoverable only within
the CLI transcript-retention window; re-ingest after) → 3) ops leg (0105 impl, push ~25 commits,
owner deploy) → 4) build 69 item 3 (L1 action log) → 5) mint+bless+build bp-070 (integrator; item 1
= fiber C + DIALOGUE enum extensions) → 6) A2 connectivity re-measure ({mirror ∪ dialogue nodes} ×
{E_sim ∪ E_proven}; resolve 0096-0100/oq-0031; CN-3 if the data moves) → 7) A1 strata-access grant
machinery (fable design pass FIRST — it must batch the G1-class owner decisions; can start parallel
any time after 0). Critical path ≈ 6-8 opus sessions + owner gates. Fable only for 7 + any CN-3 math.

**Key re-diagnosis:** oq-0031's 13-doc saturation was input starvation (nodes + edge classes), not
σ-tuning; the integrator's E_proven + the chat nodes are the fix — strata-access (A1) serves the
DREAMER, not the integrator (deterministic, structural enforcement — no runtime grants needed to
build). Risks instrumented: retention window (step 2 first), schema drift (parity ratchet +
C-coverage ship WITH 69/70), A1's hidden owner decisions (surface early), A2's graph-choice
(explicit eval-design decision at step 6).

---

## 2026-07-18 (session 28, FABLE) — sequencing AMENDED by owner: algebra leads (supersedes the order two entries up; the diamond GRAPH stands)

Owner's order accepted — scope algebra as CONSTRUCTION LANGUAGE, not just enforcement: agents born
carrying declared scopes (instantiation pressure: the grant machinery debuts on two deterministic
clients before the model-priced dreamer; no retrofit pass). **Retention-clock objection DEFUSED by
insurance:** transcripts dir snapshotted → `data/backup-staging/transcripts-snapshot-2026-07-18.tar.gz`
(60MB, 203 .jsonl — reset-guarded, restic-covered). Note: 203 files on disk vs 110 ingested — the
sensor's parity gauge must account for every file (ingested/refused/empty/excluded).

**Order: Α → Β → Γ → Δ.**
Α (lead, ~2 sessions, after owner ratifies dn-agent-taxonomy): D1 type extensions (DIALOGUE stratum +
fiber C, lattice tests); D2 declared-scope agent layer (template scopes, meet-composition, conformance
guard "handles ⊑ declared scope"); D3 instruments accept E_sim ∪ E_proven (fixtures, turnkey later).
NOT in Α: model-client grant enforcement + dreamer gates (A1's second half, later).
Β (~2-3 sessions): bp-069 RE-MINTED as the dialogue sensor agent born-scoped (Σ=dialogue, E=∅,
A=(READ,W_Σ=1,NONE), clock N_chat) → owner bless → build L0-lossless → watcher → L1 action log →
re-ingest recovers frozen tails.
Γ (~2 sessions): bp-070 the integrator, born with the real multi-strata scope
(Σ={(dialogue,L1),(observed,commit-ledger),(dialogue_artifact)}, E={C,F} write, Clock.COMMIT,
pair-cut witnesses, parity + C-coverage instruments).
Δ (~1 session): connectivity re-measure; resolve 0096-0100/oq-0031.
Parallel any time: ops leg (0105 → push → owner deploy); A1 dreamer-facing design pass (batches its
owner questions). Next: OWNER ratifies dn-agent-taxonomy → mint the Phase-Α plan(s).

---

## 2026-07-18 (session 28, FABLE) — REFORMULATION COMPLETE: the diamond as artifacts; gate list

Plan ids assigned: **bp-070 = Phase Α scope-tooling** (D1 DIALOGUE+fiber-C types · D2 declared-scope
agent layer · D3 composed graph E_sim ∪ E_proven — grounded: MirrorGraph is similarity-only, the
union enters at core-side assembly) · **bp-069 RE-MINTED = Phase Β dialogue sensor agent** (born
scoped via D2; same 3 items + total-accounting parity gauge; depends_on bp-070) · **bp-071 = Phase Γ
integrator** (charter-form; Item 0 = re-ground against landed Β; witness law, pair-cut, C-coverage +
resolution-parity gauges). Integrator references renumbered bp-070→bp-071 across the taxonomy note,
finding-0109, the brainstorm. dn-agent-taxonomy §3 rewritten as the phased program. Phase Δ
(connectivity re-measure) minted at Γ-seal time, not before (its shape depends on Δ-adjacent
findings). Next plan id **bp-072**.

**TO BEGIN (owner, by hand):** 1) RATIFY `docs/design-notes/agent-taxonomy.md` (draft→ratified — also
fixes the parked defaults: fiber letter C, DIALOGUE placement). 2) BLESS bp-070 (proposed→ready) →
/build starts Phase Α. 3) BLESS bp-069 (now or after Α seals — depends_on enforces order either way).
bp-071 stays proposed until after Β (Item 0 re-ground), bless then. Parallel owner gates any time:
push (~30 commits) + finding-0105 impl + `palace deploy`.

---

## 2026-07-18 (session 29, OPUS) — ops leg: finding-0105 landed (deploy gate unblocked)

**Built** (owner said "do both, ops leg first, then bp-070"). Decided-A impl for finding-0105:
`Launcher.gate_cmd` (`ops/lifecycle/launcher.py:259`) now carries a surgical
`--deselect tests/unit/test_core_self_containment.py::test_core_imports_nothing_outside_core`, so the
deploy gate enforces the whole deterministic suite EXCEPT the one intentional-red ratchet — and
regains full strength automatically when the cleanup reaches zero. Not `--skip-tests` (blunt, drops
the whole gate); not an xfail/skip on the test (would weaken the ratchet in the full suite too).

**Verified.** Falsifier `test_gate_deselects_only_the_intentional_ratchet`
(`tests/integration/test_lifecycle.py`): (1) structural — exactly one `--deselect`, naming the
ratchet node, so the scanner guards + every other test stay live in the gate; (2) behavioural —
the real self-containment file runs GREEN under that deselect (guards actually ran & passed; a guard
regression would flip it red and refuse the deploy). `pytest -k "deploy or ratchet"`: 9 passed.
Ratchet untouched, still red at 19 in the full suite. finding-0105 → **resolved**.

**Next.** `palace deploy` is now owner-runnable to promote the daemon onto HEAD (owner gate — chat
sensing runs continuously once landed). Then the diamond lead: `/build bp-070` (Phase Α).

---

## 2026-07-18 (session 29, OPUS) — bp-070 SEALED: Phase Α scope tooling (the diamond's root)

The diamond's first plan lands. Three additive, deterministic, fixture-tested deliverables:
- **D1** (`core/scope.py`): `DIALOGUE` base stratum + `dialogue_transcript`/`dialogue_artifact`
  refinements into `Stratum`/`_REFINES`; fiber `C` (causal-witnessed) into `Fiber`/`EdgeScope.top()`.
  Additive lattice extension — `test_scope.py` EXTENDED (4 new tests), the existing 28 pass verbatim.
- **D2** (`core/agent_scope.py`, NEW): the declared-scope agent layer — `sensor_scope`/`query_scope`/
  `integrator_scope`/`dreamer_scope` (§2.1 role regions) + `Handle`/`assert_conforms` conformance.
  Agents are BORN scoped; composition is the EXISTING `Scope.meet` (no new lattice op). Integrator
  validates ≥2 base strata + write fibers ⊆ {C,F}; conformance rejects a smuggled handle.
- **D3** (`core/graph/composed.py`, NEW): `compose(nodes, sim_edges, proven_edges)` → a `ComposedGraph`
  presenting MirrorGraph's exact surface, so the EXISTING σ*/conductance math consumes `E_sim ∪
  E_proven` UNCHANGED (a `cast` static-bridges in the test; math untouched). Per-class attribution
  retained; a proven bridge edge (weight 1.0) joins two σ-components (the oq-0031 answer, in miniature).

**Verified:** full deterministic suite (gate cmd, ratchet deselected) = **1567 passed / 4 skipped /
0 failures**; ratchet held **19** (all three modules import core substrate only). No Views/stores/
harness touched. ruff+mypy clean throughout. Committed; pushed. **Next:** `/build bp-069` (Phase Β,
the dialogue sensor agent — READY, depends_on bp-070 now satisfied); it consumes D2's
`sensor_scope(DIALOGUE)` + conformance. bp-071 (Γ) stays proposed until Β seals. Δ mints at Γ-seal.

## 2026-07-19 (session 30, OPUS) — bp-069 SEALED: Phase Β, the dialogue sensor agent (born scoped)

Phase Β of the diamond lands — all 3 items built + verified in ONE OPUS session (budget was 3). The
Claude Code transcript sensor becomes lossless + real-time (finding-0109 — freeze-once removed) and
projects at two deterministic rates, born scoped under bp-070's D2 layer:
- **Item 1 — L0 lossless** (`ops/chat_sensor.py`, `c5d8bbf`): `sync()` drops the freeze-once filter and
  gates re-parse on the rawstore `is_new` signal — an unchanged transcript is skipped (no churn), a
  GROWN one re-ingests its tail (add_batch appends only new turns). `parse_transcript` is torn-line
  tolerant. `ChatSyncReport` is now a TOTAL accounting (`is_fully_accounted()` — every file → exactly
  one bucket). Q2 "freeze at pre-secret state" is emergent (whole-session refusal unchanged).
- **Item 2 — real-time trigger** (`2821a53`): `VaultWatcher` → `DirectoryWatcher` (DRY rename, vault
  behavior byte-identical); `build_chat_watcher` (on_change → chat_sync); `[chat]` config / `ChatConfig`
  (ratchet stays 19); the launcher drives a LIST of watchers (vault + chat); chat_sync/chat_events pin
  (finding-0108 G2).
- **Item 3 — L1 action log** (`core/chat_events.py` + `core/stores/chat_events.py`, `632fa6f`):
  `extract_events` reduces a raw transcript to its ordered typed action log (prompt→response→commit(sha)
  →file_edit→build_plan→… — model-free, structural refs only, unknown tools fail-open); `ChatEventProjector`
  re-extracts iff `transcript_digest` changed. Born scoped: `DIALOGUE_SENSOR_SCOPE` + the D2 conformance
  test (handles ⊑ scope; smuggled stratum/edge-fiber rejected).

**Verified:** full deterministic suite = **1584 passed / 4 skipped / 0 failures**; ratchet held **19**
throughout. Two LIVE runs on real data: `palace ingest-chat` recovered the frozen tail (grown=1,
accounted=ok, churn-free on re-run); `project(max_sessions=5)` → 482 typed L1 events, structural refs,
no crash. ruff+mypy clean (mine; 4 pre-existing E501 in launcher gate_cmd are finding-0105 debt).
Committed all three. **Next:** owner `palace deploy` (unblocked) to put the daemon on HEAD for
continuous sensing; then Phase Γ = bp-071 (integrator, proposed — Item 0 re-grounds against the landed
L1 schema, then owner bless). Δ mints at Γ-seal. Parallel papercut: the owner-cockpit plan.

---

### bp-071 — Phase Γ: the first full integrator (chat↔code↔doc proven edges) — COMPLETE (2026-07-19)

**Status:** COMPLETE (sealed session-31, OPUS; budget was 2, done in one). Graduates
`dn-agent-taxonomy` §2.5 — the first full **integrator** role: deterministic, model-free,
multi-strata read, edges-only write. Resolves the L1 action log's references into witnessed
C-fiber proven edges.

**Item 0 — re-ground vs landed Β** (`e1d4741`, finding-0111, spec-fidelity/builder-resolved):
three divergences from the provisional plan — (1) the commit ledger stores the FULL TREE
(`git ls-tree -r`), not the diff, so a commit's changed file set is unresolvable → file/doc
endpoints come DIRECTLY from L1 write events (proven), the ledger resolves commit existence +
full-sha only; no fan-out (would be an inferred edge). (2) the L1 commit ref is ABBREVIATED →
prefix-match; 0/>1/empty NAMED (unknown/ambiguous/unparsed-sha). (3) v1 mints C only (no read/cite
endpoint survives L1; F declared-but-unfed). Decisions: sibling `causal_edges.sqlite` (not extend
`reference_edges`); `CausalEdge.pair_cut_sha`; commit→file composition is Δ's `ComposedGraph` job.

**Items 1–2** (`d7c9112`): `core/stores/causal_edges.py` (witness-keyed, replace-per-session-digest
store) + `core/integrator.py` (`INTEGRATOR_SCOPE`, `Integrator`, `IntegrationReport`, `coverage_gauge`).
Born scoped (`build_integrator` asserts conformance). Core stays self-contained — the ledger is read
via a direct `sqlite3.connect`, NOT an `ops` import (ratchet holds 19). Wired as a pinned, model-less
trough job (`INTEGRATE_KIND` in cron + `router._PINNED_KINDS`; launcher handler + housekeeping enqueue
+ `causal_edges.sqlite` reset target; `ChatConfig.integrate_max_per_pass`). Instruments: the standing
C-coverage gauge + the per-pass resolution-parity gauge (`is_fully_accounted`).

**Verified:** full suite **1629 passed / 8 skipped / 1 failed** (the intentional ratchet @ 19) —
green-except-the-ratchet, ratchet held. ruff + mypy clean (0 net; the 69 mypy baseline unchanged).
LIVE smoke over the real corpus: **1599 C-edges**, commit_events=152 (31 resolved; 121 NAMED
unresolved), coverage **93%**, `fully_accounted=True` (0 silent drops). **Next:** Δ = **bp-073**
(re-measure oq-0031 saturation over D3's `ComposedGraph`, which composes these C-edges with the
existing commit→file edges) mints at this seal. Parallel papercut: **bp-072** (owner-cockpit).
Owner `palace deploy` still puts the daemon on HEAD for continuous sensing + integration.

### bp-073 — Phase Δ: connectivity re-measure (the oq-0031 payoff) — COMPLETE (2026-07-19)

Graduates `dn-agent-taxonomy` §3 Phase Δ — the payoff of the Β→Γ→Δ arc. Assembles the composed graph
`{dialogue-artifact docs} × {E_sim ∪ E_proven}` and feeds it UNCHANGED to the ratified σ*/conductance
math to answer oq-0031. **Eval-side, model-free, NO core edit — ratchet held 19.**

**Item 0 — grounding** (`739ecd7`, finding-0112 spec-fidelity/builder-resolved + one owner ruling):
the mirror vectorstore holds only 17 janus_notes, which carry NO C-edges → E_proven is inert over the
mirror. The C-edge-bearing docs (208 of 266) are a disjoint, UNEMBEDDED corpus the mirror firewall
refuses. **Owner ruled A**: embed the dialogue-artifact corpus eval-side (ephemeral, read-only). Q2
(C-edge→node-pair) resolved as **shared-witness co-production** (no commit→file fan-out — finding-0111's
falsifier; no §10 stop). Q4 criterion PINNED before measuring.

**Items 1–2 + 2b** (`6741fcf`): `eval/harness/re_measure.py` — `assemble_composed_graph` (pure/injected:
E_sim = doc cosine ≥ min(grid), reuses `core.dreaming.cluster`; E_proven = witnessed co-production,
fail-loud on a witnessless edge) → `compose()` via `cast(MirrorGraph)`; `re_measure_oq0031` (E_sim-only
vs full, `sigma_star` over BOTH, attributes the delta; `frac_connected_by_sigma` + `n_sigma_uplifted` +
`proven_bridges`); live read-only loaders (`open_causal_edges_ro` mode=ro, `embed_docs` ephemeral). 14
tests. **Item 2b: every corpus handle read-only — a write raises `readonly`; Δ is daemon-safe.**

**LIVE VERDICT** (208 docs, 3700 C-edges → 1068 proven edges, 21528 pairs; finding-0113, owner-blessed):
the 13-doc saturation was **INPUT-STARVATION, not a real ceiling** — at n=208 the connectivity gauge
already discriminates under E_sim alone (frac_connected 1.0→0.004). **E_proven is a real second lever
via σ\*-uplift** (+0.74 at σ=0.7), NOT loose-grid bridging — the pinned bridge-criterion is vacuous on a
corpus E_sim connects at the floor (a measurement-calibration lesson). **Necessary-but-insufficient,
refined.** Honest, not forced (`discriminates=False` stands beside the strong σ*-uplift).

**Findings 0096/0099/0100 RESOLVED** directly by finding-0113; **0097/0098** resolved root-cause
(starvation — optimizer-guard hardening left as a separate future finding); **oq-0031 RETIRED**;
**oq-0024** (σ re-tune) UN-blocked. **Verified:** ratchet held 19; 91 graph/eval + 14 re_measure tests
green; ruff clean. Cost: 179.8k output (0.90×), $21.03 opus, week 19%→20%. **Next:** bp-072
(owner-cockpit, reserved); a fresh σ-sweep on the 208-doc corpus (oq-0024); or deepen Track H.
Diagnostic owed (why the mirror is stuck at 13 notes) — separate open thread.

## 2026-07-19 (session 33, FABLE) — bp-072 MINTED (owner-cockpit, proposed) + usage self-serve probe

**Post-Δ verification:** main in sync with origin @ `486628b`; CI all-green on both post-seal commits
+ a successful `release` dispatch. Nothing owed from session-32.

**bp-072 minted `proposed`** (`docs/build-plans/bp-072/plan.md`, alias owner-cockpit) — the reading
room + decision-routing v1: `cockpit.sh` (idempotent tmux session `palace`), `docket.py` (derived
awaiting-the-owner view + ambient count; front-matter via the hooks `_lib`, DRY), `readmap.py`
(quickfix emitter for a NEW structured ```read-map block — legacy prose seals honestly refused),
owner-run `palace bless <plan-id>` (guard order pinned: CLAUDECODE refusal BEFORE path resolution;
line-targeted flip, no YAML round-trip; no force path), `docs/supplemental/cockpit.md` (snippet
block — dotfiles adopted by hand, never written). **Direct mint from brainstorm, owner-authorized**
(`owner-cockpit.md:10`: "no design-note gate needed for the tooling itself"; decision-routing v1 =
"no governance change"). Blessing stays owner-by-hand — bootstrap self-reference honored: the bless
CLI cannot approve its own creation. Grounded in-session: `CLAUDECODE` env verified live; tmux 3.7b
`focus-events` runtime-settable (settles brainstorm open-Q1 — dotfiles boundary governs FILES);
`.claude/state/` already gitignores the generated docket. Estimate: opus 100k, budget 1.

**Usage self-serve (owner steer, this session):** verified `claude -p "/usage"` renders the full
usage screen headless (session/week/fable %) at ~zero cost — the pre-flight budget gate no longer
needs the owner relay. Captured `docs/brainstorms/usage-automation.md` (process rule effective now;
scheduled ledger PARKED with re-entry); memory updated.

**Next:** owner blesses bp-072 by hand → an OPUS build session; or the oq-0024 σ-sweep (un-blocked);
or deepen Track H. Usage at mint end: session ~52%, week 21%, fable 15%.

---

## 2026-07-19 (session 34, OPUS @ medium) — bp-072 BUILT + SEALED (owner-cockpit, complete)

**Pre-flight:** verified bp-072 `ready` (owner blessed by hand, `7b343b9`), main in sync with
origin. Self-serve budget probe (`claude -p "/usage"`): session 59%, week 22%, fable 17% — a
well-pinned 100k papercut fit the headroom, ran OPUS inline (no fable/xhigh — execution, not design).

**Built (all five deliverables; +21 tests GREEN):**
- `scripts/docket.py` (+`test_docket.py`) — the derived awaiting-the-owner view: proposed plans /
  draft notes / open oqs, NOTHING agent-actionable; recomputed every run (pure fn of the tree ⇒
  cannot drift); `--count` / `--write`. DRY: reuses `_lib` front-matter parser, never imports
  `core` (both AST-enforced). Live: 52 rows, lists oq-0003/oq-0024.
- `scripts/readmap.py` (+`test_readmap.py`) — emits the LAST ```read-map block of a seal journal
  verbatim (authoring format IS output format); legacy prose → exit 1, never guesses (live: bp-073).
- `scripts/palace.py` `bless <id>` (+`test_bless.py`) — owner-only proposed→ready flip; guard order
  LAW (CLAUDECODE refusal BEFORE path resolution — proven live with a fake id, zero flip risk;
  exact-`proposed` only, no force; line-targeted, comments survive byte-identical). Dispatches before
  `seal()`/launcher. Mints no capability; the Stop-gate audit is unchanged.
- `scripts/cockpit.sh` — idempotent tmux `palace`: desk (vim-on-docket | claude) + ops (status +
  daemon log tail, `data/logs/palace.out.log`, never needs the daemon up); status-bar awaiting-count;
  runtime `focus-events`; `$TMUX`-aware join (switch-client inside / attach outside). `--dry-run` is
  the headless-testable surface; `bash -n` clean.
- `docs/supplemental/cockpit.md` — dotfiles snippets (adopted by hand, never written): autoread,
  `<leader>pb`→bless, `:PalaceRead`→readmap→`:cfile`, permanent focus-events line, session-switching
  tips; the guide-not-gate rule VERBATIM; the read-map block format spec.

**Gate:** CI green gate reproduced locally — `pytest -m 'not live and not podman and not needs_vault
and not needs_restic' --deselect test_core_self_containment::test_core_imports_nothing_outside_core`
→ **1648 passed, 4 skipped, 21 deselected**. finding-0103 ratchet unchanged at **19** (core untouched).

**Finding filed:** `finding-0114` (`direction`, routed to orchestrator) — owner-observed `scripts/`
drift (34 files → three drawers: durable entrypoints · spent migrations · eval-flavored harnesses);
a future tidy plan, not acted on mid-build (moving harnesses touches `eval/`, outside scope).

**Seal-time process firsts:** this seal is the FIRST authored in the structured ```read-map block
format (`readmap.py bp-072` will emit it); the **checkpoint** skill gained the read-map cross-ref
(orchestrator act, plan §4); `cost.actual` filled (session 59→63% +4%; week 22→22% <1% = the gate
figure; fable untouched — opus discipline; ~0.8× approx, %-derived).

**Next:** push → verify CI green (routine; docs+scripts, no deploy). Then standing options: oq-0024
σ-sweep (un-blocked), or triage finding-0114 into a `scripts/` tidy plan, or deepen Track H.
Usage at seal: session 63%, week 22%, fable 17%.

---

### bp-078 — the four plane principals (LaunchDaemon + cockpit sudo + pf anchor + verifier + ratchets + runbook)

**Status:** COMPLETE + SEALED (2026-07-20, session-37). Merged `023d36d` (`--no-ff`). Re-graduated
from `dn-plane-principals` (superseding bp-076; warrant finding-0116). Delegated opus@high builder
(worktree), all 6 items; scope clean, orchestrator re-ran the full 6-leg gate before merge.

**What landed (authoring-only — NO live migration; all owner-run from the runbook):** domain/user-aware
`Launcher` (`LaunchDomain` gui↔system axis, gui byte-identical — 36 lifecycle tests) + `ouroboros`
daemon plist + `[planes]` config; cockpit launches the orchestrator as `sudo -u ouroboros-work -H`;
an inert core-egress pf anchor (`block … user ouroboros` + lo0 carve-out); a read-only 4-plane
verifier (`scripts/verify_planes.py`, PENDING-not-false-green); five self-configuring `stat().st_uid`
ratchets (all SKIP pre-migration); the owner-run migration runbook.

**Gate:** re-run green by the orchestrator — ruff · import-firewall · mypy floor 0 · argless 69 ·
type_gate · pytest **1680 passed, 12 skipped, 21 deselected**. 0103 ratchet unchanged.

**Findings:** `finding-0120` (direction/orchestrator) — the Q9 Claude-Code-credential spike; the #10
guardrail denying the credential-store probe IS the answer (a service user's store isn't
agent-reachable), so the empirical bootstrap is inherently owner-run → parked with a clean re-entry,
folded into the runbook STOP-gate. **Real discovery:** `/Users/ascalva` is `0o750` (no `o+x`) → role
accounts can't traverse to repo/vault; remediated in runbook §0.

**Cost:** 261206 tok / 103 tool-calls / 31 min, opus@high (no downgrade). **ratio 1.04×** (dead-on
the 250k estimate — well-pinned). week_delta +1% (33→34%), fable flat.

**Next:** OWNER runs the four-plane migration from `docs/runbooks/plane-migration.md` (§0 traversal
first), resolving finding-0120 at the credential STOP-gate. Standing: finding-0119 bless-ceremony
ruling · finding-0114 scripts tidy · book Architecture /scribe.

---

### plane migration — WORKFLOW plane LANDED (owner-run, 2026-07-20); CORE plane parked

Ran the bp-078 runbook live (owner at the keyboard, orchestrator verifying each step read-only).
**Workflow plane §1–§6 + the cockpit wrapper are DONE and proven:** 4 role users (`ouroboros`,
`ouroboros-work`, `ouroboros-edge`; `ascalva`), `palace` shared group, shared-repo mechanics
(`core.sharedRepository`, setgid, umask), repo-local git signing, sudoers descending grant, and
`scripts/orchestrator-launch.sh` — the cockpit's orchestrator pane now runs as the constrained
`ouroboros-work`, authenticated headlessly and committing **silently Verified** as the human. So
agents run one rung below the human login (no personal files, no vault ambiently). Adopt on the next
`cockpit.sh` restart.

**Findings this arc:** 0120 (Claude credential for a role account) RESOLVED — keychain is a dead end
for a keychain-less role account; `claude setup-token` → `CLAUDE_CODE_OAUTH_TOKEN` keeps subscription
billing, headless. 0122 (git signing gaps + unattended signing) RESOLVED — three access grants +
SSH_ASKPASS silent signing via the wrapper. **0123 OPEN → the CORE plane is PARKED:** the
`ouroboros` daemon (a launchd-at-boot LaunchDaemon) can't get its Vault unseal key from a keychain
(no login keychain, no wrapper seam); §7–§11 (daemon→ouroboros, vault 0700, pf egress) await a design
pass on the headless-daemon secret bootstrap (System keychain / file / hybrid) — likely FABLE.

**Verify surface:** `uv run scripts/verify_planes.py` (read-only) → users/group/repo-tree/signing/
traversal PASS; the vault/exhaust/data/daemon lanes PENDING (the parked core plane). Discovery en
route: `/Users/ascalva` was `0o750` (no o+x) → role accounts couldn't traverse (runbook §0 fix);
+ finding-0121 (no worktree reaper — 7GB of stale trees reclaimed).

---

## Session-39 (2026-07-21) — the dreamer track BUILT + the fiber-geometry synthesis

**Built + sealed: `dn-synchronic-diachronic-dreamer` → bp-079/080/081/082 (all `complete`).**
Four tier-verified opus worktree builders, each independently 6-leg-gated on main by the
orchestrator, `--no-ff` merged single-writer, sealed with `cost.actual`, worktrees removed.
- **bp-079** D-0: the DreamCharter dispatch record (scope⊓dreamer_scope + instrument ceiling +
  budget + gauge) + the single materialization boundary (estimate→refuse-or-force; laziness laws
  L1–L3). 164,590 tok / 0.82× (01e006b).
- **bp-080** D-1: the arrow-read census (influence loops / revision-effort asymmetries /
  reach-backs, each witnessed, gauge-immune) + the census lens on the structural panel behind the
  R&D flag (oq-0021 records-not-causes vocabulary; F-SD9 battery). Census EMPTY on the live corpus
  — fixtures carry. 176,636 tok / 0.71× (cdedfab).
- **bp-081** H-0+H-1: the HYPOTHETICAL stratum + append-only generation-clocked staging store +
  the composed-assembly overlay + the expiry sweep. The no-promotion spine invariant proven
  STRUCTURALLY (API-surface scan). 217,049 tok / 0.87× (8be3c98). Filed **finding-0130**.
- **bp-082** H-2: influence (integer Δσ*/Δcensus with CN-3 attribution + smooth Rayleigh with the
  finite-difference check; one-sided law structural) + the conditioning law (fails closed, F-SD7b;
  taint-split reuses the influence diff). 269,887 tok / 0.96× (3979291). Q3 did NOT fire.
- **Verify:** suite 1707 → **1790 passed**; finding-0103 ratchet held at **19** throughout
  (verified explicitly at the bp-082 seal; interim "22" reports were builder miscounts).
- **⚑ Built DARK:** the whole H-family (staging/overlay/influence/conditioning) is flag-off, NOT
  wired to the live daemon. A future "make the subspace live" plan wires the sweep (finding-0130)
  + the census live-read (dreamer note §2.8) when the owner turns HYPOTHETICAL on (the Track-G
  build-dark pattern). Two build reports placed on the exhaust lane (phone).

**Design output (all pushed):** `dn-synchronic-diachronic-dreamer` **RATIFIED** (owner bless
44bbeec; adopts oq-0021 ADMIT). `dn-inner-outer-core` DRAFT (v2 + S1 licensed, 7a532f0).
`dn-fiber-geometry` DRAFT (fable MAX synthesis, dada719 — one typed graph / three layers;
clock-curvature = Layer 1; sheaf coupling refuted block-diagonal; ML-d declined; the M1–M10
measure-first battery; licenses the G-A survey). Brainstorm captures: hypothetical-subspace,
book-pedagogy (+citations), synchronic-diachronic-dreamer (+laziness, +forecaster),
clock-curvature (4 capsules: metric/GR/dying-cluster/path-invariance), fiber-chain-grammar
(+reasoning-as-proof-path), edge-dynamics-vector-field (3 fields + dynamics).

**Findings this arc:** 0126 RESOLVED (diachronic park's blocker already shipped, closed by the
dreamer ratify). **0130 OPEN** (builder-lane — the staging sweep's scheduler wiring, parked to a
future live-subspace plan). **0140 ROUTED** (the F-letter collision → S/F/D/C alphabet; promotes
on the dn-fiber-geometry ratify). Next finding id **0141**.

**NEXT (design-gated on the owner):** ratify the two draft notes (oq-0032) → then /graduate the
G-A survey + M0/S1. Un-blocked execution meanwhile: oq-0024 σ-sweep + the measure-first readings
(grounds the pending fiber-geometry/clock-curvature passes; several battery rows expected null on
today's thin C-fiber). Book debt: `dn-synchronic-diachronic-dreamer` newly ratified — a /scribe
sync is owed (the sensor→…→dreamer arc).

## 2026-07-21 (session-40) — /graduate the three ratified notes → six `proposed` plans (bp-083..088)

`/graduate` over `inner-outer-core` + `fiber-geometry` + `agentic-loop` (ratified `fbea48d`).
Decomposition + grounding done in ONE orchestrator context (subagent decomposition parked §14);
every seam/instrument re-verified on disk at HEAD `d08da37`. Nothing implemented (A4). Six plans:

- **bp-083 — M0** (`inner-outer-core` §2.4/§2.7-M0): born-green inner ring — `core/rings.py` +
  `tests/unit/test_inner_ring.py`; map RECOMPUTED at build HEAD (Appendix A = expectation, F6);
  additive, outer ratchet untouched. deps: none.
- **bp-084 — S1** (§2.6b): temporal math↔persistence splits, map +7 → 36; four seams relocate one
  ring outward (bp-065 clean-break); zero behavior change; retrofit test files carried. **deps: bp-083.**
- **bp-085 — G-A** (`fiber-geometry` §2.6/§3): the read-only M1–M8 survey, eval-side
  (`eval/harness/fiber_survey.py` + finding); nulls-as-results (C thin/empty expected). deps: none.
- **bp-086 — AL-1** (`agentic-loop` §2.3): IA/EA-p/EA-x profile constructors + the G-D zone-law
  test (`Σ⊓private≠⊥ ⇒ W_world=NONE`, F-AL3); `core/agent_scope.py` + `core/scope.py`. deps: none.
- **bp-087 — AL-2** (§2.8): the owed M-3 (C-coverage) + M-6 (gap baselines) readings → finding;
  read-only, `docs/findings/**` only. deps: none. **fable/~90k.**
- **bp-088 — AL-3** (§2.4b): `exhaust ⊂ dialogue` excluded refinement (F-AL6) + the `origin(e)`
  derived view (F-AL7, no store/no minted rows); `core/scope.py` + `core/origin_view.py`.
  **deps: bp-086** (shared `core/scope.py`).

**Owner steer (session-40 brief):** graduate the READ-ONLY measurement plans (G-A, AL-2) with
priority — they generate the data the parked §5/taste questions need; leave those questions OPEN.
M0/S1/AL-1/AL-3 are the additive/born-green builds. Parallelism: bp-083/085/086/087 have disjoint
write scopes (parallelizable); bp-084 after bp-083; bp-088 after bp-086 (both write `core/scope.py`).

**NEXT (owner):** bless `proposed → ready` by hand (lazygit), then delegated `/build` per plan
(pre-flight `/usage`; priority G-A + AL-2). Book debt unchanged (dreamer /scribe sync still owed).

### 2026-07-21 (session-40) — bp-087 (AL-2) SEALED: the owed M-3/M-6 baselines recorded

First delegated build of the graduation wave landed. AL-2 (sonnet, 98k tok / 87 calls / 9 min,
ratio 1.09× — I re-tiered fable→sonnet at spawn: read-only measurement, no reasoning depth).
Read-only over live `data/`; merged `3f983a3`; `finding-0143` filed (`ftype: discovery`, direction).

**Baselines (delta anchors for the next AL pass) — recorded HERE, NOT in the ratified §2.8 (A8):**
- **M-3 C-coverage = 0.8996** (witnessed 4,084 / integrable 4,540; unwitnessed 456). The gauge's
  first reading (note had "built, not taken"). Cross-check: 4,084 == §2.8 M-2's C-edge count. ✓
- **M-6a holes = 0** (real-zero at `min_persistence=0.15`; 19 authored notes → 19×19 cosine matrix,
  full vault, not truncated).
- **M-6b doc_coverage = 0.3391** (1,008,484 / 2,973,708 symbols; 883 commits). Cross-check: matches
  the live code-sensor's 33.92%. ✓
- **M-6c drift-vs-anchor = DEFERRED** — needs a live `Retriever` (embedding model, non-negotiable
  #8), not a store read; re-enters on a daemon-attached session (finding-0143 §Re-entry).

**PD-3 precondition** (M-6 baselines recorded) now satisfied for a/b; c still owed. **Note the
A8 correction:** the builder suggested checkpointing into `dn-agentic-loop` §2.8's table — declined,
the note is ratified/immutable; the finding + this entry are the durable record. Any §2.8 refresh is
a future owner-gated amendment, not an orchestrator edit.

**Board:** bp-085 (G-A) still building (background). bp-083/086 held for sequenced merge; bp-084
after 083, bp-088 after 086.

### 2026-07-21 (session-40) — bp-086 (AL-1) SEALED: the actor profiles + the zone law (G-D)

Second build landed. AL-1 (opus, 150k tok / 69 calls / 20 min, ratio 0.68× — UNDER estimate).
Adopted `9774bd7` by **file-checkout, not git-merge** (the builder's worktree branched from the
stale session-start `d08da37`, so a merge would have reverted the intervening AL-2/brainstorm
commits — the 5 write_scope files were byte-identical at its base, so their final content applied
cleanly). Verified on main: ruff + check_imports (pure-core) + mypy(2 files) + 64 scope tests green.

- **`internal_actor` / `external_proposer` / `external_executor`** in `core/agent_scope.py`; the
  zone law **`PRIVATE_STRATA` + `zone_admissible`** in `core/scope.py` (cross-coordinate, NOT an
  `Ideal`). **F-AL3 CRUX PASSED**: `test_zone_law_REFUSES_a_constructable_private_read_with_world_reach`
  — a hand-built ⊤_Σ + W_world=SENSING grant is structurally refused. The §2.3 derivation is a
  ratchet, not decorative. No stop-and-raise, no design finding.
- **Owner question flagged (parked, non-blocking):** `PRIVATE_STRATA` ships as ⊤_Σ ∖ {world}
  (widest-exclusion, strongest law); whether `ops`/`reference` count as "private" is the owner's
  call — pinned in the code comment + `test_private_strata_membership_is_pinned` guards drift.

**Unblocks AL-3 (bp-088)** — but bp-088 adds the exhaust refinement to `core/scope.py`, which AL-1
just changed. Its worktree (if stale-based at d08da37) will build against the pre-AL-1 scope.py, so
AL-3 must be adopted by **diff-apply** (its enum/refinement region vs AL-1's PRIVATE_STRATA region
don't overlap) or spawned on post-AL-1 main — NOT whole-file checkout (would revert AL-1). Hold AL-3
until M0+G-A land.

**Board:** bp-087 complete, bp-086 complete. bp-085 (G-A) + bp-083 (M0) still building. bp-084 after
M0; bp-088 after this (with the diff-apply caveat).

### 2026-07-21 (session-40) — bp-083 (M0) SEALED: the born-green inner ring

Third build landed. M0 (opus, 98k tok / 65 calls / 42 min, ratio 0.39× — born-green additive is
cheap; duration inflated by full-suite CPU contention). Adopted `33d6929` by file-checkout (base
`4212306`, an ancestor of main — clean); re-verified born-green at post-AL-1 HEAD (AL-1's pure-core
scope.py additions did NOT shift membership — 4 tests passed).

- **`|INNER| = 30`** = Appendix A's 29 + `core.rings` itself (stdlib-only ⇒ computes inner ⇒ B1
  forces self-declaration). The computed 29 was **byte-identical to Appendix A** even though core/
  grew 135→141 modules since `97c245c` — the ring held; **F6 satisfied by construction** (no
  hand-edit toward green). `core/__init__.py` confirmed import-free (+ a new `test_core_init_is_
  import_free` guard). Outer ratchet unchanged at 19.
- Builder honesty flag (noted, moot): a hook created an intermediate `feat(...)` commit on its
  worktree branch; irrelevant — I adopted file content onto main, not the branch topology.

**Unblocks S1 (bp-084)** — the +7 promotion wave, which diffs against this `INNER` map. S1 NEEDS
core/rings.py present ⇒ run it against post-M0 main (non-isolated, or a worktree confirmed to
include `33d6929`), NOT a stale worktree.

**Board:** bp-083/086/087 complete (M0, AL-1, AL-2). **bp-085 (G-A) still building** (only builder
left). bp-084 (S1, after M0) + bp-088 (AL-3, after AL-1) held until G-A lands — run sequentially,
non-isolated, to guarantee they see the dependency's output + keep concurrency ≤2.

### 2026-07-21 (session-40) — bp-085 (G-A) SEALED: the fiber-geometry survey; the WHOLE WAVE'S 4 independent plans done

Fourth build landed — the four independent (parallelizable) plans of the graduation wave are all
sealed. G-A (opus, 218k tok / 143 calls / 59 min, ratio 0.87× — the largest build). Adopted
`978b073` by file-checkout; verified on main (ruff/imports/mypy + 9/9 survey tests green). `finding-
0142` filed (discovery, direction → orchestrator).

**Survey results (live @ HEAD, grid (0.55,0.65,0.75), each CN-1-indexed) — nulls ARE results:**
- **M1:** C = 237 nodes / 1193 edges; F = 207 / 593; D = 19 docs / 16 arcs (vault space, disjoint).
  F∩C Jaccard **0.40** (126 shared nodes); C|D = F|D = 0 (D disjoint — a measured fact).
- **M3:** D-triangles = **0** → covering-only supersession integrity CLEAN (stop-and-raise did NOT fire).
- **M6:** χ_s instrument-blocked (needs a live Spine — a daemon op, not read-only-buildable).
- **M2/M4/M5/M7/M8 DEFERRED:** all need cosines (S rows). The eval embedder trips the 120s timeout
  because it shares the memory-ceiling'd ollama with the live daemon (bright line 8); the survey
  degrades gracefully rather than evict the daemon. Re-entry: re-run with embed headroom (daemon
  down / a dedicated pass). This is environmental, by-design — NOT a plan defect.

**⚑ DIRECTION FLAG for /triage (finding-0142, no A8 edit):** the note's premise "C live census
empty at bp-080 seal" (dn-fiber-geometry §2.0/§2.5) has **MOVED** — C is now a populated fiber
(1193 edges). This partially satisfies PD-a re-entry condition 1 (support non-degenerate); condition
2 (content) still needs the deferred M2. Worth an owner-visible note-amendment candidate at the next
fiber pass — parked to /triage, not edited now.

**Board:** bp-083/085/086/087 COMPLETE. Remaining: **bp-084 (S1, after M0)** + **bp-088 (AL-3,
after AL-1)** — the two dependents. Main is now quiet (no builders). Run them SEQUENTIALLY,
NON-ISOLATED on current main (guarantees S1 sees core/rings.py, AL-3 sees AL-1's core/scope.py;
avoids the stale-worktree base + main-HEAD race). S1 next (critical path, the +7 promotion wave).

### 2026-07-21 (session-40) — bp-084 (S1) STOP-AND-RAISE → superseded by bp-089 (my graduation defect)

The delegated S1 builder did the disciplined thing: ran the read-only DRY audit (Item 3), found
the plan's `write_scope` **cannot deliver the atomic +7**, STOPPED CLEAN (no code written, tree
pristine), and filed `finding-0144` (spec-fidelity → orchestrator). The defect is MINE (graduation):
1. Missed `core/temporal_view.py` (`:56/:187/:340/:348`) + `core/temporal/__init__.py` (`:18,22,50,69`)
   as importers of the moved symbols — the retrofit scan covered only `tests/`. Clean-break repoint
   needs them in scope.
2. Missed `core/stores/claim_ops.py` — the DRY audit found NO existing store covers `claim_ops`
   (`authored_supersession` distinct; `versions` is note-version supersession). New store needed;
   `core/stores/**` was out of scope.
3. +7 named `core.integrator` where the executable promotion is **`core.integrator_math`** (new
   inner module; `core.integrator` keeps the `ledger:sqlite3.Connection` + out-of-scope importers
   `scheduler/cron.py:39`, `ops/lifecycle/launcher.py:238`, stays OUTER). Final `|INNER|=37`.

**Remediation (supersession, not in-place edit):** minted **bp-089** (S1′, `proposed`) with the 3
`write_scope` additions + the naming fix, warrant `finding-0144`, supersedes bp-084. bp-084 →
`superseded` (superseded_by bp-089), kept inspectable. **Needs owner `proposed → ready` blessing**
before build. The `dn-inner-outer-core` §2.6b design is UNCHANGED (A8 — the ratified note's Appendix
A named core.integrator; bp-089 carries the executable correction, note untouched).

**Board:** bp-083/085/086/087 complete; bp-084 superseded; **bp-089 proposed (needs blessing)**;
bp-088 (AL-3) ready, still queued. Wave: 4/6 built; S1 re-graduated; AL-3 remains.

### 2026-07-21 (session-40) — bp-088 (AL-3) SEALED: exhaust refinement + origin(e) view

Fifth build landed. AL-3 (opus, 163k tok / 72 calls / 22 min, ratio 0.54× — under). Adopted
`9e9555f` by file-checkout (builder merged main first, base cea89b7 — AL-1's scope.py present);
verified on main (ruff/imports/mypy + 76 scope/origin tests green).

- **Item 16 — `exhaust ⊂ dialogue` EXCLUDED refinement:** `Stratum.EXHAUST` + `_EXCLUDED_REFINEMENTS`;
  `_downward_close` keeps named strata verbatim, auto-adds only non-excluded refinements. **F-AL6
  holds** — `top()`/`of(DIALOGUE)` exclude EXHAUST, admitted only when named; ⊤_Σ byte-identical,
  PRIVATE_STRATA unchanged (AL-1's zone law still green).
- **Item 17 — `origin(e)` view** (`core/origin_view.py`, new): regenerable two-hop join C∘commit-
  keying; **F-AL7 holds** (reproducible from witnesses+commit keys, no store, E_disp); scoped to
  X_cite ids carrying `commit_sha` (working-tree C-edges with empty pair_cut_sha out of domain,
  PD-8 parks row-grain).
- **Builder caught a plan imprecision (no finding, correctly resolved):** my §7 Item 16 acceptance
  (iv) `of(EXHAUST) ⊑ of(DIALOGUE)` self-contradicts the exclusion crux (excluded ⇒ not in the
  downset ⇒ ⋢). The builder implemented the exclusion (the ratified note's safety property) and
  pinned the genuine order `of(EXHAUST) ⊑ of(DIALOGUE, EXHAUST)` + the load-bearing non-order
  `of(EXHAUST) ⋢ of(DIALOGUE)`. Aligned to dn-agentic-loop §2.4b EX-1(ii). Sound.

**⚑ WAVE: 5 of 6 BUILT (AL-2·AL-1·M0·G-A·AL-3). Only S1 (bp-089) remains** — `ready` (owner blessed
`85c80cc`), HELD on budget (session 77%, binding) until spawnable alone. No other plan pending.

### 2026-07-21 (session-40) — bp-089 (S1′) SEALED: the +7 promotion wave — ⚑ GRADUATION WAVE COMPLETE

Sixth and final build. S1′ (opus, 164k tok / 101 calls / 26 min, ratio 0.51× — under; ran on the
fresh post-3:20pm session pool, alone, no contention). Adopted `d8d9d09` by file-checkout; the full
gate verified on main: ruff · check_imports (core purity — the crux) · mypy 243 files · argless
mypy **69** · type_gate · 80 acceptance tests green.

- **`|INNER| = 37`** (30 → +7). Promoted: `core.integrator_math` (NEW pure gauge home),
  `core.recursion_ops`, `core.temporal` + `.boundary`/`.complex`/`.operators`/`.superconnection`.
  `core.integrator` correctly STAYS OUTER (keeps the sqlite `ledger`). **F10 clean** (computed −
  declared = exactly +7). **Zero behavior change** (seams moved verbatim; purity re-confirmed).
  **Outer ratchet unchanged at 19.** No new graduation defect — bp-089's corrected write_scope held.
- New files: `core/temporal/acquire.py`, `core/integrator_math.py`, `core/stores/claim_ops.py`.

## ⚑⚑ THE GRADUATION WAVE IS COMPLETE — all 6 licensed plans built (bp-084 superseded→bp-089)
The three ratified notes (inner-outer-core · fiber-geometry · agentic-loop) are fully graduated AND
built: **M0** (born-green ring) · **S1** (temporal +7 → INNER 37) · **G-A** (fiber survey) · **AL-1**
(actor profiles + zone law) · **AL-2** (C-coverage/gap baselines) · **AL-3** (exhaust refinement +
origin view). Sealed costs 0.39–1.09× (all ≤ estimate except AL-2's 1.09×). Pushed to origin.

**/triage backlog (not this session):** finding-0142 (C-fiber premise moved — note-amendment
candidate) · G-A's deferred S-rows (M2/M4/M5/M8 — re-run with embed headroom) · AL-1's PRIVATE_STRATA
owner-Q · the dreamer /scribe book-sync. **M1 riders now available** (packaging remedies + the
sigma_star/conductance math split can grow INNER further, each carrying its ring-map delta).

## 2026-07-22 — session-42: the workflow track built (WF-1 + WF-2)

Graduated `dn-track-board-and-deskcheck-gate` → **bp-096 (WF-1 board substrate)** + **bp-097 (WF-2
deskcheck gate)**; owner blessed both; built in **parallel** delegated worktrees (opus, tier-verified
via transcript), full attestable-green gate each, merged to main (`d7e6128`, `ee94e67`) and sealed
complete. Owner hand-tagged the 6 ratified active-track notes with `track:` (`5d0d1ba`) — the
accountable channel for A8-immutable notes, keeping D1's self-declaration pure. The board is now
DERIVED (`scripts/board.py` → TRACKS.md + DESKCHECK-QUEUE.md, no persisted state); the third
owner-only gate (deskcheck verdict) + clause (f) seal-follow-through + the new clause-(b2)
owner-staged yield are live on merge. **finding-0155** (P-WF1 probe: model id reachable indirectly
via `transcript_path`) → oq-0033. Deskcheck queue now **6** (workflow track joined). The workflow
track is DONE-not-CLOSED — it owes its own deskcheck. **Next:** budget re-probe → inner/outer core
(bp-090 K1) if usage remains.

**bp-090 (K1) DONE + sealed** (delegated builder, opus, uninterrupted): the born inner ring
relocated to `core/kernel/**` — 29 `git mv` + 455 import repoints across 215 files, kernel map
recomputed to 42, K1 import-closure = 0 external, outer ratchet 19 unchanged (move-neutral). Merged
(`0b65542`); combined tree (K1 + WF-1/WF-2) re-verified green by the orchestrator: ruff · mypy 249 ·
argless mypy = 69 · type_gate · CI pytest 1853 passed/11 skipped/21 deselected. No findings; two
refinements journaled (config/matching are full moves not splits; two `__file__` REPO_ROOT
re-anchors needed — a K3 lesson). inner-outer-core track owes its deskcheck (M0+S1+K1). **Next:**
bp-091 (K3, the S1 seven) after K1 — budget permitting.

**bp-091 (K3) DONE + sealed** (delegated builder, opus): the seven S1 modules
(`integrator_math`, `recursion_ops`, `temporal` + 4 pure math) relocated into `core/kernel/**` —
7 `git mv` + 15 repoints, kernel map 42→43, outer ratchet 19 unchanged (move-neutral), zero
behavior change. Merged (`5ecbd01`); orchestrator re-verified: ruff · mypy 250 · argless mypy = 69 ·
type_gate · CI pytest 1853 passed/11 skipped/21 deselected; inner ring computed==declared==43. No
findings; the K1 `__file__` hazard did NOT recur (none of the seven compute a repo root). Process
note: the builder briefly ran Bash in the shared main checkout, caught it, stashed the stray work
(`stash@{0}`, recoverable) and redid it cleanly in the worktree — main stayed pristine. **K1+K3 done;
inner-outer-core owes its deskcheck (M0+S1+K1+K3). Stopped before the CI wave (owner go needed).**

**CI wave started (owner-authorized 2026-07-22); the `pages` CI drift fixed en route.** bp-092 (CI-1)
sealed; separately, the `pages` (mkdocs) workflow — red since K3 — was fixed (8 API refs repointed to
`core.kernel.*`, `98bc7b2`), and finding-0157 filed on the process gap (mkdocs not in the local gate;
refs outside the mover's scope). Deployed v1.16.0.

**bp-092 (CI-1) DONE + sealed** (delegated, opus, 286k = 0.52× the 550k estimate): the three-layer
code embed lane — L0a/L0b/L1 chunkers, structurally-minted `Provenance.CODE` (mirror-excluded, no
provenance parameter — F-CI1), vectorstore `layer`+fiber columns (row/vector-preserving rebuild),
blob-sha incremental + the `code_sync` scheduler KIND, ledger captures (end_lineno/comments/
import_records), F-CI1/F-CI5 ratchets. 37 new tests. Merged (`f8b0fa6`); combined tree re-verified
green (ruff · mypy 252 · argless 69 · type_gate · CI pytest 1881 passed). **DORMANT BY DESIGN** —
`[code_ingest].enabled=false`, not auto-enqueued; the live seed run + M-C1/M-C2/M-C8 readings PARK for
an owner-visible idle daemon run (the deskcheck subject). Two mid-build drift fixes (finding-0156,
resolved): write_scope `core/provenance.py`→kernel (`dcd79c6`) + carried the φ_code pin test
(`bfa321b`), and the φ_code source hash re-pinned same-version as a verified declared refactor
(`f8b0fa6`). **Next:** bp-093 + bp-094 (both dep 092, now unblocked) → bp-095; budget permitting.

**bp-093 (CI-2) DONE + sealed** (delegated, opus, 176k): the retrieval/geometry proof machinery —
M-C3/M-C4/M-C5 battery + CN-1 ReadingIndex + 15 golden code probes (read via `provenances={CODE}`,
never the mirror). 15 new tests. Merged (`4653cf8`); re-verified green (ruff · mypy 254 · argless 69 ·
type_gate · CI pytest 1895 passed). **Parked with re-entry:** the NUMERIC M-C3/M-C4 verdicts need
real qwen3 embeddings — they park with bp-092's owner-visible seed run (re-entry: run mc3/mc4 on the
seeded store; they gate CI-4/PD-C); M-C5 recorded (synthetic, embedder-independent). No findings.
bp-094 (CI-3) still building in parallel. **Next:** seal bp-094 (verify its φ_code attestation) → bp-095.
