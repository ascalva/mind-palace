"""Parse a Logseq markdown vault into the explicit (authored) layer (BUILD-SPEC §8).

Logseq is the owner's hand-made skeleton: page text, the tags they applied, the [[links]]
they drew. We extract those as ground truth and seed the thought-graph from them rather
than imposing an ontology up front. Interpreted edges (similarity, inferred themes) are a
separate, derived layer added later.
"""

from __future__ import annotations

import re
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path

_LINK = re.compile(r"\[\[([^\]]+)\]\]")
_TAG_BRACKET = re.compile(r"#\[\[([^\]]+)\]\]")
_TAG_PLAIN = re.compile(r"(?<!\w)#([A-Za-z0-9_][\w/-]*)")
_PROP = re.compile(r"^([A-Za-z0-9_-]+)::\s?(.*)$", re.MULTILINE)

DEFAULT_PATTERN = "**/*.md"
# Logseq/editor housekeeping dirs that are not authored content (the §20.8 scoping knob
# narrows further by pattern or by pointing the vault root at a subgraph).
DEFAULT_EXCLUDE_DIRS: frozenset[str] = frozenset({".git", "bak", ".recycle", "assets", ".obsidian"})


@dataclass(frozen=True)
class ParsedNote:
    source_path: str
    title: str
    text: str
    tags: frozenset[str]
    links: frozenset[str]
    properties: dict[str, str]
    raw_bytes: bytes = b""  # verbatim original; the raw store is content-addressed on this


def _title_from_path(path: Path, vault: Path) -> str:
    rel = path.relative_to(vault).with_suffix("")
    # Logseq encodes namespace '/' as '___' in filenames.
    return str(rel).replace("___", "/")


def _decode(data: bytes) -> str:
    """Tolerant decode for the DERIVED text layer. Real-world notes (especially exports)
    are not always UTF-8 (e.g. cp1252 smart quotes). The raw store keeps the verbatim
    ORIGINAL bytes (§8); only this regenerable text view is normalized."""
    for enc in ("utf-8", "cp1252"):
        try:
            return data.decode(enc)
        except UnicodeDecodeError:
            continue
    return data.decode("utf-8", errors="replace")


def parse_text(text: str, *, source_path: str, title: str, raw_bytes: bytes) -> ParsedNote:
    """Parse an in-memory note (tags, links, properties) — the path-free core of `parse_note`.

    Used by programmatic ingest that builds note text directly rather than reading a vault file
    (the founding-corpus driver, and anywhere else authored text is composed in memory), so those
    paths get the SAME tag/link/property extraction as vault ingest — no bespoke parser."""
    tags = set(_TAG_BRACKET.findall(text)) | set(_TAG_PLAIN.findall(text))
    links = set(_LINK.findall(text))  # note: #[[x]] is also a [[x]] link — intentional
    props = {k: v.strip() for k, v in _PROP.findall(text)}
    return ParsedNote(source_path=source_path, title=title, text=text, tags=frozenset(tags),
                      links=frozenset(links), properties=props, raw_bytes=raw_bytes)


def parse_note(path: Path, vault: Path) -> ParsedNote:
    data = path.read_bytes()
    return parse_text(_decode(data), source_path=str(path),
                      title=_title_from_path(path, vault), raw_bytes=data)


def iter_vault(vault: Path, *, pattern: str = DEFAULT_PATTERN,
               exclude_dirs: frozenset[str] = DEFAULT_EXCLUDE_DIRS) -> Iterator[Path]:
    """Yield in-scope markdown files, deterministically ordered. `pattern` and
    `exclude_dirs` are the §20.8 sub-scoping knob (which graphs are ingested)."""
    for p in sorted(vault.glob(pattern)):
        if not p.is_file():
            continue
        if exclude_dirs & set(p.relative_to(vault).parts):
            continue
        yield p
