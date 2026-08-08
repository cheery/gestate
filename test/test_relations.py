"""Sets over element types other than `Int`, and the queries they allow.

A Datalog relation is a set of *tuples*, so until the generated set
operations could order a pair, no relation could be built and the only
query expressible was over a unary relation of integers.  Three things had
to change: the element comparator became structural rather than
`prim_eq_int` (`fixme.md` F11), a set literal is now canonicalised instead
of trusting the author to write it sorted, and δ's parameters are
interleaved rather than grouped (F2), which is what a two-argument helper
needs.
"""

from __future__ import annotations

import pytest

from gestate.pipeline import evaluate


def _cells(source: str) -> int:
    """How many elements the resulting set has."""
    return evaluate(source).count("Pack{1,2}")


# ── Element types ────────────────────────────────────────────────────────────


def test_a_set_of_booleans():
    assert _cells("main : Set Bool\nmain = {True, False}") == 2


def test_a_set_of_characters():
    assert _cells("main : Set Char\nmain = {chr 98, chr 97}") == 2


def test_a_set_of_pairs():
    assert _cells("main : Set (Cyclic 4, Cyclic 4)\n"
                  "main = {(0, 1), (1, 2)}") == 2


def test_a_set_of_sets():
    # Two outer elements, each a one-element set — `_cells` counts cons
    # cells, so the inner sets count too.
    assert _cells("main : Set (Set (Cyclic 4))\nmain = {{1}, {0}}") == 4


def test_a_set_of_triples():
    assert _cells("main : Set (Cyclic 4, Cyclic 4, Cyclic 4)\n"
                  "main = {(0, 1, 2), (0, 1, 3)}") == 2


# ── Canonicalisation ─────────────────────────────────────────────────────────


def test_a_literal_deduplicates():
    assert _cells("main : Set (Cyclic 4)\nmain = {1, 1, 2}") == 2


def test_a_literal_deduplicates_pairs():
    assert _cells("main : Set (Cyclic 4, Cyclic 4)\n"
                  "main = {(0, 1), (0, 1)}") == 1


def test_a_literal_written_out_of_order_is_sorted():
    """Every set operation is a merge and assumes sorted operands."""
    assert _cells("main : Set (Cyclic 4)\nmain = {3, 1, 2}") == 3
    assert _cells("main : Set (Cyclic 4, Cyclic 4)\n"
                  "main = {(1, 2), (0, 1)}") == 2


def test_an_unordered_literal_still_unions_correctly():
    assert _cells("main : Set (Cyclic 8)\n"
                  "main = {3, 1} \\/ {2, 1}") == 3


def test_the_empty_literal():
    assert _cells("main : Set (Cyclic 4)\nmain = {}") == 0


# ── Multi-argument helpers under ϕ/δ (F2) ────────────────────────────────────


def test_a_two_argument_helper_inside_a_fixed_point():
    """δ supplies `f_delta ϕa δa ϕb δb`; grouping the parameters bound
    `dx₁` to `b`.  Arity 1 hid it — the two orders coincide there."""
    assert _cells("""pair : (Cyclic 4, Cyclic 4) -> (Cyclic 4, Cyclic 4) -> Set (Cyclic 4, Cyclic 4)
pair p q = {(fst p, snd q)}

f : Box (Set (Cyclic 4, Cyclic 4)) -> Set (Cyclic 4, Cyclic 4)
f be = unbox e = be in fix Box (r => e \\/ (for (p in r) (for (q in e) (pair p q))))

main : Set (Cyclic 4, Cyclic 4)
main = f (Box {(0, 1)})
""") == 1


# ── The query the whole thing is for ─────────────────────────────────────────

CLOSURE = """compose : (Cyclic 8, Cyclic 8) -> (Cyclic 8, Cyclic 8) -> Set (Cyclic 8, Cyclic 8)
compose p q = case snd p == fst q of
    True -> {(fst p, snd q)}
    False -> {}

closure : Box (Set (Cyclic 8, Cyclic 8)) -> Set (Cyclic 8, Cyclic 8)
closure be = unbox e = be in fix Box (r => e \\/ (for (p in r) (for (q in e) (compose p q))))

main : Set (Cyclic 8, Cyclic 8)
main = closure (Box {%s})
"""


def test_transitive_closure_of_a_path():
    """`{(0,1), (1,2)}` closes to `{(0,1), (0,2), (1,2)}`."""
    assert evaluate(CLOSURE % "(0, 1), (1, 2)") == (
        "Pack{1,2} (0, 1) Pack{1,2} (0, 2) Pack{1,2} (1, 2) Pack{0,0}")


def test_transitive_closure_of_a_longer_path():
    # 0→1→2→3 closes to all 6 ordered pairs i<j.
    assert evaluate(CLOSURE % "(0, 1), (1, 2), (2, 3)").count("Pack{1,2}") == 6


def test_transitive_closure_of_a_cycle_is_complete():
    # A 3-cycle closes to every one of the 9 pairs.
    assert evaluate(CLOSURE % "(0, 1), (1, 2), (2, 0)").count("Pack{1,2}") == 9


def test_transitive_closure_of_a_disconnected_graph():
    # Two disjoint edges compose with nothing.
    assert evaluate(CLOSURE % "(0, 1), (2, 3)").count("Pack{1,2}") == 2


# ── Rejections ───────────────────────────────────────────────────────────────


def test_a_set_of_an_unorderable_type_is_reported():
    """A data type is a fine set element now — unless a *field* is not.

    `C := R | G` is comparable by constructor position, so `Set C` works
    (roadmap 2.3).  A field the helpers cannot order is still refused, and
    the eqtype check gets there first.
    """
    from gestate.helpers import ComparatorError
    from gestate.pipeline import SubgrammarError

    with pytest.raises((ComparatorError, SubgrammarError)):
        evaluate("D := D (Sig Int)\n\nmain : Set D\nmain = {}\n")
