"""The shadow runner — the harness's single-config run producer (E2, bp-043 Item 6).

Drives BOTH dream pipelines over ONE `MirrorView` snapshot in one trough window and writes:

  * **claims -> the run ledger** (`core/stores/runledger.py`): phase7 = the community lens (the
    Phase-7 single clusterer, model-free); dream_v2 = the full interpreter panel + the
    evidence-based adjudicator (model-free — the earned model call, step 8 of `dream_v2`, is
    NEVER made here);
  * **registered metric Readings -> the E1 eval store** (`eval/harness/{store,registry}`): the
    built guardrails (`drift_D`, `golden_recall`) and dream_v2's `structural_axes.*`, each keyed
    by this run's unified key (§2.1) so the A/B split is attributable.

The load-bearing property (family-2 discipline): the two pipelines are two derived functors over
ONE raw corpus — the same `corpus_digest` in yields two diffable claim sets out. The whole-plan
falsifier is the live dream surface changing: shadow reads only a `MirrorView` (Invariant 6,
structural firewall) and writes only the ledger + the eval store — NEVER the interpreted/derived
store, and NEVER the `[dream_rnd]` disk flag (dream_v2 is enabled IN-PROCESS via `replace`).

Two reconciliations of the plan's pins, forced by the model-free invariant (§7 Item 6):
  1. `Dreamer.dream_v2` makes a model call (step 8, `self.synthesize`), so the runner runs the
     pipeline STEPS directly (`collect_claims` + `adjudicate`, no `support_of` -> flat grounding,
     no derived read) rather than the method — satisfying §3 Q4 ("persist nothing but ledger rows").
  2. step-10 (the structural snapshot that feeds the A2 axes, §3 Q6) is computed directly into an
     EPHEMERAL scratch `SnapshotStore` (NOT the live `structural.duckdb` — no live pollution); the
     runner then reads `latest_structural()` from that scratch store. If it returns nothing the A2
     axes are logged *not-captured* (no silent cap, §2.8), never fabricated.
"""

from __future__ import annotations

import hashlib
import json
import logging
from collections.abc import Sequence
from dataclasses import dataclass, replace
from pathlib import Path
from time import perf_counter
from typing import TYPE_CHECKING, Any

from core.complex.temporal import SnapshotStore, compute_snapshot
from core.dreaming.adjudicator import adjudicate
from core.dreaming.graph import MirrorGraph
from core.dreaming.interpreters import (
    build_structural_context,
    collect_claims,
    community_interpreter,
)
from core.mirror import MirrorView, RowSource
from core.stores.runledger import RunLedger, polarity_and_flag
from eval.drift import DriftConfig, drift_from_report, load_drift_config
from eval.golden import (
    GoldenQuery,
    Retriever,
    evaluate,
    load_baseline,
    load_golden_set,
)
from eval.harness import registry
from eval.harness.store import EvalKey, EvalResultsStore, Reading

if TYPE_CHECKING:
    from config.loader import Config

_log = logging.getLogger(__name__)

# The guardrail metrics the runner references — BY REGISTERED NAME (E1's registry is the namespace,
# no ad-hoc metric). `structural_axes.<axis>` is written per the §3 Q6 pin (put() does not gate on
# registration; a follow-up should register the family — see the journal spec-fidelity note).
_GOLDEN_RECALL = "golden_recall"
_DRIFT_D = "drift_D"

_SPEC_PREFIX = "shadow-runner/v1"


def _corpus_digest(rows: list[dict[str, Any]]) -> str:
    """A deterministic Merkle root over the snapshot's chunk digests (§3 Q2 / §8): the exact corpus
    state a run scored. Leaves are `sorted(set(row['digest']))` (sorted -> deterministic); an odd
    level duplicates its last node. Two pipelines over one snapshot get the SAME digest — the A/B is
    provably comparable."""
    leaves = sorted({str(r.get("digest", "")) for r in rows})
    if not leaves:
        return hashlib.sha256(b"").hexdigest()
    level = [hashlib.sha256(x.encode()).hexdigest() for x in leaves]
    while len(level) > 1:
        nxt: list[str] = []
        for i in range(0, len(level), 2):
            a = level[i]
            b = level[i + 1] if i + 1 < len(level) else a
            nxt.append(hashlib.sha256((a + b).encode()).hexdigest())
        level = nxt
    return level[0]


def _config_fingerprint(config: Config) -> str:
    """sha256 of the live value of EVERY registered lever (§3 Q2). Widened (bp-046) from the
    `[dreaming]`-only subset to the registered `[dream_rnd]` levers: a σ-sweep varies
    `dream_rnd.sigma`, which dream_v2 actually reads for the mirror graph (`run()` below,
    `MirrorGraph.build(view, sigma=rnd.sigma)`) — so that value must enter the config identity or
    every grid cell collapses onto one eval-store key and the curve/resumability break (§4).

    The lever set is DERIVED FROM `ops.levers.LEVERS` (the single source of truth), never a
    hardcoded list — so bp-049 widening the registry moves this key with no second edit here.
    Keyed `"<section>.<key>"` so a `[dream_rnd]` key can never collide with a `[dreaming]` one.
    Hashes VALUES (not the manifest policy, bp-047's `resolved_fingerprint()`, which is static
    across a sweep — §4). Both pipelines share one `cfg`, so still ONE fingerprint per run."""
    from ops.levers import LEVERS

    levers = {
        f"{lever.section}.{lever.key}": getattr(getattr(config, lever.section), lever.key)
        for lever in LEVERS.values()
    }
    canon = json.dumps(levers, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canon.encode()).hexdigest()


@dataclass
class ShadowRunner:
    """One snapshot, two runs. Production: `ShadowRunner(ledger).run()` resolves the mirror + eval
    store from config and runs a scratch snapshot store. Tests inject every seam. The guardrail
    `retriever` reads the golden FIXTURE corpus (not the vault — firewall intact); absent,
    guardrails are logged not-captured rather than fabricated."""

    ledger: RunLedger
    store: RowSource | None = None              # the live mirror source; None -> open from config
    eval_store: EvalResultsStore | None = None  # None -> open_eval_store(config)
    snapshots: SnapshotStore | None = None      # scratch A2 store; None -> ephemeral in-memory
    retriever: Retriever | None = None             # golden-fixture retriever; None -> not-captured
    golden: Sequence[GoldenQuery] | None = None
    baseline: dict[str, float] | None = None
    drift_cfg: DriftConfig | None = None
    seed: int = 0

    def run(self, *, config: Config | None = None) -> tuple[str, str]:
        """Execute both pipelines over one MirrorView snapshot; return `(phase7_run_id,
        dream_v2_run_id)`. Model-free; writes only the ledger + the eval store."""
        cfg = config or _get_config()
        store = self.store if self.store is not None else _open_vector_store(cfg)
        eval_store = self.eval_store if self.eval_store is not None else _open_eval_store(cfg)
        snapshots = self.snapshots if self.snapshots is not None else _scratch_snapshots()

        view = MirrorView.project(store)
        rows = view.rows()
        corpus_digest = _corpus_digest(rows)
        config_fingerprint = _config_fingerprint(cfg)

        # dream_v2 enabled IN-PROCESS — never the disk flag (the whole-plan falsifier).
        rnd = replace(cfg.dream_rnd, enabled=True)
        graph = MirrorGraph.build(view, sigma=rnd.sigma)
        edge_count = sum(graph.degree(i) for i in range(graph.n)) // 2
        flagged: set[str] = set()

        # ---- phase7: the community lens (the Phase-7 clusterer, model-free) --------------------
        t0 = perf_counter()
        phase7_claims = community_interpreter(graph, rnd)
        run7 = self.ledger.start_run(
            pipeline="phase7", config_fingerprint=config_fingerprint, corpus_digest=corpus_digest,
            node_count=graph.n, edge_count=edge_count, duration_s=perf_counter() - t0,
            spectral_stats={"sigma": rnd.sigma, "n_claims": len(phase7_claims)})
        for c in phase7_claims:
            pol, defaulted = polarity_and_flag(c.method)
            if defaulted:
                flagged.add(c.method)
            # phase7 claims are un-adjudicated (the single lens does not rank) -> confidence 0.0.
            self.ledger.add_claim(run7, kind=c.method, confidence=0.0, support=c.support,
                                  surface_text=c.statement, polarity=pol)
        self._write_guardrails(eval_store, "phase7", corpus_digest, config_fingerprint,
                               structural=None)

        # ---- dream_v2: the full panel + adjudicator + step-10 (model-free) ---------------------
        t1 = perf_counter()
        ctx = build_structural_context(view, rnd)
        v2_claims = collect_claims(graph, ctx, rnd)
        authored = {str(r.get("digest", "")) for r in rows}
        # No support_of: flat grounding_score — identical to noisy-OR when every ref is an authored
        # leaf (always true for a MirrorView), and it reads NO derived store (isolation).
        entries = adjudicate(v2_claims, authored_digests=authored,
                             agreement_jaccard=rnd.agreement_jaccard)
        # step 10 -> the scratch snapshot store -> the A2 axes (§3 Q6). Never the live store.
        structural: dict[str, float] | None = None
        if snapshots is not None:
            snapshots.write(compute_snapshot(
                ctx.complex, distances=ctx.distances, sbm_k_max=rnd.sbm_k_max,
                hole_min_persistence=rnd.hole_min_persistence,
                thread_min_persistence=rnd.thread_min_persistence))
            structural = snapshots.latest_structural()
        run_v2 = self.ledger.start_run(
            pipeline="dream_v2", config_fingerprint=config_fingerprint, corpus_digest=corpus_digest,
            node_count=graph.n, edge_count=edge_count, duration_s=perf_counter() - t1,
            spectral_stats=structural or {})
        for e in entries:
            for m in e.members:
                pol, defaulted = polarity_and_flag(m.method)
                if defaulted:
                    flagged.add(m.method)
                self.ledger.add_claim(run_v2, kind=m.method, confidence=e.confidence,
                                      support=m.support, surface_text=m.statement, polarity=pol)
        self._write_guardrails(eval_store, "dream_v2", corpus_digest, config_fingerprint,
                               structural=structural)
        self._write_structural_axes(eval_store, "dream_v2", corpus_digest, config_fingerprint,
                                    structural)

        if flagged:
            _log.warning("shadow: %d claim kind(s) had no polarity mapping (defaulted +): %s",
                         len(flagged), sorted(flagged))
        return run7, run_v2

    # -- eval-store writes (bp-042 surface) ---------------------------------------------------
    def _key(self, pipeline: str, corpus_digest: str, config_fingerprint: str) -> EvalKey:
        # spec_hash carries the pipeline (§2.1) so phase7 vs dream_v2 get DISTINCT keys.
        spec = hashlib.sha256(f"{_SPEC_PREFIX}‖{pipeline}".encode()).hexdigest()
        return EvalKey(spec_hash=spec, corpus_ref=corpus_digest,
                       config_fingerprint=config_fingerprint, seed=self.seed)

    def _write_guardrails(self, eval_store: EvalResultsStore, pipeline: str, corpus_digest: str,
                          config_fingerprint: str, *, structural: dict[str, float] | None) -> None:
        """Evaluate the built guardrails (drift D + golden recall) over the golden FIXTURE and write
        keyed Readings. No retriever -> not-captured (no silent cap, §2.8)."""
        if self.retriever is None:
            _log.info("shadow: guardrails not-captured for %s (no retriever injected)", pipeline)
            return
        golden = self.golden if self.golden is not None else load_golden_set()
        baseline = self.baseline if self.baseline is not None else load_baseline()
        drift_cfg = self.drift_cfg if self.drift_cfg is not None else load_drift_config()
        report = evaluate(golden, self.retriever)
        drift = drift_from_report(report, baseline, drift_cfg, structural=structural)
        key = self._key(pipeline, corpus_digest, config_fingerprint)
        eval_store.put(Reading(key=key, metric_name=_GOLDEN_RECALL, value=report.recall_at_k,
                               type_tag=registry.get(_GOLDEN_RECALL).type_tag))
        eval_store.put(Reading(key=key, metric_name=_DRIFT_D, value=drift.drift,
                               type_tag=registry.get(_DRIFT_D).type_tag))

    def _write_structural_axes(self, eval_store: EvalResultsStore, pipeline: str,
                               corpus_digest: str, config_fingerprint: str,
                               structural: dict[str, float] | None) -> None:
        """dream_v2's A2 axes as keyed Readings (§3 Q6). Nothing captured -> logged not-captured
        (the bp-045/E5(A2) runtime cross-dep, §12) rather than a silent zero."""
        if not structural:
            _log.info("shadow: structural_axes.* not-captured for %s (no A2 snapshot)", pipeline)
            return
        key = self._key(pipeline, corpus_digest, config_fingerprint)
        for axis, value in structural.items():
            eval_store.put(Reading(key=key, metric_name=f"structural_axes.{axis}",
                                   value=float(value), type_tag="Inv"))


# -- lazy production resolvers (kept out of module import so the isolation scan stays clean) ------


def _get_config() -> Config:
    from config.loader import get_config
    return get_config()


def _open_vector_store(cfg: Config) -> RowSource:
    from core.stores.vectorstore import open_vector_store
    return open_vector_store(cfg)


def _open_eval_store(cfg: Config) -> EvalResultsStore:
    from eval.harness.store import open_eval_store
    return open_eval_store(cfg)


def _scratch_snapshots() -> SnapshotStore:
    """An EPHEMERAL in-memory snapshot store — the shadow run's step-10 target. NEVER the live
    `structural.duckdb` (that would pollute the longitudinal series); the A2 axes are read straight
    back from this instance."""
    return SnapshotStore(Path(":memory:"))
