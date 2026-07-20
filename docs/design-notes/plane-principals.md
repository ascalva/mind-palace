---
type: design-note
id: dn-plane-principals
status: draft               # draft → ratified → superseded.  draft→ratified is an OWNER-ONLY hand edit.
created: 2026-07-20
updated: 2026-07-20
links:
  - docs/design-notes/ouroboros-principal.md        # superseded target — stays ratified until the owner flips it
  - docs/findings/finding-0116.md                   # warrant — the exhaust write-owner conflict
  - docs/design-notes/exhaust-lane.md               # the reports writer this note re-homes
  - docs/design-notes/the-sacred-boundary.md
  - docs/design-notes/supersession-lifecycle.md     # the three-place relation this note instantiates
  - docs/design-notes/secrets-management-evolution.md
  - docs/design-notes/vault-runtime-auth.md
supersedes: dn-ouroboros-principal
superseded_by: null
warrant: finding-0116
---

# Plane principals — one OS user per plane

> Filed by a delegated design agent as `draft` (chat-side protocol). Ratification
> is a hand edit by the owner. Three-place supersession
> (`dn-supersession-lifecycle` shape): this note **supersedes**
> `dn-ouroboros-principal` on the **warrant** of `finding-0116`;
> `dn-ouroboros-principal` remains ratified and inspectable until the owner
> hand-flips it to `superseded` (A8 — the flip is never agent-performed).

## 1. Purpose and scope

`dn-ouroboros-principal` minted **one** new principal — `ouroboros`, the live
system — and drew the uid boundary between "ascalva builds the machine" and
"ouroboros is the machine running." finding-0116 showed that boundary is one
line short: exhaust has **two producer planes** (workflow writes build reports;
the system writes its own emissions), so a single new principal cannot carry the
plane model it itself articulated in §3.3 ("the uid separates planes, not agent
types"). [GROUNDED docs/findings/finding-0116.md:35-44]

The owner's decision (2026-07-20) generalizes rather than patches: **four OS
principals, one per plane** — least-privilege made physical, not conventional.
Both forks are answered and are not re-litigated here:

- `ascalva` — **the human** (personal login). Drives the system; owns none of
  the palace's private data ambiently.
- `ouroboros-work` — **the workflow plane**: the orchestrator + delegated
  builders/scribes (the Claude Code agents), the repo working tree, and owner
  of `~/.mind-palace/exhaust/reports/`. A **dedicated service user** (chosen
  over "ascalva = workflow"): agents run constrained *below* the human's login
  — no personal files, no vault, no network beyond what building needs.
- `ouroboros` — **the core plane**: the reasoning daemon + the vault (corpus).
  Vault RW including `doc_id`. No off-host network.
- `ouroboros-edge` — **the edge plane**: network-facing only, never the vault.
  **Created now** (forward-provision, chosen over park), even though edge is
  ~NONE today — the max reachable effector tier is NONE and the only edge
  surface is the Tailscale-local ambassador [GROUNDED finding-0011]. It guards
  little now; the model is complete the moment edge grows, and no future edge
  component can be born inside core for convenience.

**In scope:** the four principals, the ownership/mode matrix, the launch
ergonomics (how agents come to run as `ouroboros-work`), the kernel enforcement
of non-negotiable #2, the structural resolution of finding-0116, and
re-graduation guidance for bp-076. **Out of scope:** the exhaust lane's
layout/format/writer (`dn-exhaust-lane`, unchanged) and everything §2 retains.

## 2. What still holds — retained by reference, not restated

The superseded note's load-bearing reasoning survives intact; this note
generalizes its conclusion, not its arguments:

- **§2 Threat model** — protects against processes in the owner's login
  session; does not protect against root; `sudo` is the honest, deliberate,
  logged escape hatch. Applies verbatim, now with a sharper corollary: the
  *agents themselves* move out of the ascalva session, so the "supply-chain
  compromise under ascalva" surface no longer includes every agent run.
- **§3.1 Role-account mechanics** — hidden role account, no login window, real
  home, shell present, password disabled, owner-created via
  `sysadminctl`/`dscl`. Now applied ×3 (`ouroboros`, `ouroboros-work`,
  `ouroboros-edge`).
- **§3.2 The daemon moves** — LaunchAgent → LaunchDaemon (`UserName
  ouroboros`); Syncthing moves with it; `vault-unseal.sh` and the unseal
  keychain item migrate. Unchanged. [GROUNDED ops/lifecycle/launcher.py:110-121
  (gui/$UID bootstrap), :316-317 (installed LaunchAgent plist)]
- **§3.3 Planes, not agent types** — in-system agents (dreamers, librarian,
  interpreters) are daemon components and inherit `ouroboros`; the constitution
  frame bounds what an agent *may* do, the uid bounds what its process *can*
  do. Unchanged — except its final paragraph: the core-vs-edge boundary it
  deliberately did NOT kernel-enforce, and parked as "edge as a third
  principal," is **un-parked and resolved here** (§3.4 below).
- **§3.5 Execution protocol** — owner-run, agent-authored, reversible; the
  runbook / verifier / ratchet triple. This note's build keeps exactly that
  shape, with the artifacts extended to four principals (§5).
- **§3.6 Sequencing** — `dn-exhaust-lane` (bp-075) first, migration second, at
  a calm moment. Unchanged.
- **Parked decisions** — personal-Syncthing split, ascalva drop-box,
  sandbox-beyond-uid, eval/live posture: all carried forward unchanged (§6).

What is superseded in substance: the **two-principal model** and the **§3.4
ownership table** (its uniform `exhaust = ouroboros-write-only` row is the
defect finding-0116 names).

## 3. Decision

### 3.1 The ownership/mode matrix — the plane boundary as filesystem facts

One shared group is minted: `palace` (members: `ascalva`, `ouroboros-work`) —
it exists solely to share **write** on the repo; nothing else needs a group.
Vault isolation needs no group (`0700` exact, as before: sync-in *is*
ouroboros once Syncthing moves). [DERIVED from dn-ouroboros-principal §3.4's
group-rejection argument, which still holds for the vault]

| Path | Owner:group | Mode | Writes | Reads |
|---|---|---|---|---|
| `~/.mind-palace/vault` (ingest) [GROUNDED config/defaults.toml:46] | `ouroboros:staff` | `0700` | ouroboros only (incl. `doc_id`; sync-in is ouroboros) | ouroboros only |
| `~/.mind-palace/exhaust/` (parent) | `ouroboros:staff` | `0755` | ouroboros (creates emission subdirs) | anyone local |
| `~/.mind-palace/exhaust/reports/` | `ouroboros-work:staff` | `0755` | **ouroboros-work** (orchestrator via `scripts/exhaust_report.py`) | anyone local, incl. sync-out (ouroboros) |
| `~/.mind-palace/exhaust/<system-emissions>/` (dreams, digests, …) | `ouroboros:staff` | `0755` | ouroboros only | anyone local |
| repo working tree (incl. `.claude/worktrees/`) | `ascalva:palace` | `2775` dirs / `664` files | ascalva (hand edits, blessings) + ouroboros-work (agents) | anyone local (no secrets in the repo — #10) |
| repo `data/` runtime substrate (logs, runs db) | `ouroboros:palace` | `0755` | the daemon | anyone local (cockpit tails `data/logs/palace.out.log` [GROUNDED scripts/cockpit.sh:26]) |
| interface handoff dir (`cfg.interface.handoff_dir`) | `ouroboros-edge:palace-io` (provisional) | `2770` | edge enqueues; core consumes | the two planes only |
| network sockets | — | — | **ouroboros-edge** only (see §3.4; workflow keeps dev egress) | — |

Three rows carry flags for the re-graduated bp-076 to ground (§5):

- **`data/`** — a real conflict this note surfaces: the daemon writes runtime
  state *inside* the repo tree (`data/logs/`, the runs DB), so a
  workflow-owned repo with a core-owned `data/` needs either the `chown` above
  or relocation of runtime state into the ouroboros home. [INFERENCE — exact
  inventory of what writes under `data/` is bp-076 §3 grounding]
- **The handoff dir** — the ambassador is wired *inside* the daemon today
  [GROUNDED ops/lifecycle/launcher.py:150,227-228: `build_ambassador` feeding
  `CoreInbox(handoff=cfg.interface.handoff_dir)`]. When the network-facing
  half moves to `ouroboros-edge` (§3.4), that dir becomes the **airlock**: the
  only thing edge and core share is a spool of typed files — no shared
  network, no shared uid. Group `palace-io` (members: `ouroboros`,
  `ouroboros-edge`) is provisional; deliberately NOT `palace`, so workflow
  cannot forge edge input to core. [DERIVED]
- **Traversal** — role accounts must traverse `/Users/ascalva` to reach
  `~/.mind-palace`. macOS defaults grant `o+x` on homes, but the runbook must
  *verify* it (else: an ACL grant or relocating `~/.mind-palace`).
  [INFERENCE — the superseded note glossed this; verification line required]

Repo mechanics for the shared row: `git config core.sharedRepository=group`,
setgid dirs, umask `002` in both principals' sessions. [DERIVED — standard
git shared-repo practice; bp-076 pins the exact incantations]

### 3.2 The ergonomics — how agents come to run as ouroboros-work (the crux)

Today the human runs `./scripts/cockpit.sh`, whose right pane launches
`claude --model 'opus[1m]' --effort medium --permission-mode auto` as
`ascalva` [GROUNDED scripts/cockpit.sh:73]; delegated builders are spawned by
that orchestrator as subprocesses in repo worktrees.

**Decision: the cockpit launches the orchestrator under the service user; the
human stays ascalva.** The claude pane becomes:

```
sudo -u ouroboros-work -H claude --model 'opus[1m]' --effort medium --permission-mode auto
```

- **The interactive orchestrator session runs as `ouroboros-work`.** `sudo -u`
  in a tmux pane is an ordinary TTY process; Claude Code neither knows nor
  cares. `-H` points HOME at the service user's home, so the agent gets its
  *own* `~/.claude` (Claude Code config, its OAuth credential, projects,
  memory) — the *Anthropic* credential separates from the human's, which is the
  isolation worth having.
- **Git identity is a SEPARATE axis, deliberately NOT isolated (owner decision,
  2026-07-20).** The uid governs filesystem/network; commit identity + signing
  are orthogonal — git reads `user.email`/`user.signingkey` from the
  **repo-local** `.git/config`, which overrides `$HOME`. So agent-authored
  commits keep the human's identity and are signed with the human's key: they
  stay `Alberto <…>` and **Verified**, exactly as today (the owner runs verified
  commits; nothing about that view changes). This is status-quo — everything
  runs as the human today, so agent commits are already Alberto-signed; the uid
  split does not regress it. **Accepted residual:** `ouroboros-work` must be able
  to *read the human's signing key* to sign — a modest leak (a compromised
  workflow agent could sign a commit as the human), knowingly accepted because
  (a) it is already true today, (b) the signing key is not a crown jewel (the
  vault is, and that stays `0700 ouroboros`), and (c) the alternative — a
  separate verified bot identity — was weighed and rejected in favor of the
  human's name on the history. bp-076 §3 grounds the exact key path + how the
  `ouroboros-work` session accesses it (SSH-signing key file readable by the
  user, or GPG agent), and sets `user.email`/`user.signingkey`/`commit.gpgsign`
  in repo-local config so identity is HOME-independent.
- **The human stays `ascalva`** in every other pane: the vim/docket pane, hand
  blessings, `palace bless`, hand commits. Daily flow is unchanged — still one
  command, `./scripts/cockpit.sh`; the sudo is inside the script.
- **Delegated builders inherit `ouroboros-work` for free**: they are child
  processes of the orchestrator, and their worktrees live under the
  group-shared repo (`.claude/worktrees/`). No per-builder mechanism exists or
  is needed. [DERIVED — process-tree uid inheritance]
- **Sudoers**: `ascalva ALL=(ouroboros-work) NOPASSWD: ALL`. This is a
  *descending* grant — the target principal is strictly weaker than the
  grantor — so NOPASSWD's blast radius is "ascalva can act as a user with
  less authority than ascalva," which is the entire point. [DERIVED]

**Named costs**, honestly:

1. **Credential bootstrap (the sharpest edge).** Claude Code on macOS keeps
   its OAuth credential in the user keychain [INFERENCE]; a role account's
   keychain is not auto-unlocked by GUI login. One-time: authenticate claude
   as `ouroboros-work`. Recurring risk: a locked keychain at pane launch.
   Mitigations, in preference order: a `security unlock-keychain` line in the
   cockpit wrapper; or an `apiKeyHelper`/env-token credential path that skips
   the keychain. **bp-076 §3 must ground which mechanism Claude Code actually
   uses and pin one.**
2. **Shared-repo friction.** Mixed-owner files, umask discipline, occasional
   wrong-mode fixups. Bounded by setgid + `core.sharedRepository`; the
   verifier (§5) asserts the repo's group-write health.
3. **TCC.** Processes under `sudo -u` may hit macOS TCC prompts with odd
   attribution. The repo and `~/.mind-palace` are not TCC-protected locations
   [INFERENCE]; the runbook verifies by exercising the full agent flow once.
4. **Subscription/limits.** The service user's claude authenticates against
   the same owner account; usage pools are shared, only the OS identity
   differs. [INFERENCE — verify at bootstrap]

**Rejected alternatives**: (a) *orchestrator stays ascalva, only builders drop
privilege* — rejected by the owner's decision, and rightly: the orchestrator is
the most capable agent; leaving it ambient defeats the plane. (b) *a headless
ouroboros-work service the human talks to over a socket* — over-machinery for
a TTY tool; parked with re-entry (§6). (c) *ascalva = workflow, no fourth
user* — owner explicitly chose the dedicated user: the human's personal
authority and the agents' working authority must not be the same capability.

**What agents lose** (the payoff, stated as capabilities): as
`ouroboros-work`, an agent — and anything it spawns, and any supply-chain
compromise inside its toolchain — cannot read `~/Documents`, `~/.ssh`, the
human's keychain or browser profiles (per-user modes/TCC), cannot open the
vault (`0700 ouroboros`), and cannot touch core's runtime substrate except
read. Its writable world is: the repo (shared group), its own home, and
`exhaust/reports/`. That *is* the workflow plane, now enumerable by `ls -l`.

**What the split does NOT enforce** (mirroring the superseded note's §3.3
honesty): the blessing gates. The repo is group-writable by design, so an
errant agent process *can* still edit a ratified note file at the filesystem
level — `gate-guard`, A8 HEAD-keying, and the Stop-gate audit remain the
enforcement there, unchanged. And workflow keeps open egress (the API, git
push, `uv`) — a workflow compromise can still exfiltrate the *repo*, just no
longer the vault or the human's files. Both residuals are named, not hidden.

### 3.3 finding-0116 resolved structurally

The conflict — `dn-exhaust-lane` makes the orchestrator + `scripts/
exhaust_report.py` the reports writer (workflow plane), while
`dn-ouroboros-principal` §3.4 made exhaust `ouroboros`-write-only — dissolves
because the matrix has one owner **per producer plane**: `exhaust/reports/` is
`ouroboros-work`-owned (workflow writes its own artifact class), system
emissions stay `ouroboros`-owned. This is the finding's Option A, generalized:
"workflow-plane-owned" lands as the dedicated `ouroboros-work`, not `ascalva`,
because the owner minted a real user for that plane. No cross-plane handoff,
no shared write group on exhaust, no amendment to a ratified note by an agent
— the supersession itself carries the fix. [GROUNDED
docs/findings/finding-0116.md:56-61 (Option A + recommendation)]

### 3.4 Non-negotiable #2 becomes a kernel fact

CONSTITUTION §II.1: "private data and network access never live in the same
component." Today that is enforced at the *source* level — the import firewall
(`scripts/check_imports.py`) proves `core/` imports nothing network-touching —
which is review-time enforcement of a runtime property. The four-user split
makes it a **kernel fact**, enforced from both directions at runtime:

- **Edge cannot reach the vault**: `ouroboros-edge` ≠ `ouroboros`, and the
  vault is `0700 ouroboros`. The kernel's DAC check denies the open. No code
  path, no import, no bug in edge can cross it short of a kernel exploit or
  root. [DERIVED]
- **Core cannot reach the network**: a pf anchor keyed on uid —
  `block drop out quick proto { tcp udp } user ouroboros` — with a
  `pass quick on lo0` carve-out **before** it, because core legitimately
  speaks localhost to the resident model servers; "sealed" means zero
  *off-host* egress. The same block covers listening (pf `user` matches the
  socket's effective uid in both directions). [DERIVED — pf user-matching is
  TCP/UDP-scoped; the loopback carve-out is an [INFERENCE] about local model
  serving that bp-076 §3 verifies against the running daemon]

The two directions compose: the component holding private data has no network;
the component holding the network has no private data; and they are different
uids, so no single process can ever hold both. The import firewall does not
retire — it stays as the cheap, pre-runtime tripwire (defense in depth; it
catches the violation at review, the kernel catches it at execution). This is
the superseded note's §2 "deeper payoff" carried to completion, and the same
move as the core-seal reckoning: stop trusting posture, make the property
physical. [ANALOGY — structural-enforcement]

The edge plane's first tenant: the ambassador's network-facing half moves out
of the daemon tree into an `ouroboros-edge` LaunchDaemon, talking to core only
through the handoff-dir airlock (§3.1) — the seam already exists in the wiring
[GROUNDED ops/lifecycle/launcher.py:227-228]. If the re-graduation judges that
relocation too large for bp-076, it may be split out — but the *user* is
created unconditionally now, per the owner's forward-provision decision.

## 4. Consequences

- **bp-076 must be re-graduated against this note before it builds.** It was
  graduated from the two-principal model; the deltas are material: four users;
  `exhaust/reports/` ownership; the cockpit sudo launch + credential
  bootstrap; the pf anchor + loopback carve-out; shared-group repo mechanics;
  `data/` runtime ownership; the ambassador relocation (or its explicit
  deferral); ratchets extended per-plane. A journal note to this effect is
  filed in `docs/build-plans/bp-076/journal.md`; the plan itself is untouched
  (re-graduation is the orchestrator's, blessing the owner's).
- **The artifact triple** (runbook / verifier / ratchet, superseded note §3.5
  shape) extends per-plane. The ratchet becomes a matrix of negative asserts:
  from `ouroboros-work` posture, `os.access(vault, R_OK)` is False; from
  `ouroboros-edge` posture, vault unreadable; from `ouroboros` posture,
  off-host egress refused (pf); ownership/modes pinned to §3.1's table.
  Skip-with-reason before migration, enforced after — the self-configuring
  `stat().st_uid` gate from bp-076's graduation carries over per-path.
- **After migration**: any agent flow that assumed ascalva-ambient access
  surfaces immediately as a finding — that surfacing is a feature (it maps
  the sanctioned-interface gaps). Unchanged from the superseded note §4.
- `dn-secrets-management-evolution` / `dn-vault-runtime-auth` cross-references
  carry over (the unseal path's user still moves to `ouroboros`).

## 5. Parked decisions

Carried forward unchanged from `dn-ouroboros-principal` (defaults and
re-entry conditions as written there): **personal-Syncthing split** ·
**ascalva-side drop-box** · **sandbox/hardening beyond the user split** ·
**eval/live-test posture**. Un-parked and resolved by this note: **edge as a
third principal** (now the fourth, `ouroboros-edge`, created immediately).

New parks:

- **pf-restricting `ouroboros-work` egress to an allowlist** (API endpoints,
  git remotes, package indexes). Default: open egress — building needs the
  network, and the vault/personal-file walls are what the plane is for.
  Re-entry: a workflow-side supply-chain incident, or the owner wants the
  tighter posture.
- **A headless orchestrator service** (ouroboros-work daemon the human
  addresses over a local socket, instead of sudo-in-a-pane). Default: the
  sudo launch — one line in the cockpit, zero new machinery. Re-entry: Claude
  Code grows a client/server split, or the sudo/keychain friction (§3.2 cost
  1) bites in practice.
- **uid provenance on blessing edits** (could an owner hand-edit be
  distinguished forensically from an agent edit by uid?). Default: no — git
  records author strings, not uids, and the repo is group-writable; the
  existing hook/audit gates remain the enforcement. Re-entry: a laundering
  incident that the HEAD-keyed A8 guard fails to catch.

## Cross-references

- Superseded: `docs/design-notes/ouroboros-principal.md` (ratified; owner
  flips to `superseded` by hand — its §2, §3.1–§3.3, §3.5–§3.6 retained by
  reference, §3.4's table replaced by §3.1 here)
- Warrant: `docs/findings/finding-0116.md` (resolved by this note)
- Supersession shape: `docs/design-notes/supersession-lifecycle.md` §2
  (proposed → certified; ratification is the verdict)
- Reports writer: `docs/design-notes/exhaust-lane.md` (writer + naming
  unchanged; only ownership of `reports/` re-homed)
- Daemon lifecycle: `ops/lifecycle/launcher.py:110-121, 150, 227-228, 316-317`
- Cockpit launch: `scripts/cockpit.sh:64-75`
- Import firewall (retained as defense-in-depth): `scripts/check_imports.py`
- Kinship: `dn-the-sacred-boundary` (capability-dissolution — the vault-read
  capability is not guarded but *absent* from three of four principals);
  `structural-enforcement` (memory); CONSTITUTION §II.1/.2/.5,
  non-negotiables 1 · 2 · 3 · 10 · 11
