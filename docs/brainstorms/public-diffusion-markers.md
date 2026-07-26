# public-diffusion-markers

The corpus is published, therefore it is public fact. Can the palace *sense its own footprint* —
plant unique markers in what it publishes, then watch them surface in the reaches?

## 2026-07-26T06:20:00Z

```capsule
topic: public-diffusion-markers
date: 2026-07-26

decisions:
  - THE IDEA (owner, 2026-07-26, verbatim): "the work we do and publish is now public fact, which
    means we can use unique markers in the code/documents, to perform queries against DNSs, info
    pages, public ledgers, see how its presence passively dilutes itself into the reaches, I know
    we can't really do a whole lot, but I assume artifacts will slowly emerge in some way or
    another."
    ⇒ A new SENSING direction, pointed OUTWARD. Every existing sensor axis looks inward (φ_code
    over the repo, φ_self over the cost stream, the observed stratum, the reference sensor). This
    one measures the corpus's own diffusion into the public sphere: the palace as seen from
    outside. Call the quantity a DIFFUSION TRACE -- a dated, attributable observation of our own
    text somewhere we did not put it.
  - ⚑ THE PRECONDITION IS ALREADY TRUE AND ALREADY SETTLED. The repo is PUBLIC
    (`github.com/ascalva/mind-palace`) and the corpus is outside it (`.gitignore:13`). So this
    proposes no new exposure whatsoever: it instruments text that is already world-readable. It
    also sits squarely inside the existing security-through-transparency stance (see
    `docs/brainstorms/phone-chat-surface.md`) rather than testing it.
  - ⚑⚑ THE TIME ASYMMETRY IS THE WHOLE POINT -- AND IT ARGUES FOR ACTING NOW. A marker is only
    evidence if it was planted BEFORE the diffusion it detects. Planting is cheap, reversible,
    and possible today; querying is the expensive half and can wait indefinitely without losing
    value. ⇒ SPLIT THE WORK: plant + register now, sense later. Every day the planting slips is a
    day of diffusion that becomes permanently unmeasurable. This is the rare case where the cheap
    half is the urgent half.
  - WHAT IS ACTUALLY MEASURABLE -- four tiers, honestly separated, because an instrument that
    blurs them will overclaim, and overclaiming in the tracking record is exactly the finding-0011
    defect class:
      (1) DIRECTLY OBSERVABLE, CHEAP -- "does this string appear where I did not put it": public
          code search (GitHub code search, grep.app), general web search, fork/mirror detection,
          scraper-aggregator sites, package indices. Confirms presence with a date.
      (2) OBSERVABLE IF WE OWN THE RESOLVER -- a marker shaped as a HOSTNAME under a zone we
          control (`ascalva.com`, Route53 zone `Z04459637698U9GB7PGC`, already measured
          authoritative) yields PASSIVE resolver logs when anyone dereferences it. The classic DNS
          canary. Stronger than (1): it shows someone RESOLVED or EXECUTED the marker, not merely
          that a crawler copied bytes. Cost: Route53 query logging, already-owned infrastructure.
      (3) ⚑ THE SHARPEST ONE THE OWNER'S "PUBLIC LEDGERS" POINTS AT -- **Common Crawl is a public,
          dated, QUERYABLE index**, and it is a known upstream input to LLM training corpora. So
          "is our text in Common Crawl, and since which crawl?" is DIRECTLY answerable, which
          converts the hopeless question ("am I in a training set?") into a tractable one ("am I
          in the pipeline that feeds training sets, and since when?"). Same family: Software
          Heritage (archives public git repos with persistent SWHIDs), the Wayback Machine, and
          GH Archive (a public dataset of all public GitHub events).
      (4) WEAKLY INFERABLE, MUST NOT BE OVERSTATED -- actual training-set membership. Detectable
          only if a model RECITES a marker under extraction prompting, or by membership inference.
      (5) NOT OBSERVABLE AT ALL -- private scraping, closed internal corpora.
  - ⚑⚑ THE FALSIFIER ASYMMETRY, STATED UP FRONT SO THE INSTRUMENT CANNOT LIE LATER. This
    instrument can CONFIRM diffusion; it can never REFUTE it. Absence of a trace is not absence of
    diffusion -- tiers (4) and (5) guarantee a silent channel. ⇒ The honest claim is always "a
    dated LOWER BOUND on diffusion", never "the extent of diffusion", and a null result is
    uninformative rather than reassuring. Worth pinning in the note's non-goals, since a non-goal
    is load-bearing and fails silently forever if wrong (finding-0150).
  - ⚑⚑ THE HAZARD WITH DIRECT PRECEDENT -- MARKERS WILL POLLUTE OUR OWN EMBEDDING SPACE. Code is
    now a first-class semantic source that MUST be embedded (owner ruling 2026-07-21,
    finding-0146). So markers planted in code and docs enter the palace's own vector corpus. This
    is precisely the finding-0077 defect, already MEASURED once: a shared `"id:: "` prefix plus a
    random uuid lifted borderline pairs over σ (mirror edges 5 → 9 at σ=0.62, per-note centroid
    drift mean 0.953) and made the dreams cluster on IDENTITY METADATA instead of content. A
    high-entropy marker repeated across surfaces is the same failure shape, and it would corrupt
    the dream layer to instrument the outside world. ⇒ Markers must either be STRIPPED from the
    derived/embedded text (the `strip_properties` precedent, `core/ingest/pipeline.py`) or carry
    NO shared prefix and NO repetition. This is a hard requirement, not a nicety.
  - ⚑ PRACTICAL GOTCHA -- OUR OWN CI WILL FIGHT US. A high-entropy random token in the tree is
    what `gitleaks` and `semgrep` exist to find; both run in the authoritative GitHub CI. A marker
    must be designed to read as deliberate, documented, non-secret text, or the planting commit
    turns the security gate red and the marker gets "fixed" by a future builder who does not know
    what it is. The registry (below) is what makes it legible.
  - MARKER DESIGN, from the above constraints:
      · SURFACE-DISTINCT, never one marker everywhere -- a different marker per surface (code
        identifier, docstring, design-note prose, commit trailer, config default, filename) is the
        only way to learn WHICH surface diffuses. A single shared marker destroys that signal and
        maximizes the embedding pollution at the same time.
      · A REGISTRY IS MANDATORY: marker → surface → plant date → commit sha → expected
        observability tier. Without it, a later hit cannot be distinguished from a
        misremembering, and the experiment is unfalsifiable in the other direction too.
      · NEVER a plausible real identifier (a marker importable as a symbol could break a
        downstream reader) and never a secret-shaped string (see the CI gotcha).
      · Attribute hits, never count them: a public marker is also an invitation to POISON the
        signal by reposting it. Provenance of each hit matters; a tally is meaningless.
  - WHERE IT MAY LIVE -- the boundaries decide the architecture, and they are not negotiable.
    Querying DNS, fetching public pages, and hitting ledger APIs is NETWORK work: it belongs in
    `edge/` only, it never reads the vault (NN-2), and the sealed core keeps zero egress (NN-1).
    In effector terms this is a READ hand -- the safest class -- and therefore exactly the kind of
    capability the owner just authorized moving toward when ruling the effector ceiling up
    (autopilot ruling 2, 2026-07-26, staged per role/class with class 3 unreachable). ⇒ This
    direction is REACHABLE under a ruling already made, at the lowest-risk class. It needs no new
    permission of its own.
  - ⚑ AN UNEXPECTED CROSSOVER WORTH MORE THAN THE ORIGINAL IDEA. Autopilot ruling 5 established
    that the "publicly auditable authority record" now rests on GITHUB ALONE, to be stated as a
    named single-point dependency. Software Heritage and the Wayback Machine are INDEPENDENT
    public archives of the same text. ⇒ The ledger set this instrument would query doubles as
    REDUNDANCY for the authority record -- registering the repo with Software Heritage both plants
    a diffusion sensor and retires a named single point of failure. Two threads, one cheap action.

parked:
  - decision: does the DNS-canary tier (2) happen at all? It is the only tier that observes THIRD
    PARTIES (whoever resolved the name), which is a surveillance surface on readers, not a
    measurement of ourselves.
    default: DO NOT build tier (2) in the first pass. Tiers (1) and (3) measure only our own text's
    presence and need no stance on other people; the canary needs an explicit owner stance first,
    on the model of the security-through-transparency stance and its qualifier.
    re_entry: the design note; or the owner rules the stance directly.
  - decision: are markers stripped from embedded text, or designed prefix-free and left in?
    default: STRIP, mirroring `strip_properties` -- it is the option that cannot regress the dream
    layer, and finding-0077 is the measured precedent for what the other choice costs.
    re_entry: the design note; entangled with the still-open σ retune (oq-0024).
  - decision: which surfaces get markers, and how many.
    default: start with the three that are certainly public and certainly stable -- design-note
    prose, a docstring, and a commit trailer -- and add code identifiers only after the strip
    question is settled.
    re_entry: the design note.

open_questions:
  - Is the registry itself public? A public registry makes every marker trivially discoverable and
    therefore trivially poisonable; a private one sits in the corpus (outside the repo) and cannot
    be verified by anyone else, including a future us.
  - Does a diffusion trace enter the reasoning complex as an observation -- a new stratum or axis
    (the corpus reflected back from outside) -- or does it stay pure ops telemetry? The authorship
    -distance axis ("every stratum is self-data, at a distance") is the natural home if it enters
    at all, and "text of ours, observed in a stranger's copy" is a genuinely new distance.
  - What is the sensing CADENCE, given that diffusion is slow (months) and the queries cost money?
    A yearly sweep may dominate a monthly one at a fraction of the cost.
  - Does any of this belong to the sector-expert / external-grounding machinery already drafted,
    rather than to a new subsystem?

next_steps:
  - Design-note-first; NOT graduatable yet. The note must carry: the four measurability tiers kept
    separate, the falsifier asymmetry as an explicit non-goal, the embedding-pollution requirement,
    the edge-only placement, and the Software Heritage crossover.
  - The cheap urgent half, separable from the note: decide the marker shape and PLANT + REGISTER.
    Sensing can lag by a year without losing anything; planting cannot lag at all.

references:
  - docs/brainstorms/phone-chat-surface.md          # security-through-transparency stance + qualifier
  - docs/brainstorms/autopilot-mode.md              # ruling 2 (ε raise, read hands) · ruling 5 (GitHub alone)
  - docs/findings/finding-0077.md                   # MEASURED embedding pollution from a shared random prefix
  - docs/findings/finding-0146.md                   # owner ruling: code must be vectorized
  - docs/findings/finding-0150.md                   # non-goals are load-bearing and fail silently
  - docs/findings/finding-0011.md                   # the overclaim defect class this must not repeat
  - core/ingest/pipeline.py                         # strip_properties -- the strip-before-embed precedent
  - docs/design-notes/authorship-distance-axis.md   # candidate home if a trace enters the complex
  - docs/design-notes/attestation-layer.md          # the authority-record thread the ledgers cross into
```

## 2026-07-26T06:32:00Z

```capsule
topic: public-diffusion-markers
date: 2026-07-26

decisions:
  - ⚑⚑ THE REFRAME (owner, 2026-07-26, verbatim): "you could call it an agent, probing for itself
    in the public domain, finding how its external graph is represented."
    ⇒ This is a strictly BIGGER instrument than the first capsule's, and it renames the quantity.
    The first capsule asked a scalar question -- did our text leak, and when. This asks a
    STRUCTURAL one: reconstruct THE EXTERNAL GRAPH -- the graph of how the palace is represented
    outside itself -- and compare it to the internal one.
  - THE EXTERNAL GRAPH, concretely. Nodes: external artifacts that reference us (forks, mirrors,
    archive snapshots, crawl records, pages that cite a note, a model output that recites a
    marker). Edges: the referencing relation, plus those artifacts' own links to each other. It is
    a real graph, not a list -- and the palace is already a graph-native system with a citation
    store, so the machinery to hold it exists.
  - ⚑⚑ THE MEASUREMENT THAT MAKES THIS WORTH BUILDING IS THE *DIFFERENCE*, NOT THE GRAPH. We
    already hold the internal graph (the authored corpus and its citation structure). The external
    graph is a LOSSY, BIASED PROJECTION of it -- whatever happened to get crawled, linked, forked,
    or recited. So the instrument's real output is the DISTORTION between them:
      · which notes are OVER-represented outside relative to their internal centrality
      · which are structurally central internally and INVISIBLE outside
      · whether the outside preserves our supersession order at all, or flattens a lineage into
        whichever version got scraped -- a superseded claim can outlive its successor in public
      · whether the external graph's shape resembles ours or is dominated by a single mirror
    ⚑ That last one has teeth: if the external graph is one archive's snapshot, then "public fact"
    is really "one crawler's opinion", and the transparency the stance rests on is thinner than it
    looks. The distortion is the finding; the graph is only the substrate for computing it.
  - ⚑ IT IS THE SELF-MAP AT MAXIMUM DISTANCE, and that gives it a home. The palace is already a
    self-map, and `dn-authorship-distance-axis` holds that "every stratum is self-data, at a
    distance". The external graph is self-data held BY STRANGERS -- the largest distance the axis
    can express, and arguably the first genuinely new value on it since the axis was drafted. If a
    diffusion trace enters the reasoning complex at all (first capsule's open question), this is
    the answer to WHERE.
  - ⚑⚑ "AGENT" IS THE OPERATIVE WORD, AND IT LANDS EXACTLY ON WORK IN FLIGHT. Autopilot ruling 1
    (2026-07-26) made a role a CATALOG SUBSET -- "a hand is expressible iff it is cataloged". This
    is a new role: a PROBE (or scout). Its catalog subset is READ HANDS ONLY, and uniquely among
    the roles designed so far, its reads are NETWORK reads rather than repo reads -- so it lives in
    `edge/`, never touches the vault (NN-2), and the sealed core keeps zero egress (NN-1).
    ⇒ AND IT IS A CANDIDATE FIRST STAGE FOR THE ε RAISE (ruling 2: staged per role/class, class 3
    unreachable). An agent that only reads PUBLIC information ABOUT ITSELF is close to the safest
    conceivable first effector role: it reads no private data, mutates nothing, and its worst
    failure mode is holding a wrong belief about the outside world. If the ceiling is going up in
    stages, this is a strong argument for which stage goes first.
  - ⚑⚑ THE LEAK VECTOR, AND ITS STRUCTURAL FIX. An agent that queries the public web on our behalf
    is an OUTBOUND channel, and NN-11 is explicit: the interface may transit a third party, the
    corpus never does. A probe that formulated its queries FROM corpus content would leak corpus
    text into search queries -- the exact prohibited thing, dressed as telemetry.
    ⇒ FIX, and it is the same discipline as the effect catalog: THE PROBE'S QUERY VOCABULARY IS THE
    MARKER REGISTRY -- a closed, finite, pre-declared set. A query is EXPRESSIBLE IFF IT IS
    REGISTERED. No free-text search over corpus content, ever. This makes the leak bound provable
    by construction rather than by the agent's good behaviour, which is the only kind of bound this
    project accepts.
  - ⚑⚑ THE THREAT NOBODY ELSE IN THIS SYSTEM FACES: THE PROBE'S INPUT IS CHOSEN BY ADVERSARIES WHO
    HAVE READ OUR SOURCE CODE. The repo is public. So an attacker knows which markers the probe
    searches for, and can serve a page containing that marker plus injection text, with high
    confidence our probe will fetch it. Every other component's input comes from the owner or from
    the corpus; this one's comes from strangers who can read the spec for how it will be consumed.
    ⇒ CONSEQUENCES: (a) retrieved content is UNTRUSTED OBSERVED data, never authored corpus, and
    never instruction (NN-3/NN-4); (b) strongly prefer never feeding retrieved page BODIES to a
    model at all -- extract structured metadata only (URL, fetch date, which marker matched, a
    content hash) and let the graph be built from metadata, so there is no natural place for
    injected prose to be read as a directive; (c) hits are attributed and provenance-labelled, not
    counted (the poisoning point from the first capsule, now sharper -- poisoning is not a nuisance
    here, it is the expected adversary behaviour).

parked:
  - decision: does the probe compute the DISTORTION (internal vs external comparison), or only
    collect the external graph and leave comparison to a later lens?
    default: collect first, compare later -- the collection is the irreversible, time-critical half
    (first capsule's time asymmetry), and the comparison needs the internal graph's own centrality
    instruments, which are themselves still built-but-unvalidated at this corpus scale.
    re_entry: the design note.
  - decision: is the probe a role in the autopilot role catalog, or a separate edge subsystem that
    merely happens to be agent-shaped?
    default: catalog it as a role -- ruling 1's whole point is that granularity is structural, and
    an uncataloged network-reading agent is precisely the thing the catalog exists to forbid.
    re_entry: the role-catalog design (the superseding autopilot note).

open_questions:
  - Does the external graph get its own store, or is it edges in the existing citation store with a
    new node kind? Precedent cuts toward a new kind: the `workflow` node-kind ruling refused to
    widen `corpus` because it would make the kind-name lie. An `external` kind looks like the same
    call -- but these nodes are UNTRUSTED, which no existing kind is.
  - If a model recites one of our markers, is that an edge in the external graph -- and from what
    node? A model is not a document, has no URL, and cannot be re-observed identically.
  - Does the probe's own activity become part of what it measures (we query, therefore we appear in
    someone's logs)? Small, but it is a genuine observer effect in a system that cares about them.

next_steps:
  - Fold both capsules into ONE design note: markers + registry + the probe role + the external
    graph + the distortion measurement. The first capsule's four measurability tiers and falsifier
    asymmetry remain the note's spine; this capsule supplies the object being built and the two
    hard boundaries (registry-as-query-vocabulary, untrusted-input).
  - Still design-note-first, still not graduatable. The one separable, urgent, cheap action remains
    PLANT + REGISTER the markers -- unchanged by this reframe, and prerequisite to all of it.

references:
  - docs/brainstorms/autopilot-mode.md              # ruling 1 (roles as catalog subsets) · ruling 2 (ε raise)
  - docs/design-notes/authorship-distance-axis.md   # self-data at a distance -- the home for the external graph
  - ops/effect_catalog.py                           # "expressible iff cataloged" -- transposed to queries
  - docs/findings/finding-0065.md                   # the node-kind precedent: do not make a kind-name lie
  - CONSTITUTION.md                                 # NN-1 zero egress · NN-2 no network+private · NN-11 corpus never transits
```

## 2026-07-26T06:48:00Z

```capsule
topic: public-diffusion-markers
date: 2026-07-26

decisions:
  - ⚑⚑ THE SAFETY CONSTRAINT (owner, 2026-07-26, verbatim): "the point of the agent is to also
    perform searches safely, it shouldn't be trying to attract attention, not sure we want it
    telling the world it's looking for itself."
    ⇒ This is not a posture preference layered on top of the design -- it INVALIDATES the obvious
    architecture and forces a better one. Read the two capsules above with this as a hard constraint.
  - ⚑⚑ THE QUERY IS ITSELF A DISCLOSURE, and this is the crux. Asking an external service "where
    does string X appear?" tells that service -- and anyone with access to its query logs -- that we
    care about X. A high-entropy unique marker makes this maximally bad: a needle query puts the
    needle in someone else's log, permanently, attributed to whoever asked. The CONTENT being public
    does not make the QUERY harmless. Every tier-(1) search in the first capsule has this defect.
  - ⚑⚑ THE FIX -- INVERT THE QUERY: PULL THE HAYSTACK, NEVER BROADCAST THE NEEDLE. Do not ask a
    service about our marker. Instead fetch the PUBLIC BULK DATASET and search it LOCALLY. Common
    Crawl publishes its index; Software Heritage publishes its archive; GH Archive publishes event
    dumps. Downloading a public dataset discloses only "somebody downloaded a public dataset" --
    an uninteresting fact with no needle in it -- and the match happens on our own machine where
    it belongs. More bandwidth, zero disclosure. ⚑ And it is the architecture the palace already
    has everywhere else: local-first, the corpus never transits, compute where the data is trusted.
    The naive design was an API-call fan-out; the right design is an offline index sweep.
  - ⇒ CONSEQUENCE: THE DNS-CANARY TIER IS NOW A **NO**, not a deferral. Capsule 1 parked tier (2)
    pending an owner stance. It is settled: a canary EXISTS to be dereferenced -- it is an
    attention-attracting instrument by construction, it observes third parties, and it converts our
    own zone into a beacon. It also collides with the separately-open question of whether
    `ouroboros.ascalva.com` gets a public A record at all. Drop it from the design; keep the
    reasoning so it is not re-proposed.
  - ⚑⚑ AND THE DEEPEST TENSION, WHICH HAS A CLEAN RESOLUTION: **you cannot have a quiet instrument
    whose design lives in a public repo.** Publishing the note describes the instrument to exactly
    the people who would poison or evade it. But the resolution is standard and strong:
        DESIGN PUBLIC · MECHANISM PUBLIC · MARKER VALUES PRIVATE · REGISTRY PRIVATE
    i.e. Kerckhoffs's principle. The secret is the marker set, never the method. ⇒ This SETTLES
    capsule 1's open question ("is the registry public?") in favour of **private, corpus-side**
    (outside the repo, per `.gitignore:13`) -- and note the pleasing consequence: the markers are
    planted in public, the registry that interprets them is not, so a reader of the repo learns
    that we measure diffusion without learning what to look for or what to forge.
  - QUIETNESS REQUIREMENTS, concretely -- each one is a design constraint, not advice:
      · NO WRITES OF ANY KIND, ever. No posting, no issue-opening, no forking, no registration, no
        comment, no pingback. Read-only is no longer only a safety property (class 1) -- publishing
        anything at all IS announcing. This tightens the read-hand constraint rather than restating
        it.
      · NO DISTINCTIVE CADENCE. A probe on a fixed schedule with a recognizable request fingerprint
        becomes a marker itself, and one that identifies us on the timing channel rather than the
        content channel. Prefer rare, irregular, low-volume sweeps -- which the slow physics of
        diffusion (months) makes free: capsule 1 already argued a yearly sweep may beat a monthly
        one, and quietness now argues the same way.
      · PREFER NOT FETCHING ARBITRARY PAGES AT ALL. Fetching a page tells its operator we read it,
        with our address and timing. Bulk-index work needs no per-page fetch; if one is ever
        unavoidable, it is a deliberate, logged exception, not the default path.
      · THE OBSERVER-EFFECT NOTE FROM CAPSULE 2 IS NOW LOAD-BEARING, not a curiosity: under the
        naive design, probing puts us in other people's logs, which literally means the act of
        measuring our footprint enlarges it.
  - ⚑ MARKER DESIGN CHANGES TOO -- A REAL PRECISION/QUIETNESS TRADE-OFF. Capsule 1 wanted maximal
    uniqueness (zero natural collisions). But maximally unique is also maximally identifying, and
    under the local-index architecture we no longer need searchability-by-a-service, only
    distinguishability-in-a-dataset-we-hold. That relaxes the requirement: a marker can be an
    INNOCUOUS-LOOKING but rare construction -- an unusual word pair, a distinctive-but-natural
    phrasing -- recognizable given the private registry and unremarkable without it. Cost: lower
    precision, so hits need adjudication. Benefit: the marker does not advertise itself as a
    marker, it survives a reader's "what is this weird string" instinct (and our own gitleaks
    gate), and it cannot be lifted from the public repo and forged at scale. ⚑ This also REDUCES
    the embedding-pollution hazard from capsule 1, since natural-looking prose with no shared
    high-entropy prefix is far closer to ordinary corpus text than a random token is.

parked:
  - decision: unique-and-obvious markers vs innocuous-and-rare ones (the precision/quietness fork).
    default: INNOCUOUS-AND-RARE, per the reasoning above -- it is the only option compatible with a
    public repo, a private registry, and an un-poisoned signal, and it costs only adjudication.
    re_entry: the design note; the marker-shape decision is the one thing the urgent planting half
    cannot proceed without, so this fork blocks that half.
  - decision: which bulk datasets are in scope for the first pass, and their storage cost.
    default: Software Heritage first (smallest, most directly about our repo, and it doubles as the
    authority-record redundancy from capsule 1), then Common Crawl's index. GH Archive last.
    re_entry: the design note.

open_questions:
  - Is downloading a bulk index within the daemon's resource budget at all, or does this become an
    owner-run offline task like the purge/deploy pattern? Common Crawl's index is very large; the
    honest answer may be that the probe is a periodic MANUAL sweep, not a resident agent -- which
    would be a smaller, quieter, and more defensible thing than the "agent" framing suggests.
  - If markers are innocuous-looking, how does a future us distinguish a genuine diffusion hit from
    a natural-language coincidence? The registry must record an expected-collision-rate per marker,
    or adjudication has no baseline.
  - Does the design note itself need to omit anything? Current answer: no -- design public, values
    private is sufficient, and a note that hides its own mechanism would be unreviewable, which is
    a worse failure for this project than being read by an adversary.

next_steps:
  - The design note absorbs all three capsules. Its architecture section is now OFFLINE-INDEX-SWEEP,
    not API-fan-out; tier (2) is recorded as REJECTED with its reasoning; the registry is private.
  - The urgent planting half is now BLOCKED on one decision only: the marker shape (see parked).
    That fork is worth resolving early precisely because planting is the time-critical half.

references:
  - docs/brainstorms/public-diffusion-markers.md    # capsules 1-2, both amended by this one
  - .gitignore:13                                   # the corpus is outside the public repo -- the registry's home
  - CONSTITUTION.md                                 # NN-1 zero egress · NN-2 · NN-4 powerless code · NN-11
  - docs/findings/finding-0077.md                   # embedding pollution, reduced by the innocuous-marker choice
```
