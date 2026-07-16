---
type: build-plan
id: bp-046
alias: sweep-levers
status: ready
design_ref:
  - docs/design-notes/evaluation-harness.md   # §2.6 the closed lever registry the manifest/sweep overlay; §2.9 the dual dreamers; §2.1 config_fingerprint
contract: builder
write_scope:
  - ops/levers.py
  - core/dreaming/shadow.py
  - tests/unit/test_levers.py
  - tests/unit/test_shadow_runner.py
session_budget: 1
cost:
  estimate:
    model: opus
    tokens: 120k
  actual: null
depends_on: []
parallelizable_with: []
created: 2026-07-16
updated: 2026-07-16
links:
  - docs/design-notes/evaluation-harness.md
  - docs/findings/finding-0087.md
re_entry: null
supersedes: null
superseded_by: null
warrant: docs/findings/finding-0087.md   # the σ-lever design fork; owner resolved 2026-07-16 = "register the [dream_rnd] knobs as levers"
---

# Build Plan — E3a-1a: register the swept `[dream_rnd]` knob as a lever + widen `_config_fingerprint` (the σ-fork resolution)

## 0. Mode & provenance

Investigation and planning produced this plan; implementation proceeds item-by-item on owner
approval. Authority-to-act (the owner's 2026-07-16 directive to graduate E3a-1) is separate from the
readiness blessing (owner-only `proposed → ready`); no agent flips readiness. This plan is the
**fork-resolution half** of E3a-1: the deliberate, reviewable registry diff that `ops/levers.py`'s
own docstring demands ("a visible, reviewable diff against this registry, never a guess",
`ops/levers.py:11-13`). It makes the knob the sweep engine (bp-049) will vary an actual §14-gated
lever, and makes the run's config identity reflect it. It is the σ-fork owner-resolved in
finding-0087 (register the `[dream_rnd]` knobs as levers), made concrete for the ONE knob the first
sweep needs.

## 1. Objective

Register `dream_rnd.sigma` (σ — the mirror-graph cosine edge threshold the shadow runner actually
reads) as a bounded lever in `ops/levers.py`, and widen `core/dreaming/shadow.py:_config_fingerprint`
so the run's `config_fingerprint` hashes the **live value** of every registered lever the runner reads
(the `[dreaming]` four AND `dream_rnd.sigma`) — so a σ-sweep both moves what `dream_v2` computes and
gives every grid cell a distinct eval-store key.

## 2. Context manifest

Read in order before any work:

1. `docs/findings/finding-0087.md` — the fork and the owner's resolution (register `[dream_rnd]`
   knobs as levers). This plan's warrant.
2. `ops/levers.py` — the whole file: the `Lever` dataclass (`name/section/key/kind/lo/hi/description`,
   `coerce`/`in_bounds`/`validate`), the `_LEVERS` tuple (the 4 `[dreaming]` levers, seeded from
   `defaults.toml` comments — the pattern this plan mirrors, `:75-112`), `LEVERS`, `get_lever`,
   `ProposedChange`. The module docstring (`:1-19`) is the design constraint: only config knobs,
   structural not policy, a reviewable diff.
3. `core/dreaming/shadow.py:94-105` (`_config_fingerprint`) + its call site `:136` + the dream_v2
   read path `:139-146` (`rnd = replace(cfg.dream_rnd, enabled=True)`; `MirrorGraph.build(view,
   sigma=rnd.sigma)`). This is the proof that `dream_v2` reads `dream_rnd.sigma`, NOT
   `dreaming.similarity_threshold`.
4. `config/defaults.toml:222-238` — the `[dream_rnd]` block: `sigma = 0.62  # σ: cosine edge
   threshold for the mirror graph (matches dreaming)`. The seed value + intent.
5. `config/loader.py:79-80` (`DreamingConfig`), `:256-263` (`Config` — `dreaming: DreamingConfig`,
   `dream_rnd: DreamRnDConfig`, both `@dataclass(frozen=True)`). Where the live values live.
6. `tests/unit/test_levers.py` (whole) + `tests/unit/test_shadow_runner.py:80-105` (the
   `config_fingerprint` assertions) — the retrofit surfaces (§5).

## 3. Investigation & grounding

- **Q1 — Which knob does `dream_v2` actually read for σ, and is it registered?** `dream_v2` (via the
  shadow runner) computes the mirror graph from `rnd.sigma` where `rnd = replace(cfg.dream_rnd,
  enabled=True)` — `shadow.py:139-141`, `MirrorGraph.build(view, sigma=rnd.sigma)`. `cfg.dream_rnd.sigma`
  defaults to `0.62` (`defaults.toml:229`). It is **NOT** a registered lever: the four registered levers
  are all `section="dreaming"` (`ops/levers.py:75-112`). The existing `dream_similarity_threshold` lever
  targets `dreaming.similarity_threshold` — which the shadow runner does not read for the graph. This is
  finding-0087's fork exactly: oq-0024's σ (`dreaming.similarity_threshold`) ≠ the runner's knob
  (`dream_rnd.sigma`).
- **Q2 — What does `_config_fingerprint` hash today, and why is that wrong for a sweep?** It hashes only
  the four `[dreaming]` live values (`shadow.py:98-104`). A σ-sweep varies `dream_rnd.sigma`, which is
  NOT in the hash → every cell gets the SAME `config_fingerprint` → the eval store's key
  `(spec_hash, corpus_ref, config_fingerprint, seed)` collapses across cells → `EvalResultsStore.put`
  skips every cell after the first as a "resume" (`store.py:100-104`, `put` returns False on a present
  key). So the current fingerprint breaks BOTH the curve (all cells one point) and resumability. The fix:
  hash the live value of every registered lever the runner reads.
- **Q3 — What bound for `dream_rnd.sigma`?** `[0.55, 0.75]` — the SAME range the `[dreaming]` σ lever
  carries (`ops/levers.py:82-83`) and the SAME range bp-040's σ-connectivity sweep used
  (`docs/build-plans/bp-040/plan.md:65-66`, "σ ∈ [0.55, 0.75]"). `kind = FLOAT`. The default `0.62`
  sits inside it. This is the deliberate, reviewable choice; the owner blesses it at `proposed → ready`.
- **Q4 — Is bp-047's `resolved_fingerprint()` the config_fingerprint?** NO — it hashes the manifest
  POLICY (subsystem/autonomy/objective + bounds), which is STATIC across a sweep (`eval/harness/tuning.py`,
  bp-047). The design note §2.1's phrasing "sha256 of the resolved tuning manifest" reads as if it were,
  but the cell-distinguishing identity a sweep needs is the live lever VALUES. This plan makes
  `config_fingerprint` = hash of live registered-lever values (extending the built behavior, not adopting
  the policy hash). See §4.
- **Q5 — Should this plan register ALL `[dream_rnd]` knobs, or just σ?** Just `dream_rnd.sigma` — the ONE
  the first sweep (`sweep.dreamer-sigma-ab`, §2.9) varies and oq-0024's headline. finding-0087 licenses
  registering "the `[dream_rnd]` knobs" (plural), but the minimal reviewable diff registers exactly what
  is needed now; the broader set (`agreement_jaccard`, `bridge_clustering_max`, the count knobs, the
  persistence knobs) is a §11 parked decision with a re-entry condition, NOT registered on a guess.

**Additional risk surfaced during reading:** the two σ knobs (`dreaming.similarity_threshold` and the
new `dream_rnd.sigma`) both mean "cosine edge threshold" but live in different sections and drive
different code paths (the live Phase-7 dreamer reads `dreaming.*`; the shadow `dream_v2` reads
`dream_rnd.*`). Registering both is correct — they are genuinely two knobs — but the lever `name`s must
be unambiguous (`dream_rnd_sigma` vs the existing `dream_similarity_threshold`) and each description must
say which path it drives, so a future sweep author cannot confuse them.

## 4. Reconciliation

- `docs/design-notes/evaluation-harness.md` §2.1 — *"`config_fingerprint` is the sha256 of the resolved
  tuning manifest."* → **clarification-on-extension** (banner in the code): the cell-distinguishing
  identity a sweep needs is the hash of the resolved live lever VALUES, not the manifest policy
  (bp-047's `resolved_fingerprint()`, which is static across a sweep). This plan keeps the built
  `_config_fingerprint` semantics (hash live values) and widens their coverage; it does NOT swap in the
  policy hash. The `_config_fingerprint` docstring (`shadow.py:94-97`) already anticipates this: *"E3 widens
  this to the full tuning manifest (parked, §11)."* This plan performs that widening — but over live
  values, and the code comment records the §2.1 clarification so the note and the code do not appear to
  disagree. (Whether to ALSO fold bp-047's policy fingerprint in as a second component is bp-049's call,
  parked there — the load-bearing part is the live values.)
- `core/dreaming/shadow.py:94-97` — the `_config_fingerprint` docstring's parked "§11" widening → this
  plan closes it; update the docstring to say "widened to the registered `[dream_rnd]` levers (bp-046)".
- `tests/unit/test_shadow_runner.py:90-91` — the assertion comment *"one [dreaming] lever set → one
  config_fingerprint"* becomes stale (the hash now covers `dream_rnd.sigma` too). Carried in `write_scope`
  and corrected by Item 12 (the assertion `len(fingerprints) == 1` still HOLDS — both pipelines share one
  `cfg`, so one fingerprint per run — but its rationale text is updated). No behavior of the assertion
  changes; only its now-wider basis.
- No other committed code is corrected. `config/loader.py`, `core/dreaming/interpreters.py`,
  `eval/harness/store.py` are read-only dependencies.

## 5. Write scope

- `ops/levers.py` — register `dream_rnd_sigma` in `_LEVERS` (new lever entry).
- `core/dreaming/shadow.py` — widen `_config_fingerprint` to hash the registered `[dream_rnd]` live
  value(s) alongside the `[dreaming]` four; update the call site + docstring.
- `tests/unit/test_levers.py` — carried because it pins the registry's exact contents (count / keys /
  `sorted(LEVERS)`), which this plan widens.
- `tests/unit/test_shadow_runner.py` — carried because it pins the `config_fingerprint` surface this plan
  widens (`:88-91`).

**Deliberately OUT of scope** (read-only dependencies, guard denies writes): `config/defaults.toml` and
`config/loader.py` (the σ knob + its bound already exist there — this plan promotes the bound into the
registry, it does not re-declare the value); `ops/selfmod.py` / `ops/ledger.py` (the gate is unchanged —
a new lever flows through the existing propose path untouched); `eval/harness/**` (the sweep engine is
bp-049); `config/tuning.toml` / `eval/harness/tuning.py` (bp-047's manifest — a new lever simply gains a
default-`propose` policy there, no edit needed); every foundation-denylist file.

## 6. Interfaces pinned inline

```python
# ops/levers.py — the registry entry to mirror (verbatim shape; add ONE like this)
@dataclass(frozen=True)
class Lever:
    name: str; section: str; key: str; kind: LeverKind; lo: float; hi: float; description: str = ""
    def validate(self, value: float) -> float | int: ...   # coerce + bounds-check, fail-closed
# the new entry (values are this plan's reviewable choice — §3 Q3/Q5):
Lever(name="dream_rnd_sigma", section="dream_rnd", key="sigma", kind=LeverKind.FLOAT,
      lo=0.55, hi=0.75,
      description="σ (dream_v2 lane): cosine edge threshold for the SHADOW mirror graph "
                  "(core/dreaming/shadow.py reads dream_rnd.sigma; distinct from "
                  "dream_similarity_threshold, which drives the live Phase-7 path).")

# core/dreaming/shadow.py — the fingerprint to widen (verbatim current body)
def _config_fingerprint(dreaming: DreamingConfig) -> str:
    levers = {"similarity_threshold": dreaming.similarity_threshold,
              "min_cluster_size": dreaming.min_cluster_size,
              "max_clusters": dreaming.max_clusters,
              "near_dup_threshold": dreaming.near_dup_threshold}
    canon = json.dumps(levers, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canon.encode()).hexdigest()
# call site: shadow.py:136 — `config_fingerprint = _config_fingerprint(cfg.dreaming)`
# Widen: take the whole Config (or cfg.dreaming + cfg.dream_rnd) and add every REGISTERED
# [dream_rnd] lever's live value to the hashed dict, keyed by "<section>.<key>" so it can never
# collide with a [dreaming] key. Derive the set from ops.levers.LEVERS (single source of truth),
# NOT a hardcoded list — so bp-049 widening the registry needs no second edit here.

# eval/harness/store.py — why the fingerprint must move per cell (verbatim)
def put(self, r: Reading) -> bool:   # False if (key, metric_name) already present -> SKIP (resume)
# key = EvalKey(spec_hash, corpus_ref, config_fingerprint, seed)
```

## 7. Items

### Item 12 — register `dream_rnd_sigma` + widen `_config_fingerprint` to the registered `[dream_rnd]` levers

- **Objective:** add the `dream_rnd_sigma` lever to `ops/levers._LEVERS`; widen
  `core/dreaming/shadow.py:_config_fingerprint` to hash the live value of every registered lever
  (derived from `ops.levers.LEVERS`, keyed `"<section>.<key>"`), so a σ-sweep gives distinct
  `config_fingerprint`s. Update the docstring + the retrofit assertions.
- **Files:** `ops/levers.py`, `core/dreaming/shadow.py`, `tests/unit/test_levers.py`,
  `tests/unit/test_shadow_runner.py`.
- **Acceptance test:** `uv run pytest tests/unit/test_levers.py tests/unit/test_shadow_runner.py -q`
  green, PLUS a new assertion proving the fingerprint MOVES with σ: two `Config`s differing only in
  `dream_rnd.sigma` (e.g. 0.60 vs 0.62) yield DIFFERENT `_config_fingerprint`s; two differing only in an
  UNregistered `[dream_rnd]` knob (e.g. `min_degree`) yield the SAME fingerprint (only registered levers
  count); `get_lever("dream_rnd_sigma").validate(0.80)` raises (out of bounds); `LEVERS` now has 5 entries.
- **Falsifier:** two Configs differing only in `dream_rnd.sigma` collide on `_config_fingerprint` (the
  sweep-breaking bug this plan exists to kill); OR the fingerprint is computed from a hardcoded knob list
  rather than `ops.levers.LEVERS` (so bp-049 widening the registry silently fails to move the key); OR the
  new lever's bounds admit a value outside `[0.55, 0.75]`.
- **Invariant(s):** the registry stays the whole self-modifiable surface (a numeric knob only — no path/
  diff/command field, `ops/levers.py:7-13`); `config_fingerprint` is a hash of live registered-lever
  VALUES (not policy — §4); the shadow runner still reads ONLY a `MirrorView` and writes ONLY the ledger +
  eval store (unchanged — this plan touches only the fingerprint helper, not the run's IO).
- **Touches stored data?** No new store. It CHANGES the VALUE of `config_fingerprint` written into
  existing eval-store rows going forward — a keyed identity shift, not a migration (old rows keep their old
  key; new runs get the wider key). Note this in the journal: pre-bp-046 eval rows are keyed by the
  narrow fingerprint and are not directly comparable to post-bp-046 rows for the same σ — expected, and
  exactly why the sweep is a fresh keyed series.
- **Parallelizable?** No (single item). **Depends on:** none.

## 8. Math carried explicitly

N/A — no mathematical instrument. `_config_fingerprint` is a canonicalization hash (a set of live
scalars → sorted-key JSON → sha256); its correctness is the Item-12 "fingerprint moves with σ, and only
with registered levers" test, not a field-guide entry.

## 9. Non-goals

- No sweep, grid, curve, admissibility, selection, or `ProposedChange` emission — that is bp-049.
- No registration of the OTHER `[dream_rnd]` knobs (agreement_jaccard, the counts, the persistences) —
  §11 parked; register on owner blessing when a sweep needs them, not on a guess.
- No `auto` autonomy, no `SAFE_LEVERS` change — E3b. A new lever defaults to `propose` (bp-047's manifest).
- No change to `defaults.toml`, the loader, the §14 gate, the ledger, or the eval-store schema.
- No folding bp-047's policy `resolved_fingerprint()` into `config_fingerprint` (bp-049's call, parked there).

## 10. Stop-and-raise conditions

- If widening `_config_fingerprint` to derive from `ops.levers.LEVERS` reveals a lever whose
  `section`/`key` does not resolve on `Config` (an `AttributeError` path) — STOP and file a `codebase`
  finding; the registry and the config schema must agree, and a silent skip would reintroduce the
  collision bug.
- If registering `dream_rnd_sigma` alongside `dream_similarity_threshold` makes the manifest (bp-047)
  ambiguous about which σ a `tune.py show` displays — STOP and file a `spec-fidelity` finding (the two σ
  levers must render distinctly). (Expected to be fine — distinct names + descriptions — but verify.)
- Any blessing (`proposed→ready`, `draft→ratified`) the builder would have to perform: it must not.

## 11. Parked decisions

| Decision | Default recorded | Rejected alternatives (why) | Re-entry condition |
|---|---|---|---|
| register the broader `[dream_rnd]` knobs (agreement_jaccard, bridge_clustering_max, counts, persistences) | register `dream_rnd_sigma` ONLY | register all now (a guess on bounds no sweep needs yet; violates "reviewable diff, never a guess") | a sweep spec (bp-049+) declares one of them → add it then, its own reviewable diff |
| `dream_rnd_sigma` bound | `[0.55, 0.75]` (matches the dreaming σ + bp-040's sweep) | a wider band (unwarranted; 0.62 default sits mid-range) | a sweep's curve argues the optimum sits at an edge |
| fold bp-047 policy fingerprint into config_fingerprint | not here (live values only) | fold now (couples this small diff to the manifest; bp-049 decides identity composition) | bp-049 §6 |

## 12. Dependency & ordering summary

- **Items:** 12 only. Blast-radius: it changes a keyed identity (`config_fingerprint`) — the highest-blast
  part of E3a-1 — but in isolation, with the retrofit proving the move; correctly BEFORE the engine that
  relies on it.
- **Cross-plan:** `depends_on: []`. **bp-049 (the sweep engine) `depends_on: [bp-046]`** — it needs the
  registered `dream_rnd_sigma` to sweep and the widened fingerprint for distinct cell keys; NOT
  parallelizable with this plan. Feeds nothing else. Warranted by finding-0087.
