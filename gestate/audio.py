"""Render a gestate synth to a `.wav` — the reactive half, as sound.

The third backend on the same plan as `midi.py` and `gui.py`:

    prelude, prepended     `audio.ges`
    program supplies       `sound : Sig Float`, or a record of `Float`s
    pure core              `render(source, seconds)` → samples
    writes a file          `write(source, path)` — `wave`, from the stdlib

**One channel or several.**  `sound : Sig Float` is mono and is what almost
every synth is; `sound : Sig Stereo`, for a `Stereo := Stereo Float Float`,
is one channel per field in field order.  `render` is the mono view and
`render_frames` the general one — see `_channels_out` for why the count is
read off the type and never off the value.

Offline, and that is the design rather than a limitation.  A gestate signal
stepped per sample runs at a few thousand instants a second against 44,100
needed, and a faster interpreter would not close that: audio DSP wants flat
buffers and no allocation, which graph reduction is not.  SuperCollider
splits the language that *describes* an instrument from the engine that runs
it, and this is the describing half.  Rendering to a file needs no engine
and answers the question that decides whether the rest is worth building.

    python -m gestate.audio examples/audio/blip.ges -o blip.wav
    python -m gestate.audio examples/audio/blip.ges --seconds 1 --peak
    python -m gestate.audio examples/audio/blip.ges --golden
"""

from __future__ import annotations

import struct
import sys
import wave
from pathlib import Path

from .gmachine import NInd, NNum
from .pipeline import compile as _compile
from .reactive import init_program, react_instant

def library_text(name: str) -> str:
    """One library's source, read once — **the one copy everybody uses**.

    `internals.libraries_in_scope` decides whether `synth.ges` is in scope
    by asking whether its text appears in what `preludes` returned.  It
    used to read the file for that comparison while `preludes` answered
    from a constant captured at import, so the two could disagree — and
    when they disagree the library is judged "not in scope" and
    **enforcement silently switches off**, which is the worst way for a
    check to fail.

    They cannot disagree today for a batch compile, and they can for a
    long-running one: the editor holds this module for hours, and a
    `synth.ges` edited on disk underneath it is exactly the divergence.
    One reader, so the question has one answer.
    """
    return _LIBRARY_TEXT.setdefault(
        name, (Path(__file__).with_name(name)).read_text())


_LIBRARY_TEXT: dict = {}

#: `signal.ges` first: the vocabulary both reactive backends share.
_SIGNAL = library_text("signal.ges")

#: Then `audio.ges` — time, and the oscillator shapes — and then
#: `synth.ges`, which is built on both.  Order matters: `synth.ges` calls
#: `wrap`, `sineOf` and `lowpass`, and a definition must come after what it
#: names.
_AUDIO = (_SIGNAL + "\n"
          + library_text("audio.ges") + "\n"
          + library_text("synth.ges"))

#: `gui.ges` in front of the audio vocabulary, for a program that draws as
#: well as sounds — `spec/substrate.md` S1.
#:
#: **One numbering, and only when it is wanted.**  Both files declare
#: constructors, and a constructor's tag is its position, so a program with
#: a `sound` *and* a `scene` has to be compiled with one prelude stack or
#: its two halves are two different programs.  Conditional for the reason
#: `music.ges` is: three constructors and their compile time are not
#: something a synth that draws nothing should pay, which is the rule
#: `roadmap.md` states for the score prelude and this follows.
#:
#: Before `audio.ges` rather than after: nothing in `gui.ges` names
#: anything in it, and putting it first leaves the audio vocabulary's own
#: order — `audio.ges` then `synth.ges` — untouched.
_AUDIO_GUI = (_SIGNAL + "\n"
              + library_text("gui.ges") + "\n"
              + library_text("audio.ges") + "\n"
              + library_text("synth.ges"))


def has_scene(source: str) -> bool:
    """Does this program draw?

    `substrate : Sig Sub` is what to write.  A leftover `scene` counts too
    — **deliberately**, even though the canvas no longer draws one: it has
    to get `gui.ges` in front of it to reach `gui._drawn`, which refuses it
    by name.  Matching only `substrate` would compile it without the
    vocabulary and report `Unknown global 'scene'` from a prelude the
    author never wrote.

    Textual, and matching `audioperform.has_score` exactly: the answer
    decides *which* assembly to compile, so it cannot be had by compiling.
    """
    import re

    return re.search(r"^(substrate|scene)\s*[:=]", source, re.M) is not None


def has_sound(source: str) -> bool:
    """Does this program sound?"""
    import re

    return re.search(r"^sound\s*[:=]", source, re.M) is not None


def has_bpm(source: str) -> bool:
    """Does this program state a tempo?

    A *definition* at the start of a line, like `has_sound` and
    `has_scene`, and not a mention: prose does not begin a line with
    `bpm :`.  A substring search for the bare word would match this
    sentence.
    """
    import re

    return re.search(r"^bpm\s*[:=]", source, re.M) is not None


#: **What beat it is** — the piece's own clock, at audio rate.
#:
#: Generated rather than written in a library, for the `bpm` in it: a tempo
#: is the *program's*, and a synth that states none has no beat to answer
#: with.  `sampleRate` is supplied one step further out for the same
#: reason, and this sits beside it.
#:
#: **Wherever `bpm` is, and not only in a scored program.**  It used to be
#: added by `audioscore.assemble_performance` alone, so a synth locked to a
#: tempo but playing no notes — a drone on a grid, an arpeggiator, anything
#: that wants to move in time with a number the file states — was told
#: `Unknown global 'beat'` while `bpm` sat defined three lines above it.
#: The score was never what `beat` needed; `bpm` is.
BEAT = ("\nbeat : Sig Float\n"
        "beat = map (n => toFloat n * toFloat bpm / (60.0 * sampleRate))"
        " ticks\n")

#: The same clock under a `tempo` envelope, where it is piecewise
#: *quadratic* — tempo is linear in time and beat is its integral.
#:
#: `beatOf` walks a cons list and the audio fragment refuses that, so
#: `envexpand.py` rewrites this call into a balanced tree over the segment
#: boundaries with `a + b·t + c·t²` at each leaf.  Which is why the clock
#: is written against `elapsed` rather than `ticks`: seconds are what the
#: polynomial is in, and `tempo.envelope` — the same derivation the
#: *schedule* is built from — is what supplies its coefficients.
BEAT_ENVELOPE = ("\nbeat : Sig Float\n"
                 "beat = map (t => beatOf tempo t) elapsed\n")


def has_tempo(source: str) -> bool:
    """Does this program state its tempo as an **envelope**?

    By the declared *type*, not by the name.  `tempo` is an ordinary word
    and programs use it for ordinary things — `examples/audio/drums.ges`
    has had `tempo : Int` since long before envelopes existed, and matching
    the bare name handed it a beat clock built from `beatOf tempo`, which
    wants a list.  The failure was a type error deep inside a generated
    line the author never wrote.

    A program that writes the list without a signature gets no `beat`,
    which is the conservative way round: nothing is inferred from a name.
    """
    import re

    return re.search(r"^tempo\s*:\s*List\s+(Tempo|Envelope)\b",
                     source, re.M) is not None


def preludes(source: str) -> str:
    """The vocabulary this program is compiled against.

    One function, because every reader of a program has to agree about
    which one it is — the checker, the extractor, the oracle, `audiospans`
    and the canvas.  Two answers to this question is two numberings, and
    two numberings is a `Rect` in one half and a `Dot` in the other.

    Three cases, and the middle one is the whole point:

    * a `sound` alone — the audio vocabulary, as it always was;
    * a `sound` **and** a `substrate` — `gui.ges` in front of it, so both
      halves of one file are one program;
    * a `substrate` alone — `gui.ges` and no audio, which is what a GUI
      program has always been compiled with.
    """
    sounds, draws = has_sound(source), has_scene(source)
    if sounds and draws:
        return _AUDIO_GUI
    if draws:
        return _GUI_ONLY
    return _AUDIO


#: A program that only draws: no audio vocabulary, and none of its cost.
_GUI_ONLY = (_SIGNAL + "\n"
             + library_text("gui.ges"))

#: 22,050 is a compromise: high enough that a sawtooth is recognisably
#: itself, low enough that a second of sound is a few seconds of work.
DEFAULT_RATE = 22050


class AudioError(Exception):
    pass


def _entry(rate: int) -> str:
    """`sampleRate` is the renderer's business, so the renderer defines it.

    A synth reads it — directly, or through `seconds` — but never
    chooses it: the same program should render at any rate, and the rate is
    a property of the file being written.

    **`main` carries no signature, and that is what makes stereo possible.**
    It used to read `main : Sig Float`, which fixed the output at one
    channel in the one place a program could not argue with: a `sound : Sig
    Stereo` failed to unify against the *entry point* rather than against
    anything the author wrote.  Inference gives the same answer for every
    mono program and admits a frame type for the rest; what a `sound` may
    be is then checked by `_channels_out`, against the type the program's
    own declaration gave it and in terms of the record it named.
    """
    return (f"\nsampleRate : Float\nsampleRate = {float(rate)}\n"
            f"\nconstSig : a -> Sig a\n"
            f"constSig v = mapSig (n => v) ticks\n"
            f"\nmain = sound\n")


def _assembled(error, offset: int):
    """A `ParseError` from the author's text, moved into assembled lines.

    The message carries its position textually — `Pos(2,4)` — because that
    is how a token's `repr` reaches one, so the text is what has to move.
    `audiospans._POS` is the pattern that reads it back out; the two are a
    pair, and a change to either is a change to both.
    """
    import re

    from .syntax.ast import ParseError

    moved = re.sub(r"Pos\((\d+),\s*(\d+)\)",
                   lambda m: f"Pos({int(m.group(1)) + offset},{m.group(2)})",
                   str(error))
    pos = getattr(error, "pos", None)
    if pos is not None:
        pos = type(pos)(pos.line + offset, pos.col)
    return ParseError(moved, pos)


def assemble(source: str, rate: int = DEFAULT_RATE) -> str:
    """The whole program the renderer compiles: prelude, source, entry.

    Named because a second reader wants exactly this text and must not
    reconstruct it: `audiograph.py` checks the program that *runs*, so a
    fragment check of a slightly different assembly would be a check of a
    different program.

    `voices` banks are expanded here, for that same reason: the checker, the
    extractor, the oracle and `audiospans` all go through this function, so
    expanding here is what keeps them looking at one program.  The expansion
    blanks the declarations in place and appends, so the author's own lines
    do not move.

    **`internal` is enforced here, and it has to be here.**  The moment the
    preludes are concatenated on the front there are no longer any files in
    the program, and `svfSolve` in a synth is indistinguishable from
    `svfSolve` in `synth.ges` — so this is the last point at which the
    question can be asked at all (`gestate/internals.py`).  It is asked of
    the *expanded* source, which is what the author wrote with their banks
    written out, and the expansion is handed over rather than recomputed:
    it is a parse per bank and an editor calls this on every keystroke.
    """
    from .audiospans import prelude_lines
    from .audiovoices import expand
    from .internals import enforce
    from .prelude import shadow_libraries
    from .syntax.ast import ParseError

    prelude = preludes(source)
    # **Both of these parse the author's text on its own**, so a
    # `ParseError` out of either carries a position in the *author's*
    # coordinates — while everything downstream, `audiospans.in_source`
    # included, is entitled to assume assembled ones.  Subtracting a 2,394
    # line prelude from line 2 gave "prelude line 3": a mistake in the file
    # you are looking at, reported as being in a library you are not, on a
    # line that is not the one you typed.  Shifted here so that there is
    # one coordinate system by the time anybody else sees it.
    try:
        program = expand(source, prelude)
        enforce(source, text=program)
    except ParseError as caught:
        raise _assembled(caught, prelude_lines(source)) from None
    # **A program's own name wins**, which is the rule `prelude.ges` has
    # always had and the audio libraries did not: they are concatenated as
    # text here rather than merged as a module, so nothing was renaming
    # them out of the way and a composition with a `chorus` in it simply
    # would not compile.  See `prelude.shadow_libraries`.
    #
    # After `enforce` and after `preludes`, both deliberately.  `internal`
    # is asked of the author's own lines, which this does not touch, and
    # `internals.libraries_in_scope` compares against what `preludes`
    # returns — an unrenamed copy, which is what that comparison needs.
    # `beat` after the author's file, because it reads the author's `bpm`.
    # A program that states no tempo gets none and pays nothing for it.
    clock = (BEAT if has_bpm(source)
             else BEAT_ENVELOPE if has_tempo(source) else "")
    return (shadow_libraries(prelude, program) + "\n" + program + "\n"
            + clock + _entry(rate))


def _signal(state):
    """The `NSig` cell `main` evaluated to.

    Held by reference: a signal *is* the cell, and time advancing overwrites
    it in place, so one reference stays current for the whole render.
    """
    from .gmachine import NSig

    sig = state.stack[0] if state.stack else None
    while isinstance(sig, NInd):
        sig = sig.target
    if not isinstance(sig, NSig):
        raise AudioError(
            "the program's `sound` did not evaluate to a signal "
            f"(got {type(sig).__name__})")
    return sig


#: The clock `audio.ges` declares, and the one the renderer advances once
#: per sample.  Any other channel a program declares is control rate.
AUDIO_CLOCK = "clock"


def _channels(state, reactive) -> tuple[int, list[int]]:
    """`(audio, control…)` — the audio clock by **name**, not by id.

    `min(reactive.chans)` was wrong and had never been wrong in practice.
    Channel ids are handed out in *evaluation* order (`fixme.md` F90), so a
    program declaring its own channel can perfectly well take id 0 and leave
    the audio clock as 1 — at which point the renderer advances the user's
    channel every sample and never ticks the clock at all.  No example did
    that, so nothing caught it; two clocks make it reachable.

    Resolved by dereferencing the `clock` global to its `NChan`, which is
    exact.  The old behaviour is kept as a fallback for a program that
    somehow has channels but no `clock`.
    """
    from .gmachine import NChan

    node = state.globals.get(AUDIO_CLOCK)
    while isinstance(node, NInd):
        node = node.target
    if isinstance(node, NChan) and node.chan_id in reactive.chans:
        audio = node.chan_id
    else:
        audio = min(reactive.chans)
    return audio, sorted(c for c in reactive.chans if c != audio)


def _channel_names(state, reactive) -> dict:
    """`{channel name: id}`, for every `Chan` global the program declared.

    By name for the reason `_channels` gives at length: an id is handed out
    in evaluation order and is not a fact about the program.  A schedule is
    written against names, so this is what turns it into arrivals.
    """
    from .gmachine import NChan

    out = {}
    for name, node in state.globals.items():
        while isinstance(node, NInd):
            node = node.target
        if isinstance(node, NChan) and node.chan_id in reactive.chans:
            out[name] = node.chan_id
    return out


def _channels_out(state) -> int | None:
    """How many channels `sound` carries — from its **type**, not its value.

    The type, because the G-machine represents an `Int` and a `Float` with
    the same `NNum`: a `Frame := Frame Float Int` would otherwise be read as
    two channels and the second would be played as whatever that integer
    happened to be.  Nothing about the *value* can tell the two apart, so
    nothing about the value is asked.

    `None` when the program was compiled without types, in which case the
    shape of the first value decides and this hole is open again — no
    renderer path does that today, and `_frame` is what would notice.
    """
    from .types import TApp, TCon, tuple_parts

    declared = getattr(state, "result_type", None)
    if not isinstance(declared, TApp) or declared.fn != TCon("Sig"):
        return None
    payload = declared.arg
    if payload == TCon("Float"):
        return 1

    # A tuple is a record whose name nobody wrote, and it reaches the same
    # tagged `NCon` — so `Sig (Float, Float)` is two channels for the same
    # reason `Sig Stereo` is, and neither needs the other's spelling.
    parts = tuple_parts(payload)
    if parts is not None:
        bad = [i for i, p in enumerate(parts) if p != TCon("Float")]
        if bad:
            raise AudioError(
                "an output frame's components must all be `Float`, and "
                + ", ".join(f"component {i} is a `{parts[i]}`" for i in bad))
        return len(parts)

    if not isinstance(payload, TCon):
        raise AudioError(
            f"`sound` is a `Sig {payload}`, and a signal's payload must be "
            "`Float` for one channel or a record of `Float`s for more")

    cons = [c for c in state.cons.values() if _result_con(c.type_) == payload]
    if len(cons) != 1:
        raise AudioError(
            f"`{payload}` has {len(cons)} constructors, so it cannot be an "
            "output frame — a frame type is one constructor whose fields "
            "are all `Float`")
    con = cons[0]
    fields = _arg_types(con.type_)
    bad = [i for i, f in enumerate(fields) if f != TCon("Float")]
    if bad or not fields:
        which = ", ".join(f"field {i} is a `{fields[i]}`" for i in bad) \
            or "it has no fields"
        raise AudioError(
            f"`{con.name}` cannot be an output frame: {which}.  A "
            "multi-channel `sound` is a signal of a record of `Float`s, one "
            "field per channel")
    return len(fields)


def _arg_types(t) -> list:
    """The argument types of a constructor's type, left to right."""
    from .types import TFun

    out = []
    while isinstance(t, TFun):
        out.append(t.arg)
        t = t.ret
    return out


def _result_con(t):
    from .types import TFun

    while isinstance(t, TFun):
        t = t.ret
    return t


def _whnf(node):
    while isinstance(node, NInd):
        if node.target is None:
            raise AudioError("null indirection while reading a sample")
        node = node.target
    return node


def _frame(node, state=None) -> tuple[float, ...]:
    """One instant's output: `(x,)` if mono, `(l, r, …)` if a frame type.

    The one place the renderer decides how many channels a program has, and
    it decides it from the *value* rather than from a declared type.  A
    `Float` is one channel; a constructor whose fields are all `Float` is
    one channel per field, in field order — so `Stereo := Stereo Float
    Float` is left then right because that is how it is written.

    A **record and not a tuple**, and the reason is `fixme.md` F95: the
    G-machine gives `NTuple` no tag word, and every flat value the audio IR
    lays out is a tagged `NCon`, so `Sig (Float, Float)` is a thing the
    fragment checker admits and the extractor cannot place.  Accepting one
    here would make the offline oracle disagree with the engine it is the
    oracle *for*, which is worse than not accepting it.
    """
    node = _whnf(node)
    if isinstance(node, NNum):
        return (float(node.n),)
    from .gmachine import NCon, _force

    if isinstance(node, NCon) and node.args:
        # **Forced, not merely dereferenced.**  A constructor is built
        # lazily, so `Stereo (x * cos a) (x * sin a)` reaches here with two
        # `NAp` thunks in it — following indirections finds thunks, and
        # evaluating them is what turns them into samples.  The signal cell
        # itself is already in WHNF because the driver read it; its
        # *fields* are only whatever the program has demanded, which for an
        # output frame is nothing at all.
        fields = [_whnf(_force(a, state) if state is not None else a)
                  for a in node.args]
        if all(isinstance(f, NNum) for f in fields):
            return tuple(float(f.n) for f in fields)
        bad = next(i for i, f in enumerate(fields) if not isinstance(f, NNum))
        raise AudioError(
            f"a frame's fields must all be numbers, and field {bad} is a "
            f"{type(fields[bad]).__name__} — a multi-channel `sound` is a "
            "signal of a record of `Float`s and nothing else")
    raise AudioError(
        f"a sample must be a number, or a record of numbers for more than "
        f"one channel, got {type(node).__name__}")


def _sample(node, state=None) -> float:
    frame = _frame(node, state)
    if len(frame) != 1:
        raise AudioError(
            f"this program's `sound` carries {len(frame)} channels; "
            "`render` is the mono view of the renderer, so read it with "
            "`render_frames` instead")
    return frame[0]


def render(source: str, seconds: float = 1.0, rate: int = DEFAULT_RATE,
           progress=None, control_every: int | None = None,
           schedule=None) -> list[float]:
    """The samples the program produces, one per instant.

    Pure: no file, no audio device.  `progress`, if given, is called with
    the fraction done — the CLI uses it, because a second of sound is a few
    seconds of work and silence is indistinguishable from a hang.

    `control_every`, if given, also advances every **other** channel once
    every that many samples, which is what makes a control-rate clock
    observable offline at all.

    `schedule`, if given, says *what* those channels carry — an
    `audioschedule.Schedule`, keyed by channel name.  Without one every
    control channel is fed the instant number, which is enough to show that
    a control clock ticks and useless for anything with a shape, such as a
    note.  A channel the schedule says nothing about yet does not tick at
    all, so it keeps the value its `:::` gave it.

    **It is the engine's semantics now.**  A block boundary is *one* instant
    in which both clocks arrived, which is what `react_instant` runs and
    what `sync` reports as `SyncBoth`.  Feeding the two channels to `react`
    instead would be two instants, and everything downstream of the control
    clock would take an extra step that produces no sample — invisible for
    maps and zips, and a doubled accumulation for a `scan`.  That was open
    question 3 in `spec/liveaudio.md`; the driver answers it now.
    """
    if seconds <= 0:
        return []
    return render_assembled(assemble(source, rate), seconds, rate,
                            progress, control_every, schedule)


def safe_sample(x: float) -> float:
    """One sample, bounded and finite — **the last thing before a speaker.**

    Two failures, and the second is the one worth the function.

    *Over-range.* A sample above 1.0 is not loud, it is *wrong*: the
    conversion to 16-bit is a multiply and a truncation, and 1.2 does not
    clip there, it wraps to a large negative.  A 20% overshoot becomes a
    full-scale square wave.  So it is clamped.

    *NaN.* This is the subtle one.  `min`/`max` — Python's here, IEEE
    `minNum`/`maxNum` in the generated code — return the operand that is
    *not* NaN, so a naive clamp does not reject a NaN, it passes it
    through as the bound: measured, `max(-1.0, min(1.0, nan))` is **1.0**.
    One divide by zero anywhere in a synth therefore came out as sustained
    full-scale DC, which is the most damaging thing an audio path can
    produce — maximum power into a voice coil that is not moving, and so
    is not being cooled by moving.  NaN is silence instead, which is what
    a broken sample is worth.

    `x != x` is true only for NaN.  Infinities need no special case: the
    clamp already takes them to ±1.
    """
    if x != x:
        return 0.0
    return max(-1.0, min(1.0, x))


def render_frames(source: str, seconds: float = 1.0, rate: int = DEFAULT_RATE,
                  progress=None, control_every: int | None = None,
                  schedule=None) -> list[tuple[float, ...]]:
    """`render`, without assuming one channel — one tuple per instant.

    The primitive the rest of the renderer is built on.  `render` is the
    mono view of it and stays the name almost everything uses, because a
    mono program is still what almost every program is; a `sound : Sig
    Stereo` has nothing to give a `list[float]` and is read here instead.
    """
    if seconds <= 0:
        return []
    return render_frames_assembled(assemble(source, rate), seconds, rate,
                                   progress, control_every, schedule)


def render_assembled(program: str, seconds: float = 1.0,
                     rate: int = DEFAULT_RATE, progress=None,
                     control_every: int | None = None,
                     schedule=None) -> list[float]:
    """`render`, for a program that has already been assembled.

    A *performance* is assembled differently — it carries `music.ges` and
    its piece, so `'` and `>>=` exist — and the oracle has to be able to
    read one, or a piece assigned to its own banks would be the first thing
    here with no bit-identical check behind it.
    """
    frames = render_frames_assembled(program, seconds, rate, progress,
                                     control_every, schedule)
    if frames and len(frames[0]) != 1:
        raise AudioError(
            f"this program's `sound` carries {len(frames[0])} channels; "
            "`render` is the mono view of the renderer, so read it with "
            "`render_frames` instead")
    return [f[0] for f in frames]


def render_frames_assembled(program: str, seconds: float = 1.0,
                            rate: int = DEFAULT_RATE, progress=None,
                            control_every: int | None = None,
                            schedule=None) -> list[tuple[float, ...]]:
    """`render_frames`, for a program that has already been assembled."""
    if seconds <= 0:
        return []
    state = _compile(program)
    reactive = init_program(state)
    sig = _signal(state)
    # Before a single instant is stepped: a frame type that is not a record
    # of `Float`s is a mistake about the *program*, and saying so after a
    # minute of rendering would be saying so at the wrong moment.
    declared = _channels_out(state)
    if not reactive.chans:
        raise AudioError(
            "the program's `sound` never reads `ticks`, so it has no clock "
            "and cannot advance — a synth is a fold over `ticks`")
    channel, controls = _channels(state, reactive)
    scheduled = None
    if schedule is not None:
        names = _channel_names(state, reactive)
        scheduled = {name: cid for name, cid in names.items()
                     if cid in controls}
        unknown = set(schedule.channels()) - set(scheduled)
        if unknown:
            raise AudioError(
                "the schedule names channels this program does not declare "
                "as control channels: " + ", ".join(sorted(unknown))
                + ".  It declares " + (", ".join(sorted(scheduled)) or "none"))

    total = int(seconds * rate)
    first = _frame(sig.value, state)
    if declared is not None and len(first) != declared:
        raise AudioError(
            f"`sound` is typed for {declared} channel(s) and its first "
            f"value has {len(first)}")
    out = [first]
    step = max(1, total // 100)
    for n in range(1, total):
        arrivals = [(channel, NNum(n))]
        if control_every and n % control_every == 0:
            # Simultaneous arrivals: `sync` sees `SyncBoth`, which is what a
            # block boundary is — both clocks tick, and in between only the
            # audio one does.
            if scheduled is None:
                arrivals += [(c, NNum(n)) for c in controls]
            else:
                arrivals += [(cid, NNum(v)) for cid, v
                             in schedule.arrivals_at(n, scheduled)]
        react_instant(reactive, arrivals)
        out.append(_frame(sig.value, state))
        if progress is not None and n % step == 0:
            progress(n / total)
    return out


# ── The file ────────────────────────────────────────────────────────────────


def write(source: str, path: str, seconds: float = 1.0,
          rate: int = DEFAULT_RATE, progress=None) -> tuple[int, float]:
    """Render and write a 16-bit WAV.  Returns `(frames, peak)`.

    The channel count is the program's, not an argument: a `sound : Sig
    Float` writes mono and a `sound : Sig Stereo` writes two interleaved
    channels, which is the layout WAV already wants.  `frames` is instants,
    so it stays the number of samples for a mono program and is what
    `getnframes()` reports for either.
    """
    frames = render_frames(source, seconds, rate, progress)
    channels = len(frames[0]) if frames else 1
    peak = max((abs(x) for f in frames for x in f), default=0.0)
    data = bytearray()
    for frame in frames:
        for x in frame:
            # Clamped rather than normalised: a synth that goes over 1.0
            # should sound like it did, not be quietly rescaled.  See
            # `safe_sample` for why the clamp is not written inline —
            # a NaN survives one of those.
            v = int(safe_sample(x) * 32767)
            data += struct.pack("<h", v)
    with wave.open(path, "wb") as f:
        f.setnchannels(channels)
        f.setsampwidth(2)
        f.setframerate(rate)
        f.writeframes(bytes(data))
    return len(frames), peak


# ── Golden buffers ──────────────────────────────────────────────────────────
#
# `spec/liveaudio.md` stage 7.0.  `render()` is the *oracle* the whole live
# audio plan is verified against — graph extraction, block rendering and
# generated code are each checked by rendering the same program both ways
# and comparing samples — so what the oracle says has to be written down.
#
# The committed `.wav` beside each example is the artifact you can listen
# to; it is 16-bit and short of what a bit-identical comparison needs.  A
# `.samples` file is the same render at full `float64`, and is small and
# slow-free enough to sit in the test suite.


#: Exact and readable both: `repr` of a float is the shortest text that
#: reads back as the same double, so a diff shows the sample that moved.
GOLDEN_SUFFIX = ".samples"


def libm_fingerprint() -> str:
    """A digest of what **this machine's libm** returns for the primitives.

    A golden asserts bit-exactness, which is the right standard for
    catching a changed evaluator and is only meaningful on one machine:
    `sin`, `cos`, `exp`, `log` are not correctly rounded, so two glibcs may
    differ in the last place and a buffer made on one will not reproduce on
    the other.  Measured rather than supposed — `pluck.ges`, the only
    golden built on `exp`, differed in **3 samples of 1200 by 2.22e-16**
    between glibc 2.39 and the machine of record.

    Not the glibc version string, which is a proxy for the thing that
    matters and wrong in both directions: two builds can report the same
    version and dispatch to different code paths, and two versions can
    agree to the last bit.  This asks the functions themselves.

    Taken from `MATH_FLOAT`, so a primitive added there is fingerprinted
    without anyone remembering to.  `sqrt` is correctly rounded by IEEE and
    contributes nothing; it costs nothing to include and would matter if
    that ever stopped being true.
    """
    import hashlib
    import math

    from .gmachine import MATH_FLOAT

    probes = (0.1, 0.5, 1.0, 2.0, 2.5, 3.141592653589793, 10.0, 100.0)
    parts = []
    for fn in sorted(MATH_FLOAT):
        f = getattr(math, fn)
        for x in probes:
            try:
                parts.append(f"{fn}({x!r})={f(x)!r}")
            except ValueError:
                parts.append(f"{fn}({x!r})=domain")
    return hashlib.sha256("\n".join(parts).encode()).hexdigest()[:12]


def golden_text(samples, *, name: str, rate: int,
                seconds: float, control_every: int | None = None) -> str:
    """The committed form of a rendered buffer.

    `control_every` is written only when the example has a control clock, so
    the two audio-rate goldens keep the header they were made with.  It is
    part of the settings for the same reason `rate` is: a control-rate
    buffer rendered on a different block schedule is a different buffer.

    `samples` is a list of floats or a list of frames, and a multi-channel
    buffer writes its channels space-separated on one line per instant —
    one line is one instant either way, so a diff still points at the moment
    something moved rather than at an offset into an interleaved stream.
    `channels` is written only when there is more than one, which leaves
    every mono golden byte-identical to what it was.
    """
    frames = [f if isinstance(f, tuple) else (f,) for f in samples]
    channels = len(frames[0]) if frames else 1
    head = [
        f"# gestate golden samples — {name}",
        "#",
        "# The oracle for spec/liveaudio.md stage 7.  Every later stage is",
        "# checked against these numbers rather than against a description",
        "# of them, so a change to the evaluator, to signal.ges or to the",
        "# example shows up here as a diff and has to be meant.",
        "#",
        f"# rate: {rate}",
        f"# seconds: {seconds!r}",
        f"# samples: {len(samples)}",
        # Which machine's transcendentals these numbers came out of — see
        # `libm_fingerprint`.  A golden with a different one that also
        # *differs* is skipped rather than failed, because on that machine
        # the exactness it asserts is not a claim anybody can check.
        f"# libm: {libm_fingerprint()}",
    ]
    if control_every is not None:
        head.append(f"# control_every: {control_every}")
    if channels != 1:
        head.append(f"# channels: {channels}")
    head += [
        "#",
        f"# regenerate: python -m gestate.audio {name} --golden",
        "",
    ]
    body = [" ".join(repr(x) for x in f) for f in frames]
    return "\n".join(head + body) + "\n"


def parse_golden(text: str) -> tuple[dict[str, str], list]:
    """`(header, samples)` — the settings the file was rendered at, and it.

    The settings live in the file rather than in the test, so re-rendering
    it cannot silently use a different rate than the numbers were made at.

    `samples` is a list of floats for a mono golden and a list of frame
    tuples for a multi-channel one, which is exactly what `render` and
    `render_frames` respectively hand back — so a caller compares a golden
    against the call that made it and does not have to know which it has.
    """
    header: dict[str, str] = {}
    samples: list = []
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        if line.startswith("#"):
            body = line.lstrip("#").strip()
            key, sep, value = body.partition(":")
            if sep and " " not in key:
                header[key] = value.strip()
            continue
        parts = line.split()
        samples.append(float(parts[0]) if len(parts) == 1
                       else tuple(float(p) for p in parts))
    return header, samples


def write_golden(path: str, seconds: float | None = None,
                 rate: int | None = None, progress=None,
                 control_every: int | None = None) -> tuple[int, int]:
    """Render `path` and write the `.samples` beside it.  `(samples, rate)`.

    With no rate, duration or control schedule given, an existing golden's
    own header decides them — so regenerating one reproduces the settings it
    was made at, and only the numbers can change.
    """
    source_path = Path(path)
    out = source_path.with_suffix(GOLDEN_SUFFIX)
    if out.exists():
        header, _ = parse_golden(out.read_text())
        if rate is None and "rate" in header:
            rate = int(header["rate"])
        if seconds is None and "seconds" in header:
            seconds = float(header["seconds"])
        if control_every is None and "control_every" in header:
            control_every = int(header["control_every"])
    rate = DEFAULT_RATE if rate is None else rate
    seconds = 1.0 if seconds is None else seconds

    samples = render_frames(source_path.read_text(), seconds, rate, progress,
                            control_every=control_every)
    out.write_text(golden_text(samples, name=path, rate=rate, seconds=seconds,
                               control_every=control_every))
    return len(samples), rate


# ── CLI ─────────────────────────────────────────────────────────────────────


def main(argv=None) -> int:
    import argparse

    ap = argparse.ArgumentParser(
        prog="python -m gestate.audio",
        description="Render a gestate synth program to a .wav file.")
    ap.add_argument("file")
    ap.add_argument("-o", "--output", default=None)
    ap.add_argument("--seconds", type=float, default=None)
    ap.add_argument("--rate", type=int, default=None)
    ap.add_argument("--peak", action="store_true",
                    help="report the peak sample and write nothing")
    ap.add_argument("--golden", action="store_true",
                    help=f"write the `{GOLDEN_SUFFIX}` buffer beside the "
                         "source; an existing one supplies the rate, "
                         "duration and control schedule it was made at")
    ap.add_argument("--control-every", type=int, default=None,
                    help="tick the control clock every N samples — the "
                         "block size a control-rate example is rendered at")
    args = ap.parse_args(argv)

    def tick(fraction):
        print(f"\r  rendering {fraction:>5.0%}", end="", file=sys.stderr)

    try:
        if args.golden:
            n, rate = write_golden(args.file, args.seconds, args.rate, tick,
                                   control_every=args.control_every)
            out = Path(args.file).with_suffix(GOLDEN_SUFFIX)
            print(f"\r{out}: {n} samples at {rate} Hz")
            return 0

        source = Path(args.file).read_text()
        seconds = 2.0 if args.seconds is None else args.seconds
        rate = DEFAULT_RATE if args.rate is None else args.rate
        if args.peak:
            frames = render_frames(source, seconds, rate)
            channels = len(frames[0]) if frames else 1
            peaks = [max((abs(f[c]) for f in frames), default=0.0)
                     for c in range(channels)]
            # Per channel, because a stereo synth with one silent side is
            # exactly the mistake a single overall peak would hide.
            shown = ", ".join(f"{p:.3f}" for p in peaks)
            print(f"{len(frames)} frames at {rate} Hz, "
                  f"{channels} channel{'s' if channels != 1 else ''}, "
                  f"peak {shown}")
            return 0
        out = args.output or str(Path(args.file).with_suffix(".wav").name)

        n, peak = write(source, out, seconds, rate, tick)
        # `rate`, not `args.rate`: the latter is `None` unless `--rate` was
        # given, so writing a `.wav` without one divided by `None`.
        print(f"\r{out}: {n} frames at {rate} Hz, "
              f"{n / rate:.2f}s, peak {peak:.3f}")
        return 0
    except Exception as exc:                     # noqa: BLE001 — CLI boundary
        # Line numbers moved back into the file the author wrote, for the
        # reason `audiospans.in_source` gives: every position a compiler
        # error carries counts from the top of the *assembled* program,
        # preludes and all, so an untranslated one names a line nobody has.
        from .audiospans import in_source

        try:
            text = in_source(str(exc), Path(args.file).read_text(), args.file)
        except Exception:                        # noqa: BLE001
            text = str(exc)
        print(f"\ngestate: {type(exc).__name__}: {text}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
