# Prompt/Constitution Integrity Audit — Tamper & Injection

**Date:** 2026-07-02. **Scope:** read-only investigation of prompt integrity across the live
dispatch path. No code, test, or config was changed. Where a design note and the code disagree,
the code is reported as ground truth and the divergence is flagged. All cited logic tests were
run this session (94/94 passed: `tests/adversarial`, `tests/integrity`,
`tests/unit/test_constitution.py`, `tests/unit/test_budget.py`, `tests/unit/test_factory_roles.py`,
`tests/unit/test_factory_tools.py`, `tests/integration/test_attestation_store.py`,
`tests/integration/test_ambassador.py`, `tests/integration/test_ambassador_budget.py`).

## The two threats

**Threat A — prompt injection:** adversarial instructions arriving *inside ingested content*
(a note today; web/email/observed exhaust later), defended by the provenance firewall
(`MIRROR_READABLE` typing, `MirrorView`), the capability ceiling, and treating content as inert
data — hashing does nothing against this. **Threat B — prompt/Constitution tampering:** the
*governing text or the assembly logic itself* being altered so the model runs under different
values than intended — this is the domain of fingerprinting/hashing the prompts that will be
passed, and a hash only helps if something compares it and refuses on mismatch.

---

## G1 — What is fingerprinted today

**Verdict: CLOSED** (as a mechanism — but its coverage is exactly one file).

`constitution_fingerprint()` at `core/constitution.py:31-34` computes SHA-256 over
`load_constitution()` — the raw text of `CONSTITUTION.md` (`core/constitution.py:27-28`),
UTF-8 encoded. Tested: `tests/unit/test_constitution.py::test_fingerprint_stable_and_sha256`.

**Inside the hash:** the raw bytes of `CONSTITUTION.md`, nothing else.
**Not inside the hash:** the role prompts (`AMBASSADOR_ROLE` at `agents/ambassador/agent.py:40-51`,
`CLASSIFIER_ROLE` at `agents/ambassador/intent.py:121-131`, `BASE_ROLES` at
`core/factory/roles.py:46-87`), the assembly logic (`frame_context`,
`core/constitution.py:37-56`; `Budgeter.assemble`, `scheduler/budget.py:96-166`), retrieved
chunks, history, task text, scope grants, and config.

Two properties worth stating precisely:

1. `load_constitution()` is `@lru_cache(maxsize=1)` (`core/constitution.py:26`). The fingerprint
   and every framed prompt use the *same process-start snapshot*, so the fingerprint recorded in
   attestations faithfully identifies the Constitution text actually placed in prompts. The flip
   side: an on-disk edit to `CONSTITUTION.md` mid-run is invisible to both the prompts and the
   fingerprint until process restart.
2. A blessed anchor exists and matches: `eval/golden/baseline.json` `drift.constitution_fingerprint`
   = `1818a46e…c5b2c`, verified this session equal to `shasum -a 256 CONSTITUTION.md`. The
   comparison function is `eval/drift.py:151-158` (`constitution_intact`), and a mismatch
   hard-trips drift to ∞ (`eval/drift.py:127-130`). Where that comparison actually *runs* is G3's
   problem.

## G2 — Is the full assembled prompt hashed?

**Verdict: OPEN.**

The live interactive path is: `Ambassador.respond` → `_dispatch` → `_answer`
(`agents/ambassador/agent.py:110-155`) → `Budgeter.assemble` (`scheduler/budget.py:96-166`) →
`self.server.chat(self.tier, budgeted.messages)` at **`agents/ambassador/agent.py:147`** →
`ModelServer.chat` (`core/models/server.py:31-34`) → `OllamaClient.chat`. Nothing on that path —
or on any other model-call site — hashes the assembled message list. The other dispatch sites,
all equally unhashed: the intent classifier (`agents/ambassador/agent.py:207`), the generic agent
(`core/agent.py:39`), minted agents (`core/factory/factory.py:88-89`), the Librarian
(`core/librarian/librarian.py:157`), and the research term proposer
(`core/librarian/librarian.py:208`). `ModelServer.chat` performs no validation of any kind on
`messages`. Only the Constitution component (G1) has an identity; system prompt + role + scope
framing + retrieved context + history + task, as actually sent, have none.

**Missing:** any hash (or other identity) computed over the complete assembled prompt at any
call site.

## G3 — Detection vs prevention

**Verdict: OPEN** — there is no pre-dispatch gate; integrity is recorded after the fact, and even
the after-the-fact *comparison* does not run in the live loop.

- **No pre-dispatch validation.** No call site listed in G2 checks the prompt, the Constitution
  text, or any hash before `server.chat` fires. Nothing fails closed on mismatch.
- **Post-hoc recording only.** `StoreAttestor.emit` stamps `constitution_fingerprint` into the
  attestation *after* the action (`core/attestation/attestor.py:67-81`).
- **The blessed-anchor comparison is dormant at runtime.** `constitution_intact`
  (`eval/drift.py:151-158`) executes only inside the self-mod validator
  (`ops/selfmod.py:228-244`; `[selfmod]` is OFF) and eval/harness runs. The live palace loop
  builds its `OpsView` with no drift reading (`ops/lifecycle/launcher.py:144`), so the monitor
  snapshot reports `constitution_intact: None` — "not measured this session"
  (`core/ops_view.py:112-120`, `ops/lifecycle/snapshot.py:43`). Startup preflight checks
  Ollama/Vault/podman/data-dir only (`ops/lifecycle/preflight.py:50-108`) — no fingerprint check.
- The design acknowledges this: "attestations are *written* but nothing systematically *reads
  them back*" (`docs/design-notes/nervous-system-and-ambassador.md:69-70`); the tripwire/freeze
  (§1) and the A3 auditor (§2b) of that note are unbuilt (`docs/PROGRESS.md:1273`).

**Missing:** any point on the dispatch path where prompt (or Constitution) integrity is checked
before the model call, failing closed; and any scheduled runtime execution of the existing
fingerprint-vs-blessed-anchor comparison.

## G4 — Uncovered surfaces

| Surface | Covered? | Evidence |
|---|---|---|
| Prompt template / assembly code (`frame_context`, `Budgeter.assemble`) | **Not covered** by any runtime integrity control. Behavior is pinned by tests (`test_constitution_is_outermost_frame`, `tests/integration/test_ambassador_budget.py::test_assembled_context_is_constitution_first`) and git review, but nothing at runtime detects altered assembly logic. | `core/constitution.py:37-56`; `scheduler/budget.py:96-166` |
| Skill definitions | **Not covered — and currently dormant.** `RoleTemplate.skills` is declared (`core/factory/roles.py:33`) but no code anywhere resolves skill names to text or injects them into a prompt (grep: no consumer outside `roles.py`). No integrity control exists; there is also no live surface yet. The invariant that skills never widen capability is structural and tested (`core/factory/roles.py:35-40`; `tests/unit/test_factory_roles.py::test_template_rejects_scope_beyond_max`). | |
| Scope grants | **Split.** The *tool* ceiling is a structural control, not a hash: `scope ⊆ PRE_DECLARED_MAX` refused at construction (`core/factory/roles.py:35-40`), re-intersected at mint (`core/factory/factory.py:129`), enforced at dispatch (`dispatcher_for`, out-of-scope routed to the human gate, `core/factory/factory.py:92-104`). The *credential* grant list `[secrets].grant_roles` is plain TOML overlay config with no integrity check (`core/factory/factory.py:119,155-157`). | tests: `test_all_base_role_scopes_are_within_the_pre_declared_max`, `test_factory_tools.py` |
| Ambassador context-assembly output | **Not covered.** The `budgeted.messages` actually sent are never hashed; the turn's attestation records only the retrieved chunks' digests as `input_hashes` (`agents/ambassador/agent.py:150`), and the STATUS/DREAMS/TASK attestations carry no hashes at all (`agents/ambassador/agent.py:132,135,174`). No output hash of the reply is recorded anywhere on the interactive path. | |
| Retrieved chunks | **Partial.** Content-addressed at ingest (raw store SHA-256) and the digest rides along in retrieval and into the read attestation. But retrieval takes the vector-store row's `text` field at face value — nothing re-verifies the text against its digest (`core/librarian/librarian.py:126-142`), so a mutated LanceDB row would enter the prompt while the attestation records the stale, clean digest. | |

## G5 — Attestation record fidelity vs `attestation-layer.md`

**Verdict: PARTIAL** — the structure is faithful; signing is built and tested but **disabled in
this deployment**; two minor drifts.

Matches the note:
- **Fields** all present — role, action, constitution_fingerprint, vault_token_accessor,
  input_hashes, output_hashes, derived_from_ids, signature (`core/attestation/record.py:50-61`).
- **id = SHA-256 over the canonical payload excluding the signature** (`record.py:63-69,90-93`);
  order-insensitive, reproducible encoding (`record.py:21-46`). Tested:
  `test_id_is_content_addressed_and_order_insensitive`,
  `test_signing_does_not_change_the_content_address`.
- **Append-only store with no update/delete** (`core/attestation/store.py:73-150`; `INSERT OR
  IGNORE` at `store.py:92`). Tested: `test_store_has_no_mutation_api`,
  `test_attestation_store_is_append_only_by_construction`.
- **Ed25519 signing** (`core/attestation/crypto.py`) + verifier with the owner-key policy for
  gate actions (`core/attestation/verify.py:26-46`). Tested:
  `test_emitted_signatures_verify`, `test_tampering_a_field_breaks_the_signature`,
  `test_gate_decisions_must_be_owner_signed`.
- **Standalone verifier script**: `scripts/verify_attestation.py` (single-id chain walk, `--all`,
  `--list`).
- **DerivedStore `attestation_id` link** (`core/stores/derived.py:171-174`).

Drift to report:
1. **Signing is OFF in this deployment.** `[attestation] enabled = false` in
   `config/defaults.toml:146` and `config/local.toml` contains no `[attestation]` section — so
   every live attestation is unsigned records-only (`core/attestation/attestor.py:100-104`). The
   design's own §8 is candid that an unsigned chain "isn't tamper-evident yet"; that caveat
   currently applies to production. (Fail-closed behavior on enable-without-key is correct and
   tested: `attestor.py:105-111`.)
2. **The `signer` field is excluded from the signed payload** along with `signature`
   (`record.py:63-69`), where the note says "SHA-256(all fields except signature)". Benign in
   effect — the verifier selects the public key *by* `signer`, so a relabeled signer fails
   against the wrong key (`verify.py:36-44`) — but it is a divergence from the note's letter.
3. **The note's `att_output` json_each index (§4) was never built** — only `att_role_ts` exists
   (`store.py:23-34`); `producers_of` full-scans (`store.py:117-123`). Functional/performance
   drift only.

## G6 — Coverage of the interactive path

**Verdict: PARTIAL** — the interactive Ambassador *is* attested in running code, but the record
carries no prompt or output identity, and other interactive model calls are unattested.

Emitters in running code: vault watcher ingest (`core/ingest/sync.py:94`), dreamer
(`core/dreaming/dreamer.py:132`), curator (`core/curator/curator.py:163`), dialogue capture
(`core/ingest/dialogue.py:66`), curated ingest (`core/ingest/curated.py:65`), factory token mint
(`core/factory/factory.py:160`), and — interactive — the Ambassador: `read` on
RETRIEVE/EXPLAIN/STATUS/DREAMS, `propose` on TASK (`agents/ambassador/agent.py:132,135,150,174,
217-220`). The attestor is wired on the live path, not just tests: the palace launcher builds the
Ambassador via `build_ambassador` (`ops/lifecycle/launcher.py:117`), which constructs
`build_attestor(cfg)` and injects it (`agents/ambassador/__init__.py:74,88`). Tested:
`tests/integration/test_ambassador.py::test_retrieve_reads_the_mirror_and_captures_the_turn`
asserts `{"read","capture"}` are emitted.

So a prompt-integrity record for live interactions exists **only in the weak sense** that each
turn's attestation carries the Constitution fingerprint (stamped by
`core/attestation/attestor.py:71`, from the same cached load the prompt used — see G1). What is
missing: no `output_hashes` on any interactive attestation (the reply is unrecorded); no hash of
the assembled prompt (G2); the intent-classifier model call is unattested
(`agents/ambassador/agent.py:206-207`); `Agent.respond` (`core/agent.py:39`) and
`MintedAgent.respond` (`core/factory/factory.py:88-89`) advisory calls are unattested (only the
token mint is, `factory.py:159-161`).

## G7 — Threat-A confirmation

**Verdict: PARTIAL** — the ingest-layer and firewall defenses exist, are structural, are tested,
and pass; none depends on hashing. The *model-facing* half of the injection test from the design
note is not implemented.

Present, correct, tested (all passed this session):
- **Injection-as-content:** `tests/adversarial/test_prompt_injection.py::
  test_injected_note_is_authored_content` — a note reading "SYSTEM: ignore all previous
  instructions…" lands as `AUTHORED_SOLO` with no provenance escalation; its markup is parsed as
  data (`core/ingest/pipeline.py` path).
- **Provenance firewall, structural:** `MirrorView` makes a non-mirror-readable row
  *unrepresentable* (`core/mirror.py:62-77`); tested by
  `tests/integrity/test_mirror.py::test_direct_construction_with_a_non_authored_row_is_unrepresentable`
  and `tests/integrity/test_provenance_split.py::test_mirror_view_with_a_curated_row_is_unrepresentable`.
  `MIRROR_READABLE = {authored-solo, authored-dialogue}` (`core/provenance.py:68-70`), tested by
  `test_mirror_readable_is_both_authored_classes_and_excludes_curated`. Provenance cannot be
  laundered: `DerivedStore` has no provenance parameter (`core/stores/derived.py`).
- **Retrieval-side typing:** vector search prefilters by provenance
  (`core/stores/vectorstore.py:108-131`); the Librarian defaults to `MIRROR_READABLE`
  (`core/librarian/librarian.py:126-127`); the Ambassador's EXPLAIN path reaches CURATED only by
  explicit, deliberate provenance (`agents/ambassador/agent.py:128-130`); integration-tested that
  curated content does not reach the model on a RETRIEVE turn
  (`test_retrieve_reads_the_mirror_and_captures_the_turn`, firewall assert at
  `tests/integration/test_ambassador.py:86`) and vice versa
  (`test_explain_reads_the_curated_graph_not_the_mirror`; `tests/integrity/test_curated_firewall.py`).
- **Capability ceiling:** even a fully "obeyed" injection on the interactive path has nothing to
  wield — the Ambassador's scope is deliberately empty (`agents/ambassador/agent.py:58-63`), TASK
  only proposes through the human gate/queue (`agents/ambassador/agent.py:169-175`), and no
  shell/credential/network tool exists in `PRE_DECLARED_MAX` (`core/factory/roles.py:24`).
- **No hashing dependency:** all of the above rest on provenance labels, typed views, prefilters,
  and scope sets; the only hashes involved (content digests) serve dedup/identity, not the
  injection defense.

Missing: the second half of the design-note test
(`docs/design-notes/holistic-testing.md:96-103`) — feeding the injected note through a
dream/retrieval pass and asserting *no behavioral change / no confidence anomaly* — does not
exist. The model-facing defense today is the Constitution-outermost frame plus the grounding
self-check (`core/selfcheck.py:113-150`, flag-not-hide at `agents/ambassador/agent.py:151-154`),
neither of which is exercised against adversarial retrieved content by any test.

## G8 — Vault boundary

**Verdict: CLOSED** (confirmed absence, as designed).

The vault layer performs no prompt-integrity hashing: `config/secrets_backend.py` contains no
fingerprint/hash logic (the words appear only in docstrings about the attestation *join*), and
`docs/design-notes/vault-runtime-auth.md` frames Vault exclusively as per-interaction credential
authorization (§0 table, §2 lifecycle) — capability, not governing text. The only touchpoint with
attestations is the non-secret `accessor` recorded in `vault_token_accessor`
(`config/secrets_backend.py:40-58`, `core/attestation/record.py:59`), which carries authorization
identity, not prompt identity. Nothing in any design note expects the vault to hash prompts.

## G9 — Catch-all: additional integrity gaps found while tracing

1. **The blessed-anchor check never runs in the live loop** (detailed in G3): `[selfmod]` off +
   `OpsView` built without a drift reading (`ops/lifecycle/launcher.py:144`) + no preflight
   fingerprint check ⇒ today, a tampered `CONSTITUTION.md` would be *served to every agent* after
   the next restart and nothing running would notice. The gauge that would catch it exists
   (`eval/drift.py:127-130`) but is only invoked by the disabled self-mod validator and manual
   eval runs.
2. **Retrieved content is injected as `role: "system"` messages.** Both assemblers put RAG chunks
   in system-rank slots (`scheduler/budget.py:148-151`; `core/constitution.py:51-52`). Today only
   owner-authored/curated text can occupy those slots (G7), but this elevates content to
   instruction-rank position — the inert-data posture is register-weakened at exactly the place
   Threat A targets, and the exposure compounds once observed/web provenances ever become
   retrievable.
3. **The assembler accepts arbitrary Constitution text.** `ContextParts.constitution`
   (`scheduler/budget.py:64,97-99`) lets any caller substitute the outermost frame; only tests use
   it today (`tests/unit/test_budget.py:19`), and nothing at dispatch validates that
   `messages[0]` equals the canonical Constitution. A Threat-B seam in the assembly logic itself.
4. **The committed attestation public keys are dev keys whose private seeds are in the repo**
   (`ops/attestation/{supervisor,owner}.pub` ↔ `tests/keys/*.seed`, pinned by
   `tests/integrity/test_attestation_signatures.py::test_committed_pubkeys_match_dev_seeds`, and
   documented as carrying "no production trust" in `ops/attestation/README.md`). Combined with
   signing being OFF (G5), the current attestation trail's tamper-evidence is nominal: the SQLite
   file is mutable on disk, records are unsigned, and until the owner regenerates keys, an
   "owner-signed" gate record would be forgeable by anyone with repo read access.
5. **Chunk text is not re-verified against its digest at retrieval**
   (`core/librarian/librarian.py:130-142`) — a mutated vector-store row reaches the prompt while
   the read attestation records the original clean digest (a false-fidelity record).
6. **Role prompts have no recorded identity.** Attestations record the role *name* only
   (`record.py:53`); which `AMBASSADOR_ROLE`/`BASE_ROLES` text a turn actually ran under is
   unrecorded and unfingerprinted — git is the only control.
7. **The A3 auditor and the tamper tripwire are unbuilt** (`docs/PROGRESS.md:1273`;
   `docs/design-notes/nervous-system-and-ambassador.md` §1–2 are design-only) — so even the
   integrity records that do exist have no systematic reader, and no freeze/quarantine reaction
   path exists.

---

## Bottom line

**Threat A (prompt injection via content): good protection today, for today's surface.** The
defenses are structural (typed `MirrorView`, provenance prefilters, no-launder `DerivedStore`,
empty Ambassador scope, gate-guarded delegation), tested, and passing, and none of them leans on
hashing. The honest boundary: the corpus is currently all owner-authored, the model-facing
non-obedience test is missing (G7), and retrieved content sits in system-role slots (G9.2) — the
posture is strong now but its margin shrinks the day lower-trust provenances (observed, web, the
Hands) become retrievable.

**Threat B (prompt/Constitution tampering): weak protection today.** Exactly one artifact — the
raw `CONSTITUTION.md` — has a cryptographic identity, and it is currently correct (live hash
matches the blessed anchor), but the comparison never executes in the running system, there is no
pre-dispatch gate anywhere, the full assembled prompt / role prompts / assembly code / grant
config have no identity at all, and the attestation trail that records the fingerprint after the
fact is unsigned in this deployment with dev verification anchors. For "the prompts that will be
passed," the system today relies on git and process discipline, not on any runtime integrity
control.

**Cross-reference:** `docs/research/security-planes.md` §2 inherits this gap directly — the
foundation file set's enumeration lists "the Constitution and all assembled-prompt components"
as one entry precisely because the fingerprint-scope gap identified here is unresolved. That
note's foundation-file-set verification is blocking on this audit's findings 3 and 6 in
particular (assembly-logic seam, unfingerprinted role prompts); do not close either gap
independently of the other.
