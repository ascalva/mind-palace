---
type: design-note
id: dn-erratum-relation
status: ratified            # draft → ratified → superseded.  draft→ratified is an OWNER-ONLY hand edit.
created: 2026-07-27
updated: 2026-07-27
links:
  - docs/design-notes/chat-sensor.md                   # RATIFIED + amendment A1 (oq-0060) — the concrete instance's design warrant
  - docs/design-notes/temporal-code-corpus.md          # RATIFIED — the supersession/poset machinery this composes with
  - docs/design-notes/core-query-protocol.md           # RATIFIED — the F/D edge taxonomy; the crux this note answers
  - docs/design-notes/temporal-retrieval-algebra.md    # RATIFIED — π_active / σ_* / σ^*; the algebra extended by one factor
  - docs/design-notes/capability-scope-algebra.md      # RATIFIED — T = (clock, window); where the two forensic queries type
  - docs/design-notes/vector-membership-store.md       # DRAFT, under panel review — §5 names exactly which parts wait on it
  - docs/design-notes/trace-retrieval.md               # DRAFT — gap G1; the census discipline this note inherits
  - docs/design-notes/supersession-lifecycle.md        # the dispositional-edge dynamics; §3's demotion gate binds errata too
  - docs/findings/finding-0168.md                      # owner rulings: append-only, no machinery deletes, purge the one exception
  - docs/findings/finding-0164.md                      # corpus-wide keep-and-link — the idiom the erratum record follows
  - docs/findings/finding-0248.md                      # the in-artifact correction-notice precedent (a correction done right, by hand)
  - docs/brainstorms/the-unchecked-claim.md            # the retrospective this mechanism is the structural remedy for
  - docs/brainstorms/the-false-success-rule.md         # the degenerate-input discipline §7 applies to this design itself
supersedes: null
superseded_by: null
warrant: docs/design-notes/chat-sensor.md             # amendment A1 (oq-0060, owner-answered 2026-07-27) + the owner's question, same day
---

# The erratum relation — a correction is a supersession composed with a warranted retraction

> **The owner's question (2026-07-27):** *"can a supersession now express a correction? is that
> possible? or what is the appropriate mechanism?"* — with the standing directive: *"handle it such
> that system only sees a supersession as the correction, no need to wipe."*
>
> **The answer, in one sentence:** yes — but only as a **composition**. The supersession carries
> the replacement and preserves history; a new, warranted, unary **erratum** record carries the one
> assertion supersession cannot: *the superseded record was never true.* Supersession alone
> launders the error into "was once correct"; the erratum alone leaves consumers reading the false
> row. The composition is the correction.

Composed at fable (`claude-fable-5`, 2026-07-27, design pass; verified against the live stores
read-only). Design only; no build. Ratification is the owner's hand; `gate-guard` denies any agent
attempt.

## 1. Purpose and scope

Decide the **relation** that expresses "this record was wrong at write time," how it differs from
supersession, what queries must distinguish them, and its invariants. Storage layout follows the
`dn-vector-membership-store` panel verdict (§5 marks the seam precisely).

### 1.2 Non-goals (load-bearing; the owner reads these at ratification)

- **NOT purge.** Purge removes bytes under owner privacy authority and asserts nothing about
  truth; an erratum asserts falsity and removes nothing. The two never merge (finding-0168
  addendum 2; E7 below). `[ESTABLISHED — owner-ruled]`
- **NOT the membership row model.** The panel owns `dn-vector-membership-store`; this note designs
  the relation and stops at the storage seam. `[ESTABLISHED — the commissioning scope]`
- **NOT a change to the ratified-note amendment workflow.** `draft→ratified` and owner-hand
  amendments (the A1 idiom) stand as the carrier for ratified artifacts; no store-level erratum
  targets a design note (§6). `[INFERENCE — carrier assignment is mine, not ruled]`
- **NOT a build, a re-ingestion, or a back-correction of the 139 rows.** §5 designs the semantics;
  the act is a plan against this note plus amended CS-3, and it waits for the live wave to seal.
  `[INFERENCE — sequencing inferred from dn-trace-retrieval's wiring fence]`
- **NOT the OwnerVerdict taxonomy** (still parked at `dn-recursive-strata`); the erratum consumes
  the existing authority precedents, it mints no new verdict category. `[INFERENCE]`

## 2. The verdict: the distinction is real, and the machinery is necessary but not sufficient

**Formal statement.** Every record `r` has a *belief interval* — it entered the store at write
`b(r)` and, the ledger being append-only, is believed-recorded forever after — and a *validity
claim*. A **supersession** at `t` asserts validity `[b(r), t)`: true in its time, replaced.
A **correction** asserts validity `∅`: there is no moment at which `r` was right, while its belief
interval is untouched. Supersession keeps the two time axes glued together (believed ⇔ valid,
while current); a correction is precisely the event that forces them apart. This is the
valid-time / transaction-time split of bitemporal databases — Snodgrass's two dimensions,
standardized in SQL:2011 — with supersession living entirely on the transaction axis.
`[VERIFIED external, web check 2026-07-27: XTDB bitemporality docs
(https://v1-docs.xtdb.com/concepts/bitemporality/), M. Fowler "Bitemporal History"
(https://martinfowler.com/articles/bitemporal-history.html), Springer SLR on bitemporal databases
(https://link.springer.com/article/10.1007/s42488-026-00162-x)]`

**What exists today, per lane** (grounded read, all `mode=ro`):

| lane | supersession ("replaced") | correction ("never true") |
|---|---|---|
| code corpus | keep-and-link + `current` flag + derived chains (dn-temporal-code-corpus D2/D5, live) | nothing |
| interpreted claims | claim-`supersede` ops (`core/stores/claim_ops.py:78-83`) | **`VerdictEffect.RETRACT`** (`core/verdict/dispositions.py:41`) — a `wrong/noise` verdict, kept in history |
| authored K₀↔K₀ | owner-declared store, construction-guarded (`core/stores/authored_supersession.py:136`) | owner-hand only, no typed record |
| verdicts | "corrections are new verdicts at a higher seq" (`core/stores/verdicts.py:20-22`) | the higher-seq verdict IS the erratum, warrant = signature |
| design notes | `supersedes:` front matter + §6 declarations | owner-hand amendment (dn-chat-sensor A1) or in-artifact correction notice (finding-0248) |
| chat / observed rows | **none** — `PRIMARY KEY (session_id, turn_index)`, no version axis (`core/stores/chatlog.py:90`) | **none** — the 139-row defect sits here |

So the distinction is not a philosophical nicety: the repo already draws it **three times**
(RETRACT vs supersede; higher-seq verdict vs disposition; finding-0248's "recorded here rather
than silently rewritten"). What is missing is (a) the relation *named once, corpus-wide*, with its
invariants, and (b) any carrier at all for the observed stratum, where the live instance sits.
The existing machinery does **not** already handle it — the answer to the commissioning question's
"stop if it does" branch is: it does not, and the gap is exactly one relation wide.

## 3. The relation

**Definition.** An **erratum** is an append-only, warranted, **unary** disposition record:

```
erratum = (targets, authority, warrant, evidence, asserted_at_seq)
```

- `targets` — the corrected records, **enumerated at assertion time** (coordinates/digests), with
  the generating predicate recorded as *evidence*, never as the target (PD-1: a predicate
  re-evaluated against a grown store would silently widen an authority's assertion past what was
  examined).
- `authority` — who asserts falsity: owner-hand · owner-verdict(seq) · *ratified-amendment +
  deterministic interpreter* (the chat case: A1 is the owner's assertion; φ_chat's re-read is the
  mechanical enumeration of what A1 asserts it about).
- `warrant` — the artifact that carries the reasoning (`oq-`/finding/amendment ref).
- `asserted_at_seq` — its own position in the belief order (an erratum is itself a record).

**The composition law (the owner's directive, made precise).**

```
correction(r)  =  supersession(r → r′)  ∧  erratum(r)        (r′ optional)
```

- Replacement without erratum = ordinary supersession (a worldview refresh; both versions honest).
- Erratum without replacement = **retraction** (the RETRACT shape: some falsehoods have no
  corrected content — finding-0248's false premise has no "true premise row," it is simply
  withdrawn).
- On the **default read path the correction is indistinguishable from a supersession** — the
  current projection simply no longer contains `r`. That is the owner's "system only sees a
  supersession" clause, satisfied literally. The erratum becomes visible only on temporal opt-in
  paths — which is exactly where the defect lived.

**Invariants.**

| id | invariant |
|---|---|
| E1 | **Warranted or unrepresentable.** No erratum without verified authority — the `OwnerDeclaration`/verdict-signature precedents; an unwarranted retraction is itself authority laundering |
| E2 | **Append-only, keep-and-link.** An erratum is a NEW record pointing at old ones; the target row is never written (finding-0168 ruling 3; the verdicts idiom) |
| E3 | **Retroactive / transport-invariant.** Erratum status is a node property carried unchanged through σ_*/σ^*; it acts at every cut, including cuts before its assertion (§4) |
| E4 | **Dispositional, never support.** The grounding-ratio walk skips it, as it skips D (supersession-lifecycle §4.1); "erroneous" grounds nothing and is not an edge to traverse |
| E5 | **Iterable, latest-wins.** An erratum can itself be marked erroneous (a new erratum at higher seq — the dispositions.py idiom); §5's A1-count case shows this is not hypothetical |
| E6 | **Gated against blessed content.** An erratum whose target is blessed (authored or promoted) is owner-authority only — supersession-lifecycle §3's demotion gate, inherited verbatim |
| E7 | **Disjoint from purge.** Correction asserts falsity, keeps bytes; purge removes bytes, asserts nothing. Neither implies the other |
| E8 | **The pairing rule (anti-degenerate).** An erratum targeting a record in any DEFAULT view must land in the same act as its replacement projection or an explicit retraction — the default view may never keep serving a record its own store asserts was never true (§7) |

**The crux (core-query-protocol's edge taxonomy): marker on the dispositional class, or distinct
class?** — **Neither a marker on supersession edges nor a new edge class: a third _unary_ member
of the dispositional family.** It stays inside the dispositional class (time semantics live there;
the grounding walk already refuses the whole class, so E4 is inherited, not added), but it is not
an edge. What breaks under the marker-on-edge alternative, concretely:

1. **Retractions have no successor.** A marker needs an edge; an edge needs two endpoints;
   corrections-without-replacement would force minting phantom successors — a second source of
   truth the dn-code-ingest §436-447 doctrine forbids.
2. **Wrong anchor in time.** An edge marker sits at the transition (correction time `t_c`); a
   validity query at cut `T < t_c` would return the record clean unless the walk scans the future
   — breaking cut locality. The erratum must be node-anchored and retroactive (E3).
3. **Uniformity launders authority.** Under the membership model every re-projection (embedder
   bump, interpreter bump) mints supersession edges; a correction marked *on* such an edge is
   indistinguishable from a routine refresh except by its warrant — so the warrant must be the
   first-class object. That object is the erratum.
4. **The defect is not a transition.** In the membership model D-edges live on `(path, slot)`
   occupancy chains (finding-0168 addendum 1); the chat rows' falsehood is an attribute of their
   *birth*, not of any occupancy change.

The honest cost of the third-disposition choice: one new relation, one new algebra factor (§4),
and consumer discipline (E8) — plus the sprawl risk that every disagreement becomes an attempted
retraction, which E1/E6 bound: agents hold no erratum authority over anything blessed.

## 4. The algebra — one commuting idempotent, and the two forensic queries

Let `Ε` be the projection onto the span of erratum-targeted records (idempotent, diagonal — a node
property). The design claims, in `dn-temporal-retrieval-algebra`'s vocabulary:

- **`Ε` commutes with the transports:** `Ε σ_* = σ_* Ε` and `Ε σ^* = σ^* Ε` — erratum status
  rides through temporal transport unchanged. `π_active` deliberately does NOT commute with them
  (it is anchor-relative; that is its whole function). **This commutation property IS the formal
  content of "never true":** supersession is transport-relative, erratum is transport-invariant.
  `[DERIVED — from E3; a one-line check once Ε is concrete]`
- **The validity projection:** `π_valid(anchor) = π_active(anchor) ∘ (I − Ε)`. Default queries
  (`T = now`) get `π_valid` and see the correction only as a supersession (the owner's clause).
- **The two forensic queries, now distinguishable** — both typed in the ratified scope grammar
  (`dn-capability-scope` §2.1, `T = (clock, window)`):
  - *belief query* — "what did the store believe at cut T": the ledger slice at T (the `(N, ∗)`
    dilation space, windowed). Returns the erroneous row for any `T ≥ b(r)` — belief is a fact
    about T — and for `T ≥ asserted_at` the erratum is in-slice, so the answer self-annotates.
  - *validity query* — "what was true at T" (e.g. *what did the owner say at time T*): `π_valid ∘
    σ^*`-mediated. Excludes erratum targets at **every** T, including T inside the row's apparent
    lifetime. This is the query the question's forensic scenario actually means, and today's
    algebra cannot express it: `π_active` composed with `σ^*` resurrects any past-active row as
    legitimate. The extension is exactly the `(I − Ε)` factor — nothing else changes.
- **Answer to "can the algebra express that today?": no — and the gap is one factor wide.** All
  operators, clocks, and scopes exist; no transport-invariant projection exists. `[DERIVED]`

## 5. The concrete instance: the 139 chat rows — and the seam with the membership panel

**Ground truth (this session, all read-only).** `data/chatlog.sqlite`: 9,145 utterances; **139
rows** `speaker='owner' ∧ text LIKE 'Stop hook feedback:%'`, all ingested 2026-07-18…07-25 —
every one pre-dating A1. `dn-trace-retrieval` §2's "39" counted the **clause-(e) subset** (rows
matching the session-handoff clause's text); A1's prose generalized that census to "39
hook-feedback rows," which is **false at write time for the class it names** — the class held 139.
⚑ **A1 therefore needs its own micro-erratum (an A2, owner's hand; E5 in vivo).** Flagged here for
the owner; this note cannot and does not touch the ratified file. The hop-without-re-derivation is
precisely `the-unchecked-claim`'s pattern, inside the correction itself.

**The mechanism, instantiated.** The rows are a *derived* projection over immutable raw (CS-1);
the error lives in the interpreter, not the bytes: φ_chat 1.0.0 mapped `message.role: user` →
`speaker='owner'` (`ops/chat_sensor.py`, `_ROLE_TO_SPEAKER`), and the harness delivers hook output
inside user-role records. So:

1. **The supersession half** — φ_chat 2.0.0 (post-A1 channel/speaker taxonomy) re-projects the
   affected sessions from the rawstore. The 1.0.0 projection is superseded by the 2.0.0 projection
   at `(session, interpreter)` grain — a supersession event in the interpreter-version chain,
   exactly the coordinate `dn-temporal-retrieval-algebra` §2.5 (A7) already mandates. Old rows
   are kept (keep-and-link; "no wipe").
2. **The erratum half** — ONE erratum: targets = the 139 enumerated `(session_id, turn_index)`
   coordinates; authority = ratified-amendment-plus-deterministic-interpreter; warrant = A1 /
   `oq-0060`; evidence = the generating predicate and the census method.
3. **The collision dissolves.** `PRIMARY KEY (session_id, turn_index)` cannot hold two
   projections; the identity is under-dimensioned, missing the interpreter coordinate. No
   corrective row lands *at* the old coordinate — the new projection lands at the new worldview
   coordinate, and the erratum points at the old one.
4. Cheap today: **no embeddings exist over chat rows** (`dn-trace-retrieval` G1), so the
   correction is pure metadata. ⚑ If chat prose is ever vectorized (parked, owner-gated), the
   erratum must land **first** — a false attribution must never enter the semantic plane.

**The panel seam — what depends on `dn-vector-membership-store`'s pending row model, and what
does not:**

| independent of the panel | dependent on the panel |
|---|---|
| the relation, E1–E8, the composition law | the erratum's physical home (per-store table vs one corpus-wide table beside `memberships`) |
| the `Ε` factor and π_valid; the belief/validity split | how projection-supersession is stored for chat: widened PK `(session, turn, interpreter)` vs membership fibers keyed `(session, transcript_digest, interpreter)` — the `(path, blob_sha)` analog |
| the chat semantics: re-project + one erratum, keep both | whether "in the default view" is a row flag (`current_any`-style) or a membership property |
| the per-surface carrier table (§6) | whether the chat lane adopts the membership model at all, or only widens its key (PD-2 there) |

## 6. Corpus-wide: one relation, per-surface carriers

The same shape recurs everywhere `the-unchecked-claim` measured — this mechanism is that
retrospective's structural remedy, and they agree: the retrospective's rule marks the *hop* at
write time; the erratum is the typed channel by which a failed re-derivation lands *after* write.

| surface | supersession carrier | erratum carrier |
|---|---|---|
| store records (chat, code, observed) | interpreter/version chains, `current` flips | **the new erratum record (this note)** |
| findings, brainstorms, drafts (agent-writable) | supersedes links | in-artifact correction notice, erratum-shaped: warrant + what-was-wrong + kept text (finding-0248's idiom, now named) |
| ratified notes | owner-hand `supersedes:`/§6 declarations | owner-hand amendment (A1 idiom) — the gate IS the authority; no store record |
| verdicts | higher-seq verdict | higher-seq verdict (already erratum-complete: signed = warranted) |
| interpreted claims | claim-`supersede` | RETRACT disposition — subsumed as the erratum's verdict-lane instance once built |

`[INFERENCE]` on the carrier assignments for findings and ratified notes — existing practice,
not yet ruled as policy.

## 7. The degenerate case, and the named falsifiers

**The degenerate input (the false-success rule, applied to this design):** an erratum lands and
every consumer keeps reading the old rows — because `ChatlogStore.all_rows`/`rows_for`
(`core/stores/chatlog.py:171-190`) filter on nothing but provenance, so v1 rows remain the only
rows at their coordinates and the flag is consulted by no one. The correction "works" — a record
exists saying the rows are false — **while doing nothing.** E8 is the structural counter; the
acceptance check must *redden* on this input: after the correction act, (a) the default view's
census of `speaker='owner' ∧ 'Stop hook feedback:%'` = **0**; (b) the validity query at any
pre-correction cut also = 0; (c) the belief query at such a cut = **139, every one flagged**.
A green (a) with a red (b) or (c) is the false success, named.

**The named falsifier of the central claim (the resurrection test).** The central claim is that
"erroneous" is a transport-invariant unary disposition. It is falsified if either: (i) after a
correction, any `σ^*`-mediated **validity** query at a pre-correction cut returns a corrected row
as valid (transport-invariance fails in implementation); or (ii) a legitimate correction is
exhibited whose target has a **non-empty** validity interval — "true until t, and t < its
supersession" — i.e. a case that genuinely needs cut-relative erroneousness. Case (ii) would mean
the marker-on-edge model was right and this note's arity argument wrong; no such case exists in
the six measured instances (`the-unchecked-claim`) — all were false at birth — but the refutation
shape is recorded so it can be recognized.

## 8. Wiring sketch (design-only; nothing starts before the panel verdict and the wave seal)

A graduating plan (post-ratification, post-panel, post-wave) carries: the erratum store (home per
panel), φ_chat 2.0.0 + identity widening (per panel), the `(I − Ε)` factor on the temporal read
path, the E8 pairing check, and §7's three-census acceptance. The enable act is one owner-run
re-projection over the rawstore (`dn-chat-sensor` §5 D2's backfill posture). No flag: like
keep-and-link, correction-capability is the store's semantics, not a feature.

## 9. Parked decisions

| id | decision | default recorded | re-entry condition |
|---|---|---|---|
| PD-1 | erratum target grammar | enumerate coordinates at assertion; predicate recorded as evidence only | a target class too large to enumerate appears |
| PD-2 | erratum store home | undecided — panel-dependent (§5) | the membership-store panel verdict lands |
| PD-3 | belief-vs-validity as two views or a mode switch | two typed sentences in the existing grammar, no new View | the graduating plan types the read surface |
| PD-4 | store-level errata for ratified artifacts | never — the owner-hand amendment gate is the carrier | the owner rules otherwise |
| PD-5 | A2 on dn-chat-sensor (the 39→139 count) | flagged to the owner (§5); agent-immutable surface | the owner's hand |

## Cross-references

Ratified: `dn-core-query-protocol` (§2.2 edge classes, §2.5 transports) · `dn-temporal-retrieval-
algebra` (§2.2 π_active/σ_*/σ^*, §2.5 interpreter coordinate) · `dn-capability-scope` (§2.1 T,
§2.3 Inv/Rate) · `dn-temporal-code-corpus` (D2 keep-and-link) · `dn-chat-sensor` (CS-1…CS-4, A1).
Draft: `dn-vector-membership-store` (the panel seam) · `dn-trace-retrieval` (G1, the census).
Code (read this session, ro): `core/stores/chatlog.py:76-92,150-190` · `ops/chat_sensor.py`
(`_ROLE_TO_SPEAKER`) · `core/verdict/dispositions.py:32-44,101-109` · `core/stores/verdicts.py:
17-27` · `core/stores/claim_ops.py:78-83` · `core/stores/authored_supersession.py:40-97` ·
`core/kernel/stores/sourceset.py`. Store census (ro, 2026-07-27): 139 rows
`speaker='owner' ∧ 'Stop hook feedback:%'`, observed_at 2026-07-18…07-25, interpreter 1.0.0
uniform.
