# bp-019 journal

## 2026-07-12 — Item 5 complete: `AgentObservationStore`

Wrote `core/stores/agent_observations.py` mirroring `code_observations.py` exactly per
§6(a,b): `AgentObservation` (commit_sha, stream, subject_id, key, payload — no provenance
field), `AgentObservationStore.add_batch`/`is_projected`/`mark_projected`/`all_rows`/
`rows_for`/`count`/`chain_for`, module-local `batch_content_hash` sorted on
`(commit_sha, stream, subject_id, key)`, `open_agent_observation_store()` →
`data/agent_observations.sqlite`.

**finding-0057 filed (spec-fidelity, routed to builder/self, resolved in-session):**
`core/stores/observation_history.py`'s `IDENTITY_KEYS` dict lacks an `"agent"` entry (the
file's own comments at `:13,48,62` say bp-019 registers it, but bp-019's write_scope never
granted that file — confirmed DENY via `scope-guard.sh --standalone`). Resolution: did NOT
touch the out-of-scope file; `tests/unit/test_agent_observations.py` registers
`IDENTITY_KEYS["agent"]` via an autouse `monkeypatch` fixture so the supersession/chain
tests exercise the REAL `ObservationHistoryStore.archive()`/`chain()` code paths end-to-end.
Flagged for the orchestrator: a tiny follow-up (or an amendment to this plan's write_scope)
should land the real one-line dict entry in the shipped file before bp-020's backfill
depends on it for real.

Wrote `tests/unit/test_agent_observations.py` (13 tests, mirroring
`test_code_observations.py`'s shape): idempotence, bumped-interpreter archive+chain,
missing-history raise, same-interpreter-readd never touches history, the no-provenance-
parameter sweep (Item 5's named falsifier), observed-minting, ObservedView admits /
MirrorView refuses (§2.6), projection-mark idempotence, batch-hash determinism, open-helper.

Gate: `uv run pytest -q tests/unit/test_agent_observations.py` → **13 passed**. (Needed
`uv sync --extra dev` first — pytest is an optional dev dep, not in the base env by
default in this worktree; a one-time setup step, not a finding.)

Next: Item 6, the `AgentSensingHandoff` sibling appended to `core/sensing.py` + its
transport tests.

## 2026-07-12 — build session start (builder)

Status flipped `ready → in-progress` (mine to do; the two blessing gates —
`draft→ratified`, `proposed→ready` — are owner-only and untouched). Worktree-local
`.claude/state/active-plan` = `bp-019`. Read CLAUDE.md, plan.md in full, checkpoint/
commit/finding skills, and every §2 context-manifest file: `code_observations.py`
(mold, full), `core/sensing.py` (whole file, sibling banner `:285-292`,
`CodeSensingHandoff` `:297-349`), `ops/code_sensor.py` (sensor mold, `_project`
`:212-237`), `observation_history.py` (sidecar, `IDENTITY_KEYS` already has the
bp-019 comment at `:64` — `'agent'` not yet registered, that's mine to add),
`.githooks/post-commit`, `launcher.py:496-529` (`reset_targets()`), build-plan
template + skill, bp-011 plan (cost block fixture). Also read: `core/provenance.py`
(Provenance enum, MIRROR_READABLE), `core/attestation/attestor.py` (`Attestor.emit`
signature matches plan §6(d) verbatim), `scripts/snapshot_code.py` (driver-script
mold), existing test files `test_code_observations.py` / `test_sensing_transport.py`
/ `test_interpreter_versions.py` (the exact test-shape mold). No manifest gaps found
— everything needed was either in §2 or one hop from it (attestor/provenance, which
the mold files already import).

finding IDs start at finding-0057 (0052-0056 reserved for bp-022, parallel/disjoint).

Next: Item 5, `core/stores/agent_observations.py` + its test suite, mirroring
`code_observations.py` exactly per §6(a,b).

## 2026-07-12 — minted at graduation (orchestrator, Fable/xhigh)

Plan created `proposed` by /graduate over the ratified `dn-self-sensing` (B-b: store +
seam sibling + φ_self over the cost stream). Grounding verified in-session: the
sibling-precedent banner (`core/sensing.py:285-292`), the no-outbound-half reasoning
(`:306-312`), the post-commit hook wiring (`.githooks/post-commit`, `core.hooksPath`),
V4's SQLite confirmation (`CONVENTIONS.md:15-18`), V3's parse feasibility (4 pairs, 3
estimate-only, 11 pre-rule). First-parent diff grain pinned (§6(e)); v1 payload
worldview recorded (§6(f)). No code written. Awaiting the owner's `proposed → ready`
hand edit; depends on bp-018.
