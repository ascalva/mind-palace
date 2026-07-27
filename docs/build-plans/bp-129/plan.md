---
type: build-plan
id: bp-129
track: erratum-relation
status: proposed
design_ref:
  - docs/design-notes/erratum-relation.md
contract: builder
write_scope:
  - core/stores/errata.py
  - tests/unit/test_errata.py
  - ops/lifecycle/launcher.py
  - tests/integration/test_lifecycle.py
session_budget: 1
cost:
  estimate:
    model: opus
    tokens: 300k
  actual: null
depends_on: []
parallelizable_with: [bp-130]
created: 2026-07-27
updated: 2026-07-27
links:
  - docs/design-notes/chat-sensor.md
  - docs/findings/finding-0168.md
  - docs/findings/finding-0255.md
  - docs/findings/finding-0256.md
  - docs/brainstorms/the-false-success-rule.md
  - docs/brainstorms/the-unchecked-claim.md
re_entry: null
supersedes: null
superseded_by: null
warrant: null
---

# Build Plan — the erratum relation: a warranted, append-only, unary disposition store

## 0. Mode & provenance

Investigation and planning produced this plan; **implementation proceeds item-by-item on
owner approval**. It graduates the **panel-independent** half of `dn-erratum-relation` §5:
*the relation, E1–E8, the composition law*. It deliberately builds **no storage layout that
the `dn-vector-membership-store` panel could invalidate** (§11 PD-A records exactly how).

Authority-to-act (the owner's instruction to graduate this note) is separate from the
readiness blessing (`proposed → ready`), which is the **owner's hand only**. No agent flips
it; `gate-guard` denies pre-hoc and the Stop-gate audit catches a Bash-mediated flip.

## 1. Objective

Make "this record was wrong at write time" a **typed, owner-warranted, append-only, unary
record** that the corpus can hold — honoring E1–E8 — without deciding where it will
ultimately physically live.

## 2. Context manifest

Read these, in order, before any work:

1. `docs/design-notes/erratum-relation.md` — the decision this implements. §3 (the relation
   + E1–E8), §4 (the algebra, for vocabulary only — bp-130 builds it), §9 (parked decisions).
2. `core/stores/authored_supersession.py` — **the precedent to reuse, not re-derive.** The
   owner-capability system (`OwnerDeclaration`, `owner_declaration()`,
   `verify_owner_declaration`) lives here and is declared system-wide-unique at `:86-87`.
3. `core/verdict/dispositions.py` — the append-only, latest-wins-by-subject disposition
   idiom (E2/E5) and the `retracted()` active-projection filter shape.
4. `core/stores/chatlog.py` — the first customer's surface; its `PRIMARY KEY (session_id,
   turn_index)` at `:90` is the coordinate shape targets will carry.
5. `ops/lifecycle/launcher.py:1325-1370` — `reset_targets()`, and the recorded rationale for
   why owner-declared sidecars are corpus-side wipe targets.
6. `tests/integration/test_lifecycle.py:265-292` — the reset test whose `sidecars` list Item 3
   extends.
7. `docs/brainstorms/the-false-success-rule.md` — the degenerate-input discipline Item 2 applies.

**DRY audit — does `core/` already implement this? (required; CONVENTIONS §Language & style).**
Audited before authoring:

- **Owner capability** — **YES, and it MUST be reused.** `core/stores/authored_supersession.py:80`
  `verify_owner_declaration(declaration)`. Its own docstring at `:86-87` reads: *"There is ONE
  owner-capability system-wide and it lives here."* Minting a second owner token in `errata.py`
  is a **defect**, not a style choice. Import and call it.
- **Append-only + latest-wins ledger** — `core/verdict/dispositions.py:101` `retracted()`
  implements exactly the "latest seq wins per subject, collect the ones in state X" fold. The
  erratum's `targets_for()` is the same fold over a different key; **follow the idiom, do not
  invent a second one.**
- **An erratum record / `Ε` projection / `current_any`** — **NO. Nothing exists.** Verified by
  repo-wide search: the only `erratum` string in `core/` is `core/graph/conductance.py:60,362,378`,
  referring to an unrelated proper-time-exactness finding erratum. `current_any` appears nowhere
  in code (only at `erratum-relation.md:231`, as an open question). This is genuinely new.
- **Supersession stores** — `core/stores/versions.py`, `core/stores/claim_ops.py`,
  `core/stores/authored_supersession.py` all exist and all express *replacement*. **None
  expresses falsity-at-write-time** (the note's §2 table is correct on this point, re-derived).

## 3. Investigation & grounding

- **Q1 — Does an owner-capability primitive already exist, and is a second one permissible?**
  It exists and a second is **forbidden**. `core/stores/authored_supersession.py:80`
  `verify_owner_declaration`; the docstring at `:86-87` states it is the one system-wide owner
  capability, factored out of `record()` precisely so a second boundary (the `doc_id` re-key
  primitives, bp-034) could reuse it rather than mint another. The check verifies **token
  identity**, not just `isinstance` — `getattr(declaration, "_token", None) is _OWNER_TOKEN` at
  `:91-92` — defending against `object.__new__(OwnerDeclaration)`. **Reuse verbatim.**

- **Q2 — What does an append-only, latest-wins fold look like here?**
  `core/verdict/dispositions.py:104-109`: read all rows `ORDER BY verdict_seq`, overwrite into a
  dict keyed by subject, then filter by effect. Later seq wins by construction of the iteration
  order. E5 ("an erratum can itself be marked erroneous") is the same fold with the erratum's own
  `seq` as the subject key.

- **Q3 — Is `INSERT OR REPLACE` compatible with append-only (E2)?**
  Only where the key is the *event's own* identity. `dispositions.py:86` uses
  `INSERT OR REPLACE` keyed on `verdict_seq` — re-applying the **same** verdict is idempotent, it
  never rewrites a *different* event. `authored_supersession.py:161` does the same on the
  `(superseded, superseding)` pair. For errata the event identity is an autoincrement `seq`, so a
  new assertion is always a new row: **plain `INSERT`, never `REPLACE`.** E2 is stronger here
  than in the precedents, and deliberately so.

- **Q4 — Is `reset_targets()` the right home, and is an owner-declared store a reset target?**
  Yes, on precedent. `ops/lifecycle/launcher.py:1336` lists `authored_supersessions.sqlite` —
  itself owner-declared — with the recorded rationale at `:1333-1335`: *"All four are
  corpus/derived-chain provenance: left behind, their rows reference wiped artifacts — orphaned
  history that would pollute a fresh graph's record."* That rationale applies to errata verbatim:
  an erratum's targets are chat/corpus coordinates that a reset wipes. **The code settles this by
  precedent, not by rule** — see §11 PD-B for the residual doubt and its re-entry condition.

- **Q5 — Will adding an entry to `reset_targets()` redden an existing test?**
  **No, but a test must still be extended.** `tests/unit/test_code_sensor.py:178` and
  `tests/unit/test_self_sensor.py:428` both build `names = {t.name for t in
  launcher.reset_targets()}` and assert **membership**, not set equality — adding an entry is
  invisible to them. `tests/integration/test_lifecycle.py:275-277` seeds an explicit `sidecars`
  list and asserts all are wiped; adding to `reset_targets()` without adding to that list leaves
  the new store **untested on the wipe path**. That is why `tests/integration/test_lifecycle.py`
  is pre-widened into `write_scope` (§5).

- **Q6 — What is the target-coordinate grammar for the chat surface?**
  `core/stores/chatlog.py:90` — `PRIMARY KEY (session_id, turn_index)`. A target key is therefore
  a serialization of that pair. **The code does not settle the serialization format**; this plan
  pins one (§6) as an opaque `TEXT` chosen by the *caller*, so the store never parses a coordinate
  and stays surface-agnostic. That is what keeps it panel-independent.

- **Q7 — Does the note's §5 claim about φ_chat's role mapping hold against the code?**
  **NO — the note is imprecise, and it matters.** `erratum-relation.md:204-205` says *"φ_chat
  1.0.0 mapped `message.role: user` → `speaker='owner'`"*. The code at
  `ops/chat_sensor.py:124` reads `_ROLE_TO_SPEAKER.get(str(record.get("type", "")))` — the
  **top-level record `type`**, not `message.role`. Filed as **finding-0255**. It does not
  affect this plan (which never touches φ_chat), but it would mislead the builder of the
  re-projection half, so it is recorded now. See §4.

**Additional risks or questions surfaced during reading:**

- ⚑ **The mis-attribution class is BROADER than the 139** (finding-0256). Re-deriving the census
  read-only, I found **141** owner rows containing `Stop hook feedback`, of which **139** *begin*
  with it. The other **2** are the `update-config` skill's own documentation text
  (`# Update Config Skill / Modify Claude Code configuration by updating settings.json files.`),
  injected into a user-role record — machine text attributed to the owner, from a channel A1.2's
  closed enumeration does **not** list. This plan is unaffected (it enumerates nothing), but it is
  direct evidence for **PD-1**: a *predicate* would have swept those 2 in; an *enumeration* cannot.
- The seat's readings pane records the broader match as **146**; my re-derivation says **141**.
  The figure does not reproduce (finding-0256).

## 4. Reconciliation

- `docs/design-notes/erratum-relation.md:204-205` — *"φ_chat 1.0.0 mapped `message.role: user` →
  `speaker='owner'` (`ops/chat_sensor.py`, `_ROLE_TO_SPEAKER`)"* → **[banner: correction]**. The
  note is **ratified and therefore agent-immutable** — no diff is proposed against the file. The
  correction is carried by **finding-0255** (`route: orchestrator`, needing the owner's hand for
  any amendment), and this plan's §3 Q7 records the ground truth so no builder in this wave
  inherits the error. *No code change in this plan follows from it.*

- `core/stores/errata.py` (new) — **[cross-ref: extension]**. The new module's header comment must
  cross-reference the three relations it sits beside and state what it adds, so a later reader
  cannot mistake it for a fourth supersession store:
  ```
  # Distinct from the three SUPERSESSION carriers — versions.py (one doc_id's versions),
  # claim_ops.py (interpreted claims), authored_supersession.py (K₀↔K₀ documents). Each of
  # those asserts REPLACEMENT ("true in its time"). This one asserts FALSITY AT WRITE TIME
  # ("there is no moment at which it was right") — dn-erratum-relation §2. Composition, not
  # substitution: correction(r) = supersession(r → r′) ∧ erratum(r).
  ```

- `ops/lifecycle/launcher.py:1332-1335` — the sidecar block comment reads *"All four are
  corpus/derived-chain provenance…"* → **[banner: correction]**. Item 3 adds a fifth entry, so
  the literal word "four" becomes wrong. The comment must be updated in the same edit, and the
  erratum's own rationale appended. Not a silent count bump: the added line carries its reason.

## 5. Write scope

- `core/stores/errata.py` — **the deliverable.** New module: the `Erratum` record, `ErratumAuthority`,
  `ErrataStore`, `open_errata_store`.
- `tests/unit/test_errata.py` — **new.** E1–E8 pinned as executable tests, plus the mutation campaign.
- `ops/lifecycle/launcher.py` — **carried for Item 3 only**: one `reset_targets()` entry plus the
  block-comment correction (§4). No other edit to this file is in scope.
- `tests/integration/test_lifecycle.py` — **carried because it pins the surface Item 3 moves**
  (§3 Q5): its `sidecars` list at `:275-277` must gain `errata.sqlite` or the new store's wipe
  behavior is asserted nowhere.

**Deliberately OUT of scope:** `core/stores/chatlog.py` (bp-131 owns the read path);
`core/kernel/temporal/**` (bp-130 owns the algebra); `ops/chat_sensor.py` (φ_chat 2.0.0 is
parked — §11 PD-C); every design note (`docs/design-notes/**` — ratified notes are
agent-immutable); the foundation denylist (`CONSTITUTION.md`, `eval/golden/**`, `eval/golden.py`).
⚑ **No write to any live store under `data/`.** Every test uses `:memory:` or `tmp_path`.

## 6. Interfaces pinned inline

**The owner capability — import, never re-derive** (`core/stores/authored_supersession.py:55-97`,
copied verbatim):

```python
class MachineAuthorityRefused(PermissionError): ...

@dataclass(frozen=True)
class OwnerDeclaration:
    _token: object = None
    def __post_init__(self) -> None:
        if self._token is not _OWNER_TOKEN:
            raise MachineAuthorityRefused(...)

def owner_declaration() -> OwnerDeclaration:      # mints the capability
def verify_owner_declaration(declaration: object) -> None:   # raises MachineAuthorityRefused
```

**The erratum record** (`dn-erratum-relation` §3, verbatim):
`erratum = (targets, authority, warrant, evidence, asserted_at_seq)`

**The schema this plan pins** — deliberately *surface-agnostic*: the store never parses a
target key, so no storage-layout decision about the chat lane is embedded here (§11 PD-A):

```sql
CREATE TABLE IF NOT EXISTS errata (
    seq       INTEGER PRIMARY KEY AUTOINCREMENT,  -- asserted_at_seq: this erratum's own
                                                  -- position in the belief order (§3)
    surface   TEXT NOT NULL,   -- the corpus surface the targets live on, e.g. 'chat_utterances'.
                               -- OPAQUE to this store: never parsed, never joined here.
    authority TEXT NOT NULL,   -- owner-hand | owner-verdict | ratified-amendment
    warrant   TEXT NOT NULL,   -- the artifact carrying the reasoning (oq-/finding/amendment ref)
    evidence  TEXT NOT NULL DEFAULT '',  -- the GENERATING PREDICATE + census method.
                               -- ⚑ PD-1: recorded as evidence, NEVER re-evaluated as a target.
    at        TEXT NOT NULL,   -- wall clock, audit only — never an ordering key (Law C4)
    note      TEXT NOT NULL DEFAULT ''
);
CREATE TABLE IF NOT EXISTS erratum_targets (
    seq        INTEGER NOT NULL,   -- the asserting erratum
    target_key TEXT NOT NULL,      -- ONE enumerated coordinate/digest, opaque TEXT
    PRIMARY KEY (seq, target_key)
);
CREATE INDEX IF NOT EXISTS erratum_targets_key ON erratum_targets(target_key);
```

**The API this plan pins:**

```python
class ErratumAuthority(StrEnum):
    OWNER_HAND         = "owner-hand"
    OWNER_VERDICT      = "owner-verdict"
    RATIFIED_AMENDMENT = "ratified-amendment"

@dataclass(frozen=True)
class Erratum:
    seq: int
    surface: str
    authority: ErratumAuthority
    warrant: str
    evidence: str
    at: str
    targets: tuple[str, ...]
    note: str = ""

@dataclass
class ErrataStore:
    path: Path

    def assert_erratum(self, *, surface: str, targets: Iterable[str],
                       authority: ErratumAuthority, warrant: str,
                       declaration: OwnerDeclaration, evidence: str = "",
                       note: str = "") -> Erratum:
        """Append ONE erratum over an ENUMERATED target set (PD-1). Requires owner authority,
        VERIFIED at this boundary via verify_owner_declaration (E1). Plain INSERT — never
        REPLACE: a re-assertion is a NEW erratum at a higher seq (E2/E5). Empty `targets`
        is a ValueError: an erratum asserting falsity about nothing is meaningless."""

    def targets_for(self, surface: str) -> set[str]:
        """The VALIDITY filter (E3): every target key on `surface` currently asserted false,
        net of iterated errata (E5). Transport-invariant — takes NO cut argument, by design:
        erratum status acts at EVERY cut, including cuts before its assertion."""

    def targets_as_of(self, surface: str, seq: int) -> set[str]:
        """The BELIEF filter: targets asserted false by errata with seq <= `seq` — the ledger
        slice. Used to let a belief query self-annotate; NEVER used to exclude rows."""

    def erratum_for(self, surface: str, target_key: str) -> Erratum | None:
    def all(self) -> list[Erratum]:
    def count(self) -> int:
    def close(self) -> None:

def open_errata_store(config: Config | None = None) -> ErrataStore:
    """`data/errata.sqlite` — the sibling-store convention
    (`cfg.paths.derived_store.parent / "errata.sqlite"`, as dispositions/authored_supersessions)."""
```

**E5, made concrete.** An erratum is marked erroneous by a *later erratum whose `surface` is
`'errata'` and whose `target_key` is the earlier erratum's `seq`*. `targets_for()` must therefore
first compute the set of retracted erratum seqs (`targets_for('errata')`), then exclude those
errata's contributions. This is one self-referential fold, not a second mechanism.

**Reset-target line to add** (`ops/lifecycle/launcher.py`, inside the sidecar block):
```python
p.data_dir / "errata.sqlite",   # owner-warranted errata over corpus coordinates: their
                                # target keys reference wiped rows, so they orphan on reset
```

## 7. Items

### Item 1 — the erratum store module

- **Objective:** `core/stores/errata.py` exists and implements the §6 schema and API, honoring
  E1–E8 by construction.
- **Files:** `core/stores/errata.py` (new).
- **Acceptance test:** `uv run python -c "from core.stores.errata import ErrataStore,
  ErratumAuthority, open_errata_store"` exits 0; `uv run mypy core agents eval ops scheduler
  scripts` reports **Success: no issues** (the floor stays 0); `uv run python
  scripts/check_imports.py` exits 0 (the module imports nothing outside `core/` but stdlib).
- **Falsifier:** the module defines its own owner-token / `OwnerDeclaration` / capability check
  instead of importing `verify_owner_declaration` from
  `core/stores/authored_supersession.py`. That is a **second owner-capability system-wide**,
  which the precedent's own docstring forbids — and it would mean E1 is enforced by a copy that
  can drift. Grep the delivered file for `_OWNER_TOKEN`, `object()`, and a locally-defined
  `class OwnerDeclaration`: any hit falsifies the item.
- **Invariant(s) it must not violate:** E1 (warranted or unrepresentable) · E2 (append-only —
  the module contains **no** `UPDATE` and **no** `DELETE` SQL) · E7 (disjoint from purge — the
  module exposes **no** delete/purge/forget method) · core self-containment (imports only
  stdlib + `core.*`).
- **Touches stored data?** **No.** New table in a new file; no live store opened. Tests use
  `:memory:`/`tmp_path`.
- **Parallelizable?** No (Item 2 depends on it).  **Depends on:** none.

### Item 2 — E1–E8 pinned as executable tests, with a mutation campaign

- **Objective:** every invariant E1–E8 that this store can carry is asserted by a test that
  **reddens when the invariant is removed** — not merely by a passing test.
- **Files:** `tests/unit/test_errata.py` (new).
- **Acceptance test:** `uv run pytest tests/unit/test_errata.py -q` is green, and covers at least:
  - **E1 ×4:** `assert_erratum(declaration=None)`, `declaration=object()`,
    `declaration=object.__new__(OwnerDeclaration)` (the bypass-construction vector), and a
    directly-constructed `OwnerDeclaration()` — **all four raise `MachineAuthorityRefused`**;
    `owner_declaration()` succeeds.
  - **E2:** two `assert_erratum` calls over the same target yield **two rows at two seqs**; the
    first erratum is byte-identical before and after the second.
  - **E5:** an erratum over `surface='errata'` targeting erratum #1's seq removes #1's
    contribution from `targets_for(...)`, and a third erratum retracting *that* one restores it.
  - **E3:** `targets_for()` accepts no cut argument and returns the same set regardless of any
    `seq` in the store — asserted by signature inspection **and** by value.
  - **E7:** `dir(ErrataStore)` contains no name matching `delete|purge|forget|remove|drop`.
  - **PD-1:** `assert_erratum(targets=[])` raises `ValueError`.
  - ⚑ **The degenerate-input check (the false-success rule).** The named degenerate input for
    *this* plan is **an erratum store whose authority check is vacuous** — every test passes, an
    erratum can be asserted, and nothing anywhere is warranted. The check must **redden** on it.
- **Falsifier:** ⚑ **the mutation campaign is the falsifier, and it must be RUN, not reasoned
  about** (finding-0249: both surviving mutants in the last wave were found by mutating and
  running, neither by reading). Apply each mutant to `core/stores/errata.py`, run
  `tests/unit/test_errata.py`, record the verdict, revert:
  1. delete the `verify_owner_declaration(declaration)` call from `assert_erratum`;
  2. weaken it to `isinstance(declaration, OwnerDeclaration)` only (drops the token-identity
     check — the `object.__new__` bypass);
  3. change the plain `INSERT` to `INSERT OR REPLACE` on a fixed key (breaks E2);
  4. make `targets_for` ignore the `surface='errata'` self-retraction fold (breaks E5);
  5. give `targets_for` a `cut` parameter that filters `seq <= cut` (breaks E3 — this is
     precisely the marker-on-edge model the note's §3 argues against).
  **Every mutant must be CAUGHT.** A survivor is a vacuous test and must be strengthened
  before the item closes; record each verdict in `journal.md`.
- **Invariant(s) it must not violate:** no test opens a path under `data/`; the argless
  `uv run mypy` tail must still equal the pinned tests/ baseline (**69**) — a new tests file can
  shift it, and a shifted count is this item's problem to fix, not a pre-existing failure.
- **Touches stored data?** **No.**
- **Parallelizable?** No.  **Depends on:** Item 1.

### Item 3 — the store joins the corpus reset contract

- **Objective:** `errata.sqlite` is wiped with the corpus, so an erratum can never outlive the
  rows whose coordinates it names.
- **Files:** `ops/lifecycle/launcher.py`, `tests/integration/test_lifecycle.py`.
- **Acceptance test:** `errata.sqlite` appears in `{t.name for t in launcher.reset_targets()}`;
  `tests/integration/test_lifecycle.py`'s `sidecars` list includes `errata.sqlite` and
  `uv run pytest tests/integration/test_lifecycle.py -q` is green (the seeded file is created
  before the wipe and absent after); the `:1332-1335` block comment no longer says "four" (§4).
- **Falsifier:** the Vault Raft assertion in
  `test_reset_wipes_corpus_but_never_the_vault_raft` fails, or `reset_targets()`'s internal
  assertion that every target is under `data/` and outside the guard set trips. Either means the
  new entry was added at the wrong layer and reset has been widened beyond the corpus — a
  blast-radius regression far worse than the missing entry.
- **Invariant(s) it must not violate:** the Vault Raft is never a reset target; the raw archive
  is never a reset target (`data/raw/` is sacred — the re-projection half depends on it,
  and all 92 transcript digests behind the 139 rows were verified present there).
- **Touches stored data?** **No** in test (`tmp_path`). ⚑ **The builder must NOT run
  `launcher.reset(confirm=True)` against the real config** — that would wipe the live corpus.
  Tests only, `tmp_path` only.
- **Parallelizable?** No.  **Depends on:** Item 1.

## 8. Math carried explicitly

- **The erratum relation (a unary dispositional relation)** — *measures:* which records the
  corpus asserts had **empty validity** — no moment at which they were true — as distinct from
  records that were true and got replaced. *valid when:* every assertion carries verified owner
  authority (E1), targets are enumerated rather than predicated (PD-1), and the relation is
  node-anchored rather than edge-anchored (the note's §3 arity argument — a retraction has no
  successor, so an edge has nowhere to attach). *fails its keep if:* a legitimate correction is
  exhibited whose target has a **non-empty** validity interval — "true until t, with t before its
  supersession". That is the note's §7 falsifier (ii), and it would mean the marker-on-edge model
  was right and this store's arity wrong. None of the six measured instances in
  `the-unchecked-claim` has this shape (all were false at birth), but the refutation is recorded
  so it can be recognized rather than rationalized.

- **`Ε`'s support set** — *measures:* `targets_for(surface)` is the support of the diagonal
  projection `Ε` that bp-130 builds; this plan supplies the **set**, bp-130 supplies the
  **operator**. *valid when:* the set is transport-invariant, i.e. computed with no cut argument
  (E3). *fails its keep if:* `targets_for` ever needs a cut parameter to give a useful answer —
  that would falsify transport-invariance, and with it the note's central claim that
  erratum-ness is a node property rather than a transition.

## 9. Non-goals

- **No decision about the erratum's physical home** beyond "a sibling SQLite store, keys opaque".
  PD-2 in the note is panel-dependent and stays parked (§11 PD-A).
- **No change to `core/stores/chatlog.py`** — the read path is bp-131.
- **No `(I − Ε)` operator** — the algebra is bp-130.
- **No φ_chat 2.0.0, no re-projection, no widened PK, no back-correction of the 139 rows.**
  Explicitly a non-goal of the design note itself (§1.2) and triply blocked (§11 PD-C).
- **No erratum asserted against any live store.** This plan builds the capability; firing it is
  the owner's act (§8 of the note).
- **No store-level erratum targeting a ratified design note** (PD-4: the owner-hand amendment
  gate is that carrier, permanently).
- **No purge, delete, or byte-removal capability of any kind** (E7).

## 10. Stop-and-raise conditions

- **`verify_owner_declaration` cannot be imported from `core/stores/authored_supersession.py`**
  without creating a cycle or violating the import firewall → **stop and file a finding.** Do
  **not** resolve it by copying the capability; a second owner token is the one outcome this plan
  forbids outright.
- **A mutant survives the campaign after strengthening** → record it in `journal.md` as an
  **equivalent mutant with an argument for why**, or file a finding. Never silently accept a
  survivor (finding-0249).
- **The argless `uv run mypy` count moves off 69** in a way the new test file does not explain →
  stop, report the delta, do not "fix" the baseline.
- **The reset-target semantics feel wrong** (an erratum that should survive a corpus wipe) →
  that is an owner-level design question. **Park Item 3 with the §11 PD-B re-entry condition and
  close Items 1–2** — never block the plan on it.
- **Any instinct to touch `data/`, run ingestion, start/stop the daemon, or `deploy`** → stop.
  None is in scope; the queue is wedged and `deploy` is the owner's alone.

## 11. Parked decisions

| Decision | Default recorded | Rejected alternatives (why) | Re-entry condition |
|---|---|---|---|
| **PD-A — the erratum's physical home** (note PD-2) | A standalone sibling SQLite store with **opaque, unparsed** target keys. This is the panel-neutral choice: it commits to no row model, so a later fold into a corpus-wide table beside `memberships` is a migration, not a redesign. | *A table inside `chatlog.sqlite`* — rejected: binds the relation to one surface and pre-decides the widened-PK question. *A column on `chat_utterances`* — rejected: that is the row-flag model, which is exactly what the panel owns, and it makes E5 (errata over errata) unrepresentable. | `dn-vector-membership-store` reaches `ratified`. It is currently `draft` and returned from a three-seat adversarial panel as **BLOCK · BLOCK · RATIFY-WITH-AMENDMENTS** (three thesis-level defects: path-in-content-hash making cross-file dedup unreachable; revert corrupting the current-view; `commit_diffs` asserted "already captured" while zero tables exist live). |
| **PD-B — is an erratum corpus-side (wiped) or owner-side (sacred)?** | **Corpus-side**, a reset target — following `authored_supersessions.sqlite`, itself owner-declared and itself wiped (`launcher.py:1336`), for the recorded reason that orphaned rows pollute a fresh graph. | *Sacred, survives reset* — rejected as the default only because no precedent supports it: **every** owner-declared sidecar in the list is currently wiped. The argument for it is real (an erratum is an owner's assertion about truth, not derived data), which is why this is parked rather than settled. | The owner rules on whether owner-warranted assertions survive `reset --confirm`. Until then the precedent governs. |
| **PD-C — φ_chat 2.0.0, the widened identity, and the 139-row back-correction** | **Not in this wave at all.** | *Do it now* — rejected on **three independent blocks**, any one sufficient: (1) the note's own §1.2 declares it a non-goal — *"NOT a build, a re-ingestion, or a back-correction of the 139 rows"*; (2) the identity widening is panel-dependent (widened PK vs membership fibers); (3) the ingestion queue is **wedged** — 1,766 jobs queued, one `code_sync` job stuck `running` since 2026-07-25T03:45, nothing finished since — so any acceptance depending on ingestion completing **cannot pass today**. | All three clear: the note's sequencing fence lifts (the live wave seals), the membership panel ratifies, **and** the queue drains. The rawstore side is already proven ready: all **92** transcript digests behind the 139 rows resolve to files under `data/raw/`, verified read-only. |
| **PD-D — target-key serialization format** | Caller's choice; the store treats keys as opaque `TEXT` and never parses them. | *A structured/typed coordinate column set* — rejected: it would force this store to know each surface's identity shape, which is precisely the panel-dependent question, and would make the store un-reusable across surfaces (§6 of the note wants one relation, many carriers). | A second surface adopts errata and the two key grammars are found to need machine comparison. |

## 12. Dependency & ordering summary

**Within this plan** — strictly serial, ordered by blast radius:

```
Item 1 (new module, greenfield, no existing code)     ← lowest radius
   └─> Item 2 (new tests + mutation campaign)
   └─> Item 3 (edits ops/lifecycle/launcher.py + an existing integration test)  ← highest radius
```

Item 3 is last deliberately: it is the only item that modifies committed, live-path code, and it
is the only one a stop-and-raise can defer (§10, §11 PD-B) without stranding the plan — Items 1–2
stand alone and deliver the relation.

**Across plans:**
- `parallelizable_with: [bp-130]` — bp-130 writes only `core/kernel/temporal/**` and its own test
  file. **Disjoint from this plan's four globs; verified, not assumed.**
- **bp-131 `depends_on: [bp-129]`** — it consumes `ErrataStore.targets_for()` to make the chat
  lane's default view honor errata. It must not start until this plan's Item 1 is merged.
- Nothing here depends on bp-127 or bp-128 (a different sub-orchestrator's live wave); write
  scopes are disjoint — that wave holds `.claude/hooks/**`, which this plan never touches.
