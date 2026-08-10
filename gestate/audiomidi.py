"""MIDI continuous controllers as control-rate parameters.

A synth declares its knobs as control channels (`spec/liveaudio.md`
§"Several control channels"), and this is one way to turn them: a CC
message from a device becomes the value a control source takes at the next
block boundary.

**Why CC fits and notes do not.** A controller sends a *value*, and the
engine samples control sources once per block and holds them — so if a knob
moved five times inside one block, the block sees where it ended up, and
nothing is lost that anyone could hear.  That is what makes "never faster
than the control clock" a discipline rather than a compromise, and it is
why the device's own rate never reaches the graph.

A note-on is not a value, and coalescing one **drops it**: two note-ons in a
block become one, and a note-on with its note-off in the same block cancels
to silence.  At 256 frames and 48 kHz that is 5.3 ms, which a drum roll or a
trill reaches easily.  Notes therefore want a per-block event *list* with
sample offsets, which is allocation, which is the one thing the static
fragment is defined by excluding — so they are deliberately not here.  See
`spec/liveaudio.md` open question 5.

Nothing in this module is in the audio path.  A reader thread writes the
latest value per controller into a dict; the block callback reads it.  That
is one dict lookup per parameter per block, and no MIDI parsing anywhere
near the deadline.
"""

from __future__ import annotations

import threading
from dataclasses import dataclass, field


class MidiError(Exception):
    pass


@dataclass
class Binding:
    """One control source, and the controller that drives it."""
    node: int
    #: The definition the source came from — for reporting, and for binding
    #: by name rather than by position when a caller wants to.
    name: str
    #: The controller number, or `None` for a parameter with no controller
    #: bound — which is the ordinary state before anyone has used learn.
    cc: int | None
    #: `(lo, hi)` the CC's 0..127 is mapped onto, or `None` for raw.
    span: tuple | None = None
    #: What this parameter reads as until its controller is first moved.
    #:
    #: **The source's own initial value**, taken from the graph — not 0.
    #: A synth declares `cutoff = 70 ::: mkSig (wait c)` precisely so it
    #: sounds like something before anything is plugged in, and a host that
    #: answered 0 would silently override that at the first block boundary.
    #: Nothing catches it either: the synth plays, sounding wrong.
    initial: object = 0

    def value_of(self, raw: int) -> int:
        """A CC's 0..127 as this parameter's number."""
        if self.span is None:
            return raw
        lo, hi = self.span
        return lo + (hi - lo) * raw // 127


@dataclass
class Controls:
    """The live value of every bound controller.

    Deliberately not a MIDI object: `set` is the whole interface the engine
    needs, so the mapping and the coalescing can be tested without a device
    — which matters, since a machine may have no MIDI at all and a test
    that skips is a test that never runs.
    """
    bindings: list = field(default_factory=list)
    #: CC number → its latest raw value.  **This dict is the coalescing.**
    #: A controller that moves fifty times between two blocks leaves one
    #: entry, which is what "never faster than the control clock" means in
    #: practice.  No lock: CPython dict writes are atomic, the reader wants
    #: whatever is most recent, and a torn read is not a thing that can
    #: happen to one integer.
    latest: dict = field(default_factory=dict)
    #: The node waiting to be bound to the next controller that moves, or
    #: `None`.  **MIDI learn**, which is the only sane way to bind a knob:
    #: nobody knows which CC number their device sends, and everybody can
    #: wiggle the control they mean.
    learning: object = None

    @classmethod
    def bind(cls, graph, source: str | None = None, *, first_cc: int = 1,
             spans: dict | None = None) -> "Controls":
        """Bind a graph's control sources to consecutive CC numbers.

        In **declaration order** when `source` is given — the order a person
        reading the file sees them, and the order an environment lays them
        down a page — rather than node-id order, which is an artefact of
        extraction.  `spans` maps a parameter's name to the `(lo, hi)` its
        0..127 should cover; a name with no entry gets the raw CC value.
        """
        spans = spans or {}
        if source is not None:
            from .audiospans import controls as sites

            order = [(s.name, s.node) for s in sites(source, rate=graph.rate)]
        else:
            order = [(n.origin.split("/")[-2], n.id)
                     for n in graph.control_sources()]
        init = {n.id: n.init for n in graph.control_sources()}
        return cls([Binding(node=node, name=name, cc=first_cc + i,
                            span=spans.get(name), initial=init.get(node, 0))
                    for i, (name, node) in enumerate(order)])

    def set(self, cc: int, raw: int) -> None:
        """A controller moved.  Called from the reader thread.

        If a parameter is *learning*, this is the message that binds it —
        the first controller to move after arming is the one meant, which
        is what makes learn work without anyone reading a manual.  The
        binding is stolen from whatever held that CC, because one physical
        control driving two parameters is never what a person wants and is
        confusing to discover.
        """
        if self.learning is not None:
            self._bind(self.learning, cc)
            self.learning = None
        self.latest[cc] = raw

    def learn(self, node) -> None:
        """Arm `node`: the next controller to move becomes its knob."""
        self.learning = node

    def cancel(self) -> None:
        """Disarm.  Arming the same node twice is how a view toggles it."""
        self.learning = None

    def _bind(self, node, cc: int) -> None:
        for binding in self.bindings:
            if binding.cc == cc and binding.node != node:
                # Freed rather than shared: two parameters on one knob is
                # not a configuration anyone means, and it is hard to
                # notice once it has happened.
                binding.cc = None
        for binding in self.bindings:
            if binding.node == node:
                binding.cc = cc
                return

    def binding_of(self, node):
        return next((b for b in self.bindings if b.node == node), None)

    def control(self):
        """The `control(node_id, t)` the engine and `run_native` take."""
        by_node = {b.node: b for b in self.bindings}

        def read(node: int, _t: int):
            binding = by_node.get(node)
            if binding is None:
                return 0
            raw = None if binding.cc is None else self.latest.get(binding.cc)
            return binding.initial if raw is None else binding.value_of(raw)

        return read

    def describe(self) -> str:
        return ", ".join(
            f"{b.name}=" + ("CC{}".format(b.cc) if b.cc is not None else "—")
            for b in self.bindings) or "none"


# ── The device ──────────────────────────────────────────────────────────────


def input_names() -> list:
    """The MIDI inputs on this machine, or `[]` if mido cannot look."""
    try:
        import mido
    except ImportError:
        return []
    try:
        return list(mido.get_input_names())
    except Exception:                                   # noqa: BLE001
        # No backend (no rtmidi, no ALSA): not having MIDI is not an error,
        # it is a machine without MIDI.
        return []


def describe_ports() -> str:
    """The inputs, numbered — what `--midi-ls` prints and what an error
    that could not find a port says instead of just refusing."""
    names = input_names()
    if not names:
        return "no MIDI input on this machine"
    return "\n".join(f"  {i}  {name}" for i, name in enumerate(names))


def resolve_port(spec: str | None):
    """A real port name from what someone typed, or `None` for the first.

    **An index or a substring**, because the names real drivers hand out
    look like `Launchkey Mini MK3:Launchkey Mini MK3 MIDI 1 28:0` — not a
    thing anyone types once, let alone twice.  `--midi 1` is an index into
    `input_names`; `--midi launchkey` is matched case-insensitively and
    must pick out exactly one, since a spec that quietly took the first of
    several matches would bind your knobs to whichever device happened to
    enumerate first today.
    """
    if not spec:
        return None                 # `Listener` already means "the first"
    names = input_names()
    if not names:
        raise MidiError("no MIDI input on this machine")
    if spec.isdigit():
        index = int(spec)
        if not 0 <= index < len(names):
            raise MidiError(f"there is no MIDI input {index}:\n"
                            + describe_ports())
        return names[index]
    hits = [name for name in names if spec.lower() in name.lower()]
    if not hits:
        raise MidiError(f"no MIDI input matches `{spec}`:\n"
                        + describe_ports())
    if len(hits) > 1:
        raise MidiError(f"`{spec}` matches {len(hits)} inputs:\n"
                        + "\n".join(f"  {name}" for name in hits))
    return hits[0]


class Listener:
    """A thread that turns CC messages into `Controls.set` calls.

    Stops on `close()`.  Everything it does is outside the audio path: the
    engine never waits on it, and if the device goes away the last values
    simply persist, which is what a knob does when you let go of it.
    """

    def __init__(self, controls: Controls, port_name: str | None = None,
                 channel: int | None = None):
        self.controls = controls
        self.port_name = port_name
        #: MIDI channel 0..15 to listen on, or `None` for all of them.
        self.channel = channel
        self._port = None
        self._thread: threading.Thread | None = None
        self._stop = threading.Event()
        self.messages = 0

    def start(self) -> "Listener":
        import mido

        names = input_names()
        if not names:
            raise MidiError("no MIDI input on this machine")
        name = self.port_name or names[0]
        if name not in names:
            raise MidiError(
                f"no MIDI input `{name}`; there is " + ", ".join(names))
        self._port = mido.open_input(name)
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()
        return self

    def _run(self) -> None:
        for message in self._port:
            if self._stop.is_set():
                break
            self.feed(message)

    def feed(self, message) -> bool:
        """One message.  Separate from the thread so it can be tested."""
        if getattr(message, "type", None) != "control_change":
            return False
        if self.channel is not None and message.channel != self.channel:
            return False
        self.controls.set(message.control, message.value)
        self.messages += 1
        return True

    def close(self) -> None:
        self._stop.set()
        if self._port is not None:
            self._port.close()
            self._port = None


# ── Notes ───────────────────────────────────────────────────────────────────
#
# A controller is a *value* and survives being sampled once per block; a note
# is an *event* and does not.  This is the other half of that distinction:
# rather than coalescing note events, a note is turned into control values —
# `gateAt`, `offAt`, `pitch` — which do survive it, because the *value* names
# the instant the note starts and the voice compares it against its own
# `ticks`.  So a note arriving mid-block still begins mid-block.
#
# What is lost is only the arrival: a key pressed inside block B cannot sound
# before block B+1, because the host has already filled B.  That is the
# latency every engine has, and it is bounded by the block rather than by
# anything here.


class Notes:
    """Live MIDI notes driving a `voices` bank.

    The bridge is `audioalloc.Allocator`, which is also what a `Score` uses
    — a note is the same thing whether it arrives from a keyboard now or
    from a layout computed in advance, and only *when it is decided*
    differs.  Keeping one allocator for both is what makes a piece and a
    performance the same code path.

    Values live in a dict the audio callback reads, exactly as `Controls`
    does, and for the same reason: nothing MIDI may happen near a deadline.
    """

    def __init__(self, allocators, channel: int | None = None, payload=None,
                 route=None):
        #: Bank name → its `Allocator`.  A bare allocator is accepted and
        #: becomes the only bank, which is what a one-bank synth means.
        if not isinstance(allocators, dict):
            allocators = {"": allocators}
        if not allocators:
            raise MidiError("no banks for MIDI to play")
        self.allocators = allocators
        #: `message -> bank name`, or `None` to drop the note.  **Which
        #: bank a key plays is policy, not wiring**, so it is a function:
        #: a keyboard split by pitch, a controller sending each hand on its
        #: own MIDI channel, or a program change — all the same hook.
        # **One bank plays everything.**  Routing by MIDI channel is only
        # a choice when there is something to choose between, and defaulting
        # to it with one bank contradicts `channel=` — pin a listener to
        # channel 2 and every note would arrive, then be routed to a bank
        # that only answers for channel 0.
        names = list(allocators)
        self.route = route or (one_bank(names[0]) if len(names) == 1
                               else by_midi_channel(names))
        #: `message -> payload tuple`.  The default takes as many of
        #: `(note, velocity)` as the bank's record has fields — a keyboard
        #: is MIDI-shaped, so that is the useful default — and a bank whose
        #: payload means something else supplies its own.
        self.payload = payload
        #: Which bank*s* each sounding key went to, so its release finds
        #: the same ones.  A player may hold a note, change the split, and
        #: let go — and the note has to end where it began.
        self.playing: dict = {}
        #: `(bank, message) -> payload tuple, or None to decline`.  When
        #: set, **every listening bank is asked** and all that accept get
        #: the note: layering a piano under strings is one key on two
        #: instruments, and declining is what `Nothing` is for.
        self.accepts = None
        #: Bank name → whether it listens.  The environment's switch, not
        #: the program's: two banks may carry the same payload and share
        #: one `FromMIDI` instance, so nothing in the type can tell them
        #: apart (`audio.ges`).
        self.listening: dict = {b: True for b in allocators}
        #: MIDI channel to listen on, or `None` for all of them.
        self.channel = channel
        #: Channel name → its current value.  Written by the reader thread,
        #: read by the block callback; one integer each, so no lock.
        self.values: dict = {}
        self.notes = 0
        #: The sample the engine has reached, as far as anyone knows.  A
        #: note is stamped with it, so `gateAt` names a real instant rather
        #: than "now" — which the audio thread would have to interpret.
        self.now = 0

    # -- what the engine reads ----------------------------------------------

    def control_for(self, graph):
        """The `control(node_id, t)` this bank's channels answer."""
        by_node = {}
        for chan, node in graph.control_by_chan().items():
            by_node[node.id] = (chan, node.init)

        def control(node: int, t: int):
            entry = by_node.get(node)
            if entry is None:
                return 0
            chan, init = entry
            self.now = t
            return self.values.get(chan, init)

        return control

    # -- what MIDI writes ---------------------------------------------------

    def feed(self, message) -> bool:
        """One message.  Returns whether it was a note this bank plays.

        A `note_on` with velocity 0 is a `note_off` — the convention every
        device that runs notes together uses, and a synth that took it
        literally would hang every note it played.
        """
        kind = getattr(message, "type", None)
        if kind not in ("note_on", "note_off"):
            return False
        if self.channel is not None and message.channel != self.channel:
            return False

        at = self.now
        released = kind == "note_off" or getattr(message, "velocity", 0) == 0
        key = (message.channel, message.note)
        if released:
            # Where it *began*, not where it would be routed now.
            banks = self.playing.pop(key, None)
            if not banks:
                return False
            changes = [c for b in banks
                       for c in self.allocators[b].note_off(message.note, at)]
        elif self.accepts is not None:
            changes, taken = [], []
            for bank in self.allocators:
                if not self.listening.get(bank, True):
                    continue
                payload = self.accepts(bank, message)
                if payload is None:
                    continue
                changes += self.allocators[bank].note_on(
                    message.note, payload, at)
                taken.append(bank)
            if not taken:
                return False
            self.playing[key] = taken
        else:
            bank = self.route(message)
            if bank is None or bank not in self.allocators:
                return False
            # The switch is authoritative on **both** paths.  It gated only
            # the `accepts` one, so a program with no `FromMIDI` instance —
            # whose switches are greyed out precisely because they cannot
            # do anything — went on passing notes anyway.
            if not self.listening.get(bank, True):
                return False
            self.playing[key] = [bank]
            changes = self.allocators[bank].note_on(
                message.note, self.payload_of(message, bank), at)
        for chan, value in changes:
            self.values[chan] = value
        self.notes += 1
        return True

    def payload_of(self, message, bank: str = "") -> tuple:
        if self.payload is not None:
            return tuple(self.payload(message))
        from .audioalloc import PAYLOAD

        want = self.allocators[bank].fields - PAYLOAD
        return (message.note, message.velocity)[:want]

    def all_off(self) -> None:
        """Panic.  Every held note on every bank, released now."""
        for allocator in self.allocators.values():
            for chan, value in allocator.all_off(self.now):
                self.values[chan] = value
        self.playing.clear()

    def sounding(self) -> list:
        return sorted(k for a in self.allocators.values()
                      for k in a.sounding())

    def sounding_on(self, bank: str) -> list:
        return self.allocators[bank].sounding()


# ── Routing ─────────────────────────────────────────────────────────────────


def by_midi_channel(banks: list):
    """MIDI channel *n* plays bank *n*, in declaration order.

    The default, and what hardware does: a controller with two keyboards
    sends them on two channels, and a sequencer sends a track per channel.
    A channel past the last bank plays nothing rather than folding onto one
    — silently doubling a part is worse than not hearing it.
    """
    def route(message):
        i = getattr(message, "channel", 0)
        return banks[i] if 0 <= i < len(banks) else None

    return route


def by_pitch(splits: list):
    """A keyboard split: `[("bass", 48), ("lead", None)]`.

    Each pair is a bank and the note number *below which* it plays; `None`
    is the rest of the keyboard.  The classic left-hand/right-hand split,
    and the reason routing is a function rather than a channel number.
    """
    def route(message):
        for bank, below in splits:
            if below is None or message.note < below:
                return bank
        return None

    return route


def one_bank(name: str):
    """Everything to one bank, whatever it arrives on."""
    return lambda _message: name


class NoteListener(Listener):
    """A `Listener` that feeds notes as well as controllers.

    One port, both kinds: a keyboard sends its modulation wheel down the
    same cable as its keys, and asking the player to open two would be an
    invention of this program's rather than of MIDI's.
    """

    def __init__(self, controls, notes: Notes, port_name: str | None = None,
                 channel: int | None = None):
        super().__init__(controls, port_name, channel)
        self.notes_sink = notes

    def feed(self, message) -> bool:
        if super().feed(message):
            return True
        return self.notes_sink.feed(message)


# ── FromMIDI — a note becomes a bank's payload, or does not ─────────────────


class FromMidi:
    """Runs a program's `FromMIDI` instances to build payloads.

    **The interpreter, beside the native engine.**  The engine is machine
    code and knows nothing about instances, so `noteOn ch p v` is evaluated
    here — off the audio thread, once per key press, and cached.  Notes are
    rare enough that a G-machine run per press is nothing; the cost is at
    rebuild time, where the state has to be compiled.

    A bank whose payload has no instance simply is not in `banks`, which is
    what greys its switch out rather than failing anywhere.
    """

    def __init__(self, state, banks: list):
        #: Bank name → the generated forwarder `<bank>FromMidi`.  Generated
        #: because only *reachable* definitions are compiled and nothing in
        #: a synth calls `noteOn` — the caller is a keyboard.
        self.state = state
        self.banks = {b: f"{b}FromMidi" for b in banks
                      if f"{b}FromMidi" in getattr(state, "globals", {})}
        self._cache: dict = {}

    def offers(self, bank: str) -> bool:
        """Can this bank take a MIDI note at all?"""
        return bank in self.banks

    def payload_for(self, bank: str, channel: int, pitch: int, velocity: int):
        """The payload's fields, or `None` if the instance declined.

        `Nothing` is a real answer and the reason this is one method rather
        than a routing table: a bank that only wants one channel, or only
        the low half of the keyboard, says so in ordinary gestate.
        """
        key = (bank, channel, pitch, velocity)
        if key in self._cache:
            return self._cache[key]
        answer = self._run(bank, channel, pitch, velocity)
        self._cache[key] = answer
        return answer

    def _run(self, bank: str, *args):
        from .gmachine import Eval, GmError, GmState, Mkap, NCon, NNum, \
            _deref, run

        name = self.banks.get(bank)
        if name is None:
            return None
        stack = [self.state.globals[name]] + [NNum(a) for a in args]
        # One `Mkap` per argument: a global of arity three cannot reduce
        # until all three are applied, so applying them one at a time —
        # which is what `reactive._apply` does — unwinds with too few.
        code = [Mkap()] * len(args) + [Eval()]
        scratch = GmState(code, stack, self.state.globals, [],
                          now=[], chanCounter=0, chans={})
        try:
            run(scratch)
        except GmError:
            return None
        node = _deref(scratch.stack[0])
        if not isinstance(node, NCon) or node.tag != self.state.cons["Just"].tag:
            return None                      # `Nothing`: the bank declined
        return _fields_of(node.args[0], self.state)


def _fields_of(node, state) -> tuple:
    """A payload record's fields, flattened to the values a channel takes.

    **Forced, field by field** — a record built by an instance holds
    thunks wherever the instance *computed* (`Tone (toFloat v / 127.0)
    n`), and the version that only dereferenced skipped those fields
    silently.  Every raw-field instance in the tree worked; the first
    computed field played its note with the wrong arity.  A field that
    is not a value after forcing is a loud error, not a shorter payload.
    """
    from .gmachine import GmError, NCon, NInd, NNum, _force

    node = _force(node, state)
    while isinstance(node, NInd) and node.target is not None:
        node = node.target
    if isinstance(node, NNum):
        return (node.n,)
    if isinstance(node, NCon):
        out: list = []
        for arg in node.args:
            out.extend(_fields_of(arg, state))
        return tuple(out)
    raise GmError(
        f"a payload field that is not a value: {type(node).__name__}")
