# BP-015 — Build journal

Alive while the plan is `in-progress`; sealed by `/triage` on completion.
Fresh-agent test (§9): a session given only `plan.md` + this journal + the
write-scope files must continue without re-asking anything already answered.

---

## Markers

- **[open]** Item 5 (live wiring proof) — ORCHESTRATOR-EXECUTED at seal; builders never push. Untouched by this session, by design.
- **[process-lesson]** `git reset --hard` in a red-proof (Item 2, gitleaks git-mode) discards UNCOMMITTED working-tree edits to tracked files — it silently wiped an earlier journal draft. Fix adopted: commit the journal BEFORE any red-proof that resets HEAD. Fresh agents doing git-mode red-proofs must checkpoint first.

---

## Build-time facts pinned (this session, 2026-07-12)

**Action major versions** (latest majors, resolved via GitHub API at build time):

| Action | Pinned | Latest tag observed |
| --- | --- | --- |
| `actions/checkout` | `@v7` | v7.0.0 |
| `astral-sh/setup-uv` | `@v8` | v8.3.2 |

setup-uv v8 inputs used: `python-version: "3.12"`, `enable-cache: true`, `cache-dependency-glob: uv.lock` (confirmed present in `action.yml` at v8.3.2).

**Tooling acquired** (local verification):
- `actionlint` 1.7.12 (Homebrew) — Item 1 acceptance.
- `gitleaks` 8.30.1 (Homebrew binary) — Item 3 scan + Item 2 red-proof.
- `semgrep` via `uvx` (not pre-installed; matches the workflow's `uvx semgrep` invocation) — Item 2 red-proof.

**gitleaks acquisition decision (parked #3, now resolved):** the CI `gitleaks` job installs the **official binary** pinned to `v8.30.1` (curl the `linux_x64` tarball from the GitHub release, then `gitleaks git . --redact`), NOT `gitleaks/gitleaks-action@v2`. Rationale: (a) the marketplace action gates advanced features behind a GitLeaks license / org key; the bare binary is unlicensed and offline-friendly; (b) a pinned binary version is a reproducible, auditable fact vs. an action's floating internal binary; (c) 8.30.1 is exactly what discharged Gate-0 and ran the red-proof locally this session, so CI runs what was verified. `--redact` keeps any future match off public-repo logs (display-only; does not change detection).

## Semantic boundaries

### Item 1 — rebuild `.github/workflows/ci.yml`: five independent jobs — CLOSED (green) — committed `e9a3ee8`

Replaced the stale pre-uv workflow wholesale (`pip install -e '.[dev]'`, no type/security jobs) with the ported gate per §6(a–f,h): five mutually-independent jobs (ratchet, type-gate, vault-axis, semgrep, gitleaks), no `needs:`, no stage coupling (D6), no `paths:` filters (P2), no `pull_request` (parked #5). Triggers `push: [main]` + `workflow_dispatch`; concurrency `ci-${{ github.ref }}` / `cancel-in-progress: true` (replaces GitLab `interruptible`).

**Acceptance — actionlint exit 0:**
```
$ actionlint .github/workflows/ci.yml ; echo EXIT: $?
EXIT: 0
```

**Byte-match against §6(c–f):** verified verbatim.
- ratchet §6(c): `uv sync --frozen --extra dev` / `uv run ruff check .` / `uv run python scripts/check_imports.py` / `uv run pytest -q -m 'not live and not podman and not needs_vault and not needs_restic'` — byte-identical to `.gitlab-ci.yml:68-71`.
- type-gate §6(d): baseline block runs with `shell: bash`; `MYPY_TESTS_BASELINE=69`; the grep pipeline and `exit 1` byte-match `.gitlab-ci.yml:112-127`.
- vault-axis §6(e): service `hashicorp/vault:latest`, `VAULT_DEV_ROOT_TOKEN_ID: ci-root-disposable`, `ports: 8200:8200`, job env `VAULT_ADDR: http://localhost:8200` + `VAULT_TOKEN: ci-root-disposable` (Q4 host-networking deviation), `uv run pytest -q -m needs_vault`.
- semgrep §6(f): `uvx semgrep scan --config p/default --error`.
- gitleaks §6(f): checkout `fetch-depth: 0`, pinned-binary install, `gitleaks git . --redact`.

**Invariant §6(h):** grep for `paths:`/`needs:`/`pull_request` found only two explanatory comment lines, zero actual keys; five jobs independent; import-firewall inside ratchet.

Verdict: **GREEN.** actionlint 0; all commands byte-match; triggers/concurrency exact.

### Item 3 — gitleaks full-history run (Gate-0 residual discharge) — CLOSED (green)

Ran the official gitleaks binary (8.30.1) in git mode over full history in this worktree.

**Acceptance:**
```
$ gitleaks git . 2>/dev/null ; echo EXIT: $?
EXIT: 0
# verbose: "226 commits scanned. ... no leaks found"
```

**Findings count: 0.** No TRUE credential hit (§10 not triggered). No `.gitleaks.toml` allowlist required — the `tests/keys/*.seed` base64 Ed25519 seeds did NOT produce a hit under gitleaks 8.30.1's default rules (bare base64 with no adjacent secret-keyword context; the default generic-secret rule needs keyword/assignment context). For the fresh agent: those seeds ARE provably synthetic anyway (deterministic from a fixed phrase, public keys committed at `ops/attestation/{owner,supervisor}.pub`, `tests/keys/README.md` declares zero production trust) — so if a future ruleset bump flags them, an allowlist entry keyed to those exact paths is justified. None needed today.

**Gate-0 residual discharged:** the clean full-history scan confirms the "tree is clean" verdict (note §2).

### Item 2 — local red-proofs: every gate falsified once at command level — CLOSED (all five red)

Each ported command was falsified once with a planted defect, the nonzero exit observed, then reverted. **No planted defect was committed** (git-mode gitleaks used a temp commit hard-reset to the pre-proof HEAD; all others were scratch files removed in place). `git status` clean afterward; `find` for `*_redproof*` returns nothing.

| Gate (job) | Planted defect | Command | Observed exit |
| --- | --- | --- | --- |
| ratchet · ruff | `core/_redproof_scratch.py`: unused `import os` (F401) | `uv run ruff check .` | **1** ("Found 1 error") |
| type-gate · Tier-2 floor | `core/_redproof_scratch.py`: `_bad: str = add(1,2)` (int→str) | `uv run mypy core agents eval ops scheduler scripts` | **1** ("Found 1 error", `[assignment]`) |
| type-gate · tests/ baseline | `tests/unit/test_redproof_scratch.py`: `x: str = 123` | §6(d) baseline block (`MYPY_OUT` count check) | **1** — count 70 ≠ 69, block prints the finding-0029 message and `exit 1` |
| gitleaks · full history | temp-committed `_redproof_secret.txt` with a realistic (non-`EXAMPLE`) AWS key pair | `gitleaks git . --redact` | **1** ("leaks found: 1"); HEAD hard-reset to `e9a3ee8`, clean re-scan exit 0 |
| semgrep · SAST | `_redproof_semgrep.py`: `subprocess.Popen(user_input, shell=True)` | `uvx semgrep scan --config p/default --error` | **1** ("Findings: 1 (1 blocking)", `subprocess-shell-true`) |

**Falsifier checks (§7 Item 2):**
- The baseline-grep falsifier ("`MYPY_COUNT` comes out empty yet passes") is disconfirmed: the grep parsed `70` correctly and the block took the `!= 69` branch. Also independently confirmed the CLEAN whole-tree count is exactly `69` (`uv run mypy` → "Found 69 errors in 20 files") — the pinned constant is live, not stale.
- gitleaks default-allowlist gotcha (recorded for the fresh agent): the canonical `AKIAIOSFODNN7EXAMPLE` key is allowlisted by gitleaks' own default config and yields exit 0 — a red-proof MUST use a non-`EXAMPLE` synthetic key or it silently passes.

**Post-proof state:** `git status` clean (only tracked file expected to differ is this journal); HEAD `e9a3ee8`; no `*_redproof*` files anywhere.

### Item 4 — tombstone `.gitlab-ci.yml` + runbook correction — CLOSED (green)

**Tombstone** (`.gitlab-ci.yml:1-5` → §6(g)): the `workflow` block became the tombstone banner (naming the design note, D1/D5) + `workflow.rules: [{when: never}]`. The rest of the file (all jobs incl. `pages`, the includes, the reference body) is untouched — retained until the D4 origin migration (parked #2).

**Acceptance:**
```
$ uv run --with pyyaml python -c "import yaml; d=yaml.safe_load(open('.gitlab-ci.yml')); ..."
workflow.rules = [{'when': 'never'}]
PARSES + rules == [{when: never}]: OK
body retained? pages: True | ratchet: True | type-gate: True | vault-axis: True
```

**Runbook** (`docs/runbook.md`, the §Verifying CI paragraph): rewritten for the GitHub gate — names GitHub Actions, the tombstone + design note, all five jobs (ratchet · type-gate · vault-axis · semgrep · gitleaks), the no-docs-skip rule ("every sha yields a verdict"), unmetered minutes, and batching demoted from budget-necessity to verdict-hygiene habit. Verified: "GitHub Actions" present; all five backticked job names present; "no docs-skip" phrasing present.

**Item 4 invariant (§7):** the tombstone lands in the SAME builder session as Item 1 (both on this worktree branch, Item 1 committed first at `e9a3ee8`) — never a window with both gates dead by our own hand. The final merge-order to main is the orchestrator's at seal; the tombstone commit is ordered after the workflow commit here.

**Falsifier (§7 Item 4):** "after the next mirrored push, GitLab creates a new pipeline for the pushed sha" — this is checked ONCE on the GitLab pipelines page and is part of Item 5 (orchestrator-executed, post-merge). Not verifiable by a builder (never pushes). Left for the orchestrator.

## Worktree ratchet (builder self-check — CLOSING)

```
$ uv run ruff check .
All checks passed!                       # EXIT 0
$ uv run python scripts/check_imports.py
Import firewall (I2): OK — core imports no zone ...   # EXIT 0
```

**Ratchet GREEN.** Nothing in this worktree's write_scope touched `ops/`/`scripts/`/`tests/` — no code was bent to the gate; no `spec-fidelity` finding was needed (all five gates reached green as ported: clean gitleaks, exactly-69 mypy baseline, ruff/semgrep detect their planted defects).

## Handoff to orchestrator (Item 5, not this session)

Items 1–4 complete and committed on branch `worktree-agent-a0565fedc5daaa66e`. **Item 5 (live wiring proof) is ORCHESTRATOR-EXECUTED at seal** — builders never push. At seal, merge Items 1–4 to main, let the mirrored push produce a `ci` run (expect all five green), then one canary push (a trivial ruff violation → red `ratchet`) and its revert (→ green). Three run URLs (green → red → green) go in this journal. Secret/semgrep reds are NOT pushed (public-repo hygiene; Item 2 covered them locally). Also do the Item-4 falsifier check: confirm GitLab creates NO new pipeline for the pushed sha (tombstone effective).

---

## Item 5 — live wiring proof (ORCHESTRATOR-EXECUTED) — IN PROGRESS (2026-07-12)

### Green-run attempt 1 — FAILED (workflow-wiring defect, fixed in scope)

Merged Items 1–4 to main (`e14be25`), pushed origin (GitLab→GitHub mirror). The `ci`
run for the sha (github.com/ascalva/Mind-Palace/actions/runs/29179344841) came back
**failure**: 4/5 jobs (ratchet, type-gate, vault-axis, semgrep) failed at the very first
**"Set up job"** step; only `gitleaks` (no `setup-uv`) went green. Setup log:
`##[error]Unable to resolve action astral-sh/setup-uv@v8, unable to find version v8`.

**Root cause:** `astral-sh/setup-uv` publishes exact tags `v8.0.0`…`v8.3.2` but **no
moving `v8` major alias** (git ref `tags/v8` → HTTP 404; `v6`/`v7` DO have aliases — the
v8 series dropped the major-alias convention). The build-time pin assumed a `v8` alias by
analogy; it does not exist. `actions/checkout@v7` resolves fine (gitleaks proved it).

**Fix (orchestrator, in bp-015 write_scope — the gate's wiring, NOT gate content and NOT
the code bending):** pinned all four `setup-uv` refs to the exact tag `@v8.3.2` — the
version the builder actually verified locally (action.yml inputs confirmed).
`actionlint .github/workflows/ci.yml` → exit 0. Re-pushing for green-run attempt 2.

**Verification-gap noted (finding owed at seal):** Item 2's local red-proofs validate the
gate *commands* but run under local `uv`/`uvx` — they cannot exercise GitHub Actions'
marketplace-action *resolution* or service-container health. Only the live run (Item 5)
catches a bad action ref. Future CI-style plans should budget an Item-5 wiring-fix round
and, ideally, pre-validate action refs against the GitHub git-ref API at build time.

### Green-run attempt 2 — 4/5 GREEN; `semgrep` red on 22 real findings → PARKED (owner decision)

Run: **github.com/ascalva/Mind-Palace/actions/runs/29179448272** (sha `8d534a0`).

| job | conclusion |
| --- | --- |
| ratchet | **success** (ruff + import-firewall + model-free pytest tier all ran on GitHub) |
| type-gate | **success** (mypy Tier-2 floor 0 + the exact-69 tests/ baseline held on the runner) |
| vault-axis | **success** — the disposable `hashicorp/vault:latest` service container works under host networking (`VAULT_ADDR=http://localhost:8200`); the §10 "container unreachable" risk is **cleared** |
| gitleaks | **success** (full-history scan, clean) |
| semgrep | **failure** — scan completed OK (432 rules, 508 files); reported **22 findings (22 blocking)**; `--error` (§6(f)) makes them fatal |

**semgrep is a real, pre-existing audit backlog, not a regression** (classes: dynamic-urllib
loopback ×4 incl. an already-`# noqa: S310` one; internal-constant SQL f-strings ×3;
terraform.aws hardening ×2; flask format-string; `mutable-action-tag` flagging our own
`@v8.3.2`/`@v7`). Per §9/§10 I can neither fix 22 code sites in this plan nor drop `--error`
(gate-content change). **Parity crux:** GitLab's SAST template is report-only; the plan's
`--error` made this gate stricter than the original, and never verified green-on-clean.

**Disposition: `semgrep` job PARKED.** Filed **finding-0037** (design; routed orchestrator) and
batched **oq-0015** (blocking: true — owner rules keep-blocking-and-triage vs report-only-parity
vs narrow-ruleset). Re-entry: owner ruling on oq-0015. The four green jobs are independent
(no `needs:`), so the park does not stop them.

### Item 4 falsifier — PASS (tombstone effective)

GitLab pipelines API (public repo, no auth): the latest GitLab pipeline is for sha `688a9b8`
(the pre-tombstone graduation commit). **No GitLab pipeline was created for `e14be25` or
`8d534a0`** (the tombstoned shas) — `workflow: rules: [{when: never}]` works. (All prior GitLab
pipelines also show `failed` — the exhausted-runner state that motivated the migration.)

### Item 5 canary (green→red→green on ratchet) — DEFERRED with reasoning

The literal ratchet canary (push a ruff violation → red, revert → green) is **deferred**, not
skipped. Its falsifier ("workflow wiring swallows a failing exit code") is **already
disconfirmed by attempt 2**: `semgrep` went red while four jobs went green **in the same run**,
proving per-job exit codes are honored and not swallowed; and `ratchet` ran green having actually
executed ruff/imports/pytest (Item 2 proved ruff→red locally; each job's `run:` block is
`bash -eo pipefail`, so a mid-block failure propagates). Running the canary now would cost two
more mirror+run cycles for near-zero marginal assurance while `semgrep` keeps every run red
anyway. **Bundle it with the semgrep re-verify** once oq-0015 is answered: re-run, confirm five
green (or four-green-plus-ruled-semgrep), then one ratchet canary + revert, record the three
URLs, and seal.

### oq-0015 answered → semgrep report-only → Item 5 COMPLETE (green→red→green proven)

Owner ruled **oq-0015 = report-only, match GitLab parity** (2026-07-12, via AskUserQuestion;
finding-0037 resolved). Enacted in `.github/workflows/ci.yml`: semgrep step dropped `--error`
(findings log, non-blocking) — an owner-authorized gate change, so no longer a unilateral one.
The 22 findings persist in finding-0037 as a triage backlog (a future scoped plan / triage may
address the genuine hardening: terraform.aws CloudWatch encryption + Lambda X-Ray, the flask
format-string, SHA-pinning actions).

**Item 5 live wiring proof — three main shas, green→red→green (the canary is NO LONGER deferred):**

| leg | sha | run | verdict |
| --- | --- | --- | --- |
| GREEN #1 | `739dc98` | [29183251392](https://github.com/ascalva/Mind-Palace/actions/runs/29183251392) | **all 5 green** (semgrep now report-only) |
| RED (canary) | `874afcd` | [29183299956](https://github.com/ascalva/Mind-Palace/actions/runs/29183299956) | **ratchet failure** (planted F401 in `_ci_canary.py`), other 4 green |
| GREEN #2 (revert) | `e8eed02` | [29183331779](https://github.com/ascalva/Mind-Palace/actions/runs/29183331779) | **all 5 green** restored |

**Falsifier disconfirmed:** the canary did NOT come back green — `ratchet` red on the F401 while
`type-gate`/`vault-axis`/`semgrep`/`gitleaks` stayed green, proving the workflow honors per-job
exit codes and the red is correctly attributed to `ratchet`. The canary file was a root-level
`_ci_canary.py` (unused `import os`) — outside the type-gate mypy paths, so only `ratchet` reds,
matching the plan's "the red run's failing job is `ratchet`." Both canary commits are throwaway
main-history commits, accepted per Item 5; working tree clean after the revert.

## SEAL (2026-07-12) — bp-015 COMPLETE

All five items closed: Items 1–4 by the delegated opus builder; Item 5 by the orchestrator
(wiring fix `setup-uv@v8.3.2`, then the green→red→green proof above). **CI is live on GitHub
Actions — every main sha yields a verdict**; `.gitlab-ci.yml` tombstoned and provably dead (no
GitLab pipeline for any tombstoned sha); the runbook is repointed. The witness's "attestable
green" is now defined: five jobs, `ratchet`/`type-gate`/`vault-axis`/`gitleaks` blocking +
`semgrep` report-only. Status flipped `in-progress → complete`.

**Usage ledger (context-economy):** delegated opus builder = 63,994 tokens · 55 tool calls ·
~513 s. Orchestrator-side Item 5 (this session): the wiring diagnosis + fix + report-only
enactment + five live CI watch cycles (green-fail-1, 4/5, green#1, red-canary, green#2).

**Deferred to a later plan / triage (not bp-015):** the 22 semgrep findings (finding-0037
backlog). **bp-016 ∥ bp-017 now unblocked** (gated on this seal; disjoint scopes).

---

**SEALED — 2026-07-12, /triage.** Plan `complete` — five-job attestable green + red-canary
proof (semgrep report-only per oq-0015, now swept; the 22-finding backlog lives in
finding-0037). PROGRESS SEAL entry in the 2026-07-12 checkpoint; cost.actual ledgered (builder
opus 64k tok / 55 calls / 513s + orchestrator-side Item 5). bp-016 ∥ bp-017 unblocked. No
further narrative entries.
