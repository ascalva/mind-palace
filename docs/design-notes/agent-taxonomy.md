---
type: design-note
id: dn-agent-taxonomy
status: draft               # draft → ratified → superseded.  draft→ratified is an OWNER-ONLY hand edit.
implementation: design-only
created: 2026-07-18
updated: 2026-07-18
links:
  - docs/brainstorms/agent-type-taxonomy.md          # THE WARRANT — the owner's live design session (2026-07-18)
  - docs/findings/finding-0109.md                    # the lossless/real-time decision + the layer model this generalizes
  - docs/design-notes/capability-scope-algebra.md    # RATIFIED — the (Σ,E,T,A) lattice every signature here is written in
  - docs/design-notes/cross-strata-dreamer.md        # RATIFIED — the per-scope-grant ruling; the correlator family this refines
  - docs/design-notes/chat-sensor.md                 # RATIFIED — φ_chat, the sensor-agent type specimen (amended by finding-0109)
  - docs/design-notes/connectivity-instruments.md    # RATIFIED — the conductance/connectivity consumers of E_proven
  - docs/design-notes/global-event-clock.md          # certified cuts — the diachronic dreamer's precondition
  - docs/design-notes/observed-data-and-the-assistant-tier.md  # the mirror firewall none of this touches
supersedes: null
superseded_by: null
warrant: docs/brainstorms/agent-type-taxonomy.md
---

# The agent taxonomy — sensor, query agent, integrator, dreamer, as scope signatures

> Composed at **fable** (`claude-fable-5`/xhigh, 2026-07-18, owner-directed design pass: "a proper
> design pass … which will be used to help finish the work of building the transcript sensor agent
> and the integrator agent with more proper/generalized language"). Filed as `draft`; ratification
> is an owner-only hand edit. **Design only; no build is authorized by this note.** Everything here
> is stated in the ratified `dn-capability-scope` algebra — this note adds NO new enforcement
> machinery; it types the system's agents in the machinery that already exists.

## 1. Purpose and scope

The owner settled a four-role ontology for the system's agents (2026-07-18, captured in the warrant
brainstorm): **sensor agents**, **query agents**, **integrators**, **dreamers**. This note makes each
role well-posed as a **scope signature** `s = (Σ, E, T, A)` plus two annotations (model-class,
residence), states the two laws that relate them, resolves the strata carving the roles exposed (the
**dialogue stratum**), and derives the consequences: the generalized charters under which bp-069 (the
transcript sensor agent) is re-grounded and bp-070 (the first full integrator) is minted.

**Out of scope:** any build; the retrieval mathematics; the dreamer program's own build gates
(`dn-cross-strata-dreamer` §3 — unchanged); any relaxation of `MIRROR_READABLE` (none proposed,
none implied — §2.6).

## 2. Principles / decision

### 2.1 The four roles, as signatures

A **role** is a reusable signature: a region of the scope lattice plus a model-class annotation.
An **agent** is an instance — a concrete grant inside its role's region. (Roles are vocabulary, not
gates: enforcement stays where it lives today — typed Views, structural store properties, and the
scope algebra's admissibility, per `dn-capability-scope` §2.2.)

| Role | Σ (strata) | writes | model | residence | produces |
|---|---|---|---|---|---|
| **Sensor agent** | its OWN stratum, only | `W_Σ=1` (own layers) | **free** | core/ops | **nodes** (layer projections, multi-rate) |
| **Query agent** | grantable read subsets | `W_Σ=0` (none) | priced | core (pinned tier) | **answers** (never graph structure) |
| **Integrator** | **≥ 2 base strata** (multi-strata, layer-granular) | `W_Σ=1`, **edge stores only** | **free** | core/ops | **proven edges** (witnessed) |
| **Dreamer** | up to `⊤_Σ` per owner grant | `W_Σ=1`, interpreted-only | priced | **core** | interpreted **nodes + interpretive edges** (all fiber types) |

All four: `W_world = NONE` (no role in this taxonomy holds effector reach; the hands are Track G's
separate, flag-off surface — `⊤_deployed.W_world = NONE` stands).

- **Sensor agent** — *senses a source and projects it into layers at rates* (§2.4). Reads only its
  own source + stratum; never another stratum. The chat projection agent (bp-069), the code sensor,
  the self-sensor, the vault ingest are instances. Its `A = (READ, W_Σ=1, NONE)` — the "sensor dual"
  rung `W_Σ` in the ratified Authority product is *exactly* this role's write bit.
- **Query agent** — *reads the graph, answers, writes nothing structural.* The Ambassador (Track B)
  is the type specimen. Its own dialogue re-enters the corpus only through a **sensor** (the
  interface capture / the chat sensor) — the query agent never writes what it said; it is sensed.
- **Integrator** — *the correction that named this role (owner, 2026-07-18): integrators are
  inherently MULTI-strata.* An edge's endpoints live in different strata by construction (a dialogue
  action in the dialogue stratum; the commit it produced in the observed stratum; the doc it touched
  in reference/dialogue). So the integrator's Σ is a downset spanning ≥ 2 base strata, granted
  **layer-granular** — (stratum, layer) pairs, e.g. `(dialogue, L1-action-log) ⊔ (observed,
  commit-ledger) ⊔ (reference_repo)`. What makes that breadth safe is the role's other coordinates:
  model-free, edges-only write, `W_world = NONE` (§2.2, the pricing law).
- **Dreamer** — *the apex/general class (owner): core-resident, full-or-subset strata, can query,
  produce nodes, and produce all edge types.* This is precisely the **per-scope-grant client** the
  owner already ruled into `dn-cross-strata-dreamer` (ratified): each dreamer is a scope grant, each
  grant owner-declared, each evaluable by the harness. Subtypes by T-scope (§2.5): **synchronic**
  (point window at a consistent cut) and **diachronic** (interval window, transports across cuts).

### 2.2 The two laws

**Law 1 — the deterministic floor.** Node-production and proven-edge-production are **model-free**.
Sensors and integrators never invoke a model; a model only ever (a) reads scrubbed, model-visible
layers, and (b) writes `interpreted`-provenance artifacts (structurally unforgeable — the
`DerivedStore` has no provenance parameter). The graph's *substance* (nodes, proven edges) is
mechanical and free; the graph's *interpretation* is priced and marked. Bright line #10 becomes a
**layer boundary** (§2.4): raw layers are model-opaque; the scrub gate is the only door.

**Law 2 — the grounding law.** Two edge classes: **E_proven** (integrator-written, each edge carrying
a mechanical **witness**, §2.5) and **E_interp** (dreamer-written, inferred). Every interpretive edge
must cite its support — the proven edges/nodes it rides on. This is the apophenia control made
structural: the dreamer interprets over ground truth instead of manufacturing connections from cosine
coincidence (`E_sim` alone is where apophenia lives). Conductance/connectivity
(`dn-connectivity-instruments`) measure over `E_proven ∪ E_sim` — the answer to oq-0031's 13-doc
saturation is a second, proven edge class, not a better σ.

**The pricing corollary (access is priced by what the holder can DO with it).** A grant's cost is a
function of (breadth of Σ, model-class): model-free breadth is **cheap** — the integrator can hold
multi-strata read safely because it cannot interpret, cannot emit prose, cannot reach the world, and
writes only typed edges. Model breadth is **expensive** — the dreamer's full-strata grant is exactly
the case the capability-scope algebra was built to govern (ideals subtracted, firewalls intact,
per-grant declaration). One algebra, two price points.

### 2.3 The strata carving — the dialogue stratum (drafted for ratification)

The owner's carving (2026-07-18): **code is observed strata; transcripts and design
notes/brainstorms/documentation are dialogue strata.** The discourse of the system — the human↔agent
dialogue AND the artifacts that dialogue crystallizes into — is one substrate, distinct from observed
machine reality.

**Decision drafted:** add **`DIALOGUE`** to the stratum-refinement forest R as a base stratum, with
refinements `dialogue_transcript ⊂ dialogue` (the chat stores: rawstore transcripts, chatlog,
chat_events) and `dialogue_artifact ⊂ dialogue` (brainstorms, design notes, documentation — today
reachable as `reference_repo`). Additive lattice extension: a new enum element + two refinement
edges; no store schema changes; `⊤_Σ` grows by one base stratum; the 𝔇 denylist is unaffected.

**Reconciliations (explicit, so nothing is silently relabeled):**
- **Stratum ≠ provenance.** The chatlog's rows keep `provenance = observed` (bp-063's conservative
  landing) even as the *stores* sort under `dialogue` in R — provenance says how a datum entered;
  the stratum names which substrate a grant reaches. Whether owner-side transcript utterances
  deserve a future provenance closer to `authored-dialogue` (they are the owner's words to an
  agent — the enum's own docstring for OBSERVED, "third-party behavioral exhaust," does not
  describe them) is **parked**: it is a mirror-firewall question, it is not needed by any agent in
  this note, and `MIRROR_READABLE` does not change here.
- `dialogue_artifact` overlaps `reference_repo` (repo-backed docs). v1: both predicates may name the
  same underlying stores; R is a forest of grant-vocabulary, not a partition of disk. If ratification
  prefers a single home, `reference_repo` narrows to code-citation targets — decided at the enum
  change, not here.

### 2.4 The sensor agent, generalized — multi-rate projection

A sensor agent `S` over source `σ` maintains its stratum with a **layer family** `{L_0 … L_n}`,
each layer a deterministic projection `φ_i` applied at a declared **rate**
`r_i ∈ {event-driven (real-time), housekeeping (delayed), on-demand}`:

- **L0 — the substrate layer** (real-time): verbatim retention (content-addressed raw; "git for the
  source") + the cleaned projection (for chat: tool-stripped prose utterances). The stratum's clock
  `N_s` ticks on L0 events — the CS-4 chat clock is the dialogue stratum's `N_s`.
- **L1 … Ln — derived layers**, each at its own rate. For chat (finding-0109, owner-settled): L1 is
  the **action log** — *what* was performed, in order (`owner_prompt → commit → ratify → build_plan
  → …`), extracted from turns + tool records; delayed rate; no prose ("for prose, read L0").

**Laws of the role:** (a) **lossless/growth-aware** — projections are total over the source; a
source that grew is re-projected; freeze-once is forbidden (finding-0109 — the owner's parity
standard: every transcript change, like every commit). (b) **The scrub boundary**: `L0-raw` is
model-opaque; the deterministic credential scrub gates everything model-visible. Bright line #10,
stated at the layer boundary. (c) **Model-freeness is typed, not aspirational**: a "summarizing
rate" that needs a model is NOT a sensor rate — by Law 1 it is a separate, small scoped model-client
(query/dreamer-family) reading scrubbed layers and writing `interpreted` nodes beside the stratum.
This resolves the parked "where does the later abstractive summary sit" question by type, not taste.

**Layer tissue is fibrational, not edge-typed (owner question, 2026-07-18 — recorded).** "Fiber"
does two jobs in this system; they must not be conflated. The connective tissue *between a
stratum's layers* — an L1 action-log event ↔ the L0 turns it was extracted from — is the **fiber
structure of the projection map** `φ_i` (each derived record's fiber `φ_i⁻¹` = its source records),
carried **on** the rows as backpointers (`session_id`, `turn_index`, `transcript_digest` — the
established `sourceset` pattern: a derived object IS the set of its source records) and
re-derivable from retained raw at will. It is **not** edges in the `EdgeScope` fibers `{F, D, C}`,
which type *inter-stratum / inter-artifact* structure, stored beside the data and granted via E.
Storing projection tissue as graph edges would duplicate what the rows already carry and pollute
the connectivity graph with derivation stars. Rule of thumb: **within a stratum, layers connect by
projection fibers (structure on the data); across strata, records connect by E-fiber edges
(structure beside the data)** — the sensor/integrator boundary restated at the data level. The two
senses meet in exactly one place, the witness law: a C-edge's witness is *composed of* these
projection backpointers — the fibers are the raw material the proofs are made of.

### 2.5 The integrator, generalized — the witness law (bp-070's charter)

An integrator resolves **references** — identifiers one stratum's records name (commit SHAs, file
paths, artifact ids) — against the stores of *other* strata, minting **proven edges**. Its defining
obligation is the **witness law**: every proven edge carries the mechanical evidence it was derived
from, sufficient to re-derive or refute it — for the chat↔code↔doc integrator:
`witness = (transcript_digest, turn_index, tool_record)` → endpoints `(dialogue action, commit SHA,
file path, doc path)`. Not a time-join; a reference-resolution. Causation is *read*, not inferred.

**Well-typedness under the ratified algebra.** The SLICE rule (`dn-capability-scope` §2.2) demands a
consistent cut for any `|Σ| > 1` point-window scope — and *the commit SHA is the cut for repo-backed
strata*. The integrator's witnesses carry their commit SHAs, so **every proven edge arrives
cut-stamped by construction**: the multi-strata access the owner mandated is not merely permitted by
the algebra; it satisfies its consistency discipline for free (`Clock.COMMIT` is its clock).

**Commits as cross-clock bookmarks (owner, 2026-07-18 — recorded).** The same SHA plays a second,
diachronic role. `Clock.COMMIT` is a *range* of the parked global event clock N; a C-edge's witness
embeds that range **between two dialogue ticks** — the `tool_use` turn that issued the commit and
the `tool_result` turn that observed it: `turn_i ≺ commit ≺ turn_{i+1}` on the chat clock (CS-4).
Every C-edge is therefore a **witnessed cross-clock correspondence**: a point where the dialogue
stratum's `N_s` and the repo's commit clock are causally co-registered. Consequences: (a) *"what
conversation led to that change"* is an exact reverse traversal — commit → C-edge → (session, turn
range) — never a wall-time heuristic; (b) the accumulated C-edges are precisely the empirical
alignment data the global-event-clock program (CS-a / G3) needs when N materializes — the ratified
algebra's honestly-partial cross-clock meets gain, edge by edge, the anchor points a common
refinement will interpolate through. The integrator feeds the clock it is disciplined by.

**A new edge fiber.** `EdgeScope`'s fibers are `{F: citation, D: supersession}`. Proven causal
production ("this dialogue action produced this commit/file/doc-change") is neither — this note
proposes fiber **`C` (causal-witnessed)**, an additive lattice extension (`E ⊆ {F, D, C}`). The
integrator's write grant is fiber-scoped: it writes `C` (and may write `F` where it resolves pure
citations, as `reference_edges` — the proto-integrator, doc↔code — already does).

**Why `C` is not `D` (owner question, 2026-07-18 — recorded).** A supersession edge is
*homogeneous*: two versions of one artifact's lineage (P → P′, "this replaced that") — already
typed by the D-machinery (the versions/authored-supersessions stores, the §4A op-seq spine).
"Conversation led to a change" is *heterogeneous*: a dialogue action → the artifact it produced —
**origin, not lineage**; an utterance is not a prior version of a file. The three fibers are
orthogonal axes: `F` = support, `D` = lineage, `C` = origin. The coupling is **composition**: a
conversation that drives a change to an existing artifact yields a C-edge into the very commit that
constitutes the D-event in that artifact's lineage — C explains D, beside it, never as it. A
creation has C without D (nothing superseded); an owner hand-edit outside dialogue has D without C
(no dialogue origin). The traversal **C∘D** answers *"which conversation produced this version?"* —
the derivation-retention `dn-chat-sensor` was founded on, now a typed two-hop query.

**Family placement.** The ratified Track-D "correlator family" refines into its two halves: the
**integrator** (deterministic, proven edges — this role) and the **cross-strata dreamer** (model,
interpretive edges — the ratified note's subject). The refinement changes nothing ratified; it names
the halves so each can be built and priced correctly.

### 2.6 What none of this touches

`MIRROR_READABLE` (unchanged); the foundation denylist 𝔇 (ungrantable, all roles); the effector
ceiling (`W_world = NONE` everywhere here); the dreamer program's gate chain
(`dn-cross-strata-dreamer` §3 — its builds remain separately gated); the sealed core / egress rules.

## 3. Consequences

1. **bp-069 re-grounds** as *the dialogue sensor agent*: rates 0+1 (L0 substrate real-time +
   lossless; L1 action log delayed), vocabulary and interfaces per §2.4. Substance already matches;
   the re-ground is language + the layer/rate framing pinned in §6 of the plan.
2. **bp-070 mints** as *the first full integrator*: chat↔code↔doc, multi-strata layer-granular
   grant, witness law, fiber `C`, `reference_edges` as proto. Downstream consumers recorded:
   connectivity/conductance (`E_proven ∪ E_sim`), the dreamer's grounding law, the scope algebra.
3. **The `DIALOGUE` stratum** enters R (enum + two refinements) — additive; folded into bp-070 or a
   sibling small plan at graduation.
4. **The later abstractive summary** is typed out of the sensor (§2.4c): a small scoped model-client
   reading scrubbed layers, writing `interpreted` — its own future plan, after the dreamer-program
   gates it rides with.
5. **The curator** reconciles as a minimal-grant synchronic dreamer (single stratum, point window,
   interpreted-only output) — no code change implied; vocabulary only.

## Parked decisions

| Decision | Default recorded | Re-entry condition |
|---|---|---|
| fiber letter/name for causal edges | `C` (causal-witnessed) | ratification review of this note |
| provenance of owner-side transcript utterances | stays `observed` (bp-063) | a mirror-firewall design pass; needs owner + `MIRROR_READABLE` deliberation |
| `dialogue_artifact` vs `reference_repo` overlap | both may name the same stores (v1) | the enum-change build |
| diachronic dreamer | blocked on certified cuts (`global-event-clock` G3) | G3 materializes |
| curator-as-dreamer | vocabulary only, no re-code | if the curator ever widens scope |

## Cross-references

`core/scope.py` (Stratum/StratumScope/EdgeScope/Clock/Authority — the algebra as types) ·
`core/provenance.py:44-99` (Provenance, MIRROR_READABLE) · `core/mirror.py` (MirrorView) ·
`core/sensing.py` (ObservedView — the assistant-tier read boundary) · `ops/chat_sensor.py` (φ_chat,
the sensor specimen) · `agents/ambassador.py` (the query-agent specimen) ·
`data: reference_edges.sqlite` (the proto-integrator's store) · bp-063/bp-064/bp-068 (chat stratum:
store, clock, wiring) · bp-069 (the dialogue sensor agent, rates 0+1) · bp-070 (the integrator, to
mint) · finding-0108, finding-0109 · oq-0031 (the connectivity saturation this taxonomy answers).
