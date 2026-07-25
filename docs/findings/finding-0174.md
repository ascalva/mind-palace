---
type: finding
id: finding-0174
status: open
created: 2026-07-25
updated: 2026-07-25
links:
  - config/defaults.toml                               # [embedding] has no resident_gb; [[models]] tiers do
  - core/models/loader.py                              # the ceiling gate — sums resident_gb over TIER models only
  - scheduler/vault_sync.py                            # "calls the embedder directly … the worker slot is never evicted"
  - docs/brainstorms/local-model-runtime.md            # the llama.cpp-direct direction this bears on
  - CLAUDE.md                                          # non-negotiable 8 — respect the memory ceiling
ftype: spec-defect
origin_plan: orchestrator
route: orchestrator
resolution: null
---

# The memory ceiling is enforced over an incomplete accounting — the embedder is invisible to the loader

## What

`MemoryLoader` gates loads against `usable_ram_gb = 24.0` and `max_resident_models = 2` by summing
`resident_gb` across resident models (`core/models/loader.py:40-41`, `:58-64`). Every chat tier
declares that footprint:

| tier | model | `resident_gb` |
|---|---|---|
| router (pinned) | `qwen3.5:2b` | 2.7 |
| routine | `qwen3.5:9b` | 6.6 |
| synthesis | `qwen3.6:27b` | 17.0 |
| stretch (`evicts_pinned`) | `qwen3.6:35b-a3b` | **23.0** |

**The embedder declares nothing.** `[embedding]` (`config/defaults.toml:112-119`) carries `model`,
`dim`, and `query_instruction` — **no `resident_gb`, no `tier`, not a `[[models]]` entry at all.** It
is therefore never in `self._resident` and the ceiling gate cannot see it.

It is nevertheless really resident. `vault_sync` (and the code/chat lanes) "calls the embedder
directly" (`scheduler/vault_sync.py:9-11`) via Ollama, which holds it warm for
`default_keep_alive = "30m"` (`config/defaults.toml:10`). `qwen3-embedding:4b` is ~2.5 GB on disk
(`ollama list`).

Arithmetic the gate cannot do:

```
stretch tier          23.0 GB   (declared, gate-visible, and it evicts the pinned model)
embedder (4b)        + 2.5 GB   (real, warm for 30m, INVISIBLE)
                     ────────
                       25.5 GB   against usable_ram_gb = 24.0
```

The gate approves this, because it is summing an incomplete set.

## Why it matters

- **Non-negotiable 8 says "the scheduler refuses breaching work."** It refuses *declared* breaches.
  An undeclared consumer means the invariant is enforced over a model of memory, not memory — the
  guarantee is weaker than it reads, and nothing surfaces the gap.
- **It is most acute exactly where we were about to act.** The live question when this was found was
  whether to migrate to an 8B embedder (~5 GB at Q4). That would make the stretch-tier case
  23.0 + 5.0 = **28 GB on a 32 GB machine** before the OS and working set — and the gate would still
  approve it. Any reasoning about "can we afford a bigger embedder" is currently unfounded in
  either direction: **nobody is counting.**
- **It is the same species as finding-0169 and finding-0163** — a quantitative premise (here, the
  ceiling) trusted without the measurement that would make it true. Third instance in one week.
  See the reconciliation-audit 2026-07-25 capsule: *you cannot catch an inconsistency without first
  having made a consistency claim* — here the claim exists but its accounting is partial, which is
  arguably worse than absent, because it reads as enforced.

## What this does NOT say

It does **not** say the embedder must be co-resident with a chat model, and it does not say an
embedder upgrade is unaffordable. The scheduler already does swap-avoidance within a priority band
(`scheduler/queue.py:174`, `:188`) over a two-slot loader, and `vault_sync` routes to the **pinned**
tier precisely so embedding work never evicts the worker slot. The residency design is sound. The
defect is that one real consumer is outside its books.

## The fix — and why it is `orchestrator`, not `builder`

Mechanically, adding `resident_gb` to `[embedding]` and counting it is small. But the *right*
accounting depends on an unsettled design question, which is why this routes to design:

- Under **Ollama** (today), residency is opaque — Ollama decides when the embedder loads and
  unloads, on its own keep-alive, invisible to the palace. Declaring a static `resident_gb` would
  model that only crudely (is it resident? for how long? the palace does not know).
- Under **llama.cpp-direct** (the recorded direction, `docs/brainstorms/local-model-runtime.md`,
  2026-07-22), the embedder becomes a `llama-server` process the palace starts and stops, with an
  explicit budget and explicit lifetime. The accounting becomes *real* rather than declared.

That brainstorm's own open question is this finding in advance: *"Exact re-grounding of
`resident_gb` / `max_resident_models` against llama.cpp's REAL load/unload semantics."* This finding
is the measured instance that makes it concrete.

## Re-entry condition

Not blocking bp-100/101/102 (none touches the loader or the embedder). Re-entry: at the
llama.cpp-direct design pass, where the embedder's residency must be modelled explicitly — OR
sooner, if an embedder migration is seriously considered, in which case this must be settled FIRST
because the affordability question is unanswerable without it.

**Interim mitigation is knowledge, not code:** the ceiling gate does not see the embedder; do not
treat a gate approval as proof that a configuration fits.

## Routing

`design` → orchestrator. Batch with the llama.cpp-direct pass rather than as a standalone owner
question — it is one input to that design, not an independent decision. If an embedder migration is
proposed before that pass, promote it to an owner question at that point.
