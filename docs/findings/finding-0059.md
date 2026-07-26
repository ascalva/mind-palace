---
type: finding
id: finding-0059
status: resolved
created: 2026-07-12
updated: 2026-07-26
links:
  - docs/build-plans/bp-020/plan.md
  - docs/build-plans/bp-019/plan.md
  - docs/design-notes/self-sensing.md
ftype: spec-fidelity
origin_plan: bp-020
route: builder
resolution: resolved — bp-020 re-grounded the baseline to 8 plans and the falsifier re-passed (`bp-020/journal.md:138-142,282`); frontmatter already carried `resolution: resolved`
---

# V3's "11 pre-rule, zero-cost-block" baseline is stale — bp-006/007/009 carry backfilled `actual`-only cost blocks

> **Triage 2026-07-26 (session-52) — CLOSED on evidence.** This finding was routed to `builder` and the fix landed, but nobody flipped it, so it has been inflating the open backlog. Closed here as bookkeeping, not as an orchestrator resolution of builder work — the citation in `resolution:` is the code or commit that contradicts the finding as filed. It was one of **10 stale-open** builder findings found this sweep (against **13 orphaned** ones that stay open); the lane's missing mechanism is **finding-0209**.
>
> **Residual, recorded not lost:** Optional residual the finding itself marked non-required: the stale "11 pre-rule" phrase survives at `bp-019/plan.md:95` and `bp-020/plan.md:62`.

## What

bp-020 §3 Q1 (and its Item 10 acceptance test, §7) and bp-019 §3 Q4 both assert: "11
pre-rule plans with no cost block (bp-000..010 — zero rows, zero errors)." Verified
against the corpus at this builder's HEAD, this is false: only **8** of bp-000..010 truly
have no `cost:` block at all (bp-000, 001, 002, 003, 004, 005, 008, 010). The other
**3** — bp-006, bp-007, bp-009 — DO carry a `cost:` block, with `estimate: null # pre-dates
the ledger rule` and a filled `actual:`. Confirmed via `git log`: all three blocks were
added by `ea3d8e8` ("docs(workflow): cost ledger in plan front-matter"), the SAME commit
that introduced the `cost:` frontmatter convention itself — its message states explicitly:
"Backfilled: bp-007/009 actuals (the first calibration rows), bp-006 honestly unmeasured,
bp-011..013 estimated." V3's read-only probe (dn-self-sensing.md §3.2) predates or missed
this backfill and its "11/zero" count was carried forward into both plans without
re-verification at graduation time.

The dry-run (Item 10, this session) surfaced this correctly and safely: `sync()` projected
bp-006/007/009 as three `actual`-only rows, zero parse warnings, deterministic across two
runs. The sensor did exactly what it should — it is the STATED BASELINE that is wrong, not
the code.

## Why it matters

Item 10's literal acceptance-test wording ("bp-000..010 contribute zero rows and zero
errors") is falsified as written by 3 of those 11 IDs — but the plan's own falsifier
("a sealed plan with a complete cost block yields no estimate/actual join") is NOT
triggered: bp-006/007/009 have no `estimate`, so they correctly yield no join, matching
the spirit of "pre-rule → no calibration signal," just not the letter of "zero rows."
Anyone re-running this inventory later (a consumer, a re-verification) who trusts the
"11/zero" figure literally would be surprised by 3 non-empty rows and might mistake it for
a sensor bug rather than a corpus fact already true at HEAD. The true zero-row set (8
plans) does hold exactly as stated — no rows, no errors, confirmed this session.

## Re-entry condition

None — not a blocker; resolved this session by re-grounding against the corpus directly
rather than trusting the plan's stale count. Flagging for the orchestrator: dn-self-sensing
§3.2 V3 and bp-019 §3 Q4's "11 pre-rule / zero rows" phrasing could be corrected to "8 true
zero-block + 3 backfilled actual-only (bp-006/007/009)" if either document is amended for a
future reader — not required for bp-020 to proceed, since Item 10's actual falsifier
(complete-pair-with-no-join) was never triggered.

## Routing

`spec-fidelity` — the builder (this session) resolved it directly: re-ran Item 10's dry-run
inventory against the TRUE zero-block set (bp-000,001,002,003,004,005,008,010 — 8 plans,
not 11) and confirmed it independently satisfies the falsifier (zero rows, zero errors,
deterministic). bp-006/007/009's 3 actual-only rows are recorded in the journal's fact
table honestly, not hidden or "fixed" to match the stale count. No plan file's Q1/V3 text
was edited (both are outside this plan's write_scope — bp-019/plan.md and the design note
are read-only inputs here); this finding is the record of the correction instead.
