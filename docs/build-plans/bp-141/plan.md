---
type: build-plan
id: bp-141
track: workflow
status: proposed
design_ref:
  - docs/design-notes/dn-typed-workflow-registry.md
contract: builder
write_scope:
  - ops/registry/**
  - scripts/registry.py
  - tests/unit/test_registry_degraded.py
  - tests/integration/test_registry_reconcile.py
session_budget: 1
cost:
  estimate:
    model: opus
    tokens: 300k
  actual: null
depends_on: [bp-140]
parallelizable_with: [bp-144]
created: 2026-07-27
updated: 2026-07-27
links:
  - docs/design-notes/dn-typed-workflow-registry.md
  - docs/build-plans/bp-140/plan.md
re_entry: null
supersedes: null
superseded_by: null
warrant: null
---

# Build Plan — Degraded mode: the pending file, provisional refs, reconcile, recovery import

## 0. Mode & provenance

Investigation and planning produced this plan during `/graduate` of
`dn-typed-workflow-registry` (ratified 2026-07-27). Implementation proceeds item-by-item on
owner approval; the `proposed → ready` blessing is the owner's alone.

The note's §4 is explicit that this is **not** deferred work: "the pending-file degraded
path and the recovery import as CLI subcommands, built in stage (i)–(ii), **not deferred to
the first outage**." §2.9 makes the same demand: "a degraded mode exists and is specified
now, not discovered during the first outage."

## 1. Objective

Make the registry survive its own unavailability — a per-worktree pending file under
provisional refs, a reconcile that binds each provisional ref to a serial id exactly once,
and a recovery import that reads the markdown tree back into the log.

## 2. Context manifest

1. `docs/design-notes/dn-typed-workflow-registry.md` §2.9 (the three non-negotiables and
   their mechanisms), §2.2 (the provisional-ref = idempotency-key binding), §2.9's
   invariants 5 and 6.
2. `docs/build-plans/bp-140/plan.md` §6 — the store, the `Event` shape, the fold rule, and
   the CLI surface this plan extends. **Read the interfaces, not the design note, for the
   API**; bp-140 pins them verbatim.
3. `docs/build-plans/bp-140/journal.md` — what actually landed and what surprised the
   builder.
4. `ops/registry/store.py`, `ops/registry/events.py`, `ops/registry/ids.py`,
   `ops/registry/fold.py` — the code as it stands after bp-140.
5. `scripts/handoff.py:18-40` (the idempotence pin) — the discipline a reconcile must not
   break: a derived artifact embeds no clock and no counter.
6. `docs/build-plans/bp-141/journal.md`.

### DRY audit — does `core/` (or the wider tree) already have this?

- **An outbox/pending-queue pattern?** `data/queue.sqlite` (scheduler jobs, with leases) is
  the nearest thing, and it is the **wrong** shape: it is a work queue with a live consumer,
  in `data/` (per-worktree — the exact placement the note's §2.8 rejects), and it presumes
  the store is available. **Not reusable.**
- **An idempotency-key mechanism?** Yes, and it is **this family's own** —
  `ops/registry/store.py`'s `idempotency_key UNIQUE` from bp-140. This plan *reuses* it
  rather than adding a second dedupe path; that reuse is the note's design ("a provisional
  ref written offline **is** the idempotency key").
- **A markdown → structured-state reader?** Yes — `.claude/hooks/_lib.py:183`
  (`parse_front_matter`) plus `scripts/board.py`'s scanners (`scan_plans`, `scan_notes`,
  `scan_findings`, `scan_oqs` at `scripts/board.py:174-233`). The recovery import (Item 10)
  **must call these**, not re-derive them. `scripts/handoff.py:57-61` shows the exact
  sys.path idiom for importing both from repo-workflow tooling.
- **A UUID/ref generator?** `uuid.uuid4()` (stdlib). Nothing custom exists or is needed.

## 3. Investigation & grounding

- **Q1 — where does the pending file live?** The note says "a local pending file
  (per-worktree, append-only)". Per-worktree means **inside the checkout**, so it must be
  gitignored or it becomes tree churn the export ratchet (bp-142) will fight. Pinned:
  `data/registry-pending.jsonl`. `data/` is already per-worktree and already gitignored —
  verified: `scripts/handoff.py:29-33` records that "`data/queue.sqlite` is gitignored
  runtime state … absent from every worktree." Choosing `data/` therefore needs no
  `.gitignore` edit, and `.gitignore` is deliberately **not** in `write_scope`; confirm
  with `git check-ignore -v data/registry-pending.jsonl` as Item 7's first act. If it is
  **not** ignored, stop and raise (§10) rather than editing `.gitignore` silently.
- **Q2 — what makes a read "never block"?** Two halves. Substrate: WAL +
  `busy_timeout=5000` (bp-140 §6.1). Fallback: "every read path has a fallback to the
  *export* — the working tree's certified frontmatter" (note §2.9(1)). **The export does
  not exist until bp-142.** So this plan builds the *fallback mechanism* and points it at
  the working tree's front matter as it stands today (which is, for now, the only
  projection there is); bp-142 makes that projection certified. Say this plainly in the
  journal — do not claim invariant 5 is fully discharged here.
- **Q3 — may a privileged transition be submitted degraded?** No. Note §2.9(2), verbatim:
  "Privileged transitions are the exception: a blessing does not happen degraded — it
  *queues* unverified and is not effective until admitted. Degraded mode loosens liveness,
  never authority." The pending file may **hold** such an event; the fold must not treat it
  as effective. This is invariant 6.
- **Q4 — what counts as "privileged"?** The note's §2.5.1 table: `draft → ratified`
  requires a signature; `proposed → ready` does not. Until bp-144/bp-145 land there is no
  signature to check, so this plan's rule is **structural, not cryptographic**: a
  `transitioned` event whose `to_status` is in `PRIVILEGED_TARGETS` is never marked
  effective from the pending file, regardless of signature. The constant is pinned in §6.3.
- **Q5 — does reconcile risk double-application?** Only if the provisional ref is not the
  idempotency key. It is (note §2.2). Replay is therefore `submit()` per pending line, and
  bp-140's UNIQUE constraint makes a second replay a no-op. **The code does not settle
  whether bp-140's `submit()` returns the existing seq or raises** — bp-140 Item 4's
  acceptance requires it to return; verify that behavior in the landed code before building
  on it, and if it raises, that is a bp-140 defect (file a finding, do not paper over it).
- **Q6 — what does the recovery import do about divergence?** Note §2.9(3)(i): "a recovery
  import reconciles the tree back into the log afterward (divergences surface as **conflicts
  for the owner, not silent merges**)." So the import is **report-then-apply**, never
  apply-blind: `--dry-run` is the default and `--apply` is opt-in.

**Additional risks or questions surfaced during reading:**

- A pending file in `data/` disappears with the worktree. That is *by design* under the
  disposable-sessions doctrine, but it means an agent that queues a mint and then has its
  worktree deleted loses the mint. Acceptable: the artifact's prose is in the diff or it is
  not, and either way nothing was consequential. Record it as a known, accepted loss.
- Two worktrees each holding pending mints will, on reconcile, receive **different** serial
  ids than their provisional refs. Any file already written under the provisional ref must
  be renamed at reconcile time — Item 9 must emit the rename plan, not perform it silently.

## 4. Reconciliation

- `ops/registry/store.py` (as landed by bp-140) — its `submit()` docstring says "Append one
  event; return its seq. Idempotent on event.idempotency_key." → **cross-ref: extension**.
  This plan adds no second dedupe rule; it *depends* on that one and its docstring gains a
  cross-reference to the degraded path (`ops/registry/pending.py`) so a later reader sees
  why idempotency is load-bearing rather than defensive.
- `scripts/registry.py` (bp-140) — the CLI gains three subcommands (`reconcile`, `import`,
  and a `--degraded-ok` flag on `mint`/`submit`). → **cross-ref: extension**, documented in
  the CLI's own `--help` and in `ops/registry/schema.md`.
- Nothing is corrected. No banner is owed.

## 5. Write scope

- `ops/registry/**` — new `pending.py` (append/read/replay), `recover.py` (tree → log
  import), and edits to `store.py` / `fold.py` for the fallback read path and the
  not-effective marking of queued privileged events.
- `scripts/registry.py` — the three new subcommands.
- `tests/unit/test_registry_degraded.py`, `tests/integration/test_registry_reconcile.py`.

**Deliberately OUT of scope:** `.gitignore` (§3 Q1 — if `data/` is not ignored, that is a
stop-and-raise, not a quiet edit); every hook and `.claude/settings.json`; `docs/design-notes/**`;
the foundation denylist files; `scripts/board.py` and `scripts/handoff.py` (this plan
*imports* their scanners, never edits them); the export renderer (bp-142).

**Overlap note:** this plan's `ops/registry/**` and `scripts/registry.py` overlap bp-140's
and bp-142's. That is why `depends_on: [bp-140]` is set and why this plan is **not**
declared parallelizable with bp-142 — only with bp-144, whose scope is disjoint.

## 6. Interfaces pinned inline

### 6.1 The pending file

```
path:   data/registry-pending.jsonl        # per-worktree, gitignored, append-only
format: one canonical-JSON object per line, newline-terminated, UTF-8
```

```json
{"provisional_ref": "pending-9f2c1e4a-...", "entity_type": "finding", "kind": "minted",
 "payload": {...}, "actor": "builder:bp-141", "recorded_at": "2026-07-27T18:04:11Z",
 "signature": null, "signer": null}
```

**`provisional_ref` IS the idempotency key** (note §2.2). Format:
`pending-<uuid4-hex>`. It is written into the pending file *and* used verbatim as
`Event.idempotency_key` at replay, which is what makes reconciliation exactly-once.

### 6.2 API

```python
# ops/registry/pending.py
PENDING_PATH = Path("data/registry-pending.jsonl")     # relative to the worktree root

def append_pending(entry: PendingEntry, *, root: Path) -> str:
    """Append one entry; return its provisional_ref. Append-only: the file is opened
    'a' and fsync'd, never rewritten (note invariant 1, one level out)."""

def read_pending(*, root: Path) -> list[PendingEntry]: ...

def reconcile(registry: Registry, *, root: Path, dry_run: bool = True) -> ReconcileReport:
    """Replay pending entries through NORMAL admission, oldest first. Each replay uses
    provisional_ref as the idempotency key, so a second reconcile is a no-op (note §2.2).
    Returns the binding provisional_ref -> serial ref for every entry, plus any file
    renames the caller must perform. Applies nothing unless dry_run is False."""
```

```python
@dataclass(frozen=True)
class ReconcileReport:
    bindings: dict[str, str]          # provisional_ref -> serial ref
    renames: list[tuple[Path, Path]]  # a file written under a provisional ref -> its serial path
    queued_privileged: list[str]      # provisional refs NOT made effective (invariant 6)
    conflicts: list[str]              # human-readable; never auto-resolved
```

```python
# ops/registry/recover.py
def import_tree(registry: Registry, *, root: Path, dry_run: bool = True) -> ImportReport:
    """The escape-hatch return path (note §2.9(3)(i)): read the markdown tree's front matter
    and reconcile it back into the log. REUSES scripts/board.py's scanners and
    .claude/hooks/_lib.py's parser — never re-derives either. Divergences between tree and
    log are reported as CONFLICTS for the owner, never silently merged."""
```

### 6.3 The privileged-target constant

```python
# ops/registry/pending.py
# note §2.5.1: `draft → ratified` is signature-bearing and never automatable;
# `proposed → ready` is the autopilot-delegable gate. Both are OWNER-ONLY today, so
# neither may become effective out of a degraded queue (invariant 6). The deskcheck
# verdict is listed because it is the third owner-only gate (`_lib.py:268 verdict_of`).
PRIVILEGED_TARGETS = frozenset({"ratified", "ready", "approved", "needs-work"})
```

### 6.4 Read-path fallback

```python
# ops/registry/fold.py
def query(self, *, allow_fallback: bool = True, **filters) -> QueryResult:
    """Never blocks and never fails closed (invariant 5). If the store cannot be opened
    within the busy_timeout, and allow_fallback is True, the answer is derived from the
    working tree's front matter and the result is flagged:
        QueryResult(rows=[...], source="store" | "tree", degraded=bool)
    A reader that cannot open the store READS THE TREE AND SAYS SO (note §2.9(1)) —
    'says so' is the `source` field, and every CLI rendering must print it."""
```

### 6.5 CLI additions

```
uv run scripts/registry.py mint ... --degraded-ok      # falls back to the pending file
uv run scripts/registry.py reconcile [--apply]         # default: dry-run report
uv run scripts/registry.py import [--apply]            # tree -> log; default: dry-run
uv run scripts/registry.py doctor                      # gains: pending count, degraded?
```

### 6.6 Invariants (note §2.9, verbatim)

1. No event is ever mutated or deleted; corrections are events.
2. Two submissions with one idempotency key yield one ref, always.
5. Reads degrade to the export; they never wait on a writer and never fail closed.
6. A degraded-mode blessing is queued, not effective; authority never degrades.

## 7. Items

### Item 7 — the pending file: append, read, provisional refs

- **Objective:** an append-only per-worktree JSONL pending file whose entries carry
  provisional refs that double as idempotency keys.
- **Files:** `ops/registry/pending.py`, `tests/unit/test_registry_degraded.py`
- **Acceptance test:** `uv run pytest tests/unit/test_registry_degraded.py -q` green: three
  appends produce three lines, each parseable as canonical JSON with a distinct
  `provisional_ref`; re-reading returns them in write order. Plus
  `git check-ignore -v data/registry-pending.jsonl` exits 0 (the file is gitignored).
- **Falsifier:** the pending file appears in `git status --porcelain -uall` after an append
  — it would then be tree churn the export ratchet (bp-142) fights forever, and the
  placement decision (§3 Q1) is wrong.
- **Invariant(s) it must not violate:** append-only — the file is never rewritten or
  truncated by this module.
- **Touches stored data?** Yes (a new per-worktree file). Dry-run: `doctor` reports the
  pending count before any append.
- **Parallelizable?** No.  **Depends on:** bp-140 Items 1–4.

### Item 8 — degraded submission: the store-unavailable path

- **Objective:** `mint`/`submit` fall back to the pending file when the store cannot be
  opened, and never make a privileged transition effective.
- **Files:** `ops/registry/pending.py`, `ops/registry/store.py`, `scripts/registry.py`,
  `tests/unit/test_registry_degraded.py`
- **Acceptance test:** a test points `OUROBOROS_REGISTRY` at an unwritable path, runs
  `mint --degraded-ok`, and asserts (a) exit 0, (b) one pending line, (c) the printed ref is
  the provisional ref, (d) a `transitioned` to `ratified` submitted degraded lands in
  `queued_privileged` and is **not** reflected by `fold()`.
- **Falsifier:** **invariant 6 breached** — a `ratified` (or `ready`) status becomes visible
  through any read path while the event sits unadmitted in the pending file. That is a
  blessing manufactured by an outage, which is strictly worse than the defect this design
  removes.
- **Invariant(s) it must not violate:** invariant 6, verbatim; invariant 9 (no secret).
- **Touches stored data?** Yes (pending file).
- **Parallelizable?** No.  **Depends on:** Item 7.

### Item 9 — reconcile: exactly-once binding, with a rename plan

- **Objective:** replay pending entries through normal admission; bind each provisional ref
  to a serial ref exactly once; report the file renames the binding implies.
- **Files:** `ops/registry/pending.py`, `scripts/registry.py`,
  `tests/integration/test_registry_reconcile.py`
- **Acceptance test:** `uv run pytest tests/integration/test_registry_reconcile.py -q`
  green: 12 pending entries reconcile to 12 serial refs; running `reconcile --apply` a
  **second** time yields zero new events and identical bindings; `queued_privileged`
  entries stay queued until an admission path exists (bp-145).
- **Falsifier:** a second `reconcile --apply` produces new refs or duplicate events. That
  observation is **F1's second clause** ("a timed-out-and-retried submit yields two refs")
  reached through the degraded door, and it voids the exactly-once claim of §2.2.
- **Invariant(s) it must not violate:** invariants 1, 2, 6.
- **Touches stored data?** Yes — registry store **and** pending file. Dry-run is the
  **default**; `--apply` is opt-in and must print the full report first.
- **Parallelizable?** No.  **Depends on:** Item 8.

### Item 10 — the recovery import and the F3 drill

- **Objective:** read the markdown tree back into the log (conflicts surfaced, never
  merged), and demonstrate that the owner can operate from the tree alone during a registry
  failure.
- **Files:** `ops/registry/recover.py`, `ops/registry/fold.py`, `scripts/registry.py`,
  `tests/integration/test_registry_reconcile.py`
- **Acceptance test:** `uv run scripts/registry.py import` (dry-run) against a scratch store
  and a fixture tree exits 0 and prints one line per artifact; a divergent front-matter
  status appears under `conflicts` and **no** event is written. Then the drill: with
  `OUROBOROS_REGISTRY` pointed at an unreadable path, `uv run scripts/registry.py query`
  exits 0, prints `source=tree degraded=true`, and returns the same rows the tree contains.
- **Falsifier:** **F3 (the new deadlock)** — any read blocks on the store, or the query
  raises instead of falling back, or the drill cannot answer from the tree. The design has
  then reproduced the hook defect and §2.9 has failed. Run the drill against a **locked**
  store as well as a missing one: hold an exclusive transaction from a second process and
  assert the read still returns within the busy timeout with `degraded=true`.
- **Invariant(s) it must not violate:** invariant 5; and the import never auto-merges
  (note §2.9(3)(i)).
- **Touches stored data?** Yes with `--apply`; **no** by default. The `--apply` path
  requires the dry-run report to have been printed in the same invocation.
- **Parallelizable?** No.  **Depends on:** Item 9.

## 8. Math carried explicitly

N/A — no mathematical object implemented. Exactly-once replay is a uniqueness constraint on
a key, not a mathematical object; its obligation is Item 9's falsifier.

## 9. Non-goals

- **No enforcement change.** No hook edited, none removed, `.claude/settings.json` untouched.
- **No export renderer and no CI ratchet** — bp-142 owns both. The read fallback in this
  plan points at the tree's *current* front matter; bp-142 is what makes that projection
  certified.
- **No signature verification.** Privileged events are recognized structurally (§6.3) and
  held; cryptographic admission is bp-145.
- **No migration of existing artifacts** — bp-143.
- **No `.gitignore` edit** — if `data/` is not ignored, stop and raise.
- **No automatic file renames.** Reconcile *reports* renames; performing them is the
  session's deliberate act, so a provisional-ref file never moves behind the owner's back.
- **No new dependency.**

## 10. Stop-and-raise conditions

- `git check-ignore` says `data/registry-pending.jsonl` is **not** ignored (§3 Q1) — stop;
  `.gitignore` is out of scope by design.
- bp-140's `submit()` raises rather than returning the existing seq on a duplicate key
  (§3 Q5) — file a `spec-defect` finding against bp-140 and stop; do not add a second
  dedupe layer to work around it.
- F3 trips in Item 10 — stop. A registry that can wedge the owner out is the defect this
  design exists to remove.
- An owner-level question (e.g. "should a pending mint survive worktree deletion?") — park
  the criterion with a re-entry condition and continue the others; never block on the owner.
- Any blessing this plan would have to perform — it must not.

## 11. Parked decisions

| Decision | Default recorded | Rejected alternatives (why) | Re-entry condition |
|---|---|---|---|
| Pending-file location | `data/registry-pending.jsonl` (per-worktree, gitignored) | a machine-level pending file — it would serialize across worktrees, defeating the point of a *local* fallback and reintroducing the single point of failure | Owner names another path, or `data/` stops being gitignored |
| Pending entries lost with a deleted worktree | Accepted loss (§3 risks) | a machine-level spool — same rejection as above | An actual loss costs real work; prerequisite: an observed incident |
| Fallback source before the export exists | the working tree's front matter as-is | waiting for bp-142 — would leave invariant 5 unmet for the whole interval, which is precisely "discovered during the first outage" | bp-142 lands; the fallback re-points at the certified export |
| Automatic rename of provisional-ref files | reported, not performed | performing them — a silent move of a file the agent is mid-edit on is a blast-radius surprise | Owner asks for it after using `reconcile` on a real batch |

## 12. Dependency & ordering summary

**Within the plan.** Item 7 → Item 8 → Item 9 → Item 10, strictly serial: each item's
falsifier presupposes the previous item's mechanism. Blast-radius order holds — Item 7
creates a gitignored local file; Item 8 writes only that file; Item 9 writes the registry
store under an opt-in `--apply`; Item 10's `import --apply` is the widest-radius act in the
plan and lands last, behind a mandatory dry-run.

**Across plans.** `depends_on: [bp-140]` — this plan extends bp-140's store, `Event`, and
CLI. It is **not** parallelizable with bp-142/bp-143/bp-146 (shared `ops/registry/**` and
`scripts/registry.py` scope). It **is** parallelizable with **bp-144**, whose scope
(`ops/transition_sig.py`, `ops/transition_keys/**`, `scripts/sign_transition.py`) is
disjoint and which the note's §2.5.2 declares independent of the registry. `bp-138`/`bp-139`
are independent of this whole family (note §3(5)).
