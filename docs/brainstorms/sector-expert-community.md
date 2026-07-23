# The sector-expert community — learn, audit, defend

Brainstorms on the standing community of domain-expert agents: touch-triggered review, experts as
attested oracles, per-sector context systems, and the community itself as ingested/tracked/
attested/understood substrate. Extends the adversarial-gate + expert-panel rulings
(`reconciliation-audit.md`) from gate-time to STANDING structure. Companion threads:
`agent-type-taxonomy.md`, dn-agent-taxonomy (the corpus-side agent roles this mirrors).

## 2026-07-23 — the owner's vision capsule (+ orchestrator chewing)

```capsule
topic: sector-expert-community
date: 2026-07-23 (session-43/44 boundary; owner directive, near-verbatim)

THE VISION (owner):
  - Any time an orchestrator or builder updates any project sector, the touched areas TRIGGER a
    review from that sector's subject-matter expert — not only at bless/ratify gates; on TOUCH.
  - Those experts' context, steering files, and skills are OPTIMIZED for rigorous feedback on
    design notes, build plans, and code — AND they are the sector's ORACLE: questions needing
    definitive, load-bearing answers route to them.
  - As each component grows more complex, an agent needs more to remember and understand →
    sub-agents get their OWN context + context-management system, spawned from a GENERIC agent
    template, SPECIALIZED for learning a sector: skilled to quickly absorb the code, docs, state,
    and philosophy of their subdomain.
  - Each in charge of their own sector — "a community of support whose interactions are all
    planned, tracked, and attested."
  - And the point: THIS IS ALL INGESTED — so it can be tracked — so it can be attested — so it
    can be understood.
  - **Procedure: LEARN, AUDIT, DEFEND.**

WHERE THIS GOES (the reading the owner asked for — "do you see where we're going?"):
  The maintainer community becomes PART OF THE ORGANISM. The workshop and the palace merge: the
  system's own institutions — its experts, their reviews, their answers, their disputes — are
  corpus strata like everything else (transcripts already ingest via the chat sensor; reviews are
  artifacts; attestations already have a store; the composed causal graph covers the community's
  own work the same way it covers code). Ouroboros stops being a system WITH a development
  process and becomes a system WHOSE development process is inside it. The owner scales his
  ATTENTION, not his authority: sectors are held by experts; the CONSTITUTION and the gates stay
  human. This is also the structural answer to the jenga anxiety — no single head (his or one
  agent's) must hold every sector; detection lag is bounded per-sector by a standing specialist.

THE LIFECYCLE — learn / audit / defend, as the expert's loop:
  - **LEARN:** bootstrap = a sector sweep (code + docs + state + design philosophy → a sector
    model: invariants, interfaces, open findings, parked decisions, the "misses" checklist);
    maintain = re-learn ON CHANGE (the sector's own drift gauge decides staleness — same pattern
    as A1, per-sector).
  - **AUDIT:** touch-triggered adversarial review (the write_scope→sector map already sketched
    for auditor routing is the trigger table); gate-time panel review (already ruled) is the
    special case; on-touch review is the general case.
  - **DEFEND:** two senses, both intended. (a) Defend the sector's invariants against changes
    that erode them — the guardian posture. (b) Defend its ANSWERS: an oracle answer to a
    load-bearing question is an ARTIFACT carrying its evidence (grounding refs, greps, measured
    premises) — witness-keyed like everything else, challengeable; a successful challenge is a
    finding against the expert's model, which updates it (the community has an error-correction
    loop on itself).

ORCHESTRATOR CHEWING (extensions + the honest tensions):
  - **Lenses, not mini-palaces (DRY at the architecture level):** each expert's "own context
    system" should be a SCOPED VIEW over the ONE corpus (sector-filtered retrieval recipe +
    a curated standing brief), NOT n separate stores. The corpus is already the memory; the
    expert IS its brief + its lens + its checklist. Cheap first step exists today:
    `.claude/agents/auditor-<domain>.md` (contract) + `docs/sectors/<sector>/brief.md` (the
    grown sector model, an ARTIFACT — versioned, reviewable, itself gated).
  - **Spawn-from-artifact, not standing daemons:** sessions are disposable, artifacts are not —
    an expert is INSTANTIATED from its brief on demand (review, question, re-learn), not kept
    resident. The brief is the expert; the process is ephemeral. (Context economy: a resident
    community is unaffordable; a brief-instantiated one costs only when used.)
  - **The oracle discipline:** load-bearing answers must be graded like composed edges — an
    answer carries {evidence refs, confidence, what would falsify it}; "definitive" is earned by
    grounding, never by role. An ungrounded expert answer is a defect, not an oracle.
  - **Brief ratification:** an expert's brief/sector-model is itself a design-adjacent artifact —
    minting a NEW institution (a new expert, a new sector boundary) should pass the same
    draft→review→ratify chain. Organizational self-modification obeys §14's shape: propose →
    approve → validate → reversible.
  - **Constitution unchanged:** every expert inherits CONSTITUTION.md as outermost frame
    (non-negotiable #6); experts hold NO write power beyond reviews/findings/answers — the model
    advises, code acts, blessings stay owner-only. The community scales support, never authority.
  - **Tensions to design through (the open list):**
    * brief staleness vs re-learn cost — per-sector drift gauges; re-learn triggered by the
      sector's own change velocity, not a clock.
    * circularity — an expert's review changes the sector that defines the expert; the
      reconciliation sweep (the standing audit cadence) is the outer loop that audits the
      experts' own models. Who audits the auditors: the sweep + the challenge protocol.
    * sector boundaries — overlapping globs need one owner-ratified sector map (the routing
      table is itself a gated artifact); disputes route up, never resolved by the disputants.
    * the human bottleneck MOVES — from reading artifacts to reading reviews; needs review
      compression (severity-ranked merged reports, the named-coverage accounting) so the owner
      reads verdicts + dissents, not transcripts.
    * cost shape — touch-triggered review on EVERY touch could be heavy; tier it: cheap
      conformance pass on small touches, full expert review on invariant-adjacent surfaces
      (security/math low-threshold, as already ruled).

next:
  - Feeds TWO design passes, in order: the workflow-taxonomy pass (the chain gains the
    review stage + the sector map) and then a dedicated dn-sector-experts note (the community:
    briefs, lenses, oracle discipline, learn/audit/defend lifecycle, ingestion of the
    community's own exhaust). Both post-reset (Jul 24+), through the expert-panel gate —
    fittingly, the panel reviews the design of its own generalization.
```
