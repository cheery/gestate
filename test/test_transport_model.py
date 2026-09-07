"""`spec/transport.md` §3 — the invariants, checked by enumeration.

Two spellings of one model — the spec's type and the Python enum —
held to each other by name, and every invariant checked over every
mode and verb.  Exhaustive, not sampled: three modes, five
verbs, two values of `inert` is thirty steps.
"""

from __future__ import annotations

import re
from collections import deque
from itertools import product
from pathlib import Path

from gestate.transportmode import (Mode, Verb, OPENS_IN, facts, step,
                                   keyboard_audible)

ROOT = Path(__file__).resolve().parent.parent
SPEC = ROOT / "spec" / "transport.md"


def _spec_constructors(name: str) -> list[str]:
    text = SPEC.read_text(encoding="utf-8")
    m = re.search(rf"^\s*{name} := (.+)$", text, re.M)
    assert m, f"spec/transport.md no longer spells `{name} := …`"
    return [c.strip() for c in m.group(1).split("|")]



def test_the_two_spellings_agree_on_the_modes():
    assert _spec_constructors("Mode") == [m.name.capitalize() for m in Mode]


def test_the_two_spellings_agree_on_the_verbs():
    assert _spec_constructors("Verb") == [v.name.capitalize() for v in Verb]


def test_I1_I2_I3_the_facts_are_a_function_of_the_mode():
    for mode in Mode:
        f = facts(mode)
        assert f.card_held == (mode is not Mode.SILENT), "I1"
        assert f.clock_moving == (mode is Mode.PLAYING), "I2"
        assert f.engine_up == f.card_held, "I3"


def test_I4_step_is_total():
    for mode, verb, inert in product(Mode, Verb, (False, True)):
        assert step(mode, verb, inert) in Mode


def test_I5_an_inert_file_is_silent_under_every_verb():
    for mode, verb in product(Mode, Verb):
        assert step(mode, verb, inert=True) is Mode.SILENT


def test_I6_every_mode_is_reachable_from_the_open_state():
    seen, todo = {OPENS_IN}, deque([OPENS_IN])
    while todo:
        here = todo.popleft()
        for verb in Verb:
            there = step(here, verb)
            if there not in seen:
                seen.add(there)
                todo.append(there)
    assert seen == set(Mode)


def test_I7_stop_never_brings_the_engine_up():
    for mode in Mode:
        if not facts(mode).engine_up:
            assert not facts(step(mode, Verb.STOP)).engine_up


def test_I8_seek_keeps_the_mode():
    for mode in Mode:
        assert step(mode, Verb.SEEK) is mode


def test_the_sentences_4_and_5_the_verbs_land_where_they_say():
    assert step(Mode.SOUNDING, Verb.PLAY) is Mode.PLAYING
    assert step(Mode.SILENT, Verb.PLAY) is Mode.PLAYING, "sentence 5"
    assert step(Mode.PLAYING, Verb.PLAY) is Mode.SOUNDING, "the toggle"
    assert step(Mode.PLAYING, Verb.STOP) is Mode.SOUNDING
    assert step(Mode.SILENT, Verb.STOP) is Mode.SILENT, "nothing to stop"
    assert step(Mode.PLAYING, Verb.SILENCE) is Mode.SILENT
    assert step(Mode.SILENT, Verb.SOUND) is Mode.SOUNDING


def test_the_keyboard_is_a_conjunction_of_two_axes():
    assert keyboard_audible(Mode.SOUNDING, "on")
    assert not keyboard_audible(Mode.SOUNDING, "off")
    assert not keyboard_audible(Mode.SILENT, "on")
