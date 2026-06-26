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

**Next (Phase 7 — Curator + dreaming):** background compaction (merge near-dupes, prune, flag contradictions) on the *interpreted* layer + dreaming synthesis (cluster embeddings, track themes), cron/trough-only, never during foreground use (the Phase-3 foreground gate; `synthesis` is already in `HEAVY_TIERS`). *Mirror, not oracle* (§4); never rewrite the explicit/authored layer (§8). **Phase 6b (voice/telephony)** is skipped per owner (optional, §20.11). Notes for the build: `numpy` 2.5 is available (transitive via lancedb — add it to pyproject deps if imported directly for clustering); the **synthesis-tier model `qwen3.6:27b` is NOT pulled** (only 2b/9b/embedding/35b-a3b are), so make the dream synthesizer injectable and gate any live synthesis test on the model (pull 27b only to exercise it). `VectorStore` will need an "all rows / by-provenance" read for clustering. Store interpreted artifacts (dreams, curation findings) in a new derived store, marked `INTERPRETED`, regenerable.

## Phase 7 — Curator + dreaming (COMPLETE, 2026-06-26)
**Gate to verify:** background compaction + dreaming synthesis; run on cron in troughs only; coherent output; never during foreground use.

**Built** — the §9 cognitive-tier agents, on the **INTERPRETED** layer (§8), trough-only.
- `core/stores/derived.py`: `DerivedStore` (SQLite) — the home for INTERPRETED artifacts (dreams + curator findings). **Writes `interpreted` provenance and nothing else**: `add()` has *no* `provenance` parameter, so the derived layer cannot masquerade as authored ground truth (the §8 explicit/interpreted firewall, structural — like the telemetry write-only handle). Ids are content-derived → re-running a cron pass is **idempotent** (INSERT OR REPLACE), and `reset()` makes it **regenerable** from the immutable corpus.
- `core/stores/vectorstore.py`: added `all_rows(provenances=…)` — the by-provenance full scan the dreaming agent clusters over (`to_arrow().to_pylist()`, filtered in Python; single-user scale). The mirror passes `{AUTHORED}` so observed exhaust never seeds a dream.
- `core/dreaming/cluster.py`: **deterministic, model-free** clustering (NumPy only) — note centroids (chunk vectors averaged per digest), cosine **single-linkage connected components** over a threshold, near-duplicate pairs, and note snippets for grounding. The §9 principle in miniature: the heavy deterministic work runs in cheap code so the scarce inference slot is earned only for synthesis. Reproducible given input order.
- `core/dreaming/dreamer.py`: the **Dreamer** (§9) — clusters the AUTHORED mirror (`MIRROR_READABLE`, the firewall), frames each theme Constitution-first with the cluster's own notes as the only citable evidence (**mirror-not-oracle** role), runs the **injectable** synthesizer, and **self-checks grounding** (`core.selfcheck`) before storing the reflection as an INTERPRETED `dream`. Synthesizer is a `Callable[[messages], str]` seam so the module is testable without the (large, unpulled) 27B model.
- `core/curator/curator.py`: the **Curator** (§9) — **detects and flags; never rewrites authored ground truth** (§8). Reads the corpus; writes only INTERPRETED `finding`s: `near_duplicate` (authored merge *candidates* — never auto-merged), `prune_candidate` (derived vector rows orphaned from the raw store = dead derived weight), and `contradiction` (a model JUDGMENT — an **injectable seam, deferred** until a detector is supplied, never faked, exactly like the §4 judge seam). Applying any merge/prune to authored content is the gated self-modification loop's job (Phase 10).
- `scheduler/cron.py`: wires `dream`/`curate` into the supervisor — both already route to the **synthesis** tier (`router._SYNTHESIS_KINDS`), which the Phase-3 foreground gate (`HEAVY_TIERS`) blocks while the owner is present. So trough-only + ceiling + swap discipline apply **for free**; this module just builds the handlers + enqueue helpers. Per-cluster checkpointing (the `queue.checkpoint` seam) noted as a future refinement.
- Config: `[dreaming]` (similarity/near-dup thresholds, min cluster size, max clusters) + `paths.derived_store`; `numpy>=1.26` added to runtime deps (was transitive via lancedb).

**Verified (gate met):** `ruff` clean; `pytest` **152 logic passed (+29 new), 6 live + 6 podman/synthesis-live skipped** (164 collected). Real wiring smoke-tested (`build_dreamer`/`build_curator` load config + stores without a model call; empty-corpus runs are graceful). Librarian live re-run green (no regression in shared paths).
- *dreaming synthesis* — `test_dreamer`: clusters→themes; reads the AUTHORED mirror only; Constitution-first + grounded context; stored as INTERPRETED dreams; **fabricated citation flagged**. `test_cluster`: centroids/clustering/near-dup/determinism.
- *background compaction* — `test_curator`: near-dup candidates flagged (not merged); orphaned derived rows flagged for prune; **contradiction deferred without a detector** (and fires when one is injected); findings persisted as INTERPRETED; near-dup scan reads the mirror only.
- *derived layer firewall* — `test_derived_store`: INTERPRETED-only (no `provenance` param), idempotent content ids, regenerable `reset()`.
- *trough-only / never during foreground use* — `test_cron`: dream+curate route to synthesis; **gated QUEUED while the owner is present, run in a trough** (reuses the Phase-3 foreground gate).
- *coherent output (live)* — `test_dreaming_live` (`-m live`): real embedder + synthesis model over the fixture corpus → a theme synthesized, stored, grounding check fired. **Skipped here: `qwen3.6:27b` (synthesis tier) is not pulled** — `ollama pull` it to exercise. The deterministic structure + grounding are asserted cold in `test_dreamer`.

**Decisions / reconciliations honored**
- **Curator flags, never rewrites authored (§8).** "Merge near-duplicates / prune" is realized as *findings* (candidates) on the interpreted layer; mutating authored content is a corpus change = self-modification → the Phase-10 gate. Only genuinely-derived dead weight (orphan vectors) is a prune candidate, and even that is flagged, not auto-deleted.
- **Mirror, not oracle (§4) end to end.** Dreaming reads `MIRROR_READABLE` (authored-only firewall — observed exhaust can never seed a dream, nor enter the §15 baselines), cites only the clustered notes, and runs the same grounding self-check the Librarian does.
- **Honest seams, not theater.** Contradiction detection (a subjective model judgment) is `deferred` without a detector — never approximated by keywords — mirroring the §4 judge seam. The synthesizer is injected so the deterministic path is fully tested without the 27B model.
- **Deterministic floor (§9).** Clustering/near-dup are NumPy-only and reproducible; the model is earned only for the per-theme synthesis (capped by `max_clusters`).
- **Trough-only is structural, not new code.** `dream`/`curate` were already synthesis-tier kinds in the router; the Phase-3 foreground gate + two-slot ceiling enforce "never during foreground use" without a second mechanism.

**Next (Phase 8 — The airlock, AWS Zone C):** Terraform for `requests/`+`results/` S3 prefixes + the least-privilege fetcher (Lambda/Fargate), the containerized **bridge** (Zone B), and the one-way research flow — sanitized de-identified criteria out, public literature in, ranked inside the walls. The Librarian already has the "emit de-identified research criteria" seam (§16) noted. First **Zone C** work; needs §20.7 (AWS account/region/TF state) and §20.9 (Lambda vs Fargate) from the owner. The egress guard stays installed in core; only the bridge (edge) touches S3, and it never reads the vault (Invariant 2). **⚠️ Carry-forward:** Phase 4 empirical `-m podman` still pending (podman machine won't boot here — see runbook.md).

## Hardening pass — verifiable properties (2026-06-26)
**Not a phase.** Verification-only pass against `docs/WHITEPAPER-FORMAL-PROPERTIES.md`. **Main build not advanced (Phase 8 stays queued); dream R&D flag OFF; runtime behavior unchanged** (same outputs/defaults — internal types/checks hardened). Worked the invariant catalog by assurance tier.

**Promoted toward "unrepresentable" (structural — highest leverage)**
- **I6/G3 — typed `MirrorView`** (`core/mirror.py`). Sole constructor `project` applies the MIRROR_READABLE projection; `__post_init__` raises on any non-authored row, so a non-MR view is **unrepresentable** (not "checked then refused"). Dreamer (`clusters()`) + curator (`near_duplicates`, `contradictions`) introspective reads now flow through it. The firewall is structural for the introspective read path. **New gap G11:** guards the data, not the store handle.
- **I9/G1 — stable digest citation IDs** (`core/selfcheck.py` `Source`). Grounding resolves each `[[title]]` to a single retrieved **digest**; a title matching two distinct digests is flagged *ambiguous* (the ill-posed case G1 named) instead of silently accepted. Librarian (`Retrieval.digest`) + dreamer pass `Source`s. **New gap G10:** surface form still a title (decidable iff unique-in-Ret, now detected when not).
- **I10/G2 — `derived_from` edges + acyclicity** (`core/stores/derived.py`). `add(derived_from=…)` records edges and **refuses a cycle at insert** (`DerivationCycleError`); `depth()` computes d(κ); `core/recursion.py` `decay_bound` gives c≤γ^d·g. Dreamer/curator record authored-leaf digests → today every interpreted node is depth-1 over authored ground (recursive dreaming, flag-OFF, is what the deeper machinery is for). Additive SQLite migration for the new column. **New gap G9:** authored-leaf-only is by-convention (store can't tell a digest from a string); adjudicator that consumes the ranking is Phase 9.

**Static lint (I2 — promoted runtime→static)**
- `ops/import_lint.py` (stdlib AST, zero new deps) + `scripts/check_imports.py` + `.github/workflows/ci.yml` + `tests/test_import_firewall.py`. Core imports no `edge`/`cloud` (hard, zero-exception) and no networking primitive outside the audited loopback allowlist (`core/sealing.py`, `core/models/ollama_client.py`). Proves no core→net import path *without running*.

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

**Next R&D (only when resumed, in order):** R2 utility telemetry (separate axis) → R3 recursion (ONLY after the Phase-11 drift gauge exists to watch it — depth cap + the dreams-citing-dreams / utility-up-grounding-down / confidence-up-with-depth alarms) → R4 cross-source assistant synthesis (observed+authored, interpreted, never the mirror). **Main build resumes at Phase 8 (airlock).**

## Phase 8 — The airlock (AWS Zone C) (COMPLETE, 2026-06-26)
**Gate to verify:** sanitized request → public corpus → ranked inside core; core never touched the network; IAM tight.

First **Zone C** work. The one-way research flow (§16): core emits **de-identified criteria** → filesystem handoff → the Zone-B **bridge** PUTs to S3 `requests/` → the cloud **fetcher** (Lambda) writes public literature to S3 `results/` → bridge GETs to the handoff → core **ranks inside the walls**. The sealed core never touches S3/network; only the bridge does, and it has no vault handle (Invariant 2 & 11). **Owner decisions applied (phase8-aws-decisions):** acct 054942746160, SSO `alberto-sso`, us-east-1, fresh dedicated TF state, Lambda compute.

**Built — Zone A (sealed core), `core/research/`**
- `criteria.py`: **the privacy boundary.** `ResearchCriteria` (topic + scrubbed terms + coarse filters) is the ONLY object that crosses outbound — it has **no field that can carry note content** (`to_request()` serializes only those fields; structural firewall like `DerivedStore`'s missing `provenance` param). `deidentify()` is the **conservative** scrubber (drops/raises on emails, URLs, phones, handles, long digit runs, dates, over-long phrases; charset allowlist; capped term count/results; publication-type allowlist). `assert_clean()` re-validates at the emit boundary so a hand-built criteria can't bypass it. The model only *advises* (proposes terms); this code *acts* (Invariant 2).
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
- *sanitized request* — `test_research_criteria` (PII dropped/refused; structural firewall: `to_request` carries only criteria fields; `assert_clean` catches hand-built dirty criteria) + `test_research_airlock` (emit writes only de-identified criteria; refuses dirty at the boundary).
- *public corpus* — `test_fetcher` (dedup by DOI across sources; evidence ordering; preprint flagged; unresolvable dropped; one flaky source doesn't sink the gather; `handle_event` S3 read→aggregate→write) + `test_bridge` (push→S3 byte-for-byte; pull→handoff; ignores unknown ids; no vault handle).
- *ranked inside core* — `test_research_rank` (corpus relevance outranks irrelevant; evidence tie-break; preprint/unresolved flags; corpus-silent fallback) + **`test_research_live` PASSED** (real embedder over the golden fixture corpus: on-topic paper ranks first by private-corpus relevance — the embedding model is pulled).
- *core never touched the network / IAM tight* — import firewall + the structural no-vault-handle bridge; least-privilege IAM validated + tflint-clean.

**Decisions**
- **De-identification is structural + conservative, not best-effort.** Two layers: a type that *cannot* carry corpus content, plus a scrubber that *raises rather than passes doubt*. Both tested. The richer PII scrubber (corpus proper-noun denylist / NER) is a documented extension point.
- **Bridge is a dumb pipe with no vault handle** — network and private data never share a component (Invariant 2). Even a bug here can't leak the corpus: there's no corpus to reach, and outbound bytes are already de-identified by core.
- **Public literature is ranked transiently, never ingested into the mirror** — it's external/public, not the owner's authored writing; mixing it in would corrupt the mirror + §15 baselines.
- **S3-native state locking** (Terraform ≥1.10 `use_lockfile`) instead of a DynamoDB table — fewer resources, less IAM, simpler.
- **Fetcher web egress is a network property (no VPC), not an IAM grant** — its IAM is exactly the two prefixes + logs; it can reach only public endpoints, nothing private. ("Dumb outside / smart inside": personalization stays local — no remote summarization model, per owner default.)

**⚠️ Operational boundary honored — `terraform apply` NOT run.** Per the owner's instruction, the config is written + `validate`/`fmt`/`tflint`-clean but **no live AWS resources were created**. To deploy: `aws sso login --profile alberto-sso`, then `bootstrap` apply (state backend), then `airlock` `init`/`plan`/`apply`; copy `airlock_bucket` → config `[airlock] s3_bucket` and configure an `mind-palace-bridge` AWS profile assuming `bridge_role_arn` (steps in `cloud/terraform/airlock/README.md`). Recommended hardening at apply: set `bridge_trusted_principal_arns` to the SSO permission-set role ARN (default falls back to account root). **Carry-forward:** Phase 4 empirical `-m podman` still pending (machine won't boot here — runbook.md).

**Next (Phase 9 — Backups):** restic → S3 + SSE-KMS, scheduled; client-side encrypted + deduplicated so AWS never sees plaintext (§16b). *Verify:* encrypted backup + restore round-trips; AWS sees no plaintext. Reuses the bootstrap state backend; new namespaced bucket + KMS key. macOS/APFS — restic over data directories, don't assume btrfs.

<!-- Append new phase entries below as you complete each one. -->
