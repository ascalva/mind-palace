---
type: design-note
id: dn-guest-principal
track: query-language
status: draft                  # provenance description, never a gate; the merge is ratification
implementation: built          # the grant, the role, the surface, the universe's withholding, the leak tests and SCO-9 landed 2026-11-09
created: 2026-11-09
updated: 2026-11-09
links:
  - docs/design-notes/capability-scope-algebra.md          # the scope lattice the grant is a point of
  - docs/design-notes/dn-query-sentence-algebra.md         # clause-wise admission (QSA-5), the universe as the support
  - docs/design-notes/dn-ingress.md                        # the roles and their grants (`grant_for`), ING-1
  - docs/design-notes/plane-principals.md                  # the operating-system side, which this note does not change
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
sealing the core, like the Ambassador's server. It lists two tools:

- `query`: a sentence under `GUEST` through `ask_logged`, logged as surface `mcp`, role `guest`.
  A refusal reaches the guest as `GuestRefusal: <class>: <reason>`, the reason with every quoted
  run replaced by its length (the log's own redaction), so no refusal echoes a path, a title or a
  text, the asker's included; a scope refusal adds the strata the grant reads and how to name
  them with `over`.
- `overview`: the catalog's active entries of the classes the grant's strata hold, the curated
  store's chunk count, and the grant's planes. The Ambassador's overview also counts every vector
  row, the relation edges and the versions; each of those totals counts the notes, so none is
  shown.

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
2. a causal edge that ends at a path under the vault is withheld whole, its id with it, and so is
   a citation neighbour under the vault;
3. `witness` answers no such edge and no landing's attestation (the guest holds no receipt, and a
   note's landing is attested too);
4. the answer says so in one sentence whose words do not depend on what was withheld.

`[DERIVED]` Withholding the whole edge, rather than naming the endpoint by a placeholder or
counting what was dropped, keeps the guest's answers a function of what its grant reads: a
placeholder or a count per edge would be a function of the notes. An edge's id is a content id
over its endpoint, so it is withheld too. A grant that reads the mirror builds the same universe
as before, by the same call.

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
- The default server keeps the Ambassador's table and brief; the launcher serves the guest's
  two tools and refuses an unknown role.

## 8. Limits

- The dialogue is admitted as it is. A chat turn, a capture or an assistant reply that quoted a
  note is a dialogue row, and the guest reads it. The grant bounds strata, not what an admitted
  text says. Keeping such quotations out needs a narrower grant (reference and curated alone) or
  a filtered dialogue; neither is part of this change.
- The isolation is in code. The guest's server opens the instance's stores under the account it
  runs as. Serving an untrusted party should add the operating system's isolation as well
  (`plane-principals`): its own account, read access to what the grant reads.
- Response times may depend on the size of the excluded strata (the overview scans the whole
  catalog; the causal index reads every edge). Timing is not addressed.
- The guest's sentences enter the instance's query log with role `guest`, as every surface's do.
