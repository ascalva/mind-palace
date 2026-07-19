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
