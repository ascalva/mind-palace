---
type: build-plan
id: bp-120
track: workflow
status: proposed
design_ref:
  - docs/design-notes/dn-autopilot-and-delegated-blessing.md
contract: builder
write_scope:
  - docs/templates/intent-capsule.md
  - scripts/capsule.py
  - tests/unit/test_capsule.py
session_budget: 1
cost:
  estimate:
    model: opus
    tokens: 150k
  actual: null
depends_on: []
parallelizable_with: [bp-121]
created: 2026-07-25
updated: 2026-07-25
links:
  - docs/brainstorms/autopilot-mode.md
  - docs/findings/finding-0207.md
  - docs/templates/capsule.md
  - scripts/exhaust_report.py
re_entry: null
supersedes: null
superseded_by: null
warrant: null
---

# Build Plan — AP1: the intent capsule as a typed artifact with a stable hash

## 0. Mode & provenance

**Graduated from `dn-autopilot-and-delegated-blessing` §2.2** (ratified `b27142d`), the SMART
readback reconciled with the brainstorm's three owner capsules. This is the first of the autopilot
family and deliberately the lowest-blast-radius slice: it creates the *object* the whole design
binds to, and touches no secret, no gate, and no existing behaviour.

Investigation and planning produced this; implementation proceeds item-by-item on owner approval.
The `proposed → ready` blessing is the owner's and is not performed in any session.

⚑ **This plan is deliberately buildable while oq-0036 and oq-0037 are open.** Neither ruling
changes anything here: the capsule is a text with a hash, and both open questions concern who
*verifies* and who *flips*, not what is hashed.

## 1. Objective

An intent capsule is a typed, size-capped artifact whose canonical bytes hash reproducibly, so that
a grant can bind to a text rather than to an occasion.

## 2. Context manifest

Read in this order, whole files before citing:

1. `docs/design-notes/dn-autopilot-and-delegated-blessing.md` — §2.2 (the capsule's fields, the
   loop, the router), §2.9 invariants 2 and 3. The authority for everything below.
2. `docs/templates/capsule.md` — ⚑ the **existing, unrelated** brainstorm session capsule. Read it
   first so the name collision is understood before writing a line (§4).
3. `scripts/exhaust_report.py` — the repo-workflow-tooling precedent this plan follows: stdlib +
   `config` only, no core import, its own unit test.
4. `docs/templates/build-plan.md` — §1 and §9, the two sections the capsule is embedded into.
5. `docs/findings/finding-0207.md` — why nothing in this plan may read a secret.

**DRY audit — does core already have this?** (owner rule: the manifest must ask.) **No.**
`core/attestation/crypto.py:1-9` is **Ed25519 asymmetric signing** for observation attestations —
a different primitive with a different threat model from §2.3's symmetric HMAC, and it lives in the
sealed core. Hashing here is stdlib `hashlib.sha256`. No core code is reused, none is duplicated:
nothing in core hashes a workflow artifact.

## 3. Investigation & grounding

- **Q1 — is there already a `capsule` artifact, and does the name collide?** **Yes, and it
  collides.** `docs/templates/capsule.md:1-7` is the *brainstorm session capsule* — the chat-side
  protocol (§8) block the owner pastes into `/capture`. It has no relationship to §2.2's intent
  capsule beyond the word. A builder told "the capsule template" would reach for the wrong file.
  Resolved by naming (§4).
- **Q2 — must a new script be enrolled anywhere for the gate legs to pass?** **No.**
  `pyproject.toml:128` sets `files = ["core", "agents", "config", "eval", "ops", "scheduler",
  "scripts", "tests"]` — whole directories, so `scripts/capsule.py` and its test are covered on
  creation. This is the registry-enrollment trap the graduate skill names; it does not bite here.
- **Q3 — what may repo-workflow tooling import?** `scripts/exhaust_report.py:16-18` states the
  precedent: *"Repo-workflow tooling (dn-exhaust-lane §2.4, the docket.py precedent): stdlib +
  `config` only"*, with its own unit test. `scripts/check_imports.py:4-5` constrains **`core/`
  only**, so it does not govern this file — the constraint here is the convention, and it is
  tighter than the firewall. This plan follows the convention: **stdlib only**, not even `config`
  (nothing here needs configuration).
- **Q4 — what exactly does §2.2 require be hashed?** The note says `sha256(capsule)` (§2.3) and
  invariant 3 requires the embedded capsule be *"byte-identical to the hashed capsule"*. The note
  **does not define a canonical form**, and the code does not settle it because none exists yet.
  What would settle it: the owner's ruling on delivery (§11 row 1). This plan therefore *defines*
  the canonical form and states it as a decision, not an inference (§6).
- **Q5 — is the ≤40-line / ≈300-word cap checkable mechanically?** Yes, and it is the only
  "quality" property here that is. Word counting needs a pinned definition or two implementations
  will disagree; pinned in §6.

**Additional risks or questions surfaced during reading:**

⚑ **Invariant 2 constrains the delivery format, and the note does not say so.** Invariant 2 —
*"No code verifies against a text the owner did not read: code issuance and capsule render are one
phone-side act"* — is only satisfied if the phone derives the hash from **the text it displayed**.
If the phone is merely *handed* a hash, an agent could render capsule X to the owner while handing
the phone `sha256(Y)`; the owner would approve a text they never read. Since §4/§2.7 deliver the
capsule through the **exhaust lane as HTML**, and HTML rendering is not byte-preserving, the
capsule must also travel as **raw canonical text** the phone can hash directly. Recorded as a
decision with a default (§11 row 1), not silently assumed. This does not block: it constrains the
render plan (AP3) and the parked phone-side generator, both downstream of here.

## 4. Reconciliation

- `docs/templates/capsule.md` — *"Session capsule (chat-side protocol, §8). Every brainstorm
  session in Claude chat ends with one of these in a fenced block."* → **[cross-ref: extension]**.
  The existing file is correct and unchanged. The new artifact is named **`intent-capsule.md`**,
  never `capsule.md`, and gains a header line naming the distinction:

  ```
  <!-- The INTENT capsule (dn-autopilot-and-delegated-blessing §2.2) — the SMART readback a
  grant binds to. NOT docs/templates/capsule.md, which is the brainstorm SESSION capsule
  (chat-side protocol §8). Different artifact, different lifecycle, no shared machinery. -->
  ```

  A one-line pointer is added to the top of `capsule.md`? **No** — `capsule.md` is deliberately
  **out of write_scope**: it is a live template used by an unrelated flow, and editing it to
  disambiguate a file that does not exist yet inverts the dependency. The disambiguation lives in
  the new file only.

- `dn-autopilot-and-delegated-blessing` §2.2/§2.3 — *"`sha256(capsule)`"*, invariant 3
  *"byte-identical to the hashed capsule"* → **[banner: correction]**. The note leaves the hashed
  object undefined; this plan defines it (§6). Because the note is **ratified and agent-immutable
  (A8)**, the definition cannot be written back into it. The plan carries the banner instead, and
  §6 is the authoritative canonical form until a superseding note says otherwise. Any divergence
  between §6 here and a future note is a `spec-defect`, not a silent re-interpretation.

## 5. Write scope

Three files, all **new**:

- `docs/templates/intent-capsule.md` — the template. Named to avoid the `capsule.md` collision
  (§4). Carries the eight §2.2 fields, the size cap, and the canonical-form rule as prose.
- `scripts/capsule.py` — the tool: `hash`, `validate`, `check-embedding`. Stdlib only, dual-mode
  in the repo's standing style, its own unit test.
- `tests/unit/test_capsule.py` — the falsifiers below, executable.

**Deliberately OUT of scope**, and a denial here means file a finding, never widen by hand:

- `docs/templates/capsule.md` — the brainstorm capsule; correct as-is (§4).
- `docs/templates/build-plan.md` — §1/§9 embedding is *checked* by this plan and *changed* by none
  of it. `check-embedding` reads a plan; it never writes one.
- Anything under `.claude/hooks/**`, `config/**`, `core/**` — no gate, no secret, no config is
  touched. The foundation denylist (`CONSTITUTION.md`, `eval/golden/**`, `eval/golden.py`) binds
  regardless.

**Acceptance-reachability check (the finding-0177/0191/0204 recurrence — run before blessing).**
Item 1 → `docs/templates/intent-capsule.md` ✓. Item 2 → `scripts/capsule.py`, `tests/unit/
test_capsule.py` ✓. Item 3 → same two ✓. Item 4 → same two ✓. No criterion requires a protocol
member on an out-of-scope class, no allowlist/registry enrollment (Q2), and no test outside
`tests/unit/test_capsule.py` asks the changed surface a question — the surface is new, so nothing
existing pins it. **Every §7 criterion is buildable from §5.**

## 6. Interfaces pinned inline

**The eight capsule fields** — §2.2's table, copied verbatim so the builder infers nothing:

| capsule field | SMART letter |
|---|---|
| goal, one sentence | Specific |
| definition-of-done, runnable — the exact thing the deskcheck later evaluates | Measurable |
| write-surface summary + §2.4 predicate results + no open decisions | Achievable |
| trace to settled intent | Relevant |
| budget ceiling + base commit + TTL | Time-bound |
| named falsifier — the observation that would prove the run wrong | gap 1 |
| explicit non-goals, inferred ones graded `[INFERENCE]` | gap 2 |
| the readback close — owner recognition | gap 3 |

**Canonical form (DEFINED HERE — the note leaves it open, Q4).** The capsule is a standalone UTF-8
file. `canonical(bytes) ->  bytes` is:

1. decode UTF-8 (strict; invalid input is an error, never a silent replacement character);
2. normalize line endings `\r\n` and `\r` → `\n`;
3. strip trailing horizontal whitespace from every line;
4. strip trailing blank lines, then append exactly one `\n`;
5. re-encode UTF-8.

`capsule_hash = hashlib.sha256(canonical(raw)).hexdigest()` — lowercase hex, 64 chars.

**Why canonicalize at all, stated as the trade it is:** without it, a CRLF introduced by the phone
or a stray trailing space silently voids a valid grant — a usability failure that would train the
owner to distrust the mechanism. With it, the equivalence class is exactly "differs only in
trailing whitespace and line endings", which cannot change meaning. Invariant 3's *"byte-identical"*
is therefore implemented as **canonically identical**, and that weakening is deliberate, bounded,
and recorded here rather than discovered later.

**Word count, pinned** (two implementations must not disagree): a *word* is a maximal run of
non-whitespace characters in the canonical text, counted over the whole file including field
labels. **Line count** is the number of `\n`-separated lines in the canonical text. Caps:
**≤ 40 lines** and **≤ 300 words**, both inclusive, both hard errors.

**CLI surface:**

```
uv run scripts/capsule.py hash <capsule-file>
    -> prints the 64-char hex digest, exit 0
uv run scripts/capsule.py validate <capsule-file>
    -> exit 0 if every required field is present and non-empty AND both caps hold
    -> exit 1 with one diagnostic line per violation, naming the field or the cap
uv run scripts/capsule.py check-embedding <capsule-file> <plan-file>
    -> exit 0 iff the plan's §1 and §9 contain the capsule's goal and non-goals
       verbatim (canonical comparison); exit 1 naming the first divergence
```

## 7. Items

Ordered by blast radius: template (inert text) → pure functions → validation → cross-artifact
check. Nothing in this plan writes outside its own three files, so all four items are
reversible by `git checkout`.

### Item 1 — the `intent-capsule.md` template

- **Objective:** the artifact exists as a fillable template carrying all eight §2.2 fields, the
  caps, and the disambiguation header from §4.
- **Files:** `docs/templates/intent-capsule.md`
- **Acceptance test:** the file exists, parses as Markdown, contains all eight field labels from
  §6, and `uv run scripts/capsule.py validate docs/templates/intent-capsule.md` reports **only**
  empty-field violations — i.e. the empty template is structurally valid and fails only for want
  of content.
- **Falsifier:** the empty template already exceeds a cap. That would mean the caps cannot hold a
  real capsule and §2.2's ≤40-line rule is wrong, not the template.
- **Invariant(s) it must not violate:** it is not `capsule.md` and does not modify it (§4).
- **Touches stored data?** no
- **Parallelizable?** yes  **Depends on:** none

### Item 2 — `canonical()` and `capsule_hash()`

- **Objective:** a capsule hashes reproducibly under the §6 canonical form.
- **Files:** `scripts/capsule.py`, `tests/unit/test_capsule.py`
- **Acceptance test:** `uv run pytest tests/unit/test_capsule.py -q` green, covering: CRLF and LF
  inputs of the same text hash **equal**; trailing-whitespace variants hash **equal**; a
  one-character change in any field hashes **different**; the digest is 64 lowercase hex chars;
  invalid UTF-8 raises rather than substituting.
- **Falsifier:** two capsules whose *meaning* differs hash equal — the canonicalization is
  lossy beyond trailing whitespace and the §6 trade is wrong as specified. (Drill it: mutate a
  non-whitespace character inside a field and assert the hash moves.)
- **Invariant(s) it must not violate:** stdlib only; reads no secret, no environment, no config
  (finding-0207 — nothing in this plan may touch a secret path).
- **Touches stored data?** no
- **Parallelizable?** no  **Depends on:** none

### Item 3 — `validate`: required fields and both caps

- **Objective:** a capsule that is too long, or missing a SMART field, is rejected mechanically
  rather than by reviewer attention.
- **Files:** `scripts/capsule.py`, `tests/unit/test_capsule.py`
- **Acceptance test:** `validate` exits 1 with a naming diagnostic for each of: a missing field, an
  empty field, 41 lines, 301 words; and exits 0 on a well-formed fixture capsule.
- **Falsifier:** a capsule passing `validate` that a human would call unreadable-on-a-phone — the
  cap is measuring the wrong thing and §2.2's "too long to genuinely read" needs a different
  proxy than lines+words.
- **Invariant(s) it must not violate:** the caps are **hard errors**, never warnings — §2.2's cap
  exists to protect the read, and a warning does not protect a read.
- **Touches stored data?** no
- **Parallelizable?** no  **Depends on:** Item 2

### Item 4 — `check-embedding`: the capsule is in the plan verbatim

- **Objective:** invariant 3 becomes checkable — the plan's §1/§9 carry the capsule's goal and
  non-goals unaltered.
- **Files:** `scripts/capsule.py`, `tests/unit/test_capsule.py`
- **Acceptance test:** against fixtures — exits 0 when the plan embeds the capsule verbatim; exits
  1 naming the divergence when a single word of the goal is altered, when a non-goal is dropped,
  and when a non-goal is **added** to the plan that the capsule does not carry (the "plan exceeds
  the capsule" direction, which is the one §2.2 says Gate A audits).
- **Falsifier:** the check passes on a plan that adds a non-goal absent from the capsule. That is
  precisely "the plan exceeds the capsule" and it must fail; if it passes, the check is testing
  containment in the wrong direction and gives false assurance to Gate A.
- **Invariant(s) it must not violate:** read-only with respect to the plan file — this tool never
  edits a plan, and in particular never touches `status:` (gate-guard would deny it, and a tool
  that tries has misunderstood its job).
- **Touches stored data?** no
- **Parallelizable?** no  **Depends on:** Item 2

## 8. Math carried explicitly

- **`capsule_hash` — a binding commitment.** *measures:* the identity of the capsule text, so a
  grant authorizes one text rather than one occasion. *valid when:* `canonical()` is applied
  identically on both sides (verifier and phone), and sha256 remains collision-resistant — the
  security claim needs only second-preimage resistance, since the adversary must produce a
  *different meaningful capsule* with the same digest. *fails its keep if:* two capsules differing
  in any non-whitespace character ever collide under test (Item 2's falsifier), or if the two
  sides disagree on the canonical form in practice — at which point the hash is measuring the
  encoding pipeline rather than the text.

## 9. Non-goals

Explicitly NOT in this plan, so a builder does not helpfully overreach:

1. **No HMAC, no code derivation, no attestation tag** — that is bp-121, and it is the only place
   a secret is reasoned about at all.
2. **No Keychain, no environment read, no secret of any kind** (finding-0207).
3. **No status flip of anything, ever** — no `proposed→ready`, no plan mutation. This plan's tools
   are read-only outside their own files.
4. **No exhaust-lane render** — delivery is AP3's, and it depends on §11 row 1.
5. **No phone-side generator** — parked by the note itself (§4, Parked table).
6. **No hook, no gate, no `.claude/**` change** — the enforcement questions are oq-0036's.
7. **No edit to `docs/templates/capsule.md`** (§4/§5). [INFERENCE — that leaving the *existing*
   template untouched is preferable to cross-linking it; the collision is fully handled from the
   new file's side. If the owner would rather both files point at each other, that is a one-line
   follow-up, not a redesign.]

## 10. Stop-and-raise conditions

STOP and surface rather than proceed if:

- the §6 canonical form turns out not to survive a real phone round-trip (raises the delivery
  question early — that is oq-adjacent and belongs to the owner, park the criterion and continue
  the others);
- any acceptance criterion appears to need a file outside §5 — file a `spec-fidelity` finding and
  park. **Never widen the scope by hand and never route around a `scope-guard` denial**; a second
  denial on the same target means the plan is mis-scoped;
- the caps prove unable to hold a genuine capsule for a real example (Item 1's falsifier) — that
  contradicts the ratified note and is a `spec-defect` against §2.2, routed to the orchestrator,
  not a number to quietly raise;
- a `HOOK-FAILURE` line appears — enforcement did not apply; rerun the named hook standalone,
  reconcile, and say so in the journal before continuing.

## 11. Parked decisions

| Decision | Default recorded | Rejected alternatives (why) | Re-entry condition |
|---|---|---|---|
| How the capsule reaches the phone such that invariant 2 holds (the hash must be derivable from the text the owner *saw*) | The capsule travels as **raw canonical text** alongside any HTML render, so the phone hashes the bytes it displayed | *HTML-only delivery* — rejected: rendering is not byte-preserving, so the phone could only be **handed** a hash, and an agent could then render X while handing `sha256(Y)`; the owner would approve a text he never read, defeating invariant 2 | AP3 (the render plan) is graduated, or the owner rules on the phone-side generator (parked in the note itself) |
| Whether `check-embedding` compares rendered text or raw Markdown | Raw Markdown under §6 canonicalization | *Rendered comparison* — rejected: introduces a Markdown renderer into a stdlib-only tool and makes the check depend on renderer version | A real plan/capsule pair diverges only in formatting and the check is judged too strict |
| Whether the caps are configurable | Hard-coded 40 lines / 300 words per §2.2 | *Config-driven caps* — rejected: a cap the run can raise is not a cap, and §2.6 H4 makes budget non-self-extendable by the same reasoning | The owner tunes the cap at a deskcheck, in which case it changes in the template and this tool together |

## 12. Dependency & ordering summary

**Within the plan:** Item 1 is independent. Items 2 → 3 and 2 → 4 (both need `canonical()`).
Items 3 and 4 are parallel with each other. Blast-radius order is the item order: inert template →
pure function → validator → cross-artifact reader. Nothing is irreversible; every effect is a new
file under `git`.

**Across the family** (`dn-autopilot-and-delegated-blessing`):

- **bp-120 (this plan) — the capsule.** No dependencies. Runs first or concurrently with bp-121.
- **bp-121 — the verifier core** (HMAC derivation, attestation tag, P1–P5 predicates, secret behind
  a provider seam). `parallelizable_with: [bp-120]` — disjoint write_scope; it consumes
  `capsule_hash` only as a hex string, so it does not depend on this plan's code.
- **AP3 — config schema + capsule render to the exhaust lane.** Depends on bp-120 (§11 row 1) and
  on bp-121 for the predicate results the render must show.
- **AP4 — the verifier as an actor: secret source, invocation boundary, flip + grant record.**
  ⚑ **PARKED on oq-0037 / finding-0207** — not minted until the owner rules.
- **AP5 — post-hoc verification of committed flips in `journal-gate`.** ⚑ **PARKED on oq-0036 /
  finding-0206** — not minted until the owner rules.
- **AP6 — the halt list (H1–H8) and run artifacts** (audit records, deskcheck entry, run report).
- **AP7 — audit gates A/B and `board.py` `audit_refs` enforcement for autopilot entries.**
- **AP8 — the constitutional edits.** ⚑ **Ordering constraint the note does not state:** §3(1)
  amends `dn-agent-workflow`, which is **`status: ratified`** (`docs/design-notes/
  agent-workflow.md:4`) and therefore **agent-immutable under A8** — that amendment is the
  **owner's hand**, not a build item. §3(2)'s one-sentence `CLAUDE.md:62` edit *is* agent-buildable
  under an attended plan, but it points at the amendment, so it must not land first.

**Sequencing recommendation:** bp-120 ∥ bp-121 → AP3 → AP6 → AP7, with AP4/AP5 unblocked by their
rulings and AP8 last, after the owner's A10 amendment.
