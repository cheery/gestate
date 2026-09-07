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
    """The commands that name a mode, and the one that keeps it."""
    PLAY = "play"
    STOP = "stop"
    SOUND = "sound"
    SILENCE = "silence"
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


#: Where a program file opens (today: the card taken at once).
OPENS_IN = Mode.SOUNDING


def step(mode: Mode, verb: Verb, inert: bool = False) -> Mode:
    """One verb, one step — sentences 4, 5, 6 and 8.  Total."""
    if inert:
        return Mode.SILENT
    if verb is Verb.PLAY:
        # `play` is a toggle from playing (`command.ges`: *start the
        # transport, or stop it if it is running*), and from silent it
        # brings the engine up and plays — one word, two changes.
        return Mode.SOUNDING if mode is Mode.PLAYING else Mode.PLAYING
    if verb is Verb.STOP:
        # Nothing to stop in silent, and stop never brings the engine up.
        return Mode.SILENT if mode is Mode.SILENT else Mode.SOUNDING
    if verb is Verb.SOUND:
        return Mode.SOUNDING
    if verb is Verb.SILENCE:
        return Mode.SILENT
    return mode                                  # seek keeps the mode


def keyboard_audible(mode: Mode, performing: str) -> bool:
    """The neighbour the model names and does not own: the keyboard is
    heard when the engine is up **and** `performing` is not `off`."""
    return facts(mode).engine_up and performing != "off"
