---
type: design-note
id: dn-chat-sensor
status: ratified               # draft → ratified is an OWNER-ONLY hand edit; /graduate refuses until then
implementation: design-only
created: 2026-07-17
updated: 2026-07-17
links:
  - docs/brainstorms/cross-strata-substrate-sweep.md   # THE WARRANT — R1–R3/RQ1–RQ2 (owner's verbatim charter, 2026-07-17)
  - docs/brainstorms/graph-at-a-past-cut.md            # D7 — the memory-curve family the lag instrument extends
  - docs/design-notes/cross-strata-dreamer.md          # RATIFIED (generalized) — the correlator that READS this stratum
  - docs/design-notes/recursive-strata.md              # I1 + the parked OwnerVerdict taxonomy this defers to
  - docs/design-notes/global-event-clock.md            # spine/chains/certified cuts — the clock this store joins
  - docs/design-notes/connectivity-instruments.md      # RATIFIED — the phase-B instruments the lag rides on
supersedes: null
superseded_by: null
warrant: docs/brainstorms/cross-strata-substrate-sweep.md
---

# The chat sensor: the dialogue stream as a sensed stratum — retaining the derivation, not just the result

> Composed at **fable** (`claude-fable-5`/xhigh, 2026-07-17, owner-chartered in-session: "can you
> actually formalize it into a design note? … it has now become a crucial part of the system").
> Filed as `draft`; ratification owner-by-hand. **Design only; no build authorized.** The warrant
> is the owner's stated purpose (cross-strata capsule R1, verbatim): the chat is *"where intuition
> and creativity get the helping hand to formalize … to study the system itself."*

## 1. Purpose and scope

The artifact chain currently begins at `/capture`: the capsule keeps the **result** of a
conversation and discards the **process** — question → grounding → falsifier → refinement. This
note decides the sensor that retains the process: ingest the local Claude Code session transcripts
(103 files on disk today at `~/.claude/projects/-Users-ascalva-mind-palace/*.jsonl`, mode 600,
**ephemeral** — the CLI prunes by retention period, so the source will not keep itself) into the
palace's own stores, as a new spine-visible store in the **observed** band, readable only by the
ratified cross-strata correlator. The payoff instrument — **formalization lag**, the memory curve
with one endpoint in conversation — is designed here and gated, not built.

**Out of scope:** the correlator sweep itself (the cross-strata note's own act, behind its scoped
grant); any mirror change; the OwnerVerdict taxonomy (recursive-strata's parked act); non-Claude-
Code chat sources; any build.

## 2. Principles / decisions

### 2.1 CS-1 — verbatim retention first; the source is ephemeral (raw is sacred)

**Decision.** The sensor's first act is byte-verbatim: each session transcript is stored in the
content-addressed immutable **rawstore** (`core/stores/rawstore.py` — dedup by SHA-256, never
rewritten) *before* any extraction. The on-disk CLI transcript directory is the *source*, not the
*archive*: Claude Code prunes old sessions, so without this copy the derivation layer silently
evaporates. Extraction (CS-3) is a derived, regenerable layer over these bytes — the same
two-layer shape as ingest (`raw → derived`), no new pattern. Sensing runs at session boundaries
(batch), never live.

*Falsifiers:* a stored transcript differing byte-wise from its source at ingest time; a session
that existed on disk during a sensor pass but is absent from the rawstore after it; any extraction
row whose text is not recoverable from its stored transcript.

### 2.2 CS-2 — provenance: everything OBSERVED; promotion is human, and the seam already exists

**Decision.** Every chat-sensor row — owner utterances **and** agent utterances — lands as
`Provenance.OBSERVED`. The sensor never mints a mirror-readable class. This is decided *against*
the tempting alternative, and the reasoning is recorded because the taxonomy half-invites it:
`AUTHORED_DIALOGUE` ("owner's words to the Ambassador; mirror-ok") already exists in
`MIRROR_READABLE = {authored-solo, authored-dialogue}` (`core/provenance.py:78-80`) — but the
Ambassador channel is *deliberate owner-to-palace speech*, while CLI sessions mix registers
(operational commands, relayed /usage output, reflective prose). Auto-classifying owner CLI
utterances as authored would (a) flood the mirror with operational noise and (b) be exactly the
machine authorship-inference the taxonomy forbids: *"Promotion up to an authored class is a
deliberate human re-tag-from-raw, never automatic"* (`core/provenance.py:75-77`). The promotion
path is already typed and waiting: `promote(x: Derived[T], cap: OwnerVerdict) -> Authored[T]`
(`core/provenance.py`, deliberate stub; recursive-strata's parked verdict taxonomy). **This note
registers the chat sensor as a consumer of that seam and depends on none of it** — today,
`/capture` remains the one working promotion path (a conversation's *result*, owner-committed to
the repo, is thereby authored; the un-promoted *stream* now persists underneath it). Speaker,
session id, and turn index are row metadata, not provenance.

*Falsifiers:* any sensor-minted row with provenance ∈ MIRROR_READABLE; `MirrorView` constructed
over a source containing chat rows failing to exclude them (the `__post_init__` proof must extend
untouched); any code path deriving provenance from the speaker field.

### 2.3 CS-3 — extraction grain: utterances only; tool exhaust is stripped, and that is a firewall

**Decision.** The derived layer extracts **natural-language utterances** (owner + agent prose) at
utterance grain: `(session_id, turn_index, speaker, text)`. Tool-use blocks, tool results, file
dumps, and command output are **stripped, structurally**. Two independent reasons, either
sufficient: (a) **anti-apophenia** — tool results quote repo files verbatim; embedding them would
manufacture spurious conductance between conversation and code (the corpus bridging to itself
through a mirror of itself — fake reconnection events by duplication); (b) **secret hygiene**
(bright line #10) — accidental secret exhaust in command output must never enter a store; stripping
the whole block class is the structural form, and a secret-scan guard on extracted utterances backs
it fail-closed (refuse the row, name the session).

*Falsifiers:* tool-block content appearing in any extracted row; an extracted row failing the
secret scan yet stored; a conductance reading between a chat utterance and the code file it merely
quoted verbatim (the duplication signature — this is the instrument-level tooth).

### 2.4 CS-4 — the clock: per-session chains in the observed stratum; cuts at session close

**Decision.** The chat store joins the spine as a g1-chained store: chain-key = session id,
position = turn index (total per session, by construction). Stratum: **`observed`** — no new
Stratum enum member; the enum's refinement-predicate shape (`OBSERVED_DIALOGUE ⊂ observed`, cf.
`MIRROR_AUTHORED ⊂ mirror`) is the named extension *if* per-stratum statistics later need chat
churn separated (parked, §4). Wall timestamps in transcripts are **bookmarks only** (Law C4;
graph-at-a-past-cut D8) — order is turn index, never time. **Cut legality:** a session is
append-during, frozen-at-close; a certified cut includes only *closed* sessions (the trough-style
certificate — an open session is mid-append and excluded, exactly as un-quiesced ops stores are).
The formalization-lag clock needs no new stratum: chains are store-scoped
(`frontier_at(store)`, per-chain positions), so conversation proper time is read at store grain.

*Falsifiers:* any ordering read from a wall timestamp; a certified cut containing an open
session's chain; a per-session chain with non-contiguous positions.

### 2.5 CS-5 — the reader: correlator-only, surfacing-only (Invariant 6 untouched)

**Decision.** The sole reader of the chat stratum is the **cross-strata correlator** (ratified
generalized; its own scoped grant gates each sweep). The mirror dreamer never sees it — enforced
by CS-2's provenance (a chat row is unrepresentable in a `MirrorView`), not by convention. Every
output derived from chat data is **surfacing/report-layer only** (I1 verbatim): never a weight,
never a confidence input, never a promotion, never a behavioral-baseline input (§15). The
self-study loop (the palace observing its own ideation) is read-only by construction — the
sensed derivation may *inform the owner*, never steer the dreamer.

*Falsifiers:* a chat-derived value in any weight/confidence/promotion path; a dream log entry
whose seed traces to a chat row; a baseline computation touching the chat store.

### 2.6 CS-6 — the payoff, designed and gated: formalization lag

**Decision (design-only; the gate is triple).** The instrument this stratum exists for:
**formalization lag** — the memory-curve family (graph-at-a-past-cut D7) with endpoint A a chat
utterance and endpoint B an artifact claim (capture → note → plan → code). `lag(A→B)` = proper
time (conversation ticks; chat-store chain grain) and cut-distance between A's first utterance and
B's landing; `σ*(A,B;c)` traces when the intuition and its formalization first joined. Reported on
the two-axis discipline (the chain of custody; the conductance profile) — never fused. **Gates,
all three required:** the connectivity tranche built (bp-059+…); this note ratified + the sensor
built; the correlator's scoped grant for the observed band. Cross-strata identity (an idea's
thread from utterance to code) is claim-grain and therefore **also waits on uuid-identity** — at
which point the lag instrument becomes the fourth registered consumer (after Track D, SF-a, CN-6).

*Falsifiers:* a lag computed across an uncertified cut; any lag/confidence scalar fusion; a lag
claimed at claim grain before uuid-identity's π lands (chain-of-custody by hand-wave).

## 3. Consequences — what /graduate mints, post-ratification

Session-sized, dependency-ordered; all flag-gated additive; write scopes disjoint from `core/`
except the two named seams.

1. **Sensor core** (CS-1, CS-2, CS-3) — rawstore retention pass + the chatlog store + utterance
   extraction with tool-strip + secret guard; provenance OBSERVED throughout. Touches
   `core/stores/` (new store module) + an `ops/` sensor entry beside the code-/self-sensors.
   **~200k opus.**
2. **Clock wiring** (CS-4) — spine `_STRATUM` + `SpineSources` registration, per-session chains,
   session-close cut certificates, atlas coverage. Small, but it touches the pinned spine surface
   — ground it against `spine.py`'s "GC-2/GC-3 EXTEND, never reshape" banner. **~150k opus.**
3. **Formalization-lag instrument** (CS-6) — **NOT minted until its triple gate opens**; listed
   so the tranche's shape is honest. Backfill of the 103 historical sessions rides plan 1
   (owner decision D2 below).

## 4. Parked decisions

| Decision | Default | Re-entry |
|---|---|---|
| `OBSERVED_DIALOGUE` refinement stratum | plain `observed`; speaker/session in row metadata | CN-4-style per-stratum statistics need chat churn separated from other observed churn |
| owner-utterance promotion to AUTHORED_DIALOGUE | none automatic; `/capture` remains the promotion path | recursive-strata's OwnerVerdict taxonomy ratifies → the typed `promote` seam gets its policy |
| quoted-content dedup beyond tool-strip | strip tool blocks only; prose quotes stay | the CS-3 duplication-signature falsifier fires on real data |
| realtime / mid-session sensing | batch at session close | an instrument demonstrably needs the open session (none named today) |
| other chat sources (Ambassador logs, etc.) | Claude Code transcripts only | the Ambassador adapter lands its own transcript retention |

## 5. Owner decisions surfaced at ratification

- **D1 (the register question):** confirm CS-2 — ALL chat rows OBSERVED, no auto-authored owner
  utterances, despite `AUTHORED_DIALOGUE` existing for the Ambassador channel. The alternative
  (auto-classify owner CLI utterances as authored) is rejected in-note for register-mixing and
  the never-automatic promotion rule; ratification confirms that reading.
- **D2 (backfill):** ingest all 103 existing session transcripts (raw-is-sacred argues yes, and
  the source is ephemeral), or forward-only from ratification? Default: full backfill.
- **D3 (two acts, not one):** ratifying this note authorizes **sensing** (plans 1–2). Correlator
  **reading** of the chat stratum remains a separate act behind the cross-strata scoped grant —
  ratification here does not open it.

## 6. Non-goals

No mirror access, ever (CS-2/CS-5 — structural). No dreamer modification. No chat-derived weights,
confidences, promotions, or baselines (I1/§15). No new Provenance class and no new Stratum member
(the existing taxonomy spans v1). No realtime sensing. No transcript exfiltration — everything
local (bright line #11; the transcripts already live on this machine). No correlator sweep here.
No uuid-identity design (consumer registration only). No build before ratification + blessing.

## Cross-references

- **Code (the seams, all existing):** `core/provenance.py:44-80` (`Provenance`, `MIRROR_READABLE`,
  the never-automatic rule) · `core/provenance.py` `promote`/`OwnerVerdict` (the typed, stubbed
  promotion seam) · `core/mirror.py:66-105` (`MirrorView.__post_init__` — the proof CS-2 extends) ·
  `core/stores/rawstore.py` (CS-1's retention) · `core/temporal/spine.py:104` ("EXTEND, never
  reshape"), `:241-249` (`_STRATUM`), `:216-229` (`CertifiedCut`) · `core/scope.py:54-66`
  (`Stratum` — the refinement-predicate shape §4 names) · `ops/` code-/self-sensor pair (the
  sibling pattern; they fired on this note's own warrant commits).
- **Artifacts:** the warrant capsule (R1–R3, RQ1–RQ2 — both RQs are *decided* here: CS-2 and
  CS-3/CS-4); `graph-at-a-past-cut.md` D7/D8; `cross-strata-dreamer.md` (the ratified reader);
  `recursive-strata.md` (I1; the parked verdict taxonomy); finding-0100 (the retention chain this
  note's CS-1 mirrors).
- **Source of record for the ephemerality claim:** the CLI's transcript retention setting
  (`cleanupPeriodDays`) — transcripts are pruned by default; the palace must not outsource its
  own memory to a tool's cache policy.
