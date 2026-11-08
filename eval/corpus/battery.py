"""The retrieval battery and the attribution over sources (dn-corpus-instance §2.1, §6; SCL-3).

Retrieval is the plane's own: exact cosine over every current chunk vector (the float16 atoms the
plane holds, normalized here), top ten atoms, a hit when an item holding one of them is a gold
item. A scope `over <source>` keeps the atoms an item of that source holds: the source's mask on
the universe (QSA-10's `over` is a mask by strata, and every corpus item is observed, so the
source's mask is applied here, over the same vectors).

The families of questions:

- `titles:<source>`: a seeded sample of each source's items (Stack Exchange's questions), the
  item's title as the query, the item the gold;
- `twins:arxiv->openalex` and back: the abstract of a record with a twin, its twin the gold;
- `cite:wikipedia->paper`: a Wikipedia citation's title, the cited work (OpenAlex or arXiv, by DOI
  or arXiv id) and its twin the gold;
- `link:stackexchange->wikipedia` and `link:hackernews->wikipedia`: a question or a thread that
  links a Wikipedia article of the corpus, its title the query, the article the gold;
- `beir:<set>`: the embedder bench's two public sets, standalone (a fixed external control) and
  mixed into the corpus (the same queries, the corpus's atoms beside the set's documents).

Crowding (CIF-9): every family again over nested random subsets of the corpus's items (the gold
items always kept), unscoped and scoped, so recall at ten is read against N within the stage.

Attribution (SCL-3): `v(S)` is the share of the title questions answered (a gold item, or its
twin, in the top ten) when only the sources in `S` are present, for every `S` of the five; the
leave-one-out value of each source with the sign-flip test over questions (Holm across sources),
and the Shapley value. The OpenAlex and arXiv pair is the redundancy witness: on the questions
whose gold has a twin, each should carry about half and neither be necessary (CIF-10 broken if
both are necessary at the bar).
"""

from __future__ import annotations

import itertools
import math
import re
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from typing import Any

import numpy as np
import numpy.typing as npt

from eval.corpus.data import Corpus, Vectors

K = 10
FRACTIONS = (0.01, 0.03, 0.1, 0.3, 1.0)


@dataclass
class Question:
    family: str
    text: str
    gold: frozenset[int]            # gids
    scope: str                      # the source whose mask the scoped reading uses
    cluster: str                    # one observation (the gold's item)


def _abstract(content: str) -> str:
    return content.split("\n\n", 1)[1][:1500] if "\n\n" in content else content[:1500]


def questions(c: Corpus, rel: dict[str, Any], twins: dict[int, int], contents: dict[int, str],
              *, per_source: int = 500, seed: int = 0) -> list[Question]:
    rng = np.random.default_rng(seed)
    out: list[Question] = []
    for k, s in enumerate(c.sources):
        pool = [g for g in c.of(s).tolist()
                if s != "stackexchange" or c.meta[g].get("kind") == "question"]
        pick = pool if len(pool) <= per_source else \
            rng.choice(pool, size=per_source, replace=False).tolist()
        for g in pick:
            title = str(c.meta[g].get("title") or "").strip()
            if title:
                out.append(Question(f"titles:{s}", title, frozenset({int(g)}), s, f"g{g}"))
        del k
    ax = [g for g in c.of("arxiv").tolist() if g in twins and g in contents]
    oa = [g for g in c.of("openalex").tolist() if g in twins and g in contents]
    for fam, pool, scope in (("twins:arxiv->openalex", ax, "openalex"),
                             ("twins:openalex->arxiv", oa, "arxiv")):
        pick = pool if len(pool) <= per_source else \
            rng.choice(pool, size=per_source, replace=False).tolist()
        for g in pick:
            out.append(Question(fam, _abstract(contents[g]), frozenset({twins[g]}), scope,
                                f"g{twins[g]}"))
    cites: list[Question] = []
    for r_name in ("bridge.wikipedia-openalex", "bridge.wikipedia-arxiv"):
        r = rel.get(r_name)
        if r is None:
            continue
        for a, b in zip(r.src.tolist(), r.dst.tolist(), strict=True):
            target = c.meta[b]
            ids = {str(target.get("doi") or "").lower().removeprefix("https://doi.org/"),
                   str(target.get("arxiv_id") or "")} - {""}
            for cite in c.meta[a].get("cites", []):
                key = {str(cite.get("doi") or "").lower(), str(cite.get("arxiv") or ""),
                       str(cite.get("eprint") or "")} - {""}
                title = re.sub(r"\s+", " ", str(cite.get("title") or "")).strip()
                if title and key & ids:
                    gold = {b} | ({twins[b]} if b in twins else set())
                    cites.append(Question("cite:wikipedia->paper", title, frozenset(gold),
                                          c.sources[c.source_of[b]], f"g{b}"))
                    break
    seen: set[tuple[str, frozenset[int]]] = set()
    for q in cites:
        if (q.text, q.gold) not in seen:
            seen.add((q.text, q.gold))
            out.append(q)
    for src_name in ("stackexchange", "hackernews"):
        r = rel.get(f"bridge.{src_name}-wikipedia")
        if r is None:
            continue
        linked: dict[int, set[int]] = {}
        for a, b in zip(r.src.tolist(), r.dst.tolist(), strict=True):
            if src_name != "stackexchange" or c.meta[a].get("kind") == "question":
                linked.setdefault(a, set()).add(b)
        pool = sorted(linked)
        pick = pool if len(pool) <= per_source else \
            rng.choice(pool, size=per_source, replace=False).tolist()
        for a in pick:
            out.append(Question(f"link:{src_name}->wikipedia",
                                str(c.meta[a].get("title") or ""), frozenset(linked[a]),
                                "wikipedia", f"g{a}"))
    return [q for q in out if q.text]


class Engine:
    """Exact top-k over the plane's atoms, by blocks, under masks."""

    def __init__(self, vec: Vectors, c: Corpus) -> None:
        self.c = c
        self.m = vec.matrix
        norms = np.sqrt(np.einsum("ij,ij->i", self.m.astype(np.float32),
                                  self.m.astype(np.float32)))
        self.inv = (1.0 / np.maximum(norms, 1e-12)).astype(np.float32)
        self.holders = vec.holders
        n = len(vec.holders)
        self.atom_sources = np.zeros((n, len(c.sources)), dtype=bool)
        src = np.asarray(c.source_of)
        for i, hs in enumerate(vec.holders):
            self.atom_sources[i, src[hs]] = True

    def sims(self, q: npt.NDArray[np.float32], step: int = 250000) -> npt.NDArray[np.float32]:
        out = np.empty((q.shape[0], self.m.shape[0]), dtype=np.float32)
        for s in range(0, self.m.shape[0], step):
            block = self.m[s:s + step].astype(np.float32)
            out[:, s:s + step] = (q @ block.T) * self.inv[s:s + step]
        return out

    @staticmethod
    def topk(sims: npt.NDArray[np.float32], idx: npt.NDArray[np.int64], k: int = K
             ) -> npt.NDArray[np.int64]:
        """The top-k atoms of each row among `idx`, best first (atom rows)."""
        if len(idx) == 0:
            return np.zeros((sims.shape[0], 0), dtype=np.int64)
        sub = sims[:, idx]
        kk = min(k, sub.shape[1])
        part = np.argpartition(-sub, kth=kk - 1, axis=1)[:, :kk]
        vals = np.take_along_axis(sub, part, axis=1)
        order = np.argsort(-vals, axis=1)
        return idx[np.take_along_axis(part, order, axis=1)]

    def hit(self, atoms: Iterable[int] | npt.NDArray[np.int64], gold: frozenset[int]) -> bool:
        return any(g in gold for a in atoms for g in self.holders[int(a)])


def unit(x: npt.NDArray[np.float32]) -> npt.NDArray[np.float32]:
    return (x / np.maximum(np.linalg.norm(x, axis=1, keepdims=True), 1e-12)).astype(np.float32)


def run(c: Corpus, vec: Vectors, qs: list[Question], qvec: npt.NDArray[np.float32], *,
        twins: dict[int, int], fractions: Sequence[float] = FRACTIONS, seed: int = 0,
        block: int = 64) -> dict[str, Any]:
    """Recall at ten per family, unscoped and scoped, at each subset fraction; and v(S) for the
    title questions, gold widened by twins, over every set of sources."""
    eng = Engine(vec, c)
    rng = np.random.default_rng(seed)
    n_atoms = len(vec.holders)
    gold_items = set().union(*(q.gold for q in qs))
    order = rng.permutation(c.n)
    rank = np.empty(c.n, dtype=np.int64)
    rank[order] = np.arange(c.n)
    # an atom enters a subset with the first of its holders to enter it
    atom_rank = np.asarray([min(rank[h] for h in hs) if hs else c.n for hs in vec.holders])
    gold_atom = np.zeros(n_atoms, dtype=bool)
    for a, hs in enumerate(vec.holders):
        if any(h in gold_items for h in hs):
            gold_atom[a] = True
    levels = []
    for f in fractions:
        keep = (atom_rank < int(round(f * c.n))) | gold_atom
        levels.append((f, keep))
    src_idx = [np.flatnonzero(eng.atom_sources[:, k]) for k in range(len(c.sources))]
    rec: dict[str, dict[str, list[float]]] = {}
    sizes = {f: int(keep.sum()) for f, keep in levels}
    titles = [i for i, q in enumerate(qs) if q.family.startswith("titles:")]
    title_pos = {i: j for j, i in enumerate(titles)}
    coalitions = [frozenset(s) for r in range(1, len(c.sources) + 1)
                  for s in itertools.combinations(range(len(c.sources)), r)]
    v_hits = np.zeros((len(coalitions), len(titles)), dtype=bool)
    for s0 in range(0, len(qs), block):
        qb = unit(qvec[s0:s0 + block].astype(np.float32))
        sims = eng.sims(qb)
        for f, keep in levels:
            every = np.flatnonzero(keep)
            top_all = eng.topk(sims, every)
            scoped: dict[int, npt.NDArray[np.int64]] = {}
            for r, q in enumerate(qs[s0:s0 + block]):
                k = c.sources.index(q.scope)
                if k not in scoped:
                    scoped[k] = eng.topk(sims, np.intersect1d(every, src_idx[k],
                                                              assume_unique=True))
                fam = rec.setdefault(q.family, {})
                fam.setdefault(f"unscoped@{f}", []).append(float(eng.hit(top_all[r], q.gold)))
                fam.setdefault(f"scoped@{f}", []).append(float(eng.hit(scoped[k][r], q.gold)))
            if f == 1.0:
                per_src = [eng.topk(sims, src_idx[k]) for k in range(len(c.sources))]
                for r, q in enumerate(qs[s0:s0 + block]):
                    i = s0 + r
                    if i not in title_pos:
                        continue
                    g = set(q.gold)
                    g |= {twins[x] for x in q.gold if x in twins}
                    gold = frozenset(g)
                    for ci, coal in enumerate(coalitions):
                        cand = np.unique(np.concatenate([per_src[k][r] for k in coal]))
                        best = cand[np.argsort(-sims[r, cand])][:K]
                        v_hits[ci, title_pos[i]] = eng.hit(best, gold)
    recall = {fam: {k: float(np.mean(v)) for k, v in d.items()} for fam, d in rec.items()}
    counts = {fam: len(next(iter(d.values()))) for fam, d in rec.items()}
    return {"recall": recall, "questions": counts, "atoms_at": {str(f): sizes[f] for f in sizes},
            "attribution": attribution(c, [qs[i] for i in titles], coalitions, v_hits, twins)}


def attribution(c: Corpus, qs: list[Question], coalitions: list[frozenset[int]],
                hits: npt.NDArray[np.bool_], twins: dict[int, int]) -> dict[str, Any]:
    from eval.predictions.scoring import holm

    n = len(c.sources)
    index = {s: i for i, s in enumerate(coalitions)}
    full = frozenset(range(n))

    def v(s: frozenset[int], mask: npt.NDArray[np.bool_]) -> float:
        return float(hits[index[s], mask].mean()) if s and mask.any() else 0.0

    def readings(mask: npt.NDArray[np.bool_]) -> dict[str, Any]:
        vals = {",".join(c.sources[k] for k in sorted(s)): v(s, mask) for s in coalitions}
        shap = {}
        for i in range(n):
            tot = 0.0
            for s in coalitions:
                if i in s:
                    continue
                w = math.factorial(len(s)) * math.factorial(n - len(s) - 1) / math.factorial(n)
                tot += w * (v(s | {i}, mask) - v(s, mask))
            tot += math.factorial(n - 1) / math.factorial(n) * v(frozenset({i}), mask)
            shap[c.sources[i]] = tot
        loo, pvals = {}, []
        for i in range(n):
            rest = full - {i}
            d = hits[index[full], mask].astype(float) - hits[index[rest], mask].astype(float)
            loo[c.sources[i]] = float(d.mean())
            pvals.append(_signflip(d))
        adj = holm(pvals)
        return {"v_full": v(full, mask), "shapley": shap, "loo": loo,
                "loo_p": dict(zip(c.sources, pvals, strict=True)),
                "loo_p_holm": dict(zip(c.sources, adj, strict=True)), "values": vals,
                "questions": int(mask.sum())}
    every: npt.NDArray[np.bool_] = np.ones(len(qs), dtype=np.bool_)
    twin_q: npt.NDArray[np.bool_] = np.asarray([any(x in twins for x in q.gold) for q in qs],
                                               dtype=np.bool_)
    out: dict[str, Any] = {"all": readings(every), "twinned": readings(twin_q)}
    tw = out["twinned"]
    both_necessary = all(tw["loo_p_holm"][s] < 0.05 and tw["loo"][s] > 0
                         for s in ("openalex", "arxiv"))
    out["cif10_broken"] = bool(both_necessary)
    return out


def _signflip(d: npt.NDArray[np.float64], flips: int = 20000, seed: int = 0) -> float:
    """Two-sided p of the mean of paired differences by random sign flips (one cluster a
    question); exact zero differences carry no weight."""
    x = d[d != 0]
    if len(x) == 0:
        return 1.0
    rng = np.random.default_rng(seed)
    obs = abs(x.mean())
    signs = rng.choice([-1.0, 1.0], size=(flips, len(x)))
    null = np.abs((signs * x).mean(axis=1))
    return float((1 + np.sum(null >= obs - 1e-12)) / (flips + 1))


def beir_control(embed_docs: Any, embed_queries: Any, sets: dict[str, Any],
                 corpus_engine: Engine | None = None) -> dict[str, Any]:
    """nDCG and recall at ten on the bench's public sets, standalone; and mixed into the corpus's
    atoms when an engine is given (the corpus's atoms compete with the set's documents)."""
    out: dict[str, Any] = {}
    for name, (docs, queries, qrels) in sets.items():
        ids = list(docs)
        dv = unit(np.asarray(embed_docs([f"{docs[i][0]}\n\n{docs[i][1]}"[:2000] for i in ids]),
                             dtype=np.float32))
        qids = list(queries)
        qv = unit(np.asarray(embed_queries([queries[q] for q in qids]), dtype=np.float32))
        sims = qv @ dv.T
        ndcg, rec, mixed = [], [], []
        for r, q in enumerate(qids):
            top = np.argsort(-sims[r])[:K]
            ranked = [ids[i] for i in top]
            rels = qrels[q]
            dcg = sum((2 ** rels.get(d, 0) - 1) / math.log2(i + 2) for i, d in enumerate(ranked))
            ideal = sorted(rels.values(), reverse=True)[:K]
            idcg = sum((2 ** x - 1) / math.log2(i + 2) for i, x in enumerate(ideal))
            ndcg.append(dcg / idcg if idcg else 0.0)
            rec.append(len(set(ranked) & set(rels)) / len(rels))
        if corpus_engine is not None:
            for s0 in range(0, len(qids), 64):       # a block of queries against every atom
                cs = corpus_engine.sims(qv[s0:s0 + 64])
                for r in range(cs.shape[0]):
                    q = qids[s0 + r]
                    best_corpus = np.partition(cs[r], -K)[-K:]
                    pool = np.concatenate([sims[s0 + r], best_corpus])
                    top = np.argsort(-pool)[:K]
                    ranked = [ids[i] for i in top if i < len(ids)]
                    mixed.append(len(set(ranked) & set(qrels[q])) / len(qrels[q]))
        out[name] = {"docs": len(ids), "queries": len(qids), "ndcg10": float(np.mean(ndcg)),
                     "recall10": float(np.mean(rec)),
                     "recall10_mixed": float(np.mean(mixed)) if mixed else None}
    return out


# ── three arms: lexical, semantic, both ──────────────────────────────────────────────────────────

DEPTH = 100          # each arm's candidates, before they are read as items


@dataclass
class Lexical:
    """The lexical index of the landed chunks, with each unit's item (gid)."""

    index: Any                                  # core.ingest.lexical.LexicalIndex
    unit_item: npt.NDArray[np.int64]            # unit -> gid (-1: an item the corpus lacks)

    @staticmethod
    def load(d: Any, c: Corpus) -> Lexical:
        from core.ingest.lexical import LexicalIndex

        idx = LexicalIndex.load(d)
        units = np.load(d / "units.npz")
        paths = (d / "items.txt").read_text().split("\n")
        g = np.asarray([c.gid.get(p, -1) for p in paths], dtype=np.int64)
        return Lexical(idx, g[units["item"]])


def _items(units: npt.NDArray[np.int64], unit_item: Any, k: int = K) -> list[int]:
    """The distinct items of ranked units, in rank order, the first `k`."""
    out: list[int] = []
    seen: set[int] = set()
    for u in units.tolist():
        for g in (unit_item(u) if callable(unit_item) else [int(unit_item[u])]):
            if g >= 0 and g not in seen:
                seen.add(g)
                out.append(g)
        if len(out) >= k:
            break
    return out


def run_arms(c: Corpus, qs: list[Question], lex: Lexical, *, vec: Vectors | None = None,
             qvec: npt.NDArray[np.float32] | None = None, twins: dict[int, int],
             fractions: Sequence[float] = FRACTIONS, seed: int = 0) -> dict[str, Any]:
    """Recall at ten at the item grain (the first ten distinct items of each arm's ranking) for
    the lexical arm (BM25 over the landed chunks), the semantic arm (cosine over the plane's
    atoms) and both (reciprocal rank fusion of the two), unscoped and scoped by the gold's
    source, at each nested subset of the corpus (gold items always kept); the attribution over
    sources for each arm; and the embedder's attribution as a source, the two-player game whose
    players are the lexical index and the embedder. A question whose gold items have no vector
    yet is pending for the semantic arm and for both: counted as pending, never scored."""
    from core.ingest.lexical import rrf

    rng = np.random.default_rng(seed)
    order = rng.permutation(c.n)
    rank = np.empty(c.n, dtype=np.int64)
    rank[order] = np.arange(c.n)
    gold_items = set().union(*(q.gold for q in qs))
    is_gold: npt.NDArray[np.bool_] = np.zeros(c.n, dtype=np.bool_)
    is_gold[list(gold_items)] = True
    src = np.asarray(c.source_of)
    item_in = {f: (rank < int(round(f * c.n))) | is_gold for f in fractions}
    lex_item = lex.unit_item
    ok_unit = lex_item >= 0
    lex_src = np.where(ok_unit, src[np.maximum(lex_item, 0)], -1)
    lex_level = {f: np.flatnonzero(ok_unit & item_in[f][np.maximum(lex_item, 0)])
                 for f in fractions}
    lex_scope = {(f, k): np.intersect1d(lex_level[f], np.flatnonzero(lex_src == k),
                                         assume_unique=True)
                 for f in fractions for k in range(len(c.sources))}
    eng: Engine | None = None
    has_vec = np.zeros(c.n, dtype=bool)
    sem_level: dict[float, npt.NDArray[np.int64]] = {}
    sem_scope: dict[tuple[float, int], npt.NDArray[np.int64]] = {}
    if vec is not None and qvec is not None:
        eng = Engine(vec, c)
        for g in vec.item_atoms:
            has_vec[g] = True
        atom_first = np.asarray([min(rank[h] for h in hs) if hs else c.n for hs in vec.holders])
        atom_gold = np.asarray([any(is_gold[h] for h in hs) for hs in vec.holders],
                               dtype=np.bool_)
        for f in fractions:
            sem_level[f] = np.flatnonzero((atom_first < int(round(f * c.n))) | atom_gold)
            for k in range(len(c.sources)):
                sem_scope[(f, k)] = np.intersect1d(
                    sem_level[f], np.flatnonzero(eng.atom_sources[:, k]), assume_unique=True)
    arms = ("lexical", "semantic", "both") if eng is not None else ("lexical",)
    rec: dict[str, dict[str, list[float]]] = {}
    pending: dict[str, int] = {}
    n_src = len(c.sources)
    coalitions = [frozenset(s) for r in range(1, n_src + 1)
                  for s in itertools.combinations(range(n_src), r)]
    titles = [i for i, q in enumerate(qs) if q.family.startswith("titles:")]
    v_hits = {a: np.zeros((len(coalitions), len(titles)), dtype=bool) for a in arms}
    v_pending = np.zeros(len(titles), dtype=bool)
    tpos = {i: j for j, i in enumerate(titles)}
    sims_all: npt.NDArray[np.float32] | None = None
    block = 64
    for s0 in range(0, len(qs), block):
        batch = qs[s0:s0 + block]
        if eng is not None and qvec is not None:
            sims_all = eng.sims(unit(qvec[s0:s0 + block].astype(np.float32)))
        for r, q in enumerate(batch):
            i = s0 + r
            k = c.sources.index(q.scope)
            wide = set(q.gold) | {twins[x] for x in q.gold if x in twins}
            sem_pending = eng is not None and not any(has_vec[g] for g in q.gold)
            if sem_pending:
                pending[q.family] = pending.get(q.family, 0) + 1
            lex_scores = lex.index.scores(q.text)
            for f in fractions:
                for scope_name, lidx, sidx in (
                        ("unscoped", lex_level[f], sem_level.get(f)),
                        ("scoped", lex_scope[(f, k)], sem_scope.get((f, k)))):
                    lu = _top_units(lex_scores, lidx)
                    ranked = {"lexical": _items(lu, lex_item, DEPTH)}
                    if eng is not None and sims_all is not None and sidx is not None:
                        su = eng.topk(sims_all[r:r + 1], sidx, DEPTH)[0]
                        ranked["semantic"] = _items(su, lambda a: eng.holders[a], DEPTH)
                        ranked["both"] = rrf([np.asarray(ranked["lexical"], np.int64),
                                              np.asarray(ranked["semantic"], np.int64)],
                                             k=DEPTH).tolist()
                    for arm in arms:
                        if arm != "lexical" and sem_pending:
                            continue
                        hit = any(g in q.gold for g in ranked[arm][:K])
                        rec.setdefault(f"{arm}:{q.family}", {}).setdefault(
                            f"{scope_name}@{f}", []).append(float(hit))
            if i in tpos:
                j = tpos[i]
                v_pending[j] = sem_pending
                # each source's best units, merged by score for every set of sources: the top
                # of a union is among the tops of its parts
                per_lex = [_top_units(lex_scores, lex_scope[(1.0, kk)]) for kk in range(n_src)]
                per_sem: list[npt.NDArray[np.int64]] = []
                if eng is not None and sims_all is not None:
                    per_sem = [eng.topk(sims_all[r:r + 1], sem_scope[(1.0, kk)], DEPTH)[0]
                               for kk in range(n_src)]
                for ci, coal in enumerate(coalitions):
                    lu = np.concatenate([per_lex[kk] for kk in coal])
                    lu = lu[np.argsort(-lex_scores[lu], kind="stable")]
                    lex_rank = _items(lu, lex_item, DEPTH)
                    v_hits["lexical"][ci, j] = any(g in wide for g in lex_rank[:K])
                    if per_sem and sims_all is not None and eng is not None:
                        su = np.unique(np.concatenate([per_sem[kk] for kk in coal]))
                        su = su[np.argsort(-sims_all[r, su], kind="stable")]
                        sem_rank = _items(su, lambda a: eng.holders[a], DEPTH)
                        v_hits["semantic"][ci, j] = any(g in wide for g in sem_rank[:K])
                        fused = rrf([np.asarray(lex_rank, np.int64),
                                     np.asarray(sem_rank, np.int64)], k=K).tolist()
                        v_hits["both"][ci, j] = any(g in wide for g in fused[:K])
    recall = {name: {key: float(np.mean(v)) for key, v in d.items()} for name, d in rec.items()}
    counts = {name: len(next(iter(d.values()))) for name, d in rec.items()}
    # the fall of recall from the smallest subset to the whole corpus, paired by question, with
    # a 95% bootstrap interval over questions
    drop: dict[str, dict[str, list[float]]] = {}
    lo_f, hi_f = min(fractions), max(fractions)
    boot = np.random.default_rng(seed + 1)
    for name, d in rec.items():
        for scope_name in ("unscoped", "scoped"):
            a = np.asarray(d.get(f"{scope_name}@{lo_f}", []))
            b = np.asarray(d.get(f"{scope_name}@{hi_f}", []))
            if len(a) == 0 or len(a) != len(b):
                continue
            diff = a - b
            means = [float(diff[boot.integers(0, len(diff), len(diff))].mean())
                     for _ in range(2000)]
            drop.setdefault(name, {})[scope_name] = [
                float(diff.mean()), float(np.percentile(means, 2.5)),
                float(np.percentile(means, 97.5))]
    title_qs = [qs[i] for i in titles]
    attribution_by_arm = {}
    for arm in arms:
        mask_ok = ~v_pending if arm != "lexical" else np.ones(len(titles), dtype=bool)
        attribution_by_arm[arm] = attribution(
            c, [q for q, ok in zip(title_qs, mask_ok, strict=True) if ok], coalitions,
            v_hits[arm][:, mask_ok], twins)
    out: dict[str, Any] = {"recall": recall, "questions": counts, "pending": pending,
                           "drop": drop, "arms": list(arms), "attribution": attribution_by_arm,
                           "items_with_vectors": int(has_vec.sum()), "items": c.n}
    if eng is not None:
        out["embedder"] = embedder_game(rec)
    return out


def _top_units(scores: npt.NDArray[np.float32], among: npt.NDArray[np.int64],
               depth: int = DEPTH) -> npt.NDArray[np.int64]:
    if len(among) == 0:
        return np.zeros(0, dtype=np.int64)
    sub = scores[among]
    hit = sub > 0
    idx, sub = among[hit], sub[hit]
    if len(idx) == 0:
        return np.zeros(0, dtype=np.int64)
    kk = min(depth, len(idx))
    part = np.argpartition(-sub, kth=kk - 1)[:kk]
    return idx[part[np.argsort(-sub[part])]]


def embedder_game(rec: dict[str, dict[str, list[float]]]) -> dict[str, Any]:
    """The embedder as a source (SCL-3): the game of two players, the lexical index L and the
    embedder E, valued by recall at ten unscoped over the whole corpus: v({}) = 0,
    v({L}) = lexical, v({E}) = semantic, v({L, E}) = both. Its leave-one-out value is
    v({L, E}) - v({L}); its Shapley value (v({E}) + v({L, E}) - v({L})) / 2."""
    out: dict[str, Any] = {}
    fams = sorted({name.split(":", 1)[1] for name in rec})
    for fam in fams:
        def v(arm: str, fam: str = fam) -> float | None:
            d = rec.get(f"{arm}:{fam}", {}).get("unscoped@1.0")
            return float(np.mean(d)) if d else None
        lx, sm, bt = v("lexical"), v("semantic"), v("both")
        if lx is None or sm is None or bt is None:
            continue
        out[fam] = {"lexical": lx, "semantic": sm, "both": bt, "loo_embedder": bt - lx,
                    "shapley_embedder": (sm + bt - lx) / 2.0,
                    "shapley_lexical": (lx + bt - sm) / 2.0}
    return out
