"""ops/ci_witness.py — GitHub Actions backend (bp-016): §6(c) verdict mapping row-by-row,
the absent-grace poll loop, Keychain-absent degradation, and the mocked release dispatch.

Pure — no network, no clock, no Keychain: `run_for`/`_get`/`urlopen`/`subprocess.run`/
`time` are all mocked or injected. Falsifier discipline (plan Item 7): this suite was run
once against the pre-change GitLab module and shown RED (journal 2026-07-12) — it pins
the GitHub backend specifically, not "either backend".
"""

from __future__ import annotations

import email.message
import json
import time
import urllib.error
import urllib.request
from typing import Any

import pytest

import ops.ci_witness as w


def _run(status: str, conclusion: str | None = None, run_id: int = 1) -> dict[str, Any]:
    """A GitHub workflow-run row, shaped as observed live (journal 2026-07-12, Q3)."""
    return {"id": run_id, "status": status, "conclusion": conclusion,
            "html_url": f"https://github.com/ascalva/Mind-Palace/actions/runs/{run_id}"}


class _Clock:
    """Simulated monotonic clock: sleep() advances time; nothing actually waits."""

    def __init__(self) -> None:
        self.t = 0.0

    def monotonic(self) -> float:
        return self.t

    def sleep(self, s: float) -> None:
        self.t += s


def _wire_clock(monkeypatch: pytest.MonkeyPatch) -> _Clock:
    clock = _Clock()
    monkeypatch.setattr(time, "monotonic", clock.monotonic)
    monkeypatch.setattr(time, "sleep", clock.sleep)
    return clock


# --- §6(c) mapping, row by row ---------------------------------------------------------


def test_verdict_no_run_is_absent() -> None:
    assert w.verdict(None) == "absent"


@pytest.mark.parametrize("status", ["queued", "in_progress", "waiting", "requested", "pending"])
def test_verdict_incomplete_is_pending(status: str) -> None:
    assert w.verdict(_run(status)) == "pending"


def test_verdict_completed_success_is_green() -> None:
    assert w.verdict(_run("completed", "success")) == "green"


@pytest.mark.parametrize("conclusion", ["failure", "cancelled", "timed_out",
                                        "action_required", "neutral", "skipped", "stale"])
def test_verdict_completed_non_success_is_red(conclusion: str) -> None:
    # The Item 6 falsifier direction: ANY non-success conclusion mapping to green would
    # wrongly attest the deploy gate. Only success is green — the witness never guesses.
    # In particular action_required/neutral/skipped are NOT the GitLab 'manual'→green case
    # (Q4: no manual gate ever sits inside `ci` on GitHub; the release is a separate
    # workflow_dispatch workflow).
    assert w.verdict(_run("completed", conclusion)) == "red"


def test_grace_constant_pinned() -> None:
    assert w.GRACE_S == 300.0                                   # §6(f)


# --- run_for: endpoint shape + newest-run-wins -----------------------------------------


def test_run_for_takes_newest_row_and_passes_token(monkeypatch: pytest.MonkeyPatch) -> None:
    seen: dict[str, Any] = {}

    def fake_get(path: str, token: str | None = None) -> Any:
        seen["path"], seen["token"] = path, token
        # Two rows: GitHub returns newest first (verified live 2026-07-12, journal) —
        # run_for must take rows[0], the same rule as the GitLab predecessor.
        return {"total_count": 2,
                "workflow_runs": [_run("completed", "success", 9),
                                  _run("completed", "failure", 8)]}

    monkeypatch.setattr(w, "_get", fake_get)
    got = w.run_for("a" * 40, token="tkn")
    assert got is not None and got["id"] == 9
    assert seen["path"] == f"/actions/workflows/ci.yml/runs?head_sha={'a' * 40}&per_page=1"
    assert seen["token"] == "tkn"


def test_run_for_none_when_no_runs(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(w, "_get",
                        lambda path, token=None: {"total_count": 0, "workflow_runs": []})
    assert w.run_for("b" * 40) is None


# --- check(): absent-grace loop (§6(f)) + terminal attestation --------------------------


def test_check_absent_within_grace_keeps_polling(monkeypatch: pytest.MonkeyPatch) -> None:
    clock = _wire_clock(monkeypatch)
    monkeypatch.setattr(w, "_keychain_token", lambda: None)
    attested: list[str] = []
    monkeypatch.setattr(w, "attest_verdict", lambda sha, run, v: attested.append(v))

    def run_for(sha: str, token: str | None = None) -> dict[str, Any] | None:
        # The run appears only after 120 s — inside GRACE_S (300): absent-before-grace
        # must be treated as pending (keep polling), not concluded.
        return _run("completed", "success", 42) if clock.t >= 120 else None

    monkeypatch.setattr(w, "run_for", run_for)
    assert w.check("c" * 40, wait_s=600.0) == 0
    assert attested == ["green"]
    assert clock.t >= 120                       # it genuinely polled past the appearance


def test_check_absent_past_grace_concludes_rc1(monkeypatch: pytest.MonkeyPatch,
                                               capsys: pytest.CaptureFixture[str]) -> None:
    clock = _wire_clock(monkeypatch)
    monkeypatch.setattr(w, "_keychain_token", lambda: None)
    monkeypatch.setattr(w, "attest_verdict",
                        lambda sha, run, v: pytest.fail("absent is never attested"))
    monkeypatch.setattr(w, "run_for", lambda sha, token=None: None)
    assert w.check("d" * 40, wait_s=600.0) == 1
    out = capsys.readouterr().out
    assert "no ci run" in out and "lag" in out  # §6(f): message names lag as likely cause
    assert clock.t >= w.GRACE_S                 # waited grace out — not absent-immediate


def test_check_grace_is_bounded_by_wait(monkeypatch: pytest.MonkeyPatch) -> None:
    clock = _wire_clock(monkeypatch)
    monkeypatch.setattr(w, "_keychain_token", lambda: None)
    monkeypatch.setattr(w, "run_for", lambda sha, token=None: None)
    assert w.check("e" * 40, wait_s=50.0) == 1  # grace = min(GRACE_S, wait_s) = 50
    assert clock.t <= 60.0                      # concluded at ~wait_s, not at GRACE_S


def test_check_pending_past_wait_rc1(monkeypatch: pytest.MonkeyPatch,
                                     capsys: pytest.CaptureFixture[str]) -> None:
    _wire_clock(monkeypatch)
    monkeypatch.setattr(w, "_keychain_token", lambda: None)
    monkeypatch.setattr(w, "attest_verdict",
                        lambda sha, run, v: pytest.fail("pending is never attested"))
    monkeypatch.setattr(w, "run_for", lambda sha, token=None: _run("in_progress", None, 7))
    assert w.check("f" * 40, wait_s=60.0) == 1
    assert "still in_progress" in capsys.readouterr().out


def test_check_red_attests_and_rc1(monkeypatch: pytest.MonkeyPatch) -> None:
    _wire_clock(monkeypatch)
    monkeypatch.setattr(w, "_keychain_token", lambda: None)
    attested: list[str] = []
    monkeypatch.setattr(w, "attest_verdict", lambda sha, run, v: attested.append(v))
    monkeypatch.setattr(w, "run_for",
                        lambda sha, token=None: _run("completed", "failure", 13))
    assert w.check("a" * 40, wait_s=600.0) == 1
    assert attested == ["red"]                  # red is attested history, not a silent rc


# --- attestation emission: §6(g) — same action names, run:<id> output -------------------


def test_attest_emission_shape(monkeypatch: pytest.MonkeyPatch) -> None:
    import config.loader
    import core.attestation
    emitted: dict[str, Any] = {}

    class _FakeAttestor:
        def emit(self, **kw: Any) -> None:
            emitted.update(kw)

    monkeypatch.setattr(config.loader, "get_config", lambda: None)
    monkeypatch.setattr(core.attestation, "build_attestor", lambda cfg: _FakeAttestor())
    w.attest_verdict("f" * 40, _run("completed", "success", 314), "green")
    # Action name pipeline_green PRESERVED (P3); only the output prefix moved to run: (D3).
    assert emitted == {"agent_role": "ci_witness", "action": "pipeline_green",
                       "input_hashes": ["f" * 40], "output_hashes": ["run:314"]}


# --- Keychain: the github-api service, degraded-when-absent ------------------------------


def test_keychain_reads_github_api_service(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: dict[str, Any] = {}

    class _R:
        returncode = 0
        stdout = "tok\n"

    def fake_run(cmd: list[str], capture_output: bool = False, text: bool = False) -> _R:
        calls["cmd"] = cmd
        return _R()

    monkeypatch.setattr(w.subprocess, "run", fake_run)
    assert w._keychain_token() == "tok"
    assert calls["cmd"] == ["security", "find-generic-password", "-a", "mind-palace",
                            "-s", "github-api", "-w"]            # §6(h)


# --- release(): §6(e) degradation chain + §6(d) mocked dispatch --------------------------


def test_release_rc1_when_not_green(monkeypatch: pytest.MonkeyPatch,
                                    capsys: pytest.CaptureFixture[str]) -> None:
    monkeypatch.setattr(w, "_keychain_token", lambda: None)
    monkeypatch.setattr(w, "run_for", lambda sha, token=None: _run("completed", "failure", 3))
    assert w.release("a" * 40) == 1
    assert "no green" in capsys.readouterr().out


def test_release_degrades_without_token(monkeypatch: pytest.MonkeyPatch,
                                        capsys: pytest.CaptureFixture[str]) -> None:
    monkeypatch.setattr(w, "_keychain_token", lambda: None)
    monkeypatch.setattr(w, "run_for", lambda sha, token=None: _run("completed", "success", 3))
    assert w.release("a" * 40) == 0             # degraded, never failed: deploy proceeds
    out = capsys.readouterr().out
    assert "by hand" in out and "github-api" in out
    assert "actions/workflows/release.yml" in out                # the dispatch URL to click


def test_release_dispatches_workflow(monkeypatch: pytest.MonkeyPatch,
                                     capsys: pytest.CaptureFixture[str]) -> None:
    monkeypatch.setattr(w, "_keychain_token", lambda: "tkn")
    monkeypatch.setattr(w, "run_for", lambda sha, token=None: _run("completed", "success", 3))
    captured: dict[str, Any] = {}

    class _Resp:
        status = 204                            # fire-and-forget per §6(d)

        def read(self) -> bytes:
            return b""

        def __enter__(self) -> _Resp:
            return self

        def __exit__(self, *a: object) -> None:
            return None

    def fake_urlopen(req: urllib.request.Request, timeout: float = 0) -> _Resp:
        assert isinstance(req.data, bytes)
        captured["url"] = req.full_url
        captured["method"] = req.get_method()
        captured["body"] = json.loads(req.data.decode())
        captured["auth"] = req.get_header("Authorization")
        return _Resp()

    monkeypatch.setattr(w.urllib.request, "urlopen", fake_urlopen)
    assert w.release("a" * 40) == 0
    assert captured["url"] == \
        "https://api.github.com/repos/ascalva/Mind-Palace/actions/workflows/release.yml/dispatches"
    assert captured["method"] == "POST"
    assert captured["body"] == {"ref": "main"}                   # §6(d)
    assert captured["auth"] == "Bearer tkn"
    assert "release in flight" in capsys.readouterr().out


def test_release_dispatch_404_degrades_to_local_play(monkeypatch: pytest.MonkeyPatch,
                                                     capsys: pytest.CaptureFixture[str]) -> None:
    monkeypatch.setattr(w, "_keychain_token", lambda: "tkn")
    monkeypatch.setattr(w, "run_for", lambda sha, token=None: _run("completed", "success", 3))

    def fake_urlopen(req: urllib.request.Request, timeout: float = 0) -> Any:
        raise urllib.error.HTTPError(req.full_url, 404, "Not Found",
                                     email.message.Message(), None)

    monkeypatch.setattr(w.urllib.request, "urlopen", fake_urlopen)
    assert w.release("a" * 40) == 0             # degraded, never failed (Item 10 parked case)
    assert "pnpm run release" in capsys.readouterr().out


# --- rotate(): guided-manual (Q7 — no GitHub self-rotation endpoint; deviation carried) ---


def test_rotate_is_guided_manual_rc1(capsys: pytest.CaptureFixture[str]) -> None:
    assert w.rotate() == 1                      # nothing rotated programmatically — rc 1
    out = capsys.readouterr().out
    # The re-mint route + the §6(h) Keychain store play, and never a secret.
    assert "fine-grained" in out.lower()
    assert "Actions" in out and "read" in out.lower() and "write" in out.lower()
    assert "security add-generic-password -U -a mind-palace -s github-api -w" in out
    assert "runbook" in out
