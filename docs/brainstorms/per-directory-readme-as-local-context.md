# per-directory-readme-as-local-context

## 2026-07-27T17:14:00Z

```capsule
topic: per-directory-readme-as-local-context
date: 2026-07-27

seed (owner, verbatim): |
  "every subdir should have their own README, acts as agent context for that current directory, not
  recursive in tree indexing, each dir only carries info on what files it holds, and give just
  enough context within subdirs"
```

## WHAT IT IS — the thinness rule, applied spatially

`CLAUDE.md` is deliberately short because **every token there is paid on every turn**; depth lives in
skills that load only when invoked. This is the same economics applied to **place** instead of to
**task**: context for `core/kernel/stores/` is paid only by an agent already standing in
`core/kernel/stores/`.

⚑ **"Not recursive" is the whole design, not a simplification.** A README that summarises its
subtree is a summary that goes stale every time anything below it moves, and it re-creates the
accumulator: one file that must know about everything under it. A README that describes **only the
files it directly holds** has a bounded, locally-checkable truth condition — and a mechanical one:
*does every file in this directory appear, and does every entry name a file that exists?*

⇒ That is a **lint**, which is what makes this different from a documentation wish. It is the same
shape as the board's orphan check.

## ⚑ WHY IT MAY MATTER MORE THAN IT LOOKS

Two of this week's measured defects are directly addressed:

- **The stale `core/stores/sourceset.py` citation** — three independent agents inherited a path that
  had moved in the kernel migration. A directory README is where a moved file's absence is *locally
  visible*, and the lint would have flagged the empty slot.
- **Re-derivation as the real context cost** ([[context-load-as-a-feedback-loop]]): the measured load
  was never the mandatory frame — it was agents rediscovering the same ground. A local README is
  ground that does not need rediscovering, and is paid for only on arrival.

## ⚑ THE RISK, NAMED — this is an accumulator with N seeds

L1 in the feedback-loop diagnostic is *self-maintained · monotonic · no external check*. A README
per directory is **N of those**, and the seat's own history is the warning: the surface built to
retire a 568-line brief reached 568 lines in a day.

The structural defences, borrowed from what already worked:

1. **Bounded by construction** — a README describes only direct children, so its length is bounded
   by directory size rather than by history.
2. **PULLED, never pushed** — it must never enter a mandatory read path. This is the retrospective
   template's own guard ([[the-false-success-rule]] sibling), and the resume brief's disease was
   precisely *push*.
3. **Mechanically checkable** — coverage and existence are lintable, so drift is a red test rather
   than a discovered disappointment ([[structural-enforcement]]: a property is real only when
   something proves it).
4. `[INFERENCE]` **A line cap**, so "just enough context" is enforced rather than hoped for.

## ⚑⚑ OWNER REFINEMENT (2026-07-27) — GENERATED, NOT AUTHORED. THE RISK DISSOLVES.

> *"i know there's automated doc tools whose only purpose is to generate package/subpackage docs,
> nothing an ai writes, just a simple auto generated index, short and sweet"*

**This is a better answer than the four guards above, and it retires most of them.** A generated
index is **not an accumulator at all** — it is a *pure function of the directory's contents*, so:

| L1 clause | does it hold? |
|---|---|
| self-maintained | **no** — the writer never reads it |
| monotonic | **no** — regeneration replaces, it does not append |
| no external check | **no** — regenerate-and-diff is the check |
| authority laundering | **no** — no agent authored it, so no agent claim can hide in it |

⇒ It joins the **derived-pane family** (`handoff.md`, `TRACKS.md`, `DESKCHECK-QUEUE.md`): it has a
**fixed point**, so a `--check` mode is the whole correctness story, exactly as the handoff's is.
Guards 1–4 above collapse into one: **never hand-edit it.**

### The distinction that decides whether it is worth anything

- A generated **file listing** is worthless — `ls` already does it, and an agent has `Glob`.
- A generated **API index** — public symbols, signatures, and the first line of each docstring — is
  **not free**. Obtaining it otherwise means reading the files, which is precisely the
  re-derivation cost [[context-load-as-a-feedback-loop]] measured as the real context load.

⇒ The value is in the *extraction*, not the *inventory*.

### ⚑ DOES CORE ALREADY HAVE THIS? — yes, verified, and it changes the build

`core/ingest/code_corpus.py` already walks the AST for the code-embed lane and produces exactly the
needed fields: `qualname`, `signature`, `docstring`, `line_start`, `line_end`
(`:71-74`, `:99-109`, `:160-169`). L0a headers are literally `# {path}:{qualname}{signature}`;
L1 carries module and symbol docstrings.

⇒ **A per-directory index is a projection over data the palace already parses.** Reaching for
`pdoc` / `sphinx-autosummary` / `mkdocstrings` would duplicate a live extractor — the DRY defect
this owner treats as a defect rather than a nit, and the same self-containment principle that says
core never outsources what it already has. `[INFERENCE]` A third-party tool may still win on
*rendering* polish; it should not win on *extraction*.

### What is still authored, if anything

`[INFERENCE]` The generated index answers *what is here*. It cannot answer *why this directory
exists* or *what does not belong in it* — the judgement half. Options, unranked: accept the loss and
keep it purely generated (simplest, and the owner's stated preference); or a single hand-written
intent line above a generated block, with the lint covering only the generated half. **Not decided.**

## OPEN
- **Does it collide with the ring/firewall structure?** `core/kernel/**` has a ratchet and an import
  firewall; a README there should probably state the ring rule, and that is a claim that can go
  stale against `core/kernel/rings.py`. Cite, do not restate.
- **Every directory, or every directory an agent is likely to stand in?** `__pycache__` obviously
  not. `[INFERENCE]` The honest scope is probably "every directory in a write_scope anyone has held."
- ⚑ **Degenerate input** ([[the-false-success-rule]]): a README containing only the directory name
  satisfies "a README exists" and carries nothing. The lint must assert *coverage of the files*, not
  *presence of the file*.
