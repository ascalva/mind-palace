---
description: Compute book debt and mint a proposed scribe sync plan for docs/book/.
---
Mint a book-sync plan. The book is a derived projection of the ratified record and
the codebase (§3); it asserts nothing without citing a source. Use the **book**
skill for chapter map, voice, TikZ/notation conventions, and citation scheme.

1. **Compute book debt.** Read `docs/book/SYNC.md` (git ref + artifact ids last
   incorporated). Book debt = design notes now `ratified` or `superseded`, plus
   findings now `promoted`, that are newer than that marker. (If `docs/book/`
   does not exist yet, the debt is the initial scaffold + first edition.)
2. **Mint a sync plan** at `docs/build-plans/<id>/plan.md` against
   `docs/templates/build-plan.md` with:
   - `contract: scribe`, `status: proposed`, `session_budget: 1`
   - `write_scope: ["docs/book/**"]`
   - **§2 context manifest**: the debt delta (the specific notes/findings/code refs)
   - **Fixed acceptance on every sync plan:** whole-book review; every snippet and
     code citation re-verified against HEAD (each carries `source: path@ref`);
     clean compile (latexmk or tectonic — record the default on first run); zero
     undefined references; `docs/book/SYNC.md` updated (git ref + artifact ids).
   - Split by chapter cluster if the debt exceeds one session (standard rule).
3. Emit `status: proposed` only — the owner's ready-flip is the milestone
   confirmation (§11). Execution then flows through `/build` like any plan.

Report the sync plan id and the debt it covers.
