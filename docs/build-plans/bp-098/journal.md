# Journal — bp-098 (CI-wiring / Plan B: the code-ingest ENABLE path)

> Alive while the plan is proposed/in-progress; sealed on completion.

## 2026-07-22 — MINTED (graduation, session-42)

- **State:** `proposed`. Graduated from the ratified `dn-code-ingest-pipeline`'s deferred
  "owner-visible enable step" (§2.7), **warrant finding-0159** (the owner ruling: the ON switch
  is part of finishing — a capability with no way to turn it on is missing functionality, not
  "dormant by design"). This is "Plan B" from the session's chat.
- **Why it exists:** CI-1..4 (bp-092..094) shipped the code embed lane but with an INERT flag
  (`[code_ingest].enabled` read by nothing — no `CodeIngestConfig`), no daemon enqueue of the
  `code_sync` KIND, and no CLI. Flipping the flag did nothing; the only way to run the seed was a
  raw `build_code_corpus_sync().seed()` call. This plan builds the switch.
- **Grounding done at graduation** (so a builder inherits it): the engine (`code_corpus.py`) +
  KIND/handler/enqueue (`scheduler/code_sync.py`) are DONE (bp-092) — this plan only CALLS them.
  Pinned in §6: the `SelfModConfig` schema template (`loader.py:257`), the `build_components`
  handler dict + `_housekeeping` sibling (`enqueue_chat_sync`), and `Launcher.ingest_chat()` /
  `palace.py:245` as the CLI-triggered-enqueue precedent for `code-seed`. Two "code does not
  settle" items flagged (the loader assembly call shape; whether `ingest_chat` reaches a live
  queue) — builder reads + mirrors, never infers.
- **Scope discipline:** the seed stays owner-visible (§2.7) — housekeeping enqueues INCREMENTAL
  sync when `enabled`; the deliberate SEED is `palace code-seed`. This plan does NOT flip
  `enabled` on or run the seed (owner's runtime/deskcheck act).
- **Next action (on owner bless → ready):** `/build bp-098`; Items 1→2→3 (schema → daemon
  enqueue → CLI). After it, "turn on code ingest" is a real command through the proper discipline.
- **Blocking:** none. Awaiting the proposed→ready blessing (owner-only, by hand).
