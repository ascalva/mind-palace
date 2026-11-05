"""The door's language (dn-door-language §E1, §E3, §E10 to §E12): its grammar, its scopes and
closures, its labels, its meter, and its type system's soundness for labels (DOR-13, DOR-18)."""

from __future__ import annotations

from typing import Any

import pytest

from core.sentence.grammar import ParseError, is_request, parse
from core.sentence.interpret import (
    OBSERVED,
    Content,
    Evaluator,
    Handle,
    Meter,
    Origin,
    OStr,
    OutOfGas,
    Record,
    ScriptError,
    StoreEff,
)
from core.sentence.script import (
    GRAMMAR,
    CallScript,
    Inline,
    Let,
    Sentence,
    library_names,
    load,
    parse_request,
    parse_script,
    quote,
)
from core.sentence.script_check import Checker, check, labels_of

AUTH = "authored-solo"


class Palace:
    """A palace of two notes, a structured source of two turns, and a place of one entry."""

    def __init__(self) -> None:
        self.queries: list[str] = []

    def open(self, name: str) -> Handle:
        if name == "secret":
            raise ScriptError("source('secret'): the role may not open it")
        return Handle(name, "/v")

    def files(self, h: Handle) -> list[Record]:
        out = []
        for p, body, props in (("/v/a.md", b"alpha", {"id": "ID-A", "ref": "ID-B"}),
                               ("/v/b.md", b"beta", {})):
            o = Origin("item", h.name, p, p[3:-3])
            declared = Origin("id", h.name, p, p[3:-3])      # the source's identity property
            out.append(Record({"path": OStr(p, AUTH, o), "content": Content(body, AUTH, o),
                               "digest": OStr("d" + p, AUTH, o), "title": OStr(p[3:-3], AUTH, o),
                               "properties": Record({k: OStr(v, AUTH, declared if k == "id" else o)
                                                     for k, v in props.items()})}))
        return out

    def file(self, h: Handle, path: str) -> Record:
        return next(r for r in self.files(h) if r["path"] == path)

    def exists(self, h: Handle, path: str) -> bool:
        return path in ("/v/a.md", "/v/b.md")

    def items(self, h: Handle) -> list[Record]:
        out = []
        for i, (role, label) in enumerate((("user", "authored-dialogue"), ("assistant", OBSERVED))):
            p = f"dialogue/x/c/{i}"
            o = Origin("item", h.name, p, "")
            out.append(Record({"path": OStr(p, label, o), "role": OStr(role, label, o),
                               "content": Content(f"turn {i}".encode(), label, o),
                               "timestamp": 1_700_000_000 + i}))
        return out

    def stored(self, place: str, prefix: str) -> list[Record]:
        o = Origin("entry", place, "/v/old.md", "old")
        return [Record({"path": OStr("/v/old.md", OBSERVED, o), "identity": OStr("ID-OLD",
                        OBSERVED, o), "digest": OStr("d/v/b.md", OBSERVED, o),
                        "title": OStr("old", OBSERVED, o), "active": True})]

    def entry(self, place: str, name: str) -> Record:
        return Record({"path": name, "digest": "x" + name})

    def query(self, sentence: str) -> list[Record]:
        self.queries.append(sentence)
        return [Record({"ref": OStr("r1", OBSERVED, Origin("entry", "hit", "r1")),
                        "title": OStr("T", OBSERVED, Origin("entry", "hit", "r1"))})]


def run(text: str, *, budget: int = 100_000_000, lib: dict[str, str] | None = None,
        **kwargs: Any) -> list[Any]:
    scripts = {k: parse_script(v) for k, v in (lib or {}).items()}
    ev = Evaluator(Palace(), "cli", Meter(budget), library=scripts.__getitem__)
    return ev.run(parse_script(text), kwargs=kwargs)


# ── the grammar ─────────────────────────────────────────────────────────────────────────────

def test_the_grammar_is_one_file_read_by_a_generated_parser() -> None:
    assert GRAMMAR.name == "script.lark" and GRAMMAR.is_file()
    assert "script:" in GRAMMAR.read_text() and "request:" in GRAMMAR.read_text()


def test_a_request_is_a_library_call_or_a_script_inline() -> None:
    assert parse_request("sync_vault") == CallScript("sync_vault", (), ())
    call = parse_request('capture(text: "a thought", conversation: \'tea\')')
    assert isinstance(call, CallScript) and dict((k, v.value) for k, v in call.kwargs) == {
        "text": "a thought", "conversation": "tea"}
    assert isinstance(parse_request('{ store "x" in "observed" at "p"; run "dream" }'), Inline)


def test_one_rule_says_what_a_request_is_for_the_parser_and_every_surface() -> None:
    for text in ("do sync_vault", "  do{ run \"dream\" }", "do capture(text: \"x\")"):
        assert is_request(text)
        assert type(parse(text)).__name__ == "Do"
    for text in ('near "do"', "dog", 'diffuse S from "do"'):
        assert not is_request(text)


def test_a_newline_ends_a_statement_and_is_space_inside_brackets() -> None:
    s = parse_script('let xs = [1,\n 2,\n 3]\nlet y = first(\n none,\n 4)\n')
    assert len(s.body) == 2
    with pytest.raises(ParseError, match="newline"):
        parse_script("let x = 1 let y = 2")


def test_a_stores_clauses_come_in_any_order_each_once() -> None:
    a = parse_script('store "x" in "observed" at "p" titled "t"').body[0]
    b = parse_script('store "x" at "p" titled "t" in "observed"').body[0]
    assert a == b
    with pytest.raises(ParseError, match="one 'in' clause"):
        parse_script('store "x" in "observed" in "curated" at "p"')


def test_a_nested_sentence_names_its_captures() -> None:
    stmt = parse_script("let h = `top 3 near $topic within $region`").body[0]
    assert isinstance(stmt, Let)
    e = stmt.expr
    assert isinstance(e, Sentence) and e.captures == ("topic", "region")


@pytest.mark.parametrize("bad", ['store "x"', "let = 3", "for x in y", 'let x = "a" +',
                                 "let let = 1", 'run dream', "return", "x"])
def test_a_malformed_script_is_refused_naming_where(bad: str) -> None:
    with pytest.raises(ParseError):
        parse_script(bad)


def test_quote_is_the_inverse_of_the_string_literal() -> None:
    for s in ['plain', 'a "quote"', "back\\slash", "new\nline\ttab", "'single'"]:
        assert parse_request(f"f(t: {quote(s)})").kwargs[0][1].value == s  # type: ignore[union-attr]


def test_the_library_is_named_never_pathed() -> None:
    assert {"sync_vault", "capture", "sync_dialogue", "sync_docs", "link"} <= set(library_names())
    for bad in ("../x", "a/b", "Sync", ""):
        with pytest.raises(ParseError):
            load(bad)


# ── scopes, closures, calls ─────────────────────────────────────────────────────────────────

def test_a_let_in_a_block_never_leaks_out_of_it() -> None:
    plan = run('let x = 1\nif true { let x = 2 }\nstore str(x) in "observed" at "p"')
    assert plan[0].content.data == b"1"


def test_a_closure_captures_its_scope_by_value_and_never_itself() -> None:
    plan = run('let n = 1\nfn f() { return n }\nlet n = 2\nstore str(f()) in "observed" at "p"')
    assert plan[0].content.data == b"1"          # the binding where f was defined
    with pytest.raises(ScriptError, match="not a built-in"):
        run("fn f(x) { return f(x) }\nlet y = f(1)")
    with pytest.raises(ScriptError, match="not a built-in"):
        run("fn f(x) { return g(x) }\nfn g(x) { return f(x) }\nlet y = g(1)")


def test_a_function_may_hold_effects_and_a_call_adds_them() -> None:
    plan = run('fn keep(t) { store t in "observed" at "p/" + t }\nkeep("a")\nkeep("b")'
               .replace("\nkeep", "\nlet _ = keep"))
    assert [e.path for e in plan] == ["p/a", "p/b"]


def test_a_script_calls_a_script_in_a_scope_of_its_own() -> None:
    lib = {"inner": 'param t\nstore t in "observed" at "q/" + t',
           "a": "call b", "b": "call a"}
    plan = run('let secret = "s"\ncall inner(t: "x")', lib=lib)
    assert [e.path for e in plan] == ["q/x"]
    with pytest.raises(ScriptError, match="cycle"):
        run("call a", lib=lib)
    with pytest.raises(ScriptError, match="not bound"):
        run('call inner(t: "x")', lib={"inner": 'param t\nstore secret in "observed" at "q"'})


# ── labels (DOR-13) ─────────────────────────────────────────────────────────────────────────

def test_a_projection_keeps_its_items_label_and_anything_composed_is_observed() -> None:
    """Only an item's content carries its label and origin. A string read off an item (its
    title, its digest, a turn's role) is not the item's bytes: stored, it is composed, observed
    and of no origin, so it needs `at` and lands nowhere an item's label would (the audits'
    finding: `store n.digest` replaced the owner's note with its hash, as authored)."""
    plan = run('for n in files(source("v")) {\n'
               '  store n.content in "mirror_authored"\n'
               '  store n.title in "observed" at "t/" + n.title\n'
               '  store n.title + "!" in "observed" at "o/" + n.title\n'
               '  store n.title[0:1] in "observed" at "s/" + n.title\n}')
    labels = [(e.path, e.content.label, e.content.origin) for e in plan]
    assert labels[0][:2] == ("/v/a.md", AUTH) and labels[0][2] is not None
    assert all(label == OBSERVED and origin is None for _, label, origin in labels[1:4])
    for field in ("digest", "title", "path"):
        with pytest.raises(ScriptError, match="composed content has no origin"):
            run(f'for n in files(source("v")) {{ store n.{field} in "mirror_authored" }}')
    for t in run('for t in items(source("x")) { store t.role in "observed" at "r/" + t.role }'):
        assert t.content.label == OBSERVED and t.content.origin is None


def test_content_is_opaque_its_label_beyond_any_expression() -> None:
    with pytest.raises(ScriptError, match="fields `digest` and `path`"):
        run('for n in files(source("v")) { let l = n.content.label }')
    with pytest.raises(ScriptError):
        run('for n in files(source("v")) { let x = n.content + "x" }')


def test_an_identity_read_off_the_item_stored_is_named_as_that_items() -> None:
    plan = run('let ns = files(source("v"))\n'
               'store ns[0].content in "mirror_authored" as ns[0].properties.id\n'
               'store ns[1].content in "mirror_authored" as "composed"\n'
               'let gone = stored("mirror_authored", under: "/v/")\n'
               'store ns[1].content in "mirror_authored" as unique_by(gone, "digest")'
               '[ns[1].digest].identity')
    assert plan[0].naming.kind == "prop" and plan[0].naming.value == "ID-A"
    assert plan[1].naming.kind == "named"
    assert plan[2].naming.kind == "held" and plan[2].naming.value == "/v/old.md"
    # only the property the source declares as the identity names one: any other field of the
    # item (a `ref::`, its title) is a plain string, which names nothing but the path itself
    other = run('let ns = files(source("v"))\n'
                'store ns[0].content in "mirror_authored" as ns[0].properties.ref\n'
                'store ns[0].content in "mirror_authored" as ns[0].title')
    assert [e.naming.kind for e in other] == ["named", "named"]


# ── nested sentences (§E11) ─────────────────────────────────────────────────────────────────

def test_a_capture_enters_a_sentence_as_a_quoted_literal_never_as_syntax() -> None:
    p = Palace()
    ev = Evaluator(p, "cli", Meter(10_000_000))
    ev.run(parse_script('let t = "x\\" or near \\"y"\nlet r = `reach F from $t`\n'
                        'let h = `top 3 near $t within $r`\nlet n = len(h)'))
    assert p.queries == ['top 3 near "x\\" or near \\"y" within (reach F from "x\\" or near \\"y")']
    assert parse(p.queries[0])                      # one sentence, the text a single literal


def test_a_sentence_is_read_once_and_only_when_its_hits_are_needed() -> None:
    p = Palace()
    Evaluator(p, "cli", Meter(10_000_000)).run(parse_script('let h = `near "x"`'))
    assert p.queries == []
    Evaluator(p, "cli", Meter(10_000_000)).run(parse_script(
        'let h = `near "x"`\nlet a = len(h)\nfor x in h { let b = x.title }'))
    assert p.queries == ['near "x"']


# ── the meter (§E10) ────────────────────────────────────────────────────────────────────────

def test_a_request_out_of_budget_stops_and_lands_nothing() -> None:
    with pytest.raises(OutOfGas, match="nothing lands"):
        run('for n in files(source("v")) { for m in files(source("v")) '
            '{ store "x" in "observed" at "p" } }', budget=60)


# ── the type system (§E12, DOR-18) ──────────────────────────────────────────────────────────

class Table:
    def place_accepts(self, place: str) -> frozenset[str] | None:
        return {"mirror_authored": frozenset({AUTH, "authored-dialogue"}),
                "observed": frozenset({OBSERVED}),
                "dialogue": frozenset({OBSERVED, "authored-dialogue"})}.get(place)

    def job_known(self, job: str) -> bool:
        return job == "dream"

    def source_readable(self, name: str, role: str) -> bool | None:
        return {"v": True, "d": True, "secret": False}.get(name)

    def source_labels(self, name: str) -> frozenset[str] | None:
        return {"v": frozenset({AUTH}), "d": frozenset({"authored-dialogue", OBSERVED})}.get(name)


@pytest.mark.parametrize("text, why", [
    ('store "x" in "mirror_authored" at "p"', "R2"),
    ('let t = "x"\nstore t + "y" in "mirror_authored" at "p"', "R2"),
    ('for t in items(source("d")) { store t.content in "observed" }', "R2"),
    ("let y = x", "before it is bound"),
    ('store "x" in "nowhere" at "p"', "no such place"),
    ('run "nap"', "no such job"),
    ('let s = source("nope")', "no such source"),
    ('let s = source("secret")', "may not open"),
    ("let h = `near $missing`", "not bound"),
    ('let h = `near "x" and`', "nested sentence"),
    ("return 1", "outside a function"),
    ('fn f(a) { return a }\nlet y = f(1, 2)', "takes 1"),
])
def test_the_checker_refuses_before_anything_is_read(text: str, why: str) -> None:
    with pytest.raises(ScriptError, match=why):
        check(parse_script(text), Table(), "cli")


def test_the_checker_admits_the_projections_and_names_what_admission_needs() -> None:
    reqs = check(parse_script('for n in files(source("v")) { store n.content in "mirror_authored" }'
                              '\nfor t in items(source("d")) { store t.content in "dialogue" }'
                              '\nrun "dream"'), Table(), "cli")
    assert [(r.kind, r.name) for r in reqs] == [("place", "mirror_authored"),
                                               ("place", "dialogue"), ("job", "dream")]


def test_the_library_type_checks_under_the_palaces_table() -> None:
    from core.ingest.table import build_table
    from core.kernel.config import get_config

    table = build_table(get_config())
    for name in library_names():
        for role in ("cli", "ambassador"):
            check(load(name), table, role, library=load)


EXPRS = ["n.content", "n.title", "n.path", "n.title + n.path", "str(len(n.title))", "n.title[0:2]",
         "first(none, n.title)", "first(n.properties.id, n.path)", "digest(n.content)",
         "t.content", "t.role", "t.role + \"!\"", "first(t.role, n.title)"]


@pytest.mark.parametrize("expr", EXPRS)
def test_a_values_label_at_run_time_is_in_its_types_set(expr: str) -> None:
    """DOR-18 on the implementation: for every expression over the items, the label the evaluator
    gives a stored value is in the set the checker inferred for it."""
    script = parse_script("let ns = files(source(\"v\"))\nlet ts = items(source(\"d\"))\n"
                          f"for n in ns {{ for t in ts {{ let v = {expr} }} }}")
    checker = Checker(Table(), "cli")
    seen: list[Any] = []
    original = checker.stmt

    def spy(s: Any, env: Any) -> None:
        original(s, env)
        if type(s).__name__ == "Let" and s.name == "v":
            seen.append(env.names["v"])
    checker.stmt = spy  # type: ignore[method-assign]
    checker.check(script)
    static = labels_of(seen[0])
    plan = run("let ns = files(source(\"v\"))\nlet ts = items(source(\"d\"))\n"
               f"for n in ns {{ for t in ts {{ store {expr} in \"any\" at \"p\" }} }}")
    for e in plan:
        assert isinstance(e, StoreEff)
        if static is not None:
            assert e.content.label in static, (expr, e.content.label, static)


# ── the prices (§E10) ───────────────────────────────────────────────────────────────────────

def test_the_prices_and_the_budgets_mirror_their_measurement() -> None:
    """`PRICES` and the roles' budgets are what `docs/query/precedents.md` records, the table
    `eval/door_gas.py` measured; the two change together."""
    import re

    from core.ingest.table import build_table
    from core.kernel.config import REPO_ROOT, get_config
    from core.sentence.interpret import PRICES

    doc = (REPO_ROOT / "docs" / "query" / "precedents.md").read_text(encoding="utf-8")
    section = doc[doc.index("## The door's prices"):doc.index("## Resolutions")]
    prices = {k: int(v) for k, v in re.findall(r"^\| `(\w+)` \| `(\d+)` \|", section, re.M)}
    assert prices == dict(PRICES)
    budgets = {k: int(v) for k, v in
               re.findall(r"^\| the `(\w+)` role's budget \| `(\d+)` \|", section, re.M)}
    assert budgets == {r.name: r.budget for r in build_table(get_config()).roles.values()}


def test_a_request_is_described_without_its_strings() -> None:
    """A plan's rendering and a refusal name a request by its script and its arguments, a string
    by its length: a capture's text never travels past the request file."""
    from core.sentence.ast import Do, describe_request

    term = parse('do capture(text: "remember the milk", conversation: "tea")')
    assert isinstance(term, Do)
    assert describe_request(term.request) == 'capture(text: "<17>", conversation: "<3>")'
    inline = parse('do { store "secret" in "observed" at "dialogue/door/cli/x" }')
    assert isinstance(inline, Do) and describe_request(inline.request) == "{ 1 statement }"


# ── the audits of the second form (2026-11-05) ──────────────────────────────────────────────

def test_the_checker_is_bounded_and_a_function_is_checked_once_per_types(monkeypatch: Any) -> None:
    """The security audit's bomb: each function calls the one before twice, so checking each call
    afresh doubles the work per line. A body checked once with some types is not checked again,
    the pass is bounded, and the evaluation runs out of budget, never out of time."""
    import time

    import core.sentence.script_check as sc
    from core.sentence.script_check import Checker

    lines = ["fn f0(x) { return x }"] + [f"fn f{i}(x) {{ return f{i - 1}(f{i - 1}(x)) }}"
                                         for i in range(1, 41)] + ["let y = f40(1)"]
    script = parse_script("\n".join(lines))
    t0 = time.perf_counter()
    check(script, Table(), "cli")
    assert time.perf_counter() - t0 < 2.0
    with pytest.raises(OutOfGas):
        run("\n".join(lines), budget=1_000_000)
    monkeypatch.setattr(sc, "MAX_CHECK_STEPS", 100)      # a script is bounded by the parser too
    wide = parse_script("let x = [" + ", ".join(["1"] * 101) + "]")
    with pytest.raises(ScriptError, match="steps to check"):
        Checker(Table(), "cli").check(wide)


def test_a_nested_request_is_refused_before_it_is_compiled() -> None:
    with pytest.raises(ScriptError, match="a request does not nest"):
        check(parse_script("let h = `do dream`"), Table(), "cli")
    from core.ingest import door
    from core.kernel.config import get_config

    with pytest.raises(ScriptError, match="a request does not nest"):
        door.reader(get_config(), "ambassador")("do { let x = 1 }")


def test_work_that_grows_with_its_operands_is_paid_for_by_size() -> None:
    """The meter charges by what an operation touches: `+` by what it builds, `in` by what it
    scans, a nested sentence by its length (and no sentence grows past its cap); `str` of a
    function is no text."""
    def used(text: str) -> int:
        m = Meter(10**12)
        Evaluator(Palace(), "cli", m).run(parse_script(text))
        return m.used

    base = used("let x = [1, 2, 3, 4]")
    doubled = "let x = [1, 2, 3, 4]\n" + "\n".join(["let x = x + x"] * 12)
    assert used(doubled) - base > 4 * 2**12                   # every element copied, paid
    assert used(doubled + "\nlet b = 0 in x") - used(doubled) >= 4 * 2**12
    with pytest.raises(ScriptError, match="nested sentence of more than"):
        run('let q0 = `near "a"`\n' + "\n".join(f"let q{i} = `$q{i - 1} or $q{i - 1}`"
                                                  for i in range(1, 16)) + "\nlet n = len(q15)")
    with pytest.raises(ScriptError, match="has a text"):
        run("fn f(x) { return x }\nlet s = str(f)")
    with pytest.raises(ScriptError, match="has a text"):
        run('let s = str(`near "x"`)')


def test_a_places_entries_are_read_once_and_found_by_path_title_or_digest() -> None:
    p = Palace()
    calls: list[str] = []
    real = p.stored

    def stored(place: str, prefix: str) -> list[Record]:
        calls.append(place)
        return real(place, prefix)

    p.stored = stored  # type: ignore[method-assign]
    m = Meter(10**9)
    plan = Evaluator(p, "cli", m).run(parse_script(
        'let a = entry("mirror_authored", "/v/old.md")\n'
        'let b = entry("mirror_authored", "old")\n'
        'let c = entry("mirror_authored", "d/v/b.md")\n'
        'let d = stored("mirror_authored", under: "/v/")\n'
        'link a to c as "supports"'))
    assert calls == ["mirror_authored"] and len(plan) == 1
    with pytest.raises(ScriptError, match="no entry has that path"):
        run('let a = entry("mirror_authored", "nothing")')
    with pytest.raises(ScriptError, match="an entry of a place"):
        run('for n in files(source("v")) { link n to n as "supports" }')


def test_the_checkers_rules_contain_every_run_time_label() -> None:
    """DOR-18 on the code, where the formal audit found the rules untested: `first` joins every
    argument, a function's call returns what its body returns, and a list's elements join, so the
    set the checker infers for each `v` contains the label `v` has when the script runs."""
    from core.sentence.script_check import Checker, T

    cases = {
        'for n in files(source("v")) { for t in items(source("d")) {\n'
        '  let v = first(t.content, n.content)\n  store v in "observed" at "x" } }':
            {AUTH, "authored-dialogue", OBSERVED},
        'fn pick(n) { return n.content }\nfor n in files(source("v")) {\n'
        '  let v = pick(n)\n  store v in "observed" at "x" }': {AUTH},
        'for n in files(source("v")) {\n  let v = [n.content, n.content][0]\n'
        '  store v in "observed" at "x" }': {AUTH},
    }
    for text, expected in cases.items():
        seen: list[T] = []

        class Spy(Checker):
            def expr(self, e: Any, env: Any, seen: list[T] = seen) -> T:
                t = super().expr(e, env)
                if getattr(e, "id", None) == "v":
                    seen.append(t)
                return t

        with pytest.raises(ScriptError, match="R2"):       # each `v` may be authored: refused
            Spy(Table(), "cli").check(parse_script(text))
        inferred = labels_of(seen[0])
        assert inferred is not None and expected <= inferred, (text, inferred)
        # and at run time, every value `v` takes has a label in the inferred set
        script = parse_script(text.replace('store v in "observed" at "x"', 'let w = v'))
        labels: set[str] = set()

        class Watch(Evaluator):
            def eval(self, e: Any, env: Any, labels: set[str] = labels) -> Any:
                v = super().eval(e, env)
                if getattr(e, "id", None) == "v" and isinstance(v, Content):
                    labels.add(v.label)
                return v

        Watch(Palace(), "cli", Meter(10**9)).run(script)
        assert labels and labels <= inferred, (text, labels, inferred)
