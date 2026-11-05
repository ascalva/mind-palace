"""The door's scripts against real stores (dn-door-language §E4, §E5, §E8; DOR-7, DOR-13 to
DOR-17): each library script lands what the first form's lander landed on the same fixtures (the
differential tests of DS-5), the writer's rules refuse what they must, a run that dies before its
key lands once when run again, and a request out of budget lands nothing."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from core.ingest.curated import ingest_curated
from core.ingest.dialogue import DialogueCapture
from core.ingest.sync import VaultSync
from core.kernel.config import REPO_ROOT
from core.kernel.provenance import Provenance
from core.sentence.interpret import OutOfGas, ScriptError
from core.stores.vectorstore import VectorStore
from tests.fixtures.door import Palace, palace_at, state_of, write_file
from tests.fixtures.embedding import DIM


@pytest.fixture
def palace(tmp_path: Path) -> Palace:
    return palace_at(tmp_path)


# ── differential: each script against the first form's lander ───────────────────────────────

def _vault_sync(p: Palace) -> VaultSync:
    return VaultSync(vault=p.vault, raw=p.stores.raw, store=p.stores.plane,
                     catalog=p.stores.catalog, embedder=p.stores.embedder,
                     attestor=p.stores.attestor, version_store=p.stores.versions)


def test_sync_vault_lands_what_the_rescan_landed_through_edits_renames_and_deletions(tmp_path):
    new, old = palace_at(tmp_path, "script"), palace_at(tmp_path, "lander")
    steps: list[Any] = [
        lambda v: (write_file(v, "a.md", "# A\n\nfirst\n"),
                   write_file(v, "pages/b.md", "beta body\n"),
                   write_file(v, "c.md", "id:: ID-C\n\ngamma\n"),
                   write_file(v, "bak/x.md", "old\n")),
        lambda v: write_file(v, "a.md", "# A\n\nsecond\n"),
        lambda v: (v / "pages/b.md").rename(v / "pages/b2.md"),       # a rename keeps the chain
        lambda v: (v / "c.md").unlink(),                              # a deletion retires
        lambda v: write_file(v, "a.md", "# A\n\nfirst\n"),                # a revert is a version
    ]
    for step in steps:
        step(new.vault)
        step(old.vault)
        new.run("do sync_vault")
        _vault_sync(old).rescan()
        assert state_of(new) == state_of(old)
    assert new.run("do sync_vault")["effects"] == {"unchanged": 2}   # nothing lands twice


def test_sync_dialogue_lands_what_the_turn_capture_landed(tmp_path):
    new, old = palace_at(tmp_path, "script"), palace_at(tmp_path, "lander")
    doc = {"chats": [{"chat_id": "c1", "updated_at": 7, "turns": [
        {"id": "m1", "role": "user", "content": "my own words", "timestamp": 1_700_000_000},
        {"id": "m2", "role": "assistant", "content": "the model's words",
         "timestamp": 1_700_000_100}]}]}
    for p in (new, old):
        handoff = p.data / "handoff" / "dialogue"
        handoff.mkdir(parents=True)
        (handoff / "openwebui.json").write_text(json.dumps(doc))
    new.run('do sync_dialogue(reader: "openwebui")')
    cap = DialogueCapture(raw=old.stores.raw, store=old.stores.plane, embedder=old.stores.embedder,
                          catalog=old.stores.catalog, attestor=old.stores.attestor)
    from datetime import UTC, datetime
    turns: list[dict[str, Any]] = doc["chats"][0]["turns"]   # type: ignore[index]
    for t in turns:
        at = datetime.fromtimestamp(t["timestamp"], UTC).isoformat(timespec="seconds")
        cap.capture_turn(t["content"], conversation="openwebui/c1", turn_id=t["id"],
                         role=t["role"], at=at)
    assert state_of(new) == state_of(old)
    labels = {e.source_path: str(e.provenance) for e in new.stores.catalog.active_entries()}
    assert labels == {"dialogue/openwebui/c1/m1": "authored-dialogue",
                      "dialogue/openwebui/c1/m2": "observed"}
    mark = json.loads((new.data / "handoff" / "dialogue" / "openwebui.synced").read_text())
    assert mark["latest"] == 7                     # the heartbeat's cursor, once it all landed


def test_a_bare_sync_dialogue_lands_every_readers_turns(palace):
    """The coalescing row's request (`do sync_dialogue`, the MCP's alias) names no reader: it
    syncs every one the script names; a reader by name syncs that one."""
    handoff = palace.data / "handoff" / "dialogue"
    handoff.mkdir(parents=True)
    for reader, chat, turn in (("openwebui", "c1", "m1"), ("opencode", "s1", "u1")):
        (handoff / f"{reader}.json").write_text(json.dumps({"chats": [
            {"chat_id": chat, "updated_at": 1, "turns": [
                {"id": turn, "role": "user", "content": f"{reader} words", "timestamp": 1}]}]}))
    assert palace.run('do sync_dialogue(reader: "opencode")')["effects"] == {"landed": 1}
    assert palace.run("do sync_dialogue")["effects"] == {"landed": 1, "unchanged": 1}
    paths = sorted(e.source_path for e in palace.stores.catalog.active_entries())
    assert paths == ["dialogue/opencode/s1/u1", "dialogue/openwebui/c1/m1"]


def test_ingest_doc_lands_what_the_curated_lane_landed(tmp_path):
    new, old = palace_at(tmp_path, "script"), palace_at(tmp_path, "lander")
    rel = "docs/design-notes/dn-door-language.md"
    new.run(f'do ingest_doc(path: "{rel}")')
    ingest_curated([Path(REPO_ROOT) / rel], old.stores.raw, old.stores.plane, old.stores.embedder,
                   old.stores.catalog, repo_root=Path(REPO_ROOT), attestor=old.stores.attestor)
    assert state_of(new) == state_of(old)


# ── the writer's rules ──────────────────────────────────────────────────────────────────────

def test_a_capture_is_observed_in_the_speakers_own_namespace(palace):
    out = palace.outcomes('do capture(text: "remember this", conversation: "tea")', "ambassador")
    assert out[0]["status"] == "landed"
    (entry,) = palace.stores.catalog.active_entries()
    assert entry.source_path.startswith("dialogue/door/ambassador/tea/")
    assert str(entry.provenance) == "observed"


@pytest.mark.parametrize("script, rule", [
    # R3: the Ambassador writes only its own prefix
    ('{ store "x" in "observed" at "dialogue/door/cli/t/1" }', "R3"),
    # R8: a path in a source's space takes only that source's items
    ('{ store "x" in "dialogue" at "dialogue/openwebui/c1/m9" }', "R8"),
])
def test_the_writer_refuses_by_rule_and_lands_the_rest(palace, script, rule):
    out = palace.outcomes(f"do {script}", "ambassador")
    assert out[0]["status"] == "refused" and out[0]["why"].startswith(rule)
    assert palace.stores.catalog.active_entries() == []


def test_authored_bytes_land_only_where_they_were_written(palace):
    write_file(palace.vault, "a.md", "alpha\n")
    out = palace.outcomes('do { for n in files(source("vault")) '
                          '{ store n.content in "mirror_authored" at n.path + ".copy" } }')
    assert out[0]["status"] == "refused" and out[0]["why"].startswith("R4")


def test_a_held_label_is_never_replaced(palace):
    palace.outcomes('do capture(text: "a", conversation: "c")')
    path = palace.stores.catalog.active_entries()[0].source_path
    palace.stores.catalog.record(path, "d", "t", provenance=Provenance.AUTHORED_DIALOGUE)
    out = palace.outcomes('do capture(text: "a", conversation: "c")')
    assert out[0]["status"] == "refused" and out[0]["why"].startswith("R5")


def test_an_identity_moves_only_with_its_bytes(palace):
    write_file(palace.vault, "a.md", "alpha\n")
    write_file(palace.vault, "b.md", "beta\n")
    palace.run("do sync_vault")
    out = palace.outcomes('do { for n in files(source("vault")) { if n.title == "a" '
                          '{ store n.content in "mirror_authored" at n.path as "graft" } } }')
    assert out == []                    # a held path keeps its identity: nothing to change
    write_file(palace.vault, "c.md", "gamma\n")
    held = [e for e in palace.stores.catalog.active_entries() if e.source_path.endswith("a.md")]
    out = palace.outcomes(
        'do { let a = stored("mirror_authored", under: source("vault"))\n'
        'for n in files(source("vault")) { if n.title == "c" '
        '{ store n.content in "mirror_authored" as a[0].identity } } }')
    assert out[0]["status"] == "refused" and out[0]["why"].startswith("R6"), held


def test_retire_only_reconciles(palace):
    note = write_file(palace.vault, "a.md", "alpha\n")
    palace.run("do sync_vault")
    out = palace.outcomes(f'do {{ retire "{note}" in "mirror_authored" }}')
    assert out[0]["status"] == "refused" and out[0]["why"].startswith("R7")
    note.unlink()
    out = palace.outcomes(f'do {{ retire "{note}" in "mirror_authored" }}')
    assert out[0]["status"] == "retired"


def test_a_link_never_replaces_the_owners_edge(palace):
    write_file(palace.vault, "a.md", "alpha\n")
    write_file(palace.vault, "b.md", "beta\n")
    palace.run("do sync_vault")
    out = palace.outcomes('do link(a: "a", b: "b", relation: "supports")', "ambassador")
    assert out[0]["status"] == "linked"
    (edge,) = palace.stores.edges.all()     # type: ignore[union-attr]
    assert edge.provenance == "interpreted"
    palace.stores.edges.add(edge.u, edge.v, sign=edge.sign,  # type: ignore[union-attr]
                            rel_type="contradicts", provenance="authored-solo")
    out = palace.outcomes('do link(a: "a", b: "b", relation: "contradicts")', "ambassador")
    assert out[0]["status"] == "refused" and out[0]["why"].startswith("R5")


def test_a_run_enqueues_its_job_with_bounded_arguments(palace):
    palace.run("do relate(pairs: 7)")
    assert palace.jobs == [("relate", {"pairs": 7})]
    out = palace.outcomes('do { run "relate" with pairs: 99 }')
    assert out[0]["status"] == "refused"


# ── crash convergence (DOR-7, DOR-16) and the budget (§E10) ─────────────────────────────────

def test_a_store_that_dies_before_its_key_lands_once_when_run_again(palace, monkeypatch):
    note = write_file(palace.vault, "a.md", "# A\n\nthe first version\n")
    real, armed = palace.stores.catalog.record, {"on": True}

    def record(*a: Any, **k: Any) -> Any:
        if armed["on"]:
            armed["on"] = False
            raise RuntimeError("died before the key")
        return real(*a, **k)
    monkeypatch.setattr(palace.stores.catalog, "record", record)
    with pytest.raises(RuntimeError):
        palace.run("do sync_vault")
    assert palace.stores.catalog.get(str(note)) is None            # the prefix: no key
    assert [v.version_seq for v in palace.stores.versions.history(str(note))] == [1]
    assert palace.run("do sync_vault")["effects"] == {"landed": 1}
    assert [v.version_seq for v in palace.stores.versions.history(str(note))] == [1]
    assert palace.att.count() == 1
    assert palace.run("do sync_vault")["effects"] == {"unchanged": 1}


def test_after_a_plane_reset_the_key_lets_the_rows_land_again(palace, tmp_path):
    write_file(palace.vault, "a.md", "alpha body\n")
    palace.run("do sync_vault")
    palace.stores.plane = VectorStore(tmp_path / "fresh-plane", dim=DIM)
    assert palace.run("do sync_vault")["effects"] == {"landed": 1}


def test_a_request_out_of_budget_lands_nothing(palace):
    for i in range(5):
        write_file(palace.vault, f"n{i}.md", f"note {i} " * 50)
    with pytest.raises(OutOfGas):
        palace.run("do sync_vault", budget=200)
    assert palace.stores.catalog.active_entries() == []
    assert palace.stores.raw is not None


def test_a_read_stops_at_the_item_that_runs_the_budget_out(palace, monkeypatch):
    """A source is read item by item, each charged as it arrives: a request out of budget stops
    reading there, not after the whole source has been opened and parsed."""
    from core.ingest.readers import PalaceView

    for i in range(50):
        write_file(palace.vault, f"n{i:02}.md", f"note {i}\n")
    parsed: list[str] = []
    real = PalaceView._markdown

    def counted(self: PalaceView, source: Any, path: Path) -> Any:
        parsed.append(str(path))
        return real(self, source, path)

    monkeypatch.setattr(PalaceView, "_markdown", counted)
    with pytest.raises(OutOfGas):
        palace.run("do sync_vault", budget=200)
    assert 0 < len(parsed) < 50


def test_the_writes_and_the_embeds_are_priced_before_any_is_paid(palace, monkeypatch):
    """A plan is priced before the writer pays for any of it: a budget the evaluation fits but
    the writes do not lands nothing; one the writes fit but the embeds do not embeds nothing."""
    from core.sentence.interpret import PRICES

    for i in range(5):                       # several chunks a note: the embeds outweigh the read
        write_file(palace.vault, f"n{i}.md",
                   "\n\n".join(f"note {i} paragraph {j} " * 40 for j in range(4)))
    calls: list[int] = []
    real = palace.stores.embedder.embed_documents

    def counted(texts: list[str]) -> Any:
        calls.append(len(texts))
        return real(texts)

    monkeypatch.setattr(palace.stores.embedder, "embed_documents", counted)
    reading = 5 * (PRICES["item"] + 16 * PRICES["kib"] + PRICES["effect"]) + 1000 * PRICES["step"]
    for budget, at in ((reading, "at write"), (reading + 5 * PRICES["write"], "at embed")):
        with pytest.raises(OutOfGas, match=at):
            palace.run("do sync_vault", budget=budget)
        assert calls == [] and palace.stores.catalog.active_entries() == []


def test_a_script_may_not_open_a_source_its_role_may_not(palace):
    with pytest.raises(ScriptError):
        palace.run('do { let s = source("nope") }')
