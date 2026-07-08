---
type: design-note
id: dn-nervous-system-and-ambassador
status: draft
implementation: partial   # corpus-audit 2026-07 verification
created: 2026-06-28
updated: 2026-07-01
links: []
supersedes: null
superseded_by: null
warrant: null
---

# Design note — The nervous system: tamper response, verification, and the Ambassador

*Family tag → family 3 (guarded transition systems): the scheduler/supervisor "nervous system" (queue lifecycle, tamper response) + the Ambassador front door (family 1). See [`../NOTATION.md`](../NOTATION.md).*

**Status:** design only. Ties together (a) how the system reacts to detected
tampering, (b) who verifies attestations and at what latency, and (c) the Ambassador —
the conversational front door. Builds directly on shipped pieces: the attestation
chain, Vault runtime auth, the Phase-10 gated self-mod loop, MirrorView, and the
Phase-6 interface gateway. Honor at Phase 11 (the introspection/auditor layer) and
when text interaction is activated.

---

## 0. The unifying idea

The system now has privileged operations (code execution, secret access) and
self-modification. Three questions follow, and they are one question — *what watches
the watchers, how fast, and how do you talk to the whole thing?*

The governing principle throughout: **put each check at the lowest level that can
handle it.** Nerves are fast because reflexes resolve at the spinal cord, not the
brain. A scope check is a reflex (inline, microseconds); a full chain-audit is
cognition (async, trough-scheduled). Speed comes from *not* routing everything
through the expensive path.

---

## 1. Tamper response — graduated, provenance-aware (NOT a single kill switch)

"Unsanctioned tampering" is not vague — given the architecture it is one of a small
set of **mechanically detectable chain breaks**:
- a `DerivedStore` record with no valid attestation chain;
- a Constitution fingerprint changed without a gate ledger entry;
- a Vault access that succeeded against no minted/authenticated token;
- a config knob moved without a `levers.toml` ledger entry;
- an attestation whose Ed25519 signature does not verify.

The response is **graduated by which layer was touched**, because the fixed and
regenerable layers call for opposite reactions:

| Breach location | Reaction | Automatic? |
|-----------------|----------|-----------|
| **Regenerable layer** (forged dream, drifted interpreted cluster, orphan derived record) | Quarantine the suspect records → **reset-from-raw** (already exists). The seed is intact; regenerate. | Yes — routine |
| **Fixed layer** (Constitution fingerprint, golden set, an unrecognized signing key, gate-ledger inconsistency) | **Fail-closed freeze**: halt the scheduler, refuse new token mints, stop self-mod, drop to read-only — pending human inspection. | Yes — alarm |

**"Recovery mode" is a launch flag, not a separate OS.** It is simply the system
started with: self-mod disabled, scheduler halted, network sealed, and only the
verifier + a read-only console running. No special boot image — a `--recovery`
(or fail-closed default) startup state.

**The tripwire mechanism** ("kill switch") trips proportionally:
- regenerable breach → contain + rebuild (no human needed);
- fixed-layer breach → freeze + wait for the human.

**Honest caveat (must be stated, not hidden):** a kill switch is a *control*, and a
sufficiently compromised core could in principle suppress its own tripwire — the
watcher and the watched share a machine. The tripwire's integrity therefore rests on
the same structural foundations as everything else: the verifier reads **append-only**
attestations signed by a key the core process cannot rewrite (owner key in Secure
Enclave for the fixed-layer attestations). This **raises assurance; it does not make
tampering impossible.** The strongest guarantee remains the boring one: **the raw
seed is immutable and offline-backed (Phase 9), so the worst case is always "rebuild
from ground truth," never "irrecoverable."**

---

## 2. Verification — who, and at what latency

**The current gap:** attestations are *written* but nothing systematically *reads
them back*. They are a flight recorder no one plays. Closing this is the new work.
It splits along a latency axis:

### 2a. Inline (synchronous, blocking) — ONLY the privileged gates
When code execution requests a secret, or the self-mod loop tries to apply a change,
the attestation is verified **before the operation proceeds**. This is the
"code execution → needs secret → creates attestation → validated by the guard" loop.

**It must be cheap** — a signature check + a scope check, microseconds — **never a
full chain-walk.** The gate verifies the *immediate* token and signature, not the
entire ancestry. If inline verification ever requires walking the derivation graph,
it is in the wrong tier.

### 2b. Asynchronous (the auditor agent) — everything else, incl. deep chain-walks
A **separate auditor agent** walks the attestation graph and checks the expensive
properties:
- every `DerivedStore` record traces to authored leaves;
- no dreamer attestation references an observed-provenance input;
- Constitution fingerprints are consistent across a run;
- all signatures hold;
- every privileged access in the Vault audit log corresponds to a minted/authorized
  token (and every denial is recorded).

Auditor properties:
- **Separate role**, narrow scope: *read* attestations + Vault audit log, *raise*
  findings — **no write** to anything it audits (it cannot fix, only flag).
- **Scheduled in troughs** (like dreaming), **not parallel-on-every-operation** —
  parallel verification of every transaction would make the auditor a bottleneck and
  a contention source.
- Its findings **feed the §1 tripwire**: a chain break in the regenerable layer →
  quarantine+rebuild; in the fixed layer → freeze.

### 2c. The principle
**Verify inline only what must block; defer everything else to the auditor.** The
inline signature check already stops the dangerous *immediate* action; the async
sweep catches subtler *structural* drift, which does not need millisecond latency.
The auditor finding a forged attestation 30 s later is fine — the reflex already
fired.

---

## 3. The fast path (your "veins and nerves," made precise)
- **Reflex (inline, local, µs):** object-capability handle check; Vault scope check;
  attestation signature check at a privileged gate. No deliberation — a handle grants
  or it doesn't.
- **Cognition (async, trough-scheduled):** auditor chain-walks; drift computation;
  alignment metrics.
- **The correction to "everything as fast as possible":** speed comes from keeping
  most signals *off* the expensive path, not from speeding the expensive path up.
  This is the object-capability instinct already in the system — extend it, don't
  fight it.

---

## 4. The Ambassador — the conversational front door

What you talk to when text interaction is live: a single conversational role with a
**read-only window** into the graph, that **delegates** rather than acts, internalizes
the conversation, and can **talk about the system itself**.

### Properties that make it safe and make it work
- **Read-only on the knowledge graph.** Queries the mirror through a MirrorView-style
  read handle; **no write path** to authored content. It can *propose* (a note to
  ingest, a task to queue) — proposals go through the same gates as everything else.
- **It delegates; it does not execute.** The Ambassador is the *conversational layer
  of the supervisor*: it interprets intent, mints an appropriately-scoped task, hands
  it to a worker. It never holds the worker's capabilities. "Model advises, code acts"
  at the interface.
- **Two distinct reading scopes — keeping them distinct is the firewall:**
  1. the **authored mirror** (to reflect you), and
  2. the system's own **operational state** — attestations, gate ledger, drift
     metrics, phase status — so it can answer "what have you been doing?" and "is the
     system healthy?".
  Scope (2) is **new**: the Ambassador is the one role that may *read the audit layer
  to narrate it*. It still cannot write to it.
- **Conversations with it are `authored-dialogue`** — they feed back into the corpus
  as a distinct provenance (your words to it are more yours than its words to you).
  Chatting with the Ambassador is itself a form of feeding the system — closing the
  capture loop.

### What already exists vs. what's new
- **Exists:** the Phase-6 interface gateway (Zone B), reached over Tailscale; the
  supervisor/queue machinery; MirrorView; the agent/Constitution framing.
- **New work:**
  1. the **operational-introspection read scope** (a read handle over
     attestations / gate ledger / drift metrics / phase status);
  2. the **delegation grammar** (turning "look into X" into a scoped, gated task);
  3. the **system-narration capability** — the Ambassador knowing enough about its
     own architecture to explain itself. Fittingly, the **white papers + design notes
     are the corpus** for this: ingest them as a `curated` system-self-knowledge graph
     the Ambassador can read (its own graph, never merged into the authored mirror —
     same firewall as book dreaming).

### Boundaries
- The Ambassador never writes authored content, never holds worker capabilities,
  never mutates the audit layer, never bypasses a gate. It is a *window and a
  switchboard*, not a hand.
- Consequential-advice-defers applies (it is the voice that talks about health/
  financial/legal correlations — it defers, with uncertainty, to the owner + a pro).

---

## 5. How the three connect
The auditor (§2) writes findings as attestations; the tripwire (§1) reacts to them;
the Ambassador (§4) can *read and narrate* both — "I quarantined a drifted cluster at
03:40 and rebuilt it; the fixed layer is intact." The nervous system senses (auditor),
reflexes (tripwire), and reports (Ambassador) — fast where it must be, deliberate
where it can be, and always able to tell you the truth about its own state.

---

## 6. Open questions
- Auditor cadence (every trough? every N operations? on every self-mod attempt
  regardless?).
- Does a fixed-layer freeze auto-notify the owner (push via the interface gateway),
  or wait to be asked? (Lean: notify — a freeze the owner doesn't know about is a
  silent outage.)
- Ambassador: one always-warm small model, or minted per-conversation? (Lean:
  the pinned tier hosts it — it must be responsive.)
- How much system-self-knowledge to expose — full architecture, or a curated subset?
  (Security: explaining the design is fine; exposing live secrets/keys is never.)
