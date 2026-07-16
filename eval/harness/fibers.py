"""The σ-fibers consumer — per-claim persistence over the retained per-σ series (FB-1, bp-050).

A derived, read-only, MODEL-FREE consumer, dual to bp-049's `select`: the SELECTION consumer
collapses the σ-family to one value; this RETENTION consumer scores each content-addressed claim
across it. Design: `docs/design-notes/sigma-fibers-and-multiscale-dreaming.md` §2.1–§2.4 (RATIFIED;
math held verbatim, never re-derived here). Zero schema change — it reads two existing stores and
writes new keyed readings into a third.

Three layers, exactly as the ratified note stages them (§2.4):

  1. **Reconstruct the cell→σ join, model-free (§2.4.1).** `dream_runs.config_fingerprint` is a
     sha256 — you cannot read σ out of it, and the sweep engine held the map only in memory
     (`DriveResult.fp_to_value`). We REGENERATE it: `shadow._config_fingerprint` is a pure function
     of config, so for a declared grid we recompute `fp(modify(base, sigma=σ_i))` per σ_i and join.
     **Pin (§2.4.1):** the fingerprint hashes EVERY registered lever, so the reconstruction is only
     valid under the same lever registry + base config as the drive night. We record (grid, base
     fingerprint, lever-registry hash) into the fibers evidence at run time, and REFUSE fail-closed
     when a supplied `expected_registry_hash` disagrees with the live one — a bp-046-widening would
     otherwise silently re-key. We reuse the DRIVE's own `_config_fingerprint` + `_modify_config`
     so the reconstruction is byte-exact, not a lookalike.

  2. **The per-claim layer reads the RUN LEDGER (§2.4.2).** Group `dream_claims` by `claim_id`
     across the joined cells, per pipeline; compute `(pers, hull, gap)` per claim (§2.3). Output is
     a report artifact (`ClaimFiber`), never a new store or a DreamLogEntry field (parked SF-d).

  3. **The aggregate layer writes the EVAL STORE (§2.4.3).** Distribution summaries as keyed
     readings — `sigma_persistence.{mean,p50,max,frac_ge_strong,n_claims}` — keyed by
     `EvalKey(spec_hash, corpus_ref, config_fingerprint, seed)` where `spec_hash` carries the
     instrument id+version AND the grid descriptor π (the grid is a battery param, store.py:32),
     `corpus_ref` is the shared Merkle digest, `config_fingerprint` is the BASE config's, `seed=0`.
     Same discipline bp-049 held: consume, write keyed readings, never re-key, never overwrite.

Model-free by construction: arithmetic over two local stores, no model import, no LLM call. I1
untouched — this scores surfacing candidates, it changes no weight/confidence/promotion. `put()`
does NOT gate on registration (the `structural_axes.*` precedent, §4): FB-1 writes
`sigma_persistence.*` readings with `type_tag="Res(sigma)"` BEFORE bp-054 registers them — recorded
in the plan §4 so it never reads as a violation (registration is bp-054's job).
"""

from __future__ import annotations

import hashlib
import json
import logging
from collections.abc import Iterable, Sequence
from dataclasses import dataclass, replace
from pathlib import Path
from statistics import mean, median
from typing import TYPE_CHECKING

# The DRIVE's own pure fingerprint function — reused so the reconstruction is byte-exact (§2.4.1).
from core.dreaming.shadow import _config_fingerprint
from eval.harness.store import EvalKey, EvalResultsStore, Reading
from ops.levers import LEVERS, Lever

if TYPE_CHECKING:
    from config.loader import Config
    from core.stores.runledger import RunLedger

_log = logging.getLogger(__name__)

# spec_hash instrument tag (id + version) — the "fibers/v1" of §6/§2.4.3.
_INSTRUMENT = "fibers/v1"

# The result-typing tag (§2.6 Res(π_σ); §4). `put()` does not gate on registration, so this is
# written as-is; bp-054 registers the family and (companion permitting) the tag vocabulary.
_TYPE_TAG = "Res(sigma)"

# θ_strong for `frac_ge_strong` — the §2.5 SF-e PROVISIONAL default. DESCRIPTIVE ONLY: this is a
# distribution summary, NOT the strength→surfacing gate (three tiers), which is bp-057 (a non-goal
# here). No tier assignment, no filtering — just "the fraction of claims that hold on >= half".
STRONG_THRESHOLD = 0.5

# The five aggregate metric names — MUST match bp-054's registrations EXACTLY (§6).
METRIC_MEAN = "sigma_persistence.mean"
METRIC_P50 = "sigma_persistence.p50"
METRIC_MAX = "sigma_persistence.max"
METRIC_FRAC_GE_STRONG = "sigma_persistence.frac_ge_strong"
METRIC_N_CLAIMS = "sigma_persistence.n_claims"


class RegistryStateMismatch(RuntimeError):
    """The live lever registry differs from the drive night's — reconstruction across registry
    versions is refused (§2.4.1); the fp→σ join would silently re-key. Fail-closed (§10)."""


class MixedCorpusError(RuntimeError):
    """The joined cells span more than one `corpus_digest` — the σ-family is not over one snapshot,
    so persistence would confound corpus growth with σ (§8 validity / §10). Refuse (a confound)."""


# --- the per-claim fiber (a report artifact, NOT a store row — §2.4.2) --------------------------


@dataclass(frozen=True)
class ClaimFiber:
    """One claim's σ-fiber: its persistence, hull, and gap over the declared grid (§2.2/§2.3).
    `sigma_min`=grid[min S] (the loosest threshold it survives), `sigma_max`=grid[max S] (the
    strictest — its birth reading the filtration sparse→dense). `n_cells`=|S(χ)|; `n_seeds_rule`
    is the seed count k the ⌈k/2⌉ majority rule ran over for this pipeline."""

    claim_id: str
    kind: str
    pers: float
    sigma_min: float
    sigma_max: float
    gap: bool
    n_cells: int
    n_seeds_rule: int


@dataclass(frozen=True)
class FibersEvidence:
    """The reconstruction pins recorded at run time (§2.4.1): the declared grid, the BASE config's
    fingerprint, and the lever-registry hash the join ran under. Serialized into each reading's
    `evidence_ref` so the number stays independently recoverable and a later registry drift is
    detectable."""

    grid: tuple[float, ...]
    base_fingerprint: str
    lever_registry_hash: str

    def as_ref(self) -> str:
        return json.dumps(
            {
                "instrument": _INSTRUMENT,
                "grid": list(self.grid),
                "base_fingerprint": self.base_fingerprint,
                "lever_registry_hash": self.lever_registry_hash,
            },
            sort_keys=True,
            separators=(",", ":"),
        )


@dataclass
class FibersResult:
    """The consumer's verdict: the per-pipeline claim fibers (report artifact), the aggregate
    readings written, their spec_hashes, and the recorded evidence. `readings_written` is the count
    of NEW eval-store rows (a re-run yields 0 — the store dedups by key). `notes` records every
    coverage gap (no silent caps, §2.8)."""

    corpus_ref: str | None
    evidence: FibersEvidence
    fibers: dict[str, tuple[ClaimFiber, ...]]     # pipeline -> claim fibers
    aggregates: dict[str, dict[str, float]]        # pipeline -> {metric_name: value}
    spec_hashes: dict[str, str]                    # pipeline -> fibers spec_hash
    readings_written: int
    notes: tuple[str, ...]


# --- pure helpers -------------------------------------------------------------------------------


def lever_registry_hash() -> str:
    """A content hash over the FULL lever registry (`ops.levers.LEVERS`). `_config_fingerprint`
    hashes every registered lever, so a registry that changed between the drive night and this
    consumer would silently re-key the reconstruction (§2.4.1). Recording + comparing this hash
    makes that fail closed. Sorted by name so it is order-independent (deterministic)."""
    canon = json.dumps(
        sorted(
            [lv.name, lv.section, lv.key, str(lv.kind), lv.lo, lv.hi] for lv in LEVERS.values()
        ),
        separators=(",", ":"),
    )
    return hashlib.sha256(canon.encode()).hexdigest()


def _modify_config(base: Config, lever: Lever, value: float) -> Config:
    """Rebuild the per-cell config GENERICALLY — the exact pattern the sweep drive used
    (`eval/harness/sweep.py` _modify_config). Using the SAME construction + the SAME
    `shadow._config_fingerprint` is what makes the cell→σ join byte-exact (§2.4.1): the drive's
    fingerprint and this reconstruction's agree, or they simply do not join."""
    section = getattr(base, lever.section)
    return replace(base, **{lever.section: replace(section, **{lever.key: lever.coerce(value)})})


def _grid_descriptor(lever: Lever, grid: Sequence[float]) -> str:
    """The canonical grid descriptor π — the battery param the spec_hash carries (§2.4.3). Encodes
    the axis, its declared range, and the grid points, so a different grid/range keys DISTINCTLY
    and comparisons across unacknowledged rulers cannot collapse (the §2.6 Res(π) discipline)."""
    return json.dumps(
        {"axis": lever.key, "range": [lever.lo, lever.hi], "grid": list(grid)},
        sort_keys=True,
        separators=(",", ":"),
    )


def fibers_spec_hash(pipeline: str, lever: Lever, grid: Sequence[float]) -> str:
    """`spec_hash = sha256("fibers/v1‖<pipeline>‖<grid-descriptor>")` (§6/§2.4.3) — instrument
    id+version, then the pipeline, then the grid descriptor (a battery param, store.py:32)."""
    payload = f"{_INSTRUMENT}‖{pipeline}‖{_grid_descriptor(lever, grid)}"
    return hashlib.sha256(payload.encode()).hexdigest()


def fiber_metrics(
    support_indices: Iterable[int], grid: Sequence[float]
) -> tuple[float, float, float, bool, int]:
    """`(pers, sigma_min, sigma_max, gap, n_cells)` from a claim's σ-support INDEX set over Γ_m
    (§2.3, held verbatim). `pers = |S|/m` — the SUPPORT MEASURE, not the hull length (gaps do NOT
    count). Hull `= [grid[min S], grid[max S]]`; `gap` iff S is not one run of consecutive grid
    indices. `m = len(grid)`."""
    s = sorted(set(support_indices))
    if not s:
        raise ValueError("fiber_metrics: empty support set (a fiber requires >= 1 emitting cell)")
    m = len(grid)
    n_cells = len(s)
    pers = n_cells / m
    sigma_min = float(grid[s[0]])
    sigma_max = float(grid[s[-1]])
    gap = (s[-1] - s[0] + 1) != n_cells
    return pers, sigma_min, sigma_max, gap, n_cells


def _aggregate(fibers: Sequence[ClaimFiber]) -> dict[str, float]:
    """The five distribution summaries over the claim set's persistence values (§2.4.3)."""
    pers_vals = [f.pers for f in fibers]
    return {
        METRIC_MEAN: float(mean(pers_vals)),
        METRIC_P50: float(median(pers_vals)),
        METRIC_MAX: float(max(pers_vals)),
        METRIC_FRAC_GE_STRONG: sum(1 for p in pers_vals if p >= STRONG_THRESHOLD) / len(pers_vals),
        METRIC_N_CLAIMS: float(len(fibers)),
    }


# --- the consumer -------------------------------------------------------------------------------


@dataclass
class FibersConsumer:
    """Reconstruct the cell→σ join, score every claim across it, write the aggregates. The seams
    mirror `SweepEngine`'s: inject the stores + base config for tests; `scripts/fibers.py` resolves
    them from config over a completed sweep night. Read-only over the run ledger; writes only new
    keyed readings into the eval store (never re-keys, never overwrites — the store dedups)."""

    ledger: RunLedger
    eval_store: EvalResultsStore
    base_config: Config
    lever: Lever
    grid: tuple[float, ...]
    expected_registry_hash: str | None = None    # from the drive evidence; a mismatch refuses
    pipelines: tuple[str, ...] | None = None      # None -> every pipeline joined

    def consume(self) -> FibersResult:
        registry_hash = lever_registry_hash()
        if self.expected_registry_hash is not None and self.expected_registry_hash != registry_hash:
            raise RegistryStateMismatch(
                "fibers: the lever registry changed since the drive night — the cell→σ "
                "reconstruction would silently re-key against a changed fingerprint basis "
                f"(§2.4.1). Recorded registry hash {self.expected_registry_hash[:12]}…, live "
                f"{registry_hash[:12]}…. Refusing (fail-closed); re-drive the sweep under the "
                "current registry, or supply the matching grid/base evidence."
            )

        base_fp = _config_fingerprint(self.base_config)
        evidence = FibersEvidence(
            grid=tuple(self.grid), base_fingerprint=base_fp, lever_registry_hash=registry_hash
        )

        # Regenerate the in-memory sweep map fp→grid-index (§2.4.1) — the join key.
        fp_to_index: dict[str, int] = {}
        for i, sigma in enumerate(self.grid):
            fp = _config_fingerprint(_modify_config(self.base_config, self.lever, sigma))
            fp_to_index[fp] = i

        runs = self.ledger.runs()
        joined = [r for r in runs if r["config_fingerprint"] in fp_to_index]
        notes: list[str] = []
        if not joined:
            notes.append(
                "no run-ledger rows joined the declared grid — nothing consumed (verify the grid + "
                "base config match the drive night's lever registry; §2.4.1)."
            )
            return FibersResult(
                corpus_ref=None, evidence=evidence, fibers={}, aggregates={}, spec_hashes={},
                readings_written=0, notes=tuple(notes),
            )

        digests = {r["corpus_digest"] for r in joined}
        if len(digests) > 1:
            raise MixedCorpusError(
                "fibers: joined cells span MORE THAN ONE corpus_digest "
                f"({sorted(str(d)[:12] for d in digests)}) — the σ-family is not one snapshot, "
                "so persistence would confound corpus growth with σ (§8 validity / §10). Refusing."
            )
        corpus_ref = str(next(iter(digests)))

        pipelines = self.pipelines or tuple(sorted({str(r["pipeline"]) for r in joined}))
        fibers: dict[str, tuple[ClaimFiber, ...]] = {}
        aggregates: dict[str, dict[str, float]] = {}
        spec_hashes: dict[str, str] = {}
        written = 0
        for pipeline in pipelines:
            pipe_runs = [r for r in joined if str(r["pipeline"]) == pipeline]
            spec_hashes[pipeline] = fibers_spec_hash(pipeline, self.lever, self.grid)
            if not pipe_runs:
                notes.append(f"pipeline {pipeline!r}: no joined runs — skipped.")
                continue
            claim_fibers = self._fibers_for_pipeline(pipe_runs, fp_to_index)
            fibers[pipeline] = claim_fibers
            if not claim_fibers:
                notes.append(
                    f"pipeline {pipeline!r}: joined {len(pipe_runs)} run(s) but no claims — "
                    "no aggregate readings written (no silent cap, §2.8)."
                )
                continue
            agg = _aggregate(claim_fibers)
            aggregates[pipeline] = agg
            written += self._write_aggregates(
                spec_hashes[pipeline], corpus_ref, base_fp, agg, evidence
            )

        return FibersResult(
            corpus_ref=corpus_ref, evidence=evidence, fibers=fibers, aggregates=aggregates,
            spec_hashes=spec_hashes, readings_written=written, notes=tuple(notes),
        )

    def _fibers_for_pipeline(
        self, pipe_runs: Sequence[dict[str, object]], fp_to_index: dict[str, int]
    ) -> tuple[ClaimFiber, ...]:
        """Group ledger claims by `claim_id` across the joined cells; apply the ⌈k/2⌉ seed-majority
        rule per cell; build one `ClaimFiber` per claim emitted in >= 1 cell."""
        # cell index -> list of per-seed-run claim-id sets (one set per run at that cell). NB the
        # run ledger has NO seed column (seed reaches only the EvalKey, shadow.py:208-212), so the
        # k seed-runs at a cell are simply the k run rows sharing (pipeline, config_fingerprint).
        cell_seed_sets: dict[int, list[set[str]]] = {}
        claim_kind: dict[str, str] = {}   # claim_id -> kind (fixed per claim_id by content-address)
        for run in pipe_runs:
            idx = fp_to_index[str(run["config_fingerprint"])]
            ids: set[str] = set()
            for c in self.ledger.claims(run_id=str(run["run_id"])):
                cid = str(c["claim_id"])
                ids.add(cid)
                claim_kind.setdefault(cid, str(c["kind"]))
            cell_seed_sets.setdefault(idx, []).append(ids)

        # Seed-majority emission: e(χ, σ_i)=1 iff χ in >= ⌈k/2⌉ of the cell's k seed-runs (§2.3).
        # Today claim paths are seed-invariant so this collapses to a 0/k indicator — the rule is
        # implemented anyway for forward-compat with a stochastic pipeline (note §2.1 caveat).
        support: dict[str, set[int]] = {}
        max_k = 0
        for idx, seed_sets in cell_seed_sets.items():
            k = len(seed_sets)
            max_k = max(max_k, k)
            threshold = (k + 1) // 2      # ⌈k/2⌉
            counts: dict[str, int] = {}
            for s in seed_sets:
                for cid in s:
                    counts[cid] = counts.get(cid, 0) + 1
            for cid, n in counts.items():
                if n >= threshold:
                    support.setdefault(cid, set()).add(idx)

        out: list[ClaimFiber] = []
        for cid, idxs in support.items():
            pers, s_min, s_max, gap, n_cells = fiber_metrics(idxs, self.grid)
            out.append(
                ClaimFiber(
                    claim_id=cid, kind=claim_kind[cid], pers=pers, sigma_min=s_min,
                    sigma_max=s_max, gap=gap, n_cells=n_cells, n_seeds_rule=max_k,
                )
            )
        out.sort(key=lambda f: (-f.pers, f.claim_id))   # strongest first, id-stable
        return tuple(out)

    def _write_aggregates(
        self, spec_hash: str, corpus_ref: str, base_fp: str, agg: dict[str, float],
        evidence: FibersEvidence,
    ) -> int:
        """Write the five aggregate readings once; return the count of NEW rows (put() skips a
        present key → a re-run writes 0). Keyed per §6: base config_fingerprint, seed=0."""
        key = EvalKey(spec_hash=spec_hash, corpus_ref=corpus_ref,
                      config_fingerprint=base_fp, seed=0)
        ref = evidence.as_ref()
        written = 0
        for name, value in agg.items():
            if self.eval_store.put(
                Reading(key=key, metric_name=name, value=float(value),
                        type_tag=_TYPE_TAG, evidence_ref=ref)
            ):
                written += 1
        return written


def run_fibers(
    *,
    ledger: RunLedger,
    eval_store: EvalResultsStore,
    base_config: Config,
    lever: Lever,
    grid: Sequence[float],
    expected_registry_hash: str | None = None,
    pipelines: tuple[str, ...] | None = None,
) -> FibersResult:
    """Reconstruct + score + write in one call — the entry the script and integration test use."""
    return FibersConsumer(
        ledger=ledger, eval_store=eval_store, base_config=base_config, lever=lever,
        grid=tuple(float(v) for v in grid), expected_registry_hash=expected_registry_hash,
        pipelines=pipelines,
    ).consume()


# --- the report section (E4 tenant — model-free, deterministic, writes only data/reports/) -------


def render_markdown(result: FibersResult, *, date: str, topic: str = "sigma-fibers",
                    top_n: int = 10) -> str:
    """A deterministic markdown section over the fibers result. Prints the reconstruction pins
    (provenance), the per-pipeline aggregates, and the strongest `top_n` claim fibers. No clock is
    read (the caller stamps `date`); no model, no store write."""
    ev = result.evidence
    lines: list[str] = [
        f"# σ-fibers · {topic}",
        "",
        f"_date: {date}_",
        "",
        "## Reconstruction pins (§2.4.1)",
        "",
        f"- grid (m={len(ev.grid)}): {[round(float(v), 6) for v in ev.grid]}",
        f"- base config_fingerprint: {ev.base_fingerprint}",
        f"- lever registry hash: {ev.lever_registry_hash}",
        f"- corpus_ref: {result.corpus_ref}",
        "",
    ]
    if not result.fibers:
        lines += ["_No fibers — no run-ledger cells joined the declared grid._", ""]
    for pipeline in sorted(result.fibers):
        claim_fibers = result.fibers[pipeline]
        agg = result.aggregates.get(pipeline, {})
        lines += [f"## pipeline · {pipeline}", "",
                  f"- spec_hash: {result.spec_hashes.get(pipeline, '(unwritten)')}"]
        if agg:
            lines.append(
                "- aggregates: "
                + ", ".join(f"{name.split('.')[-1]}={value:.4f}" for name, value in agg.items())
            )
        lines += ["", "| claim_id | kind | pers | σ_min | σ_max | gap | cells | seeds |",
                  "|---|---|---|---|---|---|---|---|"]
        for f in claim_fibers[:top_n]:
            lines.append(
                f"| {f.claim_id[:12]}… | {f.kind} | {f.pers:.4f} | {f.sigma_min:.4f} | "
                f"{f.sigma_max:.4f} | {'yes' if f.gap else 'no'} | {f.n_cells} | {f.n_seeds_rule} |"
            )
        if len(claim_fibers) > top_n:
            lines.append(f"- … {len(claim_fibers) - top_n} more claim(s) (top {top_n} shown).")
        lines.append("")
    lines += ["## Coverage notes", ""]
    lines += [f"- {n}" for n in result.notes] or ["- none."]
    lines.append("")
    return "\n".join(lines)


def write_report(result: FibersResult, *, date: str, topic: str = "sigma-fibers",
                 root: str | Path = "data/reports") -> Path:
    """Write the fibers section to `<root>/<date>-<topic>/fibers.md` and return that directory. The
    ONLY filesystem write this module performs — into `data/reports/` (∉ MIRROR_READABLE, local
    file, no egress), never a store."""
    out_dir = Path(root) / f"{date}-{topic}"
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "fibers.md").write_text(render_markdown(result, date=date, topic=topic),
                                       encoding="utf-8")
    return out_dir
