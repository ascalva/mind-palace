# BP-009 — Build journal

Alive while the plan is `in-progress`; sealed by `/triage` on completion.
Fresh-agent test (§9): a session given only `plan.md` + this journal + the
write-scope files must continue without re-asking anything already answered.

---

## Seal — 2026-07-11 — /triage — bp-009 `complete`, journal sealed

**Seal.** Plan flipped `in-progress → complete`; merged to main (5 files, +625/−1; overlay
measurement discarded as designed). Spike verdict **KEEP** — falsifier untripped at 0 warranted
ignores / 0 casts on the 13-file real-seam conversion; one genuine catch demonstrated
(never-projected rows into clustering). finding-0028 (KEEP + riders) routed; its Any-laundering
rider relayed live to bp-007's builder for the floor decision. MIRROR_READABLE and all runtime
checks verified untouched at scrutiny. No narrative entries after this line.

---


## 2026-07-11 — Session start: plan flipped in-progress; seam surveyed; Item 10 next

**Status:** plan `ready → in-progress` (legal builder transition). Items 10, 11 both open.
Branch `worktree-agent-a5274515587080fd7`, based on `bfa19e1` (bp-006 sealed; core strict-green).

**Context read (plan §2 manifest, all):** plan.md; note §2.4 + B-3 + Open questions;
`core/provenance.py` (whole); `core/mirror.py`; `core/stores/derived.py`; bp-006 journal
(conventions: TypedDict for row shapes; T3 resolution order structural > narrowing > cast >
warranted ignore; `uv run --extra dev` for everything).

**Seam survey (Item 11 groundwork, done before Item 10 so the tag design fits the seam):**

- The plan's *recommended* seam — "`MirrorView.project` → Librarian read path" — **does not
  exist as described**. Verified by grep + reading `core/librarian/librarian.py`: the
  Librarian reads via `semantic_search(..., provenances=MIRROR_READABLE)` (a runtime-value
  filter, provenance-*parametric* — `answer()` accepts any provenance set), and never touches
  `MirrorView`. A binary static tag cannot honestly annotate a return type that is
  authored-or-not depending on a runtime argument. Spec-fidelity wrinkle, builder-resolvable:
  the plan says "recommend", not "must"; I take the closest REAL MirrorView seam instead.
- The real `MirrorView.project` call sites (grep, whole repo): `core/dreaming/dreamer.py:110`
  (`clusters()` — the live v1 dream path), `dreamer.py:186` (`dream_v2`),
  `core/curator/curator.py:93,132`.
- **Chosen seam: `MirrorView.rows()` → Dreamer v1 read path** — `Dreamer.clusters()` →
  `note_snippets(rows)` / `note_centroids(rows)` (`core/dreaming/cluster.py`) →
  `NoteVector` → `cluster_notes`. This is the introspective read the firewall exists for.
- **The gap the tag would actually close (the accidental-violation class to demonstrate):**
  today the runtime firewall guards only *MirrorView construction*. A consumer that bypasses
  the view — `note_centroids(store.all_rows())`, i.e. clustering OBSERVED/CURATED exhaust —
  is caught by **nothing** (no runtime check in `cluster.py`, no static check). A value-level
  `Authored[Row]` tag makes that a mypy error at authorship time. This *extends* MirrorView's
  proof past the `.rows()` boundary; it does not duplicate the view (the view stays the sole
  minting authority) and touches neither `MIRROR_READABLE` nor any runtime check (plan §10).

**Write-scope reconciliation (recorded before touching anything):** Item 11's "Files: the
sampled seam" conflicts with the frontmatter `write_scope` (no `core/mirror.py`,
`core/dreaming/**`). The frontmatter is the enforced contract and §5 prose confirms it
("the spike measures churn on a SAMPLE, it does not convert the codebase"). Resolution:
the churn measurement runs on a **scratch overlay** — verbatim copies of the seam files
outside the repo, tags applied there, mypy (strict, core flags) run over the overlay with
MYPYPATH at the repo root — and the measurement table + diff summary land HERE in the
journal; no seam file is edited in-repo. A denial is a signal to narrow, not route around.

**Item 10 design decided (recorded before writing code):**
- `Authored[T]` / `Derived[T]` as frozen generic dataclasses (nominal, `@final` so even
  deliberate subclass-laundering is a type error), field `value: T`. Binary grain per plan
  §11; values-only depth (`list[Authored[Row]]` = a container OF tagged values, which is the
  values-only choice; `Authored[list[Row]]` is the rejected container tagging).
- Tag SEMANTICS (journal-worthy subtlety): `Authored[T]` means "this value was obtained
  exclusively from mirror-readable sources" — an information-flow taint label, not "the owner
  typed this exact value". Meet = Derived (plan §8): any function mixing in Derived input
  must return Derived. The only up-move is `promote`, which demands the capability.
- `promote(x: Derived[T], cap: OwnerVerdict) -> Authored[T]` — signature verbatim from plan
  §6; body raises `NotImplementedError` citing I1 verdict-gating (unbuilt; recursive-strata
  parked). No `cast` needed at the definition site (body never produces the return value) —
  Item 10's immediate falsifier is NOT tripped by construction.
- `OwnerVerdict`: minimal NOMINAL placeholder class (`@final`, no members), NOT a Protocol —
  an empty Protocol is structurally satisfied by every object, which would make the
  capability forgeable at the type level (`promote(d, object())` would type-check) and
  vacate the constraint. Constructible-but-inert at runtime (it gates nothing; `promote`
  raises regardless), so no policy is invented. **Open design questions recorded, NOT
  resolved here (I1 verdict taxonomy is unratified):** (a) should `OwnerVerdict` unify with
  the existing runtime verdict machinery (`core/verdict/`, `core/stores/verdicts.py`) —
  i.e. is the capability a row from the verdicts store, a signed token, or a fresh type?
  (b) does a verdict carry the TARGET class (AUTHORED_SOLO vs AUTHORED_DIALOGUE) or is
  promotion always to one class? (c) scope: per-value, per-artifact, or per-derivation-run?
  These go to /triage with the finding; the placeholder deliberately answers none of them.
- Tests: `tests/unit/test_provenance_tags.py` (NEW file — bp-007 sibling edits other test
  files; I create new only). Type-level via subprocess mypy on fixture snippets written to
  tmp_path, run with cwd=tmp (so the repo's `[tool.mypy] files=[...]` config is NOT picked
  up) and MYPYPATH=repo root (so `core.provenance` resolves). Plus cheap runtime assertions:
  enum members + MIRROR_READABLE unchanged, promote raises, wrappers frozen.

**Next action:** commit this checkpoint; implement Item 10; `uv run --extra dev mypy` (0 core
errors) + `uv run --extra dev pytest -q` + `uv run ruff check .` before commit.

---

## 2026-07-11 — Item 10 COMPLETE (commit `0be851e`-ish, see git log): tags + stub landed, acceptance green

**Status:** Item 10 done. Item 11 (churn overlay) next.

**Landed:** `core/provenance.py` — `Authored[T]` / `Derived[T]` (`@final` frozen generic
dataclasses; `@final` closes subclass-laundering), nominal `@final class OwnerVerdict`
placeholder, `def promote(x: Derived[T], cap: OwnerVerdict) -> Authored[T]` (signature
verbatim per plan §6) raising `NotImplementedError` citing I1 verdict-gating.
`tests/unit/test_provenance_tags.py` (NEW file) — subprocess-mypy fixtures with inline
`# E: <code>` markers asserted line-exactly, run with `--config-file <os.devnull>` +
cwd=tmp (repo/user configs ignored) + MYPYPATH=repo root.

**Acceptance outputs (verbatim):**
- `uv run --extra dev pytest tests/unit/test_provenance_tags.py -q` → `7 passed in 1.76s`
- fixture `promote(d)` (no capability) → mypy `[call-arg]` error (FAILS mypy) ✓
- fixture `promote(d, cap)` with `cap: OwnerVerdict` → mypy exit 0, zero error lines ✓
- `uv run --extra dev mypy | grep -c '^core/'` → `0` (core strict-green preserved)
- `uv run --extra dev mypy | grep -E "test_provenance_tags|core/provenance"` → empty
  (repo-wide count 296-in-83-files is pre-existing Tier-2 report-only debt, none mine)
- `uv run ruff check .` → `All checks passed!`
- Full suite: `765 passed, 8 skipped`, 1 failed = `tests/e2e/test_scheduler_live.py::
  test_supervisor_dispatches_a_real_job` — TIMING FLAKE, passes in isolation (`1 passed in
  82.35s`), untouched by this change (provenance additions are inert at runtime).

**Item-10 falsifier check:** NOT tripped — no `cast` anywhere at the definition site (the
stub body raises, so the return value is never manufactured). One warranted ignore exists in
the runtime TESTS only (`# type: ignore[misc]  # warrant: the frozen-ness IS the assertion`
— assigning to a frozen field is the thing under test), zero in `core/provenance.py`.

**mypy behavior note (fixture calibration):** for `a2: Authored[str] = promote(d, cap)` with
`d: Derived[int]`, mypy infers T=str from the return context and reports the ARGUMENT
mismatch `[arg-type]` (Derived[int] vs Derived[str]), not `[assignment]`. Same proof
(payload type threads through T), different code than first guessed.

**Item 11 groundwork (consumer map, measured by grep + reading — the honest blast radius of
Encoding A, `MirrorView.rows() -> list[Authored[Row]]`):** direct `.rows()`-output consumers
in core: `mirror.py` (mint), `dreaming/cluster.py` (note_snippets/note_centroids sigs +
internal field access), `dreaming/dreamer.py` (clusters() passes rows through UNCHANGED —
both consumers retyped; dream_v2:189-191 touches fields → unwrap), `dreaming/graph.py:36`
(pass-through, no change), `dreaming/interpreters.py:249` (pass-through, no change),
`dreaming/adjudicator.py:144-147` (field access → unwrap), `complex/build.py:123-137`
(field access + `_created_epoch` sig), `curator/curator.py:93,132-134` (pass-through only,
no change), `effect_proposal.py:130-131` (field access → unwrap). Plus Tier-2 test churn
(tests feeding bare dict rows), counted separately.

**Method decided for the overlay:** local `git clone` of this worktree into the scratchpad;
Encoding A applied IN PLACE there (real import graph — no module renames polluting the
diff); checked with `uv run --project <this worktree> --extra dev mypy` from the clone cwd
(same pyproject config, real venv); churn read off `git diff` in the clone. The overlay is
DISCARDED after measurement — nothing lands outside write scope. Runtime tests of the
overlay: attempted via the clone's own uv env if cheap; else recorded as not-run (the spike
is type-level; behavior-preservation of `.value` unwraps is visually verified, and the
overlay does not ship).

**Next action:** build the overlay, drive it to core-green mypy, produce the churn table +
the demonstrated catch, file finding-0028 (next free id, checked `ls docs/findings/`) with
the keep-or-park verdict.

---

## 2026-07-11 — Item 11 COMPLETE: churn measured on the real seam — ZERO warranted ignores; verdict KEEP (finding-0028)

**Status:** Items 10 and 11 both done. Finding-0028 filed. Plan-complete pending orchestrator
scrutiny + /triage (builder does NOT flip to complete).

**Method (as decided in the Item-10 entry, executed verbatim):** local `git clone` of this
worktree at `951d30e` into the scratchpad (`bp009-overlay`); Encoding A — `MirrorView.rows()
-> list[Authored[dict[str, Any]]]`, the view stays the sole read-path mint, `__post_init__`
runtime re-check and `MIRROR_READABLE` byte-identical — applied in place there; checked with
`uv run --project <worktree> --extra dev mypy` (same pyproject config) and the clone's own
pytest env. Overlay discarded after measurement; NOTHING landed outside write scope.

**Headline numbers:**

- **Warranted ignores required: 0. Casts required: 0.** (grep over the full overlay diff:
  `git diff | grep -cE '^\+.*(type: ignore|cast\()'` → `0`)
- Total churn to convert the ENTIRE MirrorView consumer set (not just one path):
  **13 files, +37/−24 lines** (249-line unified diff, saved during the session as
  `overlay-full.diff` in the scratchpad; reproducible from the table below).
- mypy end state: **core 0 errors; repo-wide 296 = exact baseline parity (0 new, 0
  resolved)**. ruff: `All checks passed!`. Runtime: full overlay suite minus e2e
  **750 passed, 4 skipped** (targeted seam set passed earlier: `92 passed in 14.77s`).

**Churn table (sites touched, by file):**

| file | churn | nature |
|---|---|---|
| `core/mirror.py` | +1 import; `rows()` sig + wrap (1 method) | the mint. Runtime check UNTOUCHED |
| `core/dreaming/cluster.py` | +1 import; 2 signatures; 2 unwrap lines | the introspective entry (`note_snippets`, `note_centroids`) |
| `core/dreaming/dreamer.py` | 1 unwrap (dream_v2 title loop) | field access; `clusters()` needed NO change |
| `core/dreaming/adjudicator.py` | 2 lines → `.value.get` | field access |
| `core/complex/build.py` | +1 import; 1 helper sig (`_created_epoch`); 1 unwrap; 1 dict-comp | field access |
| `core/effect_proposal.py` | 1 line → `.value.get` | field access (model_tailor context) |
| `core/dreaming/graph.py` | **0** | pass-through (`note_centroids(view.rows())`) type-checks unchanged |
| `core/dreaming/interpreters.py` | **0** | pass-through |
| `core/curator/curator.py` | **0** | pass-through (both call sites) |
| tests ×7 files | 5 unwraps (`r.value["…"]`); 3 explicit mints (`Authored(r)`) | see laundering note below |

**The demonstrated catches (acceptance: "at least one accidental-violation the checker now
catches"):**

1. **Real site, caught statically:** `tests/unit/test_complex.py:114` —
   `note_centroids(rows)` with hand-built rows that never transited a MirrorView. mypy:
   `Argument 1 to "note_centroids" has incompatible type "list[dict[str, Any]]"; expected
   "list[Authored[dict[str, Any]]]" [arg-type]`. This is exactly the MirrorView-bypass
   class: today NOTHING catches a consumer clustering un-projected rows (the runtime
   firewall guards only view construction). Fix forced an EXPLICIT, greppable mint.
2. **Pinned permanently in-repo:** `tests/unit/test_provenance_tags.py::
   test_mirror_bypass_is_a_type_error` — raw `store.all_rows()`-shaped rows and
   `Derived[Row]` rows both rejected `[arg-type]` at an `Authored`-typed consumer;
   tagged rows accepted.

**Discovery — Any-laundering bounds the shadow's reach (the honest limit):** two test files
fed bare rows into the retyped entry and mypy saw NOTHING; both surfaced only at runtime
(`AttributeError: 'dict' object has no attribute 'value'`):
- `tests/unit/test_cluster.py` — untyped local fixture `def _row(...)` returns `Any` →
  every argument laundered (7 call sites, one-line fix at the fixture).
- `tests/metamorphic/test_order_independence.py` — `from fixtures.corpus import
  vector_rows` is unresolvable to mypy (pre-existing baseline error) → `Any` → laundered.
This is §2.1's gradual-typing boundary made concrete: in strict Tier-1 (core) the shadow is
tight — in Tier-2 it is only as strong as the flag floor and the fixture typing. Recorded in
finding-0028; feeds the note's open "Tier-2 flag floor" question.

**Honest caveats (in the finding too):**
- The mint is NOT sealed: `Authored(...)` is publicly constructible, so the tag converts a
  silent bypass into an explicit, reviewable assertion — it does not PROVE view-transit.
  Sole-mint discipline (B-7-adjacent grep gate or module-private mint) is a design question.
- "Zero runtime cost" holds for the CHECKING, not the encoding: `rows()` now allocates N
  small frozen wrappers per call (a generic `NewType` does not exist in Python's grammar, so
  a fully erased generic tag is not expressible). Negligible on this path, but nonzero.
- The seam is non-severable: retyping `rows()` propagates to ALL consumers in one move —
  "one seam" honestly = the full consumer set. The propagation was cheap (3 files needed
  zero changes) but a partial adoption is not an option under Encoding A.

**Falsifier check (the note's, verbatim: "if tagging requires warranted ignores at more than
a handful of sites, the static-shadow claim is weakened; park the spike with that evidence
attached rather than forcing the encoding"):** measured ignores = **0** across the full
consumer set, tests included. Falsifier NOT tripped — by a wide margin. **Verdict: KEEP**
(finding-0028): the static-shadow claim survives its own falsifier on real call sites.
Landing the conversion needs a follow-up plan whose write_scope covers the 6 core + 7 test
files (out of bp-009's scope by design).

**Acceptance outputs (verbatim):**
- overlay mypy: `core: 0 | total: 296 | new: 0 | resolved: 0`
- overlay ruff: `All checks passed!`
- overlay pytest (full minus e2e): `750 passed, 4 skipped in 8.77s`
- overlay diff: `13 files changed, 37 insertions(+), 24 deletions(-)`; ignores/casts added: `0`

---

## 2026-07-11 — HANDBACK: both items done, verdict KEEP, awaiting /triage

**Per-item state:** Item 10 **done** (tags + `promote` stub + type-level tests landed;
falsifier not tripped — zero casts at the definition site). Item 11 **done** (churn measured
on the full MirrorView consumer set via discarded overlay; **0 warranted ignores / 0 casts**;
note-falsifier NOT tripped; catch demonstrated on a real site and pinned in-repo;
finding-0028 filed, verdict **KEEP**, routed orchestrator).

**Final worktree state (verbatim):** `core errors: 0` (mypy) · ruff `All checks passed!` ·
`tests/unit/test_provenance_tags.py` → `7 passed` · working tree clean. Full suite last run
at Item-10 close: 765 passed / 8 skipped / 1 e2e timing flake (passes in isolation).

**Commits on `worktree-agent-a5274515587080fd7`:** `1269c7f` (flip + survey), `5a6e9c5`
(Item 10: tags + stub + tests), `951d30e` (journal), `<this + prev>` (Item 11 measurement +
finding-0028 + handback). Nothing merged to main; plan NOT flipped to complete (owner/
orchestrator act).

**For /triage:** finding-0028 (keep-or-park = direction; OwnerVerdict design questions
inside). Spec wrinkles resolved builder-side and recorded above: the plan's recommended
"Librarian read path" seam does not transit MirrorView (real seam substituted); Item 11's
"Files: the sampled seam" vs write_scope reconciled via the discarded overlay.

---

## Markers
