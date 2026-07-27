# bp-137 — journal

## Pre-build notes for whoever picks this up

- ⚑ **The warrant is real and measured.** `finding-0263`: `touches_stored_data: false` appears in
  **zero** of the 111 plans carrying the flag; the prose form has ≥20 spellings. A P3 built to
  §2.4's literal text returns PASS on **every plan in the repository**. Read the finding before the
  plan.

- ⚑ **Most existing plans will fail P3 as tightened, and that is correct.** P1–P5 gates autopilot
  eligibility, not repo hygiene. The tempting "fix" is a 111-file normalization sweep. It is a
  non-goal (§9) and it would be a template/schema change that belongs to the owner.

- ⚑ **Every predicate has a vacuous-pass twin.** Empty `write_scope` ⇒ P1 and P2 both true over the
  empty set. Zero `### Item ` headings ⇒ P3 true over the empty set. Empty §7 ⇒ P4 true. That is why
  the result type is three-valued and why `UNDETERMINED` is absorbing under conjunction. The
  243-combination enumeration in Item 17 is the assertion that a naive `all(t is not FAIL)` cannot
  survive — write it early, not last.

- **Reuse `_lib.matches_any`, do not write glob code.** Two matchers that disagree mean the
  predicate blesses a scope `scope-guard` reads differently — a security-relevant duplication, not
  a style one.

- **The finding-0085 footgun is a P2 degenerate input, not a footnote.** An entry with a glued
  inline comment (`- eval/metrics.py  # absorbed`) matches nothing, so the forbidden-set
  intersection is empty and P2 passes on a scope that names `eval/`.

- **This predicate's output is rendered to the owner's phone.** A vacuous PASS is a false statement
  shown to him at the moment he decides whether to grant. Weight the degenerate-input criteria
  accordingly.
