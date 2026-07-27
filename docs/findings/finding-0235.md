---
type: finding
id: finding-0235
status: open
created: 2026-07-26
updated: 2026-07-26
links:
  - docs/design-notes/scored-beliefs-and-earned-entitlement.md   # :4 — the corrupted `track:` value
  - docs/tracks/scored-beliefs.md                                # the manifest it should match
  - docs/TRACKS.md                                               # :130 — the corrupted orphan warning
  - scripts/board.py                                             # the DERIVED generator that reads it
  - docs/findings/finding-0085.md                                # the same footgun, on `write_scope`
  - docs/findings/finding-0233.md                                # why no agent can fix this one
ftype: codebase
origin_plan: orchestrator
route: orchestrator
resolution: null
---

# A ratified design note's `track:` value carries an inline `#` comment, so the whole comment is
# glued into the slug — the board reports a phantom orphan, and no agent is permitted to fix it

## What

`docs/design-notes/scored-beliefs-and-earned-entitlement.md:4` reads:

```yaml
track: scored-beliefs      # manifest minted with this note (docs/tracks/scored-beliefs.md); owner renames/rejects at ratification
```

`[GROUNDED]` The repo's own parser does not strip the comment. Run against the live file:

```
>>> read_front_matter(...)['track']
'scored-beliefs      # manifest minted with this note (docs/tracks/scored-beliefs.md); owner
 renames/rejects at ratification'
```

The entire comment is part of the value. `docs/TRACKS.md:130` shows the consequence verbatim:

```
⚠ artifact with no manifest: scored-beliefs-and-earned-entitlement → track: scored-beliefs
  # manifest minted with this note (…) (no docs/tracks/scored-beliefs      # manifest minted
  with this note (…).md manifest)
```

— the generator is looking for a manifest file whose name contains the comment. Two lines later it
reports `manifest 'scored-beliefs' has no plan/note members yet`. **Both statements are false and
they are each other's mirror image:** the note *is* a member of that track, and the manifest *does*
exist. The board simply cannot join them, because one side of the join is corrupted.

⚑ **This is finding-0085's footgun in a second field.** That finding records the identical failure
on `write_scope` — `scope-guard` reads each unquoted list entry literally, so
`- eval/metrics.py  # absorbed` matches nothing and denies the builder a file its plan grants. The
rule that came out of it ("bare globs only; rationale goes in §5 prose") was written for
`write_scope` and never generalized. **It is a front-matter-wide hazard, not a `write_scope` one.**

## Why it matters

**1. It corrupts a DERIVED artifact, which is the class we are told to trust.** `TRACKS.md` and
`DESKCHECK-QUEUE.md` are generated and never hand-edited, precisely so they can be believed. A
silently mis-parsed field makes the generator confidently wrong — and it *looks* like a finding
("⚠ artifact with no manifest") rather than a parse failure, so a reader chases the wrong problem.

**2. It is invisible to the deskcheck queue that depends on it.** Track membership is how work is
grouped for the third owner gate. A note that cannot be joined to its manifest is a note whose
track can never show it, so a deskcheck on `scored-beliefs` would report an empty track.

**3. ⚑ NO AGENT CAN FIX IT — and finding-0233, filed the same day, is why.** The file is a
**ratified** design note. `scope-guard` denies any agent write to a ratified note at
`_lib.py:435-441`, returning *before* the write-scope capability check is even reached; the Stop
audit's (b2) clause blocks the Bash path. A9/A8 make that immutability deliberate, not a bug. So
the remedy for a one-character parsing defect is an **owner hand-edit**, exactly as it is for a
lettered amendment.

## The ask

**An owner hand-edit**, one line, in `docs/design-notes/scored-beliefs-and-earned-entitlement.md`:

```yaml
track: scored-beliefs
```

— move the comment to the note's prose, or drop it (its content is already true and recorded: the
manifest exists at `docs/tracks/scored-beliefs.md`). Then `uv run scripts/board.py --write` and the
phantom orphan and the phantom-empty manifest both disappear together.

⚑ **Do not "fix" this by teaching the parser to strip `#`.** Comment-stripping a YAML scalar is
ambiguous — a legitimate value may contain `#` — and finding-0085 deliberately left the robustness
half optional for that reason. The durable fix is the authoring rule plus detection, below.

## The generalization worth building

finding-0085's rule exists for `write_scope` only. Two instances in different fields is enough to
generalize it:

- **Authoring rule:** front-matter *values* carry no inline `#` comments, in any field. Rationale
  goes in prose. State it wherever the templates are described, not only in the write-scope section.
- **Detection (cheap, and the part that makes it a control rather than a note):** a ratchet asserting
  that no front-matter scalar in `docs/**` contains `  #`. It would have caught this at authoring
  time, costs one test, and needs no parser change. ⚑ It also cannot be *fixed* by an agent once a
  note is ratified — which is the argument for catching it while the note is still `draft`.

## Re-entry condition

Nothing is parked and no build is blocked. The corruption is cosmetic today because the
`scored-beliefs` track has no plan members yet — but it becomes load-bearing the moment that track
acquires plans or is deskchecked, and it is silently wrong until then.

Re-entry: the owner's hand-edit, then regenerate the board. The detection ratchet is separable and
can ride any plan that touches `scripts/board.py` (bp-124 does).

## Routing

`codebase` → but **the orchestrator**, not a builder, because the fix is structurally
agent-impossible (above). Spotted by the bp-124..127 sub-orchestrator, which correctly declined to
act on it as outside its mandate and did not file it; verified independently and filed here.
