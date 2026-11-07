---
type: design-note
id: dn-ingress-language
track: query-language
status: draft                  # provenance description, never a gate; the owner's merge is ratification
implementation: built-wired    # DS-0 to DS-7 built 2026-11-05 (§4); the audits' findings and their fixes in §8; the Ambassador's inbox moved onto the ingress 2026-11-05 (§E13)
created: 2026-11-05
updated: 2026-11-05
links:
  - docs/brainstorms/ingress.md                          # THE WARRANT: the seeds and the correction, as requirements
  - docs/design-notes/dn-ingress.md                   # the first form: its ingress (D3), key-last landing, ACID answer (D5), laws (D9) and findings (§9) stand
  - docs/design-notes/dn-query-sentence-algebra.md        # the read half: sorts, QSA-5 admissibility
  - docs/design-notes/capability-scope-algebra.md         # RATIFIED: the write bit W_Σ on the strata
  - docs/design-notes/ingest-identity-and-amendment.md    # RATIFIED: content addressing, identity, versions
  - docs/design-notes/vector-membership-store.md          # the shared plane the landing writes
  - formal/Palace/Script.lean                             # the laws of this note (Script/Defs.lean the model; PalaceTest/Script.lean the attacks)
supersedes: dn-ingress D1 (the operation as a sum of source kinds), D2 (the command table), D7, D8 (in part)
superseded_by: null
warrant: docs/brainstorms/ingress.md
---

Called the door until 2026-11-05.

# The ingress, second form: a generic language, and ingestion as its scripts

> Composed by Claude Opus 5.5 on 2026-11-05 from the correction of the same day (the
> warrant's second list). The first form gave the language one command word per
> ingestion path (`do sync vault`, `do capture …`, `do ingest doc …`), each wired to the code that
> already landed that path. The correction asked for the opposite: a language that knows no path,
> in which every path is written, as a general-purpose language does not know which file a
> program will create but gives it the means to write one. Agent-drafted, filed `draft` on
> `build/ingest-door`; the owner's merge is ratification. Grades as in dn-ingress: `[THEOREM]`
> names its Lean declaration, `[ESTABLISHED]` a ratified note, `[DERIVED]` is argued here,
> `[INFERENCE]` is a design call with a named falsifier. Code claims were read at `ba6a36a`.

## 1. Purpose and scope

### 1.1 What this note decides

The language gains a generic write half: values, a dozen reading functions, three effects
(`store`, `retire`, `link`), one way to start a job the palace declares (`run`), and `let`,
`for` and `if`. Its grammar has no word for a vault, a dialogue, a note, a turn, a capture, a doc
or a dream. What Python's operating system supplies, the palace supplies: the sources a script
may open, the places it may write (the strata), who may do either, and the label every stored
row carries. Every ingestion path of today becomes a script in the repository (`ingress/`), spoken
through the ingress: the vault sync, one note, the dialogue sync, a capture, the curated docs, a
link, and the jobs.

The first form's ingress stands: a surface writes a request into its role's spool, the daemon is
the one writer, a receipt comes back (dn-ingress D3). So do the landing order with the key
last (D1's), the answer on ACID (D5), the laws (D9) and the findings (§9). Its command table
(D2), its per-command landers (D7) and its per-command refusals (D8, in part) go: each becomes a
script, a line of the palace's table, or a general rule of the writer.

### 1.2 Out of scope

- The read half: unchanged. A script may call it (`query`, §E2).
- The stores' internals, the chunker, the embedder, the plane's reconciliation: unchanged; the
  writer calls them as the first form's landers did.
- The owner's operations (purge, re-key, reset, re-embed): not effects, unrepresentable, as in
  the first form (dn-ingress §3.8).
- The jobs' internals (dream, the relation pass, curate, the code and chat lanes, the code
  sensor): a script starts them by name (`run`). They are model and parser pipelines, not
  storage; writing them as scripts is later work, if ever.
- Recursion: none. Functions are closures that never see their own name (§E11), so a script
  is total (§E1).

### 1.3 What is proved, what is cited, what is open

Proved in `formal/Palace/Script.lean` on the model of `Script/Defs.lean` (content with a label
and an origin; expressions as items, projections and constructions; the writer's checks R2 to R8
as a predicate on a store and a state; plans landed effect by effect; a store as the first form's
command), with seven attacks and eight controls (`PalaceTest/Script.lean`, seeds 273 to 287):
ING-13 to ING-18 of §E9, and the first form's ING-11 and ING-12 for every plan through ING-16.
They are the ledger's family XII beside the first form's (`docs/LAWS.md`, `formal/Spec/Script.lean`).
Cited: QSA-5 (admissibility is clause-wise), the kernel's `STRATUM_CLASSES`, CLK-2. Open (§7):
the Ambassador's places and namespaces, an operator's computed content, jobs as scripts. The
Ambassador's inbox (§E13) needs no law of its own: ING-13 and ING-14 cover its source as they are
stated, and its controls are seeds 291 to 293. ING-15 was restated on 2026-11-05 for the
retire-only prefixes (R3), with seeds 288 to 290.

### 1.4 The bar

**Correctness**: the laws first, and the firewall structural: a script cannot name, compare or
raise a label, and authored bytes land only where they were written. **Security**: labels from
the palace's table, namespaces per role, identities that move only with their bytes, bounds on
every evaluation. **Efficiency**: the first form's landing unchanged (the UNCHANGED guard,
embedding the one serial stage). **Verifiability**: a plan is a value, so what a script would
land can be shown before it lands; receipts per effect; every rewritten path is checked against
the first form's lander on the same fixtures before that lander goes. **Flexibility**: a new path
is a script, a new source a line in the table, and neither is a change to the language.

## 2. The analogy, made exact

The warrant's frame: an operating system manages hardware resources and security, the mind palace
manages data and its relationships; both are generic but powerful systems that put an
abstraction layer between a program and what it touches. Line by line:

| an operating system | the mind palace |
|---|---|
| manages hardware: the processor, memory, disks, devices | manages data and its relationships: the stores, the plane, the graph, the version chains |
| programs run as processes, scheduled by the kernel | scripts and jobs run as requests, scheduled by the queue, landed by the one writer |
| system calls: `open`, `read`, `write` | the language's reads and effects: `source`, `files`, `store`, `retire`, `link`, `run` |
| a file system: paths and mounts | places (the strata) and sources (declared locations) |
| users, groups, permissions | roles, grants with the write bit, namespaces |
| a file's owner is set by the system, never by the program | a row's label is set by the palace, never by the script |
| isolation: no process forges another's identity | the laws: authored bytes land only where they were written, identities move only with their bytes |
| `example.py`, which Python never heard of | `ingress/sync_dialogue.palace`, which the language never heard of |

Three layers, then, and only the middle one holds domain words:

1. **The language** (`core/sentence/`): the grammar, the checker, the evaluator. Generic.
2. **The palace's table** (`core/ingest/table.py`, its readers and its writer beside it): the
   sources, the places, the roles, the jobs. Domain
   words live here as data: "the vault is a directory of markdown, labelled authored-solo,
   readable by these roles".
3. **The scripts** (`ingress/*.palace`): the applications.

## 3. Decisions

### E1 — Values, expressions, statements; total by construction

**Values.** `none`, booleans, integers, strings, lists, records; **content**, bytes with a label
and an origin (§E3); **handles**, opened sources (§E2); **entries**, a place's stored rows
(`path`, `identity`, `digest`, `title`, `active`). Records come from readers and are read-only.

**Expressions.** Literals (strings, integers, `true`, `false`, `none`), names, `e.f` and `e[k]`
(a record's field, a list's element; a missing field or key is `none`, and a field of `none` is
`none`), `s[a:b]` on strings, list literals, comprehensions `[e for x in xs if c]`, calls of the
built-in functions of §E2, `+` on strings, integers and lists, `==`, `!=`, `<`, `<=`, `in`,
`not in`, `and`, `or`, `not`.

**Statements.** `param name [= literal], …` (a library script's arguments), `let name = e`,
`for x in e { … }`, `if e { … } else { … }`, `fn name(x, …) { … }` and `return e` (§E11),
`call name(k: v, …)` (a library script, §E11), and the effects of §E5. Statements end at a
newline or `;`; blocks are braced, so a script fits on one line of a query box.

**Totality.** No recursion and no `while`: a function is a closure that cannot name itself
(§E11), and every loop ranges over a finite list.
Evaluation therefore terminates, and its bounds are precedents in the ledger
(`docs/query/precedents.md`): the items a script may read, the bytes, the effects a plan may
hold, a string's length. `[DERIVED — structural recursion on a finite syntax tree, every loop
over a finite list]`

### E2 — Sources: handles the palace declares

A **source** is a line of the palace's table: a name; a location (a directory or a file); a
format (`markdown`, `json`, `text`); for a directory, a scope (a pattern and excluded
directories); for a structured file, an item rule (which records are items, the template of an
item's path); a label rule (one class, or a class for each value of a named field, with a
default); the roles that may open it; an optional refresh (an edge process the runtime runs before
the first read, as the dialogue sync runs its readers); and an optional cursor (a field whose
newest value is recorded once a plan that read the source has landed).

The reading functions are these and no others:

| function | value |
|---|---|
| `source(name)` | a handle; a role not among the source's readers is refused at compile time |
| `files(h)` | a directory's items, in scope, as the disk lists them |
| `file(h, path)` | one item, refused when out of scope |
| `exists(h, path)` | whether the source still has the item |
| `items(h)` | a structured file's items |
| `stored(place, under: x)` | the place's entries whose paths lie under a handle's root or a prefix |
| `entry(place, name)` | the entry a path or a title names; refused when none or two do |
| `query(sentence)` | the hits of a read sentence, evaluated under the speaker's grant |
| `me` | the role speaking |
| `digest(x)`, `len(x)`, `str(x)` | the obvious |
| `paths(xs)` | the list of the items' or entries' paths |
| `unique_by(xs, f)` | a record from each value of field `f` to the one element that has it; a value two elements share is dropped |
| `first(x, …)` | the first argument that is not `none` |

A source's scope is one predicate, applied by `files` and `file` alike: a path in another case
than the disk's, or under an excluded directory in any case, is not an item (the third review's
finding 3 becomes a property of the source, not a check each script must remember). An item of
a markdown source is a record: `path` (as the stores name it), `content`, `digest`, `title`,
`properties`, `tags`, `links`. An item of a structured source is its record, with its content
field and its path from the item rule. `[INFERENCE — falsifier: a path of today that needs a
reading function not in this list]`

A structured source whose rule may give a label other than the observed one, a dialogue reader's
handoff or the inbox's record (§E13), is read only as the daemon trusts it (`core/ingest/files.py`):
its directory and its file the daemon's account's, writable by no other account, the file read
through a descriptor that follows no link, of one link, under the handoff cap. Otherwise an account
that may write the handoff directory (on this machine, the `palace` group's) could plant a turn
that the rule labels as the owner's and that `sync_dialogue` lands as authored dialogue (the inbox
review's finding 2, 2026-11-06). The edge readers write their handoff `0600` in a directory made
`0700` (`edge/private_file.py`), so what they write is read whatever the umask.

### E3 — Labels are the palace's

The label of content is decided by the palace and carried by the value; the language has no
expression for it.

1. An item carries its source's label (or the one its field selects) and its **origin**: the
   source and the item's path.
2. An item's **content** keeps both, through a field, an element, iteration, a reader's
   parsing: it is the item's own bytes. A string read off an item (its title, its digest,
   `n.properties.id`) keeps the item's origin, so a store can show an identity is the item's
   own (R6), but it is not the item's bytes: stored, it is composed (rule 3). The audits of
   2026-11-05 found the first wording let `store n.digest` replace the owner's note with its
   hash, labelled authored (§8).
3. Any other content is **observed** and has no origin: a literal, a parameter, a
   concatenation, a slice, `str(…)`, a string read off an item, a value built from several.
4. No expression yields, compares or takes a label, and no operation raises one: a hit of a
   nested sentence carries no provenance, and `str` of a function or a sentence is refused.

The second rule is what keeps the owner's turns the owner's: `t.content` of a dialogue item is
the item's own bytes, labelled by the reader from the role the edge reader recorded. The third is
what keeps a script from laundering: any text a script composes is observed, whoever runs it.
`[THEOREM — ING-13, Script.lean::label_eval, origin_eval]`

### E4 — Places: the strata, their classes, their writers

A **place** is a stratum, named by a string literal; a computed place is refused at compile
time, so admission stays static. The palace's table gives each place: the classes it accepts
(the kernel's `STRATUM_CLASSES`, the one table every reader already uses), whether it keeps
version chains, the action its attestations record, and for each role the path prefixes the role
may write under.

The writer's rules, each general, none about a source:

- **R1, admission** (at compile time): each effect needs the write bit on its place in the
  speaker's grant. A script is admissible iff each of its effect clauses is. `[THEOREM — ING-1
  per effect: QSA-5, Ingress.lean::command_admissible_iff_write]`
- **R2, classes**: a store's label is one its place accepts. Checked at compile time where the
  label is known (a parameter or a literal is observed, so `store text in "mirror_authored"` is
  refused before anything is read), and again at evaluation.
- **R3, namespaces**: a role writes a place only under its prefixes, after the path is
  normalized (no `.`, no `..`, no empty component). A role may also hold prefixes it only
  retires: the first form's stored namespace, `dialogue/door/<role>/`, whose rows keep their
  identities and are never re-keyed (the rename's follow-up, 2026-11-05). A retire there passes R3
  and is still held to R7; a store there is refused. ING-15 states both halves.
- **R4, origin**: authored content lands at its own origin path and nowhere else.
- **R5, fixed labels**: a path's label is fixed at its first store; a store of another label at
  a held path is refused and reported, and the rest of the plan lands. This is the first form's
  dialogue guard (an observed turn never supersedes the owner's) and its link guard (an
  interpreted edge never replaces an authored one), as one rule.
- **R6, identities move only with their bytes**: a path's identity is fixed at its first store
  (re-keying is the owner's, bp-034). For a new path a store may name as its identity the path
  itself, the identity the item it stores declares (the one property its source names, `id::` in
  the vault; a blank one declares nothing), or the identity of an entry that holds the same digest
  and label at a path its source, the content's own, no longer has (a rename). An identity another
  path of the source still holds is refused. Anything else is refused, so no script can graft a
  new path onto another note's chain.
- **R7, retire reconciles**: `retire p` is admitted only in the speaker's namespace, only of a
  row whose label the table lets the role retire (the owner's role every label, the Ambassador
  the observed one), and, when `p` holds content that came from a source, only once the source
  no longer has it. A note that is still in the vault cannot be retired from the mirror by any
  script, and no agent retires the owner's rows, whatever its source no longer shows (an
  archived chat's turns stay).
- **R8, paths belong to their sources**: a path in a source's own space (the vault's root, the
  docs, a dialogue reader's prefix) takes only content with an origin, which R4 then makes that
  source's item at that very path. Without it a role could squat the path of a turn not yet synced
  with composed text, and R5 would then refuse the owner's turn when it came.

### E5 — Effects, the plan, the writer

Evaluation reads and writes nothing. Its value is a **plan**: an ordered list of effects with
their content resolved. The writer lands a plan, effect by effect. It takes no lock of its own:
the daemon runs its jobs one at a time on the supervisor's thread, every request and every
library job lands through this writer, and the Ambassador's inbox is a job of the same queue, so
no two landings interleave.

- `store c [at p] [as i] in P [titled t]`: content `c` at path `p` (by default `c`'s origin
  path) with identity `i` (by default the path) into place `P`, titled `t` (by default the
  item's title, else the path; content under any label but the observed one is titled by its
  item, never by a script, R2). The landing is the first form's, generalized: the raw object, the
  place's index rows (the plane's chunk-level amendment), the version chain if `P` keeps one,
  the attestation (the speaking role, `P`'s action), and the key last. Nothing lands, UNCHANGED,
  when the key names `c`'s digest and the place holds its rows (the third review's finding 2, for
  every place).
- `retire p in P`: the path's rows retired from the plane, then its row inactive (the key,
  last); the raw object kept.
- `link a to b as r`: an edge between two entries, interpreted, in the relation store.
- `run "job" [with k: v, …]`: a job of the palace's table, enqueued as its own kind; its handler
  lands what it lands. Admission needs the write bit on the strata the job declares. A plan starts
  a job once, the job counts against the speaking role's share of the queue (a start past it is
  refused as busy), and a request run again after a crash finds the job it started.

Within one plan, the effects on distinct paths commute and the effects on one path keep the
plan's order, so the first form's laws apply to every plan: each store is one of the model's
commands with its key last (ING-7), a plan is a batch (ING-3, ING-10), a crash anywhere in it
converges when the plan runs again (ING-11), and a reader that trusts the key sees each store
whole or not at all (ING-12). `[THEOREM — ING-16, Script.lean::plan_converges]`

The receipt names each effect's outcome: landed, unchanged, retired, linked, queued, or refused
with the rule that refused it, with digests and attestation ids. A refusal at evaluation (R2 to
R7) refuses that effect and lands the rest; a refusal at compile time (R1, R2 where known, an
unknown source or place) refuses the request.

### E6 — The request: `do`

`do` stays the one reserved word, and takes a script: `do name(k: v, …)` calls a library
script (`ingress/name.palace`) with its parameters; `do { … }` is a script inline. A request is
spooled, drained, compiled again under the spool's role and landed as in the first form (D3).
The surface parses and checks (R1, R2 where known, the sources' readers), so a speaker hears a
refusal at once; the daemon evaluates, since evaluation reads sources the surface may not.

### E7 — The queue

A request is one job of kind `script`: its payload the request id and the script's digest, its
text in the daemon's staged copy (queue.sqlite still never holds text). A library call with no
arguments that the table maps to one of today's coalescing kinds (`sync_vault` to `vault_sync`,
`sync_dialogue` to `dialogue_sync`) is enqueued as that kind, so it coalesces with the watcher's
and the heartbeat's rows; that kind's handler runs the same script as the daemon's own job, after
the speaker's grant has admitted it. A `run` effect enqueues the job's own kind with its tier.
The table marks the library scripts that run at the interactive tier (`capture`); every other
script runs in the background. The lane quotas stay (dn-ingress §9 item 25).

### E8 — The scripts

The library is the test of generality: every path of the first form, written in the language.
These are the drafts DS-4 lands, with the differential tests of §6 as their falsifiers.

```
# ingress/sync_vault.palace: the owner's notes, verbatim, into the mirror; a vanished note retired.
# A note new to the mirror takes its `id::` as its identity, else the identity of the vanished
# note whose bytes it has (a rename), else its path.
let vault = source("vault")
let notes = files(vault)
let gone = [e for e in stored("mirror_authored", under: vault) if e.path not in paths(notes)]
let moved = unique_by(gone, "digest")
for n in notes {
    store n.content in "mirror_authored" as first(n.properties.id, moved[n.digest].identity)
}
for e in gone { retire e.path in "mirror_authored" }
```

```
# ingress/ingest_note.palace: one note, as the sync would land it.
param path
let vault = source("vault")
let n = file(vault, path)
let gone = [e for e in stored("mirror_authored", under: vault) if not exists(vault, e.path)]
store n.content in "mirror_authored" as first(n.properties.id, unique_by(gone, "digest")[n.digest].identity)
```

```
# ingress/sync_dialogue.palace: the turns an edge reader hands off, each under its chat.
param reader
for t in items(source("dialogue/" + reader)) {
    store t.content in "dialogue" titled "dialogue/" + t.conversation + "/" + t.at + " (" + t.role + ")"
}
```

```
# ingress/capture.palace: a text the speaker relays, observed, under the speaker's own name.
param text, conversation = "captures"
store text in "observed" at "dialogue/ingress/" + me + "/" + conversation + "/" + digest(text)[0:16]
```

```
# ingress/sync_docs.palace: the system's own prose, curated.
for d in files(source("docs")) { store d.content in "curated" }
```

```
# ingress/ingest_doc.palace
param path
store file(source("docs"), path).content in "curated"
```

```
# ingress/link.palace: a relation the speaker proposes between two notes, interpreted.
param a, b, relation
link entry("mirror_authored", a) to entry("mirror_authored", b) as relation
```

```
# ingress/dream.palace, ingress/curate.palace, ingress/relate.palace, ingress/sync_code.palace, ingress/sync_chat.palace, ingress/observe_code.palace
run "dream"
run "curate"
param pairs = 24; run "relate" with pairs: pairs
run "code_sync"
run "chat_sync"
run "code_observe"
```

What moved where, from the first form's landers: the vault's scope and the case rule are the
vault source's scope; the dialogue's role-to-class rule is the dialogue source's label rule; its
path template and cursor (the heartbeat's `.synced` mark) are its item rule and cursor; the
capture's namespace is R3 with the Ambassador's prefix; the turn guard and the link guard are
R5; the rename carry-forward is the script's, made safe by R6; the reconciling rescan is the
script's, made safe by R7; the curated allow-list is the docs source's scope; the relation names
and their weights are the relation store's line in the table.

### E10 — Budgets: work as gas

The warrant's budget seed, from the bounds above: a sentence costs work, as an Ethereum transaction
costs gas, so the interpreter must know what a sentence costs and the compiler must make it cost
little. The caps of §E1 become one **budget**, in one unit of work, priced per operation:

- **Prices are measured, not assumed.** A unit is calibrated against the operations it prices on
  fixtures (reading a kilobyte of a source, an item's parse, a list element, an effect, an
  embedded chunk), and the price table is a precedent in the ledger beside the bounds it
  replaces. Measured 2026-11-05 (`eval/ingress_gas.py`, `docs/query/precedents.md`): one unit is
  one step, 0.30 µs; an item costs 270, a KiB 75, an entry 22, an effect 10,000 (the writer's
  check of a store, mostly the plane's lookup), a write 140,000 (a store that lands, its embeds
  apart), an embedded chunk 360,000. A request that lands is its embeds and its writes; the
  evaluator's own work is under one percent of a first sync.
- **A request carries a budget**: its role's, from the palace's table. Not built: a speaker
  asking for less, and a bound computed from the script's shape before it runs. A loop over a
  source is bounded by the source's size, which the surface does not read (it runs under the
  speaker's account, which need not open the source), so the shape alone bounds only a script
  that reads no source; the meter is the bound that holds for every script.
- **The evaluator meters.** Every operation charges as it runs, and by what it touches: a
  source's listing before its first item, its items each as it is read (so a read stops at the
  item that ran the budget out), a place's entries once an evaluation and each lookup after,
  `+` by what it builds, `in` by what it scans, a comparison by what it compares, a nested
  sentence by its length (capped at 32 KiB, its captures in place), a store by the KiB it hands
  the writer. A request that runs out stops, and since evaluation writes nothing, it lands
  nothing. No request a role speaks runs an edge process: a structured source is refreshed only
  by the daemon's own sync and the owner's CLI, so an edge reader's time is never a request's. Ethereum must revert the state an
  out-of-gas transaction touched; here there is none to revert. `[DERIVED — §E5: evaluation has
  no effects]`
- **The writer prices the plan before paying for it.** A plan's writes are its stores the
  UNCHANGED check would not skip and its other effects; its embeds are its distinct new atoms
  (ING-5), counted against the plane before the embedder is called. Both are charged before the
  first effect lands, so a plan whose landing would overrun its budget is refused before
  anything is written.
- **The compiler's side.** A cost is what lets the planner choose among equivalent forms: the read
  half's rewrites (masks pushed to the leaves, `top k` last) are equivalences, and a priced plan
  picks the cheaper. Pricing the read verbs in the same unit (`near` per atom compared, `diffuse`
  per edge per iteration, `walk` per product state, the walk budget being such a price already)
  is the follow-up that makes one budget cover a whole sentence, read and write.

The receipt reports the work charged. `[INFERENCE — falsifier: a request whose measured work
exceeds its charge by more than the calibration's error, or a refused request that would have
landed within its budget]`

### E11 — Nesting and scope

The warrant's direction: nested sentences, with closure and code scoping.

- **A read sentence nests in a script** as a value: `` `top 5 near $topic within $region` ``, in
  backquotes, which no sentence uses. It is compiled under the speaker's grant like any sentence
  (its own admission, QSA-5) and its value is its hits, records whose strings are observed (a hit
  is the palace's account of a row, not the row's bytes). `$name` captures a name of the enclosing
  scope; a captured value enters the sentence as a quoted literal, never as syntax, so no value
  can inject a word. The sentence is parsed when the script is checked, with its captures as
  placeholders, so a malformed one is refused at the surface, and so is a request in backquotes:
  a nested sentence reads, and a request does not nest.
- **Blocks scope lexically.** A `let` binds until the end of its block; an inner block sees the
  outer names and may shadow them; nothing leaks out of a block.
- **Functions are closures.** `fn name(x, y) { … return e }` binds a function that captures the
  scope as it stands where it is defined, by value: its body sees the names bound before it and
  never its own name, nor any name bound after it, so no function calls itself, directly or
  through another. A function may hold effects; a call adds them to the plan.
- **Scripts call scripts.** `call name(k: v)` runs a library script in a scope of its own (it
  sees its parameters, not the caller's names) under the same role and budget, and adds its plan
  to the caller's; a cycle of calls is refused.
- **Still total.** Without recursion, a well-typed script's evaluation ends (the simply typed
  calculus is strongly normalizing); the meter of §E10 bounds it in any case.
  `[ESTABLISHED — strong normalization of the simply typed lambda calculus; DERIVED for this
  language: no recursion, lists finite, the meter]`

### E12 — An interpreter with a checking pass, and a type system for the labels

The warrant's direction: real compiler tools, a consistent and secured type system, and the
language interpreted rather than compiled. It is interpreted: a generated parser reads a script,
a checking pass types and admits it, and a tree-walking evaluator runs it under the meter into
the plan the writer lands. Nothing is compiled to code; the checking pass is a type checker, as
an interpreted language may have one.

- **The front end is generated.** The grammar is one file, `core/sentence/script.lark`, read by
  Lark (LALR(1), the yacc family for Python), with a post-lexer that makes a newline a separator
  in a block and space inside brackets. The file is the language's single definition: the parser,
  its error messages and its tests come from it, and the grammar can be fuzzed from it.
- **The middle is a checking pass over the parsed tree.** It resolves every name to its binding
  and every closure to what it captures, types each expression, and checks admission (R1),
  labels (R2 where the set is known), the scripts a request calls and the arguments they take,
  and each nested sentence's syntax, with its captures as placeholders. A function is checked at
  each call site with the types it is called with, which is sound because nothing recurses; a
  body checked once with some types is not checked again with the same ones, and the pass is
  bounded (200,000 nodes), so no script costs the surface, the drain or the handler more than a
  bounded check (the audit's finding: checked afresh at each call, a function calling the one
  before it twice doubled the check's cost per line). Evaluation is the last pass and yields the
  plan. (MLIR's lesson, a tree lowered by passes that each check one thing, is the shape; the
  checker is one pass today, and the static cost bound of §E10 is not built.)
- **No machine back end.** A script's cost is reading sources and embedding, not instructions;
  generating code through LLVM would buy nothing measurable and add a toolchain to trust. Where a
  compiled back end would pay is the read half's tensor work (`near`'s similarities, `diffuse`'s
  walk sums), through XLA (MLIR underneath) if a measurement shows the time is there.
  `[INFERENCE — falsifier: a profile of a script whose time is in the evaluator]`
- **The types.** `int`, `bool`, `none`, `str⟨L⟩`, `content⟨L⟩`, `list⟨T⟩`, the records a source's
  items and a place's entries are, `source`, functions `fn(T…) → T`, where `L` is a set of labels.
  Inference is monomorphic unification, and a unification of two label sets is their union, so
  the inferred set only grows. The rules are the label rules of §E3: an item's fields carry its
  source's labels, a projection keeps its operand's, anything composed is `{observed}`.
  **Soundness**: a value's label at run time is in its type's set. `[THEOREM — ING-18, Script.lean]` Then R2 is
  decided at compile time wherever the set is known, and the writer's run-time check is the
  second wall, not the only one.

### E13 The Ambassador's inbox, a source

The first form captured the owner's message inside the Ambassador's turn
(`DialogueCapture.capture`): authored dialogue at a path keyed by the clock, so a re-run stored it
again, and the label was the inbox's code, not a source's. It moves onto the ingress here: the
owner's messages are the items of a source, the source labels them, a library script stores
them, and the one writer lands the plan.

**Where the messages come from.** The owner reaches the Ambassador through the interface handoff
(`cfg.interface.handoff_dir`, `data/handoff/` on this machine). The gateway, or `mind-palace
talk` in its own process, writes `requests/<id>.json` with the text, the conversation and the
time, `<id>` the gateway's 32 hex digits. The core inbox (`CoreInbox.process_once`, run by the
daemon's `ambassador` job or by `talk`'s runtime) asks the Ambassador for a reply, writes
`responses/<id>.json` and removes the request. The request is the only copy of the owner's words
on disk and the inbox consumes it, so before it writes the response the inbox writes what it
keeps of the exchange to its own record, `data/inbox/<id>.json`: the text as the request file
holds it and the reply it is about to send, each in a field of its own. The directory is the
daemon's account's alone (`0700`, each record `0600`), and only the inbox's code writes it. The
Ambassador says whether an exchange is kept, by the first form's rule (a recall, a task or a
capture is kept; a status, an explanation or the dreams are not), and never what is in it. A
request whose file was written by an account other than the inbox's own or the handoff
directory's owner (the edge's, `plane-principals` §3.1) is answered and not kept: where the
agents run under an account of their own, that keeps an agent's process from posing as the owner,
and where they share the daemon's account, as on this machine today, the filesystem cannot tell
them apart, as it cannot for any store. A request whose id is not 32 hex digits and its file's
name is removed unanswered, since the id names the response and the record. A record that cannot
be written is said in the reply, never lost in silence.

**The source.** `inbox`, a line of the palace's table: a directory of records (the kind
`records`), each a JSON document read through a descriptor that follows no link, a regular file of
one link that the daemon's account owns and no other account may write, in a directory of which
the same holds. A record that is not, or that is not of the inbox's shape, is refused with the
source, so no account but the daemon's adds one. The item rule makes two items of a record: the
text, labelled `authored-dialogue`, and the reply, labelled `observed`. The label follows from the
field the inbox wrote each text into, in the table's code. The record has no field a model writes
but the reply, and the reply is observed whatever it says; no script names a label (ING-13). The
replies land beside the owner's words, where the first form kept the owner's words alone;
`[ambassador] keep_replies = false` turns that off, and the rule then makes the text's item alone.

**Paths and identities.** The text's path is `dialogue/inbox/<conversation>/<id>/owner` and the
reply's `dialogue/inbox/<conversation>/<id>/ambassador`, where `<conversation>` is the request's
when it is a plain name (letters, digits, `.`, `_` and `-`, at most 64, not starting with `.`)
and otherwise `c-` and sixteen hex digits of its digest, so no conversation adds a component or
leaves the space. Each is its path's own identity, and the gateway mints the id once. The space
`dialogue/inbox/` is the source's (R8). The landing is idempotent: the same request handled twice
(a crash before the inbox removed it) writes the same record, whose text lands UNCHANGED and
whose reply, if the second answer differs, replaces the observed row at its path (R5 keeps the
label). The writer lands each store with its key last, so a crash between any two steps converges
when the job runs again (ING-7, ING-16). Once a plan has stored both items of a record, landed or
unchanged, the record is removed: the raw store holds the bytes, so a purge of them leaves no copy
behind, and the next run reads only what is pending. `[DERIVED — ING-7, ING-16; the tests in
tests/integration/test_inbox_capture.py]`

**The role and the job.** `ingress/capture_inbox.palace` stores each item of the source in
`dialogue`, at its own path. It runs under a role of its own, `inbox`, which the daemon's inbox job
speaks after each drain and `talk`'s runtime after each message. No spool belongs to the role, so
no surface can speak it. It opens only the `inbox` source, writes only under `dialogue/inbox/` in
`dialogue`, retires nothing, and speaks under the Ambassador's grant, the least the ingress gives.
Its budget is the operator's, since what it reads is the daemon's own record of what the owner
typed. The daemon is the one writer. Beside a live daemon (the run ledger's newest run active and
its process alive, as the launcher's `_refuse_if_live` reads it), `talk` keeps the exchange in the
record and lands nothing: the daemon's watcher of the record's directory enqueues the coalescing
`inbox_capture` job, as its catch-up does at start when records wait, and the job lands them
through the daemon's writer. With no daemon live, `talk` lands in its own process, the daemon's
stand-in (the inbox review's finding 3, 2026-11-06).

**What the Ambassador can and cannot do through it.** It decides which exchanges are kept, and it
writes the reply. It cannot open the `inbox` source (it is not among the readers, so a request
that names the source is refused when it is checked), cannot store or retire under
`dialogue/inbox/` (not its namespace, R3; composed text there is a squat, R8), and cannot land its
own text as the owner's anywhere: what it composes is observed (ING-13), and an authored row is an
item a source yields, at the item's own path (ING-14). At its own prefix in `dialogue`,
`dialogue/ingress/ambassador/`, in a place that takes authored dialogue, what it stores is
observed. The bright line holds: no model, the Ambassador included, can mint the owner's authored
dialogue, by any script, inline or from the library, and the authored rows under
`dialogue/inbox/` are the owner's messages as the gateway handed them.

**What is proved.** ING-13 and ING-14 cover the source as they are stated. An inbox item is an
item a source yields, with the label its rule gives (the model's `Item`, its label one that
`yields` admits), so after any plan of any role every active authored row is the row held before
or the bytes of such an item at the item's own path (`firewall_plan`). What the model takes as
given is the rule itself, that the source labels authored only the owner's messages. The table and
the inbox hold it in code, and the tests fail when it is mutated. The attacks on the inbox's shadow
check the composition and its two premises (seeds 291 to 293): every authored row a store lands is
the owner's message at its own path, a writer that takes the label a script claims lands the
Ambassador's text as the owner's at its own prefix, and a rule that labels the reply authored
lands the reply as the owner's. `[THEOREM — ING-13, ING-14: Script.lean::label_eval,
firewall_plan; the controls in PalaceTest/Script.lean]`

**What stays of the first form.** `DialogueCapture.capture` is gone. `capture_turn` stays, and no
production path calls it: it is the differential oracle for `sync_dialogue` (DS-5) and ING-7's
falsifier for a turn, and the plane's tests land turns with it. The first form's inbox rows,
`dialogue/<conversation>/<time>-<digest>`, stay as they are: no source owns their paths, and no
role's namespace but the operator's covers them.

### E9 — The laws

| law | statement | formal |
|---|---|---|
| ING-13 | a value's label is its item's under projections and observed otherwise; its origin is its item's path under projections and none otherwise; its bytes are its item's under its views; no expression raises a label | `Script.lean::label_eval`, `origin_eval`, `bytes_eval`, `root_of_label_ne` |
| ING-14 | the firewall: an admitted store whose label is not the observed one lands an item a source yields, under views, at the item's own path, with the item's label; over a plan, every active row not observed is the row held before or such a store's | `Script.lean::firewall_store`, `firewall_plan` |
| ING-15 | confinement: a plan changes a path only through an effect on it the writer admitted, a store in the role's write namespace for its place and a retire in that namespace or the role's retire-only one; a path a plan leaves holding an active row it changed was stored there, so a retire-only prefix takes no store (the write bit is ING-1's, at compile time) | `Script.lean::confined`, `confined_store` |
| ING-16 | every admitted plan is a batch of the first form's commands with the key last, so ING-7, ING-10, ING-11 and ING-12 hold of it | `Script.lean::plan_converges`, `plan_sound` |
| ING-17 | a held path keeps its label and its identity under every admitted store; a new path's identity is its own, one read off the very item stored, or one held at a path its source no longer has, with the same bytes; a path in a source's space takes only that source's item at that path; a retire of sourced content is of a path the source no longer has | `Script.lean::label_fixed`, `identity_moves_with_bytes`, `owned_by_source`, `retire_reconciles` |
| ING-18 | a well-typed value's label at run time is in its type's label set, so R2 is decided at compile time wherever the set is known | `Script.lean::label_typed` |

The first form's ING-1 holds effect by effect (R1). ING-2 to ING-12 are statements about
commands, which every store is. `[THEOREM — Script.lean; the ledger's family XII, each statement
judged by the comparator against formal/Spec/Script.lean]`

ING-15 was first stated with one namespace for both effects. The rename's follow-up gave a role
prefixes it only retires (R3), and `Table.may_retire` admits a retire there that `Table.may_write`
refuses, so the statement read with the model's namespace as the write prefixes no longer held of
the code: the Ambassador retiring its legacy row changes a path outside them. Read as the union it
held, but it then no longer said that a store stays in the write prefixes, which the follow-up
relies on (the Ambassador never writes a new row there). The model's namespace is parametric data
and now has its two parts, `ns` written and `rns` only retired; `confined` says which part each
effect needs, and `confined_store` that a retire-only prefix takes no store. A control (seed 288)
refutes the first statement on a writer with a retire-only prefix. ING-17 needed no change: R7's
reconciliation does not depend on the namespace, and `retire_reconciles` holds as stated of a
retire in either part.

## 4. Consequences — the order of work

- **DS-0, this note.** The warrant updated with the correction, as requirements.
- **DS-1, the laws.** `formal/Palace/Script/Defs.lean`: values with labels and origins, the
  expression forms that matter to labels (an item, a projection, a construction), the writer's
  checks R2 to R7 as a predicate on a store and a state, plans compiled to the first form's
  commands. `formal/Palace/Script.lean`: ING-13 to ING-18 (ING-18 with §E12), with attacks and
  controls in `formal/PalaceTest/Script.lean` (a laundering construction, a store at another
  path, an identity graft, a retire of a present item).
- **DS-2, the language.** In `core/sentence/`: the script grammar under `do`, the checker (R1, R2
  where known, readers, places and jobs by name, the static bound of §E10), the evaluator,
  metered. The first form's command words, `command_requirement` and `kind_of` go.
- **DS-3, the palace's table and the writer.** `core/ingest/table.py`: the sources (vault, docs,
  the two dialogue readers), the places, the roles and their prefixes, the jobs, the budgets.
  `core/ingest/readers.py`: markdown, json and text, with scopes and label rules.
  `core/ingest/writer.py`: store, retire, link and run with R2 to R8, calling the stores as the
  first form's landers did. The evaluator reads the palace through an interface the daemon
  hands it, so the language imports no store.
- **DS-4, the scripts and the surfaces.** `ingress/*.palace`; the CLI, the MCP aliases, the web
  filter, the watcher's and the heartbeat's jobs speak scripts.
- **DS-5, the differential tests, then the old landers go.** Each script against the first
  form's lander on the same fixtures: the same catalog rows, plane rows, version chains and
  attestations. Then `VaultSync.sync_path`, `DialogueCapture.capture_turn` and `ingest_curated`
  stop being entry points; what still calls them (the CLI's `vault-sync`, the re-embed, the owner's
  scripts) calls the scripts.
- **DS-6, the audits.** Agents, read-only: the language and the writer for security (a
  laundering, a squat, a graft, a traversal, an unbounded evaluation), the formal side against the
  code, and the scripts against the paths they replace.
- **DS-7, the ledger and the pull request.** ING-13 to ING-18 enter `docs/LAWS.md` and
  `formal/Spec/`, as the writer relies on them from its first commit; the README counts; PR #67
  rewritten to this state.

Status, 2026-11-05: DS-0 to DS-7 are built; DS-6's three audits and what was done about each
finding are §8. The thirteen scripts of §E8 are the library
in `ingress/`; `sync_vault`, `sync_dialogue` and `ingest_doc` land what their first-form landers
landed on the same fixtures (`tests/integration/test_ingress_scripts.py`), and the watcher's and the
heartbeat's jobs, the CLI, the MCP aliases and the web filter speak scripts. The first-form
landers stay for what still calls them outside the ingress: `VaultSync` for the owner's id minting
(`scripts/mint_ids.py`) and `ingest_curated` for the offline demo (`scripts/talk.py`). The
Ambassador's inbox, the path this paragraph named next, moved after #66 and #67 merged (§E13): the
inbox keeps each exchange in its own record, the `inbox` source labels the owner's text authored
and the reply observed, and `capture_inbox` lands both under the role `inbox` through the one
writer, in the daemon's `ambassador` job and in `mind-palace talk`'s runtime
(`tests/integration/test_inbox_capture.py`). `DialogueCapture.capture` is gone; `capture_turn`
stays as the oracle and the falsifier §E13 names. Not built: the static cost bound and a
speaker's smaller budget (§E10).

## 5. Wiring & enablement

The same switch as the first form (`[query]`); the same spools and modes (dn-ingress §5). The
scripts are files in the repository, read by the daemon at evaluation; a change to one is a
commit, reviewed like code. The palace's table is code in `core/ingest/table.py`, typed and
tested, built from the configuration's paths (the vault's location, the data directory).

## 6. Risks and falsifiers

- **A path that does not fit.** Falsifier: a path of the first form whose script needs a word
  outside §E1 and §E2. The library of §E8 is the test; DS-4 lands it or names the gap.
- **A rewritten path that lands differently.** Falsifier: the differential tests of DS-5, each
  script against its first-form lander on the same fixtures, comparing the catalog, the plane's
  rows, the version chains and the attestations.
- **Laundering.** Falsifier: a script that stores authored content anywhere but at its origin, or
  stores composed text under an authored label. R2 and R4 refuse it; the attacks of DS-1 and the
  security audit of DS-6 try.
- **Squatting and grafting.** Falsifier: a script that makes the owner's later store fail or
  land under another identity. R3, R5 and R6.
- **Cost.** A script can read a whole source; the bounds of §E1 cap it, and the drain's quotas
  stay. The vault sync reads what the rescan read; no new reads.

## 7. Open questions

- **The Ambassador's places and prefixes.** The first form's §9 item 21 (narrow the Ambassador's
  write plane) is now a line of the table. The draft: the Ambassador writes `observed` and
  `dialogue` under `dialogue/ingress/ambassador/`, `interpreted` through `link`, and may run the two
  syncs; the owner's call. The inbox's capture does not widen it: it runs under the role `inbox`,
  which writes only `dialogue/inbox/` (§E13).
- **An operator's composed text.** Observed, by rule 3 of §E3, even when the owner's own script
  composes it: composing is not writing. The owner's call whether an operator script may promote,
  which today is the owner's re-tag from raw and nothing else.
- **`mind-palace talk` under separate principals.** Beside a live daemon, `talk` leaves its
  record to the daemon's capture (§E13). Where the daemon runs under its own account
  (`plane-principals`), a record `talk` writes is another account's, and the daemon's reader
  refuses it; there `talk` should hand the message to the daemon's inbox as a request instead.
- **Jobs as scripts.** Dream, the relation pass and curate land interpreted content through
  their own handlers; whether a script should express them (a model call as a reading function)
  is left until a use needs it.

## 8. The audits of the second form

Three read-only audits ran on 2026-11-05 at `8d1ea8c`, before the pull request was rewritten: the
security of the language and the writer, the formal side against the code, and the scripts
against the paths they replace. Each finding below is fixed and has a test, except where it says.

1. **A string read off an item stored under the item's label** (HIGH, security and formal). `store
   n.digest in "mirror_authored"` replaced the owner's note with its hash, labelled authored and
   attested; `store t.role` did the same to a turn. A string is composed when stored (§E3, rule
   2), and ING-13's row says so.
2. **A script's title on an authored row** (HIGH, security; MEDIUM, formal). `titled` put composed text in the
   catalog and the plane's rows under the owner's label, which the UNCHANGED check never
   revisits. Content under any label but the observed one is titled by its item; the checker
   refuses `titled` on it, and the writer refuses a store whose title is not its item's (R2). The
   dialogue's titles are the source's rule now.
3. **The checker's cost** (HIGH, security). Checking a function afresh at each call made a
   1.3 KB script cost days. A body is checked once per argument types, the pass is bounded, and a
   request in backquotes is refused when checked, before anything compiles it (§E11, §E12).
4. **Work the meter did not see** (HIGH, security). A nested sentence doubled by its captures,
   `in` over a long list, a catalog scanned per `entry`, `str` of a closure, a source's listing,
   a large content stored many times, an edge reader's run: each is charged by size now, capped,
   refused, or not run for a request (§E10).
5. **The Ambassador could retire the owner's turns** (HIGH, security). An archived chat's turns
   leave the export, so R7 let the Ambassador retire them. A role retires only the labels the
   table gives it (R7).
6. **A job a script starts escaped the quotas** (HIGH, scripts; MEDIUM, security). One request
   queued six hundred dreams. A started job carries its role and counts against the role's bulk
   lane, a plan starts a job once, and a request run again after a crash finds its job (§E5).
7. **Identity grafts** (MEDIUM, security and formal). Any field of an item could name an
   identity, and a held identity moved across labels. Only the declared property names one, an
   identity another path of the source holds is refused, and a held one moves with its label
   within its source (R6). The model's `prop` naming now needs the item's declaration, with a
   control (seed 287), so ING-17 says what the writer does.
8. **The heartbeat's mark** (MEDIUM). Any plan that read a dialogue source moved it. Only a plan
   that stored every item it read moves it now.
9. **A sibling directory as the vault** (MEDIUM). `stored(…, under: source)` matched
   `<vault>-old/`. A root matches as a directory.
10. **One scope for the vault** (MEDIUM). The rescan's listing excluded directories by case and
    followed symlinks out of the vault; the ingress did neither. `iter_vault` now has the ingress's
    scope, so the re-embed and the id minting see what a sync lands. The live vault has no file
    either rule would treat differently (checked, names only).
11. **A blank `id::`** (MEDIUM) forked a chain; it declares nothing now. **An oversized note**
    (MEDIUM) stopped every sync; it is refused alone (R1) and stays as it was.
12. **ING-16 and ING-18 claimed more than their proofs** (MEDIUM, formal). ING-16's row carries
    ING-7's windows (a rename appends whatever the head); a retire writes its key last. ING-18's
    row says what is proved (the model's typing rule) and what the tests check (the checker's
    rules); the reader refuses an item whose label is outside its source's range, and an empty
    label set is no knowledge.
13. **Mutations no cited test caught** (MEDIUM, formal): R6's "still in its source", `normal`,
    the key before the attestation, the checker not descending into `call`. Each has a test now.
    The fifth, entries labelled with their row's label, is now an equivalent mutant: no string's
    label reaches a store.
14. **Lower findings, fixed**: the log's redaction lost step inside backquotes and leaked a value
    with an apostrophe; `normal` let format characters (bidirectional overrides, separators) into
    paths; a check the palace could not make stopped the plan; a receipt said `landed` when every
    effect was refused; the MCP's `relate` spooled what the writer would refuse; `link` takes
    entries only; `entry` finds a digest; `sync_docs` retires a doc gone from the repository; the
    relation pass and the code sensor are requeued after a crash, as in the first form; control
    282 tests the namespace alone.
15. **Left as they are, for the owner.** Attestations of the daemon's own syncs name the role
    `cli` where the first form named the watcher; a turn whose role changes with the same bytes
    is refused (R5) on each sync, reported and harmless; `query`'s price is one embed, its
    floor, not a measurement. The Ambassador's inbox, which still captured through the first
    form's lander, moved onto the ingress the same day (§E13).
