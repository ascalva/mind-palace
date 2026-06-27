"""Shared test fixtures and synthetic-data generators (test-organization.md §1).

Importable as a top-level package (`from fixtures.stores import ...`) because the root
`tests/conftest.py` puts `tests/` on `sys.path`. Keep helpers here pure and dependency-light
so any category — unit, metamorphic, adversarial, integrity — can reuse them.

Modules:
    corpus  — synthetic notes / vector rows (no model, deterministic)
    stores  — ephemeral local-store builders (tmp RawStore / DerivedStore)
"""
