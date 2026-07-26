---
type: build-plan
id: bp-111
track: ops
status: ready
design_ref:
  - docs/design-notes/dn-supervision-and-liveness.md
contract: builder
write_scope:
  - ops/lifecycle/lease.py
  - ops/lifecycle/launcher.py
  - ops/lifecycle/snapshot.py
  - tests/unit/test_supervisor_lease.py
  - tests/integration/test_status_report.py
  - tests/unit/test_restart_trustworthy.py
  - tests/integration/test_lifecycle.py
session_budget: 1
cost:
  estimate:
    model: opus
    tokens: 250k
  actual: null
depends_on: [bp-110]
parallelizable_with: []
created: 2026-07-25
updated: 2026-07-25
links:
  - docs/findings/finding-0172.md
  - docs/findings/finding-0186.md
  - docs/findings/finding-0188.md
re_entry: null
supersedes: null
superseded_by: null
warrant: docs/findings/finding-0172.md
---

# Build Plan — the dead-man inversion: health decays instead of being asserted

## 0. Mode & provenance

Graduated from `dn-supervision-and-liveness` §2.6 (reframing B — the supervisor lease) and §4's
wiring paragraph. **It is the half of the dead-man layer that carries no teeth**; enforcement
(budgets, escalation, the bounded-drain report) is bp-112. They are split because they have
different falsifiers — the lease's is *crying wolf*, the escalation's is *killing a healthy job* —
and because both edit `ops/lifecycle/launcher.py`, so pairing them would make one unreviewable
session out of two reviewable ones.

Investigation and planning produced this; implementation proceeds item-by-item on owner approval.

## 1. Objective

Nothing in the system asserts that the supervisor is healthy; health is computed from a lease that
decays unless the serve loop renews it.

### 1.2 Non-goals (explicit — see §9)

Not job budgets, not escalation, not the drain report (bp-112). Not a change to the run ledger's
schema. [INFERENCE] Not a continuous probe process or any new daemon — the note gives the renewer
a home in the *existing* loop, and inventing a second process would re-create the class §2.8 names
(a ledger written by the actor whose failure it records). Inferred from §2.6's "exactly one site".

## 2. Context manifest

Read in order, whole files before citing:

1. `docs/design-notes/dn-supervision-and-liveness.md` §2.6 **in full** (the inversion, the three
   mechanisms, the five-target table and the falsifier prose beneath it), §2.9, §4, **V9** — the
   content spec
2. `docs/findings/finding-0172.md` — the warrant: a stored assertion outliving its actor
3. `ops/lifecycle/runs.py:60-120` — `RunRecord.active` (`:71-74`), `open_run`, `mark_stopped`
4. `ops/lifecycle/launcher.py` — `_serve` `:662-695` (the one renewal site), `_supervisor_alive`
   `:166-212`, the status render `:1100-1205`
5. `ops/lifecycle/snapshot.py:91-117` — `run_state`, the liveness reader
6. `ops/lifecycle/lock.py` — bp-108's lockfile; its mtime is one of V9's two candidate clocks
7. `scheduler/supervisor.py` + `scheduler/worker.py` — bp-110's loop, which is what makes an honest
   lease possible at all

**Does core already have this?** Two things exist and must be **reused, not duplicated**:
`_supervisor_alive` (`launcher.py:166-212`) is the existing pid-identity probe and becomes the
**fallback**, not a competitor — §3 Q4. `RunLedger` (`ops/lifecycle/runs.py`) already owns run
rows; if V9 picks the ledger clock, the lease is a column there, not a second store. There is no
existing lease, timer, or heartbeat anywhere in the repo.

## 3. Investigation & grounding  <!-- Part A -->

- **Q1 — what asserts health today?** Two stored bits. `RunRecord.active` is literally
  `self.stopped_at is None` (`ops/lifecycle/runs.py:71-74`), and a job's `state = 'running'`
  (`scheduler/queue.py:47`). Both are written by the actor whose failure they must record, which is
  §2.8's named class. Neither decays.
- **Q2 — ⚑ why does this plan genuinely need bp-110?** Because a lease renewed from a loop that a
  handler can block is a **cry-wolf generator**, not a health signal. bp-108's `run(max_ticks=K)`
  makes the loop cycle at *job boundaries*, but one wedged job still owns the thread for hours
  (`scheduler/supervisor.py:87`), so the lease would expire during a single honest long job. Only
  bp-110's worker split puts the compute off the loop. The note says this outright (§2.6: "the
  inversion does not escape the seam … B *depends on* §2.5"); the citation confirms it rather than
  taking it on trust.
- **Q3 — where is the one renewal site?** `ops/lifecycle/launcher.py`'s `_serve` loop body,
  between `c.supervisor.run(...)` (`:676`) and the interval checks (`:677-692`). Renewing anywhere
  inside a handler, or inside the landing step, would make the signal mean "some code ran" instead
  of "the supervisory loop cycled" — the note's own falsifier.
- **Q4 — what happens to old run ledgers with no lease?** ⚑ **They must not read DOWN forever.**
  §4 requires the fallback explicitly: `status` computes liveness from lease age *when a lease
  exists*, and falls back to the bp-105 identity probe (`_supervisor_alive`, `launcher.py:166-212`)
  when it does not. Without this, every historical run in `runs.sqlite` renders as a dead
  supervisor the moment this ships.
- **Q5 — V9: what clock, and what ttl?** **Not settled by reading; Item 1 measures it.** Two
  candidates, both real: the **lockfile mtime** (bp-108 already creates the file; one `utime` call
  per tick, no SQLite write) and a **`runs.sqlite` column** (transactional, queryable, but a write
  per tick on a WAL database). The ttl must comfortably exceed the loop's worst *honest* tick,
  which now includes a p99 landing step — bp-110 Item 1's V1 number is the input. Both halves are
  measurements, not judgements.
- **Q6 — is `_supervisor_alive` safe to keep as the fallback?** Yes, and bp-105 established the
  correct rule the hard way: refuse only when identity is **positively disproven** (finding-0198 —
  a supervisor always predates its own run row, so "created before ⇒ not the supervisor" builds a
  guard that never fires). Do not re-derive that logic; call the existing function.
- **Q7 — does a lease change what `stopped_at` means?** **No, and it must not.** `mark_stopped`
  (`runs.py:110-120`) records a *deliberate* exit and stays the record of clean shutdown. The lease
  answers a different question (is the loop cycling *now*). A reader that conflates them
  re-introduces the assertion this plan removes.

**Additional risks or questions surfaced during reading:**

- ⚑ **The renewal must survive `recovery` mode.** `start()` routes to `_idle` (`launcher.py:646`)
  rather than `_serve` when the previous run was unclean. A recovery run **is** a live supervisor
  (`launcher.py:634-644` says so) — if only `_serve` renews, a recovery run reads DOWN and the
  operator is told to restart a daemon that is already up, which is precisely the wrong action.
  `_idle` must renew too.
- Wall-vs-monotonic is settled by the same constraint as bp-109 Q6: the reader is a **different
  process** (`status`), so a monotonic value is meaningless. Single-host, so this is a
  wall-vs-monotonic care question, not distributed lease semantics (§2.6 says so).
- `tests/integration/test_status_report.py`, `tests/unit/test_restart_trustworthy.py` and
  `tests/integration/test_lifecycle.py` all assert on the liveness/status surface and are carried.

## 4. Reconciliation  <!-- Part B -->

- **`ops/lifecycle/runs.py:71-74`** — `RunRecord.active`'s docstring, *"Still running (or crashed
  without closing) — `stopped_at` was never set."* → **banner: correction.** The parenthetical is
  the defect stated as a feature: "or crashed without closing" is exactly the state the lease
  exists to distinguish. Amend to say `active` means *the row was never closed* and is **not** a
  liveness signal, and point at the lease for liveness. The property's behaviour does not change —
  only the claim it makes.
- **`ops/lifecycle/launcher.py:1158-1160`** — the status line's `(no enforced job budget)` →
  **cross-ref only, NOT changed here.** bp-112 replaces it with the budget it will then have.
  Recorded so this plan does not half-edit a line another plan owns.
- **`docs/findings/finding-0172.md`** → **cross-ref: extension.** The builder must not edit the
  finding; record the closure evidence in the journal for the orchestrator at seal.

## 5. Write scope

`ops/lifecycle/lease.py` is new and holds the lease primitive and the age computation — one module,
so there is exactly one renewal implementation to grep for (§6's tier claim depends on that).
`ops/lifecycle/launcher.py` carries the renewal call in `_serve` **and** `_idle`, plus the status
render's liveness source. `ops/lifecycle/snapshot.py` carries `run_state`'s new derivation. The
three carried test files **pin the surface this plan moves**.

Deliberately OUT of scope: `ops/lifecycle/runs.py` **unless V9 picks the ledger clock** — see §10;
if it does, that is a scope question to raise, not to assume. Also out: `scheduler/` entirely
(bp-110 owns the loop's shape; this plan only calls into it), `scheduler/queue.py` (bp-109's
row-level leases are a *different* mechanism at a *different* grain — do not unify them), and every
foundation-denylist file.

## 6. Interfaces pinned inline

**The lease — one renewal implementation, one reader.**

```python
# ops/lifecycle/lease.py

@dataclass(frozen=True)
class Liveness:
    """What a reader is allowed to conclude. `state` is one of "up" | "ailing" | "down" |
    "unknown". `source` is "lease" or "identity-probe" — a reader MUST be able to tell which,
    because the fallback is weaker and saying so is the whole honesty requirement."""
    state: str
    source: str
    age_s: float | None

@dataclass
class SupervisorLease:
    path: Path                 # or a runs.sqlite row — V9 decides (Item 1)
    ttl_s: float

    def renew(self) -> None:
        """Called from EXACTLY ONE SITE: the serve/idle loop body. Never from a handler, never
        from inside the landing step. The signal means 'the supervisory loop cycled recently'
        and nothing weaker — a second call site anywhere silently changes what it means."""

    def read(self) -> Liveness: ...
```

**The fallback, verbatim and non-negotiable** (`dn-supervision-and-liveness` §4):

```
status computes liveness from lease age, FALLING BACK to the bp-105 identity probe when no lease
exists yet — old ledgers must not read as DOWN forever.
```

The fallback is the existing function; do not re-implement it (`ops/lifecycle/launcher.py:166`):

```python
def _supervisor_alive(prev: RunRecord) -> bool:
```

**What must NOT change** (`ops/lifecycle/runs.py:71-74`) — the property stays, its *meaning* is
corrected in prose:

```python
    @property
    def active(self) -> bool:
        """Still running (or crashed without closing) — `stopped_at` was never set."""
        return self.stopped_at is None
```

**The tier claim, stated exactly as the note states it, so the code comment cannot inflate it:**

```
active run row, process gone  —  tier 3: liveness is never stored, it decays.
WRONG IF: a second renewal site appears, or a reader keys on `stopped_at IS NULL` alone.
```

## 7. Items

Blast radius: measurement → an isolated module → the single renewal site → the readers.

### Item 1 — V9: measure the renewal cost and pick the clock

- **Objective:** the clock and the ttl are chosen from numbers, not from taste.
- **Files:** none (scratchpad; results recorded in `journal.md`)
- **Acceptance test:** recorded in the journal: (a) per-renewal cost of both candidates —
  lockfile `utime` vs a `runs.sqlite` UPDATE — at the loop's actual tick rate; (b) the loop's
  **worst honest tick** under bp-110's worker mode, including a p99 landing step (bp-110 Item 1's
  V1 number is the input); (c) the proposed ttl, stated as a multiple of (b), with the note's
  default of 3× as the starting point.
- **Falsifier:** ⚑ *the worst honest tick is not bounded* — i.e. there exists a legitimate loop
  pass long enough that any usable ttl would cry wolf. Then the lease cannot be honest yet and the
  right action is to park, not to pick a large ttl that re-widens GONE-mode detection back toward
  today's pull-only bound.
- **Invariant(s) it must not violate:** measurement only; nothing under `data/` is modified beyond
  a scratch file.
- **Touches stored data?** No. **Parallelizable?** No. **Depends on:** none.

### Item 2 — `ops/lifecycle/lease.py`

- **Objective:** the lease exists as an isolated, tested primitive with one renewal path.
- **Files:** `ops/lifecycle/lease.py`, `tests/unit/test_supervisor_lease.py`
- **Acceptance test:** `read()` returns `up` inside the ttl, `down` past it, and `unknown` with
  `source="identity-probe"` when no lease has ever been written; renewal is idempotent; a clock
  moving backwards does not produce a negative age or a spurious `up`.
- **Falsifier:** *`read()` returns `up` when no lease exists.* Absence must never read as health —
  that is the assertion polarity this plan inverts, reproduced inside the mechanism meant to remove
  it.
- **Invariant(s) it must not violate:** the module exposes exactly one `renew`; no reader of this
  module may key on `stopped_at`.
- **Touches stored data?** No (the lease is derived state). **Parallelizable?** No.
  **Depends on:** Item 1.

### Item 3 — the one renewal site (and `_idle` too)

- **Objective:** the serve loop renews, and a recovery run does not read as dead.
- **Files:** `ops/lifecycle/launcher.py`, carried test files
- **Acceptance test:** `_serve` renews once per loop pass; `_idle` (`launcher.py:697-702`) renews
  too, so a **recovery-mode run reads `up`**; a source scan finds exactly **two** call sites of
  `renew()` and both are loop bodies.
- **Falsifier:** ⚑ *a recovery run reads DOWN.* The operator is then told to start a daemon that is
  already live, which bp-105's gate will refuse — a dead-end loop, and the costliest possible
  false negative. ⚑ Also: *`renew()` is reachable from inside a handler or the landing step.* The
  signal then means "some code ran", and the mechanism is decorative.
- **Invariant(s) it must not violate:** the renewal is off the compute path (bp-110's worker holds
  the compute; the loop holds the renewal); no handler gains a lease reference; the loop's existing
  interval logic (`:678-692`) is unchanged.
- **Touches stored data?** No. **Parallelizable?** No. **Depends on:** Item 2.

### Item 4 — readers derive liveness, with an honest fallback

- **Objective:** `status` and `start` stop trusting `stopped_at IS NULL`, without making history
  read as dead.
- **Files:** `ops/lifecycle/snapshot.py`, `ops/lifecycle/launcher.py`, carried test files
- **Acceptance test:** with a fresh lease, `status` reports up **and names the source as the
  lease**; with a stale lease it reports down/ailing; with **no** lease (a pre-change
  `runs.sqlite`) it falls back to `_supervisor_alive` and reports the same answer it does today,
  labelled `identity-probe`. `start`'s gate keeps working in all three cases.
- **Falsifier:** ⚑ *a historical run reads DOWN after this ships*, or *the render does not
  distinguish lease-derived from probe-derived liveness*. The second is subtle and matters: a
  fallback silently presented as a lease is a weaker signal wearing a stronger one's label, which
  is the overclaiming the note calls the foot-gun.
- **Invariant(s) it must not violate:** bp-105's identity probe is **kept and called**, not
  re-implemented (finding-0198's rule is embedded in it); the ORPHANED render and the
  `embedding: YES/⚠ WEDGED` line (`launcher.py:1161-1169`) keep working — they are bp-105's
  diagnostic layer and the note keeps them throughout.
- **Touches stored data?** No (read path). **Parallelizable?** No. **Depends on:** Item 3.

## 8. Math carried explicitly

N/A — no mathematical object. `lease_age < ttl` is a timestamp comparison. The *choice* of ttl is
an engineering bound measured in Item 1, not a statistic; if it later becomes derived from a
distribution (a p99 tick), that is NEW NOTE 1's instrument doctrine, not this plan.

## 9. Non-goals

- **No budgets, no escalation, no drain report** — bp-112.
- **No new process.** The renewer lives in the existing loop (§1.2).
- **No change to `stopped_at`'s meaning** or to `mark_stopped` (§3 Q7).
- **No unification with bp-109's row leases.** Same word, different grain: bp-109 leases a *job
  row*, this leases the *supervisor role*. Merging them would couple two mechanisms with different
  clocks, different ttls and different readers.
- **No removal of `_supervisor_alive`** — it is the fallback and the diagnostic.
- **No tier-1 claim.** §2.6's honest summary: nothing here reaches tier 1; this is tier 3 because
  the clock and the filesystem are the authority.

## 10. Stop-and-raise conditions

- ⚑ **Item 1's falsifier fires** (no ttl exists that is both honest and useful) ⇒ **park the
  criterion** with the measured numbers and a re-entry condition, file the question, and continue
  with Items 2–4 shipping the lease *readable but with liveness still probe-derived*. Never block
  on the owner.
- ⚑ **V9 picks the `runs.sqlite` clock** ⇒ **STOP and raise before writing.**
  `ops/lifecycle/runs.py` is deliberately outside `write_scope` (§5). A measurement that changes
  the write scope is a
  scope question for the orchestrator, not a scope a builder widens for itself — that is the
  finding-0191 shape, and routing around a denial is forbidden.
- **A second `renew()` call site proves necessary** ⇒ STOP. The one-site property is the tier-3
  claim; two sites means the signal means something weaker and the note must be corrected first.
- **The ttl would cry wolf on a healthy long job** ⇒ STOP. bp-102 §10 records this as the
  disqualifier for exactly this class of instrument.
- **A carried test cannot be made green without weakening an assertion** ⇒ STOP and file.
- Any blessing transition — never.

## 11. Parked decisions

| Decision | Default recorded | Re-entry condition |
|---|---|---|
| lease clock | lockfile mtime | Item 1's measurement |
| ttl | 3× the worst honest tick | Item 1; then a cry-wolf observation |
| `ailing` band | ttl < age < 3×ttl | an operator finds it unhelpful |
| renewal on a wedged landing | no special case | a wedged landing is observed |

**Rejected alternatives, per row:**

- **Lease clock.** Rejected: *a `runs.sqlite` column* — transactional and queryable, and genuinely
  attractive, but it is a WAL write every tick on the ledger the supervisor also uses for its own
  bookkeeping, and it widens the write scope (§10). Rejected: *an in-memory heartbeat* — invisible
  to `status`, which is a different process; that is the whole point.
- **ttl.** Rejected: *a fixed number of seconds* — it would be a magic constant, which §2.6's
  falsifier and the note's rot argument both forbid. The ttl must be expressed as a multiple of a
  measured tick so it re-derives when the loop changes.
- **`ailing` band.** Rejected: *binary up/down* — a two-state render loses the "recently stale" case
  that distinguishes a slow loop from a dead one, which is exactly §2.9's detection-lag material
  that NEW NOTE 1 will render.
- **Wedged landing.** §2.6 accepts this residual explicitly: a wedged landing step reads
  DOWN/AILING rather than silent-green — *"the loud wrong answer the mandate prefers."* Special-
  casing it would restore the silence. Re-entry: only if a wedged landing is actually observed and
  the loud answer proves worse than the silent one.

## 12. Dependency & ordering summary

Items strictly linear: **1 → 2 → 3 → 4.**

**`depends_on: [bp-110]`** — substantively, not for file contention: §3 Q2 shows a lease renewed
from a blockable loop is a cry-wolf generator, and only bp-110's worker split takes the compute
off that loop. This is the note's own sequencing (§3: *"the supervisor lease and escalation
fail-safe (a) land with the first split lane"*), read literally.

Transitively this plan also sits after **bp-108** (which creates `ops/lifecycle/lock.py`, the
default lease clock) and **bp-109**.

**Not parallelizable with anything.** `ops/lifecycle/launcher.py` is the wave's contended file
(bp-108 → bp-111 → bp-112 → bp-116, strictly sequenced). **bp-112 depends on this plan** — the
escalation's reports render through the liveness surface this plan establishes, and both edit
`launcher.py`.
