---
type: finding
id: finding-0147
status: open
created: 2026-07-21
updated: 2026-07-21
links:
  - docs/design-notes/code-ingest-pipeline.md      # the audited artifact (draft, corrected in place)
  - docs/findings/finding-0146.md                  # the note's warrant
  - docs/findings/finding-0145.md                  # sibling measurement the note cites
ftype: spec-fidelity
route: orchestrator            # feeds the owner's ratification decision on dn-code-ingest-pipeline
resolution: null
---

# Audit log — fable line-by-line audit of `dn-code-ingest-pipeline` (opus-authored, untrusted)

## Why this audit ran

The note was authored by a worker spawned `fable/max` that was **silently downgraded to
`claude-opus-4-8`** (confirmed via completion `<usage>`; the known worker-dispatch fable→opus
bug). Its banner self-reported "Composed at fable" — **false**. The owner directed a
painstaking main-loop fable audit of every line, citation, decision, and falsifier before
ratification. This finding is the audit log; all corrections were applied in place (the note
is `draft`; A8 untouched — no ratified text was edited, and commit `625a058` is verified to
have touched only the new note).

## Verdict

**Substantially sound — no hallucinated citations found.** Every `path:line` ground-citation
opened resolved to code saying what the note claims (~50 citations across 20 files); every
design-note quote checked was verbatim or faithful (incl. the agent-taxonomy §2.4 fiber
criterion, agentic-loop EX-2's four-mechanism stack, the axis note's §8 partial-amendment
precedent, cross-strata-dreamer XS-a per-grant); the six decisions are consistent with the
hard constraints (#8 memory ceiling, mirror firewall, DRY, S/F/C/D algebra); all three worker
self-flagged corrections (origin(e) edge-scoping → PD-J; L2a-as-fiber; AST edges →
`code_to_code`) were independently confirmed **right**; the owner's full design (L0a/L0b
joined two-readings, L1 distinct-but-joined, L2a fiber, L2b resolver + S-bridge, D/C
composition) is captured. The 3,318-comments/247-files measurement **reproduced exactly**
(set = `{core, ops, edge, config, scripts, agents, eval}`), as did 28 chunks/19 sources,
528 files, 5,065 symbols, and finding-0145's 2,199/624.

**But 16 defects were found and corrected** — 2 false present-tense claims, 1 enum miscount,
1 missing-precondition overclaim, 3 stale/wrong numbers, 1 falsifier carrying dead-draft
residue, 1 garbled mitigation claim, 1 DRY-seam imprecision, and the false banner itself.

## Corrections applied (each verified against disk)

1. **Banner provenance (the headline):** "Composed at fable" → corrected to
   opus-worker-authored + fable-audited. A live instance of banners-as-unreliable-self-report
   for the standing fable-provenance audit question.
2. **§2.3 "existing five" → six.** The enum has six classes; `DERIVED_STRATUM`
   (`core/provenance.py:49-56`) was never ruled out. Added its exclusion (reserved dreamer
   substrate ≠ instrument readings).
3. **§2.1 L0a cross-module `inherits`/`calls` overclaim.** The ledger's `imports` table
   records only the ROOT of each dotted import (`ops/code_snapshot.py:73`, `_module_imports`
   `:140-147`) — it cannot resolve an imported name to its defining module. Named the
   additive import-record extension as CI-3's precondition for any cross-module mint.
4. **§2.5b D "consumed by the temporal machinery" — false.** Nothing feeds code blob chains
   into it: `supersession_poset` (`core/temporal/acquire.py:31`) reads `VersionStore` only.
   Corrected to ready-not-wired; the store-free `poset_from_chains`
   (`core/temporal/boundary.py:99-112`) accepts the chains when a consumer arrives. §2.5
   table D row re-marked **recorded** (was "live — + temporal machinery").
5. **§2.5b "vector rows carry an `embedder` version stamp (A7 pin)" — false.** The schema
   has no such column (`core/stores/vectorstore.py:27-37`). A7 is a corpus-wide config-level
   pin (fixed-version cuts; reset+re-embed on change); a per-row stamp would ride the
   `layer`-column migration.
6. **Numbers:** ledger commits 899 → **902** at `625a058` (899 was finding-0145's stale
   `20253d5` reading); LOC 76,507 → **76,508**; C-edges 4,084 annotated as the AL-3-seal
   count (**4,160** live at audit — three places + cross-ref block); reference_edges
   accumulated 950,025 at audit added.
7. **F-CI2 / M-C2 "L0⊔L1 partition byte-cover" — dead-draft residue.** After the owner's
   two-reading refinement, L0b overlaps by design and L1 re-projects content L0a carries;
   only **L0a** partitions. Falsifier and measure rewritten to the L0a cover check.
8. **§2.1 "module preamble" → module shell** (preamble + inter-symbol + trailing code) so the
   byte-cover invariant is well-defined.
9. **§2.1 L0b / §2.2 L1 DRY seam:** the reused unit is `chunk_text`
   (`core/ingest/chunk.py:31-56`), not `derive_chunks` — the wrapper bundles the note-specific
   Logseq `strip_properties` pass, which must not run on code (0 tracked `.py` lines match
   `_PROP` today — measured; exclusion made structural, not luck).
10. **§2.4 L2b-3 example-path mitigation was garbled:** the drafted text implied the
    shorthand patterns' existence check already covered the literal `note-citation` false
    positive; it does not (`extract_references` mints with no existence check,
    `ops/code_sensor.py:243-247`). Made the tree-existence check an explicit NEW rule for
    every corpus-target mint.
11. **§2.2/§2.7 "main-package" pinned** to the exact reproducing set (audit reproduced
    3,318/247 exactly).
12. **§2.6 clause table completeness:** added the UNTOUCHED disposition for §1.2's remaining
    non-goals (esp. the no-promotion-path clause).
13. **§2.6 sibling row (agentic-loop)** aligned with the note's own §2.5b correction: the
    code-side consumer is the PD-J node-keyed sibling reader, not `origin(e)` itself.
14. **Front matter:** added `cross-strata-dreamer.md` to `links` (its XS-a per-grant ruling
    is load-bearing for §2.3; φ_doc mints citation edges from `links`).
15. **Cross-ref temporal citation** corrected (poset core CAN feed, not "the poset the
    D-chain feeds"); `acquire.py:31` added.
16. **Live-store readings block** re-stamped with independent audit verification marks.

## What was checked and found CLEAN (so the owner need not re-check)

All citations into: `core/ingest/{pipeline,chunk,index,embed,amend,curated}.py`,
`core/provenance.py`, `core/stores/{vectorstore,reference_edges,code_observations,sourceset}.py`,
`ops/{code_sensor,code_snapshot}.py`, `core/{scope,origin_view,integrator}.py`,
`core/complex/build.py`, `core/temporal/boundary.py`, `config/defaults.toml`. Quotes/sections
in: dn-code-observation-projection (all seven disposition rows accurate),
dn-fiber-geometry §2.0/§2.2, dn-agent-taxonomy §2.3/§2.4/§2.5, dn-agentic-loop
§2.0/§2.4b/G-C/F-AL4, dn-authorship-distance-axis §8/PD-1/a₂/§3.7d, dn-self-sensing
§2.4/§2.6, dn-chat-sensor §2.3, dn-inner-outer-core, dn-cross-strata-dreamer XS-a.
Linked-note status annotations all correct (axis = draft; the rest ratified). Falsifiers
F-CI1–F-CI7 are real, observable, and distinct from acceptance (F-CI2 after correction).
The one `[FROM MEMORY]` claim (Qwen3-Embedding code-retrieval competence) is properly
flagged for the external-grounding gate and remains the only external dependency.

## Routing

`spec-fidelity` → orchestrator (the audited artifact is a design note awaiting the owner's
ratification hand-edit; the audit changes no gate). Sibling context: the standing
fable-provenance question (were past "fable" banners actually opus?) gains one confirmed
instance here.
