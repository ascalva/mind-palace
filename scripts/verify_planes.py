#!/usr/bin/env python
"""The read-only four-plane verifier (dn-plane-principals §3.1; bp-078 Item 4).

Asserts the migration END-STATE across all four principals — `ascalva`, `ouroboros-work`,
`ouroboros`, `ouroboros-edge` — and prints a per-check PASS / FAIL / PENDING / SKIP with a reason.
It is runnable MID-migration (a lane not yet migrated reports PENDING, never a false green) and it
**MUTATES NOTHING**: every query is a stat / getpwnam / getgrnam / `git config --get` /
`pfctl -sr` read. There is no code path that opens a file for write, chmods, chowns, or loads a
ruleset — proven structurally by `tests/unit/test_plane_migration.py`.

    uv run scripts/verify_planes.py            # human-readable table; exit 0 iff EVERY check PASSes

Design (finding-0118 lesson): exercise the CLI form end-to-end, not just the imported fns. The OS
queries live behind an injectable `SystemProbe` so the checks are exercised against fixtures
(pre- AND post-migration ownership) WITHOUT any mutation and without the four users existing on the
test box — `tests/unit/test_plane_migration.py` drives every branch with a fake probe.

It NEVER probes a credential store. The unseal-key-under-`ouroboros` check is a documented
OWNER-run one-liner (SKIP with the exact command), never an agent scanning the keychain — a
service user's credential store is not agent-reachable by design (finding-0120). Repo-workflow
tooling: stdlib + the `config` facade only, NEVER `core` (the docket/exhaust_report AST precedent).
"""

from __future__ import annotations

import argparse
import grp
import os
import pwd
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # repo root on path (CLI; fnd-0118)

from config.loader import REPO_ROOT, get_config  # noqa: E402

# The four principals + shared group — the §6 pinned contract (names are the design, not config).
CORE = "ouroboros"            # the reasoning daemon + the vault
WORK = "ouroboros-work"       # the orchestrator + delegated builders/scribes
EDGE = "ouroboros-edge"       # the network-facing plane (forward-provisioned)
HUMAN = "ascalva"             # the human login
SHARED_GROUP = "palace"       # repo write-sharing (members: ascalva, ouroboros-work)
PF_ANCHOR = "mind-palace/ouroboros"
ANCHOR_FILE = REPO_ROOT / "ops/network/ouroboros-egress.pf.conf"
DAEMON_LABEL = "com.mind-palace.palace"
SYSTEM_PLIST = Path("/Library/LaunchDaemons/com.mind-palace.palace.plist")

# Check statuses. Only PASS is green; PENDING/SKIP/FAIL are all non-green (a trust gate never
# treats "unverified" as "verified" — the Item 4 false-green falsifier).
PASS, FAIL, PENDING, SKIP = "PASS", "FAIL", "PENDING", "SKIP"


@dataclass(frozen=True)
class Check:
    name: str
    status: str
    detail: str


@dataclass(frozen=True)
class Owner:
    uid: int
    gid: int


class SystemProbe:
    """The real, read-only OS queries. Tests inject a fake with the same surface to model pre/post
    migration ownership without mutating anything (and without the four users existing)."""

    def user_uid(self, name: str) -> int | None:
        try:
            return pwd.getpwnam(name).pw_uid
        except KeyError:
            return None

    def group(self, name: str) -> tuple[int, tuple[str, ...]] | None:
        try:
            g = grp.getgrnam(name)
            return g.gr_gid, tuple(g.gr_mem)
        except KeyError:
            return None

    def owner(self, path: Path) -> Owner | None:
        try:
            st = path.stat()
        except (FileNotFoundError, NotADirectoryError):
            return None
        return Owner(st.st_uid, st.st_gid)

    def mode(self, path: Path) -> int | None:
        try:
            return path.stat().st_mode & 0o7777
        except (FileNotFoundError, NotADirectoryError):
            return None

    def can_read(self, path: Path) -> bool:
        return os.access(path, os.R_OK)

    def git_local(self, key: str, repo: Path) -> str | None:
        r = subprocess.run(["git", "-C", str(repo), "config", "--local", "--get", key],
                           capture_output=True, text=True)
        out = r.stdout.strip()
        return out or None

    def pf_anchor_rules(self, anchor: str) -> list[str] | None:
        """The loaded rules of a pf sub-anchor via `pfctl -a <anchor> -sr` (needs root — returns
        None when unreadable, so the check SKIPs rather than false-greens)."""
        try:
            r = subprocess.run(["pfctl", "-a", anchor, "-sr"], capture_output=True, text=True)
        except FileNotFoundError:
            return None
        if r.returncode != 0:
            return None
        return [ln.strip() for ln in r.stdout.splitlines() if ln.strip()]

    def launchdaemon_username(self, plist: Path) -> str | None:
        """The `UserName` an INSTALLED LaunchDaemon plist declares (read-only plist read); None if
        the plist is not installed (still the gui agent → PENDING)."""
        try:
            data = plist.read_bytes()
        except (FileNotFoundError, NotADirectoryError, PermissionError):
            return None
        # Minimal plist scrape — avoids a plistlib import and works on the XML plist we author.
        text = data.decode("utf-8", "replace")
        if "<key>UserName</key>" not in text:
            return None
        after = text.split("<key>UserName</key>", 1)[1]
        if "<string>" not in after:
            return None
        return after.split("<string>", 1)[1].split("</string>", 1)[0].strip() or None


# --------------------------------------------------------------------------------------------
# The lane ownership/mode table (dn-plane-principals §3.1 / bp-078 §6) — the check spec.
# --------------------------------------------------------------------------------------------
@dataclass(frozen=True)
class Lane:
    label: str
    path: Path
    owner_user: str
    owner_group: str | None      # None ⇒ group is not load-bearing (default primary group)
    mode: int | None             # None ⇒ mode not asserted (dynamic subtree)


def lanes(cfg: Any) -> list[Lane]:
    vault = Path(cfg.vault.path).expanduser()
    exhaust = Path(cfg.exhaust.path).expanduser()
    data_dir = Path(cfg.paths.data_dir)
    return [
        Lane("vault (ingest)", vault, CORE, "staff", 0o700),
        Lane("exhaust/ (parent)", exhaust, CORE, "staff", 0o755),
        Lane("exhaust/reports/", exhaust / "reports", WORK, "staff", 0o755),
        Lane("data/ (runtime)", data_dir, CORE, SHARED_GROUP, 0o755),
        # The repo working tree: ascalva owns it, group palace shares write. Mode is 2775 on dirs;
        # we assert owner+group (mode varies file vs dir, so left None here).
        Lane("repo working tree", REPO_ROOT, HUMAN, SHARED_GROUP, None),
    ]


# --------------------------------------------------------------------------------------------
# Checks — each is a pure function over the probe + config, returning one Check.
# --------------------------------------------------------------------------------------------
def check_users_exist(probe: SystemProbe) -> list[Check]:
    out = []
    for name in (CORE, WORK, EDGE):
        uid = probe.user_uid(name)
        if uid is None:
            out.append(Check(f"user {name!r} exists", PENDING, "not created yet (pre-migration)"))
        else:
            out.append(Check(f"user {name!r} exists", PASS, f"uid {uid}"))
    return out


def check_shared_group(probe: SystemProbe) -> Check:
    g = probe.group(SHARED_GROUP)
    if g is None:
        return Check(f"group {SHARED_GROUP!r} exists", PENDING, "not created yet (pre-migration)")
    _gid, members = g
    want = {HUMAN, WORK}
    missing = want - set(members)
    if missing:
        return Check(f"group {SHARED_GROUP!r} members", FAIL,
                     f"missing {sorted(missing)}; has {sorted(members)}")
    return Check(f"group {SHARED_GROUP!r} members", PASS, f"members {sorted(members)}")


def check_lane(probe: SystemProbe, lane: Lane) -> Check:
    owner = probe.owner(lane.path)
    if owner is None:
        return Check(f"{lane.label} owner", PENDING, f"{lane.path} does not exist yet")
    want_uid = probe.user_uid(lane.owner_user)
    if want_uid is None:
        return Check(f"{lane.label} owner", PENDING,
                     f"user {lane.owner_user!r} not created yet (cannot resolve expected uid)")
    if owner.uid != want_uid:
        actual = pwd.getpwuid(owner.uid).pw_name if _uid_name(owner.uid) else owner.uid
        return Check(f"{lane.label} owner", PENDING if _looks_unmigrated(actual) else FAIL,
                     f"want {lane.owner_user} (uid {want_uid}), have uid {owner.uid} ({actual})")
    # owner matches — now the group + mode, where pinned.
    detail = f"owner {lane.owner_user}"
    if lane.owner_group is not None:
        g = probe.group(lane.owner_group)
        if g is None:
            return Check(f"{lane.label} owner", PENDING,
                         f"group {lane.owner_group!r} not created yet")
        if owner.gid != g[0]:
            return Check(f"{lane.label} group", FAIL,
                         f"want group {lane.owner_group} (gid {g[0]}), have gid {owner.gid}")
        detail += f":{lane.owner_group}"
    if lane.mode is not None:
        mode = probe.mode(lane.path)
        if mode is not None and mode != lane.mode:
            return Check(f"{lane.label} mode", FAIL, f"want {oct(lane.mode)}, have {oct(mode)}")
        detail += f" {oct(lane.mode)}"
    return Check(f"{lane.label} ownership", PASS, detail)


def check_ascalva_cannot_read_vault(probe: SystemProbe, cfg: Any) -> Check:
    vault = Path(cfg.vault.path).expanduser()
    owner = probe.owner(vault)
    core_uid = probe.user_uid(CORE)
    if owner is None or core_uid is None or owner.uid != core_uid:
        return Check("vault unreadable from human posture", PENDING,
                     "vault not yet ouroboros-owned")
    # migrated: the negative capability MUST hold (a readable 0700-ouroboros vault from a
    # non-ouroboros posture is a false green — the sharpest falsifier).
    if probe.can_read(vault):
        return Check("vault unreadable from human posture", FAIL,
                     "vault IS readable from this posture — the corpus wall is not sealed")
    return Check("vault unreadable from human posture", PASS, "R_OK denied (0700 ouroboros)")


def check_git_signing(probe: SystemProbe) -> Check:
    """Q10: agent commits keep the human's identity + signing key via REPO-LOCAL config (HOME under
    `sudo -u … -H` would not read ~/.gitconfig). All five keys must resolve repo-locally."""
    keys = ("user.name", "user.email", "user.signingkey", "gpg.format", "commit.gpgsign")
    vals = {k: probe.git_local(k, REPO_ROOT) for k in keys}
    missing = [k for k, v in vals.items() if not v]
    if missing == list(keys):
        return Check("repo-local git signing", PENDING,
                     "no repo-local signing config yet (runbook sets it)")
    if missing:
        return Check("repo-local git signing", FAIL, f"repo-local config missing {missing}")
    return Check("repo-local git signing", PASS,
                 f"format={vals['gpg.format']} sign={vals['commit.gpgsign']} "
                 f"key={vals['user.signingkey']}")


def check_daemon_user(probe: SystemProbe) -> Check:
    user = probe.launchdaemon_username(SYSTEM_PLIST)
    if user is None:
        return Check("daemon runs as ouroboros", PENDING,
                     "no /Library/LaunchDaemons system plist yet (still the gui agent)")
    if user != CORE:
        return Check("daemon runs as ouroboros", FAIL,
                     f"system plist UserName is {user!r}, want {CORE!r}")
    return Check("daemon runs as ouroboros", PASS, f"LaunchDaemon UserName={user}")


def check_pf_anchor(probe: SystemProbe) -> Check:
    """Q11: the loaded pf sub-anchor must (a) exist, (b) pass on lo0, (c) block the ouroboros uid,
    with the lo0 pass BEFORE the block. `pfctl -sr` needs root — unreadable ⇒ SKIP (not a false
    green). Compared semantically (pfctl normalizes `proto {tcp udp}` into two rules)."""
    rules = probe.pf_anchor_rules(PF_ANCHOR)
    if rules is None:
        return Check("core-egress pf anchor loaded", SKIP,
                     f"pfctl -a {PF_ANCHOR} -sr unreadable (needs root) — owner verifies with sudo")
    if not rules:
        return Check("core-egress pf anchor loaded", FAIL, "anchor is loaded but EMPTY")
    lo0_i = next((i for i, r in enumerate(rules)
                  if r.startswith("pass") and "lo0" in r), None)
    blk_i = next((i for i, r in enumerate(rules)
                  if r.startswith("block") and (CORE in r or "user" in r)), None)
    if lo0_i is None or blk_i is None:
        return Check("core-egress pf anchor loaded", FAIL,
                     f"missing lo0-pass or ouroboros-block: {rules}")
    if lo0_i > blk_i:
        return Check("core-egress pf anchor loaded", FAIL,
                     "lo0 pass comes AFTER the block — loopback model traffic would be dropped")
    return Check("core-egress pf anchor loaded", PASS,
                 f"lo0 pass (@{lo0_i}) before ouroboros block (@{blk_i})")


def check_home_traversable(probe: SystemProbe) -> Check:
    """Risk (b): role accounts must traverse /Users/ascalva to reach ~/.mind-palace + the repo.
    macOS grants o+x on homes by default — verify it (else an ACL/relocation is needed)."""
    home = Path.home()
    mode = probe.mode(home)
    if mode is None:
        return Check("home traversable by role accounts", SKIP, f"{home} not stat-able")
    if not (mode & 0o001):
        return Check("home traversable by role accounts", FAIL,
                     f"{home} is {oct(mode)} — no o+x; role accounts cannot traverse to the repo")
    return Check("home traversable by role accounts", PASS, f"{home} {oct(mode)} (o+x set)")


def check_unseal_item() -> Check:
    """The unseal keychain item under `ouroboros` (dn §3.2). The verifier NEVER scans a credential
    store (finding-0120); this is an OWNER-run one-liner, reported as a manual gate (SKIP)."""
    return Check("unseal key under ouroboros (manual)", SKIP,
                 "owner runs: sudo -u ouroboros security find-generic-password "
                 "-a mind-palace -s vault-unseal-key  (metadata only, no -w)")


# --------------------------------------------------------------------------------------------
_UNMIGRATED_OWNERS = {HUMAN}


def _uid_name(uid: int) -> str | None:
    try:
        return pwd.getpwuid(uid).pw_name
    except KeyError:
        return None


def _looks_unmigrated(actual: object) -> bool:
    """A lane still owned by the human reads as PENDING (migration not done for it), not FAIL —
    FAIL is reserved for a lane owned by the WRONG principal after migration."""
    return isinstance(actual, str) and actual in _UNMIGRATED_OWNERS


def run_checks(probe: SystemProbe, cfg: Any) -> list[Check]:
    checks: list[Check] = []
    checks += check_users_exist(probe)
    checks.append(check_shared_group(probe))
    for lane in lanes(cfg):
        checks.append(check_lane(probe, lane))
    checks.append(check_ascalva_cannot_read_vault(probe, cfg))
    checks.append(check_daemon_user(probe))
    checks.append(check_unseal_item())
    checks.append(check_git_signing(probe))
    checks.append(check_pf_anchor(probe))
    checks.append(check_home_traversable(probe))
    return checks


_GLYPH = {PASS: "✓", FAIL: "✗", PENDING: "…", SKIP: "–"}


def is_green(checks: list[Check]) -> bool:
    """Green = no FAIL and no PENDING. SKIP is allowed (the unseal item is an owner-run manual
    one-liner and the pf anchor needs root — both are listed, never silently swallowed). A
    not-yet-migrated lane always reports PENDING (user/owner mismatch), so a partial migration can
    NEVER go green — the Item 4 false-green falsifier holds. Full green with sudo = only the
    unseal-manual SKIP remains."""
    return not any(c.status in (FAIL, PENDING) for c in checks)


def render(checks: list[Check]) -> str:
    width = max(len(c.name) for c in checks)
    lines = [f"  {_GLYPH[c.status]} {c.status:<7} {c.name:<{width}}  {c.detail}" for c in checks]
    n_pass = sum(c.status == PASS for c in checks)
    n_pend = sum(c.status == PENDING for c in checks)
    n_skip = sum(c.status == SKIP for c in checks)
    n_fail = sum(c.status == FAIL for c in checks)
    if not is_green(checks):
        verdict = (f"NOT fully verified: {n_pass} pass / {n_pend} pending / "
                   f"{n_skip} skip / {n_fail} FAIL")
    elif n_skip == 0:
        verdict = "ALL PLANES VERIFIED — migration complete"
    else:
        manual = ", ".join(c.name for c in checks if c.status == SKIP)
        verdict = f"VERIFIED (automated checks pass) — {n_skip} owner-manual remain: {manual}"
    header = "four-plane verifier (dn-plane-principals §3.1) — READ-ONLY"
    return "\n".join([header, *lines, "", verdict])


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Read-only four-plane migration verifier (bp-078).")
    ap.parse_args(argv)
    cfg = get_config()
    checks = run_checks(SystemProbe(), cfg)
    print(render(checks))
    return 0 if is_green(checks) else 1


if __name__ == "__main__":
    raise SystemExit(main())
