---
type: build-plan
id: bp-036
status: proposed
design_ref:
  - docs/findings/finding-0077.md   # the id:: mint measurably changed the mirror graph (5→9); parked-4 re-entry
contract: builder
write_scope:
  - core/ingest/logseq.py            # a deterministic strip_properties() helper co-located with _PROP
  - core/ingest/pipeline.py          # apply the strip in the ONE raw→chunks derivation (derive_chunks + ingest_note)
  - tests/unit/test_property_strip.py
  - tests/integration/test_body_only_embedding.py
  - scripts/reembed_bodyonly.py      # owner-run, gated re-embed (mirrors scripts/mint_ids.py posture)
session_budget: 1
cost:
  estimate:
    model: opus
    tokens: 250k
  actual: null
depends_on:
  - bp-034                            # the mint that introduced the id:: line into the embedded text
parallelizable_with: []
created: 2026-07-14
updated: 2026-07-14
links:
  - docs/findings/finding-0077.md
  - core/ingest/verify.py             # the retrieval-integrity constraint the strip must stay consistent with
  - core/ingest/index.py              # the vector projection / semantic search
re_entry: null
supersedes: null
superseded_by: null
warrant: docs/findings/finding-0077.md
---

# Build Plan — body-only embeddings: exclude `key::` page-properties from the embedded derivation

> **Every section below is required.** Inapplicable sections are marked `N/A — <reason>`.

## 0. Mode & provenance

Follow-on to **finding-0077** (measured, owner-directed 2026-07-14): the bp-034 `id::` mint fed identity
metadata into the semantic embedding, moving the σ=0.62 mirror graph **5 → 9 edges** (the shared `"id:: "`
prefix lifts cosine; the random uuid adds content-free noise). Owner rules (this session): **Path A**
(Logseq-native — the `id::` stays in the file; only the *embedded text* changes; no vault re-migration),
scope = **exclude ALL `key::` property lines** (extensible for future metadata), and the strip must be
**deterministic and exact**. This plan BUILDS + TESTS the change offline; the **live re-embed is a
separate, owner-gated, daemon-down step** (deploy-coupled, finding-0066), never run in the build session.

## 1. Objective

Exclude every Logseq `key::` page-property line from the text that is chunked and embedded, so the vector
layer reflects note **body/prose only** — deterministically, and consistently between ingest and the
retrieval-integrity check — while leaving the authored file, raw store, digests, `doc_id` identity, and
all reference paths byte-for-byte unchanged. Then re-embed from raw (§8, regenerable) so the live mirror
graph reverts to content-only.

## 2. Context manifest

Read whole, in order:

1. `docs/findings/finding-0077.md` — the measured regression + parked-decision-4 re-entry.
2. `core/ingest/logseq.py` — `_PROP` (`:19`, the property definition); `parse_text` (`:56`, where
   `.properties` is extracted and `.text` is the full decoded text). The strip must reuse `_PROP` so
   parse ≡ strip.
3. `core/ingest/pipeline.py` — `derive_chunks` (`:22`, the ONE authoritative raw→chunks derivation) and
   `ingest_note` (`:45`, `chunks = chunk_text(note.text)`). BOTH must apply the strip identically.
4. `core/ingest/verify.py` — the retrieval content-integrity check: a stored chunk is trusted iff its
   `text` re-derives from raw via `derive_chunks`. **This is the load-bearing constraint**: if the strip
   is applied at store time but not in `derive_chunks`, every body chunk fails integrity and is dropped.
5. `core/stores/rawstore.py` (`:31`) — `digest = sha256(raw_bytes)`. Confirms re-embedding changes NO
   digest (the file bytes keep the properties), so versions/catalog/dreams' digest refs are untouched.
6. `core/ingest/sync.py` (`:107`) — `doc_id` resolves via `parsed.properties.get("id")`, parsed from the
   full text BEFORE chunking. Confirms identity/rename-stability are independent of the embedded text.
7. `core/ingest/index.py` — `index_amendment`/`_chunk_row` (the vector projection); `semantic_search`
   (search is over content vectors + the query — no id-keyed search exists).

## 3. Investigation & grounding

- **Q1 — Where exactly is the metadata entering the embedding?** `ingest_note:52` chunks `note.text` =
  `_decode(raw_bytes)` = the FULL file text, including every `key::` line. The strip belongs in the
  raw→chunks derivation, applied to the decoded text before `chunk_text`. *The code settles this.*
- **Q2 — The exact, deterministic definition of "a property line."** `_PROP = ^([A-Za-z0-9_-]+)::\s?(.*)$`
  (MULTILINE), column-0 only. Verified boundaries: `http://…`, `time is 3::00`, and indented lines do NOT
  match; `id:: x`, `a-b_c:: ok` do. The strip removes exactly the lines `_PROP` matches — SAME pattern as
  parsing — so parse and strip can never disagree (the exactness guarantee). **Open sub-decision (§10):**
  `_PROP` does not match indented *block-level* properties; "all `key::` properties" therefore means all
  *column-0* property lines unless the vault uses block properties AND the owner wants them excluded (which
  widens `_PROP` for parse+strip together). Item 13 inspects the real 13 notes first.
- **Q3 — Does the strip change identity / references / digests?** No. `doc_id` reads `.properties` (parsed
  before chunking, `sync.py:107`); digests are `sha256(raw_bytes)` (`rawstore.py:31`), unchanged by
  re-embedding; `[[links]]` (`_LINK`) and titles (path) don't touch property lines. *The code settles this.*
- **Q4 — Does "strip ALL props" reproduce the pre-mint graph?** Not necessarily — it reverts to *body-only*.
  Equals pre-mint 5 edges IFF the notes carried no properties before the mint. Item 14's A/B **measures**
  it; the plan asserts "the id:: artifact is removed," not a hardcoded 5.

## 4. Reconciliation

- `core/ingest/pipeline.py` `derive_chunks` docstring — *"the ONE authoritative raw→chunks derivation …
  `ingest_note` performs exactly this."* → **[extension]** both now route through a shared
  `strip_properties` step so the invariant (ingest derivation == verify derivation) is *preserved*, not
  broken. The docstring is updated to record that page-property lines are excluded from the derived text.
- No design note is edited; finding-0077 is the warrant.

## 5. Write scope

`core/ingest/logseq.py` (a `strip_properties(text) -> str` helper beside `_PROP`), `core/ingest/pipeline.py`
(call it inside the shared derivation so `derive_chunks` AND `ingest_note` strip identically),
`tests/unit/test_property_strip.py` (the exactness/determinism suite), `tests/integration/
test_body_only_embedding.py` (the A/B + identity/integrity end-to-end), `scripts/reembed_bodyonly.py`
(the owner-run, `confirm`-gated, daemon-down re-embed). **Deliberately OUT of scope:** the vault/authored
files (never written — Path A), the raw store (sacred), the version/catalog stores (digests unchanged),
`_PROP`'s column-0 semantics UNLESS Item 13 finds block properties in play and the owner widens it, and
the live vector store at build time (the re-embed is owner-run).

## 6. Interfaces pinned inline

```python
# core/ingest/logseq.py — NEW, reusing the SAME property definition as parsing:
_PROP = re.compile(r"^([A-Za-z0-9_-]+)::\s?(.*)$", re.MULTILINE)   # unchanged (column-0)
def strip_properties(text: str) -> str: ...
    # remove every line _PROP matches; keep body lines verbatim; deterministic + idempotent.
    # parse≡strip: a line is a property IFF _PROP matches it (the single source of truth).

# core/ingest/pipeline.py — apply in the ONE derivation (both callers stay identical):
def derive_chunks(raw_bytes, *, max_chars=1200, overlap_chars=150) -> tuple[Chunk, ...]:
    return tuple(chunk_text(strip_properties(_decode(raw_bytes)), ...))   # <- the change
def ingest_note(note, raw, ...):
    chunks = tuple(chunk_text(strip_properties(note.text), ...))          # <- identical strip

# core/ingest/verify.py — UNCHANGED, but now consistent: it re-derives via derive_chunks, which
# strips, so a legitimately re-embedded body chunk verifies (no false drop).
```

## 7. Items

### Item 13 — the deterministic, exact property strip (+ inspect the real note structure)
- **Objective:** `strip_properties(text)` removing exactly the lines `_PROP` matches, body verbatim;
  idempotent; parse≡strip. First, inspect the 13 live notes (read-only) to report whether any use
  indented block properties (the §10 sub-decision).
- **Files:** `core/ingest/logseq.py`, `tests/unit/test_property_strip.py`.
- **Acceptance test (EXTENSIVE — the owner's "test before touching stores"):** property lines removed;
  body (incl. `http://`, `time 3::00`, `[[links]]`, code, unicode, indentation) preserved byte-for-byte;
  idempotent (`strip(strip(x))==strip(x)`); **parse≡strip** (the set of removed lines == the lines
  contributing to `parse_text(...).properties`); an all-property note → empty body; a no-property note →
  unchanged.
- **Falsifier:** a body line is dropped, OR a property line survives, OR `strip` and `_PROP.findall`
  disagree on any input.
- **Invariant(s):** deterministic; exact; parse and strip share one definition.
- **Touches stored data?** No.  **Depends on:** —

### Item 14 — apply in the shared derivation + integrity/identity consistency + the A/B (offline)
- **Objective:** route `derive_chunks` and `ingest_note` through `strip_properties`; prove the
  retrieval-integrity check still passes, identity/digests are unchanged, and MEASURE the mirror-graph
  effect on a copy (the pre-vs-post A/B).
- **Files:** `core/ingest/pipeline.py`, `tests/integration/test_body_only_embedding.py`.
- **Acceptance test:** (a) a re-embedded (body-only) chunk row **passes `verify.py`** (re-derives via
  `derive_chunks`) — no false drop; (b) `doc_id`/`id::` resolution and every note digest are **identical**
  before/after the strip (identity + rename-stability preserved); (c) **the A/B on a copy** — embed the
  corpus current-way vs body-only through the real embedder and report σ=0.62 edges: assert the id::
  artifact is removed (edges drop from the polluted count toward content-only; the exact number reported,
  compared against the pre-mint backup graph); (d) `[[links]]`/titles unchanged.
- **Falsifier:** any body chunk dropped by `verify.py`; OR a digest/`doc_id` changes; OR the strip fails
  to reduce the artificial edges.
- **Invariant(s):** ingest derivation == verify derivation; identity/digest invariance; measured (not
  assumed) graph effect.
- **Touches stored data?** No (fresh/copy stores only).  **Depends on:** Item 13.

### Item 15 — the owner-run, gated re-embed (build the tool; do NOT run it)
- **Objective:** `scripts/reembed_bodyonly.py` (mirror `scripts/purge_raw.py`/`scripts/mint_ids.py`):
  `seal()` → daemon-down gate → `confirm`-gated → back up the vector store → reset + rescan from raw with
  the fixed pipeline → verify body-only + report the new live mirror-graph edge count.
- **Files:** `scripts/reembed_bodyonly.py`.
- **Acceptance test:** on a fixture corpus (offline), the script re-embeds body-only, refuses without
  `--confirm` or with the daemon up, is idempotent, and reversible from the vector-store backup; the raw
  store, versions, catalog, and vault files are untouched.
- **Falsifier:** it writes the vault/raw/versions/catalog; OR runs with the daemon up; OR is not
  reversible.
- **Invariant(s):** offline-only; regenerable-from-raw; nothing but the derived vectors changes.
- **Touches stored data?** The tool CAN (the live vectors) — but only when the OWNER runs it, after
  the build + tests + A/B are green and approved.  **Depends on:** Items 13, 14.

## 8. Math carried explicitly

**N/A — no mathematical object implemented.** A derivation-hygiene change (metadata excluded from the
embedded text). It restores the σ-graph to content-only but implements none of the graph/complex math.

## 9. Non-goals

- **No vault/authored-file write** (Path A — the `id::` stays in the file; only the *embedded* text changes).
- **No change to identity/`doc_id` resolution, digests, `[[links]]`, or titles** — all read from paths I do
  not touch.
- **No widening of `_PROP` to block-level properties** unless Item 13 finds them in play and the owner rules.
- **No running the live re-embed in a build session** — Item 15 delivers a tested tool; the OWNER runs it.
- **No re-key, no purge, no supersession changes.**

## 10. Stop-and-raise conditions

- **The 13 notes use indented block properties** and the owner wants them excluded → widening `_PROP`
  affects property parsing everywhere; **STOP and raise** (owner rules) rather than silently change parse
  semantics.
- **The strip and `_PROP.findall` disagree** on any real note → the exactness contract is broken; STOP.
- **A body chunk fails `verify.py`** after the strip → the derive-consistency invariant is broken; STOP.
- **The A/B does not reduce the artificial edges** → the premise is wrong; STOP and re-investigate before
  any live re-embed.
- Any digest or `doc_id` change → must not (identity is sacred here).

## 11. Parked decisions

| Decision | Default recorded | Rejected alternatives (why) | Re-entry condition |
|---|---|---|---|
| Frontmatter mechanism | **Path A** — Logseq-native property exclusion (no vault re-migration; id:: stays) | Path B YAML `---` frontmatter (rejected: a second corpus write + YAML-aware resolution, fights Logseq) | owner adopts an Obsidian-style convention |
| Strip scope | **All `key::` property lines** (extensible for future metadata) | id:: only (rejected: owner wants a general metadata/body split, not a one-property patch) | — |
| Block-level (indented) properties | **Column-0 only** (== `_PROP`) pending Item 13's inspection | widen `_PROP` to indented (deferred: changes parse semantics everywhere) | Item 13 finds block properties AND owner wants them excluded |

## 12. Dependency & ordering summary

Order: **Item 13** (the pure, exhaustively-tested strip) → **Item 14** (wire into the shared derivation +
integrity/identity proof + the offline A/B) → **Item 15** (the owner-run gated re-embed tool). All offline;
**no live store is touched in the build** (owner rule 2026-07-14: extensive tests + the A/B first). The
live re-embed is **deploy-coupled** (daemon down; finding-0066), owner-fired, never in-session. Model:
**opus/high** — it changes what the semantic layer ingests and rides the retrieval-integrity invariant.
`depends_on: bp-034`. _(Numbering: bp-035 stays reserved for the diagnostic subcommand per bp-034 §12.)_
