"""Stage one — a type computed from a value (`gestate/stage.py`).

`card:strict-forms.md` §"Decided — 2026-09-14".  What these hold: a
splice is the type its expression evaluates to, in an alias and in a
signature; the row of a kind agrees between `facts.ges` and `facts.py`;
a splice that needs what it types is refused with both names; and a
program with neither form goes through the compiler untouched.
"""

from pathlib import Path

import pytest

from gestate import facts, pipeline
from gestate.stage import StageError, _read, might_stage

ROOT = Path(__file__).resolve().parent.parent
FACTS = (ROOT / "gestate" / "facts.ges").read_text()
NOTES = (ROOT / "gestate" / "notes.ges").read_text()


def _run(program: str, main: str = "main"):
    state = pipeline.compile(FACTS + "\n" + program)
    return _read(state, main)


def test_a_splice_is_the_type_its_expression_computes():
    """`type T = $(e)` in an alias and `Set ($(e))` in a signature: the
    checker sees the type either way."""
    program = """
pair : Type
pair = TyTuple (TyCon "Int" :: TyCon "Text" :: Nil)

type Cell = $(pair)

first : Cell -> Int
first (n, t) = n

size : Set ($(pair)) -> Int
size s = length (elems s)

main : (Int, Int)
main = (first (3, "x"), size {(1, "a"), (2, "b")})
"""
    assert _run(program) == (3, 2)


def test_a_splice_between_two_things_applies_the_left_to_the_type():
    """Henri, 2026-09-14: *give `$` a fixity.*  `$` is `infixl 9`, the
    tightest infix operator, so `Set $(e) -> Int` is `(Set $(e)) -> Int`
    and a program may not redeclare it."""
    from gestate.syntax.descend import FixityError

    program = """
pair : Type
pair = TyTuple (TyCon "Int" :: TyCon "Int" :: Nil)

size : Set $(pair) -> Int
size s = length (elems s)

main : Int
main = size {(1, 2), (3, 4), (1, 2)}
"""
    assert _run(program) == 2
    with pytest.raises(FixityError, match="`\\$` has a fixed fixity"):
        pipeline.compile(FACTS + "\ninfixr 2 $\nmain : Int\nmain = 0\n")


def test_a_splice_that_is_not_a_type_is_refused():
    program = """
type T = $(kindName)
main : Int
main = 0
"""
    with pytest.raises(Exception):
        pipeline.compile(FACTS + program)


def test_a_splice_that_needs_what_it_types_is_refused_with_both_names():
    """Q7, on demand: no marker says what runs first, so a definition the
    splice needs may not itself be typed by the splice."""
    program = """
type T = $(f 1)

f : T -> Type
f x = TyCon "Int"

main : Int
main = 0
"""
    with pytest.raises(StageError, match="needs `f`, and `f` is typed by what it computes"):
        pipeline.compile(FACTS + program)


def test_the_row_of_a_kind_agrees_between_the_language_and_the_host():
    """`kindColumns` in `facts.ges` and `facts.base_columns` in the host
    name the same columns for every kind gestate ships and for the
    game's — the derivation held to the declaration it came from."""
    program = NOTES + """
markRel : Rel
markRel = Rel "mark" (Col "cell" (Range 0 8) :: Col "mark" (OneOf ("X" :: "O" :: Nil)) :: Nil) ("cell" :: Nil)

markLine : Line
markLine = Line "mark" Named ("cell" :: "mark" :: Nil) (By "cell" :: Nil)

main : List (List Text)
main = map kindColumns (lineKind (markRel :: Nil) markLine :: notesKinds)
"""
    said = [["".join(map(chr, n)) for n in cols] for cols in _run(program)]
    doc = facts.load("notes")
    mark = facts.Kind(name="mark", shape=("Named",), key=("cell",), order=(("By", "cell"),),
                      fields=(facts.Field("cell", "Number", "Must", ("Range", 0, 8)),
                              facts.Field("mark", "Word", "Must", ("OneOf", ("X", "O")))))
    assert said == [facts.base_columns(k) for k in (mark, *doc.kinds)]
    assert said[0] == ["cell", "mark"]


def test_a_program_with_neither_form_pays_a_substring_test():
    assert not might_stage("main : Int\nmain = 1\n")
    assert might_stage("type T = $(x)\n")
    assert might_stage('b = document "mark"\n')


def test_the_line_view_agrees_between_the_language_and_the_host():
    """`lineKind` in `facts.ges` and `facts.line_kind` in the host derive
    the same `Kind`s from the shipped model and lines — the derivation
    written twice, once where a reader can see it and once where the
    parser runs, and held equal."""
    said = _run(NOTES + "\nmain : List Kind\nmain = notesKinds\n")
    assert tuple(facts._kind(k) for k in said) == facts.load("notes").kinds


def test_a_relation_hanging_off_a_parent_is_typed_with_the_parents_key():
    """`document "section.voices"` is a row of the section's key and
    then the rank and the value — `relRow` reading the parent off the
    model, which `rowType` alone cannot."""
    said = _run(NOTES + """
main : List Type
main = documentRow model "section.voices" ++ documentRow model "note.manner" ++ documentRow model "bpm"
""")
    def names(term):
        head, args = term
        assert head == "TyTuple"
        return [facts._text(t[1]) for t in args]
    assert names(said[0]) == ["Text", "Int", "Text"], "section.voices: name, rank, value"
    assert names(said[1]) == ["Text", "Int", "Text", "Int", "Int", "Int", "Text"], \
        "note.manner: the note's five key columns, rank, value"
    assert said[2] == ("TyCon", [ord(c) for c in "Int"]), "bpm: one column, no tuple"

