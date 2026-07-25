# Ops and the optimal form of the code — compression, cost, and measured access patterns

Brainstorms on the operations dimension of the project: performance as a first-class concern, cost
as a checkable property, and what the *optimal form* of the code and its data actually is. Warrant:
finding-0169 (the first real performance bottleneck) and the owner's reading of it as a complexity
time bomb. Companion capsule: `command-center.md` (the instrument this track needs).

## 2026-07-25 — the first bottleneck, and what it says about form

```capsule
topic: ops-and-optimal-form
date: 2026-07-25 (session-44, immediately after the finding-0169 incident)

warrant (owner, verbatim): "I'd say we hit our first performance bottleneck that resulted in a
potential ticking timebomb of complexity, I think these types of performance metrics and a quick
but deep understanding of the system's live metrics: the ops side of the project (operations, that
is), but this motivates me to now think about compression and performance, what is the optimal (or
at least more optimal) form of the code?"

owner's sharpening (same sitting): "which relates to the vector store containing vectors to
different memberships, that is a type of data compression" — i.e. finding-0168's membership model
is NOT only a semantic model; storing one vector with many memberships instead of one copy per
version/file IS compression, and the semantic and performance arguments are the same argument.

WHY IT WAS A TIME BOMB, NOT A BUG:
  Nothing about `supersede_source` changed. Its CALLING CONTEXT changed. Delete-then-re-add is
  correct and cheap at note scale (tens of rows, one-off migration). bp-099 promoted that same
  primitive into a per-version loop against a monotonically growing table. An O(n) primitive inside
  an O(n) loop is O(n^2), and NO LINE OF CODE HAD TO BE WRONG for that to happen.
  ⇒ **Cost is not a property of a function. It is a property of a function IN A CONTEXT.**
  The codebase has strong discipline about SEMANTICS (types, provenance, import firewall,
  attestations, the sealed core) and essentially NONE about COST. No function declares "I am
  O(table)", and nothing notices when such a function is called inside a loop.

THE REPEAT (uncomfortable, and the reason this deserves a track):
  finding-0163 = "PD-B was ratified on a false quantitative premise — the cost of history was never
  measured." finding-0169 = the re-land idiom was adopted without measuring its cost. SAME FAILURE
  MODE, ONE WEEK APART: a cost premise ASSERTED rather than MEASURED. The reconciliation-audit's
  "measured premises" instrument was designed for exactly this and does not exist yet.

THREE LAYERS (the question "what is the optimal form?" is really three questions):

  (1) REPRESENTATION — compression. The vector column IS the cost: 2560 dims x float32 ~ 10 KB/row;
      22,621 rows ~ 226 MB of pure geometry. An operation that drags vectors through Python pays
      ~1000x one that touches metadata only.
      · Structural rule: SEPARATE THE GEOMETRY PLANE FROM THE METADATA PLANE. Never carry vectors
        through an operation that only flips a flag.
      · ⚑ THE f-0168 CONVERGENCE: that rule is what the membership store already says — "a point is
        geometry, meaning lives in membership, history in slot-lineages." Derived from SEMANTICS
        (dedup, append-only, git's model at idea grain) and now INDEPENDENTLY RE-DERIVED FROM
        PERFORMANCE. Two orthogonal arguments converging on one design. Under it, tonight's defect
        is structurally impossible — there is no re-land.
      · The owner's point stated precisely: membership IS the compression. One vector reachable from
        many memberships replaces one copy per (version, file). Dedup across versions/reverts/files
        is a storage win AND a semantic win; the backfill was re-embedding and re-landing chunks
        that never changed.
      · Further, MEASURED not assumed: quantization (int8/binary coarse pass + exact rerank) is a
        further 4-32x on the geometry plane, but trades retrieval quality — it needs a measurement
        and a falsifier before adoption, per this very finding's lesson.

  (2) ACCESS — the mechanical rules. Any one of these alone prevents finding-0169:
      · push predicates into the store; never filter in Python after a full scan
      · never scan what can be indexed
      · never materialize a column you do not read (above all, `vector`)

  (3) DISCIPLINE — how the NEXT one is prevented. Rules in a doc do not hold (standing owner
      ruling: a property is only real when a test/ratchet proves it). The structural version is a
      PERFORMANCE RATCHET SUITE — the ops analog of the frozen golden set:
      · assert an operation's cost is independent of unrelated store size
      · store ops declare the largest N at which they have been MEASURED ("scale witness")
      · a call site operating beyond its primitive's measured N is a finding
      · candidate: extend the reconciliation-audit's decision→enforcement map with a cost column

THE REFRAME (the part worth arguing about):
  "What is the optimal form?" cannot be answered yet, because THE SYSTEM DOES NOT KNOW ITS OWN
  ACCESS PATTERNS. Optimal is a function of how data is actually read; right now that is
  speculation. But Ouroboros is unusual — it already ingests its own code, transcripts, and
  exhaust. It can measure itself.
  ⇒ Honest sequence: INSTRUMENT → MEASURE ACCESS PATTERNS → DERIVE REPRESENTATION.
  ⇒ Which makes the command center more than a dashboard: it is the SENSOR THAT MAKES PERFORMANCE
    WORK EMPIRICAL, and the same philosophy already ratified everywhere else (falsifiers over
    proofs, measured premises over asserted ones). The ops track and the compression track are the
    same track; the metrics are its INPUT, not its alarm panel.

open questions:
  - Does the performance ratchet live in `eval/` (beside the golden set, as its ops analog) or in
    `tests/` as a ratchet? The golden set is frozen and human-only; perf baselines drift with
    hardware — so they are NOT the same kind of fixed point. Needs a design answer.
  - How is a "scale witness" expressed so it is checkable and not a comment? (type? decorator?
    docstring convention parsed by a gate? — the provenance discipline is the model to copy)
  - Which access patterns actually matter? Retrieval is the obvious one, but the dreamer's full
    scans, the integrator's joins, and the drift gauges have entirely different shapes.
  - Quantization: what is the acceptable retrieval-quality loss, and what falsifier proves it?
  - Does this track absorb finding-0165 (background starvation) and f-0171 (job budgets), or do
    those stay scheduler-local? They are all "cost as a first-class concern" in different clothes.

sequencing: THIS MUST NOT DELAY THE finding-0169 FIX. That is a small mechanical change that gets
the daemon back up. This is a track — capture → Fable design pass → adversarial panel (systems +
core + math) → graduate. Its natural first deliverable is the ratchet, not a rewrite: the membership
store (f-0168) is already the representation answer, and it needs the measurement discipline around
it more than it needs new ideas.
```
