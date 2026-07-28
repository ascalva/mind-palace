---
type: finding
id: finding-0276
status: open
created: 2026-07-27
updated: 2026-07-27
links:
  - docs/brainstorms/the-typed-workflow-registry.md
  - docs/design-notes/dn-typed-workflow-registry.md
  - docs/findings/finding-0275.md
  - docs/brainstorms/blessing-auth-gate.md
ftype: spec-defect
origin_plan: orchestrator
route: orchestrator
resolution: null
---

# "Machine merges are never allowed" cannot be enforced on GitHub today: the agent holds the owner's own identity and admin credential, and merge is not a separable permission

## What

The owner ruled (2026-07-27) that build branches never merge locally — they become PRs, and he
merges from GitHub — and asked that the agent's credentials be scoped so API merges are impossible.
Three facts measured this pass say the obvious implementation does not work.

**1. The agent's credential is the owner's, and it is admin.**

```
gh auth status  → Token scopes: 'admin:public_key', 'gist', 'read:org', 'repo'
gh api repos/:owner/:repo --jq .permissions
  → {"admin":true,"maintain":true,"pull":true,"push":true,"triage":true}
```

Classic `repo` scope plus repo **admin**: the agent can merge, force-push `main`, alter or delete
branch protection, and delete the repository.

**2. ⚑ Merge is not a separable permission.** For fine-grained PATs, `PUT /repos/{owner}/{repo}/
pulls/{pull_number}/merge` sits under **`Contents: write`** — the *same* permission required to push
a branch or create a commit. `Pull requests: write` governs *opening* a PR, not merging it.

⇒ **A token that can push builder branches can necessarily merge them.** Scoping the credential
cannot, by itself, remove the merge capability without also removing the agent's ability to do its
job. `[GROUNDED — docs.github.com, "Permissions required for fine-grained personal access tokens",
fetched 2026-07-27.]`

**3. ⚑⚑ The agent is indistinguishable from the owner.**

```
gh api user --jq .login        → ascalva
gh pr view 1 --jq .author.login → ascalva
git config user.name           → Alberto Serrano-Calva
```

Every identity-based control is therefore vacuous or actively harmful:

| control | outcome today |
|---|---|
| require 1 approving review | ⚑ the owner cannot approve his own PR ⇒ **deadlock**, not protection |
| restrict merge to the owner | the agent **is** the owner ⇒ no constraint |
| bypass-actor lists | same — one identity on both sides of the line |

## Why it matters

**1. It is the same defect the whole evening was about.** A control that cannot distinguish the
actor it constrains from the actor it protects is not a control. This is
[[the-unchecked-claim]]'s shape again — the check lives inside the thing being checked — and
`blessing-auth-gate` already recorded the git half of it: *"git authorship is the owner's name on
agent commits too."* This finding is that observation reaching its consequence.

**2. Today the rule rests on agent discipline**, which `finding-0275` just finished demonstrating is
not a mechanism. `main` has **no protection at all** (`gh api .../branches/main/protection` → 404).

**3. ⚑ It is cheap to fix and needs no build.** Unlike the registry, this is available immediately —
which is exactly why it should not be left as convention while the registry is built.

## The remedy — three parts, and each closes the others' gap

⚑ **None of the three is sufficient alone. This is a partition, not a stack.**

1. ⚑ **A separate identity for the agent** — a machine account or a GitHub App installation. **This
   is the prerequisite**; without it (2) deadlocks and (3) is vacuous. It also fixes PR authorship,
   so the owner reviewing an agent's PR is two parties rather than one.
2. **A ruleset on `main`**: require a pull request, require ≥1 approving review. This is what
   actually blocks the merge endpoint — since (per fact 2) the token permission cannot. With (1) in
   place the agent cannot approve its own PR, so the owner's approval becomes the seal.
3. **A scoped credential for that identity**: `Contents: write` + `Pull requests: write` +
   `Metadata: read`, and ⚑ **no `Administration`** — so the agent cannot remove the ruleset that
   constrains it. Without this, (2) is theatre: an admin token deletes the protection and merges.

| omit | what breaks |
|---|---|
| (1) identity | approval deadlocks; every actor-based rule is vacuous |
| (2) ruleset | merge stays possible — `Contents: write` implies it |
| (3) scoping | the agent can delete the rule that binds it |

## ⚑ Ordering, and the bootstrap irony

The constraint must be installed **using the over-privileged credential**, because afterwards the
credential cannot install it. ⇒ Ruleset first (while admin is available), identity and token swap
second. Reversing the order strands the work.

`[INFERENCE]` Whether a GitHub ruleset can require review for *merges* while still permitting the
owner's own direct commits to `main` — the narrowing the owner stated (*"local main-merges do not
happen locally"*, orchestrator doc-commits unaffected) — should be **verified before it is promised**.
If it cannot express that split, the choice between protecting `main` fully and keeping direct
doc-commits is an owner ruling, not an implementation detail.

## ⚑⚑ TWO ESCALATIONS DISCOVERED WHILE SPECIFYING THE REMEDY

### 1. Merge triggers deploy ⇒ merge capability IS deploy capability

> Owner, 2026-07-27: *"which is also why aws deployments happen on merge from github"*

This simplifies the ceremony — deploy stops being a second act (`mind-palace deploy`, the standing
"ONE owner-in-loop gate") and becomes a consequence of the merge already authorized. **One seal, not
two.**

⚑ **And it raises the stakes on every line above.** An agent that can merge can now *deploy to
production*. The gap this finding describes stops being "could land unreviewed code" and becomes
"could ship to AWS." The identity separation is no longer hygiene.

### 2. ⚑ THE PAT DOES NOT CONSTRAIN `git push` AT ALL — the protocol is SSH

```
gh auth status → Git operations protocol: ssh
```

`git push` authenticates with the **SSH key**, not the PAT. ⇒ Scoping the fine-grained token
constrains `gh` (the REST API) and **nothing about a local merge followed by `git push origin main`**
— which is precisely the act the owner's rule forbids.

⇒ ⚑ **The credential scoping alone constrains almost nothing that matters.** The **server-side
ruleset is the load-bearing control**, because it applies regardless of protocol, credential, or
client. The PAT reduces blast radius (no admin ⇒ cannot delete the ruleset); it does not implement
the rule.

⚑ Recorded prominently because the reverse belief — "I scoped the token, therefore merges are
blocked" — is a false sense of security, and this repo's own standard says a control is real only
when something proves it. Here the token proves nothing about `git push`.

## Re-entry condition

The GitHub-side setup session — owner acts, no build. It composes with, and does not wait on, the
identity-foundation ceremony (`docs/brainstorms/the-identity-foundation.md`): the YubiKeys that
notarize design transitions are unrelated to the GitHub identity that opens PRs, and either can land
first.

## Routing

`spec-defect` → **orchestrator** to specify, **owner** to execute. Parts (1) and (3) create
credentials and are owner-only by nature; part (2) is a repo setting the agent could apply with its
current admin, but ⚑ should not apply unilaterally — it changes how the owner's own pushes behave.
