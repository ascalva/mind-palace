---
type: design-note
id: dn-ouroboros-principal
status: superseded            # draft → ratified → superseded.  draft→ratified is an OWNER-ONLY hand edit.
created: 2026-07-19
updated: 2026-07-19
links:
  - docs/brainstorms/exhaust-and-ingest-sync.md    # capsule 2 — the permission rules + grounding
  - docs/design-notes/exhaust-lane.md               # the mechanical companion (separate build)
  - docs/design-notes/the-sacred-boundary.md
  - docs/design-notes/secrets-management-evolution.md
  - docs/design-notes/vault-runtime-auth.md
supersedes: null
superseded_by: dn-plane-principals
warrant: null
---

# The Ouroboros principal — the live system as its own OS user

> Filed by the chat agent as `draft` (chat-side protocol, §8). Ratification is a
> hand edit by the owner — no command performs it. `/graduate` refuses this note
> until `status: ratified`.

## 1. Purpose and scope

Make Ouroboros (the live system: daemon + evolving corpus) a **distinct
least-privilege OS principal** — a dedicated `ouroboros` user — instead of
running as the owner's interactive login. Grounded current state (verified
2026-07-19): no `ouroboros` user or group exists; the daemon, Syncthing, the
vault, and `~/.mind-palace` are all `ascalva:staff`; the daemon is a launchd
**LaunchAgent in the GUI session** (`ops/lifecycle/launcher.py:312-317`,
`~/Library/LaunchAgents/com.mind-palace.palace.plist`).

The owner's two rules (capsule 2), which this note turns into structure:

1. **Ingest** (the vault): read AND identity-write (`doc_id`/dedup markers,
   `dn-ingest-identity-and-amendment`) belong to `ouroboros` **only**.
2. **Exhaust**: write belongs to `ouroboros` **only**; others read.

**In scope:** the principal, what runs as it, ownership/modes of the two lanes,
the launchd and Syncthing consequences, secrets migration, the execution
protocol (owner-run, agent-authored), and the structural proof. **Out of
scope:** the exhaust lane's layout/format/writer (`dn-exhaust-lane` — lands
first, ownership-agnostic).

## 2. Threat model, stated honestly

This protects the corpus from **processes running in the owner's login
session** — browsers, dev tools, every `pip install`, any supply-chain
compromise under `ascalva`. That is the overwhelming practical attack surface,
and today all of it can read the vault. It does **not** protect against root or
physical access (the owner is an admin; `sudo` can always read — that is the
honest escape hatch, and it is a feature: owner access is deliberate,
elevated, logged-by-macOS, never ambient).

A second, deeper payoff: several constitution lines that are today enforced by
convention become **OS-enforced facts**. Agents run as `ascalva`; after this
change an agent (or anything it spawns) *cannot* open the vault — "network and
private data never share a component" and "the model never holds raw secrets"
gain a kernel-level backstop. This is the same move as the core-seal reckoning
(`structural-enforcement`): stop trusting posture, make the property physical.

## 3. Decision

### 3.1 The principal

Mint `ouroboros` as a macOS **hidden role account**: no login window presence,
no admin rights, a real home (`/var/ouroboros` or similar) for its keychain and
Syncthing config, shell present (launchd needs to exec), password disabled
(access via `sudo -u ouroboros` only). Created by the owner with
`sysadminctl`/`dscl` per the runbook (§5).

### 3.2 What runs as ouroboros — the daemon moves (rule 1 forces it)

Ingest readable by ouroboros **only** means every corpus-touching process must
run as ouroboros — there is no half-step where the vault is `0700 ouroboros`
and an `ascalva` daemon still reads it. Therefore:

- **The palace daemon runs as ouroboros.** Mechanically: the LaunchAgent
  becomes a **LaunchDaemon** (system domain, `UserName ouroboros`) — a role
  account never logs into a GUI session, so a LaunchAgent would simply never
  start for it (`launcher.py`'s `gui/$UID` bootstrap logic is the part that
  changes). Side benefit: the daemon stops depending on the owner being logged
  in.
- **Syncthing moves to ouroboros** and carries both shares (vault in, exhaust
  out). Grounding: the current instance serves exactly one real share — the
  vault — so this is a relocation, not a split. *Assumption for the owner to
  confirm at ratification: this Syncthing serves nothing personal.* (If it
  does: second instance under ouroboros instead; parked below.)
- **`vault-unseal.sh` and Vault runtime auth move with the daemon** — the
  unseal secret lives in a per-user keychain today, so it migrates to
  ouroboros's keychain (`dn-secrets-management-evolution` §Keychain applies;
  the plan's §3 must ground the exact `security` item and its ACL).
- **What stays ascalva:** the repo, Claude/agent sessions, the cockpit, eval
  runs against non-corpus fixtures — the whole *interface and development*
  plane. The boundary in one line: **ascalva builds the machine; ouroboros is
  the machine running.**

### 3.3 Agents and the principal — the taxonomy nests inside the planes

The uid boundary separates **planes**, not agent types (owner question,
2026-07-19). Workflow agents (orchestrator / builder / scribe — Claude Code
sessions) act on the repo and run as `ascalva`. In-system agents (the
dreamers, the librarian, the interpreters, the ambassador) are **components of
the daemon** — spawned inside its process tree, reasoning over the corpus with
the local models — so they inherit `ouroboros` automatically when the daemon
moves. No per-agent arrangement exists or is needed: *ascalva builds the
machine; ouroboros is the machine running.*

Two layers, stated so neither is mistaken for the other: the **uid** bounds
what a *process can* do; the **constitution frame and scope signatures** bound
what an *agent may* do (bounded recursion, scope ceilings, minted-agent caps —
unchanged by this note, now running inside the ouroboros envelope). And one
boundary this note deliberately does NOT kernel-enforce: **core-vs-edge inside
ouroboros**. A network-touching edge component in the daemon's tree retains
OS-level vault-read *capability*; non-negotiable 2 remains enforced by the
import firewall (`scripts/check_imports.py`, Invariant 2), exactly as today.
The hardening that closes it — **edge as a third principal** — is parked below.

### 3.4 Ownership and modes of the lanes

| Path | Owner | Mode | Writes | Reads |
|---|---|---|---|---|
| `~/.mind-palace/vault` (ingest) | `ouroboros` | `0700` | ouroboros (incl. `doc_id`) + sync-in | ouroboros only |
| `~/.mind-palace/exhaust` | `ouroboros` | `0755` | ouroboros only | anyone local (incl. sync-out) |

With Syncthing itself running as ouroboros (3.2), sync-in *is* ouroboros —
rule 1 holds with no group compromise, `0700` exact. (The group+setgid
alternative from the capsule is thereby rejected: it softens "only reader" to
"the group", and it is unnecessary once Syncthing moves.) `~/.mind-palace`
(parent) becomes `ouroboros:staff 0755` so the exhaust share is traversable.

Note the owner's phone edits vault notes via SyncTrain — those writes arrive
*through* the ouroboros Syncthing, so phone capture is unaffected. Direct
`ascalva`-side edits to vault files stop working by design; the capture path
is the phone/sync or a sanctioned drop (parked below if ever wanted).

### 3.5 Execution protocol — owner-run, agent-authored, reversible

This is infra + a trust boundary: **every mutating step is performed by the
owner**, not an agent (no user creation, `chown`, launchd or keychain change
is ever agent-executed — consistent with "the model advises; code acts" and
the deploy rule). The build delivers three artifacts, none of which act:

1. **The runbook** — exact owner-run commands, ordered, each with a
   verification line and a rollback line (create user → migrate Syncthing →
   migrate keychain/unseal → install LaunchDaemon → chown lanes → bootout old
   agent). Non-negotiable 5's shape: gated → validated → reversible.
2. **The verifier** — a read-only script asserting the end-state (user exists,
   ownerships/modes exact, daemon running as ouroboros, agent-posture cannot
   read the vault) with a clear pass/fail per step, runnable mid-migration.
3. **The ratchet** — permanent tests: from `ascalva` posture, assert
   `os.access(vault, R_OK)` is **False** (skip-with-reason before migration,
   enforced after; the flip of that skip is the migration's acceptance);
   ownership/mode asserts pinned to the table above.

### 3.6 Sequencing

`dn-exhaust-lane` builds first (mechanical, ownership-agnostic). This note's
build follows as its own session; nothing else depends on it, and it can wait
for a calm moment — a botched step here interrupts the daemon, so the runbook
includes a `palace status`-verified restart at each stage.

## 4. Consequences

- **One careful build plan** (runbook + verifier + ratchet + `launcher.py`
  LaunchDaemon support + config for the ouroboros home). The plan's §3 must
  ground: the exact launchd bootstrap calls in `launcher.py`, the keychain
  item(s) `vault-unseal.sh` reads, and Syncthing's config/home relocation.
- Owner performs the migration from the runbook, step-verified.
- After migration: agents lose ambient vault read — any agent flow that
  assumed it surfaces immediately as a finding (that surfacing is a feature:
  it maps the sanctioned-interface gaps).
- `dn-secrets-management-evolution` and `dn-vault-runtime-auth` gain a
  cross-reference (the unseal path's user moved).

## Parked decisions

- **Edge as a third principal** (`ouroboros-edge`: network, no vault; core:
  vault, no network — non-negotiable 2 becomes kernel-enforced, not just
  import-firewall-enforced). Default: edge stays inside ouroboros, #2 enforced
  by `check_imports.py` as today. Re-entry: any effector tier rises above NONE
  (Track G wiring), or an edge component gains a listening/network surface
  beyond the Tailscale-local ambassador.
- **Personal-Syncthing split.** Default: move the single instance (it serves
  only the vault). Re-entry: owner reports personal shares on it → second
  instance under ouroboros instead.
- **An `ascalva`-side sanctioned drop-box for desktop capture** (write-only
  chute into ingest). Default: none — capture is the phone/sync path.
  Re-entry: the owner misses desktop capture in practice.
- **Sandbox/hardening beyond the user split** (sandbox-exec, App Sandbox,
  separate mount). Default: the uid boundary. Re-entry: threat model grows
  (multi-user machine, remote daemon exposure).
- **The eval/live-test posture** (some live tests exercise corpus paths).
  Default: they skip under ascalva post-migration exactly like the vault-read
  ratchet. Re-entry: a live-eval lane under `sudo -u ouroboros` if the skips
  bite.

## Cross-references

- Brainstorm: `docs/brainstorms/exhaust-and-ingest-sync.md` capsule 2
  (grounding: no ouroboros principal exists; all `ascalva:staff`)
- Daemon lifecycle: `ops/lifecycle/launcher.py:312-317, 453, 484-485`;
  `ops/lifecycle/com.mind-palace.palace.plist`
- Unseal: `ops/vault/vault-unseal.sh` (runs as ascalva today, pid observed)
- Ingest roots: `config/defaults.toml:46`, `config/local.toml:12`
- Kinship: `structural-enforcement` (memory), `dn-the-sacred-boundary`,
  non-negotiables 2 · 3 · 5 · 10 · 11
