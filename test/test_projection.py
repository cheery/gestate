"""Record and tuple projection — `fixme.md` F28.

`syntax.md` documents `x.0` and it did nothing: `VProj` was parsed and
fixity-resolved, and `desugar.py` had no case for it, so it never reached
the type checker.

**Resolved from the type, not through a class.**  `syntax.md` prescribes
sixteen `AttrN` classes with associated types, which would make `f p = p.0`
principal — it would infer `(Attr0 a) => a -> Field0 a`.  That costs ~120
generated tuple instances and sixteen classes in every program's namespace,
to buy record-polymorphism nothing in this language has asked for, while
D9 has already settled that the Datafun half is deliberately monomorphic.

So the base's type decides, and where it is not known the error says so.
The cost is exactly one case: an unannotated `f p = p.0` is rejected.

A tuple and a record are *different runtime shapes* — an `NTuple` selected
with `Proj` against a one-constructor `NCon` destructured with a `case` —
which is why this cannot be lowered at desugaring, which runs before there
are any types.  `EField` survives inference and a small pass lowers it.
"""

from __future__ import annotations

import pytest

from gestate.infer import InferError
from gestate.pipeline import evaluate

REC = "P := P Int Bool\n\n"
PAIR = "Pair a := Pair a a\n\n"


# ── Tuples ───────────────────────────────────────────────────────────────────


def test_tuple_components():
    assert evaluate("main : Int\nmain = (3, 4).0\n") == "3"
    assert evaluate("main : Int\nmain = (3, 4).1\n") == "4"


def test_a_wider_tuple():
    assert evaluate("main : Int\nmain = (1, 2, 3).2\n") == "3"


def test_a_tuple_component_of_another_type():
    assert evaluate("main : String\nmain = show ((1, True).1)\n") == "True"


# ── Records — a single-constructor data type ─────────────────────────────────


def test_record_fields():
    assert evaluate(REC + "main : Int\nmain = (P 7 True).0\n") == "7"
    assert evaluate(REC + "main : String\nmain = show ((P 7 True).1)\n") == "True"


def test_a_record_field_at_a_parameter():
    assert evaluate(PAIR + "f : Pair Int -> Int\nf p = p.0\n\n"
                    "main : Int\nmain = f (Pair 5 6)\n") == "5"


def test_the_field_type_is_substituted_for_the_records_parameters():
    """`Pair a`'s field is `a`, so `Pair Bool`'s field is `Bool`."""
    assert evaluate(PAIR + "f : Pair Bool -> String\nf p = show p.1\n\n"
                    "main : String\nmain = f (Pair True False)\n") == "False"


def test_projection_binds_to_the_atom_not_the_application():
    """`show p.1` is `show (p.1)`.

    The projection loop used to run after the whole application, so it
    read `(show p).1` — against the parser's own docstring.  Nothing could
    have depended on it, since projection did nothing at all before.
    """
    assert evaluate(PAIR + "f : Pair Bool -> String\nf p = show p.1\n\n"
                    "main : String\nmain = f (Pair False True)\n") == "True"


def test_pattern_matching_still_works():
    # Projection is an addition; the way records were always read is intact.
    assert evaluate(PAIR + "f : Pair Int -> Int\nf (Pair x y) = y\n\n"
                    "main : Int\nmain = f (Pair 5 6)\n") == "6"


def test_a_nested_projection_needs_parentheses():
    """`x.0.1` does not lex as two projections.

    `0.1` is a float literal, so the tokenizer takes it whole and the
    phrase reads `x . 0.1`.  Parenthesising is the workaround; the
    alternative would be to stop the number rule at a digit that follows a
    `.`-projection, which is a lexical change nothing yet needs.
    """
    assert evaluate("Q := Q (Int, Int)\n\nmain : Int\n"
                    "main = ((Q (5, 6)).0).1\n") == "6"


# ── What it refuses, and how ────────────────────────────────────────────────


def test_an_unknown_base_type_is_reported_as_such():
    """The one case this design gives up, and the message says what to do."""
    with pytest.raises(InferError, match="not known here"):
        evaluate("f p = p.0\n\nmain : Int\nmain = f (1, 2)\n")


def test_a_component_out_of_range():
    with pytest.raises(InferError, match=r"components are 0 to 1"):
        evaluate("main : Int\nmain = (1, 2).5\n")


def test_a_field_out_of_range():
    with pytest.raises(InferError, match="field"):
        evaluate(REC + "main : Int\nmain = (P 7 True).9\n")


def test_a_multi_constructor_type_is_not_a_record():
    with pytest.raises(InferError, match="constructors"):
        evaluate("C := R | G\n\nmain : Int\nmain = R.0\n")


def test_a_type_that_is_neither():
    with pytest.raises(InferError, match="not a tuple or a record"):
        evaluate("main : Int\nmain = (3 : Int).0\n")


def test_a_named_field_is_rejected_with_a_reason():
    with pytest.raises(InferError, match="no field names"):
        evaluate(REC + "main : Int\nmain = (P 7 True).foo\n")


# ── The instance-method bug this turned up (`fixme.md` F69) ─────────────────


def test_an_instance_method_may_take_a_constructor_pattern():
    """`get (P x y) = x` bound a parameter called `"P"` and never bound `x`.

    `elaborate` read `p.name` off each parameter, and a `PCon` has one —
    the *constructor's*.  Method bodies now go through the match compiler
    the way supercombinator equations always did.
    """
    assert evaluate(REC + "class G a where\n    get : a -> Int\n\n"
                    "instance G P where\n    get (P x y) = x\n\n"
                    "main : Int\nmain = get (P 7 True)\n") == "7"


def test_an_instance_method_may_take_a_tuple_pattern():
    # A `PTuple` has no `.name`, so it was silently *dropped* — the method
    # lost the parameter rather than mis-binding it.
    assert evaluate("class G a where\n    get : a -> Int\n\n"
                    "instance G (Int, Int) where\n    get (x, y) = y\n\n"
                    "main : Int\nmain = get (3, 4)\n") == "4"
