---
type: build-plan
id: bp-004
status: in-progress
design_ref:
  - docs/design-notes/agent-workflow.md
contract: builder
write_scope:
  - ".claude/hooks/**"
  - ".claude/commands/**"
  - "docs/templates/build-plan.md"
  - "docs/build-plans/bp-004/**"
  - "docs/findings/**"
session_budget: 1
depends_on: []
parallelizable_with: []
created: 2026-07-06
updated: 2026-07-06
links:
  - docs/design-notes/agent-workflow.md # §6 status-normalization (line 152), §3 schema (line 78), §16 A5 (line 279) / A6 (line 280)
  - docs/findings/finding-0006.md # A5 warrant (comment-on-status defeats every blessing gate)
  - docs/findings/finding-0008.md # A6 warrant (§3 schema vs A4 template + command-file drift)
re_entry: null # only if parked — the greppable "parked ⇒ re-entry" gate (§3, Principle 1); §11 is its human-readable expansion (A6)
supersedes: null
superseded_by: null
warrant: null
---

# Build Plan — Land the A5 (finding-0006) and A6 (finding-0008) mechanical fixes

## 0. Mode & provenance

Investigation and planning produced this plan (a grounded graduation pass, A4):
the code was read and every claim below carries a `path:line` citation; the plan
was written, not implemented. Implementation proceeds item-by-item on owner
approval. Authority-to-act (the owner's instruction to land A5/A6's mechanical
consequences) is **separate** from the readiness blessing (owner-only
`proposed → ready`, §10). **No agent flips readiness** — this plan is minted at
`status: proposed` and held there; the owner's hand edit is the only path to
`ready`. `gate-guard` denies the Edit path pre-hoc and the Stop-gate (c) audit
blocks the Bash path (§6).

A5 and A6 are **already ratified** into the design note (§16, lines 279–280;
§6 line 152; §3 line 78). This plan lands only their _mechanical consequence_ —
the `_lib.py` normalization, the template's clean status line + restored
`re_entry` key, and the command-file reconciliation — exactly as bp-003 landed
A4's. The findings promote to `promoted` as the terminal step once the fixes land
and the harness is green.

## 1. Objective

Close finding-0006's blessing-gate bypass in code and template and finding-0008's
command-file schema drift, so a comment-bearing `ready`/`ratified` status is
caught by all three blessing detectors and `/build` reads the A4 template's body
sections correctly — with a harness proving it and all prior criteria green.

## 2. Context manifest

Read in order, whole files before citing:

1. `docs/design-notes/agent-workflow.md` — §6 status-normalization clarification
   (line 152, the A5 enforcement contract), §3 build-plan front-matter schema
   (line 78, the A6 field placement: `re_entry` a front-matter key;
   `objective`/`context_manifest`/`non_goals`/`stop_conditions` body sections
   §1/§2/§9/§10), §16 A5 (line 279) and A6 (line 280). The ratified contract this
   plan makes true.
2. `docs/findings/finding-0006.md` — the A5 warrant: a trailing ` #` comment on a
   `status:` line parses to a value `!= "ready"`, escaping all three detectors.
   Carries the empirical table and the recommended fix (option (a)+(b)).
3. `docs/findings/finding-0008.md` — the A6 warrant: §3 prose vs the A4 template,
   and the command-file drift (`build.md:26-27`, `graduate.md:17`, `scribe.md:16`)
   that would misdirect a literal `/build` on a new-template plan.
4. `.claude/hooks/_lib.py` — the parser (`_scalar` L171–175, `parse_front_matter`
   L136–168), the two status extractors (`status_of` L186–189, `_status_in_text`
   L253–259), and the three blessing detectors (`cmd_gate_check` L295–313 +
   `cmd_gate_check_hook` L322–343; `_blessing_in_diff` L379–399; `_untracked_blessing`
   L417–434). The single file the A5 fix touches.
5. `.claude/hooks/gate-guard.sh` and `.claude/hooks/journal-gate.sh` — the dual-mode
   (hook stdin / `--standalone`) wrappers the harness drives.
6. `docs/templates/build-plan.md` — line 4 (the comment-bearing status line to
   clean, A5) and the front-matter block (lines 1–19; the missing `re_entry` key to
   restore, A6). §1/§2/§9/§10/§11 confirm the four fields already live in the body.
7. `.claude/commands/{build.md,graduate.md,scribe.md}` — the three files whose
   front-matter-key references to the moved fields the A6 fix reconciles.
8. `docs/build-plans/bp-002/acceptance/run.sh` — the proven harness pattern
   (isolated temp git repos, real hooks driven by reference; prior harness chained
   in). bp-004's harness extends this. (`docs/build-plans/bp-001/acceptance/run.sh`
   and `bp-000/acceptance/run.sh` are transitively re-run through it.)
9. `docs/build-plans/bp-003/{plan.md,journal.md}` — the exemplar for a plan minted
   at `proposed` and held there under direct owner instruction, with the journal
   carrying completion evidence and finding promotion recorded.

## 3. Investigation & grounding <!-- Part A -->

This plan touches existing code (`_lib.py`, the template, three command files).
Every claim below is grounded.

- **Q1 — Where does a comment-bearing status escape, and which extractors feed
  each detector?** The parser never strips a trailing YAML comment: `_scalar`
  (`_lib.py:171-175`) strips whitespace and matched quotes only; `parse_front_matter`
  (`:136-168`) applies `_scalar` uniformly and adds nothing. The two status-specific
  extractors return the un-normalized value: `status_of` = `fm.get("status")`
  verbatim (`:186-189`); `_status_in_text` = `_scalar(s.split(":",1)[1])`
  (`:253-259`). The three detectors then compare by **exact equality**:
  - **gate-guard** `cmd_gate_check` (`:304` `new_status == "ratified"`, `:308`
    `new_status == "ready"`), where `new_status` arrives from `_status_in_text`
    via `cmd_gate_check_hook` (`:340`) and `cur = status_of(fp)` (`:300`);
  - **Stop-gate tracked** `_blessing_in_diff` (`:395` `val == "ratified"`, `:397`
    `val == "ready"`), where `val = _scalar(body.split(":",1)[1])` (`:394`);
  - **Stop-gate untracked** `_untracked_blessing` (`:430`/`:432`), reading
    `status_of(f)`.
    So `status: ready   # x` → value `ready   # x` `!= "ready"` on every path. Matches
    finding-0006 exactly (`finding-0006.md:31-38`).
- **Q2 — Does normalizing only `status_of` and `_status_in_text` fix all three
  detectors?** **No — a third extraction site exists.** gate-guard is fixed by both
  extractors (`new_status`←`_status_in_text`, `cur`←`status_of`); `_untracked_blessing`
  is fixed by `status_of`. But `_blessing_in_diff` extracts via `_scalar` **directly**
  at `_lib.py:394` — it routes through _neither_ named extractor. To make the tracked
  Stop-gate path fire, the normalization must also wrap that call site. This plan
  therefore applies a single `_normalize_status` helper at **all three** status-value
  extraction points (`status_of`, `_status_in_text`, and `_blessing_in_diff:394`),
  which is the concrete realization of "the status-specific extractors" that satisfies
  the §6/A5 requirement that all three detectors fire (`agent-workflow.md:152`;
  §16 A5 `:279`).
- **Q3 — Will normalization ever fabricate a blessing (over-fire)?** No. The cut is
  at the first `" #"` (space-hash — YAML comment semantics). `ready#x` (no space) has
  no `" #"`, so `find(" #") == -1`, no cut, value stays `ready#x` `!= "ready"` — still
  a non-blessing. The failure the fix removes is one-directional (false-negative in
  the blessing direction only); normalization only ever _refuses to recognize a
  malformed blessing_, never manufactures one (`agent-workflow.md:152`;
  `finding-0006.md:59-62`).
- **Q4 — Is the scope strictly the status path?** Yes. `_scalar` and
  `parse_front_matter` are **not** modified, so a `#` in any non-status field
  survives (a `design_ref`, a `links` entry, etc. may legitimately carry one). Only
  the three status extraction sites gain `_normalize_status`. Verified by design: the
  helper is applied at named call sites, not folded into `_scalar`.
- **Q5 — Does the template model the antipattern, and is `re_entry` absent from its
  front-matter?** Yes to both. `docs/templates/build-plan.md:4` is
  `status: proposed          # proposed → ready (owner) → …` — the exact
  comment-on-status-line pattern §6/A5 forbids (`agent-workflow.md:152`). And its
  front-matter block (lines 1–19) carries **no** `re_entry` key (grep confirms none),
  the A6 gap. The four other fields are already body sections: §1 Objective (`:38`),
  §2 Context manifest (`:43`), §9 Non-goals (`:112`), §10 Stop-and-raise (`:117`),
  with §11 Parked decisions (`:124`) the human-readable re-entry home.
- **Q6 — Do the command files misdescribe the moved fields?** Yes. `build.md:26-27`
  instructs "Read the `context_manifest` in order. Then execute against `acceptance`,
  honoring `non_goals` and `stop_conditions`" — front-matter-key phrasing for four
  fields that on the A4 template are §2/§7/§9/§10 body sections. `graduate.md:17`
  lists "ordered `context_manifest`, runnable `acceptance`". `scribe.md:16` lists
  "`context_manifest`: the debt delta". Matches finding-0008 (`finding-0008.md:47-58`).
  `re_entry` is _not_ referenced by any command file, so nothing there needs the
  key-vs-body treatment; it simply remains a front-matter key per A6.
- **Q7 — Do the prior harnesses stay green under the A5 change?** Yes — the code
  does settle this. Every prior test (bp-000/001/002) drives clean status lines
  (`status: ready`, `status: proposed`, `status: ratified`; e.g.
  `bp-002/acceptance/run.sh:79,97,115,117,135,137`). `_normalize_status` on a
  comment-free value is a no-op (`find(" #") == -1`, `rstrip()` of an already-trimmed
  scalar), so the A5 fix cannot change any prior verdict. bp-004's harness re-runs
  bp-002's by reference to prove this, exactly as bp-002 wrapped bp-001 wrapped
  bp-000 (`bp-002/acceptance/run.sh:52-67`).

**Additional risks or questions surfaced during reading:**

- `cmd_brief` (`_lib.py:522-572`) reads status via `read_front_matter(pm).get("status")`
  **directly** (`:533`), _not_ through `status_of`, so the session brief still
  renders a comment-bearing status verbatim — this was finding-0006's original
  surfacing symptom (`finding-0006.md:22-26`). It is **cosmetic, not an enforcement
  path**, and the template fix (Item 2) removes the only source of comment-bearing
  status lines for newly minted plans; every existing plan already has a clean status
  line (`finding-0006.md:80-81`). Left **out of scope** (see §9) to honor "scope
  strictly to the status path" — normalizing the brief is a legibility nicety with no
  bright-line stake, and folding it in would widen the diff past the ratified contract.
- `gate-guard.sh --standalone` passes the intended status **raw** to `cmd_gate_check`
  (`gate-guard.sh:24`), which does not normalize its `new_status` parameter (the fix
  lives in the extractors that feed the _hook_ path). The real PreToolUse hook always
  uses stdin (hook mode), which routes through `_status_in_text`. The harness must
  therefore exercise gate-guard in **hook mode (stdin JSON)**, not standalone, to test
  the real enforcement path — pinned in §6 and Item 4.

## 4. Reconciliation <!-- Part B -->

This plan **corrects committed code and docs**. Each correction is announced by its
already-ratified banner (the finding + the §16 amendment) and carried by an item
below — never a silent replacement (A4 discipline).

- `.claude/hooks/_lib.py` (three detectors compare status by exact equality without
  normalization, `:304/:308/:395/:397/:430/:432`) → **banner: correction**, warrant
  finding-0006 / §16 A5 (`agent-workflow.md:279`, §6 `:152`). Carried by **Item 1**
  (add `_normalize_status`; apply at `status_of`, `_status_in_text`, `_blessing_in_diff`).
- `docs/templates/build-plan.md:4` (models the comment-on-status-line antipattern) →
  **banner: correction**, warrant finding-0006 / A5. Carried by **Item 2** (remove the
  inline comment; the minted status line becomes clean).
- `docs/templates/build-plan.md` front-matter (missing the `re_entry` key) →
  **cross-ref: extension**, warrant finding-0008 / §16 A6 (`agent-workflow.md:280`,
  §3 `:78`). Carried by **Item 2** (restore `re_entry` as a front-matter key; §11
  remains its human-readable expansion, cross-referenced by an inline comment).
- `.claude/commands/{build.md:26-27, graduate.md:17, scribe.md:16}` (describe
  `context_manifest`/`acceptance`/`non_goals`/`stop_conditions` as front-matter keys)
  → **banner: correction**, warrant finding-0008 / A6. Carried by **Item 3** (reframe
  to the §2/§7/§9/§10 body sections; `re_entry` stays a front-matter key).
- `docs/findings/finding-0006.md` (`status: open`), `docs/findings/finding-0008.md`
  (`status: routed`) → **not a correction — a lifecycle transition.** The design change
  they warranted is ratified (A5/A6); landing the mechanical consequence promotes them.
  Carried by **Item 5** (`→ promoted`, resolution links A5/A6 + bp-004).

The design note itself is **not** touched: A5/A6 are already ratified into §3/§6/§16 by
the owner's hand (`agent-workflow.md:78,152,279,280`). This plan lands only the
mechanical consequence — never a design-note edit, never a blessing flip.

## 5. Write scope

In scope (mirrors the front-matter `write_scope`):

- `.claude/hooks/**` — the `_lib.py` A5 normalization (Item 1) and the new
  `docs/build-plans/bp-004/acceptance/run.sh` harness lives under bp-004, but the
  hooks it copies/drives are here; only `_lib.py` is edited.
- `.claude/commands/**` — the three command-file A6 reconciliations (Item 3).
- `docs/templates/build-plan.md` — the A5 status-line clean + A6 `re_entry` restore
  (Item 2).
- `docs/build-plans/bp-004/**` — this plan, its journal, its acceptance harness.
- `docs/findings/**` — promote finding-0006 and finding-0008 (Item 5).

Deliberately **out of scope** (must not be touched):

- `docs/design-notes/**` — foundation denylist; A5/A6 are already ratified. Any gap
  found exits as a _new_ finding, never a design edit.
- `CONSTITUTION.md`, `eval/golden/**` — foundation denylist.
- `docs/PROGRESS.md` — the orchestrator's single-writer completion checkpoint, written
  post-build outside this plan's scope (as with bp-000..bp-003).
- `_lib.py cmd_brief`'s status read (`:533`) — cosmetic, not a bright line (see §3, §9).
- Any `status: ratified` / `proposed → ready` flip anywhere — a blessing (§10).

## 6. Interfaces pinned inline

**A5 — the normalizer (new helper, exact form to add to `_lib.py`).**

```python
def _normalize_status(v):
    """Strip a trailing YAML comment from a *status* value before the blessing
    detectors compare it by exact equality (A5, warrant finding-0006; §6). Cut at
    the first ' #' (space-hash — YAML comment semantics), then rstrip. A '#' with no
    preceding space ('ready#x') is NOT a YAML comment and is left intact, so a
    malformed status can never be normalized *into* a blessing (false-negative-only,
    the safe direction). Scoped to the status extraction path only — `_scalar` stays
    general so a legitimate '#' survives in other fields."""
    if not isinstance(v, str):
        return v
    i = v.find(" #")
    if i != -1:
        v = v[:i]
    return v.rstrip()
```

**A5 — the three application sites (exact current form → change).**

- `status_of` (`_lib.py:186-189`), current last line `return s if isinstance(...)`:
  ```python
  def status_of(path_rel: str):
      fm = read_front_matter(os.path.join(ROOT, path_rel))
      s = fm.get("status")
      if isinstance(s, str) and s:
          s = _normalize_status(s)
      return s if isinstance(s, str) and s else None
  ```
- `_status_in_text` (`_lib.py:253-259`), current `return _scalar(s.split(":", 1)[1])`:
  ```python
          if s.startswith("status:"):
              return _normalize_status(_scalar(s.split(":", 1)[1]))
  ```
- `_blessing_in_diff` (`_lib.py:394`), current `val = _scalar(body.split(":", 1)[1])`:
  ```python
          val = _normalize_status(_scalar(body.split(":", 1)[1]))
  ```

`_scalar` (`:171-175`), `parse_front_matter` (`:136-168`), `cmd_gate_check` (`:295-313`),
`cmd_gate_check_hook` (`:322-343`), `_untracked_blessing` (`:417-434`) are **unchanged**;
the last two inherit normalization through `status_of`/`_status_in_text`.

**A5 — the template status line (`docs/templates/build-plan.md:4`).**

- Before: `status: proposed          # proposed → ready (owner) → in-progress → complete | parked | superseded`
- After: `status: proposed`

**A6 — the restored front-matter key (insert before `supersedes: null`, currently
`docs/templates/build-plan.md:16`).**

```
re_entry: null            # only if parked — the greppable "parked ⇒ re-entry" gate (§3, Principle 1); §11 is its human-readable expansion (A6)
```

(Front-matter comments on _non-status_ lines are permitted — A5 forbids the comment
only on the status line, `agent-workflow.md:152`. `objective`/`context_manifest`/
`non_goals`/`stop_conditions` remain **body** sections §1/§2/§9/§10, not restored.)

**A6 — the three command-file reconciliations (front-matter-key phrasing → body
section refs).**

- `build.md:26-27` before: "Read the `context_manifest` in order. Then execute against
  `acceptance`, honoring `non_goals` and `stop_conditions`." → after: read the **§2
  Context manifest** in order, then execute against each **§7** item's **Acceptance
  test**, honoring the **§9 Non-goals** and **§10 Stop-and-raise conditions** — body
  sections on the A4 template, not front-matter keys (A6). (`re_entry` remains a
  front-matter key.)
- `graduate.md:17` before: "an ordered `context_manifest`, runnable `acceptance`, and
  **interfaces pinned inline**" → after: an ordered **§2 context manifest**, **§7**
  items with runnable per-item **Acceptance test**s, and **interfaces pinned inline**
  (§6) — the body sections the graduate skill already emits.
- `scribe.md:16` before: "- `context_manifest`: the debt delta …" → after: "- **§2
  context manifest**: the debt delta …". (The `contract`/`status`/`session_budget`/
  `write_scope` front-matter keys named at `scribe.md:16-17` are correct and unchanged.)

**Harness invariants (pinned; realized in Item 4).**

- gate-guard is tested in **hook mode (stdin JSON)** — `{"tool_input": {"file_path":
"<plan.md>", "content": "…status: ready   # x…"}}` piped to `gate-guard.sh` — because
  standalone passes status raw (see §3). Expect `DENY` / rc=2.
- The Stop-gate tracked path is tested by an **uncommitted in-place flip on a tracked**
  plan (`git diff HEAD` shows `+status: ready   # x`); the untracked path by an
  **untracked minted** plan at `status: ready   # x` (`_untracked_blessing` reads it via
  `status_of`). Both via `journal-gate.sh --standalone` in an isolated temp repo, the
  bp-002 pattern (`bp-002/acceptance/run.sh:37-50`).
- Each of the three paths runs the comment-bearing `ready` (must block) beside a clean
  `ready` control (must block — proves the path is wired and non-vacuous) and a nospace
  `ready#x` case (must NOT block — proves no over-fire).

## 7. Items

Ordered by blast radius: all are **reversible file writes** (no stored data, no
external effect); within that, the enforcement mechanism first, then the artifacts it
governs, then the harness that proves them, then the terminal finding accounting.

### Item 1 — A5 code fix: normalize status before the exact-equality comparison

- **Objective:** all three blessing detectors fire on a comment-bearing
  `ready`/`ratified` status.
- **Files:** `.claude/hooks/_lib.py` (add `_normalize_status`; apply at `status_of`,
  `_status_in_text`, `_blessing_in_diff:394` — exact forms in §6).
- **Acceptance test:** in isolated temp repos (bp-002 pattern), `status: ready   # x`
  BLOCKS on all three paths — gate-guard hook-mode `DENY`/rc=2; Stop-gate tracked
  (uncommitted in-place flip) BLOCK/rc=2 citing the blessing + file; Stop-gate untracked
  (minted file) BLOCK/rc=2 — each beside a clean `ready` control that also blocks. Run
  from Item 4's harness.
- **Falsifier:** `status: ready#x` (no space) starts BLOCKING on any path (normalization
  fabricated a blessing), **or** a clean `status: proposed` starts blocking, **or** any
  bp-000/001/002 criterion regresses (the change was not a no-op on clean lines). Any of
  these means the fix over-reached its one-directional, status-only contract.
- **Invariant(s) it must not violate:** `_scalar`/`parse_front_matter` unchanged (a `#`
  in a non-status field survives, §3 Q4); normalization is false-negative-only (never
  manufactures a blessing, `agent-workflow.md:152`); the A1/A3 committed-self-clears and
  untracked-inclusive behaviors are preserved.
- **Touches stored data?** No — a hook-logic edit; no mind-palace store, no live behavior.
- **Parallelizable?** No (Item 4's harness verifies it). **Depends on:** none.

### Item 2 — A5 + A6 template fix: clean status line, restore `re_entry` key

- **Objective:** the template no longer models the comment-on-status-line antipattern,
  and carries `re_entry` as a greppable front-matter key.
- **Files:** `docs/templates/build-plan.md` (line 4 → `status: proposed`; insert
  `re_entry: null` before `supersedes:` — exact forms in §6).
- **Acceptance test:** `sed -n '4p'` shows `status: proposed` with **no** `#`;
  `grep -n 're_entry' docs/templates/build-plan.md` finds the front-matter key;
  `objective`/`context_manifest`/`non_goals`/`stop_conditions` are **absent** from the
  front-matter block (still body sections §1/§2/§9/§10, confirmed by `grep`).
- **Falsifier:** minting a fresh plan verbatim from the template reproduces a `#` on the
  status line (A5 hole reopens), **or** `re_entry` lands only in §11 with no front-matter
  key (the "parked ⇒ re-entry" gate is no longer greppable, `agent-workflow.md:78`).
- **Invariant(s) it must not violate:** other front-matter lines' inline comments are
  untouched (A5 scopes the ban to the status line); the four body-section fields are
  **not** promoted back to front-matter (A6 keeps them in the body).
- **Touches stored data?** No — a template doc edit.
- **Parallelizable?** Yes (independent of Item 1). **Depends on:** none.

### Item 3 — A6 command fix: read the moved fields from body sections

- **Objective:** `/build`, `/graduate`, `/scribe` reference the A4 template's §2/§7/§9/§10
  body sections, not front-matter keys, for the four moved fields; `re_entry` stays FM.
- **Files:** `.claude/commands/build.md` (`:26-27`), `.claude/commands/graduate.md`
  (`:17`), `.claude/commands/scribe.md` (`:16`) — exact rewrites in §6.
- **Acceptance test:** a `/build` dry-run on a new-template plan (bp-004 itself) resolves
  `context_manifest` from §2 and `acceptance` from §7 (not front-matter), recorded in the
  journal; and `grep` confirms all three files reference the body sections and no longer
  instruct reading these four as front-matter keys.
- **Falsifier:** a literal `/build` on a new-template plan looks for a front-matter
  `context_manifest`/`acceptance` key and, finding none, stalls or misreads — i.e. the
  drift finding-0008 named still bites.
- **Invariant(s) it must not violate:** `re_entry` continues to be described (where
  relevant) as a front-matter key (A6); the correct front-matter keys named in
  `scribe.md:16-17` (`contract`/`status`/`session_budget`/`write_scope`) are unchanged.
- **Touches stored data?** No — command-doc edits.
- **Parallelizable?** Yes (independent of Items 1–2). **Depends on:** none.

### Item 4 — Extend the acceptance harness (keep all prior green)

- **Objective:** `docs/build-plans/bp-004/acceptance/run.sh` proves the A5/A6 fixes and
  chains bp-002's harness (transitively bp-001, bp-000) green.
- **Files:** `docs/build-plans/bp-004/acceptance/run.sh` (new).
- **Acceptance test:** the harness exits 0, with: **PRIOR** — bp-002's run.sh by
  reference exits 0 (all 18 prior criteria); **0006-strip** — comment-bearing `ready`
  blocks on gate-guard (hook mode), Stop-gate tracked, Stop-gate untracked, each with a
  clean-`ready` control that also blocks; **0006-nospace** — `ready#x` does NOT block
  (rc=0) on all three; **0006-scope** — a `#` in a non-status field survives
  `parse_front_matter` while `_status_in_text`/`status_of` strip it from status;
  **template/command/finding checks** — Items 2/3/5's grep assertions.
- **Falsifier:** a new test passes **vacuously** — e.g. a Stop-gate BLOCK fires for a
  reason other than the blessing (the reason-string grep for "blessing"/the filename
  fails), or the clean-`ready` control does not block (the path is not actually wired).
- **Invariant(s) it must not violate:** all new checks run in **isolated temp git repos**
  (never mutate the main worktree's enforcement state); the active-plan pointer is
  saved/restored (bp-002 pattern, `bp-002/acceptance/run.sh:27-32`).
- **Touches stored data?** No — a test harness; temp repos only.
- **Parallelizable?** No — depends on Items 1–3 landing first. **Depends on:** Items 1, 2, 3.

### Item 5 — Promote finding-0006 and finding-0008

- **Objective:** both findings reach their terminal `promoted` state, accounted to A5/A6.
- **Files:** `docs/findings/finding-0006.md` (`status: open → promoted`),
  `docs/findings/finding-0008.md` (`status: routed → promoted`); each set `resolution`
  to link the amendment (A5 / A6) + this plan (bp-004), bump `updated: 2026-07-06`.
- **Acceptance test:** `grep` shows `status: promoted` and a `resolution:` citing A5
  (finding-0006) / A6 (finding-0008) and bp-004 on each finding.
- **Falsifier:** a finding is flipped to `promoted` while its fix is **not** actually
  landed (premature promotion) — guarded by ordering this **last**, after Item 4's harness
  is green.
- **Invariant(s) it must not violate:** promotion is not a blessing gate (findings are not
  gate-guarded), but it is a terminal accounting act — it must trail the landed fix and
  green harness, never lead it.
- **Touches stored data?** No — finding-doc lifecycle edits.
- **Parallelizable?** No — the terminal step. **Depends on:** Items 1, 2, 3, 4.

## 8. Math carried explicitly

N/A — no mathematical object implemented. This plan lands parser/enforcement,
template, command, and finding-lifecycle edits; no measure, metric, or field-guide
object is introduced.

## 9. Non-goals

- **No design-note edit.** A5/A6 are already ratified (§3/§6/§16); this plan lands only
  their mechanical consequence. `docs/design-notes/**` is foundation-denylisted.
- **No blessing flip.** This session writes no `status: ratified` and no
  `proposed → ready` anywhere, and does not flip bp-004 out of `proposed`. Readiness is
  the owner's hand edit (§10).
- **No normalization of `cmd_brief`'s status read** (`_lib.py:533`) — cosmetic, not a
  bright line; the template fix removes the comment-bearing source for new plans (§3).
- **No fold of `_normalize_status` into `_scalar`/`parse_front_matter`** — the fix is
  status-path-only; a general strip would break a legitimate `#` in other fields (§3 Q4).
- **No rewrite of bp-000..bp-003** or their harnesses — historical, minted on the old
  template; they need no change (finding-0008.md:60-61).
- **No `docs/PROGRESS.md` entry** — the orchestrator's post-build single-writer act.

## 10. Stop-and-raise conditions

- The design note is not `status: ratified` — halt and tell the owner (confirmed
  `ratified`, `agent-workflow.md:4`, before starting).
- A discovered spec defect (e.g. A5/A6 as written cannot be realized without a
  design-note change) — **file a finding, route it, park the criterion, continue** the
  rest; never edit the design note and never block on the owner (§5).
- A blast-radius surprise — `_normalize_status` would change a verdict on a clean status
  line, or a prior harness criterion regresses — **stop, investigate, do not weaken a
  test to make it pass.**
- A blessing transition would be required to proceed — **it must not be performed** (§10);
  surface and stop.
- An out-of-scope change cannot be reverted or converted to a finding — end the session
  after a fresh journal (a `blocker`).

## 11. Parked decisions

| Decision                                                                     | Default recorded                                                         | Rejected alternatives (why)                                                                                                                                                        | Re-entry condition                                                                                                                                         |
| ---------------------------------------------------------------------------- | ------------------------------------------------------------------------ | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Normalize `cmd_brief`'s status render (`_lib.py:533`)                        | **Not done** — leave the cosmetic path as-is                             | (a) route `cmd_brief` through `status_of` — widens the diff past the ratified A5 contract for a non-enforcement nicety; the template fix already moots it for new plans            | A real session is observed rendering a comment-bearing status in the brief for a plan whose status line legitimately carries a comment (none exists today) |
| Belt-and-suspenders: normalize `cmd_gate_check`'s `new_status` parameter too | **Not done** — the extractor-level fix covers the real (hook/stdin) path | (a) normalize inside `cmd_gate_check` — only reachable via `--standalone` with a raw comment-bearing status, a debug-only input; redundant with the extractor fix on the real path | A `--standalone` invocation with a raw comment-bearing status is shown to matter operationally (it is a debug convenience today)                           |

## 12. Dependency & ordering summary

Blast-radius phase order (all reversible file writes; no read-only-sensing or
irreversible/external items):

1. **Item 1** (A5 `_lib.py` fix) — the enforcement mechanism; no deps.
2. **Item 2** (A5+A6 template) — parallelizable with Item 1; no deps.
3. **Item 3** (A6 commands) — parallelizable with Items 1–2; no deps.
4. **Item 4** (harness) — **gated on Items 1, 2, 3** (it verifies them).
5. **Item 5** (promote findings) — **gated on Items 1–4** (terminal accounting; must
   trail the green harness).

Items 1/2/3 may proceed in any order or concurrently (disjoint files); Item 4 is the
join point; Item 5 is the terminal step. No cross-plan dependency — bp-004 is
self-contained and requires no other plan. Completion evidence lives in the **journal**;
bp-004 is held at `proposed` (owner's ready-flip is the only path onward, §10).
