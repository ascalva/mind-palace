"""The CI witness — attest GitLab pipeline verdicts into the chain (owner rule 2026-07-11).

A green pipeline is a claim by an external system; the witness turns it into an
ATTESTED fact: it fetches the pipeline for a commit from the GitLab API and emits
`ci_witness / pipeline_green|pipeline_red` with the commit sha as input and
`pipeline:<id>` as output — chained to the code-sensor's ingest of the same sha, so
"this commit's tests passed remotely" is signed history, not a memory of a web page.

Zone note, stated honestly: this runs UNSEALED at the ops tier and talks to gitlab.com
(stdlib urllib) — the restic/terraform precedent (ops tools reach services from their
own process; the sealed core never does). It is invoked standalone or as a subprocess
of `palace deploy` (whose own process IS sealed; the witness child is not).

Auth: pipeline metadata on this project is public (no token). Playing the manual
semantic-release job needs a token — read from Keychain (`security find-generic-password
-a mind-palace -s gitlab-api -w`), never from config or argv. Absent a token, `release`
degrades to printing the pipeline URL for a by-hand play.
"""

from __future__ import annotations

import json
import subprocess
import urllib.parse
import urllib.request
from typing import Any

PROJECT = "ascalva-projects/mind-palace"
API = "https://gitlab.com/api/v4/projects/" + urllib.parse.quote(PROJECT, safe="")

# pipeline states that still have a verdict coming (poll); everything else is terminal
_PENDING = {"created", "waiting_for_resource", "preparing", "pending", "running"}


def _get(path: str, token: str | None = None) -> Any:
    # JSON HTTP boundary: GitLab's API returns a list (pipelines/jobs listing) or a dict
    # (single-resource endpoints) depending on the path — Any is the honest shape here (same
    # warranted pattern as core/models/ollama_client.py's JSON boundary); callers narrow per
    # call site (isinstance checks / TypedDict-shaped access) rather than this helper guessing.
    req = urllib.request.Request(API + path)
    if token:
        req.add_header("PRIVATE-TOKEN", token)
    with urllib.request.urlopen(req, timeout=20) as r:  # noqa: S310 — fixed https host
        return json.load(r)


def _keychain_token() -> str | None:
    r = subprocess.run(["security", "find-generic-password", "-a", "mind-palace",
                        "-s", "gitlab-api", "-w"], capture_output=True, text=True)
    return r.stdout.strip() or None if r.returncode == 0 else None


def pipeline_for(sha: str) -> dict[str, Any] | None:
    """Newest pipeline for the commit, or None if GitLab has none for it."""
    rows = _get(f"/pipelines?sha={sha}&per_page=1")
    return rows[0] if isinstance(rows, list) and rows else None


def verdict(pipe: dict[str, Any] | None) -> str:
    """'green' | 'red' | 'pending' | 'absent' — the witness never guesses."""
    if pipe is None:
        return "absent"
    if pipe["status"] in _PENDING:
        return "pending"
    # 'manual' = all automatic jobs done, only manual gates (semantic-release) remain: green.
    return "green" if pipe["status"] in ("success", "manual") else "red"


def attest_verdict(sha: str, pipe: dict[str, Any], v: str) -> None:
    from config.loader import get_config
    from core.attestation import build_attestor

    attestor = build_attestor(get_config())
    if attestor is not None:
        attestor.emit(agent_role="ci_witness", action=f"pipeline_{v}",
                      input_hashes=[sha], output_hashes=[f"pipeline:{pipe['id']}"])


def check(sha: str, *, wait_s: float = 600.0) -> int:
    """Poll to a terminal verdict, attest it, rc 0 only on green."""
    import time
    deadline = time.monotonic() + wait_s
    pipe = pipeline_for(sha)
    while verdict(pipe) == "pending" and time.monotonic() < deadline:
        time.sleep(10)
        pipe = pipeline_for(sha)
    v = verdict(pipe)
    if v == "absent":
        print(f"ci-witness: no pipeline for {sha[:12]} — was it pushed? (docs-only pushes "
              "still create a pipeline; a missing one means the sha never reached origin)")
        return 1
    # verdict(None) is always "absent" (see verdict()) — v != "absent" here means pipe is set.
    assert pipe is not None
    if v == "pending":
        print(f"ci-witness: pipeline {pipe['id']} still {pipe['status']} after {wait_s:.0f}s")
        return 1
    attest_verdict(sha, pipe, v)
    print(f"ci-witness: pipeline {pipe['id']} {v.upper()} for {sha[:12]} — attested")
    return 0 if v == "green" else 1


def _api_root(path: str, token: str, *, method: str = "GET", timeout: int = 20) -> Any:
    """Top-level (non-project) API call — rotation lives at /personal_access_tokens/…"""
    req = urllib.request.Request("https://gitlab.com/api/v4" + path, method=method,
                                 headers={"PRIVATE-TOKEN": token})
    with urllib.request.urlopen(req, timeout=timeout) as r:  # noqa: S310 — fixed https host
        return json.load(r)


def rotation_expiry(days: int = 30) -> str:
    from datetime import date, timedelta
    return (date.today() + timedelta(days=days)).isoformat()


def rotate() -> int:
    """Self-rotate the Keychain token (owner rule 2026-07-11): the old token is revoked
    server-side the moment rotation succeeds, so the ordering is fail-safe by design —
    VERIFY the new token works, THEN overwrite Keychain, THEN read back and compare,
    THEN attest the event (token id + expiry; never the secret). Any failure after
    rotation prints loud instructions to re-mint — the fail state is a dead token and
    a five-minute manual re-mint, never a silently broken credential.

    Residual exposure, stated honestly: `security add-generic-password -w` places the
    secret on argv for the write (same exposure as the owner's one-time setup command,
    single-user Mac). Keychain has no stdin write path for -w; accepted and recorded."""
    token = _keychain_token()
    if token is None:
        print("ci-witness: no gitlab-api token in Keychain — nothing to rotate. "
              "Mint one first (runbook §CI witness).")
        return 1
    rotated = _api_root(f"/personal_access_tokens/self/rotate?expires_at={rotation_expiry()}",
                        token, method="POST")
    new_token, new_id = rotated["token"], rotated.get("id", "?")
    try:
        _api_root("/personal_access_tokens/self", new_token)   # prove it works before storing
        subprocess.run(["security", "add-generic-password", "-U", "-a", "mind-palace",
                        "-s", "gitlab-api", "-w", new_token], check=True, capture_output=True)
        if _keychain_token() != new_token:
            raise RuntimeError("keychain read-back mismatch")
    except Exception as e:  # noqa: BLE001 — the old token is already dead; be LOUD
        print(f"ci-witness: ROTATION STORE FAILED ({e}) — the old token is revoked and the "
              "new one was NOT stored. Re-mint by hand: gitlab → access tokens → api scope, "
              "then: security add-generic-password -U -a mind-palace -s gitlab-api -w <TOKEN>")
        return 1
    from config.loader import get_config
    from core.attestation import build_attestor
    attestor = build_attestor(get_config())
    if attestor is not None:
        attestor.emit(agent_role="ci_witness", action="token_rotated",
                      input_hashes=[f"token:{new_id}"],
                      output_hashes=[f"expires:{rotated.get('expires_at', '?')}"])
    print(f"ci-witness: token rotated (id {new_id}, expires {rotated.get('expires_at')}) — "
          "stored + attested")
    return 0


def release(sha: str) -> int:
    """Play the manual semantic-release job for the sha's pipeline (token required)."""
    pipe = pipeline_for(sha)
    if verdict(pipe) != "green":
        print(f"ci-witness: no green pipeline for {sha[:12]} — nothing to release.")
        return 1
    # verdict(None) is always "absent" ("green" required above) — pipe is set here.
    assert pipe is not None
    token = _keychain_token()
    if token is None:
        print("ci-witness: no gitlab-api token in Keychain — play semantic-release by hand:\n"
              f"  {pipe['web_url']}\n"
              "  (one-time setup: security add-generic-password -a mind-palace "
              "-s gitlab-api -w <PAT with api scope>)")
        return 0                                    # degraded, not failed: deploy proceeds
    jobs = _get(f"/pipelines/{pipe['id']}/jobs?scope[]=manual", token)
    rel = [j for j in jobs if j["name"] == "semantic-release"]
    if not rel:
        print("ci-witness: no manual semantic-release job on this pipeline — nothing to play.")
        return 0
    req = urllib.request.Request(API + f"/jobs/{rel[0]['id']}/play", method="POST",
                                 headers={"PRIVATE-TOKEN": token})
    with urllib.request.urlopen(req, timeout=20) as r:  # noqa: S310
        played = json.load(r)
    print(f"ci-witness: played semantic-release (job {played['id']}) — release in flight")
    return 0
