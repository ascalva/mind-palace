"""Curate a reference manifest: flip DISTILLED → EMBEDDED, and guard the dangling claim (Item 30).

After the persist step (Item 29) embeds a keeper's open-access full text into the curated store,
its `docs/reference_material/<slug>/manifest.md` records the transition: `source_ingestion.state:
embedded` with the `store_ref` join to `data/` (the v0 schema, `reference_material/README.md`).

Two mechanisms, both deliberately format-respecting (the repo has NO YAML dependency — manifests
are hand-authored markdown with inline comments, so a naive YAML round-trip would strip them):

  * `set_embedded(text, ...)` rewrites ONLY the `source_ingestion:` block, leaving every other
    block (and its comments) byte-identical — the minimal edit a curation-time flip needs.
  * `ingestion_errors(...)` is the **dangling-claim guard** — the Item-30 falsifier as a check: a
    manifest may not read `embedded` without a non-null `store_ref`/`venue`/`retrieved`, and (given
    the store) without curated vectors actually present for that `store_ref`. A pointer that
    promises full text the store does not hold is exactly the "verify before trust" failure the
    whole arc guards against.

This module writes/validates manifest TEXT; the real DISTILLED→EMBEDDED flip of a live keeper rides
a live driver run (there is no core-side fetch — Inv 2), so it is a curation-time act, not a
build-time one (bp-029 journal; the offline build delivers the mechanism + guard, tested).
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from core.research.persist import CuratedRecord
from core.stores.vectorstore import VectorStore

_VALID_STATE = frozenset({"not_fetched", "fetched", "embedded"})
_REQUIRED_TOP = frozenset({
    "type", "id", "citation", "identifiers", "verification",
    "source_ingestion", "authority", "provenance",
})


def _scalar(v: str) -> Any:
    """Convert a raw YAML scalar to a Python value (null/bool/int/quoted-string/plain)."""
    v = v.strip()
    if not v:
        return None
    if v[0] in "\"'":                       # quoted: read to the closing quote (comment-safe)
        q = v[0]
        end = v.find(q, 1)
        return v[1:end] if end != -1 else v[1:]
    # unquoted: a ' #' begins a YAML comment; a bare '#' inside the value is kept
    hp = v.find(" #")
    if hp != -1:
        v = v[:hp].strip()
    low = v.lower()
    if low in ("null", "~", ""):
        return None
    if low == "true":
        return True
    if low == "false":
        return False
    if v.lstrip("-").isdigit():
        return int(v)
    return v


def _frontmatter_lines(text: str) -> list[str]:
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        raise ValueError("manifest has no '---' front matter")
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            return lines[1:i]
    raise ValueError("manifest front matter is not terminated by '---'")


def parse_frontmatter(text: str) -> dict[str, Any]:
    """Parse a reference manifest's front matter (one level of nesting: dicts + lists).

    Enough for the v0 schema — top-level scalars, the nested `verification`/`identifiers`/
    `source_ingestion` mappings, and the `load_bearing_for`/`cited_by`/`docs` lists. No external
    YAML dependency (the repo hand-parses front matter everywhere)."""
    out: dict[str, Any] = {}
    parent: str | None = None
    for ln in _frontmatter_lines(text):
        if not ln.strip() or ln.lstrip().startswith("#"):
            continue
        indented = ln.startswith(" ")
        s = ln.strip()
        if indented and parent is not None:
            if s.startswith("- "):
                cur = out.get(parent)
                if not isinstance(cur, list):
                    cur = out[parent] = []
                cur.append(_scalar(s[2:]))
            elif ":" in s:
                cur = out.get(parent)
                if not isinstance(cur, dict):
                    cur = out[parent] = {}
                k, _, v = s.partition(":")
                cur[k.strip()] = _scalar(v)
            continue
        if ":" in s:                        # a top-level key
            k, _, v = s.partition(":")
            parent = k.strip()
            v = v.strip()
            if v == "":
                out[parent] = ""            # may become a dict or list on following lines
            else:
                out[parent] = _scalar(v)
                parent = None               # a scalar top-level key has no children
    return out


def set_embedded(text: str, *, venue: str, store_ref: str, retrieved: str) -> str:
    """Return `text` with its `source_ingestion:` block rewritten to the EMBEDDED state.

    Only that block changes; every other line (and comment) is preserved. Idempotent in shape."""
    lines = text.splitlines()
    start = next((i for i, ln in enumerate(lines)
                  if ln.startswith("source_ingestion:")), None)
    if start is None:
        raise ValueError("manifest has no 'source_ingestion:' block")
    end = start + 1
    while end < len(lines) and lines[end][:1] in (" ", "\t"):  # consume the indented children
        end += 1
    block = [
        "source_ingestion:",
        "  state: embedded",
        f"  venue: {venue}",
        f"  store_ref: {store_ref}",
        f"  retrieved: {retrieved}",
    ]
    new = lines[:start] + block + lines[end:]
    return "\n".join(new) + ("\n" if text.endswith("\n") else "")


def mark_manifest_embedded(path: Path, record: CuratedRecord, *, retrieved: str) -> None:
    """Flip a manifest file DISTILLED → EMBEDDED from a persist `CuratedRecord` (venue + store_ref).

    Refuses to write a dangling claim: validates the result against the store the record was
    persisted into is the caller's responsibility (`ingestion_errors`); here we only guarantee the
    written block carries the record's real `store_ref`."""
    text = path.read_text(encoding="utf-8")
    path.write_text(
        set_embedded(text, venue=record.paper_source, store_ref=record.store_ref,
                     retrieved=retrieved),
        encoding="utf-8",
    )


def schema_errors(fm: dict[str, Any]) -> list[str]:
    """Validate a parsed manifest against the v0 schema (required keys + enum values)."""
    errs = [f"missing required key: {k}" for k in _REQUIRED_TOP if k not in fm]
    if fm.get("type") != "reference-material":
        errs.append(f"type must be 'reference-material', got {fm.get('type')!r}")
    si = fm.get("source_ingestion")
    if not isinstance(si, dict):
        errs.append("source_ingestion must be a mapping")
    elif si.get("state") not in _VALID_STATE:
        errs.append(f"source_ingestion.state invalid: {si.get('state')!r}")
    return errs


def ingestion_errors(fm: dict[str, Any], *, curated_store: VectorStore | None = None) -> list[str]:
    """The dangling-claim guard (Item-30 falsifier): an `embedded` manifest must be backed by a
    real `store_ref`/`venue`/`retrieved` and, when the store is given, by curated vectors that
    actually exist for that `store_ref`. A `not_fetched` manifest must carry no `store_ref`."""
    si = fm.get("source_ingestion")
    if not isinstance(si, dict):
        return ["source_ingestion missing or not a mapping"]
    state, ref = si.get("state"), si.get("store_ref")
    errs: list[str] = []
    if state == "embedded":
        if not ref:
            errs.append("state=embedded but store_ref is null (dangling claim)")
        if not si.get("venue"):
            errs.append("state=embedded but venue is null")
        if not si.get("retrieved"):
            errs.append("state=embedded but retrieved is null")
        if curated_store is not None and ref:
            if not any(r.get("digest") == ref for r in curated_store.all_rows()):
                errs.append(f"state=embedded but no curated vectors for store_ref {ref!r}")
    elif state == "not_fetched" and ref:
        errs.append("state=not_fetched but store_ref is set")
    return errs
