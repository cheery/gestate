"""Tests for the offside rule where it meets brackets.

``spec/syntax.md`` §Layout says which forms open a layout block but not
what closes one.  Indentation alone cannot: a block opened inside a
bracket has to end at the closing bracket, which arrives before the next
line's dedent would.  This is Haskell's parse-error rule, narrowed to the
one case that provokes it.
"""

from __future__ import annotations

import pytest

from gestate.pipeline import evaluate
from gestate.syntax import parse
from gestate.syntax.tokenize import TT, tokenize


def _kinds(source: str) -> list[tuple[str, str]]:
    return [(t.kind.name, t.value) for t in tokenize(source)]


# ── The frontier itself ──────────────────────────────────────────────────────


def test_dedent_precedes_the_closing_bracket():
    """The block parser must see its DEDENT before anyone eats the `)`."""
    toks = _kinds("f = g (case x of\n    True -> 1\n    False -> 2)\n")
    dedent = toks.index(("DEDENT", ""))
    close = toks.index(("SEP", ")"))

    assert dedent < close
    assert close == dedent + 1


def test_a_bracket_inside_a_block_does_not_close_it():
    """Only a bracket opened *before* the block ends it."""
    source = "f x = case x of\n    True -> g (1 + 2)\n    False -> 3\n"
    toks = _kinds(source)
    close = toks.index(("SEP", ")"))
    dedent = toks.index(("DEDENT", ""))

    assert close < dedent      # the inner `)` leaves the block open
    parse(source)


# ── Programs the rule unblocks ───────────────────────────────────────────────


def test_case_as_an_argument():
    assert evaluate("f : Int -> Int\n"
                    "f n = g (case n < 3 of\n"
                    "    True -> 1\n"
                    "    False -> 2)\n"
                    "g : Int -> Int\ng x = x + 10\n"
                    "main : Int\nmain = f 5\n") == "12"


def test_case_as_an_infix_operand():
    assert evaluate("f : Int -> Int\n"
                    "f n = (case n < 3 of\n"
                    "    True -> 1\n"
                    "    False -> 2) + 100\n"
                    "main : Int\nmain = f 5\n") == "102"


def test_nested_brackets_close_one_block_each():
    assert evaluate("f : Int -> Int\n"
                    "f n = (g (case n < 3 of\n"
                    "    True -> 1\n"
                    "    False -> 2)) + 1\n"
                    "g : Int -> Int\ng x = x\n"
                    "main : Int\nmain = f 5\n") == "3"


def test_case_inside_a_case_alternative():
    assert evaluate("f : Int -> Int\n"
                    "f n = case n < 3 of\n"
                    "    True -> (case n < 1 of\n"
                    "        True -> 0\n"
                    "        False -> 1)\n"
                    "    False -> 2\n"
                    "main : Int\nmain = f 2\n") == "1"


def test_let_block_in_brackets():
    assert evaluate("f : Int\nf = (let y = 1 in y) + 2\n"
                    "main : Int\nmain = f\n") == "3"


def test_declarations_after_the_block_still_parse():
    """The dedent must not be spent twice."""
    assert evaluate("f : Int -> Int\n"
                    "f n = g (case n < 3 of\n"
                    "    True -> 1\n"
                    "    False -> 2)\n"
                    "g : Int -> Int\ng x = x\n"
                    "h : Int\nh = 7\n"
                    "main : Int\nmain = f 5 + h\n") == "9"


# ── Blocks inside class and instance bodies ──────────────────────────────────
#
# A multi-line `case` leaves its closing DEDENT for the caller — at the top
# level the application-parsing loop needs to see it.  Inside a `class` or
# `instance` body, and inside an enclosing `case`, that same DEDENT read as
# the end of the *enclosing* block: every member or alternative after a
# multi-line one silently fell out of it.


def test_instance_member_after_a_multi_line_case():
    from gestate.declarations import classify
    from gestate.syntax import parse

    program = classify(parse("""class C a where
    f : a -> Int
    g : a -> Int

instance C Int where
    f x = case x < 0 of
        True -> 0
        False -> x
    g x = x + 1
"""))
    inst = program.instances[0]
    assert sorted(inst.methods) == ["f", "g"]


def test_class_member_after_a_multi_line_member():
    from gestate.declarations import classify
    from gestate.syntax import parse

    program = classify(parse("""class C a where
    f : a -> Int
    g : a -> Int

main : Int
main = 1
"""))
    assert sorted(program.classes["C"].methods) == ["f", "g"]


def test_alternative_after_a_nested_case():
    from gestate.pipeline import evaluate

    assert evaluate("""f : List (List Int) -> Int
f xs = case xs of
    [] -> case xs of
        [] -> 1
        y :: ys -> 2
    x :: rest -> 3

main : Int
main = f [[7]]
""") == "3"


def test_deeply_nested_case_alternatives():
    from gestate.pipeline import evaluate

    assert evaluate("""f : List Int -> List Int -> Int
f xs ys = case xs of
    [] -> case ys of
        [] -> 0
        z :: zs -> 1
    x :: rest -> case ys of
        [] -> 2
        z :: zs -> case x < z of
            True -> 3
            False -> 4

main : Int
main = f [5] [9]
""") == "3"


# ── Three parse defects found while writing the music prelude ────────────────


def test_a_trailing_comment_does_not_end_a_constructor_list():
    """`fixme.md` F70 — a comment decided whether a program parsed.

    `T := A  # hi` left the `COMMENT` token in front of the `INDENT`, so the
    continuation loop never started and the declaration silently ended after
    its first constructor.  Removing the comment made the same source parse,
    which is the one thing a comment must never change.
    """
    import gestate.syntax as S

    S.parse("T := A   # hi\n   | B Int\nmain = 1\n")
    S.parse("T := A\n   | B Int   # hi\n   | C\nmain = 1\n")


def test_a_single_line_case_inside_brackets():
    """`fixme.md` F72 — the other half of F45.

    F45 fixed a *multi-line* `case` inside brackets, where the tokenizer
    emits the block's `DEDENT` before the closer.  A one-line `case` opens
    no block, so it never reached that machinery and the alternative loop
    read the `)` as the start of another pattern.
    """
    import gestate.syntax as S

    S.parse("f = (case x of (a, b) -> a)\n")
    S.parse("f = map (e => case e of (a, b) -> a) xs\n")
    S.parse("f = (case x of A -> 1, 2)\n")


def test_a_lambda_may_take_a_pattern():
    """`fixme.md` F71 — the parser accepted what the desugarer refused."""
    from gestate.pipeline import evaluate

    assert evaluate("main : Int\n"
                    "main = sum (map ((a, b) => a + b) [(1,2),(3,4)])\n") == "10"
    assert evaluate("main : Int\n"
                    "main = sum (map (((a, b), c) => a + b + c) [((1,2),3)])\n") == "6"


def test_a_refutable_lambda_pattern_is_rejected():
    """There is nowhere for a failed match in a lambda to go.

    The same rule as a `for` clause: irrefutable patterns only, and the
    message names `case` as what to use instead.
    """
    import pytest

    from gestate.desugar import DesugarError
    from gestate.pipeline import evaluate

    with pytest.raises(DesugarError, match="irrefutable"):
        evaluate("main : Int\nmain = sum (map ((Just x) => x) [Just 1])\n")


# ── Continuation lines (`fixme.md` F82) ─────────────────────────────────────
#
# An indented line is normally a layout block.  Two shapes continue the line
# above instead, and the value of the change is that the third group below —
# the forms that already worked — is unaffected.


def test_a_line_beginning_with_an_operator_continues_the_one_above():
    assert evaluate("main : Int\nmain = 1 + 2\n    + 3\n") == "6"


def test_a_body_may_start_on_the_line_after_the_equals():
    assert evaluate("main : Int\nmain =\n    1 + 2\n") == "3"


def test_a_continuation_works_inside_brackets():
    assert evaluate("main : Int\nmain = (1 + 2\n    + 3) * 2\n") == "12"


def test_a_signature_may_be_broken_at_the_arrow():
    assert evaluate("f : Int\n    -> Int\nf x = x + 1\n\n"
                    "main : Int\nmain = f 1\n") == "2"


def test_a_continuation_works_inside_a_case_alternative():
    # The alternative's body continues; the `case` block itself is not
    # closed by the dedent that follows.
    assert evaluate("main : Int\nmain = case True of\n"
                    "    True -> 1\n        + 2\n    False -> 0\n") == "3"


def test_several_continuation_lines_in_a_row():
    assert evaluate("main : Int\nmain = 1\n    + 2\n    + 3\n    + 4\n") == "10"


def test_a_line_at_the_same_indent_is_not_a_continuation():
    # It is the next declaration, whatever it starts with.
    from gestate.syntax.parse import ParseError

    with pytest.raises((ParseError, Exception)):
        evaluate("main : Int\nmain = 1 + 2\n+ 3\n")


def test_an_indented_line_that_could_begin_an_item_still_opens_a_block():
    # The form the narrow rule exists to protect: `y = 6` could start an
    # item, so it does, and `let` keeps its block.
    assert evaluate("main : Int\nmain = let x = 5\n"
                    "           y = 6\n       in x + y\n") == "11"


def test_a_bare_operand_on_its_own_line_is_not_a_continuation():
    """Documented as not covered — there is no way to tell it from an item.

    If this ever starts working, the manual and `spec/syntax.md` both say it
    does not; update them rather than restoring the limitation.
    """
    with pytest.raises(Exception):
        evaluate("f : Int -> Int -> Int\nf a b = a + b\n\n"
                 "main : Int\nmain = f 1\n    2\n")


# ── A continuation may begin with `(` (`fixme.md` F86) ──────────────────────


def test_a_line_beginning_with_a_paren_continues_the_one_above():
    assert evaluate("main : Int\nmain = sum\n    ([1,2,3])\n") == "6"


def test_a_long_application_broken_across_lines():
    """The prelude's own `showFloat` is written this way.

    Spelled with `show` rather than the `showNat` the prelude itself uses:
    that one is below `prelude.ges`'s `internal` marker now, and a test is
    not exempt from the rule it is testing around.
    """
    assert evaluate('g : Int -> String\n'
                    'g n = append (show n)\n'
                    '             (append "." (show n))\n\n'
                    'main : String\nmain = g 7\n') == "7.7"


def test_a_paren_continuation_inside_a_case_alternative():
    assert evaluate("main : Int\nmain = case True of\n"
                    "    True -> sum\n        ([1,2,3])\n"
                    "    False -> 0\n") == "6"


def test_a_tuple_pattern_alternative_is_not_a_continuation():
    """The form the block-opener guard exists for.

    `(a, b) -> a + b` is deeper than the `case` and starts with `(`.  It is
    the block's first item, not a continuation of the scrutinee — and the
    only way to tell is that `of` came immediately before.
    """
    assert evaluate("main : Int\nmain = case (1, 2) of\n"
                    "    (a, b) -> a + b\n") == "3"


def test_an_operator_class_member_is_not_a_continuation():
    assert evaluate("class Sum a where\n    (<+>) : a -> a -> a\n\n"
                    "instance Sum Int where\n    (<+>) x y = x + y\n\n"
                    "main : Int\nmain = 1 <+> 2\n") == "3"


def test_two_operator_members_in_a_row():
    # The second is at the same indent as the first, so it was never at
    # risk — but it is the shape the prelude uses everywhere.
    assert evaluate("instance Eq (Int, Int, Int) where\n"
                    "    (==) a b = True\n"
                    "    (/=) a b = False\n\n"
                    "main : String\nmain = show ((1,2,3) == (1,2,3))\n") == "True"
