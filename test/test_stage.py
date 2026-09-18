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


def test_stage_one_is_items_and_never_text(monkeypatch):
    """`card:strict-forms.md` §"Read — 2026-09-18", item 1, its
    postcondition: *a program with a splice compiles without the
    compiler reading its own source text a second time, and the stage
    cannot wait on the front end's lock because it never takes it.*
    Every door that takes a text is made to refuse stage one's, and the
    seam registry gains nothing of stage one's; and a stage-one type
    error is reported at the splice's own line, which the appended text
    of the old road put past the end of the file."""
    from gestate import syntax

    def refusing(door):
        def refuse(source, *a, **k):
            assert "__stage_" not in source, "stage one went through a text door"
            return door(source, *a, **k)
        return refuse

    for name in ("_compile", "compile", "analyse", "_analyse"):
        monkeypatch.setattr(pipeline, name, refusing(getattr(pipeline, name)))
    monkeypatch.setattr(syntax, "note_seam",
                        refusing(syntax.note_seam))
    before = set(syntax._SEAMS)
    program = """
pair : Type
pair = TyTuple (TyCon "Int" :: TyCon "Text" :: Nil)

type Cell = $(pair)

first : Cell -> Int
first (n, t) = n

main : Int
main = first (7, "x")
"""
    assert _run(program) == 7
    assert not [k for k in set(syntax._SEAMS) - before if "__stage_" in k]

    bad = FACTS + "\n\ntype T = $(kindName)\n\nmain : Int\nmain = 0\n"
    line = bad[:bad.index("$(kindName)")].count("\n")
    with pytest.raises(Exception) as got:
        pipeline.compile(bad)
    assert f"while checking `__stage_0__` (at {line}:" in str(got.value)


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




# ── The reflector — `card:types-in-the-host.md` ─────────────────────────────

def _reify(term):
    """`unreflect`: `_type_val` then the checker's own reader, the value
    as the type the checker would see."""
    from gestate.stage import unreflect
    return unreflect(term)


def test_a_ground_type_reflected_then_reified_is_itself():
    """The theory's soundness pair, held by a test: on every closed type
    the compiler's grammar has, reflect then reify is the identity —
    the type the checker infers, read as a `Type` value, read back, is
    the same type.  The list is the six the game's compile asks zero
    changes at, plus the forms `Type` has a constructor for."""
    from gestate.stage import reflect
    from gestate.types import TApp, TCon, TFun, TInt, mk_tuple

    Int, Text, Char = TCon("Int"), TCon("Text"), TCon("Char")
    ground = [
        Int, TCon("Tuple0"), TCon("String"), mk_tuple([Int, Text]),
        mk_tuple([Int, Int, Int]), Char,
        TApp(TCon("List"), Char), TApp(TCon("Set"), mk_tuple([Int, Text])),
        TFun(Int, TFun(Text, TApp(TCon("Sig"), Int))),
        TApp(TCon("Cyclic"), TInt(12)),
        TApp(TApp(TCon("Bounded"), TInt(4)), TInt(30)),
        mk_tuple([mk_tuple([Int, Int]), TApp(TCon("List"), mk_tuple([Char, Int]))]),
    ]
    for t in ground:
        assert _reify(reflect(t)) == t, t


def test_a_type_with_a_variable_is_refused_by_the_reflector():
    """A scheme cannot be said in `Type`: it has no binder.  The refusal
    names the place, so a reader of a polymorphic definition's type gets
    a line and not `()`.  A reader whose answer is *about* the variable
    asks for it by name and gets a `TyVar`, which the reifier refuses
    on the way back: nothing binds it."""
    from gestate.show import show_type
    from gestate.stage import reflect
    from gestate.types import TCon, TFun, TVar

    with pytest.raises(StageError, match=r"a type with a variable.* in `id` \(at 3:0\)"):
        reflect(TFun(TVar(7), TVar(7)), place=" in `id` (at 3:0)")
    said = reflect(TFun(TVar(7), TCon("Int")), variables=True)
    assert said == ("TyFun", ("TyVar", show_type(TVar(7))), ("TyCon", "Int"))
    with pytest.raises(StageError, match="a variable cannot be a type"):
        _reify(("TyVar", "a"))


def test_a_monotone_arrow_is_refused_by_the_reflector():
    """`TyFun` has no monotone flag; a value that forgot `~>` would reify
    to `->`, which is the other function space."""
    from gestate.stage import reflect
    from gestate.types import TCon, TFun

    with pytest.raises(StageError, match="monotone arrow"):
        reflect(TFun(TCon("Int"), TCon("Int"), None, True))


def test_a_ground_types_constructors_reflect_with_the_parameters_filled_in():
    """The second reflector: what a type is made of, at one ground
    instantiation, in declaration order — `Maybe Int`'s `Just` holds an
    `Int`, not an `a`."""
    from gestate.declarations import classify
    from gestate.stage import reflect_data
    from gestate.syntax import parse
    from gestate.types import TApp, TCon, mk_tuple

    cons = classify(parse("Pair a b := Pair a b")).cons
    Int, Text = TCon("Int"), TCon("Text")
    assert reflect_data(TApp(TCon("Maybe"), Int), cons) == [
        ("Con", "Nothing", []), ("Con", "Just", [("TyCon", "Int")])]
    assert reflect_data(TApp(TApp(TCon("Pair"), Int), Text), cons) == [
        ("Con", "Pair", [("TyCon", "Int"), ("TyCon", "Text")])]
    assert reflect_data(mk_tuple([Int, Int]), cons) == []
    assert reflect_data(TCon("Float"), cons) == []


# ── Reader 4: what `sound` carries, by the rule ─────────────────────────────

def _frame(payload: str, decls: str = ""):
    from gestate.audio import frame_of
    from gestate.declarations import classify
    from gestate.syntax import parse

    program = classify(parse(decls + "\nx : " + payload + "\nx = x\n"))
    sig = next(sc.sig_type for sc in program.scs if sc.name == "x")
    return frame_of(sig, program.cons)


def test_the_frame_rule_counts_channels_off_the_type():
    """`Float` is one; a tuple of `Float`s is one per component; a record
    with one constructor of `Float`s is one per field — decided in
    `rules.ges`, read back as a count."""
    assert _frame("Float") == 1
    assert _frame("(Float, Float)") == 2
    assert _frame("Stereo", "Stereo := Stereo Float Float") == 2
    assert _frame("Quad", "Quad := Quad Float Float Float Float") == 4


def test_the_frame_rule_refuses_what_is_not_a_frame_and_says_which_part():
    from gestate.audio import AudioError

    with pytest.raises(AudioError, match=r"component 1 is a `Int`"):
        _frame("(Float, Int)")
    with pytest.raises(AudioError, match=r"`Frame` cannot be an output frame: field 1 is a `Int`"):
        _frame("Frame", "Frame := Frame Float Int")
    with pytest.raises(AudioError, match=r"it has no fields"):
        _frame("Unit", "Unit := Unit")
    with pytest.raises(AudioError, match=r"`Two` has 2 constructors"):
        _frame("Two", "Two := A Float | B Float")
    with pytest.raises(AudioError, match=r"`sound` is a `Sig List Float`"):
        _frame("List Float")


# ── Reader 5: the flatness judge, by the rule ───────────────────────────────

def test_the_closure_of_a_type_is_every_declared_type_it_reaches():
    from gestate.declarations import classify
    from gestate.stage import reflect_closure
    from gestate.syntax import parse
    from gestate.types import TApp, TCon

    cons = classify(parse("Deep := Deep (Maybe (List Int))")).cons
    table = dict(reflect_closure(TCon("Deep"), cons))
    assert set(table) >= {"Deep", "Maybe", "List"}
    assert table["Deep"] == [("Con", "Deep", [("TyApp", ("TyCon", "Maybe"),
                                                 ("TyApp", ("TyCon", "List"), ("TyCon", "Int")))])]
    assert table["Maybe"][1] == ("Con", "Just", [("TyApp", ("TyCon", "List"), ("TyCon", "Int"))])


def test_a_recursive_type_is_said_to_be_recursive_at_its_field():
    """The old judge looped for ever composing this sentence; the rule
    says which field, and that it is the type itself."""
    from gestate.declarations import classify
    from gestate.syntax import parse
    from gestate.types import TCon, is_flat, why_not_flat

    cons = classify(parse("Tree := Leaf | Node Tree Tree")).cons
    assert not is_flat(TCon("Tree"), cons)
    assert why_not_flat(TCon("Tree"), cons) == (
        "a data type whose field Tree is recursive, so a value of it is a "
        "chain of heap cells whose length is a run-time fact")


# ── The calculus, `spec/types.md` §8 — stability and the phase rule ─────────


def test_staging_swaps_the_sites_and_touches_nothing_else():
    """Kovács's stability and strictness, for the tree: in a sited
    program every unsited item comes out the very object it went in as,
    and nothing else is rewritten — no inlining, no normalisation; and
    in the staged program no site remains, which is Allais's phase rule
    held by a refusal rather than an index."""
    from gestate.pipeline import _analyse_module, _lower, _merge_prelude
    from gestate.stage import _sites, staged
    from gestate.syntax import parse
    from gestate.syntax.ast import VModule

    facts = _merge_prelude(FACTS)           # the prelude in front, as every compile has
    program = parse("""
pair : Type
pair = TyTuple (TyCon "Int" :: TyCon "Text" :: Nil)

type Cell = $(pair)

first : Cell -> Int
first (n, t) = n

main : Int
main = first (7, "x")
""")
    items = list(program.items)
    head = list(facts.items)
    out, _values = staged(
        items, lambda its: _lower(_analyse_module(VModule(head + list(its)),
                                                  typecheck=True)))
    sited = [i for i, item in enumerate(items) if _sites(item)]
    assert sited == [items.index(next(i for i in items if getattr(i, "name", "") == "Cell"))]
    for i, item in enumerate(items):
        if i not in sited:
            assert out[i] is item, f"item {i} was rewritten though it holds no site"
    assert not any(_sites(item) for item in out), "a site survived staging"
