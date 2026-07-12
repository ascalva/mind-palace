---
type: finding
id: finding-0037
status: resolved
created: 2026-07-12
updated: 2026-07-12
links:
  - docs/build-plans/bp-015/plan.md # §6(f) pinned `semgrep ... --error`; §9/§10 forbid in-plan resolution
  - docs/design-notes/ci-platform-and-runner-strategy.md # Q8 SAST-template replacement
  - docs/inbox/owner-questions.md # oq-0015 batches this decision
ftype: design
origin_plan: bp-015
route: orchestrator
resolution: >
  RESOLVED (owner ruling oq-0015, 2026-07-12): option 2 — REPORT-ONLY, match GitLab
  parity. `.github/workflows/ci.yml` semgrep step dropped `--error` (findings log,
  non-blocking). The 22 findings persist here as a triage backlog (not fixed — a future
  scoped plan or /triage may address the genuine hardening items: terraform.aws CloudWatch
  encryption + Lambda X-Ray, the flask format-string, SHA-pinning actions). bp-015 then
  re-verified 5/5 green + ratchet canary and sealed. The verification-methodology lesson
  (pre-validate action refs; run blocking gates on the clean tree) stands for future CI plans.
---

# The ported `semgrep --error` gate is blocking, and reaches red on the existing tree (22 findings) — GitLab's SAST was report-only

## What

bp-015 Item 5's first successful live run (github.com/ascalva/Mind-Palace/actions/runs/29179448272,
sha `8d534a0`, after the `setup-uv@v8.3.2` wiring fix) came back **4/5 green**: `ratchet`,
`type-gate` (mypy Tier-2 floor + the exact-69 tests/ baseline held on GitHub), `vault-axis`
(the disposable Vault service container works under host networking — the §10 "container
unreachable" risk is cleared), and `gitleaks` all passed. **`semgrep` failed**: the scan
itself completed successfully (432 rules, 508 files) and reported **22 findings (22 blocking)**;
`uvx semgrep scan --config p/default --error` (§6(f)) exits 1 because `--error` makes findings
fatal.

The 22 are a pre-existing backlog, not a regression this plan introduced — spanning classes:
- `python.lang.security.audit.dynamic-urllib-use-detected` (×4) — loopback/localhost `urllib`
  calls (`core/models/ollama_client.py`, `ops/lifecycle/preflight.py:67` which already carries
  `# noqa: S310 — loopback only`, `ops/ci_witness.py`, `cloud/fetcher/sources.py`). Audit-level;
  the ruff-equivalent (S310) was already reviewed and suppressed, but `# noqa` does not silence
  semgrep (it uses `# nosemgrep`).
- `python.sqlalchemy.security.sqlalchemy-execute-raw-query` / `.formatted-sql-query` (×3) —
  f-string SQL in migrations, e.g. `ops/code_snapshot.py:304`
  `db.execute(f"ALTER TABLE snapshots ADD COLUMN {col} TEXT NOT NULL DEFAULT ''")` where `col`
  is an internal migration constant, not untrusted input (false-positive-in-context).
- `terraform.aws.security.*` (×2) — CloudWatch log group unencrypted, Lambda X-Ray tracing not
  active (deploy-side hardening, Phase-8 Terraform).
- `python.flask.security.audit.directly-returned-format-string` (×1).
- `yaml.github-actions.security.github-actions-mutable-action-tag` (×1) — semgrep flags a
  **mutable action tag** (our own `@v7` / `@v8.3.2` refs want full commit-SHA pins). Notably
  self-referential to the wiring fix just applied.
- (~11 more of the same families; full log at the run URL.)

None are exploitable sealed-core vulnerabilities; this is the classic "`p/default` on a mature
codebase surfaces an audit backlog" shape.

## Why it matters

This is a §10 situation ("any gate that cannot reach green on GitHub without changing gate
content → spec-defect finding; parity is the contract") crossed with §9 ("fixing code a gate
exposes is a finding + park, never bend the code in-plan"). I can neither silently fix 22 code
sites (out of scope; several need owner judgment on acceptability) nor silently drop `--error`
(gate-content change). So the resolution is an owner decision, not a build step.

**The parity crux:** GitLab's `Security/SAST.gitlab-ci.yml` template is **report-only** at the
pipeline level — the `sast` job exits 0 with findings and surfaces them in the MR security
widget; blocking is a separate approval-gate feature. The plan's §6(f) deliberately chose
`--error` (blocking), making the GitHub gate **stricter than the GitLab original it ports**.
The plan never verified `semgrep` green-on-clean before making it blocking (Item 2 only proved
it goes red on a *planted* defect), so the divergence surfaced only at the live run.

**Verification-methodology gap (recorded for future CI plans):** local red-proofs (Item 2)
validate gate *commands* under local `uv`/`uvx`, but cannot exercise (a) GitHub Actions
marketplace-action *resolution* (this is what killed green-run attempt 1: `setup-uv@v8` had no
moving major tag) nor (b) whether a *blocking* gate passes on the *current tree*. Only the live
run catches both. Future CI-style plans should: pre-validate every action ref against the GitHub
git-ref API at build time, and run each blocking gate on the clean tree before merging it.

## Disposition options (for oq-0015)

1. **Keep blocking; remediate/suppress the 22** — triage each: `# nosemgrep` (with justification)
   for the reviewed-intentional ones (the loopback urllib, the internal-constant SQL f-strings),
   SHA-pin actions for the mutable-tag rule, and open follow-up items for any genuine hardening
   (the Terraform AWS pair, the Flask format-string). Highest assurance; most work; needs a
   suppression-policy ruling. Code edits land in a *separate* scoped plan (not bp-015).
2. **Match GitLab parity: report-only** — drop `--error` (or `--error` → artifact upload), so
   semgrep reports but does not fail the pipeline. Restores true parity with the ported template;
   loses the blocking guarantee the plan wanted.
3. **A `.semgrepignore` / narrowed ruleset** — scope the gate to a curated subset above/below
   `p/default`. §6(f) forbids dropping *below* p/default; extending or path-scoping is allowed.

## Re-entry condition

Owner rules oq-0015. Until then bp-015's `semgrep` job is **parked** (it is one of five mutually
independent jobs — no `needs:` — so its red does not block the other four from running/greening);
bp-015 stays `in-progress`, and the bp-016 witness's definition of "attestable green" waits on
this ruling (it must know whether semgrep counts).
