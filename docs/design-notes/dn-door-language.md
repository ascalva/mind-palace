---
type: design-note
id: dn-door-language
track: query-language
status: draft                  # provenance description, never a gate; the owner's merge is ratification
implementation: designing      # DS-0 this note; DS-1 to DS-7 follow (§4)
created: 2026-11-05
updated: 2026-11-05
links:
  - docs/brainstorms/the-door.md                          # THE WARRANT: the owner's seeds and the correction, verbatim
  - docs/design-notes/dn-ingest-door.md                   # the first form: its door (D3), key-last landing, ACID answer (D5), laws (D9) and findings (§9) stand
  - docs/design-notes/dn-query-sentence-algebra.md        # the read half: sorts, QSA-5 admissibility
  - docs/design-notes/capability-scope-algebra.md         # RATIFIED: the write bit W_Σ on the strata
  - docs/design-notes/ingest-identity-and-amendment.md    # RATIFIED: content addressing, identity, versions
  - docs/design-notes/vector-membership-store.md          # the shared plane the landing writes
  - formal/Palace/Script.lean                             # the laws of this note (Script/Defs.lean the model; PalaceTest/Script.lean the attacks)
supersedes: dn-ingest-door D1 (the operation as a sum of source kinds), D2 (the command table), D7, D8 (in part)
superseded_by: null
warrant: docs/brainstorms/the-door.md
---

# The door, second form: a generic language, and ingestion as its scripts

> Composed by Claude Opus 5.5 on 2026-11-05 from the owner's correction of the same day (the
> warrant's last three passages). The first form gave the language one command word per
> ingestion path (`do sync vault`, `do capture …`, `do ingest doc …`), each wired to the code that
> already landed that path. The owner wanted the opposite: a language that knows no path, in which
> every path is written, "like python doesn't know that i want to create a file called
> example.py, but it gives me the tools to write it". Agent-drafted, filed `draft` on
> `build/ingest-door`; the owner's merge is ratification. Grades as in dn-ingest-door: `[THEOREM]`
> names its Lean declaration, `[ESTABLISHED]` a ratified note, `[DERIVED]` is argued here,
> `[INFERENCE]` is a design call with a named falsifier. Code claims were read at `ba6a36a`.

## 1. Purpose and scope

### 1.1 What this note decides

The language gains a generic write half: values, a dozen reading functions, three effects
(`store`, `retire`, `link`), one way to start a job the palace declares (`run`), and `let`,
`for` and `if`. Its grammar has no word for a vault, a dialogue, a note, a turn, a capture, a doc
or a dream. What Python's operating system supplies, the palace supplies: the sources a script
may open, the places it may write (the strata), who may do either, and the label every stored
row carries. Every ingestion path of today becomes a script in the repository (`door/`), spoken
through the door: the vault sync, one note, the dialogue sync, a capture, the curated docs, a
link, and the jobs.

The first form's door stands: a surface writes a request into its role's spool, the daemon is
the one writer, a receipt comes back (dn-ingest-door D3). So do the landing order with the key
last (D1's), the answer on ACID (D5), the laws (D9) and the findings (§9). Its command table
(D2), its per-command landers (D7) and its per-command refusals (D8, in part) go: each becomes a
script, a line of the palace's table, or a general rule of the writer.

### 1.2 Out of scope

- The read half: unchanged. A script may call it (`query`, §E2).
- The stores' internals, the chunker, the embedder, the plane's reconciliation: unchanged; the
  writer calls them as the first form's landers did.
- The owner's operations (purge, re-key, reset, re-embed): not effects, unrepresentable, as in
  the first form (dn-ingest-door §3.8).
- The jobs' internals (dream, the relation pass, curate, the code and chat lanes, the code
  sensor): a script starts them by name (`run`). They are model and parser pipelines, not
  storage; writing them as scripts is later work, if ever.
- User-defined functions and recursion: none. A script is total (§E1).

### 1.3 What is proved, what is cited, what is open

To be filled by DS-1: the label laws (DOR-13 to DOR-17, §E9) over a model of the language's
values and the writer's checks, with the first form's laws (DOR-1 to DOR-12) applying to every
plan. Cited: QSA-5 (admissibility is clause-wise), the kernel's `STRATUM_CLASSES`, CLK-2. Open
(§7): the Ambassador's places and namespaces, an operator's computed content, jobs as scripts.

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

The owner's frame: an operating system manages hardware resources and security, the mind palace
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
| `example.py`, which Python never heard of | `door/sync_dialogue.palace`, which the language never heard of |

Three layers, then, and only the middle one holds domain words:

1. **The language** (`core/sentence/`): the grammar, the checker, the evaluator. Generic.
2. **The palace's table** (`core/door/`): the sources, the places, the roles, the jobs. Domain
   words live here as data: "the vault is a directory of markdown, labelled authored-solo,
   readable by these roles".
3. **The scripts** (`door/*.palace`): the applications.

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
`for x in e { … }`, `if e { … } else { … }`, and the effects of §E5. Statements end at a newline
or `;`; blocks are braced, so a script fits on one line of a query box.

**Totality.** No recursion, no `while`, no user functions; every loop ranges over a finite list.
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

### E3 — Labels are the palace's

The label of content is decided by the palace and carried by the value; the language has no
expression for it.

1. An item carries its source's label (or the one its field selects) and its **origin**: the
   source and the item's path.
2. A **projection** keeps both: a field, an element, iteration, a reader's parsing. A string
   read off an item (`n.properties.id`) is a projection too, and carries the item's origin.
3. Any other content is **observed** and has no origin: a literal, a parameter, a
   concatenation, a slice, `str(…)`, a value built from several.
4. No expression yields, compares or takes a label, and no operation raises one.

The second rule is what keeps the owner's turns the owner's: `t.content` of a dialogue item is
the item's own bytes, labelled by the reader from the role the edge reader recorded. The third is
what keeps a script from laundering: any text a script composes is observed, whoever runs it.
`[THEOREM — DOR-13, Script.lean::label_eval, origin_eval]`

### E4 — Places: the strata, their classes, their writers

A **place** is a stratum, named by a string literal; a computed place is refused at compile
time, so admission stays static. The palace's table gives each place: the classes it accepts
(the kernel's `STRATUM_CLASSES`, the one table every reader already uses), whether it keeps
version chains, the action its attestations record, and for each role the path prefixes the role
may write under.

The writer's rules, each general, none about a source:

- **R1, admission** (at compile time): each effect needs the write bit on its place in the
  speaker's grant. A script is admissible iff each of its effect clauses is. `[THEOREM — DOR-1
  per effect: QSA-5, Door.lean::command_admissible_iff_write]`
- **R2, classes**: a store's label is one its place accepts. Checked at compile time where the
  label is known (a parameter or a literal is observed, so `store text in "mirror_authored"` is
  refused before anything is read), and again at evaluation.
- **R3, namespaces**: a role writes a place only under its prefixes, after the path is
  normalized (no `.`, no `..`, no empty component).
- **R4, origin**: authored content lands at its own origin path and nowhere else.
- **R5, fixed labels**: a path's label is fixed at its first store; a store of another label at
  a held path is refused and reported, and the rest of the plan lands. This is the first form's
  dialogue guard (an observed turn never supersedes the owner's) and its link guard (an
  interpreted edge never replaces an authored one), as one rule.
- **R6, identities move only with their bytes**: a path's identity is fixed at its first store
  (re-keying is the owner's, bp-034). For a new path a store may name as its identity the path
  itself, a string projected from the content it stores (an `id::` property), or the identity of
  an entry that holds the same digest at a path its source no longer has (a rename). Anything
  else is refused, so no script can graft a new path onto another note's chain.
- **R7, retire reconciles**: `retire p` is admitted only when `p`'s source no longer has it, or,
  for content with no source, when `p` lies in the speaker's namespace. A note that is still in
  the vault cannot be retired from the mirror by any script.

### E5 — Effects, the plan, the writer

Evaluation reads and writes nothing. Its value is a **plan**: an ordered list of effects with
their content resolved. The writer lands a plan, effect by effect, under the plane's lock.

- `store c [at p] [as i] in P [titled t]`: content `c` at path `p` (by default `c`'s origin
  path) with identity `i` (by default the path) into place `P`, titled `t` (by default the
  item's title, else the path). The landing is the first form's, generalized: the raw object, the
  place's index rows (the plane's chunk-level amendment), the version chain if `P` keeps one,
  the attestation (the speaking role, `P`'s action), and the key last. Nothing lands, UNCHANGED,
  when the key names `c`'s digest and the place holds its rows (the third review's finding 2, for
  every place).
- `retire p in P`: the path's row inactive and its rows retired; the raw object kept.
- `link a to b as r`: an edge between two entries, interpreted, in the relation store.
- `run "job" [with k: v, …]`: a job of the palace's table, enqueued as its own kind; its handler
  lands what it lands. Admission needs the write bit on the strata the job declares.

Within one plan, the effects on distinct paths commute and the effects on one path keep the
plan's order, so the first form's laws apply to every plan: each store is one of the model's
commands with its key last (DOR-7), a plan is a batch (DOR-3, DOR-10), a crash anywhere in it
converges when the plan runs again (DOR-11), and a reader that trusts the key sees each store
whole or not at all (DOR-12). `[THEOREM — DOR-16, Script.lean::plan_converges]`

The receipt names each effect's outcome: landed, unchanged, retired, linked, queued, or refused
with the rule that refused it, with digests and attestation ids. A refusal at evaluation (R2 to
R7) refuses that effect and lands the rest; a refusal at compile time (R1, R2 where known, an
unknown source or place) refuses the request.

### E6 — The request: `do`

`do` stays the one reserved word, and takes a script: `do name(k: v, …)` calls a library
script (`door/name.palace`) with its parameters; `do { … }` is a script inline. A request is
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
script runs in the background. The lane quotas stay (dn-ingest-door §9 item 25).

### E8 — The scripts

The library is the test of generality: every path of the first form, written in the language.
These are the drafts DS-4 lands, with the differential tests of §6 as their falsifiers.

```
# door/sync_vault.palace: the owner's notes, verbatim, into the mirror; a vanished note retired.
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
# door/ingest_note.palace: one note, as the sync would land it.
param path
let vault = source("vault")
let n = file(vault, path)
let gone = [e for e in stored("mirror_authored", under: vault) if not exists(vault, e.path)]
store n.content in "mirror_authored" as first(n.properties.id, unique_by(gone, "digest")[n.digest].identity)
```

```
# door/sync_dialogue.palace: the turns an edge reader hands off, each under its chat.
param reader
for t in items(source("dialogue/" + reader)) {
    store t.content in "dialogue" titled "dialogue/" + t.conversation + "/" + t.at + " (" + t.role + ")"
}
```

```
# door/capture.palace: a text the speaker relays, observed, under the speaker's own name.
param text, conversation = "captures"
store text in "observed" at "dialogue/door/" + me + "/" + conversation + "/" + digest(text)[0:16]
```

```
# door/sync_docs.palace: the system's own prose, curated.
for d in files(source("docs")) { store d.content in "curated" }
```

```
# door/ingest_doc.palace
param path
store file(source("docs"), path).content in "curated"
```

```
# door/link.palace: a relation the speaker proposes between two notes, interpreted.
param a, b, relation
link entry("mirror_authored", a) to entry("mirror_authored", b) as relation
```

```
# door/dream.palace, door/curate.palace, door/relate.palace, door/sync_code.palace, door/sync_chat.palace, door/observe_code.palace
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

### E9 — The laws

| law | statement | formal |
|---|---|---|
| DOR-13 | a value's label is its item's under projections and observed otherwise; its origin is its item's under projections and none otherwise; no expression raises a label | `Script.lean::label_eval`, `origin_eval` |
| DOR-14 | the firewall: from a state whose authored rows are each an authored item's projection at the item's own path, any plan the writer admits lands a state of which that is still true | `Script.lean::firewall_preserved` |
| DOR-15 | confinement: an admitted plan writes only places its role's grant gives the write bit, and within a place only under the role's prefixes | `Script.lean::confined` |
| DOR-16 | every admitted plan is a batch of the first form's commands with the key last, so DOR-7, DOR-10, DOR-11 and DOR-12 hold of it | `Script.lean::plan_converges`, `plan_sound` |
| DOR-17 | a held path keeps its label and its identity under every admitted store; a new path's identity is its own, its content's, or a vanished path's with the same digest | `Script.lean::label_fixed`, `identity_moves_with_bytes` |

The first form's DOR-1 holds effect by effect (R1). DOR-2 to DOR-12 are statements about
commands, which every store is. `[THEOREM — to be stated and proved in DS-1]`

## 4. Consequences — the order of work

- **DS-0, this note.** The warrant updated with the owner's correction, verbatim.
- **DS-1, the laws.** `formal/Palace/Script/Defs.lean`: values with labels and origins, the
  expression forms that matter to labels (an item, a projection, a construction), the writer's
  checks R2 to R7 as a predicate on a store and a state, plans compiled to the first form's
  commands. `formal/Palace/Script.lean`: DOR-13 to DOR-17, with attacks and controls in
  `formal/PalaceTest/Script.lean` (a laundering construction, a store at another path, an
  identity graft, a retire of a present item).
- **DS-2, the language.** In `core/sentence/`: the script grammar under `do`, the checker (R1, R2
  where known, readers, places and jobs by name), the evaluator with its bounds. The first form's
  command words, `command_requirement` and `kind_of` go.
- **DS-3, the palace's table and the writer.** `core/door/`: the sources (vault, docs, the two
  dialogue readers), the places, the roles and their prefixes, the jobs; the readers (markdown,
  json, text) with scopes and label rules; the writer (store, retire, link, run) with R2 to R7,
  calling the stores as the first form's landers did.
- **DS-4, the scripts and the surfaces.** `door/*.palace`; the CLI, the MCP aliases, the web
  filter, the watcher's and the heartbeat's jobs speak scripts.
- **DS-5, the differential tests, then the old landers go.** Each script against the first
  form's lander on the same fixtures: the same catalog rows, plane rows, version chains and
  attestations. Then `VaultSync.sync_path`, `DialogueCapture.capture_turn` and `ingest_curated`
  stop being entry points; what still calls them (the CLI's `vault-sync`, the re-embed, the owner's
  scripts) calls the scripts.
- **DS-6, the audits.** Agents, read-only: the language and the writer for security (a
  laundering, a squat, a graft, a traversal, an unbounded evaluation), the formal side against the
  code, and the scripts against the paths they replace.
- **DS-7, the ledger and the pull request.** DOR-13 to DOR-17 enter `docs/LAWS.md` and
  `formal/Spec/`, as the writer relies on them from its first commit; the README counts; PR #67
  rewritten to this state.

## 5. Wiring & enablement

The same switch as the first form (`[query]`); the same spools and modes (dn-ingest-door §5). The
scripts are files in the repository, read by the daemon at evaluation; a change to one is a
commit, reviewed like code. The palace's table is code in `core/door/`, typed and tested, built
from the configuration's paths (the vault's location, the data directory).

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
  `dialogue` under `dialogue/door/ambassador/`, `interpreted` through `link`, and may run the two
  syncs; the owner's call.
- **An operator's composed text.** Observed, by rule 3 of §E3, even when the owner's own script
  composes it: composing is not writing. The owner's call whether an operator script may promote,
  which today is the owner's re-tag from raw and nothing else.
- **Jobs as scripts.** Dream, the relation pass and curate land interpreted content through
  their own handlers; whether a script should express them (a model call as a reading function)
  is left until a use needs it.
