"""`Float` — `fixme.md` F84.

The design decision this file pins is that **a literal's form is its type**:
`1.5` is a `Float` and `1` is an `Int`, with no `Fractional` class and no
defaulting.  Mixing still works, because `1` is `Num a => a` and unifies
with `Float` through `Num Float` — so `x * 2 + 1.5` needs no coercion — but
nothing is ever silently chosen for you.
"""

from __future__ import annotations

import pytest

from gestate.pipeline import evaluate


# ── Literals and their types ────────────────────────────────────────────────


def test_a_literal_with_a_point_is_a_float():
    assert evaluate("main : Float\nmain = 1.5\n") == "1.5"


def test_a_literal_without_one_is_still_an_int():
    assert evaluate("main : Int\nmain = 42\n") == "42"


def test_a_float_literal_does_not_fit_an_int_signature():
    """Still refused — as a missing instance rather than a type mismatch.

    `1.5` is `Floating a => a` since `Floating` arrived, so what it fails
    is `Floating Int`: there is no such instance and there should not be.
    The message has to say that in the author's terms, because `Floating`
    is a class nobody writes and a literal is what brings it.
    """
    from gestate.constraint import ConstraintError

    with pytest.raises(ConstraintError, match="not `Int`"):
        evaluate("main : Int\nmain = 1.5\n")


def test_an_int_literal_does_fit_a_float_signature():
    # Not defaulting — `1` is `Num a => a`, and `Num Float` exists, so the
    # constraint is discharged rather than guessed.  `fromInteger` at
    # `Float` really converts, so this is 3.0 and not 3.
    assert evaluate("main : Float\nmain = 3\n") == "3.0"


# ── Arithmetic ──────────────────────────────────────────────────────────────


def test_the_arithmetic():
    assert evaluate("main : Float\nmain = 1.5 + 2.25\n") == "3.75"
    assert evaluate("main : Float\nmain = 5.0 - 1.25\n") == "3.75"
    assert evaluate("main : Float\nmain = 1.5 * 3.0\n") == "4.5"


def test_division_is_true_division():
    # The one arithmetic instruction floats need of their own: `DivInt`
    # floors, and `7.0 / 2.0` must not be 3.
    assert evaluate("main : Float\nmain = 7.0 / 2.0\n") == "3.5"


def test_division_by_zero_is_reported():
    from gestate.gmachine import GmError

    with pytest.raises(GmError, match="division by zero"):
        evaluate("main : Float\nmain = 1.0 / 0.0\n")


def test_integer_division_is_untouched_and_still_floors():
    assert evaluate("main : Int\nmain = prim_div_int 7 2\n") == "3"
    assert evaluate("main : Int\nmain = prim_div_int (0 - 7) 2\n") == "-4"


def test_mixing_needs_no_coercion():
    assert evaluate("f : Float -> Float\nf x = x * 2 + 1\n\n"
                    "main : Float\nmain = f 1.5\n") == "4.0"


def test_comparison():
    # Through `show`: a bare `Bool` prints as its constructor tag, and the
    # tag moves when the program declares a data type of its own.
    def b(expr):
        return evaluate(f"main : String\nmain = show ({expr})\n")

    assert b("1.5 < 2.0") == "True"
    assert b("2.0 <= 2.0") == "True"
    assert b("1.5 == 1.5") == "True"
    assert b("1.5 == 1.25") == "False"


# ── Conversions ─────────────────────────────────────────────────────────────


def test_to_float_and_floor():
    assert evaluate("main : Float\nmain = toFloat 3 / 2.0\n") == "1.5"
    assert evaluate("main : Int\nmain = floor 2.7\n") == "2"


def test_floor_is_floor_and_not_truncation():
    # It agrees with `prim_div_int`, which also floors.
    assert evaluate("main : Int\nmain = floor (0.0 - 2.7)\n") == "-3"


def test_abs():
    assert evaluate("main : Float\nmain = abs (0.0 - 3.5)\n") == "3.5"
    assert evaluate("main : Float\nmain = abs 3.5\n") == "3.5"


# ── Show ────────────────────────────────────────────────────────────────────


def test_show_truncates_to_three_places():
    assert evaluate('main : String\nmain = show 1.5\n') == "1.500"
    assert evaluate('main : String\nmain = show 0.125\n') == "0.125"
    assert evaluate('main : String\nmain = show 12.0\n') == "12.000"


def test_show_peels_the_sign_first():
    """`floor` is floor, so the fraction of -2.75 taken from -3 would be
    .25 and print "-3.250".  The sign comes off before the split."""
    assert evaluate('main : String\nmain = show (0.0 - 2.75)\n') == "-2.750"


# ── Where `Float` sits in the subgrammars ───────────────────────────────────


def test_float_is_an_eqtype_so_a_set_of_them_builds():
    out = evaluate("main : Set Float\nmain = {2.5, 1.5}\n")
    assert out.startswith("Pack"), out


def test_float_is_not_a_fixtype():
    """Exactly `Int`'s standing: decidable equality, infinite chains.

    `fix` over `{Float}` need not terminate for the same reason `{Int}`
    does not, so the subgrammar refuses it — and says why.
    """
    from gestate.pipeline import SubgrammarError

    with pytest.raises(SubgrammarError, match="not a .fixtype|finite"):
        evaluate("main : Set Float\nmain = fix Box (r => r \\/ {1.5})\n")


def test_a_data_type_may_have_float_fields():
    assert evaluate("P := P Float Float deriving (Eq, Ord)\n\n"
                    "main : String\nmain = show (P 1.0 2.0 == P 1.0 2.0)\n") == "True"


def test_ordering_a_data_type_by_its_float_fields():
    assert evaluate("P := P Float Float deriving (Eq, Ord)\n\n"
                    "main : String\nmain = show (P 1.0 2.0 < P 1.0 3.0)\n") == "True"


# ── `Floating` — what a literal with a point in it means ────────────────────
#
# `2` has been `Num a => a` since there was a `Num`, so `x * 2` needs no
# coercion at any type with an instance.  A literal with a point in it was
# a `Float` and nothing else, so the same expression one decimal place
# later stopped typechecking — invisible until a type other than `Float`
# wants literals.  `Sig Float` does: `spec/frp_lesson.md` is the reading
# that turned "`tone * 2` works and `tone * 0.5` does not" into a class.


def test_a_float_literal_is_polymorphic_now():
    """`Floating a => a`, the way `2` is `Num a => a`."""
    assert evaluate("main : Float\nmain = 1.5\n") == "1.5"
    assert evaluate("main : Float\nmain = 1.5 + 2\n") == "3.5"


def test_an_ambiguous_float_literal_defaults_to_float():
    """It cannot default to `Int` — that is the one type it is not.

    A variable carrying `Num` alone still defaults to `Int`, so this is
    about the constraint deciding, not about floats winning.
    """
    assert evaluate("main : String\nmain = show (1.5 < 2.0)\n") == "True"
    assert evaluate("main : String\nmain = show (1 < 2)\n") == "True"


def test_a_program_may_say_what_a_float_literal_means_at_its_own_type():
    """The point of the class: an instance is a program's own answer.

    `Wrapped` here stands for what `audio.ges` does with `Sig Float` — a
    literal becomes a constant signal — with none of the audio machinery
    in the way.
    """
    source = ("Wrapped := Wrapped Float\n"
              "\ninstance Floating Wrapped where\n"
              "    fromFloat x = Wrapped x\n"
              "\nunwrap : Wrapped -> Float\n"
              "unwrap w = case w of\n"
              "    Wrapped x -> x\n"
              "\nhalf : Wrapped\nhalf = 0.5\n"
              "\nmain : Float\nmain = unwrap half\n")
    assert evaluate(source) == "0.5"
