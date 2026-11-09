"""Experiment 1: the lexical tokenizer and Unicode normalization (docs/experiments/
embedder-use-2026-11-08.md).

Arms are `core.ingest.lexical.Tokenizer`s, so the study and the store tokenize by one function:
T0 is `LEGACY` (no normalization, `lower()`, marks splitting), T1 to T4 the four combinations of
NFC or NFKC with `lower()` or `casefold()`, T5 NFKC and `casefold()` with combining marks inside a
token; T6 adds Harman's S stemmer to T5 (three suffix rules for English plurals; informational, it
is English only).

Two readings. **Counts**, over a collection's chunks: each arm's vocabulary and token
occurrences; the T0 terms that merge with another T0 term under the arm (two terms whose arm
forms are one); the T0 occurrences whose term changes; and the atoms, the distinct chunk texts,
that coincide under NFC and under NFKC (what hashing normalized text would merge; the store keeps
hashing raw bytes). **Retrieval**: BM25 over the chunks with each arm (`LexicalIndex`, the store's
weights), a document's score its best unit's, recall@10 and nDCG@10 paired against T0; on the
public sets with the live chunks, and on the corpus battery's lexical arm over every chunk of the
corpus instance.
"""

from __future__ import annotations

import re
import time
import unicodedata
from collections import Counter
from collections.abc import Callable, Iterable, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np

from core.ingest.lexical import LEGACY, LexicalIndex, Tokenizer, _marks_class
from core.kernel.ingest.pipeline import derive_chunks
from eval.embedder_use.common import I64, Collection, compare, read_catalog, score

ARMS: dict[str, Tokenizer] = {
    "T0": LEGACY,
    "T1": Tokenizer("NFC", "lower", False),
    "T2": Tokenizer("NFC", "casefold", False),
    "T3": Tokenizer("NFKC", "lower", False),
    "T4": Tokenizer("NFKC", "casefold", False),
    "T5": Tokenizer("NFKC", "casefold", True),
}
Log = Callable[[str], None]


def s_stem(term: str) -> str:
    """Harman's S stemmer (1991): the first rule that applies of -ies to -y (not -eies, -aies),
    -es to -e (not -aes, -ees, -oes), and -s dropped (not -us, -ss)."""
    if term.endswith("ies") and not term.endswith(("eies", "aies")):
        return term[:-3] + "y"
    if term.endswith("es") and not term.endswith(("aes", "ees", "oes")):
        return term[:-1]
    if term.endswith("s") and not term.endswith(("us", "ss")):
        return term[:-1]
    return term


@dataclass(frozen=True)
class Stemmed:
    """A tokenizer whose terms are S-stemmed (terms of three letters or fewer kept)."""

    inner: Tokenizer

    @property
    def identity(self) -> str:
        return f"{self.inner.identity}+s-stem"

    def __call__(self, text: str) -> list[str]:
        return [s_stem(t) if len(t) > 3 else t for t in self.inner(text)]


@dataclass(frozen=True)
class Ascii:
    """The tokenizer stage 1's corpus index was built with: runs of `[0-9a-z]` in the
    lower-cased text, every other character a separator (a reference arm, not a candidate)."""

    @property
    def identity(self) -> str:
        return "ascii/[0-9a-z]+/lower"

    def __call__(self, text: str) -> list[str]:
        return _ASCII.findall(text.lower())


_ASCII = re.compile(r"[0-9a-z]+")


def arms(with_stem: bool = True, with_ascii: bool = False) -> dict[str, Any]:
    out: dict[str, Any] = dict(ARMS)
    if with_stem:
        out["T6"] = Stemmed(ARMS["T5"])
    if with_ascii:
        out["TA"] = Ascii()
    return out


# ── counts ───────────────────────────────────────────────────────────────────────────────────────

def counts(texts: Sequence[str], log: Log) -> dict[str, Any]:
    """Vocabulary, occurrences, merges and coinciding atoms of a collection's chunks, per arm."""
    t0 = time.monotonic()
    base: Counter[str] = Counter()
    for t in texts:
        base.update(LEGACY(t))
    out: dict[str, Any] = {"units": len(texts), "atoms": len(set(texts))}
    for name, tk in arms().items():
        vocab: Counter[str] = Counter()
        for t in texts:
            vocab.update(tk(t))
        forms: dict[str, list[str]] = {}
        changed = 0
        for term, n in base.items():
            f = tk(term)
            key = " ".join(f)
            forms.setdefault(key, []).append(term)
            if f != [term]:
                changed += n
        merged_groups = [g for g in forms.values() if len(g) > 1]
        out[name] = {"identity": tk.identity, "vocabulary": len(vocab),
                     "occurrences": int(sum(vocab.values())),
                     "t0_terms_merging": int(sum(len(g) for g in merged_groups)),
                     "t0_terms_lost_to_merges": int(sum(len(g) - 1 for g in merged_groups)),
                     "t0_occurrences_changed": int(changed),
                     "t0_occurrences_changed_share": round(changed / max(1, sum(base.values())),
                                                           6)}
        log(f"  counts {name}: vocabulary {len(vocab)} ({time.monotonic() - t0:.0f} s)")
    atoms = set(texts)
    out["atoms_coinciding"] = {
        form: len(atoms) - len({unicodedata.normalize(form, a) for a in atoms})
        for form in ("NFC", "NFKC")}
    out["atoms_not_nfc"] = sum(1 for a in atoms if not unicodedata.is_normalized("NFC", a))
    out["atoms_not_nfkc"] = sum(1 for a in atoms if not unicodedata.is_normalized("NFKC", a))
    marks = re.compile(f"[{_marks_class()}]")
    out["atoms_with_marks"] = sum(1 for a in atoms if marks.search(a))
    return out


# ── retrieval on a collection ────────────────────────────────────────────────────────────────────

def beir_units(col: Collection) -> tuple[list[str], I64, list[str]]:
    """The live chunks of every document, with each chunk's document number."""
    texts: list[str] = []
    doc_of: list[int] = []
    docs = list(col.docs)
    for i, d in enumerate(docs):
        for c in derive_chunks(col.docs[d][1]):
            texts.append(c.text)
            doc_of.append(i)
    return texts, np.asarray(doc_of, dtype=np.int64), docs


def lexical_ranking(index: LexicalIndex, query: str, doc_of: I64, docs: list[str],
                    k: int = 10, depth: int = 200) -> list[str]:
    """The first `k` documents by their best unit's BM25 score (units sharing no term never
    rank)."""
    top = index.search(query, k=depth)
    out: list[str] = []
    for u in top.tolist():
        d = docs[int(doc_of[u])]
        if d not in out:
            out.append(d)
            if len(out) == k:
                break
    return out


def run_collection(col: Collection, log: Log) -> dict[str, Any]:
    texts, doc_of, docs = beir_units(col)
    qids = list(col.queries)
    results: dict[str, dict[str, list[float]]] = {}
    sizes: dict[str, Any] = {}
    for name, tk in arms().items():
        index = LexicalIndex.build(texts, tokenizer=tk)
        ranked = [lexical_ranking(index, col.queries[q], doc_of, docs) for q in qids]
        results[name] = score(col, qids, ranked)
        sizes[name] = {"terms": len(index.vocab), "postings": int(index.weights.nnz)}
        log(f"  {col.name} {name}: ndcg {np.mean(results[name]['ndcg']):.4f}")
    return {"collection": col.name, "units": len(texts), "index": sizes,
            "comparison": compare(results, "T0", qids), "counts": counts(texts, log)}


# ── the corpus battery's lexical arm ─────────────────────────────────────────────────────────────

def corpus_units(instance: Path, gid: dict[str, int], log: Log) -> tuple[list[str], I64]:
    """Every chunk of every active item of the corpus instance, from its raw store as the
    landing chunks it, with each chunk's item (gid; -1 for an item the streams lack). Read
    only."""
    texts: list[str] = []
    item: list[int] = []
    raw = instance / "data" / "raw"
    for n, (path, (_title, digest)) in enumerate(sorted(read_catalog(instance).items())):
        for c in derive_chunks((raw / digest[:2] / digest).read_bytes()):
            texts.append(c.text)
            item.append(gid.get(path, -1))
        if n % 100000 == 0:
            log(f"  corpus units: {n} items, {len(texts)} chunks")
    return texts, np.asarray(item, dtype=np.int64)


def item_ranking(index: LexicalIndex, query: str, unit_item: I64, k: int = 10,
                 depth: int = 100) -> list[int]:
    out: list[int] = []
    for u in index.search(query, k=depth).tolist():
        g = int(unit_item[u])
        if g >= 0 and g not in out:
            out.append(g)
            if len(out) == k:
                break
    return out


def binary_scores(ranked: Iterable[list[int]], golds: Iterable[frozenset[int]]
                  ) -> dict[str, list[float]]:
    rec, ndcg, hit = [], [], []
    for r, g in zip(ranked, golds, strict=True):
        found = [x in g for x in r[:10]]
        rec.append(sum(found) / len(g))
        dcg = sum(1.0 / np.log2(i + 2) for i, f in enumerate(found) if f)
        idcg = sum(1.0 / np.log2(i + 2) for i in range(min(len(g), 10)))
        ndcg.append(float(dcg / idcg))
        hit.append(float(any(found)))
    return {"recall": rec, "ndcg": ndcg, "hit": hit}


def run_corpus(instance: Path, log: Log, *, only: Sequence[str] | None = None,
               with_counts: bool = True) -> dict[str, Any]:
    from eval.corpus.battery import questions
    from eval.corpus.data import SOURCES, load
    from eval.corpus.edges import build, twins
    from eval.embedder_use.common import stream_contents

    c = load(instance / "sources", SOURCES)
    rel = build(c)
    tw = twins(rel)
    qs = questions(c, rel, tw, stream_contents(instance, c, set(tw)), per_source=500)
    texts, unit_item = corpus_units(instance, c.gid, log)
    log(f"corpus: {len(texts)} units, {len(qs)} questions")
    qids = [f"q{i}" for i in range(len(qs))]
    results: dict[str, dict[str, list[float]]] = {}
    sizes: dict[str, Any] = {}
    for name, tk in arms(with_ascii=bool(only and "TA" in only)).items():
        if only and name not in only:
            continue
        t0 = time.monotonic()
        index = LexicalIndex.build(texts, tokenizer=tk)
        built = time.monotonic() - t0
        ranked = [item_ranking(index, q.text, unit_item) for q in qs]
        results[name] = binary_scores(ranked, [q.gold for q in qs])
        sizes[name] = {"terms": len(index.vocab), "postings": int(index.weights.nnz),
                       "build_seconds": round(built, 1)}
        log(f"  corpus {name}: recall {np.mean(results[name]['recall']):.4f} "
            f"({sizes[name]})")
        del index
    fams = sorted({q.family for q in qs})
    by_family = {}
    for fam in fams:
        idx = [i for i, q in enumerate(qs) if q.family == fam]
        by_family[fam] = {a: {m: round(float(np.mean([r[m][i] for i in idx])), 4)
                              for m in ("recall", "ndcg", "hit")} for a, r in results.items()}
    return {"units": len(texts), "questions": len(qs), "index": sizes,
            "comparison": compare(results, "T0", qids, metrics=("recall", "ndcg", "hit")),
            "by_family": by_family, "counts": counts(texts, log) if with_counts else None}
