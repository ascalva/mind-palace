# bp-131 — journal

## Pre-build notes for whoever picks this up

- ⚑ **This plan carries the design note's OWN named degenerate input as its central criterion.**
  `dn-erratum-relation` §7: *"an erratum lands and every consumer keeps reading the old rows."*
  Everything else here is scaffolding for making that impossible to ship silently. If you find
  yourself trimming Item 3, you are removing the plan's point.

- ⚑ **Follow `DreamsView`'s shape; REJECT its default.** `core/dreams_view.py:52-55` makes its
  retraction filter optional — *"None = no verdict layer wired → surfaces every dream"* — and that
  is right for *its* invariant. Here it would make the **default construction** the E8 violation.
  The erratum source is **required**. Test the direct-`ChatValidityView(...)` construction path
  too, not just `over()`: a `@dataclass` leaves that door open and it is Item 1's falsifier.

- ⚑ **Three censuses, not one. (a) alone is the false success.** The note is explicit
  (`erratum-relation.md:261`): *"A green (a) with a red (b) or (c) is the false success, named."*
  (a) default view = 0 · (b) validity at a pre-correction cut = 0 · (c) belief at that cut = 139
  **every one flagged**. Assert (c) per-row, not by count — "every one flagged" is the clause a
  count assertion silently drops.

- ⚑ **The 2 decoy rows are the PD-1 proof and must survive.** finding-0256: two owner-attributed
  rows *contain* `Stop hook feedback` but do not *begin* with it — they are the `update-config`
  skill's documentation text injected into a user-role record. They are mis-attributed too, but
  they are **not** in A2's warranted 139. If your implementation removes them, it matched a
  **predicate** instead of the **enumerated** key set, and PD-1 is violated. Seed them; assert they
  remain in `valid_rows()`.

- ⚑ **Item 3's tripwire must be PROVEN to redden.** A scan written slightly wrong matches nothing
  and passes green forever while measuring nothing — the degenerate input *of the tripwire itself*.
  Add a throwaway file with a bypassing call site, confirm the test fails, remove it, and paste the
  observed failure output into this journal. Not optional.

- **Do not migrate the two consumers.** `core/chat_events.py` and `core/temporal/spine.py` are
  outside `write_scope` and belong to bp-132. The tripwire being **red** is this plan's deliverable.
  `scope-guard` will deny the write; a denial means narrow the scope or file a finding, never route
  around. ⚑ And read finding-0258 before you form an opinion about what that migration should do —
  the obvious answer is wrong.

- ⚑ **Import an outer symbol, or you will redden `tests/unit/test_inner_ring.py`** (§3 Q8). That
  test asserts computed-inner == declared-inner in **both directions**, so a module written with
  only `typing`/`dataclasses`/Protocols computes as inner-ring and goes red until
  `core/kernel/rings.py` declares it. Follow `core/dreams_view.py:26`, which imports concrete types
  from `core.stores.derived` while keeping Protocols for its bound reads. `core/kernel/rings.py`
  and `tests/unit/test_inner_ring.py` are in `write_scope` as a **fallback only** — the intended
  outcome is that you touch neither. If you find yourself editing the rings map, stop: that is an
  architectural change (a view in the inner ring), and the map's own rule is *"never edit toward
  green"*.

- **`core/stores/chatlog.py` is not modified by this plan or any plan in this wave.** The view sits
  *over* the store. Filtering inside the store would make criterion (c) — the belief query —
  unreachable, and would couple an inner store to the errata store.

- ⚑ **Never point a test at `data/chatlog.sqlite`, even `mode=ro`.** A test green against live data
  becomes a false green the moment the data moves. The fixture *replicates* the 139-row shape.

- **Run the mutation campaign; do not reason about it** (finding-0249). Five mutants in Item 4.
  Mutant 1 (`valid_rows` returns unfiltered) is the note's degenerate input verbatim — if it
  survives, Item 2 was measuring the fixture rather than the filter.

## Grounding carried in from graduation (verified read-only, 2026-07-27)

- The chat reads filter on provenance and nothing else — `core/stores/chatlog.py:177-183`. Since
  every row is `observed`, that filter is a no-op; the docstring at `:174-176` says so.
- **Two live consumers, both unfiltered:** `core/chat_events.py:205,208` and
  `core/temporal/spine.py:434`. This is §7's degenerate input, verified rather than assumed.
- The 139: re-derived exactly — 33 sessions, `interpreter` 1.0.0 uniform, 2026-07-18…07-25, of
  9,145 utterances. Substring match gives **141**, not the 146 the seat's readings pane records
  (finding-0256).
- No embeddings exist over chat rows (`dn-trace-retrieval` G1), so this correction is pure
  metadata. ⚑ If chat prose is ever vectorized, the erratum must land **first** — a false
  attribution must never enter the semantic plane (`dn-erratum-relation` §5(4)).
