"""Implicit parameters — `(using n)` and `given`, and what they must not do.

`doc/manual.md` §4 documents the feature and `test_manual.py` keeps those
examples running.  This file covers the part a reader never sees: the
requirement analysis walks every body in the program, so it has to respect
binders.  Getting that wrong does not produce an error — it silently gives
some *other* definition an extra parameter, which is how the bug below was
found (the prelude's `flip f x y = f y x` acquired an implicit because a
test defined a supercombinator called `f`).
"""

from __future__ import annotations

import pytest

from gestate.desugar import DesugarError
from gestate.pipeline import evaluate


# ── Binders shadow globals in the requirement analysis ───────────────────────


def _needs(src: str) -> dict[str, list[str]]:
    from gestate.declarations import classify
    from gestate.desugar import _implicit_needs
    from gestate.prelude import merge
    return _implicit_needs(classify(merge(src)))


IMPLICIT = "implicit n : Int\n\nf : Int\nf (using n) = n\n\n"


def test_a_parameter_shadows_a_supercombinator_of_the_same_name():
    # `apply f x = f x` names *its parameter*, not the global `f`, so it
    # requires nothing — and keeps the arity its signature promises.
    src = (IMPLICIT + "apply : (Int -> Int) -> Int -> Int\napply f x = f x\n\n"
           "main : Int\nmain = apply (y => y + 1) 2\n")
    assert "apply" not in _needs(src)
    assert evaluate(src) == "3"


def test_a_lambda_parameter_shadows_it_too():
    src = (IMPLICIT + "g : Int\ng = (f => f 1) (y => y + 1)\n\n"
           "main : Int\nmain = g\n")
    assert "g" not in _needs(src)
    assert evaluate(src) == "2"


def test_a_let_binding_shadows_it():
    src = (IMPLICIT + "g : Int\ng = let f = 7 in f\n\nmain : Int\nmain = g\n")
    assert "g" not in _needs(src)
    assert evaluate(src) == "7"


def test_a_case_alternative_binds_its_pattern_variables():
    src = (IMPLICIT + "g : Int\ng = case Just 5 of\n"
           "    Just f -> f\n    Nothing -> 0\n\nmain : Int\nmain = g\n")
    assert "g" not in _needs(src)
    assert evaluate(src) == "5"


def test_a_comprehension_generator_binds_its_pattern():
    src = (IMPLICIT + "g : Set (Cyclic 8)\ng = for (f in {1,2}) {f}\n\n"
           "main : Set (Cyclic 8)\nmain = g\n")
    assert "g" not in _needs(src)
    assert evaluate(src).startswith("Pack")


def test_the_prelude_is_untouched_by_a_users_implicit():
    # The regression itself: no prelude definition may acquire a parameter
    # because a *user* program happens to name a supercombinator `f`.
    src = IMPLICIT + "main : Int\nmain = given n = 1 in f\n"
    needs = _needs(src)
    assert set(needs) == {"f"}, f"leaked into: {sorted(set(needs) - {'f'})}"
    assert evaluate(src) == "1"


# ── Propagation itself ───────────────────────────────────────────────────────


def test_it_reaches_a_fixed_point_through_a_chain():
    assert evaluate(IMPLICIT + "a : Int\na = f + 1\n\n"
                    "b : Int\nb = a + 1\n\n"
                    "c : Int\nc = b + 1\n\n"
                    "main : Int\nmain = given n = 10 in c\n") == "13"


def test_a_recursive_definition_terminates():
    # `needs` is a least fixed point, so a cycle must not loop forever.
    src = (IMPLICIT + "countdown : Int -> Int\n"
           "countdown k = case k == 0 of\n"
           "    True -> f\n    False -> countdown (k - 1)\n\n"
           "main : Int\nmain = given n = 4 in countdown 3\n")
    assert _needs(src)["countdown"] == ["n"]
    assert evaluate(src) == "4"


def test_two_definitions_needing_different_implicits():
    src = ("implicit w : Int\nimplicit h : Int\n\n"
           "p : Int\np (using w) = w\n\n"
           "q : Int\nq (using h) = h\n\n"
           "both : Int\nboth = p * q\n\n"
           "main : Int\nmain = given w = 3, h = 4 in both\n")
    assert _needs(src)["both"] == ["h", "w"]     # sorted, so callers agree
    assert evaluate(src) == "12"


# ── The link-time check ──────────────────────────────────────────────────────


def test_an_implicit_reaching_main_is_rejected():
    with pytest.raises(DesugarError, match="unfilled implicit"):
        evaluate(IMPLICIT + "main : Int\nmain = f\n")


def test_it_is_rejected_through_a_chain_too():
    with pytest.raises(DesugarError, match="required by `f`"):
        evaluate(IMPLICIT + "a : Int\na = f + 1\n\n"
                 "main : Int\nmain = a\n")


def test_a_given_on_one_path_does_not_excuse_another():
    # `ok` is supplied; `bad` is not.  Rejecting needs the union, not the
    # first path found.
    with pytest.raises(DesugarError, match="unfilled implicit"):
        evaluate(IMPLICIT + "ok : Int\nok = given n = 1 in f\n\n"
                 "bad : Int\nbad = f\n\n"
                 "main : Int\nmain = ok + bad\n")


# ── `implicit n : τ` — the declaration site ──────────────────────────────────


def test_a_signature_does_not_mention_the_implicit():
    """The point of declaring the type once.

    `f : Int` even though `f` takes `n`, and `g : Int` even though `g`
    inherits the requirement.  Neither signature changes when the other
    definition does, which is what an inferred requirement should cost.
    """
    assert evaluate(IMPLICIT + "g : Int\ng = f + 1\n\n"
                    "main : Int\nmain = given n = 5 in g\n") == "6"


def test_an_undeclared_implicit_is_rejected_at_the_use():
    with pytest.raises(DesugarError, match="undeclared implicit `ppq`"):
        evaluate("f : Int\nf (using ppq) = ppq\n\n"
                 "main : Int\nmain = given ppq = 1 in f\n")


def test_the_declaration_gives_the_parameter_its_type():
    from gestate.unify import UnifyError

    # `given n = True` cannot fill an `implicit n : Int`.
    with pytest.raises(UnifyError, match="Int"):
        evaluate(IMPLICIT + "main : Int\nmain = given n = True in f\n")


def test_an_implicit_need_not_be_an_int():
    assert evaluate('implicit label : String\n\n'
                    'tag : String\ntag (using label) = label\n\n'
                    'main : String\nmain = given label = "hi" in tag\n') == "hi"


def test_a_duplicate_declaration_is_rejected():
    from gestate.declarations import DeclError

    with pytest.raises(DeclError, match="Duplicate `implicit`"):
        evaluate("implicit n : Int\nimplicit n : Int\n\n"
                 "main : Int\nmain = 1\n")


def test_an_implicit_may_not_carry_a_class_context():
    from gestate.declarations import DeclError

    # A `given` passes a value, not a dictionary, so there is nowhere for
    # the predicate to be discharged.
    with pytest.raises(DeclError, match="class context"):
        evaluate("implicit n : (Eq a) => a\n\nmain : Int\nmain = 1\n")


def test_the_formatter_round_trips_a_declaration():
    from gestate.fmt import format_source

    assert format_source("implicit ppq : Int\n") == "implicit ppq : Int\n"


# ── Through the audio path ──────────────────────────────────────────────────


def test_an_implicit_renders_the_same_as_the_parameter_it_hides():
    """`doc/manual.md` §4's claim, checked where it had never been run.

    *"The propagation happens once, during compilation, and what runs is
    an ordinary function with an ordinary extra argument."*  Every other
    test in this file goes through the interpreter; until 2026-08-17 no
    `.ges` program in the tree used `using`/`given` at all, so nothing
    had ever taken one through `audioextract` and the engine.

    **A buffer comparison rather than a golden**, and that is the point:
    a golden pins one render on one machine, while this pins the claim.
    Write the same drone twice — once with the reference threaded
    implicitly, once with it passed by hand — and if the manual is right
    the two are the same samples, not merely the same sound.
    `examples/audio/tuning.ges` is the readable version of the first.

    Both renderers, because they are different code: `audio.render` is
    the pure-Python reference, and `run_native` is the graph through
    `clang` — which is the one an implicit had never been near.
    """
    import shutil
    import tempfile

    from gestate.audio import render
    from gestate.audioextract import extract
    from gestate.audiollvm import run_native

    shared = """
partial : Float -> Float -> Sig Float
partial level n = !level * sine (step n)

drone : Sig Float
drone = partial 0.30 0.0 + partial 0.18 7.0 + partial 0.10 12.0
"""
    implicit = ("implicit concert : Sig Float\n"
                "\nstep : Float -> Sig Float\n"
                "step (using concert) n = concert * !(pow 2.0 (n / 12.0))\n"
                + shared +
                "\nsound : Sig Float\n"
                "sound = given concert = !415.0 in 0.6 * drone\n")
    # The same program with the argument written out: `step` takes the
    # reference first, and every caller in between has to say so.
    spelt = ("step : Sig Float -> Float -> Sig Float\n"
             "step concert n = concert * !(pow 2.0 (n / 12.0))\n"
             + shared.replace("partial level n = !level * sine (step n)",
                              "partial level n = !level * sine (step !415.0 n)")
             + "\nsound : Sig Float\nsound = 0.6 * drone\n")

    hidden = render(implicit, 0.25, 8000)
    shown = render(spelt, 0.25, 8000)
    assert hidden == shown, "an implicit is an ordinary extra argument"
    assert max(abs(x) for x in hidden) > 0.1, "and it is not silence"

    if shutil.which("clang") is None:
        pytest.skip("no clang to build the graph with")
    with tempfile.TemporaryDirectory() as d:
        native = run_native(extract(implicit, rate=8000), d, len(hidden))
    assert native == hidden, \
        "and the engine agrees with the reference about it"
