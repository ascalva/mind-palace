# The synced folder as ingest / exhaust — the system's two-way port to the phone

## 2026-07-19T21:10:00Z

```capsule
topic: exhaust-and-ingest-sync
date: 2026-07-19

decisions:
  - Owner intent: the Syncthing/SyncTrain folder that already reaches Alberto's phone
    (over Tailscale) should be the system's TWO-WAY port, organized into two sections:
    `ingest/` (material flowing INTO the system — the corpus feed) and `exhaust/`
    (material the system EMITS — starting with `exhaust/reports/`, the build reports).
    Alberto opens `exhaust/reports/` on his phone via a Files shortcut to review.
  - Framing: this is the sensor/output duality made physical. The system already has
    inbound sensors (code-sensor, self-sensor); "exhaust" names the outbound side. One
    folder, two one-way lanes: `ingest/` is write-from-phone / read-by-system;
    `exhaust/` is write-by-system / read-from-phone.
  - Privacy is SATISFIED, not at risk: Syncthing-over-Tailscale IS the constitution's
    sanctioned private default (local/Tailscale), NOT a third party (non-negotiable 11).
    The corpus already rides this channel to the phone (the existing vault sync). So
    corpus-on-the-sync is fine; the concern is purely the ingest/exhaust separation below.

invariants:
  - THE load-bearing rule: the ingest scanner watches `ingest/` ONLY and must NEVER
    descend into `exhaust/`. Otherwise the system ingests its own build reports as
    corpus — and since reports DESCRIBE the system, that is recursive self-ingestion of
    meta-content. Enforce structurally (scanner root = ingest/, or an exclude the
    scanner honors), not by convention. This is the make-or-break property.
  - `exhaust/` is system-authored, owner-read (reports, digests, exports). `ingest/` is
    owner-authored, system-read (the capture path). Neither lane reads the other.
  - Reports are WORKFLOW/EXHAUST, never corpus. They must not re-enter the reasoning
    complex via any path (mirrors the interface/corpus separation, non-negotiable 11).

open_questions:
  - Layout vs the existing vault: the current synced folder is `~/.mind-palace/vault`,
    which IS the corpus + ingest root. Does `ingest/` BECOME the vault (restructure the
    synced folder to a parent holding `ingest/` = today's vault content + `exhaust/`), or
    does `exhaust/` become a SEPARATE Syncthing share alongside the vault? Separate share
    = cleanest isolation (the ingest scanner physically cannot see it) but two folders to
    pair; unified parent = one folder, but the scanner-exclusion must be airtight.
    LEANING: separate share (structural isolation beats a honored-exclude).
  - Does this extend `dn-vault-sync-and-capture` (the ingest side is likely already
    spec'd there) as an amendment, or warrant its own design note for the exhaust side?
  - Report format for iOS Files: self-contained HTML (opens in browser, rich) vs PDF
    (universal Files preview) vs Markdown (plain). PROVISIONAL: self-contained HTML,
    theme-aware — already used for the bp-074 proof-of-concept.
  - Naming/retention: one file per build (`YYYY-MM-DD-bp-NNN-slug.html`)? A rolling
    index? Prune policy? (Exhaust could also carry non-report digests later.)

provisional_today (works NOW, folds into the design later):
  - `~/mind-palace-reports/` created as a standalone dir (OUTSIDE the vault — corpus-safe
    by construction); the bp-074 report written there as self-contained HTML. Alberto can
    add it as a Syncthing share to his phone today; it becomes `exhaust/reports/` when the
    design lands. The [[phone-build-report]] workflow (memory) now targets a synced-folder
    FILE write, not (only) the Gmail draft — the draft path stays as a fallback.

next_steps:
  - Decide separate-share vs unified-parent (the gating layout question).
  - Graduate into an amendment to dn-vault-sync-and-capture OR a new exhaust design note,
    with the ingest-never-scans-exhaust invariant as a STRUCTURAL enforcement (a test).
  - Then a small build: the report writer targets `exhaust/reports/`; wire it into the
    merge-ready step of the delegated-build flow.

references:
  - docs/design-notes/vault-sync-and-capture.md    # the ingest side — this extends it
  - docs/design-notes/the-sacred-boundary.md        # writes-to-core discipline (kinship)
  - memory phone-build-report                        # the report spec + delivery workflow
  - ~/.mind-palace/vault (Syncthing "Mind Palace Vault") # the existing synced corpus folder
  - ~/mind-palace-reports/2026-07-19-bp-074-*.html   # today's proof-of-concept report
```
