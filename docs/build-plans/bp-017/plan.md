---
type: build-plan
id: bp-017
status: complete
design_ref:
  - docs/design-notes/ci-platform-and-runner-strategy.md # D5 (Pages dies with the tombstone), Consequences Plan C, parked #4
contract: builder
write_scope:
  - ".github/workflows/pages.yml"
  - "mkdocs.yml"
  - "docs/findings/**"
  - "docs/build-plans/bp-017/**"
session_budget: 1
cost:
  estimate: { model: sonnet, tokens: 100k } # small mechanical port; crisp checker (site builds, workflow lints)
  actual: { model: sonnet, tokens: 97449, tool_calls: 90, duration_min: 22 } # 0.97x — first near-1x pair in the ledger; excludes the orchestrator's seal fix (setup-uv step)
depends_on: [bp-015] # the tombstone kills GitLab Pages; this restores docs hosting on the new host
parallelizable_with: [bp-016] # disjoint write_scope
created: 2026-07-11
updated: 2026-07-12
links:
  - docs/findings/finding-0034.md # warrant-in-fact of the design note
supersedes: null
superseded_by: null
warrant: null
---

# Build Plan — Plan C: docs home — the docstring docs publish via GitHub Pages

> **Every section below is required.** N/A is an accountability act.

## 0. Mode & provenance

Graduated 2026-07-11 from the **ratified** `dn-ci-platform-and-runner-strategy` (D5 +
Consequences). Minted as its own small plan rather than folded into Plan A: bp-015's
verification burden (per-gate red proofs + live wiring) is already a full session, and
the docs lane has an independent, crisper checker. Implementation proceeds item-by-item
on owner approval; `proposed → ready` is the owner's hand edit.

## 1. Objective

The docstring-rendered documentation publishes via a GitHub Pages Actions workflow —
same mkdocs build the GitLab `pages` job ran — replacing the hosting the `.gitlab-ci.yml`
tombstone killed.

## 2. Context manifest

1. `docs/design-notes/ci-platform-and-runner-strategy.md` — D5, Consequences (Plan C),
   parked decision #4 (URL default).
2. `.gitlab-ci.yml:164-197` — the `pages` job being ported (command re-pinned §6).
3. `mkdocs.yml` — the site config whose URLs re-point (Item 13).
4. `.github/workflows/ci.yml` (as landed by bp-015) — the house style for workflow
   skeleton/setup this file matches.

## 3. Investigation & grounding

- **Q1 — what did the GitLab pages job run?** One command:
  `uvx --with mkdocs-material --with "mkdocstrings[python]" mkdocs build --site-dir public`
  (`.gitlab-ci.yml:195`), publishing the `public` artifact; gated by `rules:changes`
  (`:179-193`). The build command ports verbatim; the paths-filter does not — pages is
  not the gate (P2 is about `ci`), but minutes are unmetered and a uniform
  no-filter trigger keeps the two workflows consistent. Deviation recorded here.
- **Q2 — which URLs pin the old host?** `mkdocs.yml:5-7`: `site_url:
https://ascalva-projects.gitlab.io/mind-palace/`, `repo_url:
https://gitlab.com/ascalva-projects/mind-palace`. Repo-wide sweep 2026-07-11: the only
  live `gitlab.io` consumers are `mkdocs.yml` and the design note's own prose (historical
  record — not edited). No README badge, no other consumer.
- **Q3 — GitHub Pages deploy mechanics.** The Actions-native pattern:
  `actions/configure-pages` → build → `actions/upload-pages-artifact` →
  `actions/deploy-pages`, with `permissions: pages: write, id-token: write` and the repo
  setting Pages → Source: **GitHub Actions** (an owner console toggle — parked, §11).
  The code does not settle action versions; the builder pins current majors at build and
  journals them.
- **Q4 — does the build run today?** The GitLab job ran green within ~1 min on
  doc-relevant pushes (`.gitlab-ci.yml:164-167` comment). The builder re-proves locally
  as Item 12's acceptance — the identical command is the acceptance test, so drift shows
  immediately.

**Additional risks or questions surfaced during reading:** mkdocstrings/griffe renders
~330 modules; if a module rename since the last green pages run breaks a `nav:` entry,
mkdocs errors — that is a legitimate red for acceptance (fix the nav in `mkdocs.yml`,
in-scope), not a reason to loosen `--strict`ness.

## 4. Reconciliation

- `mkdocs.yml:5-7` (gitlab.io site_url / gitlab.com repo_url) → **[banner: correction]**,
  carried by Item 13: re-pointed to the GitHub host with the parked-decision default
  (`https://ascalva.github.io/Mind-Palace/`; note parked #4 — the owner may override the
  URL preference at the `proposed → ready` gate).
- `.gitlab-ci.yml:164-197` (the `pages` job) → no edit here — bp-015's tombstone already
  silences it; this plan is the **[cross-ref: extension]** that re-homes what it did.

## 5. Write scope

In: the new pages workflow, `mkdocs.yml`, findings, own directory. Out, deliberately:
`site/**` content (the markdown/API stubs — content changes are not this plan),
`.github/workflows/ci.yml` and `release.yml` (bp-015/bp-016), the runbook (no pages
reference exists — verified Q2), design notes, foundation denylist.

## 6. Interfaces pinned inline

**(a) The build command — verbatim from `.gitlab-ci.yml:195`:**

```
uvx --with mkdocs-material --with "mkdocstrings[python]" mkdocs build --site-dir public
```

(uvx keeps the doc tooling out of the project env — no pyproject/lock churn; mkdocstrings
uses griffe static analysis, zero project dependencies installed. Both properties must
survive the port.)

**(b) Workflow skeleton** (`.github/workflows/pages.yml`):

```yaml
name: pages
on:
  push:
    branches: [main]
  workflow_dispatch:
permissions:
  contents: read
  pages: write
  id-token: write
concurrency:
  group: pages
  cancel-in-progress: false # never cancel a deployment mid-flight (deploy-pages guidance)
# jobs: checkout → setup uv → §6(a) build → upload-pages-artifact (path: public) → deploy-pages
```

**(c) URL re-point** (`mkdocs.yml`, Item 13):

```yaml
site_url: https://ascalva.github.io/Mind-Palace/ # parked-decision default; owner may override at the gate
repo_url: https://github.com/ascalva/Mind-Palace
repo_name: Mind-Palace
```

## 7. Items

_(family numbering continues from bp-016)_

### Item 12 — `.github/workflows/pages.yml`: build + deploy

- **Objective:** the workflow per §6(a,b); publishes `public/` to GitHub Pages on every
  main push.
- **Files:** `.github/workflows/pages.yml`
- **Acceptance test:** `actionlint` exits 0; the local run of the §6(a) command exits 0
  and `public/index.html` + `public/api/` exist. Live proof at seal
  (orchestrator-executed; builders never push): the mirrored push's `pages` run is green
  and the site serves.
- **Falsifier:** the deploy run is green but the served site 404s the API pages
  (mkdocstrings failure downgraded to a warning somewhere in the chain) — checked by
  fetching `/api/core/` on the live site at seal, not just the run verdict.
- **Invariant(s):** doc tooling stays out of the project env (§6(a) note); no gate
  semantics — a red `pages` run never blocks deploy attestation (the witness reads only
  `ci`, bp-016 §6(d)).
- **Touches stored data?** no
- **Parallelizable?** yes (with Item 13) **Depends on:** bp-015 complete; owner console
  toggle (§11) for the live half — the workflow can land parked-on-toggle without
  blocking.

### Item 13 — `mkdocs.yml` re-point + old-URL sweep

- **Objective:** §6(c) applied; no live consumer of the old URL remains.
- **Files:** `mkdocs.yml`
- **Acceptance test:** the §6(a) build still exits 0 after the edit; repo-wide
  `grep -rn "gitlab.io"` hits only historical artifacts (design note prose, sealed
  journals/findings — history is history, never retro-edited).
- **Falsifier:** a live consumer of the old URL surfaces outside `mkdocs.yml` (Q2's
  sweep missed one) — file a finding and route rather than chase it out of scope.
- **Invariant(s):** historical artifacts are not retro-edited to the new URL.
- **Touches stored data?** no
- **Parallelizable?** yes (with Item 12) **Depends on:** none

## 8. Math carried explicitly

N/A — no mathematical object implemented (a docs build and two URLs).

## 9. Non-goals

Site content or navigation redesign (`site/**` is out of scope beyond what a broken nav
entry strictly requires — and that lives in `mkdocs.yml`); custom domains; docs
versioning (mike); porting the `rules:changes` filter (Q1 deviation, recorded); touching
`ci.yml`/`release.yml`; the GitLab Pages teardown (dies with bp-015's tombstone; the
stale `*.gitlab.io` site expires with the GitLab lane's retirement, bp-016 Item 11c).

## 10. Stop-and-raise conditions

The mkdocs build cannot go green without touching `site/**` content beyond a `mkdocs.yml`
nav fix (scope is wrong — finding, re-gate); GitHub Pages requires a paid feature for
this repo shape (it should not on a public repo — verify, then raise if real); the owner
console toggle is the only blocker left (that is a PARK on Item 12's live half, not a
stop — land the workflow, journal the re-entry).

## 11. Parked decisions

| Decision             | Default recorded                                                  | Rejected alternatives (why)                                                                        | Re-entry condition                                       |
| -------------------- | ----------------------------------------------------------------- | -------------------------------------------------------------------------------------------------- | -------------------------------------------------------- |
| Pages URL            | `https://ascalva.github.io/Mind-Palace/` (note parked #4 default) | custom domain (no need; adds DNS surface)                                                          | owner states a preference at the `proposed → ready` gate |
| Pages source toggle  | owner flips Settings → Pages → GitHub Actions                     | agent-side API enablement (repo settings are owner surface, same class as secret-scanning toggles) | owner flips it; Item 12's live half re-enters            |
| build trigger filter | none (every main push)                                            | port `rules:changes` (metered-era optimization; inconsistent with `ci.yml`'s no-filter posture)    | hosted-runner pressure ever returns (D7 trigger 3)       |

## 12. Dependency & ordering summary

Item 12 ∥ Item 13 (disjoint files; both reversible), one merge. Live verification at
seal is orchestrator-executed (push → green `pages` run → site serves → `/api/core/`
fetch). Cross-plan: **depends_on bp-015** (tombstone kills the old hosting; house
workflow style established); **parallelizable_with bp-016** (disjoint scope). The only
externally visible effect is the published site itself — the URL the owner already
expects (note D5, parked #4).
