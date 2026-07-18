---
type: finding
id: finding-0104
status: open
created: 2026-07-18
updated: 2026-07-18
links:
  - docs/build-plans/bp-067/plan.md                # the config-split plan this obstructs
  - config/loader.py                               # the module being moved
  - config/secrets_backend.py                      # the network Vault path get_secret's token branch reaches
re_entry: awaiting owner decision on scope (A/B/C below); bp-067 is parked in-progress with no code changes
ftype: spec-fidelity
origin_plan: bp-067
route: orchestrator
resolution: null
---

# bp-067's clean loader move is blocked: out-of-scope tests couple to loader internals + the get_secret token path

## What
Discovered at the START of the bp-067 build (before any code change). The plan's premise — move
`config.loader` into `core.config`, leave the ~104 non-core importers untouched behind a re-export
facade — does not hold, for a structural reason:

1. **Core needs `get_config`/`load_config`** (39+ imports), so those MUST move into `core.config`.
2. **~7 OUT-OF-SCOPE files couple to `config.loader`'s INTERNALS**, not just its public API:
   - `tests/integration/test_levers_overlay.py`, `test_secrets_backend_wiring.py`,
     `test_lifecycle.py` — `monkeypatch.setattr(loader, "LEVERS_OVERLAY"/"_LOCAL", …)` then call
     `load_config()`. A re-export facade does NOT preserve this: the patched name lives in
     `config.loader`, but `load_config` reads its globals from `core.config.loader` — the patch is
     inert and the test fails. **No facade trick preserves monkeypatch-of-module-globals across a
     module move.**
   - `test_secrets_backend_wiring.py`, `test_secrets_backend.py`, `test_ci_witness.py`,
     `scripts/{review,verdict}.py` — import privates (`_DEFAULTS`, `_LOCAL`) or `get_secret`.
3. **`get_secret`'s token branch is the network Vault path** (lazily imports `config.secrets_backend`).
   It CANNOT live in `core.config` (Invariant 1 / `import_lint` bans `hvac` from core). So core's
   `get_secret` must be env-only — but `test_secrets_backend_wiring.py:70` and `factory.py:82` need the
   token-capable form under `config.loader`. A transparent `sys.modules` alias (which WOULD fix the
   monkeypatch problem) forces core's env-only `get_secret` onto those callers ⇒ their token path
   breaks. The two requirements pull the facade in opposite directions.

Net: the loader move cannot leave every out-of-scope caller untouched. The tests that exercise the
loader's internals must move/repoint WITH the loader — which bp-067's write_scope excluded.

## Why it matters
bp-067 is the single biggest ratchet drop (106 → ~18) and the owner chose it (option 1) specifically to
keep the secrets/Vault trust boundary ISOLATED from a wide mechanical sweep. The obstacle forces a
choice about HOW to preserve behavior, and one of the options (a backend-resolver injection) would pull
that very boundary into this plan — the thing option 1 was meant to avoid.

## Options (owner decision)
- **A — expand scope to the coupled tests/scripts (RECOMMENDED).** Add the ~7 files to bp-067's
  write_scope; repoint them to `core.config.loader` (patch its globals, import its privates). Keep
  `get_secret` env-only in `core.config`; the token-capable `get_secret` stays a real function in the
  outside `config/loader.py` facade (for the outside callers + the moved token test). Trust boundary
  UNTOUCHED — this only acknowledges that tests of the loader move with the loader. Red → ~18. Needs an
  owner re-bless of the widened write_scope.
- **B — inject a backend resolver (folds a slice of the secrets inversion).** Give `core.config`'s
  `get_secret` a registered `_backend_builder` hook (default None ⇒ raise) so it is token-capable
  WITHOUT importing `config.secrets_backend`; then `config.loader` can transparently alias
  `core.config.loader` and every out-of-scope test passes UNCHANGED. Red → ~16. But it touches the
  credential trust boundary inside this plan — what option 1 deferred.
- **C — reorder: do the secrets inversion FIRST** (its own security-focused plan), which removes
  `get_secret`'s token path from the equation, THEN the loader move is a clean mechanical facade.

## Routing
`spec-fidelity` discovery at build time → orchestrator → owner (the scope/boundary decision). Surfaced
by grounding the facade against the actual out-of-scope callers before writing any code.
