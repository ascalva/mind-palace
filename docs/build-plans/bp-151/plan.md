---
type: build-plan
id: bp-151
track: code-ingest
status: proposed
design_ref:
  - docs/design-notes/vector-membership-store.md
contract: builder
write_scope:
  - core/ingest/code_corpus.py
  - tests/unit/test_code_corpus.py
  - tests/unit/test_code_retrieval.py
  - tests/integration/test_code_mirror.py
  - tests/integration/test_code_vector_isolation.py
session_budget: 1
cost:
  estimate:
    model: opus
    tokens: 250k
  actual: null
depends_on: []
parallelizable_with: []
created: 2026-08-01
updated: 2026-08-01
links:
  - docs/findings/finding-0168.md
  - docs/findings/finding-0167.md
  - docs/brainstorms/strip-headers-from-the-atom-hash.md
re_entry: null
supersedes: null
superseded_by: null
warrant: null
---

# Build Plan — canonical atom identity: the header-free body (D0)

## 0. Mode & provenance

Graduated from `dn-vector-membership-store` D0 on 2026-08-01, under the owner's
"graduate now, merge = blessing" ruling (the note's blessing signal is the merge of the
graduation PR; issue #27). Investigation and planning produced this plan; implementation
proceeds item-by-item. Every `path:line` in §3 was re-opened against HEAD `174d06c` — the
note's citations were written 2026-07-27 and `git log --since` confirms **zero drift** in
every file cited here.

This is the first of three plans (bp-151 → bp-152 → bp-153). The note sketched *two*
("store+land+read; rebuild+gauges+probe+compaction") and delegated the final split to
graduation ("split at /graduate against the then-current tree", §8). Against the current
tree D0 separates cleanly and is pulled out as its own plan — see §12 for the reasoning.

## 1. Objective

Make a code chunk's `content_hash` identify its **header-free canonical body**, so that a
rename or a line shift mints zero new atoms.

## 2. Context manifest

Read in order, whole files before citing:

1. `docs/design-notes/vector-membership-store.md` — §0(5), D0, §8(h)(i), R7. D0 is this
   plan in full; the rest is why.
2. `docs/brainstorms/strip-headers-from-the-atom-hash.md` — the owner's identity ruling
   verbatim (2026-07-27), the warrant D0 rests on. Read the reasoning, not just the rule.
3. `core/ingest/code_corpus.py` — the whole file. The three chunkers and `content_hash`
   are the entire surface this plan moves.
4. `docs/findings/finding-0168.md` — addendum 4 (`:135-188`), rename-as-membership-edge;
   raised edit-stable chunk identity to load-bearing. D0 is its precondition.
5. `docs/findings/finding-0167.md` — `:37`, the owed L1 line-header check this plan
   discharges.
6. `tests/unit/test_code_corpus.py` — the determinism and layer assertions this plan must
   keep green while changing what they hash.

## 3. Investigation & grounding

- **Q1 — Does `content_hash` really include the coordinate header today?** Yes, and it is
  the whole defect. `content_hash` is `sha256(self.text)` over the chunk's *full* text —
  `core/ingest/code_corpus.py:80-81` — and L0a's text is `full = f"{header}\n{body}"`
  (`:118`) where `header = f"# {path}:{qualname}{signature}"` (`:109`). So the path is
  inside the hash for every L0a chunk.
- **Q2 — Is the L0a header a cleanly strippable first line?** Yes. It is joined with a
  single `\n` at `:118`, and the oversized branch already re-prefixes a header onto
  header-free body pieces (`:121-123`), proving the body is separable in the existing code.
- **Q3 — Is L0b headerless as the note claims?** Yes. `_l0b_chunks` emits
  `CodeChunk(LAYER_CODE_TEXT, "", ls, le, c.text)` straight from `chunk_text(source, ...)`
  — `:150-157`. No header is ever added. Canonical body = the text, unchanged.
- **Q4 — Are L1 headers interleaved *before* windowing (the reason strip-at-hash is not
  enough)?** Yes, confirmed exactly. `_l1_chunks` builds `items` as
  `f"# {path}\n{...}"` / `f"# {path}:{s.qualname}\n{...}"` / `f"# {path}:{c.lineno}\n{...}"`
  (`:166-172`), joins them into `prose` (`:176`), and only then windows:
  `chunk_text(prose, ...)` (`:177-178`). Window boundaries are therefore computed over
  header-bearing text, so a path-length change recuts windows. This is the mechanism
  behind the note's measured "strip-at-hash-only still mints 7 L1 atoms on a rename".
- **Q5 — Is L1 slotless as R4 claims (so no slot lineage is at risk here)?** Yes.
  `:177` emits `CodeChunk(LAYER_CODEDOC, "", 1, n_lines, c.text)` — `qualname=''`,
  identical to L0b. L0a is the only slotted layer. This plan does not change that.
- **Q6 — Who consumes `derive_code_chunks` / `code_rows` in production?** Only
  `core/ingest/code_corpus.py` itself — `:272` and `:277`. There is no external production
  caller, so the blast radius of a hash change is the store's contents, not other modules.
- **Q7 — Does anything outside this file depend on the *shape* of the id?**
  `code_rows` builds `rid = f"{path}:{ch.layer}:{ch.content_hash}"` (`:213`) and dedups
  `by_id.setdefault(rid, row)` (`:229`). This plan does **not** change the id shape — the
  path-free id `"{layer}:{content_hash}"` is D1's change and belongs to bp-152. Here the
  id keeps its current form and only the hash *inside* it becomes canonical. That
  containment is deliberate: it keeps bp-151 a pure chunker change.

**Additional risks or questions surfaced during reading:**

- **The stored corpus is invalidated by this plan, by design.** Changing `content_hash`
  means every existing code row's id no longer matches what the chunker now derives. This
  is expected — vectors are derived and regenerable — but it means bp-151 landing alone
  leaves the live store *stale*, not corrupt: existing rows keep working for retrieval,
  and the reconciliation is bp-153's rebuild. The builder must not attempt a migration
  here (§9).
- **The note's `[INFERENCE]` marker on the L1 windowing pin is real and stays.** §1.2
  records that the owner's ruling pins *identity* only, and the L1 windowing pin is the
  note's own derivation from the rename probe. This plan implements the derivation; if the
  measured numbers in §7 Item 3 do not reproduce, that is a spec question, not a bug to
  code around (§10).
- **`_locate_span` is best-effort and unchanged.** L0b line coordinates are located by
  matching text back into the source (`:129-147`). This plan does not touch it; L0b's
  canonical body is already the text.

## 4. Reconciliation

- `core/ingest/code_corpus.py:80-81` — `return sha256(self.text.encode("utf-8")).hexdigest()`
  → **[banner: correction]**. The docstring on `CodeChunk` (`:69-71`) must state that
  identity is the canonical body and that `text` (the embed rendering) may differ. Proposed:

  ```python
  @property
  def content_hash(self) -> str:
      """Identity = the CANONICAL (header-free) body, never the embed text (D0, owner-ruled
      2026-07-27). A filename is mutable: with the coordinate header inside the hash, a
      rename re-hashes every chunk and every (path, slot) occupancy chain through the file
      severs — on an operation this repo performs constantly. Embed text may keep headers;
      identity may not."""
      return sha256(self.canonical_body.encode("utf-8")).hexdigest()
  ```

- `core/ingest/code_corpus.py:162-178` — `_l1_chunks` windows header-bearing prose
  → **[banner: correction]**. Windows are recut over canonical prose; the header returns as
  a single strippable `# {path}` prefix. The correction is carried by §7 Item 2, called out
  in the docstring as a correction, not slipped in.

- `docs/findings/finding-0167.md:37` (the owed L1 line-header check) →
  **[cross-ref: extension]**. This plan discharges it. The finding is frozen history and is
  **not edited**; the discharge is recorded in the PR body and in this plan's §7 Item 3
  acceptance, per the merge-gated regime (findings are issues now; frozen files stay frozen).

- `core/ingest/code_corpus.py:203-210` — the `code_rows` docstring says the id is
  "`(source_path, layer, chunk_hash)` — doc+layer-scoped and content-addressed, so an
  unchanged chunk keeps its point across versions" → **[cross-ref: extension]**. Still true
  after this plan, and it becomes *more* true (a renamed file's chunks now keep their point
  too). Add one line noting the hash is canonical-body-scoped as of D0. The id shape itself
  changes in bp-152, not here.

## 5. Write scope

`core/ingest/code_corpus.py` is the only production file. Everything this plan changes —
`content_hash`, the L0a canonicalization, the L1 windowing — lives there (§3 Q6: no external
production caller exists).

Four test files are carried because they pin the surface this plan moves:

- `tests/unit/test_code_corpus.py` — imports `derive_code_chunks` (`:22`) and asserts
  bit-identical determinism (`:70`); it is where the new canonicalization tests land.
- `tests/unit/test_code_retrieval.py` — imports `code_rows, derive_code_chunks` (`:16`) and
  builds rows through them (`:68`, `:71`), so any hash change moves the ids it observes.
- `tests/integration/test_code_mirror.py` and
  `tests/integration/test_code_vector_isolation.py` — both assert over code-lane rows whose
  ids embed `content_hash`; carried so a red from the identity change can be repaired in
  the same session rather than stranding acceptance.

Deliberately **out of scope**: `core/stores/vectorstore.py` (D1 — bp-152), any new store
(`core/stores/memberships.py` — bp-152), `ops/code_lineage.py` and `ops/code_snapshot.py`
(untouched by D0), every design note, and the fixed points (`CONSTITUTION.md`,
`eval/golden/**`, `eval/golden.py` — the standing denylist, never written by an agent).

## 6. Interfaces pinned inline

The current form, copied from HEAD `174d06c` — the builder must not infer these.

`core/ingest/code_corpus.py:69-81` (the type being changed):

```python
class CodeChunk:
    """One embeddable code chunk with its fiber coordinates. `layer` discriminates the projection;
    `(qualname, line_start, line_end)` are the §2.4 backpointers carried on the row."""
    # ... fields: layer, qualname, line_start, line_end, text
    @property
    def content_hash(self) -> str:
        return sha256(self.text.encode("utf-8")).hexdigest()
```

`core/ingest/code_corpus.py:113-124` (L0a emission — note the existing header/body split):

```python
    out: list[CodeChunk] = []
    # emit in source order (by first owned line) so the layer is deterministic
    for key in sorted(owned, key=lambda k: owned[k][0]):
        header, ls, le = coords[key]
        body = "\n".join(lines[i - 1] for i in owned[key])
        full = f"{header}\n{body}"
        if len(full) <= max_chars:
            out.append(CodeChunk(LAYER_CODE_AST, key, ls, le, full))
        else:  # oversized slice: hard-split the body via the ONE window machinery, re-headered
            for piece in chunk_text(body, max_chars=max_chars, overlap_chars=overlap_chars):
                out.append(CodeChunk(LAYER_CODE_AST, key, ls, le, f"{header}\n{piece.text}"))
    return out
```

`core/ingest/code_corpus.py:162-178` (L1 emission — the windowing to be re-cut):

```python
def _l1_chunks(path: str, n_lines: int, shape: FileShape, *,
               max_chars: int, overlap_chars: int) -> list[CodeChunk]:
    items: list[tuple[int, str]] = []   # (source line, "header\nbody") in source order
    if shape.docstring:
        items.append((1, f"# {path}\n{shape.docstring}"))
    for s in shape.symbols:
        if s.docstring:
            items.append((s.lineno, f"# {path}:{s.qualname}\n{s.docstring}"))
    for c in shape.comments:
        body = c.text.lstrip("#").strip() or c.text
        items.append((c.lineno, f"# {path}:{c.lineno}\n{body}"))
    if not items:
        return []
    items.sort(key=lambda t: t[0])
    prose = "\n\n".join(block for _, block in items)
    return [CodeChunk(LAYER_CODEDOC, "", 1, n_lines, c.text)
            for c in chunk_text(prose, max_chars=max_chars, overlap_chars=overlap_chars)]
```

`core/ingest/code_corpus.py:181-194` (the pure derivation — determinism is contractual):

```python
def derive_code_chunks(path: str, source: str, *,
                       max_chars: int = _DEFAULT_MAX_CHARS,
                       overlap_chars: int = _DEFAULT_OVERLAP_CHARS) -> list[CodeChunk]:
    """The PURE derivation: (path, source) -> the file's L0a + L0b + L1 chunks. Deterministic and
    bit-identically re-derivable from the blob (F-CI2) ..."""
```

**The D0 pin, verbatim from the note (§2 D0):** identity hashes the header-free canonical
body; embed text may keep headers. Per layer — **L0a**: canonical body = text minus the
first line. **L0b**: canonical body = the text, unchanged. **L1**: windows are cut over the
CANONICAL (header-free) prose; the canonical window is both identity input and embed body,
prefixed for retrieval context by a single `# {path}` line (a strippable prefix, exactly the
L0a shape; per-item linenos live in memberships, not in the text).

**Consequence, named (note §2 D0, R7):** identity now differs from embed text, so a shared
atom's stored `text`/`vector` is its FIRST-LANDED rendering — an L0a prefix may carry
another occupancy's path. Coordinates for display resolve from memberships (bp-152), never
from the stored text.

## 7. Items

### Item 1 — L0a + L0b canonicalization, and `content_hash` over the canonical body

- **Objective:** `content_hash` hashes the header-free body; L0a strips its first line,
  L0b is unchanged.
- **Files:** `core/ingest/code_corpus.py`, `tests/unit/test_code_corpus.py`
- **Acceptance test:** a new unit test asserts that for a fixture module, two L0a chunks
  derived from the *same* source at two *different* paths have equal `content_hash` and
  unequal `text`. `uv run pytest tests/unit/test_code_corpus.py` green.
- **Falsifier:** the two hashes differ — the header is still inside the hash, or the
  canonical body was computed off the wrong text. Also falsified if `text` becomes
  header-free (the embed rendering must keep its header; only identity changes).
- **Invariant(s) it must not violate:** `derive_code_chunks` stays a pure, deterministic,
  bit-identical re-derivation (`:184-187`, F-CI2) — same `(path, source)` in, same chunks
  out. Provenance stays structurally hardcoded (`:220`, F-CI1). Layer discrimination
  unchanged.
- **Touches stored data?** No — this item changes derivation only; no store is written.
- **Parallelizable?** No. **Depends on:** none.

### Item 2 — L1 windows cut over canonical prose

- **Objective:** `_l1_chunks` windows the header-free prose and re-prefixes a single
  `# {path}` line, so window boundaries no longer move when a path's length changes.
- **Files:** `core/ingest/code_corpus.py`, `tests/unit/test_code_corpus.py`
- **Acceptance test:** a unit test derives L1 chunks for a fixture whose prose spans ≥2
  windows at two different paths and asserts the `content_hash` **sets** are equal, while
  each chunk's `text` starts with its own `# {path}` prefix.
- **Falsifier:** the hash sets differ at two paths — window boundaries still depend on
  path length, meaning the pin was implemented as strip-at-hash-only rather than
  cut-over-canonical. This is precisely the case the note measured at 7 residual atoms;
  seeing >0 here means the pin did not land.
- **Invariant(s) it must not violate:** L1 stays slotless — `qualname=''` (`:177`, R4).
  Per-item linenos are **not** re-introduced into the text (they live in memberships,
  bp-152). Determinism as Item 1.
- **Touches stored data?** No.
- **Parallelizable?** No. **Depends on:** Item 1.

### Item 3 — the two measured falsifiers: rename mints 0, top-of-file insert mints 0

- **Objective:** discharge acceptance §8(h) and §8(i) as runnable tests carrying the note's
  measured numbers.
- **Files:** `tests/unit/test_code_corpus.py`
- **Acceptance test:** **(h)** rename a fixture file (same bytes, new path): **0** new
  `content_hash` values across all three layers, with the precondition asserted first that
  the atoms pre-exist (a never-embedded file mints 0 trivially — the degenerate input the
  note names). **(i)** insert one line at the top of a fixture whose prose items span ≥2 L1
  windows: **0** new `codedoc` hashes, with the precondition asserted first that the fixture
  has ≥2 prose items (a 0–1-item file passes vacuously).
- **Falsifier:** either precondition assertion passes on a fixture that should fail it —
  the test is vacuous and proves nothing. Or: the counts are non-zero, i.e. D0 did not
  achieve edit-stable identity. The note's counterfactuals are the calibration: rename
  yields 38 under the old identity and 7 under strip-at-hash-only; anything but 0 means the
  windowing pin (not merely the strip) is missing.
- **Invariant(s) it must not violate:** the tests must redden on the degenerate input —
  assert the precondition **before** the claim, per the false-success rule.
- **Touches stored data?** No.
- **Parallelizable?** No. **Depends on:** Items 1, 2.

### Item 4 — repair the carried test surface

- **Objective:** the four carried test files are green under canonical identity.
- **Files:** `tests/unit/test_code_retrieval.py`, `tests/integration/test_code_mirror.py`,
  `tests/integration/test_code_vector_isolation.py`, `tests/unit/test_code_corpus.py`
- **Acceptance test:** the local CI gate — ruff, import-firewall, mypy at its current
  baseline, type_gate, CI-tier pytest — is green. Counts drift; trust the run, not a
  remembered number.
- **Falsifier:** a test is made green by weakening its assertion (deleting a case, relaxing
  an equality to a membership check) rather than by updating the expected identity. Any
  such edit is a red flag on this item, not a pass.
- **Invariant(s) it must not violate:** the mirror firewall assertions in
  `test_code_mirror.py` / `test_code_vector_isolation.py` keep their *strength* — code must
  still be unable to surface in an AUTHORED-scoped read.
- **Touches stored data?** No.
- **Parallelizable?** No. **Depends on:** Items 1–3.

## 8. Math carried explicitly

- **`content_hash`: the atom identity function** — *measures:* the equivalence class of
  chunk bodies modulo their mutable coordinate header — i.e. "same idea, wherever it
  lives". *valid when:* the header is a deterministic, separable prefix of the rendering
  (verified: L0a `:118`, L1 by construction after Item 2) and the canonical body is
  derived by a pure function of `(path, source)`. *fails its keep if:* a rename or a line
  shift mints any atom (§7 Item 3), or two semantically distinct chunks collide because
  canonicalization stripped something load-bearing rather than only the coordinate.

- **The counterfactual ladder (the note's D7 identity row)** — *measures:* how much of the
  dedup is bought by *which* half of D0. Rename cost: **38** atoms under headers-in-hash,
  **7** under strip-at-hash-only, **0** under the full windowing pin. *valid when:*
  measured over the real chunkers on real blobs, like-for-like. *fails its keep if:* the
  ladder does not reproduce — then the note's mechanism story (§3 Q4) is wrong and the
  design question reopens (§10).

## 9. Non-goals

- **No id-shape change.** `rid = f"{path}:{ch.layer}:{ch.content_hash}"` (`:213`) keeps its
  current form. The path-free `"{layer}:{content_hash}"` id is D1 — bp-152.
- **No store, schema, or membership work.** No new file under `core/stores/`.
- **No migration, no rebuild, no re-embedding.** The live store goes stale by design; the
  reconciliation is bp-153. The builder must not "helpfully" migrate rows.
- **No other chunker behavior changes** — the note's §1.2 amendment is exactly bounded:
  identity hashes the canonical body and L1 windows over canonical prose. Nothing else.
  No re-slotting of L1 (PD-5), no L0b span rework.
- **No embed-text redesign.** R7 (representative renderings) is a T4 falsifier, not this
  plan's business.

## 10. Stop-and-raise conditions

- **The counterfactual ladder does not reproduce** (Item 3 shows non-zero, or shows 7 where
  0 is claimed). This is a spec-level surprise about D0's mechanism, not a bug to code
  around: file an issue (`type:defect`, `route:orchestrator`, `track:code-ingest`), park
  the criterion with its re-entry condition, and continue the remaining items.
- **Canonicalization proves non-separable for some real chunk** — e.g. a symbol whose body
  legitimately begins with a `#` line indistinguishable from a coordinate header. Stop and
  raise: a wrong strip is silent corruption of identity.
- **A carried test cannot be repaired without weakening it** (Item 4's falsifier). Raise
  rather than weaken.
- **Any temptation to widen scope into `core/stores/`** — that is bp-152. File and stop.
- The builder performs **no blessing and no status flip** (regime: the owner's merge is the
  only gate) and never writes the fixed points.

## 11. Parked decisions

| Decision | Default recorded | Rejected alternatives (why) | Re-entry condition |
|---|---|---|---|
| L1 per-item slotting | L1 stays windowed + slotless (R4) | Per-item L1 chunks would give L1 lineage chains — rejected as a deliberate re-chunk far beyond D0's bounded amendment | A consumer needs docstring/comment lineage (note PD-5) |
| Embed text keeps headers | Headers stay in `text`; only identity is canonical | Header-free embed text — rejected: retrieval context is load-bearing and the note pins embed text as untouched | T4 shows retrieval loss attributable to header prefixes (R7) |
| Stale-store window | The live store goes stale between bp-151 and bp-153 | Migrate in this plan — rejected: mixes a pure derivation change with a stored-data mutation, the exact coupling the note's D7 slicing avoids | bp-153 lands the rebuild |

## 12. Dependency & ordering summary

Items are strictly sequential: **1 → 2 → 3 → 4**. Item 1 changes the hash; Item 2 changes
what L1 hashes *over*; Item 3 measures the pair; Item 4 repairs the surface they moved.
Nothing here is parallelizable — one file, one semantic change.

Blast-radius order holds: Items 1–3 are pure-derivation and read-only with respect to every
store; Item 4 touches only tests. **No item in this plan writes stored data** — that is
what makes it the safe first plan.

**Why D0 is its own plan (the split judgment the note delegated to /graduate).** The note
guessed two plans; against the current tree it is three, because D0 separates on all four
of the skill's split tests:

1. *One-sentence objective.* "store + land + read" needs two ands; "identity hashes the
   canonical body" does not.
2. *Write scope a reviewer can hold.* This plan is **one** production file (§3 Q6 — no
   external production caller). bp-152's is a new store plus a schema evolution plus a
   lander.
3. *Different blast radius.* bp-151 writes no stored data at all. bp-152 changes a live
   schema. Blast-radius ordering is a within-plan rule; honoring it *across* plans is
   strictly better.
4. *Independently falsifiable, with numbers already measured.* §8(h) and §8(i) are
   discharged here and nowhere else, against a three-rung counterfactual ladder
   (38 → 7 → 0) that localizes a failure to the exact half of D0 that broke.

D0 is also the **precondition** for the rest: finding-0168 addendum 4 raised edit-stable
chunk identity to load-bearing, and D1/D2's dedup claims are only true once identity
survives a rename. Landing it first means bp-152 builds the membership store on an identity
that has already been proven stable, rather than proving both at once.

**Cross-plan edges:** bp-152 `depends_on: [bp-151]` — the store split assumes canonical
identity. bp-153 `depends_on: [bp-152]` — the rebuild needs a lander to rebuild *into*.
Neither is parallelizable with this plan; all three touch the code-ingest lane in sequence.
