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
                             schedule_shapes, schedule_voices, shapes_of)
    from .audiovoices import banks_of, channels_of

    both = synth + "\n" + piece
    bpm, events = perform_voices(synth, piece, rate, seed)
    allocators = {b.name: Allocator(channels_of(both, b), policy=policy)
                  for b in banks_of(both)}
    schedule = schedule_voices(events, bpm, rate, allocators, block=block)
    # The piece's own automation, baked beside its notes: an offline
    # render of a shaped piece should sound like a live one.
    schedule_shapes(schedule, shapes_of(synth, piece, rate, seed), bpm,
                    rate, block=block)
    return schedule, duration_of_voices(events, bpm, rate), allocators


def holds_reader(notes, ports: dict):
    """`Notes` as a probe's world: what each bank's port holds, sorted.

    Sorted for determinism — a chord is a set, but a reading is a value
    in a transcript, and one spelling of it replays.
    """
    def reader(port, key=None):
        bank = ports.get(port)
        if bank is None or notes is None:
            return []
        # A playing key is `(channel, note)` — the port holds *notes*.
        return sorted((key[1] if isinstance(key, tuple) else key)
                      for key, banks in notes.playing.items()
                      if bank in banks)

    return reader


#: How a performance's confessions read out loud, singular and plural.
#: A stall, a dropped note and a dry thread all *sound* like silence;
#: the log is the only thing that can say which one a listener heard,
#: so the words are spelled here rather than left as bare counts.
_CONFESSED = {
    "stall": ("stall", "stalls"),
    "dropped": ("dropped note", "dropped notes"),
    "dry": ("question the thread had no record of",
            "questions the thread had no record of"),
}


def _confessed(counts: dict) -> str:
    if not counts:
        return ""
    parts = []
    for kind, n in sorted(counts.items()):
        one, many = _CONFESSED.get(kind, (kind, kind))
        parts.append(f"{n} {one if n == 1 else many}")
    return " — " + ", ".join(parts)


def _progress(control, performer, samples: int, rate: int):
    """`control`, with the render saying where it stands.

    Offline is the one place a stall is invisible: live, the silence is
    audible and the player turns around; offline it is a long wait with
    the fan on — observed as twenty minutes of it, on a piece whose
    stream was never going to produce.  The wrapper rides the control
    clock, the hook every block already passes through, and says two
    things on stderr: where the render stands (a tty line, rewritten in
    place, so a log never carries it), and — the moment the transcript
    confesses one — that the stream is stalling and at which beat.  A
    stall that persists with nothing *ever* forced is also named for
    what it usually is, because "no events and no error" cost a real
    afternoon to read as "the walk cannot terminate".
    """
    import sys
    import time

    err = sys.stderr
    tty = err.isatty()
    if performer is None and not tty:
        return control

    last_block = -1
    last_line = 0.0
    begun = time.monotonic()
    line = False                    # a rewritten line stands unfinished
    stalls = 0                      # confessions already spoken for
    named = False                   # the non-termination suspicion, once

    def say(text: str):
        nonlocal line
        if line:
            err.write("\r\x1b[K")
            line = False
        err.write(text + "\n")
        err.flush()

    def wrapped(node: int, t: int):
        nonlocal last_block, last_line, stalls, named, line
        if t != last_block:
            last_block = t
            now = time.monotonic()
            if performer is not None:
                said = [e for e in performer.transcript
                        if e[0] == "stall"]
                for _, beat in said[stalls:]:
                    say(f"score: stalling at beat {beat:.1f} — the "
                        f"render is waiting on the stream")
                stalls = len(said)
                if (not named and stalls and not performer.history
                        and now - begun > 10.0):
                    named = True
                    say("score: ten seconds of forcing and nothing has "
                        "arrived — this walk may never produce; a "
                        "clipped `cycle` with no notes in it (a silent "
                        "section spelled `long n (cycle rests)`) does "
                        "exactly this")
            if tty and now - last_line >= 1.0:
                last_line = now
                err.write(f"\r{t / rate:.1f}s / {samples / rate:.1f}s")
                err.flush()
                line = True
        return control(node, t)

    def finish():
        if line:
            err.write("\r\x1b[K")
            err.flush()

    wrapped.finish = finish
    return wrapped


def dynamic(synth: str, piece: str = "", *, rate: int, block: int,
            policy="oldest", horizon: float = 4.0, seed: int = 0,
            patience: float | None = None, tick: int = 0, reader=None):
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
    from .audiodynamic import LazyPerformer, LiveStream
    from .audioscore import stream_root
    from .audiovoices import banks_of, channels_of

    from .transcript import Transcript

    both = synth + "\n" + piece
    tempo, state, root, by_tag = stream_root(synth, piece, rate, seed,
                                             tick, live=True)
    allocators = {b.name: Allocator(channels_of(both, b), policy=policy)
                  for b in banks_of(both)}
    # Crust forces the score when the piece can cross (~10× on layouts
    # and draws — a take of an endless piece renders sooner); the
    # reference machine remains the fallback and the meaning.
    from .crust import live_native

    stream = (live_native(state, by_tag, seed, tick)
              or LiveStream(state, root, by_tag, patience=patience))
    from .audioscore import shape_plan

    shapes = shape_plan(state, seed, both)
    record = Transcript(source_sha=Transcript.sha_of(both), rate=rate,
                        block=block, seed=seed)
    performer = LazyPerformer(stream, tempo, rate, allocators, block=block,
                              horizon=horizon, record=record, origin=tick,
                              reader=reader, shapes=shapes)
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


def render_wav(graph, path: str, seconds: float, rate: int, block: int,
               control) -> int:
    """Render a performance to a `.wav` — written as it renders.

    Block by block onto disk, because the piece that is being rendered
    does not fit anywhere else: twenty minutes of stereo held whole as
    Python floats was half the machine's memory, and the writer only
    ever needed one block of it.  `wave` patches the frame count into
    the header on close, which is what makes incremental writing free.
    The interpreter fallback still renders to a list first — a machine
    with no `clang` measures that render in days, not gigabytes.
    """
    import shutil
    import struct
    import tempfile
    import wave

    from .audio import safe_sample

    total = int(seconds * rate)
    channels = graph.channels()
    with wave.open(path, "wb") as f:
        f.setnchannels(channels)
        f.setsampwidth(2)
        f.setframerate(rate)
        if shutil.which("clang") is not None:
            from .audiollvm import native_blocks

            written = 0
            with tempfile.TemporaryDirectory() as d:
                for got in native_blocks(graph, d, total, block=block,
                                         control=control):
                    data = bytearray()
                    for x in got:
                        data += struct.pack("<h",
                                            int(safe_sample(x) * 32767))
                    f.writeframes(bytes(data))
                    written += len(got) // channels
            return written
        from .audioengine import run

        samples = graph.frames(run(graph, total, block=block,
                                   control=control))
        data = bytearray()
        for frame in samples:
            for x in (frame if channels > 1 else (frame,)):
                data += struct.pack("<h", int(safe_sample(x) * 32767))
        f.writeframes(bytes(data))
        return len(samples)


# ── CLI ─────────────────────────────────────────────────────────────────────


def _oracle_main(args) -> int:
    """`gestate.audio`'s retired CLI, living here now: the interpreter
    render — the reference, the goldens' own machine.  `args.synth` is
    the file; a `piece` argument makes no sense at the oracle (it
    renders one program) and is refused rather than ignored."""
    import sys
    from pathlib import Path

    from .audio import (DEFAULT_RATE, GOLDEN_SUFFIX, render_frames,
                        write, write_golden)

    if args.piece:
        print("gestate: --oracle renders one program; give it one file",
              file=sys.stderr)
        return 1

    def tick(fraction):
        print(f"\r  rendering {fraction:>5.0%}", end="", file=sys.stderr)

    try:
        if args.golden:
            n, rate = write_golden(args.synth, args.seconds, args.rate,
                                   tick, control_every=args.control_every)
            out = Path(args.synth).with_suffix(GOLDEN_SUFFIX)
            print(f"\r{out}: {n} samples at {rate} Hz")
            return 0

        source = Path(args.synth).read_text()
        seconds = 2.0 if args.seconds is None else args.seconds
        rate = DEFAULT_RATE if args.rate is None else args.rate
        if args.peak:
            frames = render_frames(source, seconds, rate)
            channels = len(frames[0]) if frames else 1
            peaks = [max((abs(f[c]) for f in frames), default=0.0)
                     for c in range(channels)]
            # Per channel, because a stereo synth with one silent side
            # is exactly the mistake a single overall peak would hide.
            shown = ", ".join(f"{p:.3f}" for p in peaks)
            print(f"{len(frames)} frames at {rate} Hz, "
                  f"{channels} channel{'s' if channels != 1 else ''}, "
                  f"peak {shown}")
            return 0
        out = args.output or str(Path(args.synth).with_suffix(".wav").name)
        n, peak = write(source, out, seconds, rate, tick)
        print(f"\r{out}: {n} frames at {rate} Hz, "
              f"{n / rate:.2f}s, peak {peak:.3f}")
        return 0
    except Exception as exc:                     # noqa: BLE001 — CLI boundary
        from .audiospans import in_source

        try:
            text = in_source(str(exc), Path(args.synth).read_text(),
                             args.synth)
        except Exception:                        # noqa: BLE001
            text = str(exc)
        print(f"\ngestate: {type(exc).__name__}: {text}", file=sys.stderr)
        return 1


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
    # `None`, not a number: the oracle's flags need to know whether a
    # rate was *said* — a golden re-rendered supplies its own — and
    # the player and the oracle default differently.
    ap.add_argument("--rate", type=int, default=None)
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
    # ── The oracle's flags, folded in from `gestate.audio`'s retired
    # CLI: one door for every rendering, whichever machine answers.
    # The oracle is the interpreter — slow, pure Python, the reference
    # the goldens hold three engines against — and it stays reachable
    # from the same command that plays.
    ap.add_argument("--oracle", action="store_true",
                    help="render through the interpreter — the "
                         "reference, pure Python, no clang — instead "
                         "of the engine")
    ap.add_argument("--golden", action="store_true",
                    help="write the golden buffer beside the source; "
                         "an existing one supplies the rate, duration "
                         "and control schedule it was made at")
    ap.add_argument("--peak", action="store_true",
                    help="report the oracle's peak sample per channel "
                         "and write nothing")
    ap.add_argument("--control-every", type=int, default=None,
                    help="tick the oracle's control clock every N "
                         "samples — the block size a control-rate "
                         "golden is rendered at")
    args = ap.parse_args(argv)

    if args.golden or args.peak or args.oracle:
        return _oracle_main(args)
    if args.rate is None:
        args.rate = DEFAULT_RATE

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

            # **Named, not bare**: a bare allocator becomes the anonymous
            # bank `""`, and then `holds.<bank>` looks for a name the
            # note port never records — the arpeggiator that cannot hear
            # its own player.
            notes = Notes({args.midi_bank:
                           allocator_for(synth, args.midi_bank,
                                         args.policy)})
            # The program's own `FromMIDI` instances, exactly as the
            # editor wires them: without this, a computed payload
            # (`Tone (toFloat v / 127.0) n`) would be replaced by the
            # raw `(key, velocity)` default — in whatever order the
            # record's fields happen to sit.
            from .audiomidi import FromMidi
            from .audioscore import assemble_performance
            from .pipeline import compile as _compile_program

            from .audio import assemble as _assemble

            assembled = (assemble_performance(synth, piece, args.rate)
                         if has_score(synth + "\n" + piece)
                         else _assemble(synth, args.rate))
            fm = FromMidi(_compile_program(assembled), [args.midi_bank])
            if fm.banks:
                def _accepts(bank, message):
                    return fm.payload_for(bank, getattr(message, "channel", 0),
                                          message.note, message.velocity)

                notes.accepts = _accepts
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
            control = _progress(control, performer,
                                int((seconds or 2.0) * args.rate),
                                args.rate)
            n = render_wav(graph, args.output, seconds or 2.0,
                           args.rate, args.block, control)
            getattr(control, "finish", lambda: None)()
            print(f"{args.output}: {n} samples at {args.rate} Hz")
            if performer is not None and args.transcript is None:
                # The take's confessions, said even when nobody asked
                # for the log — a render that dropped notes or stalled
                # is not the render the score describes, and finding
                # that out by listening costs twenty minutes.
                said = _confessed(performer.record.confessions())
                if said:
                    print("score" + said + "; --transcript writes the "
                          "log", file=sys.stderr)
            if args.transcript is not None:
                if performer is None:
                    print("gestate: only a dynamic performance keeps a "
                          "transcript; nothing was written", file=sys.stderr)
                else:
                    performer.record.save(args.transcript)
                    kept = len(performer.record.events)
                    # **What the performance owned up to**, named rather
                    # than counted: a stall, a dropped note and a dry
                    # thread all sound like silence, and only the log
                    # can say which silence was heard.
                    said = _confessed(performer.record.confessions())
                    print(f"{args.transcript}: seed {performer.record.seed},"
                          f" {kept} event(s)" + said, file=sys.stderr)
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
