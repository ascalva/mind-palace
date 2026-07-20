# Runbook — the four-plane principal migration (owner-run)

> **Design:** `docs/design-notes/plane-principals.md` (ratified) · **Plan:** `bp-078` ·
> **Warrant:** `finding-0116` · **Spike:** `finding-0120` (Q9 credential bootstrap).

This migration makes least-privilege **physical**: one macOS user per plane, so the constitution's
bright lines become kernel facts (non-negotiable #2: the core has no network, the edge has no
vault, and no single process is ever both).

| Plane | User | Owns |
|---|---|---|
| human | `ascalva` (your login) | the repo working tree (with group `palace`); nothing private ambiently |
| workflow | `ouroboros-work` | the agents (orchestrator + builders); `exhaust/reports/` |
| core | `ouroboros` | the daemon + the vault (corpus); `data/`; NO off-host network |
| edge | `ouroboros-edge` | network-facing only (forward-provisioned; no live tenant yet) |

Shared group `palace` (members `ascalva`, `ouroboros-work`) exists solely to share **write** on
the repo.

## How to run this

- **Every mutating step below is YOURS.** No agent runs any of it (non-negotiable #3, #5). The
  build delivered only authoring artifacts — the launcher's daemon mode, the daemon plist, the pf
  anchor, the verifier, the ratchets, and this runbook.
- **Each step has a `Verify:` and a `Rollback:` line.** Run the verify before moving on; if it
  fails, run the rollback and stop.
- **Do it at a calm moment** — it interrupts the daemon. Run `mind-palace status` between stages.
- **Placeholders:** `$REPO=/Users/ascalva/mind-palace`, `$MP=~/.mind-palace`. Role-account homes
  are `/var/ouroboros{,-work,-edge}` (config `[planes]`). Pick two free service uids/gids (e.g.
  `550/551/552`, group `560`) — the exact numbers are yours; only the NAMES are load-bearing.
- **The end-state gate:** the whole procedure ends with `uv run scripts/verify_planes.py` **green**
  (run it any time mid-migration — it reports each lane PASS / PENDING / FAIL / SKIP and mutates
  nothing).

> ### ⛔ Ordering guards (getting these wrong wedges the system)
> 1. **Unseal key migrates to `ouroboros` BEFORE you chown the vault** (§7 before §8) — else the
>    daemon cannot unseal the corpus it now owns.
> 2. **Verify the lo0 model-server carve-out is real BEFORE you load the pf block** (§10a before
>    §10b) — else core's calls to the local Ollama server are dropped and it wedges.
> 3. **Install the daemon plist BEFORE `bootstrap system`** (§9a before §9b) — bootstrap of a
>    missing file fails.
> 4. **Grant `/Users/ascalva` traversal BEFORE the daemon runs as `ouroboros`** (§0) — on THIS
>    machine `/Users/ascalva` is `0o750` (no `o+x`), so a role account cannot even reach the repo.

---

## §0 — Precondition: make the repo + vault reachable by role accounts (risk b)

A role account must traverse `/Users/ascalva` to reach `$REPO` and `$MP`. The verifier found this
box's home is `0o750` — **no `o+x`** — so without this step every role account is blocked at the
door.

```sh
stat -f '%Sp %N' /Users/ascalva              # look for the last triad: --- means no o+x
sudo chmod o+x /Users/ascalva                 # grant TRAVERSE only (not read/list) to others
# If you prefer not to widen the home at all, the alternative is a scoped ACL on just the two paths:
#   sudo chmod +a "group:palace allow execute" /Users/ascalva      # (or per-account ACLs)
# or relocate ~/.mind-palace outside the home. `chmod o+x` grants traverse, NOT read — `ls` of the
# home still fails for others; this is the least-effort correct fix.
```

- **Verify:** `sudo -u nobody test -x /Users/ascalva && echo traversable` (once the users exist,
  re-check with `sudo -u ouroboros test -x /Users/ascalva`). Also confirm `o+x` on `/Users`.
- **Rollback:** `sudo chmod o-x /Users/ascalva` (or remove the ACL: `sudo chmod -a "…" …`).

---

## §1 — Create the three role accounts

Hidden role accounts: no login-window presence, real home, shell present (launchd execs), password
disabled (reachable only via `sudo -u`). Repeat for each name with its own uid/home.

```sh
# ouroboros (core) — repeat with 551/ouroboros-work and 552/ouroboros-edge:
sudo sysadminctl -addUser ouroboros -UID 550 -home /var/ouroboros -shell /bin/zsh -roleAccount
# (sysadminctl -roleAccount requires the name to start with _ on some macOS versions; if so use
#  `_ouroboros` etc. and adjust NAMES everywhere — OR create via dscl directly:)
#   sudo dscl . -create /Users/ouroboros UserShell /bin/zsh
#   sudo dscl . -create /Users/ouroboros UniqueID 550
#   sudo dscl . -create /Users/ouroboros PrimaryGroupID 20
#   sudo dscl . -create /Users/ouroboros NFSHomeDirectory /var/ouroboros
#   sudo mkdir -p /var/ouroboros && sudo chown 550:20 /var/ouroboros
sudo dscl . -create /Users/ouroboros IsHidden 1            # keep it out of the login UI
sudo dscl . -delete /Users/ouroboros AuthenticationAuthority 2>/dev/null   # disable password
sudo dscl . -delete /Users/ouroboros passwd 2>/dev/null
```

- **Verify:** `id ouroboros && id ouroboros-work && id ouroboros-edge` (each prints uid/gid).
- **Rollback:** `sudo sysadminctl -deleteUser ouroboros` (repeat per name) — or
  `sudo dscl . -delete /Users/ouroboros`.

---

## §2 — Create the `palace` shared group + members

```sh
sudo dseditgroup -o create -i 560 palace
sudo dseditgroup -o edit -a ascalva        -t user palace
sudo dseditgroup -o edit -a ouroboros-work -t user palace
```

- **Verify:** `dscl . -read /Groups/palace GroupMembership` shows `ascalva ouroboros-work`.
  (`scripts/verify_planes.py` → "group 'palace' members" PASS.)
- **Rollback:** `sudo dseditgroup -o delete palace`.

---

## §3 — Repo shared-repo mechanics (so ascalva + ouroboros-work co-write cleanly)

```sh
cd "$REPO"
git config core.sharedRepository group                 # git writes group-writable objects
sudo chgrp -R palace "$REPO"                            # group the whole tree
sudo chmod -R g+w "$REPO"
sudo find "$REPO" -type d -exec chmod g+s {} +          # setgid dirs: new files inherit group palace
# Put umask 002 in BOTH principals' shells so freshly-created files stay group-writable:
echo 'umask 002' | sudo tee -a /var/ouroboros-work/.zshrc >/dev/null
grep -q 'umask 002' ~/.zshrc || echo 'umask 002' >> ~/.zshrc
```

- **Verify:** `git config core.sharedRepository` → `group`; `stat -f '%Sp' "$REPO/.git"` shows the
  setgid `s` bit and group `palace`.
- **Rollback:** `git config --unset core.sharedRepository`; `sudo find "$REPO" -type d -exec chmod
  g-s {} +`; restore the prior group if needed.

---

## §4 — Repo-local git identity + signing (Q10 — necessary, not tidy)

Under `sudo -u ouroboros-work -H` the agent's HOME changes, so your **global** `~/.gitconfig`
(where signing lives today: `user.signingkey=~/.ssh/id_ed25519.pub`, `gpg.format=ssh`,
`commit.gpgsign=true`) is **not read** — signing would silently break. Pin it **repo-local**
(`.git/config` overrides HOME):

```sh
cd "$REPO"
git config --local user.name  "Alberto Serrano-Calva"
git config --local user.email "ascalva@gmail.com"
git config --local gpg.format ssh
git config --local user.signingkey /Users/ascalva/.ssh/id_ed25519.pub
git config --local commit.gpgsign true
```

**Accepted residual (design decision):** `ouroboros-work` must be able to *read the human's private
signing key* to sign — grant it deliberately. Either make the key file group-readable by `palace`
(least effort) **or** forward an ssh-agent the role session can reach:

```sh
sudo chgrp palace /Users/ascalva/.ssh/id_ed25519 && sudo chmod g+r /Users/ascalva/.ssh/id_ed25519
```

- **Verify:** `git -C "$REPO" config --local --get user.signingkey` is non-empty; make a scratch
  commit as the role user and confirm it is **Verified**:
  `sudo -u ouroboros-work -H git -C "$REPO" commit --allow-empty -m 'signing probe' && git log
  --show-signature -1` → `Good "git" signature`. Delete the probe commit after
  (`git reset --hard HEAD~1`). (`verify_planes.py` → "repo-local git signing" PASS.)
- **Rollback:** `git config --local --remove-section user; git config --local --unset gpg.format;
  git config --local --unset commit.gpgsign`; `sudo chmod g-r /Users/ascalva/.ssh/id_ed25519`.

---

## §5 — ⛔ STOP-GATE: bootstrap + verify Claude Code credentials for `ouroboros-work` (Q9)

**This is the sharpest step and a genuine spike (`finding-0120`).** Claude Code keeps its OAuth
credential in the login **Keychain** (service `Claude Code-credentials`) or, on a Keychain-less
platform, `~/.claude/.credentials.json`; a role account's keychain is **not** auto-unlocked (it
never GUI-logs-in). No agent can settle where the credential lands or whether a locked keychain
breaks the pane relaunch — **only you, by observing it.** Do NOT proceed to daily use until this
gate is green.

```sh
# 1. Authenticate claude ONCE as the role user (its own ~/.claude via -H):
sudo -u ouroboros-work -H claude    # complete the OAuth login in the browser it opens, then /exit
# 2. Create the role user's login keychain if prompted, and set a password you record.
# 3. THE TEST THAT MATTERS — lock the keychain, then relaunch the pane and see if it re-auths:
sudo -u ouroboros-work -H security lock-keychain
sudo -u ouroboros-work -H claude -p 'say ok'    # does it answer, or fail on a locked keychain?
```

**Decide the mitigation from what you observe (preference order, note §3.2 cost 1):**

- **(a) preferred — unlock in the cockpit wrapper.** If the relaunch fails on a locked keychain,
  add BEFORE the `sudo -u ouroboros-work -H claude …` line in `scripts/cockpit.sh` (or a wrapper it
  calls):
  ```sh
  sudo -u ouroboros-work -H security unlock-keychain -p "$OUROBOROS_WORK_KC_PW" \
       /var/ouroboros-work/Library/Keychains/login.keychain-db
  ```
  (keep `$OUROBOROS_WORK_KC_PW` in YOUR keychain, read at cockpit launch — never in the repo, #10.)
- **(b) fallback — skip the keychain entirely.** Set an `apiKeyHelper` in
  `/var/ouroboros-work/.claude/settings.json` (a script that prints a key) or export
  `ANTHROPIC_API_KEY` in the role session. Usage still pools against your one account; only the OS
  identity differs.

- **Verify:** step 3's relaunch answers `ok` with the keychain locked (mitigation applied). Record
  which of (a)/(b) you used in `finding-0120` and flip it to `resolved`.
- **Rollback:** `sudo -u ouroboros-work -H claude /logout`; remove the wrapper line / settings.
- **§10 stop-and-raise:** if NEITHER (a) nor (b) makes the locked-keychain relaunch succeed, **stop
  the migration** and re-open the design via `finding-0120` — do not invent a third path.

---

## §6 — Sudoers: the descending NOPASSWD grant

Lets the cockpit become `ouroboros-work` without a prompt. This is a **descending** grant (the
target is strictly weaker than you), so its blast radius is "ascalva may act as a user with LESS
authority" — the whole point.

```sh
echo 'ascalva ALL=(ouroboros-work) NOPASSWD: ALL' | sudo tee /etc/sudoers.d/mind-palace-work
sudo visudo -cf /etc/sudoers.d/mind-palace-work        # syntax-check (MUST print "parsed OK")
sudo chmod 440 /etc/sudoers.d/mind-palace-work
```

- **Verify:** `sudo -n -u ouroboros-work id` prints ouroboros-work's id with no password prompt.
- **Rollback:** `sudo rm /etc/sudoers.d/mind-palace-work`.

---

## §7 — Migrate Syncthing + the unseal keychain item to `ouroboros` (BEFORE §8)

The vault's Syncthing serves only the vault, so this is a relocation, not a split (confirm you have
no personal shares on it first — if you do, run a second instance under `ouroboros` instead).

```sh
mind-palace stop                                        # drain the current (ascalva) daemon first
# --- Syncthing: stop the ascalva instance; re-create its config under /var/ouroboros and re-add the
#     vault + exhaust shares as the ouroboros user (Syncthing's own migration; carry the device ID).
# --- Unseal key: copy the item into ouroboros's keychain (the daemon, as ouroboros, will read it).
sudo -u ouroboros -H security add-generic-password -U -a mind-palace -s vault-unseal-key -w \
     "$(security find-generic-password -a mind-palace -s vault-unseal-key -w)"
```

- **Verify (no secret printed):** `sudo -u ouroboros -H security find-generic-password -a
  mind-palace -s vault-unseal-key >/dev/null && echo 'unseal item present for ouroboros'`.
  (`verify_planes.py` → "unseal key under ouroboros" is a manual SKIP — this IS that check.)
- **Rollback:** `sudo -u ouroboros -H security delete-generic-password -a mind-palace -s
  vault-unseal-key`; restart the ascalva Syncthing instance.

---

## §8 — chown / chmod every lane to its plane (AFTER §7)

The §3.1 ownership matrix, made real. `exhaust/reports/` goes to **`ouroboros-work`** (the
finding-0116 fix — the orchestrator writes reports); everything else core-emitted stays
`ouroboros`. `data/` (the daemon's runtime sink — logs + runs db) is `ouroboros:palace`.

```sh
sudo chown -R ouroboros:staff  "$MP/vault"       && sudo chmod 700 "$MP/vault"
sudo chown    ouroboros:staff  "$MP/exhaust"     && sudo chmod 755 "$MP/exhaust"
sudo chown -R ouroboros-work:staff "$MP/exhaust/reports" && sudo chmod 755 "$MP/exhaust/reports"
sudo chown -R ouroboros:palace "$REPO/data"      && sudo chmod 755 "$REPO/data"
# data/logs must be ouroboros-writable (StandardOut/Err sink) AND group-readable so the cockpit
# tails palace.out.log as a palace member — the 0755 above already gives group+other read.
```

- **Verify:** `stat -f '%Su:%Sg %Sp %N' "$MP/vault" "$MP/exhaust/reports" "$REPO/data"` matches the
  matrix; from your shell `cat "$MP/vault"/*` is **Permission denied** (the corpus wall).
  (`verify_planes.py` → the lane-owner checks + "vault unreadable from human posture" PASS.)
- **Rollback:** `sudo chown -R ascalva:staff "$MP/vault" "$MP/exhaust" "$REPO/data"` and restore
  prior modes.

---

## §9 — Install the daemon plist + move launchd control to the system domain

### §9a — install the plist (BEFORE bootstrap)

```sh
sudo cp "$REPO/ops/lifecycle/com.mind-palace.palace-daemon.plist" \
        /Library/LaunchDaemons/com.mind-palace.palace.plist
sudo chown root:wheel /Library/LaunchDaemons/com.mind-palace.palace.plist
sudo chmod 644        /Library/LaunchDaemons/com.mind-palace.palace.plist
```

### §9b — retire the gui agent, bootstrap the system daemon

```sh
launchctl bootout gui/$(id -u)/com.mind-palace.palace 2>/dev/null   # retire the ascalva LaunchAgent
sudo launchctl bootstrap system /Library/LaunchDaemons/com.mind-palace.palace.plist
```

- **Verify:** `sudo launchctl print system/com.mind-palace.palace | grep -i username` shows
  `ouroboros`; `mind-palace status` shows a live run; `data/logs/palace.out.log` grows.
  (`verify_planes.py` → "daemon runs as ouroboros" PASS.)
- **Control caveat (risk c):** under KeepAlive, `mind-palace stop` = **restart**; a true stop is
  `sudo launchctl bootout system/com.mind-palace.palace`, and a signal is `sudo launchctl kill
  SIGTERM system/com.mind-palace.palace`.
- **Rollback:** `sudo launchctl bootout system/com.mind-palace.palace`; reinstall + bootstrap the
  gui agent: `cp "$REPO/ops/lifecycle/com.mind-palace.palace.plist" ~/Library/LaunchAgents/ &&
  launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/com.mind-palace.palace.plist`.

---

## §10 — Load the core-egress pf anchor (verify lo0 FIRST)

### §10a — confirm the loopback carve-out is real (BEFORE the block)

The anchor's `pass out quick on lo0` exists so core can speak to the LOCAL Ollama model server. If
core does not actually open a loopback model socket, the carve-out assumption is wrong — do NOT
load the block until this is confirmed.

```sh
sudo lsof -nP -iTCP@127.0.0.1:11434 -a -u ouroboros    # the running daemon's loopback model socket
# expect an ESTABLISHED/lo0 connection to 127.0.0.1:11434 owned by ouroboros while it reasons.
```

- **Verify:** the `lsof` shows a `127.0.0.1:11434` socket owned by `ouroboros`. If it does NOT (core
  opens no loopback socket, or a non-lo0 one) → **§10 stop-and-raise**: file a finding, do not load
  the anchor on a wrong assumption.

### §10b — parse, then load into a named sub-anchor + a persistent loader

```sh
sudo pfctl -n -f "$REPO/ops/network/ouroboros-egress.pf.conf"    # parse-only; now that `ouroboros`
                                                                 # exists, `user ouroboros` resolves
sudo pfctl -a mind-palace/ouroboros -f "$REPO/ops/network/ouroboros-egress.pf.conf"
# make it survive reload/reboot — add to /etc/pf.conf, then reload:
#   anchor "mind-palace/ouroboros"
#   load anchor "mind-palace/ouroboros" from "/Users/ascalva/mind-palace/ops/network/ouroboros-egress.pf.conf"
sudo pfctl -f /etc/pf.conf        # (and `sudo pfctl -e` if pf is disabled)
```

- **Verify:** `sudo pfctl -a mind-palace/ouroboros -sr` shows the lo0 pass BEFORE the ouroboros
  block; core still reasons (its loopback model calls work), and an off-host probe as ouroboros
  fails: `sudo -u ouroboros curl -m5 https://example.com` → **times out / refused**, while
  `sudo -u ouroboros-work curl -m5 https://example.com` still **succeeds** (workflow keeps egress).
  (`verify_planes.py` → "core-egress pf anchor loaded" PASS.)
- **Rollback:** `sudo pfctl -a mind-palace/ouroboros -F rules` (flush just this sub-anchor); remove
  the two `/etc/pf.conf` loader lines and `sudo pfctl -f /etc/pf.conf`.

---

## §11 — Final gate: the verifier must be green

```sh
uv run scripts/verify_planes.py        # exit 0; every lane PASS (only the unseal manual = SKIP)
```

- **Verify:** the verdict reads `VERIFIED (automated checks pass) — 1 owner-manual remain` (or
  `ALL PLANES VERIFIED`), exit 0. Any PENDING/FAIL names the exact lane still to fix — return to
  its §.
- **After migration:** any agent flow that assumed ascalva-ambient access now surfaces as a finding
  — that surfacing is a feature (it maps the sanctioned-interface gaps). The blessing gates
  (`gate-guard`, A8 HEAD-keying) and the import firewall stay as-is; the repo is group-writable by
  design, so an errant agent process can still edit a ratified file at the filesystem level — those
  gates, not the uid, are the enforcement there.

## What this migration deliberately does NOT do (bp-078 §9)

- **The ambassador does not move to `ouroboros-edge`** (deferred, Q13/§11): the network-facing half
  stays wired inside the daemon and `data/handoff` stays core-owned. The `ouroboros-edge` **user is
  created now** (§1) as a forward-provision; its first tenant is a later plan.
- **`ouroboros-work` keeps open dev egress** (the API, git push, uv) — the pf anchor blocks ONLY
  `ouroboros`. Tightening workflow egress to an allowlist is parked (note §5).
