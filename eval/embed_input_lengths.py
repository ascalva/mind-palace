"""How long, in the embedder's tokens, are the texts a store embeds? (core/ingest/embed.py)

    uv run python -m eval.embed_input_lengths --lance DATA/vectors.lance [--label store]
    uv run python -m eval.embed_input_lengths --instance ROOT --sample 2000 [--chunks 5000]
    ... [--template 'title: none | text: {text}'] [--port 8081] [--limit 2048] [--out PATH]

The embedding server refuses an input longer than its batch rather than truncating it, and a
chunk's budget of characters does not bound its tokens. This counts, with the server's own
tokenizer (`/tokenize`, special tokens included, the document template applied as the embedder
applies it: `--template`, by default the loaded configuration's), how many of a store's texts
exceed the limit, and how many characters a token takes per source. Two readers, both read-only:
`--lance` reads the `text` column of a vector store's chunks table (every atom the store embedded);
`--instance` samples up to `--sample` items a source from an instance's catalog (paths
`<namespace>/<source>/...`), reads their bytes from its raw store, chunks them as the landing
chunks them and keeps at most `--chunks` of a source's chunks. Only counts leave the run.
"""

from __future__ import annotations

import argparse
import json
import random
import sqlite3
import statistics
import sys
import urllib.request
from collections import defaultdict
from collections.abc import Iterable, Sequence
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # repo root on path

from core.kernel.config import get_config  # noqa: E402


def tokens(text: str, port: int) -> int:
    """The server's token count of one input, special tokens included."""
    body = json.dumps({"content": text, "add_special": True}).encode("utf-8")
    req = urllib.request.Request(f"http://127.0.0.1:{port}/tokenize", data=body,
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return len(json.loads(r.read())["tokens"])


def from_lance(path: Path) -> list[str]:
    from core.typedshims.lancedb import connect

    table = connect(str(path)).open_table("chunks")
    return [str(r["text"]) for r in table.to_arrow().to_pylist() if r.get("text")]


def from_instance(root: Path, sample: int, cap: int, seed: int) -> dict[str, list[str]]:
    from core.kernel.ingest.pipeline import derive_chunks
    from core.kernel.stores.rawstore import RawStore

    data = root / "data"
    con = sqlite3.connect(f"file:{data / 'vault_catalog.sqlite'}?mode=ro", uri=True)
    try:
        rows = con.execute(
            "SELECT source_path, digest FROM vault_files WHERE active = 1").fetchall()
    finally:
        con.close()
    by_source: dict[str, list[str]] = defaultdict(list)
    for path, digest in rows:
        parts = str(path).split("/")
        if len(parts) > 2:
            by_source[parts[1]].append(str(digest))
    raw, rng, out = RawStore(data / "raw"), random.Random(seed), {}
    for source, digests in sorted(by_source.items()):
        picked = rng.sample(digests, min(sample, len(digests)))
        chunks = [c.text for d in picked for c in derive_chunks(raw.get(d))]
        out[source] = rng.sample(chunks, cap) if len(chunks) > cap else chunks
    return out


def summary(texts: Sequence[str], template: str, port: int, limit: int) -> dict[str, Any]:
    counts = [tokens(template.format(text=t), port) for t in texts]
    ys = sorted(counts)

    def q(p: float) -> int:
        return ys[min(len(ys) - 1, int(p * len(ys)))]

    ratios = [len(t) / max(1, n) for t, n in zip(texts, counts, strict=True)]
    over = [n for n in counts if n > limit]
    return {"texts": len(texts), "p50": q(0.5), "p90": q(0.9), "p99": q(0.99),
            "p999": q(0.999), "max": ys[-1] if ys else 0,
            "chars_per_token_median": round(statistics.median(ratios), 2) if ratios else None,
            "over_limit": len(over), "over_limit_share": round(len(over) / len(ys), 6) if ys else 0,
            "longest_chars": max((len(t) for t in texts), default=0)}


def main(argv: Iterable[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--lance", default="")
    ap.add_argument("--label", default="store")
    ap.add_argument("--instance", default="")
    ap.add_argument("--sample", type=int, default=2000, help="items a source (with --instance)")
    ap.add_argument("--chunks", type=int, default=5000, help="at most this many chunks a source")
    ap.add_argument("--seed", type=int, default=7)
    ap.add_argument("--port", type=int, default=8081)
    ap.add_argument("--limit", type=int, default=2048, help="the server's tokens an input")
    ap.add_argument("--template", default="", help="the embedder's document template")
    ap.add_argument("--out", default="")
    a = ap.parse_args(list(argv) if argv is not None else None)
    template = a.template or get_config().embedding.document_template
    groups = ({a.label: from_lance(Path(a.lance).expanduser())} if a.lance
              else from_instance(Path(a.instance).expanduser(), a.sample, a.chunks, a.seed))
    report = {"limit": a.limit, "template": template, "port": a.port,
              "groups": {k: summary(v, template, a.port, a.limit) for k, v in groups.items()}}
    text = json.dumps(report, indent=1)
    if a.out:
        Path(a.out).write_text(text + "\n")
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
