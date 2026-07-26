# effect-catalog-missing-axes

## 2026-07-26T00:00:00Z

```capsule
topic: effect-catalog-missing-axes
date: 2026-07-26

context: |
  Track G built the hands (G1-G7, complete 2026-07-04): a typed effect catalog, a 72-state
  gate, reversible writes as propose-never-send with a `MirrorView`, irreversible effects
  behind a JIT-credential executor, and a blast-radius drift axis. All flag-off; max
  reachable effector tier is NONE and nothing is wired at any tier (finding-0011).

  Three independent arrivals on 2026-07-26 each showed the SAME thing: the catalog's
  reversible/irreversible axis is too coarse to carry the weight now placed on it. Three
  arrivals in one day is design-note-shaped, not three findings.

  ⚑ What makes this urgent rather than tidy: on the same day the owner RULED the frame
  question (oq-0051) — "the mirror MAY act, bounded by RETRACTABILITY". Retractability is
  now the LOAD-BEARING AXIS of the whole authority structure. Every gap below is a gap in
  the thing the ruling rests on.

decisions:
  - The three axes are one design note, not three findings. They are the same defect seen
    from three angles: the catalog reads reversibility off the RESOURCE, and authority
    needs it read off the WORLD.

axes:
  - id: A1
    name: Irreversible but BOUNDED blast radius
    first_seen: docs/brainstorms/ouroboros-email-identity.md
    sharpened_by: the $100 wallet
    claim: |
      "Irreversible" collapses two very different things: an act that cannot be undone and
      is unbounded, and an act that cannot be undone but whose worst case is capped. Spending
      $100 from a wallet holding exactly $100 is irreversible and its damage is bounded BY THE
      WORLD — not by trusting the agent's restraint, and not by a number in a config file.
    why_it_matters: |
      Without this axis every irreversible act is gated identically, so the gate is either too
      tight to be useful or too loose to be safe. With it, a bounded-irreversible act is a
      candidate for a standing grant rather than a per-act permission.

  - id: A2
    name: Bounded BY CONSTRUCTION and verifiable FROM OUTSIDE
    origin: the custody refinement
    claim: |
      A bound only counts if a third party could check it without trusting the system. The
      wallet's balance is such a bound. An exchange API key with withdrawal or margin scope is
      NOT bounded by its balance — margin can lose more than the deposit, withdrawal reaches
      assets the balance does not describe.
    why_it_matters: |
      This is the falsifier for A1. Without it, "bounded" becomes self-asserted, and A1 turns
      into a loophole that launders unbounded acts as bounded ones. The pair only works together.

  - id: A3
    name: Technically reversible, SOCIALLY irreversible
    claim: |
      A sent message can be deleted and cannot be UNSENT. A cancelled order was still placed.
      **Reversibility of the RESOURCE is not reversibility of the RELATIONSHIP.**
    why_it_matters: |
      ⚑ This is oq-0051's named gap 2 and its most likely failure mode in practice. The ruling
      makes the retractable tier AUTONOMOUS. If "retractable" is read off the resource — which is
      what a catalog naturally encodes, because the resource is the thing with an API — then the
      autonomous tier silently swallows every socially-irreversible act, and it does so without
      anyone deciding that it should.

connections:
  - oq-0051 (RULED 2026-07-26) — retractability is the governing axis of world-facing authority.
    A1/A2 refine what "unretractable but acceptable" can mean; A3 is the ruling's own gap 2.
  - oq-0052 (open) — impersonation is ORTHOGONAL to all three: a message under the owner's name
    is retractable as a resource and unretractable as a relationship, so A3 explains WHY
    retractability cannot decide impersonation, but does not decide it either.
  - finding-0218 — `ActuatorSpec` has no actor-identity field. Whatever these axes become, they
    must land IN THE TYPE; an axis that exists only in prose is decoration.
  - docs/design-notes/effector-risk-computation.md and hands-and-the-effector-layer.md — the
    built surfaces these axes would extend.

parked:
  - decision: Mint a design note for the effect catalog's authority axes.
    default: Not minted — captured here only.
    re_entry: The owed revision pass on `dn-world-facing-agency` (`draft`), which must seat
      oq-0051's ruling as its governing structure. These axes are what "retractable" has to mean
      in that note for the ruling to be implementable, so they belong to that pass rather than to
      a separate note competing with it.

open_questions:
  - Is A1+A2 one axis (bounded-and-externally-verifiable) or two? They only function together,
    which is an argument for one; but A2 is a PROPERTY OF THE BOUND rather than of the effect,
    which is an argument for two. Getting this wrong makes the catalog either lossy or noisy.
  - Does A3 belong in the catalog at all, or is it a property of the COUNTERPARTY rather than of
    the effect? An identical API call is socially reversible with a vendor and not with a friend.
    If it is counterparty-dependent, the catalog cannot carry it alone and the gate needs a
    counterparty model — which is a much larger claim.
  - Track G's built taxonomy is reversible/irreversible. Do these axes REPLACE it, or refine it
    beneath it? Replacement is a superseding note; refinement is an amendment. The answer decides
    whether the built code changes or only grows.
```
