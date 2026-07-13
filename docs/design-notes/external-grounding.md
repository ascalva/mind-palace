---
type: design-note
id: dn-external-grounding
status: draft # draft → ratified → superseded.  draft→ratified is an OWNER-ONLY hand edit.
implementation: partially-built # the airlock + fetcher exist but are DORMANT (no live driver); the curated store, the EMBED tail, and reference_material/ curation are to-build. See §3.
created: 2026-07-13
updated: 2026-07-13
links:
  - docs/brainstorms/external-grounding.md # the warrant — the 2026-07-13 arc (8 capsules): origin (live self-index), the two threads, citation-as-free-edge, ratification-as-gate, the cross-strata circuit, the two-plane model, the research-airlock reframe
  - docs/design-notes/core-query-protocol.md # dn-core-query-protocol — the query algebra over the live index; the Librarian is this note's outbound seam; the curated store is a NEW stratum its §2.1 scope grammar must scope (flagged for its Item 0)
  - docs/design-notes/authorship-distance-axis.md # the strata/depth axis this extends — author (subjective) vs curated (objective) as two K₀ bedrocks on a distinct provenance axis
  - docs/design-notes/edge-core-handoff-protocol.md # the edge/core diode the airlock instantiates; research as a β=0 sensing hand
  - docs/design-notes/hands-and-the-effector-layer.md # research-fetch as a β=0 (sensing) hand; the effector taxonomy home
  - docs/design-notes/observed-data-and-the-assistant-tier.md # the mirror firewall the curated store must not cross
  - docs/reference_material/README.md # the v0 manifest schema + the two-plane (git distillation ↔ local embedded full text) model + the Moore–Aronszajn exemplar
supersedes: null
superseded_by: null
warrant: null # finding-0062 (reference-gap) is ANSWERED by this note; promote at /triage
---

# External grounding — the curated literature stratum and the live self-index

> Filed as `draft` (chat-side protocol). Ratification is a hand edit by the owner —
> no command performs it, and `gate-guard` denies any agent attempt. `/graduate`
> refuses this note until `status: ratified`. This note is the design home for the
> external-grounding arc (`docs/brainstorms/external-grounding.md`, 2026-07-13); it
> unifies the two threads (curated literature + math verification) under one frame
> and licenses the near-term index/curation build without waiting on the fable-vet.

## 1. Purpose and scope

**The seed (the origin, and the load-bearing "why").** This arc grew outward from one
concrete engineering need (owner, 2026-07-13): use **Ouroboros itself** — the live
daemon + evolving corpus + reference store, projected per-commit — as a **live,
always-up-to-date self-index** so the orchestrator and builders **query** the graph to
resolve "what code/docs bear on X" instead of grepping/reading for it. Search-by-
context-burn is O(context × turns × tier) (context-economy); a lookup against a
precomputed live index is not. Everything below serves that end: a **richer, more
precise live index**. The philosophy is in service of the tool, not the reverse.

**What this note decides.** How the system grounds its reasoning in **externally-vetted
truth** rather than model assertion, and how that grounding is stored, ingested,
promoted, and queried. Concretely it decides:

1. The **curated literature stratum** as a second bedrock (K₀'), objective, on a
   *provenance* axis distinct from the authored mirror (§2.1).
2. The **two-plane storage model** — a git manifest+distillation plane and a local
   embedded-full-text plane — and the three separable states a reference passes
   through: `asserted → verified → DISTILLED → EMBEDDED` (§2.2).
3. **Ratification as the promotion gate** — a citation is curated when a design note
   that cites it *load-bearingly* is ratified (§2.3).
4. The **reframe of the §16 research airlock**: the acquisition pipeline is already
   built and dormant; the one decision to flip is **transient → EMBEDDED**, made safe
   by embedding into a *separate curated store*, never the mirror (§2.4).
5. The **live driver** — the common missing piece for both the medical and the
   design-grounding use case (foreground Ambassador TASK-intent + background scheduler
   trough job) (§2.5).
6. The **EMBED tail** (fetch open-access full text → chunk → embed) and its
   **copyright/licence gate** — the real decision this note opens (§2.6).
7. **Invariant reconciliation** — the whole design against Inv 1/2/4/7/11 (§2.7).
8. **Math verification (Thread 1)** — its frame and its home, deferred as a companion
   (§2.8).

**Out of scope — deferred to the `dn-core-query-protocol` fable-vet (gated Jul 17).**
This note does NOT settle: the formal `reference`/`literature` **kind** in the graph
taxonomy (the 5th kind); the retrieval **weight** `w(d,a,c) = γ^{(d+μc)/a}` (authority
as decay-*rate*, fable-verified — banked in the brainstorm's 18:16 capsule); how
authority `a` is *estimated* per node; the citation-extraction **grammar** φ_doc
recognizes; and the graph-migration that tags these cards as a distinct kind. This note
**references** those objects and **flags them for that vet's Item 0**; it does not
re-derive them. Until the vet, the curated cards ingest as **ordinary corpus**
(semantically searchable, not kind-distinguished) — which is sufficient for the
near-term index win.

## 2. Principles / decision

### 2.1 The curated literature stratum — a second objective bedrock

The corpus today is all-**internal**: the authored mirror, dialogue (brainstorms/
design), and observed code. It has **no principled home for external ground-truth
knowledge** (finding-0062, the reference-gap). We add one.

- **Two authored bedrocks, dual grounding.** The mirror is ground truth *about the
  owner* — subjective/personal authority; strengthens subjective-domain arguments. The
  curated stratum is ground truth *about the world* — objective/field-vetted authority;
  strengthens objective-domain arguments. Both are K₀ (un-derived, high-warrant), but on
  a **distinct provenance axis**, not a depth axis. This forces the separation the
  internal-only taxonomy blurred: **derivation-depth is not authority.** Literature is
  depth-0, high-authority, and *not the owner's* — three properties the single γ^d-over-
  depth model could not express. (The successor weight `w(d,a,c)` that resolves this is
  fable-verified and deferred to the vet; §1 out-of-scope.)
- **Objective only.** These cards are ground truth about the world, never about the
  owner — never mirror/private/interaction content. The firewall
  (`observed-data-and-the-assistant-tier.md`) holds by construction: a separate store,
  objective by definition.
- **Curation is human-gated, and that constraint IS the point.** "Well-vetted" makes
  this stratum behave like the golden set / `CONSTITUTION.md` (the fixed points are
  sacred — human-only, deliberate, logged), not like the freely-growing dialogue corpus.
  Trust is earned by curation cost; the bar for entry is: authoritative source + bridges
  a real gap the system has + owner-vetted. It grows only as fast as the owner curates.
- **The stratum is connective tissue, not a silo.** The curated layer links to *every*
  other kind: to the **mirror** (the owner's subjective intuition is the origin;
  literature grounds or *contradicts* it — a mirror↔literature contradiction is a
  high-signal event to **surface, never silently resolve**); to **dialogue** (the
  citation lives in the note that reaches for it); to **observed code** (the theorem/
  construction cited is *realized* in a module). The **design note is the join** where
  authored-intuition, objective-literature, and code-realization meet — which is *why*
  ratifying it (§2.3) seals the whole cross-strata circuit at once.

### 2.2 Two-plane storage; the maturity gradient

A reference is a **bundle** (paper + appendix + our excerpt + our distillation), so its
filesystem home is a **subdirectory per reference**: `docs/reference_material/<slug>/`
with a `manifest.md` (the typed node) + `distillation.md` (our extraction) + fair-use
docs. This is already stood up (`docs/reference_material/README.md`, v0 schema; first
resident `moore-aronszajn-1950/`).

**"Not git-tracked" ≠ "not ingested" — two separate decisions (owner correction,
20:34).** Two planes:

- **Git plane** (`docs/reference_material/<slug>/`): the manifest + our **distillation**
  + fair-use excerpts. Lightweight, portable, shareable — *what we know we use* (the
  load-bearing claim). Raw paywalled PDFs are **not** git-tracked (copyright + bloat).
- **Local embedding plane** (`data/`, gitignored): the **full source text**, fetched
  from the searchable venue and embedded into the reference corpus. This *is* ingested —
  it is the **pattern-finding substrate**. Manual distillation only surfaces a pattern we
  *already saw*; embedding the *whole* source lets the system find connections we did not
  anticipate (proximity in embedding space over the full text). Distillation = known
  utility; full-text ingestion = latent utility. This is what makes the curated stratum a
  genuine part of the **live index** (§1's origin).
- **The manifest is the join**: it records the identifier (how to fetch), points at the
  git distillation, and references the locally-ingested full text by `store_ref`.

**Three separable states** (do not conflate): **VERIFIED** (the claim — source exists +
says what we cite; the 2026-07-13 web pass) · **DISTILLED** (our summary, in git) ·
**EMBEDDED** (full source in the local store). A reference can be VERIFIED+DISTILLED
without being EMBEDDED (the seed set, initially). The precursor `asserted` = a citation
in a note with no subdir yet — a **candidate** (like an unresolved `[[wikilink]]`: valid,
marks something worth curating later). The maturity gradient is thus
`asserted → verified → DISTILLED → EMBEDDED`; creating the subdir is distillation,
embedding the full text is EMBEDDED.

### 2.3 Ratification is the promotion gate

**When** does an `asserted` candidate become `curated`? The demand signal is
**ratification** — the artifact chain's *existing* owner-only blessing (draft →
ratified). No new human ceremony:

- cited in a brainstorm / **draft** note → `asserted` candidate (free edge, tentative);
- cited **load-bearingly** in a **ratified** design note → PROMOTE: verify + ingest →
  `curated` (load-bearing).

Ratification is the moment the owner blesses an argument that *depends on* the reference;
its utility is now realized in a ratified artifact, so its curation is **earned**. The
ingestion **rides** that same owner-by-hand act (the blessing fence): a note's
ratification and its load-bearing references' curation become one coordinated blessing.
This is also where **both threads lock in** (§2.8): the references verified+ingested, the
computational machinery attested — ratification seals a **doubly-warranted** argument.

- **Load-bearing vs see-also.** Only the **soundness-bearing** refs (the argument's
  validity depends on them) are priority ingests; "see also" / related-work mentions stay
  `asserted` — else a 40-item related-work list forces 40 ingestions. Marking the split
  (e.g. `grounds:` vs `see-also:` in note front-matter) is a **parked** decision.
- **Seed set.** The forward rule triggers on *new* ratifications, but the current corpus's
  already-ratified notes' load-bearing citations are the initial curation **worklist** —
  demand-proven, not boil-the-ocean. The 9 web-verified citations from the 2026-07-13
  literature pass (7 CONFIRMED / 2 PARTIAL) are the first fill; `moore-aronszajn-1950/`
  (the citation that pass *corrected*) is resident.

### 2.4 The §16 research airlock — reframe, don't rebuild

The acquisition pipeline this arc assumed we would build **already exists**, complete and
tested but **dormant** (BUILD-SPEC §16, Phase 8; verified on disk this session):

- `core/research/` — the de-identification **airlock**: `criteria.py` (scrub PII from a
  query before egress), `airlock.py` (a one-way filesystem diode: core writes criteria,
  reads results, **never touches the network**), `rank.py` (rank fetched papers by
  relevance-to-notes + evidence tier — currently **transient**, `rank.py:7`).
- `cloud/fetcher/` — the **fetcher** (Zone C): `sources.py` queries OpenAlex, Europe PMC,
  arXiv; `aggregate.py` dedups by DOI and biases systematic-review > meta-analysis > … >
  preprint. Sources already span **both** target corpora: arXiv+OpenAlex (math/CS — our
  design-grounding) and Europe PMC/PubMed (medical — the owner's original intent).
- `core/librarian/librarian.py::research_criteria()` — owner query → de-identified
  criteria (the outbound seam).

The `edge/` network boundary our design assumed is **already the airlock** — Inv 2
satisfied by construction. **The one decision to flip is `transient → EMBEDDED`.** The old
design ranks papers in-memory and **discards** them — because there was no curated home
and the fear was polluting the authored mirror. This note gives it a home: a **separate
curated store** (`data/`), *not* the mirror. So "embed the full source locally" is fully
compatible with the old design's "never pollutes the mirror" invariant — it lands in a
distinct store. **The transient decision was a consequence of a missing store, not a
principle to preserve.** `reference_material/` is the curation layer the transient
pipeline never had; the airlock+fetcher produce candidates, `reference_material/` curates
keepers, the local store holds the full text.

### 2.5 The live driver — the common missing piece

What §16 lacks is the **live driver**: no coroutine calls `research_criteria → emit →
collect → rank → surface`; the Ambassador's `_delegate` seam and `narrate_effort` are
aspirational stubs. Both use cases need it, so it is the near-term build's spine:

- **Foreground** — an Ambassador **TASK-intent** path drives a fetch when the owner (or a
  design session) asks to ground a topic.
- **Background** — a **scheduler trough job** (BUILD-SPEC §13) runs the demand-driven
  worklist (the load-bearing refs of ratified notes) in idle windows.

The Librarian is already named in `dn-core-query-protocol` as the semantic-RAG client;
research/airlock is its **outbound** seam. The curated store is a **new stratum** the query
algebra (§2.1 scope grammar there) must scope — **flag for the fable-vet's Item 0.**

### 2.6 The EMBED tail and its copyright/licence gate — the real decision

The substantive build is the **EMBED tail**: flip transient→persist by fetching
**open-access full text** (Europe PMC / arXiv PDFs) → chunk → embed into the local curated
store, minting a `reference_material/` manifest per keeper. This is a real build with a
**network boundary** (the airlock/`edge/` already) and, crucially, a **copyright/licence
gate** — the genuine decision this note opens:

- **Local private ingestion ≠ redistribution.** Embedding full text into `data/`
  (gitignored, offline, owner-only pattern-finding) is a different act from committing it
  to a shareable repo. The two-plane split (§2.2) exists *because* of this: the
  distillation is portable **because it is ours**; the source stays local **because it is
  not**. Git-tracking a source would be redistribution; local embedding is not.
- **Prefer open-access by construction.** The fetcher biases to venues with open-access
  full text (Europe PMC flagged as such; arXiv). The licence gate should **default-deny**
  full-text embedding for sources without a clear open/fair-use basis, falling back to
  distillation-only (VERIFIED+DISTILLED, not EMBEDDED). The exact licence policy — which
  venues/licences clear the gate automatically vs need owner sign-off — is **parked** for
  the EMBED-tail plan (this note licenses the plan; the plan settles the policy).

### 2.7 Invariant reconciliation

- **Inv 1 (sealed core zero egress).** The sealed core never fetches. Acquisition is an
  `edge/` (airlock/fetcher) act or an owner curation-time act; the core reasons over the
  local store **offline**.
- **Inv 2 (only edge/ touches the network).** Satisfied *by construction* — the airlock is
  the `edge/` boundary (§2.4). Research is a **β=0 sensing hand**
  (`hands-and-the-effector-layer.md`): it reads the world, returns data, mutates nothing.
- **Inv 4 (executed code returns data, never actions).** Fetch+rank+embed return data
  (papers, rankings, vectors). A math check (§2.8) returns true/false/a-form — a natural
  Inv-4 fit for the sandbox.
- **Inv 7 (consequential health advice defers).** The **medical** use case keeps Inv 7 +
  the evidence-tier honesty already coded (§16). The **design-grounding** use case doesn't
  trigger Inv 7. Both ride the same de-id airlock; neither ingests into the mirror.
- **Inv 11 (the corpus never transits a third party; the interface may).** The full text
  enters the *local* corpus exactly as vault content does — never git, never egress. The
  corpus never transits a third party **at query time**; acquisition is a build/curation-
  time outside-core act.
- **Never-pollute-the-mirror** (not a numbered invariant but load-bearing): the curated
  store is a *distinct* store from the mirror; objective-about-the-world content never
  lands in subjective-about-owner space. This is what makes the transient→EMBEDDED flip
  safe (§2.4).

### 2.8 Math verification (Thread 1) — frame and home, deferred

The sibling thread grounds **computation**: a deterministic checker verifies the math
**machinery** (the normalization sums to 1, the identity holds, the series converges) —
**not** the modeling **theory** (that γ^d is the *right* weighting stays owner/fable
judgment). "The model advises; code acts," applied to math. Decisions carried from the
brainstorm:

- **Start with SymPy** (Python-native, in-stack, zero-licence, fully offline). A network
  CAS (e.g. Wolfram Alpha API) would violate Inv 1 + Inv 4 — **local kernel only**. Reserve
  a proof assistant (Lean 4/mathlib) for the rare load-bearing theorem an invariant rests
  on; don't pay formalization cost for routine identity/normalization/convergence checks.
- **It AUGMENTS fable, never replaces it.** Verified machinery on a wrong premise is a
  well-dressed wrong answer; the check raises warrant on the *derivation*, not the
  *premise*. The win is the **division of labour**: mechanical verification offloaded to a
  deterministic tool, so fable's scarce tokens go where only judgment works.
- **Home (parked default):** a machine-checkable companion attached to the build-plan §8
  "Math carried explicitly" field (run like a test), with a standing **math gate**
  (analogous to `type_gate` / attestable-green) aggregating the companions. Re-entry: the
  first math-bearing plan that needs its math attested — prototype the §8 companion + gate
  then. SymPy needs no design note to merely *try*.

**Convergence.** At ratification, a technical argument is grounded **two** ways: (a) its
cited theorems — Thread 2, curated (§2.3); (b) its computational machinery — Thread 1,
SymPy-attested. Ratification seals a **doubly-warranted** argument. That is the whole
frame realized at a concrete gate.

## 3. Consequences — what this note licenses

Once ratified, this note is the design home for (to be `/graduate`d into plans):

1. **The live-index query surface (near-term, no fable, no curated strata).** Orch/
   builders query the live v2 reference graph (~188k edges, per-commit) to resolve
   "references to code/docs for X" instead of grepping. This is `dn-core-query-protocol`'s
   read-query core over substrate that **exists today**. Scope whether a **read-only
   slice can graduate without ratifying the full query-protocol note** — the fastest
   context-cost win the owner actually asked for. *(This is queue-item 2 in the resume
   brief; it needs neither the fable-vet nor the curated strata.)*
2. **The `reference_material/` seed fill (near-term, no fable).** Git-author manifests +
   distillations for the 9 web-verified refs (pure authoring). Optionally wire bp-026's
   φ_doc to extract manifest `cited_by`/back-links into dialogue↔reference edges.
3. **The live driver** (§2.5) — `research_criteria → airlock.emit → collect → rank`,
   foreground (Ambassador TASK-intent) + background (scheduler trough §13). The common
   missing piece.
4. **The EMBED tail** (§2.6) — fetch open-access full text → chunk → embed into the local
   curated store; the **copyright/licence gate** lives in *this* plan. A deliberate,
   network-boundary build.
5. **Reframe BUILD-SPEC §16** from medical-only to **general literature grounding**
   (math/CS via arXiv/OpenAlex), one machinery, two use cases.
6. **The math gate** (§2.8) — prototyped at the first math-bearing plan (SymPy §8
   companion + aggregating gate).

**Seam to `dn-core-query-protocol` (the fable-vet, Jul 17).** The curated store is a new
stratum its §2.1 scope grammar must scope, and the `reference`/`literature` kind + the
`w(d,a,c)` weight + φ_doc's citation grammar are **its** Item 0 — flagged, not decided
here. The Librarian there is this note's outbound seam. **This note supersedes the
brainstorm's queue as the design home; the fable-vet supersedes the *taxonomy* questions
this note leaves open.**

## Parked decisions

- **Load-bearing vs see-also marking** (§2.3). *Default:* an explicit front-matter split
  (`grounds:` vs `see-also:`) so the ratification gate knows which refs to ingest.
  *Re-entry:* the first ratified note whose citation list is long enough that ingesting
  all of it is wrong — introduce the split then.
- **Ratification-triggered ingestion: fully owner-manual, or one-click confirm?** (§2.3).
  *Default:* the gate **presents** the load-bearing refs for one-click owner confirmation
  (human-in-the-loop on curation, per the golden-set trust posture) rather than fully
  automatic or fully manual. *Re-entry:* when the live driver (§2.5) is built.
- **The copyright/licence policy** (§2.6). *Default:* default-deny full-text embedding
  absent a clear open/fair-use basis; distillation-only fallback. *Re-entry:* the EMBED-
  tail plan owns the exact venue/licence allow-list.
- **The mirror↔literature contradiction handler** (§2.1). *Default:* **surface-only** —
  flag "what you believe diverges from the vetted record here", never silently resolve.
  *Re-entry:* if a structured reconciliation protocol is ever wanted (a later design
  question, not this note).
- **Transient-or-curated per medical topic** (§2.4). *Default:* the owner's call per
  topic — design-grounding refs are curated (they ground ratified notes); a personal
  medical query may stay transient. *Re-entry:* the live-driver plan surfaces the choice.
- **The math-verification home** (§2.8). *Default:* build-plan §8 companion + a standing
  math gate. *Re-entry:* the first math-bearing plan.
- **Taxonomy / weight / kind / authority-estimation / citation-grammar** — NOT parked
  here; **owned by the `dn-core-query-protocol` fable-vet** (Jul 17), Item 0. This note
  references `w(d,a,c) = γ^{(d+μc)/a}` (fable-verified) but does not re-derive it.

## Cross-references

- **Warrant:** `docs/brainstorms/external-grounding.md` — the 2026-07-13 arc (8 capsules):
  origin/live-self-index (18:03), the two threads (17:24), citation-as-free-edge (17:40),
  ratification-as-gate (17:50), the cross-strata warrant circuit (17:53), the
  `reference_material/` two-plane model (20:29 / 20:34), the research-airlock reframe
  (20:49), the fable-verified `w(d,a,c)` weight (18:16), the verify-before-trust dogfood
  (18:38).
- **Sibling / seam:** `docs/design-notes/core-query-protocol.md` (dn-core-query-protocol) —
  the query algebra; Item 0 owns the taxonomy this note defers.
- **Strata axis:** `docs/design-notes/authorship-distance-axis.md`;
  `docs/design-notes/observed-data-and-the-assistant-tier.md` (the mirror firewall).
- **Edge/effector home:** `docs/design-notes/edge-core-handoff-protocol.md`;
  `docs/design-notes/hands-and-the-effector-layer.md` (research as a β=0 sensing hand).
- **Existing code reframed:** `core/research/{criteria,airlock,rank}.py`;
  `cloud/fetcher/{sources,aggregate,handler}.py`;
  `core/librarian/librarian.py::research_criteria`; `agents/ambassador/` (`_delegate` +
  `narrate_effort` stubs). Spec: `docs/BUILD-SPEC.md` §16 (the airlock), §13 (the
  scheduler trough).
- **Curated layer:** `docs/reference_material/README.md` (v0 manifest schema, two-plane
  model); `docs/reference_material/moore-aronszajn-1950/` (the first resident).
- **Substrate:** bp-026 / φ_doc (doc→doc + doc→code extractor) — extends to manifest
  `cited_by` + external citations; reference_edges v2 (~188k edges, per-commit projection)
  — the live index this all enriches.
- **Findings:** finding-0062 (reference-gap — **answered** by this note, promote at
  /triage); finding-0068 (γ^d derivation gradient — the weight's predecessor).
- **Invariants:** `CONSTITUTION.md` Inv 1, 2, 4, 7, 11 (§2.7).
- **References (external, cited in the brainstorm; candidates for the curated stratum):**
  Meurer et al., "SymPy", PeerJ CS 3:e103 (2017); Aronszajn, "Theory of Reproducing
  Kernels", Trans. AMS 68 (1950); Popper, "Objective Knowledge" (1972) — World 3 ~ the
  curated stratum; Polanyi, "Personal Knowledge" (1958) — tacit knowledge ~ the mirror.
  (These are ANALOGY/scaffold, not authority, except SymPy/Aronszajn which are load-
  bearing technical citations.)
