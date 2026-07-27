---
type: build-plan
id: bp-139
track: workflow
status: ready
design_ref:
  - docs/design-notes/dn-autopilot-and-delegated-blessing.md
contract: builder
write_scope:
  - config/defaults.toml
  - core/kernel/config/loader.py
  - scripts/capsule_render.py
  - tests/unit/test_capsule_render.py
  - tests/unit/test_autopilot_wiring.py
  - docs/templates/grant-record.md
session_budget: 1
cost:
  estimate:
    model: opus
    tokens: 250k
  actual: null
depends_on: [bp-138]
parallelizable_with: []
created: 2026-07-27
updated: 2026-07-27
links:
  - docs/findings/finding-0115.md
  - docs/findings/finding-0219.md
  - docs/build-plans/bp-120/plan.md
  - docs/design-notes/exhaust-lane.md
re_entry: null
supersedes: null
superseded_by: null
warrant: null
---

# Build Plan — AP6: the ON switch — `[autopilot]` reaches a caller, and the capsule reaches the phone as bytes it can hash

## 0. Mode & provenance

**Graduated from `dn-autopilot-and-delegated-blessing` §4 (Wiring & enablement), §2.7(1) (the grant
record), and §2.9 invariant 2** (`status: ratified`). Investigation and planning produced this;
implementation proceeds item-by-item on owner approval. The `proposed → ready` blessing is the
owner's and is not performed in any session.

⚑ **Bootstrap wrinkle:** this plan builds part of *delegated* blessing and is itself blessed by the
owner's hand, at the keyboard. Stated once per wave in `bp-135` §0 and again here.

⚑ **This plan exists because AP1 shipped un-runnable, and the owner ruled that is not done.**
`bp-120` delivered the intent capsule — typed, hashed, validated, 2153 tests green — and the
mechanism is **unusable today**: there is no config section, no way to put a capsule in front of the
owner, and no record for a grant to land in. The standing rule is that flag-off is not done and the
ON switch — config schema plus wiring — must **exist** as part of the deliverable, even gated off,
with the enable path inside `write_scope`. It is (§5). This plan is that rule applied to the
autopilot family so the family does not repeat AP1's shape.

⚑ **Last in the wave.** `depends_on: [bp-138]`, which itself depends on the three seat-filling
plans. The switch cannot precede the machinery it switches on.

## 1. Objective

Autopilot gains an off-by-default config section that provably reaches a caller, and a capsule
renders to the exhaust lane as **both** a readable page and the exact canonical bytes the phone
hashes.

## 2. Context manifest

Read in this order, whole files before citing:

1. `docs/design-notes/dn-autopilot-and-delegated-blessing.md` — **§4 whole**, **§2.7(1)** (the
   grant record's fields and its two prohibitions), **§2.9 invariant 2** (*"No code verifies against
   a text the owner did not read: code issuance and capsule render are one phone-side act"*), and
   **§1.2**. The authority for everything below.
2. `docs/build-plans/bp-120/plan.md` — whole, and especially **§11 row 1**: the parked decision that
   the capsule must travel as **raw canonical text** alongside any HTML render, because *"HTML
   rendering is not byte-preserving"* and a phone merely **handed** a hash could be shown text X
   while approving `sha256(Y)`. ⚑ This plan is that row's re-entry condition. Its §3 additional-risk
   paragraph (`:134-142`) is the argument, in full.
3. `scripts/capsule.py` — whole. `canonical`/`canonical_text`/`capsule_hash` (`:94-114`) produce the
   bytes this plan places. **Not re-derived here.**
4. `scripts/exhaust_report.py` — whole (95 lines). `place_report` (`:41`), `report_name` (`:35`),
   the config-derived destination (`:57-58`) and the import discipline (`:16-19`). The lane exists;
   this plan uses it, it does not rebuild it.
5. `tests/unit/test_exhaust_report.py` — whole. The AST allowlist (`:163-179`) and the ingest
   invariant (`:73`, `:79`) — the two properties a second writer into the same lane must not break.
6. `core/kernel/config/loader.py` — the `Config` dataclass (`:388`), the optional-section idiom
   (`:646-650`, `selfmod`), the required-section idiom (`:544`, `exhaust`), and the overlay chain
   (`:433-435`, `:488-497`).
7. `docs/findings/finding-0115.md:32` — ⚑ the sentence that makes Item 22's degenerate input real:
   *"**A section with no corresponding `Config` field is parsed into `raw` and then silently
   DROPPED** — it never reaches a caller."*
8. `config/defaults.toml` — the shape and ordering of existing sections; `[exhaust]` at `:65`.
9. `docs/findings/finding-0219.md` and `docs/inbox/owner-questions.md:1899-1933` (`oq-0054`) — the
   capsule's caps bound **shape, not bytes**, and the ruling is **`open` with no recorded answer**.
   This plan must not assume a byte bound (§9).
10. `docs/brainstorms/the-false-success-rule.md:17-31`, `:52-65`.

**DRY audit — does `core/` already have this?** (owner rule.) **Partly, and the answer is "reuse,
do not rebuild".** The exhaust lane already exists: `scripts/exhaust_report.place_report`
(`scripts/exhaust_report.py:41-64`) resolves `get_config().exhaust.path / "reports"` and places a
file there, with `report_name` (`:35-38`) owning the filename convention. This plan **imports and
calls it** for the HTML half rather than re-deriving a destination — two writers computing the same
directory is the duplication the owner grades as a defect, and here a drifted copy would put the
capsule somewhere Syncthing does not carry. Canonicalization and hashing are `scripts/capsule.py`'s
(`:94-114`) and are imported, never re-implemented — invariant 3 depends on there being exactly one
implementation. `core/` holds nothing of this shape; the config **loader** is core's and is extended
in place, which is the opposite of duplication.

## 3. Investigation & grounding

- **Q1 — what does it take for `[autopilot]` to reach a caller?** **Four edits in two files, and
  omitting any one of them yields a section that silently does nothing.**
  (a) `config/defaults.toml` — the `[autopilot]` table itself, appended after the last section
  (`:410`). (b) `core/kernel/config/loader.py:378` region — a frozen `AutopilotConfig` dataclass
  beside the others. (c) `:412` region — `autopilot: AutopilotConfig = field(default_factory=...)`
  on `Config` (`:388`). (d) `:510` and `:682` regions — `ap = raw.get("autopilot", {})` and the
  `autopilot=AutopilotConfig(...)` block inside `load_config`.
  ⚑ The failure mode if (b)–(d) are skipped is **silent**, not loud: `finding-0115.md:32`, and the
  live proof is still in the tree — `config/defaults.toml:67`'s `[planes]` has no dataclass, and
  its only reader goes around the loader entirely (`tests/unit/test_plane_migration.py:397` reads
  the TOML with `tomllib`).
- **Q2 — required or optional section idiom?** **Optional.** Copy `selfmod`
  (`core/kernel/config/loader.py:646-650`): `raw.get("autopilot", {})` plus per-key
  `.get(key, default)`. ⚑ Do **not** copy `exhaust` (`:544`, bare `raw["exhaust"][...]`) — that
  shape raises on a config that omits the section, and an autopilot section that can break an
  unrelated deployment by its absence is the opposite of off-by-default.
- **Q3 — is there a parity test that would catch a missing dataclass?** **No — none exists.** The
  only four readers of `defaults.toml` (`tests/unit/test_config_split.py:29`,
  `test_code_ingest_wiring.py:43`, `test_plane_migration.py:397`,
  `tests/integration/test_secrets_backend_wiring.py`) all assert **specific values**; none asserts
  key/field parity. `[planes]` being schemaless and green is the empirical proof. ⇒ Item 22 must
  assert **both** halves itself, and the pattern to copy is
  `tests/unit/test_config_split.py:33` — `assert load_config(_DEFAULTS).secrets.enabled is False`.
- **Q4 — does the machine overlay change where the section is declared?** **No.** Precedence is
  `defaults ← levers.toml ← ouroboros.toml` (`core/kernel/config/loader.py:488-497`) and the merge
  is a **shallow per-section update** that *"names just the keys it changes"* (`:433-435`). Both
  overlays are gitignored (`.gitignore:28`, `:32`). So the section must be declared in
  `config/defaults.toml` regardless, and a fresh clone or CI is safe-by-default — which is exactly
  what `config/ouroboros.toml:1-3` says.
- **Q5 — can a second writer share the exhaust lane safely?** Yes, and two existing properties
  constrain how. `tests/unit/test_exhaust_report.py:163-179` pins that writer's imports to
  `{__future__, argparse, shutil, sys, datetime, pathlib, config}`; `:73`/`:79` pin an **ingest
  invariant** on the lane's contents; and `tests/unit/test_plane_migration.py:300` is an ownership
  ratchet, `test_ratchet_exhaust_reports_owned_by_work`. ⚑ The new writer must satisfy the same
  ownership expectation and must not break the ingest invariant. It is a **new file** — those three
  tests are about `exhaust_report.py` and the lane, not about this plan's module, so none is in
  `write_scope`; if any reddens, that is a manifest defect (§10).
- **Q6 — how is the push notification fired?** ⚑ **It is not in the repository.** A grep across
  `.py/.sh/.md/.json/.yml` for `PushNotification|push_notification|pushover|ntfy` returns exactly
  two hits, both prose in design notes (`docs/design-notes/exhaust-lane.md:107` and this note's
  `:437`), and zero code. The composing and firing step is an **agent harness action** held in the
  owner's `phone-build-report` standing rule. ⇒ **No acceptance criterion in this plan may depend
  on a notification being sent**, because nothing in the repo can send one. §2.7(5)'s run report is
  therefore the supervisor's obligation (documented in `bp-136`'s skill), not a build item here
  (§9).
- **Q7 — enrollment, imports, lint?** `pyproject.toml:128` enrolls `scripts/` and `core/` by
  directory; `scripts` is a **Tier-2 0-error hard floor** and `core.*` is additionally **Tier-1
  strict** (`pyproject.toml:140-147`), so the loader edit must be fully typed. ruff
  `line-length = 100`. The `sys.path` bootstrap needs `# noqa: E402`. ⚑ `scripts/capsule_render.py`
  imports **`config`** (for the exhaust root, via `exhaust_report`) — so its AST allowlist is
  `exhaust_report.py`'s, not `capsule.py`'s stricter one (§6).

**Additional risks or questions surfaced during reading:**

⚑ **The queue is wedged and nothing in this plan may depend on ingestion.** As of 2026-07-27 the
scheduler queue holds a stranded `code_sync` job with ~1,766 queued behind it. The exhaust lane's
**ingest** invariant (`tests/unit/test_exhaust_report.py:73`, `:79`) is a *unit* property of paths
and is unaffected — but any acceptance that required a placed file to be **ingested** could not
pass today. None below does; every criterion is a file-existence, byte-equality or exit-code check.
Stated so a builder does not add one.

⚑ **`oq-0054` is open with no recorded answer.** `docs/inbox/owner-questions.md:1922-1933` records
that a ruling was evidently made in conversation on 2026-07-26 but **no answer text was ever
written**, and the orchestrator refused to invent one. The capsule's caps therefore still bound
**shape, not bytes** (`finding-0219`). ⇒ The render must not assume a byte bound, must not add one,
and must not fail a capsule for size beyond what `capsule.py validate` already enforces (§9).

## 4. Reconciliation

- `docs/build-plans/bp-120/plan.md:364` (§11 row 1) — the parked delivery decision, whose default
  is *"The capsule travels as **raw canonical text** alongside any HTML render, so the phone hashes
  the bytes it displayed"* → **[cross-ref: extension]**. This plan is that row's **re-entry
  condition** (*"AP3 (the render plan) is graduated"*). It implements the recorded default rather
  than re-deciding it; Item 23 makes the property testable, and the row is answered rather than
  quietly inherited. `bp-120/plan.md` is `complete` and out of `write_scope`: the answer lives
  here, and the journal records that the row is discharged.

- `scripts/exhaust_report.py:35-38` (`report_name`, `f"{on.isoformat()}-{plan}-{slug}.html"`) →
  **[cross-ref: extension]**. The lane's filename convention is `.html`-suffixed. The capsule needs
  a **second** artifact with a `.txt` suffix and the same stem. Rather than change `report_name`
  (out of scope, and it has callers), `scripts/capsule_render.py` derives the sibling name from
  `report_name`'s output by suffix replacement and states the coupling in a comment naming
  `exhaust_report.py:35-38`. ⚑ If that proves too fragile, the correct move is a `suffix` parameter
  on `report_name` — which is a change to `exhaust_report.py`, out of `write_scope`: file a finding,
  do not widen (§10).

- `core/kernel/config/loader.py:544` (`exhaust=ExhaustConfig(path=Path(raw["exhaust"]["path"])…)`)
  → **[cross-ref: extension]**, not corrected. The bare-subscript required-section idiom is left
  exactly as it is; `[autopilot]` uses the `.get()` optional idiom instead (§3 Q2) and the new
  code's comment names the deliberate difference so a later reader does not "fix" the
  inconsistency into a crash.

## 5. Write scope

Six paths — three new, three changed. ⚑ This list **is** the enable path, in `write_scope`, per the
standing "wiring is part of finishing" rule.

- `config/defaults.toml` — **changed**. The `[autopilot]` table, `enabled = false`.
- `core/kernel/config/loader.py` — **changed**. `AutopilotConfig`, the `Config` field, the
  `load_config` wiring block. Without these three the TOML section is inert (§3 Q1).
- `scripts/capsule_render.py` — **new**. Places the capsule into the exhaust lane as raw canonical
  bytes **and** HTML, and refuses when the flag is off.
- `tests/unit/test_capsule_render.py` — **new**.
- `tests/unit/test_autopilot_wiring.py` — **new**. The two-sided config assertion (§3 Q3) and the
  grant-record template's checks.
- `docs/templates/grant-record.md` — **new**. §2.7(1)'s record, with its two prohibitions.

**Deliberately OUT of scope** — a denial means file a finding, never widen by hand:

- `scripts/exhaust_report.py` and `tests/unit/test_exhaust_report.py` — the lane writer is
  **imported and called**, never modified (§4, DRY audit).
- `scripts/capsule.py` and `tests/unit/test_capsule.py` — canonicalization and hashing are imported,
  never re-implemented; invariant 3 depends on there being exactly one implementation.
- `scripts/grant_core.py` — `bp-138`'s. This plan writes the record *template*; it computes no tag
  and holds no secret.
- `config/loader.py`, `config/__init__.py`, `core/kernel/config/__init__.py` — the facade
  re-exports. **Not needed**: nothing outside `core` imports the `AutopilotConfig` *class*, only
  `get_config().autopilot`. `ExhaustConfig` is likewise absent from `config/__init__.py:4-13`, so
  this follows the established precedent rather than inventing a wider surface.
- `config/ouroboros.toml`, `config/levers.toml` — gitignored machine overlays (`.gitignore:28`,
  `:32`); a section must be declared in `defaults.toml` regardless (§3 Q4).
- `.claude/hooks/**` (parked on `oq-0036`), `docs/design-notes/**` (A8, agent-immutable), and the
  foundation denylist (`CONSTITUTION.md`, `eval/golden/**`, `eval/golden.py`), which binds
  regardless.

**Acceptance-reachability check** (findings 0177/0191/0204):

| item | files its acceptance must modify | all in §5? |
|---|---|---|
| 22 | `config/defaults.toml`; `core/kernel/config/loader.py`; `tests/unit/test_autopilot_wiring.py` | ✓ |
| 23 | `scripts/capsule_render.py`; `tests/unit/test_capsule_render.py` | ✓ |
| 24 | `scripts/capsule_render.py`; `tests/unit/test_capsule_render.py` | ✓ |
| 25 | `docs/templates/grant-record.md`; `tests/unit/test_autopilot_wiring.py` | ✓ |

Non-obvious targets checked against the graduate skill's list:
**(a) protocol member on an out-of-scope class** — none; `AutopilotConfig` is a new dataclass and
`Config` is in scope. **(b) allowlist / registry / manifest enrollment** — `pyproject.toml:128`
covers both `scripts/` and `core/` by directory, so no `[tool.mypy].files` edit is needed;
`ops/import_lint.py`'s `NETWORK_ALLOWLIST` is irrelevant (nothing here touches a network
primitive); `.claude/settings.json` registers nothing relevant. **(c) a call site in a test outside
this plan's own test files** — the four existing readers of `defaults.toml`
(`tests/unit/test_config_split.py`, `test_code_ingest_wiring.py`, `test_plane_migration.py`,
`tests/integration/test_secrets_backend_wiring.py`) assert **specific values**, not key/field
parity (§3 Q3), so **adding** a section and a dataclass field should not redden them. ⚑ That is a
reasoned expectation, not a guarantee — the loader is widely imported. If any of the four reddens,
it is a manifest defect: file a `spec-fidelity` finding and stop (§10). It is deliberately **not**
pre-widened, because carrying four unrelated test files would grant a capability this plan has no
intent to use.

## 6. Interfaces pinned inline

**§4's wiring sentence, verbatim** (`dn-autopilot-and-delegated-blessing.md:508-517`) — the scope of
this plan and of its parked siblings, in the note's own words:

> config schema `[autopilot]` (`enabled = false` default) in `config/defaults.toml` + loader; the
> `mfa-verifier` script (dual-mode like every hook: stdin JSON and standalone, fail-loud
> `HOOK-FAILURE` on error) holding no secret in code — Keychain read at invocation (NN-10); the
> phone-side code generator (parked …); capsule render placed into `~/.mind-palace/exhaust/reports/`
> (lane exists — Syncthing to phone); inbound code path v1 = owner enters the code via any shell
> (SSH/Tailscale) into the verifier's standalone mode …; the journal-gate (c) exception and the
> P1–P5 pre-flight inside the verifier; the halt-list supervisor as orchestrator-session logic (no
> daemon change).

⚑ Of that list this plan builds **the config schema and the capsule render**. The `mfa-verifier`
script, the Keychain read, the inbound code path and the journal-gate exception are the **parked**
AP-actor/AP-posthoc plans (`oq-0037`/`oq-0036`); the halt-list supervisor is `bp-136`; the P1–P5
pre-flight is `bp-137`.

**Invariant 2, verbatim** (`:463-464`): *"No code verifies against a text the owner did not read:
code issuance and capsule render are one phone-side act."*

**`bp-120` §11 row 1's default, verbatim** (`docs/build-plans/bp-120/plan.md:364`): *"The capsule
travels as **raw canonical text** alongside any HTML render, so the phone hashes the bytes it
displayed"* — rejecting *HTML-only delivery* because *"rendering is not byte-preserving, so the
phone could only be **handed** a hash, and an agent could then render X while handing `sha256(Y)`;
the owner would approve a text he never read, defeating invariant 2."*

**The config section — DEFINED HERE.** In `config/defaults.toml`:

```toml
[autopilot]
# dn-autopilot-and-delegated-blessing §4. OFF by default: the flag alone authorizes
# nothing — no run is possible without a per-run grant, and no grant exists until the
# owner's phone makes a code against a specific capsule hash.
enabled = false
ttl_hours = 72          # §2.3's TTL default, parked there for owner tuning
```

In `core/kernel/config/loader.py`, beside the other frozen dataclasses:

```python
@dataclass(frozen=True)
class AutopilotConfig:
    enabled: bool = False
    ttl_hours: int = 72
```

on `Config`: `autopilot: AutopilotConfig = field(default_factory=AutopilotConfig)`; and in
`load_config`, following the `selfmod` idiom at `:646-650` exactly:

```python
ap = raw.get("autopilot", {})
...
autopilot=AutopilotConfig(
    enabled=bool(ap.get("enabled", False)),
    ttl_hours=int(ap.get("ttl_hours", 72)),
),
```

**The render's CLI surface — DEFINED HERE:**

```
uv run scripts/capsule_render.py place <capsule-file> --plan bp-NNN [--force]
    -> when autopilot.enabled is False and --force is absent:
         writes NOTHING, prints one diagnostic naming the flag, exit 1
    -> otherwise places TWO files into get_config().exhaust.path / "reports":
         <date>-<plan>-capsule.txt   the CANONICAL BYTES, byte-identical to
                                     capsule.canonical(raw)
         <date>-<plan>-capsule.html  a readable render that DISPLAYS the digest
       prints both paths and the digest, exit 0
    -> exit 1, writing nothing, if `capsule.validate` reports any diagnostic
```

**The two-artifact invariant, pinned:** `sha256(the .txt file's bytes)` **must equal** the digest
printed in the `.html`, **and** must equal `capsule.capsule_hash(raw)`. The `.txt` is the object of
the grant; the `.html` is a courtesy. A test asserts all three agree, and asserts the `.txt` is
byte-identical to `capsule.canonical(raw)` — not merely equal after re-canonicalization, which
would hide exactly the transformation the invariant forbids.

**The grant record — DEFINED HERE** from §2.7(1), which names the fields in prose:

```yaml
---
type: grant-record
id: grant-<plan-id>
plan: bp-NNN
capsule_sha256: <64 lowercase hex>
base_commit: <sha>
issued_at: <RFC-3339 UTC, second precision, Z>     # bp-138 §6's pinned form
verified_at: <RFC-3339 UTC, second precision, Z>
ttl_hours: 72
budget_tokens_ceiling: <int>
predicates:                                        # bp-137's P1-P5 report line
  p1: pass|fail|undetermined
  p2: pass|fail|undetermined
  p3: pass|fail|undetermined
  p4: pass|fail|undetermined
  p5: pass|fail|undetermined
attestation_tag: <64 lowercase hex>                # bp-138 §6, full width, never truncated
---
## The capsule, verbatim
<the canonical capsule text, unaltered>
```

⚑ **The two prohibitions, from §2.7(1), carried in the template as a rule and as a test:**
**never the code, never the secret.** *"the code is verified and discarded"*. The template carries
no field for either, and Item 25's test asserts the template's field names contain no `code` and no
`secret`, and that its prose states the prohibition. ⚑ Note the nested `predicates:` mapping is
**not** parseable by `_lib.parse_front_matter` (a YAML subset, `.claude/hooks/_lib.py:180-182`); as
in `bp-135` §6, the flat form `predicate_p1: … predicate_p5:` is what ships, and the nested display
above is illustrative only.

## 7. Items

Ordered by blast radius: the config edit (inert while `enabled = false`) → the render's read-only
half → the fail-closed switch → the inert template. Item numbering continues the family (`bp-120`
1–4, `bp-135` 5–8, `bp-136` 9–13, `bp-137` 14–17, `bp-138` 18–21).

### Item 22 — `[autopilot]` reaches a caller, not just a TOML file

- **Objective:** the config section exists **and** arrives at `get_config().autopilot`, so the
  switch is real rather than decorative.
- **Files:** `config/defaults.toml`, `core/kernel/config/loader.py`,
  `tests/unit/test_autopilot_wiring.py`
- **Acceptance test:** `uv run pytest tests/unit/test_autopilot_wiring.py -q` green on **both**
  halves: (a) `config/defaults.toml`, read directly with `tomllib`, declares `[autopilot]` with
  `enabled = false` — the `tests/unit/test_code_ingest_wiring.py:43` pattern, which reads the file
  directly so a machine overlay cannot mask it; and (b)
  `assert load_config(_DEFAULTS).autopilot.enabled is False` and `.ttl_hours == 72` — the
  `tests/unit/test_config_split.py:33` pattern. Then the full gate: `uv run ruff check .`,
  `uv run python scripts/check_imports.py`, `uv run mypy core agents eval ops scheduler scripts`
  (0 errors — `core.*` is Tier-1 strict), `uv run python -m ops.type_gate`, and `uv run pytest -q`
  showing no **new** failures beyond the two known-expected ones (the finding-0103 ratchet and the
  finding-0226 dream-v2 live test).
- **Falsifier:** adding the section reddens an existing consumer of `Config` — the frozen dataclass
  has a positional construction site somewhere that a new field breaks. ⚑ Drill it: grep for
  `Config(` construction sites outside `load_config` before writing, and record what was found. If
  one exists and is positional, that is the falsifier and the field ordering matters.
- **⚑ Degenerate input (false-success rule):** **the TOML section with no dataclass field.** A test
  that only reads `defaults.toml` with `tomllib` passes while `load_config` parses the section into
  `raw` and **silently drops it** — it never reaches a caller (`finding-0115.md:32`), and
  `config/defaults.toml:67`'s `[planes]` is the live proof that this exact state ships green today.
  Assert the check reddens: **delete the `Config.autopilot` field, re-run, and show half (b) going
  red while half (a) stays green.** That demonstration is the item's real acceptance — recorded in
  the journal with the actual output.
- **⚑ Mutation obligation** (`the-false-success-rule.md:52-65`): mutate (m1) the `Config` field
  away; (m2) the `load_config` wiring block away, leaving the field at its default — half (b) must
  still catch it via a non-default value probe; (m3) `enabled` to default `True`. Each caught by a
  named test.
- **Invariant(s) it must not violate:** ⚑ **off by default, and the flag alone authorizes
  nothing** (§4: *"the enable flag alone authorizes nothing, because no code exists until the
  owner's phone makes one against a specific capsule hash"*). The optional `.get()` idiom, never
  `exhaust`'s bare subscript (§3 Q2) — a config omitting the section must not raise.
- **Touches stored data?** No.
- **Parallelizable?** yes  **Depends on:** none

### Item 23 — the render places the bytes the phone hashes, not only a page it cannot

- **Objective:** invariant 2 becomes achievable — the capsule reaches the phone in a form the phone
  can hash for itself.
- **Files:** `scripts/capsule_render.py`, `tests/unit/test_capsule_render.py`
- **Acceptance test:** green on: `place` writes **two** files into
  `get_config().exhaust.path / "reports"` (redirected to `tmp_path` in tests) with the same stem and
  `.txt`/`.html` suffixes; the `.txt` is **byte-identical** to `capsule.canonical(raw)`; the digest
  printed in the `.html` equals `capsule.capsule_hash(raw)` equals `sha256` of the `.txt` bytes;
  `place` exits 1 and writes **nothing** when `capsule.validate` reports any diagnostic; the module
  calls `exhaust_report.place_report` for the HTML rather than computing the destination itself
  (AST-asserted); and the AST import allowlist matches `exhaust_report.py`'s
  (`{__future__, argparse, shutil, sys, datetime, pathlib, config}` plus `capsule` and
  `exhaust_report`), with **no** `os`, `subprocess`, `keyring`, `hmac`, or `core`.
- **Falsifier:** the `.txt` and the `.html` disagree — the digest shown to the owner is not the
  digest of the bytes beside it. That is invariant 2 defeated inside the very artifact meant to
  secure it. ⚑ Drill it: mutate one character of the `.txt` after placement and show the
  consistency check catching it.
- **⚑ Degenerate input (false-success rule):** **an HTML-only placement.** A render that writes only
  the page satisfies "the capsule reached the phone" and passes any file-exists check — while the
  phone can then only be **handed** a hash, which is precisely the attack `bp-120` §11 row 1
  rejects: render X, hand `sha256(Y)`, and the owner approves a text he never read. Assert the
  check **reddens** when the `.txt` is absent, and separately when the `.txt` is present but its
  sha256 differs from the digest in the `.html`. Second degenerate: a `.txt` written from the
  **raw** file rather than from `capsule.canonical(raw)` — identical for a well-formed capsule,
  divergent for one with CRLF line endings. Assert the check reddens on a CRLF input.
- **⚑ Mutation obligation:** the two-artifact invariant is load-bearing. Mutate (m1) the `.txt`
  write to use `raw` instead of `canonical(raw)`; (m2) the digest in the HTML to be computed from
  the HTML body; (m3) drop the `.txt` write entirely. All three caught by named tests.
- **Invariant(s) it must not violate:** invariant 2, and invariant 3 by construction — it imports
  `capsule.canonical`/`capsule_hash` and re-implements neither. It must not break the lane's ingest
  invariant (`tests/unit/test_exhaust_report.py:73,79`) or its ownership ratchet
  (`tests/unit/test_plane_migration.py:300`) — neither file is in `write_scope`, so a red there is
  a stop-and-raise (§10).
- **Touches stored data?** No — it writes into the exhaust lane (`~/.mind-palace/exhaust/reports/`),
  which is an outbound courier directory, not a store. No vector store, no sqlite, no corpus. Tests
  redirect the destination to `tmp_path` and never write to the real lane.
- **Parallelizable?** no  **Depends on:** Item 22

### Item 24 — the switch is fail-closed

- **Objective:** `autopilot.enabled = false` is load-bearing — the render refuses rather than
  proceeding with a warning.
- **Files:** `scripts/capsule_render.py`, `tests/unit/test_capsule_render.py`
- **Acceptance test:** green on: with `enabled = False` and no `--force`, `place` writes **zero**
  files (asserted by listing the destination directory before and after), prints one diagnostic
  naming `autopilot.enabled`, and exits 1; with `enabled = False` and `--force`, it places both
  files and prints a line stating the flag was overridden; with `enabled = True`, it places both
  without a `--force`.
- **Falsifier:** `--force` becomes the normal invocation because the flag is inconvenient — then the
  switch is decorative in practice even though it works in test. ⚑ Drill it: the builder documents
  the intended flow in the module docstring (attended use = `--force`; a real grant run = the flag
  on) and states in the journal which of the two the first deskcheck will exercise.
- **⚑ Degenerate input (false-success rule):** **a flag read that never fails closed** — the
  natural implementation reads `get_config().autopilot.enabled`, logs "autopilot disabled", and
  places the files anyway, because refusing to write feels unhelpful. Every file-exists assertion
  still passes. Assert the **before/after directory listing** is unchanged in the disabled case;
  a check that only asserts a non-zero exit code passes on an implementation that writes and *then*
  exits 1. Second degenerate: the config read raising (no `[autopilot]` section at all, e.g. an old
  overlay) — a bare `except` that defaults to "enabled" fails open. Assert a missing section is
  treated as **disabled**, matching Item 22's `.get()` default.
- **Invariant(s) it must not violate:** §4 — *"the enable flag alone authorizes nothing"*. Refusing
  is safe; proceeding is not. Ambiguity resolves toward refusing (invariant 7).
- **Touches stored data?** No.
- **Parallelizable?** no  **Depends on:** Item 23

### Item 25 — `docs/templates/grant-record.md`: the record, and the two things it must never hold

- **Objective:** §2.7(1)'s grant record exists as a typed template that structurally cannot carry a
  code or a secret.
- **Files:** `docs/templates/grant-record.md`, `tests/unit/test_autopilot_wiring.py`
- **Acceptance test:** the file exists and parses; `_lib.parse_front_matter` returns exactly the §6
  key set (flat `predicate_p1..p5`, not nested); a test asserts **no** front-matter key contains
  `code` or `secret` as a word; a test asserts the template's prose carries the §2.7(1) prohibition
  verbatim — *"**Never the code or the secret**"* — and states that the code is verified and
  discarded; and a test asserts the template contains an `attestation_tag` field described as
  **full width, 64 hex, never truncated** (invariant 9).
- **Falsifier:** a real grant record cannot be filled from what the parked actor will actually have
  at flip time — a field has no source. ⚑ Drill it: fill the template by hand for a hypothetical
  trivial run using only values `bp-137` and `bp-138` can produce, and name every field with no
  source. A field with no source is a `spec-defect` against §2.7(1), filed, not invented.
- **⚑ Degenerate input (false-success rule):** **a template that carries a `code:` field commented
  out**, or one whose prose mentions the prohibition inside an HTML comment. A key-name check passes
  (the key is not active) and a `substring in text` prose check passes (the comment is in the file)
  — both green without testing the claim. Assert the key check scans the **whole file** for a
  `code:`/`secret:` line at any indentation including inside comments, and that the prose check
  reads rendered prose rather than comments.
- **Invariant(s) it must not violate:** NN-10 and §2.7(1) — the record proves the binding
  *checkably*, never by narrative (invariant 9). ⚑ This item creates a **template**; it writes no
  record and computes no tag. The writer is the parked AP-actor plan.
- **Touches stored data?** No.
- **Parallelizable?** yes  **Depends on:** none

## 8. Math carried explicitly

`N/A — no mathematical object implemented.` The two-artifact invariant is an equality between an
existing digest (`bp-120` §8's commitment) and a file's bytes; the config wiring is plumbing. The
wave's mathematical objects are `bp-120` §8 (the capsule commitment) and `bp-138` §8 (the keyed
PRF and the MAC).

## 9. Non-goals

1. **⚑ No verifier, no secret, no Keychain, no code entry.** §4's `mfa-verifier`, its Keychain read
   and the inbound code path are the **parked** AP-actor plan (`oq-0037`, and now `finding-0262`).
   Nothing here reads or holds a secret.
2. **No status flip.** No `proposed→ready`, no plan mutation, no `journal-gate` change
   (`oq-0036`, parked).
3. **No grant record is written** — the template only (Item 25).
4. **No push notification.** Nothing in the repository can send one (§3 Q6); §2.7(5)'s run report is
   the supervisor's obligation, documented in `bp-136`'s skill.
5. **No phone-side generator.** Parked by the note itself; §2.3 fixes the *property*, not the
   implementation.
6. **⚑ No character cap on the capsule.** `oq-0054` is `open` with **no recorded answer**
   (`docs/inbox/owner-questions.md:1922-1933`); the caps bound shape, not bytes (`finding-0219`).
   Adding one is a design act and `bp-120` §11 row 3 forbids making them configurable.
7. **No change to `scripts/exhaust_report.py`** — imported and called, never modified (§4).
8. **No ingestion, no daemon, no deploy.** The queue is wedged (§3) and no acceptance here depends
   on ingestion.
9. **No facade re-exports** of `AutopilotConfig` (§5). [INFERENCE — that following `ExhaustConfig`'s
   precedent (absent from `config/__init__.py:4-13`) is right until a caller outside `core` needs
   the class. If one appears, that is a one-line follow-up.]

## 10. Stop-and-raise conditions

STOP and surface rather than proceed if:

- any of the four existing `defaults.toml` readers, or any other consumer of `Config`, reddens on
  the new section (§5's reasoned expectation is not a guarantee) — file a `spec-fidelity` finding,
  park the criterion, continue the rest. **Never widen the scope by hand and never route around a
  `scope-guard` denial**; a second denial on the same target means the plan is mis-scoped.
- `tests/unit/test_exhaust_report.py` or `tests/unit/test_plane_migration.py:300` reddens — the new
  writer broke the lane's ingest invariant or its ownership ratchet. Both are out of `write_scope`
  deliberately: file a finding and stop.
- `report_name`'s `.html` coupling proves too fragile for the `.txt` sibling (§4) — the fix is a
  parameter on `exhaust_report.py`, out of scope. File a finding; do not widen.
- a grant-record field has no producible source (Item 25's falsifier) — `spec-defect` against
  §2.7(1), routed to the orchestrator, not a value to invent.
- **any item would put a secret, an MFA code, or a status flip within reach.** None is needed here.
  If one appears necessary, that is not a design choice — stop and raise it.
- a `HOOK-FAILURE` line appears — rerun the named hook standalone, reconcile, say so in the journal
  before continuing.
- `depends_on` is unsatisfied — `bp-138` is not `complete`. The switch must not precede the
  machinery it switches on.

## 11. Parked decisions

| Decision | Default recorded | Rejected alternatives (why) | Re-entry condition |
|---|---|---|---|
| `[autopilot]`'s key set beyond `enabled` | `enabled = false` + `ttl_hours = 72` only | *Add budget ceilings, auditor counts, halt toggles* — rejected: §2.6 H4 makes budget non-self-extendable and a config-tunable halt list is a halt list the run can loosen; the note's parked table keeps auditor count a design decision, not a lever | The owner tunes the TTL (the note's own parked row), or a second run needs a lever that does not exist |
| `.txt` + `.html` as two files vs one self-contained HTML with an embedded `<pre>` | Two files, per `bp-120` §11 row 1's recorded default | *One HTML with the canonical text in a `<pre>`* — rejected: extracting exact bytes from HTML requires un-escaping, which is a transformation, and the whole point is that the phone hashes bytes nobody transformed | The phone-side generator lands and proves it can hash a `<pre>` block byte-exactly |
| Whether `--force` should exist at all | Yes — attended use needs it, and without it the flag makes the tool untestable in the disabled state | *No `--force`; flip the config to test* — rejected: mutating real config to run a tool is worse than an explicit, logged override. *Default `--force` on* — rejected: that is the decorative-switch failure Item 24's degenerate input names | `--force` becomes the normal invocation (Item 24's falsifier), at which point the flag needs a different design |
| Where the run report (§2.7(5)) is composed | Not here — the supervisor's obligation, documented in `bp-136`'s skill | *Build an HTML report generator* — rejected: `scripts/exhaust_report.py` already places reports and the **composing** step is agent judgement held in the `phone-build-report` standing rule; nothing in the repo fires the notification (§3 Q6) | A notification mechanism lands in the repo, or the owner asks for a templated run report |

## 12. Dependency & ordering summary

**Within the plan:** Item 22 first (the render reads the flag it adds). Item 23 depends on 22;
Item 24 depends on 23. Item 25 is independent of all three and may be built first or last.
Blast-radius order is the item order: an inert config section (off by default) → a writer confined
to the exhaust lane and to `tmp_path` in test → the fail-closed switch → an inert template. Nothing
is irreversible; every effect is `git checkout`-able except files placed into
`~/.mind-palace/exhaust/reports/`, which tests never write to (they redirect to `tmp_path`) and
which a real run leaves as removable courier artifacts.

**Across the wave:** see `bp-135` §12 for the full map. This plan is last:
`depends_on: [bp-138]`, which itself depends on `bp-135`/`bp-136`/`bp-137`. The chain is the
ordering constraint made structural — the reviewer's seat is filled, then the grant's cryptography
exists, then the switch that would turn any of it on.

**Un-minted and why** (restated so this file stands alone): **AP-actor** — the verifier as an actor
(secret source, invocation boundary, the flip, the grant-record *writer*, and the verification
attempt bound `finding-0262` demands) — **PARKED** on `oq-0037`, `oq-0036` and `finding-0262`.
**AP-posthoc** — the Stop-gate/journal-gate grant-record rule — **PARKED** on `oq-0036`.
**AP-const** — the one-sentence `CLAUDE.md:62` edit (§3(2)) — **PARKED** on the owner's A10
amendment to `dn-agent-workflow`, which is `status: ratified` and agent-immutable under A8, so the
amendment is his hand and the `CLAUDE.md` sentence must not land before it.

⚑ **After this wave, autopilot still cannot run.** Everything is built, wired and off except the
one thing three parked plans hold: the actor that verifies a code and performs the flip. That is
the honest state, and it is stated here so no seal or deskcheck reads this wave as "autopilot
delivered".
