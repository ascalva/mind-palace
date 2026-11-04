"""The artifact front-matter parser the repo's derived views share (`board.py`, `docket.py`,
`handoff.py`): a deliberately small reader of the `---` block — scalars, inline and block lists,
quoted values with trailing comments stripped — so no second YAML parser enters the tree.

Moved here from the retired `.claude/hooks/_lib.py` on 2026-11-04, when the owner retired the
agent-workflow controls; the parser outlived the hooks because the derived board still reads
every artifact's front matter through it.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any


def parse_front_matter(text: str) -> dict[str, Any]:
    """The front-matter block of `text` as a dict: `key: scalar`, `key: [a, b]`, or a block list
    under a bare `key:`; comments and blank lines skipped. `{}` when there is no block."""
    if not text.startswith("---"):
        return {}
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}
    body: list[str] = []
    for ln in lines[1:]:
        if ln.strip() == "---":
            break
        body.append(ln)
    out: dict[str, Any] = {}
    key: str | None = None
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
            if v == "":
                out[key] = ""  # value may be a block list on following lines
            elif v.startswith("[") and v.endswith("]"):
                inner = v[1:-1].strip()
                out[key] = [_scalar(x.strip()) for x in inner.split(",") if x.strip()]
            else:
                out[key] = _scalar(v)
    return out


def _scalar(v: str) -> str:
    """A scalar: a quoted value honours its closing quote and drops a trailing inline comment
    (`"path"  # note`); an unquoted one keeps its `#`, so a plain value is never truncated."""
    v = v.strip()
    if len(v) >= 2 and v[0] in "\"'":
        q = v[0]
        end = v.find(q, 1)
        if end != -1:
            return v[1:end]
        return v[1:]  # unterminated quote — best-effort strip of the leading quote
    return v


def _normalize_status(v: Any) -> Any:
    """Strip a trailing YAML comment (` #…`) from a status value; a `#` with no preceding space
    is not a comment and is left intact, so a malformed status never normalizes into another."""
    if not isinstance(v, str):
        return v
    i = v.find(" #")
    if i != -1:
        v = v[:i]
    return v.rstrip()


def read_front_matter(path: str | Path) -> dict[str, Any]:
    """The front matter of the file at `path`, or `{}` when it cannot be read."""
    try:
        return parse_front_matter(Path(path).read_text(encoding="utf-8"))
    except Exception:
        return {}
