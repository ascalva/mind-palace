# Brainstorm — the agent-type taxonomy (sensor / projector / integrator) + the multi-rate chat projection agent

> Captured by the orchestrator from a live owner design session (2026-07-18). Exploratory —
> the owner's verbatim thinking, distilled. Warrants finding-0109 + bp-069 (built) and bp-070
> (to mint). Candidate to graduate into a design note once the owner is ready.

## The ontology the owner settled on (2026-07-18)

THREE agent types, distinguished by their relationship to the corpus graph (nodes / edges / read):

1. **Sensor(s) agent** — senses a source AND projects it into layers. Deterministic, model-free.
   Writes **nodes** (observations + their layer projections). (Sensing and projecting are ONE type
   here — the sensor agent both ingests and re-represents its own data at rates.)
   *Instances:* the **chat projection agent** — layer 0 (dialogue: raw snapshot + tool-stripped
   prose, real-time) + layer 1 (the ACTION LOG, "what happened, in order": `owner_prompt → commit →
   ratify → build_plan → …`, delayed, from turns + tool records); the code sensor; the self-sensor;
   the vault ingest/watcher.
2. **Query agent (ambassador style)** — reads the corpus (nodes + edges) and answers, USING A MODEL.
   The consumer. Reads **nodes + edges** → writes **answers** (no graph structure).
   *Instance:* the **Ambassador** (Track B, `agents/ambassador.py`) — the conversational front door.
3. **Integrator** — connects strata into PROVEN cross-stratum links. Deterministic, model-free.
   Writes **edges**. Resolves the references a transcript's tool records name (commit SHAs, file
   paths, doc paths) against the OTHER sensors' stores.
   *Instances:* the chat agent's **layer 2** / bp-070 ("where it happened": chat action → real commit
   → real files → real doc); `reference_edges` (doc↔code) was the proto.

## The dreamer — a distinct, apex class (NOT a query agent)

The dreamer is a DIFFERENT class entirely — the only GENERAL agent, where the other three are each
specialized to one move:
- **Lives in the CORE** (full privilege — not edge, not sandboxed).
- **Full strata access** — reads across ALL strata (full or a subset). This is WHY Track-2 exists:
  `capability-scope-algebra` is the dreamer's access bound ("grant this dreamer full/subset strata,
  safely"); the resume brief's "privileged reader/dreamer reads full/subset strata" IS this class.
  (Sensors read only their own data. **Integrators DO cross strata — owner correction 2026-07-18:**
  multi-strata layer access is their defining need — code = observed strata; transcripts + design
  notes/brainstorms/documentation = dialogue strata; an edge's endpoints span both. But the
  integrator's grant is CHEAP: model-free, edges-only write. The dreamer's is the EXPENSIVE grant:
  model + breadth. Both are priced by the same scope algebra — access is priced by what the holder
  can DO with it.)
- **Can query, produce nodes, AND produce ALL edge types** — it spans every capability.
- **Subtypes by temporal mode:**
  - **Synchronic** — structure at a single certified cut: themes, clusters, the σ-graph,
    conductance/connectivity *now*. (`docs/design-notes/connectivity-instruments.md`)
  - **Diachronic** — evolution across cuts: how a theme forms/decays, memory curves, lag. Needs the
    certified-cut clock. (`global-event-clock`, the `graph-at-a-past-cut` brainstorm)

## Two load-bearing properties

- **The deterministic floor holds up the interpretive ceiling — TWO EDGE CLASSES.** Integrators write
  PROVEN edges (deterministic, free, causal); dreamers write INTERPRETIVE edges (inferred, model). The
  dreamer's interpretive edges are grounded BY the integrator's proven ones — that is the apophenia
  control, made structural. Sensors + integrators are the model-free floor; the model lives in the
  query agent and the dreamer.
- **Integration was hiding as a projection side-effect** (`reference_edges` built inside the code
  projection). Promoting it to a first-class type clarifies the split: **sensors write nodes,
  integrators write proven edges, query agents read → answer, dreamers (full-strata) query + write
  nodes + write all edge types.**

## Why it matters downstream (the connectivity payoff)

The integrator's free proven edges are the substrate the whole connectivity program rides on:
- the **dreamer** interprets over ground-truth connections instead of guessing them;
- the **capability-scope-algebra** exploits them as real structure;
- **conductance + connectivity** (`docs/design-notes/connectivity-instruments.md`) stop being a
  similarity-only graph — the free edges are real conductive paths across strata.

This is the answer to **oq-0031** (the σ-sweep saturating at 13 docs): the graph was thin because
cosine was its only connective signal. The integrator injects a second, proven class of edges.

## Instantiation status (the build program)

- **bp-069 (proposed) — the chat projection agent, layers 0 + 1** (sensor + projector, both
  deterministic/model-free). Layer 0 = the lossless real-time dialogue (the urgent data-loss fix);
  layer 1 = the action log. Item 3 builds the tool-record parser layer 2 reuses.
- **bp-070 (to mint) — layer 2, the sensor integrator** (chat↔code↔doc proven edges). Must ref the
  ratified `connectivity-instruments.md` + `cross-strata-dreamer.md` + `capability-scope-algebra.md`
  as its downstream consumers.
- **Later** — an abstractive model summary (a projector rate that DOES use a model, reading only the
  scrubbed store — the model boundary = bright line #10).

## The four types (settled 2026-07-18)
1. **Sensor agent** — deterministic; reads its OWN data; senses + projects; writes **nodes**.
2. **Query agent** (ambassador) — model; reads the graph; writes **answers** (no structure).
3. **Integrator** — deterministic; MULTI-strata layer-granular read (owner correction 2026-07-18);
   resolves references; writes **proven edges**.
4. **Dreamer** — core-resident, FULL strata access; queries + writes **nodes + all edge types**;
   synchronic (single-cut structure) | diachronic (across-cut evolution). The apex/general class.

## Open / to settle
- **The later model summary** (abstractive per-session) puts a MODEL inside what is otherwise a sensor
  agent — a sensor-agent rate that borrows a model, or a query/dreamer step? Settle when that rate is built
  (reads only the scrubbed store — the model boundary = bright line #10).
- **Curator's home:** where does the curator (near-dup / prune / contradiction findings) sit — a dreamer
  subtype, or its own thing? Reconcile against `core/curator.py`.
- ~~GRADUATE this into a design note~~ **DONE (2026-07-18, fable/xhigh):**
  `docs/design-notes/agent-taxonomy.md` (`dn-agent-taxonomy`, draft — awaits owner ratification).
  The note additionally records: the multi-strata integrator correction; fiber C (causal-witnessed)
  beside F/D, with C-explains-D composition; layer tissue as projection fibers (not edges); commits
  as cross-clock bookmarks (C-edges feed the future global clock N); the DIALOGUE stratum drafted
  into R; the abstractive-summary question resolved by type (not a sensor rate).
