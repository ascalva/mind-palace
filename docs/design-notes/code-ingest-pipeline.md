---
type: design-note
id: dn-code-ingest-pipeline
track: code-ingest
status: ratified            # draft → ratified → superseded.  draft→ratified is an OWNER-ONLY hand edit.
implementation: design-only   # nothing built; corrects the plane model, licenses the CI-* plan family
created: 2026-07-21
updated: 2026-07-21
links:
  - docs/findings/finding-0146.md                      # THE WARRANT — owner ruled the un-vectorized code corpus a BUG
  - docs/findings/finding-0145.md                      # sibling — the reference-sensor staleness/shorthand axis (L2b pairs with it)
  - docs/design-notes/code-observation-projection.md   # RATIFIED — partially SUPERSEDED by this note (§2.6 banner; the rest absorbed)
  - docs/design-notes/fiber-geometry.md                # RATIFIED — the S/F/D/C alphabet code nodes enter; S↔F mismatch instrument
  - docs/design-notes/agent-taxonomy.md                # RATIFIED — sensor role, fiber C, fiber-vs-edge criterion, "code is observed strata"
  - docs/design-notes/agentic-loop.md                  # RATIFIED — §2.4b exhaust/self-authored + origin(e); the C-witness spine
  - docs/design-notes/authorship-distance-axis.md      # DRAFT — a₂ cross-map; footprint meet; the PD-1 self-authored gate
  - docs/design-notes/self-sensing.md                  # RATIFIED — interpreter-version supersession; the §2.6 regress line
  - docs/design-notes/chat-sensor.md                   # RATIFIED — CS-3 tool-strip / duplication-apophenia precedent
  - docs/design-notes/inner-outer-core.md              # RATIFIED — ring placement of the new lane
  - docs/design-notes/cross-strata-dreamer.md          # RATIFIED — XS-a per-grant ruling (§2.3's dream-grant posture)
supersedes: dn-code-observation-projection         # intended at ratification: PARTIAL supersession of dn-code-observation-projection (§2.6)
superseded_by: null
warrant: docs/findings/finding-0146.md
---

# The code ingest pipeline — three layers: the code, its documentation, and the bridge into the corpus

> Composed by an orchestrator-dispatched worker (2026-07-21, design pass on finding-0146 —
> the owner ruled the un-vectorized code corpus a **critical bug**, not an open question).
> **Provenance correction (audit):** the worker was spawned `fable/max` but its completion
> usage shows it ran at `claude-opus-4-8` (the known worker-dispatch downgrade bug); the
> original banner's "Composed at fable" self-report was **false** — a live instance of
> banners-as-unreliable-self-report. **Audited line-by-line at fable** (`claude-fable-5`,
> main loop, 2026-07-21): every `path:line` ground-citation opened on disk, every graded
> claim re-checked, every decision re-derived against the hard constraints, live stores
> re-queried at `625a058`; corrections applied in place, logged in
> `docs/findings/finding-0147.md`. Filed as `draft`; ratification is an owner-only hand
> edit; `/graduate` refuses this note until `status: ratified`. **Design only; no build is
> authorized beyond §3's plan family.** Every nontrivial claim carries a grade
> (`[ESTABLISHED]`/`[DERIVED]`/`[INFERENCE]`/`[ANALOGY]`); external-literature claims are
> `[FROM MEMORY]`. The correction to `dn-code-observation-projection` is announced in §2.6
> — banner-on-correction, never silent.

## 1. Purpose and scope

### 1.1 What this note decides

The owner's ruling (finding-0146, 2026-07-21): the code — its source, its docstrings, its
comments — **is a semantic source and must be embedded**. Today it is not: the only embed path
(`core/ingest/pipeline.py:71-76`, `ingest_vault`, globs `**/*.md`) takes vault notes only;
`vectors.lance` holds **28 AUTHORED note chunks / 19 note centroids** and zero lines of code
(finding-0146 §"The defect", live-store count at HEAD `db5fc0d`). The code sensor
(`ops/code_sensor.py:1-43`) is model-less *by construction* and vectorizes nothing; inline `#`
comments enter **no store at all** (`ops/code_snapshot.py` captures only `ast.get_docstring`,
`:158,131-136`); and code→doc references resolve literal paths only
(`_RE_NOTE_CITATION`, `ops/code_sensor.py:109` — 19 captured vs 165 `dn-<slug>` + 55
`finding-NNNN` + 968 `§` tokens in core docstrings, finding-0146's table). `[ESTABLISHED]`

This note designs the fix as the owner framed it — **three layers**:

- **Layer 0 — the code itself, in TWO sublayers (owner refinement, 2026-07-21).**
  **L0a — the structural (AST) reading:** per-symbol ingestion; each symbol a node decorated
  with its name, carrying the AST's edges between symbols (containment, calls, inheritance).
  **L0b — the windowed textual reading:** the note chunker's sliding char-window applied to
  the raw source — code-as-written, bodies and inline comments flowing together. Two
  independent semantic readings of the same code, both embedded, deterministically joined
  (§2.1).
- **Layer 1 — the code documentation.** Docstrings + comments, embedded the way notes are —
  prose with code stripped, living in the note space; belonging to (contained in) their file
  (§2.2).
- **Layer 2 — code↔docs integration.** (a) the deterministic "these comments refer to this
  code" tie; (b) the edges bridging code/docstrings to the doc corpus — and, once both sides
  share one embedding space, the S-fiber bridge (§2.4, §2.5).

It also decides: the embedder (§2.1b), whether L1 combines with L0b (§2.2 — ruled: distinct,
tightly joined), the provenance class and its composition with the authorship/exhaust
machinery — mirror firewall intact (§2.3), the D/C fiber composition — supersession grain,
incremental re-embed keying, and `origin` over code versions (§2.5b), the reconciliation with
the ratified two-plane note this corrects (§2.6), ingest weight and sequencing against the
memory ceiling (§2.7), and the build order (§3).

### 1.2 Out of scope

- **The Track-D correlator/detangler** — unchanged; it gains substrate here, not a charter.
- **Any change to `MIRROR_READABLE`**, the verdict taxonomy, or the effector tier
  (finding-0011 stands).
- **Multi-scale ("smear") embedding of the *note* corpus** — the standing single-scale-at-
  chunk-grain decision is untouched; §2.1's partition rule keeps code single-scale too.
- **The reference sensor's scheduling/current-view build** (finding-0145 / PD-5) — a sibling
  track; L2b (§2.4) shares its extraction seam but this note does not design its store pass.
- **Non-Python surfaces** (`.toml`, `.sh`, notebook cells) — parked (PD-G).

## 2. Principles / decisions

### 2.1 D1 — Layer 0: two sublayers — the AST reading (L0a) and the windowed reading (L0b), joined

**The ruling (owner refinement, 2026-07-21): L0 is TWO independent semantic readings of the
same code, both embedded, deterministically cross-linked.** Not one grain but two — a
structural reading whose boundaries follow the tree, and a textual reading whose windows
ignore it. Two independent measures of one artifact cross-check each other *and* capture
different semantics; this is the house redundant-reading pattern — the strict-vs-lax ring
scanners cross-checking (`dn-inner-outer-core`), the S↔F two-measures-diverge discipline
(`dn-fiber-geometry` §2.2: "two measures diverge and the divergence is the signal").
`[DERIVED — pattern reuse; the cross-check value claim is [INFERENCE] until M-C8 reads it]`

**L0a — the structural (AST) reading: symbol nodes + AST edges.**

- **Unit:** one embedded chunk per symbol — function / async function / method / class /
  module shell (the file's code outside every top-level symbol slice: preamble, inter-symbol
  statements, trailing code — the module treated as the outermost parent, so byte-cover holds) —
  the verbatim source slice at AST-given boundaries, docstring and comments
  in place. Nested defs are their own symbols (`_walk_defs` recurses, qualname `Cls.method`,
  `ops/code_snapshot.py:126-137`), so a parent embeds as its *shell* (its slice minus child-
  symbol slices) — each source line appears in exactly one L0a chunk (single-scale within the
  sublayer; the parked note-smear decision is not reopened). Each chunk is prefixed with a
  deterministic header `# {path}:{qualname}{signature}` — the owner's "each node decorated
  with its name," in the embedded text where it does retrieval work. Oversized slices
  hard-split via `chunk_text` (`core/ingest/chunk.py:44-56`).
- **Extraction:** the snapshot walk already enumerates exactly these symbols with
  qualname/signature/lineno (`ops/code_snapshot.py:60-69`); L0a adds `end_lineno` (on every
  `ast` node) so a slice is `(path, qualname, lineno..end_lineno)` — an additive ledger
  migration in the `open_snapshot_db` pattern (`:296-318`). `[DERIVED]`
- **The AST's edges, typed by the house criteria — not one bucket:**
  - **containment** (module ⊃ class ⊃ method) is one-stratum, re-derivable from the blob ⇒ a
    **fiber**, carried on the rows as `(path, qualname, line-range)` backpointers
    (`dn-agent-taxonomy` §2.4's criterion; §2.4 here) — never minted as edge rows.
  - **inheritance and calls** are inter-symbol structural relations ⇒ **`code_to_code`
    reference edges** — a direction the v2 symmetric store already admits and nothing yet
    mints (`core/stores/reference_edges.py:104-107`: "`code_to_code`, reachable, not minted
    anywhere yet"). New ref_types `inherits` / `calls`, precision-first per the bp-011
    discipline: v1 mints only **statically resolvable** targets — base/callee names resolving
    within the module; cross-module resolution is NOT free today (audit correction): the
    ledger's `imports` table records only the ROOT of each dotted import
    (`ops/code_snapshot.py:70-75`; `_module_imports` splits to `[0]`, `:140-147`), which cannot
    map an imported name to its defining module, so CI-3 includes an **additive import-record
    extension** (full module path + imported names, the same `open_snapshot_db` migration
    pattern) as the precondition for any cross-module mint. Dynamic dispatch and attribute
    chains are dropped, not guessed (PD-I parks the fuller call graph). Balance-math isolation
    is inherited from the store's standing invariant (`reference_edges.py:1-10,50-56`).
    `[DERIVED — the store seam exists; the import-record gap is named; resolution precision
    gates per pattern, M-C6]`

**L0b — the windowed textual reading: the note path applied to raw source.**

- **Unit:** the existing sliding char-window — `chunk_text`'s blank-line-aware packing with
  overlap (`core/ingest/chunk.py:31-56`, the ONE window machinery) — applied to the file's
  **raw source text**, boundaries ignoring the tree. Bodies and inline `#` comments flow
  together exactly as written: the reading is *"what is this code region about,"* local
  co-occurrence and comment-as-code-texture included. Maximal DRY at the right seam (audit
  correction): the reused unit is `chunk_text`, NOT `derive_chunks`
  (`core/ingest/pipeline.py:22-34`) — that wrapper is the *note* lane's raw→chunks derivation
  and bundles two note-specific steps, the tolerant decode and the Logseq `strip_properties`
  pass; the strip must not run on code (0 tracked `.py` lines match `_PROP` today — measured
  at audit — but the exclusion is structural, not luck). `[DERIVED]`
- L0b is what catches semantics the tree hides: cross-symbol locality (a helper beside its
  caller), region-level comment context, module "paragraphs" that straddle def boundaries.
  L0a is what catches semantics the window smears: the whole-symbol atom, name-anchored.

**The join (load-bearing): deterministic alignment, no inference.** Every L0a symbol node
aligns to the L0b window chunk(s) covering its line range — computed from the two layers'
line-range coordinates carried on the rows (file + line-range containment; the same
backpointer fiber as containment, so **no edge rows** — a derived join, the `origin`-view
posture of §2.4b/EX-2 applied here). Any code region therefore has both a structural
embedding and a textual embedding, cross-linked by construction. *The disagreement is itself
an instrument:* the **structural↔textual mismatch** — an L0a symbol vector far (in cosine)
from the centroid of its covering L0b windows — is the S↔F mismatch shape one floor down
(same-object two-readings divergence: a symbol whose in-context texture says something its
own body does not, or vice versa). Read by M-C8; graded `[INFERENCE]` until it shows signal
on the real corpus; a null parks it as vocabulary.

**Rejected alternatives (recorded):**
1. *Node-as-graph-vertex embeddings* (AST nodes as structural tokens / GNN-style): needs a
   new model class, violates the deterministic floor's shape, and produces vectors in a space
   disjoint from the note space — killing the L2 bridge that is the point. Rejected. The
   structural information those vertices would carry lands instead as the typed
   `inherits`/`calls` edges + containment fibers above — recorded structure beside computed
   similarity, the ratified S-vs-recorded split (`dn-fiber-geometry` §2.0).
2. *Token-per-AST-node rows*: ~10⁵ near-meaningless vectors; an embedding of `BinOp` carries
   no retrievable semantics. The AST's value here is **boundaries + names + edges**, not
   vertex identity. Rejected. (`[INFERENCE]` on the retrieval half; definitional otherwise.)
3. *One layer only* — either alone: L0a-only loses locality/texture; L0b-only loses the
   symbol atom and was the note-path bug's shape applied to code. The owner's two-reading
   ruling supersedes the single-partition draft this pass first considered (windows straddle
   defs *by design* in L0b — that is the independence, not a defect).

**Multi-grain shape — the sourceset echo, computed not stored.** A file's vector is its
**centroid over its chunks** (per layer, or pooled — a read-time choice), computed on read
exactly as note centroids are today
(`core/complex/build.py:121-124` → `core/dreaming/cluster.note_centroids`; live corpus 28
chunks → 19 centroids). The vector store's `digest` column carries the **git blob sha** of the
file (git is already the content-addressed raw store for code — adding blobs to `RawStore`
would duplicate a content-addressed store with a content-addressed store; DRY), so the
established group-by-digest machinery (`core/stores/sourceset.py`: "a source object IS the set
of its idea-vectors"; `grouped_semantic_search`, `core/ingest/index.py:124-138`) works for code
**unchanged**: source object = file, members = its L0a/L0b/L1 chunks. No new grouping
machinery. `[DERIVED]`

### 2.1b D2 — the embedder: reuse `qwen3-embedding:4b`; one space or no bridge

**Ruling: the note model, unchanged** (`config/defaults.toml:96-100`, `qwen3-embedding:4b`;
adapter `core/ingest/embed.py:26-34`). Three grounds, the first decisive:

1. **The bridge requires one space.** L2's payoff — S-fiber similarity between code and design
   notes, the S↔F mismatch instrument for code↔design (`dn-fiber-geometry` §2.2) — is only
   defined if code chunks and note chunks are points in the *same* embedding space. A
   code-tuned second model gives better code↔code neighborhoods and **no code↔doc geometry at
   all** (two incomparable spaces; alignment projections are machinery-ahead-of-need).
   `[DERIVED]`
2. **The memory ceiling (non-negotiable #8).** A second resident embedder competes with the
   pinned router + slot-2 budget (`config/defaults.toml:111-132`); the deploy-vs-ingest memory
   race just observed is the live warning. One embedder, already resident on the ingest path,
   adds zero model footprint.
3. **Qwen3-Embedding is trained on code as well as prose** `[FROM MEMORY — verify at the
   external-grounding gate; the model card claims code retrieval competence]` — and the
   embedder is already versioned (A7: embedder-version pins; re-embed from raw on change), so
   a later model swap is an amendment, not a redesign.

**Rejected:** a code-tuned embedder (ground 1+2); dual-space with learned alignment (ground 1,
plus no harness to tune it). **Re-entry (PD-C):** if the M-battery (§2.8 M-C3/M-C4) shows
code↔doc neighborhoods are degenerate or code↔code retrieval is materially worse than a
code-tuned baseline *measured offline*, the swap re-enters as an embedder-version bump — the
full re-embed path already exists (`vectorstore.reset`, `core/stores/vectorstore.py:72-77`).

### 2.2 D-L1 — Layer 1: docstrings + comments, embedded the way notes are

**What embeds.** Per file, the **prose view**: module docstring, every symbol docstring, and —
new capture — every inline `#` comment, assembled **in source order** with its coordinate
header (`{path}:{qualname or line}`), then chunked by the ONE window machinery `chunk_text`
(`core/ingest/chunk.py:31-56`; `derive_chunks`' note-specific property-strip does not apply
to code — §2.1 L0b) — the owner's DRY rule applied: the note
chunker, the note embed call (`index_records`, `core/ingest/index.py:43-58` row assembly via
`_chunk_row`), the note store. The file *contains* its L1 chunks exactly as it contains its L0
chunks: same `digest` = blob sha, same group-by-digest superset relation. A `layer` coordinate
(`code_ast` = L0a | `code_text` = L0b | `codedoc` = L1; existing note rows default `prose`)
discriminates the projections — one additive vector-store schema extension, delivered by
rebuild (vectors are derived and regenerable, §8 doctrine; `vectorstore.reset` is the
idempotent path). `[DERIVED]`

**The comment capture (closing finding-0146 defect 2).** Today `#` comments exist in no store
(`ops/code_snapshot.py` stores only `ast.get_docstring` output — `:158`, `:131-136`; the AST
drops comment trivia). Capture is a **tokenize pass** (stdlib `tokenize`, `COMMENT` tokens —
3,318 of them across the 247 main-package `.py` files, "main-package" =
`{core, ops, edge, config, scripts, agents, eval}`, tests excluded; reproduced exactly at
audit), recorded at
symbol grain by line-range containment (a comment belongs to the innermost symbol whose
`lineno..end_lineno` spans it; file grain otherwise). Lands as a new `comments` column/sidecar
in the snapshot ledger (additive migration, `open_snapshot_db` pattern) so φ_code remains the
**sole interpreter** of the code stream (`dn-code-observation-projection` §2.2, preserved) and
L1's prose view is derivable from the ledger without a second parser downstream. The tokenize
pass rides the same blob walk (one read per blob, cached — `snapshot_commit`'s `_cache`
discipline, `ops/code_snapshot.py:193-208`). `[DERIVED]`

**Why L1 is its own layer and not folded into L0b (the owner's "combines with?" question,
ruled DISTINCT-but-JOINED).** L0b already embeds comments *in place* (raw source includes
them), so one might fold docstrings/comments there and drop L1. Rejected, three grounds:
1. **Different query, different space membership.** L1 is *prose*, chunked and embedded like a
   note — it is meant to sit in the note neighborhood ("find where we *explained* X"), and its
   S-edges to design notes are the L2b bridge's whole point (§2.4). L0b is *code texture*
   ("what is this region about"); its neighbors are other code. Folding L1 into L0b would put
   the prose in the code neighborhood, weakening exactly the code↔doc bridge finding-0146
   demands. `[DERIVED]`
2. **L1 is symbol-attributed prose; L0b is window-attributed text.** L1 carries `(path,
   qualname)` so "the documentation of symbol X" is a clean join (§2.4 L2a); L0b's windows do
   not respect symbol boundaries. The two attributions are both wanted.
3. **The tie is kept, not lost.** L1 and L0b are *joined* by the same line-range containment
   the L0a↔L0b join uses (§2.1) — a comment's L1 chunk and the L0b window covering it are
   cross-linked deterministically. So nothing is disconnected by separating them; the prose
   simply also lives, cleanly, in the note space.

This is the sensor-role layer family exactly (`dn-agent-taxonomy` §2.4 — one source, layer
projections at declared grains): **three co-registered projections of one file — L0a
(structural), L0b (textual), L1 (prose) — cross-linked by line-range, discriminated by a
`layer` coordinate.** No new pattern. `[DERIVED]`

### 2.3 D3 — provenance: a new `CODE` class — structurally minted, mirror-excluded, dreamable by grant

**The ruling.** Add **`Provenance.CODE`** ("builder-produced reality read from the repo
instrument") to the enum (`core/provenance.py:44-61`), with:

- **∉ `MIRROR_READABLE`** (`core/provenance.py:78-80` unchanged): a `MirrorView` refuses code
  rows by construction; `semantic_search`'s default stays MIRROR_READABLE
  (`core/ingest/index.py:115-121`), so the mirror and the §15 baselines never see code. The
  firewall is untouched. `[ESTABLISHED — the mechanism exists; this adds a class outside the set]`
- **Structural mint.** The code lane's row assembly hardcodes `CODE` — **no provenance
  parameter anywhere on its API** (the `CodeObservation.to_row` / `DerivedStore` move,
  `core/stores/code_observations.py:146-150`). A caller physically cannot launder code into an
  authored class. The lane does NOT reuse `ingest_note`'s provenance-parametric entry
  (`core/ingest/pipeline.py:49-51`) precisely because that parameter is a laundering surface
  here; it reuses the *chunk/embed/row* machinery below the parameter.
- **Dreamable by deliberate grant.** The dreamer's synthesis reads code via
  `provenances={CODE}` — the exact CURATED precedent (`core/provenance.py:29-30`,
  `core/ingest/curated.py:1-14`: own graph, never merged into the mirror, deliberate
  non-default query). Cross-strata dream grants name it per `dn-cross-strata-dreamer`'s
  per-grant ruling; the default grant excludes it (default-deny is already how every
  provenance filter works). Ouroboros can dream over its own implementation — deliberately,
  never by default. `[DERIVED]`

**Why a new class and not one of the existing six:**
- **Not `OBSERVED`:** the enum's own docstring scopes it "third-party behavioral exhaust …
  assistant-tier only" (`core/provenance.py:33-34,59-61`) — already strained by agent dialogue
  rows (dn-agentic-loop G-C); adding the entire codebase would make one label cover three
  unlike populations and force every observed-tier consumer to sub-filter. Rejected — though
  the *α cross-map is the same*: code is **a₂ (author-sensed)** — the repo as instrument
  reading the build — exactly the cross-map the ratified projection note recorded (§2.1
  there), preserved here.
- **Not `AUTHORED_*`:** masquerade at origin — builder output entering the self-model's food
  supply is the exact leak the ratified note named; that reasoning survives this correction
  verbatim.
- **Not `CURATED`:** code is not "others' words the owner selected"; erasing the
  testimony-vs-measurement line was rejected once already (ratified §2.1) and stays rejected.
- **Not `INTERPRETED`:** the chunks are measurements/projections of the repo, not system
  inference over the corpus; and INTERPRETED's mint is structurally reserved to `DerivedStore`.
- **Not `DERIVED_STRATUM`** (the sixth class the drafted pass omitted — audit addition):
  reserved for promoted, depth-carrying dreamer outputs that re-enter reasoning as substrate
  (`core/provenance.py:49-56`) — trusted as to origin, untrusted as to truth. Code chunks are
  instrument readings, not model-generated strata; spending the reserved label here would
  conflate measurement with dream substrate and burn the recursive-Dreamer unpark path.

**Composition with the authorship/exhaust machinery (the AL-3 / bp-088 layer).** The corpus
now knows *which dialogue produced which code*: 4,084 witnessed C-edges at the AL-3 seal
(4,160 live at audit, 2026-07-21 — the integrator keeps minting), commit-keyed
(`dn-agentic-loop` §2.0, §2.4b EX-2), and the `exhaust ⊂ dialogue` refinement + `origin(e)`
view are built (`core/scope.py:79-90,100-107` — EXHAUST as an excluded-by-default refinement).
The composition, ruled:

1. **One provenance class, authorship by witness — not two classes.** Owner-authored code
   (hand edits: D-event without C-witness) vs agent-authored code (C-witnessed, exhaust-
   descended) is a **row/witness-level attribution**, resolved through `origin`: a code chunk's
   `digest` (blob sha) + the snapshot's commit key joins to the C-edge that produced it, or to
   none (= owner hand edit / pre-agent history). Splitting the enum by author would repeat the
   producers-are-unbounded mistake §2.4b already rejected ("NOT a stratum per agent"); the
   discrimination the trust math needs arrives as the **α footprint** (a₂ base; the
   self-authored `w(a_self)` entry lands at the axis note's PD-1 gate, not here). `[DERIVED]`
2. **Code chunks are not exhaust rows.** The `exhaust` refinement covers agent-side *dialogue*
   rows; code is the exhaust's *product*, already provenance-spined to its producing dialogue
   by C (EX-2's "mint a view, never a second store" — reused verbatim). No `exhaust` tagging
   of code rows; `origin(e)` reaching code chunks is the typed answer to "is this agent-made?".
3. **Trust propagation composes unchanged:** a derived claim over code support carries the
   footprint meet (α̂ ≤ a₂), is dreamer-proposed until verdict-certified, and earns lift only
   via distinct-interpreter corroboration (the EX-2 four-mechanism stack) — with one *new*
   corroborator this note names: **the test suite / CI is a distinct deterministic interpreter
   of the same code**; a green gate is corroboration-shaped evidence about behavior claims.
   Registered as vocabulary, not machinery (`[INFERENCE]` — a Track-D-adjacent consumer would
   have to type it; nothing builds on it here).
4. **Stratum unchanged:** "code is observed strata" (`dn-agent-taxonomy` §2.3) stands —
   stratum ≠ provenance; grants reach code stores via the observed/reference_repo vocabulary
   as today; the vector rows are provenance-filtered, which is the operative gate on every
   semantic surface.

*Falsifier F-CI1:* a code chunk row surfacing through any `MirrorView`/MIRROR_READABLE-default
read, or any code-lane API accepting a provenance argument ⇒ the firewall composition failed;
stop, treat as a firewall incident (the F-AL4 posture), not a bug.

### 2.4 D-L2 — Layer 2a is a fiber, not an edge; Layer 2b is the shorthand resolver

**L2a — docstring/comment ↔ code: STRUCTURALLY FREE, and ruled a fiber (backpointers), not an
edge store.** A symbol's docstring is its first statement; a comment's owner is the symbol
whose line range contains it — observer-independent, zero inference. But the house criterion
rules on *storage*: "structure re-derivable from ONE stratum's retained raw is a **fiber** —
store it on the data (backpointers); structure whose derivation requires jointly reading ≥ 2
strata is an edge" (`dn-agent-taxonomy` §2.4, verbatim). Docstring↔code is one-stratum,
re-derivable from the blob. **Ruling: L2a is carried on the rows** — every L0 and L1 chunk row
carries `(path, qualname, line-range)` coordinates (the `sourceset` backpointer pattern), and
"the documentation of symbol X" / "the code this comment refers to" are derived joins over
those coordinates plus the shared `digest`. No containment edges are minted into
`reference_edges`; minting them would pollute the reference graph with derivation stars —
the exact failure §2.4 names. This *corrects the dispatch framing* ("a deterministic
`documents`/containment edge") by the ratified criterion — extension announced, not silent.
`[DERIVED]`

**L2b — code/docstrings → the doc corpus: fix the resolver (the finding-0145 axis).** The
extractor exists and is precision-validated for literal paths (`VALIDATED_PATTERNS`,
`ops/code_sensor.py:104-111`; bp-011's 100%-precision bar). The gap is shorthand — the
dominant citation forms. Ruling, precision-first per the bp-011 discipline:

1. **`dn-<slug>` → `docs/design-notes/<slug>.md`** and **`finding-NNNN` →
   `docs/findings/finding-NNNN.md`**: deterministic, collision-free resolutions against the
   tree at the same commit (`git ls-tree` walk already in `_corpus_reference_edges`,
   `ops/code_sensor.py:414`); unresolved tokens are dropped, never guessed. New ref_types
   (`dn-slug`, `finding-id`) enter `REF_TYPES` (`core/stores/reference_edges.py:102`) —
   additive vocabulary. A hand-checked precision sample gates each pattern before it is
   trusted (the V4/bp-011 protocol, reused; falsifier F-CI6).
2. **`§N` tokens resolve only when PAIRED**: a `§` reference in a docstring binds to a note
   already cited in the *same docstring* (path, `dn-slug`, or wikilink); the edge minted is to
   that note with `source_detail` carrying the section anchor. An unpaired `§N` is ambiguous
   (whose §N?) and is **dropped** — 968 tokens is a volume argument for the paired rule, not
   for guessing. `[DERIVED — precision-first]`
3. **The example-path false positive** (finding-0146: the sensor's own docstring example
   `docs/design-notes/x.md` minted a real edge): fixed by an explicit NEW rule (audit
   correction — the drafted text implied (1)'s existence check already covered this; it
   covers only the new shorthand patterns): **every corpus-target mint gains the tree-
   existence check**, the existing literal `note-citation` pattern included — which today
   mints with no existence check at all (`extract_references`, `ops/code_sensor.py:243-247`).
   A target absent from the tree at that commit is dropped; that kills the `x.md` class. The
   residual (existing paths cited as *examples*) is accepted as noise at Lane-1's measured
   precision, re-checked by the F-CI6 sample. Recorded honestly rather than over-engineered.

**The NEW capability — the S-fiber bridge (why L0+L1 change what L2 can see).** Once code
chunks and note chunks share one space, **S (similarity) spans code↔docs** with no new
machinery — the σ-graph's kernel computes it (`dn-fiber-geometry` §2.0: S is computed, not
recorded). That activates the fiber-geometry mismatch instrument for the code↔design pair
(§2.2 there, S↔F):

- **resemblance without citation** (high cosine code↔note, no F-edge) = *undocumented
  realization* — code implementing a design nothing cites;
- **citation without resemblance** (F-edge, low cosine) = *drift* — code citing a note it no
  longer resembles.

Both are census-adjacent readings over `composed.edge_classes` + the reference store —
licensed as a survey lens (§3 CI-4), records-not-causes vocabulary binding. `[DERIVED]`

### 2.5 The big picture — code as a first-class σ-graph citizen (the self-map completed)

With §2.1–§2.4 landed, code enters the **same S/F/C/D algebra** as the corpus, with every
fiber already populated or computed:

| fiber | code instance | status after this note |
|---|---|---|
| **S** | cosine over L0a/L0b/L1 chunks, and across to notes | computed by the kernel once embedded (CI-1) |
| **F** | `reference_edges` code↔corpus (shorthand-resolved) + `code_to_code` inherits/calls | extractor exists; resolver fixed + code_to_code minted (CI-3) |
| **C** | dialogue → commit → file, witnessed; node-keyed authorship join (§2.5b) | **live** — 4,084 edges at the AL-3 seal / 4,160 at audit; node-keyed reader is CI-2's rider (PD-J) |
| **D** | blob version chain per path + orthogonal embedder-version axis (§2.5b) | **recorded** — snapshots ledger carries the chains; the store-free poset core is ready but not yet wired to them (§2.5b); drives incremental sync |

The palace is a self-map ("mining my own brain"); its largest artifact — the code, carrying
the math and the §-warrants — was the one region outside the map. This note pulls it in under
the same instruments (σ*/conductance/curvature/census/dreamer-by-grant) rather than minting a
parallel apparatus for it. `[DERIVED — each cell above cites built machinery]`

### 2.5b D-DC — the D and C fibers over code: version chain + dialogue origin (owner refinement)

The owner named "D-fiber = git version chain via the temporal machinery; C-fiber already links
dialogue→code" as part of the big picture. Made precise, so the embed lane composes correctly
with the built fabric rather than duplicating it.

**D over code — the version chain is the blob lineage, and it is NOT re-minted here.** A file's
supersession chain is `blob_sha(v) → blob_sha(v+1)` along the path's commit history — already
carried by the snapshots ledger (`ops/code_snapshot.py:49-59` `files.blob_sha` per commit).
The temporal machinery is READY for those chains, not yet wired to them (audit correction —
the drafted "consumed by" was false): `supersession_poset` (`core/temporal/acquire.py:31`)
reads `VersionStore` chains only; the store-free poset core `poset_from_chains`
(`core/temporal/boundary.py:99-112`) accepts per-path blob chains as-is when a consumer
arrives — a reader wiring, no new machinery. **Ruling: the embed lane keys on `blob_sha`, and
the D-chain stays where it lives.** The concrete payoff for ingest: `index_amendment`'s reuse-unchanged
discipline (`core/ingest/index.py:61-82`) means a file whose blob is unchanged across a commit
re-embeds **nothing**, and the D-edge (old blob → new blob) is exactly the signal that its
chunks must be re-derived. Incremental sync (§2.7) is therefore *driven by* the D-fiber: walk
the commits new since last sync, re-embed only the paths whose `blob_sha` changed. `[DERIVED —
the ledger carries blob lineage; the amendment path consumes it]`

**Interpreter/embedder version is a SECOND D-axis, orthogonal to content.** Re-embedding the
same blob under a new embedder version is the interpreter-version supersession the code sensor
already runs for observations (`ops/code_sensor.py:68-86` `INTERPRETER_VERSION`;
`dn-self-sensing` §2.4 versioned re-interpretation). A7 pins the embedder version
corpus-wide, not per-row (audit correction — the drafted "rows carry an `embedder` stamp"
was false: the schema has no such column, `core/stores/vectorstore.py:27-37`): the pin is
config-level (`config/defaults.toml:96-101`, model+dim) with fixed-version cuts and
reset+re-embed-from-raw on change; if a per-row `embedder` stamp is wanted it rides the same
`layer`-column migration (§5-4). A bump re-derives from git (§2.7-3). Two D-axes — *content changed*
(new blob) and *worldview changed* (new embedder) — never conflated, exactly as the
observation store separates them. `[DERIVED]`

**C over code — dialogue→code is LIVE; the embed lane consumes it, adds nothing to it.** The
integrator already mints witnessed C-edges dialogue-action → (commit, file, doc) — 4,084 at
the AL-3 seal, 4,160 at audit
(`core/integrator.py`; `dn-agent-taxonomy` §2.5). A code chunk's `(digest=blob_sha, commit,
path)` coordinates join to the C-edge whose witnessed commit touched that path — the typed
answer to "which conversation wrote this code," and the mechanism behind §2.3-1's
agent-vs-owner authorship attribution. **Grounding correction (not silent):** the built
`origin(e)` view is scoped to **reference-edge (X_cite) ids** — the durable kind carrying a
resolvable `commit_sha` (`core/origin_view.py:34-39,81-88`, the recorded target-kind
boundary). Code chunks are *nodes*, not reference edges, so authorship attribution for a code
chunk is the **sibling join** `C ∘ commit-keying at the node's commit` (hop 2 of `origin`
alone: the causal edge whose `pair_cut_sha`/witnessed commit produced the chunk's commit),
not `origin(e)` itself. This is the same C∘D family; it needs no new store (the C-edges and
commit keys exist), but it IS a small derived reader beyond what `origin_view.py` exposes
today — recorded as CI-2's optional rider (PD-J), not claimed as free. `[DERIVED — C-edges
live; the node-keyed reader is a named small addition, not an existing function]`

**The composition, one line:** S is *computed* over the code chunks (new, this note), F is the
*resolved* reference edges (§2.4, fixed here), C is *witnessed* dialogue→code (live), D is the
*blob + embedder* version chain (live) — code becomes a full S/F/C/D citizen with three of four
fibers already populated and only S newly minted. `[DERIVED]`

### 2.6 D4 — Reconciliation with `dn-code-observation-projection` — PARTIAL SUPERSESSION, announced

**⚑ CORRECTION BANNER.** The ratified two-plane model — *"code is a structural-only OBSERVED
plane, kept out of the semantic AUTHORED corpus"* — was **rejected by the owner as the
intended design** (finding-0146, owner ruling verbatim: "this is a bug, this is not a design
that I would ever think is ok"). This note is the correction. Nothing here edits the ratified
text (A8); the supersession front-matter lands at ratification, by the owner's hand, warrant =
finding-0146.

**Ruling: PARTIAL supersession — the *plane boundary* dies; the *projection machinery* is
absorbed verbatim.** Clause by clause:

| ratified clause | disposition |
|---|---|
| §1.2 "Ingesting code TEXT into the vector corpus" as a non-goal; PD-b "code-text embedding: never" | **SUPERSEDED** — the owner ruled the boundary itself a bug. (Honest note: PD-b's own re-entry — "a measured retrieval case" — was *not* the path taken; the owner overruled the default on inspection of the blindness, which is the stronger warrant. PD-b's *measurement discipline* survives as F-CI3: the lane must still prove retrieval value.) |
| §2.1 stream classification: repo = instrument, commits = readings, φ_code sole interpreter; never AUTHORED/CURATED/INTERPRETED | **ABSORBED** — §2.3 here re-derives the same exclusions; the a₂ cross-map is preserved. The "no new provenance class" sub-clause is superseded by `CODE` (the 2026-07-11 ruling predates the exhaust/authorship machinery that now needs the discrimination). |
| §2.2 φ_code interpreter contract (deterministic, sole path, versioned supersession) | **ABSORBED, extended** — the embed lane's structural extraction (spans, comments) rides φ_code; the *embedding* is a fixed versioned transform beside it (§2.7). |
| §2.3 observation schema / §2.4 seam / B-a..B-c | **UNTOUCHED** — built and live (`core/stores/code_observations.py`, `core/stores/reference_edges.py`); this note adds a lane beside them, changes none. |
| §2.5 two lanes | **EXTENDED to three**: Lane 0 (new) = the semantic embedding lane; Lane 1 = deterministic reference edges (kept, resolver fixed); Lane 2 = correlator-class proposals (kept, still unbuilt). The lanes still never merge. |
| §2.6 firewall obligations | **PRESERVED and sharpened**: mirror-opacity now covers the vector rows too (CODE ∉ MIRROR_READABLE), enforced at the same structural surfaces. |
| §3.2 V4 / observation-grain PD-a | **VINDICATED** — symbol grain, measured then, is the grain §2.1 embeds at. |
| §1.2's remaining non-goals: the no-promotion path ("observations never become authored — the path does not exist"), the parked smear, the correlator boundary | **UNTOUCHED** (audit addition — the drafted table left these undisposed) — CODE ∉ MIRROR_READABLE keeps the no-promotion line intact for the new rows (promotion up stays a deliberate human re-tag-from-raw, `core/provenance.py:74-77`, unused here); the smear stays parked (§1.2 here); Lane 2 stays Track D's charter. |

**Why partial and not full:** the projection note's machinery is ratified, built, tested, and
*correct*; only its sufficiency claim (structure-only, semantics never) was wrong. Superseding
the whole note would orphan the live stores' design record. The precedent is the
authorship-axis note's partial-amendment shape (§8 there): supersede the boundary paragraph,
banner it, preserve the rest as authoritative.

**Sibling reconciliations (extensions, none silent):**
- `dn-fiber-geometry` (ratified) — **EXTEND**: code nodes enter S; the M-battery gains the
  code rows (§2.8); the S↔F mismatch instrument gains the code↔design pair. Alphabet unchanged.
- `dn-agent-taxonomy` (ratified) — **EXTEND**: the embed lane is a sensor-role layer family
  over the repo source (§2.4 there); the fiber-vs-edge criterion *ruled L2a* (§2.4 here);
  "code is observed strata" stands.
- `dn-agentic-loop` (ratified) — **EXTEND**: the origin family (C∘commit-keying) gains its
  first code-side consumer — through the PD-J node-keyed sibling reader beside
  `origin_view.py`, not `origin(e)` itself (§2.5b's grounding correction); agent-vs-owner
  code attribution, §2.3-1. No exhaust semantics change.
- `dn-authorship-distance-axis` (draft) — **EXTEND**: code = a₂ base rows with transform
  attribution (embedder version = the calibration sheet's transform half, §3.7d there);
  `w(a_self)` for agent-authored code rides its existing PD-1 gate unchanged.
- `dn-self-sensing` (ratified) — **HONORED**: the lane's domain is primal (git blobs), not any
  sensor's output; the regress line (§2.6 there) is untouched. Embedding-version bumps follow
  the interpreter-version supersession discipline (§2.4 there; the `INTERPRETER_VERSION`
  precedent, `ops/code_sensor.py:68-86`).
- `dn-inner-outer-core` (ratified) — **HONORED**: the lane lands in `core/ingest/` (outer
  ring — it imports the embedder/LanceDB like every ingest module); zero inner-ring impact.
- `dn-chat-sensor` (ratified) — **EXTEND**: CS-3's duplication-apophenia reasoning is the
  warrant for the §2.1 partition rule.

### 2.7 D5 — ingest weight and sequencing vs the memory ceiling

**Sizing (measured this session; re-verified at audit against the ledger at `625a058`):**
528 tracked `.py` files / 5,065 symbols at the latest snapshot; 76,508 total `.py` LOC
(drafted 76,507 was off by one); 3,318 inline comments in the 247 main-package files
(§2.2's set — both counts reproduced exactly at audit). Estimated chunk volume: ~5.6k L0 chunks (symbols + module preambles; oversized splits
roughly offset by empty shells) + ~1–2k L1 chunks after `derive_chunks` packing ≈ **~7k
chunks, ~250× today's 28** — still small absolutely: at the configured dim, tens of MB in
LanceDB; single-user scale readers (`all_rows` Python-side filters,
`core/stores/vectorstore.py:128-140`) remain viable, re-checked by M-C5. `[DERIVED — counts
this session; the chunk estimate is ±2×]`

**Rulings:**
1. **HEAD-only, incremental — no historical embedding backfill.** The semantic space is a
   *current-view* instrument; history is already carried by D (snapshots ledger, 902 commits
   at `625a058`; the drafted 899 was finding-0145's stale `20253d5` reading) and by
   re-projection. Embedding every historical blob would multiply cost for no named
   consumer (PD-B parks it with one). Incremental sync rides the existing post-commit cadence:
   changed blobs only, keyed by blob sha — `digest`-keyed delete + re-add is exactly the
   watcher's amendment idiom (`vectorstore.delete(digest=…)` `:78-86`; `index_amendment`'s
   reuse-unchanged-chunks discipline, `core/ingest/index.py:61-82`). An unchanged file costs
   zero embeds, ever.
2. **The one-time seed run is scheduler-gated (non-negotiable #8).** ~7k embed calls through
   `qwen3-embedding:4b` at idle/housekeeping rate, batched (the `embed_documents` list call);
   the scheduler's refuse-breaching-work rule governs co-residency — the seed never runs
   beside a slot-2 heavyweight (the deploy-vs-ingest race is the recorded warning). One
   measured file's timing lands in the build journal before the full run (measure-first;
   M-C1). No daemon restart required — the lane is an ingest entry point, not a resident.
3. **Re-index posture:** embedder-version bump or chunker change ⇒ `reset` + full re-derive
   from git (vectors are derived, §8; the blob cache makes a full pass one parse per unique
   blob). The A7 embedder-version pin extends to code rows unchanged.

### 2.8 The measure-first battery (gates before and after CI-1)

| id | measurement | gates |
|---|---|---|
| M-C1 | one-file end-to-end timing (parse→strip→chunk→embed→land) + projected seed cost | the seed run's scheduling (§2.7-2) |
| M-C2 | chunk census after CI-1: per-layer counts, size distribution, the L0a cover check (module shell + symbol slices reassemble every file byte-identically) | F-CI2 |
| M-C3 | retrieval probe: a small golden set of "find the code that does X" queries, code-lane vs docstring-only baseline | F-CI3; PD-b's measurement debt, paid |
| M-C4 | cross-space geometry: code↔doc cosine distribution vs within-class; are cross neighborhoods informative or bimodally degenerate? | PD-C (embedder re-entry); the §2.4 bridge's viability |
| M-C5 | reader-scale check: `all_rows`/search latency at ~7k rows | the Python-side-filter posture |
| M-C6 | resolver precision: hand-checked sample per new pattern (`dn-slug`, `finding-id`, paired-`§`) | F-CI6; each pattern mints only above the bp-011 bar |
| M-C7 | S↔F first read: undocumented-realization and drift counts on the real corpus | CI-4's licensing; a null is a finding, not a failure |
| M-C8 | L0a↔L0b structural↔textual mismatch: distribution of symbol-vector vs covering-window-centroid cosine | the two-reading cross-check's value (§2.1); a null demotes L0b's separateness to vocabulary (fold ⇒ PD-K) |

## 3. Consequences — the build sequence (session-sized; blast-radius ordered)

- **CI-1 — the embed lane (L0a + L0b + L1 + provenance), graduates first.**
  `core/ingest/code_corpus.py` (outer ring): span+comment capture extensions to φ_code's walk
  (additive ledger migration); the L0a structural chunker (slice + name header) and the L0b
  windowed chunker (`derive_chunks` on raw source) and the L1 prose chunker (strip → note
  path); the three `layer`-tagged row sets into the existing vector store with hardcoded
  `Provenance.CODE`; the L0a↔L0b↔L1 line-range join carried as row coordinates; incremental
  sync driven by blob-sha D-edges; the seed run scheduler-gated. Includes M-C1/M-C2/M-C8 and
  the F-CI1/F-CI2/F-CI5 tests. *L2a rides free* (the backpointer coordinates are the row
  schema). Depends on nothing unbuilt.
- **CI-2 — the isolation + retrieval proof (+ the node-keyed C reader rider).** M-C3/M-C4/M-C5;
  the golden probe set; the mirror-isolation ratchet (F-CI5) in the
  `test_reference_edge_isolation` pattern; optionally the node-keyed authorship join (PD-J) as
  a small derived reader beside `origin_view.py`. (May merge into CI-1 if it fits one session —
  split at graduation, not mid-build.)
- **CI-3 — the reference layer (L2b + the AST edges).** The three shorthand patterns
  (`dn-slug`/`finding-id`/paired-`§`) + the `code_to_code` `inherits`/`calls` patterns, each
  with a precision sample (M-C6); new `REF_TYPES` entries. Pairs with, but does not depend on,
  finding-0145's current-view projection (PD-5's track). Independent of CI-1 — parallel in a
  disjoint write scope.
- **CI-4 — the S↔F code↔design lens (conditional on CI-1 + CI-3 landing and M-C4 showing
  signal).** The mismatch reading (M-C7) as a census-adjacent survey — read-only, eval-side.
- **Explicitly NOT licensed:** any correlator/Lane-2 build; any dreamer default-grant change
  (CODE stays opt-in per grant — owner's call per grant, §5); any historical embedding
  backfill; any second embedder; any non-Python surface.

## Falsifiers (the load-bearing set)

- **F-CI1** (§2.3) — a CODE row reachable through a MirrorView / MIRROR_READABLE-default
  search, or a code-lane API with a provenance parameter ⇒ firewall incident; halt the lane.
- **F-CI2** (§2.1/§2.2) — the **L0a** slices fail byte-cover on any file (a source line in
  zero or ≥2 L0a chunks — the audit killed the drafted "L0⊔L1 partition" phrasing, a residue
  of the superseded single-partition draft: L0b overlaps by design and L1 re-projects content
  L0a carries, so L0a alone is the partition), or any layer's chunks are not re-derivable
  bit-identically from the blob (the `core.ingest.verify` re-derivation discipline) ⇒ the
  derivation is not regenerable; the lane is malformed.
- **F-CI3** (§2.7/M-C3) — the code lane fails to beat the docstring-only retrieval baseline on
  the golden probes ⇒ the embedding earns no keep; record as no-signal, re-open grain (PD-D)
  before scale-up. (PD-b's measurement obligation, inherited and inverted.)
- **F-CI4** (§2.1b/M-C4) — code↔doc neighborhoods degenerate (near-total class separation) ⇒
  the shared-space ground of D2 fails; PD-C re-enters.
- **F-CI5** (§2.3/§2.5) — any mirror-path instrument result (σ-graph over MIRROR_READABLE,
  balance math) changes when code rows are added/removed ⇒ isolation breached (the B-c
  falsifier pattern, applied to the vector plane).
- **F-CI6** (§2.4) — any new resolver pattern (`dn-slug`/`finding-id`/paired-`§`) or AST edge
  pattern (`inherits`/`calls`) below the bp-011 precision bar on the M-C6 hand-check ⇒ that
  pattern is dropped, not shipped-and-tuned.
- **F-CI7** (§2.1/M-C8) — if the L0a↔L0b mismatch distribution is degenerate (symbol vectors
  and their covering-window centroids near-identical everywhere) ⇒ the two readings are
  redundant, not complementary; fold L0b into L0a (PD-K) rather than paying for both.

## Parked decisions

| id | decision | default recorded | re-entry condition |
|---|---|---|---|
| PD-A | test-file inclusion in the embed lane | include (φ_code parity: the sensor snapshots all tracked `.py`; tests carry spec knowledge) | M-C3 shows test chunks dominate/degrade retrieval — then a `layer`-side exclusion, not a walk change |
| PD-B | historical embedding backfill (all commits' blobs) | never — HEAD-only incremental | a temporal-semantic consumer is exhibited (e.g. "semantic diff across versions") that D + re-projection cannot serve |
| PD-C | code-tuned embedder | `qwen3-embedding:4b`, one space | F-CI4 fires, or M-C3/M-C4 show material deficit vs an offline code-model baseline; lands as an embedder-version bump |
| PD-D | sub-symbol grain (statement/block-level chunks) | symbol partition | F-CI3 fires AND error analysis attributes it to oversized atoms |
| PD-E | stored file centroids | computed on read (`note_centroids` pattern) | profiling shows centroid computation hot on a consumer path (the axis note's PD-2 shape) |
| PD-F | unpaired `§N` resolution (e.g. via `design_ref` front-matter of the nearest cited note) | dropped | a measured recall case + a precision sample clearing the bar |
| PD-G | non-Python surfaces (`.toml`, `.sh`, templates) | out | a retrieval miss traced to them; each surface needs its own deterministic chunk rule |
| PD-H | dreamer default-grant inclusion of CODE | opt-in per grant (CURATED precedent) | owner deliberation at grant-writing time — never flipped by a build |
| PD-I | the fuller call graph (dynamic dispatch, cross-module attribute chains) | statically-resolvable `inherits`/`calls` only (precision-first) | a consumer needs call-graph reach AND a resolution method clears the bp-011 bar |
| PD-J | the node-keyed C authorship reader (code chunk → producing dialogue) | derivable, uninhabited beyond `origin_view.py`'s edge-scoped view | CI-2 rider, or the first consumer needing per-chunk authorship attribution |
| PD-K | fold L0b into L0a (drop the separate windowed reading) | keep both (two independent readings) | F-CI7 fires — M-C8 shows the readings are redundant, not complementary |

## 5. Open questions (owner)

1. **Dream-grant posture:** should the *standing* dream configuration gain a CODE-inclusive
   grant at CI-1 landing, or only ad-hoc grants? (Default recorded: opt-in per grant, PD-H —
   but the owner's "dream over its own implementation" framing may want a standing grant.)
2. **The α position of agent-authored code** rides the axis note's PD-1 gate (with the
   `w(a_self)` entry); confirm at that gate that code rows' a₂ cross-map + origin-based
   authorship attribution (§2.3-1) is the intended composition.
3. **Partial vs full supersession** of `dn-code-observation-projection` (§2.6 argues partial);
   the owner places the banner either way at ratification.
4. **Vector-store schema evolution** (the `layer` column): delivered by reset+rebuild (derived
   layer, cheap at 28 rows today) — acceptable, or is an in-place additive path preferred?

## Cross-references

**Code (verified on disk this session, worktree @ `441fcc3`):**
`core/ingest/pipeline.py:22-34,49-76` (derive_chunks; provenance-parametric ingest; the
`**/*.md` glob) · `core/ingest/chunk.py:16-56` (Chunk, content_hash, chunk_text) ·
`core/ingest/index.py:27-58,61-82,115-138` (row assembly; amendment reuse; MIRROR_READABLE
default; grouped search) · `core/ingest/embed.py:26-41` (Qwen3 adapter) ·
`core/ingest/curated.py:1-14` (the CURATED own-graph precedent) ·
`core/stores/vectorstore.py:27-37,54-65,72-86,128-153` (schema; dim check; reset/delete;
provenance filters) · `core/provenance.py:44-80` (the enum; MIRROR_READABLE) ·
`core/stores/code_observations.py:59-91,103-150` (schema; structural OBSERVED mint) ·
`core/stores/reference_edges.py:96-114` (REF_TYPES/KINDS; `code_to_code` reachable-not-minted) ·
`ops/code_sensor.py:1-43,68-86,104-113,236-253,299-333,406-425` (the model-less sensor;
INTERPRETER_VERSION; the regexes; extract_references; sync; corpus scan) ·
`ops/code_snapshot.py:33-76,126-161,193-224,296-318` (ledger DDL incl. `imports`; the AST walk;
snapshot; additive migrations) · `core/scope.py:60-107` (Stratum; EXHAUST as excluded
refinement) · `core/complex/build.py:121-124` (note centroids computed on read) ·
`core/ingest/amend.py:43-74` (chunk_point_id; plan_amendment) · `core/origin_view.py:1-100`
(the C∘commit-keying view; the reference-edge target-kind boundary) · `core/integrator.py`
(the live C-edge minter) · `core/temporal/boundary.py:17,99-112` + `core/temporal/acquire.py:31`
(the store-free poset core the D-chain CAN feed — not yet wired, §2.5b) ·
`config/defaults.toml:96-132` (embedding model; the model slots).

**Live-store readings (2026-07-21; ✓ = re-verified independently at the fable audit, at
`625a058`):** vectors.lance 28 chunks / 19 notes ✓ (finding-0146; all rows `authored-solo` ✓);
code_snapshots latest commit 528 files ✓ / 5,065 symbols ✓ / 76,508 LOC ✓ / 902 commits ✓;
3,318 `#` comment tokens across 247 main-package `.py` files ✓ (tokenize; reproduced exactly);
causal_edges 4,160 at audit (4,084 at the AL-3 seal); reference_edges 950,025 accumulated at
audit / current view 2,199 / 624 doc→doc (finding-0145).

**Design:** finding-0146 (warrant) · finding-0145 · dn-code-observation-projection (§2.6
disposition table) · dn-fiber-geometry §2.0/§2.2 · dn-agent-taxonomy §2.3/§2.4/§2.5 ·
dn-agentic-loop §2.4/§2.4b · dn-authorship-distance-axis §1/§3.2/§3.7 · dn-self-sensing
§2.4/§2.6 · dn-chat-sensor §2.3 · dn-inner-outer-core (ring placement) · the sourceset
relation (2026-07-03, `core/stores/sourceset.py`).

**External claims `[FROM MEMORY]` for the grounding gate:** Qwen3-Embedding's code-retrieval
competence (model card); nothing else external is load-bearing.
