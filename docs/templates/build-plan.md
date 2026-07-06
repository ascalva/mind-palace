---
type: build-plan
id: <bp-NNN | descriptive-slug>
status: proposed
design_ref:               # ratified design-note id(s) this plan graduates from
  - <docs/design-notes/....md>
contract: builder         # builder | scribe
write_scope:              # exact globs — the capability; enforced by scope-guard
  - <path/glob>
session_budget: 1         # if the work will not fit ONE session, SPLIT at graduation, never mid-build
depends_on: []            # plan/item ids that must complete before this may start
parallelizable_with: []   # plan ids that may run concurrently (requires disjoint write_scope)
created: <date>
updated: <date>
links: []
re_entry: null            # only if parked — the greppable "parked ⇒ re-entry" gate (§3, Principle 1); §11 is its human-readable expansion (A6)
supersedes: null          # plan id this replaces, if any
superseded_by: null
warrant: null             # finding id, if this plan supersedes another or corrects committed code
---

# Build Plan — <title>

> **Every section below is required.** A section that does not apply is marked
> `N/A — <one-line reason>`, never silently omitted. The explicit N/A is an
> accountability act: it records that the author considered the section and
> judged it inapplicable, rather than leaving a reader to guess. Sections most
> often N/A on greenfield or trivial-mechanical plans: §3 Investigation,
> §4 Reconciliation, §8 Math. They are never N/A on a plan that touches existing
> code or implements a mathematical object.

## 0. Mode & provenance

<!-- For a domain/grounding plan: state "investigation and planning produced this;
implementation proceeds item-by-item on owner approval." Separate authority-to-act
(the owner's instruction to build) from the readiness blessing (owner-only
proposed → ready). No agent flips readiness. -->

## 1. Objective

<!-- ONE sentence. What this plan makes true. If it needs two sentences, it may
be two plans. -->

## 2. Context manifest

<!-- The exact files to read, IN ORDER, before any work. No wandering. Whole files
before citing. This is what a fresh /resume session loads. -->

1. `<path>` — <why>

## 3. Investigation & grounding  <!-- Part A -->

<!-- REQUIRED for any plan touching existing code. Answer each open question with a
`path:line` citation. Where the code does not settle a question, SAY SO — never
infer. This is the grounding pass that makes the plan trustworthy before a builder
acts. Mark `N/A — greenfield, no existing code touched` only when literally true. -->

- **Q<n> — <question>.** <answer> — `path:line`. <If unsettled: "code does not settle this; <what would">.>

**Additional risks or questions surfaced during reading:** <list, or "none">

## 4. Reconciliation  <!-- Part B -->

<!-- REQUIRED where this design corrects or extends existing docs/code. For each
affected artifact: quote the passage, then propose a **banner-on-correction** or a
**cross-reference-on-extension** — NEVER a silent replacement. Corrections to
committed code are called out as corrections and carry a code change in an item
below, not a quiet edit. Present as proposed diffs. Mark `N/A — nothing corrected
or extended` if true. -->

- `<artifact>` — <quoted passage> → **[banner: correction | cross-ref: extension]**: <proposed diff>

## 5. Write scope

<!-- Mirror the front-matter write_scope in prose, and name what is deliberately
OUT of scope (foundation files, design notes, stores this plan must not touch).
scope-guard enforces the front-matter; this section makes the intent legible. -->

## 6. Interfaces pinned inline

<!-- Signatures, schemas, invariants the plan depends on — COPIED IN, not
referenced. The builder must never infer design from a pointer. If it's load-bearing
and lives in another file, paste the exact current form here with its `path:line`. -->

## 7. Items

<!-- The phased work. Continue item numbering across the plan family (don't reset).
Order by BLAST RADIUS: read-only sensing → reversible writes → irreversible/external
effects. Each item is INDEPENDENTLY APPROVABLE. -->

### Item <n> — <title>

- **Objective:** <one line>
- **Files:** <created or changed only — path list>
- **Acceptance test:** <runnable — what proves it works>
- **Falsifier:** <the observable result that would show it FAILED or the approach is
  WRONG — distinct from acceptance. Acceptance says "it works"; the falsifier names
  the thing that, if seen, means it doesn't or the assumption is false.>
- **Invariant(s) it must not violate:** <the guarantees that must still hold after>
- **Touches stored data?** <yes/no — blast-radius flag; if yes, require a dry-run /
  verification pass before the real write>
- **Parallelizable?** <yes/no>  **Depends on:** <item/plan ids, or "none">

## 8. Math carried explicitly

<!-- REQUIRED for any plan implementing a mathematical object. For EACH object, its
three-clause field-guide entry. Formalism earns its place or is cut; this is where it
earns it. Mark `N/A — no mathematical object implemented` if true. -->

- **<object>** — *measures:* <what it measures>. *valid when:* <assumptions that make
  it valid>. *fails its keep if:* <observable result showing it is not earning its place>.

## 9. Non-goals

<!-- Explicit. What this plan deliberately does NOT do, to bound scope creep and
prevent the builder from helpfully overreaching. -->

## 10. Stop-and-raise conditions

<!-- When the builder must STOP and surface rather than proceed: an owner-level
question (park the criterion, continue others — never block on owner), a discovered
spec defect (file a finding), a blast-radius surprise, a blessing it would have to
perform (it must not). -->

## 11. Parked decisions

<!-- Each deferred decision: the default recorded, the rejected alternatives WITH
reasons, and an explicit re-entry condition + named blocking prerequisite. A parked
decision is a first-class artifact, never silently dropped. -->

| Decision | Default recorded | Rejected alternatives (why) | Re-entry condition |
|---|---|---|---|
| <decision> | <default> | <alt — reason> | <condition + prerequisite> |

## 12. Dependency & ordering summary

<!-- The dependency edges among this plan's items (and to other plans), and the
blast-radius phase order. State which items are parallelizable and which are gated.
This is the map /graduate used to size the plan and the map the owner approves. -->
