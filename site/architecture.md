# Architecture

Three zones, separated structurally — not by convention:

- **Zone A — `core/` (sealed).** Zero network egress, enforced twice: a runtime seal
  (loopback-only socket guard) and a static import firewall proving no `core` module can
  even *name* a networked zone. Holds the stores, the provenance system, the reasoning
  complex, and the typed views.
- **Zone B — `edge/`** — the only code that touches the network. Communicates with core
  by filesystem handoff, never imports.
- **Host tier — `ops/`, `scheduler/`, `scripts/`** — lifecycle (the always-on daemon,
  the deploy gate), supervised jobs, sensors (the code-snapshot ledger), and witnesses
  (attested CI verdicts).

## The load-bearing asymmetries

- **MirrorView** reads only what the owner authored — wrong-provenance rows are
  unconstructable, not filtered.
- **DerivedStore** mints only `interpreted` artifacts — there is no parameter with which
  to lie about provenance.
- **Authored[T] / Derived[T]** make accidental promotion a *compile-time* error; real
  promotion demands an owner-verdict capability object.
- **The blessing gates** (`draft→ratified`, `proposed→ready`) are owner-only hand edits,
  denied to agents pre-hoc and audited post-hoc against committed history.

Every consequential act — ingest, dream, deploy, rotation — lands in an append-only,
hash-chained attestation record.
