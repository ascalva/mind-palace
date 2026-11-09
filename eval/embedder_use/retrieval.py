"""Experiments 2 to 5 on the public sets and the corpus subsample W: the chunk budget, the chunk's
context, the query's task prompt, and Matryoshka truncation, each arm scored at the document level
against the live default (docs/experiments/embedder-use-2026-11-08.md).

Every arm is a chunking, a document template and a query template. Its chunks are embedded through
the cached `Embedder` (one stream, the length fit on every request, the server's slots sampled
through the phase), documents are ranked by their best chunk, and each query's recall@10 and
nDCG@10 are paired with the reference arm's. An arm also reports the vectors it stores (distinct
chunk inputs, the plane's atoms), their bytes at float16, and the tokens its inputs take in the
server's tokenizer, which is what re-embedding a store under that arm costs.
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from typing import Any

import numpy as np

from eval.embedder_use.chunking import (
    char_chunks,
    chunk_spans,
    document_text,
    token_chunks,
)
from eval.embedder_use.common import (
    DOC_NONE,
    DOC_TITLE,
    F32,
    MODEL,
    QUERY_FACT,
    QUERY_QA,
    QUERY_SEARCH,
    Cache,
    Chunked,
    Collection,
    Embedder,
    ServerTokenizer,
    chunked,
    compare,
    float16_bytes,
    quantiles,
    rank_documents,
    score,
    unit,
)
from eval.embedder_use.late import OVERLAP, WINDOW, LateLedger, late_vectors
from eval.two_phase_bench import Contention

CHAR_BUDGETS = (600, 1200, 2400, 4800)
TOKEN_BUDGETS = (128, 256, 512, 1024)
REFERENCE_CHARS = 1200
Log = Callable[[str], None]


def families(col: Collection) -> dict[str, list[str]]:
    """The query sets a collection is scored on: every query of a public set; W's link questions
    (primary) and its title questions."""
    if col.name == "W":
        return {"link": col.subset("link"), "title": col.subset("title")}
    return {col.name: list(col.queries)}


def inputs(col: Collection, ch: Chunked, template: str) -> list[str]:
    """Each chunk's input to the embedder: the document template with its text (and its
    document's title, when the template names one)."""
    if "{title}" not in template:
        return [template.format(text=t) for t in ch.texts]
    return [template.format(title=col.docs[ch.docs[int(d)]][0] or "none", text=t)
            for t, d in zip(ch.texts, ch.doc_of.tolist(), strict=True)]


def query_vectors(col: Collection, emb: Embedder, template: str, log: Log) -> dict[str, F32]:
    qids = list(col.queries)
    m = emb.vectors([template.format(text=col.queries[q]) for q in qids], log=log)
    return {q: m[i] for i, q in enumerate(qids)}


def evaluate(col: Collection, ch: Chunked, cv: F32, qv: dict[str, F32]
             ) -> dict[str, dict[str, list[float]]]:
    """Each family's per-query recall@10 and nDCG@10 for chunk vectors `cv`."""
    out = {}
    for fam, qids in families(col).items():
        q = np.stack([qv[x] for x in qids])
        out[fam] = score(col, qids, rank_documents(q, cv, ch))
    return out


def cost(ch: Chunked, ins: Sequence[str], tok: ServerTokenizer) -> dict[str, Any]:
    distinct = sorted(set(ins))
    counts = tok.count(distinct)
    return {"chunks": len(ch.texts), "vectors": len(distinct),
            "bytes_float16": float16_bytes(len(distinct)), "tokens": int(sum(counts)),
            "tokens_per_input": quantiles([float(x) for x in counts])}


def table(col: Collection, results: dict[str, dict[str, dict[str, list[float]]]], ref: str
          ) -> dict[str, Any]:
    """The comparison of every arm against `ref`, per family."""
    return {fam: compare({arm: r[fam] for arm, r in results.items()}, ref, qids)
            for fam, qids in families(col).items()}


def by_chars(budget: int) -> Callable[[str, str], list[str]]:
    def chunk(_doc: str, body: str) -> list[str]:
        return char_chunks(body, budget)
    return chunk


def by_tokens(budget: int, tok: ServerTokenizer) -> Callable[[str, str], list[str]]:
    def chunk(_doc: str, body: str) -> list[str]:
        return token_chunks(body, budget, tok.spans)
    return chunk


def chunkings(col: Collection, tok: ServerTokenizer) -> dict[str, Chunked]:
    arms: dict[str, Chunked] = {}
    for b in CHAR_BUDGETS:
        arms[f"C{b}"] = chunked(col, by_chars(b))
    for b in TOKEN_BUDGETS:
        arms[f"K{b}"] = chunked(col, by_tokens(b, tok))
    return arms


def run_chunks(col: Collection, emb: Embedder, tok: ServerTokenizer, log: Log) -> dict[str, Any]:
    """Experiment 2: every budget, in characters and in tokens, against C1200."""
    log(f"{col.name}: chunking")
    arms = chunkings(col, tok)
    qv = query_vectors(col, emb, QUERY_SEARCH, log)
    results, costs = {}, {}
    with Contention(emb.port, own=None) as c:
        for name, ch in arms.items():
            ins = inputs(col, ch, DOC_NONE)
            log(f"{col.name} {name}: {len(ins)} chunks")
            results[name] = evaluate(col, ch, emb.vectors(ins, log=log), qv)
            costs[name] = cost(ch, ins, tok)
    return {"collection": col.name, "documents": len(col.docs), "costs": costs,
            "comparison": table(col, results, f"C{REFERENCE_CHARS}"),
            "contention": c.summary(), "embedder": emb.ledger.summary()}


LATE_ARMS = (("L", DOC_NONE, True), ("LT", DOC_TITLE, True), ("L1", DOC_NONE, False))


def late(col: Collection, ch: Chunked, tok: ServerTokenizer, template: str, port: int,
         ledger: LateLedger, log: Log, *, context: bool = True) -> F32:
    """Late-chunked vectors of a C1200 chunking, document by document, cached by the prefix, the
    document's text and the chunk's span. With `context` false each chunk is its own document
    (the control: late pooling, no other chunk in view)."""
    out = np.zeros((len(ch.texts), 768), dtype=np.float32)
    starts = ch.starts.tolist() + [len(ch.texts)]
    salt = f"{MODEL}/late/{WINDOW}/{OVERLAP}"
    for n, (s, e) in enumerate(zip(starts[:-1], starts[1:], strict=True)):
        doc = ch.docs[int(ch.doc_of[s])]
        title = col.docs[doc][0] or "none"
        prefix = template.split("{text}")[0].format(title=title)
        if context:
            text = document_text(col.body(doc), REFERENCE_CHARS)
            parts = [(text, chunk_spans(text, ch.texts[s:e]), list(range(s, e)))]
        else:
            parts = [(t, [(0, len(t))], [i]) for i, t in zip(range(s, e), ch.texts[s:e],
                                                              strict=True)]
        for text, spans, rows in parts:
            keys = [Cache.key(f"{prefix}\x00{text}\x00{a}:{b}", salt=salt) for a, b in spans]
            have = tok.cache.vectors(keys)
            if len(have) < len(keys):
                v = late_vectors(prefix, text, spans, tok, port=port, ledger=ledger)
                tok.cache.put_vectors(list(zip(keys, v, strict=True)))
                have = dict(zip(keys, v, strict=True))
            out[rows] = np.stack([have[k] for k in keys])
        if n % 500 == 0:
            log(f"    late {n} of {len(starts) - 1} documents")
    return out


def precompute_late(col: Collection, tok: ServerTokenizer, port: int, log: Log
                    ) -> dict[str, Any]:
    """Every late arm's vectors into the cache (the pooling-none server alone), so the context
    experiment reads them back while the stack's server embeds the other arms."""
    ch = chunked(col, by_chars(REFERENCE_CHARS))
    out: dict[str, Any] = {"collection": col.name}
    for name, template, context in LATE_ARMS:
        ledger = LateLedger()
        log(f"{col.name} {name}: late chunking on port {port}")
        late(col, ch, tok, template, port, ledger, log, context=context)
        out[name] = ledger.summary()
    return out


def run_context(col: Collection, emb: Embedder, tok: ServerTokenizer, log: Log, *,
                late_port: int | None, late_tok: ServerTokenizer | None) -> dict[str, Any]:
    """Experiment 3: the title in the document template, and late chunking, against N."""
    ch = chunked(col, by_chars(REFERENCE_CHARS))
    qv = query_vectors(col, emb, QUERY_SEARCH, log)
    results: dict[str, dict[str, dict[str, list[float]]]] = {}
    costs: dict[str, Any] = {}
    with Contention(emb.port, own=None) as c:
        for name, template in (("N", DOC_NONE), ("T", DOC_TITLE)):
            ins = inputs(col, ch, template)
            log(f"{col.name} {name}: {len(ins)} chunks")
            results[name] = evaluate(col, ch, emb.vectors(ins, log=log), qv)
            costs[name] = cost(ch, ins, tok)
    out: dict[str, Any] = {"collection": col.name, "contention": c.summary()}
    if late_port is not None and late_tok is not None:
        for name, template, context in LATE_ARMS:
            ledger = LateLedger()
            cv = late(col, ch, late_tok, template, late_port, ledger, log, context=context)
            results[name] = evaluate(col, ch, cv, qv)
            costs[name] = {"chunks": len(ch.texts), "vectors": ch.atoms(),
                           "bytes_float16": float16_bytes(ch.atoms()), **ledger.summary()}
            out[f"{name}_agreement_one_chunk_docs"] = agreement(col, ch, cv, emb, template)
    out.update({"costs": costs, "comparison": table(col, results, "N"),
                "embedder": emb.ledger.summary()})
    return out


def agreement(col: Collection, ch: Chunked, cv: F32, emb: Embedder, template: str
              ) -> dict[str, float]:
    """The cosine between a document's late vector and its independent vector, over documents of
    one chunk (where only the pooling set differs: the chunk's tokens against every token)."""
    starts = ch.starts.tolist() + [len(ch.texts)]
    one = [s for s, e in zip(starts[:-1], starts[1:], strict=True) if e - s == 1][:300]
    if not one:
        return {}
    sub = Chunked([ch.texts[s] for s in one], ch.doc_of[one], ch.docs)
    ind = emb.vectors(inputs(col, sub, template))
    cos = np.sum(ind * cv[one], axis=1)
    return {"documents": len(one), "median": float(np.median(cos)), "min": float(cos.min())}


def run_prompts(col: Collection, emb: Embedder, log: Log) -> dict[str, Any]:
    """Experiment 4: the query's task prompt, the documents as N."""
    ch = chunked(col, by_chars(REFERENCE_CHARS))
    with Contention(emb.port, own=None) as c:
        cv = emb.vectors(inputs(col, ch, DOC_NONE), log=log)
        results = {name: evaluate(col, ch, cv, query_vectors(col, emb, template, log))
                   for name, template in (("search", QUERY_SEARCH), ("qa", QUERY_QA),
                                          ("fact", QUERY_FACT))}
    return {"collection": col.name, "comparison": table(col, results, "search"),
            "contention": c.summary(), "embedder": emb.ledger.summary()}


def truncate(x: F32, d: int) -> F32:
    """The first `d` coordinates, renormalized, held at float16 as a store would hold them."""
    return unit(x[:, :d]).astype(np.float16).astype(np.float32)


def run_dims(col: Collection, emb: Embedder, log: Log, *, rescore: int = 50) -> dict[str, Any]:
    """Experiment 5: Matryoshka truncation, flat and rescored, the documents as N."""
    ch = chunked(col, by_chars(REFERENCE_CHARS))
    full = emb.vectors(inputs(col, ch, DOC_NONE), log=log)
    qv = query_vectors(col, emb, QUERY_SEARCH, log)
    exact = full.astype(np.float16).astype(np.float32)
    results: dict[str, dict[str, dict[str, list[float]]]] = {}
    for d in (768, 512, 256, 128):
        qd = {q: truncate(v[None, :], d)[0] for q, v in qv.items()}
        results[f"D{d}"] = evaluate(col, ch, truncate(full, d), qd)
        if d < 768:
            results[f"D{d}r"] = rescored(col, ch, full, exact, qv, d, rescore)
    return {"collection": col.name, "chunks": len(ch.texts), "vectors": ch.atoms(),
            "bytes_per_vector": {f"D{d}": 2 * d for d in (768, 512, 256, 128)},
            "rescore_candidates": rescore,
            "comparison": table(col, results, "D768")}


def rescored(col: Collection, ch: Chunked, full: F32, exact: F32, qv: dict[str, F32], d: int,
             m: int) -> dict[str, dict[str, list[float]]]:
    """The `m` best chunks at `d` dimensions, rescored with the full float16 vectors; documents
    ranked by their best rescored chunk (a document outside the candidates is not ranked)."""
    coarse = truncate(full, d)
    out = {}
    for fam, qids in families(col).items():
        ranked = []
        for x in qids:
            q = qv[x]
            s = coarse @ unit(q[None, :d].astype(np.float32))[0]
            cand = np.argpartition(-s, kth=min(m, len(s)) - 1)[:m]
            fine = exact[cand] @ q
            order = cand[np.argsort(-fine, kind="stable")]
            docs: list[str] = []
            for i in order.tolist():
                doc = ch.docs[int(ch.doc_of[i])]
                if doc not in docs:
                    docs.append(doc)
                if len(docs) == 10:
                    break
            ranked.append(docs)
        out[fam] = score(col, qids, ranked)
    return out


def carried(texts: list[str]) -> list[bool]:
    """Whether each chunk is carried whole into the next one as its overlap (a chunk shorter
    than the overlap: the chunker emits it, then starts the next chunk with all of it)."""
    return [i + 1 < len(texts) and texts[i + 1].startswith(texts[i] + "\n\n")
            for i in range(len(texts))]


def run_carried(col: Collection, emb: Embedder, log: Log) -> dict[str, Any]:
    """An exploratory arm added after the counts: the live chunks without the ones carried whole
    into the next (on these sets, the title emitted alone), from the cached vectors of N."""
    ch = chunked(col, by_chars(REFERENCE_CHARS))
    cv = emb.vectors(inputs(col, ch, DOC_NONE), log=log)
    qv = query_vectors(col, emb, QUERY_SEARCH, log)
    drop = np.zeros(len(ch.texts), dtype=bool)
    starts = ch.starts.tolist() + [len(ch.texts)]
    for s, e in zip(starts[:-1], starts[1:], strict=True):
        drop[s:e] = carried(ch.texts[s:e])
    keep = ~drop
    kept = Chunked([t for t, k in zip(ch.texts, keep.tolist(), strict=True) if k],
                   ch.doc_of[keep], ch.docs)
    results = {"N": evaluate(col, ch, cv, qv), "Nd": evaluate(col, kept, cv[keep], qv)}
    return {"collection": col.name, "chunks": len(ch.texts), "carried": int(drop.sum()),
            "vectors": {"N": ch.atoms(), "Nd": kept.atoms()},
            "comparison": table(col, results, "N")}
