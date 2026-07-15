"""The §2.6 repo-grep differential oracle over the LIVE reference store (bp-035 Item 3).

The self-grading loop (dn-core-query-protocol §2.6): query the reference graph, check it against
an INDEPENDENT repo-grep oracle at HEAD, score the sensor's fidelity. Because reference lookup is
deterministic, the judge has free, correct ground truth — a differential test against an oracle,
stronger than any LLM-judge.

The three load-bearing disciplines (§2.6), honored here:
  1. **The oracle is repo-grep, NOT the store** — else it is circular. The ground-truth citations
     come ONLY from grepping the doc files (the regexes below are reimplemented here, deliberately
     NOT imported from `ops/code_sensor`). The store is queried ONLY through the built
     `ReferenceView` (`references_from`), never for ground truth. This measures whether the STORED
     graph matches repo reality — turning finding-0059/0061's staleness anxiety into a monitored
     number.
  2. **Golden-set firewall** — this reads the LIVE reference store + greps the repo; it never
     touches `eval/golden/**` (Constitution §9).
  3. The printed number is the φ_ref sensor-fidelity datum (recording it as an observation stream
     is future — plan §11).

**Floor, not equality (the §7 Item 3 falsifier).** The sensor is precision-gated: it mints
doc→doc edges from full `docs/….md` paths + validated front-matter/wikilink patterns, NOT from
every bare `finding-NNNN`/`dn-slug` prose mention. So the expanded-surface recall is EXPECTED
below the full-path-surface recall — asserting exact equality would mistake precision-gating for
a bug. The floor is set well below the first measured run.

**Reconciliation datum.** The note's hand-run demo (§2.6) reported doc→doc recall **0/16 = 0.000**
at the 61k-edge snapshot. With ~75k corpus_to_corpus edges now minted (the extractor shipped via
`ops/code_sensor.py` post-note-snapshot — the owed spec-fidelity erratum, plan §4), the first
measured run here (worktree HEAD `5168b42`, 994 edges at anchor) is **227/228 = 0.996** on the
full-path surface. The test PRINTS the live number every run.
"""

from __future__ import annotations

import re
import subprocess

import pytest

from config.loader import REPO_ROOT, get_config
from core.reference_view import open_reference_view
from core.stores.reference_edges import open_reference_edge_store

# ── INDEPENDENT grep surfaces (reimplemented here — §2.6 discipline 1; not imported from the
#    extractor). Full `docs/….md` citation paths, backtick `*.py` mentions, and the bare
#    `finding-NNNN`/`dn-slug` prose forms the plan names. ──────────────────────────────────────
_RE_DOC = re.compile(r"docs/(?:design-notes|findings|brainstorms)/[\w.\-]+\.md")
_RE_PY = re.compile(r"`([\w./\-]+\.py)(?::\d+)?`")
_RE_FINDING = re.compile(r"\bfinding-(\d{4})\b")
_RE_DN = re.compile(r"\bdn-([\w\-]+)\b")

_DOC_DIRS = ("design-notes", "findings", "brainstorms")

# The asserted floor is on the clean full-path doc→doc recall. First measured run: 0.996.
# Floored well below (NOT equality — precision-gating, §7 Item 3 falsifier) so a slightly
# different projected commit still passes; if recall crashes toward zero the sensor is broken
# (plan §10 stop-and-raise → a codebase finding, not a lowered floor).
_DOC_RECALL_FLOOR = 0.90
_PY_RECALL_FLOOR = 0.90
_PRECISION_FLOOR = 0.85


def _head_sha() -> str:
    return subprocess.run(["git", "-C", str(REPO_ROOT), "rev-parse", "HEAD"],  # noqa: S607
                          capture_output=True, text=True, check=True).stdout.strip()


def _dn_id_map() -> dict[str, str]:
    """`dn-<id>` → its repo-relative path, from each design note's front-matter `id:` — so a bare
    `dn-slug` prose mention resolves to the same `target_ref` the store would key."""
    out: dict[str, str] = {}
    for f in sorted((REPO_ROOT / "docs" / "design-notes").glob("*.md")):
        m = re.search(r"^id:\s*(dn-[\w\-]+)", f.read_text(encoding="utf-8", errors="replace"), re.M)
        if m:
            out[m.group(1)] = str(f.relative_to(REPO_ROOT))
    return out


def _grep_citations(text: str, self_rel: str,
                    dn_map: dict[str, str]) -> tuple[set[str], set[str], set[str]]:
    """The INDEPENDENT oracle — a doc's outbound citations by repo-grep alone (never the store).
    Returns `(path_docs, expanded_docs, py_paths)`: the clean full-path doc surface, that surface
    PLUS resolved bare `finding-`/`dn-` prose mentions, and backtick `.py` mentions. Every target
    is filtered to a path that actually exists in the repo, and self-references are dropped."""
    path_docs = {m.group(0) for m in _RE_DOC.finditer(text)}
    py_paths = {m.group(1) for m in _RE_PY.finditer(text)}
    expanded = set(path_docs)
    for m in _RE_FINDING.finditer(text):
        p = f"docs/findings/finding-{m.group(1)}.md"
        if (REPO_ROOT / p).exists():
            expanded.add(p)
    for m in _RE_DN.finditer(text):
        key = "dn-" + m.group(1)
        if key in dn_map:
            expanded.add(dn_map[key])
    for s in (path_docs, expanded, py_paths):
        s.discard(self_rel)
    path_docs = {t for t in path_docs if (REPO_ROOT / t).exists()}
    expanded = {t for t in expanded if (REPO_ROOT / t).exists()}
    return path_docs, expanded, py_paths


def test_reference_store_fidelity_against_repo_grep_oracle() -> None:
    head = _head_sha()

    # Skip guard: the comparison is grep-at-HEAD vs store-at-HEAD, so the store must be projected
    # at HEAD or the mismatch is pure commit-skew, not sensor fidelity. A fresh git worktree has
    # no projected store (it lives in the running system's data dir) → environmental skip. In the
    # main checkout (where the daemon projects), the store exists at HEAD and this MEASURES.
    probe = open_reference_edge_store(get_config())
    try:
        edges_at_head = len(probe.for_commit(head))
    finally:
        probe.close()
    if edges_at_head == 0:
        pytest.skip(f"no reference store projected at HEAD {head[:12]} in this checkout "
                    "(environmental — the projected store lives in the running system's data dir)")

    view = open_reference_view(commit=head)
    dn_map = _dn_id_map()
    md_files = sorted(p for p in (REPO_ROOT / "docs").rglob("*.md")
                      if any(seg in p.parts for seg in _DOC_DIRS))

    doc_hit = doc_tot = 0        # recall: full-path grepped doc citations found in the store
    exp_hit = exp_tot = 0        # recall over the expanded (bare finding-/dn- prose) surface
    py_hit = py_tot = 0          # recall: grepped `.py` mentions found in the store
    prec_hit = prec_tot = 0      # precision: stored doc→doc edges an independent grep corroborates
    docs_with_citations = 0
    worst: list[tuple[int, int, str]] = []

    for f in md_files:
        rel = str(f.relative_to(REPO_ROOT))
        text = f.read_text(encoding="utf-8", errors="replace")
        grep_docs, grep_expanded, grep_py = _grep_citations(text, rel, dn_map)

        # The STORE's answer comes from the built VIEW — exercising the Item 1 surface, not raw SQL.
        from_edges = view.references_from(rel)
        stored_docs = {e.target_ref for e in from_edges if e.target_kind == "corpus"}
        stored_py = {e.target_ref for e in from_edges if e.target_kind == "code"}

        if grep_docs:
            docs_with_citations += 1
            hit = len(grep_docs & stored_docs)
            doc_hit += hit
            doc_tot += len(grep_docs)
            if hit < len(grep_docs):
                worst.append((hit, len(grep_docs), rel))
        if grep_expanded:
            exp_hit += len(grep_expanded & stored_docs)
            exp_tot += len(grep_expanded)
        if grep_py:
            py_hit += len(grep_py & stored_py)
            py_tot += len(grep_py)
        if stored_docs:
            prec_hit += len(stored_docs & grep_expanded)
            prec_tot += len(stored_docs)

    doc_recall = doc_hit / max(doc_tot, 1)
    exp_recall = exp_hit / max(exp_tot, 1)
    py_recall = py_hit / max(py_tot, 1)
    precision = prec_hit / max(prec_tot, 1)

    # PRINT the φ_ref fidelity number (plan §7 Item 3; visible with `pytest -s`/`-rP`).
    print("\n=== reference sensor fidelity — grep-oracle vs live store @ HEAD ===")
    print(f"anchor commit: {head[:12]}   edges@anchor: {edges_at_head}   "
          f"docs with citations: {docs_with_citations}")
    print(f"doc->doc recall  (full-path surface):   {doc_hit}/{doc_tot} = {doc_recall:.3f}")
    print(f"doc->doc recall  (expanded +bare ids):  {exp_hit}/{exp_tot} = {exp_recall:.3f}")
    print(f"doc->doc precision (grep-confirmable):  {prec_hit}/{prec_tot} = {precision:.3f}")
    print(f"doc->code(.py) recall:                  {py_hit}/{py_tot} = {py_recall:.3f}")
    print(f"note's stale demo: doc->doc 0/16 = 0.000  ->  now {doc_recall:.3f} (full-path surface)")
    if worst:
        print("full-path recall gaps (hit/total  doc):")
        for hit, tot, rel in sorted(worst)[:8]:
            print(f"  {hit}/{tot}  {rel}")

    # --- assertions: FLOORS, never equality (the §7 Item 3 falsifier) -------------------------
    assert docs_with_citations >= 10, (
        f"expected a meaningful doc sample; only {docs_with_citations} docs had grepped citations")
    assert doc_recall >= _DOC_RECALL_FLOOR, (
        f"doc->doc full-path recall {doc_recall:.3f} ({doc_hit}/{doc_tot}) below floor "
        f"{_DOC_RECALL_FLOOR} — the sensor may be broken (finding-0059/0061); plan §10 "
        "stop-and-raise says file a codebase finding, do NOT lower the floor to force green")
    assert py_recall >= _PY_RECALL_FLOOR, (
        f"doc->code(.py) recall {py_recall:.3f} ({py_hit}/{py_tot}) below floor {_PY_RECALL_FLOOR}")
    assert precision >= _PRECISION_FLOOR, (
        f"doc->doc precision {precision:.3f} ({prec_hit}/{prec_tot}) below floor "
        f"{_PRECISION_FLOOR} — the sensor may be over-minting edges with no independent grep")
    # The expanded surface is EXPECTED below the full-path surface (precision-gating on bare-id
    # prose) — assert only that it is night-and-day above the note's 0.000 baseline, NOT equal to
    # the full-path recall (asserting equality would mistake precision-gating for a bug).
    assert exp_recall > 0.5, (
        f"expanded-surface recall {exp_recall:.3f} — even with precision-gating this should be far "
        "above the note's 0.000 baseline")
    assert doc_recall > exp_recall or doc_tot == exp_tot  # precision-gating: full-path ⊇ recall
