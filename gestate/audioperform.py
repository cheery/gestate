"""Play a synth with a `Score` on one bank and your hands on another.

    python -m gestate.audioperform examples/audio/duet.ges \\
        examples/music/duetline.ges --midi --seconds 12

**The two sources meet here and nowhere else.**  `audioscore` turns a music
program's layout into a `Schedule`; `audiomidi.Notes` turns a keyboard into
values as they arrive.  Both write channel values for a `voices` bank, and
the engine cannot tell which of its channels came from which — so merging
them is a dictionary lookup rather than a design.

That is the whole claim of `examples/audio/duet.ges`: a note is the same
thing whether it was decided by a composer in advance or by a player just
now, and only *when it is decided* differs.

Rendering it offline is the same call with no listener, which is what makes
the scored half checkable against the oracle like everything else here.
"""

from __future__ import annotations

from dataclasses import dataclass, field


class PerformError(Exception):
    pass


@dataclass
class Performance:
    """A graph, and the several things writing control values into it.

    `sources` are consulted in order and the first with an answer wins.  A
    bank driven by a `Score` and one driven by MIDI touch disjoint channels,
    so the order never actually arbitrates — it is defined anyway, because a
    rule that only works while nobody overlaps is not a rule.
    """
    graph: object
    #: Callables `(channel name, t) -> value or None`.
    sources: list = field(default_factory=list)

    def control(self):
        """The `control(node_id, t)` the engine and generated code take."""
        by_node = {node.id: (chan, node.init)
                   for chan, node in self.graph.control_by_chan().items()}

        def control(node: int, t: int):
            entry = by_node.get(node)
            if entry is None:
                return 0
            chan, init = entry
            for source in self.sources:
                value = source(chan, t)
                if value is not None:
                    return value
            return init

        return control


def from_schedule(schedule):
    """A `Schedule` as a source: what it says at `t`, or nothing."""
    return lambda chan, t: schedule.value_at(chan, t)


def from_notes(notes):
    """Live MIDI notes as a source.

    Also the place the engine's position is handed back to the note reader:
    a note has to be stamped with a real instant, and the audio thread is
    the only one that knows which instant it is filling.
    """
    def source(chan, t):
        notes.now = t
        return notes.values.get(chan)

    return source


def bank_named(source: str, name: str):
    """One `voices` bank of a synth, by name, with a useful failure."""
    from .audiovoices import banks_of

    banks = banks_of(source)
    bank = next((b for b in banks if b.name == name), None)
    if bank is None:
        raise PerformError(
            f"this synth has no bank called `{name}`; it has "
            + (", ".join(f"`{b.name}`" for b in banks) or "none"))
    return bank


def allocator_for(source: str, name: str, policy="oldest"):
    from .audioalloc import Allocator
    from .audiovoices import channels_of

    return Allocator(channels_of(source, bank_named(source, name)),
                     policy=policy)


def scored_midi(synth: str, piece: str, bank: str, *, rate: int, block: int,
                policy="oldest"):
    """`(schedule, samples)` — a *MIDI-shaped* music program onto one bank.

    The older path, kept because a piece written with `instrument 32` is a
    real thing: its notes are `Play (Midi …)` and its payload is whatever
    of `(key, velocity)` the bank has room for.  A piece written in the
    program's own payload goes through `scored` below instead.
    """
    from . import midi
    from .audioscore import BankRef, duration_of, schedule_of

    bpm, events = midi.perform(piece)
    allocator = allocator_for(synth, bank, policy)
    schedule = schedule_of(events, bpm, rate, [BankRef(bank, allocator,
                                                       default=True)],
                           block=block)
    return schedule, duration_of(events, bpm, rate)


def has_score(source: str) -> bool:
    """Does this program declare a `score` of its own?

    Textual, and matching how `midi.perform` decides a program is a music
    program: the alternative is compiling it to find out, and the answer is
    needed to choose *which* assembly to compile.
    """
    import re

    return re.search(r"^score\s*[:=]", source, re.M) is not None


def scored(synth: str, piece: str = "", *, rate: int, block: int,
           policy="oldest"):
    """`(schedule, samples, allocators)` — a piece assigned to its own banks.

    The `voices.<bank>` path: the piece names its banks lexically, so which
    bank plays a note is already decided by the time this runs and there is
    no program number to map.  One allocator per bank the piece touches, so
    two banks steal voices independently.
    """
    from .audioalloc import Allocator
    from .audioscore import (duration_of_voices, perform_voices,
                             schedule_voices)
    from .audiovoices import banks_of, channels_of

    both = synth + "\n" + piece
    bpm, events = perform_voices(synth, piece, rate)
    allocators = {b.name: Allocator(channels_of(both, b), policy=policy)
                  for b in banks_of(both)}
    schedule = schedule_voices(events, bpm, rate, allocators, block=block)
    return schedule, duration_of_voices(events, bpm, rate), allocators


def graph_of(synth: str, piece: str = "", *, rate: int):
    """The graph, from whichever assembly this program needs.

    A program with a `score` is compiled with the music prelude and its
    piece; one without is not, because nine constructors and their compile
    time are not something a synth that plays no score should pay.  Both
    readings have to come from the *same* assembly as the schedule, or the
    channels a note is written to are not the channels the graph has.
    """
    from .audioextract import extract, extract_analysis
    from .audioscore import assemble_performance
    from .pipeline import analyse

    if has_score(synth + "\n" + piece):
        return extract_analysis(
            analyse(assemble_performance(synth, piece, rate)), rate=rate)
    return extract(synth, rate=rate)


def render_wav(graph, path: str, seconds: float, rate: int, block: int,
               control) -> int:
    """Render a performance to a `.wav` through the *engine*.

    The engine rather than the oracle, because a scored piece of any length
    is minutes of interpreter and milliseconds of compiled code — and the
    two are bit-identical, which is the whole point of having checked.
    """
    import struct
    import wave

    from .audio import safe_sample
    from .audioengine import run

    samples = graph.frames(
        run(graph, int(seconds * rate), block=block, control=control))
    channels = graph.channels()
    data = bytearray()
    for frame in samples:
        for x in (frame if channels > 1 else (frame,)):
            data += struct.pack("<h", int(safe_sample(x) * 32767))
    with wave.open(path, "wb") as f:
        f.setnchannels(channels)
        f.setsampwidth(2)
        f.setframerate(rate)
        f.writeframes(bytes(data))
    return len(samples)


# ── CLI ─────────────────────────────────────────────────────────────────────


def main(argv=None) -> int:
    import argparse

    from .audiospans import cli_error
    import sys
    from pathlib import Path

    from .audioextract import ExtractError
    from .audiolive import DEFAULT_BLOCK, DEFAULT_RATE, LiveError, play
    from .audiollvm import LLVMError

    ap = argparse.ArgumentParser(
        prog="python -m gestate.audioperform",
        description="Play a synth with a score on one bank and MIDI on another.")
    ap.add_argument("synth")
    ap.add_argument("piece", nargs="?", default=None,
                    help="a music program; its layout drives `--score-bank`")
    ap.add_argument("--score-bank", default="bass")
    ap.add_argument("--midi-bank", default="lead")
    ap.add_argument("--midi", nargs="?", const="", default=None,
                    metavar="PORT", help="play `--midi-bank` from a keyboard")
    ap.add_argument("--rate", type=int, default=DEFAULT_RATE)
    ap.add_argument("--block", type=int, default=DEFAULT_BLOCK)
    ap.add_argument("--seconds", type=float, default=None)
    ap.add_argument("--policy", default="oldest",
                    help="voice stealing: oldest, or none to drop the note")
    ap.add_argument("-o", "--output", default=None,
                    help="render to a .wav instead of playing")
    args = ap.parse_args(argv)

    listener = None
    try:
        synth = Path(args.synth).read_text()
        piece = Path(args.piece).read_text() if args.piece else ""
        graph = graph_of(synth, piece, rate=args.rate)
        performance = Performance(graph)
        seconds = args.seconds

        if has_score(synth + "\n" + piece):
            # The piece names its own banks, so nothing here chooses one.
            schedule, samples, allocators = scored(
                synth, piece, rate=args.rate, block=args.block,
                policy=args.policy)
            performance.sources.append(from_schedule(schedule))
            if seconds is None:
                seconds = samples / args.rate
            print(f"score: {len(schedule.channels())} channels across "
                  f"{', '.join('`' + b + '`' for b in sorted(allocators))}, "
                  f"{samples / args.rate:.1f}s", file=sys.stderr)
        elif args.piece is not None:
            schedule, samples = scored_midi(
                synth, piece, args.score_bank,
                rate=args.rate, block=args.block, policy=args.policy)
            performance.sources.append(from_schedule(schedule))
            if seconds is None:
                seconds = samples / args.rate
            print(f"score (MIDI-shaped): {len(schedule.channels())} channels "
                  f"on `{args.score_bank}`, {samples / args.rate:.1f}s",
                  file=sys.stderr)

        if args.midi is not None:
            from .audiomidi import Listener, MidiError, Notes

            notes = Notes(allocator_for(synth, args.midi_bank, args.policy))
            performance.sources.append(from_notes(notes))
            try:
                listener = Listener(None, args.midi or None)
                listener.feed = notes.feed          # notes only, on this port
                listener.start()
                print(f"MIDI: playing `{args.midi_bank}`", file=sys.stderr)
            except MidiError as exc:
                print(f"gestate: {cli_error(exc, args.synth)}", file=sys.stderr)
                return 1

        control = performance.control()
        if args.output:
            n = render_wav(graph, args.output, seconds or 2.0,
                           args.rate, args.block, control)
            print(f"{args.output}: {n} samples at {args.rate} Hz")
            return 0

        frames, backend = play(synth, seconds, args.rate, args.block,
                               control=control)
        print(f"{args.synth}: {frames} frames through {backend}",
              file=sys.stderr)
    except (ExtractError, LLVMError, LiveError, PerformError) as exc:
        print(f"gestate: {cli_error(exc, args.synth)}", file=sys.stderr)
        return 1
    except FileNotFoundError as exc:
        print(f"gestate: {cli_error(exc, args.synth)}", file=sys.stderr)
        return 1
    finally:
        if listener is not None:
            listener.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
