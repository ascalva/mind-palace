# Golden set — a frozen capability anchor

This directory is one of the system's two **fixed points** (BUILD-SPEC §15, Invariant 9).
It is **hand-blessed and never auto-modified by any agent** — only the owner changes it,
deliberately, with the change logged.

- `corpus/` — a small **synthetic** fixture corpus. Deliberately *not* the owner's private
  vault: a frozen anchor must be reproducible across machines and over time, and the live
  vault is private and changes. These notes are invented, contain no private data, and are
  safe to commit.
- `golden_set.json` — fixed queries with known-good expected retrievals (`expected` titles
  are corpus filenames without `.md`) and the retrieval depth `k`.
- `baseline.json` — the blessed metric values. A relevant change must not regress these
  (`eval.golden.regressions`). Re-bless with `python scripts/eval.py --bless` only when the
  owner intends to move the anchor (e.g. after a deliberate embedding-model change).

Capability metrics are deterministic (`eval/metrics.py`): recall@k, set overlap (Jaccard),
mean cosine distance. The *behavioral* fixed point (the Constitution) is checked separately
in `core/selfcheck.py`.

Run it: `python scripts/eval.py` (prints the report); add `--bless` to write `baseline.json`.
