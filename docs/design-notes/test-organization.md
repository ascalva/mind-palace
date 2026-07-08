---
type: design-note
id: dn-test-organization
status: draft
implementation: built-wired   # corpus-audit 2026-07 verification
created: 2026-06-27
updated: 2026-07-01
links: []
supersedes: null
superseded_by: null
warrant: null
---

# Design note — Test directory reorganization

*Family tag → cross-cutting: test-suite organization (by execution profile) for verifying all five families. See [`../NOTATION.md`](../NOTATION.md).*

**Status:** actionable now. Migrate the flat `tests/` directory into category
subdirectories driven by execution profile (speed, infrastructure, when-it-runs),
not subject alone. Pair with pytest markers for cross-cutting selection. This is a
mechanical refactor — no test logic changes, only location and markers.

---

## 0. Why reorganize

A flat `tests/` directory stops scaling when test categories diverge in *when and
why they run*: unit tests fire on every save; longitudinal tests run nightly; e2e
needs models pulled; integrity tests are a non-skippable gate. Organizing by
execution profile lets the developer and CI select the right suite for the moment.

The governing principle: **organize by execution profile, not just subject.** Two
tests can both exercise the firewall yet belong in different directories if one runs
in milliseconds with no infrastructure and the other needs the attestation layer.

---

## 1. Target structure

```
tests/
├── conftest.py              # root fixtures + marker registration
├── fixtures/                # shared fixtures, synthetic corpus generators
│   ├── corpus.py            # synthetic_corpus() Hypothesis strategies
│   ├── stores.py            # ephemeral store fixtures (tmp LanceDB/DuckDB/SQLite)
│   └── attestation.py       # attestation chain fixtures
├── unit/                    # fast, isolated, no I/O
│   ├── test_constitution.py
│   ├── test_provenance.py
│   ├── test_recursion.py    # depth/acyclicity logic
│   └── …
├── integration/             # component pairs, real local stores, no network
│   ├── test_ingest_to_vectorstore.py
│   ├── test_dreamer_derivedstore.py
│   └── …
├── e2e/                     # full pipeline, slow, may need models
│   ├── test_note_to_dream.py
│   ├── test_research_airlock_flow.py
│   └── …
├── property/                # Hypothesis — invariants over generated inputs
│   ├── test_grounding_property.py      # I9
│   ├── test_recursion_decay_property.py # I10
│   ├── test_firewall_property.py        # I6
│   └── test_authority_property.py       # I13
├── metamorphic/             # input/output relationships, no ground truth
│   ├── test_topic_strengthening.py
│   ├── test_deletion_propagation.py
│   ├── test_ingest_idempotency.py
│   └── test_order_independence.py
├── adversarial/             # red-team: violate invariants through interfaces
│   ├── test_prompt_injection.py
│   ├── test_derivation_cycle.py
│   ├── test_pii_scrubber.py
│   └── test_vault_scope.py
├── integrity/               # firewall/provenance/attestation — the CI gate
│   ├── test_firewall_structural.py
│   ├── test_provenance_separation.py
│   ├── test_attestation_chain.py
│   └── test_import_lint.py   # core cannot reach network
├── emergent/                # multi-component, concurrent, cross-invariant
│   ├── test_firewall_under_composition.py
│   ├── test_confidence_non_inflation.py
│   └── test_reset_from_raw_clean.py
└── longitudinal/            # slow drift, scheduled — NOT in standard CI
    ├── test_alignment_drift.py
    ├── test_grounding_over_time.py
    └── test_attestation_durability.py
```

---

## 2. Execution profile matrix

| Suite | Speed | Infra needed | Runs when |
|-------|-------|-------------|-----------|
| `unit/` | ms | none | every file save |
| `integration/` | seconds | local stores | every commit |
| `property/` | seconds–min | local stores | every commit |
| `metamorphic/` | seconds | local stores | every commit |
| `adversarial/` | seconds | local stores | every commit |
| `integrity/` | seconds | stores + attestation | **every commit (required gate)** |
| `e2e/` | minutes | full stack, models | pre-merge |
| `emergent/` | minutes | full stack, concurrent | pre-merge |
| `longitudinal/` | hours | running system | scheduled (nightly/weekly) |

---

## 3. Markers (pyproject.toml)

```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
markers = [
    "unit: fast isolated tests",
    "integration: component-pair tests with real stores",
    "e2e: full-pipeline tests",
    "property: Hypothesis property-based tests",
    "metamorphic: input/output relationship tests",
    "adversarial: red-team invariant-violation attempts",
    "integrity: firewall/provenance/attestation tests (CI gate)",
    "emergent: multi-component concurrent tests",
    "longitudinal: slow drift tests, scheduled only",
    "slow: takes >10s",
    "needs_models: requires Ollama models pulled",
    "needs_network: requires network (edge/cloud only — never core)",
]
# longitudinal excluded from default runs; opt in explicitly
addopts = "-m 'not longitudinal'"
```

Apply markers at the directory level via `conftest.py` in each subdir, so every
test in `adversarial/` is automatically marked `adversarial` without per-file
decoration:

```python
# tests/adversarial/conftest.py
import pytest
def pytest_collection_modifyitems(items):
    for item in items:
        item.add_marker(pytest.mark.adversarial)
```

---

## 4. Developer workflows

```bash
# Tight inner loop — every save
pytest tests/unit

# Pre-commit — everything fast, no models
pytest -m "not slow and not needs_models and not longitudinal"

# The critical gate — invariants that must never break
pytest -m integrity

# Pre-merge — full validation including slow + models
pytest -m "not longitudinal"

# Nightly — the slow drift suite, separately
pytest tests/longitudinal -m longitudinal

# One category across the whole tree
pytest -m adversarial
```

---

## 5. CI stages

| Stage | Command | Blocks merge? |
|-------|---------|--------------|
| Lint + import-firewall | `pytest -m integrity tests/integrity/test_import_lint.py` | YES |
| Fast suite | `pytest -m "not slow and not needs_models and not longitudinal"` | YES |
| Integrity gate | `pytest -m integrity` | YES — non-skippable |
| Full suite | `pytest -m "not longitudinal"` (with models) | YES |
| Longitudinal | `pytest tests/longitudinal` | NO — scheduled, reports only |

**The `integrity/` suite is the required, non-skippable gate.** It is where the
firewall, provenance separation, and attestation validity live — the invariants
that, if broken, mean the system has violated its core promises. Everything else
verifies correctness; `integrity/` verifies the constitution holds. A failure here
blocks merge unconditionally and is never marked xfail or skipped.

---

## 6. Migration steps (mechanical, no logic changes)

1. Create the subdirectories + a `conftest.py` in each that applies its marker.
2. Move existing test files into the matching subdir. Most current tests are `unit/`
   or `integration/`; sort them by what they actually touch.
3. Extract shared fixtures into `tests/fixtures/`; update imports.
4. Register markers in `pyproject.toml`; add `addopts` to exclude longitudinal by
   default.
5. Update CI to the staged commands in §5.
6. Run the full suite once to confirm nothing broke in the move (same count, same
   pass/fail as before — this is a pure refactor).
7. Going forward: new tests land in the directory matching their execution profile;
   the holistic-testing.md categories (metamorphic, adversarial, emergent,
   attestation-as-oracle, longitudinal) now have homes.

---

## 7. Relationship to holistic-testing.md

This structure is the home for the test categories defined in `holistic-testing.md`:
- metamorphic → `metamorphic/`
- adversarial → `adversarial/`
- emergent behavior → `emergent/`
- attestation-as-oracle → `integrity/` (chain validity) + `e2e/` (full-run oracle)
- longitudinal → `longitudinal/`
- property-based (I6/I9/I10/I13) → `property/`

The two notes are complementary: `holistic-testing.md` defines *what* the tests
assert; this note defines *where* they live and *when* they run.
