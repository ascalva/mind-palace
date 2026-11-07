"""What the ingress trusts of a file and of a directory: one place for the checks the spools, the
inbox's record and the handoff files of the sources that may yield the owner's words all make
(dn-ingress §5, dn-ingress-language §E2, §E13).

A directory is trusted when it is a real directory (a symlink is never followed), owned by the
daemon's own account and writable by no other account (by its group only where the caller says the
group writes). A file is read through a descriptor that follows no link and blocks on nothing, as
a regular file under a cap; the caller judges its owner, mode and links from the descriptor's own
`stat`, so a file swapped after the check is never the one read.
"""

from __future__ import annotations

import os
import stat
from pathlib import Path


def daemon_uid() -> int:
    """The daemon's account: the process's own. One function, so a test can stand another
    account's ownership in for the daemon's."""
    return os.getuid()


def check_dir(d: Path, *, group_writes: bool = False) -> str | None:
    """Why `d` is not trusted, or `None`: a real directory (a symlink is not one), owned by the
    daemon's own account, writable by no other, and by the group only where the group writes."""
    try:
        st = os.lstat(d)
    except OSError as e:
        return f"{d}: {type(e).__name__}"
    if not stat.S_ISDIR(st.st_mode):
        return f"{d} is not a directory (a symlink is never followed)"
    if st.st_uid != daemon_uid():
        return f"{d} is owned by uid {st.st_uid}, not the daemon's {daemon_uid()}"
    if st.st_mode & stat.S_IWOTH or (st.st_mode & stat.S_IWGRP and not group_writes):
        return f"{d} is writable by {'others' if st.st_mode & stat.S_IWOTH else 'its group'}"
    return None


def real_dir(d: Path) -> bool:
    """Whether `d` is a directory itself, not a link to one."""
    try:
        return stat.S_ISDIR(os.lstat(d).st_mode)
    except OSError:
        return False


def read_bounded(path: Path, cap: int) -> tuple[bytes, os.stat_result]:
    """A file's bytes through a descriptor that follows no link and blocks on nothing: a regular
    file under `cap` bytes, read to at most `cap + 1`. Raises on anything else."""
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    try:
        st = os.fstat(fd)
        if not stat.S_ISREG(st.st_mode):
            raise ValueError("not a regular file")
        if st.st_size > cap:
            raise ValueError(f"{st.st_size} bytes, over the cap of {cap}")
        chunks, n = [], 0
        while n <= cap:
            chunk = os.read(fd, cap + 1 - n)
            if not chunk:
                break
            chunks.append(chunk)
            n += len(chunk)
        data = b"".join(chunks)
        if len(data) > cap:
            raise ValueError(f"grew past the cap of {cap} while read")
        return data, st
    finally:
        os.close(fd)


def written_by_one(st: os.stat_result) -> str | None:
    """Why a file, by its descriptor's `stat`, is not the daemon's own, or `None`: one link (a
    writer keeping a second name could change it after the check), owned by the daemon's account,
    writable by no other."""
    if st.st_nlink != 1:
        return f"{st.st_nlink} links; the file has one"
    if st.st_uid != daemon_uid():
        return f"owned by uid {st.st_uid}, not the daemon's {daemon_uid()}"
    if st.st_mode & (stat.S_IWGRP | stat.S_IWOTH):
        return "writable by another account"
    return None
