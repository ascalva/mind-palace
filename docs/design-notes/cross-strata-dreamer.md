---
type: design-note
id: dn-cross-strata-dreamer
status: draft            # draft → ratified → superseded.  draft→ratified is an OWNER-ONLY hand edit.
implementation: design-only
created: 2026-07-16
updated: 2026-07-16
links:
  - docs/brainstorms/cross-strata-and-multiscale-dreamers.md   # THE WARRANT — the founding capsule (Idea B + the reconciliation principle + the parked fork)
  - docs/design-notes/sigma-fibers-and-multiscale-dreaming.md  # companion: Idea A (firewall-compatible, near-term)
  - docs/design-notes/capability-scope-algebra.md              # §2.2 ideals/SLICE/partial T-meet — the machinery that types this note's verdicts
  - docs/design-notes/observed-data-and-the-assistant-tier.md  # the two-pool core decision this note preserves
  - docs/design-notes/recursive-strata.md                      # I1 + promote-by-verdict — the only authored crossing
supersedes: null
superseded_by: null
warrant: docs/brainstorms/cross-strata-and-multiscale-dreamers.md
---

# The cross-strata dreamer: a correlator-family, interpreted-tier subsystem — and the firewall fork, resolved

> Composed at **fable** (`claude-fable-5`, 2026-07-16, the sanctioned design pass). Filed as
> `draft`. **This note sits NEAR an inviolable** (the mirror firewall / the fixed points): the
> founding capsule parked the firewall-scope fork with re-entry "the fable design-note pass
> decides it deliberately and logs it — human-only, deliberate, recorded, not slipped into a
> build." This note is that deliberate record; **the owner's ratification of this note IS the
> human decision.** Until ratified, the default stands unmodified: the firewall as written,
> nothing cross-strata reads anything. **Design only; no build is authorized by this note —
> and unlike its companion, ratification alone licenses no build either (§3).**

## 1. Purpose and scope

Idea B of the parent brainstorm: a dreamer that sees the **whole strata** and proposes
connections **between** layers. This note (1) resolves the parked firewall-scope fork, (2) types
the composed "union scope" against the ratified algebra and reports what the type system
*already* rules — including two structural gates the brainstorm did not anticipate, (3) places
the subsystem in the existing architecture (correlator-family, Track D), and (4) records the
gate chain that must clear before any build plan may even be graduated. Out of scope: Idea A
(the companion note); the conversation-sensor thread (its own brainstorm); any relaxation of
`MIRROR_READABLE` (none is proposed — see §2.1).

## 2. Principles / decision

### 2.1 The fork, resolved: the firewall stands as written — and the dreamer is not a mirror agent

The parked fork: does the mirror firewall forbid observed/non-authored data from seeding ANY
dream, or only the MIRROR dreamer's dreams? **Ruling (drafted for ratification): the latter —
and `MIRROR_READABLE` is not touched in either case.**

The firewall's two structural facts, verbatim from the code, decide it:

1. **What I6 protects is the introspective read path and what may be reflected back as
   authored insight.** `MIRROR_READABLE = {authored-solo, authored-dialogue}`
   (`core/provenance.py:78-80`) is enforced by `MirrorView` — "the only thing the introspective
   agents cluster over" (`core/mirror.py:15-24`); a non-MR row in it is unrepresentable.
   Nothing in I6 forbids a **non-introspective** component from reading other strata through
   their own typed Views — the architecture already ships exactly that seam: `ObservedView` is
   "the assistant-tier read boundary, dual to MirrorView," and its declared intended consumer is
   the **Track-D correlator** (`core/sensing.py:190-197`).
2. **The output side is already unforgeable.** Everything such a subsystem emits lands
   `interpreted`: the `DerivedStore` has no provenance parameter, so "no pipeline can launder
   curated/observed/interpreted into authored" (`core/provenance.py:74-77`); and the two views
   PARTITION the tiers in both directions (`sensing.py:195-196`), so a cross-strata product can
   never re-enter a `MirrorView`.

Therefore the cross-strata dreamer is **not the mirror's reflective dreamer with a wider
scope** — it is a *distinct subsystem of the correlator family*: reads composed non-mirror-plus-
mirror strata through per-stratum typed Views, emits `interpreted`-provenance **candidates**,
and the only crossing into authored remains **owner ratification** — at the type level,
`promote(Derived[T], OwnerVerdict) -> Authored[T]` (`core/provenance.py:145-160`), which is
today a deliberate stub because the verdict taxonomy is unratified (gate G1, §2.4). The
brainstorm's reconciliation principle is thus confirmed and sharpened: the strata get unified
the safe way — the system finds candidate connections; the owner decides which are actually
part of their thought (I5/I6 intact; a dream can never launder machine or third-party exhaust
into what looks like the owner's insight).

**What ratifying this note changes, precisely:** it grants the *client class* "cross-strata
correlator" a declared **read-exemption** from the mirror-payload ideal (§2.2) — read-only,
with the §2.3 bounding conditions. It changes no enum, no view, no store, no baseline path.

### 2.2 The union scope, typed — the algebra answers the feasibility question

The founding capsule's open question: is a composed scope over authored ⊕ observed ⊕ reference
expressible under the firewall ideals, or does it collapse to ⊥? Worked against
`dn-capability-scope` §2.2 and `core/scope.py`:

**The scope.** `s_x = (Σ_x, E_x, T_x, A_x)` with `Σ_x = {mirror_authored, observed,
interpreted, reference_repo}` (named per-stratum — deliberately NOT `⊤_Σ`), `E_x = {F}`,
`A_x = (READ_PROPOSE, 1, NONE)` — W_Σ = 1 is the projection-write bit for its interpreted-only
output, paired to the interpreted stratum by construction (the DerivedStore mint; the CS-c park
keeps the pairing constructional, not type-fused); world reach NONE.

**Admissibility (the ideal question).** A grant is admissible for client class c iff
`s ⊓ ι = ⊥` for every ideal *applicable to c* (`capability-scope-algebra.md` §2.2;
`core/scope.py:529-551`). Two ideals exist: 𝔇 (always applicable — `Σ_x` excludes FOUNDATION,
satisfied ✓) and the mirror-payload ideal ι_MR, applicable to **non-exempt** clients. So the
answer to "does authored ⊕ observed collapse to ⊥?" is: **not intrinsically — admissibility is
per-client-class.** Precedent already in-tree: the shadow runner holds a `MirrorView` for eval
and is not an introspective agent (`core/dreaming/shadow.py:141`). But absent an owner-declared
exemption for this class, `s_x ⊓ ι_MR ≠ ⊥` and the grant is **inadmissible — the firewall
stands by default**, which is exactly the parked default this note leaves in force until
ratification. The join itself obeys the ratified law "a widening, grantable only by an
authority already holding the join" — the owner.

**The two structural gates the type system already imposes (found by typing, not anticipated by
the brainstorm — the strongest result of this pass):**

1. **The SLICE rule.** `|Σ_x| > 1` with a point window and no cut-supplying clock raises
   `SliceError` at construction (`core/scope.py:441-450, :471-480`): a cross-strata dream over
   bare "now" is **ill-typed**. The scope must carry an explicit consistent cut; the commit SHA
   is the cut for repo-backed strata only (`_CUT_CLOCKS`, `core/scope.py:450`) — mirror runs on
   `projection_event`, ops on `last_write` (`core/scope.py:171-184`), which commit does not
   cover.
2. **The partial T-meet.** The strata's clocks are pairwise incomparable except through the
   global event clock N, which is **parked** (CS-a) — so a unified T for `s_x` raises
   `NoCommonClockError` (`core/scope.py:311-314, :334-348`), a constructor error, never a
   silent guess.

**Consequently the lawful v1 shape is forced, not chosen:** the cross-strata dreamer reads
**stratum-by-stratum** — a product of single-stratum scopes, each on its own clock with its own
anchor — and every candidate connection it emits carries the **pair of per-stratum anchors** it
was observed at (its own consistent-cut discipline, in the output rather than the scope). A
genuinely unified cross-strata snapshot waits on CS-a (materialize N) or an explicit
cut-construction design. Note what this means: **the type system re-derives the Track-D
correlator's pairwise shape from first principles** — evidence the algebra carves reality at a
joint, and the formal ground for §2.3's placement ruling.

### 2.3 Placement and bounding conditions

- **The cross-strata dreamer IS Track D's growth path, not a subsystem beside it.** Same read
  seam (`ObservedView` and siblings), same output tier, same pairwise shape forced by §2.2. The
  founding capsule's surfacing question is answered the same way: candidates surface through the
  built review channel (E6 REPL / verdict store) — no third channel.
- **Bounding conditions attached to the §2.1 exemption** (all inherited, none new): read-only
  with respect to every non-interpreted stratum; outputs `interpreted` only (structural);
  nothing it emits enters behavioral baselines or any `MIRROR_READABLE` path (structural,
  partition); promotion exclusively via owner verdict (I1, `recursive-strata.md` §4 — and §9:
  never confidence-weighted, ever); candidate volume under the I5-style budgets when the Track D
  charter pins them; the model-advises-code-acts line unchanged.
- **Idea A's instruments compose forward:** if the companion's σ-persistence gate validates, the
  same tiering discipline applies to cross-strata candidates (strength-gated surfacing of
  correlations), with its own F9-style validation on cross-strata fixtures — a re-derivation,
  not an inheritance; recorded as a forward reference only.

### 2.4 The gate chain (must clear IN ORDER before any build plan is graduated)

| gate | what | status today |
|---|---|---|
| G0 | THIS note ratified (the fork decision — owner hand) | draft |
| G1 | verdict taxonomy ratified → `promote`/`OwnerVerdict` un-stubbed (`core/provenance.py:129-160`; recursive-strata §8 action 2) | unratified, stub |
| G2 | Track D correlator charter (the subsystem this generalizes) — its ObservedView consumer, schema, budgets | not chartered |
| G3 | the cut discipline: either CS-a (materialize N) or a ratified per-stratum-anchor output design (§2.2) | CS-a parked; anchor design drafted here, not ratified |
| G4 | the mirror-substrate precondition: the *mirror* dreamer demonstrates value first (the same ordering that parks recursion behind adoption — `recursive-strata.md` §1) | dual-dreamer A/B just beginning (13 notes / 4 edges) |

## 3. Consequences

**On ratification: the fork is decided and recorded; the exemption class exists on paper;
NO build is licensed.** The first build plan can be graduated only after G1–G4 clear, and it
belongs to the Track D charter, not to this note. What this note does license immediately:
the orchestrator may cite the fork as resolved (no more re-litigating whether cross-strata
reads are thinkable), and the Track D charter, when written, inherits §2.2's typed shape and
§2.3's bounding conditions as its starting constraints.

## Parked decisions

| id | decision | default recorded | re-entry condition |
|---|---|---|---|
| XS-a | the exemption's Σ extent (does it include `curated`? `ops`?) | the §2.2 four-stratum list; curated/ops excluded | the Track D charter argues a concrete consumer per added stratum |
| XS-b | unified-snapshot semantics | per-stratum anchors in the output (§2.2 forced shape) | CS-a materializes N, or a cut-construction note ratifies |
| XS-c | whether cross-strata candidates carry a persistence-style strength | unscored v1 (candidates ranked by the correlator's own evidence) | companion FB-3 validates; a cross-strata fixture battery exists |
| XS-d | authored-dialogue capture into the mirror (the substrate-growth lever the capsule flagged) | untouched here — belongs to the conversation-sensor brainstorm | that brainstorm's own graduation |

## Cross-references

- **Warrant:** `docs/brainstorms/cross-strata-and-multiscale-dreamers.md` — the founding capsule
  (the reconciliation principle, the parked fork whose re-entry this note is, the open questions
  §2.2 answers).
- **Code (verified on disk 2026-07-16):** `core/provenance.py` (:74-80, :129-160),
  `core/mirror.py` (:15-24, :76-82), `core/sensing.py` (:190-197, :171-182),
  `core/scope.py` (:171-184, :311-314, :334-348, :441-480, :529-551),
  `core/dreaming/shadow.py` (:141).
- **Design:** `dn-capability-scope` §2.2 (ideals, SLICE, partial T-meet; CS-a/CS-c parks);
  `dn-observed-data-and-the-assistant-tier` (the two-pool decision, preserved);
  `dn-recursive-strata` §1 (the ordering principle behind G4), §4 I1, §8;
  `dn-sigma-fibers` (Idea A companion; XS-c's instrument).
