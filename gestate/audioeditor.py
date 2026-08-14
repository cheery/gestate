"""The environment — `spec/liveaudio.md` stage 6, model half.

A playing instrument you can edit: the synth's source, a worker that
rebuilds it without stopping the sound, a transport, the parameters, and
what a key means.

    python -m gestate.workbench examples/audio/twoknobs.ges

**No toolkit in here, and that is the whole shape of it.**  `Workbench`
owns the instrument, the rebuild, the transport and the parameters;
`Keyboard` owns what a key means; `Transport` sits between the driver
and the engine.  None of them can reach a window, so a view is a second
view against the same object rather than a fork of it — which is what
let `shell/editor` replace the one that used to live here without
touching any of this.

**There was a `tkinter` view below this line**, and it is gone: 640
lines of text widget, gutter, knob column and piano, retired the day
`shell/editor` did all four.  `spec/workbench.md` records why the
replacement was written at all.  What it leaves behind is the argument
that outlasted it — *"two halves, and only one of them is a GUI"* —
which is why the retirement cost nothing above.

**The keyboard has no path of its own.**  A key becomes a message and
goes to `audiomidi.Notes.feed`, which is where a real MIDI keyboard's
notes go and where a `Score`'s allocator writes; the engine cannot tell
them apart.

**Knobs are placed, not listed.**  `gestate/audiospans.py` says which
file and line each control source was written on, so a parameter appears
next to its own declaration rather than in a panel that has to be read
against the code.  That is the whole reason the placement exists, and it
is why several control channels had to come first: one channel is one
knob, however many parameters a synth wants.
"""

from __future__ import annotations

import threading
from dataclasses import dataclass
from pathlib import Path

from .audiolive import (DEFAULT_BLOCK, DEFAULT_LATENCY_MS, DEFAULT_RATE,
                        Live, play)

#: What a slider hands the running graph when the channel carries an `Int`.
#: 0..100 reads as a percentage and is what the examples expect.
KNOB_RANGE = (0, 100)

#: And when it carries a `Float`.  Every `Float` a synth takes a knob for is
#: already a fraction — a filter coefficient, a mix, a modulation depth — so
#: 0..100 would ask the author to divide by a hundred in the one place the
#: language cannot check that they remembered to.
KNOB_RANGE_FLOAT = (0.0, 1.0)

#: How finely a `Float` slider moves.  A hundred steps across the range, so
#: it has the same feel under the hand as the integer one.
KNOB_STEP_FLOAT = 0.01


def _unwritten(error) -> bool:
    """Did this fail because a definition has not been written yet?

    **A hole is not a broken program; it is an absent declaration.**  Every
    half of a file here is optional — a synth need not draw, a canvas need
    not sound, and a program with no `score` simply has no piece — so the
    honest reading of `substrate = _` is a file with no canvas *yet*, and
    the honest thing to do about it is what this host already does for a
    file that declares no canvas at all: nothing, quietly, while everything
    else goes on running.

    `gmachine.Hole` says so by name when the code around it is reached, and
    this is the one place that name is recognised — three loaders ask, and
    a fourth would be a fourth opinion about what a `_` means.
    """
    return "a hole (`_`)" in str(error)


class HostTransport:
    """`Transport`'s face, with `gestate/host.c` behind it.

    Same six things — play, stop, seek, loop, position, meter — and none of
    them on the audio thread any more.  `Transport` did them between blocks
    from Python, which is the only place they are cheap *in Python*; the C
    host does them between blocks too, and cannot be stopped by a garbage
    collection while it is at it.

    **The editor cannot tell the two apart**, which is the point of the
    class: `Workbench` and the views ask the same questions of either.

    Two things genuinely differ, and both are written down rather than
    hidden:

    * **A seek is a request.**  `Transport.seek` wrote the new instant into
      the engine's state on the spot, which is safe when the caller *is*
      the thread that renders.  Here the render loop is inside C and may be
      halfway through a block, so the instant is left where C will pick it
      up — one block later, which is 5 ms.
    * **The note clock is sampled, not pushed.**  `control` used to stamp
      `notes.now` once per block, and there is no per-block Python left to
      do it in.  A housekeeping thread reads the position instead, at a
      rate chosen to match what a block gave: see `_HOUSEKEEPING`.
    """

    def __init__(self, host, live, rate: int, block: int):
        self.host = host
        self.live = live
        self.rate = rate
        self.block = block
        self.on_seek = None
        self._loop: tuple | None = None

    # -- what the view asks --------------------------------------------------

    @property
    def channels(self) -> int:
        return self.live.channels

    @property
    def playing(self) -> bool:
        return self.host.playing

    @playing.setter
    def playing(self, on: bool) -> None:
        self.host.playing = bool(on)

    @property
    def position(self) -> int:
        return self.host.position

    @position.setter
    def position(self, at: int) -> None:
        self.host.seek(at)

    @property
    def loop(self) -> tuple | None:
        return self._loop

    @loop.setter
    def loop(self, span: tuple | None) -> None:
        self._loop = span
        self.host.loop(*(span or (None, None)))

    @property
    def watch_peak(self) -> bool:
        return self._watching

    @watch_peak.setter
    def watch_peak(self, on: bool) -> None:
        self._watching = bool(on)
        self.host.watch_peak(bool(on))

    _watching = False

    def take_peak(self) -> float:
        """The loudest sample since the last look — C clears it on read,
        for the reason `Transport.take_peak` gives: a meter shows what has
        happened since it last looked."""
        return self.host.peak()

    # -- and what a *driver* asks, when one is filling ----------------------

    def fill(self, buffer, frames: int, control=None, t: int = 0) -> None:
        """One block, for a driver that owns the clock.

        Not used on the device path — there C runs the loop and nothing
        here is called at all — and present because it makes this a true
        stand-in for `Transport`, which is what lets the views be unable to
        tell them apart.

        It is also the shape a **sounddevice** path would take: PortAudio
        calls a Python callback, so the swap, the fade and the transport
        would still be C's and only the one call would be Python's.  That
        is strictly better than the Python driver and is not wired up,
        because nothing has needed it yet.
        """
        self.host.fill(buffer, frames)

    def take_rms(self) -> float:
        return self.host.rms()

    def watch_bands(self, on: bool) -> None:
        self.host.watch_bands(on)

    def band(self, k: int) -> float:
        return self.host.band(k)

    def seek(self, sample: int) -> None:
        """Jump.  The instrument keeps its shape; its notes do not.

        Every held note is released, because a jump leaves them hanging:
        the schedule already ran their note-offs at instants the transport
        has just left behind, and nothing would end them.
        """
        sample = max(0, int(sample))
        self.host.seek(sample)
        if self.on_seek is not None:
            self.on_seek(sample)


class Transport:
    """Play, stop, seek and loop — wrapped around the block filler.

    **It sits between the driver and the engine**, because that is the only
    place all four are cheap.  A block is filled by one call; stopping is
    filling it with silence and *not advancing*, seeking is writing a new
    instant into the state, and a loop is a comparison made between blocks —
    the same gap `Live.install` already uses, on the same thread, with no
    deadline to miss.

    Stopping does not tear the engine down.  The state is the instrument:
    an oscillator's phase, a filter's memory, every knob you have moved.
    Rebuilding it to press play again would throw away exactly what live
    coding is for.
    """

    def __init__(self, live, rate: int, block: int):
        self.live = live
        self.rate = rate
        self.block = block
        self.playing = True
        #: `(start, end)` in samples, or `None`.
        self.loop: tuple | None = None
        #: Where the engine has reached.  Tracked rather than read back out
        #: of the state each block: it advances by exactly `frames`, and
        #: unpacking the whole state to learn that would be work in the one
        #: place there is none to spare.
        self.position = 0
        #: Called with the sample seeked to — the view's cue to redraw.
        self.on_seek = None
        #: Track the loudest sample, for a canvas that shows one.  Off
        #: unless a substrate asks: this is the one place in the program
        #: with no time to spare, and a reading nobody looks at is a cost
        #: nobody agreed to.
        self.watch_peak = False
        self._peak = 0.0

    @property
    def channels(self) -> int:
        """The instrument's, passed straight through.

        `audiolive.channels_of` asks whatever it is filling, and a
        transport is what it is filling here — so a `sound : Sig Stereo`
        under a transport reaches the sound card as two channels rather
        than as a mono buffer read at twice the rate.
        """
        return self.live.channels

    # -- the audio thread calls this ---------------------------------------

    def fill(self, buffer, frames: int, control=None, t: int = 0) -> None:
        import ctypes

        if self.loop is not None and self.position >= self.loop[1]:
            self.seek(self.loop[0])

        if not self.playing:
            # Silence, and the clock does not move: a stopped transport is
            # stopped, not playing nothing.  Through `address_of` for the
            # same reason the engine is: PortAudio's buffer is cffi's, and
            # `memset` will not take it either.
            from .audiolive import address_of

            ctypes.memset(address_of(buffer), 0,
                          frames * self.channels
                          * ctypes.sizeof(ctypes.c_float))
            return

        self.live.fill(buffer, frames, control, self.position)
        self.position += frames

        if self.watch_peak:
            # **Sampled, not scanned.**  Sixteen points of a block is
            # enough to see a meter move and is a rounding error beside
            # the block itself; reading all 256 in Python, 187 times a
            # second, is the sort of thing `PLAYING_SWITCH_INTERVAL`
            # exists to protect.
            #
            # **Read through a typed view, whatever kind of buffer this
            # is.**  The pipe driver allocates a `ctypes` array of floats
            # and indexing it gives a float; **PortAudio hands the
            # callback raw bytes**, and indexing *that* gives a `bytes` of
            # length one — so `abs` raised `TypeError` inside a callback
            # that may not raise, which aborted the stream.  A file that
            # declared `peak` therefore played nothing at all on the
            # low-latency path, `examples/audio/substrate.ges` included.
            # `audiolive.address_of` already exists for this exact
            # difference, and this is the second reader of it.
            from .audiolive import address_of

            span = frames * self.channels
            step = max(1, span // 16)
            samples = (ctypes.c_float * span).from_address(
                address_of(buffer).value)
            loudest = max(abs(samples[i]) for i in range(0, span, step))
            self._peak = max(self._peak, loudest)

    def take_rms(self) -> float:
        """The Python driver samples a peak and not a level: an RMS is a
        second accumulator in the one place there is no time to spare, and
        a machine on this path is already rendering the slow way."""
        return 0.0

    def watch_bands(self, on: bool) -> None:
        """**The Python driver has no filter bank**, and says so by doing
        nothing rather than by growing one.  Analysing eight bands per
        sample in the interpreter is exactly the work this driver exists
        to avoid; a machine on this path is already rendering the sound
        the slow way and does not need a picture of it too."""

    def band(self, _k: int) -> float:
        return 0.0

    def take_peak(self) -> float:
        """The loudest sample since the last time this was asked.

        Taken rather than read: a meter shows what has happened since it
        last looked, and one that decayed on its own would be showing its
        own decay rather than the instrument.
        """
        peak, self._peak = self._peak, 0.0
        return peak

    # -- and the view calls these ------------------------------------------

    def seek(self, sample: int) -> None:
        """Jump.  The instrument keeps its shape; its notes do not.

        Every held note is released, because a jump leaves them hanging:
        the schedule already ran their note-offs at instants the transport
        has just left behind, and nothing would end them.
        """
        sample = max(0, int(sample))
        # The rings come back out and go straight back in: a seek moves the
        # *clock*, and a delay line's buffer is as much the instrument's
        # shape as an oscillator's phase is.
        values, _t, lines = self.live.engine.snapshot()
        self.live.engine.restore(values, sample, lines)
        self.position = sample
        if self.on_seek is not None:
            self.on_seek(sample)


class Keyboard:
    """A keyboard with no hardware behind it.

    **It plays through exactly what a real one plays through.**  A key press
    becomes a message and goes to `audiomidi.Notes.feed`, which routes it to
    a bank, runs the program's `FromMIDI` instance to build a payload, and
    asks the `Allocator` for a voice.  Nothing here knows what a voice is,
    and `mido` is not involved at any point — `feed` reads four attributes
    off whatever it is handed.

    That is the same claim `duet.ges` is built on, tested from the other
    side: a note is the same thing whether a schedule or a hand decided it,
    and only *when it was decided* differs.  If this needed its own path
    into the engine, that claim would have been false.

    No toolkit in here, for the reason `Workbench` has none: the useful
    half — what a key means, which are held, whether a bank will take one —
    is testable without opening a window, and `test_audiokeyboard.py` never
    opens one.
    """

    #: The tracker layout, and it is worth saying why rather than which.
    #: The lower row is one octave with the black keys on the row above, so
    #: the shape under your fingers is the shape on the screen; `,` is the
    #: octave above's C, so a scale can be finished without reaching for
    #: the octave control.  Every tracker since Soundtracker has used it,
    #: which makes it the layout a person is most likely to already know.
    LOWER = "zsxdcvgbhnjm,"
    #: The row above plays an octave higher, so two hands reach two octaves.
    UPPER = "q2w3er5t6y7ui"

    #: Semitone offsets from the row's C, in the order the rows above spell
    #: them: white, black, white, black, white, white, black, …
    _STEPS = (0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12)

    #: MIDI key 60 is middle C, and is octave 4 by the convention every
    #: keyboard's front panel uses.
    MIDDLE_C = 60

    def __init__(self, bench, channel: int = 0, velocity: int = 96):
        self.bench = bench
        #: Which MIDI channel the notes claim to be on.  It matters: the
        #: default routing is `by_midi_channel` when a program has more
        #: than one bank, so this is what chooses between them.
        self.channel = channel
        self.velocity = velocity
        #: Octave 4 puts `z` on middle C.
        self.octave = 4
        #: Keys currently down, by MIDI number.
        self.held: set = set()
        #: **Physical key → the note it started.**  A release has to end
        #: the note the *press* began, and recomputing it from the
        #: character is wrong in every case where the two differ: move the
        #: octave while holding a key and the recomputed note is a
        #: different one, so the original is never released and sticks
        #: forever.  X11 also delivers `KeyRelease` with an empty `char`
        #: often enough to matter, and an empty char maps to no note at
        #: all.  A `keysym` is stable between the two events, so that is
        #: what is remembered.
        self._by_key: dict = {}

    # -- what a key means ---------------------------------------------------

    def key_for(self, char: str) -> int | None:
        """The MIDI note a typed character plays, or `None` for any other.

        The empty string is `None` and the guard is load-bearing: `str.find`
        answers 0 for it, so an event with no character — which X11 sends
        for every modifier and for many key releases — would have played
        middle C.
        """
        char = (char or "").lower()
        if len(char) != 1:
            return None
        i = self.LOWER.find(char)
        if i >= 0:
            return self._note(self._STEPS[i])
        i = self.UPPER.find(char)
        if i >= 0:
            return self._note(self._STEPS[i] + 12)
        return None

    def _note(self, offset: int) -> int:
        return self.MIDDLE_C + (self.octave - 4) * 12 + offset

    def transpose(self, octaves: int) -> int:
        """Move the keyboard, releasing anything held.

        Held notes are released rather than carried, because the key that
        would release them has just changed pitch: a note carried across a
        transpose has no key left to end it.
        """
        self.all_off()
        self.octave = max(0, min(9, self.octave + octaves))
        return self.octave

    # -- playing ------------------------------------------------------------

    def press(self, note: int) -> bool:
        """Start `note`.  `False` if it was already down or nothing took it."""
        if note in self.held:
            return False                       # auto-repeat, not a new press
        self.held.add(note)
        if not self._feed("note_on", note, self.velocity):
            self.held.discard(note)
            return False
        return True

    def release(self, note: int) -> bool:
        if note not in self.held:
            return False
        self.held.discard(note)
        return self._feed("note_off", note, 0)

    # -- by physical key ----------------------------------------------------
    #
    # What the view calls.  A typed key is identified by its `keysym`, which
    # is the same string on the press and the release; the note it plays is
    # decided *once*, at the press, and remembered.

    def press_key(self, char: str, keysym: str = "") -> int | None:
        """Play whatever this physical key plays.

        Returns the note on a **fresh press of a note key**, and `None` for
        a key that plays nothing or one already down — so a caller can tell
        a first press from auto-repeat, which is what makes X11's repeated
        `KeyPress` harmless here.

        The note comes back **whether or not a bank took it**, and the key
        is remembered either way.  Both follow from `_by_key` meaning "this
        physical key is down", which is a fact about the hand rather than
        about the synth: step mode writes a note nothing played, and a
        release must still be matched even when the press made no sound.
        Ask `sounding()` for whether it was heard.
        """
        ident = keysym or char
        if not ident or ident in self._by_key:
            return None
        note = self.key_for(char)
        if note is None:
            return None
        self._by_key[ident] = note
        self.press(note)
        return note

    def release_key(self, keysym: str, char: str = "") -> int | None:
        """End the note this physical key started, whatever it was."""
        note = self._by_key.pop(keysym or char, None)
        if note is None:
            return None
        self.release(note)
        return note

    def is_down(self, keysym: str) -> bool:
        return keysym in self._by_key

    def all_off(self) -> None:
        """Every held key up — what a window losing focus has to do.

        Without it a note held while you click away is held forever: the
        `KeyRelease` goes to whatever has focus now, and the voice is never
        handed back to the allocator.
        """
        for note in sorted(self.held):
            self._feed("note_off", note, 0)
        self.held.clear()
        self._by_key.clear()

    def sounding(self) -> set:
        """The notes this keyboard believes are down."""
        return set(self.held)

    def _feed(self, kind: str, note: int, velocity: int) -> bool:
        notes = self.bench.notes
        if notes is None:
            return False
        return notes.feed(_Press(kind, self.channel, note, velocity))


@dataclass(frozen=True)
class _Press:
    """What `Notes.feed` reads, and nothing more.

    A `mido.Message` in the four attributes that matter.  Deliberately not
    a `mido` object: the virtual keyboard has to work on a machine with no
    MIDI stack installed at all, which is most machines.
    """
    type: str
    channel: int
    note: int
    velocity: int


class Workbench:
    """A synth that is playing and can be edited.  No toolkit in here.

    The audio runs on its own thread and rebuilds happen on another, so the
    view's job is only to hand over text and read back messages.  Nothing
    here blocks: `apply` returns immediately and the result arrives as a
    status line, because a 400 ms rebuild in a GUI callback is a frozen
    window.

    **Parameters are keyed by name, not by node id.**  An edit renumbers
    nodes — insert a definition and everything after it shifts — so a knob
    remembered by id would jump to a different parameter the moment you
    added a line above it.  The name is what the person turning it thinks
    they are turning.
    """

    def __init__(self, path, rate: int = DEFAULT_RATE,
                 block: int = DEFAULT_BLOCK, command: list | None = None,
                 midi: bool = False, midi_port: str | None = None,
                 latency_ms: int = DEFAULT_LATENCY_MS,
                 seed: int | None = None):
        self.path = Path(path)
        #: **A file that is not a program opens inert** — `.txt` and
        #: `.md`, by suffix, which is the one fact known before the file
        #: is read.  Nothing compiles, nothing asks for the sound card,
        #: and saving is all applying means; the window wears `[inert]`
        #: so the quiet reads as a mode rather than as breakage
        #: (`roadmap.md` §"Small improvements queued from use").
        self.inert = self.path.suffix.lower() in INERT
        #: **A file that is not there yet, held in memory until it is
        #: saved.**  Naming a file that does not exist is how an editor is
        #: asked to start a new one, and every other editor waits for the
        #: first `Ctrl-S` before anything appears on disk — so this does
        #: too.  Empty when the file exists, and then `source()` reads the
        #: file as it always did.  An inert file starts empty either way:
        #: notes must not be born wearing a synth.
        self.pending = ("" if Path(path).exists() or self.inert
                        else STARTER)
        #: **The last compiler complaint, whole.**  A status bar shows one
        #: line of it because a status bar *is* one line; this is where the
        #: other nine live, so that "expected X, got Y, at this position"
        #: is something the editor can still be asked for rather than
        #: something that existed until it was formatted.  Cleared when an
        #: edit lands, because an error that no longer applies should stop
        #: being offered.
        self.trouble = ""
        #: The C audio host when one could be opened, and `None` when the
        #: Python driver is doing the work — see `_open_host`.
        self.host = None
        self.rate = rate
        self.block = block
        self.command = command
        #: What the *player* may hold.  The delay you feel when playing a
        #: key is this, not the engine — see `audiolive.DEFAULT_LATENCY_MS`.
        self.latency_ms = latency_ms
        #: Parameter name → its value.  Survives a rebuild; see the class
        #: docstring for why it is not keyed by node.
        self.values: dict = {}
        #: Parameter name → the type its control channel carries, `"Int"`
        #: or `"Float"`.  What `knob_range` reads; recomputed with the
        #: sites, because an edit can change a channel's type.
        self.knob_types: dict = {}
        #: Where each parameter was declared — `audiospans.Site`s, in
        #: reading order.  Recomputed on every successful rebuild.
        self.sites: list = []
        #: `(line, col, type)` per `_`, from the last program that
        #: reached inference.  Drawn in the margin beside its own line.
        self.holes: list = []
        #: `(name, line, literal, is_float)` per `mkKnob` the sound never
        #: reaches — drawn, and marked as not connected.
        self.loose: list = []
        #: `voices` banks, and the line each was declared on — what the
        #: view puts a row beside.  Recomputed with the knobs, and for the
        #: same reason: an edit moves them.
        self.banks: list = []
        #: The piece this program plays, as a `Schedule`, or `None`.
        self.schedule = None
        #: The piece again, when it *unfolds* (`spec/dynamicscore.md`):
        #: a `LazyPerformer` deciding notes as the transport reaches
        #: them.  One of `schedule`/`performer` is set, never both.
        self.performer = None
        #: Remembered performer states, by the sample they stand at.
        self._seeks: dict = {}
        self._performer_lock = threading.Lock()
        #: Banks the score assigns to, by spelling — the dynamic path
        #: cannot enumerate its channels up front, so the text answers.
        self._score_banks: set = set()
        #: The session's take: `--seed` when given, else drawn once and
        #: said once — stable across rebuilds either way, so Ctrl-S
        #: changes the music you edited, not the music chance dealt you.
        self.seed = seed
        self.notes = None
        #: The program's canvas, when it has one — `spec/substrate.md`.
        #: Rebuilt with the sound, because a substrate is the same file.
        self.substrate = None
        #: The on-screen keyboard.  Built here rather than by the view, so
        #: what it is holding survives a rebuild and so a test can play it
        #: without a window — see `Keyboard`.
        self.keyboard = Keyboard(self)
        self.transport = None
        #: Banks whose MIDI switch has been seeded once, so a rebuild does
        #: not undo what you set.
        self._switched: set = set()
        #: Channels belonging to a bank the keyboard has been given.  The
        #: score does not drive these; see `control`.
        self._midi_channels: set = set()
        #: Runs the program's `FromMIDI` instances, or `None` when it
        #: declares none.  An interpreter kept beside the native engine —
        #: the engine is machine code and knows nothing about instances.
        self.from_midi = None
        #: The piece's tempo, so the transport can talk in beats.  A synth
        #: with no score keeps the default, which makes a bar a round
        #: number of samples rather than a special case.
        self.bpm = 120
        self.messages: list = []
        #: Per confession kind, the count last reported —
        #: see `_report_confessions`' doubling rule.
        self._confessed_at: dict = {}
        self.live: Live | None = None
        self.midi = None
        self.listener = None
        self._want_midi = midi
        self._midi_port = midi_port
        self._audio: threading.Thread | None = None
        #: The housekeeping thread, so `stop` can wait for it
        #: before freeing what it reads.
        self._keeper: threading.Thread | None = None
        #: The text of the edit being installed, for a restart that
        #: cannot read it off the disk — see `apply`.
        self._applying: str | None = None
        self._stop = threading.Event()
        self._directory = None
        self._seen = 0

    # -- lifecycle ----------------------------------------------------------

    def start(self, seconds: float | None = None,
              text: str | None = None) -> None:
        """Compile the file and start playing it.

        `text` overrides what is on disk, which is what a restart for an
        *audition* needs: an audition deliberately does not save, so
        reading the file would bring back the program you were trying to
        hear past.

        **A start that fails records its complaint on the way out**,
        through the same `_first_line` a failed `apply` uses — so the
        positions are the file's own, not the assembled program's, and
        the content box under the line has a fact to draw.  `apply`
        always recorded its failures and `start` never did; a file that
        is broken when it is *opened* is the first broken file anyone
        meets, and its complaint went to the status line raw, naming
        line 2649 of a 130-line file.
        """
        if self.inert:
            # A text file is opened, not started: nothing compiles,
            # nothing asks for the sound card, and the quiet is a mode
            # — the description says `inert` and the window wears it.
            self.say(f"editing {self.path.name} — inert")
            return
        try:
            self._start(seconds, text)
        except Exception as error:
            self._first_line(error)
            raise

    def _start(self, seconds: float | None = None,
               text: str | None = None) -> None:
        import tempfile

        self._directory = tempfile.mkdtemp()
        text = self.source() if text is None else text
        # The canvas, the score and the `FromMIDI` interpreter need only
        # the text, so they compile on a thread while `Live.start` waits
        # on `clang` — the one stretch of a start that holds no GIL, and
        # measured at several seconds on `quartet.ges`.  Joined before
        # anything below reads what they set.
        side = threading.Thread(target=lambda: (self._load_substrate(text),
                                                self._load_score(text),
                                                self._load_from_midi(text)))
        side.start()
        self.live = Live.start(text, self.rate, self._directory)
        self._place(text)
        side.join()
        # Always, and before the port: the on-screen keyboard needs the
        # allocators whether or not a MIDI device was asked for.
        self._start_notes(text)
        if self._want_midi:
            self._start_midi()
        # It compiled and it is playing; whatever it said last time is
        # over.  `start` is the other way a program becomes good, and it
        # does not go through `apply`.
        self.trouble = ""
        self.say(f"playing {self.path.name} at {self.rate} Hz"
                 + (f" — {len(self.sites)} knob(s)" if self.sites
                    else " — no parameters"))

        # **The C host when the machine has one, and Python otherwise.**
        # `gestate/host.c` owns the swap, the fade, the transport and the
        # control block, and opens the sound card itself — so a rebuild
        # cannot stall a block however long the front end takes.  Where
        # there is no device backend to build (no `alsa/asoundlib.h`) or no
        # `clang`, the Python driver is still there and still works; it is
        # the same sound with a garbage collector in front of it.
        self.host = self._open_host()

        # Wraps `Live`, not `Engine`: an edit swaps the engine underneath
        # and the transport must not be holding the old one.
        self.transport = (HostTransport(self.host, self.live, self.rate,
                                        self.block)
                          if self.host is not None
                          else Transport(self.live, self.rate, self.block))
        self.transport.on_seek = self._after_seek
        if self.substrate is not None:
            self.transport.watch_peak = "peak" in self.substrate.by_name
            self.transport.watch_bands(
                any(n in self.substrate.by_name for n in self.BANDS))

        def run():
            try:
                if self.host is not None:
                    self._run_host(seconds)
                else:
                    play(None, seconds, self.rate, self.block,
                         command=self.command, engine=self.transport,
                         progress=self._progress, control=self.control,
                         latency_ms=self.latency_ms,
                         should_stop=self._stop.is_set)
            except Exception as exc:                    # noqa: BLE001
                self.say(f"audio stopped: {exc}")

        self._audio = threading.Thread(target=run, daemon=True)
        self._audio.start()

    #: How often the housekeeping thread looks, in seconds.  **Matched to
    #: what a block gave**, not chosen: `control` used to stamp
    #: `notes.now` once per block — 5.3 ms at 48 kHz — and there is no
    #: per-block Python left to stamp it in.  Five milliseconds keeps a
    #: note's `gateAt` as accurate as it was, and 200 wake-ups a second of
    #: three attribute reads is nowhere near anything with a deadline.
    _HOUSEKEEPING = 0.005

    def _open_host(self):
        """A `Host` with the sound card open, or `None` to use Python.

        Returns `None` rather than raising for every reason it can fail —
        no `clang`, no ALSA headers, no card, a card that will not take
        float32 — because each of those is a machine that should still get
        an editor.  A `command` was asked for by name, so that is honoured
        as it always was and this stays out of the way.
        """
        if self.command is not None:
            return None
        try:
            from .audiohost import Host

            host = Host(channels=self.live.channels, rate=self.rate,
                        controls=len(self.live.engine.control_sources),
                        directory=self._directory)
            if not host.has_device:
                host.close()
                return None
            host.open(latency_ms=self.latency_ms)
            # **What the player was started with**, so a later edit that
            # wants more slots is refused with a sentence rather than
            # installed and then found unfeedable.
            self.live.controls = len(host.control)
        except Exception as exc:                        # noqa: BLE001
            self.say(f"no C audio host ({exc}); using the Python driver")
            return None
        host.install(self.live.engine)
        return host

    def _run_host(self, seconds: float | None) -> None:
        """The C render loop, and a housekeeping thread beside it.

        Nothing in the loop is Python.  What is left up here is what was
        never per-block work in the first place: pushing knob values in
        when they change, sampling the position for the note clock, and
        draining the message queue the view reads.
        """
        watching = threading.Event()

        def housekeeping():
            was = -1
            while not watching.wait(self._HOUSEKEEPING):
                if self._stop.is_set():
                    self.host.stop()
                    return
                # **One reading of the position, used for both.**  The
                # schedule is asked what it says *at this instant*, and the
                # note clock is stamped with the same one — two readings a
                # few hundred microseconds apart would put a note's start
                # and its `gateAt` on different instants.
                at = self.host.position
                # **And a loop wrap is a seek that nobody announced.**
                # The C engine closes its own loop between blocks — it
                # moves `position` back and tells this side nothing — so
                # `on_seek` never fires and `_after_seek` never runs.
                # A `LazyPerformer` only ever goes forward, so it went on
                # answering with the values from the end of the loop for
                # the whole of the next pass: notes late, or never
                # released at all.  The clock going backwards is the
                # announcement, and this is the thread that watches it.
                if self._wrapped(at, was):
                    self._after_seek(at)
                was = at
                self._push_controls(at)
                if self.notes is not None:
                    self.notes.now = at
                self._progress(self.host.frames)
                self._report_confessions()

        keeper = threading.Thread(target=housekeeping, daemon=True)
        # **Kept where `stop` can reach it.**  This thread reads
        # `self.host.position` and `self.host.frames` every five
        # milliseconds — straight into the workspace `Host.close` frees.
        # It was a local, joined here with a one-second timeout, and that
        # was safe for as long as `stop` only ever ran at quit: a keeper
        # that outlived its timeout touched freed memory in a process
        # that was ending anyway.  A **restart** calls `stop` in the
        # middle of a session and then goes on running, so the same race
        # is now a segfault in a program somebody is still using.
        self._keeper = keeper
        keeper.start()
        try:
            self.host.run_device(
                self.block, 0 if seconds is None else int(seconds * self.rate))
        finally:
            watching.set()
            keeper.join(timeout=1.0)

    def _push_controls(self, at: int) -> None:
        """Knob values into the block the generated code reads.

        **Pushed when they are looked at, not pulled every block.**  The
        Python driver called `control(node, t)` once per block per
        parameter; here the value is written where the render loop will
        find it, and the loop never asks anybody anything.

        **`at` is where the engine has reached, and it has to be.**  This
        was written passing `0`, which is a constant only a knob could
        survive: a knob's value does not depend on the instant, so every
        hand-driven parameter worked and nothing looked wrong.  A *score*
        does depend on it — `control` resolves a scheduled channel with
        `schedule.value_at(chan, at)` — so every scored channel was pinned
        to whatever the schedule said at instant 0 and a performance played
        its first note for ever.  It also re-armed the bug `control`'s own
        docstring records: `notes.now` is what stamps a note's `gateAt`,
        and stamping it 0 while the engine is at instant 200,000 gives a
        note whose envelope decayed before anybody read it.

        Nothing in the suite saw either, because `test/conftest.py` shuts
        the C host to keep the tests off the sound card, so every test
        drives the Python path where the time argument was already right.
        The gap is between the two drivers, which is where a second
        implementation of anything puts its bugs.
        """
        sources = self.live.engine.control_sources
        for i, node in enumerate(sources):
            self.host.set_control(i, self.control(node.id, at), node.type_)

    def _load_substrate(self, text: str) -> None:
        """Start (or restart) the canvas half of this file.

        Best-effort, exactly as `_place` is: a canvas that fails to compile
        must not stop the instrument.  A file with no `substrate` has no
        canvas, and pays nothing for it.
        """
        from .audio import has_substrate
        from .gui import Substrate

        if not has_substrate(text):
            self.substrate = None
            return
        try:
            self.substrate = Substrate(text, self.rate)
            # **Both inside the guard.**  `_load_substrate` runs from
            # `start` *before* there is a transport, so a reading switched
            # on out here raised on `None` — and the `except` below turned
            # that into "no canvas", which is how one misplaced line made
            # every substrate program in the tree draw nothing at all.
            if self.transport is not None:
                self.transport.watch_peak = "peak" in self.substrate.by_name
                self.transport.watch_bands(
                    any(n in self.substrate.by_name for n in self.BANDS))
        except Exception as exc:                        # noqa: BLE001
            self.substrate = None
            self.say(f"no canvas: {self._first_line(exc)}" if _unwritten(exc)
                     else f"the canvas did not build: {self._first_line(exc)}")

    #: What the host will write into a canvas, if the canvas declares it.
    #:
    #: Well-known names, the way `sound`, `substrate`, `score` and
    #: `bpm` are well-known: the program says it wants a reading by
    #: declaring a channel with that name, and says nothing at all if it
    #: does not.  Both are one control value, for the reason every other
    #: channel is.
    #: **`band0` … `band7` are the spectrum.**  Eight numbers, written the
    #: same way and for the same reason: a program that wants a spectrum
    #: analyser declares the channels and gets one, and a program that does
    #: not is not charged for the filter bank.  The names are positional
    #: because the bands are — `band0` is the lowest.
    BANDS = tuple(f"band{k}" for k in range(8))

    #: **Probes — readings from inside the instrument.**  Where `peak`,
    #: `rms` and the bands are measurements of the *output*, a probe says
    #: what one of the program's own voices is doing: `probe0` is how many
    #: samples voice 0 of the first `voices` bank has been sounding, and
    #: `0` when it is silent.
    #:
    #: That one number is what a picture of an envelope needs.  The
    #: envelope's *shape* the canvas already has — it is a function the
    #: file declares, and the interpreted half can call the same one the
    #: sound does — so what is missing is only **where along it** the voice
    #: has walked, which is its age.
    #:
    #: The first bank, and said rather than guessed at: a program with two
    #: banks gets probes into the one it declared first.  Naming a bank
    #: would be the general answer and nothing has needed it.
    PROBES = tuple(f"probe{k}" for k in range(8))

    WATCHED = ("peak", "rms", "voices", "position") + BANDS + PROBES

    def observe(self) -> list:
        """Write what the instrument is doing into the canvas.

        Called once a *frame* by the view — not per block, and not from the
        audio thread.  The engine's own clock is far faster than anything
        anyone can watch, so a meter that updated per block would be
        drawing sixty of them a frame and showing the last.

        **And say what was written**, as `(name, value)` pairs — the
        `reading` verb's half (`spec/workbench.md` §"The canvas walks
        over crust"): a window that walks the substrate itself needs
        the same facts by the same names, and returning them here is
        what keeps the two canvases fed from one reading.  Only the
        instrument's facts ride out — never a touch's echo, which
        would snap a fader back under the hand that had moved on.
        """
        told = []
        if self.substrate is None or self.transport is None:
            return told

        def put(name, value):
            self.substrate.write(name, value)
            told.append((name, value))

        if "peak" in self.substrate.by_name:
            put("peak", self.transport.take_peak())
        if "position" in self.substrate.by_name:
            put("position", self.transport.position)
        if "rms" in self.substrate.by_name:
            put("rms", self.transport.take_rms())
        for k, name in enumerate(self.BANDS):
            if name in self.substrate.by_name:
                put(name, self.transport.band(k))
        if "voices" in self.substrate.by_name:
            put("voices", self.voices_held())
        if any(n in self.substrate.by_name for n in self.PROBES):
            ages = self.voice_ages()
            for k, name in enumerate(self.PROBES):
                if name in self.substrate.by_name:
                    put(name, ages[k] if k < len(ages) else 0)
        return told

    #: How many points a scope's trace crosses as: the window
    #: downsampled by **max-absolute per bucket**, because a scope that
    #: averages away a click is a scope that lies (`spec/scope.md`).
    TRACE_POINTS = 128

    #: And a spectro's: log-spaced magnitude bins over the newest
    #: `SPECTRO_N` samples of the same window — the scope's second
    #: reader, by frequency instead of by time.
    SPECTRO_BINS, SPECTRO_N = 64, 1024

    def scope_traces(self) -> list:
        """`(label, points)` per scope of the playing instrument.

        Read from the running engine's own rings — the read may seam
        at a block edge, which a diagnostic tolerates.  A `scope`
        downsamples by time, a `spectro` transforms to frequency; the
        wire and the box do not care which, the flavor rides the
        furniture.  Empty when nothing plays or nothing is scoped,
        which is most programs.
        """
        engine = getattr(self.live, "engine", None) if self.live else None
        if engine is None or not hasattr(engine.graph, "scopes"):
            return []
        out = []
        for label, _length, node in engine.graph.scopes():
            window = engine.scope_window(label)
            if not window:
                continue
            if node.kind == "spectro":
                out.append((label, _spectrum(window[-self.SPECTRO_N:],
                                             self.SPECTRO_BINS)))
                continue
            size = max(1, len(window) // self.TRACE_POINTS)
            points = [max(window[b * size:(b + 1) * size], key=abs)
                      for b in range(self.TRACE_POINTS)
                      if window[b * size:(b + 1) * size]]
            out.append((label, points))
        return out

    def voices_held(self) -> int:
        """How many voices are sounding, across every bank."""
        return sum(len(self.sounding_on(b["name"]))
                   for b in getattr(self, "banks", []))

    def voice_ages(self) -> list:
        """Samples each voice of the first bank has been sounding, or `0`.

        **From the allocator, not from a probe into the graph.**  A voice
        records the sample its note began at — `audioalloc.Voice.started`,
        which is what "oldest" means when stealing — and the transport
        knows the instant, so the age is a subtraction the host can already
        do.  Reading it out of the engine's state would be the general
        mechanism and is not needed for this.

        **One-based, so that zero means *nothing*.**  A silent voice and a
        note that began this instant are both "age 0", and a picture drawn
        from that puts a marker at the start of the envelope for four
        voices that are not playing.  `audioalloc` solved the same problem
        the same way and says so at length: `gateAt` and `offAt` are
        1-based precisely so that a bank whose channels were never written
        reads as "nothing has played" rather than "everything started at
        sample 0".  A probe follows its own timing convention.
        """
        if self.notes is None or self.transport is None:
            return []
        names = list(self.notes.allocators)
        if not names:
            return []
        at = self.transport.position
        out = []
        for voice in self.notes.allocators[names[0]].voices:
            started = getattr(voice, "started", -1)
            sounding = voice.key is not None and started >= 0
            out.append(max(0, at - started) + 1 if sounding else 0)
        return out

    def touch(self, kind: str, x: int, y: int) -> None:
        """A gesture on the canvas — `"press"`, `"drag"` or `"release"`.

        **One gesture, both halves.**  The interpreted channel is written
        so the picture follows, and the value is left where `control` will
        find it by name so the sound does.  Neither half knows about the
        other; the program named the channel once.
        """
        if self.substrate is not None:
            self.substrate.touch(kind, x, y)

    def touched(self, name: str, value: float) -> None:
        """A canvas element wrote its channel, by name.

        `touch` minus the walk: the window walked the substrate,
        hit-tested, grabbed and clamped, and this is what the gesture
        *meant* (`spec/workbench.md` §"The canvas walks over crust").
        The reference substrate keeps its picture in step, and the
        value lands where `control` finds it by name so the sound
        follows — the same two halves, from the other side of the wire.
        """
        if self.substrate is not None:
            self.substrate.write(name, value)

    def tick(self) -> None:
        """A frame has passed, into the canvas.

        **Not gated on the transport, the way `observe` is.**  A reading is
        the instrument's and there is nothing to report when nothing plays;
        a frame is the *view's*, and a canvas animates whether or not a
        sound is running.
        """
        if self.substrate is not None:
            self.substrate.tick()

    def picture(self) -> list:
        """What the canvas shows now, as shapes a view can draw."""
        return [] if self.substrate is None else self.substrate.picture()

    def restart(self, why: str, seconds: float | None = None,
                text: str | None = None) -> None:
        """Fade out, build the player again, fade back in.

        **The answer to everything that is sized when playback starts.**
        The host allocates its control block and tells the card how many
        channels to expect at construction, and neither can be
        renegotiated between blocks — so adding a knob or a `voices` bank
        to a synth that had none used to be refused with a sentence
        telling you to restart it yourself.

        Which is a strange thing for a program to ask.  It knows the edit
        is good, it knows exactly what is too small, and it has a master
        fader: `stop` already fades out, joins, insists, and frees only
        once nothing is using it, and a new `Host` starts with the fader
        down and fades in.  So the seam is two fades and the program does
        the restarting.

        **`stop` and `start`, not a third teardown.**  This is the code
        that produced the one core file this project has had, and the
        discipline that fixed it — `halt` when the polite stop cannot
        complete, free only after the thread is really gone — lives in
        `stop`.  A restart that reimplemented any of that would be the
        second copy that today already cost a silent failure.

        What does not survive: notes that were down, and the position.
        A restart is a restart, and saying so is better than a fade that
        pretends nothing happened.

        **`text` is what is being restarted *for*, and it matters.**
        `start` reads the file, and an audition deliberately does not
        write one — so a restart without this brought back the program
        on disk, said *"playing demo6.ges"*, and threw away the edit you
        were listening for.  Silently, which is the worst of it.
        """
        if self.host is None:
            return                     # the Python driver sizes nothing
        self.say(f"{why} — restarting the player")
        self.stop()
        # `stop` set it, and `start` is about to be a fresh run.
        self._stop.clear()
        try:
            self.start(seconds, text=text)
        except Exception as exc:                        # noqa: BLE001
            self.say(f"could not restart: {self._first_line(exc)}")

    def stop(self, timeout: float = 2.0) -> None:
        self._stop.set()
        # **The C loop is asked to stop first**, because it is the one that
        # cannot be asked anything else: it is inside a foreign call with
        # the GIL released and the only thing it looks at is this flag.
        if self.host is not None:
            self.host.stop()
        # Keys first: a note still down when the audio thread goes away is
        # a voice the allocator never gets back, and the next run would
        # start with it already spent.
        self.keyboard.all_off()
        if self.listener is not None:
            self.listener.close()
            self.listener = None
        if self._audio is not None:
            self._audio.join(timeout)
            # **Then insist.**  `stop` asks for a fade and the device loop
            # waits for silence to arrive, which needs the card to keep
            # taking frames; when another program holds the card it never
            # does, and the polite request never completes.  `halt` leaves
            # without the fade — a click on the way out, which is the
            # right trade against the alternative below.
            if self._audio.is_alive() and self.host is not None:
                self.host.halt()
                self._audio.join(timeout)
            # **Freed only once nothing is using it.**  This used to close
            # the host straight after the first join and warn about the
            # danger afterwards — so a thread that had not stopped went on
            # running in a workspace that had just been freed, which is
            # not a risk of a crash but the crash itself.  A host left
            # open leaks until the process ends, and the process is
            # ending; that is the cheaper of the two.
            # **And the housekeeping thread, which nothing waited for.**
            # It reads the host's workspace on a five-millisecond loop,
            # so freeing while it is alive is the same use-after-free
            # the audio thread's own join exists to prevent — the
            # difference being that nobody had noticed this one because
            # `stop` used to run only as the process ended.
            keeper = getattr(self, "_keeper", None)
            if keeper is not None and keeper.is_alive():
                keeper.join(timeout)
            if self._audio.is_alive() or (keeper is not None
                                          and keeper.is_alive()):
                self.say("the audio thread did not stop; "
                         "leaving its workspace alone")
            else:
                self._keeper = None
                if self.host is not None:
                    self.host.close()
                    self.host = None
                self._audio = None
                self._clean_up()

    def _clean_up(self) -> None:
        """Remove the directory the engines were built in.

        **After the join, never before.**  Every `.so` the session compiled
        lives here, and while `dlopen` keeps a mapping alive across the
        file being unlinked, removing it under a thread that is about to
        build the next engine would not be.
        """
        import shutil

        if self._directory is not None:
            shutil.rmtree(self._directory, ignore_errors=True)
            self._directory = None

    @property
    def playing(self) -> bool:
        return self._audio is not None and self._audio.is_alive()

    # -- parameters ---------------------------------------------------------

    def _find_banks(self, text: str) -> None:
        """The `voices` declarations, and the line each is on.

        Read from the source rather than from the graph: a bank's *name*
        and the line it was written on are facts about the text, and the
        graph has neither — its nodes carry an origin path, which is
        deliberately not a position (`audiospans.py`).
        """
        from .audiovoices import banks_of

        try:
            found = banks_of(text)
        except Exception as exc:                        # noqa: BLE001
            self.say(f"could not read the banks: {self._first_line(exc)}")
            return
        from .audiovoices import channels_of

        self.banks = []
        for bank in found:
            try:
                rows = channels_of(text, bank)
            except Exception:                           # noqa: BLE001
                rows = []
            # The channel rows are cached here rather than looked up when
            # the row is drawn: the view redraws ten times a second and
            # `channels_of` parses.
            self.banks.append({"name": bank.name, "count": bank.count,
                               "line": bank.line + 1, "record": bank.record,
                               "channels": rows, "wired": True})
        # **Whether the sound reaches each bank** — the one question the
        # text cannot answer and the graph can, the same split as a
        # knob's cross.  A bank the mix dropped is "layered away": the
        # score still writes it, the keyboard still feeds it, and
        # nothing comes out — an evening spent deciding whether the
        # synth is broken, unless the margin says so.  A graph that is
        # not there to ask (a build that failed) answers wired, because
        # a mark that cries wolf teaches people to ignore it.
        chans = self._graph_channels()
        if chans is not None:
            # `None` is "no graph to ask" and keeps the benefit of the
            # doubt; an *empty set* is an answer — a program whose
            # graph reads no channels has every bank disconnected,
            # which is exactly the case that found this distinction:
            # comment the one bank out of `sound` and the remaining
            # graph has nothing but its clock.
            for row in self.banks:
                row["wired"] = any(c in chans
                                   for voice in row["channels"]
                                   for c in voice)
        # **Where the score writes each bank** — the lines saying
        # `voices.<name>`, cached for the margin: when a bank's switch
        # is on, MIDI has it and the score no longer drives it, so
        # every one of these lines is silently displaced ("layered
        # away") and the margin should say so at the line itself.
        # Comments are stripped first — `duet.ges` has one *suggesting*
        # `voices.lead`, and a suggestion does not play.
        import re

        mention = re.compile(r"voices\.(\w+)")
        mentions: dict = {}
        for n, line in enumerate(text.splitlines(), start=1):
            for m in mention.finditer(line.split("#", 1)[0]):
                mentions.setdefault(m.group(1), []).append(n)
        for row in self.banks:
            row["mentions"] = mentions.get(row["name"], [])

    def _graph_channels(self) -> set | None:
        """Every control channel the playing (or arriving) graph reads.

        The *pending* engine when an edit is being installed, because
        the margin should say what the text in the window wires, not
        what the crossfade is still fading out.  `None` when there is
        no graph to ask — which is a different fact from an *empty*
        answer, and conflating them left a fully disconnected bank
        wearing its count.
        """
        live = getattr(self, "live", None)
        if live is None:
            return None
        engine = getattr(live, "pending", None)
        if engine is None or isinstance(engine, Exception):
            engine = getattr(live, "engine", None)
        if engine is None:
            return None
        try:
            return {getattr(n, "chan", None) or getattr(n, "name", "")
                    for n in engine.graph.control_sources()}
        except Exception:                               # noqa: BLE001
            return None

    @staticmethod
    def _bank_channels(text: str) -> set:
        """Every channel a `voices` bank owns.

        **Not knobs.**  A bank's channels are written by a scheduler or a
        keyboard, and a slider fighting either would be a control that does
        nothing you can predict.  They still *place*, because the innermost
        definition their origin can reach is the bank itself — which is why
        a synth with two banks offered thirty-six sliders at one line.

        Asked of the expander, which generated them and knows what it
        called them, rather than inferred from an origin path.  Computed
        **once per rebuild**: it parses, and per-site it turned a 1.7 s
        audition into 2.8 s.
        """
        from .audiovoices import banks_of, channels_of

        try:
            return {c for b in banks_of(text) for row in channels_of(text, b)
                    for c in row}
        except Exception:                               # noqa: BLE001
            return set()

    def sounding_on(self, bank: str) -> list:
        """What that bank is playing *now*, from either source.

        Both, and that is the point of asking here rather than of asking
        the allocator.  A bank driven by a keyboard has an allocator that
        knows what it holds; a bank driven by the **score** has none at
        playback time — the schedule wrote its channels ahead of time and
        nothing tracks them.  A row that counted only the first would sit
        at `0/3` through an entire piece.
        """
        keys = []
        if self.notes is not None:
            try:
                keys += self.notes.sounding_on(bank)
            except KeyError:
                pass
        return sorted(keys + self._scheduled_on(bank))

    def _performed_value(self, chan: str, at: int):
        """The dynamic score's answer for `chan` at instant `at`.

        The advance rides whoever asked — the housekeeping push on the C
        path, `control` per block on the Python one — which keeps the
        forcing off the audio thread on both.  A performer that has not
        yet begun while the transport stands past zero (a rebuild
        mid-play) **seeks first**: silent replay to here, so an edit
        rejoins the piece instead of replaying its whole past fortissimo.
        """
        with self._performer_lock:
            if self.performer.position < 0 and at > 0:
                self.performer.seek(at)
            # A few blocks of lookahead: delivery may land early — the
            # value names its exact instant — never late.
            self.performer.advance(at + 4 * self.block)
            return self.performer.values.get(chan)

    def _scheduled_on(self, bank: str) -> list:
        """The scored notes sounding at the transport's instant.

        Read straight out of the schedule: a voice is sounding when its
        `gateAt` has arrived and its `offAt` has not.  That is the same
        arithmetic the *voice* does per sample, which is what makes the row
        agree with what you can hear.
        """
        if (self.schedule is None and self.performer is None) \
                or self.transport is None:
            return []
        if self.notes is not None and self.notes.listening.get(bank, False):
            # Handed to the keyboard, so the score is not driving it — and
            # a row that went on listing the notes it *would* have played
            # would be reporting sound nobody can hear.
            return []
        rows = next((b["channels"] for b in self.banks
                     if b["name"] == bank), [])
        now = self.transport.position

        def look(chan):
            if self.schedule is not None:
                return self.schedule.value_at(chan, now)
            with self._performer_lock:
                return self.performer.values.get(chan)

        out = []
        for row in rows:
            if len(row) < 3:
                continue
            on = look(row[0])
            off = look(row[1])
            if not on or now < on - 1:
                continue
            if off and now >= off - 1:
                continue
            value = look(row[2])
            if value is not None:
                out.append(value)
        return out

    def _place(self, text: str) -> None:
        """Work out where each control source was declared.

        Best-effort: a synth is playing either way, and a placement that
        failed should cost the knobs their *position*, not the sound.  So a
        failure here is reported and the previous placement kept.
        """
        from .audiospans import controls_and_graph as sites

        # Banks first: they are read from the text and cannot fail the way
        # placement can, and losing them to a placement error would take
        # the view's bank rows with it.
        self._find_banks(text)
        try:
            # **The graph the sites were placed in, not the one playing.**
            # A `Site.node` is an index into the graph `text` extracts to,
            # and the engine is still running the *previous* one until the
            # audio thread installs the rebuild between blocks — so asking
            # it about these nodes read a node that had moved, or, when the
            # edit removed one, ran off the end of the list (`IndexError` in
            # `Graph.node`).  `install` can also refuse an edit outright
            # (a channel-count change), which leaves the two disagreeing
            # for as long as the synth plays.
            self.sites, graph = sites(text, rate=self.rate,
                                      path=self.path.name)
        except Exception as exc:                        # noqa: BLE001
            self.say(f"could not place the knobs: {self._first_line(exc)}")
            return
        owned = self._bank_channels(text)
        if owned:
            self.sites = [s for s in self.sites
                          if graph.node(s.node).chan not in owned]
        # **A knob's range follows its channel's type.**  Recorded here
        # because this is where the sites and the graph are both in hand;
        # `value_of` is asked by the view long before either is.
        for site in self.sites:
            self.knob_types[site.name] = graph.node(site.node).type_
            self.values.setdefault(site.name, self.knob_default(site.name))
        if self.midi is not None:
            self._rebind_midi()
        self._find_loose_knobs(text)
        self._find_holes(text)

    def _find_loose_knobs(self, text: str) -> None:
        """Knobs the file declares that the sound never reaches.

        **A knob with no site is not a knob that does not exist.**
        `audiospans` reports control sources found *in the graph*, so a
        `mkKnob` nothing downstream of `sound` reads has none — and the
        margin drew nothing at all, which reads as the editor having
        missed the line rather than as the program having ignored it.
        Declaring a parameter and forgetting to use it is an ordinary
        mistake and one the window is in the best position to point at.

        Read from the text, like `goto`'s declarations, and for the same
        reason: the graph is precisely what cannot answer this.
        """
        import re

        wired = {getattr(s, "name", None) for s in (self.sites or [])}
        found = []
        for n, line in enumerate(text.splitlines(), start=1):
            m = re.match(r"([A-Za-z_]\w*)\s*=\s*mkKnob\s+(-?[\d.]+)\s*$",
                         line)
            if m and m.group(1) not in wired:
                literal = m.group(2)
                found.append((m.group(1), n, literal, "." in literal))
        self.loose = found

    def _find_holes(self, text: str) -> None:
        """Where every `_` is, and what type it wants.

        **Here and not in the description.**  `furniture` is derived every
        time it is asked for, which is right for it — a knob's value is a
        dictionary lookup — and this is a whole run of inference.  The
        poll is two milliseconds; a typecheck is not.  So a hole is a fact
        about the *compiled* program, worked out where the placement is
        and kept beside it, exactly like `sites`.

        Best-effort for the same reason placement is: a program mid-edit
        does not reach inference, and the last good answer is a better
        thing to keep showing than nothing.
        """
        from .typecheck import FitsError, holes_in_source

        try:
            self.holes = holes_in_source(text, rate=self.rate)
        except (FitsError, Exception):                  # noqa: BLE001
            pass

    def knob_range(self, name: str) -> tuple:
        """`(low, high)` for this parameter's slider.

        **A `Float` channel runs 0.0 .. 1.0 and an `Int` one 0 .. 100**,
        because those are the numbers each is written against: a filter
        coefficient, a mix, a depth — every `Float` a synth takes a knob
        for is already a fraction, and handing it 0 .. 100 asks the author
        to divide by a hundred in the one place the language cannot check
        that they did.  An `Int` knob is a note number or a percentage, so
        it keeps the range the examples expect.
        """
        return (KNOB_RANGE_FLOAT if self.is_float_knob(name) else KNOB_RANGE)

    def is_float_knob(self, name: str) -> bool:
        return self.knob_types.get(name) == "Float"

    def knob_default(self, name: str):
        """Mid-travel, so a control does something in either direction."""
        low, high = self.knob_range(name)
        return (low + high) / 2.0 if self.is_float_knob(name) else \
            (low + high) // 2

    @property
    def has_knob(self) -> bool:
        """Does the running graph have a control-rate source to drive?"""
        return bool(self.sites)

    @property
    def knob_source(self) -> str | None:
        """The origin of the first parameter, or `None`.

        Kept for the one thing that wants a single answer — the status line
        of a synth with one knob — now that there may be several.
        """
        return self.sites[0].origin if self.sites else None

    def value_of(self, name: str):
        return self.values.get(name, self.knob_default(name))

    def set_value(self, name: str, value) -> None:
        """Store what the slider says, in the channel's own type.

        The coercion is not cosmetic: `audiollvm.pack_control` writes an
        `Int` channel as an integer and a `Float` one as the *bits* of a
        double, and reads the slot back the way the graph says.  A float
        arriving in an `Int` channel, or an int in a `Float` one, is a
        silently wrong sound rather than an error.
        """
        self.values[name] = (float(value) if self.is_float_knob(name)
                             else int(float(value)))

    def control(self, node: int, _t: int):
        """What the engine reads once per block, per control source.

        MIDI wins when a controller is bound and has been moved, because a
        physical knob is the one the person's hand is on.  Otherwise the
        slider's value.
        """
        # **Unconditionally, and first.**  `now` is what stamps a note's
        # `gateAt`, and it used to be set only when a channel was already
        # in `values` — that is, only *after* a note had been played.  So
        # the first note of a session was stamped at instant 0 while the
        # engine was at instant 200,000, and its envelope had decayed to
        # nothing before it was ever read.  The note played, silently.
        if self.notes is not None:
            self.notes.now = _t

        chan = self.live.engine.graph.node(node).chan if self.live else ""
        # **A bank handed to the keyboard is not driven by the score.**
        # Both write the same channels, and the allocator hands out voices
        # the schedule writes past — so with the score winning, a played
        # note on a scored bank was taken, shown in its row, and never
        # heard.  Ticking the switch takes the bank; unticking gives it
        # back.
        if chan in self._midi_channels:
            if self.notes is not None:
                return self.notes.values.get(
                    chan, self.live.engine.graph.node(node).init)
        elif self.schedule is not None and chan:
            value = self.schedule.value_at(chan, _t)
            if value is not None:
                return value
        elif self.performer is not None and chan:
            value = self._performed_value(chan, _t)
            if value is not None:
                return value
        if self.notes is not None and chan in self.notes.values:
            return self.notes.values[chan]

        # The canvas, if this channel is one a substrate element feeds.
        # By *name*, which is the whole bridge: the graph calls it `cutoff`
        # because the program did, and so does the element that writes it.
        if self.substrate is not None and chan in self.substrate.values:
            return self.substrate.values[chan]

        name = next((s.name for s in self.sites if s.node == node), None)
        if name is None:
            return 0
        if self.midi is not None:
            binding = self.midi.binding_of(node)
            if binding is not None and binding.cc is not None \
                    and binding.cc in self.midi.latest:
                return binding.value_of(self.midi.latest[binding.cc])
        return self.value_of(name)

    # -- MIDI ---------------------------------------------------------------

    def _start_notes(self, text: str | None = None) -> None:
        """The note plumbing — allocators and `Notes`, with no port.

        **Split out of `_start_midi` because the on-screen keyboard plays
        through this and not through MIDI.**  It used to be built inside
        the `try` that opens a port, so a machine with no MIDI device — or
        an editor started without `--midi`, which is the ordinary case —
        had no allocators, and there was nothing for a key press to reach.

        **`text` is what is being started, and it matters here too.**  An
        audition deliberately does not write the file, so a restart for
        one that read the banks off the disk built no allocator for the
        bank you just added — the engine played the audition, `FromMIDI`
        loaded from it, and `listen` answered "would not switch" because
        there was no `Notes` behind the switch.  The same omission
        `restart` itself documents, one layer down.

        Nothing here imports `mido`: `audiomidi` defers that to the two
        functions that open a port, so `Notes` is available on a machine
        with no MIDI stack installed at all.
        """
        from .audiomidi import Notes

        allocators = self._allocators(text)
        self.notes = Notes(allocators) if allocators else None
        self._rewire_notes()                 # seeds the switches in turn

    def _start_midi(self) -> None:
        """Open a port, so knobs and keys can arrive from hardware too.

        `_start_notes` has already run, so a failure here costs the *port*
        and not the keyboard: the window still plays.
        """
        from .audiomidi import Controls, Listener, MidiError, NoteListener

        try:
            self.midi = Controls([])
            self._rebind_midi()
            # One port carries knobs and keys alike, so the listener reads
            # both when there is a bank to play and controllers only when
            # there is not.
            listener = (NoteListener(self.midi, self.notes, self._midi_port)
                        if self.notes is not None
                        else Listener(self.midi, self._midi_port))
            self.listener = listener.start()
            played = ", ".join(f"`{b}`" for b in self.notes.allocators) \
                if self.notes is not None else "no banks"
            self.say(f"MIDI: {played}; right-click a knob to learn a controller")
        except MidiError as exc:
            self.midi, self.listener = None, None
            self.say(f"no MIDI: {exc}")

    def midi_ports(self) -> list:
        """Every MIDI input on this machine, or `[]`.

        `[]` is *not* an error — a machine with no controller plugged in,
        or no `mido`, is a machine without MIDI, and `audiomidi` already
        makes that distinction so nothing here has to.
        """
        from .audiomidi import input_names

        return input_names()

    @property
    def midi_port(self) -> str | None:
        """The port that is open, or `None` — **open, not wanted.**

        Asked while a device is being chosen, so it has to be about what
        is actually listening rather than about what was asked for on the
        command line: a port that failed to open must not read as active,
        which is the same rule the piano follows when it is drawn grey.
        """
        return self._midi_port if self.listener is not None else None

    def midi_open(self, port: str | None = None) -> bool:
        """Listen to a controller — this one, or the first there is.

        Closes whatever was open first, because two listeners on one
        machine is two copies of every note, and a device chosen from a
        list is a *change* of device far more often than a first one.
        """
        self.midi_close()
        self._midi_port = port or None
        self._start_midi()
        return self.listener is not None

    def midi_close(self) -> bool:
        """Stop listening.  `False` if nothing was."""
        if self.listener is None:
            return False
        self.listener.close()
        self.listener = None
        self.midi = None
        return True

    def _refresh_notes(self, text: str) -> None:
        """The note plumbing follows the banks of what is playing.

        **What an apply calls.**  `_rewire_notes` swaps the instances and
        keeps the allocators, which is right for the ordinary edit — a
        rebuild must not steal the voices out from under held notes.  But
        an edit that changes the *bank list* leaves a switch with nothing
        behind it: the first bank added to a bankless synth found
        `notes` still `None`, `_rewire_notes` returned at its first
        line, and `listen` answered "would not switch" about a bank the
        engine was playing.  Under the C host a first bank forces a
        player restart and `_start_notes` runs anyway; under the Python
        driver nothing does, so this is the one place that notices.
        """
        try:
            from .audiovoices import banks_of

            want = {b.name for b in banks_of(text)}
        except Exception:                               # noqa: BLE001
            want = None
        have = set(self.notes.allocators) if self.notes is not None else set()
        if want is not None and want != have:
            self._start_notes(text)
        else:
            self._rewire_notes()

    def _rewire_notes(self) -> None:
        """Point `Notes` at the program's `FromMIDI`, if it has one.

        Kept out of `_start_midi` because a rebuild replaces the instances
        as surely as it replaces the graph: edit `noteOn`, press Ctrl-S,
        and the next key you press goes through the new one.
        """
        if self.notes is None:
            return
        if self.from_midi is None:
            self.notes.accepts = None
            # Still seeded: the early return skipped it, so a program with
            # no instance kept every switch on — greyed out in the view and
            # passing notes underneath, which is the exact thing the switch
            # is there to stop.
            self._seed_switches()
            return

        def accepts(bank, message):
            return self.from_midi.payload_for(
                bank, getattr(message, "channel", 0), message.note,
                message.velocity)

        self.notes.accepts = accepts
        self._seed_switches()

    def _seed_switches(self) -> None:
        """Set each bank's switch once, then leave it alone.

        A bank the score drives starts **off** — two writers on one set of
        channels is a fight — and one you have touched keeps what you set,
        across every rebuild.  A bank that cannot take MIDI at all is
        forced off whatever anyone set, because its switch is greyed and a
        greyed switch that still passes notes is worse than no switch.
        """
        if self.notes is None:
            return
        scored = self.scored_banks()
        for bank in list(self.notes.allocators):
            if bank not in self._switched:
                self.notes.listening[bank] = bank not in scored
                self._switched.add(bank)
            if not self.takes_midi(bank):
                self.notes.listening[bank] = False
        self._note_midi_channels()

    def _note_midi_channels(self) -> None:
        """Which channels the keyboard owns, recomputed when a switch moves."""
        owned = set()
        if self.notes is not None:
            for bank in self.banks:
                if self.notes.listening.get(bank["name"], False):
                    owned.update(c for row in bank["channels"] for c in row)
        self._midi_channels = owned

    def _allocators(self, text: str | None = None) -> dict:
        """One allocator per bank the keyboard may play.

        **Every bank, including the ones a score drives.**  Leaving those
        out meant their switch had nothing behind it — you could tick
        `bass` and nothing would play, because there was no allocator to
        play it.  Two writers on one set of channels is still a fight, so
        a scored bank starts switched *off*; that is a default you can
        change rather than a decision made for you.
        """
        from .audioalloc import AllocError, Allocator
        from .audiovoices import banks_of, channels_of

        text = self.source() if text is None else text
        out = {}
        for bank in banks_of(text):
            try:
                out[bank.name] = Allocator(channels_of(text, bank))
            except AllocError:
                continue
        return out

    def scored_banks(self) -> set:
        """Which banks the program's own `score` writes to.

        Taken from the **schedule's own channels**, not by looking for
        `voices.<name>` in the text.  Scanning the source finds mentions in
        *comments* too — `duet.ges` has one suggesting you try
        `voices.lead` — and that silently left the keyboard with no bank at
        all.  The schedule knows exactly which channels it writes, so it is
        the thing to ask.
        """
        if self.schedule is not None:
            return {c.split("Chan")[0] for c in self.schedule.channels()}
        if self.performer is not None:
            # No baked channels to ask, so the *parsed* assignment scan
            # answers — reachable declarations, never comments, which is
            # the mistake recorded above (`audioscore.assigned_banks`).
            return set(self._score_banks)
        return set()

    # -- the transport ------------------------------------------------------

    def play(self) -> None:
        if self.transport is not None:
            self.transport.playing = True
            self.say("playing")

    def pause(self) -> None:
        """Silence, and the clock stops.  The instrument is untouched.

        **Called `pause` because it was called `stop`**, and a second
        `def stop` in this class silently replaced the *lifecycle* one
        above — so shutting the window set `transport.playing = False` and
        never signalled the audio thread, never joined it and never closed
        the MIDI port.  The process then exited with a daemon thread still
        inside the generated code, which is the intermittent crash on
        close.  Two methods of one name is a thing Python will not tell you
        about; the fix is not to have two.
        """
        if self.transport is not None:
            self.transport.playing = False
            self.say(f"stopped at {self.position_in_beats():.1f}")

    def toggle(self) -> bool:
        if self.transport is None:
            return False
        (self.pause if self.transport.playing else self.play)()
        return self.transport.playing

    def seek_beats(self, beat: float) -> None:
        if self.transport is not None:
            self.transport.seek(self.beats_to_samples(beat))

    def set_loop(self, start_beat: float, end_beat: float) -> None:
        """Loop a section, in beats.  `end` must be after `start`."""
        if self.transport is None:
            return
        start = self.beats_to_samples(start_beat)
        end = self.beats_to_samples(end_beat)
        if end <= start:
            self.say("a loop must end after it starts")
            return
        self.transport.loop = (start, end)
        self.say(f"looping {start_beat:g}–{end_beat:g}")
        if not (start <= self.transport.position < end):
            self.transport.seek(start)

    def clear_loop(self) -> None:
        if self.transport is not None:
            self.transport.loop = None
            self.say("loop off")

    #: How many seek targets to keep the performer's state for.
    #:
    #: A loop needs one.  A handful covers moving between a few places
    #: in a piece, which is what somebody working on a middle section
    #: actually does, and puts a ceiling on the memory.
    _SEEKS_KEPT = 8

    def _remember(self, sample: int) -> None:
        """Keep the moment the performer now stands at."""
        if self.performer is None:
            return
        if len(self._seeks) >= self._SEEKS_KEPT:
            # Oldest out: a dict remembers its insertion order, and the
            # place you have not been back to in a while is the place
            # you are least likely to return to next.
            del self._seeks[next(iter(self._seeks))]
        self._seeks[sample] = self.performer.snapshot()

    @staticmethod
    def _wrapped(at: int, was: int) -> bool:
        """Whether the engine's clock has just jumped backwards.

        **The Python transport cannot need this and the C one cannot do
        without it.**  `Transport.fill` closes a loop by calling `seek`,
        which announces itself; the generated host closes one by
        assigning `position`, which announces nothing.  The gap between
        two drivers is where a second implementation puts its bugs —
        `_push_controls` carries the same note about the same pair.
        """
        return 0 <= at < was

    def _after_seek(self, _sample: int) -> None:
        """Every held note released — the jump left them with no note-off.

        The schedule ran their releases at instants the transport has just
        left, so nothing else would ever end them.
        """
        if self.notes is not None:
            self.notes.all_off()
        for bank in self.banks:
            allocator = (self.notes.allocators.get(bank["name"])
                         if self.notes is not None else None)
            if allocator is not None:
                for chan, value in allocator.all_off(0):
                    self.notes.values[chan] = value
        # A dynamic score answers the transport's question itself:
        # release what sounds, silent replay to the target
        # (`audiodynamic.LazyPerformer.seek` — stage one's semantics,
        # already pinned by its tests).
        #
        # **Remembered, because a loop asks the same question every
        # pass.**  That replay costs more the further into a piece it
        # lands — nineteen milliseconds at bar sixty-five — and a loop
        # pays it on every wrap, on this thread, holding the lock that
        # `_push_controls` also wants. The state at an instant is a pure
        # function of what came before it, which is exactly what makes
        # it safe to keep: `restore` refuses any moment that no longer
        # fits and the seek happens after all.
        if self.performer is not None:
            with self._performer_lock:
                if not self.performer.restore(self._seeks.get(_sample)):
                    self.performer.seek(_sample)
                    self._remember(_sample)

    # -- beats and samples --------------------------------------------------

    def beats_to_samples(self, beat: float) -> int:
        return int(beat * 60 * self.rate / max(1, self.bpm))

    def samples_to_beats(self, sample: int) -> float:
        return sample * self.bpm / (60.0 * self.rate)

    def position_in_beats(self) -> float:
        return self.samples_to_beats(
            self.transport.position if self.transport else 0)

    def _load_from_midi(self, text: str) -> None:
        """Compile a state that can run this program's `FromMIDI` instances.

        **Skipped entirely when the program declares none**, which is the
        common case and would otherwise pay a whole extra front end on
        every rebuild for nothing.  The textual check is the same one the
        expander uses to decide whether to emit a forwarder, so the two
        cannot disagree about whether there is anything to run.
        """
        from .audiomidi import FromMidi

        if "instance FromMIDI" not in text:
            self.from_midi = None
            return
        try:
            from .audioperform import has_score
            from .audioscore import assemble_performance
            from .audio import assemble
            from .audiovoices import banks_of
            from .pipeline import compile as _compile

            program = (assemble_performance(text, "", self.rate)
                       if has_score(text) else assemble(text, self.rate))
            # `banks_of(text)`, not `self.banks`: this runs on `start`'s
            # side thread, and `self.banks` is `_place`'s to fill — on the
            # main thread, in a race this used to win by being sequential.
            self.from_midi = FromMidi(_compile(program),
                                      [b.name for b in banks_of(text)])
        except Exception as exc:                        # noqa: BLE001
            self.from_midi = None
            if not _unwritten(exc):
                self.say(f"FromMIDI not loaded: {self._first_line(exc)}")

    def takes_midi(self, bank: str) -> bool:
        """Is this bank able to take MIDI at all?

        What greys the switch out: a bank whose payload has no `FromMIDI`
        instance cannot be handed a note, however much you want it to be.
        """
        return self.from_midi is not None and self.from_midi.offers(bank)

    def listening(self, bank: str) -> bool:
        """Is it *set* to take MIDI?  The switch itself."""
        return (self.notes is not None
                and self.notes.listening.get(bank, False))

    def listen(self, bank: str, on: bool) -> None:
        if self.notes is not None and self.takes_midi(bank):
            self._switched.add(bank)
            self.notes.listening[bank] = on
            if not on:
                # Handing the bank back ends whatever is being held on it:
                # the channels stop answering to the keyboard, so a note
                # left down could never be released and would simply be
                # forgotten while still counted.
                for chan, value in self.notes.allocators[bank].all_off(
                        self.notes.now):
                    self.notes.values[chan] = value
                self.notes.playing = {
                    k: [b for b in v if b != bank]
                    for k, v in self.notes.playing.items()}
            self._note_midi_channels()
            self.say(f"{bank}: MIDI {'on' if on else 'off'}"
                     + (" (the score no longer drives it)" if on else ""))

    # -- a note, as source --------------------------------------------------

    def note_text(self, note: int) -> str:
        """What a played note looks like written down.

        **The key number and its separator.**  It once rendered the bank's
        whole payload — `'(Key 60 96)` — which is more than a step
        sequencer should decide: a number goes wherever you put the cursor,
        into an argument list, a `chord 45 60 64 67`, or inside a `'(…)` you
        are already writing.  A pre-spelled constructor only fits the one
        place it guessed at, and is in the way everywhere else.

        The trailing space is load-bearing: two steps used to write
        `5050`, one wrong number instead of two right ones, because the
        second insert landed hard against the first (`fixme.md` F108).
        Everywhere a bare number goes, whitespace separates.
        """
        return f"{note} "

    def _load_score(self, text: str) -> None:
        """The piece this program plays, if it has one.

        Rebuilt with everything else, because an edit to the score is an
        edit: change a note, press Ctrl-S, and the bass line changes under
        whatever you are playing over it.
        """
        import re

        from .audioperform import has_score

        if not has_score(text):
            self.schedule = None
            self.performer = None
            return
        try:
            from .audioalloc import Allocator
            from .audioscore import assigned_banks, unfolding_names
            from .audiovoices import banks_of, channels_of

            self._score_banks = assigned_banks(text)
            # The session's seed, drawn the first time a piece can tell
            # the difference and **said** — the renderer records what it
            # supplied — then held, so a rebuild replays the same take.
            if self.seed is None and re.search(
                    r"\b(sown|roll|chance|sow)\b", text):
                import os

                self.seed = int.from_bytes(os.urandom(8), "big")
                self.say(f"seed {self.seed} — this session's take")
            allocators = {b.name: Allocator(channels_of(text, b))
                          for b in banks_of(text)}
            if unfolding_names(text):
                # The score has no end (or no proof of one), so nothing
                # is baked: the performer decides notes as the transport
                # reaches them, off the audio thread — `control` and the
                # housekeeping push are its clock.
                from .audiodynamic import LazyPerformer, LiveStream
                from .audioperform import holds_reader
                from .audioscore import ports_of, stream_root
                from .tempo import TempoEnvelope, constant

                # A rebuild mid-piece resumes at the beat the transport
                # stands on: `resumeAt` descends by declared widths, so
                # rejoining minute forty costs what rejoining bar two
                # does.  Fresh takes start at zero like always.
                tick = 0
                if self.transport is not None and self.transport.position > 0:
                    probe_tempo = (self.bpm if not isinstance(self.bpm, str)
                                   else 120)
                    env = (probe_tempo
                           if isinstance(probe_tempo, TempoEnvelope)
                           else constant(probe_tempo))
                    tick = int(env.beat_at(
                        self.transport.position / self.rate)) * 96
                tempo, state, root, by_tag = stream_root(
                    text, "", self.rate, self.seed or 0, tick, live=True)
                self.bpm = tempo
                self.schedule = None
                # The world a probe reads: the keyboard's own note
                # port, asked at decision instants, never earlier.
                # `self.notes` is looked up at *call* time — rebuilds
                # replace the Notes object, and a reader that captured
                # one would listen to a keyboard nobody holds anymore.
                # By channel id, which needs the compiled state:
                # `holds.<bank>` is a `Chan` now, not an index.
                ports = ports_of(text, state)

                def reader(port, key=None, _ports=ports):
                    return holds_reader(self.notes, _ports)(port, key)
                # **Crust forces the score when the piece can cross**
                # (`crust.live_native` — the one routing decision,
                # spelled once beside `audioperform.dynamic`'s use).
                # The fuel is the 20 ms patience below, respelled in
                # steps; the fallback is never wrong, only slower.
                from .crust import live_native

                stream = live_native(state, by_tag, self.seed or 0,
                                     tick, fuel=100_000)
                with self._performer_lock:
                    # A new score, so every remembered moment is stale.
                    self._seeks.clear()
                    fresh = LazyPerformer(
                        stream if stream is not None else
                        LiveStream(state, root, by_tag, patience=0.02),
                        tempo, self.rate, allocators, block=self.block,
                        origin=tick, reader=reader)
                    # **What was sounding survives the swap** (F131):
                    # the resumed stream stands past the leaf it is
                    # in, so without this a note held across the seam
                    # fell silent until its next onset — the pad died
                    # at every apply, and probing was applying.
                    if self.performer is not None:
                        fresh.inherit(self.performer)
                    self.performer = fresh
            else:
                from .audioscore import perform_voices, schedule_voices

                # **Once.**  `perform_voices` is a whole front end and a
                # run, and calling it for the tempo and again inside
                # `scored` made every audition wait for two of them — on
                # top of the two the rebuild and the knob placement
                # already cost.
                self.bpm, events = perform_voices(text, "", self.rate,
                                                  self.seed or 0)
                self.performer = None
                self.schedule = schedule_voices(
                    events, self.bpm, self.rate, allocators,
                    block=self.block)
        except Exception as exc:                        # noqa: BLE001
            self.schedule = None
            self.performer = None
            self.say(f"no piece: {self._first_line(exc)}" if _unwritten(exc)
                     else f"score not loaded: {self._first_line(exc)}")

    # ── What the command list asks for ───────────────────────────────
    #
    # `spec/commands.md`.  Three questions the workbench could always
    # have answered and was never asked, because the old editors reached
    # into its attributes instead of asking.

    def end_beat(self) -> float | None:
        """Where the piece ends, in beats, or `None` if it has no end.
        
        What `loopAll` needs.  `None` is the honest answer for an
        unfolding score — a `cycle` has no end and looping "all" of it
        means nothing — which is why this is a question rather than a
        number somebody caches.
        """
        # `Schedule.horizon` is "one past the last change, so a caller
        # knows how long to render" — the same number, in the unit the
        # renderer works in.  A *performer* has no schedule and no
        # horizon, which is the `None` case: an unfolding score has no
        # end and looping "all" of it means nothing.
        if self.schedule is None:
            return None
        # **`horizon` is exclusive** — "one past the last change, so a
        # caller knows how long to render" — so the last thing that
        # happens is one before it, and that is where a loop wraps.
        # Without the step back a four-bar piece answers 16.0002, which
        # is one sample and a number nobody wants to read.
        return self.samples_to_beats(max(0, int(self.schedule.horizon()) - 1))

    def set_seed(self, value: int) -> None:
        """Play a different take of a chancy piece.

        **A rebuild, because the seed decides the notes from the first
        instant.**  There is nothing to patch and no way to fade between
        two takes, which is exactly what the plugin found: a re-seed and
        a re-root are one operation there, and here it is a re-load of
        the score with everything else left alone.
        """
        self.seed = int(value)
        self._load_score(self.source())
        self.say(f"seed {self.seed}")

    def roll_seed(self) -> int:
        """Draw a new one, and never the one it is already playing.

        A reroll that can land on the take you are already hearing is
        one that sometimes looks broken — and at one chance in
        2**64 it would be a bug nobody could reproduce.
        """
        import os

        for _ in range(8):
            drawn = int.from_bytes(os.urandom(8), "big")
            if drawn != self.seed:
                return drawn
        return drawn

    def _rebind_midi(self) -> None:
        """Carry the learned controllers across a rebuild, by name.

        Node ids move when the file is edited, so a binding held by id
        would follow whatever node inherited the number — a knob you
        learned onto `cutoff` silently driving `pitch`.
        """
        from .audiomidi import Binding

        if self.midi is None:
            return
        was = {b.name: b.cc for b in self.midi.bindings}
        init = {}
        if self.live is not None:
            init = {n.id: n.init for n in self.live.engine.graph.control_sources()}
        self.midi.bindings = [
            Binding(node=s.node, name=s.name, cc=was.get(s.name),
                    span=KNOB_RANGE, initial=init.get(s.node, 0))
            for s in self.sites]

    def learn(self, name: str) -> bool:
        """Arm (or disarm) `name` for MIDI learn.  Returns whether it is armed.

        A toggle, because the gesture that starts it is the one that should
        stop it: right-click to learn, right-click again to change your mind
        (`spec/liveaudio.md` stage 6).
        """
        if self.midi is None:
            self.say("no MIDI to learn from")
            return False
        site = next((s for s in self.sites if s.name == name), None)
        if site is None:
            return False
        if self.midi.learning == site.node:
            self.midi.cancel()
            self.say(f"{name}: learn cancelled")
            return False
        self.midi.learn(site.node)
        self.say(f"{name}: move a controller to bind it")
        return True

    def learning(self) -> str | None:
        """The name of the parameter waiting for a controller, if any."""
        if self.midi is None or self.midi.learning is None:
            return None
        return next((s.name for s in self.sites
                     if s.node == self.midi.learning), None)

    def binding_text(self, name: str) -> str:
        """`CC7`, `learning…`, or empty — what to show beside a knob."""
        if self.learning() == name:
            return "learning…"
        if self.midi is None:
            return ""
        site = next((s for s in self.sites if s.name == name), None)
        binding = None if site is None else self.midi.binding_of(site.node)
        return "" if binding is None or binding.cc is None else f"CC{binding.cc}"

    # -- editing ------------------------------------------------------------

    def apply(self, text: str, save: bool = True) -> None:
        """Rebuild from `text`, without blocking the caller.

        `save` writes the file first, so what is playing and what is on disk
        are the same thing.  **`save=False` is an audition**: the sound
        changes and the file does not, which is what you want while trying
        a filter coefficient you may not keep.  The status line says which
        happened, because an environment where the two are indistinguishable
        is how work gets lost.
        """
        if self.inert:
            # **Saving is all applying means for a file that is not a
            # program.**  No rebuild to schedule and nothing to restart
            # — and an audition, which deliberately never writes, has
            # nothing at all to do here.
            if not save:
                self.say("nothing to audition — the file is inert")
                return
            self.path.parent.mkdir(parents=True, exist_ok=True)
            self.path.write_text(text)
            self.pending = ""
            self.saved = True
            self.say(f"saved {self.path.name}")
            return
        # **What is being installed, kept for a restart.**  An edit that
        # does not fit has to be started again *as this text* — the file
        # is either behind it (an audition never writes) or exactly it (a
        # save), so remembering it is right either way.
        self._applying = text
        if save:
            # The first save is what creates a new file — and its parent,
            # so `gestate.workbench sketches/a.ges` works before
            # `sketches` does.
            self.path.parent.mkdir(parents=True, exist_ok=True)
            self.path.write_text(text)
            self.pending = ""
        self.saved = save
        if self.live is None:
            # **Saving is not conditional on anything playing.**  A file
            # that was malformed when the editor opened has no
            # instrument, and this used to refuse *before* writing —
            # so you could fix the syntax error, press Ctrl-S, and be
            # told "nothing is playing yet" while your fix went nowhere.
            # An editor that will not save is not an editor, whatever
            # else is wrong.
            #
            # And the save is exactly what makes a retry worth trying:
            # `start` compiles what is on disk, which is now the fixed
            # text.  Off the caller's thread, because it runs `clang`.
            if not save:
                self.say("nothing is playing yet")
                return

            def begin():
                try:
                    self.start()
                except Exception as exc:                 # noqa: BLE001
                    self.trouble = str(exc)
                    self.say(f"saved; still not playing: "
                             f"{self._first_line(exc)}")

            self.say("saved; starting it")
            threading.Thread(target=begin, daemon=True).start()
            return

        def build():
            self.live.compile(text)
            if isinstance(self.live.pending, Exception):
                self.say(f"not applied: {self._first_line(self.live.pending)}")
            else:
                self._load_substrate(text)
                self._place(text)
                self._load_score(text)
                self._load_from_midi(text)
                self._refresh_notes(text)
                # **The build succeeded, so the complaint is over.**  This
                # used to be cleared only in `_progress`, which the driver
                # calls *between blocks* — so an error survived being fixed
                # for as long as nothing was playing, and a program that
                # started clean still showed the error that had stopped it
                # starting the time before.  Cleared where the good news is
                # known rather than where it is next heard.
                self.trouble = ""
                self.say("rebuilt; waiting for the next block"
                         if save else "auditioning (not saved)")

        threading.Thread(target=build, daemon=True).start()

    def audition(self, text: str) -> None:
        """Hear the edit without committing it to the file."""
        self.apply(text, save=False)

    def _progress(self, _written) -> None:
        """Called between blocks, or by the housekeeping thread when the C
        host is running — never on the render loop either way."""
        self._hand_over()
        while self.live.errors:
            self.say("error: " + self._first_line(self.live.errors.pop(0)))
        if self.live.generation != self._seen:
            self._seen = self.live.generation
            # An edit that ran is an error that no longer applies.
            self.trouble = ""
            self.say(f"applied edit {self._seen}"
                     + ("" if self.has_knob else " (no knob in this synth)"))

    def _hand_over(self) -> None:
        """Give a freshly compiled engine to the C host, migrated.

        **Migration stays in Python, and happens here rather than in the
        render loop.**  `audioengine.migrate` is a hundred lines of
        dictionary work matching nodes by origin, which has no business on
        a thread with five milliseconds to fill a buffer — and the reason
        it can be up here is the crossfade: the state it reads is a
        snapshot of an engine that is still sounding, so it is a block or
        so stale by the time the new one takes over, and a 40 ms fade is
        long enough that nobody can hear the difference.

        The read is not synchronised with the render loop, and that is a
        deliberate acceptance rather than an oversight: every field of the
        state is an independent scalar — a phase, a filter's memory, a
        ring — so a torn read is a phase from one instant beside a filter
        from the next, which is a fraction of a sample of drift and not a
        broken value.  There is no invariant across fields to break.
        """
        if self.host is None:
            return                              # the Python driver installs
        waiting = self.live.pending
        if waiting is None or isinstance(waiting, Exception):
            return
        self.live.pending = None
        # **The same rule the Python driver uses**, asked rather than
        # written out again: this was a second copy of the channel check,
        # and when the control block needed one too it went into the
        # other driver and this one went on accepting the edit.
        bigger = self.live.needs_restart(waiting)
        if bigger is not None:
            # **Not a refusal any more — a restart.**  The edit is good
            # and what is too small is known, so asking somebody to quit
            # and start the program again is asking them to do a thing
            # the program can do better: fade out, build the player at
            # the size the new graph wants, fade back in.
            #
            # On another thread, because this runs *on the audio thread*
            # between blocks: `stop` joins that very thread, and a join
            # on yourself is a hang.
            # **The waiting engine is dropped, not kept.**  `start`
            # compiles the file again from scratch and builds a new
            # `Live`, so handing this one back would only give the engine
            # being torn down something to install mid-teardown.
            # **With the text it is restarting *for*.**  `start` reads
            # the file, and an audition deliberately does not write one —
            # so a restart without this brought back the program on disk:
            # the audition never played, and the new player was sized for
            # the *old* program, so the next audition asked to restart
            # again.  One omission, both symptoms.
            threading.Thread(target=self.restart,
                             args=(bigger,), kwargs={"text": self._applying},
                             daemon=True).start()
            return
        from .audioengine import State, migrate

        values, t, lines = self.live.engine.snapshot()
        carried = migrate(self.live.engine.graph, State(values, t, lines),
                          waiting.graph)
        waiting.restore(carried.values, carried.t, carried.lines)
        waiting.frames = self.live.engine.frames
        self.live.engine = waiting
        self.live.generation += 1
        self.host.publish(waiting)

    def _whole(self, error) -> str:
        """The error in full, with its line numbers moved back into the
        author's file.

        Every position a compiler error carries counts from the top of the
        *assembled* program, preludes included, so a mistake on line 3 was
        reported at line 872 and named no file at all — a number that is
        not wrong so much as answering a question nobody asked.  This is
        the one place every message in this class passes through, which is
        why the translation is here and not at each of the six call sites.
        """
        from .audiospans import in_source

        try:
            return in_source(str(error), self._source_text, self.path)
        except Exception:                                   # noqa: BLE001
            return str(error)            # never lose the error to the fixer

    def _first_line(self, error) -> str:
        """A compiler error is a paragraph; a status bar is a line.

        **And the rest of the paragraph is kept**, which it was not: this
        returned the first line and dropped the others on the floor, so the
        half of a type error that says *what was expected where* existed
        only until it was formatted.  What the bar shows is a summary now
        rather than the whole of what is known — `trouble` holds the rest,
        and the editor offers it.
        """
        self.trouble = text = self._whole(error).strip()
        lines = text.splitlines()
        return lines[0] if lines else "unknown error"

    def source(self) -> str:
        """The program's text — **from the file, or from what will be saved
        into it.**

        Every reader of the program goes through here: compiling it,
        placing its knobs, finding its banks, sizing the prelude in front
        of it.  A new file has none of that on disk yet and all of it in
        `pending`, and routing the reads through one method is what lets
        the engine play a program that has never been written.
        """
        try:
            return self.path.read_text()
        except OSError:
            return self.pending

    @property
    def _source_text(self) -> str:
        """The author's own text, for sizing the prelude in front of it.

        A program with a `score` is assembled with `music.ges` as well, so
        the offset depends on the source — see `audiospans._regions`.
        """
        return self.source()

    # -- what the performance owned up to -------------------------------

    #: How a confession reads, singular and plural.  A stall, a dropped
    #: note and a dry thread all *sound* like silence, and the player
    #: deserves to be told which silence they just heard.
    _CONFESSED = {
        "stall": ("the score stalled", "the score stalled"),
        "dropped": ("a note arrived too late to play",
                    "notes arrived too late to play"),
        "dry": ("a question the thread had no record of",
                "questions the thread had no record of"),
    }

    def _report_confessions(self) -> None:
        """Say what the performer confessed, once and then rarely.

        **Doubling, not every time.**  A piece that stalls once wants
        one line; a piece stalling every bar wants to be mentioned, not
        to fill the log with the same sentence — so a kind is said on
        its first occurrence and again only when its count has doubled.
        Silence about a thing happening steadily is its own bug.
        """
        performer = self.performer
        if performer is None:
            return
        counts: dict = {}
        for entry in list(performer.transcript):
            if entry[0] != "reading":
                counts[entry[0]] = counts.get(entry[0], 0) + 1
        for kind, n in sorted(counts.items()):
            told = self._confessed_at.get(kind, 0)
            if n < max(1, told * 2):
                continue
            self._confessed_at[kind] = n
            one, many = self._CONFESSED.get(kind, (kind, kind))
            self.say(f"{one if n == 1 else many}"
                     + ("" if n == 1 else f" ({n} so far)"))

    # -- messages -----------------------------------------------------------

    def say(self, message: str) -> None:
        self.messages.append(message)

    def drain(self) -> list:
        """Everything said since the last call.  The view polls this."""
        out, self.messages = self.messages, []
        return out


# ── The view ────────────────────────────────────────────────────────────────


#: What a file that does not exist yet is opened as.
#:
#: **Not empty.**  An empty file has no `sound`, so the editor would open
#: on a compile error — which is a poor first second in a tool whose whole
#: point is that the program is running while you type.  This is the
#: smallest program that plays, and it shows the one declaration the
#: engine looks for.
#: The suffixes that open **inert** — a text file being edited beside
#: the music, not a program.  The suffix is the one fact known before
#: the file is read, so it is what answers "what says a file is plain";
#: everything else is treated as a program, because guessing from
#: content would refuse somebody's notes over how they happen to start.
INERT = {".txt", ".md"}

STARTER = """# A new synth.
#
# `sound : Sig Float` is what the engine plays — samples in -1.0 .. 1.0,
# one per instant.  Everything else in this file is yours.
#
# `doc/ref/index.md` is what is in scope; the [ref] button top right is
# the same pages in here.

sound : Sig Float
sound = 0.2 * sine 220.0
"""


def _spectrum(samples: list, bins: int) -> list:
    """Log-spaced magnitude bins of a Hann-windowed FFT, 0…1.

    Pure Python and pure function, which is what makes it testable
    with a sine and nothing else.  The scale is a full-scale
    Hann-windowed tone (`n/4` peak magnitude), and the square root on
    the way out is the eye's dynamic range: a -40 dB partial is real
    music and a linear scale would draw it as nothing.
    """
    import math

    n = 1
    while n * 2 <= len(samples):
        n *= 2
    xs = samples[-n:]
    re = [xs[i] * (0.5 - 0.5 * math.cos(2.0 * math.pi * i / (n - 1)))
          for i in range(n)]
    im = [0.0] * n
    # Iterative radix-2, bit-reversed — the textbook loop, written out
    # because a dependency for one transform is not worth its wheel.
    j = 0
    for i in range(1, n):
        bit = n >> 1
        while j & bit:
            j ^= bit
            bit >>= 1
        j |= bit
        if i < j:
            re[i], re[j] = re[j], re[i]
            im[i], im[j] = im[j], im[i]
    length = 2
    while length <= n:
        ang = -2.0 * math.pi / length
        wr, wi = math.cos(ang), math.sin(ang)
        half = length // 2
        for start in range(0, n, length):
            cr, ci = 1.0, 0.0
            for k in range(start, start + half):
                vr = re[k + half] * cr - im[k + half] * ci
                vi = re[k + half] * ci + im[k + half] * cr
                re[k + half], im[k + half] = re[k] - vr, im[k] - vi
                re[k], im[k] = re[k] + vr, im[k] + vi
                cr, ci = cr * wr - ci * wi, cr * wi + ci * wr
        length *= 2
    mags = [math.hypot(re[i], im[i]) for i in range(n // 2)]
    lo, hi = 1, n // 2
    out = []
    for b in range(bins):
        a = int(lo * (hi / lo) ** (b / bins))
        z = max(int(lo * (hi / lo) ** ((b + 1) / bins)), a + 1)
        out.append(max(mags[a:z]))
    scale = n / 4.0
    return [min(1.0, (m / scale) ** 0.5) for m in out]


def is_new(path) -> bool:
    """Is this a file that does not exist yet?

    **A missing file is not an error for an editor.**  `python -m
    gestate.audiopygame a.ges` on a name that is not there used to be a
    `FileNotFoundError` traceback out of `Pane.open`; naming a file that
    does not exist yet is how every editor is asked to start a new one.

    Nothing is written here.  `Workbench` opens on `STARTER` held in
    memory and the **first `Ctrl-S` creates the file**, which is what every
    other editor does and what a name typed by mistake deserves.
    """
    return not Path(path).exists()
