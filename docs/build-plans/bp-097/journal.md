# Journal — bp-097 (WF-2: the deskcheck gate)

> Alive while the plan is proposed/in-progress; sealed on completion.

## 2026-07-21 — MINTED (graduation, session-42)

- **State:** `proposed`. Graduated from the ratified
  `dn-track-board-and-deskcheck-gate` (§3's WF-2) alongside bp-096 (WF-1).
- **Grounding done at graduation:** gate-guard fires on `Edit|Write|MultiEdit`
  broadly with file-type gating in the lib (`_lib.py:424-426`), so covering
  `docs/deskchecks/**` is a lib change only — no settings.json edit (Q1). The
  post-hoc (c) scanner (`_blessing_in_diff:510-527`) and `cmd_stop_audit`
  (`:571-745`) are the surfaces extended; `test_handoff_gate.py` is carried in
  `write_scope` (retrofit rule) because this plan modifies `cmd_stop_audit`.
- **A NEW gap this session surfaced (folded into Item 4):** D6 teaches clause (c)
  to yield to an owner-staged *blessing*, but clause **(b2)** has no yield
  affordance — and the WF-1 track-backfill (owner hand-editing ratified notes)
  is a brand-new (b2) trigger that thrashed live this session (repeated Stop
  BLOCKs on the uncommitted `track:` edits). Item 4 adds a narrow, conservative
  (b2) yield for additive-metadata edits (never for body edits). `[ESTABLISHED —
  observed 2026-07-21]`.
- **Next action (on owner bless → ready):** `/build bp-097`; ship Item 1 (dc
  template + dir) first so the gate has a shape to test, then skills/probe
  (5,6,7), then the `_lib.py` chain 2→3→4 in sequence. Do NOT run concurrently
  with bp-090. Verdict flip stays owner-only after this lands.
- **Blocking:** none. Awaiting the proposed→ready blessing (owner-only, by hand).

## 2026-07-21 — BUILT (delegated builder, worktree agent-a0492b48d1e28525a)

- **Status:** all 7 items complete; full attestable-green gate passed (5 legs,
  argless-mypy tail = 69 = baseline). NOT merged (orchestrator sequences merges).
  Plan status left `ready` for the orchestrator to flip on seal. Ready to deskcheck.
- **Worktree note:** this worktree's base (22bdaee) predated the bp-097 mint, so it
  had no plan.md/journal.md. Fast-forwarded the branch to main (28e66f2) — clean ff,
  no local commits — to materialize the plan. active-plan pointer bound to `bp-097`.

- **Item 1 (dc template + store) DONE.** `docs/templates/deskcheck.md` matches
  bp-096 §6 / bp-097 §6 verbatim (`board.py` will parse the verdict).
  `parse_front_matter` reads `type: deskcheck` + all fields; `_normalize_status`
  strips the `verdict: pending  # …` inline comment back to `pending` (verified).
  `docs/deskchecks/README.md` seeds the store (no real `dc-NNN` authored — owner
  sessions).
- **Item 2 (pre-hoc verdict denial) DONE.** New `is_deskcheck` (keyed on the `dc-`
  basename so README/scaffolding is never gated), `verdict_of`, `_verdict_in_text`
  (Q2: `_status_in_text` is NOT reused for `verdict:` — explicit sibling).
  `cmd_gate_check` gains a dc branch mirroring the two blessing branches; a
  `pending→approved|needs-work` flip DENIES, `pending` ALLOWS. `cmd_gate_check_hook`
  picks the reader (`_verdict_in_text` vs `_status_in_text`) by file type.
  `gate-guard.sh` header comment corrected (three gates; +docs/deskchecks). Standalone
  smoke + the two blessing gates still DENY (no regression).
- **Item 3 (post-hoc (c) verdict audit + D6 yield) DONE.** `_diff_text_head` now
  also diffs `docs/deskchecks`; `_blessing_in_diff` catches a `+verdict:
  approved|needs-work` on a dc; `_untracked_blessing` catches a dc minted at a
  verdict. The (c) reason (tracked + untracked) reworded to the D6 YIELD posture
  ("if it is the owner's staged hand, say so once and YIELD … do not poll"). Still
  BLOCKS — only the guidance changed. Committed verdict self-clears (HEAD-keyed, A1).
- **Item 4 (clause (f) + (b2) yield) DONE — the (b2) yield SHIPPED SAFE.**
  - Clause (f): `_sealed_plans_in_diff` finds plans flipping to `status: complete`
    in the HEAD diff; `_journal_tail_has_followthrough` checks the LAST entry (tail
    from the final `## ` header, skipping the Follow-through block itself and the
    `## Markers` trailer) for a `## Follow-through` header. **Decision on the
    unsettled "journal tail" window (§3 Q4):** bounded to the final entry, not
    whole-file — grep-class header presence; anti-false-clear tested (an early
    mention does NOT clear a seal whose tail lacks it). Grounded in the observed
    convention: real sealed journals (bp-007..bp-011) are oldest-first with SEAL at
    the tail (verified bp-008).
  - **(b2) yield — SHIPPED (made provably safe).** The shape check
    `_is_additive_frontmatter_only` compares the parsed BODY (byte-identical) + the
    front-matter key-map (status unchanged, no existing key mutated, only additions)
    vs HEAD — NOT a diff-line regex. So a body edit dressed as `key:` falls out via
    the body compare. `all(...)` over tampered files; ANY body edit / deletion /
    key-mutation / doubt → hard block. The yield NEVER lets anything pass (both
    branches BLOCK); it only changes the message. A body edit hard-blocks with the
    immutable message, no yield (tested). This is why it was safe to ship rather than
    park (§10): the failure mode (owner committing a body edit thinking it's fine) is
    structurally impossible because the shape check requires a byte-identical body.
- **Item 5 (checkpoint skill) DONE.** New "Seal entries answer follow-through"
  section with the five-question `## Follow-through` block VERBATIM to clause (f)'s
  grep; "On the way out" now names clause (f).
- **Item 6 (delegate skill) DONE.** "Right-sizing the AUDIT" section: delegated/
  lower-tier ⇒ independent Opus pass; supervised same-tier ⇒ merge scrutiny IS the
  audit, recorded — the basis for board.py's "audit: present/owed" flag.
- **Item 7 (P-WF1 probe) DONE — filed finding-0155 (discovery → orchestrator).**
  The running model id is NOT directly exposed to hooks (env has `CLAUDE_EFFORT=high`
  but no model id; PreToolUse stdin has no `model` key), but IS reachable INDIRECTLY
  via `transcript_path` → last `message.model` (this build read `claude-opus-4-8` —
  the fable→opus silent downgrade, confirmed). Per §10 I shipped no gate code;
  routed to the owner to decide whether the fragile indirect path warrants a new
  plan or P-WF1 stays parked (backstop: procedural banner + usage-verify).

- **Green gate (each leg run separately):** ruff `All checks passed`; mypy dirs
  `Success: no issues found in 243 source files`; argless mypy `Found 69 errors in
  20 files` (= baseline); type_gate both scans OK; pytest — new
  `test_deskcheck_gate.py` 14/14 pass, `test_handoff_gate.py` 6/6 pass (no fixture
  needed a Follow-through block — none flip to complete). `_lib.py` is outside the
  mypy target dirs but ruff-clean.
- **Findings:** finding-0155 (P-WF1 indirect model-id path; discovery; orchestrator).
- **Next action:** orchestrator reviews the diff, runs the green gate, merges to
  main, flips bp-097 → complete, and files bp-097 (workflow track) into
  DESKCHECK-QUEUE.md. The verdict gate this installs is owner-only thereafter.

## Follow-through
- **Built?** Yes — all 7 items: the deskcheck template + store, the third
  owner-only gate (pre-hoc `cmd_gate_check` + post-hoc (c) verdict audit), clause
  (f) seal follow-through, the (b2) owner-staged yield (shipped safe), the two skill
  edits, and the P-WF1 probe (finding-0155). 14 new tests, all green.
- **Wired / delivered (or why dormant)?** WIRED and live: gate-guard (PreToolUse)
  and journal-gate (Stop) already invoke these `_lib.py` paths on every session, so
  the deskcheck verdict + clause (f) + the D6/(b2) yields enforce as of this merge —
  no flag, no separate wiring step. The skills load on invocation.
- **Does a consumer use it?** Yes — every agent session (the hooks fire universally);
  and `board.py` (bp-096/WF-1) consumes the dc template's verdict schema, pinned
  identically in both plans so they cannot drift. No real `dc-NNN` exists yet (owner
  sessions), so the common board path stays "no dc → deskcheck-pending".
- **Track state (what remains on this track)?** The `workflow` track: WF-2 (this)
  done; WF-1 (bp-096, the board substrate) is the sibling build in
  agent-a75921da9dde8c99d. After both merge, the deskcheck gate has both its typed
  artifact (dc records) and its board surface. bp-090 must not run concurrently with
  this (shared hooks/skills tree). The track is not CLOSED until an owner deskcheck.
- **Opened a new track/finding?** finding-0155 (P-WF1: the model id is indirectly
  reachable via `transcript_path`) — routed to the orchestrator/owner to decide
  whether to graduate a structural model-per-phase plan or keep P-WF1 parked.
