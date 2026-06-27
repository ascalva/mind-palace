# Runbook

Operational notes for running and verifying the mind-palace. Grows per phase.

## Prerequisites (Phase 0)
- Python 3.11+ (built/verified on 3.14). Local venv at `.venv`.
- Ollama running on loopback (`127.0.0.1:11434`).
- Models: `qwen3.5:2b` (pinned, pulled). `qwen3.5:9b` / `qwen3.6:27b` are pulled as
  Phases 1–2 need them; `qwen3.6:35b-a3b` (stretch) already present.

## Setup
```
python3 -m venv .venv
./.venv/bin/pip install duckdb psutil pytest ruff
```

## Verify Phase 0
```
./.venv/bin/ruff check .
./.venv/bin/pytest -q              # full suite (skips live if Ollama down)
./.venv/bin/pytest -q -m "not live"   # logic-only, no Ollama needed
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

## Sandbox runtime — Podman machine (Phase 4) — ⚠️ KNOWN ISSUE, REVISIT

The Phase 4 sandbox (`core/sandbox/`) runs code in rootless Podman. On macOS Podman needs
a Linux VM ("podman machine"). The **logic gate is fully met by construction** — the
isolation profile is asserted on the argv (`tests/test_sandbox_policy.py`) and the
pool/broker behavior with a fake runner (`tests/test_sandbox_*.py`), all passing. What is
**not yet done is the empirical run** (`pytest -m podman`), because no podman machine would
stay up on this host (2026-06-25).

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
3. Empirically verify isolation: `./.venv/bin/pytest -m podman`
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
./.venv/bin/python scripts/watch.py     # seals the core, then watches [vault].path
```
Real-time via `watchdog` (FSEvents) if installed (`./.venv/bin/pip install watchdog`); without
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
./.venv/bin/python scripts/purge_raw.py --list                 # show purgeable (tombstoned) digests
./.venv/bin/python scripts/purge_raw.py <digest> --confirm     # destroy raw + derived for it
```

### Verify
- Edit a note → its embeddings update (search reflects the new content; old rows gone).
- Delete a note → it stops surfacing in search; raw blob is retained until a purge.
- Unchanged re-scan → no-op (no new digests, no duplicate rows).
- `./.venv/bin/python -m ops.import_lint` → green (the watcher reaches no network).
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
# plist ProgramArguments: [ .../scripts/run_with_secrets.sh, .../.venv/bin/python, .../scripts/watch.py ]
```

A secret that isn't placed yet just resolves to `None` — the corresponding layer stays off,
fail-closed where it matters (see §1). Place only the ones whose layer you're turning on.

### 1. Attestation signing keys — turn on the signed runtime-proof layer

Activates Ed25519 signing inside `StoreAttestor.emit` (records become tamper-evident). The
committed `ops/attestation/*.pub` are **DEV** keys with no production trust — replace them:

```sh
./.venv/bin/python scripts/gen_attestation_keys.py supervisor   # prints a base64 seed; rewrites supervisor.pub
./.venv/bin/python scripts/gen_attestation_keys.py owner         # prints a base64 seed; rewrites owner.pub
security add-generic-password -U -a mind-palace -s attestation-signing-key -w   # paste the supervisor seed
security add-generic-password -U -a mind-palace -s attestation-owner-key   -w   # paste the owner seed
git add ops/attestation/supervisor.pub ops/attestation/owner.pub && git commit   # pubs are public
```

Then set `[attestation] enabled = true` in config. Turning it on **without** a placed signing key
is a hard error (`AttestationKeyMissing`, fail-closed) — never a silent unsigned run. The owner
seed signs **gate decisions only** (non-repudiable approval); the supervisor seed signs all other
agent attestations. Verify:

```sh
./.venv/bin/python scripts/verify_attestation.py --all     # every stored attestation's signature + chain
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
./.venv/bin/python -m pytest -m needs_vault -v             # seeds policies from ops/vault/policies/, asserts the join
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
./.venv/bin/python -m pytest -m needs_vault -v        # real Vault: scoped mint/read + out-of-policy denial (§2a)
./.venv/bin/python scripts/verify_attestation.py --all   # signatures + chains to authored leaves (§1)
./.venv/bin/python -m ops.import_lint                  # core/ still reaches no network, no hvac/boto3
```

Gate: a `dreamer` token reads `kv/oura-daily-aggregates` but is **denied** the financial key; the
supervisor token cannot read role secrets directly; emitted attestations verify and (when an action
runs under a minted token) carry that token's **accessor** — never the token (Step 5 join).
