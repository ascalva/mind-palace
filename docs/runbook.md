# Runbook

Operational notes for running and verifying the mind-palace. Grows per phase.

---

## ⭐ Owner command quick-reference (deferred / operational steps)

Everything the builder leaves for you to run, in dependency order. Detailed sections are linked.

**`mind-palace` is on your PATH** (2026-06-30) — a shim at `/opt/homebrew/bin/mind-palace` (symlink
→ `bin/mind-palace` in the repo) resolves the repo root from its own location and dispatches to
**every** owner-facing script under `scripts/` — `mind-palace <verb> [args...]` works from any
directory, no `cd` and no remembering which file does what. Run `mind-palace help` for the full verb
list (it's the same list as this section). Adding a new script later = one new `case` line in
`bin/mind-palace`.

```sh
# --- DAY-TO-DAY (from anywhere) ----------------------------------------------------------------
mind-palace start              # run the whole system (preflight + supervise)
mind-palace status             # health checklist + recent runs (commit-pinned)
mind-palace stop                # graceful drain (under launchd KeepAlive this = RESTART)
mind-palace deploy              # promotion gate: cycle the ALWAYS-ON run onto HEAD (see below)
mind-palace talk                 # talk to it locally (LIVE; --offline = no-Ollama demo)
#   Remote dashboard + chat from your phone: set [monitor] enabled=true + host=<tailscale-ip>, then
#   `mind-palace start` spawns it → http://<tailscale-ip>:8787  (see "Remote dashboard + chat" below)

# --- FRESH START (done 2026-06-29; re-runnable) — see "Fresh start" below ---------------------
launchctl bootout gui/$(id -u)/com.mind-palace.watch 2>/dev/null   # retire the old watcher
mind-palace reset --confirm                                        # hard-wipe corpus (Vault guarded)
#   …then re-export notes into ~/.mind-palace/vault/janus_notes/ + point Synctrain there…
mind-palace start                                                  # re-ingests as authored-solo

# --- ONE-TIME ENABLEMENT ----------------------------------------------------------------------
mind-palace ingest-self-knowledge      # so "how do you work?" answers from docs
mind-palace build-sandbox-image        # data-analysis libs image (numpy/scipy/…)
#   then set [sandbox] image = "mind-palace-sandbox:latest" in config/local.toml — see "Code-exec sandbox"

# --- INSTALL THE ALWAYS-ON DAEMON (supersedes com.mind-palace.watch) — see "One-command lifecycle"
cp ops/lifecycle/com.mind-palace.palace.plist ~/Library/LaunchAgents/
launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/com.mind-palace.palace.plist

# --- USE THE SANDBOX DIRECTLY (data in, data out) — see "Code-exec sandbox" -------------------
echo 'print(40+2)' | mind-palace sandbox -
mind-palace sandbox analysis.py --input series.csv=~/data/series.csv

# --- SECURITY / AUDIT (owner-operated) — see their sections below -----------------------------
mind-palace gen-attestation-keys supervisor   # / owner — print a fresh signing seed for Keychain
mind-palace verify-attestation --all          # / --list / <id> — verify the signed chain
mind-palace check-imports                     # the import-firewall lint, standalone (also in CI)
mind-palace purge-raw <digest> --confirm      # owner-gated TRUE deletion of a tombstoned blob

# --- ALREADY-LIVE LAYERS (reference; turn on/operate as needed) -------------------------------
#   Vault (unseal LaunchAgent), Backups ([backup] in local.toml + restic), Self-mod gate
#   ([selfmod] enabled + ops/selfmod_cli.py), Attestation signing ([attestation] above).
#   The provenance-split migration is now MOOT (the fresh start re-tags everything authored-solo);
#   `mind-palace migrate-provenance` still exists if you ever need it again.
```

Optional (your call): the edge monitor (remote dashboard + chat over Tailscale — built; `[monitor]
enabled=true`); Vault credential grants (`[secrets].grant_roles`); a WASI `python.wasm` to activate
the WASM sandbox substrate. All in their sections below.

---

## Verifying a change — run live wherever possible (owner policy, 2026-07-02)

The default `pytest` run deselects `live`/`podman`/`needs_*` — it's the fast, deterministic
inner-loop ratchet (stores + the model-free reasoning/structural layer), and it stays green before
and after every step. **It is no longer the finish line** for anything that touches an Ollama model
tier or the sandbox — verify those live, as a matter of course, whenever the real thing is
available:

```sh
uv run pytest -m 'not live and not podman and not needs_vault and not needs_restic'  # the ratchet (fast, always)
uv run pytest -m live       # real Ollama: embedder + router/routine/synthesis/stretch tiers
uv run pytest -m podman     # real rootless-Podman run_python execution (separate axis, below)
```

CI (2026-07-12): the gate runs on **GitHub Actions** (`.github/workflows/ci.yml`) — the GitLab
pipeline is tombstoned (`.gitlab-ci.yml`, `workflow: when: never`; see
docs/design-notes/ci-platform-and-runner-strategy.md D1/D5). **Every** push to main (no
docs-skip — every sha yields a verdict) runs **five mutually-independent jobs**: `ratchet`
(ruff + import-firewall + the model-free pytest tier), `type-gate` (mypy Tier-2 floor + the
tests/ baseline + membership scans), `vault-axis` (the `needs_vault` suite against a disposable
dev-mode Vault service container), `semgrep` (SAST, `p/default`), and `gitleaks` (secret
detection over full history). The live/podman/restic axes still never run in CI — the runner
has none of those substrates; they remain local verification, above. Runner minutes are now
unmetered (public repo), so batching is no longer a budget necessity — but push at unit
boundaries anyway for verdict hygiene and wall-clock (a stale run is auto-cancelled by a newer
push, `concurrency: cancel-in-progress`).

**These are two different axes — don't conflate them.** `-m live` needs a pulled model + a running
Ollama server (`ollama list` / `curl localhost:11434/api/version`); `-m podman` needs
`podman machine list` showing `Currently running`. A live/dreaming change needs `-m live`, not
`-m podman` — the Dreamer and the reasoning complex (`core/dreaming/`, `core/complex/`) run their
own computation in-process (model-free, deterministic aside from the embed/synthesize calls) and
never touch the sandbox. `-m podman` only matters for `core/sandbox/` itself or a role's
`run_python` scope. Each live test has an honest `skipif` on the actual model/tier being pulled
(e.g. `test_dreaming_live.py` needs the `synthesis` tier, `qwen3.6:27b`) — if a gate skips, that's
the real state, not a mock standing in for it; say so rather than treating the offline suite as
sufficient.

---

## Prerequisites (Phase 0)
- Python 3.11+ (built/verified on 3.14), managed by **uv** (`uv.lock` is authoritative;
  `uv run` resolves the env — never invoke `./.venv/bin/...` paths by hand, house rule 2026-07-11).
- Ollama running on loopback (`127.0.0.1:11434`).
- Models: `qwen3.5:2b` (pinned, pulled). `qwen3.5:9b` / `qwen3.6:27b` are pulled as
  Phases 1–2 need them; `qwen3.6:35b-a3b` (stretch) already present.

## Setup
```
uv sync --extra dev
```

## Verify Phase 0
```
uv run ruff check .
uv run pytest -q              # full suite (skips live if Ollama down)
uv run pytest -q -m "not live"   # logic-only, no Ollama needed
```
Gate: model responds; vitals flow into DuckDB; sealed core blocks external egress;
a trivial agent inherits the Constitution.

## Sealing — egress enforcement (Invariant 1)
The sealed core (`core/`) must have zero network egress. Enforcement is layered:

1. **In-process guard (`core.sealing`, active now).** `core.runtime.bootstrap()` calls
   `seal()` at startup, installing a fail-closed guard that permits only loopback
   connects (the local Ollama channel) and raises `SealedCoreEgressError` on anything
   else. Verifiable in tests. Fails closed, but a native extension opening its own
   socket could bypass a Python-level hook — hence layer 2.
2. **OS-level isolation (deployment hardening, TODO before any networked phase).**
   Run the core process under a `pf` anchor that denies outbound for its uid, or in a
   container/netns with `--network=none` plus a loopback path to Ollama. This is the
   structural guarantee the in-process guard approximates on bare macOS.

Edge (`edge/`, Zone B) is the only zone allowed to reach the network; the guard is
**not** installed there. Core↔edge communicate by filesystem handoff, never imports.

## Sandbox runtime — Podman machine (Phase 4) — ✅ RESOLVED 2026-06-29 (E1 closed)

**The empirical gap is closed.** A podman machine runs here (libkrun provider, the
`podman-machine-default` VM) and `pytest -m podman` passes **7/7** — real containers verify
network-off, vault-unreachable, non-root, wall-clock-timeout, AND the new data-in path (data
readable at `/tmp/input`, vault still unreachable with inputs present). So the isolation that
was previously "proven only by construction" is now also proven empirically. Keep the podman
machine running (`podman machine start`) for the sandbox + the `palace` preflight. The
historical boot-troubleshooting notes below are retained for reference only.

The Phase 4 sandbox (`core/sandbox/`) runs code in rootless Podman. On macOS Podman needs
a Linux VM ("podman machine"). The **logic gate is fully met by construction** — the
isolation profile is asserted on the argv (`tests/unit/test_sandbox_policy.py`) and the
pool/broker behavior with a fake runner, all passing — AND now empirically (above).

**Config written:** `~/.config/containers/containers.conf` sets `[machine] provider = applehv`,
`cpus = 2`, `memory = 2048`, `disk_size = 20`. Sizing is deliberately small so the VM does
not eat the model RAM ceiling (Invariant 8); the sandbox uses 256 MB containers, concurrency 1.

**What was tried and what failed:**
- **libkrun / krunkit 1.2.2 + podman 6.0** — guest Fedora CoreOS boots into **emergency
  mode** (a virtio-fs mount failure in the guest → SSH never starts → `connection refused`).
  Unusable here. (krunkit is installed from the `libkrun/krun` tap, tap trusted.)
- **applehv** — the **first** machine booted cleanly and a smoke test passed
  (`podman run --network=none python:3.12-slim …` → ok). After tearing it down to try
  libkrun and back, the **re-created** applehv machine fails with `vfkit exited unexpectedly
  (exit 1)` / ssh handshake reset — i.e. wedged machine/socket state from the churn, not a
  code problem.

**Current state:** no machine defined (cleaned up), no zombie `vfkit`/`krunkit`/`gvproxy`
procs, provider config left at `applehv`. Decent/idle.

**To come back (do this when revisiting):**
1. Fresh start: `podman machine init --now` (uses applehv from config). If `vfkit exited
   unexpectedly` recurs, try `podman machine reset` first, or reboot to clear stale state.
2. Pre-pull the image so the 10 s wall-clock timeout isn't spent pulling:
   `podman pull python:3.12-slim`.
3. Empirically verify isolation: `uv run pytest -m podman`
   (network-off, vault-unreachable, non-root, timeout-enforced).
4. **Fallback if Podman stays broken:** Docker works on this host but its daemon is
   **rootful** (weaker than rootless Podman). To use it, add a `DockerRunner` alongside
   `PodmanRunner` (same `build_run_argv` flags — `docker run` accepts the same isolation
   flags except `--pids-limit` syntax is identical; drop `--security-opt no-new-privileges`
   only if unsupported) and set `[sandbox] runtime` accordingly. Treat rootful as a
   temporary measure; the isolation profile (no mounts, no net, caps dropped) still holds
   per-container. Revisit `--userns` for rootless-equivalent uid mapping.

## Vault watcher & sync (capture path, design-notes/vault-sync-and-capture.md)

How the owner feeds notes in and keeps embeddings current. **Two separable pieces:** the
**watcher** (code, core-side, local-filesystem only) and the **sync transport** (a separate
process — never the core). **Status: both operationally configured and live-verified
(2026-06-27)** on the owner's Mac (M2 Max) + iPhone — see `docs/PROGRESS.md` for the full
session log, including a concurrency bug found and fixed during verification.

### Watcher (code — runs locally, no network)
Re-ingests changed notes through the Phase-1 pipeline, idempotently (content-addressing):
unchanged = no-op, changed = re-embed, deleted = **tombstone** (derived dropped, raw kept).
```
uv run scripts/watch.py     # seals the core, then watches [vault].path
```
Real-time via `watchdog` (FSEvents) if installed (`uv pip install watchdog`); without
it the watcher **falls back to polling** every `[vault].watch_poll_interval_s`. Either way the
trigger just enqueues a background `vault_sync` job and the supervisor runs the idempotent
rescan — missed/duplicate events are harmless. It is core-side and reaches no network (the
import-lint proves it); only the local filesystem and local stores are touched.

`scheduler/queue.py`'s `JobQueue` connection is `check_same_thread=False` + `RLock`-guarded
specifically because the watcher's debounce timer and poll loop call `on_change` (→ `enqueue`)
from a thread they spawn, not the thread that constructed the queue. Without this, real-time
and polled triggers crash silently (swallowed by `threading`'s default excepthook) while
`launchctl`/`ps` still report the service healthy — caught + fixed 2026-06-27, see PROGRESS.md.

### Running the watcher as a launchd service (so it survives logout/reboot)
```
~/Library/LaunchAgents/com.mind-palace.watch.plist
```
`ProgramArguments` = the repo's `.venv` python + `scripts/watch.py`; `RunAtLoad`+`KeepAlive`
(10s `ThrottleInterval`); `PYTHONUNBUFFERED=1` (otherwise stdout buffers and the log looks
empty); logs to `data/logs/watch.{out,err}.log`.
```
launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/com.mind-palace.watch.plist  # start
launchctl bootout   gui/$(id -u)/com.mind-palace.watch                              # stop
launchctl print     gui/$(id -u)/com.mind-palace.watch | grep state                 # status
tail -f data/logs/watch.out.log                                                     # live log
cat data/logs/watch.err.log                                                         # errors
```
To pick up a code change, `bootout` then `bootstrap` again (no separate "restart" verb).

### Sync transport (operational — a SEPARATE process, NOT the core)
Keeps the vault directory current across the owner's devices. The core only watches a local
folder; it never runs or talks to the sync daemon.
- **Configured: Syncthing over Tailscale** — peer-to-peer, device-to-device, encrypted, **no
  vendor in the path**. Mac: `brew install syncthing && brew services start syncthing` (GUI at
  `localhost:8384`, loopback-only). iPhone: **Synctrain** (free/OSS; Möbius Sync is the
  documented fallback if it ever stops working). The vault folder (id `mind-palace-vault`) is
  shared `sendreceive` between the two devices; a `.stignore` in the vault root excludes
  `.DS_Store`/`.stversions`/temp files from syncing.
- **Tailscale** is the private mesh: it gives the phone an encrypted path to the laptop, used
  for (a) Syncthing peer sync and (b) reaching the future interface gateway (Zone B) to
  chat-capture/query — matching the established "private default" interface posture.
- **Confinement — both ends, not just one.** Public/global discovery, relays, NAT-PMP/UPnP, and
  STUN are all disabled on **both** the Mac (Syncthing GUI → Settings → Connections) and the
  phone (Synctrain → Advanced Settings); each device's peer address is pinned to the other's
  **Tailscale IP** (`tcp://100.x.x.x:22000`) instead of left `dynamic`. This matters off-LAN: a
  one-sided pin still lets the *other* device fall back to a public discovery/relay server.
  **Verify in the Syncthing GUI:** click the phone device in the sidebar — the address shown
  must read the phone's Tailscale IP (`100.x.x.x`), never a relay name or a different subnet.
  Confirmed live over the phone's cellular connection (no LAN involved):
  `/rest/system/connections` reported `type: tcp-server` direct, not `relay-client`.
- **Vendor-transit tradeoff (flagged):** iCloud / Obsidian Sync are convenient but **transit a
  vendor** — the same class of tradeoff as the interface-transits-third-party invariant
  (Invariant 11). They move the owner's *own authored notes* through a third party (encrypted
  in transit, but the vendor is in the path). Syncthing-over-Tailscale avoids that entirely;
  the owner chooses, and the private option is recommended (and is what's configured).

### iOS capture (no third-party notes app)
Apple Notes' Share→Save-to-Files always names the export `text.txt` (auto-numbering on
collision) and can't produce a real `.md`. Use an iOS **Shortcut** instead: `Ask for Input`
(Text) → `Format Date` (input **Current Date** — not "Date Created") → `Save File` (saves the
*input text*; destination `Ask Each Time` — pick Synctrain → Mind Palace Vault; `Subpath`
`note-[Formatted Date].md`) → **`Rename`** (required — Shortcuts' `Save File` silently forces
the input's native `.txt` extension regardless of what's typed in `Subpath`; `Rename` to the
same `note-[Formatted Date].md` string fixes it). One tap from the home screen or share sheet.
After saving, Synctrain needs a manual **rescan** of the folder (pull-to-refresh) to push a
phone-authored file — iOS suspends its background watcher (see "Known Synctrain quirk" below).

### Known Synctrain quirk — reverse sync needs a manual rescan
A file created/edited *on the phone* often doesn't push to the Mac until Synctrain's
**Mind Palace Vault folder is manually rescanned**: open the folder in Synctrain and
pull-to-refresh (or use its Rescan action). Mac→phone sync doesn't need this — only
phone-originated changes are affected, because iOS suspends Synctrain's background
file-watcher. Forward sync (Mac edits → phone) is unaffected.

### True deletion — owner-gated purge (not the watcher's default)
A vault delete only **tombstones** (raw kept) so re-adds dedup and nothing is lost. To destroy
the raw bytes too (genuine privacy deletion), use the deliberate, irreversible purge — refused
unless `--confirm` is passed AND the content is held by no active note (tombstone it first):
```
uv run scripts/purge_raw.py --list                 # show purgeable (tombstoned) digests
uv run scripts/purge_raw.py <digest> --confirm     # destroy raw + derived for it
```

### Verify
- Edit a note → its embeddings update (search reflects the new content; old rows gone).
- Delete a note → it stops surfacing in search; raw blob is retained until a purge.
- Unchanged re-scan → no-op (no new digests, no duplicate rows).
- `uv run python -m ops.import_lint` → green (the watcher reaches no network).
Cold-tested in `tests/test_vault_sync.py`, `tests/test_vault_watcher.py`,
`tests/test_purge_raw.py`, `tests/test_vault_sync_wiring.py`.

**Live-verified end-to-end (2026-06-27, real iPhone + Mac, not mocks):** a phone-authored note
(via the Shortcut above, over cellular) synced → watcher caught it automatically → embedded →
returned as the top semantic-search hit. Deleting a tracked note tombstoned automatically
(catalog inactive, vector rows dropped, `RawStore.exists(digest)` still `True`). A no-change
rescan returned `indexed=0` with the vector count unchanged. Full details + the concurrency bug
this surfaced (now fixed) in `docs/PROGRESS.md`'s 2026-06-27 entry.

## Security & trust infrastructure (owner-operated) — attestation keys, Vault, AWS airlock

The consolidated owner runbook for the **security & attestation track** (Step 6 — the last step).
The build agent wrote the code, dev-mode/mock tests, policy-as-code (`ops/vault/policies/*.hcl`),
and this runbook; **nothing below has been run against production** — placing real keys, standing
up real Vault, and applying real AWS are owner-operated by design (the model advises; code acts;
*you* hold the credentials). The three component READMEs each point here for the full steps:
`ops/attestation/README.md`, `ops/vault/README.md`, `cloud/terraform/airlock/README.md`.

**Everything here is additive and independently reversible.** Until you do these, the system runs
exactly as tested: attestation **records-only** (chained + content-addressed but unsigned),
`[secrets]` **disabled** (so `get_secret(name)` reads env/Keychain unchanged), no AWS airlock.
Each layer's bottom turtle is one secret in macOS Keychain. Do them in the order below.

### 0. Keychain — the bottom turtle (delivery mechanism for every secret below)

`get_secret(name)` is `os.environ.get(name)` (`config/loader.py`). So every "place X in Keychain"
step means **store it in Keychain, and make sure the mind-palace process inherits it in its
environment.** Store with the macOS `security` CLI (the seed never touches a file, a shell
history entry, or a log — `-w` with no value prompts interactively):

```sh
security add-generic-password -U -a mind-palace -s attestation-signing-key -w   # prompts; paste seed
security find-generic-password -a mind-palace -s attestation-signing-key -w     # read back to verify
```

Deliver to the process via a launch wrapper the agent execs — the secret names are hyphenated
(`attestation-signing-key`), which `os.environ` and `env(1)` accept fine but shell `export` does
not, so set them through `env(1)`, not `export`. Save as `scripts/run_with_secrets.sh` and point
the LaunchAgent's `ProgramArguments` at it instead of `python` directly:

```sh
#!/bin/sh
# Read secrets from Keychain into the env, then exec the real command. No seed is ever written
# to disk — they live only in Keychain and this process's memory.
set -eu
kc() { security find-generic-password -a mind-palace -s "$1" -w; }
exec env \
  "attestation-signing-key=$(kc attestation-signing-key)" \
  "attestation-owner-key=$(kc attestation-owner-key)" \
  "vault-supervisor-token=$(kc vault-supervisor-token)" \
  "$@"
# plist ProgramArguments: [ .../scripts/run_with_secrets.sh, .../uv, run, .../scripts/watch.py ]
```

A secret that isn't placed yet just resolves to `None` — the corresponding layer stays off,
fail-closed where it matters (see §1). Place only the ones whose layer you're turning on.

### 1. Attestation signing keys — turn on the signed runtime-proof layer

Activates Ed25519 signing inside `StoreAttestor.emit` (records become tamper-evident). The
committed `ops/attestation/*.pub` are **DEV** keys with no production trust — replace them:

```sh
uv run scripts/gen_attestation_keys.py supervisor   # prints a base64 seed; rewrites supervisor.pub
uv run scripts/gen_attestation_keys.py owner         # prints a base64 seed; rewrites owner.pub
security add-generic-password -U -a mind-palace -s attestation-signing-key -w   # paste the supervisor seed
security add-generic-password -U -a mind-palace -s attestation-owner-key   -w   # paste the owner seed
git add ops/attestation/supervisor.pub ops/attestation/owner.pub && git commit   # pubs are public
```

Then set `[attestation] enabled = true` in config. Turning it on **without** a placed signing key
is a hard error (`AttestationKeyMissing`, fail-closed) — never a silent unsigned run. The owner
seed signs **gate decisions only** (non-repudiable approval); the supervisor seed signs all other
agent attestations. Verify:

```sh
uv run scripts/verify_attestation.py --all     # every stored attestation's signature + chain
```

### 2. Vault (Homebrew) — the runtime credential-authorization layer

You installed `vault` via Homebrew (`/opt/homebrew/bin/vault`). The design note
(`vault-runtime-auth.md` §1) sketches Vault in a rootless Podman container; the Homebrew binary is
simpler on a single-user Mac and equally loopback-bound — the client `addr` and the stored data
are identical, only the process manager differs. Either is fine.

#### 2a. Quick validation NOW — dev mode (disposable, in-memory, no production keys)

This is what the `needs_vault` live tests target; it proves the real mint → accessor → scoped-read
round-trip end to end. Dev mode auto-unseals, prints a root token, and **loses everything on
Ctrl-C** — never use it for real secrets.

```sh
# Terminal 1 — throwaway server
vault server -dev -dev-listen-address=127.0.0.1:8200      # copy the "Root Token: hvs.…" it prints

# Terminal 2
export VAULT_ADDR=http://127.0.0.1:8200
export VAULT_TOKEN=<root token from terminal 1>
uv run python -m pytest -m needs_vault -v             # seeds policies from ops/vault/policies/, asserts the join
```

The test seeds `ops/vault/policies/dreamer.hcl` via the root token (the dev-mode equivalent of
`vault policy write`), mints a `dreamer` token, and checks both a permitted read and an
out-of-policy denial against the **real** server — the same assertions `FakeVault` makes in the
unit suite, now against `hvac`.

#### 2b. Production — persistent, auto-unsealed on login

Run the server from a config file (not `brew services`' dev default), with Raft integrated storage:

```hcl
# ~/.mind-palace/vault.hcl
storage "raft" { path = "/Users/<you>/.mind-palace/vault-data"  node_id = "mac" }
listener "tcp" { address = "127.0.0.1:8200"  tls_disable = true }   # loopback = inside the egress guard (Invariant 1)
api_addr     = "http://127.0.0.1:8200"
cluster_addr = "http://127.0.0.1:8201"
disable_mlock = true
ui = true
# When the server node joins the Tailscale mesh, ADD a second listener on the 100.x.x.x iface — do
# not replace the loopback one (vault-runtime-auth.md §1).
```

```sh
vault server -config ~/.mind-palace/vault.hcl &            # or a LaunchAgent, mirroring com.mind-palace.watch
export VAULT_ADDR=http://127.0.0.1:8200
vault operator init -key-shares=1 -key-threshold=1         # single-user simplicity; note the single-key tradeoff
#   → store BOTH outputs in Keychain:
security add-generic-password -U -a mind-palace -s vault-unseal-key   -w   # paste Unseal Key 1
security add-generic-password -U -a mind-palace -s vault-root-token   -w   # paste Initial Root Token
vault operator unseal "$(security find-generic-password -a mind-palace -s vault-unseal-key -w)"
export VAULT_TOKEN="$(security find-generic-password -a mind-palace -s vault-root-token -w)"
```

Auto-unseal on login — a LaunchAgent (same pattern as `com.mind-palace.watch`) that starts the
server then unseals from Keychain:

```sh
#!/bin/sh                                  # scripts/vault_unseal.sh, invoked by the LaunchAgent
set -eu
vault server -config "$HOME/.mind-palace/vault.hcl" &
until vault status >/dev/null 2>&1 || [ "$?" = 2 ]; do sleep 1; done   # status exits 2 while sealed
vault operator unseal "$(security find-generic-password -a mind-palace -s vault-unseal-key -w)"
```

Enable the engines, write the policies, bind a token role per agent, and load the static secrets
(`ops/vault/README.md` has the role→grant table; `kv` paths must match it exactly):

```sh
vault secrets enable -version=2 -path=kv kv
vault secrets enable -path=aws aws            # then configure bridge-role / airlock-role IAM (see §3 + the aws engine docs)
for f in ops/vault/policies/*.hcl; do vault policy write "$(basename "$f" .hcl)" "$f"; done
# one token role per policy so the supervisor can mint scoped child tokens:
for r in dreamer bridge research-airlock advisor correlator gate; do
  vault write "auth/token/roles/$r" allowed_policies="$r" period=10m orphan=false; done
# static secrets the policies grant (values are yours; these are the names the code reads):
vault kv put kv/oura-daily-aggregates value=<…>
vault kv put kv/oura-api-token        value=<…>
vault kv put kv/financial-readonly-key value=<…>
vault kv put kv/gate-ledger-key       value=<…>
```

The **supervisor's** own bootstrap token is the bottom turtle for this layer — it holds
`auth/token/create` (mints child tokens) and nothing else, and lives in Keychain, never in Vault:

```sh
vault token create -policy=supervisor -period=24h -orphan        # copy the token
security add-generic-password -U -a mind-palace -s vault-supervisor-token -w    # paste it
```

Finally set `[secrets] enabled = true`. `build_secrets_backend` now wires a real `VaultClient`
(`addr`/`kv_mount`/`aws_mount` from `[secrets]`, supervisor token from
`get_secret("vault-supervisor-token")`). Agents still never call Vault directly — they receive a
minted token in context (Phase 5) and pass it to `get_secret(name, token=…)`; an out-of-scope read
raises `VaultPermissionDenied`, and that denial is itself an alignment signal (§6).

### 3. AWS research airlock — apply Phase 8 (Zone C)

Owner-operated infra apply (account `054942746160`, SSO `alberto-sso`, `us-east-1`). Full notes in
`cloud/terraform/airlock/README.md`:

```sh
aws sso login --profile alberto-sso
cd cloud/terraform/bootstrap && AWS_PROFILE=alberto-sso terraform init && AWS_PROFILE=alberto-sso terraform apply
cd ../airlock && AWS_PROFILE=alberto-sso terraform init && AWS_PROFILE=alberto-sso terraform apply
```

Copy `airlock_bucket` → `config/defaults.toml [airlock] s3_bucket`, and add a `mind-palace-bridge`
AWS profile that assumes `bridge_role_arn` (`source_profile = alberto-sso`). Recommended: narrow
`bridge_trusted_principal_arns` to the SSO role (the TF still also trusts the Vault engine user, so
that stays working). The bridge (Zone B) is the only component that holds AWS creds and touches S3;
the corpus never crosses — only de-identified criteria (Inv. 2/11).

#### 3a. Vault AWS dynamic engine (Phase B — the end state)

The airlock TF (`vault_engine.tf`) also creates `mind-palace-vault`, the IAM user Vault's AWS engine
authenticates as. Its only permission is `sts:AssumeRole` on bridge-role, so Vault can mint
short-lived (TTL=1h) bridge creds on demand (`vault-runtime-auth.md §4`). After `terraform apply`:

```sh
# 1. Mint the engine user's access key BY HAND — kept out of tfstate. (Long-lived bootstrap key;
#    this is the one durable secret the dynamic engine needs. Rotate later via aws/config/rotate-root.)
aws iam create-access-key --user-name mind-palace-vault --profile alberto-sso

# 2. Hand it to Vault as config/root (secret — by hand, never scripted):
export VAULT_ADDR=http://127.0.0.1:8200
export VAULT_TOKEN="$(security find-generic-password -a mind-palace -s vault-root-token -w)"
vault secrets enable -path=aws aws
vault write aws/config/root access_key=<…> secret_key=<…> region=us-east-1

# 3. Configure the bridge role (validated script; bridge-role is the only assumable role):
export BRIDGE_ROLE_ARN="$(cd cloud/terraform/airlock && terraform output -raw bridge_role_arn)"
sh ops/vault/setup_aws_engine.sh

# 4. Verify — mints a real temporary AWS cred that expires in 1h:
vault read aws/creds/bridge-role
```

**Note on consumption:** nothing fetches `aws/creds/bridge-role` from Vault yet — the bridge still
uses the static `mind-palace-bridge` SSO profile. Rewiring the bridge to mint AWS creds from Vault
is Phase 5 (the bridge holding its own identity). On a single-user Mac with SSO this engine is the
*end state staged early*; it truly earns its keep on the headless server (no SSO session to lean on).

### 4. Secrets ↔ where they live (the full map)

| Secret name (`get_secret`) | Lives in | Read by | Scope |
|---|---|---|---|
| `attestation-signing-key` | Keychain | `build_attestor` (supervisor signer) | signs all non-gate attestations |
| `attestation-owner-key` | Keychain | `build_attestor` (owner signer) | signs **gate decisions only** |
| `vault-supervisor-token` | Keychain | `build_secrets_backend` | mints scoped child tokens; reads no role secret |
| `vault-unseal-key` / `vault-root-token` | Keychain | the unseal LaunchAgent / you | bootstrap Vault itself |
| `kv/oura-daily-aggregates` | Vault kv-v2 | `dreamer`, `correlator` tokens | biometric aggregates |
| `kv/oura-api-token` | Vault kv-v2 | `bridge`, `advisor` tokens | Oura API |
| `kv/financial-readonly-key` | Vault kv-v2 | `advisor` token | read-only financial |
| `kv/gate-ledger-key` | Vault kv-v2 | `gate` token | gate-state encryption |
| `aws/creds/bridge-role` | Vault aws (dynamic) | `bridge` token | S3 airlock, TTL=1h |
| `aws/creds/airlock-role` | Vault aws (dynamic) | `research-airlock` token | research S3, TTL=1h |
| AWS SSO | Keychain (owner-operated) | `aws sso login` (you) | not code-operated |

### 5. End-to-end verification

```sh
uv run python -m pytest -m needs_vault -v        # real Vault: scoped mint/read + out-of-policy denial (§2a)
uv run scripts/verify_attestation.py --all   # signatures + chains to authored leaves (§1)
uv run python -m ops.import_lint                  # core/ still reaches no network, no hvac/boto3
```

Gate: a `dreamer` token reads `kv/oura-daily-aggregates` but is **denied** the financial key; the
supervisor token cannot read role secrets directly; emitted attestations verify and (when an action
runs under a minted token) carry that token's **accessor** — never the token (Step 5 join).

## Encrypted backups — restic → S3 (Phase 9, owner-operated)

`restic` encrypts + deduplicates **client-side**, so the only bytes that reach S3 are ciphertext —
AWS never sees plaintext (§16b). The bucket's SSE-KMS is defense in depth; the bucket is versioned
so a bad prune is recoverable. The scheduled job (`ops/backup/backup.sh`) reads the data dirs and a
consistent Vault snapshot, and is the only thing here that crosses the network — the sealed core
never runs backups. The restic invocation itself is built + unit-tested in `ops/backup/plan.py`;
backup + restore + no-plaintext are proven against a local repo (`pytest -m needs_restic`).

```sh
brew install restic        # the backup tool

# 1. Infra (cloud/terraform/backups — S3 + KMS + the scoped mind-palace-backup IAM user):
aws sso login --profile alberto-sso
cd cloud/terraform/backups && AWS_PROFILE=alberto-sso terraform init && AWS_PROFILE=alberto-sso terraform apply
#   note outputs: backup_bucket, backup_user_name (=mind-palace-backup), restic_repository

# 2. Backup IAM key by hand (kept out of tfstate) -> Keychain:
aws iam create-access-key --user-name mind-palace-backup --profile alberto-sso
security add-generic-password -U -a mind-palace -s backup-aws-access-key-id     -w   # paste AccessKeyId
security add-generic-password -U -a mind-palace -s backup-aws-secret-access-key -w   # paste SecretAccessKey

# 3. The restic repo password — generate a STRONG one and place it in Keychain. ⚠️ ALSO escrow it
#    out-of-band (printed/password-manager): lose it and the backups are UNRECOVERABLE.
security add-generic-password -U -a mind-palace -s restic-password -w               # paste a long random string

# 4. (Full-DR Vault snapshot) apply the backup policy + a long-lived snapshot token -> Keychain:
export VAULT_ADDR=http://127.0.0.1:8200
export VAULT_TOKEN="$(security find-generic-password -a mind-palace -s vault-root-token -w)"
vault policy write backup ops/vault/policies/backup.hcl       # (or re-run ops/vault/setup_policies.sh)
vault token create -policy=backup -period=768h -orphan -field=token   # copy it
security add-generic-password -U -a mind-palace -s vault-backup-token -w            # paste it

# 5. Enable [backup] for THIS machine in config/local.toml (gitignored), with the repo URL:
#    [backup]
#    enabled = true
#    repository = "<terraform output restic_repository>"

# 6. First run (self-inits the repo), then verify a restore + install the daily schedule:
sh ops/backup/backup.sh                                        # init + backup + prune + check
uv run python -m ops.backup.run snapshots                 # should list one snapshot
#   restore-verify into a scratch dir (do this once to trust the chain end-to-end):
RESTIC_PASSWORD="$(security find-generic-password -a mind-palace -s restic-password -w)" \
AWS_ACCESS_KEY_ID="$(security find-generic-password -a mind-palace -s backup-aws-access-key-id -w)" \
AWS_SECRET_ACCESS_KEY="$(security find-generic-password -a mind-palace -s backup-aws-secret-access-key -w)" \
  uv run python -m ops.backup.run restore latest /tmp/restore-check
cp ops/backup/com.mind-palace.backup.plist ~/Library/LaunchAgents/
launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/com.mind-palace.backup.plist   # daily 03:30
launchctl kickstart -k gui/$(id -u)/com.mind-palace.backup     # run once now to confirm; logs in data/logs/backup.*.log
```

Gate (BUILD-SPEC §18 Phase 9): an encrypted backup + restore round-trips, and AWS sees no plaintext.
The `needs_restic` test proves the encryption boundary locally; step 6's S3 restore-verify confirms
the live path. **Backup independence:** the `mind-palace-backup` identity is deliberately separate
from Vault's AWS engine, so restore works even when Vault is sealed/down (it's the DR path).

## Self-modification gate — operating the loop (Phase 10, owner-operated)

The system can tune its own **alignment/quality knobs** (the `[dreaming]` levers) through a gated,
validated, reversible loop (BUILD-SPEC §14). The writable surface is knobs ONLY — `ops/levers.py`
physically cannot express a code or infrastructure change (a `ProposedChange` has no field for a
path/diff/command). The loop ships **OFF**; activating and driving it is owner work.

```sh
# 1. Activate the loop on THIS machine — add to config/local.toml (gitignored):
#    [selfmod]
#    enabled = true
#    # unattended_enabled stays false: every change goes through you at the gate.

# 2. Drive the gate (a model may write PROPOSED rows; only you approve — Invariant 5):
uv run python -m ops.selfmod_cli list                         # pending proposals
uv run python -m ops.selfmod_cli propose dream_similarity_threshold 0.66 "tighten themes"
uv run python -m ops.selfmod_cli show 1                       # full detail of a proposal
uv run python -m ops.selfmod_cli approve 1                    # approve -> execute -> VALIDATE
#   approve runs the frozen golden anchor with the real embedder (Ollama must be up + the embed
#   model pulled). If capability regresses, the knob AUTO-ROLLS-BACK and `approve` says so.
uv run python -m ops.selfmod_cli deny 2                       # reject a proposal
uv run python -m ops.selfmod_cli history                     # full audit trail
```

Tuned values land in `config/levers.toml` (machine-owned, gitignored); your hand-authored
`config/local.toml` always overrides them (human authority is supreme). Delete `config/levers.toml`
to revert every tuned knob to its committed default.

**Registered levers** (hard bounds enforced — an out-of-range target is refused): `dream_similarity_threshold` [0.55–0.75],
`dream_near_dup_threshold` [0.90–0.99], `dream_min_cluster_size` [2–6], `dream_max_clusters` [4–16].

**Deferred by design:** behavioral (`conforms`) validation is the small-model judge seam — the gate
honestly omits it rather than stubbing it True, so a knob change is kept on *capability-non-regression*
only, with behavior the human's call. Nothing autonomously proposes yet (no cron wiring); the
`unattended_enabled` "safe levers" path exists but is flag-off. Gate (BUILD-SPEC §18 Phase 10): a
proposed change traverses the gate; a bad change auto-rolls-back; the frozen anchor catches drift the
rolling baseline misses — all proven in `tests/integration/test_selfmod.py`.

## Dreamer output-quality suite (F9, Track F) — running it + the two owner-deferred hooks

The signal-vs-noise / apophenia suite (`tests/quality/`, design-notes/dreamer-quality-suite-evaluation.md)
asks the one question the safety/provenance/drift suites do not: *is a dream real signal, or
well-attested noise?* It is **pure-CI** — no Ollama, no scheduler — and runs in the default `pytest`.
The `DreamerAdapter` is bound to the **live** Dreamer/DerivedStore in `tests/fixtures/dreamer_adapter.py`
(`MindPalaceDreamerAdapter`): real clustering, real grounding, real interpreted-only persistence; only
the embedder and synthesizer are deterministic offline stand-ins (the quality layer does not grade
prose, and the real embedder needs Ollama).

```sh
# Runs against BOTH the in-file reference fake AND the real binding (parametrized [ref]/[real]):
uv run pytest tests/quality/ -v
uv run pytest -m quality                       # the same, selected by marker

# Force a single explicit adapter (the design-note env seam):
MIND_PALACE_DREAMER_ADAPTER="fixtures.dreamer_adapter:build_real_dreamer_adapter" \
  uv run pytest tests/quality/test_dreamer_quality.py -q
```

**Optional full-fidelity run against the real embedder.** The CI binding uses a deterministic
*lexical* embedder (no model) tuned at clustering threshold ~0.50. To exercise the suite against the
real Qwen3 embedding model, point `MindPalaceDreamerAdapter(embedder=…, threshold=cfg.dreaming.
similarity_threshold)` at `core.ingest.embed.build_embedder()` (Ollama up, embed model pulled). This is
the **"tune THRESH on known corpora"** step from the design note: `THRESH` (in `test_dreamer_quality.py`)
is the tuning surface — drive it the same way you drive the drift bands γ/λ/σ/Θ; a tightened threshold
is a logged tuning decision, not a code change.

**Hook 1 — wire `rate_blind` to validate the value claim (owner ritual).** The headline value test
`test_real_dreams_beat_decoys_under_blind_rating` **SKIPS** until you wire it, and the suite says so
loudly: whether a real dream beats Barnum-bait is irreducibly a *human* question. The automatable proxy
(`test_real_dreams_are_demonstrably_anchored`) only proves the dreams are *anchored*, not *meaningful*.
To close it, periodically (say monthly): run the dreamer over your real corpus, mix its dreams with
random-recombination decoys *unlabelled*, score each for usefulness without knowing which is which, then
implement `rate_blind(candidates) -> [scores]` on the adapter returning those scores. The test then
asserts real-mean > decoy-mean. **A green proxy is NOT a validated value-claim — keep this open until
the blind rating runs.**

**Hook 2 — fold support COUNT into the adjudicator's `g` when the R&D path goes live (deferred).** The
binding resolved review-note-2's open question: confidence must scale with the *number* of authored
supports, not cohesion alone (a 2-note cosine-1.0 coincidence is weak support — the apophenia failure in
miniature). The binding computes `g = grounding_score · cohesion · size_factor`. But the **flag-OFF R&D
adjudicator** (`core/dreaming/adjudicator.py`) still defines `g = grounding_score` only (pure
resolvability) — so when C1/R2 activates that path, its confidence will be *un-calibrated* for exactly
this reason, and the quality suite will (correctly) flag it. Extend the adjudicator's `g` the same way
**in that deliberate R&D session** — not now (flipping/altering flag-OFF R&D is a separate decision).

## Alignment drift gauge (A1, Track A) — the blessed fixed points + re-bless rituals

The drift gauge `D(t) = d(μ(s_t), B)` (`eval/drift.py`, BUILD-SPEC §15, gap G4) measures how far the
system's behavioral profile (golden-set capability rates ⊕ Constitution conformance) has drifted from
the frozen anchor. It is **detection only** — it computes a number; it changes nothing. It is consumed
by the gate's validate step (the real `D ≤ Θ` conjunct) and by the F4 trajectory harness. Two of its
inputs are **owner-blessed frozen fixed points** in `eval/golden/baseline.json` → `drift` (Invariant 9
— edited only by you, on purpose, logged; structurally outside the self-mod lever set):

- **Θ (`drift_tolerance`, shipped 1.0)** — the tolerance band. It is a placeholder until the **F4**
  longitudinal harness plots D(t) on known corpora; calibrate Θ against those observed curves the same
  way you'd tune γ/λ/σ, then re-bless the value here. Never auto-tuned.
- **Per-axis tolerances (`recall_tol`/`overlap_tol`/`distance_tol`)** — one "tolerance-unit" of
  deterioration on each capability axis; the normalization that makes D meaningful. Re-tune with Θ.
- **`constitution_fingerprint`** — the frozen-anchor identity of `CONSTITUTION.md` (sha256). The gauge
  hard-trips (D=∞, out of band) if the live Constitution doesn't match it. **Whenever you deliberately
  amend the Constitution** (a §V human-only act), re-bless this:

```sh
# 1. amend CONSTITUTION.md (deliberate, logged — §V), then recompute its identity:
uv run -c "from core.constitution import constitution_fingerprint as f; print(f())"
# 2. paste the new hash into eval/golden/baseline.json -> drift.constitution_fingerprint
# 3. re-run the golden set against the new anchor and re-bless baseline.json -> metrics if needed.
#    (Skipping step 2 is fail-safe, not fail-dangerous: every drift reading hard-trips until you do.)
```

Nothing here is wired to act: the gate that consumes `D ≤ Θ` is the self-mod loop, which is flag-OFF
by default. The gauge is live as a *measurement* the moment you call it.

---

## ⚠️ Provenance spectrum split — one-time data migration (Track B / B0, owner-operated)

Track B split the single `authored` provenance into `authored-solo` + `authored-dialogue` and added
`curated`. **Rows written before this change carry the literal string `"authored"`, which is no longer
in `MIRROR_READABLE`** — so until you migrate, the mirror (Librarian retrieval, the dreamer, the
Ambassador) sees those notes as *not* mirror-readable and your live mirror reads effectively EMPTY.

This is a **same-trust-tier relabel** (`authored` → `authored-solo`; both are mirror-readable), NOT a
promotion across the §8 firewall — so it's a safe deterministic migration, not a gated change. It is
**idempotent** (a second run changes nothing). On this machine the dry-run counted real legacy rows
(vectors + catalog), so this DOES need to run once:

```sh
# 0. Your nightly restic snapshot is the safety net; optionally take a fresh one first.
# 1. DRY RUN — counts the legacy 'authored' rows in the vector store + catalog, mutates nothing:
uv run scripts/migrate_provenance_split.py
# 2. APPLY — relabel 'authored' -> 'authored-solo' in BOTH stores (idempotent, re-runnable):
uv run scripts/migrate_provenance_split.py --apply
# 3. confirm the mirror is back: a query should return your notes again
uv run scripts/talk.py            # ask "what did I write about <topic>?"
```

(The DerivedStore is `interpreted`-only and the raw/attestation stores carry no `authored` literal, so
only the vector store + catalog need relabeling — both covered by the script.)

---

## Talking to the system — the Ambassador (Track B, owner-operated)

The Ambassador is the conversational front door: a reasoning agent on the always-warm pinned tier that
reads your mirror, reads its own operational state, captures the dialogue as `authored-dialogue`, and
delegates heavy work — **read + propose, never write + act**.

```sh
# Day-one surface (no daemon, no network decision) — an in-process REPL over the real path
# (adapter → gateway → filesystem handoff → core inbox → Ambassador):
uv run scripts/talk.py                 # LIVE: needs Ollama + a migrated, ingested vault
uv run scripts/talk.py --offline       # deterministic demo, throwaway store, no Ollama

# So it can answer "how do you work?" / "is my data safe?" — ingest its OWN docs as the `curated`
# self-knowledge graph (own graph, never merged into the mirror; needs Ollama for embeddings):
uv run scripts/ingest_self_knowledge.py
```

What it does each turn: reasons about intent (deterministic floor for the obvious cases, the model
earned for the rest) → **retrieve** (mirror) / **explain** (curated) / **status** (plain-language
operational narration) / **task** (delegate → gate → queue, "give me a bit", result surfaced on a
later turn) / **capture** (store + acknowledge). The unprompted-message dial is
`[ambassador] interruption_sensitivity` (off | earned_only | verbose; default earned_only).

**Optional follow-up (not built — your call):** a tiny stdlib-only local HTTP front end reachable over
Tailscale, following `LocalAdapter`'s "loopback/Tailscale" framing, so you can talk to it from your
phone. The CLI above is sufficient to use it today; standing up a reachable daemon is an operational/
exposure decision left to you, not something this build turns on.

To run it as a scheduled service (instead of the in-process REPL), use the one-command launcher
below — it runs the full supervisor (which includes the `ambassador_task` delegated-work handler),
so delegations from `talk.py` are completed by the running daemon.

---

## Deploy — the promotion gate (owner rule 2026-07-11)

Code/infra reaches the always-on system only through `mind-palace deploy` — never a hand kill.
The gate refuses: no live run, dirty tree, off-main, HEAD already live, or a red ratchet
(`--skip-tests` is the emergency hatch). Then it drains gracefully and, under launchd
KeepAlive, the exit IS the restart: the successor run comes up on the new code and deploy
verifies its pinned SHA (loud failure if it lands in recovery). If the repo plist drifted
from `~/Library/LaunchAgents/`, deploy does the full bootout → cp → bootstrap instead, so
plist changes ship the same way code does. **Corollary: under KeepAlive, `palace stop`
means restart** — a true stop is `launchctl bootout gui/$(id -u)/com.mind-palace.palace`.
Rollback = `git revert` + `deploy` again; the run ledger keeps every stretch pinned to its
commit, so "what was live when" is always answerable.

## One-command lifecycle — `palace start | stop | status | reset` (owner-operated)

`scripts/palace.py` runs the **whole mind-palace as one supervised process** — the supersession of
the standalone `scripts/watch.py` / `com.mind-palace.watch` agent. It manages our own components and
*verifies* the externals (Vault, Ollama, podman) fail-closed; it does NOT start/stop those (they keep
their own LaunchAgents).

**`mind-palace` is on PATH** (`/opt/homebrew/bin/mind-palace` → `bin/mind-palace`, the dispatcher for
every owner-facing script — see the quick-reference above and `mind-palace help`) — `start`/`stop`/
`status`/`reset` pass straight through to `scripts/palace.py`, runnable from any directory:

```sh
mind-palace status            # preflight checklist + recent runs
mind-palace start             # the full system, foreground (Ctrl-C = drain)
mind-palace stop               # graceful drain of the live run (from another shell)
mind-palace reset --confirm   # the fresh-start corpus wipe (see below)
```

**What `start` does:** seals the core → preflight (ensure data dirs; verify Ollama up, Vault
unsealed, podman present — a required ✗ refuses the start, `--force` overrides) → records a **run
pinned to the current git commit** in `data/runs.sqlite` → enqueues a catch-up vault sync (reconciles
notes changed while down; rebuilds an empty cache) → supervises the queue + vault watcher (auto-ingest;
trough dream/curate; delegated Ambassador tasks). On **SIGTERM/SIGINT** it stops claiming new work, lets
the in-flight job finish at its boundary (the scheduler is cooperative), and marks the run **clean** —
the graceful shutdown / ASG-style lifecycle hook. State lives in the stores/files, so the next `start`
just resumes.

**Recovery:** if the previous run never marked itself stopped (crash / `kill -9` / power loss), `start`
comes up in **recovery mode** — scheduler halted, watcher off, read-only — and asks you to inspect, then
`start --force` to resume. (The full graduated tamper response is Track A / A4; this is the boot-time
fail-closed half.)

**How self-mod knob changes persist across runs** (your question): the tuned value is written to the
`config/levers.toml` overlay (merged `defaults ← levers.toml ← local.toml`, so your `local.toml` always
wins and deleting `levers.toml` reverts every knob); the propose→approve→validate→rollback *history* is
the SQLite ledger `data/selfmod_ledger.sqlite`. No new store — a restart re-reads `levers.toml` and picks
up exactly where it left off. The **run ledger** adds which commit each run executed under, so a tuned
knob can be correlated to the run/commit it was tuned during.

**Always-on daemon:** install `ops/lifecycle/com.mind-palace.palace.plist` (header has the exact
`launchctl bootstrap` / `bootout` commands, including retiring the old `com.mind-palace.watch`). Logs at
`data/logs/palace.{out,err}.log`. `ExitTimeOut=120` is the drain window before launchd escalates to KILL.

### Fresh start — wipe the corpus + re-export notes (executed 2026-06-29; re-runnable)

`palace reset` surgically wipes the **corpus + derived layer** (raw, vectors, vault catalog, the now-
stale attestation chain, the queue) and is hard-guarded to **never** touch the production Vault Raft
store (`data/vault`), the run/self-mod ledgers, telemetry, backups, or logs. It refuses while a run is
live. Sequence for a clean re-export onto the new Synctrain-over-Tailscale setup:

```sh
launchctl bootout gui/$(id -u)/com.mind-palace.watch 2>/dev/null   # stop the old watcher first
mind-palace reset --confirm                                       # hard-wipe the corpus (restic = net)
# re-export your notes into ~/.mind-palace/vault/janus_notes/ and point Synctrain there
mind-palace start                                                 # re-ingests everything as authored-solo
```

`[vault] path` is set to `~/.mind-palace/vault/janus_notes` (config/local.toml) so only that synced
subdir is ingested — old/stray files in the vault root are ignored. A fresh re-ingest tags everything
`authored-solo` natively, so the provenance-split migration is **not needed** after a reset.

### Remote dashboard + chat — the edge monitor over Tailscale (owner-operated)

palace supervises a SEPARATE child process (Invariant 2 — network-facing can't share the sealed core)
that serves a small dashboard + chat surface. It reads the core-emitted status snapshot and relays chat
over the interface handoff; it never imports core or reads a store. **Off by default.** To turn it on,
add to `config/local.toml` and bind to this Mac's **Tailscale IP** (the tailnet is the auth boundary —
do NOT use `0.0.0.0`):

```toml
[monitor]
enabled = true
host = "100.x.y.z"     # this machine's Tailscale IP (`tailscale ip -4`); 127.0.0.1 = local-only
port = 8787
```

Then `palace start` spawns it (you'll see `↳ started child 'monitor'`); open `http://100.x.y.z:8787`
from your phone on the tailnet. `GET /` = dashboard (health, run/commit, activity, queue, dream counts,
auto-refreshing), `POST /chat` = talk to the Ambassador (same five paths as `talk.py`). palace restarts
it if it dies and SIGTERMs it on a graceful stop. Run it standalone for a quick look:
`uv run scripts/monitor.py`. The snapshot is metadata only — **no note text crosses to the
network** (only counts + the *shape* of activity). It is deliberately NOT sealed (Zone B).

---

## Code-execution sandbox — libraries, data-piping, WASM (BUILD-SPEC §11, owner-operated)

Executed code is **powerless** (Invariant 4): network-off, vault-less, non-root, read-only rootfs,
resource-limited, wall-clock-bounded. As of 2026-06-29 the isolation is **empirically verified**
(`pytest -m podman` → 7 live tests: runs code, network off, vault unreachable, timeout, non-root,
**data-in works**, vault-still-unreachable-with-data). Prerequisite: the podman machine running
(`podman machine start`).

**Pipe data IN, get results OUT.** An agent (or you) hands the sandbox a dataset and gets the
computed result back — data in, data out, never creds/vault/host-fs. Inputs land at
`/tmp/input/<name>` (carried in-band on stdin, *not* a host mount, so the vault stays structurally
unreachable). Use it directly:

```sh
echo 'import numpy as np; print(np.arange(5).sum())' | uv run scripts/sandbox.py -
uv run scripts/sandbox.py analysis.py --input series.csv=~/data/series.csv --timeout 30
# inside analysis.py:  open('/tmp/input/series.csv')  → your data
```

**Scientific libraries.** The default image is `python:3.12-slim` (stdlib only, so a fresh clone
works). For numpy / scipy / pandas / scikit-learn / cryptography, build the libs image once (slow —
it downloads the wheels, which are then baked in so the sandbox needs NO network at run time):

```sh
./scripts/build_sandbox_image.sh                 # -> mind-palace-sandbox:latest
#   then in config/local.toml:
#   [sandbox]
#   image = "mind-palace-sandbox:latest"
```

This is exactly the seam a future correlator / data-analyst agent uses to find patterns in
observed/IoT data and cross-check the knowledge graph (the DANGLING item #2 in `docs/WIRING-AUDIT.md`
— the sandbox is ready; the autonomous agentic driver is Track D).

**WASM substrate (optional, strongest isolation — isolation by absence of syscalls).** The
`WasmRunner` + `RoutingRunner` are real (wasmtime is installed). To activate the pure-compute WASM
path, place a WASI build of CPython and point config at it:

```sh
# 1. (already done) pip install wasmtime  — into .venv
# 2. obtain a WASI python (a python.wasm) and place it, e.g. ~/.mind-palace/python.wasm
# 3. config/local.toml:
#    [sandbox]
#    runtime = "routing"                       # WASM for pure-compute python, else podman
#    wasm_module = "~/.mind-palace/python.wasm"
```

Until a `python.wasm` is placed, `WasmRunner.available()` is False and `routing` falls back to the
verified Podman substrate — fail-closed, never a silent wrong-substrate run. `runtime="podman"`
(the default) ignores WASM entirely.
