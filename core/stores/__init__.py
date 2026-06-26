"""Zone A — scoped store access layers (BUILD-SPEC §8, CONVENTIONS).

Polyglot persistence, each store independently replaceable, with access scoped IN CODE
(not by convention): a handle exposes exactly the reads/writes a role needs and nothing
more. Present: the DuckDB telemetry store, the content-addressed raw store (immutable, §8),
the LanceDB thought-graph vectors (derived), and the SQLite derived store for INTERPRETED
artifacts (dreams + curator findings, §8) — the last writes `interpreted` provenance only,
so the derived layer can never masquerade as authored ground truth.
"""
