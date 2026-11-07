"""The console script's verb table is `bin/mind-palace`'s (packaging): same verbs, same usage."""

from __future__ import annotations

import re
from pathlib import Path

CHECKOUT = next(p for p in Path(__file__).resolve().parents if (p / "pyproject.toml").exists())


def test_the_console_script_verbs_match_the_shell_front_door() -> None:
    from scripts import cli
    sh = (CHECKOUT / "bin" / "mind-palace").read_text()
    body = sh.split('case "$verb" in', 1)[1]
    shell_verbs = set()
    for line in body.splitlines():
        m = re.match(r"\s{2}([a-z|-]+(?:\|[a-z-]+)*)\)", line)
        if m:
            shell_verbs |= set(m.group(1).split("|"))
    shell_verbs -= {"help", "-h", "--help", ""}
    assert shell_verbs == set(cli.PY_VERBS) | set(cli.SH_VERBS)
    usage = (CHECKOUT / "bin" / "mind-palace").read_text().split("<<'EOF'\n", 1)[1]
    assert cli.USAGE.rstrip("\n") == usage.split("\nEOF\n", 1)[0].rstrip("\n")
