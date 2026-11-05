"""The ledger cross-reference reads Lean declarations by their heads (the review of 2026-11-05,
gate finding 7: the pattern missed `set_option … in theorem`, two attribute blocks, and
`nonrec`, so a Spec theorem written that way was never flagged as unjudged)."""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
_spec = importlib.util.spec_from_file_location("check_laws_xref",
                                               ROOT / "scripts" / "check_laws_xref.py")
assert _spec is not None and _spec.loader is not None
xref = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(xref)


@pytest.mark.parametrize(("line", "kind", "name"), [
    ("theorem foo : True := trivial", "theorem", "foo"),
    ("set_option maxHeartbeats 400000 in theorem foo : True := trivial", "theorem", "foo"),
    ("@[simp] @[norm_cast] theorem bar (x : Nat) : x = x := rfl", "theorem", "bar"),
    ("nonrec theorem baz : True := trivial", "theorem", "baz"),
    ("private lemma q : True := trivial", "lemma", "q"),
    ("noncomputable def d : Nat := 0", "def", "d"),
])
def test_a_declaration_head_is_read_whatever_precedes_it(line: str, kind: str,
                                                          name: str) -> None:
    m = xref.DECL.match(line)
    assert m is not None and (m.group(1), m.group(2)) == (kind, name)
