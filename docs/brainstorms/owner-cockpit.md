# Brainstorm — the owner cockpit: tmux + LazyVim as the reading room; the curated read surface

> Captured by the orchestrator from a live owner brainstorm (2026-07-18 evening local, fable
> session-29). Owner's seed, verbatim: *"one thing that I also want you to focus is my interaction
> with the ui, I will be using lazy vim to be reading everything, so we can also create a
> specialized tmux session for me to have lazy vim next to claude code, my programming workflow is
> something I love, and making it more tailored to me is the point."* Mid-session refinement:
> *"because I still do want to read design documents, I still want to read code, maybe I don't need
> to be reading every test, but a focused way of coding, the relevant coding."* Feeds bp-072 (v1
> tooling, with decision-routing v1); no design-note gate needed for the tooling itself.

## 2026-07-19 UTC (session-29)

### Why this is load-bearing, not cosmetic

Per the owner's own dyadic-epistemology capture (S2, same evening): intrinsic enjoyment of the
process is the incentive-compatibility condition of the whole epistemology — the thing that keeps
scrutiny honest all the way down. A workflow the owner loves is infrastructure. Tailoring the
cockpit maintains the foundation everything else stands on.

### The cockpit

A named tmux session **`palace`**, created idempotently by `scripts/cockpit.sh` (attach if it
exists, build if not; panes rooted at the repo):

- **Window "desk"** — LazyVim left, **opened on the docket**; Claude Code right. The session opens
  by *reading what awaits*, not by asking the agent what is pending.
- **Window "ops"** — `palace status` / daemon log tail / suite state. Glanceable, not resident in
  attention.
- **Status bar** — `scripts/docket.py --count` in tmux status-right ("3 awaiting"): the decision
  queue as ambient signal. The owner never checks the docket; they notice it.

### The interaction contract (the efficiency mechanism)

**Read in vim · decide in dialogue · act by keystroke.**

- **Read in vim:** artifacts (plans, seals, design notes, journals, diffs) are read natively —
  never summarized into chat. Shifts read-load off the dialogue (cheaper sessions; the chat narrows
  to what it is for: scrutiny and decisions — the dyadic part).
- **Live buffers:** vim `autoread` + tmux `focus-events on` ⇒ when the agent checkpoints a journal
  or updates an artifact, the buffer refreshes on pane focus. The owner watches a build live
  without `:e`.
- **Act by keystroke:** the blessing act from the buffer just read — `<leader>pb` shells out
  `palace bless <plan-id>` (owner-run; the agent never touches it; Stop-gate audit unchanged).
  Scrutiny and approval become one motion; deliberateness preserved, friction ~zero.

### The curated read surface (the mid-session refinement)

The owner's reading is tiered the same way approvals are — **design documents and load-bearing code
are always read; mechanical tests are counted, not read**:

- **Read maps on every seal.** Each sealed plan's journal/seal carries a "read this" section: the
  ordered, load-bearing ~20% as `file:line` spans with a one-line *why* each — the 3 files that
  matter, the diff hunks that carry the design, the tests that encode interesting falsifiers.
  Mechanical coverage is summarized by count ("+11 tests; 3 worth reading: the falsifiers").
- **Vim-native traversal:** `scripts/readmap.py <plan-id>` emits a quickfix-format list
  (`file:line: note`) so the review is `:cfile` + `]q` — a native vim walk of the curated reading.
  (Later, `:PalaceRead <id>` in the plugin.)
- **The guide-not-gate rule (trust surface, named honestly):** the agent curating the read map is a
  filter that could hide things. Mitigations: the FULL diff is always one `:DiffviewOpen` away; the
  read map is a guide, never the only path; audit sampling (decision-routing's gauge) occasionally
  reads beyond the map. Curation aids attention; it never substitutes for access.
- **Reading tiers:** design notes — written for the owner, always read (this never changes with any
  automation). Kernel/inner-core code — always on the map. Machinery code — on the map when novel,
  else summarized. Tests — falsifier-encoding ones on the map; mechanical coverage counted.

### The dotfiles boundary (keeping the tailoring honest)

**The repo owns the session and the data** (`cockpit.sh`, `docket.py`, `readmap.py`, the bless
CLI); **the owner's dotfiles own the editor.** The repo ships a documented snippet block
(`docs/supplemental/cockpit.md`: autoread + focus-events, the `<leader>pb` binding, quickfix
read-map recipe, render-markdown suggestion) that the owner adopts by hand — proposals into a
config they love, never injections. If the snippets prove sticky: a tiny optional `palace.lua`
(`:PalaceDocket`, `:PalaceBless`, `:PalaceRead`, statusline docket count) as v1.5 — parked.

```capsule
topic: owner-cockpit
date: 2026-07-18   # owner local; appended 2026-07-19 UTC

decisions:
  - The cockpit is load-bearing infrastructure (dyadic-epistemology S2), designed as such.
  - The interaction contract: read in vim, decide in dialogue, act by keystroke; artifacts are read
    natively, not summarized into chat.
  - Reading is tiered: design docs + load-bearing code always; falsifier tests on the map;
    mechanical tests counted, not read. Every seal carries a READ MAP (file:line + why).
  - Read maps are guides, never gates: full diff always one command away; audit sampling reads
    beyond the map.
  - Repo owns session+data; the owner's dotfiles own the editor (snippets proposed, adopted by
    hand).

parked:
  - decision: palace.lua neovim plugin (:PalaceDocket/:PalaceBless/:PalaceRead, statusline count)
    default: documented snippets only (docs/supplemental/cockpit.md)
    re_entry: the snippets prove sticky and the owner wants native commands
  - decision: exact desk-window layout (splits, sizes, which pane focused on attach)
    default: vim left on docket, claude right; tuned live at first use
    re_entry: first cockpit session — owner taste decides, then pinned in the script

open_questions:
  - Does `focus-events on` (a global tmux option) go in the snippet doc only, or may cockpit.sh set
    it session-side without touching the owner's global config?
  - Read-map authoring cost: hand-written per seal (start here) vs derived from the diff + journal
    (later automation)?
  - Should the docket open as the vim landing buffer, or a dashboard (e.g. snacks.nvim dashboard
    with docket + recent seals)?

next_steps:
  - Fold into bp-072 with decision-routing v1: cockpit.sh + docket.py + readmap.py + bless CLI +
    docs/supplemental/cockpit.md. Leaf write_scope (scripts/**, two docs paths); papercut-tier;
    owner blesses manually.
  - Seals begin carrying read-map sections immediately (process change, no build needed).
  - bp-069 remains the lead build; bp-072 rides parallel (disjoint write_scope).

references:
  - docs/brainstorms/decision-routing.md         # the docket/batch lane this is the reading room for
  - docs/brainstorms/dyadic-epistemology.md      # S2 — enjoying the process is load-bearing
  - scripts/palace.py                            # CLI home; cockpit/bless naming consistency
  - docs/inbox/owner-questions.md                # absorbed/adjacent: the docket generalizes this
  - LazyVim · tmux focus-events · diffview.nvim · render-markdown.nvim   # the toolchain
```

---

## 2026-07-25 UTC (session-49)

### Owner ask — `gf` should resolve an ARTIFACT ID, not just a path

Verbatim: *"I like that when I type gf over a build plan file, it goes there, can you make it such
that that is the behavior everywhere else? sometimes I forget what a file did with just the name,
so something like dn-supervision-and-liveness should route and open the correct file if I 'gf'
when cursor is on top of the path/filename, so that I can easily find files and read context, it
would be useful for reading the context manifest."*

**Why this is load-bearing, not convenience.** It is the editor-side twin of the standing
`gloss IDs inline` rule (never make the owner hunt for what an id means). That rule fixes the
*chat* surface; this fixes the *reading* surface. The stated use case is the decisive one: a build
plan's **§2 context manifest** is a dense list of ids, and today reading it means leaving the file
to go look each one up. `gf` on the id collapses that to one keystroke — which is exactly the
"focused way of reading the relevant thing" the original cockpit capture asked for.

### The mechanism — `includeexpr`, not a plugin

`gf` already does most of the work: it grabs the token under the cursor using `isfname`, passes it
through **`includeexpr`**, then resolves the result against `path` with `suffixesadd`. So the whole
feature is one transform function. No plugin, no keymap override, and `gf` keeps working on real
paths for free (return the input unchanged when it doesn't match an id pattern).

Sketch of the routing table, as the ids actually appear in the corpus:

| id form | target |
|---|---|
| `bp-NNN` | `docs/build-plans/bp-NNN/plan.md` |
| `bp-NNN` + `journal` in context | `docs/build-plans/bp-NNN/journal.md` |
| `finding-NNNN`, `f-NNNN` | `docs/findings/finding-NNNN.md` |
| `dn-<slug>` | `docs/design-notes/dn-<slug>.md` |
| track slug | `docs/tracks/<slug>.md` |
| brainstorm topic | `docs/brainstorms/<topic>.md` |
| `oq-NNNN` | ⚠ NOT a file — a **section** of `docs/inbox/owner-questions.md` |
| `dc-NNN` | ⚠ NOT a file — lives in a track manifest / `DESKCHECK-QUEUE.md` |

### ⚑ Two problems a naive prefix map gets wrong — both found by looking, not assumed

1. **Design-note naming is NOT uniformly `dn-` prefixed, and bare slugs COLLIDE.** Verified:
   `docs/brainstorms/supervision-and-liveness.md` + `docs/design-notes/dn-supervision-and-liveness.md`
   (prefixed, unambiguous) but `docs/brainstorms/inner-outer-core.md` +
   `docs/design-notes/inner-outer-core.md` — **the same bare slug in two directories**. So a bare
   slug cannot be resolved by prefix alone. Options: (a) precedence order (design-note wins, since
   the ratified artifact outranks the brainstorm that fed it), (b) fall back to a picker when >1
   hit, (c) normalize the naming so every design note carries `dn-`. **(c) is the real fix** — the
   inconsistency is a corpus defect that this feature merely surfaces; it probably also confuses
   grep-based lookups and the routing map. Worth a finding on its own.
2. **`oq-` and `dc-` are section anchors, not files.** `gf` opens files. Resolving these needs an
   open-then-search (jump to the heading), which `includeexpr` alone cannot express — it needs a
   small wrapper mapping on `gf` that special-cases them, or accept "opens the file, you search."

### Where it should live

**Project-local, committed with the repo** — the routing table is a function of the artifact
layout, so it should version alongside it rather than rot in personal dotfiles. nvim's `exrc`
supports a repo-root `.nvim.lua` (trusted once via `:trust`). That also means it only fires inside
the palace, and a layout change updates the resolver in the same commit.

Open: whether to scope it to `markdown` only (an ftplugin) or repo-wide.

### Status

Captured, not built. Small and self-contained — one lua function plus `.nvim.lua`. The corpus
question in problem 1 should be settled first, since the resolver encodes whatever answer we pick.

### Owner refinement, same session — a TYPED REFERENCE instead of a rename

Verbatim: *"you can also just refer to brainstorms with a bs- prefix, so if a document has a path,
easy, if it has the name of the file, add the prefix, or some prefix, something like
`<doc-type>:<name-with-or-without-extension>`, so `dn:supervision-and-liveness` is acceptable."*

**This is the better idea and it retires the rename proposal.** The disambiguation moves out of the
*filename* and into the *reference*. `inner-outer-core` stops being ambiguous not because we renamed
a file but because the citation now says which plane it means. Corollary: the design-note naming
inconsistency (`dn-` on some, bare on others) stops being load-bearing — still worth tidying, no
longer blocking.

It is really two things, and they should not be conflated:
1. **An authoring convention** — how ids are written in docs from now on. Touches CONVENTIONS /
   the templates / the `gloss IDs inline` rule.
2. **A resolver** — the `includeexpr` that turns a typed reference into a path.

The resolver must accept **both** typed and bare forms regardless: the corpus already contains
thousands of bare `dn-…` / `finding-NNNN` / `bp-NNN` references and they are not getting rewritten.
Typed wins when present (unambiguous); bare falls back to precedence + picker.

#### ⚑ The separator matters more than it looks — MEASURED, not assumed

| form | isfname change | collision risk |
|---|---|---|
| **`bs-supervision-and-liveness`** (hyphen — the owner's own first phrasing) | **none** — `-` is already in `isfname` | none |
| `bs:supervision-and-liveness` (colon) | **required** — `:` is NOT in the default | ⚑ real, see below |

Measured this session: nvim's default is `isfname=@,48-57,/,.,-,_,+,,,#,$,%,~,=` — **no colon**.
So `gf` on `dn:supervision-and-liveness` today grabs only one side of the colon.

And the cost of adding it is not hypothetical: **1,753 `path:line` references** live in
`docs/build-plans/` + `docs/design-notes/` alone (the §3 grounding convention — `queue.py:222`,
`launcher.py:676`). Putting `:` in `isfname` makes `gf` swallow the `:222` on every one of them,
breaking the plain-path case that **works correctly today**. That is a regression traded for a
cosmetic gain.

Mitigable — `includeexpr` can strip a trailing `:%d+`, and **`gF` already jumps to file+line
natively**, so `path:line` arguably wants `gF` anyway. But it is added machinery in service of a
separator, not of the feature.

#### Recommendation

**Take the hyphen form: `bs-<slug>`, `dn-<slug>`, `bp-NNN`, `finding-NNNN`, `oq-NNNN`, `tr-<slug>`.**
- Zero editor surgery; `-` is already a filename char.
- Consistent with every id the corpus already uses — `bp-108` and `finding-0199` are ALREADY
  virtual ids that don't match their filenames (`bp-108` → `docs/build-plans/bp-108/plan.md`), so
  `bs-<slug>` → `docs/brainstorms/<slug>.md` introduces no new concept.
- Leaves the 1,753 `path:line` refs untouched and working.

The colon reads slightly better as "typed reference", and if that legibility is what the owner
wants, it is buildable — the cost is the `isfname` change plus a strip rule, and it should be a
deliberate trade, not a side effect. **Owner's call; recommendation is hyphen.**

Unchanged from the capsule above: `oq-` and `dc-` resolve to **section anchors, not files**, so
they need an open-then-search wrapper either way.

### Owner generalization — a REFERENCE STANDARD for the whole corpus

Verbatim: *"maybe that is a new standard for references in docs, at least when written so it's easy
to navigate in an unambiguous way, something like
`<doc-type><delim><filename-optional-ext><optional-line-delim><optional-line-number>`."*

This is a bigger move than the `gf` resolver: the resolver becomes the *consumer* of a corpus-wide
convention rather than a bag of heuristics. Worth stating plainly — **it also reverses the
recommendation two capsules up.**

#### ⚑ Why the hyphen recommendation is WITHDRAWN

The earlier argument for `-` over `:` was that `:` is absent from nvim's default `isfname`, so
adding it would make `gf` swallow the `:222` on 1,753 existing `path:line` refs.

**Folding the line number into the grammar dissolves that objection.** If `[<line-delim><line>]` is
part of the standard, the resolver needs a line-suffix rule *regardless* of which delimiter we pick
— so the "extra machinery" is no longer a cost attributable to the colon; it is a requirement of
the feature. And once it exists, `:` is strictly the better choice:

- `path:line` is the **universal** convention (compilers, stack traces, ripgrep, `gF`), already used
  1,753 times here. A standard that reuses it inherits every tool that already speaks it.
- `gF` parses `file:line` **natively**. Pick `:` and `gF` works on typed refs for free.
- `-` is ambiguous *inside* the grammar: slugs contain hyphens (`supervision-and-liveness`), so
  `dn-supervision-and-liveness` needs the parser to know `dn` is a type rather than the first word
  of the slug. `:` cannot collide — slugs never contain colons.

Corrected cost statement: adding `:` to `isfname` breaks the 1,753 refs **only if** `includeexpr`
lacks a strip rule. With it, `gf` → file, `gF` → file+line. That is neutral-to-better, not a
regression. The earlier capsule overstated it.

#### The grammar

```
<ref>       ::= <type> ":" <name> [ ":" <line> ]
<type>      ::= dn | bs | bp | f | oq | tr | dc | au | src
<name>      ::= <slug> | <slug>".md" | <path>          # extension optional
<line>      ::= [0-9]+
```

| ref | resolves to |
|---|---|
| `dn:supervision-and-liveness` | `docs/design-notes/dn-supervision-and-liveness.md` |
| `dn:inner-outer-core` | `docs/design-notes/inner-outer-core.md` — **the collision, now unambiguous** |
| `bs:inner-outer-core` | `docs/brainstorms/inner-outer-core.md` |
| `bp:108` | `docs/build-plans/bp-108/plan.md` |
| `bp:108/journal` | `docs/build-plans/bp-108/journal.md` |
| `f:0199` | `docs/findings/finding-0199.md` |
| `tr:ops` | `docs/tracks/ops.md` |
| `oq:0035` · `dc:NNN` | ⚠ **section anchors, not files** — open-then-search |
| `src:scheduler/queue.py:222` | the file, at line 222 |
| `scheduler/queue.py:222` (bare) | implicit `src:` — **the 1,753 existing refs stay valid** |

Note the `dn:` row does the real work: it resolves whether or not the file carries the `dn-` prefix,
which is why this **retires the rename** rather than deferring it.

#### ⚑ Two decisions the standard has to make

1. **Uniform, or typed-only-where-ambiguous?** `bp-108`, `finding-0199`, `oq-0035` are already
   globally unique — they need no type tag. Only slug-named artifacts (`dn`, `bs`, `tr`) actually
   collide. Minimal-change says tag only those; uniformity says tag everything because one rule is
   easier to teach, lint, and machine-read than "tag it when you sense ambiguity." **Recommend
   uniform for NEW writing, with bare forms permanently accepted by the resolver** — the corpus has
   thousands of bare refs and they are not getting rewritten.
2. **Retrofit: no.** Accept bare forms forever. A migration would touch nearly every doc for no
   navigational gain (bare `bp-108` already resolves unambiguously).

#### ⚑ Enforcement — otherwise the standard rots

Per the owner's own standing rule (`structural enforcement`: a property is real only when a test
proves it), a reference convention with no validator decays silently — a typo'd or stale
`dn:foo` looks identical to a good one until someone hits `gf` and gets nothing.

Proposal: **`scripts/check_refs.py`** walks `docs/`, extracts every typed ref, asserts each resolves
to a real file (or a real anchor for `oq:`/`dc:`), and joins the green gate next to
`scripts/check_imports.py`. That also makes it a **ratchet against link rot in general** — the
corpus is heavily cross-referenced and nothing currently checks that any of it points anywhere.
Arguably the validator is worth more than the `gf` feature that motivated it.

#### Status / gate

Captured, not adopted. This is an **authoring-convention change**, so it touches `CONVENTIONS.md`,
`docs/templates/`, and the `gloss IDs inline` rule — not a system design note. Sequence if adopted:
(1) settle the two decisions above → (2) write the convention into `CONVENTIONS.md` + templates →
(3) `scripts/check_refs.py` + gate → (4) the `.nvim.lua` resolver. The editor feature is LAST; it
is the payoff, not the foundation.

### Owner refinement — GRADUATED precision, and what it costs

Verbatim: *"something that allows us to be exact about the file, or even exact about a specific line
ref if we need to be more specific."*

Confirms the optional tail in the grammar above. Worth naming the property directly: a reference
carries **exactly as much specificity as the author needs, and no more** —

| ref | precision |
|---|---|
| `dn:supervision-and-liveness` | the artifact — "this note" |
| `dn:supervision-and-liveness.md` | the exact file |
| `dn:supervision-and-liveness:42` | the exact line |
| `src:scheduler/queue.py:222` | the exact line of code |

Each level is a strict refinement, so an author can start loose and tighten without changing form —
and `gf` / `gF` do the right thing at every level.

#### ⚑ But line precision DECAYS, and this corpus has already been bitten

A file ref is stable under edits; **a line ref is correct only until the file changes.** Not
hypothetical here — grounded, `bp:105/journal` Checkpoint 1:

> *"`ops/lifecycle/snapshot.py:574,585` → the file is **431 lines**. `stalled` is at
> `snapshot.py:191`, `wedged` at `snapshot.py:202`. Same predicates, different lines; `f:0188`
> carries the same stale refs."*

Two artifacts (a build plan's §2 manifest **and** a finding) both cited line numbers that pointed
past the end of the file. The builder re-anchored by reading — which is exactly the manual lookup
this whole standard exists to abolish.

⚑ **This is what the validator can and cannot do.** `scripts/check_refs.py` can prove a *file*
exists. It **cannot** prove a line number still points at the thing meant — `:574` in a 431-line
file is catchable (out of range), but `:191` drifting to `:202` is not. So a naive validator would
have caught one of the two failures above and issued a clean bill for the corpus that still
contained the other.

Options, in increasing strength:
1. **Range check only.** Cheap, catches gross rot (out-of-range), silent on drift. Better than
   nothing; do not let it read as "refs verified."
2. **Symbol anchors** — `src:scheduler/queue.py#_effective_priority` instead of `:222`. Stable
   under insertion/deletion, and checkable *by name*, which is the property line numbers lack. Costs
   a symbol-resolution step in the resolver; only works where a named symbol exists.
3. **Commit-pinned lines** — `src:queue.py:222@33defda`. Exact and honest ("true as of this commit")
   but immediately archaeological, and `gf` can't open a past blob without extra machinery.

**Recommend (2) for code, (1) as the floor for everything.** Line numbers stay legal — sometimes
there is no symbol — but the convention should prefer a symbol anchor when one exists, precisely
because the failure above was two artifacts drifting off the same two predicates that *did* have
names. Line-precision is the level to reach for last, not first.

Open for the owner: whether the standard should actively **discourage** bare line refs in docs
(as opposed to code comments), given the decay evidence.

### Owner extension — a finding prefix, and a reserved SUBTYPE slot

Verbatim: *"also findings can have a prefix as well, owner questions already do, maybe you can
define a finding as `f?:<name>`, where `?` can be any char to help organize findings if we need to."*

Two separable proposals. **Take the first, reserve-but-do-not-populate the second.**

#### 1. `f:` as the finding prefix — yes, adopt

Already in the grammar above (`f:0199` → `docs/findings/finding-0199.md`). It restores symmetry:
`oq:0035` and `f:0199` are the same shape, and today's `finding-0199` is the only artifact id that
spells its type out in full. Cheap, no decisions blocked.

#### 2. `f?:` — a subtype char. ⚑ Reserve the SYNTAX; do NOT fill it yet.

The instinct is sound — leaving a growth slot in a grammar is cheaper than retrofitting one. But
populating it now would freeze an **incoherent vocabulary** into every citation in the corpus.

**Measured this session — the corpus runs TWO disjoint ftype vocabularies simultaneously:**

| `docs/templates/finding.md` set | n | `CLAUDE.md` routing set | n |
|---|---|---|---|
| discovery | 51 | spec-fidelity | 22 |
| spec-defect | 50 | direction | 24 |
| question | 3 | design | 13 |
| blocker | 1 | math · codebase | 10 |
| **105** | | **69** | |

That is `f:0193` exactly ("the ftype vocabulary in the finding template and CLAUDE.md are disjoint
sets"), **still `open` and unruled**. A subtype char has to draw from *some* closed vocabulary, and
there is currently no single one to draw from. ⇒ **`f:0193` is a hard prerequisite.**

#### ⚑ The deeper objection — ftype is MUTABLE, and identifiers should not be

Even after `f:0193` is ruled, encoding type into the *reference* is the wrong shape:

- **A finding's type changes.** Triage re-routes and re-types; a `discovery` becomes a
  `spec-defect` once someone proves it bites. The id is cited from plans, journals, other findings,
  track manifests, and the book.
- **A stale subtype still RESOLVES — it just lies.** `fb:0199` for a finding that is no longer a
  blocker opens the right file and misinforms the reader silently. That is strictly worse than a
  broken link, which at least fails loudly. Compare the line-ref decay above: same failure mode,
  larger blast radius, because a retype invalidates *every* citation at once rather than drifting
  one.
- **The filename would have to encode it too**, so a retype means a file rename → git history
  break + every existing ref dead.

General principle worth writing into the standard: **identifiers are opaque and stable; attributes
live in frontmatter and in derived views.** The corpus already follows it everywhere else —
`bp-108` does not encode its track or status, and `docs/TRACKS.md` is generated rather than named.

#### What actually serves the stated goal ("help organize findings")

A **derived index** — `scripts/board.py` for findings: group by ftype / route / status / track,
regenerate, never hand-edit. Same pattern already proven twice (`TRACKS.md`, `DESKCHECK-QUEUE.md`).
It gives filtering and grouping *without* putting mutable state in a name, and it stays correct
across retypes for free. If the want is to see the type *while reading a ref*, that is a resolver/
picker affordance (show frontmatter on completion), not an identifier change.

#### Recommendation

Grammar reserves the slot: `<type> ::= f | f<subtype-char> | dn | bs | …` — **syntax legal,
vocabulary empty**, so adopting it later costs nothing and needs no re-parse. Populate only if
(a) `f:0193` is ruled AND (b) someone shows a real need the derived index cannot serve.

### Owner correction — anchor to a SECTION, not a line ⚑ (supersedes the line-ref design)

Verbatim: *"you're right, maybe line number is a bad metric, you can maybe anchor a ref to a
section/subsection/exact parking condition/etc, so instead of `:line`, it's `:<doc-anchor>`."*

**Adopt. This is strictly better than the line form and it repairs the standard's weakest joint.**

#### ⚑ The corpus already does this — informally, thousands of times

Measured: build-plan prose carries **673 × `§3`, 580 × `§6`, 342 × `§2.3`, 341 × `§2.4`,
315 × `§4`** … The convention exists; it is simply not machine-resolvable. This is not a new
notation to teach — it is **making an organic convention executable**, which is a far cheaper
adoption than inventing one.

And the anchors are unusually stable *here* because build plans are template-generated: §0 Mode,
§1 Objective, §2 Context manifest, §3 Investigation & grounding, §5 Write scope, §6 Interfaces
pinned inline, §7 Items, §10 Stop-and-raise, §11 Parked decisions, §12 Dependency summary — the
**same numbers in every plan, by construction**. `bp:110#§10` means "that plan's STOP conditions"
forever. No line number is that durable, and unlike a heading slug it cannot be reworded.

#### ⚑ It fixes what the validator could not do

The line design left a hole I flagged two capsules up: `check_refs.py` can prove a *file* exists and
can catch an out-of-range line, but **cannot** prove `:191` still means what `:574` meant — the
exact drift that bit `bp:105`'s §2 manifest and `f:0188`.

**An anchor is checkable by name.** `dn:supervision-and-liveness#§2.3` either matches a heading in
that file or it does not. Rename the section and the ref fails **loudly, at gate time**, instead of
silently pointing at whatever moved into those coordinates. That converts the validator from
"catches gross rot" to a genuine ratchet — and it is the thing that makes the standard
*self-defending* rather than another convention that decays.

#### ⚑ It dissolves the `oq:` / `dc:` special case

Flagged twice above as a wrinkle: *"`oq:0035` and `dc:NNN` are section anchors, not files."* Under
this design that stops being an exception — **they are simply anchor refs into a shared file**:

    oq:0035   ≡   docs/inbox/owner-questions.md  #oq-0035
    dc:NNN    ≡   the track manifest             #dc-NNN

One mechanism, no special-casing, and the open-then-search wrapper the resolver needed for them is
now the *primary* code path rather than a carve-out.

#### Anchor kinds, by stability

| anchor | example | stability |
|---|---|---|
| template section | `bp:110#§10` | **highest** — template-defined, same in every plan |
| heading slug | `dn:supervision-and-liveness#the-worker-protocol` | high — breaks on rewording, loudly |
| frontmatter field | `bp:119#re_entry` | high — schema-defined |
| named element (parking condition, falsifier, criterion) | `bp:110#F2` | medium — depends on local naming discipline |
| line number | `src:queue.py:222` | **lowest — last resort**, keep only where no name exists |

#### Separator

Propose **`#` for anchors**, keeping `:` for the residual numeric line case:

    <ref> ::= <type> ":" <name> [ "#" <anchor> | ":" <line> ]

- `#` is the universal fragment convention (URLs, markdown), so it reads correctly with no
  explanation, and it is **already in nvim's default `isfname`** — no further surgery.
- Numeric-vs-anchor stays trivially parseable, and it matches the code form already proposed:
  `src:scheduler/queue.py#_effective_priority`.

⇒ The grammar's optional tail is now **`#<anchor>` preferred, `:<line>` tolerated**. The earlier
capsule's line-centric framing is superseded.

### Owner ask — jump on a bare `§3`. ⚑ And the reason he "forgets" is a CORPUS DEFECT, not memory

Verbatim: *"sometimes I also easily forget when you use a symbol like §3, so being able to move my
cursor over and jump to file would be amazing."*

The feature is right. But grounding it turned up something more important: **a bare `§N` in this
corpus is genuinely ambiguous about WHICH DOCUMENT it indexes**, so the difficulty is a property of
the notation, not of the reader.

#### The evidence — one file, bare `§N`, two different targets

`docs/build-plans/bp-110/plan.md`:

| line | ref | actually means |
|---|---|---|
| 69, 71 | `§2.3`, `§2.7`, `§2.10` | **the design note's** sections (`dn-supervision-and-liveness`) |
| 82, 109, 131, 152 | `§10` | **the plan's own** §10 (Stop-and-raise) |
| 105 | `§2.3` | the note's — recoverable only from the prose *"The note's §2.3"* |
| 237 | `§2.3` | the note's — **inside a docstring, with no qualifier at all** |

The same token means different files depending on surrounding sentence. Line 237 is the sharp case:
it survives into shipped source, where the disambiguating prose does not travel with it.

⚑ **No editor feature can resolve this.** A jump-to-section keymap over line 237's `§2.3` has no way
to know it means the note rather than the plan. **The notation has to be fixed first; the tooling is
downstream of that.** This is the same shape as the `dn-`/`bs-` slug collision that started the
thread — ambiguity in the *reference*, discovered because someone tried to make it executable.

#### What the standard should say

Bare `§N` = **the current document**, always. Crossing documents **requires** qualification:

    §10                                  -- this document's §10
    dn:supervision-and-liveness#§2.3     -- explicit, unambiguous, resolvable
    bp:110#§10                           -- explicit even when self-referential

That makes `bp-110`'s line 237 read `dn:supervision-and-liveness#§2.3` — self-contained, and it
still means the right thing after it is copied into a docstring. It also lets the validator check
cross-document `§` refs, which today are unverifiable by construction.

⇒ This directly extends the standing `gloss IDs inline` rule (never make the owner hunt for what an
id means) from ids to **section references**, which are the denser and more frequent case: 673 ×
`§3`, 580 × `§6`.

#### The two jumps — different mechanisms

1. **Bare `§N` → intra-document motion.** Not `gf` (nothing to open): a keymap that searches the
   current buffer for `^#+ N\.` / `^#+ §N`. Cheap, and it works on the corpus **as it stands today**
   — no convention change required, which makes it the right thing to build first.
2. **Qualified `<type>:<name>#§N` → open + jump.** The resolver from the capsules above; same
   open-then-search path already required for `oq:` / `dc:`.

Build (1) immediately for the reading-room win; (1) is also the honest partial answer while the
notation question is still open. (2) lands with the standard.

#### ⚑ Worth escalating separately

The bp-110 line-237 case is a live hazard, not a hypothetical: a builder reading that docstring has
no local way to know which document's §2.3 is meant, and bp-110 is **blessed-pending and about to
be built**. Candidate for a finding against the plan (spec-fidelity), independent of whether the
reference standard is ever adopted.

### Owner refinement — `:` everywhere; the anchor is what follows the SECOND colon

Three messages, same session, converging: *"or even `::<anchor>` for ':' consistency"* · *"for the
sake of brevity, if a document references itself, it can use the shorthand `:<anchor>`"* ·
**`"anchors only come after the second colon"`**.

The last one is the rule, and it **resolves the tension between the first two**: a single-colon
`:§10` contradicts it, while `::§10` satisfies it exactly — empty type, empty name, anchor still
after the second colon. So the self-reference needs **no special case**; it is the general form with
the first two fields elided. Adopt `::<anchor>`.

#### The grammar, settled

```
<ref>    ::= <type> ":" <name> [ ":" <anchor> ]     -- cross-document
           | ":" ":" <anchor>                       -- self-reference (fields elided)
<anchor> ::= "§" <num>            -- template section: the corpus's native form
           | <heading-slug>
           | <symbol>             -- code: prefer over a line
           | <digits>             -- a LINE: last resort, only where nothing is named
```

| ref | meaning |
|---|---|
| `dn:supervision-and-liveness` | the note |
| `dn:supervision-and-liveness:§2.3` | the note, §2.3 |
| `bp:110:§10` | that plan's STOP conditions |
| `::§10` | **this** document's §10 |
| `src:scheduler/queue.py:_effective_priority` | the symbol |
| `src:scheduler/queue.py:222` | the line — numerically distinguishable, last resort |

⚑ **The line form is no longer a separate production.** A line number is simply a numeric anchor, so
`path:line` — all 1,753 existing refs — is already a well-formed instance of the grammar. The
notation absorbs the corpus's most common reference form instead of competing with it.

#### ⚑ Measured this session — the `isfname` cost, stated honestly

| char | in nvim's default `isfname`? |
|---|---|
| `§` | **yes** (matches `@`) — `gf` can grab a section anchor as-is |
| `#` | **yes** |
| `:` | **no** |

So choosing `:` over `#` for consistency does cost the one `isfname` change — `#` would have been
free. That is a real trade and it is being made deliberately: **one separator, one rule to teach,
and `path:line` absorbed for free** in exchange for `vim.opt_local.isfname:append(":")`. One line of
config. Worth it.

(The earlier `#`-for-anchors proposal is superseded. `§` matching `isfname` was the open risk in the
anchor design — it does, so the corpus's native `§N` form works under `gf` with no rewriting.)

#### Consequence for the resolver

Parsing is a split on `:` with the anchor as the last field when >1 colon is present; an empty first
field means self-reference. Unambiguous because slugs and Unix paths contain no colons. The
self-reference case resolves to the **current buffer**, so `::§10` is an intra-document motion —
which is exactly the jump-on-`§3` feature asked for above, now expressible in the standard rather
than needing a bespoke keymap.

### Owner refinement — TYPE ELISION by context

Verbatim: *"you can play with anchors, if you are in a dn that references another dn, something like
`:<other-dn>:<opt-anchor>` also works since that's the assumed context."*

This completes the grammar with one rule: **an empty leading field inherits from the current
document.** Self-reference and sibling-reference stop being two features and become one:

| form | fields | means |
|---|---|---|
| `dn:supervision-and-liveness:§2.3` | type, name, anchor | fully qualified |
| `:supervision-and-liveness:§2.3` | ⌀, name, anchor | **same type** as current doc, different file |
| `:supervision-and-liveness` | ⌀, name | same type, no anchor |
| `::§10` | ⌀, ⌀, anchor | **same file** (name also elided) |

Parsing stays a plain split on `:` — `["", "supervision-and-liveness"]` vs `["", "", "§10"]` are
distinguishable by arity, and slugs/Unix paths contain no colons. Nothing about the resolver gets
harder. Reading a design note that cites three sibling notes, the `dn:` repetition genuinely is
noise, so the brevity is earned.

#### ⚑ But elision reintroduces the exact defect this standard was invented to kill

Two capsules up, the bp-110 finding: a bare `§2.3` **inside a docstring** (`plan.md:237`) loses its
meaning the moment it leaves the paragraph that disambiguated it. Elided refs have the same
property, and one case is worse than the original:

- `::§10` pasted into another build plan **still resolves** — every plan has a §10 by template. It
  does not fail; it silently points at a different document's STOP conditions.
- `:supervision-and-liveness` pasted from a design note into a build plan now means
  `bp:supervision-and-liveness` — resolves to nothing, or to the wrong thing.

This corpus copies text between artifacts constantly: plans quote notes, findings quote plans,
docstrings quote plans (proven), the book quotes everything. **A context-dependent reference is
correct exactly until someone moves it**, and the failure is silent rather than loud — which is the
property that made bare `§N` a defect in the first place.

⇒ Brevity and portability are genuinely in tension here. Neither is wrong; the standard has to say
*where* each applies.

#### Proposed rule — elision is scoped, and the scope is CHECKABLE

**Elided forms are legal only in running prose inside `docs/`.** The fully qualified form is
required wherever a reference travels:

| context | form required | why |
|---|---|---|
| prose in a doc | elided OK | the context is present and stable |
| **source code / docstrings** | **qualified** | proven hazard — `bp-110:237` ships into `.py` |
| **findings** | **qualified** | cited from plans, notes, journals, the book |
| **the book** | **qualified** | assembled from many sources |
| commit messages, chat, journals | **qualified** | no surrounding document at all |

⚑ **This is enforceable, which is the point.** `scripts/check_refs.py` knows the file it is reading,
so "elided ref outside `docs/`" is a mechanical check — not a style note anyone has to remember.
Same move as the `§`-anchor validation: the convention defends itself, or it decays.

Open for the owner: whether journals count as prose (they are `docs/`, but they are also the
handoff surface a fresh agent reads cold, which argues for qualified).

### Owner — don't force `gf`; and the binding question

Verbatim: *"you don't have to force it into gf if it won't work, this could be a different binded
action, a more powerful one."* Then, self-corrected: *"jf could also be nice, jump-to-file"* →
*"oh wait, that's a nav binding, so I cant."*

**The self-correction is right:** `j` is motion-down, so any `j`-prefixed mapping makes every `j`
press wait `timeoutlen` for a possible second key. That is a tax on the most-used key in the editor.
(The common `jk`-as-escape trick accepts exactly this cost; here it buys nothing.)

#### ⚑ Releasing `gf` retroactively makes the COLON FREE — the thread's oldest debate dissolves

The entire hyphen-vs-colon argument (two reversals, several capsules) turned on one fact: `:` is not
in nvim's default `isfname`, so `gf` could not grab it.

**That constraint only exists if the mechanism is `includeexpr`.** A custom action grabs the token
itself — `expand('<cWORD>')` plus a pattern — and `isfname` never enters into it. So:

- **no `isfname` change**, hence no risk to the 1,753 `path:line` refs, hence the last remaining
  objection to `:` is gone;
- `gf`/`gF` keep working **exactly as today** on real paths — zero regression surface;
- the separator choice becomes purely a *legibility* decision, which is how the owner was choosing
  it anyway.

`includeexpr` was always the weak vehicle: it returns a **filename and nothing else**, so it cannot
express an anchor jump, a picker, an in-buffer motion (`::§10` opens no file at all), or a preview.
Every interesting part of this standard was fighting that ceiling.

#### What the dedicated action can do that `gf` cannot

1. Parse the full grammar — type/name/anchor, elision, `::self`.
2. **Jump to the anchor**, not just the file.
3. **In-buffer motion** for `::§10` — no file opened.
4. **Picker on ambiguity** — the pragmatic answer for the thousands of legacy bare refs that will
   never be rewritten: offer the candidates instead of guessing.
5. ⚑ **Gloss without leaving the buffer** — this is the owner's ORIGINAL complaint (*"sometimes I
   forget what a file did with just the name"*). Jumping answers it; a hover that renders the
   target's frontmatter (title, type, status) answers it **faster and without losing your place**.

#### Binding proposal

| key | action | note |
|---|---|---|
| **`gf`, markdown-only** | the smart ref jump, falling back to built-in `gf` when the token is a plain path | keeps existing muscle memory — the ask that started this thread was literally *"I like that when I type gf over a build plan file, it goes there"*. Rebinding the KEY is not the same as forcing the MECHANISM. |
| **`K`, markdown-only** | the gloss/hover | thematically exact (`K` = "what is this"), and free in markdown where there is no LSP hover |
| `<leader>`-prefixed | picker / open-in-split | which-key discoverable, zero conflict |

Avoid `gr`/`gd` (LSP: references/definition) and anything on a motion prefix.

Recommendation: **`gf` + `K`, scoped to markdown via ftplugin.** Nothing new to memorize, nothing
shadowed outside `docs/`.
