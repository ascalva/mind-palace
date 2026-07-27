---
type: build-plan
id: bp-138
track: workflow
status: proposed
design_ref:
  - docs/design-notes/dn-autopilot-and-delegated-blessing.md
contract: builder
write_scope:
  - scripts/grant_core.py
  - tests/unit/test_grant_core.py
session_budget: 1
cost:
  estimate:
    model: opus
    tokens: 250k
  actual: null
depends_on: [bp-135, bp-136, bp-137]
parallelizable_with: []
created: 2026-07-27
updated: 2026-07-27
links:
  - docs/findings/finding-0207.md
  - docs/findings/finding-0262.md
  - docs/inbox/owner-questions.md
  - docs/build-plans/bp-120/plan.md
re_entry: null
supersedes: null
superseded_by: null
warrant: null
---

# Build Plan — AP5: the grant's pure core — code derivation, the domain-separated attestation tag, and expiry, with the secret behind an injection-only seam

## 0. Mode & provenance

**Graduated from `dn-autopilot-and-delegated-blessing` §2.3 (the grant's cryptographic properties)
and §2.9 invariants 1, 3 and 9** (`status: ratified`). Investigation and planning produced this;
implementation proceeds item-by-item on owner approval. The `proposed → ready` blessing is the
owner's and is not performed in any session.

⚑ **Bootstrap wrinkle, stated once more because this is the plan that would most tempt a reader to
suspect a shortcut:** this plan builds the cryptography of *delegated* blessing and is itself
blessed **by the owner's hand, at the keyboard**, because the mechanism that would issue a grant
does not exist until after it. There is no grant, no capsule and no code for this plan. That is the
only possible order, and it is not a circumvention.

## ⚑ 0.1 What this plan is NOT, and why the wave is ordered this way

This is the plan the wave's ordering constraint exists for, so it is stated before anything else.

**§2.3's grant removes the owner from the reviewer's seat.** §2.5's audit pair, §2.6's halt list
and §2.7's trail are what occupy that seat in his place. A wave that delivered grant machinery
before the machinery that stands where the owner stood would delegate blessing **with nothing in
the seat**. Hence `depends_on: [bp-135, bp-136, bp-137]`.

⚑ **That dependency is not technical.** Nothing in this file imports anything from those three
plans; this is pure, stdlib-only cryptography that would compile on an empty tree. The edge exists
**so the wave cannot be built in the wrong order by scheduling accident**. A builder who notices
the dependency is satisfiable on paper and starts anyway has removed the only thing holding the
order — file a finding instead.

**And this plan builds no actor.** It builds *functions*. Specifically it does **not** build:

- any reader of a real secret — no Keychain, no environment, no file. The `SecretProvider` seam has
  exactly one in-repo implementation and it takes the bytes from its caller (Item 18);
- any `proposed → ready` flip, or any writer of any status anywhere;
- any **verification oracle** — no daemon, no service, no long-lived process, and no CLI
  subcommand that accepts a candidate code. ⚑ This is `finding-0262`: a 6–8 digit code with no
  bound on verification attempts is a 10^6–10^8 search against a local oracle, well inside the
  72-hour TTL. Building the oracle is the **parked** AP-actor plan's problem, and it must solve
  attempt-bounding before it exists. This plan deliberately ships no surface that could be one
  (§6, §9, §10).

The actor that holds a real secret and performs the flip is **parked on `oq-0037`** (whose ruling
is *"deferred to a Fable design pass"*), on `oq-0036`, and now additionally on `finding-0262`.
This plan is exactly the half `oq-0037` says is buildable today: *"The verifier's **pure core**
(HMAC derivation, the domain-separated attestation tag, capsule hashing, P1–P5 predicates) is
testable with an injected secret and needs no ruling; it is planned now behind a provider seam — the
same shape bp-115 used for the inference client, so your decision later is a config flip, not a
rewrite"* (`docs/inbox/owner-questions.md:1236-1242`).

## 1. Objective

The grant's cryptography exists as pure, injected-secret functions that flip nothing, read no
secret, answer no verification query, and whose attestation tag is re-verifiable offline and
provably independent of the code.

## 2. Context manifest

Read in this order, whole files before citing:

1. `docs/design-notes/dn-autopilot-and-delegated-blessing.md` — **§2.3 whole** (every bullet is a
   property this plan implements or explicitly defers), **§2.9 invariants 1, 3 and 9**, **§2.7(1)**
   (what the grant record carries and what it must never carry), and **§1.2** whole. The authority
   for everything below.
2. `docs/findings/finding-0207.md` — `route: orchestrator`, **open**. Why nothing here may read a
   secret, and why the `scripts/capsule.py` import discipline is a *structural* answer rather than
   a convention. `:98-99` and `:104-105` license exactly this plan.
3. `docs/findings/finding-0262.md` — **open**, filed at this graduation. Why this plan ships no
   verification oracle, and what the parked actor plan must solve before it does.
4. `docs/inbox/owner-questions.md:1190-1268` — `oq-0037` whole, including the answer (*"deferred to
   a Fable design pass"*) and the externally-verified primitives that must not be re-derived.
5. `docs/inbox/owner-questions.md:1120-1188` — `oq-0036` whole. Why no post-hoc check is built here.
6. `scripts/capsule.py` — whole. `capsule_hash` (`:111-114`) is this plan's input; the AST-enforced
   secret-freedom at `:45-50` is the discipline this plan inherits and tightens.
7. `tests/unit/test_capsule.py:414-431` — the AST invariant test to copy and tighten (§3 Q4).
8. `core/attestation/crypto.py` — whole, **for the DRY audit** and to confirm it is the wrong
   primitive (§2 DRY audit, §3 Q1).
9. `docs/brainstorms/the-false-success-rule.md:17-31`, `:52-65` — the degenerate-input obligation
   and the mutation companion. Items 18–21 each deliver a gate or a check.
10. `CONVENTIONS.md:38-39` (`## Secrets`) and `:45-50` (`## Trust boundaries in code`) — the two
    sections that bind. ⚑ There is **no** `§Security` heading in `CONVENTIONS.md`; these are it.

**DRY audit — does `core/` already have this?** (owner rule.) **No — and the near-miss is the
important part.** `core/attestation/crypto.py` is **Ed25519 asymmetric signing** (`:1`,
*"Ed25519 signing primitives for attestations"*), public API `sign`/`verify`/`Ed25519Signer`
(`:52`, `:56`, `:67`). It is a **public-key signature scheme, not a keyed MAC** — different
primitive, different threat model, no shared secret — and it lives in the sealed core, which
repo-workflow tooling never imports (`scripts/board.py:17`, `scripts/capsule.py:45-50`).
`bp-120/plan.md:102` already recorded the same conclusion. Measured repo-wide: **no file anywhere
imports `hmac`, and `compare_digest` appears nowhere in the tree.** So this plan writes the
repository's first keyed MAC, from stdlib `hmac`, and duplicates nothing. Hashing reuses
`hashlib.sha256`; the capsule's canonical form is **not** re-derived — `capsule_hash` arrives as a
64-char hex string and this plan never canonicalizes anything (§6).

## 3. Investigation & grounding

- **Q1 — is there an existing keyed MAC or HMAC to reuse?** **No.** Repo-wide grep for
  `hmac|HMAC|compare_digest`: every hit is prose in design notes, plans, findings and one
  *negative* assertion — `tests/unit/test_capsule.py:430` lists `hmac` among the imports
  `scripts/capsule.py` must **never** have. No file imports `hmac`; `compare_digest` appears
  nowhere. ⚑ Consequence: **this must be a new module, not an extension of `scripts/capsule.py`** —
  that tool's own AST test forbids it the `hmac` import, and relaxing that test to accommodate this
  work would delete a structural guarantee `finding-0207` bought.
- **Q2 — what does the repo's `get_secret` do, and why can this plan not use it?** Two
  implementations, deliberately split: `core/kernel/config/loader.py:710-725` is env-only
  (`return os.environ.get(name)`), and `config/loader.py:55-68` is token-capable and may reach
  network Vault. **Neither is usable here**, for the reason `finding-0207` names: *"the verifier
  reads the secret at invocation, and the agent is the invoker"*. Importing either would put a
  secret in the invoker's environment, i.e. in the model's reach. This plan imports **neither**,
  and its AST test forbids `os`, `subprocess`, `config` and `core` outright so the route does not
  exist to be taken.
- **Q3 — is there a provider-seam precedent to follow?** Yes — `oq-0037`'s answer names it:
  *"the bp-115 shape"*, the inference client behind a seam so the later decision is a config flip
  rather than a rewrite. This plan follows it with the seam narrowed to a `Protocol` and exactly
  one in-repo implementation that **takes bytes from its caller** (§6).
- **Q4 — is the existing AST import test strong enough to copy verbatim?** **Almost.**
  `tests/unit/test_capsule.py:419-427` walks with `ast.walk`, so it **does** catch an
  `import os` nested inside a function body — the obvious evasion. ⚑ It does **not** catch a
  *dynamic* import: `__import__("os")`, `importlib.import_module("os")`, or an attribute walk
  through `sys.modules`. For a tool that computes MAC values from a secret, that gap matters more
  than it does for `capsule.py`. Item 18 tightens the test to also reject `__import__`/`importlib`
  call nodes and any `sys.modules` subscript, and asserts the tightening reddens on a fixture that
  uses them (§7).
- **Q5 — what exactly is hashed, and does this plan re-derive it?** **No.** `bp-120` defined the
  canonical form and shipped it: `canonical_text` (`scripts/capsule.py:94-104`), `capsule_hash`
  (`:111-114`, `hashlib.sha256(canonical(raw)).hexdigest()`, lowercase, 64 chars). This plan's
  inputs are **already-computed hex digests**. It validates their shape (64 lowercase hex) and
  refuses anything else; it never opens a capsule file. That keeps invariant 3 a property of one
  implementation rather than two.
- **Q6 — does the note fix the code's digit count?** Only as a range: *"truncated to 6–8 digits"*
  (`:247-248`). The code does not settle it further. §6 pins **8** and §11 records the choice with
  its rationale and re-entry, because the number is a security parameter and a builder must not
  pick one by feel.
- **Q7 — enrollment, imports, lint?** As `bp-136`/`bp-137`: `pyproject.toml:128` enrolls `scripts/`
  by directory at a **Tier-2 0-error hard floor** (`.github/workflows/ci.yml:71`);
  `scripts/check_imports.py:2-11` constrains `core/` and the worker boundary only, so the
  stdlib-only discipline exists **only** because Item 18 writes its AST test; ruff
  `line-length = 100`, no per-file ignore for `scripts/` (`pyproject.toml:104-112`).

**Additional risks or questions surfaced during reading:**

⚑ **`finding-0262` — the note's threat model has no bound on verification attempts.** §2.3 defends
the code's transmissibility with hash-binding, single-use and TTL. All three are orthogonal to
guessing: hash-binding fixes *which* code is right, single-use retires it *after* acceptance, and
the TTL is the *window* guessing is allowed in. Single-use as worded (*"records each **consumed**
capsule-hash"*) burns on success; the note never says a failure burns anything. **This plan's
response is structural: it ships no verification oracle at all** (§0.1, §6, §9). A pure function
that a caller must already hold a candidate code and a secret to invoke is not an oracle; a process
that answers `verify(hash, code)` on request is. The parked AP-actor plan must solve attempt
bounding before it becomes the second thing.

⚑ **The attestation tag proves the verifier ran, not that the owner read.** §2.3's tag is minted on
successful code verification, so it inherits whatever the code's strength is. This is worth stating
in the module docstring, because invariant 9 (*"A grant record without a re-verifiable attestation
tag is not a grant record"*) is easy to over-read as "a tag proves the owner approved". It proves
**binding**, not comprehension; comprehension is invariant 2's job, and invariant 2 is discharged
by `bp-139`'s render, not by any cryptography here.

## 4. Reconciliation

- `dn-autopilot-and-delegated-blessing.md:247-248` — *"truncated to 6–8 digits"* →
  **[banner: correction]**, narrowing. The range is not implementable; §6 pins **8** and the module
  docstring announces the narrowing as a decision with its rationale, not as a reading of the note.
  Any future note that fixes a different number supersedes §6, and a divergence is a `spec-defect`
  rather than a silent re-interpretation. Because the note is ratified and agent-immutable (A8),
  the pin cannot be written back into it.
- `dn-autopilot-and-delegated-blessing.md:267-269` — *"Single-use is verifier-enforced: the verifier
  records each consumed capsule-hash on its own side"* → **[cross-ref: extension]**, carried by
  `finding-0262`. This plan implements the **shape** of single-use as a pure predicate over a
  supplied consumed-set (Item 21) and states plainly in the docstring that the **ledger itself, and
  the counting of failures, belong to the parked actor** and are not built here. The extension is
  announced; nothing is quietly assumed.
- `tests/unit/test_capsule.py:414-431` — the AST allowlist precedent → **[cross-ref: extension]**.
  This plan's AST test is the same idea **tightened** (dynamic imports, §3 Q4). `test_capsule.py`
  is **not edited** — it is out of `write_scope` and its own guarantee is unchanged; the new,
  stricter test lives in this plan's test file and names the precedent it extends.

## 5. Write scope

Two paths, both **new**:

- `scripts/grant_core.py` — the pure core. stdlib only: `hmac`, `hashlib`, `dataclasses`,
  `datetime`, `argparse`, `sys`, `re`, `typing`. **No `os`. No `subprocess`. No `pathlib`. No
  `core`. No `config`. No `keyring`. No network module of any kind.**
- `tests/unit/test_grant_core.py` — the falsifiers, the degenerate inputs, the mutation campaign
  and the tightened AST invariant.

**Deliberately OUT of scope** — a denial means file a finding, never widen by hand:

- ⚑ **`scripts/capsule.py` and `tests/unit/test_capsule.py`.** `test_capsule.py:430` forbids
  `capsule.py` the `hmac` import. That test is a structural guarantee bought by `finding-0207` and
  **must not be relaxed to make room for this work**. If an item appears to need it, the item is
  wrong: this is a new module, by design (§3 Q1).
- **`config/**`, `core/**`** — no config schema, no loader change. `bp-139` owns `[autopilot]`.
- **`.claude/hooks/**`** — no gate, no Stop-gate change. That is `oq-0036`'s, parked.
- **`docs/templates/grant-record.md`** — the record *template* is `bp-139`'s; this plan computes
  the tag that would go in it and writes no record.
- **Anything that could hold or reach a secret**: no `.env`, no Keychain script, no launchd plist,
  no service definition. The actor is parked.
- `docs/design-notes/**` (A8, agent-immutable) and the foundation denylist (`CONSTITUTION.md`,
  `eval/golden/**`, `eval/golden.py`), which binds regardless.

**Acceptance-reachability check** (findings 0177/0191/0204):

| item | files its acceptance must modify | all in §5? |
|---|---|---|
| 18 | `scripts/grant_core.py`; `tests/unit/test_grant_core.py` | ✓ |
| 19 | same two | ✓ |
| 20 | same two | ✓ |
| 21 | same two | ✓ |

Non-obvious targets checked: **no protocol member** is added to any out-of-scope class — the
`SecretProvider` Protocol and its one implementation both live in `scripts/grant_core.py`; **no
allowlist/registry enrollment** — `pyproject.toml:128` covers `scripts/` by directory, and unlike
`ops/import_lint.py`'s `NETWORK_ALLOWLIST` there is no allowlist governing `scripts/` at all
(§3 Q7); **no test outside this plan's own file** asks the changed surface a question, because
every surface is new. ⚑ Item 18's AST test **reads** `scripts/grant_core.py`; reading is not
writing.

## 6. Interfaces pinned inline

**§2.3's properties, verbatim** (`dn-autopilot-and-delegated-blessing.md:245-275`) — the builder
implements these and not paraphrases:

> - The code is `f(secret, artifact-hash)` — HMAC-style over the capsule hash, truncated to
>   6–8 digits — never `f(secret, time)`. It authorizes **a text**, not an occasion. Any edit to
>   the capsule invalidates it. Single-use.
> - The shared secret lives in Keychain (NN-10); **the model never sees it.** A small verifier
>   script recomputes and compares.
> - **The grant record carries an attestation no model can mint.** On successful code
>   verification, the verifier writes into the grant record a full-width
>   `HMAC(secret, "record" ‖ capsule-hash ‖ issued-at)` — domain-separated from the code's own
>   derivation, so the stored tag reveals nothing about any code, past or future.
> - **Expiry:** the grant is void at the earliest of: a TTL (default 72 h, parked for owner
>   tuning), or **base drift** — any file in the plan's context manifest or write_scope changed on
>   main since the capsule's base commit (mechanical: `git diff --name-only base..HEAD` intersected
>   with those sets).

**Invariant 1, verbatim** (`:462`): *"The model never sees the MFA secret; the model never performs
a blessing flip (NN-3)."*
**Invariant 9, verbatim** (`:474-475`): *"A grant record without a re-verifiable attestation tag is
not a grant record — the flip it accompanies reads as unauthorized. Narrative alone never proves a
grant."*

**The binding constitutional text** (`CONSTITUTION.md` §II, and `CLAUDE.md`'s digest):
NN-3 *the model advises; code acts — no agent seeks or accepts a shell, raw credentials, or the
power to change infrastructure directly*; NN-10 *secrets are never read by a model, never logged,
never embedded*; and `CONVENTIONS.md:39`: *"macOS Keychain … or environment variables. Never commit
secrets, never let a model read them, never log them."*

**The secret seam — DEFINED HERE (the `oq-0037` "bp-115 shape"):**

```python
class SecretProvider(Protocol):
    def secret(self) -> bytes: ...

@dataclass(frozen=True)
class InjectedSecret:
    """The ONLY in-repo implementation. It holds bytes its caller already has.
    It reads no environment, no file, no Keychain — there is no code here that could.
    A provider that fetches a real secret is the PARKED actor plan's (oq-0037), and it
    lives outside this module."""
    value: bytes
    def secret(self) -> bytes: return self.value
```

**Domain separation — DEFINED HERE**, pinned so two implementations cannot disagree. Both derive
from HMAC-SHA256 over the injected secret, with disjoint, length-unambiguous message prefixes:

```
code_msg(capsule_hash)              = b"mind-palace/grant/code/v1\x00"   + capsule_hash_bytes
record_msg(capsule_hash, issued_at) = b"mind-palace/grant/record/v1\x00" + capsule_hash_bytes
                                       + b"\x00" + issued_at_bytes
```

where `capsule_hash_bytes` is the **64 ASCII hex characters**, and `issued_at_bytes` is an RFC-3339
UTC timestamp, second precision, `Z`-suffixed. The `\x00` separators make the concatenation
unambiguous; the version tag makes a future change a new domain rather than a silent break.

```python
def derive_code(provider: SecretProvider, capsule_hash: str) -> str
    # HMAC-SHA256(secret, code_msg(capsule_hash)); take the first 4 bytes big-endian,
    # mod 10**8, zero-padded to exactly 8 digits.  Returns an 8-character string.

def code_matches(provider: SecretProvider, capsule_hash: str, candidate: str) -> bool
    # hmac.compare_digest(derive_code(...), candidate). MUST use compare_digest, never `==`.

def attestation_tag(provider: SecretProvider, capsule_hash: str, issued_at: str) -> str
    # HMAC-SHA256(secret, record_msg(...)).hexdigest() — FULL width, 64 hex chars, never truncated.

def tag_matches(provider: SecretProvider, capsule_hash: str, issued_at: str, tag: str) -> bool
    # hmac.compare_digest over the hex strings.
```

**Digit count: 8, pinned** (§4, §11 row 1). The note allows 6–8; 8 is the widest it permits and
costs nothing.

**Expiry — DEFINED HERE as a pure function that takes git's answer as data:**

```python
@dataclass(frozen=True)
class DriftInput:
    drift_checked: bool          # did the caller actually run the diff?
    changed_paths: tuple[str, ...]

def grant_void_reason(
    *, capsule_hash: str, plan_capsule_hash: str,
    issued_at: str, now: str, ttl_hours: int,
    manifest_paths: tuple[str, ...], scope_globs: tuple[str, ...],
    drift: DriftInput,
) -> str | None
    # None iff the grant is live. Otherwise a one-line reason.
```

⚑ **`drift.drift_checked` is the point of the type.** `changed_paths=()` is ambiguous between "the
diff ran and found nothing" and "nobody ran the diff"; the boolean disambiguates, and
`drift_checked=False` **always** returns a void reason (invariant 7). Running `git` is the
**caller's** job — this module imports no `subprocess` and cannot shell out, which is exactly why
it also cannot reach the `security` CLI.

**CLI surface — DEFINED HERE, and deliberately impoverished:**

```
uv run scripts/grant_core.py selftest
    -> runs the module's own known-answer vectors against a FIXED TEST SECRET
       compiled into the test file, prints PASS/FAIL, exit 0/1
uv run scripts/grant_core.py explain
    -> prints the domain-separation strings and the digit count; takes no secret,
       computes nothing
```

⚑ **There is no `verify` subcommand, no `derive` subcommand, and no way to pass a secret on the
command line.** This is the `finding-0262` response made structural: a CLI that accepts
`--secret` and `--code` **is** the brute-force oracle, and it would additionally put a secret on a
process command line, where it is visible to any process listing — a direct NN-10 violation. The
functions are importable by a future actor that runs in its own trust boundary; they are not
callable by a shell. A test asserts the argparse surface contains exactly `selftest` and `explain`.

**The no-logging rule, pinned:** no function in this module ever `print`s, logs, or embeds in an
exception message: a secret, a derived code, or any candidate code. Diagnostics say *"code did not
match"*, never *"expected 41938271, got 41938272"*. A test asserts every raised message and every
stdout byte, over a fixture run, is free of the fixture secret and the derived code.

## 7. Items

Ordered by blast radius: the structural cage first (so nothing built afterwards can escape it) →
the code → the tag → expiry. All pure functions; nothing writes outside this plan's two files. Item
numbering continues the family (`bp-120` 1–4, `bp-135` 5–8, `bp-136` 9–13, `bp-137` 14–17).

### Item 18 — the cage: the seam, and an AST invariant that catches dynamic imports

- **Objective:** the module is structurally incapable of reaching a secret, and the check that says
  so cannot be evaded by a dynamic import.
- **Files:** `scripts/grant_core.py`, `tests/unit/test_grant_core.py`
- **Acceptance test:** `uv run pytest tests/unit/test_grant_core.py -q` green on: the module's
  imports are a subset of `{__future__, hmac, hashlib, argparse, sys, re, dataclasses, datetime,
  typing, enum}`; **none** of `os`, `subprocess`, `pathlib`, `socket`, `urllib`, `http`, `keyring`,
  `core`, `config` is imported at **any** depth (`ast.walk`); **no** `__import__(...)` call, **no**
  `importlib` reference, and **no** `sys.modules[...]` subscript appears anywhere; `InjectedSecret`
  is the only class implementing `SecretProvider` in the module; and the argparse surface is
  exactly `{selftest, explain}`.
- **Falsifier:** the seam turns out to be unusable by the eventual actor — it needs a provider that
  can fetch, and the Protocol's shape forces a rewrite rather than a config flip. That would mean
  `oq-0037`'s *"the bp-115 shape … a config flip, not a rewrite"* does not hold here. ⚑ Drill it:
  the builder writes (in the **test file**, never in the module) a five-line fake fetching provider
  and shows the four public functions accept it unchanged.
- **⚑ Degenerate input (false-success rule):** **a module that reaches `os` via
  `__import__("os")`.** The precedent test at `tests/unit/test_capsule.py:419-427` walks
  `Import`/`ImportFrom` nodes only, so it passes on this — the check greening without testing its
  claim, on exactly the evasion a security-relevant module invites. Assert the tightened scan
  **reddens** on a fixture source containing `__import__("os")`, one containing
  `importlib.import_module("os")`, and one containing `sys.modules["os"]`. Second degenerate: an
  empty source file — a scan phrased as "no forbidden import found" passes on a file with no code;
  assert the check requires the module's four public functions to be present.
- **⚑ Mutation obligation** (`the-false-success-rule.md:52-65`, `finding-0249` — both surviving
  mutants that wave were found by mutating and running, neither by reading): this is the load-bearing
  gate of the whole plan. Mutate (m1) the scan back to `Import`/`ImportFrom` only — must be caught by
  the `__import__` fixture; (m2) drop `pathlib` from the forbidden set; (m3) drop the argparse-surface
  assertion. Each caught by a named test; campaign recorded in the journal.
- **Invariant(s) it must not violate:** invariant 1 and NN-3/NN-10. ⚑ **This item must not weaken
  `tests/unit/test_capsule.py`** — that file is out of `write_scope` and its `hmac` prohibition
  stands (§5).
- **Touches stored data?** No.
- **Parallelizable?** no  **Depends on:** none

### Item 19 — `derive_code` / `code_matches`: the code binds a text, in constant time, and is never printed

- **Objective:** the grant code is a deterministic function of (secret, capsule hash) alone,
  compared without a timing side channel, and never emitted.
- **Files:** `scripts/grant_core.py`, `tests/unit/test_grant_core.py`
- **Acceptance test:** green on known-answer vectors computed from a fixed test secret: the code is
  exactly 8 decimal digits including leading zeros; the same (secret, hash) yields the same code
  across runs and processes; a **one-character** change anywhere in the capsule hash moves the code;
  a different secret moves the code; the code depends on **no** clock — `derive_code` called twice
  a simulated week apart is identical (asserting §2.3's *"never `f(secret, time)`"*);
  `code_matches` returns `False` for a candidate of the wrong length, for a non-digit candidate and
  for an off-by-one code; an AST assertion that `hmac.compare_digest` is used and the literal `==`
  never compares a code; and the no-logging test — over a full fixture run, neither the secret bytes
  nor the derived code appears in stdout, stderr or any raised message.
- **Falsifier:** two capsules with **different** hashes produce the same code with non-negligible
  frequency — the truncation is collapsing the space in a way 10^8 does not predict, and the
  binding is weaker than the note claims. ⚑ Drill it: derive codes for 100,000 distinct random
  hashes under one secret and assert the collision count is within a factor of three of the birthday
  expectation for 10^8; a gross excess is the falsifier firing.
- **⚑ Degenerate input (false-success rule):** **a `code_matches` implemented with `==`.** It passes
  every functional test above — same inputs match, different inputs do not — while losing the
  constant-time property, which is the entire reason `compare_digest` exists. The functional tests
  cannot tell; the AST assertion is what tells. Assert the AST check reddens on a fixture using
  `==`. Second degenerate: **`derive_code` that ignores the secret entirely** (e.g. truncating the
  capsule hash itself) — deterministic, 8 digits, hash-bound, and it passes every test except one.
  Assert a test compares codes under two different secrets and requires them to differ.
- **⚑ Mutation obligation:** mutate (m1) `compare_digest` → `==`; (m2) the secret out of the HMAC
  input; (m3) the zero-padding, so a code with a leading zero is 7 characters. All three caught by
  named tests.
- **Invariant(s) it must not violate:** NN-10 — never logged, never embedded, never on a command
  line (§6: there is no CLI path that takes one). §2.3 — `f(secret, artifact-hash)`, never
  `f(secret, time)`. ⚑ **No verification oracle** (`finding-0262`): `code_matches` is an importable
  function, and this plan ships no process, service or subcommand that calls it on request.
- **Touches stored data?** No.
- **Parallelizable?** no  **Depends on:** Item 18

### Item 20 — `attestation_tag` / `tag_matches`: full width, domain-separated, and provably not the code

- **Objective:** the grant record's tag is unforgeable without the secret and reveals nothing about
  any code — the property invariant 9 rests on, made testable.
- **Files:** `scripts/grant_core.py`, `tests/unit/test_grant_core.py`
- **Acceptance test:** green on: the tag is 64 lowercase hex characters, **never truncated**; it
  changes when the capsule hash changes, when `issued_at` changes, and when the secret changes;
  `tag_matches` uses `compare_digest` (AST-asserted) and rejects a one-character edit; the tag is
  recomputable from (secret, hash, issued_at) alone — an offline re-verification test recomputes it
  in a second process; and the **domain-separation** assertions: for the same secret and hash,
  `attestation_tag` and the pre-truncation `derive_code` digest are different, **and no 8-digit
  window of the tag, and no arithmetic reduction of any 4-byte prefix of the tag, equals the code**.
- **Falsifier:** a tag from which the code is recoverable — that is the note's own claim
  (*"the stored tag reveals nothing about any code, past or future"*) failing, and it would mean the
  grant record leaks the credential it exists to attest. ⚑ Drill it: the builder implements a
  deliberately **wrong** variant that derives both from the same message without domain separation
  and shows the recovery working, then shows the correct variant defeating it. That is the
  falsifier-demo discipline, and it has **no live side effects** — pure functions over a fixed test
  secret, nothing to mock (build-plan skill's side-effect audit: nil, and stated).
- **⚑ Degenerate input (false-success rule):** **a domain-separation test that only checks
  `tag != code`.** It passes trivially — the tag is 64 characters and the code is 8, so they can
  never be equal as strings, and the check greens without testing the claim at all. The real claim
  is *non-recoverability*, so the assertions above must operate on **windows and reductions of the
  tag**, not on string equality. Assert the test reddens against the no-domain-separation variant.
  Second degenerate: `issued_at` accepted in any format — two callers using `2026-07-27T10:00:00Z`
  and `2026-07-27 10:00:00+00:00` produce different tags for the same moment, so the record fails
  re-verification for a formatting reason. Assert `attestation_tag` **rejects** any `issued_at` not
  matching the pinned RFC-3339 UTC second-precision form.
- **Invariant(s) it must not violate:** invariant 9. ⚑ And the honesty clause from §3: the module
  docstring must state that the tag proves **binding**, not comprehension — invariant 2's read is
  discharged by `bp-139`'s render, not by any cryptography here.
- **Touches stored data?** No.
- **Parallelizable?** no  **Depends on:** Item 18

### Item 21 — `grant_void_reason`: expiry, base drift, hash mismatch, and the un-run check

- **Objective:** a grant's liveness is a pure decision in which "nobody looked" is void, not live.
- **Files:** `scripts/grant_core.py`, `tests/unit/test_grant_core.py`
- **Acceptance test:** green on: a void reason naming **TTL** when `now - issued_at > ttl_hours`
  (default 72, per §2.3), and `None` when inside it; a reason naming **hash mismatch** when
  `capsule_hash != plan_capsule_hash` (invariant 3 checked at every checkpoint, per H7); a reason
  naming **base drift** when any `changed_paths` entry is in `manifest_paths` or matches any
  `scope_globs` entry; a reason naming **drift not checked** whenever `drift.drift_checked` is
  `False`, *regardless of every other input*; a reason naming **single-use** when the capsule hash
  is in a supplied consumed-set; and a malformed `issued_at`, `now` or hash yielding a void reason
  rather than an exception.
- **Falsifier:** base drift fires on essentially every real grant, because `main` moves constantly
  and a plan's context manifest names files that change — making the 72-hour TTL irrelevant and the
  mechanism unusable in practice. ⚑ Drill it: over the last 30 days of this repository's history,
  compute for five representative completed plans how long their manifest+scope sets stayed
  unchanged. If the median is hours rather than days, base drift as specified is too tight and that
  is a `spec-defect` against §2.3 — filed, not tuned.
- **⚑ Degenerate input (false-success rule):** **`changed_paths=()` with `drift_checked=False`.**
  "No changed path intersects the scope" is **vacuously true** over the empty tuple, so a naive
  implementation returns `None` — *the grant is live* — precisely when the caller never ran
  `git diff`. That is the check passing without testing its claim, in the direction that authorizes
  a stale grant. Assert `drift_checked=False` **always** yields a void reason, and assert a named
  test would redden if `DriftInput` collapsed to a bare tuple. Second degenerate: an **empty**
  `manifest_paths` and `scope_globs` — the intersection is empty for any diff, so drift can never
  fire; assert both-empty yields a void reason (a plan with no manifest and no scope is not one a
  grant can be live against).
- **⚑ Mutation obligation:** mutate (m1) `drift_checked` out of the decision; (m2) the TTL
  comparison to `>=` vs `>` at the boundary; (m3) the hash comparison to a prefix match. All caught
  by named tests.
- **Invariant(s) it must not violate:** invariant 7 (ambiguity resolves toward halting — here,
  toward *void*). ⚑ It imports no `subprocess` and runs no `git`: the diff is the caller's, passed
  as data. That is what keeps the module unable to shell out at all.
- **Touches stored data?** No.
- **Parallelizable?** no  **Depends on:** Item 18

## 8. Math carried explicitly

- **`derive_code` — a truncated keyed PRF over a commitment.** *measures:* the holder's possession
  of the shared secret, bound to one specific capsule text via its sha256 commitment; it measures
  authority over a text, never over an occasion. *valid when:* HMAC-SHA256 behaves as a PRF (so the
  8-digit truncation is uniform over 10^8 and reveals nothing about the key), the capsule hash is
  second-preimage resistant (the adversary must produce a *different meaningful capsule* with the
  same digest — `bp-120` §8's identical assumption), the two sides canonicalize identically
  (`bp-120` §6, not re-derived here), **and the number of verification attempts is bounded** —
  ⚑ the last is *not* established by this plan and is `finding-0262`; a 10^8 space is strong only
  against a bounded guesser. *fails its keep if:* codes collide far above the birthday expectation
  for 10^8 (Item 19's falsifier), or if any code proves derivable from a published attestation tag
  (Item 20's falsifier) — at which point the truncation is leaking key material rather than
  committing to a text.
- **`attestation_tag` — a full-width keyed MAC under a disjoint domain.** *measures:* that a party
  holding the Keychain secret verified this capsule hash at this instant; it is offline-recomputable
  by that party and unforgeable by anything else, which is what makes a grant record evidence rather
  than prose (invariant 9). *valid when:* the two message spaces are provably disjoint (the
  length-unambiguous version-tagged prefixes of §6) and the tag is never truncated. *fails its keep
  if:* a tag is ever produced whose windows or reductions yield the corresponding code (domain
  separation has failed), or if a record's tag re-verifies under a secret the owner did not enroll —
  at which point the tag is attesting to the verifier's existence rather than to the owner's act.

## 9. Non-goals

Explicitly NOT in this plan, so a builder does not helpfully overreach:

1. **⚑ No verification oracle.** No daemon, no service, no long-lived process, no CLI subcommand
   accepting a candidate code, no `--secret` flag. `finding-0262`, and §6's impoverished CLI is the
   enforcement.
2. **⚑ No real secret source.** No Keychain, no environment, no file, no `get_secret` import. The
   only provider takes bytes from its caller. `oq-0037` is parked and this plan does not pre-empt it.
3. **No status flip of anything, ever.** No `proposed→ready`, no plan mutation, no writer of any
   kind. `gate-guard` would deny it and a tool that tried has misunderstood its job.
4. **No grant record is written.** The template is `bp-139`'s; the writer is the parked actor's.
5. **No post-hoc Stop-gate check.** `oq-0036`, parked. Nothing in `.claude/hooks/**` is touched.
6. **No capsule parsing, hashing or canonicalization** — `bp-120` owns it; inputs arrive as hex
   digests (§3 Q5).
7. **No `git` invocation.** The diff is passed as data (Item 21).
8. **No relaxation of `tests/unit/test_capsule.py`'s `hmac` prohibition** (§5). [INFERENCE — that a
   separate module is strictly better than widening a proven structural guarantee. If the owner
   would rather one tool held both, that is a design act with a security consequence and belongs in
   a note, not in a builder's judgement.]

## 10. Stop-and-raise conditions

STOP and surface rather than proceed if:

- ⚑ **any criterion would put a secret, a derived code, or a candidate code within reach of a
  model** — on a command line, in an environment variable, in a log line, in an exception message,
  in a test fixture committed as anything other than an obviously-fake constant, or behind a
  callable oracle. **This is not a design choice to make.** Stop, file a finding, and raise it. It
  is the one condition in this plan that outranks finishing the work.
- base drift proves to fire on essentially every real grant (Item 21's falsifier) — file a
  `spec-defect` against §2.3, park the criterion, continue the rest.
- the seam proves unusable by a fetching provider (Item 18's falsifier) — that contradicts
  `oq-0037`'s "config flip, not a rewrite"; file a finding and park rather than widening the module.
- an item appears to need `scripts/capsule.py`, `tests/unit/test_capsule.py`, `.claude/hooks/**`,
  `config/**` or `core/**` — file a `spec-fidelity` finding and stop. **Never widen the scope by
  hand and never route around a `scope-guard` denial**; a second denial on the same target means
  the plan is mis-scoped.
- `depends_on` is unsatisfied — `bp-135`, `bp-136` and `bp-137` are not all `complete`. ⚑ The
  dependency is the wave's ordering constraint, not a technical one (§0.1); it is satisfiable on
  paper at any time, and starting anyway removes the only thing holding the order. File a finding.
- a `HOOK-FAILURE` line appears — rerun the named hook standalone, reconcile, and say so in the
  journal before continuing.

## 11. Parked decisions

| Decision | Default recorded | Rejected alternatives (why) | Re-entry condition |
|---|---|---|---|
| Code length within §2.3's 6–8 digit range | **8**, zero-padded (§6) | *6 digits* — rejected: the note permits 8, and 8 costs the owner two keystrokes while multiplying an unbounded guesser's work by 100. *A longer non-numeric code* — rejected: the note pins digits, and the parked phone generator (iOS Shortcut) is specified around them | The owner tunes it, or `finding-0262`'s attempt-bounding ruling makes the length moot |
| The TTL default | **72 h**, per §2.3, and parked there too | *A shorter default* — rejected: the note records 72 h explicitly as parked for owner tuning, and pre-empting it here would decide by build what the note reserved for the owner | The owner tunes the TTL (the note's own parked row) |
| Where the single-use ledger lives | **Nowhere here.** `grant_void_reason` takes a consumed-set as data; the ledger is the parked actor's | *A file-backed ledger in this module* — rejected: it would need `pathlib`/`os` and would put state (and therefore a write) inside the pure core, breaking the cage Item 18 builds | `oq-0037`'s Fable pass rules on what actor holds verifier-side state |
| Whether a **failed** verification consumes the capsule hash | **Undecided here, deliberately** — this module never verifies on request, so it has no failures to count | *Decide it now* — rejected: it is a property of the oracle, and the oracle is parked; deciding it in a module that has no oracle would be a decision with no enforcement | `finding-0262` is ruled in the `oq-0036`/`oq-0037` Fable pass |
| `issued_at` format | RFC-3339 UTC, second precision, `Z`-suffixed, **rejected if it does not match** | *Accept any parseable timestamp* — rejected: the tag is a function of the exact bytes, so two spellings of one moment give two tags and a record fails re-verification for a formatting reason (Item 20's second degenerate input) | A phone-side generator cannot produce this form; then the format changes in the module and the generator spec together |

## 12. Dependency & ordering summary

**Within the plan:** Item 18 is first and gates everything — the cage must exist before anything
that computes with a secret is written inside it. Items 19, 20 and 21 each depend on Item 18 and
are mutually independent. Blast-radius order is the item order: structural invariant → the code
(the thing that must never leak) → the tag (which must not leak the code) → expiry (pure arithmetic
over supplied data). Nothing is irreversible; every effect is a new file under `git`.

**Across the wave:** see `bp-135` §12 for the full map. This plan's `depends_on: [bp-135, bp-136,
bp-137]` is **the ordering constraint made structural** and is explained at §0.1: the grant vacates
the reviewer's seat, and the three plans that fill it must land first. `parallelizable_with: []` —
it shares no file with anything, but it is deliberately not offered as parallel work.

**Downstream:** `bp-139` (the ON switch) `depends_on: [bp-138]`.

**Un-minted and why:** **AP-actor** — the verifier as an actor (secret source, invocation boundary,
the flip, writing the grant record, and the attempt bound `finding-0262` demands) — **PARKED** on
`oq-0037`, `oq-0036` and `finding-0262`. **AP-posthoc** — the Stop-gate/journal-gate grant-record
rule — **PARKED** on `oq-0036`. **AP-const** — the one-sentence `CLAUDE.md:62` edit — **PARKED** on
the owner's A10 amendment to `dn-agent-workflow`, which is agent-immutable under A8 and therefore
his hand, not a build item. None is minted; all three are enumerated here so no future reader has
to reconstruct what was left, which is the failure this note's own history demonstrates.

**Blessing-round recommendation:** bless `bp-135`/`bp-136`/`bp-137` as one round; bless this plan
and `bp-139` only once the first three are `complete`. `depends_on` enforces the build order;
staging the blessing means the reviewer's seat is demonstrably occupied before the grant's
cryptography is authorized to exist at all.
