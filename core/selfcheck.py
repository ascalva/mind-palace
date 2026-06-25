"""The Constitution pre-return self-evaluation check (BUILD-SPEC §4, §15; Constitution §IV).

Every agent runs this before returning output (Invariant 6 / §IV). Two layers, matching
the Constitution's own mandate:

  * Deterministic, always-on (cheap): verify the output is *grounded* — every note it
    cites must resolve to a source that was actually retrieved. "A cited identifier that
    does not resolve is a failure" (Constitution §III.1). This is the concrete,
    deterministic check the spec explicitly calls for.

  * Subjective (mirror-vs-oracle, overclaimed certainty, consequential deference): these
    are NOT decided by brittle keyword matching. The spec is emphatic (§4, §15): a
    small-model judge, A/B'd against a known-good baseline snapshot, *never scored cold*.
    The baseline/anchor machinery is part of the safety fixed point and lands with the
    self-modification loop (Phase 10). Until then this module exposes a `judge` seam;
    when no judge is wired these dimensions are reported as `deferred` — honestly
    not-yet-evaluated, never silently passed off as conforming.

`passed` is True iff there are no FAIL findings; a `deferred` finding does not fail.
"""

from __future__ import annotations

import re
from collections.abc import Callable
from dataclasses import dataclass

PASS = "pass"
FAIL = "fail"
DEFERRED = "deferred"

# [[note title]] — the corpus's own link/citation convention (Logseq), reused so the
# librarian cites notes the way the owner already references them.
_CITATION = re.compile(r"\[\[([^\]]+)\]\]")

# Subjective directives the deterministic layer cannot judge honestly. Each awaits the
# small-model judge + baseline snapshot (Phase 10); reported as `deferred` until then.
_JUDGE_DIRECTIVES: tuple[tuple[str, str], ...] = (
    ("mirror-not-oracle", "Constitution §III.2 — present synthesis as a lens, not external truth"),
    ("calibrated-certainty", "Constitution §III.1 — do not overclaim certainty"),
    ("consequential-deference", "Constitution §III.3 — defer on health/financial/legal"),
)


@dataclass(frozen=True)
class Finding:
    directive: str       # which Constitution directive this concerns
    status: str          # PASS | FAIL | DEFERRED
    detail: str = ""


@dataclass(frozen=True)
class SelfCheck:
    """Result of the pre-return Constitution check (§IV)."""

    passed: bool
    findings: tuple[Finding, ...] = ()

    @property
    def notes(self) -> tuple[str, ...]:
        """Compact summary, e.g. ("grounded-citations:pass", "mirror-not-oracle:deferred")."""
        return tuple(f"{f.directive}:{f.status}" for f in self.findings)

    def failures(self) -> tuple[Finding, ...]:
        return tuple(f for f in self.findings if f.status == FAIL)


# A judge maps the output text -> findings for the subjective directives. It is A/B'd
# against a baseline by its caller (Phase 10), never scored cold here.
SubjectiveJudge = Callable[[str], "list[Finding]"]


def _normalize(s: str) -> str:
    return s.strip().casefold()


def check_grounding(output: str, sources: set[str] | None) -> Finding:
    """Deterministic: every [[cited]] note must be one that was actually retrieved
    (Constitution §III.1, "a cited identifier that does not resolve is a failure").

    `sources=None` means there was no retrieval context (e.g. a generic agent), so the
    check is not applicable and is reported as deferred rather than failing.
    """
    if sources is None:
        return Finding("grounded-citations", DEFERRED, "no retrieval context to check against")
    cited = {m.strip() for m in _CITATION.findall(output)}
    if not cited:
        return Finding("grounded-citations", PASS, "no citations to resolve")
    allowed = {_normalize(s) for s in sources}
    unresolved = sorted(c for c in cited if _normalize(c) not in allowed)
    if unresolved:
        return Finding(
            "grounded-citations", FAIL,
            f"cited note(s) not in retrieved sources: {', '.join(unresolved)}",
        )
    return Finding("grounded-citations", PASS, f"all {len(cited)} citation(s) resolve")


def self_evaluate(output: str, *, sources: set[str] | None = None,
                  judge: SubjectiveJudge | None = None) -> SelfCheck:
    """Run the pre-return Constitution check.

    `sources`: the legitimate citation targets (titles of retrieved notes). Pass the
    retrieved set for a RAG agent; omit it (None) for an agent with no retrieval context.
    `judge`: optional small-model judge for the subjective directives; when absent those
    directives are reported as `deferred` (Phase 10 wires the judge + baseline).
    """
    findings: list[Finding] = [check_grounding(output, sources)]
    if judge is not None:
        findings.extend(judge(output))
    else:
        findings.extend(
            Finding(key, DEFERRED, f"needs judge + baseline (Phase 10): {detail}")
            for key, detail in _JUDGE_DIRECTIVES
        )
    passed = not any(f.status == FAIL for f in findings)
    return SelfCheck(passed=passed, findings=tuple(findings))
