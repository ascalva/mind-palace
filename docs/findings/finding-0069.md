---
type: finding
id: finding-0069
status: routed
created: 2026-07-13
updated: 2026-07-13
links:
  - docs/build-plans/bp-023/plan.md
  - docs/build-plans/bp-023/journal.md
  - tests/e2e/conftest.py
ftype: discovery
origin_plan: bp-023
route: orchestrator
resolution: null
---

# The live-test lock is correct, but Item 13's proof still flakes — the wider contention is machine-wide RAM pressure across sibling worktrees, not endpoint-level

## What

bp-023 Item 12's endpoint-keyed `fcntl.flock` fixture (`tests/e2e/conftest.py`) was built
and independently verified correct: a server-log cross-reference (matching the real
model weight-blob hash, not the shorter digest `ollama list` shows) during a clean
two-process race (journal "run 3") shows exactly ONE `"loading model via llama-server"`
event for the contended model during the whole race window — i.e. the two processes in
THIS worktree never both hit the endpoint concurrently; the lock serialized them as
designed.

However, Item 13's literal acceptance test ("two concurrent
`uv run pytest -m live -k <test>` processes both pass") did NOT hold on two of four
attempts (journal "run 1" and "run 4") — both processes failed with a `TimeoutError`
inside `OllamaClient.load()` (the control-plane `request_timeout_s`, 120s), with a
~120s gap between the two processes' finish times (t≈122s / t≈242s) — the exact
signature CORRECT serialization produces when the endpoint is simply too slow to answer
within one client timeout, not what a broken/no-op lock would produce (which would show
both processes finishing around the same t, racing the endpoint simultaneously).

The root cause, found directly in `~/.ollama/logs/server.log` at the failure window, is
NOT endpoint contention between this worktree's two live tests — it's a scheduler-level
memory eviction stall: `"llama-server model predicted to exceed available memory,
evicting" predicted="5.8 GiB" ... available="3.2 GiB" ... system_free="3.2 GiB"
system_limited=true`. `top -l 1 -n 0` at the same moment showed `PhysMem: 31G used (19G
wired, 1949M compressor), 295M unused` — i.e. the physical machine was nearly out of
RAM. `ps aux` at the same instant showed two OTHER, unrelated sibling builder worktrees
(`agent-a0ad3880303482f76`, `agent-a2d9a8f009e88308e`) both actively running their own
full `pytest -q` gate suites concurrently (32.8% and 91.6% CPU) — competing for the same
physical machine's memory, entirely independent of bp-023's single-worktree,
endpoint-keyed lock (their worktrees don't carry this uncommitted fixture at all).

This is the plan's own §10 stop condition, fired exactly as specified: *"If the
two-process proof still flakes WITH the lock held, STOP: the contention is not solely
endpoint-level."*

## Why it matters

The live-test flake class (finding-0046, finding-0048, bp-018's cross-suite evidence) was
modeled as **cross-process, endpoint-level** contention — fixed by serializing access to
the Ollama endpoint. That model is confirmed correct as far as it goes (Item 12's lock
demonstrably prevents two live tests in one worktree from racing the endpoint). But the
owner's delegated-builders-mode (parallel worktrees on one physical machine, each running
independent live/e2e suites against the SAME shared local Ollama daemon) introduces a
**second, wider contention axis this plan cannot reach**: whole-machine RAM pressure from
concurrent SIBLING worktrees, each of which would need to carry (or share) the same lock
for it to serialize machine-wide. A single-worktree `write_scope` (per this plan, and per
scope-guard generally) cannot install a lock that spans worktrees it isn't allowed to
write to.

Left unaddressed, the live-flake tax persists whenever multiple builders are delegated in
parallel (the owner's now-standard mode, per the delegated-builders-mode memory) and
their live/e2e suites happen to overlap — exactly the bp-018 scenario this plan's own
context manifest (§2 item 3) cites as evidence the contention is cross-process. bp-023
narrowed that correctly to "cross-process within reach of one write_scope"; the residual
is "cross-process across builder worktrees," a genuinely different resource-scheduling
question (shared machine capacity, not shared test-infra) — a `direction`-level call: does
the framework need a machine-global (not repo-scoped) lock file, a scheduler-side rule
("no two delegated builders run `-m live` concurrently"), or is the existing
"re-run before investigating" mitigation (finding-0046) the accepted cost of the
delegated-parallel-builders mode for the live tier specifically?

## Re-entry condition

The orchestrator (or a future design note under `docs/design-notes/`) decides whether:
(a) a machine-global lock (outside any single worktree's `write_scope` — e.g. a
scheduler-level or `~/.ollama`-adjacent convention) is warranted, keyed the same way
(endpoint hash) but shared across worktrees; or
(b) the delegate skill / delegation-budget-discipline gets a rule against scheduling
concurrent `live`-marked suites across parallel builders (i.e., a policy fix, not a code
fix); or
(c) the residual is accepted as the documented cost of delegated-parallel-builders mode
for the live tier, and finding-0046's "re-run before investigating" fallback is the
permanent answer for this specific cross-worktree case (Item 12's lock remains the fix
for the *originally modeled* class — one worktree's live tests racing each other, or a
builder's suite overlapping the orchestrator's own gate run in the SAME checkout).

Until decided: Item 13's literal "both processes pass" acceptance is satisfied by the
plan's own alternate clause instead (§6(b): "or that the endpoint windows are provably
disjoint") — met via the run-3 server-log cross-reference in
`docs/build-plans/bp-023/journal.md`. This does not block bp-023 from proceeding to the
green gate and merge; Item 12's fixture is correct and complete on its own terms.

## Routing

`discovery`, routed to the orchestrator — this is a scheduling/policy question spanning
multiple builder worktrees, outside any single plan's `write_scope` and outside a
builder's authority to resolve unilaterally (it may warrant a design-note amendment to
the delegate skill, or simply an owner-acknowledged fallback). Not a blocker: bp-023's own
work (Items 12–13, as scoped) is complete and independently verified; this finding
documents the residual class for the next /triage.

**Batched to `docs/inbox/owner-questions.md` oq-0018 (orchestrator, 2026-07-13).** The
(a) machine-global lock / (b) scheduler-delegate policy / (c) accept-the-fallback call is
the owner's; default-if-unanswered is (c) — Item 12's lock stands for the originally-modeled
class and the CI gate never runs live tests, so the residual does not gate merges. bp-023
sealed at the wave boundary regardless (Item 12 correct; Item 13 met via §6(b)'s alternate
disjoint-window acceptance). Ironic provenance worth noting: this session's own
parallel-builder decision produced the RAM pressure that exposed the wider axis.
