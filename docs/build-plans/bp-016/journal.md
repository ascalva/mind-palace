# BP-016 — Build journal

Alive while the plan is `in-progress`; sealed by `/triage` on completion.
Fresh-agent test (§9): a session given only `plan.md` + this journal + the
write-scope files must continue without re-asking anything already answered.

---

## 2026-07-12 — ORCHESTRATOR RECOVERY: snapshot restructured, scrutinized, gate green (evening session)

**Status:** builder died on the spend limit before its commits; the orchestrator resumed
in this worktree from plan + journal + safety snapshot `60bd857` (resume-beats-restart,
context-economy skill). All items complete; gate green; ready to merge.

**Completed:**
- **Scrutiny (pre-commit, full diff vs `daf9264`): PASS.** Plan §6 checked line-by-line
  against the diff: §6(a) CLI arg surface byte-identical (old shim diffed — docstring-only
  change); §6(b,c) verdict mapping exact, only `success` green; §6(d) endpoints/headers
  verbatim; §6(e) degradation chain all three rows; §6(f) grace in `check()` only,
  `verdict()` pure; §6(g) emission shape exact (action names preserved, `run:<id>`);
  §6(h) Keychain service/account; §6(i) workflow matches the skeleton + two journaled
  additions (`persist-credentials: true`, current action majors); §6(j) plugin swap keeps
  the three disable flags, `package.json` has the `release` script the workflow calls.
  Launcher untouched; nothing outside write_scope (11 files, all in scope); no secrets
  anywhere in the diff. Falsifier evidence accepted from the journal (Item 7 RED demo;
  Item 10 dry-run push-target + version-lineage checks).
- **Snapshot restructured** into the planned logical commits (soft reset of `60bd857`):
  `f5bb116` code (witness + suite + shim, Items 6–8), `2205057` docs (runbook §CI
  witness + finding-0039 + plan/journal, Item 9), `6a4de1c` release trio + workflow
  (Item 10). `node_modules/` removed (never committed).
- **`git merge main` clean** (`4da9c38`; main had moved daf9264→19d884b: bp-017 +
  pages fix + graduations + blessings — zero file overlap with this plan's scope).
- **Five-part gate (worktree, post-merge):** ruff clean · mypy scoped clean (168 files) ·
  **argless mypy = 69 = pinned baseline** · type_gate OK (Tier-2 membership + bare-ignore
  scan) · pytest **1 failed / 850 passed / 8 skipped** — the failure is
  `test_supervisor_dispatches_a_real_job` (live axis), **environmental**: failed 2×
  (~132 s, DONE + empty text) then passed on re-runs in both checkouts (worktree 15.8 s);
  direct probes of the same chat path from this worktree passed warm (2.4 s) and cold
  (92 s). Mechanism (async-unload race in the test's own clean-slate step) recorded as
  **finding-0046** (ftype codebase; `tests/e2e/` is outside this plan's scope). Same
  precedent as bp-017's live-axis timeouts.
- **Usage (context-economy ledger):** builder's actual usage UNKNOWN — it died on the
  org spend limit before reporting; its work spanned Items 6–10 complete with evidence.
  Recovery (restructure + scrutiny + gate) ran orchestrator-side in the 2026-07-12
  evening Fable/xhigh session; recorded qualitatively in the seal.

**Next action:** merge to main (orchestrator sequences), push, live CI proof on the merge
sha, witness live `check` (doubles as Item 9's falsifier replay), then seal + §4
attestation-layer cross-ref (orchestrator's).

---

## 2026-07-12 — Items 6/7/8 built + green; Item 9 written; Item 10 acceptance evidence complete

**Status:** the GitHub witness module + suite are green (29 passed; ruff clean; mypy ops
0; Tier-2 0; argless mypy = 69 = baseline); runbook §CI witness written; release trio
swapped and dry-run acceptance PASSED. The full five-part gate's pytest leg is running;
commits follow it. Coordinator directed a `git merge main` (bp-017 merged, disjoint
scope) — ordered after commit A lands on a clean tree.

**Completed:**
- **Item 6** — `ops/ci_witness.py` rewritten per §6(b,c,d,f,g,h): `run_for` queries
  `ci.yml` by file path (`?head_sha=&per_page=1`, newest-first rows[0]); `verdict()` pure,
  only `completed`+`success` green, no `'manual'`→green analogue (Q4); `check()` grace
  loop (`GRACE_S=300`, `min(GRACE_S, wait_s)`, verdict() untouched); attestation emission
  `pipeline_green|pipeline_red` + `run:<id>` (§6(g)); Keychain `github-api` (§6(h));
  GitLab read-path/rotation/manual-play code fully removed; docstrings rewritten (§4
  banner). CLI shim docstring re-pointed; arg surface byte-identical
  (`check|release <sha>`, `rotate`; same rc semantics).
- **Item 7** — 29-test suite: every §6(c) row asserted (5 pending statuses, success,
  7 red conclusions, absent); grace-loop timing on a simulated clock (absent-within-grace
  polls on; absent-past-grace rc 1 with lag-naming message; grace bounded by wait_s);
  emission shape (`run:314`, action preserved); Keychain service pin; §6(e) degradation
  rows; mocked §6(d) dispatch (URL/method/body/Bearer header). Falsifier demo: RED shown
  against the pre-change module (next entry). No network, no clock, no Keychain touched.
- **Item 8** — `rotate()` = guided-manual print + rc 1; deviation stated in the
  code docstring (Q7 re-verified at build time — see session-start entry); unit test
  pins the message (re-mint route + §6(h) store command; no secret).
- **Item 9** — runbook §CI witness added (docs/runbook.md:789, between §Deploy and
  §One-command lifecycle): what/why, deploy-gate interaction (launcher.py:423-428 check
  + :455-457 release-on-deploy best-effort), absent-grace, PAT mint play, degraded mode,
  rotate-is-manual, release dispatch chain. Acceptance: `grep -n 'CI witness'` hits the
  header; both in-code references (module docstring; rotate()) resolve.
- **Item 10** — gate condition HOLDS (origin=GitHub verified; tag parity PASS —
  session-start entry), so built, not parked:
  - `.github/workflows/release.yml` per §6(i) (+ `persist-credentials: true` for
    commit-back; `pnpm/action-setup@v6` + `actions/setup-node@v6` — current majors
    verified via the GitHub API 2026-07-12; checkout@v7 matches bp-015's ci.yml).
    **actionlint: clean.**
  - `.releaserc.json`: `@semantic-release/gitlab → @semantic-release/github`, same three
    disable flags; assets block untouched. `package.json`: dep swap — **installed
    @semantic-release/github 12.0.9** (`pnpm add -D` pin `^12.0.9`); lockfile
    regenerated (side effect: semantic-release 25.0.2→25.0.5 within `^25.0.2`).
  - **Acceptance run (method + result):** scratch clone of the GitHub origin at main
    (scratchpad, not the repo), release trio copied in, clone origin set to the SSH URL
    (the true origin form), token via env from Keychain (never printed; semantic-release
    masks it as `[secure]`): `pnpm install --frozen-lockfile` → exit 0;
    `pnpm exec semantic-release --dry-run --no-ci` → **exit 0, "Found git tag v1.3.0
    associated with version 1.3.0 on branch main", "The next release version is 1.4.0"**.
    Both falsifiers un-tripped: push target verified = origin
    (`git@github.com:ascalva/Mind-Palace.git`, "Allowed to push"); v1.x lineage honored.
    **Nothing real published** (verified: "Skip v1.4.0 tag creation in dry-run mode" +
    all prepare/publish/success steps skipped; GitHub releases list still empty; origin
    tags still end at v1.3.0). NOTE for a future local dry-run: over https +
    Actions-scoped PAT it fails EGITNOPERMISSION at core verifyAuth (the PAT can't
    git-push — correct least-privilege behavior); the SSH origin form is the one that
    works. The @semantic-release/github plugin itself verified fine with the
    Actions-scoped PAT.
  - Q9 confirm-on-first-live-release (commit-back must not re-trigger `ci`) is carried
    to the owner's first dispatch — noted in release.yml's header comment.
- Mocked-dispatch tests live in the Item 7 suite (test_release_dispatches_workflow,
  test_release_dispatch_404_degrades_to_local_play) — landing with commit A because the
  module rewrite can't keep a GitLab release path (see session-start plan note).

**In-flight:** five-part gate pytest leg running (bare `pytest -q` includes live axes on
this machine). Commit A (code: witness+suite+shim) + docs commits + `git merge main`
+ commit B (release trio + workflow) follow the green tail.

**Next action:** when the gate tail is green: commit A, commit docs, merge main, commit B,
rerun the five-part gate verbatim, final checkpoint. Cleanup owed: `rm -rf node_modules/`
(untracked, NOT gitignored on this branch — pre-merge .gitignore has no node_modules
entry; do not commit it), remove the scratchpad clone.

**Open questions:** none new; finding-0039 routed (orchestrator).

---

## 2026-07-12 — Item 7 falsifier demo: RED shown; finding-0039 filed (live side effect)

**Status:** new GitHub-shape suite written (`tests/unit/test_ci_witness.py`, 24 tests);
run ONCE against the pre-change GitLab module per the falsifier-demo discipline —
**RED: 20 failed, 9 passed** (pytest tail below). The suite pins the GitHub backend,
not "either backend". Item 6 (module rewrite) is next.

**The red, shown (tail of `uv run pytest tests/unit/test_ci_witness.py -q` on the
pre-change module):**

```
FAILED test_verdict_incomplete_is_pending[queued|in_progress|waiting|requested]
FAILED test_verdict_completed_success_is_green        ← GitLab module maps it RED
FAILED test_grace_constant_pinned                      ← no GRACE_S existed
FAILED test_run_for_* (2)                              ← no run_for existed
FAILED test_check_* (5)                                ← absent-immediate, no grace loop
FAILED test_attest_emission_shape                      ← pipeline:<id>, not run:<id>
FAILED test_keychain_reads_github_api_service          ← read gitlab-api
FAILED test_release_* (4)                              ← manual-job play, not dispatch
FAILED test_rotate_is_guided_manual_rc1                ← rc 0: it LIVE-ROTATED (below)
20 failed, 9 passed in 1.59s
```

The 9 passes are the genuinely backend-agnostic rows (verdict(None)→absent; the
red-conclusion rows — GitLab's fall-through also maps GitHub-shaped completed rows red;
the literal "pending" status string).

**finding-0039 filed (discovery → orchestrator):** the demo run executed the OLD
module's `rotate()` live — it rotated the real GitLab PAT (id 25599923, new expiry
2026-08-11; fail-safe ordering completed: verified → stored → read-back OK; no secret
exposed; the `token_rotated` attestation landed in the worktree-local gitignored
`data/attestations.sqlite`, not the live store). Benign outcome, real hazard class:
falsifier-demo runs point suites at pre-change code, which may hold live
side-effecting functions. Routed to the orchestrator with an owner notice.

**Next action:** rewrite `ops/ci_witness.py` per §6(b,c,d,e,f,g,h) — GitHub backend,
grace loop, guided-manual rotate, dispatch-based release — then the suite goes green
and Items 6+7+8 commit together (one logical change: the re-point; journal note in the
session-start entry explains why release()'s dispatch path lands here too).

---

## 2026-07-12 — session start: setup + pre-checks (builder, delegated worktree)

**Status:** plan flipped `ready → in-progress`; all build-time verifications pass;
Item 10's P5 gate condition HOLDS. Beginning Item 7-first (falsifier-demo discipline),
then Item 6.

**Completed:**
- Setup: worktree `/Users/ascalva/mind-palace/.claude/worktrees/agent-a9ab532a788bd1549`
  (branch `worktree-agent-a9ab532a788bd1549`, based on main `daf9264`);
  `.claude/state/active-plan` = bp-016; plan front-matter `status: in-progress`,
  `updated: 2026-07-12`.
- **Owner step 11a verified DONE:** `security find-generic-password -a mind-palace -s github-api`
  (no `-w`; secret never printed) → entry present.
- **Owner step 11b verified DONE:** `git remote -v` → `origin git@github.com:ascalva/Mind-Palace.git`;
  GitLab retained as secondary remote `gitlab git@gitlab.com:ascalva-projects/mind-palace.git`.
- **Q10 tag-parity pre-check: PASS (2026-07-12, this session).** `git ls-remote --tags`
  against both hosts → identical four tags, identical shas:
  `v1.0.0=c828d83f`, `v1.1.0=563bac50`, `v1.2.0=cad8a344`, `v1.3.0=10f5da4f`.
  → **Item 10's gate condition holds in full**; Item 10 proceeds (not parked).
- **Q3 live shape verification (read-only GET, unauthenticated, public repo):**
  `GET /repos/ascalva/Mind-Palace/actions/workflows/ci.yml/runs?head_sha=daf9264…&per_page=1`
  → top-level keys `{total_count, workflow_runs}`; `workflow_runs[0]` carries
  `id=29205421290, name="ci", status="completed", conclusion="success", html_url=…,
  path=".github/workflows/ci.yml"`. Matches §6(d) exactly. `ci` is green at main head.
- **Newest-first sort order verified empirically** (§3 additional-risks item):
  `runs?per_page=5` returns run_number 108→104, created_at strictly descending —
  `workflow_runs[0]` is the newest run; the GitLab `rows[0]` rule ports unchanged.
- **Q7 re-verified at build time (2026-07-12): NO GitHub self-rotation endpoint for
  user fine-grained PATs.** docs.github.com "Endpoints available for fine-grained PATs"
  lists no personal-access-tokens self-service category; the only PAT REST endpoints are
  org-admin management/revocation (`/orgs/{org}/personal-access-tokens`), not
  self-rotation. GitLab's `POST /personal_access_tokens/self/rotate` has no equivalent.
  Sources: docs.github.com/en/rest/authentication/endpoints-available-for-fine-grained-personal-access-tokens;
  docs.github.com/en/rest/orgs/personal-access-tokens;
  github.blog changelog 2024-10-18 (PAT rotation *policies*, not a rotation API).
  → Item 8's guided-manual disposition STANDS; §10 stop-and-raise does NOT fire.
- bp-015 dependency confirmed: `.github/workflows/ci.yml` live and green (run
  29205421290 success on main head daf9264).

**In-flight:** nothing mid-motion; next semantic unit is Item 7's suite.

**Next action:** write the new GitHub-shape test suite (`tests/unit/test_ci_witness.py`,
per §6(c) row-by-row + grace loop + degradation), run it ONCE against the pre-change
GitLab module, journal the RED (falsifier demo), then rewrite `ops/ci_witness.py`
(Item 6) and go green.

**Open questions:** none open. (Q7 closed above; Q10 closed above.)

**Context-manifest delta:** read beyond the manifest: `tests/integration/test_lifecycle.py:300-360`
(confirms the launcher consumes the witness ONLY as an injected subprocess command —
no import coupling; my module rewrite cannot break those tests);
`.github/workflows/ci.yml` (bp-015's, for the type-gate baseline mechanics). Tooling
verified present: node v26.5.0, pnpm 9.15.0 (matches `packageManager`), actionlint 1.7.12.

**Plan notes for the executor of Item 10:** `release()`'s dispatch path + mocked-dispatch
tests will land with the Item 6–8 module commit (the GitLab release path cannot survive
the read-path deletion; §6(e)'s 404-degradation covers the window before `release.yml`
lands). Item 10's own commit carries `release.yml` + the `.releaserc.json`/`package.json`/
lockfile swap + dry-run/actionlint acceptance.

---

## Owner-step ledger (Item 11 — maintained from day one)

| Step | Status | Re-entry |
|---|---|---|
| (a) fine-grained PAT → Keychain `github-api` | **DONE (2026-07-12; re-verified this session, no `-w`)** | — |
| (b) origin re-point → GitHub authoritative (+ tag-parity) | **DONE (2026-07-12; re-verified this session: origin=GitHub, tag parity PASS)** | — |
| (c) mirror **reversal** → GitHub → GitLab (GitLab = downstream mirror) | DONE — owner removed GitLab→GitHub push-mirror (2026-07-12); GitLab now a manual/secondary `gitlab` remote | — |
| (d) secret-scanning + push-protection toggles (GitHub) | **DONE — already on** (owner 2026-07-12) | — |
| (e) retire GitLab **pipeline** | DONE — owner disabled GitLab CI; `.gitlab-ci.yml` tombstoned (deletion parked, mirror-harmless) | note parked #3 |
| (f) retire GitLab **Pages** | DONE — owner removed GitLab Pages; GitHub Pages is up (owner 2026-07-12) | bp-017 builds `pages.yml` |

No criterion in this plan is blocked on any owner step: 11a/11b (the only gating ones)
are done and re-verified.

### Pre-session history (orchestrator entries, 2026-07-11/12)

Step (a) verified DONE (2026-07-12): PAT stored in Keychain (`security find-generic-password
-a mind-palace -s github-api`); an authed `GET /repos/ascalva/Mind-Palace/actions/workflows`
returned HTTP 200 with JSON (`total_count=1`, `.github/workflows/ci.yml`) — the authenticated
polling/dispatch path the witness (bp-016) needs is live.

**GitLab-relationship RULING (owner, 2026-07-12):** GitHub is authoritative; **GitLab becomes a
downstream mirror** ("just another place the current code lives") — the REVERSE of today's
GitLab→GitHub push-mirror. GitLab **pipeline retired** (already tombstoned `when: never`; full
`.gitlab-ci.yml` deletion stays parked — as a pure mirror the tombstoned file is harmless) and
GitLab **Pages retired** (bp-017 stands up GitHub Pages).

**(b) tag-parity PRE-CHECK: PASS (2026-07-12, orchestrator).** GitHub already carries all 4 release
tags `v1.0.0..v1.3.0`, identical to local/GitLab (the push-mirror carried tags). So the origin
re-point is safe for semantic-release continuity. The ordering hazard (mirror pushing a stale ref)
was resolved by sequencing: owner disabled the push-mirror FIRST, then the re-point.

**MIGRATION EXECUTED (2026-07-12).** Owner did the console steps: removed the GitLab→GitHub
push-mirror, disabled GitLab CI, removed GitLab Pages (GitHub Pages now up), and confirmed
GitHub secret-scanning + push-protection already on. Orchestrator then re-pointed local remotes:
`origin` → `git@github.com:ascalva/Mind-Palace.git` (SSH auth OK), GitLab kept as the `gitlab`
remote; `main` tracks `origin/main`; fast-forward push `6f2a9a7..595a1be` succeeded; tags in
parity (`v1.0.0..v1.3.0` both sides). **Pushes now hit GitHub directly — no mirror lag before CI.**
GitLab is a manual secondary (`git push gitlab main` when we want to refresh the copy; no
auto-sync). **STILL OWED for bp-016's build:** Item 10 swaps `@semantic-release/gitlab →
@semantic-release/github` (`.releaserc.json` still targets gitlab) — must land with the witness
re-point; until then no release should be cut (deploy owner-gated, so safe).

SSH key setup is DONE (verified 2026-07-11): `~/.ssh/id_ed25519.pub` registered on GitHub
as both Authentication key (`ssh -T git@github.com` authenticates) and Signing key
(signed history renders Verified on the mirror).

## Markers
