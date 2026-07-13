---
type: build-plan
id: bp-019
status: in-progress
design_ref:
  - docs/design-notes/self-sensing.md # B-b: §2.2 φ_self contract, §2.3 schema + S1, §2.5 seam sibling, §2.6 safety line
contract: builder
write_scope:
  - "core/stores/agent_observations.py"
  - "core/sensing.py" # APPEND the AgentSensingHandoff sibling block only; every existing contract in the file is untouched
  - "ops/self_sensor.py"
  - "scripts/sense_self.py"
  - ".githooks/post-commit" # ONE appended non-blocking invocation line (§6(g))
  - "ops/lifecycle/launcher.py" # ONE list entry in reset_targets() candidates (+ comment) — the oq-0013 grant precedent
  - "tests/unit/test_agent_observations.py"
  - "tests/unit/test_self_sensor.py"
  - "tests/unit/test_sensing_transport.py"
  - "tests/unit/test_interpreter_versions.py" # add the phi_self (version, hash) pair
  - "docs/build-plans/bp-019/**"
  - "docs/findings/**"
session_budget: 1
cost:
  estimate: { model: sonnet, tokens: 350k } # mold-following build (code store/sensor as template) with crisp acceptance; interfaces fully pinned
  actual: null
depends_on: [bp-018] # inherits the version-supersession mechanics + history sidecar + ratchet-test pattern — SATISFIED (bp-018 complete, merged 160fd2f, 2026-07-12)
parallelizable_with: [bp-022] # disjoint write_scope (sensing/self-sensor/agent-store vs dreaming/temporal/config; only docs/findings/** shared — new files, disjoint ID ranges 0057+/0052+); asserted at spawn 2026-07-12, graduation-author's amendment
created: 2026-07-12
updated: 2026-07-12
links:
  - docs/design-notes/code-observation-projection.md # the sibling precedent (§2.2 interpreter contract, §2.4 seam)
  - docs/brainstorms/cost-forecasting.md # S1's origin thread; the parked report generator stays parked there
  - docs/brainstorms/self-sensing.md # owner capsules (stateless sensor; ledger-class ruling)
supersedes: null
superseded_by: null
warrant: null
---

# Build Plan — B-b: the third stream — `AgentSensingHandoff` + `AgentObservationStore` + φ_self over the cost ledger

> **Every section below is required.** N/A is an accountability act.

## 0. Mode & provenance

Graduated 2026-07-12 from the **ratified** `dn-self-sensing` (§2.2/§2.3/§2.5/§2.6, B-b).
Investigation and planning produced this; implementation proceeds item-by-item on owner
approval. `proposed → ready` is the owner's hand edit. Second plan of the family:
requires bp-018's mechanics; bp-020 runs the history backfill this plan makes possible.

## 1. Objective

The agent's own operation becomes the third stream through the sensing seam: a
deterministic, stateless φ_self projects build-plan cost blocks (estimates at their
landing commit, actuals at theirs) through a new `AgentSensingHandoff` into a new
OBSERVED-only, interpreter-versioned `agent_observations` store — attested, idempotent
per commit, wired to the post-commit sync, consuming nothing.

## 2. Context manifest

1. `docs/design-notes/self-sensing.md` — whole note; §2.3's schema is the contract.
2. `core/stores/code_observations.py` — the mold (post bp-018: version mechanics
   included). Structural-OBSERVED moves copied, not adapted.
3. `core/sensing.py` — whole file; the sibling block lands at the end beside
   `CodeSensingHandoff` (`:285-349`), which is the shape to mirror.
4. `ops/code_sensor.py` — the sensor mold: `_project` seam round-trip, attestation,
   deterministic `git show sha:path` reads (`:244-263`), `INTERPRETER_VERSION` (bp-018).
5. `core/stores/observation_history.py` (bp-018) — the family sidecar this store's
   supersessions archive into (store discriminator `'agent'`).
6. `.githooks/post-commit` — the non-blocking hook pattern Item 8 extends.
7. `ops/lifecycle/launcher.py:496-525` — `reset_targets()`; Item 8's one line.
8. `docs/templates/build-plan.md:11-17` — the `cost:` block being parsed (the S1
   source's authoritative shape).
9. `docs/build-plans/bp-011/plan.md` (cost block) — the first live pair; the parse
   fixture that must work.

## 3. Investigation & grounding

- **Q1 — the seam-sibling question is settled.** `SensingHandoff.collect()` is typed to
  `SensedObservation` and `CodeSensingHandoff.collect()` to `CodeObservation`
  (`core/sensing.py:259-272,335-349`) — a second payload type cannot ride an existing
  handoff (bp-012 Q1, recorded in the sensing.py sibling banner `:285-292`). The
  sibling is the decided shape; this plan adds the third instance, not infrastructure.
- **Q2 — no outbound half.** Like the code stream, the instrument is local (the repo);
  nothing crosses toward a carrier, so no `Effect`/`EffectView` ceiling and no
  `[effectors]` gate apply (the `CodeSensingHandoff` docstring's reasoning,
  `core/sensing.py:306-312`, inherits verbatim — quoted in §6(c)).
- **Q3 — how does the cost fact reach a commit?** The `cost:` block lives in plan
  frontmatter (`docs/templates/build-plan.md:11-17`): `estimate` is set at graduation
  (lands with the plan's creating commit), `actual` is filled at seal (lands with the
  seal commit). So the fact's landing commit is discoverable as: the commit whose diff
  ADDS or CHANGES that fact in that plan file. First-parent diff semantics are required
  — plans land on main via merge commits from builder worktrees (observed repo-wide;
  e.g. bp-012/bp-013 landed by merge). Pinned §6(e).
- **Q4 — is the parse deterministic?** V3 ran 2026-07-12 (read-only, pre-ratification):
  every `docs/build-plans/*/plan.md` frontmatter parses deterministically; 4 complete
  estimate/actual pairs, 3 estimate-only, 11 pre-rule plans with no cost block (yield
  nothing, correctly). Known wrinkle: trailing `# comments` on cost lines (the bp-014
  `_scalar()` precedent in the hooks' parser) — the parser must strip them (§6(f)).
- **Q5 — where does φ_self hook into commit time?** `.githooks/post-commit` (versioned;
  `core.hooksPath` = `.githooks`) runs `scripts/snapshot_code.py` on main commits,
  non-blocking, idempotent-catch-up semantics. φ_self rides the same hook with the same
  pattern (Item 8): a sibling script invocation, never a second hook file.
- **Q6 — store engine (V4).** SQLite confirmed: CONVENTIONS §Data stores
  (`CONVENTIONS.md:15-18`) assigns SQLite to identity-keyed ledgers/state and DuckDB to
  telemetry time-series; this is an identity-keyed ledger (the code store's Q2
  precedent). Rejected alternative recorded: DuckDB (wrong lane — this is not
  append-heavy telemetry).
- **Q7 — what identifies φ_self's version?** bp-018's §6(a) pattern: declared
  `INTERPRETER_VERSION = "1.0.0"` in `ops/self_sensor.py` + a `(version, source-hash)`
  pair in `tests/unit/test_interpreter_versions.py` (sources: `ops/self_sensor.py`).
- **Q8 — can φ_self observe its own store?** Structurally impossible and must stay so:
  φ_self reads committed workflow artifacts (git trees); it writes SQLite rows under
  `data/` (gitignored, never committed). Domain excludes codomain (§2.6 cut 2). The
  test suite pins the sensor's read surface to `git` subprocess reads only.

**Additional risks surfaced during reading:** merge commits mean one fact can appear in
BOTH a worktree branch commit and its merge commit — but candidate commits come from
`rev-list main` (first-parent diffs, §6(e)), so the branch-side duplicates are never
candidates; the identity key would also absorb an accidental double-landing at
different shas as two honest readings of two commits (the join reads latest). Plans
edited in place (e.g. a cost-actual annotation, bp-020 Item 9) change a fact at a later
commit — that is a NEW observation at a new `commit_sha`, exactly the intended grain.

## 4. Reconciliation

- `core/sensing.py:285-292` (the sibling banner: "the biometric contract above … is
  untouched") → **[cross-ref: extension]** carried by Item 6: the banner's family
  description gains the third member; existing prose untouched.
- `ops/lifecycle/launcher.py` `reset_targets()` candidates comment block (`:503-518`)
  → **[cross-ref: extension]** carried by Item 8: `agent_observations.sqlite` joins
  with a comment citing dn-self-sensing §2.5 (readings corpus-class; history rides the
  bp-018 sidecar, guarded).
- `.githooks/post-commit` header comment ("Code-sensor agent sync on every commit") →
  **[cross-ref: extension]** carried by Item 8: header mentions both sensors.
- No corrections: nothing existing is wrong; this plan only adds the third instance.

## 5. Write scope

In: the new store, the sensing-seam sibling (append-only edit to `core/sensing.py`),
the new sensor + driver script, one hook line, one launcher list entry, four test
files, own plan dir, findings. Out, deliberately: `core/stores/code_observations.py`
and `ops/code_sensor.py` (bp-018's, read-only mold here); `core/mirror.py` /
`MIRROR_READABLE` (the firewall — literally untouched); design notes; templates; the
foundation denylist. The launcher and hook grants are each ONE line + comment; more is
stop-and-raise.

## 6. Interfaces pinned inline

**(a) The observation type + schema (note §2.3, verbatim contract):**

```python
@dataclass(frozen=True)
class AgentObservation:
    commit_sha: str    # time coordinate — the commit that landed the fact
    stream: str        # 'cost' ONLY in this plan (S1; other streams are NOT licensed)
    subject_id: str    # the artifact the reading is about, e.g. 'bp-011'
    key: str           # stream-scoped fact name: 'estimate' | 'actual'
    payload: dict      # the fact, structured verbatim (§6(f))
    # NO provenance field, NO interpreter field on the wire type: provenance is minted
    # at to_row() with no parameter (the SensedObservation/CodeObservation move,
    # verbatim); interpreter is passed at store-write time (bp-018 §6(c) shape).
```

```sql
CREATE TABLE IF NOT EXISTS agent_observations (
    commit_sha   TEXT NOT NULL,
    stream       TEXT NOT NULL,
    subject_id   TEXT NOT NULL,
    key          TEXT NOT NULL,
    payload      TEXT NOT NULL,      -- JSON
    interpreter  TEXT NOT NULL,      -- φ_self version (outside the identity key)
    provenance   TEXT NOT NULL,      -- always 'observed' (nothing else is written)
    observed_at  TEXT NOT NULL,
    PRIMARY KEY (commit_sha, stream, subject_id, key)
);
CREATE TABLE IF NOT EXISTS projections (   -- version-keyed from birth (bp-018 §6(e) shape)
    commit_sha   TEXT NOT NULL,
    interpreter  TEXT NOT NULL,
    batch_hash   TEXT NOT NULL,
    projected_at TEXT NOT NULL,
    PRIMARY KEY (commit_sha, interpreter)
);
```

**(b) The store** (`core/stores/agent_observations.py`) — mirrors the post-bp-018 code
store exactly: `add_batch(observations, *, interpreter, history=None) -> (int, int)`
with archive-then-replace into the family sidecar (`store='agent'`); `is_projected`/
`mark_projected` version-keyed; `all_rows(provenances=None)` / `rows_for(sha)` /
`count()` view-compatible; module-local `batch_content_hash` with sort key
`(commit_sha, stream, subject_id, key)`; `open_agent_observation_store()` →
`data/agent_observations.sqlite`. Provenance hardcoded at `to_row()`; **no API surface
anywhere in the module accepts a provenance value** (the B-b falsifier, ruled out by
construction and pinned by test).

**(c) The handoff sibling** (`core/sensing.py`, appended):

```python
AGENT_OBSERVATIONS = "agent_observations"

@dataclass
class AgentSensingHandoff:
    """Core-side handoff for the SELF sensing stream — φ_self's sole path in (§2.2).
    <handoff>/agent_observations/<commit_sha>.json   (ops writes → core collects)
    Deliberately ABSENT, same reasoning as CodeSensingHandoff verbatim: no Effect/
    EffectView ceiling, no [effectors] gate — no outbound half exists (the repo is a
    local instrument; nothing crosses toward a carrier). Inbound guarantees identical:
    payload carries no provenance field, to_row() mints observed with no parameter,
    ObservedView admits the rows, MirrorView refuses them."""
    handoff: Path
    def emit_batch(self, commit_sha: str, observations: list[AgentObservation]) -> str: ...
    def collect(self, *, consume: bool = True) -> list[AgentObservation]: ...
```

Handoff root: `cfg.paths.data_dir / "agent_sensing_handoff"` (the code stream's
convention, `ops/code_sensor.py:295`).

**(d) The sensor** (`ops/self_sensor.py`):

```python
INTERPRETER_VERSION = "1.0.0"   # φ_self's worldview coordinate; ratchet-pinned

@dataclass
class SelfSensor:
    repo: Path
    store: AgentObservationStore
    handoff: AgentSensingHandoff
    attestor: Attestor | None = None
    history: ObservationHistoryStore | None = None
    branch: str = "main"
    def sync(self) -> SelfSyncReport: ...
        # candidates = git rev-list --reverse <branch> -- 'docs/build-plans/*/plan.md'
        # for each sha not is_projected(sha, INTERPRETER_VERSION): project (§6(e)),
        # emit→collect→add_batch→mark_projected, attest. FULL-history reconcile by
        # construction (PD-d: backfill is the default; V3 measured the parse trivial) —
        # the first live run IS the backfill, executed as bp-020, not here.

def build_self_sensor(config=None) -> SelfSensor: ...
```

Attestation: `agent_role="self_sensor", action="project_agent_observations",
input_hashes=[sha], output_hashes=[batch content hash]` (note §2.2, verbatim). A
zero-fact commit marks projected with the empty-batch hash — a recorded no-op (the
projections-table precedent), never a rescan-forever.

**(e) The projection function (φ_self v1.0.0, deterministic):** for candidate commit
`sha`: changed plan files = `git diff-tree --no-commit-id --name-only -r -m
--first-parent sha -- docs/build-plans` filtered to `*/plan.md`; for each, parse the
`cost:` block from `git show sha:path` (never the working tree) AND from
`git show sha^:path` (first parent; absent file ⇒ no prior facts); emit one
`AgentObservation(stream='cost', subject_id=<frontmatter id:>, key=<'estimate'|'actual'>)`
for each fact that is present at `sha` and absent-or-different at the parent. Root
commits (no parent) treat all present facts as new.

**(f) The payload (v1 worldview, recorded):**

```python
{"model": "sonnet", "tokens": 350000, "tool_calls": 142, "duration_min": 19,
 "raw": "{ model: sonnet, tokens: 350k }"}
# tokens normalized: '350k' → 350000, '1.2m' → 1200000, bare int passes; model
# lowercase str; tool_calls/duration_min optional (absent keys omitted); 'raw' keeps
# the source text verbatim. Trailing '# comments' stripped BEFORE parse (the bp-014
# _scalar() wrinkle, Q4). null/absent actual ⇒ NO observation (a fact not yet in the
# world, not an empty reading). An unparseable non-null block ⇒ no observation + a
# WARNING in the report — deterministic skip, and a template-tightening finding is
# filed (note V3's re-entry for PD-d).
```

Parser: stdlib-only (line-based over the frontmatter block, the V3 probe's approach) —
no new dependency for a 6-line block.

**(g) The hook line** (`.githooks/post-commit`, appended after the snapshot line, same
non-blocking pattern):

```sh
$RUN scripts/sense_self.py 2>&1 || echo "self-sensor sync failed (non-blocking; next sync heals)"
```

`scripts/sense_self.py` mirrors `scripts/snapshot_code.py`: print
`build_self_sensor().sync()`.

**(h) The reset line** (`ops/lifecycle/launcher.py` `reset_targets()` candidates):
`p.data_dir / "agent_observations.sqlite"` + comment: readings corpus-class
(dn-self-sensing §2.5); worldview history rides the guarded `observation_history.sqlite`
sidecar (bp-018).

## 7. Items

_(family numbering continues from bp-018)_

### Item 5 — `AgentObservationStore` (structural OBSERVED, versioned from birth)

- **Objective:** `core/stores/agent_observations.py` per §6(a,b) + its suite.
- **Files:** `core/stores/agent_observations.py`, `tests/unit/test_agent_observations.py`
- **Acceptance test:** suite green: same-batch idempotence (row count unchanged — the
  note's falsifier inverted); bumped-interpreter supersession archives to the family
  sidecar under `store='agent'`; a reflective test asserts NO public API accepts a
  `provenance` argument (inspect signatures); `ObservedView` admits `to_row()` rows;
  `MirrorView` refuses them.
- **Falsifier:** any API surface accepting a provenance parameter, or a second
  projection of the same batch changing row count (note §3.3 B-b, verbatim).
- **Invariant(s):** rows unrepresentable outside `observed`; identity key exactly
  `(commit_sha, stream, subject_id, key)`; interpreter outside it.
- **Touches stored data?** no
- **Parallelizable?** yes (with Item 6) **Depends on:** bp-018 Items 2–3

### Item 6 — `AgentSensingHandoff` (the seam's third instance)

- **Objective:** the sibling block per §6(c), appended to `core/sensing.py`; transport
  tests.
- **Files:** `core/sensing.py`, `tests/unit/test_sensing_transport.py`
- **Acceptance test:** emit→collect round-trip (atomic file, consume-and-heal: a batch
  left by a "crash" is collected on the next pass); batch content hash deterministic
  across re-emission; existing transport tests untouched and green.
- **Falsifier:** the biometric or code contract changes in any way (the sibling rule:
  own payload type, own dir, zero shared mutation) — diff of the file outside the
  appended block must be empty.
- **Invariant(s):** no `Effect` ceiling and no `[effectors]` gate on this stream (Q2 —
  no outbound half); `SenseRequest`/`SensedObservation`/`CodeObservation` contracts
  byte-identical.
- **Touches stored data?** no
- **Parallelizable?** yes (with Item 5) **Depends on:** none

### Item 7 — φ_self v1.0.0 (the cost-stream projector)

- **Objective:** `ops/self_sensor.py` per §6(d,e,f); the ratchet pair added to
  `tests/unit/test_interpreter_versions.py`.
- **Files:** `ops/self_sensor.py`, `tests/unit/test_self_sensor.py`,
  `tests/unit/test_interpreter_versions.py`
- **Acceptance test:** on a fixture repo (tmp git repo with plan files evolving across
  commits incl. a merge and a root commit): estimate lands at its landing commit,
  actual at the seal commit, edits land as new-commit observations; re-`sync()` adds
  zero rows; a zero-fact commit is marked projected (no rescan); token normalization
  table-tested ('350k'→350000, '1.2m'→1200000, int passthrough); trailing-comment
  stripping tested against the REAL bp-011 cost block text; attestation emitted per
  batch with the pinned action name.
- **Falsifier:** a second projection of the same commit changes row count (§3.3 B-b);
  or the sensor reads ANY source other than `git` subprocess output + config paths
  (statelessness broken — §2.6: it "reads deterministically, projection-maps, and
  forgets").
- **Invariant(s):** committed artifacts only (never the working tree, never
  transcripts); stream vocabulary exactly `{'cost'}`; determinism (same repo state ⇒
  same batch hash).
- **Touches stored data?** no (fixture repos + tmp stores)
- **Parallelizable?** no **Depends on:** Items 5, 6

### Item 8 — wiring: the hook line, the driver script, the reset entry

- **Objective:** `scripts/sense_self.py`; the `.githooks/post-commit` line per §6(g);
  `reset_targets()` entry per §6(h); reconciliation banners (§4).
- **Files:** `scripts/sense_self.py`, `.githooks/post-commit`,
  `ops/lifecycle/launcher.py`, `tests/unit/test_self_sensor.py`
- **Acceptance test:** `uv run scripts/sense_self.py` on the fixture exits 0 and prints
  the report line; the hook script still exits 0 when the sensor fails (non-blocking
  pinned by running the hook body with a poisoned command); `reset_targets()` lists
  `agent_observations.sqlite`; a non-main branch commit projects nothing (the hook's
  branch guard — existing line, verified still upstream of both sensors).
- **Falsifier:** a failing self-sensor blocks a commit (the hook's never-block contract
  broken); or reset dry-run omits the new store (readings would survive a corpus wipe —
  §2.5 violated in the corpus-class direction).
- **Invariant(s):** hook stays non-blocking and main-only; launcher change is one list
  entry; the code-sensor invocation line is byte-identical.
- **Touches stored data?** no (the live first run is bp-020's, deliberately)
- **Parallelizable?** no **Depends on:** Item 7

## 8. Math carried explicitly

N/A — no mathematical object implemented (deterministic parsing, content hashing via
the established sha256 pattern, and bookkeeping).

## 9. Non-goals

Any consumer (nothing reads `ObservedView` here); any stream beyond `cost` (PD-a:
additional streams re-enter per-stream with their own small plans); the live backfill
run (bp-020); the report generator (parked in `cost-forecasting.md`); transcript
parsing (PD-b: never); touching `MIRROR_READABLE`, the mirror, or the dreamer; a
generic `ObservationStream` abstraction (note §5 rule-of-three: siblings stay explicit).

## 10. Stop-and-raise conditions

The frontmatter parse hits a plan file the stdlib parser cannot read deterministically
(V3 said none exists today — if one appears, stop: the parked template-tightening
decision re-enters, file the finding, park the file); the sibling append cannot avoid
touching an existing contract in `core/sensing.py` (spec-defect finding — the seam
family assumption broke); any need for a provenance/interpreter parameter on a wire
type (the structural firewall would be weakening — stop, that is a design question);
the hook's branch guard turns out not to cover the new line (never wire a sensor that
projects branch commits).

## 11. Parked decisions

| Decision | Default recorded | Rejected alternatives (why) | Re-entry condition |
| --- | --- | --- | --- |
| shared batch-hash helper | module-local `batch_content_hash` per store (siblings explicit) | generalize `code_observations.batch_content_hash` (premature abstraction; sort keys differ; rule-of-three not met — note §5) | a fourth stream arrives AND the three copies have measurably diverged |
| token normalization in-payload | normalized int + `raw` verbatim (v1 worldview) | raw-only (pushes parsing to every consumer); normalized-only (loses the source text a worldview bump might re-read) | a φ_self version bump re-decides; the chain records the change (that is the point) |
| candidate-commit scan | `rev-list <branch> -- docs/build-plans/*/plan.md` full-history reconcile | forward-only from wiring date (contradicts PD-d's backfill default); all-commits scan without pathspec (wasteful, same result) | never — decided here; the pathspec is the S1 domain |
| driver script granularity | own `scripts/sense_self.py` | folding into `scripts/snapshot_code.py` (couples two sensors' failure modes in one non-blocking line; hook line per sensor keeps degradation independent) | hook latency measurably matters |

## 12. Dependency & ordering summary

{Item 5 ∥ Item 6} → Item 7 → Item 8. All items reversible code/test/docs writes; the
only live-data effect (the first real projection over history) is deliberately deferred
to bp-020. Cross-plan: **depends_on bp-018** (family mechanics + sidecar + ratchet);
**bp-020 depends on this plan**. The post-commit hook line makes every future main
commit self-project incrementally once merged — bp-020's backfill covers everything
before that moment.
