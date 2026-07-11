"""The Ambassador — the conversational front door (Track B / the Voice).

A reasoning agent that is computationally light: it reasons about intent, answers from
already-grounded material on the pinned tier, reads its own operational state, captures the
dialogue as `authored-dialogue`, and delegates heavy work to the async scheduler — read +
propose, never write + act. See `agent.py` for the full design.
"""

from __future__ import annotations

from agents.ambassador.agent import (
    AMBASSADOR_ROLE,
    AMBASSADOR_TEMPLATE,
    Ambassador,
    DeliveredResult,
    Turn,
)
from agents.ambassador.intent import Intent, classify, classify_floor
from agents.ambassador.policy import InterruptionPolicy, Sensitivity, narrate_effort
from config.loader import Config

__all__ = [
    "AMBASSADOR_ROLE",
    "AMBASSADOR_TEMPLATE",
    "Ambassador",
    "DeliveredResult",
    "Intent",
    "InterruptionPolicy",
    "Sensitivity",
    "Turn",
    "build_ambassador",
    "classify",
    "classify_floor",
    "narrate_effort",
]


def build_ambassador(config: Config | None = None, *, delegate=None, pending_results=None,
                     server=None, embedder=None, store=None, drift=None,
                     derived=None) -> Ambassador:
    """Wire an Ambassador against the real configured stores + models.

    Delegation (the gate→queue seam + completed-result surfacing) is INJECTED by the
    scheduler-layer wiring (`scheduler/interface.py`), which owns the queue — the Ambassador
    never imports the scheduler, so this base build leaves `delegate`/`pending_results` as
    passed (None → TASK still attests + narrates effort, just enqueues nothing).

    `server`/`embedder`/`store` are injectable so the offline CLI + tests can swap the two
    model-backed pieces for deterministic stand-ins without touching the real machinery. The
    ONE vector store is shared by the librarian (reads) and the dialogue capture (writes) so a
    captured turn is immediately retrievable. `drift` is an optional bound DriftReport reading
    for the ops-view (None per-chat — drift is measured by a separate job, not on every turn)."""
    from agents.ambassador.policy import InterruptionPolicy, parse_sensitivity
    from config.loader import get_config
    from core.attestation import build_attestor
    from core.attestation.store import open_attestation_store
    from core.dreams_view import DreamsView
    from core.ingest.dialogue import DialogueCapture
    from core.ingest.embed import build_embedder
    from core.librarian import Librarian
    from core.models import build_model_server
    from core.ops_view import OpsView
    from core.stores.catalog import VaultCatalog
    from core.stores.derived import open_derived_store
    from core.stores.rawstore import RawStore
    from core.stores.vectorstore import open_vector_store
    from core.verdict.apply import OwnerKeyMissing, build_verdict_receiver
    from core.verdict.dispositions import open_disposition_store
    from ops.ledger import open_ledger
    from scheduler.budget import Budgeter

    cfg = config or get_config()
    amb = cfg.ambassador
    server = server or build_model_server(cfg)
    embedder = embedder or build_embedder(cfg)
    store = store if store is not None else open_vector_store(cfg)
    attestor = build_attestor(cfg)
    ops_view = OpsView.over(open_attestation_store(cfg), open_ledger(cfg),
                            drift=(lambda: drift) if drift is not None else None)
    # The interpreted view is the ACTIVE projection: dreams the owner verdicted `wrong`/`noise` are
    # dropped from surfacing (build plan Item 4b-apply; ingest-identity §6).
    dispositions = open_disposition_store(cfg)
    dreams_view = DreamsView.over(derived if derived is not None else open_derived_store(cfg),
                                  dispositions=dispositions)
    # Inbound verdict transport (R7): wire the verify+apply receiver only if the owner key is
    # placed; else the Ambassador has no verdict channel (fail-SAFE — a missing key must not break
    # the whole Voice). The CLI (scripts/verdict.py) is the primary transport surface either way.
    try:
        verdict_transport = build_verdict_receiver(cfg)
    except OwnerKeyMissing:
        verdict_transport = None
    raw = RawStore(cfg.paths.raw_store)
    capture = DialogueCapture(raw=raw, store=store, embedder=embedder,
                              catalog=VaultCatalog(cfg.paths.vault_catalog), attestor=attestor)
    return Ambassador(
        server=server,
        librarian=Librarian(server=server, embedder=embedder, store=store, raw=raw,
                            k=amb.retrieval_k),
        ops_view=ops_view,
        dreams_view=dreams_view,
        budgeter=Budgeter(window=cfg.pinned_model.num_ctx),
        tier=cfg.pinned_model.tier,
        capture_sink=capture,
        attestor=attestor,
        delegate=delegate,
        pending_results=pending_results,
        verdict_transport=verdict_transport,
        interruption=InterruptionPolicy(parse_sensitivity(amb.interruption_sensitivity)),
        history_max_turns=amb.history_max_turns,
    )
