---
type: design-note
id: dn-trace-retrieval
track: code-ingest
status: draft            # draft → ratified → superseded.  draft→ratified is an OWNER-ONLY hand edit.
created: 2026-07-27
updated: 2026-07-27
links:
  - docs/brainstorms/commit-economy-and-the-succession-path.md   # R2 — "decouple the sensor first"; this is the note it says is owed
  - docs/brainstorms/owner-intent-audit.md                       # the three-channel discovery; L-4 (the wipe-permission loss)
  - docs/brainstorms/context-load-as-a-feedback-loop.md          # the four-part destructive-loop diagnostic applied in §6
  - docs/design-notes/chat-sensor.md                             # ratified — L0 substrate this note extends
  - docs/design-notes/temporal-code-corpus.md                    # ratified — the supersession/poset machinery reused in §5
  - docs/design-notes/role-state-and-scoped-handoff.md           # ratified — clause (e)'s designed fix; §2 measures what it will end
  - docs/design-notes/dialogue-ingest-and-recursion.md           # draft sibling — SEMANTIC ingestion of dialogue; disjoint from this note (§1.2)
  - docs/design-notes/session-handoff-gate.md                    # ratified — the clause under forensic study
supersedes: null
superseded_by: null
warrant: null
---

# Trace retrieval — hook forensics and the succession path as one instrument

> Filed by the chat agent as `draft` (chat-side protocol, §8). Ratification is a
> hand edit by the owner — no command performs it, and `gate-guard` denies any
> agent attempt (§10). `/graduate` refuses this note until `status: ratified`.

**Commissioning question (owner, 2026-07-27, in substance):** *can ouroboros itself — once the
transcript backlog is ingested — pinpoint when in the transcripts a hook trigger occurred and read
the local area around those triggers?* Motivated by clause (e) of the Stop gate firing for days:
*"there may exist potential critical conversations hijacked by the (e) trigger and forcing a
context scramble, which now we see can confuse a claude worker."*

**Standing ruling this note serves (owner, 2026-07-27, `commit-economy-and-the-succession-path`
R2):** the code sensor is to read artifacts and their edit events directly, rather than commit
bodies, *before* committing is reduced — and ouroboros's retrieval is to stand in as the proof of
lineage for internal documents (the succession path). The forensic query and the lineage query are
the same shape: **reconstruct a path through history, and give me a window around each hit.**

## 0. Verdict

**POSSIBLE — WITH CONDITIONS.** And substantially cheaper than it looks, because roughly 70% of
the instrument already exists, ratified and wired:

- The transcripts are already retained **byte-verbatim** in an immutable content-addressed
  rawstore, and already extracted into an **ordered** utterance store — `data/chatlog.sqlite`,
  `PRIMARY KEY (session_id, turn_index)` (`core/stores/chatlog.py:76-92`), sensor wired into the
  daemon (`ops/lifecycle/launcher.py:492`).
- A **typed, ordered action log** over each session already exists — `data/chat_events.sqlite`,
  kinds `prompt|response|commit|file_edit|build_plan|finding|design_note|ratify|tool_use`, each
  event carrying a structural ref and a `turn_index` backpointer into the prose layer
  (`core/stores/chat_events.py:40-48`, `core/chat_events.py:47-50`). 22,031 events live today.
- The succession substrate partially exists: 660,577 corpus `note-citation` edges
  (`data/reference_edges.sqlite`, measured 2026-07-27) and the store-free supersession poset
  (`core/kernel/temporal/boundary.py:99`).

The conditions, each argued below:

1. **The exhaustiveness authority is the structural spine, never the embedding** (§4, D1).
2. **Three transcript channels must be closed** — queue-operations, hook/system rows, and
   `AskUserQuestion` results are structurally invisible today, and hook text is currently
   **mislabeled as owner speech** — 39 live rows (§3, D2).
3. **Windowing is read-time reconstruction from the raw bytes**, never embed-time storage of tool
   exhaust — CS-3 stays intact (§4, D3).
4. **Nothing crosses the edge**; observed rows stay outside `MIRROR_READABLE`; vectorizing chat
   prose is parked as its own owner gate (§6, §7).
5. **Build after the bp-125..127 wave seals** — every write surface this note implies is inside
   the live wave's frozen dirs (§8).

## 1. Purpose and scope

This note decides: (D1) where exhaustiveness lives — structural spine vs. semantic retrieval;
(D2) the channel-closure amendment to the dialogue sensor (the R2 decoupling seam); (D3) the
window operation; (D4) the shared query contract `trace(anchor) → path + windows`; (D5) the
succession-path walker over document lineage; (D6) the feedback-loop containment obligations. It
also carries, as §2, the ground-truth forensic census of clause (e) that any implementation must
reproduce — the named falsifier (§9).

### 1.2 Non-goals — load-bearing; the owner reads these at ratification

- **NOT a semantic-completeness claim.** No embedding-based query is ever presented as "every
  occurrence." Derived in §4 from the measured properties of the two layers; uncited intuition
  about embedding recall is labeled as such there.
- **NOT vectorization of the dialogue stratum.** Chat utterances are not embedded under this
  note. `[INFERENCE]` — the owner has not ruled on chat vectorization; §6 argues it is the one
  step that would materially feed loop L5, so it is parked as a separate owner gate, not smuggled
  in here. (finding-0146 — "code must be vectorized" — is about *code*, and is not read here as
  covering agent/owner dialogue.)
- **NOT a change to commit practice.** R1 of the commit-economy ruling stays gated behind this
  note's build, per the owner's own ordering (R2 gates R1). Nothing here alters what commits.
- **NOT an edge or adapter surface.** No transcript byte, raw or derived, becomes reachable from
  `edge/` or any third-party transit. Bright lines #2 and #11 (§7).
- **NOT a dreamer/belief substrate.** No conditioning grant over the dialogue stratum is created
  or widened; CS-5's correlator remains the sole named future reader, surfacing-only
  (`core/stores/chatlog.py` module doc). `[INFERENCE]` that the owner wants this held — derived
  from the L5 analysis, not from an explicit ruling.
- **NOT a re-litigation of `dn-dialogue-ingest-and-recursion` (draft).** That note is about
  ingesting dialogue *as reasoning* into the semantic layer with supersession semantics. This
  note is about *querying history* through the structural layer. Disjoint surfaces; if that note
  ratifies later, its ingestion must still satisfy §6 here.
- **NOT run now.** This study deployed nothing, started no daemon, ingested nothing. The census
  in §2 was produced by throwaway scratchpad scripts over the raw files, read-only.

## 2. Ground truth — the clause-(e) census (2026-07-19 → 2026-07-27)

Method: streamed all 218 transcript files (357 MB) in `~/.claude/projects/-Users-ascalva-mind-palace/`,
matched the Stop-hook feedback shape (`type:"user"`, string content starting `Stop hook feedback`,
containing the clause-(e) text pinned at `.claude/hooks/_lib.py:915-920`), deduplicated fork-pair
sessions by timestamp, and read a ±9-row window around every firing.

| quantity | value |
|---|---|
| clause-(e) firings, raw / fork-deduped | **108 / 99** |
| span | 2026-07-19T23:42Z (the session that shipped the gate) → 2026-07-27T04:45Z |
| sessions touched (deduped) | 16 |
| peak session | `a73e8b34` — **17** (the KMS/autopilot design night; matches the loops capsule) |
| peak day | 2026-07-26 — 36 raw firings |
| clause co-census on the same feedback rows | (e) 108 · (c) 75 · (b) 27 · (a) 18 |
| tool ops consumed per firing before the next real turn | mean 5.4 · median 4 · max 21 |
| resume-brief file operations spent servicing the gate | **302**, across 93 of 99 firings |
| immediate cascades (second (e) within 180 s) | 4 |
| firings with a queued owner message pending in the ±9-row window | 10 |
| tool errors during forced brief writes (unread-file, stale-read, failed-edit) | 11 |
| documented self-contradiction incidents minted during forced rewrites | 4 (L3; the agent itself counted "fourth instance") |

**Classification.** The gate fires at turn end, so it never truncated an answer mid-sentence. Its
damage is to the *next* turn and to the queue channel. Roughly 15–20 firings were genuine closes
(session actually wrapping). The remaining ~80 fired **mid-conversation** — between owner turns of
a live design thread — converting the inter-turn gap into forced brief maintenance.

**Named damage, with coordinates:**

1. **The L-4 loss.** The owner's *"I give you permission to wipe the resume"* arrived on the
   queue channel at `2026-07-26T03:16:25Z` (`a73e8b34` q660) **during (e)-churn** and was
   dropped; ~17 further firings were paid over the following 24 h before he re-issued it three
   times. (Already found by the owner-intent audit; this census confirms the mechanism.)
2. **The contradiction mint.** Session-55's forced rewrites produced three same-line
   contradictions plus the `_lib.py:762` mis-citation that propagated into a Fable design prompt
   (firings #24–27 of the census; the loops capsule's L3/L4, observed here in the raw).
3. **The context burn.** The owner ended session `61710eca` at 72% context — *"you're still
   carrying baggage"* — after 10 firings interleaved with the role-state and commit-economy
   design work (the succession-path conversation itself ran between firings #22–28).
4. **A latent corpus corruption.** The live chatlog already holds **39 clause-(e) feedback rows
   attributed to `speaker='owner'`** (measured read-only, `data/chatlog.sqlite`, 2026-07-27) —
   the gate's words recorded as Alberto's. §3 D2 is the fix.

**Verdict on the owner's hypothesis, stated plainly:** *partially supported.* Supported — as
sustained context churn, a measurable turn tax, worker confusion with receipts (errors,
contradictions, one near-corruption of another seat's state refused at `ff614288` firings
#96–97), and one documented critical loss via queue displacement (L-4). **Not supported** in the
strong form: no conversation was found that was killed mid-thought by (e) itself, and the other
permanent losses of the window (L-1, L-2) were multi-intent/queue losses, not (e) displacements.
The gate was expensive and corrosive; it was not, on this evidence, fatal to any single thread.

## 3. The three-layer shape that already exists

```
L-raw   rawstore            byte-verbatim transcripts, content-addressed, immutable   (CS-1)
L0      chatlog.sqlite      ordered prose utterances   (session_id, turn_index)       (CS-3)
L1      chat_events.sqlite  ordered TYPED actions      (session_id, ord) + turn_index backptr
sem     vectors.lance       chunk-grain embeddings     — notes + code today; NO chat rows
```

Grounding: `ops/chat_sensor.py:12-26` (retention-before-extraction), `core/stores/chatlog.py:76-92`
(ordered schema), `core/stores/chat_events.py:40-48` (typed schema), `core/chat_events.py:136-176`
(the deterministic projector), `core/ingest/index.py:27-40` (`chunk_index` on every vector row),
`ops/lifecycle/launcher.py:492,507,528` (both passes wired into the daemon).

### D2 — channel closure (the sensor amendment; this IS the R2 decoupling seam)

Measured blind spots of the current interpreters (both v1):

| channel | today | fix |
|---|---|---|
| `type:"queue-operation"` (typed mid-turn) | dropped — no `message` dict (`ops/chat_sensor.py:124-129`) | L0 row, `speaker='owner'`, new `channel='queue'` |
| Stop-hook feedback (`type:"user"`, string content) | **ingested as owner speech** (`_ROLE_TO_SPEAKER`, `ops/chat_sensor.py:64`) | `speaker='system'`, `channel='hook'`; L1 kind `hook_feedback`, ref = `<hook>:<clauses>` (e.g. `journal-gate:e`) |
| `type:"system"` (`stop_hook_summary`, hookErrors) | dropped (`core/chat_events.py:158-160`) | L1 `hook_feedback` corroboration; no L0 row (not prose) |
| `AskUserQuestion` tool_result (channel 3) | stripped with all tool_results | L1 kind `ask_answer`, structural ref; `[INFERENCE]` L0 verbatim row is owner speech and should land `channel='ask'` — owner to confirm at ratification |
| `isSidechain` rows | ingested unmarked | carry a `sidechain` flag on L0/L1 rows |

The owner-intent audit measured the cost of the first row alone: a channel-1-only sweep recovers
~60% of what he typed. **Any ingestion design that skips this table inherits a 40% blind spot.**

Mechanics: bump both interpreter versions (`ops/chat_sensor.py` `INTERPRETER_VERSION`,
`core/chat_events.py`); additive column migrations on both stores (the `_migrate_layer_if_needed`
precedent, `core/stores/vectorstore.py:97-118`); everything regenerates from L-raw — **no
embedding exists over these rows, so re-extraction costs minutes, not model time.** Two wiring
gaps found and named in §8: re-projection keys on transcript digest, not interpreter version
(`core/chat_events.py:211-213`), and the L0 sensor reads only the live transcripts dir, so
sessions the CLI has pruned need a `resync-from-raw` entry that replays the rawstore.

### D3 — the window operation

"Read the local area around a hit" decomposes cleanly, because ordering survives at every layer:

- **prose window** — `chatlog.rows_for(session_id)` filtered to `turn_index ∈ [t−k, t+k]`
  (`core/stores/chatlog.py:185`); adjacency is the primary key, chunking never touched it.
- **action window** — same over `(session_id, ord)` in L1.
- **full-fidelity window** — resolve the row's `transcript_digest` → `RawStore.get`
  (`core/kernel/stores/rawstore.py:45`) → re-parse the ±k raw records *at read time*, tool blocks
  included. Displayed, never stored, never embedded — CS-3's anti-apophenia strip stays intact.
- For documents, the semantic rows themselves carry `(source_path, chunk_index)`
  (`core/ingest/index.py:36`), so a chunk hit expands to its neighbors the same way.

## 4. D1 — where exhaustiveness lives

"Find EVERY occurrence of clause (e)" is an exact-match census with a completeness obligation.
The two layers have opposite competencies:

- The **spine** is deterministic, total, and cheap: a SQL scan over L0/L1 is exhaustive *by
  construction*, and §2's census is the proof — a substring scan over the raw bytes found all 108
  raw firings, and the live chatlog independently reproduces the pre-horizon count to within one
  row (39 vs 40; the gap decomposes into the excluded active session, Q4, and fork-pair
  double-ingestion — both nameable, neither silent).
- The **embedding** is a similarity instrument. It ranks; it does not enumerate. Uncited
  intuition, labeled as such: k-NN retrieval has no completeness semantics at any k, and no
  recall measurement can *prove* totality — absence of a hit is not evidence of absence.

**Ruling this note proposes: the structural spine is the sole exhaustiveness authority. Semantic
search is an entry point** — "find where Alberto sounded frustrated about handoffs" is a
legitimate fuzzy anchor — **whose results are then expanded and completed through the spine.**
Never the reverse.

**Consequence for the succession path, stated because it reshapes R2:** a lineage proof carries
the same completeness obligation — a succession path that silently omits a step is worse than
none, because it *asserts* continuity. So the succession path also rides the spine (typed edges,
supersession chains, edit events), with semantic retrieval as its entry point only. The owner's
"ouroboros's retrieval stands in as proof of lineage" is honored with retrieval meaning *trace
retrieval* (this instrument), not similarity search.

## 5. D4/D5 — one contract, two walkers

The shared contract:

```
trace(anchor, spine, k) -> ordered path of typed events, each with window(±k) on demand
```

| | forensic walker | succession walker |
|---|---|---|
| anchor | event predicate (kind/ref/text) or semantic hit | artifact id (dn-/bp-/finding-/brainstorm path) |
| spine | L1 per-session order (`ord`), total per session | citation + supersession edges over artifacts — a **poset** |
| window | ±k turns via L0 / L-raw (D3) | the artifact text at that step ± its neighbor edits (L1 backptrs) |
| completeness | SQL scan (D1) | edge closure over the typed lineage graph (D1) |

They are one instrument because layers, contract, window, and completeness authority are shared.
They are **not** one flat query, and honesty requires saying why: the forensic spine is a total
order per session; the succession spine is a partial order (a note graduates to several plans;
plans merge findings back). One walker iterates; the other computes reachability over typed
edges. Same instrument, two order structures — the difference is real and lives in the walker,
not the contract.

**What the succession walker stands on today, measured:**

- `note-citation` corpus↔corpus edges: **660,577 rows** (`data/reference_edges.sqlite`,
  2026-07-27), minted per commit by φ_doc (`ops/code_sensor.py` module doc, bp-026).
- Supersession chains → poset: `core/kernel/temporal/boundary.py:99` (`poset_from_chains`),
  `ops/code_lineage.py` (per-path blob chains).
- Edit events with artifact-typed refs: L1 already logs `design_note` / `build_plan` / `finding`
  writes with ids and session/turn backpointers (`core/chat_events.py:75-86`) — **this is the
  commit-free edit-event stream R2 asked for, and it already exists.**
- **The honest gap:** the REF_TYPES vocabulary declares `design-ref`, `dn-slug`, `finding-id`
  (`core/stores/reference_edges.py:117-118`), but the live store holds **zero** rows of those
  types — only `path-mention` (1,166,062) and `note-citation` (660,577). The *typed* lineage a
  proof needs (warrant vs. mere mention; supersedes vs. cites) is vocabulary-present,
  data-absent. Minting those edges (from front-matter, which φ_doc already parses) is the one
  genuinely new extraction this note requires. Everything else is a query surface over existing
  stores.

## 6. The loop this design could create — the required self-diagnosis

Applying `context-load-as-a-feedback-loop`'s four-part destructive signature to this proposal
(the corpus ingesting transcripts of conversations about the corpus):

1. **SELF-MAINTAINED — HIT.** The system's sessions produce transcripts; its sensor ingests
   them; future sessions query the result. The same process reads and writes the node.
2. **MONOTONIC — HIT.** Rawstore and chatlog are append-only; sessions only grow.
3. **NO EXTERNAL CHECK — PARTIAL MISS, and this is a load-bearing property:** the raw transcript
   is written by the CLI harness, *outside* every corpus process, and is content-addressed and
   immutable (CS-1). The corpus cannot rewrite its own input. Every derived layer is regenerable
   from, and checkable against, bytes the loop cannot touch.
4. **AUTHORITY LAUNDERING — the live danger, already observed:** the 39 hook rows labeled
   `speaker='owner'` are laundering in its purest form — gate text becoming "the owner said."
   A dreamer conditioning on dialogue rows would compound it (L5).

**What breaks the loop, by design — each mapped to the capsule's lever ranking
(derived > checked-from-outside > cleared):**

- **Derived:** every layer above L-raw is a deterministic, versioned projection with no
  hand-written summary anywhere in the path. Nothing accumulates authority by being re-written;
  a bad extraction is fixed by bumping the interpreter and re-projecting, not by editing output.
- **Checked from outside:** the named falsifier (§9) is a from-scratch scan of the raw bytes
  that depends on no corpus store — a standing external auditor for the spine, re-runnable at
  any time. Clause-3's partial miss is thereby made permanent: the check lives outside the cycle.
- **Laundering broken structurally, twice:** (a) D2's channel/actor typing makes hook text
  `system`-authored — unrepresentable as owner speech, the same move as CS-2's
  provenance-never-from-speaker firewall; (b) dialogue rows are `observed`, and
  `observed ∉ MIRror_READABLE` (`core/kernel/provenance.py:74-80`) — structurally invisible to
  the mirror and to `semantic_search`'s introspective default (`core/ingest/index.py:122-128`).
- **Bounded output path:** the instrument *displays* windows; it stores nothing new. Its
  conclusions re-enter the system only as findings/notes through the artifact chain's one gate —
  the same rule CLAUDE.md already imposes on every insight.
- **The one step that would re-arm the loop is named and parked:** embedding chat prose would put
  the system's self-narration into the semantic substrate dreamers condition on (L5's mass).
  That is precisely clause-1 + clause-4 rejoined at the layer where beliefs are scored. Parked
  decision, owner gate, default OFF (§1.2). If a future note wires it, it must carry its own
  §6-grade diagnostic — that obligation is part of what ratifying this note means.
  `[INFERENCE]` on the default; the analysis is this note's, not an owner ruling.

## 7. Privacy and the non-negotiables

- **#2 (network and private data never share a component):** every store here (rawstore, chatlog,
  chat_events, reference_edges) is core/ops-local; the sensors are model-free with no network
  handle (`ops/chat_sensor.py:5-9` — "no inference, no embedder, no network, no vault, no
  attestor"). `edge/` gains no read path. Unchanged by this design.
- **#11 (the interface may transit a third party; the corpus never does):** transcripts are the
  most sensitive corpus there is — they contain the owner's unguarded thinking. Ingestion under
  this note keeps every byte on-machine; no adapter, report lane, or artifact carries transcript
  content off-box. What ingestion permits is *local* query; what it does not and cannot permit is
  any remote surface over the result.
- **#10 (secrets):** the fail-closed whole-session refusal guard already runs on every utterance
  (`ops/chat_sensor.py:178-218`); D2's new channels pass through the same guard (queue text is
  owner prose — exactly the guard's jurisdiction).
- **Mirror-opacity:** observed dialogue rows are structurally unreadable by the self-model
  (`core/stores/chatlog.py` module doc; `core/kernel/provenance.py:74-80`). This note adds no
  reader with a wider grant.

## 8. Consequences and build boundary

A single build plan (post-ratification, post-graduation) covering: D2 channel closure + actor fix
(sensor + projector + two additive migrations), the `resync-from-raw` backfill entry, typed
lineage-edge minting (§5's gap), and the `trace` query surface (read-only; CLI or core-query-
protocol verb). Cost shape: re-projection is model-free over 357 MB — minutes; zero embedding
spend; the 2.6 GB `code_observations`/4 GB `code_snapshots` stores are untouched.

⚑ **Every implied write surface (`ops/**`, `core/**`, `scripts/**`, launcher wiring) is inside or
adjacent to the live bp-125..127 wave's frozen dirs. Nothing here starts before that wave seals**
— the same boundary the commit-economy capsule already records. This note is design only;
implements nothing.

## Wiring & enablement

**How it wires:** the dialogue sensor and L1 projector are already daemon-wired
(`ops/lifecycle/launcher.py:492,507,528`); the stores are already registered reset targets
(`ops/lifecycle/launcher.py:1363`). The build adds: (a) interpreter bumps + additive schema
migrations; (b) a forced re-projection path — today `ChatEventProjector.project` skips when the
transcript digest is unchanged (`core/chat_events.py:211-213`), so an interpreter bump alone
re-projects nothing; (c) `resync-from-raw` — `ChatSensor.sync` reads only the live transcripts
dir (`ops/chat_sensor.py:283-287`), and the CLI prunes by retention, so backlog replay must come
from the rawstore; (d) the `trace` verb; (e) lineage-edge minting in φ_doc's existing pass.

**What it takes to flip it on:** (a) the build above lands the switches; (b) the owner runs the
backfill once — `palace <resync-entry>` (name decided at graduation) — then `trace` is a
read-only query needing no further enablement. Ingestion of the backlog is itself an owner-run
step, never autonomous — it rides the existing deploy/start gate, which remains the owner's.

## Parked decisions

- **Chat-prose vectorization (semantic entry over dialogue).** Default OFF. Re-entry: an owner
  ruling plus a note that satisfies §6 for the embedding layer (the L5 mass argument), plus the
  CS-5 correlator design it would actually serve.
- **Retro-attribution of channel-3 answers as L0 owner rows.** Marked `[INFERENCE]` in D2; owner
  confirms or strikes at ratification.
- **Whether `trace` lands in the core query protocol or as a `palace` CLI verb first.** Default:
  CLI first (read-only, ops-side), protocol verb when a core consumer exists. `[INFERENCE]`.
- **Brainstorm-batching ahead of R2** (from the commit-economy capsule) — untouched here; still
  not ruled; do not assume.

## 9. The named falsifier

**The census-reproduction test.** The instrument, run over the ingested backlog, must return
exactly the clause-(e) firing set found by the from-scratch raw-bytes scan of 2026-07-27 (§2: 108
raw / 99 fork-deduped; within its sync horizon, the store-side count must match the raw scan with
every discrepancy *nameable* — active-session exclusion, fork pairs, refused sessions — never
silent). And for the designated probe firing — `a73e8b34`, 2026-07-26T03:16:25Z — the ±9 window
must surface the queued *"I give you permission to wipe the resume"* message that the current
sensor structurally cannot see. Substituting semantic retrieval for the spine must *fail* this
test measurably; if it does not — if similarity search alone reproduces the census — this note's
central ruling (D1) is falsified and the design should be re-cut. The scan scripts are throwaway
by design; the test is re-derivable from §2's method paragraph alone.

## Cross-references

`ops/chat_sensor.py` (φ_chat, CS-1/CS-3; `:64` role map, `:124-129` queue blindness, `:178-218`
secret guard, `:283-287` dir-only read) · `core/stores/chatlog.py` (`:76-92` ordered schema,
`:185` `rows_for`) · `core/chat_events.py` (`:47-50` EVENT_KINDS, `:136-176` extractor,
`:211-213` digest-keyed skip) · `core/stores/chat_events.py` (`:40-52` L1 schema) ·
`core/kernel/stores/rawstore.py` (`:45` `get`) · `core/kernel/stores/sourceset.py` (source-set
relation) · `core/ingest/index.py` (`:27-40` chunk rows, `:122-145` search entry points) ·
`core/stores/vectorstore.py` (`:97-118` additive-migration precedent) ·
`core/stores/reference_edges.py` (`:117-124` REF_TYPES/KINDS) · `ops/code_lineage.py` ·
`core/kernel/temporal/boundary.py` (`:99`) · `ops/lifecycle/launcher.py` (`:492,507,528,1363`) ·
`.claude/hooks/_lib.py` (`:892-920` clause (e)) · measured stores: `data/chatlog.sqlite` (9,145
utterances / 173 sessions / 39 mislabeled hook rows), `data/chat_events.sqlite` (22,031 events),
`data/reference_edges.sqlite` (1,826,639 edges: 1,166,062 path-mention + 660,577 note-citation;
zero design-ref/dn-slug/finding-id) — all read-only, 2026-07-27.
