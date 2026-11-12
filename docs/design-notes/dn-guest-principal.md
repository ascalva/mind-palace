---
type: design-note
id: dn-guest-principal
track: query-language
status: draft                  # provenance description, never a gate; the merge is ratification
implementation: built          # the grant, the role, the surface, the universe's withholding, the leak tests and SCO-9 landed 2026-11-09; the lite profile's overview and tests 2026-11-11; the audit's repairs 2026-11-12
created: 2026-11-09
updated: 2026-11-12
links:
  - docs/design-notes/capability-scope-algebra.md          # the scope lattice the grant is a point of
  - docs/design-notes/dn-query-sentence-algebra.md         # clause-wise admission (QSA-5), the universe as the support
  - docs/design-notes/dn-ingress.md                        # the roles and their grants (`grant_for`), ING-1
  - docs/design-notes/plane-principals.md                  # the operating-system side, which this note does not change
  - docs/design-notes/dn-palace-lite.md                    # an instance that embeds nothing; the code instance the guest serves
  - formal/Palace/Scope.lean                               # SCO-9, with Sentence.lean and Ingress.lean
  - papers/2026-11-09-guest-principal/paper.tex            # the article
supersedes: null
superseded_by: null
warrant: null
---

# The guest principal: a read-only grant for an external agent

> Agent-drafted on a branch; the merge is ratification. Grades as elsewhere: `[THEOREM]` is
> machine-checked in `formal/` and names its declaration; `[ESTABLISHED]` is a ratified note's or
> a fact of the repository; `[DERIVED]` is argued here; `[TESTED]` names the test that holds it.

## 1. Purpose

An agent that is not the owner's local model, run by someone else or on another machine, may ask
the palace over MCP. It should read the dialogue, the repository's code and docs, the curated
papers and the observed records, and never the owner's notes or what a model derived from them.
The Ambassador's grant reads the notes; a second grant is needed, and a surface that serves it.

## 2. The grant

`core/query.py::GUEST` follows the Ambassador's plane structure without the mirror's version
plane:

| plane | strata named (closed downward) | fibers | clock | authority |
|---|---|---|---|---|
| projection events | dialogue (transcript, artifact), reference (reference_repo), curated, observed | F, D | projection_event | read |
| commits | reference (reference_repo), dialogue (transcript, artifact) | F, C | commit | read |

`[THEOREM: SCO-9]` The grant is one the code accepts (`Scope.lean::guest_grantOk`); none of its
planes names the mirror, `mirror_authored` or the interpreted stratum, closure included
(`Scope.lean::guest_reads_no_note`), so a clause that reads any of them is refused
(`Scope.lean::guest_refuses_note`); no plane carries the write bit, so it admits no command
(`Ingress.lean::guest_admits_no_command`, from ING-1's `readonly_admits_no_command`); none names
the overlay, so it admits no `assume` (`Sentence.lean::Sentence.guest_no_assume`, from QSA-5's
`admissible_assume_overlay`). The closure is SCO-1's: a refinement closes downward within its own
tree, and the four strata's trees do not hold the mirror; `exhaust` is excluded by the closure and
`hypothetical` is named by no plane.

The interpreted stratum is left out because its relations and dreams are readings of the notes
and can quote them. The version plane is left out because its chains are the notes' own.

## 3. The role

`grant_for("guest")` returns `GUEST` (`core/ingest/ingress.py`, `_READ_ROLES`). The role has no
spool and no role in the table: a request compiled for it is refused at admission (no plane has
the write bit) or by the script checker (the role opens no source), and `write_request` refuses
the role before it touches a directory. `[TESTED: test_the_guest_role_is_refused_every_request]`

## 4. The surface

`uv run --project <checkout> python scripts/palace_mcp.py --role guest` speaks MCP on stdio after
sealing the core, like the Ambassador's server. With `MIND_PALACE_OVERLAY=config/instances/code.toml`
it serves the code instance (`dn-palace-lite` §4.4), whose files a sentence names as
`code/<name>/<path>`. It lists two tools:

- `query`: a sentence under `GUEST` through `ask_logged`, logged as surface `mcp`, role `guest`.
  A refusal reaches the guest as `GuestRefusal: <class>: <text>`, and the text depends on where
  the sentence was refused. The surface compiles the sentence again, alone, with the trace when
  the call asked for one, as the first compile had it (the trace renders the parse, so a sentence
  can fail to compile with it alone); that reads the sentence and the grant and no store. If the
  compiler refuses it, the text is the compiler's reason with every quoted run replaced by its
  length (`redact_reason`, the log's own redaction): that reason holds the asker's words and
  nothing a store holds. If it compiles, the refusal was raised while the sentence ran against
  the stores, and the text is one fixed sentence for its class (`GUEST_RAN`: lookup, ambiguous,
  unsupported, scope, sort, parse, busy, error), never the reason. A reason raised in the run may
  quote what a store holds, and the redaction pairs quotes by position: an apostrophe in a
  reason's own words pairs with the opening quote of a quoted path and leaves the path in clear,
  and text quoted any other way passes whole. The query log keeps the reason for the owner. A
  scope refusal of either kind adds the strata the grant reads and how to name them with `over`.
  `[TESTED: test_a_refusal_says_the_compilers_reason_or_its_classs_one_sentence,
  test_a_sentence_the_compiler_refuses_under_the_trace_alone_reads_its_reason]`
- `overview`: the catalog's active entries of the classes the grant's strata hold, the curated
  store's chunk count, and the grant's planes. On an instance of the lite profile
  (`dn-palace-lite`) it says what the Ambassador's says of the profile, over the same classes:
  that the instance embeds nothing, the lexical index's current units of those classes, and each
  repository of the lexical code source by its name and ref, with the commit it last landed,
  when, and how many commits the ref has moved past it. The Ambassador's overview also counts
  every vector row, the relation edges, the versions and every lexical unit; each of those totals
  counts the notes, so none is shown. An overview that fails says one fixed sentence.

The body of each of the guest's tools raises `GuestRefusal` and nothing else. The engine is built
on first use, inside the body, so a configuration or a store that cannot be opened is a refusal
too, and a refusal is raised without its cause, so its traceback on stderr holds the refusal's
words only. The client reads stdout as the protocol stream, one message per line, and nothing
else reaches it: the launcher writes the replies to a copy of file descriptor 1 that no child
inherits and points the descriptor itself at stderr (`protocol_stream`), so what C code, a child
process or `sys.__stdout__` writes there lands on stderr, and a tool runs with `sys.stdout`
pointed at stderr as well (`Server.handle`). A reply that UTF-8 cannot encode, one repeating a
lone surrogate that a sentence held, is written as ASCII, the same JSON, whatever the stream's
error handler: Python's UTF-8 mode gives stdout `surrogateescape`, which would write some
surrogates as bytes that are not UTF-8. A line that is no request (JSON that is not an object,
params that are not one, an id that is no string or number, a number past Python's limit on the
digits it converts, nesting past the stack) is answered with JSON-RPC's error for it.
`initialize` repeats the protocol version a client asks for only when it is a string and answers
any other value with the server's own, so no reply carries a nesting the client sent, and a reply
that `json.dumps` cannot write all the same is answered as an internal error with the request's
id. Either way the server reads on.
`[TESTED: test_what_the_guests_tools_print_stays_off_the_protocol_stream,
test_what_a_tool_writes_to_the_descriptor_stays_off_the_protocol_stream,
test_a_line_that_is_no_request_is_answered_and_the_server_reads_on,
test_initialize_answers_the_version_asked_when_it_is_a_string_and_its_own_otherwise,
test_a_request_whose_reply_cannot_be_written_is_answered_as_an_internal_error]`

`status` is left out: it lists the owner's open and due tasks and the running jobs, whose briefs
can name notes. No write tool is served (capture, tasks, reminders, link, dream, relate, the
syncs). The instructions are the guest's own; the brief describes tools the guest does not have.
With no `--role`, the server is the Ambassador's, its table and brief unchanged.

## 5. What the other stores say of the notes

`[ESTABLISHED]` Admission is clause-wise and the universe holds only the strata the admitted
clauses read (QSA-5, `core/sentence/universe.py`). That bounds rows. It does not bound what an
admitted row says. The causal store belongs to the transcript stratum, and an edge's endpoint is
a path: a turn that wrote a note names the note's vault path. Under a sentence that does not read
the mirror, the universe named such an endpoint as a node of the transcript stratum, path and
title alike, and `witness` of the edge returned its endpoint. For the Ambassador, whose grant
reads the mirror, that shows nothing new. For a grant without the mirror it is a leak.
`[TESTED]` With the change below switched off, five sentences of the guest's battery returned the
canary note's path: `reach C` and `walk … via C` from the turn, over strata that hold the
transcript, and `witness` of the edge.

The change keys on the grant, not the sentence. `Grant.strata` is the union of a grant's planes.
When it holds no stratum of the mirror, `ask_logged` builds the universe with `hide_mirror`:

1. the note graph is not built; the dialogue loads through its own clearance;
2. a causal edge is shown only when it ends at a commit, named by its hex sha, or at a file git
   tracks in this checkout at HEAD (`_Builder._named`), written as an absolute path under a
   checkout of the repository or as a doc's id that resolves to exactly one file. The vault is
   asked first, and a path is withheld when it is the vault or lies under it with each component
   folded for letter case and Unicode normal form, as written, normalized or resolved
   (`_in_vault`). Every other edge is withheld whole, its id with it;
3. a citation neighbour is named only when it is spelled as a repo-relative path (not absolute,
   not under `~`, no URI, no `..` component) and, joined to the root of each checkout, lies
   outside the vault (`_citable`);
4. `witness` answers no withheld edge, asked by its own id or through the reference edge whose
   commit it witnessed, and no landing's attestation (the guest holds no receipt, and a note's
   landing is attested too). Through a reference edge it answers the first edge keyed to the
   commit that the reader may see named: a withheld one is judged before the first is chosen,
   so it never stands in front of a named one (`origin`'s `admit`);
5. the answer says so in one sentence whose words do not depend on what was withheld.

`[DERIVED]` Withholding the whole edge, rather than naming the endpoint by a placeholder or
counting what was dropped, keeps the guest's answers a function of what its grant reads: a
placeholder or a count per edge would be a function of the notes. An edge's id is a content id
over its endpoint, so it is withheld too. A grant that reads the mirror builds the same universe
as before, by the same call.

`[DERIVED]` Item 2 is an allow list, and fails closed. Its first form was a deny rule, which
withheld an edge whose endpoint lay lexically under the vault path, and a path has more
spellings than that rule knew. A red team found five that passed it, each showing the guest a
note's path or name as a hit and through `witness`: the vault directory in another letter case,
or the path in another Unicode normal form, which a file system that folds them treats as the
same file; a relative path; a `file://` URI; and the bare file name the event projector keeps for
a file written under a `docs/design-notes/` folder. A deny rule has to know every spelling of a
vault path. An allow list has to know only what may be shown, and what it cannot judge it
withholds: git that cannot be asked names no file, an endpoint that raises while it is judged is
not named, and a doc's id that holds a glob's characters resolves to no file (the projector keeps
a file name as the id, and a finding's or a plan's file is found by a glob). The vault check
folds letter case, the Unicode normal form, `.` and `..`, symlinks and `~`. A file system knows
a note by other names as well, a hard link or its path through another mount of the volume
(macOS's `/System/Volumes/Data`), which the check does not fold; the allow list judges such a
name as it judges any path, and names it only when it is a file git tracks in a checkout of the
repository. The cost falls on endpoints the rule cannot tie to a tracked file. The guest no
longer sees named an endpoint outside the repository, a relative path (one that names a tracked
file among them), a tracked file's path in another letter case or under another clone, a file
git does not track at HEAD (untracked, or deleted since), a file that exists only in another
worktree, or a doc's id that is not one tracked file; a grant that reads the mirror is shown
each of them as before.
`[TESTED: test_an_edge_is_shown_only_when_it_ends_at_a_commit_or_a_tracked_file]` Nine such
edges and four such citations added to the fixture change no guest output, byte for byte;
`witness` of each id answers nothing; the Ambassador is shown every one.

`[DERIVED]` An instance that embeds nothing (`dn-palace-lite`) is what the guest is meant to
serve: an external coding agent reads the code instance (`config/instances/code.toml`). Such an
instance lands every item with its lexical units and no vector, a vault's notes among them, in
one index, and ranks `near` by BM25 over it, so a ranking whose unit count, mean length or
document frequencies were read over the whole index would be a function of the notes. They are
read over the classes a ranking asks for (`LexicalStore._score_units`), and every lexical path of
the universe asks for classes the grant reads: the reference seed for the code's, the curated
seed for the papers', the dialogue's vectorless items for the dialogue's (`load_pending` lists
no other class under `hide_mirror`), and the scores of a clause's vectorless nodes for the
classes of those nodes, which are the admitted strata's. A landed repository file is read from
the raw store only when the catalog holds it as code (`_read_landed_file`); any other ref falls
to git's tree at the cut, as before. The rules above hold unchanged. So the guest's ranks,
scores, notes and counts on such an instance are functions of what its grant reads.
`[TESTED: test_the_guest_cannot_tell_two_palaces_that_embed_nothing_apart]` Two such palaces
whose notes differ in their words and their length, and which are alike in all else the guest
reads, the second their repository landed included, give the guest the same answers to the
battery and the code source's refs, and the same overview; a ranking's statistics over every
class, the reference seed over every class or the overview's units as a total each fail the test,
and the Ambassador's answers and counts tell the two palaces apart.

## 6. The laws the guarantee rests on

SCO-1 (the closure of the four strata holds no mirror stratum), SCO-6 (admissibility and the zone
law), QSA-5 (a sentence is admitted clause by clause), ING-1 (a read-only grant admits no
command), PLN-1 (a read under a clearance returns only the classes it names), PLN-2 and BRG-5
(noninterference through the plane), QSA-10 (`over` is the mask by the clearances' table), and
the new SCO-9 for this grant. The universe's withholding is code, held by the noninterference test
below and not by a theorem.

## 7. The tests

`tests/adversarial/test_guest_leaks.py` builds a palace on real stores holding a note with a
canary in its path, title and body, landed by the ingress; an interpreted relation from it to an
authored dialogue turn; an authored and an observed dialogue turn; a transcript turn whose causal
edges point at the note and at a repo file; a paper; a code atom; and a citation graph. As the
guest, it asks every verb, with and without `over`, every adjective and connective, `assume` and
the requests, with and without `trace`, then `overview` and `status`.

- No output carries the canary, as a path, a title, a text, a count or a refusal; every sentence
  that names the note is refused.
- The admitted strata answer: dialogue, code, papers, the transcript and the repo's files.
- Over a second palace whose note, relation, landing and vault edge differ, every guest output
  is the same once the names the asker typed are normalized.
- The control: the Ambassador, asked the same, sees the canary in the `near`, `reach C`,
  `witness`, `relate` and `read` answers.
- The note under other spellings: the causal store gains nine edges from the turn (the vault
  directory upper-cased, the path in its other Unicode normal form, two relative paths, a
  `file://` URI, the file name the projector keeps for a vault file under `docs/design-notes/`,
  such a name that is a glob's pattern for a tracked finding, an untracked path in the checkout,
  a path outside the repository), and the citation graph four from a repo file to the note's
  path and three spellings of it. Asked the battery, each new id and each new endpoint, the guest
  answers what it answered before, byte for byte; `witness` of each id answers nothing; the
  Ambassador is shown every one.
- Refusals: a sentence the compiler refuses reads the compiler's reason, redacted, and so does
  one it refuses under the trace alone; one refused while it ran reads its class's fixed
  sentence, with and without the trace; a store's error whose reason quotes a path with an
  apostrophe reaches the guest as its class alone, on the stream and on stderr, while the query
  log keeps the reason; an `overview` that fails and an engine that cannot be built are each one
  fixed sentence.
- The query log: a sentence with a line separator, one with an escape sequence and a forged
  line, a bidi override, a lone surrogate, a sentence of 300,000 characters and one of 50,000
  characters outside the BMP each take one ASCII line of the log, the long ones cut, no line
  longer than the cut allows, and both renderings of `palace query --log` print every such
  character escaped.
- The protocol stream: a store that prints while the guest's tools run leaves one reply per
  request on the stream the server writes and nothing else; what it printed is on stderr. The
  launcher, spawned with a guest tool that writes a forged reply to file descriptor 1, runs a
  child that prints and writes to `sys.__stdout__`, leaves one reply per request on stdout, and
  every such line on stderr.
- The default server keeps the Ambassador's table and brief; the launcher serves the guest's
  two tools and refuses an unknown role.

`tests/unit/test_sentence_universe_withheld.py` holds the rule at the universe builder, over a
scratch git repository standing for the checkout: the tracked paths are the tree at HEAD and none
when git cannot answer; a vault path is recognised in another letter case, another Unicode normal
form, with `.` and `..`, through a symlink and under `~`, and a name the check does not fold, a
hard link or the path through another mount, is not named by the allow list; only a commit or a
tracked file is named, and only a commit when the tree cannot be read, and a configured vault
that is a symlink into the checkout withholds the tracked files under it; a turn whose edges are
all withheld is refused as a turn no edge names; the witness of a reference edge is judged like
any other, and a withheld edge keyed to its commit stands in front of no named one; the
withholding note is one sentence whatever the store holds; a citation neighbour is named only as
a repo-relative path outside the vault. A grant that reads the mirror is shown what it was shown
before, and `tests/unit/test_sentence_universe.py` passes unchanged.
`tests/unit/test_sentence_surface.py` holds the log (a line separator, a lone surrogate, the cut
in characters and in bytes, the escapes in both renderings, a line that is not an entry skipped
and counted, the log read a line at a time), `tests/unit/test_ambassador_surface.py` the stream
(what a tool prints goes to stderr; a process without stderr drops it; a reply UTF-8 does not
encode is written as ASCII, on a strict stream and on one with `surrogateescape`; a line that is
no request is answered and the server reads on; `initialize` repeats a version only when it is a
string; a request whose reply cannot be written is answered as an internal error and the server
reads on), and `tests/unit/test_sentence_grammar.py` that a string literal is read in memory its
text bounds. How deep `json` nests depends on the thread's stack (8 MB for a Linux main thread
under the usual `ulimit -s`, 16 MB for the main thread of a macOS framework build), so the tests
that need a nesting past it serve their lines on a thread whose stack they set to 1 MB.

`tests/adversarial/test_guest_lite.py` asks the same of an instance that embeds nothing. Its
palace lands the note through `sync_vault` and a scratch repository's files through
`sync_repository`, each with its lexical units and no vector, and holds the dialogue and a paper
with lexical units alone and the same transcript turn, causal edges and citation graph.

- The battery and the code source's refs (a lexical `near` over reference, `read` of a landed
  file, `diffuse S` and `reach F` from one, `trace`, a file the repository does not have): no
  output carries the canary; `S` has no edge there, so its walks are empty, and the paper, which
  such an instance keeps in no plane, is ranked and not read; every sentence the battery refuses
  is refused.
- Over a second such palace whose note differs in its words and its length, its repository's
  landing dated to the same second as the first's, every guest output and the overview are the
  same; the Ambassador ranks the first note first and counts more units.
- Every score and every count the lexical index makes while the guest asks names its classes,
  each one the grant reads; the Ambassador's `near` over the notes names the notes' class.
- `near` over reference ranks the repository's files, each labelled `ranked_by`, its notes saying
  the instance embeds nothing; `read` opens a landed file; `overview` says the profile, the units
  of the admitted classes (fewer than the index's) and the repository with its landed commit.
- The launcher, spawned with an overlay made from the code instance's own after its repository
  landed, lists the guest's tools and answers `overview`, a lexical `near`, a `read` and three
  refusals in their fixed words, one reply per request on stdout; the instance's own query log
  holds the guest's sentences, and no vector store is made.

## 8. Limits

- The dialogue is admitted as it is. A chat turn, a capture or an assistant reply that quoted a
  note is a dialogue row, and the guest reads it. The grant bounds strata, not what an admitted
  text says. Keeping such quotations out needs a narrower grant (reference and curated alone) or
  a filtered dialogue; neither is part of this change.
- The isolation is in code. The guest's server opens the instance's stores under the account it
  runs as. Serving an untrusted party should add the operating system's isolation as well
  (`plane-principals`): its own account, read access to what the grant reads.
- Response times may depend on the size of the excluded strata (the overview scans the whole
  catalog; the causal index reads every edge; a lexical ranking reads a term's postings in every
  class before it keeps its own). So may a time the guest reads: the overview shows the second
  each repository landed, a clock reading, and the daemon's one queue lands a vault's notes and
  a repository's files in turn, so a landing of the notes queued first delays it. Timing is not
  addressed.
- The reference stratum holds what the instance lands in it. A repository source is read through
  git at its ref, and the loader compares a repository's path with no vault: a repository whose
  tree tracks a vault's files would land the notes as code, and the guest reads code. The code
  instance declares this repository alone. Refusing a repository at, inside or around a vault
  this host reads belongs in the loader and is not part of this change.
- A vault file under a `docs/design-notes/`, `docs/findings/` or `docs/build-plans/` folder is
  recorded by the event projector (`core/chat_events.py`) as a bare doc id, with no path. Its
  edge is shown only when the id resolves to exactly one tracked doc of the repository, and then
  as that doc: the guest learns that a turn wrote a file of that doc's name, never the vault's
  path. The exact fix keeps the path at projection, or classifies a doc only under a checkout;
  it belongs in the projector and is not part of this change.
- A citation neighbour is not checked against the tree at HEAD, since the citation graph is read
  at other cuts. Its refs are repo-relative paths projected from the repository's history, so
  they denote the repository's files; a citation store that held a relative path naming
  anything else would show it.
- The client that spawned the server also reads its stderr: a refusal's traceback, which holds
  the refusal's words only, and whatever a tool, a library under it or a child process writes
  there or to file descriptor 1. What reaches stderr is not filtered.
- The guest's sentences enter the instance's query log with role `guest`, as every surface's do.
  A line is ASCII, a sentence is kept up to 4,096 characters and up to 8,192 bytes of the line,
  a character counted as its escape, and then a marker of its full length, and
  `palace query --log` reads the log a line at a time and prints every character that is not
  printable as its escape, so a sentence cannot break the log or write into the terminal that
  reads it. Nothing bounds the log's size: each call appends a line of at most some 12 KB, and a
  guest that calls without pause grows it by megabytes a second until the disk is full (2,000
  calls of 5,000 characters outside the BMP, through the launcher, appended 8,536 bytes each,
  17 MB in 2.8 s, at a one-minute load of 2.0). How it is bounded (a size past which it rotates
  or stops, a budget per role) and what is dropped at the bound are the owner's to decide; this
  change sets no bound.
- A sentence's size is not capped; only a command's is (`MAX_COMMAND_BYTES`). The server reads
  a request's line whole and holds some five times its size while it answers: through the
  launcher, a request refused as it parses took the server to 411 MB for a line of 50 MB and to
  1,169 MB for one of 200 MB, answered in 6.1 s (one-minute load 1.5 to 2.0), so a line of about
  0.8 GB would take it past 4 GB. A sentence refused as it parses is read three times: by the
  compile, by the log's entry, which reads its shape, and by the surface's second compile. A
  string literal is read in memory its text bounds: asked in process, a refused sentence of
  40 MB raised the server's peak by some 40 MB past the sentence itself and was answered in
  0.8 s, and one of 40 MB of escaped quotes by some 54 MB, in 1.3 s (one-minute load 3.4 to
  3.8). Whether a guest's sentence is capped, at what size, whether every surface takes the cap,
  and whether the server's reader stops a line at it, are the owner's to decide.
