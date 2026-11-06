"""The trace — a sentence's proof of work (dn-query-sentence-algebra §2.7, `explain`).

Opt in (`palace query --trace`; the MCP `query` tool's `trace: true`): the compiler, the universe
builder and the executor each note what they did, with the numbers in hand and the law it rests
on — the parse and its sort, every rewrite of the normal form, the support's census, each
clause's arithmetic (the kernel column, the killed walk and its free energies, the Schur product,
the masks and the cuts), a hypothetical's rank-one update and its sever horizon, the ranking.
Nothing is recomputed to produce it, and nothing in it is a note's text: refs, counts and
scores only, of nodes the sentence was admitted to read. Off, every hook is one `None` check.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

# `act` is the ingress's stage (dn-ingress D3): a command is written as a request for the
# daemon's one writer, and the trace names the request and its kind.
STAGES = ("parse", "plan", "universe", "eval", "rank", "act")


@dataclass(frozen=True)
class Step:
    """One line of work: the stage it belongs to, what was done (with its numbers), and the
    ledger rows or design theorems it rests on, comma-separated."""

    stage: str
    what: str
    law: str = ""


@dataclass
class Trace:
    """The steps, in the order they happened."""

    steps: list[Step] = field(default_factory=list)

    def note(self, stage: str, what: str, law: str = "") -> None:
        if stage not in STAGES:
            raise ValueError(f"unknown trace stage {stage!r}")
        self.steps.append(Step(stage, what, law))

    @property
    def laws(self) -> tuple[str, ...]:
        """Every law cited, once, in order of first use."""
        seen: dict[str, None] = {}
        for s in self.steps:
            for law in (x.strip() for x in s.law.split(",")):
                if law:
                    seen.setdefault(law, None)
        return tuple(seen)

    def render(self) -> str:
        """The trace as text, grouped by stage; a multi-line step indents its continuation."""
        lines = ["trace (the proof of work):"]
        stage = ""
        for s in self.steps:
            if s.stage != stage:
                stage = s.stage
                lines.append(f"  {stage}:")
            first, *rest = s.what.splitlines() or [""]
            law = f"  [{s.law}]" if s.law else ""
            lines.append(f"    - {first}{law}")
            lines += [f"      {ln}" for ln in rest]
        if self.laws:
            lines.append(f"  laws: {', '.join(self.laws)} (the ledger rows in docs/LAWS.md, the "
                         "design theorems in formal/Palace/)")
        return "\n".join(lines)

    def to_dict(self) -> dict[str, Any]:
        return {"steps": [{"stage": s.stage, "what": s.what, **({"law": s.law} if s.law else {})}
                          for s in self.steps],
                "laws": list(self.laws)}
