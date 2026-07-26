# Journal — bp-120 (AP1: the intent capsule)

## Graduation — 2026-07-25, session-51 (orchestrator)

Minted `proposed` by `/graduate dn-autopilot-and-delegated-blessing` (note ratified `b27142d`
earlier the same session). No implementation was performed; graduation plans and grounds only.

**Grounded, with citations, before the plan was written** (all in §3):

- `docs/templates/capsule.md:1-7` — a **name collision**: the existing `capsule.md` is the
  brainstorm *session* capsule (chat-side protocol §8), unrelated to §2.2's *intent* capsule. The
  new template is therefore `intent-capsule.md` and carries a disambiguating header. The existing
  file is deliberately left untouched (§4, §9 non-goal 7).
- `pyproject.toml:128` — `files = [… "scripts", "tests"]` covers whole directories, so new files
  need **no registry enrollment** for the mypy leg. This is the trap the graduate skill names; it
  does not bite here, and that is recorded rather than assumed.
- `scripts/exhaust_report.py:16-18` — the repo-workflow-tooling precedent (stdlib + `config` only,
  own unit test). This plan is tighter still: **stdlib only**.
- `core/attestation/crypto.py:1-9` — the DRY audit the owner rule requires. Core has **Ed25519
  asymmetric** signing for observation attestations; §2.3 needs **symmetric HMAC**. Different
  primitive, different threat model, and it lives in the sealed core. Nothing is reused and
  nothing is duplicated.

**Open questions the note did not settle, resolved here as decisions rather than inferences:**

- The note never defines the **canonical form** of the hashed capsule (§2.3 says `sha256(capsule)`,
  invariant 3 says "byte-identical"). §6 defines it, and states plainly that "byte-identical" is
  implemented as **canonically identical** — a deliberate, bounded weakening so a stray CRLF from
  the phone cannot silently void a valid grant. Carried as a **banner-on-correction** (§4) because
  the note is ratified and agent-immutable (A8), so the definition cannot be written back into it.
- ⚑ **Invariant 2 constrains delivery, and the note does not say so.** The phone must derive the
  hash from *the text it displayed*; if it is merely handed a hash, an agent could render capsule X
  while handing `sha256(Y)` and the owner would approve a text he never read. Since delivery is via
  the exhaust lane as HTML — not byte-preserving — the capsule must also travel as raw canonical
  text. Parked with a default (§11 row 1), blocking nothing in this plan.

**Two findings were filed against the ratified note during this same pass**, both batched for the
owner (`ba5ff17`): **finding-0206 / oq-0036** (the post-hoc grant check has no existing rule to be
an exception to, and cannot distinguish the owner's committed hand-flip from a forged one) and
**finding-0207 / oq-0037** (invariant 1's "the model never sees the secret" is asserted, not
mechanised; ACL pinning cannot work while the verifier is a script). **Neither blocks this plan** —
both concern who verifies and who flips, not what is hashed. Each parks exactly one downstream
plan (AP4, AP5); the rest of the family proceeds.

**Acceptance-reachability check: run, and it passes.** All four §7 criteria are buildable from the
three files in §5 — no protocol member on an out-of-scope class, no allowlist enrollment (Q2), no
existing test pinning the new surface (it is new).

**Status:** `proposed`. The `proposed → ready` blessing is the owner's, by hand. Nothing further is
owed by this plan until then.
