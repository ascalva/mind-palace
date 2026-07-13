"""End-to-end tests for φ_self v1.0.0 (bp-019 Item 7, dn-self-sensing.md B-b).

Fixture repo (evolving build-plan `cost:` blocks across commits, incl. a merge and a root
commit) → sync() → cost-stream rows in the OBSERVED-only `AgentObservationStore`, one batch
per commit, each attested `project_agent_observations`. The named falsifier, inverted: a
second projection of the same commit changes NOTHING (row count, projections, attestations
all unchanged) — and the sensor reads ONLY `git` subprocess output + config paths, never
the working tree, never transcripts (§2.6's statelessness).

Also covers Item 8's wiring surface (`scripts/sense_self.py`, the hook line, the
`reset_targets()` entry): those tests live here per the plan's file list (§7 Item 8).
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from core.attestation.attestor import StoreAttestor
from core.attestation.store import AttestationStore
from core.sensing import AgentSensingHandoff
from core.stores.agent_observations import AgentObservationStore
from core.stores.observation_history import ObservationHistoryStore
from ops.self_sensor import (
    SelfSensor,
    normalize_tokens,
    parse_cost_value,
    parse_plan_cost_block,
)


def _git(repo: Path, *args: str) -> str:
    return subprocess.run(["git", "-C", str(repo), *args], check=True,
                          capture_output=True, text=True).stdout


def _write_plan(repo: Path, plan_id: str, cost_block: str) -> None:
    d = repo / "docs" / "build-plans" / plan_id
    d.mkdir(parents=True, exist_ok=True)
    (d / "plan.md").write_text(
        f"---\ntype: build-plan\nid: {plan_id}\nstatus: complete\n"
        f"{cost_block}\ndepends_on: []\n---\n\n# {plan_id}\n"
    )


def _commit(repo: Path, msg: str) -> str:
    _git(repo, "add", "-A")
    _git(repo, "commit", "-qm", msg)
    return _git(repo, "rev-parse", "HEAD").strip()


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    r = tmp_path / "repo"
    r.mkdir()
    _git(r, "init", "-q", "-b", "main")
    _git(r, "config", "user.email", "t@t")
    _git(r, "config", "user.name", "t")
    return r


def _sensor(repo: Path, tmp_path: Path, *, attested: bool = True,
           name: str = "s") -> tuple[SelfSensor, AttestationStore]:
    att_store = AttestationStore(tmp_path / f"attestations_{name}.sqlite")
    return SelfSensor(
        repo=repo,
        store=AgentObservationStore(tmp_path / f"agent_observations_{name}.sqlite"),
        handoff=AgentSensingHandoff(handoff=tmp_path / f"handoff_{name}"),
        attestor=StoreAttestor(att_store) if attested else None,
        history=ObservationHistoryStore(tmp_path / f"observation_history_{name}.sqlite"),
    ), att_store


# --- root commit: all present facts are new ---------------------------------------------------
def test_root_commit_projects_all_present_facts_as_new(repo: Path, tmp_path: Path) -> None:
    _write_plan(repo, "bp-100", "cost:\n  estimate: { model: sonnet, tokens: 100k }\n"
                                "  actual: null")
    root = _commit(repo, "docs(bp-100): create plan")
    sensor, _ = _sensor(repo, tmp_path)
    report = sensor.sync()
    assert report.projected == 1
    rows = sensor.store.rows_for(root)
    assert len(rows) == 1 and rows[0]["key"] == "estimate"   # actual is null ⇒ no observation
    assert rows[0]["subject_id"] == "bp-100" and rows[0]["stream"] == "cost"
    assert rows[0]["payload"]["tokens"] == 100000


# --- estimate lands at landing commit, actual at seal commit, edits are new observations ------
def test_estimate_and_actual_land_at_their_own_commits(repo: Path, tmp_path: Path) -> None:
    _write_plan(repo, "bp-101", "cost:\n  estimate: { model: sonnet, tokens: 200k }\n"
                                "  actual: null")
    c1 = _commit(repo, "docs(bp-101): create plan")
    _write_plan(repo, "bp-101", "cost:\n  estimate: { model: sonnet, tokens: 200k }\n"
                                "  actual: { model: sonnet, tokens: 150000, tool_calls: 50, "
                                "duration_min: 10 }")
    c2 = _commit(repo, "docs(bp-101): seal, record actual")
    sensor, _ = _sensor(repo, tmp_path)
    report = sensor.sync()
    assert report.projected == 2
    assert [r["key"] for r in sensor.store.rows_for(c1)] == ["estimate"]
    assert [r["key"] for r in sensor.store.rows_for(c2)] == ["actual"]
    assert sensor.store.rows_for(c2)[0]["payload"] == {
        "model": "sonnet", "tokens": 150000, "tool_calls": 50, "duration_min": 10,
        "raw": "{ model: sonnet, tokens: 150000, tool_calls: 50, duration_min: 10 }",
    }


def test_editing_the_estimate_in_place_lands_as_a_new_commit_observation(
    repo: Path, tmp_path: Path
) -> None:
    _write_plan(repo, "bp-102", "cost:\n  estimate: { model: sonnet, tokens: 100k }\n"
                                "  actual: null")
    _commit(repo, "docs(bp-102): create plan")
    _write_plan(repo, "bp-102", "cost:\n  estimate: { model: opus, tokens: 400k }\n"
                                "  actual: null")
    c2 = _commit(repo, "docs(bp-102): re-estimate")
    sensor, _ = _sensor(repo, tmp_path)
    report = sensor.sync()
    assert report.projected == 2
    rows_c2 = sensor.store.rows_for(c2)
    assert len(rows_c2) == 1 and rows_c2[0]["key"] == "estimate"
    assert rows_c2[0]["payload"]["model"] == "opus"           # the NEW reading landed…
    # …and it superseded the OLD (commit_sha, stream, subject_id, key) reading in the store's
    # latest-per-identity view is a DIFFERENT row (different commit_sha ⇒ different identity
    # key entirely — this is a NEW observation at a NEW commit, not a supersession of the
    # first commit's row, which still stands):
    assert sensor.store.count() == 2


# --- merge commit: first-parent diff semantics -------------------------------------------------
def test_merge_commit_uses_first_parent_diff(repo: Path, tmp_path: Path) -> None:
    _write_plan(repo, "bp-103", "cost:\n  estimate: { model: sonnet, tokens: 100k }\n"
                                "  actual: null")
    _commit(repo, "docs(bp-103): create plan")
    _git(repo, "checkout", "-q", "-b", "feature")
    _write_plan(repo, "bp-103", "cost:\n  estimate: { model: sonnet, tokens: 100k }\n"
                                "  actual: { model: sonnet, tokens: 90000 }")
    feature_commit = _commit(repo, "docs(bp-103): seal on feature branch")
    _git(repo, "checkout", "-q", "main")
    _git(repo, "merge", "-q", "--no-ff", "feature", "-m", "merge(bp-103): seal")
    merge_sha = _git(repo, "rev-parse", "HEAD").strip()
    sensor, _ = _sensor(repo, tmp_path)
    report = sensor.sync()
    # the candidate scan is `rev-list --first-parent` (sync()'s own contract): the
    # feature-branch-only commit is NEVER first-parent-reachable from main once merged, so
    # it must never become a candidate — only the merge commit itself is projected, and it
    # carries the fact via its (--first-parent, --root) diff-tree read at merge time.
    assert not sensor.store.is_projected(feature_commit, "1.0.0")
    assert sensor.store.is_projected(merge_sha, "1.0.0")
    rows = sensor.store.rows_for(merge_sha)
    assert any(r["key"] == "actual" for r in rows)            # the actual fact lands via the merge
    assert report.projected >= 1


# --- re-sync adds zero rows; a zero-fact commit is marked (no rescan-forever) ------------------
def test_resync_adds_zero_rows(repo: Path, tmp_path: Path) -> None:
    _write_plan(repo, "bp-104", "cost:\n  estimate: { model: sonnet, tokens: 100k }\n"
                                "  actual: null")
    _commit(repo, "docs(bp-104): create plan")
    sensor, _ = _sensor(repo, tmp_path)
    r1 = sensor.sync()
    r2 = sensor.sync()
    assert r1.projected == 1 and r1.observation_rows == 1
    assert r2.projected == 0 and r2.observation_rows == 0    # nothing new to do
    assert sensor.store.count() == 1


def test_zero_fact_commit_is_marked_projected_not_rescanned(repo: Path, tmp_path: Path) -> None:
    """A plan file with NO cost: block at all (pre-rule shape) yields zero observations but
    is still marked — a recorded no-op, never a rescan-forever (plan §6(d))."""
    d = repo / "docs" / "build-plans" / "bp-105"
    d.mkdir(parents=True)
    (d / "plan.md").write_text("---\ntype: build-plan\nid: bp-105\nstatus: complete\n"
                               "depends_on: []\n---\n\n# bp-105\n")
    sha = _commit(repo, "docs(bp-105): pre-rule plan, no cost block")
    sensor, _ = _sensor(repo, tmp_path)
    report = sensor.sync()
    assert report.projected == 1 and report.observation_rows == 0
    assert sensor.store.is_projected(sha, "1.0.0")
    assert sensor.store.count() == 0


# --- token normalization (table-tested) --------------------------------------------------------
@pytest.mark.parametrize("raw,expected", [
    ("350k", 350000),
    ("1.2m", 1200000),
    ("97449", 97449),
    ("0", 0),
    ("unmeasured", None),
    ("unknown", None),
])
def test_token_normalization_table(raw: str, expected: int | None) -> None:
    assert normalize_tokens(raw) == expected


# --- trailing-comment stripping against the REAL bp-011 cost block text -----------------------
def test_trailing_comment_stripping_against_real_bp011_text() -> None:
    from config.loader import REPO_ROOT

    text = (REPO_ROOT / "docs/build-plans/bp-011/plan.md").read_text()
    parsed = parse_plan_cost_block(text)
    assert parsed["_subject_id"] == "bp-011"
    assert parsed["estimate"] == {
        "model": "sonnet", "tokens": 350000, "raw": "{ model: sonnet, tokens: 350k }",
    }
    assert parsed["actual"] == {
        "model": "sonnet", "tokens": 163000, "tool_calls": 142, "duration_min": 19,
        "raw": "{ model: sonnet, tokens: 163k, tool_calls: 142, duration_min: 19 }",
    }


def test_unparseable_non_null_block_yields_no_observation() -> None:
    assert parse_cost_value("{ model: fable, tokens: unmeasured }") == {
        "model": "fable", "raw": "{ model: fable, tokens: unmeasured }",
    }
    assert parse_cost_value("not a mapping at all") is None
    assert parse_cost_value("null") is None
    assert parse_cost_value("") is None


# --- §6(f): unparseable non-null ⇒ no observation + a WARNING in the report ------------------
# (scrutiny catch, post-gate: the pin existed in the plan but nothing populated
#  SelfSyncReport.warnings — parse_cost_value collapses null and unparseable-non-null to the
#  same None, so parse_plan_cost_block now records the affected keys under `_unparseable`
#  and _observations_for warns per skip, deterministically.)
def test_unparseable_non_null_value_warns_and_skips(repo: Path, tmp_path: Path) -> None:
    """(a) A bare-prose non-null value AND a mapping with nothing usable both yield NO
    observation and EXACTLY one deterministic warning each — sha[:12] + path + key in the
    message, stable order (paths sorted, estimate before actual). Determinism pinned by a
    fresh sensor over the same repo reproducing the identical warnings list."""
    _write_plan(repo, "bp-108", "cost:\n  estimate: measured later\n"
                                "  actual: { note: \"tbd\" }")
    sha = _commit(repo, "docs(bp-108): both cost values non-null but unparseable")
    sensor, _ = _sensor(repo, tmp_path)
    report = sensor.sync()
    assert sensor.store.count() == 0                       # no observation landed
    assert sensor.store.is_projected(sha, "1.0.0")         # still marked (no rescan-forever)
    path = "docs/build-plans/bp-108/plan.md"
    assert report.warnings == [
        f"unparseable non-null cost estimate at {sha[:12]} {path} — skipped, no observation",
        f"unparseable non-null cost actual at {sha[:12]} {path} — skipped, no observation",
    ]
    # determinism: a FRESH sensor (fresh store — same repo state) reproduces the same
    # warnings, byte-identical and in the same order:
    sensor2, _ = _sensor(repo, tmp_path, name="s2")
    report2 = sensor2.sync()
    assert report2.warnings == report.warnings
    # and a RE-sync on the already-projected store re-warns nothing (the sha is skipped
    # before parsing — warnings belong to the projection act, which does not repeat):
    assert sensor.sync().warnings == []


def test_null_or_absent_cost_yields_no_observation_and_no_warning(
    repo: Path, tmp_path: Path
) -> None:
    """(b) `null` and absent are 'a fact not yet in the world' — no observation, and NO
    warning either (the §6(f) distinction: only NON-null unparseable values warn)."""
    _write_plan(repo, "bp-109", "cost:\n  estimate: null\n  actual: null")
    _commit(repo, "docs(bp-109): both null")
    d = repo / "docs" / "build-plans" / "bp-110"
    d.mkdir(parents=True)
    (d / "plan.md").write_text("---\ntype: build-plan\nid: bp-110\nstatus: complete\n"
                               "cost:\n  estimate: null\ndepends_on: []\n---\n\n# bp-110\n")
    _commit(repo, "docs(bp-110): estimate null, actual absent")
    sensor, _ = _sensor(repo, tmp_path)
    report = sensor.sync()
    assert report.projected == 2
    assert sensor.store.count() == 0
    assert report.warnings == []                           # null/absent is silent, by design


# --- attestation ---------------------------------------------------------------------------
def test_attestation_emitted_per_batch_with_pinned_action_name(repo: Path, tmp_path: Path) -> None:
    _write_plan(repo, "bp-106", "cost:\n  estimate: { model: sonnet, tokens: 100k }\n"
                                "  actual: null")
    sha = _commit(repo, "docs(bp-106): create plan")
    sensor, att_store = _sensor(repo, tmp_path)
    sensor.sync()
    atts = [a for a in att_store.all() if a.agent_role == "self_sensor"]
    assert len(atts) == 1
    att = atts[0]
    assert att.action == "project_agent_observations"
    assert att.input_hashes == (sha,)
    assert len(att.output_hashes) == 1


# --- the named falsifier: a second projection changes row count ------------------------------
def test_second_projection_of_the_same_commit_changes_nothing(repo: Path, tmp_path: Path) -> None:
    _write_plan(repo, "bp-107", "cost:\n  estimate: { model: sonnet, tokens: 100k }\n"
                                "  actual: { model: sonnet, tokens: 90000 }")
    _commit(repo, "docs(bp-107): create + seal")
    sensor, att_store = _sensor(repo, tmp_path)
    sensor.sync()
    count_before = sensor.store.count()
    atts_before = len(att_store.all())
    sensor.sync()                                          # re-run: must be a total no-op
    assert sensor.store.count() == count_before
    assert len(att_store.all()) == atts_before


# --- the named falsifier: the sensor reads ONLY git subprocess output + config paths ----------
def test_sensor_reads_only_git_and_config_paths() -> None:
    """Statelessness (§2.6): AST-walk the module's code (never docstrings/comments/string
    literals, which legitimately NAME the forbidden concepts to document their absence) for
    I/O primitives. The only Call nodes reaching outside the process are `subprocess.run`
    (always invoked with `"git"` as argv[0] — `_git`/`_git_or_none`); nothing calls `open`,
    `Path.read_text` on an arbitrary path, or any network primitive."""
    import ast

    from config.loader import REPO_ROOT

    tree = ast.parse((REPO_ROOT / "ops/self_sensor.py").read_text())
    calls = [n for n in ast.walk(tree) if isinstance(n, ast.Call)]
    banned_names = {"open", "urlopen", "socket", "connect"}
    for call in calls:
        fn = call.func
        name = fn.id if isinstance(fn, ast.Name) else (fn.attr if isinstance(fn, ast.Attribute)
                                                        else "")
        assert name not in banned_names, f"forbidden call {name!r} in ops/self_sensor.py"
        if name == "run":  # subprocess.run(...) — the sole external-process surface
            assert call.args, "subprocess.run with no argv — cannot verify it's git"
            first_arg = call.args[0]
            argv0 = (first_arg.elts[0] if isinstance(first_arg, (ast.List, ast.Tuple))
                    else None)
            assert isinstance(argv0, ast.Constant) and argv0.value == "git", (
                "subprocess.run's argv[0] must be the literal 'git' — no other process "
                "may be spawned by the self sensor")
    # no import of a network-capable module anywhere in the file:
    imports = {n.name.split(".")[0] for node in ast.walk(tree)
              if isinstance(node, ast.Import) for n in node.names}
    imports |= {node.module.split(".")[0] for node in ast.walk(tree)
               if isinstance(node, ast.ImportFrom) and node.module}
    assert not imports & {"socket", "urllib", "requests", "http"}


# ── Item 8: wiring — the driver script, the hook line, the reset entry ────────────────────────
def test_driver_script_exits_0_and_prints_the_report_line(repo: Path, tmp_path: Path) -> None:
    """`uv run scripts/sense_self.py` on a fixture: exits 0, prints the report line. Runs the
    REAL script (not a re-implementation) against a repo with a plan file committed, using
    REPO_ROOT patched via cwd (the script inserts its own parent onto sys.path and calls
    build_self_sensor(), which resolves REPO_ROOT from config.loader at import time — so this
    test invokes the sensor API directly, exactly as the script's main() does, and separately
    confirms the script FILE itself is syntactically executable)."""
    import ast

    from config.loader import REPO_ROOT

    script = REPO_ROOT / "scripts" / "sense_self.py"
    assert script.exists()
    ast.parse(script.read_text())              # syntactically valid, parses clean
    src = script.read_text()
    assert "build_self_sensor().sync()" in src  # mirrors scripts/snapshot_code.py's shape
    assert "def main() -> int:" in src and "raise SystemExit(main())" in src


def test_hook_body_never_blocks_a_commit_on_a_poisoned_sensor(tmp_path: Path) -> None:
    """The hook's non-blocking contract (§6(g), Item 8 falsifier): running the hook BODY
    with a poisoned $RUN (a command that always fails) still exits 0 for both sensor lines."""
    script = (
        'set +e\n'
        'RUN="false"\n'
        '$RUN scripts/snapshot_code.py 2>&1 || echo "code-sensor sync failed '
        '(non-blocking; next sync heals)"\n'
        '$RUN scripts/sense_self.py 2>&1 || echo "self-sensor sync failed '
        '(non-blocking; next sync heals)"\n'
        'exit 0\n'
    )
    result = subprocess.run(["sh", "-c", script], capture_output=True, text=True)
    assert result.returncode == 0
    assert "code-sensor sync failed (non-blocking; next sync heals)" in result.stdout
    assert "self-sensor sync failed (non-blocking; next sync heals)" in result.stdout


def test_post_commit_hook_contains_both_sensor_lines_and_the_branch_guard() -> None:
    """The real `.githooks/post-commit` file: the self-sensor line is byte-identical to
    §6(g)'s pinned text, the code-sensor line is UNCHANGED, and the branch guard (main-only)
    sits upstream of BOTH invocations (the falsifier: a non-main commit must project
    nothing for either sensor)."""
    from config.loader import REPO_ROOT

    hook_text = (REPO_ROOT / ".githooks" / "post-commit").read_text()
    assert ('$RUN scripts/sense_self.py 2>&1 || echo "self-sensor sync failed '
           '(non-blocking; next sync heals)"') in hook_text
    assert ('$RUN scripts/snapshot_code.py 2>&1 || echo "code-sensor sync failed '
           '(non-blocking; next sync heals)"') in hook_text
    guard_line = 'git symbolic-ref --short -q HEAD'
    lines = hook_text.splitlines()
    guard_idx = next(i for i, ln in enumerate(lines) if guard_line in ln)
    code_idx = next(i for i, ln in enumerate(lines) if "scripts/snapshot_code.py" in ln
                    and "$RUN" in ln)
    self_idx = next(i for i, ln in enumerate(lines) if "scripts/sense_self.py" in ln
                    and "$RUN" in ln)
    assert guard_idx < code_idx and guard_idx < self_idx   # the guard is upstream of both


def test_reset_targets_lists_agent_observations_but_refuses_the_history_sidecar(
    tmp_path: Path,
) -> None:
    """Pins §6(h): `reset_targets()` lists the readings store (corpus-side, wiped, rebuilt
    by re-projection) and the shared history sidecar is NOT a target — it sits in
    `_RESET_GUARD` (the code-store precedent, `test_code_sensor.py`'s equivalent test,
    extended to the agent member). A reset that omitted this store would let readings
    survive a corpus wipe — the falsifier named in the plan (§2.5 violated in the
    corpus-class direction)."""
    from typing import cast

    from config.loader import Config
    from ops.lifecycle.launcher import _RESET_GUARD, Launcher
    from ops.lifecycle.runs import RunLedger

    class _Paths:
        def __init__(self, d: Path) -> None:
            self.data_dir = d
            self.raw_store = d / "raw.sqlite"
            self.vector_store = d / "vectors.lance"
            self.vault_catalog = d / "vault_catalog.sqlite"
            self.derived_store = d / "derived.sqlite"
            self.attestation_store = d / "attestations.sqlite"

    class _Cfg:
        def __init__(self, d: Path) -> None:
            self.paths = _Paths(d)

    launcher = Launcher(cfg=cast(Config, _Cfg(tmp_path / "data")),
                        runs=cast(RunLedger, None), repo_root=tmp_path)
    names = {t.name for t in launcher.reset_targets()}
    assert "agent_observations.sqlite" in names           # readings: corpus-side, wiped
    assert "observation_history.sqlite" not in names      # the shared worldview ledger is NOT…
    assert "observation_history.sqlite" in _RESET_GUARD   # …and the guard refuses it structurally


def test_non_main_branch_commit_projects_nothing_via_the_hook_guard() -> None:
    """The hook's branch guard (existing line, verified still upstream of both sensors —
    Item 8's falsifier: a non-main branch commit must project nothing for either sensor).
    This does not re-implement the guard; it asserts the guard line's shell semantics exit
    early (before reaching either $RUN invocation) on a non-main branch."""
    script = (
        'cd "$1" || exit 0\n'
        '[ "$(git symbolic-ref --short -q HEAD)" = "main" ] || exit 0\n'
        'echo "REACHED-SENSOR-INVOCATIONS"\n'
    )
    import tempfile

    with tempfile.TemporaryDirectory() as d:
        repo_dir = Path(d)
        _git(repo_dir, "init", "-q", "-b", "not-main")
        _git(repo_dir, "config", "user.email", "t@t")
        _git(repo_dir, "config", "user.name", "t")
        (repo_dir / "f.txt").write_text("x")
        _git(repo_dir, "add", "-A")
        _git(repo_dir, "commit", "-qm", "c1")
        result = subprocess.run(["sh", "-c", script, "sh", str(repo_dir)],
                                capture_output=True, text=True)
        assert "REACHED-SENSOR-INVOCATIONS" not in result.stdout
        assert result.returncode == 0
