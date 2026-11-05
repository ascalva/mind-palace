"""Admission bounds what a sentence reads (the review of 2026-11-05, finding 2).

QSA-5 admits a sentence clause by clause; the Lean model's evaluator is `Local`: a clause reads
only the strata it requires. These tests hold the Python evaluator to that on a universe whose
nodes carry their strata as the builder labels them: a verb is evaluated on its clause's nodes
and its value lies within them; a complement, a reversal or a threshold is taken within the
strata its term reads; `over` masks both arms of a hypothetical; and the Ambassador's planes are
pinned, so a stratum cannot be added to them unnoticed.
"""

from __future__ import annotations

from collections.abc import Mapping

import numpy as np
import pytest

from core.kernel.scope import Clock, Stratum, StratumScope, Window
from core.query import AMBASSADOR, Grant, scope
from core.sentence import compile_sentence, execute
from core.sentence.ast import Rel
from core.sentence.execute import Relation, Universe
from core.sentence.grammar import parse
from core.sentence.types import IllScopedSentence, admissible, check_admissible, clauses_of

# a: the owner's note; b: another; t1: an observed turn (the assistant's words, a capture);
# t2: the owner's own words in chat; x: a file of the reference graph. On the backbone a — t1 — b
# is the only way from a to b, through the observed turn; a — t2 is the owner's chat.
_NOTES: list[dict[str, object]] = [
    {"source_path": "a.md", "title": "A", "digest": "da", "provenance": "authored-solo",
     "stratum": "mirror"},
    {"source_path": "b.md", "title": "B", "digest": "db", "provenance": "authored-solo",
     "stratum": "mirror"},
    {"source_path": "dialogue/c/t1", "title": "T1", "digest": "dt1", "provenance": "observed",
     "stratum": "dialogue"},
    {"source_path": "dialogue/c/t2", "title": "T2", "digest": "dt2",
     "provenance": "authored-dialogue", "stratum": "dialogue"},
    {"source_path": "docs/x.md", "title": "docs/x.md", "digest": "", "provenance": "corpus",
     "stratum": "reference"},
]


def _universe(t1_weight: float = 0.9) -> Universe:
    w = np.zeros((5, 5))
    for i, j, x in ((0, 2, t1_weight), (2, 1, t1_weight), (0, 3, 0.5)):
        w[i, j] = w[j, i] = x
    vectors = np.eye(5)

    def embed(text: str) -> np.ndarray:
        return np.array([0.6, 0.5, 0.9, 0.4, 0.7])          # nearest the observed turn

    def history(atom: str) -> list[tuple[str, int, str, str]]:
        return []

    def witness(edge: str) -> Mapping[str, object] | None:
        return None

    return Universe([dict(n) for n in _NOTES], vectors, w,
                    {Rel.F: {"docs/x.md": {"a.md"}}, Rel.D: {}, Rel.C: {}},
                    [Relation("da", "db", 1, "supports", 1.0),
                     Relation("da", "dt1", 1, "supports", 1.0)],
                    embed, history, witness)


def _refs(sentence: str, u: Universe | None = None) -> list[str]:
    return [h.ref for h in execute(compile_sentence(sentence), u or _universe()).hits]


def test_near_reads_the_owners_words_by_default_and_the_dialogue_only_over_it() -> None:
    """`near` with no `over` is the mirror's (the precedent): the owner's notes and chat turns,
    never an observed turn, however near it is."""
    assert set(_refs('near "q"')) == {"a.md", "b.md", "dialogue/c/t2"}
    assert set(_refs('near "q" over dialogue')) == {"dialogue/c/t1", "dialogue/c/t2"}


def test_a_walk_never_steps_through_a_node_outside_its_strata() -> None:
    """The backbone joins a to b only through the observed turn: under the mirror's strata the
    walk does not take that step, `diffuse` puts no mass on b, and `walk` finds no chain."""
    field = execute(compile_sentence('diffuse S from "a.md"'), _universe()).hits
    assert {h.ref for h in field} == {"dialogue/c/t2"}           # the owner's chat turn only
    assert _refs('walk from "a.md" to "b.md" via S+') == []
    assert _refs('reach S from "a.md" depth 3') == ["dialogue/c/t2"]
    # a title names a node of the strata in force: over the dialogue, "a.md" names no turn
    with pytest.raises(LookupError, match="no node"):
        _refs('reach S from "a.md" depth 3 over dialogue')


def test_a_clauses_answer_does_not_depend_on_what_it_does_not_read() -> None:
    """The Lean model's `Local`: change only the observed turn's edges and the mirror clause's
    answer is the same, field for field."""
    sentence = compile_sentence('diffuse S from "a.md"')
    one = execute(sentence, _universe(0.9)).hits
    two = execute(sentence, _universe(0.2)).hits
    assert [(h.ref, h.score) for h in one] == [(h.ref, h.score) for h in two]


def test_not_far_and_atleast_stay_within_the_strata_their_term_reads() -> None:
    """A complement, a reversal and a threshold are taken within the strata the term's verbs
    read: none of them can bring in a node of a stratum no clause admitted."""
    mirror = {"a.md", "b.md", "dialogue/c/t2"}
    # relate reads the mirror: its complement is the mirror's other nodes, never the observed
    # turn it is related to, nor the reference graph's file
    assert set(_refs('not relate "a.md"')) == mirror - {"b.md"}
    assert set(_refs('atleast 0 near "q"')) == mirror
    assert set(_refs('far near "q"')) <= mirror


def test_over_masks_both_arms_of_a_hypothetical() -> None:
    answer = execute(compile_sentence(
        '(assume S "a.md" "b.md" +0.5 in near "q") over dialogue'), _universe())
    assert answer.hyp is not None
    assert {h.ref for h in answer.hits} <= {"dialogue/c/t1", "dialogue/c/t2"}
    assert {h.ref for h in answer.hyp.value} <= {"dialogue/c/t1", "dialogue/c/t2"}


def test_then_masks_the_right_side_to_the_left_sides_region() -> None:
    """`then` restricts: the right side's answer is cut to the left's region (a mutation that
    stopped masking survived the suite before this test)."""
    assert set(_refs('near "q" over dialogue')) == {"dialogue/c/t1", "dialogue/c/t2"}
    assert _refs('relate "a.md" then near "q"') == ["b.md"]


def test_the_ambassadors_planes_are_pinned() -> None:
    """The strata, fibers and clocks of the Ambassador's grant, exactly: adding a stratum (OPS,
    EXHAUST, FOUNDATION) to a plane fails here (a mutation adding OPS survived before)."""
    planes = [(frozenset(s.sigma.strata), frozenset(s.edges.fibers), s.time.clock)
              for s in AMBASSADOR.scopes]
    assert planes == [
        (StratumScope.of(Stratum.MIRROR, Stratum.CURATED, Stratum.INTERPRETED, Stratum.DIALOGUE,
                         Stratum.OBSERVED, Stratum.REFERENCE).strata,
         frozenset({"F", "D"}), Clock.PROJECTION_EVENT),
        (StratumScope.of(Stratum.REFERENCE, Stratum.DIALOGUE).strata, frozenset({"F", "C"}),
         Clock.COMMIT),
        (StratumScope.of(Stratum.MIRROR).strata, frozenset({"D"}), Clock.N_S),
    ]
    for s in AMBASSADOR.scopes:
        assert not {Stratum.EXHAUST, Stratum.FOUNDATION, Stratum.HYPOTHETICAL} & s.sigma.strata


def test_relate_reads_the_mirror() -> None:
    """The signed relation edges are among the mirror's notes: a grant without the mirror does not
    admit `relate` (a mutation typing it with no strata survived before)."""
    reference_only = Grant((scope({Stratum.REFERENCE}, {"F"}, Clock.COMMIT, Window.all()),))
    assert not admissible(parse('relate "a.md"'), reference_only)
    with pytest.raises(IllScopedSentence, match="relate"):
        check_admissible(parse('relate "a.md"'), reference_only)
    (relate,) = clauses_of(parse('relate "a.md"'))
    assert Stratum.MIRROR_AUTHORED in relate.req.sigma.strata


def test_a_narrower_grant_reads_only_what_it_admits() -> None:
    """Under a grant of the mirror alone, the default `near` is admitted and answers from the
    mirror; `over dialogue` is refused at admission, before anything is read."""
    mirror_only = Grant((scope({Stratum.MIRROR}, set(), Clock.PROJECTION_EVENT, Window.all()),))
    plan = compile_sentence('near "q"', mirror_only)
    assert {h.ref for h in execute(plan, _universe()).hits} == {"a.md", "b.md", "dialogue/c/t2"}
    with pytest.raises(IllScopedSentence):
        compile_sentence('near "q" over dialogue', mirror_only)


@pytest.mark.parametrize("sentence", [
    'read "a.md" over dialogue', 'assume S "a.md" "b.md" in read "a.md"',
    'witness "e1" over dialogue', 'top 1 near "q" then read "a.md"'])
def test_a_record_composes_with_nothing(sentence: str) -> None:
    """`read` and `witness` answer with a record; a mask or a hypothesis has nothing to act on,
    so the sentence is refused when it is typed, as `docs/query/asking.md` says."""
    from core.sentence.types import SortError

    with pytest.raises(SortError, match="composes with nothing"):
        compile_sentence(sentence)


def test_top_ranks_within_its_adjectives_and_answers_in_score_order() -> None:
    """`top k` takes its field with the field's adjectives, so it ranks within a region or a
    stratum instead of ranking everything and masking after (which dropped hits the mask would
    have kept); a region is answered highest score first (finding 4)."""
    assert _refs('top 1 near "q" over dialogue') == ["dialogue/c/t1"]
    hits = execute(compile_sentence('top 3 near "q"'), _universe()).hits
    assert [h.ref for h in hits] == ["a.md", "b.md", "dialogue/c/t2"]
    assert [h.detail["score"] for h in hits] == sorted((h.detail["score"] for h in hits),
                                                       reverse=True)
    assert _refs('top 1 near "q" within relate "a.md"') == ["b.md"]
    assert _refs('(top 1 near "q") within relate "a.md"') == []      # written outside: masked after


def test_a_hypothesis_on_one_node_is_refused_by_node_not_by_name() -> None:
    """`assume S "a.md" "A"` names one note twice, by its path and its title: refused, so no self
    loop reaches the backbone (the walk's solver forbids one) and no answer is labelled `Hyp` on
    a perturbation that never happened (finding 6)."""
    for sentence in ('assume S "a.md" "A" +0.5 in near "q"',
                     'assume contradict "a.md" "A" in relate "b.md"'):
        with pytest.raises(IllScopedSentence, match="same node"):
            execute(compile_sentence(sentence), _universe())


def test_the_response_note_claims_no_growth_diffusion_does_not_have() -> None:
    """Adding weight lowers no effective resistance (QSA-9), but the walk normalises by degree, so
    a diffusion field can fall where the weight was added: the note says reach grows and
    diffusion can move either way, and the answer shows a fall."""
    answer = execute(compile_sentence('assume S "a.md" "b.md" +0.5 in diffuse S from "a.md"'),
                     _universe())
    note = next(n for n in answer.notes if n.startswith("adds weight"))
    assert "can move either way" in note and "diffusion and reach can only grow" not in note
    before = {h.ref: h.score for h in answer.hits}
    assert answer.hyp is not None
    after = {h.ref: h.score for h in answer.hyp.value}
    fell, was = after["dialogue/c/t2"], before["dialogue/c/t2"]
    assert fell is not None and was is not None and fell < was  # the owner's turn: 0.25 → 0.18
    assert any("1 up, 1 down" in n for n in answer.notes)
