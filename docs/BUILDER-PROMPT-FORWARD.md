# Builder prompt — the forward roadmap (post-base-build)

The base build (Phases 0–10) is complete and live. This drives the **forward layer** —
six tracks (A–F) that take the system from built to fully realized. Hand to a fresh
builder session per work item; the order across tracks is the owner's choice, the order
*within* a track and the one cross-track dependency are not.

---

## The prompt (paste into a fresh builder session)

> **Fresh builder session — forward roadmap work item.**
>
> Re-ground per CLAUDE.md: read `docs/PROGRESS.md`, `CLAUDE.md`, `CONSTITUTION.md`,
> `CONVENTIONS.md`, `docs/MIND-PALACE-V1.md` (the v1 system map), `docs/ROADMAP-V1.md`
> (the track/dependency map), and the specific design note(s) for the item you are
> building. The ten numbered phases are DONE and live; this is forward-layer work, built
> as **tracks**, not numbered phases.
>
> **The owner will tell you which item (e.g. "A1 — the drift gauge" or "B2 — the
> Ambassador agent").** Build exactly that item. If none is named, propose the
> dependency-respecting default from `ROADMAP-V1.md` §"Suggested ordering" and ask.
>
> **Hold these, every item, without exception:**
> - **The seven principles (MIND-PALACE-V1 Part II)** — especially: model advises / code
>   acts; make illegal states unrepresentable (prefer a type that can't express the wrong
>   thing over a check that detects it); put each check at the lowest tier that can handle
>   it; the firewall (`observed` never feeds the mirror or baselines; the dreamer reads
>   `authored` only via `MirrorView`).
> - **The boundaries that never move (Part VII)** — the Constitution + golden set are
>   human-only; the core never egresses; no agent holds live send/pay credentials; every
>   outward action is gated; consequential advice defers.
> - **The verification discipline** — write tests as you build, in the right
>   `tests/<category>/` home (`test-organization.md`); the `integrity/` suite is a
>   non-skippable gate; new invariants get the right assurance tier (structural > static >
>   guard > property-test). Anything that touches the attestation chain or provenance is
>   `integrity/`.
> - **The build/owner boundary** — you write code, dev-mode/mock tests, policy-as-code,
>   and runbook docs. You do NOT run production Vault ops, apply Terraform, install
>   daemons, authenticate anything, or place production private keys. Those go in the
>   runbook for the owner to run.
> - **Checkpoint discipline** — each item is a checkpoint boundary: build, verify (report
>   test counts before/after), append a terse PROGRESS.md entry (built / verified /
>   owner-deferred / next), then STOP and hand off. Do not chain items in one session if
>   context tightens.
>
> **The one cross-track dependency that is NOT optional:** the **drift gauge (A1)** must
> exist before **recursive dreaming (R3 / C2)** is built. Recursion without the gauge is
> the documented self-amplifying-drift failure mode. If asked to build R3 and A1 is not
> done, STOP and surface it.
>
> **Feature flags stay as they are:** the dream R&D track is flag-OFF; self-mod is
> fail-closed OFF; nothing autonomously proposes. Building an item does not flip its flag
> — wiring into the live path / cron is a separate, deliberate, owner-approved step.
>
> **Per-item specifics:** the design note named in `ROADMAP-V1.md` for the item is the
> spec. Reconcile it against what is actually built before writing code; if the note
> conflicts with the live system, STOP and surface it rather than silently reconciling.
>
> When the item is built, verified, checkpointed — stop. The owner starts the next fresh
> session for the next item.

---

## Track → design-note quick map (for whoever drives the sessions)

| Item | Design note(s) |
|------|----------------|
| A1 drift gauge | `alignment-subsystem.md` §2,4; `WHITEPAPER-FORMAL-PROPERTIES.md` (G4) |
| A2 structural detection | `alignment-subsystem.md` §2 |
| A3 auditor agent | `nervous-system-and-ambassador.md` §2 |
| A4 tamper tripwire | `nervous-system-and-ambassador.md` §1 |
| A5 alignment-steering self-mod | `alignment-subsystem.md` §5 |
| B1–B5 Ambassador | `ambassador-as-reasoning-agent.md` (authoritative); `ambassador-interpretation-and-flow.md`; `nervous-system-and-ambassador.md` §4 |
| C1 R2 utility | `dream-phase-rnd-charter.md` |
| C2 R3 recursion | `recursive-dreaming-bounded-by-grounding.md` (after A1) |
| C3 R4 cross-source | `dream-phase-rnd-charter.md`; `observed-iot-and-cross-source-synthesis.md` |
| C4 R5 curated dreaming | `dreaming-on-curated-graphs.md` |
| D1 observed ingest | `observed-iot-and-cross-source-synthesis.md` §1 |
| D2 correlator | `observed-iot-and-cross-source-synthesis.md` §2 |
| D3 advisor agents | `observed-data-and-the-assistant-tier.md`; `skills-and-scope.md` |
| E1 podman gap | `runbook.md` → "Sandbox runtime" |
| E2 WASM sandbox | `wasm-sandbox-runtime.md` (after E1) |
| E3 voice | BUILD-SPEC §20.11 |
| E4 formal gaps | `WHITEPAPER-FORMAL-PROPERTIES.md` (G4/G9/G10/G11) |
| F1 synthetic corpora | `simulation-harness-and-reasoning-probes.md` §1b |
| F2 simulation harness | `simulation-harness-and-reasoning-probes.md` §1 |
| F3 mock-approver gate test | `simulation-harness-and-reasoning-probes.md` §1d |
| F4 drift trajectory asserts | `simulation-harness-and-reasoning-probes.md` §1c (after A1) |
| F5 logic-puzzle probes | `simulation-harness-and-reasoning-probes.md` §2 |
| F6 literary structural extraction | `literary-interpretation-probes.md` §4 (needs R5 CuratedView) |
| F7 literary grounding precision | `literary-interpretation-probes.md` §3,5 (THE architecture signal) |
| F8 literary theme recall | `literary-interpretation-probes.md` §6 |
| F9 dreamer quality suite (signal-vs-noise) | `dreamer-quality-suite-evaluation.md` (bind DreamerAdapter; THRESH joins harness tuning; wire rate_blind for the value claim) |

---

## PROGRESS.md — add a forward-roadmap pointer block

```markdown
## Forward roadmap (post-base-build, see docs/ROADMAP-V1.md)
Base build (Phases 0–10) COMPLETE + live. Forward layer organized as six tracks:
- A — The Senses: drift gauge → structural detection → auditor → tamper tripwire → alignment-steering self-mod.
- B — The Voice: the Ambassador — a reasoning agent that is computationally light (a mind that uses deterministic tools), read+propose, delegates heavy work, contextual updates (expected + earned interruptions), transparent about effort in plain language + text interaction.
- C — The Subconscious: dream R&D R2 (utility) → R3 (recursion, AFTER A1) → R4 (cross-source) → R5 (curated dreaming).
- D — The World: observed/IoT ingest → correlator → advisor agents (assistant tier; firewall holds).
- E — Hardening: close the podman empirical gap → WASM sandbox; optional voice; close formal gaps G4/G9/G10/G11.
- F — Testing & Tuning: synthetic corpora → simulation harness (trajectory asserts, mock-approver refusal) → logic-puzzle + literary probes (grounded interpretation = the grounding stress test). The baseline-tuning instrument.
Cross-track rule (non-optional): the drift gauge (A1) precedes recursive dreaming (R3/C2). All else is owner preference; the honest first move is to use the system. Full map: docs/MIND-PALACE-V1.md + docs/ROADMAP-V1.md.
```

---

## Track B — full-track session prompt

**Owner override (2026-06-29), THIS TRACK ONLY:** finish all of B1–B5 plus the
cross-cutting refinements in one session, with real wiring, so the owner can start
talking to the system. Do not stop after one sub-item the way other tracks do — the
"one item per checkpoint" rule is explicitly suspended for Track B. Everything else in
the generic prompt above (the seven principles, the boundaries that never move, the
verification discipline, the build/owner boundary, feature-flag discipline) still
applies in full.

> **Fresh builder session — Track B, the Ambassador, build it end to end.**
>
> Re-ground per CLAUDE.md: read `docs/PROGRESS.md` (esp. the A1/F9 entries and the §1
> provenance-spectrum note), `CLAUDE.md`, `CONSTITUTION.md`, `CONVENTIONS.md`,
> `docs/MIND-PALACE-V1.md`, `docs/ROADMAP-V1.md` (Track B section), then the three
> design notes in this precedence order: `ambassador-as-reasoning-agent.md`
> (**authoritative** — corrects "thin dispatcher" to "computationally light, not
> cognitively shallow"; read this one first), `ambassador-interpretation-and-flow.md`
> (§§1–4 are unchanged and give you the concrete conversation loop + integration
> table), `nervous-system-and-ambassador.md` §4 (the read-only/delegate-not-act
> boundary). Where they conflict, the reasoning-agent note wins.
>
> **Mission:** by the end of this session the owner can have a real conversation with
> the system — send a message, get a grounded answer, ask "what have you been doing,"
> ask it to look into something and get a deferred result, and have the exchange land
> in the corpus as `authored-dialogue`. Code + tests + an actual interaction surface,
> not just unit tests of isolated pieces.
>
> ### 0. A structural decision is already made for you — execute it, don't re-derive it
> The provenance-spectrum growth path (`docs/PROGRESS.md` §1 note, confirmed in
> `docs/WHITEPAPER-TECHNICAL.md` line ~62 and `docs/WHITEPAPER.md`) says: when
> `authored-dialogue`/`curated` sources land, `Provenance.AUTHORED` splits into
> `AUTHORED_SOLO` + `AUTHORED_DIALOGUE` and gains `CURATED`; the existing single
> `authored` tag maps to `AUTHORED_SOLO` (conservative); `MIRROR_READABLE` becomes
> `{AUTHORED_SOLO, AUTHORED_DIALOGUE}` (matches the formal spec, which already assumes
> this). **B1 needs `AUTHORED_DIALOGUE`; B4 needs `CURATED`. This session is "when
> those sources land." Do the split now**, not as a separate decision:
> - `core/provenance.py` — replace `AUTHORED` with `AUTHORED_SOLO = "authored-solo"` +
>   `AUTHORED_DIALOGUE = "authored-dialogue"`, add `CURATED = "curated"`. Update
>   `MIRROR_READABLE = frozenset({AUTHORED_SOLO, AUTHORED_DIALOGUE})`. Update the
>   module docstring/comments that describe the old single-class shape.
> - Blast radius is small and already mapped (verified by grep this session, non-test
>   code only): `core/ingest/pipeline.py:39` (`ingest_note` hardcodes
>   `Provenance.AUTHORED` → make it a parameter defaulting to `AUTHORED_SOLO`, since
>   vault notes are solo-authored but B4's curated ingest and a future chat-capture
>   path need to pass a different value through the same chunker); `core/stores/catalog.py`
>   (DDL default `'authored'` + `Provenance.AUTHORED.value` defaults) → `AUTHORED_SOLO`.
>   `core/mirror.py` needs no change — it derives `_ALLOWED` from `MIRROR_READABLE`.
> - Existing LanceDB rows have the literal string `"authored"` already written. This
>   is a same-trust-tier *relabeling* (not a promotion across the §8 firewall — both
>   old and new values are mirror-readable), so a deterministic migration (rewrite
>   `provenance == "authored"` rows to `"authored-solo"` in the vector store + raw
>   catalog) is in scope for you to write and is safe to run against dev/test fixtures
>   directly. Whether to run it against the owner's live `~/.mind-palace` vault data is
>   a production-data mutation — write the migration as a small idempotent script,
>   dry-run it against a copy first, and put the live-run step in the runbook for the
>   owner to execute themselves (build/owner boundary), backed by the existing daily
>   restic snapshot as your safety net. Add/extend tests in `tests/integrity/` (this
>   touches provenance, which is an integrity-tier concern) proving: the split values
>   round-trip, `MIRROR_READABLE` excludes `CURATED`, `MirrorView.project` still raises
>   on a non-MR row, and the migration is idempotent (run twice = same result).
>
> ### 1. What's already built (reuse, don't rebuild)
> - **Gateway/adapter substrate (edge/interface/)** — `protocol.py` (wire format),
>   `adapter.py` (`InterfaceAdapter` protocol + `LocalAdapter`, the private default —
>   "a local app reached over loopback/Tailscale"; `WhatsAppAdapter` stub, opt-in,
>   not your concern), `channel.py` (`GatewayChannel`, the edge-side handoff
>   writer/reader), `gateway.py` (`InterfaceGateway`, polls the adapter, submits to
>   the channel, delivers responses back). All built, all tested, all dormant.
> - **Core-side handoff** — `core/interface.py`: `CoreInbox` reads `requests/`, calls
>   an injected `Handler = Callable[[str], str]`, writes `responses/`.
>   `build_core_inbox()` currently wires the handler straight to
>   `librarian.answer(text).text` — **this is the seam you replace with the
>   Ambassador**. Today nothing drives `CoreInbox.run()`/`process_once()` on a
>   schedule and nothing drives the gateway's `submit_inbound()`/`deliver_responses()`
>   either — **confirmed this session: `scheduler/cron.py` has zero references to
>   interface/gateway/inbox.** That's the real gap behind "the interface gateway is
>   ✅ built" in the roadmap's dependency table — built, never scheduled.
> - **Librarian** (`core/librarian/librarian.py`) — `retrieve()` (defaults to
>   `MIRROR_READABLE`, takes an explicit `provenances=` override — this is exactly the
>   hook B4 needs to read the `CURATED` self-knowledge graph instead), `answer()`
>   (grounded, self-checked), `context_for()` (Constitution-framed messages). Reuse
>   directly; do not reimplement retrieval.
> - **Operational state, read-only, already has the right shape for B3:**
>   `core/attestation/store.py` `AttestationStore` — `all()`, `by_role()`,
>   `chain_for()`, `producers_of()`, `count()` (no delete/mutate method exists — it's
>   already append-only by construction). `ops/ledger.py` `ProposalLedger` — `all()`,
>   `pending()`, `get()` (also has `approve`/`deny`/mutating methods you must NOT
>   expose to the Ambassador). `eval/drift.py` `measure_drift()` /
>   `load_drift_config()` for "is the system healthy." Build a thin read-only wrapper
>   (call it `core/ops_view.py` or similar) exposing only the read methods of these
>   three, the same structural-typing move as `MirrorView` — so the Ambassador holds a
>   type that *cannot* call `approve`/`deny`/`append`, not just a convention not to.
> - **Budgeter** (`scheduler/budget.py`) — `Budgeter.assemble(ContextParts)` exists,
>   is fully tested, and is **wired into zero live agents today** (confirmed by grep:
>   only `core/stores/telemetry.py` references it, for an unrelated reason, plus its
>   own tests). B5 is the *first real wiring* of the budgeter into a live path — give
>   the Ambassador a `Budgeter` and assemble every turn's context through it
>   (`ContextParts.retrieved` = what B2's retrieve-path pulls, `.history` = rehydrated
>   `authored-dialogue` turns, `.tool_outputs` = B3's narrated operational state when
>   relevant) instead of hand-building messages. This is the literal realization of
>   "agent-judged retrieval within the budgeter ceiling": the Ambassador decides *what*
>   to put in `ContextParts`; `Budgeter` decides what survives the window.
> - **Role/agent pattern** — `core/agent.py` `Agent` (Constitution-framed, tiered,
>   `respond()`), `core/factory/roles.py` `RoleTemplate`/`BASE_ROLES` (the minted-role
>   pattern, scope ceiling). The Ambassador is a **persistent, first-class role**, not
>   a minted one — it belongs in `agents/` (currently an empty reserved scaffold per
>   its own docstring: "Populated Phase 2 onward... see BUILD-SPEC §18"). Give it its
>   own scope (read MirrorView, read CURATED, read the ops-view, propose tasks/notes —
>   never the `run_python` capability, never a write path) rather than reusing
>   `general_conversation`'s empty scope by coincidence — be deliberate about what's
>   in `Ambassador`'s scope and why, matching `RoleTemplate.__post_init__`'s
>   pre-declared-max enforcement if you choose to express it as one.
> - **Router/queue** (`scheduler/router.py`, `scheduler/queue.py`) — `Router.tier_for()`
>   currently has no kind that maps to the pinned tier for *conversation* (only
>   `_ROUTER_KINDS = {route, classify, watchdog}` and `_PINNED_KINDS = {vault_sync}`
>   map to pinned; `_ROUTINE_KINDS` includes `chat`/`converse`/`assistant` mapped to
>   `routine`). The roadmap is explicit the Ambassador runs on the **pinned tier**
>   (always-warm, low-latency). Add a distinct kind (e.g. `"ambassador"`) routed to
>   `config.pinned_model.tier` at `PRIORITY_REACTIVE`, rather than overloading
>   `chat`/`converse` (those names are used by existing tests/paths at `routine` —
>   don't change their meaning). The delegated path (B2c, "task → gate → queue") is a
>   `JobQueue.enqueue()` of a real job kind (`dream`/`curate`/etc., or a new generic
>   one if the task doesn't fit an existing kind) at whatever tier *that work* needs —
>   the Ambassador's own turn stays on the pinned tier regardless.
>
> ### 2. Build B1–B5 against the conversation loop already specified
> `ambassador-interpretation-and-flow.md` §3 gives you the exact loop — implement it
> literally:
> ```
> 1. Owner message arrives via the gateway/CoreInbox handoff.
> 2. Ambassador (pinned tier) reasons about intent — deterministic floor for the
>    obvious cases (a clear retrieval keyword, a clear "what have you been doing"),
>    model-earned reasoning for ambiguous/compound requests (per the authoritative
>    note §1/§5 — this is NOT a bucket classifier; bucket the cheap cases, reason
>    about the rest):
>    (a) retrieve → Librarian.retrieve over MirrorView/derived → render. Inline.   [B2, B5]
>    (b) status   → the read-only ops-view (attestations/ledger/drift) → render.   [B2, B3]
>    (c) task     → compose a scoped task → ops/gate.py (or the factory's routing-
>                   to-human-gate pattern) → JobQueue.enqueue(). Reply "on it";
>                   result delivered on completion or next turn.                   [B2]
>    (d) capture  → store the message as AUTHORED_DIALOGUE, enqueue ingest through
>                   the (now-parametrized) pipeline. Reply, done.                   [B1, B2]
> 3. Every step emits an attestation (role="ambassador", action=read|propose|capture)
>    via the existing `core/attestation/` machinery — reuse `Attestor`, don't bypass it.
> 4. (c)'s result narration and any unprompted surfacing follow the earned-interruption
>    policy below — never spontaneous noise.
> ```
> - **B1 (interface gateway path).** Wire the missing schedule: a
>   `scheduler/interface.py` (mirror `scheduler/vault_sync.py`'s pattern) that drives
>   `CoreInbox.process_once()` each cron tick, enqueued/dispatched like the other
>   pinned-tier jobs. For the actual "talk to it" surface the owner can use *today*
>   without any operational risk (no daemon install, no Tailscale exposure decision
>   needed to start using it locally): build a small CLI REPL (e.g. `scripts/talk.py`)
>   that drives `LocalAdapter.receive()` / reads `.sent` directly, in-process — this is
>   your primary verification surface and the owner's day-one interaction surface.
>   Document, in the runbook only, the optional next step (a tiny stdlib-only local
>   HTTP front end reachable over Tailscale, following `LocalAdapter`'s existing
>   "loopback/Tailscale" framing) as an owner-operational follow-up, not something you
>   stand up as a daemon in this session (build/owner boundary).
> - **B2 (the Ambassador agent).** The agent class (in `agents/`), the intent step
>   (deterministic floor + model-earned reasoning per the authoritative note — write
>   the floor rules and the model-reasoning fallback as separately testable units),
>   the three inline paths, the one delegated path. The capture path (d) is what
>   closes the loop into `AUTHORED_DIALOGUE` — make sure it goes through the same
>   chunk/embed/store pipeline as vault ingest (parametrized provenance from step 0),
>   not a bespoke writer.
> - **B3 (operational-introspection read scope).** The read-only wrapper from §1
>   above. Must render findings in plain language for the "status" inline path and
>   for effort-narration (below) — never raw internals (tier names, "synthesis-tier
>   job," credentials, plumbing) per the authoritative note §4's contrast example.
> - **B4 (self-knowledge graph).** Ingest `CONSTITUTION.md`, `CONVENTIONS.md`,
>   `docs/*.md`, and `docs/design-notes/*.md` tagged `CURATED`, into the existing
>   `VectorStore` (it's already multi-provenance, single-table — no new store needed,
>   same pattern as the dormant `OBSERVED` schema). The Ambassador's "explain
>   yourself" path is a `Librarian.retrieve(query, provenances={Provenance.CURATED})`
>   call — note this is a **separate, deliberate, non-default** `provenances=`
>   argument, never the `MIRROR_READABLE` default, so curated material never leaks
>   into a mirror-scoped answer and vice versa (the same firewall shape as
>   `dreaming-on-curated-graphs.md`'s `curated ∉ MIRROR_READABLE`, without needing a
>   full `CuratedView` type — that's the dream-R&D track's concern, not yours; a plain
>   `provenances=` filter is sufficient here since this isn't introspective dreaming).
>   Never expose live secrets/keys even when narrating architecture (the note's own
>   caveat).
> - **B5 (selective per-turn retrieval).** Wire `Budgeter` into the Ambassador's
>   context assembly as described in §1 above. The Ambassador *chooses* what goes
>   into `ContextParts` (how much history to rehydrate from `AUTHORED_DIALOGUE`, how
>   many retrieved chunks, whether to include an ops-view summary); `Budgeter` is the
>   one and only thing that enforces the ceiling. Test that an oversized choice still
>   fits (or escalates) rather than silently blowing the window.
>
> ### 3. The two cross-cutting build deltas (apply across B2–B5, per the authoritative note §5)
> - **Effort narration.** One small render template: when the Ambassador delegates a
>   slow task (path c), it tells the owner plainly that it needs to go work, roughly
>   what, and that there will be a wait — in the *plain* register the note gives
>   ("let me dig through your notes and cross-check a few things — give me a bit"),
>   never the *wrong* register ("spawning a synthesis-tier job..."). Backed by B3's
>   read scope, not a new capability — write it as a pure function from "what was
>   delegated" to a plain sentence, and unit-test the register directly (assert it
>   doesn't leak tier names/internal nouns).
> - **Earned-interruption policy.** The Ambassador may surface something unprompted
>   only when it judges the owner would want it raised (a real alarm, a high-
>   confidence finding) — default "earned only," owner-tunable sensitivity. Since the
>   judgment itself is a model call, keep the *policy* (the gate that decides whether
>   to deliver an unprompted message at all, and the default-off/on knob) as plain,
>   testable code, and let only the "is this worth raising" judgment be model-advised
>   — model advises, code still acts on the decision to actually push a message via
>   the gateway.
>
> ### 4. Definition of done — "completely finished," not just "code exists"
> Don't call this done until:
> - The owner (or you, standing in) can run `scripts/talk.py`, have a multi-turn
>   conversation, ask something the corpus can answer (retrieve), ask "what have you
>   been doing" (status), ask it to look into something and get a deferred response
>   (task→gate→queue), and see the exchange land back in the vault store as
>   `authored-dialogue` on the next retrieval. Actually run this, don't just unit-test
>   the pieces in isolation — this is the "interact with the system in a meaningful
>   way" bar the owner asked for.
> - Every new invariant (the provenance split; read-only-ness of the ops-view; the
>   curated/mirror firewall) lives at the right assurance tier per
>   `test-organization.md` (structural > static > guard > property), with
>   provenance-touching tests in `tests/integrity/`.
> - Full logic suite reported before/after (no regressions); ruff clean; import
>   firewall (I2) green; core still reaches no network (the Ambassador is core-side —
>   double check nothing in `agents/` or the new core modules imports `edge`).
> - Feature flags unchanged (dream R&D OFF, self-mod fail-closed OFF) — this track
>   doesn't touch either.
> - `docs/PROGRESS.md` gets a real entry (built/verified/owner-deferred/next, same
>   format as the A1/F9 entries) and `CLAUDE.md`'s "Current phase" marker is updated
>   to reflect Track B done.
>
> ### 5. If you get genuinely stuck on an owner-only decision
> Two candidates surfaced while scoping this (ask via `AskUserQuestion` if they
> actually block you; otherwise pick the stated lean and note it inline):
> - Whether to expose the Tailscale-reachable local UI in this session or leave it as
>   a runbook follow-up (lean: leave it — the CLI REPL is sufficient to meet the
>   "interact with it meaningfully" bar without any operational/security decision).
> - Default earned-interruption sensitivity (a single dial vs. per-category) — the
>   design notes leave this genuinely open (`ambassador-as-reasoning-agent.md` §7).
>   Lean: ship a single owner-tunable knob (off/earned-only/verbose), default
>   earned-only, and leave per-category as a documented future extension rather than
>   building it now (avoids the premature-abstraction trap on an unused axis).
>
> When B1–B5 are built, verified, and checkpointed — stop and hand off as usual.
