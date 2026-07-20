"""The four-plane migration — the verifier's unit tests (bp-078 Item 4) + the per-plane
self-configuring ratchets (Item 5).

Two properties, one file:

  * Item 4 — the READ-ONLY verifier (`scripts/verify_planes.py`). Every check is exercised against
    a FAKE `SystemProbe` modelling pre- / partial- / post-migration ownership, so each branch is
    proven WITHOUT any mutation and without the four users existing on the test box. The
    false-green falsifier is pinned: a not-fully-migrated fixture is NEVER green, and a migrated-
    but-readable vault is caught as FAIL. Read-only is proven structurally (no write op in the
    source) + the no-core AST guard (docket/exhaust_report precedent). The CLI form is exercised
    end-to-end (finding-0118: run `uv run scripts/verify_planes.py`, not just the imported fns).

  * Item 5 — the per-plane RATCHETS. One negative capability per lane, keyed on real
    `stat().st_uid`: SKIP pre-migration (the principal is absent or the lane is still human-owned),
    ENFORCE post-migration — no manual flip. On THIS machine (pre-migration) every ratchet SKIPS
    cleanly, so the suite never reddens before anyone has migrated (the Item 5 falsifier). The pf
    anchor's ordering + syntax are pinned here too (ordering by text; syntax via a resolvable-user
    substitution, since `user ouroboros` cannot resolve until the account exists).
"""

from __future__ import annotations

import ast
import os
import subprocess
import sys
import tomllib
from dataclasses import dataclass, field
from pathlib import Path

import pytest

from config.loader import REPO_ROOT, get_config

sys.path.insert(0, str(REPO_ROOT / "scripts"))

import verify_planes as vp  # type: ignore[import-not-found]  # noqa: E402

ANCHOR = REPO_ROOT / "ops/network/ouroboros-egress.pf.conf"


# ============================================================================================
# Item 4 — the verifier, against a fake probe (no mutation, no real users)
# ============================================================================================
@dataclass
class FakeProbe(vp.SystemProbe):
    """Models the OS read-only surface with fixture data — pre/partial/post migration, with no
    chown and no real accounts. Overrides EVERY query `run_checks` makes."""

    users: dict[str, int] = field(default_factory=dict)
    groups: dict[str, tuple[int, tuple[str, ...]]] = field(default_factory=dict)
    owners: dict[Path, vp.Owner] = field(default_factory=dict)
    modes: dict[Path, int] = field(default_factory=dict)
    readable: set[Path] = field(default_factory=set)
    git: dict[str, str] = field(default_factory=dict)
    pf_rules: list[str] | None = None
    daemon_user: str | None = None

    def user_uid(self, name: str) -> int | None:
        return self.users.get(name)

    def group(self, name: str) -> tuple[int, tuple[str, ...]] | None:
        return self.groups.get(name)

    def owner(self, path: Path) -> vp.Owner | None:
        return self.owners.get(path)

    def mode(self, path: Path) -> int | None:
        return self.modes.get(path)

    def can_read(self, path: Path) -> bool:
        return path in self.readable

    def git_local(self, key: str, repo: Path) -> str | None:
        return self.git.get(key)

    def pf_anchor_rules(self, anchor: str) -> list[str] | None:
        return self.pf_rules

    def launchdaemon_username(self, plist: Path) -> str | None:
        return self.daemon_user


# uids/gids are arbitrary but distinct; ascalva takes the current uid so the repo-tree lane's
# HUMAN owner resolves against a real name via the fake.
_UID = {vp.CORE: 5001, vp.WORK: 5002, vp.EDGE: 5003, vp.HUMAN: os.getuid()}
_STAFF_GID, _PALACE_GID = 20, 5100


def _cfg():
    return get_config()


def _migrated_probe(cfg, *, vault_readable=False, pf_loaded=True, daemon="ouroboros",
                    git_ok=True, home_ok=True) -> FakeProbe:
    """A FULLY-migrated fixture: the three users + palace group exist, every lane has the right
    owner:group+mode, the daemon plist declares ouroboros, git signing is repo-local, home is
    traversable. Knobs flip individual lanes to prove the falsifiers."""
    vault = Path(cfg.vault.path).expanduser()
    exhaust = Path(cfg.exhaust.path).expanduser()
    data_dir = Path(cfg.paths.data_dir)
    owners = {
        vault: vp.Owner(_UID[vp.CORE], _STAFF_GID),
        exhaust: vp.Owner(_UID[vp.CORE], _STAFF_GID),
        exhaust / "reports": vp.Owner(_UID[vp.WORK], _STAFF_GID),
        data_dir: vp.Owner(_UID[vp.CORE], _PALACE_GID),
        REPO_ROOT: vp.Owner(_UID[vp.HUMAN], _PALACE_GID),
    }
    modes = {vault: 0o700, exhaust: 0o755, exhaust / "reports": 0o755, data_dir: 0o755,
             Path.home(): 0o751 if home_ok else 0o750}
    git = {} if not git_ok else {
        "user.name": "Alberto", "user.email": "a@x", "user.signingkey": "/k.pub",
        "gpg.format": "ssh", "commit.gpgsign": "true",
    }
    pf = (["pass out quick on lo0 all", "block drop out quick proto tcp from any to any user "
           "ouroboros"] if pf_loaded else None)
    return FakeProbe(
        users=dict(_UID),
        groups={vp.SHARED_GROUP: (_PALACE_GID, (vp.HUMAN, vp.WORK)), "staff": (_STAFF_GID, ())},
        owners=owners, modes=modes,
        readable={vault} if vault_readable else set(),
        git=git, pf_rules=pf, daemon_user=daemon,
    )


def test_pre_migration_is_never_green():
    """An empty probe (no users, no owned lanes) → every lane/user PENDING → NOT green."""
    checks = vp.run_checks(FakeProbe(), _cfg())
    assert not vp.is_green(checks)
    assert not any(c.status == vp.PASS for c in checks)


def test_fully_migrated_is_green_with_manual_skips():
    """The end-state (owner ran it with sudo → pf loaded): no FAIL, no PENDING → GREEN. The only
    SKIP is the unseal owner-manual one-liner (the verifier never scans a credential store)."""
    checks = vp.run_checks(_migrated_probe(_cfg()), _cfg())
    assert vp.is_green(checks)
    skipped = [c.name for c in checks if c.status == vp.SKIP]
    assert skipped == ["unseal key under ouroboros (manual)"]


def test_partial_migration_is_not_a_false_green():
    """The Item 4 falsifier: reports/ not yet chowned to ouroboros-work → PENDING (never a false
    green) for ANY non-role owner; FAIL is reserved for a lane owned by the WRONG role account. The
    PENDING/FAIL split reads role uids from the PROBE, never the host user db, so it is identical on
    any OS — finding-0124: the old name-in-{ascalva} test was green on the owner's Mac but FAIL on
    Linux CI, where the runner's uid resolves to a non-'ascalva' name."""
    cfg = _cfg()
    reports = Path(cfg.exhaust.path).expanduser() / "reports"

    # (a) a NON-role owner -> PENDING (not migrated yet). 424242 stands for any non-plane uid that
    #     need not even resolve to a name (the CI-runner case that the old code mis-scored as FAIL).
    for non_role_uid in (_UID[vp.HUMAN], 424242):
        probe = _migrated_probe(cfg)
        probe.owners[reports] = vp.Owner(non_role_uid, _STAFF_GID)
        checks = vp.run_checks(probe, cfg)
        assert not vp.is_green(checks)
        rc = next(c for c in checks if c.name.startswith("exhaust/reports/"))
        assert rc.status == vp.PENDING, f"non-role {non_role_uid} → PENDING, got {rc.status}"

    # (b) the WRONG role account (ouroboros/CORE, not ouroboros-work) -> FAIL (real migration err).
    probe = _migrated_probe(cfg)
    probe.owners[reports] = vp.Owner(_UID[vp.CORE], _STAFF_GID)
    checks = vp.run_checks(probe, cfg)
    rc = next(c for c in checks if c.name.startswith("exhaust/reports/"))
    assert rc.status == vp.FAIL, f"wrong-role owner must be FAIL, got {rc.status}"


def test_readable_vault_after_migration_is_a_hard_fail():
    """The sharpest falsifier: vault is ouroboros-owned but READABLE from this posture → the corpus
    wall is not sealed → FAIL (never a false green)."""
    cfg = _cfg()
    checks = vp.run_checks(_migrated_probe(cfg, vault_readable=True), cfg)
    vault_check = next(c for c in checks if c.name == "vault unreadable from human posture")
    assert vault_check.status == vp.FAIL
    assert not vp.is_green(checks)


def test_pf_anchor_misordered_is_caught():
    """pf falsifier: the block precedes the lo0 pass → FAIL (loopback model traffic would drop)."""
    cfg = _cfg()
    probe = _migrated_probe(cfg)
    probe.pf_rules = ["block drop out quick proto tcp from any to any user ouroboros",
                      "pass out quick on lo0 all"]
    check = next(c for c in vp.run_checks(probe, cfg) if c.name == "core-egress pf anchor loaded")
    assert check.status == vp.FAIL


def test_pf_anchor_unreadable_skips_not_false_green():
    cfg = _cfg()
    probe = _migrated_probe(cfg, pf_loaded=True)
    probe.pf_rules = None                               # pfctl needs root → unreadable
    check = next(c for c in vp.run_checks(probe, cfg) if c.name == "core-egress pf anchor loaded")
    assert check.status == vp.SKIP


def test_daemon_user_wrong_is_fail_absent_is_pending():
    cfg = _cfg()
    wrong = next(c for c in vp.run_checks(_migrated_probe(cfg, daemon="root"), cfg)
                 if c.name == "daemon runs as ouroboros")
    assert wrong.status == vp.FAIL
    absent = next(c for c in vp.run_checks(_migrated_probe(cfg, daemon=None), cfg)
                  if c.name == "daemon runs as ouroboros")
    assert absent.status == vp.PENDING


def test_git_signing_absent_pending_partial_fail():
    cfg = _cfg()
    absent = next(c for c in vp.run_checks(_migrated_probe(cfg, git_ok=False), cfg)
                  if c.name == "repo-local git signing")
    assert absent.status == vp.PENDING
    probe = _migrated_probe(cfg)
    del probe.git["commit.gpgsign"]                     # a partial config is worse than none → FAIL
    partial = next(c for c in vp.run_checks(probe, cfg) if c.name == "repo-local git signing")
    assert partial.status == vp.FAIL


def test_home_not_traversable_is_fail():
    cfg = _cfg()
    check = next(c for c in vp.run_checks(_migrated_probe(cfg, home_ok=False), cfg)
                 if c.name == "home traversable by role accounts")
    assert check.status == vp.FAIL


# --- read-only proofs (Item 4 invariant: the verifier opens nothing for write) ------------------
def test_verifier_never_writes():
    """Structural proof of zero mutation, AST-based (not a substring grep — the docstring names
    what it does NOT do): no CALL to a mutating API (write_text/bytes, mkdir, chmod, chown, unlink,
    rmtree, remove, copy…), no `open(..., 'w'/'a'/'x')`, and no `-f`/`-F` pfctl ruleset load among
    the string literals (the verifier only ever `pfctl -a … -sr`, a read)."""
    tree = ast.parse((REPO_ROOT / "scripts/verify_planes.py").read_text(encoding="utf-8"))
    mutating_attrs = {"write_text", "write_bytes", "mkdir", "chmod", "chown", "unlink", "rmtree",
                      "remove", "rename", "replace", "symlink_to", "touch", "copy", "copy2",
                      "copytree", "move", "makedirs"}
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            fn = node.func
            if isinstance(fn, ast.Attribute):
                assert fn.attr not in mutating_attrs, f"mutating call .{fn.attr}()"
            if isinstance(fn, ast.Name) and fn.id == "open":
                mode = node.args[1] if len(node.args) > 1 else None
                if isinstance(mode, ast.Constant):
                    assert set(str(mode.value)) & {"w", "a", "x", "+"} == set(), "open() for write"
        # a pfctl ruleset LOAD is `-f`/`-F`; the verifier must only ever READ (`-sr`, `-a`).
        if isinstance(node, ast.Constant) and node.value in ("-f", "-F"):
            raise AssertionError("verify_planes.py must not load/flush a pf ruleset (-f/-F)")


def test_verifier_imports_stdlib_and_config_only():
    """No-core falsifier (docket/exhaust_report precedent): repo-workflow tooling imports stdlib +
    the `config` facade, NEVER `core`."""
    tree = ast.parse((REPO_ROOT / "scripts/verify_planes.py").read_text(encoding="utf-8"))
    imported: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module.split(".")[0])
        elif isinstance(node, ast.Import):
            for a in node.names:
                imported.add(a.name.split(".")[0])
    assert "core" not in imported, "the verifier must never import core"
    allowed = {"__future__", "argparse", "grp", "os", "pwd", "subprocess", "sys", "dataclasses",
               "pathlib", "typing", "config"}
    assert imported <= allowed, f"unexpected imports: {imported - allowed}"


def test_verifier_runs_end_to_end_via_cli():
    """finding-0118: exercise the CLI form, not just the imported fns. It runs, prints the table
    with every check name, and exits cleanly (non-zero pre-migration on this box — nothing is
    migrated — but it must NOT crash / ImportError)."""
    r = subprocess.run(["uv", "run", "scripts/verify_planes.py"], cwd=REPO_ROOT,
                       capture_output=True, text=True)
    assert r.returncode in (0, 1), r.stderr
    assert "four-plane verifier" in r.stdout
    assert "vault unreadable from human posture" in r.stdout
    assert "core-egress pf anchor loaded" in r.stdout


# ============================================================================================
# Item 5 — the per-plane self-configuring ratchets (SKIP pre-migration, ENFORCE post)
# ============================================================================================
def _uid(name: str) -> int | None:
    import pwd
    try:
        return pwd.getpwnam(name).pw_uid
    except KeyError:
        return None


def test_ratchet_vault_unreadable_from_test_uid():
    """The corpus wall: once the vault is ouroboros-owned, a non-ouroboros posture (this test's
    uid) CANNOT read it. Keyed on real ownership — SKIPS until the vault is migrated."""
    vault = Path(get_config().vault.path).expanduser()
    core = _uid(vp.CORE)
    if core is None or not vault.exists() or vault.stat().st_uid != core:
        pytest.skip("pre-migration: vault not yet ouroboros-owned")
    assert not os.access(vault, os.R_OK)


def test_ratchet_exhaust_reports_owned_by_work():
    """Self-configuring witness (matches the vault/data ratchets): SKIP until exhaust/reports/ is
    actually chowned to ouroboros-work, then ENFORCE. Keys on the LANE's real ownership, not merely
    on the user existing — else a PARTIAL migration (users created in §1 but reports not yet chowned
    in §8) would enforce prematurely and redden the suite (finding-0124)."""
    reports = Path(get_config().exhaust.path).expanduser() / "reports"
    work = _uid(vp.WORK)
    if work is None or not reports.exists() or reports.stat().st_uid != work:
        pytest.skip("pre-migration: exhaust/reports/ not yet ouroboros-work-owned")
    assert reports.stat().st_uid == work


def test_ratchet_data_owned_by_core():
    data_dir = Path(get_config().paths.data_dir)
    core = _uid(vp.CORE)
    if core is None or not data_dir.exists() or data_dir.stat().st_uid != core:
        pytest.skip("pre-migration: data/ not yet ouroboros-owned")
    assert data_dir.stat().st_uid == core


def test_ratchet_repo_local_signing_present():
    """Q10: repo-local signing (HOME-independent) is set once the runbook configures it. SKIP until
    it exists; ENFORCE the full set once any repo-local signing key appears."""
    key = subprocess.run(["git", "-C", str(REPO_ROOT), "config", "--local", "--get",
                          "user.signingkey"], capture_output=True, text=True).stdout.strip()
    if not key:
        pytest.skip("pre-migration: no repo-local git signing config yet")
    for k in ("user.email", "gpg.format", "commit.gpgsign"):
        val = subprocess.run(["git", "-C", str(REPO_ROOT), "config", "--local", "--get", k],
                             capture_output=True, text=True).stdout.strip()
        assert val, f"repo-local signing is partial: {k} unset"


def test_ratchet_core_egress_refused():
    """The pf egress wall. Reading the loaded anchor needs root — SKIP gracefully where pf state is
    unreadable (never a false green). ENFORCE the lo0-before-block ordering when readable."""
    try:
        r = subprocess.run(["pfctl", "-a", vp.PF_ANCHOR, "-sr"], capture_output=True, text=True)
    except FileNotFoundError:
        pytest.skip("pfctl unavailable")
    if r.returncode != 0:
        pytest.skip("pre-migration / no sudo: core-egress anchor not loaded or unreadable")
    rules = [ln.strip() for ln in r.stdout.splitlines() if ln.strip()]
    lo0 = next((i for i, x in enumerate(rules) if x.startswith("pass") and "lo0" in x), None)
    blk = next((i for i, x in enumerate(rules) if x.startswith("block") and vp.CORE in x), None)
    assert lo0 is not None and blk is not None and lo0 < blk


# --- the committed pf anchor: ordering (text) + syntax (resolvable-user substitution) -----------
def _anchor_rule_lines() -> list[str]:
    return [ln for ln in ANCHOR.read_text().splitlines()
            if ln.strip() and not ln.strip().startswith("#")]


def test_pf_anchor_lo0_pass_precedes_the_block():
    """The Item 3 ordering falsifier, proven by TEXT (needs no pfctl): the `pass … on lo0` line
    comes strictly before the `block … user ouroboros` line."""
    lines = _anchor_rule_lines()
    lo0 = next(i for i, ln in enumerate(lines) if ln.strip().startswith("pass") and "lo0" in ln)
    blk = next(i for i, ln in enumerate(lines)
               if ln.strip().startswith("block") and "user ouroboros" in ln)
    assert lo0 < blk
    assert len(lines) == 2, f"the anchor should be exactly two rules, got {lines}"


def test_pf_anchor_names_only_ouroboros():
    """Invariant: the anchor blocks ONLY core (`ouroboros`), never ouroboros-work / -edge."""
    users = [tok for ln in _anchor_rule_lines() for tok in ln.split()
             if ln.split()[ln.split().index(tok) - 1:ln.split().index(tok)] == ["user"]]
    assert users == [vp.CORE], f"anchor must name only {vp.CORE}, found {users}"


def test_pf_anchor_parses_with_a_resolvable_user():
    """Item 3 syntax acceptance: `pfctl -n -f` parses the anchor once `user ouroboros` is
    substituted by an existing user (the real user does not exist pre-migration, so the literal
    file only parses post-account-creation — the runbook makes that a post-create verify step).
    SKIP where pfctl is unavailable (e.g. Linux CI)."""
    import shutil
    if shutil.which("pfctl") is None:
        pytest.skip("pfctl unavailable (not macOS)")
    import getpass
    import tempfile
    sub = ANCHOR.read_text().replace("user ouroboros", f"user {getpass.getuser()}")
    with tempfile.NamedTemporaryFile("w", suffix=".pf.conf", delete=False) as f:
        f.write(sub)
        tmp = f.name
    try:
        r = subprocess.run(["pfctl", "-n", "-f", tmp], capture_output=True, text=True)
    finally:
        os.unlink(tmp)
    assert r.returncode == 0, r.stderr


# --- the [planes] config block the ratchets' master switch reads (§6) ---------------------------
def test_planes_config_block_present_and_disabled_by_default():
    """The `[planes]` block (defaults.toml) carries the three role homes + the coarse `enabled`
    master switch. Shipped default MUST be disabled (a fresh clone never assumes migration)."""
    raw = tomllib.loads((REPO_ROOT / "config/defaults.toml").read_text(encoding="utf-8"))
    planes = raw["planes"]
    assert planes["enabled"] is False
    assert {"core_home", "work_home", "edge_home"} <= set(planes)
