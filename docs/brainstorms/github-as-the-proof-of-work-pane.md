# github-as-the-proof-of-work-pane

## 2026-07-27T17:10:00Z

```capsule
topic: github-as-the-proof-of-work-pane
date: 2026-07-27

seed (owner, verbatim): |
  "github issues is proof of work, as the system schedules builds, to creating design docs, to the
  draft, proposed, ratified, minted, ready, in-process, done, you can manage a set of issues, not
  sure if this is just proof of work, or the source of truth, but I'm leaning more towards proof of
  work, a birds-eye-view into how the builds are being managed, works because I get to look at
  github for current step in the process, and by proof of work, I mean, this is on a need to know
  basis, when a gate changes, that's performed, I guess I am grasping for something like JIRA, but
  does github have that capability? I know gitlab does. it doesn't show owner-work, only the
  development tracks and their design notes (which build plans act as subtasks, brief descriptors)"
```

## ⚑ THE OWNER ALREADY ANSWERED THE HARD QUESTION

*"I'm leaning more towards proof of work"* — that lean is the whole design, and it is the correct one.

**Proof of work = a PROJECTION.** One-directional, derived, disposable, regenerable. It joins the
family this repo already has — `docs/TRACKS.md`, `DESKCHECK-QUEUE.md`, the seat's `handoff.md` — all
of which are *rendered from* the artifact chain and never read back into it.

**Source of truth = a second writer.** That is the failure this repo has spent the week naming: two
places that can assert the same fact, drifting, with no rule for which wins
([[the-unchecked-claim]]). ⚑ If an issue could be edited and that edit mattered, GitHub becomes a
plane where a status can change without passing a gate — and `proposed → ready` would have two doors.

⇒ **Design rule, and it is the load-bearing one: the projection is WRITE-ONLY from the palace, and
an issue edit is INERT.** Divergence is a defect in the renderer, never a fact about the plan.

## THE TRIGGER — "when a gate changes, that's performed"

This is exactly the derived-pane cadence already in use: regenerate on state transition, not on a
timer and not continuously. The state machine he enumerated is already the artifact chain's:

`draft → ratified` · `proposed → ready` · `ready → in-progress → complete`

⇒ A gate flip is a **commit**, and commits are already the palace's event source. The renderer is a
sensor-shaped thing that reads front-matter and reconciles a set of issues. No new event plane.

## DOES GITHUB HAVE THE JIRA CAPABILITY?

`[INFERENCE — verify before building]` GitHub has moved a long way toward this and the pieces
plausibly suffice: **Projects (v2)** gives custom fields, saved views, board/table/roadmap layouts;
**sub-issues** give the parent/child nesting the owner wants (design note → build plans as subtasks);
**issue types** give the taxonomy. What GitLab has that GitHub historically lacked is a first-class
*epic* object — sub-issues are the closest analogue.

⚑ **This must be verified against current GitHub capability before any plan is written**, not taken
from an agent's recollection — the external-grounding gate applies.

**Mapping, provisional:**

| palace | GitHub |
|---|---|
| track | Project (or a label/field) |
| design note | parent issue, its status field = `draft/ratified/superseded` |
| build plan | **sub-issue** of its note, status = `proposed/ready/in-progress/complete` |
| finding | issue, linked to origin plan |
| owner question | ⚑ **excluded** — see below |

## ⚑ THE EXCLUSION IS A PRIVACY BOUNDARY, NOT A PREFERENCE

*"it doesn't show owner-work, only the development tracks and their design notes"*

That is non-negotiable #11 landing on a new surface: **the interface may transit a third party; the
corpus never does.** GitHub is a third party. What may cross: plan ids, titles, statuses, track
coordinates. What must not: `owner-questions.md`, journals, findings' prose, capsule content, any
seat narrative, anything from the vault.

⇒ The renderer needs a **whitelist of fields**, not a blacklist — and a test asserting a
non-whitelisted field never appears in a rendered payload. `[INFERENCE]` The degenerate input
([[the-false-success-rule]]): a renderer that emits nothing at all passes a "no private data
leaked" check trivially.

## OPEN

- **Does it earn its keep?** The board already answers "what is the current step" locally. The win
  is *away from the keyboard* — the same argument as the phone report lane and autopilot. If the
  owner reads it on a phone while a wave runs, it is worth building; if it duplicates a pane he
  reads at the terminal, it is a second copy that will rot.
- **Failure mode:** GitHub API down or rate-limited mid-wave. The renderer must fail **open and
  silent** — a projection that can block a gate has become load-bearing, which is the thing it is
  explicitly not.
- `[INFERENCE]` Whether issues close automatically on `complete`, or wait on deskcheck — the repo's
  own rule says a track closes at deskcheck, not at seal ([[deskcheck-discipline]]), so a plan going
  `complete` should probably *not* close its parent.
