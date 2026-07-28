# bp-141 — journal

## Pre-build notes for whoever picks this up

- ⚑ **First act, before any code: `git check-ignore -v data/registry-pending.jsonl`.**
  If it does not exit 0, STOP (§10). `.gitignore` is deliberately out of `write_scope` — a
  non-ignored pending file becomes permanent tree churn that the bp-142 export ratchet will
  fight forever.

- ⚑ **Invariant 6 is the one that must not bend.** A blessing does not happen degraded. An
  event queued in the pending file whose `to_status` is in `PRIVILEGED_TARGETS` must be
  invisible to `fold()`. If you find yourself writing "just for reads" — stop. That is a
  blessing manufactured by an outage.

- **Verify bp-140's `submit()` behaviour before building on it.** The plan requires it to
  return the existing seq on a duplicate idempotency key, not raise. Check the landed code;
  if it raises, that is a bp-140 defect — file a finding, do not add a second dedupe layer.

- **Dry-run is the default for both `reconcile` and `import`.** `--apply` must print the
  full report in the same invocation before writing anything. The recovery import never
  auto-merges: divergence is a conflict for the owner (note §2.9(3)(i)).

- **The F3 drill needs two failure shapes, not one:** a *missing/unreadable* store and a
  *locked* store (hold an exclusive transaction from a second process). A read that survives
  the first but blocks on the second has not discharged invariant 5.

- **Reuse, don't re-derive:** `scripts/board.py`'s scanners and `.claude/hooks/_lib.py`'s
  front-matter parser are the import path's inputs. `scripts/handoff.py:57-61` shows the
  sys.path idiom.

- **Local gate before sealing:** ruff · `scripts/check_imports.py` · mypy (scripts floor 0,
  tests baseline 69) · `ops.type_gate` · pytest with the standard deselects.

## Entries

_(none yet — this plan is `proposed`; the first entry is written by the build session)_
