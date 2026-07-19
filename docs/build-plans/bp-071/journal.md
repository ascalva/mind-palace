# Journal — bp-071 (Phase Γ: the first full integrator — chat↔code↔doc proven edges)

## 2026-07-18 (session-28, FABLE) — minted (proposed) AHEAD of its inputs; Item 0 = re-ground
Graduates dn-agent-taxonomy §2.5. Deliberately minted charter-form so the owner sees the whole
diamond: §2/§6 are PROVISIONAL until bp-069 lands the L1 schema — Item 0 re-grounds against landed
reality before any code (stop-and-raise if L1 can't name what resolution needs). Born scoped
(`integrator_scope`: (DIALOGUE,L1)+(OBSERVED,commit-ledger)+(DIALOGUE_ARTIFACT,*) read; {C,F}
write), witness-keyed idempotent, pair-cut on every edge, C-coverage + resolution-parity gauges,
never a time-join. `depends_on: [bp-069, bp-070]`. Bless after Β (recommended).

## 2026-07-19 (session-31, OPUS) — Item 0 RE-GROUND complete; plan §3/§6/§8/§11 amended; finding-0111
Read the whole §2 manifest against LANDED reality: `core/chat_events.py` + `core/stores/chat_events.py`
(bp-069 L1), `core/agent_scope.py` + `core/scope.py` (bp-070 scope: `integrator_scope`,
`assert_conforms`, `Fiber=Literal["F","D","C"]`, `Clock.COMMIT`, DIALOGUE/OBSERVED strata),
`ops/code_sensor.py` + `ops/code_snapshot.py` (the commit ledger `code_snapshots.sqlite`:
snapshots/files/symbols), `core/stores/code_observations.py`, `core/stores/reference_edges.py`.

**Three divergences found (finding-0111, spec-fidelity, builder-resolved — no owner):**
1. **Ledger is FULL TREE, not diff** (`_py_blobs` = `git ls-tree -r`). A commit's *changed* file set
   is unresolvable from any store → the §10 "cannot resolve a SHA's file set" trip. REDESIGN (stays
   in charter): file/doc endpoints come DIRECTLY from L1 `file_edit`/`build_plan`/`finding`/
   `design_note` events (each a proven Write tool record); the ledger resolves commit EXISTENCE +
   full-sha ONLY. No fan-out (fanning to the tree = inferred edge = the falsifier). commit→file
   composition is Δ's `ComposedGraph` job (C≠D composition), not the integrator's.
2. **L1 commit ref is ABBREVIATED** (`[branch abc1234]`, `[0-9a-f]{7,40}`); ledger key is full 40-char.
   Resolve by PREFIX-match; 0/>1/empty → NAMED (`unknown`/`ambiguous`/`unparsed-sha`), never dropped.
3. **v1 mints C only.** Landed L1 emits a structural ref ONLY for writes/commits (a read → `tool_use`,
   no path) — no read/cite endpoint survives L1. F stays in scope (declared) but unfed; the write
   handle claims fiber "C" (conformance: actual ⊑ declared).

**Decisions recorded:** extend-vs-sibling → **sibling** `causal_edges.sqlite` (reference_edges is
φ_code's balance-isolated exclusive store; a 2nd writer breaks its sole-interpreter invariant; DRY =
reuse the SHAPE not the table). C/F → C only (above). CausalEdge gains `pair_cut_sha` (so the
(digest, sha) cut rides file/doc edges too — "" when no commit anchor). Idempotency = replace-per-
session-digest (the landed L1 `replace_session` pattern) + `causal_edge_digests` sidecar.

**The L1 schema NAMES everything resolution needs** (session, order, kind, ref, turn_index +
`digest_for`) → NO stop-and-raise. dst_type INHERITS the L1 kind (sensor already classified — DRY
by construction, no re-parse). Next: Item 1.

## 2026-07-19 (session-31, OPUS) — Item 1 DONE: edge store + resolver (26 tests green, ratchet 19)
Built `core/stores/causal_edges.py` (`CausalEdge` + `CausalEdgeStore`) and `core/integrator.py`
(`INTEGRATOR_SCOPE` + `Integrator` + `IntegrationReport` + `build_integrator`).
- **Store:** content-derived `edge_id` over (witness_digest, event_order, dst_type, dst); closed
  vocab validated at `mint` (fiber∈{C,F}, dst_type∈{commit,file,doc}); replace-per-session-digest +
  `causal_edge_digests` sidecar (the landed L1 pattern). `replace_session` ASSERTS every edge
  belongs to the key session (fail-loud — a mismatch would orphan a row past the keyed DELETE; this
  surfaced via a buggy test helper and is now a pinned invariant + test).
- **Resolver:** commit event → ledger prefix-match (unparsed/unknown/ambiguous NAMED, never dropped);
  write events (file_edit→file, build_plan/finding/design_note→doc) mint directly, pair_cut_sha="";
  every other kind counted `non_integrable`. `IntegrationReport` carries the C-coverage + parity
  gauges' substrate (`coverage`, `is_fully_accounted`, `integrable_events`).
- **CORE SELF-CONTAINMENT (finding-0103):** the ledger read must NOT import `ops` (the scanner walks
  function-level imports too — an `ops` import would bump the ratchet 19→20). `build_integrator`
  opens `code_snapshots.sqlite` via a DIRECT `sqlite3.connect` (a file read, not an import reach);
  `_resolve_commit` tolerates a missing `snapshots` table (names every sha unknown — the daemon may
  integrate before the first code-sensor sync). **Ratchet confirmed still 19; neither new module
  appears in the violation list.**
- **Born scoped (D2):** `build_integrator` asserts `assert_conforms(INTEGRATOR_SCOPE, inventory)`;
  tests prove conformance passes AND rejects a smuggled fiber-D handle + an out-of-Σ stratum.
- ruff + mypy clean on both modules. Next: Item 2 — daemon wiring (cron INTEGRATE_KIND + launcher
  reset target + multi-watcher/housekeeping enqueue) + the two gauges as instrument fns + live smoke.

## 2026-07-19 (session-31, OPUS) — Item 2 DONE: daemon wiring + instruments + LIVE SMOKE
Wired the integrator as a pinned, model-less trough job (the `chat_events` sibling):
- `scheduler/cron.py`: `INTEGRATE_KIND="integrate"` + `integrate_handler` + `enqueue_integrate`
  (BACKGROUND priority; Integrator injected, TYPE_CHECKING import — no runtime core import into
  scheduler's own space beyond the injected handle).
- `scheduler/router.py`: `"integrate"` added to `_PINNED_KINDS` (pinned tier, never evicts a slot).
- `ops/lifecycle/launcher.py`: handler wired into `build_components` (`build_integrator(cfg)`,
  `max_per_pass=cfg.chat.integrate_max_per_pass`); `enqueue_integrate` in `_housekeeping` (one tick
  behind `chat_events`, which produces the L1 it reads); `causal_edges.sqlite` added to
  `reset_targets()` (corpus-side, rebuilt by re-integration — the floor invariant).
- `core/config/loader.py` + `config/defaults.toml`: `ChatConfig.integrate_max_per_pass=50` (plain
  field — ratchet stays 19).
- **Instruments:** `coverage_gauge(events, edges) -> CoverageGauge` (standing C-coverage over the two
  stores — integrable/witnessed/unwitnessed/coverage); the resolution-parity gauge is
  `IntegrationReport.is_fully_accounted` (per-pass, by-reason).

**LIVE SMOKE (real corpus, `build_integrator().integrate(max_sessions=1000)`):** 55 sessions,
**1599 edges minted** (>0 ✓), commit_events=152 (resolved 31; NAMED: 112 unparsed-sha + 9
unknown-sha), write_events=1568, non_integrable=5430, **coverage 93.0%, fully_accounted=True**
(0 silent drops ✓). Standing gauge agrees (integrable=1720, witnessed=1599). The high unparsed-sha
count is EXPECTED + honest: `_tool_event` types any Bash containing "git commit" as a commit event,
so failed/hook-rejected/help-text invocations have no sha in their result → NAMED, never dropped
(not an integrator defect; the sensor's L1 is consumed as-is per §9 non-goal). NO finding filed —
the behavior is correct.

**Tests:** `test_integrator_wiring.py` (pinned tier + background + handler summary + coverage gauge
+ parity gauge) green; targeted set (wiring+cron+lifecycle+item1+config+chat_events) all green;
ruff + mypy clean across all changed files; ratchet confirmed still 19. Full suite running (Item-1
state was 1624p/8s/1-ratchet). Next: seal (Item 2 done → all items complete).

## 2026-07-19 (session-31, OPUS) — SEALED. Phase Γ complete: the first full integrator (Items 0–2)
All three items done in ONE OPUS session (budget was 2). Full suite **1629 passed / 8 skipped / 1
failed** (the intentional self-containment ratchet @ 19) — green-except-the-ratchet, ratchet held.
ruff + mypy clean (0 net mypy — the 69 baseline unchanged). Two commits: `e1d4741` (Item 0
re-ground + finding-0111) + `d7c9112` (the integrator: store/resolver/wiring/instruments). Live
smoke over the real corpus: 1599 C-edges, coverage 93%, fully_accounted=True (0 silent drops).

### READ MAP (the ~20% of the diff that carries the concept — read these, skip the rest)
1. **The witness law made concrete** — `core/integrator.py:_resolve_session` (the two-species
   resolver: commit→ledger-prefix vs write→direct) + `_resolve_commit` (prefix match; unresolvable
   NAMED). This is finding-0111's whole redesign in ~40 lines: each edge is the image of ONE L1
   tool record, never a fan-out.
2. **The edge shape + pair-cut** — `core/stores/causal_edges.py:CausalEdge` (fields) +
   `_edge_id` (witness-keyed identity). `pair_cut_sha` is the (digest, sha) cut riding every commit
   edge; "" for working-tree writes.
3. **Born scoped** — `core/integrator.py:INTEGRATOR_SCOPE` + `Integrator.handle_inventory` +
   `build_integrator`'s `assert_conforms` call. The conformance seam (D2) in one place.
4. **The instruments** — `core/integrator.py:IntegrationReport.is_fully_accounted`/`coverage` (the
   parity + C-coverage gauges) + `coverage_gauge` (the standing view).
5. **Core-self-containment discipline** — `build_integrator`'s comment + direct `sqlite3.connect`
   (why the ledger is NOT an `ops` import; ratchet 19).
6. **The wiring pattern** — `scheduler/cron.py:integrate_handler`/`enqueue_integrate` +
   `ops/lifecycle/launcher.py` (handler + `_housekeeping` enqueue + reset target). Mirrors
   `chat_events` exactly.
7. **The re-ground record** — `docs/findings/finding-0111.md` (the three divergences + the
   extend-vs-sibling decision) — the design story behind all of the above.

### Cost
- estimate: opus, 180k tokens. actual: FILLED at seal (owner /usage relay) — see plan front-matter.

### Downstream (unchanged by the build)
Δ (bp-073) re-measures oq-0031 saturation over D3's `ComposedGraph`, which composes these C-edges
(action→commit) with the existing commit→file edges. bp-072 (owner-cockpit) still a parallel papercut.
