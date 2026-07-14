# Brainstorm — the magnetic Laplacian: "direction" as a field on the graph

> Seed (owner + orchestrator, 2026-07-14). The owner: the magnetic Laplacian *"feels like the
> natural progression of the physics and intuition I've been describing via 'direction' of a
> graph."* This is the **framing/scouting doc** a fable pass consumes (now, on credits) — so
> fable spends on reasoning, not rediscovery. It **reverses decision-#4's DEFER** (owner,
> 2026-07-14) and gives the ratified `dn-temporal-retrieval-algebra` TA-a its re-entry. Extends
> the ratified `dn-temporal-retrieval-algebra` (§2.1 ii, the named `L^{(q)}` upgrade; TA-a) and
> `dn-edge-dynamics` (Hodge/curvature); it edits neither (both immutable).

## The arc, in one line

The program went **state → direction**: the snapshot is `q`; the 1-form lift + supersession /
edge-strength series gave `p`; the dreamer-direction seed asked for the graph's *velocity*. The
**magnetic Laplacian** is the next rung — the operator that makes "direction" a first-class
**field on the graph** (direction encoded as a magnetic flux) while keeping the
symmetric-operator spectral theory the whole `core/complex/` module rests on. It formalizes "the
graph has a direction" as an *operator*, not a metaphor.

## 1. The physics progression (why it fits the intuition)

| owner intuition | discrete structure | house object |
|---|---|---|
| state / position `q` | the snapshot | stores at HEAD (built) |
| direction / momentum `p` | supersession chains + edge-strength series; the 1-form lift | `dn-self-sensing` B-a; `dn-edge-dynamics` (built floor: `hodge.py`) |
| **"direction" as a field the whole graph feels** | the **magnetic (Hermitian) Laplacian `L^{(q)}`** — a charged particle diffusing on the graph feels edge-direction as a magnetic field (Aharonov–Bohm / Peierls phase); **flux around a loop = net directed circulation** | *this brainstorm → fable → a new note* |

`q=0` (field off) recovers the ordinary symmetric Laplacian **exactly** — today's undirected v1;
`q>0` (field on) encodes direction in a complex phase while staying **Hermitian ⇒ real spectrum,
PSD, an orthogonal (complex) eigenbasis** (all the spectral machinery, now direction-aware). It
is DAG-native (unlike Chung's directed Laplacian, which needs strong connectivity) — exactly the
citation/supersession shape.

## 2. The two directed structures it would sit over

- **Citation graph `X_cite`** — directed by *intellectual influence* (citing → cited). Has
  undirected cycles; flux = directed circulation of influence.
- **Supersession DAG** — directed by *time* (old → new). Acyclic ⇒ no directed cycles — **but the
  undirected skeleton has cycles at fork/merge diamonds**; flux there = the fork/merge
  **holonomy**.

## 3. The sharp questions (for the fable pass — all `[OPEN]`)

1. **Magnetic Hodge.** Does `L^{(q)}` lift to degree 1 (a magnetic `L₁`)? Is there a magnetic
   Helmholtz decomposition (gradient ⊕ curl ⊕ harmonic, complexified)? Is the flux a genuine
   curvature 2-form?
2. **The diamond identification (the exciting conjecture).** Is the magnetic flux around a
   supersession fork/merge **diamond** the SAME object as the `[d,τ]` diamond holonomy that
   `dn-temporal-retrieval-algebra` §2.3 Result 3 could only **sketch** (TA-c)? **If yes, the
   magnetic Laplacian closes TA-c.** Test it, don't assume it.
3. **The E_disp question.** A5 ruled E_disp (acyclic supersession) is *pure gradient* (curl-free,
   harmonic-free). So on the DAG, does the magnetic field live **only** on the fork/merge diamonds
   (net-zero elsewhere)? Is that exactly the place "direction" is NOT already captured by the depth
   gradient — the magnetic Laplacian's non-trivial content on the temporal side?
4. **One field or two.** Citation-influence direction vs supersession-time direction — one charge
   `q` or two? Do they correlate (does influence flow forward in time)?
5. **Flux ⟷ Ricci.** The owner's curvature instinct: is the magnetic flux the **directed
   curvature** that connects to Forman–Ricci (built, `curvature.py`) / Ollivier–Ricci (deferred,
   PD-c)? Is "magnetic flux ≈ directed Ricci"?
6. **The three roles — rule which it EARNS (owner: all of the above).** (a) *retrieval upgrade* —
   directed Mode-1b diffusion (PD-b's "second customer"; "downstream of s" vs "upstream of s"); (b)
   *diagnostic lens* — an arrow-aware directed-flow dreamer interpreter (the THREAD lens's directed
   cousin); (c) *unifying structure* — magnetic Hodge / flux-as-curvature / the diamond + Ricci
   unification. Rule which it earns against the discipline (§4), don't assume all three.
7. **The falsifier + graduate-or-defer.** The magnetic analog of the built `dim ker L₁ == ripser`
   falsifier (a directed/magnetic homology invariant?). Does it earn **buildable-now** (a
   falsifiable structural deliverable, like the undirected Hodge lift) or **wait** for a
   retrieval-eval customer?

## 4. The discipline (must earn its place)

The undirected Hodge lift graduated because its deliverable — the *thread structure* — was
topological and falsifiable, not because it was elegant. The magnetic version must pass the **same
test**: a falsifiable customer or a falsifiable structural deliverable. **The fable pass RULES
this; it does not assume graduation.** Elegant-but-unfalsifiable → it stays design-tier vocabulary.

## 5. Inherited constraints (unchanged)

- `q=0` recovers v1 **exactly** — a graceful generalization, never a silent behavior swap.
- Deterministic, sparse, model-free (same house as `hodge.py`); DAG-native.
- **The inversion binds:** the magnetic spectrum is INTERPRETED-class, falsified against exact
  discrete invariants at the sample times.
- A magnetic/temporal module lives **OUTSIDE `core/complex/`** (the isolation grep, `dn-temporal-
  retrieval-algebra` A4), reading `ReferenceEdgeStore`, never touching `A_signed`/`build_complex`.
- `dn-edge-dynamics` + `dn-temporal-retrieval-algebra` are **ratified/immutable** — the
  formalization enters as a **NEW draft note**, cross-linked, never an edit.

## 6. Routing

- **Reverses decision-#4** (DEFER → develop now). The ratified `dn-temporal-retrieval-algebra`
  TA-a's re-entry is *"this brainstorm + the fable pass."*
- **Fable pass NOW** (on credits, owner-approved 2026-07-14). Home of the formalized answer: a
  **NEW draft design note** (companion/successor to `dn-temporal-retrieval-algebra`). This
  brainstorm is the charter seed the pass consumes.
