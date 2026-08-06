# bp-151 — journal

## Pre-build notes for whoever picks this up

- ⚑ **Do NOT change the row id shape.** `code_rows` builds
  `rid = f"{path}:{ch.layer}:{ch.content_hash}"` (`core/ingest/code_corpus.py:213`) and it
  keeps that form in this plan. The path-free `"{layer}:{content_hash}"` id is D1's change
  and belongs to bp-152. Here only the *hash inside* the id becomes canonical. Widening into
  the id shape turns a pure chunker change into a store change and breaks the plan's
  blast-radius guarantee (this plan writes no stored data at all).

- ⚑ **Identity changes; embed text does NOT.** `text` keeps its coordinate header — that
  header is retrieval context and the note pins it as untouched (R7). Only `content_hash`
  hashes the header-free body. A builder who strips headers from `text` has implemented a
  different design.

- ⚑ **L1 is the whole difficulty, and strip-at-hash-only is the trap.** `_l1_chunks`
  interleaves one header per prose item (`:166-172`), joins into `prose` (`:176`), and only
  *then* windows (`:177-178`). So window boundaries are computed over header-bearing text.
  Stripping at hash time alone leaves a rename minting **7** L1 atoms. The pin is: **cut the
  windows over canonical prose**, then re-prefix a single `# {path}` line. The
  counterfactual ladder is your instrument — rename cost **38** (headers in hash) → **7**
  (strip-at-hash-only) → **0** (the windowing pin). If you measure 7, you implemented the
  wrong half.

- ⚑ **Assert the precondition BEFORE the claim, every time.** Both §8(h) and §8(i) have named
  degenerate inputs that pass vacuously: renaming a never-embedded file mints 0 trivially,
  and a file with 0–1 prose items has no window boundary to move. The test must redden on
  those fixtures. A green test that cannot fail is worse than no test — this is the
  false-success rule, owner-agreed.

- ⚑ **The live store goes stale, by design — do not migrate it.** Changing `content_hash`
  means stored ids no longer match derived ones. That is expected: vectors are derived and
  regenerable, and the reconciliation is bp-153's rebuild. Existing rows keep serving
  retrieval in the meantime. Any migration attempt here is scope creep with stored-data
  blast radius.

- ⚑ **Canonicalization must be provably separable.** L0a's header is a single first line
  joined with `\n` (`:118`), and the oversized branch already re-prefixes onto a header-free
  body (`:121-123`) — so the split is demonstrably safe there. If you find a real chunk
  whose body legitimately starts with a `#` line indistinguishable from a coordinate header,
  **stop and raise**: a wrong strip is silent identity corruption, the exact failure class
  this plan exists to remove.

- **Determinism is contractual.** `derive_code_chunks` is documented as bit-identically
  re-derivable (`:184-187`, F-CI2). Nothing in this plan may make it path-dependent,
  order-dependent, or environment-dependent.

- **Grounding is fresh.** Every `path:line` in §3 was re-opened against HEAD `174d06c` on
  2026-08-01, and `git log --since=2026-07-27` shows zero drift in `code_corpus.py`. Trust
  the plan's citations, but re-verify if HEAD has moved before you start.
