# Embedding-space specialization — one geometry or many?

Brainstorms on whether the corpus should be embedded by ONE model or several specialized ones
(by language, by modality, by layer), and what that choice costs. Sibling of
`ops-and-optimal-form.md` — the same "what is the optimal representation?" question, one level up:
that capsule asks about the form of the *data*, this one about the form of the *space*.

## 2026-07-25 — "different priority embedders?" (the multilingual question)

```capsule
topic: embedding-space-specialization
date: 2026-07-25 (session-44, ~01:40, alongside the ops-track work)

warrant (owner, verbatim): "is there such a thing as different priority embedders? that is, maybe
one embedder is better for capturing english, for example, but it might not properly capture the
essense of spanish"

GROUNDED FIRST (measured, not assumed — config/defaults.toml:112-118 + `ollama list`):
  the palace runs **`qwen3-embedding:4b`, 2560 dims**. Qwen3-Embedding is multilingual by design
  (trained across 100+ languages), so Spanish is genuinely represented rather than incidental —
  a materially better starting position than the English-centric defaults (nomic-embed-text,
  mxbai-embed-large) the owner's worry would apply to sharply. The config also already notes
  Qwen3-Embedding is **instruction-aware on the QUERY side; documents embed plain**.

⚑ THE CONSTRAINT THAT DOMINATES THE QUESTION:
  **Vectors from different embedders live in DIFFERENT SPACES.** Cosine between a vector from
  model A and one from model B is not worse — it is MEANINGLESS (no shared origin, axes, or scale).
  So "a different embedder for Spanish" is not a per-document knob. It is a decision to SPLIT THE
  GEOMETRY INTO DISJOINT PLANES.
  For THIS system that is unusually expensive, because the single shared space is load-bearing:
    · dreams cluster over the whole corpus
    · the sigma-graph draws edges by cosine — and defaults.toml:268-271 already states
      sigma in [0.55, 0.75] is "corpus- and EMBEDDER-specific", so two embedders = two calibrations
    · near-duplicate detection (the Jul-23 note pair at cosine 0.990) assumes one metric
    · the fiber-geometry survey assumes one space to survey
  Split it and cross-lingual retrieval (a Spanish note surfacing an English doc) dies outright
  unless an alignment step is added. Fragmenting the geometry fragments what the palace IS.

THE FOUR OPTIONS, honestly costed:
  (1) ONE multilingual model (status quo). Shared space; cross-lingual retrieval works. Cost: the
      "curse of multilinguality" — fixed capacity spread across many languages, so each is somewhat
      weaker than a dedicated monolingual model would be.
  (2) MULTIPLE embedders -> multiple planes. Query-time routing, per-plane sigma calibration, NO
      cross-plane comparison. Loses cross-lingual entirely.
  (3) LEARNED ALIGNMENT between spaces — orthogonal Procrustes over anchor pairs (the
      Mikolov / Artetxe VecMap line). Real, but research-grade: introduces a learned artifact whose
      residual error contaminates every downstream metric. Would itself need a falsifier.
  (4) ⚑ THE CHEAP LEVER ALREADY PRESENT — Qwen3-Embedding's query-side instruction awareness. Steer
      retrieval with query-side instructions WITHOUT touching the space. Exhaust this first.

RECOMMENDATION (mine, offered — not a decision):
  **Do not split the space on a suspicion.** "Spanish is under-served" is exactly the shape of claim
  that f-0163 (PD-B's cost premise) and f-0169 (the re-land idiom's cost premise) were — a
  quantitative premise ASSERTED rather than MEASURED, one week apart, twice. It is measurable:
    · do non-English chunks show anomalous norms / anisotropy vs English ones?
    · does a Spanish note retrieve its English counterpart (cross-lingual pair test)?
    · is retrieval precision language-dependent at fixed k?
  Natural first customer for the evaluation-harness ladder (docs/brainstorms/evaluation-harness
  capsule) — a per-language retrieval readout with HONEST NULLS.
  Switching later is anticipated by the design, not a trap: `[embedding]` reads dimension from
  config precisely so **re-embedding from raw (§8) on a model change** works. But a model change is
  a FULL RE-EMBED, which is unaffordable until bp-100 lands (finding-0169).

⚑ OPEN PREMISE — NOT YET CONFIRMED BY THE OWNER:
  Whether the corpus contains non-English material TODAY, or whether this is forward-looking. Asked,
  unanswered at capture time. It changes the work from "measure a live gap" to "record a constraint
  before it bites". DO NOT treat the Spanish-content premise as established.

THE PROBABLY-MORE-URGENT VARIANT OF THE SAME QUESTION:
  **code vs prose.** The palace embeds source, docstrings, and comments (layers code_ast /
  code_text / codedoc) with the SAME model as authored prose. Code-specific embedders exist, and
  the identical space-splitting constraint applies. Given [[code-must-be-vectorized]] (code is a
  first-class semantic source, owner ruling 2026-07-21) this is live now, whereas the multilingual
  case may be forward-looking. Same question, nearer horizon.

open questions:
  - Is there a measurable per-language quality gap in THIS corpus at all? (Unknown; nobody has
    looked. That is itself the finding-shaped observation.)
  - Does layer-aware retrieval already recover most of what a code-specific embedder would buy?
    (The layer field exists and is queryable — cheaper than a second model if so.)
  - How does this interact with quantization (ops-and-optimal-form capsule 1)? Quantizing a
    multilingual space may degrade low-resource languages FIRST and unevenly — a compression
    decision with a fairness-shaped failure mode, and one that would not show in an English-only
    eval.
  - If the space is ever split, what carries cross-plane meaning — membership (f-0168), which is
    NOT geometric? Membership might be exactly the invariant that survives a geometry split.
    Worth thinking about before, not after.
```
