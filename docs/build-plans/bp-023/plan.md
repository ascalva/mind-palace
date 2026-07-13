---
type: build-plan
id: bp-023
status: ready
design_ref:
  - docs/findings/finding-0046.md # findings-driven test-infra hardening — no design-note graduation (see §0)
contract: builder
write_scope:
  - "tests/e2e/conftest.py"        # the auto-applied cross-process live lock fixture
  - "tests/**/conftest.py"         # only if grounding shows the `live` marker is applied elsewhere (§3 Q2)
  - "docs/build-plans/bp-023/**"
  - "docs/findings/**"
session_budget: 1
cost:
  estimate: { model: sonnet, tokens: 80k } # one fixture + a two-process contention proof
  actual: null
depends_on: []
parallelizable_with: []
created: 2026-07-12
updated: 2026-07-12
links:
  - docs/findings/finding-0046.md # scheduler live flake — async-unload race under contention
  - docs/findings/finding-0048.md # dream_v2 live flake — same load class (folded here)
  - docs/build-plans/bp-018/journal.md # research_live + semantic_search_live — the third+ members, cross-suite overlap
re_entry: null
supersedes: null
superseded_by: null
warrant: finding-0046
---

# Build Plan — serialize the live test axis across processes (the flake class's real cause)

> **Every section below is required.** N/A is an accountability act.

## 0. Mode & provenance

Triage-promoted (third /triage, 2026-07-12), NOT a design-note graduation: the
live-flake class (finding-0046 + finding-0048 + the bp-018 journal's research_live /
semantic_search_live evidence) is a test-infra defect, not a design question, so the
fable pre-ruling minted it directly as a plan with the finding as `warrant`. Investigation
and planning produced this; implementation proceeds item-by-item on owner approval.
`proposed → ready` is the owner's hand edit.

## 1. Objective

Live-marked tests hold an OS-level, endpoint-keyed lock for their duration so that no two
live tests — **across separate pytest processes** (two builder suites, or a builder suite
overlapping the orchestrator's gate) — ever hit the single local Ollama endpoint
concurrently, removing the resource-contention race that produces the DONE-empty-text /
mid-embed-HTTP-death flakes.

## 2. Context manifest

1. `docs/findings/finding-0046.md` — the scheduler flake's observed mechanism (async
   unload race) and the "re-run before investigating" workaround it documents.
2. `docs/findings/finding-0048.md` — the dream_v2 flake; establishes the class is wider
   than one test (full-suite load starves the endpoint).
3. `docs/build-plans/bp-018/journal.md` (tail) — research_live + semantic_search_live
   failing when a builder suite overlapped bp-022's gate suite for 18 min: the proof the
   contention is **cross-process**, which an in-process lock cannot fix.
4. `tests/conftest.py` + `tests/e2e/conftest.py` — the marker plumbing the fixture hangs
   off; `pyproject.toml:55-68` — the `live` capability marker registration.
5. `core/models/ollama_client.py` — the endpoint the lock key is derived from (base URL).

## 3. Investigation & grounding

- **Q1 — is the contention truly cross-process (so an in-process lock is insufficient)?**
  YES — bp-018's journal records research_live + semantic_search_live failing precisely
  when a *separate* builder suite overlapped the orchestrator's gate suite. Two OS
  processes sharing one Ollama endpoint is the failure geometry; a `threading.Lock` or a
  pytest-xdist in-process guard cannot serialize across unrelated processes. Only an
  OS-level primitive (an advisory file lock) does.
- **Q2 — where is the `live` marker applied at HEAD?** The builder greps
  `pytest.mark.live` before writing: the `live` marker is a *capability* marker
  (`pyproject.toml:68`), applied per-test (not by directory — `tests/e2e/conftest.py`
  applies only the `e2e` directory marker). The lock fixture must trigger on the `live`
  marker specifically (an autouse fixture that no-ops for items lacking it), so a live
  test in any directory is covered and a non-live e2e test pays nothing.
- **Q3 — is `filelock` available?** NO — not importable, absent from `pyproject.toml`
  (verified 2026-07-12). Default: stdlib `fcntl.flock` on a lockfile in the system temp
  dir keyed to the endpoint — no new dependency, and both CI (Linux) and the dev box
  (darwin) are POSIX. `filelock` recorded as the rejected alternative (§11).
- **Q4 — deadlock / stale-lock risk?** An `fcntl.flock` advisory lock is released
  automatically when the holding process exits (even on crash — the kernel drops it), so
  a killed builder cannot wedge the lock. The fixture acquires in setup, releases in
  teardown (context-managed), blocking-with-timeout so a genuinely hung holder surfaces as
  a test error, not an infinite hang.

**Additional risks surfaced during reading:** the lock *serializes* live tests, lengthening
wall-clock when two suites run live tests at once (acceptable — correctness over speed for
the end-to-end tier; the alternative is the current flake tax). The lock must NOT be held
across the whole session (that would serialize collection/non-live work too) — it is
per-live-test, acquired at each live test's setup.

## 4. Reconciliation

- `docs/findings/finding-0046.md` — its "re-run before investigating" workaround is a
  *mitigation*, not a fix. **[cross-ref: extension]**: this plan supplies the structural
  fix; on merge+seal the finding flips `→ promoted` and its re-run advice becomes the
  documented fallback for the residual (a genuinely hung endpoint), not the routine path.
- `docs/findings/finding-0048.md` — recommends folding into 0046's known-flake note.
  **[cross-ref]**: superseded by this structural fix; folded into 0046 at this triage and
  promoted alongside it.

## 5. Write scope

In: `tests/e2e/conftest.py` (the autouse endpoint-keyed lock fixture), any other
`tests/**/conftest.py` the §3-Q2 grep shows owns the `live`-marked items, own plan dir,
findings. Out, deliberately: ALL non-test code (the endpoint client is read for its base
URL only, not edited); `pyproject.toml` (no dependency added — stdlib `fcntl`); design
notes; the foundation denylist.

## 6. Interfaces pinned inline

**(a) The lock fixture (autouse, `live`-triggered):**

```python
# tests/e2e/conftest.py — autouse; no-ops unless the item carries the `live` marker.
import fcntl, hashlib, tempfile
from pathlib import Path
import pytest

@pytest.fixture(autouse=True)
def _serialize_live_axis(request):
    if request.node.get_closest_marker("live") is None:
        yield
        return
    # Key the lock to the Ollama endpoint so distinct endpoints don't serialize needlessly.
    endpoint = <the base URL from core/models/ollama_client — grounded at HEAD>
    key = hashlib.sha256(endpoint.encode()).hexdigest()[:16]
    lockfile = Path(tempfile.gettempdir()) / f"mp-live-ollama-{key}.lock"
    with open(lockfile, "w") as fh:
        fcntl.flock(fh, fcntl.LOCK_EX)   # blocks until the other process releases
        try:
            yield
        finally:
            fcntl.flock(fh, fcntl.LOCK_UN)
```

(The endpoint expression is grounded at HEAD by the builder — do not hardcode a guessed
URL. If the client exposes no importable base-URL constant, key the lock to a fixed
sentinel string `"ollama-local"` and note it.)

**(b) The contention proof (Item 13's acceptance):** two pytest processes launched
concurrently, each running the same live test, must both pass and their endpoint-touch
windows must not overlap — demonstrated by a timing log or by both passing where the
pre-fix baseline flakes. A stdlib-only harness (two `subprocess.Popen` of
`uv run pytest -m live -k <one test>`) suffices; it lives in the journal, not the suite
(it needs a live endpoint and is itself slow).

## 7. Items

_(numbering continues the global sequence; this plan family starts at 12)_

### Item 12 — the endpoint-keyed live lock fixture

- **Objective:** add §6(a) so every `live`-marked test acquires the cross-process lock for
  its duration; non-live tests are untouched (the autouse fixture no-ops).
- **Files:** `tests/e2e/conftest.py` (and any conftest §3-Q2 shows owns live items)
- **Acceptance test:** `uv run pytest -q -m "not live"` unchanged (fixture no-ops off the
  marker); a single `uv run pytest -m live -k <one live test>` passes (lock acquired and
  released, no hang); `grep -n flock tests/e2e/conftest.py` shows LOCK_EX + LOCK_UN.
- **Falsifier:** the fixture acquires the lock for non-live tests (serializing the fast
  tier — the autouse guard's marker check is wrong), or a killed process leaves the lock
  held (it must not — `flock` is auto-released on process exit; prove by killing mid-hold
  and re-running).
- **Invariant(s):** no non-test code edited; no new dependency in `pyproject.toml`; the
  fast (`not live`) suite's wall-clock is not regressed.
- **Touches stored data?** no
- **Parallelizable?** yes **Depends on:** none

### Item 13 — the cross-process contention proof

- **Objective:** demonstrate the lock actually serializes two *separate* pytest processes
  against the endpoint (the property finding-0046/0048's re-runs only worked around).
- **Files:** `docs/build-plans/bp-023/journal.md` (the two-process run log)
- **Acceptance test:** §6(b) — two concurrent `uv run pytest -m live -k <test>` processes
  both pass; the journal records that pre-fix this combination flakes and post-fix it does
  not (or that the endpoint windows are provably disjoint).
- **Falsifier:** both processes enter the endpoint concurrently despite the lock (the lock
  key differs between processes, or the lockfile path is process-local) — the fix is inert.
- **Invariant(s):** the proof uses a real live endpoint (it is the whole point); it lives
  in the journal, never added to the collected suite.
- **Touches stored data?** no
- **Parallelizable?** no **Depends on:** Item 12

## 8. Math carried explicitly

N/A — no mathematical object; a mutual-exclusion lock, not a modeled quantity.

## 9. Non-goals

Fixing the *root* Ollama behavior (empty-content-on-mid-swap is upstream; the lock avoids
provoking it, does not patch it); removing the live tier or any live test; pytest-xdist
adoption; any retry/backoff logic inside the tests (the lock removes the need); touching
non-test code.

## 10. Stop-and-raise conditions

The `live` marker turns out to be applied by directory (not per-test) at HEAD — re-ground
Q2 and hang the fixture off the actual mechanism, do not guess. The endpoint client
exposes no stable base-URL handle — fall back to the sentinel key (§6(a) note) and record
it, do not invent a config read. If the two-process proof still flakes WITH the lock held,
STOP: the contention is not solely endpoint-level (file a finding — the class is wider than
modeled), do not paper over with a retry.

## 11. Parked decisions

| Decision | Default recorded | Rejected alternatives (why) | Re-entry condition |
| --- | --- | --- | --- |
| lock primitive | stdlib `fcntl.flock` (no new dep; POSIX on CI + darwin) | `filelock` package (adds a runtime dependency for a test-only concern; not currently installed); `threading.Lock` / xdist in-process guard (cannot serialize across separate processes — the actual geometry, Q1) | a non-POSIX CI runner appears, or Windows support is needed |
| lock scope | per-live-test (acquire at each live test's setup) | session-scoped hold (serializes collection + non-live work too — wrong grain) | never — the grain is the live test |
| what to do about upstream empty-content | avoid provoking it via serialization | patch/retry the Ollama call (upstream behavior, out of scope; the lock removes the trigger) | the flake recurs WITH the lock (§10 stop condition → finding) |

## 12. Dependency & ordering summary

Item 12 → Item 13; strictly serial, blast-radius ascending (add a no-op-by-default fixture
→ prove it under real contention). No cross-plan dependency (test-infra only, disjoint from
every code plan). After Item 13 the live tier is contention-safe and finding-0046/0048's
re-run workaround demotes to the documented fallback for a genuinely hung endpoint.
