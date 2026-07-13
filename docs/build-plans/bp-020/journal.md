# bp-020 journal

## 2026-07-12 — minted at graduation (orchestrator, Fable/xhigh)

Plan created `proposed` by /graduate over the ratified `dn-self-sensing` (B-c:
backfill). Grounding verified in-session: bp-013's partially-recoverable seal usage
(`docs/build-plans/bp-013/journal.md:263-265` — opus, 54,048 tokens for the Item-8
session; Items 6-7 never captured, the recorded ledger gap), V3's expected inventory
(→ ≥5 pairs post-annotation), the dry-run-then-orchestrator-live split (finding-0031
class: builders never touch the main checkout's live stores). No code written; no data
touched. Awaiting the owner's `proposed → ready` hand edit; depends on bp-019.

## 2026-07-12 — /build enactment (builder session, worktree agent-acf8163bd0be42450)

Plan flipped `ready → in-progress`. Worktree pointer written to
`.claude/state/active-plan` (own worktree, `$PWD`-explicit per finding-0051).
Read the full §2 manifest: dn-self-sensing.md whole, bp-019/plan.md §6(d,e,f),
bp-013/journal.md:263-265, build-plan.md template §cost, `ops/self_sensor.py` +
`scripts/sense_self.py` as landed by bp-019.

**Reconciliation note (honest delta from plan §4's premise).** Plan §4 states
bp-013's `actual: null` → correction. At this builder's HEAD, `actual` was **NOT
null** — bp-013 was already seal-filled at commit `ef9319e` ("docs(triage): seal
bp-013") with `actual: { model: opus, tokens_item8: 54k, tool_calls_item8: 44,
note: "items 6-7 uncaptured" }`. That fill used non-conforming field names
(`tokens_item8`/`tool_calls_item8` instead of the schema's `tokens`/`tool_calls`,
and `54k` not the exact `54048`), so it silently under-parsed: running the current
`ops/self_sensor.py` `parse_plan_cost_block` against pre-edit HEAD yielded
`actual: {model: 'opus', raw: …}` — **no `tokens` key at all**, which would NOT
have joined as a complete pair the way Q1/V3 expects. So Item 9 is not "filling a
null" — it is **correcting a mis-shaped fill to match the parser's schema** so the
join is actually recoverable. The recorded facts (opus, 54048, items-6-7
uncaptured) are unchanged; only the encoding moves to match §6(a)'s pinned shape.
Not a stop-and-raise (no invented number; the correction is licensed by Item 9's
own §6(a) target-state spec, and Q3's "late ledger discipline, not history
rewriting" reasoning covers a field-name fix identically to a null fill).

**Item 9 — DONE.** Edited `docs/build-plans/bp-013/plan.md` cost block:
```
-  actual: { model: opus, tokens_item8: 54k, tool_calls_item8: 44, note: "items 6-7 uncaptured" }
+  actual: { model: opus, tokens: 54048, tool_calls: null, duration_min: null } # PARTIAL — Item 8 + finding-renumber session only; the Items 6-7 session was never captured (journal :263-265, the recorded ledger gap). Late seal-fill, 2026-07-12.
```
`git diff` confirms exactly one changed line (the honesty comment rides the same
line). `estimate:` line untouched (copied verbatim — never edited). Verified via
`uv run python3 -c "..."` calling `ops.self_sensor.parse_plan_cost_block` against
the edited file text: `actual == {model: 'opus', tokens: 54048, raw: '{ model:
opus, tokens: 54048, tool_calls: null, duration_min: null }'}` — acceptance test
PASSES. `tool_calls`/`duration_min` correctly absent from the payload (both
`null`, not digit strings) — no invented numbers, falsifier respected.
