"""`mind-palace shell` (scripts/shell.py): completion that comes from the parser, help whose shapes
the parser accepts, the cheat sheet generated from both, and a shell that is read-only by
construction: `plan` never executes, a request is refused, and no writer lock is taken, on a
scratch instance whose store bytes the shell leaves as it found them."""

from __future__ import annotations

import ast as pyast
import dataclasses
import fcntl
import hashlib
import importlib
import io
import itertools
import re
from pathlib import Path
from typing import Any

import pytest

from core.kernel.provenance import Provenance
from core.query import AMBASSADOR_OVERLAY
from core.sentence.grammar import KEYWORDS, ParseError, parse
from core.sentence.plan import compile_sentence
from scripts import shell
from scripts.shell import VERBS, Catalog, Completer, Shell

CHECKOUT = next(p for p in Path(__file__).resolve().parents if (p / "pyproject.toml").exists())
NOTE = "dialogue/amb/capture-1"


# ── the scratch instance ───────────────────────────────────────────────────────────────────────


def scratch_config(root: Path) -> Any:
    """An instance under `root`: every store path in its own data directory, never the live
    one, with one observed record landed in the catalog and the raw store."""
    from config.loader import load_config
    from core.kernel.stores.rawstore import RawStore
    from core.stores.catalog import VaultCatalog

    base = load_config()
    d = root / "data"
    d.mkdir(parents=True)
    paths = dataclasses.replace(
        base.paths, data_dir=d, telemetry_db=d / "telemetry.duckdb", raw_store=d / "raw",
        vector_store=d / "vectors.lance", derived_store=d / "derived.sqlite",
        vault_catalog=d / "vault_catalog.sqlite", attestation_store=d / "attestations.sqlite",
        curated_store=d / "curated.lance")
    vault = dataclasses.replace(base.ingestion.vault, path=root / "vault")
    cfg = dataclasses.replace(base, paths=paths,
                              ingestion=dataclasses.replace(base.ingestion, vault=vault))
    digest, _ = RawStore(cfg.paths.raw_store).add_text("# Sleep\nthe body of the capture")
    VaultCatalog(cfg.paths.vault_catalog).record(NOTE, digest, "Sleep",
                                                 provenance=Provenance.OBSERVED)
    return cfg


@pytest.fixture
def scratch(tmp_path: Path) -> tuple[Any, Shell]:
    cfg = scratch_config(tmp_path / "instance")
    return cfg, shell.open_shell(cfg)


def _bytes(data: Path) -> dict[str, str]:
    """Every store file's digest; SQLite's shared-memory index is a reader's scratch, not data."""
    return {str(p.relative_to(data)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(data.rglob("*")) if p.is_file() and not p.name.endswith("-shm")}


# ── completion comes from the parser ───────────────────────────────────────────────────────────


#: Arguments that complete a sentence after a leading keyword, tried blindly: the oracle the
#: completer is checked against is the parser itself, not the completer's own probe.
_TAILS = ('"x"', "a", 'from a', 'F from a', 'from a via F', '3 near "x"', '0.5 near "x"',
          'near "x"', 'S a b in near "x"', 'sever F a b in near "x"')


def _starts_by_trial() -> set[str]:
    out = set()
    for kw, tail in itertools.product(sorted(KEYWORDS), _TAILS):
        try:
            parse(f"{kw} {tail}")
        except ParseError:
            continue
        out.add(kw)
    return out


def _infix_by_trial() -> set[str]:
    out = set()
    for kw, tail in itertools.product(sorted(KEYWORDS), ("near \"y\"", "mirror", 'of "HEAD"')):
        try:
            parse(f'near "x" {kw} {tail}')
        except ParseError:
            continue
        out.add("as of" if kw == "as" else kw)
    return out


def test_completion_offers_every_verb_the_parser_accepts() -> None:
    c = Completer(Catalog())
    starts, infix = _starts_by_trial(), _infix_by_trial()
    assert "do" in starts                       # the parser accepts the action sort ...
    assert set(c.complete("")) >= starts - {"do"}
    assert "do" not in c.complete("")           # ... the read-only shell does not offer it
    after = set(c.complete('near "x" '))
    assert after >= {k.split()[0] for k in infix}
    assert c.complete('near "x" as ') == ["of"]
    assert set(shell.parser_verbs()) == (starts | infix) - {"do"}
    for verb in shell.parser_verbs():
        assert verb in c.complete("help ")


def test_every_verb_has_help_whose_shapes_the_parser_accepts() -> None:
    assert set(VERBS) == set(shell.parser_verbs())
    used: set[str] = set()
    for name, verb in VERBS.items():
        for shape in verb.shapes:
            for sentence in _expand(shape):
                parse(sentence)                  # raises with the production if it drifted
                used |= set(sentence.split())
        compile_sentence(verb.example, AMBASSADOR_OVERLAY)
        used |= set(name.split())
    assert KEYWORDS - {"do"} <= used, "keywords no help shape documents"


_FILL = {"<text>": '"x"', "<note>": '"a.md"', "<n>": "2", "<number>": "0.5", "<path>": "F+",
         "<strata>": "mirror", "<s>": 'near "x"'}


def _expand(shape: str) -> list[str]:
    """Every sentence a shape denotes: each optional group present and absent, each
    alternative taken, each placeholder filled."""
    tokens = re.findall(r"\[|\]|[^\s\[\]]+", shape)

    def seq(i: int, close: bool) -> tuple[list[list[str]], int]:
        outs: list[list[str]] = [[]]
        while i < len(tokens):
            t = tokens[i]
            if t == "]" and close:
                return outs, i + 1
            if t == "[":
                inner, i = seq(i + 1, True)
                outs = [o + x for o in outs for x in [[], *inner]]
                continue
            alts = [_FILL.get(a, a) for a in t.split("|")] if t != "|" else ["|"]
            outs = [o + [a] for o in outs for a in alts]
            i += 1
        return outs, i

    return [" ".join(o) for o in seq(0, False)[0]]


def test_slots_are_filled_from_the_instance(scratch: tuple[Any, Shell]) -> None:
    _, sh = scratch
    c = Completer(sh.catalog)
    assert f'"{NOTE}"' in c.complete('reach F from "dia')
    assert '"Sleep"' in c.complete("relate ")               # a title names a note too
    assert "curated" in c.complete('near "x" over cu')
    assert "foundation" not in c.complete('near "x" over ')  # never a stratum `over` accepts
    assert c.complete('reach F from a depth ') == [str(shell.DEFAULT.depth)]
    assert set(c.complete("walk from a via ")) >= {"S", "F", "D", "C", "("}
    assert "near" not in c.complete("walk from a via F ")    # a path, not a sentence, continues


def test_the_cheat_sheet_lists_the_verbs_the_parser_accepts() -> None:
    doc = (CHECKOUT / "docs" / "sentence-cheat-sheet.md").read_text(encoding="utf-8")
    body = doc.split("-->\n", 1)[1].split("\n<!-- verbs:end -->", 1)[0]
    assert body == shell.verb_list(), "regenerate the verbs with scripts.shell.verb_list()"
    examples = re.findall(r"^\d\. `([^`]+)`", doc, flags=re.M)
    assert len(examples) == 5
    for e in examples:
        compile_sentence(e, AMBASSADOR_OVERLAY)


# ── the shell is read-only ─────────────────────────────────────────────────────────────────────


def test_plan_never_executes(scratch: tuple[Any, Shell], monkeypatch: pytest.MonkeyPatch) -> None:
    ex = importlib.import_module("core.sentence.execute")

    def boom(*a: object, **k: object) -> None:
        raise AssertionError("plan executed the sentence")

    monkeypatch.setattr(ex, "execute", boom)
    monkeypatch.setattr(ex.Evaluator, "eval", boom)
    _, sh = scratch
    out = sh.handle(f'plan read "{NOTE}"')
    assert out.startswith("plan (text):")
    assert "support: 0 nodes" in out and "missing:" in out
    assert "the universe is the sentence's support" in out


def test_an_unknown_verb_gives_the_parsers_error_with_its_position(
        scratch: tuple[Any, Shell]) -> None:
    _, sh = scratch
    out = sh.handle('near "x" and frobnicate "y"')
    assert out.startswith("refused (parse): clause: expected a verb")
    assert re.search(r"'frobnicate' at \d+", out)
    sentence, mark = out.splitlines()[-2:]
    assert mark.index("^") == sentence.index("frobnicate")   # the caret under the word


def test_the_shell_never_takes_a_writer_lock_nor_writes_a_store(
        scratch: tuple[Any, Shell], monkeypatch: pytest.MonkeyPatch) -> None:
    from ops.lifecycle import lock

    cfg, sh = scratch
    sentences = (f'read "{NOTE}"', f'plan read "{NOTE}"', 'reach F from "core/query.py"',
                 'witness "e-1"', "do sync_vault", 'do capture(text: "x", conversation: "t")')
    for s in sentences:                         # a fresh instance's stores are made on first open
        sh.handle(s)
    before = _bytes(Path(cfg.paths.data_dir))
    taken: list[str] = []

    def no_flock(fd: object, op: int) -> None:
        taken.append(f"flock {op}")
        raise AssertionError("a lock was taken")

    def no_supervisor(self: object) -> None:
        taken.append("supervisor")
        raise AssertionError("the supervisor lock was taken")

    monkeypatch.setattr(fcntl, "flock", no_flock)
    monkeypatch.setattr(lock.SupervisorLock, "acquire", no_supervisor)
    outs = [sh.handle(s) for s in sentences]
    assert taken == []
    assert "the body of the capture" in outs[0] and "[observed]" in outs[0]
    assert all(o.startswith("refused (read-only)") for o in outs[-2:])
    assert _bytes(Path(cfg.paths.data_dir)) == before
    assert not (Path(cfg.paths.data_dir) / "query_log.jsonl").exists()
    assert not (Path(cfg.paths.data_dir) / "handoff").exists()


def test_the_shell_imports_no_writer() -> None:
    """The module names no ingress, no writer, no logged surface: read-only by what it imports."""
    tree = pyast.parse((CHECKOUT / "scripts" / "shell.py").read_text(encoding="utf-8"))
    names: set[str] = set()
    for node in pyast.walk(tree):
        if isinstance(node, pyast.ImportFrom) and node.module:
            names.add(node.module)
            names |= {f"{node.module}.{a.name}" for a in node.names}
        elif isinstance(node, pyast.Import):
            names |= {a.name for a in node.names}
    assert not any(n.startswith(("core.ingest", "core.stores", "scheduler", "edge")) for n in names)
    assert not any(n.endswith(("ask_logged", "ask", "run_query")) for n in names)


# ── the loop ───────────────────────────────────────────────────────────────────────────────────


def test_a_sentence_continues_while_the_parser_can_complete_it(
        scratch: tuple[Any, Shell]) -> None:
    _, sh = scratch
    out = io.StringIO()
    lines = "\n".join(["read", f'"{NOTE}"', "near", "", ":quit", "help"]) + "\n"
    shell.repl(sh, stdin=io.StringIO(lines), out=out, interactive=False)
    text = out.getvalue()
    assert "the body of the capture" in text                  # `read` + the next line, run
    assert "refused (parse): near: expected a quoted string" in text   # ended by a blank line
    assert "Type a sentence" not in text                      # nothing after :quit
    assert shell.needs_more("plan reach F from") and not shell.needs_more("help reach")
    assert shell.needs_more('near "unclosed') and not shell.needs_more('near "x"')


def test_help_names_the_shape_the_example_and_the_defaults() -> None:
    out = shell.verb_help("reach")
    assert out.splitlines()[0] == VERBS["reach"].shapes[0]
    assert "example: reach F" in out and "depth = 1" in out
    assert "no verb 'frob'" in shell.verb_help("frob")
    names = {f.name for f in dataclasses.fields(shell.DEFAULT)}     # the precedents' own names
    assert set(shell.NUMBER_PRECEDENT.values()) <= names
    assert {p for ps in shell.VERB_PRECEDENTS.values() for p in ps} <= names
    for verb in VERBS:
        assert shell.verb_help(verb).startswith(VERBS[verb].shapes[0])
