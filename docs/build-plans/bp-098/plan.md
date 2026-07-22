---
type: build-plan
id: bp-098
track: code-ingest
status: proposed
design_ref:
  - docs/design-notes/code-ingest-pipeline.md
contract: builder
write_scope:
  - core/kernel/config/loader.py
  - ops/lifecycle/launcher.py
  - scripts/palace.py
  - config/defaults.toml
  - tests/unit/test_config*.py
  - tests/unit/test_code_ingest_wiring.py
  - tests/integration/test_launcher*.py
session_budget: 1
cost:
  estimate:
    model: opus
    tokens: 200k
  actual: null
depends_on:
  - bp-092
parallelizable_with: []
created: 2026-07-22
updated: 2026-07-22
links:
  - docs/design-notes/code-ingest-pipeline.md
  - docs/findings/finding-0159.md
  - docs/findings/finding-0146.md
  - docs/build-plans/bp-092/plan.md
re_entry: null
supersedes: null
superseded_by: null
warrant: docs/findings/finding-0159.md
---

# Build Plan — CI-wiring (Plan B): the code-ingest ENABLE path

> Every section below is required; an inapplicable one is `N/A — <reason>`.

## 0. Mode & provenance

Investigation and planning produced this plan (graduation of `dn-code-ingest-pipeline`'s
deferred "owner-visible enable step", §2.7). **Warrant finding-0159** (the owner ruling: the
ON switch is part of finishing — a capability with no way to turn it on is missing
functionality, not "dormant by design"). CI-1..4 shipped the code embed lane but with an
INERT flag, no daemon enqueue, and no CLI — this plan builds the switch. Implementation
proceeds item-by-item on owner approval; proposed→ready is the owner's hand.

## 1. Objective

Make the code embed lane runnable through the proper discipline: `[code_ingest].enabled`
becomes a real typed config the daemon reads, `code_sync` is enqueued into daemon housekeeping
(gated on `enabled`), and `palace code-seed` triggers the deliberate owner-visible seed on the
supervisor queue.

## 2. Context manifest

Read these, in order, before any work:

1. `docs/findings/finding-0159.md` — the warrant (the enable-path-is-finishing principle).
2. `docs/design-notes/code-ingest-pipeline.md` §2.7 — the seed-is-one-owner-visible-run ruling
   this wires (the seed stays owner-triggered; the incremental sync rides housekeeping).
3. `core/kernel/config/loader.py` — `SelfModConfig` (`:257`, the frozen-dataclass template),
   the top `Config` class (`:293`) + its `selfmod:` field (`:312`), and the toml assembly
   (`:339` section loop; `:500` `selfmod=SelfModConfig(...)`) where a section becomes typed.
4. `scheduler/code_sync.py` — `CODE_SYNC_KIND`, `code_sync_handler(sync)`, `enqueue_code_sync(
   queue, router)` (all built by bp-092; this plan only CALLS them).
5. `core/ingest/code_corpus.py` — `build_code_corpus_sync(config, repo=…)` (`:287`) + `.seed()`/
   `.sync()` (the runnable engine — unchanged by this plan).
6. `ops/lifecycle/launcher.py` — `build_components` (`:230`): the `handlers` dict (`:311`-ish,
   where `VAULT_SYNC_KIND`/`CHAT_SYNC_KIND` register) and `_housekeeping()` (enqueue_dream/
   curate/chat_sync) where `code_sync` attaches; and `Launcher.ingest_chat()` — the
   CLI-triggered-enqueue precedent `code_seed()` mirrors.
7. `scripts/palace.py` `main()` (`:202`) — the `if cmd == "…"` dispatch + `USAGE`; `ingest-chat`
   (`:245`) is the precedent for a new `code-seed` subcommand.
8. `config/defaults.toml` `[code_ingest]` (`:96`) — the currently-inert block (`enabled=false`).

## 3. Investigation & grounding

- **Q1 — Why is `[code_ingest].enabled` inert today?** The loader drops unknown sections; there
  is no `CodeIngestConfig` and nothing reads it (`config/defaults.toml:100-101` says so; grep
  confirms only `selfmod.enabled` is consumed). So the flag is decorative until this plan adds
  the schema. `[ESTABLISHED]`
- **Q2 — Is the seed engine complete?** Yes. `CodeCorpusSync.seed()` = `sync()` on an empty
  store, blob-sha-keyed, local embedder, idempotent (`core/ingest/code_corpus.py:259-285`).
  `build_code_corpus_sync()` wires it against the configured store + embedder + repo
  (`:287-320`). This plan changes NONE of it — it only makes it reachable.
- **Q3 — How does a config section become typed?** `SelfModConfig` (frozen dataclass, `enabled:
  bool = False`) + a `selfmod:` field on `Config` (default_factory) + `selfmod=SelfModConfig(
  **raw.get("selfmod", {}))`-style assembly in the loader (`:500`). Mirror exactly for
  `CodeIngestConfig`. **Code does not settle** the precise assembly call shape at `:500` — read
  the surrounding lines and copy the section's construction verbatim; do not infer.
- **Q4 — Where do sync KINDs enqueue?** Handlers register in `build_components`' `handlers`
  dict; periodic enqueue is in the local `_housekeeping()` (`enqueue_chat_sync(queue, router)`
  is the exact sibling). `code_sync` adds one handler entry + one gated enqueue. `[ESTABLISHED]`
- **Q5 — How does a CLI command reach the running daemon's queue?** `Launcher.ingest_chat()`
  (called from `palace.py:245`) is the precedent — a CLI-triggered enqueue. `code_seed()` mirrors
  it, calling `enqueue_code_sync`. **Code does not settle** whether `ingest_chat` enqueues into a
  live queue vs a one-shot; read it and mirror its exact mechanism (live-daemon vs standalone).
- **Q6 — Retrofit surface:** adding a `Config` field + a section may redden config tests that
  assert the `Config` shape or the loaded sections. `tests/unit/test_config*.py` (incl.
  `test_config_split.py`, touched by K1) is carried in `write_scope`; scan it for `Config(`/
  `selfmod`/section assertions before editing.

**Additional risks:** the seed is HEAVY (embeds all HEAD `.py`); §2.7 wants it owner-visible.
So housekeeping enqueues the INCREMENTAL sync only when `enabled` (cheap after seed); the SEED
is the deliberate `palace code-seed` (Item 3) — do not auto-run the first seed from housekeeping.

## 4. Reconciliation

- `config/defaults.toml:100-101` — the comment "this block is currently INERT … no
  CodeIngestConfig yet" → **[banner: correction]**: the comment is updated to cite this plan (the
  loader now schemas the section); an announced correction to committed config.
- `ops/lifecycle/launcher.py` `build_components` — **[cross-ref: extension]**: `code_sync` joins
  the handler registry + `_housekeeping`, gated on `cfg.code_ingest.enabled` — additive, the
  vault_sync/chat_sync pattern extended.
- `scripts/palace.py` `USAGE` + dispatch — **[cross-ref: extension]**: a new `code-seed`
  subcommand, mirroring `ingest-chat`.

## 5. Write scope

- `core/kernel/config/loader.py` — `CodeIngestConfig` + the `Config.code_ingest` field + the
  assembly. (Kernel file, agent-writable; not denylisted.)
- `ops/lifecycle/launcher.py` — the handler entry + gated housekeeping enqueue + `Launcher.
  code_seed()`.
- `scripts/palace.py` — the `code-seed` dispatch + `USAGE`.
- `config/defaults.toml` — the inert-comment correction + any `[code_ingest]` keys the schema
  reads (keep `enabled=false` — this plan builds the switch, does not flip it).
- `tests/unit/test_config*.py` — carried (retrofit; config-shape assertions).
- `tests/unit/test_code_ingest_wiring.py` (new), `tests/integration/test_launcher*.py` — the
  wiring tests.

**Deliberately OUT of scope:** `core/ingest/code_corpus.py` + `scheduler/code_sync.py` (the
engine + KIND — already built by bp-092, unchanged); the vector store; enabling any pattern
(`ENABLED_L2B_PATTERNS`, bp-094's gate — separate, needs F-CI6 samples); FLIPPING `enabled` to
true (that is the owner's runtime act, not this build); the foundation denylist.

## 6. Interfaces pinned inline

**Config template (`loader.py:257`, mirror for `CodeIngestConfig`):**
```
@dataclass(frozen=True)
class SelfModConfig:
    enabled: bool = False
    unattended_enabled: bool = False
    ledger_db: Path = Path("data/selfmod_ledger.sqlite")
```
`CodeIngestConfig` carries at least `enabled: bool = False` (+ `max_chars`/`overlap_chars` if the
lane should read them from config rather than the `code_corpus` defaults — optional; the note
chunker budget). Add `code_ingest: CodeIngestConfig = field(default_factory=CodeIngestConfig)` to
`Config`, and construct it in the loader assembly beside `selfmod=…`.

**The KIND + enqueue already built (bp-092, `scheduler/code_sync.py`) — CALL, don't redefine:**
```
CODE_SYNC_KIND = "code_sync"
def code_sync_handler(sync: CodeCorpusSync) -> Handler: ...   # handle(job) -> sync.sync()
def enqueue_code_sync(queue: JobQueue, router: Router) -> Job # BACKGROUND, pinned tier
```

**Daemon wiring (mirror the chat_sync sibling in `build_components`):**
```
handlers = { …, CHAT_SYNC_KIND: chat_sync_handler(build_chat_sensor(cfg)),
             CODE_SYNC_KIND: code_sync_handler(build_code_corpus_sync(cfg)), … }

def _housekeeping():
    enqueue_dream(queue, router); enqueue_curate(queue, router); enqueue_chat_sync(queue, router)
    if cfg.code_ingest.enabled:
        enqueue_code_sync(queue, router)     # incremental only; the SEED is `palace code-seed`
```

**CLI (mirror `Launcher.ingest_chat()` / `palace.py:245`):**
```
# palace.py main():   if cmd == "code-seed": return launcher.code_seed()
# launcher.py:        def code_seed(self): ...enqueue_code_sync(...)  # the deliberate owner-visible seed
```

## 7. Items

### Item 1 — `CodeIngestConfig` loader schema
- **Objective:** `[code_ingest].enabled` (and any lane knobs) are read into a typed frozen config.
- **Files:** `core/kernel/config/loader.py`, `config/defaults.toml` (comment correction),
  `tests/unit/test_config*.py` (+ the wiring test asserts `get_config().code_ingest.enabled is
  False` on defaults).
- **Acceptance test:** `uv run python -c "from core.kernel.config import get_config as g;
  print(g().code_ingest.enabled)"` prints `False`; a `local.toml` with
  `[code_ingest] enabled=true` yields `True`. Config tests green.
- **Falsifier:** the section still drops (reading `.code_ingest` raises/AttributeErrors) ⇒ the
  field/assembly wasn't wired; or an existing config test reddens un-carried.
- **Invariant(s):** frozen dataclass; default OFF (a fresh clone can't ingest until deliberate);
  no other section's typing changes.
- **Touches stored data?** No.  **Parallelizable?** No (shares loader).  **Depends on:** none.

### Item 2 — daemon enqueue (housekeeping, gated on enabled)
- **Objective:** the running daemon enqueues incremental `code_sync` when `enabled`, on the
  supervisor queue (single-writer, BACKGROUND, memory-gated).
- **Files:** `ops/lifecycle/launcher.py`, `tests/integration/test_launcher*.py` /
  `tests/unit/test_code_ingest_wiring.py`.
- **Acceptance test:** `build_components(cfg with code_ingest.enabled=True)` registers
  `CODE_SYNC_KIND` in `handlers` and `_housekeeping` enqueues one `code_sync`; with
  `enabled=False` it does NOT enqueue (assert the queue). No daemon restart required.
- **Falsifier:** `code_sync` enqueues while `enabled=False` (gate ignored), or the first
  housekeeping pass auto-runs the full SEED (should be Item 3's deliberate path only).
- **Invariant(s):** single-writer discipline (enqueue, never a direct store write);
  non-negotiable #8 (the loader's per-embed ceiling, unchanged); BACKGROUND priority.
- **Touches stored data?** No (enqueues; the handler embeds under the existing ceiling).
  **Parallelizable?** No.  **Depends on:** Item 1.

### Item 3 — `palace code-seed` (the deliberate owner-visible seed)
- **Objective:** one CLI command triggers the seed through the queue — the §2.7 owner-visible run.
- **Files:** `scripts/palace.py` (dispatch + USAGE), `ops/lifecycle/launcher.py`
  (`Launcher.code_seed()`), tests.
- **Acceptance test:** `uv run scripts/palace.py code-seed` (against a running daemon) enqueues
  one `code_sync`; `palace.py --help`/USAGE lists it; `code_seed()` mirrors `ingest_chat()`'s
  live-daemon enqueue mechanism. A unit test asserts `code_seed()` calls `enqueue_code_sync`.
- **Falsifier:** the command runs the seed OUTSIDE the queue (bypasses single-writer), or does
  nothing when the daemon is down without a clear message (mirror `ingest_chat`'s posture).
- **Invariant(s):** the seed rides the supervisor queue (never a raw store write from the CLI);
  loopback/egress guard (`seal()`) still runs first (palace.py:220).
- **Touches stored data?** No directly (enqueues the job that does, under the ceiling).
  **Parallelizable?** No.  **Depends on:** Items 1, 2.

## 8. Math carried explicitly

N/A — no mathematical object implemented (config + daemon wiring + a CLI command).

## 9. Non-goals

No change to the embed engine or the `code_sync` KIND (bp-092's, unchanged). No enabling of the
reference-edge patterns (bp-094's `ENABLED_L2B_PATTERNS`, needs F-CI6 samples). No flipping
`enabled` to true (owner's runtime act). No historical backfill (HEAD-only, PD-B). No φ_code /
observation-plane change.

## 10. Stop-and-raise conditions

`ingest_chat`'s enqueue mechanism turns out NOT to reach a live daemon queue cleanly (then the
seed-trigger design needs an owner decision — park Item 3, ship Items 1–2). A config test asserts
a `Config` shape this plan must change in a way that implies a semantic (not mechanical) shift
(file a finding). Any pressure to flip `enabled` on or run the seed as part of the build (that is
the owner's deskcheck act, not this plan).

## 11. Parked decisions

| Decision | Default recorded | Rejected alternatives (why) | Re-entry condition |
|---|---|---|---|
| lane knobs in config (max_chars/overlap) | read from `[code_ingest]` if present, else the `code_corpus` defaults | hardcode only (loses the note's corpus-wide budget tie) | a consumer needs to retune chunking without a code change |
| seed auto-run on first enable | NO — seed is `palace code-seed` (owner-visible, §2.7); housekeeping does incremental only | auto-seed on enable (a heavy op firing from a flag flip — violates §2.7 + the memory ceiling posture) | the owner asks for hands-off first-seed |

## 12. Dependency & ordering summary

Items linear 1→2→3 (schema → daemon enqueue reads the schema → CLI triggers the enqueue).
`depends_on: bp-092` (the KIND/handler/engine it calls — all sealed). Not parallel with anything
(shares loader + launcher). This plan is the enable path the CI-1..4 wave deferred (finding-0159);
after it, "turn on code ingest" = `palace code-seed` (deliberate) + `[code_ingest].enabled=true`
(incremental sync), both through the proper discipline. The seed RUN itself remains the owner's
deskcheck act.
