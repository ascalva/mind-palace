"""Shadow-isolation firewall (bp-043 Item 7, dn-evaluation-harness §2.10) — non-skippable.

The whole-plan falsifier is the live dream surface changing. Two structural facts prove — from the
SOURCE of `core/dreaming/shadow.py` itself, without running it — that shadow cannot touch it:

* **No write path to the interpreted/derived store.** `shadow.py` must NOT import
  `core.stores.derived` at all (it drives the pipelines by running the interpreters/adjudicator
  directly and persists nothing but ledger + eval-store rows) — so a derived write is unreachable
  BY CONSTRUCTION, not merely unused.
* **Reads only a `MirrorView`.** The corpus is read ONLY through `MirrorView.project` — never a raw
  `.all_rows(` / `.search(` that could bypass the authored-only firewall (Invariant 6, #11).

Same spirit as `test_eval_isolation.py` / `test_import_firewall.py`: an AST scan is stronger than a
runtime guard — it proves no path *exists*. The negative controls prove the scanner has teeth.
"""

from __future__ import annotations

import ast
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SHADOW = REPO_ROOT / "core" / "dreaming" / "shadow.py"

# The forbidden write target: the interpreted/derived store.
_DERIVED_MODULE = "core.stores.derived"


def _imported_modules(path: Path) -> set[str]:
    """Every module imported anywhere in the file (nested/lazy imports included — ast.walk)."""
    tree = ast.parse(path.read_text(encoding="utf-8"))
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names.update(a.name for a in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            names.add(node.module)
    return names


def _attribute_calls(path: Path) -> set[str]:
    """The attribute names of every `x.attr(...)` call in the file (e.g. `project`, `all_rows`)."""
    tree = ast.parse(path.read_text(encoding="utf-8"))
    calls: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            calls.add(node.func.attr)
    return calls


def test_shadow_never_imports_the_derived_store() -> None:
    """No write path to the interpreted/derived store: `shadow.py` does not import it at all, so a
    derived write is unrepresentable (the whole-plan falsifier can't be tripped by construction)."""
    imports = _imported_modules(SHADOW)
    derived = {m for m in imports if m == _DERIVED_MODULE or m.startswith(_DERIVED_MODULE + ".")}
    assert derived == set(), f"shadow.py imports the derived store: {sorted(derived)}"


def test_shadow_reads_the_corpus_only_through_a_mirror_view() -> None:
    """The corpus read is `MirrorView.project` ONLY — no raw provenance-bypassing read."""
    imports = _imported_modules(SHADOW)
    assert "core.mirror" in imports, "shadow.py must read the corpus via core.mirror.MirrorView"
    calls = _attribute_calls(SHADOW)
    assert "project" in calls, "shadow.py must project a MirrorView (the sanctioned read)"
    # A raw store scan that bypasses the mirror firewall must not appear in shadow's own source.
    assert "all_rows" not in calls, "shadow.py bypasses MirrorView via a raw .all_rows() read"
    assert "search" not in calls, "shadow.py bypasses MirrorView via a raw .search() read"


def test_scanner_would_catch_a_derived_import() -> None:
    """Negative control: the import scan actually detects a derived-store import when one exists (a
    green result above means isolation, not a broken scanner)."""
    dreamer = REPO_ROOT / "core" / "dreaming" / "dreamer.py"
    imports = _imported_modules(dreamer)
    assert any(m == _DERIVED_MODULE or m.startswith(_DERIVED_MODULE + ".") for m in imports), \
        "dreamer.py DOES import the derived store — the scanner should see it"


def test_scanner_would_catch_a_raw_all_rows_read() -> None:
    """Negative control: the call scan detects a raw `.all_rows(` read where one exists (the mirror
    itself calls it — so `all_rows not in shadow` above is a real fact, not a dead check)."""
    mirror = REPO_ROOT / "core" / "mirror.py"
    assert "all_rows" in _attribute_calls(mirror)


def test_shadow_job_is_background_and_foreground_gated_like_dream(tmp_path) -> None:
    """The trough job (Item 7): `enqueue_shadow` lands at BACKGROUND priority on the synthesis tier,
    so the supervisor's HEAVY_TIERS foreground gate keeps it out of the owner's time exactly like
    `dream` (never foreground — the falsifier)."""
    from config.loader import load_config
    from scheduler.cron import DREAM_KIND, SHADOW_KIND, enqueue_dream, enqueue_shadow
    from scheduler.queue import PRIORITY_BACKGROUND, JobQueue
    from scheduler.router import Router
    from scheduler.supervisor import HEAVY_TIERS

    router = Router(load_config())
    queue = JobQueue(tmp_path / "q.db")

    shadow_job = enqueue_shadow(queue, router)
    dream_job = enqueue_dream(queue, router)

    assert shadow_job.kind == SHADOW_KIND and dream_job.kind == DREAM_KIND
    # same tier + same priority as dream -> same foreground gate, same trough discipline.
    assert shadow_job.tier == dream_job.tier == "synthesis"
    assert shadow_job.tier in HEAVY_TIERS, "shadow must be foreground-gated (HEAVY_TIERS)"
    assert shadow_job.priority == dream_job.priority == PRIORITY_BACKGROUND
