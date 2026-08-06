# bp-151 — journal

## 2026-08-06 — build complete, all four items, PR open

**Status.** Items 1–4 built and green on `build/bp-151-canonical-atom-identity` (base
`45c4a15`); the ladder reproduces (rename 11,096 → 2,373 → **3**; top-insert 2,114 → 2,114 →
**0**); one spec-level surprise found, measured, filed as **issue #31** and parked with a test.
Not a seal and not a status flip — the owner's merge is the gate.

**Completed.**

- **Item 1 — L0a/L0b canonicalization + `content_hash` over the canonical body.** `CodeChunk`
  gained a sixth field, `canonical_body`, and `content_hash` hashes *that*. The field is the
  design judgement of this build: the plan's §4 wrote `sha256(self.canonical_body…)` without
  saying whether the body is a stored field or a property that re-strips `text`. A property
  would re-derive identity by parsing the embed text, and the plan's own stop-and-raise names
  the failure it invites — a body whose first line legitimately starts with `#`. A field carries
  the canonical body *from the site that already holds it* (L0a has `body` in hand; L0b's window
  IS its body; L1's window is cut canonical), so a wrong strip is unrepresentable rather than
  merely unlikely. Cost: six positional fields, mitigated by keyword construction at all four
  sites and by a ratchet test (`test_every_chunk_pairs_a_headered_embed_text_with_a_header_free_
  canonical_body`) that checks the text↔body relation per layer at every site.
- **Item 2 — L1 windows cut over canonical prose.** `_l1_chunks` no longer interleaves per-item
  headers; `prose` is the bodies alone, windowed, and each window's embed text is
  `# {path}\n{window}` — one strippable line, the L0a shape. Per-item linenos deliberately not
  re-introduced (they are bp-152's memberships). L1 stays slotless.
- **Item 3 — the two measured falsifiers.** §8(h) rename → 0 new atoms across all three layers;
  §8(i) one-line top-of-file insert → 0 new codedoc atoms. Both assert their preconditions before
  their claim, and (h) additionally computes the pre-D0 identity inline (`_raw_atoms`, one
  hashlib call — not a duplicated chunker) and asserts the SAME rename mints under it, so the
  claim cannot pass vacuously.
- **Item 4 — carried tests.** Nothing needed repair: 39/39 green across the four carried files
  with no assertion touched. The reason is §3 Q7 — the row id keeps `{path}:{layer}:{hash}`, so
  ids stayed unique and every id-shaped assertion held.

**The three traps, and what actually happened at each.**

1. *Row id shape* — untouched, as pinned. The (h) test asserts over `(layer, content_hash)` and
   says so in its docstring, because rids DO still move on a rename until bp-152.
2. *Embed text* — unchanged in kind; L0a/L0b renderings are byte-identical to before. L1's
   rendering DID change (one `# {path}` line instead of interleaved per-item headers) — that is
   the D0 pin itself, not drift, and the note's D7 already budgets L1 re-embedding for it.
3. *Strip-at-hash-only* — measured, not guessed. Mutation B (headers back in the prose, hash
   strips the window's first line) reddens four tests including §8(i); the aggregate rename cost
   under it is 2,373, ~790× the pinned residue of 3.

**The one surprise — issue #31, parked.** With D0 landed, 577/580 files mint 0 on rename; three
mint exactly 1, all `code_ast`. Cause, confirmed by instrumented measurement rather than
inspection: `_l0a_chunks` decides the oversize split on `len(header + "\n" + body) <= max_chars`,
so the *path's length participates in a cut decision* — the exact L1 mechanism, surviving in a
second place. Fixing it is one token (`len(body)`), and that is precisely why it is filed rather
than done: it changes chunk boundaries for **123 L0a groups across 95 files** (1.8% of 6,813),
which §9 forbids ("no other chunker behavior changes"). Widening a non-goal is not a builder's
call. The residue is now *executable*: `test_l0a_oversize_threshold_is_the_one_rename_residue`
pins it at exactly 1 minted atom and reddens the moment someone implements option A — the
re-entry condition, made mechanical.

**Verification.** ruff clean · mypy(dirs) 0 in 262 files · mypy(argless) 69 at the tests baseline,
unmoved · type_gate OK · pytest 2427 passed / 5 failed, all five proven diff-innocent by stashing
the branch and re-running on the clean base (2 expected — the finding-0103 core-self-containment
ratchet and `test_dream_v2_live`; 3 the known local-only enforcement redness, issue #13 /
finding-0280). Teeth proven by three mutations, each reverted: identity→`text` reds 3 tests;
strip-at-hash-only reds 4; a wrong L0b canonical body reds the ratchet.

**In-flight.** Nothing. Working tree = the two files below plus this journal.

**Next action.** None for the builder. For the reviewer: audit the `canonical_body`-as-field
judgement (Item 1 above) and rule issue #31 A-or-B. bp-152 is unblocked either way — the residue
is orthogonal to the store split.

**Open questions.** Issue #31 (`type:defect`, `route:orchestrator`, `track:code-ingest`, `parked`)
— the L0a oversize-threshold residue, with both options costed and the re-entry condition stated.

**Context-manifest delta.** Read beyond §2: `core/kernel/ingest/chunk.py` (the window machinery —
load-bearing, its `_blocks` strip-and-repack is why a *blank*-line top insert is invisible to L0a
and a real code line is not), `ops/code_snapshot.py` `parse_source`/`FileShape` (the prose items'
provenance), and the four carried test files. Proved irrelevant: `core/stores/vectorstore.py`
beyond the three layer constants — nothing in D0 reaches the store.

```read-map
core/ingest/code_corpus.py:102: content_hash — identity is the canonical body, the whole plan in one line
core/ingest/code_corpus.py:98: the CodeChunk field pair — embed text vs identity input, the design judgement
core/ingest/code_corpus.py:147: the KNOWN RESIDUE comment — issue #31 at the exact decision that carries it
core/ingest/code_corpus.py:197: _l1_chunks docstring — why strip-at-hash-only is not enough, measured
core/ingest/code_corpus.py:212: prose items lose their headers — the windowing pin itself
tests/unit/test_code_corpus.py:196: §8(h) rename mints 0, with the pre-D0 counterfactual as teeth
tests/unit/test_code_corpus.py:222: §8(i) insert mints 0, three preconditions before the claim
tests/unit/test_code_corpus.py:251: the text↔canonical_body ratchet across all four construction sites
tests/unit/test_code_corpus.py:275: the parked residue, pinned at 1 atom — the issue #31 tripwire
docs/build-plans/bp-151/journal.md:1: this entry — why canonical_body is a field, not a property
```

## Follow-through
- **Built?** Yes — all four items, plus one ratchet and one characterization test beyond the plan.
- **Wired / delivered (or why dormant)?** Live on the derivation path: `derive_code_chunks` is what
  `CodeCorpusSync._embed_and_land` calls, so the next `code_sync` derives canonical ids with no
  switch to flip. There is no flag and none is wanted — D0 is a correction, not a feature.
- **Does a consumer use it?** Yes, immediately and by design the stored corpus goes STALE: derived
  ids no longer match stored ones (§9 — no migration here; bp-153's rebuild reconciles). Existing
  rows keep serving retrieval meanwhile; nothing breaks, nothing was migrated.
- **Track state (what remains on this track)?** bp-152 (membership store + path-free atom id) and
  bp-153 (the one rebuild) — both un-minted, both gated on this merge. Issue #31 is the only open
  question this build raised.
- **Opened a new track/finding?** No new track. One issue: **#31**.

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
