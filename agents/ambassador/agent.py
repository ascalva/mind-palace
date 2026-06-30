"""The Ambassador — the conversational front door (Track B; ambassador-as-reasoning-agent.md).

A **reasoning agent that is computationally light** (note §0): it genuinely reasons about each
message (the intent step), but holds no heavy work inline — it answers from already-grounded
material on the always-warm pinned tier, and *delegates* anything expensive to the async
scheduler. "Wide window, narrow hands": it can read the authored mirror, the curated
self-knowledge graph, and the operational state, but its authority is **read + propose, never
write + act** (nervous-system-and-ambassador.md §4). Every step is attested.

The five paths (ambassador-interpretation-and-flow.md §3, split by which graph retrieval reads):
  RETRIEVE → the authored mirror → grounded answer (inline).            [B2, B5]
  EXPLAIN  → the CURATED self-knowledge graph → grounded answer (inline). [B2, B4]
  STATUS   → the read-only ops-view, narrated in plain language (inline). [B2, B3]
  TASK     → compose a scoped task → gate → queue; narrate the effort.    [B2]
  CAPTURE  → (the owner's message is stored as authored-dialogue) → ack.  [B1, B2]

Context for the inline answers is assembled through the §13 budgeter (B5): the Ambassador
*chooses* what to put in `ContextParts` (which chunks, how much history); the budgeter is the
one thing that enforces the window — "agent-judged retrieval within the budgeter ceiling".
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field

from agents.ambassador.intent import CLASSIFIER_ROLE, Intent, classify
from agents.ambassador.policy import InterruptionPolicy, narrate_effort, topic_of
from core.attestation import Attestor
from core.constitution import Message, frame_context
from core.dreams_view import DreamsView
from core.factory.roles import RoleTemplate
from core.ingest.dialogue import DialogueCapture
from core.librarian import Librarian, Retrieval
from core.ops_view import OpsView
from core.provenance import MIRROR_READABLE, Provenance
from core.selfcheck import SelfCheck, Source, self_evaluate
from scheduler.budget import BudgetedContext, Budgeter, ContextParts

AMBASSADOR_ROLE = (
    "You are the Ambassador of the owner's sealed personal mind-palace — the voice they talk "
    "to. You are a mirror onto their own mind, not an oracle (Constitution §III.2): reflect "
    "what they actually wrote, hold interpretive claims loosely, and let them draw the "
    "conclusions — the judgment is theirs.\n\n"
    "Ground every substantive claim in the retrieved notes below and cite them by title in "
    "double brackets, e.g. [[note title]]. Never invent notes, quotes, facts, or citations. "
    "When their notes don't cover something, say so plainly instead of guessing.\n\n"
    "Be concise and warm; surface options and tradeoffs, not directives. On health, financial, "
    "or legal matters be substantive and honest about uncertainty, but defer the final decision "
    "to the owner and a qualified professional (Constitution §III.3)."
)

# The Ambassador is a PERSISTENT, first-class role (not a minted one). Its scope is DELIBERATE:
# the empty set — it holds NO executable capability (no `run_python`), and read+propose is not a
# tool capability at all (it is the typed handles it is *given*: MirrorView/Librarian, the
# curated read, the OpsView, the propose-task seam). Expressed as a RoleTemplate so the §10
# scope-ceiling check (`scope ⊆ PRE_DECLARED_MAX`) guards it for free.
AMBASSADOR_TEMPLATE = RoleTemplate(
    name="ambassador",
    prompt_fragment=AMBASSADOR_ROLE,
    default_tier="router",          # the always-warm pinned slot (note §2b)
    scope=frozenset(),              # read + propose only — never write, never run_python
)

_CAPTURE_INTENTS = frozenset({Intent.RETRIEVE, Intent.TASK, Intent.CAPTURE})  # owner's-mind turns


@dataclass(frozen=True)
class DeliveredResult:
    """A completed delegated task's result, ready to surface as an EXPECTED update."""

    ref: str
    topic: str
    text: str


@dataclass(frozen=True)
class Turn:
    reply: str
    intent: Intent
    sources: tuple[Retrieval, ...] = ()
    check: SelfCheck | None = None


def _format_chunk(r: Retrieval) -> str:
    return f"[[{r.title}]]\n{r.text}"


@dataclass
class Ambassador:
    server: object                         # ModelServer-like: .chat(tier, messages, **kw) -> str
    librarian: Librarian
    ops_view: OpsView
    budgeter: Budgeter
    dreams_view: DreamsView | None = None   # the INTERPRETED layer, mirror-not-oracle (DREAMS path)
    tier: str = "router"                   # the pinned tier (always warm — note §2b)
    capture_sink: DialogueCapture | None = None
    attestor: Attestor | None = None
    # B2c delegation seam (injected by the scheduler-layer wiring, which owns the queue/gate —
    # the Ambassador never imports the scheduler, keeping it pure + testable):
    delegate: Callable[[str, str], str] | None = None          # (query, conversation) -> task ref
    pending_results: Callable[[str], list[DeliveredResult]] | None = None  # completed → surface
    interruption: InterruptionPolicy = field(default_factory=InterruptionPolicy)
    role_prompt: str = AMBASSADOR_ROLE
    history_max_turns: int = 6
    _history: dict[str, list[Message]] = field(default_factory=dict)
    _surfaced: set[str] = field(default_factory=set)

    # --- the turn -----------------------------------------------------------------------------
    def respond(self, text: str, *, conversation: str = "default") -> Turn:
        prefix = self._surface(conversation)            # expected updates + earned interruptions
        intent = classify(text, chat=self._classify_chat)
        reply, sources, check = self._dispatch(intent, text, conversation)
        if intent in _CAPTURE_INTENTS and self.capture_sink is not None:
            # Close the capture loop: the owner's message becomes authored-dialogue (note §4).
            self.capture_sink.capture(text, conversation=conversation)
        self._remember(conversation, text, reply)
        full = f"{prefix}\n\n{reply}".strip() if prefix else reply
        return Turn(reply=full, intent=intent, sources=sources, check=check)

    def handler(self, text: str) -> str:
        """The `CoreInbox` Handler: text -> reply text (single default conversation)."""
        return self.respond(text).reply

    # --- dispatch -----------------------------------------------------------------------------
    def _dispatch(self, intent: Intent, text: str, conversation: str):
        if intent is Intent.RETRIEVE:
            return self._answer(text, conversation, provenances=MIRROR_READABLE)
        if intent is Intent.EXPLAIN:
            return self._answer(text, conversation, provenances={Provenance.CURATED})
        if intent is Intent.STATUS:
            self._attest("read")
            return self.ops_view.narrate(), (), None
        if intent is Intent.DREAMS:
            self._attest("read")
            return self._reflect_dreams(), (), None
        if intent is Intent.TASK:
            return self._delegate(text, conversation), (), None
        # CAPTURE: the storing happens in respond(); here we just acknowledge.
        return "Noted — I've saved that to your corpus.", (), None

    def _answer(self, text: str, conversation: str, *, provenances):
        """RETRIEVE / EXPLAIN: reuse the Librarian's retrieval, assemble through the budgeter
        (B5), render on the pinned tier, and self-check grounding before returning."""
        retrievals = self.librarian.retrieve(text, provenances=provenances)
        budgeted = self._assemble(text, retrievals, conversation)
        output = self.server.chat(self.tier, budgeted.messages)
        sources = [Source(title=r.title, digest=r.digest) for r in retrievals]
        check = self_evaluate(output, sources=sources)
        self._attest("read", input_hashes=[r.digest for r in retrievals if r.digest])
        if not check.passed:
            # Calibrated honesty (Constitution §III.1): flag, don't hide, an ungrounded answer.
            output += ("\n\n(Heads up — I may have referenced something I couldn't fully ground "
                       "in your notes; take that part with a grain of salt.)")
        return output, tuple(retrievals), check

    def _assemble(self, text: str, retrievals: list[Retrieval],
                  conversation: str) -> BudgetedContext:
        """B5: the Ambassador chooses what goes in ContextParts; the budgeter enforces the
        window (trims retrieval → history → tool, or escalates — never a silent overflow)."""
        parts = ContextParts(
            role=self.role_prompt,
            task=text,
            retrieved=tuple(_format_chunk(r) for r in retrievals),
            history=tuple(self._history.get(conversation, [])),
        )
        return self.budgeter.assemble(parts)

    def _delegate(self, text: str, conversation: str) -> str:
        """TASK: compose a scoped task → gate → queue (the injected seam), then narrate the
        effort in plain language. Never executes the work itself — model advises, code acts."""
        if self.delegate is not None:
            self.delegate(text, conversation)
        self._attest("propose")
        return narrate_effort(topic_of(text))

    def _reflect_dreams(self) -> str:
        """DREAMS: reflect the INTERPRETED layer (dreams + findings) back, mirror-not-oracle.
        Read-only — the Ambassador can never write the interpreted layer through the view."""
        if self.dreams_view is None:
            return ("I haven't started looking for patterns across your notes yet — that runs in "
                    "the background once there's a corpus to dream over.")
        return self.dreams_view.narrate_recent()

    # --- surfacing (expected updates + earned interruptions) ----------------------------------
    def _surface(self, conversation: str) -> str:
        out: list[str] = []
        # 1. Results the owner explicitly asked for = EXPECTED updates → always delivered.
        if self.pending_results is not None:
            for r in self.pending_results(conversation):
                if r.ref in self._surfaced:
                    continue
                self._surfaced.add(r.ref)
                topic = f" about {r.topic}" if r.topic else ""
                out.append(f"Earlier you asked me to look into something{topic}. "
                           f"Here's what I found:\n{r.text}")
        # 2. Unprompted findings (a real drift alarm) → only if the policy admits (note §3).
        report = self.ops_view.drift_report()
        worth_raising = report is not None and not report.within_tolerance
        if worth_raising and self.interruption.admits(True):
            out.append("Before we go on — I've drifted a little further from my baseline than "
                       "I'd like. You may want to take a look when you have a moment.")
        return "\n\n".join(out)

    # --- helpers ------------------------------------------------------------------------------
    def _classify_chat(self, text: str) -> str:
        return self.server.chat(self.tier, frame_context(CLASSIFIER_ROLE, text))

    def _remember(self, conversation: str, text: str, reply: str) -> None:
        h = self._history.setdefault(conversation, [])
        h.append({"role": "user", "content": text})
        h.append({"role": "assistant", "content": reply})
        cap = self.history_max_turns * 2
        if len(h) > cap:
            del h[: len(h) - cap]

    def _attest(self, action: str, *, input_hashes=()) -> None:
        if self.attestor is not None:
            self.attestor.emit(agent_role="ambassador", action=action,
                               input_hashes=list(input_hashes))
