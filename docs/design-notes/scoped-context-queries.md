---
type: design-note
id: dn-scoped-context-queries
track: workflow          # how agents acquire context is how work moves; kin: dn-role-state-and-scoped-handoff
status: draft            # draft → ratified → superseded.  draft→ratified is an OWNER-ONLY hand edit.
created: 2026-07-28
updated: 2026-07-28
links:
  - docs/brainstorms/scoped-context-queries.md          # THE WARRANT — owner seeds 2026-07-28T03:20Z + chat-side scrutiny (whole file)
  - docs/brainstorms/the-distributed-ecosystem.md       # 05:07Z capsule — the query plan as privacy compiler (the jurisdiction duty)
  - docs/brainstorms/synchronic-diachronic-dreamer.md   # 02:54Z the brief retired; 05:34Z+ scope-sweep grading, the union bound (the epistemic duty)
  - docs/design-notes/capability-scope-algebra.md       # RATIFIED — the (Σ,E,T,A) lattice this note compiles INTO, never beside
  - docs/design-notes/temporal-retrieval-algebra.md     # RATIFIED — π_active/σ_*/σ^*; the temporal bound's math home, built on, never re-derived
  - docs/design-notes/agent-taxonomy.md                 # RATIFIED — role = scope signature; the query-agent row this note reads A from
  - docs/design-notes/core-query-protocol.md            # RATIFIED — every core reader a capability-scoped client of one protocol
supersedes: null
superseded_by: null
warrant: docs/brainstorms/scoped-context-queries.md
---

# Scoped context queries — the corpus as its own onboarding organ

> Filed by the chat agent as `draft` (chat-side protocol, §8). Ratification is a
> hand edit by the owner — no command performs it, and `gate-guard` denies any
> agent attempt (§10). `/graduate` refuses this note until `status: ratified`.
>
> Composed at **fable** (`claude-fable-5`, 2026-07-28) from the warrant capsule and the two
> sibling threads' 2026-07-28 capsules. Chat-frame "decisions" in those capsules are restated
> here as **proposals**; every ratification is the owner's alone. Two sibling notes are being
> drafted in parallel PRs — **dn-prediction-castles** (the dreamer's castle/grading complex)
> and **dn-distributed-ecosystem** (panic-seals, envelope encryption, node federation) — and
> this note owns one definition they both cite: the authority bound (§2.4).

## 1. Purpose and scope

### 1.1 What this note decides

The owner's seed, near-verbatim (2026-07-28T03:20Z): *"the agent can be dropped in the project
with the skills required to query ouroboros for scoped context — via the query. Let's say: how
could you translate this question such that it is a valid, well-bounded query? Lessons learned
are recorded and inform future design."* Sharpened moments later: *"the query that acts on a
true database — a query of scoped knowledge."*

This note makes that seed well-posed in the ratified family's vocabulary. It decides:

1. **The third onboarding regime (§2.1):** brief (push — retired 2026-07-28) → traversal
   (pull, manual — the current regime) → **query** (pull, through the system's own retrieval).
   The regime serves fresh agents locally and, per the ecosystem thread, fresh **nodes**
   remotely — one interface at two trust tiers.
2. **The compilation target (§2.2):** a natural question compiles to the three bounds
   (semantic, temporal, authority) — and each bound is a *reading of the ratified
   `dn-capability-scope` lattice* (`s = (Σ, E, T, A)`), never a parallel algebra. The
   authority bound is decided to be a **Σ-refinement reading**, not a new axis (§2.2.2).
3. **True-database semantics (§2.3):** deterministic, replayable, loud on absence; similarity
   demoted to one operator inside a real query plan.
4. **The authority bound's three duties (§2.4):** trust tier, jurisdiction, epistemic status —
   one axis, three loads, all surfaced in one night (2026-07-28). This note owns the axis's
   definition; the sibling notes cite it.
5. **read_scope as write_scope's dual (§2.5):** a view definition; granting context is
   grant-select on the view; plans and roles may pre-declare read_scope.
6. **The lessons loop (§2.6):** (question → compiled query → sufficiency verdict) triples as
   typed exhaust; failed translations are findings; the query log is a sensor.
7. **The wiring deliverable (§4):** a `palace query` verb plus a `/context` translation skill
   are part of any eventual build — gated off is fine; absent is not (the
   wiring-is-part-of-finishing rule, owner 2026-07-22). This note SPECIFIES; it builds nothing.

### 1.2 Non-goals

Explicit, because wrong non-goals fail silently forever (finding-0150 — the projection-note
lesson: an inferred out-of-scope clause must carry its marker for the ratification gate).

- **No build.** Owner-stated: *"nothing wired; Ouroboros revival and green main stay ahead of
  it in line"* (warrant capsule, next_steps). Graduation follows ratification.
- **Traversal stays the default regime** until the owner rules enablement. Owner-stated (the
  warrant capsule's parked default: "agents onboard by traversal of the artifact chain").
- [INFERENCE] **No new retrieval mathematics and no parallel scope algebra.** The temporal
  bound's math home is `dn-temporal-retrieval-algebra` (π_active/σ_*/σ^*, the K(β) retrieval
  curve); the scope type is `dn-capability-scope`. This note compiles into them and re-derives
  nothing.
- [INFERENCE] **Not the encryption/deployment architecture.** Panic-seals, envelope
  encryption, the skeleton/payload schema audit belong to dn-distributed-ecosystem; this note
  takes only the jurisdiction duty's *definition* (§2.4).
- [INFERENCE] **Not the castle lifecycle or grading machinery.** TTL leases, the castle state
  machine, registration metrics belong to dn-prediction-castles; this note takes only the
  epistemic duty and the union bound's legality conditions (§2.4).
- [INFERENCE] **Not a conversational surface.** A scoped context query returns typed atoms
  with provenance, never synthesized prose; prose belongs to the model that consumes the
  atoms (the Ambassador's lane, untouched).
- [INFERENCE] **No firewall change.** `MIRROR_READABLE` defaults, the foundation denylist 𝔇,
  and every ideal of `dn-capability-scope` §2.2 bind this surface exactly as they bind every
  other reader. The query surface *inherits* the boundary; it never widens it.

## 2. Principles / decision

### 2.1 The third onboarding regime

The resume-brief was retired 2026-07-28 (`synchronic-diachronic-dreamer` 02:54Z capsule): a
brief is episodic memory passed off as semantic memory — *"a belief stripped of its Σ"* (Σ here
in the warrant sense of `dn-scored-beliefs-and-earned-entitlement`, draft: a belief's support
set). Successors inherited posture without the experience that earned it. What replaced it is
traversal: a fresh session walks the typed artifact chain by hand. That works — the corpus is
easily traversable by design — but it is manual, unmeasured, and its cost grows with the
corpus.

The third regime is **query**: the fresh agent asks the corpus, and the corpus answers with
provenance. The dogfood moment is deliberate — the system built to answer "what does it mean
to know why you believe something" becomes the context provider for the agents building it.
And per the ecosystem thread, the same surface is an individual's **public face**: a sibling
instance or remote principal meets an Ouroboros *only* through scoped queries answered with
pointers and provenance, never corpus (NN-11 — the non-negotiable "the interface may transit a
third party; the corpus never does"). Onboarding-by-query locally and inter-instance contact
remotely are the same interface at two trust tiers; maximum skepticism just tightens the
authority bound.

### 2.2 The compilation target — a question compiles to a scope

*"Valid, well-bounded"* = the question compiles to three bounds: **semantic** (what about),
**temporal** (when), **authority** (what counts). The decision this section makes: those
bounds are not a new formal object. They are a *reading* of the ratified scope lattice
`s = (Σ, E, T, A)` (`dn-capability-scope` §2.1) — the compiler's target type already exists.

#### 2.2.1 Semantic and temporal bounds — direct readings

- **Semantic bound → Σ and E.** Strata + fiber selection is exactly the stratum-scope
  component Σ (a downward-closed subset of the refinement forest R) plus the edge-class scope
  E. The similarity predicate is the *kernel-carrying* part of the scope — and by the ratified
  mode-corollary (`dn-capability-scope` §2.4: "mode is a corollary of scope, never a flag"),
  kernel-carrying Σ is what *makes* a query semantic. Similarity is thereby demoted by type:
  one predicate among peers, not the retrieval (§2.3).
- **Temporal bound → T = (clock κ, window W), verbatim.** The ratified T component is the
  temporal bound's formal home, already built for this: wall-time is an exogenous labeling,
  never an event clock; a point window applies `π_active(anchor)` ambient; an interval window
  evaluates `σ_*`/`σ^*` transports with declared direction (`dn-temporal-retrieval-algebra`
  §2.2, anchor-indexed per `dn-capability-scope` §2.1). A chat-side "last 14 days" is
  therefore *sugar that must resolve to a materialized clock window* — canonically
  `(commit, [c₋₁₄d, HEAD])` for repo-backed strata — and a multi-stratum window must carry a
  consistent cut (the SLICE rule; the commit SHA is the cut for repo-backed strata). The
  warrant capsule's open question "wall clock or strata clocks?" is thus already half-ruled by
  the ratified family: clocks, not wall time; the residue (which clock per question) is parked
  as SQ-c.

#### 2.2.2 The authority bound — a Σ reading, NOT a new axis (the mapping decision)

The warrant's word "authority" collides with the lattice's fourth component A — and the
collision must be resolved explicitly, because inventing a parallel algebra is the one failure
this family does not forgive. Decision:

- **The lattice's A is untouched.** A = P × W_Σ × W_world is *holder* authority — what the
  scope-holder may DO. Every scoped context query runs at the query-agent signature
  `A = (READ, W_Σ=0, W_world=NONE)` (`dn-agent-taxonomy` §2.1 — the query agent "reads the
  graph, answers, writes nothing structural"). A is a constant of this surface, never a
  compilation output.
- **The authority bound is a refinement-family reading of Σ.** "What counts" — ratified vs
  draft vs finding-open, evidence vs castle — selects *which refined strata the query reaches*.
  The ratified refinement forest R already holds refinements as first-class lattice
  *elements*, not annotations (`reference_repo ⊂ reference`, `mirror_authored ⊂ mirror` —
  `dn-capability-scope` §2.1). This note proposes the same move one dimension over: **status
  predicates are refinement elements** (`design_notes@ratified ⊂ design_notes`,
  `findings@open ⊂ findings`), and the **castle realm is a refinement below the existing
  `interpreted` base stratum** (per the dreamer thread: the castle is "an interpretive stratum
  with its own authority tier"). Additive lattice extension; no new component; meets, joins,
  ideals, and the delegation law apply unchanged.
- **Jurisdiction is an annotation on the compiled plan, not a lattice element** — following
  the ratified precedent exactly ("enforcement tier is an annotation, never a lattice
  element," `dn-capability-scope` §2.2). Each predicate of a compiled plan carries an
  evaluation locus: host-evaluable (plaintext skeleton) or core-evaluable (decrypted payload).
  §2.4 gives this its content.

Vocabulary ruling for the family: the vernacular "authority bound" survives as the *name* of
this Σ-selection-plus-result-discipline; the symbol A keeps its ratified meaning. Where
ambiguity threatens, write Σ_status for the refinement family.

#### 2.2.3 Worked example

The owner's worked example (warrant, kept verbatim as the chat-side form):

    question: "where is the project headed?"
    query:
      strata:   [design-notes, findings, brainstorms]
      status:   [ratified, open]        # authority bound
      window:   last 14 days            # temporal bound
      rank:     recency × centrality
      k:        12 atoms, grouped by source digest (sourceset relation)
      return:   (path, digest, status, Σ) per atom — never bare text

Compiled into the ratified type (the form this note adds):

    scope s:
      Σ:  design_notes@{ratified} ⊔ findings@{open} ⊔ brainstorms      # semantic ∧ authority: refinement selection in R
      E:  {F}                                                          # citation fibers, for the centrality term
      T:  (commit, [c₋₁₄d, HEAD]), direction = σ^* (backward)          # "last 14 days" resolved; cut = commit SHA (SLICE)
      A:  (READ, 0, NONE)                                              # constant — the query-agent signature
    plan:
      WHERE stratum ∈ Σ ∧ status per refinement                        # host-evaluable   (skeleton)   ─ jurisdiction
        AND tick ∈ W on clock κ                                        # host-evaluable   (skeleton)   ─ annotations
        AND sim(q̂, ·) ranks among top-k                                # core-evaluable   (payload)    ─ per predicate
      RANK  recency × centrality;  k = 12 chunks, grouped by digest    # SourceSet grouping (§2.3)
      RETURN (path, digest, status, provenance, realm) per atom        # never bare text (§2.4, duty 1)

The `return` line's `Σ` in the owner's form is the *warrant* sense (the atom's support), not
the scope component — the compiled form spells the fields out to keep the two Σ senses apart.

### 2.3 True-database semantics — not retrieval-with-vibes

The owner's sharpening — *"the query that acts on a true database"* — demotes semantic search
to one operator inside a query plan: similarity is a predicate alongside `status IN (...)`,
`tick ∈ W`, fiber membership, evaluated relationally against typed strata. Three consequences,
each a falsifiable property (§5):

1. **Determinism.** Same query + same corpus state → same answer. The answer is auditable and
   the study stays checkable (study-not-product, applied to retrieval).
2. **The query is a replayable artifact.** A query is text; text is corpus. Re-run
   yesterday's query against today's corpus and *diff the answers*: **answer-drift becomes a
   measurable instrument** — the formal version of the dreamer thread's "true recall."
3. **Loud on absence.** A bounded query whose bounds exclude the answer returns **empty,
   visibly** — never a silent nearest-neighbor mush that *looks* like an answer. An empty
   result with tight bounds is information: the bounds were wrong, or the corpus is (a
   §2.6 lesson either way).

And this is not aspiration — the database is physically there; only the surfaced query
language is missing. Verified seams (correcting the warrant's path, which cites a pre-move
location): the source-set relation and `SourceId` type live at `core/kernel/stores/sourceset.py`
("a source object IS the set of its idea-vectors"); `grouped_semantic_search` exists at
`core/ingest/index.py:131` (opt-in source-grained retrieval, flat path untouched,
`MIRROR_READABLE` default); the vector store sits on **LanceDB**
(`core/stores/vectorstore.py`, typed shim `core/typedshims/lancedb.py`); **DuckDB** already
serves the telemetry and structural-snapshot stores (`core/stores/telemetry.py`,
`core/complex/temporal.py`). Determinism has one honest caveat carried as parked SQ-d: it
holds trivially under exact scan at today's scale; an approximate index at future scale makes
"corpus state" include the index snapshot, or the claim dies.

### 2.4 The authority axis's three duties — one axis, three loads, measured in one night

All three surfaced 2026-07-28, in three threads that did not know about each other — the
capsule's own words: *"the authority bound now serves three duties in one night... It is
becoming the load-bearing dimension of the whole design and should be treated as such at
graduation."* This section is that treatment. The definition lives here; the siblings cite it.

1. **Trust tier — retrieval hygiene** (this note's warrant). The brief's failure was affect
   without warrant; a query that omits the authority bound reproduces it — pulling draft fears
   as if ratified truth. The law: **atoms return with status, provenance, and their
   Σ-coordinates attached — never bare text.** Unwarranted vigilance cannot masquerade,
   because every returned atom says what it is and where it stands. Retrieval inherits the
   warrant discipline.
2. **Jurisdiction — where a predicate may be evaluated** (dn-distributed-ecosystem, 05:07Z:
   the query plan as privacy compiler). Under envelope encryption the relational SKELETON
   (ids, edges, strata, status, timestamps) stays host-visible; every payload column is
   ciphertext. The three bounds split exactly along this line: **temporal + authority bounds
   evaluate host-side on the plaintext skeleton; the semantic bound evaluates only in-core,
   after decryption.** One query, two jurisdictions — and the compiler that translates a
   question into bounds is the same machinery that decides what the host is allowed to
   compute. The skeleton/payload column audit and the vector question (payload by default,
   fail-closed) are the sibling's; the duty's definition is this note's.
3. **Epistemic status — prediction vs evidence** (dn-prediction-castles' thread, 05:34Z+).
   Grading a dreamer's forecast is **scope-sweep**: hold Σ_semantic and T fixed, sweep the
   authority bound — `q(s, t, castle)` returns the predicted thread, `q(s, t, evidence)`
   returns what happened, and the prediction error is the difference of the two projections.
   The **union bound** {warranted, interpretive} is legal only under three conditions: (i) it
   is explicitly requested; (ii) every atom carries its **realm tag** — duty 1's
   never-bare-text law is exactly what makes the union non-contaminating; (iii) the castle is
   built in the **same coordinate system** as the corpus — same embedding space, same strata
   clocks, different authority tier. Same base space, different fiber: comparison is
   projection, never translation. The grading machinery, lifecycle, and registration metrics
   are dn-prediction-castles'; the bound's legality conditions are this note's.

The three duties are one axis because all three are the same operation — *selecting which
epistemic standing a reader is exposed to* — applied to hygiene, to cryptographic reach, and
to dream-space. That triple load is why the axis is defined once, here.

### 2.5 read_scope is write_scope's dual

Write discipline is already a capability, not a suggestion (`scope-guard`; CLAUDE.md). This
note proposes the read side: **if scoped knowledge is a relation, a role's read_scope is a
view definition, and granting context is `GRANT SELECT ON <view> TO <role>`** — the capability
discipline inherits fifty years of database authority machinery instead of inventing its own
(DRY at the architecture level, the owner's standing strictness).

The ratified family already carries the type: a role IS a scope signature
(`dn-agent-taxonomy` §2.1), and the admissibility law — a grant is admissible iff
`s ⊓ ι = ⊥` for every applicable firewall ideal ι (`dn-capability-scope` §2.2) — is precisely
grant-time view authorization. What this note adds is the *declaration surface*: a build plan
or agent role may pre-declare its read_scope the way it pre-declares write_scope, making the
fresh-agent test mechanical — a session's context acquisition becomes a replayable set of
scoped queries against a declared view, instead of an unbounded walk. Same algebra, third
client (after the dreamer's dispatch scopes and the effector MirrorView tailoring). Default
and gate are parked as SQ-b: reading stays unbounded until the query log (§2.6) shows what
roles actually read.

### 2.6 The lessons loop — the query log is a sensor

*"Lessons learned are recorded and inform future design"* (owner seed). Each
**(natural question → compiled query → sufficiency verdict)** triple is typed exhaust. A
translation that failed — wrong strata, window too tight, an authority tier that starved the
answer — is a **finding**, entering design through the same gate everything else does. The
query log becomes a sensor: which strata actually serve which roles, measured, feeding
retrieval design. The system learns *why* a context request succeeded — warrant, applied to
its own memory access. Answer-drift (§2.3, replay-and-diff) is the same log read
diachronically. Who issues the sufficiency verdict, and which artifact type holds a
query-lesson, are carried as open questions (owner rules at graduation).

## 3. Consequences

What this note licenses **on ratification** (nothing before):

1. **One graduation: the query-surface build.** The three-bound compiler (a read-only module;
   the graduating plan pins its home — the TA-d precedent `core/temporal/` vs `core/query/`
   applies), the `palace query` verb, the `/context` skill, and the query-log lane — §4's
   wiring in write_scope, per the wiring-is-part-of-finishing rule. *Falsifier at build: any
   surfaced atom without status/provenance/realm tags, or a nondeterministic replay at fixed
   corpus state.*
2. **The sibling notes cite this axis.** dn-prediction-castles consumes the epistemic duty
   and the union bound's legality conditions; dn-distributed-ecosystem consumes the
   jurisdiction duty and the never-bare-text law at the federation boundary. Neither
   re-defines the bound.
3. **The build-plan template may gain `read_scope`** (parked SQ-b) — the taxonomy's
   signatures become per-plan declarations once the log shows what roles read.
4. **Node onboarding is free.** When the ecosystem thread graduates, a fresh node's first
   contact is this same surface with a tightened authority bound — no second interface to
   design (NN-11 intact: pointers and provenance cross the wire; the corpus never does).

## 4. Wiring & enablement

**How it wires:** the wiring gap is named honestly and verified — `scripts/palace.py`'s usage
line today is `{start|stop|down|up|restart|status|queue|reset|deploy|ingest-chat|code-seed|`
`code-backfill|bless}`; there is **no `query` verb** (`queue` is the build-queue view, not
this). The connective tissue a graduating plan must build: (a) a **read-only `palace query`
verb** — like `queue`, dispatched before the daemon/launcher path, returning typed atoms,
never actions (NN-3: the model advises; code acts — this surface only ever returns data);
(b) a **`/context <question>` project skill** that owns the question→bounds translation, so
agents invoke the compiler rather than hand-rolling queries; (c) a **config block** (e.g.
`[query] enabled=false`) and the **query-log lane** the lessons loop reads. All of it is
in-scope for the build and in its write_scope; gated off is fine, absent is not.

**What it takes to flip it on:** (a) the build above lands the verb + skill + log behind
`[query].enabled=false`; (b) the owner flips `enabled=true` and runs the owner-visible seed:
`palace query` over the onboarding question of §2.2.3, checking the returned atoms carry
their tags. Until then, traversal remains the regime.

## 5. Falsifiers

For each major claim, the observation that would kill it (rows are claims of *this* note;
inherited falsifiers cite their owners):

| claim | the observation that kills it |
|---|---|
| determinism (§2.3) | two runs of one query at one pinned corpus state differ — the surface is retrieval-with-vibes, not a database |
| loud absence (§2.3) | bounds that exclude the answer yield a plausible non-empty result instead of visible empty |
| never-bare-text (§2.4.1) | any surfaced atom lacking status/provenance/realm tags — unwarranted material can masquerade again |
| authority-as-Σ mapping (§2.2.2) | a "what counts" constraint inexpressible as refinement selection in R + result tags — reopen as a lattice amendment, never a parallel algebra |
| jurisdiction split (§2.4.2) | host-visible columns shown to reconstruct payload semantics — the ecosystem capsule's ⚑ embedding-inversion falsifier, inherited |
| union bound (§2.4.3) | grading prediction against evidence needs a representation translator (separate space or clocks) — the shared-coordinate condition failed |
| read_scope-as-view (§2.5) | a role's real context needs escape the view algebra (bespoke per-session grants proliferate) — views were the wrong formalization |
| lessons loop (§2.6) | the query log accumulates across sessions with zero retrieval-design changes traceable to it — the sensor is dead weight |
| third regime (§2.1) | with the surface enabled, fresh agents fall back to traversal at ≥ the pre-surface rate (the sufficiency-verdict proxy) — the regime failed its purpose |

## Parked decisions

| id | decision | default recorded | re-entry condition |
|---|---|---|---|
| SQ-a | graduation home for the query surface | none built; agents onboard by traversal | owner rules at ratification of this note |
| SQ-b | `read_scope` as a declared build-plan field | write_scope only; reading unbounded | the query log shows what roles actually read |
| SQ-c | which clock a wall-time sugar resolves to, per stratum | commit for repo-backed strata; cross-clock meets stay partial | CS-a materializes, or a non-repo window is needed |
| SQ-d | determinism at scale: exact scan vs ANN | exact/pinned scan at current scale | corpus scale forces an approximate index |

Detail the rows compress (per the doc-table rule, detail in prose): **SQ-a** — the warrant
parked "its own design note, or an item under an existing retrieval/interface note"; this
draft proposes itself as the home, and the owner's ratification (or rejection) of this note IS
that ruling exercised. **SQ-b** — the warrant capsule's gate, verbatim: "the query surface
above exists and its logs show what roles actually read." **SQ-c** — CS-a is
`dn-capability-scope`'s parked global event clock N; until it materializes, cross-clock meets
are honestly partial (constructor error), so a wall-time label may only resolve within one
stratum's materialized clock — commit is the only cross-stratum cut for repo-backed strata.
**SQ-d** — if ANN arrives, "same corpus state" must be redefined to include a frozen index
snapshot, or §2.3's determinism claim is re-litigated rather than silently weakened.

## Open questions

Carried faithfully from the warrant capsule (owner rules the graduation home; nothing wired
until then):

1. Who issues the **sufficiency verdict** on a translation — agent self-report, or a
   mechanical proxy (did the session re-ask, or fall back to traversal)?
2. What artifact type holds a **query-lesson** — a finding ftype, or a new exhaust lane the
   curator digests?
3. The temporal bound's clock: **half-ruled** by the ratified family (clocks, never wall
   time — §2.2.1); the per-question residue is parked as SQ-c.
4. Is the **/context skill itself versioned corpus content**, so instances can evolve their
   own translation layer — and drift in it is measurable?

Added by this note (beyond the capsules):

5. **Result typing of answer-drift:** is the replay-diff an `Inv` or a `Rate(κ)` quantity
   (dn-capability-scope §2.3 — clock-dependence as a compile-time distinction), and which
   clock indexes drift between two corpus states?
6. **The query log's own jurisdiction:** once remote principals query (§2.1), the log is
   exhaust *about them* — is it skeleton or payload under the §2.4 split, and does NN-11's
   "adapters leak interactions, not the corpus" clause classify it?

## Cross-references

- `docs/brainstorms/scoped-context-queries.md` — **the warrant**: owner seeds near-verbatim
  (2026-07-28T03:20Z) + the chat-side scrutiny this note restates as proposals.
- `docs/brainstorms/the-distributed-ecosystem.md` (05:07Z) — the jurisdiction duty's warrant:
  skeleton/payload, the query plan as privacy compiler, the ⚑ vector falsifier.
- `docs/brainstorms/synchronic-diachronic-dreamer.md` (02:54Z; 05:34Z–05:49Z) — the brief's
  retirement; scope-sweep grading, the union bound, the castle realm, lifecycle and TTL.
- `docs/design-notes/capability-scope-algebra.md` (`dn-capability-scope`, RATIFIED) — the
  (Σ,E,T,A) lattice; refinements as elements; ideals; SLICE; annotations-not-elements.
- `docs/design-notes/temporal-retrieval-algebra.md` (`dn-temporal-retrieval-algebra`,
  RATIFIED) — π_active ambient / σ_* σ^* opt-in; K(β); the temporal bound's math home.
- `docs/design-notes/agent-taxonomy.md` (`dn-agent-taxonomy`, RATIFIED) — role = scope
  signature; the query-agent row whose A this surface runs at.
- `docs/design-notes/core-query-protocol.md` (`dn-core-query-protocol`, RATIFIED) — every
  core reader a capability-scoped client of one protocol; this surface is one more client.
- **dn-prediction-castles** and **dn-distributed-ecosystem** — sibling drafts in parallel
  PRs (forward links; ids stable, paths land with their PRs).
- `docs/design-notes/scored-beliefs-and-earned-entitlement.md`
  (`dn-scored-beliefs-and-earned-entitlement`, draft) — the warrant-Σ sense used in §2.1/§2.2.3.
- code (verified seams): `core/kernel/stores/sourceset.py` (SourceSet — the group-by-digest
  relation); `core/ingest/index.py:131` (`grouped_semantic_search`);
  `core/stores/vectorstore.py` + `core/typedshims/lancedb.py` (LanceDB);
  `core/stores/telemetry.py`, `core/complex/temporal.py` (DuckDB); `scripts/palace.py:44`
  (the USAGE line with no `query` verb — the wiring gap, verified 2026-07-28).
- `docs/findings/finding-0146.md` — code is vectorized (code context flows through this same
  channel); `docs/findings/finding-0150.md` — non-goals are load-bearing (the §1.2
  discipline).
