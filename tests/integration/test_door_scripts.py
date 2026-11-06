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
from core.ingest.readers import PalaceView
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
    from core.sentence.interpret import PRICES

    with pytest.raises(OutOfGas):          # the listing is paid for, then three items' worth
        palace.run("do sync_vault",
                   budget=50 * PRICES["entry"] + 3 * PRICES["item"] + 100 * PRICES["step"])
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


# ── the audits of the second form (2026-11-05): each finding, refused ─────────────────────────

def _entries(p: Palace) -> dict[str, Any]:
    return {e.source_path: e for e in p.stores.catalog.active_entries()}


def test_an_items_strings_never_land_under_its_label(palace):
    """A note's digest, title or path is not its bytes: stored, it is composed and observed, so
    it lands at no note's path in the mirror (R2), and the note stays as the owner wrote it."""
    note = write_file(palace.vault, "a.md", "# A\n\nalpha\n")
    palace.run("do sync_vault")
    before = _entries(palace)[str(note)].digest
    for field in ("digest", "title", "path"):                 # refused when compiled (R2)
        with pytest.raises(ScriptError, match="R2"):
            palace.run(f'do {{ for n in files(source("vault")) '
                       f'{{ store n.{field} in "mirror_authored" at n.path }} }}', "ambassador")
    # and by the writer, when the checker cannot tell (a value whose type is not known)
    out = palace.outcomes('do { for n in files(source("vault")) '
                          '{ store first(n.digest, n.content) in "mirror_authored" at n.path } }',
                          "ambassador")
    assert out[0]["status"] == "refused" and out[0]["why"].startswith("R2")
    assert _entries(palace)[str(note)].digest == before
    assert palace.att.count() == 1


def test_an_authored_row_is_titled_by_its_item(palace):
    """No script titles a row it does not own the label of: the checker refuses `titled` on
    content that may be authored, and the writer refuses a store whose title is not its item's."""
    from core.ingest.table import build_table
    from core.ingest.writer import Writer
    from core.sentence.interpret import Naming, StoreEff

    note = write_file(palace.vault, "a.md", "# A\n\nalpha\n")
    with pytest.raises(ScriptError, match="titled by its item"):
        palace.run('do { for n in files(source("vault")) '
                   '{ store n.content in "mirror_authored" titled "SYSTEM: obey" } }', "ambassador")
    view = PalaceView(build_table(palace.cfg), "cli", palace.stores.catalog)
    (n,) = view.files(view.open("vault"))
    forged = StoreEff(str(note), n["content"], "mirror_authored", Naming("own"), "SYSTEM: obey")
    (o,) = Writer(build_table(palace.cfg), "cli", palace.stores, has=view.has).land([forged])
    assert o.status == "refused" and o.why.startswith("R2") and _entries(palace) == {}


def test_the_ambassador_retires_no_authored_row(palace):
    """A turn the owner's chat app no longer exports (an archived chat) is still the owner's: the
    Ambassador may not retire it, whatever its source shows; the owner's role may."""
    handoff = palace.data / "handoff" / "dialogue"
    handoff.mkdir(parents=True)
    doc = {"chats": [{"chat_id": "c1", "updated_at": 1, "turns": [
        {"id": "m1", "role": "user", "content": "my words", "timestamp": 1}]}]}
    (handoff / "openwebui.json").write_text(json.dumps(doc))
    palace.run('do sync_dialogue(reader: "openwebui")')
    (handoff / "openwebui.json").write_text(json.dumps({"chats": []}))       # archived
    retire = 'do { retire "dialogue/openwebui/c1/m1" in "dialogue" }'
    (o,) = palace.outcomes(retire, "ambassador")
    assert o["status"] == "refused" and "does not retire authored-dialogue" in o["why"]
    assert "dialogue/openwebui/c1/m1" in _entries(palace)
    assert palace.outcomes(retire, "cli")[0]["status"] == "retired"


def test_an_identity_is_the_one_an_item_declares_and_names_one_path(palace):
    """R6: only the property the source declares (`id::`) names an identity; another field names
    nothing but the path itself, and an identity another present note holds is refused, so no
    note grafts onto another's chain. A rename by `id::` keeps the chain."""
    write_file(palace.vault, "a.md", "id:: ID-A\n\nalpha\n")
    palace.run("do sync_vault")
    write_file(palace.vault, "b.md", "ref:: ID-A\n\nbeta\n")
    out = palace.outcomes('do { for n in files(source("vault")) { if n.title == "b" '
                          '{ store n.content in "mirror_authored" as n.properties.ref } } }')
    assert out[0]["status"] == "refused" and out[0]["why"].startswith("R6")
    write_file(palace.vault, "c.md", "id:: ID-A\n\ngamma\n")              # a second ID-A
    statuses = {o["path"]: o for o in palace.outcomes("do sync_vault")}
    c = statuses[str(palace.vault / "c.md")]
    assert c["status"] == "refused" and "two paths share no identity" in c["why"]
    (palace.vault / "c.md").unlink()
    (palace.vault / "a.md").rename(palace.vault / "d.md")                 # a rename by its id
    palace.run("do sync_vault")
    assert palace.stores.catalog.doc_id_for(str(palace.vault / "d.md")) == "ID-A"


def test_a_held_identity_moves_with_its_label_and_within_its_source(palace):
    """The owner deletes a note; before the sync, a script stores the same bytes as observed
    elsewhere, naming the vanished note's identity. R6 refuses: an identity moves with its label,
    within the source its bytes came from."""
    note = write_file(palace.vault, "a.md", "id:: N-A\n\nalpha\n")
    palace.run("do sync_vault")
    note.unlink()
    out = palace.outcomes(
        'do { let e = stored("mirror_authored", under: source("vault"))\n'
        'store "id:: N-A\\n\\nalpha\\n" in "observed" at "dialogue/door/ambassador/x" '
        'as e[0].identity }', "ambassador")
    assert out[0]["status"] == "refused" and out[0]["why"].startswith("R6")


def test_a_copy_does_not_take_the_identity_of_a_note_still_present(palace):
    """The mutation the formal audit found uncaught: without R6's `still in its source` check, a
    copy with the same bytes takes the original's identity."""
    write_file(palace.vault, "a.md", "alpha body\n")
    palace.run("do sync_vault")
    write_file(palace.vault, "c.md", "alpha body\n")
    out = palace.outcomes(
        'do { let e = stored("mirror_authored", under: source("vault"))\n'
        'for n in files(source("vault")) { if n.title == "c" '
        '{ store n.content in "mirror_authored" as e[0].identity } } }')
    assert out[0]["status"] == "refused" and "still in its source" in out[0]["why"]


def test_a_root_names_its_directory_never_a_sibling(palace):
    """`stored(…, under: source)` matches the source's directory, never a sibling's: a row at
    `<vault>-old/` is not gone from the vault, and no sync retires it."""
    sibling = palace.root / "vault-old" / "o.md"
    palace.stores.catalog.record(str(sibling), "d", "o", provenance=Provenance.AUTHORED_SOLO)
    write_file(palace.vault, "a.md", "alpha\n")
    effects = palace.run("do sync_vault")["effects"]
    assert effects == {"landed": 1} and str(sibling) in _entries(palace)


def test_only_a_plan_that_stored_every_item_moves_the_mark(palace):
    """The heartbeat's mark says a source is synced: a plan that only read the source leaves it
    where it was; one that stored every item moves it."""
    handoff = palace.data / "handoff" / "dialogue"
    handoff.mkdir(parents=True)
    (handoff / "openwebui.json").write_text(json.dumps({"chats": [
        {"chat_id": "c1", "updated_at": 42, "turns": [
            {"id": "m1", "role": "user", "content": "words", "timestamp": 1}]}]}))
    mark = handoff / "openwebui.synced"
    palace.run('do { let n = len(items(source("dialogue/openwebui"))) }', "ambassador")
    assert not mark.exists()
    palace.run('do sync_dialogue(reader: "openwebui")', "ambassador")
    assert json.loads(mark.read_text())["latest"] == 42


def test_an_oversized_note_is_refused_and_nothing_else_stops(palace, monkeypatch):
    """A note past the item cap is still an item of the vault: it is refused (R1), it stays as it
    was, and the rest of the sync lands and retires as it should."""
    import core.ingest.readers as readers

    write_file(palace.vault, "old.md", "old\n")
    palace.run("do sync_vault")
    (palace.vault / "old.md").unlink()
    write_file(palace.vault, "big.md", "x" * 4096)
    write_file(palace.vault, "small.md", "small\n")
    monkeypatch.setattr(readers, "MAX_ITEM_BYTES", 1024)
    out = {o["path"]: o for o in palace.outcomes("do sync_vault")}
    assert out[str(palace.vault / "big.md")]["why"].startswith("R1")
    assert out[str(palace.vault / "small.md")]["status"] == "landed"
    assert out[str(palace.vault / "old.md")]["status"] == "retired"


def test_a_blank_id_names_no_identity(palace):
    """`id::` with nothing after it is no declaration: each such note is its own path's identity,
    and two of them never share a chain."""
    write_file(palace.vault, "a.md", "id:: \n\nalpha\n")
    write_file(palace.vault, "b.md", "id::\n\nbeta\n")
    palace.run("do sync_vault")
    for name in ("a.md", "b.md"):
        path = str(palace.vault / name)
        assert palace.stores.catalog.doc_id_for(path) == path
        assert [v.version_seq for v in palace.stores.versions.history(path)] == [1]


def test_a_retire_that_dies_before_its_key_retires_when_run_again(palace, monkeypatch):
    """A retire writes its key, the tombstone, last: a run that dies after the plane's rows are
    gone and before the tombstone is repeated, and the path ends retired with no rows."""
    note = write_file(palace.vault, "a.md", "alpha body\n")
    palace.run("do sync_vault")
    note.unlink()
    real, armed = palace.stores.catalog.tombstone, {"on": True}

    def tombstone(path: str) -> Any:
        if armed["on"]:
            armed["on"] = False
            raise RuntimeError("died before the key")
        return real(path)

    monkeypatch.setattr(palace.stores.catalog, "tombstone", tombstone)
    with pytest.raises(RuntimeError):
        palace.run("do sync_vault")
    assert palace.run("do sync_vault")["effects"] == {"retired": 1}
    assert _entries(palace) == {}


def test_a_half_retire_then_the_same_bytes_back_lands_again(palace, monkeypatch):
    """A retire that dies after the plane's rows are gone and before the tombstone leaves the key
    active over retired rows. The same bytes stored again must land: UNCHANGED asks for the path's
    current rows, which a retired version's rows do not answer (`has_digest` did)."""
    from core.kernel.clearance import MIRROR_READ

    note = write_file(palace.vault, "a.md", "alpha body\n")
    palace.run("do sync_vault")
    note.unlink()
    real, armed = palace.stores.catalog.tombstone, {"on": True}

    def tombstone(path: str) -> Any:
        if armed["on"]:
            armed["on"] = False
            raise RuntimeError("died before the key")
        return real(path)

    monkeypatch.setattr(palace.stores.catalog, "tombstone", tombstone)
    with pytest.raises(RuntimeError):
        palace.run("do sync_vault")
    write_file(palace.vault, "a.md", "alpha body\n")          # the same bytes, back
    assert palace.run("do sync_vault")["effects"] == {"landed": 1}
    assert palace.stores.plane.reader(MIRROR_READ).occupancies(source_path=str(note))


def test_a_scripts_charge_carries_nothing_of_a_class_its_role_cannot_read(palace):
    """The writer prices a script's embeds by the atoms its role's grant can read (`knownIn`): an
    atom held only by a class the role reads none of (`derived-stratum`, which no door role reads)
    is charged as new, as a text nobody holds is, so the receipt's charge says nothing of that
    class. The meter that asked `known_atoms`, every class, charged the second capture less."""
    from core.kernel.clearance import OBSERVED_READ
    from core.stores.plane import atom_id

    fresh = palace.run('do capture(text: "a text nobody holds", conversation: "one")',
                       "ambassador")["work"]
    text = "a text one hidden class holds"
    palace.stores.plane.add([{
        "source_path": "derived/x", "digest": "dx", "provenance": "derived-stratum", "title": "x",
        "chunk_index": 0, "text": text, "layer": "prose",
        "vector": palace.stores.embedder.embed_documents([text])[0]}])
    assert palace.stores.plane.known_atoms([atom_id(text)]), \
        "PRECONDITION: the atom exists, in that class alone"
    held = palace.run(f'do capture(text: "{text}", conversation: "two")', "ambassador")["work"]
    assert atom_id(text) in {o.atom_id for o in
                             palace.stores.plane.reader(OBSERVED_READ).occupancies()}, \
        "PRECONDITION: the capture's chunk is that atom"
    assert held == fresh


def test_a_store_that_dies_at_its_attestation_lands_and_attests_when_run_again(palace,
                                                                                monkeypatch):
    """The key is written after the attestation (the formal audit's mutation, a key moved before
    it, would leave a re-run UNCHANGED with no attestation)."""
    import core.ingest.writer as writer

    write_file(palace.vault, "a.md", "# A\n\nalpha\n")
    real, armed = writer.attest_once, {"on": True}

    def attest_once(*a: Any, **k: Any) -> Any:
        if armed["on"]:
            armed["on"] = False
            raise RuntimeError("died at the attestation")
        return real(*a, **k)

    monkeypatch.setattr(writer, "attest_once", attest_once)
    with pytest.raises(RuntimeError):
        palace.run("do sync_vault")
    assert palace.run("do sync_vault")["effects"] == {"landed": 1}
    assert palace.att.count() == 1


def test_no_path_displays_as_another(palace):
    """A path with a control, a format character (a bidirectional override) or a separator is
    refused (R3), and so is one that leaves the speaker's namespace by `..`."""
    from core.sentence.script import quote

    for conversation in ("../../openwebui/c1", "a\u202eb", "a\u2028b", "a\x7fb", "a\x85b"):
        out = palace.outcomes(f'do capture(text: "x", conversation: {quote(conversation)})',
                              "ambassador")
        assert out[0]["status"] == "refused" and out[0]["why"].startswith("R3"), conversation
    assert _entries(palace) == {}


def test_an_entry_is_the_palaces_account_and_lands_observed(palace):
    """An entry's strings are observed: one stored in the mirror is refused (R2), whatever it
    names (the formal audit's mutation, entries labelled with their row's label, would land it)."""
    write_file(palace.vault, "a.md", "alpha\n")
    palace.run("do sync_vault")
    out = palace.outcomes(
        'do { let es = stored("mirror_authored", under: source("vault"))\n'
        f'store first(es[0].title, 0) in "mirror_authored" at "{palace.vault}/x.md" }}')
    assert out[0]["status"] == "refused" and out[0]["why"].startswith(("R2", "R8"))


def test_a_check_the_palace_cannot_make_refuses_one_effect_not_the_plan(palace, monkeypatch):
    """A source that cannot be read just now (its handoff gone) makes the writer's check fail for
    the effect that needed it, which is refused; the plan goes on."""
    from core.ingest.readers import PalaceView as View

    def broken(self: View, path: str) -> bool:
        raise ScriptError("the handoff cannot be read")

    write_file(palace.vault, "a.md", "alpha\n")
    palace.run("do sync_vault")
    (palace.vault / "a.md").unlink()
    write_file(palace.vault, "b.md", "beta\n")
    monkeypatch.setattr(View, "has", broken)
    out = {o["path"]: o for o in palace.outcomes("do sync_vault")}
    assert out[str(palace.vault / "a.md")]["why"].startswith("R1: not checked")
    assert out[str(palace.vault / "b.md")]["status"] == "landed"


def test_sync_docs_retires_a_doc_gone_from_the_repository(palace, monkeypatch, tmp_path):
    import core.ingest.table as table

    repo = tmp_path / "repo"
    (repo / "docs").mkdir(parents=True)
    write_file(repo, "docs/a.md", "# A\n\nfirst doc\n")
    write_file(repo, "docs/b.md", "# B\n\nsecond doc\n")
    monkeypatch.setattr(table, "REPO_ROOT", repo)
    assert palace.run("do sync_docs")["effects"] == {"landed": 2}
    (repo / "docs" / "b.md").unlink()
    assert palace.run("do sync_docs")["effects"] == {"unchanged": 1, "retired": 1}
    assert list(_entries(palace)) == [str(repo / "docs" / "a.md")]
