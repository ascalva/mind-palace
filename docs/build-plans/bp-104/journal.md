# Journal — bp-104 (scribe: book sync, Chapter 2 Architecture)

Worktree: `.claude/worktrees/agent-aba53f32a3c9ff4f8`, branch
`worktree-agent-aba53f32a3c9ff4f8`. Delegated scribe. Write scope: `docs/book/**`
(+ this journal, + new `docs/findings/**`).

---

## 2026-07-25T07:50Z — session start; worktree fast-forwarded; sources ground-checked

**Worktree was stale.** It was created at `ed72554`, two commits before the plan
existed. `git merge --ff-only main` fast-forwarded to `009b726` (the bless commit).
`docs/build-plans/bp-104/plan.md` now present. **The edition ref for this sync is
`009b726`** — every `\coderef` and snippet below is verified at that ref.

### Read (in the plan's §2 order)

plan.md · book skill · `docs/book/SYNC.md` · `chapters/01-philosophy.tex` ·
`main.tex` / `preamble.tex` / `notation.tex` · `dn-agent-workflow` §3 and §6 ·
then the §2 source list.

### Status sweep of every candidate source (verified on disk at `009b726`)

RATIFIED and citable: `dn-plane-principals`, `dn-type-system-as-core-audit`,
`dn-capability-scope` (**note: the file is `capability-scope-algebra.md` but its
`id:` is `dn-capability-scope` — cite the id, not the filename**),
`dn-agent-taxonomy`, `dn-session-handoff-gate`, `dn-exhaust-lane`,
`dn-track-board-and-deskcheck-gate`, `dn-inner-outer-core`, `dn-agent-workflow`.

SUPERSEDED (citable, but only *as* superseded, naming the successor):
`dn-ouroboros-principal` → `superseded_by: dn-plane-principals`, warrant
`finding-0116`.

**BARRED (draft) — confirmed:** `dn-the-sacred-boundary`, `dn-the-edge-model`,
`dn-authorship-distance-axis`, `dn-founding-corpus`. Also barred and worth
recording because a ratified note leans on it: `docs/research/security-planes.md`
is `type: research, status: draft` — so the three-plane composition is **not**
citable, even though `dn-type-system-as-core-audit` §1.1 references it. Chapter 2
therefore takes the type material only from the ratified note's own text.

### Grounding of the code claims (all re-verified at `009b726`)

- `ops/import_lint.py` — `FORBIDDEN_ZONES = {edge, cloud}`; `NETWORK_MODULES`;
  `NETWORK_ALLOWLIST = {core/sealing.py, core/models/ollama_client.py}`. Docstring
  carries the composition argument verbatim.
- `scripts/check_imports.py` — thin CLI over `ops.import_lint.main`. **Chapter 1's
  citation still resolves.**
- `core/factory/roles.py:24` — `PRE_DECLARED_MAX: frozenset[str] = frozenset({"run_python"})`.
  **Chapter 1's snippet is byte-accurate at HEAD.**
- `core/sealing.py` — the in-process fail-closed egress guard (loopback + AF_UNIX only).
- `ops/network/ouroboros-egress.pf.conf:43-44` — the two-line pf anchor. **Built.**
- `core/kernel/rings.py` — exists; INNER is 43 members; the ring physically lives at
  `core/kernel/**` (K1 = bp-090, K3 = bp-091 have landed). `tests/unit/test_inner_ring.py`
  forces declared == computed.
- `core/typedshims/{lancedb,psutil,sknetwork}.py` — the boundary wrappers are built.
- `.claude/hooks/_lib.py` — `DENYLIST` at :35; `cmd_scope_check` at :415;
  Stop-audit clauses (a),(b2),(c),(d),(e),(f) all present.
- `scripts/verify_planes.py`, `tests/unit/test_plane_migration.py`,
  `docs/runbooks/plane-migration.md` — bp-078 `complete`. The three role accounts
  **exist on this host** (`dscl . -list /Users` shows `ouroboros`, `ouroboros-work`,
  `ouroboros-edge`), so the plane split is migrated, not merely designed.
- `config/defaults.toml:55-65` — the `[exhaust]` block; `tests/unit/test_exhaust_report.py`
  asserts the ingest invariant.

### ⚑ Two problems found before writing a line

1. **SYNC.md `pending.architecture` lists two DRAFT ids as sources**
   (`the-sacred-boundary`, `the-edge-model`) — exactly the finding-0117 trap.
   Item 1 fixes it.
2. **Chapter 1 makes a forward promise Chapter 2 cannot keep from ratified sources.**
   `01-philosophy.tex:97-98`: *"The full taxonomy of the three channels that cross
   the core's boundary is architecture; \autoref{ch:architecture} gives it."* The
   only source for that taxonomy is `dn-the-sacred-boundary` §1 — **draft**. Two
   consequences: (a) Chapter 1 needs a minimal cross-reference repair (licensed by
   Item 3, "any Chapter 1 cross-reference fixes"); (b) a finding is owed.
   Also: Chapter 1 cites `dn-ouroboros-principal` §1/§2 as if current — it is now
   `superseded`. Repair = cite it *as* superseded + name `dn-plane-principals`, and
   carry the change as a design-evolution remark (book skill, "provenance as pedagogy").

**Next:** Item 1 (SYNC.md correction), then Item 2 (the chapter), then Item 3.
