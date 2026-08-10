"""`do` — the monad's sugar (`spec/monad.md`).

The sugar is a parser-level rewrite into `>>=` chains — no node
survives it — so what these tests hold is the *translation*: each
surface form against the spelling it means, through the machine, and
the score form against `perform_voices` where the bind's meaning is
already pinned by three other suites.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))

from gestate.crust import canonical
from gestate.gmachine import run
from gestate.pipeline import compile as compile_program
from gestate.syntax.ast import ParseError


def _value(source: str) -> str:
    state = compile_program(source)
    run(state)
    return canonical(state.stack[0], state)


def test_binds_lets_and_drops_desugar_to_the_chain_they_mean():
    """The three item forms in one block: binds thread, a `=` item is
    a `let` (no monad involved), a mid-block expression is dropped —
    and the last item is the block's value, `'` standing as `pure`
    the way the prelude already says it does."""
    sugar = _value("""
sum2 : Maybe Int
sum2 = do
    x <- Just 4
    y <- Just 5
    z = x + y
    Just 100
    '(z + 1)

main : Maybe Int
main = sum2
""")
    plain = _value("""
sum2 : Maybe Int
sum2 = Just 4 >>= (x => Just 5 >>= (y =>
    let z = x + y in Just 100 >>= (_ => '(z + 1))))

main : Maybe Int
main = sum2
""")
    assert sugar == plain
    assert "10" in sugar


def test_the_list_monad_reads_as_substitution():
    got = _value("""
flat : List Int
flat = do
    x <- [1, 2, 3]
    y <- [10, 20]
    '(x * y)

main : List Int
main = flat
""")
    want = _value("main : List Int\n"
                  "main = [1, 2, 3] >>= (x => [10, 20] >>= (y => '(x * y)))\n")
    assert got == want


def test_a_bind_short_circuits_like_the_bind_it_is():
    got = _value("""
short : Maybe Int
short = do
    x <- Just 1
    _ <- Nothing
    '(x + 99)

main : Maybe Int
main = short
""")
    assert got == "#80()"                     # Nothing


def test_one_line_holds_items_with_semicolons():
    got = _value("main : Maybe Int\n"
                 "main = (do a <- Just 7; b <- Just 8; '(a * b))\n")
    assert got == "#81(56)"                   # Just 56


def test_a_pattern_binds_like_a_lambda_parameter():
    got = _value("""
main : Maybe Int
main = do
    (a, b) <- Just (3, 4)
    '(a * b)
""")
    assert got == "#81(12)"


def test_do_over_a_score_is_the_bind_the_walks_already_pin():
    """The score instance: `do` on `[: a :]` is `>>=`, which three
    suites already hold to the bake — so here, only the translation."""
    from test_dynamicscore import RATE, SYNTH

    from gestate.audioscore import perform_voices

    sugared = """
line : [: Custom :]
line = '(Custom 1.0 60) ++ '(Custom 0.8 64)

score : [: Void :]
score = do
    k <- line
    voices.lead k

bpm : Int
bpm = 120
"""
    plain = sugared.replace(
        "do\n    k <- line\n    voices.lead k",
        "line >>= voices.lead")
    a = perform_voices(SYNTH, sugared, RATE)[1]
    b = perform_voices(SYNTH, plain, RATE)[1]
    assert a == b and a


def test_a_block_ending_in_a_bind_is_refused_by_name():
    with pytest.raises(ParseError, match="ends with an expression"):
        compile_program("bad : Maybe Int\nbad = do\n    x <- Just 1\n"
                        "\nmain : Int\nmain = 0\n")


def test_do_is_reserved_and_says_so():
    """A program using `do` as a name meets the keyword, not a silent
    reparse."""
    with pytest.raises(Exception):
        compile_program("do : Int\ndo = 5\nmain : Int\nmain = do\n")
