---
type: build-plan
id: bp-143
track: workflow
status: proposed
design_ref:
  - docs/design-notes/dn-typed-workflow-registry.md
contract: builder
write_scope:
  - ops/registry/**
  - scripts/registry.py
  - tests/unit/test_registry_migration.py
  - tests/integrity/test_registry_export_ratchet.py
session_budget: 1
cost:
  estimate:
    model: opus
    tokens: 400k
  actual: null
depends_on: [bp-140, bp-142]
parallelizable_with: [bp-144]
created: 2026-07-27
updated: 2026-07-27
links:
  - docs/design-notes/dn-typed-workflow-registry.md
  - docs/build-plans/bp-142/plan.md
  - scripts/board.py
re_entry: null
supersedes: null
superseded_by: null
warrant: null
---

# Build Plan — The front-matter migration: every artifact ingested, not one byte rewritten

## 0. Mode & provenance

Investigation and planning produced this plan during `/graduate` of
`dn-typed-workflow-registry` (ratified 2026-07-27); it graduates the second half of the
note's license (ii). Implementation proceeds item-by-item on owner approval; the
`proposed → ready` blessing is the owner's alone.

⚑ **This plan's central design commitment, decided at graduation and load-bearing for its
entire write scope:** the migration is **read-only over the artifact tree**. Every artifact's
front matter is *ingested* into the registry; **no artifact file is rewritten**. The
migration succeeds exactly when `export == working tree` is byte-identical *without any
file having changed*. That is what keeps the widest-blast-radius plan in the family from
touching a single committed artifact — and it is what makes the plan lawful at all, since
ratified and superseded design notes are agent-immutable (A8) and no builder may edit them.

## 1. Objective

Ingest every existing workflow artifact's front matter into the registry, faithfully enough
that the bp-142 export reproduces the working tree byte-for-byte with zero file changes.

## 2. Context manifest

1. `docs/design-notes/dn-typed-workflow-registry.md` — §2.3 (the seam and the ratchet),
   §1.2 non-goal 7 ("Historical prose is not migrated. Migration moves frontmatter *fields*
   into the registry; the §1..§9 bodies of every existing artifact stay byte-identical
   markdown"), §2.2 (entity types), falsifier F2.
2. `docs/build-plans/bp-142/plan.md` §6 — the export API, `KEY_ORDER`, the rendering rules,
   the snapshot format, the ratchet. **This plan extends §6.3**; read it before writing.
3. `docs/build-plans/bp-142/journal.md` — what landed, and the CRLF scan result.
4. `scripts/board.py:139-233` — `_scan_manifests`, `scan_plans`, `scan_notes`,
   `scan_findings`, `scan_oqs`. **The tree scanners already exist and are already trusted by
   two derived views.** The migration reuses them; it does not write a third scanner.
5. `.claude/hooks/_lib.py:183-250` — `parse_front_matter`, `_scalar`, `_normalize_status`.
   The one parser. Note especially `_scalar`'s quoted-vs-unquoted comment behavior — it is
   the source of the known round-trip hazard (§3 Q3).
6. `CLAUDE.md` §"Rules that bind every session" — "Design notes are status-guarded (A8):
   `draft` is agent-writable working material; `ratified`/`superseded` are agent-immutable
   (HEAD-keyed, laundering-proof)." This is why the migration cannot rewrite files.
7. `.claude/hooks/_lib.py:35-39` — the foundation `DENYLIST`, verbatim.
8. `docs/build-plans/bp-143/journal.md`.

### DRY audit — does `core/` (or the wider tree) already have this?

- **Tree scanners for plans / notes / findings / owner questions?** **Yes** —
  `scripts/board.py:174` `scan_plans`, `:190` `scan_notes`, `:199` `scan_findings`, `:219`
  `scan_oqs`, `:283` `_scan_deskchecks`. `scripts/handoff.py:57-61` already imports them
  from repo-workflow tooling; this plan does the same. **Writing a fifth scanner is a
  defect**, and it is the specific defect (finding-0101/0103) the owner treats as a bug.
- **A front-matter parser?** One, `_lib.py:183`. Reused, never re-derived.
- **A tree→log importer?** **Yes — `ops/registry/recover.py::import_tree` from bp-141.**
  This is the DRY answer that most changes this plan's shape: the recovery import *already*
  reads the tree into the log with conflict reporting. **The migration is `import_tree`
  run once against an empty registry, not a second importer.** Item 16 extends and
  hardens it; it does not duplicate it. If bp-141 has not landed, see §10.
- **`core/` audit:** core owns nothing here and must not.

## 3. Investigation & grounding

- **Q1 — how many artifacts are in scope, and of what types?** Measure before building
  (`ls docs/build-plans | wc -l`, `ls docs/findings | wc -l`, `ls docs/design-notes | wc -l`).
  As of graduation the tree holds ~30 build-plan directories (`bp-108`…`bp-139` with gaps),
  ~270 findings (`finding-0269` is the highest seen), and a design-note directory of
  comparable size. **Exact counts are Item 16's first recorded measurement**, not this plan's
  assertion — do not hard-code a number anywhere.
- **Q2 — may the migration rewrite files?** **No, for two independent reasons.** (a) Ratified
  and superseded design notes are agent-immutable under A8 — `scope-guard` denies pre-hoc on
  on-disk status and the Stop-gate clause (b2) catches a HEAD-keyed launder
  (`CLAUDE.md`; `.claude/hooks/_lib.py:453`). A migration that rewrote them would be denied
  mid-build, or worse, would be a laundering attempt. (b) The note's own non-goal 7 keeps
  bodies byte-identical, and there is no need to touch headers if ingestion is faithful.
  **Therefore the artifact tree is not in `write_scope` at all** — the strongest possible
  statement of this constraint, enforced by the guard rather than by intent.
- **Q3 — will the export round-trip today's front matter byte-for-byte?** ⚑ **Not
  automatically, and this is the plan's core technical risk.** Three known hazards, each
  grounded:
  - **Key order.** bp-142 §6.3 pins a single `KEY_ORDER` from `docs/templates/build-plan.md`.
    Real artifacts predate the template's current order and findings/notes use different key
    sets entirely. A rendered file whose keys are correctly *valued* but differently
    *ordered* is a ratchet failure the builder **cannot lawfully fix by editing the file**.
    ⇒ **Resolution pinned in §6.2: the registry preserves each entity's observed key order
    as a field, and the export renders in that order when present.** This is an extension of
    bp-142 §6.3, reconciled in §4.
  - **Inline comments on unquoted values.** `_lib.py:218 _scalar` keeps a `#` intact in an
    unquoted scalar; so `- eval/metrics.py  # absorbed` parses to the string
    `eval/metrics.py  # absorbed` (finding-0085, the bp-066 footgun). Such a value *does*
    round-trip byte-for-byte if re-emitted verbatim — but bp-142 §6.4 makes an entry
    containing ` #` a **hard error**. ⇒ The migration must **detect and report** these, not
    fix them. Any that exist become a finding for the orchestrator (§10).
  - **Whitespace and blank lines inside the front-matter block, and comment lines.**
    `parse_front_matter` skips blank lines and `#`-prefixed lines entirely (`_lib.py:196-197`)
    — so they are **invisible to the parser and therefore unrecoverable from the parse**.
    `docs/templates/build-plan.md:9-12` shows exactly such comment lines in a front-matter
    block. ⇒ §6.3 pins the answer: the entity payload carries a verbatim
    `front_matter_raw` field, and the export prefers a byte-exact replay of it whenever the
    parsed fields are unchanged. This is the only mechanism that can make migration
    byte-exact against a lossy parser, and it is why this is a *plan*, not a script.
- **Q4 — what about artifacts that are not entities?** Deskcheck records and owner questions
  are parked as non-entities by bp-140 §11. `docs/tracks/*.md` manifests, `docs/PROGRESS.md`,
  `docs/TRACKS.md`, `docs/DESKCHECK-QUEUE.md`, and every generated view are **not** workflow
  artifacts in the note's §2.2 taxonomy. They stay entirely outside the registry and outside
  the ratchet's `unregistered` complaint list — Item 18 pins the exclusion list explicitly so
  the ratchet does not grow a permanent false-positive backlog.
- **Q5 — do journals become entities?** Note §2.2 names "journal entry" as a typed entity,
  and §2.7 narrows the journal to judgement. But **the code does not settle** how a
  markdown journal's entries map to registry rows, and the note gives no schema. ⇒ This plan
  ingests journals as **one entity per journal file** with a content hash only (no entry
  decomposition), and parks the entry-level model (§11). Entry-level typing is bp-147's
  concern (the seal event) and bp-148's (the judgement narrowing).
- **Q6 — what does "migrated" mean for status, given the tree is authoritative today?**
  The `minted` event's payload carries the artifact's current front matter and its current
  status; there is **no** attempt to reconstruct the artifact's transition history from git.
  The note does not ask for it, and a reconstructed history would be an archaeological claim
  of exactly the kind §2.1 says the event log exists to abolish. Record `minted` at the
  observed state, and let real history begin at migration.

**Additional risks or questions surfaced during reading:**

- The `unregistered` list from bp-142's `ExportReport` becomes meaningful for the first time
  here. If the exclusion list (Q4) is wrong, the ratchet is permanently noisy and will be
  ignored — the classic way a green-by-habit gate dies.
- This plan writes a large `ops/registry/snapshot/events.jsonl` in one commit. It is
  committed data, and it will be large. That is acceptable (it is append-only, line-oriented,
  and diffs cleanly) but should be measured and recorded, not discovered.

## 4. Reconciliation

- `docs/build-plans/bp-142/plan.md` §6.3 (`KEY_ORDER`, "unknown keys appended in `sorted()`
  order") → ⚑ **banner: correction.** bp-142's rule is insufficient for pre-existing
  artifacts, which have neither the template's key order nor a subset of its keys. The
  correction is additive and announced as a correction:

  ```diff
  - Keys emitted in KEY_ORDER; unknown keys appended in sorted() order.
  + Keys emitted in the entity's OBSERVED key order when the entity carries one
  + (`fields["_key_order"]`, set at migration); otherwise in KEY_ORDER with unknown
  + keys appended in sorted() order. Newly minted entities carry no observed order
  + and therefore render in KEY_ORDER — the template's order — unchanged.
  ```

  `ops/registry/export.py`'s docstring must carry a banner naming this plan and bp-142's
  §6.3 as the corrected text, so a reader of either plan finds the other.
- `ops/registry/recover.py::import_tree` (bp-141) → **cross-ref: extension.** The migration
  *is* this function, hardened: byte-exactness becomes a post-condition, and the exclusion
  list (Q4) becomes a parameter. Its docstring gains a cross-reference to this plan.
- `ops/registry/schema.md` → **cross-ref: extension**: gains a "Migration" section recording
  the measured counts, the exclusion list, and the `front_matter_raw` mechanism.
- **Nothing in `docs/` is corrected or edited.** Any artifact that cannot round-trip is
  reported as a finding, never repaired in place by this plan.

## 5. Write scope

- `ops/registry/**` — `recover.py` (hardened), `export.py` (observed key order +
  `front_matter_raw` replay), `snapshot/events.jsonl` (now large and real), `schema.md`.
- `scripts/registry.py` — a `migrate` subcommand (dry-run by default) wrapping `import_tree`.
- `tests/unit/test_registry_migration.py` — round-trip fidelity per artifact type.
- `tests/integrity/test_registry_export_ratchet.py` — carried because it is the ratchet this
  plan's data now makes non-vacuous, and its fixture set must widen from synthetic to real.

**Deliberately and emphatically OUT of scope:** ⚑ **the entire artifact tree.**
`docs/design-notes/**` (ratified/superseded are agent-immutable, A8),
`docs/build-plans/*/plan.md`, `docs/build-plans/*/journal.md`, `docs/tracks/**`,
`docs/PROGRESS.md`, `docs/TRACKS.md`, `docs/DESKCHECK-QUEUE.md`, `docs/inbox/**`. If the
migration appears to *need* one of these edited, that is a stop-and-raise (§10), not a scope
widening. `docs/findings/**` is writable to **every** plan by construction (build-plan
skill) and is how a non-round-trippable artifact gets recorded. Also out: every hook,
`.claude/settings.json`, the foundation denylist, `.github/workflows/**`.

**Retrofit check.** `tests/integrity/test_registry_export_ratchet.py` is bp-142's file and
this plan changes it — it is in `write_scope` for exactly that reason. `grep -rn "registry"
tests/` before starting to catch any other test that pins the export surface; add it to the
journal's manifest delta if found, and file a finding if it needs editing and is not in
scope.

## 6. Interfaces pinned inline

### 6.1 The migration entry point

```python
# ops/registry/recover.py  (extended)
def import_tree(registry: Registry, *, root: Path, dry_run: bool = True,
                exclude: frozenset[str] = DEFAULT_EXCLUDE) -> ImportReport:
    """Read the artifact tree's front matter into the log. REUSES scripts/board.py's
    scanners and .claude/hooks/_lib.py's parser. POST-CONDITION when dry_run is False:
    ops.registry.export.check(registry, root=root).ok is True AND
    `git status --porcelain -uall` is unchanged from before the call — the migration
    changes the LOG, never the TREE."""
```

```python
@dataclass(frozen=True)
class ImportReport:
    minted: dict[str, str]           # path -> ref
    conflicts: list[str]             # never auto-resolved (note §2.9(3)(i))
    not_round_trippable: list[tuple[Path, str]]   # path, the exact reason
    excluded: list[Path]
    counts: dict[str, int]           # entity_type -> n
```

### 6.2 Observed key order (the §4 correction, pinned)

```python
# ops/registry/export.py
def render_front_matter(state: EntityState) -> str:
    """... Key order: state.fields["_key_order"] when present (a list[str] captured at
    migration from the artifact's own header), else KEY_ORDER with unknown keys appended
    in sorted() order. A newly minted entity has no observed order and renders in
    KEY_ORDER — the template's order — so new artifacts are uniform and old artifacts
    are preserved. (Corrects bp-142 §6.3; see the banner in this module's docstring.)"""
```

### 6.3 `front_matter_raw` — byte-exact replay against a lossy parser

```python
# The minted payload for a MIGRATED entity carries, in addition to the parsed fields:
#   "_front_matter_raw": "<the exact text between the opening and closing '---', verbatim>"
#   "_key_order":        ["type", "id", ...]      # observed order of top-level keys
#
# export_file() renders as follows:
#   1. Compute the rendered header from the entity's CURRENT fields.
#   2. If the entity carries _front_matter_raw AND re-parsing it yields fields equal to
#      the entity's current fields (i.e. nothing has changed since migration), emit
#      _front_matter_raw VERBATIM.
#   3. Otherwise emit the rendered header (the entity has genuinely changed and the
#      registry is now authoritative for it).
#
# WHY: `.claude/hooks/_lib.py:196-197` skips blank lines and '#' comment lines entirely,
# so they cannot be recovered from a parse. Verbatim replay is the only mechanism that
# makes migration byte-exact against a parser that is deliberately lossy — and clause 2's
# equality test is what stops it from becoming a way to launder stale bytes past the
# registry: the moment a field changes, the raw text is abandoned.
```

⚑ Clause 2's equality test is load-bearing. Without it, `_front_matter_raw` would let a
hand-edited header survive the ratchet forever, which is precisely the drift the ratchet
exists to catch (note §2.3: "a hand-edited `status:` line … is a *drift* event, and the
ratchet turns it red").

### 6.4 The exclusion list

```python
DEFAULT_EXCLUDE: frozenset[str] = frozenset({
    # generated / derived views — owned by their generators, not the registry
    "docs/TRACKS.md", "docs/DESKCHECK-QUEUE.md", "docs/roles/*/handoff.md",
    # narrative and orchestrator-owned surfaces, not typed workflow entities
    "docs/PROGRESS.md", "docs/inbox/**", "docs/brainstorms/**", "docs/book/**",
    "docs/templates/**", "docs/tracks/**", "docs/deskchecks/**",
})
```

Grounded: `docs/TRACKS.md`/`docs/DESKCHECK-QUEUE.md` are written by `scripts/board.py`
(`GENERATED_BANNER`, `scripts/board.py:45`); `docs/roles/*/handoff.md` by
`scripts/handoff.py:63`; templates are not artifacts; brainstorms are pre-artifact input
(note §"The artifact chain"); tracks are manifests (bp-140 §11 parks them as non-entities);
deskcheck records are parked as non-entities. **Verify each glob against the tree before
landing** — an exclusion that matches nothing is a stale rule, and an artifact type that
matches nothing is a silently unmigrated corpus.

### 6.5 Foundation denylist (`.claude/hooks/_lib.py:35-39`, verbatim)

```python
DENYLIST = [
    "CONSTITUTION.md",
    "eval/golden/**",
    "eval/golden.py",
]
```

Never writable, orchestrator included. The migration reads none of them and writes none.

### 6.6 Invariants

1. No event is ever mutated or deleted; corrections are events.
4. The export embeds no clock and no counter; two exports of an unchanged log are
   byte-identical.
- **This plan's own:** `git status --porcelain -uall` over `docs/` is **unchanged** by the
  migration. The log grows; the tree does not move.

## 7. Items

### Item 16 — measure, then ingest (dry-run)

- **Objective:** a dry-run migration that reports counts, conflicts, exclusions, and every
  artifact that cannot round-trip — writing nothing.
- **Files:** `ops/registry/recover.py`, `scripts/registry.py`,
  `tests/unit/test_registry_migration.py`
- **Acceptance test:** `uv run scripts/registry.py migrate` (dry-run default) exits 0 and
  prints an `ImportReport` with per-type counts; `git status --porcelain` is empty
  afterwards. The measured counts are recorded in the journal (§3 Q1 — measured, not
  assumed).
- **Falsifier:** the report's `not_round_trippable` list is empty **and** a hand-check of
  three arbitrary artifacts of different types shows a byte difference between the tree and
  the rendering. An empty list that is wrong is worse than a long list that is right — the
  check must be able to find something, so seed the fixture set with a deliberately
  awkward header (comment lines, blank lines, an unquoted `#`) and assert it is flagged.
- **Invariant(s) it must not violate:** writes nothing; opens no artifact for writing.
- **Touches stored data?** No — dry-run only, by construction.
- **Parallelizable?** No.  **Depends on:** bp-140, bp-142 (and bp-141's `import_tree` if
  landed — see §10).

### Item 17 — byte-exact rendering: observed key order + `front_matter_raw`

- **Objective:** the export reproduces every existing artifact's header byte-for-byte.
- **Files:** `ops/registry/export.py`, `tests/unit/test_registry_migration.py`
- **Acceptance test:** for **every** artifact the dry-run ingested, `export_file(...)` equals
  the file's current bytes. Assert over the whole corpus, not a sample:
  `uv run pytest tests/unit/test_registry_migration.py -q` green with a parametrized case
  per artifact discovered at collection time.
- **Falsifier:** ⚑ `front_matter_raw` replay masks a genuine field change — construct the
  case: ingest an artifact, mutate one field in the registry, and assert the export now
  emits the **rendered** header (not the raw one) and the ratchet goes red. If raw replay
  survives a field change, the mechanism has become a laundering channel and must be cut.
- **Invariant(s) it must not violate:** invariant 4; the bp-142 §6.4 rule that a
  `write_scope` entry containing ` #` is a hard error (report it, never quote it away).
- **Touches stored data?** No — rendering only; still no `--write`.
- **Parallelizable?** No.  **Depends on:** Item 16.

### Item 18 — the exclusion list, verified against the tree

- **Objective:** every path in `DEFAULT_EXCLUDE` matches something, and every artifact type
  in the note's §2.2 taxonomy matches something.
- **Files:** `ops/registry/recover.py`, `tests/unit/test_registry_migration.py`
- **Acceptance test:** a test asserts (a) each exclusion glob matches ≥ 1 path in the tree,
  (b) the union of ingested + excluded covers every `.md` under `docs/` with front matter,
  (c) the residue — files with front matter that are neither ingested nor excluded — is
  **empty**, and prints the residue when it is not.
- **Falsifier:** the residue is non-empty and consists of a *real* artifact type the note's
  §2.2 names. That means the taxonomy and the tree disagree, and migrating anyway would
  leave a silently unmanaged corpus — file a `spec-fidelity` finding and stop.
- **Invariant(s) it must not violate:** nothing in `DENYLIST` is read into the registry.
- **Touches stored data?** No.
- **Parallelizable?** Yes.  **Depends on:** Item 16.

### Item 19 — apply, snapshot, and make the ratchet real

- **Objective:** run the migration for real, commit the snapshot, and turn the previously
  vacuous ratchet into one guarding the whole corpus.
- **Files:** `ops/registry/snapshot/events.jsonl`, `ops/registry/schema.md`,
  `tests/integrity/test_registry_export_ratchet.py`, `scripts/registry.py`
- **Acceptance test:** `uv run scripts/registry.py migrate --apply` exits 0; then
  `uv run scripts/registry.py export --check` exits 0; then
  `uv run pytest -q -m integrity` green; and — the point of the whole plan —
  `git status --porcelain -uall docs/` is **empty**. The only changed files in the commit
  are `ops/registry/**` and `tests/**`.
- **Falsifier:** ⚑ **F2, now with real data** — a second `export --check` after the apply
  differs, or `git status` over `docs/` is non-empty. Additionally: perturb one real
  artifact's `status:` by hand in a scratch checkout and assert the ratchet reddens naming
  that file. A ratchet that cannot detect a hand-edited status has not replaced
  `gate-guard`'s guarantee and bp-149 must not proceed on it.
- **Invariant(s) it must not violate:** the tree does not move (§6.6); invariants 1 and 4.
- **Touches stored data?** **Yes — the widest blast radius in this family.** Mandatory
  dry-run first (Items 16–18 are that dry run). Before `--apply`: commit all other work, so
  the apply is a clean, revertible commit on its own; capture `git status --porcelain -uall`
  before and after and diff the two.
- **Parallelizable?** No.  **Depends on:** Items 16, 17, 18.

## 8. Math carried explicitly

N/A — no mathematical object implemented. The migration is a faithful re-representation, and
its correctness obligation is byte-equality (Item 17/19), not a mathematical property.

## 9. Non-goals

- ⚑ **No artifact file is edited. None.** Not a status, not a key order, not a stray comment.
  Repairs are findings, not edits.
- **No transition history reconstructed from git** (§3 Q6). Real history begins at migration.
- **No journal-entry decomposition** (§3 Q5) — one entity per journal file, content hash only.
- **No deskcheck or owner-question entities** (bp-140 §11 parks them).
- **No enforcement change.** No hook edited or removed; `.claude/settings.json` untouched.
  After this plan, status is in *both* places — the tree (authoritative for the guards) and
  the registry (authoritative for the ratchet). That redundancy is the design's intended
  intermediate state, and bp-149 is what ends it, blocked on owner amendments.
- **No signature verification.** bp-145.
- **No consumer re-pointing.** `scripts/board.py`/`scripts/handoff.py` keep scanning the tree
  and keep working, because the tree does not move. bp-148.

## 10. Stop-and-raise conditions

- **bp-141 has not landed**, so `import_tree` does not exist. Do **not** write a second
  importer — that is the duplication defect. File a finding and stop, or (owner's call)
  re-sequence so bp-141 lands first. Recorded as a dependency risk in §12.
- Any artifact requires an **edit** to migrate (§3 Q3's second and third hazards, or a
  malformed header) — file a `codebase` finding with the exact bytes and the exact reason,
  park that criterion with a re-entry condition, and continue with the rest. **Never widen
  the write scope into `docs/`.**
- Item 18's residue contains a real artifact type — `spec-fidelity` finding, stop.
- `--apply` leaves `git status` over `docs/` non-empty — **revert immediately** and stop.
  That is the plan's own invariant broken.
- The snapshot file's size makes a commit impractical — surface it as an owner question with
  the measured number; park, do not silently truncate or compress.
- Any blessing this plan would have to perform — it must not.

## 11. Parked decisions

| Decision | Default recorded | Rejected alternatives (why) | Re-entry condition |
|---|---|---|---|
| Journal entity granularity | one entity per journal **file**, content hash only | per-entry rows — the note names "journal entry" as a type but gives no schema, and inventing one is the infer-design defect | bp-147 (the seal event's typed fields) or bp-148 (the judgement narrowing) needs entry-level rows |
| Transition history reconstruction | not attempted; `minted` at observed state | reconstructing from git diffs — an archaeological claim, exactly what §2.1 says the log abolishes | An owner asks for pre-migration provenance; prerequisite: an owner ruling on what would count as evidence |
| `front_matter_raw` retention | kept indefinitely; abandoned per-entity on first field change | dropping it after migration — the ratchet would redden on every untouched artifact forever | Every migrated entity has changed at least once, making the field dead weight |
| Snapshot compaction | none — the log is append-only and the file grows | periodic compaction — would violate invariant 1's spirit and break the prefix-extension check | The file becomes a practical problem (measured, not feared) |

## 12. Dependency & ordering summary

**Within the plan.** Item 16 (read-only measurement) → Item 17 (pure rendering) and Item 18
(read-only coverage check, parallel with 17) → Item 19 (the single writing act). Blast
radius is flat and near-zero for Items 16–18 and concentrated entirely in Item 19, which is
gated on all three and preceded by a mandatory dry run. This is the note's blast-radius
ordering applied literally: three sensing items, then one irreversible-feeling act that is
nonetheless fully revertible (`git revert` of one commit; the machine-level store is
rebuildable from the snapshot).

**Across plans.** `depends_on: [bp-140, bp-142]` — the store and the export/ratchet.
**Soft dependency on bp-141** for `import_tree` (§10): if bp-141 has not landed, stop rather
than duplicate. Not parallelizable with bp-141/bp-142/bp-146 (shared `ops/registry/**`).
**Parallelizable with bp-144** (disjoint scope, independent by note §2.5.2). **bp-149 (hook
retirement) depends on this plan** — `gate-guard`'s guarantee is only replaced once the
ratchet guards real data (Item 19's falsifier is the parity evidence). `bp-138`/`bp-139` are
independent of this whole family (note §3(5)).
