# Domain-expert briefs — `.claude/agents/auditor-<domain>.md`

Capture lane for the owner's 2026-07-23 ruling: standing domain-expert briefs that an
auditor (or any specialist agent) inherits, so each run does not re-derive the same
context. The ruling could not be executed as written twice, because the briefs do not
exist — `.claude/agents/` holds only `builder.md` and `scribe.md`.

---

## 2026-07-25 — the ops-wave audit, run as the design experiment

Six auditors, cold-read, parallel worktrees, briefed inline. Full results:
`docs/audits/ops-wave-2026-07-25.md`. This capsule is the *design* harvest, not the
findings harvest.

### The converged structure

All six auditors independently proposed variants of the same shape. That convergence —
from six agents that could not see each other — is the strongest argument the run
produced for what a brief should contain:

```
1. Environment      — exact incantation in a fresh worktree; PYTHONPATH; known footguns
2. Domain contract  — subsystem invariants, and which are ENFORCED vs merely conventional
3. Production probes— the live artifacts to read-only-query, with the queries
4. Known hazards    — pre-existing defects, so REGRESSIONS are reported separately
5. Ritual           — quote falsifier verbatim → name test → state what it ACTUALLY
                      proves → mutate the specific guard → revert
6. Taxonomy         — the authoritative ftype set and routing table
7. Prohibitions     — no journal, no findings/ writes, no full suite
8. Dismissal list   — hypotheses already disproven, so they are not re-run
```

§2 and §4 are the two an inline brief cannot cheaply supply and a *standing* brief can.
That is the argument for standing briefs over inline ones, stated in evidence.

### §1 is not a nicety — it cost every auditor a round trip

Every one of the six lost time to the same environment facts. This is the cheapest,
highest-yield section:

- `uv run --extra dev pytest` — bare `uv run pytest` fails in a fresh worktree
- `uv sync --extra dev` is a required first step in a new worktree
- `PYTHONPATH=.` for ad-hoc probe scripts (package is not installed editable)
- `timeout(1)` does not exist on this macOS shell
- `pytest tests/unit` (subdirectory path) **mis-collects** — 36 errors; collect from root
- `cwd` resets between Bash calls in agent threads — absolute paths only
- `latexmk` needs `PATH=$PATH:/Library/TeX/texbin`; `docs/book/main.pdf` is gitignored
- artifact ids resolve by frontmatter `id:`, **not** by filename

### The mutation catalogue — the run's most transferable artifact

Proposed independently by four auditors, in compatible form. Organize §5 by defect class:

| mutation | what it falsifies | expected signature |
|---|---|---|
| revert-the-fix | "this ratchet is real" | the new tests fail |
| **blind-the-instrument** | "the meter measures the objective" | *nothing fails* ⇒ finding |
| break-the-escaping | "hostile input is handled" | syntax/injection error surfaces |
| delete-the-bound | `limit`/`k`/timeout is load-bearing | *nothing fails* ⇒ inert falsifier |
| no-op-the-operation | "the acceptance asserts an effect" | semantics suite fails |

**The rule that makes it work: if a mutation changes nothing, the falsifier is inert —
that is a finding, not a pass.** Two real defects this run were found exactly there
(bp-103's `limit(0)` rationale; bp-102's false-alarm guard).

**Blind-the-instrument is the new move.** No other check would have found bp-103's
overstated seal. A ratchet's credibility is a *joint* property of the assertion and the
meter, and builders self-report only the former.

### Named procedures worth promoting to doctrine

- **The tense test** — for every present-tense architectural assertion, open the cited
  §: *is it describing state or intent?* Migration plans, end-states, and M-gates are
  the reservoir. Both of bp-104's real defects came from this one generator: a ratified
  §-number cited correctly, with the *tense* of the claim inside it changed.
  Citation-*existence* checks are automatable; tense-fidelity is not, and is where
  invention actually hides.
- **The closure reflex** — when an invariant is phrased "no path exists" but the checker
  is per-file, build the graph. ~40 lines of AST walking found the `hvac` chain.
- **The three-ref ratchet sweep** — recompute any ratchet's metric at the previous
  edition ref, the plan's base, and HEAD; then grep whether monotonicity is *asserted*
  or merely *narrated*. Turned "the ratchet is red" into "the ratchet regressed and
  nothing noticed."
- **Build both states** — for any meter or gauge, construct the complementary state and
  diff the output. If the outputs match, the instrument has failed regardless of tests.
- **The read-only-verification recipe** — bare temp data dir → snapshot filenames → run
  the command → diff. Ten lines; proved `status` is not read-only.
- **The citation sweep** — resolve every `finding-\d+`/`bp-\d+`/`dn-*` reference in
  shipped source to its actual title. One loop caught ten wrong citations.
- **Enumerate every constructor of the changed class** — new in-object state is only safe
  if *every* construction site sets it.
- **A widened Protocol is a coverage regression until proven otherwise** — the new
  method's only test implementation is a fake *by construction*. Mechanical check: grep
  the fake's recording attribute; **written and never read ⇒ decorative seam.**

### Two structural proposals the run generated

**1. The two-axis verdict.** CLEAN/CONCERNS/SERIOUS cannot express "the code is right and
the seal overstates why" — which, given `completion-claims-honesty`, is exactly the
failure mode this repo most needs an auditor for. Adopt:

> `artifact: clean | concerns | serious` × `record: accurate | overstated | misleading`

bp-103 then reads **artifact: CLEAN / record: OVERSTATED**, which is the honest summary.

**2. The auditor's structural edge, named explicitly.** The auditor is often *outside*
the `write_scope` that stopped the builder. bp-103's auditor closed finding-0180's open
reachability question with one read-only probe the builder was structurally unable to
run. Standing permission belongs in the brief: **schema and count reads yes;
`add`/`update`/`delete`/`drop` never.**

### What the cold-read fence bought

Keep it, and keep the *reason* in the brief. bp-101's auditor:

> "F1 is precisely the thing a builder's own journal would have argued me out of — the
> builder's reasoning is internally airtight and only fails on an assumption stated
> nowhere in the diff."

**The strongest single signal of the run:** bp-101 and SEAMS converged on the same
defect from disjoint diffs with journals withheld. Independent convergence is evidence a
single reviewer structurally cannot produce, and it is the argument for N auditors over
one thorough one.

### Open questions for the owner

1. **One brief per domain, or per concern?** The run suggests domains
   (`auditor-scheduler`, `auditor-stores`, `auditor-ops`, `auditor-scribe`) because §2
   and §4 are domain-shaped. But the *ritual* (§5) is identical across all six — argues
   for a shared `auditor-base.md` plus thin domain overlays.
2. **Who maintains §4 (known hazards) and §8 (dismissals)?** They rot fastest and are
   worth the most. Candidate: `/triage` appends to them as findings resolve.
3. **Does the builder get the mutation catalogue too?** Every instrument-blindness
   defect would have been caught pre-seal if the builder ran blind-the-instrument on its
   own meter. Arguably §5 belongs in `builder.md` as a *self*-check, with the auditor
   verifying it was run.
4. **Cost.** Six auditors ≈ 680k tokens, ~9 min wall-clock each in parallel. Weekly moved
   7% → ~11%. Right-sizing question: is SEAMS-only a viable cheap mode for small waves?
   The run says the seam auditor found the most per token.
