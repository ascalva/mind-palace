---
type: finding
id: finding-0110
status: resolved
created: 2026-07-19
updated: 2026-07-19
links:
  - .github/workflows/ci.yml
  - ops/lifecycle/launcher.py
  - docs/findings/finding-0105.md
  - pyproject.toml
ftype: discovery
origin_plan: orchestrator
route: orchestrator
resolution: FIXED 2026-07-19 (session-30) — five commits (c5d8bbf..5943622 relevant: c9171d4 + 5943622); CI green for HEAD 5943622, ci-witness attests, `palace deploy` unblocked.
---

# The remote CI has been silently red for ~4 sessions; the deploy's ci-witness half was never green

## What
`palace deploy` (owner-run, 2026-07-19) refused at the **ci-witness** step: "no attested green
pipeline for HEAD." The **local** gate (`gate_cmd` pytest) passed — finding-0105 taught it to
deselect the one intentional-red ratchet — but the deploy ALSO runs `ci_check_cmd` (ci-witness),
which requires the **remote** GitHub Actions pipeline to be green for HEAD. It was not, and had not
been since ~session-26 (every `ci.yml` run back through bp-066 shows `failure`). None of it was a
bp-069 regression — bp-069's deploy merely surfaced long-standing rot. Four independent pre-existing
breaks, plus the structural one:

1. **ratchet job / ruff** — 4 `E501`s from finding-0105's `gate_cmd` (an unsplittable pytest node-id
   string + long comments). `ruff check .` is stricter than the pytest-only local gate.
2. **type-gate / mypy count** — finding-0105's `gate_cmd` test read `Launcher.__dataclass_fields__
   [...].default` (typed `Any | _MISSING_TYPE`) → 3 errors over the pinned 69 baseline (72 ≠ 69).
3. **type-gate / membership** — **bp-067** (finding-0103) made `config/loader.py` a core-importing
   facade but never re-classified `config` from Tier-3 (bp-007's "zero core imports" measurement,
   since invalidated). The type-gate membership invariant flagged `config` as a core-importer absent
   from `[tool.mypy].files`. Masked because the count check `exit 1`s BEFORE `ops.type_gate` runs.
4. **gitleaks** — 3 `generic-api-key` flags on the secret-GUARD test fixtures (fake sequential
   dummies that EXERCISE the scanner, bp-063). No `.gitleaks.toml` existed.
5. **ratchet job / pytest (STRUCTURAL)** — the CI ratchet job runs the full model-free tier WITHOUT
   the deploy gate's `--deselect`, so `test_core_imports_nothing_outside_core` (red-by-design under
   finding-0103) kept the job red. **finding-0105 fixed only the LOCAL gate half; the CI half it did
   not consider.**

## Why it matters
The deploy gate has TWO independent halves — local pytest AND remote ci-witness — and only the local
half was being watched. Resume briefs asserted "CI witness can attest HEAD" for multiple sessions
WITHOUT verifying it; the assertion was false the whole time. A red CI also silences its real signal:
a genuine ruff/type/secret regression would have been invisible under the noise.

## Resolution
- 1,2,3,4 fixed surgically (commit `c9171d4`): ruff comment-shortening + `# noqa` the node-id string;
  `cast` the `.default` read → 69; promote `config` to Tier-2 (add to `[tool.mypy].files`, drop from
  the silent-follow override, `hvac.*` → `ignore_missing_imports`, type `build_secrets_backend`);
  a narrow `.gitleaks.toml` allowlist scoped to the two secret-guard test files (default rules else
  unchanged).
- 5 fixed (commit `5943622`): **owner decision (2026-07-19) — extend finding-0105 decision-A to the
  CI surface**: the CI ratchet job now mirrors the local gate's surgical `--deselect`. CI enforces
  everything else; the test stays red in the dev full-suite (the forcing function holds); a real
  scanner/import regression still blocks CI; the deselect vanishes automatically at ratchet-0.
- **Verified:** all 5 CI jobs green for HEAD `5943622`; `ci_witness.py check` exits 0 (attested).
  `palace deploy` (owner-run) is now genuinely unblocked.

## Process lesson (for the resume-brief discipline)
Before a resume brief claims CI is "attestable/green," VERIFY it (`gh run list --workflow=ci.yml` or
`ci_witness.py check <HEAD>`). "Pushed" ≠ "green." The deploy is gated on the REMOTE pipeline, not the
local suite; a green local gate says nothing about ci-witness. finding-0103's cleanup (19→0) remains
the path to restoring full ratchet strength on both surfaces.

## Routing
`direction` (deploy-gate / CI policy) → orchestrator → owner. The owner decided the one policy fork
(extend decision-A to CI); the rest were mechanical repairs. Resolved same session.
