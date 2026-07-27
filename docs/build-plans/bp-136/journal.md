# bp-136 — journal

## Pre-build notes for whoever picks this up

- ⚑ **The single most important degenerate input in this plan is `classify({})`.** The obvious
  implementation — walk H1…H8, return CONTINUE if none matched — returns **CONTINUE** on the empty
  object, which is invariant 7 exactly inverted. Write Item 9 first and let every later item compose
  on a function that is already total.

- ⚑ **`oq-0047` is ANSWERED** (`docs/inbox/owner-questions.md:1653`, *"YES — `ftype` BECOMES THE
  ROUTING AXIS"*) **and nothing implements it.** `grep -rn ftype .claude/hooks/ scripts/ core/`
  returns zero and `docs/templates/finding.md:9` still carries the old vocabulary. So H1 ships the
  conservative reading §2.4 licenses. Do **not** sweep the template — that is a separate plan.

- **H5 has no evidence source.** `scope-guard` prints `DENY:` and nothing persists it. The plan's
  answer is declaration-plus-refusal, not a new hook write. If you find yourself editing
  `.claude/hooks/`, stop: that is `oq-0036`'s territory and it is parked.

- ⚑ **Exit 1 means HALT — the safe outcome.** Document the inversion loudly in the module docstring.
  A caller that reads non-zero as "the tool broke" and proceeds has inverted the whole mechanism.

- **Item 12 enforces two of the note's non-goals by vocabulary alone**: there is no verdict code
  meaning "merge", "deskcheck" or "done". That is the cheapest possible enforcement. Do not add one
  for convenience.

- **The skill (Item 13) must link the graduate skill's session-sizing heuristic, never restate it.**
  A drifted copy routes design-scale work into autopilot, which is the one thing §2.2's router
  exists to prevent. Grep your own file for the heuristic's phrases before you finish.
