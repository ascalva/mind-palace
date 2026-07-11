---
type: build-plan
id: bp-015
status: proposed
design_ref:
  - docs/design-notes/ci-platform-and-runner-strategy.md # D1 (gate moves), D2 (parity content), D5 (tombstone), Gate-0 residual
contract: builder
write_scope:
  - ".github/workflows/ci.yml"
  - ".gitlab-ci.yml"
  - ".gitleaks.toml"        # only if synthetic fixtures need allowlisting (Item 3)
  - "docs/runbook.md"
  - "docs/findings/**"
  - "docs/build-plans/bp-015/**"
session_budget: 1
cost:
  estimate: { model: opus, tokens: 250k } # commands fully pinned; verification crisp (CI verdict) but the red-proof protocol needs discipline
  actual: null
depends_on: []               # first of the family; unblocks bp-016/bp-017 and the deploy path
parallelizable_with: [bp-014] # disjoint write_scope (.claude/hooks vs CI files); owner priority sequences the two
created: 2026-07-11
updated: 2026-07-11
links:
  - docs/findings/finding-0034.md # warrant-in-fact of the design note (runner-minutes exhaustion)
  - docs/findings/finding-0029.md # the mypy 0-floor/69-baseline split the type-gate pins
  - docs/findings/finding-0014.md # scripts/check_imports.py as the Invariant 2 CI proof
supersedes: null
superseded_by: null
warrant: null
---

# Build Plan — Plan A: the parity gate — `.github/workflows/ci.yml` reaches GitLab parity; `.gitlab-ci.yml` tombstoned

> **Every section below is required.** N/A is an accountability act.

## 0. Mode & provenance

Graduated 2026-07-11 from the **ratified** `dn-ci-platform-and-runner-strategy` (owner
hand-ratified 2026-07-11; D4 ruled end-state — GitHub becomes origin). Investigation and
planning produced this; implementation proceeds item-by-item on owner approval.
Authority-to-act is the ratified note; the readiness blessing is the owner-only
`proposed → ready` hand edit — no agent flips it. **Builders never push**: the live wiring
proof (Item 5) is orchestrator-executed at seal.

## 1. Objective

Every push to main yields a real, attestable verdict again: `.github/workflows/ci.yml`
runs the full ported gate (ratchet · type-gate · vault-axis · semgrep · gitleaks) green on
GitHub Actions, while `.gitlab-ci.yml` is tombstoned so the monthly runner-minute reset
never resurrects a non-authoritative pipeline.

## 2. Context manifest

1. `docs/design-notes/ci-platform-and-runner-strategy.md` — the licensing decisions:
   P1–P5, D1/D2/D5/D6, Gate-0 residual. Read once; everything buildable is re-pinned in §6.
2. `.gitlab-ci.yml` — the source of truth being ported (commands re-pinned verbatim §6).
3. `.github/workflows/ci.yml` — the stale workflow being replaced wholesale.
4. `pyproject.toml` — the `markers` block (:54-78) and `[tool.mypy]` (:95+): the marker
   vocabulary and type-gate configuration the commands rely on.
5. `tests/e2e/test_secrets_vault_live.py` — how the vault-axis tests consume
   `VAULT_ADDR`/`VAULT_TOKEN` (:25-26): the service-container env contract.
6. `docs/runbook.md` §Verifying (:66-95) — the paragraph Item 4 corrects.
7. `docs/findings/finding-0029.md` — why the tests/ baseline is exactly 69.

## 3. Investigation & grounding

- **Q1 — what exactly is the parity target?** Four GitLab jobs plus two security
  templates: `ratchet` (`.gitlab-ci.yml:33-71`), `type-gate` (`:86-127`), `vault-axis`
  (`:133-162`), `pages` (`:164-197` — **not this plan**; bp-017), and the `SAST` +
  `Secret-Detection` template includes (`:16-17,22-26`). Commands pinned verbatim in §6.
- **Q2 — is the stale GitHub workflow salvageable?** No — pre-uv
  `pip install -e '.[dev]'` (`.github/workflows/ci.yml:39-42,53-56`), observed
  red-at-install on mirrored main (run 29169533661, sha `ef9319ea`, note D1); its marker
  expression (`not live and not podman and not longitudinal`, `:60`) predates
  `needs_vault`/`needs_restic`; no type-gate, no security jobs. Replaced wholesale;
  nothing ports from it.
- **Q3 — does the 4-marker exclusion leak `longitudinal` (CLI `-m` overrides the
  `addopts` `-m`)?** No — measured 2026-07-11: `uv run pytest -m 'not live and not podman
  and not needs_vault and not needs_restic' --collect-only` → 808/828 collected, zero
  longitudinal items; `pytest tests/longitudinal --collect-only` → 0 collected. The
  command ports verbatim, unmodified.
- **Q4 — how does the vault service container resolve on GitHub?** GitLab used alias
  `vault` → `http://vault:8200` (`.gitlab-ci.yml:137-145`). On GitHub Actions a job
  running on the runner host reaches a service via **mapped ports on localhost** (alias
  DNS applies only to container-run jobs). The tests consume `VAULT_ADDR`/`VAULT_TOKEN`
  from env (`tests/e2e/test_secrets_vault_live.py:25-26`), so the deviation is env-only:
  `ports: 8200:8200`, `VAULT_ADDR=http://localhost:8200`. Pinned §6(e).
- **Q5 — the `chore(release)` pipeline-skip (`.gitlab-ci.yml:1-4`)?** Deliberately NOT
  ported. P2 wants every sha to yield a verdict and minutes are unmetered. On-GitHub
  release commit-backs (bp-016) are pushed with `GITHUB_TOKEN`, which does not trigger
  workflows (GitHub's documented loop guard) — the code does not settle this; bp-016's
  live release run confirms it. Either way no skip rule is written here.
- **Q6 — Python version?** 3.12 floor: scikit-network's locked version ships linux wheels
  only for cp311/cp312 (`.gitlab-ci.yml:35-38` comment); local dev runs 3.14, CI validates
  the floor. Pinned §6(b).
- **Q7 — is git available?** The GitLab slim image needed `apt-get install git`
  (`.gitlab-ci.yml:66`); `ubuntu-latest` ships git — the line drops.
- **Q8 — what replaces the SAST/Secret-Detection templates?** Their engines, run
  directly: semgrep (the SAST analyzer relevant to Python) and gitleaks (secret detection
  over full history — the first green run also discharges Gate-0's entropy-scan residual,
  note §2). The GitLab templates' exact internal rulesets are GitLab-side includes the
  code does not settle; the replacement pins rulesets explicitly instead (§6(f)).

**Additional risks surfaced during reading:**

- `tests/keys/` holds ASCII seed files (`owner.seed`, `supervisor.seed`), not PEM blocks —
  low gitleaks-hit risk, but Item 3 anticipates fixture allowlisting via `.gitleaks.toml`
  (each entry justified as provably synthetic).
- The push-mirror batches up to ~5 min, so CI verdicts trail local pushes; that is
  bp-016's grace-window concern, irrelevant to gate content here.

## 4. Reconciliation

- `docs/runbook.md:80-84` — "every **code** push to main runs the `ratchet` job on GitLab
  shared runners … Free-tier minutes are the budget: batch commits and push at
  boundaries, not per commit." → **[banner: correction]**, carried by Item 4: rewritten
  for the GitHub gate (five jobs, every push, no docs-skip, unmetered; batching demoted
  from budget-necessity to habit — verdict hygiene and wall-clock still favor
  unit-boundary pushes).
- `.github/workflows/ci.yml` (whole file) → **[correction]**, carried by Item 1: replaced
  wholesale; its header comments carry into the new file's header where still true
  (Invariant 2 discharge; live/podman stay local).
- `.gitlab-ci.yml` → **[banner: correction-by-tombstone]**, carried by Item 4: the
  `workflow` block becomes `when: never` with a banner naming the design note; the body
  is retained until the parked deletion (note parked decision #3).

## 5. Write scope

In: the two CI files, `.gitleaks.toml` (fixture allowlist, only if Item 3 needs it), the
runbook §Verifying CI paragraph, findings, this plan's own directory. Out, deliberately:
`ops/**`, `scripts/**`, `tests/**` — **the gate ports; the code never bends to it.** If a
ported gate exposes a real defect, that is a finding, not an edit. Also out: the witness
(bp-016), mkdocs/pages (bp-017), design notes, and the foundation denylist.

## 6. Interfaces pinned inline

**(a) Workflow skeleton** (triggers per note D2/P2; concurrency replaces `interruptible`):

```yaml
name: ci
on:
  push:
    branches: [main]
  workflow_dispatch:
# NO paths: filters (P2 — every main sha yields a verdict).
# NO pull_request (parked: no PR refs exist until the D4 origin re-point executes).
concurrency:
  group: ci-${{ github.ref }}
  cancel-in-progress: true      # replaces GitLab `interruptible: true`
```

**(b) Common job setup** (all five jobs): `runs-on: ubuntu-latest`; `actions/checkout`
(default shallow — **except gitleaks: `fetch-depth: 0`**); uv via `astral-sh/setup-uv`
with caching keyed on `uv.lock`, interpreter CPython **3.12** (Q6). The pinned
*constraints* are: uv-managed, 3.12, `--frozen` against `uv.lock`; the builder pins the
current action major versions at build time and records them in the journal.

**(c) `ratchet` job script** — verbatim from `.gitlab-ci.yml:68-71`:

```
uv sync --frozen --extra dev
uv run ruff check .
uv run python scripts/check_imports.py   # Invariant 2 static proof in CI (finding-0014)
uv run pytest -q -m 'not live and not podman and not needs_vault and not needs_restic'
```

**(d) `type-gate` job script** — verbatim from `.gitlab-ci.yml:112-127`; the baseline
block runs with `shell: bash`:

```
uv sync --frozen --extra dev
uv run mypy core agents eval ops scheduler scripts   # Tier-2 hard floor: 0 errors, no exceptions
MYPY_TESTS_BASELINE=69
MYPY_OUT="$(uv run mypy 2>&1)" || true
echo "$MYPY_OUT"
MYPY_COUNT="$(echo "$MYPY_OUT" | tail -1 | grep -oE '[0-9]+ error' | grep -oE '[0-9]+')"
if [ "$MYPY_COUNT" != "$MYPY_TESTS_BASELINE" ]; then
  echo "type-gate: expected exactly $MYPY_TESTS_BASELINE mypy errors (tests/ baseline, finding-0029), got '${MYPY_COUNT:-0}'"
  exit 1
fi
uv run python -m ops.type_gate   # Tier-2 membership + bare-ignore scans (bp-008)
```

**(e) `vault-axis` job** — service container + env (Q4 deviation pinned):

```yaml
services:
  vault:
    image: hashicorp/vault:latest
    env:
      VAULT_DEV_ROOT_TOKEN_ID: ci-root-disposable
    ports:
      - 8200:8200
env:
  VAULT_ADDR: http://localhost:8200   # host-run job: localhost + mapped port, not the GitLab alias
  VAULT_TOKEN: ci-root-disposable
# steps: uv sync --frozen --extra dev  →  uv run pytest -q -m needs_vault
```

**(f) Security jobs** (template replacements, Q8):

```
semgrep:   uvx semgrep scan --config p/default --error
           # --error ⇒ nonzero exit on findings; ruleset may be EXTENDED, never dropped below p/default
gitleaks:  checkout fetch-depth: 0, then a git-mode scan over FULL history (every run)
           # first green run discharges Gate-0's entropy residual (note §2)
           # acquisition (official binary vs gitleaks/gitleaks-action@v2) is a build-time
           # fact — builder picks, pins the version, journals the choice
```

**(g) Tombstone** — `.gitlab-ci.yml:1-5` (the `workflow` block) becomes exactly:

```yaml
# TOMBSTONE (2026-07-11) — the CI gate moved to GitHub Actions (.github/workflows/ci.yml).
# See docs/design-notes/ci-platform-and-runner-strategy.md (D1/D5). This pipeline never
# runs; the file is retained until the D4 origin migration completes (parked decision #3).
workflow:
  rules:
    - when: never
```

The rest of the file is untouched (retained reference body).

**(h) Invariants:** the five jobs are mutually independent — no `needs:`, no stage
coupling (D6: no ordering exists that could suppress a gate); each job can go red alone;
the import-firewall lives inside `ratchet` via `scripts/check_imports.py`; no `paths:`
filters anywhere in the `ci` workflow (P2).

## 7. Items

### Item 1 — rebuild `.github/workflows/ci.yml`: five independent jobs

- **Objective:** the workflow per §6(a–f,h) — ratchet, type-gate, vault-axis, semgrep,
  gitleaks; triggers and concurrency per §6(a).
- **Files:** `.github/workflows/ci.yml`
- **Acceptance test:** `actionlint` exits 0 over the file; YAML parses; every gate command
  byte-matches §6(c–f); triggers/concurrency match §6(a) exactly.
- **Falsifier:** any pinned command drifting from the `.gitlab-ci.yml` source (diff the
  script lines against §6), or a `paths:`/`needs:` key present anywhere (P2/D6 violation).
- **Invariant(s):** §6(h); gate *content* is ported, never redesigned (note "out of scope").
- **Touches stored data?** no
- **Parallelizable?** yes (with Item 3)  **Depends on:** none

### Item 2 — local red-proofs: every gate falsified once at command level

- **Objective:** prove each ported command can actually fail before trusting its green:
  run each §6(c–f) gate locally with a planted defect (a ruff violation; a type error in
  `core/` → floor breaks; a type error in `tests/` → count ≠ 69 breaks; a fake secret in
  a scratch file → gitleaks red; a semgrep-detectable pattern), observe the nonzero exit,
  revert. Planted defects are NEVER committed.
- **Files:** none committed (scratch worktree; the journal records each red).
- **Acceptance test:** journal table gate → planted defect → observed nonzero exit; `git
  status` clean afterwards.
- **Falsifier:** a gate that stays green under its planted defect — the port is cosmetic
  (e.g. the baseline grep parses nothing and `MYPY_COUNT` comes out empty yet passes).
- **Invariant(s):** no planted defect ever reaches a commit, let alone a push.
- **Touches stored data?** no
- **Parallelizable?** no  **Depends on:** Item 1

### Item 3 — gitleaks full-history run (Gate-0 residual discharge)

- **Objective:** an entropy-based scan over ALL commits, locally; green discharges the
  note §2 residual. Any true hit fires the named remediation, which is owner-level:
  rotate the credential → `git filter-repo` → force-remirror (stop-and-raise, §10).
- **Files:** `.gitleaks.toml` only if synthetic fixtures need allowlisting — each entry
  justified in the journal as provably synthetic (e.g. `tests/keys/*.seed`).
- **Acceptance test:** full-history `gitleaks` git-mode scan exits 0 (bare, or after
  fixture-only allowlisting); journal records the gitleaks version and findings count.
- **Falsifier:** a TRUE credential hit — not a plan failure but the disconfirmation of
  Gate-0's "tree is clean" verdict; §10 fires.
- **Invariant(s):** allowlist entries never cover a real credential pattern class, only
  named fixture paths.
- **Touches stored data?** no
- **Parallelizable?** yes (with Item 1)  **Depends on:** none

### Item 4 — tombstone `.gitlab-ci.yml` + runbook correction

- **Objective:** the GitLab pipeline provably never runs again; the runbook stops
  describing a dead gate.
- **Files:** `.gitlab-ci.yml` (workflow block → §6(g)), `docs/runbook.md` (:80-84
  paragraph per §4).
- **Acceptance test:** tombstoned file parses as YAML with `workflow.rules` exactly
  `[{when: never}]` plus the banner; the runbook paragraph names GitHub Actions, all five
  jobs, and the no-docs-skip rule.
- **Falsifier:** after the next mirrored push, GitLab creates ANY new pipeline for the
  pushed sha (tombstone ineffective — checked once on the GitLab pipelines page).
- **Invariant(s):** tombstone lands in the SAME merge as (or after) Item 1 — never a
  window with both gates dead by our own hand.
- **Touches stored data?** no
- **Parallelizable?** no  **Depends on:** Item 1

### Item 5 — live wiring proof (ORCHESTRATOR-EXECUTED at seal; builders never push)

- **Objective:** on the merged parity sha, the mirrored push yields a `ci` run with all
  five jobs green; one canary push (trivial ruff violation) yields red; the revert push
  restores green. Secret/semgrep reds are NOT pushed — public-repo hygiene; Item 2
  covered them locally.
- **Files:** none beyond two throwaway commits (canary + revert) in main history — noted
  and accepted.
- **Acceptance test:** three run URLs in the journal (green → red → green), all main
  shas; the red run's failing job is `ratchet`.
- **Falsifier:** the canary comes back green (workflow wiring swallows a failing exit
  code), or no run appears for a pushed sha within the mirror window (P2 broken).
- **Invariant(s):** performed by the orchestrator/owner, never the builder; no deploy
  attempted off the red canary sha.
- **Touches stored data?** no
- **Parallelizable?** no  **Depends on:** Items 1–4 merged

## 8. Math carried explicitly

N/A — no mathematical object implemented (the 69 constant is a pinned regression
baseline, finding-0029, not a mathematical construction).

## 9. Non-goals

Docs/Pages hosting (bp-017); witness/attestation re-point (bp-016); release machinery;
changing ANY gate content — commands port verbatim, a desired gate change is a finding;
deleting `.gitlab-ci.yml` (parked, note #3); MicroVM runners (D7 parked); `pull_request`
triggers (parked, note #5); fixing any code defect a ported gate exposes (finding + park
the item, never bend the code inside this plan).

## 10. Stop-and-raise conditions

A TRUE secret hit in Item 3 (owner-level remediation: rotate → filter-repo →
force-remirror — never improvised solo); any gate that cannot reach green on GitHub
without changing gate *content* (spec-defect finding — parity is the contract); the vault
service container unreachable under host networking after honest attempts (park the
vault-axis item with a re-entry condition, continue the rest — never weaken to a skip); a
marketplace action turning out to require an org license (fall back to the binary; if
that also fails, raise); any needed write outside §5 (narrow the item or file a finding —
never route around scope-guard).

## 11. Parked decisions

| Decision | Default recorded | Rejected alternatives (why) | Re-entry condition |
|---|---|---|---|
| `pull_request` CI | not enabled | enable now (no PR refs exist — the mirror is main-only; a dead trigger is noise) | D4 origin re-point executes (bp-016 Item 11b) |
| `.gitlab-ci.yml` deletion | tombstoned, retained | delete now (loses the reference body; note parked #3 awaits D4 completion) | D4 migration completes |
| gitleaks acquisition | builder picks binary vs `gitleaks-action` at build, journals it | pre-pinning here (marketplace/licensing facts are build-time facts) | — |
| runner arch | `ubuntu-latest` x64 | arm64 (only cheaper on private repos; D7 territory) | a D7 trigger fires |

## 12. Dependency & ordering summary

Items 1 ∥ 3 (both read-only-verifiable, reversible) → Item 2 (red-proofs against Item 1's
file) → Item 4 (tombstone, same merge as 1) → Item 5 (the only externally visible step;
orchestrator-owned, post-merge). Cross-plan: **bp-016 depends on this plan** (the witness
needs a green `ci` workflow to attest; the tombstone makes the GitLab read-path dead
code); **bp-017 follows immediately** (the tombstone kills GitLab Pages — the sooner
`pages.yml` lands, the shorter the docs outage); bp-014 is parallel-safe (disjoint
scope) — owner priority sequences the two lanes.
