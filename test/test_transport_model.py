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
SPEC = ROOT / "spec" / "transport.md"


def _spec_constructors(name: str) -> list[str]:
    text = SPEC.read_text(encoding="utf-8")
    m = re.search(rf"^\s*{name} := (.+)$", text, re.M)
    assert m, f"spec/transport.md no longer spells `{name} := …`"
    return [c.strip() for c in m.group(1).split("|")]



def test_the_two_spellings_agree_on_the_modes():
    assert _spec_constructors("State") == [m.name.capitalize() for m in State]


def test_the_two_spellings_agree_on_the_verbs():
    assert _spec_constructors("Verb") == [v.name.capitalize() for v in Verb]


def test_I1_I2_I3_the_facts_are_a_function_of_the_mode():
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


def test_I8_seek_keeps_the_mode():
    for state in State:
        assert step(state, Verb.SEEK) is state


def test_I9_stop_lands_in_silent_from_every_mode():
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
