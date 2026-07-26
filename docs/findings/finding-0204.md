---
type: finding
id: finding-0204
status: resolved
created: 2026-07-25
updated: 2026-07-25   # /triage session-49: DISCHARGED by bp-115
links:
  - docs/build-plans/bp-115/plan.md                    # §5 write_scope vs §7 Items 1 and 3
  - core/models/ollama_client.py                       # needs `healthy()` — NOT in write_scope
  - ops/import_lint.py                                 # NETWORK_ALLOWLIST — NOT in write_scope
  - core/models/llama_server_client.py                 # the second audited loopback client
  - docs/findings/finding-0191.md                      # write_scope is not a partition of the diff
  - docs/findings/finding-0177.md                      # the same shape, one wave earlier
ftype: spec-defect
origin_plan: bp-115
route: builder
resolution: |
  DISCHARGED by bp-115 (`909a6bf`), via the remedy this finding itself prescribed.
  The owner granted the widening verbatim -- "i grant you, the orchestrator, to make the edits
  to the write scope of bp-115" -- and `b44376d` amended §5 (+core/models/ollama_client.py,
  +ops/import_lint.py, +tests/e2e/test_ollama_live.py) with each addition's reason recorded.
  Both patches then landed UNDER THE PLAN, which is the re-entry through the artifact chain
  finding-0191 requires: a finding whose resolution is a code change is never discharged by a
  bare orchestrator commit. `healthy()` is an ADDED method (Item 1's falsifier did not fire);
  `llama_server_client.py` is now enrolled in NETWORK_ALLOWLIST on the record, and the import
  firewall reports it as an audited loopback exception.
  ⚑ The THIRD instance of finding-0191's pattern this wave (with 0177, 0191). The systemic fix
  is the graduate skill's new acceptance-reachability check (`e7915c2`, owner-approved): every
  §7 criterion must be buildable from §5, checked BEFORE the blessing where it costs one line.
---

# bp-115's `write_scope` omits the two files its own §7 acceptance requires

## What

bp-115 §6 pins `InferenceClient` with three members and states that `healthy()` "is the one
addition" to `OllamaClient`'s existing surface; §7 Item 1's acceptance is *"mypy accepts
`OllamaClient` where `InferenceClient` is required, with no change to any `OllamaClient` method
body; `healthy()` is the only added method."* §7 Item 3 requires a second client speaking
loopback HTTP with **stdlib `urllib`** (§3 Q5, quoting the note verbatim).

Both are unreachable from the plan's `write_scope`, and both were confirmed by running the gate,
not inferred:

**(a) `core/models/ollama_client.py` — `healthy()` has no home.**

```
$ uv run mypy core agents eval ops scheduler scripts
core/models/inference.py:89: error: Incompatible return value type (got "OllamaClient",
    expected "InferenceClient")  [return-value]
core/models/inference.py:89: note: "OllamaClient" is missing following "InferenceClient"
    protocol member:
core/models/inference.py:89: note:     healthy
core/models/server.py:63: error: Argument "client" to "ModelServer" has incompatible type
    "OllamaClient"; expected "InferenceClient"  [arg-type]
Found 2 errors in 2 files (checked 257 source files)
```

`healthy()` is a *protocol member*, so structural conformance requires it on the class. There is
no in-scope substitute: a `Protocol` default body is only inherited by an explicit subclass, and
`OllamaClient` conforms structurally; a subclass or wrapper would build the second facade §2
forbids AND would still fail the acceptance as literally worded ("mypy accepts **`OllamaClient`**
where `InferenceClient` is required"). Splitting the protocol into narrower ones so the widening
type-checks without `healthy()` would contradict the §6 pin and §11's parked decision
(*"`healthy()` on the protocol — yes, both backends need it; re-entry: never"*).

**(b) `ops/import_lint.py` — the new client is not on the audited allowlist.**

```
$ uv run python scripts/check_imports.py
Import firewall (I2) VIOLATIONS — sealed core must not reach the network:
  core/models/llama_server_client.py:37: imports 'urllib.error' (network firewall)
  core/models/llama_server_client.py:38: imports 'urllib.request' (network firewall)
EXIT=1
```

`NETWORK_ALLOWLIST` (`ops/import_lint.py:54-57`) is the audited two-file exception. A third
loopback client is exactly the kind of addition it exists to make *deliberate* — which is why the
right response is to extend it on the record rather than to evade the scan. Two integrity tests
consume the same list and go red with it (`tests/integrity/test_import_firewall.py`:
`test_core_has_no_forbidden_imports` and `test_allowlist_files_exist_and_are_the_only_network_importers`,
the latter asserting the allowlist is *exactly* the set of network-importing core files, so a
stale or missing entry fails in both directions).

Neither file appears in §5's ⚑ *"Deliberately OUT of scope, each for a stated reason"* list —
which does name `core/models/loader.py`, the launcher, preflight, `watch.py` and the golden set.
This is an omission, not an exclusion.

## Why it matters

The gap is not cosmetic: it is load-bearing for three of the plan's four items. Item 1's stated
acceptance cannot be satisfied; Item 2's widening (`Embedder.client`, `ModelServer.client`) does
not type-check without (a); Item 4's factory returns `InferenceClient` and inherits the same
error. Item 3's client cannot pass a green gate without (b). A P1 whose whole claim is *"nothing
observable changes"* must land green, or the reversibility story it exists to establish is
unproven.

It is also the third instance of finding-0191's pattern in this wave — `write_scope` drawn from
the *narrative* of a change rather than from its *closure*. The closure of "add a protocol member"
includes every class that must satisfy it; the closure of "add a networked client to core"
includes the firewall that audits it. Both are mechanically derivable from the plan text at
graduation: §6 says `healthy()` is added to a class the plan never lists, and §3 Q5 says the new
file imports `urllib` while `ops/import_lint.py` names every core file allowed to.

⚑ finding-0191's caution applies to the *remedy*, not just the defect: a hand-off finding
carrying a code patch must not be discharged by a bare orchestrator commit. The exact changes are
given below so the amendment is mechanical, but they should land under an amended `write_scope`
(bp-115 re-entered, or bp-116 which already owns `ops/lifecycle/` and the manager), not as
ungoverned lines.

## The exact change required (three lines, two files)

`core/models/ollama_client.py` — an ADDED method; no existing body is touched, so Item 1's
falsifier does not fire:

```python
    def healthy(self) -> bool:
        """Up and serving. Ollama has no readiness transition to express (a loaded model is
        served or the request blocks), so a non-empty version string IS its liveness signal;
        llama-server's form is /health 503->200. See core/models/inference.py."""
        return bool(self.version())
```

`ops/import_lint.py` — one allowlist entry plus the docstring count (`:19-23` says "the two
audited loopback/seal modules"):

```python
NETWORK_ALLOWLIST: frozenset[str] = frozenset({
    "core/sealing.py",                       # wraps socket to seal it
    "core/models/ollama_client.py",          # loopback Ollama IPC channel (127.0.0.1)
    "core/models/llama_server_client.py",    # loopback llama-server channel (127.0.0.1)
})
```

The second entry is a genuine widening of the audited exception and deserves the sentence the
existing two get. The client binds a `127.0.0.1` LITERAL (never a hostname, so no DNS), never
spawns a process, and holds no download capability — `dn-local-model-runtime` §2.4 keeps the seal
boundary exactly where Ollama already puts it.

## Re-entry condition

bp-115 Items 1, 2 and 4 are **built but not green**, parked on this finding alone. They re-enter
the moment `core/models/ollama_client.py` and `ops/import_lint.py` are writable under a plan and
the three lines above land; the gate is expected green at that point with no further code change
(everything else in the plan's `write_scope` is complete and committed). Item 3 is complete and
independently correct — only the firewall entry is owed.

## Routing

`spec-fidelity` → the builder resolves. The builder **cannot** here: the resolution is entirely
outside the plan's `write_scope`, and routing around a scope denial is forbidden. Filed instead,
with the patch stated exactly, for the orchestrator to bring under a plan.
