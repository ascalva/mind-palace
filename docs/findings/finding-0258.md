---
type: finding
id: finding-0258
status: open
created: 2026-07-27
updated: 2026-07-27
links:
  - docs/design-notes/erratum-relation.md
  - core/temporal/spine.py
  - core/chat_events.py
  - docs/build-plans/bp-132/plan.md
ftype: discovery
origin_plan: orchestrator
route: orchestrator
resolution: null
---

# Both live chat consumers are belief-axis readers — validity-filtering either one would corrupt it

## What

`dn-erratum-relation` §7 names its own degenerate input: *"an erratum lands and every consumer
keeps reading the old rows — because `ChatlogStore.all_rows`/`rows_for` filter on nothing but
provenance."* Verified accurate (`core/stores/chatlog.py:171-190`). The obvious remedy — *route
every consumer through the validity view* — is **wrong for both live consumers**, and graduating it
would have shipped a real corruption.

**Consumer #1 — `core/temporal/spine.py:434`** builds the CS-4 g1 chain over chat rows:

```python
for row in store.all_rows():
    session_id, turn_index = str(row["session_id"]), int(row["turn_index"])
    eid = self._add("chatlog", session_id, turn_index, produces=(), consumes=())
    prev = prev_by_session.get(session_id)
    if prev is not None:                       # per-session chain (turn-index order)
        self.g13_edges.add((prev, eid, "g1"))
```

Validity-filtering this would **link across gaps** — `turn_index` 4 chained directly to 6 when 5 is
erratum-targeted — silently redefining the chain from *"consecutive observed turns"* to
*"consecutive surviving turns"*, and threatening the invariant its own docstring pins at
`:428-431`: *"introduces no generator edge into any cut — `crossing_edges` stays [] for a certified
observed cut."*

**Consumer #2 — `core/chat_events.py:205-212`** does not read row content at all. It calls
`sessions()`, then `rows_for(session_id)`, then uses **only** `rows[-1]["transcript_digest"]` for
churn detection. Validity-filtering could **drop the last row** and hand back a stale digest,
causing a session to be re-projected forever or skipped wrongly.

⇒ **Both are transaction-time (belief) readers.** Neither asks *"was this true?"*; they ask
*"was this recorded, and in what order?"* — and the note's own §2 answers that an erratum leaves
the belief interval **untouched**: a record *"entered the store at write `b(r)` and, the ledger
being append-only, is believed-recorded forever after."*

## Why it matters

- **The plausible migration is the corrupting one.** "Make consumers honor the erratum" reads as an
  unambiguous instruction and produces, applied to the spine, a silently-wrong certified structure
  that no downstream consumer could detect. This is the failure mode a grounded graduation pass
  exists to catch, caught before a builder was spawned.
- **E8 needs a sharper statement than "consumers must filter."** Its text —*"the default view may
  never keep serving a record its own store asserts was never true"*— is about the **default
  view**, not about every reader. A belief reader explicitly asking for belief is not an E8
  violation; a reader that cannot *express* which axis it wants is. The real requirement is that
  **every consumer's axis be a declared, tested choice** rather than an artifact of reading the
  store directly.
- **The note does not settle this.** §5 says "the chat semantics: re-project + one erratum, keep
  both" and §7 names the consumer problem, but neither assigns an axis per consumer. That
  assignment is design work, done here at graduation and carried by `bp-132`.
- It generalizes: any future consumer of a corrected surface must declare an axis. A chain, a
  ledger, an audit trail, a churn detector are belief-axis; a retrieval, a synthesis, a
  "what did the owner say" query are validity-axis. Getting it backwards is silent in both
  directions.

## Re-entry condition

No criterion is parked. `bp-132` is built directly on this finding: its objective is *"every chat
consumer declares its axis"* rather than *"migrate to the validity view"*, both consumers are
routed to `believed_rows(...)` with the reason annotated at the call site, and its §7 Item 2
falsifier is exactly the corruption above (nine events, or a gap-spanning `g1` edge).

Re-entry for the **general** rule: when a third consumer of the chat lane appears, or when a
second corrected surface acquires consumers. At that point the per-consumer axis declaration
should probably be a stated design rule rather than a per-plan convention — see Routing.

## Routing

`discovery` bearing on design ⇒ **route: orchestrator**. One owner-level question, batched, not
blocking:

> Should the **per-consumer axis declaration** be promoted into `dn-erratum-relation` as an
> invariant (an E9, alongside E8), or does it stay a build-plan convention? E8 as written governs
> the *default view*; this finding shows the governing requirement is one level broader — every
> reader of a correctable surface declares belief or validity, and the choice is tested.

`bp-132` proceeds either way; promotion would only make the rule binding beyond this wave.
