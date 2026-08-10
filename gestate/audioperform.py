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


def from_performer(performer):
    """A `Performer` as a source: advanced to `t`, then read like `Notes`.

    The advance rides the control tick — the first channel asked at a
    boundary moves the cursor, every channel then reads the values it
    left — so a performer costs what a schedule lookup costs, plus the
    allocator exactly when a note happens.
    """
    def source(chan, t):
        performer.advance(t)
        return performer.values.get(chan)

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

    By its declarations, not its text — `audio._authored` parses the
    author's file — because the answer decides *which* assembly to
    compile, and it should be about what the program declares rather than
    what a line happens to look like.
    """
    from .audio import _authored

    return "score" in _authored(source)[1]


def scored(synth: str, piece: str = "", *, rate: int, block: int,
           policy="oldest", seed: int = 0):
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
    bpm, events = perform_voices(synth, piece, rate, seed)
    allocators = {b.name: Allocator(channels_of(both, b), policy=policy)
                  for b in banks_of(both)}
    schedule = schedule_voices(events, bpm, rate, allocators, block=block)
    return schedule, duration_of_voices(events, bpm, rate), allocators


def dynamic(synth: str, piece: str = "", *, rate: int, block: int,
            policy="oldest", horizon: float = 4.0, seed: int = 0,
            patience: float | None = None):
    """`scored`'s twin with nothing baked: `(performer, allocators)`.

    Stage two's portal (`spec/dynamicscore.md`): the layout is forced as
    the clock reaches it, a beat horizon at a time, so an endless score —
    `cycle`, `unfold` — is as welcome as one that ends.  Which is why,
    unlike `scored`, this returns no duration: an unfolding score does
    not know when it ends, and pretending otherwise would mean forcing
    it to find out.  The bake stays the default everywhere; this path
    exists beside it, held equal on finite scores by `test_lazyscore.py`.
    """
    from .audioalloc import Allocator
    from .audiodynamic import LazyPerformer, ScoreStream
    from .audioscore import stream_root
    from .audiovoices import banks_of, channels_of

    from .transcript import Transcript

    both = synth + "\n" + piece
    tempo, state, root, by_tag = stream_root(synth, piece, rate, seed)
    allocators = {b.name: Allocator(channels_of(both, b), policy=policy)
                  for b in banks_of(both)}
    stream = ScoreStream(state, root, by_tag, patience=patience)
    record = Transcript(source_sha=Transcript.sha_of(both), rate=rate,
                        block=block, seed=seed)
    performer = LazyPerformer(stream, tempo, rate, allocators, block=block,
                              horizon=horizon, record=record)
    return performer, allocators


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


def _frames(graph, samples: int, block: int, control) -> list:
    """`samples` frames of a graph — compiled when there is a compiler.

    `quartet.ges` measured the gap: the interpreter renders its three
    minutes in about a day and a half, the generated code in under a
    minute.  The two are bit-identical (`test_audiollvm.py` is that
    check), so which one ran is not something a listener can tell — a
    machine with no `clang` simply takes the long way rather than failing.
    """
    import shutil
    import tempfile

    if shutil.which("clang") is not None:
        from .audiollvm import run_native

        with tempfile.TemporaryDirectory() as d:
            return run_native(graph, d, samples, block=block, control=control)
    from .audioengine import run

    return graph.frames(run(graph, samples, block=block, control=control))


def render_wav(graph, path: str, seconds: float, rate: int, block: int,
               control) -> int:
    """Render a performance to a `.wav` — `_frames`, packed and written."""
    import struct
    import wave

    from .audio import safe_sample

    samples = _frames(graph, int(seconds * rate), block, control)
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
    ap.add_argument("--dynamic", action="store_true",
                    help="perform the score as it plays instead of baking it")
    ap.add_argument("--seed", type=int, default=None,
                    help="the take's seed; omitted, a chancy score draws "
                         "one and says so")
    ap.add_argument("--transcript", default=None, metavar="PATH",
                    help="write the dynamic performance's log — seed, "
                         "stalls, drops — after rendering")
    ap.add_argument("-o", "--output", default=None,
                    help="render to a .wav instead of playing")
    args = ap.parse_args(argv)

    listener = None
    performer = None
    try:
        synth = Path(args.synth).read_text()
        piece = Path(args.piece).read_text() if args.piece else ""
        graph = graph_of(synth, piece, rate=args.rate)
        performance = Performance(graph)
        seconds = args.seconds

        # The take's seed.  An author-declared `seed` wins inside the
        # assembly whatever is passed; entropy is drawn only when the
        # piece can tell the difference, and **the renderer records what
        # it supplied** — here, by saying it, so the take is repeatable
        # with `--seed` (`spec/dynamicscore.md`, provenance).
        import re

        seed = args.seed
        if seed is None:
            if re.search(r"\b(sown|roll|chance|sow)\b", synth + "\n" + piece):
                import os as _os

                seed = int.from_bytes(_os.urandom(8), "big")
                print(f"seed: {seed} (replay this take with --seed {seed})",
                      file=sys.stderr)
            else:
                seed = 0

        if has_score(synth + "\n" + piece):
            from .audioscore import unfolding_names

            # The piece names its own banks, so nothing here chooses one.
            # A score the bake cannot be trusted to finish laying out is
            # routed to the dynamic path rather than refused: it plays
            # the same where both can play at all, and only this path
            # can play it.
            unfolding = args.dynamic or unfolding_names(synth + "\n" + piece)
            if unfolding and not args.dynamic:
                print("score: unfolds ("
                      + ", ".join(f"`{n}`" for n in unfolding)
                      + "); performing dynamically", file=sys.stderr)
            if unfolding:
                if seconds is None:
                    # An unfolding score does not know when it ends, and
                    # forcing it to find out is exactly what this path is
                    # for not doing.
                    print("gestate: a dynamic performance cannot know when "
                          "an unfolding score ends; give --seconds",
                          file=sys.stderr)
                    return 1
                # A wall-clock budget only when the clock is a wall's:
                # an offline render waits out an expensive forcing, a
                # live one must not.
                performer, allocators = dynamic(
                    synth, piece, rate=args.rate, block=args.block,
                    policy=args.policy, seed=seed,
                    patience=None if args.output else 0.05)
                performance.sources.append(from_performer(performer))
                print(f"score (dynamic): performed across "
                      f"{', '.join('`' + b + '`' for b in sorted(allocators))}"
                      f", {seconds:.1f}s", file=sys.stderr)
            else:
                schedule, samples, allocators = scored(
                    synth, piece, rate=args.rate, block=args.block,
                    policy=args.policy, seed=seed)
                performance.sources.append(from_schedule(schedule))
                if seconds is None:
                    seconds = samples / args.rate
                print(f"score: {len(schedule.channels())} channels across "
                      f"{', '.join('`' + b + '`' for b in sorted(allocators))}"
                      f", {samples / args.rate:.1f}s", file=sys.stderr)
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
            if args.transcript is not None:
                if performer is None:
                    print("gestate: only a dynamic performance keeps a "
                          "transcript; nothing was written", file=sys.stderr)
                else:
                    performer.record.save(args.transcript)
                    kept = len(performer.record.events)
                    print(f"{args.transcript}: seed {performer.record.seed}, "
                          f"{kept} event(s)", file=sys.stderr)
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
