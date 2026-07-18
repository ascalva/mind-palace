# Journal — bp-069 (chat real-time + lossless: growth-aware append + a live transcript watcher)

## 2026-07-18 — minted (proposed), awaiting owner bless
Owner-directed (2026-07-18), warranted by **finding-0109**. bp-068's live verification surfaced that
`sync()` FREEZES a session once ingested (bp-063 Q4), so a session left open for hours / overnight is
captured PARTIAL and its tail is lost. Owner (emphatic): unacceptable, data loss would be common, the
system is real-time so ingestion must be IMMEDIATE — parity with the code sensor (every commit → every
transcript change). This plan makes chat ingestion growth-aware + real-time. Status `proposed` — awaits
the owner's `proposed → ready` blessing (owner-only, by hand).

**Grounding carried in the plan (so a fresh builder needn't re-derive):**
- **Change detection = the rawstore `is_new` signal** (stateless, "git for transcripts"): a growth-aware
  `sync()` `add_text`s each transcript and only re-parses when `is_new` (changed); `add_batch` is
  idempotent by `(session_id, turn_index)` so re-parsing a grown file appends ONLY the new turns. No
  sidecar state store needed. Freeze-once (Q4) removed.
- **Torn-line tolerance:** `parse_transcript` (ops/chat_sensor.py:91) has a bare `json.loads` — a live
  file read mid-append can crash. Wrap per-line in try/except JSONDecodeError (skip-and-continue).
- **Watcher:** `VaultWatcher` (core/ingest/watch.py) is already a generic debounced dir-watcher
  (watchdog→poll), independent per instance. Generalize → `DirectoryWatcher` (`vault`→`path`); repoint
  the sole caller (build_vault_watcher). `build_chat_watcher` on_change → `enqueue_chat_sync`. Small
  debounce (0.5s) for immediacy.
- **Launcher:** `Components.watcher` (single) → `watchers: list`; `_serve`/`_shutdown` iterate;
  `build_components` builds vault + chat watchers. Register `chat_sync` in `router._PINNED_KINDS`.
- **Config:** a `[chat]` section (`transcripts_dir` override + watch debounce/poll) — plain fields, ratchet
  STAYS 19. Folds finding-0108's two follow-ups (G1 transcripts_dir override, G2 _PINNED_KINDS).
- **AMENDS ratified dn-chat-sensor Q4** (owner is the design authority) + notes the whole-session-refusal
  behavior under growth (a secret in a new turn freezes the session at its pre-secret state; still
  fail-closed — bright line #10 intact).

**Architecture refinement (owner, 2026-07-18):** ONE agent, MULTI-RATE PROJECTION — the model-free chat
sensor always accepts the latest real-time transcripts and projects each layer at its own rate. bp-069 =
*rate 0* (real-time: raw layer 0 + dialogue-strata projection); layers 1 (summaries) + 2 (references) are
LOWER-rate projections by the same agent, later, on already-scrubbed text (Track 2 / CS-5). Credential
removal stays the DETERMINISTIC gate at the real-time rate (bright line #10 — a model never reads a
secret; downstream projections read only scrubbed text). Recorded in §1 + finding-0109.

**Next action when blessed:** Item 1 (growth-aware sensor + torn-line) → Item 2 (watcher + generalization
+ multi-watcher launcher + `[chat]` config). Est opus/180k, session_budget 2. ⚠️ suite stays RED-by-design
at the ratchet 19 — acceptance = only `test_core_self_containment` fails AND count == 19; verify the vault
watcher is byte-identical post-rename; verify a live transcript change re-ingests appended turns.
