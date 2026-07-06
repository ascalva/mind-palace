#!/usr/bin/env python3
"""Shared decision logic for the six workflow hooks (design-note §6).

The bash hook scripts are thin, self-contained wrappers (mode detection, the
fail-loud trap, journal markers); the *decisions* live here where a real parser
and a correct glob matcher are cheap and robust. Every subcommand prints a
single decision line and exits 0 on a clean decision:

    ALLOW
    DENY: <reason>          # scope-guard / gate-guard: block the write (exit 2)
    BLOCK: <reason>         # journal-gate: block session close (exit 2)

An *internal* error raises (non-zero exit) so the calling bash wrapper can tell
"clean deny" (exit 0, decision=DENY) apart from "the enforcement machinery
broke" (exit != 0 -> fail-loud, fail-open). No third-party deps: system
python3 only, so the hooks never depend on the project .venv.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from datetime import datetime, timezone

# --- Foundation-file denylist (design-note §6, §10; origin: security-planes.md).
# Never writable by any session, orchestrator included, beneath any plan. These
# are the sacred fixed points (CONSTITUTION §V, §9): the constitution, the
# ratified design record, the frozen golden set. Blessing *transitions* on plans
# and notes are a separate concern handled by gate-guard.
DENYLIST = [
    "CONSTITUTION.md",
    "docs/design-notes/**",
    "eval/golden/**",
    "eval/golden.py",
]


# --------------------------------------------------------------------------- #
# Repo root + path normalization
# --------------------------------------------------------------------------- #
def repo_root() -> str:
    root = os.environ.get("CLAUDE_PROJECT_DIR")
    if root:
        return os.path.realpath(root)
    try:
        out = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            capture_output=True, text=True, check=True,
        )
        return os.path.realpath(out.stdout.strip())
    except Exception:
        return os.path.realpath(os.getcwd())


ROOT = repo_root()


def rel(path: str) -> str:
    """Normalize an arbitrary path to a clean repo-relative POSIX path."""
    if not path:
        return ""
    p = path
    if os.path.isabs(p):
        try:
            p = os.path.relpath(os.path.realpath(p), ROOT)
        except Exception:
            pass
    p = p.replace("\\", "/").lstrip("./")
    while p.startswith("/"):
        p = p[1:]
    return p


# --------------------------------------------------------------------------- #
# Glob matcher with correct `**` (any depth) vs `*` (within a segment) semantics
# --------------------------------------------------------------------------- #
def _seg_match(pat: str, seg: str) -> bool:
    """Match one path segment (no '/') against a glob segment (*, ?, literals)."""
    pi = si = 0
    star = -1
    star_si = 0
    while si < len(seg):
        if pi < len(pat) and (pat[pi] == "?" or pat[pi] == seg[si]):
            pi += 1
            si += 1
        elif pi < len(pat) and pat[pi] == "*":
            star = pi
            star_si = si
            pi += 1
        elif star != -1:
            pi = star + 1
            star_si += 1
            si = star_si
        else:
            return False
    while pi < len(pat) and pat[pi] == "*":
        pi += 1
    return pi == len(pat)


def glob_match(pattern: str, path: str) -> bool:
    """True if `path` matches `pattern`. `**` spans zero or more segments;
    `*`/`?` stay within a single segment. Both are repo-relative POSIX paths."""
    pattern = pattern.replace("\\", "/").lstrip("./")
    path = path.replace("\\", "/").lstrip("./")
    pp = pattern.split("/")
    tp = path.split("/")

    def m(i: int, j: int) -> bool:
        if i == len(pp):
            return j == len(tp)
        if pp[i] == "**":
            # `**` matches zero or more segments.
            for k in range(j, len(tp) + 1):
                if m(i + 1, k):
                    return True
            return False
        if j == len(tp):
            return False
        if _seg_match(pp[i], tp[j]):
            return m(i + 1, j + 1)
        return False

    return m(0, 0)


def matches_any(path: str, patterns) -> bool:
    return any(glob_match(pat, path) for pat in patterns)


# --------------------------------------------------------------------------- #
# Minimal front-matter parser (YAML subset: scalars + simple block/flow lists)
# --------------------------------------------------------------------------- #
def parse_front_matter(text: str) -> dict:
    if not text.startswith("---"):
        return {}
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}
    body = []
    for ln in lines[1:]:
        if ln.strip() == "---":
            break
        body.append(ln)
    out: dict = {}
    key = None
    for ln in body:
        if not ln.strip() or ln.lstrip().startswith("#"):
            continue
        if (ln.startswith("  - ") or ln.startswith("- ")) and key is not None:
            if not isinstance(out.get(key), list):
                out[key] = []  # upgrade the empty-value placeholder to a list
            out[key].append(_scalar(ln.split("-", 1)[1].strip()))
            continue
        if ":" in ln and not ln.startswith(" "):
            k, _, v = ln.partition(":")
            key = k.strip()
            v = v.strip()
            if v == "" or v is None:
                out[key] = ""  # value may be a block list on following lines
            elif v.startswith("[") and v.endswith("]"):
                inner = v[1:-1].strip()
                out[key] = [_scalar(x.strip()) for x in inner.split(",") if x.strip()]
            else:
                out[key] = _scalar(v)
    return out


def _scalar(v: str):
    v = v.strip()
    if len(v) >= 2 and v[0] in "\"'" and v[-1] == v[0]:
        v = v[1:-1]
    return v


def _normalize_status(v):
    """Strip a trailing YAML comment from a *status* value before the blessing
    detectors compare it by exact equality (A5, warrant finding-0006; design-note
    §6). Cut at the first ' #' (space-hash — YAML comment semantics), then rstrip.
    A '#' with no preceding space ('ready#x') is NOT a YAML comment and is left
    intact, so a malformed status can never be normalized *into* a blessing
    (false-negative-only, the safe direction). Scoped to the status extraction path
    only — `_scalar` stays general so a legitimate '#' survives in other fields."""
    if not isinstance(v, str):
        return v
    i = v.find(" #")
    if i != -1:
        v = v[:i]
    return v.rstrip()


def read_front_matter(path_abs: str) -> dict:
    try:
        with open(path_abs, "r", encoding="utf-8") as fh:
            return parse_front_matter(fh.read())
    except Exception:
        return {}


def status_of(path_rel: str):
    fm = read_front_matter(os.path.join(ROOT, path_rel))
    s = fm.get("status")
    if isinstance(s, str) and s:
        s = _normalize_status(s)
    return s if isinstance(s, str) and s else None


# --------------------------------------------------------------------------- #
# Active-plan resolution
# --------------------------------------------------------------------------- #
def active_plan_path() -> str | None:
    """Repo-relative path to the active plan.md, or None. The pointer is
    worktree-local (`.claude/state/active-plan`), so concurrent worktrees never
    collide on enforcement state (design-note §4)."""
    ptr = os.path.join(ROOT, ".claude", "state", "active-plan")
    try:
        with open(ptr, "r", encoding="utf-8") as fh:
            val = fh.read().strip()
    except Exception:
        return None
    if not val:
        return None
    val = rel(val)
    # Tolerate a bare plan id (e.g. "bp-000") as well as a path to plan.md.
    if not val.endswith(".md"):
        val = f"docs/build-plans/{val}/plan.md"
    return val if os.path.exists(os.path.join(ROOT, val)) else val


def plan_write_scope(plan_rel: str) -> list:
    fm = read_front_matter(os.path.join(ROOT, plan_rel))
    ws = fm.get("write_scope")
    if isinstance(ws, list):
        return [str(x) for x in ws if str(x).strip()]
    if isinstance(ws, str) and ws.strip():
        return [ws.strip()]
    return []


def journal_for(plan_rel: str) -> str:
    return os.path.join(os.path.dirname(plan_rel), "journal.md")


# --------------------------------------------------------------------------- #
# Artifact classification (for gate-guard)
# --------------------------------------------------------------------------- #
def is_design_note(path_rel: str) -> bool:
    return path_rel.startswith("docs/design-notes/") and path_rel.endswith(".md") \
        and not path_rel.rstrip("/").endswith("design-notes")


def is_build_plan(path_rel: str) -> bool:
    return path_rel.startswith("docs/build-plans/") and os.path.basename(path_rel) == "plan.md"


# --------------------------------------------------------------------------- #
# stdin (hook mode) JSON
# --------------------------------------------------------------------------- #
def load_stdin() -> dict:
    data = sys.stdin.read()
    if not data.strip():
        return {}
    try:
        return json.loads(data)
    except Exception:
        return {}


def _status_in_text(text: str):
    """Return the status value assigned by a `status:` line in a blob, or None."""
    for ln in text.splitlines():
        s = ln.strip().lstrip("+").strip()
        if s.startswith("status:"):
            return _normalize_status(_scalar(s.split(":", 1)[1]))
    return None


# =========================================================================== #
# Subcommands
# =========================================================================== #
def cmd_scope_check(file_path: str) -> int:
    fp = rel(file_path)
    if not fp:
        print("ALLOW")
        return 0
    # 1. Foundation denylist — absolute, beneath any plan, every session.
    if matches_any(fp, DENYLIST):
        print(f"DENY: foundation file '{fp}' is never writable by a session "
              f"(design-note §6 denylist); route a finding instead.")
        return 0
    # 2. Plan write-scope capability.
    plan = active_plan_path()
    if plan is None:
        # Orchestrator posture: no plan capability; denylist already applied.
        print("ALLOW")
        return 0
    allowed = list(plan_write_scope(plan))
    plandir = os.path.dirname(plan)
    allowed += [plan, f"{plandir}/journal.md", "docs/findings/**"]
    if matches_any(fp, allowed):
        print("ALLOW")
        return 0
    pid = os.path.basename(os.path.dirname(plan))
    print(f"DENY: '{fp}' is outside plan '{pid}' write_scope "
          f"{plan_write_scope(plan)} (+ its journal, + docs/findings/**). "
          f"A builder writes only its capability, its journal, and findings "
          f"(design-note §5). Revert, narrow, or raise a finding.")
    return 0


def cmd_gate_check(file_path: str, new_status) -> int:
    fp = rel(file_path)
    dn, bp = is_design_note(fp), is_build_plan(fp)
    if not (dn or bp):
        print("ALLOW")
        return 0
    cur = status_of(fp)  # on-disk status (None if new file)
    reason = ("blessing transitions are owner-manual, made by hand outside any "
              "agent session (design-note §10). ")
    if dn and new_status == "ratified" and cur != "ratified":
        print(f"DENY: {reason}Design-note ratification "
              f"({cur or 'new'}→ratified) on '{fp}' denied.")
        return 0
    if bp and new_status == "ready" and cur != "ready":
        print(f"DENY: {reason}Plan readiness "
              f"({cur or 'new'}→ready) on '{fp}' denied.")
        return 0
    print("ALLOW")
    return 0


def cmd_scope_check_hook() -> int:
    ev = load_stdin()
    ti = ev.get("tool_input", {}) or {}
    return cmd_scope_check(ti.get("file_path", "") or "")


def cmd_gate_check_hook() -> int:
    ev = load_stdin()
    ti = ev.get("tool_input", {}) or {}
    fp = ti.get("file_path", "") or ""
    # Gather every blob this tool would introduce, and read any status it sets.
    blobs = []
    if "content" in ti:
        blobs.append(str(ti.get("content") or ""))
    if "new_string" in ti:
        blobs.append(str(ti.get("new_string") or ""))
    for e in ti.get("edits", []) or []:
        blobs.append(str((e or {}).get("new_string") or ""))
    new_status = None
    for b in blobs:
        s = _status_in_text(b)
        if s:
            new_status = s
    if new_status is None:
        # The edit does not touch status -> no transition -> allow.
        print("ALLOW")
        return 0
    return cmd_gate_check(fp, new_status)


def _changed_files() -> list:
    try:
        out = subprocess.run(
            # -uall lists untracked files individually (not collapsed to a dir),
            # so file paths match a deep write_scope glob correctly.
            ["git", "status", "--porcelain", "--no-renames", "-uall"],
            capture_output=True, text=True, cwd=ROOT, check=True,
        ).stdout
    except Exception:
        return []
    files = []
    for ln in out.splitlines():
        if len(ln) < 4:
            continue
        files.append(ln[3:].strip())
    return files


def _diff_text_head() -> str:
    """Unified diff of the working tree against HEAD, scoped to the artifact trees
    that carry blessings. Against HEAD (not a stale session baseline) so a
    *committed* blessing self-clears — it is in history, hence accountable to its
    commit author (§10, "deliberate, logged") — while an *uncommitted* in-flight
    flip still shows (§6c, A1; warrant finding-0003)."""
    try:
        return subprocess.run(
            ["git", "diff", "HEAD", "--", "docs/design-notes", "docs/build-plans"],
            capture_output=True, text=True, cwd=ROOT,
        ).stdout
    except Exception:
        return ""


def _blessing_in_diff(diff: str) -> str | None:
    """Scan unified diff text for a Bash-mediated blessing transition."""
    cur_file = None
    for ln in diff.splitlines():
        if ln.startswith("+++ b/"):
            cur_file = rel(ln[6:].strip())
            continue
        if ln.startswith("diff --git"):
            cur_file = None
            continue
        if not ln.startswith("+") or ln.startswith("+++"):
            continue
        body = ln[1:].strip()
        if not body.startswith("status:"):
            continue
        val = _normalize_status(_scalar(body.split(":", 1)[1]))
        if cur_file and is_design_note(cur_file) and val == "ratified":
            return f"design-note ratification introduced in '{cur_file}'"
        if cur_file and is_build_plan(cur_file) and val == "ready":
            return f"plan readiness introduced in '{cur_file}'"
    return None


def _untracked_under(prefixes) -> list:
    """Untracked, non-ignored files under the given path prefixes. `--others` is
    precisely the set a tracked-only `git diff HEAD` cannot see; `--exclude-standard`
    honors .gitignore, so a genuinely ambient ignored path (e.g.
    `.claude/settings.local.json`, finding-0004) never enters the audit at all."""
    try:
        out = subprocess.run(
            ["git", "ls-files", "--others", "--exclude-standard", "--", *prefixes],
            capture_output=True, text=True, cwd=ROOT, check=True,
        ).stdout
    except Exception:
        return []
    return [rel(ln.strip()) for ln in out.splitlines() if ln.strip()]


def _untracked_blessing() -> str | None:
    """A3 (warrant finding-0005): a plan or design note *minted fresh through Bash*
    directly at a blessed status. Such a file is untracked, so it is invisible to
    `git diff HEAD` (the tracked (c) path scanned by `_blessing_in_diff`) and to
    gate-guard (Edit/Write-only) — the exact hole that left `proposed → ready`
    unenforced against a Bash-minting agent, the asymmetry A1 fixed for (b) but left
    open in (c). Its on-disk front-matter is therefore read directly, and a new file
    already at a blessed status is treated as a blessing transition *from nothing* —
    the same as flipping one in place. A newly minted plan is legitimate only at
    `status: proposed` (a note at `draft`); `ready`/`ratified` on an untracked file
    is a violation. Untracked ⇒ never committed, so this cannot fire on a committed
    (accountable, self-clearing) blessing — the A1 behavior is preserved intact."""
    for f in _untracked_under(["docs/design-notes", "docs/build-plans"]):
        if is_design_note(f) and status_of(f) == "ratified":
            return f"design-note ratification on untracked file '{f}'"
        if is_build_plan(f) and status_of(f) == "ready":
            return f"plan readiness on untracked file '{f}'"
    return None


def cmd_stop_audit(diff_file: str | None) -> int:
    reasons = []
    plan = active_plan_path()

    # (a) journal staleness + (b) out-of-scope worktree changes -> need a plan.
    if plan is not None:
        journal = journal_for(plan)
        j_abs = os.path.join(ROOT, journal)
        try:
            last_commit = int(subprocess.run(
                ["git", "log", "-1", "--format=%ct"],
                capture_output=True, text=True, cwd=ROOT, check=True,
            ).stdout.strip() or "0")
        except Exception:
            last_commit = 0
        if last_commit and os.path.exists(j_abs):
            if os.path.getmtime(j_abs) < last_commit:
                reasons.append(
                    f"(a) journal '{journal}' mtime predates the last commit — "
                    f"checkpoint before close (§9).")
        elif not os.path.exists(j_abs):
            reasons.append(f"(a) journal '{journal}' is missing for the active plan.")

        allowed = list(plan_write_scope(plan))
        plandir = os.path.dirname(plan)
        allowed += [plan, f"{plandir}/journal.md", "docs/findings/**"]
        oos = [f for f in _changed_files()
               if f and not matches_any(f, allowed) and not matches_any(f, DENYLIST)]
        deny = [f for f in _changed_files() if f and matches_any(f, DENYLIST)]
        if oos:
            reasons.append(
                "(b) out-of-scope changes in the worktree (Bash-mediated writes "
                f"the pre-hoc guard cannot see): {oos}. Revert or route a finding.")
        if deny:
            reasons.append(f"(b) foundation files modified: {deny}.")
    else:
        deny = [f for f in _changed_files() if f and matches_any(f, DENYLIST)]
        if deny:
            reasons.append(f"(b) foundation files modified: {deny}.")

    # (c) uncommitted blessing transition -> every session. Diff the working tree
    # against HEAD, not the session baseline (§6c, A1; warrant finding-0003): a
    # *committed* blessing is accountable to its commit author (§10, "deliberate,
    # logged") and must self-clear; only an *uncommitted* in-flight flip is
    # flagged. session-baseline is retained solely for the SessionStart brief's
    # narration and is deliberately not consulted here.
    if diff_file:
        try:
            with open(diff_file, "r", encoding="utf-8") as fh:
                diff = fh.read()
        except Exception:
            diff = ""
    else:
        diff = _diff_text_head()
    bless = _blessing_in_diff(diff)
    if bless:
        reasons.append(
            f"(c) uncommitted blessing transition vs HEAD: {bless}. Blessing is "
            f"owner-manual (§10) — commit it (then it is accountable) or revert "
            f"the Bash-mediated flip.")

    # A3 (warrant finding-0005): the (c) detector is untracked-inclusive over the
    # blessing surfaces. The tracked diff above sees a *flip of an existing artifact*
    # but not a plan/note *minted fresh through Bash* directly at a blessed status —
    # that file is untracked, invisible both to `git diff HEAD` and to gate-guard
    # (Edit/Write-only). This reads the untracked plan/design paths directly so all
    # three owner-only blessings are enforced against the Bash write path too. It
    # scans only *untracked* files, so a committed blessing (tracked, in HEAD) never
    # trips it — the A1 committed-self-clears behavior is preserved unchanged.
    unbless = _untracked_blessing()
    if unbless:
        reasons.append(
            f"(c) uncommitted blessing transition vs HEAD: {unbless}. A newly minted "
            f"plan is legitimate only at status: proposed (a design note at draft); a "
            f"blessed status on an untracked file is a from-nothing blessing (§6c, "
            f"A3). Commit it (then it is accountable to its author) or revert the "
            f"Bash-mediated creation.")

    if reasons:
        print("BLOCK: " + " ".join(reasons))
    else:
        print("ALLOW")
    return 0


def cmd_brief() -> int:
    lines = ["═══ SESSION BRIEF ═══  (bare session at root ⇒ orchestrator posture)"]

    # Plans by status.
    plans = {}
    bp_dir = os.path.join(ROOT, "docs", "build-plans")
    if os.path.isdir(bp_dir):
        for pid in sorted(os.listdir(bp_dir)):
            pm = os.path.join(bp_dir, pid, "plan.md")
            if os.path.exists(pm):
                st = read_front_matter(pm).get("status", "?") or "?"
                plans.setdefault(str(st), []).append(pid)
    if plans:
        lines.append("Plans: " + "; ".join(
            f"{st}={','.join(ids)}" for st, ids in sorted(plans.items())))
    else:
        lines.append("Plans: (none yet)")

    # Findings not yet terminal (open/routed).
    fnd_open = 0
    fnd_dir = os.path.join(ROOT, "docs", "findings")
    if os.path.isdir(fnd_dir):
        for fn in os.listdir(fnd_dir):
            if fn.endswith(".md"):
                st = read_front_matter(os.path.join(fnd_dir, fn)).get("status", "")
                if st in ("open", "routed"):
                    fnd_open += 1
    lines.append(f"Unswept findings: {fnd_open}")

    # Open owner questions.
    oq = os.path.join(ROOT, "docs", "inbox", "owner-questions.md")
    open_q = 0
    if os.path.exists(oq):
        with open(oq, encoding="utf-8") as fh:
            for ln in fh:
                if ln.strip().lower().startswith("- status:") and "open" in ln.lower():
                    open_q += 1
    lines.append(f"Open owner questions: {open_q}  (docs/inbox/owner-questions.md)")

    # Active worktree plan.
    plan = active_plan_path()
    lines.append(f"Active plan (this worktree): {plan if plan else '(none)'}")

    # Book debt (§11). Book scaffold is post-BP-000 (first scribe plan).
    if not os.path.isdir(os.path.join(ROOT, "docs", "book")):
        lines.append("Book: not yet scaffolded — first scribe plan pending (§12).")

    lines.append("Duties: /graduate · /build · /resume · /triage · /scribe · /capture. "
                 "Never block on the owner (§5); park + finding + continue.")
    print("\n".join(lines))
    return 0


def cmd_staleness() -> int:
    plan = active_plan_path()
    if plan is None:
        return 0
    j_abs = os.path.join(ROOT, journal_for(plan))
    try:
        head_ct = int(subprocess.run(
            ["git", "log", "-1", "--format=%ct"],
            capture_output=True, text=True, cwd=ROOT, check=True,
        ).stdout.strip() or "0")
    except Exception:
        return 0
    if head_ct and os.path.exists(j_abs) and os.path.getmtime(j_abs) < head_ct:
        print("⟳ journal is stale relative to HEAD — checkpoint at the next "
              "semantic boundary (§9).")
    return 0


def cmd_marker(text: str) -> int:
    plan = active_plan_path()
    if plan is None:
        # Best-effort: nothing to mark without an active journal.
        return 0
    j_abs = os.path.join(ROOT, journal_for(plan))
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    line = f"- [{ts}] {text}\n"
    try:
        os.makedirs(os.path.dirname(j_abs), exist_ok=True)
        with open(j_abs, "a", encoding="utf-8") as fh:
            fh.write(line)
    except Exception:
        return 0
    return 0


def main(argv) -> int:
    if not argv:
        print("usage: _lib.py <scope-check|gate-check|gate-check-hook|"
              "stop-audit|brief|staleness|marker> [args]", file=sys.stderr)
        return 64
    cmd = argv[0]
    if cmd == "scope-check":
        return cmd_scope_check(argv[1] if len(argv) > 1 else "")
    if cmd == "scope-check-hook":
        return cmd_scope_check_hook()
    if cmd == "gate-check":
        return cmd_gate_check(argv[1] if len(argv) > 1 else "",
                              argv[2] if len(argv) > 2 else None)
    if cmd == "gate-check-hook":
        return cmd_gate_check_hook()
    if cmd == "stop-audit":
        diff_file = None
        if "--diff-file" in argv:
            i = argv.index("--diff-file")
            diff_file = argv[i + 1] if i + 1 < len(argv) else None
        return cmd_stop_audit(diff_file)
    if cmd == "brief":
        return cmd_brief()
    if cmd == "staleness":
        return cmd_staleness()
    if cmd == "marker":
        return cmd_marker(" ".join(argv[1:]))
    print(f"_lib.py: unknown subcommand {cmd!r}", file=sys.stderr)
    return 64


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
