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
from datetime import UTC, datetime

# --- Foundation-file denylist (design-note §6, §10; origin: security-planes.md).
# Never writable by any session, orchestrator included, beneath any plan. These
# are the sacred fixed points (CONSTITUTION §V, §9): the constitution and the
# frozen golden set. Design notes left this list under amendment A8 (warrant
# finding-0025): they are guarded by STATUS, not location — draft notes are
# agent-writable working material (cmd_scope_check's status arm + the (b2)
# HEAD-keyed Stop clause protect the ratified/superseded record instead).
# Blessing *transitions* on plans and notes remain gate-guard's concern.
DENYLIST = [
    "CONSTITUTION.md",
    "eval/golden/**",
    "eval/golden.py",
]


# --------------------------------------------------------------------------- #
# Repo root + path normalization
# --------------------------------------------------------------------------- #
def _cwd_toplevel() -> str | None:
    """The git-worktree toplevel of the process CWD (realpath'd), or None. Each
    git worktree is its own toplevel, so from a hook firing inside a worktree this
    returns the WORKTREE path — the correct enforcement root (finding-0031)."""
    try:
        out = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            capture_output=True,
            text=True,
            check=True,
        )
        top = out.stdout.strip()
        return os.path.realpath(top) if top else None
    except Exception:
        return None


def repo_root() -> str:
    """Resolve the enforcement ROOT worktree-aware (finding-0031 / bp-014).

    Prefer the CWD git-worktree toplevel over the inherited ``CLAUDE_PROJECT_DIR``
    **when they differ AND the CWD-toplevel carries its own ``.claude/state/``** —
    so a hook firing inside a worktree reads THAT worktree's ``active-plan`` pointer,
    not the main checkout's (which the delegate harness sets ``CLAUDE_PROJECT_DIR``
    to). Fail-closed: the CWD worktree's own state governs its own writes, so a broad
    main-checkout pointer never loosens a narrow worktree builder. When the two agree,
    or the CWD-toplevel lacks ``.claude/state/``, behavior is byte-identical to before
    (the common main-checkout case). Both sides are realpath-normalized so
    ``/tmp``→``/private/tmp`` symlink drift can never spoof the comparison."""
    env = os.environ.get("CLAUDE_PROJECT_DIR")
    env_norm = os.path.realpath(env) if env else None
    cwd_top = _cwd_toplevel()
    if (
        cwd_top
        and cwd_top != env_norm
        and os.path.isdir(os.path.join(cwd_top, ".claude", "state"))
    ):
        return cwd_top
    if env_norm:
        return env_norm
    if cwd_top:
        return cwd_top
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
    if len(v) >= 2 and v[0] in "\"'":
        # Quoted scalar: honor the closing quote and DISCARD any trailing inline
        # comment after it (`"path"  # note`). This is the write_scope list-entry
        # shape the oq-0013 amendment introduced (bp-012's builder worked around a
        # mis-parse where the comment stayed glued to the value). Only the quoted
        # form is trimmed here; an UNQUOTED scalar keeps its '#' intact so a
        # legitimate hash in a plain value (or a status like `ready#x`, guarded by
        # _normalize_status) is never silently truncated — _scalar stays general.
        q = v[0]
        end = v.find(q, 1)
        if end != -1:
            return v[1:end]
        return v[1:]  # unterminated quote — best-effort strip of the leading quote
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
        with open(path_abs, encoding="utf-8") as fh:
            return parse_front_matter(fh.read())
    except Exception:
        return {}


def status_of(path_rel: str):
    fm = read_front_matter(os.path.join(ROOT, path_rel))
    s = fm.get("status")
    if isinstance(s, str) and s:
        s = _normalize_status(s)
    return s if isinstance(s, str) and s else None


def verdict_of(path_rel: str):
    """On-disk `verdict:` of a deskcheck record, normalized (None if absent). The
    deskcheck analogue of status_of — it is the field the third gate protects.
    `_normalize_status` is the YAML-comment strip (` #…`) and is field-agnostic, so
    the template's `verdict: pending  # …` inline comment reads back as `pending`
    (owner DRY: one comment-strip, not a `_normalize_verdict` twin)."""
    fm = read_front_matter(os.path.join(ROOT, path_rel))
    v = fm.get("verdict")
    if isinstance(v, str) and v:
        v = _normalize_status(v)
    return v if isinstance(v, str) and v else None


def git_show_head(path_rel: str) -> str | None:
    """`git show HEAD:<path>` text, or None when the path does not exist at HEAD
    (the committed truth — the read-HEAD discipline the (b2)/(c) post-hoc clauses
    share, since a Bash write may have laundered the on-disk value already)."""
    try:
        return subprocess.run(
            ["git", "show", f"HEAD:{path_rel}"],
            capture_output=True,
            text=True,
            cwd=ROOT,
            check=True,
        ).stdout
    except Exception:
        return None


def _head_status_of(path_rel: str):
    """Front-matter status of the file AT HEAD (the committed truth), or None when the
    file does not exist at HEAD. The Stop-side design-note clause (b2) compares against
    THIS, never the working tree: post-hoc, a Bash write has already happened, so the
    on-disk status may be the laundered value (A8, finding-0025 Correction 2 — the same
    read-HEAD discipline as _blessing_in_diff). Normalized with _normalize_status for A5
    parity: comment evasion must not survive the HEAD read either."""
    out = git_show_head(path_rel)
    if out is None:
        return None
    s = parse_front_matter(out).get("status")
    if isinstance(s, str) and s:
        s = _normalize_status(s)
    return s if isinstance(s, str) and s else None


# --------------------------------------------------------------------------- #
# Active-plan resolution
# --------------------------------------------------------------------------- #
def active_plan_path() -> str | None:
    """Repo-relative path to the active plan.md, or None. The pointer is
    worktree-local (`.claude/state/active-plan`), so concurrent worktrees never
    collide on enforcement state (design-note §4). This holds because `repo_root()`
    resolves ROOT to the CWD worktree's own toplevel (bp-014), so this read is of
    THIS worktree's pointer — never the main checkout's."""
    ptr = os.path.join(ROOT, ".claude", "state", "active-plan")
    try:
        with open(ptr, encoding="utf-8") as fh:
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


def _normalize_plan_ref(val: str) -> str:
    """Normalize a raw ``active-plan`` pointer value to the same
    ``docs/build-plans/<id>/plan.md`` form ``active_plan_path()`` produces, WITHOUT
    checking existence against this worktree's ``ROOT`` — the value may name a plan
    in a different checkout entirely (the (d) cross-checkout bleed check's use case,
    warrant finding-0051). Tolerates a bare plan id or a path; strips a leading
    slash and normalizes separators the same way ``rel()`` does, but never resolves
    against ``ROOT`` (that would silently coerce a foreign path onto this
    worktree's filesystem)."""
    v = val.strip().replace("\\", "/").lstrip("./")
    while v.startswith("/"):
        v = v[1:]
    if not v.endswith(".md"):
        v = f"docs/build-plans/{v}/plan.md"
    return v


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
    return (
        path_rel.startswith("docs/design-notes/")
        and path_rel.endswith(".md")
        and not path_rel.rstrip("/").endswith("design-notes")
    )


def is_build_plan(path_rel: str) -> bool:
    return path_rel.startswith("docs/build-plans/") and os.path.basename(path_rel) == "plan.md"


def is_deskcheck(path_rel: str) -> bool:
    """A deskcheck RECORD: `docs/deskchecks/dc-NNN.md` (design-note D3). Gated on the
    `dc-` basename prefix so the store's `README.md`/`.gitkeep` scaffolding is never
    mistaken for a record whose `verdict:` is owner-only (mirrors is_design_note's
    shape, but keyed on the filename convention the third gate protects)."""
    return (
        path_rel.startswith("docs/deskchecks/")
        and path_rel.endswith(".md")
        and os.path.basename(path_rel).startswith("dc-")
    )


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


def _verdict_in_text(text: str):
    """Return the value assigned by a `verdict:` line in a blob, or None — the
    deskcheck sibling of _status_in_text (Q2: `_status_in_text` is named for status
    and must NOT be assumed to match `verdict:`, so the read is explicit here)."""
    for ln in text.splitlines():
        s = ln.strip().lstrip("+").strip()
        if s.startswith("verdict:"):
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
        print(
            f"DENY: foundation file '{fp}' is never writable by a session "
            f"(design-note §6 denylist); route a finding instead."
        )
        return 0
    # 1b. Design notes — guarded by STATUS, not location (A8, warrant finding-0025).
    #     On-disk status is the committed truth here: pre-hoc, the write has not
    #     happened yet. Ratified/superseded = the blessed/historical record,
    #     agent-immutable in content AND status (the Bash/laundering paths are the
    #     Stop audit's (b2) clause). Draft or new notes are working material and
    #     fall through to the normal capability check.
    if is_design_note(fp):
        st = status_of(fp)
        if st in ("ratified", "superseded"):
            print(
                f"DENY: design note '{fp}' is {st} — the blessed record is "
                f"agent-immutable (A8). Evolve it via supersession or a finding "
                f"at the owner's gate, never in place."
            )
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
    print(
        f"DENY: '{fp}' is outside plan '{pid}' write_scope "
        f"{plan_write_scope(plan)} (+ its journal, + docs/findings/**). "
        f"A builder writes only its capability, its journal, and findings "
        f"(design-note §5). Revert, narrow, or raise a finding."
    )
    return 0


def cmd_gate_check(file_path: str, new_status) -> int:
    fp = rel(file_path)
    dn, bp, dc = is_design_note(fp), is_build_plan(fp), is_deskcheck(fp)
    if not (dn or bp or dc):
        print("ALLOW")
        return 0
    reason = (
        "blessing transitions are owner-manual, made by hand outside any "
        "agent session (design-note §10). "
    )
    if dn or bp:
        cur = status_of(fp)  # on-disk status (None if new file)
        if dn and new_status == "ratified" and cur != "ratified":
            print(
                f"DENY: {reason}Design-note ratification "
                f"({cur or 'new'}→ratified) on '{fp}' denied."
            )
            return 0
        if bp and new_status == "ready" and cur != "ready":
            print(f"DENY: {reason}Plan readiness ({cur or 'new'}→ready) on '{fp}' denied.")
            return 0
    if dc:
        # The third owner-only gate (design-note D3): a deskcheck verdict flip to
        # approved|needs-work is owner-by-hand. `pending` (the only agent-legal
        # start) always passes. `cur or 'pending'` names the effective prior value.
        cur = verdict_of(fp)  # on-disk verdict (None if new file / no verdict yet)
        nv = _normalize_status(new_status) if isinstance(new_status, str) else new_status
        if nv in ("approved", "needs-work") and cur != nv:
            print(f"DENY: {reason}Deskcheck verdict ({cur or 'pending'}→{nv}) on '{fp}' denied.")
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
    # Gather every blob this tool would introduce, and read the field this file
    # type's gate keys on: `verdict:` for a deskcheck record, `status:` otherwise.
    blobs = []
    if "content" in ti:
        blobs.append(str(ti.get("content") or ""))
    if "new_string" in ti:
        blobs.append(str(ti.get("new_string") or ""))
    for e in ti.get("edits", []) or []:
        blobs.append(str((e or {}).get("new_string") or ""))
    reader = _verdict_in_text if is_deskcheck(rel(fp)) else _status_in_text
    new_value = None
    for b in blobs:
        v = reader(b)
        if v:
            new_value = v
    if new_value is None:
        # The edit sets no gated field -> no transition -> allow.
        print("ALLOW")
        return 0
    return cmd_gate_check(fp, new_value)


def _changed_files() -> list:
    try:
        out = subprocess.run(
            # -uall lists untracked files individually (not collapsed to a dir),
            # so file paths match a deep write_scope glob correctly.
            ["git", "status", "--porcelain", "--no-renames", "-uall"],
            capture_output=True,
            text=True,
            cwd=ROOT,
            check=True,
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
            # docs/deskchecks joins the blessing surfaces so the (c) scanner sees a
            # Bash-mediated verdict flip (the third owner-only gate, D3/D6).
            ["git", "diff", "HEAD", "--",
             "docs/design-notes", "docs/build-plans", "docs/deskchecks"],
            capture_output=True,
            text=True,
            cwd=ROOT,
        ).stdout
    except Exception:
        return ""


def _blessing_in_diff(diff: str) -> str | None:
    """Scan unified diff text for a Bash-mediated blessing OR deskcheck-verdict
    transition (all three owner-only flips, D3/D6)."""
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
        if body.startswith("status:"):
            val = _normalize_status(_scalar(body.split(":", 1)[1]))
            if cur_file and is_design_note(cur_file) and val == "ratified":
                return f"design-note ratification introduced in '{cur_file}'"
            if cur_file and is_build_plan(cur_file) and val == "ready":
                return f"plan readiness introduced in '{cur_file}'"
        elif body.startswith("verdict:"):
            val = _normalize_status(_scalar(body.split(":", 1)[1]))
            if cur_file and is_deskcheck(cur_file) and val in ("approved", "needs-work"):
                return f"deskcheck verdict ({val}) introduced in '{cur_file}'"
    return None


def _untracked_under(prefixes) -> list:
    """Untracked, non-ignored files under the given path prefixes. `--others` is
    precisely the set a tracked-only `git diff HEAD` cannot see; `--exclude-standard`
    honors .gitignore, so a genuinely ambient ignored path (e.g.
    `.claude/settings.local.json`, finding-0004) never enters the audit at all."""
    try:
        out = subprocess.run(
            ["git", "ls-files", "--others", "--exclude-standard", "--", *prefixes],
            capture_output=True,
            text=True,
            cwd=ROOT,
            check=True,
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
    for f in _untracked_under(["docs/design-notes", "docs/build-plans", "docs/deskchecks"]):
        if is_design_note(f) and status_of(f) == "ratified":
            return f"design-note ratification on untracked file '{f}'"
        if is_build_plan(f) and status_of(f) == "ready":
            return f"plan readiness on untracked file '{f}'"
        if is_deskcheck(f) and verdict_of(f) in ("approved", "needs-work"):
            return f"deskcheck verdict on untracked file '{f}'"
    return None


def _split_front_matter(text: str) -> tuple[str, str]:
    """Split a doc into (front-matter-text, body-text) at the `---` fences. When
    there is no front matter, the whole doc is body. A missing closing fence means
    all-front-matter, no body (best-effort; the body compare then trivially holds)."""
    if not text.startswith("---"):
        return "", text
    lines = text.splitlines(keepends=True)
    if not lines or lines[0].strip() != "---":
        return "", text
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            return "".join(lines[1:i]), "".join(lines[i + 1 :])
    return "".join(lines[1:]), ""


def _is_additive_frontmatter_only(file_rel: str) -> bool:
    """True iff the working-tree change to `file_rel` vs HEAD is PURELY additive
    front matter: body byte-identical, `status` unchanged, no existing key changed —
    only new `key: value` lines added (e.g. the owner staging a `track:` line). This
    gates the (b2) owner-staged YIELD posture, and it is deliberately false-negative
    safe: ANY body edit, status change, key mutation, or a deletion/unreadable file
    returns False, so a body edit can NEVER earn the yield message that invites a
    commit (design-note D6; plan bp-097 §6, §10). Comparing the parsed body + the
    front-matter key-map (not raw diff lines) makes a body line dressed as `key:`
    fall out via the body compare, not slip through a line-shape regex."""
    head_text = git_show_head(file_rel)
    if head_text is None:
        return False  # not at HEAD (untracked) — not a modification of a blessed note
    try:
        with open(os.path.join(ROOT, file_rel), encoding="utf-8") as fh:
            work_text = fh.read()
    except Exception:
        return False  # deleted / unreadable -> never yield
    _, head_body = _split_front_matter(head_text)
    _, work_body = _split_front_matter(work_text)
    if head_body != work_body:
        return False  # any body change -> hard block, no yield
    head_fm = parse_front_matter(head_text)
    work_fm = parse_front_matter(work_text)
    if head_fm.get("status") != work_fm.get("status"):
        return False  # a status flip is never mere metadata
    for k, v in head_fm.items():
        if work_fm.get(k) != v:
            return False  # an existing key changed/removed -> not purely additive
    return work_fm != head_fm  # something WAS added (else it is a no-op, not a yield case)


def _sealed_plans_in_diff(diff: str) -> list:
    """Build-plan files whose diff introduces `status: complete` — a seal made this
    session (mirrors _blessing_in_diff's per-file status parse). Clause (f) checks
    each such plan's journal for the follow-through block before allowing close."""
    out = []
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
        if body.startswith("status:"):
            val = _normalize_status(_scalar(body.split(":", 1)[1]))
            if cur_file and is_build_plan(cur_file) and val == "complete":
                out.append(cur_file)
    return out


def _journal_tail_has_followthrough(journal_rel: str) -> bool:
    """Does the journal's LAST entry carry a `## Follow-through` block? Sealed
    journals order oldest-first with the SEAL entry at the tail (observed bp-007..
    bp-011), and the five follow-through questions (D5, checkpoint skill) live in
    that seal entry. Bounded to the final entry — the tail from the last `## `
    header that is neither the Follow-through block itself nor the hook-appended
    `## Markers` trailer — so an EARLY draft mention can't false-clear the gate.
    Header-presence only: the grep-class tooth (F-WF5's accepted residual — the
    block's completeness is the deskcheck's job, not this crude check's)."""
    try:
        with open(os.path.join(ROOT, journal_rel), encoding="utf-8") as fh:
            text = fh.read()
    except Exception:
        return False  # missing journal for a sealed plan -> block (a seal must checkpoint)
    lines = text.splitlines()
    start = 0
    for i, ln in enumerate(lines):
        s = ln.strip()
        if ln.startswith("## ") and s != "## Follow-through" and s != "## Markers":
            start = i
    tail = "\n".join(lines[start:])
    return "## Follow-through" in tail


def cmd_stop_audit(diff_file: str | None) -> int:
    reasons = []
    plan = active_plan_path()

    # HEAD sha + last-commit epoch in ONE subprocess — shared by (a) journal
    # staleness and (e) the session-handoff gate (owner DRY rule: never a second
    # git call). Empty-repo safe: "" / 0 on failure, and every use is guarded
    # (`if last_commit and ...`, `if ... head_sha ...`). %H yields the same 40-char
    # sha session-brief.sh records into session-baseline via `git rev-parse HEAD`,
    # so (e)'s `head_sha != baseline` is a valid commits-this-session test.
    try:
        _headline = subprocess.run(
            ["git", "log", "-1", "--format=%H %ct"],
            capture_output=True,
            text=True,
            cwd=ROOT,
            check=True,
        ).stdout.split()
        head_sha = _headline[0] if _headline else ""
        last_commit = int(_headline[1]) if len(_headline) > 1 else 0
    except Exception:
        head_sha, last_commit = "", 0

    # (a) journal staleness + (b) out-of-scope worktree changes -> need a plan.
    if plan is not None:
        journal = journal_for(plan)
        j_abs = os.path.join(ROOT, journal)
        if last_commit and os.path.exists(j_abs):
            if os.path.getmtime(j_abs) < last_commit:
                reasons.append(
                    f"(a) journal '{journal}' mtime predates the last commit — "
                    f"checkpoint before close (§9)."
                )
        elif not os.path.exists(j_abs):
            reasons.append(f"(a) journal '{journal}' is missing for the active plan.")

        allowed = list(plan_write_scope(plan))
        plandir = os.path.dirname(plan)
        allowed += [plan, f"{plandir}/journal.md", "docs/findings/**"]
        oos = [
            f
            for f in _changed_files()
            if f and not matches_any(f, allowed) and not matches_any(f, DENYLIST)
        ]
        deny = [f for f in _changed_files() if f and matches_any(f, DENYLIST)]
        if oos:
            reasons.append(
                "(b) out-of-scope changes in the worktree (Bash-mediated writes "
                f"the pre-hoc guard cannot see): {oos}. Revert or route a finding."
            )
        if deny:
            reasons.append(f"(b) foundation files modified: {deny}.")
    else:
        deny = [f for f in _changed_files() if f and matches_any(f, DENYLIST)]
        if deny:
            reasons.append(f"(b) foundation files modified: {deny}.")

    # (b2) design-note immutability, HEAD-keyed -> every session (A8, warrant
    # finding-0025 Correction 2). The working tree's status can be laundered by a
    # Bash write; HEAD's cannot. Any modification or deletion of a note that is
    # ratified/superseded AT HEAD blocks close — symmetric with (c)'s read-HEAD
    # blessing detection, and untracked-new notes pass (no HEAD status: legal
    # draft creation; a forged untracked blessing is (c)'s _untracked_blessing).
    tampered = [
        f
        for f in _changed_files()
        if f and is_design_note(f) and _head_status_of(f) in ("ratified", "superseded")
    ]
    if tampered:
        # D6 yield (bp-097): if EVERY tampered note's change is purely additive front
        # matter (the owner staging a `track:` line — no body or status change), the
        # reason gains the owner-staged yield posture. It STILL BLOCKS until committed
        # — the yield only guides "commit + say-so-once, don't thrash" instead of
        # "revert". `all(...)` is conservative: a single non-additive (body edit,
        # deletion, key mutation) among them, or any doubt, keeps the hard block —
        # a body edit must NEVER earn the commit-inviting yield message (§10).
        if all(_is_additive_frontmatter_only(f) for f in tampered):
            reasons.append(
                f"(b2) blessed design notes modified vs HEAD: {tampered} — the change "
                "is additive front matter only (no body or status edit). If this is "
                "the owner's staged hand (e.g. a `track:` line), commit it (then it is "
                "accountable) and say so ONCE — do not thrash. A ratified/superseded "
                "note's BODY stays agent-immutable (A8)."
            )
        else:
            reasons.append(
                f"(b2) blessed design notes modified/deleted vs HEAD: {tampered} — "
                "ratified/superseded notes are agent-immutable (A8). Revert the "
                "session's change, or the owner commits their own edit (then it is "
                "accountable)."
            )

    # (c) uncommitted blessing transition -> every session. Diff the working tree
    # against HEAD, not the session baseline (§6c, A1; warrant finding-0003): a
    # *committed* blessing is accountable to its commit author (§10, "deliberate,
    # logged") and must self-clear; only an *uncommitted* in-flight flip is
    # flagged. session-baseline is deliberately not consulted by (c) here (which
    # diffs against HEAD); its second consumer is clause (e) below — the
    # session-handoff gate (dn-session-handoff-gate) — where its content is the
    # commits-this-session guard for the orchestrator resume-brief check.
    if diff_file:
        try:
            with open(diff_file, encoding="utf-8") as fh:
                diff = fh.read()
        except Exception:
            diff = ""
    else:
        diff = _diff_text_head()
    bless = _blessing_in_diff(diff)
    if bless:
        reasons.append(
            f"(c) uncommitted blessing/verdict transition vs HEAD: {bless}. Blessings "
            f"and deskcheck verdicts are owner-manual (§10). If this flip is yours "
            f"(agent), revert the Bash-mediated change; if it is the owner's staged "
            f"hand, say so once and YIELD — commit it (then it is accountable), do not "
            f"poll, do not re-ask."
        )

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
            f"plan is legitimate only at status: proposed (a design note at draft, a "
            f"deskcheck at verdict: pending); a blessed status/verdict on an untracked "
            f"file is a from-nothing blessing (§6c, A3). Commit it (then it is "
            f"accountable to its author) or revert the Bash-mediated creation."
        )

    # (d) cross-checkout state bleed (warrant finding-0051) -> worktree sessions only.
    # A worktree builder must never write the MAIN checkout's .claude/state/**; the
    # pre-hoc guard can't see the Bash write, so flag it at Stop. Signature (zero false
    # positives, §3 Q3): running in a worktree AND main's active-plan resolves to THIS
    # worktree's own plan. Read-only; fail-open on any error (enforcement never crashes).
    try:
        env_top = os.environ.get("CLAUDE_PROJECT_DIR")
        cwd_top = _cwd_toplevel()  # realpath'd git toplevel of CWD, or None
        if env_top and cwd_top and os.path.realpath(env_top) != cwd_top and plan is not None:
            main_ptr = os.path.join(os.path.realpath(env_top), ".claude", "state", "active-plan")
            with open(main_ptr, encoding="utf-8") as fh:
                main_val = fh.read().strip()
            if main_val and _normalize_plan_ref(main_val) == plan:
                reasons.append(
                    "(d) cross-checkout state bleed: the MAIN checkout's active-plan "
                    f"points to this worktree's plan ('{main_val}'). A worktree builder "
                    "never writes the main checkout's .claude/state/** (finding-0051). "
                    f"Clear it: printf '' > {main_ptr}"
                )
    except Exception:
        pass  # fail-open, fail-loud is the .sh's job; a missing/unreadable pointer never blocks

    # (e) session-handoff gate (dn-session-handoff-gate §2.2) -> orchestrator
    # posture only (no active plan; builder sessions carry one and are governed by
    # (a)). BLOCK when commits landed THIS session (HEAD moved past the SessionStart
    # baseline) but the resume brief is stale (mtime older than the last commit) or
    # absent (a missing brief is infinitely stale). Fail-open on a missing/unreadable
    # session-baseline: the signal can't be evaluated, so no block (note §2.5). The
    # block reason IS the automation — it instructs writing the brief.
    if plan is None:
        try:
            with open(
                os.path.join(ROOT, ".claude", "state", "session-baseline"),
                encoding="utf-8",
            ) as fh:
                baseline = fh.read().strip()
        except Exception:
            baseline = ""  # missing/unreadable baseline -> fail-open (skip)
        if baseline and head_sha and head_sha != baseline:
            brief_abs = os.path.join(ROOT, ".claude", "state", "resume-brief.md")
            try:
                brief_fresh = os.path.getmtime(brief_abs) >= last_commit
            except OSError:
                brief_fresh = False  # missing brief = infinitely stale
            if not brief_fresh:
                reasons.append(
                    "(e) commits landed this session but the resume brief is stale "
                    "or missing — write .claude/state/resume-brief.md (the resume-"
                    "brief shape, context-economy skill) citing the final commit "
                    "hashes, then close again (dn-session-handoff-gate)."
                )

    # (f) seal follow-through (bp-097; design-note D5) -> every posture. A plan
    # sealed to `status: complete` this session (the flip shows in the HEAD-keyed
    # `diff` above, in both builder and orchestrator posture) must carry a
    # `## Follow-through` block in its journal tail — the five questions that turn a
    # ledger-close into an honest one (checkpoint skill). Missing block -> BLOCK.
    # Grep-class (header presence), the (a)-staleness family of crude post-hoc
    # checks; the deskcheck itself is the real backstop (F-WF5 residual, §11).
    for sealed in _sealed_plans_in_diff(diff):
        if not _journal_tail_has_followthrough(journal_for(sealed)):
            reasons.append(
                f"(f) plan '{sealed}' is sealed to complete but its journal tail "
                f"lacks a '## Follow-through' block — a seal must answer the five "
                f"follow-through questions (built? / wired-or-dormant? / consumer? / "
                f"track state? / new track or finding?; checkpoint skill, D5) before "
                f"close. Add the block to the seal entry, then close again."
            )

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
        lines.append(
            "Plans: " + "; ".join(f"{st}={','.join(ids)}" for st, ids in sorted(plans.items()))
        )
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

    lines.append(
        "Duties: /graduate · /build · /resume · /triage · /scribe · /capture. "
        "Never block on the owner (§5); park + finding + continue."
    )
    print("\n".join(lines))
    return 0


def cmd_staleness() -> int:
    plan = active_plan_path()
    if plan is None:
        return 0
    j_abs = os.path.join(ROOT, journal_for(plan))
    try:
        head_ct = int(
            subprocess.run(
                ["git", "log", "-1", "--format=%ct"],
                capture_output=True,
                text=True,
                cwd=ROOT,
                check=True,
            ).stdout.strip()
            or "0"
        )
    except Exception:
        return 0
    if head_ct and os.path.exists(j_abs) and os.path.getmtime(j_abs) < head_ct:
        print(
            "⟳ journal is stale relative to HEAD — checkpoint at the next semantic boundary (§9)."
        )
    return 0


def cmd_marker(text: str) -> int:
    plan = active_plan_path()
    if plan is None:
        # Best-effort: nothing to mark without an active journal.
        return 0
    j_abs = os.path.join(ROOT, journal_for(plan))
    ts = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
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
        print(
            "usage: _lib.py <scope-check|gate-check|gate-check-hook|"
            "stop-audit|brief|staleness|marker> [args]",
            file=sys.stderr,
        )
        return 64
    cmd = argv[0]
    if cmd == "scope-check":
        return cmd_scope_check(argv[1] if len(argv) > 1 else "")
    if cmd == "scope-check-hook":
        return cmd_scope_check_hook()
    if cmd == "gate-check":
        return cmd_gate_check(argv[1] if len(argv) > 1 else "", argv[2] if len(argv) > 2 else None)
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
