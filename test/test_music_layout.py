"""`music.ges`'s layout agrees with a direct model of it — `fixme.md` F76.

`lay` used to be written the obvious way: `Seq a b` laid both sides and
`append ea (shiftEvents da eb)`.  A melody is one long `Seq` chain, so each
level copied the events gathered so far and laying out n notes cost O(n²).

It now carries an *offset down* instead of shifting events up, and prepends
onto an accumulator instead of appending — which reverses the result, undone
once at the end.  That is a different algorithm computing the same thing, and
"the same thing" is what this file checks: a reference implementation of the
original semantics, run against randomly shaped scores.

The interesting cases are `Scale` and `Shrink`, because an offset does *not*
compose with them — an event at local `x` inside `Scale t k` belongs at
`off + x*k`, not `(off + x)*k` — so those two lay their subtree at the origin
and transform its events.  A generator that nests them under `Seq` and `At`
is the point of the exercise.
"""

from __future__ import annotations

import random

import pytest

BEAT = 96


# ── A reference implementation of the original `lay` ─────────────────────────


def _lay(node):
    """`(duration, [(onset, offset, key)])`, written the direct way."""
    kind = node[0]
    if kind == "note":
        return BEAT, [(0, BEAT, node[1])]
    if kind == "rest":
        return BEAT, []
    if kind == "seq":
        da, ea = _lay(node[1])
        db, eb = _lay(node[2])
        return da + db, ea + [(a + da, b + da, x) for a, b, x in eb]
    if kind == "over":
        da, ea = _lay(node[1])
        db, eb = _lay(node[2])
        return max(da, db), ea + eb
    if kind == "at":
        dt, et = _lay(node[2])
        n = node[1]
        return dt, [(a + n, b + n, x) for a, b, x in et]
    if kind == "scale":
        dt, et = _lay(node[1])
        k = node[2]
        return dt * k, [(a * k, b * k, x) for a, b, x in et]
    if kind == "shrink":
        dt, et = _lay(node[1])
        k = node[2]
        # `prim_div_int` is Python's `//` — floor, not truncation, which
        # matters once `at` has moved a coordinate negative.
        return dt // k, [(a // k, b // k, x) for a, b, x in et]
    raise AssertionError(kind)


def _source(node) -> str:
    """The same tree as gestate surface syntax, fully parenthesised."""
    kind = node[0]
    if kind == "note":
        return f"('{node[1]})"
    if kind == "rest":
        return "r"
    if kind == "seq":
        return f"({_source(node[1])} ++ {_source(node[2])})"
    if kind == "over":
        return f"({_source(node[1])} || {_source(node[2])})"
    if kind == "at":
        n = node[1]
        arg = str(n) if n >= 0 else f"(0 - {-n})"
        return f"(at {arg} {_source(node[2])})"
    if kind == "scale":
        return f"({_source(node[1])} |* {node[2]})"
    if kind == "shrink":
        return f"({_source(node[1])} |/ {node[2]})"
    raise AssertionError(kind)


def _random_score(rng, depth, keys):
    if depth <= 0 or rng.random() < 0.18:
        if rng.random() < 0.15:
            return ("rest",)
        keys[0] += 1
        return ("note", 40 + keys[0])
    # Weighted toward the branching pair: `at`/`scale`/`shrink` are unary,
    # so an even choice spends the depth budget on a thin spine and the
    # generated scores come out one or two notes long.
    pick = rng.choice(["seq", "seq", "seq", "seq", "over", "over",
                       "at", "scale", "shrink"])
    if pick in ("seq", "over"):
        return (pick, _random_score(rng, depth - 1, keys),
                _random_score(rng, depth - 1, keys))
    if pick == "at":
        return ("at", rng.choice([-BEAT, -13, 0, 7, BEAT]),
                _random_score(rng, depth - 1, keys))
    return (pick, _random_score(rng, depth - 1, keys), rng.randint(1, 4))


def _render(node) -> list[tuple[int, int, int]]:
    """What gestate actually lays out, as `(onset, offset, key)`."""
    from gestate.midi import perform

    _bpm, events = perform(
        f"score : [: Void :]\nscore = {_source(node)} >>= prog 0\n\n"
        "bpm : Int\nbpm = 120\n")
    return [(on, off, key) for on, off, _prog, key, _vel in events]


# ── The property ─────────────────────────────────────────────────────────────


@pytest.mark.parametrize("seed", range(14))
def test_layout_agrees_with_the_direct_model(seed):
    rng = random.Random(seed)
    node = _random_score(rng, 6, [0])
    _dur, expected = _lay(node)
    assert _render(node) == expected, _source(node)


def test_a_long_sequence_lays_out_in_order():
    node = ("note", 60)
    for k in range(1, 40):
        node = ("seq", node, ("note", 60 + k))
    _dur, expected = _lay(node)
    assert _render(node) == expected


def test_scaling_nested_under_a_sequence():
    # The case an offset cannot be folded through: the scaled subtree does
    # not start at the origin, so `(off + x) * k` would be wrong.
    node = ("seq", ("note", 60),
            ("scale", ("seq", ("note", 61), ("note", 62)), 3))
    _dur, expected = _lay(node)
    assert _render(node) == expected


def test_shrinking_after_a_negative_translation():
    node = ("seq", ("note", 60), ("shrink", ("at", -13, ("note", 61)), 2))
    _dur, expected = _lay(node)
    assert _render(node) == expected


def test_overlay_keeps_both_voices_in_order():
    node = ("over", ("seq", ("note", 60), ("note", 62)), ("note", 67))
    _dur, expected = _lay(node)
    assert _render(node) == expected


# ── `reverse` is linear too ──────────────────────────────────────────────────

_UPTO = ("upTo : Int -> List Int\n"
         "upTo n = case n == 0 of\n"
         "    True -> []\n"
         "    False -> n :: upTo (n - 1)\n\n"
         "firstOr : Int -> List Int -> Int\n"
         "firstOr d xs = case xs of\n"
         "    [] -> d\n"
         "    x :: rest -> x\n\n")


def test_reverse_still_reverses():
    from gestate.pipeline import evaluate

    # It was `append (reverse rest) (single x)` — correct, and O(n²) for the
    # one list function nobody expects to be expensive.  `lay` now calls it
    # once per layout, so a quadratic reverse would have undone the fix.
    assert evaluate(_UPTO + "main : Int\nmain = firstOr 0 (reverse [1,2,3,4])\n") == "4"
    assert evaluate(_UPTO + "main : Int\nmain = firstOr 9 (reverse [])\n") == "9"
    assert evaluate("main : Int\nmain = length (reverse [1,2,3])\n") == "3"
    assert evaluate("main : Int\nmain = sum (reverse [1,2,3])\n") == "6"


def test_reverse_of_a_long_list_is_not_quadratic():
    from gestate.pipeline import evaluate

    # 400 elements: slow if quadratic, instant if not.  Asserting the answer
    # rather than the clock — a wall-clock bound would be flaky, and a
    # quadratic reverse makes this test itself the alarm by dragging.
    assert evaluate(
        _UPTO + "main : Int\nmain = firstOr 0 (reverse (upTo 400))\n") == "1"
