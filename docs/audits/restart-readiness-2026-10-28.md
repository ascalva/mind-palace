# Ouroboros restart readiness — 2026-10-28

**Scope.** The owner asked for a fresh start of the live instance (Ouroboros) on llama.cpp instead
of Ollama, with dreaming on demand only, and for a full read of what is left before the palace is
usable as persistent context for the local model (the Ambassador entry point). This audit records
what was done, what was measured, and what each subsystem still needs. Where a design note and the
code disagree, the code (and the live run) is reported as ground truth.

**Method.** `git pull` to `f5306d4..ef33ae9` (29 commits, incl. bp-153), the deterministic test
tier, `mypy`, the import firewall, `palace status`, the board (`scripts/board.py`), the design
notes' own `implementation:` fields, and live runs against the fresh store. Changes are on branch
`ops/llamacpp-endpoints` (uncommitted at the time of writing).

## 1. What was done

| step | result |
|---|---|
| Fresh start | The corpus layer was **moved, not deleted**: 30 paths, 11 GB, to `~/mind-palace-archive/ouroboros-2026-10-28/data/` (same volume, instant, reversible). Guarded items untouched: Vault Raft, `runs.sqlite`, `selfmod_ledger.sqlite`, `telemetry.duckdb`, `code_snapshots.sqlite` (4.7 GB build history), `observation_history.sqlite`, `backup-staging`, `logs`. The pre-edit `config/ouroboros.toml` is copied next to the archive. |
| Embedder → llama.cpp | `Qwen3-Embedding-4B-Q4_K_M.gguf` (2.50 GB, sha256 verified against Hugging Face) served by `llama-server --embedding --pooling last` on `127.0.0.1:8081`, `--sleep-idle-seconds 60`. Measured: dim 2560, unit-norm vectors, **RSS 3.70 GB** at 8K ctx (the note recorded 3.69 GB for the same model under llama-server). Same quant Ollama served, so σ and the near-dup threshold keep their calibration. |
| Chat tiers → llama.cpp | All four tiers (router, routine, synthesis, stretch) → lmtune's llama-server (Qwen3.8-27B Q4_0, `:8080`, bearer key passed by env-var NAME `LMTUNE_API_KEY`). Flipping all four together means Ollama never loads a chat model. |
| L0 re-ingest | 29 notes in `~/.mind-palace/vault/janus_notes` → 29 raw, **38 chunks, 38 vectors**. The full vault lane (`VaultSync.rescan`) then wrote catalog, versions and attestations; a second rescan reported `indexed=0 unchanged=29` and the vector count stayed 38 (idempotent, no duplication). Retrieval spot-check: "recursion and self-reference" → the 07-11/07-12 notes at cosine distance 0.37–0.43. |
| Dreaming | `[dreaming] scheduled = false` in the overlay: the daemon's trough passes no longer enqueue dream or curate. On demand: `mind-palace dream` — 4 themes, 4 grounded, 430 s (§2.4). |

### Code changes on the branch (all defaults keep today's behaviour)

- `[runtime] ports` (per role) and `api_key_env` (env-var name) — the client seam can now reach two
  owner-launched servers at once, and lmtune's authenticated one. The key never enters config, a
  file read by core, or a repr (Invariant 10). Interim until bp-116 assigns ports at spawn.
- `ModelServer.chat` dispatches a `llamacpp` tier to that tier's server (the P5 shape);
  `TwoSlotLoader.ensure_tier/ensure_pinned` skip Ollama for `llamacpp` tiers.
- Preflight requires Ollama only if some role still uses it; otherwise it checks each llama-server's
  `/health` (answered without waking a sleeping model). `status` reads the embedder's residency
  from `/props.is_sleeping`.
- `[dreaming] scheduled` lever; `palace dream` and `palace vault-sync` (one-shot, refuse while a
  live run owns the stores).
- Reset gap fixed: `memberships.sqlite` added to `reset_targets()` (it was left behind, pointing
  into a wiped vector plane).
- Tests: 4 new in `tests/unit/test_inference_seam.py` (port routing, key on the wire, no key → no
  header, key absent from repr) + 2 default assertions; 7 in the new
  `tests/unit/test_llamacpp_cutover.py` (a llamacpp tier never loads or evicts in Ollama, an Ollama
  tier still does, chat routes to the tier's server without Ollama knobs, preflight passes/fails
  closed on llama-server health, the dreaming lever's default, memberships in the reset set); and the
  `tests/conftest.py` overlay isolation (§2.9). Full tier results in §2.9.

## 2. Readiness by subsystem

### 2.1 Inference and the two-slot discipline — **partly done; one measured hazard**

Ollama was hard-wired in five places: `build_model_server` (every chat consumer: runtime, Librarian,
Dreamer, factory, Ambassador), the supervisor's `TwoSlotLoader` (`launcher.py:478`,
`scripts/watch.py:94`), preflight's `check_ollama`, and the `status` residency probe. All five now
follow `[runtime]`.

**Measured hazard (the reason bp-116 matters).** The first `palace dream` failed with HTTP 500
"Compute error"; lmtune's log shows Metal `kIOGPUCommandBufferCallbackErrorOutOfMemory` during
prefill. Resident at the time: the 27B (64K ctx) + the 4B embedder (3.70 GB) + a full test run,
with 7.7 GB of swap in use. After that failure the server's Metal backend stayed in an error state
(every later request failed in < 2 s) until `lmtune serve restart`. **"At most two resident models"
is not sufficient on this Mac: the 27B and the embedder fit together only when nothing else is
under pressure.** Ollama's loader used to evict to stay under budget; with llama.cpp nothing does
yet. Interim: the embedder unloads after 60 s idle, and a dream does not need it (clustering reads
stored vectors). Left:
- **bp-116 (process manager)**: residency as a kernel fact — before a synthesis-tier call, make the
  embedder sleep (or refuse), and the reverse before a bulk embed. llama.cpp's router mode
  (`--models-max`, b11669) is an alternative that enforces the slot count in one process.
- **bp-117 (equivalence gate)** and the chat-tier verification bp-119 was parked on: the chat path
  has now run against a real model (Qwen3.8 loads in upstream llama.cpp), so V-B's premise is met.
- A failed-backend detector: a 500 "Compute error" should mark the server unhealthy and ask for a
  restart instead of failing every job after it.

### 2.2 Vector storage — **vault lane good; code lane built, never run live**

- Vault lane: chunk-level amendment reuses unchanged chunks; verified idempotent above.
- Code lane: the vector-membership arc (bp-151 → bp-155 → bp-152 → bp-153) is merged — one row per
  idea-atom, occupancy in `memberships.sqlite`, compaction, `|M|/|V|` gauge. The arc's own dry run
  measured **2.280×** (52,200 chunks → 22,897 atoms). The live rebuild never ran (issue #39); after
  this reset there is nothing to rebuild — the next `palace code-seed` lands atoms + memberships
  from scratch. Left: run the seed (long: every HEAD `.py`), check `|M|/|V|`, then lift the overlay's
  code/transcript pause, whose stated re-entry condition ("set membership lands and re-ingest is a
  diff") is now met. Deskcheck owed.
- No ANN index is configured; at 38 rows (and ~23k atoms for code) brute force is fine.

### 2.3 Query algebra — **built and wired (update, same day)**

_First pass found it "not usable by an agent". The notes' `design-only` fields were stale: the whole
typing layer was already built in `core/kernel/scope.py` (the scope lattice, firewall ideals,
`req_admissible`, the zone law, `Inv`/`Rate`/`Res`). What was missing was the sentence layer._

`core/query.py` adds it: a `Query(verb, grant, …)` whose construction IS the admissibility check
(`req(verb) ⊑ some granted scope`, else `IllScopedQuery`); a grant as **one scope per clock plane**
(semantic on the projection-event clock, structural/causal on the commit clock, temporal on the
per-stratum ledger — `TimeScope.⊑` compares one clock, and cross-clock joins are constructor errors
until N materializes, so one scope cannot hold all three); mode derived from scope (§2.4); and the
operators: SEARCH (K_sem over the provenance classes Σ names), REACH (F reachability through
`ReferenceView`), DIFFUSE (the TRA §2.1 RSP free-energy curve on the σ-backbone, β the single dial,
z := γ = 0.5 from `core/kernel/recursion.py` — the convergence condition the note ties to the γ
ceiling), HYBRID (K_sem ⊙ K_struct), HISTORY (σ_*/σ^* along the version chain, resolved through the
catalog's doc_id), RELATED (signed edges), ORIGIN (the C ∘ commit-keying join). Every result is
`Inv`. Verified on the live store: search, the β dial changing neighbourhoods (β = 0.1 vs 50),
hybrid, history, and an ill-scoped history sentence refused at construction.

Left: the §2.3 *reference agent archetype* as its own deterministic client with the §2.6 self-grading
oracle; `Rate` results (none yet); the multi-stratum SLICE cut is a single-read token today.

### 2.4 Dreaming — **live path works on demand**

Phase-7 `Dreamer.dream()` is the live path; `dream_v2`/shadow, D-0/D-1, H-0..H-2 are complete
(deskcheck pending); the interpreter panel (`[dream_rnd]`) is flag-off; recursive dreaming is
parked. Manual trigger now exists.

RESULT: with the embedder asleep, `mind-palace dream` over the 38-vector L0 store produced
**4 themes, 4 grounded** in 430 s on Qwen3.8-27B via lmtune — the first time the palace's
llama.cpp chat path has run against a real model. Measured on the first theme: 2,652 prompt
tokens at 89.5 tok/s (29.6 s), 3,479 tokens generated at 14.0 tok/s (MTP acceptance 0.76).
`palace status` afterwards: preflight `inference: llama.cpp up`, `dreams: 4`, `store: 38 vector
rows`, embedder `asleep (loads on the next request) — llama.cpp :8081`. Left: thinking is on at the
template default for synthesis (most of the 4.6 min/theme is decode); whether `think=False` keeps
grounding at this speed is a measurement, not an assumption.

### 2.5 Code investigation — **built; paused; one plan unbuilt**

CI-1..CI-3 (L0a/L0b/L1 embed lanes, isolation + retrieval proof, L2b reference resolvers +
`code_to_code` AST edges), bp-098 (enable path) and bp-099 (temporal code corpus) are complete;
bp-095 (the S↔F code↔design lens) is ready, unbuilt. The snapshot ledger (4.7 GB) was kept. Left:
seed, lift pause (§2.2), bp-095.

### 2.6 Edges — **two of seven producers live**

| edge type | store | producer | state now |
|---|---|---|---|
| similarity (σ-graph) | recomputed, not stored | dreaming / clustering | live |
| note-version supersession | `versions.sqlite` | vault lane | **live** (written today) |
| derivation hyperedges (B-arcs) | `derived.sqlite` junction | dreaming | live once a dream lands |
| signed relations (supports / contradicts / contextualizes) | `edges.sqlite` | **none** — `open_edge_store` has no caller outside the temporal spine's reader | **no producer**: the balance math has no input |
| owner-declared K₀ supersessions | `authored_supersessions.sqlite` | founding ingest (manifest) | empty — no manifest on disk |
| reference edges (code↔corpus, code↔code) | `reference_edges.sqlite` | code lane (L2b, AST) | empty until code seed |
| causal C-fiber | `causal_edges.sqlite` | integrator over L1 | empty until the dialogue lane runs |
| memberships (fibers) | `memberships.sqlite` | code lane (bp-152) | empty until code seed |

**Update (same day): every edge type now has a producer you can run.** Signed relations:
`core/relations.py` — authored `supports::/contradicts::/contextualizes:: [[Note]]` properties
(provenance authored-solo) plus an on-demand model-mediated detector over σ-backbone pairs
(provenance interpreted), `palace relate`. Reference edges: `palace lanes code-observe` re-projects
the kept snapshot ledger (`backfill_observations`, the re-projection a corpus reset needs).
Memberships: `palace lanes code-embed`. Causal C-fibers: `palace lanes dialogue` (chat sensor → L1
→ integrator). K₀ supersessions stay owner-asserted (`mind-palace supersede`). Counts after the
first runs are in §4.

### 2.7 Integrators — **built; fed by `palace lanes dialogue`**

The integrator (bp-071, dispatch seam bp-110) derives C-fiber edges from the L1 action log; L1 comes
from the transcripts lane. The daemon's lever stays paused; the on-demand lane runs it in-process.

### 2.8 Clocks — **built; green**

Per-stratum clocks and the cross-clock atlas (`core/temporal/{acquire,atlas,spine}.py`) are built
and their tests pass in the deterministic tier (§2.9). They read run ledgers and stores that this
reset emptied, so they have nothing to tell time over until lanes and dreams run again.

### 2.9 Core and inner core — **green except one inherited debt list**

Inner ring enforced in place (bp-083) and migrated to `core/kernel/**` (bp-090/091). On the branch:
the deterministic tier (`not live and not podman and not needs_vault and not needs_restic`) ran
**2,515 passed, 11 skipped, 1 failed in 97 s**; mypy reports the repo's recorded baseline of 69
(tests/ only); the import firewall and the worker-boundary scan are OK.

The one failure, `test_core_imports_nothing_outside_core`, **fails identically on a clean
`origin/main`** (same 21 sites): `core/` still imports `ops` (sensing, reference_view, effect_proposal,
factory, code_corpus, ops_view, shadow), `eval` (shadow, ops_view, temporal/spine), `config`
(factory) and `agents` (interface). The test names its own remedy — the config split (bp-067) and the
"16 machinery inversions" (bp-068+). Not caused by this branch; worth an issue if CI's ratchet job is
red on it.

**Test isolation fixed on the branch.** Before, the suite read this machine's
`config/ouroboros.toml`, so it passed only while the overlay happened not to touch what a test
depended on: flipping `[runtime]` made 8 loader tests fail. `tests/conftest.py` now points both
overlays at an absent file for every test (tests that need an overlay already patch it themselves).

### 2.10 Reset — **one gap fixed, four for the owner**

`reset_targets()` missed `memberships.sqlite` (fixed on the branch). It also leaves
`run_ledger.sqlite`, `eval_results.duckdb`, `structural.duckdb` and `dream_runs.sqlite`, whose rows
describe runs over the wiped corpus. Whether those are history to keep or corpus to wipe is an owner
call; this reset archived them.

### 2.11 Embedder upgrade — **deferred, with a reason**

Newer candidates exist (Qwen3-VL-Embedding 2B/8B, Jan 2026; EmbeddingGemma-2, Oct 2026, official
ggml-org GGUF). The golden set (5 queries, 6 synthetic docs) cannot tell embedders apart, and σ,
its bound [0.55, 0.75] and the near-dup threshold are calibrated to Qwen3-Embedding-4B. An upgrade
needs a real retrieval benchmark and the σ sweep (oq-0024 / bp-046) re-run first.

## 3. The Ambassador entry point — what the owner asked for next

The owner's direction (2026-10-28): the local model (Qwen3.8-27B via lmtune) becomes **the
Ambassador** — an entry point into the palace, using it as persistent context over MCP; the
model gets a skill for the query algebra; conversations are ingested into the dialogue stratum;
dreaming and models wake only when needed; one command sets the whole stack up. In dependency order:

1. **Process manager, minimal** (§2.1): embedder ↔ synthesis sequencing; failed-backend detection.
2. **A read-only palace MCP server** for the Ambassador: semantic search over `MirrorView`,
   temporal and origin queries, each a typed tool whose scope is checked in code (Invariants 2/3:
   the edge process holds no vault handle; the core answers through the handoff). This is the
   first concrete client of `dn-core-query-protocol` — it should be designed as its §2.3 archetype.
3. **The Ambassador skill + OpenCode workflow**: agents with their own model, prompt and tool
   permissions; the palace MCP + reflex browser tools; skills for the query algebra loaded on
   demand (prefill is the local model's bottleneck: ~80–90 tok/s).
4. **The dialogue lane**: Claude Code transcripts (the existing chat sensor) plus an OpenCode-session
   adapter → `chatlog` + L1 → the integrator; `dn-dialogue-ingest-and-recursion` is draft and
   present-not-wired.
5. **Code seed + lift the pauses** (§2.2).
6. **One-command setup**: launchd for the embedder, lmtune serve, the palace on demand, the OpenCode
   harness, verify probes — the "declarative services" idea in lmtune's backlog.

## 4. Where this stands — resume here (end of 2026-10-28)

Branch `ouroboros/ambassador-infra` (local; `main` = `16cb027`, ahead of origin by 1, never pushed;
the owner asked for local merges, no PRs). Commits on the branch: `a25fc25` (query algebra,
relations, dialogue capture, MCP), `be8ed78` (OpenCode sessions, `lanes`, `reembed`, embedder
templates), `d36e4d5` (config-driven embedder service, CORS, bench report, bridge capture).

**Done since (evening of 2026-10-28):**
- `palace lanes code-observe`: all 1,459 ledger commits re-projected in 2 h 04 min —
  **6,990,291 code observations** (3.4 GB) and **2,619,022 reference edges** (0.96 GB):
  corpus→code path-mention 1,267,496 · corpus→corpus note-citation 974,923 · code→corpus
  path-mention 356,250 · code→corpus note-citation 20,353.
- The embedder benchmark finished (`docs/experiments/embedder-bench-2026-10-28.md`): quality
  splits between EmbeddingGemma-2 and the 4B (SciFact 0.849 vs 0.778, NFCorpus 0.367 vs 0.406);
  Gemma is 14× faster in a sixth of the memory. Recommendation: switch, σ = 0.785, near-dup 0.93.
- Deterministic tier on the branch: **2,534 passed, 10 skipped, 1 failed in 143 s** — the one
  failure is §2.9's inherited `test_core_imports_nothing_outside_core` (20 import sites, none from
  this branch).
- bp-094 Item 2 (the M-C6 samples for the gated reference-edge patterns): dn-slug, finding-id,
  inherits and calls clear the 100% bar; paired-section (15/30) does not and stays off. A census
  over every code→code edge found two resolver bugs (decorator calls, facade targets), now fixed
  and tested. The enable itself waits on the owner (journal, 2026-10-28).

Next, in order:
1. Owner: the embedder. If switching: `[embedder]` model/alias/pooling in `config/stack.toml`;
   the owner runs `mind-palace stack up` once (the plist moves to the config-driven form); then
   `[embedding]` model/dim/templates and `[dreaming]` σ in `config/ouroboros.toml`, the σ lever
   bound in `ops/levers.py` → [0.772, 0.867], and `mind-palace reembed --confirm`.
2. Owner: the edge enable (`ENABLED_L2B_PATTERNS`, four patterns).
3. `mind-palace lanes code-embed dialogue` (memberships; chatlog → L1 → integrator → causal edges).
4. `mind-palace relate` (the 27B; embedder asleep first), then an OpenCode `ambassador` run end to
   end (`opencode run --agent ambassador …`), then `mind-palace stack check`.
5. Merge the branch into `main` locally, then `palace lanes code-observe` once more: the sensor
   walks `main`, so that pass mints the enabled patterns' edges (~10,483) at the merge commit.

Open proposals: `docs/brainstorms/ambassador-open-webui-bridge.md` (Qwen inside Open WebUI calling
palace tools); a separate session to evaluate Hermes Agent as a phone gateway.
