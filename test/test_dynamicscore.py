"""`spec/dynamicscore.md` stage one — static layout, dynamic execution.

The claim under test is the stage's own parity clause: *the dynamic
performance of a static score is the static schedule, change for change,
sample for sample.*  A `Performer` walking the beat-ordered events at a
constant tempo must emit precisely what `schedule_voices` bakes — same
channels, same delivery boundaries, same values — and the rendered audio
must be bit-identical.

The seek tests pin the second clause before any second implementation
exists: *seek-then-perform equals `value_at`*.  Stage 10's silent defects
lived exactly where two implementations decided when-a-note-happens, so
the semantics are held here, in one language, first.
"""

from __future__ import annotations

import shutil
import tempfile

import pytest

from gestate.audioalloc import GATE_AT, OFF_AT, Allocator
from gestate.audiodynamic import Performer
from gestate.audiollvm import run_native
from gestate.audioschedule import Schedule
from gestate.audioscore import (assemble_performance, duration_of_voices,
                                perform_voices, schedule_voices)
from gestate.audiovoices import banks_of, channels_of
from gestate.tempo import envelope

needs_clang = pytest.mark.skipif(shutil.which("clang") is None,
                                 reason="no clang to build the IR with")

SYNTH = """
Custom := Custom Float Int

voices lead 3 myVoice : Sig Float

voices bass 2 myVoice : Sig Float

outV : Both Gate Custom -> Float
outV p = case p of
    Both w c -> case w of
        Gate on off -> inner on off c

inner : Int -> Int -> Custom -> Float
inner on off c = case c of
    Custom f k -> sawOf (wrap (toFloat k * 0.002)) * f * 0.2

myVoice : Sig Gate -> Sig Custom -> Sig Float
myVoice g s = myVoiceFolded (!Both g s)

myVoiceFolded : Sig (Both Gate Custom) -> Sig Float
myVoiceFolded s = map outV s

sound : Sig Float
sound = 0.5 * (lead + bass)
"""

#: Four beats of melody with a *four*-note chord on a three-voice bank —
#: so the stealing policy runs and parity covers it — over a bass line
#: whose first note is a four-beat pedal, so a seek can land inside a
#: held note.  Eight beats in all.
PIECE = """
chord : [: Custom :]
chord = '(Custom 0.9 72) || '(Custom 0.7 76) || '(Custom 0.5 79) || '(Custom 0.4 83)

tune : [: Custom :]
tune = '(Custom 1.0 60) ++ '(Custom 0.8 64) ++ '(Custom 0.6 67) ++ chord ++ '(Custom 0.8 74)

line : [: Custom :]
line = ('(Custom 0.7 36) |* 4) ++ ('(Custom 0.6 43) |* 2) ++ ('(Custom 0.5 36) |* 2)

score : [: Void :]
score = (tune >>= voices.lead) || (line >>= voices.bass)

bpm : Int
bpm = 120
"""

RATE, BLOCK = 4000, 64
BOTH = SYNTH + "\n" + PIECE


def _allocators():
    return {b.name: Allocator(channels_of(BOTH, b)) for b in banks_of(BOTH)}


def _events():
    return perform_voices(SYNTH, PIECE, RATE)


def _advance_through(performer, samples, start=0):
    """Drive block by block, as an engine would; the changes, in order."""
    out = []
    for t in range(start, samples + BLOCK, BLOCK):
        out += performer.advance(t)
    return out


def _as_schedule(changes) -> Schedule:
    schedule = Schedule()
    for boundary, chan, value in changes:
        schedule.change(boundary, chan, value)
    return schedule


# ── Change for change ───────────────────────────────────────────────────────


def test_dynamic_equals_baked_change_for_change():
    """The parity anchor: a performer at a constant tempo *is* the bake."""
    bpm, events = _events()
    baked = schedule_voices(events, bpm, RATE, _allocators(), block=BLOCK)
    samples = duration_of_voices(events, bpm, RATE)

    performer = Performer(events, bpm, RATE, _allocators(), block=BLOCK)
    performed = _as_schedule(_advance_through(performer, samples))
    assert performed.changes == baked.changes


def test_one_advance_to_the_end_is_also_the_bake():
    """Granularity must not matter: one giant step equals every small one."""
    bpm, events = _events()
    baked = schedule_voices(events, bpm, RATE, _allocators(), block=BLOCK)
    samples = duration_of_voices(events, bpm, RATE)

    performer = Performer(events, bpm, RATE, _allocators(), block=BLOCK)
    performed = _as_schedule(performer.advance(samples))
    assert performed.changes == baked.changes


def test_dynamic_equals_baked_under_a_tempo_envelope():
    """The shared `samples_of` is held on its other branch too.

    A ritardando from 120 to 60 across the first four beats: the floating
    path with the square root in it, where a second spelling of tick-to-
    sample would drift first.
    """
    _bpm, events = _events()
    tempo = envelope([(0.0, False, 120.0), (4.0, True, 60.0)])
    baked = schedule_voices(events, tempo, RATE, _allocators(), block=BLOCK)
    samples = duration_of_voices(events, tempo, RATE)

    performer = Performer(events, tempo, RATE, _allocators(), block=BLOCK)
    performed = _as_schedule(_advance_through(performer, samples))
    assert performed.changes == baked.changes


def test_advance_is_idempotent():
    """A control tick asked twice delivers nothing twice."""
    bpm, events = _events()
    performer = Performer(events, bpm, RATE, _allocators(), block=BLOCK)
    assert performer.advance(5000) != []
    assert performer.advance(5000) == []


# ── Sample for sample ───────────────────────────────────────────────────────


@needs_clang
def test_dynamic_equals_baked_sample_for_sample():
    """The whole piece through the engine twice: bit-identical audio."""
    from gestate.audioextract import extract_analysis
    from gestate.audioperform import Performance, from_performer
    from gestate.pipeline import analyse

    bpm, events = _events()
    samples = duration_of_voices(events, bpm, RATE)
    graph = extract_analysis(
        analyse(assemble_performance(SYNTH, PIECE, RATE)), rate=RATE)

    baked = schedule_voices(events, bpm, RATE, _allocators(), block=BLOCK)
    performer = Performer(events, bpm, RATE, _allocators(), block=BLOCK)
    dynamic = Performance(graph, [from_performer(performer)]).control()

    with tempfile.TemporaryDirectory() as d:
        want = run_native(graph, d, samples, block=BLOCK,
                          control=baked.control_for(graph))
    with tempfile.TemporaryDirectory() as d:
        got = run_native(graph, d, samples, block=BLOCK, control=dynamic)
    assert max(abs(s) for s in want) > 0.01, "silent"
    assert got == want


# ── Seek ────────────────────────────────────────────────────────────────────


def test_seek_then_perform_equals_value_at():
    """The parity's second clause, on a cold seek.

    Stand at a mid-piece boundary as if played from the top, then perform
    to the end: at every boundary, every channel the bake has touched by
    then reads exactly what the bake's `value_at` says — held notes
    included, which is the silent replay doing `into_schedule`'s work on
    demand.
    """
    bpm, events = _events()
    baked = schedule_voices(events, bpm, RATE, _allocators(), block=BLOCK)
    samples = duration_of_voices(events, bpm, RATE)
    target = 6400                       # beat 3.2 — inside the chord

    performer = Performer(events, bpm, RATE, _allocators(), block=BLOCK)
    performer.seek(target)
    for t in range(target, samples + BLOCK, BLOCK):
        performer.advance(t)
        for chan in baked.channels():
            want = baked.value_at(chan, t)
            if want is not None:
                assert performer.values.get(chan) == want, (chan, t)


def test_seek_into_a_held_note_resumes_it():
    """A note begun before the target and held across it *sounds* there.

    Its `gateAt` still names the original onset, so the envelope lands
    mid-flight — the arithmetic-on-the-instant half seeking for free.
    """
    bpm, events = _events()
    performer = Performer(events, bpm, RATE, _allocators(), block=BLOCK)
    performer.seek(6400)                # inside the bass's four-beat pedal

    gate = performer.allocators["bass"].channels[0][GATE_AT]
    off = performer.allocators["bass"].channels[0][OFF_AT]
    assert performer.values[gate] == 1  # onset at sample 0, 1-based
    assert performer.values[off] == 0   # and not yet released


def test_seek_releases_what_sounds():
    """A hot seek: what sounded is released or re-occupied, never left on.

    Every voice sounding before the seek gets `offAt` at the seek instant
    — unless the replay re-occupies its channels, in which case the
    replayed state wins, which is what `value_at` parity demands.
    """
    bpm, events = _events()
    baked = schedule_voices(events, bpm, RATE, _allocators(), block=BLOCK)
    performer = Performer(events, bpm, RATE, _allocators(), block=BLOCK)
    _advance_through(performer, 6400)   # chord and pedal sounding
    before = {name: [v for v in a.voices if v.key is not None]
              for name, a in performer.allocators.items()}
    assert any(before.values()), "nothing was sounding — the test is empty"

    target = 14016                      # beat 7, on a block boundary
    performer.seek(target)
    for name, sounding in before.items():
        for voice in sounding:
            chan = performer.allocators[name].channels[voice.index][OFF_AT]
            replayed = baked.value_at(chan, target)
            want = replayed if replayed is not None else target + 1
            assert performer.values[chan] == want, (name, voice.index)


def test_a_backward_seek_releases_into_silence():
    """Seek to the top: nothing has history there, so what sounded is
    released and every gate reads "never played"."""
    bpm, events = _events()
    performer = Performer(events, bpm, RATE, _allocators(), block=BLOCK)
    _advance_through(performer, 6400)

    sounding = [(name, v.index)
                for name, a in performer.allocators.items()
                for v in a.voices if v.key is not None]
    performer.seek(0)
    for name, index in sounding:
        chans = performer.allocators[name].channels[index]
        assert performer.values[chans[OFF_AT]] == 1      # released at 0
        assert chans[GATE_AT] not in performer.values    # no note stands


# ── Loop ────────────────────────────────────────────────────────────────────


def test_loop_replays_the_same_changes():
    """A loop is a seek on a boundary, and the second pass is the first.

    Same changes with the same values — `gateAt` names score positions,
    not wall time — and the allocators come out in the same state, so the
    seam does not corrupt what follows.
    """
    bpm, events = _events()
    end = 8000                          # loop beats 0..4

    performer = Performer(events, bpm, RATE, _allocators(), block=BLOCK)
    first = [c for t in range(0, end, BLOCK) for c in performer.advance(t)]
    performer.seek(0)
    second = [c for t in range(0, end, BLOCK) for c in performer.advance(t)]

    assert first == second
    assert first, "the loop body was empty"
