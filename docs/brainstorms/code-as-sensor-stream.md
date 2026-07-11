# code-as-sensor-stream

Owner–orchestrator design dialogue (2026-07-11, chat) on whether source code needs
its own provenance class, held immediately after the per-commit structural
code-snapshot tool landed (`ops/code_snapshot.py`, commit `01e34e9`). Restructured
from the raw exchange on append — lossy capture beats no capture (§8).

## 2026-07-11T06:05:00Z (captured)

```capsule
topic: code-as-sensor-stream
date: 2026-07-11

decisions:
  - Source code does NOT get a new provenance class (owner ruling). It is a sensor
    data stream handled by an agent outside the sealed core — the repo is an
    instrument, the snapshot tool is its interpreter (deterministic, versioned,
    sole path in — the authorship-distance-axis §3.7 interpreter shape), and
    data/code_snapshots.sqlite is the normalized store. This answers finding-0021's
    open code-provenance-label sub-question queued for founding-corpus ratification:
    no distinct label; the sensed-stream treatment covers it.
  - The snapshot ledger stays OUTSIDE the knowledge corpus (event-log-only), the
    same default the axis note's PD-5 sets for author-initiated append-only
    streams. It is build history, guarded from `palace reset` like the run ledger.
  - If the code stream ever needs to enter core, it enters through the same typed
    handoff seam as any sensor (SensingHandoff → typed-view shape), mirror-opaque
    by construction — no taxonomy change, no new machinery.
  - Corroboration use (code as the external arbiter for supersession candidates,
    per finding-0021's s(C,D) lesson) reads the ledger ops-side; it does not
    require corpus entry.
  - Orchestrator analysis, accepted as context for the ruling: no existing class
    fits code as a corpus citizen — authored-solo would let builder output feed
    the mirror (masquerade at origin); curated would erase the testimony-vs-
    measurement distinction the archive pass depended on; code's chronology is
    machine-perfect (no timestamp lie) and supersession is intrinsic per commit,
    already recorded by git + the snapshot ledger, never the note-version store.

parked:
  - decision: whether the Ambassador's self-knowledge answers ("how do you work?")
      should ever be grounded in actual code rather than the curated docs graph
    default: docs-only self-knowledge (ingest_self_knowledge.py, curated), ledger
      queryable beside the corpus but not reasoned over in-graph
    re_entry: a self-knowledge answer is wrong because the docs lag the code, or
      the supersession-recovery evaluation wants code corroboration as an in-graph
      feature (either reopens HOW the sensed code stream is consumed, not the
      no-new-label ruling)

open_questions:
  - Where does the snapshot agent formally live when it becomes a live sensing
    agent rather than a git hook? (Today it runs host-side in ops/ — local
    instrument, no network, no vault. The zone-B framing binds if it ever watches
    anything remote.)

next_steps:
  - Fold this ruling into the founding-corpus ratification pass when the owner
    ratifies (it settles the three-source-class sub-question finding-0021 queued
    there; the finding's enrichment items 1-3 are otherwise unchanged).
  - No build action — the tool, hook, backfill (91 commits), and reset guard all
    landed in 01e34e9.

references:
  - docs/findings/finding-0021.md            # the code-provenance sub-question this settles
  - docs/design-notes/authorship-distance-axis.md   # §3.7 interpreters; PD-5 event-log default
  - ops/code_snapshot.py@01e34e9             # the interpreter
  - data/code_snapshots.sqlite               # the normalized store (reset-guarded)
  - core/sensing.py                          # the handoff seam if the stream ever enters core
```
