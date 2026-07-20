---
type: build-plan
id: bp-075
status: in-progress
design_ref:
  - docs/design-notes/exhaust-lane.md
contract: builder
write_scope:
  - config/defaults.toml
  - core/config/loader.py
  - config/loader.py
  - scripts/exhaust_report.py
  - tests/unit/test_exhaust_report.py
  - docs/supplemental/cockpit.md
session_budget: 1
cost:
  estimate:
    model: opus
    tokens: 80k
  actual: null
depends_on: []
parallelizable_with: []
created: 2026-07-19
updated: 2026-07-19
links:
  - docs/brainstorms/exhaust-and-ingest-sync.md
  - docs/design-notes/ouroboros-principal.md
re_entry: null
supersedes: null
superseded_by: null
warrant: null
---

# Build Plan — The exhaust lane: config root, invariant test, report writer

> **Every section below is required.** A section that does not apply is marked
> `N/A — <one-line reason>`, never silently omitted.

## 0. Mode & provenance

Graduated 2026-07-19 from `dn-exhaust-lane` (ratified by the owner, `d3366a5`)
in the same fable session that drafted the note — grounding was done at design
time and is cited below. Implementation proceeds item-by-item on owner
approval; `proposed → ready` is the owner's keystroke (`palace bless bp-075` +
hand commit).

## 1. Objective

The exhaust lane exists as configuration, enforcement, and a writer: a
config-pinned root (`~/.mind-palace/exhaust/`), a test proving no ingest
source can lie inside it, and a script that places six-section HTML build
reports into `reports/`.

## 2. Context manifest

1. `docs/build-plans/bp-075/plan.md` — this plan, whole.
2. `docs/design-notes/exhaust-lane.md` — the ratified decision (§2 is the
   contract: layout, invariant, format, writer).
3. `config/defaults.toml` — whole; the `[vault]` block (`:42-46`) is the
   pattern the new exhaust key mirrors.
4. `config/loader.py` — whole; how `get_config()` merges defaults + local and
   surfaces sections (the builder confirms passthrough needs no code change,
   or makes the minimal one — see §3 Q2).
5. `scripts/docket.py` + `tests/unit/test_docket.py` — the repo-workflow
   script precedent: no `core` import, and the AST test (`test_docket.py:
   120-134`) that enforces it; mirror both.
6. `scripts/verify_attestation.py:25` — the `from config.loader import
   get_config` scripts-side pattern.
7. `~/mind-palace-reports/2026-07-19-bp-074-session-handoff-gate.html` —
   the report format's reference instance (read-only; lives outside the repo).

## 3. Investigation & grounding

- **Q1 — where does the exhaust root live in config?** A new top-level
  `[exhaust]` table with `path = "~/.mind-palace/exhaust"`, sibling in spirit
  to `[vault]`'s `path` (`config/defaults.toml:42-46`). Single source of
  truth: the writer and the invariant test both read it via `get_config()`.
- **Q2 — does the loader pass new tables through?** The code likely settles
  this (`config/loader.py` — generic TOML merge vs schema'd sections); the
  builder reads it first. If schema'd, the minimal addition is in-scope only
  if it lives in `config/` — if it requires touching `core/`, STOP and file a
  finding (write_scope excludes `core/**` deliberately).
- **Q3 — how is "no ingest root inside exhaust" testable?** Ingest roots are
  config-pinned (`defaults.toml:46`, `local.toml:12` — the note's §2.1
  grounding). The test loads the merged config, resolves every `path`-bearing
  source entry (`expanduser`, `resolve()`), and asserts none is equal to or
  under the exhaust root. Symlink normalization matters (`/tmp` vs
  `/private/tmp` precedent in the hooks).
- **Q4 — script precedent for no-core tooling?** `scripts/docket.py`
  (bp-072): `config`/stdlib only, plus an AST test asserting the import set
  (`tests/unit/test_docket.py:120-134`). The writer mirrors both the shape
  and the test.
- **Q5 — who creates the on-disk directory?** The writer, `mkdir -p`, at
  first placement — the builder never touches `~/.mind-palace/**` (outside
  the repo; a production-adjacent mutation). Tests use `tmp_path` configs
  only. The real first write is an orchestrator act post-merge.

**Additional risks or questions surfaced during reading:** none — the design
note's grounding (done same-session) covered the layout and roots; Q2 is the
one code-settled question left deliberately to the builder's reading.

## 4. Reconciliation

- `docs/supplemental/cockpit.md` — **cross-ref: extension**: gains an
  owner-side section (pair `~/.mind-palace/exhaust` in SyncTrain; iPhone
  Files-app shortcut to `exhaust/reports/`). Nothing corrected.
- No code or ratified doc is corrected by this plan; the Gmail-draft fallback
  demotion is recorded in agent memory (`phone-build-report`), not a repo
  artifact.

## 5. Write scope

`config/defaults.toml` (the `[exhaust]` table — DONE, merged `9bb4d3b`),
`core/config/loader.py` + `config/loader.py` (the `ExhaustConfig` surface —
WIDENED IN per finding-0115, owner Option A 2026-07-20; the loader is schema'd,
so surfacing `[exhaust]` via `get_config()` requires a core dataclass field, the
same shape as `VaultConfig`), `scripts/exhaust_report.py` (new),
`tests/unit/test_exhaust_report.py` (new — the invariant test and the writer
tests), `docs/supplemental/cockpit.md` (the owner-side section).

The `core/config/loader.py` grant is a NARROW, single-purpose widening: an
`ExhaustConfig` mirroring the existing `VaultConfig` — the config system used as
designed (every section lives there), NOT outsourcing and NOT a trust boundary
(finding-0115 §Options A). Deliberately still OUT: the rest of `core/**`,
`config/local.toml` (owner's machine-local file), `~/.mind-palace/**` (live
data — the builder never writes outside the repo), `.claude/hooks/**`, the
foundation denylist as always.

## 6. Interfaces pinned inline

Config key (Item 1 adds; writer and test read):

```toml
[exhaust]
path = "~/.mind-palace/exhaust"   # system-written, owner-read; NEVER an ingest root
```

Config access pattern — CORRECTED per finding-0115 (the loader returns a frozen
`Config` dataclass, NOT a subscriptable dict; `get_config()["exhaust"]["path"]`
was unimplementable). The real form, after Item 1 adds the `ExhaustConfig` field:

```python
from config.loader import get_config
exhaust_root = get_config().exhaust.path      # .path is already an expanduser'd Path
```

`ExhaustConfig` to add in `core/config/loader.py` (mirror `VaultConfig` exactly):

```python
@dataclass(frozen=True)
class ExhaustConfig:
    path: Path
# on Config:  exhaust: ExhaustConfig
# in load_config():  exhaust=ExhaustConfig(path=Path(raw["exhaust"]["path"]).expanduser())
# re-export the name in the config/loader.py facade + its __all__
```

Writer CLI contract (Item 3):

```
uv run scripts/exhaust_report.py <html-file> --plan bp-NNN --slug <slug>
  -> writes <exhaust>/reports/YYYY-MM-DD-bp-NNN-<slug>.html   (date = today)
  -> mkdir -p on the reports dir; REFUSES silent overwrite (exit 1 if the
     target exists, --force to replace); prints the destination path.
```

The invariant (dn-exhaust-lane §2.2, verbatim): "No configured ingest/source
root may lie inside `~/.mind-palace/exhaust/`, and no core/ingest code path
may read from it."

Report naming: `reports/YYYY-MM-DD-<bp-id>-<slug>.html` (note §2.3). Format:
self-contained theme-aware HTML; the writer PLACES files and never composes
or rewrites content (composition is the orchestrator's, memory
`phone-build-report`).

## 7. Items

### Item 1 — the `[exhaust]` config surface  (data half DONE; code half now in-scope)

- **Status:** the `[exhaust]` table landed in `config/defaults.toml` (merged
  `9bb4d3b`). Remaining: the `ExhaustConfig` surface in the schema'd loader.
- **Objective:** add `ExhaustConfig` to `core/config/loader.py` (mirror
  `VaultConfig`: frozen dataclass, `expanduser()`'d path), the `exhaust` field
  on `Config`, the `load_config()` wiring, and the `config/loader.py` facade
  re-export (+ `__all__`).
- **Files:** `core/config/loader.py`, `config/loader.py`.
- **Acceptance test:** `get_config().exhaust.path` returns the expanduser'd
  pinned path in a test; `[vault]`/every existing section unchanged; the full
  config test suite green.
- **Falsifier:** an existing config field changes meaning or a config test
  reddens (the mirror was not faithful), or `ExhaustConfig` needs anything
  beyond the `VaultConfig` shape (a sign the section is more than a path — stop
  and reconsider).
- **Invariant(s):** no existing config key changes meaning; `[vault]` untouched;
  the widening stays confined to `ExhaustConfig` (the finding-0115 grant is
  single-purpose).
- **Touches stored data?** No.
- **Parallelizable?** No (Items 2/3 read this surface). **Depends on:** none.

### Item 2 — the ingest-invariant test

- **Objective:** the note's §2.2 rule as a permanent unit test.
- **Files:** `tests/unit/test_exhaust_report.py`.
- **Acceptance test:** (a) against the real merged config: every resolved
  source path is outside the exhaust root — passes today; (b) against a
  `tmp_path` config that plants a source *inside* exhaust: the assertion
  logic flags it (the test of the test).
- **Falsifier:** the check cannot enumerate source roots generically (config
  shape too irregular) — file a finding proposing the config restructure;
  do not hand-pin a path list that will drift.
- **Invariant(s):** reads config only; never touches `~/.mind-palace/**`.
- **Touches stored data?** No.
- **Parallelizable?** With Item 3. **Depends on:** Item 1.

### Item 3 — the writer, `scripts/exhaust_report.py`

- **Objective:** the placement tool per the pinned CLI contract.
- **Files:** `scripts/exhaust_report.py`, `tests/unit/test_exhaust_report.py`.
- **Acceptance test:** with a `tmp_path` exhaust root in config: places the
  file at the dated name, creates `reports/`, refuses overwrite without
  `--force`, exits 0/1 correctly; AST test asserts imports ⊆ {stdlib,
  config} — no `core` (docket precedent).
- **Falsifier:** the script needs `core` for anything — wrong altitude; it is
  a placement tool, finding + rethink.
- **Invariant(s):** never composes/edits report content; never writes outside
  the configured exhaust root.
- **Touches stored data?** No (tests tmp-rooted; live dir is created only at
  real first use, post-merge, by the orchestrator).
- **Parallelizable?** With Item 2. **Depends on:** Item 1.

### Item 4 — the owner-side guide (`cockpit.md`)

- **Objective:** the SyncTrain pairing + iPhone Files shortcut section, and
  the note that reports land in `exhaust/reports/`.
- **Files:** `docs/supplemental/cockpit.md`.
- **Acceptance test:** section exists, names the exact share path and the
  writer command; adopt-by-hand framing preserved (nothing auto-applied).
- **Falsifier:** N/A — documentation; the falsifier is the owner failing to
  pair from the instructions, which routes back as feedback.
- **Invariant(s):** guide-not-gate rule text untouched.
- **Touches stored data?** No.
- **Parallelizable?** Yes. **Depends on:** Item 1 (the path it documents).

## 8. Math carried explicitly

N/A — no mathematical object implemented (path containment is `Path.resolve`
prefix checking, not one).

## 9. Non-goals

- No ownership/permission changes (`dn-ouroboros-principal`, separate build).
- No report composition logic — the orchestrator composes; the script places.
- No Syncthing configuration by the builder (owner pairs the share by hand).
- No migration of the bp-074 proof-of-concept file (orchestrator act at first
  real use).
- No pruning/retention, no index.html, no non-report exhaust types (parked in
  the note).

## 10. Stop-and-raise conditions

- Q2 resolves to a `core/`-side loader change → finding, park Item 1.
- The invariant test cannot enumerate source roots generically → finding
  (Item 2 falsifier).
- Any write outside the repo tree would be needed → stop; that is never this
  builder's to do.
- Owner-level question → park with re-entry, continue the rest.

## 11. Parked decisions

| Decision | Default recorded | Rejected alternatives (why) | Re-entry condition |
|---|---|---|---|
| Report retention/pruning | Keep all | Auto-prune (premature; files are small) | Folder unwieldy on phone / sync cost felt (note, parked) |
| Non-report exhaust types | Reports only | Speculative subdirs now (no consumer) | Owner asks to read another artifact class on the phone |
| Rolling index.html | None | Generate per write (complexity, no need) | File-by-file navigation proves annoying in real use |

## 12. Dependency & ordering summary

Item 1 → {Item 2 ∥ Item 3} → Item 4 (documents the landed path; parallel in
practice). Blast radius uniformly low: config key + new script + tests + docs;
no stored data, no live-tree writes. No cross-plan dependencies;
`dn-ouroboros-principal`'s build follows independently and changes nothing
here (the note's §2.5 ownership-agnostic guarantee).
