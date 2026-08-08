"""`gestate/signal.ges` — the combinators both reactive backends share.

`zip` is the one worth testing hard.  Two signals need not tick together:
each has its own clock, so combining them is not pairing up their tails but
asking `sync` which arrived and carrying the other one over.  That carrying
is sound only because a signal is a *cell* overwritten in place — the one
that did not tick still holds what it held.

**A note on channel identifiers**, because it cost an hour: they are handed
out in *evaluation* order, not declaration order, and `:::` evaluates its
tail before its value.  So in a program declaring `lchan` then `rchan`, the
*right* signal's channel is 0.  The tests below settle which is which by
element type rather than assuming, which is the only reliable way.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from gestate.gmachine import NNum
from gestate.pipeline import compile
from gestate.reactive import init_program, react

SIGNAL = (Path(__file__).resolve().parent.parent
          / "gestate" / "signal.ges").read_text()

#: Two signals on independent clocks, told apart by their element type.
TWO_CLOCKS = SIGNAL + """
lchan : Chan Int
lchan = chan

rchan : Chan Char
rchan = chan

ls : Sig Int
ls = 100 ::: mkSig (wait lchan)

rs : Sig Char
rs = chr 97 ::: mkSig (wait rchan)

main : Sig Int
main = zip (a b => a * 1000 + ord b) ls rs
"""


def _start(src):
    state = compile(src)
    reactive = init_program(state)
    return state, reactive, state.stack[0]


def _channels(reactive):
    """`(left, right)` channel ids, identified by element type."""
    left = [k for k, t in reactive.chans.items() if t == "Int"][0]
    right = [k for k, t in reactive.chans.items() if t == "Char"][0]
    return left, right


# ── Two clocks ──────────────────────────────────────────────────────────────


def test_channel_ids_follow_evaluation_order_not_declaration_order():
    """Recorded because it is genuinely surprising, and a trap.

    `lchan` is declared first and gets the *higher* id, because `:::`
    evaluates its tail — which is where `wait rchan` lives — before its
    value.  Anything reading `chans` positionally will be wrong.
    """
    _state, reactive, _sig = _start(TWO_CLOCKS)
    assert reactive.chans[0] == "Char", reactive.chans
    assert reactive.chans[1] == "Int"


def test_it_pairs_the_current_values_at_the_first_instant():
    _state, reactive, sig = _start(TWO_CLOCKS)
    assert sig.value.n == 100 * 1000 + 97


def test_only_the_left_advancing_keeps_the_right():
    _state, reactive, sig = _start(TWO_CLOCKS)
    left, _right = _channels(reactive)
    react(reactive, [(left, NNum(101))])
    assert sig.value.n == 101 * 1000 + 97


def test_only_the_right_advancing_keeps_the_left():
    _state, reactive, sig = _start(TWO_CLOCKS)
    _left, right = _channels(reactive)
    react(reactive, [(right, NNum(98))])
    assert sig.value.n == 100 * 1000 + 98


def test_they_advance_independently_over_a_sequence():
    _state, reactive, sig = _start(TWO_CLOCKS)
    left, right = _channels(reactive)
    seen = [sig.value.n]
    for chan, val in [(left, 101), (right, 98), (left, 102), (right, 99)]:
        react(reactive, [(chan, NNum(val))])
        seen.append(sig.value.n)
    assert seen == [100097, 101097, 101098, 102098, 102099]


# ── One clock, which is what a backend actually does ────────────────────────


ONE_CLOCK = SIGNAL + """
c : Chan Int
c = chan

base : Sig Int
base = 0 ::: mkSig (wait c)

main : Sig Int
main = zip (a b => a * 100 + b) (map (x => x + 1) base) (map (x => x * 2) base)
"""


def test_two_signals_from_one_clock_stay_in_step():
    state, reactive, sig = _start(ONE_CLOCK)
    out = [sig.value.n]
    for v in (3, 5, 7):
        react(reactive, [(0, NNum(v))])
        out.append(sig.value.n)
    assert out == [(v + 1) * 100 + v * 2 for v in (0, 3, 5, 7)]


def test_add_sig_mixes_two_float_signals():
    """The reason `zip` was wanted: two oscillators as two signals."""
    src = SIGNAL + """
c : Chan Int
c = chan

base : Sig Int
base = 0 ::: mkSig (wait c)

a : Sig Float
a = map (n => toFloat n) base

b : Sig Float
b = map (n => toFloat n * 0.5) base

main : Sig Float
main = gain 2.0 (addSig a b)
"""
    state, reactive, sig = _start(src)
    react(reactive, [(0, NNum(4))])
    assert sig.value.n == pytest.approx(2.0 * (4.0 + 2.0))


# ── The other combinators, still working from the shared file ───────────────


def test_scan_accumulates():
    src = SIGNAL + """
c : Chan Int
c = chan

main : Sig Int
main = scan (a b => a + b) 0 (0 ::: mkSig (wait c))
"""
    state, reactive, sig = _start(src)
    out = [sig.value.n]
    for v in (5, 3, 10, 1):
        react(reactive, [(0, NNum(v))])
        out.append(sig.value.n)
    assert out == [0, 5, 8, 18, 19]


def test_map_sig_maps():
    src = SIGNAL + """
c : Chan Int
c = chan

main : Sig Int
main = map (x => x * 3) (1 ::: mkSig (wait c))
"""
    state, reactive, sig = _start(src)
    assert sig.value.n == 3
    react(reactive, [(0, NNum(5))])
    assert sig.value.n == 15


def test_both_backends_prepend_the_same_file():
    from gestate import audio, gui

    assert audio._SIGNAL == gui._SIGNAL == SIGNAL
    # `zip` is a *method* here — `instance Zip Sig`, with the class in
    # `prelude.ges` beside `Functor` — so it is looked for as one.
    for name in ("mkSig", "mapSig", "scan", "zipSig", "addSig", "gain"):
        assert f"\n{name} " in SIGNAL, name
    assert "instance Zip Sig" in SIGNAL
