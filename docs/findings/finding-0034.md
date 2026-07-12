---
type: finding
id: finding-0034
status: promoted
ftype: direction
origin_plan: null   # operational — owner-surfaced runner-budget warning, 2026-07-11
route: orchestrator
created: 2026-07-11
updated: 2026-07-12
links:
  - .gitlab-ci.yml                          # workflow.rules + the included security/release templates
  - docs/findings/finding-0032.md           # sibling CI-topology finding (needs:[]); fold together
  - docs/memory/... (push & deploy policy)  # deploy needs an attested green pipeline
resolution: promoted → docs/design-notes/ci-platform-and-runner-strategy.md, RATIFIED by owner hand 2026-07-11 (ruling record oq-0014; D4 = (i) end-state, GitHub becomes origin). Plan A (parity gate) = bp-015, sealed 2026-07-12 five-job green; Plan B (witness re-point + release relocation) = bp-016 ready; Plan C (Pages docs home) = bp-017 ready. MicroVM runners parked at D7 triggers.
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

## Owner direction + settled inputs (2026-07-11, evening) — TRIGGER FIRED, now priority

Two of this finding's open variables have resolved, and the trigger has fired:

1. **GitLab shared runners are EXHAUSTED (0 min).** The "minute balance hits a working
   floor" re-entry trigger has fired: there is now **no working CI gate at all** on GitLab.
   Every `.gitlab-ci.yml` pipeline is dead until the monthly reset. This promotes the design
   from queued to **priority** — but the owner chose the deliberate path (mint a proper design
   note + plan, Fable/xhigh), NOT a supervision-session hack.
2. **The GitHub mirror is PUBLIC** (`github.com/ascalva/Mind-Palace`, owner-confirmed
   2026-07-11). This resolves this finding's headline open question: **GitHub Actions is
   unlimited-free CI for a public repo** — the "cheapest fix of ALL" branch above is now LIVE
   (unlimited free CI, zero AWS infra required for the CI gate itself). Framework code is public;
   the corpus/data stays local (privacy ethos intact — confirm nothing sensitive is in the tree
   at design time).

**Owner's framing of the fork (2026-07-11):** GitHub is NOT necessarily either/or with the AWS
MicroVM runner. The owner sees three live shapes the design note must weigh as a *sequence/hybrid*,
not a mutually-exclusive pick:
- **(a) GitHub as the destination** — GitHub Actions IS the CI gate going forward; unlimited free
  minutes for a public repo make AWS runners unnecessary for the gate. Re-point `ci_witness` +
  move `semantic-release` to GitHub; retire `.gitlab-ci.yml`.
- **(b) GitHub as the bootstrap step toward proper AWS runners** — stand up GitHub Actions now
  (fast, free, unblocks the dead gate), then layer **self-hosted AWS Lambda MicroVM runners**
  under GitHub Actions (the MicroVM community tooling is GitHub-Actions-first — this is the
  MATURE integration path finding-0034 §3 flagged, vs. the DIY GitLab custom-executor). The
  Firecracker per-job isolation = the constitution's "executed code is powerless" at the infra
  layer, which matters most for the sandbox/effector tiers, not the lint gate.
- **(c) both / split** — GitHub-hosted runners for the cheap deterministic + security gate
  (free, public); self-hosted MicroVM runners for anything needing real isolation or heavier
  compute (sandbox-adjacent jobs, future effector CI). The gate and the sandbox have different
  runner needs.

**Existing starting artifact:** `.github/workflows/ci.yml` already exists (Jun 27) but is STALE —
missing the mypy type-gate (bp-008 split: 0-floor + 69 baseline), SAST/secret-detection,
semantic-release, and predating the uv migration + the `check_imports.py` rename (finding-0014).
Relying on it today is a FALSE GREEN. The design note's first plan must bring it to parity, not
trust it as-is.

**finding-0032 interaction:** its `needs:[]` fix is a GitLab `.pre`-stage-suppression remedy. On
GitHub Actions, jobs are independent by default (no implicit stage ordering), so the finding-0032
concern is largely SUBSUMED by a GitHub migration — the design note should note this rather than
port `needs:[]` blindly. If GitLab stays authoritative for any window, finding-0032 still applies there.

**Next step (deferred to a Fable/xhigh design-tier session, owner-directed):** promote this
finding (+ finding-0032) into a **runner-strategy design note** structured around the (a)/(b)/(c)
fork above, ratify (owner gate), `/graduate` into plans (first plan = the deterministic+security
GitHub Actions gate to parity; later plan(s) = deploy-attestation re-point + optional MicroVM
runners). bp-013 does NOT need this to land — it merges on local-green (CI is attestation, not the
gate).

## Promoted — closed at /triage (2026-07-12), ratification swept from oq-0014

The full promotion chain completed:
- **Note drafted** (`ci-platform-and-runner-strategy.md`, warrant: this finding + finding-0032)
  → **RATIFIED by the owner's hand 2026-07-11** (the blessing gate proper; ruling record
  oq-0014). **D4 ruled (i) end-state: GitHub becomes origin** — releases run on GitHub
  (`workflow_dispatch`, witness-dispatched), `@semantic-release/gitlab → @semantic-release/github`,
  mirror reverses/retires, PR/branch CI unlocks.
- **Graduated + built:** Plan A (parity gate) = **bp-015, sealed 2026-07-12** — five-job
  attestable green on GitHub Actions (`ratchet` · `type-gate` · `vault-axis` · `gitleaks` ·
  `semgrep` report-only per oq-0015), the dead-gate condition this finding opened on is CLOSED
  (unlimited free CI on the public repo). Plan B (witness re-point + release relocation) =
  **bp-016 ready**; Plan C (Pages docs home) = **bp-017 ready**.
- **MicroVM runners:** parked at the note's D7 triggers (unchanged — the Firecracker isolation
  case re-enters with sandbox-adjacent CI needs, not the lint gate).
- finding-0032 promoted alongside (D6, subsumed by construction).
