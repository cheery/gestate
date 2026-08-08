"""The remaining fig. 2.2 sugars — `errata.md` D6, roadmap 2.1.

Three spellings, each decided rather than inherited, because Datafun's own
notation collides with syntax gestate already had:

- **`empty?`** keeps its name; a trailing `?` now belongs to an identifier.
  It is a *primitive*, and necessarily so — `for` eliminates only into a
  semilattice and `Bool` is not one, so nothing in the language can define
  the non-monotone observation of a `Prop`.
- **`fix r => e`** replaces `fix X is e`, which would have reserved `is`
  for sugar that saves one `Box`.
- **`Box p`** replaces Datafun's `[p]`, which is unavailable: `[p]` is
  already a one-element list pattern.

Guards and comprehensions are in `test_comprehensions.py`; `Prop` itself in
`test_prop.py`.
"""

from __future__ import annotations

import pytest

from gestate.pipeline import MonotoneError, evaluate
from gestate.syntax.tokenize import tokenize


def _show(expr: str, ty: str = "Bool") -> str:
    return evaluate(f"main : String\nmain = show ({expr} : {ty})")


# ── A trailing `?` is part of an identifier ──────────────────────────────────


def _words(src: str) -> list[str]:
    skip = ("NEWLINE", "EOF", "INDENT", "DEDENT")
    return [t.value for t in tokenize(src) if t.kind.name not in skip]


def test_a_trailing_question_mark_joins_the_identifier():
    assert _words("empty? x") == ["empty?", "x"]


def test_only_one_and_only_at_the_end():
    assert _words("empty??") == ["empty?", "?"]


def test_a_spaced_question_mark_is_still_a_symbol():
    assert _words("x ? y") == ["x", "?", "y"]


# ── `empty?` and `holds` ─────────────────────────────────────────────────────


def test_empty_of_false_is_true():
    assert _show("empty? ({} : Prop)") == "True"


def test_empty_of_true_is_false():
    assert _show("empty? {()}") == "False"


def test_holds_is_the_other_way_round():
    assert _show("holds {()}") == "True"
    assert _show("holds ({} : Prop)") == "False"


def test_a_bool_round_trips_through_prop():
    assert _show("holds (guard (1 == 1))") == "True"
    assert _show("holds (guard (1 == 2))") == "False"


def test_observing_a_prop_is_not_monotone():
    """The restriction that makes `empty?` sound.

    `holds`/`empty?` take their argument at the plain arrow, which *is*
    `□A -> B`, so a fixpoint variable cannot be observed as it converges —
    which is precisely what would let a query see a non-monotone truth.
    """
    with pytest.raises(MonotoneError, match="monotone variable"):
        evaluate("f : Box (Set Int) -> Prop\n"
                 "f (Box s) = fix r => guard (holds r)\n"
                 "main : Prop\nmain = f (Box {1})\n")


# ── `fix r => e` ─────────────────────────────────────────────────────────────


REACH = "main : {Cyclic 4}\nmain = %s {0} \\/ (for (x in r) {x + 1})%s\n"


def test_the_three_fix_spellings_agree():
    full = evaluate(REACH % ("fix Box (r => ", ")"))
    assert evaluate(REACH % ("fix (r => ", ")")) == full
    assert evaluate(REACH % ("fix r => ", "")) == full
    assert full == "Pack{1,2} 0 Pack{1,2} 1 Pack{1,2} 2 Pack{1,2} 3 Pack{0,0}"


# ── `Box p` ──────────────────────────────────────────────────────────────────


def test_a_box_pattern_in_a_case():
    assert evaluate("k : Box Int -> Int\nk b = case b of\n    Box n -> n + 1\n"
                    "main : Int\nmain = k (Box 7)\n") == "8"


def test_a_box_pattern_as_a_parameter():
    # Where it earns its keep: `unbox` is an *expression* form, so before
    # this the box had to be undone in the body rather than in the binder.
    assert evaluate("k : Box Int -> Int\nk (Box n) = n + 1\n"
                    "main : Int\nmain = k (Box 7)\n") == "8"


def test_a_box_pattern_nests():
    assert evaluate("k : Box (Int, Int) -> Int\nk (Box (a, b)) = a + b\n"
                    "main : Int\nmain = k (Box (3, 4))\n") == "7"


def test_a_box_pattern_is_irrefutable():
    # Every `Box A` matches, so one alternative is exhaustive — no
    # non-exhaustive-match complaint, and a `for` clause accepts it.
    assert evaluate("k : Box Int -> Int\nk (Box n) = n\n"
                    "main : Int\nmain = k (Box 3)\n") == "3"


# ── All of it at once ────────────────────────────────────────────────────────


def test_transitive_closure_with_every_sugar():
    """The query this stage existed to make writable.

    Against `test_relations.py`'s version, which needs a two-argument
    `compose` supercombinator, an explicit `unbox … in`, and `fix Box (…)`.
    """
    src = """closure : Box (Set (Cyclic 8, Cyclic 8)) -> Set (Cyclic 8, Cyclic 8)
closure (Box e) = fix r => e \\/ {(x, w) | (x, y) in r, (z, w) in e, y == z}

main : Set (Cyclic 8, Cyclic 8)
main = closure (Box {(0, 1), (1, 2)})
"""
    assert evaluate(src) == (
        "Pack{1,2} (0, 1) Pack{1,2} (0, 2) Pack{1,2} (1, 2) Pack{0,0}")
