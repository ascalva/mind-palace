"""The Constitution pre-return check (BUILD-SPEC §4, §15; Constitution §IV).

Deterministic grounding (cited notes must resolve to retrieved sources) + the judge seam
for the subjective directives (deferred until the Phase 10 baseline machinery exists).
"""

from core.selfcheck import DEFERRED, FAIL, PASS, Finding, self_evaluate


def test_grounding_passes_when_citations_resolve():
    chk = self_evaluate("As in [[Sleep]] and [[Budget]], rest matters.",
                        sources={"Sleep", "Budget"})
    assert chk.passed
    g = next(f for f in chk.findings if f.directive == "grounded-citations")
    assert g.status == PASS


def test_grounding_fails_on_unresolved_citation():
    chk = self_evaluate("See [[Nonexistent Note]] for details.", sources={"Sleep"})
    assert not chk.passed
    assert chk.failures()
    g = next(f for f in chk.findings if f.directive == "grounded-citations")
    assert g.status == FAIL
    assert "Nonexistent Note" in g.detail


def test_grounding_not_applicable_without_retrieval_context():
    chk = self_evaluate("a plain answer with no retrieval", sources=None)
    assert chk.passed
    g = next(f for f in chk.findings if f.directive == "grounded-citations")
    assert g.status == DEFERRED


def test_citation_match_is_case_insensitive():
    assert self_evaluate("[[sleep]]", sources={"Sleep"}).passed


def test_subjective_directives_deferred_without_judge():
    statuses = {f.directive: f.status for f in self_evaluate("anything", sources=set()).findings}
    assert statuses["mirror-not-oracle"] == DEFERRED
    assert statuses["calibrated-certainty"] == DEFERRED
    assert statuses["consequential-deference"] == DEFERRED


def test_judge_seam_fires_and_can_fail():
    def judge(_output):
        return [Finding("mirror-not-oracle", FAIL, "presented synthesis as external truth")]

    chk = self_evaluate("The objective truth is X.", sources=set(), judge=judge)
    assert not chk.passed
    assert any(f.directive == "mirror-not-oracle" and f.status == FAIL for f in chk.findings)
