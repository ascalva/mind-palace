# Brainstorm — scoped context queries: the palace as its own onboarding organ

> Captured by the orchestrator from owner chat (2026-07-28, bg session, fable), minutes after
> the resume-brief-as-trauma-vector capsule and the distributed-ecosystem capture — this seed
> completes both. Third onboarding regime: brief (push) → traversal (pull, manual) → query
> (pull, through the system's own retrieval).

## 2026-07-28T03:20Z (bg orchestrator session)

### The seed

Owner, near-verbatim: *"the agent can be dropped in the project with the skills required to
query ouroboros for scoped context — via the query. Let's say: how could you translate this
question such that it is a valid, well-bounded query? Lessons learned are recorded and inform
future design."* Sharpened moments later: *"the query that acts on a true database — a query
of scoped knowledge."*

### Orchestrator scrutiny (chat-side — connections offered, not decided)

- **The dogfood moment.** The system built to answer "what does it mean to know why you
  believe something" becomes the context provider for the agents building it. A fresh session
  doesn't inherit a predecessor's state and doesn't hand-walk the tree — it asks the corpus,
  and the corpus answers with provenance.
- **A question compiles to three bounds.** "Valid, well-bounded" = (semantic, temporal,
  authority): *what about* (strata + fiber selection), *when* (time window / clock), *what
  counts* (status and provenance tier — ratified vs draft vs finding-open). Worked example,
  the onboarding question itself:

      question: "where is the project headed?"
      query:
        strata:   [design-notes, findings, brainstorms]
        status:   [ratified, open]        # authority bound
        window:   last 14 days            # temporal bound
        rank:     recency × centrality
        k:        12 atoms, grouped by source digest (sourceset relation)
        return:   (path, digest, status, Σ) per atom — never bare text

- **A true database query — not retrieval-with-vibes.** The owner's sharpening demotes
  semantic search to *one operator inside a query plan*: similarity is a predicate alongside
  `status IN (...)`, `ts > ...`, fiber membership — evaluated relationally, deterministically,
  against typed strata. Three consequences. (1) **Determinism**: same query + same corpus
  state → same answer; the answer is auditable and the study stays checkable. (2) **The query
  is a replayable artifact**: it is text, text is corpus; re-run yesterday's query against
  today's corpus and *diff the answers* — answer-drift becomes a measurable instrument, the
  formal version of "true recall." (3) **Loud failure**: a bounded query whose bounds exclude
  the answer returns empty, visibly — never a silent nearest-neighbor mush that *looks* like
  an answer. And this is not aspiration: the store already sits on LanceDB + DuckDB — the
  database is physically there; only the surfaced query language is missing.
- **read_scope becomes literal, not metaphorical.** If scoped knowledge is a relation, a
  role's read_scope is a *view definition*, and granting context is `GRANT SELECT ON <view> TO
  <role>` — the capability discipline inherits fifty years of database authority machinery
  instead of inventing its own (DRY at the architecture level).
- **The authority bound is the trauma lesson applied to reading.** The brief's failure was
  affect without warrant. A query that omits the authority bound reproduces it — pulling
  draft fears as if ratified truth. Every returned atom carries its status flags; unwarranted
  vigilance cannot masquerade. Retrieval inherits the warrant discipline.
- **read_scope is write_scope's dual.** We already treat writing as a capability
  (scope-guard). This proposes scoped *reading* as a first-class declaration: a plan or agent
  role could pre-declare its context bounds the way it pre-declares write_scope. Same
  algebra, third client (after the dreamer's dispatch scopes and the effector MirrorView
  tailoring): a scope-parameterized query is what a role IS, on the read side.
- **The lessons loop is the design payload.** Each (natural question → compiled query →
  sufficiency verdict) triple is typed exhaust. A translation that failed — wrong strata,
  window too tight, authority tier that starved the answer — is a finding. The query log
  becomes a sensor: which strata actually serve which roles, measured, feeding retrieval
  design. The system learns *why* a context request succeeded — warrant, applied to its own
  memory access.
- **The wiring gap, named honestly (wiring-is-part-of-finishing).** Core has the machinery
  (`grouped_semantic_search`, the sourceset relation, 22k+ vector rows). The agent-facing
  surface does not exist: `palace.py` usage shows no `query` subcommand. The buildable unit
  this seed implies is exactly that ON switch — a `palace query` (or equivalent read-only
  surface) plus a project skill (`/context <question>`) that owns the translation, so agents
  invoke the compiler rather than hand-rolling queries. Read-only: the model advises, code
  acts; this surface only ever returns data.
- **Ecosystem hook.** The query surface is an individual's public face. A sibling instance or
  remote principal meets an Ouroboros *only* through scoped queries answered with pointers
  and provenance, never corpus (NN-11). Onboarding-by-query locally and
  inter-instance-contact remotely are the same interface at two trust tiers — maximum
  skepticism just tightens the authority bound.

```capsule
topic: scoped-context-queries
date: 2026-07-28

decisions:
  - Frame adopted: fresh-agent context acquisition moves from traversal toward scoped
    queries against the corpus; a question compiles to (semantic, temporal, authority)
    bounds; answers always carry provenance + status, never bare text.
  - Lessons learned are first-class: failed translations are findings; the query log is a
    sensor that informs retrieval design.

parked:
  - decision: building the agent-facing query surface (`palace query` + a /context skill)
    default: agents onboard by traversal of the artifact chain (the current regime)
    re_entry: owner rules where this graduates — its own design note, or an item under an
      existing retrieval/interface note
  - decision: read_scope as a declared field in the build-plan template
    default: plans declare write_scope only; reading stays unbounded
    re_entry: the query surface above exists and its logs show what roles actually read

open_questions:
  - Who issues the sufficiency verdict on a translation — agent self-report, or a mechanical
    proxy (did it re-ask / fall back to traversal within the session)?
  - What artifact type holds a query-lesson — a finding ftype, or a new exhaust lane the
    curator digests?
  - Does the temporal bound use wall clock or the strata/event clocks
    (temporal-clocks-and-strata)?
  - Is the /context skill itself versioned corpus content, so instances can evolve their own
    translation layer — and drift in it is measurable?

next_steps:
  - Owner rules the graduation home (this note is ready to seed one).
  - Until then: nothing wired; Ouroboros revival and green main stay ahead of it in line.

references:
  - docs/brainstorms/synchronic-diachronic-dreamer.md (scope algebra; the 2026-07-28
    trauma-vector capsule this completes)
  - docs/brainstorms/the-distributed-ecosystem.md (the query surface as an individual's face)
  - docs/brainstorms/retrieval-and-temporal-scaling.md
  - docs/brainstorms/per-directory-readme-as-local-context.md
  - docs/brainstorms/temporal-clocks-and-strata.md
  - core/stores/sourceset.py (grouped_semantic_search — the machinery half, already built)
  - finding-0146 (code is vectorized — code context flows through the same channel)
```
