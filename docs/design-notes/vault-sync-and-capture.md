---
type: design-note
id: dn-vault-sync-and-capture
status: draft
implementation: built-wired   # corpus-audit 2026-07 verification
created: 2026-06-26
updated: 2026-07-01
links: []
supersedes: null
superseded_by: null
warrant: null
---

# Design note — Vault sync & capture: the owner's path to feed the system

*Family tag → family 2 (regenerable derivation): incremental, idempotent, content-addressed re-ingest (unchanged=no-op, changed=re-embed, delete=tombstone, raw kept) + authored/dialogue capture (a family 1 label). See [`../NOTATION.md`](../NOTATION.md).*

**Status:** **near-term, buildable now** — the practical path for the owner to start feeding the
system his writings. Touches the existing Phase-1 ingest; **not a new phase.** The watcher is
code; the sync transport is operational (documented in `runbook.md`).

## Goal
The owner writes notes (phone + laptop); the system **auto-ingests them and keeps embeddings
current**; the owner can also capture and query by chat over a private transport. Priority,
because the owner is actively writing notes the system cannot yet read.

## Architecture (firewall-preserving)
1. **Local vault watcher — core-side, LOCAL filesystem only, no network.**
   A filesystem watcher (e.g. `watchdog`/FSEvents) on the configured vault path, wired into the
   scheduler as a background task. On change → re-ingest through the existing Phase-1 pipeline.
   **Idempotent via the existing content-addressing:** unchanged content (same digest) = no-op;
   changed = re-embed; deleted = **tombstone** (mark inactive, drop derived rows, **keep raw** —
   raw is sacred). Provenance = `authored-solo`. *Must not import `edge`/sockets/http; the
   import-lint stays green.* This is the only new code.
2. **Sync transport — a SEPARATE process, not the core.**
   Keeps the vault directory current across devices. The core never touches it; it only watches
   a local folder. **Recommend Syncthing** (peer-to-peer, no third-party server) **run over
   Tailscale** ⇒ the owner's notes sync **device-to-device, encrypted, with no vendor in the
   path.** iCloud / Obsidian Sync are convenient but **transit a vendor** — the same class of
   tradeoff as the interface-transits-third-party invariant. Flag it; recommend the private
   option.
3. **Tailscale — the private mesh.** Gives the phone an encrypted, private path to the laptop
   with **no public exposure** — used for (a) Syncthing peer-to-peer sync and (b) reaching the
   interface gateway (Zone B) to chat-capture and query. Fits the established "private default"
   interface posture.
4. **Messaging capture — Zone B interface gateway** (when the interface lands). Notes texted to
   the assistant → stored as `authored-dialogue` → ingested. The query path is the same gateway.

## Seal integrity (why this doesn't break Invariant 1)
- The watcher reads **local files** and writes **local stores** — filesystem, not network. The
  seal holds; the import-lint proves it.
- The networked parts (sync daemon, interface gateway) are **separate processes / Zone B**, never
  the core.
- **Honest note:** the sync transport moves the owner's *own authored notes* over the network
  (encrypted). Syncthing-over-Tailscale keeps it fully peer-to-peer (no vendor sees the notes);
  vendor sync transits a third party. The owner chooses; the private option is recommended.

## Provenance
- Synced vault notes → `authored-solo`. Chat-captured notes → `authored-dialogue`. Both feed the
  mirror.

## Deletion semantics
- Default on vault delete: **tombstone** (inactive, derived dropped, raw kept) so re-adds dedup
  and nothing is lost. For true privacy deletion, a deliberate **purge-raw** action removes the
  raw blob — a gated, owner-initiated operation (not the watcher's default).

## Build (discrete task, then continue to Phase 9)
- The watcher + scheduler wiring + tombstone-on-delete. Operational setup (Syncthing + Tailscale)
  documented in `runbook.md`.
- Verify: edit a note → embeddings update; delete → stops surfacing in search; unchanged re-scan
  → no-op (no new digests); import-lint green (watcher reaches no network).
