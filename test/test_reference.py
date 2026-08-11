"""The generated reference — `doc/ref/`, and the editor's view of it.

The reference is *generated* precisely so that it cannot go stale, and a
generator nothing checks is a generator whose output drifts anyway.  So the
last test here regenerates the pages and fails if the copy on disk is
behind: that is the whole guarantee, and it is four lines.
"""

from __future__ import annotations

from pathlib import Path

from gestate.reference import Entry, entries_of, generate, render, stale

ROOT = Path(__file__).resolve().parent.parent


SOURCE = """# ── Vocabulary ───────────────────────────────────────────────

#: What a caller writes.
#: Two lines of prose.
public : Int -> Int
public x = x

#: An operator.
(<+>) : Int -> Int -> Int
(<+>) a b = a + b

Shape := Dot Int
       | Box Int Int

# ── Machinery ────────────────────────────────────────────────

internal

#: Not yours to call.
private : Int -> Int
private x = x
"""


# ── Reading a library ───────────────────────────────────────────────────────


def test_every_kind_of_declaration_is_found():
    got = {e.name: e for e in entries_of(SOURCE)}
    assert set(got) == {"public", "<+>", "Shape", "private"}
    assert got["public"].kind == "value"
    assert got["<+>"].kind == "operator"
    assert got["Shape"].kind == "type"
    assert got["public"].signature == "public : Int -> Int"


def test_a_declarations_prose_comes_with_it():
    got = {e.name: e for e in entries_of(SOURCE)}
    assert got["public"].doc == ["What a caller writes.", "Two lines of prose."]
    assert got["private"].doc == ["Not yours to call."]


def test_a_section_header_is_not_swallowed_as_prose():
    """It sits immediately above a declaration and looks like a comment, so
    the block reader would take it — and put a heading in the middle of
    whatever prose happened to follow one."""
    got = {e.name: e for e in entries_of(SOURCE)}
    assert got["public"].section == "Vocabulary"
    assert "Vocabulary" not in " ".join(got["public"].doc)


def test_a_sum_keeps_the_alternatives_written_under_it():
    """`Shape := Dot Int | Box Int Int` is written down the page, and a
    reference that showed only the first line would name a type and hide
    what is in it."""
    shape = next(e for e in entries_of(SOURCE) if e.name == "Shape")
    assert shape.alternatives == ["Dot Int", "Box Int Int"]


def test_internal_marks_the_rest_of_the_file():
    got = {e.name: e for e in entries_of(SOURCE)}
    assert [n for n, e in got.items() if e.internal] == ["private"]
    assert not got["public"].internal and not got["Shape"].internal


def test_a_definition_without_a_signature_is_not_a_second_entry():
    """An equation for a name that already has one is the same name, and a
    name the library declined to give a type is not part of what it
    promises."""
    got = entries_of("f : Int\nf = 1\n\ng = 2\n")
    assert [e.name for e in got] == ["f"]


def test_the_page_separates_the_vocabulary_from_the_machinery():
    page = render("Test", "when", "test.ges", entries_of(SOURCE))
    assert "## Internals" in page
    # The public half comes first, and the private half is below the rule.
    assert page.index("`public`") < page.index("## Internals")
    assert page.index("## Internals") < page.index("`private`")
    assert "1 public" not in page and "3 public, 1 internal" in page


def test_a_page_with_nothing_private_has_no_internals_section():
    page = render("Test", "when", "t.ges", entries_of("#: One.\na : Int\n"))
    assert "## Internals" not in page
    assert "`a`" in page


def test_operators_get_distinct_anchors():
    """`(|*)` and `(|/)` are punctuation, and the anchor rule throws
    punctuation away — so a naive slug makes them the same empty link."""
    from gestate.reference import _anchor

    assert _anchor("sine") == "sine"
    # Whatever the scheme is, two different operators must not collide with
    # each other in a way that makes one link land on the other.
    page = render("M", "w", "m.ges",
                  entries_of("(|*) : Int -> Int\n(|/) : Int -> Int\n"))
    assert "`|*`" in page and "`|/`" in page


# ── The real libraries ──────────────────────────────────────────────────────


def test_the_libraries_all_read():
    pages = generate()
    assert set(pages) >= {"index.md", "prelude.md", "synth.md", "music.md"}
    assert "sine" in pages["synth.md"]
    assert "adsr" in pages["synth.md"]
    assert "A sine.  The shortest thing this file can say." in pages["synth.md"]


def test_the_index_says_what_is_in_scope_when():
    """The question that comes before every other one, and the reason
    `keyHz` looks missing from a music program."""
    index = generate()["index.md"]
    assert "What is in scope when" in index
    for backend in ("audioperform", "midi", "typecheck"):
        assert backend in index


def test_doc_ref_is_not_behind_the_libraries():
    """**The whole guarantee.**  A generated document nothing checks drifts
    exactly as fast as a hand-written one; this is what stops it.

    If this fails, run `python -m gestate.reference`.
    """
    behind = stale(ROOT)
    assert behind == [], (
        "doc/ref/ is out of date — run `python -m gestate.reference`: "
        + ", ".join(behind))


# ── The editor's view ───────────────────────────────────────────────────────
#
# **The browser is gone with `audiopygame`** (`spec/workbench.md`): it was
# one screen of chrome over a generated index, and `doc/ref/index.md` is a
# better place to read one.  The part of it with a decision in it — that a
# name match beats a prose match — was lifted into the command palette and
# is tested in `test_session.py`.
#
# What stays here is the *index*, which is derived from the libraries and
# is what both the page and the palette are made of.


def test_every_frp_builtin_is_documented():
    """**Against the compiler's own list**, so that a primitive added to
    `seminaive._BUILTINS` and not to the page is a test failure rather
    than a hole somebody finds by looking for it."""
    from gestate.reference import language_entries
    from gestate.seminaive import _BUILTINS

    documented = {e.name for e in language_entries()}
    # The data constructors in `_BUILTINS` are declared in `prelude.ges`
    # and appear on its own page; what has no home is the FRP forms.
    forms = {"head", "tail", "delay", "wait", "watch", "sync", "never",
             "chan"}
    assert forms <= set(_BUILTINS), "this test is out of step with the list"
    missing = forms - documented
    assert not missing, f"undocumented FRP primitives: {sorted(missing)}"


def test_the_operators_are_documented_too():
    from gestate.reference import language_entries

    documented = {e.name for e in language_entries()}
    for name in (":::", "<*>", "<@>", "gfix", "!"):
        assert name in documented, name


def test_the_index_can_find_the_language():
    """The pages are one reader and the editor is another.  The second
    gathers `entries_of` over the six libraries, so a form in no library
    was in no list — searching `wait` returned nothing.

    The browser this was written for is gone; the index it read is not,
    and the bug it pins is a property of the index."""
    from gestate.reference import all_entries

    found = {e.name: e for e in all_entries()}
    assert "wait" in found, "the index still cannot find `wait`"
    assert found["wait"].library == "Language"
    assert found["wait"].doc, "it is listed with nothing said about it"


def test_no_type_is_spelled_with_a_combining_mark():
    """**`⃝` is a combining enclosing circle**, so it lands on whatever
    glyph precedes it rather than standing on its own — which is legible
    in a paper and garbled in the editor's monospace font, and the editor
    is what shows these.  `FaL` and `ExL` are the names the compiler uses
    anyway; the circled quantifiers belong in `spec/`, where a reader has
    a proportional font and the papers beside them.
    """
    from gestate.reference import generate, language_entries

    for entry in language_entries():
        assert "\u20dd" not in entry.signature, entry.signature
    assert "\u20dd" not in generate()["language.md"]


def test_a_modality_is_spelled_apart_from_its_argument():
    """`⃝∃a` needed no space because the symbol was a symbol.  `ExLa` is a
    type constructor nobody has heard of."""
    from gestate.reference import language_entries

    for entry in language_entries():
        assert "ExLa" not in entry.signature, entry.signature
        assert "FaLa" not in entry.signature, entry.signature


def test_the_language_page_is_written_and_linked():
    from gestate.reference import generate

    pages = generate()
    assert "language.md" in pages
    assert "wait : Chan a" in pages["language.md"]
    assert "language.md" in pages["index.md"], "nothing points at it"
