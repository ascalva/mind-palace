# Journal — bp-064 (chat clock wiring: CS-4)

## 2026-07-17 — graduated (proposed), not yet started
Minted by /graduate from RATIFIED `dn-chat-sensor` CS-4 (second of the §3 tranche). Status `proposed` —
awaits the owner's `proposed → ready` blessing (owner-only, by hand). **`depends_on: bp-063`** — the
`chatlog` store must be built first (this plan enrolls it).

**Grounding carried in the plan (so a fresh builder needn't re-derive):**
- This plan EXTENDS the pinned spine surface (`spine.py:100-105` "EXTEND, never reshape"): additive only —
  a `chatlog: ChatlogStore | None` field on `SpineSources`, a `_Builder.chatlog` method (per-session g1
  chains copied from the `versions` per-doc exemplar `:394-406`; chain-key = session_id, pos = turn_index),
  a `Spine.derive` call, `_STRATUM["chatlog"]="observed"`, and — the one behavioral change —
  `_STRATUM_CERTIFICATES["observed"]=frozenset({TROUGH})` (§3 Q2: session-close trough-style; local-file
  sensor ⇒ NO HANDOFF, unlike ops/interpreted; grounded against the `eval→TROUGH` case `:259`).
- Cut legality: open sessions are excluded at INGEST (bp-063 stores only closed sessions), so a cut's
  frontier is closed-only; TROUGH attests no in-flight sensor append. Utterances consume nothing ⇒
  `crossing_edges == []` (§3 Q5).
- Atlas (§3 Q4): the chat clock is store-scoped (read-clock frontier borrow, Law C3 `:740-741`) — expected
  to resolve through existing atlas machinery with NO change; a gap is a `codebase` finding, not a patch.
- Write_scope carries `test_cuts.py` + `test_cut_soundness.py` (the retrofit rule — CS-4 extends the
  surface they pin; a new positive `observed→TROUGH` case, never an edited assertion meaning).

**Next action when built:** item 1 (`observed→TROUGH` certificate rule + test_cuts case) → item 2 (enroll
the store's per-session chains + resolve()/derive wiring + the CS-4 falsifiers). 2-item serial. Estimate
opus/150k. Completing this opens ONE of CS-6's three gates (sensor+clock built); the lag instrument stays
gated on the correlator's scoped grant (owner act) + uuid-identity for claim grain.
