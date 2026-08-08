"""Fixity resolution for the music operators — `fixme.md` F59.

Prefix and postfix operators used to be recognised only at the two *ends*
of an operator phrase, and any symbol followed by another symbol was read
as postfix.  Between them, `'a ++ 'b` came out as `(('a)++) ' b`: `++`
postfix, `'` infix.  Since `'` is the unit-note constructor and a piece of
music is a sequence of notes, nothing in `music.md` was writable.
"""

from __future__ import annotations

import pytest

import gestate.syntax as S


def _tree(expr: str) -> str:
    """The resolved fixity tree, fully parenthesised."""
    def sh(v):
        n = type(v).__name__
        if n == "VInfix":   return f"({sh(v.left)} {v.op} {sh(v.right)})"
        if n == "VPrefix":  return f"({v.op}{sh(v.arg)})"
        if n == "VPostfix": return f"({sh(v.arg)}{v.op})"
        if n == "VNum":     return str(v.value)
        if n == "VApp":     return f"({sh(v.fn)} {sh(v.arg)})"
        return getattr(v, "value", n)
    module = S.parse(f"main = {expr}\n")
    for item in module.items:
        if type(item).__name__ == "VSCDecl":
            return sh(item.equations[0].body)
    raise AssertionError("no declaration parsed")


# ── Prefix operators away from the start of a phrase ─────────────────────────


def test_a_lone_prefix_operator():
    assert _tree("'a") == "('a)"


def test_a_prefix_operator_after_an_infix_one():
    # The regression: `++` was read as postfix and `'` as infix.
    assert _tree("'a ++ 'b") == "(('a) ++ ('b))"


def test_a_sequence_of_notes():
    assert _tree("'a ++ 'b ++ 'c") == "((('a) ++ ('b)) ++ ('c))"


def test_a_prefix_operator_binds_tighter_than_a_looser_infix():
    # `'` is precedence 9 and `++` is 4, so `'` takes the note beside it
    # rather than the whole sequence.
    assert _tree("'a ++ b") == "(('a) ++ b)"


# ── The operators that were already fine, kept fine ──────────────────────────


def test_infix_minus_is_still_infix():
    assert _tree("0 - 1") == "(0 - 1)"


def test_prefix_minus_is_still_prefix():
    assert _tree("- x") == "(-x)"
    assert _tree("a * - b") == "(a * (-b))"


def test_ordinary_precedence_is_unchanged():
    assert _tree("1 + 2 * 3") == "(1 + (2 * 3))"


def test_postfix_still_works_including_before_an_infix_operator():
    assert _tree("a >|") == "(a>|)"
    assert _tree("a >| ++ b") == "((a>|) ++ b)"


def test_prefix_shift_operator():
    assert _tree("|< a") == "(|<a)"


# ── Score type syntax (`fixme.md` F61) and `Void` (F60) ──────────────────────


def _compiles(src: str) -> bool:
    from gestate.pipeline import compile
    compile(src)
    return True


def test_the_score_type_parses_in_a_signature():
    # `[: a :]` is what `syntax.md` and `music.md` both document; it used to
    # be a parse error everywhere except an instance head, because the `[:`
    # branch reachable from a signature built a *List* and then choked on
    # the closing `:]`.
    assert _compiles("f : [: Int :] -> Int\nf s = 1\n\nmain : Int\nmain = 1\n")


def test_the_score_type_parses_in_an_alias():
    assert _compiles("type Sc = [: Int :]\n\nf : Sc -> Int\nf s = 1\n\n"
                     "main : Int\nmain = 1\n")


def test_score_and_the_bracket_form_are_the_same_type():
    assert _compiles("f : [: Int :] -> Int\nf s = 1\n\n"
                     "g : Score Int -> Int\ng s = f s\n\nmain : Int\nmain = 1\n")


def test_void_is_a_builtin_type():
    # Uninhabited, and builtin because `:=` cannot declare a constructorless
    # type.  `[: Void :]` is `music.md`'s performable score.
    assert _compiles("f : [: Void :] -> Int\nf s = 1\n\nmain : Int\nmain = 1\n")


def test_a_list_literal_is_untouched():
    from gestate.pipeline import evaluate
    assert evaluate("main : List Int\nmain = [1,2,3]\n").count("Pack{1,2}") == 3


# ── Fixity: `music.md`'s worked example ──────────────────────────────────────


def test_the_music_example_groups_as_the_spec_says():
    """`music.md`'s own example, under the precedence it settled on.

    Scaling used to be *looser* than sequencing, so this scaled the whole
    phrase.  Writing music changed the answer: two scaled groups in a row —
    `(a) |/ 2 ++ (b) |/ 2`, a bar of eighth notes — is the common shape, and
    under the loose reading the second `|/` swallowed everything before it.
    Scaling is `infixl 6` now; a phrase to be scaled is parenthesised.
    """
    assert _tree("'1 ++ '2 ++ '3 |* 2 || '5 |* 6") == (
        "(((('1) ++ ('2)) ++ (('3) |* 2)) || (('5) |* 6))")


def test_sequencing_binds_tighter_than_overlay():
    assert _tree("a || b ++ c") == "(a || (b ++ c))"


def test_scaling_applies_to_the_group_beside_it():
    assert _tree("a ++ b |* 2") == "(a ++ (b |* 2))"
    assert _tree("(a ++ b) |* 2") == "((a ++ b) |* 2)"


def test_two_scaled_groups_in_a_row():
    """The shape that decided the precedence: a bar of eighth notes."""
    assert _tree("a |/ 2 ++ b |/ 2") == "((a |/ 2) ++ (b |/ 2))"
    assert _tree("a ++ b |* 2 ++ c") == "((a ++ (b |* 2)) ++ c)"


def test_the_scaling_factor_binds_tighter_than_the_scaling():
    assert _tree("a |* 2 + 1") == "(a |* (2 + 1))"


# ── `[a]` is a type (`fixme.md` F62) ─────────────────────────────────────────


def test_the_list_type_parses():
    assert _compiles("f : [Int] -> Int\nf xs = 1\n\nmain : Int\nmain = f [1,2]\n")


def test_the_list_type_takes_a_variable():
    # The `a` has to be collected as a signature type variable; it was not,
    # so it came out a nullary constructor and the kind checker rejected it.
    assert _compiles("f : [a] -> Int\nf xs = 1\n\nmain : Int\nmain = f [1]\n")


def test_the_list_type_nests():
    assert _compiles("f : [[Int]] -> Int\nf xs = 1\n\nmain : Int\nmain = f [[1]]\n")


def test_the_bracket_and_word_list_types_agree():
    assert _compiles("f : [a] -> Int\nf xs = 1\n\n"
                     "g : List Int -> Int\ng xs = f xs\n\n"
                     "main : Int\nmain = g [1]\n")


def test_a_list_type_with_a_tail_is_rejected():
    from gestate.declarations import DeclError
    with pytest.raises(DeclError, match="one element type"):
        _compiles("f : [Int|x] -> Int\nf xs = 1\n\nmain : Int\nmain = 1\n")


# ── Spec hygiene made testable (`fixme.md` F24) ──────────────────────────────


def test_the_function_arrow_cannot_be_given_a_fixity():
    """`syntax.md`: "`->` is the only operator that cannot be overrided."

    It could be, silently: a user `infixl 9 ->` replaced the built-in
    `infixr 1` and re-associated every function type in the program.
    Rejected now rather than ignored — ignoring a declaration someone wrote
    is its own surprise.
    """
    from gestate.syntax.descend import FixityError

    for op in ("->", "~>"):
        with pytest.raises(FixityError, match="fixed fixity"):
            _compiles(f"infixl 9 {op}\n\nmain : Int\nmain = 1\n")


def test_an_ordinary_operator_may_still_be_given_a_fixity():
    assert _compiles("infixl 9 ++\n\nmain : String\nmain = \"a\" ++ \"b\"\n")


# ── A name used as an operator — `` x `over` y `` ───────────────────────────


def test_a_name_in_backticks_is_an_infix_operator():
    """The mirror of `(+)`: an operator parenthesised into a name, and a
    name quoted into an operator."""
    assert _tree("x `over` y") == "(x over y)"


def test_a_quoted_name_binds_like_any_undeclared_operator():
    """Tightly and to the left — the `infixl 9` every other language gives
    them, and it falls out of the default rather than being a rule here."""
    assert _tree("a `f` b `f` c") == "((a f b) f c)"
    assert _tree("2 * 3 `f` 4") == "(2 * (3 f 4))"


def test_a_quoted_name_takes_a_fixity_declaration():
    from gestate.pipeline import evaluate

    right = ("infixr 5 `pair`\n\npair : Int -> Int -> Int\n"
             "pair a b = a * 10 + b\n\nmain : Int\nmain = 1 `pair` 2 `pair` 3\n")
    assert evaluate(right) == "33", "right-associated: 1*10 + (2*10+3)"


def test_a_quoted_name_is_the_name_applied():
    """A local, a global and a constructor each behave as they do anywhere
    else, because the desugarer builds the application and stops there."""
    from gestate.pipeline import evaluate

    assert evaluate("over : Int -> Int -> Int\nover a b = a * 10 + b\n"
                    "\nmain : Int\nmain = 3 `over` 4\n") == "34"
    assert evaluate("main : Int\n"
                    "main = let f = (x y => x - y) in 9 `f` 4\n") == "5"
    assert evaluate("main : Int\nmain = case (1 `Cons` []) of\n"
                    "    Cons x xs -> x\n    Nil -> 0\n") == "1"


def test_a_backtick_with_no_name_in_it_says_so():
    from gestate.syntax.parse import ParseError

    for bad in ("main = x `` y\n", "main = x `over y\n"):
        with pytest.raises(ParseError, match="operator"):
            S.parse(bad)
