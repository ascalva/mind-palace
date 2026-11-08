"""The `[ingestion.corpus]` section (dn-corpus-instance §3.1): off and sourceless by default, its
root a path the instance writes, under a named instance's own root and never outside it, its
source names single path segments. Every case runs in a temporary config directory; the live
overlay is never read."""

from __future__ import annotations

from pathlib import Path

import pytest

from core.kernel.config import loader
from core.kernel.config.loader import CorpusIngestConfig, namespaces_of, shared

CORPUS = loader.REPO_ROOT / "config" / "instances" / "corpus.toml"


def _isolated(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setattr(loader, "_CONFIG_DIR", tmp_path)
    monkeypatch.setattr(loader, "_INSTANCE_OVERLAY", tmp_path / "ouroboros.toml")
    monkeypatch.setattr(loader, "_LEGACY_OVERLAY", tmp_path / "local.toml")
    monkeypatch.setattr(loader, "LEVERS_OVERLAY", tmp_path / "levers.toml")


def test_the_default_instance_reads_no_corpus(monkeypatch, tmp_path):
    _isolated(monkeypatch, tmp_path)
    c = loader.load_config().ingestion.corpus
    assert not c.enabled and c.sources == ()
    assert c.root == loader.REPO_ROOT / "data" / "corpus"


def test_the_corpus_overlay_is_a_named_instance_whose_streams_lie_under_its_root(
        monkeypatch, tmp_path):
    _isolated(monkeypatch, tmp_path)
    monkeypatch.setenv(loader.OVERLAY_ENV, str(CORPUS))
    cfg = loader.load_config()
    assert cfg.instance.id == "corpus"
    c = cfg.ingestion.corpus
    assert c.enabled and c.sources == ("wikipedia", "openalex", "arxiv", "stackexchange",
                                       "gutenberg")
    assert c.root == cfg.instance.root / "sources"
    ns = namespaces_of(cfg)
    assert c.root in ns.paths, "the streams are written, so they are a namespace"
    assert all(str(p).startswith(str(cfg.instance.root)) for p in ns.paths)
    assert not cfg.ingestion.vault.enabled and not cfg.ingestion.transcripts.enabled
    assert not cfg.ingestion.code.enabled


def test_the_corpus_instance_shares_nothing_with_the_default_chain(monkeypatch, tmp_path):
    _isolated(monkeypatch, tmp_path)
    ouroboros = namespaces_of(loader.load_config())
    monkeypatch.setenv(loader.OVERLAY_ENV, str(CORPUS))
    assert shared(namespaces_of(loader.load_config()), ouroboros) == []


def test_a_named_instance_may_not_move_its_streams_out_of_its_root(monkeypatch, tmp_path):
    _isolated(monkeypatch, tmp_path)
    for root in ("/tmp/elsewhere", "../escape"):
        named = tmp_path / "x.toml"
        named.write_text(f'[instance]\nid = "x"\n[ingestion.corpus]\nenabled = true\n'
                         f'root = "{root}"\nsources = ["s"]\n')
        monkeypatch.setenv(loader.OVERLAY_ENV, str(named))
        with pytest.raises(loader.InstanceOverlayError, match="leaves the instance's root"):
            loader.load_config()


def test_a_source_name_is_one_segment_and_a_batch_at_least_one():
    for bad in ("Wiki", "a/b", "a.b", "", "x" * 40):
        with pytest.raises(ValueError, match="not a source name"):
            CorpusIngestConfig(sources=(bad,))
    with pytest.raises(ValueError, match="repeat"):
        CorpusIngestConfig(sources=("a", "a"))
    with pytest.raises(ValueError, match="at least one"):
        CorpusIngestConfig(batch=0)
    assert CorpusIngestConfig(sources=("wikipedia", "stack-exchange")).batch == 2000


def test_the_table_opens_a_stream_per_source_to_the_corpus_role_alone(monkeypatch, tmp_path):
    from core.ingest.table import build_table

    _isolated(monkeypatch, tmp_path)
    monkeypatch.setenv(loader.OVERLAY_ENV, str(CORPUS))
    cfg = loader.load_config()
    t = build_table(cfg)
    s = t.sources["corpus/openalex"]
    assert s.kind == "stream" and s.location == cfg.ingestion.corpus.root / "openalex"
    assert s.readers == frozenset({"corpus", "cli"}) and t.source_labels(s.name) == {"observed"}
    assert t.may_write("corpus", "observed", "corpus/openalex/W1")
    assert not t.may_write("corpus", "observed", "dialogue/x")
    assert not t.may_write("corpus", "mirror_authored", "corpus/openalex/W1")
    assert t.roles["corpus"].retires == frozenset()
    monkeypatch.delenv(loader.OVERLAY_ENV)
    assert not any(n.startswith("corpus/") for n in build_table(loader.load_config()).sources)
