"""The transport's three modes — `spec/transport.md` §2, the type.

**Written before the transport reads it** (`card:transport-modes.md`,
day one, 2026-09-07): the model in Python, held to the spec's spelling
by `test/test_transport_model.py`,
which also checks every invariant in §3 over every mode and verb.
Nothing here touches `Transport`; when it lands, `Transport.playing`
becomes a `Mode` and `Workbench.play`/`pause` call `step`.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class Mode(Enum):
    """Exactly one of these — sentence 1."""
    SILENT = "silent"        # engine down, card free, clock held
    SOUNDING = "sounding"    # engine up, card held, clock held
    PLAYING = "playing"      # engine up, card held, clock moving


class Verb(Enum):
    """The commands that name a mode — the window's own three, Henri,
    2026-09-07: *"'stop' goes to silence, 'play' goes to playing,
    'audition' goes to 'sounding'"* — and the one that keeps it."""
    PLAY = "play"
    STOP = "stop"
    AUDITION = "audition"
    SEEK = "seek"


@dataclass(frozen=True)
class Facts:
    """What a mode decides — sentence 3.  A function of the mode, so a
    state like *card held, engine down* has no value to be written in."""
    engine_up: bool
    card_held: bool
    clock_moving: bool


def facts(mode: Mode) -> Facts:
    up = mode is not Mode.SILENT
    return Facts(engine_up=up, card_held=up,
                 clock_moving=mode is Mode.PLAYING)


#: Where a program file opens — *playing*, as it always has: "opening a
#: file and hearing it is the point" (`test_session_live.py`).  The
#: first draft of this model said *sounding*, which was the session
#: misreading the card's Q2; corrected 2026-09-07 while landing.
OPENS_IN = Mode.PLAYING


def step(mode: Mode, verb: Verb, inert: bool = False) -> Mode:
    """One verb, one step — sentences 4, 5, 6 and 8.  Total."""
    if inert:
        return Mode.SILENT
    if verb is Verb.PLAY:
        # `play` is a toggle from playing (`command.ges`: *start the
        # transport, or stop it if it is running*) and lands in
        # sounding — the score stops, the instrument stays up; from
        # silent it brings the engine up and plays, one word, two changes.
        return Mode.SOUNDING if mode is Mode.PLAYING else Mode.PLAYING
    if verb is Verb.STOP:
        # The word that frees the card, from anywhere.
        return Mode.SILENT
    if verb is Verb.AUDITION:
        # A request to hear: brings the engine up; while playing it is
        # a rebuild and the score keeps going.
        return Mode.PLAYING if mode is Mode.PLAYING else Mode.SOUNDING
    return mode                                  # seek keeps the mode


def keyboard_audible(mode: Mode, performing: str) -> bool:
    """The neighbour the model names and does not own: the keyboard is
    heard when the engine is up **and** `performing` is not `off`."""
    return facts(mode).engine_up and performing != "off"
