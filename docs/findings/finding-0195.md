---
type: finding
id: finding-0195
status: open
created: 2026-07-25
updated: 2026-07-25
links:
  - docs/audits/ops-wave-2026-07-25.md
  - ops/lifecycle/launcher.py
  - core/models/ollama_client.py
ftype: spec-defect
origin_plan: orchestrator
route: builder
resolution: null
---

# `status` can block up to 120 s on a hung Ollama — uncosted, untested, in the tool built to diagnose that exact failure

## What
`_embedder_state` (`launcher.py:958-975`) calls `OllamaClient.ps()`, which does a
synchronous `urlopen(..., timeout=request_timeout_s)` (`ollama_client.py:59-67`) with
`request_timeout_s` defaulting to 120. bp-102's Item-2 falsifier bounds STORE and QUEUE
cost; nothing bounds this network round trip. The gate is `preflight_ok`, which only proves
Ollama answered once. Every test stubs `_embedder_state`, so the path is never exercised.

## Why it matters
The incident this entire wave exists for was an Ollama socket timeout. The diagnostic tool
will therefore hang in precisely the failure mode it was built to diagnose — for two
minutes, with no output, at the moment the operator most needs it.

`except Exception` correctly catches the `TimeoutError` that finding-0178 discovered escapes
`URLError` — but only AFTER the wait. Generalizable rule for the seal gate: when a plan's
falsifier is "cost", enumerate EVERY I/O path the diff adds (SQL, store, network,
filesystem) and confirm each has a bound and a test. bp-102 bounded two of three.
