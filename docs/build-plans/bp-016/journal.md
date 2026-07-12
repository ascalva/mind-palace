# BP-016 — Build journal

Alive while the plan is `in-progress`; sealed by `/triage` on completion.
Fresh-agent test (§9): a session given only `plan.md` + this journal + the
write-scope files must continue without re-asking anything already answered.

---

## Markers

## Owner-step ledger (Item 11 — maintained from day one)

| Step | Status | Re-entry |
|---|---|---|
| (a) fine-grained PAT → Keychain `github-api` | DONE (2026-07-12) | authenticated polling + dispatch |
| (b) origin re-point → GitHub authoritative (+ tag-parity check) | RULED, tags PASS; local re-point PENDING owner-console step first | gates Item 10 |
| (c) mirror **reversal** → GitHub → GitLab (GitLab = downstream mirror) | RULED (owner 2026-07-12) | — |
| (d) secret-scanning + push-protection toggles (GitHub) | OWED | — (any time) |
| (e) retire GitLab **pipeline** | tombstoned+dead; deletion parked (mirror-harmless) | note parked #3 / D4 |
| (f) retire GitLab **Pages** | RULED — owner-console + bp-017 builds GitHub Pages | bp-017 |

Step (a) verified DONE (2026-07-12): PAT stored in Keychain (`security find-generic-password
-a mind-palace -s github-api`); an authed `GET /repos/ascalva/Mind-Palace/actions/workflows`
returned HTTP 200 with JSON (`total_count=1`, `.github/workflows/ci.yml`) — the authenticated
polling/dispatch path the witness (bp-016) needs is live.

**GitLab-relationship RULING (owner, 2026-07-12):** GitHub is authoritative; **GitLab becomes a
downstream mirror** ("just another place the current code lives") — the REVERSE of today's
GitLab→GitHub push-mirror. GitLab **pipeline retired** (already tombstoned `when: never`; full
`.gitlab-ci.yml` deletion stays parked — as a pure mirror the tombstoned file is harmless) and
GitLab **Pages retired** (bp-017 stands up GitHub Pages).

**(b) tag-parity PRE-CHECK: PASS (2026-07-12).** GitHub already carries all 4 release tags
`v1.0.0..v1.3.0`, identical to local/GitLab (the push-mirror carried tags). So the origin re-point
is safe for semantic-release continuity. **Ordering hazard (why the local re-point is not done
yet):** today's GitLab→GitHub **push-mirror is still live**; re-pointing local `origin` to GitHub
before the owner disables that push-mirror risks GitLab pushing a stale ref at GitHub. Safe
sequence: (1) owner disables the GitLab→GitHub push-mirror + sets up the reverse (or treats GitLab
as a manual secondary); (2) orchestrator `git remote` re-point (`origin`→GitHub, keep GitLab as a
`gitlab` remote) — reversible, tags already parity; (3) bp-016 Item 10 swaps
`@semantic-release/gitlab → @semantic-release/github` (must be atomic-ish with the re-point — no
release cut in between; deploy is owner-gated so none is imminent).

SSH key setup is DONE (verified 2026-07-11): `~/.ssh/id_ed25519.pub` registered on GitHub
as both Authentication key (`ssh -T git@github.com` authenticates) and Signing key
(signed history renders Verified on the mirror).

SSH key setup is DONE (verified 2026-07-11): `~/.ssh/id_ed25519.pub` registered on GitHub
as both Authentication key (`ssh -T git@github.com` authenticates) and Signing key
(signed history renders Verified on the mirror).
