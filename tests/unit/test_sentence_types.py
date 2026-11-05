"""The typing of the query sentence algebra (`core/sentence/types.py`): sorts, Rule NOUN, the
clause-wise scope check (QSA-5, `formal/Palace/Sentence.lean`), and the result grade (Rule HYP)."""

from __future__ import annotations

import pytest

from core.kernel.scope import Clock, Stratum, Window
from core.query import AMBASSADOR, Grant, Mode, Verb, mode_of, required, scope
from core.sentence import (
    AmbiguousSentence,
    IllScopedSentence,
    Sort,
    SortError,
    admissible,
    clauses_of,
    hyps_of,
    is_inv,
    parse,
    sort_of,
    typecheck,
)
from core.sentence.ast import Rel
from core.sentence.types import check_admissible


def test_sorts_follow_the_structure() -> None:
    assert sort_of(parse('near "x"')) is Sort.FIELD
    assert sort_of(parse('top 3 near "x"')) is Sort.REGION
    assert sort_of(parse('near "x" and reach F from "n"')) is Sort.FIELD   # a masked field
    assert sort_of(parse('reach F from "n" and relate "n"')) is Sort.REGION
    assert sort_of(parse('trace "n"')) is Sort.CHAIN
    assert sort_of(parse('witness "e"')) is Sort.WITNESS
    assert sort_of(parse('assume S "a" "b" in near "x"')) is Sort.FIELD


@pytest.mark.parametrize("text, reason", [
    ('not near "x"', "complement"),            # the cone has no complement
    ('near "x" then near "y"', "region"),      # then needs a region on the left
    ('near "x" or reach F from "n"', "two fields or two regions"),
    ('trace "n" and near "x"', "fields and regions"),
    ('far reach F from "n"', "field"),
    ('assume S "a" "a" in near "x"', "distinct"),
])
def test_an_ill_sorted_sentence_is_refused_with_the_reason(text: str, reason: str) -> None:
    with pytest.raises(SortError) as e:
        typecheck(parse(text))
    assert reason in str(e.value)


def test_rule_noun_the_relation_carries_the_letter() -> None:
    (near,) = clauses_of(parse('near "x"'))
    assert near.mode is Mode.SEMANTIC and near.req.edges.fibers == frozenset()
    assert near.req.sigma.strata == frozenset({Stratum.MIRROR_AUTHORED})
    (diffuse,) = clauses_of(parse('diffuse S from "n"'))
    assert diffuse.mode is Mode.SEMANTIC and diffuse.req.edges.fibers == frozenset()
    # the legacy table types DIFFUSE as citation-structural though it walks the backbone
    assert mode_of(required(Verb.DIFFUSE)) is Mode.STRUCTURAL
    (reach,) = clauses_of(parse('reach F from "core/x.py"'))
    assert reach.mode is Mode.STRUCTURAL and reach.req.edges.fibers == frozenset({"F"})
    assert reach.req.time.clock is Clock.COMMIT
    # a title names a node of the strata in force: finding it is a clause of its own when the
    # relation's strata do not cover it
    reach, name = clauses_of(parse('reach F from "n"'))
    assert reach.req.sigma.strata == frozenset({Stratum.REFERENCE, Stratum.REFERENCE_REPO})
    assert name.verb == "name" and name.req.sigma.strata == frozenset({Stratum.MIRROR_AUTHORED})
    (trace,) = clauses_of(parse('trace "n"'))
    assert trace.mode is Mode.TEMPORAL and trace.req.edges.fibers == frozenset({"D"})
    (witness,) = clauses_of(parse('witness "e"'))
    assert witness.mode is Mode.CAUSAL
    (walk,) = clauses_of(parse('walk from "a" via S*C'))
    assert walk.mode is Mode.CAUSAL and walk.req.edges.fibers == frozenset({"C"})
    assert walk.req.time.clock is Clock.COMMIT


def test_a_transcript_ref_reads_the_dialogues_transcript_stratum() -> None:
    from core.sentence.types import read_strata, short_names

    assert read_strata("transcript/s1/3") == (Stratum.DIALOGUE_TRANSCRIPT,)
    assert short_names(read_strata("transcript/s1/3")) == frozenset({"transcript"})
    assert read_strata("dialogue/c/t1") == (Stratum.DIALOGUE,)
    assert short_names(read_strata("dialogue/c/t1")) == frozenset({"dialogue"})
    # a clause over the dialogue admits both, since the transcript stratum sits below it
    assert short_names({Stratum.DIALOGUE, Stratum.DIALOGUE_TRANSCRIPT}) == frozenset(
        {"dialogue", "transcript"})


def test_over_sets_the_strata_and_refuses_an_unknown_one() -> None:
    (c,) = clauses_of(parse('near "x" over curated'))
    assert c.req.sigma.strata == frozenset({Stratum.CURATED})
    with pytest.raises(AmbiguousSentence, match="not a stratum"):
        clauses_of(parse('near "x" over nowhere'))


def test_admissibility_is_clause_wise() -> None:
    """QSA-5: `and`, `or` and `then` are admissible iff both halves are (`admissible_and`)."""
    mirror_only = Grant((scope({Stratum.MIRROR}, set(), Clock.PROJECTION_EVENT, Window.all()),))
    cases = ['near "x"', 'reach F from "n"', 'diffuse S from "n"', 'witness "e"', 'trace "n"']
    for grant in (AMBASSADOR, mirror_only):
        for a in cases:
            for b in cases:
                both = admissible(parse(f"({a}) and ({b})"), grant)
                assert both == (admissible(parse(a), grant) and admissible(parse(b), grant))
    assert admissible(parse('near "x"'), mirror_only)
    assert not admissible(parse('reach F from "n"'), mirror_only)
    with pytest.raises(IllScopedSentence, match="reach F"):
        check_admissible(parse('near "x" and reach F from "n"'), mirror_only)


def test_assume_needs_a_plane_naming_the_overlay() -> None:
    """QSA-5: `admissible_assume_overlay`, `ambassador_no_assume`."""
    sentence = parse('assume S "a" "b" +0.5 in near "x"')
    assert admissible(parse('near "x"'), AMBASSADOR)
    assert not admissible(sentence, AMBASSADOR)
    with pytest.raises(IllScopedSentence, match="overlay"):
        check_admissible(sentence, AMBASSADOR)
    with_overlay = Grant((scope({Stratum.MIRROR, Stratum.HYPOTHETICAL}, set(),
                                Clock.PROJECTION_EVENT, Window.all()),))
    assert admissible(sentence, with_overlay)
    hyp, body = clauses_of(sentence)          # the hypothesis is a clause of its own (it reads S)
    assert hyp.verb == "reach" and hyp.rel is Rel.S
    for c in (hyp, body):
        assert c.overlay and Stratum.HYPOTHETICAL in c.req.sigma.strata


def test_an_assumed_edge_needs_a_plane_that_admits_its_relation() -> None:
    """The hypothesis reads what it perturbs: `assume C …` needs a plane admitting C as surely as
    `reach C` does, so a grant without C refuses it even when the body reads only the mirror (the
    review of 2026-11-05: the universe walked C for a letter no admitted clause typed)."""
    mirror_only = Grant((scope({Stratum.MIRROR, Stratum.HYPOTHETICAL}, set(),
                               Clock.PROJECTION_EVENT, Window.all()),))
    assert admissible(parse('assume S "a" "b" in near "x"'), mirror_only)
    with pytest.raises(IllScopedSentence):
        check_admissible(parse('assume C "transcript/s/1" "core/y.py" in near "x"'), mirror_only)
    contradict, _ = clauses_of(parse('assume contradict "a" "b" in near "x"'))
    assert contradict.verb == "relate"


def test_rule_hyp_a_result_under_assume_is_never_inv() -> None:
    assert is_inv(parse('near "x" and reach F from "n"'))
    assert hyps_of(parse('near "x"')) == ()
    s = parse('(assume S "a" "b" +0.5 in near "x") and assume contradict "c" "d" in near "y"')
    assert not is_inv(s)
    assert hyps_of(s) == ("S 'a' 'b' +0.5", "contradict 'c' 'd'")


def test_read_is_a_text_that_composes_with_nothing_and_reads_by_the_refs_shape() -> None:
    """`read` has sort `text`; `and`/`or`/`within`/`top` refuse it; its clause reads the curated
    stratum for a paper ref and the mirror or the dialogue for anything else, with the single-read
    cut the multi-stratum point read needs (SCO-8); both are admitted by the Ambassador's grant."""
    assert sort_of(parse('read "a.md"')) is Sort.TEXT
    for bad in ('read "a.md" and near "x"', 'near "x" or read "a.md"', 'top 3 read "a.md"',
                'read "a.md" within reach F from "n"'):
        with pytest.raises(SortError):
            typecheck(parse(bad))
    (paper,) = clauses_of(parse('read "reference:arxiv-1"'))
    assert paper.verb == "read" and paper.req.sigma.strata == {Stratum.CURATED}
    (note,) = clauses_of(parse('read "/vault/n.md"'))                      # an absolute path
    assert note.req.sigma.strata == {Stratum.MIRROR_AUTHORED} and note.req.cut is None
    (title,) = clauses_of(parse('read "note-2026-07-11"'))                 # a title: either
    assert {Stratum.MIRROR_AUTHORED, Stratum.DIALOGUE} <= title.req.sigma.strata
    assert title.req.cut == "single-read" and title.mode.value == "semantic"
    (turn,) = clauses_of(parse('read "dialogue/c/t1"'))
    assert Stratum.DIALOGUE in turn.req.sigma.strata
    (repo,) = clauses_of(parse('read "docs/x.md"'))                        # a repo path: reference
    assert Stratum.REFERENCE in repo.req.sigma.strata and repo.req.time.clock.value == "commit"
    for s in ('read "reference:arxiv-1"', 'read "/vault/n.md"', 'read "note-2026-07-11"',
              'read "dialogue/c/t1"', 'read "docs/x.md"'):
        assert admissible(parse(s), AMBASSADOR), s
    _, under = clauses_of(parse('assume contradict "a" "b" in read "/vault/n.md"'))
    assert under.overlay and Stratum.HYPOTHETICAL in under.req.sigma.strata


# ── the action sort: a command requires the write bit (dn-ingest-door D2, DOR-1) ───────────────


def test_a_command_is_an_event_and_requires_the_write_bit_on_what_it_writes() -> None:
    from core.sentence import ast
    from core.sentence.types import command_requirement

    (c,) = clauses_of(parse('do ingest note "x.md"'))
    assert c.verb == "ingest note" and c.req.authority.store_write == 1
    assert c.req.sigma.strata == frozenset({Stratum.MIRROR_AUTHORED})
    assert c.req.time.clock is Clock.PROJECTION_EVENT
    (d,) = clauses_of(parse("do dream"))
    assert d.req.sigma.strata == frozenset({Stratum.INTERPRETED})
    assert d.req.authority.store_write == 1
    assert d.req.authority.privilege.name == "READ_PROPOSE"
    (t,) = clauses_of(parse("do sync chat"))
    assert t.req.time.clock is Clock.COMMIT and t.req.edges.fibers == frozenset({"C"})
    assert t.mode is Mode.CAUSAL
    (o,) = clauses_of(parse("do observe code"))
    assert o.req.edges.fibers == frozenset({"F"}) and o.req.time.clock is Clock.COMMIT
    # the table is total over the commands the grammar admits
    for text in ('do ingest turn c 1 "t"', "do ingest doc d/x.md", 'do ingest paper "reference:p"',
                 "do ingest code", "do ingest transcript s", "do sync vault", "do sync dialogue",
                 "do sync code", "do curate", "do relate", 'do link "a" "b" supports',
                 'do capture "t"', 'do research "q"'):
        node = parse(text)
        assert isinstance(node, ast.Do)
        name, strata, _fibers, _clock, _propose = command_requirement(node.command)
        assert name and strata and typecheck(node) is Sort.EVENT


def test_the_ambassadors_grant_as_written_admits_projection_event_commands_only() -> None:
    """DOR-1 read on the grant as it stands (dn-ingest-door D2, §8): the first plane carries the
    write bit at the projection-event clock over six strata, the commit-clock plane carries none,
    and the order is false across clocks."""
    from core.query import AMBASSADOR, AMBASSADOR_OVERLAY

    admitted = ["do dream", 'do capture "t"', 'do link "a" "b" supports', 'do ingest note "x"',
                "do sync vault", 'do ingest doc d/x.md', "do relate"]
    refused = ["do ingest code", "do sync code", "do sync chat", "do observe code",
               "do ingest transcript s"]
    for text in admitted:
        assert admissible(parse(text), AMBASSADOR), text
        assert admissible(parse(text), AMBASSADOR_OVERLAY), text
    for text in refused:
        assert not admissible(parse(text), AMBASSADOR), text
        with pytest.raises(IllScopedSentence):
            check_admissible(parse(text), AMBASSADOR)


def test_a_read_only_grant_admits_no_command_and_still_admits_every_query() -> None:
    """DOR-1 `readonly_admits_no_command`: planes without the write bit refuse every command."""
    from core.kernel.scope import Window
    from core.query import Grant, scope

    read_only = Grant((
        scope({Stratum.MIRROR, Stratum.CURATED, Stratum.INTERPRETED, Stratum.DIALOGUE,
               Stratum.OBSERVED, Stratum.REFERENCE}, {"F", "D"}, Clock.PROJECTION_EVENT,
              Window.all(), propose=True),
        scope({Stratum.REFERENCE, Stratum.DIALOGUE}, {"F", "C"}, Clock.COMMIT, Window.all(),
              propose=True),
    ))
    for text in ("do dream", 'do capture "t"', 'do ingest note "x"', "do sync vault",
                 'do link "a" "b" supports', "do ingest code", 'do research "q"'):
        assert not admissible(parse(text), read_only), text
    for text in ('near "x"', 'reach F from "core/x.py"', 'reach C from "x"', 'witness "e"'):
        assert admissible(parse(text), read_only), text
