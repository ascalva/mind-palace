---
type: retrospective
id: retro-<slug>
status: open              # open → sealed → superseded. All flips agent-performable — no blessing
                          # gate, BECAUSE the type confers no authority (header rule 1).
created: <YYYY-MM-DD>
updated: <YYYY-MM-DD>
window: <the bounded span observed — e.g. "the role-state wave, bp-124→bp-127, 2026-07-26/27">
origins: []               # plan/session ids the instances span. ≥2 REQUIRED: one origin is an
                          # incident, and an incident is a finding, not a retrospective.
instances: <N>            # MUST equal the §3 ledger's entry count — a mismatch is malformed.
                          # The redundancy is a deliberate cross-check, not a convenience copy.
                          # N ≥ 3 REQUIRED: below that, file a finding and link the pair.
followup: null            # declared at WRITE time: the re-measurement that completes this record
                          # (e.g. "re-take the counters after bp-12x lands"), or `N/A — <reason>`.
                          # Sealing requires it resolved (one dated block in §3) or explicitly
                          # waived here with a reason. A baseline with no after-reading is an
                          # anecdote — declare the after or waive it, never leave it implicit.
exits: []                 # artifact ids carrying this retrospective's consequences onward
                          # (finding | brainstorm capsule | plan | owner-question). Mirrors §6.
links: []
supersedes: null          # prior retro this replaces. Growth is BY SUPERSESSION, never append —
superseded_by: null       # the successor re-compresses the class; it never concatenates records.
---

# Retrospective — <the class, named>

> Lives at `docs/retrospectives/<slug>.md`. **The type in one line:** it looks backward, at a
> CLASS, across plans, and decides nothing — the only artifact whose subject is the process
> rather than the product. **Every section below is required**; an inapplicable section is
> marked `N/A — <one-line reason>`, never silently omitted — the explicit N/A is the
> accountability act. Four structural rules, each guarding against a measured failure:
>
> 1. **Terminal evidence — no channel into design.** Findings are the ONLY channel from build
>    back to design (CLAUDE.md; dn-agent-workflow §11). A retrospective proposes nothing and
>    ratifies nothing; anything here that wants authority EXITS (§6) through the existing gated
>    channels and earns it there. It may be cited as supporting evidence; it is never a warrant.
>    This is also why its status flips need no owner gate: no authority is conferred.
> 2. **Pulled, never pushed.** Never in a mandatory read path — no session brief, no default
>    context manifest, no skill points here as required reading. Anything every session must
>    know does not live here; it graduates via the gates into a skill or the constitution.
>    (The resume brief was read every session start; that made its growth a tax on everyone.)
> 3. **Hard cap: 150 lines (`wc -l`).** `[INFERENCE]` — corpus max 137 + slack. Over the cap,
>    compress or split the class. The accumulator is the disease this type documents; a
>    retrospective that grows without bound has caught it.
> 4. **Sealed means closed.** After sealing, the ONLY permitted in-place edit is a
>    `⚑ CORRECTION (<source>, <date>) — <wrong → true, and why it matters>` banner on a factual
>    error — never a silent fix, never new material. New instances of the class do not append;
>    they warrant a SUCCESSOR (supersedes/superseded_by), which re-diagnoses and re-compresses.

## 1. Occasion & window

<!-- What triggered this, concretely: the owner's ask, or the Nth instance that turned a run of
incidents into a class — name that instance. Then the window's boundaries: which plans/sessions
are inside the observation, which are outside. A retrospective with no boundary cannot seal. -->

## 2. Fence — what this is NOT about

<!-- REQUIRED, and it must contain at least one GENUINE near-miss: an event that superficially
resembles the class but is excluded, with the property that excludes it. This is the
false-success rule applied to diagnosis: the degenerate diagnosis matches everything, and the
fence is the check that reddens on it — a class that can exclude nothing is not a class.
Also fence off adjacent WORK: a defect documented here still needs its fix routed as work
(finding/plan); a retrospective is in ADDITION to the fix, never instead of it. -->

| excluded | why it is outside the class |
|---|---|
| <near-miss> | <the membership property it fails> |

## 3. Instance ledger

<!-- The evidence, in whatever structure the class demands — a flat table, named sub-patterns
(loops, variants) each with instances, a measurements table, or a mix. The template constrains
COORDINATES, not shape. Every entry carries either:
  (a) a re-checkable coordinate — `path:line@commit`, transcript/session ref, or the
      measurement (command + reading) — so a reader RE-DERIVES rather than re-reads; or
  (b) an explicit `relayed — unverified` marker naming the secondary source.
An unmarked secondary citation is the exact defect retro-the-unchecked-claim records; this type
does not get to commit it. Keep table rows ≤ ~180 chars (detail in prose).
If front-matter `followup` resolves, its after-reading lands HERE as one dated block
(`### Follow-up (<date>)`), then the retrospective seals. That is the single sanctioned append. -->

| # | instance | coordinate (re-checkable) | how it was caught / measured |
|---|---|---|---|

## 4. Diagnosis — the shared structure, as a membership test

<!-- The property ALL instances share, stated so that membership is decidable:
"an event is in this class iff <property>". It must ADMIT every §3 entry and EXCLUDE every §2
near-miss — walk both directions; a diagnosis that cannot fail this walk is boilerplate.
Generalization beyond the measured window (other surfaces the structure may reach) is welcome
but carries `[INFERENCE]` per claim, and any resulting decision still exits via §6. -->

## 5. What actually worked

<!-- The countermeasure RECORD, not the countermeasure proposal: what in fact caught, broke, or
bounded the instances, each tied to ledger #s. Rank levers if there are several (weakest first
is the house precedent). This section is empirical — if nothing worked, say so; that is itself
the finding. Proposals belong in §6. -->

## 6. Transferable rule(s) & exits

<!-- The terminal payload — a retrospective with nothing transferable is malformed by
construction (state `no rule extractable — <why>` explicitly if defensible; that claim is
itself checkable). At most ~3 rules. EACH rule must carry:
  - one sentence, naming the OBSERVABLE it keys on (a rule with no observable is an exhortation);
  - "would have caught: #<ledger ids>" — a rule that catches none of its own instances is
    vacuous, and this line is where that reddens;
  - an EXIT: the artifact that carries it toward authority (finding for build-facing defects;
    brainstorm capsule for design-facing rules; plan for a skill/code edit; owner-question for
    a ruling) — or `evidence only — no action sought`. Mirror every exit in front-matter
    `exits:`. NOTHING RESIDES HERE: an open item without a named onward home is the
    accumulator's seed, and it is malformed. -->

| rule (one sentence, observable named) | would have caught | exit |
|---|---|---|

## 7. Not claimed

<!-- The over-readings disclaimed, explicitly — the class boundary from the other side ("not
that anyone was careless", "not that X is bad in general", "not novel practice — the finding is
that WE measured OUR rate"). All three corpus retrospectives converged on this section
independently; it is what keeps a diagnosis from laundering into a verdict. -->
