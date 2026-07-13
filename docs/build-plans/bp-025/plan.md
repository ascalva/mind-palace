---
type: build-plan
id: bp-025
status: in-progress
design_ref:
  - docs/design-notes/self-sensing.md # N/A as graduation — wave-debt micro-sweep, no design note (see §0)
contract: builder
write_scope:
  - "ops/ci_witness.py"              # (a) the short-sha guard
  - "ops/lifecycle/launcher.py"      # (b) one stale comment line
  - ".claude/skills/delegate/SKILL.md" # (c) the gate-text separation (skill file, agent-writable)
  - "tests/unit/test_ci_witness.py"  # (a)'s falsifier test
  - "docs/build-plans/bp-025/**"
  - "docs/findings/**"
session_budget: 1
cost:
  estimate: { model: sonnet, tokens: 50k } # three crisp, independent micro-fixes with a checker each
  actual: null
depends_on: []
parallelizable_with: []
created: 2026-07-12
updated: 2026-07-13
links:
  - docs/findings/finding-0038.md # attestable-green rec 3 (the &&-chain fix's origin)
re_entry: null
supersedes: null
superseded_by: null
warrant: null
---

# Build Plan — wave-debt micro-sweep (witness short-sha guard · stale comment · gate-text)

> **Every section below is required.** N/A is an accountability act.

## 0. Mode & provenance

Triage-promoted (third /triage, 2026-07-12): three independent wave-debt items, each with a
crisp checker, NOT a design-note graduation (`design_ref` is a formal placeholder — none of
these graduate from a note; recorded honestly here). Investigation and planning produced
this; implementation proceeds item-by-item on owner approval. `proposed → ready` is the
owner's hand edit. The items are mutually independent (any subset is approvable).

## 1. Objective

Retire three papercuts the wave surfaced: the CI witness silently burning its full grace
window on a non-40-char sha, a launcher comment still naming `gitlab.com`, and the delegate
skill's `&&`-chained gate text that short-circuits at leg 3 (argless `mypy` exits 1 at the
pinned baseline).

## 2. Context manifest

1. `ops/ci_witness.py:73-141` — `run_for(sha)` (`:73`, the `head_sha={sha}` query, `:80`)
   and `check(sha)` (`:110`, the grace-poll loop); `release(sha)` (`:165`) is the second
   sha entry point.
2. `ops/lifecycle/launcher.py:265` — the stale comment `# imports: the witness talks to
   gitlab.com and must stay outside this sealed process.`
3. `.claude/skills/delegate/SKILL.md:64-76` — the `&&`-chained five-leg gate block and the
   "argless == 69" prose around it.
4. `docs/findings/finding-0038.md` — the attestable-green origin (rec 3); the standing-rule
   phrasing "five-part gate legs run SEPARATELY (argless == 69 pinned)".
5. `tests/unit/test_ci_witness.py` — where the short-sha guard's falsifier test lands.

## 3. Investigation & grounding

- **Q1 — why does a short sha silently burn the grace window?** GitHub's
  `?head_sha={sha}` (`ci_witness.py:80`) matches only a *full* 40-char sha; a short or
  bogus sha matches zero runs, so `run_for` returns `None` → `verdict` "absent" →
  `check()` polls to the full `min(GRACE_S, wait_s)` grace before concluding absent
  (`:122-135`). The deploy standing rule already says "witness `check <FULL-sha>` — never a
  short sha", but nothing *enforces* it; a slip costs a 300s grace window (observed
  2026-07-12).
- **Q2 — reject or expand?** Expand-then-verify is friendlier and safe: `ci_witness.py`
  already imports `subprocess` (`:29`), so `git rev-parse --verify <sha>^{commit}` resolves
  a short sha (or a ref) to the full 40 before any HTTP poll; if it cannot resolve, error
  out immediately (rc≠0) rather than poll. Normalize once at each *entry* point (`check`,
  `release`) — NOT inside `run_for` (it is called in the poll loop with the
  already-resolved sha).
- **Q3 — the launcher comment.** `launcher.py:265` still says "gitlab.com"; the witness
  now targets `api.github.com` (`ci_witness.py:58-80`, D4 = GitHub). Comment-only; no
  behavior. (The line number is 265, not the resume brief's approximate 259 — grounded.)
- **Q4 — the delegate gate text.** `SKILL.md:64-76` chains all five legs with `&&`. Leg 3
  is the *argless* `uv run mypy`, which exits 1 at the pinned tests/-baseline (69 errors),
  so the chain short-circuits and legs 4-5 (`type_gate`, `pytest`) never run — a builder
  copying the block verbatim gets a false-green surface. The standing rule already mandates
  separated legs; the skill text lags it.

**Additional risks surfaced during reading:** none — three independent, low-blast changes;
(a) is the only behavior change and it is guarded by a unit test with a stubbed
`subprocess`/HTTP boundary.

## 4. Reconciliation

- `ops/lifecycle/launcher.py:265` — "the witness talks to gitlab.com" → **[banner:
  correction]** "the witness talks to api.github.com" (carried by Item 16).
- `.claude/skills/delegate/SKILL.md:64-76` — the `&&`-chained block → **[correction]**
  five legs on separate lines with the "argless `uv run mypy` exits 1 at the tests/-baseline
  (69) — run each leg and read its result; do NOT `&&`-chain past leg 3" note (Item 17).

## 5. Write scope

In: `ops/ci_witness.py` (the guard + a small `_full_sha` helper), `ops/lifecycle/launcher.py`
(one comment line), `.claude/skills/delegate/SKILL.md` (the gate block + note),
`tests/unit/test_ci_witness.py`, own plan dir, findings. Out, deliberately: any design note
(the delegate SKILL is agent-writable working material, not a note); `scripts/
attestable_green.sh` (0038 rec 3 — stays a deferred nicety, §11); the foundation denylist;
all other code.

## 6. Interfaces pinned inline

**(a) The sha guard (`ci_witness.py`, a helper + one call at each entry):**

```python
import re
_FULL_SHA = re.compile(r"^[0-9a-f]{40}$")

def _full_sha(sha: str) -> str:
    """Return the 40-hex sha. Identity if already full; else resolve via git.
    Raises SystemExit with a clear message if it cannot resolve (never poll on a
    sha that can never match GitHub's head_sha= query, §3 Q1)."""
    if _FULL_SHA.match(sha):
        return sha
    r = subprocess.run(["git", "rev-parse", "--verify", f"{sha}^{{commit}}"],
                       capture_output=True, text=True)
    out = r.stdout.strip()
    if r.returncode != 0 or not _FULL_SHA.match(out):
        raise SystemExit(f"ci-witness: '{sha}' is not a resolvable 40-char commit sha "
                         f"(head_sha= needs the full sha; pass the full commit).")
    return out
```

Called as the FIRST line of `check()` (`:110`) and `release()` (`:165`): `sha = _full_sha(sha)`.
`run_for` is unchanged (it receives the already-normalized sha).

**(b) The launcher comment (`launcher.py:265`):**

```python
    # imports: the witness talks to api.github.com and must stay outside this sealed process.
```

**(c) The delegate gate text (`SKILL.md`, replacing the `&&`-chained block):**

```
Run each leg SEPARATELY and read its result — do NOT `&&`-chain them:

    uv run ruff check .
    uv run mypy core agents eval ops scheduler scripts
    uv run mypy                 # ARGLESS — exits 1 at the tests/-baseline (69 errors);
                                # this is why the legs must not be &&-chained (leg 3
                                # would short-circuit legs 4-5).
    uv run python -m ops.type_gate
    uv run pytest -q

Assert the argless `uv run mypy` tail equals the pinned tests/-baseline (**69** today —
finding-0029; re-pin here when it changes).
```

## 7. Items

_(numbering continues the global sequence)_

### Item 15 — the witness short-sha guard

- **Objective:** `check()` and `release()` resolve their `sha` to a full 40-hex value
  before any HTTP poll; a non-resolvable sha errors immediately instead of burning grace.
- **Files:** `ops/ci_witness.py`, `tests/unit/test_ci_witness.py`
- **Acceptance test:** `uv run pytest -q tests/unit/test_ci_witness.py` green including a new
  test: a full 40-hex sha passes through unchanged (no `git` call needed / identity); a
  short sha is expanded via a stubbed `git rev-parse`; an unresolvable sha raises
  `SystemExit` BEFORE any `run_for`/HTTP call (assert the HTTP boundary is never reached).
- **Falsifier:** a short/bogus sha still reaches the poll loop and burns the grace window
  (the guard is bypassed or placed after `run_for`); or a legitimate full sha triggers a
  spurious `git` call / error.
- **Invariant(s):** `run_for`/`verdict`/`attest_verdict` behavior unchanged; the deploy
  gate's full-sha path is byte-identical (identity branch); no new dependency (`re`,
  `subprocess` already imported).
- **Touches stored data?** no
- **Parallelizable?** yes **Depends on:** none

### Item 16 — the launcher comment correction

- **Objective:** `launcher.py:265` names `api.github.com`, not `gitlab.com`.
- **Files:** `ops/lifecycle/launcher.py`
- **Acceptance test:** `grep -n gitlab ops/lifecycle/launcher.py` returns nothing;
  `grep -n "api.github.com" ops/lifecycle/launcher.py` shows the line. Comment-only —
  `uv run ruff check ops/lifecycle/launcher.py` clean.
- **Falsifier:** any non-comment line changed (a `git diff` shows an executable-line edit).
- **Invariant(s):** zero behavior change; the sealed-process comment's intent (witness
  imports stay outside the sealed process) is preserved.
- **Touches stored data?** no
- **Parallelizable?** yes **Depends on:** none

### Item 17 — the delegate gate-text separation

- **Objective:** the delegate skill shows the five legs run separately with the
  argless-exits-1 note (§6(c)), so a builder copying it cannot get a false-green.
- **Files:** `.claude/skills/delegate/SKILL.md`
- **Acceptance test:** `grep -n "&&" .claude/skills/delegate/SKILL.md` shows no `&&`-chained
  gate legs; the argless-mypy note ("exits 1 at the tests/-baseline (69)") is present;
  reads coherently against the surrounding §"Supervision & scrutiny".
- **Falsifier:** the block still `&&`-chains the legs, or drops the argless-baseline note
  (the two things that make the original wrong).
- **Invariant(s):** the skill's other sections unchanged; no design note touched (SKILL
  files are agent-writable working material).
- **Touches stored data?** no
- **Parallelizable?** yes **Depends on:** none

## 8. Math carried explicitly

N/A — no mathematical object.

## 9. Non-goals

Enforcing full-sha at the CLI/argparse layer beyond `check`/`release` (those are the two
sha entry points that poll); any change to the witness's HTTP/verdict logic; creating
`scripts/attestable_green.sh` (deferred, §11); folding the gate into a script (0038 rec 3
stays deferred); any behavior change in `launcher.py`.

## 10. Stop-and-raise conditions

If `ci_witness.py` no longer runs inside the repo (so `git rev-parse` is unavailable at the
call site), STOP — the expand strategy assumes repo context; fall back to reject-only (the
§11 alternative) and record it. If `launcher.py:265`'s comment already reads github at HEAD
(a prior sweep landed it), mark Item 16 N/A in the journal and continue. If separating the
delegate legs surfaces a deeper contradiction with the standing rule text, file a finding
rather than editing beyond the block.

## 11. Parked decisions

| Decision | Default recorded | Rejected alternatives (why) | Re-entry condition |
| --- | --- | --- | --- |
| short-sha handling | expand via `git rev-parse`, then verify; error if unresolvable | reject-only (rejects a legitimate short sha a human might paste — less friendly); silently pad/guess (unsafe) | `ci_witness` loses repo context (§10) → reject-only |
| `scripts/attestable_green.sh` | deferred (design-tier, 0038 rec 3) | build it now (scope creep on a micro-sweep; the standing-rule text + Item 17 already deliver the correctness) | a dedicated gate-script plan, or the &&-chain recurs elsewhere |

## 12. Dependency & ordering summary

Items 15, 16, 17 are mutually INDEPENDENT (disjoint files, any subset approvable) — no
intra-plan ordering. Item 15 is the only behavior change (guarded by its unit test); 16 and
17 are comment/doc corrections. No cross-plan dependency. Blast radius stays low: a witness
entry-guard, a comment, and a skill-file edit.
