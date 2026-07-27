---
type: build-plan
id: bp-132
track: erratum-relation
status: proposed
design_ref:
  - docs/design-notes/erratum-relation.md
contract: builder
write_scope:
  - core/chat_events.py
  - core/temporal/spine.py
  - tests/unit/test_chat_events.py
  - tests/unit/test_chat_clock.py
  - tests/unit/test_chat_sync.py
  - tests/unit/test_cuts.py
  - tests/unit/test_chat_validity_view.py
session_budget: 1
cost:
  estimate:
    model: opus
    tokens: 300k
  actual: null
depends_on: [bp-131]
parallelizable_with: []
created: 2026-07-27
updated: 2026-07-27
links:
  - docs/design-notes/chat-sensor.md
  - docs/findings/finding-0258.md
  - docs/brainstorms/the-false-success-rule.md
re_entry: null
supersedes: null
superseded_by: null
warrant: null
---

# Build Plan — every chat consumer declares its axis: belief or validity

## 0. Mode & provenance

Investigation and planning produced this plan; **implementation proceeds item-by-item on
owner approval**. It closes what bp-131's Item 3 tripwire measures: the two live consumers
that read the chat store directly and therefore cannot honor an erratum either way.

⚑ **The grounding pass changed this plan's objective, and the change is the point.** The
obvious framing — *"migrate both consumers to the validity view"* — is **wrong**, and
graduating it would have shipped a real corruption. §3 Q1/Q2 establish that **both live
consumers are belief-axis readers**: filtering either one by validity would break it. The
objective is therefore to make each consumer's axis **explicit and annotated**, not to
filter it. Filed as **finding-0258** because the design note does not settle this.

Authority-to-act is separate from the readiness blessing (`proposed → ready`), which is the
**owner's hand only**.

## 1. Objective

Route both live chat consumers through `ChatValidityView` so each one's **belief-vs-validity
choice is a declared, tested decision** rather than an accident of reading the store directly.

## 2. Context manifest

Read these, in order, before any work:

1. `docs/design-notes/erratum-relation.md` §2 (the belief-interval / validity-claim split — the
   distinction this plan applies), §3 (E2, E8), §4 (the two forensic queries).
2. `docs/build-plans/bp-131/plan.md` §6 — `ChatValidityView`'s pinned surface, which this plan
   consumes; and its Item 3, whose pinned consumer set this plan drives to empty.
3. `core/chat_validity_view.py` — bp-131's deliverable, as merged.
4. `core/chat_events.py:195-215` — consumer #1. The `sessions()` + `rows_for()` churn-detection
   read.
5. `core/temporal/spine.py:420-445` — consumer #2. The `all_rows()` g1-chain construction over
   chat rows.
6. `docs/findings/finding-0258.md` — the axis discovery this plan is built on.
7. `docs/brainstorms/the-false-success-rule.md` — the degenerate input for a migration plan is
   unusually subtle (§7 Item 3).

**DRY audit — does `core/` already implement this?** This plan introduces **no** algorithm or
primitive; it re-points two existing call sites at a view built by bp-131. The relevant audit is
the inverse — *does a second filtering path get introduced?* It must not: all erratum awareness
comes from `ChatValidityView`, and neither consumer may compute a target set itself.

## 3. Investigation & grounding

- **Q1 — Should `core/temporal/spine.py` read VALID rows or BELIEVED rows?**
  ⚑ **BELIEVED — and validity-filtering it would corrupt the spine.** Two independent reasons,
  both grounded:
  1. **Structural.** `spine.py:434-440` builds a per-session g1 chain: one event per row, linked
     in `turn_index` order via `prev_by_session`. Dropping erratum-targeted rows would leave the
     chain **linking across gaps** — `turn_index` 5 chained directly to 7 — silently changing the
     chain's meaning from "consecutive observed turns" to "consecutive *surviving* turns".
     The docstring at `:429-431` pins the invariant this breaks: *"introduces no generator edge
     into any cut — `crossing_edges` stays [] for a certified observed cut"*.
  2. **Semantic.** The spine is a **transaction-time** structure: it records *that a row was
     observed, and in what order*. Per the note's §2, a record *"entered the store at write `b(r)`
     and, the ledger being append-only, is believed-recorded forever after"* — and an erratum
     leaves the belief interval **untouched**. The row was genuinely recorded; only its content
     was never true. ⇒ The spine's correct query is the **belief** query.

- **Q2 — Should `core/chat_events.py` read VALID rows or BELIEVED rows?**
  **BELIEVED**, for a different reason: it does not read row *content* at all. `:205-212` calls
  `sessions()`, then `rows_for(session_id)`, then uses **only** `rows[-1]["transcript_digest"]`
  — the newest raw blob's digest — for churn detection (*"A session is skipped when its latest
  digest equals the stored one"*, `:201-203`). Validity-filtering could **remove the last row**
  and hand back a stale digest, causing a session to be re-projected forever or skipped wrongly.
  The read is bookkeeping over the belief ledger; erratum status is irrelevant to it and
  filtering is actively harmful.

- **Q3 — Then what does this plan actually change, if neither consumer filters?**
  It changes **who they ask and what they declare.** Today both reach into `ChatlogStore`
  directly, so their axis is unstated and unenforced — no reader can tell whether the belief read
  is a decision or an oversight, and a future edit could switch either to a validity read with no
  test objecting. After this plan both call `ChatValidityView.believed_rows(...)`, the choice is
  **named at the call site, justified in a comment, and pinned by a test**. That is the whole
  deliverable, and it is worth a plan precisely because the *wrong* migration is the plausible one.

- **Q4 — Does `ChatValidityView` expose what these consumers need?**
  **Partly — and the gap is real.** bp-131 pins `believed_rows(*, as_of_seq=None)`, `valid_rows()`,
  `valid_rows_for(session_id)`, `sessions()` binding, and `census(...)`. Consumer #1 needs a
  **per-session belief read** (`rows_for` on the belief axis), which bp-131's surface does **not**
  include — it pins `valid_rows_for` but no `believed_rows_for`. ⇒ **This plan must add
  `believed_rows_for(session_id)` to the view.** ⚑ That file is **not** in this plan's
  `write_scope` (§5 records the consequence and §10 the stop condition).

- **Q5 — Which tests pin the surfaces this plan moves? (the retrofit scan)**
  Measured by grepping `chatlog|all_rows|rows_for` across `tests/`:
  `tests/unit/test_chat_clock.py` (**19** hits — the heaviest; the CS-4 clock/chain tests over
  spine chat wiring), `tests/unit/test_chat_events.py` (**10**), `tests/unit/test_chat_sync.py`
  (**5**), `tests/unit/test_cuts.py` (**2**). `tests/unit/test_spine.py` and
  `tests/unit/test_chat_sensor_wiring.py` have **0** and are deliberately excluded.
  All four with hits are pre-widened into `write_scope` (§5) — they construct `ChatlogStore`
  fixtures and hand them to the consumers, so a constructor-signature change reddens them.

- **Q6 — Does either consumer construct its store, or receive it?**
  Both **receive** it, which makes this tractable: `core/chat_events.py:195` holds
  `chatlog: ChatlogStore` as a field, wired at `:225-229` in a factory; `core/temporal/spine.py:327`
  holds `chatlog: ChatlogStore | None`, wired at `:372` and via a setter at `:424`.
  ⇒ The change is at the **wiring** points plus the read call sites — no consumer needs to learn
  where a store lives, and the `| None` shape on the spine must be preserved (`:372` only
  constructs the store `if chatlog_p.exists()`).

**Additional risks or questions surfaced during reading:**

- ⚑ **`core/temporal/spine.py` is a ~60KB module on the certified-cut path.** It is by far the
  highest blast radius in this wave. Item 2 is ordered last for that reason, and §10 names the
  stop conditions that must halt it rather than push through.
- The erratum source must be **optional at the wiring layer** for the spine, because the spine
  already tolerates an absent chatlog (`:372`). A required-errata view (bp-131's E8 design) inside
  an optional-store consumer needs care: the view is constructed only when the store exists.

## 4. Reconciliation

- `core/temporal/spine.py:434` — `for row in store.all_rows():` → **[banner: correction]**. Not a
  behavior correction (the rows returned are identical) but an **explicitness** correction: the
  call site must state its axis so a later edit cannot silently change it.
  ```python
  # BELIEF axis, deliberately — NOT validity. The spine records that a row was OBSERVED and in
  # what order; an erratum leaves the belief interval untouched (dn-erratum-relation §2).
  # Validity-filtering here would chain across gaps (turn 5 → 7), silently redefining the g1
  # chain from "consecutive observed turns" to "consecutive surviving turns". See finding-0258.
  for row in view.believed_rows():
  ```

- `core/chat_events.py:208` — `rows = self.chatlog.rows_for(session_id)` → **[banner: correction]**,
  same shape:
  ```python
  # BELIEF axis, deliberately. This read uses ONLY rows[-1]["transcript_digest"] for churn
  # detection; validity-filtering could drop the last row and yield a stale digest, re-projecting
  # a session forever. Erratum status is irrelevant to raw-blob bookkeeping. finding-0258.
  rows = view.believed_rows_for(session_id)
  ```

- `docs/build-plans/bp-131/plan.md` §7 Item 3 — its pinned consumer set names these two files as
  *known-unmigrated*. → **[cross-ref: extension]**: this plan drives that set to **empty** and
  updates the pin in `tests/unit/test_chat_validity_view.py`. The tripwire is not deleted — it
  keeps guarding against a **new** bypassing consumer.

## 5. Write scope

- `core/chat_events.py` — consumer #1: the wiring and the one read call site.
- `core/temporal/spine.py` — consumer #2: the wiring, the setter, and the one read call site.
- `tests/unit/test_chat_clock.py` · `tests/unit/test_chat_events.py` ·
  `tests/unit/test_chat_sync.py` · `tests/unit/test_cuts.py` — **carried because they pin the
  surfaces this plan moves** (§3 Q5: 19 / 10 / 5 / 2 hits respectively). They build `ChatlogStore`
  fixtures and pass them to the consumers, so a wiring-signature change reddens them.
- `tests/unit/test_chat_validity_view.py` — **carried to update bp-131's pinned consumer set** to
  empty; without it, Item 3's tripwire reddens on a *shrink* it was designed to notice.

⚑ **The gap, stated plainly:** §3 Q4 establishes that `believed_rows_for(session_id)` must be
**added to `core/chat_validity_view.py`**, which is **deliberately NOT in this write_scope** —
it is bp-131's file, and widening a plan's scope onto another plan's deliverable after the fact
is how surfaces drift. See §10 and §11 PD-K for the two lawful routes.

**Deliberately OUT of scope:** `core/stores/chatlog.py` (unchanged throughout the wave);
`core/stores/errata.py`; `ops/chat_sensor.py`; every design note; the foundation denylist.
⚑ **No live store is opened or written; no ingestion is run; the daemon is not touched.**

## 6. Interfaces pinned inline

**Consumed from bp-131** (`core/chat_validity_view.py`, as merged):
```python
CHAT_SURFACE = "chat_utterances"
def chat_target_key(session_id: str, turn_index: int) -> str
class ChatValidityView:
    @classmethod
    def over(cls, store: ChatRowReads, *, errata: ErratumReads) -> ChatValidityView
    def valid_rows(self) -> list[dict[str, Any]]
    def valid_rows_for(self, session_id: str) -> list[dict[str, Any]]
    def believed_rows(self, *, as_of_seq: int | None = None) -> list[dict[str, Any]]
    def census(self, *, speaker: str, text_prefix: str, believed: bool = False) -> int
class ErratumSourceRequired(ValueError)
```

**The one addition this plan requires** (§3 Q4 — landing route per §11 PD-K):
```python
def believed_rows_for(self, session_id: str, *, as_of_seq: int | None = None) -> list[dict[str, Any]]:
    """One session's rows on the BELIEF axis, in chain order (turn_index), each annotated with
    `erratum: bool`. The per-session dual of `believed_rows`; NEVER excludes."""
```

**Consumer #1 — current form** (`core/chat_events.py:195,205-212`, verbatim):
```python
    chatlog: ChatlogStore
    ...
        for session_id in self.chatlog.sessions():
            if projected >= max_sessions:
                break
            rows = self.chatlog.rows_for(session_id)
            if not rows:
                continue
            digest = str(rows[-1]["transcript_digest"])         # the newest (fullest) raw for it
```

**Consumer #2 — current form** (`core/temporal/spine.py:327,372,433-440`, verbatim):
```python
    chatlog: ChatlogStore | None = None      # CS-4 (bp-064): the observed-stratum chat store
    ...
            chatlog=ChatlogStore(chatlog_p) if chatlog_p.exists() else None,
    ...
        self.present.append("chatlog")
        prev_by_session: dict[str, str] = {}
        for row in store.all_rows():
            session_id, turn_index = str(row["session_id"]), int(row["turn_index"])
            eid = self._add("chatlog", session_id, turn_index, produces=(), consumes=())
            prev = prev_by_session.get(session_id)
            if prev is not None:                              # per-session chain (turn-index order)
                self.g13_edges.add((prev, eid, "g1"))
            prev_by_session[session_id] = eid
```

**The invariant the spine read must preserve** (`spine.py:428-431`, verbatim): *"introduces no
generator edge into any cut — `crossing_edges` stays [] for a certified observed cut (plan §3 Q5).
Order is turn index, NEVER the ts_bookmark wall time (Law C4)."*

## 7. Items

### Item 1 — consumer #1: `core/chat_events.py` declares the belief axis

- **Objective:** the churn-detection read goes through `ChatValidityView.believed_rows_for`, with
  its axis choice annotated and tested.
- **Files:** `core/chat_events.py`, `tests/unit/test_chat_events.py`, `tests/unit/test_chat_sync.py`.
- **Acceptance test:** `uv run pytest tests/unit/test_chat_events.py tests/unit/test_chat_sync.py -q`
  green; a new test asserts that with an erratum over **every** row of a session, the churn
  detector still computes the **same** digest and makes the **same** re-projection decision as
  with no erratum at all — i.e. the read is provably erratum-**insensitive**, which is the
  correctness claim (§3 Q2).
- **Falsifier:** the digest or the re-projection decision **changes** when an erratum is asserted.
  That means the consumer was wired to the validity axis, and a corrected session would either
  re-project forever or be skipped wrongly. ⚑ This falsifier is the reason the plan exists: it is
  the observable that distinguishes the correct migration from the plausible-but-wrong one.
- **Invariant(s) it must not violate:** churn detection stays digest-based; no erratum computation
  happens inside the consumer (all of it comes from the view).
- **Touches stored data?** **No** — tests use `:memory:`/`tmp_path`.
- **Parallelizable?** No.  **Depends on:** bp-131 (merged), and the §11 PD-K addition.

### Item 2 — consumer #2: `core/temporal/spine.py` declares the belief axis

- **Objective:** the g1 chain is built from `believed_rows()`, with the gap hazard annotated and
  the chain's integrity tested.
- **Files:** `core/temporal/spine.py`, `tests/unit/test_chat_clock.py`, `tests/unit/test_cuts.py`.
- **Acceptance test:** `uv run pytest tests/unit/test_chat_clock.py tests/unit/test_cuts.py -q`
  green; a new test asserts that with an erratum over a **middle** row of a session (say
  `turn_index` 5 of 0..9), the g1 chain still contains **all ten** events and **every consecutive
  link** — no gap-spanning edge — and `crossing_edges` is still `[]` for a certified observed cut.
- **Falsifier:** the chain contains **nine** events, or a `g1` edge linking `turn_index` 4 directly
  to 6. Either shows the spine was wired to the validity axis, silently redefining the chain from
  "consecutive observed turns" to "consecutive surviving turns" — a corruption of a certified
  structure that no downstream consumer could detect.
- **Invariant(s) it must not violate:** ⚑ the `spine.py:428-431` invariant, verbatim — no
  generator edge into any cut, `crossing_edges == []` for a certified observed cut, order by turn
  index never `ts_bookmark` (Law C4); the `chatlog: ChatlogStore | None` optionality at `:327,372`
  survives (an absent chat store must still be tolerated).
- **Touches stored data?** **No** — tests use `:memory:`/`tmp_path`. ⚑ The builder must not point
  the spine at `data/chatlog.sqlite`.
- **Parallelizable?** No.  **Depends on:** Item 1 (sequenced so the low-radius consumer proves the
  pattern before the high-radius one adopts it).

### Item 3 — the tripwire goes green, and stays a tripwire

- **Objective:** bp-131's pinned consumer set is empty, and the gate still catches a **new**
  bypassing consumer.
- **Files:** `tests/unit/test_chat_validity_view.py`.
- **Acceptance test:** the pinned expected set in bp-131's Item 3 scan is updated to **empty**, and
  `uv run pytest tests/unit/test_chat_validity_view.py -q` is green. ⚑ **Then prove it still
  reddens:** add a throwaway file with a direct `ChatlogStore.all_rows()` call site, confirm the
  test **fails**, remove it, and record the observed failure output in `journal.md`.
- **Falsifier:** ⚑ **the degenerate input for a migration plan** — the tripwire goes green because
  the *scan* was narrowed (a path exclusion, a loosened pattern) rather than because the
  *consumers* moved. Green-by-narrowing is indistinguishable from green-by-fixing in the test
  output, which is exactly why the redden-check above is mandatory rather than optional. Diff the
  scan's own source against bp-131's version and confirm **only the expected-set literal changed**.
- **Invariant(s) it must not violate:** the scan's pattern and path-exclusion logic are unchanged
  from bp-131 — only the expected set moves.
- **Touches stored data?** **No.**
- **Parallelizable?** No.  **Depends on:** Items 1, 2.

### Item 4 — the mutation campaign

- **Objective:** prove Items 1–3 are not vacuous.
- **Files:** the three test files touched above.
- **Acceptance test:** apply, run, record in `journal.md`, revert:
  1. `core/chat_events.py` reads `valid_rows_for` instead of `believed_rows_for` — **must be
     caught by Item 1's falsifier**;
  2. `core/temporal/spine.py` reads `valid_rows()` instead of `believed_rows()` — **must be caught
     by Item 2's falsifier** (this is the corruption the plan exists to prevent; if it survives,
     the plan delivered nothing);
  3. the spine's `prev_by_session` chain links across a skipped row — must be caught;
  4. the tripwire scan's path exclusion widened to cover `core/` — must be caught by Item 3's
     redden-check.
  **Every mutant must be CAUGHT.**
- **Falsifier:** mutant 2 survives.
- **Invariant(s) it must not violate:** the argless `uv run mypy` tail still equals the pinned
  tests/ baseline (**69**); the full-suite failure count is unchanged from the wave's baseline.
- **Touches stored data?** **No.**
- **Parallelizable?** No.  **Depends on:** Items 1–3.

## 8. Math carried explicitly

- **The belief/validity axis choice, per consumer** — *measures:* which of the two time axes a
  given reader is asking about — transaction time (*was this recorded, and in what order?*) or
  valid time (*was this true?*). *valid when:* the choice is made per consumer on the semantics of
  what it computes, not globally: a chain-of-observation structure is belief-axis; a
  "what did the owner say" retrieval is validity-axis. *fails its keep if:* a consumer is found
  whose correct answer needs **both** axes simultaneously and cannot be expressed as two reads —
  that would mean the two-query split (note PD-3) is under-powered and a joint surface is needed.
  Neither live consumer has this shape; the refutation is recorded so it can be recognized.

- **Chain integrity under projection** — *measures:* whether the g1 chain's meaning survives a
  filtering of its underlying rows. *valid when:* the chain is built over the **unfiltered**
  belief sequence, so consecutive links correspond to consecutive observed turns. *fails its keep
  if:* a gap-spanning `g1` edge is ever produced (Item 2's falsifier) — the chain would then
  encode a different relation than its docstring claims, and every certified cut over it inherits
  the error silently.

## 9. Non-goals

- **No filtering of either consumer.** Both stay erratum-insensitive by design (§3 Q1/Q2); this
  plan makes that explicit, it does not change what rows they see.
- **No new erratum-awareness logic inside a consumer.** All of it comes from `ChatValidityView`.
- **No correction of the live 139 rows**; no erratum asserted against any live store.
- **No φ_chat 2.0.0, no re-projection, no widened PK.** Parked (bp-129 §11 PD-C).
- **No change to `core/stores/chatlog.py`** — unchanged across the whole wave.
- **No new consumer** of the chat lane. If one is wanted, it is a different plan and the tripwire
  will require it to declare an axis.

## 10. Stop-and-raise conditions

- ⚑ **`believed_rows_for` is missing from `core/chat_validity_view.py`** (§3 Q4) and that file is
  **outside this write_scope**. `scope-guard` will deny the write. **Do not route around it.** The
  two lawful moves are in §11 PD-K: file a `spec-defect` finding and park Item 1, or — if bp-131 is
  not yet merged when this is discovered — surface it so bp-131 lands the method. **A denial means
  narrow the scope or file a finding, never widen it by hand.**
- **Item 2's falsifier trips** (nine events, or a gap-spanning `g1` edge) → **stop immediately.**
  That is a corruption of a certified structure, not a test failure to iterate past. Revert and
  file a finding.
- **A `test_chat_clock.py` assertion cannot be satisfied without changing what the chain means** →
  stop and file a `spec-defect`. The CS-4 clock contract is ratified design; a builder must not
  renegotiate it to make a migration pass.
- **The tripwire can only be made green by editing the scan's logic** rather than the consumers →
  stop. That is green-by-narrowing (Item 3's falsifier).
- **A mutant survives after strengthening** → record as an equivalent mutant with an explicit
  argument, or file a finding.
- **Any instinct to touch `data/`, run ingestion, start/stop the daemon, or `deploy`** → stop.

## 11. Parked decisions

| Decision | Default recorded | Rejected alternatives (why) | Re-entry condition |
|---|---|---|---|
| **PD-K — how `believed_rows_for` lands** (§3 Q4) | **bp-131 adds it**, as part of its own §6 surface, before this plan starts. It is bp-131's file and bp-131's surface; the method is a per-session dual of one it already pins, so it belongs there. | *Widen this plan's `write_scope` to include `core/chat_validity_view.py`* — rejected: two plans holding one glob makes them mutually exclusive (delegate skill: *"plans sharing a `write_scope` glob are still mutually exclusive whatever their status says"*) and lets a consumer plan reshape a view plan's surface after review. *Have the consumer filter inline* — rejected: it puts erratum logic back into the consumer, which is exactly what this wave removes. | Noticed **at bp-131's blessing** ⇒ add the method to bp-131 §6 before it builds. Noticed **after bp-131 merges** ⇒ a `spec-defect` finding and a one-item follow-up plan; park Item 1 meanwhile and close Item 2, which does not need it. |
| **PD-L — should the spine ever expose a validity view of the chat chain?** | **No, not in this wave.** The spine is transaction-time by construction (§3 Q1). | *A parallel validity chain* — rejected: it doubles a certified structure for a consumer that does not exist, and the note's §4 types the validity query as a retrieval concern, not a spine one. | A real retrieval consumer needs "the chain as it would have been if the false rows had never landed" — which no artifact currently asks for. |
| **PD-M — the erratum source's optionality at the spine's wiring layer** | The view is constructed **only when the chat store exists**, preserving `chatlog: ChatlogStore \| None` (`spine.py:327,372`). Absent store ⇒ absent view ⇒ the chat chain is simply not built, exactly as today. | *Make the spine always construct a view over a possibly-empty store* — rejected: it changes `self.present.append("chatlog")` semantics, so a machine with no chat store would start reporting a chat stratum it does not have. | The spine's optional-store handling is redesigned for another reason. |

## 12. Dependency & ordering summary

**Within this plan** — strictly serial, ordered by blast radius, lowest first:

```
Item 1 (core/chat_events.py — small consumer, digest bookkeeping)
   └─> Item 2 (core/temporal/spine.py — ~60KB, certified-cut path)   ← HIGHEST radius in the wave
        └─> Item 3 (tripwire pin → empty, + prove it still reddens)
             └─> Item 4 (mutation campaign)
```

Item 1 before Item 2 deliberately: the low-radius consumer establishes the annotation-and-test
pattern, so the spine edit is a repetition of a proven shape rather than a first attempt on the
riskiest file.

**Across plans:**
- **`depends_on: [bp-131]`** — hard. This plan consumes `ChatValidityView` and updates bp-131's
  pinned tripwire set. It must not start until bp-131 is merged, and §11 PD-K must be settled
  first.
- **`parallelizable_with: []`** — deliberately empty. This plan holds
  `tests/unit/test_chat_validity_view.py`, which bp-131 also holds, so the two are **mutually
  exclusive by write_scope regardless of status**. It is also the wave's highest-blast-radius plan
  and should run with nothing else in flight.

**Wave order:** `bp-129` → (`bp-130` ∥ `bp-131`) → `bp-132`.
