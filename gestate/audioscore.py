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
#: The entries take the take's **seed** as an argument rather than baking
#: it into the text: entropy differs per take, and a seed in the assembly
#: would shatter every cache keyed on the source — `pipeline._analysed`,
#: the compiled object, the laid-out score.  The host applies the entry
#: to a number (`PushInt`/`Mkap`); `seedRoot` lets an author-declared
#: `seed` win over whatever the renderer supplied, which is the fixed-art
#: rule of `spec/dynamicscore.md` stage three.  A score with no `sown`
#: passes through `sowScore` unchanged whatever the number, so fixed art
#: stays fixed without asking.
_VOICE_ENTRY = ("scoreMain : Int -> (Int, List (Int, Int, Voice))\n"
                "scoreMain sd = (bpm, layVoices (sowScore (seedRoot sd) score))\n")

#: The same, for a piece whose tempo is an envelope rather than a number.
#:
#: A second entry rather than a wider one: a piece writes `bpm` *or*
#: `tempo`, so an entry naming both would demand a definition of whichever
#: the author did not write.
_TEMPO_ENTRY = ("scoreMain : Int -> (List Tempo, List (Int, Int, Voice))\n"
                "scoreMain sd = (tempo, layVoices (sowScore (seedRoot sd) score))\n")

#: The score again, as the stream a *dynamic* performance forces — beside
#: `scoreMain` rather than in place of it, in the one assembly, so the
#: eager and the unfolding readings cannot drift apart in anything
#: (`spec/dynamicscore.md`, stage two).  Evaluated by name and only by
#: the dynamic path; a baked performance never touches it.
_STREAM_ENTRY = ("streamMain : Int -> List (Int, Int, Voice)\n"
                 "streamMain sd = streamVoices (sowScore (seedRoot sd) score)\n")

#: The bar points, `(tick, mark)`, lazily — what a transport lists to
#: offer re-entry, and what a resume will name instead of unfolding
#: everything left of it (`spec/dynamicscore.md`, the span-and-mark
#: answer to the rebuild question).
_MARKS_ENTRY = ("marksMain : Int -> List (Int, String)\n"
                "marksMain sd = streamMarks (sowScore (seedRoot sd) score)\n")

#: The remainder from tick `t`, rebased to zero — the resume a rebuild
#: plays.  Sown *first*, cut second: the surviving subtrees keep the
#: seeds their positions always had, which is what makes a resumed take
#: the same take.
_RESUME_ENTRY = ("resumeMain : Int -> Int -> List (Int, Int, Voice)\n"
                 "resumeMain sd t = streamVoices (resumeAt t "
                 "(sowScore (seedRoot sd) score))\n")

#: The listening reading: a stream that can end in a question
#: (`music.ges`, `liveVoices`).  On a probe-free score it must sound
#: exactly `streamMain` — `test_probescore.py` holds the two equal —
#: so the dynamic path reads through this one always, and the flat
#: stream remains the bake's and the parity suite's.
_LIVE_ENTRY = ("liveMain : Int -> Int -> List Cue\n"
               "liveMain sd t = liveVoices (resumeAt t "
               "(sowScore (seedRoot sd) score))\n")

#: `seedRoot` — one line, chosen by whether the author declared a `seed`.
#: Their number is fixed art, replayable from the text alone; the
#: argument is the renderer's entropy, recorded by whoever supplied it.
_SEED_OWN = "seedRoot : Int -> Int\nseedRoot sd = seed\n"
_SEED_GIVEN = "seedRoot : Int -> Int\nseedRoot sd = sd\n"


#: The boxed stage-three surface, retired by ariadne
#: (`spec/ariadne.md`) — refused *as itself*, the retirement rule: a
#: stray old piece gets told what to write, not an unknown-name error.
_RETIRED = {
    "sown": "`sown (s => X)` is retired — write `do s <- draw; X`: the "
            "seed is a value now, and the content's time is its own "
            "(`long n` is the box, where a box is meant)",
    "probe": "`probe p f` is retired — write `do ks <- hear p; f ks`: "
             "no box, a four-beat answer takes four beats",
}


def _refuse_retired(authored: str) -> None:
    import re

    bare = re.sub(r"#[^\n]*", "", authored)
    for name, hint in _RETIRED.items():
        found = re.search(rf"\b{name}\b", bare)
        if found:
            line = bare[:found.start()].count("\n") + 1
            raise ScoreError(f"line {line}: {hint}")


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
def assemble_performance(synth: str, piece: str = "", rate: int = 22050,
                         clock_text: str | None = None) -> str:
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
    from .audio import _authored

    tail = _entry(rate) + "\n" + (
        _VOICE_ENTRY if _tempo_of(synth + "\n" + piece) == "bpm"
        else _TEMPO_ENTRY) + _STREAM_ENTRY + _MARKS_ENTRY + _RESUME_ENTRY + _LIVE_ENTRY + (
        _SEED_OWN if "seed" in _authored(synth + "\n" + piece)[1]
        else _SEED_GIVEN)
    # `beat` goes with the entry point rather than into `head`, because it
    # reads the author's own `bpm` or `tempo` and must come after their
    # file.  A plain `bpm` makes the beat clock linear; an envelope makes
    # it piecewise *quadratic*, since tempo is linear in time and beat is
    # its integral.  Both are `map`s the fragment accepts — the second only
    # because `envexpand` expands `beatOf` into a tree over the segment
    # boundaries — so a scored program has a `beat` either way.
    # `clock_text` overrides the derivation — a hosting DAW's transport
    # is the conductor where there is one (`spec/substrate.md`, the
    # context contract); the program's own `bpm`/`tempo` stay what they
    # are: how gestate-as-its-own-renderer answers the same name.
    if clock_text is not None:
        tail = clock_text + tail
    elif _tempo_of(synth + "\n" + piece) == "bpm":
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
    _refuse_retired(authored)
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


def perform_voices(synth: str, piece: str = "", rate: int = 22050,
                   seed: int = 0) -> tuple:
    """`(bpm, [(onset, offset, bank, payload)])` — a piece, in ticks.

    `bank` is the name from the `voices` declaration and `payload` a tuple
    of the author's own record's fields, so nothing downstream has to know
    what either means.

    `seed` reaches `sowScore` through the entry point.  A score with no
    `sown` lays out identically whatever it is — which is why a default
    of 0 changes nothing for fixed art — and a caller performing a chancy
    score is the one who chose the number, so recording it is theirs to
    do (`spec/dynamicscore.md`, provenance).
    """
    from .audiovoices import banks_of
    from .midi import _force, _int, _list
    from .pipeline import compile as _compile

    from .gmachine import (NCon, Mkap, PushGlobal, PushInt, Unwind, is_tuple,
                           run)

    # Refused here rather than hung here: laying out is a walk to the
    # score's end, and these names say there may not be one.
    unfolding = unfolding_names(synth + "\n" + piece)
    if unfolding:
        raise ScoreError(
            "this score unfolds — "
            + ", ".join(f"`{n}`" for n in unfolding)
            + " — so laying it out whole may never finish.  Perform it "
              "dynamically instead (`--dynamic` with `--seconds`, or "
              "`audiodynamic.LazyPerformer`); a score that does end plays "
              "the same either way")

    spelling = _tempo_of(synth + "\n" + piece)
    # The *same* text the graph was extracted from — `assemble_performance`
    # carries both entries — so the front end is answered from
    # `pipeline._analysed` rather than run again.  The score's reading is
    # `scoreMain`, evaluated by name the way `gui.Substrate._force` does.
    source = assemble_performance(synth, piece, rate)
    stored = _score_path(source, seed)
    if stored is not None and stored.exists():
        import pickle

        try:
            with open(stored, "rb") as f:
                return pickle.load(f)
        except Exception:                               # noqa: BLE001
            pass                        # a torn cache is only a slow one
    state = _compile(source)
    # The entry applied to the seed: `Mkap` takes the function from the
    # top, so the argument is pushed first.
    state._code = [PushInt(seed), PushGlobal("scoreMain"), Mkap(), Unwind()]
    state._pc = 0
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
    if stored is not None:
        import pickle

        try:
            stored.parent.mkdir(parents=True, exist_ok=True)
            tmp = stored.with_name(stored.name + ".tmp")
            with open(tmp, "wb") as f:
                pickle.dump((bpm, events), f,
                            protocol=pickle.HIGHEST_PROTOCOL)
            tmp.replace(stored)         # atomic — a reader sees whole files
        except Exception:                               # noqa: BLE001
            pass
    return bpm, events


#: The library's two declared-endless makers.  Everything else in
#: `music.ges` terminates on finite input; these two are endless *by
#: contract*, which is why naming one is already the answer.
_ENDLESS = ("cycle", "unfold")


def unfolding_names(source: str) -> list:
    """Why this score cannot be laid out whole — the names to blame, or `[]`.

    A layout is walked to its end before it plays, and a score with no
    end hangs that walk rather than failing it.  Whether a score *has*
    an end is not decidable, and is not what is decided here: the scan
    asks the weaker, safer question — can the bake be **trusted** to
    end?  No recursion reachable from `score` in the author's own text
    means yes: the language has no other loop, and the library's walks
    terminate on finite input.  A reachable `cycle` or `unfold` (endless
    by contract), or the author's own recursion (self or mutual), means
    the score is treated as *unfolding*.

    Conservative by design, and the price of a false positive is
    deliberately nothing but routing: a recursive score that does end
    plays through the dynamic path exactly what the bake would have
    baked (`test_lazyscore.py` holds the two equal), so being unsure
    costs correctness nothing — where guessing "finite" and being wrong
    costs a hang.
    """
    import dataclasses

    from .audio import _expansion_prelude
    from .prelude import _parsed
    from .syntax.ast import VSCDecl, VWord

    try:
        module = _parsed(source)
    except Exception:                                    # noqa: BLE001
        try:
            from .audiovoices import expand

            module = _parsed(expand(source, _expansion_prelude()))
        except Exception:                                # noqa: BLE001
            return []          # the real error is a parse error, told elsewhere

    defs = {item.name: item for item in module.items
            if isinstance(item, VSCDecl)}

    def words_of(node, out):
        if isinstance(node, VWord):
            out.add(node.value)
        if dataclasses.is_dataclass(node):
            for f in dataclasses.fields(node):
                words_of(getattr(node, f.name), out)
        elif isinstance(node, (list, tuple)):
            for item in node:
                words_of(item, out)

    mentions = {}

    def mentioned(name):
        if name not in mentions:
            out: set = set()
            words_of(defs[name].equations, out)
            mentions[name] = out
        return mentions[name]

    blame, seen, stack = set(), set(), ["score"]
    while stack:
        name = stack.pop()
        if name in seen or name not in defs:
            continue
        seen.add(name)
        for word in mentioned(name):
            if word in _ENDLESS and word not in defs:
                blame.add(word)
            if word in defs:
                stack.append(word)

    for name in seen:
        frontier = {w for w in mentioned(name) if w in defs}
        visited: set = set()
        while frontier:
            n = frontier.pop()
            if n == name:
                blame.add(name)
                break
            if n in visited or n not in defs:
                continue
            visited.add(n)
            frontier |= {w for w in mentioned(n) if w in defs}
    return sorted(blame)


def assigned_banks(source: str) -> set:
    """Which banks the score assigns to — by parsed mention, not by text.

    A dynamic score has no baked schedule to enumerate channels from, so
    the *source* must answer — but scanned as declarations, reachable
    from `score`, never as text: a `voices.lead` in a comment is exactly
    the false positive `audioeditor.scored_banks`' docstring records.
    The expander has rewritten `voices.<bank>` to `voices<Bank>` by the
    time anything parses, so those are the words looked for.
    """
    import dataclasses

    from .audio import _expansion_prelude
    from .audiovoices import banks_of
    from .prelude import _parsed
    from .syntax.ast import VSCDecl, VWord

    try:
        module = _parsed(source)
    except Exception:                                    # noqa: BLE001
        try:
            from .audiovoices import expand

            module = _parsed(expand(source, _expansion_prelude()))
        except Exception:                                # noqa: BLE001
            return set()
    defs = {item.name: item for item in module.items
            if isinstance(item, VSCDecl)}
    spelling = {"voices" + b.name[0].upper() + b.name[1:]: b.name
                for b in banks_of(source)}

    def words_of(node, out):
        if isinstance(node, VWord):
            out.add(node.value)
        if dataclasses.is_dataclass(node):
            for f in dataclasses.fields(node):
                words_of(getattr(node, f.name), out)
        elif isinstance(node, (list, tuple)):
            for item in node:
                words_of(item, out)

    banks, seen, stack = set(), set(), ["score"]
    while stack:
        name = stack.pop()
        if name in seen or name not in defs:
            continue
        seen.add(name)
        out: set = set()
        words_of(defs[name].equations, out)
        for word in out:
            if word in spelling:
                banks.add(spelling[word])
            if word in defs:
                stack.append(word)
    return banks


def ports_of(source: str) -> dict:
    """`{port id: bank name}` — the identities `holds.<bank>` expands to.

    The expander numbers ports by bank declaration order, so this is the
    same enumeration read back; a reader answers `reader(port)` with the
    keys that bank's note port currently holds.
    """
    from .audiovoices import banks_of

    return {i: b.name for i, b in enumerate(banks_of(source))}


def stream_root(synth: str, piece: str = "", rate: int = 22050,
                seed: int = 0, tick: int = 0, live: bool = False) -> tuple:
    """`(tempo, state, root, by_tag)` — the unforced stream and its readers.

    The stage-two entry.  Nothing of the layout is forced here: `tempo`
    is `scoreMain`'s first component, which a lazy pair yields without
    touching its second, and `root` is `streamMain`'s own global,
    unevaluated — so an endless score returns at once, and every cons
    cell after this is paid for under `audiodynamic.ScoreStream`'s
    budget.  No pickle cache, deliberately: the eager cache memoises a
    *finished* walk, and this walk is finished only when the piece is.
    """
    from .audiovoices import banks_of
    from .midi import _force, _int
    from .pipeline import compile as _compile

    from .gmachine import Mkap, NAp, NNum, PushGlobal, PushInt, Unwind, \
        is_tuple, run

    spelling = _tempo_of(synth + "\n" + piece)
    source = assemble_performance(synth, piece, rate)
    state = _compile(source)
    state._code = [PushInt(seed), PushGlobal("scoreMain"), Mkap(), Unwind()]
    state._pc = 0
    state.stack, state.dump = [], []
    run(state)
    top = _force(state.stack[0], state)
    if not is_tuple(top, 2):
        raise ScoreError("internal: the entry point did not produce a pair")
    tempo = (_int(top.args[0], state) if spelling == "bpm"
             else _tempo_envelope(top.args[0], state))

    banks = banks_of(synth + "\n" + piece)
    by_tag = {}
    for bank in banks:
        name = bank.name[0].upper() + bank.name[1:] + "Note"
        info = state.cons.get(name)
        if info is not None:
            by_tag[info.tag] = bank.name
    if live:
        # The listening reading: resume-aware by its own second argument.
        root = NAp(NAp(state.globals["liveMain"], NNum(seed)), NNum(tick))
    elif tick > 0:
        # The remainder from `tick`, rebased to zero: `resumeAt` descends
        # by declared widths, so what stood left of the tick is skipped,
        # never forced — the rebuild answer (`spec/dynamicscore.md`).
        root = NAp(NAp(state.globals["resumeMain"], NNum(seed)), NNum(tick))
    else:
        root = NAp(state.globals["streamMain"], NNum(seed))
    return tempo, state, root, by_tag


def marks_of(synth: str, piece: str = "", rate: int = 22050,
             seed: int = 0, limit: int = 256) -> list:
    """**The piece's map** — `[(tick, name)]`, in beat order.

    What a transport offers as re-entry points, and what `section`
    writes: the names a piece gives its own parts, at the ticks they
    begin.  Lazy and therefore bounded by `limit`, because an endless
    piece has endless marks — asking for the first N of a `cycle` is
    the honest shape of the question.

    Read from the score itself rather than from the text, so a form
    that is *computed* — bound from payloads, chosen by a seed, even
    heard — maps exactly as a written one does.
    """
    from .gmachine import NAp, NCon, NNum, is_tuple
    from .midi import _force, _int, _list

    _tempo, state, _root, _tags = stream_root(synth, piece, rate, seed)
    cons = state.cons["Cons"].tag
    nil = state.cons["Nil"].tag
    # **The spine, cell by cell.**  Not `midi._list`, which walks to
    # `Nil` and therefore never returns on an endless form — the very
    # kind of piece whose map is most worth having.  A name is finite,
    # so its own characters may be forced whole.
    node = _force(NAp(state.globals["marksMain"], NNum(seed)), state)
    out: list = []
    while len(out) < limit:
        if not isinstance(node, NCon) or node.tag not in (cons, nil):
            raise ScoreError("internal: the marks stream is not a list")
        if node.tag == nil:
            break
        entry = _force(node.args[0], state)
        if not is_tuple(entry, 2):
            raise ScoreError("internal: a mark is not a (tick, name)")
        name = "".join(chr(_int(c, state))
                       for c in _list(entry.args[1], state))
        out.append((_int(entry.args[0], state), name))
        node = _force(node.args[1], state)
    return out


def tick_of_mark(marks: list, name: str, occurrence: int = 1):
    """Where a named part begins — `("verse", 2)` is the second verse.

    Occurrences are counted left to right, which is how a person reads
    a form and how a host should number them; `None` when the piece
    has no such part (or not that many of it), which a caller should
    say rather than guess at.
    """
    seen = 0
    for tick, mark in marks:
        if mark == name:
            seen += 1
            if seen == occurrence:
                return tick
    return None


#: Bump when what `perform_voices` returns changes shape — the stored
#: layout is keyed by `(schema, sha256(assembled source))`, and the source
#: hash covers the rate, which is written into the assembly's own
#: `sampleRate` line.
_SCORE_SCHEMA = 1


def _score_path(source: str, seed: int = 0):
    """Where this piece's laid-out score would be remembered, or `None`.

    A *cache* in the strict sense, like the stack front's and the compiled
    object's: the G-machine layout of a long piece is seconds of
    interpreter (five, for `quartet.ges`), it is a pure function of the
    assembled text — and, since stage three, of the seed — and reopening
    an unedited piece should not pay it twice.  `GESTATE_SCORE_CACHE=0`
    turns it off.
    """
    import hashlib
    import os
    from pathlib import Path

    if os.environ.get("GESTATE_SCORE_CACHE", "1") == "0":
        return None
    root = os.environ.get("XDG_CACHE_HOME") or (Path.home() / ".cache")
    sha = hashlib.sha256(f"{seed}\n{source}".encode()).hexdigest()[:32]
    return Path(root) / "gestate" / f"score-{_SCORE_SCHEMA}-{sha}.pickle"


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


def timed_events(events: list, bpm, rate: int) -> list:
    """A `layVoices` layout in the performance's one true order.

    `[(sample, order, key, bank, payload, is_off)]`, sorted by `(sample,
    releases-first)`: at one instant a release comes *first*, so a voice
    freed at the same sample can be taken by the note arriving there —
    which is what a legato line of one voice needs.

    Shared by the bake below and by `audiodynamic.Performer`, deliberately:
    when a note happens is decided *here and only here*, because two
    spellings of that decision is exactly where a note goes missing
    silently (`spec/dynamicscore.md`, the stage-one parity claim).

    `key` is the event's own index: a `Score` may hold the same payload
    twice and each is its own note, where MIDI's key doubles as an
    identity because a keyboard cannot press one key twice.
    """
    timed: list = []
    for i, (onset, offset, bank, payload) in enumerate(events):
        start = samples_of(onset, bpm, rate)
        end = samples_of(offset, bpm, rate)
        timed.append((start, 1, i, bank, payload, False))
        timed.append((max(end, start), 0, i, bank, payload, True))
    timed.sort(key=lambda e: (e[0], e[1]))
    return timed


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
    for at, _order, key, bank, payload, is_off in timed_events(events, bpm,
                                                               rate):
        allocator = allocators.get(bank)
        if allocator is None:
            raise ScoreError(
                f"this piece assigns notes to `{bank}` and no allocator was "
                f"given for it; there is "
                + (", ".join(f"`{b}`" for b in sorted(allocators)) or "none"))
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
