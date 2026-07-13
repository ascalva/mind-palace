---
type: finding
id: finding-0048
status: resolved         # open → routed → resolved | promoted
created: 2026-07-12
updated: 2026-07-12
links:
  - docs/findings/finding-0046.md
  - tests/e2e/test_dream_v2_live.py
ftype: discovery
origin_plan: bp-018
route: builder           # codebase concern: flake evidenced, re-run green, annotated
resolution: >
  Re-run in isolation green (2 passed, 437s). Same environmental class as
  finding-0046 (live-model resource contention in a full-suite run), not the
  bp-018 diff — nothing in the plan touches the dream/embed path and the
  observation stratum has no consumer. Recommend the orchestrator fold this
  test into finding-0046's known-flake note so future gate runs re-run it
  before investigating.
---

# A second live e2e flake under full-suite load: dream_v2 embeds die in the Ollama HTTP call

## What

During bp-018's verbatim gate (`uv run pytest -q`, full suite), BOTH live e2e tests
failed: the documented finding-0046 flake
(`test_scheduler_live.py::test_supervisor_dispatches_a_real_job`, DONE + empty text)
AND `test_dream_v2_live.py::test_dream_v2_synthesizes_grounded_themes_live` — the
latter not documented as a known flake. Its failure is environmental, not assertive:
`core/models/ollama_client.py:48 _post("/api/embed")` dies inside
`urllib.request.urlopen → http.client.getresponse` while indexing the fixture corpus
(gate log: scratchpad `gate2.log`, full-suite tail `2 failed, 867 passed, 8 skipped in
569.72s`). An immediate re-run of both tests in isolation: `2 passed in 437.81s`.

## Why it matters

Gate reliability: a builder who doesn't know this class will burn a session
investigating a diff-unrelated failure. finding-0046 documents the scheduler test's
async-unload race; this shows the CLASS is wider — under full-suite load (two live
model tests, model load/unload against the ~2-resident-model memory ceiling), the
local Ollama endpoint can drop/starve an HTTP response mid-run.

## Re-entry condition

None parked — bp-018 proceeds (gate green with the documented re-run). Reopens if the
test fails twice consecutively in isolation (then it is not contention, and the
embed-path timeout/retry posture deserves a real look).

## Routing

`discovery`, codebase concern → builder resolved by evidence + annotation (this file,
journal, FINISH report); orchestrator may fold into finding-0046's known-flake note.
