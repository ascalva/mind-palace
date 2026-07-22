"""`core/temporal/` — the OUTER residue of the temporal package after K3 (bp-091).

The pure citation-complex mathematics (`boundary`, `complex`, `operators`, `superconnection`)
and this package's old re-exporting init were the S1 seven (bp-089); K3 relocated them to
`core/kernel/temporal/**` (dn-inner-outer-core §2.6b/§2.7). Import that math from
`core.kernel.temporal.*` directly.

What stays here is OUTER **by design**: the store-reading acquisition seam `acquire.py`
(the S1 seam — "the pure builder takes data; the store-reading acquisition seam moves one
ring outward"), the eval-coupled `spine.py`, and `atlas.py`. This residue init is a
docstring-only package marker: import-free, side-effect-free, so the inner-ring fixed point
claims it (§2.4-B1) while its outer submodules stay behind — the same shape as the K1
split-package residues (`core.complex` / `core.ingest` / `core.stores` / `core.typedshims`).
"""

from __future__ import annotations
