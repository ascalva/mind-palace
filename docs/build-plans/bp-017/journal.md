# BP-017 — Build journal

Alive while the plan is `in-progress`; sealed by `/triage` on completion.
Fresh-agent test (§9): a session given only `plan.md` + this journal + the
write-scope files must continue without re-asking anything already answered.

---

## 2026-07-12 (final) — gate run, commits landed, session closes; live proof owed at seal

**Status line:** Session complete to the builder boundary: Items 12 & 13 committed
(`f5afa26`, `de4e6cd`), finding-0045 committed (`cd4853e`), five-part gate run with
results below; plan stays `in-progress` — the orchestrator owes the live half at seal
(push → green `pages` run → site serves → `/api/core/` fetch) and the `complete` flip.

**Five-part green gate (run verbatim in this worktree, fresh `uv sync --extra dev`):**

1. `uv run ruff check .` → `All checks passed!` exit 0.
2. `uv run mypy core agents eval ops scheduler scripts` → `Success: no issues found in
   168 source files` exit 0.
3. `uv run mypy` (argless) → `Found 69 errors in 20 files (checked 334 source files)` —
   **exactly the pinned tests/ baseline 69** (finding-0029). Asserted, not assumed.
4. `uv run python -m ops.type_gate` → Tier-2 membership OK; bare-ignore scan OK; exit 0.
5. `uv run pytest -q` (full, no marker filter) →
   `2 failed, 822 passed, 8 skipped in 781.77s (0:13:01)`
   - The two reds, honestly: `tests/e2e/test_scheduler_live.py::
     test_supervisor_dispatches_a_real_job` and `tests/e2e/test_semantic_search_live.py::
     test_semantic_search_ranks_relevant_first` — both `live`-marked e2e tests, both
     failing with `TimeoutError: timed out` inside `urllib` reaching Ollama
     `/api/embed`. Root cause is environmental contention, not this diff: the bp-016
     builder's own full `pytest -q` was running **concurrently in its sibling worktree**
     (observed: PID 20194, `agent-a9ab532a788bd1549`) against the same single local
     Ollama (v0.31.2, reachable and healthy when probed immediately after). This plan's
     entire diff is one workflow YAML + two URL lines in `mkdocs.yml` — no import path,
     no runtime surface, no causal route to the scheduler or semantic search.
   - Deterministic tier proven independently: `uv run pytest -q -m 'not live and not
     podman and not needs_vault and not needs_restic'` → `808 passed, 4 skipped,
     20 deselected in 14.16s`, exit 0 (the CONVENTIONS fast ratchet / commit gate).
   - Per the orchestrator's mid-session direction, reporting the red with output rather
     than looping on a third full-suite run. Recommended check at seal: re-run the two
     named live tests (or full `-m live`) with no concurrent suite — expected green;
     nothing in this diff touches them.

**Commits (this worktree branch `worktree-agent-a35f3a0cb9b0f591d`):**
- `f5afa26` ops(pages): add GitHub Pages workflow porting the GitLab docs job (Item 12)
- `de4e6cd` fix(mkdocs): re-point site_url/repo_url to the GitHub Pages host (Item 13)
- `cd4853e` docs(findings): file finding-0045 — .gitignore misses public/ build output
- (this entry + the plan's `ready → in-progress` flip land as the closing docs commit)

**What the orchestrator owes at seal:** merge this branch; push; watch the `pages` run
go green (first live exercise of the four marketplace-action refs — local actionlint
cannot prove resolution, bp-015 precedent); fetch the served site and `/api/core/`
specifically (Item 12's falsifier); optionally re-run the two live tests uncontended;
apply finding-0045's one-line `.gitignore` fix (out of this plan's scope); flip plan
status to `complete`. The owner console toggle (Settings → Pages → GitHub Actions) is
already done per session brief — no park remains on Item 12's live half.

## 2026-07-12 — Items 12 & 13 landed; local build/lint proofs green; finding-0045 filed

**Status line:** Both items complete locally (workflow authored + actionlint clean +
§6(a) build proven twice; mkdocs.yml re-pointed + old-URL sweep clean); plan stays
`in-progress` — live proof (push → green `pages` run → `/api/core/` fetch) is
orchestrator-executed at seal, not this session's job.

**Completed:**

- **Item 12 — `.github/workflows/pages.yml`: build + deploy.** Authored per §6(a,b):
  `build` job (checkout → configure-pages → §6(a) uvx mkdocs build → upload-pages-artifact)
  then a separate `deploy` job (`needs: build`, `environment: github-pages`, deploy-pages).
  Split into two jobs (rather than one) because `deploy-pages` requires the
  `environment:`/`page_url` output shape from the Actions-native docs — a single-job
  version cannot express the deployment's environment binding cleanly; this is the
  standard actions/starter-workflows pages.yml shape, not a deviation from anything §6
  pinned.
  - Triggers: `push: [main]` + `workflow_dispatch` (identical to ci.yml). Deliberate
    **deviation from the ported job's `rules:changes` paths filter** (plan Q1, already
    recorded in the plan — not re-litigated here): no `paths:` filter, matching ci.yml's
    P2 no-filter posture; minutes are unmetered on this host.
  - `permissions: {contents: read, pages: write, id-token: write}`; `concurrency: {group:
    pages, cancel-in-progress: false}` — verbatim from §6(b) (never cancel a Pages deploy
    mid-flight).
  - **Action versions pinned (current majors verified against the GitHub API at build
    time, 2026-07-12 — bare-major refs, matching `ci.yml`'s `actions/checkout@v7`
    convention since all four have moving-major tags, unlike `setup-uv` which does not):**
    | Action | Pinned | Verified via |
    | --- | --- | --- |
    | `actions/checkout` | `@v7` | `GET /repos/actions/checkout/releases/latest` → `v7.0.0` |
    | `actions/configure-pages` | `@v6` | `GET /repos/actions/configure-pages/releases/latest` → `v6.0.0` |
    | `actions/upload-pages-artifact` | `@v5` | `GET /repos/actions/upload-pages-artifact/releases/latest` → `v5.0.0` |
    | `actions/deploy-pages` | `@v5` | `GET /repos/actions/deploy-pages/releases/latest` → `v5.0.0` |
  - **actionlint:** `actionlint .github/workflows/pages.yml` → `EXIT: 0` (Homebrew
    `actionlint`, same invocation bp-015's journal recorded for `ci.yml`; no repo-level
    actionlint config exists, so no other invocation was in play).
  - **§6(a) build, run twice (once mid-session, once as a final clean proof after
    finding-0045's cleanup) — both exit 0:**
    ```
    $ uvx --with mkdocs-material --with "mkdocstrings[python]" mkdocs build --site-dir public
    INFO    -  Cleaning site directory
    INFO    -  Building documentation to directory: .../public
    INFO    -  Doc file 'index.md' contains an unrecognized relative link 'api/core/', it was left as is. Did you mean 'api/core.md'?
    INFO    -  Doc file 'index.md' contains an unrecognized relative link 'api/ops/', it was left as is. Did you mean 'api/ops.md'?
    INFO    -  Documentation built in 2.83 seconds
    BUILD EXIT: 0
    ```
    The two INFO lines are pre-existing prose in `site/index.md` (`[core](api/core/)`
    style links intended for the directory-URL served path, not `.md` filenames) — not
    `--strict` failures (the command has never used `--strict`, matching the original
    GitLab job byte-for-byte), and not new: same two lines would fire against the
    pre-port `mkdocs.yml`. Not in scope to silence (site/** content is out of scope per
    plan §5/§9).
  - **Existence checks:** `public/index.html` (32238 bytes) and `public/api/` (28
    subdirectory entries, one per `nav:` module group) both present.
  - **Falsifier check (mkdocstrings failure downgraded to a warning):** inspected
    `public/api/core/index.html` directly (14405 lines, 296KB) — contains real rendered
    docstring content (class refs like `core.effect_proposal.NotAReversibleWriteError`,
    `core.sealing.SealedCoreEgressError`), not an error/stub page. mkdocstrings/griffe
    rendered cleanly for all ~330 modules locally; no nav-entry break found (Q4's stated
    risk did not materialize this session).
  - Local proof is necessarily partial: cannot exercise GitHub Actions' marketplace-action
    *resolution* from here (bp-015's journal flagged the same gap for `ci.yml` — a bad
    action ref only surfaces on a live run). That live proof is explicitly the
    orchestrator's job at seal (plan §7 Item 12, §12).

- **Item 13 — `mkdocs.yml` re-point + old-URL sweep.** Applied §6(c) verbatim:
  `site_url: https://ascalva.github.io/Mind-Palace/`, `repo_url:
  https://github.com/ascalva/Mind-Palace`, `repo_name: Mind-Palace` (repo_name
  capitalization matches the actual GitHub repo name `Mind-Palace`, confirmed via the
  plan's own Setup-section fact: "Origin is github.com:ascalva/Mind-Palace").
  - **Acceptance — §6(a) build still exits 0 after the edit:** yes (see Item 12's proof
    above; same run covers both items since they're both live in the tree simultaneously).
  - **Acceptance — repo-wide `grep -rn "gitlab.io"` sweep:** re-ran after the edit. Zero
    hits in `mkdocs.yml` (the edit worked). Remaining hits are exactly the ones the plan's
    own Q2 investigation predicted and blessed as historical: the design note's prose
    (`ci-platform-and-runner-strategy.md:204`, describing the URL change itself) and the
    plan's own text (`bp-017/plan.md`, describing what it swept for). Per the invariant
    ("historical artifacts are not retro-edited to the new URL"), left untouched.

**In-flight:** nothing — both items closed to the local-proof boundary this plan asks
of a builder. Not committed yet as of this checkpoint entry (commit follows immediately
after; see next checkpoint for the SHA).

**Next action:** run the full five-part green gate (ruff, mypy ×2 incl. baseline-69
assertion, `ops.type_gate`, pytest), then commit both items (workflow + mkdocs.yml
re-point are one merge-worth of work per the plan, but land as separate logical commits
— pages.yml is new-file/feat, mkdocs.yml re-point is its own fix-shaped change) plus the
finding, then final journal checkpoint (fresh-agent complete) and hand back to the
orchestrator. Plan status stays `in-progress` — orchestrator flips to `complete` after
the live seal proof.

**Open questions:** none new. finding-0045 (below) is routed to the orchestrator, not
parked against either item's acceptance — both items are otherwise unblocked.

**Findings filed:**
- **finding-0045** (`spec-defect`, routed `orchestrator`) — `.gitignore` does not cover
  `public/` (the mkdocs build-output directory); confirmed via `git status --short`
  showing `public/` untracked after a local build. Not in this plan's `write_scope`
  (only `.github/workflows/pages.yml`, `mkdocs.yml`, `docs/findings/**`,
  `docs/build-plans/bp-017/**`) so routed rather than self-resolved. Not a blocker: both
  items proceed regardless; `public/` was `rm -rf`'d after each proof run so the worktree
  stays clean. Re-entry: whoever next has `.gitignore` in scope adds a `public/` line.

**Context-manifest delta:** read beyond the plan's §2 manifest: `.gitignore` (to check
Item-12's build-output-hygiene requirement — confirmed the gap, filed finding-0045);
`docs/design-notes/ci-platform-and-runner-strategy.md` around D5/D7 (context for why
Pages is Plan C and not folded into Plan A); GitHub's REST API for the four pages
actions' latest-release tags and tag lists (to pin current majors per plan Q3 and confirm
each has a moving-major alias, unlike `setup-uv`). Nothing in the manifest proved
irrelevant — all four listed items were used.

## Markers

## 2026-07-12 — orchestrator, at seal verification (live proof)

First live `pages` run (dcfb524/e149592) FAILED at the build step: `uvx` is not
preinstalled on ubuntu-latest runners, and the workflow had no setup-uv step — the plan's
own §6(b) comment listed "checkout → setup uv → build"; the builder omitted it, actionlint
cannot catch a missing tool, and the local acceptance run used the machine's uv. Scrutiny
miss shared by builder and orchestrator; caught exactly where the plan said it would be
(live proof at seal, bp-015 precedent: "actionlint can't prove resolution"). Fix applied
by the orchestrator (one step in `.github/workflows/pages.yml`: `astral-sh/setup-uv@v8.3.2`
with the ci.yml options verbatim). Re-proof: next main push.

## 2026-07-12 — SEAL (orchestrator)

Live proof COMPLETE after the setup-uv fix: pages run green on 1528ffd; site root 200;
`/api/core/` 200 with real rendered docstrings (783 content matches — the Item 12
falsifier cleared, not a stub). The two live-axis pytest timeouts from the builder's
gate re-run UNCONTENDED (bp-016 builder no longer hammering Ollama): **2 passed in
34.49s** — environmental as diagnosed; the gate is fully green. finding-0045 resolved
same session (.gitignore covers public/). Usage into cost.actual: sonnet, 97,449 tokens,
90 tool calls, ~22 min — 0.97x of estimate, the ledger's first near-1x pair. Plan
flipped `complete`. One scrutiny lesson recorded: the missing setup-uv step was in the
plan's own §6(b) comment — both builder and orchestrator-diff-review missed it; the
live-proof-at-seal discipline caught it exactly as designed.

**SEALED by /triage (2026-07-12).** No further narrative entries.
