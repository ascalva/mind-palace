"""The corpus's relations as columnar edges (dn-corpus-instance §4.3, §6): per source and per
kind, sorted triples of int32 (source item, target item, the day the edge appears), and the
explicit bridges between sources.

    relation    source          edge                                        its day
    hyperlink   Wikipedia       an article links to an article              the later creation
    citation    OpenAlex        a work references a work                    the citing work's
    answer      Stack Exchange  an answer answers its question              the answer's
    link        Stack Exchange  a post links a post (duplicate, related)    the later post's
    version     arXiv, SE       a version follows the one before            the later version's
    (none)      Gutenberg       no dated relation between books

Both ends of an edge are items of the corpus (`Corpus.gid`), so an edge to a page, a work or a post
outside the sample is dropped. A version edge joins two versions of one item, so its nodes are
(item, version) pairs numbered on their own. The bridges cross sources: a Wikipedia citation to
an OpenAlex work (by DOI) or an arXiv record (by arXiv id), a Wikipedia Gutenberg template to a
book, a Stack Exchange link to a Wikipedia article, an arXiv record or a DOI, and the OpenAlex
and arXiv twins (one paper in both: an OpenAlex location or DOI naming the arXiv id, or the
same DOI). `save` writes each relation as `<name>.npy` (an (m, 3) int32 array), so its bytes per
edge are measured, not assumed.
"""

from __future__ import annotations

import re
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import numpy.typing as npt

from eval.corpus.data import Corpus, day

IntArr = npt.NDArray[np.int64]


@dataclass(frozen=True)
class Relation:
    """Directed, dated edges: `src -> dst` appears on day `t`."""

    name: str
    source: str            # the source whose items it joins ("bridge" for cross-source)
    src: IntArr
    dst: IntArr
    t: IntArr

    @property
    def m(self) -> int:
        return len(self.src)

    def triples(self) -> npt.NDArray[np.int32]:
        order = np.lexsort((self.dst, self.src, self.t))
        return np.stack([self.src[order], self.dst[order], self.t[order]], axis=1).astype(np.int32)


def _rel(name: str, source: str, pairs: list[tuple[int, int, int]]) -> Relation:
    if not pairs:
        z = np.zeros(0, dtype=np.int64)
        return Relation(name, source, z, z, z)
    arr = np.asarray(sorted(set(pairs)), dtype=np.int64)
    keep = arr[:, 0] != arr[:, 1]
    arr = arr[keep]
    return Relation(name, source, arr[:, 0], arr[:, 1], arr[:, 2])


def _doi(text: str | None) -> str:
    t = str(text or "").strip().lower()
    t = re.sub(r"^https?://(dx\.)?doi\.org/", "", t)
    return t.removeprefix("doi:").strip()


def _title(t: str) -> str:
    t = t.replace("_", " ").strip()
    return (t[:1].upper() + t[1:]) if t else ""


def _arxiv(text: str | None) -> str:
    return re.sub(r"v\d+$", "", str(text or "").strip()).removesuffix(".pdf")


def build(c: Corpus) -> dict[str, Relation]:
    """Every relation of the corpus, and the bridges, keyed by name."""
    s_idx = {s: k for k, s in enumerate(c.sources)}
    by_source: dict[str, list[int]] = defaultdict(list)
    for g, k in enumerate(c.source_of):
        by_source[c.sources[k]].append(g)
    wiki_title = {_title(str(c.meta[g].get("title", ""))): g for g in by_source["wikipedia"]}
    oa_doi = {d: g for g in by_source["openalex"] if (d := _doi(c.meta[g].get("doi")))}
    oa_id = {str(c.meta[g]["id"]): g for g in by_source["openalex"]}
    ax_id = {_arxiv(c.meta[g].get("arxiv_id")): g for g in by_source["arxiv"]
             if c.meta[g].get("arxiv_id")}
    ax_doi = {d: g for g in by_source["arxiv"] if (d := _doi(c.meta[g].get("doi")))}
    se_id = {str(c.meta[g]["id"]): g for g in by_source["stackexchange"]}
    pg_id = {int(c.meta[g]["ebook"]): g for g in by_source["gutenberg"] if c.meta[g].get("ebook")}
    rel: dict[str, Relation] = {}

    def later(a: int, b: int) -> int:
        return max(c.dates[a], c.dates[b])

    # Wikipedia: hyperlinks between articles of the sample
    pairs = []
    for g in by_source["wikipedia"]:
        for t in c.meta[g].get("links", []):
            h = wiki_title.get(_title(str(t)))
            if h is not None:
                pairs.append((g, h, later(g, h)))
    rel["wikipedia.hyperlink"] = _rel("hyperlink", "wikipedia", pairs)
    # OpenAlex: references within the sample, on the citing work's date
    pairs = []
    for g in by_source["openalex"]:
        for r in c.meta[g].get("refs", []):
            h = oa_id.get(str(r))
            if h is not None:
                pairs.append((g, h, c.dates[g]))
    rel["openalex.citation"] = _rel("citation", "openalex", pairs)
    # Stack Exchange: answers to their questions, and links between posts
    answers, links = [], []
    for g in by_source["stackexchange"]:
        m = c.meta[g]
        q = se_id.get(str(m.get("parent") or ""))
        if q is not None:
            answers.append((g, q, c.dates[g]))
        for target, _kind in m.get("post_links", []):
            h = se_id.get(str(target))
            if h is not None:
                links.append((g, h, later(g, h)))
    rel["stackexchange.answer"] = _rel("answer", "stackexchange", answers)
    rel["stackexchange.link"] = _rel("link", "stackexchange", links)
    # versions: a chain per item, its nodes (item, version) numbered on their own
    for source, key in (("arxiv", "versions"), ("stackexchange", "versions")):
        pairs, node = [], 0
        for g in by_source[source]:
            vs = [day(v) for v in c.meta[g].get(key, []) if day(v) >= 0]
            for a, b in zip(vs, vs[1:], strict=False):
                pairs.append((node, node + 1, max(a, b)))
                node += 1
            node += 1
        rel[f"{source}.version"] = _rel("version", source, pairs)
    # the bridges, explicit, between sources
    bridges: dict[str, list[tuple[int, int, int]]] = defaultdict(list)
    for g in by_source["wikipedia"]:
        m = c.meta[g]
        for cite in m.get("cites", []):
            if (h := oa_doi.get(_doi(cite.get("doi")))) is not None:
                bridges["wikipedia-openalex"].append((g, h, later(g, h)))
            arx = _arxiv(cite.get("arxiv") or cite.get("eprint"))
            if arx and (h := ax_id.get(arx)) is not None:
                bridges["wikipedia-arxiv"].append((g, h, later(g, h)))
            if (h := ax_doi.get(_doi(cite.get("doi")))) is not None:
                bridges["wikipedia-arxiv"].append((g, h, later(g, h)))
        for n in m.get("gutenberg", []):
            if (h := pg_id.get(int(n))) is not None:
                bridges["wikipedia-gutenberg"].append((g, h, later(g, h)))
    for g in by_source["stackexchange"]:
        ln = c.meta[g].get("links", {})
        for t in ln.get("wikipedia", []):
            if (h := wiki_title.get(_title(str(t)))) is not None:
                bridges["stackexchange-wikipedia"].append((g, h, later(g, h)))
        for a in ln.get("arxiv", []):
            if (h := ax_id.get(_arxiv(a))) is not None:
                bridges["stackexchange-arxiv"].append((g, h, later(g, h)))
        for d in ln.get("doi", []):
            if (h := oa_doi.get(_doi(d))) is not None:
                bridges["stackexchange-openalex"].append((g, h, later(g, h)))
    for g in by_source["openalex"]:
        arx = _arxiv(c.meta[g].get("arxiv"))
        if arx and (h := ax_id.get(arx)) is not None:
            bridges["openalex-arxiv"].append((g, h, later(g, h)))
        elif (h := ax_doi.get(_doi(c.meta[g].get("doi")))) is not None:
            bridges["openalex-arxiv"].append((g, h, later(g, h)))
    for name, pairs in bridges.items():
        rel[f"bridge.{name}"] = _rel(name, "bridge", pairs)
    del s_idx
    return rel


def twins(rel: dict[str, Relation]) -> dict[int, int]:
    """The OpenAlex work of each arXiv record that has one (and the reverse), by gid."""
    r = rel.get("bridge.openalex-arxiv")
    out: dict[int, int] = {}
    if r is None:
        return out
    for a, b in zip(r.src.tolist(), r.dst.tolist(), strict=True):
        out.setdefault(a, b)
        out.setdefault(b, a)
    return out


def save(rel: dict[str, Relation], out: Path) -> dict[str, dict[str, float]]:
    """Each relation as an (m, 3) int32 array, and its bytes per edge on disk."""
    out.mkdir(parents=True, exist_ok=True)
    report: dict[str, dict[str, float]] = {}
    for name, r in rel.items():
        f = out / f"{name}.npy"
        np.save(f, r.triples())
        size = f.stat().st_size
        report[name] = {"edges": r.m, "bytes": size,
                        "bytes_per_edge": round(size / r.m, 2) if r.m else float("nan")}
    return report
