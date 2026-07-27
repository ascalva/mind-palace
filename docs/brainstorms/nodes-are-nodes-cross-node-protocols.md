# nodes-are-nodes-cross-node-protocols

## 2026-07-27T18:05:00Z

```capsule
topic: nodes-are-nodes-cross-node-protocols
date: 2026-07-27

seed (owner, verbatim): |
  "mind palace is a framework, ouroboros is the main instance, but really a node/instance is just
  another node in the graph (you see what i did there?), cross-node protocols will be necessary"

status: THOUGHTS ONLY. The self-similarity is seductive; the risk section exists because of that.
```

## THE RECURSION, STATED PLAINLY

| scale | nodes | edges |
|---|---|---|
| **inside an instance** | idea-atoms | membership, lineage, citation, supersession |
| **across instances** | ⚑ **palaces** | cross-node protocol |

The system's **topology** and the system's **subject matter** are the same shape. The name was
already correct — and this is the third time this week the palace's own structure turned out to be
an instance of what it studies: the context explosion was a feedback loop
([[context-load-as-a-feedback-loop]]); the corpus laundered its owner's voice; now the network of
palaces is a graph.

⚑ The owner's own joke, lost for two days and recovered by the intent audit, was **"even the logic
system has a logic system."** It keeps being load-bearing.

## ⚑⚑ THE PAYOFF — the machinery may already exist, one level up

If instances are nodes, the existing algebra is a candidate for cross-node relations rather than
something to invent: the query language (`dn-core-query-protocol`), the scope lattice
(`dn-capability-scope`), provenance, supersession, and the correction relation
(`dn-erratum-relation`) all type *relations between things* and none of them are inherently about
idea-atoms.

**The strongest fit is the edge-class distinction that already exists.** `dn-core-query-protocol`
separates **fibers** (warrant/citation — the semantic geometry) from **dispositional edges**
(supersession — carrying time), and rules that *the grounding-ratio walk must not traverse the
dispositional class*.

⇒ `[INFERENCE]` **A cross-node edge is plausibly a third class**, with the same shape of rule:

> **A semantic walk must never traverse a cross-node edge.**

⚑ **That single rule *is* the isolation property.** "The knowledge graph is contained to its own
node" stops being a policy and becomes a **walk rule on an edge class** — mechanically enforceable,
testable, and exactly the form the repo already trusts ([[structural-enforcement]]: a property is
real only when something proves it). Two palaces can be adjacent in a topology while remaining
non-adjacent in meaning.

## ⚑ THE RISK — self-similarity is the most seductive kind of wrong

A graph of instances is **not obviously the same kind of graph** as a graph of ideas, and the
differences are not decorative:

| | idea-atoms | instances |
|---|---|---|
| agency | none — an atom cannot decline | ⚑ a node can **refuse** |
| trust | an atom does not distrust another atom | mutual authentication is required |
| knowledge asymmetry | derivation is symmetric | a node may **know what it must not say** |
| truth | a claim is warranted or not | a claim is *also* **attributed to a speaker** |

⇒ Cross-node edges are **negotiated, authenticated, and refusable** — protocol edges, not derived
ones. Treating them as ordinary graph edges because the diagram looks the same would import an
assumption that does not survive the change of scale. `[INFERENCE]` The elegance is evidence that
this is worth exploring, **not** evidence that it is correct.

## WHAT A CROSS-NODE PROTOCOL HAS TO ANSWER

The identity half is already sketched ([[aws-as-the-authorization-spine]]): the spine holds the
role→node binding, so *who is speaking* has a mechanism. The rest is open:

1. ⚑ **What may cross — and the default is not "data".** [[palace-instances-as-nodes]] argues the
   NN-11 shape: **interactions leak, the corpus never moves.** A question and an answer may cross;
   a fiber may not.
2. ⚑ **What provenance does a received claim land as?** This is the chat-sensor problem again, one
   scale up. A claim from the trader is not this palace's observation and is certainly not its
   authored belief — it is *attributed testimony*, which the taxonomy has no member for today.
   ⚑ **Getting this wrong is exactly the 139-row defect**: text from elsewhere, filed as though it
   were the owner's own.
3. **How is a received claim corrected?** [[the-unchecked-claim]]'s twin at network scale: a node
   asserts something that turns out to be false. `dn-erratum-relation` supplies the shape —
   *correction = supersession ∧ erratum* — but the **warrant** for the erratum now lives on another
   node, and an unwarranted retraction is itself an authority claim.
4. **Refusal semantics.** A node declining must be distinguishable from a node being unreachable,
   and both from a node answering "no". Three states, not two.
5. **Loops.** ⚑ If A cites B and B cites A, the four-part destructive-loop signature applies
   *across nodes*, with no single process able to see the whole cycle
   ([[context-load-as-a-feedback-loop]]). The diagnostic was built for exactly this and has never
   been run on a topology it could not observe entirely.

## ⚑⚑ OWNER REFINEMENT (2026-07-27) — THE TRUST ANCHOR, AND TWO AXES THAT MUST NOT MERGE

> *"aws becomes the trusted third party, instance A and instance B are not living in a vacuum, they
> both know a trusted third party. a different instance is a different author, the trader is the
> trader author, not the alberto author, not the claude/dev author, not my node's system author,
> different authors, and when talking about authorship as an axis, they are at the opposite end of
> alberto author, i can still interact with those instances, and they could have slightly different
> authored content and dialogue, and that's ok, but their trust relationship between each other
> (instance nodes) are not the same as my authorship"*

### The anchor solves the bootstrap — and has one line that must not be crossed

Two instances that have never met cannot authenticate each other from nothing. A **common trust
anchor** is the standard resolution (the certificate-authority shape): neither needs to know the
other, both know the spine, and mutual authentication follows.

⚑ **But the anchor authenticates; it must never carry.** NN-11 says the interface may transit a
third party and the corpus never does — and AWS is a third party in *exactly* that sense. So:

| the anchor may | the anchor must never |
|---|---|
| assert *who is speaking* (role→node binding) | see what is said |
| revoke a node's standing | hold, relay, or store corpus |

`[INFERENCE]` ⇒ **Authentication and transport are separate concerns and should be separately
designed.** A protocol that authenticates through the anchor and *also* routes through it has
quietly made a third party a corpus carrier. Also worth stating plainly: a single trust anchor is a
**single point of trust failure** — if the spine is compromised, every instance's notion of "who is
speaking" is compromised at once. That is an accepted cost, not an absent one.

### ⚑⚑ THE CORRECTION THAT MATTERS MOST: authorship and trust are ORTHOGONAL

`dn-authorship-distance-axis` (`draft`) already defines the axis as **mediation between the owner
and the content**: a₀ self-authored → a₁ author-initiated → a₂ author-sensed → a₃ author-curated,
total order, nearer = higher.

**The owner's refinement adds two things to it:**

1. **The axis is OWNER-RELATIVE, and there is more than one author.** He names four already —
   *alberto author*, *claude/dev author*, *my node's system author*, *the trader author*. ⇒ Trader
   content is **a₀ on the trader's own axis** and far from a₀ on Alberto's. `[INFERENCE]` The axis
   is therefore not one line with instances strung along it; it is **one axis per author**, and
   cross-instance content is a *frame change*, not merely a longer distance. The note's own flagged
   edge case — *"`AUTHORED_DIALOGUE` is the owner's words only"* — is this same problem at
   conversational scale, and it is already recorded as unresolved.

2. ⚑ **Trust between nodes is a DIFFERENT AXIS and must not be folded into authorship.** His words:
   *their trust relationship between each other are not the same as my authorship.*

| axis | question | scale |
|---|---|---|
| **authorship distance** | how mediated is this content from a given author? | a₀ … a₃, per author |
| **node trust** | what protocol standing does this node hold? | attested / revoked / unreachable |

⇒ They are **independent**. A trader instance may sit at the far end of Alberto's authorship axis
*and* hold the highest node trust — spine-attested, enclave-bound. Conversely, content close to a₀
(Alberto's own words, relayed) can arrive over a channel with **no** node trust at all. Collapsing
the two would mean *"far from me" implies "distrusted"*, which is false and would make the trader
useless, or *"trusted node" implies "my authorship"*, which is the **139-row defect exactly** —
attributing another speaker's words to the owner because the channel was legitimate.

⚑ **Same partition-not-stack shape as [[kms-threat-layering]].** Independent controls answering
different questions; merging them loses the distinction that makes each one useful.

### ⇒ This answers open question 2, above

A received cross-node claim needs **both coordinates**: its position on the *sending author's*
authorship axis, and the *node trust* under which it arrived. Neither alone is sufficient, and
neither is a member of today's provenance taxonomy — which is the same gap `dn-chat-sensor` A1 just
had to amend a ratified note to close for `speaker='system'`.

And *"they could have slightly different authored content and dialogue, and that's ok"* is itself a
design permission worth recording: **instances are expected to diverge.** Divergence between nodes
is not drift to be reconciled — it is two authors, correctly, not being the same author.

## ⚑⚑ AND SO SCOPING PLAYS A ROLE HERE TOO — the owner, closing his own circle

> *"which means scoping now plays a role even here"*

This lands back on his statement from earlier the same day, about the query language:

> *"different scopes will automatically protect scopes, the types help… you ask a question through a
> question and a series of constraints… the query is lazy, an answer is only computed when the query
> is well-scoped and well-constructed."*

⇒ **That sentence was about retrieval inside one palace. It holds unchanged one level up.**

### Isolation stops being policy and becomes a TYPE

`dn-capability-scope` (ratified) already types a client by what it may reach — which strata, over
what window, with what authority. Add **node** as an axis and the containment rule from
[[palace-instances-as-nodes]] — *the knowledge graph is contained to its own node* — becomes:

> **No scope may name another node's stratum.**

⚑ Not a rule an agent must remember; a sentence that **cannot be constructed**. The same
unrepresentability that makes an ill-scoped query fail to compute makes a cross-node semantic read
fail to *type*. That is the strongest form of the walk-rule sketched above: the edge is not
untraversable by convention, it is unnameable by construction.

### The two axes enter scope at different points

The orthogonality established above is not a complication here — it resolves cleanly:

| | where it acts | what it decides |
|---|---|---|
| **node trust** | **before** the query — a precondition on scope grant | *may I address this node at all?* |
| **authorship distance** | **on the result** — a coordinate carried by what returns | *how mediated is what came back, and from whose hand?* |

⇒ **Trust gates the sentence; authorship annotates the answer.** A revoked node cannot be scoped,
so no query is even expressible against it. An attested node can be scoped — and everything it
returns arrives stamped far from a₀-Alberto, which is *correct* rather than a defect.

### Laziness earns its keep at network scale

The lazy property matters more here than locally: **an under-constrained cross-node query should not
resolve.** Locally, an over-broad query wastes compute. Across nodes, an over-broad query is a
**request another palace should refuse** — and a language where insufficient bounding simply does not
compute means the refusal happens before anything is transmitted, rather than depending on the
receiving node's good behaviour. `[INFERENCE]` That is a meaningful security property, not only an
efficiency one: the caller cannot ask a question it has not narrowed.

⚑ And it inherits the guarantee already noted: a lazy query **cannot emit an incomplete answer that
looks complete** — the structural defence against authority laundering. Across nodes, where the
answer arrives from another author, that guarantee is doing considerably more work.

## OPEN

- Is **node** a new axis of the capability-scope algebra, or a new **stratum**? The strata machinery
  already handles cross-stratum reads with budgets and firewalls; if a node is a stratum, much of
  the governance is inherited rather than invented. `[INFERENCE]` — attractive, and precisely the
  kind of attractive this capsule's risk section warns about.
- Does a cross-node claim need a **speaker** field the way `dn-chat-sensor` A1 now needs
  `speaker='system'`? The two problems look identical at different scales.
- ⚑ **Nothing here is buildable until a second instance exists.** Until then the protocol has one
  endpoint, and a protocol with one endpoint is a design that cannot be falsified.
