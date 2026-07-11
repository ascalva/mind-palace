# Mind Palace

> A knowledge system built around a single question: what does it mean for a system to
> know *why* it believes something?

This site is the **code documentation** — generated directly from the docstrings, the
same English layer that bridges the private corpus to the code inside the system itself
(the "Rosetta" layer). For the project's goals, principles, honest status, and
verification commands, read the [repository README](https://gitlab.com/ascalva-projects/mind-palace).

Two names: **mind-palace** is the framework (public, this repo); **Ouroboros** is the
live instance (one person's always-on daemon; its corpus is never public).

## Where to start

- [Architecture](architecture.md) — the zones and the load-bearing asymmetries.
- [core](api/core/) — the sealed kernel: stores, provenance, the reasoning complex.
- [ops](api/ops/) — lifecycle, deploy gate, sensors, witnesses.

## The design record

The system's *design* is not documented here — it lives as a typed artifact chain in the
repository (`docs/design-notes/`, ratified by hand, immutable to agents; `docs/PROGRESS.md`,
the build log). This split is deliberate: the site documents what the code **is**; the
corpus documents **why** it is that way, with warrants.
