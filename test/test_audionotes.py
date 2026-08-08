"""Notes: allocation, live MIDI, and `Score` — the three on one path.

A note is the same thing whether it arrives from a keyboard now or from a
layout computed in advance; only *when it is decided* differs.  So there is
one `Allocator`, and the two callers differ in where its changes go — live
MIDI into the values the audio callback reads, a `Score` into a `Schedule`
that can be rendered offline and checked against the oracle.

That last part is why this is checkable at all.  The final test here
performs a gestate `Score` through a gestate instrument and requires the
interpreter, the block renderer and the generated code to agree sample for
sample — which is the standard every stage of `spec/liveaudio.md` was built
to, applied to the two backends meeting.
"""

from __future__ import annotations

import shutil
import tempfile
from pathlib import Path

import pytest

from gestate import midi
from gestate.audio import render
from gestate.audioalloc import (AllocError, Allocator, into_schedule,
                                steal_none, steal_oldest)
from gestate.audioengine import run
from gestate.audioextract import extract
from gestate.audiollvm import run_native
from gestate.audiomidi import Notes
from gestate.audioschedule import Schedule
from gestate.audioscore import (BankRef, ScoreError, duration_of,
                                samples_of, schedule_of)
from gestate.audiovoices import banks_of, channels_of

needs_clang = pytest.mark.skipif(shutil.which("clang") is None,
                                 reason="no clang to build the IR with")

#: Four voices, each a sawtooth with an attack/release the note's own times
#: drive.  `gateAt`/`offAt` are 1-based, so an untouched bank is silent —
#: which is what makes eight idle voices cost nothing at start-up.
SYNTH = """
Pitched := Pitched Int

voices lead 4 : Pitched -> Sig Float
lead = plucked

hzOf : Int -> Float
hzOf k = 8.1758 * pow 2.0 (toFloat k / 12.0)

Osc := Osc Float Int

bump : Float -> Int -> Both Gate Pitched -> Osc
bump ph t nn = case nn of
    Both w q -> case w of
        Gate on off -> bend ph t q

bend : Float -> Int -> Pitched -> Osc
bend ph t q = case q of
    Pitched p -> Osc (wrap (ph + hzOf p / sampleRate)) (t + 1)

stepOsc : Osc -> Both Gate Pitched -> Osc
stepOsc o nn = case o of
    Osc ph t -> bump ph t nn

levelAt : Int -> Both Gate Pitched -> Float
levelAt n nn = case nn of
    Both w q -> case w of
        Gate on off -> gateOf n on off

gateOf : Int -> Int -> Int -> Float
gateOf n on off = case on of
    0 -> 0.0
    _ -> heldOf n on off

heldOf : Int -> Int -> Int -> Float
heldOf n on off = case n < on - 1 of
    True -> 0.0
    False -> decayOf n on off

decayOf : Int -> Int -> Int -> Float
decayOf n on off = case off of
    0 -> exp (negate 2.0 * toFloat (n - on + 1) / sampleRate)
    _ -> releaseOf n on off

releaseOf : Int -> Int -> Int -> Float
releaseOf n on off = case n < off - 1 of
    True -> exp (negate 2.0 * toFloat (n - on + 1) / sampleRate)
    False -> exp (negate 12.0 * toFloat (n - off + 1) / sampleRate)

outOsc : Osc -> Both Gate Pitched -> Float
outOsc o nn = case o of
    Osc ph t -> sawOf ph * levelAt t nn * 0.2

plucked : Sig Gate -> Sig Pitched -> Sig Float
plucked g s = pluckedFolded (!Both g s)

pluckedFolded : Sig (Both Gate Pitched) -> Sig Float
pluckedFolded s = lowpass 0.4 (zip outOsc (scan stepOsc (Osc 0.0 0) s) s)

sound : Sig Float
sound = gain 0.8 lead
"""

PIECE = """
bpm : Int
bpm = 120

melody : [: Int :]
melody = '60 ++ '64 ++ '67 ++ '72

score : [: Void :]
score = melody >>= prog 0
"""

RATE, BLOCK = 4000, 64


def _alloc(policy="oldest", count=None) -> Allocator:
    bank = banks_of(SYNTH)[0]
    channels = channels_of(SYNTH, bank)
    return Allocator(channels[:count] if count else channels, policy=policy)


# ── Allocation ──────────────────────────────────────────────────────────────


def test_a_note_takes_a_voice_and_sets_its_three_channels():
    """`gateAt` is 1-based, and that is load-bearing.

    Zero means *no note*, so a bank whose channels have never been written
    reads as "nothing has played" rather than as "every voice started at
    sample 0" — eight silent voices at start-up fall out of the channels'
    own defaults rather than from anything the host must remember to send.
    """
    alloc = _alloc()
    assert alloc.note_on(60, (60,), at=0) == [
        ("leadChan0f0", 1), ("leadChan0f1", 0), ("leadChan0f2", 60)]
    assert alloc.sounding() == [60]


def test_notes_land_on_different_voices():
    alloc = _alloc()
    voices = []
    for i, pitch in enumerate((60, 64, 67)):
        changes = alloc.note_on(pitch, (pitch,), at=i * 100)
        voices.append(changes[0][0].split("f")[0])
    assert len(set(voices)) == 3, "three notes on one voice"
    assert alloc.sounding() == [60, 64, 67]


def test_a_note_off_releases_the_voice_playing_that_pitch():
    alloc = _alloc()
    alloc.note_on(60, (60,), at=0)
    alloc.note_on(64, (64,), at=10)
    assert alloc.note_off(64, at=50) == [("leadChan1f1", 51)]
    assert alloc.sounding() == [60]


def test_a_note_off_for_nothing_is_silently_nothing():
    """A stuck key, or a note whose voice was stolen.  Ordinary, not an error."""
    assert _alloc().note_off(60, at=10) == []


def test_a_freed_voice_is_reused_released_longest_ago_first():
    """So a note lands on the voice whose tail has had most time to decay."""
    alloc = _alloc(count=2)
    alloc.note_on(60, (60,), at=0)
    alloc.note_on(64, (64,), at=10)
    alloc.note_off(60, at=100)          # voice 0 free, released at 100
    alloc.note_off(64, at=200)          # voice 1 free, released at 200
    changes = alloc.note_on(67, (67,), at=300)
    assert changes[0][0] == "leadChan0f0", "took the more recently freed voice"


def test_oldest_is_stolen_when_every_voice_is_held():
    """The default, and the one policy easy to explain to a player.

    Hold five notes on a four-voice synth and the first you played goes.
    """
    alloc = _alloc()
    for i, pitch in enumerate((60, 62, 64, 65)):
        alloc.note_on(pitch, (pitch,), at=i * 10)
    assert alloc.sounding() == [60, 62, 64, 65]

    changes = alloc.note_on(72, (72,), at=100)
    assert changes[0][0] == "leadChan0f0", "did not steal the oldest"
    assert alloc.sounding() == [62, 64, 65, 72], "60 should have gone"


def test_the_none_policy_drops_the_note_instead():
    alloc = _alloc(policy="none")
    for i, pitch in enumerate((60, 62, 64, 65)):
        alloc.note_on(pitch, (pitch,), at=i * 10)
    assert alloc.note_on(72, (72,), at=100) == [], "the note should be refused"
    assert alloc.sounding() == [60, 62, 64, 65]


def test_a_policy_can_be_a_function():
    """Selectable, with a good default — the policy is the caller's."""
    alloc = Allocator(channels_of(SYNTH, banks_of(SYNTH)[0]),
                      policy=lambda voices: voices[-1])
    for i, pitch in enumerate((60, 62, 64, 65)):
        alloc.note_on(pitch, (pitch,), at=i * 10)
    assert alloc.note_on(72, (72,), at=100)[0][0] == "leadChan3f0"


def test_an_unknown_policy_says_which_there_are():
    with pytest.raises(AllocError, match="no voice-stealing policy"):
        _alloc(policy="loudest")


def test_all_off_releases_everything_held():
    alloc = _alloc()
    alloc.note_on(60, (60,), at=0)
    alloc.note_on(64, (64,), at=10)
    changes = alloc.all_off(at=99)
    assert sorted(changes) == [("leadChan0f1", 100), ("leadChan1f1", 100)]
    assert alloc.sounding() == []


# ── Live MIDI notes ─────────────────────────────────────────────────────────


class _Message:
    def __init__(self, type_, note=60, velocity=100, channel=0):
        self.type, self.note = type_, note
        self.velocity, self.channel = velocity, channel


# ── Routing: which bank a key plays ─────────────────────────────────────────


def _two_banks():
    """`duet.ges`'s two banks, with their own allocators."""
    from gestate.audioperform import allocator_for

    synth, _ = _duet()
    return {"lead": allocator_for(synth, "lead"),
            "bass": allocator_for(synth, "bass")}


def test_midi_channel_n_plays_bank_n_by_default():
    """What hardware does: a keyboard per channel, a track per channel."""
    banks = _two_banks()
    notes = Notes(banks)
    assert notes.feed(_Message("note_on", 60, channel=0))
    assert notes.feed(_Message("note_on", 40, channel=1))
    assert banks["lead"].sounding() == [60]
    assert banks["bass"].sounding() == [40]


def test_a_channel_past_the_last_bank_plays_nothing():
    """Rather than folding onto one — silently doubling a part is worse
    than not hearing it."""
    banks = _two_banks()
    notes = Notes(banks)
    assert not notes.feed(_Message("note_on", 60, channel=7))
    assert notes.sounding() == []


def test_a_keyboard_can_be_split_by_pitch():
    """The classic left hand/right hand, and the reason routing is a
    function rather than a channel number."""
    from gestate.audiomidi import by_pitch

    banks = _two_banks()
    notes = Notes(banks, route=by_pitch([("bass", 48), ("lead", None)]))
    notes.feed(_Message("note_on", 36))
    notes.feed(_Message("note_on", 72))
    assert banks["bass"].sounding() == [36]
    assert banks["lead"].sounding() == [72]


def test_a_note_is_released_on_the_bank_it_began_on():
    """A player may hold a note, change the split, and let go.

    Routed again at release it would end on the wrong bank — and the right
    one would hold that note forever.
    """
    from gestate.audiomidi import by_pitch, one_bank

    banks = _two_banks()
    notes = Notes(banks, route=by_pitch([("bass", 48), ("lead", None)]))
    notes.feed(_Message("note_on", 36))
    assert banks["bass"].sounding() == [36]

    notes.route = one_bank("lead")             # the split moves under it
    notes.feed(_Message("note_off", 36))
    assert banks["bass"].sounding() == [], "the note was left hanging"
    assert banks["lead"].sounding() == []


def test_all_off_reaches_every_bank():
    banks = _two_banks()
    notes = Notes(banks)
    notes.feed(_Message("note_on", 60, channel=0))
    notes.feed(_Message("note_on", 40, channel=1))
    notes.all_off()
    assert notes.sounding() == []


def test_a_note_on_becomes_control_values():
    notes = Notes(_alloc())
    assert notes.feed(_Message("note_on", 60))
    assert notes.values == {"leadChan0f0": 1, "leadChan0f1": 0,
                            "leadChan0f2": 60}


def test_note_on_with_velocity_zero_is_a_note_off():
    """Every device that runs notes together sends this.

    A synth taking it literally would hang every note it played, so it is
    not a nicety.
    """
    notes = Notes(_alloc())
    notes.feed(_Message("note_on", 60, velocity=64))
    notes.now = 500
    assert notes.feed(_Message("note_on", 60, velocity=0))
    assert notes.values["leadChan0f1"] == 501, "not released"
    assert notes.sounding() == []


def test_a_note_is_stamped_with_the_instant_the_engine_has_reached():
    """`gateAt` names a real sample, not "now".

    The audio thread would otherwise have to interpret "now", and it is the
    only thread that knows what instant it is filling.
    """
    graph = extract(SYNTH, rate=RATE)
    notes = Notes(_alloc())
    control = notes.control_for(graph)
    node = graph.control_sources()[0].id

    control(node, 1000)                     # the engine reaches sample 1000
    notes.feed(_Message("note_on", 67))
    assert notes.values["leadChan0f0"] == 1001


def test_other_messages_are_not_notes():
    notes = Notes(_alloc())
    assert not notes.feed(_Message("control_change"))
    assert not notes.feed(_Message("pitchwheel"))
    assert notes.values == {}


def test_notes_can_be_pinned_to_one_midi_channel():
    notes = Notes(_alloc(), channel=2)
    assert not notes.feed(_Message("note_on", 60, channel=0))
    assert notes.feed(_Message("note_on", 60, channel=2))


def test_an_untouched_channel_still_reads_the_synths_default():
    """The rule the rest of the audio stack follows, and for the same reason."""
    graph = extract(SYNTH, rate=RATE)
    control = Notes(_alloc()).control_for(graph)
    for node in graph.control_sources():
        assert control(node.id, 0) == node.init


# ── Score ───────────────────────────────────────────────────────────────────


def test_ticks_become_samples():
    """96 ticks to the beat, 120 bpm — a beat is half a second."""
    assert samples_of(0, 120, 4000) == 0
    assert samples_of(96, 120, 4000) == 2000
    assert samples_of(192, 120, 4000) == 4000
    assert samples_of(96, 60, 4000) == 4000, "half the tempo, twice as long"


@pytest.mark.parametrize("bpm,rate", [(0, 4000), (-1, 4000), (120, 0)])
def test_a_nonsense_tempo_or_rate_is_refused(bpm, rate):
    with pytest.raises(ScoreError):
        samples_of(96, bpm, rate)


def test_a_score_becomes_a_schedule():
    bpm, events = midi.perform(PIECE)
    alloc = _alloc()
    schedule = schedule_of(events, bpm, RATE,
                           [BankRef("lead", alloc, default=True)], block=BLOCK)

    # Four notes, four voices, three channels each.
    assert len(schedule.channels()) == 12
    # The first note starts at sample 0, so `gateAt` is 1 and it is
    # delivered at the boundary at or before it — which is 0.
    assert schedule.value_at("leadChan0f0", 0) == 1
    assert schedule.value_at("leadChan0f2", 0) == 60


def test_an_instrument_with_no_bank_is_refused_by_name():
    """Rather than played on the wrong one, which is silent and wrong."""
    bpm, events = midi.perform(PIECE)
    other = BankRef("bass", _alloc(), programs=(42,))
    with pytest.raises(ScoreError, match="no bank plays it"):
        schedule_of(events, bpm, RATE, [other], block=BLOCK)


def test_a_program_number_picks_its_bank():
    bpm, events = midi.perform(PIECE)
    lead, bass = _alloc(), _alloc()
    schedule_of(events, bpm, RATE,
                [BankRef("bass", bass, programs=(42,)),
                 BankRef("lead", lead, programs=(0,))], block=BLOCK)
    assert lead.sounding() == [] and bass.sounding() == []
    # All four notes went to `lead`: `bass` never had a voice taken.
    assert all(v.started == -1 for v in bass.voices)
    assert any(v.started >= 0 for v in lead.voices)


def test_a_release_at_one_instant_comes_before_the_note_there():
    """So a monophonic line needs one voice, not two.

    A pass that did every onset first would need a voice per note; a legato
    line reuses the one it just freed, which is only possible if the
    release is processed first at a shared instant.
    """
    events = [(0, 96, 0, 60, 64), (96, 192, 0, 64, 64)]
    alloc = _alloc(count=1)                 # one voice: it must be reused
    schedule_of(events, 120, RATE, [BankRef("lead", alloc, default=True)],
                block=BLOCK)
    assert alloc.sounding() == []


def test_the_duration_reaches_the_last_note_off():
    """Not the last onset — a held final chord would be cut off."""
    bpm, events = midi.perform(PIECE)
    assert duration_of(events, bpm, RATE) == samples_of(384, bpm, RATE)


def test_delivery_lands_on_the_boundary_before_the_note():
    """The arithmetic that keeps an onset sample-accurate.

    The value *names* the instant; the delivery makes sure the voice holds
    it before that instant arrives.
    """
    schedule = Schedule()
    into_schedule(schedule, [("leadChan0f0", 1201)], at=1200, block=64)
    assert schedule.value_at("leadChan0f0", 1152) == 1201
    assert schedule.value_at("leadChan0f0", 1151) is None


# ── The two backends meeting ────────────────────────────────────────────────


@needs_clang
def test_a_gestate_score_plays_through_a_gestate_instrument():
    """The whole point, and checked the only way that counts.

    `midi.py` takes a `score` and writes a file for somebody else's
    synthesiser.  This takes the same layout and drives a `voices` bank
    compiled by the audio backend — so a piece written in gestate is
    performed by an instrument written in gestate, and the interpreter, the
    block renderer and the generated code must all agree about the result.
    """
    bpm, events = midi.perform(PIECE)
    alloc = _alloc()
    schedule = schedule_of(events, bpm, RATE,
                           [BankRef("lead", alloc, default=True)], block=BLOCK)
    samples = duration_of(events, bpm, RATE)

    graph = extract(SYNTH, rate=RATE)
    control = schedule.control_for(graph)

    oracle = render(SYNTH, samples / RATE, RATE,
                    control_every=BLOCK, schedule=schedule)
    assert run(graph, samples, block=BLOCK, control=control) == oracle
    with tempfile.TemporaryDirectory() as d:
        assert run_native(graph, d, samples, block=BLOCK,
                          control=control) == oracle

    assert max(abs(s) for s in oracle) > 0.05, "silent"
    assert all(-1.0 <= s <= 1.0 for s in oracle), "out of range"


def test_an_untouched_bank_is_silent():
    """Four idle voices must cost nothing — the reason `gateAt` is 1-based.

    Were it 0-based, every voice would read as having started at sample 0
    and a synth would open with a four-note chord nobody asked for.
    """
    graph = extract(SYNTH, rate=RATE)
    control = Schedule().control_for(graph)
    assert run(graph, 200, block=BLOCK, control=control) == [0.0] * 200


def test_the_notes_are_where_the_score_says():
    """Each note begins when its own onset does, not at a block boundary."""
    bpm, events = midi.perform(PIECE)
    alloc = _alloc()
    schedule = schedule_of(events, bpm, RATE,
                           [BankRef("lead", alloc, default=True)], block=BLOCK)
    graph = extract(SYNTH, rate=RATE)
    out = run(graph, duration_of(events, bpm, RATE), block=BLOCK,
              control=schedule.control_for(graph))

    # A beat is 2000 samples here; the second note starts there.
    before = max(abs(s) for s in out[1900:1990])
    after = max(abs(s) for s in out[2000:2100])
    assert after > before, "the second note did not arrive on the beat"


# ── Both at once — `examples/audio/duet.ges` ────────────────────────────────


DUET = Path(__file__).resolve().parent.parent / "examples" / "audio" / "duet.ges"


def _duet():
    """`duet.ges` is **one program** — instruments, piece and mix together.

    `voices.bass` names a bank lexically, so the type checker can say
    whether the piece fits the instrument; written apart, "does this bass
    line suit this bass" would be discovered as silence.
    """
    return DUET.read_text(), ""


def test_the_two_banks_touch_disjoint_channels():
    """Which is why merging a score with a keyboard is a lookup.

    The engine cannot tell which of its channels was written by a scheduler
    and which by a hand — so nothing has to arbitrate between them.
    """
    from gestate.audioperform import allocator_for

    synth, _ = _duet()
    bass = set(sum(allocator_for(synth, "bass").channels, []))
    lead = set(sum(allocator_for(synth, "lead").channels, []))
    assert bass and lead
    assert bass.isdisjoint(lead)


def test_a_bank_that_is_not_there_is_named():
    from gestate.audioperform import PerformError, allocator_for

    synth, _ = _duet()
    with pytest.raises(PerformError, match="no bank called `drums`"):
        allocator_for(synth, "drums")


def test_a_score_and_a_keyboard_drive_one_graph():
    """The example's whole claim, without needing a keyboard plugged in.

    Notes are injected through `Notes.feed` exactly as the listener thread
    would, so what is exercised is the merge rather than a mock of it.
    """
    from gestate.audioperform import (Performance, allocator_for,
                                      from_notes, from_schedule, graph_of,
                                      scored)

    synth, piece = _duet()
    rate, block = 4000, 64
    graph = graph_of(synth, piece, rate=rate)

    schedule, _samples, _allocs = scored(synth, piece, rate=rate, block=block)
    notes = Notes(allocator_for(synth, "lead"))
    play = Performance(graph, [from_schedule(schedule), from_notes(notes)])
    control = play.control()

    scored_only = run(graph, 600, block=block, control=control)

    # A hand arrives partway through and the sound changes — while the bass
    # line, which is on other channels entirely, does not stop.
    notes.now = 200
    notes.feed(_Message("note_on", 72, velocity=100))
    both = run(graph, 600, block=block, control=control)
    assert both != scored_only, "the keyboard changed nothing"

    assert notes.sounding() == [72]
    assert max(abs(s) for s in both) > 0.05, "silent"
    assert all(-1.0 <= s <= 1.0 for s in both), "out of range"


@needs_clang
def test_the_scored_half_is_still_bit_identical():
    """A performance is checkable even though half of it is improvised.

    The scored half is a `Schedule`, so it renders the same through the
    interpreter, the block renderer and the generated code — which is what
    makes `duet.ges` a thing that can be wrong in a way anyone notices.
    """
    from gestate.audioperform import (Performance, from_schedule, graph_of,
                                      scored)

    synth, piece = _duet()
    rate, block, samples = 4000, 64, 500
    graph = graph_of(synth, piece, rate=rate)
    schedule, _samples, _allocs = scored(synth, piece, rate=rate, block=block)
    control = Performance(graph, [from_schedule(schedule)]).control()

    from gestate.audio import render_assembled
    from gestate.audioscore import assemble_performance

    # The performance assembly, not the plain one: this program carries a
    # piece, so `'` and `>>=` have to exist for the oracle too.
    oracle = render_assembled(assemble_performance(synth, piece, rate),
                              samples / rate, rate,
                              control_every=block, schedule=schedule)
    assert run(graph, samples, block=block, control=control) == oracle
    with tempfile.TemporaryDirectory() as d:
        assert run_native(graph, d, samples, block=block,
                          control=control) == oracle


def test_the_example_renders_from_the_command_line(tmp_path, capsys):
    from gestate.audioperform import main

    out = tmp_path / "duet.wav"
    assert main([str(DUET), "-o", str(out),
                 "--rate", "4000", "--seconds", "0.5"]) == 0
    assert out.exists() and out.stat().st_size > 1000
