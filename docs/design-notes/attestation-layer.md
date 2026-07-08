---
type: design-note
id: dn-attestation-layer
status: draft
implementation: partial   # corpus-audit 2026-07 verification
created: 2026-06-27
updated: 2026-07-01
links: []
supersedes: null
superseded_by: null
warrant: null
---

# Design note — Attestation layer: verifiable chain of custody for agent actions

*Family tag → family 2 (regenerable derivation): an attestation chain is a signed path in the derivation DAG, terminating in authored leaves. See [`../NOTATION.md`](../NOTATION.md).*

**Status:** design only. Extends `vault-runtime-auth.md` and
`WHITEPAPER-FORMAL-PROPERTIES.md`. The building blocks are already in place; this
note adds the signing layer that ties them into a verifiable chain. Honor at Phase
10 or alongside Vault integration (Phase 5+). Start simple — attestation records
without signatures first; add the signing key once the structure is proven.

---

## 0. The core idea

A Vault token is already an attestation — a cryptographically-backed claim that
"agent role X was authorized to access resources Y at time T." What's missing is
an equivalent claim for the *action itself*: "agent X performed operation A on
inputs I (by hash), producing output O (by hash), under authorization T, with
Constitution at fingerprint F."

Chain those records together and every piece of derived content acquires a
**verifiable lineage** — traceable back to the authored raw through a sequence of
authorized, signed, content-addressed steps.

---

## 1. Two proof layers — static and runtime

The formal properties document (WHITEPAPER-FORMAL-PROPERTIES.md) is the
**static proof layer**: what the code cannot do, proven before runtime (import lint,
type constraints, FSM checks). Attestations are the **runtime proof layer**: what
the code actually did, proven after each interaction. They are complementary, not
redundant:

| | Static proof | Runtime attestation |
|--|-------------|-------------------|
| Claim | "The dreamer cannot import edge" | "The dreamer did not access financial credentials in interaction 42" |
| Evidence | Import lint + CI | Vault audit log + signed attestation record |
| When | Before execution | After each interaction |
| Forgeable? | Requires code change | Requires compromising the signing key |

Together they close the gap between "the system was designed correctly" and "the
system behaved correctly in this specific interaction."

---

## 2. Attestation anatomy

```python
@dataclass
class Attestation:
    id: str                    # content-addressed: SHA-256(all fields below)
    timestamp: str             # ISO-8601
    agent_role: str            # "dreamer", "bridge", "correlator", …
    action: str                # "dream_pass", "ingest_note", "gate_decision", …
    constitution_fingerprint: str  # from core/constitution.py — always present
    vault_token_accessor: str  # Vault's non-sensitive token identifier (not the token)
    input_hashes: list[str]    # SHA-256 of each input (authored notes, biometric
                               # aggregates, prior interpretations — whatever fed this)
    output_hashes: list[str]   # SHA-256 of each output written to any store
    derived_from_ids: list[str]  # attestation IDs of prior attestations whose
                                 # outputs are in input_hashes — the chain links
    signature: str             # Ed25519 sig over all fields above, by supervisor key
```

The attestation ID is `SHA-256(all fields except signature)` — so the ID is stable
and the signature is verifiable independently. The `derived_from_ids` field is what
creates the chain: each attestation references the attestations whose outputs it
consumed as inputs.

---

## 3. Attestation types

**Ingest attestation** — vault watcher / Phase-1 pipeline:
```
role: "vault_watcher"
action: "ingest_note"
inputs: [file path + mtime]
outputs: [content digest, vector digest]
vault_token_accessor: (watcher's token)
constitution_fingerprint: F
```
This is signed provenance for the authored layer — not just "this digest came from
path P" (the Source type already gives that) but "the authorized watcher ingested
it under Constitution F."

**Dream attestation** — dreamer / adjudicator:
```
role: "dreamer"
action: "dream_pass"
inputs: [authored note digests used as evidence]
outputs: [interpreted record IDs written to DerivedStore]
vault_token_accessor: (dreamer's ephemeral token)
constitution_fingerprint: F
```
Every interpretation in DerivedStore now has a provable lineage to specific authored
content, through a specific authorized interaction, under a specific Constitution.

**Correlator attestation** — cross-source synthesis:
```
role: "correlator"
action: "correlate"
inputs: [interpreted record IDs, biometric aggregate IDs]
outputs: [correlation record IDs]
vault_token_accessor: (correlator's ephemeral token)
```
Note: biometric aggregates (observed) are referenced by ID, never by content — the
attestation proves the correlator consumed these specific aggregates without exposing
the raw biometric data to the attestation record.

**Gate attestation** — the highest-stakes record:
```
role: "gate"
action: "approve" | "reject"
inputs: [proposed change hash, baseline hash, drift metric]
outputs: [applied change hash] | []
vault_token_accessor: (gate's token)
constitution_fingerprint: F
signature_by: owner's key (hardware-bound if possible)
```
Gate attestations are the only ones signed by the **owner's key** (stored in Keychain
/ Secure Enclave), not just the supervisor's key. This makes gate decisions
non-repudiable — the owner's signature proves they personally approved the change.

---

## 4. The signing infrastructure

**Supervisor signing key:** Ed25519, generated once, stored in Vault KV under a path
only the supervisor role can read. Used for all attestations except gate decisions.

**Owner signing key:** Ed25519, stored in macOS Keychain, hardware-bound to Secure
Enclave if possible. Used only for gate decision attestations. The owner signs gate
decisions — not the supervisor, not an agent.

**AttestationStore:** an append-only SQLite table (separate from DerivedStore —
attestations are meta-records about the system, not derived content):
```sql
CREATE TABLE attestations (
  id TEXT PRIMARY KEY,          -- SHA-256 content address
  timestamp TEXT NOT NULL,
  agent_role TEXT NOT NULL,
  action TEXT NOT NULL,
  payload_json TEXT NOT NULL,   -- the full Attestation record as JSON
  signature TEXT NOT NULL,      -- Ed25519 sig, base64
  signer TEXT NOT NULL          -- "supervisor" | "owner"
);
CREATE INDEX att_role_ts ON attestations(agent_role, timestamp);
CREATE INDEX att_output ON attestations(json_each(payload_json, '$.output_hashes'));
```

Append-only is enforced structurally — `AttestationStore` has no `delete` or
`update` method. The gate's purge-raw action appends a deletion attestation rather
than removing records.

---

## 5. DerivedStore integration

Every record written to DerivedStore gains an `attestation_id` column:
```sql
ALTER TABLE derived ADD COLUMN attestation_id TEXT REFERENCES attestations(id);
```
This links every interpretation, correlation, and curation record to the signed
attestation that produced it. To verify a derived record: retrieve its attestation,
check the signature, verify the input hashes match the content still in the raw/
vector stores, confirm the Constitution fingerprint matches the live Constitution.

This makes "derived is regenerable from raw" *verifiable* rather than just promised:
you can prove that a specific interpretation was produced from specific authored
content by a specific authorized agent under a specific Constitution — or detect if
something has changed.

---

## 6. The alignment connection

The attestation chain is a behavioral sensor for the alignment subsystem
(alignment-subsystem.md):

- **Vault denials** (authorization attempted, refused): behavioral signal — an agent
  that repeatedly attempts out-of-scope access is exhibiting drift.
- **Attestation gaps**: a DerivedStore record without a valid attestation chain is
  suspect — it either predates the attestation layer or was written outside the
  authorized path.
- **Constitutional drift**: if the Constitution fingerprint in a run of attestations
  shifts, something changed the Constitution — this is the "boiling frog" drift
  detection made concrete.
- **Input-hash audit**: the correlator's attestation lists the exact biometric
  aggregate IDs it consumed. If those IDs ever include records with `observed`
  provenance that weren't properly aggregated, the chain exposes it.

The alignment report can include an attestation health metric: "X% of derived records
have complete, valid attestation chains back to authored content." Degradation of
that metric is a structural alignment signal.

---

## 7. What's already in place (the building blocks)

| Building block | Status | Notes |
|---------------|--------|-------|
| Content-addressed digests | ✅ Phase 1 | SHA-256 on all authored content |
| Constitution fingerprint | ✅ Phase 0 | `core/constitution.py` |
| `derived_from` edges + acyclicity | ✅ Hardening | The derivation graph |
| Vault token accessor | ✅ (with Vault) | Non-sensitive, loggable |
| Ed25519 signing | 🔲 | One key pair; straightforward to add |
| AttestationStore | 🔲 | Append-only SQLite; small schema |
| DerivedStore `attestation_id` | 🔲 | One column migration |

The only new pieces are the signing key, the store, and the column. Everything else
is already content-addressed and fingerprintable.

---

## 8. Build guidance

**Start without signatures.** Build the `Attestation` dataclass and `AttestationStore`
first, write attestation records for every agent action, wire `attestation_id` into
DerivedStore — but leave `signature` as an empty string initially. Verify the chain
structure is correct and the records are complete before adding the cryptographic
layer. A chain without signatures is still a useful audit trail; it just isn't
tamper-evident yet.

**Add signatures second.** Generate the supervisor Ed25519 key pair, store the
private key in Vault KV, store the public key in the repo (it's public). Add the
signing step to the supervisor's token-minting/action-dispatching flow. The
`verify_attestation(id)` function is then a standalone tool the owner can run.

**Gate attestations last.** The owner signing key and hardware binding are the most
sensitive piece. Add after the supervisor layer is working.
