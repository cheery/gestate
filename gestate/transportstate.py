"""The transport's three states — `spec/transport.md` §2, the type.

**Written before the transport reads it** (`card:transport-modes.md`,
day one, 2026-09-07): the model in Python, held to the spec's spelling
by `test/test_transport_model.py`,
which also checks every invariant in §3 over every state and verb.
Nothing here touches `Transport`; when it lands, `Transport.playing`
becomes a `State` and `Workbench.play`/`pause` call `step`.
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
#: file and hearing it is the point" (`test_session_live.py`).  The
#: first draft of this model said *sounding*, which was the session
#: misreading the card's Q2; corrected 2026-09-07 while landing.
OPENS_IN = State.PLAYING


def step(state: State, verb: Verb, inert: bool = False) -> State:
    """One verb, one step — sentences 4, 5, 6 and 8.  Total."""
    if inert:
        return State.SILENT
    if verb is Verb.PLAY:
        # `play` is a toggle from playing (`command.ges`: *start the
        # transport, or stop it if it is running*) and lands in
        # sounding — the score stops, the instrument stays up; from
        # silent it brings the engine up and plays, one word, two changes.
        return State.SOUNDING if state is State.PLAYING else State.PLAYING
    if verb is Verb.STOP:
        # The word that frees the card, from anywhere.
        return State.SILENT
    if verb is Verb.AUDITION:
        # A request to hear: brings the engine up; while playing it is
        # a rebuild and the score keeps going.
        return State.PLAYING if state is State.PLAYING else State.SOUNDING
    return state                                  # seek keeps the state


def keyboard_audible(state: State, performing: str) -> bool:
    """The neighbour the model names and does not own: the keyboard is
    heard when the engine is up **and** `performing` is not `off`."""
    return facts(state).engine_up and performing != "off"
