# palace-instances-as-nodes

## 2026-07-27T17:50:00Z

```capsule
topic: palace-instances-as-nodes
date: 2026-07-27

seed (owner, verbatim): |
  "now, you can have multiple mind palace instances, but each one must live in its own node: let's
  use the trader as an example, it can potentially run an aws version of itself, the mind palace
  code, different knowledge base, and that's what interacts with edge agents, the knowledge graph
  itself is contained to its own node"

status: THOUGHTS ONLY. ⚑ This one reaches the constitution; nothing here is decided.
```

## THE SPLIT ALREADY EXISTS — this generalizes it, it does not invent it

The owner's own naming already separates the two: **mind-palace is the framework; Ouroboros is the
live system** (daemon + evolving corpus), named by its founding note. This idea simply says the
framework can be instantiated **more than once**, and that each instantiation is a **node**.

And there is a precedent one layer down: `dn-ouroboros-principal` (`superseded`) made Ouroboros a
**distinct least-privilege OS principal** — a dedicated user, not the owner's login. The progression
is one idea climbing layers:

| layer | the unit of isolation |
|---|---|
| OS | a principal (`dn-ouroboros-principal`) |
| network | ⚑ **a node role** ([[aws-as-the-authorization-spine]]) |
| system | ⚑ **an instance** — this capsule |

⇒ The singleton property carries up: *"one node may assume the Ouroboros role"* generalizes to
**one node per role**, with the spine holding the role→node binding. Trader is a different role;
it cannot be assumed by the node holding Ouroboros.

## WHAT IS SHARED AND WHAT IS NOT

**Shared: the code.** The framework, the gates, the artifact chain, the ring structure, the sensors.
⚑ This is a strong argument for the self-containment discipline already enforced here — code that
reaches sideways into one instance's specifics cannot be framework code.

**Not shared: the knowledge graph.** *"the knowledge graph itself is contained to its own node."*
That is the isolation property and it should be structural, not conventional — the same standard as
the sealed core's zero egress. Two palaces do not share a corpus, a vault, or a provenance history.

`[INFERENCE]` **Cross-instance interaction, if any, is edge-to-edge and never core-to-core.** It
would be an *interaction* that leaks, never a corpus that moves — the exact shape NN-11 already
draws for third parties. A trader that learns something does not thereby teach Ouroboros; if that is
ever wanted, it is a deliberate, gated transfer and its own design.

## ⚑⚑ THE CONSEQUENTIAL PART — the non-negotiables are parameterized by what the corpus IS

`CONSTITUTION.md` is the inviolable kernel every agent inherits, and `BUILD-SPEC §3`'s bright lines
were written for **this** corpus: the owner's private, personal knowledge. Read them against a
trading instance and several change character:

| line | Ouroboros (personal corpus) | ⚑ a trader instance |
|---|---|---|
| #1 sealed core, zero egress | the core sees the owner's life | the core sees market data and strategy |
| #11 the corpus never transits a third party | **the whole point** | a corpus that already *lives* in AWS has no "never" to protect |
| #8 memory ceiling ≤2 models, ~20–24 GB | a laptop's real limit | a **node property**, not a framework law |
| #12 telephony bounded to the owner's number | protects a person | means little for a strategy engine |

⇒ **Some constraints are about the framework; others are about what a particular instance holds.**
Conflating them is the danger in both directions:

- **Loosening by analogy** — *"the trader's data isn't sensitive, so this line can relax"* is exactly
  how bright lines erode. `CLAUDE.md` keeps the safety digest in context on **every turn**
  specifically because an out-of-context guardrail is not a guardrail.
- **Tightening by inheritance** — imposing the laptop's memory ceiling on a cloud node would be
  treating an environmental measurement as a law.

`[INFERENCE]` **The honest resolution is probably to make each instance DECLARE its posture
explicitly** — a per-instance constitution that *narrows*, never widens, the framework kernel, and
states what its corpus is and therefore which lines bind hardest. **⚑ Whether the kernel is global
or per-instance is a constitutional question and is the owner's alone.** It should not be settled by
a build.

## WHAT A SECOND INSTANCE WOULD ACTUALLY TEST

⚑ The framework has never been instantiated twice, so several things believed to be framework are
**unproven** and would surface immediately:

- **Hard-coded paths and identities** — `~/.mind-palace`, the single vault, the single exhaust lane,
  the `ouroboros` principal name itself.
- **Whether the "framework vs instance" line holds in the code** — the founding corpus, the golden
  set, `docs/tracks/**` and the artifact chain's content are all *this* instance's, sitting inside
  what is nominally the framework repo.
- **The scheduler's assumptions** — ≤2 resident models is a laptop fact; a cloud node has different
  arithmetic and possibly a different model tier entirely.

⇒ **A second instance is the falsifier for the framework/instance distinction.** Until one exists,
the split is asserted rather than demonstrated — and this repo's standard is that a property is real
only when something proves it ([[structural-enforcement]]).

## OPEN — owner-questions, not guesses

1. ⚑ **Is `CONSTITUTION.md` global to the framework, per-instance, or a global kernel each instance
   narrows?** The most consequential question here.
2. Does a second instance run **the same repo** or a fork? A fork drifts; a shared repo means this
   instance's artifact chain ships with the framework.
3. What, if anything, may cross **instance to instance** — and through which gate? `[INFERENCE]`
   the honest default is *nothing*, with any exception designed rather than permitted.
4. Does the spine's role binding make **role** a first-class axis of the capability-scope algebra,
   alongside strata and read/write?
