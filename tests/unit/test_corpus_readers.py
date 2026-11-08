"""The corpus edge readers' reductions (dn-corpus-instance §7): markup to the landing form, and the
identifiers each keeps beside it. No network: every input is a literal."""

from __future__ import annotations

import email.message
import gzip
import json
from pathlib import Path

import pytest

from edge.corpus import arxiv, gutenberg, openalex, stackexchange
from edge.corpus.common import Fetcher, html_text, tidy, wikitext
from edge.corpus.stream import item_id_ok


def test_wikitext_keeps_the_prose_and_its_links_and_drops_the_markup():
    text = """{{Short description|A field}}
'''Graph theory''' is the study of [[Graph (discrete mathematics)|graphs]], which model
[[pairwise]] relations.<ref>{{cite journal |title=On graphs |doi=10.1/xyz |arxiv=1312.0976}}</ref>
[[File:Konigsberg.png|thumb|The [[Seven Bridges]]]]
== History ==
The [[Seven Bridges of Königsberg]] problem.{{citation needed}}
{| class="wikitable"
| cell
|}
== References ==
{{reflist}}
[[Category:Graph theory]]
"""
    r = wikitext(text)
    assert r["text"].startswith("Graph theory is the study of graphs, which model")
    assert "History" in r["text"] and "Seven Bridges of Königsberg problem." in r["text"]
    assert "cell" not in r["text"] and "thumb" not in r["text"] and "reflist" not in r["text"]
    assert r["links"] == ["Graph (discrete mathematics)", "Pairwise",
                          "Seven Bridges of Königsberg"]
    assert r["cites"] == [{"doi": "10.1/xyz", "arxiv": "1312.0976", "title": "On graphs"}]
    assert not r["redirect"] and not r["disambiguation"]


def test_wikitext_names_redirects_disambiguations_and_gutenberg_templates():
    assert wikitext("#REDIRECT [[Graph theory]]")["redirect"]
    assert wikitext("'''Mercury''' may refer to:\n{{disambiguation}}")["disambiguation"]
    assert wikitext("text {{Gutenberg|no=1342|name=Pride and Prejudice}}")["gutenberg"] == [1342]


def test_html_text_breaks_blocks_and_collects_links():
    body, links = html_text('<p>A <a href="https://en.wikipedia.org/wiki/Graph_theory">graph</a>'
                            '</p><ul><li>one</li><li>two</li></ul><pre>x = 1\ny = 2</pre>')
    assert body == "A graph\n\n- one\n\n- two\n\nx = 1\ny = 2"
    assert links == ["https://en.wikipedia.org/wiki/Graph_theory"]
    assert tidy("a  b\n\n\n\nc ") == "a b\n\nc"


def test_stackexchange_links_are_classified_by_their_target():
    got = stackexchange.classify_links([
        "https://en.wikipedia.org/wiki/Planar_graph#Euler", "https://arxiv.org/abs/1703.01234v2",
        "http://dx.doi.org/10.1145/12345.67890", "https://example.org"])
    assert got == {"wikipedia": ["Planar graph"], "arxiv": ["1703.01234"],
                   "doi": ["10.1145/12345.67890"]}


def test_stackexchange_rows_read_utf16_dumps_and_mend_invalid_references(tmp_path: Path):
    f = tmp_path / "Posts.xml"
    xml = ('<?xml version="1.0" encoding="utf-8"?>\n<posts>\n'
           '  <row Id="1" PostTypeId="1" Body="&lt;p&gt;a&#x1;b&lt;/p&gt;" Title="T" />\n'
           '</posts>\n')
    f.write_bytes(xml.encode("utf-16"))
    rows = list(stackexchange.rows(f))
    assert rows == [{"Id": "1", "PostTypeId": "1", "Body": "<p>a b</p>", "Title": "T"}]


def test_openalex_rebuilds_an_abstract_and_finds_an_arxiv_twin():
    assert openalex.abstract({"graphs": [1], "Random": [0], "grow.": [2]}) == "Random graphs grow."
    assert openalex.arxiv_of({"doi": "https://doi.org/10.48550/arxiv.2101.00001"}) == "2101.00001"
    assert openalex.arxiv_of({"locations": [{"landing_page_url":
                                             "http://arxiv.org/abs/cond-mat/0106096v1"}]}) \
        == "cond-mat/0106096"
    assert openalex.arxiv_of({"doi": "https://doi.org/10.1/x"}) == ""


def test_arxiv_reads_raw_records_with_their_versions():
    xml = b"""<?xml version="1.0"?>
<OAI-PMH xmlns="http://www.openarchives.org/OAI/2.0/"><ListRecords>
<record><header><identifier>oai:arXiv.org:0704.0001</identifier></header><metadata>
<arXivRaw xmlns="http://arxiv.org/OAI/arXivRaw/"><id>0704.0001</id>
<version version="v1"><date>Mon, 2 Apr 2007 19:18:42 GMT</date></version>
<version version="v2"><date>Tue, 24 Jul 2007 20:10:27 GMT</date></version>
<title>A  title
 here</title><categories>physics.soc-ph cs.SI</categories><doi>10.1/y</doi>
<abstract>  An abstract. </abstract></arXivRaw></metadata></record>
<resumptionToken cursor="0">tok123</resumptionToken></ListRecords></OAI-PMH>"""
    recs, token, err = arxiv.records(xml)
    assert token == "tok123" and err == ""
    assert recs == [{"id": "0704.0001", "title": "A title here", "abstract": "An abstract.",
                     "categories": ["physics.soc-ph", "cs.SI"], "doi": "10.1/y", "license": "",
                     "versions": [{"v": "v1", "date": "2007-04-02"},
                                  {"v": "v2", "date": "2007-07-24"}]}]
    assert arxiv.months("2026-10", "2026-11") == [("2026-11-01", "2026-11-30"),
                                                  ("2026-10-01", "2026-10-31")]


def test_gutenberg_cuts_the_licence_and_skips_a_copyrighted_text():
    text = ("header\n*** START OF THE PROJECT GUTENBERG EBOOK X ***\nline one\nline two\n\n"
            "next para\n*** END OF THE PROJECT GUTENBERG EBOOK X ***\nfooter")
    assert gutenberg.body(text) == "line one line two\n\nnext para"
    assert gutenberg.body("This is a COPYRIGHTED Project Gutenberg eBook\n...") is None
    assert not gutenberg.prose("3.14159265358979 " * 2000)
    assert gutenberg.prose("words of a book. " * 2000)


def test_an_item_id_is_one_path_component():
    assert item_id_ok("W1234") and item_id_ok("cs-12") and item_id_ok("physics_0601001")
    assert not item_id_ok("a/b") and not item_id_ok("..") and not item_id_ok("")
    assert not item_id_ok("a..b")


def test_the_fetcher_backs_off_and_honours_retry_after(monkeypatch):
    import urllib.error

    calls: list[float] = []
    sleeps: list[float] = []

    class Resp:
        headers = {"Content-Encoding": "gzip"}

        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

        def read(self):
            return gzip.compress(json.dumps({"ok": True}).encode())

    def urlopen(req, timeout):
        calls.append(timeout)
        if len(calls) == 1:
            headers = email.message.Message()
            headers["Retry-After"] = "7"
            raise urllib.error.HTTPError(req.full_url, 429, "slow down", headers, None)
        assert req.get_header("User-agent").startswith("mind-palace-corpus/")
        return Resp()
    monkeypatch.setattr("urllib.request.urlopen", urlopen)
    monkeypatch.setattr("time.sleep", sleeps.append)
    assert Fetcher(0.0).get_json("https://example.org/x") == {"ok": True}
    assert len(calls) == 2 and 7.0 in sleeps


def test_the_fetcher_gives_up_on_a_refusal(monkeypatch):
    import urllib.error

    from edge.corpus.common import FetchError

    def urlopen(req, timeout):
        raise urllib.error.HTTPError(req.full_url, 403, "no", email.message.Message(), None)
    monkeypatch.setattr("urllib.request.urlopen", urlopen)
    with pytest.raises(FetchError, match="403"):
        Fetcher(0.0).get("https://example.org/x")


def test_a_hacker_news_thread_is_its_story_and_its_reply_tree_in_order():
    from edge.corpus import hackernews

    story = {"id": 1, "title": "A graph result", "url": "https://www.example.org/p",
             "time": 86400 * 3, "score": 5, "kids": [3, 2], "text": ""}
    comments = {2: {"id": 2, "parent": 1, "time": 86400 * 3 + 5, "kids": [4],
                    "text": "second <a href=\"https://en.wikipedia.org/wiki/Planar_graph\">x</a>"},
                3: {"id": 3, "parent": 1, "time": 86400 * 3 + 9, "text": "first"},
                4: {"id": 4, "parent": 2, "time": 86400 * 3 + 20,
                    "text": "reply to second, see https://arxiv.org/abs/2101.00001"},
                9: {"id": 9, "parent": 99, "text": "not in this thread"}}
    content, meta = hackernews.thread_of(story, comments)
    assert content == "A graph result\n(example.org)\n\nfirst\n\nsecond x\n\n" \
                      "reply to second, see https://arxiv.org/abs/2101.00001"
    assert [r[0] for r in meta["replies"]] == [3, 2, 4]          # the tree's order
    assert meta["replies"][2][1] == 2 and meta["comments"] == 3
    assert meta["links"]["wikipedia"] == ["Planar graph"] and meta["host"] == "example.org"
    assert meta["date"] == "1970-01-04"
