---
type: build-plan
id: bp-047
alias: tuning-manifest
status: complete
design_ref:
  - docs/design-notes/evaluation-harness.md   # §2.6 the automated-tuning layer (manifest half); §3 E3a
contract: builder
write_scope:
  - config/tuning.toml
  - eval/harness/tuning.py
  - scripts/tune.py
  - tests/unit/test_tuning_manifest.py
  - tests/integration/test_tune_cli.py
session_budget: 1
cost:
  estimate:
    model: opus
    tokens: 200k
  actual:
    model: claude-opus-4-8
    tokens: 104k          # harness-measured (subagent_tokens); self-report est ~130-150k
    ratio: 0.52           # 104k / 200k — well under; matches milestone-1's well-pinned delegated builds landing < estimate
    tool_uses: 58
    duration: ~11min
    delegated: true       # parallel supervised builder, worktree
    gate: 5-leg green (orchestrator re-ran independently; argless mypy tail==69; suite 1243)
depends_on: []
parallelizable_with: [bp-048]
created: 2026-07-16
updated: 2026-07-16
links:
  - docs/design-notes/evaluation-harness.md
re_entry: null
supersedes: null
superseded_by: null
warrant: null
---

# Build Plan — E3a-2: the tuning manifest + `scripts/tune.py` (the human control surface over the §14 gate)

## 0. Mode & provenance

Investigation and planning produced this plan; implementation proceeds item-by-item on owner
approval. Authority-to-act (the owner's 2026-07-16 directive to graduate E3a) is separate from the
readiness blessing (owner-only `proposed → ready`); no agent flips readiness. This is the
**manifest half** of E3a — the E3a-1 sweep engine (bp-046, reserved) is the *producer* of
proposals; this plan is the *human control surface* over the same §14 proposal ledger and lever
registry. It is **independent of E3a-1** (both feed/read the built `ProposalLedger`; neither calls
the other) and independent of the σ-lever design fork that parks E3a-1 (this plan is a schema layer
over whatever levers `ops/levers.py` registers — it decides no lever's existence).

## 1. Objective

Add the per-lever tuning manifest (`config/tuning.toml`, an `autonomy`-schema overlay on the built
lever registry) and `scripts/tune.py` (`show` / `set` / `history` / `--revert`), so the owner can
inspect and hand-drive lever changes through the built §14 self-mod gate from one attested CLI.

## 2. Context manifest

Read in order before any work:

1. `docs/design-notes/evaluation-harness.md` §2.6 — the tuning layer: the manifest schema, the two
   autonomy modes, the propose-mode default (`autonomy = "propose"` is the value when the field is
   absent), and the structural fixed-point exclusion.
2. `ops/levers.py` — the whole file: `Lever`, `LEVERS` (the 4 `[dreaming]` levers), `get_lever`,
   `ProposedChange`, `.resolve()`. This plan's manifest is a per-`Lever` overlay; it registers no lever.
3. `ops/selfmod.py` — `SelfModLoop` (`propose` / `approve` / `execute` / `validate` /
   `execute_and_validate`), `build_loop`, `build_golden_validator`, the two fail-closed switches,
   `SAFE_LEVERS`. The CLI's `set`/`--revert` drive this; **it does not reimplement the gate.**
4. `ops/ledger.py` — `Proposal`, `ProposalLedger` (`propose` / `approve` / `all` / `pending` /
   `get`), `LedgerStatus` (the state machine), `open_ledger`. `history` renders this.
5. `config/loader.py:80-95, 256-370, 480-490` — `DreamingConfig`, `Config`, the TOML parse, and
   `get_config` / `refresh_config`. Establishes where live lever values are read from.

## 3. Investigation & grounding

- **Q1 — What is the built self-modifiable surface, and does this plan widen it?** The registry
  `_LEVERS` holds exactly four `[dreaming]` levers — `dream_similarity_threshold` (σ, [0.55,0.75]),
  `dream_near_dup_threshold` ([0.90,0.99]), `dream_min_cluster_size` ([2,6]), `dream_max_clusters`
  ([4,16]) — `ops/levers.py:75-112`. This plan **does not** add or modify a lever; the manifest is a
  per-lever *policy overlay* (autonomy, subsystem, default). Adding a lever is "a deliberate,
  reviewable diff against this registry, never a guess" (`ops/levers.py:11-13`) and is out of scope.
- **Q2 — How does a `set` reach the live config, reversibly?** `SelfModLoop.execute` calls
  `overlay_set(lever, target, overlay_path)` (writes the machine overlay, `LEVERS_OVERLAY`) and
  records the exact prior value for rollback, then `refresh_config()` — `ops/selfmod.py:129-140`.
  `--revert` maps to `SelfModLoop.validate`'s rollback path (`overlay_restore`,
  `ops/selfmod.py:159-164`) **only for an EXECUTED proposal**; a VALIDATED/terminal proposal has no
  successor (`ops/ledger.py:50-55`), so `--revert` on a kept change is a *new* inverse proposal, not
  a state transition. The CLI must surface this distinction, not fake a transition.
- **Q3 — Where do live lever values come from for `show`?** `_section_value(cfg, lever) =
  float(getattr(getattr(cfg, lever.section), lever.key))` — `ops/selfmod.py:78-79`. `show` reuses
  this exact accessor; it does not re-read TOML.
- **Q4 — Is the CLI attended (no auto-apply)?** Yes. This plan implements ONLY the attended path
  (`propose → owner-approve → execute → validate`). The unattended `apply_unattended` path and the
  `auto` autonomy mode (`auto_band`/`auto_max_step`/`auto_cooldown_runs`, derived `SAFE_LEVERS`) are
  **E3b** (`ops/selfmod.py:174-191`; note §2.6) and are explicitly out of scope — the manifest
  schema *reserves* the `autonomy` field but this plan accepts only `"propose"`.
- **Q5 — Does `set` require `[selfmod] enabled`?** Yes — `SelfModLoop._require_enabled` raises
  `SelfModDisabled` when off (`ops/selfmod.py:104-106`). `show`/`history` are read-only and must work
  with the loop disabled; the CLI must not force-enable anything.

**Additional risks surfaced during reading:** (a) `config/tuning.toml` must be **subordinate to
`local.toml` — the human always wins** (note §2.6). This plan's manifest carries *policy* (autonomy,
default), NOT live values; live values remain in the config/overlay chain. Do not let the manifest
become a second value source that could shadow `local.toml`. (b) The loader "hard-fails on unknown
keys" (note §2.6 backstop) — a manifest key that names an unregistered lever must raise at load, not
be silently ignored.

## 4. Reconciliation

- `docs/design-notes/evaluation-harness.md` §2.6 — *"Track L's L3 manifest (`config/tuning.toml`,
  `scripts/tune.py show/set/history/--revert, attested, fingerprinted`) is absorbed as the manifest
  layer over the same closed lever registry."* → **cross-reference-on-extension**: this plan builds
  exactly that layer over the *current* four-lever registry; no correction. The manifest fingerprint
  (`config_fingerprint`, note §2.1 = "sha256 of the resolved tuning manifest") is authored here as the
  canonical hash of the resolved manifest, which E3a-1's sweep will consume as its key component — a
  forward cross-reference recorded in §6, not a change to any built code.
- No committed code is corrected by this plan. `ops/levers.py`, `ops/selfmod.py`, `ops/ledger.py`,
  `config/loader.py` are **read-only dependencies**, not in `write_scope`.

## 5. Write scope

- `config/tuning.toml` — the per-lever manifest (new).
- `eval/harness/tuning.py` — the manifest model + loader + resolved-manifest fingerprint (new).
- `scripts/tune.py` — the CLI (new).
- `tests/unit/test_tuning_manifest.py`, `tests/integration/test_tune_cli.py` — tests (new).

**Deliberately OUT of scope** (read-only dependencies, guard denies writes): `ops/levers.py`
(no new lever), `ops/selfmod.py` / `ops/ledger.py` / `ops/apply.py` (the gate is reused, never
reimplemented), `config/loader.py`, `config/local.toml` / the overlay (the human's value channel),
and every foundation-denylist file. No `eval/golden/**`, no `baseline.json`.

## 6. Interfaces pinned inline

```python
# ops/levers.py — the registry this manifest overlays (verbatim)
@dataclass(frozen=True)
class Lever:
    name: str; section: str; key: str; kind: LeverKind; lo: float; hi: float; description: str = ""
    def validate(self, value: float) -> float | int: ...   # coerce + bounds-check, raises out-of-range
LEVERS: dict[str, Lever]              # name -> Lever; the 4 [dreaming] levers
def get_lever(name: str) -> Lever    # raises KeyError (fail-closed) on unknown name

@dataclass(frozen=True)
class ProposedChange:
    lever: str; target: float; rationale: str = ""
    def resolve(self) -> tuple[Lever, float | int]: ...    # validates bounds before the ledger

# ops/selfmod.py — the gate the CLI drives (verbatim signatures)
class SelfModLoop:                     # dataclass(config, ledger, validator, overlay_path=LEVERS_OVERLAY)
    def propose(self, change: ProposedChange, *, proposer: str = "") -> Proposal
    def approve(self, proposal_id: int, *, approver: str = "owner") -> Proposal
    def execute(self, proposal_id: int) -> Proposal                 # writes overlay, records prior, refresh_config
    def validate(self, proposal_id: int) -> Proposal                # gate → VALIDATED or rollback→ROLLED_BACK
    def execute_and_validate(self, proposal_id: int) -> Proposal
def build_loop(validator, *, config=None, ledger=None) -> SelfModLoop
def build_golden_validator(retriever, *, golden=None, frozen_baseline=None, rolling_baseline=None) -> Validator

# ops/ledger.py — history renders these (verbatim)
class LedgerStatus(StrEnum):  # proposed → approved → executed → validated | rolled_back ; proposed → denied
@dataclass(frozen=True)
class Proposal:
    id: int; lever: str; current_value: float; target_value: float; status: LedgerStatus
    rationale: str; proposer: str; approver: str | None; prior_overlay: float | None
    attestation_id: str | None   # ...plus proposed_at/decided_at/resolved_at timestamps
class ProposalLedger:
    def all(self) -> list[Proposal]; def pending(self) -> list[Proposal]
    def get(self, proposal_id: int) -> Proposal | None
def open_ledger(config) -> ProposalLedger
```

**The manifest schema authored by this plan** (note §2.6 — propose-mode subset; `auto`-mode fields
are E3b and MUST be absent/rejected here):

```toml
# config/tuning.toml — per-lever policy overlay on ops/levers.LEVERS. Subordinate to local.toml.
[tuning.dream_similarity_threshold]
subsystem = "dreaming"        # informational grouping
autonomy  = "propose"         # "propose" only in E3a (the DEFAULT + the value when the key is absent)
objective = "f9_composite"    # OPTIONAL: the default registry key this lever's sweeps optimize (note §2.6)
# range/default are DERIVED from ops/levers.Lever (lo/hi) — never re-declared here (single source of truth)
```

## 7. Items

### Item 15 — `eval/harness/tuning.py`: the manifest model + loader + resolved-manifest fingerprint

- **Objective:** parse `config/tuning.toml` into a validated `TuningManifest` over `ops.levers.LEVERS`;
  expose `resolved_fingerprint() -> str` (sha256 of the canonical resolved manifest, note §2.1).
- **Files:** `eval/harness/tuning.py`, `config/tuning.toml`.
- **Acceptance test:** `uv run pytest tests/unit/test_tuning_manifest.py -q` green: a manifest loads;
  a missing `autonomy` resolves to `"propose"`; a key naming an unregistered lever raises at load
  (fail-closed, Q1/Q-note backstop); `autonomy = "auto"` raises `NotImplementedError`/a clear
  "E3b" error (out of scope here); `resolved_fingerprint()` is stable across reorderings of the TOML
  and changes when a policy value changes.
- **Falsifier:** the fingerprint changes when only TOML key ORDER changes (not canonicalized), or a
  manifest that names a non-lever loads without raising (silent shadow surface).
- **Invariant(s):** the manifest carries POLICY only, never live lever values (range/default derived
  from `Lever`, §5); it is subordinate to `local.toml` (never a value source).
- **Touches stored data?** No (config + a pure loader).
- **Parallelizable?** No (Item 16 depends on it). **Depends on:** none.

### Item 16 — `scripts/tune.py`: `show` / `set` / `history` / `--revert` over the built §14 loop

- **Objective:** the attended CLI: `show` (levers + live values via `_section_value` + manifest
  policy), `set <lever> <value>` (→ `SelfModLoop.propose`; prints the proposal id and that it awaits
  owner approval — the CLI never auto-approves), `history` (`ProposalLedger.all()` rendered by
  status), `--revert <proposal_id>` (rollback an EXECUTED proposal via the loop; for a VALIDATED/
  terminal proposal, refuse the transition and offer to file the inverse proposal — Q2).
- **Files:** `scripts/tune.py`.
- **Acceptance test:** `uv run pytest tests/integration/test_tune_cli.py -q` green, driving the CLI
  against an in-memory `ProposalLedger` + a stub validator + a tmp overlay (the `test_selfmod.py`
  idiom): `set` yields a PROPOSED row (no auto-approve); `history` shows it; an owner-approved+
  executed proposal `--revert`s to ROLLED_BACK and restores the prior overlay; `set` with an
  out-of-bounds value raises before any ledger write (fail-closed, `ProposedChange.resolve`); `show`
  works with `[selfmod] enabled=false` (read-only, Q5).
- **Falsifier:** the CLI approves its own proposal (bypasses the human gate), OR `--revert` mutates a
  VALIDATED proposal's status (illegal transition), OR `set` writes the overlay before approval.
- **Invariant(s):** the model advises, code acts (the CLI is the *human's* hand; no model in the
  path); every apply transits §14; `[selfmod] enabled`/`unattended_enabled` are honored, never forced;
  attestation is recorded where the loop records it (the CLI adds no unattested apply path).
- **Touches stored data?** Yes — `set`/`--revert` write the machine overlay + the proposal ledger via
  the built loop. Require the test-driven dry path (in-memory ledger + tmp overlay) to prove the
  reversible write before any real invocation; the real overlay is only touched by an owner running
  the CLI, never by the builder.
- **Parallelizable?** No. **Depends on:** Item 15.

## 8. Math carried explicitly

N/A — no mathematical object implemented. (The manifest fingerprint is a canonicalization hash, not
a mathematical instrument; its correctness is the Item-15 stability test, not a field-guide entry.)

## 9. Non-goals

- No new lever (no `ops/levers.py` edit); registering `dream_rnd.sigma` or any knob is out of scope
  (that is the E3a-1 σ-fork, owner-gated).
- No `auto` autonomy mode, no `apply_unattended`, no derived `SAFE_LEVERS`, no cooldowns — **E3b**.
- No sweep, no curves, no `TuningProposal` emission — **E3a-1** (bp-046).
- No change to the gate, the ledger schema, `overlay_set`/`overlay_restore`, or the validator.

## 10. Stop-and-raise conditions

- If building `show`/`set` reveals that the manifest MUST carry live values to be useful (i.e. the
  policy/value separation cannot hold) — STOP and file a `design` finding (it contradicts the
  "subordinate to local.toml" pin); do not let the manifest shadow the human's value channel.
- If `--revert` semantics for a VALIDATED proposal prove ambiguous against the built state machine —
  STOP and file a `codebase` finding rather than inventing a transition.
- Any blessing (`proposed→ready`, `draft→ratified`) the builder would have to perform: it must not.

## 11. Parked decisions

| Decision | Default recorded | Rejected alternatives (why) | Re-entry condition |
|---|---|---|---|
| `auto` autonomy mode + fields | schema reserves `autonomy`; accepts only `"propose"` | build auto now (couples to E3b's unattended path + derived SAFE_LEVERS; note sequences E3b after propose-mode earns trust) | bp for E3b (note §3) |
| manifest `objective` per lever | optional key; unused by this plan | require it (E3a-1 consumes it; not this plan's job) | E3a-1 (bp-046) reads it |
| fingerprint canonicalization form | sorted-key JSON of resolved policy, sha256 | TOML-bytes hash (order-sensitive, brittle) | a consumer needs a different identity |

## 12. Dependency & ordering summary

- **Items:** 15 → 16 (16 depends on 15). Blast-radius order: Item 15 is a pure loader (read-only of
  the registry); Item 16 performs reversible writes (overlay + ledger) — correctly later.
- **Cross-plan:** `depends_on: []` — independent of E3a-1 (bp-046) and of the σ-lever fork.
  `parallelizable_with: [bp-048]` (E6) — disjoint `write_scope`. Feeds E3a-1: the resolved-manifest
  fingerprint (Item 15) is E3a-1's `config_fingerprint` component (note §2.1) — a forward
  cross-reference, not a dependency (E3a-1 can compute its own until this lands).
