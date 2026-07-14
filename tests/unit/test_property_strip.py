"""Deterministic, exact property strip for body-only embeddings (bp-036 Item 13; finding-0077).

`strip_properties` removes every Logseq `key:: value` page-property line from the text handed to
the embedder, so the vector layer reflects note BODY only (the `id::` mint's uuid + `"id:: "` prefix
measurably polluted the graph, finding-0077). The owner's contract is *deterministic and exact*: a
line is a property IFF the module's `_PROP` object matches it — the SAME object parsing uses — so
strip and parse can never disagree (parse≡strip). This suite is that contract; it touches no store.
"""

from __future__ import annotations

from core.ingest.logseq import _PROP, strip_properties

# ── the core contract: parse ≡ strip ──────────────────────────────────────────────────────────

def test_removed_lines_are_exactly_the_parsed_properties():
    # The exactness guarantee: the lines strip REMOVES == the lines _PROP parses as properties.
    text = "id:: 28f36d5a\ndate:: 2026-07-11\n\nActual prose about systems.\nmore prose\n"
    kept = strip_properties(text)
    removed = [ln for ln in text.split("\n") if ln not in kept.split("\n")]
    parsed_keys = [m[0] for m in _PROP.findall(text)]
    removed_keys = [m.group(1) for ln in removed if (m := _PROP.match(ln))]
    assert removed_keys == parsed_keys == ["id", "date"]
    # and every surviving line is NOT a property
    assert all(not _PROP.match(ln) for ln in kept.split("\n"))


def test_strips_props_keeps_body():
    text = "id:: x\nThe body.\n"
    assert strip_properties(text) == "The body.\n"


# ── body preserved verbatim (the falsifier: a dropped/altered body line) ───────────────────────

def test_body_preserved_verbatim_including_tricky_lines():
    body = (
        "A paragraph with a link [[note-2026-07-11-000843]] and #tag.\n"
        "A URL http://example.com/path?q=1 stays.\n"   # `:` then `/`, not `::`
        "The time is 3::00 apparently.\n"              # 'time is 3' has a space → not a property
        "```\ncode with x::y inside\n```\n"            # 'code with x::y' has a space → not a prop
        "Unicode: café — naïve — 日本語.\n"
        "  indented prose line\n"                      # indented → not a property (§10: prose)
    )
    text = "id:: keep-out\ntags:: a, b\n" + body
    assert strip_properties(text) == body                  # every body line survives byte-for-byte


def test_indented_block_property_is_kept_as_prose():
    # §10 decision (verified against the corpus): _PROP is column-0 only, so an INDENTED `key::`
    # line is not a property and stays as body (a future block-property need is a conscious change).
    text = "id:: x\n- a bullet\n  block:: value\n"
    assert strip_properties(text) == "- a bullet\n  block:: value\n"


def test_property_value_may_contain_colons_and_is_still_removed():
    text = "source:: http://a.com/b::c\nbody\n"
    assert _PROP.match("source:: http://a.com/b::c")       # it IS a property (key then ::)
    assert strip_properties(text) == "body\n"


# ── determinism / idempotence ──────────────────────────────────────────────────────────────────

def test_idempotent():
    text = "id:: x\ndate:: y\nbody line\nsecond\n"
    once = strip_properties(text)
    assert strip_properties(once) == once                  # stripping a stripped text is a no-op


def test_deterministic():
    text = "id:: x\nsome body\n"
    assert strip_properties(text) == strip_properties(text)


# ── boundary shapes ────────────────────────────────────────────────────────────────────────────

def test_all_property_note_yields_empty_body():
    text = "id:: x\ndate:: y\ntags:: z\n"
    # every line is a property (plus the trailing empty line) → body is empty/whitespace only
    assert strip_properties(text).strip() == ""


def test_no_property_note_is_unchanged():
    text = "Just prose.\nAnother line.\nNo properties here.\n"
    assert strip_properties(text) == text


def test_empty_text():
    assert strip_properties("") == ""


def test_property_only_at_line_start_underscore_and_hyphen_keys():
    # _PROP key class is [A-Za-z0-9_-]+ — hyphen/underscore keys are props; a leading space is not.
    text = "a-b_c:: v\n prefixed:: not-a-prop\nbody\n"
    kept = strip_properties(text)
    assert "a-b_c:: v" not in kept                          # removed
    assert " prefixed:: not-a-prop" in kept                 # leading space → not a property → body
    assert "body" in kept
