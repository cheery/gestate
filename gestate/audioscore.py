"""Play a `Score` through gestate instruments instead of out of a MIDI port.

This is where the project's two backends finally meet.  `midi.py` takes a
music program's `score : [: Void :]` and writes a Standard MIDI File, which
hands the sound to somebody else's synthesiser.  Here the same layout drives
a `voices` bank compiled by the audio backend — so a piece written in
gestate is *performed* by instruments written in gestate.

    bpm, events = midi.perform(music_source)
    schedule = schedule_of(events, bpm, rate, banks)

`midi.perform` gives `(onset, offset, program, key, velocity)` in **ticks**,
96 to the beat (`spec/music.md`).  Two conversions and an allocation stand
between that and a sounding note:

* **ticks to samples** — `onset * 60 * rate / (bpm * 96)`.  Done in integer
  arithmetic, because the result is a sample index and a `Score` that lands
  a note between two samples has to land it on one of them predictably.
* **program to bank** — a `Score`'s instrument selects *which voice bank*,
  which is the only reading that keeps each voice's graph static.  A
  program with no bank of its own is refused by name rather than played on
  the wrong instrument.
* **note to voice** — `audioalloc.Allocator`, one per bank, so two banks
  steal voices independently.

The result is a `Schedule`, which means a `Score` performance is checkable:
render it through the interpreter and through the engine and compare, the
same as everything else in `spec/liveaudio.md`.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from functools import lru_cache

#: `spec/music.md`, and `midi.TICKS_PER_BEAT` — kept as one number by
#: importing it rather than repeating it.
from .audio import BEAT, BEAT_ENVELOPE, has_bpm, has_tempo
from .midi import TICKS_PER_BEAT


class ScoreError(Exception):
    pass


def samples_of(tick: int, tempo, rate: int) -> int:
    """A tick position as a sample index.

    `tempo` is either a plain `bpm` — the number a piece writes when its
    tempo never changes — or a `tempo.TempoEnvelope` for one that does.
    Both are accepted here rather than at every call site, because there
    are four of them and a piece's tempo is one thing.

    Integer arithmetic throughout **for a constant tempo**: a note is
    delivered *at* a sample, and rounding it differently in two places is
    how an offline render and a live one come to disagree about a rhythm.
    A varying tempo cannot stay in integers — its inverse is a square root
    — so it floors at the end instead, and `tempo.samples_of` is the one
    place that decides which of the two applies.  A piece with an
    unchanging tempo gets the integer path whichever way it wrote it.
    """
    from .tempo import TempoEnvelope, TempoError, constant

    try:
        env = tempo if isinstance(tempo, TempoEnvelope) else constant(tempo)
        return env.samples_of(tick, rate)
    except TempoError as caught:
        # One exception type reaches a score's reader, and it is this
        # module's: a bad tempo is a fault in the *piece*, whichever layer
        # noticed it.
        raise ScoreError(str(caught)) from None


@dataclass
class BankRef:
    """One bank, and which of a `Score`'s instruments it plays.

    `programs` are the MIDI program numbers this bank answers for, with
    `None` meaning percussion — the same encoding `midi.perform` produces,
    so nothing has to be translated on the way in.
    """
    name: str
    allocator: object
    programs: tuple = ()
    #: Answer for anything no other bank claims.
    default: bool = False
    #: `(program, key, velocity) -> payload tuple` — what this bank's
    #: voices are handed.  The default takes as many of `(key, velocity)`
    #: as the bank's record has fields, which is what a MIDI-shaped score
    #: means; a bank whose payload is its own thing supplies its own.
    payload: object = None

    def payload_of(self, program, key, velocity) -> tuple:
        if self.payload is not None:
            return tuple(self.payload(program, key, velocity))
        from .audioalloc import PAYLOAD

        want = self.allocator.fields - PAYLOAD
        return (key, velocity)[:want]


def _bank_for(program, banks: list) -> BankRef:
    for bank in banks:
        if program in bank.programs:
            return bank
    for bank in banks:
        if bank.default:
            return bank
    known = ", ".join(
        f"{b.name}({', '.join(str(p) for p in b.programs) or 'default'})"
        for b in banks)
    raise ScoreError(
        f"this score uses instrument {program!r} and no bank plays it; "
        f"there is {known}.  Give a bank that program, or mark one default")


def schedule_of(events: list, bpm: int, rate: int, banks: list, *,
                block: int, schedule=None):
    """Turn a layout into a `Schedule` that plays it.

    Events are processed **in time order**, which the allocator needs: it
    chooses a voice from what is sounding *now*, so feeding it a score by
    voice or by pitch would steal voices that had not started yet.
    `midi.perform` does not promise an order, so this sorts.

    Note-offs are interleaved with note-ons rather than done in a second
    pass, for the same reason — a voice has to be released before it can be
    reused, and a pass that did all the onsets first would need eight voices
    for a monophonic melody.
    """
    from .audioalloc import into_schedule
    from .audioschedule import Schedule

    if not banks:
        raise ScoreError("no banks to play a score through")
    schedule = Schedule() if schedule is None else schedule

    # `(sample, is_off, …)`: at one instant a release comes *first*, so a
    # voice freed at the same sample can be taken by the note arriving
    # there — which is what a legato line of one voice needs.
    timed: list = []
    for onset, offset, program, key, velocity in events:
        start = samples_of(onset, bpm, rate)
        end = samples_of(offset, bpm, rate)
        timed.append((start, 1, program, key, velocity, False))
        timed.append((max(end, start), 0, program, key, velocity, True))
    timed.sort(key=lambda e: (e[0], e[1]))

    for at, _order, program, key, velocity, is_off in timed:
        bank = _bank_for(program, banks)
        changes = (bank.allocator.note_off(key, at) if is_off
                   else bank.allocator.note_on(
                       key, bank.payload_of(program, key, velocity), at))
        into_schedule(schedule, changes, at, block)
    return schedule


def duration_of(events: list, bpm: int, rate: int) -> int:
    """How many samples the score lasts, to the last note-off.

    Not to the last *onset*: a piece whose final chord is held for two beats
    ends when it stops sounding, and rendering to the last onset would cut
    it off.  A release tail beyond that is the instrument's business.
    """
    return max((samples_of(offset, bpm, rate)
                for _on, offset, _p, _k, _v in events), default=0)


# ── The other half: a score assigned to gestate banks ───────────────────────
#
# `perform` above reads a MIDI-shaped layout — `Play (Midi …)` — and is what
# a piece written for somebody else's synthesiser produces.  What follows
# reads the *other* committed leaf, `Assigned Voice`, and is what a piece
# written for this program's own banks produces.
#
# The two are the same construct at different ages (`music.ges` says so at
# `Voice`), so this is the same walk with a different leaf: `layVoices`
# instead of `layout`, and a `Voice` opened by **tag** instead of a
# `Rendered`.  Opening it by tag is the whole of "the host opens it": the
# constructor's position is the bank, and its arguments are the payload.


#: The score's own entry point, beside `main` rather than in place of it.
#: Named so the *one* assembly carries both readings: `main = sound` for
#: the graph, `scoreMain` for the layout, and `perform_voices` evaluates
#: the second by name.  An author defining `scoreMain` collides with it and
#: is told so as a duplicate definition, exactly as defining `main` is
#: refused — the name is part of the assembly's contract.
_VOICE_ENTRY = ("scoreMain : (Int, List (Int, Int, Voice))\n"
                "scoreMain = (bpm, layVoices score)\n")

#: The same, for a piece whose tempo is an envelope rather than a number.
#:
#: A second entry rather than a wider one: a piece writes `bpm` *or*
#: `tempo`, so an entry naming both would demand a definition of whichever
#: the author did not write.
_TEMPO_ENTRY = ("scoreMain : (List Tempo, List (Int, Int, Voice))\n"
                "scoreMain = (tempo, layVoices score)\n")


def _tempo_of(source: str) -> str:
    """Which spelling this piece uses, refusing both at once.

    Two answers to how fast a piece goes is not a question this can
    settle, and letting one win silently is how a piece plays at a tempo
    nothing in the file states.

    Both questions go through `audio`'s parsed answers rather than being
    matched here: `tempo : [Envelope]` and `tempo : List Envelope` are one
    declaration written two ways, and only a parse sees that.
    """
    if has_tempo(source):
        if has_bpm(source):
            raise ScoreError(
                "this piece declares both a `bpm` and a `tempo`, and only "
                "one of them says how fast it goes.  A `bpm` is a `tempo` "
                "of one point — `tempo = [Step 0.0 120.0]` — so keep "
                "whichever says what you mean and drop the other")
        return "tempo"
    return "bpm"

#: **What time it is, in beats** — the piece's own clock, at audio rate.
#:
#: Generated here rather than written in `synth.ges`, and the reason is the
#: `bpm` in it: a tempo is a *piece's*, and a synth with no piece has none
#: to read.  `sampleRate` is supplied by the renderer for the same reason
#: one step further out, and this sits beside it.
#:
#: So `beat` is in scope exactly where `score` and `bpm` are — an
#: `audioperform` program — and an unscored synth that names it gets
#: `Unknown global 'beat'`, which is the truth: there is no tempo to
#: answer with.  `music.ges`'s ticks-per-beat resolution is
#: `ticksPerBeat`; this is the plain word, because "what beat are we on"
#: is the thing a synth wants to modulate against.
#: `audio.BEAT`, under the name this module already used.  **One copy**:
#: it is added here for a scored program and by `audio.assemble` for an
#: unscored one that states a `bpm`, and two spellings of one definition
#: is two clocks waiting to disagree.
_BEAT = BEAT

@lru_cache(maxsize=4)
def assemble_performance(synth: str, piece: str = "", rate: int = 22050) -> str:
    """The whole program a performance compiles: preludes, both sources, entries.

    Cached, because one editor start asks for this text four ways — the
    graph, the score, the `FromMIDI` interpreter and the sidebar — and
    the expansion, the `internal` check and the shadowing each parse.  It
    is a pure function of its arguments; a violation `enforce` raises is
    not cached, so a broken program is told so every time it asks.

    Two entry points, because a performance is read twice — and **both are
    in the one text**.  Extracting the *graph* wants `main = sound`, which
    is `audio._entry`; reading the *score* wants `scoreMain = (bpm,
    layVoices score)`, which is `_VOICE_ENTRY`, evaluated by name.  One
    assembly carrying both, so the two readings cannot drift apart in
    anything — and so they are one front end rather than two:
    `pipeline._analysed` is keyed by exact text, and a choice of last line
    was a whole second analysis of the same program, paid on every start
    and every Ctrl-S of the editor.

    **Synth and piece are one program**, and that is not a convenience.
    `voices.lead` names a bank lexically, and the payload type it carries
    has to agree with the bank's declared record — which the type checker
    can only say if both are in scope.  Compiling them apart would leave
    "does this piece fit this instrument" to be discovered as silence.

    `music.ges` is prepended here and *not* by `audio.assemble`, for the
    reason `roadmap.md` gives about stage 3: nine constructors and their
    compile time are not something a synth that plays no score should pay.

    **What goes in front of it is `audio.preludes`' answer, not `_AUDIO`.**
    A performance may also *draw* — a piece, an instrument and a fader in
    one file is the obvious thing to write once both exist — and this used
    to prepend the audio vocabulary alone, so its `substrate : Sig Sub`
    was checked against a program in which `Sub` had never been declared.
    The report was `KindError: Unknown type constructor: Sub` from
    whichever tool asked (`--holes`, `--fits`, the editor's sidebar), which
    names the symptom and not one word of the cause.  One function decides
    the vocabulary, as its docstring says, and this is now a caller of it.
    """
    from pathlib import Path

    from .audio import _entry, preludes
    from .audiovoices import expand
    from .internals import enforce
    from .prelude import shadow_libraries

    music = (Path(__file__).with_name("music.ges")).read_text()
    head = preludes(synth + "\n" + piece) + "\n" + music
    # `audio._entry`'s tail — `sampleRate`, `constSig`, `main = sound` —
    # and the score's own entry after it, under its own name.  Which
    # spelling of the tempo the piece uses decides the pair's first half.
    tail = _entry(rate) + "\n" + (
        _VOICE_ENTRY if _tempo_of(synth + "\n" + piece) == "bpm"
        else _TEMPO_ENTRY)
    # `beat` goes with the entry point rather than into `head`, because it
    # reads the author's own `bpm` or `tempo` and must come after their
    # file.  A plain `bpm` makes the beat clock linear; an envelope makes
    # it piecewise *quadratic*, since tempo is linear in time and beat is
    # its integral.  Both are `map`s the fragment accepts — the second only
    # because `envexpand` expands `beatOf` into a tree over the segment
    # boundaries — so a scored program has a `beat` either way.
    if _tempo_of(synth + "\n" + piece) == "bpm":
        tail = _BEAT + tail
    else:
        tail = BEAT_ENVELOPE + tail
    # `internal`, enforced on both halves at once — see `audio.assemble` for
    # why it cannot be asked any later than this.  A performance is one
    # program, so it is one check: a piece that names a filter's insides is
    # as much a violation as an instrument that does.
    authored = synth + "\n" + piece
    written = expand(authored, head)
    enforce(authored, text=written)
    # **A program's own name wins**, as in `audio.assemble` and for the same
    # reason — and this is the path a *composition* takes, so it is the one
    # where it matters most: `chorus` is an effect in `synth.ges` and a
    # section of a song in every piece ever written, and the collision that
    # found this was exactly that (`examples/audio/quartet.ges`).
    from .syntax import note_seam

    shadowed = shadow_libraries(head, written)
    out = shadowed + "\n" + written + "\n" + tail
    # Only an unshadowed head can stand alone — see `audio.assemble`.
    if shadowed is head:
        note_seam(out, len(shadowed) + 1)
    return out


def perform_voices(synth: str, piece: str = "", rate: int = 22050) -> tuple:
    """`(bpm, [(onset, offset, bank, payload)])` — a piece, in ticks.

    `bank` is the name from the `voices` declaration and `payload` a tuple
    of the author's own record's fields, so nothing downstream has to know
    what either means.
    """
    from .audiovoices import banks_of
    from .midi import _force, _int, _list
    from .pipeline import compile as _compile

    from .gmachine import NCon, PushGlobal, Unwind, is_tuple, run

    spelling = _tempo_of(synth + "\n" + piece)
    # The *same* text the graph was extracted from — `assemble_performance`
    # carries both entries — so the front end is answered from
    # `pipeline._analysed` rather than run again.  The score's reading is
    # `scoreMain`, evaluated by name the way `gui.Substrate._force` does.
    source = assemble_performance(synth, piece, rate)
    state = _compile(source)
    state._code, state._pc = [PushGlobal("scoreMain"), Unwind()], 0
    state.stack, state.dump = [], []
    run(state)
    top = _force(state.stack[0], state)
    if not is_tuple(top, 2):
        raise ScoreError("internal: the entry point did not produce a pair")
    bpm = (_int(top.args[0], state) if spelling == "bpm"
           else _tempo_envelope(top.args[0], state))

    # Tag → bank name, from the constructors the expander generated: one per
    # bank, named `<Bank>Note`, in declaration order.
    banks = banks_of(synth + "\n" + piece)
    by_tag = {}
    for bank in banks:
        name = bank.name[0].upper() + bank.name[1:] + "Note"
        info = state.cons.get(name)
        if info is not None:
            by_tag[info.tag] = bank.name

    events = []
    for cell in _list(top.args[1], state):
        node = _force(cell, state)
        if not is_tuple(node, 3):
            raise ScoreError("expected an (onset, offset, voice) triple")
        onset, offset, voice = node.args
        v = _force(voice, state)
        if not isinstance(v, NCon):
            raise ScoreError("expected a `Voice` value")
        bank = by_tag.get(v.tag)
        if bank is None:
            raise ScoreError(
                f"a note assigned to a voice bank this program does not "
                f"declare (constructor tag {v.tag})")
        payload = tuple(_read_flat(a, state) for a in v.args)
        events.append((_int(onset, state), _int(offset, state), bank, payload))
    return bpm, events


def _tempo_envelope(node, state):
    """A `List Tempo` from the heap, as a `tempo.TempoEnvelope`.

    Read by **tag**, the same way a `Voice` is: the constructor's position
    is which of `Step` and `Ramp` it is, and its arguments are the beat and
    the tempo there.  Nothing is matched by name, so the piece and the host
    agree because they were compiled together.
    """
    from .gmachine import NCon
    from .midi import _force, _list
    from .tempo import TempoError, envelope

    step = state.cons["Step"].tag
    ramp = state.cons["Ramp"].tag
    points = []
    for cell in _list(node, state):
        item = _force(cell, state)
        if not isinstance(item, NCon) or item.tag not in (step, ramp):
            raise ScoreError("expected a `Step` or a `Ramp` in `tempo`")
        at, value = (_force(a, state).n for a in item.args)
        points.append((float(at), item.tag == ramp, float(value)))
    try:
        return envelope(points)
    except TempoError as caught:
        raise ScoreError(str(caught)) from None


def _read_flat(node, state):
    """One payload value: a number, or a record's fields flattened.

    A payload is a record of scalars — that is what `audiovoices` requires,
    since every field becomes a control channel — so this is one level deep
    by construction, and a nested one would be refused long before here.
    """
    from .midi import _force

    from .gmachine import NCon, NNum

    node = _force(node, state)
    if isinstance(node, NNum):
        return node.n
    if isinstance(node, NCon):
        return tuple(_read_flat(a, state) for a in node.args)
    raise ScoreError(f"a payload field that is not a value: {type(node).__name__}")


def schedule_voices(events: list, bpm: int, rate: int, allocators: dict, *,
                    block: int, schedule=None):
    """A `layVoices` layout as a `Schedule`, one allocator per bank.

    The same shape as `schedule_of` and for the same reasons — time order,
    releases before onsets at a shared instant — but the bank is named by
    the note rather than looked up from a program number, because
    `voices.lead` already said which one.
    """
    from .audioalloc import into_schedule
    from .audioschedule import Schedule

    schedule = Schedule() if schedule is None else schedule
    timed: list = []
    for i, (onset, offset, bank, payload) in enumerate(events):
        start = samples_of(onset, bpm, rate)
        end = samples_of(offset, bpm, rate)
        timed.append((start, 1, i, bank, payload, False))
        timed.append((max(end, start), 0, i, bank, payload, True))
    timed.sort(key=lambda e: (e[0], e[1]))

    for at, _order, key, bank, payload, is_off in timed:
        allocator = allocators.get(bank)
        if allocator is None:
            raise ScoreError(
                f"this piece assigns notes to `{bank}` and no allocator was "
                f"given for it; there is "
                + (", ".join(f"`{b}`" for b in sorted(allocators)) or "none"))
        # Keyed by the event's own index: a `Score` may hold the same
        # payload twice and each is its own note, where MIDI's key doubles
        # as an identity because a keyboard cannot press one key twice.
        changes = (allocator.note_off(key, at) if is_off
                   else allocator.note_on(key, _flatten(payload), at))
        into_schedule(schedule, changes, at, block)
    return schedule


def _flatten(payload) -> tuple:
    """A payload's fields, one level down: `((60, 100),)` is `(60, 100)`."""
    out: list = []
    for value in payload:
        if isinstance(value, tuple):
            out.extend(_flatten(value))
        else:
            out.append(value)
    return tuple(out)


def duration_of_voices(events: list, bpm: int, rate: int) -> int:
    return max((samples_of(offset, bpm, rate)
                for _on, offset, _b, _p in events), default=0)
