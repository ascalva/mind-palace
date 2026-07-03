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
- [observed-data-and-the-assistant-tier](design-notes/observed-data-and-the-assistant-tier.md) — firewall the owner's _authored_ corpus (the mirror) from third-party _observed_ exhaust (the assistant) as separate provenance pools; observed never feeds the mirror or behavioral baselines; assistant capabilities are gated executable skills (see skills-and-scope); multi-node offload deferred to Phase 3. Honor when airlock/assistant/provenance-classes land (Phases 3+). **Reconciliation flags in this session's notes below.**
- [roadmap-and-future-directions](design-notes/roadmap-and-future-directions.md) — post-Phase-10 roadmap (NOT committed spec; does not change Phases 0–10): provenance spectrum, inbound distillation gate, new sources/sensors/multimodal, process/concurrency model, OS-agent health, self-audit, dashboards/drift gauge, security posture. Two items flagged **[affects current build]** — reconciled below: honor §7 (concurrency) in Phase 3; §1 (provenance spectrum) is the growth path for the Phase-1 `Provenance` type.
- [alignment-subsystem](design-notes/alignment-subsystem.md) — alignment as a measurable subsystem: fixed seed (authored+Constitution+golden) vs regenerable layer (dreams/structure/params); detection (drift gauge + min-cut-to-authored + community/echo-chamber metrics), gated surgery (prune bubbles, interpreted-only), reset-from-raw; Phase-10 expansion = modifiable params + alignment-steering self-mod. Honor at Phase 10.
- [dreaming-on-curated-graphs](design-notes/dreaming-on-curated-graphs.md) — dream R&D **R5** (flag OFF): run the interpreter panel on a curated corpus (a book) in its OWN graph (never the authored mirror — curated ∉ MIRROR_READABLE), then cross-graph **resonance** between curated and authored theme-centroids (interpreted-only). Build after R0/R1.
- [vault-sync-and-capture](design-notes/vault-sync-and-capture.md) — **near-term, buildable now**: local vault watcher (filesystem-only, no egress) auto-re-ingests changed notes (idempotent via content-addressing), provenance authored-solo; Syncthing-over-Tailscale for private peer-to-peer sync (iCloud/Obsidian Sync transit a vendor — flagged); Tailscale to reach the interface gateway for chat-capture (authored-dialogue) + queries.
- [nervous-system-and-ambassador](design-notes/nervous-system-and-ambassador.md) — tamper response (graduated/provenance-aware, NOT a single kill switch: regenerable breach→quarantine+reset-from-raw, fixed-layer breach→fail-closed freeze; "recovery mode" = a launch flag; honest caveat that watcher+watched share a machine, seed-immutability is the real guarantee); verification latency tiers (inline cheap signature/scope check at privileged gates ONLY; async auditor agent — separate, read-only, trough-scheduled — for deep chain-walks; findings feed the tripwire); the Ambassador (conversational front door: read-only MirrorView + NEW operational-introspection scope over attestations/ledger/metrics, delegates-not-acts, conversations are authored-dialogue, narrates system state; white papers as a curated system-self-knowledge graph). Honor at Phase 11 + text-interaction activation.
- [ambassador-interpretation-and-flow](design-notes/ambassador-interpretation-and-flow.md) — refines the Ambassador (nervous-system note §4): interpretation splits into retrieval-time (safe — narrating already-grounded/attested conclusions, downstream of all grounding) vs intent interpretation (the only consequential kind — gated as a proposed task, never acted on; blast radius = a wrong query, not a corrupted mirror). Not a bottleneck because it's a thin dispatcher on the always-warm pinned tier (qwen3.5:2b) that delegates all heavy work to the async scheduler; real risk is context over-assembly, bounded by the §13 budgeter (selective per-turn retrieval). "Wide window, narrow hands, thin body." Honor at Phase 11 / text-interaction.

### Reconciliation — roadmap design note (asked 2026-06-25)

- **Consistent** with what's built and both other design notes. The multi-node item explicitly preserves the Phase-1 "corpus crosses a network hop" flag; §11 security (keys from a sealed core via Keychain/Secure-Enclave or an edge-side broker, _never_ KMS from the core) matches Invariant 1 + the `get_secret` env/Keychain-only seam; §10 drift gauge consumes exactly the golden-set + Constitution-conformance anchors built in Phase 2; §4 sensors land in the dormant `sensor_readings` table (Phase 0). No genuine conflicts.
- **§7 process/concurrency [affects Phase 3] — a clarification to honor, not a conflict.** Refines BUILD-SPEC §13's "reactive escalations preempt batch work": preemption is **cooperative, at job boundaries** — the escalation is dispatched _next_, never interrupting an in-flight generation (you can't cleanly preempt mid-generation; model-load is the dominant cost). Phase 3 therefore: one supervisor owns the SQLite queue (WAL, single-writer); agents are in-process tasks (context re-composed per invocation), not OS processes; the execution unit is run-to-completion or checkpointed-step, not a time quantum. Rules-first scheduling with the router model as an _enhancement_ + a fall-back-to-rules path (also §8) — matches §13's "start with rules."
- **§1 provenance spectrum [affects current build] — Phase-1 type is forward-compatible; no change now.** Today's `Provenance{AUTHORED, INTERPRETED, OBSERVED}` + the `MIRROR_READABLE` frozenset already realize §1's rule shape ("a query declares which classes it may read; the mirror declares the authored classes"): retrieval read-scope is a _passed frozenset_ (Librarian default `MIRROR_READABLE`), not a hardcoded binary. Growth path when those sources land: `AUTHORED` splits into `authored-solo` + `authored-dialogue` and adds `curated`; the existing single `authored` tag maps to **`authored-solo`** by default (conservative) via a deliberate human re-tag-from-raw (§8), never automatic (matches §1's "promotion is a deliberate human act"). Phase 3 carries provenance read-scope _through_ the job/agent abstraction rather than assuming authored-only, keeping the seam open.

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

**Verified (gate met):** `ruff` clean; `pytest` 35/35 (2 live). Live: semantic search ranks the relevant note first (Anxiety > Cooking/Cycling for a panic/sleeplessness query) — _search sane_. Real sealed ingest of the initialized vault → `notes=1 new_raw=1 chunks_indexed=1 vector_rows=1`; query returns it (authored). Dedup verified (raw-store tests + is_new). Provenance firewall verified (observed excluded from an authored-only search).

**Decisions**

- Embedding model (owner chose higher quality): **`qwen3-embedding:4b`** (~2.5 GB, **2560-dim**, instruction-aware). Dim read from config so re-embedding from raw (§8) is a config change.
- §20.8 source: Apple Notes is proprietary sqlite (needs an authorized export, not direct ingest); the Obsidian vault had 1 note; ~/Documents `.md` are uncurated. → initialized a new authored vault at `~/.mind-palace/vault` (owner's stated fallback), seeded with a Welcome note.

**Corpus ingested (2026-06-25):** owner provided `~/notes_export` (116 `.md` + 2 extensionless notes across `poem_archive/`, `work_notes_archive/`, `misc/`; 1 jpeg + 1 pdf attachment skipped). Copied **non-destructively** into `~/.mind-palace/vault` (originals retained); ingested **118 notes → 117 unique (1 dedup) → 914 chunks/vectors**. Real-corpus search sane: "personal musing"→poem_archive, "work performance review"→work_notes_archive. Robustness fixes landed: tolerant decode (utf-8→cp1252→replace) for the derived text, and the raw store now stores **verbatim original bytes** (true §8 "raw is sacred", was re-encoding decoded text). All authored content currently feeds the mirror; a future "reflective vs operational" sub-distinction within `authored` (e.g. keep todo lists out of dreaming) is a Phase 7 consideration, not the observed firewall.

**Next (Phase 2 — Librarian + golden set + behavioral check):** core RAG agent over the thought-graph, the frozen golden set + deterministic metrics, and the Constitution pre-return check (replacing the `self_evaluate` stub). Needs the vault populated for a meaningful golden set; pull `qwen3.5:9b` (routine/RAG tier) when starting.

### Reconciliation — observed-data design note vs what's built (asked 2026-06-25)

- **Consistent.** Note builds on skills-and-scope (assistant capabilities = gated executable skills); the §8 explicit/interpreted layers + the new `observed` class fit the provenance type added this increment. The dormant `sensor_readings` table (Phase 0) is the right home for sensor data, which the note classes as `observed` → reinforces keeping it out of the mirror.
- **Carry-forward (no conflict, sequencing):** note says "nothing changes Phases 0–2", but provenance extends §8 (Phase 1). Resolved by building provenance as an _extensible_ type now (authored/interpreted live; observed reserved); the firewall _enforcement_ (observed quarantine, provenance-filtered reads) lands with the assistant tier (Phase 3+). LanceDB schema (increment 2) must carry `provenance` + support provenance-filtered search so the mirror=authored-only firewall is structurally expressible from day one.
- **Genuine conflict to resolve before it lands — multi-node offload vs Invariant 1.** The note calls a second worker node "no rearchitecture", but the Phase 0 egress guard permits loopback only, and sending corpus-bearing synthesis jobs to another machine is the **private corpus crossing a network hop** — an airlock concern, not just a guard-config tweak. When multi-node lands (Phase 3+) it must be a _deliberate_ extension of the sealed boundary to a second sealed peer (private link e.g. Tailscale, no internet egress, explicitly allowlisted in `core.sealing`) or routed via edge — never silently. Flagged so "no rearchitecture" doesn't paper over the invariant.

## Phase 2 — Librarian + golden set + behavioral check (COMPLETE, 2026-06-25)

**Gate to verify:** golden-set queries pass; metrics computed; the behavioral check fires.

**Built**

- `core/selfcheck.py`: the Constitution pre-return check (§4/§IV, §15), replacing the Phase 0 `self_evaluate` stub. Two honest layers — (a) **deterministic grounding** (always-on): every `[[cited]]` note must resolve to a source that was actually retrieved ("a cited identifier that does not resolve is a failure", §III.1); (b) a **judge seam** for the subjective directives (mirror-not-oracle, calibrated-certainty, consequential-deference) reported as `deferred` until the small-model judge + baseline-snapshot machinery lands (Phase 10) — _not_ faked with brittle keyword scoring (spec is explicit: never scored cold). `passed` iff no FAIL findings.
- `core/agent.py`: now delegates to `core.selfcheck` (re-exports `SelfCheck`/`Finding`/`self_evaluate`); generic agents pass `sources=None` (grounding N/A).
- `core/constitution.py`: `frame_context()` gained `context_blocks=` — retrieved RAG grounding injected after the role, before history (the §13 priority order), query last. Back-compatible (Phase 0 tests unchanged).
- `core/librarian/`: the **Librarian** RAG agent (§9). Retrieves over the AUTHORED **mirror** by default (`MIRROR_READABLE` — observed firewall, structural), frames Constitution-outermost with the retrieved notes as the only citable evidence (mirror-not-oracle role prompt), runs on the `routine` tier (qwen3.5:9b), and self-checks grounding before returning. `LibrarianAnswer{text, sources, check}`. De-identified research-criteria seam (§16) noted, deferred to Phase 8.
- `eval/`: the **frozen golden set** (Invariant 9). `metrics.py` (deterministic recall@k, Jaccard set overlap, mean cosine distance); `golden.py` (model-decoupled harness via a `Retriever` callable + `regressions()` gate vs the blessed baseline); `golden/corpus/` = **synthetic fixture notes** (committable, privacy-safe — deliberately NOT the owner's live vault, which is private and changes); `golden_set.json` (5 blessed queries) + `baseline.json` (blessed metrics) + `README.md` (frozen-anchor, owner-only edits).
- `scripts/eval.py`: seals, ingests the fixture corpus into a throwaway store, scores the golden set; `--bless` re-writes the baseline (owner-only, Invariant 9).

**Verified (gate met):** `ruff` clean; `pytest` **54/54** (50 logic + 4 live).

- _golden-set queries pass_ — `test_golden_live`: every blessed query retrieves its expected note at **rank 1** (recall@k=1.0), no regression vs the frozen baseline (recall 1.0 / overlap 0.333 / mean_dist 0.617).
- _metrics computed_ — `test_metrics`: recall@k / overlap / cosine-distance math + harness aggregation + regression detection, deterministic (stub retriever).
- _behavioral check fires_ — `test_selfcheck`: grounding passes a grounded answer, **flags a fabricated citation** (FAIL), defers subjective dims without a judge, and the judge seam fires and can fail. Wired into `Librarian.answer` + `Agent.respond`.
- _Librarian end to end_ — `test_librarian_live`: real embedder + qwen3.5:9b over the fixture corpus → right note retrieved first, grounded answer, no fabricated citations.

**Decisions**

- **Behavioral check is honest, not theatrical.** Only the deterministic grounding check ships as authoritative now; the subjective directives are `deferred` (needs judge + frozen baseline, Phase 10/§15) rather than approximated by regex. This respects §4's "small-model judge … A/B'd against a baseline, never scored cold."
- **Golden set ships its own synthetic corpus**, not the live vault — a frozen anchor must be reproducible and human-blessed (Invariant 9) and must not leak private notes into git. The harness is model-decoupled so the same code path is unit-tested cold and run live.
- Librarian retrieval defaults to `MIRROR_READABLE` (authored-only); widening to other provenance classes is the assistant tier's call (Phase 3+), structurally expressible via the existing provenance prefilter.

**Next (Phase 3 — Scheduler + tiers + two-slot + context budget):** durable SQLite job table, supervisor loop, tier grouping + swap minimization, foreground check, preemption, pinned router/watchdog, and the deterministic context budgeter (token counting, priority assembly, history compaction, overflow→escalate). The §13 budgeter consumes `frame_context`'s priority order; telemetry already has a home for per-job usage tracking.

## Phase 3 — Scheduler + tiers + two-slot + context budget (COMPLETE, 2026-06-25)

**Gate to verify:** jobs scheduled by tier; swaps minimized; foreground check blocks heavy jobs; ceiling enforced; contexts always fit the active model's window and usage is tracked.

**Built (all in `scheduler/`)**

- `queue.py`: durable SQLite job table (**WAL, single-writer** — the one safe serialization point, roadmap §7). `Job` + states (queued/running/done/failed/deferred), priorities (reactive/interactive/default/background), `num_ctx` window for batching. `claim()` is the §13 policy: highest priority first, **swap-avoidance** within the top band (prefer the job whose `(tier, window)` is already loaded), FIFO tiebreak, skipping `blocked_tiers` (the foreground gate) which stay QUEUED. `defer/revive_deferred` (ceiling), `checkpoint` (re-queues a long job to yield at the next boundary — cooperative steps, roadmap §7), `depth/counts`.
- `budget.py`: the **deterministic context budgeter** (§13) — tokenizer estimate + priority assembly (Constitution → role → RAG → history → tool → task) with the trim ladder **retrieval → history → tool outputs → escalate**. Constitution/role/task never trimmed (Invariant 6); when even the mandatory frame won't fit it flags `escalate` (route to a larger window) rather than dropping the Constitution. `suggest_num_ctx()` = p95 + headroom (the per-role window safe-lever basis, §14). Pluggable estimator seam for a real tokenizer.
- `presence.py`: foreground check via macOS HID idle time (`ioreg`), injectable probe, **fail-safe** (assume present when idle is unknown — never run heavy work blind).
- `router.py`: **rules-first** router (kind → tier/window/priority from the lineup) + `Watchdog` (reads vitals, raises threshold flags → high-priority jobs). Roadmap §8: the router model is an enhancement, not an SPOF; deterministic rules are the floor.
- `supervisor.py`: the loop — claim → make `(tier, window)` resident via the two-slot loader (refuses ceiling-breaching loads → **defer**, Invariant 8) → run the handler to completion (or one checkpointed step) → record vitals. Counts **worker** swaps only (the pinned router does interstitial work without evicting the worker, roadmap §7). Cooperative, **job-boundary** preemption; a handler crash fails its job, never the loop.
- Telemetry: schema v2 adds `context_usage` (per-agent/job budget outcomes — §13 visibility for window right-sizing); `record_context_usage` (duck-typed report so telemetry stays independent of the scheduler) + reader count. `vitals` gains `queue.depth` / `model.load_seconds` from the supervisor.

**Verified (gate met):** `ruff` clean; `pytest` **80/80** (75 logic + 5 live).

- _scheduled by tier / swaps minimized_ — `test_supervisor::test_groups_same_tier_to_minimize_swaps` (two routine jobs run back-to-back, one swap to synthesis); `test_queue` priority + swap-avoidance; `test_router` kind→tier/window/priority.
- _foreground blocks heavy jobs_ — `test_supervisor::test_foreground_gates_heavy_tiers` (synthesis stays QUEUED while present; routine runs).
- _ceiling enforced_ — `test_supervisor::test_ceiling_breach_defers_job` (real loader, 5 GB budget → synthesis deferred, not crashed).
- _contexts fit + usage tracked_ — `test_budget` (fits/trim-ladder/escalate, never drops the mandatory frame); `test_budget::test_context_usage_is_recorded` (DuckDB round-trip).
- _resilience / cooperative yielding_ — handler-exception isolation + checkpoint-resume tests; live `test_scheduler_live` dispatches a real job through the loader + Ollama end to end.

**Decisions / reconciliations honored**

- **Cooperative, job-boundary preemption (roadmap §7).** No mid-generation interrupt; reactive escalations are high-priority jobs dispatched next. Worker-swap counting ignores the pinned router (interstitial). One supervisor owns the WAL queue (single-writer).
- **Rules-first (roadmap §8, §13).** The router/watchdog are deterministic; the tiny model is a later enhancement with a fall-back-to-rules path.
- **Provenance read-scope (roadmap §1) stays open.** Jobs carry tier/window/kind; provenance read-scope rides on the agent/handler (Librarian still defaults `MIRROR_READABLE`), not assumed authored-only — the spectrum's growth path is unobstructed.
- `num_ctx` is treated as a per-role **load-time** window (changing it reloads, §13); same-window jobs batch with same-tier ones via `Job.load_key`.

**Next (Phase 4 — Sandboxed code execution):** rootless Podman execution broker (network-off, no-mount, dropped caps, seccomp, limits + wall-clock), warm pool, optional WASM path; executed code returns data, never actions (Invariant 4). No new models needed.

## Phase 4 — Sandboxed code execution (COMPLETE, 2026-06-25)

**Gate to verify:** code runs isolated — no network, no creds, no vault; limits + timeout enforced; warm pool works.

**Built (all in `core/sandbox/`)**

- `spec.py`: `ExecSpec` (code, language, timeout, `Limits`, `Network`, non-secret env) + `ExecResult` (stdout/stderr/exit/timed_out/duration/truncated). Output capped to 64 KiB so a result can't blow the context budget (§13). Validation (non-empty code, bounded timeout). Code returns **data, never actions** (Invariant 4).
- `policy.py`: the isolation profile **built into the podman argv as pure functions** — `--network=none`, `--read-only`, scratch `--tmpfs /tmp`, `--cap-drop=ALL`, `no-new-privileges`, non-root `--user 65534`, `--memory`/`--memory-swap`/`--cpus`/`--pids-limit`, default seccomp (never `unconfined`), and **zero `-v`/`--mount`** so the vault (the whole host FS) is structurally unreachable. Code is delivered on **stdin** to the interpreter, so no bind mount is ever needed. Per-language `RUNTIMES`; `build_warm_argv` for idle pool containers. A network request raises (grants are a deliberate, logged later extension).
- `runner.py`: `SandboxRunner` protocol; `PodmanRunner` (ephemeral `podman run` + warm `exec`/`reset`/`destroy`; wall-clock timeout via subprocess, force-removes an overrun container; `available()` probes the Podman service, not just the binary); `WasmRunner` seam (wasmtime+Pyodide pure-compute path, §11 — declared, not built).
- `pool.py`: `WarmPool` — lazy warming, reuse, **pool size = concurrency cap** (Invariant 8), reset-on-healthy, **discard-on-timeout** (never reuse a wedged container), prewarm/shutdown.
- `broker.py`: `ExecutionBroker.run(spec) -> ExecResult` — pool routing (ephemeral fallback for non-pooled languages), concurrency-cap guard, and **logs every execution** (language/network/timeout) to telemetry so any future network grant is auditable (§11). `build_broker(config)` wires it from `[sandbox]` config.
- Config: `[sandbox]` section + `SandboxConfig` (runtime, image, timeout, memory/cpus/pids, max_concurrency, warm_pool_size).

**Verified (gate met by construction + fakes; empirical tests gated):** `ruff` clean; `pytest` **98 passed (93 logic + 5 live), 5 podman skipped**.

- _isolated — no network/creds/vault_ — `test_sandbox_policy` asserts the full isolation set on the argv and that **nothing is mounted** (vault unreachable) and seccomp is never disabled.
- _limits + timeout_ — limits in argv; `test_sandbox_broker::test_timeout_result_discards_the_container` (timed-out container discarded); broker concurrency cap + per-exec logging.
- _warm pool works_ — `test_sandbox_pool` (lazy warm, reuse, cap, discard-unhealthy, prewarm/shutdown); `test_build_broker_wires_from_config`.
- _empirical isolation_ — `test_sandbox_podman_live` (`-m podman`): runs real containers and checks network-off, vault-absent, non-root, and timeout. **Skipped here because the Podman machine isn't running on this host** (`podman` is on PATH but `podman info` fails). To validate empirically: `podman machine start` (or install Podman), then `pytest -m podman`.

**Decisions**

- **Code via stdin, zero host mounts** — the strongest no-vault posture (nothing to escape to), and it makes the "no vault" property structural, not a path-blocklist.
- **Pool size == concurrency cap** — one knob honors the RAM ceiling (Invariant 8); the supervisor is single-worker so 1 is the default.
- **Network = none only; grants are a logged seam** — honors "no network unless an explicit scoped grant, logged" without shipping ungated network plumbing.
- **WASM path is a declared seam** (§11 calls it optional) — Podman is the real substrate; gVisor/Firecracker remain the documented hardening upgrade.
- Shelling out to `podman` is deterministic **code acting** (Invariant 3); the executed code stays powerless (Invariant 4). The sealed core opens no socket; the container has no network.

**⚠️ Podman runtime — empirical verification still pending (2026-06-25).** Attempted to bring up a podman machine to run `-m podman`: **libkrun/krunkit 1.2.2 + podman 6.0** boots the guest into emergency mode (virtio-fs mount failure → no SSH); **applehv** booted cleanly the first time (smoke test passed) but the re-created machine wedged (`vfkit exited unexpectedly`). Cleaned up to idle; `~/.config/containers/containers.conf` left at `provider=applehv`, small sizing. The Phase 4 logic gate stands (isolation is asserted by construction + fake-runner tests, all green); only the empirical `-m podman` run is outstanding. **Full diagnosis + come-back steps + Docker (rootful) fallback are in `docs/runbook.md` → "Sandbox runtime — Podman machine".** Owner okayed proceeding on the by-construction tests for now.

**Next (Phase 5 — Dynamic agent factory + base role library):** mint agents from templates (Constitution inheritance, **scope ceiling**, ephemeral/persist, self-evaluation, privileged-request routing to the gate). Honors the [skills-and-scope] design note (capability flows only from the scope ceiling, checked independently of skill membership) and gives the sandbox broker its first caller (the coder/analyst roles). No new models needed.

## Phase 5 — Dynamic agent factory + base role library + scope ceiling (COMPLETE, 2026-06-25)

**Gate to verify:** minting works; a generated agent cannot exceed scope; inherits the Constitution; self-evaluates; privileged tasks route to the human.

**Built (`core/factory/` + `ops/gate.py`), honoring [skills-and-scope]**

- `roles.py`: `RoleTemplate` (prompt_fragment, default_tier, **scope** = tool-id ceiling, skills) + the **base role library** (§9): personal_assistant, coder, data_analyst, financial_advisor, health_research_advisor, writer_editor, general_conversation. `PRE_DECLARED_MAX = {run_python}` — the absolute §10 ceiling; **no shell/credential/network tool exists**, so the factory is structurally incapable of minting one. A template whose scope exceeds MAX is rejected at definition.
- `tools.py`: capability as **object-capability handles** (the telemetry store-layer precedent). `ToolRegistry` (tools registered independently of roles), `ToolDispatcher` that **holds only the in-scope handles** — an out-of-scope id is _unreachable_ (`ToolNotInScopeError`), not "checked then refused". `run_python` runs through the Phase-4 sandbox broker (powerless, returns data); registered only if a broker is supplied.
- `factory.py`: `AgentFactory.mint(role)` composes Constitution → role → task (Invariant 6), resolves **scope = role.scope ∩ MAX**, binds a dispatcher of only those handles, returns an ephemeral `MintedAgent` (or persists it). `requested_tools` beyond the resolved scope → **routed to the human gate**, never minted. `MintedAgent` keeps the **advisory path (`respond`, self-evaluates) separate from the action path (`invoke`, dispatcher)** — model advises, code acts (Invariant 3). Out-of-scope `invoke` → gate + refuse.
- `registry.py`: SQLite `AgentRegistry` — promote an ephemeral agent to a persistent named one (§8/§10).
- `ops/gate.py`: `HumanGate` seam — records beyond-scope/privileged requests as PENDING (nothing privileged unattended, Invariant 5). The full propose→approve→execute→validate→rollback ledger is Phase 10; this is its inbox.

**Verified (gate met):** `ruff` clean; `pytest` **120 passed (114 logic + 6 live), 5 podman skipped**.

- _minting + Constitution inheritance_ — `test_factory_mint` (ctx[0] == Constitution; ephemeral default); live `test_factory_live` mints general_conversation and gets a grounded answer.
- _cannot exceed scope_ — scope resolves to role∩MAX; out-of-scope `invoke` raises + routes to gate; `requested_tools` beyond scope/MAX → `GateRequest`; template rejects beyond-MAX scope; object-capability dispatcher tests (`test_factory_tools`).
- _self-evaluates_ — `respond` returns a `SelfCheck` (the §4 pre-return check); live-verified.
- _privileged → human_ — `test_privileged_request_routes_to_gate`, `..._beyond_pre_declared_max...`, out-of-scope invoke → `HumanGate.pending()`.

**Decisions**

- **Two predicates, two subsystems, two times** (backdoor-proofing, per the design note): `loaded(skill)` at assembly vs `can_invoke(tool)` at dispatch; capability flows only from `role.scope ∩ MAX`, resolved at mint, enforced at dispatch, never widened by a skill. Instructional skills (context) are seeded later; the seam (`RoleTemplate.skills` + `frame_context` context_blocks) is in place.
- **No privileged tools exist at all** — the safest form of "can't mint privileged": the capability isn't representable. Beyond-scope needs go to the gate.
- The gate + agent registry are minimal seams; Phase 10 makes the gate the durable propose/approve/validate/rollback ledger.

**Next (Phase 6 — Interface layer, Zone B):** the interface gateway + the private local/Tailscale adapter (primary), optional WhatsApp adapter, relaying owner messages to the sealed core and back. First **Zone B** (networked) work — the egress guard is NOT installed there; core↔edge communicate by filesystem handoff, never imports (Invariant 2). No new models needed.

## Phase 6 — Interface layer (Zone B) (COMPLETE, 2026-06-25)

**Gate to verify:** messages round-trip; core never touches the messaging service directly; private default works.

**Built** — first **Zone B** (networked) work. The trust boundary is a **filesystem handoff, never an import** (Invariant 2): the gateway holds the network-facing adapter; the core holds the vault; they meet only at a handoff directory.

- `core/interface.py` (Zone A): `CoreInbox` — reads sanitized request JSON from `handoff/requests/`, dispatches to an injected handler (the librarian/factory), writes answer JSON to `handoff/responses/` (atomic write-then-rename), consumes the request. **No network, no adapter, no `import edge`** — the structural form of "network and private data never share a component". A handler error becomes an error response, never a crash. `build_core_inbox` wires the librarian as the default handler.
- `edge/interface/protocol.py`: `InboundMessage`/`OutboundMessage` + the on-disk wire format (mirrored, not imported, by the core).
- `edge/interface/adapter.py`: `InterfaceAdapter` Protocol + **`LocalAdapter`** (the private default — loopback/Tailscale, `transits_third_party=False`) + **`WhatsAppAdapter`** (opt-in stub, `transits_third_party=True`, Invariant 11).
- `edge/interface/channel.py`: `GatewayChannel` — the edge side of the handoff (submit request, poll/await response).
- `edge/interface/gateway.py`: `InterfaceGateway` — relays adapter ↔ core over the channel; **refuses third-party adapters unless `allow_third_party=True`** (Invariant 11 opt-in).
- Config: `[interface]` (`handoff_dir`, `default_adapter="local"`) + `InterfaceConfig`.

**Verified (gate met):** `ruff` clean; `pytest` **129 passed (123 logic + 6 live), 5 podman skipped**.

- _round-trip_ — `test_message_round_trips_gateway_to_core_to_gateway` (owner→LocalAdapter→handoff→CoreInbox→handoff→adapter reply).
- _core never touches messaging_ — `test_core_inbox_never_imports_the_messaging_side` (no `import edge`) + the core processes purely from disk + handler; the gateway holds the adapter.
- _private default works_ — `LocalAdapter` round-trips in-memory, `transits_third_party=False`, default adapter is `local`; third-party adapters refused unless opted in.

**Decisions**

- **Handoff = JSON files in a shared dir; the wire format is mirrored, not a shared import** — honors "core↔edge communicate by filesystem handoff, never imports" (CONVENTIONS). Atomic write-then-rename so neither side reads a partial file.
- **Adapters carry a `transits_third_party` flag**; the gateway makes the Invariant-11 tradeoff explicit and opt-in. WhatsApp is a declared stub (the live unofficial-lib/Cloud-API integration is deferred — §20.3/§20.4 owner decision).
- **The core handler is injectable** (librarian by default) so the inbox is model-agnostic and testable; the scheduler (Phase 3) can also drive `CoreInbox.process_once` as a job.

**Next (Phase 7 — Curator + dreaming):** background compaction (merge near-dupes, prune, flag contradictions) on the _interpreted_ layer + dreaming synthesis (cluster embeddings, track themes), cron/trough-only, never during foreground use (the Phase-3 foreground gate; `synthesis` is already in `HEAVY_TIERS`). _Mirror, not oracle_ (§4); never rewrite the explicit/authored layer (§8). **Phase 6b (voice/telephony)** is skipped per owner (optional, §20.11). Notes for the build: `numpy` 2.5 is available (transitive via lancedb — add it to pyproject deps if imported directly for clustering); the **synthesis-tier model `qwen3.6:27b` is NOT pulled** (only 2b/9b/embedding/35b-a3b are), so make the dream synthesizer injectable and gate any live synthesis test on the model (pull 27b only to exercise it). `VectorStore` will need an "all rows / by-provenance" read for clustering. Store interpreted artifacts (dreams, curation findings) in a new derived store, marked `INTERPRETED`, regenerable.

## Phase 7 — Curator + dreaming (COMPLETE, 2026-06-26)

**Gate to verify:** background compaction + dreaming synthesis; run on cron in troughs only; coherent output; never during foreground use.

**Built** — the §9 cognitive-tier agents, on the **INTERPRETED** layer (§8), trough-only.

- `core/stores/derived.py`: `DerivedStore` (SQLite) — the home for INTERPRETED artifacts (dreams + curator findings). **Writes `interpreted` provenance and nothing else**: `add()` has _no_ `provenance` parameter, so the derived layer cannot masquerade as authored ground truth (the §8 explicit/interpreted firewall, structural — like the telemetry write-only handle). Ids are content-derived → re-running a cron pass is **idempotent** (INSERT OR REPLACE), and `reset()` makes it **regenerable** from the immutable corpus.
- `core/stores/vectorstore.py`: added `all_rows(provenances=…)` — the by-provenance full scan the dreaming agent clusters over (`to_arrow().to_pylist()`, filtered in Python; single-user scale). The mirror passes `{AUTHORED}` so observed exhaust never seeds a dream.
- `core/dreaming/cluster.py`: **deterministic, model-free** clustering (NumPy only) — note centroids (chunk vectors averaged per digest), cosine **single-linkage connected components** over a threshold, near-duplicate pairs, and note snippets for grounding. The §9 principle in miniature: the heavy deterministic work runs in cheap code so the scarce inference slot is earned only for synthesis. Reproducible given input order.
- `core/dreaming/dreamer.py`: the **Dreamer** (§9) — clusters the AUTHORED mirror (`MIRROR_READABLE`, the firewall), frames each theme Constitution-first with the cluster's own notes as the only citable evidence (**mirror-not-oracle** role), runs the **injectable** synthesizer, and **self-checks grounding** (`core.selfcheck`) before storing the reflection as an INTERPRETED `dream`. Synthesizer is a `Callable[[messages], str]` seam so the module is testable without the (large, unpulled) 27B model.
- `core/curator/curator.py`: the **Curator** (§9) — **detects and flags; never rewrites authored ground truth** (§8). Reads the corpus; writes only INTERPRETED `finding`s: `near_duplicate` (authored merge _candidates_ — never auto-merged), `prune_candidate` (derived vector rows orphaned from the raw store = dead derived weight), and `contradiction` (a model JUDGMENT — an **injectable seam, deferred** until a detector is supplied, never faked, exactly like the §4 judge seam). Applying any merge/prune to authored content is the gated self-modification loop's job (Phase 10).
- `scheduler/cron.py`: wires `dream`/`curate` into the supervisor — both already route to the **synthesis** tier (`router._SYNTHESIS_KINDS`), which the Phase-3 foreground gate (`HEAVY_TIERS`) blocks while the owner is present. So trough-only + ceiling + swap discipline apply **for free**; this module just builds the handlers + enqueue helpers. Per-cluster checkpointing (the `queue.checkpoint` seam) noted as a future refinement.
- Config: `[dreaming]` (similarity/near-dup thresholds, min cluster size, max clusters) + `paths.derived_store`; `numpy>=1.26` added to runtime deps (was transitive via lancedb).

**Verified (gate met):** `ruff` clean; `pytest` **152 logic passed (+29 new), 6 live + 6 podman/synthesis-live skipped** (164 collected). Real wiring smoke-tested (`build_dreamer`/`build_curator` load config + stores without a model call; empty-corpus runs are graceful). Librarian live re-run green (no regression in shared paths).

- _dreaming synthesis_ — `test_dreamer`: clusters→themes; reads the AUTHORED mirror only; Constitution-first + grounded context; stored as INTERPRETED dreams; **fabricated citation flagged**. `test_cluster`: centroids/clustering/near-dup/determinism.
- _background compaction_ — `test_curator`: near-dup candidates flagged (not merged); orphaned derived rows flagged for prune; **contradiction deferred without a detector** (and fires when one is injected); findings persisted as INTERPRETED; near-dup scan reads the mirror only.
- _derived layer firewall_ — `test_derived_store`: INTERPRETED-only (no `provenance` param), idempotent content ids, regenerable `reset()`.
- _trough-only / never during foreground use_ — `test_cron`: dream+curate route to synthesis; **gated QUEUED while the owner is present, run in a trough** (reuses the Phase-3 foreground gate).
- _coherent output (live)_ — `test_dreaming_live` (`-m live`): real embedder + synthesis model over the fixture corpus → a theme synthesized, stored, grounding check fired. **Skipped here: `qwen3.6:27b` (synthesis tier) is not pulled** — `ollama pull` it to exercise. The deterministic structure + grounding are asserted cold in `test_dreamer`.

**Decisions / reconciliations honored**

- **Curator flags, never rewrites authored (§8).** "Merge near-duplicates / prune" is realized as _findings_ (candidates) on the interpreted layer; mutating authored content is a corpus change = self-modification → the Phase-10 gate. Only genuinely-derived dead weight (orphan vectors) is a prune candidate, and even that is flagged, not auto-deleted.
- **Mirror, not oracle (§4) end to end.** Dreaming reads `MIRROR_READABLE` (authored-only firewall — observed exhaust can never seed a dream, nor enter the §15 baselines), cites only the clustered notes, and runs the same grounding self-check the Librarian does.
- **Honest seams, not theater.** Contradiction detection (a subjective model judgment) is `deferred` without a detector — never approximated by keywords — mirroring the §4 judge seam. The synthesizer is injected so the deterministic path is fully tested without the 27B model.
- **Deterministic floor (§9).** Clustering/near-dup are NumPy-only and reproducible; the model is earned only for the per-theme synthesis (capped by `max_clusters`).
- **Trough-only is structural, not new code.** `dream`/`curate` were already synthesis-tier kinds in the router; the Phase-3 foreground gate + two-slot ceiling enforce "never during foreground use" without a second mechanism.

**Next (Phase 8 — The airlock, AWS Zone C):** Terraform for `requests/`+`results/` S3 prefixes + the least-privilege fetcher (Lambda/Fargate), the containerized **bridge** (Zone B), and the one-way research flow — sanitized de-identified criteria out, public literature in, ranked inside the walls. The Librarian already has the "emit de-identified research criteria" seam (§16) noted. First **Zone C** work; needs §20.7 (AWS account/region/TF state) and §20.9 (Lambda vs Fargate) from the owner. The egress guard stays installed in core; only the bridge (edge) touches S3, and it never reads the vault (Invariant 2). **⚠️ Carry-forward:** Phase 4 empirical `-m podman` still pending (podman machine won't boot here — see runbook.md).

## Hardening pass — verifiable properties (2026-06-26)

**Not a phase.** Verification-only pass against `docs/WHITEPAPER-FORMAL-PROPERTIES.md`. **Main build not advanced (Phase 8 stays queued); dream R&D flag OFF; runtime behavior unchanged** (same outputs/defaults — internal types/checks hardened). Worked the invariant catalog by assurance tier.

**Promoted toward "unrepresentable" (structural — highest leverage)**

- **I6/G3 — typed `MirrorView`** (`core/mirror.py`). Sole constructor `project` applies the MIRROR_READABLE projection; `__post_init__` raises on any non-authored row, so a non-MR view is **unrepresentable** (not "checked then refused"). Dreamer (`clusters()`) + curator (`near_duplicates`, `contradictions`) introspective reads now flow through it. The firewall is structural for the introspective read path. **New gap G11:** guards the data, not the store handle.
- **I9/G1 — stable digest citation IDs** (`core/selfcheck.py` `Source`). Grounding resolves each `[[title]]` to a single retrieved **digest**; a title matching two distinct digests is flagged _ambiguous_ (the ill-posed case G1 named) instead of silently accepted. Librarian (`Retrieval.digest`) + dreamer pass `Source`s. **New gap G10:** surface form still a title (decidable iff unique-in-Ret, now detected when not).
- **I10/G2 — `derived_from` edges + acyclicity** (`core/stores/derived.py`). `add(derived_from=…)` records edges and **refuses a cycle at insert** (`DerivationCycleError`); `depth()` computes d(κ); `core/recursion.py` `decay_bound` gives c≤γ^d·g. Dreamer/curator record authored-leaf digests → today every interpreted node is depth-1 over authored ground (recursive dreaming, flag-OFF, is what the deeper machinery is for). Additive SQLite migration for the new column. **New gap G9:** authored-leaf-only is by-convention (store can't tell a digest from a string); adjudicator that consumes the ranking is Phase 9.

**Static lint (I2 — promoted runtime→static)**

- `ops/import_lint.py` (stdlib AST, zero new deps) + `scripts/check_imports.py` + `.github/workflows/ci.yml` + `tests/test_import_firewall.py`. Core imports no `edge`/`cloud` (hard, zero-exception) and no networking primitive outside the audited loopback allowlist (`core/sealing.py`, `core/models/ollama_client.py`). Proves no core→net import path _without running_.

**Property tests (Hypothesis)** — `tests/test_properties.py`: I6 (observed never survives projection), I9 (grounded ⇔ citations resolve uniquely), I10 (decay non-increasing in depth; chain depths increase; cycle rejected), I13 (authority non-widening under arbitrary skill composition). `hypothesis` added to dev deps.

**Exhaustive FSM checks**

- **I8** (`tests/test_loader_fsm.py`): BFS over every reachable two-slot resident set (real budget + a 5GB tight budget); ceiling holds in all reachable states; a load is refused **iff** it would breach; a refusal never mutates state.
- **I12/G5** (`ops/gate.py` `gate_admits` + `tests/test_gate_fsm.py`): pure admission predicate G_now = approved ∧ golden≥B ∧ D≤Θ — **`conforms` deferred, absent not stubbed-true**; all 8 boolean states enumerated (admits only all-true, fail-closed); Δ-never-self-applies asserted structurally (data-in/bool-out, no Δ handle). The apply/validate/rollback loop stays Phase 10 — only the decision core is verified.

**Honesty fixes**

- **G5** — live gate guard stated without the `conforms` conjunct (above).
- **I1** — native-bypass assumption + OS-isolation bound reaffirmed; already consistent across `core/sealing.py` docstring + `runbook.md §Sealing`; formal doc discharge-status row makes the bound explicit (pf/netns is the real guarantee before any networked phase).
- **G6** — anti-starvation aging (`scheduler/queue.py` `AgingPolicy`): a QUEUED job's effective priority improves with wait time up to the INTERACTIVE floor (never preempts a REACTIVE escalation), a no-op under normal load. Tests in `tests/test_queue.py`.
- **G7** — bounds declared at each site: γ=0.5 (depth-3 ≤ 0.125·g) + λ≤0.25 (`core/recursion.py`); σ ∈ [0.55,0.75] (`config/defaults.toml [dreaming]`); k ∈ [3,8] (`Librarian.k`); h ∈ [512,2048] (`scheduler/budget.py`).
- **G8** — provenance preorder **retired** (decorative; only MR-set membership + derivation-invariance are load-bearing, both now structural). Removed from `core/provenance.py` note + `WHITEPAPER-TECHNICAL.md §provenance`.

**Verified:** `ruff check .` clean; `pytest -m "not live and not podman"` **183 passed (+31 new)**, 12 deselected (live + podman). Import firewall `python -m ops.import_lint` → OK. No runtime-behavior change: existing Phase 0–7 logic tests unchanged and green.

**Gap ledger after this pass:** CLOSED G1, G2, G3, G6; STATED G5; DECLARED G7; RETIRED G8. OPEN: **G4** (drift metric & Θ — Phase 11), and newly-exposed **G9** (structural authored-leaf check), **G10** (digest-as-surface-citation), **G11** (MirrorView guards data not handle) — all recorded in the formal doc, none blocking. **Carry-forward:** Phase 4 empirical `-m podman` still pending.

**Next:** unchanged — **Phase 8 (the airlock, AWS Zone C)**; needs §20.7 + §20.9 from the owner.

## Dream R&D detour — R0 + R1 (2026-06-26, FEATURE-FLAG OFF)

**Not a phase; not the live path.** R&D track per `docs/design-notes/dream-phase-rnd-charter.md` (+ `dreaming-v2-interpreter-panel.md`, `recursive-dreaming-bounded-by-grounding.md`) and WHITEPAPER-TECHNICAL §6–8. **Main build NOT advanced (Phase 8 stays queued); flag OFF by default; never wired into `scheduler/cron.py`** (the live dream path still runs the Phase-7 `Dreamer`). Builds on the hardening-pass substrate: MirrorView (G3), digest IDs (G1), `derived_from`+acyclicity+`decay_bound` (G2/I10). Built **R0 then R1 only** — NOT R2 (utility), R3 (recursion), or R4 (cross-source).

**Hard flag boundary** — `core/dreaming/rnd.py` `require_rnd_enabled()` raises `DreamRnDDisabledError` unless `[dream_rnd] enabled = true`; every R0/R1 entry point calls it, so the engine cannot run in a normal session even via a direct import. `[dream_rnd]` config + `DreamRnDConfig` loader wiring (default `enabled=false`).

**R0 — interpreter panel** (`core/dreaming/graph.py` + `interpreters.py`). Generalized the single Phase-7 clusterer into a REGISTRY of deterministic, model-free method-specialists over the **`MirrorView`** (authored-only firewall, structural): `community` (connected components), `centrality` (degree hubs), `bridge` (structural holes via local clustering coefficient — dependency-free, no graph lib in the sealed core), `density` (cores + explicit noise/outliers). `change_point` is a **deferred seam** (returns nothing — needs a per-note temporal axis the MirrorView lacks; never faked). Each emits a `Claim(method, statement, support=authored digests, data)` — model-free; the model is earned only for narration, which R0/R1 do not do.

**R1 — evidence-based adjudicator** (`core/dreaming/adjudicator.py`; `core/selfcheck.py grounding_score`). Extended grounding into a ranker: confidence `c(κ) = γ^d·g(κ)·(1+λ(|Agr|−1))` over consensus groups (union-find on support-set Jaccard). **Evidence, not persuasion:** `g` (authored-grounding) is the currency; `g=0 ⇒ c=0`, so **agreement is a confidence multiplier, not a vote** (corroboration can't manufacture confidence). Output = a **confidence-ordered dream log**, each entry carrying content-addressed authored evidence refs, stored **INTERPRETED-only** (`DerivedStore`, no provenance param) with `derived_from` = authored leaves (depth-1, acyclic). **Confidence and utility are separate axes** — only `confidence` is stored; no combined scalar (utility = R2, not built). New `DREAM_LOG` kind.

**Safety spine held (all enforced + tested):** inputs are MirrorView (authored-only; observed can't enter — `test_observed_rows_cannot_enter_the_panel`); grounding terminates in authored leaves (`terminates_in_authored`, `grounding_score` penalizes non-authored refs → the R3 chain-may-not-close-in-interpreted guard); confidence ≠ utility (separate, never one scalar); agreement multiplies, never votes (`test_agreement_cannot_manufacture_confidence_from_no_evidence`). **No recursion (R3) or cross-source (R4).**

**Verified:** `ruff` clean; `pytest -m "not live and not podman"` **194 passed (+11 R&D)**, 12 deselected; import-firewall OK (the new `core/dreaming/*` modules import no network/zone). Confirmed `scheduler/`+live dreamer reference NO R&D symbol (`grep` clean) — the boundary holds. Determinism + INTERPRETED-only storage asserted (`tests/test_dream_rnd.py`).

**Next R&D (only when resumed, in order):** R2 utility telemetry (separate axis) → R3 recursion (ONLY after the Phase-11 drift gauge exists to watch it — depth cap + the dreams-citing-dreams / utility-up-grounding-down / confidence-up-with-depth alarms) → R4 cross-source assistant synthesis (observed+authored, interpreted, never the mirror). **R5 — curated-graph dreaming + cross-graph resonance** sits _beside_ this chain (needs only R0/R1, not R2–R4): run the panel on a `curated` corpus (a book) in its OWN graph via a `CuratedView`, then cosine **resonance** between curated and authored theme-centroids — firewall held: `curated ∉ MIRROR_READABLE` (so `MirrorView` structurally excludes it — verified), the book is never merged into the authored mirror, resonance output is `interpreted`-only (DerivedStore has no provenance param) and never mutates the mirror. See [design-notes/dreaming-on-curated-graphs.md](design-notes/dreaming-on-curated-graphs.md); build after R0/R1 in a deliberate R&D session, flag OFF. **Main build resumes at Phase 8 (airlock).**

## Phase 8 — The airlock (AWS Zone C) (COMPLETE, 2026-06-26)

**Gate to verify:** sanitized request → public corpus → ranked inside core; core never touched the network; IAM tight.

First **Zone C** work. The one-way research flow (§16): core emits **de-identified criteria** → filesystem handoff → the Zone-B **bridge** PUTs to S3 `requests/` → the cloud **fetcher** (Lambda) writes public literature to S3 `results/` → bridge GETs to the handoff → core **ranks inside the walls**. The sealed core never touches S3/network; only the bridge does, and it has no vault handle (Invariant 2 & 11). **Owner decisions applied (phase8-aws-decisions):** acct 054942746160, SSO `alberto-sso`, us-east-1, fresh dedicated TF state, Lambda compute.

**Built — Zone A (sealed core), `core/research/`**

- `criteria.py`: **the privacy boundary.** `ResearchCriteria` (topic + scrubbed terms + coarse filters) is the ONLY object that crosses outbound — it has **no field that can carry note content** (`to_request()` serializes only those fields; structural firewall like `DerivedStore`'s missing `provenance` param). `deidentify()` is the **conservative** scrubber (drops/raises on emails, URLs, phones, handles, long digit runs, dates, over-long phrases; charset allowlist; capped term count/results; publication-type allowlist). `assert_clean()` re-validates at the emit boundary so a hand-built criteria can't bypass it. The model only _advises_ (proposes terms); this code _acts_ (Invariant 2).
- `airlock.py`: `ResearchAirlock` (core side) — writes criteria requests / reads literature results on disk ONLY (`data/airlock/requests|results`), mirroring the §12 interface handoff. **No S3, no network, no `import edge`.** `emit()` re-asserts cleanliness before anything leaves.
- `rank.py`: `rank_literature()` — "smart inside" personalization. Ranks public papers by cosine to the centroid of the owner's most-relevant **AUTHORED** notes (mirror firewall holds), adjusted by evidence tier; flags preprints (not-yet-vetted) + unresolved identifiers (§III.1 honesty). **Transient — never ingested into the mirror** (public ≠ authored). Falls back to topic-query similarity when the corpus is silent.
- Librarian §16 seam realized: `research_criteria(query)` (deterministic keyword proposer default; `model_term_proposer` is the richer injectable option) — both feed `deidentify`, the enforcer.

**Built — Zone B (edge), `edge/bridge/`**

- `bridge.py`: `ResearchBridge` — the **only** component that touches S3. A **dumb pipe**: shuttles opaque JSON (handoff/requests → S3 `requests/`; S3 `results/` → handoff/results), never interprets criteria or papers, **has no vault handle** (constructed with only a handoff dir + an injected S3 client). `boto3` imported **lazily** in `build_bridge` so tests (fake S3) need no boto3 and core never sees it. No S3 delete → bucket lifecycle handles cleanup (tighter IAM). `protocol.py` = the key-layout contract (mirrored, not imported, by core).

**Built — Zone C (cloud), `cloud/fetcher/` + `cloud/terraform/`**

- `fetcher/`: the Lambda. `sources.py` (OpenAlex/Europe PMC/arXiv — **key-free**, stdlib `urllib`/`xml` only, injectable `fetch`), `aggregate.py` (gather → de-dup by DOI/title → bias toward systematic reviews/meta-analyses/guidelines → flag preprints → **drop unresolvable identifiers**), `handler.py` (`process_request`/`handle_event` pure+injectable; `lambda_handler` wires real boto3+net). **Dependency-free zip** (stdlib + runtime boto3).
- `terraform/bootstrap/`: fresh **dedicated state backend** — `mind-palace-tfstate-054942746160` (versioned, SSE-KMS, public-access-blocked, TLS-only), **local** state, **S3-native locking** (`use_lockfile`, no DynamoDB).
- `terraform/airlock/`: the airlock bucket (`requests/`+`results/` prefixes, public-access-blocked, SSE-S3, TLS-only, short lifecycle expiry — it's a transit), the fetcher Lambda (S3 PUT→`requests/` trigger; **no VPC** = public egress to the literature APIs only), CloudWatch logs, and **least-privilege IAM** — fetcher: `GetObject requests/*` + `PutObject results/*` + own logs; bridge role: `PutObject requests/*` + `GetObject/List results/*` (prefix-scoped). Account-id guardrail (`allowed_account_ids`). Backend in `backend.tf`; offline `validate` via `init -backend=false`.
- Config: `[airlock]` (`handoff_dir` for core; S3 bucket/region/profile/prefixes for the bridge only) + `AirlockConfig`. `pyproject` `edge` optional dep (`boto3`) — never a core dep.

**Verified (gate met):** `ruff` clean; `pytest -m "not live and not podman"` **225 passed (+31 new)**, 13 deselected; import-firewall (`python -m ops.import_lint`) **OK** — `core/research/*` add no network/zone imports (AST-checked); core has zero S3/boto3/edge reach. `terraform validate` + `tflint` + `fmt -check` clean on **both** configs.

- _sanitized request_ — `test_research_criteria` (PII dropped/refused; structural firewall: `to_request` carries only criteria fields; `assert_clean` catches hand-built dirty criteria) + `test_research_airlock` (emit writes only de-identified criteria; refuses dirty at the boundary).
- _public corpus_ — `test_fetcher` (dedup by DOI across sources; evidence ordering; preprint flagged; unresolvable dropped; one flaky source doesn't sink the gather; `handle_event` S3 read→aggregate→write) + `test_bridge` (push→S3 byte-for-byte; pull→handoff; ignores unknown ids; no vault handle).
- _ranked inside core_ — `test_research_rank` (corpus relevance outranks irrelevant; evidence tie-break; preprint/unresolved flags; corpus-silent fallback) + **`test_research_live` PASSED** (real embedder over the golden fixture corpus: on-topic paper ranks first by private-corpus relevance — the embedding model is pulled).
- _core never touched the network / IAM tight_ — import firewall + the structural no-vault-handle bridge; least-privilege IAM validated + tflint-clean.

**Decisions**

- **De-identification is structural + conservative, not best-effort.** Two layers: a type that _cannot_ carry corpus content, plus a scrubber that _raises rather than passes doubt_. Both tested. The richer PII scrubber (corpus proper-noun denylist / NER) is a documented extension point.
- **Bridge is a dumb pipe with no vault handle** — network and private data never share a component (Invariant 2). Even a bug here can't leak the corpus: there's no corpus to reach, and outbound bytes are already de-identified by core.
- **Public literature is ranked transiently, never ingested into the mirror** — it's external/public, not the owner's authored writing; mixing it in would corrupt the mirror + §15 baselines.
- **S3-native state locking** (Terraform ≥1.10 `use_lockfile`) instead of a DynamoDB table — fewer resources, less IAM, simpler.
- **Fetcher web egress is a network property (no VPC), not an IAM grant** — its IAM is exactly the two prefixes + logs; it can reach only public endpoints, nothing private. ("Dumb outside / smart inside": personalization stays local — no remote summarization model, per owner default.)

**⚠️ Operational boundary honored — `terraform apply` NOT run.** Per the owner's instruction, the config is written + `validate`/`fmt`/`tflint`-clean but **no live AWS resources were created**. To deploy: `aws sso login --profile alberto-sso`, then `bootstrap` apply (state backend), then `airlock` `init`/`plan`/`apply`; copy `airlock_bucket` → config `[airlock] s3_bucket` and configure an `mind-palace-bridge` AWS profile assuming `bridge_role_arn` (steps in `cloud/terraform/airlock/README.md`). Recommended hardening at apply: set `bridge_trusted_principal_arns` to the SSO permission-set role ARN (default falls back to account root). **Carry-forward:** Phase 4 empirical `-m podman` still pending (machine won't boot here — runbook.md).

**Next (Phase 9 — Backups):** restic → S3 + SSE-KMS, scheduled; client-side encrypted + deduplicated so AWS never sees plaintext (§16b). _Verify:_ encrypted backup + restore round-trips; AWS sees no plaintext. Reuses the bootstrap state backend; new namespaced bucket + KMS key. macOS/APFS — restic over data directories, don't assume btrfs.

## Near-term task — Vault watcher & capture (2026-06-26, NOT a phase)

**Not a phase; main build stays at Phase 9 next.** Built the capture path from design-notes/vault-sync-and-capture.md so the owner's notes auto-ingest and embeddings stay current. Touches the Phase-1 ingest; adds an incremental watcher + tombstone deletion + a gated purge. The networked sync transport is **documented, not coded** (a separate process, never the core).

**Built — core-side, LOCAL filesystem only (no network; import-lint stays green)**

- `core/stores/catalog.py`: `VaultCatalog` (SQLite) — the **active/tombstone ledger** mapping `source_path → (digest, active)`. Content-addressing gives dedup but not "which file holds which content"; this is that map + the authority for tombstone semantics. `record`/`get`/`tombstone`/`active_refs`/`paths_for_digest`/`remove_digest`. All notes are `authored-solo` = the existing AUTHORED tag (spectrum split deferred, §1).
- `core/ingest/sync.py`: `VaultSync` — the deterministic re-ingest engine. `sync_path` (unchanged digest+active → **no-op**; else (re)embed through the Phase-1 `ingest_note`+`index_records`, **delete-then-add so re-index is idempotent**, then drop the previous digest's derived rows iff no active file still references them); `handle_deleted` (**tombstone**: derived dropped, catalog inactive, **raw KEPT**); `rescan` (full catalog-vs-vault reconciliation — the idempotent backbone + catch-up). `SyncOutcome`/`SyncReport`.
- `core/ingest/watch.py`: `VaultWatcher` — watches the vault, **debounces** a save burst into one `on_change`, takes an **injected callback** (so core never imports the scheduler). `watchdog`/FSEvents is an **optional, lazily-imported** real-time backend; **polling fallback** when absent. No `edge`/socket/http import.
- `core/ingest/purge.py`: `purge_raw` — the **owner-gated true-deletion** action (the ONE exception to "raw is sacred"). Two fail-closed gates: `confirm=True` required, and refuses if `active_refs(digest) > 0` (delete from vault first). Mirrors the propose/approve posture (Invariant 4). `RawStore.delete` + `VectorStore.delete(digest=…)` are the new store primitives.

**Built — scheduler wiring (depends on core, never the reverse)**

- `scheduler/vault_sync.py`: `vault_sync_handler` (runs the idempotent `rescan`), `enqueue_vault_sync` (**BACKGROUND** priority), `build_vault_watcher` (on_change → enqueue). Routed to the **pinned** tier (`scheduler/router.py` `_PINNED_KINDS`): vault_sync needs no chat model (it calls the embedder directly), so `ensure_tier` is a no-op and the **worker slot is never evicted**; it's NOT in HEAVY_TIERS, so a note saved mid-session re-ingests promptly (not trough-gated).
- `scripts/watch.py` (seals → wires watcher+supervisor → loop) + `scripts/purge_raw.py` (`--list` / `<digest> --confirm`). Config: `paths.vault_catalog`, `[vault] watch_debounce_s`/`watch_poll_interval_s`; `watchdog` as an OPTIONAL `[watch]` extra (poll fallback otherwise).

**Verified:** `ruff` clean; `pytest -m "not live and not podman"` **242 passed (+17 new)**, 13 deselected; import-firewall **OK** (the watcher reaches no network). **Real-embedder end-to-end smoke** (temp stores, 2560-dim): edit a note → embeddings update (old digest rows gone) → search reflects new content; **unchanged re-scan → no-op** (`UNCHANGED`); **delete → stops surfacing, raw kept**. Cold tests pin the same plus **dedup-safety** (shared content isn't dropped until the last active ref) and **re-add reactivates** a tombstone (`tests/test_vault_sync.py`), the **debounce/poll-fallback** (`tests/test_vault_watcher.py`), the **gated purge** (`tests/test_purge_raw.py`), and the **scheduler wiring** (pinned tier + background priority + watcher→enqueue, `tests/test_vault_sync_wiring.py`).

**Documented (operational, not code) — `docs/runbook.md` "Vault watcher & sync":** **Syncthing over Tailscale** for private peer-to-peer vault sync (device-to-device, encrypted, **no vendor in the path**); Tailscale as the private mesh to also reach the future interface gateway; the **iCloud/Obsidian-Sync vendor-transit tradeoff flagged** (Invariant 11 class). The sync transport is a separate process; the core only watches a local folder.

**Decisions / invariants held**

- **Watcher signals, supervisor acts.** The watcher enqueues a job; all store mutation stays on the single-writer queue. Core stays scheduler-free (clean layering) via the injected callback.
- **Delete = tombstone, not destroy.** Raw is sacred; derived rows are dropped and the catalog marks inactive, so re-adds dedup and nothing is lost. True deletion is the separate, gated, owner-initiated purge.
- **Dedup-safe deletion.** Derived rows for a digest are dropped only when no active file still references that content (the catalog's `active_refs`) — so two files with identical content don't pull each other's embeddings out.
- **Seal integrity.** The watcher is core-side, local-filesystem only; `watchdog` (no network) is optional + lazy; import-lint green. The networked sync daemon/interface gateway are separate processes / Zone B.

**Next:** unchanged — **Phase 9 (Backups)**: restic → S3 + SSE-KMS, scheduled; AWS sees no plaintext (§16b).

## Near-term task — Vault sync operational setup + concurrency fix (2026-06-27, NOT a phase)

Continuation of the 2026-06-26 vault-sync entry above: that session built the code; this session did the **operational setup** (Tailscale + Syncthing + the watcher as a launchd service) end-to-end on the owner's Mac + iPhone, found and fixed a real concurrency bug the operational run surfaced, and live-verified all three gate behaviors (not just unit tests). Main build is **still at Phase 9 next** — not started this session.

**Configured — Tailscale.** Mac (Homebrew cask) + iPhone joined the same tailnet. `tailscale status` shows both (`albertos-macbook-pro` 100.97.85.13, `iphone182` 100.74.4.2); `tailscale ping` confirmed a **direct** path (`via 192.168.x.x:41641`, no DERP relay) before Syncthing was even installed.

**Configured — Syncthing, confined to the tailnet.** Installed on Mac via `brew services start syncthing` (loopback GUI at :8384, persists across logins). Synctrain on iPhone (free/OSS Syncthing client; Möbius Sync was the fallback option, not needed). Vault folder (`~/.mind-palace/vault`, id `mind-palace-vault`, type `sendreceive`) shared between the two devices; `.stignore` added for `.DS_Store`/`.stversions`/temp files so macOS metadata never syncs. **Confinement (the privacy-sensitive part):** `globalAnnounceEnabled`/`relaysEnabled`/`natEnabled`/`localAnnounceEnabled` all set `false` on the Mac; the phone's Synctrain Advanced Settings matched (`Announce globally` off, `Enable relaying` off, `Enable STUN` off); both devices' peer address pinned to the other's **Tailscale IP** (`tcp://100.97.85.13:22000` / `tcp://100.74.4.2:22000`) rather than left `dynamic`. Verified live on **cellular** (no LAN involved): Syncthing's `/rest/system/connections` showed `address: 100.74.4.2:22000, type: tcp-server` — i.e. direct device-to-device over the tailnet, not a relay, with no public discovery/relay server ever contacted.

**Configured — watcher as a launchd service.** `watchdog` installed (real-time FSEvents; was previously absent → would have silently run in 5 s-poll fallback). New LaunchAgent `~/Library/LaunchAgents/com.mind-palace.watch.plist` → `./.venv/bin/python scripts/watch.py`, `RunAtLoad`+`KeepAlive` (10 s `ThrottleInterval` so a real crash can't loop tight), `PYTHONUNBUFFERED=1` so logs flush, stdout/stderr to `data/logs/watch.{out,err}.log`. Managed via `launchctl bootstrap|bootout gui/$(id -u)[/com.mind-palace.watch]`.

**Bug found + fixed: `scheduler/queue.py` cross-thread SQLite crash.** Live verification (a file touched on the Mac while the launchd service was running) produced **no enqueued job** — silent failure invisible to `launchctl`/`ps` (service looked healthy throughout). Root cause: `JobQueue.__post_init__` opened its `sqlite3.connect()` with the default `check_same_thread=True`, but `core/ingest/watch.py`'s debounce (`threading.Timer`) and its poll fallback both fire `on_change` from a thread they spawn, not the thread that constructed the queue — so every real-time-triggered `enqueue()` raised `sqlite3.ProgrammingError`, caught only by `threading`'s default excepthook (prints to stderr, doesn't propagate). `tests/test_vault_sync_wiring.py::test_watcher_on_change_enqueues_a_job` never caught this because it calls `watcher.on_change()` synchronously on the test's own main thread. **Fix:** `sqlite3.connect(..., check_same_thread=False)` + an internal `threading.RLock` (reentrant — `enqueue()`/`claim()` call `self.get()` while already holding the lock) guarding every `JobQueue` method body. No behavior change for the existing single-thread callers (supervisor loop); makes the already-stated "single-writer" design (roadmap §7) actually safe across the in-process threads that now legitimately call it. **247 logic pass** (up from 242; no tests removed — the gap was a missing scenario, not a wrong assertion), ruff clean, import-lint green.

**Configured — iOS capture (no third-party notes app).** Owner tried Apple Notes → Share → Save to Files, which (a) always names the export `text.txt` and auto-numbers on collision, and (b) can't produce a real `.md` at all — Shortcuts' own `Save File` action forces the input's native UTType extension (`.txt` for plain Text) regardless of what's typed in `Subpath`, even when the subpath string visibly ends in `.md`. Built an iOS Shortcut instead: `Ask for Input` (Text, multiline) → `Format Date` (input = **Current Date**, not Date Created — an easy variable-picker miswire) `yyyy-MM-dd-HHmmss` → `Save File` (saves the **input text**, not the date; destination = **Ask Each Time** since this iOS has no folder-bookmark action that can reach a third-party Files provider like Synctrain; `Subpath` = `note-[Formatted Date].md`) → **`Rename`** (the fix for the forced-`.txt` quirk — renames the just-saved file to the same `note-[Formatted Date].md` string). One tap, lands directly in the Synctrain → Mind Palace Vault folder.

**Live end-to-end verification (real devices, not mocks):**

- _Sync → ingest → searchable:_ a note authored via the Shortcut on the iPhone (sentinel phrase, cellular connection) synced to the Mac, was picked up by the watcher **fully automatically** (no manual rescan) once the threading fix landed, embedded, and came back as the #1 semantic-search hit (distance 0.42 vs. 0.61 for the next-closest note).
- _Delete → tombstone:_ removing a tracked `.md` produced `tombstoned=1` automatically; catalog row `active=False`; vector rows for its digest dropped (no longer in search results); **`RawStore.exists(digest)` still `True`** — raw kept, per spec.
- _Unchanged → no-op:_ a rescan with zero vault changes returned `indexed=0 unchanged=121 tombstoned=0`; vector count identical before/after (917 → 917).
- Synctrain quirk confirmed and handled: phone-authored files don't push until the **Mind Palace Vault folder is manually rescanned** (pull-to-refresh) in Synctrain — iOS suspends the app's background file-watcher.

**Decisions**

- **Tailscale-only addresses + all discovery/relay disabled, on both ends, not just one.** Pinning only the Mac's address would still let the phone fall back to public discovery when off-LAN; both sides needed the same lockdown for the "no vendor in the path" guarantee to hold in every network condition (confirmed by testing the lockdown over cellular, not just Wi-Fi).
- **`RLock` over a plain `Lock`** for the `JobQueue` fix — `enqueue()` and `claim()` already call `self.get()` internally; a non-reentrant lock would deadlock on that self-call. Kept the fix mechanical (lock the existing methods) rather than refactoring to private `_locked` variants, matching the no-premature-abstraction convention.
- **iOS Shortcut over Obsidian/Runestone for capture** — owner's call: zero extra apps, can even share straight from Apple Notes' share sheet into the Shortcut-adjacent folder workflow once the Rename step exists.
- Scratch/test artifacts created during verification (`Untitled.md`, `_direct_touch_test.md`, assorted `.txt` exports) deleted from the vault at session close (two-way sync removes them from the phone too); the one real verification note (`note-2026-06-27-115916.md`) was kept.

**Next:** unchanged — **Phase 9 (Backups)**, not started this session.

## Security & attestation track — Step 1: test reorganization (2026-06-27, NOT a phase)

**Not a phase; main build stays at Phase 9 next.** First step of the cross-cutting **security & attestation track** (test foundation → attestation records → crypto → Vault dev-mode → Vault↔attestation join → owner runbook), per design-notes/{test-organization,holistic-testing,attestation-layer,vault-runtime-auth}.md. Like the hardening pass: pulls forward attestation (Phase 10) + Vault primitives (Phase 5) because the building blocks exist (digests, Constitution fingerprint, `derived_from` edges, the `get_secret()` seam). This step is the **pure test-suite refactor** + seeding the new holistic-testing categories. **No production/runtime behavior changed.**

**Built — test reorganization (mechanical, no logic change)**

- Migrated the flat `tests/` into execution-profile subdirs (test-organization.md §1): `unit/` (65), `integration/` (154), `e2e/` (13 = all live+podman), `property/` (11 = Hypothesis + FSM checks), `integrity/` (12), plus empty-but-tracked `metamorphic/ adversarial/ emergent/ longitudinal/ fixtures/`. All 56 files moved via `git mv` (history preserved).
- Per-dir `conftest.py` applies its **category marker** by **path filter** (the global-items pytest gotcha: a subdir conftest's `pytest_collection_modifyitems` still receives the _whole_ item list, so each only marks items under its own dir). Capability markers (live/podman/slow/needs\_\*) stay per-file (`pytestmark`). All markers registered in `pyproject.toml`; `addopts = -m 'not longitudinal'` keeps the scheduled suite out of a bare `pytest`.
- **`integrity/` = the non-skippable CI gate**: network seal (`test_sealing`), import-firewall (`test_import_firewall`), mirror/provenance firewall (`test_mirror`). `.github/workflows/ci.yml` gains an `integrity-gate` job (`pytest -m "integrity and not live and not podman"`) as its own required check; the fast-suite job now also excludes `longitudinal`.
- The move surfaced + fixed **two inter-test-module imports** (`from tests.test_vault_sync import DIM, FakeEmbedder`; `from tests.test_sandbox_pool import FakeRunner`) that would have broken — resolved the design-note way: extracted the shared fakes into the new **`tests/fixtures/`** package (`embedding.py`, `sandbox.py` + `corpus.py`/`stores.py` generators); root `tests/conftest.py` puts `tests/` on `sys.path` so `fixtures` imports from any category. Two `__file__`-relative repo-root refs (`test_import_firewall`, `test_fetcher`) re-anchored to `parents[2]` for the new depth.

**Seeded — holistic-testing categories (new, additive, all passing)**

- `metamorphic/` (+3): ingest idempotency (content-addressing — re-ingest ⇒ same digest, stored once, verbatim bytes round-trip); clustering order-independence.
- `adversarial/` (+7): derivation-cycle refused through the public `add()` path (multi-hop + self-ref); prompt-injection note ingested as AUTHORED content with no provenance escalation; PII scrubber raises-on-doubt (email/phone/URL topic) + `assert_clean` bypass-proof.

**Verified**

- **Pure-refactor invariant held:** before = after = **255 collected / 242 passed** (`-m "not live and not podman"`), 8 live + 5 podman deselected. The move changed zero test outcomes.
- After seeds: **265 collected / 252 passed** (+10). Categories partition exactly (65+154+13+11+3+7+12 = 265 — verified no double-marking); `e2e` == `live or podman` (13); `integrity` gate = **12 passed**.
- `ruff check .` clean; import-firewall (`python -m ops.import_lint`) **OK** — core still reaches no network/zone.

**Owner-deferred:** none this step (no production action; CI change is config only). **Carry-forward:** Phase 4 empirical `-m podman` still pending (machine won't boot here — runbook.md).

**Next (Step 2 — attestation: records layer, NO signatures):** `core/attestation/` `Attestation` dataclass + append-only `AttestationStore` (no delete/update); `attestation_id` column on `DerivedStore`; emit **unsigned** attestations from Dreamer/Curator/VaultSync; `integrity/` tests asserting complete chains to authored leaves + dreamer attestation never references observed. Verify chain structure before adding crypto (Step 3). Steps 4–6 (Vault dev-mode, Vault↔attestation join, owner runbook) follow.

## Security & attestation track — Step 2: attestation records, NO signatures (2026-06-27, NOT a phase)

**Not a phase; main build stays at Phase 9 next.** Second step of the security & attestation track (attestation-layer.md §2,§4,§5,§8). Built the **runtime proof layer's RECORDS** — the unsigned chain of custody — leaving `signature`/`signer` empty until Step 3, per the design note's "start without signatures; prove the structure first." **No runtime output changed** (the attestor is optional + additive; existing direct-construction tests pass an implicit `None`).

**Built — `core/attestation/` (Zone A, stdlib-only; import-lint green)**

- `record.py` `Attestation` (frozen): content-addressed `id = SHA-256(signing_payload())` over a canonical, **order-insensitive** (sorted hash tuples), fixed-separator JSON of all fields except `id`/`signature`/`signer`. So the id is stable and the future signature signs the _same_ bytes the id is derived from (§2,§8). `create()` computes the id (never hand-set); `to_dict`/`from_dict` round-trip; `signing_payload()` is the Step-3 signing surface. `vault_token_accessor` defaults `""` (Step 5 populates).
- `store.py` `AttestationStore` (SQLite, **append-only STRUCTURALLY** — exposes `append` + reads, **no `delete`/`update` method exists to call**; `INSERT OR IGNORE` so a re-emitted identical record is a no-op, never an overwrite). `check_same_thread=False` + `RLock` (the watcher emits from a spawned thread — same posture as the JobQueue fix). `producers_of(hashes)` = the chain-linking lookup (attestations whose outputs ∩ hashes); `chain_for(id)` assembles the transitive `derived_from_ids` closure and flags broken links. `AttestationChain` (`is_complete`/`leaves`/`leaf_input_hashes`/`roles`/`constitution_fingerprints`/`verify_signatures(verify)` — the last a Step-3 hook).
- `attestor.py` `StoreAttestor` (the `Attestor` seam): agents call `emit(agent_role, action, input_hashes, output_hashes)`; it stamps the Constitution fingerprint + timestamp, **auto-links the chain** (`derived_from_ids = producers_of(input_hashes)` — so a dream that consumed digest D auto-derives from the ingest attestation that produced D), and appends. Step-3 signing slots in _inside_ `emit` — agents stay untouched. `build_attestor(cfg)` wires the configured store.
- `DerivedStore` gained an `attestation_id` column (additive migration + nullable) linking each interpreted record to the attestation that produced it (§5); public `artifact_id(kind, subkind, subjects)` so an emitter precomputes the record id, attests it as output, then writes the record with the link. `[paths] attestation_store` config (loader uses `.get` default so older TOMLs still load).
- **Emitters wired** (each gains an optional `attestor`; `None` = off, default): Dreamer (`dream_pass`: inputs = clustered authored digests, output = dream record), Curator (`curate_finding` per finding), VaultSync (`ingest_note` on INDEXED: input==output==content digest — the authored leaf). `build_dreamer`/`build_curator`/`build_vault_sync` auto-wire a shared `build_attestor(cfg)`, so a live run produces a chained audit trail (ingest leaves → dreams/findings) in `data/attestations.sqlite`.

**Verified**

- `ruff` clean; import-firewall (`python -m ops.import_lint`) **OK** — `core/attestation/*` reach no network/zone. Fast suite **265 → 278 collected / 252 → 265 passed** (+13: 8 store mechanics, 3 integrity chain, 2 derived `attestation_id`), 13 deselected. Integrity gate **12 → 15 passed**.
- **Records-layer integrity (the new gate tests, `tests/integrity/test_attestation_chain.py`):** a real dreaming pass (fake synthesizer, fixed-fingerprint attestor) over a corpus where an OBSERVED note sits _right next to_ the authored cluster in vector space → every derived dream's `attestation_id` resolves to a **complete chain** whose leaves are the ingest attestations, `leaf_input_hashes` == exactly the authored digests (present in raw), `roles == {dreamer, vault_watcher}`, one Constitution fingerprint; and **no dreamer attestation references the observed digest** — the firewall holds at the attestation level (runtime half; the static half is MirrorView + import-lint). Append-only asserted structurally (no `delete`/`update` attr).
- Store mechanics (`tests/integration/test_attestation_store.py`): content-addressed + order-insensitive ids, idempotent append, `producers_of`, chain closure + broken-link/missing-root detection, `by_role`.

**Owner-deferred:** none (no production action; `data/attestations.sqlite` is gitignored). **Carry-forward:** Phase 4 empirical `-m podman` still pending.

**Next (Step 3 — attestation crypto, Ed25519, test keys):** signing in `StoreAttestor.emit` over `signing_payload()`; private key via `get_secret("attestation-signing-key")`, public key in repo, **test keypair in tests** (`@pytest.mark.needs_vault`-free — cold); `scripts/verify_attestation.py` standalone verifier; `chain.verify_signatures(verify)` wired to the real Ed25519 check; gate that attestations are signed by the owner key for gate decisions (owner key = Step 3 last). `integrity/`: signatures verify, tampering breaks them. Add `cryptography` dep (not a network lib — import-lint allows). **Production key placement is owner-operated.** Steps 4–6 (Vault dev-mode, Vault↔attestation join, owner runbook) follow.

## Security & attestation track — Step 3: attestation crypto, Ed25519 (2026-06-27, NOT a phase)

**Not a phase; main build stays at Phase 9 next.** Third step of the security & attestation track (attestation-layer.md §3–4,§8). Added the **tamper-evidence**: Ed25519 signatures over the Step-2 records. Signing is **owner-gated** (`[attestation] enabled=false` default → records-only; turning it on without a placed key is a hard error, never a silent unsigned run). **No runtime output changed** by default.

**Built — `core/attestation/` crypto (Zone A; `cryptography` dep — not a net lib, import-lint allows)**

- `crypto.py`: Ed25519 `sign`/`verify` (base64 seeds/pubkeys/sigs; `verify` returns False on any malformed input, never raises) + `Ed25519Signer` (private key + name "supervisor"|"owner"; the key never leaves the object — callers hand it a payload, get a signature; the model/agents never see it). `generate_seed()`.
- `verify.py`: `make_verifier(public_keys)` → `verify(att)` for `chain.verify_signatures`. An attestation verifies iff signed + known signer + valid Ed25519 over `signing_payload()` **and** — the §3 policy — **gate actions (`gate_approve`/`gate_reject`) are OWNER-signed** (a supervisor-signed gate decision is rejected, making gate approval non-repudiable). `load_public_keys` / `build_verifier` from the committed pub paths. (Gate-attestation _emission_ lands with the Phase-10 gate loop — `ops/gate.py` is still the pure decision core; the verification half is enforced now.)
- `StoreAttestor.emit` now signs when a `signer` is set: `signature = sign(signing_payload())`, `signer = name`, via `replace` — and because the id is computed over `signing_payload()` (which **excludes** signature/signer), **signing does not change the content-addressed id** (verified: signed and unsigned emits of the same action share an id). `build_attestor` attaches a supervisor signer only when `enabled` AND the seed is placed; **fail-closed (`AttestationKeyMissing`)** otherwise.
- `[attestation]` config (`enabled`, `signing_key_secret`, `owner_key_secret`, `supervisor_pub`, `owner_pub`) + `AttestationConfig` (Config field has a `default_factory` so direct `Config(...)` in tests stays valid).

**Built — keys, scripts, docs (the build/owner split)**

- Committed **public** keys `ops/attestation/{supervisor,owner}.pub` + **DEV** private seeds `tests/keys/{supervisor,owner}.seed` (deterministic from a fixed phrase; clearly marked NOT-production; `build_attestor` never reads `tests/keys/` — production signing uses `get_secret`). READMEs in both dirs draw the dev/production boundary.
- `scripts/verify_attestation.py` — owner's standalone audit tool (`<id>` verifies signature + chain to authored leaves; `--all`; `--list`; seals first, read-only, no net). `scripts/gen_attestation_keys.py` — owner-operated keygen (prints the base64 seed to place in Keychain, writes only the public half to `ops/attestation/`).

**Verified**

- `ruff` clean; import-firewall **OK** (cryptography is not a network module; core still reaches no net/zone). Fast suite **278 → 293 collected / 265 → 280 passed** (+15: 7 crypto unit, 8 signature integrity), 13 deselected. **Integrity gate 15 → 23 passed.** No category double-marking (72+164+13+11+3+7+23 = 293).
- **Signature integrity (`tests/integrity/test_attestation_signatures.py`):** emitted signatures verify (incl. after a store round-trip); **tampering any signed field or the signature breaks verification**; an unknown signer fails closed; `chain.verify_signatures` is True for a fully-signed ingest→dream chain and **False if any one link is tampered**; **gate decisions must be owner-signed** (supervisor-signed `gate_approve`/`gate_reject` rejected, owner-signed accepted); committed `ops/attestation/*.pub` match the dev seeds. Crypto mechanics in `tests/unit/test_attestation_crypto.py`.
- CLI smoke: `verify_attestation.py` end-to-end verifies a signed chain; exit codes correct (not-found→1, list→0, usage→2). `build_attestor` fail-closed when `enabled=true` + no key → `AttestationKeyMissing`.

**Owner-deferred (you write code; owner operates production keys):** generate real keypairs (`scripts/gen_attestation_keys.py supervisor|owner`), place the printed seeds in Keychain (`attestation-signing-key`, `attestation-owner-key`), commit the regenerated `*.pub`, set `[attestation] enabled = true`. Full steps go in the Step-6 runbook.

## Carry-forward RESOLVED — Phase 4 empirical `-m podman` (2026-06-27)

**Not a phase; a status correction.** The Phase-4 empirical isolation gate had been carried forward as "pending" across every checkpoint since 2026-06-25 (podman machine wouldn't boot: libkrun virtio-fs mount failure, then applehv wedged on recreation — see the Phase 4 entry + `docs/runbook.md`). Re-checked while pausing before Step 4: `podman machine list` now shows `podman-machine-default` (libkrun, 2 CPU/2GiB) **currently running**; `podman info` returns full healthy host info (cgroups v2, fedora podman-machine-os); a manual `podman run --rm alpine:latest echo ...` pulled and ran successfully. Ran the actual gate: **`pytest -m podman` → 5/5 passed** (`tests/e2e/test_sandbox_podman_live.py`: runs code + returns stdout, network is off, vault is unreachable, wall-clock timeout enforced, runs as non-root). Likely cause: a podman/libkrun update since the last attempt fixed the virtio-fs boot bug; no code or test changes were needed — the by-construction logic gate (Phase 4) and the empirical gate now agree. **The Phase 4 gate is now fully closed, both tiers.** No further carry-forward needed; do not re-add this note to future entries unless the machine regresses again.

## Security & attestation track — testing-coverage backfill (2026-06-27, NOT a phase)

**Not a phase; closes out the owner-requested pause** (testing-coverage + sandbox-resilience review before Step 4 — the podman half is the RESOLVED entry above). Grepped for the gap rather than guessing: confirmed no test anywhere constructed `Curator(..., attestor=...)`, `VaultSync(..., attestor=...)`, or called `build_dreamer`/`build_curator`/`build_vault_sync` — so the `self.attestor.emit(...)` lines added in Step 2 had never executed under test for two of the three emitters, and none of the three `build_*` wiring branches had ever run. Backfilled all three; no production code changed.

**Built (tests only)**

- `tests/integrity/test_attestation_chain.py`: extended with the Curator half of the existing Dreamer pattern — `test_curator_finding_carries_a_complete_chain_to_authored_leaves` (a real `Curator(attestor=...)` over a corpus with an OBSERVED note sitting next to the authored near-dup pair in vector space; every finding's `attestation_id` resolves to a complete chain, `roles == {curator, vault_watcher}`, `leaf_input_hashes` == exactly the authored digests, present in raw) + `test_curator_attestation_never_references_observed` (the runtime firewall half, mirrored from the dreamer test).
- `tests/integration/test_vault_sync.py`: `_sync()` helper now takes an optional `attestor=`. `test_indexed_emits_a_leaf_ingest_attestation` (a real `sync_path()` INDEXED outcome emits exactly one `vault_watcher`/`ingest_note` attestation with `input_hashes == output_hashes == (digest,)` — the chain's leaf) + `test_unchanged_rescan_does_not_emit_a_duplicate_attestation` (the UNCHANGED early-return never calls `attestor.emit`, asserted via `att_store.count()` staying at 1 across a second `rescan()`).
- `tests/integration/test_attestor_build_wiring.py` (new file): `build_curator`/`build_dreamer`/`build_vault_sync` each wire a real `StoreAttestor` pointed at the configured attestation-store path, checked with `dataclasses.replace(get_config(), paths=..., vault=...)` into `tmp_path` (so the smoke test never touches the live repo's `data/` dir) — no live model/Ollama call needed, since `OllamaClient`/`build_model_server`/`lancedb.connect` are all side-effect-free at construction. Plus one cross-agent check that all three resolve to the same on-disk store path (so production attestations from different agents actually chain together).

**Verified**

- `ruff` clean; import-firewall **OK**. Fast suite **293 → 301 collected / 280 → 288 passed** (+8: 2 curator chain integrity, 2 vault-sync emission, 4 build-wiring), 13 deselected. **Integrity gate 23 → 25 passed.** No category double-marking.

**Owner-deferred:** none (tests only). **Carry-forward:** none new.

## Security & attestation track — WASM sandbox runner, scoped not built (2026-06-27, NOT a phase)

**Design only — no code, no tests, no config changes.** Per the owner's selected sequencing
("scope, build-it-later, not now"), wrote `docs/design-notes/wasm-sandbox-runtime.md`: how a
future `WasmRunner` (wasmtime + Pyodide, named in CONVENTIONS.md/BUILD-SPEC §11 as the
pure-compute upgrade path) fills the existing `core/sandbox/runner.py` seam without changing
the `SandboxRunner` Protocol, `ExecSpec`/`ExecResult`/`Limits`/`Network`, or
`ExecutionBroker`. Covers: isolation-mechanism comparison (Podman's kernel boundary vs
wasmtime's capability boundary — no syscall import ever wired, vs one removed by flag);
mapping the six `SandboxRunner` methods onto wasmtime `Store` lifecycle; a `RoutingRunner`
design for per-execution WASM-vs-Podman routing (today's `build_broker()` picks one runtime
for the process's lifetime — routing per `ExecSpec` is new); a conservative allowlist-based
Pyodide package-compatibility check (deny-by-default, routes to Podman before execution, never
a retry-after-failure); explicit non-goals (`bash`/`node` stay Podman-only — Pyodide is
Python-only); open risks (Pyodide load cost, fuel/timeout tuning, allowlist staleness) flagged
as resolve-before-building; a rough 6-step build scope for whenever it's picked up.
Recommends staying unbuilt until exercised under real load — no urgency, since the Phase-4
Podman gate is fully closed (see the RESOLVED entry above) and nothing currently depends on a
second substrate.

**Owner-deferred:** none. **Carry-forward:** none — this is a future-optional upgrade, not a
gap; do not treat the unbuilt `WasmRunner` as pending work unless a real need for it shows up.

## Security & attestation track — Step 4: Vault integration, dev-mode/fake (2026-06-27, NOT a phase)

**Vault as a per-interaction runtime authorization layer** (`docs/design-notes/vault-runtime-auth.md`):
an agent never holds a real secret, only an ephemeral token minted by the supervisor and scoped to
a named role's policy; a token that doesn't cover a path is denied (`VaultPermissionDenied`) and the
denial itself is logged as a signal, not just noise (§6). Disabled by default — `get_secret(name)`
with no token is the env/Keychain path from Phase 0, completely unchanged.

**Naming note:** `config/loader.py` already had a `VaultConfig` for the owner's _note_ vault
(`VaultSync`/`VaultCatalog`/`VaultWatcher` — unrelated). Every new identifier at the config/module/
section layer uses "Secrets" instead to avoid the collision (`SecretsConfig`, `SecretsBackend`,
`config/secrets_backend.py`, `[secrets]`); class names that are unambiguously about HashiCorp Vault
itself still say so (`FakeVault`, `VaultClient`, `VaultPermissionDenied`).

**Built**

- `config/secrets_backend.py`: `SecretsBackend` Protocol (`mint_token`/`read_secret`); `FakeVault`
  (in-memory dev double — `policies: dict[role, frozenset[secret_name]]`, append-only `minted`/
  `denials` audit lists); `VaultClient` (real Vault via `hvac`, construction side-effect-free —
  `hvac` imported per-method, not in `__init__`, mirroring `edge/bridge/bridge.py`'s lazy `boto3`);
  `build_secrets_backend(config)` → `None` when `[secrets].enabled = false` (the default).
- `config/loader.py`: `SecretsConfig` (`enabled`, `addr`, `kv_mount`, `aws_mount`) + `[secrets]` in
  `config/defaults.toml`. `get_secret(name, token=None)` extended — `token=None` unchanged
  (env/Keychain); a real token routes through `build_secrets_backend()` and raises on disabled/denied.
- `scheduler/supervisor.py`: `Supervisor.secrets: SecretsBackend | None` field + `mint_token(role,
ttl="10m")` — the supervisor holds minting authority only, never reads what it mints a token for.
  Threading minted tokens into actual dreamer/curator/vault-sync call sites stays deferred to
  Phase 5 (agent factory + dispatcher) per the design note's own framing; this step only makes that
  wiring _possible_.
- `ops/import_lint.py`: `"hvac"` added to `NETWORK_MODULES`, no allowlist entry — flatly forbidden
  under `core/`. Covered by the existing blanket `test_core_has_no_forbidden_imports`; no new test
  needed for that guarantee specifically.
- `ops/vault/policies/{dreamer,bridge,research-airlock,advisor,correlator,supervisor,gate}.hcl` (7
  files) — the policy taxonomy from vault-runtime-auth.md §3, one path-stanza set per role.
  `ops/vault/README.md` mirrors `ops/attestation/README.md`'s structure: grant table, **NOT applied**
  warning, 6-step owner-operated production-application list.
- `pyproject.toml`: optional `secrets = ["hvac>=2.0"]` extra; `needs_vault` marker.
- Tests: `tests/fixtures/secrets.py` (`fake_vault()` helper over the policy taxonomy, mirrors the
  7 `.hcl` files exactly) + `tests/unit/test_secrets_backend.py` (7 — mint for known/unknown role,
  read in/out of policy, unknown token, two roles' overlapping grants stay scoped, env-fallback
  unchanged) + `tests/integration/test_supervisor.py` (+2 — `mint_token` returns a token scoped to
  the role; raises without a wired backend) + `tests/integration/test_secrets_backend_wiring.py`
  (4 — disabled-by-default → `None`; enabled wires a real `VaultClient` **with no hvac installed**,
  proving side-effect-free construction; custom addr/kv_mount picked up; `get_secret(token=...)`
  raises when disabled) + `tests/e2e/test_secrets_vault_live.py` (2, `@pytest.mark.needs_vault` —
  mint+read round-trips through a real dev-server; an out-of-policy read is denied by the real
  server, not just `FakeVault`; self-contained setup via the dev-mode root token, auto-skips with no
  reachable dev-server, same pattern as `test_sandbox_podman_live.py`/`test_research_live.py`).

**Verified**

- `ruff` clean; import-firewall **OK** (`hvac` confirmed blocked under `core/`, zero reach). Fast
  suite **301 → 316 collected, 313 passed** (+15 new: 13 pass here, 2 skip — no Vault dev-server in
  this environment, expected and correct); **3 total skips** (the 2 new + 1 pre-existing
  `test_dreaming_live` — model not pulled, unrelated to this step). **Integrity gate unchanged at
  25 passed** (this step didn't add structural-firewall tests; the import-lint addition is covered
  by the existing blanket test). No category double-marking.
- Caught and fixed two self-review issues before they shipped: `VaultClient.__init__` originally
  imported `hvac` eagerly, contradicting its own "side-effect-free construction" docstring claim —
  moved the import into `mint_token`/`read_secret` individually. A vacuous test assertion
  (`"hvac" not in sys.modules or True` — always `True` regardless of the left operand) was written,
  caught on review, and deleted rather than left in.

**Owner-deferred (you write code/policy-as-code; owner operates production Vault):** stand up a
Vault dev or production server, `vault policy write` each `ops/vault/policies/*.hcl`, enable the
kv-v2 and AWS secrets engines, create AppRole bindings, place `vault-supervisor-token` via
Keychain/env, set `[secrets] enabled = true`. Steps in `ops/vault/README.md`. Live-gate test
(`pytest -m needs_vault`) will then exercise the real path instead of skipping.

**Carry-forward:** threading minted tokens into real agent call sites (dreamer/curator/bridge) is
Phase 5 work, not a Step-4 gap — the design note scopes it there explicitly.

## Security & attestation track — Step 5: Vault↔attestation join (2026-06-27, NOT a phase)

**Joins the two subsystems built across this track** (Vault tokens, Step 4 ↔ signed attestation
records, Steps 2–3): every attestation has a `vault_token_accessor` field that has defaulted to
`""` since Step 2 (the record was built ready for this) — Step 5 populates it. The crux is a
security distinction (attestation-layer.md §2, vault-runtime-auth.md §6): a minted Vault token
comes with an **accessor** — a _non-secret_ audit handle that can look up a token's metadata or
revoke it, but **cannot authenticate or read any secret**. The attestation records the **accessor**
(tying an action to the Vault authorization it ran under), **never the token** (the credential —
Invariant 10). The accessor is already inside `signing_payload()`, so the authorization claim is
part of the signed, tamper-evident surface automatically. Same scope discipline as Step 4: build
the join primitive + prove its security properties; live token-threading through agents stays
Phase 5.

**Built**

- `config/secrets_backend.py`: `MintedToken(token, accessor)` frozen value object — a mint returns
  both (real Vault hands back `resp["auth"]["client_token"]` + `["accessor"]` in one response).
  `FakeVault.mint_token` now generates a distinct token AND accessor in **separate keyspaces**
  (`fake-token-*` vs `fake-accessor-*` — a token can't be used where an accessor is expected, nor
  vice versa) and adds `role_for_accessor(accessor)` (the dev-mode analogue of Vault's
  `lookup-accessor`: resolves an accessor → role _without_ the token — what makes the join
  verifiable). `VaultClient.mint_token` captures the real accessor. `SecretsBackend` Protocol +
  `Supervisor.mint_token` return `MintedToken`.
- `core/attestation/attestor.py`: `Attestor` Protocol + `StoreAttestor.emit` gained
  `vault_token_accessor: str = ""`, flowing into `Attestation.create`. Default `""` leaves every
  live emitter (Dreamer/Curator/VaultSync) **unchanged** — no live token threading yet (Phase 5).
- Tests: updated all Step-4 call sites to the new `MintedToken` return (`.token` for reads).
  `tests/unit/test_secrets_backend.py` (+1: token/accessor occupy separate keyspaces — accessor
  can't authenticate a read, token doesn't resolve as an accessor). `tests/integration/
test_supervisor.py` (mint test now also asserts `role_for_accessor(minted.accessor) == role`).
  `tests/integrity/test_attestation_vault_join.py` (new, +4, the non-skippable gate): emit records
  the accessor and the **token string appears NOWHERE** in the serialized attestation (the
  firewall); the accessor resolves back to the attested `agent_role` (verifiable join) and a forged
  accessor doesn't; the accessor is in the **signed** surface (swapping it breaks signature
  verification, mirroring the field-tamper test); the accessor is in the content-address (two
  actions differing only in authorization are distinct attestations).

**Verified**

- `ruff` clean; import-firewall **OK** (`hvac` still flatly blocked under `core/`, 4/4). Fast suite
  **316 → 321 collected** (+5: 1 unit, 4 integrity join). **Integrity gate 25 → 29 passed.** Full
  suite: of 321 collected, **all 318 non-skipped pass**, 3 skip (2 `needs_vault`, 1 `dreaming_live`
  — infra-gated, unrelated). ⚠️ One full-suite run showed `test_scheduler_live::test_supervisor_
dispatches_a_real_job` failing with `TimeoutError` — a **concurrency-induced model timeout**
  (I'd launched parallel `pytest` runs alongside the suite, starving the live Ollama dispatch); it
  **passes clean in isolation (55.89s)**, confirmed. Not a regression — Step 5 doesn't touch the
  dispatch path (only _added_ `mint_token` + a default-`None` `secrets` field). Lesson: don't run
  concurrent pytest against the live suite.

**Owner-deferred:** none new — the Step-4 Vault standup (above) is the same prerequisite; once a
real dev-server is up, `pytest -m needs_vault` exercises the real accessor round-trip too.

**Carry-forward:** live token+accessor threading through real agent dispatch (supervisor mints →
passes `.token` to the agent in context, records `.accessor` on the action's attestation) is
Phase 5, as scoped — the seam is now complete and proven; Phase 5 wires it into the live loop.

## Security & attestation track — Step 6: owner-operated runbook + live-validated (2026-06-27, NOT a phase) — TRACK COMPLETE

**The last step. Consolidates every owner-deferred production step across the track into one
owner-facing runbook**, and — because the owner had just installed Vault via Homebrew — actually
**validated the Step-5 join end-to-end against a real Vault server** (the dev-mode side of the
build/owner split, which is the build agent's to run; production standup remains the owner's).

**Built (docs)**

- `docs/runbook.md` → new **"Security & trust infrastructure (owner-operated)"** section, the
  single place the three component READMEs (`ops/attestation/`, `ops/vault/`,
  `cloud/terraform/airlock/`) already point to. Ordered, copy-pasteable, tailored to the owner's
  actual environment (Homebrew `vault` at `/opt/homebrew/bin/vault`, macOS Keychain via the
  `security` CLI, launchd, SSO `alberto-sso`): §0 Keychain bottom-turtle + a `run_with_secrets.sh`
  launch-wrapper snippet that injects hyphenated secret names via `env(1)` (not shell `export`)
  into the existing `get_secret`→`os.environ` path — no new code; §1 attestation keypair gen +
  Keychain placement + `[attestation] enabled` (fail-closed); §2 Vault — **2a dev-mode quick
  validation** (`vault server -dev` → `pytest -m needs_vault`) and **2b production** (Raft config,
  `operator init`, Keychain auto-unseal LaunchAgent, enable kv/aws, `vault policy write` each
  `ops/vault/policies/*.hcl`, per-role token roles, static secrets, `vault-supervisor-token`,
  `[secrets] enabled`); §3 AWS airlock `terraform apply` (Phase 8, account `054942746160`); §4 a
  full secret↔location↔reader↔scope table; §5 end-to-end verification commands. Notes the design
  note's Podman-container option vs the owner's Homebrew binary (equivalent, loopback either way).

**Built (code — surfaced by the live run)**

- `config/secrets_backend.py`: `VaultClient.read_secret` now passes `raise_on_deleted_version=True`
  to hvac's `read_secret_version` — pins current behavior and silences an hvac-v3 DeprecationWarning
  that only appeared once the call hit a **real** server. Exactly the kind of thing the FakeVault
  unit tests can't catch; the dev-mode validation earned its keep.

**Verified — the join, live against real Vault (not FakeVault)**

- Stood up a disposable `vault server -dev` on `127.0.0.1:8200` (in-memory, auto-unsealed, fixed
  dev root token; **torn down after** — no production init/unseal, no real secrets, no daemon left
  running). Installed `hvac` 2.4.0 into `.venv` (the `[secrets]` extra; doesn't affect the
  import-firewall, which scans `core/` source, not site-packages). **`pytest -m needs_vault` → 2/2
  PASSED** against the real server: a `dreamer` token mints (with a distinct accessor), reads its
  in-policy `kv/oura-daily-aggregates`, and is **denied** the out-of-policy `financial-readonly-key`
  by Vault itself — the same assertions `FakeVault` makes in the unit suite, now proven against
  `hvac` + real policy enforcement. Re-ran after the deprecation fix: clean, no warnings.
- `ruff` clean; import-firewall still OK (`hvac` installed but flatly blocked under `core/`). The
  16 secrets/join logic tests green. No production keys placed, `[secrets]`/`[attestation]` remain
  `false` — the live validation used only the disposable dev server + fake secret values.

**Owner-deferred (now fully documented in the runbook — the build/owner line held throughout):**
attestation keypair generation + Keychain placement + `[attestation] enabled`; production Vault
standup (init/unseal, engines, AppRole, `vault-supervisor-token`, `[secrets] enabled`); AWS airlock
`terraform apply`. All owner-operated; the build agent ran only the dev-mode validation.

**Carry-forward:** live token+accessor threading through real agent dispatch remains Phase 5 (the
seam is complete and now proven against real Vault). No track-level gaps remain.

---

### ✅ Security & attestation track COMPLETE (all 6 steps, 2026-06-27)

1. test reorganization · 2. attestation records (unsigned) · 3. attestation crypto (Ed25519) ·
2. Vault dev-mode integration · 5. Vault↔attestation join · 6. owner runbook + live validation.
   The runtime proof layer (signed, chained, content-addressed attestations) and the runtime
   credential-authorization layer (scoped ephemeral Vault tokens, accessor-not-token in the audit
   trail) are built, tested cold, and the Vault path is proven live. **Main build remains parked at
   Phase 8 complete — next is Phase 9 (Backups), untouched by this track.**

## Production Vault standup — scaffolding + token-role fix (2026-06-27, NOT a phase, owner-operated)

**Track is complete; this is the owner-operated production setup**, picked up because the owner had
installed Vault via Homebrew and wanted it standing before Phase 9. Owner chose full scope (kv +
AWS dynamic engine) + auto-unseal (Keychain + launchd). Build agent authored IaC + a correctness
fix + validated against dev Vault; the owner runs init/unseal/key-placement (held the line).

**Fixed (real correctness bug, surfaced by thinking about a _scoped_ supervisor)**

- `VaultClient.mint_token` now mints via the **token role** (`create(role_name=role,
policies=[role])`), not a bare `policies=[role]`. The bare form only worked in dev because the
  dev **root** token bypasses Vault's subset rule; a real _scoped_ supervisor token can't assign a
  policy it doesn't hold — and giving it those policies would let it _read_ the secrets, breaking
  "supervisor mints but cannot read" (vault-runtime-auth.md §3). The token role's `allowed_policies`
  is the authorizer instead. `ops/vault/policies/supervisor.hcl` → `auth/token/create/*`.
- New live test `test_scoped_supervisor_mints_but_cannot_read` proves it against real Vault with a
  **non-root** supervisor token: it mints a working `dreamer` token yet is denied the secret. The
  two existing live tests gained the token-role setup. **`pytest -m needs_vault` → 3/3** on a fresh
  dev server.

**Built (IaC — committed, owner-run; no secrets in any of it)**

- `ops/vault/vault.hcl` (Raft at `data/vault/raft`, loopback listener, `disable_mlock`+FileVault
  posture), `ops/vault/vault-unseal.sh` (launchd-managed server + auto-unseal from Keychain via
  `security`, `wait`s so launchd supervises the pair), `ops/vault/com.mind-palace.vault.plist`
  (RunAtLoad+KeepAlive, logs to `data/logs`, mirrors the watcher agent).
- `ops/vault/setup_policies.sh` (idempotent: enable kv-v2, write 7 policies, create 6 token roles)
  — **validated end-to-end** against `vault server -dev`: ran the real script, then a scoped
  supervisor minted a `dreamer` token through the real `VaultClient` and read the secret while the
  supervisor token itself was denied. `ops/vault/setup_aws_engine.sh` (Phase B: `aws` engine +
  assumed-role creds, TTL=1h — gated on the airlock IAM existing). `scripts/run_with_secrets.sh`
  (Keychain→env launch wrapper via `env(1)` for the hyphenated secret names).
- `ops/vault/README.md` updated with a scaffolding table + the short ordered standup; `docs/
runbook.md` §2 is the full guide. All `.sh` pass `sh -n`; plist passes `plutil -lint`.

**Verified:** `ruff` clean; logic suite **306 passed**; live **3/3** against dev Vault. `hvac` 2.4.0
in `.venv`. No production server stood up, no real keys placed, `[secrets]`/`[attestation]` still
`false` — all dev-mode/disposable.

**Owner-operated remaining (Phase A — do now):** run the standup from `docs/runbook.md §2b` /
`ops/vault/README.md` — init, place `vault-unseal-key`+`vault-root-token`+`vault-supervisor-token`
in Keychain, unseal, `setup_policies.sh`, load static secrets, install the LaunchAgent, set
`[secrets] enabled = true`. **Phase B (AWS engine):** after the airlock `terraform apply`, run
`setup_aws_engine.sh`. The build agent cannot place keys or init/unseal a production server.

## Production Vault standup — Phase A complete + live (2026-06-27, owner-operated, DONE)

Owner ran the full Phase A standup on the Mac: `vault server -config ops/vault/vault.hcl` →
`operator init` (1-share Shamir, single-user) → unseal key + root token in Keychain → unsealed →
`setup_policies.sh` (real run: kv engine + 7 policies + 6 token roles, matched the dev validation
exactly) → supervisor token (`auth/token/create -policy=supervisor`) in Keychain → LaunchAgent
installed (`com.mind-palace.vault.plist`) — confirmed **auto-unseal works**: after a fresh
`launchctl bootstrap`, `vault status` showed `Sealed false` / `HA Mode active` with no manual
unseal, log showed `core: post-unseal setup complete`.

**Build-side fix needed first:** `[secrets] enabled` only existed in the committed
`config/defaults.toml`, which a test pins `false` and which is now on a shared GitLab repo — no
clean way to turn it on for just this machine. Added a **gitignored `config/local.toml` overlay**:
`config/loader.py` `load_config()` shallow-merges it onto defaults section-by-section when no
explicit `path` is passed; `.gitignore` excludes `config/local.toml`. Created it here with
`[secrets] enabled = true`. Made the two defaults-dependent tests hermetic (assert the _shipped_
default directly via `load_config(_DEFAULTS)`, not the ambient `get_config()`) so they can't be
masked by a real local override — `tests/integration/test_secrets_backend_wiring.py`.

**Live-verified production path (real Vault, real Keychain, not dev-mode):**
`./scripts/run_with_secrets.sh ./.venv/bin/python -c "...build_secrets_backend()...mint_token('dreamer','10m')..."`
→ printed a real accessor; a follow-up `read_secret` round-trip on `kv/oura-daily-aggregates`
returned the seeded test value. Logic suite **307 passed** with the overlay active (secrets
ambiently enabled during the test run) — confirms the hermetic-test fix holds.

**State:** Vault live, auto-unsealing on login, minting scoped tokens via token roles, `[secrets]`
on for this machine only. Everything committed by the owner. **Phase A fully done.**

## Phase B — Vault AWS dynamic engine, live on production AWS (2026-06-27, DONE)

Owner chose full scope (kv done above + AWS dynamic engine now) over deferring to Phase 5/the
future server. Goal: the bridge gets short-lived (TTL=1h) AWS creds minted by Vault instead of a
static SSO profile — vault-runtime-auth.md §4.

**Design correction found by reading the real Terraform:** the role taxonomy's `airlock-role` has
no IAM counterpart — `cloud/terraform/airlock/iam.tf` only creates a `bridge` (assumable) role and
the fetcher's own Lambda execution role. Fixed `ops/vault/setup_aws_engine.sh` to configure
`aws/roles/bridge-role` only.

**Built:** `cloud/terraform/airlock/vault_engine.tf` — IAM user `mind-palace-vault` (Vault's AWS
engine `config/root`), policy scoped to `sts:AssumeRole` on the bridge role ARN only (no wildcard);
access key deliberately not created in Terraform (kept out of tfstate). `iam.tf` bridge trust
extended to include this user. `terraform fmt`/`validate` clean; plan reviewed before every apply.

**Owner applied live (account `054942746160`):** `aws sso login` → bootstrap + airlock
`terraform apply` (outputs confirmed: `airlock_bucket`, `bridge_role_arn`, `fetcher_function_name`,
`vault_engine_user_name`) → minted the engine's access key by hand → `vault write aws/config/root`
→ `setup_aws_engine.sh` → **`vault read aws/creds/bridge-role` returned real temporary AWS
credentials.** Dynamic engine live.

**⚠️ Security incident during setup (caught, remediated):** a real AWS access key + secret
appeared in the chat transcript (owner pasted literal values instead of placeholders into a `vault
write` command). Flagged immediately; blast radius was small by construction (the leaked
credential could only `sts:AssumeRole` on bridge-role, which itself can only PUT `requests/`/GET
`results/` on the airlock bucket — no corpus access, no IAM, nothing else) but it was rotated
immediately (`aws iam delete-access-key` + `create-access-key`) and confirmed only one key existed
afterward. Separately, a `secret-key=` (hyphen) vs `secret_key=` (underscore) typo had also caused
an earlier, unrelated `vault write aws/config/root` to silently half-apply — caught via the
resulting "access key or secret key were provided but not both" error, fixed by re-running with
the correct field name and the freshly rotated key.

**Self-rotation gap (build agent's oversight, fixed):** `vault write -f aws/config/rotate-root`
failed — `mind-palace-vault` had no `iam:GetUser`/`CreateAccessKey`/`DeleteAccessKey` on itself,
because its policy was deliberately scoped to assume-role-only without anticipating rotate-root's
self-management requirement. Asked the owner: widen narrowly vs skip. Owner chose to widen — added
a second statement to `vault_engine.tf` granting exactly those three actions, `resources` locked to
`aws_iam_user.vault_engine.arn` (itself only, never a wildcard). Plan verified `0 add / 1 change / 0
destroy` before the owner applied (the build agent's own attempt to `terraform apply` directly was
correctly blocked by the harness as an unreviewed production change — apply stayed owner-run, as
it should). After apply: `rotate-root` succeeded; the very next `aws/creds/bridge-role` read
failed once with `could not obtain sts client` (transient AWS IAM/STS propagation lag after two
back-to-back AWS-side changes — policy update, then key rotation); a ~30–60s wait + retry
succeeded. **No human has seen the live AWS key since** — Vault generated and holds it alone.

**State:** kv engine + AWS dynamic engine both live on production Vault; bridge-role mints
real expiring AWS creds; engine credential self-rotates. **Note on consumption (unchanged):**
the bridge itself still uses the static SSO profile — wiring it to mint from Vault instead is
Phase 5 work, not done here. **Phase A + Phase B both DONE.**

**Session ended here (owner out of credits).** Next: **Phase 9 — Backups** (restic → S3 +
SSE-KMS, scheduled; AWS sees no plaintext; BUILD-SPEC §16b) — fresh session, re-ground from this
file + CLAUDE.md + BUILD-SPEC §16b.

## Phase 9 — Backups (restic → S3 + SSE-KMS): code complete + gate verified (2026-06-27)

**The numbered phase.** restic → S3, client-side encrypted + deduplicated so AWS never sees
plaintext; SSE-KMS on the bucket for defense in depth; scheduled (BUILD-SPEC §16b, §18 gate).
Owner chose **full DR** (data + a consistent Vault raft snapshot). Architecture mirrors the airlock:
Terraform for the AWS side, a testable argv-builder for the restic invocation (like
`sandbox/policy.py`), a launchd runner, and a real round-trip test.

**Built**

- `cloud/terraform/backups/` — S3 bucket (private, **versioned**, TLS-only, **SSE-KMS** default via a
  customer-managed `aws_kms_key` with rotation), lifecycle (expire noncurrent versions + abort MPU),
  and a **dedicated** `mind-palace-backup` IAM user scoped to exactly this bucket + key. The user is
  deliberately **independent of Vault's AWS engine**: restore is the DR path and must work when Vault
  is sealed/down — a dependency on Vault (whose own state we back up) would be circular. Access key
  NOT created in TF (kept out of tfstate). `terraform fmt`/`validate` clean offline.
- `[backup]` config + `BackupConfig` (loader.py): repo URL, Keychain item names (password + AWS key —
  never the values), region, `vault_snapshot`, exclude globs, retention (keep daily/weekly/monthly).
  Off by default; enable per machine via the `config/local.toml` overlay.
- `ops/backup/plan.py` — `BackupPlan` + pure, deterministic argv builders (`init/backup/forget/
restore/check/snapshots`) and `ResticRunner` (subprocess; secrets via env, never argv). No password
  or AWS key can appear in argv by construction (no field carries one). `build_backup_plan()` backs
  up the note vault + the data dir, **excluding the live Vault raft store** (`<data>/vault`) — that's
  captured separately as a consistent snapshot the runner stages inside the data dir so it rides
  along. `ops/backup/run.py` — CLI the launchd wrapper drives.
- `ops/backup/backup.sh` (launchd-driven) — reads `restic-password` + the backup AWS key from
  Keychain into env; best-effort `vault operator raft snapshot save` (full DR; skipped if Vault
  sealed/no token); self-inits the repo on first run; `backup` → `forget --prune` → `check`.
  `ops/backup/com.mind-palace.backup.plist` (daily 03:30, missed-while-asleep fires on wake).
  `ops/vault/policies/backup.hcl` — least-privilege `sys/storage/raft/snapshot` read only (the
  backup token sees no secret value), auto-applied by `setup_policies.sh`.
- Tests: `tests/unit/test_backup_plan.py` (6 — argv builders deterministic + secret-free; plan
  excludes the live raft). `tests/e2e/test_backup_roundtrip.py` (`@pytest.mark.needs_restic`) — the
  gate, against a LOCAL restic repo (encryption is identical local-vs-S3): backup → restore →
  byte-compare, AND grep the repo for the plaintext → **absent** (AWS-sees-no-plaintext). `needs_restic`
  marker in pyproject.

**Verified — the Phase 9 gate, demonstrated cold**

- Installed `restic` 0.19.0 (brew — a real Phase-9 prerequisite, not throwaway). **`pytest -m
needs_restic` → 1/1 PASSED**: encrypted backup + restore round-trips; the repository's bytes
  contain no plaintext; `restic check` passes. ruff clean; import-firewall green (`ops/backup` is
  operational, not core — imports subprocess/shutil, no network lib). Logic suite **307 → 313
  passed** (+6 backup unit). `run.py` CLI plumbing + exit codes smoke-tested.

**Deployed live (2026-06-27, owner-operated):** `cloud/terraform/backups` applied for real —
`mind-palace-backups-054942746160` (S3, versioned, SSE-KMS) + the `mind-palace-backup` IAM user.
Access key minted by hand → Keychain (`backup-aws-access-key-id`/`-secret-access-key`, kept out of
tfstate); a generated restic repo password → Keychain (`restic-password`) + escrowed out-of-band;
`backup` Vault policy applied + a 768h orphan token → Keychain (`vault-backup-token`). `[backup]`
enabled in `config/local.toml` (the repository line had briefly landed under `[secrets]` by mistake
— moved to its own `[backup]` block, see `config/local.toml`). First real run: `vault operator raft
snapshot save` succeeded, restic **initialized the live S3 repo** and backed up 1083 files / 26.756
MiB (19.238 MiB stored after dedup/compression) → snapshot `fbb9935a`, `forget` applied retention,
`check` found no errors. Restore-verify (`restore latest` to a scratch dir) confirmed byte-for-byte
recovery from S3. LaunchAgent installed (`launchctl bootstrap` + a manual `kickstart -k`) and
confirmed via `data/logs/backup.out.log` — daily 03:30 going forward.

**Two operator slips caught + fixed live (worth noting for future deploys, not code bugs):**
(1) `setup_policies.sh` was run from inside `cloud/terraform/backups` (left over from the apply
step's `cd`) — relative path resolved wrong, "no such file or directory"; fix was `cd` back to the
repo root. (2) the `restic_repository` terraform output was pasted under `[secrets]` instead of a
new `[backup]` section in `config/local.toml`, so `backup.sh` ran (vault snapshot succeeded) but then
correctly refused with "no `[backup]` repository configured" rather than silently doing the wrong
thing. Both are runbook/sequencing footguns, not bugs in `ops/backup/` — the fail-closed config
check did its job.

**Phase 9 — code, gate, AND live deploy all COMPLETE.** Main build: Phases 0–9 fully done (+ the
security/attestation track + production Vault + AWS airlock, all live). Next numbered phase:
**Phase 10 — Self-modification loop** (the last + most dangerous; propose/approve/execute gate, safe
levers, validate against rolling baseline + frozen golden set + Constitution, auto-rollback;
BUILD-SPEC §18). Fresh session for it.

<!-- Append new phase entries below as you complete each one. -->

## Phase 10 — Self-modification loop (the last phase): code complete + gate verified (2026-06-28)

**The final numbered phase.** propose→approve→execute→validate→rollback (BUILD-SPEC §14/§15/§18).
Owner's scoping steer this session, which SHAPED the design: for now the loop may tune **knobs**
(dream/alignment parameters, system weights) and nothing else; **infrastructure and code are an
extremely privileged resource the loop must not write**; feature-flag anything risky.

**The safety property, made STRUCTURAL (not a runtime check):** the entire self-modifiable surface
is a registry of bounded numeric config knobs (`ops/levers.py`). A `ProposedChange` is a
(lever-name, numeric-target, rationale) value object with NO field that can carry a path / diff /
command / code / TF plan — so a code or infrastructure change is not a proposal the loop can even
_construct_ (the same move as `ResearchCriteria` having no field for note content). A unit test
asserts the field set is exactly `{lever, target, rationale}` and intersects no forbidden name —
adding a code/infra lever later would be a visible, reviewable diff that breaks that test.

**Built**

- `ops/levers.py` — the lever registry = the whole writable surface. Seeded with the `[dreaming]`
  knobs whose hard bounds defaults.toml already documented (σ∈[0.55,0.75], near-dup≥0.90,
  min_cluster_size∈[2,6], max_clusters∈[4,16]). `Lever.validate` is fail-closed: out-of-bounds
  RAISES, never silently clamps. `ProposedChange.resolve()` validates before anything reaches the
  ledger.
- `ops/ledger.py` — durable SQLite `ProposalLedger` (the Phase-10 upgrade of gate.py's in-memory
  `HumanGate`). Lifecycle is an FSM enforced in the store so §14 ordering can't be skipped:
  PROPOSED→APPROVED/DENIED→EXECUTED→VALIDATED/ROLLED_BACK; every transition asserts its precondition
  (can't execute the un-approved, validate the un-executed, resurrect a denied/validated one).
  Records prior-overlay (NULL = "loop introduced the key") for an exact rollback, validation
  metrics, rollback reason, optional attestation-id join. `check_same_thread=False` + RLock
  (matches AttestationStore/JobQueue idiom).
- `ops/apply.py` — the reversible execute/rollback primitive. Writes ONLY a machine-owned
  `config/levers.toml` overlay (gitignored), never the owner's hand-authored `local.toml`. Atomic
  replace; deterministic emit; `overlay_set` returns the exact prior so `overlay_restore` reverses
  with no residue (restores a value, or removes a key the loop introduced).
- `config/loader.py` — `[selfmod]` + `SelfModConfig` (two fail-closed switches: `enabled` master,
  `unattended_enabled` for the no-human path — both OFF). Overlay precedence is now
  **defaults ← levers.toml ← local.toml** (a `_overlay()` helper), so a human knob in local.toml
  always WINS over a loop-tuned one (human authority supreme). `refresh_config()` drops the cache so
  an executed knob takes effect without a restart.
- `ops/selfmod.py` — `SelfModLoop` ties registry+ledger+apply+validator. `validate` builds a
  `ops/gate.GateDecision` from the FROZEN golden anchor (capability) + the rolling baseline (acute
  drift) and lets `gate_admits(...)` decide mechanically; deny → restore prior overlay → ROLLED_BACK.
  `conforms` (behavioral) stays HONESTLY DEFERRED — `gate_admits` omits it, not stubs it True, exactly
  as ops/gate documents. `build_golden_validator(retriever,...)` is the default (injectable, mirrors
  eval.golden's Retriever seam). **Unattended safe-lever path (`apply_unattended`) is built but
  FLAG-OFF**: refuses unless `enabled` AND `unattended_enabled`, and the lever must be in an explicit
  `SAFE_LEVERS={dream_max_clusters}` (a workload cap, can't touch authored data). Auto-approval is
  recorded as approver='unattended' (auditable).
- `ops/selfmod_cli.py` — the owner's front door: `list|history|show|propose|deny|approve`. `approve`
  = approve→execute→validate against the live golden anchor (ingests the self-contained fixture
  corpus through the real embedder); keeps or reports the auto-rollback. Reads work even with
  `[selfmod]` disabled; state-changing commands go through the loop's fail-closed gate.

**Verified — the §18 Phase-10 gate, demonstrated**

- `tests/integration/test_selfmod.py` IS the gate: a good change traverses propose→approve→execute→
  validate and is KEPT (overlay shows the tuned knob); a deliberately-bad change AUTO-ROLLS-BACK
  (overlay restored, no residue); the **boiling-frog** case — validator reports
  drift_within_tolerance=True (rolling happy) but golden_non_regressing=False (FROZEN anchor caught
  it) → still denied → rollback, reason cites the frozen anchor not drift; master switch + unattended
  switch both fail-closed by default; out-of-bounds refused before the ledger; execute requires
  approval. Plus the default validator wired to the REAL frozen baseline (passes on no-capability-harm,
  flags a real recall drop). `test_ledger.py` FSM (illegal transitions refused, durable across reopen),
  `test_levers.py` (bounds + the structural firewall), `test_levers_overlay.py` (precedence: levers
  changes the effective knob; local.toml wins; no overlay → committed defaults), `test_selfmod_cli.py`.
  **Logic suite 313 → 350 (+37)**. ruff clean; import-firewall green (ops is operational, may import
  core; core still reaches no network/edge/cloud).

**Owner-operated to ACTIVATE (deliberately deferred — fail-closed by default):** the loop ships OFF.
To use it on a machine, set `[selfmod] enabled = true` in `config/local.toml`, then drive the gate
with `python -m ops.selfmod_cli` (propose/list/approve/deny). `unattended_enabled` stays off unless
the owner deliberately turns it on. **NOT auto-wired into cron** this session: nothing autonomously
proposes knob changes yet — the proposer side (e.g. the watchdog suggesting a σ nudge from telemetry)
is a future, equally-cautious wiring. The gate, anchors, and reversibility exist; unleashing an
autonomous proposer is a separate decision.

**Phase 10 code + gate COMPLETE. ALL TEN NUMBERED PHASES (0–10) DONE.** The system is built: sealed
core, ingest/matching/dreaming/curator, scheduler+budgeter, agent factory+gate, sandbox, edge
interface, research airlock (live), encrypted backups (live), production Vault + attestations (live),
and now the gated/validated/reversible self-modification loop. Remaining is operational/optional:
activate `[selfmod]` when desired, wire a cautious proposer, Phase 6b voice (§20.11), and the
still-pending empirical `-m podman` sandbox check (docs/runbook.md → "Sandbox runtime").

---

## Forward layer (Track items, not numbered phases)

### F9 — dreamer output-quality suite, real binding (Track F)

**Status:** COMPLETE (2026-06-28). Item spec: `design-notes/dreamer-quality-suite-evaluation.md`
(adopt) + `ROADMAP-V1.md` Track F. Bind the signal-vs-noise / apophenia suite to the LIVE
Dreamer/DerivedStore and run it. No flags flipped; no live/R&D code changed.

**Built**

- `tests/fixtures/dreamer_adapter.py` — `MindPalaceDreamerAdapter` binding the suite's
  `DreamerAdapter` protocol to the live machinery: real `Dreamer.clusters()` over a `MirrorView`
  (authored-only, structural), real `cluster_notes`/`note_centroids`/`similarity_matrix`, real
  `grounding_score` + `core.recursion`. Only the embedder + synthesizer are deterministic offline
  stand-ins (the real ones need Ollama; the quality layer grades structure, not prose). `run()` =
  fast clustering→Dreams; `persist_dreams()` = full live `dream()` into a real `DerivedStore`;
  `run_without_grounding()` = the decorative-citation negative control. NO `rate_blind` (value
  claim stays honestly open). `LexicalEmbedder` = offline, similarity-PRESERVING (the shipped
  `FakeEmbedder` hashes whole strings → useless for clustering); per-batch presence vectors,
  clustering threshold tuned to 0.50 (single-linkage is chain-prone on lexical vectors; 0.50 is
  the stable band where noise can't bridge themes AND calibration has ≥6 dreams).
- **Resolved the open `g` question (review note 2 / §4) IN THE BINDING:** confidence
  `c₀ = g·(1+λ(|Agr|−1))` with `g = grounding_score · cohesion · size_factor` — folds in support
  COUNT (`size_factor = min(1,(n−1)/4)`), so a 2-note cosine-1.0 coincidence scores weak (the
  apophenia failure in miniature). The live adjudicator's `g = grounding_score` (resolvability
  only) would make confidence flat and FAIL calibration — exactly what the suite is built to flag.
  Reports the base confidence c₀ (depth-uniform live run, d=1 = `AUTHORED_LEAF_DEPTH`); γ^d
  cross-depth decay is the recursion/drift suite's job (binding-seam note 3). **NOT changed in the
  flag-OFF `core/dreaming/adjudicator.py`** — recorded as a deferred R&D follow-up (runbook Hook 2).
- `tests/quality/test_dreamer_quality.py` (the adopted contribution) — `_load_adapter` →
  parametrized `adapter` fixture over `[ref]` + `[real]`, so the whole suite runs against BOTH the
  reference fake and the real binding; env `MIND_PALACE_DREAMER_ADAPTER` still forces one. Adopted
  ruff-clean (mechanical, behavior-preserving). `THRESH` left as the tuning surface (untouched).
- `tests/quality/test_real_dreamer_binding.py` — end-to-end proof the binding reaches the real
  Dreamer AND DerivedStore: full `dream()` persists INTERPRETED-only, `derived_from` = authored
  leaves (G2), grounded self-check passes, fast `run()` ⇄ persisted grounding agree, idempotent,
  deterministic. `tests/quality/conftest.py` + `quality` marker (pyproject).

**Verified**

- `tests/quality/`: **22 passed, 4 skipped**. Real binding `[real]`: 9 pass + 1 skip
  (`beat_decoys_under_blind_rating` — `rate_blind` unwired = value claim honestly OPEN). The 2
  drift-deferred tests skip (need A1; move to `longitudinal/` then). Calibration `[real]`: 7
  grounded dreams, top−bottom precision margin = 1.0; noise max-conf 0.25 (≤0.70); planted recall
  1.0; real ≥ TF-IDF baseline; paraphrase stability 1.0.
- Full logic suite **372 passed, 4 skipped** (non-quality unchanged at 350 — no regressions; F9
  adds +22 quality). ruff clean (incl. the adopted file); import firewall (I2) green; core reaches
  no network. Everything deterministic (fixed seeds) → green is stable.

**Owner-deferred (build/owner boundary; documented in runbook → "Dreamer output-quality suite")**

- **Hook 1:** wire `rate_blind` to a periodic blind-rating ritual — the ONLY path that validates
  the value claim. A green proxy is not a proven value-claim; keep it open until the rating runs.
- **Hook 2:** fold support count into the adjudicator's `g` when the C1/R2 R&D path is activated
  (a deliberate R&D session — not now; flag stays OFF).
- Optional full-fidelity run against the real Ollama embedder (`needs_models`) = the THRESH
  harness-tuning step.

**Next:** owner picks the next forward item. Per ROADMAP-V1 ordering, **A1 (the drift gauge)** is
the keystone — it unblocks R3/C2 recursion AND F4 drift-trajectory asserts (and would unlock F9's
two drift-deferred tests). Track B (the Ambassador) is the other high-value parallel.

### A1 — the drift gauge (Track A, the keystone)

**Status:** COMPLETE (2026-06-29, same session as F9 — owner said "continue"). Item spec:
`design-notes/alignment-subsystem.md` §2/§5 + BUILD-SPEC §15 + gap **G4**. Realize the §15 drift
metric `D(t)=d(μ(s_t),B)`. **Closes G4** (was OPEN). Detection only — alters no live behavior
(self-mod is flag-OFF).

**Two owner decisions (asked, not guessed — `AskUserQuestion`, 2026-06-29):**
- **Metric:** one-sided L2 deterioration distance — each axis contributes only its bad-direction
  deviation past baseline, normalized by a blessed per-axis tolerance, combined by L2; healthy
  improvement = 0 drift; Constitution-fingerprint mismatch = hard trip (D=∞).
- **Θ:** ship **Θ=1.0**, blessed in `baseline.json`, F4-calibrated-then-re-blessed. A human-set
  frozen fixed point — excluded from the lever set (structurally: levers only tune `[dreaming]`).

**Built**

- `eval/drift.py` — the gauge: `Profile` (μ = capability rates ⊕ Constitution conformance, G4's
  "rates ⊕ conformance vector"), `Axis` (flat + additive so A2 appends structural axes as data),
  one-sided `deterioration()`, `drift()` (L2 + the conformance hard-trip), `DriftReport`,
  `constitution_intact()` (live fingerprint vs blessed; no-blessed ⇒ intact, no false trip),
  `drift_from_report()` (reuses one golden report) + `measure_drift()` (standalone entry for the
  A2 report / F4 harness). Reuses `eval.golden` + `core.constitution.constitution_fingerprint`.
- `eval/golden/baseline.json` — extended with a blessed `drift` section (per-axis tols, Θ=1.0,
  the Constitution fingerprint `1818a46e…`). Owner-blessed/frozen, never auto-modified (I9);
  `load_baseline()`/`regressions()` untouched (backward-compatible).
- `ops/selfmod.build_golden_validator` — `drift_within_tolerance` is now the REAL gauge
  `D(Δ·s) ≤ Θ` (`drift_from_report`), the honest realization of the gate's drift conjunct (G4/G5),
  replacing the rolling-regression stand-in (now retained as advisory `metrics`). Self-mod flag-OFF
  ⇒ no live behavior change.
- `docs/WHITEPAPER-FORMAL-PROPERTIES.md` — **G4 OPEN → CLOSED** with the realization.

**Verified**

- `tests/unit/test_drift.py` (15) + `tests/property/test_drift_property.py` (3 Hypothesis:
  D≥0, within⇔D≤Θ, at-or-better⇒0, monotonic) + `tests/integration/test_selfmod.py` (+1: the gate
  conjunct is the real gauge). Gauge behaviors proven: at-baseline D=0; healthy improvement D=0
  (one-sided); one-tol drop D=1.0=Θ (within, boundary); 2-tol D=2.0 (out); L2 combine = √2;
  Constitution breach D=∞ (hard trip regardless of perfect capability).
- Full logic suite **372 → 391 passed (+19)**, 4 skipped. ruff clean (whole tree); import firewall
  (I2) green (eval may import core; core still reaches no network).

**Owner-deferred / next:** Θ is a placeholder until **F4** calibrates it on observed curves (then
re-bless in `baseline.json`); re-bless the Constitution fingerprint whenever `CONSTITUTION.md` is
amended (runbook → "Alignment drift gauge"). A1 now unblocks **R3/C2** (recursive dreaming),
**F4** (drift-trajectory asserts), and F9's two drift-deferred tests (move them to
`longitudinal/` when F4 lands). Natural next: **A2** (structural detection + the alignment report,
extends μ) or **F4** (uses the gauge), or Track B (Ambassador).

### Track B — the Ambassador (the Voice), END TO END (B0–B5 + cross-cutting)

**Status:** COMPLETE (2026-06-29; owner override: build the whole track in one session so the owner
can start talking to the system — one-item-per-checkpoint suspended for Track B only). Notes (in
precedence order): `ambassador-as-reasoning-agent.md` (authoritative), `ambassador-interpretation-and-flow.md`,
`nervous-system-and-ambassador.md` §4. **No feature flags flipped** (dream R&D OFF, self-mod fail-closed
OFF — untouched); nothing auto-activates (the CLI is the surface; the scheduled daemon is a runbook
follow-up). The Ambassador is **core-side, reaches no network** (verified: no `core/`|`agents/` → `edge`).

**Built**

- **B0 — the §1 provenance split (the structural decision already made — executed, not re-derived).**
  `core/provenance.py`: `AUTHORED` → `AUTHORED_SOLO` + `AUTHORED_DIALOGUE`, add `CURATED`;
  `MIRROR_READABLE = {AUTHORED_SOLO, AUTHORED_DIALOGUE}` (curated/observed/interpreted excluded —
  matches the formal spec). Blast radius exactly as mapped: `ingest_note` is now provenance-PARAMETRIC
  (default `AUTHORED_SOLO`); `catalog.py` DDL default + `record` default `authored-solo`; `core/mirror.py`
  unchanged (derives from `MIRROR_READABLE`). `VectorStore.relabel_provenance` + `VaultCatalog.relabel_provenance`
  (delete-then-add / UPDATE; idempotent) back `scripts/migrate_provenance_split.py` (dry-run default,
  `--apply`, same-trust-tier relabel — NOT a §8-firewall promotion, so safe + ungated).
- **B3 — `core/ops_view.py` `OpsView`** (read-only operational introspection): binds ONLY the *read*
  callables of the attestation store + proposal ledger + drift gauge — no `approve`/`deny`/`append`/
  `mark_*` on its surface (static + guard tier; honestly weaker than MirrorView's structural copy, and
  labelled so). `narrate()` renders status in plain language with NO internal nouns (tier/job/queue/
  credentials), the §4 register; `_drift` is optional (drift not computed per-chat).
- **Capture + curated.** `core/ingest/dialogue.py` `DialogueCapture.capture()` stores the owner's
  message as `AUTHORED_DIALOGUE` through the SAME pipeline as vault ingest (parametrized provenance —
  not a bespoke writer), mirror-readable + retrievable, idempotent, attested (`action=capture`).
  `core/ingest/curated.py` ingests CONSTITUTION/CONVENTIONS/`docs/**` as `CURATED` (own graph, never
  the mirror — `curated ∉ MIRROR_READABLE`); the "explain yourself" path is a deliberate, non-default
  `Librarian.retrieve(provenances={CURATED})`.
- **B2/B5 — `agents/ambassador/`** (the reasoning agent, pinned tier; persistent first-class role,
  DELIBERATE empty scope — no `run_python`, no write — expressed as a `RoleTemplate` so the §10 ceiling
  guards it). `intent.py`: deterministic floor (RETRIEVE/EXPLAIN/STATUS/TASK/CAPTURE) + model-earned
  fallback, separately testable ("floor for the obvious, mind for the rest"). `agent.py`: the five
  paths — RETRIEVE (mirror) / EXPLAIN (curated) / STATUS (ops-view, no model) / TASK (gate→queue +
  effort narration) / CAPTURE (store + ack); B5 = context assembled through the §13 `Budgeter` every
  turn (agent chooses ContextParts, budgeter enforces the window); grounding self-checked, ungrounded
  answers flagged-not-hidden; per-step attestations; in-memory recent-history (older context re-retrieved
  from `authored-dialogue`, no double-store). `policy.py`: effort narration (pure fn, no leaks) +
  earned-interruption policy (off|earned_only|verbose, default earned_only; expected updates always
  delivered, unprompted gated). `[ambassador]` config + `AmbassadorConfig`.
- **B1 — wiring + CLI.** `scheduler/router.py`: `ambassador` kind → pinned tier @ REACTIVE,
  `ambassador_task` → synthesis @ background. `scheduler/interface.py`: inbox-drain + delegated-task
  handlers, the `task→gate→queue` delegation closures (the Ambassador never imports the scheduler —
  injected), and `ConversationRuntime`/`build_conversation_runtime` (the in-process driver).
  `core/interface.build_core_inbox` rewired to the Ambassador (lazy `agents` import — no load-time
  cycle, no layering inversion). `scripts/talk.py` (REPL, `--offline` deterministic mode = the
  verification + day-one surface), `scripts/ingest_self_knowledge.py`.

**Verified**

- Full logic suite **391 → 436 passed (+45)**, 4 skipped — no regressions. New: integrity
  (`test_provenance_split` 7, `test_ops_view` 4, `test_curated_firewall` 3), unit (`test_ambassador_intent`
  9, `test_ambassador_policy` 4), integration (`test_dialogue_capture` 3, `test_ambassador` 10,
  `test_ambassador_budget` 3, `test_ambassador_conversation` 2 = the DoD as a test). Integrity gate **43**
  green; import firewall (I2) green; ruff clean tree-wide; existing split-touched tests relabeled.
- **Actually ran it** (the "interact meaningfully" bar): `scripts/talk.py --offline` drives a real
  multi-turn conversation — retrieve (grounded, cited), explain (curated), status (plain narration),
  task→deferred result on the next turn, capture → the exchange lands as `authored-dialogue` and
  surfaces on a later retrieval (capture loop confirmed live, not just unit-tested).
- Env note: the venv was rebuilt mid-session (uv.lock appeared) and lost pytest/ruff; reinstalled both
  to verify. Run tests via `.venv/bin/python -m pytest`.

**Owner-deferred (build/owner boundary)**

- ⚠️ **Run the provenance migration** — `scripts/migrate_provenance_split.py --apply` (runbook →
  "Provenance spectrum split"). The dry-run found **918 legacy `authored` vector rows + 135 catalog
  rows** in live data; until relabeled they are NOT mirror-readable, so the live mirror reads empty.
  Idempotent; restic snapshot is the safety net.
- Run `scripts/ingest_self_knowledge.py` (needs Ollama) so EXPLAIN answers from the real docs.
- Optional: the Tailscale-reachable local HTTP front end (lean: left as a runbook note — the CLI meets
  the bar without an exposure decision); the scheduled-daemon wiring (handlers exist in
  `scheduler/interface.py`, not enabled).

**Next:** owner picks. Track B done unblocks daily use. Natural neighbors: **A2** (structural detection
— extends the drift μ the ops-view can already narrate) or **F1–F3** (the harness). Per-category
interruption sensitivity is a documented future extension (single dial shipped).

### Operational lifecycle (`palace` launcher) + fresh-start (owner-requested, not a track item)

**Status:** COMPLETE (2026-06-29). Owner asked for (a) a one-command start/stop for the whole system
and (b) a clean wipe + re-point to a new Synctrain-over-Tailscale notes location. Both done.

**Built**

- `ops/lifecycle/` + `scripts/palace.py {start|stop|status|reset}` — the whole mind-palace as ONE
  supervised process (supersedes the standalone `scripts/watch.py` / `com.mind-palace.watch`).
  `runs.py` = a run ledger (`data/runs.sqlite`) pinning each run to its **git commit** + dirty flag +
  clean/unclean shutdown. `preflight.py` = ensure-own + **verify-externals fail-closed** (Ollama
  `version()`, Vault `/sys/health`, podman `which`; required ✗ refuses start, optional = warn) —
  owner's chosen scope (manage own; verify, don't manage, the external daemons). `launcher.py`:
  `start` (preflight → record run → catch-up vault sync / empty-cache rebuild → supervise queue +
  watcher, with vault_sync + dream/curate + the delegating Ambassador inbox + `ambassador_task` all on
  one supervisor) with a **graceful SIGTERM/SIGINT shutdown hook** (drain at a job boundary → mark run
  clean — the ASG-lifecycle-hook analog); `stop` (signals the live run's pid); `status`; `reset` (the
  surgical corpus wipe). **Recovery mode** on an unclean prior run (scheduler halted, read-only;
  `--force` resumes) — the boot-time half of the A4 tamper response. launchd plist
  `ops/lifecycle/com.mind-palace.palace.plist` (owner installs; `ExitTimeOut=120` drain window).
- **Self-mod persistence answered + documented** (owner's question): tuned knob value →
  `config/levers.toml` overlay (a file, not a db — `local.toml` always wins; delete = revert); the
  propose→validate→rollback history → existing SQLite `data/selfmod_ledger.sqlite`; a restart re-reads
  the overlay and resumes. The new run-ledger correlates a tuned knob to the commit/run it happened on.

**Verified**

- `tests/integration/test_lifecycle.py` (10): run-ledger clean/unclean detection (the recovery basis),
  preflight fail-closed aggregation, launcher start→serve→mark-clean (fakes, no models), recovery on
  unclean prior + `--force` resume, and **`reset` wipes the corpus but NEVER `data/vault`** (Raft) — the
  load-bearing guard. Logic suite **436 → 446 (+10)**; ruff clean; preflight green against the live box
  (Ollama 0.30.7, Vault health 200, podman present).

**Executed (operational, owner-requested)**

- `[vault] path` → `~/.mind-palace/vault/janus_notes` (config/local.toml) — ingest scoped to exactly
  the new synced subdir. Retired the old `com.mind-palace.watch` LaunchAgent (superseded). Ran
  `palace reset --confirm`: **hard-wiped the corpus** (raw + vectors + catalog + stale attestation chain
  + queue = 9 paths); **production Vault Raft, ledgers, telemetry, backups untouched** (the guard held);
  restic daily snapshot is the recovery net. A fresh re-ingest writes `authored-solo` natively → **the
  provenance-split migration is now MOOT** (no `--apply` needed).

**Owner-deferred / next**

- ⚠️ Re-export your real notes into `~/.mind-palace/vault/janus_notes/` + point Synctrain there, then
  `palace start` (re-ingests as authored-solo). `janus_notes/` still has 2 leftover 7–9 byte test stubs
  from 06-27 — delete them (or let Synctrain reconcile) so they aren't ingested as junk.
- Optional: install `com.mind-palace.palace.plist` for an always-on daemon; run
  `scripts/ingest_self_knowledge.py` so the Ambassador's EXPLAIN path has the curated docs.
- Future: a real cron cadence for dream/curate (currently a coarse in-loop interval); the full A4
  graduated tamper response (this is the boot-time recovery half); a final-snapshot shutdown hook
  (the `on_shutdown` seam is present, default off).

### Wiring audit + sandbox finalization (owner-requested, not a track item)

**Status:** COMPLETE (2026-06-29). Owner asked for a deep-dive on what's actually wired (fear of
built-but-dangling parts), to finalize the code-exec sandbox/WASM + libraries + data-piping, and to
clarify the watcher/process model.

**Deep-dive audit → `docs/WIRING-AUDIT.md`** (durable map: WIRED / DANGLING / FLAG-OFF for every
subsystem). Confirmed the fear is partly real. **DANGLING** (built+tested, no live driver):
(1) dreams/curator findings are generated but never *surfaced* to the owner; (2) no agent
autonomously *uses* the sandbox (the factory/run_python is built but undriven — Track D correlator);
(3) the research airlock has no live driver; (4) Vault scoped tokens are mintable but unthreaded;
(5) no auditor reads the attestation chain back (A3); (6) no remote gateway daemon (talk.py is the
surface). All six are self-contained next-steps, documented with recommended fixes.

**Finalized the sandbox (Track E E1/E2 + the owner's libs/data asks):**
- **E1 closed** — podman runs here (libkrun machine); `pytest -m podman` **7/7** (added data-in +
  vault-unreachable-with-inputs). Isolation now proven empirically, not just by construction. The
  stale "KNOWN ISSUE" runbook section marked RESOLVED.
- **Data-piping** — `ExecSpec.inputs` (name→text, 16 MB cap, name-safe) materialized at
  `/tmp/input/<name>` by `policy.compose_program` IN-BAND on stdin (NO host mount → the vault stays
  structurally unreachable; asserted). `run_python` tool + the new `scripts/sandbox.py` CLI thread
  it through. Verified live: a CSV piped in, summed in-sandbox → 42.
- **Libraries** — `ops/sandbox/Containerfile` (numpy/scipy/pandas/scikit-learn/cryptography) +
  `scripts/build_sandbox_image.sh`; `[sandbox] image` selects it (owner builds once; default stays
  slim so a fresh clone works). Wheels baked in → sandbox needs no network at run time.
- **WASM (E2)** — `WasmRunner` is now a REAL wasmtime/WASI implementation (was a NotImplementedError
  stub) + `RoutingRunner` (wasm for pure-compute python when available, else the verified podman);
  fail-closed `available()`. `[sandbox] runtime` ∈ {podman, wasm, routing} + `wasm_module`. wasmtime
  installed; activation needs an owner-placed `python.wasm` (documented). Isolation by absence of
  syscall imports — no preopens/sockets granted.
- **OS-health "agent" wired** — the `Watchdog` (built but never called) now runs in the palace serve
  loop: feeds `mem.available_gb` (psutil) + raises a low-headroom flag (sense + report; the loader
  already refuses ceiling-breaching loads). Closes a dangling end the owner named.

**Watcher/process-model clarification:** "retired the watcher" = booted out the *duplicate*
standalone `com.mind-palace.watch` LaunchAgent (else two watchers double-ingest). The watcher code
+ function live on, now *managed by* palace (started in serve, stopped in the graceful hook) — which
IS the thin-supervisor model the owner described. Agents (ambassador/dreamer) are in-process config
per BUILD-SPEC ("agents are config, not OS processes"), not separate daemons; Vault/Ollama are
external daemons palace verifies. No code change needed — palace already starts everything + tears
it down gracefully on stop.

**Verified:** logic suite **446 → 456 (+10)**: data-piping (`test_sandbox_policy` +6), WASM/routing
(`test_sandbox_wasm` +7), health-check wiring (`test_lifecycle`), minus overlap. podman e2e 7/7.
ruff clean tree-wide; import firewall green. Deps added to `.venv`: wasmtime (+ earlier pytest/
hypothesis/ruff after the mid-session venv rebuild). Owner command quick-reference added to the top
of `docs/runbook.md`; sandbox/WASM section added.

**Next (owner picks):** the six DANGLING items in `WIRING-AUDIT.md` — highest-value is surfacing
dreams (small) and the Track D correlator (the autonomous sandbox driver, the owner's IoT example).

---

## Forward layer — knocking out the DANGLING frontier (2026-06-29, owner override: multiple wins)

Owner steer: confirmed the thin-master/supervised-children runtime model (palace stays the master;
network-facing components become supervised child processes — forced by Invariant 2 + the model
ceiling, not a style choice); wants a small dashboard reachable over Tailscale; "knock out these
small but significant wins." Doing the self-contained core wins first, then the edge process.

**Win 1 — Surface dreams (WIRING-AUDIT DANGLING #1).** The dreamer/curator wrote `interpreted`
artifacts that nothing ever *showed*. New `core/dreams_view.py` `DreamsView` (read-only over the
`DerivedStore`, the OpsView move — binds `all`/`count`, no `add`/`reset` on its surface); a 6th
Ambassador intent `DREAMS` (`agents/ambassador/intent.py` cues + classifier line) → `_reflect_dreams`
→ `narrate_recent()`, **mirror-not-oracle** (frames dreams as the system's interpretation, cites the
spanned authored notes in [[brackets]], hands judgment back — §III.2 / §8 firewall). Wired in
`build_ambassador` (`derived=` injectable). Tests: `tests/unit/test_dreams_view.py` (+5, incl.
no-mutator guard), intent cases, `test_ambassador.py` DREAMS path (+2; deterministic, no model, not
captured, attested read). RETRIEVE stays mirror-only — firewall intact.

**Win 2 — Thread Vault scoped tokens into dispatch (DANGLING #4).** The §2 lifecycle primitives all
existed (`Supervisor.mint_token`, `get_secret(name, token)`, `Attestor.emit(vault_token_accessor=)`,
`FakeVault`); the glue did not. `MintedAgent` now carries `token` (off the prompt — `repr=False`,
never in `build_context`) + `accessor` (audit handle) + `grant()` + a **code-only** `read_secret(name)`
(the orchestration calls it; the model never sees the token — credentials are deliberately NOT a tool,
PRE_DECLARED_MAX unchanged). `AgentFactory` mints+binds+attests-the-accessor for a role in
`grant_roles` (fail-closed empty; `[secrets].grant_roles`/`token_ttl` config; `build_factory` wires
the backend+attestor only when `[secrets]` enabled). `read_secret`→`get_secret(name, token)` so the
agent holds only the token; Vault enforces scope (denied = opaque). Tests:
`tests/integration/test_factory_credential_grant.py` (+6) prove in-scope read, out-of-scope denial
(logged), ungranted/no-backend = no token, accessor-attested-not-token, token off prompt+repr.
Mechanism is now live end-to-end; its first *consumer* is the Track D correlator (Win 4) — owner
opts a role into `grant_roles` to activate (recommended `["correlator","advisor"]`).

**Verified (Wins 1–2):** logic suite **456 → 470 (+14)**; ruff clean (core/config/tests); import
firewall green (the two new core modules reach no network/edge). No flags flipped.

**Win 3 — the edge monitor process (DANGLING #6 + the dashboard).** The thin-master/child model the
owner confirmed, realized: palace stays the master and now spawns a SEPARATE child process for the
network-facing surface (forced by Invariant 2 — it can't share the sealed core). New `edge/monitor/`
(`server.py` = `MonitorApp` routing + `render_dashboard` + a `_Server` that skips `getfqdn`;
`page.py` = the HTML/CSS/JS asset): `GET /` dashboard + `GET /status.json` + `POST /chat`. It reads a
core-emitted snapshot file and relays chat over the existing interface handoff — **never imports core,
never reads a store**. Core side: `ops/lifecycle/snapshot.py` (`build_status`/`write_status` — METADATA
only: health, activity *shape*, queue depth, mem, dream counts; no note text). Supervision:
`ops/lifecycle/children.py` `Child` (injectable spawn; idempotent start; graceful SIGTERM→SIGKILL);
the launcher starts children in `_serve`, restarts a dead child, writes the snapshot every
`snapshot_interval_s` (5s), and drains children on the graceful shutdown. `scripts/monitor.py` is the
entry palace spawns (Zone B → deliberately NOT sealed). `[monitor]` config (OFF by default; bind
`host` to the Tailscale IP for the phone — the tailnet is the auth boundary). Tests: `test_children.py`
(+4), `test_monitor_server.py` (+5), `test_monitor_snapshot.py` (+2, incl. no-corpus-leak + chat
round-trip through a real handoff), `test_lifecycle.py` (+1, child start/stop + snapshot). **Real bug
found + fixed:** `HTTPServer.server_bind()` calls `socket.getfqdn(host)`, a reverse-DNS lookup that
hung **35s** on a DNS-less host — would stall `palace start`; `_Server` skips it.

**Verified (Win 3):** logic suite **470 → 482 (+12)**; **live HTTP smoke passed** (real socket: GET /
renders metrics, GET /status.json, POST /chat round-trips through the handoff → reply); ruff clean
tree-wide (asset lines isolated in `page.py` via a scoped per-file E501 ignore); import firewall green
(core still reaches no edge — the monitor is edge-only). No flags flipped (`[monitor]` off by default).

**Session total:** 456 → 482 (+26). DANGLING #1/#4/#6 closed; three remain (sandbox-driver, airlock
driver, auditor) and collapse toward the **Track D correlator** capstone.

**Next:** Win 4 — Track D correlator (autonomous sandbox driver + Apple Health `OBSERVED` ingest +
the de-identified airlock question). Owner prep: export Apple Health (`export.zip`→`export.xml`); to
use the dashboard now, set `[monitor] enabled=true` + `host=<tailscale-ip>` and `palace start`.

---

## `mind-palace` on PATH (2026-06-30, owner-requested, not a phase)

`bin/mind-palace` (new, executable): a bash shim that resolves its own real location (follows the
symlink), derives `REPO_ROOT` from that, so it works from any cwd without relying on `$PWD` (every
`scripts/*.py` already resolves its own paths from `__file__`, confirmed by tracing
`config.loader.REPO_ROOT`). Symlinked at `/opt/homebrew/bin/mind-palace` (already on PATH,
user-writable, no sudo). Initially just `start`/`stop`/`status`/`reset` → `palace.py`.

**Same day, follow-up ("I don't want to have to find those specific scripts every time"):** turned
it into a full dispatcher — a `case` statement covering every owner-facing script in `scripts/`
(`talk`, `monitor`, `sandbox`, `ingest`, `ingest-self-knowledge`, `migrate-provenance`, `purge-raw`,
`gen-attestation-keys`, `verify-attestation`, `check-imports`, `run-with-secrets`, `eval`,
`build-sandbox-image`, `keep-awake`, `watch` — `watch` prints a deprecation note pointing at `start`
before running). `start|stop|status|reset` keep the verb in argv (palace.py's own dispatch expects
it); every other verb is stripped before exec (the target script doesn't expect its own name as
argv[0]). `mind-palace help`/`-h`/`--help`/no-args prints the full table; an unknown verb exits 2 with
the same usage on stderr. **Real pre-existing bug found + fixed:** `scripts/check_imports.py` was
missing the standard `sys.path.insert(0, …)` repo-root line every sibling script has — it threw
`ModuleNotFoundError: No module named 'ops'` even run the old way (`./.venv/bin/python
scripts/check_imports.py` from the repo root, since Python puts the *script's own dir* on
`sys.path[0]`, not cwd). Fixed by adding the same path-insert line as every other script; verified
`mind-palace check-imports` now passes (`ops.import_lint`'s own `python -m` entry point, used by CI,
was never affected). **Verified:** `bash -n` syntax-clean; ruff clean (`bin/mind-palace` has no
extension so `ruff check .` correctly skips it — confirmed CI's actual invocation is unaffected);
full logic suite still 482/482; live-tested `status`/`sandbox`/`check-imports`/`verify-attestation`/
unknown-verb from `/tmp` in a fresh `zsh -l` shell. `docs/runbook.md` quick-ref + lifecycle section
updated throughout to `mind-palace <verb>`.

---

## Mathematical reframing — Prompt R0: notation wiring (2026-07-01, documentation only, zero runtime risk)

The first step of the companion-IV reframing (`docs/MATHEMATICAL-REFRAMING.md` §B.6 step 1–3, 5):
propagate the shared vocabulary. **Pure documentation — no code logic changed**; only comment
headers were added to code files. The five-families account (companion IV) now has a single glossary
and every load-bearing boundary states its object/invariant/enforcement in place.

**Built (5 deliverables):**
1. **`docs/NOTATION.md`** (new) — the one glossary: symbol ↔ code name ↔ object ↔ family, for every
   load-bearing symbol (ρ, π_MR, 𝒜, MAX, H, Σ, c, g, d, γ, λ, D(t), B, Θ, 𝔎, K_σ, ℋ, δ\*δ), grouped
   by family, plus a supporting-notation table (MR, μ, Δ/s/s′, G/G_now, |Agr|, Cit/Ret). **Referenced
   from the top of all six whitepapers** (I, technical, II, III-math, III-build, IV). Family 5 symbols
   are marked **NOT YET BUILT** honestly (`core/complex/` does not exist; `ℋ` is only *seeded* today by
   `derived_from`).
2. **Boundary docstring headers** (companion IV §B.4) — the three-line `OBJECT / INVARIANT / ENFORCED`
   comment header on each family 1–4 boundary: `core/mirror.py` (π_MR), `core/provenance.py` (ρ),
   `core/stores/derived.py` (interpreted DAG), `ops/gate.py` (the gate FSM), `scheduler/queue.py`
   (queue lifecycle), `eval/drift.py` (D(t)), `core/research/criteria.py` (π_public), and the factory
   scope `core/factory/roles.py` (𝒜/MAX). Placed above the module docstring (comments don't disturb
   `__doc__` — verified). **Honest residuals recorded inline** where enforcement is weaker than the
   invariant: G11 (mirror guards data not the handle), G9 (authored-leaf by-convention), G5 (`conforms`
   absent, not stubbed), and liveness-not-safety on the queue. Notation does not outrun enforcement.
3. **Companion II regrouped by family** — `WHITEPAPER-FORMAL-PROPERTIES.md`'s flat I1–I13 catalog is now
   read under the five family headings (A.1 labelings/flow: I1–I7,I11,I13; A.2 derivation: I9,I10;
   A.3 automata: I8,I12; A.4 metric: the D(t)/G4 obligation; A.5 complex: not-yet-built). Every row's
   formal statement, tier, and discharge is **verbatim-preserved** — only the grouping is new;
   cross-family invariants filed under their primary family with a cross-ref.
4. **Design-note family tags** — a one-line `*Family tag → …*` at the top of all **20** design notes,
   each pointing back to `NOTATION.md`; genuinely cross-cutting notes (holistic-testing, roadmap,
   test-organization) tagged "cross-cutting" honestly rather than forced into one family.

**Verified:** full logic suite **unchanged at 482 passed / 4 skipped / 19 deselected** (green before
and after — the ratchet held); ruff clean tree-wide; import firewall green (core reaches no
network/edge); all 8 module docstrings intact after the comment headers; all 18 required symbols in the
glossary; all 6 whitepapers reference it; all 20 design notes tagged. No flags flipped; no behavior
changed.

**Next (companion IV §B.6):** step 4 — **the small type moves** (each a reviewed, tested,
behavior-preserving diff): `derived_from` → the hyperedge junction, the `c`-clamp as the single
definition of confidence, and the signed-edge polarity enum. Then step 6 — **family 5** (`core/complex/`
+ Dreamer loop v2 per companions III, Track H) behind the `DreamerAdapter` seam, flag-OFF, trough-only.
The DANGLING correlator capstone (Track D) and the A3 auditor remain from the wiring frontier.

---

## Mathematical reframing — Prompt R1: the three small type moves (2026-07-01, behavior-preserving)

Companion IV §B.6 step 4: three reframings that each **delete an illegal state** (the
`MirrorView`/`ProposedChange` move, §B.1). No behavior change; each verified by tests. Full logic
suite **482 → 498 (+16)**, ruff clean, import firewall green.

**Move 1 — the hyperedge junction (`core/stores/derived.py`).** The derivation hypergraph ℋ
(companion III §1.2–§1.3) is now a normalized **junction**: `hyperedges` (one `derives` B-arc per
artifact, `DERIVES` rel_type) + `hyperedge_nodes(role ∈ {tail, head})`, with a first-class
`Hyperedge(edge_id, head, tails: frozenset, rel_type)` type. Each derivation is head κ + tail set
supp(κ); today every head-set has size 1. **Additive + behavior-preserving:** the `derived_from`
JSON column stays as the denormalized projection feeding the `Artifact` API and O(1) traversal;
`add()` writes both together via `_write_hyperedge` and they never drift; `_backfill_hyperedges`
(one-time, idempotent) migrates a pre-junction DB from the surviving column; `reset()` clears the
junction too. **Acyclicity-at-insert is unchanged** (still guards on `derived_from` before any
write). New read accessors `hyperedges()` / `tails_of(head)` are what family 5 (`core/complex/`)
will consume. Tests (+7): typed-roles populate, junction == derived_from (as a set), no-edges ⇒
no-hyperedge, exactly {tail,head} roles stored, idempotent re-add leaves no stale tails, reset
clears it, backfill from a simulated pre-junction store.

**Move 2 — the single confidence clamp (`core/recursion.py` + adjudicator).** `claim_confidence(depth,
grounding, agreement, gamma, lam)` is now **THE** definition: `c = min{1, γ^d·g·(1+λ(|Agr|−1))}`.
`decay_bound` stays the depth-decay *ceiling* γ^d·g (I10); `claim_confidence` multiplies in the
bounded corroboration bonus and applies the **min{1,·} clamp**. The adjudicator no longer assembles
the bonus itself (`core/dreaming/adjudicator.py` calls `claim_confidence`), so **no path can produce
c>1 or a depth-rising c** — closing the companion III §7.2 clamp tension. **Provably a no-op today:**
the R0 panel has 4 distinct methods (agreement ≤ 4), d=1, γ=0.5 ⇒ raw product ≤ 0.65 < 1, so the
clamp changes nothing currently produced (unit test asserts `claim_confidence == old assembly` on
those inputs; the dream-R&D and quality-determinism tests confirm end-to-end). Property tests (+2,
Hypothesis over d≤20, agreement≤50, λ≤2, γ∈(0.01,0.99)): **c ∈ [0,1]** and **c non-increasing in
depth** — the clamp bites when agreement/grounding would push the product past 1. Unit tests (+4):
equals-unclamped-today, clamps-above-one, agreement-is-a-multiplier-not-a-vote (g=0 ⇒ c=0),
rejects illegal inputs.

**Move 3 — the signed-edge enum (`core/complex_types.py`, new leaf module).** Closed value-sets are
now types, not free ints/strings: **`EdgeSign`** (`IntEnum`, SUPPORT=+1 / CONTRADICT=−1 — the value
*is* the ±1 the signed-Laplacian arithmetic and the `edges.sign` column use; deletes the illegal
`sign=3`/`0` state; a non-edge is an absent row, not sign 0) for the Prompt-H1 `edges` table, and
**`HyperedgeRole`** (`StrEnum`, tail/head) used by move 1's junction now. Leaf module, stdlib-only
imports, no network (firewall green). Tests (+3, new `tests/unit/test_complex_types.py`): ±1 values
usable in arithmetic, {tail,head} membership, out-of-set values rejected.

**Verified:** logic suite 498/498 (+16 new: derived +7, recursion +4, complex_types +3, properties
+2), ruff clean tree-wide on touched files, import firewall green (the new `core/complex_types`
reaches no network/edge), acyclicity + all prior derived-store/adjudicator behavior unchanged. No
flags flipped; dream R&D still OFF.

**Next (companion IV §B.6):** step 6 — **family 5** (`core/complex/` build.py/laplacian.py/… + the
Dreamer loop v2 per companions III, Track H, Prompt H1) behind the `DreamerAdapter` seam, flag-OFF,
trough-only; the `edges` table + `EdgeSign` land there. Then the DANGLING correlator capstone
(Track D) and the A3 auditor.

---

## Track H — Prompt H1–H3: the reasoning-complex core (2026-07-01, new code behind the seam)

The foundation of the strong Dreamer — the object, the principled clusterer, rigorous
contradiction (companions III §1–§2). All in a new **`core/complex/`** package (Zone A, model-free,
deterministic, import-firewall green). **New dependencies:** `scipy` (sparse Laplacians + partial
eigensolves) and `scikit-network` (Louvain cross-check) — the offline compute libs BUILD §2.2 adopts;
both compute-only (not networking), declared in `pyproject.toml`.

**H1 — the object.** `core/stores/edges.py` `EdgeStore`: the typed/signed **edges** table (the fiber
(t, w, s, τ), BUILD §1.2) using the R1 `EdgeSign` enum — the persistent home for polarity the cosine
graph can't carry (chiefly contradiction); idempotent content-ids; negative-strength refused; sign is
the closed ±1 set. `core/complex/build.py` `build_complex(view: MirrorView) -> ReasoningComplex`:
nodes + weighted cosine backbone A (symmetric, zero-diag, w≥0) + signed adjacency A_signed (= A until
a persisted contradiction edge overlays −w) + derivation hyperedges (from the `DerivedStore` junction,
touching these authored nodes). **The constructor takes a `MirrorView`, so a non-authored complex is
unrepresentable** (I6 structural — the firewall is the input type).

**H2 — the operator + the clusterer.** `core/complex/laplacian.py` (L = D−A, L_sym = I − D^{-1/2}AD^{-1/2},
signed L̄ = D̄ − A_signed). `core/complex/spectral.py`: `fiedler` (λ₂ + vector), `diffusion_map`
(heat-weighted bottom eigenvectors of L_sym via **`scipy.sparse.linalg.eigsh`**, fixed ARPACK start
⇒ deterministic; dense-`eigh` fallback for tiny/near-full components and on ARPACK non-convergence),
`spectral_labels` (per connected component, eigengap-selected k, NJW row-normalized `kmeans2` with a
fixed seed), and **`diffusion_cluster_notes`** — a drop-in for `cluster.cluster_notes` (same signature
+ `Cluster` return) that dissolves single-linkage chaining (§2.2). Plus `louvain_labels` (scikit-network,
deterministic `random_state=0`) — the second, modularity-based method for the §2.3 cross-check.
**The clusterer is pluggable behind the seam, not the default:** `Dreamer.clusterer` (defaults to the
Phase-7 single-linkage — **behavior unchanged**) and `MindPalaceDreamerAdapter.clusterer` +
`build_diffusion_dreamer_adapter()`. Flipping the default is a deliberate later step (like a flag), not
taken here.

**H3 — rigorous contradiction.** `core/complex/balance.py`: `signed_spectrum` (λ_min(L̄), the global
dissonance proxy — 0 ⇔ balanced, Hou/Kunegis), `frustrated_triangles` (odd-negative triangles — the
*specific* unresolved tensions, O(#△)), `frustration` → (λ_min, triangles). Replaces the 0.1 draft's
deferred contradiction judge with structure.

**Verified:** logic suite **498 → 518 (+20)** — `test_complex` (build/Laplacian/clusterer/Fiedler/Louvain,
+8), `test_edges_store` (+5), `test_complex_properties` (determinism, spectral stability, frustration
correctness, +4), `test_diffusion_clusterer` (+3). **F9 non-regression through `MindPalaceDreamerAdapter`
passes: diffusion planted-signal recall (1.00) ≥ lexical baseline (1.00) and clears the F9 bar; noise
max-confidence 0.10 ≤ 0.70 ceiling.** Balance enumerates a planted frustrated triangle. ruff clean
tree-wide; import firewall green (`core/complex/` reaches no network/edge — scipy/sknetwork are
compute-only); the default single-linkage path and the whole existing quality/binding suite are
**unchanged**. No flags flipped; dream R&D still OFF; live cron dreamer still uses single-linkage.

**Next:** flip the diffusion clusterer to the live default (a deliberate adoption step, once tuned on
the real Ollama embedder's cosine statistics — §2.2 notes σ can drop), then the deferred instruments
(curvature/topology/SBM/support = the rest of the strong-Dreamer pass, companion III §7) and the
Dreamer loop v2. Then the DANGLING correlator capstone (Track D) and the A3 auditor.

---

## Track H — Prompt H4–H7: the structural interpreters (2026-07-02, new code behind the flag)

The Dreamer now has real things to reason over: bridges, holes, alignment, themes-with-confidence —
four new `core/complex/` instruments, each surfaced as a thin `Claim`-emitter in the R0 panel
(BUILD §3.2 "each interpreter is a thin adapter over a `core/complex/` function"). All deterministic,
model-free, flag-gated (`[dream_rnd] enabled=false` — `run_panel` still refuses by default; the live
cron Dreamer is untouched). New dep: **`ripser`** (BUILD §2.2's adopted persistence backend; imported
lazily inside `topology.persistence` — it drags plotting libs never used at module import).

**H4 — `core/complex/curvature.py`.** Augmented Forman–Ricci (`Ric_F = 4 − deg(u) − deg(v) + 3·|△|`,
computed on the σ-graph's support; O(#△), exact) + `most_negative_edges` (emission rule: κ ≤ 0, or
only the minimum-κ edges when all are positive — never the whole graph; deterministic tie-break).
**The panel's `bridge` lens upgraded from the local-clustering proxy to this instrument** (companion
III §3.2's own framing: the proxy's principled replacement) — one claim per most-negative edge,
support = the two linked notes. Ollivier–Ricci stays optional/ungated-out (§3.1), NOT built. The one
pinned proxy test (`data["focus"]`) updated to assert the same planted intent (G1 carries every
bridge) against the new instrument.

**H5 — `core/complex/topology.py`.** `cosine_distance_matrix` + Vietoris–Rips persistence via ripser
(the flag complex K_σ, §4.1) + `long_lived_holes`: H₁ features with lifetime ≥ `hole_min_persistence`,
each completed into a **cycle witness** (representative cocycle edge + BFS path at the birth scale —
the notes circling the hole; documented as a witness, not the unique minimal cycle). The `hole` lens
surfaces them as **gaps, never contradictions** (§4.2 correction held in code and statement text —
dissonance stays routed through `balance.py`/signed edges).

**H6 — `core/complex/cut.py` + the A2 drift axes.** `conductance` (Φ(S) = w(∂S)/min(vol S, vol S̄)),
`min_conductance` (worst community over the deterministic spectral partition — the echo-chamber
axis), `grounding_cut` (min cut = max flow from an interpreted artifact to the authored leaves
through its derivation refs; unit-capacity per ref, fixed-point-scaled integers for scipy's
`maximum_flow`; multi-hop chains bottleneck correctly), `alignment_snapshot(K) → {frustration,
min_conductance}`. **`eval/drift.py` extended additively (A2):** `Profile` gains optional
`frustration`/`min_conductance` (default None), `DriftConfig` gains declared tolerances
(`frustration_tol=0.25`, `conductance_tol=0.10`; readable from baseline.json's `drift` section), and
`drift()` appends the axes **only when both the measured value and a blessed baseline key exist** —
a profile without them produces exactly the pre-A2 drift (proven by test). Rising frustration and
falling conductance are deterioration; improvement stays 0 (one-sided).

**H7 — `core/complex/blocks.py`.** Light degree-corrected **Poisson SBM** (mean-field VEM, ~130
lines per the BUILD §2.2 disposition): deterministic init from the diffusion embedding (fixed-seed
kmeans2), fixed iteration budget, ICL/BIC-style model selection (Karrer–Newman objective −
½·[k(k+1)/2]·ln W − ½·(k−1)·ln n; a **declared engineering penalty validated on planted graphs**,
not a derived MDL bound — stated honestly in the docstring). Returns hard labels + the n×k
**posterior** + the model-selected k. The `theme` lens emits one claim per non-singleton block with
membership confidence and the **spectral cross-check** (`k_sbm` vs `k_spectral`, `counts_agree`) —
§6.3's line held: the posterior organizes the graph, never certifies a thought.

**Wiring.** `core/dreaming/interpreters.py`: new `StructuralContext` (one shared complex at σ +
the unthresholded distance matrix, built once per pass from the MirrorView — non-authored claims
unrepresentable) + `STRUCTURAL_INTERPRETERS` registry {bridge, hole, theme} run by `run_panel`
alongside the σ-graph lenses. Three new `[dream_rnd]` tunables (declared bounds, G7):
`bridge_top_k=5`, `hole_min_persistence=0.15`, `sbm_k_max=8`. **Package-init cycle broken**: 
`core/complex/{build,spectral}` now lazy-import `core.dreaming.cluster` (the panel consumes the
instruments, not vice versa; `core.dreaming.__init__` eagerly pulls the panel).

**Verified:** logic suite **518 → 533 (+15)** — `test_structural_interpreters` property suite (+6:
planted-bridge curvature sign incl. closed form, persistence bottleneck-stability under ≤ε jitter,
grounding-cut monotonicity + chain bottleneck, SBM recovery k∈{2,3,4} at ≥0.95 co-membership +
blockless-graph k=1), `test_structural_panel` (+3: planted ring hole surfaced-as-gap-never-
contradiction, two concerns with posterior + cross-check, firewall/support-authored), drift A2
(+6: axes-absent ⇒ exactly pre-A2 D, axes appear, rising frustration/falling conductance trip,
one-sided improvement, `alignment_snapshot`→Profile→drift end to end). ruff clean tree-wide;
import firewall green; **no flags flipped** (dream R&D OFF; live path untouched).

**Next:** the remaining strong-Dreamer pieces — `support.py` (noisy-OR multi-path grounding, §6.1),
the `tension` lens (needs a contradiction detector to assert `contradicts` edges), `temporal.py`
(structural snapshots feeding the A2 axes live), then the Dreamer loop v2 assembly (BUILD §3.1).
Then the Track D correlator capstone and the A3 auditor.

---

## Track H — Prompt H8–H9: support propagation, temporal self-watching, the loop v2 (2026-07-02)

The strong Dreamer is now ASSEMBLED end to end — multi-path support, the system watching its own
structure evolve, and the BUILD §3.1 ten-step pass — all behind the existing dream-R&D hard
boundary (`[dream_rnd] enabled=false`; **the live `dream()`/cron path is byte-for-byte untouched**,
proven by test). No new flag: the loop v2 is the productionization of the R0/R1 engine that flag
already gates; flipping it live remains a deliberate owner step.

**H8 — `core/complex/support.py` (noisy-OR, §6.1).** `noisy_or` (1 − Π(1−s_p)),
`support_scores` (memoized topological sweep over the derivation map — exact on the polytree,
linear, cycle-defensive), and the adjudicator feed **`grounding_with_support`**: per evidence ref a
*path strength* (authored → 1, interpreted node → its DAG-combined noisy-OR, unresolvable → 0),
aggregated by **mean** — deliberately NOT a noisy-OR at the evidence level, so one good citation
cannot carry nine junk ones (adjudication-not-voting held; padding test proves it). **Equals the
flat `grounding_score` exactly whenever no ref is an interpreted node** — today's only live case —
so R1's clamp law and every existing adjudication are numerically untouched (Hypothesis property +
unit equality tests). `adjudicate()` gains the optional `support_of` seam (default None = flat
score, unchanged); interpreted parents earn partial credit only once recursion exists.

**H9 — `core/complex/temporal.py` (§5.4).** `compute_snapshot(K, distances=…)` → the BUILD §1.2
invariants (β₀, Fiedler λ₂, frustration, mean Forman, frac-negative-curvature, SBM count,
min-conductance, H₁ count — NULL, not a fake 0, when the distance matrix isn't supplied) +
`SnapshotStore` (DuckDB, own file beside the derived store; append-only; `trajectory(metric)` with
an allowlisted column set → the F4 time-series input; `latest_structural()` → the A2 axes dict).
Drift wiring completed additively: `drift_from_report`/`measure_drift` gain optional
`structural=…` passthrough → `Profile` → the A2 axes; snapshot→drift proven end to end.

**The loop v2 (`Dreamer.dream_v2`, BUILD §3.1).** 1 BUILD 𝔎|_MR (one shared complex, persisted
edges overlaid) → 2–5 LOCATE/THEME/TENSION/GAPS (`collect_claims` — the un-gated core factored out
of `run_panel`, now including the **tension lens**: frustrated triangles from asserted
`contradicts` edges, honestly empty on an all-support graph) → 6 SUPPORT (noisy-OR over the
DerivedStore's derivation map) → 7 ADJUDICATE (confidence-ordered; c=0/no-evidence candidates never
earn the model) → 8 SYNTHESIZE (**the only model seam** — one call per stored dream, each grounded
in its candidate's authored evidence, mirror-not-oracle; call-count == stored-dream-count asserted)
→ 9 STORE (interpreted-only, `derived_from` = authored leaves, `dream_pass_v2` attestation, data
carries confidence/methods/statement/loop=v2) → 10 MEASURE (snapshot appended when a store is
injected). `Dreamer` gains optional `edge_store`/`snapshots` fields (defaults None — every v1
construction unchanged).

**Real bug found + fixed (ARPACK):** the fixed start vector `v0 = ones/√n` IS the exact kernel
eigenvector of a balanced all-positive component's L̄ (and of L_sym on regular components) —
Lanczos breaks down on an exact-eigenvector start (ARPACK error −9, surfaced by Hypothesis).
Fixed in `balance._lambda_min` + `spectral._bottom_eigen`: a normalized *ramp* start + dense-exact
fallback on any ARPACK failure. **Semantics fix alongside:** `signed_spectrum` is now the **max
over connected components** of λ_min(L̄) — the raw global λ_min is the *min* over components
(block-diagonal L̄), so one balanced domain or a single isolated note would mask a frustrated
triangle elsewhere; a dissonance detector must register tension anywhere (docstring states it;
every prior balance property still holds).

**Verified:** logic suite **533 → 552 (+19)** — `test_support` (+7: noisy-OR math, polytree
exactness, unresolvable-refs, flat-equality, interpreted-parent partial credit, padding gate,
cycle-defensive determinism), `test_temporal` (+4: planted invariants, contradiction raises
frustration + NULL-h1 honesty, DuckDB roundtrip/trajectory/allowlist, snapshot→drift end to end),
`test_dream_v2` (+7: flag-off refuses, end-to-end store/provenance/confidence/methods, synthesis-
only-model-seam call count, confidence-ordered + earned, tension fires on an asserted
contradiction + gauge sees it, two-pass trajectory, determinism, v1-untouched), flat-equality
Hypothesis property (+1). ruff clean tree-wide; import firewall green; **F9 + the whole quality/
binding suite green and untouched**; no flags flipped.

**Next:** the owner's deliberate adoption steps — flip `[dream_rnd]` for a live v2 R&D session
(and/or wire `dream_v2` + snapshots into the cron dream job in place of v1), tune the diffusion
clusterer on the real Ollama embedder, and bless `frustration`/`min_conductance` baselines into
`eval/golden/baseline.json` once real snapshots exist. Then the Track D correlator capstone and
the A3 auditor.

**Live-model verification (same day, owner asked "real models, not mocked?").** The honest split:
the logic suite substitutes ONLY the two model seams (embedder + synthesizer — injected
deterministic stand-ins); all stores and the entire structural/reasoning layer are the real code
(model-free by design). The `-m live` tier runs real Ollama: executed now — **7 passed / 1 skipped
(3m45s)** on the real `qwen3-embedding:4b` + generation tiers (librarian/factory/scheduler/golden/
research/semantic-search/ollama). The one skip = v1 dreaming synthesis (`qwen3.6:27b` synthesis
tier not pulled; embedding/router/routine/stretch all pulled). **Gap closed:** new
`tests/e2e/test_dream_v2_live.py` — the full loop v2 with real models, same synthesis-tier skip
convention as v1 (will run the moment the 27b is pulled). **And proven today** via a one-off
stretch-tier smoke (`qwen3.6:35b-a3b`, pulled): real embedder → panel (density+theme corroborated)
→ adjudication (confidence 0.55 = the clamp law exactly) → real 35b narration, grounded [[cited]],
self-check PASSED → INTERPRETED store (loop=v2) → snapshot written (frustration 0.0,
min_conductance 1.0). To exercise both committed live dreaming gates: `ollama pull qwen3.6:27b`
(~17 GB), then `pytest -m live`.

## Forward layer — READ-ONLY AUDIT: prompt/Constitution integrity vs tamper & injection (2026-07-02)

**Audit performed, nothing built** — pure investigation per the owner's mandate; no code/test/config
changed; deliverable is `docs/audits/prompt-integrity-audit.md` (the single new file). Cited test
subset re-run this session: 94/94 pass (adversarial + integrity + constitution/budget/factory units +
attestation-store/ambassador integration). Live `CONSTITUTION.md` hash verified == blessed anchor.

**Per-gap verdicts** (evidence + minimal-missing statements in the audit file):
- **G1 CLOSED** — fingerprint = SHA-256 of raw `CONSTITUTION.md` only (`core/constitution.py:31`), lru-cached at process start; nothing else is in the hash.
- **G2 OPEN** — no call site hashes the assembled prompt (`agents/ambassador/agent.py:147` et al.); only the Constitution has an identity.
- **G3 OPEN** — no pre-dispatch gate anywhere; fingerprint recorded post-hoc in attestations; the blessed-anchor comparison runs only in the (OFF) self-mod validator/eval, not the live loop (`ops/lifecycle/launcher.py:144`, preflight has no fingerprint check).
- **G4** — assembly code / skill defs (dormant) / ambassador context output: NOT covered; scope grants: structural tool ceiling covered, `[secrets].grant_roles` config unhashed; retrieved chunks: partial (digests attested, text never re-verified against digest).
- **G5 PARTIAL** — record/store/crypto/verifier faithful to attestation-layer.md, BUT signing OFF in this deployment (records-only, unsigned); minor drifts: `signer` outside signed payload, `att_output` index never built.
- **G6 PARTIAL** — interactive Ambassador IS attested live (read/propose/capture, wired via launcher), but no prompt/output hashes; classifier + Agent/MintedAgent.respond calls unattested.
- **G7 PARTIAL** — injection-as-content + firewall + ceiling all structural, tested, passing, hash-free; missing the model-facing half (adversarial note through retrieval → non-obedience assert, holistic-testing §1c second half).
- **G8 CLOSED** — vault does no prompt hashing and nothing expects it to (capability only).
- **G9** — extra gaps: blessed check never scheduled at runtime; RAG chunks enter as role:"system"; `ContextParts.constitution` override seam; committed pubkeys are dev keys w/ seeds in repo + signing off ⇒ trail tamper-evidence nominal; role prompts have no recorded identity; A3 auditor/tripwire unbuilt.

**Bottom line:** Threat A (injection) = good today for the authored-only surface; Threat B (tamper) =
weak — one file fingerprinted, comparison dormant, no pre-dispatch gate, assembled prompts identity-free.
**Next:** owner picks remediation priorities from the audit (natural neighbor: the A3 auditor).

---

## Policy change — live verification is now routine, not opt-in (2026-07-02, owner directive)

Owner: "start running live but scoped tests, like dreamer functionality with an actual model,
moving forward." Documentation updated to make this a standing rule, not a one-off: `CLAUDE.md` →
"How to work" (new bullet), `CONVENTIONS.md` → "Testing & validation" (the policy + the sandbox
clarification), `docs/runbook.md` (new "Verifying a change" section right after the quick-reference,
with the exact commands). The offline `pytest -m 'not live and not podman and not needs_*'` suite
(552 tests) stays the fast inner-loop ratchet; `-m live` / `-m podman` are now the outer verification
step for anything touching a model tier or the sandbox, run whenever the real thing is available —
not treated as a separate optional pass.

**Corrected a premise along the way.** The owner's framing ("live tests will force us to use the
sandbox, since a lot of the computation happens there") doesn't hold for this codebase: `core/
dreaming/` and `core/complex/` have zero references to sandbox/podman/run_python (confirmed by
grep) — the Dreamer/reasoning-complex runs its own computation in-process (model-free and
deterministic except the embed/synthesize calls), never inside Podman. The sandbox (`-m podman`,
currently 7/7 passing, podman-machine confirmed running) is exclusively the `run_python` **tool**
path for agent-*authored* code (coder/data_analyst roles) — an orthogonal concern from live-model
dreaming tests. `CONVENTIONS.md` now states this explicitly so it isn't re-conflated later.

**Live-model status today:** `pytest -m live` → **7 passed / 1 skipped** (embedding + router/
routine/stretch tiers real; the one skip is dreaming's `synthesis` tier, `qwen3.6:27b`, not yet
pulled — confirmed via `ollama list` this session). The owner has started pulling it; once it
lands, both committed dreaming live gates run for real: `test_dreaming_live.py` (v1) and the H8/H9
session's new `test_dream_v2_live.py` (v2 loop) — the latter already smoke-tested end to end
against the real `qwen3.6:35b-a3b` (stretch) tier and produced a correctly-grounded, self-check-
passing narration (see the H8–H9 entry above).

## Live-tier bug fix — split Ollama socket timeout (2026-07-02)

Running the full suite with the `qwen3.6:27b` synthesis tier finally pulled surfaced a **real
production bug** (not a test artifact): 2 live failures, both `TimeoutError` on `OllamaClient.chat`
— `test_scheduler_live` (a `router` ping under full-suite model-load pressure) and
`test_dream_v2_live` (real `synthesis` narration). Root cause: `request_timeout_s = 120` was the
*single* socket timeout on every Ollama POST. Measured a realistic 27b synthesis chat at **~290s**
(2442 thinking+narration tokens) — 2.4× the ceiling; a real dream/synthesis pass would hit the
identical wall. 120s is wrong in both directions: too long for a hung health/load probe, far too
short for a heavy thinking-model generation.

**Fix:** split by operation class. New `[ollama] generation_timeout_s = 600` (`OllamaConfig`,
`.get`-defaulted so older TOMLs load); `OllamaClient._post` takes a `timeout` override; `chat()`
uses the generation timeout, all control-plane ops (health/load/embed/evict) keep the fast 120s.
Job-level liveness (a pass that never returns) is the supervisor's concern *above* the socket
layer, so a generous generation timeout here is safe. **Verified:** both previously-failing live
tests now pass (`test_dream_v2_live` = the loop v2 end to end on real 27b synthesis, grounded +
self-check-passing — the first full-fidelity v2 run); offline suite unaffected (552 green); ruff
clean. Pre-existing honest skip unchanged: `test_dreaming_live` (v1) skips when the golden fixture
doesn't cluster at its 0.45 threshold under the real embedder (a fixture-threshold matter, not a
regression).

## Track G — Prompt G1–G3: the hands (the type, the gate, read-only sensing) (2026-07-03)

Opened the outward-action boundary at its **safest end** — β = 0, read-only sensing — with the
whole surface **flag-OFF by default** (`[effectors] enabled=false`, empty upstream allowlist).
No acting classes built; the types structurally refuse them. Design: `docs/hands-and-the-
effector-layer.md` (Track G). Everything below is new code behind the flag; no existing behavior
changed (proven by the untouched 552 baseline still green inside the new 602).

**G1 — the effector types (`ops/effects.py`).** `Effect` / `EffectView` + the `ReversibilityClass`
enum (SENSING/REVERSIBLE/IRREVERSIBLE, an `IntEnum` because — unlike provenance, where G8 retired
the order — the order here is the §4 filtration index). The load-bearing move, the **dual of
`MirrorView`**: `Effect.__post_init__` **raises** unless the approval reference covers w(β) for the
class (None admissible ONLY for SENSING), so an unapproved consequential effect is *unconstructable*,
not checked-then-refused. Two more structural facts: (a) an effect carries **no confidence of its
own** — `cites` names motivating interpretation ids, but there is deliberately no `confidence`
field, holding companion III's u≠c separation at the actuator (a high-c dream earns no automatic
action; test asserts the field's absence); (b) `ScopedCapability` carries a scope NAME + a Vault
**accessor** (non-secret reference), and has **no token/secret/credential field at all** — one step
harder than `MintedAgent.token` (off-prompt/off-repr): here the field doesn't exist. `EffectView` is
**Effects_{β≤ε} as a type** — ceiling defaults to SENSING (ε=0); `admit` re-validates; a class above
ε raises `CeilingExceededError`. β (`blast_radius`) and w(β) (`required_approval`) are property-tested
monotone.

**G2 — the gate generalized (`ops/effect_gate.py`).** The Phase-10 guarded transition system (I12),
wider domain: `ProposedChange`→`ProposedEffect`, `G_now`→`G_effect(E) = proposed ∧ approved_{w(β)} ∧
scoped_cap_valid ∧ attested` (§6). `ProposedEffect` inherits the structural ceiling — an
(actuator-name, allowlisted-string-params) pair with **no path/diff/command/code/url field**, so
"run this"/"fetch that address" is unexpressable (the `ProposedChange`/`ResearchCriteria` move);
`resolve()` is fail-closed against the actuator registry (sensing-only: `sense_fetch`) + each
actuator's **closed** param-key allowlist. `effect_gate_admits` is pure data-in/bool-out (no E
handle, no apply ⇒ **E can never self-apply**, I12 inherited), the approval requirement **computed
from the class** via w(β) (no `required` field a decision could understate), the scoped-capability
check a **first-class conjunct** (the confused-deputy answer: no minted scope ⇒ no effect even
fully-approved). **FSM-verified exhaustively over all 72 states** (3×2×3×2×2), same discipline as the
8-state config gate. `capability_covers` = exact-scope-match (no glob authority) + fail-closed expiry
(unparseable⇒expired). Scope note: the durable EffectLedger (execute/validate/rollback rows) lands
with G5 (the first class with world state to roll back); β=0 has none — the guard + types +
attestation trail are the whole machine.

**G3 — read-only sensing, end to end (β = 0).** Core side `core/sensing.py`: `SenseRequest`
(outbound — de-identified, carries **no note content and no URL**: `terms` pass the SAME conservative
scrubber as airlock criteria via the new shared `core.research.criteria.clean_term` seam — one
policy, one impl; `upstream` is a short NAME into the edge allowlist, shaped so a URL/host/path is
unrepresentable → the confused-deputy answer made structural), `SensingHandoff.emit(request, effect)`
(admission **IS** `EffectView.admit(ceiling=SENSING)` — an acting-class effect raises before anything
touches the handoff), `SensedObservation.to_row()` (stamps provenance `observed` with **no
parameter** — the DerivedStore unforgeability move; result type has **no actuator field**, §3),
`ObservedView` (the assistant-tier read boundary, dual to MirrorView; the Track-D correlator's
intended seam). **Edge side** `edge/effectors/sensing.py` (Zone B): `SensingEffector` serves
`sense_fetch` from the handoff with a **powerless constrained fetch** (`UrllibTransport`: **https-only**,
**redirects refused** — 3xx off-host is an exfil vector, **size-capped/refused-not-truncated**,
timeout, no auth/cookies), resolving the request's NAME against its **own reviewed allowlist** (the
ONLY place a URL exists; empty by default ⇒ every fetch refused); **never imports core/ops/scheduler**
(AST-asserted). Refusals come back as **honest error observations**, not silent gaps. Wire shapes
mirrored, not imported — airlock/monitor pattern.

**The firewall (the §3 "done when"), structural both directions.** `MirrorView` refuses `observed`
rows while `ObservedView` refuses everything non-`observed`, so the two views **partition** the tiers
with no representable overlap: sensed exhaust provably **cannot reach the authored mirror or the §15
baselines** (a store of observed rows projects to an empty MirrorView; a sensed row into MirrorView is
a type error). Tested in `tests/integrity/test_sensing_firewall.py`.

**Config** — new `[effectors]` section + `EffectorsConfig` (`.get`-defaulted so older TOMLs load):
`enabled=false`, `handoff_dir`, `timeout_s`, `max_response_kb`, `[effectors.upstreams]` (name→https
allowlist, empty). Fail-closed twice: `build_sensing_handoff` / `build_sensing_effector` both **refuse
unless enabled**, and an empty allowlist refuses every fetch even when enabled.

**Verified.** New tests: `test_effects.py` (G1 types), `test_effect_gate_fsm.py` (G2, 72-state FSM),
`test_sensing.py` (core handoff), `test_sensing_effector.py` (edge, fake transport),
`test_sensing_firewall.py` (the partition + the edge→private-zone import check),
`test_sensing_transport.py` (non-https guard). **Offline suite 552→602 (+50), ruff clean tree-wide,
import-firewall green** (core reaches no network; effectors are edge — both directions now enforced).
**Live network smoke passed** (real `UrllibTransport` → `https://api.github.com/zen` returned a body;
non-https + unknown-upstream refusals fired) — the real egress path, not just the fake. **No flags
flipped** (effectors OFF, self-mod OFF, dream R&D OFF). Not touched: any Ollama tier or the podman
sandbox, so `-m live`/`-m podman` don't apply. **Next (Track G):** G4 (the effector catalog + the
SKILL-mining pipeline doc = the §8 audit as a repeatable process); then G5 (reversible writes) only
once its property tests are green — you do not get a class until the one below is solid (§4). The
acting classes' *value* is gated on Track H producing a deep-enough model to tailor actions (§7).


---

## Security planes — design note (docs/research/)

**Status:** DRAFT, pending ratification (2026-07-03)

**Written:** `docs/research/security-planes.md`. Three-plane security composition — types (code
plane, Threat B-adjacent), provenance (data plane, Threat A), capabilities (boundary, Threat B).
Covers: foundation file set enumeration (builder never holds write access; blocking on repo
verification pass), the Rust/PyO3 privileged-path split (parked, default recorded, rejected
Nelua/Haskell-subroutine/Coq-Agda-F*/Koka-Frank), lightweight TLA+/Alloy + Hypothesis treatment
for three invariants (label monotonicity, capability non-amplification, append-only), store
encryption as capability-hardening rather than a confidentiality silver bullet (AEAD for
integrity, key-as-capability, index-leakage caveat recorded), and the librarian/adjudicator
split — one librarian indexing external strata on ingest and derived strata on promotion only;
the adjudicator as an owner-facing clerk, not a pipeline component, writing recommendations to
the verdict store inbox with promotion spent only by the owner.

**Cross-referenced into:** `docs/audits/prompt-integrity-audit.md` (foundation-file-set gap),
`docs/design-notes/recursive-strata.md` (indexing-on-promotion policy, I1 enforcement),
`docs/design-notes/stability-adjudication.md` (adjudicator's stability-filter input).

**Blocking on:** foundation file set verification pass against the repo (§2 of the note).
**Not built:** no code changes; the note is design-only, same status class as the parked notes
it cross-references.
