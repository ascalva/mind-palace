# strip-headers-from-the-atom-hash

## 2026-07-27T15:50:00Z

```capsule
topic: strip-headers-from-the-atom-hash
date: 2026-07-27
status: OWNER RULED. Resolves the fork the adversarial panel opened against
        dn-vector-membership-store. The note is `draft`; the revision pass carries this in.

seed (verbatim): |
  "I say strip headers from the hash, a filename is mutable, it can change over time, if we keep
  the headers, then we can't even rename or move a file in the code, in the docs, the chain would
  keep breaking, we need the rename/form taxonomy"
```

## THE RULING

**`content_hash` pins to the header-free body.** Identity only — the **embed text may keep its
headers**, so retrieval quality is untouched. What changes is what counts as *the same atom*.

⇒ `dn-vector-membership-store` §1.2's non-goal — *"atoms are whatever the (unchanged) chunkers
emit"* — is **amended**, not preserved. That non-goal was the thing forcing the defect.

## ⚑ WHY THE OWNER'S ARGUMENT IS STRONGER THAN THE PANEL'S

The panel (math seat F1, systems seat #3) framed the header defect as a **capability** loss:
`# {path}:{qualname}` and `# {path}:{lineno}` sit inside the hashed text, so identical code in two
files hashes differently and cross-file dedup is unreachable outside L0b.

The owner reframed it as a **correctness** loss:

> **A filename is mutable.** Rename or move a file and every chunk re-hashes — so the `(path, slot)`
> occupancy chain **breaks**, on an operation performed constantly, in code *and* in `docs/`.

⇒ This is not a missing feature. It is the **lineage guarantee failing under routine work** — and
this repo renames and moves files as a matter of course (the kernel migration moved `sourceset.py`;
the panel found three artifacts still citing its old path). A membership store whose chains sever on
`git mv` cannot serve the succession path it exists to enable.

## WHAT IT RESTORES

`finding-0168`'s **addendum 4** (2026-07-25) named **rename-as-membership-edge** and raised
edit-stable chunk identity from cleanup to **load-bearing**. The note — written 07-23, before the
addendum — carries it in no risk, acceptance, or parked decision; the core and math seats both
flagged the orphaned precondition. This ruling reinstates it as the design's spine rather than a
footnote, and the rename/fork taxonomy (D4, D6, PD-1) stops being structurally vacuous.

## THE COST, MEASURED — and it is not the efficiency

The systems seat measured both branches by running the real chunkers over every ledger version:

| branch | dedup factor |
|---|---|
| headers kept in the hash | **2.05×** |
| headers stripped from the hash | **2.15×** |

⇒ **The ingest-efficiency motive is nearly indifferent to this choice.** The ruling is not bought
with throughput — it is bought for **lineage survival across renames**, which the efficiency framing
alone would have undersold. `[INFERENCE]` The real cost is design surface: identity now differs from
embed text, so anything joining the two must say which it means.

## WHAT THIS DOES NOT RESOLVE

The panel raised defects that stand independently of the header question, and the revision owes all
of them: **revert** corrupts the current view and cycles the atom projection (found twice,
independently); **merges** break §4's total order, since the ledger walks all commits while chains
are first-parent only; `commit_diffs` is asserted "already captured" when **zero tables exist live**;
the 4–5× duplication claim was never measured; set-vs-multiset is unpinned; Lance churn has no
compaction path. Stripping headers fixes one thesis-level defect, not the note.
