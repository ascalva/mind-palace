# Verification audit — auditing the corpus audit (2026-07-06)

**Type:** read-only verification of `docs/audits/corpus-state-audit-2026-07.md` (the
"prior audit"). **Premise under test:** the prior audit had a directory-scope defect —
it checked implementation reality primarily against `core/ scripts/ tests/`, so any note
whose code lives elsewhere may be wrongly marked negative, and any finding filed on that
basis may be spurious. **Do not trust the prior report.**

**Nothing implemented, no note edited, no status flipped, no prior finding resolved or
withdrawn.** Writes this pass: this file, and `docs/findings/finding-0018..0020`. VCS is
jj-over-git; I used the filesystem (`ls`/grep/Read) for content, so colocation does not
affect any citation.

## Method

- **Step 0 — scope established empirically.** Listed every top-level entry and classified
  SOURCE vs NOISE. True source dirs: `agents/ bin/ cloud/ config/ core/ edge/ eval/ ops/
  scheduler/ scripts/ tests/ .claude/` + root config. `.py` distribution: tests 153,
  core 97, ops 22, scripts 16, edge 15, scheduler 9, eval 5, agents 5, config 3, cloud 3;
  non-py source: cloud 21 (Terraform+sh), ops 13 (sh), bin 1. `data/` confirmed
  source-free (runtime stores only — their presence proves the live path has run). The
  **only materially un-walked source dir was `cloud/`** (`agents/` holds only
  `ambassador/`, already covered; `bin/` is a verb dispatcher + dev shell tooling).
- **Step 0.5 — tracking record read in full** and treated as *claims to verify* against
  code: `docs/PROGRESS.md`, `docs/archive/PROGRESS-phases-0-10.md`, `docs/ROADMAP-V1.md`,
  `docs/runbook.md`, `docs/archive/HANDOFF.md`, `CHANGELOG.md`.
- **Steps 1–4.7** run as four independent evidence streams (three parallel subagents +
  direct owner-of-record checks), reconciled here. Live path re-confirmed directly:
  `scripts/palace.py start` → `ops/lifecycle/launcher.py build_components()` (`:66-170`)
  wires exactly six job kinds (vault-sync+watcher, Ambassador inbox, `ambassador_task`,
  dream, curate, watchdog/health) + the edge monitor iff `[monitor]` on
  (`scheduler/router.py:27-40` confirms no other kind). `config/local.toml` flips only
  `[secrets]` and `[backup]`.

EXISTS vs TESTED vs WIRED held distinct throughout.

---

## HEADLINE (Step 6)

1. **Did the scope defect materially change the corpus picture? — NO for status, YES for
   completeness.** The scope defect flipped **zero** status verdicts: all 23
   not-built/partial/PNW verdicts were re-confirmed across every dir including `cloud/`.
   What it *did* cost was completeness — a whole built + AWS-deployed subsystem (the
   research airlock; finding-0019) was invisible to the prior pass, and EXISTS-as-IaC
   evidence for three notes was missed. The **one** status correction — `the-edge-model`,
   BUILT & WIRED → PRESENT-BUT-NOT-WIRED — came from a **rigor** error (a flag-off call
   chain mis-traced), *not* the scope defect. Corrections concentrate in the reverse
   cross-check and EXISTS-evidence enrichment, not in status.
2. **Does the tracking record materially overclaim reality? — YES, on operational
   reality (not build/test status).** The CHANGELOG one-liners, the Phase-10/archive
   roll-up, and `README.md` log built-but-unwired subsystems (airlock, Vault-to-cloud,
   effectors ε=SENSING, drift keystone) as "complete / live / wired." The current
   `docs/PROGRESS.md` is itself honest and self-correcting; the overclaim lives in the
   terse summaries and stale status lines (finding-0020).

**Net:** the prior audit's *conclusions* are substantially sound (23/23 negatives stand,
9/10 positives upheld, 8/8 prior findings valid, none spurious), but it was **incomplete**
(missed the airlock + cloud IaC) and had **one wrong positive** (the-edge-model). Both
defects are corrected below.

---

## 1. Corrections summary (verdicts that CHANGED)

| Note | Prior verdict | Corrected verdict | Driver | Evidence |
|------|---------------|-------------------|--------|----------|
| the-edge-model.md | BUILT & WIRED | **PRESENT-BUT-NOT-WIRED** | **rigor** (not scope) | `build_complex`'s only caller is `core/dreaming/interpreters.py:249` (`build_structural_context`), reachable only via `dream_v2` (`dreamer.py:195`, gated `require_rnd_enabled` `:183`) and `run_panel` (`interpreters.py:294`, gated). Live cron `scheduler/cron.py:33` calls `dreamer.dream()` (v1, `dreamer.py:124-163`) which never assembles a complex. `core/dreaming/__init__.py:7-10` states the panel is "never wired into scheduler/cron.py." |

That is the **only** verdict-level change. The partition (`core/complex/build.py:139-162`)
EXISTS and is TESTED (`tests/integration/test_edge_partition.py`, which imports
`build_complex` directly — i.e. test-only), and some E_disp stores are written by live
ingest (`core/ingest/sync.py:111`), but the partition's computational purpose — E_geom
into the signed Laplacian, E_disp excluded — is exercised **only** on the flag-off
`[dream_rnd]` path. **Consequence:** `the-edge-model` is removed from the §4
completed-format proposals (a downgraded note is not eligible).

### Citation refinements (verdict unchanged, prior cite imprecise)
- **ingest-identity-and-amendment** (UPHELD BUILT & WIRED): the prior audit cited
  `amend.py:43-85`, which conflates the *wired* content-addressing (`chunk_point_id`,
  `amend.py:36-51`, used via `index.py:60-81 index_amendment`) with the *uncalled*
  `plan_amendment`/`AmendmentPlan` planner (`amend.py:54-85`, zero callers, gated behind
  an owner-ratified §4 go). The wired path is `index_amendment`, not `plan_amendment`.
- **ambassador-as-reasoning-agent** (UPHELD BUILT & WIRED): wired via `scripts/talk.py`'s
  in-process `ConversationRuntime`, not a self-driving daemon inbox — the daemon
  registers the `AMBASSADOR_KIND` handler (`launcher.py:122`) but `enqueue_ambassador_inbox`
  has no daemon caller. Still a genuine live path (talk.py).

### EXISTS-as-IaC enrichments (verdict unchanged; evidence the prior scope could not see)
- **vault-runtime-auth** (PNW): `cloud/terraform/airlock/vault_engine.tf` deploys §4's
  Vault **AWS dynamic secrets engine** — larger EXISTS than the prior `config/secrets_backend.py`
  cite; still PNW (no live `mint()` caller).
- **secrets-management-evolution** (PARTIAL): `cloud/terraform/backups/kms.tf` (restic
  SSE-KMS) + `vault_engine.tf` exist — but neither is this note's proposal (server-hosted
  Vault / KMS auto-unseal / AppRole-per-component), which remains not built.
- **observed-iot-and-cross-source-synthesis** (PARTIAL, seam-only): `ops/vault/policies/
  correlator.hcl` + `dreamer.hcl` provision a Vault `correlator` role reading
  `oura-daily-aggregates` — IaC *anticipating* the unbuilt correlator; verdict unchanged
  (no code, not wired). See finding-0019.

---

## 2. Confirmations — negatives now evidence-backed across the full tree (Step 1)

**All 23 negatives CONFIRMED**, re-derived by grepping every source dir (`agents/ bin/
cloud/ config/ core/ edge/ eval/ ops/ scheduler/ scripts/ tests/`). None overturned.

- **NOT BUILT (4):** core-integrity (no manifest/posture/seal-ceremony in any dir; only
  `preflight.py check_constitution`), dreaming-on-curated-graphs (no `CuratedView/
  resonance/cross_graph`), stability-adjudication (no runtime perturbation-consensus
  adjudicator; only test-time jitter/ablation), live-adoption-and-longitudinal-harness
  (`eval/longitudinal.py`, `core/dreaming/shadow.py`, `core/stores/runledger.py`,
  `scripts/{review,tune,curves}.py`, `config/tuning.toml` all absent).
- **PARTIAL (14):** attestation-layer (signing off `defaults.toml:175`; gate-emitter
  absent — verify-half only), supersession-lifecycle (certification layer no code;
  `apply_operations` no live caller), dream-phase-rnd-charter (R2–R5 absent),
  recursive-dreaming (no depth>1 path), effector-risk-computation (no reachability
  measure/optimizer), recursive-strata (no strata/budgets), nervous-system (`class Auditor`
  zero hits anywhere; §1 tripwire absent; only §4 OpsView live), observed-data
  (no imap/smtp/ical/rss impl — those tokens are the import ban-list), observed-iot
  (no correlator/biometric/oura/sensor-writer code), secrets-management-evolution
  (no approle/auto_unseal/KMS-unseal), wasm-sandbox-runtime (inert config; `_run_wasi`
  untested), alignment-subsystem (`measure_drift`/`alignment_snapshot` no live caller),
  holistic-testing (emergent/longitudinal 0 test files), roadmap-and-future-directions
  (forward items absent).
- **PRESENT-BUT-NOT-WIRED (6):** dialogue-ingest-and-recursion, dreaming-v2-interpreter-panel,
  hands-and-the-effector-layer (effector import sweep of every live entry = empty),
  vault-runtime-auth, skill-mining-pipeline, skills-and-scope — each: code exists, no live
  caller in any dir.

**8 false-correction traps confirmed** (keyword collided; negative correctly stands):
`cloud/fetcher` "sources" = literature (OpenAlex/PMC/arXiv), not observed data →
observed-data/observed-iot stand; `vault_engine.tf` = AWS dynamic engine, not server-Vault/
auto-unseal → secrets-management stands; `backups/kms.tf` = restic SSE-KMS, not Vault
unseal; `correlator.hcl` = a Vault *policy*, not correlator code; `ops/lifecycle/runs.py
RunLedger` = clean-shutdown record, not the F4 runledger; `smtp/imap/poplib` = the
import ban-list; `tamper` = tamper-*evident* store property, not a §1 tripwire;
`core/vitals.py rss` = resident-set-size, not an RSS feed.

---

## 3. Positives — upheld vs downgraded (Step 2)

**9 UPHELD · 1 DOWNGRADED**, each re-derived by opening the cited code and tracing a live
call chain. None of the 10 verdicts rested on design-note prose.

| Note | Result | Live call chain (or why not) |
|------|--------|------------------------------|
| the-edge-model | **DOWNGRADED → PNW** | see §1 (flag-off `build_complex`) |
| ingest-identity-and-amendment | UPHELD | `sync.py:97,110-111` via `vault_sync_handler` (`launcher.py:122`) |
| founding-corpus | UPHELD | owner CLI `scripts/ingest_founding.py:29-37` (by design) |
| vault-sync-and-capture | UPHELD | `launcher.py:122,128,165,220` (daemon drives watcher+sync+catchup) |
| verdict-authority | UPHELD | CLI `scripts/verdict.py` + live Ambassador `agents/ambassador/__init__.py:88` (fail-safe None) |
| ambassador-as-reasoning-agent | UPHELD | `talk.py:117` → `ConversationRuntime.send` → `inbox.process_once` → handler |
| ambassador-interpretation-and-flow | UPHELD | same chain; note §3 lists 4 intents, code has 6 (partially superseded) |
| dreamer-quality-suite-evaluation | UPHELD | CI only (zero importers outside tests) — correctly *not* a runtime claim |
| test-organization | UPHELD | `pyproject.toml:48-77` markers pytest consumes; emergent/longitudinal empty (as stated) |
| agent-workflow | UPHELD | 6 hooks + `_lib.py` registered in `.claude/settings.json`; live-fire on events |

---

## 4. Reverse cross-check — built work the prior pass missed (Step 3)

1. **The research airlock's cloud tier — `cloud/fetcher/{handler,sources,aggregate}.py`**
   — a built + tested Lambda (OpenAlex/Europe PMC/arXiv aggregation + evidence ranking,
   `tests/integration/test_fetcher.py`). **No design note exists** (verified: none of the
   37 design-notes + 3 research notes covers it; its home is BUILD-SPEC §16). The prior §3
   *speculated* "a research-airlock note … worth confirming one exists" — it does not — and
   omitted `cloud/fetcher` entirely. → finding-0019.
2. **`cloud/terraform/` (bootstrap + airlock + backups)** — the whole AWS IaC tree
   (tfstate bucket, airlock S3+Lambda+IAM+`vault_engine.tf`, backups S3+`kms.tf`+IAM). No
   design note (operational; `cloud/README.md` + owner memory only). Prior §3 touched
   `ops/backup/` but missed all of `cloud/terraform/`. → finding-0019.
3. **`ops/vault/` deployment assets pointing at unbuilt code** — `policies/correlator.hcl`
   (+ `dreamer.hcl` "biometric aggregates") provision Vault roles/paths for a
   correlator/biometric pipeline with **no implementation** — IaC-ahead-of-code. → finding-0019.
4. **`bin/mind-palace` + `bin/mp-env.sh`** (minor) — the CLI verb dispatcher + 175-line env
   bootstrap; thin operational glue, absent from prior §3.

(The prior §3's other undocumented-work items — `preflight.check_constitution`,
`core/stores/sourceset.py`, `core/ingest/curated.py`, the `core/complex/` package,
`edge/bridge/`, `.claude/hooks/_lib.py`, etc. — were re-checked and stand.)

---

## 4.5 Prior-findings verification (Step 4.5) — recommended dispositions for owner triage

I did **not** edit or resolve any prior finding. Assessment against full-tree evidence:

| Finding | Assessment | Basis / recommended disposition |
|---------|-----------|----------------------------------|
| 0010 (stale note status cohort) | **VALID** | V3 status-conflict S5 confirms the notes understate deployed reality; §4 (minus the-edge-model) is the fix. **Stands.** |
| 0011 ("ε=SENSING wired" overstates) | **VALID** | Confirmed: no effector wired any tier (`build_components` import sweep = 0; `EffectView` default `effects.py` never constructed live). **Stands.** |
| 0012 (supersession dynamics dormant) | **VALID** | `apply_operations` no live caller; certification layer no code; `PROGRESS:1547` "nothing demotes from retrieval yet". **Stands.** |
| 0013 (edge/supersession contradictions) | **VALID** | V3 confirms S1 (DERIVED_STRATUM `PROGRESS:984-986` vs `provenance.py:54`), S2/S3 (stale plan status), and the §3 field / "EdgeStore refuses" overclaims. Independent of the the-edge-model downgrade. **Stands.** |
| 0014 (import-firewall asymmetry + GitLab CI) | **VALID (strengthened)** | Confirmed by direct read: `.gitlab-ci.yml` runs only SAST/secret/semantic-release; `.github/workflows/ci.yml` runs the lint. CHANGELOG commit links → `gitlab.com` ⇒ GitLab is the canonical host and does **not** run the Invariant-2 lint. **Stands; consider raising priority.** |
| 0015 (alignment gauge inert live) | **VALID** | V3 overclaim #5 confirms: `measure_drift` no live caller; only the boot fingerprint conjunct wired. **Stands.** |
| 0016 (execution substrate undriven) | **VALID (broaden)** | Confirmed (sandbox/factory/mint/instructional-skill/wasm). **Recommend broadening** to name the research airlock as another undriven substrate (finding-0019). **Stands.** |
| 0017 (planar_graphs orphan; surveys statusless) | **VALID** | Unaffected by scope. **Stands.** |

**No prior finding is INVALID-SCOPE or INVALID-RIGOR.** The scope defect produced *no*
spurious findings — because the prior audit *omitted* `cloud/` rather than mis-judging it
(it filed nothing about the airlock/cloud at all). All 8 survive.

---

## 4.7 Tracking-record reconciliation (Step 4.7) — three-way: docs vs CODE vs tracking

### OVERCLAIMS (tracking says done/live/wired; code shows unwired/partial)
- **Research airlock / Phase 8** — `CHANGELOG.md:58` "Phase 8 Complete" + `archive:1015`
  "research airlock (live)" ⟂ no live driver (`core/research/*`, `edge/bridge/*` referenced
  only by tests; `PROGRESS:267` itself concedes it). TF *was* applied later (`archive:824`)
  so S3/Lambda/IAM is live — "complete" = deployed, not driven. → finding-0019/0020.
- **Vault "production setup … to access cloud"** — `CHANGELOG.md:39` + `archive:806/857`
  "Phase A+B DONE" ⟂ nothing on the daemon consumes Vault; the bridge still uses a static
  SSO profile (`archive:855` "wiring it to mint from Vault … is Phase 5 work, not done
  here"). **New overclaim (beyond the prior audit).** → finding-0020.
- **Track G "WIRED ceiling ε=SENSING"** — `PROGRESS:1085-1087` ⟂ no effector wired
  (`EffectView` type default only). → finding-0011.
- **Drift gauge A1 "keystone COMPLETE"** — `PROGRESS:78` ⟂ inert live; boot fingerprint
  only. → finding-0015.
- **"Complete and running"** — `README.md:32` ⟂ `palace start` drives six job kinds; the
  advanced layer is behind-flag/undriven. → finding-0020.

### GAPS (built reality the tracking under-conveys)
- **G1 — backups run outside `palace start`.** Phase 9 is genuinely deployed (restic
  snapshot `fbb9935a`, `archive:908-919`), but `ops/backup/` has no importer in
  `launcher.py`/`scheduler/`; it is driven by an independent launchd job
  (`ops/backup/com.mind-palace.backup.plist` → `backup.sh`). "backups (live)" is true but
  `palace start` alone performs none — easy to miss.
- **G2 — the live daemon is narrower than the summary implies** (see README overclaim).
- **G3 — attestation signing off despite a live verifier half** (`[attestation]=false`;
  `verify.py` enforces owner-signed gate decisions) — a dangling verify-half not surfaced
  in the CHANGELOG headline. (Prior audit caught it in §2.)

### STATUS CONFLICTS
- **S1** `PROGRESS:984-986` "DERIVED_STRATUM undone" ⟂ `PROGRESS:1257-1259` reserved +
  `provenance.py:54`. (finding-0013)
- **S2/S3** build-plan self-status ("Item 6 PLANNING ONLY", "Item 8 awaiting approval") ⟂
  PROGRESS + code show both executed + wired. (finding-0013)
- **S4** `hands…md §10` "G1–G7 ✅" ⟂ `PROGRESS:1084-1088` "behind the flag". (finding-0011)
- **S5** `vault-runtime-auth.md`/`secrets-management-evolution.md` "design only" *understate*
  deployed reality ⟂ `PROGRESS:327-336` "wiring win" + `archive` deployed. (finding-0010)

---

## 5. Findings I filed (Step 5)

Three new findings, all routed to orchestrator (I did not touch the prior 0010–0017):

| Finding | ftype | Theme |
|---------|-------|-------|
| [0018](../findings/finding-0018.md) | discovery | **Meta** — the audit ran with a directory-scope defect + one rigor error; procedure must derive source dirs empirically and reconcile cross-cluster contradictions before a WIRED verdict |
| [0019](../findings/finding-0019.md) | discovery | The research airlock (core/research + edge/bridge + cloud/fetcher + cloud/terraform) — built, AWS-deployed, tested, but no design note and no live driver — missed by the prior scope; incl. IaC-ahead-of-code (`correlator.hcl` for an unbuilt correlator) |
| [0020](../findings/finding-0020.md) | discovery | Tracking-record overclaim pattern — CHANGELOG/README/archive log built-but-unwired subsystems (airlock, Vault-to-cloud, effectors, drift) as "complete/live/wired" |

---

## Corrected §4 — completed-format proposals (revised; still NOT APPLIED)

The prior audit proposed 9 notes for `status: ratified`. After verification, **remove
the-edge-model** (downgraded to PRESENT-BUT-NOT-WIRED — not eligible). The remaining **8
stand** (all UPHELD in §3). No note was newly established as BUILT & WIRED (0 upward
corrections), so none is added. As before: **not applied** — `docs/design-notes/**` is
denylisted and `draft→ratified` is an owner-only hand edit at the blessing gate (§10).

**Eligible (8):** ingest-identity-and-amendment · founding-corpus · vault-sync-and-capture ·
verdict-authority (core mechanism; §5 HW-MFA + weight-promotion stay parked) ·
ambassador-as-reasoning-agent · ambassador-interpretation-and-flow (→ `superseded`, not
ratified) · dreamer-quality-suite-evaluation · test-organization. (Front-matter blocks as
in the prior audit §4, minus the-edge-model.)

**Removed:** ~~the-edge-model~~ — build-but-not-wired; re-propose only if the partition's
consumer (`build_complex`) is wired onto the live path.

---

*End of verification. The prior audit and this report are both retained — their diff is
signal. The owner reviews both before any status is flipped, any note ratified, or any
finding (0010–0020) resolved or withdrawn at triage.*
