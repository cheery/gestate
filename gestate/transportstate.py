"""The transport's three states — the Python face of `transport.ges`.

**The chart is the truth** (`card:gui-is-difficult.md` §"The first
slice", 2026-09-07 evening): `step` and `advance` here ask
`gestate/transport.ges` through `charts.load`, and the enums are the
three words the bar, the session and the tests speak.  Before that, one
afternoon, `step` was written out here in Python; `spec/transport.md`
tells the order.  `test/test_transport_model.py` walks every state and
verb through the chart and holds the enums to its constructors.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class State(Enum):
    """Exactly one of these — sentence 1."""
    SILENT = "silent"        # engine down, card free, clock held
    SOUNDING = "sounding"    # engine up, card held, clock held
    PLAYING = "playing"      # engine up, card held, clock moving


class Verb(Enum):
    """The commands that name a state — the window's own three, Henri,
    2026-09-07: *"'stop' goes to silence, 'play' goes to playing,
    'audition' goes to 'sounding'"* — and the one that keeps it."""
    PLAY = "play"
    STOP = "stop"
    AUDITION = "audition"
    SEEK = "seek"


@dataclass(frozen=True)
class Facts:
    """What a state decides — sentence 3.  A function of the state, so a
    state like *card held, engine down* has no value to be written in."""
    engine_up: bool
    card_held: bool
    clock_moving: bool


def facts(state: State) -> Facts:
    up = state is not State.SILENT
    return Facts(engine_up=up, card_held=up,
                 clock_moving=state is State.PLAYING)


#: Where a program file opens — *playing*, as it always has: "opening a
#: file and hearing it is the point" (`test_session_live.py`).
OPENS_IN = State.PLAYING


# -- the chart, and the terms that cross to it ---------------------------------

def chart():
    from .charts import load

    return load("transport")


def term_of(state: State, at: int = 0):
    """The chart's spelling of a state: `Silent` carries the parked
    position, the other two sit under `Up`."""
    if state is State.SILENT:
        return ("Silent", int(at))
    return ("Up", ("Sounding",) if state is State.SOUNDING else ("Playing",))


def state_of(term) -> State:
    if term[0] == "Silent":
        return State.SILENT
    return State.SOUNDING if term[1] == ("Sounding",) else State.PLAYING


def event_of(verb: Verb, at: int = 0):
    if verb is Verb.STOP:
        return ("Stop", int(at))
    if verb is Verb.SEEK:
        return ("Seek", int(at))
    return (verb.name.capitalize(),)


def advance(term, verb: Verb, at: int = 0) -> tuple:
    """One event through the chart: `(new term, actions)`.  A `Stay`
    answers the same term and no actions."""
    new, actions = chart().advance(term, event_of(verb, at))
    return (term if new is None else new), actions


def step(state: State, verb: Verb, inert: bool = False) -> State:
    """One verb, one step — the chart's answer as the three words.
    Total; an inert file is silent under every verb (sentence 8)."""
    if inert:
        return State.SILENT
    new, _actions = advance(term_of(state), verb)
    return state_of(new)


def keyboard_audible(state: State, performing: str) -> bool:
    """The neighbour the model names and does not own: the keyboard is
    heard when the engine is up **and** `performing` is not `off`."""
    return facts(state).engine_up and performing != "off"
