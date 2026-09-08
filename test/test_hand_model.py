"""`gestate/hand.ges` — a hand on the roll's notes, checked by enumeration.

Eight states, four touches, three things a press can find: every pair
walked with a number or two standing in for a tick or a key, and every
arrow the roll's `if` ladders used to be is here as a fact about the
chart (`card:gui-is-difficult.md`, 2026-09-08, reading A).
"""

from __future__ import annotations

from collections import deque
from itertools import product

import pytest

from gestate.charts import load

FREE = ("Free",)
STATES = [FREE, ("Railed", 3), ("Held", 7, 3, 60), ("Carried", 7, 3, 60, 5, 62),
          ("Ending", 7, 3), ("Ended", 7, 3, 9), ("Sweeping", 3, 60), ("Swept", 3, 60, 5, 62)]
TOUCHES = [("Rail", 8), ("Pitch", 64, ("OnNote", 2)), ("Pitch", 64, ("OnEnd", 2)),
           ("Pitch", 64, ("OnRoll",)), ("Lift",), ("Abort",)]


@pytest.fixture(scope="module")
def hand():
    return load("hand")


def test_every_hand_starts_free(hand):
    assert hand.initial() == FREE


def test_every_state_answers_every_touch(hand):
    """Total: eight states, six touches, forty-eight answers, none an
    error — the chart has no catch-all on the touch."""
    for state, touch in product(STATES, TOUCHES):
        hand.advance(state, touch)


def test_the_rail_speaks_first_and_the_pitch_decides_which_hand(hand):
    assert hand.advance(FREE, ("Pitch", 64, ("OnNote", 2))) == (None, []), "a pitch touch with no rail before it is nothing"
    new, acts = hand.advance(FREE, ("Rail", 3))
    assert new == ("Railed", 3) and acts == []
    assert hand.advance(new, ("Rail", 4)) == (("Railed", 4), []), "the rail may move before the pitch speaks"
    assert hand.advance(new, ("Pitch", 60, ("OnNote", 7))) == (("Held", 7, 3, 60), [("Grab", 7, 3, 60)])
    assert hand.advance(new, ("Pitch", 60, ("OnEnd", 7))) == (("Ending", 7, 3), [("GrabEnd", 7, 3)])
    assert hand.advance(new, ("Pitch", 60, ("OnRoll",))) == (("Sweeping", 3, 60), [("Clear", 3, 60)])
    assert hand.advance(new, ("Lift",)) == (FREE, []), "the rail alone, let go, commits nothing"


def test_a_held_note_is_carried_on_either_axis_from_where_it_was_taken(hand):
    held = ("Held", 7, 3, 60)
    new, acts = hand.advance(held, ("Rail", 5))
    assert new == ("Carried", 7, 3, 60, 5, 60) and acts == [("Shift", 7, 3, 60, 5, 60)]
    new, acts = hand.advance(new, ("Pitch", 63, ("OnRoll",)))
    assert new == ("Carried", 7, 3, 60, 5, 63) and acts == [("Shift", 7, 3, 60, 5, 63)], \
        "the latest place on each axis, and the hit on a drag is not looked at"
    assert hand.advance(new, ("Lift",)) == (FREE, [("Carry", 7, 3, 60, 5, 63)])
    assert hand.advance(held, ("Lift",)) == (FREE, [("Click", 7)]), "let go where it was taken is a click"


def test_a_hand_on_an_end_carries_no_pitch(hand):
    ending = ("Ending", 7, 3)
    assert hand.advance(ending, ("Pitch", 70, ("OnRoll",))) == (None, [])
    new, acts = hand.advance(ending, ("Rail", 9))
    assert new == ("Ended", 7, 3, 9) and acts == [("Grow", 7, 3, 9)]
    assert hand.advance(new, ("Pitch", 70, ("OnRoll",))) == (None, [])
    assert hand.advance(new, ("Lift",)) == (FREE, [("Resize", 7, 3, 9)])
    assert hand.advance(ending, ("Lift",)) == (FREE, [("Click", 7)])


def test_a_band_is_swept_from_its_corner_and_let_go_selects(hand):
    sweeping = ("Sweeping", 3, 60)
    new, acts = hand.advance(sweeping, ("Rail", 5))
    assert new == ("Swept", 3, 60, 5, 60) and acts == [("Sweep", 3, 60, 5, 60)]
    new, acts = hand.advance(new, ("Pitch", 62, ("OnRoll",)))
    assert new == ("Swept", 3, 60, 5, 62) and acts == [("Sweep", 3, 60, 5, 62)]
    assert hand.advance(new, ("Lift",)) == (FREE, [("Select", 3, 60, 5, 62)])
    assert hand.advance(sweeping, ("Lift",)) == (FREE, [("Drop",)]), "a click on nothing selects nothing"


def test_abort_lands_free_from_anywhere_and_undoes_the_picture(hand):
    for state in STATES[2:]:
        assert hand.advance(state, ("Abort",)) == (FREE, [("Drop",)]), state
    assert hand.advance(("Railed", 3), ("Abort",)) == (FREE, [])
    assert hand.advance(FREE, ("Abort",)) == (None, [])


def test_every_state_is_reachable_and_no_hand_is_held_forever(hand):
    seen, queue = {FREE}, deque([FREE])
    while queue:
        here = queue.popleft()
        for touch in TOUCHES:
            new, _acts = hand.advance(here, touch)
            if new is not None and new[0] not in {s[0] for s in seen}:
                seen.add(new)
                queue.append(new)
    assert {s[0] for s in seen} == {s[0] for s in STATES}
    for state in seen:
        new, _acts = hand.advance(state, ("Lift",))
        assert (new or state) == FREE, state


def test_the_session_hosts_the_chart_for_the_roll():
    import inspect

    from gestate.session import Session

    source = inspect.getsource(Session._hand_act)
    for act in ("Grab", "GrabEnd", "Shift", "Click", "Carry", "Grow", "Resize",
                "Sweep", "Select", "Clear", "Drop"):
        assert f'"{act}"' in source, act
    assert 'load("hand")' in inspect.getsource(Session._hand_event)
