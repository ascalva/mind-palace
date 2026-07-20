---
type: build-plan
id: bp-078
status: in-progress
design_ref:
  - docs/design-notes/plane-principals.md
contract: builder
write_scope:
  - ops/lifecycle/launcher.py
  - ops/lifecycle/com.mind-palace.palace-daemon.plist
  - ops/network/ouroboros-egress.pf.conf
  - scripts/cockpit.sh
  - tests/integration/test_lifecycle_control.py
  - tests/integration/test_lifecycle.py
  - scripts/verify_planes.py
  - tests/unit/test_plane_migration.py
  - docs/runbooks/plane-migration.md
  - docs/runbook.md
  - config/defaults.toml
session_budget: 1
cost:
  estimate:
    model: opus
    tokens: 250k
  actual: null
depends_on: []
parallelizable_with: []
created: 2026-07-20
updated: 2026-07-20
links:
  - docs/design-notes/ouroboros-principal.md
  - docs/design-notes/exhaust-lane.md
  - docs/findings/finding-0116.md
  - docs/build-plans/bp-076/plan.md
  - docs/build-plans/bp-076/journal.md
re_entry: null
supersedes: bp-076
superseded_by: null
warrant: finding-0116
---

# Build Plan — The four plane principals: LaunchDaemon support, cockpit sudo launch, egress anchor, migration runbook, verifier, per-plane ratchets

> **Every section below is required.** A section that does not apply is marked
> `N/A — <one-line reason>`, never silently omitted.

## 0. Mode & provenance

Re-graduated 2026-07-20 from `dn-plane-principals` (ratified by the owner,
`215070d`), which **supersedes** `dn-ouroboros-principal` on the warrant of
`finding-0116`. This plan **supersedes bp-076** (three-place supersession,
`dn-supersession-lifecycle` shape): bp-076 was graduated from the now-superseded
two-principal note and would, as written, `chown` `exhaust/reports/`
`ouroboros`-write-only — re-introducing exactly the finding-0116 defect
(workflow can no longer place build reports). bp-076 stays inspectable at
`status: superseded`; its journal carries the 8-point delta this plan discharges.

This is INFRA + a TRUST-BOUNDARY change. The build delivers only **authoring**
artifacts — code that supports the move, an installable pf anchor, a runbook, a
read-only verifier, per-plane ratchets. It performs **no** migration step: every
mutating act (create the four users, `chown`, launchd/keychain/pf/git-config/
Syncthing changes) is OWNER-RUN from the runbook (`dn-plane-principals` §3.5;
non-negotiable #3 "the model advises, code acts"; #5 gated → validated →
reversible). Implementation proceeds item-by-item on owner approval;
`proposed → ready` is the owner's keystroke, never an agent's.

## 1. Objective

Give the owner the tooling to make the four-plane principal model
(`dn-plane-principals` §3.1) real — a domain/user-aware daemon launcher, the
cockpit's `sudo -u ouroboros-work` orchestrator launch, an installable core-egress
pf anchor, an owner-run migration runbook, a read-only verifier, and per-plane
self-configuring ratchets — without any of the tooling itself mutating the live
system.

## 2. Context manifest

Read IN ORDER before any work:

1. `docs/build-plans/bp-078/plan.md` — this plan, whole.
2. `docs/design-notes/plane-principals.md` — the ratified decision; §3.1 (the
   ownership/mode matrix), §3.2 (the cockpit sudo launch + credential/signing
   costs — the crux), §3.4 (non-negotiable #2 as a kernel fact: the pf anchor),
   §4 (consequences: the per-plane artifact triple) are the contract.
3. `docs/design-notes/ouroboros-principal.md` — SUPERSEDED but retained by
   reference; its §2 (threat model), §3.1 (role-account mechanics), §3.2 (the
   daemon moves), §3.5 (execution protocol), §3.6 (sequencing) still hold verbatim
   (`dn-plane-principals` §2 enumerates exactly what survives).
4. `docs/build-plans/bp-076/plan.md` + `journal.md` — the superseded plan and its
   recorded 8-point delta; §3 Q1–Q6 grounding on `launcher.py` is CARRIED intact
   (the launcher parameterization is unchanged by the four-user generalization).
5. `ops/lifecycle/launcher.py` — whole; the launchd control surface. Key spans:
   `_launchd_managed` (`:110-111`, `gui/{getuid}`), `_launchd_cycle` (`:117-121`,
   `bootout`→`cp`→`bootstrap`), `build_components` (`:149-152`, wires the
   ambassador via `CoreInbox(handoff=cfg.interface.handoff_dir)` — the edge seam),
   the `Launcher` dataclass fields (`:313-317`, injectable runner + installed-plist
   path), `deploy` (`:484-491`, drift → cycle). The `gui/{os.getuid()}` domain is
   threaded through all of these — that is what gains a system-domain variant.
6. `ops/lifecycle/com.mind-palace.palace.plist` — the current LaunchAgent plist
   (`StandardOut`/`Err` → `data/logs/…` at `:60,63`); the daemon plist mirrors it
   + adds `UserName ouroboros`.
7. `tests/integration/test_lifecycle_control.py` — the fake-`launchctl` harness
   that pins the EXACT incantations (`:61` `bootout gui/$UID/label`, `:67`
   `bootstrap gui/$UID …`). Asserts the gui-domain surface this plan generalizes —
   CARRIED in write_scope (findings 0071/0072: a retrofit carries its target's
   surface-pinning tests).
8. `tests/integration/test_lifecycle.py` — the deploy/managed-state tests
   (`:325` monkeypatches `_launchd_managed`); carried for the same reason.
9. `scripts/cockpit.sh` — the owner cockpit; `:73` launches the orchestrator as
   `ascalva` (`claude --model 'opus[1m]' --effort medium --permission-mode auto`);
   `:26` tails `data/logs/palace.out.log`; `--dry-run` (`:29`) prints the tmux
   plan without executing — the acceptance surface for the launch-line change.
10. `config/defaults.toml` — the `[vault]` block (`:43-46`, the ingest root —
    config-pinned, why the scanner can't see exhaust), `[exhaust]` (`:57+`), the
    handoff dirs (`:128 data/handoff`, `:155`, `:172`); a new plane-homes block
    pins the three role homes + a per-plane `enabled` flag.
11. `ops/vault/vault-unseal.sh` — reads the unseal key from the invoking user's
    keychain (`:31`); the runbook migrates this item to `ouroboros`'s keychain.
    READ, not written (bp-076 Q5; still holds).
12. `docs/runbook.md` — the single growing owner runbook; its quick-reference
    gets a one-line pointer to the new migration doc.

## 3. Investigation & grounding

Carried intact from bp-076 §3 (launcher parameterization — the four-user
generalization does not touch it): **Q1** (domain hardcoded `gui/{getuid}`,
runner injectable — parameterize, don't rewrite — `launcher.py:111,118`;
`test_lifecycle_control.py:21-39`), **Q2** (system-daemon control via `sudo
launchctl system/<label>`, consistent with the threat model — pinned, a deeper
objection is a stop-and-raise), **Q3** (gui-agent default stays byte-identical),
**Q5** (`vault-unseal.sh:31` reads the invoking user's keychain — no code change,
the item re-adds under `ouroboros`), **Q6** (Syncthing relocation is owner-run,
runbook-only). New grounding the four-user delta requires:

- **Q7 — `exhaust/reports/` ownership (finding-0116 resolution).** The matrix
  (`dn-plane-principals` §3.1) homes `~/.mind-palace/exhaust/reports/` on
  **`ouroboros-work`** (the orchestrator writes reports via
  `scripts/exhaust_report.py`), while the `exhaust/` parent and system-emission
  subdirs stay `ouroboros`. The exhaust root is config-pinned and is NOT an ingest
  root (`config/defaults.toml` `[exhaust]`, separate Syncthing share) — so
  ouroboros-work owning `reports/` does not widen the ingest surface. The runbook
  `chown`s `reports/` to `ouroboros-work`, NOT the whole of `exhaust/`. [GROUNDED
  docs/design-notes/plane-principals.md:113-116; config/defaults.toml `[exhaust]`]
- **Q8 — the cockpit sudo launch (the crux).** `scripts/cockpit.sh:73` launches
  the orchestrator pane as the invoking user (`ascalva`). Per §3.2 it becomes
  `sudo -u ouroboros-work -H claude --model 'opus[1m]' --effort medium
  --permission-mode auto`. `-H` repoints HOME so the service user gets its own
  `~/.claude` (its Anthropic OAuth credential separates from the human's).
  Delegated builders inherit the uid for free (child processes in the shared repo
  worktrees). Sudoers: `ascalva ALL=(ouroboros-work) NOPASSWD: ALL` — a
  *descending* grant. [GROUNDED scripts/cockpit.sh:64-75;
  plane-principals.md:153-194]
- **Q9 — Claude Code's credential storage for a role account (THE SHARPEST item;
  may need a spike).** The code does NOT settle this — Claude Code's OAuth
  credential lives *outside this repo* (the macOS login keychain and/or
  `~/.claude/.credentials.json`, version-dependent), and a role account's keychain
  is not auto-unlocked by GUI login (the account never GUI-logs-in). **What would
  settle it:** authenticate `claude` once as `ouroboros-work` and observe where the
  credential lands and whether the pane relaunch re-reads it with the keychain
  locked. The runbook makes this an explicit BOOTSTRAP-AND-VERIFY step with a
  stop-gate; the mitigation preference order (§3.2 cost 1) is pinned: (a) a
  `security unlock-keychain` line in the cockpit wrapper, else (b) an
  `apiKeyHelper`/env-token path that skips the keychain. This item is a legitimate
  spike candidate — if the empirical bootstrap contradicts both mitigations, STOP
  and file a finding rather than invent a credential path. [INFERENCE +
  code-does-not-settle; plane-principals.md:198-205]
- **Q10 — git identity + signing under `-H` (the accepted residual, made
  concrete).** §3.2 asserts agent commits keep the human's identity + signing key,
  "repo-local, HOME-independent." Grounding shows signing is currently **global**,
  NOT repo-local: `git config --global` yields
  `user.signingkey=/Users/ascalva/.ssh/id_ed25519.pub`, `gpg.format=ssh`,
  `commit.gpgsign=true`; there is NO repo-local signing config. `~/.gitconfig` is
  HOME-dependent, so under `sudo -u ouroboros-work -H` it is **not read** and
  signing would silently break. Therefore the runbook MUST set
  `user.name`/`user.email`/`user.signingkey`/`gpg.format`/`commit.gpgsign` in
  **repo-local** `.git/config` (the note's own prescription — grounding confirms it
  is *necessary*, not merely tidy). The accepted residual is concrete:
  `ouroboros-work` must read the human's private signing key at
  `/Users/ascalva/.ssh/id_ed25519` (or reach it via a running ssh-agent). The
  verifier asserts the repo-local signing config resolves; the runbook grounds the
  key-access path (file mode vs ssh-agent) at migration. [GROUNDED `git config
  --global` on this machine 2026-07-20; plane-principals.md:166-183]
- **Q11 — the core-egress pf anchor.** §3.4 pins
  `block drop out quick proto { tcp udp } user ouroboros` with a
  `pass quick on lo0` carve-out **before** it (core speaks localhost to the
  resident model servers; "sealed" = zero *off-host* egress). This is authored as
  a versioned, reviewable anchor file the owner installs (`pfctl -a
  mind-palace/ouroboros -f …` + a loader anchor in `/etc/pf.conf`); the verifier
  checks the loaded anchor matches. The lo0 carve-out's *necessity* is an
  [INFERENCE] about local model serving — the runbook VERIFIES it against the
  running daemon (does core actually open a localhost socket to a model server?)
  before relying on it. [DERIVED from plane-principals.md:266-273; pf `user`
  matching is TCP/UDP-scoped, both directions]
- **Q12 — `data/` runtime ownership (new conflict the note surfaces).** The daemon
  writes runtime state *inside* the repo tree: `data/logs/*` (four plists sink
  StandardOut/Err there — `palace`, `token-rotate`, `backup`, `vault` — e.g.
  `com.mind-palace.palace.plist:60,63`) and `data/runs.sqlite` (the runs DB,
  `ops/lifecycle/runs.py:10`). The matrix homes `data/` on `ouroboros:palace 0755`
  (the daemon writes; the repo tree around it is `ascalva:palace`). The cockpit
  tails `data/logs/palace.out.log` as a group reader (`cockpit.sh:26`) — group-read
  suffices, no write needed. DECISION pinned: **`chown data/` to `ouroboros:palace`**
  in the runbook (not relocate — relocation would touch four plists and the runs-DB
  path, a larger change with no benefit while `data/` is already the sink). The
  verifier asserts `data/` owner + that a group reader can tail the log.
  [GROUNDED com.mind-palace.palace.plist:60,63; ops/lifecycle/runs.py:10;
  cockpit.sh:26; plane-principals.md:118,124-128]
- **Q13 — the handoff-dir airlock is entangled with the ambassador relocation
  (why edge relocation defers).** §3.1 homes the interface handoff dir on
  `ouroboros-edge:palace-io 2770`, but grounding shows
  `interface.handoff_dir = "data/handoff"` — *inside* the `data/` tree
  (`config/defaults.toml:128`; also `:155 data/handoff/sensing`, `:172
  data/airlock`). The ambassador is wired *inside* the daemon today
  (`launcher.py:149-152`). Splitting the handoff dir to a separate `palace-io`
  group only makes sense once the network-facing half actually moves to a distinct
  `ouroboros-edge` uid. Therefore this plan DEFERS the ambassador relocation +
  the `palace-io`/edge-plist mechanics (§9, §11) and keeps `data/handoff` under the
  `data/` core ownership of Q12; the **`ouroboros-edge` user is still created
  unconditionally** (owner's forward-provision, §3.4). [GROUNDED
  config/defaults.toml:128,155,172; launcher.py:149-152; plane-principals.md:284-289]

**Additional risks or questions surfaced during reading:** (a) `deploy`'s
plist-drift check (`launcher.py:487`) compares installed vs repo plist — in daemon
mode the installed path is `/Library/LaunchDaemons/…`, so `installed_plist` must
follow the domain (carried from bp-076 risk (a)). (b) role accounts must traverse
`/Users/ascalva` to reach `~/.mind-palace`; macOS grants `o+x` on homes by
default, but the runbook must *verify* it (else an ACL grant or relocating
`~/.mind-palace`) — `dn-plane-principals` §3.1's required verification line. (c)
`mind-palace stop`/KeepAlive for a system daemon needs `sudo launchctl kill
SIGTERM system/…` — stated in the runbook so the owner isn't surprised (bp-076
risk (b)).

## 4. Reconciliation

- `ops/lifecycle/launcher.py` — the gui-domain hardcodes (`:111,118`) → **[banner:
  correction, carried by Item 1]**: generalized to a domain/user-aware `Launcher`
  with the gui-agent as the **default** (byte-identical when unmodified), so no
  existing behavior changes silently. Called out, not slipped in.
- `scripts/cockpit.sh:73` — `claude --model 'opus[1m]' …` (as `ascalva`) →
  **[banner: correction, carried by Item 2]**: prefixed with `sudo -u
  ouroboros-work -H`. The change is a launch-identity correction, announced as one;
  `--dry-run` proves the emitted command.
- `docs/runbook.md` — **[cross-ref: extension]**: a one-line pointer under the
  quick-reference to `docs/runbooks/plane-migration.md`. Nothing corrected.
- `dn-secrets-management-evolution`, `dn-vault-runtime-auth` — the note already
  records the unseal path's user moves to `ouroboros`; this plan adds no doc edit
  there (the design note carries the cross-reference).
- `docs/build-plans/bp-076/plan.md` — superseded by THIS plan (three-place,
  front-matter `supersedes: bp-076` / bp-076 `superseded_by: bp-078`, warrant
  `finding-0116`). bp-076 is not edited except the status/superseded_by flip (the
  supersession relation, not a content edit).

## 5. Write scope

Front-matter globs, with per-path rationale:

- `ops/lifecycle/launcher.py` — domain/user parameterization (Item 1; carried
  correction §4).
- `ops/lifecycle/com.mind-palace.palace-daemon.plist` — NEW: the system-daemon
  variant with `UserName ouroboros` (Item 1).
- `ops/network/ouroboros-egress.pf.conf` — NEW: the versioned core-egress pf anchor
  the owner installs (Item 3).
- `scripts/cockpit.sh` — the `sudo -u ouroboros-work -H` launch-line correction
  (Item 2).
- `tests/integration/test_lifecycle_control.py`, `tests/integration/test_lifecycle.py`
  — CARRIED because they pin the exact launchctl surface this plan generalizes
  (findings 0071/0072); extended with daemon-mode cases, not rewritten.
- `scripts/verify_planes.py` — NEW: the read-only four-plane verifier (Item 4).
- `tests/unit/test_plane_migration.py` — NEW: the per-plane ratchets + the
  verifier's unit tests (Items 4/5).
- `docs/runbooks/plane-migration.md` — NEW: the owner-run migration runbook (Item 6).
- `docs/runbook.md` — one-line pointer (Item 6).
- `config/defaults.toml` — the plane-homes block (Item 1).

Deliberately OUT: the live system (`~/.mind-palace/**`, the real launchd domains,
the real keychain, `.git/config`, `/etc/pf.conf`, Syncthing config) — the builder
NEVER runs a migration step; all mutation is the owner's from the runbook. The
ambassador/edge code relocation and the `palace-io`/edge-plist mechanics (Q13,
§9). `core/**`, `agents/**`, `edge/**`, `config/local.toml`, and the foundation
denylist (`CONSTITUTION.md`, `eval/golden/**`, `eval/golden.py`) as always.
`ops/vault/vault-unseal.sh` is READ (Q5) but not written unless it turns out to
hardcode a user (then a finding first).

## 6. Interfaces pinned inline

The four principals and the ownership/mode matrix the verifier asserts
(`dn-plane-principals` §3.1) — copied verbatim:

```
ascalva         — the human (personal login). Owns none of the palace's private data ambiently.
ouroboros-work  — the workflow plane: orchestrator + delegated builders/scribes; repo working tree;
                  owner of ~/.mind-palace/exhaust/reports/.
ouroboros       — the core plane: the reasoning daemon + the vault (corpus). No off-host network.
ouroboros-edge  — the edge plane: network-facing only, never the vault. Created NOW (forward-provision);
                  its first tenant (ambassador relocation) is DEFERRED (Q13, §9).
Shared group: palace (members ascalva, ouroboros-work) — repo write-sharing only.
```

| Path | Owner:group | Mode |
|---|---|---|
| `~/.mind-palace/vault` (ingest) | `ouroboros:staff` | `0700` |
| `~/.mind-palace/exhaust/` (parent) | `ouroboros:staff` | `0755` |
| `~/.mind-palace/exhaust/reports/` | `ouroboros-work:staff` | `0755` |
| `~/.mind-palace/exhaust/<system-emissions>/` | `ouroboros:staff` | `0755` |
| repo working tree (incl. `.claude/worktrees/`) | `ascalva:palace` | `2775` dirs / `664` files |
| repo `data/` (logs, runs db) | `ouroboros:palace` | `0755` |
| network sockets | ouroboros-edge only (workflow keeps dev egress; core blocked by pf) | — |

Cockpit launch line (Q8, `cockpit.sh:73`), gui-default vs the change:

```
# today:
claude --model 'opus[1m]' --effort medium --permission-mode auto
# after (Item 2):
sudo -u ouroboros-work -H claude --model 'opus[1m]' --effort medium --permission-mode auto
```

Launchd domains (Q1/Q2), gui-agent default vs system-daemon:

```
gui-agent (default, today):   gui/$(id -u)/com.mind-palace.palace       # no sudo
system-daemon (ouroboros):    system/com.mind-palace.palace             # sudo launchctl
  plist: /Library/LaunchDaemons/com.mind-palace.palace.plist  (UserName ouroboros)
control incantations the fake-launchctl tests assert:
  bootout    gui/$UID/com.mind-palace.palace                                 # default
  bootstrap  gui/$UID  ~/Library/LaunchAgents/com.mind-palace.palace.plist   # default
  sudo launchctl bootout   system/com.mind-palace.palace                     # daemon (NEW cases)
  sudo launchctl bootstrap system /Library/LaunchDaemons/com.mind-palace.palace.plist
```

The core-egress pf anchor (Q11, `dn-plane-principals` §3.4) — verbatim, the lo0
carve-out BEFORE the block:

```
# ops/network/ouroboros-egress.pf.conf — installed via `pfctl -a mind-palace/ouroboros -f`
pass  out quick on lo0
block drop out quick proto { tcp udp } from any to any user ouroboros
```

Config block (Item 1 adds — three role homes + a per-plane enabled flag):

```toml
[planes]
# Role-account homes (hidden service users; never GUI-login). `enabled` gates the
# per-plane ratchets on/off until the owner completes the migration (self-configuring
# via stat().st_uid is the primary signal; this flag is the coarse master switch).
core_home = "/var/ouroboros"            # ouroboros:      the daemon + vault
work_home = "/var/ouroboros-work"       # ouroboros-work: the orchestrator + builders
edge_home = "/var/ouroboros-edge"       # ouroboros-edge: network-facing (forward-provisioned)
enabled = false                          # false until the owner completes the migration
```

The per-plane ratchet skeleton (Q4 shape, self-configuring — one negative
capability per path, keyed on real ownership, no manual flip):

```python
# tests/unit/test_plane_migration.py
vault = Path(get_config()["vault"]["path"]).expanduser()
if vault.stat().st_uid == _uid("ouroboros"):          # migration done for this path
    assert not os.access(vault, os.R_OK)              # ascalva/test-uid CANNOT read the corpus
else:
    pytest.skip("pre-migration: vault still ascalva-owned")
# repeated per path: exhaust/reports owner==ouroboros-work; data/ owner==ouroboros;
# repo-local signing config resolves; the pf anchor is loaded (core egress refused).
```

## 7. Items

Ordered by blast radius: read-only/foundation → repo-file corrections → authored
system-config → verifier → ratchets → runbook.

### Item 1 — domain/user-aware Launcher + the daemon plist + `[planes]` config

- **Objective:** parameterize the launchd domain (gui-agent default ↔ system-daemon)
  behind the injectable runner; add the daemon plist (`UserName ouroboros`) and the
  `[planes]` config block. Zero behavior change in the default gui path.
- **Files:** `ops/lifecycle/launcher.py`,
  `ops/lifecycle/com.mind-palace.palace-daemon.plist`, `config/defaults.toml`,
  carried `tests/integration/test_lifecycle_control.py` + `test_lifecycle.py`.
- **Acceptance test:** existing lifecycle tests stay green for the default (gui)
  Launcher (byte-identical incantations); NEW cases assert the daemon Launcher emits
  `sudo launchctl bootout/bootstrap system/<label>` and points `installed_plist` at
  `/Library/LaunchDaemons/…`. Full green gate (ruff · import-firewall · mypy ·
  type_gate · pytest).
- **Falsifier:** any existing gui-domain lifecycle assertion reddens for the DEFAULT
  Launcher (parameterization leaked into the default path) — the no-silent-change
  invariant is broken.
- **Invariant(s):** default construction = today's behavior exactly; the runner
  stays injectable (no real `launchctl` in tests); `deploy`'s drift check follows the
  domain's installed-plist path (risk (a)).
- **Touches stored data?** No.
- **Parallelizable?** No (foundation). **Depends on:** none.

### Item 2 — the cockpit sudo launch line

- **Objective:** change `scripts/cockpit.sh:73` to launch the orchestrator as
  `sudo -u ouroboros-work -H claude …`; the human stays `ascalva` in every other
  pane. Daily flow unchanged (still one `./scripts/cockpit.sh`).
- **Files:** `scripts/cockpit.sh`.
- **Acceptance test:** `bash scripts/cockpit.sh --dry-run` prints the tmux plan with
  the orchestrator pane's `send-keys` carrying `sudo -u ouroboros-work -H claude
  --model 'opus[1m]' --effort medium --permission-mode auto`; every other pane's
  command is unchanged; `shellcheck` (if present) clean. NO tmux session is created
  under `--dry-run`.
- **Falsifier:** `--dry-run` shows the sudo prefix on a pane other than the
  orchestrator, or the orchestrator pane lost its model/effort/permission flags, or
  the dry-run actually spawns tmux.
- **Invariant(s):** only the orchestrator pane's launch identity changes; the sudo
  is a *descending* grant (target strictly weaker than `ascalva`); `--dry-run`
  mutates nothing.
- **Touches stored data?** No.
- **Parallelizable?** With Item 3. **Depends on:** none (Item 1's config names are
  referenced by comment only).

### Item 3 — the core-egress pf anchor (authored, owner-installed)

- **Objective:** author `ops/network/ouroboros-egress.pf.conf` — the versioned,
  reviewable anchor enforcing "core has zero off-host egress" (non-negotiable #2 as a
  kernel fact) with the lo0 carve-out ordered BEFORE the block.
- **Files:** `ops/network/ouroboros-egress.pf.conf`.
- **Acceptance test:** the file parses under `pfctl -n -f ops/network/ouroboros-egress.pf.conf`
  (syntax-only, `-n` = no-load); it contains the `pass out quick on lo0` line
  strictly before the `block drop out … user ouroboros` line; the verifier (Item 4)
  reads it as the expected-anchor reference.
- **Falsifier:** the block precedes the lo0 pass (pf is last-match-wins for
  non-`quick`, first-match for `quick` — a misordered `quick` pair would drop
  localhost model-server traffic and wedge core), or `pfctl -n` reports a parse error.
- **Invariant(s):** the anchor blocks only `ouroboros` (core), never `ouroboros-work`
  (workflow keeps dev egress) nor `ouroboros-edge`; the file is inert until the owner
  loads it (authoring only).
- **Touches stored data?** No.
- **Parallelizable?** With Item 2. **Depends on:** none.

### Item 4 — the read-only four-plane verifier `scripts/verify_planes.py`

- **Objective:** a script that asserts the migration END-STATE across all four planes
  and prints a per-check pass/fail, runnable mid-migration; it MUTATES NOTHING.
- **Files:** `scripts/verify_planes.py`, `tests/unit/test_plane_migration.py`.
- **Acceptance test:** against `tmp_path` fixtures modelling pre- and post-migration
  ownership/modes, each check reports correctly: the three role users exist; every
  §3.1 lane has the right owner:group + mode (incl. `exhaust/reports/` ==
  `ouroboros-work`, `data/` == `ouroboros:palace`); the daemon runs as `ouroboros`;
  the unseal item resolves under `ouroboros`; `ascalva` cannot read the vault;
  repo-local git signing config resolves (Q10); the pf anchor is loaded and matches
  `ops/network/ouroboros-egress.pf.conf` (Q11); `/Users/ascalva` is traversable by a
  role account (risk (b)). No-core AST check (docket precedent). Read-only proven:
  the script opens nothing for write. Full green gate.
- **Falsifier:** the verifier reports "migrated/OK" against a fixture that is NOT
  fully migrated (a false green — worse than useless for a trust gate), or any check
  mutates the fixture.
- **Invariant(s):** zero mutation; fail-loud per check; exit non-zero if any check
  fails; runnable by `uv run scripts/verify_planes.py` end-to-end (the finding-0118
  lesson — exercise the CLI form, not just the imported fns).
- **Touches stored data?** No (fixtures only; against the real system it only reads).
- **Parallelizable?** With Item 5. **Depends on:** Item 1 (config/plist paths),
  Item 3 (the anchor it references).

### Item 5 — the per-plane self-configuring ratchets

- **Objective:** the permanent tests (Q4 shape, one per path) — SKIP pre-migration,
  ENFORCE the negative capability post-migration, keyed on real `stat().st_uid`, no
  manual flip: vault unreadable from the test uid; `exhaust/reports/` owned by
  `ouroboros-work`; `data/` owned by `ouroboros`; repo-local signing config present.
- **Files:** `tests/unit/test_plane_migration.py`.
- **Acceptance test:** on THIS machine today (pre-migration) every ratchet SKIPS with
  its reason; a fixture forcing post-migration ownership drives each enforce branch's
  assertion logic; the skip→enforce flip is documented as the migration's acceptance
  witness (finding-0105 CI-deselect-until-zero shape). Green gate: these ratchets skip
  cleanly (they do not redden the suite pre-migration).
- **Falsifier:** any ratchet ENFORCES (not skips) pre-migration and reddens the suite
  for everyone before anyone has migrated — the self-configuration is wrong.
- **Invariant(s):** each enforce branch runs only when its path's `st_uid` matches the
  target principal; never mutates ownership; the egress ratchet degrades gracefully
  where pf state is unreadable without sudo (skip-with-reason, not a false green).
- **Touches stored data?** No.
- **Parallelizable?** With Item 4. **Depends on:** Item 1.

### Item 6 — the migration runbook `docs/runbooks/plane-migration.md`

- **Objective:** the exact OWNER-RUN command sequence, ordered, each step with a
  verification line and a rollback line (§3.5 artifact 1), for all four planes:
  create the three role accounts (`sysadminctl`/`dscl`) → create the `palace` group +
  add members → set repo shared-repo mechanics (`core.sharedRepository=group`, setgid
  dirs, umask 002) → set repo-local git identity/signing (Q10) → **bootstrap-and-
  verify Claude Code credentials for `ouroboros-work`** (Q9, the stop-gate spike
  step) → sudoers `NOPASSWD` descending grant → migrate Syncthing + the unseal
  keychain item to `ouroboros` → `chown`/`chmod` every §3.1 lane (incl. `data/` →
  `ouroboros:palace`, `exhaust/reports/` → `ouroboros-work`) → install the daemon
  plist + `sudo launchctl bootstrap system …` and bootout the gui agent → install the
  pf anchor (`pfctl -a mind-palace/ouroboros -f …` + `/etc/pf.conf` loader) after
  verifying the lo0 model-server necessity → `verify_planes.py` green. Gated →
  validated → reversible (non-negotiable #5).
- **Files:** `docs/runbooks/plane-migration.md`, `docs/runbook.md` (pointer).
- **Acceptance test:** every step is copy-pasteable and cites the exact command; each
  has a paired verify + rollback; ordering never leaves the daemon unable to unseal
  (key migrates before the vault `chown`) nor core wedged (lo0 necessity verified
  before the pf block loads); the credential-bootstrap step is an explicit STOP-gate
  with the §3.2 mitigation preference order; the whole procedure ends with
  `verify_planes.py` green. The `docs/runbook.md` pointer resolves.
- **Falsifier:** a step mutates without a stated rollback; or the ordering would wedge
  the system (chown-before-key, pf-block-before-lo0-verify, launchd-bootstrap-before-
  plist-install); or any step is written as agent-run.
- **Invariant(s):** NO step is agent-run; the doc only instructs. The KeepAlive/sudo
  control caveat (risk (c)), the `/Users/ascalva` traversal check (risk (b)), and the
  git signing-key access path (Q10) are all stated.
- **Touches stored data?** No (documentation).
- **Parallelizable?** With Items 4/5. **Depends on:** Items 1 & 3 (it references the
  plist/config/anchor names).

## 8. Math carried explicitly

N/A — no mathematical object implemented (uid/ownership/mode assertions, launchctl
incantations, and pf rules are not mathematical objects).

## 9. Non-goals

- The builder performs NO migration step — no user/group creation, `chown`,
  launchd/keychain/pf/git-config/Syncthing change. All are owner-run from the runbook.
- **The ambassador/edge code relocation is DEFERRED** (Q13): the network-facing half
  does NOT move to an `ouroboros-edge` LaunchDaemon in this plan, no edge plist is
  authored, and `data/handoff` stays under the `data/` core ownership of Q12. The
  `ouroboros-edge` **user is still created** (forward-provision) and the pf/vault
  walls already exclude it. Re-entry: a follow-on plan when the owner wants the
  relocation (§11).
- No control model beyond `sudo launchctl` for the system domain (Q2); a deeper
  rework is a finding, not this plan.
- No `pf` restriction of `ouroboros-work` egress (workflow keeps open dev egress —
  parked in the note §5).
- No change to `vault-unseal.sh` unless Q5 finds a hardcoded user (finding first).
- No new pre-hoc enforcement hook — the ratchets + verifier are the proof surface.
- No dedicated verified bot identity for the orchestrator's commits (parked, note §5;
  agent commits keep the human's identity per Q10).

## 10. Stop-and-raise conditions

- **Q9 credential bootstrap contradicts both mitigations** (the service user's claude
  credential cannot be made available at pane launch by either a `security
  unlock-keychain` wrapper or an `apiKeyHelper`/env path) → STOP, file a finding; this
  is the designated spike (do not invent a credential path).
- Q2's control model draws a substantive owner objection (control should move to
  `sudo -u ouroboros` entirely) → finding, park.
- `vault-unseal.sh` (or any read-only-assumed file) turns out to hardcode a user →
  finding before any edit.
- The gui-agent default path cannot stay byte-identical under parameterization → a
  redesign signal; finding, do not ship a silent behavior change.
- The lo0 model-server carve-out proves unnecessary or insufficient against the
  running daemon (core opens no localhost socket, or opens a non-lo0 one) → finding;
  the pf anchor must not be authored on a wrong assumption.
- A verifier check can only be written by mutating the system → wrong design; finding.
- Any owner-level question → park the criterion with a re-entry condition, continue
  the rest (never block on the owner).

## 11. Parked decisions

| Decision | Default recorded | Rejected alternatives (why) | Re-entry condition |
|---|---|---|---|
| Ambassador → `ouroboros-edge` code relocation | DEFERRED; the edge USER is still created (forward-provision); `data/handoff` stays core-owned (Q13) | Do it in this plan (crosses into `edge/`/`agents/`, real code movement, entangles the `palace-io` handoff split — sprawls the write_scope across zones) | A follow-on plan when the owner wants edge as a live plane; prerequisite: this plan merged (the users + walls exist) |
| System-daemon control channel | `sudo launchctl system/…` (owner is admin; note §2 sanctions sudo) | `sudo -u ouroboros` full handoff (larger rework, no clear need) | Owner objects to per-command sudo |
| Claude Code credential for `ouroboros-work` | `security unlock-keychain` in the cockpit wrapper (§3.2 cost 1 preference (a)) | `apiKeyHelper`/env-token (preference (b)) — used only if (a) fails at bootstrap | The empirical bootstrap (Q9) contradicts (a); the runbook's stop-gate decides |
| `data/` runtime substrate | `chown data/` → `ouroboros:palace` (already the daemon's sink) | Relocate runtime state into `~ouroboros` (touches four plists + the runs-DB path; no benefit) | The daemon's runtime-state layout changes such that in-repo `data/` no longer fits |
| Git identity for agent commits | Human's identity + key, repo-local config (Q10; note §3.2) | A dedicated verified bot identity (note §5 — closes the signing-key residual but the owner chose their name on the history) | Any of the note-§5 workflow benefits becomes wanted (CI keying on bot author, review policy, the residual felt) |
| Role-account home location | `/var/ouroboros{,-work,-edge}` | `~ouroboros` under `/Users` (visible in the login UI) | The owner prefers a different hidden-home convention |
| Syncthing move vs second instance | Move the single instance (serves only the vault) | Second instance under `ouroboros` (only if personal shares present) | Owner reports personal shares on the current Syncthing |

## 12. Dependency & ordering summary

Item 1 (foundation: domain-aware launcher + daemon plist + `[planes]` config) →
{ Item 2 cockpit launch ∥ Item 3 pf anchor } (independent of Item 1's code, may run
alongside) → Item 4 verifier (needs Item 1's config/plist names + Item 3's anchor) ∥
Item 5 ratchets (needs Item 1) → Item 6 runbook (references Items 1 & 3's
names/paths). Blast radius: Items 1–3 touch repo files (guarded by the carried
lifecycle tests, the byte-identical-default invariant, and `pfctl -n` parse-only);
Items 4–6 are read-only/authoring artifacts with no live effect. **No stored-data
writes anywhere in the build.** The live four-plane migration is entirely the
owner's, post-merge, from Item 6's runbook. No cross-plan dependency (bp-075 exhaust
lane is already merged; this plan assumes those lanes exist and only re-homes the
ownership of `exhaust/reports/`).
