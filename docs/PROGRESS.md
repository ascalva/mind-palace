# Build Progress

Terse, append-only log maintained by the building agent. **One entry per phase/checkpoint:** what was built, what was verified against the gate, what's next, and any decisions made. A fresh build session resumes from this file + `CLAUDE.md` + the current phase's section of `docs/BUILD-SPEC.md` — not by replaying chat history.

Keep entries short. Cite paths, not contents.

---

## Phase 0 — Foundations, invariants & Constitution

**Status:** COMPLETE (2026-06-25)
**Gate to verify:** model responds over HTTP; vitals flow into DuckDB; sealed core has no network egress (test it); a trivial agent inherits the Constitution.

**Built**

- Repo scaffold per §17: zone packages `core/` (Zone A) + `edge/` (Zone B) with boundary docstrings; reserved packages (librarian/curator/dreaming/ingest/matching/factory/sandbox, scheduler/ops/eval/agents) stubbed with phase markers; `cloud/` (Terraform, READMEs). `pyproject.toml` (deps: duckdb, psutil; dev: pytest, ruff; pytest `pythonpath="."`), `.gitignore`, `.venv`.
- Structural egress guard `core/sealing.py`: fail-closed, process-wide, permits only loopback (the Ollama channel) + AF_UNIX; raises `SealedCoreEgressError` otherwise. Pure decision fn + `socket.connect` monkeypatch. Installed by `core.runtime.bootstrap()`, not at import.
- Config `config/defaults.toml` + typed loader (`config/loader.py`); `get_secret()` reads env/Keychain only — no secrets in repo.
- Two-slot model server `core/models/`: registry + memory-ceiling accounting, stdlib Ollama HTTP client (no 3rd-party net dep in core), `TwoSlotLoader` (pinned + single worker, stretch evicts pinned, refuses breaching loads before any Ollama call), `ModelServer` facade.
- Telemetry `core/stores/telemetry.py`: DuckDB store, scoped `TelemetryWriter`/`TelemetryReader` (write-only / read-only by design), `vitals` table + dormant `sensor_readings` (§20.6), migrations. Vitals emitter `core/vitals.py` (mem/cpu/load/rss).
- Constitution inheritance `core/constitution.py`: load + SHA-256 fingerprint + `frame_context()` assembling Constitution outermost. Trivial `Agent` (`core/agent.py`) + self-evaluation seam stub. Sealed-core entrypoint `core/runtime.py`.
- Docs: `docs/schema.md`, `docs/runbook.md`.

**Verified**

- `ruff check .` clean; `pytest` 23/23 pass (22 logic + 1 live).
- [1] no-egress: external connect (192.0.2.1) blocked by guard, live; loopback to Ollama allowed.
- [2] vitals flow: 6 readings written to real `data/telemetry.duckdb`, read back.
- [3] inheritance: `ctx[0]` is the Constitution; fingerprint `1818a46e…`.
- [4] model responds: pinned `qwen3.5:2b` returned "ready" through the sealed core.

**Decisions (§20)**

- §20.1 models: pinned `qwen3.5:2b` (q8, ~2.7 GB; q4_K_M ~1.9 GB optimization deferred); routine `qwen3.5:9b`; synthesis `qwen3.6:27b`; stretch `qwen3.6:35b-a3b` (evicts pinned). Hard RAM ceiling 24 GB.
- §20.6 sensors: none at launch; dormant `sensor_readings` schema built.
- §20.2 queue: hand-rolled Python + SQLite (lands Phase 3).
- Sealing on bare macOS: in-process guard now; OS-level pf/netns hardening documented in runbook for before any networked phase.

**Next (Phase 1 — Stores & ingest):** LanceDB + Logseq ingestion + ingest analyzer + telemetry. Needs §20.8 (vault path + in-scope graphs) and an embedding-model pick. Pull `qwen3.5:9b` when foreground RAG (Phase 2) needs it.

## Design notes (forward-looking, not yet implemented)

- [skills-and-scope](design-notes/skills-and-scope.md) — how "skills" attach to roles: instructional (context) vs executable (context + scoped tool); capability flows only from the §10 scope ceiling, checked independently of skill membership. Honor when roles + factory land (Phases 3–5).
- [observed-data-and-the-assistant-tier](design-notes/observed-data-and-the-assistant-tier.md) — firewall the owner's *authored* corpus (the mirror) from third-party *observed* exhaust (the assistant) as separate provenance pools; observed never feeds the mirror or behavioral baselines; assistant capabilities are gated executable skills (see skills-and-scope); multi-node offload deferred to Phase 3. Honor when airlock/assistant/provenance-classes land (Phases 3+). **Reconciliation flags in this session's notes below.**
## Phase 1 — Stores & ingest (COMPLETE, 2026-06-25)
**Gate to verify:** notes indexed; semantic search sane; dedup works.

**Built (increment 1 — deterministic write path; no vault path or embedding model needed)**
- `core/provenance.py`: `Provenance{AUTHORED, INTERPRETED, OBSERVED(reserved)}` + `MIRROR_READABLE = {AUTHORED}` — the authored/observed firewall as a first-class type (honors the observed-data design note before its tier exists).
- `core/stores/rawstore.py`: content-addressed immutable raw store (sha256 → verbatim blob; dedup for free; atomic write-then-rename; never overwrites). "Raw is sacred" (§8).
- `core/ingest/logseq.py`: Logseq parser (title incl. `___`→`/` namespaces, `#tag`/`#[[tag]]`, `[[links]]`, `key:: value` props) + `iter_vault` with pattern + excluded-dirs (the §20.8 scoping knob).
- `core/ingest/chunk.py`: deterministic block-aware chunker (hard-splits oversized blocks; char-budget + overlap; token-aware sizing deferred).
- `core/ingest/pipeline.py`: `ingest_vault/ingest_note` → `IngestRecord` (digest, title, provenance=AUTHORED, tags, links, chunks, is_new). Stops at "records ready to embed".

**Verified:** `ruff` clean; `pytest -m "not live"` 30/30 (8 new: dedup, immutability, parse/explicit-layer, vault scoping, chunk coverage, pipeline dedup+AUTHORED, mirror firewall).

**Built (increment 2)**
- `core/ingest/embed.py` (`Embedder`): Ollama `/api/embed`; query-instruction wrapping (Qwen3-Embedding is instruction-aware on the query side); `OllamaClient.embed()`.
- `core/stores/vectorstore.py`: LanceDB store, provenance-aware schema, cosine search with **prefiltered provenance** (`search(..., provenances={AUTHORED})` = the mirror firewall, structural), dim guard, `reset()` for rebuilds.
- `core/ingest/index.py`: `index_records` (per-digest dedup) + `semantic_search` (defaults to MIRROR_READABLE = authored only).
- `core/ingest/run.py` + `scripts/ingest.py`: sealed, rebuild-from-raw ingest entry (the Phase 3 scheduler will drive it).
- Config: `[vault]` (path `~/.mind-palace/vault`, pattern), `[embedding]` (model/dim/query_instruction), `paths.raw_store`/`vector_store`; loader types added. `lancedb` dep added.

**Verified (gate met):** `ruff` clean; `pytest` 35/35 (2 live). Live: semantic search ranks the relevant note first (Anxiety > Cooking/Cycling for a panic/sleeplessness query) — *search sane*. Real sealed ingest of the initialized vault → `notes=1 new_raw=1 chunks_indexed=1 vector_rows=1`; query returns it (authored). Dedup verified (raw-store tests + is_new). Provenance firewall verified (observed excluded from an authored-only search).

**Decisions**
- Embedding model (owner chose higher quality): **`qwen3-embedding:4b`** (~2.5 GB, **2560-dim**, instruction-aware). Dim read from config so re-embedding from raw (§8) is a config change.
- §20.8 source: Apple Notes is proprietary sqlite (needs an authorized export, not direct ingest); the Obsidian vault had 1 note; ~/Documents `.md` are uncurated. → initialized a new authored vault at `~/.mind-palace/vault` (owner's stated fallback), seeded with a Welcome note.

**Corpus ingested (2026-06-25):** owner provided `~/notes_export` (116 `.md` + 2 extensionless notes across `poem_archive/`, `work_notes_archive/`, `misc/`; 1 jpeg + 1 pdf attachment skipped). Copied **non-destructively** into `~/.mind-palace/vault` (originals retained); ingested **118 notes → 117 unique (1 dedup) → 914 chunks/vectors**. Real-corpus search sane: "personal musing"→poem_archive, "work performance review"→work_notes_archive. Robustness fixes landed: tolerant decode (utf-8→cp1252→replace) for the derived text, and the raw store now stores **verbatim original bytes** (true §8 "raw is sacred", was re-encoding decoded text). All authored content currently feeds the mirror; a future "reflective vs operational" sub-distinction within `authored` (e.g. keep todo lists out of dreaming) is a Phase 7 consideration, not the observed firewall.

**Next (Phase 2 — Librarian + golden set + behavioral check):** core RAG agent over the thought-graph, the frozen golden set + deterministic metrics, and the Constitution pre-return check (replacing the `self_evaluate` stub). Needs the vault populated for a meaningful golden set; pull `qwen3.5:9b` (routine/RAG tier) when starting.

### Reconciliation — observed-data design note vs what's built (asked 2026-06-25)
- **Consistent.** Note builds on skills-and-scope (assistant capabilities = gated executable skills); the §8 explicit/interpreted layers + the new `observed` class fit the provenance type added this increment. The dormant `sensor_readings` table (Phase 0) is the right home for sensor data, which the note classes as `observed` → reinforces keeping it out of the mirror.
- **Carry-forward (no conflict, sequencing):** note says "nothing changes Phases 0–2", but provenance extends §8 (Phase 1). Resolved by building provenance as an *extensible* type now (authored/interpreted live; observed reserved); the firewall *enforcement* (observed quarantine, provenance-filtered reads) lands with the assistant tier (Phase 3+). LanceDB schema (increment 2) must carry `provenance` + support provenance-filtered search so the mirror=authored-only firewall is structurally expressible from day one.
- **Genuine conflict to resolve before it lands — multi-node offload vs Invariant 1.** The note calls a second worker node "no rearchitecture", but the Phase 0 egress guard permits loopback only, and sending corpus-bearing synthesis jobs to another machine is the **private corpus crossing a network hop** — an airlock concern, not just a guard-config tweak. When multi-node lands (Phase 3+) it must be a *deliberate* extension of the sealed boundary to a second sealed peer (private link e.g. Tailscale, no internet egress, explicitly allowlisted in `core.sealing`) or routed via edge — never silently. Flagged so "no rearchitecture" doesn't paper over the invariant.

## Phase 2 — Librarian + golden set + behavioral check (COMPLETE, 2026-06-25)
**Gate to verify:** golden-set queries pass; metrics computed; the behavioral check fires.

**Built**
- `core/selfcheck.py`: the Constitution pre-return check (§4/§IV, §15), replacing the Phase 0 `self_evaluate` stub. Two honest layers — (a) **deterministic grounding** (always-on): every `[[cited]]` note must resolve to a source that was actually retrieved ("a cited identifier that does not resolve is a failure", §III.1); (b) a **judge seam** for the subjective directives (mirror-not-oracle, calibrated-certainty, consequential-deference) reported as `deferred` until the small-model judge + baseline-snapshot machinery lands (Phase 10) — *not* faked with brittle keyword scoring (spec is explicit: never scored cold). `passed` iff no FAIL findings.
- `core/agent.py`: now delegates to `core.selfcheck` (re-exports `SelfCheck`/`Finding`/`self_evaluate`); generic agents pass `sources=None` (grounding N/A).
- `core/constitution.py`: `frame_context()` gained `context_blocks=` — retrieved RAG grounding injected after the role, before history (the §13 priority order), query last. Back-compatible (Phase 0 tests unchanged).
- `core/librarian/`: the **Librarian** RAG agent (§9). Retrieves over the AUTHORED **mirror** by default (`MIRROR_READABLE` — observed firewall, structural), frames Constitution-outermost with the retrieved notes as the only citable evidence (mirror-not-oracle role prompt), runs on the `routine` tier (qwen3.5:9b), and self-checks grounding before returning. `LibrarianAnswer{text, sources, check}`. De-identified research-criteria seam (§16) noted, deferred to Phase 8.
- `eval/`: the **frozen golden set** (Invariant 9). `metrics.py` (deterministic recall@k, Jaccard set overlap, mean cosine distance); `golden.py` (model-decoupled harness via a `Retriever` callable + `regressions()` gate vs the blessed baseline); `golden/corpus/` = **synthetic fixture notes** (committable, privacy-safe — deliberately NOT the owner's live vault, which is private and changes); `golden_set.json` (5 blessed queries) + `baseline.json` (blessed metrics) + `README.md` (frozen-anchor, owner-only edits).
- `scripts/eval.py`: seals, ingests the fixture corpus into a throwaway store, scores the golden set; `--bless` re-writes the baseline (owner-only, Invariant 9).

**Verified (gate met):** `ruff` clean; `pytest` **54/54** (50 logic + 4 live).
- *golden-set queries pass* — `test_golden_live`: every blessed query retrieves its expected note at **rank 1** (recall@k=1.0), no regression vs the frozen baseline (recall 1.0 / overlap 0.333 / mean_dist 0.617).
- *metrics computed* — `test_metrics`: recall@k / overlap / cosine-distance math + harness aggregation + regression detection, deterministic (stub retriever).
- *behavioral check fires* — `test_selfcheck`: grounding passes a grounded answer, **flags a fabricated citation** (FAIL), defers subjective dims without a judge, and the judge seam fires and can fail. Wired into `Librarian.answer` + `Agent.respond`.
- *Librarian end to end* — `test_librarian_live`: real embedder + qwen3.5:9b over the fixture corpus → right note retrieved first, grounded answer, no fabricated citations.

**Decisions**
- **Behavioral check is honest, not theatrical.** Only the deterministic grounding check ships as authoritative now; the subjective directives are `deferred` (needs judge + frozen baseline, Phase 10/§15) rather than approximated by regex. This respects §4's "small-model judge … A/B'd against a baseline, never scored cold."
- **Golden set ships its own synthetic corpus**, not the live vault — a frozen anchor must be reproducible and human-blessed (Invariant 9) and must not leak private notes into git. The harness is model-decoupled so the same code path is unit-tested cold and run live.
- Librarian retrieval defaults to `MIRROR_READABLE` (authored-only); widening to other provenance classes is the assistant tier's call (Phase 3+), structurally expressible via the existing provenance prefilter.

**Next (Phase 3 — Scheduler + tiers + two-slot + context budget):** durable SQLite job table, supervisor loop, tier grouping + swap minimization, foreground check, preemption, pinned router/watchdog, and the deterministic context budgeter (token counting, priority assembly, history compaction, overflow→escalate). The §13 budgeter consumes `frame_context`'s priority order; telemetry already has a home for per-job usage tracking.

<!-- Append new phase entries below as you complete each one. -->
