---
type: build-plan
id: bp-048
alias: review-repl
status: in-progress
design_ref:
  - docs/design-notes/evaluation-harness.md   # §2.2 the verdict store + review REPL; §3 E6 (Track L L2)
contract: builder
write_scope:
  - scripts/review.py
  - eval/harness/probes.py
  - tests/integration/test_review_repl.py
  - tests/unit/test_probes.py
session_budget: 1
cost:
  estimate:
    model: opus
    tokens: 220k
  actual: null
depends_on: []
parallelizable_with: [bp-047]
created: 2026-07-16
updated: 2026-07-16
links:
  - docs/design-notes/evaluation-harness.md
  - docs/design-notes/live-adoption-and-longitudinal-harness.md   # protocol annex — Track L §3 (probes)
re_entry: null
supersedes: null
superseded_by: null
warrant: null
---

# Build Plan — E6: the review REPL + theory probes (the human-labeling surface the precision@review objective needs)

## 0. Mode & provenance

Investigation and planning produced this plan; implementation proceeds item-by-item on owner
approval. Authority-to-act (the owner's 2026-07-16 directive to graduate E6) is separate from the
readiness blessing (owner-only `proposed → ready`); no agent flips readiness. E6 is **independent of
all other harness plans** (it reads the BUILT `RunLedger` + the BUILT verdict store; it produces no
input any other plan consumes except the verdicts that later feed E7's `precision@review`). It has
no dependence on the σ-lever fork parking E3a-1.

## 1. Objective

Add `scripts/review.py` — a model-free REPL that interleaves the run ledger's phase7 vs dream_v2
claims (native A/B), captures keystroke owner verdicts (signed + stored through the BUILT verdict
path), and records theory probes for `plausible` claims — turning dream output into the labeled
ground truth `precision@review` will be computed from.

## 2. Context manifest

Read in order before any work:

1. `docs/design-notes/evaluation-harness.md` §2.2 (the verdict store + review REPL paragraph), §3
   E6, §2.6 (the EH-c upgrade: `precision@review` becomes the headline objective once L2 verdicts
   accrue past a floor — this REPL is how they accrue).
2. `docs/design-notes/live-adoption-and-longitudinal-harness.md` §3 (Track L §3 — the **protocol
   annex of record** for the review REPL AND the theory probes: keystroke verdicts, pipeline-labeled
   interleave, probe candidates). **The probe schema is grounded HERE, not inferred** (see §3 Q4).
3. `core/stores/runledger.py` — `RunLedger`: `runs()`, `claims()`, the `dream_runs`/`dream_claims`
   schema, the content-addressed `claim_id`, the `pipeline` column, `novel`. The REPL's data source.
4. `scripts/verdict.py` — the whole file: the owner-signing path (`get_secret` → `sign_verdict` →
   `build_verdict_receiver`), the taxonomy check, the default-seq rule. The REPL REUSES this path.
5. `core/verdict/payload.py` (`VerdictPayload`, `sign_verdict`, `SignedVerdict.verify`),
   `core/stores/verdicts.py` (`VerdictStore.append`, `open_verdict_store`, `latest_seq`),
   `core/verdict/apply.py` (`build_verdict_receiver`, `effect_of`), `core/verdict/taxonomy.py`
   (`VERDICT_TAXONOMY`).

## 3. Investigation & grounding

- **Q1 — What does the REPL display, and how is A/B "native"?** `RunLedger.claims(run_id=None)`
  returns all claim rows; each carries its `run_id`, and `runs()` maps `run_id → pipeline`
  ("phase7"|"dream_v2") — `runledger.py:171-186`, schema `:79-95`. Interleaving claims labeled by
  their run's pipeline IS the A/B: the reviewer judges blind-to-source or source-labeled, and
  precision splits by pipeline fall out of the verdict × pipeline join. No separate A/B machinery.
- **Q2 — What is a claim's verdict `subject_id`?** The content-addressed `claim_id`
  (`sha256(kind ‖ canonical(support) ‖ polarity)`, excluding surface wording + confidence —
  `runledger.py:34+`), so a re-emitted claim across runs shares one verdict subject (the note's
  "re-emitted claims inherit prior verdicts"). The REPL uses `claim_id` as `VerdictPayload.subject_id`.
- **Q3 — How does a keystroke verdict get signed + stored, reversibly and fail-closed?** Exactly
  `scripts/verdict.py`'s path: `seed = get_secret(cfg.attestation.owner_key_secret)`; refuse if
  absent (`scripts/verdict.py:43-47`); `signed = sign_verdict(VerdictPayload(subject_id=claim_id,
  verdict=<key>, seq=<next>, timestamp), Ed25519Signer.from_seed(seed, "owner"))`; then
  `build_verdict_receiver(cfg)(signed)` verifies + appends (monotonic seq) + applies the disposition
  (`core/verdict/apply.py:50-53`). The store is append-only (no update/delete); a correction is a new
  verdict at a higher seq (`verdicts.py` boundary comment). The REPL adds NO new persistence path.
- **Q4 — Is the theory-probe schema settled by the code?** No — the code does not settle this; the
  BUILT surface has no probe store. The probe protocol lives in the **Track L §3 protocol annex**
  (context manifest #2). The builder grounds the probe shape THERE and, if the annex is ambiguous or
  implies a store this plan can't scope, STOPS and files a finding (§10) rather than inventing a
  schema. Default scope: a probe is a recorded *candidate* (claim_id + the probe question) emitted
  when the owner verdicts a claim `plausible`; probe *execution* (a dreamer-alone run) is out of scope
  (that is catalog row 12 / the R-gated demon protocol).
- **Q5 — Does the REPL hold a model?** No. "review REPL (`scripts/review.py`, model-free display,
  keystroke verdicts, pipeline-labeled interleave = native A/B)" — note §2.2. Display + keystroke
  capture + signing only; no model in the path (Invariant: the model advises, code acts).

**Additional risks surfaced during reading:** (a) the REPL writes signed owner verdicts to the live
verdict store — this is the owner's own act at their terminal (they hold the key), NOT an agent
write; the builder tests against an in-memory store + a test signer and NEVER invokes the real
signed path. (b) Verdicts are operational ground truth, ∉ `MIRROR_READABLE` (note §2.2) — the REPL
must not route any verdict or claim surface into a mirror-readable location.

## 4. Reconciliation

- `docs/design-notes/evaluation-harness.md` §2.2 — *"the review REPL (`scripts/review.py` …) …
  carry unchanged from Track L §3."* → **cross-reference-on-extension**: this plan builds
  `scripts/review.py` for the first time (it does not exist on disk — verified) over the ALREADY-BUILT
  verdict store; it extends, correcting nothing. The one prior art it composes with — `scripts/verdict.py`
  (the single-verdict transport CLI) — is a **read-only dependency reused verbatim**, not modified: the
  REPL is the batch/interactive sibling over the same signing+receiver primitives.
- No committed code is corrected. `RunLedger`, the verdict modules, and `scripts/verdict.py` are
  read-only dependencies, NOT in `write_scope`.

## 5. Write scope

- `scripts/review.py` — the REPL (new).
- `eval/harness/probes.py` — the probe-candidate model + recorder (new; schema grounded in the Track
  L §3 annex at build).
- `tests/integration/test_review_repl.py`, `tests/unit/test_probes.py` — tests (new).

**Deliberately OUT of scope** (read-only dependencies): `core/stores/runledger.py`, `scripts/verdict.py`,
`core/verdict/**`, `core/stores/verdicts.py`, `config/loader.py`, and every foundation-denylist file.
No modification to the verdict store schema, the signing primitives, or the run ledger.

## 6. Interfaces pinned inline

```python
# core/stores/runledger.py — the REPL's data source (verbatim)
class RunLedger:
    def runs(self, *, pipeline: str | None = None) -> list[dict[str, Any]]      # run_id, pipeline, corpus_digest, config_fingerprint, ...
    def claims(self, *, run_id: str | None = None) -> list[dict[str, Any]]      # claim_id, run_id, kind, confidence, support_json, surface_text, polarity, novel
def open_run_ledger(config: Any = None) -> RunLedger
# claim_id = sha256(kind ‖ canonical(support_set) ‖ polarity)  — excludes surface wording + confidence

# core/verdict + core/stores/verdicts — the signing + store path (verbatim; reuse, don't reimplement)
@dataclass(frozen=True)
class VerdictPayload:
    subject_id: str; verdict: str; seq: int; timestamp: str      # __post_init__ rejects seq < 0
def sign_verdict(payload: VerdictPayload, signer: Ed25519Signer) -> SignedVerdict
class SignedVerdict:
    def verify(self, public_b64: str) -> bool
    def to_dict(self) -> dict; @classmethod def from_dict(cls, d) -> SignedVerdict
class VerdictStore:                                              # append-only; append + reads only
    def append(self, signed: SignedVerdict, *, public_b64: str) -> VerdictRecord   # verifies + monotonic-seq
    def all(self) -> list[VerdictRecord]; def latest_seq(self) -> int | None; def gaps(self) -> list[int]
def open_verdict_store(config=None, allowed_verdicts: Iterable[str] | None = None) -> VerdictStore
# core/verdict/apply.py
def build_verdict_receiver(config) -> Callable[[SignedVerdict], VerdictRecord]     # verify + store + apply, fail-closed
def effect_of(verdict: str) -> Effect                            # novel_useful⇒promote, wrong/noise⇒retract, ...
VERDICT_TAXONOMY: frozenset[str] = {"novel_useful","true_known","plausible","wrong","noise"}

# scripts/verdict.py — the owner-key sourcing to REUSE (verbatim pattern)
seed = get_secret(cfg.attestation.owner_key_secret)             # Keychain: attestation-owner-key; refuse if absent
signer = Ed25519Signer.from_seed(seed, "owner")
seq = (open_verdict_store(cfg).latest_seq() or 0) + 1           # one past the stored maximum
```

## 7. Items

### Item 17 — `scripts/review.py`: the model-free review REPL (interleaved A/B + keystroke signed verdicts)

- **Objective:** load claims via `RunLedger.claims()`, interleave by pipeline (labeled or blind),
  present each claim (surface_text, kind, confidence, novel, pipeline), read a keystroke mapped to a
  `VERDICT_TAXONOMY` category, and for each verdict sign+submit through `build_verdict_receiver` with
  `subject_id = claim_id`; skip/quit keys; a session summary (counts per verdict × pipeline).
- **Files:** `scripts/review.py`.
- **Acceptance test:** `uv run pytest tests/integration/test_review_repl.py -q` green, driving the
  REPL loop against an in-memory `RunLedger` (seeded phase7 + dream_v2 claims) + an in-memory
  `VerdictStore` + a **test** `Ed25519Signer` (generated seed, `test_verdict_signing.py` idiom) +
  scripted keystrokes: each verdict lands as a signed, seq-monotonic record whose `subject_id` is the
  claim_id; a re-emitted claim's verdict reuses the same subject_id; an out-of-taxonomy keystroke is
  rejected without a store write; the summary counts split correctly by pipeline.
- **Falsifier:** a stored verdict's `subject_id` is the run_id or surface text (not the claim_id, so
  re-emission wouldn't inherit); OR a verdict is written unsigned / bypassing `build_verdict_receiver`;
  OR the REPL imports or invokes any model.
- **Invariant(s):** model-free (the model advises, code acts); append-only verdict store (no update/
  delete; corrections are new higher-seq verdicts); verdicts ∉ `MIRROR_READABLE`; fail-closed on a
  missing owner key (refuse, as `scripts/verdict.py:43-47`).
- **Touches stored data?** Yes — signed verdicts to the verdict store (+ dispositions via apply). The
  builder exercises ONLY the in-memory/test-signer path; the real signed store is the owner's act at
  their terminal, never the builder's. No dry-run needed beyond the test harness (append-only is
  self-reversible by a corrective higher-seq verdict; there is no destructive write).
- **Parallelizable?** No (Item 18 composes with it). **Depends on:** none.

### Item 18 — `eval/harness/probes.py`: the theory-probe candidate recorder

- **Objective:** when the REPL verdicts a claim `plausible`, record a probe candidate (claim_id +
  the probe question + provenance key) per the Track L §3 annex schema; expose a reader for the
  report/E7 to enumerate open probes.
- **Files:** `eval/harness/probes.py`; wired into `scripts/review.py` (the `plausible` branch).
- **Acceptance test:** `uv run pytest tests/unit/test_probes.py -q` green: a `plausible` verdict in
  the REPL emits exactly one probe candidate keyed to the claim_id; a non-`plausible` verdict emits
  none; the recorder is append-only and idempotent by (claim_id, question).
- **Falsifier:** a probe is emitted for a non-`plausible` verdict, OR probe execution (a dreamer-alone
  run) is implemented here (that is catalog row 12, R-gated — out of scope), OR the probe schema is
  invented rather than grounded in the annex.
- **Invariant(s):** probes are candidates/records only — never a run trigger (the demon protocol is
  owner-gated, note §2.3 row 12); probe records ∉ `MIRROR_READABLE`.
- **Touches stored data?** Yes — a new probe-candidate store (small, additive, its own file/table);
  append-only. Verify the schema against the annex before the first write.
- **Parallelizable?** No. **Depends on:** Item 17 (composes into its `plausible` branch).

## 8. Math carried explicitly

N/A — no mathematical object implemented. (The A/B "split" is a group-by over the verdict × pipeline
join, not an instrument; precision@review is computed in E7, not here.)

## 9. Non-goals

- No `precision@review` metric, no longitudinal curve, no `adoption_ready()` — **E7**.
- No probe *execution* / dreamer-alone run — catalog row 12, R3/R4-gated, owner-only.
- No change to the verdict store schema, signing primitives, run ledger, or `scripts/verdict.py`.
- No model anywhere in the REPL (display + capture + sign only).
- No mirror write of any verdict or claim.

## 10. Stop-and-raise conditions

- If the Track L §3 annex's probe schema implies a store or a run trigger this plan's `write_scope`
  cannot honor — STOP and file a `spec-fidelity` finding; do not invent a probe schema or overreach.
- If `build_verdict_receiver`'s disposition-apply has a side effect on the live projection the REPL
  must not trigger in a review session — STOP and file a `codebase` finding (the REPL should capture
  verdicts, not silently retract subjects mid-review unless that is the intended disposition).
- Any blessing the builder would have to perform: it must not.

## 11. Parked decisions

| Decision | Default recorded | Rejected alternatives (why) | Re-entry condition |
|---|---|---|---|
| blind vs source-labeled interleave | offer both (a flag); default source-labeled | blind-only (loses the A/B legend the owner wants); labeled-only (biases judgment) | owner preference after first use |
| probe-candidate store backend | small append-only table beside the verdict store (SQLite) | reuse the eval DuckDB (probes are records, not metric readings) | E7 needs probes joined to metrics |
| probe execution | out of scope (candidates only) | execute here (row 12 is R-gated, owner-only) | R-gate opened + owner runs the demon protocol |

## 12. Dependency & ordering summary

- **Items:** 17 → 18 (18 composes into 17's `plausible` branch). Blast-radius order: both write
  operational ground truth (append-only) — Item 17 (verdicts) before Item 18 (probe candidates).
- **Cross-plan:** `depends_on: []` — independent of E3a-1/E3a-2 and the σ fork.
  `parallelizable_with: [bp-047]` (E3a-2) — disjoint `write_scope` → real parallel builder fan-out
  once both are blessed. Feeds E7 (the verdicts become `precision@review`) and EH-c (the objective
  upgrade) — forward references, not dependencies.
