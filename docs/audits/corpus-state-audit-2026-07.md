# Corpus-state audit — design/research corpus vs. implementation reality (2026-07-06)

**Type:** read-only reconciliation audit. **Scope:** every note in
`docs/design-notes/` (incl. `build-plans/`) and `docs/research/`, reconciled against
`core/ edge/ ops/ eval/ scripts/ tests/` and the tracking record
(`docs/PROGRESS.md`, `docs/ROADMAP-V1.md`, archive PROGRESS, findings, owner-questions).
**Nothing was implemented, no note was edited, no status was flipped.** Writes made
by this pass: this file, and `docs/findings/finding-0010`…`finding-0017`.

## Method & ground rule

Every status claim below cites CODE or TESTS (`path:line`), never a note's own prose.
Three facts are held distinct throughout:

- **EXISTS** — implementing code is present.
- **TESTED** — a test exercises it.
- **WIRED** — a live-path call site actually invokes it in the default/live config.

`PRESENT-BUT-NOT-WIRED` = whole but disconnected (code exists, nothing live calls it,
often behind an off-by-default flag). `PARTIAL` = the piece itself is incomplete. These
are not conflated.

**The live path** (what "wired" means here). `scripts/palace.py start` →
`ops/lifecycle/launcher.py build_launcher()`/`build_components()` wires the daemon:
vault-sync + watcher, the Ambassador inbox, the delegated-task worker, and the
trough dream/curate handlers on one supervisor (`launcher.py:66-170`). Other live
entries: `scripts/ingest.py`, `scripts/talk.py`, `scripts/watch.py`,
`scripts/monitor.py`, `scripts/verdict.py`. Two wiring facts shaped this audit:

1. **`core/runtime.py bootstrap()` is NOT on the live path** — it is called only by
   `tests/e2e/test_ollama_live.py`. The live egress seal comes from direct `seal()`
   calls in each entry script (`palace.py:37`, `ingest.py:21`, `talk.py:109`,
   `watch.py:27`). Invariant 1 holds; the documented entrypoint is dead (finding-0016).
2. **The flag posture is safe-by-default.** `config/defaults.toml` ships
   `effectors`, `attestation` (enforcement), `secrets`, `backup`, `dream_rnd`,
   `selfmod`, `monitor` all `enabled = false`. This deployment's `config/local.toml`
   additionally flips **secrets** and **backup** on — but *not* attestation, effectors,
   dream_rnd, selfmod, or monitor. Where "wired" depends on config, this is noted per row.

## Executive summary

Of 41 notes: **10 BUILT & WIRED**, **6 PRESENT-BUT-NOT-WIRED**, **14 PARTIAL**,
**4 NOT BUILT**, **5 N/A-DESIGN-ONLY**, **2 build-plans EXECUTED** (both with stale
status lines).

Two structural patterns dominate:

- **A large, well-tested "advanced" layer is deliberately flag-off and unwired** — the
  effectors/hands (max live tier = *none*, not even sensing), the reasoning-complex /
  recursion, the dream-R&D interpreter panel, vault-runtime-auth, the sandbox executor,
  the observed/IoT correlator. This is by design (safe-by-default) and the notes largely
  self-declare it — but the *tracking record* in places implies more is live than is
  (findings 0011, 0012, 0016).
- **Metadata drift** — a cohort of notes labelled "design only" / "not implemented" /
  "DRAFT — pending reconciliation" badly understate code that is built, tested, and in
  several cases wired (finding-0010). §4 proposes the completed-format front-matter for
  the BUILT & WIRED subset.

The live, wired spine is real and healthy: the sealed-core egress guard, the ingest /
vault-sync / amendment / versioning path, the Ambassador (end-to-end), the trough
dreamer (v1, grounding-checked), the verdict authority + transport, the edge-partition
(E_geom ⊔ E_disp), the attestation *records* layer, the workflow machinery, and the
foundation denylist.

---

## 1. Summary table

Impl-state key: **B&W** BUILT & WIRED · **PNW** PRESENT-BUT-NOT-WIRED · **PARTIAL** ·
**NOT BUILT** · **N/A** N/A-DESIGN-ONLY · **EXEC** build-plan executed.

| # | Note | Self-status | State | Key evidence (path:line) |
|---|------|-------------|-------|--------------------------|
| **Cluster A — sacred boundary / edge** |
| 1 | the-sacred-boundary.md | DRAFT — pending reconciliation | N/A | spine/index; properties piecewise (verdict `core/verdict/`, append-only `core/stores/versions.py`, gate `ops/effect_gate.py:132`) |
| 2 | the-edge-model.md | DRAFT — pending reconciliation | **B&W** | E_geom⊔E_disp partition `core/complex/build.py:139-152`, live via dreamer `core/dreaming/interpreters.py:249`; §3 authority = store-identity not a field (`core/stores/edges.py:61-72`) |
| 3 | build-plans/sacred-boundary-build-plan.md | "Item 6 PLANNING ONLY" | **EXEC** (status stale) | Item 6 `core/stores/versions.py` wired `core/ingest/sync.py:111`; contradicts its own line 707 |
| 4 | build-plans/edge-and-supersession-build-plan.md | "IN PROGRESS; 7&9 built" | **EXEC** (edge) | Item 7 `core/complex/build.py:139-152`; 8f `core/stores/authored_supersession.py`; "EdgeStore refuses supersedes" overclaims (`edges.py:87-99`) |
| **Cluster B — attestation / integrity** |
| 5 | attestation-layer.md | design only (stale) | **PARTIAL** | records B&W unsigned (`core/attestation/*`, `launcher.py:121-127`, emit `sync.py:102`); signing PNW (`defaults.toml:175` off); gate-emission NOT BUILT |
| 6 | core-integrity.md | draft | **NOT BUILT** | no manifest/seal-ceremony/verifier; only adjacent = `preflight.py:124` CONSTITUTION-only fingerprint |
| 7 | research/security-planes.md | Draft for review | **N/A** | doctrine; load-bearing invariant realized as foundation denylist `.claude/hooks/_lib.py:27-36,288-291` |
| **Cluster C — ingest / supersession** |
| 8 | dialogue-ingest-and-recursion.md | DRAFT | **PNW** | op vocab `core/recursion_ops.py:66-293` tested but 0 live callers; analyzer no-op `:102-123` |
| 9 | ingest-identity-and-amendment.md | DRAFT | **B&W** | content-addressed index `core/ingest/index.py:26-39`, amend `amend.py:43-85`, versions `versions.py`, wired `sync.py:97,110` |
| 10 | supersession-lifecycle.md | DRAFT | **PARTIAL** | `stale_closure` exists `recursion_ops.py:218-240`; certification/gate/`s(C,D)` = no code; PROGRESS:1451 "Item 8 Next" |
| 11 | founding-corpus.md | DRAFT | **B&W** | `core/ingest/founding.py:90-133` via `scripts/ingest_founding.py` (owner CLI, by design) |
| 12 | vault-sync-and-capture.md | near-term, buildable now | **B&W** | watcher `core/ingest/watch.py`, sync `sync.py:59-133`, wired `launcher.py:74,122,128,231` |
| **Cluster D — dreaming** |
| 13 | dream-phase-rnd-charter.md | R&D, flag OFF | **PARTIAL** | R0/R1 PNW (`interpreters.py:290`, `adjudicator.py:92`); R2–R5 not built; flag `defaults.toml:237` |
| 14 | dreaming-on-curated-graphs.md | R5, flag OFF | **NOT BUILT** | no `CuratedView`/`resonance` repo-wide |
| 15 | dreaming-v2-interpreter-panel.md | design only | **PNW** | panel `interpreters.py:76-297` + adjudicator tested `test_dream_rnd.py`; gated `[dream_rnd]` off; no live call |
| 16 | recursive-dreaming-bounded-by-grounding.md | design only | **PARTIAL** | bound built+tested `core/recursion.py:56-80`; depth>1 feature not built (`AUTHORED_LEAF_DEPTH=1`) |
| 17 | dreamer-quality-suite-evaluation.md | evaluation; adopt (F9) | **B&W** (CI) | real binding `tests/fixtures/dreamer_adapter.py`, `tests/quality/test_real_dreamer_binding.py`; CI not runtime (by design) |
| **Cluster E — hands / effectors / verdict** |
| 18 | hands-and-the-effector-layer.md | *(no status line)* | **PNW** | G1–G7 exist+tested (`ops/effects.py`, `effect_gate.py`, `effect_exec.py`, `eval/effector_drift.py`); 0 live callers; `[effectors]` off |
| 19 | effector-risk-computation.md | DRAFT | **PARTIAL** | constraint-only realized (`effects.py:79`, `effect_gate.py:132`); reachability measure + optimizer not built |
| 20 | verdict-authority.md | DRAFT | **B&W** | Ed25519 `core/verdict/payload.py`, store `verdicts.py:113`, wired `scripts/verdict.py` + `ambassador/__init__.py:88`; §5 HW-MFA + weight-promotion not built |
| **Cluster F — recursive strata** |
| 21 | recursive-strata.md | Parked; no implementation | **PARTIAL** | decay+ops built (`recursion.py:43-80`, `recursion_ops.py`); strata/budgets/gauges not built; `DERIVED_STRATUM` reserved `provenance.py:54` |
| 22 | recursive-strata-amendment.md | DRAFT patch-spec | **N/A** | edits unapplied; embedded code items mostly built (§1 SUPERSEDES-removed, §5 warrant-anchor `recursion_ops.py:270-275`) |
| 23 | stability-adjudication.md | design only; parked | **NOT BUILT** | no perturbation-consensus adjudicator; the 2 test-time perturbations it catalogs do exist as tests |
| **Cluster G — ambassador / observed** |
| 24 | ambassador-as-reasoning-agent.md | design only (authoritative) | **B&W** | `agents/ambassador/{agent,intent,policy}.py`, wired `launcher.py:117-124` |
| 25 | ambassador-interpretation-and-flow.md | design only, ⚠ partially superseded | **B&W** | same call sites; note §3 lists 4 intents, code has 6 (`intent.py:25-31`) |
| 26 | nervous-system-and-ambassador.md | design only | **PARTIAL** | §4 OpsView live (`ops_view.py:60`); §1 tamper-tripwire + §2 auditor no code |
| 27 | observed-data-and-the-assistant-tier.md | design only, not implemented | **PARTIAL** | firewall B&W (`provenance.py:59`, `sensing.py:184-213`); assistant tier not built |
| 28 | observed-iot-and-cross-source-synthesis.md | design only | **PARTIAL** | `sensor_readings` dormant `telemetry.py:39-46`; correlator + biometric ingest not built; schema drift vs note §1b |
| **Cluster H — vault / sandbox / skills** |
| 29 | vault-runtime-auth.md | design only (stale) | **PNW** | backend+factory built+tested (`secrets_backend.py`, `factory.py:61-80`); `mint()` 0 live callers |
| 30 | secrets-management-evolution.md | design only | **PARTIAL** | Keychain half wired (`run_with_secrets.sh`); server/KMS/AppRole not built; superseded by #29, unmarked |
| 31 | wasm-sandbox-runtime.md | partially built | **PARTIAL** | real wasmtime `runner.py:115-193`; inert by config (`runtime=podman`, `wasm_module=""`); `_run_wasi` untested |
| 32 | skill-mining-pipeline.md | *(no status line)* | **PNW** | catalog-as-data `ops/effect_catalog.py:96` (5 audited entries); effector layer off; no runtime miner |
| 33 | skills-and-scope.md | design only, not implemented (stale) | **PNW** | capability half built+tested (`factory/roles.py`, `tools.py`); instructional `RoleTemplate.skills` 0 consumers |
| **Cluster I — alignment / testing** |
| 34 | alignment-subsystem.md | design only | **PARTIAL** | gauge built+tested `eval/drift.py`; only boot fingerprint wired `preflight.py:135-137`; A2/report/surgery not live |
| 35 | holistic-testing.md | design only | **PARTIAL** | property/metamorphic/adversarial run; `tests/emergent/`+`tests/longitudinal/` = 0 test files |
| 36 | test-organization.md | actionable now | **B&W** (skeleton) | 9 subdirs+fixtures present, markers/addopts match §3 verbatim `pyproject.toml:52-75`; emergent/longitudinal empty |
| 37 | live-adoption-and-longitudinal-harness.md | forward-looking (Track L) | **NOT BUILT** | L-series absent; only `core/stores/verdicts.py` pulled ahead; "Built:" headers are prospective |
| **Cluster J — meta / roadmap / research-math** |
| 38 | agent-workflow.md | ratified (YAML) | **B&W** | all 6 hooks/6 cmds/5 skills/4 templates present + registered `.claude/settings.json`; only gap = finding-0009 |
| 39 | roadmap-and-future-directions.md | roadmap, not spec | **PARTIAL** (by design) | §1/§7/§8/§10/§11 landed; §4/§5/§12/most-§3 future |
| 40 | research/planar_graphs.md | *(statusless)* | **N/A** | subject not built (grep planar/kuratowski=0); orphan; `core/complex/` is different (persistent-homology) math |
| 41 | research/un-represent-ability.md | *(statusless)* | **N/A** | background survey seeding security-planes; philosophy realized via that note, not this |

**Tracking-record reconciliation:** PROGRESS agrees with code almost everywhere
(cited per-note in §2). The exceptions surfaced as findings: PROGRESS:1085-1087
"WIRED ceiling ε=SENSING" (no effector is wired — 0011); PROGRESS:984-986
`DERIVED_STRATUM` "undone" (it is reserved, `provenance.py:54` — 0013); the two
build-plan status lines (#3, #4 — 0013); PROGRESS:1547 honestly concedes "nothing
demotes from retrieval yet" (0012).

---

## 2. Per-file detail

Citations are `path:line`. Where a note's own status is stale, that is stated but not
changed.

### Cluster A — sacred boundary, edge, network egress

**Special-focus verdicts (Invariants 1 & 2):**
- **Egress guard is live** via `core/sealing.py:94-105 seal()` (process-wide
  `socket.connect` interceptor, loopback+AF_UNIX only), called first-thing by
  `palace.py:37`, `ingest.py:21`, `talk.py:109`, `watch.py:27`; tested
  `tests/integrity/test_sealing.py:11-34`. `runtime.py bootstrap()` is *not* the live
  seal (dead — finding-0016).
- **core→edge separation is structurally linted** (`ops/import_lint.py:96-98,54-57`),
  run as a test (`tests/integrity/test_import_firewall.py`) and a dedicated GitHub CI
  job (`.github/workflows/ci.yml:15-25`). But the **edge→core direction has no blanket
  lint** (only `edge/effectors/**` barred, `test_sensing_firewall.py:111-121`) and
  **`.gitlab-ci.yml` does not run the lint** — finding-0014.
- **Edge components:** `edge/interface` WIRED (`talk.py`, LocalAdapter, sealed);
  `edge/monitor` PNW (`[monitor] enabled=false` `defaults.toml:123`); `edge/bridge`,
  `edge/effectors` PNW scaffolding.

**the-sacred-boundary.md** — DRAFT — **N/A-DESIGN-ONLY.** A spine/principle/index note;
its four properties are instantiated piecewise by the subsystem builds (attributable →
`core/verdict/`+`core/attestation/crypto.py:52-83`; append-only → `versions.py`,
`attestation/store.py`; constraints-not-EV → `effect_gate.py:132-144`), not by any one
code unit. §4 ordering: verdict store reachable, "recursive loop" inert (dialogue-op
no-op), longitudinal absent, outbound effect flag-off. *Conflict:* still DRAFT though
its reconciliation build plan reports items built+owner-approved. Property 4
("un-purchasable by EV") holds only vacuously — no EV machinery exists
(`ops/effects.py:20-26` an effect carries no confidence).

**the-edge-model.md** — DRAFT — **BUILT & WIRED** (partition), §3 PARTIAL. Four stores
(`edges.py` E_geom, `versions.py`, `recursion_ops.py` ClaimOpStore,
`authored_supersession.py`); partition assembled `core/complex/build.py:139-152`
(E_geom only into `L`); tested bit-identically `tests/integration/test_edge_partition.py:57-95`.
Wired: `build_complex` runs live in the dreamer lens (`core/dreaming/interpreters.py:249`)
via the dream cron handler (`scheduler/cron.py:31-48` → `launcher.py:125,131`); edge/version/
authored-historical stores written by live ingest (`sync.py:111`, `founding.py:130,152`).
PROGRESS:1425 agrees. *Conflict:* §3 presents assertion-authority as a per-edge field
`{geometry, dreamer-proposed, verdict-certified}` — no such field/enum exists; Item 7
realized authority as store-identity (finding-0013).

**build-plans/sacred-boundary-build-plan.md** (build-plan) — **EXECUTED**, status stale.
Items 1c/2a/4a-b/DERIVED_STRATUM/verdict/Part B all landed and wired
(`scripts/verdict.py`, `provenance.py:54`, `sync.py`). *Conflict:* header + line 707
say "Item 6 PLANNING ONLY / nothing implemented," but `core/stores/versions.py` exists
and is wired (`sync.py:111`); `edges.py:30-33,122` and the later plan treat Item 6 as
landed (finding-0013).

**build-plans/edge-and-supersession-build-plan.md** (build-plan, edge portions) —
**EXECUTED.** Item 7 built+wired+tested; 8f (`authored_supersession.py`,
`MachineAuthorityRefused` fail-closed) built+wired+tested — despite the header listing
"Item 8 awaiting approval." PROGRESS:1425,591,1448 agree. *Conflict:* the plan
(lines 343,525) and `core/complex/build.py:149` say "EdgeStore forbids/refuses a
supersedes rel-type" — it does not (`EdgeStore.add()` accepts any `rel_type`,
`edges.py:87-99`); the real protection is no-writer + no-handle (finding-0013).

### Cluster B — attestation, core integrity, security planes

**attestation-layer.md** — self-status "design only" (**stale**) — **PARTIAL.** Records
layer BUILT & WIRED but **unsigned**: `record.py:50`, append-only `store.py:73`,
`Ed25519Signer crypto.py:66`, `build_attestor` (fail-closed) `attestor.py:91`; wired
into vault-sync/dreamer/curator/ambassador (`sync.py:151`, `dreamer.py:282`,
`curator.py:197`, `ambassador/__init__.py:76`) assembled `launcher.py:121-127`; live
emissions `sync.py:102`, `dreamer.py:142/221`, `curator.py:163`. Tested extensively
(`tests/integration/test_attestation_store.py`, `tests/integrity/test_attestation_{signatures,chain}.py`).
**Signing is flag-off** (`defaults.toml:175`, no local override → `signer=None`,
`attestor.py:103-104`). **Owner-key gate-attestation emission is NOT BUILT** while the
verifier already enforces owner-signing (`verify.py:39`) — a dangling verify-half.
PROGRESS:718 ("G5 PARTIAL") agrees. *Conflicts:* §4 `att_output` SQL index never
created (`store.py:33` only `att_role_ts`); `signer` persisted outside `signing_payload()`
(`record.py:63`).

**core-integrity.md** — draft (2026-07-05) — **NOT BUILT** (design-only; §12 says it
"graduates as a build plan after ratification"). No manifest, posture field, verifier
preflight, or seal ceremony (grep clean). The nearest live analog is
`ops/lifecycle/preflight.py:124 check_constitution` — a boot-time fingerprint gate over
**CONSTITUTION.md only** (`eval/golden/baseline.json`), no Ed25519/YubiKey/`core/**`
manifest. finding-0003 confirms it as a new untracked draft. *Caution:* three unrelated
"seal" meanings collide (egress guard / Vault seal-state / signed byte-manifest) — flag
before it graduates.

**research/security-planes.md** — "Draft for review" — **N/A-DESIGN-ONLY** doctrine, but
its load-bearing invariant *is* realized and wired: the foundation denylist
`.claude/hooks/_lib.py:27-36` (comment "origin: security-planes.md"), enforced every
session by the scope guard `_lib.py:288-291`. Parked items (Rust split, store
encryption, TLA+/Alloy) unbuilt by declaration. *Conflict:* §2 lists "attestation keys
+ signing config" as foundation files, but `ops/attestation/*.pub` and
`config [attestation]` are absent from the enforced denylist — enumeration not matched
by the control it claims.

### Cluster C — ingest, identity/amendment, supersession, founding, vault-sync

**dialogue-ingest-and-recursion.md** — DRAFT — **PRESENT-BUT-NOT-WIRED.** The §4
operation vocabulary is whole and tested (`core/recursion_ops.py:66-293`,
`tests/integration/test_dialogue_ops.py`) but has **zero non-test callers**; the injected
`DialogueAnalyzer` defaults to no-op (`recursion_ops.py:102-123`). The wired dialogue path
(`DialogueCapture.capture`, `dialogue.py:60-64`) only stores `authored-dialogue`. §4.2
`derived_from` correction (warrant anchors, never `[C]`) *is* implemented
(`recursion_ops.py:270-277`). PROGRESS:1353-1379 agrees ("non-recursive floor").
(finding-0012.)

**ingest-identity-and-amendment.md** — DRAFT — **BUILT & WIRED.** Content-addressed index
(`index.py:26-39`), chunk-level amendment (`amend.py:43-85`), version store keyed
`(doc_id, version_seq)` (`versions.py:43-104`); wired live at `sync.py:97,110-111`
(not flag-gated). Tested (`test_index_keying.py`, `test_chunk_amendment.py`,
`test_version_history.py`). PROGRESS:1267-1348 agrees. *Gap:* VersionStore is write-only
— no live reader consumes `history()`/`supersessions()` (finding-0012).

**supersession-lifecycle.md** — DRAFT — **PARTIAL.** `stale_closure` (§5) and the
warrant-anchor grounding (§4.2) exist and are tested (`recursion_ops.py:218-240,270-277`)
but are not wired (`apply_operations` has no live caller). §2 `proposed→certified`, §3
blessing gate, §3 disposition-authority, §6 candidate `s(C,D)` — **no code at all.**
PROGRESS:1451,1543-1549 agree ("Item 8 — Next … nothing demotes from retrieval yet").
(finding-0012.)

**founding-corpus.md** — DRAFT — **BUILT & WIRED** (owner CLI, by design). `founding.py:90-133`
(undated/forward-supersession guards), run via `scripts/ingest_founding.py:29-37` sharing
the one ingest pipeline + recording K₀↔K₀ supersession through `AuthoredSupersessionStore`
(`founding.py:129`). Not part of `palace start` — matches the note's "injected at once"
design. Tested `test_founding_corpus.py`. *Note:* §2.1 dates land in raw but the temporal
layer that would read them is dormant (`founding.py:16-17`).

**vault-sync-and-capture.md** — "near-term, buildable now" — **BUILT & WIRED.** Watcher
(`watch.py:26-113`, filesystem-only), sync with UNCHANGED/INDEXED/TOMBSTONED outcomes
(`sync.py:59-133`), gated purge (`purge.py`, `scripts/purge_raw.py`); wired at
`launcher.py:74,122,128,165,231`. Seal preserved (no `edge`/socket imports). Tested
(`test_vault_sync.py`, `test_vault_watcher.py`, `test_vault_sync_wiring.py`).
PROGRESS:217-218 agrees. Syncthing/Tailscale transport is operational/runbook (N/A-code).

### Cluster D — dreaming (live loop vs flag-off R&D)

Foundational: the live path runs `dreamer.dream()` (v1: cluster→synthesis→grounding
check→INTERPRETED, `dreamer.py:124-163`, no panel/adjudicator/confidence) via
`scheduler/cron.py:31-36` → `launcher.py:125`. The R&D track (`dream_v2`, `run_panel`,
`run_dream_rnd`, `adjudicate`) is called nowhere outside tests; `[dream_rnd] enabled=false`
(`defaults.toml:237`), `require_rnd_enabled` raises (`rnd.py:31-40`).

**dream-phase-rnd-charter.md** — R&D, flag OFF — **PARTIAL.** R0 panel (`interpreters.py:290`)
+ R1 adjudicator (`adjudicator.py:92,138`) present + tested (`test_dream_rnd.py:50-143`),
not wired; R2 (utility), R3 (recursion), R4 (cross-source), R5 (curated) not built.
PROGRESS:561,630 + README:122 agree.

**dreaming-on-curated-graphs.md** — R5, flag OFF — **NOT BUILT.** No `CuratedView`/
`resonance`/`cross_graph` anywhere. (The `curated` provenance + `core/ingest/curated.py`
exist but are self-knowledge *ingest*, not the R5 dreamer.)

**dreaming-v2-interpreter-panel.md** — design only — **PRESENT-BUT-NOT-WIRED.** Panel
`interpreters.py:76-297` (change_point an honest empty seam `:218-223`) + evidence-not-
persuasion adjudicator `adjudicator.py:92-135`; tested `test_dream_rnd.py:63-143`; gated
off, no live call site. *Note:* adjudicator `g` (resolvability only, `adjudicator.py:113`)
differs from the F9 quality-suite `g` (folds support-count) — a documented divergence
(Hook 2, PROGRESS:69-70), not a defect.

**recursive-dreaming-bounded-by-grounding.md** — design only — **PARTIAL.** The bounding
primitives are BUILT & TESTED — decay clamp `core/recursion.py:56-80`
(`c=min{1,γ^d·g·(1+λ(|Agr|−1))}`), acyclicity `derived.py:83-87`, authored-terminating
support `support.py:41-65`, tested `test_recursion.py:14-48`. But **no path produces
depth>1** (`AUTHORED_LEAF_DEPTH=1`, `adjudicator.py:43,118`; `derived_from`=authored
leaves, `dreamer.py:158,234`) — the recursion feature is unbuilt; the bound is only ever
evaluated at d=1 inside the flag-off adjudicator. Rule-4 fixed point = the drift gauge
(A1, `eval/drift.py`). Residual gap G9 (authored-leaf-only not yet *structurally*
enforced) documented `derived.py:7`.

**dreamer-quality-suite-evaluation.md** — evaluation; verdict "adopt" (F9) — **BUILT &
WIRED** (as a CI suite — correctly not a runtime feature). Real binding
`tests/fixtures/dreamer_adapter.py` (real `Dreamer.clusters()`/`grounding_score`/recursion);
suite `tests/quality/test_dreamer_quality.py`; live-persistence proof
`test_real_dreamer_binding.py:50-112`. Runs under `pytest -m quality`, selected by
`MIND_PALACE_DREAMER_ADAPTER`. PROGRESS:18-76 "F9 COMPLETE" agrees. Caveats honored:
`rate_blind` deliberately unwired (value claim OPEN, Hook 1); the `g`-support question
resolved in the binding only (Hook 2).

### Cluster E — hands / effectors / verdict authority

**Headline:** the entire Track-G effector layer — sensing included — is
**PRESENT-BUT-NOT-WIRED.** No live entry imports any effector module (grep of
`scripts/`, `ops/lifecycle/`, `core/runtime.py`, `scheduler/` = 0). `[effectors]
enabled=false` (`defaults.toml:138`, not in local.toml). Max wired tier = **NONE**;
"ε=SENSING" is only the `EffectView` type default (`ops/effects.py:184`), never
constructed live (finding-0011).

**hands-and-the-effector-layer.md** — *(no status line)*; §10 self-marks G1–G7 ✅ —
**PRESENT-BUT-NOT-WIRED.** G1 `effects.py:47,91,170`; G2 gate `effect_gate.py:60,132`;
G3 sensing `edge/effectors/sensing.py:114`; G4 catalog `effect_catalog.py:96,177`; G5
reversible `effect_proposal.py:74`+`writes.py:56`+`effect_ledger.py:130`; G6 irreversible
`effect_exec.py:96,164`; G7 drift `eval/effector_drift.py:105,118`. Tested including the
72-state gate FSM (`tests/property/test_effect_gate_fsm.py:5-6,34`). No live caller.
PROGRESS:780-855,1082-1141 agree the acting classes are off but overstate the sensing
wire (finding-0011).

**effector-risk-computation.md** — DRAFT — **PARTIAL.** The constraint discipline it
demands is realized structurally — `required_approval` monotone step (`effects.py:79`),
`effect_gate_admits` a pure conjunction with no priced/EV term (`effect_gate.py:132`),
tested `test_effect_gate_fsm.py:63-65`. The §2 reachability-contraction *measure* and §3
constrained *optimizer* are not built (parked PD1). *Answerable from code:* §7 Q5 —
bright lines are **gated, not priced.**

**verdict-authority.md** — DRAFT (R4 footer "Built: core/verdict/") — **BUILT & WIRED**
(core mechanism), two named sub-parts not built. Ed25519 over canonical bytes
(`payload.py:44,80,111`, reusing `attestation/crypto.py:33`), verify-on-append monotonic
store (`verdicts.py:113,128,135`), dispositions+apply (`apply.py:47,67,77`), taxonomy
(5 categories). Wired via `scripts/verdict.py:32,62,81` and the Ambassador verdict-receiver
(`ambassador/__init__.py:88` → `agent.py:129 transport_verdict`, transport-only,
fail-safe `None` if no owner pubkey). PROGRESS:1147-1229 agrees. *Not built:* §5
hardware-gated signature (Secure Enclave/FIDO2/PIV — grep=0; plain Keychain seed
`scripts/verdict.py:43`); the weight-promotion half of apply (only RETRACT/ENDORSE/RECORD,
`apply.py:67`). No TOTP anywhere.

### Cluster F — recursive strata + stability adjudication

Live path runs v1 `dream()`; the whole reasoning-complex is reachable only via
`dream_v2()`→`require_rnd_enabled` (`dreamer.py:183`), flag-off.

**recursive-strata.md** — "Parked; no implementation" — **PARTIAL.** Built: γ^d·g decay +
`claim_confidence` clamp (`recursion.py:43,56`); the dialogue-op instantiation of the map
`D` (`recursion_ops.py:72,160,243`); `DERIVED_STRATUM` label reserved (`provenance.py:54`).
Not built: the Sₙ strata, `layer_weight`, budgets, gauges, promotion. Not wired
(`apply_operations` 0 non-test callers; `claim_confidence` only in the flag-off
adjudicator). *Conflicts:* PROGRESS:984-986 claims `DERIVED_STRATUM` "undone" — false to
code (finding-0013); §8-action-1 half-done (label reserved, integer `depth` deferred
`provenance.py:51`); §8-action-2 (promote-insight verdict) *deliberately* reversed by the
ratified `taxonomy.py:9-21` (≤5 fatigue bound), note un-annotated.

**recursive-strata-amendment.md** — DRAFT patch-spec — **N/A-DESIGN-ONLY** (edits
unapplied), but its embedded code items are mostly built: §1 (`SUPERSEDES` removed from
the edge store, `edges.py:33`; version supersession moved to `versions.py:45-54`) and §5
(warrant-anchor grounding, `recursion_ops.py:270-275`, tested `test_dialogue_ops.py:121-183`).
*Conflict:* the stale I2 cross-ref the amendment fixes still stands in
`recursive-strata.md:45` ("built as SUPERSEDES") — now false to code. §3 blessing/demotion
gate for *blessed* derived content is still an open gap (`recursion_ops.py:184` removes
with no blessed/unpromoted distinction) — finding-0013.

**stability-adjudication.md** — "design only; parked" (flag-off R&D) — **NOT BUILT.** No
perturbation-consensus adjudicator; `adjudicator.py:92` builds one complex and adjudicates
once (no K-loop, no survival rate). The two test-time perturbations the note catalogs *do*
exist as tests (`test_structural_interpreters.py:68`, `test_dreamer_quality.py:731`).
Accurate self-description; no drift. PROGRESS:881,976 agree.

### Cluster G — Ambassador, nervous system, observed data, IoT

**ambassador-as-reasoning-agent.md** — design only (marked authoritative) — **BUILT &
WIRED.** `agents/ambassador/agent.py:90`, deterministic-floor + model-earned intent
(`intent.py:71,95`), narrate-effort + earned-interruption (`policy.py:44,63`); wired
`launcher.py:117-124` + `scheduler/interface.py:148` + `core/interface.py:99`; retrieval-
within-budgeter `agent.py:175-185`. Tested (`test_ambassador*.py`). PROGRESS:126-180,719
("Track B END TO END … attested live") agrees strongly.

**ambassador-interpretation-and-flow.md** — design only, "⚠ PARTIALLY SUPERSEDED
(2026-06-28)" — **BUILT & WIRED.** §3 loop `agent.py:144-158`; intent→gated-task (never
acts) `agent.py:187-193` + `scheduler/interface.py:66-91` (HumanGate); pinned router tier
`agent.py:58-63`. Tested `test_ambassador_conversation.py`. *Note:* the built loop has 6
intents (`intent.py:25-31`); this note's §3 enumerates 4. Should carry a `superseded_by`
pointer (see §4).

**nervous-system-and-ambassador.md** — design only — **PARTIAL.** Only §4 (the Ambassador
+ operational-introspection scope) is live: `OpsView` (`ops_view.py:60`, narrate `:123`),
authored-dialogue capture (`agent.py:97,118-120`); §1 recovery-as-a-flag exists
(`launcher.py:201-214`). **§1 graduated tamper tripwire and §2 async auditor: no code**
(grep `class Auditor|chain_walk`=none). The note reads as one integrated senses→reflex→
reports system, but only the reports limb is live; the trigger for recovery mode is an
*unclean shutdown*, not tamper detection. PROGRESS agrees ("A3 auditor remains", 447/500/
552/622/688) — finding surfaced as part of the design gap.

**observed-data-and-the-assistant-tier.md** — design only, not implemented — **PARTIAL.**
The authored/observed firewall is built + wired — `observed` provenance excluded from
`MIRROR_READABLE` (`provenance.py:59,76-77`), `ObservedView` vs `MirrorView`
(`sensing.py:184-213`), gating the Ambassador RETRIEVE path (`agent.py:146`). The
assistant tier (email/calendar/news reading the observed pool via Data Portability) is
**not built**. (The Track-G catalog has `draft_reply`/`calendar_hold`/`send_email` entries
but flag-off and reading no observed pool.)

**observed-iot-and-cross-source-synthesis.md** — design only — **PARTIAL (seam-only).**
`sensor_readings` table exists but dormant (`telemetry.py:39-46`, docstring "no adapter
writes to it yet"); `ObservedView` seam `sensing.py:185`. **The correlator has no code**
("correlator" appears only in comments); **biometric/Oura ingest: none.** Nothing consumes
`ObservedView` and nothing writes `sensor_readings`. PROGRESS strongly agrees ("DANGLING
correlator capstone, Track D", 447/500/552/622/688/987/1143). *Conflict:* schema drift —
note §1b `sensor_readings(ts, source, metric, value, unit, raw_json JSON)` vs built
`(ts, sensor, metric, value, unit, meta VARCHAR)` (finding surfaced; see §5 note).

### Cluster H — vault runtime auth, secrets, sandbox, skills

**vault-runtime-auth.md** — design only (**stale**) — **PRESENT-BUT-NOT-WIRED.** Backend
(`config/secrets_backend.py:110` real hvac, `:40` MintedToken), `get_secret(name, token)`
Vault branch (`loader.py:508`), factory grant path (`factory.py:61-80,150`), full
`ops/vault/` deployment assets — all built + tested (`test_secrets_backend.py`,
`test_factory_credential_grant.py`, live-skip `test_secrets_vault_live.py`). **Not wired:**
the only consumer is `build_factory` (`factory.py:179`), and `build_factory`/`.mint()` are
never called outside tests; neither `bootstrap()` nor `build_components()` construct a
factory. (`[secrets].enabled=true` on this machine would wire the *backend* if a factory
existed — but none does on the live path.) The plain `get_secret(name)` env/Keychain path
is live, but that is not the Vault runtime-auth layer. PROGRESS:327-336 agrees ("wiring
win … only when `[secrets]` enabled"; no live-daemon claim). finding-0010, 0016.

**secrets-management-evolution.md** — design only — **PARTIAL (superseded).** Current
Keychain path is wired (`run_with_secrets.sh:15-21`, `loader.py:530`). The note's
distinctive proposal — server-hosted Vault, KMS auto-unseal, AppRole-per-component — is
**not built**; what shipped is vault-runtime-auth's local `127.0.0.1:8200` model
(`defaults.toml:187`). *Conflict:* `vault-runtime-auth.md:5` declares it supersedes this
note, but this note carries no superseded/deprecated marker and disagrees on host + unseal
— a reader hitting it first gets the wrong server-first model (finding-0010).

**wasm-sandbox-runtime.md** — "partially built (corrected 2026-07-03)" — **PARTIAL.**
`WasmRunner` is genuinely wasmtime (`runner.py:115-193`: `wasmtime.Engine/Store/WasiConfig/
Linker.define_wasi/Module.from_file`, epoch watchdog, "ONLY stdio — no preopen_dir, no
sockets" `:182`), fail-closed `available()`; `RoutingRunner:225` picks WASM for pure-compute
python else Podman. **Inert by config** (`[sandbox] runtime="podman"`, `wasm_module=""`,
`defaults.toml:274,276`) → `available()` always False, always falls to Podman; nothing runs
under WASM. `build_broker` is invoked only by `scripts/sandbox.py:53`, never the daemon.
Tests are **structure-only** (`test_sandbox_wasm.py` — fail-closed, routing with fake
runners); the real `_run_wasi` path is untested (needs an owner-placed `python.wasm`).
PROGRESS:282-285 agrees. *Conflict:* §2 claims `reset()`/warm-pool parity, but WASM
`start`/`exec_in` raise `NotImplementedError` (`runner.py:214-218`) — single-shot only
(finding-0016).

**skill-mining-pipeline.md** — *(no status line)* — **PRESENT-BUT-NOT-WIRED.** The pipeline
is process-as-data: `ops/effect_catalog.py:96 _CATALOG` holds 5 audited `CatalogEntry`
objects (each with reversibility/scope/param_keys/sandbox_profile/`audited=True`), fail-closed
lookup `:177`; supporting effect types + JIT-credential exec `effect_exec.py:175`. There is
**no runtime skill miner** — "mining" is a human diff to `_CATALOG`. Tested
`test_effect_catalog.py:33` ("every cataloged hand is audited"). Not wired — the effector
layer is flag-off (`test_effect_catalog.py:79-91` asserts acting hands unreachable at
ε=SENSING). Maps to the effector layer, not `core/curator`/`core/librarian`.

**skills-and-scope.md** — design only, not implemented (**stale**) — **PRESENT-BUT-NOT-
WIRED.** Capability half built + tested: `PRE_DECLARED_MAX={run_python}` (`roles.py:24`, no
shell/cred/net by construction), `RoleTemplate` refuses `scope⊄MAX` (`:35`), object-capability
dispatch (`tools.py:62,82`), `mint()` routes over-ask to `HumanGate` (`factory.py:122,131-135`),
tested `test_factory_roles.py`. **Not wired:** `build_factory`/`.mint()` never called outside
tests. **Instructional half is a dead field:** `RoleTemplate.skills` has zero consumers and
`build_context` (`factory.py:56-59`) never loads skill frames (finding-0016). PROGRESS:266,367,
717 agree ("factory/run_python built but undriven"). finding-0010.

### Cluster I — alignment, testing doctrine, longitudinal harness

**alignment-subsystem.md** — design only — **PARTIAL.** The drift gauge is BUILT + TESTED —
`drift()` one-sided-L2 + Constitution hard-trip (`eval/drift.py:133`), `measure_drift()`
(`:210`), fixed points in `eval/golden/baseline.json`; A2 structural
`core/complex/cut.py:111 alignment_snapshot`; reset `derived.py:389`; surgery seam
`curator.py:104`; tested `test_drift.py`, `test_drift_property.py`. **Wiring is minimal:**
only the Constitution-conformance conjunct runs live (boot fingerprint,
`preflight.py:135-137` on every `palace start`). Numeric capability-`D(t)` is computed only
in the flag-off self-mod validator (`selfmod.py:215-227`); `measure_drift()` has no live
caller; `alignment_snapshot()` is called only from tests. Surgery/reset loop + the alignment
report: design-only. PROGRESS:78,581-590,1006,123 agree. finding-0015.

**holistic-testing.md** — design only — **PARTIAL.** Present + running: `tests/property/`
(8), `tests/metamorphic/` (2), `tests/adversarial/` (3), partial attestation-as-oracle
(`test_attestation_chain.py`). **Empty:** `tests/emergent/` and `tests/longitudinal/` are
conftest-only scaffolds (0 test files). PROGRESS:720 ("G7 PARTIAL … missing model-facing
adversarial half") corroborates. Descriptive for the populated categories; aspirational for
emergent/longitudinal/full-attestation-oracle.

**test-organization.md** — "actionable now; mechanical refactor" — **BUILT & WIRED
(skeleton) / PARTIAL (population).** All 9 named subdirs + `fixtures/` (+ an undocumented
`quality/`) exist; per-dir marker conftests and `addopts="-m 'not longitudinal'"` match §3
**verbatim** (`pyproject.toml:52-75`); `testpaths=["tests"]`. The reorg — the note's actual
deliverable — is done and is what pytest consumes. *Divergences:* `test_import_lint.py` is
actually `test_import_firewall.py`; `fixtures/corpus.py` has deterministic helpers, not the
`synthetic_corpus()` Hypothesis strategies §1 specifies; `quality/` dir undocumented;
`emergent/`+`longitudinal/` are homes without tenants (finding surfaced with holistic-testing).

**live-adoption-and-longitudinal-harness.md** — forward-looking (Track L) — **NOT BUILT.**
Nearly all L-series artifacts absent (`eval/longitudinal.py`, `scripts/{review,tune,curves}.py`,
`config/tuning.toml`, `core/dreaming/shadow.py`, `core/stores/runledger.py` — all not found).
Only `core/stores/verdicts.py` (L2 verdict store) exists, pulled ahead as a sacred-boundary
item. No shadow job, no curves, no F4 drift-trajectory asserts (`tests/longitudinal/` empty).
PROGRESS:987 ("Absence confirmed … Track L all L-series absent") agrees. *Caution:* the note's
"**Built:**" section headers are prospective builder-prompt language, not statements of
reality — only the verdict store landed.

### Cluster J — agent-workflow machinery, roadmap, research-math

**agent-workflow.md** — ratified (YAML, A1–A6) — **BUILT & WIRED.** All 6 hooks
(`.claude/hooks/{scope-guard,gate-guard,session-brief,journal-gate,staleness-nudge,
compaction-marker}.sh` + `_lib.py`), 6 commands, 5 skills, 4 templates present; amendments
landed in `_lib.py` (A5 `:178`, A3 `:435`, gate-check `:313`, stop-audit `:455`). Registered
in `.claude/settings.json` on every event; live-fire evidence in `.claude/state/`. Acceptance
`bp-004/acceptance/run.sh` (21/21, PROGRESS:1659). PROGRESS:1544-1700 agrees ("board uniform,
bp-000…004 complete"). **No hook/skill/command/template missing.** One open machinery gap:
**finding-0009** (already open) — `cmd_gate_check` (`_lib.py:313-331`) gates only
`→ready`/`→ratified`, so `proposed→complete`/`→in-progress` bypasses the readiness blessing
(candidate amendment A7). Findings→amendments already resolved: 0001→A2, 0003→A1, 0004+0005→A3,
0006→A5, 0007→A4, 0008→A6.

**roadmap-and-future-directions.md** — "roadmap, NOT committed spec" — **PARTIAL (by design).**
Landed: §1 provenance spectrum (`provenance.py:9` self-cites it + `sourceset.py`), §7 process/
concurrency (`scheduler/`), §8 lifecycle (`ops/lifecycle/`), §10 dashboards (`edge/monitor/` +
`scripts/monitor.py`), §11 security/effectors (`ops/effect_*.py`). Not landed: §4 peripherals/
sensors, §5 multi-sensory/creative, §12 backups-as-drift-recovery, most of §3. Correctly
non-binding; no conflict.

**research/planar_graphs.md** — *(statusless)* — **N/A-DESIGN-ONLY.** Subject not built (grep
`planar|kuratowski|genus|planariz`=0). `core/complex/` implements a *different* body of math —
persistent homology / Vietoris–Rips (`topology.py:59`), spectral (`spectral.py`), Forman–Ricci
curvature (`curvature.py`), Laplacian (`laplacian.py`), min-cut/conductance (`cut.py`) — under
the H-track notes, not planar-graph drawing. Uncatalogued orphan (finding-0017).

**research/un-represent-ability.md** — *(statusless)* — **N/A-DESIGN-ONLY.** Background
literature survey; `docs/README.md:134` frames it as "raw material that seeded security-planes
… not a spec." The philosophy is realized structurally (`core/research/criteria.py:5-6`
"no free-text/content field (unrepresentable)", airlock `core/research/airlock.py`) — but that
traces to security-planes, not this survey. No conflict.

---

## 3. Cross-check — substantial built work with no (or misplaced) design note

Aggregated from every cluster's undocumented-work scan. None of these is a defect on its
own; they are recorded so the corpus's design record is honest about what code exists.

- **`ops/lifecycle/preflight.py:124 check_constitution`** — the live boot-time
  Constitution-fingerprint gate (the closest realized analog to core-integrity's "verify a
  blessed hash at startup," scoped to one file). Not homed in any note; operationalizes
  Invariant 9 / alignment §2's conformance conjunct.
- **`core/stores/sourceset.py` + `index.py:122-136` `grouped_semantic_search`** — the
  "source-set as a typed relation" retrieval; documented by the provenance-spectrum growth
  path (roadmap §1) and PROGRESS, not by an ingest design note.
- **`core/ingest/curated.py`** — CURATED self-knowledge ingest (same one-pipeline shape as
  dialogue/founding); documented by the provenance-spectrum note only.
- **`core/ingest/verify.py`, `scripts/migrate_provenance_split.py`, `scripts/migrate_chunk_keys.py`**
  — retrieval-integrity re-derivation + migration tooling; referenced in PROGRESS, not spec'd.
- **The `core/complex/` compute package** (build/spectral/curvature/topology/blocks/balance/cut/
  laplacian/support/temporal + `complex_types.py`) — imported only by the flag-off `dream_v2`/
  `run_panel`, *except* `complex_types.py`'s enums which live stores import (`derived.py:32`,
  `edges.py:22`). Documented by Track-H / companion-III / dreaming-v2 notes.
- **`edge/bridge/{bridge,protocol}.py`** — a research-airlock S3 bridge (`ResearchBridge`),
  present + tested (`test_research_airlock.py`), **no live caller**; documented by a
  research-airlock note (not in the audited set — worth confirming one exists).
- **`edge/interface/adapter.py WhatsAppAdapter`** — a third-party network adapter, present,
  not exercised live (`LocalAdapter` is what `talk.py` uses).
- **`core/factory/*` Vault↔attestation accessor join** (`factory.py:49-53,159-161`,
  `secrets_backend.py:57 role_for_accessor`) — the audit-handle join; a Step-5 addition
  post-dating vault-runtime-auth.md.
- **`ops/backup/` + `scripts/build_sandbox_image.sh` + `ops/sandbox/Containerfile`** — backup
  plan/run (enabled on this machine via local.toml) and the sandbox libs image / data-piping
  seam; in PROGRESS, not in a design note.
- **`.claude/hooks/_lib.py`** (≈25 KB) — the actual decision engine behind all six hook
  wrappers; described in agent-workflow §6 prose but itself substantial. `.claude/agents/`
  custom agent defs undocumented. `core/matching/` is a reserved empty scaffold (BUILD-SPEC §18).
- **`core/verdict/taxonomy.py`** — the ratified 5-category disposition set that *consciously
  excludes* recursive-strata §8's "promote insight weight" (the ≤5 fatigue bound); the code
  documents the rationale, the note does not.

---

## 4. Proposed completed-format front-matter (Step 4) — NOT APPLIED

The following notes are **BUILT & WIRED and stable**, and should carry current
artifact-chain front-matter with `status: ratified`. **I am NOT applying these** —
`docs/design-notes/**` is on the foundation denylist and `draft→ratified` is an
owner-only hand edit at the blessing gate (§10). Presented for by-hand application.
`created:` values are best-estimates — **preserve each note's true original date**;
`updated: 2026-07-06`. Each block's realization evidence is the corresponding §2 row.

**1. the-edge-model.md** — realized: E_geom⊔E_disp partition (`core/complex/build.py:139-152`).
Caveat: reconcile §3 wording to store-identity before ratifying (finding-0013).
```yaml
type: design-note
id: dn-the-edge-model
status: ratified
created: 2026-07-01        # verify/preserve
updated: 2026-07-06
links:
  - docs/design-notes/build-plans/edge-and-supersession-build-plan.md
  - docs/design-notes/recursive-strata.md
  - docs/findings/finding-0013.md
supersedes: null
superseded_by: null
warrant: null
```

**2. ingest-identity-and-amendment.md** — realized: `core/ingest/index.py`, `amend.py`,
`core/stores/versions.py`, wired `sync.py:97,110`.
```yaml
type: design-note
id: dn-ingest-identity-and-amendment
status: ratified
created: 2026-07-04        # verify/preserve
updated: 2026-07-06
links:
  - docs/design-notes/supersession-lifecycle.md
  - docs/design-notes/build-plans/sacred-boundary-build-plan.md
supersedes: null
superseded_by: null
warrant: null
```

**3. founding-corpus.md** — realized: `core/ingest/founding.py`, `scripts/ingest_founding.py`.
```yaml
type: design-note
id: dn-founding-corpus
status: ratified
created: 2026-07-04        # verify/preserve
updated: 2026-07-06
links:
  - docs/design-notes/ingest-identity-and-amendment.md
  - docs/design-notes/the-edge-model.md
supersedes: null
superseded_by: null
warrant: null
```

**4. vault-sync-and-capture.md** — realized: `core/ingest/watch.py`, `sync.py`, wired
`launcher.py:74,122,128`.
```yaml
type: design-note
id: dn-vault-sync-and-capture
status: ratified
created: 2026-06-25        # verify/preserve
updated: 2026-07-06
links:
  - docs/design-notes/ingest-identity-and-amendment.md
supersedes: null
superseded_by: null
warrant: null
```

**5. verdict-authority.md** — realized: `core/verdict/`, `core/stores/verdicts.py`, wired
`scripts/verdict.py` + Ambassador transport. Caveat: §5 hardware-MFA and the weight-promotion
half remain parked sub-items — ratify the *authority mechanism*, keep those flagged parked.
```yaml
type: design-note
id: dn-verdict-authority
status: ratified
created: 2026-07-04        # verify/preserve
updated: 2026-07-06
links:
  - docs/design-notes/the-sacred-boundary.md
  - docs/design-notes/recursive-strata.md
  - docs/design-notes/live-adoption-and-longitudinal-harness.md
supersedes: null
superseded_by: null
warrant: null
```

**6. ambassador-as-reasoning-agent.md** — realized: `agents/ambassador/*`, wired
`launcher.py:117-124`. This is the *authoritative* Ambassador note.
```yaml
type: design-note
id: dn-ambassador-as-reasoning-agent
status: ratified
created: 2026-06-28        # verify/preserve
updated: 2026-07-06
links:
  - docs/design-notes/ambassador-interpretation-and-flow.md
  - docs/design-notes/nervous-system-and-ambassador.md
supersedes: dn-ambassador-interpretation-and-flow   # partial — see note 7
superseded_by: null
warrant: null
```

**7. ambassador-interpretation-and-flow.md** — realized + **partially superseded** by note 6
(the note already declares this). Mark `superseded` rather than `ratified`.
```yaml
type: design-note
id: dn-ambassador-interpretation-and-flow
status: superseded
created: 2026-06-25        # verify/preserve
updated: 2026-07-06
links:
  - docs/design-notes/ambassador-as-reasoning-agent.md
supersedes: null
superseded_by: dn-ambassador-as-reasoning-agent
warrant: null
```

**8. dreamer-quality-suite-evaluation.md** — realized: `tests/fixtures/dreamer_adapter.py`,
`tests/quality/`. (An evaluation/decision note; "adopt" is executed as a CI suite.)
```yaml
type: design-note
id: dn-dreamer-quality-suite-evaluation
status: ratified
created: 2026-06-28        # verify/preserve
updated: 2026-07-06
links:
  - docs/design-notes/dreaming-v2-interpreter-panel.md
  - docs/design-notes/holistic-testing.md
supersedes: null
superseded_by: null
warrant: null
```

**9. test-organization.md** — realized: the `tests/` reorg + markers (`pyproject.toml:52-75`).
Caveat: the reorg (the note's deliverable) is complete; `emergent/`+`longitudinal/` remain
empty homes (that is expected, not incomplete).
```yaml
type: design-note
id: dn-test-organization
status: ratified
created: 2026-06-27        # verify/preserve
updated: 2026-07-06
links:
  - docs/design-notes/holistic-testing.md
supersedes: null
superseded_by: null
warrant: null
```

**Already current-format:** `agent-workflow.md` (ratified YAML) and `core-integrity.md`
(draft YAML) — no change proposed; core-integrity is correctly `draft` (NOT BUILT).

**Explicitly NOT eligible** (built but not yet live, or incomplete — do **not** mark
completed): attestation-layer (PARTIAL — records wired, signing off), hands-and-the-effector-
layer (PNW), effector-risk-computation (PARTIAL), dialogue-ingest-and-recursion (PNW),
supersession-lifecycle (PARTIAL), recursive-strata (PARTIAL), recursive-dreaming (PARTIAL),
dream-phase-rnd-charter (PARTIAL), dreaming-v2-interpreter-panel (PNW), vault-runtime-auth
(PNW), skills-and-scope (PNW), skill-mining-pipeline (PNW), wasm-sandbox-runtime (PARTIAL),
alignment-subsystem (PARTIAL), holistic-testing (PARTIAL), nervous-system-and-ambassador
(PARTIAL), observed-data (PARTIAL), observed-iot (PARTIAL), secrets-management-evolution
(PARTIAL/superseded).

**Doctrine / research / not-built** (ratification is an owner call *independent of build*,
or the note is correctly non-terminal): the-sacred-boundary (DRAFT spine), security-planes
(research doctrine), stability-adjudication (parked R&D), dreaming-on-curated-graphs (NOT
BUILT), live-adoption-and-longitudinal-harness (NOT BUILT), core-integrity (draft, NOT BUILT),
recursive-strata-amendment (unapplied patch), roadmap-and-future-directions (non-binding),
planar_graphs / un-represent-ability (background surveys).

---

## 5. Findings filed (Step 5)

Eight findings filed this pass, all typed and routed to the orchestrator. Existing
`finding-0009` (open) is referenced, not re-filed.

| Finding | ftype | Theme |
|---------|-------|-------|
| [0010](../findings/finding-0010.md) | discovery | Cohort of notes' self-status understates built+wired reality (§4 resolves) |
| [0011](../findings/finding-0011.md) | spec-defect | "Wired ceiling ε=SENSING" overstates — no effector is wired (max live tier = none) |
| [0012](../findings/finding-0012.md) | discovery | Supersession/dialogue-recursion dynamics specified but wholly dormant ("nothing demotes from retrieval yet") |
| [0013](../findings/finding-0013.md) | spec-defect | Edge/supersession notes+plans assert mechanisms code realizes differently (assertion-authority field, SUPERSEDES cross-ref, "EdgeStore refuses", stale Item-6, DERIVED_STRATUM) |
| [0014](../findings/finding-0014.md) | discovery | Invariant-2 import-firewall is asymmetric (no edge→core lint) and not run by the GitLab CI |
| [0015](../findings/finding-0015.md) | discovery | Alignment "keystone" drift gauge is built but largely inert live (no periodic audit; dead narration seam) |
| [0016](../findings/finding-0016.md) | discovery | Execution/agency substrate present but undriven (sandbox/factory/mint/instructional-skill/wasm-untested; dead `bootstrap()`) |
| [0017](../findings/finding-0017.md) | discovery | `planar_graphs.md` uncatalogued orphan + naming collision; research surveys statusless |
| [0009](../findings/finding-0009.md) | discovery *(already open)* | `proposed→complete` escapes the readiness blessing (candidate amendment A7) |

**Minor observations recorded in §2 but not separately filed** (fold into the relevant
finding or handle in a status sweep): the attestation `att_output` index never created +
`signer` outside `signing_payload()` (attestation-layer §2); the `sensor_readings` schema
drift (observed-iot §2); the nervous-system integrated-note reading vs. only-§4-live;
`scripts/verdict.py` not calling `seal()` unlike the other entry scripts; security-planes §2
foundation-set enumeration not matched by the enforced denylist.

---

*End of audit. No note has been converted and no status flipped — awaiting owner review
before any `draft→ratified` blessing (owner-only, §10) or any tracking correction.*
