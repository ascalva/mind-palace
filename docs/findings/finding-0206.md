---
type: finding
id: finding-0206
status: open
created: 2026-07-25
updated: 2026-07-25
links:
  - docs/design-notes/dn-autopilot-and-delegated-blessing.md   # §2.3 post-hoc rule, §2.9 invariant 9
  - .claude/hooks/_lib.py                                      # the (c) clause this rule assumes
  - docs/design-notes/agent-workflow.md                        # A1 (committed-self-clears), A3
  - .claude/skills/commit/SKILL.md                             # the lazygit ceremony that collides
ftype: spec-defect
origin_plan: orchestrator
route: orchestrator
resolution: null
---

# The autopilot note's post-hoc grant check has no existing rule to be an "exception" to — and as written it cannot distinguish the owner's committed hand-flip from a forged one

## What

Found during the `/graduate` grounded pass on `dn-autopilot-and-delegated-blessing` (ratified
`b27142d`), before any plan was minted. Two defects in §2.3's post-hoc enforcement rule, one
framing and one substantive.

**(1) Framing — it is a tightening, not an exception.** §2.3 says the Stop-gate clause (c)
*"contract gains one narrow exception: a committed `proposed→ready` flip is legitimate **iff** the
same commit carries a grant record…"*. That presupposes (c) currently blocks committed flips, so
that a grant record would carve out a permitted case. **It does not.** Clause (c) examines only
the working tree against HEAD, and the code says so in its own comments:

- `.claude/hooks/_lib.py:826-833` — *"a **committed** blessing is accountable to its commit author
  (§10, 'deliberate, logged') and must self-clear; only an **uncommitted** in-flight flip is
  flagged."*
- `.claude/hooks/_lib.py:852-858` (the `_untracked_blessing` A3 path) — *"It scans only
  **untracked** files, so a committed blessing (tracked, in HEAD) never trips it — the A1
  committed-self-clears behavior is preserved unchanged."*

So today a committed `proposed→ready` flip passes unconditionally, grant record or not. The
autopilot verifier's flip would therefore already pass. What §2.3 actually specifies is a **new
post-hoc verification of committed flips** — strictly stronger than today's rule, and a partial
reversal of A1's deliberate committed-self-clears posture. Calling it "one narrow exception"
understates both the build cost and the constitutional reach.

**(2) ⚑ Substantive — the rule is not implementable as stated.** §2.3 closes: *"All other
agent-side flips remain violations."* A post-hoc check operates on **commits**, and a commit
carries no trustworthy agent-vs-owner signal:

- The git author is the owner (`Alberto Serrano-Calva`) for **both** cases, because this repo's
  standing blessing ceremony has the **agent commit the owner's hand-made flip** — verified live
  this session: the owner flipped `dn-autopilot-and-delegated-blessing` to `ratified` by hand and
  the agent committed it as `b27142d`.
- Therefore "committed flip with no grant record" is simultaneously the signature of the **owner's
  legitimate blessing** (every plan blessed to date) and of the **forged agent flip** the rule
  exists to catch. The predicate cannot separate them.

Enforce §2.3 literally and every owner blessing that is not autopilot-granted reads as
unauthorized. Relax it to "no grant record ⇒ assume owner," and the forgery hole §2.3 was written
to close reopens — an agent Bash-commits a flip with no grant record and is indistinguishable from
the owner's hand.

## Why it matters

The note's §2.9 invariant 9 — *"A grant record without a re-verifiable attestation tag is not a
grant record — the flip it accompanies reads as unauthorized. Narrative alone never proves a
grant"* — is the audit's strongest catch and the property the design most depends on. It is sound
for the autopilot path. It is silent on the **owner-hand path**, which shares the same wire format
(a committed flip) and has no attestation by construction, because the owner's hand is not a
verifier and holds no HMAC.

This is not an autopilot-only concern. Any post-hoc committed-flip check must answer "what
legitimises a flip that carries no grant record?" before it can be built at all, and that answer
is a constitutional choice, not an implementation detail.

Unresolved, the mechanism plan is unbuildable: its acceptance criterion ("an unauthorized committed
flip is caught") has no test that does not also fire on the owner's own blessings.

## Candidate resolutions (a ruling, not the agent's to make)

- **(a) Two legitimisers, explicitly.** A committed `proposed→ready` flip is legitimate iff it
  carries a re-verifying grant record **or** it is signed by the owner — which requires the
  blessing ceremony to gain a real owner signature (git commit signing, or an owner-side
  attestation over the flip). Closes the hole properly; costs a change to the by-hand ceremony,
  which is the thing the owner most values for being frictionless.
- **(b) Scope the check to autopilot-eligible plans only.** A plan that has ever carried a capsule
  is held to the grant rule; a plan that never did keeps A1's committed-self-clears. Cheap and
  non-invasive, but leaves the forgery hole open for any plan the agent simply declines to give a
  capsule — which is every plan it wants to forge.
- **(c) Keep the check uncommitted-only and drop §2.3's post-hoc clause.** Rely on the verifier
  being the only actor able to produce a valid grant record, and on the grant record's tag being
  checked at *use* rather than at Stop. Smallest build; abandons offline post-hoc detection, which
  §2.3 explicitly wanted.

Recommendation withheld pending the owner's read — this sits on a bright line (`CLAUDE.md:62`,
NN-5), and the note is now agent-immutable, so a change here needs a superseding note rather than
an edit.

## Re-entry condition

Graduation of `dn-autopilot-and-delegated-blessing` proceeds for every unit that does **not**
depend on the post-hoc rule (the verifier crypto, the capsule, the predicate check, the config
schema, the halt list, the audit gates — all unaffected). The **journal-gate / post-hoc
verification plan is parked** and is not minted until the owner rules among (a)/(b)/(c) or
supplies a fourth. No plan may assert the post-hoc rule as buildable before that ruling.

## Routing

`spec-defect` in a **ratified** design note, and the correction is design-level ⇒ `design` →
orchestrator → batched to `docs/inbox/owner-questions.md`. Per §4 Reconciliation discipline the
correction is announced, never quiet: the note is agent-immutable (A8), so this finding is the
banner, and any plan touching §2.3 carries a banner-on-correction citing it. The owner's options
are above; the decision is his.
