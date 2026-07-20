---
type: build-plan
id: bp-076
status: proposed
design_ref:
  - docs/design-notes/ouroboros-principal.md
contract: builder
write_scope:
  - ops/lifecycle/launcher.py
  - ops/lifecycle/com.mind-palace.palace-daemon.plist
  - tests/integration/test_lifecycle_control.py
  - tests/integration/test_lifecycle.py
  - scripts/verify_ouroboros.py
  - tests/unit/test_ouroboros_migration.py
  - docs/runbooks/ouroboros-migration.md
  - docs/runbook.md
  - config/defaults.toml
session_budget: 1
cost:
  estimate:
    model: opus
    tokens: 220k
  actual: null
depends_on: []
parallelizable_with: []
created: 2026-07-19
updated: 2026-07-19
links:
  - docs/brainstorms/exhaust-and-ingest-sync.md
  - docs/design-notes/exhaust-lane.md
re_entry: null
supersedes: null
superseded_by: null
warrant: null
---

# Build Plan — The Ouroboros principal: LaunchDaemon support, migration runbook, verifier, ratchet

> **Every section below is required.** A section that does not apply is marked
> `N/A — <one-line reason>`, never silently omitted.

## 0. Mode & provenance

Graduated 2026-07-19 from `dn-ouroboros-principal` (ratified by the owner,
`216623b`). This is INFRA + a TRUST-BOUNDARY change: the build delivers only
**authoring** artifacts (code that supports the move, a runbook, a verifier, a
ratchet) — it performs **no** migration step. Every mutating act (create user,
`chown`, launchd/keychain change) is OWNER-RUN from the runbook (§3.5 of the
note; "the model advises, code acts"). Implementation proceeds item-by-item on
owner approval; `proposed → ready` is the owner's keystroke.

## 1. Objective

Give the daemon the ability to run as a system LaunchDaemon under `UserName
ouroboros` (without breaking the current gui-agent path), and ship the runbook,
read-only verifier, and permanent ratchet that let the owner perform and prove
the migration.

## 2. Context manifest

1. `docs/build-plans/bp-076/plan.md` — this plan, whole.
2. `docs/design-notes/ouroboros-principal.md` — the ratified decision;
   §3.1–3.6 are the contract (principal, what-moves, lanes, protocol).
3. `ops/lifecycle/launcher.py` — whole; the launchd control surface. Key spans:
   `_launchd_managed` (`:110-111`, `gui/{getuid}`), `_launchd_cycle`
   (`:117-121`, `bootout`→`cp`→`bootstrap`), the `Launcher` dataclass fields
   (`:313-317`, injectable runner + installed-plist path), `deploy`
   (`:484-491`, drift → cycle). The `gui/{os.getuid()}` domain is threaded
   through all of these — that is what gains a system-domain variant.
4. `ops/lifecycle/com.mind-palace.palace.plist` — the current LaunchAgent plist
   (`RunAtLoad`/`KeepAlive` at `:44-47`); the daemon plist mirrors it + adds
   `UserName`.
5. `tests/integration/test_lifecycle_control.py` — the fake-`launchctl` harness
   that pins the EXACT incantations (`:61` `bootout gui/$UID/label`, `:67`
   `bootstrap gui/$UID …`, `:73-83` cycle order + idempotency). These assert
   the gui-domain surface this plan generalizes — CARRIED in write_scope
   (findings 0071/0072: a retrofit carries its target's surface-pinning tests).
6. `tests/integration/test_lifecycle.py` — the deploy/managed-state tests
   (`:325` monkeypatches `_launchd_managed`); carried for the same reason.
7. `ops/vault/vault-unseal.sh` — reads the unseal key from the login keychain
   (`:31` `security find-generic-password -a mind-palace -s vault-unseal-key
   -w`); the runbook migrates this item to ouroboros's keychain.
8. `config/defaults.toml` + `config/loader.py` — the `[vault]` block (`:42-46`)
   pattern; a new `[ouroboros]` block pins the role home.
9. `docs/runbook.md` — the single growing owner runbook; §"Owner command
   quick-reference" (`:7`) gets a one-line pointer to the new migration doc.

## 3. Investigation & grounding

- **Q1 — how is the launchd domain threaded today?** Hardcoded `gui/{os.getuid()}`
  in `_launchd_managed` (`launcher.py:111`), `_launchd_cycle` (`:118`), and the
  control verbs; the runner is injectable (tests pass a fake,
  `test_lifecycle_control.py:21-39`). So domain is a value to parameterize, not
  a rewrite — a `domain`/`user` field on `Launcher` (default gui-agent, opt to
  system-daemon) that the runner calls interpolate.
- **Q2 — CONTROL MODEL of a system daemon by an ascalva `palace`** (the crux):
  a `system/` LaunchDaemon cannot be `bootout`/`bootstrap`'d by a non-root user.
  DECISION, pinned (consistent with the note's threat model §2 — "sudo is the
  honest escape hatch; owner access is deliberate, elevated, logged"): system-
  domain control commands run via **`sudo launchctl system/<label>`**. The owner
  is admin; sudo is the sanctioned control channel. `palace down/up/deploy` in
  daemon mode prepend `sudo` to the launchctl runner; the injectable runner keeps
  this testable with a fake. If a deeper objection surfaces (e.g. the owner wants
  control to move to `sudo -u ouroboros` entirely), STOP and file a finding —
  do not invent a control model beyond this.
- **Q3 — does the gui-agent path stay byte-identical when unmodified?** It must:
  the parameterization defaults to today's behavior (gui domain, no sudo, the
  existing plist), so an un-migrated machine sees ZERO change. The carried
  lifecycle tests are the proof — they keep asserting the gui incantations for
  the default Launcher, and NEW cases assert the system-daemon incantations for
  the daemon-mode Launcher.
- **Q4 — the ratchet's self-configuring skip/enforce (note §3.5 artifact 3).**
  The vault-read ratchet must SKIP before migration and ENFORCE after, with no
  manual flip. Signal: `stat(vault).st_uid` — if the vault is owned by
  `ouroboros` (migration done), assert `os.access(vault, R_OK) is False` from
  the ascalva test process; else `pytest.skip("pre-migration: vault still
  ascalva-owned")`. The ownership flip IS the migration's acceptance; the skip
  vanishing is the witness. (Mirrors the finding-0105 CI-deselect-until-zero
  shape.)
- **Q5 — keychain migration mechanics.** `vault-unseal.sh:31` reads
  `-a mind-palace -s vault-unseal-key` from the invoking user's keychain. Under
  ouroboros the daemon runs as ouroboros, so the item must exist in ouroboros's
  keychain. The runbook step: `sudo -u ouroboros security add-generic-password
  …` (re-add from the owner's known value), NOT a copy of the ascalva item
  (keychain items don't portably export). The verifier checks the item resolves
  as ouroboros. `vault-unseal.sh` itself needs NO change (it reads "the invoking
  user's" keychain, which becomes ouroboros's when run by the daemon) — confirm
  this by reading it whole; if it hardcodes a user, that is a finding.
- **Q6 — Syncthing relocation.** Out of code scope (owner-run, runbook only):
  stop the ascalva Syncthing, re-home its config under ouroboros, re-pair the
  vault + exhaust shares. The verifier checks the running syncthing's owner is
  ouroboros. NO repo code configures Syncthing.

**Additional risks or questions surfaced during reading:** (a) `deploy`'s
plist-drift check (`launcher.py:487`) compares the installed plist to the repo
plist — in daemon mode the installed path is `/Library/LaunchDaemons/…`, not
`~/Library/LaunchAgents/…`; the `installed_plist` field must follow the domain.
(b) `mind-palace stop`/KeepAlive semantics differ for a system daemon (still
KeepAlive, but `launchctl kill SIGTERM system/…` needs sudo) — the runbook must
state this so the owner isn't surprised.

## 4. Reconciliation

- `ops/lifecycle/launcher.py` — the gui-domain hardcodes → **code correction,
  carried by Item 1** (called out, not slipped in): generalized to a
  domain/user-aware Launcher with the gui-agent as the default, so no existing
  behavior changes silently.
- `docs/runbook.md` — **cross-ref: extension**: a one-line pointer under the
  quick-reference to `docs/runbooks/ouroboros-migration.md`. Nothing corrected.
- `dn-secrets-management-evolution`, `dn-vault-runtime-auth` — the note already
  records that the unseal path's user moves; this plan adds no doc edit there
  (the design note carries the cross-reference).

## 5. Write scope

`ops/lifecycle/launcher.py` (domain/user parameterization),
`ops/lifecycle/com.mind-palace.palace-daemon.plist` (NEW — the system-daemon
variant with `UserName ouroboros`), `tests/integration/test_lifecycle_control.py`
+ `tests/integration/test_lifecycle.py` (carried surface-pinning tests, extended
with daemon-mode cases), `scripts/verify_ouroboros.py` (NEW — read-only
verifier), `tests/unit/test_ouroboros_migration.py` (NEW — the ratchet + the
verifier's unit tests), `docs/runbooks/ouroboros-migration.md` (NEW — the
owner-run runbook), `docs/runbook.md` (one-line pointer), `config/defaults.toml`
(the `[ouroboros]` home block).

Deliberately OUT: the live system (`~/.mind-palace/**`, the real launchd
domains, the real keychain, Syncthing config) — the builder NEVER runs a
migration step; all mutation is the owner's from the runbook. `core/**`,
`config/local.toml`, the foundation denylist as always. `vault-unseal.sh` is
READ (Q5) but not written unless Q5 finds a hardcoded user (then it's a finding
first).

## 6. Interfaces pinned inline

Launchd domains (Q1/Q2):

```
gui-agent (default, today):   gui/$(id -u)/com.mind-palace.palace       # no sudo
system-daemon (ouroboros):    system/com.mind-palace.palace             # sudo launchctl
  plist: /Library/LaunchDaemons/com.mind-palace.palace.plist  (UserName ouroboros)
```

Current control incantations to generalize (`test_lifecycle_control.py:61,67`):

```
bootout    gui/$UID/com.mind-palace.palace
bootstrap  gui/$UID  ~/Library/LaunchAgents/com.mind-palace.palace.plist
# daemon mode (NEW cases assert):
sudo launchctl bootout   system/com.mind-palace.palace
sudo launchctl bootstrap system /Library/LaunchDaemons/com.mind-palace.palace.plist
```

Config block (Item 1 adds):

```toml
[ouroboros]
home = "/var/ouroboros"        # role-account home: its keychain + syncthing config
enabled = false                # false until the owner completes the migration
```

The ratchet (Q4, `test_ouroboros_migration.py`):

```python
vault = Path(get_config()["vault"]["path"]).expanduser()
if vault.stat().st_uid == _uid("ouroboros"):        # migration done
    assert not os.access(vault, os.R_OK)            # ascalva CANNOT read the corpus
else:
    pytest.skip("pre-migration: vault still ascalva-owned")
```

Lane ownership/modes the verifier asserts (note §3.4):

| Path | Owner | Mode |
|---|---|---|
| `~/.mind-palace/vault` | ouroboros | 0700 |
| `~/.mind-palace/exhaust` | ouroboros | 0755 |
| `~/.mind-palace` (parent) | ouroboros:staff | 0755 |

## 7. Items

### Item 1 — domain/user-aware Launcher + the daemon plist + config

- **Objective:** parameterize the launchd domain (gui-agent default ↔ system-
  daemon) behind the injectable runner; add the daemon plist and `[ouroboros]`
  config. Zero behavior change in the default gui path.
- **Files:** `ops/lifecycle/launcher.py`,
  `ops/lifecycle/com.mind-palace.palace-daemon.plist`, `config/defaults.toml`,
  and the carried `tests/integration/test_lifecycle_control.py` +
  `test_lifecycle.py` (extended, not rewritten).
- **Acceptance test:** existing lifecycle tests stay green for the default
  (gui) Launcher (byte-identical incantations); NEW cases assert the daemon
  Launcher emits `sudo launchctl bootout/bootstrap system/<label>` and points
  `installed_plist` at `/Library/LaunchDaemons/…`. Full green gate.
- **Falsifier:** any existing gui-domain lifecycle assertion reddens for the
  DEFAULT Launcher (the parameterization leaked into the default path) — the
  no-silent-change invariant is broken.
- **Invariant(s):** default construction = today's behavior exactly; the
  runner stays injectable (no real launchctl in tests); `deploy`'s drift check
  follows the domain's installed-plist path (surfaced risk (a)).
- **Touches stored data?** No.
- **Parallelizable?** No (foundation for the rest). **Depends on:** none.

### Item 2 — the read-only verifier `scripts/verify_ouroboros.py`

- **Objective:** a script that asserts the migration END-STATE and prints a
  per-check pass/fail, runnable mid-migration; it MUTATES NOTHING.
- **Files:** `scripts/verify_ouroboros.py`, `tests/unit/test_ouroboros_migration.py`.
- **Acceptance test:** against a `tmp_path` fixture modelling both pre- and
  post-migration ownership/modes, each check reports correctly (user exists,
  lane owner+mode per the table, daemon running as ouroboros, unseal item
  resolves as ouroboros, ascalva cannot read the vault). No-core AST check
  (docket precedent). Read-only proven: the script opens nothing for write.
- **Falsifier:** the verifier reports "migrated/OK" against a fixture that is
  NOT fully migrated (a false green) — worse than useless for a trust gate.
- **Invariant(s):** zero mutation; fail-loud per check; exit non-zero if any
  check fails.
- **Touches stored data?** No (fixtures only; against the real system it only
  reads).
- **Parallelizable?** With Item 3. **Depends on:** Item 1 (config/plist paths).

### Item 3 — the vault-read ratchet

- **Objective:** the permanent self-configuring test (Q4) — skip pre-migration,
  enforce "ascalva cannot read the vault" post-migration.
- **Files:** `tests/unit/test_ouroboros_migration.py`.
- **Acceptance test:** on THIS machine today (pre-migration) it SKIPS with the
  reason; the skip→enforce flip is documented as the migration's acceptance
  witness. A fixture forcing ouroboros-owned ownership drives the enforce
  branch's assertion logic.
- **Falsifier:** the test enforces (not skips) pre-migration and reddens the
  suite for everyone before anyone has migrated — the self-configuration is
  wrong.
- **Invariant(s):** the enforce branch runs only when the vault is
  ouroboros-owned; never mutates ownership.
- **Touches stored data?** No.
- **Parallelizable?** With Item 2. **Depends on:** Item 1.

### Item 4 — the migration runbook `docs/runbooks/ouroboros-migration.md`

- **Objective:** the exact OWNER-RUN command sequence, ordered, each step with
  a verification line and a rollback line (note §3.5 artifact 1): create the
  role account → migrate Syncthing → migrate the unseal keychain item → install
  the LaunchDaemon plist → `chown`/`chmod` the lanes → bootout the old gui
  agent → `verify_ouroboros.py`. Gated → validated → reversible (non-negotiable
  5).
- **Files:** `docs/runbooks/ouroboros-migration.md`, `docs/runbook.md` (pointer).
- **Acceptance test:** every step is copy-pasteable and cites the exact command
  (`sysadminctl`/`dscl` for the user, `sudo -u ouroboros security add-generic-
  password …` for the key, `sudo launchctl bootstrap system …`, the `chown`
  lines); each has a paired verify + rollback; the whole procedure ends with
  `verify_ouroboros.py` green. The pointer resolves.
- **Falsifier:** a step mutates without a stated rollback, or the ordering
  would leave the daemon unable to unseal (e.g. chown before the key migrates)
  — an owner following it verbatim gets a broken system.
- **Invariant(s):** NO step is agent-run; the doc only instructs. The KeepAlive
  restart caveat and the sudo-control note (risks (a)/(b)) are stated.
- **Touches stored data?** No (documentation).
- **Parallelizable?** With Items 2/3. **Depends on:** Item 1 (names the plist +
  config it references).

## 8. Math carried explicitly

N/A — no mathematical object implemented (uid/ownership/mode assertions and
launchctl incantations are not mathematical objects).

## 9. Non-goals

- The builder performs NO migration step — no user creation, `chown`, launchd,
  keychain, or Syncthing change. All are owner-run from the runbook.
- No control model beyond `sudo launchctl` for the system domain (Q2); a deeper
  rework is a finding, not this plan.
- No exhaust-lane work (that is bp-075; this plan only assumes the lanes exist).
- No edge-as-third-principal (parked in the note).
- No change to `vault-unseal.sh` unless Q5 finds a hardcoded user (finding first).
- No new pre-hoc enforcement hook — the ratchet + verifier are the proof surface.

## 10. Stop-and-raise conditions

- Q2's control model draws a substantive owner objection (control should move to
  `sudo -u ouroboros`, or sudo-per-command is unacceptable) → finding, park.
- `vault-unseal.sh` (or any read-only-assumed file) turns out to hardcode the
  ascalva user → finding before any edit.
- The gui-agent default path cannot stay byte-identical under parameterization
  → this is a redesign signal; finding, do not ship a silent behavior change.
- A verifier check can only be written by mutating the system → wrong design;
  finding.
- Owner-level question → park with re-entry, continue the rest.

## 11. Parked decisions

| Decision | Default recorded | Rejected alternatives (why) | Re-entry condition |
|---|---|---|---|
| System-daemon control channel | `sudo launchctl system/…` (owner is admin; note §2 sanctions sudo) | `sudo -u ouroboros` full handoff (larger rework, no clear need) | Owner objects to per-command sudo, or wants control fully under ouroboros |
| Syncthing move vs second instance | Move the single instance (serves only the vault) | Second instance under ouroboros (only if the current one carries personal shares) | Owner reports personal shares on the current Syncthing |
| Role-account home location | `/var/ouroboros` | `~ouroboros` under /Users (visible in login UI) | The owner prefers a different hidden-home convention |

## 12. Dependency & ordering summary

Item 1 (foundation: domain-aware launcher + plist + config) → {Item 2 verifier
∥ Item 3 ratchet ∥ Item 4 runbook} (all depend only on Item 1's names/paths).
Blast radius: Item 1 touches load-bearing infra (`launcher.py`) but is guarded
by the carried lifecycle tests and the byte-identical-default invariant; Items
2–4 are read-only/authoring artifacts with no live effect. No stored-data
writes anywhere in the build; the live migration is entirely the owner's,
post-merge, from Item 4's runbook. No cross-plan dependency (bp-075 is
independent; this plan only assumes the lanes it creates will exist).
