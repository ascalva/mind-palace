---
type: finding
id: finding-0122
status: open
created: 2026-07-20
updated: 2026-07-20
links:
  - docs/runbooks/plane-migration.md               # §4 — amended by this finding
  - docs/build-plans/bp-078/plan.md                # Q10 (§3), the signing residual
  - docs/design-notes/plane-principals.md          # §3.2 the accepted signing-key residual
  - docs/findings/finding-0120.md                  # sibling: the same "secret for the role session" class
re_entry: null
ftype: spec-defect
origin_plan: bp-078
route: orchestrator
resolution: null
---

# Runbook §4 (git signing) shipped incomplete — the key-access chain needs `.ssh` traversal + `safe.directory`, and a passphrase-protected key can't sign unattended

## What
Discovered while running the live plane migration (2026-07-20, owner at the keyboard, orchestrator
verifying each step). bp-078's `plane-migration.md` §4 grants `ouroboros-work` read of the human's
signing key with a single `chgrp palace + g+r` on the key file — but the actual key-access chain
needs **three** grants, and the missing two each fail the verify with a misleading error:

1. **`~/.ssh` directory traversal.** `.ssh` was `0700`, so even with the key group-readable,
   `ouroboros-work` could not traverse into `.ssh`. Symptom: `git commit` →
   `Couldn't load public key /Users/ascalva/.ssh/id_ed25519.pub: No such file or directory` (a
   traverse EACCES surfacing as ENOENT, not a real missing file). Fix: `chgrp palace ~/.ssh &&
   chmod g+x ~/.ssh` (g+x only — traverse, not list; other keys stay `600`/invisible).
2. **`safe.directory`.** git refuses a repo owned by a *different uid* (CVE-2022-24765);
   `core.sharedRepository=group` does **not** satisfy it (that check is uid-based, not group-based).
   Symptom: `dubious ownership`. Fix: `git config --global --add safe.directory <repo>` for
   `ouroboros-work`.
3. **Passphrase → unattended signing.** With (1)+(2) fixed, signing succeeded and produced a
   correctly **Verified** commit (`Good "git" signature for ascalva@gmail.com`, authored as the
   human) — but only after the human **typed the key passphrase**. The autonomous orchestrator
   (running as `ouroboros-work`) cannot type a passphrase on every commit, so signing is not yet
   unattended.

Minor: the §4 verify makes its probe commit on `main` then `reset --hard`s it — which trips the
post-commit code-sensor (a phantom ledger row) and momentarily moves `main`. The probe should run on
a throwaway branch.

## Why it matters
§4's own verify would have *caught* each gap (the safety net worked — this is not a silent defect),
but an owner following the runbook verbatim hits three consecutive misleading failures on the
single fiddliest step. Worse, item 3 is not a runbook-text gap but a **design-completeness** one: the
whole point of the plane split is that agents commit *unattended* as `ouroboros-work` with the
human's Verified identity — a per-commit passphrase prompt defeats that. It is the same class as
`finding-0120` (a secret the non-interactive role session must obtain at launch), for a different
secret (the SSH signing key vs the Claude OAuth credential).

## Resolution / re-entry
- **Runbook §4 amended** (this commit): the three grants pinned with their symptoms, the
  passphrase/unattended-signing note (deferred to the cockpit wrapper), and probe-off-main guidance.
  The **doc-completeness** half is thereby resolved.
- **The unattended-signing half stays open**, converging with `finding-0120` on the cockpit wrapper:
  the wrapper starts an ssh-agent for `ouroboros-work` and `ssh-add`s the signing key once at launch
  (passphrase from its keychain via `--apple-use-keychain`), so SSH signing goes through the agent
  silently. **Re-entry:** the owner builds/《decides》the cockpit wrapper at §5 (the credential
  STOP-gate) — solve claude-credential and ssh-key-passphrase in the ONE wrapper. Flip to `resolved`
  when the wrapper signs a commit unattended.

## Routing
`spec-defect` → orchestrator. The runbook text fix is in-repo (done). The unattended-signing design
piece is owner-run at §5 alongside `finding-0120`; both are the "make the role session's secrets
available at launch" problem, solved once in the cockpit wrapper.
