"""`gestate/specialise.py` — a constrained definition, in a synth.

The pass exists for one sentence in `audiograph`: *needs the dictionary
`__dict_Ord_Float__`, so it is polymorphic.  The fragment is monomorphic.*
Before it, `clamp : (Ord a) => a -> a -> a -> a` compiled fine and then
could not be *used* by an audio program — the same definition written at
`Float` was accepted, and the call site read identically either way.

So the tests come in two halves: the copies are made and are right (which
is ordinary compilation), and a program that uses one extracts to a graph
(which is the reason).
"""

from __future__ import annotations

from gestate.audioperform import graph_of
from gestate.pipeline import _analyse, evaluate

CLAMP = """clamp : (Ord a) => a -> a -> a -> a
clamp lo hi x = case x < lo of
    True -> lo
    False -> case hi < x of
        True -> hi
        False -> x

"""


def _names(source: str) -> dict:
    """Every supercombinator, by name, as `(arity, params, sig)`."""
    analysis = _analyse(source, typecheck=True, prelude=True)
    return {str(n): (a, list(l.params), s) for n, a, l, s in analysis.scs}


# ── The copies ───────────────────────────────────────────────────────────────


def test_a_constrained_function_gets_one_copy_per_instantiation():
    src = CLAMP + """cut : Float -> Float
cut x = clamp 0.0 1.0 x

pick : Int -> Int
pick n = clamp 0 127 n

main : Int
main = pick 200
"""
    scs = _names(src)
    assert "clamp#Ord_Float#Eq_Float" in scs
    assert "clamp#Ord_Int#Eq_Int" in scs
    # `Ord` carries `Eq` as a superclass, so there are two dictionaries and
    # the copy is named for both.
    assert scs["clamp#Ord_Float#Eq_Float"][1] == ["lo", "hi", "x"]
    assert str(scs["clamp#Ord_Float#Eq_Float"][2]) == \
        "(Float -> (Float -> (Float -> Float)))"
    assert str(scs["clamp#Ord_Int#Eq_Int"][2]) == \
        "(Int -> (Int -> (Int -> Int)))"


def test_the_original_stays_for_callers_that_are_still_polymorphic():
    """A copy is an addition, not a replacement.

    `length` and `elem` take dictionaries from their own callers, and
    ordinary compiled code passes them perfectly well — the fragment is
    the only place that cannot.
    """
    scs = _names(CLAMP + "main : Int\nmain = clamp 0 9 20\n")
    assert scs["clamp"][1][:2] == ["_g0", "_g1"]


def test_one_copy_however_many_call_sites():
    src = CLAMP + """main : Int
main = clamp 0 9 20 + clamp 0 9 30 + clamp 0 9 40
"""
    scs = _names(src)
    assert len([n for n in scs if n.startswith("clamp#")]) == 1


def test_a_dictionary_that_is_not_a_constant_is_left_alone():
    """`Eq (List a)` takes the element's dictionary, so the call site
    *builds* one — an application, not a global, and not one answer."""
    src = """same : (Eq a) => a -> a -> Bool
same x y = x == y

main : String
main = show (same [1, 2] [1, 2])
"""
    scs = _names(src)
    assert "same" in scs and scs["same"][1][:1] == ["_g0"]
    assert not any(n.startswith("same#") for n in scs)
    assert evaluate(src, prelude=True) == "True"


def test_a_recursive_constrained_function_terminates():
    """The copy is registered before its body is walked, so the recursive
    call inside it finds the copy rather than asking for another."""
    src = """countDown : (Ord a, Num a) => a -> Int
countDown x = case x < 1 of
    True -> 0
    False -> 1 + countDown (x - 1)

main : Int
main = countDown 5
"""
    scs = _names(src)
    assert len([n for n in scs if n.startswith("countDown#")]) == 1
    assert evaluate(src, prelude=True) == "5"


# ── The copies compute the right thing ───────────────────────────────────────


def test_the_copies_agree_with_the_definition_at_both_types():
    src = CLAMP + """main : (Float, Int)
main = (clamp 0.0 1.0 5.0, clamp 0 127 (0 - 5))
"""
    _names(src)                                   # it compiles
    for expr, ty, want in [("clamp 0.0 1.0 5.0", "Float", "1.0"),
                           ("clamp 0.0 1.0 (0.0 - 2.0)", "Float", "0.0"),
                           ("clamp 0.0 1.0 0.25", "Float", "0.25"),
                           ("clamp 0 127 200", "Int", "127"),
                           ("clamp 0 127 (0 - 5)", "Int", "0"),
                           ("clamp 0 127 64", "Int", "64")]:
        got = evaluate(CLAMP + f"main : {ty}\nmain = {expr}\n", prelude=True)
        assert got == want, f"{expr} gave {got}"


def test_a_constrained_function_over_a_class_the_program_declared():
    """Not only the built-in classes: the dictionary is a constant
    whatever class made it."""
    src = """class Size a where
    size : a -> Int

instance Size Bool where
    size b = 1

instance Size (List b) where
    size xs = length xs

twice : (Size a) => a -> Int
twice x = size x + size x

main : Int
main = twice [1, 2, 3] + twice True
"""
    scs = _names(src)
    assert any(n.startswith("twice#Size_") for n in scs)
    assert evaluate(src, prelude=True) == "8"


# ── The reason: a synth may use one ──────────────────────────────────────────


def test_a_constrained_function_is_in_the_static_fragment():
    """The whole point.  Without the pass this is `needs the dictionary
    __dict_Ord_Float__, so it is polymorphic`, reported against a
    definition the author never wrote a dictionary into."""
    src = """cut : Float -> Float
cut x = clamp 0.0 1.0 x

sound : Sig Float
sound = map cut (sine 220.0)
"""
    graph = graph_of(src, "", rate=8000)
    assert graph.nodes


def test_the_synthesis_library_clamps_at_two_types_in_one_synth():
    """`clamp` at `Int` and at `Float` in the same program, which is what
    a class-constrained definition buys over the old `clampF`."""
    src = """hz : Float
hz = keyHz (clamp 0 127 200)

sound : Sig Float
sound = 0.2 * sine (!hz) * !(clamp 0.0 1.0 4.0)
"""
    graph = graph_of(src, "", rate=8000)
    assert graph.nodes


def test_mix_is_the_same_function_at_a_signal_and_at_a_frame():
    """`mix : (Num a) => a -> a -> a -> a` — a crossfade over signals and
    a blend of two stereo frames are one definition."""
    for src in ["""sound : Sig Float
sound = mix (sine 220.0) (sine 330.0) (unipolar (sine 0.5))
""",
                """sound : Sig Stereo
sound = mix (pan (0.0 - 1.0) (sine 220.0)) (pan 1.0 (sine 330.0)) 0.25
"""]:
        graph = graph_of(src, "", rate=8000)
        assert graph.nodes
