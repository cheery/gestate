"""Which note goes to which voice — host policy, outside the language.

A `voices` bank is N fixed subgraphs (`audiovoices.py`).  Deciding *which*
one plays an arriving note is the part the static fragment cannot do, and
does not have to: it is a few integers, chosen here and delivered as
control values.

**The allocator emits changes, not sound.**  `note_on` returns a list of
`(channel name, value)` and nothing else, which is what lets the same
allocator serve both callers: live MIDI applies them to the running
engine's current values, and a `Score` writes them into a `Schedule` to be
rendered offline and checked against the oracle.  A note is the same thing
either way; only when it is decided differs.

A voice's channels are `gateAt`, `offAt`, then the **author's own record**,
field by field.  This module owns the first two and treats the rest as
opaque values it is handed: a payload's meaning belongs to the program that
declared it, and a note's *timing* belongs to the layout or the keyboard
that placed it.  Neither should be smuggled into the other.

`gateAt` and `offAt` are **1-based** sample indices, and that is the whole
trick of the encoding: zero means *nothing*, so a bank whose channels have
never been written reads as "no voice has ever played" rather than as
"every voice started at sample 0".  A voice therefore tests

    gateAt > 0 && n >= gateAt - 1          -- sounding
    offAt > 0 && n >= offAt - 1            -- released

and eight silent voices at start-up fall out of the channels' own defaults
rather than from anything the host has to remember to send.
"""

from __future__ import annotations

from dataclasses import dataclass, field

#: The first two channels of every voice.  `audiovoices.TIMING` generates
#: them, and a payload's own field `j` is channel `j + PAYLOAD`.
GATE_AT, OFF_AT, PAYLOAD = 0, 1, 2


class AllocError(Exception):
    pass


@dataclass
class Voice:
    """One voice of a bank, and what it is doing."""
    index: int
    #: What it is currently playing — a *key*, opaque to this module: a
    #: MIDI pitch, a score event's identity, whatever the caller uses to
    #: match a release to what it releases.  `None` means free.
    key: object = None
    #: The sample it started at — what "oldest" means when stealing.
    started: int = -1
    #: The sample it was released at, or `None` while it is held.
    released: int | None = None

    @property
    def free(self) -> bool:
        return self.key is None


def steal_oldest(voices: list) -> Voice:
    """The default: the voice that has been sounding longest.

    Conventional, and the one policy that is easy to explain to whoever is
    playing — hold nine notes on an eight-voice synth and the first one you
    played is the one that goes.
    """
    return min(voices, key=lambda v: (v.started, v.index))


def steal_none(voices: list):
    """Drop the note instead.  Returns `None`, and the note is not played."""
    return None


#: By name, so a caller can say `policy="oldest"` without importing one.
POLICIES = {"oldest": steal_oldest, "none": steal_none}


@dataclass
class Allocator:
    """A bank's voices, and the policy for when they are all busy."""

    #: `[[channel name per field] per voice]` — `audiovoices.channels_of`.
    channels: list
    policy: object = steal_oldest
    voices: list = field(default_factory=list)

    def __post_init__(self):
        if isinstance(self.policy, str):
            if self.policy not in POLICIES:
                raise AllocError(
                    f"no voice-stealing policy `{self.policy}`; there is "
                    + " and ".join(sorted(POLICIES)))
            self.policy = POLICIES[self.policy]
        if not self.channels:
            raise AllocError("a bank with no voices cannot play anything")
        self.voices = [Voice(i) for i in range(len(self.channels))]

    @property
    def fields(self) -> int:
        return len(self.channels[0])

    # -- choosing -----------------------------------------------------------

    def _pick(self, at: int):
        """A free voice, else whatever the policy says.

        Free voices are preferred **released-longest-ago first**, so a note
        lands on the voice whose tail has had the most time to decay rather
        than on the lowest-numbered one.  A voice that has never played
        counts as released at the beginning of time.
        """
        free = [v for v in self.voices if v.free]
        if free:
            return min(free, key=lambda v: (v.released
                                            if v.released is not None else -1,
                                            v.index))
        return self.policy(self.voices)

    # -- playing ------------------------------------------------------------

    def note_on(self, key, payload, at: int) -> list:
        """Start a note at sample `at`.  Returns the channel changes.

        `payload` is the values of the *author's own record*, in field
        order — this module does not know what they mean and does not need
        to.  A note's pitch, if it has one, is one of them; so is a filter
        setting, or nothing at all.  What this owns is **when**.

        An empty list means the note was refused, which only the `none`
        policy does.
        """
        if at < 0:
            raise AllocError(f"a note at sample {at}, before the start")
        payload = tuple(payload)
        want = self.fields - PAYLOAD
        if len(payload) != want:
            raise AllocError(
                f"this bank's voices take {want} payload value(s) and this "
                f"note carries {len(payload)}")
        voice = self._pick(at)
        if voice is None:
            return []

        voice.key, voice.started, voice.released = key, at, None
        chans = self.channels[voice.index]
        # 1-based: zero is "no note", which is what an untouched channel
        # holds — see the module docstring.
        return ([(chans[GATE_AT], at + 1), (chans[OFF_AT], 0)]
                + [(chans[PAYLOAD + j], v) for j, v in enumerate(payload)])

    def note_off(self, key, at: int) -> list:
        """Release the voice playing `key`.  Empty if none is.

        The *oldest* voice on that key, so repeated notes at one pitch
        release in the order they were struck.  A note-off for a key
        nothing is playing is ordinary — a stuck key, a `Score` whose note
        was stolen — and is silently nothing rather than an error.
        """
        held = [v for v in self.voices
                if v.key == key and v.released is None]
        if not held:
            return []
        voice = min(held, key=lambda v: (v.started, v.index))
        voice.released, voice.key = at, None
        return [(self.channels[voice.index][OFF_AT], at + 1)]

    def all_off(self, at: int) -> list:
        """Release everything — a panic, or the end of a piece."""
        changes = []
        for voice in self.voices:
            if voice.released is None and voice.started >= 0:
                voice.released, voice.key = at, None
                changes.append((self.channels[voice.index][OFF_AT], at + 1))
        return changes

    # -- reporting ----------------------------------------------------------

    def sounding(self) -> list:
        """The keys currently held, for a status line."""
        return sorted(v.key for v in self.voices if v.key is not None)


def into_schedule(schedule, changes: list, at: int, block: int):
    """Write `changes` into a `Schedule`, delivered before instant `at`.

    The delivery boundary is what keeps an onset sample-accurate: the value
    *names* the instant the note starts, and it has to be held by the voice
    before that instant arrives.  `Schedule.deliver` does the arithmetic;
    this is the loop around it.
    """
    for chan, value in changes:
        schedule.deliver(at, chan, value, block=block)
    return schedule
