# bp-135 — journal

## Pre-build notes for whoever picks this up

- ⚑ **This is the first of five plans that fill the reviewer's seat before the grant vacates it.**
  Read `bp-135` §0 and §12 before anything else. If you find yourself building `bp-138`'s
  cryptography "while you're in here", stop — the wave's ordering is the safety property.

- ⚑ **`docs/TRACKS.md` and `docs/DESKCHECK-QUEUE.md` are in `write_scope` for a reason.**
  `tests/unit/test_board.py:212-226` runs `--write`, which writes both. They carry a
  `<!-- GENERATED … do not hand-edit -->` banner: **regenerate, never edit**. If your diff shows a
  hand-shaped change in either, you have gone wrong.

- **Four existing `test_board.py` tests will redden the moment you add the column** (idempotence
  `:99`, row width `:106`, queue membership `:133`, `--write` byte-equality `:212-226`). That is
  expected and pre-widened; it is not a surprise to file a finding about.

- **The live tree has almost no data for the "audit: present" path** — `docs/tracks/ops.md:7-8` is
  the only manifest with a populated `audit_refs`, and `docs/deskchecks/` holds zero records. Write
  the acceptance against fixtures and record the live census honestly (§7 Item 8's falsifier).

- ⚑ **finding-0208's line citations are stale by five lines** (`:123,142,150` → `:128,147,155`).
  Fix them in the finding while resolving it and say so here.

- **The nested `verdict:` mapping in §6 is illustrative only.** `_lib.parse_front_matter` is a YAML
  subset with no nesting. Ship the flat `verdict_artifact:` / `verdict_record:` keys. Do not write a
  YAML parser.
