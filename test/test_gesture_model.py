"""`gestate/gesture.ges` — a hand on one thing, checked by enumeration.

The chart is finite up to its payloads, so every state and touch is
walked with a place or two standing in for the tick: three states,
three touches, nine steps — and every arrow the ruler's `if` ladder
used to be is here as a fact about the chart, not about the roll
(`card:gui-is-difficult.md`, 2026-09-08).
"""

from __future__ import annotations

from collections import deque
from itertools import product

import pytest

from gestate.charts import load

IDLE = ("Idle",)
STATES = [IDLE, ("Pressed", 3), ("Dragging", 3, 7)]
TOUCHES = [("Touched", 5), ("Released",), ("Cancel",)]


@pytest.fixture(scope="module")
def gesture():
    return load("gesture")


def test_every_hand_starts_empty(gesture):
    assert gesture.initial() == IDLE


def test_every_state_answers_every_touch(gesture):
    """Total: nine pairs, nine answers, none an error — the chart has
    no catch-all, so this is the pattern checker's word repeated."""
    for state, touch in product(STATES, TOUCHES):
        gesture.advance(state, touch)


def test_a_touch_while_idle_is_the_press_and_takes_hold_once(gesture):
    new, acts = gesture.advance(IDLE, ("Touched", 3))
    assert new == ("Pressed", 3)
    assert acts == [("Take", 3)], "the entry action, once, on the arrow in"


def test_a_touch_while_held_is_the_drag_and_previews_from_the_press(gesture):
    new, acts = gesture.advance(("Pressed", 3), ("Touched", 7))
    assert new == ("Dragging", 3, 7) and acts == [("Preview", 3, 7)]
    new, acts = gesture.advance(new, ("Touched", 9))
    assert new == ("Dragging", 3, 9), "the latest place, measured from the press"
    assert acts == [("Preview", 3, 9)], "and no Take: entering Dragging takes nothing"


def test_a_release_is_a_click_from_pressed_and_a_commit_from_dragging(gesture):
    new, acts = gesture.advance(("Pressed", 3), ("Released",))
    assert new == IDLE and acts == [("Reveal", 3)]
    new, acts = gesture.advance(("Dragging", 3, 7), ("Released",))
    assert new == IDLE and acts == [("Commit", 3, 7)], "both ends, so the host can say the interval"


def test_a_drag_back_to_where_it_began_is_still_a_commit(gesture):
    """The chart cannot know the host's grid, so it does not decide
    that a drag back is a click; it says `Commit p p` and the host,
    which knows what a bar is, decides — `Session._ruler_act`."""
    new, acts = gesture.advance(("Dragging", 3, 3), ("Released",))
    assert new == IDLE and acts == [("Commit", 3, 3)]


def test_cancel_lands_idle_from_anywhere_and_undoes_the_picture(gesture):
    for state in STATES[1:]:
        new, acts = gesture.advance(state, ("Cancel",))
        assert new == IDLE and acts == [("Unpreview",)], state
    assert gesture.advance(IDLE, ("Cancel",)) == (None, []), "nothing to undo while idle"


def test_a_release_while_idle_is_nothing(gesture):
    assert gesture.advance(IDLE, ("Released",)) == (None, [])


def test_every_state_is_reachable_and_every_gesture_ends_idle(gesture):
    """Breadth-first over the touches from `Idle`: every state is
    reached, and from every state a `Released` or a `Cancel` is one
    step from `Idle` — no hand is held forever."""
    seen, queue = {IDLE}, deque([IDLE])
    while queue:
        here = queue.popleft()
        for touch in TOUCHES:
            new, _acts = gesture.advance(here, touch)
            if new is not None and new[0] not in {s[0] for s in seen}:
                seen.add(new)
                queue.append(new)
    assert {s[0] for s in seen} == {"Idle", "Pressed", "Dragging"}
    for state in seen:
        for touch in (("Released",), ("Cancel",)):
            new, _acts = gesture.advance(state, touch)
            assert (new or state) == IDLE, (state, touch)


def test_the_session_hosts_the_chart_for_the_ruler():
    """The chart is the ruler's truth: `Session._ruler_event` asks it,
    and the acts it answers are the ones `_ruler_act` knows."""
    import inspect

    from gestate.session import Session

    source = inspect.getsource(Session._ruler_act)
    for act in ("Take", "Preview", "Reveal", "Commit", "Unpreview"):
        assert f'"{act}"' in source, act
    assert 'load("gesture")' in inspect.getsource(Session._ruler_event)
