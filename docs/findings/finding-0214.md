---
type: finding
id: finding-0214
status: resolved
created: 2026-07-26
updated: 2026-07-26
links:
  - tests/integration/test_selfmod.py          # :76 — hard-codes current_value == 0.62
  - tests/integration/test_selfmod_cli.py      # :38 — hard-codes "0.62 -> 0.66" in the render
  - config/local.toml                          # :47 — the owner's oq-0024 σ enactment, GITIGNORED
  - config/defaults.toml                       # keeps 0.62, which is why CI never sees this
  - docs/findings/finding-0212.md              # the same seam, opposite sign
ftype: blocker
origin_plan: bp-121
route: builder
resolution: >-
  Discharged by bp-122 (the two self-mod tests made hermetic) and VERIFIED EMPIRICALLY by the orchestrator at the 2026-07-26 sweep, not taken on report: `uv run pytest tests/integration/test_selfmod.py tests/integration/test_selfmod_cli.py -q` in the MAIN checkout, against the owner's real gitignored overlay (sigma=0.58) -> **18 passed in 0.18s**. The local suite and CI now agree; deploy gate 5 is clear.
---

> ⚑ **ESCALATED to `blocker` — 2026-07-26, same day, on the owner's report that deploy is
> blocked.** `Launcher.deploy`'s gate 5 (`launcher.py:586-597`, `gate_cmd`) is *byte-for-byte the
> local tier these two tests fail*. So this is not builder friction: **it will refuse
> `mind-palace deploy` on the owner's machine**, and it is the next gate he hits after starting the
> daemon. Original write-up (filed as `codebase`) below, unchanged.

# Two self-mod tests read the owner's gitignored config overlay, so the local suite is red while CI is green

## What

Discovered incidentally while running bp-121's pre-push gate. The CI-equivalent tier is
**2 failed, 2099 passed** locally, and the same tier on the runner is green on both tests.

```
FAILED tests/integration/test_selfmod.py::test_good_change_traverses_the_gate_and_is_kept
  assert 0.58 == 0.62
FAILED tests/integration/test_selfmod_cli.py::test_propose_list_show_history
  assert "0.62 -> 0.66" in "…dream_similarity_threshold: 0.58 -> 0.66  (tighten themes)"
```

Both are one cause, and neither is a defect in the code under test. The two tests build a
self-mod loop over the **merged live config** and then assert against a literal `0.62` — the
`defaults.toml` value for `dream_similarity_threshold`. The owner's **oq-0024** ruling (σ
0.62 → 0.58) was enacted in `config/local.toml:47`, which is **gitignored** (`.gitignore:25`) and
deliberately so: `defaults.toml` keeps 0.62 precisely so a fresh clone and CI are unchanged.

So the tests do not pin a fixture value; they pin *whatever this machine's σ currently is*. Any
owner-side lever change turns them red, on that machine only, forever.

⚑ Confirmed **not** caused by bp-121: the remote `ratchet` on `8086182` fails on exactly the three
`test_restart_trustworthy.py` tests and nothing else, and these two failures reproduce with
bp-121's diff reverted.

## Why it matters

**It is finding-0212 with the sign flipped, on the same seam.** finding-0212 is *local green while
the authoritative gate is red*; this is *local red while the authoritative gate is green*. Both
come from the pre-seal gate and CI measuring different things, and the second is the more
corrosive of the two: a gate that is red for a reason unrelated to your change trains every
builder to read "2 failed" and shrug. That habit is the precondition for finding-0212's miss —
bp-105 sealed with a locally-green board while CI was red, and four subsequent seals never looked.

It also makes the documented local gate unusable as written: the green-gate recipe deselects two
known-red nodes by name, and there is now a third and fourth red that no recipe covers and that
exist only on the owner's machine.

Secondarily, it is a hermeticity defect in its own right. An integration test that reads the
machine-local overlay has no fixed expected value — the assertion is `0.62` today because of a
config file that is not in the repository, so the test cannot be reasoned about from the tree.

## ⚑ The deploy consequence (added on escalation)

`Launcher.deploy` has six gates in order (`launcher.py:868-908`): a live run exists · tree clean ·
on `main` · HEAD ≠ the live run's commit · **the local ratchet is green (`gate_cmd`)** · the
ci-witness attests a green remote HEAD.

`gate_cmd` is `uv run pytest -q -m 'not live and not podman and not needs_vault and not
needs_restic' --deselect …test_core_imports_nothing_outside_core` — *identical* to the tier these
two tests fail on. So the sequence the owner is about to walk is:

1. gate 1 refuses today (`deploy: no live run — nothing to cycle`) because the daemon is down;
2. he starts the daemon, clearing gate 1;
3. **gate 5 then refuses on these two tests**, and the only documented escape is `--skip-tests`,
   which drops the *whole* gate — local ratchet *and* ci-witness — for a config-overlay artifact.

That is the shape worth naming: a false red on a gate whose only bypass is total. It converts an
unrelated test-hermeticity defect into pressure to deploy with no verification at all. `bp-121`
cleared the *remote* half of the gate (ci-witness); this is the *local* half, and it was hidden
behind the remote failure until now.

## Re-entry condition

Nothing is parked on it — bp-121 proceeded, since the failures are provably unrelated (see above)
and the plan's acceptance is the remote run. It is **out of bp-121's `write_scope`** (which is
`ops/lifecycle/launcher.py` + `tests/unit/test_restart_trustworthy.py`), so it is filed rather
than fixed: §10 of that plan names widening scope as a stop-and-file condition.

Resolves when both tests pin σ from a fixture or from `defaults.toml` rather than the merged live
config, and the local CI-equivalent tier is green on a machine carrying a `config/local.toml`
overlay. The falsifier for any fix: set `similarity_threshold` to a third value in `local.toml`
and re-run — a fix that only special-cases 0.58 has not made the test hermetic.

## Routing

`codebase` → builder. Bounded and mechanical (two assertions, plus whatever fixture the loop needs
to take σ from). Not foldable into finding-0212, which is a *duty* (compare the local gate against
the authoritative host at seal time) rather than a test defect — but the two should be read
together, since fixing 0212's duty without fixing this one means every future seal record carries
a permanent unexplained local delta.

⚑ Sweep note for `/triage`: **oq-0024 is still open on the sweep axis**, and this is a second
consequence of that enactment living only in a gitignored file. Worth recording there too — a
builder may not edit an existing owner question.
