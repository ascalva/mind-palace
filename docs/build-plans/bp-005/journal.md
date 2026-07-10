# BP-005 — Build journal

Records the corpus front-matter conversion: prepending machine front-matter to
notes that lacked it, landing at `status: draft`, prose untouched. **Outcome: both
halves landed — 3 research + 30 design notes converted; design notes additionally
carry an `implementation:` stamp from the 2026-07 verification audit.** The
design-note half was first blocked by the `docs/design-notes/**` foundation
denylist and reverted; the owner then lifted that path from the `DENYLIST` and it
was re-run. Narrative entries are newest-first; `## Markers` at the end receives
hook-appended lines.

Fresh-agent test (§9): a session given only `plan.md` + this journal + the
write-scope files must continue without re-asking anything already answered.

---

## Seal — 2026-07-09 — /triage — bp-005 `complete`, journal sealed

**Seal.** Plan flipped `in-progress → complete` (`plan.md:4`) and this journal sealed by
`/triage`, 2026-07-09. The work itself landed earlier: the owner committed the conversion
(`66c3e6f` on `claude-convert-notes`, merged to main at `a33ecab`) — 30 design + 3 research
notes converted (+13/−0 prepends, prose untouched), design notes stamped with the 2026-07
verification audit's `implementation:` verdicts, denylist temp-lift restored (`d6e518f` →
`f5d435d`). **But this journal and `finding-0023.md` were left untracked in the
`mp-convert-notes` worktree** — the commit the previous entry requested never included them —
so the plan sat unsealable with its results (incl. Appendix A, the 204-hit supersession-marker
inventory that seeds `supersession-recovery-evaluation.md` §3) at risk of loss to worktree
cleanup. This sweep recovered both files to main and committed them. Verified at seal: all 43
notes under `docs/design-notes/` + `docs/research/` carry front-matter (the three post-bp-005
notes self-carry it at `draft` — the convention took hold). finding-0023 routed → oq-0010
(research-note schema ratification). No narrative entries after this line.

---

## Entry — 2026-07-08 — denylist RESTORED by owner; conversion complete and awaits commit

**State.** The owner re-added `docs/design-notes/**` to the `DENYLIST` (committed:
`d6e518f` temp-lift → `f5d435d` re-add; HEAD now carries the restored denylist).
The 30 design-note conversions (below) are **complete and owner-desired** but sit
**uncommitted** in the worktree, so the Stop-gate correctly flags them again as
foundation-file modifications — this time they are wanted changes, not a violation.

**How this clears (do NOT revert — the changes are desired).** A committed
design-note change is the constitution's "deliberate, logged" act (§9) and is
accountable to its committer; once committed it leaves the working-tree-vs-HEAD
delta and the `(b)` foundation check passes (same mechanism that cleared when the
earlier revert emptied the delta). So: **commit the conversion** (owner's hand, or
owner-authorized) — 30 design + 3 research notes + `plan.md` + this journal +
`finding-0023.md`. This checkpoint re-touches the journal so it post-dates HEAD,
clearing the `(a)` staleness reason; `(b)` remains only until the commit lands.

**No further edits needed** — the work below is final and verified.

---

## Entry — 2026-07-08 — deny lifted → 30 design notes converted+stamped; mid-session addendum (items 1–4) applied; finding-0024 deleted

**Status.** Build complete on both halves. The owner lifted `docs/design-notes/**`
from the `DENYLIST` (`_lib.py:34`, now commented out) — resolving the collision the
previous entry parked — so the 30 design notes were converted **with** the
addendum's item-2 implementation stamp in one pass. Plus a mid-session addendum
(supplied after `/build` began; the plan body was only §1+§5) added three
enrichments + a record repair, now appended to `plan.md` as "Addendum (supplied
mid-session)". Stop-gate standalone audit → **ALLOW** (verified end of run). Plan
left `in-progress` for `/triage` to seal (convention: triage seals `complete`).

**Worktree delta (all in `write_scope`).** 30 M design notes + 3 M research notes
+ `plan.md` (status flip + re_entry reset + Addendum) + this journal + `finding-0023.md`.
`finding-0024.md` **deleted** (owner-instructed: the denylist lift resolved it).

### Conversion + item-2 stamp (30 design notes)
Each a pure **+13 / −0** prepend (12-line FM block + blank), prose md5 preserved
(verified per file; `git diff --numstat` = `13 0` on all 30; deletion grep empty).
FM: `type · id: dn-<slug> · status: draft · implementation: <verdict>   # corpus-audit
2026-07 verification · created · updated · links: [] · supersedes/superseded_by/warrant:
null`. Verdicts sourced verbatim (kebab-cased) from
`docs/audits/corpus-state-audit-2026-07-verification.md`:

- **built-wired (6):** dreamer-quality-suite-evaluation, founding-corpus,
  ingest-identity-and-amendment, test-organization, vault-sync-and-capture,
  verdict-authority.
- **present-not-wired (6):** dialogue-ingest-and-recursion, dreaming-v2-interpreter-panel,
  hands-and-the-effector-layer, skill-mining-pipeline, skills-and-scope,
  **the-edge-model** (the audit's *one* status change — BUILT&WIRED→PNW, §1, a
  rigor correction: `build_complex` is flag-off-only).
- **partial (13):** alignment-subsystem, attestation-layer, dream-phase-rnd-charter,
  effector-risk-computation, holistic-testing, nervous-system-and-ambassador,
  observed-data-and-the-assistant-tier, observed-iot-and-cross-source-synthesis,
  recursive-dreaming-bounded-by-grounding, recursive-strata, roadmap-and-future-directions,
  supersession-lifecycle, wasm-sandbox-runtime.
- **not-built (3):** dreaming-on-curated-graphs, live-adoption-and-longitudinal-harness,
  stability-adjudication.
- **design-only (2):** the-sacred-boundary, recursive-strata-amendment — no verdict
  in the *verification* audit (it only diffs the prior); both are `N/A-DESIGN-ONLY`
  in the prior audit (`corpus-state-audit-2026-07.md:157,360` — spine/principle note;
  patch-spec with edits unapplied), a disposition the verification pass left
  unchanged. Comment: `# corpus-audit 2026-07 (N/A-design-only)`. **Not guessed** —
  it is the audit's own N/A ruling.

**Gap journaled — 3 research notes get NO `implementation:` field.** planar_graphs,
security-planes, un-represent-ability are literature surveys, "statusless"
(finding-0017), and not doctrine/philosophy → per the addendum rule (no verdict +
not doctrine ⇒ omit + journal the gap). They keep their earlier front-matter
unchanged.

**7 pre-existing-FM design notes are NOT in the conversion set** (they already had
front-matter; the `head -n1 == "---"` guard skipped them) and were left untouched —
several are ratified/superseded and re-editing them is out of scope. Their
would-be verdicts, for owner reference if a later pass stamps them: agent-workflow
built-wired · ambassador-as-reasoning-agent built-wired · ambassador-interpretation-and-flow
built-wired · core-integrity not-built · secrets-management-evolution partial ·
vault-runtime-auth present-not-wired · supersession-recovery-evaluation
no-verdict (2026-07-06 eval-design note, absent from the audit).

### Item 1 — supersession-marker prose inventory (seeds the scrub-pattern file)
Method: case-insensitive stem grep over **all** of `docs/design-notes/**` (incl. the
`build-plans/` subdir) + `docs/research/**`, front-matter `supersedes`/`superseded_by`
/`warrant` field-lines excluded. **204 genuine-stem hits** (stems: `supersed`,
`takes precedence`, `authoritativ`, `corrected`, `correct but incomplete`,
`replaces`/`replaced by`, `in favor of`, `retire`, `overrid`). Complete verbatim
`file:line:text` list in **Appendix A**. **0 hits in `docs/research/`** — the surveys
carry no supersession markers.

**Sanity check PASSED** (the three the addendum said must hit):
ambassador-interpretation-and-flow banner `:20–22,32`; secrets-management-evolution
banner+Status `:17–20,27`; vault-runtime-auth Status "Supersedes …" `:18–19`.

**Tier A — edge-leakage (a note names a specific supersession/authority relation
over another note; these are the must-scrub lines for the blind fixture):**
- `secrets-management-evolution.md:17` `> **⚠️ SUPERSEDED (2026-07-07).** \`vault-runtime-auth.md\` is the authoritative Vault`
- `secrets-management-evolution.md:18` `> note and takes precedence wherever the two differ. …`
- `secrets-management-evolution.md:20` `> (its own words: this note was "correct but incomplete"), …`
- `secrets-management-evolution.md:27` `**Status:** superseded by \`vault-runtime-auth.md\` — see banner. …`
- `vault-runtime-auth.md:18` `**Status:** design only. Supersedes \`secrets-management-evolution.md\` (which framed`
- `vault-runtime-auth.md:19` `Vault as a multi-machine secrets store — correct but incomplete). …`
- `ambassador-interpretation-and-flow.md:20` `> **⚠️ PARTIALLY SUPERSEDED (2026-06-28).** \`ambassador-as-reasoning-agent.md\` is the`
- `ambassador-interpretation-and-flow.md:21` `> **authoritative** Ambassador note and takes precedence wherever the two differ. …`
- `ambassador-interpretation-and-flow.md:22` `> … the **"thin dispatcher"** framing below is _corrected_ there …`
- `ambassador-interpretation-and-flow.md:32` `> … read this note for those, and the reasoning-agent note for the corrected`
- `ambassador-as-reasoning-agent.md:22` `… The corrections here take precedence where they differ from the earlier` (pre-existing-FM note; still inventoried)
- Banner-style, inside the amendment/build-plan record (reconciliation banners naming a supersession on a note/plan): `recursive-strata-amendment.md:57` block; `edge-and-supersession-build-plan.md:48,367–371` ("⚠ Partially superseded (edge-model reconciliation …)").

**Tier B — mechanism/vocabulary (the word `supersede`/`supersedes` as load-bearing
domain vocabulary and *code identifiers* — NOT an inter-note edge).** A naive scrub
of the token would gut these without removing any edge. Coverage (file → count):
the-edge-model 17 (E_disp taxonomy: note-version `supersedes` vs claim `supersede`
vs authored-historical `supersede`), ingest-identity-and-amendment 14, supersession-lifecycle
13, agent-workflow 12 (lifecycle schema `draft→ratified→superseded`, three-place plan
supersession), recursive-strata-amendment 12, supersession-recovery-evaluation 8
(**describes the scrub itself, §3 — see `:61–66`**), dialogue-ingest-and-recursion 8,
recursive-strata 5, founding-corpus 2, verdict-authority 1 (verdict verb list),
core-integrity 1 ("authoritative store"), effector-risk-computation 1 ("partially-superseded
banner"). **build-plans/ subdir: edge-and-supersession-build-plan 68 + sacred-boundary-build-plan
25 = 93** — implementation detail + code (`OpKind.SUPERSEDE`, `superseded()`); these
are build plans under `docs/design-notes/build-plans/`, likely outside the fixture's
note-corpus, flagged for the fixture author to decide.

**Genuine-stem-but-non-edge (flagged; scrubbing these would be wrong):**
`vault-runtime-auth.md:129` (TTL "replaces static key"), `wasm-sandbox-runtime.md:54`
("Neither replaces the other"), `recursive-strata.md:52` ("none replaces one"),
`the-sacred-boundary.md:88` ("replaced by an asymmetric public-key check"),
`live-adoption…:235` ("Retire the single-linkage shadow"), `:248` ("resolved in
favor of your hypothesis"), `wasm…:18` ("corrected 2026-07-03 audit" — a *status*
correction).

**Noise stems scanned and EXCLUDED from the 204 (documented for completeness):**
bare `correction`/`correct` (52 — drift-surgery §3 in alignment-subsystem, test
"correctness", "corrected audit"), `canonical` (25 — canonical form/graph), bare
`no longer` (9 — general prose), `defer(s) to` (6 — owner escalation, Invariant 7),
bare `precedence` w/o "takes". These name no overruling relation between notes.

**Scrub-pattern SEED (for `supersession-recovery-evaluation.md` §3's scrub list).**
Scrub the edge-NAMING phrasings, keyed to a note filename as object — NOT the bare
token:
- Banners: `⚠️?\s*(PARTIALLY\s+)?SUPERSEDED`, `is the (\*\*)?authoritative(\*\*)? \w+ note`, `takes precedence wherever the two differ`.
- Status lines: `^\*\*Status:\*\*.*(superseded by|Supersedes)\s+\`?[\w-]+\.md`.
- Inline relation: `(Supersedes?|superseded by)\s+\`?[\w-]+\.md`, `correct but incomplete`, `corrected\s+there`, `the corrections here take precedence`.
- **Caveat (must be in the scrub note):** do **not** blanket-scrub `supersede`/`supersedes`
  — it is domain vocabulary + a code identifier across ~13 mechanism notes and 2
  build plans (Tier B). Removing it destroys content without removing an edge.

### Item 3 — created-date sources
`created:` = **git first-commit date** (`git log --diff-filter=A --follow --date=short
| tail -1`) for all 33 converted notes. **Corroboration:** for all 30 design notes
the git first-commit date is *identical* to the first explicit date in the note's own
prose (dated header) — the note was committed the day it was dated; two independent
sources agree, so the value is high-confidence. Research: security-planes &
un-represent-ability likewise corroborated; **planar_graphs.md** has no internal
date → git-only. `updated:` = git last-commit (pre-migration), per finding-0023 —
not today. No audit-chronology fallback was needed. Full date table: Appendix B.

### Item 4 — record repair
The plan body was **§1 Objective + §5 Write scope only** at `/build` time —
incomplete. The addendum (items 1–4) arrived **mid-session**, after conversion had
begun. Appended to `plan.md` verbatim-in-substance as "Addendum (supplied
mid-session)" so history describes the actual run. **finding-0024 deleted**
(owner-instructed): it parked the design-note criterion on the denylist collision;
the owner's `DENYLIST` lift resolved it, so it is no longer an issue for this work.
finding-0023 updated to drop its reference and note both halves converted.

**Verification.** `git diff --numstat` = `13 0` × 30 design notes, `12 0` × 3
research (unchanged from before); all prose md5 preserved; 0 notes without
front-matter; inventory sanity-check passed; Stop-gate standalone → ALLOW. No
`ratified`/`superseded` status written anywhere; no prose edited (the human
`**Status:**` lines and supersession banners are inventoried, not modified).

**Next action (`/triage`).** Review + commit the delta; seal bp-005 `complete`;
`docs/PROGRESS.md` checkpoint. Sweep finding-0023 (research-note schema). The
inventory (Appendix A) is ready to seed `supersession-recovery-evaluation.md` §3's
scrub-pattern file.

---

## Entry — 2026-07-08 — CORRECTION: design-note half was a denylist violation; reverted. Research half stands.

*(Superseded by the entry above once the owner lifted the denylist. Retained for
provenance — this was the true state before the lift.)*

I first read the plan's `write_scope` (which lists `docs/design-notes/**`) at face
value and prepended front-matter to all 30 no-FM design notes + the 3 research
notes via Bash. That was wrong for the design notes: `docs/design-notes/**` was on
the foundation denylist (`_lib.py` `DENYLIST`; builder contract "Never edit a design
note") — never writable by any session, beneath any plan; a plan's `write_scope`
cannot re-grant a denylisted path. The Bash writes slipped past pre-hoc `scope-guard`
(Edit/Write-only) and the **Stop-gate `journal-gate` caught them**. I reverted all
30 (`git restore docs/design-notes/`) — the denylist branch of the stop-audit has no
route-a-finding escape, so revert was the only clearance. The 3 research notes
(`docs/research/**`, not denylisted, in `write_scope`) were kept. Filed finding-0024
(the plan/denylist collision, since deleted) and finding-0023 (research-note schema).

---

## Appendix A — complete genuine-stem supersession-marker inventory (204 hits)

Every genuine supersession/overruling-stem prose occurrence, verbatim
`file:line:text`, front-matter fields excluded; noise stems (`correction`,
`canonical`, bare `no longer`, `defer`) excluded per the entry above.

```text
docs/design-notes/agent-workflow.md:57:| Design note          | `docs/design-notes/<slug>.md`                      | draft → ratified → superseded                                     | superseded           |
docs/design-notes/agent-workflow.md:58:| Build plan           | `docs/build-plans/<id>/plan.md`                    | proposed → ready → in-progress → complete \| parked \| superseded | complete, superseded |
docs/design-notes/agent-workflow.md:69:- **Plan supersession** is three-place: (P, P′, warrant), where the warrant is a `spec-defect` finding. A defect never edits a plan in place; graduation mints P′ citing the finding, P flips to `superseded` with a `superseded_by` link. Same relation as claim supersession (see `supersession-lifecycle.md`), same reason: the discredited plan must remain inspectable, and P′ must ground on the warrant, not on P.
docs/design-notes/agent-workflow.md:72:- **Book editions**: the book is a _derived projection_ of the ratified record and the codebase — design notes remain authoritative for design, the repo for implementation. It synthesizes and asserts nothing without citing a source: an artifact id, or code by path plus git ref. Code snippets are included wherever they genuinely aid understanding; each is a copy annotated `source: path@ref`, so drift is detectable rather than silent. A scribe run ends by updating the sync marker (`docs/book/SYNC.md`: git ref + artifact ids incorporated); the commit is the edition. Draft notes never enter the book; parked decisions populate the future-work chapter verbatim with their re-entry conditions; superseded material may be retained as marked design-evolution remarks, warrant-linked — provenance as pedagogy.
docs/design-notes/agent-workflow.md:78:Build plan front-matter (A4/A6, template at `docs/templates/build-plan.md`): `type, id, status, design_ref, contract: builder | scribe` (defaults to builder), `write_scope` (glob list — the capability), `session_budget: 1`, `depends_on` / `parallelizable_with` (item/plan dependency edges), `re_entry` (if parked — **retained as a front-matter key**, so the "parked ⇒ re-entry" gate below stays greppable per Principle 1; §11 of the template is its human-readable expansion, not its authoritative location), `supersedes`/`superseded_by` + `warrant` (if applicable). Fields that are _body sections_, not front-matter keys (A6 reconciliation — they carry no enforcement stake and read better as prose): `objective` (§1), `context_manifest` (§2, ordered read list), `non_goals` (§9), `stop_conditions` (§10). Per-item body: each item carries `acceptance` (runnable), a **named falsifier** (the observable that would show the item failed or its approach is wrong — distinct from acceptance), the `invariants` it must not violate, a `touches_stored_data` blast-radius flag, and its own parallelizable/depends-on edges. Plans that touch existing code additionally carry an **Investigation** section (open questions answered with `path:line` citations) and a **Reconciliation** section (banner-on-correction / cross-reference-on-extension, never silent replacement); plans implementing a mathematical object carry a **Math** section with each object's three-clause field-guide entry. Every template section is required; inapplicable sections are marked `N/A — <reason>`, never omitted.
docs/design-notes/agent-workflow.md:82:Design note adds: `supersedes`/`superseded_by`, `warrant`.
docs/design-notes/agent-workflow.md:136:| `gate-guard`        | PreToolUse: Edit\|Write\|MultiEdit on `docs/design-notes/` and `docs/build-plans/*/plan.md` | Deny any edit performing a blessing transition — setting `status: ratified`, or `proposed → ready` — in every session, every role. Deny reason states: blessing transitions are owner-manual, made by hand outside a session. All other status transitions (`ready → in-progress → complete \| parked \| superseded`) pass.                                                                                                                                                                                    |
docs/design-notes/agent-workflow.md:150:**Ambient-path exclusion (warrant: finding-0004).** The audit excludes genuinely ambient churn that is neither a scope target nor a blessing surface — `.claude/settings.local.json` (a per-machine permission cache) is the known case and is gitignored (§9) so it never reaches the working-tree diff at all. The principle generalizing 0004 and 0005: the Stop-gate must judge exactly the set it is responsible for — untracked-inclusive where a Bash write could smuggle something past (scope targets, blessing surfaces), and blind to paths that are legitimately none of its business. Both are the same defect class — the diff not matching the responsible set — corrected in opposite directions.
docs/design-notes/agent-workflow.md:164:| `/scribe`                 | Compute book debt — ratified or superseded design notes and promoted findings newer than `docs/book/SYNC.md` — and mint a sync plan (`contract: scribe`, `write_scope: docs/book/**`, the delta as context manifest) as `status: proposed`. Fixed acceptance on every sync plan: whole-book review, every snippet and code citation re-verified against HEAD, clean compile (latexmk or tectonic; default recorded on first run), zero undefined references, sync marker updated. Execution flows through `/build`. |
docs/design-notes/agent-workflow.md:207:Milestones close a second, slower loop. `/triage` surfaces book debt in the session brief and runs `/scribe` to mint a proposed sync plan whenever a design note has been ratified or superseded since the last edition; the owner's ready-flip is the milestone confirmation — the existing gate, reused, no new ceremony. The scribe then feeds back through the same findings channel: the book sits downstream of design, but writing it audits design.
docs/design-notes/agent-workflow.md:273:Amendments to a ratified note are warranted by findings and re-ratified by hand (defect patches amend in place; substantive pivots supersede — the same distinction the store draws between amendment and supersession). Each entry records the warrant and the change.
docs/design-notes/agent-workflow.md:280:- **A6** — warrant: finding-0008 (spec-defect, surfaced by bp-003 installing A4). Reconciles the §3 build-plan schema prose to the A4 template's field placement, closing a self-contradiction A4 left in the record: `objective`/`context_manifest`/`non_goals`/`stop_conditions` are described as body sections (§1/§2/§9/§10), not front-matter keys; `re_entry` is **retained as a front-matter key** (owner ruling) so the §3 "parked ⇒ re-entry" gate stays greppable per Principle 1, with §11 of the template as its human-readable expansion. The command files (`build.md`, `graduate.md`, `scribe.md`), which still instructed reading these as front-matter keys and would have misdirected a literal `/build` on a new-template plan, are corrected to the body sections by the same build plan that lands A5's code fix.
docs/design-notes/ambassador-as-reasoning-agent.md:22:Track B (the Voice). The corrections here take precedence where they differ from the earlier
docs/design-notes/ambassador-interpretation-and-flow.md:20:> **⚠️ PARTIALLY SUPERSEDED (2026-06-28).** `ambassador-as-reasoning-agent.md` is the
docs/design-notes/ambassador-interpretation-and-flow.md:21:> **authoritative** Ambassador note and takes precedence wherever the two differ. In
docs/design-notes/ambassador-interpretation-and-flow.md:22:> particular, the **"thin dispatcher"** framing below is _corrected_ there: the Ambassador
docs/design-notes/ambassador-interpretation-and-flow.md:32:> refinement — read this note for those, and the reasoning-agent note for the corrected
docs/design-notes/build-plans/edge-and-supersession-build-plan.md:82:  (`core/stores/derived.py:257-265`) **and a claim `supersede` currently writes
docs/design-notes/build-plans/edge-and-supersession-build-plan.md:102:claim-`supersede` from writing `derived_from=[C]`. Item 11 is the confirmation/enforcement item and
docs/design-notes/build-plans/edge-and-supersession-build-plan.md:109:**Finding:** ❌ as the note predicts. A claim `supersede` mints the alternative with
docs/design-notes/build-plans/edge-and-supersession-build-plan.md:110:**`derived_from=[C]`** — the claim it replaces — not the warrant's anchors:
docs/design-notes/build-plans/edge-and-supersession-build-plan.md:114:if isinstance(op, Supersede):
docs/design-notes/build-plans/edge-and-supersession-build-plan.md:117:    ops_store.record(OpKind.SUPERSEDE, op.claim, related_id=art.id, text=op.warrant)
docs/design-notes/build-plans/edge-and-supersession-build-plan.md:138:parameter** (`core/stores/derived.py:181-199`). Under the corrected grounding its parents are
docs/design-notes/build-plans/edge-and-supersession-build-plan.md:146:(the dialogue path). The founding-corpus path records its supersede **directly** —
docs/design-notes/build-plans/edge-and-supersession-build-plan.md:147:`ops_store.record(OpKind.SUPERSEDE, prior, related_id=record.digest, …)`
docs/design-notes/build-plans/edge-and-supersession-build-plan.md:155:**Finding:** ❌ no gate. `superseded()` returns **every** claim id with a `SUPERSEDE` op, with no
docs/design-notes/build-plans/edge-and-supersession-build-plan.md:160:def superseded(self) -> set[str]:
docs/design-notes/build-plans/edge-and-supersession-build-plan.md:162:        "SELECT claim_id FROM claim_ops WHERE kind = ?", [OpKind.SUPERSEDE.value])}
docs/design-notes/build-plans/edge-and-supersession-build-plan.md:165:`apply_operations` records the supersede unconditionally (`core/recursion_ops.py:211-216`). Nothing
docs/design-notes/build-plans/edge-and-supersession-build-plan.md:170:**Mitigating fact (why it is latent, not yet live):** ⚠️ nothing **consumes** `superseded()` as an
docs/design-notes/build-plans/edge-and-supersession-build-plan.md:176:reads `superseded()`, the ungated silent removal becomes live. `core/ingest/founding.py:121-123`
docs/design-notes/build-plans/edge-and-supersession-build-plan.md:177:already writes real supersede ops **between two authored (K₀) notes**, so the store contains the
docs/design-notes/build-plans/edge-and-supersession-build-plan.md:203:  (`core/recursion_ops.py:119-129`) — **no authority column**, and `superseded()` returns bare ids
docs/design-notes/build-plans/edge-and-supersession-build-plan.md:216:**Finding — states:** ❌ single type. `OpKind` has only `SUPERSEDE`
docs/design-notes/build-plans/edge-and-supersession-build-plan.md:218:(`core/recursion_ops.py:119-129`); a supersede is recorded and *immediately* appears in
docs/design-notes/build-plans/edge-and-supersession-build-plan.md:219:`superseded()` (`core/recursion_ops.py:167-172`). There is no `proposed → certified` transition and
docs/design-notes/build-plans/edge-and-supersession-build-plan.md:303:- **R2 — Item 7's partition is structural for `L`, but the claim-`supersede` is *not* fully
docs/design-notes/build-plans/edge-and-supersession-build-plan.md:304:  partitioned today.** Version-`supersedes` is fully isolated (`VersionStore`, never passed to
docs/design-notes/build-plans/edge-and-supersession-build-plan.md:305:  `build_complex`, `core/complex/build.py:106-114`). The claim-`supersede`, however, **mirrors itself
docs/design-notes/build-plans/edge-and-supersession-build-plan.md:312:  E_disp partition for claim-`supersede` requires Item 9.
docs/design-notes/build-plans/edge-and-supersession-build-plan.md:315:  never scores confidence (`core/recursion_ops.py:199-225`), `superseded()` is unconsumed by any
docs/design-notes/build-plans/edge-and-supersession-build-plan.md:326:  `core/ingest/founding.py:121-123` records a claim-`supersede` between two **authored (K₀)** founding
docs/design-notes/build-plans/edge-and-supersession-build-plan.md:328:  Under Item 8's gate, superseding blessed content should record a defeater + recommendation and leave
docs/design-notes/build-plans/edge-and-supersession-build-plan.md:342:(`core/complex/build.py:127,139-152`), and `EdgeStore` structurally forbids a `supersedes` rel-type
docs/design-notes/build-plans/edge-and-supersession-build-plan.md:356:(`recursive-strata.md:45`) still says supersession was built as `SUPERSEDES` in
docs/design-notes/build-plans/edge-and-supersession-build-plan.md:364:- > as an edge type is introduced there (built as `SUPERSEDES`, `core/stores/edges.py`), not here.
docs/design-notes/build-plans/edge-and-supersession-build-plan.md:367:+ > **⚠ Partially superseded (edge-model reconciliation, July 2026).** The clause "built as
docs/design-notes/build-plans/edge-and-supersession-build-plan.md:368:+ > `SUPERSEDES`, `core/stores/edges.py`" is **stale**: Item 6 removed `SUPERSEDES` from
docs/design-notes/build-plans/edge-and-supersession-build-plan.md:370:+ > edge types in distinct stores** — note-version `supersedes` in the version store
docs/design-notes/build-plans/edge-and-supersession-build-plan.md:371:+ > (`core/stores/versions.py`, Item 6) and claim-level `supersede` in the claim-op store
docs/design-notes/build-plans/edge-and-supersession-build-plan.md:384:+ > The dispositional supersession edges (note-version `supersedes`, claim `supersede`) live in
docs/design-notes/build-plans/edge-and-supersession-build-plan.md:401:+ both retrievable, both owner-endorsed. Superseding blessed content records a defeater + the
docs/design-notes/build-plans/edge-and-supersession-build-plan.md:406:+ §3 and Item 8. (Closes the gap in committed Item 2b, whose `superseded()` removed without this
docs/design-notes/build-plans/edge-and-supersession-build-plan.md:418:`supersede` must set `derived_from` to the warrant's K₀ anchors, not `[C]`; cross-reference
docs/design-notes/build-plans/edge-and-supersession-build-plan.md:444:+   wrong — it cites the very claim it discredits and collapses `g` when `C` is superseded
docs/design-notes/build-plans/edge-and-supersession-build-plan.md:517:> supersede over the same authored nodes; and `build_complex`'s signature admits no dispositional
docs/design-notes/build-plans/edge-and-supersession-build-plan.md:525:`EdgeStore` forbids `supersedes`, `core/stores/edges.py:30-33`) — Item 7 pins it with a regression
docs/design-notes/build-plans/edge-and-supersession-build-plan.md:537:`VersionStore` supersession row **and** a `ClaimOpStore` supersede op referencing the same nodes;
docs/design-notes/build-plans/edge-and-supersession-build-plan.md:544:C2–C3. **Note (R2):** this item's invariant is about `A_geom`/`L`. The claim-`supersede`'s
docs/design-notes/build-plans/edge-and-supersession-build-plan.md:556:1. **Blessing gate (Q11).** In `apply_operations`, branch a `Supersede` on the target's blessing
docs/design-notes/build-plans/edge-and-supersession-build-plan.md:560:   still retrievable**. **Unblessed** (unpromoted derived) ⇒ `superseded()` removal stays free.
docs/design-notes/build-plans/edge-and-supersession-build-plan.md:562:   `claim_ops`; a dreamer/dialogue supersede lands `proposed`; the `proposed → certified` transition
docs/design-notes/build-plans/edge-and-supersession-build-plan.md:565:   `superseded()` returns only `certified` (or free-unblessed) removals.
docs/design-notes/build-plans/edge-and-supersession-build-plan.md:571:**Files.** `core/recursion_ops.py` (gate in `apply_operations`; `state` column + `superseded()`
docs/design-notes/build-plans/edge-and-supersession-build-plan.md:577:without an owner verdict — superseding a blessed `C` yields a defeater + unpromoted `C′` +
docs/design-notes/build-plans/edge-and-supersession-build-plan.md:578:recommendation, and `C` is still retrievable and flagged contested. (b) Superseding an unpromoted
docs/design-notes/build-plans/edge-and-supersession-build-plan.md:583:**Falsifier.** A blessed claim disappears from retrieval after a `Supersede` with no corresponding
docs/design-notes/build-plans/edge-and-supersession-build-plan.md:595:> keyed on the two authored digests; `superseded()` active-projection filter), **owner-declared only,
docs/design-notes/build-plans/edge-and-supersession-build-plan.md:602:> 722 passed; ruff clean; seal green. (3) — the active-projection *consumer* of `superseded()` is the
docs/design-notes/build-plans/edge-and-supersession-build-plan.md:606:`supersede(A, B)` has `A`, `B` at **different `source_paths`** (`founding.py:114-123`: `prior` and
docs/design-notes/build-plans/edge-and-supersession-build-plan.md:608:note-version `supersedes`; and it carries **no warrant, no reasoning act, mints no derived
docs/design-notes/build-plans/edge-and-supersession-build-plan.md:609:alternative** → it is **not** a claim-`supersede`. It is a **third thing: an authored-historical
docs/design-notes/build-plans/edge-and-supersession-build-plan.md:615:third E_disp member distinct from note-version `supersedes` and claim `supersede` (documented in
docs/design-notes/build-plans/edge-and-supersession-build-plan.md:627:`FoundingItem.supersedes` is an owner-authored manifest field (`scripts/ingest_founding.py:33-34`,
docs/design-notes/build-plans/edge-and-supersession-build-plan.md:648:`ClaimOpStore.superseded()` has **no consumer** (grep), and the wired active projection filters on
docs/design-notes/build-plans/edge-and-supersession-build-plan.md:671:> **Built.** `core/recursion_ops.py`: (1) `Supersede` gains `anchors: tuple[str,...] = ()` (the
docs/design-notes/build-plans/edge-and-supersession-build-plan.md:681:> flagged-for-re-examination set (never cascade-retracted). Docstrings corrected per Part B.2.
docs/design-notes/build-plans/edge-and-supersession-build-plan.md:757:**Acceptance.** Adding or removing a dispositional edge (a `ClaimOpStore` supersede / `VersionStore`
docs/design-notes/build-plans/edge-and-supersession-build-plan.md:759:superseded claim's revision has `C ∈ derived_from`, so both `d` and `g` move (Q9/Q10). Include the
docs/design-notes/build-plans/edge-and-supersession-build-plan.md:854:member distinct from note-version `supersedes` and claim `supersede`. *Rejected (a):* reuse the
docs/design-notes/build-plans/edge-and-supersession-build-plan.md:860:`FoundingItem.supersedes` is an owner-authored manifest field (`scripts/ingest_founding.py:33-34`), but
docs/design-notes/build-plans/edge-and-supersession-build-plan.md:870:to defer — the current claim-op records are inert, no `superseded()` consumer). Documented
docs/design-notes/build-plans/edge-and-supersession-build-plan.md:880:A `supersede` with no explicit anchors grounds C′ by C's type: **derived** C → inherit `leaf_refs(C)`,
docs/design-notes/build-plans/edge-and-supersession-build-plan.md:883:bug. The `[C]` prohibition targets grounding through content that **decays or is superseded without a
docs/design-notes/build-plans/sacred-boundary-build-plan.md:50:  supersedes v1.
docs/design-notes/build-plans/sacred-boundary-build-plan.md:54:- No `supersedes` relation exists: EdgeStore rel-types are
docs/design-notes/build-plans/sacred-boundary-build-plan.md:67:`{supersede, attach_defeater, record_warrant}` is **entirely absent**; **warrant is
docs/design-notes/build-plans/sacred-boundary-build-plan.md:80:  it"), **recommend NO additions** to `{supersede, attach_defeater, record_warrant}`
docs/design-notes/build-plans/sacred-boundary-build-plan.md:265:**Answer.** The balance-math consumer reads the **same `EdgeStore`** that now holds `supersedes`
docs/design-notes/build-plans/sacred-boundary-build-plan.md:266:edges and **does not filter by rel-type**. `supersedes` is excluded today only **accidentally** —
docs/design-notes/build-plans/sacred-boundary-build-plan.md:274:- So `supersedes` is skipped **only because the superseded endpoint (the prev-version digest) is not
docs/design-notes/build-plans/sacred-boundary-build-plan.md:294:  supersession edges (`recursive-strata.md:39-43`), and the EdgeStore has no `supersedes`
docs/design-notes/build-plans/sacred-boundary-build-plan.md:298:  "adopt / reject / supersede / promote", but the ratified-candidate taxonomy is
docs/design-notes/build-plans/sacred-boundary-build-plan.md:336:not contradicts. **Therefore: five cross-references, zero partially-superseded banners
docs/design-notes/build-plans/sacred-boundary-build-plan.md:392:+  > (supersede / attach_defeater / record_warrant) that turns "a thought" into a graph
docs/design-notes/build-plans/sacred-boundary-build-plan.md:446:  Item6  ─▶ Item2/Item2b   (version-`supersedes` store separation BEFORE claim-`supersede` vocab — §4A C3)
docs/design-notes/build-plans/sacred-boundary-build-plan.md:512:  set), do not hard-code "adopt/reject/supersede/promote".
docs/design-notes/build-plans/sacred-boundary-build-plan.md:517:  ratify `{supersede, attach_defeater, record_warrant}`; decide `retract/split/merge/
docs/design-notes/build-plans/sacred-boundary-build-plan.md:548:  unchanged chunks retained, changed/new re-embedded, removed marked superseded — §4);
docs/design-notes/build-plans/sacred-boundary-build-plan.md:549:  `core/stores/edges.py:26-29` (add a `supersedes` rel-type — resolves R2);
docs/design-notes/build-plans/sacred-boundary-build-plan.md:567:`supersede` must not collide with version-`supersedes`). Touches stored data: **YES** — re-keys the
docs/design-notes/build-plans/sacred-boundary-build-plan.md:569:- *Problem (built today, confirmed Q7/Q8):* `sync_path` writes a `SUPERSEDES` edge into the
docs/design-notes/build-plans/sacred-boundary-build-plan.md:574:  (`versions(doc_id, version_seq, digest, superseded_by, at)`) the balance math cannot reach
docs/design-notes/build-plans/sacred-boundary-build-plan.md:577:  the `source_path`) and **remove** the `EdgeStore`/`SUPERSEDES` write; **change**
docs/design-notes/build-plans/sacred-boundary-build-plan.md:578:  `core/stores/edges.py` to drop the `SUPERSEDES` constant; **change** `core/ingest/sync.py`
docs/design-notes/build-plans/sacred-boundary-build-plan.md:580:  existing `supersedes` rows out of the `EdgeStore`; `tests/integration/test_version_history.py`.
docs/design-notes/build-plans/sacred-boundary-build-plan.md:582:  from v1 by `version_seq`, not digest); `build_complex._overlay_signed` sees **no** `supersedes`
docs/design-notes/build-plans/sacred-boundary-build-plan.md:586:- *Named falsifier:* the version chain forms a cycle on revert; OR a `supersedes` sign enters
docs/design-notes/build-plans/sacred-boundary-build-plan.md:604:- *Acceptance test:* a dialogue **correction** emits a `supersede` edge — the active
docs/design-notes/core-integrity.md:80:| **sealed** | Refuses handoff, exits loud | Operational runs: the Dreamer over the authoritative store, anything trusted against real data |
docs/design-notes/dialogue-ingest-and-recursion.md:52:contradiction: X′ **supersedes** X. The graph cannot see supersession because the
docs/design-notes/dialogue-ingest-and-recursion.md:70:- `supersede(claim C, claim C′, warrant W)` — C′ replaces C in the active
docs/design-notes/dialogue-ingest-and-recursion.md:80:**Distinct from version-supersession.** This claim-level `supersede(C, C′, W)` —
docs/design-notes/dialogue-ingest-and-recursion.md:82:`supersedes(v1, v2)` in `ingest-identity-and-amendment.md` §4A (no warrant, a
docs/design-notes/dialogue-ingest-and-recursion.md:93:`derived_from=[C]` is corrected there (§4.2): a revision grounds on its warrant's
docs/design-notes/dialogue-ingest-and-recursion.md:94:anchors, not on the claim it replaces.
docs/design-notes/dialogue-ingest-and-recursion.md:138:  the starter vocabulary {`supersede`, `attach_defeater`, `record_warrant`}
docs/design-notes/dialogue-ingest-and-recursion.md:152:propose cross-references or partially-superseded banners per repository
docs/design-notes/effector-risk-computation.md:112:partially-superseded banner.
docs/design-notes/founding-corpus.md:55:including musings that *supersede each other* — into simultaneous peers, baking
docs/design-notes/founding-corpus.md:103:superseded banners per repository discipline.
docs/design-notes/ingest-identity-and-amendment.md:26:> mechanics are specified and corrected in §4A below — the edge must be keyed on
docs/design-notes/ingest-identity-and-amendment.md:77:- the log records **supersession**: version *v2*, hash *H₂*, supersedes *v1*.
docs/design-notes/ingest-identity-and-amendment.md:87:- removed chunks are marked superseded.
docs/design-notes/ingest-identity-and-amendment.md:98:taxonomy in `the-edge-model.md` (E_geom ⊔ E_disp; note-version `supersedes` and
docs/design-notes/ingest-identity-and-amendment.md:99:claim `supersede` are distinct dispositional edges, both excluded from the
docs/design-notes/ingest-identity-and-amendment.md:121:consumer filtering `supersedes` out by rel-type — that makes correctness a
docs/design-notes/ingest-identity-and-amendment.md:129:`supersede(C, C′, W)` that carries a warrant and is a reasoning act. Amendment
docs/design-notes/ingest-identity-and-amendment.md:130:`supersedes(v1, v2)` is note-version-level: no warrant, a file edit. They are
docs/design-notes/ingest-identity-and-amendment.md:131:orthogonal — a note can be amended without superseding any claim (a typo fix),
docs/design-notes/ingest-identity-and-amendment.md:132:and a claim can be superseded without editing any note (a dialogue concludes a
docs/design-notes/ingest-identity-and-amendment.md:137:**Constraint 4 — "removed chunks are marked superseded" (§4) means excluded from
docs/design-notes/ingest-identity-and-amendment.md:203:  frustration / diffusion) read the same store that holds `supersedes` edges, and
docs/design-notes/ingest-identity-and-amendment.md:205:  consumer's rel-type selection. Confirm `supersedes` and its placeholder sign
docs/design-notes/ingest-identity-and-amendment.md:215:superseded banner if any existing text conflicts), per repository discipline.
docs/design-notes/live-adoption-and-longitudinal-harness.md:235:curve. Retire the single-linkage shadow only after 2 further clean weeks — then it becomes the
docs/design-notes/live-adoption-and-longitudinal-harness.md:248:  probe resolved in favor of your hypothesis; 4 claims await review; precision is trending up since
docs/design-notes/recursive-strata-amendment.md:43:been corrected to match `c ≤ γ^d · g`.
docs/design-notes/recursive-strata-amendment.md:50:introduced in ingest-identity, *built as `SUPERSEDES` in `core/stores/edges.py`*.
docs/design-notes/recursive-strata-amendment.md:51:That is now **stale**: Item 6 **dropped** `SUPERSEDES` from `core/stores/edges.py`
docs/design-notes/recursive-strata-amendment.md:57:> stores** — note-version `supersedes` in the version store
docs/design-notes/recursive-strata-amendment.md:58:> (`core/stores/versions.py`, Item 6; `SUPERSEDES` was removed from
docs/design-notes/recursive-strata-amendment.md:59:> `core/stores/edges.py`) and claim-level `supersede` in the claim-op store
docs/design-notes/recursive-strata-amendment.md:73:> supersession edges (note-version `supersedes`, claim `supersede`) live in
docs/design-notes/recursive-strata-amendment.md:98:> owner-endorsed. Superseding blessed content records a defeater plus the (unpromoted)
docs/design-notes/recursive-strata-amendment.md:105:This closes a gap in the current build (Item 2b's `superseded()` removes from the
docs/design-notes/recursive-strata-amendment.md:127:- A claim `supersede` must set the alternative's `derived_from` to the **warrant's
docs/design-notes/recursive-strata-amendment.md:128:  K₀-reaching anchors**, not to the superseded claim `[C]` (the committed Item 2b
docs/design-notes/recursive-strata-amendment.md:130:  makes its `g` collapse when `C` is superseded. See `supersession-lifecycle.md`
docs/design-notes/recursive-strata.md:36:> **Cross-ref (ingest operations):** `design-notes/dialogue-ingest-and-recursion.md` is the concrete ingest-operation instantiation of this map D — the operation vocabulary (supersede / attach_defeater / record_warrant) that turns "a thought" into a graph change, composing with the I5 budgets and the γ^d bound (built: `core/recursion.py`; I5 budgets still parked).
docs/design-notes/recursive-strata.md:52:These extend existing invariants; none replaces one.
docs/design-notes/recursive-strata.md:58:> **Cross-ref (identity & amendment):** `design-notes/ingest-identity-and-amendment.md` gives the structural-layer instantiation — corrections are supersession + re-projection of the derived index, never in-place edits. Decay (I2) and *supersession* are distinct mechanisms: supersession as an edge type is introduced there (built as `SUPERSEDES`, `core/stores/edges.py`), not here.
docs/design-notes/recursive-strata.md:81:- `strata.node_budget` — per-cycle ceiling on derived-node proposals, relative to grounded count; overridden by the owner review-capacity absolute at current scale (I5).
docs/design-notes/recursive-strata.md:112:Deferred deliberately; listing them now so unparking starts from a decision list, not a blank page: initial `layer_weight` ceiling; decay half-life; whether demote verdicts exist symmetrically with promote or decay alone handles removal; whether strata participate in the frozen-control-corpus reruns (recommended: yes, with a separately frozen stratum set, so longitudinal curves isolate recursion's contribution the same way they isolate corpus growth); whether the grounding ratio earns an interruption threshold or remains digest-only; and the I5 budgets — the initial `node_budget` fraction and the review-capacity absolute that overrides it at current scale, the `edge_budget` values per type, and specifically whether cross-stratum edges start at a hard zero at first unpark (strictest: no derived→derived-across-strata citation until the mechanism is trusted) or a small positive ceiling.
docs/design-notes/secrets-management-evolution.md:17:> **⚠️ SUPERSEDED (2026-07-07).** `vault-runtime-auth.md` is the authoritative Vault
docs/design-notes/secrets-management-evolution.md:18:> note and takes precedence wherever the two differ. It reframes Vault from a
docs/design-notes/secrets-management-evolution.md:20:> (its own words: this note was "correct but incomplete"), and the audit confirms the
docs/design-notes/secrets-management-evolution.md:27:**Status:** superseded by `vault-runtime-auth.md` — see banner. Keychain remains
docs/design-notes/supersession-lifecycle.md:65:from silently **superseding (hiding)** owner-blessed content — the inverse
docs/design-notes/supersession-lifecycle.md:76:  contested**, until an owner verdict executes the removal. Superseding a
docs/design-notes/supersession-lifecycle.md:81:  retrievable): `superseded()` removes it freely. This churn happens entirely in
docs/design-notes/supersession-lifecycle.md:126:### 4.2 A revision grounds on its warrant's anchors, not on the claim it replaces
docs/design-notes/supersession-lifecycle.md:127:`C′` supersedes `C`. `C` is **replaced, not built upon**. Therefore `C′`'s
docs/design-notes/supersession-lifecycle.md:134:on the claim it replaces is wrong on two grounds, both now expressed through the
docs/design-notes/supersession-lifecycle.md:141:2. **`g` collapses when `C` is superseded (self-staleness).** The grounding ratio
docs/design-notes/supersession-lifecycle.md:143:   `C` is superseded (removed from active), that path no longer reaches live
docs/design-notes/supersession-lifecycle.md:159:dispositional (supersession) edges, and does a claim `supersede` set `derived_from`
docs/design-notes/supersession-lifecycle.md:210:When `C` is superseded at op-seq `t`, claims grounded on `C` during its active
docs/design-notes/supersession-lifecycle.md:211:window are now grounded in superseded content — their grounding ratio `g` drops as
docs/design-notes/supersession-lifecycle.md:272:superseded authored note is demoted **only after an owner verdict**, never silently —
docs/design-notes/supersession-lifecycle.md:273:and it must **not** be written to the owner-declared authored-historical `supersede`
docs/design-notes/supersession-recovery-evaluation.md:45:  seven negatives whose _extends-vs-supersedes_ discrimination is the genuinely
docs/design-notes/supersession-recovery-evaluation.md:61:   - front-matter `supersedes`, `superseded_by`, `warrant` fields → removed;
docs/design-notes/supersession-recovery-evaluation.md:62:   - `status: superseded` → `status: draft` in the copy;
docs/design-notes/supersession-recovery-evaluation.md:63:   - prose self-declarations — "⚠️ PARTIALLY SUPERSEDED", "Supersedes …",
docs/design-notes/supersession-recovery-evaluation.md:64:     "superseded by …" lines and equivalent markers → removed (the scrub list is
docs/design-notes/supersession-recovery-evaluation.md:66:   - cross-references that _name the relation_ (e.g. "this note replaces X") →
docs/design-notes/supersession-recovery-evaluation.md:134:    machinery cannot distinguish _extends_ from _supersedes_ as designed;
docs/design-notes/supersession-recovery-evaluation.md:172:- Does not ratify, supersede, or edit any note under test (the fixture is a copy).
docs/design-notes/the-edge-model.md:73:- **Intent** (C′ replaces C, warranted) is observer-**dependent**: geometry
docs/design-notes/the-edge-model.md:74:  underdetermines it. Identical claims may **corroborate**, not supersede;
docs/design-notes/the-edge-model.md:115:- **E_disp** — dispositional edges: note-version `supersedes` (Item 6, version
docs/design-notes/the-edge-model.md:116:  store), claim-level `supersede` (reasoning paths, claim-op store), **and
docs/design-notes/the-edge-model.md:117:  authored-historical `supersede`** (§4a). All **excluded** from the balance math.
docs/design-notes/the-edge-model.md:128:(store separation) and Constraint 3 (version-`supersedes` vs claim-`supersede`
docs/design-notes/the-edge-model.md:140:## 4a. A third dispositional edge: authored-historical `supersede` (PD11)
docs/design-notes/the-edge-model.md:142:The founding corpus records "a later musing supersedes an earlier one." Apply the
docs/design-notes/the-edge-model.md:144:documents?* A founding `supersede(A, B)` has `A`, `B` at **different `source_paths`**
docs/design-notes/the-edge-model.md:148:- **not note-version `supersedes`** — that relation is *within one `doc_id`*, keyed
docs/design-notes/the-edge-model.md:151:- **not claim `supersede`** — it carries **no warrant**, is **no reasoning act**, and
docs/design-notes/the-edge-model.md:154:So it is a **third E_disp member: authored-historical `supersede`** — both endpoints
docs/design-notes/the-edge-model.md:162:of the founding manifest / an owner CLI (`FoundingItem.supersedes` is an owner-authored
docs/design-notes/the-edge-model.md:184:| note-version `supersedes` | 2-place, directed | geometry (file edit) | no | version store |
docs/design-notes/the-edge-model.md:185:| claim `supersede` (reasoning path) | 3-place `(C,C′,W)`, directed | dreamer-proposed → verdict-certified | no | claim-op store |
docs/design-notes/the-edge-model.md:186:| authored-historical `supersede` (§4a) | 2-place, directed | authored-ingest (owner's hand at authoring) | no | authored-supersession store |
docs/design-notes/the-edge-model.md:194:Extends `the-sacred-boundary.md` §2.3. The claim-`supersede` row is the vocabulary
docs/design-notes/the-sacred-boundary.md:88:- Verdict verifier that could forge → replaced by an asymmetric public-key check
docs/design-notes/vault-runtime-auth.md:18:**Status:** design only. Supersedes `secrets-management-evolution.md` (which framed
docs/design-notes/vault-runtime-auth.md:19:Vault as a multi-machine secrets store — correct but incomplete). This note frames
docs/design-notes/vault-runtime-auth.md:129:| AWS bridge role          | `aws/` (dynamic) | TTL=1h; replaces static key               |
docs/design-notes/verdict-authority.md:32:(adopt / reject / supersede / promote). The authorization must be easy for the
docs/design-notes/wasm-sandbox-runtime.md:18:**Status:** partially built (corrected 2026-07-03 audit — the original "design only" header was
docs/design-notes/wasm-sandbox-runtime.md:54:Neither replaces the other. Podman stays the default substrate for anything Pyodide can't
```

## Appendix B — created-date table (git first-commit)

```text
alignment-subsystem.md                         2026-06-27   git==prose
attestation-layer.md                           2026-06-27   git==prose
dialogue-ingest-and-recursion.md               2026-07-04   git==prose
dream-phase-rnd-charter.md                     2026-06-26   git==prose
dreamer-quality-suite-evaluation.md            2026-06-29   git==prose
dreaming-on-curated-graphs.md                  2026-06-26   git==prose
dreaming-v2-interpreter-panel.md               2026-06-26   git==prose
effector-risk-computation.md                   2026-07-04   git==prose
founding-corpus.md                             2026-07-04   git==prose
hands-and-the-effector-layer.md                2026-07-01   git==prose
holistic-testing.md                            2026-06-27   git==prose
ingest-identity-and-amendment.md               2026-07-04   git==prose
live-adoption-and-longitudinal-harness.md      2026-07-03   git==prose
nervous-system-and-ambassador.md               2026-06-28   git==prose
observed-data-and-the-assistant-tier.md        2026-06-25   git==prose
observed-iot-and-cross-source-synthesis.md     2026-06-27   git==prose
recursive-dreaming-bounded-by-grounding.md     2026-06-26   git==prose
recursive-strata-amendment.md                  2026-07-04   git==prose
recursive-strata.md                            2026-07-03   git==prose
roadmap-and-future-directions.md               2026-06-25   git==prose
skill-mining-pipeline.md                       2026-07-03   git==prose
skills-and-scope.md                            2026-06-25   git==prose
stability-adjudication.md                      2026-07-02   git==prose
supersession-lifecycle.md                      2026-07-04   git==prose
test-organization.md                           2026-06-27   git==prose
the-edge-model.md                              2026-07-04   git==prose
the-sacred-boundary.md                         2026-07-04   git==prose
vault-sync-and-capture.md                      2026-06-26   git==prose
verdict-authority.md                           2026-07-04   git==prose
wasm-sandbox-runtime.md                        2026-06-27   git==prose
planar_graphs.md                               2026-07-03   git-only
security-planes.md                             2026-07-03   git==prose
un-represent-ability.md                        2026-07-03   git==prose
```

## Markers
