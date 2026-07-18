# Journal — bp-067 (config-split: move the loader into core.config)

## 2026-07-18 — minted (proposed), awaiting owner bless
Owner-directed (2026-07-18), the config leg of finding-0103's cleanup program under the core-is-sacred
principle (bp-066). Owner chose **option 1** — the loader move (red 106 → ~18) — after asking for "the
most secure approach that keeps the spirit of the form"; the secrets/Vault inversion is DELIBERATELY
deferred to its own adversarially-verified plan (bp-068+) rather than smuggled into a wide mechanical
sweep. Status `proposed` — awaits the owner's `proposed → ready` blessing (owner-only, by hand).

**Grounding carried in the plan (so a fresh builder needn't re-derive):**
- `config/loader.py` is stdlib-only + side-effect-free (`lru_cache`'d pure TOML reads → frozen
  dataclasses). Clean move into `core/config/`. Its tomls (`defaults/local/levers.toml`) move with it;
  `tuning.toml`/`sweeps/` stay outside (not loader-read).
- TWO entanglements, both pinned in §6: `REPO_ROOT = __file__.parent.parent` re-anchors to `.parent
  .parent.parent` (module now two levels deeper); `get_secret`'s token branch lazily reaches
  `config.secrets_backend` (network Vault) — so core's `get_secret` is the ENV path ONLY, the
  token-capable form stays in the outside facade.
- The entire core secrets/Vault/network entanglement is LOCALIZED to `core/factory/factory.py` (the one
  core file using the Vault `get_secret` token path + the 2 `secrets_backend` imports). It stays RED
  after this plan — the deferred inversion. The attestor (env-path get_secret) repoints cleanly.
- The outside `config/` becomes a re-export FACADE over `core.config` → the 104 non-core importers are
  untouched; only the ~47 core files repoint. Facade re-exports (defines nothing but the token
  get_secret wrapper) ⇒ one source of truth, DRY-clean.
- Security WIN: once inside `core/`, config loading falls under `import_lint`'s network ban — config
  loading becomes structurally network-proven (it wasn't, as an outside module).

**Next action when blessed:** item 1 (relocate + re-anchor + get_secret split) → item 2 (repoint core +
facade) → item 3 (verify red drops 106→~18 with the remaining set = factory secrets + the 16 reaches,
and core/config/** is network-free). Estimate opus/130k. ⚠️ The suite stays RED-by-design (the ratchet)
— acceptance = the ONLY failure is `test_core_self_containment` AND its count dropped to ~18.

---

## 2026-07-18 (session-27) — STOP-AND-RAISE at build start (NO code changes) → finding-0104
Owner blessed `ready`; I set active-plan + flipped `ready → in-progress`, then grounded the FACADE
against the actual out-of-scope callers BEFORE writing any code (§10 discipline + the "scrutinize the
measurement code before it builds" lesson). Found a structural blocker:

- Core needs `get_config`/`load_config` (39+ imports) → those MUST move to `core.config`. But ~7
  OUT-OF-SCOPE files couple to `config.loader`'s INTERNALS: `test_levers_overlay`,
  `test_secrets_backend_wiring`, `test_lifecycle` monkeypatch `config.loader.{LEVERS_OVERLAY,_LOCAL}`
  and call `load_config()` — a re-export facade does NOT preserve this (the patch lands on the facade,
  `load_config` reads core.config.loader's globals). No facade trick preserves monkeypatch-of-globals
  across a module move.
- `get_secret`'s token branch is the network Vault path (can't be in core; `import_lint` bans hvac).
  So core's get_secret is env-only — but the token test + factory need the token form under
  `config.loader`. A transparent sys.modules alias (which would fix monkeypatch) forces env-only onto
  them ⇒ their token path breaks. The two pull the facade in opposite directions.

⇒ The loader move cannot leave every out-of-scope caller untouched (the plan's premise). The coupled
tests must move/repoint WITH the loader — which the write_scope excluded. Filed **finding-0104** with
three options (A: widen scope to the ~7 coupled files [recommended, boundary untouched, →18]; B: inject
a backend resolver [folds a secrets-inversion slice, →16]; C: secrets inversion FIRST, then clean move).

**PARKED in-progress** (re-entry: owner picks A/B/C). Zero code changes — clean to revise the plan and
resume. active-plan pointer still set; status left `in-progress`.

## 2026-07-18 (session-27) — RE-SCOPED per finding-0104 (owner option A); back to proposed
Owner chose **option A**: widen scope to the 3 monkeypatch-coupled tests, keep the trust boundary
untouched. Revised the plan: write_scope +3 tests (`test_levers_overlay`, `test_secrets_backend_wiring`,
`test_ci_witness`); §0 records the re-scope; §2 adds the 3 tests + how each repoints; §5/§7 updated
(item 2 now also repoints the coupled tests). Verified by exhaustive sweep that ONLY those 3 files
monkeypatch loader internals — the other ~147 non-core importers are facade-served (public API / env
get_secret). Status `in-progress → proposed`; active-plan cleared. **Awaits the owner `proposed→ready`
re-bless (by hand), then `/build bp-067` resumes from item 1.** finding-0104 resolved.
