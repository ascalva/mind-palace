---
type: build-plan
id: bp-145
track: workflow
status: proposed
design_ref:
  - docs/design-notes/dn-typed-workflow-registry.md
contract: builder
write_scope:
  - ops/registry/**
  - scripts/registry.py
  - tests/unit/test_registry_admission.py
  - tests/integrity/test_registry_signature_ratchet.py
session_budget: 1
cost:
  estimate:
    model: opus
    tokens: 350k
  actual: null
depends_on: [bp-140, bp-142, bp-144]
parallelizable_with: []
created: 2026-07-27
updated: 2026-07-27
links:
  - docs/design-notes/dn-typed-workflow-registry.md
  - docs/build-plans/bp-144/plan.md
  - docs/build-plans/bp-142/plan.md
re_entry: null
supersedes: null
superseded_by: null
warrant: null
---

# Build Plan — Signed admission: no unsigned path to `ratified`, verified twice

## 0. Mode & provenance

Investigation and planning produced this plan during `/graduate` of
`dn-typed-workflow-registry` (ratified 2026-07-27); it graduates the second half of the
note's license (iii) — "the signed transition event + verification (adopts the
separately-landed key onboarding)". Implementation proceeds item-by-item on owner approval;
the `proposed → ready` blessing is the owner's alone, and nothing in this plan performs or
enables an agent-side blessing.

## 1. Objective

Make the registry refuse an unsigned privileged transition at admission and re-verify every
privileged transition in CI, so invariant 3 — "no unsigned path to `ratified` exists in the
schema — not flagged off, absent" — is a property of the type, not of a check.

## 2. Context manifest

1. `docs/design-notes/dn-typed-workflow-registry.md` — §2.4.1 (the event and the
   **two** verification sites), §2.5.1 (the asymmetry made structural: "an unsigned
   `→ratified` event is malformed input, rejected at the type level"), §2.5.3 (the recorded
   collisions with the ratified autopilot note), §2.9 invariants 3 and 6.
2. `docs/build-plans/bp-144/plan.md` §6 — `canonical_transition`, `TransitionPayload`,
   `SignedTransition`, `TrustStore`, `body_hash`, `PRIVILEGED_TARGETS`. **The primitive is
   pinned there verbatim; do not re-read the design note for it.**
3. `docs/build-plans/bp-144/journal.md` — what landed and what the ceremony still owes.
4. `docs/build-plans/bp-140/plan.md` §6.2 (the `events` table, including the
   already-present nullable `signature`/`signer` columns) and §6.6 (the fold rule).
5. `docs/build-plans/bp-142/plan.md` §6.2/§6.5 — the snapshot loader and the `integrity`
   ratchet this plan extends with a second leg.
6. `docs/design-notes/dn-autopilot-and-delegated-blessing.md` §2.3 — the ratified grant
   mechanics. ⚑ Read it to know what this plan must **not** change (§9).
7. `docs/build-plans/bp-145/journal.md`.

### DRY audit — does `core/` (or the wider tree) already have this?

- **Signature verification?** `ops/transition_sig.py` (bp-144), which itself imports
  `core.attestation.crypto`. **Import it; implement nothing.** A second verifier in
  `ops/registry/` would be the third implementation of Ed25519 verification in this repo and
  is exactly the defect the note's §2.4.3 ruling exists to prevent.
- **A monotonic append-only signed store with admission rules?** `core/stores/verdicts.py`
  is the shape, in core, for verdicts. Not reusable (zone, subject matter); the *pattern*
  — "verification is public-key-only; monotonic-seq enforcement is the store's job, not the
  pure layer's" (`core/verdict/payload.py:1-8`) — is what this plan copies: `transition_sig`
  stays pure, the registry does admission.
- **A CI-side integrity check?** `tests/integrity/` (marker: "the non-skippable CI gate") and
  bp-142's `test_registry_export_ratchet.py`. **A second file in the same directory**, not a
  second mechanism.
- **`core/` audit:** core owns the crypto (imported) and nothing else here.

## 3. Investigation & grounding

- **Q1 — where are the two verification sites?** Note §2.4.1, verbatim: "Twice,
  deliberately: at **admission** (the registry refuses an unsigned privileged event — the
  convenient check) and at **CI/export** (the ratchet re-verifies every privileged transition
  in the log against the enrolled public keys — the check outside the agent's reach…). A
  local check alone is a local check; the CI leg is what makes patching the local verifier
  pointless." Both are required; neither substitutes.
- **Q2 — what makes it a *schema* property rather than a check?** Note §2.5.1: "the registry
  schema admits **no unsigned path** to `ratified` — there is no flag, no config, no
  privileged role that waives the signature. An unsigned `→ratified` event is malformed
  input, rejected at the type level." ⇒ Pinned in §6.1: the admission path constructs a
  `PrivilegedEvent` type whose construction *requires* a verified `SignedTransition`; there
  is no code path from a raw dict to a stored `→ratified` event. A boolean parameter that
  could waive it would be exactly the "flagged off" state the note forbids.
- **Q3 — does `proposed → ready` need a signature?** **No.** §2.5.1's table is explicit and
  §2.5.2 turns it into a declared independence: "`bp-138`/`bp-139` … automate the gate with
  **no** signing requirement; the hardware key serves the gate autopilot will **never**
  touch." Adding a signature requirement to `ready` would silently block the autopilot track
  the note declares independent. `PRIVILEGED_TARGETS = {"ratified"}` (bp-144 §6.3) is the
  operative constant and must not be widened here.
- **Q4 — can CI verify without the machine-level store?** Yes, by the same argument as
  bp-142 §3 Q2: the committed snapshot (`ops/registry/snapshot/events.jsonl`) carries the
  `signature`/`signer` columns, and `ops/transition_keys/*.pub` is committed. The CI leg
  therefore reads two committed inputs and nothing else — hermetic. Verified: bp-140 §6.2
  already gives the `events` table nullable `signature`/`signer` columns, so **no
  `ALTER TABLE` is needed** and invariant 1 is never at risk.
- **Q5 — what happens with an empty trust store (no ceremony yet)?** Every signature fails
  to verify, so **every** `→ratified` admission fails. That is the correct fail-closed
  posture for authority — but it would also mean the registry cannot record a ratification
  until the ceremony happens. ⇒ This is *not* a liveness problem, because **the tree remains
  authoritative for status until bp-149 retires the hooks**: the owner ratifies by hand
  exactly as today, and the registry simply has no event for it. Item 27 must make that
  state legible (`doctor` reports "trust store empty — privileged admission unavailable")
  rather than silently red. Recorded in §11.
- **Q6 — what about degraded mode?** bp-141 already queues privileged events unadmitted
  (invariant 6). This plan is what finally gives "admitted" a meaning: reconcile replays a
  queued privileged event through **this** admission path, and it becomes effective only if
  its signature verifies. **The code does not settle** whether bp-141's `queued_privileged`
  entries carry their signature bytes — verify in the landed code; if they do not, that is a
  bp-141 defect (finding, not a workaround).
- **Q7 — does this plan touch the autopilot grant flow?** **No, and it must not.** Note
  §2.5.3 row 1: re-homing the grant record onto an event payload "is an amendment to that
  note, owner-ratified, licensed only after this note is itself ratified" — i.e. an owner
  act, not a builder's. `oq-0037` stays parked (§2.5.3 row 3). This plan stores signatures
  for `→ratified` only and leaves `proposed → ready` mechanics exactly as
  `dn-autopilot-and-delegated-blessing` §2.3 specifies.
- **Q8 — retrofit surface.** This plan changes `ops/registry/store.py`'s `submit()`
  behaviour for one class of event. `grep -rn "submit(" tests/` before starting; any test
  that submits a `transitioned` event with `to_status="ratified"` will start failing and
  must be updated. bp-140's and bp-141's test files are **not** in this plan's `write_scope`
  — if such a test exists, file a finding and stop rather than widening (§10).

**Additional risks or questions surfaced during reading:**

- The CI leg will pass vacuously until the first real signed ratification exists. Same trap
  as bp-142's ratchet — Item 28 must therefore include a **fixture-backed red case**: a
  synthetic log containing an unsigned `→ratified` event must make the integrity test fail
  with a message naming the event.
- A verified signature proves authorization, not correctness of the *fold*. An event whose
  `from_content_hash` does not match the entity's recorded content hash is signed but
  *stale*. Admission must reject that too, or a valid signature over an old pre-image
  becomes a replay. This is the note's own "the pre-image is part of the signed object"
  (§2.4.1) taken to its conclusion; §6.2 pins it.

## 4. Reconciliation

- `ops/registry/store.py::submit` (bp-140) — "Append one event; return its seq. Idempotent on
  event.idempotency_key." → ⚑ **banner: correction.** Its contract narrows: a `transitioned`
  event whose `to_status` is in `PRIVILEGED_TARGETS` is now **rejected** unless it carries a
  verified `SignedTransition` whose `from_content_hash` matches the entity's recorded content
  hash. The docstring gains a banner naming this plan and the note's §2.5.1, so a reader of
  bp-140's text finds the narrowing rather than being surprised by it.
- `ops/registry/pending.py::PRIVILEGED_TARGETS` (bp-141) → **cross-ref: extension.** bp-141's
  set answers "what must not become effective while queued"; bp-144's answers "what must
  carry a signature". They are **deliberately different** (note §2.5.1). Each constant's
  comment must name the other and say why they diverge, so a later reader does not "fix" the
  divergence.
- `ops/registry/schema.md` → **cross-ref: extension**: gains an "Admission" section stating
  the two verification sites and the empty-trust-store posture.
- **Nothing in `docs/design-notes/**` is edited.** The §2.5.3 collisions are the owner's to
  amend; this plan records them and stays inside them.

## 5. Write scope

- `ops/registry/**` — `admission.py` (the privileged-event type and the verification gate),
  edits to `store.py` (submit narrowing), `snapshot.py` (signature columns round-trip),
  `schema.md`.
- `scripts/registry.py` — `bless` (prepare + submit a signed transition), and `doctor` gains
  trust-store status.
- `tests/unit/test_registry_admission.py` — the admission rules and the unrepresentability
  of an unsigned `→ratified`.
- `tests/integrity/test_registry_signature_ratchet.py` — the CI leg: re-verify every
  privileged transition in the committed snapshot.

**Deliberately OUT of scope:** `ops/transition_sig.py` and `ops/transition_keys/**` (bp-144
owns them; this plan **imports** the primitive and **reads** the trust dir); `core/**`;
bp-140's and bp-141's test files (§10 — a finding, not a widening); every hook and
`.claude/settings.json` (`gate-guard` still denies blessings, and it must until bp-149);
`docs/design-notes/**`; the foundation denylist; anything in the autopilot grant flow
(`config/`, the capsule, the HMAC tag — note §1.2 non-goal 3).

## 6. Interfaces pinned inline

### 6.1 Unrepresentability, not a check

```python
# ops/registry/admission.py
@dataclass(frozen=True)
class PrivilegedEvent:
    """A privileged transition that HAS ALREADY VERIFIED. There is no constructor that
    produces one from an unverified input: `admit()` is the only factory, and it either
    returns a PrivilegedEvent or raises. `store.submit()` refuses a `transitioned` event
    whose to_status is in PRIVILEGED_TARGETS unless it is carried by one of these.

    This is the note's §2.5.1 made structural: 'the registry schema admits NO unsigned path
    to ratified — there is no flag, no config, no privileged role that waives the signature.
    An unsigned →ratified event is malformed input, rejected at the type level.'
    ⚑ Adding a `skip_verify: bool = False` parameter anywhere on this path would recreate
    exactly the 'flagged off' state invariant 3 forbids. There is no such parameter."""
    event: Event
    signed: SignedTransition
    verified_under: str          # the trust-store label whose key validated it

def admit(registry: Registry, event: Event, signed: SignedTransition,
          trust: TrustStore) -> PrivilegedEvent:
    """Raises AdmissionError unless ALL of:
      1. signed.verify(trust) is True under signed.signer's enrolled key (bp-144 §6.3);
      2. signed.payload's five-tuple equals the event's (entity_id, from_status,
         from_content_hash, to_status, to_content_hash) — the signature covers THIS event;
      3. signed.payload.from_content_hash == registry.fold(entity_id).content_hash
         — the pre-image is the entity's ACTUAL prior content, not a stale one (replay);
      4. signed.payload.to_status is in PRIVILEGED_TARGETS (else this path is not the one).
    Every failure names WHICH clause failed. A bare False is never returned."""
```

### 6.2 The narrowed `submit`

```python
# ops/registry/store.py  (corrected — see §4 banner)
def submit(self, event: Event, *, privileged: PrivilegedEvent | None = None) -> int:
    """Append one event; return its seq. Idempotent on event.idempotency_key.

    ⚑ CORRECTION (bp-145, design note §2.5.1): if event.kind == "transitioned" and
    event.payload["to_status"] in PRIVILEGED_TARGETS, `privileged` is REQUIRED and its
    `.event` must be this event. Raises AdmissionError otherwise. The signature and signer
    label are persisted into the events table's `signature` / `signer` columns (present and
    nullable since bp-140 §6.2 — no ALTER, invariant 1 intact)."""
```

### 6.3 The CI re-verification leg

```python
# tests/integrity/test_registry_signature_ratchet.py
# Hermetic inputs, both committed, no machine-level store (note §2.8):
#     ops/registry/snapshot/events.jsonl      — the event log snapshot
#     ops/transition_keys/*.pub               — the enrolled public keys
# For EVERY event in the snapshot with kind == "transitioned" and
# payload["to_status"] in PRIVILEGED_TARGETS:
#     assert the row carries a signature and a signer label
#     assert the signature verifies under THAT label's enrolled key
#     assert the five-tuple in the signature equals the event's fields
# An event failing any clause fails the test, naming the event's seq and entity_id.
```

Note §2.4.1's justification, verbatim: "A local check alone is a local check; the CI leg is
what makes patching the local verifier pointless."

### 6.4 CLI additions

```
uv run scripts/registry.py bless <ref> --to ratified --signed <signed.json>
uv run scripts/registry.py doctor        # gains: trust-store labels, privileged-admission availability
uv run scripts/registry.py verify-log    # re-run the CI leg locally over the snapshot
```

⚑ `bless` **does not sign**. It takes an already-signed payload produced by
`scripts/sign_transition.py` (bp-144 §6.6) — which itself signs via `--external` on the
owner's token. No agent-reachable path produces a signature. This is what keeps
`draft → ratified` owner-only in fact and not merely by policy.

### 6.5 Invariants (note §2.9, verbatim)

1. No event is ever mutated or deleted; corrections are events.
3. No unsigned path to `ratified` exists in the schema — not flagged off, absent.
6. A degraded-mode blessing is queued, not effective; authority never degrades.
9. The registry holds no secret … public keys and signatures only (NN-10).

## 7. Items

### Item 25 — the admission gate

- **Objective:** `admit()` + `PrivilegedEvent`, with all four clauses and named failures.
- **Files:** `ops/registry/admission.py`, `tests/unit/test_registry_admission.py`
- **Acceptance test:** `uv run pytest tests/unit/test_registry_admission.py -q` green: a
  correctly signed transition admits; each of the four clauses is violated in turn and the
  raised error names that clause. Includes the **stale pre-image** case (clause 3): a
  signature valid over an older `from_content_hash` is rejected.
- **Falsifier:** ⚑ a signature produced for entity A admits for entity B (or for a different
  `to_status`). The five-tuple binding would then not be doing its job, and finding-0206's
  forged flip survives in a new form.
- **Invariant(s) it must not violate:** invariant 3 — no parameter, flag, or environment
  variable may waive verification. Grep the diff for `skip`, `force`, `unsafe`, `bypass`
  before committing.
- **Touches stored data?** No — pure verification.
- **Parallelizable?** No.  **Depends on:** bp-144 Items 20–22.

### Item 26 — the narrowed `submit`, and signature persistence

- **Objective:** `store.submit()` refuses an unsigned privileged event and persists the
  signature/signer of an admitted one.
- **Files:** `ops/registry/store.py`, `ops/registry/snapshot.py`,
  `tests/unit/test_registry_admission.py`
- **Acceptance test:** submitting a `transitioned` to `ratified` without `privileged=`
  raises; with it, the row's `signature`/`signer` columns are populated; a snapshot
  round-trip preserves both byte-for-byte.
- **Falsifier:** ⚑ **the unsigned path still exists somewhere** — prove its absence
  actively, not by inspection: an AST/grep scan asserting that the only assignment to
  `to_status == "ratified"` in `ops/registry/**` flows through `admit()`. If a second path
  exists, invariant 3 is a convention, not a schema property, and the note's foreclosure
  "at the frame" has not been achieved.
- **Invariant(s) it must not violate:** invariants 1 and 3; **no `ALTER TABLE`** (the columns
  already exist, bp-140 §6.2).
- **Touches stored data?** Yes — the registry's own store. Dry-run: `verify-log` before and
  after.
- **Parallelizable?** No.  **Depends on:** Item 25.

### Item 27 — the empty-trust-store posture, made legible

- **Objective:** with no key enrolled, the system says so plainly and nothing pretends to
  work.
- **Files:** `scripts/registry.py`, `ops/registry/admission.py`, `ops/registry/schema.md`,
  `tests/unit/test_registry_admission.py`
- **Acceptance test:** `uv run scripts/registry.py doctor` against an empty
  `ops/transition_keys/` prints `privileged admission: UNAVAILABLE (trust store empty — key
  ceremony pending)` and exits **0** (this is a legitimate pre-ceremony state, not an
  error); `bless` in that state exits non-zero with the same reason.
- **Falsifier:** the empty-trust state is reported as a generic verification failure
  indistinguishable from a bad signature. An operator would then read "signature invalid"
  when the truth is "no keys enrolled" — the exact confusion bp-144 §3's risk note warns
  about, one layer up.
- **Invariant(s) it must not violate:** authority never degrades (invariant 6) — an empty
  trust store must never fall back to accepting unsigned events.
- **Touches stored data?** No.
- **Parallelizable?** Yes.  **Depends on:** Item 25.

### Item 28 — the CI leg, with a fixture-backed red case

- **Objective:** an `integrity`-marked test that re-verifies every privileged transition in
  the committed snapshot, and that has been **observed red**.
- **Files:** `tests/integrity/test_registry_signature_ratchet.py`
- **Acceptance test:** `uv run pytest -q -m integrity` green against the committed snapshot;
  the test reads only `ops/registry/snapshot/events.jsonl` and `ops/transition_keys/*.pub`
  (assert it never opens `~/.mind-palace/`).
- **Falsifier:** ⚑ **the test is vacuously green** (no privileged transitions exist yet, and
  none will until the ceremony). It must therefore also build a **synthetic** snapshot
  containing (a) an unsigned `→ratified`, (b) a `→ratified` signed by a non-enrolled key, and
  (c) a `→ratified` whose signature covers a different five-tuple — and assert **red** for
  each, with the failing seq named. A ratchet never observed red is not a ratchet.
- **Invariant(s) it must not violate:** hermeticity — two committed inputs, no network, no
  machine-level store.
- **Touches stored data?** No — temp paths and fixtures only.
- **Parallelizable?** No.  **Depends on:** Items 25, 26.

## 8. Math carried explicitly

- **The two-site verification of the transition commitment** — *measures:* whether a stored
  privileged transition is, and remains, backed by an owner authorization over its exact
  pre-image and post-image. *valid when:* the two sites are genuinely independent — the
  admission check runs where the agent acts, the CI check runs where the agent cannot patch
  it, and both read the same committed public keys. *fails its keep if:* the CI leg's inputs
  are ever derived from the local store (then it is the same check twice, and note §2.4.1's
  "a local check alone is a local check" applies), or the leg is vacuously green with no
  observed red case (Item 28's falsifier).
- The signature primitive itself is bp-144's field-guide entry; it is imported here, not
  implemented.

## 9. Non-goals

- ⚑ **No signing.** No agent-reachable code path produces a signature. `bless` consumes one.
- ⚑ **No signature requirement on `proposed → ready`.** §2.5.1 and §2.5.2 forbid it, and it
  would block `bp-138`/`bp-139`, declared independent by §3(5).
- **No change to blessing semantics** — the capsule hash, the HMAC attestation tag, the halt
  list, P1–P5 remain `dn-autopilot-and-delegated-blessing`'s (note §1.2 non-goal 3). **No
  answer to `oq-0037`** (§2.5.3 row 3, parked).
- **No re-homing of the grant record** onto an event payload — §2.5.3 row 1 makes that an
  owner-ratified amendment, not a build act.
- **No hook change.** `gate-guard` still denies agent blessings; the tree is still
  authoritative for status. bp-149 (blocked) is the only plan that changes that.
- **No key ceremony, no enrolled key.** bp-144 §9 and note §1.2 non-goal 1.
- **No `ALTER TABLE`** — the columns exist.
- **No new dependency.**

## 10. Stop-and-raise conditions

- A test in bp-140's or bp-141's files must change (§3 Q8) — file a finding and stop; those
  files are not in this plan's `write_scope` and routing around the guard is forbidden.
- bp-141's queued privileged events do not carry their signature bytes (§3 Q6) — bp-141
  defect; finding, stop, do not work around.
- Item 26's scan finds a second path to `ratified` that cannot be removed within this
  `write_scope` — stop; invariant 3 is not achievable and that is a design-level report.
- The owner asks for `proposed → ready` to be signed — that is an amendment to a ratified
  note; park with a re-entry condition and surface it. Never implement it under this plan.
- Any blessing this plan would have to perform — it must not.

## 11. Parked decisions

| Decision | Default recorded | Rejected alternatives (why) | Re-entry condition |
|---|---|---|---|
| Behaviour with an empty trust store | privileged admission **unavailable**, reported plainly, exit 0 from `doctor` | (a) treat as a hard error — the pre-ceremony state is legitimate and would make every `doctor` run red; (b) fall back to unsigned — breaches invariant 6 outright | The key ceremony enrolls the first public key |
| Grant record (P1–P5, HMAC tag) as an event payload | **not done** — the ratified autopilot note's commit mechanics govern | doing it now — note §2.5.3 row 1 makes it an owner-ratified amendment | The owner amends `dn-autopilot-and-delegated-blessing` §2.3 |
| Batch signature over a set of five-tuples | not built (the note's own parked row) | — | Owner hits the per-touch friction on a real batch |
| Deskcheck verdict signing | unsigned, owner-by-hand (note §2.5.2 [INFERENCE]) | signing it — reversible, so §2.5.2's discriminator classifies it out | Observed verdict forgery, or an owner ruling |

## 12. Dependency & ordering summary

**Within the plan.** Item 25 (pure verification, no writes) → Item 26 (narrows a write path)
→ Item 28 (the CI leg); Item 27 is parallel with 26. Blast-radius order holds: verification
before persistence, persistence before the ratchet that polices it.

**Across plans.** `depends_on: [bp-140, bp-142, bp-144]` — the store, the snapshot/ratchet
surface, and the signing primitive. `parallelizable_with: []` — it shares `ops/registry/**`
with bp-141/142/143/146 and imports bp-144's module, so it runs alone. **bp-149 (hook
retirement) depends on this plan**: `gate-guard`'s guarantee ("owner-only status flips denied
pre-hoc") is only replaceable once an unsigned `→ratified` is unrepresentable **and** the CI
leg has been observed red. `bp-138`/`bp-139` are unaffected — the note's §2.5.2 declares the
signing track and the autopilot track independent, and this plan deliberately leaves
`proposed → ready` unsigned.
