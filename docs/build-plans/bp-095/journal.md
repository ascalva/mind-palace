# bp-095 journal

## 2026-07-21 — minted (graduation, session-41)

Graduated from ratified dn-code-ingest-pipeline (0c2deae; fable-audited, finding-0147)
per §3. Status: proposed — awaiting the owner's proposed→ready hand-bless. No work
performed. Grounding computed at graduation is recorded in the plan's §3.

## 2026-07-26 — SEAL (no-build disposition; delegated builder, worktree agent-a8b4f5ac5fdd34fcb)

**Status line.** bp-095 **REFUSED AT ITS OWN §10 GATE and was not built** — the M-C4 verdict is
PARKED (unread), which §10 names verbatim as a do-not-start. `finding-0221` (`blocker`, routed
to orchestrator) is the recorded disposition; the plan is left **`ready`**, un-started. Zero
lines of the lens were written. The gate worked exactly as designed.

**Step 0 — bind + ground.** Base `7941da1` (`origin/main`, verified — `merge(bp-123 Items 1+3):
the overlay is config/ouroboros.toml`), branch `worktree-agent-a8b4f5ac5fdd34fcb`. `uv sync
--frozen --extra dev` (fresh worktree lacked dev extras). `active-plan` = `docs/build-plans/
bp-095/plan.md` (verified). `config/` holds neither `ouroboros.toml` nor the refused legacy
`local.toml` — no `ConfigMigrationError` encountered, nothing worked around. Read whole: plan
§0–§12, `CLAUDE.md`, the finding + checkpoint skills, the §2 manifest in order (below).

### The gate read — UNREAD, a third state the `re_entry` never contemplated

Plan §10: *"The M-C4 gate unread or degenerate (do not start; flip per `re_entry`)."*
Front-matter `re_entry`: *"M-C4 verdict = informative (bp-093 journal) — if degenerate, this
plan is superseded by a finding, never built."* bp-093's journal gives neither verdict:

- `bp-093/journal.md:70` — heading **"M-C3 / M-C4 REAL verdicts — PARKED (re-entry: the
  owner-visible seed run)"**; line 76 re-entry: run `run_mc4(store)` on the seeded store.
- The lone `INFORMATIVE` string there (line 63) is a **unit-test case name** over the
  deterministic **fake** embedders — proof the verdict logic discriminates, **not** a reading.
  Reading it as the gate's "informative" would have been the session's one available
  false-green; it was checked precisely because it is the tempting misread.
- Independently corroborated by the orchestrator: `PROGRESS.md:5379` — *"bp-095 (CI-4) is
  **GATED, not built**"*; `:5381` — *"M-C4 is PARKED (needs the real qwen3 seed run)."*

Searched for any post-bp-093 real verdict (2026-07-22 → today) across `docs/`, `TRACKS.md`,
`PROGRESS.md`, `tracks/code-ingest.md`, and all four CI plans/journals: **none exists**.

**Why not flip `superseded`.** `re_entry`/§0 license `superseded` **only** on a *degenerate*
reading. Unread ≠ degenerate: flipping would fabricate a negative verdict from an absent one
— reporting a null as a result, which this project forbids. Left `ready`.

### The new reading — both join populations are provably EMPTY (the finding's substance)

The lens is a join of S (code↔note cosines) against F (resolved code↔corpus edges). Measured
read-only on this machine today — **both sides are empty at the source**:

| Population | Evidence | State |
|---|---|---|
| S — code vectors | **no** LanceDB/vectorstore dir anywhere under `~/.mind-palace/` (only `vault/`, `exhaust/`, three 0-byte sqlite files) | empty — corpus never seeded (bp-092 parked the seed) |
| F — resolved code↔corpus edges | `~/.mind-palace/reference_edges.sqlite` = **0 bytes**; `ops/code_sensor.py:154` `ENABLED_L2B_PATTERNS: frozenset[str] = frozenset()` (*"empty = all off"*) | empty — patterns ship DISABLED; bp-094 Item 2 (M-C6 enable) parked on owner/deskcheck |

Plan §3 predicted an empty/thin first read was *"LIKELY."* It is not likely — it is **certain**,
for **two independent reasons, only one of which the gate encodes**. Hence the finding's
recommendation: widen `re_entry` to a conjunction (informative M-C4 **AND** a non-trivial
F-population), promoting into the gate the validity condition the plan's own §8:117 already
names — *"valid when: … F-population non-trivial."* An informative M-C4 is a geometry reading
over **vectors** and would go green on a seeded corpus while F stayed zero (patterns off), so
M-C4 alone is a reachable false-green that would license an instrument no reading ever
exercised. That plan-front-matter edit is the orchestrator's, not a builder's.

### Survey readings — HONEST NULL (no run performed, and why that is the correct null)

**No M-C7 reading was taken; the lens does not exist.** The null is *structural*, not a failed
measurement: §10 forbade starting. Had the lens been built and run today, §6's honest-seam law
(*"zero claims when either population is empty"*) guarantees its only possible output is
**zero claims in both mismatch tables** — undocumented-realization: 0; drift: 0 — and §7's
acceptance test would have passed **vacuously** over an empty set while §8's keep-condition
stayed unevaluable. A green suite over an unfalsifiable instrument is the outcome §10 exists to
prevent.

**Why the gate was not opened by this builder, though the tooling was present.** Ollama *is*
reachable and `qwen3-embedding:4b` *is* pulled locally (checked) — so the blocker is the
owner-owed act, not tooling. Opening it would have required one of three scope breaches:
seeding the real corpus (a **large mutation of stored data**, against a plan whose §7 says
*"Touches stored data? no"* and §5 *"read-only against every store"*, `write_scope` = `eval/**`);
enabling `ENABLED_L2B_PATTERNS` (bp-094 Item 2's owner-gated M-C6 act); or performing the
seed run reserved as the track's owner-visible deskcheck (`PROGRESS.md:5408-5411`). Each would
have manufactured the very signal that licenses the build — the inversion §9 forbids (*"No
thresholds tuned to manufacture signal"*). Refusing is the deliverable.

### Item 1 — the lens + M-C7 first read — **NOT STARTED** (§10 do-not-start)

Not attempted; not partially attempted. Verified nothing exists in `write_scope`:
`eval/code_sf_lens.py` absent, `tests/unit/test_code_sf*` absent, `eval/harness/` unchanged
(16 pre-existing modules, none touched). Acceptance test, falsifier and invariants are all
**unexercised** — correctly, since the criterion never opened.

**Completed:** the gate read + the empty-population survey + `finding-0221` (both in the commit
below). **In-flight:** nothing. **Non-goals honored:** no census/narration wiring, no
thresholds tuned, no correlator work, no edges minted, no store written.

### The full attestable-green gate (this worktree; docs-only diff, so a no-regression attestation)

- `uv run ruff check .` → **All checks passed!**
- `uv run python scripts/check_imports.py` → **Import firewall (I2): OK**
- `uv run mypy core agents eval ops scheduler scripts` → **Success: no issues found in 258 source files** (0 errors)
- `uv run mypy` (argless) tail → **Found 69 errors in 20 files (checked 550 source files)** — == baseline 69 ✓
- `uv run python -m ops.type_gate` → Tier-2 membership OK; bare-ignore scan OK
- `uv run pytest -q -m 'not live and not podman and not needs_vault and not needs_restic' --deselect
  'tests/unit/test_core_self_containment.py::test_core_imports_nothing_outside_core'` →
  **2102 passed, 11 skipped, 21 deselected, 12 warnings in 73.90s** — **0 failed**

**Next action.** Orchestrator: (1) rule on the `re_entry` conjunction in `finding-0221`
(batch to `owner-questions.md` if the owner's call is wanted; the `default_if_unanswered`
degrades to the parked state, so nothing stalls); (2) confirm bp-095 stays `ready`; (3) at the
owner's CI-1 seed/deskcheck window, run `run_mc4(store)` and record the verdict in bp-093's
journal — `informative` (+ a non-trivial F-count) reopens this plan for a real build,
`degenerate` fires F-CI4 and flips it `superseded` per `re_entry`.

**Open questions.** One, typed + routed: `finding-0221` (`blocker` / direction → orchestrator),
carrying its three-clause re-entry condition. No owner-blocking wait introduced.

**Context-manifest delta.** Manifest items read in order: (1) `dn-code-ingest-pipeline`
§2.4/§2.8 M-C7/F-CI4 + §3 CI-4; (2) `dn-fiber-geometry` §2.2/§2.6 — *read only as far as the
gate decision needed*: the S↔F definition and the falsifier discipline were confirmed, but the
M2 mismatch-density protocol was **not** mined for implementation detail, since no
implementation was licensed; (4) `bp-093/journal.md` **whole** (the gate — load-bearing).
Item (3) `core/graph/composed.py` `edge_classes` **deliberately NOT read** — it is
implementation grounding for a build that §10 forbade; reading it would have been pre-work
toward a refused criterion. Beyond the manifest: `bp-092/journal.md`, `bp-094/journal.md`
(F-substrate dormancy, `:87`), `bp-093/plan.md`, `PROGRESS.md` §CI wave, `TRACKS.md:31`,
`docs/tracks/code-ingest.md:38`, `ops/code_sensor.py:88-154`, `core/stores/reference_edges.py:105`,
`config/defaults.toml:117-121`, `eval/harness/` listing, `~/.mind-palace/` tree, the local
Ollama model list. Proved irrelevant: `eval/harness/code_retrieval.py` internals (the M-C4
implementation — its *verdict record*, not its code, is the gate).

```read-map
docs/build-plans/bp-095/plan.md:29: the re_entry gate — "M-C4 verdict = informative … if degenerate, superseded, never built"; licenses `superseded` ONLY on degenerate
docs/build-plans/bp-095/plan.md:128: §10 stop-and-raise, verbatim — "The M-C4 gate unread or degenerate (do not start)"; the clause this session executed
docs/build-plans/bp-095/plan.md:117: §8 validity — "F-population non-trivial"; the condition the front-matter gate omits (the finding's recommendation)
docs/build-plans/bp-095/plan.md:94: §6 honest-seam law — zero claims when either population is empty; why a build today emits nothing
docs/build-plans/bp-093/journal.md:70: THE GATE — "M-C3 / M-C4 REAL verdicts — PARKED"; verdict unread, so neither re_entry branch applies
docs/build-plans/bp-093/journal.md:63: the tempting false-green — "M-C4 INFORMATIVE" here is a FAKE-embedder unit-test case name, not a reading
docs/build-plans/bp-093/journal.md:76: bp-093's own re-entry — run run_mc4 on the seeded store; a degenerate M-C4 is a FINDING, never a silent tune
docs/PROGRESS.md:5379: orchestrator already recorded "bp-095 (CI-4) is GATED, not built" — independent corroboration
docs/PROGRESS.md:5381: "M-C4 is PARKED (needs the real qwen3 seed run)"
docs/build-plans/bp-094/journal.md:87: F-substrate for bp-095 is DORMANT — patterns flag-gated off, Item 2 parked
ops/code_sensor.py:154: ENABLED_L2B_PATTERNS = frozenset() "empty = all off" — the F-population mints nothing, so F ≡ 0
docs/design-notes/code-ingest-pipeline.md:620: F-CI4 — degenerate code↔doc neighborhoods ⇒ the supersession branch, for contrast with UNREAD
docs/findings/finding-0221.md:1: the disposition — blocker/direction, the two-clause gate recommendation, the three-clause re-entry
```

## Follow-through

- **Built?** **No — deliberately nothing.** bp-095 refused at its own §10 gate ("do not start")
  because the M-C4 verdict is PARKED/unread (`bp-093/journal.md:70`), not `informative`.
  `eval/code_sf_lens.py`, `eval/harness/**` additions and `tests/unit/test_code_sf*` were **not
  created** — verified absent. The session's product is a gate read, a grounded
  empty-population survey, and `finding-0221`. Item 1 is NOT STARTED, not partially built.
- **Wired / delivered (or why dormant)?** N/A — no code, so nothing to wire. The *finding* is
  delivered and routed. bp-095 is left **`ready`** (not `in-progress`, not `superseded`, not
  `complete`): `superseded` is licensed only by a *degenerate* reading, and asserting one from
  an absent reading would report a null as a result.
- **Does a consumer use it?** No consumer, because there is no artifact. Conversely bp-095 is
  itself the blocked consumer: it needs bp-092's seed (S) and bp-094 Item 2's enabled,
  projected F-edges (F) — `reference_edges.sqlite` is 0 bytes and no vectorstore exists, so
  **both** its inputs are empty. `finding-0221` is consumed by the orchestrator.
- **Track state (what remains on this track)?** code-ingest: CI-1 (bp-092), CI-2 (bp-093),
  CI-3 (bp-094) sealed; bp-098 (the enable path) sealed. **CI-4 (bp-095) remains OPEN and
  un-started** — the CI program's tail is NOT disposed, contra a "wave complete" reading.
  Owner-owed and unchanged by this session: the CI-1 seed run / code-ingest deskcheck (the
  linchpin that discharges bp-092's seed, bp-093's M-C3/M-C4 verdicts, bp-094's 1.1.0
  re-projection, and this gate at once), bp-094 Item 2's M-C6 enable, and integrator
  densification (finding-0151).
- **Opened a new track/finding?** Yes — **`finding-0221`** (`blocker`, route `orchestrator`,
  direction). No new track. Two asks: rule on widening `re_entry` to *informative M-C4 AND
  non-trivial F-population* (promoting §8:117 into the gate, closing a reachable false-green),
  and confirm the `ready` disposition. **No spec-defect** against `dn-code-ingest-pipeline` —
  §3 CI-4 and F-CI4 are self-consistent and the double gate did its job; the gap is narrowly
  in bp-095's front-matter `re_entry`.

**NOT ready to deskcheck** — there is nothing built to deskcheck. This seal closes a *no-build
disposition*, not a delivery; bp-095 is not `complete` and must not be flipped so. It is the
orchestrator's to re-open once the gate reads. Do not add this to `docs/DESKCHECK-QUEUE.md`;
the track's already-queued code-ingest deskcheck (the seed run) is what unblocks it.

## Orchestrator note — 2026-07-26, merge-time correction to `7ab5187`'s commit message

⚑ **`7ab5187`'s body is corrupted and this is the correction of record.** I passed that merge message
via an inline `-m` string containing backticks, and zsh performed command substitution on them, so two
words were silently deleted before the commit was written (`(eval):1: command not found: superseded` /
`... not found: ready`). The two damaged sentences should read:

- *"It also declined to flip **`superseded`**, because `re_entry` licenses that only on a DEGENERATE
  reading — and unread is not degenerate."*
- *"Plan left **`ready`**, untouched."*

Both statements are true of the merged tree: `docs/build-plans/bp-095/plan.md` is still
`status: ready` and nothing was flipped.

**Not amended deliberately.** A force-push would rewrite a pushed commit on `main` while two sibling
builders are live, and it would *not* clean the code-sensor ledger — `code_snapshots.sqlite` already
ingested the corrupted body at commit time, so amending would leave both versions there and only
tidy `git log`. Recording the correction where a reader of bp-095 will find it keeps the record
honest in both places, which is the standing preference here (auditability over tidiness).

**The lesson, for the next session:** every other commit today used `git commit -F -` with a heredoc
and was fine. This one was inlined. **Use `-F -` whenever a message contains backticks** — the repo's
commit style is full of `code refs`, so the hazard is structural rather than incidental.
