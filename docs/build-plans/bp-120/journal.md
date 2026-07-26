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

---

## Build session — 2026-07-26, delegated builder (worktree)

Worktree `worktree-agent-a53618cd6e026bf1f`, branched from `origin/main` @ **`7941da1`**
("merge(bp-123 Items 1+3): the overlay is `config/ouroboros.toml`, and cannot be silently lost")
— verified before starting; the base matches the orchestrator's stated expectation (`7941da1` or
later). Contract: `builder`. Plan flipped `ready → in-progress` (a non-blessing transition).

**Committed on the branch, NOT pushed. Plan left at `status: in-progress`** — flipping to
`complete` is the orchestrator's single-writer duty.

All four items are **done**, all gate legs green. One finding filed: **finding-0219**, Item 3's
named falsifier, which **fired**. Nothing is parked; the finding is design-level and routes to the
orchestrator without holding any criterion open.

Config note (the orchestrator's warning): this worktree has neither `config/local.toml` nor
`config/ouroboros.toml`, so committed defaults loaded cleanly. **No `ConfigMigrationError` was
seen at any point.** (This plan's tool imports no `config` at all, but the suite does.)

---

## Checkpoint 1 — §2 manifest read; the name collision confirmed; Item 1 built

`uv sync --frozen --extra dev` first, per the orchestrator's environment note — the fresh
worktree `.venv` indeed lacked dev extras.

**Manifest read in order**, whole files: the ratified note (§2.2 fields / loop / router, §2.3
grant, §2.9 invariants 2 and 3), `docs/templates/capsule.md`, `scripts/exhaust_report.py`,
`docs/templates/build-plan.md` (§1 and §9 — the two sections the capsule embeds into), and
`docs/findings/finding-0207.md`.

**§3 Q1 re-confirmed independently, and it matters:** `docs/templates/capsule.md` is the
*brainstorm SESSION capsule* — a fenced ```` ```capsule ```` block with `topic` / `decisions` /
`parked` / `open_questions` / `next_steps` / `references`, pasted into `/capture`. Zero overlap
with §2.2's intent capsule beyond the word. It was **not touched** (out of write_scope by §4/§5);
the whole disambiguation lives in the new file, exactly as §4 directs.

**§3 Q2 re-confirmed:** `pyproject.toml` `[tool.mypy] files = [… "scripts", "tests"]` — whole
directories, so both new Python files are covered on creation with no enrollment. The
registry-enrollment trap does not bite.

### Item 1 — `docs/templates/intent-capsule.md` — DONE

Eighteen lines: the §4 disambiguation header (verbatim in substance, extended with the caps and
the canonical-form rule per §5), then the eight fields, `non-goals` as a bullet list.

**Two decisions I had to make, because §6 pins the field set and the counting rules but not a
serialization.** Both are recorded in the tool's docstrings, not only here:

1. **Format**: `name:` at column 0, rest-of-line is the scalar value, bullets are list items,
   HTML comments ignored by the parser (but counted by the caps and covered by the hash — §6 says
   "the whole file"). The eight field *keys* are the machine contract: `goal` ·
   `definition-of-done` · `achievable` · `relevant` · `time-bound` · `falsifier` · `non-goals` ·
   `readback`, in SMART order followed by the three fields SMART lacks; each carries §6's
   descriptive wording as its placeholder text, so the note's own vocabulary travels with the
   artifact.
2. **A bare `<placeholder>` counts as EMPTY.** This is what makes Item 1's acceptance
   ("structurally valid, fails only for want of content") reachable at all — and it is a safety
   win on its own: a capsule with a forgotten field can never reach a grant.

**Acceptance — met.** All eight fields parse; `validate` emits **exactly eight diagnostics, all of
them empty-field** ones and nothing else (`field: \`goal\` is empty (line 9)` …
`field: \`readback\` is empty (line 18)`), exit 1.

**Item 1's falsifier — did NOT fire.** The empty template is **18 / 40 lines** and
**168 / 300 words**, leaving 22 lines and 132 words of headroom. The caps comfortably hold a real
capsule, so §2.2's ≤ 40-line rule stands. Cross-checked with a *genuine* capsule for the owner's
own named ask (markdown spell-check, note §1.1): **17 lines / 159 words**, validates clean. That
fixture is now `GOOD` in the test file.

---

## Checkpoint 2 — Items 2, 3, 4 built; all four falsifiers drilled; finding-0219 filed

### Item 2 — `canonical()` / `capsule_hash()` — DONE

§6 implemented literally, all five steps, in `canonical_text()`. Three things worth carrying:

- **Strict UTF-8**, by writing no `errors=` argument at all — a decode substitution would change
  the text the owner read into a text that hashes.
- **Degenerate case, documented rather than discovered later:** §6 step 4 read literally means an
  all-blank file canonicalizes to a lone `"\n"`, so it hashes equal to the empty file. Harmless —
  `validate` rejects it for want of all eight fields — but it is now in the docstring.
- **Idempotence** is tested (`canonical(canonical(x)) == canonical(x)`): the phone and the
  verifier cannot disagree by applying the canonical form a different number of times.

**Acceptance — met.** CRLF / CR / LF variants of one text hash equal; trailing spaces, trailing
tabs, extra trailing blank lines, and a missing final newline all hash equal; the digest is 64
lowercase hex; invalid UTF-8 raises `UnicodeDecodeError`.

**Item 2's falsifier — did NOT fire.** Drilled as the plan directs, and drilled **per field**
rather than once: eight parametrized mutations, one non-whitespace change inside each of the eight
fields, each asserted to move the digest. No collision. The equivalence class is exactly "differs
only in trailing whitespace and line endings", so §6's trade holds as specified and invariant 3's
"byte-identical" is honestly implementable as "canonically identical".

### Item 3 — `validate` — DONE

Caps first, then the eight required fields in order; one diagnostic line per violation, each
prefixed `cap:` or `field:` so it names the thing it is about. Caps are **hard errors**: an
over-cap capsule with all eight fields filled is still rejected (there is a test for exactly that,
because a warning does not protect a read).

**Acceptance — met.** Parametrized over all eight fields for *missing* and for *empty* (the empty
case uses a bare `<placeholder>`, which is the realistic failure). Both caps are pinned at their
boundary from **both sides** — 40 lines passes / 41 fails, 300 words passes / 301 fails — so §6's
inclusivity is proved, not assumed. The word-cap fixture pads on **one line** so the line cap
cannot be what fires; each cap is proved independently.

### ⚑ Item 3's falsifier — **FIRED**. finding-0219 filed

The falsifier: *"a capsule passing `validate` that a human would call unreadable-on-a-phone."*
Measured, both passing with zero diagnostics:

| capsule | lines | words | characters | `validate` |
|---|---|---|---|---|
| eight fields filled + one unbroken 8,000-char token | 18 / 40 | 161 / 300 | 9,177 | passes |
| eight fields filled + 30 lines of seven 180-char tokens | 39 / 40 | 227 / 300 | **38,122** | passes |

Neither count is wrong — both are exactly what §6 pins. **lines × words does not bound the size of
the text**, because a "word" has no maximum length. Since the capsule is *agent-authored* (§2.2:
the agent restates, the owner verifies), the thing the cap must bound is the length of a text an
agent produces and the owner is asked to read, and a proxy admitting 38 KB does not bound it.

**Not fixed here, and that is the discipline rather than laziness.** §6 pins the two counts exactly
and §11 row 3 pins them as non-configurable ("a cap the run can raise is not a cap"); adding a
third cap changes a pinned interface, which is a design act. So: **`docs/findings/finding-0219.md`**,
`ftype: spec-defect`, `route: orchestrator`, with three candidate resolutions (character cap /
max token length / amend §2.2 to say the cap bounds shape and not bytes) and the ruling left to
the owner — naturally at this plan's deskcheck, which §11 row 3 already names as the re-entry.

The boundary is also **encoded as a passing test**,
`test_item3_falsifier_the_caps_do_not_bound_characters_finding_0219`, which asserts the current
behaviour and says in its docstring that a future cap flips it to failing. That is deliberate: the
defect cannot hide, and the fix cannot land without someone reading the finding.

Note the *opposite* defect — the one §10 named as a stop condition, "the caps prove unable to hold
a genuine capsule for a real example" — did **not** occur (17–18 lines / 159–168 words). So §10 was
not triggered and the session correctly continued.

### Item 4 — `check-embedding` — DONE

Reads the plan's `## 1.` and `## 9.` sections (comments blanked, so the build-plan *template*'s
comment-only §9 cannot read as a non-goal). Goal: normalized containment in §1. Non-goals: **set
equality**, deliberately symmetric.

**Acceptance — met**, drilled against fixtures in all four directions:

| case | result |
|---|---|
| plan carries the capsule verbatim (second non-goal **wrapped** across two lines) | exit 0 |
| one word of the goal altered (`on by default` → `on by request`) | exit 1, `goal:` line first |
| a non-goal dropped | exit 1, `non-goal: missing from plan §9: …` |
| a non-goal **added** to the plan | exit 1, `non-goal: plan §9 exceeds the capsule …` |

**Item 4's falsifier — did NOT fire.** The "plan exceeds the capsule" direction — the one §2.2 says
Gate A audits — fails as it must. Containment is checked *both* ways; a one-directional check would
have handed Gate A false assurance on exactly the property it exists to test.

Two comparison decisions, both recorded in the code:

- **`_norm` collapses whitespace runs only** — no case folding, no punctuation stripping. So a plan
  may **re-wrap** a non-goal but not **re-word** it. This is §11 row 2's default (raw Markdown
  under §6 canonicalization) implemented as strictly as recorded; a Markdown renderer would make
  the check depend on renderer version.
- **Parser asymmetry, intentional:** on the capsule side any wrapped line continues the current
  field (never silently drop content from the hashed authority); on the plan side a continuation
  must be *indented* (a plan section legitimately ends in a column-0 closing paragraph, and folding
  that in would manufacture a divergence).

### Invariants held

- **Stdlib only** — `argparse`, `hashlib`, `re`, `sys`, `dataclasses`, `pathlib`. Not even
  `config` (nothing here needs configuration), tighter than the `exhaust_report.py` precedent.
- **finding-0207 satisfied structurally, not asserted:** the tool imports **no `os` and no
  `subprocess`**, so there is no route to an environment variable, the `security` CLI, or any other
  secret path. An AST test pins the whole import set and names the forbidden modules.
- **Never writes.** A source scan asserts no `write_text` / `write_bytes` / `open(` / `unlink` /
  `rename` / `mkdir` anywhere in the tool, plus a byte-for-byte before/after check on a plan file
  after `check-embedding` runs. In particular it never touches a plan's `status:`.
- **§9 non-goals 1–6 all held** — no HMAC, no secret, no gate, no hook, no `.claude/**`, no config
  schema, no status flip of anything but this plan's own `ready → in-progress`.
  `docs/templates/capsule.md` untouched (non-goal 7).
- No `HOOK-FAILURE` line appeared at any point.

---

## Checkpoint 3 — SEAL: gates green, committed on the branch

### Gate results — every leg, exact numbers

| leg | result |
|---|---|
| `uv run ruff check .` | **All checks passed!** |
| `uv run python scripts/check_imports.py` | **OK** — core imports no zone or networking module |
| `uv run mypy core agents eval ops scheduler scripts` | **0 errors**, 259 source files |
| `uv run mypy` (pinned tests baseline) | **exactly 69** errors in 20 files, 552 files — unmoved |
| `uv run python -m ops.type_gate` | **OK** — Tier-2 membership OK, bare-ignore scan OK |
| `uv run pytest -q …` (green-gate marks + the one deselect) | **2152 passed, 11 skipped, 21 deselected, 0 failed** |

The pre-edit baseline was measured for comparison: ruff clean, code mypy 0, tests mypy **69**. The
69 did **not** move — the new test file adds zero mypy errors.

`tests/unit/test_capsule.py`: **51 tests**, all passing. Of those, 3 are the named falsifier drills
that did not fire (Items 1, 2, 4), 1 records the falsifier that did (Item 3 / finding-0219), and 2
are the tooling invariants (stdlib-only + never-writes); the rest is mechanical coverage — counted,
not listed.

### Read map

```read-map
docs/findings/finding-0219.md:56: WHY the cap gap matters — the owner's read is the only detector for the finding-0150 class; read before the deskcheck
docs/findings/finding-0219.md:78: the three candidate resolutions; the ruling belongs here, not in code
scripts/capsule.py:19: the canonical form DEFINED — bp-120 §6 is authoritative because the ratified note leaves it open
docs/templates/intent-capsule.md:4: the template header carries the caps + canonical rule; a bare placeholder counts as EMPTY
scripts/capsule.py:94: canonical_text — §6's five steps, strict UTF-8, and the all-blank degenerate case
scripts/capsule.py:146: is_empty — an unreplaced placeholder is want of content, so a forgotten field cannot reach a grant
scripts/capsule.py:179: the parser asymmetry: never silently drop a wrapped line from the HASHED authority
scripts/capsule.py:250: _norm — a plan may re-wrap a non-goal but not re-word it (§11 row 2, as strict as recorded)
scripts/capsule.py:295: check_embedding — set equality BOTH ways, because the plan may not exceed the capsule
tests/unit/test_capsule.py:312: Item 3's falsifier, FIRED and recorded as a passing test a future cap will flip
tests/unit/test_capsule.py:207: Item 2's falsifier drilled per field — eight mutations, none collide
tests/unit/test_capsule.py:372: Item 4's falsifier — a plan that ADDS a non-goal must fail
tests/unit/test_capsule.py:414: finding-0207 held structurally: no os, no subprocess, so no route to a secret
tests/unit/test_capsule.py:133: Item 1's falsifier — the empty template's HEADROOM inside both caps
```

### What /triage owes

- Flip **bp-120 → `complete`** and seal with `cost.actual` (single-writer duty; not done here).
- Route **finding-0219** — `spec-defect` → orchestrator → `docs/inbox/owner-questions.md`. The ask
  is self-contained in the finding: *does the capsule cap gain a character/token bound, or does
  §2.2 get amended to say it bounds shape and not bytes?* §11 row 3's re-entry ("the owner tunes
  the cap at a deskcheck") is the natural place, and the caps then change in `scripts/capsule.py`
  and `docs/templates/intent-capsule.md` **together**.
- **AP3 (the capsule render) must not assume a byte bound** until finding-0219 rules.
- **Deskcheck**: file into `docs/DESKCHECK-QUEUE.md`. The natural deskcheck is to fill the template
  for a real QoL ask, run `hash` / `validate` / `check-embedding` against a plan that embeds it,
  then mutate one non-goal in the plan and watch it fail.
- bp-121 (the verifier core) consumes `capsule_hash` **only as a hex string**, so nothing here
  gates it; the two remain `parallelizable_with` as planned.

### Context-manifest delta

Read **beyond** the §2 manifest: `CLAUDE.md` and `.claude/agents/builder.md` (the contract);
`pyproject.toml` `[tool.ruff]`/`[tool.mypy]` (Q2 re-confirmation and the strictness floor);
`tests/unit/test_exhaust_report.py` (the AST no-core-import precedent this file follows);
`.claude/skills/checkpoint/SKILL.md`, `.claude/skills/finding/SKILL.md`,
`docs/templates/finding.md`, `docs/supplemental/cockpit.md` §"read-map block format" (artifact
forms); `docs/build-plans/bp-123/journal.md` (journal house style). Nothing in the manifest proved
irrelevant — `docs/templates/capsule.md` was the most load-bearing read of the five, because it is
the file this plan must **not** touch.

### Open questions

One, routed, parking nothing: **finding-0219** (`spec-defect` → orchestrator). No `design`, `math`,
or `direction` question arose beyond it, and no `codebase`/`spec-fidelity` question needed
resolving that the code and the plan did not settle.

## Follow-through
- **Built?** Yes — all four items. `docs/templates/intent-capsule.md` (18 lines, the eight §2.2
  fields, the caps and the canonical form as prose, the §4 disambiguation header);
  `scripts/capsule.py` (`hash` / `validate` / `check-embedding`, stdlib only, 0 mypy errors);
  `tests/unit/test_capsule.py` (51 tests, every named falsifier drilled). Every §7 acceptance
  criterion met, with the evidence recorded above.
- **Wired / delivered (or why dormant)?** ⚑ **Deliberately not wired, and there is no ON switch to
  build here.** The tool is a hand-run CLI, which is the whole of its deliverable at AP1: the
  consumers the design names (the verifier's P1–P5 pre-flight, Gate A's intent-fidelity audit, the
  exhaust-lane render) are bp-121, AP3 and AP7, and §9 non-goals 1–6 forbid this plan from touching
  a hook, a gate, a config schema, or `.claude/**`. The "wiring is part of finishing" rule is
  satisfied in the only form available: the CLI exists, runs, and documents itself in `--help` and
  its module docstring. No flag exists because no flag is meaningful for a tool with no automated
  caller yet.
- **Does a consumer use it?** **Not yet — none exists.** Today's only callers are its own tests and
  a human at a shell. Named future consumers, in dependency order: **bp-121** (the verifier core —
  consumes `capsule_hash` as a hex string only, no code dependency), **AP3** (config schema +
  capsule render to the exhaust lane — the first *automated* caller, and the one blocked on §11
  row 1's delivery decision), **AP7** (audit gates A/B). `check-embedding` is what makes note
  invariant 3 checkable, so Gate A is the consumer that gives it teeth.
- **Track state (what remains on this track)?** `workflow` track, the autopilot family from
  `dn-autopilot-and-delegated-blessing`. **bp-120 done** (this plan — pending the owner's flip and
  its deskcheck). **bp-121** — the verifier core — was blessed `ready` and runs in parallel.
  **Un-minted still:** AP3 (render, needs §11 row 1), AP6 (halt list H1–H8 + run artifacts), AP7
  (audit gates + `board.py` `audit_refs`). **Parked on owner rulings:** AP4 (the verifier as an
  actor — oq-0037 / finding-0207) and AP5 (post-hoc verification in `journal-gate` — oq-0036 /
  finding-0206). **AP8 (the constitutional edits) is the owner's hand**, not a build item: §3(1)
  amends `dn-agent-workflow`, which is `status: ratified` and therefore agent-immutable under A8.
  So the family is 1 of ~8 stages landed, and autopilot cannot run at any tier today.
- **Opened a new track/finding?** One finding, no new track. **finding-0219** — `spec-defect`,
  `route: orchestrator`, `status: open`: the ≤ 40-line / ≤ 300-word cap bounds the capsule's
  *shape* but not its *size*, so a 38 KB capsule validates clean. It is Item 3's own named
  falsifier firing, it parks nothing, and it needs an owner ruling among three candidates. Not
  fixed here because §6 pins the counts and §11 row 3 pins their non-configurability.

## Markers
