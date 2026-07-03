> **Archived (2026-07-03 docs cleanup).** The security & attestation track this builder prompt
> scoped is complete — see `docs/PROGRESS.md` (Security & attestation track, 6 steps, 2026-06-27)
> and production Vault standup entries. Kept for historical reference; 0 inbound references.

# Handoff — security & attestation track (ACTUAL BUILD) + test foundation

Eight design notes (in `docs/design-notes/`), the builder prompt, and the exact
PROGRESS.md index lines. This track **builds** the test foundation, the attestation
layer, and the Vault primitives — pulling attestation forward from its default
Phase-10 placement and the Vault primitives forward from Phase 5 (sound: their
building blocks already exist). The full per-interaction token wiring still lands
with the Phase-5 dispatcher; production Vault/key setup is owner-operated.
**Phase 9 (backups) remains a separate later item.**

---

## The builder prompt (paste into a fresh builder session)

> **Fresh builder session — security & attestation track: test foundation + attestation + Vault (ACTUAL BUILD).**
>
> Resume the Mind Palace build in a fresh session. Re-ground per CLAUDE.md: read
> `docs/PROGRESS.md`, `CLAUDE.md`, `CONSTITUTION.md`, `CONVENTIONS.md`, and the design
> notes now in `docs/design-notes/` — especially `attestation-layer.md`,
> `vault-runtime-auth.md`, `holistic-testing.md`, `test-organization.md` — before
> acting. Current state: Phase 8 complete; vault watcher operationally complete (247
> logic tests passing).
>
> This is a **cross-cutting security & attestation track** (like the hardening pass,
> NOT a numbered phase). **Phase 9 (backups) remains a separate later item — do not
> build it here.** Two subsystems are **pulled forward from their default placement**
> (attestation from Phase 10, Vault primitives from Phase 5); this is sound because
> their building blocks already exist (content digests, Constitution fingerprint,
> `derived_from` edges, the `get_secret()` seam). The universal per-interaction token
> wiring still lands with the Phase-5 dispatcher — this track builds the primitives
> and wires them into the components that already exist.
>
> Work the steps **in order**. **Each numbered step is a checkpoint boundary:** build,
> verify, append a terse PROGRESS.md entry, then either continue (if context is
> healthy) or STOP and hand to a fresh session that resumes from PROGRESS.md. Do not
> force all steps into one session — partial, verified, checkpointed progress is the
> goal.
>
> For every step hold the **build/owner boundary**: you write code, dev-mode/mock
> tests, policy-as-code (HCL), and runbook docs. You do NOT run production Vault
> init/unseal, install daemons, apply the AWS secrets engine, authenticate anything,
> or place production private keys — those are owner-operated and documented in the
> runbook.
>
> **Step 1 — Test reorganization (mechanical, no logic change).** Execute
> `test-organization.md`: flat `tests/` → category subdirs (`unit/ integration/ e2e/
> property/ metamorphic/ adversarial/ integrity/ emergent/ longitudinal/` +
> `fixtures/`), per-dir `conftest.py` applying markers, markers in `pyproject.toml`,
> `longitudinal` excluded from default runs, CI to the staged commands. **Pure
> refactor: report test count + pass/fail before and after — they MUST match.** Move
> firewall/provenance/import-lint tests into `integrity/`; make `integrity/` a
> required, non-skippable CI gate. Seed starter `metamorphic/` (ingest idempotency,
> order independence, topic strengthening, deletion propagation) and `adversarial/`
> (prompt-injection-as-content, derivation-cycle-rejected, PII-scrubber-raises) tests
> against existing code.
>
> **Step 2 — Attestation: records layer (NO signatures yet).** Per
> `attestation-layer.md` §2,§4,§8. New `core/attestation/`: the `Attestation`
> dataclass (id = SHA-256 of all fields except signature; role, action,
> constitution_fingerprint, vault_token_accessor [empty for now], input_hashes,
> output_hashes, derived_from_ids, signature [empty for now]); `AttestationStore`
> (append-only SQLite — **no delete/update methods**, structural). Add an
> `attestation_id` column to `DerivedStore` (migration). Emit **unsigned**
> attestations from the agents that already run: `Dreamer` (dream_pass), `Curator`
> (curate), `VaultSync`/ingest (ingest_note) — each recording the authored input
> digests read, the output record ids written, the live Constitution fingerprint,
> and derived_from_ids. Tests in `integrity/`: every derived record has a complete
> attestation chain to authored leaves; a dreamer attestation never references an
> observed-provenance input; chain links resolve. **Verify chain STRUCTURE before
> adding crypto.**
>
> **Step 3 — Attestation: crypto layer (Ed25519, test keys).** Per
> `attestation-layer.md` §4,§8. Add Ed25519 signing + `scripts/verify_attestation.py`
> (standalone verifier). The signing key is read via
> `get_secret("attestation-signing-key")` (Keychain now, Vault after Step 4); commit
> the **public** key to the repo; use a test keypair fixture in tests. Gate
> attestations (the Phase-3 gate, `ops/`) are signed by the **owner** key via
> `get_secret("owner-signing-key")` — build the code path; production key placement
> (Keychain/Secure-Enclave) is owner-operated (runbook). Tests in `integrity/`:
> signatures verify; tampering any field breaks verification; gate attestations use
> the owner key. **Boundary:** production private-key placement is owner-operated.
>
> **Step 4 — Vault integration (against dev-mode/fake Vault).** Per
> `vault-runtime-auth.md` §2–§5,§7. In `config/`: a `VaultBackend` (`hvac`) and
> extend `get_secret(name, token=None)` — token → Vault path, None → env/Keychain
> fallback (bootstrap/owner-operated). In `ops/`: `mint_token(role, ttl)` via
> AppRole. Commit AppRole **policies as HCL** under `ops/vault/policies/` (the note's
> policy table: dreamer/bridge/airlock/correlator/advisor/supervisor/gate) — NOT
> applied to production (owner-operated). **Two token-acquisition patterns:** (1)
> in-process core agents — the supervisor's `mint_token` injects a scoped token via
> context (build the primitive + scope-enforcement tests; live wiring to a
> secret-reading core agent lands with the Phase-5 dispatcher, since no current core
> agent reads a secret); (2) separate processes — the **bridge** holds its own
> AppRole identity (role_id+secret_id in its own secret store) and authenticates to
> Vault directly. Use pattern (2) for the bridge as the first real consumer (reads
> its AWS creds via Vault — static KV now; the dynamic AWS secrets engine is the
> owner-operated upgrade, code written + documented). **Do NOT pass minted tokens
> across the core↔edge filesystem handoff — the bridge authenticates itself; if this
> conflicts with the Phase-8 bridge design, surface it.** `hvac` is a
> `config/`+`ops/`+`edge/` dependency — `core/` agents must NOT import it; update
> `ops/import_lint.py` and keep it green. Vault on loopback (127.0.0.1:8200) is inside
> the egress guard — no guard change. Tests: a `FakeVault` double for the integration
> logic (mint → allowed read succeeds, out-of-scope read raises PermissionDenied +
> logs a denial) in `adversarial/`+`integrity/`, plus a `@pytest.mark.needs_vault`
> integration test against a real dev-mode Vault when `VAULT_ADDR` is set (skips
> otherwise, like existing live tests). **Boundary:** production Vault
> init/unseal/launchd, applying policies + KV secrets, and the AWS secrets engine
> config are owner-operated (runbook).
>
> **Step 5 — Vault ↔ attestation join.** Populate `attestation.vault_token_accessor`
> from the real minted/authenticated token's accessor. Emit an attestation **denial
> record** whenever a token is denied a secret (the supervisor logs it). Add
> attestation-as-oracle tests (`integrity/`/`e2e/`) asserting on BOTH the attestation
> chain AND the Vault audit log together (`holistic-testing.md` §1e). Leave a TODO
> marker for the Phase-10 alignment hook (Vault denials = alignment signals,
> `alignment-subsystem.md`) — not built now.
>
> **Step 6 — Owner-operated runbook section (docs).** Write the `runbook.md` "Vault &
> attestation — production setup" section the owner executes: Vault binary + launchd +
> KMS auto-unseal (or Keychain unseal), `vault operator init`, applying the AppRole
> policies + KV secrets, the AWS secrets engine config for dynamic bridge/airlock
> creds, placing the supervisor signing key in Vault KV and the owner signing key in
> Keychain/Secure-Enclave. You WRITE it; the owner RUNS it.
>
> **Still registered, NOT built this track:** IoT/correlator (Phase 5+), alignment
> subsystem (Phase 10), curated-graph dreaming R5 (dream R&D, flag OFF), and the
> universal per-interaction token minting wired into the Phase-5 dispatcher (the
> bridge is the only token consumer for now; Phase 5 generalizes it).
>
> **Checkpoint discipline:** after each step, append PROGRESS.md (built / verified
> with test counts / owner-deferred items / next step). Stop and hand off if context
> tightens. Respect every invariant; the import-lint stays green; core reaches no
> network.

---

## Exact PROGRESS.md index lines (append to the design-notes list)

```markdown
- [vault-runtime-auth](design-notes/vault-runtime-auth.md) — Vault as per-interaction runtime authorization layer (AUTHORITATIVE; supersedes secrets-management-evolution): supervisor mints an ephemeral scoped token per agent interaction; the model never holds a real credential. Closes the credential-layer gap in the object-capability model (runtime analog of MirrorView). AWS dynamic creds (TTL=1h) for bridge/airlock. Vault denials = alignment signals. Loopback (127.0.0.1:8200, inside the egress guard). **Security track: primitives pulled forward; full dispatcher wiring at Phase 5.**
- [secrets-management-evolution](design-notes/secrets-management-evolution.md) — SUPERSEDED by vault-runtime-auth; kept for lineage (Vault as multi-machine secrets store; the unseal "bottom turtle").
- [attestation-layer](design-notes/attestation-layer.md) — verifiable chain of custody for every agent action: signed Attestation records (role, action, input/output hashes, Constitution fingerprint, Vault token accessor, derived_from_ids, Ed25519 sig) chaining from authored raw through every derivation. Static proof (lint/types) + runtime proof (attestations). Building blocks already present. Records first → crypto second → owner-key gate attestations last. **Security track: pulled forward from Phase 10.**
- [holistic-testing](design-notes/holistic-testing.md) — testing beyond unit/integration: metamorphic, adversarial, emergent, attestation-as-oracle, longitudinal. Build order: metamorphic+adversarial now; emergent at Phase 7+; attestation-as-oracle with the attestation layer; longitudinal when running continuously.
- [test-organization](design-notes/test-organization.md) — reorganize flat tests/ into category subdirs by execution profile; per-dir conftest markers; longitudinal excluded from default runs; integrity/ is the non-skippable CI gate. Mechanical refactor. **Security track: Step 1.**
- [observed-iot-and-cross-source-synthesis](design-notes/observed-iot-and-cross-source-synthesis.md) — IoT/biometric sources as observed tier; extends dormant Phase-0 sensor_readings schema; correlator (NOT the dreamer) reads interpreted ↔ observed → interpreted correlations; firewall holds. Honor at Phase 5+.
- [alignment-subsystem](design-notes/alignment-subsystem.md) — alignment as a measurable subsystem: fixed seed vs regenerable layer; detection (drift + min-cut-to-authored + community metrics), gated surgery (interpreted-only), reset-from-raw; Phase-10 expansion = modifiable params + alignment-steering self-mod. Honor at Phase 10.
- [dreaming-on-curated-graphs](design-notes/dreaming-on-curated-graphs.md) — dream R&D R5 (flag OFF): interpreter panel on a curated corpus in its OWN graph (never the authored mirror), then cross-graph resonance (interpreted-only). Build after R0/R1.
```

---

## Sequencing
1. **Security track (this handoff):** Steps 1–6, multi-session, checkpointed.
2. **Phase 9 (backups):** separate later build-track item (restic → S3 + SSE-KMS).
3. **Phase 5 / Phase 10 / dream R&D:** IoT/correlator, alignment, R5, and the universal
   per-interaction token wiring — at their phases.
