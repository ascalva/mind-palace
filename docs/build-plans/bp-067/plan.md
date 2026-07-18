---
type: build-plan
id: bp-067
alias: config-split-loader-into-core
status: complete
design_ref:
  - docs/findings/finding-0103.md                  # THE WARRANT — the 106-import audit + the SPLIT ruling
  - docs/findings/finding-0104.md                  # the build-time obstacle + the owner's option-A scope widening
  - CONVENTIONS.md                                  # the self-containment + DRY rules (bp-066) this advances
contract: builder
write_scope:                                       # per-path rationale lives in §5 Write scope, never inline (bp-066 footgun)
  - core/config/**
  - core/**/*.py
  - config/loader.py
  - config/__init__.py
  - tests/unit/test_config_split.py
  - tests/integration/test_levers_overlay.py
  - tests/integration/test_secrets_backend_wiring.py
  - tests/unit/test_ci_witness.py
session_budget: 1
cost:
  estimate:
    model: opus
    tokens: 130k
  actual:
    model: opus                                    # in-session self-build (session-27); no delegation
    tokens: ~155k                                  # incl. the stop-and-raise round-trip + ruff/mypy iters
    ratio: ~1.2                                    # a shade over — the facade/get_secret entanglement +
    dollars: pending /usage relay                  #   the core.* stricter-mypy fixups were unforecast
    session_delta: pending /usage relay
    week_delta: pending /usage relay
    note: >-
      One stop-and-raise (finding-0104) before any code: the facade can't preserve
      monkeypatch-of-globals across a module move, so 3 coupled tests joined scope (owner option A).
      Deviation from the §6 toml pin: data stays in config/ (gitignore out of scope), loader reads by
      path. Ratchet 106→19 as planned; get_secret env/token split kept the trust boundary intact.
depends_on: [bp-066]
parallelizable_with: []
supersedes: null
superseded_by: null
warrant: docs/findings/finding-0103.md
created: 2026-07-18
updated: 2026-07-18                                 # re-scoped per finding-0104 (owner option A); awaits re-bless
re_entry: null
---

# Build Plan — split config: move the (pure, side-effect-free) loader into `core.config`

## 0. Mode & provenance — OWNER-DIRECTED cleanup (the config leg of finding-0103)
Not graduated from a design note — **owner-directed (2026-07-18)**, the first cleanup plan warranted by
finding-0103 (the 106-import audit) under the standing **core-is-sacred** principle (CONVENTIONS
§Trust boundaries, landed by bp-066). The ruling is fixed: config is IN-scope, remediated by a **SPLIT,
not DI** — a core-scoped config that LIVES INSIDE `core/`, and an outside config for the machinery. This
plan does the SECURE, security-neutral half: it relocates the **loader** (already stdlib-only and
side-effect-free) into `core.config` and repoints core's imports. The credential/Vault wiring —
`config.secrets_backend` and `get_secret`'s token branch, both network-capable and localized to
`core/factory/factory.py` — is DELIBERATELY NOT touched here: moving a trust-boundary (credential
authority, `hvac`/Vault) inside a wide mechanical sweep is how a boundary erosion slips by unseen. It
gets its own focused, adversarially-verified inversion plan (bp-068+). Owner-confirmed 2026-07-18:
option 1 (loader move → red 106 → ~18), "the most secure approach that keeps the spirit of the form."

**RE-SCOPED 2026-07-18 (finding-0104, owner option A).** Grounding the facade at build start found that
3 out-of-scope tests **monkeypatch `config.loader`'s module globals / functions** (`LEVERS_OVERLAY`,
`_LOCAL`, `get_config`) and expect `load_config`/the witness to honor the patch — which NO re-export
facade preserves across a module move (the patch lands on the facade; the function reads
`core.config.loader`'s globals). Those 3 tests test the loader that is moving, so they move/repoint WITH
it — added to `write_scope`. The owner chose this (option A) over folding a secret-backend injection
(option B) precisely to keep the credential trust boundary UNTOUCHED. The other ~147 non-core importers
(public-API only, and env-path `get_secret` callers) remain served by the facade, untouched.

## 1. Objective
`config.loader`'s definitions live at `core/config/` (core owns its own settings + paths); every core
module imports `from core.config import …`; the outside `config/` becomes a thin **re-export facade**
over `core.config` so the ~104 non-core importers are UNTOUCHED (outside → core is allowed, owner-ruled
2026-07-18). `core.config` is provably **side-effect-free and network-free** — `get_secret` in core is
the ENV path only (`os.environ.get`); the Vault-token capability stays OUTSIDE. The self-containment
ratchet (`test_core_self_containment`) drops from **106 to ~18**: the only remaining core → `config`
imports are the secrets/Vault-entangled ones in `factory.py` (deferred) + the 16 non-config machinery
reaches.

## 2. Context manifest (read in order)
1. `docs/findings/finding-0103.md` — the audit + the SPLIT ruling (config core-scoped INSIDE core).
2. `config/loader.py` — the module being moved. Public API: constants `REPO_ROOT`, `LEVERS_OVERLAY`;
   18 frozen dataclasses (`OllamaConfig … Config`); `load_config`, `get_config`, `refresh_config`,
   `get_secret`. Imports ONLY stdlib (`os`, `tomllib`, `dataclasses`, `functools.lru_cache`, `pathlib`)
   — no first-party coupling. **Two entanglement points to handle (below):** `REPO_ROOT =
   __file__.parent.parent` (`:15`) re-anchors when the module moves deeper; `get_secret`'s token branch
   (`:507-513`) lazily imports `config.secrets_backend` (the network Vault path).
3. `config/__init__.py` — the current public re-export (`Config, ModelConfig, OllamaConfig, PathsConfig,
   ResourceConfig, get_config, get_secret, load_config`). Becomes a facade over `core.config`.
4. `core/factory/factory.py` — the ONE core file that is secrets/Vault-entangled: `get_secret(name,
   token=self.token)` (`:82`, the Vault path), `from config.secrets_backend import build_secrets_backend`
   (`:179`), TYPE_CHECKING `MintedToken, SecretsBackend` (`:37`). These stay RED after this plan (the
   secrets-inversion, bp-068+). Its `from config.loader import get_config` (`:178`) DOES repoint.
5. `core/attestation/attestor.py:100,108` — the OTHER get_secret core caller: `get_secret(acfg.
   signing_key_secret)` — NO token (the env path). Repoints cleanly to `core.config.get_secret`.
6. `ops/import_lint.py:39-55` — the network/`hvac` ban on `core/`. After the move `core/config/**`
   falls under it — the security WIN (config loading becomes structurally network-proven). Confirm it
   passes (loader is stdlib-only; the env-only get_secret imports nothing banned).
7. `config/secrets_backend.py` (skim) — stays OUTSIDE core (holds the network `VaultClient`; `hvac`
   lazy + firewalled). NOT moved. Named here so the facade's token `get_secret` can reach it.
8. The 3 coupled tests (finding-0104), which repoint to `core.config.loader`:
   - `tests/integration/test_levers_overlay.py` — `monkeypatch.setattr(loader, "LEVERS_OVERLAY"/
     "_LOCAL", …)` + `load_config()` (`:18-20,30-39`). Repoint `import config.loader as loader` →
     `from core.config import loader` (patch the module that now owns `load_config`'s globals).
   - `tests/integration/test_secrets_backend_wiring.py` — `from config.loader import _DEFAULTS,…`
     (`:16`), `monkeypatch.setattr(loader, "_LOCAL", …)` (`:39`); the token `get_secret` case (`:65-70`)
     stays on the OUTSIDE facade (the token form lives there). Split its imports: loader internals from
     `core.config.loader`, the token `get_secret` from `config.loader`.
   - `tests/unit/test_ci_witness.py` — `monkeypatch.setattr(config.loader, "get_config", …)` (`:264`):
     repoint the patch target to wherever the witness now reads `get_config` (`core.config`).

## 3. Investigation & grounding
- **The loader is a clean move.** Stdlib-only, `lru_cache`'d pure TOML reads returning frozen
  dataclasses — zero side effects, zero network, no first-party import. Relocating it adds core NO
  capability; it only brings config loading INSIDE the sealing/import-lint perimeter (a strengthening).
- **The tomls it reads move with it:** `defaults.toml` (committed base), `local.toml` (gitignored
  overrides — its gitignore entry must follow), `levers.toml` (`LEVERS_OVERLAY`, self-mod overlay, read
  if present). `tuning.toml` + `sweeps/` are NOT loader-read (dreamer/eval tuning) → they STAY outside.
- **`REPO_ROOT` re-anchor (correctness).** `config/loader.py:15` computes repo root as
  `Path(__file__).resolve().parent.parent` (config/ → root). At `core/config/loader.py` that is
  `parent.parent.parent` (core/config/ → core/ → root). MUST be fixed or every derived path breaks.
- **`get_secret` splits at the trust boundary (the security crux).** Core's env path
  (`os.environ.get(name)`) is pure and network-free; the token path lazily reaches `secrets_backend`
  (Vault/network). Core's `get_secret` in `core.config` is the **env path ONLY** — no `token` param, no
  `secrets_backend` import — so the network Vault path CANNOT leak into anything core.config exposes.
  The attestor (env caller) is served. The token-capable `get_secret(name, token=None)` lives in the
  outside facade (it may reach `secrets_backend` — the machinery zone). `factory.py`'s token call keeps
  importing the outside `config` version ⇒ stays RED (the deferred secrets-inversion).
- **The facade bounds the repoint to core.** Making `config/loader.py` + `config/__init__.py`
  re-export from `core.config` keeps every non-core importer (`from config.loader import …`, 104 files)
  working unchanged. Only the ~47 core files repoint. Re-export is NOT duplication (DRY-clean): one
  source of truth (`core.config`), the facade holds none of the definitions.
- **Post-move red (honest arithmetic).** 106 = 90 config + 8 ops + 7 eval + 1 agents. The move fixes
  every core `config.loader` import that resolves to a pure symbol (get_config, Config, the dataclasses,
  REPO_ROOT, the env get_secret) — ~87 of the 88 loader imports. It does NOT touch factory's Vault
  `get_secret` (`:80`) or the 2 `secrets_backend` imports. So red → ~18: factory's secrets/Vault
  reaches + the 16 non-config machinery reaches. The exact N is whatever the ratchet reports; the
  acceptance asserts the REMAINING set is exactly those.

## 4. Reconciliation
- `config/loader.py` — RELOCATED, not superseded: definitions move to `core/config/loader.py`; the old
  path becomes a re-export facade (banner-comment: "facade — definitions live in `core.config`;
  outside→core is the allowed arrow, finding-0103/bp-066"). No behavior change for outside callers.
- `config/loader.py:15` `REPO_ROOT` — CORRECTION (the move breaks the relative anchor): re-anchored in
  the moved module, with a comment naming the depth change. Announced, never silent.
- `config/loader.py:492` `get_secret` — EXTENSION-by-split: core gets the env-only form; the outside
  facade keeps the token-capable form delegating env→`core.config`. A comment at each site grounds the
  split in the network-boundary (Invariant 1) + finding-0103.
- No design-note edit (engineering cleanup under the ratified principle). No `core/**` logic change
  beyond import lines + the loader's own relocation.

## 5. Write scope
`core/config/**` (the moved loader + tomls + `__init__`), `core/**/*.py` (import repoint — LINE-level:
`from config… import X` → `from core.config import X`; NO logic edits), `config/loader.py` +
`config/__init__.py` (the facade), a new `tests/unit/test_config_split.py` (the falsifiers), and the 3
coupled tests that monkeypatch loader internals and so must repoint with the loader (finding-0104):
`tests/integration/test_levers_overlay.py`, `tests/integration/test_secrets_backend_wiring.py`,
`tests/unit/test_ci_witness.py`. **OUT:** `config/secrets_backend.py`, `config/tuning.toml`,
`config/sweeps/**`; the ~147 non-core importers that use only the public API or the env-path
`get_secret` (the facade spares them — verified: only those 3 tests monkeypatch loader internals);
`core/factory/factory.py`'s secrets/Vault imports (the deferred inversion — its `config.loader`
get_config import DOES repoint, but its get_secret-token + secrets_backend imports stay);
`CONSTITUTION.md`, `eval/golden/**` (denylist).

## 6. Interfaces pinned inline
```python
# core/config/loader.py — REPO_ROOT re-anchored (module now two levels deeper than the old config/):
REPO_ROOT = Path(__file__).resolve().parent.parent.parent   # core/config/loader.py → core/ → <root>
_DEFAULTS = Path(__file__).resolve().parent / "defaults.toml"     # tomls move alongside the module
_LOCAL    = Path(__file__).resolve().parent / "local.toml"
LEVERS_OVERLAY = Path(__file__).resolve().parent / "levers.toml"

# core/config/loader.py — get_secret is the ENV PATH ONLY (network-free; no token param, no
# secrets_backend import — the Vault path stays OUTSIDE core, Invariant 1 / finding-0103):
def get_secret(name: str) -> str | None:
    """Fetch a secret from the environment (Keychain-backed in the owner's setup). Env-only by
    design: the token/Vault path is machinery (config.secrets_backend, network) and lives in the
    outside facade — core.config never names it, so no network path can leak in (Invariant 1)."""
    return os.environ.get(name)

# core/config/__init__.py — the single public surface core imports from:
from core.config.loader import (              # re-export the pure API
    Config, OllamaConfig, ResourceConfig, PathsConfig, VaultConfig, EmbeddingConfig, DreamingConfig,
    DreamRnDConfig, InterfaceConfig, AmbassadorConfig, EffectorsConfig, AirlockConfig,
    AttestationConfig, SecretsConfig, BackupConfig, SelfModConfig, SandboxConfig, ModelConfig,
    REPO_ROOT, LEVERS_OVERLAY, load_config, get_config, refresh_config, get_secret,
)

# config/loader.py (OUTSIDE) — FACADE: re-export core.config, PLUS the token-capable get_secret that
# the machinery uses (it MAY reach secrets_backend — the machinery zone):
from core.config.loader import *          # noqa: F403 — pure re-export, one source of truth
from core.config.loader import get_secret as _env_secret
def get_secret(name: str, token: str | None = None) -> str | None:
    if token is not None:
        from config.secrets_backend import build_secrets_backend
        backend = build_secrets_backend()
        if backend is None:
            raise RuntimeError("a token was passed but [secrets] is not enabled")
        return backend.read_secret(name, token)
    return _env_secret(name)

# core import repoint — every core file, LINE-level, e.g.:
#   from config.loader import get_config, Config   →   from core.config import get_config, Config
#   from config import Config                       →   from core.config import Config
# EXCEPT core/factory/factory.py's `from config.loader import get_secret` (Vault token, :80) and its
# `from config.secrets_backend import …` — those STAY (the deferred secrets-inversion, bp-068+).
```

## 7. Items
### Item 1 — relocate the loader into `core/config/`  (blast: a module + data move; reversible)
- **Objective:** `git mv config/loader.py core/config/loader.py`; move `defaults.toml`, `local.toml`,
  `levers.toml` alongside; add `core/config/__init__.py` (the re-export). Re-anchor `REPO_ROOT`. Split
  `get_secret` to the env-only form. Follow `local.toml`'s gitignore to the new path.
- **Acceptance test:** `python -c "from core.config import get_config; c=get_config(); print(c.paths.derived_store)"`
  resolves to the SAME path as before the move (REPO_ROOT correct); `uv run ruff check core/config/` +
  `uv run mypy core/config/loader.py` clean; `test_config_split.py::test_config_values_unchanged`
  green (a field-by-field compare of `get_config()` against a snapshot of the pre-move values).
- **Falsifier:** any `get_config()` field differs pre/post (a path mis-anchored, a toml not moved); a
  `token`/`secrets_backend`/`hvac` symbol reachable from `core.config` (the Vault path leaked in);
  `core.config.get_secret` accepting a `token` arg.
- **Invariant(s):** side-effect-free (no writes/network on import or call); config values byte-identical;
  the env-only get_secret. **Touches stored data?** No (reads config; writes nothing).  **Parallelizable?** No.

### Item 2 — repoint core's imports + build the outside facade + repoint the 3 coupled tests  (blast: line-level import edits)
- **Objective:** repoint every core `from config… import <pure symbol>` → `from core.config import …`
  (EXCEPT factory's secrets/Vault lines); make `config/loader.py` + `config/__init__.py` re-export
  facades (with the token-capable `get_secret`); repoint the 3 monkeypatch-coupled tests (finding-0104)
  to patch `core.config.loader`'s globals/functions (their token-`get_secret` assertions stay on the
  outside facade).
- **Acceptance test:** `uv run pytest -q` is green-except-the-intentional-ratchet; the FULL suite's
  non-core tests (which import `config.*`) pass unchanged (the facade holds); the 3 repointed tests pass
  (their monkeypatches now bite the real module); `test_config_split.py` asserts the outside
  `config.loader` still exposes the full API incl. the token `get_secret`.
- **Falsifier:** a non-core importer breaks (facade incomplete); a core file still importing
  `config.loader` for a pure symbol (repoint missed); a repointed test's monkeypatch still inert (wrong
  target module); the facade re-implementing (not re-exporting) any definition (a DRY violation / second
  source of truth).
- **Invariant(s):** outside→core only (never core→outside for a pure symbol); one source of truth
  (facade re-exports, defines nothing but the token get_secret wrapper).  **Touches stored data?** No.  **Parallelizable?** No (after item 1).

### Item 3 — the ratchet drops + core stays network-free  (blast: verification)
- **Objective:** confirm the deliverable: red 106 → N with the remaining set EXACTLY the deferred
  factory secrets/Vault reaches + the 16 machinery reaches; `core/config/**` passes `import_lint`.
- **Acceptance test:** `uv run pytest tests/unit/test_core_self_containment.py -q` still fails (RED by
  design) but at **N ≈ 18**, and its enumeration contains NO `→ config` line except the factory
  secrets-entangled ones; `uv run python ops/import_lint.py` (or its test) passes over `core/config/**`
  (no hvac/socket/http); `test_config_split.py::test_core_config_is_network_free` asserts an AST scan of
  `core/config/**` imports nothing in the `import_lint` banned set.
- **Falsifier:** the red count did NOT drop by ~87; a surviving `core → config.loader` pure-symbol
  import; any banned import under `core/config/**`.
- **Invariant(s):** the ratchet is monotone (only decreases); core.config network-free.  **Touches stored data?** No.  **Parallelizable?** No.

## 8. Math carried explicitly
N/A — no mathematical object. A module relocation + an import-graph edit + two prose-level boundary
splits (get_secret env/token; the facade).

## 9. Non-goals
NO secrets-inversion (factory's Vault `get_secret` + `secrets_backend` wiring + `ops/effect_exec.py`'s
matching `build_secrets_backend` — bp-068+, its own security-focused plan). NO move of
`config.secrets_backend` into core (it holds the network `VaultClient`; `hvac` is core-banned —
Invariant 1). NO move of `tuning.toml`/`sweeps/` (machinery tuning, not loader-read). NO repoint of the
104 non-core importers (the facade spares them; a later sweep may migrate them, out of scope). NO logic
change to any config value or any core module beyond its import lines. NO weakening of the ratchet test.

## 10. Stop-and-raise conditions
- A `get_config()` field changes pre/post the move → STOP: a path/toml/anchor is wrong; the config must
  be byte-identical (a silent config drift is a latent production bug). Fix before proceeding.
- The env/token `get_secret` split would force factory's Vault path into `core.config` (i.e. a core file
  other than factory.py uses the token path) → STOP, file a `codebase` finding: the secrets entanglement
  is wider than factory alone and the inversion scope must grow.
- `core/config/**` trips `import_lint` (a banned import rides in with the loader) → STOP: the loader was
  not as pure as audited; re-examine before landing it inside the sealed perimeter.
- Any pressure to also invert the secrets wiring "while we're here" → STOP (§0): the trust-boundary
  change is a SEPARATE, adversarially-verified plan by design.
- Any blessing (`proposed→ready`, `draft→ratified`): never.

## 11. Parked decisions
| Decision | Default recorded | Rejected alternatives (why) | Re-entry condition |
|---|---|---|---|
| the secrets/Vault inversion | DEFERRED to bp-068+ (its own security-focused plan) | fold into this plan (mixes a wide mechanical move with a credential trust-boundary change — the exact place an erosion hides) | this plan lands + the owner blesses the secrets-inversion plan |
| migrate the 104 non-core importers to `core.config` | NO — keep the facade (outside→core, allowed) | repoint all 151 files now (churns tests/scripts/ops for no ratchet gain; the red only counts core) | a later "retire the config facade" cleanup, if ever wanted |
| `core/config/` package vs `core/config.py` + tomls elsewhere | a package (holds loader + the tomls it reads, mirrors the old config/) | a single module (the 3 tomls would need a separate home + path logic — more moving parts) | never (the package is the clean shape) |

## 12. Dependency & ordering summary
`depends_on: bp-066` — this plan is measured against bp-066's ratchet test (it must drop the count, not
break the test). Items serial: 1 (relocate + re-anchor + get_secret split — the foundation) → 2 (repoint
core + facade — needs the new module) → 3 (verify the drop + network-free — needs both). Blast radius:
read-only/mechanical throughout (a module move + import lines; the loader writes nothing). **Downstream:**
the secrets-inversion (bp-068+) clears factory's remaining reaches; the 16 machinery inversions clear the
rest → the ratchet reaches zero and the suite goes fully green. This plan is the single biggest drop
(106 → ~18) and the security-neutral one.
