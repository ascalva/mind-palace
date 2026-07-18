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
2. **Query agent (ambassador style)** — reads the corpus (nodes + edges) and answers / interprets,
   USING A MODEL. The consumer. Reads **nodes + edges**.
   *Instance:* the **Ambassador** (Track B, `agents/ambassador.py`) — the conversational front door,
   the type specimen. (The dreamer — a model-using reader that produces interpretations — likely
   belongs to this family too; TO RECONCILE, don't force.)
3. **Integrator** — connects strata into proven cross-stratum links. Deterministic, model-free.
   Writes **edges**. Resolves the references a transcript's tool records name (commit SHAs, file
   paths, doc paths) against the OTHER sensors' stores.
   *Instances:* the chat agent's **layer 2** / bp-070 ("where it happened": chat action → real commit
   → real files → real doc); `reference_edges` (doc↔code) was the proto.

## Two load-bearing properties

- **The deterministic floor holds up the model ceiling.** Sensor agents + integrators are model-free
  and FREE (no inference) — they write the graph's nodes and edges. The MODEL lives only in the query
  agent, which consumes the integrator's PROVEN edges as ground truth — so its answers/interpretations
  stand on fact, not cosine coincidence.
- **Integration was hiding as a projection side-effect** (`reference_edges` built inside the code
  projection). Promoting it to a first-class type clarifies the split: **sensors write nodes,
  integrators write edges, query agents read the graph.**

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

## Open / to settle
- **Dreamer's home in the taxonomy:** is the dreamer a query agent (autonomous, ambassador-family,
  model-using reader that writes interpretations), or a distinct type? Lean: query-agent family. Reconcile
  against the existing dreaming/curator design; don't duplicate.
- **The later model summary** (an abstractive per-session summary) puts a MODEL inside what is otherwise a
  sensor agent — is that a sensor-agent rate that borrows a model, or a query-agent step feeding the sensor?
  Settle when that rate is built (it reads only the scrubbed store — the model boundary = bright line #10).
- Graduate this into a design note (`dn-agent-taxonomy`?) once the owner confirms the ontology is stable.
