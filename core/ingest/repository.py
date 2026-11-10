"""A git repository read as a source: the files of a ref's tree, through git's object store
(dn-palace-lite).

A repository source's items are the regular files of the tree a ref names, read as blobs, never
through the working tree: so no untracked file, uncommitted edit, data directory or symlink target
beside the repository is ever read, and the files are exactly the commit's whatever the file
system's case rules. Three git commands, each a plumbing read: `rev-parse` resolves the ref to its
commit, `ls-tree` lists the tree, and one `cat-file --batch` process reads the blobs. None of them
touches the network, and git is told so (`GIT_NO_LAZY_FETCH`, `protocol.allow=never`), so a partial
clone's missing blob is an error here, never a fetch.

The foundation's paths (the constitution, the golden set) are never items, as `read` never opens
them (`core.sentence.types.is_foundation`), nor are the tool directories; a blob holding a NUL byte
is not text and is not an item.
"""

from __future__ import annotations

import os
import re
import subprocess
from collections.abc import Iterator, Sequence
from dataclasses import dataclass
from pathlib import Path

from core.sentence.types import is_foundation

_TOOL_DIRS = (".git/", ".jj/", ".claude/")
_SHA = re.compile(r"[0-9a-f]{40}|[0-9a-f]{64}")
_REGULAR = (b"100644", b"100755")


class RepositoryError(RuntimeError):
    """The repository, its ref or one of its blobs could not be read."""


@dataclass(frozen=True)
class Entry:
    """One regular file of a tree: its path in the repository, its blob and the blob's size."""

    path: str
    blob: str
    size: int


def _env() -> dict[str, str]:
    env = dict(os.environ)
    env.update({"GIT_NO_LAZY_FETCH": "1", "GIT_TERMINAL_PROMPT": "0", "GIT_OPTIONAL_LOCKS": "0"})
    return env


def _git(location: Path, *args: str, stdin: bytes | None = None) -> bytes:
    try:
        done = subprocess.run(["git", "-c", "protocol.allow=never", "-C", str(location), *args],
                              input=stdin, capture_output=True, env=_env(), timeout=300)
    except (OSError, subprocess.TimeoutExpired) as e:
        raise RepositoryError(f"git {args[0]} in {location}: {e}") from None
    if done.returncode != 0:
        raise RepositoryError(f"git {args[0]} in {location}: "
                              f"{done.stderr.decode('utf-8', 'replace').strip()[-300:]}")
    return done.stdout


def commit_of(location: Path, ref: str) -> str:
    """The commit a ref names in the repository."""
    if ref.startswith("-"):
        raise RepositoryError(f"{ref!r} is not a ref")
    return _git(location, "rev-parse", "--verify", "--quiet", "--end-of-options",
                f"{ref}^{{commit}}").decode().strip()


def itemizable(path: str) -> bool:
    """Whether a path of the tree may be an item: not the foundation's, not a tool directory's."""
    folded = path.casefold()
    return not is_foundation(path) and not folded.startswith(_TOOL_DIRS)


def tree(location: Path, commit: str) -> list[Entry]:
    """The regular files of the commit's tree that may be items, in path order: a symlink, a
    submodule, the foundation's paths and the tool directories are left out."""
    out = []
    for record in _git(location, "ls-tree", "-r", "-l", "-z", "--full-tree", commit).split(b"\0"):
        if not record:
            continue
        meta, _, name = record.partition(b"\t")
        fields = meta.split()
        if len(fields) != 4 or fields[1] != b"blob" or fields[0] not in _REGULAR:
            continue
        path = name.decode("utf-8", "surrogateescape")
        if itemizable(path):
            out.append(Entry(path, fields[2].decode(), int(fields[3])))
    return sorted(out, key=lambda e: e.path)


def read_blobs(location: Path, blobs: Sequence[str]) -> Iterator[tuple[str, bytes]]:
    """Each blob's bytes, in the order asked, read by one `cat-file --batch` process."""
    if not blobs:
        return
    data = _git(location, "cat-file", "--batch", stdin=("\n".join(blobs) + "\n").encode())
    at = 0
    for blob in blobs:
        end = data.index(b"\n", at)
        header = data[at:end].split()
        if len(header) != 3 or header[1] != b"blob":
            raise RepositoryError(f"blob {blob} is missing from {location}")
        size = int(header[2])
        yield blob, data[end + 1:end + 1 + size]
        at = end + 1 + size + 1                  # the content, then the batch's own newline


def is_text(data: bytes) -> bool:
    """Whether a blob is text: it holds no NUL byte."""
    return b"\0" not in data


def behind(location: Path, landed: str, ref: str) -> int | None:
    """How many commits the ref has that the landed commit has not (None when either is
    unknown to the repository, or the landed commit is not a commit's name): how stale a
    repository source is."""
    if not _SHA.fullmatch(landed):
        return None
    try:
        out = _git(location, "rev-list", "--count", f"{landed}..{commit_of(location, ref)}")
    except RepositoryError:
        return None
    return int(out.decode().strip() or 0)
