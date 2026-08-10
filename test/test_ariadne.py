"""Ariadne's leaves — `spec/ariadne.md`, stages one to three.

The law everything here answers to: **route a constant through any
reactive construct and the algebra must not notice.**  `draw` and
`hear` are zero-width leaves of the score monad — no box, the
continuation's content carrying its own time — so a constant draw is
invisible to the bake, a constant answer equals its own splice to the
tick, and what follows a `hear` is placed after whatever the answer
chose, which is the one place time is decided by the thread rather
than the text.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))

from test_dynamicscore import BLOCK, RATE, SYNTH, _allocators

from gestate.audiodynamic import LazyPerformer, LiveStream
from gestate.audioscore import perform_voices, stream_root

BPM = "\nbpm : Int\nbpm = 120\n"


def _events(piece, seed=0):
    return perform_voices(SYNTH, piece + BPM, RATE, seed=seed)[1]


def _drive(piece, reading, beats=14, seed=3):
    tempo, state, root, by_tag = stream_root(SYNTH, piece + BPM, RATE,
                                             seed, 0, True)
    perf = LazyPerformer(LiveStream(state, root, by_tag), tempo, RATE,
                         _allocators(), block=BLOCK,
                         reader=lambda port, key=None: list(reading))
    for t in range(0, beats * 2000, BLOCK):
        perf.advance(t)
    return [(on, off, p) for on, off, _b, p in perf.history]


# ── draw ────────────────────────────────────────────────────────────────────


def test_a_constant_draw_is_invisible_to_the_algebra():
    """The constant law, chance half: a draw whose continuation ignores
    the seed changes nothing — events, ticks, durations — at any seed."""
    law = ("\nscore : [: Void :]\n"
           "score = ((do s <- draw; '(Custom 1.0 60) |* 2)"
           " ++ '(Custom 0.8 64)) >>= voices.lead\n")
    plain = law.replace("(do s <- draw; '(Custom 1.0 60) |* 2)",
                        "('(Custom 1.0 60) |* 2)")
    for seed in (0, 7, 123):
        assert _events(law, seed) == _events(plain, seed)


def test_a_used_draw_is_deterministic_by_position():
    """Same seed, same take; different seed, different take; two draws
    in one chain are two splits, not one value twice."""
    used = ("\nscore : [: Void :]\n"
            "score = (do a <- draw; b <- draw;"
            " '(Custom 1.0 (60 + below 12 a))"
            " ++ '(Custom 0.9 (60 + below 12 b))) >>= voices.lead\n")
    take5 = _events(used, seed=5)
    assert take5 == _events(used, seed=5)
    assert take5 != _events(used, seed=9)
    first, second = take5[0][3], take5[1][3]
    assert first != second, "two draws drew the same value — one split"


def test_a_draw_can_seed_a_walk():
    """The take-entropy gap (`dynscore-constraints.md` §D4), closed:
    `do s <- draw; unfold …` threads the take's own entropy into an
    endless walk — the spelling the old surface could not say."""
    from gestate.audiodynamic import ScoreStream

    piece = ("""
step : Int -> ([: Custom :], Int)
step s = case split s of
    (use, keep) -> ('(Custom 1.0 (60 + below 12 use)), keep)

score : [: Void :]
score = (do s <- draw; unfold s step) >>= voices.lead
""" + BPM)
    def take(seed):
        _t, state, root, by_tag = stream_root(SYNTH, piece, RATE, seed)
        return ScoreStream(state, root, by_tag).pull(8 * 96)

    assert take(4) == take(4), "a take must be replayable from its seed"
    assert take(4) != take(11), "the walk ignored the take's entropy"
    assert len(take(4)) == 8, "the walk did not stream"


# ── hear ────────────────────────────────────────────────────────────────────


HEARD = """
world : Chan (List Int)
world = chan

phraseOf : List Int -> [: Custom :]
phraseOf ks = case ks of
    Nil -> r
    k :: kt -> '(Custom 0.9 k) ++ phraseOf kt

score : [: Void :]
score = ((do ks <- hear world; phraseOf ks) ++ '(Custom 0.5 36)) >>= voices.lead
"""


def _spliced(keys):
    body = " ++ ".join([f"'(Custom 0.9 {k})" for k in keys] + ["r"])
    return (f"\nscore : [: Void :]\n"
            f"score = (({body}) ++ '(Custom 0.5 36)) >>= voices.lead\n")


def test_a_constant_answer_equals_its_own_splice():
    """The constant law, world half — and the deliberate break with the
    old surface: the answer's content carries its own time, so the coda
    lands after one beat, three beats, or the bare rest, moving with
    what the world said.  No box."""
    for world in ([60], [60, 64, 67], []):
        assert _drive(HEARD, world) == _drive(_spliced(world), world), world


def test_what_follows_moves_with_the_answer():
    """B7 restated, measured: the same written coda starts at three
    different ticks under three different worlds."""
    codas = {tuple(w): _drive(HEARD, list(w))[-1][0]
             for w in ((60,), (60, 64, 67), ())}
    assert codas[(60,)] == 2 * 96          # note + trailing rest
    assert codas[(60, 64, 67)] == 4 * 96
    assert codas[()] == 96                 # the rest alone


def test_the_crust_twin_speaks_hear_unchanged(tmp_path):
    """`Hear` reaches the performer as `CueAsk` — the same cue, the
    same wire — so the native stream listens without a line of new
    machinery.  Change for change against the reference."""
    import shutil

    import pytest

    if shutil.which("cargo") is None:
        pytest.skip("no cargo to build crust with")
    from gestate.crust import native_stream

    def drive_stream(make_perf):
        held = [60, 64]
        perf = make_perf(lambda port, key=None: list(held))
        out = []
        for t in range(0, 20_000, BLOCK):
            out += perf.advance(t)
        return out

    tempo, state, root, by_tag = stream_root(SYNTH, HEARD + BPM, RATE,
                                             6, 0, True)
    want = drive_stream(lambda r: LazyPerformer(
        LiveStream(state, root, by_tag), tempo, RATE, _allocators(),
        block=BLOCK, reader=r))
    tempo2, _native, stream, _tags = native_stream(SYNTH, HEARD + BPM,
                                                   RATE, seed=6,
                                                   live=True)
    got = drive_stream(lambda r: LazyPerformer(
        stream, tempo2, RATE, _allocators(), block=BLOCK, reader=r))
    assert got == want and want


def test_the_old_spellings_are_refused_by_name():
    """`sown` and `probe` are retired as themselves — a stray old piece
    gets told what to write (`spec/ariadne.md`, the retirement stage),
    never an unknown-name error."""
    import pytest

    from gestate.audioscore import ScoreError

    with pytest.raises(ScoreError, match="do s <- draw"):
        _events("\nscore : [: Void :]\n"
                "score = (sown (s => '(Custom 1.0 60))) >>= voices.lead\n")
    with pytest.raises(ScoreError, match="do ks <- hear"):
        _events("\nscore : [: Void :]\n"
                "score = (probe 0 (ks => r)) >>= voices.lead\n")


# ── The thread: readings keyed by position ──────────────────────────────────


LISTENER = """
world : Chan (List Int)
world = chan

phraseOf : List Int -> [: Custom :]
phraseOf ks = case ks of
    Nil -> r
    k :: kt -> '(Custom 0.9 k)

score : [: Void :]
score = cycle (long 1 (do ks <- hear world; phraseOf ks)) >>= voices.lead
"""

#: Three different worlds at three times, so a reader answering *in
#: order* cannot help but drift once a prefix is skipped.
SCRIPT = {0: [60], 4 * 2000: [64], 8 * 2000: [67]}


def _take(reader, beats=12, seed=8, tick=0):
    """One performance — from the top, or rejoined at `tick`."""
    from gestate.audioalloc import Allocator
    from gestate.audiovoices import banks_of, channels_of

    source = SYNTH + "\n" + LISTENER + BPM
    tempo, state, root, by_tag = stream_root(SYNTH, LISTENER + BPM, RATE,
                                             seed, tick, live=True)
    allocators = {b.name: Allocator(channels_of(source, b))
                  for b in banks_of(source)}
    from gestate.transcript import Transcript

    record = Transcript(source_sha=Transcript.sha_of(source), rate=RATE,
                        block=BLOCK, seed=seed)
    perf = LazyPerformer(LiveStream(state, root, by_tag), tempo, RATE,
                         allocators, block=BLOCK, origin=tick,
                         record=record, reader=reader)
    for t in range(tick * RATE // 96 // 20, beats * 2000, BLOCK):
        perf.advance(t)
    return perf


def _scripted():
    """A world that changes on the clock the script names."""
    now = {"keys": []}
    seen = {"t": 0}

    def reader(port, *rest):
        return list(now["keys"])

    def tick(t):
        for at, keys in SCRIPT.items():
            if t >= at:
                now["keys"] = keys
    return reader, tick


def test_a_rejoin_replays_the_thread_instead_of_asking_again():
    """The defect paths exist for (`roadmap.md`, ariadne's next stage):
    a rebuild mid-piece resumes **by descent** — the prefix is skipped,
    never walked — so a thread answering *in arrival order* hands the
    resumed walk answers meant for beats it never played.  Keyed by
    position, the thread answers correctly from anywhere in the piece.
    """
    from gestate.audioalloc import Allocator
    from gestate.audiovoices import banks_of, channels_of

    # The take, with the world on a script.
    reader, tick_world = _scripted()
    source = SYNTH + "\n" + LISTENER + BPM
    tempo, state, root, by_tag = stream_root(SYNTH, LISTENER + BPM, RATE,
                                             8, 0, live=True)
    allocators = {b.name: Allocator(channels_of(source, b))
                  for b in banks_of(source)}
    from gestate.transcript import Transcript

    record = Transcript(source_sha=Transcript.sha_of(source), rate=RATE,
                        block=BLOCK, seed=8)
    live = LazyPerformer(LiveStream(state, root, by_tag), tempo, RATE,
                         allocators, block=BLOCK, record=record,
                         reader=reader)
    for t in range(0, 12 * 2000, BLOCK):
        tick_world(t)
        live.advance(t)
    assert live.history, "the take was silent — the test is empty"

    # Rejoin at beat 6 with the thread as the only world.
    tickpos = 6 * 96
    want = [e for e in live.history if e[0] >= tickpos]
    assert want, "nothing to rejoin into"

    tempo2, state2, root2, tags2 = stream_root(SYNTH, LISTENER + BPM,
                                               RATE, 8, tickpos, live=True)
    rejoined = LazyPerformer(
        LiveStream(state2, root2, tags2), tempo2, RATE,
        {b.name: Allocator(channels_of(source, b))
         for b in banks_of(source)},
        block=BLOCK, origin=tickpos, reader=record.reader_of())
    for t in range(6 * 2000, 12 * 2000, BLOCK):
        rejoined.advance(t)
    got = [(on + tickpos, off + tickpos, b, p)
           for on, off, b, p in rejoined.history]
    assert got, "the rejoined take was silent"
    assert got == want[:len(got)], (got[:3], want[:3])

    # And the keys are *what* fixed it: answering the same rejoin in
    # arrival order — the mechanism before ariadne — hands it the
    # take's opening answers, which is the defect itself.
    from collections import defaultdict, deque

    queues = defaultdict(deque)
    for entry in record.events:
        if entry[0] == "reading":
            queues[entry[2]].append(list(entry[3]))

    def in_order(port, key=None):
        q = queues.get(port)
        return list(q.popleft()) if q else []

    t3, s3, r3, g3 = stream_root(SYNTH, LISTENER + BPM, RATE, 8,
                                 tickpos, live=True)
    ordered = LazyPerformer(
        LiveStream(s3, r3, g3), t3, RATE,
        {b.name: Allocator(channels_of(source, b))
         for b in banks_of(source)},
        block=BLOCK, origin=tickpos, reader=in_order)
    for t in range(6 * 2000, 12 * 2000, BLOCK):
        ordered.advance(t)
    drifted = [(on + tickpos, off + tickpos, b, p)
               for on, off, b, p in ordered.history]
    assert drifted != got, "order-keying happened to agree — pick a "\
                           "script whose worlds differ more"


def test_a_rejoin_into_an_undeclared_joint_restarts_it_rather_than_stalling():
    """`durOf` of an unanswered question is 0, so a resume has nothing
    to step over — and stepping *repeatedly* was a walk that never
    advanced and fell silent.  It stops at the joint now: the phrase
    restarts there, audibly, with the thread answering by key.  The
    cure for wanting the skip is one word — `long` — and the test
    beside this one shows that spelling skipping properly.
    """
    undeclared = LISTENER.replace(
        "cycle (long 1 (do ks <- hear world; phraseOf ks))",
        "cycle (do ks <- hear world; phraseOf ks)")
    tempo, state, root, by_tag = stream_root(SYNTH, undeclared + BPM,
                                             RATE, 8, 6 * 96, live=True)
    stream = LiveStream(state, root, by_tag)
    stream.pull(20 * 96)
    assert stream.ask is not None, "the resume fell silent again"
    assert not stream.stalled, "a question is not a stall"


def test_a_thread_that_runs_dry_reads_as_silence():
    """Past the end of a take — or in a bar it never reached — the
    honest reading is that the world said nothing.  The queue must not
    answer there: falling back to it served *stale* answers, which is a
    replay inventing a world it never had.  A replay is exactly as long
    as its thread, and the band lays out after it.
    """
    from gestate.transcript import Transcript

    source = SYNTH + "\n" + LISTENER + BPM
    tempo, state, root, by_tag = stream_root(SYNTH, LISTENER + BPM, RATE,
                                             8, 0, live=True)
    record = Transcript(source_sha=Transcript.sha_of(source), rate=RATE,
                        block=BLOCK, seed=8)
    live = LazyPerformer(LiveStream(state, root, by_tag), tempo, RATE,
                         _allocators(), block=BLOCK, record=record,
                         reader=lambda port, key=None: [60, 64])
    for t in range(0, 3 * 2000, BLOCK):
        live.advance(t)
    assert live.history, "the take was silent — the test is empty"

    t2, s2, r2, g2 = stream_root(SYNTH, LISTENER + BPM, RATE, 8, 0,
                                 live=True)
    dry = LazyPerformer(LiveStream(s2, r2, g2), t2, RATE, _allocators(),
                        block=BLOCK, reader=record.reader_of())
    for t in range(0, 12 * 2000, BLOCK):      # four times the take
        dry.advance(t)
    assert len(dry.history) == len(live.history), \
        "the replay played on past what the thread knew"


def test_a_dry_thread_is_a_recorded_fact_not_only_a_silence():
    """Henri's rule: silence is the right sound, and the performance
    should be able to say *which* silence it was.  A question the
    thread has no record of plays as nothing and is written down —
    beside the stalls and the drops — so a host can explain it."""
    from gestate.transcript import Transcript

    source = SYNTH + "\n" + LISTENER + BPM
    tempo, state, root, by_tag = stream_root(SYNTH, LISTENER + BPM, RATE,
                                             8, 0, live=True)
    record = Transcript(source_sha=Transcript.sha_of(source), rate=RATE,
                        block=BLOCK, seed=8)
    live = LazyPerformer(LiveStream(state, root, by_tag), tempo, RATE,
                         _allocators(), block=BLOCK, record=record,
                         reader=lambda port, key=None: [60, 64])
    for t in range(0, 3 * 2000, BLOCK):
        live.advance(t)

    t2, s2, r2, g2 = stream_root(SYNTH, LISTENER + BPM, RATE, 8, 0,
                                 live=True)
    replay = Transcript(source_sha=Transcript.sha_of(source), rate=RATE,
                        block=BLOCK, seed=8)
    dry = LazyPerformer(LiveStream(s2, r2, g2), t2, RATE, _allocators(),
                        block=BLOCK, record=replay,
                        reader=record.reader_of())
    for t in range(0, 9 * 2000, BLOCK):
        dry.advance(t)

    told = replay.confessions()
    assert told.get("dry"), "a dry thread went unrecorded"
    assert not [e for e in record.events if e[0] == "dry"], \
        "the live take had a world; nothing there was dry"
    # And the two silences are told apart: an empty world is a reading
    # of nothing, a dry thread is no reading at all.
    empty = [e for e in replay.events
             if e[0] == "reading" and e[3] == []]
    assert empty, "the dry questions still read as silence"


# ── The two acceptance clauses the suite still owed ─────────────────────────


def test_bind_distributes_through_a_joint():
    """Acceptance 2 (`spec/ariadne.md`): the homomorphism holds when a
    branch contains a question.  `(a ++ b) >>= f` is `(a >>= f) ++
    (b >>= f)` even where `a` is decided by the world — which is the
    property the old boxed surface broke and the whole redesign is
    for."""
    joined = ("\nworld : Chan (List Int)\nworld = chan\n"
              "\nphraseOf : List Int -> [: Custom :]\n"
              "phraseOf ks = case ks of\n"
              "    Nil -> r\n"
              "    k :: kt -> '(Custom 0.9 k)\n"
              "\nscore : [: Void :]\n"
              "score = (((do ks <- hear world; phraseOf ks)"
              " ++ '(Custom 0.5 36)) >>= voices.lead)\n")
    spread = joined.replace(
        "(((do ks <- hear world; phraseOf ks) ++ '(Custom 0.5 36))"
        " >>= voices.lead)",
        "(((do ks <- hear world; phraseOf ks) >>= voices.lead)"
        " ++ ('(Custom 0.5 36) >>= voices.lead))")
    assert spread != joined
    for world in ([60], [60, 64], []):
        assert _drive(joined, world) == _drive(spread, world), world


def test_the_label_bind_sentence_holds_with_joints_inside():
    """Acceptance 7: Henri's own spelling — the sections of a piece as
    *payloads*, bound to the function that plays them —

        ('"opening" ++ '"verse" ++ '"closing") >>= scoreParts

    equals the piece written out, to the tick, and keeps doing so when
    the parts listen.  This is what makes labels *paths*: bind
    preserves the spine exactly, so a position in the form is a
    position in the music.
    """
    parts = """
world : Chan (List Int)
world = chan

opening : [: Custom :]
opening = '(Custom 1.0 60) |* 2

verse : [: Custom :]
verse = do
    ks <- hear world
    case ks of
        Nil -> r
        k :: kt -> '(Custom 0.9 k)

closing : [: Custom :]
closing = '(Custom 0.6 72) |* 2

scoreParts : String -> [: Custom :]
scoreParts name = case name == "opening" of
    True -> opening
    False -> case name == "verse" of
        True -> verse
        False -> closing
"""
    bound = parts + ("\nscore : [: Void :]\n"
                     "score = (('\"opening\" ++ '\"verse\" ++ '\"closing\")"
                     " >>= scoreParts) >>= voices.lead\n")
    written = parts + ("\nscore : [: Void :]\n"
                       "score = (opening ++ verse ++ closing)"
                       " >>= voices.lead\n")
    for world in ([64], []):
        assert _drive(bound, world) == _drive(written, world), world


# ── The label half of paths: sections, and seeking by name ─────────────────


FORM = """
verse : [: Custom :]
verse = '(Custom 0.9 64)

chorus : [: Custom :]
chorus = '(Custom 1.0 72) |* 2

scoreParts : String -> [: Custom :]
scoreParts name = section name (case name of
    "verse" -> verse
    _ -> chorus)
"""


def test_a_piece_names_its_own_parts():
    """Acceptance 6 (`spec/ariadne.md`), the label half: the form
    written as *payloads* and bound to the function that plays them
    gives the transport a map — `[(tick, name)]` — read off the score
    itself, so a form that is computed maps as a written one does.
    """
    from gestate.audioscore import marks_of, tick_of_mark

    piece = FORM + ("\nscore : [: Void :]\n"
                    "score = (('\"opening\" ++ '\"verse\" ++ '\"closing\")"
                    " >>= scoreParts) >>= voices.lead\n") + BPM
    marks = marks_of(SYNTH, piece, RATE, limit=8)
    assert marks == [(0, "opening"), (192, "verse"), (288, "closing")]
    assert tick_of_mark(marks, "verse") == 192
    assert tick_of_mark(marks, "nowhere") is None


def test_an_endless_form_maps_as_far_as_it_is_asked():
    """A `cycle` of sections has endless marks, so the map is a
    *prefix* — the honest shape of the question — and occurrences are
    counted left to right, which is how a person reads a form and how
    `seek "verse/3"` finds its bar."""
    from gestate.audioscore import marks_of, tick_of_mark

    piece = FORM + ("\nscore : [: Void :]\n"
                    "score = ((cycle ('\"verse\" ++ '\"chorus\"))"
                    " >>= scoreParts) >>= voices.lead\n") + BPM
    marks = marks_of(SYNTH, piece, RATE, limit=6)
    assert len(marks) == 6, "the map should stop where it was asked to"
    assert [m for _t, m in marks] == ["verse", "chorus"] * 3
    assert tick_of_mark(marks, "verse", 3) == 576
    assert tick_of_mark(marks, "chorus", 2) == 384


def test_a_section_costs_the_music_nothing():
    """The constant law once more: naming a part changes no event and
    no tick — a mark is zero wide and the body follows it, so
    `durOf (section n s)` is `durOf s` by construction."""
    named = FORM + ("\nscore : [: Void :]\n"
                    "score = (('\"verse\" ++ '\"chorus\"')"
                    " >>= scoreParts) >>= voices.lead\n").replace("'\"chorus\"'",
                                                                  "'\"chorus\"")
    bare = ("\nverse : [: Custom :]\nverse = '(Custom 0.9 64)\n"
            "\nchorus : [: Custom :]\nchorus = '(Custom 1.0 72) |* 2\n"
            "\nscore : [: Void :]\n"
            "score = (verse ++ chorus) >>= voices.lead\n")
    assert _events(named) == _events(bare)


# ── tempoShape: a tempo written where it happens ───────────────────────────


def _onsets(piece):
    from gestate.audioscore import perform_voices, samples_of

    tempo, events = perform_voices(SYNTH, piece + BPM, RATE)
    return [samples_of(on, tempo, RATE) for on, _o, _b, _p in events]


PHRASE = ("\nscore : [: Void :]\n"
          "score = (BODY ++ '(Custom 0.8 67)) >>= voices.lead\n")
PAIR = "('(Custom 1.0 60) ++ '(Custom 0.9 64))"


def test_a_flat_tempo_shape_is_invisible():
    """The constant law at the clock — and it costs nothing to keep,
    because `tempo.envelope` already collapses an envelope of one
    value back to the *integer* path a plain `bpm` takes."""
    plain = PHRASE.replace("BODY", PAIR)
    flat = PHRASE.replace("BODY", f"tempoShape [Step 0.0 120.0] {PAIR}")
    assert _onsets(flat) == _onsets(plain)


def test_a_written_rit_slows_its_span_and_moves_what_follows():
    """A tempo written where it happens: the span slows, and the beat
    after it lands later by exactly the time the slowing added — the
    displacement is real and local, which is what a rit *is*."""
    plain = PHRASE.replace("BODY", PAIR)
    rit = PHRASE.replace(
        "BODY", f"tempoShape [Step 0.0 120.0, Ramp 1.0 60.0] {PAIR}")
    was, now = _onsets(plain), _onsets(rit)
    assert now[0] == was[0], "the span starts where it always did"
    assert now[1] > was[1], "the second beat should arrive late"
    assert now[2] - now[1] > was[2] - was[1], \
        "and the beat after the span carries the displacement"


def test_a_tempo_shape_keeps_the_closed_form_inverse():
    """The property the whole design rests on: a shaped piece is still
    an envelope, so beat -> time is the quadratic formula rather than
    a replay.  `time_at` answering at all is the assertion."""
    from gestate.audioscore import perform_voices
    from gestate.tempo import TempoEnvelope

    rit = PHRASE.replace(
        "BODY", f"tempoShape [Step 0.0 120.0, Ramp 1.0 60.0] {PAIR}")
    tempo, _events = perform_voices(SYNTH, rit + BPM, RATE)
    assert isinstance(tempo, TempoEnvelope)
    assert tempo.time_at(2.0) > 1.0, "beat 2 arrives after the rit"
    assert tempo.beat_at(tempo.time_at(3.0)) == pytest.approx(3.0), \
        "the two directions must be one answer"


# ── shape and fermata ──────────────────────────────────────────────────────


SHAPED = """
swell : Chan Float
swell = chan

score : [: Void :]
score = shape swell POINTS ('(Custom 1.0 60) ++ '(Custom 0.9 64)) >>= voices.lead
"""


def _swell(points, beats=4):
    from gestate.audioperform import dynamic

    perf, _a = dynamic(SYNTH, SHAPED.replace("POINTS", points) + BPM,
                       rate=RATE, block=BLOCK)
    seen = []
    for t in range(0, beats * 2000, BLOCK):
        perf.advance(t)
        seen.append(perf.values.get("swell"))
    return seen


def test_a_shape_writes_its_channel_across_its_span():
    """Automation at control rate, which in gestate is once per block:
    the channel follows the envelope, the points being fractions of
    the span's own width."""
    seen = _swell("[Step 0.0 0.2, Ramp 1.0 0.9]")
    assert seen[0] == pytest.approx(0.2)
    assert seen[len(seen) // 4] > 0.2, "it should be climbing"
    assert max(v for v in seen if v is not None) == pytest.approx(0.9, abs=0.02)
    assert all(a <= b + 1e-9 for a, b in zip(seen, seen[1:])), "monotone"


def test_a_flat_shape_is_a_knob_set_once():
    """The constant law: an envelope of one value is indistinguishable
    from writing the knob."""
    assert set(_swell("[Step 0.0 0.5]")) == {0.5}


FERMATA = """
pedal : Chan Int
pedal = chan

score : [: Void :]
score = ('(Custom 1.0 60) ++ fermata pedal ++ '(Custom 0.9 64)) >>= voices.lead
"""


def _held_take(samples_held):
    from gestate.audioalloc import GATE_AT
    from gestate.audiodynamic import LazyPerformer, LiveStream

    tempo, state, root, tags = stream_root(SYNTH, FERMATA + BPM, RATE,
                                           0, 0, live=True)
    now = [0]
    perf = LazyPerformer(LiveStream(state, root, tags), tempo, RATE,
                         _allocators(), block=BLOCK,
                         holding=lambda chan, beat, waited: now[0] < samples_held)
    gates = []
    for t in range(0, 20 * 2000, BLOCK):
        now[0] = t
        for boundary, chan, value in perf.advance(t):
            if chan.endswith("f0") and value:
                gates.append(boundary)
    return gates, perf


def test_a_fermata_waits_exactly_as_long_as_it_is_held():
    """The world chooses *when*: what follows the fermata arrives
    later by exactly the time the piece spent waiting, and a fermata
    nobody holds costs the piece nothing."""
    loose, _p = _held_take(0)
    short, _q = _held_take(3 * 2000)
    long_, _r = _held_take(6 * 2000)
    assert len(loose) == len(short) == len(long_) == 2
    assert loose[1] == pytest.approx(1984, abs=64)
    assert short[1] - loose[1] == pytest.approx(3 * 2000, abs=128)
    assert long_[1] - loose[1] == pytest.approx(6 * 2000, abs=128)


def test_a_held_note_goes_on_sounding_through_the_fermata():
    """It falls out rather than being built: the note's release sits
    at a tick the clock has not reached, so the instrument simply
    holds it — which is what stopping the clock *means*."""
    from gestate.audioalloc import OFF_AT

    _gates, perf = _held_take(6 * 2000)
    offs = [chan for chan, value in perf.values.items()
            if chan.endswith("f1") and value]
    # The first note's release lands only after the wait is over, so
    # during the hold nothing was released early.
    assert perf._held >= 6 * 2000 - 128, "the clock did not wait"


def test_a_take_that_waited_replays_as_one_that_waited():
    """The oracle, with fermatas in it.  A hold's *length* is world
    input — the one thing about a fermata that is not arithmetic — so
    the thread records it and a replay holds for exactly as long,
    with no channel being touched at all.  Without this entry
    "improv equals replay" is false for any piece that waits.
    """
    from gestate.audiodynamic import LazyPerformer, LiveStream
    from gestate.transcript import Transcript

    source = SYNTH + "\n" + FERMATA + BPM

    def take(holding, record):
        tempo, state, root, tags = stream_root(SYNTH, FERMATA + BPM, RATE,
                                               0, 0, live=True)
        perf = LazyPerformer(LiveStream(state, root, tags), tempo, RATE,
                             _allocators(), block=BLOCK, record=record,
                             holding=holding)
        gates = []
        for t in range(0, 20 * 2000, BLOCK):
            take.now = t
            for boundary, chan, value in perf.advance(t):
                if chan.endswith("f0") and value:
                    gates.append(boundary)
        return gates

    record = Transcript(source_sha=Transcript.sha_of(source), rate=RATE,
                        block=BLOCK, seed=0)
    live = take(lambda chan, beat, waited: take.now < 5 * 2000, record)
    held = [e for e in record.events if e[0] == "held"]
    assert held, "the wait went unrecorded"
    assert held[0][3] == pytest.approx(5 * 2000, abs=128)

    replayed = take(record.holding_of(), None)
    assert replayed == live, "the replay did not wait what the take waited"


def _shaped(expr, beats=3, points="[Step 0.0 0.2, Ramp 1.0 0.9]"):
    from gestate.audioperform import dynamic

    piece = ("\nswell : Chan Float\nswell = chan\n\nscore : [: Void :]\n"
             f"score = {expr.replace('POINTS', points)} >>= voices.lead\n")
    perf, _a = dynamic(SYNTH, piece + BPM, rate=RATE, block=BLOCK)
    out = []
    for t in range(0, beats * 2000, BLOCK):
        perf.advance(t)
        out.append(perf.values.get("swell"))
    return [v for v in out if v is not None]


PAIR2 = "('(Custom 1.0 60) ++ '(Custom 0.9 64))"


def test_a_shape_reverses_with_its_content():
    """Acceptance 8, the law that was quietly broken: a shape under
    `reverse` runs backwards.  It was *dropped* (the span walk said
    `Nil` at a retrograde), and mirroring the beats alone left every
    ramp behind a step — a flat line that looked like a shape."""
    forward = _shaped(f"shape swell POINTS {PAIR2}")
    backward = _shaped(f"reverse (shape swell POINTS {PAIR2})")
    assert forward[0] == pytest.approx(0.2, abs=0.02)
    assert backward[0] == pytest.approx(0.9, abs=0.02)
    assert backward[len(backward) // 3] < backward[0], "it must descend"


def test_a_shape_scales_with_its_span():
    """Fractions of the span, so `|*` stretches the curve rather than
    leaving it behind."""
    plain = _shaped(f"shape swell POINTS {PAIR2}", beats=3)
    wide = _shaped(f"(shape swell POINTS {PAIR2}) |* 2", beats=5)
    assert plain[0] == pytest.approx(wide[0], abs=0.02)
    # Half way through the doubled span reads what the whole one read
    # half way through its own.
    assert wide[len(wide) // 4] == pytest.approx(plain[len(plain) // 4],
                                                 abs=0.08)


def test_a_shape_survives_the_instrument_bind():
    """It commutes with `>>=`: the annotation rides the subtree, so
    committing the notes to a bank leaves it writing."""
    assert max(_shaped(f"shape swell POINTS {PAIR2}")) > 0.8


def test_the_bake_writes_a_shape_too():
    """An offline render of a shaped piece should sound like a live
    one — so the schedule carries the automation beside the notes."""
    from gestate.audioperform import scored

    piece = ("\nswell : Chan Float\nswell = chan\n\nscore : [: Void :]\n"
             f"score = shape swell [Step 0.0 0.2, Ramp 1.0 0.9] {PAIR2}"
             " >>= voices.lead\n")
    schedule, _samples, _a = scored(SYNTH, piece + BPM, rate=RATE,
                                    block=BLOCK)
    early = schedule.value_at("swell", 0)
    late = schedule.value_at("swell", 3 * RATE // 2)
    assert early == pytest.approx(0.2, abs=0.02)
    assert late > early, "the baked automation must climb"


def test_a_shape_over_a_question_is_refused_by_name():
    """A shape's points are fractions and a question has no width
    until it is answered, so there is nothing to be a fraction of.
    Refused with the cure in the message."""
    from gestate.audioperform import scored
    from gestate.audioscore import ScoreError

    piece = ("\nworld : Chan (List Int)\nworld = chan\n"
             "\nswell : Chan Float\nswell = chan\n\nscore : [: Void :]\n"
             "score = shape swell [Step 0.0 0.2, Ramp 1.0 0.9]"
             " (do ks <- hear world; '(Custom 1.0 60)) >>= voices.lead\n")
    with pytest.raises(ScoreError, match="long"):
        scored(SYNTH, piece + BPM, rate=RATE, block=BLOCK)
