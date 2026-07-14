"""Manifest DISTILLED → EMBEDDED + the dangling-claim guard (bp-029 Item 30).

Deterministic (HashingEmbedder + temp store). Exercises the tail end-to-end on TEMP manifests:
persist a keeper (Item 29) → flip its manifest to EMBEDDED → validate the store_ref is backed by
real curated vectors. Also validates every REAL `reference_material/` seed manifest against the v0
schema and confirms the offline build flipped NONE of them (no dangling claims land in git).
"""

from __future__ import annotations

from typing import cast

from config.loader import REPO_ROOT
from core.ingest.embed import Embedder
from core.research.criteria import Paper
from core.research.curate import (
    ingestion_errors,
    mark_manifest_embedded,
    parse_frontmatter,
    schema_errors,
    set_embedded,
)
from core.research.persist import persist_keepers
from core.research.rank import RankedPaper
from core.stores.vectorstore import VectorStore
from tests.fixtures.fakes import HashingEmbedder

DIM = 8
FULL_TEXT = "The reproducing kernel Hilbert space is the crux. " * 20

SAMPLE_MANIFEST = """---
type: reference-material
id: sample-2020
citation: "Author (2020). Title. Journal."
identifiers:
  doi: 10.9/x
  arxiv: null
  isbn: null
  url: https://doi.org/10.9/x
verification:
  state: verified
  date: 2026-07-13
  verdict: CONFIRMED
  by: web-check 2026-07-13
source_ingestion:
  state: not_fetched          # VERIFIED + DISTILLED, not yet EMBEDDED
  venue: null
  store_ref: null
  retrieved: null
authority: high
load_bearing_for:
  - "docs/design-notes/x.md#2.2: the load-bearing claim"
cited_by:
  - docs/design-notes/x.md
docs:
  - distillation.md
provenance: agent-proposed
---

# Sample

Body text preserved across the flip.
"""


def _persist_one(tmp_path, *, pid="sample-2020"):
    store = VectorStore(tmp_path / "curated.lance", dim=DIM)
    paper = Paper(source="europepmc", id=pid, title="A paper", abstract="a", year=2020,
                  venue="J", type="review", doi="10.9/x", url="u", is_preprint=False,
                  open_access=True, full_text=FULL_TEXT)
    ranked = [RankedPaper(paper=paper, relevance=0.9, evidence_tier="high", score=0.9, flags=())]
    record = persist_keepers(ranked, cast(Embedder, HashingEmbedder(DIM)), store)[0]
    return store, record


def test_sample_manifest_parses_and_passes_v0_schema():
    fm = parse_frontmatter(SAMPLE_MANIFEST)
    assert fm["type"] == "reference-material"
    assert fm["source_ingestion"]["state"] == "not_fetched"
    assert fm["source_ingestion"]["store_ref"] is None
    assert schema_errors(fm) == []
    assert ingestion_errors(fm) == []          # not_fetched + null ref → consistent


def test_flip_to_embedded_is_backed_by_real_vectors(tmp_path):
    store, record = _persist_one(tmp_path)
    manifest = tmp_path / "manifest.md"
    manifest.write_text(SAMPLE_MANIFEST, encoding="utf-8")

    mark_manifest_embedded(manifest, record, retrieved="2026-07-13")

    fm = parse_frontmatter(manifest.read_text(encoding="utf-8"))
    assert fm["source_ingestion"]["state"] == "embedded"
    assert fm["source_ingestion"]["store_ref"] == record.store_ref
    assert fm["source_ingestion"]["venue"] == "europepmc"
    assert fm["source_ingestion"]["retrieved"] == "2026-07-13"
    # No dangling claim: the store actually holds vectors for this store_ref.
    assert ingestion_errors(fm, curated_store=store) == []
    assert schema_errors(fm) == []
    # Every other block + the body survive the surgical edit.
    body = manifest.read_text(encoding="utf-8")
    assert "verification:" in body and "load_bearing_for:" in body
    assert "Body text preserved across the flip." in body


def test_dangling_embedded_claim_is_caught(tmp_path):
    store, _ = _persist_one(tmp_path)
    # A manifest that CLAIMS embedded but points at a store_ref the store does not hold.
    text = set_embedded(SAMPLE_MANIFEST, venue="europepmc", store_ref="deadbeef" * 8,
                        retrieved="2026-07-13")
    fm = parse_frontmatter(text)
    errs = ingestion_errors(fm, curated_store=store)
    assert any("no curated vectors" in e for e in errs)   # the verify-before-trust guard fires


def test_embedded_with_null_store_ref_is_caught():
    # Hand-craft the exact dangling shape: state=embedded, store_ref null.
    bad = SAMPLE_MANIFEST.replace(
        "  state: not_fetched          # VERIFIED + DISTILLED, not yet EMBEDDED",
        "  state: embedded",
    )
    fm = parse_frontmatter(bad)
    errs = ingestion_errors(fm)
    assert any("store_ref is null" in e for e in errs)


def test_not_fetched_with_a_store_ref_is_inconsistent():
    bad = SAMPLE_MANIFEST.replace("  store_ref: null", "  store_ref: abc123")
    fm = parse_frontmatter(bad)
    assert any("store_ref is set" in e for e in ingestion_errors(fm))


def test_all_real_seed_manifests_pass_schema_and_are_not_dangling():
    # The real bp-027 seed layer + moore-aronszajn: every card passes the v0 schema, and the
    # offline build flipped NONE to embedded (no dangling claim enters git).
    manifests = sorted((REPO_ROOT / "docs" / "reference_material").glob("*/manifest.md"))
    assert len(manifests) >= 10
    for m in manifests:
        fm = parse_frontmatter(m.read_text(encoding="utf-8"))
        assert schema_errors(fm) == [], f"{m} fails v0 schema"
        assert ingestion_errors(fm) == [], f"{m} has an inconsistent source_ingestion"
        assert fm["source_ingestion"]["state"] == "not_fetched", f"{m} was unexpectedly flipped"
