---
type: finding
id: finding-0151
status: open
created: 2026-07-21
updated: 2026-07-21
links:
  - docs/design-notes/code-ingest-pipeline.md          # §2.5b / §2.3-1 — the code→dialogue authorship channel
  - docs/design-notes/agentic-loop.md                  # §2.4b / G-E — the C-fiber, thin; the integrator's home
  - docs/design-notes/agent-taxonomy.md                # §2.5 — the integrator / witness law
  - docs/findings/finding-0111.md                      # the commit-diff resolution boundary (why C is commit-thin)
  - docs/findings/finding-0141.md                      # the C-fiber thinness / built-not-wired precedent
  - docs/build-plans/bp-093/plan.md                    # PD-J pulled here
ftype: design
route: orchestrator
resolution: null
---

# The code→dialogue authorship channel is integrator-gated — a proper integrator design pass is required, and it completes the code-ingest program

## The gap (verified 2026-07-21)

`code_origin` (the PD-J reader that answers "which conversation wrote this code version")
joins a code chunk's blob → its commit → the C-edge witnessing that commit. But the
integrator mints C-edges **directly from L1 events** and, by design (finding-0111), refuses
to fan a commit out to its changed-file set — so it produces only **78 commit-anchored edges
(`pair_cut_sha` set) of 4,160**; the other ~4,082 are `file`/`doc` working-tree writes with
`pair_cut_sha=''` (no commit anchor). The join therefore resolves for almost nothing.

Neither available path is adequate:
- **commit-join** (78 edges): version-precise but sparse → useless coverage;
- **file-join** (4,082 edges): dense but *file-grain and version-blind* (which turns ever
  wrote this file, not which turn wrote this blob).

Useful authorship needs **dense AND version-grain** resolution, which requires a capability
nobody built: capture each commit's **diff** (`git diff-tree`, cheap, currently uncaptured —
the ledger stores full trees, finding-0111) and/or **blob-tag** the write edges, then compose
`action→commit ∘ commit→changed-blob`. The integrator's own docstring already names this
composition as "Δ's `ComposedGraph` job" — but the edges to compose against don't exist.

## Owner ruling (2026-07-21)

1. **Option 2 only:** the PD-J `code_origin` reader is **PULLED from bp-093** (done —
   bp-093 §0); shipping it thin is rejected.
2. **A proper integrator design pass is required** — investigate the best way to build the
   integrator that makes dense, version-grain dialogue→code resolution real (commit-diff
   capture vs blob-tagged writes vs both; the ComposedGraph composition; schema). This ALSO
   fixes the general C-fiber thinness (bp-080 census came back empty; finding-0141).
3. **It must complete WITH the code-ingest program** — the code ingestion is NOT "done"
   until code→dialogue authorship actually works; the integrator densification is part of
   its definition-of-done, not a deferrable sibling.
4. **Sequencing / tier:** the design pass runs at **Fable** (main orchestrator re-tiered),
   **AFTER the current build tracks** (K-wave + CI-1/3/4). Recorded so it is not started at
   the wrong tier or ahead of the builds.

## Re-entry / next step

After the build tracks land: switch the orchestrator to Fable → a rigorous design pass
(capture → design note → owner ratify → graduate) on the integrator, scoped so its build
plans join the code-ingest program's completion. Until then this finding holds the ruling.

## Routing

`design` → orchestrator. Warrant for the PD-J pull (bp-093) and the future integrator note.
