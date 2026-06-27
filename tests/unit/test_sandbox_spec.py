"""ExecSpec validation + ExecResult semantics (BUILD-SPEC §11)."""

import pytest

from core.sandbox import ExecResult, ExecSpec


def test_execspec_rejects_empty_code():
    with pytest.raises(ValueError):
        ExecSpec(code="   ")


def test_execspec_rejects_out_of_bounds_timeout():
    with pytest.raises(ValueError):
        ExecSpec(code="x", timeout_s=0)
    with pytest.raises(ValueError):
        ExecSpec(code="x", timeout_s=10_000)


def test_execresult_ok_requires_clean_exit_and_no_timeout():
    assert ExecResult("out", "", 0).ok
    assert not ExecResult("", "", 1).ok
    assert not ExecResult("", "", 0, timed_out=True).ok
