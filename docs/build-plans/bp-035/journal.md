# bp-035 journal

## 2026-07-14 — authored `proposed` (orchestrator, graduation of dn-core-query-protocol)

Graduated from ratified `dn-core-query-protocol` §2.3 (the reference agent — "the archetype, and the
first build") + §3 Consequence 2. Owner directed the graduation in-session ("loop back to using ouroboros
itself to identify references"); tier ruled **opus/high, no fable** — the math/design is banked in the
ratified notes, and §2.3 is deliberately the simplest client (no model, no firewall composition).

**Why this is the first plan (not §3.1's doc→doc extractor):** the note's §3 named the doc→doc extractor
as the recommended first graduation, but grounding (Explore sweep, 2026-07-14) found it **already built**
— `ops/code_sensor.py:427` (`_corpus_to_corpus_edges`) mints doc→doc edges (front-matter + inline +
wikilink); the store holds ~272k edges incl. ~73k corpus_to_corpus. So the real gap is the READ surface:
the graph is fed but **agent-unreachable** (`all(target_ref=…)` has zero callers). This plan closes that.

**Grounding done at graduation (§3):** the store's read API (`reference_edges.py:282,312`), the per-commit
identity (`:118-120,142`) → the "current commit" anchor question (Q1, pinned to the run ledger's active
commit / HEAD, parked with the union-across-history alternative rejected); fibers `F` = the reference
store is citation-only, so `E={F}` is free (Q2); zero-reader confirmation (Q3); connected_set = bounded
BFS (Q4); the §2.6 grep-not-store oracle discipline (Q5).

**Reconciliation (§4) → OWED FINDING:** the ratified note's frontmatter ("61k edges … code-anchored") and
§3.1 (extractor as first plan) are STALE — the extractor shipped via the sensor post-snapshot. File a
`spec-fidelity` finding recording this (the note is immutable A8; the finding is the channel; orchestrator
batches the erratum to the owner). This plan edits the note nowhere.

**Scope (§5):** new `core/reference_view.py` + two test files. Store/extractor/`core/temporal` all
untouched (reused/separate). Three items ordered by blast radius: read window → connected_set → grep
oracle. Model estimate opus/250k (deterministic read surface + a differential oracle; the falsifiers are
runnable, not judgment calls).

**Downstream graduations this note still licenses** (recorded in plan §12, NOT authored here): the
build-time repo-derived twin (§2.4), the general capability-scope type system (§2.1 — the fable-grade
piece), wiring `core/temporal` into a query answer, the alignment instrument + diachronic interpreter.

Awaiting the owner-only `proposed → ready` blessing. No work started.
