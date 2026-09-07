"""`spec/transport.md` §3 — the invariants, checked by enumeration.

Two spellings of one model — the spec's type and the Python enum —
held to each other by name, and every invariant checked over every
state and verb.  Exhaustive, not sampled: three states, five
verbs, two values of `inert` is thirty steps.
"""

from __future__ import annotations

import re
from collections import deque
from itertools import product
from pathlib import Path

from gestate.transportstate import (State, Verb, OPENS_IN, facts, step,
                                   keyboard_audible)

ROOT = Path(__file__).resolve().parent.parent


def test_the_enums_name_constructors_of_the_chart():
    """The three words and the four verbs are the chart's own
    constructors — `transport.ges` is the truth, the enums its face."""
    from gestate.charts import load

    cons = load("transport").constructors
    for s in State:
        assert s.name.capitalize() in cons, s
    for v in Verb:
        assert v.name.capitalize() in cons, v


def test_entering_sounding_releases_the_held_notes():
    """`enter (Up Sounding) = [AllOff]` — an entry action on the state,
    folded in by `advance`, not written on every arrow."""
    from gestate.transportstate import advance, term_of

    new, acts = advance(term_of(State.PLAYING), Verb.PLAY)
    assert new == ("Up", ("Sounding",))
    assert acts == [("AllOff",)]


def test_play_and_audition_from_silent_resume_where_the_score_was_parked():
    """History as a payload: `Silent at` carries the position, and the
    arrow out of it seeks there — what `_parked` did by hand."""
    from gestate.transportstate import advance

    new, acts = advance(("Silent", 4410), Verb.PLAY)
    assert new == ("Up", ("Playing",))
    assert acts == [("Sound",), ("SeekTo", 4410)]
    new, acts = advance(("Silent", 4410), Verb.AUDITION)
    assert new == ("Up", ("Sounding",))
    assert acts == [("Sound",), ("SeekTo", 4410), ("AllOff",)]


def test_a_stop_parks_the_position_the_event_carried():
    """A chart never asks the world: the position arrives on the event."""
    from gestate.transportstate import advance, term_of

    new, acts = advance(term_of(State.PLAYING), Verb.STOP, at=777)
    assert new == ("Silent", 777)
    assert acts == [("Hush",)]


def test_two_charts_beside_each_other_share_nothing(tmp_path):
    """`beside` over the two real files, `transport.ges` and `hands.ges`:
    the product is the region, an event reaches one side, the other
    side's state is untouched, and each side's actions come back tagged
    — so two files that cannot share a type compose (Q2)."""
    from gestate.charts import Chart

    both = tmp_path / "both.ges"
    both.write_text(
        (ROOT / "gestate" / "transport.ges").read_text()
        + (ROOT / "gestate" / "hands.ges").read_text()
        + """
both : Chart (State, Hands) (Or Verb Piano) (Or Do Cue)
both = beside transport hands
""")
    chart = Chart(both, "both")
    assert chart.initial() == (("Up", ("Playing",)), ("Off",))
    new, acts = chart.advance((("Up", ("Playing",)), ("Off",)), ("R", ("PianoOn",)))
    assert new == (("Up", ("Playing",)), ("On",))
    assert acts == [("R", ("Loud",))], "the right side's entry cue, tagged"
    new, acts = chart.advance(new, ("L", ("Stop", 5)))
    assert new == (("Silent", 5), ("On",))
    assert acts == [("L", ("Hush",))], "the left side's action, tagged"


def test_the_hands_chart_lands_every_verb_in_its_state():
    from gestate.charts import load

    hands = load("hands")
    assert hands.initial() == ("Off",)
    for verb, state, cue in (("PianoOn", "On", "Loud"),
                             ("PianoStep", "Noting", "Written"),
                             ("PianoOff", "Off", "Quiet")):
        for here in ("Off", "On", "Noting"):
            new, cues = hands.advance((here,), (verb,))
            assert new == (state,) and cues == [(cue,)], (here, verb)


def test_I1_I2_I3_the_facts_are_a_function_of_the_state():
    for state in State:
        f = facts(state)
        assert f.card_held == (state is not State.SILENT), "I1"
        assert f.clock_moving == (state is State.PLAYING), "I2"
        assert f.engine_up == f.card_held, "I3"


def test_I4_step_is_total():
    for state, verb, inert in product(State, Verb, (False, True)):
        assert step(state, verb, inert) in State


def test_I5_an_inert_file_is_silent_under_every_verb():
    for state, verb in product(State, Verb):
        assert step(state, verb, inert=True) is State.SILENT


def test_I6_every_mode_is_reachable_from_the_open_state():
    seen, todo = {OPENS_IN}, deque([OPENS_IN])
    while todo:
        here = todo.popleft()
        for verb in Verb:
            there = step(here, verb)
            if there not in seen:
                seen.add(there)
                todo.append(there)
    assert seen == set(State)


def test_I7_stop_never_brings_the_engine_up():
    for state in State:
        if not facts(state).engine_up:
            assert not facts(step(state, Verb.STOP)).engine_up


def test_I8_seek_keeps_the_state():
    for state in State:
        assert step(state, Verb.SEEK) is state


def test_I9_stop_lands_in_silent_from_every_state():
    for state in State:
        assert step(state, Verb.STOP) is State.SILENT
        assert not facts(step(state, Verb.STOP)).card_held, "the card is free"


def test_I10_audition_never_lands_in_silent():
    for state in State:
        assert step(state, Verb.AUDITION) is not State.SILENT


def test_the_sentences_4_and_5_the_verbs_land_where_they_say():
    assert step(State.SOUNDING, Verb.PLAY) is State.PLAYING
    assert step(State.SILENT, Verb.PLAY) is State.PLAYING, "sentence 5"
    assert step(State.PLAYING, Verb.PLAY) is State.SOUNDING, "the toggle"
    assert step(State.SILENT, Verb.AUDITION) is State.SOUNDING
    assert step(State.PLAYING, Verb.AUDITION) is State.PLAYING, "a rebuild"


def test_the_keyboard_is_a_conjunction_of_two_axes():
    assert keyboard_audible(State.SOUNDING, "on")
    assert not keyboard_audible(State.SOUNDING, "off")
    assert not keyboard_audible(State.SILENT, "on")
