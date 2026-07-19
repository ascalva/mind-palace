# Journal — bp-073 (Phase Δ: connectivity re-measure — does E_proven break oq-0031 saturation?)

## 2026-07-19 (session-31, OPUS) — minted (proposed) at the Γ-seal; Item 0 = ground the mapping
Graduates dn-agent-taxonomy §3 Phase Δ, the payoff measurement of the Β→Γ→Δ arc. Minted immediately
after bp-071 sealed (Γ), grounded against the LANDED upstream: D3 `core/graph/composed.py`
(`compose` + `ComposedGraph.classes_of` — the per-class attribution the oq-0031 falsifier needs),
the ratified σ*/conductance consumers (`core/graph/sigma_star.py`, `conductance.py`), bp-071's
`causal_edges.sqlite` (E_proven source), MirrorView/MirrorGraph (E_sim + authored nodes), and the
saturation cluster (findings 0096–0100 / oq-0031: golden_recall flat at 1.0 on the 13-doc corpus).

**Deliberately minted with genuine open design (the bp-071 pattern):** §3 carries four lean-defaulted
questions the build's Item 0 must pin against reality —
- Q1 what the dialogue nodes ARE (lean: authored mirror ∪ dialogue_artifact digests; events proven-only);
- Q2 how C-edges (event→endpoint) become node-PAIRS (lean: witnessed COMPOSITION action→commit→file/doc,
  carrying the concatenated witness tuple — finding-0111 + the owner's session-31 composition note);
- Q3 E_sim for dialogue nodes (lean: reuse mirror cosine over dialogue_artifact embeddings);
- Q4 the oq-0031 success criterion, PINNED before measuring (lean: golden_recall un-flattens AND/OR an
  E_proven bottleneck bridges a σ-component) — no moving goalposts, and an honest "still saturates"
  verdict is a `math` finding, never a forced green.

Eval-side (finding-0100: the measurement is eval-side constructible; the substrate retains everything).
NO new instruments (feed the ratified ones unchanged — the note's "assembly, not new instruments").
`depends_on: [bp-069, bp-070, bp-071]` — all landed. write_scope = eval/harness measurement + tests.

**Operational safety (owner raised, session-31): Δ cannot push Ouroboros into recovery.** Recovery is
an UNCLEAN-EXIT fail-safe read off `runs.sqlite`; Δ is eval-side, touches neither the daemon process
nor the run ledger. Added **Item 2b — READ-ONLY by construction:** the live measurement opens every
corpus store with sqlite `mode=ro` (a test asserts no writable handle), so Δ runs safely WHILE the
daemon is live — zero write-contention, recovery structurally unreachable. Made the property STRUCTURAL,
not conventional (the owner's enforcement principle).
**Next:** owner blesses proposed→ready (by hand); then a fresh OPUS /build session, Item 0 first.

## 2026-07-19 (session-32, OPUS) — Item 0 GROUNDING against landed reality (in progress)
Deploy verified first: run #29 (`6b6d21c`, RUNNING) has ZERO code drift vs bp-071 HEAD (`97274e3`);
the integrator is LIVE — `causal_edges.sqlite` grew 1599→**3700 edges / 67 sessions** at run-#29
startup; standing coverage gauge integrable=4074 / witnessed=3700 / **90.8%**, unwitnessed=374
(unresolved commits, NAMED + edge-less by design — no silent drops). Δ deploy-gate satisfied.

**Grounded against the LIVE stores (all reads read-only). Four load-bearing facts:**
1. **E_proven endpoint distribution (causal_edges, 3700 edges):** dst_type = commit 78 · doc **941**
   · file **2681**. Distinct doc endpoints = **208** (build-plan ids 71, finding ids 85, `*.md` 52),
   all resolving to real repo docs on disk (64 design-notes + 72 build-plans + 97 findings + 33
   brainstorms = 266 files). Distinct file endpoints are abs paths (code + memory files).
2. **Q2 (C-edge → node-PAIR) — CONFIRMED (Alberto pre-confirmed the composition lean at mint) +
   concretely grounded.** The robust projection is **shared-witness co-production**: two direct
   `action→{doc,file}` C-edges in the SAME session are causally co-produced → an endpoint↔endpoint
   E_proven pair, witness = (session transcript_digest, both event turns). **53 sessions co-produce
   ≥2 DISTINCT docs** → abundant doc↔doc pairs. This needs NO `commit→file` relation → the §10
   codebase-STOP does NOT trigger (finding-0111 already established a commit's changed-file set is
   unresolvable from any store; co-production sidesteps it — the pairs come from the two proven
   writes directly, not from fanning a commit). Reference-composition (`action→commit ∘
   reference_edges@commit`) is a BONUS where reference_edges has rows at a C-edge's commit sha.
3. **Q1/Q3 (dialogue nodes + their E_sim) — a real DIVERGENCE from the plan §1 E_sim-source
   assumption.** Plan §1 says "MirrorView for E_sim + authored nodes." But the LIVE mirror
   vectorstore (`data/vectors.lance`) holds **ONLY 17 authored janus_notes** (provenance
   `authored-solo`, 26 chunks, 17 digests) — **zero repo docs**. The 208 dialogue_artifacts that
   carry C-edges are a DISJOINT, UNEMBEDDED corpus, and the mirror firewall (MIRROR_READABLE =
   {authored}) structurally REFUSES them (a MirrorView cannot hold them by construction).
   **Consequence (the load-bearing one): over the mirror node set E_proven is EMPTY** — the 17
   janus_notes carry no C-edges — so adding E_proven to the mirror graph does NOTHING and CANNOT
   break the oq-0031 saturation. The measurement is only non-trivial over the **dialogue_artifact**
   node set (the docs that HAVE C-edges), and for E_proven to be shown BRIDGING E_sim-gaps there,
   those docs must carry E_sim — i.e. **the measurement must embed the dialogue-artifact corpus
   eval-side** (Q3 lean's own words: "reuse the mirror's cosine machinery over dialogue_artifact
   embeddings"). That is a heavier, embedder-touching build than "feed the existing MirrorView," and
   it brushes the §9 "NO model" non-goal (embeddings are the deterministic substrate the note already
   treats as model-free — `MirrorGraph` is "model-free (NumPy cosine only)"; the vectors are upstream
   floor — but running the embedder over 208–266 docs is a real, owner-visible scope change).
4. **Q4 (success criterion):** the CLEAN, computable signal is structural — an E_proven bottleneck
   edge bridges two nodes that E_sim leaves in different σ-components (`ComposedGraph.classes_of`
   attributes the bridge to E_proven; `sigma_star` flips None→reading). golden_recall-un-flattening
   is the retrieval signal but golden_recall is a MIRROR-retrieval metric (over janus_notes + the
   golden set) — it does not obviously transfer to the doc graph, so it may be an honest limitation,
   not a forced green. Pin the structural signal as primary; treat recall as best-effort.

**Item 0 verdict so far:** Q2 resolved (builder, spec-fidelity — co-production supplies E_proven, no
§10 stop). Q1/Q3 grounding surfaces ONE owner-level decision — what node set the payoff is measured
over + accepting the embedder in the eval loop — because it materially changes the build's shape and
brushes a non-goal. RAISING to Alberto (present) before committing Items 1–2; finding-0112 to record
the grounding. Items 1–2 PARKED on that answer; re-entry = the node-set/E_sim ruling.

### OWNER RULING (2026-07-19, session-32) — OPTION A. finding-0112 RESOLVED. Item 0 COMPLETE.
Alberto ruled **A**: the Δ measurement **embeds the dialogue-artifact doc corpus eval-side**
(ephemeral, read-only, never persisted). Accepts the deterministic ingest embedder in the eval loop
over the doc corpus. **Item 0 answers, PINNED (these supersede the plan §1/§3/§6/§11 provisional leans):**
- **Q1 (node set):** the **dialogue-artifact docs that carry C-edges** — build-plans, findings,
  design-notes, brainstorms (208 distinct doc endpoints of 266 on disk). Each doc = ONE node,
  identified by its **artifact-id / repo path** (NOT a content digest — the C-edge `dst` is the id).
  The 17 janus_notes are NOT in the measured graph (disjoint island, no C-edges → inert for E_proven).
  Chat-session/L1-event nodes stay out (proven-only endpoints, not graph participants in v1).
- **Q2 (C-edge → node-pair):** **shared-witness co-production** — group C-edges by `session_id`;
  every unordered pair of DISTINCT doc endpoints within a session is an E_proven doc↔doc edge,
  weight `PROVEN_WEIGHT=1.0`, carrying the witness tuple (session `transcript_digest` + the two
  events' `(event_order, witness_turn)`). 53 sessions co-produce ≥2 docs. NO commit→file fan-out
  (finding-0111's falsifier); reference-composition deferred (optional bonus, not v1).
- **Q3 (E_sim):** cosine over **eval-side doc embeddings** — read each doc file, embed with the
  ingest embedder (reuse `core/ingest/embed.py` machinery, the model-free substrate), one centroid
  per doc (the `note_centroids` pattern), `sim ≥ σ` edges over the shared σ-grid. Ephemeral: computed
  in-memory for the measurement, NEVER written to `data/vectors.lance` or any daemon store.
- **Q4 (success criterion — PINNED before measuring, no moving goalposts):** PRIMARY = **structural**:
  ≥1 doc-pair whose `sigma_star` is None under E_sim-alone but a reading under E_sim∪E_proven, with
  `classes_of` attributing the connecting bottleneck edge to **E_proven** (a genuine proven bridge
  across an E_sim gap). SECONDARY/best-effort = golden_recall un-flattening — but golden_recall is a
  MIRROR-retrieval metric (janus_notes + golden set), so it likely does NOT transfer to the doc graph;
  report that honestly rather than force it. `discriminates := (proven_bridges non-empty)`.
- **Module decision:** NEW `eval/harness/re_measure.py` (per §11 default) — the doc embedding +
  assembly + measurement lane; connectivity.py/fibers.py touched only if a shared helper is needed.
**Items 1–2 UNPARKED.** Next: Item 1 — `assemble_composed_graph` over real stores (read-only),
fixture-tested; then Item 2 — re-measure + honest oq-0031 verdict. Item 2b (read-only construction)
threads through both. All corpus reads use sqlite `mode=ro` / read-only file opens.

## 2026-07-19 (session-32, OPUS) — Item 1 GREEN (assemble_composed_graph)
`eval/harness/re_measure.py` (NEW, in write_scope) — the pure/injected Δ assembly:
- **`proven_pairs_from_causal(edges, *, node_ids)`** — E_proven via shared-witness co-production:
  group C-edges by session, every unordered pair of DISTINCT doc endpoints (in node_ids) → a
  `ProvenPair` carrying `(session_id, (ProvenEndpoint_a, ProvenEndpoint_b))` where each endpoint =
  (dst, event_order, witness_turn, witness_digest). Empty witness_digest → `WitnesslessProvenEdge`
  (fail-loud, the Item 1 falsifier). Min-event_order per doc for determinism; non-doc endpoints
  (commit/file) ignored; a doc outside node_ids dropped. Same pair in N sessions → N witnessed pairs,
  ONE graph edge (compose flattens by max).
- **`sim_edges_from_embeddings(emb, *, node_ids, sigma_floor)`** — E_sim = cosine (reuses
  `core.dreaming.cluster.similarity_matrix` + `NoteVector`, DRY — no new similarity), kept where
  `cos >= sigma_floor`. Thresholding at the loosest grid σ MATCHES `MirrorGraph.build(view,
  sigma=min(grid))` so `build_max_spanning_tree`/`_grid_snap` (which floors at grid[0]) see an
  equivalent graph. A node without an embedding is E_sim-absent (proven-only) — supported.
- **`assemble_composed_graph(*, node_ids, embeddings, causal_edges, sigma_floor, proven_weight=1.0)
  -> ComposedGraph`** — feeds the two edge classes to core's `compose()` UNCHANGED. Pure/injected
  (reads no store, calls no embedder) → **fixture-testable without ollama** (composed.py's discipline
  + finding-0100). Embeddings are a Mapping arg; the live read-only loaders are Item 2.
`tests/unit/test_re_measure.py` (NEW) — 9 tests: headline (a proven co-production bridge db—dc flips
da—dd None→reading via the REAL `sigma_star`, chain `da→db→dc→dd`, classes_of={E_proven}); the three
falsifiers (witnessless→raises; single-doc/non-doc→no pair; both-classes→both tags kept); dedup-with-
two-witnesses; witness-carried. **16 passed** (9 + the 7 composed-graph guards, unchanged). Ratchet
untouched (no core edit — eval-side only). **Next: Item 2** — live read-only loaders (embed the doc
corpus eval-side, ephemeral; read `causal_edges.sqlite` mode=ro) + `ReMeasureReport` + the oq-0031
verdict; Item 2b asserts every corpus handle is read-only.

## 2026-07-19 (session-32, OPUS) — Items 2 + 2b GREEN; oq-0031 LIVE VERDICT (finding-0113, owner-routed)
Added to `re_measure.py`: `ReMeasureReport`/`ProvenBridge` + `re_measure_oq0031` (assembles E_sim-only
vs E_sim∪E_proven, runs the RATIFIED `sigma_star` over BOTH via `cast`, attributes the delta); the
saturation gauge `frac_connected_by_sigma` + `n_sigma_uplifted`; live read-only loaders
`open_causal_edges_ro` (mode=ro), `load_causal_edges`, `doc_node_ids`, `resolve_doc_path`, `embed_docs`
(ephemeral doc embedding, head-truncated to `char_limit=4000` to fit the embedder context window —
8000 chars 400'd; empty/unresolved → proven-only node). **14 tests pass; ruff clean; no core edit
(ratchet 19 untouched).**
**Item 2b:** `test_open_causal_edges_ro_refuses_writes` — a write through the measurement's C-edge
handle raises `sqlite3.OperationalError: readonly`. Every corpus read is mode=ro / read-mode `open`;
embeddings are in-memory, NEVER persisted → Δ is safe against the live daemon (recovery unreachable).

### LIVE oq-0031 VERDICT (real corpus: 208 docs, 3700 C-edges → 1068 proven edges, 21528 pairs)
doc-doc cosine p50=**0.46** (topically DENSE — one project). frac_connected E_sim → E_sim∪E_proven:
σ0.30 1.000→1.000 · σ0.60 0.943→1.000 · **σ0.70 0.261→1.000 (+0.739)** · σ0.80 0.004→0.770 · σ0.90
0.0002→0.457. **`proven_bridges=0`, `discriminates(pinned)=False`** — HONESTLY, not forced.
**The nuanced, non-forced answer (finding-0113, ftype=math, route=orchestrator):**
1. The 13-doc saturation was **INPUT-STARVATION** — at n=208 the connectivity gauge already
   discriminates strongly under E_sim ALONE (sweeps 1.0→0.004); the ceiling was not real.
2. E_proven is a **real second lever via σ\*-UPLIFT** (not loose-grid bridging): with nodes+E_sim held
   identical, +0.74 connectivity at σ=0.7 is cleanly attributable to the proven edges. Confirms the
   grounding law (§2.2) as a genuine mechanism.
3. The pinned bridge-criterion (None→reading at the loosest grid) is **VACUOUS on a dense corpus** —
   E_sim alone fully connects all 208 docs at σ=0.30, so no disconnected pair exists to rescue. The
   correctly-calibrated structural signal is σ*-uplift (`n_sigma_uplifted`/the frac_connected curve),
   NOT the component-bridge count. A measurement-calibration lesson, recorded honestly.
**Net:** the taxonomy's answer is **necessary-but-insufficient, refined**. finding-0113 proposes
resolving the 0096–0100 cluster with this verdict — OWNER-ROUTED (a math finding re-enters via the
gate). σ*-uplift derived from the curve: ≥73.9% of the 21528 pairs cross σ=0.7 (E_sim→full). The exact
`n_sigma_uplifted` scalar wasn't separately captured — the confirmation rerun's embedder TIMED OUT
under contention with the live daemon (run #29 also embeds); a fitting demonstration that Δ is
read-only/daemon-safe (Item 2b) yet shares the deterministic embedder. The curve is the primary
quantification. **Ratchet confirmed 19 (unchanged); 91 graph/eval tests + 14 re_measure tests green;
ruff clean.** Remaining: commit (feat re_measure / finding / seal); push; CI green; seal.

### SESSION PAUSE (2026-07-19, session-32) — build COMPLETE + committed locally; awaiting owner
All three items done. THREE commits landed on `main` (local, NOT pushed): `6741fcf` feat (re_measure.py
+ test_re_measure.py) · `739ecd7` finding-0112/0113 + journal + plan(status→in-progress) · `b996479`
checkpoint (this pause note). This trailing checkpoint edit is left UNCOMMITTED by design (the
journal-gate wants a journal fresher than the last commit at close; the fresh-agent content is already
committed at `b996479`). **Held the push deliberately** — the oq-0031 verdict (finding-0113) is the
arc's payoff + an OWNER-ROUTED math finding, presented to Alberto for engagement before it goes to
CI/main. **PARKED on owner (re-entry conditions):**
1. `/usage` relay to fill `cost.actual` (well-pinned build, ~0.5× territory expected).
2. Owner blessing to resolve the **0096–0100** cluster with finding-0113's verdict (a design act).
3. Push decision (routine — push→CI→semantic-release; expect a rebase onto a `chore(release)` commit
   per finding-0110).
**To SEAL (after owner):** clear `.claude/state/active-plan`; flip plan status→complete + cost.actual;
PROGRESS.md checkpoint (orchestrator, single-writer — do AFTER clearing active-plan so scope-guard
permits it); final journal seal w/ read map; push; verify CI all-green BEFORE claiming attestable.
**Read map (concept-bearing lines, ~15% of the diff):** `eval/harness/re_measure.py`
`proven_pairs_from_causal` (the co-production projection + fail-loud witness), `sim_edges_from_embeddings`
(the grid-floor threshold matching MirrorGraph), `re_measure_oq0031` (E_sim-only vs full + the σ*-uplift
loop), `ProvenBridge` docstring (why the bottleneck is NOT the proven edge), `embed_docs` (ephemeral
read-only doc embedding); `finding-0113` §Verdict (the 3-part answer). Fresh-agent sufficient.

### SEAL (2026-07-19, session-32) — owner blessed: seal + push + resolve 0096–0100. bp-073 COMPLETE.
Alberto: "seal it and push, resolve 0096–0100" + `/usage`. Executed:
- Plan status in-progress→**complete**; `cost.actual` filled (179.8k output = 0.90×; $21.03 opus;
  week 19%→20% +1% gate figure; Fable 14% untouched; session →41%).
- **finding-0113** status→resolved (owner-blessed verdict). **Findings 0096/0099/0100 RESOLVED**
  directly; **0097/0098** resolved root-cause (starvation) — the optimizer emit-on-flat / SE-3-bar
  hardening is a SEPARATE future finding if wanted (bp-073 §9 held sweep-rule tuning out of Δ; recorded
  honestly, not silently claimed fixed). **oq-0031 RETIRED** (answer filled, status→resolved);
  **oq-0024 UN-blocked** (σ re-tune can now discriminate on the 208-doc corpus).
- PROGRESS.md bp-073 seal entry appended; active-plan pointer cleared (builder→orchestrator).
- Diagnostic still owed + tracked separately: why the mirror note-corpus is stuck at 13 while Ouroboros
  runs (vault-sync not finding new notes?) — NOT re-blocking.
**Then:** commit the seal (docs; no code trailer); push; verify CI all-green BEFORE attestable
(finding-0110 — expect a rebase onto a `chore(release)` semantic-release commit). Δ is read-only, so the
push does not touch the live daemon's stores. Suite green-except-ratchet(19). bp-073 SEALED.

### CI FIX (2026-07-19, session-32) — type-gate RED @ 3a1cce3, fixed (the finding-0110 lesson, extended)
Pushed @ 3a1cce3, then CI: `pages` green, `ci` FAILED on the **type-gate** (ratchet/semgrep/vault/
gitleaks all green). I ran ruff pre-push but NOT mypy — the finding-0110 lesson ("green ≠ pushed")
extends to mypy, not just pytest. 4 Tier-2-floor errors in `re_measure.py`: (1-2) `int(e["event_order"])`
/`int(e["witness_turn"])` on `object`-typed Mapping values → `int(str(...))`; (3-4) the σ*-uplift sum
compared `float | None` σ* values (mypy couldn't narrow across a subscript) → extracted a typed
`_sig(SigmaStar | None) -> float` helper (None→-inf). Now: Tier-2 floor **0 errors**, tests baseline
**69** (unchanged), ruff clean, 14 tests green. Fix commit + re-push; re-verify CI. **PROCESS:
run `uv run mypy core agents eval ops scheduler scripts` BEFORE every push, alongside ruff + pytest.**
