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
