"""The CI witness — attest GitHub Actions verdicts into the chain (owner rule 2026-07-11;
re-pointed from GitLab per dn-ci-platform-and-runner-strategy D3, bp-016).

A green CI run is a claim by an external system; the witness turns it into an ATTESTED
fact: it fetches the `ci` workflow's newest run for a commit from the GitHub API and
emits `ci_witness / pipeline_green|pipeline_red` with the commit sha as input and
`run:<id>` as output — chained to the code-sensor's ingest of the same sha, so "this
commit's tests passed remotely" is signed history, not a memory of a web page. The
action names keep the `pipeline_` prefix on purpose (P3): chain history stays one
vocabulary across the host move; only the output prefix changed (`pipeline:` → `run:`).

Zone note, stated honestly: this runs UNSEALED at the ops tier and talks to
api.github.com (stdlib urllib) — the restic/terraform precedent (ops tools reach
services from their own process; the sealed core never does). It is invoked standalone
or as a subprocess of `palace deploy` (whose own process IS sealed; the witness child
is not).

Auth: run metadata on this public repo needs no token, but unauthenticated reads are
rate-limited (60/h/IP — one 600 s poll at 10 s intervals consumes the hour) and
dispatching the release workflow requires one — read from Keychain (`security
find-generic-password -a mind-palace -s github-api -w`), never from config or argv.
Absent a token, reads degrade to unauthenticated and `release` degrades to printing
the dispatch URL for a by-hand play (runbook §CI witness).
"""

from __future__ import annotations

import json
import subprocess
import urllib.error
import urllib.request
from typing import Any

REPO = "ascalva/Mind-Palace"
API = "https://api.github.com/repos/" + REPO
# The gate workflow, queried BY FILE PATH (immune to display-name edits — plan Q3);
# the release workflow the witness dispatches after green (§6(d)).
WORKFLOW = "ci.yml"
RELEASE_WORKFLOW = "release.yml"

# Absent-grace (§6(f)): GitHub creates workflow runs asynchronously after a push, so a
# just-pushed sha can be legitimately runless for a while. Inside check()'s poll loop an
# `absent` verdict younger than min(GRACE_S, wait_s) is treated as pending; verdict()
# itself stays pure — absent is absent. (GitLab created pipelines synchronously, so the
# old witness could conclude absent immediately.) Sized ≤ the 600 s poll and ≥ the
# observed mirror batch; the origin re-point (2026-07-12) makes lag ~0 — the constant is
# revisited at first post-migration triage (plan §11).
GRACE_S = 300.0


def _headers(token: str | None) -> dict[str, str]:
    h = {"Accept": "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28"}
    if token:
        h["Authorization"] = f"Bearer {token}"
    return h


def _get(path: str, token: str | None = None) -> Any:
    # JSON HTTP boundary: Any is the honest shape here (same warranted pattern as
    # core/models/ollama_client.py's JSON boundary); callers narrow per call site rather
    # than this helper guessing.
    req = urllib.request.Request(API + path, headers=_headers(token))
    with urllib.request.urlopen(req, timeout=20) as r:  # noqa: S310 — fixed https host
        return json.load(r)


def _keychain_token() -> str | None:
    r = subprocess.run(["security", "find-generic-password", "-a", "mind-palace",
                        "-s", "github-api", "-w"], capture_output=True, text=True)
    return r.stdout.strip() or None if r.returncode == 0 else None


def run_for(sha: str, token: str | None = None) -> dict[str, Any] | None:
    """Newest `ci` run for the commit, or None if GitHub has none for it.

    GitHub returns workflow runs newest-first (verified empirically 2026-07-12, bp-016
    journal) — rows[0] is the newest, the same "newest run wins" rule the GitLab
    predecessor used for re-run/dispatch duplicates.
    """
    data = _get(f"/actions/workflows/{WORKFLOW}/runs?head_sha={sha}&per_page=1", token)
    runs = data.get("workflow_runs") if isinstance(data, dict) else None
    return runs[0] if isinstance(runs, list) and runs else None


def verdict(run: dict[str, Any] | None) -> str:
    """'green' | 'red' | 'pending' | 'absent' — the witness never guesses (P3)."""
    if run is None:
        return "absent"
    if run["status"] != "completed":
        return "pending"          # queued | in_progress | waiting | requested | pending
    # Only success is green. Every other completed conclusion — failure, cancelled,
    # timed_out, action_required, neutral, skipped, stale — is red. There is no
    # GitLab-'manual'→green analogue here (plan Q4): the release is a separate
    # workflow_dispatch workflow, never a manual gate inside `ci`.
    return "green" if run["conclusion"] == "success" else "red"


def attest_verdict(sha: str, run: dict[str, Any], v: str) -> None:
    from config.loader import get_config
    from core.attestation import build_attestor

    attestor = build_attestor(get_config())
    if attestor is not None:
        # Action names pipeline_green|pipeline_red PRESERVED across the host move (P3 —
        # chain history stays one vocabulary); only the output prefix changed (D3).
        attestor.emit(agent_role="ci_witness", action=f"pipeline_{v}",
                      input_hashes=[sha], output_hashes=[f"run:{run['id']}"])


def check(sha: str, *, wait_s: float = 600.0) -> int:
    """Poll to a terminal verdict, attest it, rc 0 only on green.

    Absent-grace per §6(f): an absent verdict with elapsed < min(GRACE_S, wait_s) keeps
    polling (run creation is asynchronous); still absent past grace concludes absent.
    """
    import time
    token = _keychain_token()                 # degrades to unauthenticated when absent
    start = time.monotonic()
    deadline = start + wait_s
    grace = min(GRACE_S, wait_s)
    run = run_for(sha, token)
    v = verdict(run)
    while (v == "pending" or (v == "absent" and time.monotonic() - start < grace)) \
            and time.monotonic() < deadline:
        time.sleep(10)
        run = run_for(sha, token)
        v = verdict(run)
    if v == "absent":
        print(f"ci-witness: no ci run for {sha[:12]} after {grace:.0f}s grace — was it "
              "pushed? (every main push triggers `ci`; run creation is asynchronous, and "
              "residual mirror/propagation lag is the likely cause if the push just landed)")
        return 1
    # verdict(None) is always "absent" (see verdict()) — v != "absent" here means run is set.
    assert run is not None
    if v == "pending":
        print(f"ci-witness: run {run['id']} still {run['status']} after {wait_s:.0f}s")
        return 1
    attest_verdict(sha, run, v)
    print(f"ci-witness: run {run['id']} {v.upper()} for {sha[:12]} — attested")
    return 0 if v == "green" else 1


def rotate() -> int:
    """Guided-manual PAT rotation — an OPEN DEVIATION from the design note's "mirroring
    the gitlab-api pattern including rotate()" (dn-ci-platform-and-runner-strategy D3),
    carried per bp-016 Item 8/Q7: GitHub exposes NO self-rotation endpoint for user
    fine-grained PATs (re-verified against the REST docs at build time, 2026-07-12 —
    the only PAT endpoints are org-admin management, not self-service; GitLab's
    `POST /personal_access_tokens/self/rotate` has no equivalent). Rotation is therefore
    a by-hand play: re-mint in the web UI, then store to Keychain. rc 1 always —
    printing instructions is not rotating, and no caller may mistake it for done.
    No secret is read, printed, or stored by this function (Invariant 10)."""
    print(
        "ci-witness: GitHub has no self-rotation API for user PATs — rotate by hand:\n"
        f"  1. github.com → Settings → Developer settings → Fine-grained personal access\n"
        f"     tokens → regenerate (or re-mint) the token scoped to {REPO} with\n"
        "     repository permission Actions: read and write (nothing else).\n"
        "  2. Store it (overwrites in place):\n"
        "     security add-generic-password -U -a mind-palace -s github-api -w <PAT>\n"
        "  Details: docs/runbook.md §CI witness."
    )
    return 1


def release(sha: str) -> int:
    """Dispatch the release workflow after confirming the sha is green (token required).

    Degradation chain (§6(e), parity with the GitLab manual-play predecessor):
    not green → rc 1 · no token → print the dispatch URL for a by-hand play, rc 0 ·
    dispatch 404 (release workflow not landed) → print the local play, rc 0 —
    degraded, never failed: deploy proceeds.
    """
    token = _keychain_token()
    run = run_for(sha, token)
    if verdict(run) != "green":
        print(f"ci-witness: no green ci run for {sha[:12]} — nothing to release.")
        return 1
    if token is None:
        print("ci-witness: no github-api token in Keychain — dispatch the release by hand:\n"
              f"  https://github.com/{REPO}/actions/workflows/{RELEASE_WORKFLOW}\n"
              "  (one-time setup: security add-generic-password -U -a mind-palace "
              "-s github-api -w <fine-grained PAT, Actions read+write>)")
        return 0                                    # degraded, not failed: deploy proceeds
    req = urllib.request.Request(
        f"{API}/actions/workflows/{RELEASE_WORKFLOW}/dispatches",
        data=json.dumps({"ref": "main"}).encode(),
        headers={**_headers(token), "Content-Type": "application/json"},
        method="POST")
    try:
        with urllib.request.urlopen(req, timeout=20):  # noqa: S310 — fixed https host
            pass                                       # 204 No Content: fire-and-forget
    except urllib.error.HTTPError as e:
        if e.code == 404:
            print("ci-witness: release workflow not found on GitHub (bp-016 Item 10 "
                  "parked?) — cut locally: `pnpm run release` (D4 interim)")
            return 0                                # degraded, not failed
        raise
    print(f"ci-witness: dispatched {RELEASE_WORKFLOW} (ref main) — release in flight:\n"
          f"  https://github.com/{REPO}/actions/workflows/{RELEASE_WORKFLOW}")
    return 0
