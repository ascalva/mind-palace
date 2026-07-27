---
type: build-plan
id: bp-131
track: erratum-relation
status: proposed
design_ref:
  - docs/design-notes/erratum-relation.md
contract: builder
write_scope:
  - core/chat_validity_view.py
  - tests/unit/test_chat_validity_view.py
  - core/kernel/rings.py
  - tests/unit/test_inner_ring.py
session_budget: 1
cost:
  estimate:
    model: opus
    tokens: 260k
  actual: null
depends_on: [bp-129]
parallelizable_with: [bp-130]
created: 2026-07-27
updated: 2026-07-27
links:
  - docs/design-notes/chat-sensor.md
  - docs/findings/finding-0256.md
  - docs/brainstorms/the-false-success-rule.md
re_entry: null
supersedes: null
superseded_by: null
warrant: null
---

# Build Plan — the chat lane's belief/validity split, and the E8 tripwire

## 0. Mode & provenance

Investigation and planning produced this plan; **implementation proceeds item-by-item on
owner approval**. It graduates the **panel-independent** chat semantics of
`dn-erratum-relation` §5 — *"the belief/validity query split"* and *"the chat semantics"* —
and it is the plan that carries the note's **own named degenerate input** (§7) as its
central criterion.

⚑ **This plan performs no correction.** It builds the read discipline and an executable
**tripwire** that measures how far the live tree is from honoring E8. It asserts no erratum
against any live store, and it re-projects nothing. The three-census check runs against a
**fixture** that replicates the 139-row shape — never `data/chatlog.sqlite`.

Authority-to-act is separate from the readiness blessing (`proposed → ready`), which is the
**owner's hand only**.

## 1. Objective

Give the chat lane a **validity view that structurally cannot serve an erratum-targeted row**,
alongside an explicitly-named belief query that returns those rows flagged — and measure, as a
test, how many live consumers still bypass it.

## 2. Context manifest

Read these, in order, before any work:

1. `docs/design-notes/erratum-relation.md` — §3 (E8, the pairing rule), §4 (the two forensic
   queries: belief vs validity), §5 (the concrete instance), **§7 (the degenerate input — this
   plan's spine)**.
2. `docs/brainstorms/the-false-success-rule.md` — the discipline §7 applies to itself. Read
   before writing acceptance.
3. `core/stores/chatlog.py` — the surface being viewed. `all_rows` `:171-184`, `rows_for`
   `:185-190`, `sessions` `:196`, `PRIMARY KEY (session_id, turn_index)` `:90`.
4. `core/dreams_view.py:29-75` — **the view-composition precedent to follow** (`ArtifactReads` /
   `RetractedReads` Protocols; `DreamsView.over(store, dispositions=…)`; the bound-read-callables
   shape with no mutator on the surface). ⚑ Follow its *shape*; **reject its optional-filter
   default** — §3 Q3 explains why E8 forbids it.
5. `core/sensing.py:186-215` — `ObservedView`, the fail-closed `__post_init__` re-check idiom
   (a view that raises rather than silently admitting a wrong-class row).
6. `core/stores/errata.py` — **bp-129's deliverable**: `ErrataStore.targets_for(surface)` (the
   validity filter) and `targets_as_of(surface, seq)` (the belief filter).

**DRY audit — does `core/` already implement this? (required).** Audited before authoring:

- **A read-only view composing a source with an exclusion filter** — **YES: `core/dreams_view.py:44`
  `DreamsView`.** It binds `store.all`/`store.count` as callables and takes an optional
  `retracted()` source, dropping retracted subjects from what it surfaces. `ChatValidityView` is
  the **same construction** over a different pair, and must reuse the Protocol + bound-callable
  idiom rather than invent a second view style.
- **A fail-closed view constructor** — **YES: `core/sensing.py:190` `ObservedView`**, whose
  `__post_init__` raises when offered a wrong-class row. The E8 constructor check (§7 Item 1)
  is that idiom applied to a missing filter instead of a wrong row.
- **A census/count helper over chat rows** — **NO.** `ChatlogStore.count()` (`:192`) counts all
  rows and takes no predicate. The three-census check needs a predicate; it belongs in the view,
  not as a second store method.
- **Any existing belief/validity distinction on any read path** — **NO.** Verified: nothing in
  `core/` distinguishes "what was believed" from "what was true". This is genuinely new.

## 3. Investigation & grounding

- **Q1 — What do the chat reads filter on today?**
  **Provenance and nothing else** — the note's §7 claim, re-derived. `core/stores/chatlog.py:177-183`:
  `all_rows` runs `SELECT * FROM chat_utterances ORDER BY session_id, turn_index` and then filters
  only by `r["provenance"] in allowed`. Since *every* stored row is `observed`
  (`to_row()` hardcodes it, `:130`), that filter is a no-op in practice — the docstring at
  `:174-176` says so outright: *"a filter containing OBSERVED sees ALL rows and any filter
  excluding it sees NONE — there is no third case."* `rows_for` (`:185-190`) filters on
  `session_id` only. **⇒ There is no mechanism by which an erratum could affect any chat read.**

- **Q2 — Who actually consumes these reads? (the degenerate input, made concrete)**
  **Two live consumers, both unfiltered:**
  - `core/chat_events.py:205,208` — `self.chatlog.sessions()` then `self.chatlog.rows_for(session_id)`;
  - `core/temporal/spine.py:434` — `for row in store.all_rows():`.
  Both bypass any possible erratum. This *is* §7's *"an erratum lands and every consumer keeps
  reading the old rows"*, verified rather than assumed. ⚑ Migrating them is **bp-132**, not this
  plan (blast radius — §12); this plan makes the gap **measurable** so it cannot be silently shipped.

- **Q3 — Can this follow `DreamsView`'s optional-filter default?**
  **No, and this is the load-bearing design point.** `core/dreams_view.py:52-55` documents its
  default: *"None = no verdict layer wired → surfaces every dream"*, and `over()` at `:62-63`
  says omitting it *"keep[s] the prior behavior byte-identical."* That is a sound choice for an
  opt-in active projection. **E8 forbids it here**: *"the default view may never keep serving a
  record its own store asserts was never true."* A `None`-defaulted filter means the **default
  construction is the E8 violation** — the degenerate input shipped as the API's happy path.
  ⇒ The erratum source is **required**, and the unfiltered read is **not reachable by default** —
  it must be asked for by a differently-named method (§6). Follow the shape, reject the default.

- **Q4 — What are the three censuses of §7, precisely?**
  From `erratum-relation.md:258-261`, verbatim: *"(a) the default view's census of
  `speaker='owner' ∧ 'Stop hook feedback:%'` = 0; (b) the validity query at any pre-correction cut
  also = 0; (c) the belief query at such a cut = 139, every one flagged. A green (a) with a red (b)
  or (c) is the false success, named."* All three must be asserted; (a) alone is the false success.

- **Q5 — Can (a)=0 be reached without the parked re-projection?**
  **Yes, and legitimately.** The note's §3 states: *"Erratum without replacement = retraction"* —
  a correction with no corrected content, which is exactly the RETRACT shape. For a retraction,
  exclusion **is** the complete answer; no v2 row need exist. The re-projection (φ_chat 2.0.0)
  would additionally *supply corrected rows*, which is parked (bp-129 §11 PD-C, triply blocked).
  ⇒ This plan targets the retraction semantics, which are fully buildable today.

- **Q6 — What is the target-key grammar for a chat row?**
  `core/stores/chatlog.py:90` — `PRIMARY KEY (session_id, turn_index)`. bp-129 pins target keys as
  **opaque `TEXT`, never parsed by the store** (its §6/PD-D). ⇒ This view owns the chat lane's
  serialization and must keep it in **one** private helper so the format has a single definition
  (§6). **The code does not settle the format**; this plan pins `f"{session_id}:{turn_index}"`
  and states the collision caveat in §6.

- **Q7 — Is the 139 figure sound as a fixture target?**
  Re-derived read-only, this session: `speaker='owner' AND text LIKE 'Stop hook feedback:%'` =
  **139**, across **33** distinct sessions, `interpreter` uniformly `1.0.0`, `observed_at`
  2026-07-18…07-25, over 9,145 total utterances. Sampled rows are genuine hook output
  (`Stop hook feedback: [bash ".../journal-gate.sh"]: (b) foundation files modified: [...]`).
  ⇒ The A2 figure holds. **But see the risk below.**

- **Q8 — ⚑ Will a new `core/` module redden the inner-ring fixed-point test?**
  **It can, and this is the plan's one non-obvious gate.** `tests/unit/test_inner_ring.py:170-190`
  computes the maximal import-closed subset of `core/` by `rglob("*.py")` and asserts
  `computed == INNER` in **BOTH directions**, with the explicit rule:
  *"A module that becomes pure enters the computed set → red until the map adds it (a promotion).
  Every membership change is thereby forced to be an explicit `core/rings.py` diff."*
  A `ChatValidityView` written with only `typing`/`dataclasses`/`collections.abc` and duck-typed
  Protocols would import **nothing outer**, compute as inner-ring, and **redden the test** until
  `core/kernel/rings.py` declares it.
  ⇒ **Pinned resolution: this module is OUTER, and must import an outer symbol to be so.** That is
  not a workaround — it matches the precedent exactly: `core/dreams_view.py:26` imports
  `from core.stores.derived import DREAM, FINDING, Artifact` while still using Protocols for its
  bound reads, and is outer by that import. `core/chat_validity_view.py` should likewise import its
  concrete companion types from `core.stores.chatlog` / `core.stores.errata` for typing, keeping
  the Protocols for the bound callables. **Verified:** `core/kernel/rings.py:80-105` lists
  `core.stores` only as an outer "residue" marker, so neither `core/stores/errata.py` (bp-129, which
  imports `core.stores.authored_supersession`) nor this module is inner **provided** the outer
  import is present.

**Additional risks or questions surfaced during reading:**

- ⚑ **The mis-attribution class is broader than the 139 (finding-0256).** The substring match
  (`text LIKE '%Stop hook feedback%'`) returns **141**, not the **146** the seat's readings pane
  records — the pane's figure **does not reproduce**. The 2 extra rows are the `update-config`
  skill's own documentation text injected into a user-role record — machine text attributed to
  the owner, arriving on a channel that A1.2's *closed* enumeration (ordinary turn / queued
  prompt / structured answer) does not list. **This is direct evidence for PD-1**: a predicate
  would have swept those 2 in; an enumeration cannot. It also means A1.2's closure claim is
  incomplete — routed to the owner, not resolved here.
- The fixture must therefore **enumerate** its targets, exactly as PD-1 requires of the real act.

## 4. Reconciliation

- `core/dreams_view.py:52-55,62-63` — *"None = no verdict layer wired → surfaces every dream"* /
  *"Omit it to keep the prior behavior byte-identical."* → **[cross-ref: extension]**. Not a
  correction: `DreamsView`'s default is right for *its* invariant. `ChatValidityView` must
  document the divergence at its own constructor so a later refactor cannot "harmonize" the two
  and silently reintroduce the E8 hole:
  ```
  # Divergence from DreamsView, deliberate: there, the retraction filter is OPTIONAL and omitting
  # it preserves prior behavior. Here it is REQUIRED. E8 (dn-erratum-relation §3): "the default
  # view may never keep serving a record its own store asserts was never true." An optional
  # filter makes the DEFAULT construction the violation. The unfiltered read still exists — it is
  # `believed_rows()`, named for what it is: a belief query, never the default.
  ```

- `docs/design-notes/erratum-relation.md:255-256` — *"`ChatlogStore.all_rows`/`rows_for`
  (`core/stores/chatlog.py:171-190`) filter on nothing but provenance"* → **verified accurate**
  (§3 Q1). No correction; recorded because it is the one claim this plan most depends on.

- **No change is proposed to `core/stores/chatlog.py`.** The store's reads stay exactly as they
  are — this plan adds a view *over* them rather than filtering *inside* them. Rationale, recorded
  so it is not re-litigated: filtering inside the store would make the belief query
  (§7's criterion (c), which must return all 139 **flagged**) unreachable, and would couple an
  inner store to the errata store. The view is the correct seam; the store keeps both truths.

## 5. Write scope

- `core/chat_validity_view.py` — **the deliverable.** New module: `ChatValidityView`, its two
  Protocols, and the chat target-key helper.
- `tests/unit/test_chat_validity_view.py` — **new.** The three-census check on a fixture, the E8
  constructor test, the consumer-census tripwire, and the mutation campaign.
- `core/kernel/rings.py` · `tests/unit/test_inner_ring.py` — ⚑ **carried as a FALLBACK only**
  (§3 Q8). The intended outcome is that neither is touched: the module imports an outer symbol
  (the `dreams_view` precedent) and therefore computes outer, exactly as every other `core/*_view.py`
  does. They are in scope because `test_inner_ring.py` reddens on an *un-declared promotion* and a
  builder discovering that mid-session would otherwise be denied a file its plan needs — the
  false-negative denial finding-0085 exists to prevent. **If you edit `core/kernel/rings.py`, stop
  and re-read §3 Q8 first**: declaring this view inner would be a real architectural change (a view
  in the inner ring), not a test fix, and the map's own rule is *"never edit toward green"*.

**Deliberately OUT of scope:** `core/stores/chatlog.py` (unchanged by design — §4);
`core/chat_events.py` and `core/temporal/spine.py` (**bp-132** migrates them — §12);
`core/stores/errata.py` (bp-129's, consumed read-only here); `ops/chat_sensor.py` (φ_chat 2.0.0
is parked); every design note; the foundation denylist.
⚑ **No live store is opened, read, or written.** Every test uses `:memory:`/`tmp_path`. The
fixture *replicates* the 139-row shape; it never reads `data/chatlog.sqlite`.

## 6. Interfaces pinned inline

**Consumed from bp-129** (`core/stores/errata.py`):
```python
def targets_for(self, surface: str) -> set[str]:        # validity filter, NO cut argument (E3)
def targets_as_of(self, surface: str, seq: int) -> set[str]:   # belief filter, ledger slice
```

**Consumed from the chat store** (`core/stores/chatlog.py:171-190`, verbatim signatures):
```python
def all_rows(self, *, provenances: Iterable[Provenance] | None = None) -> list[dict[str, Any]]:
def rows_for(self, session_id: str) -> list[dict[str, Any]]:
def sessions(self) -> list[str]:
```
Row dict keys (from the DDL, `:76-91`): `session_id`, `turn_index`, `speaker`, `text`,
`transcript_digest`, `provenance`, `ts_bookmark`, `observed_at`, `interpreter`.

**The module this plan adds:**

```python
CHAT_SURFACE = "chat_utterances"   # the `surface` value errata over these rows carry


def chat_target_key(session_id: str, turn_index: int) -> str:
    """The ONE definition of a chat row's erratum target key. bp-129's store keeps keys opaque
    and never parses them, so this lane owns the format and must define it exactly once.
    ⚑ Caveat: `session_id` is a uuid and `turn_index` an int, so ':' cannot occur in either —
    the join is unambiguous. Asserted by test, not assumed."""
    return f"{session_id}:{turn_index}"


class ChatRowReads(Protocol):
    """The read slice of a ChatlogStore this view binds — reads and ONLY reads."""
    def all_rows(self, *, provenances: Any = ...) -> list[dict[str, Any]]: ...
    def rows_for(self, session_id: str) -> list[dict[str, Any]]: ...
    def sessions(self) -> list[str]: ...


class ErratumReads(Protocol):
    """A duck-typed source of erratum target keys (an `ErrataStore`)."""
    def targets_for(self, surface: str) -> set[str]: ...
    def targets_as_of(self, surface: str, seq: int) -> set[str]: ...


@dataclass(frozen=True)
class ChatValidityView:
    """Read-only view splitting BELIEF from VALIDITY over the chat stratum.

    ⚑ The erratum source is REQUIRED, not optional — E8. There is no construction of this view
    that serves erratum-targeted rows from a default-named read."""

    _all_rows: Callable[..., list[dict[str, Any]]]
    _rows_for: Callable[[str], list[dict[str, Any]]]
    _sessions: Callable[[], list[str]]
    _targets_for: Callable[[str], set[str]]
    _targets_as_of: Callable[[str, int], set[str]]

    @classmethod
    def over(cls, store: ChatRowReads, *, errata: ErratumReads) -> ChatValidityView:
        """Bind the store's reads plus the REQUIRED erratum source. `errata=None` raises
        `ErratumSourceRequired` — the E8 structural check, fail-closed at construction (the
        `ObservedView.__post_init__` idiom)."""

    # --- the validity query (the DEFAULT read) -------------------------------------------
    def valid_rows(self) -> list[dict[str, Any]]:
        """π_valid over the chat lane: every row the store holds MINUS every erratum target.
        Transport-invariant — takes no cut, because erratum status acts at every cut (E3)."""

    def valid_rows_for(self, session_id: str) -> list[dict[str, Any]]:

    # --- the belief query (EXPLICITLY named; never the default) ---------------------------
    def believed_rows(self, *, as_of_seq: int | None = None) -> list[dict[str, Any]]:
        """What the store BELIEVED: every row, each annotated with `erratum: bool`. With
        `as_of_seq`, the ledger slice at that belief position (`targets_as_of`) — so for
        `seq >= asserted_at` the answer self-annotates. Belief is a fact about the cut;
        this NEVER excludes."""

    # --- the census used by §7's three-part check ------------------------------------------
    def census(self, *, speaker: str, text_prefix: str, believed: bool = False) -> int:
        """Count rows matching (speaker, text_prefix) in the VALIDITY view by default, or in
        the BELIEF view when `believed=True`. The §7 acceptance is three calls to this."""


class ErratumSourceRequired(ValueError):
    """A ChatValidityView was constructed without an erratum source — refused at the
    boundary (E8: the default view may never serve a record asserted never true)."""
```

**E8, verbatim** (`dn-erratum-relation` §3): *"An erratum targeting a record in any DEFAULT view
must land in the same act as its replacement projection or an explicit retraction — the default
view may never keep serving a record its own store asserts was never true."*

## 7. Items

### Item 1 — the view, with the erratum source structurally required

- **Objective:** `ChatValidityView` exists; it cannot be constructed without an erratum source;
  its default-named reads exclude erratum targets and its belief read is separately named.
- **Files:** `core/chat_validity_view.py` (new).
- **Acceptance test:** `ChatValidityView.over(store, errata=None)` raises `ErratumSourceRequired`;
  `ChatValidityView.over(store)` (omitted kwarg) raises `TypeError`; a constructed view exposes
  **no** mutator (`dir()` contains no `add`/`add_batch`/`reset`/`close`); `uv run mypy core agents
  eval ops scheduler scripts` reports **Success: no issues**; `uv run python
  scripts/check_imports.py` exits 0.
- **Falsifier:** the erratum source turns out to be reachable as `None` through **any** path —
  a default argument, a dataclass field default, a `replace()`, or direct `ChatValidityView(...)`
  construction bypassing `over()`. Any of these restores the `DreamsView` default that E8 forbids
  (§3 Q3) and the E8 guarantee becomes advisory. Test the direct-construction path explicitly;
  it is the one a `@dataclass` silently leaves open.
- **Invariant(s) it must not violate:** E8 · E3 (`valid_rows` takes no cut argument — a signature
  assertion) · the view exposes reads only · `core/stores/chatlog.py` is not modified.
- **Touches stored data?** **No.**
- **Parallelizable?** No.  **Depends on:** bp-129 Item 1 (`ErrataStore.targets_for`).

### Item 2 — the §7 three-census check, on a fixture

- **Objective:** the note's own acceptance criterion, executable.
- **Files:** `tests/unit/test_chat_validity_view.py` (new).
- **Acceptance test:** build a fixture `ChatlogStore(":memory:")` seeded with a replica of the
  live shape — **139** rows `speaker='owner'`, text beginning `Stop hook feedback:`, spread over
  **33** sessions, plus a control population of genuine owner and agent rows (including ⚑ **2
  decoy rows that *contain* `Stop hook feedback` but do not *begin* with it** — the finding-0256
  shape, which must survive as valid). Assert an erratum over the **139 enumerated** target keys,
  then:
  - **(a)** `view.census(speaker="owner", text_prefix="Stop hook feedback:")` == **0**;
  - **(b)** the same census through a `σ^*`-style pre-assertion cut == **0** (validity is
    transport-invariant: the answer does not depend on the cut);
  - **(c)** `view.census(..., believed=True)` == **139**, and **every one of those rows carries
    `erratum: True`** — the "every one flagged" clause, asserted per-row, not by count alone;
  - the **2 decoy rows remain in `valid_rows()`** — proof the correction enumerated rather than
    predicated (PD-1).
- **Falsifier:** ⚑ **(a) green while (b) or (c) is red** — *"A green (a) with a red (b) or (c) is
  the false success, named"* (`erratum-relation.md:261`). Concretely: the view excludes rows from
  the default read but the belief query has lost them (history destroyed — E2 violated), or the
  validity answer changes with the cut (E3 violated, the marker-on-edge model in disguise).
  A second falsifier: a decoy row disappears, meaning the implementation matched a **predicate**
  rather than the enumerated key set.
- **Invariant(s) it must not violate:** E2 (belief query still returns all 139 — nothing is
  destroyed) · E3 · PD-1 (enumeration, never predication) · no live store touched.
- **Touches stored data?** **No** — fixture only. ⚑ The builder must **not** point any test at
  `data/chatlog.sqlite`, even read-only: a passing test against live data would silently become a
  false green the moment the live store changes.
- **Parallelizable?** No.  **Depends on:** Item 1.

### Item 3 — the E8 consumer tripwire (the false-success alarm, executable)

- **Objective:** make "an erratum lands but every consumer still reads the false rows" a **red
  test**, not a thing someone notices later.
- **Files:** `tests/unit/test_chat_validity_view.py`.
- **Acceptance test:** a test that scans the tree for production call sites of
  `ChatlogStore.all_rows` / `.rows_for` / `.sessions` **outside** `core/stores/chatlog.py`,
  `core/chat_validity_view.py`, and `tests/`, and asserts the set equals a **pinned, enumerated
  expected set** — today exactly:
  - `core/chat_events.py` (`:205`, `:208`)
  - `core/temporal/spine.py` (`:434`)
  The test **names them as known-unmigrated (bp-132)** and fails if the set **grows** — a new
  bypassing consumer — or if it **shrinks without the pin being updated**. ⚑ This is the plan's
  most important criterion: it converts §7's degenerate input from prose into a gate.
- **Falsifier:** the scan is written so loosely that it matches nothing (e.g. a grep for a symbol
  that does not appear, or one that excludes `core/` by accident) — then it passes green forever
  while measuring **nothing**. ⚑ **Prove it reddens:** add a throwaway file with a bypassing call
  site, confirm the test **fails**, remove it. Record the observed failure output in `journal.md`.
  This is the degenerate input *of the tripwire itself*, and it must be demonstrated, not argued.
- **Invariant(s) it must not violate:** the test must not import or execute the consumers (a
  static scan, not a runtime one) — importing `core/temporal/spine.py` pulls a 60KB module and
  its store wiring into a unit test.
- **Touches stored data?** **No.**
- **Parallelizable?** No.  **Depends on:** Items 1, 2.

### Item 4 — the mutation campaign

- **Objective:** prove Items 1–3 are not vacuous.
- **Files:** `tests/unit/test_chat_validity_view.py`.
- **Acceptance test:** apply each mutant to `core/chat_validity_view.py`, run the test module,
  record the verdict in `journal.md`, revert:
  1. `valid_rows` returns `self._all_rows()` unfiltered — **the note's degenerate input exactly**;
  2. `believed_rows` excludes erratum targets (collapses belief into validity — kills criterion (c));
  3. `over()` accepts `errata=None` and stores it (restores the `DreamsView` default — E8 hole);
  4. `census` matches by substring rather than prefix (sweeps in the 2 decoys — PD-1 violated);
  5. `valid_rows` gains a cut parameter and filters `targets_as_of` instead of `targets_for`
     (breaks E3 — validity becomes cut-relative).
  **Every mutant must be CAUGHT.**
- **Falsifier:** mutant 1 survives. That is the false-success signature in its purest form: the
  view exists, the suite is green, and the default read still serves every row the store asserts
  was never true. If it survives, Item 2's acceptance was measuring the fixture rather than the
  filter.
- **Invariant(s) it must not violate:** the argless `uv run mypy` tail still equals the pinned
  tests/ baseline (**69**); the full suite's failure count is unchanged.
- **Touches stored data?** **No.**
- **Parallelizable?** No.  **Depends on:** Items 1–3.

## 8. Math carried explicitly

- **`π_valid` restricted to the chat lane** — *measures:* which chat rows were **true**, as
  opposed to which the store **believed**. Realized here as a **set-difference over enumerated
  target keys**, not as a matrix product: bp-130 builds the operator form over a
  `CitationComplex`; this is the same projection expressed on a row set, which is what a SQL-shaped
  lane can carry (§3 Q2 of bp-130). *valid when:* the target set is enumerated at assertion (PD-1)
  and cut-independent (E3), and every consumer of the lane reads through the view. *fails its keep
  if:* the two realizations disagree — a row excluded by `valid_rows()` that the operator form
  would keep, or vice versa, for the same target set. That would mean "validity" means two
  different things in two places, and the note's one-relation claim (§6) is false.

- **The belief/validity split (the bitemporal pair)** — *measures:* the two time axes the note's
  §2 separates — transaction time (when the store believed) and valid time (when it was true) —
  which supersession alone keeps glued together. *valid when:* the belief query is
  non-destructive (E2: all 139 still returned, flagged) **and** the validity query is
  transport-invariant (E3). *fails its keep if:* criterion (c) cannot be satisfied — i.e. the
  belief query cannot return a corrected row at all. Then the correction destroyed history, the
  append-only ruling (finding-0168) is violated, and this is a purge wearing an erratum's name
  (E7).

## 9. Non-goals

- **No correction of the live 139 rows.** No erratum is asserted against `data/chatlog.sqlite`.
  Firing the real act is the owner's (`dn-erratum-relation` §8), and it is triply blocked
  (bp-129 §11 PD-C).
- **No migration of the two live consumers** — that is **bp-132**. This plan *measures* the gap
  (Item 3); it does not close it.
- **No change to `core/stores/chatlog.py`** (§4 records why).
- **No φ_chat 2.0.0, no re-projection, no widened PK, no `speaker='system'` value.** All parked.
- **No decision about whether "in the default view" is a row flag or a membership property** —
  panel-dependent (§11 PD-H).
- **No embedding of chat prose.** ⚑ The note's §5(4) warns that if chat prose is ever vectorized,
  the erratum must land **first** — a false attribution must never enter the semantic plane. This
  plan does not vectorize anything, and must not.

## 10. Stop-and-raise conditions

- **Item 3's tripwire cannot be made to redden** → stop. A gate that cannot fail is worse than no
  gate: it launders the absence of a check into a green tick. File a finding rather than shipping it.
- **The fixture cannot reproduce the (a)/(b)/(c) split** — e.g. criterion (c) proves unreachable
  because the belief query has nowhere to read the flag from → that is a **`spec-defect`** in the
  design's read-surface typing (note PD-3, "belief-vs-validity as two views or a mode switch",
  whose re-entry condition is *"the graduating plan types the read surface"* — i.e. **this plan**).
  File it and park the criterion; do not invent a third view to route around it.
- **A mutant survives after strengthening** → record as an equivalent mutant with an explicit
  argument, or file a finding. Never silently accept a survivor (finding-0249).
- **Any instinct to point a test at `data/chatlog.sqlite`** (even `mode=ro`) → **stop.** A test
  green against live data is a false green the moment the data moves.
- **Any instinct to migrate `core/chat_events.py` or `core/temporal/spine.py`** because the
  tripwire is red → **stop.** Those files are outside `write_scope`; the red is the *deliverable*,
  and bp-132 is where it turns green. `scope-guard` will deny the write; a denial means narrow the
  scope or file a finding, never route around.

## 11. Parked decisions

| Decision | Default recorded | Rejected alternatives (why) | Re-entry condition |
|---|---|---|---|
| **PD-H — is "in the default view" a row flag or a membership property?** (note §5, panel column) | **Neither: a join against the errata store**, computed in the view. This is the panel-neutral third option — it presumes no row model and no `current_any` column, so the membership panel's verdict cannot invalidate it. | *A `current_any`-style row flag on `chat_utterances`* — rejected: that is the panel's question, and it would require a schema migration on a live store this wave must not touch. *A membership property* — rejected: `dn-vector-membership-store` is `draft` and returned **BLOCK · BLOCK · RATIFY-WITH-AMENDMENTS**; building against it now is designing against a substrate three reviewers just tried to break. | `dn-vector-membership-store` reaches `ratified`, at which point the view's internals may be re-expressed over whatever row model it settles — a change behind a stable view surface. |
| **PD-I — where the belief-query cut comes from** | An integer `as_of_seq` (the erratum ledger's own belief order), not a wall clock or a `CertifiedCut`. | *A `CertifiedCut` from `core/temporal/spine.py`* — rejected for now: it couples this view to the spine, which is one of the two unmigrated consumers, and the note's §4 types the belief query in the existing scope grammar without requiring a certificate. | bp-132 migrates the spine consumer, making the coupling free; or a caller needs a real certified cut. |
| **PD-J — the target-key format** | `f"{session_id}:{turn_index}"`, defined once in `chat_target_key()`. | *A JSON or tuple key* — rejected: bp-129 pins keys as opaque `TEXT`; a structured key would push parsing into the store, which its PD-D forbids. | A second surface adopts errata and the two key grammars need machine comparison (bp-129 PD-D's own re-entry). |

## 12. Dependency & ordering summary

**Within this plan** — strictly serial, ordered by blast radius (all items are additive; nothing
existing is modified, which is why this plan is safe to run before bp-132):

```
Item 1 (new view module)  ─>  Item 2 (§7 three-census, fixture)
                          ─>  Item 3 (E8 consumer tripwire)  ─>  Item 4 (mutation campaign)
```

**Across plans:**
- **`depends_on: [bp-129]`** — this plan consumes `ErrataStore.targets_for` / `targets_as_of`.
  It **must not start until bp-129 Item 1 is merged to main.** Hard edge, not advisory.
- `parallelizable_with: [bp-130]` — bp-130 writes only `core/kernel/temporal/**` +
  `tests/unit/test_temporal_operators.py`. **Disjoint from this plan's two globs; verified.**
- ⚑ **`bp-132` depends on THIS plan** and closes what Item 3 measures. The ordering is deliberate:
  the tripwire must exist and be **proven to redden** before the migration that turns it green,
  or the migration's success is unfalsifiable.

**Wave order:** `bp-129` → (`bp-130` ∥ `bp-131`) → `bp-132`.
