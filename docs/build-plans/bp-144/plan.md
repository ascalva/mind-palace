---
type: build-plan
id: bp-144
track: workflow
status: proposed
design_ref:
  - docs/design-notes/dn-typed-workflow-registry.md
contract: builder
write_scope:
  - ops/transition_sig.py
  - ops/transition_keys/**
  - scripts/sign_transition.py
  - tests/unit/test_transition_sig.py
  - tests/integration/test_transition_sig_tree.py
session_budget: 1
cost:
  estimate:
    model: opus
    tokens: 300k
  actual: null
depends_on: []
parallelizable_with: [bp-140, bp-141, bp-142, bp-143, bp-146]
created: 2026-07-27
updated: 2026-07-27
links:
  - docs/design-notes/dn-typed-workflow-registry.md
  - docs/brainstorms/blessing-auth-gate.md
  - core/attestation/crypto.py
  - core/verdict/payload.py
re_entry: null
supersedes: null
superseded_by: null
warrant: null
---

# Build Plan — The signed transition: a canonical five-tuple, verified with the existing Ed25519 layer

## 0. Mode & provenance

Investigation and planning produced this plan during `/graduate` of
`dn-typed-workflow-registry` (ratified 2026-07-27); it graduates the first half of the
note's license (iii). Implementation proceeds item-by-item on owner approval; the
`proposed → ready` blessing is the owner's alone.

⚑ **This plan is independent of the registry.** Note §2.5.2, verbatim: "key onboarding does
not block on the registry: the signing primitive works against today's markdown+git world
(the pre-image hash is merely harder to obtain), so onboarding + the primitive can land
first and the registry adopts them." Its `write_scope` is disjoint from every other plan in
the family, so it may run concurrently with bp-140/141/142/143/146. bp-145 is what adopts
it into the registry.

## 1. Objective

Build the signed workflow transition — a canonical five-tuple payload, signed and verified
through the existing `core.attestation.crypto` Ed25519 layer against an enrolled public-key
trust directory — usable today against the markdown+git tree.

## 2. Context manifest

1. `docs/design-notes/dn-typed-workflow-registry.md` §2.4 in full (§2.4.1 the event, §2.4.2
   the YubiKey substrate, §2.4.3 the ⚑⚑ owner ruling on crypto reuse, §2.4.4
   proportionality), §2.5.1 (the gate asymmetry), §2.5.2 (the independence this plan
   depends on), falsifier F5, invariant 9.
2. `core/attestation/crypto.py` — the whole file (84 lines). ⚑ **This is the layer this plan
   imports.** `generate_seed`, `seed_b64`, `public_b64`, `private_from_seed`,
   `public_from_b64`, `sign`, `verify`, `Ed25519Signer`.
3. `core/verdict/payload.py` — the whole file. **The structural precedent, named by the note
   §2.4.3:** canonical serialization of a typed payload, signature over the canonical bytes,
   acceptor holds only the public key, and the recorded judgement (`:20-27`) that it reuses
   the attestation *crypto* verbatim while deliberately minting its own canonical form.
   This plan is the same move, one artifact family over.
4. `scripts/gen_attestation_keys.py` — the owner-operated key-generation idiom and the
   `ops/attestation/<role>.pub` public-key placement convention this plan mirrors.
5. `.claude/hooks/_lib.py:654 _split_front_matter` — the frontmatter/body seam, needed for
   the content hash (§3 Q2).
6. `CONVENTIONS.md` §Secrets and §Trust boundaries — "never commit secrets, never let a
   model read them, never log them"; the `everything → core` arrow.
7. `docs/build-plans/bp-144/journal.md`.

### DRY audit — does `core/` (or the wider tree) already have this?

⚑ **This audit is the plan's central design question, and the owner has already ruled on
it** (note §2.4.3, 2026-07-27): *"import it, the bigger issue is that core doesn't depend on
anything outside the core."* Self-containment is **directional** — `core` must not depend
outward; nothing forbids the inward arrow.

- **Ed25519 sign/verify?** **Yes — `core/attestation/crypto.py`. IMPORT IT DIRECTLY.** No
  sibling module, no parity test, no second implementation. The withdrawn parity-test
  proposal is struck through in the note itself; do not resurrect it, and do not cite
  `scripts/handoff.py:41-43`'s no-core-import stance as a precedent — the note records
  explicitly that it is a *stdlib-purity* choice for a zero-dependency renderer and "does
  not generalize to tooling that needs cryptography."
- **Is `ops/` allowed to import `core`?** Yes, and ten `ops/` modules already do
  (`ops/effect_exec.py`, `ops/ci_witness.py`, `ops/supersede.py`, `ops/self_sensor.py`,
  `ops/code_sensor.py`, `ops/chat_sensor.py`, `ops/staging_sweep.py`, `ops/effects.py`,
  `ops/selfmod_cli.py`, `ops/lifecycle/launcher.py` — verified by grep at graduation).
- **A canonical typed payload + signature dataclass pair?** `core/verdict/payload.py`'s
  `VerdictPayload` / `SignedVerdict`. **Structurally copied, not imported** — and the note
  §2.4.3 gives the reason verbatim: "the transition has fields neither existing payload
  carries." `_canonical(subject_id, verdict, seq, timestamp)` has no room for a five-tuple.
  This is the identical judgement `core/verdict/payload.py:20-27` records about the
  attestation *record*, and it is a reuse decision, not a duplication.
- **A public-key trust store?** `ops/attestation/*.pub` (base64 raw public keys, one file
  per role, written by `scripts/gen_attestation_keys.py`). **Convention reused; a separate
  directory is used** because this is a *different trust root* (owner-held YubiKeys vs the
  supervisor/owner software attestation keys) and conflating two trust roots in one
  directory is how a key gets accepted for the wrong purpose.
- **A content hasher for markdown bodies?** **None exists** — verified. `hashlib` (stdlib)
  plus `_lib.py:654 _split_front_matter` is the whole implementation; do not add a
  dependency.

## 3. Investigation & grounding

- **Q1 — what exactly is signed?** Note §2.4.1, verbatim: "a privileged transition is an
  event whose payload is the five-tuple `(id, from_status, from_content_hash, to_status,
  to_content_hash)` and whose signature is verified before the event is accepted into the
  log." Three defects die: the forged flip (finding-0206), the from-nothing blessing
  (oq-0040), and the missing grant record (oq-0036).
- **Q2 — what is a "content hash"?** ⚑ **The note does not define it, and the code does not
  settle it.** Two readings: the whole file, or the prose body only. The design's own seam
  decides it — §2.3: "the registry owns state … the file owns prose." If the hash covered
  the front matter, then the registry rendering its own authoritative front matter back into
  the file would change the hash of every artifact on every export, and the signature over a
  ratified note would break the moment the export ran. ⇒ **Pinned: the content hash is over
  the prose body only** (`sha256` of the bytes after the closing `---`, LF-normalized),
  computed via `_split_front_matter`. This is a graduation inference from the note's own
  seam; it is recorded as such in §11 and the owner may overrule at the readiness gate.
- **Q3 — can `core/attestation/crypto.py` verify a YubiKey signature?** ⚑ **Unknown, and
  the note says explicitly not to guess.** §2.4.3: "`crypto.py` speaks software Ed25519
  (seed in Keychain); a YubiKey signs *on-token* and its available algorithms depend on
  applet and firmware. If the chosen slot cannot produce Ed25519 signatures, the registry's
  verify path needs an algorithm-parametric extension … verify at the key ceremony, do not
  build from this note's guess. This is falsifier F5." ⇒ **This plan builds and tests the
  Ed25519 path with software keys only**, and structures the verifier so an algorithm is a
  parameter, not a hard-coded call (§6.4). The ceremony is owner-run and out of scope
  (note §1.2 non-goal 1).
- **Q4 — where do enrolled public keys live?** Mirroring `scripts/gen_attestation_keys.py`'s
  convention (`ops/attestation/<role>.pub`, "commit that — it is non-secret"): pinned as
  `ops/transition_keys/<label>.pub`, one base64 raw Ed25519 public key per file, committed.
  At landing the directory contains only a `README.md` describing enrollment — **no key is
  enrolled by this plan**; enrollment is the owner's ceremony.
- **Q5 — does this plan ever touch a private key?** **No.** Invariant 9: "The registry holds
  no secret … public keys and signatures only (NN-10)." NN-3 ("the model advises; code
  acts") and NN-10 ("secrets outside code") both bind. The signer path exists for **tests
  only**, using a generated ephemeral seed; the production signer is the YubiKey and the
  CLI's `sign` subcommand must be able to shell out to an external signer rather than hold a
  seed (§6.5). CONVENTIONS §Secrets: never committed, never read by a model, never logged.
- **Q6 — what is the pre-image in today's markdown world?** Note §2.5.2: "the signing
  primitive works against today's markdown+git world (the pre-image hash is merely harder to
  obtain)". Concretely: `from_content_hash` = the body hash at `HEAD` (via
  `git show HEAD:<path>`), `to_content_hash` = the body hash in the working tree.
  `.claude/hooks/_lib.py:281 git_show_head` already does exactly this fetch and is reusable.
- **Q7 — does anything import `ops/transition_sig.py` today?** No — it is new. Nothing in
  `tests/` asserts a surface this plan moves, so no retrofit pre-widening is needed. Confirm
  with `grep -rn "transition_sig\|sign_transition" . --include=*.py` before starting.
- **Q8 — does `ops/` importing `core` pass the import firewall?** Yes. `scripts/check_imports.py`
  enforces Invariant 2 over `core/` (core must not import a networked zone) and the worker
  boundary; neither scan constrains `ops → core`. `pyproject.toml [tool.mypy].files`
  already includes `ops`, so the new module lands in the Tier-2 checked region with a
  **zero-error** floor.

**Additional risks or questions surfaced during reading:**

- `core.attestation.crypto.verify` returns `False` on **any** failure and never raises
  (`crypto.py:56-63`). That is the right posture for a verifier, but it means a *malformed
  trust file* is indistinguishable from a *bad signature* at the call site. The trust-file
  loader must fail loudly and separately (§6.4) — otherwise an empty `ops/transition_keys/`
  silently rejects every valid signature and looks like an attack.
- A signature is only as good as the label it is attributed to. `SignedTransition.signer`
  must be the trust-file **label**, and verification must confirm the signature validates
  under *that* label's key — not under any enrolled key. Otherwise "who blessed this" is
  unanswerable, which defeats oq-0036.

## 4. Reconciliation

- `core/verdict/payload.py:20-27` — "It **reuses the attestation crypto verbatim and
  deliberately does not reuse the attestation record**, because the record's canonical form
  lacks the verdict's fields" → **cross-ref: extension.** `ops/transition_sig.py`'s module
  docstring states the same relation one level out, naming `core/verdict/payload.py` as the
  precedent it follows, so the tree shows one pattern with three instances rather than three
  ad-hoc choices.
- `scripts/gen_attestation_keys.py:1-14` — the public-key placement convention → **cross-ref:
  extension.** `ops/transition_keys/README.md` names it and explains why a *separate*
  directory is used (a distinct trust root), so a later reader does not consolidate them.
- `docs/design-notes/dn-typed-workflow-registry.md` §4 — "**never** importing `core` unless
  the owner rules otherwise per §2.4.3" → **no action; the owner ruled.** Recorded here so a
  reader of §4 alone does not treat the clause as live. **The note is not edited by this
  plan** (ratified, agent-immutable).
- Nothing is corrected. No banner is owed.

## 5. Write scope

- `ops/transition_sig.py` — the canonical five-tuple, the payload/signed dataclasses, the
  content hasher, the trust-file loader, and `verify`.
- `ops/transition_keys/**` — `README.md` (enrollment instructions) at landing; `*.pub` files
  are added by the **owner's** ceremony, never by this plan.
- `scripts/sign_transition.py` — the thin CLI (`hash`, `prepare`, `sign`, `verify`).
- `tests/unit/test_transition_sig.py` — canonicalization, sign/verify, tamper cases,
  trust-file failure modes.
- `tests/integration/test_transition_sig_tree.py` — the markdown+git pre-image path (§3 Q6).

**Deliberately OUT of scope:** `core/**` (this plan **imports** core, never edits it — an
edit to `core/attestation/crypto.py` would be an outward change to the sacred zone and is a
stop-and-raise); `ops/registry/**` and `scripts/registry.py` (bp-145 adopts this primitive —
keeping the scopes disjoint is what makes this plan parallelizable); `ops/attestation/**`
(the other trust root); every hook and `.claude/settings.json`; `docs/design-notes/**`; the
foundation denylist; Keychain and any secret store.

## 6. Interfaces pinned inline

### 6.1 What is imported from core, verbatim (`core/attestation/crypto.py:44-63`)

```python
def public_from_b64(pub: str) -> Ed25519PublicKey:
    return Ed25519PublicKey.from_public_bytes(base64.b64decode(pub))

def sign(priv: Ed25519PrivateKey, payload: bytes) -> str:
    return base64.b64encode(priv.sign(payload)).decode()

def verify(pub: Ed25519PublicKey, payload: bytes, signature_b64: str) -> bool:
    """True iff `signature_b64` is a valid Ed25519 signature of `payload` under `pub`. Any
    failure mode — bad signature, malformed base64, wrong length — returns False, never raises."""
```

```python
@dataclass(frozen=True)
class Ed25519Signer:
    _private: Ed25519PrivateKey
    name: str
    @classmethod
    def from_seed(cls, seed: str, name: str) -> Ed25519Signer: ...
    def sign(self, payload: bytes) -> str: ...
    def public_b64(self) -> str: ...
```

Import line, exactly:

```python
from core.attestation.crypto import Ed25519Signer, public_from_b64, verify
```

— the same import `core/verdict/payload.py:34` already uses.

### 6.2 The canonical five-tuple

```python
# ops/transition_sig.py
def canonical_transition(entity_id: str, from_status: str | None, from_content_hash: str,
                         to_status: str, to_content_hash: str) -> bytes:
    """The deterministic bytes the signature covers. sort_keys + fixed separators make the
    encoding reproducible across processes and versions — the core/verdict/payload.py:37-42
    discipline, copied. The FIVE-TUPLE is the note's §2.4.1 payload, verbatim."""
    obj = {
        "entity_id": entity_id,
        "from_content_hash": from_content_hash,
        "from_status": from_status,
        "to_content_hash": to_content_hash,
        "to_status": to_status,
    }
    return json.dumps(obj, sort_keys=True, separators=(",", ":")).encode("utf-8")
```

⚑ `from_content_hash` is **never** empty or absent for a privileged transition: "the
from-nothing blessing is unexpressible because there is no event without a pre-image"
(note §2.1). Construction with an empty `from_content_hash` raises `ValueError` — that is
oq-0040 closed at the type level, not by a check.

### 6.3 The payload and its signed form

```python
@dataclass(frozen=True)
class TransitionPayload:
    entity_id: str
    from_status: str | None          # None only for a mint, which is NOT privileged
    from_content_hash: str           # sha256 hex of the PRE-image body; never ""
    to_status: str
    to_content_hash: str             # sha256 hex of the POST-image body

    def __post_init__(self) -> None:
        # Fail closed at the boundary (the VerdictPayload.__post_init__ house style).
        if not self.from_content_hash:
            raise ValueError("from_content_hash is required: a blessing has a pre-image "
                             "(oq-0040; design note §2.1)")
        if self.from_status is not None and self.to_status in PRIVILEGED_TARGETS and \
           self.from_status == self.to_status:
            raise ValueError("a privileged transition must change status")

    def signing_payload(self) -> bytes:
        return canonical_transition(self.entity_id, self.from_status,
                                    self.from_content_hash, self.to_status,
                                    self.to_content_hash)

@dataclass(frozen=True)
class SignedTransition:
    payload: TransitionPayload
    signature: str        # base64 Ed25519 over payload.signing_payload()
    signer: str           # the TRUST-FILE LABEL, e.g. "owner-yubikey-1"
    algorithm: str = "ed25519"

    def verify(self, trust: TrustStore) -> bool:
        """True iff `signature` validates under the key enrolled for THIS `signer` label —
        not under any enrolled key. 'Who blessed this' must be answerable (oq-0036)."""
```

```python
# note §2.5.1: draft->ratified requires a signature and is NEVER automatable;
# proposed->ready has NO signing requirement (it is what autopilot delegates).
PRIVILEGED_TARGETS: frozenset[str] = frozenset({"ratified"})
```

⚑ `PRIVILEGED_TARGETS` here is **only** `{"ratified"}` — narrower than bp-141's degraded-mode
constant, and deliberately so. bp-141's set answers "what must not become *effective*
without admission"; this set answers "what must carry a *signature*". Note §2.5.1 is
explicit that `proposed → ready` carries **no** signing requirement. Do not merge the two
constants; the divergence is the ruling.

### 6.4 The trust store

```python
TRUST_DIR = Path("ops/transition_keys")     # repo-relative; committed; public keys only

@dataclass(frozen=True)
class TrustStore:
    keys: dict[str, str]                    # label -> base64 raw Ed25519 public key

    @classmethod
    def load(cls, directory: Path = TRUST_DIR) -> TrustStore:
        """Every *.pub file in `directory`; the label is the filename stem. RAISES on a
        malformed key file — loudly and distinguishably, because crypto.verify() returns
        False for every failure mode, so a silently-empty or corrupt trust store would be
        indistinguishable from an attack (§3, risks)."""

    def verify(self, signed: SignedTransition) -> bool: ...
```

An **empty** trust store is a valid state (no ceremony yet) and every verification against
it returns `False` with a distinguishable reason string — never a bare `False`.

### 6.5 Content hashing and the markdown pre-image

```python
def body_hash(text: str) -> str:
    """sha256 hex of the PROSE BODY only — the bytes after the closing '---' of the front
    matter, newline-normalized to LF, UTF-8. The registry owns the front matter and rewrites
    it on export (note §2.3), so hashing it would break every signature on the next export.
    Body extraction REUSES .claude/hooks/_lib.py:654 _split_front_matter."""

def head_body_hash(path_rel: str) -> str | None:
    """The pre-image hash from git HEAD. REUSES .claude/hooks/_lib.py:281 git_show_head."""
```

### 6.6 CLI

```
uv run scripts/sign_transition.py hash <path>                       # body hash, working tree
uv run scripts/sign_transition.py prepare <path> --to <status>      # the five-tuple, canonical JSON
uv run scripts/sign_transition.py sign --payload <f> --signer <label> [--seed-env VAR | --external CMD]
uv run scripts/sign_transition.py verify --signed <f>               # exit 0 == valid
```

⚑ `sign` **never** reads a seed from a file, an argument, or the repo. `--seed-env` (tests
and drills only) reads an environment variable; `--external CMD` pipes the canonical bytes to
an external signer's stdin and reads a base64 signature from stdout — **this is the YubiKey
path**, and it is why the CLI must exist before the ceremony does. No secret is ever logged
or printed.

### 6.7 Invariants

9. The registry holds no secret: not the MFA secret (oq-0037, parked), not key material —
   public keys and signatures only (NN-10). *(note §2.9, verbatim)*
3. No unsigned path to `ratified` exists in the schema — not flagged off, absent. *(this
   plan supplies the primitive; bp-145 makes it a schema property)*
- **NN-3:** the model advises; code acts. No model holds raw secrets.

## 7. Items

### Item 20 — the canonical five-tuple

- **Objective:** `canonical_transition` + `TransitionPayload`, with the from-nothing blessing
  unrepresentable.
- **Files:** `ops/transition_sig.py`, `tests/unit/test_transition_sig.py`
- **Acceptance test:** `uv run pytest tests/unit/test_transition_sig.py -q` green: the same
  five-tuple canonicalizes identically across two Python **subprocesses**; constructing a
  payload with `from_content_hash=""` raises `ValueError`; changing any one of the five
  fields changes the bytes.
- **Falsifier:** two payloads that differ only in field *order at construction* produce
  different canonical bytes — the encoding would then be position-dependent and a signature
  could not be re-verified by a different implementation, which is the whole point of a
  canonical form.
- **Invariant(s) it must not violate:** the from-nothing blessing stays unrepresentable
  (oq-0040).
- **Touches stored data?** No.
- **Parallelizable?** No.  **Depends on:** none.

### Item 21 — the body hash and the git pre-image

- **Objective:** `body_hash` / `head_body_hash`, reusing `_split_front_matter` and
  `git_show_head`.
- **Files:** `ops/transition_sig.py`, `tests/integration/test_transition_sig_tree.py`
- **Acceptance test:** `uv run pytest tests/integration/test_transition_sig_tree.py -q`
  green: for a fixture artifact, editing **only** the front matter leaves `body_hash`
  unchanged; editing one body character changes it; `head_body_hash` of an unmodified
  tracked file equals `body_hash` of its working-tree text.
- **Falsifier:** ⚑ the hash changes when only front matter changes. If it does, every
  signature over a ratified note breaks on the next `export --write` (bp-142), and §2.3's
  seam and §2.4's signatures are mutually incompatible — a design-level contradiction to
  raise, not to patch.
- **Invariant(s) it must not violate:** `_split_front_matter` is reused, never re-derived.
- **Touches stored data?** No — reads only; the test writes fixtures under `tmp_path`.
- **Parallelizable?** Yes.  **Depends on:** Item 20.

### Item 22 — sign and verify through the core layer

- **Objective:** `SignedTransition` + `TrustStore`, importing `core.attestation.crypto`.
- **Files:** `ops/transition_sig.py`, `ops/transition_keys/README.md`,
  `tests/unit/test_transition_sig.py`
- **Acceptance test:** with an ephemeral generated seed: sign a payload, enroll the public
  key under a label in a `tmp_path` trust dir, and `verify` returns `True`. Tamper cases all
  return `False`: a flipped `to_status`, a flipped `from_content_hash`, a signature moved to
  a different payload, and a signature attributed to a **different enrolled label**.
- **Falsifier:** ⚑ **verification succeeds under a label whose key did not sign** (i.e. the
  implementation tries every enrolled key). "Who blessed what" is then unanswerable, and
  oq-0036 is not closed — the grant record would name a signer the signature does not
  support.
- **Invariant(s) it must not violate:** invariant 9 — no seed is written to disk, logged, or
  committed; the test's seed is generated in-process and discarded. `core/` is imported,
  never modified.
- **Touches stored data?** No.
- **Parallelizable?** No.  **Depends on:** Item 20.

### Item 23 — the CLI, including the external-signer path

- **Objective:** `scripts/sign_transition.py` with `hash`/`prepare`/`sign`/`verify`, where
  `sign --external` never holds a key.
- **Files:** `scripts/sign_transition.py`, `tests/integration/test_transition_sig_tree.py`
- **Acceptance test:** an end-to-end run against a fixture repo: `prepare` → `sign --external
  <a fake signer script>` → `verify` exits 0. A `grep` of the captured stdout/stderr for the
  seed's first 8 characters finds nothing.
- **Falsifier:** the seed (or any private key material) appears in stdout, stderr, an
  argv-visible argument, or a written file. CONVENTIONS §Secrets and NN-10 are breached, and
  a CLI that leaks a key is worse than no CLI.
- **Invariant(s) it must not violate:** invariant 9; NN-3 (no model holds raw secrets).
- **Touches stored data?** No — reads the tree, writes only to paths the caller names.
- **Parallelizable?** No.  **Depends on:** Items 21, 22.

### Item 24 — the F5 posture: algorithm as a parameter, ceremony deferred

- **Objective:** make the verify path algorithm-parametric so a non-Ed25519 YubiKey slot is a
  configuration problem, not a redesign — and document the enrollment ceremony without
  performing it.
- **Files:** `ops/transition_sig.py`, `ops/transition_keys/README.md`,
  `tests/unit/test_transition_sig.py`
- **Acceptance test:** `SignedTransition.algorithm` round-trips through `to_dict`/`from_dict`;
  a `SignedTransition` carrying an unsupported algorithm verifies to `False` with a
  distinguishable reason naming the algorithm (not a bare `False`); `README.md` states the
  enrollment steps, the "both keys enroll before key #2 leaves" constraint, and that **no key
  is enrolled by this plan**.
- **Falsifier:** ⚑ **F5 (crypto reuse)** — "the enrolled YubiKey configuration cannot produce
  signatures the reused verification layer accepts on shared test vectors." This plan cannot
  *run* F5 (the ceremony is owner-run, note §1.2 non-goal 1) — so its obligation is to make
  F5 **cheap to run later**: ship a `verify` path that accepts an externally-produced
  signature plus a public key and says yes or no, so the owner's first touch-to-sign is the
  test. If the code hard-codes Ed25519 in a way that makes that test impossible, this item
  has failed.
- **Invariant(s) it must not violate:** invariant 9; note §1.2 non-goal 1 — the identity
  foundation is not designed here.
- **Touches stored data?** No. **No key is generated, enrolled, or committed.**
- **Parallelizable?** Yes.  **Depends on:** Item 22.

## 8. Math carried explicitly

- **The signed transition pre-image commitment** (the five-tuple `(id, from_status,
  from_content_hash, to_status, to_content_hash)` under Ed25519) — *measures:* whether a
  specific human, holding a specific enrolled key, authorized **this** state change of
  **this** artifact from **this** exact prior content to **this** exact resulting content.
  *valid when:* the hash is collision-resistant over the hashed region, the hashed region is
  stable under operations the system performs routinely (§6.5: body only, because the front
  matter is rewritten by the export), the private key never leaves the token, and the
  acceptor holds only the public half. *fails its keep if:* a signature verifies for a
  transition whose pre-image was never the artifact's actual prior state (the commitment is
  not binding), or a routine operation invalidates a valid signature (Item 21's falsifier —
  the commitment is not stable), or verification succeeds under a label that did not sign
  (Item 22's falsifier — the commitment is not attributable).
- **Ed25519 itself is NOT implemented here** — it is `cryptography`'s, wrapped by
  `core/attestation/crypto.py`, imported. No field-guide entry is owed for a primitive this
  plan reuses verbatim.

## 9. Non-goals

- ⚑ **No key ceremony.** No key is generated for production, enrolled, or committed. Applet,
  slot, algorithm, and key #2's offsite location are owner ceremony (note §1.2 non-goal 1,
  §Parked). The constraint this plan *records* but does not execute: **both keys enroll
  before key #2 leaves.**
- **No registry integration.** Admission, the schema's no-unsigned-path-to-`ratified`
  property, and the CI re-verification leg are bp-145. Keeping them out is what makes this
  plan parallelizable.
- **No change to `core/`.** Import only.
- **No parity-tested sibling verifier.** Withdrawn by owner ruling; do not resurrect it.
- **No enforcement change.** No hook edited or removed; `.claude/settings.json` untouched.
  `gate-guard` still denies blessings, and it must.
- **No blessing semantics changed.** The HMAC attestation tag, the capsule hash, the halt
  list, P1–P5 remain `dn-autopilot-and-delegated-blessing`'s authority (note §1.2 non-goal 3).
- **No batch signature.** Parked by the note; default "not built until the owner hits the
  friction" (§2.4.4).
- **No new dependency.** `cryptography` is already a runtime dep; `hashlib`/`json` are stdlib.

## 10. Stop-and-raise conditions

- Item 21's falsifier trips (the body hash changes when only front matter changes) — **stop**.
  That is a contradiction between §2.3's seam and §2.4's signatures, an owner-level design
  question, not a build decision.
- A change to `core/attestation/crypto.py` appears necessary — **stop and file a finding**.
  Core is sacred; an edit under a plan whose `write_scope` excludes it is denied pre-hoc, and
  routing around is forbidden.
- The owner overrules the body-only content-hash definition (§3 Q2 / §11) — park the affected
  items with the re-entry condition and continue.
- Any temptation to generate, store, or log a private key — **stop**. NN-10 and CONVENTIONS
  §Secrets are bright lines.
- Any blessing this plan would have to perform — it must not.

## 11. Parked decisions

| Decision | Default recorded | Rejected alternatives (why) | Re-entry condition |
|---|---|---|---|
| What the content hash covers | the **prose body only** (§6.5) | whole-file hash — the export rewrites front matter, so every signature would break on the next export; front-matter-only — signs the part the registry owns anyway and leaves the prose unbound | Owner overrules at the readiness gate; prerequisite: the owner's reading of §2.3's seam against §2.4's signature |
| YubiKey applet/slot + algorithm; key #2's location | none — owner ceremony decides (the note's own parked row) | guessing from firmware documentation — the note forbids it explicitly ("verify at the key ceremony, do not build from this note's guess") | The key-onboarding ceremony (identity-foundation capsule) |
| Trust-directory location | `ops/transition_keys/` (separate from `ops/attestation/`) | one shared directory — conflating two trust roots is how a key gets accepted for the wrong purpose | Owner consolidates the trust roots deliberately |
| `PRIVILEGED_TARGETS` = `{"ratified"}` only | per note §2.5.1: `proposed→ready` carries **no** signing requirement | including `ready` — would contradict the ratified asymmetry and block the autopilot track (bp-138/bp-139) the note declares independent | The owner amends the §2.5.1 asymmetry |
| Deskcheck-verdict signing | unsigned, owner-by-hand as today (the note's own parked row) | signing it — semantically deep but reversible; §2.5.2 classifies it out | Any observed verdict forgery, or an owner ruling |
| Batch signature over a set of transitions | not built | — | Owner hits the per-touch friction on a real batch |

## 12. Dependency & ordering summary

**Within the plan.** Item 20 (pure encoding) → Item 21 (pure hashing, reads the tree) and
Item 22 (pure verification) in parallel → Item 23 (the CLI, the only process-spawning
surface) and Item 24 (posture + docs, parallel with 23). Blast radius is uniformly low: this
plan writes no store, mutates no artifact, and holds no secret. The riskiest surface is Item
23's external-signer plumbing, and its falsifier is a leak check.

**Across plans.** `depends_on: []` — ⚑ **independent of the registry by design**, per note
§2.5.2 and §3(4)'s sequencing rule ("key onboarding proceeds now against the markdown world;
the registry adopts the primitive when stage (iii) lands"). `parallelizable_with:
[bp-140, bp-141, bp-142, bp-143, bp-146]` — all five have `write_scope`s disjoint from this
plan's (`ops/transition_sig.py`, `ops/transition_keys/**`, `scripts/sign_transition.py`, two
test files). **bp-145 depends on this plan** and on bp-140. `bp-138`/`bp-139` (autopilot
AP5/AP6) are independent of this whole family and are specifically **unaffected** by the
signing track: note §2.5.2, "the hardware key serves the gate autopilot will **never**
touch."
