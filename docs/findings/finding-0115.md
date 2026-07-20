---
type: finding
id: finding-0115
status: open
created: 2026-07-19
updated: 2026-07-19
links:
  - docs/build-plans/bp-075/plan.md                # the exhaust-lane plan this obstructs (Item 1)
  - docs/design-notes/exhaust-lane.md              # §2.2: the exhaust root is pinned in config (SSOT)
  - core/config/loader.py                          # the schema'd loader that must gain ExhaustConfig
  - config/loader.py                               # the facade that re-exports it
re_entry: PARKED — Items 1 (code half) / 2 / 3 / 4 resume once the orchestrator makes the scope call and the exhaust root is surfaced via get_config() (a core/ ExhaustConfig, or a blessed config-only reader). The [exhaust] table (data half of Item 1) already landed in config/defaults.toml this session.
ftype: spec-fidelity
origin_plan: bp-075
route: orchestrator
resolution: null
---

# bp-075's `[exhaust]` config root cannot be surfaced via get_config() without a core/ change — the loader is schema'd, and write_scope excludes core/

## What
Settled at the START of the bp-075 build (Q2, before writing any code), by reading the loader. The
plan's Item 1 premise — add a top-level `[exhaust]` table to `config/defaults.toml` and read it via
`get_config()["exhaust"]["path"]` (§6) — **does not hold**, for a structural reason:

1. **`config/loader.py` is a thin FACADE** (bp-067). It only re-exports names from
   `core.config.loader`; it does no TOML parsing itself.
2. **The real loader, `core/config/loader.py`, is SCHEMA'D, not a passthrough.** `load_config()`
   does `raw = tomllib.loads(...)`, then constructs a **frozen `Config` dataclass** with exactly one
   typed field per *named* section (`ollama`, `resources`, `paths`, `vault`, `effectors`, …). Each
   field is read explicitly (`raw["vault"]`, `raw.get("effectors", {})`, …). **A section with no
   corresponding `Config` field is parsed into `raw` and then silently DROPPED** — it never reaches a
   caller. So `[exhaust]` in `defaults.toml` is inert until the loader is taught about it.
3. **Surfacing it requires a `core/`-side change:** an `ExhaustConfig` dataclass (a ~5-line mirror of
   `VaultConfig`), an `exhaust: ExhaustConfig` field on `Config`, a wiring block in `load_config()`,
   and a re-export line in the `config/loader.py` facade + its `__all__`. All the load-bearing edits
   live in `core/config/loader.py` — which bp-075 §5 lists as **deliberately OUT of write_scope**
   (`core/**`; the Q2 escape hatch is a finding, not scope creep).
4. **The §6 pinned access pattern is also unimplementable as written.** `get_config()` returns a
   *frozen dataclass* — `cfg["exhaust"]["path"]` (subscript) cannot work, and there is no `exhaust`
   attribute. Once the field exists the real form is `get_config().exhaust.path`.

Net: Item 1's config-only premise is false. The exhaust root cannot be surfaced through `get_config()`
without editing `core/config/loader.py`, which this plan's write_scope excludes.

## Why it matters
Item 1 is the foundation of the whole plan: **Items 2 (ingest-invariant test) and 3 (report writer)
are both pinned to read the exhaust root via `get_config()`** (§6, §7) — the exact blocked surface. So
the block cascades to 3 of 4 items (Item 4's cockpit guide documents the Item-3 writer, so it parks
too). No further implementation can proceed to the pinned interface until this is resolved. Surfaced by
grounding the plan against the loader's real shape before writing code (the `ground-before-building` /
finding-0104 pattern — same file, same class of obstacle).

## Options (orchestrator / owner decision)
- **A — widen write_scope to `core/config/loader.py` (RECOMMENDED; smallest, cleanest).** Add
  `core/config/loader.py` (+ `config/loader.py` facade) to bp-075's write_scope and add `ExhaustConfig`
  the same way `VaultConfig` / `EffectorsConfig` are wired (frozen dataclass, `.get`-defaulted,
  `expanduser()` on the path). ~15 lines, no trust boundary touched, no ratchet impact (a plain path
  field, like `vault`). Needs an owner re-bless of the widened write_scope. Then §6's pattern becomes
  `get_config().exhaust.path` (fix the subscript form in the plan), and Items 2/3/4 proceed unchanged.
- **B — read the config root without `get_config()` (config-only, stays in the current scope).** Have
  the writer + test read `config/defaults.toml` directly via stdlib `tomllib`. Rejected as-is: it
  duplicates the loader's overlay precedence (`defaults ← levers ← local`), so a `local.toml` exhaust
  override would be missed unless the overlay logic is re-implemented — a DRY defect (owner treats
  duplicated code as a smell) and a deviation from the §6 pinned interface. Only viable if the
  orchestrator explicitly blesses a small shared config-side reader.
- **C — split a tiny core-config plan** that lands `ExhaustConfig` first (its own write_scope over
  `core/config/`), then bp-075 becomes a clean config-data + scripts + docs build against a working
  `get_config().exhaust.path`.

## Re-entry condition
Items 1 (code half) / 2 / 3 / 4 resume once the orchestrator picks an option and the exhaust root is
reachable at the pinned interface. The DATA half of Item 1 (`[exhaust]` in `config/defaults.toml`,
matching note §2.1/§2.2 and §6) already landed this session, so any option starts from there.

## Routing
`spec-fidelity` discovery at build time → the resolution is a **write_scope / capability decision**
the builder cannot make (widening scope, or blessing a reader, is not a builder act) → **orchestrator**
(→ owner for the scope re-bless, as with finding-0104 on this same file).
