"""The laws ledger's pointers resolve at HEAD: MF-2's minimal ledger checker
(dn-mathematical-foundations §2.2, "Resolution and repair").

`docs/LAWS.md` indexes and never restates: each row points at the code that holds its law, the
anchor `file::symbol`, and at the tests that would catch it false, pytest node ids. A refactor that
moves a law's ground leaves its row pointing at nothing; this test then fails, and the refactoring
PR carries the row repair. Reading the source, never importing it, it checks that

- every anchor's file exists and defines its symbol, `name` or `Class.member`;
- every node id in a falsifier cell names a test module that defines the test, a `test*`
  function or a `test*` method of a `Test*` class, the names pytest's default patterns collect;
- a row whose falsifier reads `GAP` claims no rung above Conjecture, the cap the ledger's header
  states (a Definition has no truth value to cap).

Statement drift against symbols that did not move is beyond it, by design (the note's §3); the
formal column is `scripts/check_laws_xref.py`'s.
"""

from __future__ import annotations

import ast
import re
from functools import cache
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LEDGER = ROOT / "docs" / "LAWS.md"
COLUMNS = ["law", "statement", "structure", "anchor", "label", "falsifier", "formal"]
_ROW = re.compile(r"\| ([A-Z]+-\d+) \|")
_CELL = re.compile(r"(?<!\\)\|")
_TICKED = re.compile(r"`([^`]+)`")
_ABOVE_CONJECTURE = ("Observation", "Claim", "Prop", "Lemma", "Theorem", "Corollary")


def _cells(line: str) -> list[str]:
    return [c.strip() for c in _CELL.split(line.strip())[1:-1]]


def _table() -> tuple[list[list[str]], dict[str, list[str]]]:
    lines = LEDGER.read_text().splitlines()
    headers = [_cells(line) for line in lines if line.startswith("| law |")]
    rows = {cells[0]: cells for cells in (_cells(line) for line in lines if _ROW.match(line))}
    return headers, rows


HEADERS, ROWS = _table()


@cache
def _module(path: str) -> ast.Module:
    return ast.parse((ROOT / path).read_text())


def _defined(body: list[ast.stmt], name: str) -> ast.stmt | None:
    """The statement in `body` that defines `name`: a function, a class, or an assignment."""
    for node in body:
        if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef):
            if node.name == name:
                return node
        elif isinstance(node, ast.Assign | ast.AnnAssign):
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            if any(isinstance(t, ast.Name) and t.id == name for t in targets):
                return node
    return None


def anchor_resolves(anchor: str) -> bool:
    """`file`, `file::name` or `file::Class.member`, a Python file under the repository."""
    path, _, symbol = anchor.partition("::")
    if not (path.endswith(".py") and (ROOT / path).is_file()):
        return False
    body: list[ast.stmt] = _module(path).body
    for part in symbol.split(".") if symbol else []:
        node = _defined(body, part)
        if node is None:
            return False
        body = node.body if isinstance(node, ast.ClassDef) else []
    return True


def node_id_collects(node_id: str) -> bool:
    """`tests/…/test_x.py::test_y` or `tests/…/test_x.py::TestZ::test_y`."""
    path, *names = node_id.split("::")
    if not (path.startswith("tests/") and Path(path).name.startswith("test_")
            and (ROOT / path).is_file() and names):
        return False
    body: list[ast.stmt] = _module(path).body
    *classes, test = names
    for cls in classes:
        node = _defined(body, cls)
        if not (isinstance(node, ast.ClassDef) and cls.startswith("Test")):
            return False
        body = node.body
    node = _defined(body, test)
    return isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef) and test.startswith("test")


def test_every_table_has_the_ledger_columns():
    """The schema the checks below read by position."""
    assert HEADERS and all(h == COLUMNS for h in HEADERS)
    assert ROWS and all(len(cells) == len(COLUMNS) for cells in ROWS.values())


def test_every_anchor_resolves_at_head():
    """Every anchor names a file that exists and a symbol that file defines."""
    stale = [(law, a) for law, cells in ROWS.items() for a in _TICKED.findall(cells[3])
             if not anchor_resolves(a)]
    assert stale == []


def test_every_falsifier_names_a_collected_test():
    """Every node id a falsifier cell names is a test pytest collects."""
    stale = [(law, f) for law, cells in ROWS.items() for f in _TICKED.findall(cells[5])
             if not node_id_collects(f)]
    assert stale == []


def test_a_gap_caps_the_label_at_conjecture():
    """A row whose falsifier is `GAP` claims no rung above Conjecture; a target after `→` is not a
    claim, only the rung the gap's closing unit is to earn."""
    over = [(law, cells[4]) for law, cells in ROWS.items() if cells[5].startswith("GAP")
            and any(rung in cells[4].split("→")[0] for rung in _ABOVE_CONJECTURE)]
    assert over == []


def test_the_checker_rejects_planted_stale_pointers():
    """Control, MF-2's own falsifier: a planted stale pointer of each kind is caught."""
    assert anchor_resolves("core/kernel/complex/hodge.py::boundary_1")
    assert not anchor_resolves("core/kernel/complex/hodge.py::boundary_3")
    assert not anchor_resolves("core/kernel/scope.py::StratumScope.of_all")
    assert not anchor_resolves("core/kernel/complex/hodges.py")
    assert node_id_collects("tests/unit/test_hodge.py::TestItem2SyntheticTopologySuite::test_psd")
    assert not node_id_collects("tests/unit/test_hodge.py::test_psd")
    assert not node_id_collects("tests/unit/test_hodge.py::TestItem2SyntheticTopologySuite::test_x")
    assert not node_id_collects("tests/unit/test_hodge.py::_cycle_adjacency")
    assert not node_id_collects("tests/unit/test_hodge.py")
