---
type: design-note
id: dn-skills-and-scope
status: draft
implementation: present-not-wired   # corpus-audit 2026-07 verification
created: 2026-06-25
updated: 2026-07-01
links: []
supersedes: null
superseded_by: null
warrant: null
---

# Design note — Skills, roles, and the scope ceiling

*Family tag → family 1 (the capability semilattice): 𝒜 = scope ∩ MAX; skills are non-widening, 𝒜(a ⊕ ς) = 𝒜(a) (I13). See [`../NOTATION.md`](../NOTATION.md).*

**Status:** design only, not implemented. Thread raised 2026-06-25; to be honored when
roles + the factory land (instructional half ~Phase 3 context composition; capability
half Phases 4–5). Reconciled against what Phase 0 actually built.

## The question
How should "skills" attach to agent roles (BUILD-SPEC §10) without becoming a backdoor
around *model-advises-code-acts* (Invariant 3)?

## Resolution — "skill" is two things, attached by two independent mechanisms
1. **Instructional skill** — packaged competence as *text* (procedure, playbook, domain
   directives, few-shots). Pure context. The composer loads relevant ones into the
   role's frame; choosing which is a routing/retrieval decision, like pulling notes.
   Versionable docs, **no new capability**.
2. **Executable skill** — an instructional half (what it does / when to use it) **plus**
   a capability half: a scoped tool the agent is *permitted* to invoke, run by
   deterministic code, sandboxed per §11 if it executes.

**Invariant we hold:** *membership grants context; the scope ceiling grants capability;
the two are checked independently, by different subsystems, at different times.* A skill
can only activate a tool already inside the role's pre-declared scope. Load a
"deploy to AWS" skill into an agent not scoped for it and you get an agent that **knows
about deploying and cannot do it** — never one that suddenly can.

## What Phase 0 actually built (reconciliation)
- **`core/agent.py`** — `Agent = {name, role_prompt, tier, server}`. **No tool scope, no
  tools, no dispatch loop.** `respond()` returns `(text, SelfCheck)` — purely advisory;
  there is no action path at all. → The safety property holds *trivially* today (no agent
  can act), and it tells us the executable half must be built as a **separate,
  code-mediated dispatch path — never bolted onto `respond()`**.
- **`core/constitution.py:frame_context()`** — composes ordered system frames with the
  Constitution outermost (Invariant 6). → This is exactly the seam the instructional half
  slots into: `Constitution → role template → [skill frames] → history → task`. No
  rework; just generalize the single `role_prompt` to an ordered frame list. The budgeter
  (Phase 3) owns *which* skills fit; the router (§9) owns *which* are relevant.
- **`core/stores/telemetry.py`** — already implements scoped capability as
  **object-capability**: a `TelemetryWriter` *has no read method* — "the wrong access is
  impossible, not discouraged" (CONVENTIONS). → This is the precedent for the capability
  half: **a tool is a narrow handle the agent is given, not a flag it is granted.** Scope
  is the set of handles; out-of-scope is *unreachable*, not "checked then refused."

**Conclusion:** the two-layer model fits cleanly on top of Phase 0. Phase 0 changes the
executable half in exactly one (good) way: follow the store-layer object-capability
pattern rather than a dispatch-time string-flag check.

## Concrete shape (for §9/§10, Phase 5)
Role template declares two **separate** fields — never conflated:
```
RoleTemplate:
  prompt_fragment, default_tier, code_exec_profile, network_profile
  skills: tuple[SkillId]      # instructional skills loaded/available (CONTEXT)
  scope:  frozenset[ToolId]   # capability ceiling for the role, ≤ pre-declared max (§10)
```

**Instructional skill** — a versioned doc: `skills/<id>/skill.md`, frontmatter
`{id, version, when_to_use, requires_tools?}` + body (procedure / playbook / few-shots).
Selected by the router (§9), fitted into context by the budgeter (§13). No capability.

**Executable skill** — the same doc **plus** `requires_tools: [tool_id…]`. The tool lives
in an **independent tool registry**: `ToolSpec{ id, handler | code_exec, io_schema,
exec_profile }` where `exec_profile` declares sandbox (§11) / scoped network grant / none.
Binding is by *name*; the tool is registered independently of any skill.

**Two predicates, two subsystems, two times** (this is the backdoor-proofing):
- `loaded(skill, agent)` — the context composer/budgeter, at assembly.
- `can_invoke(tool, agent)` — the tool dispatcher, at invocation:
  `tool_id ∈ agent.scope`, where `agent.scope = role.scope ∩ pre_declared_max`, resolved
  **at mint** by the factory (§10) and **never widened by a skill**.

Backed by object-capability (the store-layer precedent): the dispatcher's table holds
*only the in-scope tool handles*, so a model-emitted tool name that isn't there resolves
to nothing → refuse, and route genuinely-privileged requests to the human gate
(§10/§14). An explicit `authorize()` makes the refusal auditable.

A skill referencing a tool **outside** the role's scope still loads its instructional
half (knowledge); its capability half is inert. The composer should surface this:
"advice-only — skill X references tool Y outside this role's scope."

## Conflicts flagged
- **Scope ceiling (§10):** the entire risk is skill-membership ⇒ capability. Closed:
  capability flows *only* from `role.scope ∩ max`, resolved at mint, enforced at dispatch;
  skills never widen it.
- **Sandboxed execution (Inv 4, §11):** executable skills that run code declare a
  code-exec profile routed through the §11 broker — powerless, no creds/network/vault,
  returns data. A skill cannot define a non-sandboxed execution path.
- **Model-advises-code-acts (Inv 3):** the action path is the deterministic dispatcher,
  not `respond()`. Do not regress Phase 0's advisory-only agent.
- **Context budget (§13):** skills consume the window; the budgeter trims skills and
  retrieval *before* the Constitution; skill docs stay lean; track skill-load to telemetry.
- **Fixed points (§4/§15, §8):** the skill library is *explicit/authored* data (not
  interpreted) — human-curated, versioned, under behavioral-conformance baselines.
  Changing it is a **gated change, not a safe lever**, and it is **not** the Constitution.

## Phase ownership
- Instructional half: library may seed any time; selection + composition = router (§9) +
  budgeter (Phase 3).
- Capability half: tool registry + scope resolution + dispatch/`authorize` = factory +
  sandbox (Phases 4–5).
