---
type: build-plan
id: bp-016
status: ready
design_ref:
  - docs/design-notes/ci-platform-and-runner-strategy.md # D3 (witness re-point), D4 RULED end-state (GitHub becomes origin), P3/P5
contract: builder
write_scope:
  - "ops/ci_witness.py"
  - "scripts/ci_witness.py"
  - "tests/unit/test_ci_witness.py"
  - ".releaserc.json"
  - "package.json"
  - "pnpm-lock.yaml"
  - ".github/workflows/release.yml"
  - "docs/runbook.md"
  - "docs/findings/**"
  - "docs/build-plans/bp-016/**"
session_budget: 1
cost:
  estimate: { model: fable, tokens: 300k } # deploy-promotion-gate blast radius: the false-green direction needs judgment, not just tests
  actual: null
depends_on: [bp-015] # the witness needs a live green `ci` workflow to point at (D1: parity before attestation)
parallelizable_with: [bp-017] # disjoint write_scope
created: 2026-07-11
updated: 2026-07-11
links:
  - docs/design-notes/attestation-layer.md # the witness this plan re-points (status: draft)
  - docs/findings/finding-0034.md # warrant-in-fact of the design note
supersedes: null
superseded_by: null
warrant: null
---

# Build Plan — Plan B: witness re-point + release relocation — deploy attestation reads GitHub; semantic-release moves with the origin

> **Every section below is required.** N/A is an accountability act.

## 0. Mode & provenance

Graduated 2026-07-11 from the **ratified** `dn-ci-platform-and-runner-strategy`. The D4
fork is **ruled**: (i) end-state — GitHub becomes origin (owner answer to oq-0014,
2026-07-11). Owner steps (PAT mint, origin re-point, mirror disposition, repo toggles)
are carried as parked items with re-entry conditions — **never block on the owner** (§5
rule); the P5 sequencing guard gates exactly one item (Item 10). Implementation proceeds
item-by-item on owner approval; `proposed → ready` is the owner's hand edit.

## 1. Objective

`mind-palace deploy`'s attestation gate reads GitHub Actions — same verdict vocabulary,
same emission shape, `run:<id>` — and semantic-release relocates to a GitHub
`workflow_dispatch` workflow the witness dispatches, landing only with/after the owner's
origin re-point (P5: the diverging shape is never built).

## 2. Context manifest

1. `docs/design-notes/ci-platform-and-runner-strategy.md` — D3 (mapping, grace, auth),
   D4 ruling, P3/P5.
2. `ops/ci_witness.py` — whole file; every function is re-pointed (couplings mapped §3 Q1).
3. `scripts/ci_witness.py` — the CLI whose surface must NOT change (§6(a)).
4. `ops/lifecycle/launcher.py:254-262,387-428` — the deploy-gate call sites. READ-ONLY:
   the contract consumer this plan must not touch.
5. `tests/unit/test_ci_witness.py` — the existing verdict tests Item 7 extends.
6. `.releaserc.json` + `package.json` — the release shape Item 10 relocates.
7. `.github/workflows/ci.yml` (as landed by bp-015) — the workflow file path the witness
   queries by name.
8. `docs/runbook.md` — where the new §CI witness section (Item 9) lands.

## 3. Investigation & grounding

- **Q1 — every GitLab coupling in the witness, mapped:** `PROJECT`/`API` constants
  (`ops/ci_witness.py:28-29`); `_PENDING` GitLab status vocabulary (`:32`);
  `PRIVATE-TOKEN` header (`:41-43,:104-107`); Keychain service `gitlab-api` (`:47-50`);
  `pipeline_for` newest-first listing (`:53-56`); `verdict()` incl. `'manual'→green`
  (`:59-66`); attestation output `pipeline:<id>` (`:69-76`); `check()`'s
  absent-returns-immediately (`:88-91`); rotation via
  `/personal_access_tokens/self/rotate` (`:115-154`); `release()` playing a manual
  in-pipeline job (`:157-182`). Each is re-pointed or re-dispositioned in Items 6–10.
- **Q2 — the contract that must survive:** the launcher invokes
  `uv run scripts/ci_witness.py check <sha>` / `release <sha>` as subprocesses and
  branches on return code (`ops/lifecycle/launcher.py:260-261,423-428`);
  `scripts/ci_witness.py:22-29` is the arg surface. Both stay byte-compatible — this plan
  touches no launcher line.
- **Q3 — GitHub verdict source.** Query the `ci` workflow **by file path** (immune to
  display-name edits): `GET /repos/ascalva/Mind-Palace/actions/workflows/ci.yml/runs?head_sha=<sha>&per_page=1`
  → `{workflow_runs: [{id, status, conclusion, html_url, …}]}`, newest first. The code
  cannot settle an external API: pinned from GitHub's documented schema (§6(c,d)); the
  builder re-verifies against the live endpoint (curl) before coding and journals the
  observed shape.
- **Q4 — does `'manual'→green` port?** No. It existed because semantic-release was a
  manual job INSIDE the GitLab pipeline (`:65-66`). On GitHub the release is a separate
  `workflow_dispatch` workflow — no manual gate ever sits inside `ci`. Only
  `completed`+`success` is green; every other completed conclusion (incl.
  `action_required`, `neutral`, `skipped`) is red — the witness never guesses (P3).
- **Q5 — absent-grace.** GitLab created pipelines synchronously with the push to origin,
  so absent meant "never pushed" (`:88-91`). Until the origin re-point executes, GitHub
  learns of a sha only when the push-mirror fires (batches up to ~5 min); after
  re-point, lag shrinks but run creation is still asynchronous. Pinned §6(f): the grace
  lives in `check()`'s poll loop; `verdict()` stays pure (absent is absent) so the
  vocabulary is untouched.
- **Q6 — auth + rate limits.** Unauthenticated GitHub reads: 60 req/h/IP — one 600 s
  poll at 10 s intervals consumes the hour. A fine-grained PAT (Actions: read + write —
  write is what permits `workflow_dispatch`) goes to Keychain as `github-api`, account
  `mind-palace` (mirror of the `gitlab-api` pattern `:47-50`). The witness sends the
  token when present and still works degraded without one (public repo).
- **Q7 — does `rotate()` port?** **No — deviation from the note.** GitLab exposes
  `POST /personal_access_tokens/self/rotate` (`:131`); GitHub exposes **no self-rotation
  endpoint for user PATs** (fine-grained PATs regenerate via the web UI only). The
  note's D3 says "mirroring the `gitlab-api` pattern including `rotate()`" — carried
  openly as Item 8: `rotate()` survives as a guided-manual play, not silent removal. The
  builder re-verifies the no-endpoint fact against current GitHub REST docs at build
  time; if an endpoint now exists, §10 fires and the GitLab shape ports after all.
- **Q8 — release relocation.** Today `release()` plays the manual `semantic-release` job
  on the sha's green pipeline (`:157-182`). Target: after confirming green for the sha,
  `POST /actions/workflows/release.yml/dispatches` (`ref: main`); degradation parity
  with today (`:166-171`) pinned in §6(e). `.releaserc.json:56-63` swaps
  `@semantic-release/gitlab → @semantic-release/github` (same three disable flags);
  `package.json:21` dep swap; lockfile regenerates. Commit-back assets (`:46-55`)
  unchanged — and commit-back only converges on main if GitHub IS origin, which is why
  P5 gates Item 10 on the owner's re-point.
- **Q9 — does the release commit-back re-trigger `ci`?** No — pushes authenticated with
  the workflow's `GITHUB_TOKEN` do not trigger new runs (GitHub's loop guard; builder
  confirms on the first live release). Release shas therefore carry no `ci` verdict —
  **identical to today**: GitLab skips pipelines on `chore(release):` commits
  (`.gitlab-ci.yml:1-4`), so deploy-at-a-release-sha is already refused-by-absent. Not a
  regression; recorded honestly.
- **Q10 — tag parity.** semantic-release computes the next version from tag history. The
  push-mirror is main-only; whether `v*` tags reached GitHub is unverified — the code
  does not settle it; `git ls-remote --tags` against both hosts does. Pinned as Item
  10's pre-check; a mismatch is stop-and-raise (owner pushes tags at re-point, Item 11b).

**Additional risks surfaced during reading:** multiple runs can exist per sha (re-runs,
`workflow_dispatch`); the GitLab code took `rows[0]` newest-first (`:53-56`) — pin the
same "newest run wins" rule and have the builder verify GitHub's sort order empirically.

## 4. Reconciliation

- `ops/ci_witness.py:1-18` module docstring — "attest GitLab pipeline verdicts …
  talks to gitlab.com" → **[banner: correction]**, carried by Item 6: rewritten for the
  GitHub host; the zone note (unsealed ops tier; the sealed core never reaches out)
  carries over verbatim — it is host-independent and still true.
- `ops/ci_witness.py:129,167-170` reference "runbook §CI witness" — **the section does
  not exist** (grep 2026-07-11: zero matches for 'witness' in `docs/runbook.md`). A
  dangling pointer → **[cross-ref: extension]**, repaired by Item 9 creating the section.
- `.releaserc.json:56-63` (`@semantic-release/gitlab`) → **[correction]**, carried by
  Item 10 — never edited before its P5 gate condition holds.
- `docs/design-notes/attestation-layer.md` (status: **draft**) speaks GitLab pipeline
  vocabulary for the witness. Design notes sit outside builder write_scope — the
  cross-reference (one line pointing at `dn-ci-platform-and-runner-strategy` D3 and the
  `pipeline:→run:` output change) is applied by the **orchestrator** at seal, not the
  builder; recorded here so it is not lost.

## 5. Write scope

In: the witness module, its CLI shim, its unit tests, the release trio
(`.releaserc.json`, `package.json`, `pnpm-lock.yaml`), the new release workflow, the
runbook §CI witness section, findings, own directory. Out, deliberately:
`ops/lifecycle/launcher.py` (the contract consumer — if it needs a change, the contract
broke: spec-defect finding); `.github/workflows/ci.yml` (bp-015's); mkdocs/pages
(bp-017); design notes; the foundation denylist.

## 6. Interfaces pinned inline

**(a) CLI contract — unchanged, byte-compatible** (`scripts/ci_witness.py:22-29`;
consumer `ops/lifecycle/launcher.py:260-261`):

```
uv run scripts/ci_witness.py check <sha>     # rc 0 ONLY on attested green
uv run scripts/ci_witness.py release <sha>   # rc 0 on dispatched OR degraded-print; rc 1 on not-green/error
uv run scripts/ci_witness.py rotate          # Item 8 disposition
```

```python
ci_check_cmd: tuple[str, ...] | None = ("uv", "run", "scripts/ci_witness.py", "check")
ci_release_cmd: tuple[str, ...] | None = ("uv", "run", "scripts/ci_witness.py", "release")
```

**(b) Verdict vocabulary — preserved exactly (P3):** `'green' | 'red' | 'pending' |
'absent'`; signature stays `verdict(run: dict[str, Any] | None) -> str`; pure, no
network, no clock.

**(c) GitHub → vocabulary mapping (Q3/Q4):**

| GitHub run state                                                                                                                         | verdict   |
| ---------------------------------------------------------------------------------------------------------------------------------------- | --------- |
| no run for sha                                                                                                                           | `absent`  |
| `status != "completed"` (`queued`, `in_progress`, `waiting`, `requested`, `pending`)                                                     | `pending` |
| `status == "completed"` and `conclusion == "success"`                                                                                    | `green`   |
| `status == "completed"` and any other conclusion (`failure`, `cancelled`, `timed_out`, `action_required`, `neutral`, `skipped`, `stale`) | `red`     |

Only `success` is green. The witness never guesses.

**(d) Endpoints + headers:**

```
run_for(sha):  GET https://api.github.com/repos/ascalva/Mind-Palace/actions/workflows/ci.yml/runs?head_sha=<sha>&per_page=1
               → workflow_runs[0] (newest) or None
dispatch:      POST https://api.github.com/repos/ascalva/Mind-Palace/actions/workflows/release.yml/dispatches
               body {"ref": "main"} → HTTP 204 (fire-and-forget; print the Actions URL after)
headers:       Accept: application/vnd.github+json
               X-GitHub-Api-Version: 2022-11-28
               Authorization: Bearer <token>        # only when Keychain github-api present
```

**(e) `release(sha)` degradation chain** (parity with `:157-182`):
not green → rc 1 · no token → print the Actions dispatch URL for a by-hand play, rc 0 ·
dispatch 404 (release workflow not yet landed / Item 10 parked) → print "cut locally:
`pnpm run release` (D4 interim)", rc 0 — degraded, never failed; deploy proceeds.

**(f) Grace constant:** `GRACE_S = 300.0`. Inside `check()`'s poll loop: an `absent`
verdict with `elapsed < min(GRACE_S, wait_s)` is treated as pending (keep polling); still
absent past grace ⇒ conclude absent, rc 1, message names mirror lag as the likely cause.
`verdict()` itself is untouched.

**(g) Attestation emission — same shape, new output tag (D3):**

```python
attestor.emit(agent_role="ci_witness", action=f"pipeline_{v}",
              input_hashes=[sha], output_hashes=[f"run:{run['id']}"])
```

Action names `pipeline_green|pipeline_red` are PRESERVED (P3 — chain history stays one
vocabulary); only the output prefix changes `pipeline: → run:`.

**(h) Keychain:** service `github-api`, account `mind-palace`; read mirrors `:47-50`
(`security find-generic-password -a mind-palace -s github-api -w`); store play (runbook
Item 9): `security add-generic-password -U -a mind-palace -s github-api -w <PAT>`.

**(i) Release workflow skeleton** (`.github/workflows/release.yml`, Item 10):

```yaml
name: release
on: workflow_dispatch
permissions:
  contents: write # @semantic-release/git commit-back + tag push
concurrency: release # never two releases interleaved
jobs:
  release:
    runs-on: ubuntu-latest
    steps:
      # checkout with fetch-depth: 0 (semantic-release reads full tag history)
      # node 20 (package.json engines) + pnpm 9.15.0 (packageManager field)
      # pnpm install --frozen-lockfile
      # pnpm run release          env: GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

**(j) `.releaserc.json` diff (Item 10):** `"@semantic-release/gitlab"` →
`"@semantic-release/github"`, keeping exactly
`{"successComment": false, "failComment": false, "failTitle": false}`; all other plugins
and the `@semantic-release/git` assets block (`:46-55`) unchanged. `package.json`: drop
`"@semantic-release/gitlab": "^13.2.9"`, add `@semantic-release/github` at the current
major (pnpm add -D pins it; journal the version).

## 7. Items

_(family numbering continues from bp-015)_

### Item 6 — GitHub backend in `ops/ci_witness.py`

- **Objective:** `run_for`/`verdict`/`check`/`attest_verdict` speak GitHub per §6(b,c,d,f,g,h);
  module docstring rewritten (§4); the GitLab read-path (`PROJECT`/`API`, `_PENDING`,
  `pipeline_for`) is removed — dead code once bp-015's tombstone guarantees GitLab
  verdicts are permanently absent.
- **Files:** `ops/ci_witness.py`
- **Acceptance test:** `uv run pytest tests/unit/test_ci_witness.py` green (with Item 7's
  suite); `uv run ruff check .` + `uv run mypy ops` clean; the module imports and its
  pure functions run with zero network.
- **Falsifier:** any non-`success` conclusion mapping to green (the false-green
  direction — a wrongly-attested deploy gate), or `check()` concluding absent before
  grace expiry under a mocked mirror-lag sequence.
- **Invariant(s):** §6(a) CLI contract byte-compatible; §6(b) vocabulary unchanged; §6(g)
  action names preserved; launcher untouched.
- **Touches stored data?** no (attestation emission is append-only by design and only
  fires on live runs, not in tests)
- **Parallelizable?** no **Depends on:** bp-015 complete

### Item 7 — the test suite: GitHub shapes + grace timing

- **Objective:** pin the §6(c) mapping row-by-row (every conclusion listed), the
  absent-grace loop (mocked `run_for`: None while `elapsed < grace` → keeps polling; None
  past grace → rc 1), and Keychain-absent degradation. No network; inject/mock `_get`.
- **Files:** `tests/unit/test_ci_witness.py`
- **Acceptance test:** suite green; every §6(c) row has an assertion.
- **Falsifier:** the falsifier-demo discipline — run the new suite once against the
  pre-change (GitLab) module and show red; a suite that passes against BOTH backends pins
  nothing.
- **Invariant(s):** tests stay pure (no live GitHub calls; `not live` tier).
- **Touches stored data?** no
- **Parallelizable?** no **Depends on:** Item 6

### Item 8 — `rotate()` disposition (the honest deviation, Q7)

- **Objective:** `rotate()` becomes a guided-manual play for GitHub: print the
  fine-grained-PAT re-mint route (repo-scoped, Actions read+write) + the §6(h) Keychain
  store command, rc 1 (nothing rotated programmatically). GitLab rotation code goes with
  the read-path. Deviation from the note's "including rotate()" is stated in the code
  comment and the journal — the owner sees it at this item's gate.
- **Files:** `ops/ci_witness.py`, `tests/unit/test_ci_witness.py`
- **Acceptance test:** `uv run scripts/ci_witness.py rotate` prints the re-mint
  instructions incl. the Keychain command and exits 1; a unit test pins the message.
- **Falsifier:** a GitHub self-rotation endpoint exists after all (builder's build-time
  doc check, Q7) — then this item's approach is wrong: stop-and-raise, port the GitLab
  fail-safe ordering (verify-new → store → read-back → attest) instead.
- **Invariant(s):** no secret ever printed, logged, or committed; Invariant 10.
- **Touches stored data?** no
- **Parallelizable?** yes (with Item 9) **Depends on:** Item 6

### Item 9 — runbook §CI witness (repairs the dangling reference)

- **Objective:** a new runbook section: what the witness attests and why; the
  `github-api` PAT mint play (fine-grained, Actions read+write, nothing else) + Keychain
  store; rotate-is-manual note; the deploy-gate interaction
  (`launcher.py:423-428`); absent-grace and mirror-lag behavior.
- **Files:** `docs/runbook.md`
- **Acceptance test:** `grep -n 'CI witness' docs/runbook.md` hits a section header; the
  two in-code references (`ops/ci_witness.py:129,167-170` regions post-edit) resolve to
  a section that exists.
- **Falsifier:** following the section verbatim on a clean machine fails to produce a
  working authenticated witness call (owner/orchestrator replays it at seal).
- **Invariant(s):** no secret material in the docs — plays only.
- **Touches stored data?** no
- **Parallelizable?** yes (with Item 8) **Depends on:** Item 6

### Item 10 — release relocation (P5-GUARDED: lands only WITH/AFTER the origin re-point)

- **GATE CONDITION (pinned):** `git remote get-url origin` resolves to
  `github.com[:/]ascalva/Mind-Palace` BEFORE this item's commit merges, AND the Item 10
  pre-check passes: `git ls-remote --tags` parity between GitLab and GitHub (Q10). If
  the owner has not re-pointed by session time: **PARK this item** (re-entry: Item 11b
  done), proceed with everything else. The diverging shape — GitHub-hosted release while
  GitLab is origin — is never built, not even briefly (P5).
- **Objective:** semantic-release runs as `.github/workflows/release.yml` (§6(i));
  `.releaserc.json`/`package.json`/lockfile per §6(j); `release(sha)` dispatches per
  §6(d,e).
- **Files:** `.releaserc.json`, `package.json`, `pnpm-lock.yaml`,
  `.github/workflows/release.yml`, `ops/ci_witness.py` (dispatch path),
  `tests/unit/test_ci_witness.py` (mocked dispatch).
- **Acceptance test:** `pnpm install --frozen-lockfile` exits 0; `npx semantic-release
--dry-run` exits 0 against the GitHub origin and computes a sane next version (>
  v1.0.0 lineage, proving tag history is visible); `actionlint` clean on release.yml;
  mocked-dispatch unit test green.
- **Falsifier:** the dry-run wants to push anywhere other than origin, or computes a
  version that ignores the existing `v1.0.0` tag (tag history invisible → the Q10
  assumption failed).
- **Invariant(s):** P5 — commit-back lands only on the true origin; no real release is
  cut in this plan (dispatch is exercised mocked; the first live release is
  owner-initiated).
- **Touches stored data?** no (repo files only; external effect — an actual release —
  requires a later owner-initiated dispatch)
- **Parallelizable?** no **Depends on:** Items 6–7 + owner step 11b

### Item 11 — the owner-step ledger (parked sub-items; never blocking)

- **Objective:** carry the owner-only steps as first-class parked entries the journal
  tracks to done, each with a re-entry:
  - **(a) mint the fine-grained PAT** (Actions read+write on `Mind-Palace`) → Keychain
    `github-api` per §6(h). Re-entry: authenticated polling + dispatch work; witness runs
    degraded until then.
  - **(b) origin re-point:** `git remote set-url origin
git@github.com:ascalva/Mind-Palace.git` + `git push origin --tags` + `ls-remote`
    parity check. Gates Item 10.
  - **(c) mirror reversal/retirement** on the GitLab side. Re-entry condition for
    deleting the GitLab lane entirely (note parked #3).
  - **(d) flip GitHub secret-scanning + push-protection** (repo settings; note parked
    #6). Any time; zero dependencies.
- **Files:** journal only (ledger table).
- **Acceptance test:** the journal ledger exists with per-step status + re-entry
  condition; no session ever blocked waiting on a step.
- **Falsifier:** a criterion found silently blocked on an owner step without a park
  entry (the never-block rule violated in practice).
- **Invariant(s):** none of (a)–(d) is agent-executed — they change where pushes land
  and what credentials exist; owner-by-hand.
- **Touches stored data?** no
- **Parallelizable?** yes (ledger spans the session) **Depends on:** none

## 8. Math carried explicitly

N/A — no mathematical object implemented (a grace-window constant and a status mapping).

## 9. Non-goals

Touching `ops/lifecycle/launcher.py` or any deploy logic (the CLI contract is the seam);
changing attestation action names or chain semantics (P3); editing `.github/workflows/ci.yml`
(bp-015's); Pages/docs (bp-017); a GitLab `needs:[]` rider (D6 subsumed; D4 end-state
forecloses an authoritative GitLab lane); executing any owner step; cutting a real
release.

## 10. Stop-and-raise conditions

A GitHub PAT self-rotation endpoint exists (Item 8's approach is then wrong — re-plan
that item, don't improvise); tag-parity mismatch at Item 10's pre-check (owner must push
tags first — park); any change needed in `launcher.py` (the contract broke: spec-defect
finding); PAT permissions prove insufficient for dispatch (park on re-mint, degrade
gracefully meanwhile); the attestation chain rejects the `run:<id>` output shape
anywhere downstream (blast-radius surprise — stop, finding, owner question if design-level).

## 11. Parked decisions

| Decision                                       | Default recorded                                  | Rejected alternatives (why)                                                                              | Re-entry condition                                                            |
| ---------------------------------------------- | ------------------------------------------------- | -------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------- |
| Item 10 timing                                 | parked until origin re-point (11b)                | land it early behind a flag (P5 says the diverging shape is never built — a flag is still a built shape) | owner runs 11b                                                                |
| `gitlab-api` Keychain token                    | left in place                                     | delete now (GitLab stays reachable until the mirror retires; the token is the owner's to revoke)         | Item 11c done → owner revokes + deletes                                       |
| GitLab release history (v1.0.0 release object) | stays on GitLab as history                        | migrate release notes to GitHub (no consumer; CHANGELOG.md in-repo is the record)                        | someone actually needs it                                                     |
| absent-grace size                              | 300 s (≤ the 600 s poll, ≥ observed mirror batch) | 0 s (today's semantics — wrong under mirror lag); full wait_s (masks "never pushed")                     | origin re-point makes lag ~0; revisit constant at first post-migration triage |

## 12. Dependency & ordering summary

Item 6 → Item 7 → {Item 8 ∥ Item 9} → Item 10 (P5-gated on owner step 11b + tag parity);
Item 11 is a ledger spanning the session. All of 6–9 are reversible code/docs writes; 10
is the only item with an external-facing consequence (a dispatchable release lane) and
lands last. Cross-plan: **depends_on bp-015** (a green `ci` workflow must exist; the
tombstone kills the GitLab read-path this plan deletes); **parallelizable_with bp-017**
(disjoint scope). The witness keeps working degraded (unauthenticated, no dispatch)
until owner steps (a)/(b) land — deploy stays possible the moment bp-015 + Item 6 give
it an attestable green.
