"""An input the embedding server cannot take whole is cut, not refused (core/ingest/embed.py).

The server answers an input longer than its physical batch with an error rather than truncating
it, and a chunk's character budget does not bound its tokens. Every request of the embedder goes
through `embed_fitting`: a refused batch goes in halves until the refused text is alone, and that
text is cut to the longest prefix the server takes. The fake server here refuses an input longer
than a number of characters, as llama-server refuses one longer than its batch in tokens.
"""

from __future__ import annotations

import hashlib
from dataclasses import replace
from pathlib import Path
from typing import Any, cast

import pytest

from core.ingest.embed import Embedder, embed_fitting
from core.kernel.config import get_config
from tests.fixtures.embedding import DIM
from tests.fixtures.ingress import EVERY, palace_at, write_file

REFUSAL = ("input (2951 tokens) is too large to process. increase the physical batch size "
           "(current batch size: 2048)")


def _vec(text: str) -> list[float]:
    h = hashlib.sha256(text.encode("utf-8")).digest()
    return [b / 255.0 for b in h[:DIM]]


class _Server:
    """An embedding server that refuses any request holding an input longer than `limit`."""

    def __init__(self, limit: int) -> None:
        self.limit = limit
        self.calls: list[list[str]] = []

    def embed(self, model: str, inputs: list[str], *,
              keep_alive: str | int | None = None) -> list[list[float]]:
        self.calls.append(list(inputs))
        if any(len(x) > self.limit for x in inputs):
            raise RuntimeError(REFUSAL)
        return [_vec(x) for x in inputs]


def _embedder(server: _Server, *, template: str = "title: none | text: {text}") -> Embedder:
    cfg = replace(get_config().embedding, model="fake", dim=DIM, document_template=template,
                  query_template="query: {text}")
    return Embedder(client=cast("Any", server), config=cfg)


def test_a_batch_the_server_takes_is_one_request_as_before():
    server = _Server(limit=1000)
    e = _embedder(server)
    vectors = e.embed_documents(["alpha", "beta"])
    assert server.calls == [["title: none | text: alpha", "title: none | text: beta"]]
    assert vectors == [_vec("title: none | text: alpha"), _vec("title: none | text: beta")]
    assert e.cut == 0 and list(e.last_cuts) == []


def test_a_refused_text_is_cut_to_the_longest_prefix_the_server_takes():
    server = _Server(limit=120)
    e = _embedder(server)
    long = "w" * 400
    vectors = e.embed_documents(["short", long, "also short"])
    kept = 120 - len("title: none | text: ")                 # the template counts against the limit
    assert e.cut == 1 and list(e.last_cuts) == [(400, kept)]
    assert vectors[0] == _vec("title: none | text: short")
    assert vectors[1] == _vec("title: none | text: " + long[:kept])
    assert vectors[2] == _vec("title: none | text: also short")
    assert e.embed_documents([long]) == [vectors[1]]          # the same text, cut the same way
    assert e.cut == 2


def test_a_query_too_long_for_the_server_is_cut_the_same_way():
    server = _Server(limit=50)
    e = _embedder(server)
    vector = e.embed_query("q" * 200)
    assert vector == _vec("query: " + "q" * (50 - len("query: ")))
    assert e.cut == 1


def test_any_other_failure_is_raised_and_nothing_is_counted():
    class _Down:
        def embed(self, model: str, inputs: list[str], *,
                  keep_alive: str | int | None = None) -> list[list[float]]:
            raise ConnectionError("connection refused")

    e = _embedder(cast("Any", _Down()))
    with pytest.raises(ConnectionError):
        e.embed_documents(["alpha"])
    assert e.cut == 0


def test_a_server_that_takes_no_prefix_is_an_error_not_a_guess():
    server = _Server(limit=5)                                  # shorter than the template itself
    with pytest.raises(RuntimeError, match="refuses every prefix"):
        _embedder(server).embed_documents(["anything"])


def test_the_fitting_splits_a_refused_batch_instead_of_resending_it_whole():
    server = _Server(limit=10)
    texts = [f"t{i}" for i in range(8)] + ["x" * 30]
    vectors, cuts = embed_fitting(lambda batch: server.embed("m", batch), texts)
    assert len(vectors) == 9 and cuts == [(30, 10)]
    # halves down to the long text: no request repeats the whole batch after its refusal
    assert sum(1 for c in server.calls if len(c) == len(texts)) == 1


def test_a_synchronous_landing_cuts_a_text_the_server_refuses_and_says_so(tmp_path: Path):
    """On the default instance's path (embedding before the key), a note with a chunk the server
    refuses lands with the vector of its longest accepted prefix, and the receipt counts the cut;
    run again, the store is unchanged and nothing is cut."""
    p = palace_at(tmp_path)
    server = _Server(limit=300)
    p.stores.embedder = _embedder(server, template="{text}")
    write_file(p.vault, "long.md", "# L\n\n" + "z" * 900 + "\n")
    write_file(p.vault, "short.md", "# S\n\na short body\n")
    receipt = p.run("do sync_vault")
    assert receipt["effects"] == {"landed": 2} and receipt["cut"] == 1
    paths = {str(r["source_path"]) for r in p.stores.plane.all_rows(clearance=EVERY)}
    assert {Path(x).name for x in paths} == {"long.md", "short.md"}
    again = p.run("do sync_vault")
    assert again["effects"] == {"unchanged": 2} and "cut" not in again
