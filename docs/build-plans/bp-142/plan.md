---
type: build-plan
id: bp-142
track: workflow
status: proposed
design_ref:
  - docs/design-notes/dn-typed-workflow-registry.md
contract: builder
write_scope:
  - ops/registry/**
  - scripts/registry.py
  - tests/unit/test_registry_export.py
  - tests/integrity/test_registry_export_ratchet.py
session_budget: 1
cost:
  estimate:
    model: opus
    tokens: 350k
  actual: null
depends_on: [bp-140]
parallelizable_with: [bp-144]
created: 2026-07-27
updated: 2026-07-27
links:
  - docs/design-notes/dn-typed-workflow-registry.md
  - docs/build-plans/bp-140/plan.md
  - scripts/handoff.py
re_entry: null
supersedes: null
superseded_by: null
warrant: null
---

# Build Plan — The export renderer, the idempotence pin, and the `export == working tree` ratchet

## 0. Mode & provenance

Investigation and planning produced this plan during `/graduate` of
`dn-typed-workflow-registry` (ratified 2026-07-27); it graduates the first half of the
note's license (ii). Implementation proceeds item-by-item on owner approval; the
`proposed → ready` blessing is the owner's alone.

This plan builds the ratchet but **migrates nothing** — the registry is still empty of real
artifacts, so `export == working tree` is vacuously true until bp-143 backfills. That
ordering is deliberate: the check exists and is green *before* the data move, so the data
move has a red/green signal to move against.

## 1. Objective

Render an entity's authoritative front matter back into its markdown file as a derived view
under an idempotence pin — no clock, no counter — and prove `export == working tree` as a
non-skippable CI check.

## 2. Context manifest

1. `docs/design-notes/dn-typed-workflow-registry.md` §2.3 (the seam, the export pin, the
   ratchet, what survives of today's ergonomics), §2.8's last bullet (CI needs no tunnel),
   §2.9 invariant 4, falsifier F2.
2. `scripts/handoff.py:18-40` — **the in-tree idempotence pin, verbatim.** "The *committed*
   rendering is a pure function of the artifact tree EXCLUDING ITSELF, and embeds **no HEAD
   sha and no generation timestamp**. So regenerate-then-commit converges in one step." The
   note names this as the exact precedent; this plan copies its discipline, not its code.
3. `scripts/handoff.py:63` + `scripts/board.py:45` — `GENERATED_BANNER`, the in-tree marker
   for a derived file, and the `--write` / `--check` / `--json` mode split.
4. `docs/build-plans/bp-140/plan.md` §6 — the store, `Event`, `EntityState`, the fold rule,
   the CLI. This plan extends that CLI.
5. `.claude/hooks/_lib.py:183-250` — `parse_front_matter`, `_scalar`, `_normalize_status`.
   The export must round-trip through **this** parser, because it is the parser every guard
   and every derived view already uses; anything the export renders that this parser reads
   back differently is drift by construction.
6. `docs/templates/build-plan.md:1-31` and any one existing plan (e.g.
   `docs/build-plans/bp-139/plan.md:1-32`) — the front-matter shape and key ordering the
   export must reproduce.
7. `pyproject.toml [tool.pytest.ini_options] markers` — the `integrity` marker:
   "firewall/provenance/attestation/import-lint — the non-skippable CI gate". The ratchet
   belongs there.
8. `docs/build-plans/bp-142/journal.md`.

### DRY audit — does `core/` (or the wider tree) already have this?

- **An idempotent derived-view renderer with a `--check` byte-compare?** **Yes, twice:**
  `scripts/handoff.py` (`--write`/`--check`, the idempotence pin at `:18-40`) and
  `scripts/board.py` (`--write`, `GENERATED_BANNER` at `:45`). Neither renders *front
  matter*, and neither is parameterized over artifact type — so the **pattern is reused and
  the code is not**. Copy the mode split, the banner discipline, and the no-clock/no-counter
  rule; do not import `handoff.py` (it renders seat panes) or fork it.
- **A front-matter *writer*?** **None exists** — verified: `.claude/hooks/_lib.py` parses
  only (`parse_front_matter`, `_split_front_matter` at `:654`), and no module in the tree
  emits front matter. `_split_front_matter` is directly reusable for the "replace the header,
  keep the body byte-identical" operation and **must** be reused (Item 11).
- **A canonical serializer?** `core/verdict/payload.py:37-42` for JSON; the export emits
  YAML-subset front matter, a different target. Reuse the *discipline* (deterministic key
  order, fixed separators), not the function.
- **`core/` audit:** core owns nothing about markdown front matter and must not — this is
  repo-workflow tooling, and core never absorbs it (CONVENTIONS §Trust boundaries).

## 3. Investigation & grounding

- **Q1 — where does the git-visible event-log snapshot live?** The note says only "a
  git-visible export of the event log snapshot for CI" (§2.8) and parks the format
  ("snapshot format — decided at stage (i) build"). `data/` is gitignored and per-worktree
  (`scripts/handoff.py:29-33`), so it cannot hold a committed artifact. Pinned:
  `ops/registry/snapshot/events.jsonl` — inside this plan's existing `write_scope`, on the
  machinery side where `ops/attestation/*.pub` already keeps committed non-secret state, and
  requiring no new top-level directory. Recorded in §11.
- **Q2 — how is the ratchet made hermetic in CI?** Note §2.3: "CI regenerates the export
  from the committed event log snapshot and byte-compares. This needs **no access to the
  machine-level store**." So the check is: build a **throwaway registry in a temp dir** from
  `snapshot/events.jsonl`, export it, byte-compare against the working tree. Verified
  feasible: the CI `ratchet` job checks out the repo and runs the model-free pytest tier
  (`.github/workflows/ci.yml`), which needs no machine-level state.
- **Q3 — does this need a new CI job?** **No.** The existing `ratchet` job runs
  `uv run pytest -q -m 'not live and not podman and not needs_vault and not needs_restic'`,
  which includes `tests/integrity/`. Putting the ratchet in `tests/integrity/` gets it into
  **both** the remote pipeline and the local gate (`ops/lifecycle/launcher.py:578-589`
  `gate_cmd` runs the same deselect-set) with **zero** workflow-file edits. `.github/workflows/ci.yml`
  and `ops/lifecycle/launcher.py` are therefore deliberately **out of `write_scope`** — least
  privilege, and one fewer surface to get wrong. Recorded in §11 in case the owner wants a
  named job for signal.
- **Q4 — what exactly does the export own?** Note §2.3: "the registry owns state, identity,
  relations, transitions, ordering; the file owns prose. The file keeps a **minimal header**
  (its ref, so a file is self-identifying when read cold) and nothing else that can drift."
  So the export renders the **whole front-matter block** and touches **not one byte** of the
  body. `_split_front_matter` (`_lib.py:654`) is the seam.
- **Q5 — is key ordering in the rendered front matter stable?** It must be, or F2 trips.
  Python dicts preserve insertion order, and `.claude/hooks/_lib.py:183`'s parser returns an
  insertion-ordered dict — but a *fold* over events has no inherent key order. Pinned in §6.3:
  an explicit `KEY_ORDER` tuple, with unknown keys appended in sorted order. This is the
  single most likely F2 trip; test it directly.
- **Q6 — does anything read `updated:` as a clock?** Yes — `updated:` is a date field in
  every artifact's front matter (`docs/build-plans/bp-139/plan.md:22`). It is **data**, not a
  render input: it comes from an event payload, so re-exporting an unchanged log reproduces
  it byte-for-byte. The export must never call `datetime.now()`. Assert it: Item 13's
  falsifier greps the export module for a clock read.
- **Q7 — is there a `.gitattributes` or line-ending hazard?** The comparison is byte-exact.
  `_split_front_matter` operates on text; the export must write with `newline="\n"` and
  UTF-8 explicitly so a platform default never enters the bytes. **The code does not settle
  whether any artifact currently contains CRLF** — Item 11's first act is a scan
  (`grep -rlU $'\r' docs/`), reported in the journal.

**Additional risks or questions surfaced during reading:**

- The ratchet's failure message is a user interface. When it goes red, an agent must be able
  to fix it in one mechanical command — that is the whole point of the pin
  (`scripts/handoff.py:18-27`: "the freshness gate is dischargeable by one mechanical
  command"). The failure output must print the exact command (`uv run scripts/registry.py
  export --write`) and a unified diff, not just "files differ".
- Until bp-143 migrates, the snapshot is empty and the ratchet is vacuously green. A
  vacuously-green ratchet is a real risk: it could stay vacuous and nobody would notice.
  Item 14 therefore requires a **fixture-backed** test with a non-empty synthetic registry,
  so the ratchet is proven to be able to go red before it has real data to guard.

## 4. Reconciliation

- `scripts/handoff.py:18-27` (THE IDEMPOTENCE PIN) → **cross-ref: extension.** The export
  adopts the same pin for a second derived-view family. Add a one-line cross-reference in
  `ops/registry/export.py`'s module docstring naming `scripts/handoff.py:18-27` as the
  precedent, so a later reader sees one rule with two implementations rather than two rules.
- `.claude/hooks/_lib.py:654 _split_front_matter` → **cross-ref: extension.** Its docstring
  gains a note that it is now also the seam for the registry export's header replacement.
  **No behavior change**; if the function's current behavior is wrong for this use, that is a
  finding, not a quiet edit.
- `ops/registry/schema.md` (from bp-140) → **cross-ref: extension**: gains an "Export" section
  describing the snapshot format and the ratchet.
- Nothing is corrected; no banner is owed. In particular the design note is ratified and
  agent-immutable and is not edited by this plan.

## 5. Write scope

- `ops/registry/**` — new `export.py` (render + write + check), `snapshot.py` (log →
  `events.jsonl` and back), `snapshot/events.jsonl` (the committed snapshot, empty at
  landing), and an "Export" section appended to `schema.md`.
- `scripts/registry.py` — `export` and `snapshot` subcommands.
- `tests/unit/test_registry_export.py` — rendering, key order, body preservation,
  byte-idempotence.
- `tests/integrity/test_registry_export_ratchet.py` — the non-skippable gate: rebuild from
  the committed snapshot, export, byte-compare the working tree.

**Deliberately OUT of scope:** `.github/workflows/ci.yml` and `ops/lifecycle/launcher.py`
(§3 Q3 — the `integrity` marker already puts the check in both gates); every existing
artifact's front matter (bp-143 migrates; this plan's export must be a **no-op** against
today's tree because the registry is empty); `.claude/hooks/_lib.py` **beyond a docstring
cross-reference** (behavior change there is a finding); every hook and
`.claude/settings.json`; `docs/design-notes/**`; the foundation denylist.

**Retrofit check.** `grep -rn "_split_front_matter\|GENERATED_BANNER" tests/ .claude/ scripts/`
before starting. `tests/unit/test_board.py` and `tests/unit/test_handoff_purity.py` pin the
*existing* derived views' purity; this plan changes neither renderer, so neither test moves —
but re-run both, because a shared-parser regression would surface there first. If a change to
`_lib.py` beyond a docstring proves necessary, `tests/unit/` files asserting `_lib` behavior
must be added to `write_scope` **before** touching it — file a finding and stop instead
(§10).

## 6. Interfaces pinned inline

### 6.1 The idempotence pin (from `scripts/handoff.py:18-27`, verbatim — the rule this plan inherits)

> ⚑ THE IDEMPOTENCE PIN (§2.9, load-bearing for the whole family). The *committed* rendering
> is a pure function of the artifact tree EXCLUDING ITSELF, and embeds **no HEAD sha and no
> generation timestamp**. So regenerate-then-commit converges in one step, and a freshness
> gate that compares the regeneration against the committed file can be discharged by one
> mechanical command instead of re-arming forever. A rendering that embedded HEAD or `now()`
> would have no fixed point — the defect this design exists to remove, mechanized.

Registry restatement (note §2.3): "no wall-clock, no sequence counters in the rendered text,
so two exports of an unchanged registry are byte-identical." This is **invariant 4**.

### 6.2 API

```python
# ops/registry/export.py
def render_front_matter(state: EntityState) -> str:
    """The front-matter block for one entity — '---\\n' … '---\\n'. PURE: no clock, no
    counter, no HEAD, no environment. Keys emitted in KEY_ORDER (§6.3); unknown keys
    appended in sorted() order so a new field cannot reorder an old one."""

def export_file(state: EntityState, path: Path) -> str:
    """The full file bytes: rendered front matter + the EXISTING body, byte-identical.
    Body extraction reuses .claude/hooks/_lib.py:654 _split_front_matter — never a
    re-derived split."""

def export_all(registry: Registry, *, root: Path, write: bool) -> ExportReport: ...

def check(registry: Registry, *, root: Path) -> ExportReport:
    """export_all(write=False) + byte-compare. report.ok is True iff every entity's file
    is byte-identical to its rendering."""
```

```python
@dataclass(frozen=True)
class ExportReport:
    ok: bool
    differing: list[Path]
    missing: list[Path]          # entity in the registry with no file in the tree
    unregistered: list[Path]     # file in the tree with no entity in the registry
    diff_text: str               # unified diff, for the ratchet's failure message
```

```python
# ops/registry/snapshot.py
SNAPSHOT_PATH = Path("ops/registry/snapshot/events.jsonl")

def write_snapshot(registry: Registry, *, root: Path) -> None:
    """One canonical-JSON event per line, ascending seq, newline-terminated, UTF-8, LF.
    APPEND-ONLY IN EFFECT: because the log is append-only (invariant 1), a rewrite of this
    file can only ever extend it. Assert that: refuse to write a snapshot that is not a
    prefix-extension of the committed one."""

def load_snapshot(path: Path, into: Registry) -> int:
    """Replay a snapshot into an empty registry; return the number of events. This is the
    hermetic CI path — no machine-level store is ever opened (note §2.8)."""
```

### 6.3 Deterministic key order

```python
KEY_ORDER: tuple[str, ...] = (
    "type", "id", "track", "status", "design_ref", "contract", "write_scope",
    "session_budget", "cost", "depends_on", "parallelizable_with", "created",
    "updated", "links", "re_entry", "supersedes", "superseded_by", "warrant",
)
```

Grounded in `docs/templates/build-plan.md:1-31` — this is the template's own order, so an
exported plan reads like a hand-written one. Keys not in `KEY_ORDER` are appended in
`sorted()` order. Design notes and findings use the same rule over their own templates'
orders; a key absent from an entity is **omitted**, never emitted as `null`, unless the
template itself carries it as an explicit `null` (e.g. `re_entry: null`).

### 6.4 Rendering rules (F2 lives here)

- Scalars: emitted bare unless the value contains `: `, ` #`, or a leading/trailing space —
  then double-quoted. ⚑ **`write_scope` entries are ALWAYS emitted bare** and an entry
  containing ` #` is a **hard error**, not a quoted escape: `.claude/hooks/_lib.py:218
  _scalar` strips a trailing comment only from a *quoted* scalar, so a quoted glob would
  silently change what `scope-guard` matches. This is the bp-066 footgun, mechanized.
- Lists: block style, two-space indent, `  - value`. Empty list → `[]` on the key line.
- `null` → the literal `null`.
- No trailing whitespace on any line; exactly one `\n` after the closing `---`.
- **No clock, no counter, no HEAD, no environment read** anywhere in the module.

### 6.5 CLI additions

```
uv run scripts/registry.py export            # render to stdout (all entities, dry)
uv run scripts/registry.py export --write    # write the tree
uv run scripts/registry.py export --check    # byte-compare; exit 0 == identical, 1 == drift
uv run scripts/registry.py snapshot --write  # refresh ops/registry/snapshot/events.jsonl
uv run scripts/registry.py snapshot --check  # snapshot matches the log
```

`--check`'s failure output prints the unified diff **and** the literal remediation command
`uv run scripts/registry.py export --write`.

### 6.6 Invariants

4. The export embeds no clock and no counter; two exports of an unchanged log are
   byte-identical. *(note §2.9, verbatim — this plan's central obligation)*
1. No event is ever mutated or deleted; the snapshot can only extend.
5. Reads degrade to the export — this plan is what makes that fallback *certified* rather
   than merely available.

## 7. Items

### Item 11 — the renderer: front matter out, body untouched

- **Objective:** `render_front_matter` + `export_file` produce a file whose header is derived
  and whose body is byte-identical to what was there.
- **Files:** `ops/registry/export.py`, `tests/unit/test_registry_export.py`
- **Acceptance test:** `uv run pytest tests/unit/test_registry_export.py -q` green: for a
  fixture artifact, `export_file` reproduces the body byte-for-byte (assert on `bytes`, not
  `str`), and re-parsing the rendered header with `.claude/hooks/_lib.py:parse_front_matter`
  returns exactly the `EntityState` fields it was rendered from (round-trip).
- **Falsifier:** the round-trip loses or mangles a field — most likely a `write_scope` glob
  or a list-valued `links`. If `parse_front_matter(render(x)) != x` for any fixture, the
  export is not a faithful projection and every downstream guard reading the tree is being
  handed a lie.
- **Invariant(s) it must not violate:** the body is never touched; `_split_front_matter` is
  reused, never re-derived.
- **Touches stored data?** No — `--write` is not implemented until Item 13.
- **Parallelizable?** No.  **Depends on:** bp-140 Item 5 (`EntityState`).

### Item 12 — the snapshot: log → `events.jsonl` → throwaway registry

- **Objective:** a committed, git-visible, prefix-extending snapshot of the event log, and a
  loader that rebuilds a registry from it with no machine-level store.
- **Files:** `ops/registry/snapshot.py`, `ops/registry/snapshot/events.jsonl`,
  `scripts/registry.py`, `tests/unit/test_registry_export.py`
- **Acceptance test:** a test writes N events, snapshots, loads into a **second, empty**
  registry at a temp path, and asserts `fold()` agrees for every entity. Plus: attempting to
  write a snapshot that is **not** a prefix-extension of the committed file exits non-zero
  with a named reason.
- **Falsifier:** the reloaded registry disagrees with the original on any entity's status,
  relations, or content hash. The snapshot is then not a faithful serialization and CI's
  hermetic leg (note §2.8) cannot be trusted.
- **Invariant(s) it must not violate:** invariant 1 — a snapshot rewrite can only extend.
- **Touches stored data?** Yes — writes a committed file. Dry-run: `snapshot --check` first;
  the initial committed file is **empty** (zero events) and that is correct at landing.
- **Parallelizable?** Yes.  **Depends on:** bp-140 Items 1–5.

### Item 13 — `export --write` / `--check`, and the no-clock proof

- **Objective:** the CLI writes and byte-compares, and the module provably reads no clock.
- **Files:** `ops/registry/export.py`, `scripts/registry.py`,
  `tests/unit/test_registry_export.py`
- **Acceptance test:** two consecutive `export --write` runs against an unchanged registry
  leave the tree byte-identical (`git status --porcelain` empty after the second); a test
  asserts `export --check` exits 0 on a converged tree and 1 with a unified diff and the
  remediation command on a hand-perturbed one.
- **Falsifier:** **F2 (idempotent export)** — two consecutive exports of an unchanged
  registry differ by one byte. Prove it *actively*, not by hoping: an AST scan of
  `ops/registry/export.py` for `datetime`, `time`, `now`, `uuid`, `random`, `os.environ`,
  `subprocess` — any hit fails the test. (The same shape as `scripts/check_imports.py`'s
  AST scans, which this repo already trusts as a tier-4 backing.)
- **Invariant(s) it must not violate:** invariant 4, verbatim.
- **Touches stored data?** Yes — writes artifact files. Guarded: with an **empty** registry
  the export is a no-op over zero entities, which is the state at landing. Any run that
  would modify an existing tracked artifact in this plan is a bug (bp-143 owns migration) —
  assert `git status --porcelain` is empty after `export --write` on the shipped state.
- **Parallelizable?** No.  **Depends on:** Items 11, 12.

### Item 14 — the ratchet: `export == working tree`, non-skippable

- **Objective:** an `integrity`-marked test that rebuilds from the committed snapshot,
  exports, and byte-compares — hermetic, no machine-level store.
- **Files:** `tests/integrity/test_registry_export_ratchet.py`
- **Acceptance test:** `uv run pytest -q -m integrity` green, and the same test runs inside
  the standard gate (`uv run pytest -q -m 'not live and not podman and not needs_vault and
  not needs_restic'`) — confirm by running it and seeing the test id in `-v` output. The
  test must set `OUROBOROS_REGISTRY` to a temp path and assert it never opens
  `~/.mind-palace/registry.sqlite`.
- **Falsifier:** ⚑ **the ratchet is vacuously green.** With an empty snapshot the check
  passes trivially and would keep passing forever. The test must therefore *also* build a
  **non-empty synthetic** registry, perturb one exported file, and assert the check goes
  **red** with a diff naming that file. A ratchet that has never been observed red is not a
  ratchet (structural-enforcement rule: a property is only real when a test proves it).
- **Invariant(s) it must not violate:** hermeticity — no network, no machine-level store, no
  `~` access.
- **Touches stored data?** No — temp paths only.
- **Parallelizable?** No.  **Depends on:** Items 12, 13.

### Item 15 — `schema.md` gains the export contract

- **Objective:** the store's shipped documentation states the snapshot format, the key
  order, the pin, and the one-command remediation.
- **Files:** `ops/registry/schema.md`
- **Acceptance test:** the file exists, names `ops/registry/snapshot/events.jsonl`, quotes
  `KEY_ORDER`, and states the remediation command verbatim; `uv run scripts/registry.py
  export --help` prints the same command string (grep both, assert equal).
- **Falsifier:** the documented remediation command does not actually converge the tree —
  run it on a perturbed tree and check `git status`. Documentation that names a command that
  does not work is worse than none, because it is trusted.
- **Invariant(s) it must not violate:** CONVENTIONS §Data stores: "Ship migrations and a
  `schema.md`."
- **Touches stored data?** No.
- **Parallelizable?** Yes.  **Depends on:** Items 13, 14.

## 8. Math carried explicitly

N/A — no mathematical object implemented. Byte-idempotence is a fixed-point property of a
rendering function, and it earns its place through Item 13's falsifier rather than a
field-guide entry.

## 9. Non-goals

- **No migration.** The registry stays empty; no existing artifact's front matter is
  rewritten. `export --write` on the shipped state must be a **no-op**. bp-143 owns the
  backfill.
- **No enforcement change.** No hook edited or removed; `.claude/settings.json` untouched.
- **No new CI job and no workflow-file edit** (§3 Q3).
- **No `_lib.py` behavior change** — a docstring cross-reference only.
- **No signature verification in the ratchet.** Re-verifying privileged transitions in CI
  (note §2.4.1's second leg) is bp-145.
- **No consumer re-pointing.** `scripts/board.py` and `scripts/handoff.py` keep scanning the
  tree; they are unaffected because the tree stays authoritative-looking. bp-148.
- **No new dependency.**

## 10. Stop-and-raise conditions

- The round-trip (Item 11) requires a **behavior** change in `.claude/hooks/_lib.py` — stop
  and file a `codebase` finding. That parser is read by every guard; changing it under a
  plan whose `write_scope` does not carry its tests is exactly the retrofit trap
  (findings 0071/0072/0075/0084).
- Any artifact in `docs/` is found to contain CRLF (§3 Q7) — stop and report; a silent
  normalization would rewrite files this plan promises not to touch.
- `export --write` on the shipped state produces a non-empty `git status` — stop. That means
  the export is not a no-op against today's tree and the plan has silently become bp-143.
- F2 trips — stop; the frontmatter/prose split re-arms the staleness treadmill it was built
  to end.
- Any blessing this plan would have to perform — it must not.

## 11. Parked decisions

| Decision | Default recorded | Rejected alternatives (why) | Re-entry condition |
|---|---|---|---|
| Snapshot location | `ops/registry/snapshot/events.jsonl` | `data/` (gitignored, per-worktree — cannot be committed); a new top-level `.registry/` (a new convention for one file) | Owner names another path |
| Ratchet as an `integrity` test vs a named CI job | an `integrity`-marked test — reaches remote CI **and** the local gate with zero workflow edits | a dedicated `registry-ratchet` job — better failure signal in the Actions UI, but a second surface to maintain and an edit to `.github/workflows/ci.yml` this plan otherwise does not need | The owner wants a named job in the Actions UI; prerequisite: an owner ruling |
| Front-matter emission style for long lists | block style, two-space indent, always | flow style `[a, b]` — the parser reads both (`_lib.py:206-210`), but block style is what every existing artifact uses and diff-legibility is the whole point of keeping prose in git | A rendered file becomes unreadable in review |
| What to do about `unregistered` files (in tree, not in registry) | **reported, not deleted, not registered** | auto-registering — it would let a hand-written file mint itself an identity, defeating serial minting | bp-143, which is exactly the plan that turns them from unregistered into registered |

## 12. Dependency & ordering summary

**Within the plan.** Item 11 (pure rendering, no writes) → Item 12 (writes a committed
snapshot) → Item 13 (writes artifact files, guarded to a no-op) → Item 14 (the ratchet, temp
paths only) → Item 15 (documentation). Blast radius rises to Item 13 and falls again: the
widest-radius act is `export --write`, and it is provably a no-op on the shipped state.

**Across plans.** `depends_on: [bp-140]` — the store, `Event`, `EntityState`, and the fold.
**bp-143 depends on this plan**: migration needs a ratchet to move against, and the note's
§2.3 makes the ratchet the thing "that makes the split safe." Not parallelizable with
bp-141/bp-143/bp-146 (shared `ops/registry/**`). **Parallelizable with bp-144** (disjoint
scope; independent by note §2.5.2). `bp-138`/`bp-139` are independent of this whole family
(note §3(5)).
