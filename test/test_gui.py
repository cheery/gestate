"""The GUI backend — `fixme.md` F85.

`scenes(source, events)` is the whole thing as far as correctness goes: it
feeds events in and hands back the picture after each one.  It opens no
window and imports no pygame, so this file is cheap and runs anywhere —
the same split `midi.perform` and `midi.write` already have.

What is really under test is the *reactive* half.  A GUI program is a
`scan` over an event stream, and `scan` is guarded recursion: its recursive
call sits under a `delay`, which is what makes the signal productive.  If
that ever stops working, a picture here stops changing.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from gestate.gui import GuiError, scenes

GUI_DIR = Path(__file__).resolve().parent.parent / "examples" / "gui"
EXAMPLE = GUI_DIR / "bounce.ges"
CHAIN = GUI_DIR / "chain.ges"


def _source() -> str:
    return EXAMPLE.read_text()


def _ball(scene):
    """The `(x, y)` of the one dot in a scene."""
    dots = [s for s in scene if s[0] == "dot"]
    assert len(dots) == 1, f"expected one dot, got {len(dots)}"
    return dots[0][1], dots[0][2]


# ── The example ─────────────────────────────────────────────────────────────


def test_the_example_draws_something_before_anything_happens():
    """`events` starts with `Tick`, so there is a picture at instant zero."""
    first = scenes(_source(), [])[0]
    assert len(first) == 3
    assert [s[0] for s in first] == ["rect", "rect", "dot"]


def test_a_tick_moves_the_ball():
    out = scenes(_source(), [("Tick",)])
    assert _ball(out[0]) != _ball(out[1])


def test_the_velocity_is_fractional():
    """The reason `Float` had to land first.

    At 2.3 pixels a frame the ball advances by 2, 2, 2, 3 — the fraction
    accumulates.  In integers it would move by 2 every frame, or by 0.
    """
    out = scenes(_source(), [("Tick",)] * 4)
    steps = [_ball(out[i + 1])[0] - _ball(out[i])[0] for i in range(4)]
    assert set(steps) == {2, 3}, steps


def test_a_press_puts_the_ball_under_the_pointer():
    out = scenes(_source(), [("Tick",), ("Press", 100, 200)])
    assert _ball(out[2]) == (100, 200)


def test_movement_alone_does_not_disturb_it():
    out = scenes(_source(), [("Move", 5, 5), ("Move", 300, 300)])
    assert _ball(out[0]) == _ball(out[1]) == _ball(out[2])


def test_it_bounces_and_stays_inside():
    """Reflecting on *exit* rather than clamping: it must not stick."""
    out = scenes(_source(), [("Tick",)] * 260)
    xs = [_ball(s)[0] for s in out]
    ys = [_ball(s)[1] for s in out]
    assert min(xs) >= 0 and min(ys) >= 0
    # A margin of one step: the reflection happens the frame *after* the
    # ball has left, which is what stops it sticking to the wall.
    assert max(xs) <= 480 + 4 and max(ys) <= 360 + 4
    forward = [xs[i + 1] - xs[i] > 0 for i in range(len(xs) - 1)]
    assert True in forward and False in forward, "never turned around"


def test_the_state_is_a_fold_so_the_frames_are_a_trajectory():
    """Frame n+1 depends on frame n — this is `scan`, not a redraw."""
    a = scenes(_source(), [("Tick",)] * 10)
    b = scenes(_source(), [("Press", 10, 10)] + [("Tick",)] * 10)
    assert _ball(a[-1]) != _ball(b[-1])


# ── The backend ─────────────────────────────────────────────────────────────


def test_a_static_program_needs_no_channel():
    """A program that never reads `events` allocates no channel.

    It is not an error to send events to it; the picture simply does not
    change, which is what a static scene means.
    """
    src = ("substrate : Sig Sub\n"
           "substrate = map (e => Rect 10 10 (RGB 1 2 3)) events\n")
    out = scenes(src, [("Tick",), ("Press", 1, 1)])
    assert out[0] == out[1] == out[2]
    # Placed by its centre, and the root's centre is the origin.
    assert out[0] == [("rect", -5, -5, 10, 10, (1, 2, 3))]


def test_colour_components_are_clamped():
    src = ("substrate : Sig Sub\n"
           "substrate = map (e => Shift 1 2 (Circle 3 (RGB 300 (0 - 5) 128)))"
           " events\n")
    assert scenes(src, [])[0] == [("dot", 1, 2, 3, (255, 0, 128))]


def test_an_unknown_event_says_which_ones_exist():
    with pytest.raises(GuiError, match="unknown event"):
        scenes(_source(), [("Wiggle", 1)])


def test_an_event_with_the_wrong_arity_is_caught():
    with pytest.raises(GuiError, match="argument"):
        scenes(_source(), [("Press", 1)])


def test_a_program_whose_scene_is_not_a_signal_is_rejected():
    from gestate.unify import UnifyError

    with pytest.raises((GuiError, UnifyError)):
        scenes("substrate : Sub\nsubstrate = Gap 0 0\n", [])


# ── The shape a program takes ───────────────────────────────────────────────


def test_folding_the_events_into_a_state_and_drawing_it():
    """Three definitions and a fold is a whole application.

    `world step init draw` used to name this; it was `map draw (scan step
    init events)` and nothing else, so it is written out now.  A
    combinator whose body is shorter than its own documentation was one
    name too many.
    """
    src = (
        "Counter := Counter Int\n\n"
        "bump : Counter -> Event -> Counter\n"
        "bump c e = case e of\n"
        "    Press x y -> case c of\n"
        "        Counter n -> Counter (n + 1)\n"
        "    Tick -> c\n"
        "    Move x y -> c\n"
        "    Release x y -> c\n"
        "    Key k -> c\n\n"
        "showCount : Counter -> Sub\n"
        "showCount c = case c of\n"
        "    Counter n -> Shift n 0 (Circle 1 (RGB 0 0 0))\n\n"
        "substrate : Sig Sub\n"
        "substrate = map showCount (scan bump (Counter 0) events)\n"
    )
    out = scenes(src, [("Press", 0, 0), ("Tick",), ("Press", 0, 0)])
    assert [s[0][1] for s in out] == [0, 1, 1, 2]


# ── `chain.ges` — list state ────────────────────────────────────────────────


def _dots(scene):
    return [s[1:3] for s in scene if s[0] == "dot"]


def test_every_gui_example_is_exercised_here():
    assert {p.name for p in GUI_DIR.glob("*.ges")} == {"bounce.ges", "chain.ges"}


def test_the_chain_keeps_its_length():
    """A new head is prepended as the last is dropped."""
    out = scenes(CHAIN.read_text(), [("Move", 400, 100)] + [("Tick",)] * 20)
    assert all(len(_dots(s)) == 16 for s in out)


def test_the_head_follows_the_pointer():
    out = scenes(CHAIN.read_text(), [("Move", 400, 100)] + [("Tick",)] * 30)
    hx, hy = _dots(out[-1])[0]
    assert abs(hx - 400) < 5 and abs(hy - 100) < 5


def test_the_tail_lags_behind_the_head():
    """The trail *is* the past, carried explicitly — a signal does not
    remember, so the program has to."""
    out = scenes(CHAIN.read_text(), [("Move", 400, 100)] + [("Tick",)] * 8)
    head, tail = _dots(out[-1])[0], _dots(out[-1])[-1]
    assert head != tail
    assert abs(head[0] - 400) < abs(tail[0] - 400)


def test_the_chain_tapers():
    scene = scenes(CHAIN.read_text(), [])[0]
    radii = [s[3] for s in scene if s[0] == "dot"]
    assert radii == sorted(radii, reverse=True)
    assert radii[0] > radii[-1] >= 3


def test_moving_without_a_tick_does_not_move_the_chain():
    out = scenes(CHAIN.read_text(), [("Move", 10, 10), ("Move", 470, 350)])
    assert _dots(out[0]) == _dots(out[1]) == _dots(out[2])
