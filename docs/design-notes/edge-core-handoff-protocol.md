---
type: design-note
id: dn-edge-core-handoff-protocol
status: draft
implementation: design-only   # nothing built; hardening + doorbell + adapter all specified, not coded
created: 2026-07-10
updated: 2026-07-10
links:
  - docs/research/security-planes.md
  - docs/design-notes/authorship-distance-axis.md
  - docs/design-notes/the-sacred-boundary.md
  - docs/design-notes/the-edge-model.md
  - docs/design-notes/live-adoption-and-longitudinal-harness.md
  - ops/import_lint.py
supersedes: null
superseded_by: null
warrant: null           # requires a warrant finding at ratification (§8, V-items resolved)
---

# Design note — The Edge–Core Handoff: capsule protocol, doorbell, and portability

*Family tag → family 3 (guarded transition systems) primary: the crossing is a
small automaton with a checked guard — fd-bound hash and signature verification —
before the side effect of admission to core. Family 1 (labelings & information-flow)
secondary: the permission diode is one-way flow control and capsules carry typed
provenance labels. Family 2 (regenerable derivation) secondary: capsule identity is
its content address `H(payload)`. See [`../NOTATION.md`](../NOTATION.md).*

**Status:** Draft for review; V-items (§8) unresolved, warrant pending at ratification.
**Origin:** Owner question — can the filesystem handoff be optimized without dissolving
its security properties? — worked through a survey of cross-domain-solution architecture,
the crash-consistency literature, macOS/APFS durability behavior, and Unix-domain-socket
credential mechanics (references §12).
**Placement:** `docs/design-notes/` as a hardening of the standing edge–core boundary;
does not modify the Librarian gate or the sealed-core doctrine.

---

## 0. Position

Zone A (sealed core) and Zone B (networked edge) communicate by filesystem
handoff, never shared imports. This note does not change that doctrine. It
does three things:

1. Names what the handoff *is* in the security literature (a software
   protocol break, the primitive high-assurance cross-domain solutions are
   built on), so its properties are defended deliberately rather than
   accidentally.
2. Specifies a hardened **capsule protocol** (commit discipline, durability
   tiers, content-hash naming, permission diode, TOCTOU rules) and a
   **doorbell wake path** that removes polling latency while carrying zero
   bits of payload.
3. Defines a **two-primitive platform adapter** so the protocol is not
   married to macOS. The current host is an M2 Max; future hardware may not
   be. Portability is achieved by designing to the weakest contract across
   target platforms, not by per-platform forks.

The unifying move is doctrinal: **notification is a latency optimization,
never a correctness mechanism.** Correctness lives entirely in the capsule
protocol and the sweep. Because every candidate notification primitive on
every platform is advisory under load, this doctrine is also what makes
portability cheap — platform differences in watchers can affect latency
only, never correctness.

---

## 1. What the handoff is

The filesystem handoff is a software **protocol break**. In cross-domain
solution (CDS) architecture — the defense/ICS lineage of this problem — an
import path terminates one transmission path, extracts information from the
data flow, and starts a new transmission path into the high domain,
stripping any live protocol context in between. Data diodes add hardware
enforcement of one-way flow; the software half of every serious CDS is a
guard that validates inert artifacts before admission. (References §12:
Oakdoor CDS primer; OPSWAT transfer-CDS architecture; ST Engineering
deployment guidance.)

The handoff gives four properties that most "faster" IPC silently discards:

| # | Property | Mechanism | What it defeats |
|---|----------|-----------|-----------------|
| P1 | Temporal decoupling | Core parses at its own chosen time; no live channel | Interactive probing of core by a compromised edge |
| P2 | At-rest inspection point | The Librarian gate runs on an inert artifact | Protocol-context smuggling; parser races |
| P3 | Persistent attributable object per crossing | One capsule = one file, hashable, Ed25519-signable | Deniable / unlogged influence; matches append-only doctrine for free |
| P4 | No shared failure domain | No shared memory, no shared library session, no RPC stack in core reachable from edge | Memory-safety coupling; confused-deputy channels |

Every alternative considered in the prior analysis (full UDS/gRPC IPC,
shared-memory rings, SQLite-as-shared-inbox) sells back one or more of
P1–P4 for latency this system does not need. The two retained options —
harden-in-place and doorbell — preserve all four. The Android UDS misuse
study (CCS 2016) is the standing cautionary tale for the rejected path:
unauthenticated live local-socket servers enabled privilege escalation and
arbitrary file access precisely because a channel accepted commands
interactively.

---

## 2. Threat accounting (three-plane model)

- **Data plane (Threat A):** unchanged. The injection surface before and
  after this note is exactly the typed capsule parser behind the Librarian
  gate. The doorbell parses nothing (§4.2), so it adds zero data-plane
  surface.
- **Boundary plane (Threat B):** the permission diode (§3.4) and the
  socket-file permissions (§4.3) are object-capability-flavored OS
  enforcement: a process that cannot open the inbox or the socket cannot
  cross. Peer-credential checks are logging-grade defense in depth, not the
  load-bearing control.
- **Code plane:** the platform adapter (§6) is a Tier-1 candidate for the
  strict-mypy checked region — it is small, interface-critical, and sits on
  the boundary.

**Falsification clause.** The composition fails if a demonstrated crossing
occurs in which (a) data influences core state without a corresponding
capsule artifact and ledger row, or (b) a capsule reaches the typed parser
without fd-bound hash and signature verification having run. Either
demonstration requires redesign, not patching.

---

## 3. The capsule protocol (Option 1, hardened)

### 3.1 Commit sequence (edge side)

1. Write payload to `spool/tmp/<uuid>` on the **same volume** as the inbox
   (rename atomicity holds only within a filesystem).
2. `durable_sync(fd, tier)` — platform adapter, §6.2. Sync the *file*
   before rename.
3. `rename(2)` to `spool/inbox/<content-hash>.capsule`.
4. Open the inbox directory fd and `durable_sync(dirfd, tier)` — sync the
   *directory* after rename, so the name change itself survives power loss.
5. Best-effort doorbell ping (§4). Failure of this step is ignored.

Steps 2 and 4 are not optional decoration. The crash-consistency
literature's canonical result (Pillai et al., OSDI 2014) is that rename is
not always atomic with respect to crashes even though POSIX implies it;
their block-order analysis found sixty crash vulnerabilities across mature
applications, and follow-on work (CrashMonkey, ToS 2019) kept finding
ordering bugs in production filesystems — including one formally verified
one. The application-level protocol above (fsync file → rename → fsync
directory) is the pattern that survives that literature. A 2025
macOS/APFS-specific study measured the same protocol under 2,030
fault-injection trials and confirmed the ordering discipline plus a
content-hash integrity check detects 99.8–100 % of injected corruptions.

Maildir is the prior art for the tmp/inbox shape: same-volume write-then-
rename gives lock-free single-writer/single-reader semantics that have run
mail spools for decades.

### 3.2 Durability tiers

The commit sequence is parameterized by a tier, because "synced" means
different things per platform (§6.2) and different capsule classes deserve
different costs:

| Tier | Guarantee | Intended class |
|------|-----------|----------------|
| D0 | Ordering in page cache only; survives process crash, not power loss | none by default (available for scratch) |
| D1 | Write *ordering* to the device; survives kernel panic; may lose the tail on power loss | telemetry-grade crossings |
| D2 | Full flush to stable storage; survives power loss | any capsule that can feed promotion — it is evidence |

Recorded default: **D2 for promotion-feeding capsules, D1 for telemetry**,
pending V1 benchmarks (PD-1).

### 3.3 Content-hash naming

The capsule filename is the hash of its content. This buys, at zero
mechanism cost: idempotent redelivery (duplicate = same name = no-op),
integrity binding (the name *is* the expected digest), natural
append-only keying (identical to the chunk-content-hash doctrine already
governing the embedding index), and dedupe. A detached manifest —
`<hash>.manifest` — carries stratum label, authorship-distance class,
producing-agent identity, timestamp, and an Ed25519 signature over the
manifest body; the manifest binds the content hash, so one signature covers
both. Manifest is renamed into the inbox *before* its capsule so the reader
never sees a capsule without its manifest (a capsule without a manifest is
swept as garbage, never parsed).

### 3.4 Permission diode

Directory permissions make the inbox a one-way surface:

- Edge user: write + traverse on `inbox/`, **no read** (cannot list or
  read back what it delivered — a drop slot, not a shared folder).
- Core user: read + traverse, **no write** (cannot be induced to author
  into its own ingestion path).
- `tmp/` is edge-only in both directions; core never looks at it.

This is diode-by-permissions: the OS enforces direction, the capsule
protocol enforces shape. On the rejected-alternatives ledger this is what
the SQLite-shared-inbox variant could not offer — a shared database file is
readable and writable by both parties by construction, and both sides parse
the same complex file format.

### 3.5 TOCTOU discipline (core side)

1. `open()` the capsule **once**; every subsequent operation uses that fd.
2. Hash the fd's content; compare against the filename and the manifest.
3. Verify the manifest signature.
4. Parse *from the same fd* through the typed gate.
5. Record the verdict in the consumption ledger (append-only), then move
   the capsule to `consumed/` — never delete. The ledger row is written
   before the move; a crash between them re-presents the capsule, which the
   content-hash dedupe resolves as a no-op.

Never stat-then-reopen by path; never trust a path twice. The permission
diode means edge cannot swap a file after delivery anyway (no read/rename
rights inside the inbox), so the fd rule is a second independent layer.

### 3.6 Failure modes

| Failure | Outcome | Guarantee source |
|---------|---------|------------------|
| Edge crash mid-tmp-write | Orphan in `tmp/`; janitor sweeps by age; nothing entered the inbox | rename is the commit point |
| Power loss after rename, before dir-sync (D2) | Capsule may vanish; edge-side ledger retries; redelivery is idempotent | content-hash naming |
| Doorbell ping lost | Latency degrades to sweep cadence; zero data loss | notification-is-advisory doctrine |
| Core crash mid-consume | Capsule re-presented on restart; ledger + hash dedupe make reprocessing a no-op | append-only ledger ordering |
| Duplicate delivery | Same filename; second rename is a no-op or overwrite-with-identical-bytes | content-hash naming |
| Inbox flooding by compromised edge | Bounded by inbox quota; edge blocks or drops locally, core unaffected | B-2 (quota semantics to be specified) |

---

## 4. The doorbell (Option 2)

### 4.1 Why a socket rather than a filesystem watcher as the primary wake

Filesystem event APIs are weaker than their reputation, and macOS's flagship
one is the weakest fit for this job:

- **FSEvents** is explicitly advisory. Its latency parameter coalesces
  events (the client is notified at most once per interval); its persistent
  event database is documented by Apple as advisory, with periodic full
  scans still recommended; the kernel queue is a bounded circular buffer
  (default depth 4096) that sets a dropped-events flag on overflow and
  delivers must-scan-subdirectories markers when events were coalesced away.
  Its strengths — recursive watching of large trees, replay-since-event-ID —
  are features this design does not use.
- **kqueue `EVFILT_VNODE`** (macOS/BSD) is the right *watcher* shape for a
  single directory: open the inbox dir with `O_EVTONLY`, register
  `NOTE_WRITE`, get an fd-based wakeup with no coalescing database. It is
  retained as the doorbell-free fallback (§6.3).
- A **UDS doorbell** beats both on intent semantics: a crossing *announces
  itself* rather than being inferred from directory churn. The wakeup is
  explicit, attributable (the sender opened a permissioned socket), and
  deterministic — no coalescing pipeline between the rename and the wake.

### 4.2 Doorbell semantics — the bright line

The doorbell carries **zero bits of payload**. Not a filename, not a
sequence number, not a count. One byte, meaning "sweep the inbox now."

This is load-bearing, twice over. Security: a channel that carries no
information cannot be an injection vector; core reads and discards one byte
and parses nothing. Reliability: on BSD-family kernels (macOS included),
Unix-domain `SOCK_DGRAM` sockets are documented as unreliable and always
non-blocking for writes — a ping can drop when the receive buffer is full.
Because the ping is informationless, a lost ping degrades latency to sweep
cadence and loses nothing. It also means edge never blocks on core:
temporal decoupling (P1) is preserved by construction, not by care.

(Linux UDS datagrams happen to be reliable. The protocol is designed to the
BSD contract anyway — §6.1's weakest-contract rule.)

### 4.3 Doorbell access control

The socket lives at a filesystem path (never the Linux abstract namespace —
see §6.4), so ordinary permissions govern it: if a process cannot open the
socket file, it cannot ring. Core owns the socket; the edge user is the
only other principal with connect rights. As defense-in-depth logging, core
may record peer identity: `getpeereid()` on a connected Unix stream socket
returns the peer's effective uid/gid, and the mechanism is documented as
reliable — neither side can influence what the other observes.
One caution from the platform references: never authenticate by PID (PIDs
are recycled); key on euid only. With dedicated Unix users per zone, the
socket-file permissions are the actual control and peer-cred is audit
trail.

### 4.4 Liveness composition

Core's wake condition is the OR of three sources, any of which alone is
sufficient for correctness:

1. Doorbell ping (fast path, explicit).
2. Platform watcher on the inbox (kqueue / inotify — fast path, implicit).
3. Periodic sweep timer (slow path, the *only* one correctness relies on).

Wake → scan inbox → process every complete manifest+capsule pair found.
Scanning on every wake (rather than trusting the wake to name a file) is
what makes sources 1 and 2 safely lossy.

---

## 5. The composed protocol, end to end

```
EDGE                                        CORE
----                                        ----
write   spool/tmp/<uuid>
sync    fd            (tier per class)
rename  → inbox/<hash>.manifest
rename  → inbox/<hash>.capsule
sync    inbox dirfd   (tier per class)
ping    doorbell  (best-effort) ─────────→  wake (doorbell | watcher | timer)
                                            scan inbox
                                            open capsule fd (once)
                                            verify hash on fd  = filename
                                            verify Ed25519 over manifest
                                            parse from fd through typed gate
                                            append ledger row (verdict)
                                            move → consumed/<hash>.capsule
```

Latency budget, honestly stated: the wakeup itself is tens of microseconds
(UDS or kqueue) versus poll-interval today; the dominant per-crossing cost
becomes the durability sync — single-digit to low-double-digit milliseconds
at D2 on Apple NVMe (V1 measures the real number). Edge-to-core-visible
latency lands at roughly the sync cost, i.e. ~10 ms-class, versus seconds
under polling. Throughput is a non-issue at current crossing rates; if
Track L or sensor ingestion raises the rate by orders of magnitude, capsule
batching amortizes the sync (group commit) *within* the protocol — no
architectural change required.

---

## 6. Portability layer

### 6.1 The rule

**Design to the weakest contract across supported platforms. Platform
adapters may strengthen delivered guarantees, never weaken assumed ones.**

Concretely: the protocol assumes datagrams can drop (BSD contract, though
Linux is reliable), assumes watchers can coalesce or overflow (true of
FSEvents, kqueue under load, and inotify's `IN_Q_OVERFLOW` alike), and
assumes `fsync` alone may not be durable (true on macOS; on Linux it is,
which the adapter simply enjoys). A platform where the primitives are
stronger runs the identical protocol slightly better.

Everything except two primitives is already portable POSIX: `rename(2)`,
directory permissions, Unix-domain sockets, `open`-once fd discipline,
Ed25519, SHA-256. The adapter surface is therefore exactly two functions.

### 6.2 Primitive 1: `durable_sync(fd, tier)`

The macOS trap that motivates this abstraction: on macOS, `fsync()` moves
data out of the host but the drive may hold it in its own cache
indefinitely; only the `F_FULLFSYNC` fcntl asks the drive to flush to
stable storage, and Apple's own documentation describes post-fsync data
loss on power failure as easily reproduced with real workloads, not a
theoretical edge case. There is a middle tier, `F_BARRIERFSYNC`, which
enforces write *ordering* without a full flush; SQLite uses it on Darwin.
Measured cost on macOS/APFS (2025 fault-injection study): roughly 56–108 %
overhead for file-level durability and 84–570 % for file-plus-directory
durability versus no-sync — large relatively, milliseconds absolutely,
irrelevant at this crossing rate.

| Tier | macOS / APFS | Linux / ext4, xfs, btrfs |
|------|--------------|--------------------------|
| D0 | nothing | nothing |
| D1 | `fcntl(F_BARRIERFSYNC)` | `fdatasync()` |
| D2 | `fcntl(F_FULLFSYNC)` | `fsync()` (issues device flush by default on mainstream filesystems) |

Note the asymmetry: Linux `fsync` already means D2, so the Linux column is
*simpler*. Python detail: `os.fsync` on macOS does **not** issue
`F_FULLFSYNC` (a long-standing CPython discussion confirms this); the
adapter must call `fcntl.fcntl(fd, fcntl.F_FULLFSYNC)` explicitly on
Darwin. This single line is the most likely silent-portability bug in any
naive implementation and is half the reason the adapter exists.

### 6.3 Primitive 2: `inbox_watch(dirfd) → wake events`

| Platform | Primitive | Notes |
|----------|-----------|-------|
| macOS / BSD | kqueue `EVFILT_VNODE` + `NOTE_WRITE` on the inbox dir fd, opened `O_EVTONLY` | fd-based, no coalescing database; stdlib `select.kqueue` suffices, no third-party watcher dependency (V5) |
| Linux | inotify `IN_MOVED_TO` on the inbox path | fires precisely on rename-into, which is exactly the commit event; `IN_Q_OVERFLOW` handled by the same sweep doctrine |
| any | none (doorbell + timer only) | fully supported degraded mode; correctness identical |

FSEvents is recorded as rejected for this role (coalescing latency,
advisory replay database, recursive-tree features unused). The `watchdog`
library is likewise not needed: one directory, one filter, stdlib reach.

### 6.4 Portability–security agreements

Two places where the portable choice and the secure choice coincide, worth
recording so neither is "optimized" away later:

1. **Socket path, never abstract namespace.** Linux offers abstract-
   namespace UDS (names starting `\0`) that exist outside the filesystem —
   and therefore outside filesystem permissions. The portable choice
   (path-bound sockets, which is all macOS has) is also the secure one:
   the permission diode extends to the doorbell.
2. **Manifest-carried identity, never kernel-carried identity.** Peer
   credentials differ per platform (`SO_PEERCRED` struct on Linux,
   `LOCAL_PEERCRED`/`getpeereid` on macOS/FreeBSD, with different structs
   and levels). Because attribution lives in the Ed25519-signed manifest —
   not in socket ancillary data — the protocol's attributability (P3) is
   platform-invariant, and peer-cred remains what it should be: optional
   audit seasoning behind the adapter.

### 6.5 Linux-only upgrades, recorded not taken

If the platform migrates, two strengthenings become available *inside the
same protocol shape*:

- **Sealed capsules**: `memfd_create` + `F_SEAL_WRITE|F_SEAL_SHRINK` yields
  a kernel-enforced immutable buffer; passing the sealed fd over the
  doorbell socket (`SCM_RIGHTS`) would give file semantics at socket
  latency. This changes the doorbell's zero-payload bright line and
  therefore requires its own design pass — parked, PD-2.
- **Invisible staging**: `O_TMPFILE` + `linkat` creates the tmp file with
  no name at all until commit, eliminating the orphan-sweep janitor class.

Neither is a prerequisite for migration; the base protocol runs unmodified.

### 6.6 What portability does *not* cover

Cross-*host* handoff (edge on separate hardware from core) is a different
security model — the shared-volume assumption and the permission diode both
dissolve, and a transport appears where none existed. The capsule format
itself (content-hash name, signed manifest, typed payload) is deliberately
transport-independent and would survive such a move; the *protocol around
it* would need a new design pass. Out of scope here; re-entry condition is
an actual hardware split (PD-3).

---

## 7. Rejected alternatives (this note's scope)

| Alternative | Rejected because |
|-------------|------------------|
| FSEvents as primary wake | Coalescing latency parameter; advisory event database requiring periodic full scans anyway; drop/must-scan flags under load; features (recursive trees, replay) unused |
| Payload-bearing doorbell (filename or count in the ping) | Converts an informationless wakeup into an injection surface and a lossiness bug (BSD datagrams drop); violates the zero-bits bright line |
| SQLite file as shared inbox | Both zones parse one complex format; both hold handles to one file (breaks the diode); library-version coupling across the boundary |
| Full UDS/gRPC/Arrow Flight IPC | Sells P1, P2, P3 for latency the system does not need; live endpoint = interactive attack surface (Android UDS misuse literature) |
| Shared-memory rings | Dissolves P4 outright |
| `watchdog` / other watcher dependencies | One directory, one event type; stdlib primitives suffice on both target platforms |

---

## 8. Verification items

| # | Claim to verify | Method |
|---|-----------------|--------|
| V1 | Real cost of D1 vs D2 on the M2 Max internal APFS volume at representative capsule sizes (1 KB / 100 KB / 10 MB) | microbenchmark; informs PD-1 tier assignment |
| V2 | kqueue `NOTE_WRITE` on an APFS directory fd fires on rename-*into* that directory | 10-line spike; expected yes (rename modifies the directory) but verify, don't assume |
| V3 | Current handoff detection mechanism and cadence (assumed polling — unverified) | grep the handoff interface implementation; path currently unknown to this note |
| V4 | `ops/import_lint.py` docstring records the handoff rule at the cited location | grep-and-cite, path and line |
| V5 | `select.kqueue` available and sufficient in the pinned Python runtime; `fcntl.F_FULLFSYNC` constant present | interpreter check |

## 9. Builder items

| # | Task | Falsifier |
|---|------|-----------|
| B-1 | Implement the two-primitive platform adapter + doorbell + sweep, behind one module boundary (Tier-1 mypy candidate) | A capsule renamed into the inbox is visible to core within 50 ms with **all poll timers disabled**; with doorbell and watcher both killed, it is visible within one sweep interval |
| B-2 | Inbox quota and edge-side backpressure semantics (max bytes, max count, edge behavior on full) | Flooding test: edge saturates inbox; core memory/latency unaffected; edge degrades locally as specified |
| B-3 | Crash-injection harness in the holistic-testing style: kill -9 / power-sim at every protocol step on both sides | Property: no capsule is ever half-visible to the parser; no loss beyond the declared tier; every consumed capsule has exactly one ledger row |

## 10. Parked decisions

| # | Decision | Default recorded | Re-entry condition |
|---|----------|------------------|--------------------|
| PD-1 | Durability tier per capsule class | D2 promotion-feeding, D1 telemetry | V1 numbers land |
| PD-2 | Sealed-capsule (memfd) variant | Not taken | Platform migration to Linux **and** a measured need beyond the base protocol |
| PD-3 | Cross-host handoff | Out of scope | Actual edge/core hardware split |
| PD-4 | Capsule batching / group commit | Not taken | Track L or sensor ingestion raises crossing rate ≥ 100× |

## 11. Open questions

1. Should the consumption ledger live in the existing SQLite gate ledger or
   as its own append-only store? (Leans existing — same write-channel
   properties — but the ledger is core-side only, so no diode concern.)
2. Manifest schema versioning: does the manifest carry its own schema
   version for the typed gate, or is capsule-format evolution handled as
   versioned supersession like everything else? (Leans the latter, for
   uniformity.)
3. Sweep cadence as a function of doorbell health: fixed, or adaptive
   (lengthen while doorbell is verifiably alive)? Fixed is simpler and the
   cost is one directory scan.

## 12. References (research trail, July 2026)

- Oakdoor, "What are Cross Domain Solutions" — protocol-break definition on
  the import path. https://oakdoor.io/insights/what-is-a-cross-domain-solution-cds
- OPSWAT, "Data Diodes in Transfer CDS" — diode + guard composition;
  one-way enforcement vs content validation split.
  https://www.opswat.com/blog/data-diodes-in-transfer-cds-securing-high-assurance-cross-domain-solutions
- Trenton Systems, CDS overview — protocol termination/resume framing.
  https://www.trentonsystems.com/en-us/resource-hub/blog/what-is-a-cross-domain-solution
- Pillai et al., "All File Systems Are Not Created Equal," OSDI 2014 —
  crash-consistency canon; rename-atomicity caveats; 60 application
  vulnerabilities.
- Mohan et al., CrashMonkey/ACE, ACM ToS 2019 — crash bugs in mature and
  formally verified filesystems.
- "Crash-Consistent Checkpointing for AI Training on macOS/APFS,"
  arXiv:2511.18323 — measured D1/D2 overheads and hash-guard detection
  rates under fault injection on the exact target platform.
- Apple, FSEvents / Kernel Queues programming guides — advisory nature of
  the event database; kqueue `EVFILT_VNODE` mechanics.
  https://developer.apple.com/library/archive/documentation/Darwin/Conceptual/FSEvents_ProgGuide/KernelQueues/KernelQueues.html
- fsnotify/fsevents documentation — latency coalescing, MUSTSCANSUBDIRS on
  drops, 4096-event kernel queue. https://pkg.go.dev/github.com/fsnotify/fsevents
- Michael Tsai (aggregating Apple engineering commentary), "Apple SSD
  Benchmarks and F_FULLFSYNC" — fsync vs F_FULLFSYNC vs F_BARRIERFSYNC on
  Darwin; SQLite's use of the barrier variant.
  https://mjtsai.com/blog/2022/02/17/apple-ssd-benchmarks-and-f_fullsync/
- Eclectic Light Co., "How can you trust a disk to write data?" —
  F_FULLFSYNC implementation across APFS/HFS+; Apple's "not a theoretical
  edge case" language. https://eclecticlight.co/2022/02/18/how-can-you-trust-a-disk-to-write-data/
- CPython discuss thread, "Call F_FULLFSYNC in os.fsync for macOS" —
  confirmation that `os.fsync` does not full-flush on Darwin.
  https://discuss.python.org/t/call-f-fullfsync-in-os-fsync-for-macos/79332
- FreeBSD unix(4) man page — SOCK_DGRAM UDS documented unreliable and
  non-blocking for writes; LOCAL_PEERCRED semantics.
  https://man.freebsd.org/cgi/man.cgi?query=unix&sektion=4
- getpeereid(3), macOS/FreeBSD — reliability guarantee of peer-credential
  retrieval on connected stream sockets.
- Linux unix(7) man page — SO_PEERCRED; abstract-namespace sockets (the
  thing §6.4 forbids). https://man7.org/linux/man-pages/man7/unix.7.html
- Jiayun Han et al., "The Misuse of Android Unix Domain Sockets," CCS 2016
  — live unauthenticated local-socket servers as an escalation class;
  cautionary evidence for the rejected full-IPC path.
- D. J. Bernstein, maildir specification — prior art for tmp/rename
  lock-free spool semantics.

## 13. Non-goals

- Not a replacement for or modification of the Librarian gate; the typed
  promotion path is untouched.
- Not a message bus, not bidirectional, not RPC. The doorbell will never
  carry payload — this is a bright line, not a default.
- Not a cross-host transport (PD-3).
- No new dependencies: stdlib primitives on both target platforms.
