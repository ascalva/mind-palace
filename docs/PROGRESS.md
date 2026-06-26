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
- [roadmap-and-future-directions](design-notes/roadmap-and-future-directions.md) — post-Phase-10 roadmap (NOT committed spec; does not change Phases 0–10): provenance spectrum, inbound distillation gate, new sources/sensors/multimodal, process/concurrency model, OS-agent health, self-audit, dashboards/drift gauge, security posture. Two items flagged **[affects current build]** — reconciled below: honor §7 (concurrency) in Phase 3; §1 (provenance spectrum) is the growth path for the Phase-1 `Provenance` type.

### Reconciliation — roadmap design note (asked 2026-06-25)
- **Consistent** with what's built and both other design notes. The multi-node item explicitly preserves the Phase-1 "corpus crosses a network hop" flag; §11 security (keys from a sealed core via Keychain/Secure-Enclave or an edge-side broker, *never* KMS from the core) matches Invariant 1 + the `get_secret` env/Keychain-only seam; §10 drift gauge consumes exactly the golden-set + Constitution-conformance anchors built in Phase 2; §4 sensors land in the dormant `sensor_readings` table (Phase 0). No genuine conflicts.
- **§7 process/concurrency [affects Phase 3] — a clarification to honor, not a conflict.** Refines BUILD-SPEC §13's "reactive escalations preempt batch work": preemption is **cooperative, at job boundaries** — the escalation is dispatched *next*, never interrupting an in-flight generation (you can't cleanly preempt mid-generation; model-load is the dominant cost). Phase 3 therefore: one supervisor owns the SQLite queue (WAL, single-writer); agents are in-process tasks (context re-composed per invocation), not OS processes; the execution unit is run-to-completion or checkpointed-step, not a time quantum. Rules-first scheduling with the router model as an *enhancement* + a fall-back-to-rules path (also §8) — matches §13's "start with rules."
- **§1 provenance spectrum [affects current build] — Phase-1 type is forward-compatible; no change now.** Today's `Provenance{AUTHORED, INTERPRETED, OBSERVED}` + the `MIRROR_READABLE` frozenset already realize §1's rule shape ("a query declares which classes it may read; the mirror declares the authored classes"): retrieval read-scope is a *passed frozenset* (Librarian default `MIRROR_READABLE`), not a hardcoded binary. Growth path when those sources land: `AUTHORED` splits into `authored-solo` + `authored-dialogue` and adds `curated`; the existing single `authored` tag maps to **`authored-solo`** by default (conservative) via a deliberate human re-tag-from-raw (§8), never automatic (matches §1's "promotion is a deliberate human act"). Phase 3 carries provenance read-scope *through* the job/agent abstraction rather than assuming authored-only, keeping the seam open.
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
- *scheduled by tier / swaps minimized* — `test_supervisor::test_groups_same_tier_to_minimize_swaps` (two routine jobs run back-to-back, one swap to synthesis); `test_queue` priority + swap-avoidance; `test_router` kind→tier/window/priority.
- *foreground blocks heavy jobs* — `test_supervisor::test_foreground_gates_heavy_tiers` (synthesis stays QUEUED while present; routine runs).
- *ceiling enforced* — `test_supervisor::test_ceiling_breach_defers_job` (real loader, 5 GB budget → synthesis deferred, not crashed).
- *contexts fit + usage tracked* — `test_budget` (fits/trim-ladder/escalate, never drops the mandatory frame); `test_budget::test_context_usage_is_recorded` (DuckDB round-trip).
- *resilience / cooperative yielding* — handler-exception isolation + checkpoint-resume tests; live `test_scheduler_live` dispatches a real job through the loader + Ollama end to end.

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
- *isolated — no network/creds/vault* — `test_sandbox_policy` asserts the full isolation set on the argv and that **nothing is mounted** (vault unreachable) and seccomp is never disabled.
- *limits + timeout* — limits in argv; `test_sandbox_broker::test_timeout_result_discards_the_container` (timed-out container discarded); broker concurrency cap + per-exec logging.
- *warm pool works* — `test_sandbox_pool` (lazy warm, reuse, cap, discard-unhealthy, prewarm/shutdown); `test_build_broker_wires_from_config`.
- *empirical isolation* — `test_sandbox_podman_live` (`-m podman`): runs real containers and checks network-off, vault-absent, non-root, and timeout. **Skipped here because the Podman machine isn't running on this host** (`podman` is on PATH but `podman info` fails). To validate empirically: `podman machine start` (or install Podman), then `pytest -m podman`.

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
- `tools.py`: capability as **object-capability handles** (the telemetry store-layer precedent). `ToolRegistry` (tools registered independently of roles), `ToolDispatcher` that **holds only the in-scope handles** — an out-of-scope id is *unreachable* (`ToolNotInScopeError`), not "checked then refused". `run_python` runs through the Phase-4 sandbox broker (powerless, returns data); registered only if a broker is supplied.
- `factory.py`: `AgentFactory.mint(role)` composes Constitution → role → task (Invariant 6), resolves **scope = role.scope ∩ MAX**, binds a dispatcher of only those handles, returns an ephemeral `MintedAgent` (or persists it). `requested_tools` beyond the resolved scope → **routed to the human gate**, never minted. `MintedAgent` keeps the **advisory path (`respond`, self-evaluates) separate from the action path (`invoke`, dispatcher)** — model advises, code acts (Invariant 3). Out-of-scope `invoke` → gate + refuse.
- `registry.py`: SQLite `AgentRegistry` — promote an ephemeral agent to a persistent named one (§8/§10).
- `ops/gate.py`: `HumanGate` seam — records beyond-scope/privileged requests as PENDING (nothing privileged unattended, Invariant 5). The full propose→approve→execute→validate→rollback ledger is Phase 10; this is its inbox.

**Verified (gate met):** `ruff` clean; `pytest` **120 passed (114 logic + 6 live), 5 podman skipped**.
- *minting + Constitution inheritance* — `test_factory_mint` (ctx[0] == Constitution; ephemeral default); live `test_factory_live` mints general_conversation and gets a grounded answer.
- *cannot exceed scope* — scope resolves to role∩MAX; out-of-scope `invoke` raises + routes to gate; `requested_tools` beyond scope/MAX → `GateRequest`; template rejects beyond-MAX scope; object-capability dispatcher tests (`test_factory_tools`).
- *self-evaluates* — `respond` returns a `SelfCheck` (the §4 pre-return check); live-verified.
- *privileged → human* — `test_privileged_request_routes_to_gate`, `..._beyond_pre_declared_max...`, out-of-scope invoke → `HumanGate.pending()`.

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
- *round-trip* — `test_message_round_trips_gateway_to_core_to_gateway` (owner→LocalAdapter→handoff→CoreInbox→handoff→adapter reply).
- *core never touches messaging* — `test_core_inbox_never_imports_the_messaging_side` (no `import edge`) + the core processes purely from disk + handler; the gateway holds the adapter.
- *private default works* — `LocalAdapter` round-trips in-memory, `transits_third_party=False`, default adapter is `local`; third-party adapters refused unless opted in.

**Decisions**
- **Handoff = JSON files in a shared dir; the wire format is mirrored, not a shared import** — honors "core↔edge communicate by filesystem handoff, never imports" (CONVENTIONS). Atomic write-then-rename so neither side reads a partial file.
- **Adapters carry a `transits_third_party` flag**; the gateway makes the Invariant-11 tradeoff explicit and opt-in. WhatsApp is a declared stub (the live unofficial-lib/Cloud-API integration is deferred — §20.3/§20.4 owner decision).
- **The core handler is injectable** (librarian by default) so the inbox is model-agnostic and testable; the scheduler (Phase 3) can also drive `CoreInbox.process_once` as a job.

**Next (Phase 7 — Curator + dreaming):** background compaction (merge near-dupes, prune, flag contradictions) on the *interpreted* layer + dreaming synthesis (cluster embeddings, track themes), cron/trough-only, never during foreground use (the Phase-3 foreground gate). *Mirror, not oracle* (§4). **Phase 6b (voice/telephony)** remains an optional extension (§20.11 — needs owner's go-ahead + provider/number); skipped unless requested. No new models needed for Phase 7.

<!-- Append new phase entries below as you complete each one. -->
