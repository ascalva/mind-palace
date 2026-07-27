# bp-132 — journal

## Pre-build notes for whoever picks this up

- ⚑⚑ **READ finding-0258 FIRST. The obvious version of this plan is the corrupting one.**
  "Make the consumers honor the erratum" reads as an unambiguous instruction. Applied to
  `core/temporal/spine.py` it produces a **silently wrong certified structure**: dropping
  erratum-targeted rows leaves the g1 chain linking across gaps (`turn_index` 4 → 6), redefining it
  from *"consecutive observed turns"* to *"consecutive surviving turns"*. Nothing downstream could
  detect that. **Neither consumer filters.** Both are belief-axis readers, and this plan's job is
  to make that a *declared, tested* choice rather than an accident.

- ⚑ **Item 2's falsifier is a corruption, not a test failure to iterate past.** Nine events instead
  of ten, or a `g1` edge spanning a skipped turn ⇒ **stop, revert, file a finding.** Do not "fix
  forward" on the spine.

- ⚑ **`believed_rows_for(session_id)` may not exist yet** (§3 Q4). bp-131 pins `valid_rows_for` but
  no belief dual, and `core/chat_validity_view.py` is **outside this plan's write_scope** —
  deliberately, because two plans holding one glob makes them mutually exclusive and lets a consumer
  plan reshape a view plan's surface after review. §11 PD-K names the two lawful routes. **Do not
  widen the scope by hand.** If `scope-guard` denies you here, that denial is working correctly.

- **Item 1 before Item 2, and the order is not arbitrary.** `core/chat_events.py` is small and its
  read is pure bookkeeping. `core/temporal/spine.py` is ~60KB on the certified-cut path — the
  highest blast radius in the whole wave. Establish the annotation-and-test pattern on the cheap
  consumer first so the spine edit is a repetition of a proven shape.

- ⚑ **Green-by-narrowing is Item 3's falsifier.** The tripwire can be made green by editing the
  *scan* (a path exclusion, a loosened pattern) instead of the *consumers*, and the test output
  looks identical either way. After updating the pinned set, diff the scan's own source against
  bp-131's version and confirm **only the expected-set literal changed** — then re-prove it reddens
  with a throwaway bypassing call site and paste the failure output here.

- **Preserve the spine's optionality.** `chatlog: ChatlogStore | None` (`spine.py:327`), constructed
  only `if chatlog_p.exists()` (`:372`). A machine with no chat store must keep working exactly as
  it does now — the view is constructed only when the store exists (§11 PD-M).

- **The invariant you must not break, verbatim** (`spine.py:428-431`): *"introduces no generator
  edge into any cut — `crossing_edges` stays [] for a certified observed cut. Order is turn index,
  NEVER the ts_bookmark wall time (Law C4)."*

- **Run the mutation campaign; do not reason about it** (finding-0249). Four mutants in Item 4.
  **Mutant 2** (spine reads `valid_rows()`) is the one that matters — it is the corruption this
  whole plan exists to prevent. If it survives, the plan delivered nothing.

- **Do not touch `data/`, do not run ingestion, do not start/stop the daemon, do not deploy.**

## Grounding carried in from graduation (verified read-only, 2026-07-27)

- Consumer #1 — `core/chat_events.py:205-212`: `sessions()` → `rows_for(session_id)` → uses **only**
  `rows[-1]["transcript_digest"]` for churn detection. Reads no row content semantically.
- Consumer #2 — `core/temporal/spine.py:434`: `for row in store.all_rows():`, building the
  per-session g1 chain via `prev_by_session` in `turn_index` order.
- Both **receive** their store rather than constructing it (`chat_events.py:195`, wired `:225-229`;
  `spine.py:327`, wired `:372`, setter `:424`) — so the change is at the wiring points plus the two
  read call sites.
- Retrofit scan (`chatlog|all_rows|rows_for` across `tests/`): `test_chat_clock.py` **19** hits ·
  `test_chat_events.py` **10** · `test_chat_sync.py` **5** · `test_cuts.py` **2** ·
  `test_spine.py` **0** · `test_chat_sensor_wiring.py` **0**. The four with hits are pre-widened
  into `write_scope`; the two without are deliberately excluded.
