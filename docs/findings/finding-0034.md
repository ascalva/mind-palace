---
type: finding
id: finding-0034
status: routed
ftype: direction
origin_plan: null   # operational — owner-surfaced runner-budget warning, 2026-07-11
route: orchestrator
created: 2026-07-11
updated: 2026-07-11
links:
  - .gitlab-ci.yml                          # workflow.rules + the included security/release templates
  - docs/findings/finding-0032.md           # sibling CI-topology finding (needs:[]); fold together
  - docs/memory/... (push & deploy policy)  # deploy needs an attested green pipeline
resolution: null
---

# finding-0034 — CI runner-minutes are a deploy-blocking bottleneck; every push burns them

## What

The namespace's **shared-runner compute is a hard monthly cap (400 min); at ~55/400 (14%)
on 2026-07-11**. When it hits zero, **no jobs or pipelines run at all** in any project in
the namespace.

The leak is structural, not incidental:
- `.gitlab-ci.yml` `workflow.rules` is `- when: always` (only `chore(release):` commits are
  `never`). So **every push, on any branch, creates a pipeline.**
- `ratchet` / `type-gate` / `vault-axis` correctly carry `rules:changes` on code paths, so
  they skip docs-only pushes. **But `next-version` (`.pre`, from the external
  `pipeline-fragments` template) and the security scans `semgrep-sast` + `secret_detection`
  (from GitLab's `Security/*` templates) carry NO `rules:changes`** — they run on EVERY
  pipeline, including docs-only pushes and non-main branch pushes.
- Net: an orchestrator docs commit, or a builder pushing its worktree branch, each burns
  `next-version` + `semgrep` + `secret_detection` runtime for zero code benefit. Observed
  live: ~6 orchestrator docs pushes on 2026-07-11 each spun those three jobs.

## Why it matters

**The deploy gate is coupled to this.** `mind-palace deploy` requires an ATTESTED
remote-green pipeline (`ci_witness` polls for `pipeline_green`, chained to the commit's
ingest). Zero minutes ⇒ no pipeline ⇒ no green attestation ⇒ **deploy is hard-blocked.**
So runner exhaustion isn't just slow CI — it removes the project's one owner-in-loop
release path. The owner flagged exactly this: "if we can't run a pipeline, we can't deploy."
It is a recurring constraint (the free tier resets monthly), so it will bite again.

## Recommended directions (route: orchestrator → owner), ranked

1. **Immediate, no config change — conserve (in effect now).** Batch pushes (commit locally;
   push once per unit, not per commit — the code-sensor ingests on local commit, so pushes
   are only for origin-sync / CI-attestation). Builders commit on their worktree branch and
   do NOT push it (a branch push burns the `when: always` jobs). Reserve headroom for a
   deploy pipeline. This alone removes the orchestrator/builder leak.

2. **Cheap CI-hygiene plan — make routine pushes ~free.** Give `next-version` +
   `semgrep-sast` + `secret_detection` a `rules:changes` (skip docs-only), mirroring
   `ratchet`/`type-gate`. Caveat: those jobs come from INCLUDED templates
   (`pipeline-fragments` `ref: v1.3.6`; `Security/SAST` + `Security/Secret-Detection`) — we
   override their `rules:` in our own `.gitlab-ci.yml` rather than editing the templates.
   **Fold this with finding-0032** (the `needs:[]` gate-topology change) into ONE small
   `.gitlab-ci.yml` plan — both are CI-gate-topology, same file, same blessing.

3. **Structural — a self-managed AWS runner (owner's suggestion; strong fit).** A
   self-managed runner does NOT consume the 400-min shared quota (you pay AWS compute
   instead), which **removes the cap and decouples deploy from the shared budget
   permanently.** Incremental given the project already runs on AWS (acct 054942746160,
   us-east-1, Terraform, Lambda/airlock). Flavors, cheapest-fit first:
   - **AWS Lambda MicroVMs (owner-identified; the leading candidate).** Launched 2026-06-22
     (Firecracker-powered, VM-level isolation with no shared kernel between sessions,
     near-instant start, up to 8h lifetime, ARM64/Graviton, ~$0.005/min, pay-per-use, no
     idle cost). AWS markets them *explicitly* for "running code as part of a CI/CD process"
     AND "running AI-generated code while guarding against prompt injection" — which is this
     project's exact posture. **The security fit is the headline, not the cost:** per-job
     Firecracker isolation IS the constitution's "executed code is powerless / sandboxed"
     non-negotiable, realized at the infra layer. Cost model matches a bursty personal
     project (pay only when a job runs) far better than an always-on box.
   - EC2 + `gitlab-runner` docker executor (simplest/most mature; small always-on ~$30/mo or
     scheduled/spot), or EKS Auto Mode + Spot ephemeral runners (enterprise-scale, ~90% off,
     overkill here).
   **Caveats to settle in a design note (MicroVMs are ~5 weeks old as of 2026-07):**
   GitLab-runner-on-MicroVM is a CUSTOM-executor integration (the public write-ups are
   GitHub Actions, not GitLab — maturity/DinD support to verify); ARM64-only means the CI
   images (`uv:python3.12-...`, the vault-axis dev-Vault **service container**, semgrep) need
   arm64 variants + a check that nested/service containers work under MicroVMs; confirm
   us-east-1 availability. **Security/IAM is load-bearing, not a checkbox:** the runner
   executes arbitrary code and must hold minimal/no IAM, no vault reach, ephemeral workspaces
   — the isolation model is the whole design. **Not overkill** — it is the correct structural
   answer to a recurring hard cap that gates the one release path; conservation (1) buys the
   runway to build it deliberately (design note → plan → owner blessing).

## Re-entry

Owner rules on (2) and (3). Parked as this finding; triggers that reopen immediately: the
minute balance hits a working floor, OR a deploy is actually blocked by exhaustion, OR the
next monthly reset arrives without a structural fix in place.

## Owner direction (2026-07-11)

**Keep building** (the bp-011→012→013 queue continues, merged locally, pushes batched to
one pipeline). **Definitely queue the AWS Lambda MicroVM runner** as the structural fix —
promote this to a **design note** for a design-tier (Fable/xhigh) session, NOT a supervision
session. **A platform axis is explicitly in scope:** the owner is open to **GitHub** if it
suits the workflow better. So the design note must weigh, at least:

- **Stay on GitLab + self-managed MicroVM runner** — least migration; but MicroVM↔GitLab is a
  custom-executor integration (public tooling is GitHub-Actions-first, so more DIY).
- **Add / migrate CI to GitHub (Actions)** — **the repo is ALREADY mirrored to GitHub via
  push (`github.com/ascalva/Mind-Palace`, owner 2026-07-11), so the code is already there —
  the friction is only the workflow + the deploy attestation, not a repo move.** The
  MicroVM-runner community tooling is GitHub-Actions-first (more mature), and GitHub's
  free-tier is far larger than GitLab's 400 min: **2,000 min/mo for a private repo, and
  UNLIMITED for a public one.** *First thing the design note must check: is the mirror public
  or private?* If public, GitHub Actions may be the cheapest fix of ALL — unlimited free CI,
  zero AWS infra, MicroVMs unnecessary. (Weigh against the project's privacy ethos — the
  framework code can be public while the corpus/data stays local; confirm nothing sensitive is
  in the tree.) **Cost either way:** the deploy path (`mind-palace deploy` → `ci_witness`
  polls for `pipeline_green` chained to the commit ingest) currently keys off **GitLab
  pipelines**; making GitHub authoritative means re-pointing `ci_witness` + moving
  `semantic-release` — that attestation-machinery move is the real migration cost to weigh
  against the tooling-maturity + free-minutes win.

Interim cheap fix (option 2 above — `rules:changes` on the always-run jobs + finding-0032's
`needs:[]`) proceeds regardless of the platform decision, on whichever host is current.
