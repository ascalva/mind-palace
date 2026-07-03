# ── Family 1 + family 5 boundary · symbols in docs/NOTATION.md ──
# OBJECT:    the reversible-write proposal composer — tailors a class-2 effect by READING a
#            MirrorView (authored-only) and emitting a ProposedEffect (hands-and-the-effector-
#            layer.md §7: "the effector tailors a PROPOSAL, never a sent artifact").
# INVARIANT: the tailoring read is a MirrorView (observed/curated exhaust is unrepresentable, I6);
#            this module can only PROPOSE — it has no stage/send path and constructs no Effect.
# ENFORCED:  structural — the tailor is TYPED to receive a MirrorView (the firewall by type); the
#            return is a ProposedEffect (pure data); the class is asserted REVERSIBLE, fail-closed;
#            no network/stage/credential import exists here.
"""Compose a reversible-write proposal, tailored to the owner (Track G, item G5).

This is the point §7 names: an effector that writes in the owner's voice must read a *model of the
owner* — and that read is a `MirrorView` (authored-only; the firewall holds even here), with the
**output a proposal, never a sent artifact**. So the whole of this module is: read the mirror,
tailor a body, return a `ProposedEffect`. There is deliberately no send, no stage, and no `Effect`
construction here — composing the proposal ("the model advises") is strictly separate from acting
on it ("code acts", after the gate: `ops/effect_gate` → `ops/effect_ledger` → the edge effector).

Two boundaries make the separation structural, not a convention:

  * **The firewall.** `tailor` is typed `Callable[[MirrorView, str], str]`. A `MirrorView` cannot
    hold observed or curated rows (`core/mirror.py` raises), so a steered composer physically
    cannot tailor a reply from third-party exhaust — only from the owner's own authored notes.
  * **Propose, never send.** The return type is `ProposedEffect` — an actuator name + allowlisted
    string params and nothing more (no send field exists to set). The class is asserted REVERSIBLE
    against the catalog (fail-closed): this composer proposes reversible writes and nothing else.

The proposal then rides the ordinary path: a human approves it (LIGHT, `EffectLedger.approve`), an
`Effect` is constructed under that approval, and the edge effector STAGES a draft the owner can
delete (`edge/effectors/writes.py`). Sending that draft is a *different*, irreversible, full-gated
act (G6) — never something this module can reach.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from core.mirror import MirrorView
from ops.effect_catalog import get_actuator
from ops.effect_gate import ProposedEffect
from ops.effects import ReversibilityClass

# A tailor turns (authored context, request) into drafted body text. It only ADVISES — its output
# is wrapped into a proposal and never sent. The context it sees is a MirrorView, so it cannot read
# anything but the owner's authored notes (the firewall, by type).
Tailor = Callable[[MirrorView, str], str]


class NotAReversibleWriteError(ValueError):
    """A non-reversible actuator was handed to the reversible-write proposer (fail-closed): sensing
    has its own path (`core/sensing.py`) and irreversible sends are composed + gated elsewhere (G6),
    never proposed here where approval is only LIGHT."""


def _require_reversible(actuator: str) -> None:
    spec = get_actuator(actuator)               # fail-closed on an uncataloged hand
    if spec.reversibility is not ReversibilityClass.REVERSIBLE:
        raise NotAReversibleWriteError(
            f"actuator {actuator!r} is {spec.reversibility.name}, not REVERSIBLE — the reversible-"
            f"write proposer refuses it (§3 class boundary)"
        )


def _grounded_default_tailor(mirror: MirrorView, request: str) -> str:
    """A model-free tailor for tests / cold paths: a short body that says, honestly, it is grounded
    in the owner's own notes and awaiting review. Deterministic — no model, no network. A real
    deployment injects `model_tailor` for a voiced draft; both read the SAME MirrorView."""
    n = len(mirror)
    grounding = f"(drafted from {n} of your notes)" if n else "(no notes matched; general draft)"
    return f"Draft re: {request.strip()} {grounding}\n\n[awaiting your review — not sent]"


@dataclass
class ReversibleWriteProposer:
    """Composes class-2 (reversible) effect proposals. Holds only a `tailor` (advice); it never
    holds a store handle, a credential, or a send path. Every method returns a `ProposedEffect`."""

    tailor: Tailor = _grounded_default_tailor

    def propose_draft_reply(
        self, *, to: str, subject: str, request: str, mirror: MirrorView, rationale: str = "",
    ) -> ProposedEffect:
        """Propose a DRAFT reply, its body tailored from the owner's authored notes (`mirror`). The
        result is a proposal — never a sent artifact. `mirror` is a `MirrorView`, so the tailoring
        cannot draw on observed/curated exhaust (the firewall). Validated against the catalog via
        `.resolve()` before return (fail-closed on any bad param)."""
        _require_reversible("draft_reply")
        body = self.tailor(mirror, request)
        proposal = ProposedEffect(
            actuator="draft_reply",
            params=(("body", body), ("subject", subject), ("to", to)),
            rationale=rationale or f"drafted reply re: {request[:120]}",
        )
        proposal.resolve()      # catalog-validate: a malformed proposal never leaves here
        return proposal

    def propose(
        self, actuator: str, params: dict[str, str], *, rationale: str = "",
    ) -> ProposedEffect:
        """Propose any cataloged reversible write (calendar_hold, stage_file, …) from explicit
        params. No tailoring read — use `propose_draft_reply` for a voiced body. Fail-closed on a
        non-reversible actuator or any param outside the catalog's closed allowlist."""
        _require_reversible(actuator)
        proposal = ProposedEffect(
            actuator=actuator,
            params=tuple(sorted((str(k), str(v)) for k, v in params.items())),
            rationale=rationale,
        )
        proposal.resolve()
        return proposal


def model_tailor(server: object, *, tier: str = "routine", max_notes: int = 12) -> Tailor:
    """A tailor backed by the local model, reading the owner's authored notes to draft in their
    voice. The model only ADVISES: its output is a proposal body wrapped into a `ProposedEffect` and
    never sent. It sees a `MirrorView` (authored-only) — never observed exhaust, never a credential.

    Parsing is forgiving; an empty reply degrades to the grounded default (honest, not a fabricated
    draft). Lazy about the model interface (duck-typed `.chat`) so this module imports no server."""
    from core.constitution import frame_context

    role = (
        "You draft a reply in the owner's own voice, grounded ONLY in the notes below. Write the "
        "body text and nothing else — no headers, no 'Subject:', no commentary. This is a DRAFT "
        "for the owner to review and is never sent by you."
    )

    def tail(mirror: MirrorView, request: str) -> str:
        rows = mirror.rows()[:max_notes]
        context = "\n\n".join(f"[[{r.get('title', '')}]]\n{r.get('text', '')}" for r in rows)
        messages = frame_context(role, request, context_blocks=[context] if context else None)
        out = str(server.chat(tier, messages)).strip()   # type: ignore[attr-defined]
        return out or _grounded_default_tailor(mirror, request)

    return tail
