# BP-009 — Build journal

Alive while the plan is `in-progress`; sealed by `/triage` on completion.
Fresh-agent test (§9): a session given only `plan.md` + this journal + the
write-scope files must continue without re-asking anything already answered.

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

## Markers
