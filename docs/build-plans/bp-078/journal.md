# bp-078 — journal

## 2026-07-20 — minted at re-graduation (orchestrator, session-37, opus@high)

Re-graduated from `dn-plane-principals` (ratified `215070d`), which supersedes
`dn-ouroboros-principal` on warrant `finding-0116`. **bp-078 supersedes bp-076**
(three-place, `dn-supersession-lifecycle` shape): bp-076 was graduated from the
now-superseded two-principal note and, as written, would `chown`
`exhaust/reports/` `ouroboros`-write-only — re-introducing exactly finding-0116
(workflow can no longer place build reports). bp-076 flipped to `superseded`
(`superseded_by: bp-078`), stays inspectable; its journal's 8-point delta is the
checklist this plan discharges.

**All 8 deltas discharged:**
1. Four role accounts + shared group `palace` → §6 matrix, Item 6 runbook.
2. `exhaust/reports/` = `ouroboros-work` (finding-0116 fix) → §3 Q7, §6, Item 4/6.
3. Cockpit `sudo -u ouroboros-work -H claude` + credential grounding → §3 Q8/Q9
   (Q9 = THE sharp item, a legitimate spike; STOP-gate in §10 + Item 6), git
   signing under `-H` → §3 Q10.
4. pf anchor (block core off-host egress + lo0 carve-out) → §3 Q11, Item 3.
5. Shared-repo mechanics (setgid, `core.sharedRepository`, umask) → Item 6.
6. `data/` runtime ownership → §3 Q12 (decision: `chown` not relocate), Item 4/6.
7. Ambassador relocation → **DEFERRED** (§3 Q13, §9, §11): entangled with the
   `data/handoff`-inside-`data/` grounding and a zone-crossing code move; the
   `ouroboros-edge` USER is still created (forward-provision). Re-entry parked.
8. Per-plane ratchets (self-configuring skip/enforce) → Item 5.

**Grounding done at re-graduation (§3):** carried bp-076's launcher grounding
intact (Q1–Q3, Q5, Q6 unchanged by the four-user generalization). New:
- **Q10 (sharp catch):** git signing is currently GLOBAL, not repo-local —
  `user.signingkey=/Users/ascalva/.ssh/id_ed25519.pub`, `gpg.format=ssh`,
  `commit.gpgsign=true` in `~/.gitconfig`. Under `sudo -u … -H`, HOME changes and
  the global config is NOT read → signing silently breaks. This confirms the
  note §3.2 "repo-local, HOME-independent" prescription is *necessary*, not tidy,
  and pins the accepted residual to a concrete path (`ouroboros-work` reads
  `/Users/ascalva/.ssh/id_ed25519` or ssh-agent).
- **Q12:** `data/` is the daemon's live sink — four plists → `data/logs/*`
  (`com.mind-palace.palace.plist:60,63` + token-rotate/backup/vault) and
  `data/runs.sqlite` (`ops/lifecycle/runs.py:10`). Decision: `chown` to
  `ouroboros:palace`, not relocate; cockpit tails as a group reader
  (`cockpit.sh:26`).
- **Q13:** `interface.handoff_dir = "data/handoff"` is INSIDE `data/`
  (`config/defaults.toml:128`); the ambassador is wired in the daemon
  (`launcher.py:149-152`). The note's `palace-io` airlock split only pays off
  once edge is a distinct uid → why the relocation defers cleanly.

**BUILDER DISCIPLINE (loud):** this build performs NO migration step. Every
mutating act is owner-run from Item 6's runbook. The builder writes code + an
inert pf anchor + docs + tests that SUPPORT and PROVE the move; it never creates
a user/group, chowns, or touches launchd/keychain/pf/`.git/config`/Syncthing.
The finding-0118 lesson is baked into Item 4's invariant: exercise
`uv run scripts/verify_planes.py` end-to-end, not just the imported fns.

Est. 250k, opus@high (owner-set for the trust-boundary weight). If it doesn't fit
one session, file `spec-defect` and re-graduate — do NOT re-split mid-build.

Status: `proposed`. Awaiting the owner's `palace bless bp-078` + hand commit
(proposed→ready is owner-only, by hand).

## 2026-07-20 — build start + grounding (delegated builder, opus@high, worktree)

Blessed `ready` (`6b8e4a5`); worktree rebased onto main to obtain the plan. Status
flipped `ready → in-progress` (`0e98112`, no trailer). Context manifest read in
order: plan whole → dn-plane-principals (§3.1/3.2/3.4/4) → dn-ouroboros-principal
(§2/3.1/3.2/3.5/3.6 retained) → launcher.py whole → the gui plist → both lifecycle
tests → cockpit.sh → config/defaults.toml + core/config/loader.py → vault-unseal.sh.

**Read-only grounding probes (mutated nothing):**
- **Q10 CONFIRMED on this machine (2026-07-20):** global git signing is
  `user.signingkey=/Users/ascalva/.ssh/id_ed25519.pub`, `gpg.format=ssh`,
  `commit.gpgsign=true`, `user.email=ascalva@gmail.com`; NO repo-local signing
  config (`git config --local --get user.signingkey` empty). Under `sudo -u … -H`
  the global `~/.gitconfig` is not read → signing silently breaks unless the
  runbook writes repo-local config. The note's "repo-local, HOME-independent"
  prescription is NECESSARY, not tidy.
- **Role accounts + `palace` group ABSENT** (pre-migration, as expected):
  `id ouroboros{,-work,-edge}` all fail; no `palace` group. So `pwd.getpwnam`
  raises for the three users — the verifier + ratchets MUST degrade to
  skip/PENDING (never crash) when a principal is absent. This is the primary
  self-configuring signal.
- **pfctl parse (Item 3) — a finding-0118-style env truth:** `pfctl -n -f <file>`
  runs WITHOUT sudo and DOES parse-check (broken syntax → rc 1). BUT `user
  ouroboros` fails `pfctl -n`: "unknown user ouroboros" (rc 1) because the user
  does not exist yet. So the LITERAL Item-3 acceptance command (`pfctl -n -f
  ops/network/ouroboros-egress.pf.conf`) cannot pass pre-migration. RESOLVED
  INLINE (spec-fidelity, builder-owned): the committed anchor names `user
  ouroboros` (the real post-migration form; a numeric uid is unknowable pre-create,
  and any existing user would be wrong). Its PROOF is split: (1) ordering falsifier
  = a pure text assertion that the `pass … lo0` line precedes the `block … user
  ouroboros` line (needs no pfctl); (2) syntax = `pfctl -n -f` on a copy with
  `ouroboros` substituted by a resolvable user, skipped if pfctl absent. The
  runbook makes the literal `pfctl -n -f <file>` a POST-user-creation verify step.
- **Config loader (finding-0115 lineage):** `core/config/loader.py::load_config`
  builds `Config` section-by-section and SILENTLY IGNORES unknown TOML sections
  (they land in `raw`, are never read, and `Config` does not choke). So adding
  `[planes]` to defaults.toml is SAFE (test_config_split does not enumerate
  sections) BUT it is NOT surfaced via `get_config()` — there is no `PlanesConfig`
  and `core/config/loader.py` is OUT of write_scope. Therefore verify_planes.py +
  the ratchets read the `[planes]` block by a direct `tomllib` parse of
  defaults.toml (with the local.toml overlay honored), not via `get_config()`.
  The vault path IS exposed (`get_config().vault.path`) and is read that way.
- **Q9 (Claude Code credential for `ouroboros-work`) — SPIKE disposition:** the
  metadata probe of the credential stores was DENIED by the auto-mode guardrail
  (non-negotiable #10, "secrets never read by a model") — correctly, and that
  denial is itself the answer: a service user's credential store is NOT
  agent-probeable by design. I did not work around it. So the empirical bootstrap
  (authenticate `claude` once as `ouroboros-work`, observe where the credential
  lands + whether a locked keychain breaks the pane relaunch) is INHERENTLY
  owner-run. Grounded from documented behavior: Claude Code on macOS keeps its
  OAuth credential in the login Keychain (service `Claude Code-credentials`) or, on
  Keychain-less platforms, `~/.claude/.credentials.json`; it also honors
  `apiKeyHelper` and `ANTHROPIC_API_KEY`. Runbook Item 6 pins the BOOTSTRAP-AND-
  VERIFY STOP-gate with the §3.2 mitigation order (a: `security unlock-keychain`
  in the cockpit wrapper → b: apiKeyHelper/env). Filing finding-0120 (direction,
  route: orchestrator) so the owner runs the empirical settle; NOT inventing a path.

**Import firewall** scans `core/` only — verify_planes.py (scripts/) is exempt and
may use `subprocess`/`pwd`/`grp`. It stays repo-workflow tooling: stdlib + `config`
facade, NEVER `core` (docket/exhaust_report AST precedent), asserted by a no-core
AST test.

## 2026-07-20 — Item 1 DONE (domain/user-aware Launcher + daemon plist + `[planes]`)

Landed a `LaunchDomain` frozen dataclass (`ops/lifecycle/launcher.py`) as the single
gui↔system axis: `.target()`, `.bootstrap_domain()`, `.launchctl_argv()` (prepends
`sudo` only for system), `.installed_plist()`, `.repo_plist()`. The gui form is
BYTE-IDENTICAL to the historical incantations. Changes:
- `_launchd_managed(label, domain=gui)` + `_launchd_cycle(…, domain=gui)` now
  domain-aware, defaulted to gui (unchanged behavior). `_run_launchctl_sudo` added.
- `Launcher.domain: LaunchDomain = gui` field + `__post_init__`: when domain is
  system AND the caller did not override, swaps the runner to `_run_launchctl_sudo`
  and points `installed_plist` at /Library/LaunchDaemons (risk (a)). Injected fakes
  + explicit paths always win, so tests + the gui default are untouched.
- `_managed`/`down`/`up`/`deploy` read `self.domain.*` (deploy's drift check now
  follows the domain's installed-plist path — risk (a)).
- NEW `ops/lifecycle/com.mind-palace.palace-daemon.plist`: mirrors the gui plist +
  `UserName ouroboros`, with system-domain owner-install instructions + the
  preconditions the runbook establishes. Nothing in the repo loads it.
- `config/defaults.toml` `[planes]` block (core/work/edge homes + `enabled=false`).
  SAFE: loader drops unknown sections; NOT surfaced via get_config (documented in
  the block — verifier/ratchets parse it directly).

Test proof (`tests/integration/test_lifecycle_control.py`, CARRIED + extended, not
rewritten): all 29 original assertions pass verbatim (gui byte-identical — the
falsifier). 7 NEW cases pin the daemon incantations: gui-vs-system LaunchDomain
forms, the `sudo launchctl` runner + LaunchDaemon path via post_init, and
`down`/`up` emitting `system/<label>` / `bootstrap system`. `test_lifecycle.py`:
the `_launchd_managed` monkeypatch extended to accept the domain arg (one-line).
**tests/integration/test_lifecycle_control.py + test_lifecycle.py: 36 passed.**
ruff clean, mypy(launcher) clean, import-firewall OK.

## 2026-07-20 — Items 2 + 3 DONE

- **Item 2** (`scripts/cockpit.sh`): the orchestrator pane launches `sudo -u ouroboros-work
  -H claude …`; every other pane + hand action stays ascalva. `bash scripts/cockpit.sh
  --dry-run` prints the sudo prefix on `desk.1` ONLY (all other panes unchanged) and spawns no
  tmux (`run()` prints in DRY mode). shellcheck clean. Committed `a4ea16f`.
- **Item 3** (`ops/network/ouroboros-egress.pf.conf`): `pass out quick on lo0` STRICTLY before
  `block drop out quick proto { tcp udp } … user ouroboros`. Ordering proven by text; syntax by
  `pfctl -n -f` on a resolvable-user substitution (rc 0). Names only ouroboros. Committed `ebe99bf`.

## 2026-07-20 — Items 4 + 5 DONE (verifier + ratchets) + a real risk-(b) discovery

- **Item 4** (`scripts/verify_planes.py`): read-only four-plane verifier behind an injectable
  `SystemProbe` so every check is exercised against pre/partial/post fixtures with NO mutation
  and no real accounts. Verdict semantics: **green (exit 0) = no FAIL and no PENDING**; SKIP is
  allowed but LISTED (the unseal item is an owner-run one-liner — the verifier NEVER scans a
  credential store, finding-0120; pf needs root). A not-yet-migrated lane is always PENDING → a
  partial migration can never false-green (the Item 4 falsifier). Runs end-to-end via `uv run
  scripts/verify_planes.py` (finding-0118 — a subprocess test pins the CLI form). Read-only
  proven by an AST test (no mutating call, no `open` for write, no pfctl `-f`) + the no-core AST
  guard. **REAL DISCOVERY (risk (b) grounded):** on this machine `/Users/ascalva` is `0o750` — NO
  o+x, so role accounts genuinely CANNOT traverse to the repo / ~/.mind-palace. The verifier
  flags it FAIL; Item 6's runbook MUST remediate (an ACL grant or `chmod o+x` on the traversal
  path, or relocate). The note only *warned* this needed verifying; the verifier turned the
  warning into a concrete, machine-specific gap.
- **Item 5** (`tests/unit/test_plane_migration.py`): 5 self-configuring ratchets keyed on real
  `stat().st_uid` — vault-unreadable, exhaust/reports==work, data==core, repo-local signing, pf
  egress. On THIS machine (pre-migration) ALL FIVE **SKIP** with a reason (the suite does not
  redden pre-migration — the Item 5 falsifier). Plus the committed anchor's ordering (text) +
  syntax (resolvable-user `pfctl -n`) + names-only-ouroboros, and a `[planes]` default-disabled
  assertion. **tests/unit/test_plane_migration.py: 16 passed, 5 skipped.** ruff + mypy(verifier)
  clean; verifier end-to-end exit 1 (honest: nothing migrated).

## 2026-07-20 — Item 6 DONE (migration runbook + pointer)

`docs/runbooks/plane-migration.md`: the full owner-run sequence, §0–§11, each step with a
`Verify:` + `Rollback:` line (13 verify / 12 rollback). Ordering guards called out up front
(key-before-vault-chown, lo0-before-pf-block, plist-before-bootstrap, traversal-before-daemon).
§5 is the ⛔ Q9 credential STOP-gate with the §3.2 mitigation order (a: cockpit
`security unlock-keychain` → b: apiKeyHelper/env) AND the §10 stop-and-raise if neither works
(→ finding-0120, do not invent a path). §0 remediates the DISCOVERED risk-(b) `/Users/ascalva`
`0o750` gap (chmod o+x traverse, or a scoped ACL). risk (c) KeepAlive control caveat stated in
§9. Ends with `uv run scripts/verify_planes.py` green. `docs/runbook.md` gets a quick-reference
pointer block (resolves). No agent-run step anywhere — authoring only.

All 6 items done. Running the full green gate next.

## 2026-07-20 — SEAL: all six items complete, green gate passing (delegated builder)

**Green gate (each leg run separately, actual tails):**
1. `ruff check .` → `All checks passed!`
2. `check_imports.py` → `Import firewall (I2): OK`
3. `mypy core agents eval ops scheduler scripts` → `Success: no issues found in 230 source files`
   (Tier-2 floor == 0).
4. `mypy` (argless) → `Found 69 errors in 20 files (checked 486 source files)` — the tests/
   baseline, UNCHANGED (my new test file added zero mypy errors).
5. `python -m ops.type_gate` → membership OK · bare-ignore scan OK.
6. `pytest -q -m 'not live and not podman and not needs_vault and not needs_restic' --deselect
   …test_core_imports_nothing_outside_core` → **1680 passed, 12 skipped, 21 deselected**. The 5
   plane-migration ratchets are within the skips (SKIP pre-migration — Item 5 falsifier holds).

**Per-item landing:** 1 launcher LaunchDomain + daemon plist + `[planes]` (byte-identical gui,
36 lifecycle tests); 2 cockpit `sudo -u ouroboros-work -H` (dry-run proof, shellcheck clean);
3 pf anchor (lo0-before-block, parses via substitution); 4 verify_planes.py (read-only, green =
no FAIL/PENDING, end-to-end CLI); 5 five self-configuring ratchets (all SKIP pre-migration);
6 migration runbook + pointer. **finding-0120** filed (direction/orchestrator) for the Q9
credential spike — the empirical bootstrap is inherently owner-run (the credential-store probe was
correctly blocked by the #10 guardrail). **Real discovery:** `/Users/ascalva` is `0o750` (no o+x)
— risk (b) is a concrete gap, remediated in runbook §0.

Scope: 14 files, all within write_scope + journal + plan-status-flip + finding-0120. NOT merged —
the orchestrator reviews the diff and merges. `status: in-progress` (the orchestrator flips it to
`complete` on merge, per the roles contract).

**Self-reported usage (for the orchestrator's seal):** model = Opus 4.8 (1M context), opus@high as
tasked (no downgrade observed, no interruption/resume — one continuous session in the worktree).
~55 tool calls; the pytest leg alone was ~54s. Token count not self-measurable precisely; the
orchestrator computes ratio/session_delta/week_delta at merge.
