"""`crust/` against `gmachine.py` — the mirror held to the reference.

Program for program: compile once in Python, run in both machines,
compare the canonical spelling of the forced result.  The programs are
chosen for the corners where a port quietly diverges — laziness and
sharing, floor division on negatives, case dispatch — and end on the
one that pays for the whole crate: the SplitMix64 seed arithmetic,
which is the future Rust score cursor's randomness, computed here to
the bit before that cursor exists.
"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest

from gestate.crust import canonical, serialize
from gestate.gmachine import run
from gestate.pipeline import compile as compile_program

CRUST = Path(__file__).resolve().parent.parent / "crust"

needs_cargo = pytest.mark.skipif(shutil.which("cargo") is None,
                                 reason="no cargo to build crust with")


@pytest.fixture(scope="module")
def crust_bin():
    subprocess.run(["cargo", "build", "--quiet", "--release"],
                   cwd=CRUST, check=True)
    return CRUST / "target" / "release" / "crust"


def _both(source: str, tmp_path, crust_bin) -> tuple:
    state = compile_program(source)
    text = serialize(state, "main")
    path = tmp_path / "program.crust"
    path.write_text(text)
    got = subprocess.run([crust_bin, path], capture_output=True, text=True,
                         check=True).stdout.strip()

    run(state)
    want = canonical(state.stack[0], state)
    return got, want


@needs_cargo
def test_arithmetic_and_recursion_agree(tmp_path, crust_bin):
    got, want = _both("""
fib : Int -> Int
fib n = case n < 2 of
    True -> n
    False -> fib (n - 1) + fib (n - 2)

main : Int
main = fib 15
""", tmp_path, crust_bin)
    assert got == want == "610"


@needs_cargo
def test_division_floors_like_the_reference(tmp_path, crust_bin):
    """`div_euclid` is not Python's `//` on a negative divisor — the
    exact quiet corner a parity suite exists for."""
    got, want = _both("""
main : (Int, Int, Int, Int)
main = ((0 - 7) / 2, (0 - 7) % 2, 7 / (0 - 2), 7 % (0 - 2))
""", tmp_path, crust_bin)
    assert got == want
    assert got.startswith("#") and "-4" in got and "-1" in got


@needs_cargo
def test_laziness_and_sharing_agree(tmp_path, crust_bin):
    """An endless list, taken from — `Update`'s sharing is what makes
    the second `head` free, and a port that copied instead of updating
    would still pass; one that mis-indexed the redex would not."""
    got, want = _both("""
from : Int -> List Int
from n = n :: from (n + 1)

grab : Int -> List Int -> List Int
grab n xs = case n < 1 of
    True -> []
    False -> case xs of
        [] -> []
        x :: rest -> x :: grab (n - 1) rest

main : List Int
main = grab 5 (map (x => x * x) (from 3))
""", tmp_path, crust_bin)
    assert got == want
    assert "9" in got and "49" in got


@needs_cargo
def test_the_seed_arithmetic_agrees_to_the_bit(tmp_path, crust_bin):
    """The one that pays for the crate: `music.ges`'s SplitMix64, in
    both machines, on seeds that force the 128-bit intermediates."""
    from gestate.audio import library_text

    music = library_text("music.ges")
    # The seed block's own words, sliced from the library so there is
    # one source of truth — up to `unit`, whose floats sit outside the
    # integer core this cut of crust carries.
    start = music.index("wrap64 : Int -> Int")
    stop = music.index("#: One uniform draw")
    seeds = music[start:stop]
    got, want = _both(seeds + """
main : (Int, Int, Int)
main = (mix64 (wrap64 42), mix64 (wrap64 9223372036854775825),
        prim_mod_int (mix64 (wrap64 123456789)) 97)
""", tmp_path, crust_bin)
    assert got == want

    M = (1 << 64) - 1

    def mix64(z):
        z &= M
        z ^= z >> 30
        z = (z * 0xBF58476D1CE4E5B9) & M
        z ^= z >> 27
        z = (z * 0x94D049BB133111EB) & M
        z ^= z >> 31
        return z

    assert str(mix64(42)) in got
