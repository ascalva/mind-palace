---
type: finding
id: finding-0123
status: routed
created: 2026-07-20
updated: 2026-07-26
links:
  - docs/design-notes/plane-principals.md          # §3.2 — grounded the workflow cred, not the daemon's
  - docs/design-notes/vault-runtime-auth.md         # the Vault the daemon unseals
  - docs/design-notes/secrets-management-evolution.md
  - ops/vault/vault-unseal.sh                        # :31 reads vault-unseal-key from the keychain
  - ops/vault/com.mind-palace.vault.plist           # the LaunchAgent that invokes it
  - ops/lifecycle/com.mind-palace.palace-daemon.plist  # :27 lists the (unsatisfiable) precondition
  - docs/runbooks/plane-migration.md               # §7 — blocked by this
  - docs/findings/finding-0120.md                  # the same keychain-less-role-account reality (workflow half)
re_entry: >
  A design pass decides the headless-daemon secret-bootstrap mechanism (System keychain w/ ACL, an
  ouroboros-only file, or a hybrid where Vault stays ascalva-operated), then §7–§11 re-graduate
  against it. Blocking prerequisite: that decision (likely a FABLE design pass — touches the secrets
  architecture + the sacred vault).
ftype: spec-defect
origin_plan: bp-078
route: orchestrator
resolution: routed → owner (oq-0041); the design pass happened but its note is still draft, so §7–§11 cannot re-graduate
---

# The `ouroboros` daemon's secret bootstrap is keychain-based — incompatible with a headless role-account LaunchDaemon; §7–§11 (the core-plane move) are blocked

> **Triage 2026-07-26 (session-52) — batched to `oq-0041`.** Still blocked, unchanged in substance.
> The design pass *did* happen — `dn-headless-daemon-secret-bootstrap` exists with `warrant:` this
> finding — but it is **`status: draft`**, so `/graduate` refuses it and runbook §7–§11 (the core
> plane) cannot re-graduate. The mechanism it must replace is untouched:
> `ops/vault/vault-unseal.sh:31` still reads the unseal key from a *login* keychain via
> `security find-generic-password`, and the daemon plist still lists that migration as a precondition
> a role account cannot meet.
> **Sequencing:** finding-0125's Opus-residual gates this ratification — answer `oq-0042` first.

## What
Surfaced mid-migration (2026-07-20, right after `finding-0120`). Runbook §7 tells the migration to
place the Vault **unseal key** in `ouroboros`'s keychain, so the daemon (as a LaunchDaemon under
`UserName ouroboros`) can auto-unseal Vault at boot. But:

- **A role account has no login keychain** (finding-0120) — `security add-generic-password` as
  `ouroboros` hits the same "a keychain cannot be found to store" wall.
- **A LaunchDaemon starts at boot, headless** — no GUI login to unlock a keychain, and **no wrapper
  to inject a secret via env** (the finding-0120 fix for the *workflow* agent relies on the cockpit
  wrapper exporting `CLAUDE_CODE_OAUTH_TOKEN`; launchd offers no such seam for the daemon).

This is not one secret: `ops/vault/vault-unseal.sh:31` reads `vault-unseal-key`; the same
`security find-generic-password -a mind-palace -s <svc>` pattern feeds `vault-root-token`
(`setup_policies.sh`), `github-api` (`ci_witness.py:86`), and the backup keys (`backup.sh:13`) — the
daemon's entire secret bootstrap is login-keychain-based. `com.mind-palace.palace-daemon.plist:27`
even lists "the unseal keychain item … migrated to `ouroboros`" as a **precondition** it cannot meet.

## Why it matters
§7–§9 (move the daemon + Vault to `ouroboros`), and therefore §8 (chown the corpus vault to
`ouroboros:0700`) and §10–§11, **cannot complete as written**. Running them anyway strands the
daemon unable to unseal Vault — the secrets backend (and everything gated on it) down. This is the
**core-plane** half of the migration; it is the part that delivers "even an ascalva-login process
can't read the corpus" and "core has no network."

## Root cause
`dn-plane-principals` §3.2 grounded the **workflow** credential (claude) — for which a
cockpit-launched wrapper can inject an env var — but assumed the daemon's keychain item simply
"migrates," without grounding that against the keychain-less-role-account reality that
`finding-0120` then proved. The two credential problems look alike but differ structurally:
**wrapper-launched (workflow) vs launchd-launched-at-boot (daemon)**. Only the first is solved.

## Options (a design decision, not an inline fix)
1. **System keychain** (`/Library/Keychains/System.keychain`) — auto-unlocked at boot, daemon-
   reachable; add the items there with an ACL granting `ouroboros`, and add System to its search
   list (`security find-generic-password -a … -s … /Library/Keychains/System.keychain`). Most
   keychain-native; needs testing that a non-root `ouroboros` daemon can read it.
2. **An `ouroboros`-only file** (e.g. `/var/ouroboros/.vault-unseal`, `0600 ouroboros`) — simplest,
   but a plaintext secret on disk (tension with non-negotiable #10 "secrets in Keychain/env only").
3. **Hybrid** — the Vault + its unseal LaunchAgent stay **ascalva-operated** (keychain works,
   GUI-unlocked); the palace daemon moves to `ouroboros` and reaches Vault over loopback with a
   token. Shrinks the isolation win (Vault runs in the ascalva session) but sidesteps the boot
   secret entirely. The token bootstrap needs the same treatment.
4. **A boot-time unseal helper** (a privileged one-shot that unseals then drops).

Each trades off security, complexity, and how much of the core-plane isolation survives → a small,
deliberate design pass, likely **FABLE** (touches the secrets architecture and the sacred vault).

## Recommendation — SPLIT the migration (owner principle: mechanical move ≠ trust-boundary change)
- **Land the WORKFLOW plane now** (§1–§6, done + safe, + the cockpit wrapper): agents run as the
  constrained `ouroboros-work`, isolated from the human's personal files/keychain. This is the bulk
  of the day-to-day value and is fully reversible.
- **PARK the CORE plane** (§7–§11: daemon → `ouroboros` LaunchDaemon, vault `0700`, pf egress) behind
  the design pass above. `ouroboros` + `ouroboros-edge` users already exist (forward-provisioned); no
  work is lost.

## Routing
`spec-defect` / direction → orchestrator; needs an owner decision + a design pass (amends
`dn-plane-principals` §3.2; touches `dn-vault-runtime-auth` / `dn-secrets-management-evolution`).
Pre-task FABLE flag when the design pass is run.
