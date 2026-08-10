---
type: design-note
id: dn-research-register
track: workflow            # the artifact chain's own register is how work moves; docs/tracks/workflow.md exists — no new manifest minted (its DoD gains rows, §3)
status: draft              # provenance description, never a gate (merge-gated regime, 2026-07-28)
created: 2026-08-09
updated: 2026-08-09        # revision pass, same day — four-audit verdicts applied
links:
  - docs/brainstorms/mathematical-foundations.md         # THE WARRANT (PR #42, capture branch — lands first; see Sequencing) — terminology seeds + the structure-instantiation bridge
  - docs/design-notes/track-board-and-deskcheck-gate.md  # RATIFIED parent — its D3 minted the deskcheck template/body this note evolves; D2's derived board is untouched
  - docs/design-notes/external-grounding.md              # RATIFIED — the verified-citation gate every paper bibliography obeys (never [FROM MEMORY])
  - docs/design-notes/erratum-relation.md                # RATIFIED — correction = supersession composed with a warranted erratum; the retraction algebra the lexicon maps
  - docs/design-notes/dn-typed-workflow-registry.md      # RATIFIED (pre-regime) — parks deskcheck-verdict signing; that park is untouched here
  - docs/design-notes/authorship-distance-axis.md        # DRAFT at HEAD — agent-vs-owner authorship as a first-class coordinate; the provenance block leans on the idea
  - docs/templates/deskcheck.md                          # the 17-line artifact re-typed here — evolved in place, never paralleled
  - docs/book/preamble.tex                               # the house claim registry + citation macros the paper format factors and extends
  - .claude/skills/book/SKILL.md                         # LaTeX conventions authority — reused, not forked
  - .claude/skills/issue/SKILL.md                        # the label taxonomy the claim ladder maps onto
  - docs/design-notes/dn-mathematical-foundations.md    # THE SIBLING — same PR #47; consumes the §2.3 labels; carries the laws ledger (docs/LAWS.md) + the Lean L0–L4 ladder
supersedes: null           # PARTIAL overlay on dn-track-board-and-deskcheck-gate D3 — template/body shape only (§2.4); D3's pre-regime verdict-hook mechanics are not propagated; D2's board, the dc- lifecycle, and the queue are untouched
superseded_by: null
warrant: docs/brainstorms/mathematical-foundations.md    # owner seed 2, 2026-08-09 — quoted in the opening blockquote; reaches main via PR #42, sequenced first
---

# The research register — the palace adopts the literature's language without inflating its claims

> Composed at **fable** (`claude-fable-5`, xhigh, 2026-08-09; revision pass same day,
> same tier). Per the banner-unreliability lesson (finding-0147, frozen history: a
> composed-at banner is a claim, not a proof), the owner cross-checks usage at review.
> Agent-drafted, filed as `draft` on a branch. Under the merge-gated regime (owner
> ruling 2026-07-28) nobody flips a status — **the owner's merge of this PR is
> ratification**, and the `status:` line above is provenance description, never a gate.
> If this text is on `main`, the owner put it there.
>
> **Sequencing:** the warrant capsule lives only on the capture branch of PR #42 and is
> not at HEAD (verified: `git cat-file -e` fails at `68d8d39`). That PR lands first —
> or this branch stacks on it — so the warrant path resolves in the tree the reviewer
> reads. A note establishing citation hygiene does not itself merge with a dangling
> warrant.

> *"capture-as-theorem gave me a thought: could/should we start using that terminology,
> and start adopting mathematical research style formats? we could refresh the templates
> and skills around framing and terminology that reflect the research community. this is
> also a little for me — I'd like to better understand mathematical/computer-science
> research language in research communities. it would add credibility, but more
> importantly it makes the project more accessible to the technical research communities.
> all this to also say: that's what a deskcheck could be — a research PDF document, typed
> in LaTeX, formatted like an academic/research paper, like an article in a math/science
> journal."* — owner, 2026-08-09.
>
> The answer, in one sentence: **adopt the register as an alias layer that teaches and a
> claim ladder that raises the bar — and evolve the deskcheck, in place, into the one
> genre it already is: an artifact-evaluation report, typed in the book's LaTeX.**

## 1. Purpose and scope

### 1.1 What this note decides

Three mechanisms and one surfaced absence, presented as one note because they are one
move — the palace learning to say precisely what it knows, in the language of the
communities that invented the distinctions:

1. **The lexicon** (§2.2) — a terminology layer mapping every house term to its
   research-register counterpart, living in one glossary artifact (`docs/lexicon.md`),
   loaded on demand, never resident in `CLAUDE.md`. Terms **alias and deepen; they never
   replace** — the invariant is §2.1, and it is load-bearing.
2. **The claim ladder** (§2.3) — a rigor-honesty policy: which claim-strength labels
   exist, what each one *costs*, and where labels attach. The register is adopted to
   raise the bar, not to decorate; most of what the palace knows is conjecture and
   proposition, and the ladder makes saying so the path of least resistance.
3. **The deskcheck as paper** (§2.4) — the deskcheck artifact evolves into a short
   research paper: LaTeX, the book's conventions reused wholesale, the
   artifact-evaluation genre, the same `dc-` lifecycle, the same board, the same owner
   holding the same final say. Evolution of the existing artifact — the 2026-07-28
   regime just retired ceremony, and this note will not smuggle a new one in: the form
   is chosen before a word is authored (§2.4.2), and the bill is priced in §3.
4. **The empty slot** (§2.6) — the research idiom sharpens what the palace has never
   had: a stated research Question. This note surfaces the absence and builds the slot.
   Authoring the Question is the owner's alone; not one word of it is drafted here.

The track is `workflow` — the register governs how work is framed, recorded, and
evidenced, which is exactly what the workflow track already owns. No new manifest is
needed; `docs/tracks/workflow.md` exists at HEAD, and §3 licenses the working-material
DoD rows that make this work visible to the lane's own deskcheck.

### 1.2 Non-goals (load-bearing — read at ratification)

1. **No renaming of ids, commands, or machine-parsed strings.** `dn-`/`bp-`/`dc-`
   grammars, the six slash commands, `type: track`, the `Build Plan — ` H1 prefix, the
   `read-map` fence, the `## Follow-through` header, the intent-capsule caps, the commit
   grammar — all frozen. The alias invariant (§2.1) is the positive form of this
   non-goal. [ESTABLISHED — parser/vocabulary coupling verified at HEAD, §2.1's list.]
2. **No actual journal or venue submission.** No arXiv, no conference, no DOI minting.
   The register is adopted internally; external publication is a parked decision with
   the Question as its re-entry condition. [INFERENCE — the owner asked for
   accessibility to research communities, not submission to them; parking the venue
   keeps the smaller reading.]
3. **No retroactive rewriting of history.** Frozen surfaces (`docs/findings/**`, the
   owner-questions inbox, sealed journals, merged notes and capsules) keep their
   vocabulary byte-identical. The register applies forward. [ESTABLISHED — frozen
   history is a standing rule.]
4. **`CLAUDE.md` gains nothing.** Not a glossary line, not a pointer. Depth lives in
   the glossary and templates, loaded on demand. [ESTABLISHED — thinness rule.]
5. **The research Question is not authored here.** Study-not-product: the Question is
   owner-only. This note builds the slot and leaves it empty, labeled empty.
   [ESTABLISHED — owner-only authorship is a standing rule.]
6. **Lean adoption is not decided here — the sibling carries it.** The warrant
   capsule's flat park is superseded by the L0–L4 ladder of
   dn-mathematical-foundations (§2.4 there; investigation: issue #48). Consequence
   for the ladder unchanged in spirit: "Theorem" stays rare until L2 discharge makes
   *Theorem (machine-checked, `formal/...`)* honestly reachable, and its absence
   meanwhile is honest (§2.3).
   [ESTABLISHED — the park's disposition moved to the sibling, riding this same PR.]
7. **No second LaTeX stack.** The paper format factors the book's preamble and extends
   its notation registry; it duplicates nothing. Two copies drift. [ESTABLISHED — DRY
   is a defect, not a nit.]
8. **No new ritual.** The deskcheck's lifecycle, store, board parsing, and queue are
   unchanged; the carrier `.md` alone remains a legal deskcheck, and the form is picked
   before authoring, never waived after the cost is sunk (§2.4.2). If the paper ever
   *delays* closure, the format has failed its own bar (falsifier F6).
   [INFERENCE — "evolved, never paralleled" is this note's reading of the owner's seed
   against the regime's retirement of ceremony; the owner confirms at ratification.]
9. **The laws-ledger sweep is not licensed here.** The per-component
   claimed-structure + laws + falsifier sweep belongs to the sibling,
   dn-mathematical-foundations (§1.3 — same PR); this note only specifies the labels
   that sweep consumes. [ESTABLISHED — the boundary is owner-directed (seed 3,
   2026-08-09) and both notes ride PR #47.]
10. **The dormant deskcheck-gate machinery is not retired here.** `gate-guard.sh`,
    `_lib.py`'s verdict clauses, and `tests/integration/test_deskcheck_gate.py` stay
    untouched; the carrier keeps their expected shape so they stay green. Disposition
    is parked, and filed as a `parked` issue with this PR so it cannot silently rot.
    [INFERENCE — a format change and a trust-boundary change never share a plan.]

### 1.3 The sibling note — named, landing beside this one

The warrant capsule carries two arcs. This note is the register arc. The foundations
arc — structure-instantiation as the bridge, the laws ledger, memberships first —
is **dn-mathematical-foundations**
(`docs/design-notes/dn-mathematical-foundations.md`), landing in this same PR.
One shared boundary, flagged: the claim-ladder labels of §2.3 are *consumed* by the
laws ledger (each law lands as a labeled claim with a falsifier); neither note should
redefine the labels without the other. The float-epsilon caveat (float addition is
non-associative — the capsule's named foundational risk) appears in both: here as a
register rule (§2.3.3), there as substance.

## 2. Principles / decision

### 2.1 The invariant first: alias and deepen, never replace

**Decision.** The research register is a *reading* of the house vocabulary, not a
rename of it. Every house term keeps its id grammar, its file paths, its commands, and
its machine-parsed strings; the research term is the teaching layer stacked on top.
Concretely:

- `dc-NNN` never becomes `paper-NNN`; a capture is still `/capture`; a finding is still
  an issue. The research term appears in prose, glossaries, templates' teaching
  comments, and the paper genre — never in identifiers.
- **Vocabulary and parser move in the same PR or not at all** — and RR-1..3 (§3) move
  no parser. The frozen machine layer, enumerated so review can grep for it: `type:
  track` and the manifest keys (`scripts/board.py:143-155`), the `Build Plan — ` H1
  prefix (`board.py:160`), the ` ```read-map ` fence (`scripts/readmap.py:27`), the
  verbatim `## Follow-through` header (checkpoint skill), the intent-capsule canonical
  caps (`scripts/capsule.py:41,62`), the `type(scope): subject` commit grammar, and the
  deskcheck front-matter schema (`board.py:283-294`).

Why this is the right shape and not timidity: the house terms are *coordinates* — the
board, the queue, CI, and every merged artifact address by them. The research terms are
*meanings*. Coordinates must be stable; meanings are allowed to deepen. Breaking ids to
gain register would trade the system's addressability for its accent.

### 2.2 The lexicon — one glossary that teaches

**Where it lives.** `docs/lexicon.md` — a single authored artifact (not derived, not a
skill; there is no procedure to run, only meaning to load). Templates and the skills
that traffic in the mapped terms gain a one-line pointer (`Register: docs/lexicon.md`);
`CLAUDE.md` gains nothing.

**The entry contract — four clauses, all mandatory, plus a mechanical fifth.** The
owner's stated goal is to *learn* the research language, so an entry that merely
renames is a defect. Every entry carries: (1) the **house meaning**, precise; (2) the
**research meaning** as the community actually uses it; (3) **why the mapping holds** —
the warrant for the analogy; (4) **where it breaks** — the disanalogy, stated plainly.
An analogy without its breaking point teaches wrong. The mechanical fifth clause is
**verification status**: a verified source with date, or `[FROM MEMORY]` — R6's
discipline applied to the glossary itself, so a reader always knows which glosses are
community practice recalled and which are checked. An optional sixth clause, **usage**,
says when the research term is admissible in house prose (rule of thumb: only where its
community meaning is fully earned; otherwise the house term stands).

**The map — the index.** The glossary carries every row as a full entry per the
contract; this table is the index only (terse cells; the fourth clause — where each
mapping breaks — is prose, below). Every research-meaning gloss here is community
practice carried `[FROM MEMORY]` except where a verified source is named (§2.4.3's
badge definitions).

| house term | research register | the mapping's warrant, one clause |
|---|---|---|
| capture / brainstorm capsule | **conjecture** | precise, falsifiable, believed, unproven — naming a sharp one is a contribution |
| design note, merged | **definition admission + invariants** | ratification admits terms and pins invariants — a normative spec, in force |
| owner's merge | **editorial acceptance** | accept, camera-ready, and publication of record in one act; the merge log is the record |
| PR review rounds | **shepherding — internal referee report** | revision-under-supervision until acceptable |
| amendment (A-series) | **erratum / addendum** | append-only, warranted, on the record; the original stands annotated |
| supersession ∧ erratum | **correction — retraction and replacement, reason stated** | the ratified correction composition (dn-erratum-relation) |
| build plan | **proof obligation** | §7's acceptance + falsifier pairs are statement + refutation condition |
| journal | **lab notebook** | contemporaneous working record — judgement, surprises, dead ends |
| issue `type:defect` | **counterexample** | a witness against a claimed property |
| issue `type:investigation` | **conjecture / hypothesis** | "establish or falsify" is the conjecture register |
| issue `type:ruling` | **axiom / postulate** | admitted by authority, not proven; filed closed because it IS the record |
| deskcheck | **artifact evaluation — Functional criteria** | "show it working, owner has final say", with the owner as evaluator |
| golden set | **benchmark, frozen** | fixed evaluation target, human-only changes |
| `CONSTITUTION.md` | **axioms / postulates** | the outermost admitted frame every agent inherits — never derived, never auto-modified |
| property test, green | **"tested — no counterexample found"** | a mechanized falsification attempt, survived |
| structure-instantiation | **model of a known structure** | proven theorems import under stated hypotheses — the honest "first principles" |
| fresh-agent test | **reproduction — in-house analog** | a party other than the authoring session re-derives from artifacts alone |
| one-way artifact chain | **preregistration-style trail (analog)** | capture is timestamped before design before build |
| parked + re-entry | **open problem, with reopening condition** | future work that names what would reopen it |

**Where the mappings break — the fourth clause, previewed.** The glossary carries these
in full; recorded here so the map cannot be read stronger than it is:

- *Capture → conjecture:* capsules also carry mood and direction, which are not claims.
- *Merged note → definition:* never a theorem — the worked entry below is the register's
  cardinal lesson.
- *Merge → acceptance:* it is not refereeing; see the shepherding break.
- *Shepherding:* reviewers here share the author's incentives — say "internally
  reviewed", never "peer-reviewed" (R2).
- *Amendment → erratum:* the house form is append-only and warranted; whether that is
  stronger than venue practice is an unmeasured comparative, and stays unclaimed.
- *Correction:* the house term is deliberately the **composition** — plain
  supersession-with-warrant is *replacement* (was once right; the everyday analogs are
  arXiv v2 and RFC "obsoletes"), not retraction (was never right). Only
  supersession ∧ erratum earns the retraction register (dn-erratum-relation, ratified
  2026-07-27: *a correction is a supersession composed with a warranted retraction*).
  And community "retraction" additionally connotes fatal error or misconduct — routine
  design evolution must not borrow that weight.
- *Build plan → proof obligation:* a category difference, named plainly — in
  formal-methods practice an obligation is *discharged only by proof*; one not proven is
  *open*. The house discharges by tests, so the honest status is "supported, obligation
  open", never "discharged". The term teaches the shape (statement + what would refute
  it), not the standard of discharge.
- *Journal → lab notebook:* regulated notebooks are tamper-evident and witnessed; a
  journal is self-authored markdown, mutable until merged.
- *Defect → counterexample:* some defects refute nothing stated — they are just bugs.
- *Investigation → conjecture:* a settled investigation later work cites may earn
  **lemma** — but that promotion is a **house rule stricter than the community's**: in
  the literature "lemma" is an authorial label at write time (auxiliary intent), and
  earned-by-citation naming is folklore about famous lemmas, not the label's meaning.
  The glossary presents it as house-stricter-than-community, never as the community
  meaning.
- *Ruling → axiom:* axioms are minimal by taste, criticized via independence and
  consistency; rulings are operational by need, criticized by filing an issue. And the
  register says **axioms**, not "axiom schema" — schema is a precise term of art (a
  template with metavariables generating axiom instances: PA induction, ZF separation)
  that nothing here instantiates.
- *Deskcheck → artifact evaluation:* the evaluator is not independent — criteria are
  self-assessed; no badge is held or implied (§2.4.3).
- *Golden set → benchmark:* single-project; no community baselines attach.
- *Property test:* never shortens to "proven"; that word is reserved (§2.3.3).
- *Structure-instantiation:* transfer holds only while the stated hypotheses do.
- *Fresh-agent test:* ACM "Results Reproduced" requires another *team*; always say
  "analog".
- *One-way chain → preregistration:* the fullest break in the register — the worked
  entry below.
- *Parked → open problem:* open problems are announced to invite anyone's attack;
  parked items address the house's own future selves.

**Four worked entries, to fix the teaching shape** (the glossary carries all of them at
this depth):

- *Theorem vs. ratified note.* A theorem is descriptive and proven: the world already
  behaves this way, and here is the complete argument. A ratified design note is
  prescriptive and admitted: the system *shall* behave this way, because the owner
  merged it. Conflating them is the register's cardinal failure — a spec cannot be
  true, only in force.
- *Deskcheck vs. artifact evaluation.* The ACM ladder (policy v1.1, five badges, three
  families) puts "Evaluated–Functional" at: documented, consistent, complete,
  exercisable, with evidence of verification. That is the deskcheck's exact question,
  with the owner as the evaluation committee — a *criteria self-assessment*, since
  badges are conferred by independent evaluation and nobody self-awards one. What the
  house cannot claim: "Results Reproduced" (requires a party other than the authors —
  the fresh-agent test is the honest *analog*) and "Results Replicated" (no in-house
  analog exists; never claimed).
- *Ruling vs. axiom.* Both are admitted, not proven, and both are load-bearing
  downstream. The difference is criticism: an axiom is challenged by independence and
  consistency arguments; a ruling is challenged by filing an issue. The mapping holds
  because deduction downstream treats both as given; it breaks because rulings are
  revisable by their author and axioms, once a literature builds on them, effectively
  are not.
- *Preregistration vs. the one-way chain.* Preregistration, as the community practices
  it, means hypotheses **and an analysis plan** lodged with an **independent registrar**
  (OSF, AsPredicted) *before* data collection. The chain has something real but
  different: a timestamped design trail — capture before design before build, hardened
  at each merge. The breaks: (a) the registrar is the author — the repo is
  owner-controlled and branch history is mutable until merge, so the strongest
  timestamp is the merge commit, not a third-party lodgment; (b) the registered object
  is a design trail, not hypotheses plus an analysis plan, which is what anti-HARKing
  protection is actually about; (c) no comparative to industrial practice is claimed —
  that would be an unevidenced comparative of exactly the kind §2.3.3 prices. What
  survives, stated precisely, is still worth having: **a preregistration-style trail,
  in-house analog** — and nothing more (R8).

### 2.3 The claim ladder — what each label costs

**The principle.** A claim label encodes proof status and importance — never
enthusiasm. The ladder exists so that over-claiming becomes a *review-visible* defect:
after RR-2, a label is a checkable assertion about the evidence in the same
artifact, and review rejects mismatches the way it rejects failing tests.

#### 2.3.1 The rungs

| label | what earns it | agent-authorable? |
|---|---|---|
| **Definition** | introduces a term; no truth value; criticized as ill-formed or unmotivated, never false | yes |
| **Observation** | true by inspection or a raw measurement, pinned to a sha / run id | yes |
| **Remark** | commentary, explicitly non-load-bearing | yes |
| **Conjecture** | precise, falsifiable, believed, unproven — the falsifier named at birth | yes |
| **Hypothesis** | empirical register: a testable explanation; only ever *supported* or *falsified* | yes |
| **Claim** | an assertion the same artifact's evaluation section is contractually obliged to support | yes, with the evidence attached |
| **Proposition** | proven *relative to stated premises* — cited invariants, structure hypotheses, arithmetic domain; proof inline, checkable | yes — **the agent ceiling** |
| **Lemma** | proven auxiliary that earns the house name by later *use* (stricter than the community label — §2.2) | proof yes; the name, retrospectively |
| **Theorem** | proven, important, standalone — a complete written proof (machine-checked when Lean unparks) | effectively no; absence is honest |
| **Corollary** | immediate from a stated labeled result; proof short or omitted | yes, from a labeled result only |

The ceiling rule, stated plainly: **agent-authored claims cap at Proposition-with-
checkable-inline-proof or Claim-with-named-falsifier.** This is not modesty theater —
it is the bar the book's preamble already sets (`Proposition` there is "a consequence
the manual DERIVES from a cited invariant — its proof is given inline and is checkable
by the reader; it asserts nothing the record does not", `preamble.tex:50-53`), promoted
from book convention to chain-wide policy. "Theorem" without a checked proof is the one
register error the research community treats as fraud-adjacent; the palace will simply
never make it, because the ladder gives every weaker-but-honest rung a name.

Two guards on the rung agents will use most, because a plausible-but-wrong inline proof
— not Theorem abuse — is the realistic inflation channel:

- **"Proven" in a Proposition always means relative to admitted premises.** The
  premises are cited (invariants, structure hypotheses, arithmetic domain), and the
  proposition asserts nothing the record does not. Un-anchored "proven" is the
  theorem-conflation of the first worked entry, and review treats it as such.
- **Executable Propositions pair a property test with the prose proof.** Where the
  labeled statement is checkable by machine, the falsifier is written and run — the
  laws-ledger pattern (§2.3.2, item 3) generalized. A prose proof alone is the weakest
  verification the house accepts anywhere; the pairing keeps the ladder on the same
  mechanized-falsification footing as everything else. Falsifier F2 patrols both
  guards.

#### 2.3.2 Where labels attach

1. **Design notes** — §2 decisions may carry labels. The native registers are
   Definition and Invariant (admitted, in force); anything labeled Proposition carries
   its proof inline. Wired as template teaching comments, not new frontmatter.
2. **The deskcheck paper** — its Definitions-and-claims section (§2.4.3) is written in
   ladder labels; its Evaluation section discharges every Claim or says so honestly.
3. **The laws ledger** (dn-mathematical-foundations §2.2, `docs/LAWS.md`) — each
   algebraic law lands as a
   labeled claim (typically Claim, or Proposition with its paired falsifier) with one
   falsifier per law; the label column is specified here so the sibling note consumes
   it, never redefines it.
4. **The book** — the amsthm registry in `docs/book/preamble.tex:43-62` (principle,
   invariant, proposition, devolution) extends with conjecture / definition / lemma /
   theorem / corollary / remark environments and `\autoref` names, under a
   scribe-contract plan. One taxonomy, one home — never a parallel set. Ordering note:
   after RR-3 the claim environments live in the factored `docs/latex/palace-macros.tex`
   (§2.4.5); whichever of the scribe sync and RR-3 lands second targets the file where
   the environments then live, not a stale line pin.
5. **Issues** — no new labels. The lexicon's mapping (defect ≈ counterexample,
   investigation ≈ conjecture, ruling ≈ axiom) is descriptive teaching, not taxonomy
   change; the `type:`/`route:` grammar is frozen (§2.1).

#### 2.3.3 Reserved words and the arithmetic-domain rule

The words below are load-bearing in the research register; after RR-2 their use
costs what the community charges:

| word | costs |
|---|---|
| **proven / proof** | a complete checkable argument exists in or is cited by the artifact; a green property test is "tested", "no counterexample found" |
| **significant** | a statistical test was run and is named |
| **optimal** | an optimality proof; otherwise "best measured" |
| **correct** | a stated spec and verification against it; otherwise "conforms to tests" |
| **novel / first** | a recorded literature search; the house default is the opposite claim — instantiation of a *known* structure, which is the credible direction |
| **complete** | an enumeration or exhaustiveness argument |

And the domain rule, from the capsule's named foundational risk: **every algebraic or
equality claim states its arithmetic domain.** "Holds exactly over ℤ / exact
rationals; holds up to ε = <stated> over float64." Float addition is non-associative;
exact-equality claims over floats are precision theater, and the ladder forbids them.

### 2.4 The deskcheck becomes a paper — same artifact, deeper genre

#### 2.4.1 The genre decision

A deskcheck is not a full research paper and pretending otherwise would be register
inflation (§2.5). The genre it already *is* — "show it working, or its honest current
state, with the evaluator holding final say" — has a name in the community:
**the artifact-evaluation report / artifact appendix**. Short (target 4–8 pages),
evidence-dense, self-assessing against the pinned ACM v1.1 criteria (no badge is held
or implied — §2.4.3). That is the format adopted.

#### 2.4.2 Carrier, lifecycle, and the form choice — the compatibility spine

**Nothing about the `dc-` lifecycle changes.** Verified at HEAD: `scripts/board.py`
globs `docs/deskchecks/*.md`, requires `type: deskcheck`, and reads exactly
`{id, track, verdict}`; closure is computed, never flipped; the queue derives from
manifests. So:

- **The carrier stays `docs/deskchecks/dc-NNN.md`** with the front-matter schema
  byte-compatible (`type, id, track, date, items, audit_refs, verdict, send_back,
  links`) and the four house sections retained — What was built · How · Surprises ·
  What is NOT done. Three of them may shrink to short paragraphs pointing into the
  paper; **How keeps the runnable demo commands in full** (or points at a plain sibling
  script, `docs/deskchecks/dc-NNN/demo.sh`). The carrier alone must pass the
  fresh-agent test with no LaTeX toolchain installed: the tree stays self-sufficient;
  the paper deepens — recorded outputs, tolerances, figures — it never gatekeeps.
- **The form is chosen when the track is picked, before a word is authored.** Every
  deskcheck is track-closing (closure is computed from the approved dc, so a
  "track-closing deskchecks only" qualifier would be vacuous) — which makes the choice
  point the whole game. The owner names paper or short form when he picks the track off
  the queue; absent an owner pick, the agent proposes the form in the dc PR *before*
  writing the paper, never after the cost is sunk. **For the five currently-owed tracks
  the default is the short form** — draining real debt without waiting on RR-3, and
  minting the closure baseline F6's supplementary clause needs. The paper becomes the
  default *proposal* only after the owed queue drains; the short form remains legal
  forever. The four-question core is the invariant; the paper is the deepening, priced
  in §3 (falsifier F6 patrols the boundary).
- **The paper source lives at `docs/deskchecks/dc-NNN/main.tex`** (one directory per
  deskcheck, TikZ/pgfplots figures as sibling `.tex` files per book convention).
- **PDFs are never committed.** `docs/deskchecks/.gitignore` replicates the book's
  source-only precedent (`*.pdf`, `*.aux`, latexmk residue). Delivery rides the
  existing exhaust lane: the compiled `main.pdf` is copied to
  `~/.mind-palace/exhaust/reports/dc-NNN.pdf` (Syncthing → phone) — the lane the phone
  build report already uses. No new channel; at deskcheck time the PDF *absorbs* the
  phone report's role for that track (full retirement of the HTML report is parked).
- **`board.py` changes by zero lines.** A compatibility test (RR-3) asserts a
  paper-era dc closes its track and renders in the queue; `tests/unit/test_board.py`
  and the dormant-gate integration suite stay green unmodified.

#### 2.4.3 The section spine — the four questions, grown up

Adapted from empirical-CS practice and the artifact-appendix shape, with the house's
four headings surviving as the spine's load-bearing members:

| paper section | carries | house ancestor |
|---|---|---|
| Abstract | track, claims evaluated, verdict-relevant headline, criteria self-assessment | — |
| 1 Motivation | why the track exists — the manifest's warrant and dod, cited | track manifest |
| 2 Definitions & claims | ladder-labeled claims this artifact supports; scope of claims stated | — |
| 3 What was built | design → implementation, every assertion `\artifact`/`\coderef`-pinned | **What was built** |
| 4 Evaluation | the demonstration record: observed outputs **with tolerances**, per-dod-criterion results | **How** |
| 5 Surprises & discussion | what building revealed; negative results in full | **Surprises** |
| 6 Threats to validity | what is NOT done; construct/internal/external threats; the float-ε caveat where it applies | **What is NOT done** |
| 7 Availability & provenance | repo refs, the paper's edition sha, how to re-run; who drafted, who evaluated, how it landed | — |
| References | verified-only; DOIs recorded in-repo, never [FROM MEMORY] | external-grounding gate |

The Evaluation section records what the carrier's demo script produced — the runnable
commands live in the carrier (§2.4.2), the paper carries the observed outputs with
tolerances, so the waived short form and the fresh-agent test stay coherent.

**The provenance statement is required, not decorative.** These papers are
agent-drafted, and research-community norms now expect generative-AI involvement
disclosed in manuscripts [FROM MEMORY — stable practice since 2023]. The house already
treats agent-vs-owner authorship as a first-class coordinate
(`docs/design-notes/authorship-distance-axis.md` — dn-authorship-distance-axis, the
authorship-distance design, *draft* at HEAD, leaned on as an idea, not cited as
ratified). The honest statement is a strength, not a confession, and the template
hard-codes its shape: *drafted by <agent, tier> under supervision; evaluated by the
owner against the live demo; landed by the owner's merge.*

**The criteria self-assessment, phrased so it cannot inflate.** The template pins the
ACM v1.1 definitions — five badges, three families — and the paper states which
*criteria were met and by whose evaluation*, never that a badge or rung was "achieved"
(badges are conferred by independent committees; nobody self-awards one). The in-house
maximum reads: "meets the 'Artifacts Evaluated – Functional' criteria; evaluator: the
owner — a self-assessment against the pinned definitions; no ACM badge is held or
implied", plus the fresh-agent reproduction *analog* when a fresh session re-ran the
demo from merged artifacts alone. "Replicated" is never claimable and the template says
so. The pinned definition text carries its verification source and date, re-verified
against the fullest available primary quotation at RR-3 build time — this note's
verification ran through SIG mirrors because acm.org refuses automated fetches, which
is good enough for a design note and not for a standing pin (R6; filed as an issue).

Rules carried over from the book: assert nothing uncited (`\artifact{}` for design
claims, `\coderef{}{}` for implementation); one edition marker per paper (the `\gitref`
pattern, pinned at the demo sha); notation extends `docs/book/notation.tex`, never
forks it; figures are TikZ/pgfplots, text-only, no binary assets.

#### 2.4.4 The evidence and the verdict — the tension, resolved explicitly

The paper **carries** the evidence; it does not **replace** the owner's live approval.
The carrier's How is the demo *script*; the paper's §4 is the demo *record* — the owner
runs the script at the keyboard, per the deskcheck discipline; the paper is what makes
his evaluation repeatable and reviewable away from the keyboard (the exhaust-lane PDF),
not what substitutes for it.

How a verdict lands post-regime — the gap, stated exactly: the store's own README
(`docs/deskchecks/README.md`) specifies only the *pre-regime* mechanics — gate-guard
denial, the lazygit blessing ceremony, "the third owner-only gate" beside two retired
flips — and no artifact at HEAD writes the post-regime translation. Closed here:
**a dc lands by PR like everything else.** The agent authors the whole bundle (carrier
+ paper) with `verdict: pending` — the only agent-legal value, unchanged. At the
deskcheck session the owner runs the demo, sets `approved` or `needs-work` (+
`send_back`) **by his own hand in that PR**, and merges; the merge carries the verdict,
and `board.py` computes closure from the merged field exactly as today. The verdict
field survives as the one hand-set value because closure is *computed from it* and
because a pure merge-equals-approval reading would lose `needs-work`/`send_back`
expressiveness and force a board change for nothing. Agents still never touch it.
[INFERENCE — this regime translation is this note's proposal; nothing at HEAD
specifies it, and the owner confirms or corrects it at ratification. The ruling ask is
filed as a `route:owner` issue alongside this PR so the decision is citable either way;
meanwhile the owner's merge of this note adopts the recorded default. The
deskcheck-verdict *signing* question stays parked exactly where
dn-typed-workflow-registry (ratified 2026-07-27 — the sign-based-security design) left
it.]

#### 2.4.5 Toolchain and the DRY factoring

Toolchain: **the book's, unchanged** — `latexmk -pdf` (pdflatex; MacTeX at
`/Library/TeX/texbin`; tectonic is not installed and is not introduced). Compile:
`cd docs/deskchecks/dc-NNN && latexmk -pdf main.tex`.

The shared layer: the citation macros, claim environments, and house colors currently
live in `docs/book/preamble.tex` and are needed by an `article`-class paper. RR-3
factors them into **`docs/latex/palace-macros.tex`**, `\input` by both the book's
preamble and the paper template's — one definition, two consumers. **The factoring has
design content, and the plan says so plainly, twice over:** (a) the theorem
environments are `[chapter]`-numbered (`preamble.tex:46,55,57`) and `article` has no
chapter counter — they cannot lift verbatim; the macros file takes its numbering parent
as a parameter, or the environment definitions stay per-consumer and only the
counterless layer (citation macros, colors, `\fwdthesis`) is shared — RR-3's builder
decides which, as design scope, not as a surprise. (b) `\gitref` is the book's edition
marker and stays per-document — the book pins its edition, each paper pins its demo
sha. The move carries a two-sided compile obligation: the book builds cleanly and
renders page-identically after it, **and** the paper template compiles from the
skeleton (falsifier F4, both clauses). The include mechanism (relative `\input` vs
`TEXINPUTS`) and latexmkrc niceties remain build decisions. The notation registry
stays where it is — `docs/book/notation.tex`, single, extended never forked — and
papers `\input` it directly.

### 2.5 The honesty denylist — over-claiming as a review-visible defect

The register's credibility failure mode is decoration: research words doing prestige
work their evidence has not paid for. The rules below bind all register-bearing
artifacts and land in the glossary's front section; PR review enforces them the way it
enforces scope:

1. **R1** — "Theorem"/"proven" only per the ladder (§2.3.1, §2.3.3). The cardinal rule.
2. **R2** — "internally reviewed" / "audited", never "peer-reviewed". The merge is an
   editorial accept, not refereeing.
3. **R3** — criteria claims only per the pinned v1.1 definitions, phrased as *criteria
   met + evaluator*, never as a badge or rung "achieved" — no ACM badge is ever held or
   implied; "Replicated" never.
4. **R4** — no "novel"/"first" without a recorded search; the house's default posture
   is structure-instantiation, which is anti-novelty and credible.
5. **R5** — standard names for known objects (Ollivier-Ricci curvature, W₁/Wasserstein
   LP, finite Boolean algebra) — never house rebrands. Internal metaphors stay
   internal: "our mini Langlands" never appears in a paper.
6. **R6** — citations verified-only (the external-grounding gate); no decorative or
   from-memory references, in the deskcheck template as a hard rule.
7. **R7** — numbers carry tolerances; equality claims carry their arithmetic domain
   (§2.3.3).
8. **R8** — the chain claim is "a preregistration-style trail (in-house analog)", with
   the registrar-is-the-author break stated (§2.2's worked entry) — and nothing more.
9. **R9** — externally, the project is what it is: a single-investigator study whose
   artifacts are agent-drafted and owner-reviewed, publishing internally reviewed
   technical reports. That framing is credible and even distinctive;
   "journal/lab/research program" cosplay is what actual researchers smell instantly.

**Enforcement, priced honestly.** Under the merge gate the merging reviewer is the
owner, so R1–R9 are review load and this note does not pretend otherwise. Three
mitigations, none free but none ceremonial: the reserved-words table is grep-able and
agent pre-merge audits grep it; the paper template hard-codes the phrasings that
inflate most (the provenance block, the criteria wording); and the ladder makes the
honest label the path of least resistance. The owner's read is the last wall, not the
only one.

### 2.6 The empty slot — the research Question

A paper opens with a question. The palace, at HEAD, has none stated — the study has no
owner-authored research Question, and authoring one is owner-only by standing rule.
The register makes this absence *visible* rather than filling it: the glossary's front
matter carries the slot explicitly ("Research Question: unwritten — owner-only"), and
the deskcheck paper's Motivation section cites the track's warrant and dod, never a
global Question, until one exists. No mechanism nags; surfacing is the design's whole
obligation here. When the owner writes the Question, it becomes the anchor every
paper's Motivation may cite — and the strongest single credibility move available to
the project, because a stated question converts a collection of artifacts into a study.

## 3. Consequences

**On the owner's merge of this note, and not before** — three graduation licenses,
session-sized, dependency-ordered, split at graduation. They are named **RR-1/RR-2/
RR-3** (research register), following the parent note's WF-N unit-naming precedent —
"track" stays reserved for the board's own coordinate, per §2.1's invariant applied to
this note itself:

- **RR-1 — the lexicon.** Deliverable: `docs/lexicon.md` with every §2.2 map row as a
  complete entry per the contract (four clauses + verification status), the honesty
  denylist (§2.5), the Question slot (§2.6), and one-line register pointers in the
  templates and skills that traffic in mapped terms. The workflow manifest gains its
  working-material rows in the same diff — three DoD lines (RR-1/2/3) and a one-clause
  scope extension — a D1-licensed edit ("owner or orchestrator may add; only a
  deskcheck closes"), so the lane's own deskcheck can see this work. De-staling rides
  along: any template/skill line this unit touches that still carries retired mechanics
  (gate-guard, hand-flips, `/graduate refuses`) is rewritten to merge-gated language
  *in the same diff* — touched files never re-propagate dead regime. Falsifier: any
  entry missing its where-it-breaks clause or its verification status; or the owner's
  cold-read spot-check (F5) fails.
- **RR-2 — the claim ladder wired.** Gated on RR-1 (labels are lexicon entries).
  Deliverable: ladder + reserved-words + domain-rule conventions into
  `docs/templates/design-note.md` and `docs/templates/build-plan.md` as teaching
  comments; the issue skill's descriptive mapping paragraph; a minted scribe-contract
  item extending the book's amsthm registry (`preamble.tex:43-62` pattern, `\autoref`
  names, notation untouched; post-RR-3 home is `palace-macros.tex` — §2.3.2's ordering
  note). Falsifier: F2 — a post-RR-2 merged artifact labels property-test evidence
  "proven", or a Proposition lands past its guards, and review passes it.
- **RR-3 — the deskcheck paper.** Gated on RR-2 (the paper writes in ladder labels).
  Deliverable: the evolved `docs/templates/deskcheck.md` (carrier, schema
  byte-compatible), the `docs/templates/deskcheck-paper/` LaTeX skeleton (spine of
  §2.4.3, provenance block, criteria definitions pinned with recorded verification
  source per R6), `docs/latex/palace-macros.tex` factored with the two-sided compile
  obligation (§2.4.5), `docs/deskchecks/.gitignore`, **`docs/deskchecks/README.md`
  rewritten to the §2.4.4 mechanics** (it still teaches the retired lazygit/gate-guard
  ceremony — filed as a defect issue with this PR), the exhaust-lane delivery step, and
  the board compatibility test. Falsifiers: F3 (board), F4 (compile, both sides).

**Priced, so the owner ratifies with the bill visible.** The short-form carrier is
minutes of agent work and a 1–2 page read. A paper is a dedicated authoring session per
deskcheck — order 5–10× the carrier — plus the owner's review of a 4–8 page PDF and its
`.tex` diff on top of the same live demo. The exhaust-lane PDF moves that review
off-keyboard; it does not shrink it. The five currently-owed tracks default to the
short form (§2.4.2), so the owed queue costs nothing new; the paper's bill starts only
where the owner picks it, and F6 fires if a bundle ever exceeds one authoring session.

**Independence declared, so nobody serializes what need not wait:** the five
currently-owed deskchecks (agentic-loop, fiber-geometry, inner-outer-core, ops,
sync-diac-dreamers) do **not** wait on any of this — they default to the 17-line short
form, and the queue never blocks on a design note. The sibling foundations note (§1.3)
proceeds independently; only the label definitions are shared, and they are frozen
here.

**First real exercise — two artifacts, not one.** The first paper-format deskcheck is
an owner session off the existing queue — his pick of track — producing that track's
`dc-NNN` as the first paper. That *exercises* the RR-3 pipeline; it does not close this
note's own lane. Closing the workflow lane still requires an approved dc naming
`track: workflow` (computed closure, `board.py:309-327`), evaluated against the
manifest's RR rows — the board's phase function does not care which pipeline the dc was
typed in.

**Explicitly NOT licensed:** the laws-ledger sweep (dn-mathematical-foundations
MF-1..MF-3); Lean beyond the sibling's L-ladder (its MF-4..MF-6); authoring the
Question; retiring the HTML phone report; disposing of the dormant gate machinery;
book chapter content beyond the registry extension; any parser change.

## 4. Wiring & enablement

**How it wires:** `docs/lexicon.md` (new, authored); one-line register pointers in
`docs/templates/{design-note,build-plan,deskcheck,capsule}.md` and the issue/pr/
checkpoint skills; ladder teaching comments in the design-note and build-plan
templates; the workflow manifest's DoD rows (D1-licensed working material);
`docs/templates/deskcheck.md` evolved in place (carrier schema byte-compatible) plus
`docs/templates/deskcheck-paper/main.tex` (spine, provenance block, pinned criteria
with verification source, `\input` of `docs/latex/palace-macros.tex` and
`docs/book/notation.tex`); `docs/latex/palace-macros.tex` factored from
`docs/book/preamble.tex` with the counter-parent question resolved as RR-3 design
scope and the book re-pointed at it; `docs/deskchecks/.gitignore` (book precedent);
`docs/deskchecks/README.md` rewritten to the post-regime verdict mechanics; the
compile target documented in the template (`cd docs/deskchecks/dc-NNN && latexmk -pdf
main.tex`); the delivery step copying `main.pdf` →
`~/.mind-palace/exhaust/reports/dc-NNN.pdf` (existing Syncthing lane; whether as a
documented command or a small extension of `scripts/exhaust_report.py` is a build
decision); a board-compatibility test asserting a paper-era dc closes its track.
`scripts/board.py`: zero lines. `CLAUDE.md`: zero lines.

**What it takes to flip it on:** (a) RR-1 merges → the glossary is live on read;
(b) RR-2 merges → the next authored note/plan carries the ladder, live on first
use; the registry extension lands at the next scribe sync; (c) RR-3 merges → the
pipeline is runnable end-to-end: template → `latexmk` → PDF → exhaust lane. The
owner's only hand-acts: pick a track off the deskcheck queue *and name the form*, sit
the deskcheck session, run the carrier's demo script, set the verdict by hand, merge
the dc PR — the same acts the deskcheck discipline always required, now optionally
producing a paper. No daemon flag; this is workflow tooling — `mind-palace deploy` is
not involved.

## Parked decisions

| decision | default recorded | re-entry condition |
|---|---|---|
| Lean / proof-assistant adoption | L0 — ladder specified in dn-mathematical-foundations §2.4 (L1 = its MF-4 unit) | for L1: the laws ledger's first laws exist to state (issue #48) |
| external venue / arXiv / DOI | none — internally reviewed technical reports only | the owner authors the Question and wants external referees |
| brainstorm capsules adopting the register | chat stays vernacular; capture template gains only the Conjecture gloss (RR-1) | owner asks, after living with RR-1 |
| HTML phone build report | kept for mid-track build waves; the dc PDF absorbs the track-closure role | two paper deskchecks delivered → owner reviews the overlap |
| dc verdict mechanics (§2.4.4) | owner-hand field, landed by his merge; agents write only `pending` | the `route:owner` issue filed with this PR — merging this note adopts the default |
| dormant deskcheck-gate machinery | untouched — carrier stays shape-compatible, tests stay green | a hooks-disposition sweep opens, or the tests redden (the `parked` issue with this PR) |
| lexicon drift maintenance | no standing sweep minted; entries carry verification status | an entry teaching a retired mechanic or stale term — a `type:defect` reopens RR-1 for it |
| bibliography tooling | manual `thebibliography`, DOI-verified entries (the SYNC.md pattern) | a single paper exceeds ~10 external references |
| the research Question | slot exists, empty, labeled empty | owner-only authorship, any time — not a condition of anything here |

The dormant-machinery row's members, named (this half is prose, not a cell):
`.claude/hooks/gate-guard.sh`, `_lib.py`'s verdict clauses, and the 346-line
`tests/integration/test_deskcheck_gate.py` — all green-but-dormant at HEAD.

## Falsifiers — what would prove this design wrong

The owner ratifies falsifiers, not proofs.

- **F1 (alias invariant):** any RR-1..3 merge renames a machine-parsed string
  (§2.1's enumerated list) without its parser in the same diff, or breaks an existing
  id or command. Grep-checkable at review; one occurrence voids §2.1.
- **F2 (bar raised, not decorated):** a post-RR-2 merged artifact carries
  "Theorem"/"proven" over property-test-only evidence; **or** a merged Proposition's
  inline proof fails a cold-check; **or** an executable Proposition lands without its
  paired falsifier — and review passes it. The ladder then decorates instead of
  binding, and §2.3 has failed as policy.
- **F3 (board compatibility):** a paper-era dc fails to move its track to CLOSED, or
  the queue misrenders it, or `test_board.py`/`test_deskcheck_gate.py` redden without
  intentional cause. The carrier contract (§2.4.2) is then broken.
- **F4 (DRY compile parity, both sides):** after the `palace-macros.tex` factoring the
  book fails `latexmk` or renders divergent pages, **or** the paper template fails to
  compile from the skeleton. The shared layer then forked instead of factored, and
  §2.4.5 must be redone.
- **F5 (the glossary teaches):** the owner cold-reads three glossary entries and cannot
  recover house meaning, research meaning, and the breaking point. The lexicon then
  renames instead of teaching, and RR-1's deliverable is not done.
- **F6 (evolution, not ritual):** a dc bundle (carrier + paper) exceeds one authoring
  session; or the owner declares at a verdict session that the paper delayed his
  verdict; or a track is waived to the short form because the paper felt too heavy.
  Any one firing shrinks the default to carrier-only and the paper becomes opt-in.
  (A relative clause — median time-to-closure versus the short-form baseline — only
  becomes measurable once short-form closures exist; the five owed tracks defaulting
  short-form mints that baseline, and the clause then activates as a supplement, never
  as the operative test. At HEAD zero deskchecks have ever been recorded, so no
  baseline exists yet and this note does not pretend one does.)
- **F7 (register inflation):** any merged artifact says "peer-reviewed", claims a
  badge or an unmet criterion, or carries an internal metaphor in external register.
  The §2.5 denylist then failed at review, and its rules move from glossary prose into
  the pr skill's audit guidance as a grep-able list — not a new ceremony, a sharper
  grep.

## Cross-references

Code and templates (all at `68d8d39`): `scripts/board.py:283-294` (dc scan — the
front-matter contract §2.4.2 preserves), `:309-327` (computed closure), `:445-494`
(queue rendering); `docs/templates/deskcheck.md:1-17` (the carrier, evolved in place);
`docs/deskchecks/README.md` (pre-regime verdict mechanics — rewritten in RR-3, never
propagated); `docs/book/preamble.tex:28` (`\gitref` edition marker), `:30-35`
(`\artifact`/`\coderef`), `:43-62` (the amsthm registry §2.3.2 extends), `:46,55,57`
(the `[chapter]`-numbered environments behind §2.4.5's counter-parent scope);
`docs/book/notation.tex:1-4` (the single symbol registry); `docs/book/.gitignore` (the
source-only precedent); `scripts/readmap.py:27`, `scripts/capsule.py:41,62` (frozen
parse points, §2.1); `.claude/skills/issue/SKILL.md:24-38` (the label taxonomy the
lexicon maps); `.claude/skills/book/SKILL.md` (LaTeX conventions authority);
`.claude/skills/checkpoint/SKILL.md` (the fresh-agent test — the reproduction analog).

Artifacts, glossed: `docs/brainstorms/mathematical-foundations.md` (the warrant capsule,
PR #42, sequenced first — owner seeds 1–2, the terminology seeds,
structure-instantiation, the falsifiers-before-proofs epistemology, the float-ε risk);
`docs/design-notes/track-board-and-deskcheck-gate.md` (dn-track-board-and-deskcheck-gate,
ratified 2026-07-21 — D2's derived board untouched; D3 minted the deskcheck artifact
this note evolves, and D3's verdict-hook mechanics predate the merge-gated regime and
are not propagated; D1 licenses the manifest DoD edit);
`docs/design-notes/erratum-relation.md` (dn-erratum-relation, ratified 2026-07-27 — the
correction composition the lexicon's retraction row maps);
`docs/design-notes/external-grounding.md` (dn-external-grounding, ratified — the
verified-citation gate, R6); `docs/design-notes/dn-typed-workflow-registry.md`
(dn-typed-workflow-registry, ratified 2026-07-27, pre-regime — parks deskcheck-verdict
signing; park preserved §2.4.4); `docs/design-notes/authorship-distance-axis.md`
(dn-authorship-distance-axis, *draft* at HEAD — authorship distance as a first-class
coordinate; the provenance block's conceptual ancestor, not a ratified citation);
`docs/DESKCHECK-QUEUE.md` (derived — the five owed tracks, never hand-edited);
`docs/tracks/workflow.md` (this note's track manifest, pre-existing; gains RR DoD rows
in RR-1).

External (per the external-grounding gate): ACM Artifact Review and Badging v1.1 badge
definitions — VERIFIED 2026-08-09 via sigir.org and sigsim.acm.org quoting the policy
(acm.org itself refused the fetch; re-verification against the fullest primary source
is an RR-3 obligation, filed as an issue); AE practice at SOSP/OSDI/EuroSys/ATC/FAST —
VERIFIED via sysartifacts.github.io. Claim-ladder community norms, the empirical-paper
spine, the threats-to-validity taxonomy, the AI-disclosure norm, **and the
research-meaning glosses of the §2.2 map wholesale** (preregistration practice,
shepherding, the retraction genre, axiom-criticism norms, the artifact-appendix shape)
are stable community practice carried here as [FROM MEMORY] — admissible in a design
note, barred from any paper bibliography until verified per R6; RR-1's glossary
records per-entry verification status so the distinction survives into the artifact
that teaches it.