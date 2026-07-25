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

---

## 2026-07-25T08:05Z — Item 1 CLOSED (commit `df2f966`)

`docs/book/SYNC.md` `pending:` gained a ⚑ banner making the rule mechanical (every
id under a chapter row is ratified/superseded at HEAD), `pending.architecture` was
emptied (this edition discharges it), `pending.mathematics` was repopulated with
**ratified ids only**, and a new `forward-referenced:` block now holds the four
draft theses the book NAMES but never CITES, each with what is withheld and the
chapter it lands in on ratification.

Two findings filed with it — **finding-0183** (Ch.1 forward-promised the
three-channel taxonomy whose only source is the draft `dn-the-sacred-boundary`) and
**finding-0184** (the three-plane composition is load-bearing but lives in the draft
`docs/research/security-planes.md`, which is also `_lib.py:27`'s cited denylist
origin). Both `spec-defect` → orchestrator; both need the owner (ratification).

## 2026-07-25T09:40Z — Item 2 CLOSED: Chapter 2 written

`docs/book/chapters/02-architecture.tex`, ~1170 lines, **pages 6–23** of the PDF.
Four new TikZ figures. `notation.tex` extended (not forked); `preamble.tex` gained
`booktabs` plus `invariant` / `proposition` theorem environments with `\autoref`
names.

**The spine** (motivation → prerequisites → idea → what it unlocks → why it
matters, per the owner's voice brief): Ch.1 left the principle *dissolve, don't
guard*; Ch.2 asks **where** you put a boundary so the dangerous permission becomes
unnecessary — and answers that the same move is made at five scales (processes, OS
users, modules, types, queries), graded throughout by the **enforcement-tier ladder**
(`dn-capability-scope` §2.2, `structural ≻ static+guard ≻ convention`, min along the
chain). §2.9 then states every residual, sourced to the note that owns each
mechanism. The framing is flagged in-text as the manual's own synthesis and is
anchored on `dn-inner-outer-core` §2.8's explicit same-geometry claim.

**Sections:** tiers · zones (BUILD-SPEC §6; the handoff as an inert spool, the
airlock asymmetry) · the import firewall (the math, below) · planes
(`dn-plane-principals`, with a `devolution` remark carrying the superseded
two-principal model + finding-0116 warrant; the pf snippet) · rings (the greatest
import-closed subset; declaration-forced-to-equal-a-computation) · types
(Curry–Howard, the two obligations, the static shadow, the self-growing Tier-2) ·
scope (⊤_Σ = R∖𝔇; meet = delegation; **firewalls as ideals = "dissolve, don't guard"
in lattice theory** — the chapter's best synthesis beat) · workflow-as-a-zone
(write_scope as capability; clause family (a)–(f); derivation-instead-of-enforcement;
the exhaust one-way invariant closing Ch.1's ouroboros loop) · residuals.

### ⚑ The one place I nearly invented something — read this before touching §2.3

My first draft stated the import firewall's guarantee as
`Reach(core) ∩ N ⊆ Reach(allowlist) ∩ N` and "proved" it. **That is false.**
`ops/import_lint.py` (`scan_file` → `_imported_names`) checks **direct imports
only**; it does not walk a closure. The closure claim in its docstring is a true
*conditional*, and its antecedent is discharged only under

  (⋆) every module core reaches outside `core/` is stdlib or a pinned pure library

— which is exactly `tests/unit/test_core_self_containment.py`, **red by design**
(finding-0103). Rewritten honestly: Invariant 2.1 = the local condition;
Proposition 2.1 = "every escape route is visible" (proved); (⋆) named explicitly;
Proposition 2.2 = the unconditional closure **at the limit**. Filed
**finding-0185** (`discovery` → orchestrator): the firewall and the
self-containment ratchet are the two hypotheses of one theorem, which reclassifies
finding-0103 as a safety-discharge item, not only hygiene.

### Grounding corrections made against the live code (do not undo)

- `core/kernel/scope.py` **is built** — so the C fiber is no longer a proposal
  (`E ⊆ {F,D,C}`), the forest carries a `dialogue` stratum with `exhaust`
  default-excluded (`dn-agentic-loop` §2.4b, ratified), and the module's own header
  says it "wires NO enforcement into any read path — it is vocabulary, not a gate."
  That last line is now a residual bullet in §2.9.
- The pf anchor file is **inert until owner-loaded**; the text says so rather than
  implying the migration is complete. bp-078 is `complete`, the three role accounts
  exist on this host, and `scripts/verify_planes.py` reports PENDING mid-migration.
- `INNER` is **43** members at `009b726` (counted by AST, not trusted from a
  comment). No stale ratchet number is asserted in the chapter — the 19→0 figure is
  attributed to `dn-inner-outer-core` §2.4 rather than claimed as current.

### External references — VERIFIED, never from memory

Four, each confirmed in-session against DOI/CrossRef metadata (title, venue,
volume, pages, year, authors) and footnoted with its DOI: Tarski 1955
(`10.2140/pjm.1955.5.285`), Wadler 2015 (`10.1145/2699407`), Lamport 1978
(`10.1145/359545.359563`), Chandy & Lamport 1985 (`10.1145/214451.214456`).
No bibliography package was added — footnotes keep the compile risk at zero.

## 2026-07-25T10:20Z — Item 3 CLOSED: whole-book review + re-key

**Every** citation checked, not spot-checked (260 commits had passed):

- 12 distinct `\coderef` paths — all resolve at `009b726` (`git cat-file -e`).
- 16 distinct `\artifact` ids — all resolve; 9 ratified, 1 superseded (marked as
  such at every use), 6 findings present on disk. **Zero draft ids cited anywhere.**
- ~34 distinguishing prose quotations machine-checked against their sources with
  whitespace normalisation; all present verbatim.
- Snippets: Ch.1's `PRE_DECLARED_MAX` is byte-identical at `roles.py:24`; Ch.2's
  `FORBIDDEN_ZONES`/`NETWORK_ALLOWLIST` are byte-identical (elision between them now
  marked); the pf rules match `:43-44`. The session-handoff block condition was
  relabelled from `source:` to **restatement** because I had abbreviated its paths —
  a labelled copy must be a copy.

**Chapter-1 drift found (the one meaning-affecting item):**
`dn-ouroboros-principal` flipped `ratified → superseded` (→ `dn-plane-principals`,
warrant finding-0116) since `bdcd9bc`. All three Ch.1 citations repaired in place to
cite it *as superseded* and name the successor; Ch.2 carries the transition as a
`devolution` remark ("provenance as pedagogy", book skill). Ch.1's sacred-boundary
forward promise was downgraded to `\fwdthesis` (finding-0183). Everything else in
Ch.1 was typographic: two figures adjusted (an overfull box and a bold-small-caps
font substitution, both pre-existing at `bdcd9bc`).

**SYNC.md re-keyed:** `git-ref: bdcd9bc → 009b726` (and `\gitref` in `preamble.tex`
with it — *this is easy to miss; every `\coderef` renders through that macro*);
`incorporated` expanded to the full source set with per-file `@009b726` pins, the
findings cited as content, and a new `external-references` block carrying the four
verified DOIs; `chapters-present: [01-philosophy, 02-architecture]`; new `figures`
and `notation-additions` blocks; the `open` block now carries all three findings
with explicit re-entry conditions plus a verification note for the next scribe.

**Compile (the recorded toolchain — tectonic is NOT installed):**
`cd docs/book && latexmk -pdf main.tex` → **rc=0, 26 pages**. Final pdflatex pass:
**zero** errors, warnings, undefined references, font substitutions, and
overfull/underfull boxes. `main.pdf` (724 KB) is present in the worktree and is
gitignored by `docs/book/.gitignore` (source-only commits, bp-077 §9).

**Local CI gate: N/A.** The change surface is `docs/book/**` + `docs/findings/**` +
this journal. No Python, no config, no hooks touched — verified with
`git status --porcelain -uall`.

### For the next scribe

Remaining debt is chapters 3–5, listed in `SYNC.md` `pending` with **ratified ids
only**. If the owner ratifies `dn-the-sacred-boundary` or a successor (finding-0183),
Chapter 2 gains the channel taxonomy and Ch.1's `\fwdthesis` reverts to a citation.
If `security-planes` is promoted and ratified (finding-0184), Ch.2's organizing
frame becomes a cited thesis instead of the manual's own reading. Plan status is
NOT flipped — that is the orchestrator's.
