"""The self sensor — φ_self, a deterministic, stateless projector over the agent's OWN
operation as recorded in build-plan `cost:` frontmatter (dn-self-sensing.md B-b, bp-019).

The third stream through the sensing seam (after the biometric stream and the code stream,
bp-012): where the code sensor reads the repo's TREE (symbols, docstrings), φ_self reads the
repo's WORKFLOW ARTIFACTS (`docs/build-plans/*/plan.md` frontmatter) — same instrument (the
repo, via `git show sha:path`), same discipline (committed state only, never the working
tree), same seam family (`AgentSensingHandoff`, `core/sensing.py`), same store shape
(`AgentObservationStore`, versioned from birth per bp-018's mechanics).

Stateless by construction (§2.6, dn-self-sensing): φ_self reads the COST stream ONLY — no
transcript content, no prompt text, nothing that could carry vault material into the
observed stratum. It "reads deterministically, projection-maps, and forgets": every fact is
re-derivable by re-running `sync()` against the same commit range, so there is no private
state anywhere in this module beyond the store's own bookkeeping.

Sensor framing (bp-011/bp-012 precedent): the repo is the instrument, the commit stream
carrying `cost:` block edits is the sensed data, `project_agent_cost_observations` is the
interpreter action, `AgentObservationStore` is the normalized record. `sync()` reconciles
`rev-list --reverse main -- docs/build-plans/*/plan.md` against `is_projected(sha,
INTERPRETER_VERSION)`, oldest first, idempotent — a missed post-commit hook heals on the
next invocation. FULL-history reconcile by construction (plan PD-d): the first LIVE run over
real history is deliberately deferred to bp-020, never run here or by the hook (the hook
line just calls `sync()`, which — on a fresh store — WOULD backfill everything; that is the
intended behavior once wired, not a special-cased "backfill mode").
"""

from __future__ import annotations

import re
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from config.loader import Config
from core.attestation import Attestor
from core.sensing import AgentSensingHandoff
from core.stores.agent_observations import AgentObservation, AgentObservationStore
from core.stores.observation_history import ObservationHistoryStore

INTERPRETER_VERSION = "1.0.0"   # phi_self's worldview coordinate; ratchet-pinned
# Bump ⇒ re-projection supersedes; an unbumped source change is a RED ratchet test
# (tests/unit/test_interpreter_versions.py), never silent (bp-018's §6(a) pattern).

_PLAN_GLOB = "docs/build-plans/*/plan.md"


class GitCommandError(RuntimeError):
    """A `git` invocation used by φ_self failed for a reason other than 'absent at this
    ref' (which is handled by returning None from `_read_plan_at`, never by raising)."""


def _git(repo: Path, *args: str) -> str:
    """The sensor's ONLY read surface: `git` subprocess output over committed state. Never
    the working tree — every read pins an explicit ref (§2.6's statelessness contract,
    mechanically pinned by the falsifier test)."""
    return subprocess.run(["git", "-C", str(repo), *args], check=True,
                          capture_output=True, text=True).stdout


def _git_or_none(repo: Path, *args: str) -> str | None:
    """Like `_git`, but a non-zero exit (e.g. `show sha:path` where `path` does not exist at
    `sha` — a root commit's `sha^`, or a plan file added later) is 'absent', not an error."""
    proc = subprocess.run(["git", "-C", str(repo), *args],
                          capture_output=True, text=True)
    if proc.returncode != 0:
        return None
    return proc.stdout


# ── The cost: block parser (§6(f)) — stdlib-only, line-based over the frontmatter ──────────
# Matches an unindented `key:` starting a new top-level frontmatter field (ends the cost:
# block scan) — the same "no leading space ⇒ new key" rule `_lib.py:parse_front_matter` uses.
_TOP_KEY = re.compile(r"^[A-Za-z_][\w-]*:")
_FIELD_LINE = re.compile(r"^\s*(estimate|actual):\s*(.*)$")
_TOKENS_RE = re.compile(r"^(\d+(?:\.\d+)?)([km])$", re.IGNORECASE)


def _strip_trailing_comment(line: str) -> str:
    """Strip a trailing `# comment` BEFORE parsing the value (the bp-014 `_scalar()`/
    `_normalize_status()` wrinkle, Q4): cut at the first ' #' (space-hash — YAML comment
    semantics) that is NOT inside a quoted string, so a `note: "... # not a comment ..."`
    survives. A '#' with no preceding space is left intact (not a YAML comment)."""
    in_quote: str | None = None
    i = 0
    while i < len(line):
        ch = line[i]
        if in_quote:
            if ch == in_quote:
                in_quote = None
        elif ch in "\"'":
            in_quote = ch
        elif ch == "#" and i > 0 and line[i - 1] == " ":
            return line[: i - 1].rstrip()
        i += 1
    return line.rstrip()


def _split_top_level_commas(inner: str) -> list[str]:
    """Split a flow-mapping's inner text on commas NOT inside a quoted string — a bare
    `str.split(",")` would break a `note: "a, b"` value."""
    parts: list[str] = []
    buf: list[str] = []
    in_quote: str | None = None
    for ch in inner:
        if in_quote:
            buf.append(ch)
            if ch == in_quote:
                in_quote = None
            continue
        if ch in "\"'":
            in_quote = ch
            buf.append(ch)
        elif ch == ",":
            parts.append("".join(buf))
            buf = []
        else:
            buf.append(ch)
    if buf:
        parts.append("".join(buf))
    return parts


def normalize_tokens(raw: str) -> int | None:
    """`'350k'` → 350000, `'1.2m'` → 1200000, a bare int string passes through, anything
    else (e.g. `'unmeasured'`, `'unknown'`) is unparseable → None (plan §6(f))."""
    raw = raw.strip()
    m = _TOKENS_RE.match(raw)
    if m:
        n = float(m.group(1))
        mult = 1000 if m.group(2).lower() == "k" else 1_000_000
        return int(n * mult)
    if raw.isdigit():
        return int(raw)
    return None


def parse_cost_value(raw: str) -> dict[str, Any] | None:
    """Parse one `estimate:`/`actual:` value (§6(f)). `null` (or empty) ⇒ None (no
    observation — a fact not yet in the world). A non-null value that is not a `{ ... }`
    flow mapping, or one with no usable `model`/`tokens` inside, ⇒ None too (an unparseable
    non-null block yields no observation + a caller-side WARNING — deterministic skip).
    A well-formed block returns the v1 worldview payload: normalized `tokens` (int) +
    `model` (lowercased) if present, optional `tool_calls`/`duration_min`, and `raw` — the
    source text verbatim (trailing comment already stripped by the caller)."""
    raw = raw.strip()
    if raw == "" or raw == "null":
        return None
    if not (raw.startswith("{") and raw.endswith("}")):
        return None
    inner = raw[1:-1].strip()
    fields: dict[str, str] = {}
    for part in _split_top_level_commas(inner):
        if ":" not in part:
            continue
        k, _, v = part.partition(":")
        fields[k.strip()] = v.strip().strip("\"'")
    payload: dict[str, Any] = {}
    if "model" in fields:
        payload["model"] = fields["model"].lower()
    if "tokens" in fields:
        tokens = normalize_tokens(fields["tokens"])
        if tokens is not None:
            payload["tokens"] = tokens
    if "tool_calls" in fields and fields["tool_calls"].isdigit():
        payload["tool_calls"] = int(fields["tool_calls"])
    if "duration_min" in fields and fields["duration_min"].isdigit():
        payload["duration_min"] = int(fields["duration_min"])
    if "model" not in payload and "tokens" not in payload:
        return None   # nothing usable landed — an unparseable non-null block
    payload["raw"] = raw
    return payload


def parse_plan_cost_block(text: str) -> dict[str, Any]:
    """Extract `{'estimate': {...}|None, 'actual': {...}|None}` from one plan file's FULL
    text (frontmatter + body — the scan only looks inside `cost:`, so body content never
    interferes). Returns {} if there is no `cost:` field at all (pre-rule plans, V4's 11
    no-cost-block cases). `id:` is returned too (the `subject_id`, plan §6(e), under
    `_subject_id`), and `_unparseable` carries the tuple of keys whose value was NON-NULL
    but yielded nothing usable — the §6(f) distinction `parse_cost_value`'s None return
    collapses (null and unparseable both map to None there; only HERE, with the raw text
    still in hand, can the two be told apart). The caller warns per `_unparseable` key."""
    lines = text.splitlines()
    out: dict[str, Any] = {}
    unparseable: list[str] = []
    plan_id = ""
    in_cost = False
    for ln in lines:
        if not in_cost:
            m = re.match(r"^id:\s*(.*)$", ln)
            if m:
                plan_id = _strip_trailing_comment(m.group(1)).strip()
            if re.match(r"^cost:\s*$", ln):
                in_cost = True
            continue
        if _TOP_KEY.match(ln):        # a new unindented top-level key ends the cost: block
            break
        fm = _FIELD_LINE.match(_strip_trailing_comment(ln))
        if fm:
            key, raw_value = fm.group(1), fm.group(2).strip()
            parsed = parse_cost_value(raw_value)
            out[key] = parsed
            if parsed is None and raw_value not in ("", "null"):
                unparseable.append(key)   # §6(f): non-null but nothing usable — warn upstream
    if unparseable:
        out["_unparseable"] = tuple(unparseable)
    if plan_id:
        out["_subject_id"] = plan_id
    return out


def _read_plan_at(repo: Path, sha: str, path: str) -> dict[str, Any] | None:
    """`git show sha:path` (never the working tree) → parsed cost block, or None if the
    path does not exist at `sha` (a root commit's parent read, or a plan added later)."""
    text = _git_or_none(repo, "show", f"{sha}:{path}")
    if text is None:
        return None
    return parse_plan_cost_block(text)


@dataclass
class SelfSyncReport:
    projected: int = 0             # commits whose observation batch landed this sync
    observation_rows: int = 0      # NEW observed-stratum rows this sync (0 on a re-run)
    warnings: list[str] = field(default_factory=list)

    def __str__(self) -> str:
        return (f"self-sensor sync: projected={self.projected} "
                f"observation_rows={self.observation_rows} warnings={len(self.warnings)}")


@dataclass
class SelfSensor:
    """Tools are the wiring; the agent is the discipline over them (the code-sensor shape,
    verbatim). Holds git-read (read-only), the OBSERVED-only store, the sensing-seam
    handoff, the attestor, and the shared history sidecar — nothing else: no model, no
    embedder, no transcript access (§2.6)."""

    repo: Path
    store: AgentObservationStore
    handoff: AgentSensingHandoff
    attestor: Attestor | None = None
    history: ObservationHistoryStore | None = None
    branch: str = "main"

    def sync(self) -> SelfSyncReport:
        """Reconcile the observed stratum against every commit that touched a build-plan's
        `cost:` block, oldest first — FULL-history reconcile by construction (plan PD-d):
        the candidate scan is `rev-list --first-parent --reverse <branch> --
        docs/build-plans/*/plan.md`, every FIRST-PARENT ancestor of `branch`, not a
        forward-only-since-wiring scan. `--first-parent` here (not just on the per-commit
        diff-tree call) is required by the plan's own risk analysis (§3): plans land on
        main via merge commits from builder worktrees, and a BARE `rev-list` would include
        the branch-side commit itself as a candidate too (verified empirically — it is
        reachable from main and touches the pathspec), which is exactly the double-candidacy
        the design rules out ("branch-side duplicates are never candidates"). Idempotent per
        (sha, INTERPRETER_VERSION) via `is_projected`."""
        report = SelfSyncReport()
        shas = _git(self.repo, "rev-list", "--first-parent", "--reverse", self.branch,
                   "--", _PLAN_GLOB).splitlines()
        for sha in shas:
            if self.store.is_projected(sha, INTERPRETER_VERSION):
                continue
            rows = self._project(sha, report)
            report.observation_rows += rows
            report.projected += 1
        return report

    def _changed_plan_files(self, sha: str) -> list[str]:
        """First-parent diff (plan §6(e), Q3): merge commits land on main from builder
        worktrees, so first-parent semantics are required — branch-side duplicate commits
        are never candidates (they never appear in `rev-list main`'s first-parent-reachable
        history the way `--first-parent` walks it for THIS call). `--root` is required for
        `diff-tree` to emit anything for a commit with NO parent (bare `diff-tree` shows an
        empty diff for a root commit otherwise; verified empirically — `--root` is a no-op
        for every non-root commit, so it is always safe to pass)."""
        out = _git(self.repo, "diff-tree", "--no-commit-id", "--name-only", "-r", "-m",
                  "--first-parent", "--root", sha, "--", "docs/build-plans")
        return sorted(p for p in out.splitlines() if p.endswith("/plan.md"))

    def _project(self, sha: str, report: SelfSyncReport) -> int:
        """Project one commit through the seam: emit the batch to the handoff, collect it
        back, land it in the OBSERVED-only store, attest. Idempotent: an already-projected
        sha is a no-op; `collect()` drains any batch a prior crash left in the handoff.
        Returns NEW observation rows landed (0 for a zero-fact commit, still marked)."""
        batch = self._observations_for(sha, report)
        content = self.handoff.emit_batch(sha, batch)
        added, _ = self.store.add_batch(self.handoff.collect(),
                                        interpreter=INTERPRETER_VERSION,
                                        history=self.history)
        self.store.mark_projected(sha, content, INTERPRETER_VERSION)
        if self.attestor is not None:
            # inputs=[commit sha], outputs=[batch content hash] (plan §6(d), verbatim).
            self.attestor.emit(agent_role="self_sensor", action="project_agent_observations",
                               input_hashes=[sha], output_hashes=[content])
        return added

    def _observations_for(self, sha: str, report: SelfSyncReport) -> list[AgentObservation]:
        """φ_self v1.0.0 (plan §6(e)): for each plan file changed at `sha` (first-parent
        diff), parse the `cost:` block at `sha` AND at `sha^` (absent parent/file ⇒ no
        prior facts — root commits treat all present facts as new); emit one
        `AgentObservation` per fact present at `sha` and absent-or-different at the parent.
        An unparseable NON-NULL value (§6(f)) yields no observation + a deterministic
        WARNING in the report — one line per (path, key), sha-prefixed; stable order (paths
        sorted by `_changed_plan_files`, keys in ('estimate', 'actual') order), so the same
        repo state always produces the same warnings."""
        out: list[AgentObservation] = []
        parents = _git(self.repo, "rev-list", "--parents", "-n", "1", sha).split()
        parent = parents[1] if len(parents) > 1 else None   # None ⇒ root commit (no parent)
        for path in self._changed_plan_files(sha):
            current = _read_plan_at(self.repo, sha, path)
            if current is None:
                continue                                     # deleted/renamed away at sha
            prior = _read_plan_at(self.repo, parent, path) if parent else None
            subject_id = str(current.get("_subject_id") or Path(path).parent.name)
            for key in ("estimate", "actual"):
                if key in current.get("_unparseable", ()):
                    report.warnings.append(                  # §6(f): deterministic skip, warned
                        f"unparseable non-null cost {key} at {sha[:12]} {path} — "
                        f"skipped, no observation")
                    continue
                fact = current.get(key)
                if fact is None:
                    continue                                 # null/absent ⇒ no observation
                if prior is not None and prior.get(key) == fact:
                    continue                                 # unchanged from the parent
                out.append(AgentObservation(commit_sha=sha, stream="cost",
                                            subject_id=subject_id, key=key, payload=fact))
        return out


def build_self_sensor(config: Config | None = None) -> SelfSensor:
    """Wire the agent's handles against the real repo, store, seam, and chain."""
    from config.loader import REPO_ROOT, get_config
    from core.attestation import build_attestor
    from core.stores.agent_observations import open_agent_observation_store
    from core.stores.observation_history import open_observation_history_store

    cfg = config or get_config()
    return SelfSensor(
        repo=REPO_ROOT,
        store=open_agent_observation_store(cfg),
        handoff=AgentSensingHandoff(handoff=cfg.paths.data_dir / "agent_sensing_handoff"),
        attestor=build_attestor(cfg),
        history=open_observation_history_store(cfg),
    )
