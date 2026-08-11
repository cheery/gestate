"""The world half — `hear` and `holds` (`spec/ariadne.md`).

The stage's shape, held by tests: a probe is a leaf whose content the
world decides *at the leaf's own downbeat* — never earlier, because the
reading does not exist yet, which is what makes responsiveness the
author's written cadence rather than the performer's policy.  Readings
land in the transcript beat by beat, and the stage's oracle closes:
**a performance that listened equals its own replay**, the recorded
world standing in for the live one, change for change.

And underneath it all, the parity that keeps the new walk honest: on a
probe-free score, `liveVoices` must sound exactly `streamVoices`.
"""

from __future__ import annotations

import pytest

from test_dynamicscore import BLOCK, RATE, SYNTH, _allocators
from test_sownscore import BEAT, CHANCY

from gestate.audiodynamic import LazyPerformer, LiveStream, ScoreStream
from gestate.audioschedule import Schedule
from gestate.audioscore import ports_of, stream_root

ARP = """
step : List Int -> [: Custom :]
step ks = case ks of
    Nil -> r
    k :: kt -> do
        s <- draw
        '(Custom 0.8 (pick ks s))

pick : List Int -> Int -> Int
pick ks s = nth (below (length ks) s) ks

nth : Int -> List Int -> Int
nth n ks = case ks of
    Nil -> 0
    k :: kt -> case n < 1 of
        True -> k
        False -> nth (n - 1) kt

score : [: Void :]
score = (cycle ((do ks <- hear holds.lead; step ks) |/ 2) >>= voices.lead) || (cycle ('(Custom 0.6 36) |* 2) >>= voices.bass)

bpm : Int
bpm = 120
"""


def _performer(piece, seed, reader=None, synth=SYNTH):
    tempo, state, root, by_tag = stream_root(synth, piece, RATE, seed, 0,
                                             True)
    return LazyPerformer(LiveStream(state, root, by_tag), tempo, RATE,
                         _allocators(), block=BLOCK, reader=reader)


def _changes(performer, upto):
    out = []
    for t in range(0, upto, BLOCK):
        out += performer.advance(t)
    return out


# ── The parity underneath ───────────────────────────────────────────────────


def test_a_probe_free_score_sounds_identical_through_the_live_walk():
    """`liveVoices` is `streamVoices` with one more power; on a score
    that never uses it, the two must be the same stream — the discipline
    every second spelling in this project is held to."""
    tempo, state, root, by_tag = stream_root(SYNTH, CHANCY, RATE, 5)
    flat = LazyPerformer(ScoreStream(state, root, by_tag), tempo, RATE,
                         _allocators(), block=BLOCK)
    live = _performer(CHANCY, seed=5)

    a, b = Schedule(), Schedule()
    for t in range(0, 6 * BEAT, BLOCK):
        for boundary, chan, value in flat.advance(t):
            a.change(boundary, chan, value)
        for boundary, chan, value in live.advance(t):
            b.change(boundary, chan, value)
    assert a.changes == b.changes


# ── The arpeggiator ─────────────────────────────────────────────────────────


def test_the_arpeggiator_follows_the_hands():
    """The stage's acceptance test: held keys become a line.

    The probe listens every half beat (`|/ 2`, the author's written
    latency); the seed picks among what is held, so the line breathes;
    the bass walks on beside it un-probed — the overlay seam the cue
    merge exists for.
    """
    held: list = []
    live = _performer(ARP, seed=4, reader=lambda port, key=None: list(held))

    for t in range(0, 8 * BEAT, BLOCK):
        if t >= 2 * BEAT:
            held[:] = [60, 64, 67]
        if t >= 6 * BEAT:
            held[:] = [62, 65]
        live.advance(t)

    lead = [(e[0], e[3][0][1]) for e in live.history
            if e[2] == "lead"]
    assert lead, "nothing arpeggiated"
    assert all(tick >= 2 * 96 for tick, _p in lead), \
        "an empty world must rest, not guess"
    early = {p for tick, p in lead if tick < 6 * 96}
    late = {p for tick, p in lead if tick >= 6 * 96 + 48}
    assert early <= {60, 64, 67} and len(early) > 1, early
    assert late <= {62, 65} and late, late

    bass = [e for e in live.history if e[2] == "bass"]
    assert bass and bass[0][0] == 0, "the bass must not wait on the probe"

    readings = [e for e in live.transcript if e[0] == "reading"]
    assert readings and readings[0][1] == 0.0
    assert all(r[1] * 2 == int(r[1] * 2) for r in readings), \
        "readings land on the written cadence, every half beat"


def test_the_unheard_branch_of_an_overlay_is_unbent():
    """The listener's answers stretch its own branch and no other: the
    bass walks its written two-beat bars whatever the lead heard."""
    held: list = []
    live = _performer(ARP, seed=4, reader=lambda port, key=None: list(held))
    for t in range(0, 4 * BEAT + BLOCK, BLOCK):
        if t >= BEAT:
            held[:] = [60]
        live.advance(t)
    bass = [e[0] for e in live.history if e[2] == "bass"]
    assert bass == [0, 192, 384], bass       # unbent by the probing above


# ── The oracle ──────────────────────────────────────────────────────────────


def test_an_improvisation_equals_its_own_replay(tmp_path):
    """Stage three's whole claim in one assertion: the transcript records
    the world and the seed; everything else is arithmetic.  A performance
    that listened, replayed against its own log with no world at all,
    lands every change on the same sample with the same value."""
    from gestate.transcript import Transcript

    script = {2 * BEAT: [60, 64, 67], 5 * BEAT: [59, 62]}
    held: list = []
    live = _performer(ARP, seed=11, reader=lambda port, key=None: list(held))
    first = []
    for t in range(0, 8 * BEAT, BLOCK):
        for at, keys in script.items():
            if t >= at:
                held[:] = keys
        first += live.advance(t)
    assert any(e[0] == "reading" and e[3] for e in live.transcript)

    path = tmp_path / "improv.transcript"
    live.record.save(path)
    kept = Transcript.load(path)

    again = _performer(ARP, seed=11, reader=kept.reader_of())
    second = _changes(again, 8 * BEAT)
    assert second == first
    assert [e for e in again.transcript if e[0] == "reading"] == \
           [e for e in kept.events if e[0] == "reading"]


def test_ports_are_the_banks_in_declaration_order():
    assert ports_of(SYNTH + "\n" + ARP) == {0: "lead", 1: "bass"}


def test_an_instance_that_computes_a_field_keeps_every_field():
    """`FromMIDI` with arithmetic in it — the silent field-dropper, pinned.

    `_fields_of` used to dereference without forcing, so a field an
    instance *computed* (`Tone (toFloat v / 127.0) n`) was still a thunk
    and silently skipped: every raw-field instance in the tree worked,
    and the first computed one hit the allocator with the wrong arity.
    """
    from pathlib import Path

    from gestate.audiomidi import FromMidi
    from gestate.audioscore import assemble_performance
    from gestate.audiovoices import banks_of
    from gestate.pipeline import compile as compile_program

    source = (Path(__file__).resolve().parent.parent
              / "examples" / "audio" / "jazz.ges").read_text()
    banks = [b.name for b in banks_of(source)]
    fm = FromMidi(compile_program(assemble_performance(source, "", RATE)),
                  banks)
    payload = fm.payload_for("horn", 0, 62, 100)
    assert payload is not None, "the instance declined"
    assert len(payload) == 2, payload
    assert payload == (pytest.approx(100 / 127.0), 62)


# ── Remembering a moment ─────────────────────────────────────────────────
#
# `seek` releases what sounds and then silently replays every entry
# before the target, which is what makes seek-then-perform equal
# `value_at` — and what makes it cost more the further into a piece it
# lands.  A loop pays that on every pass, for the same instant every
# time.  The state at an instant is a pure function of what came before
# it, so it can be kept; these hold that keeping it changes nothing.

def _standing_at(performer):
    """Everything about a performer that anything downstream can see."""
    return (dict(performer.values), list(performer.pending),
            performer.position,
            {n: a.state() for n, a in performer.allocators.items()})


def test_a_restored_moment_is_the_moment_it_replaced():
    """The claim the whole optimisation rests on."""
    one = _performer(ARP, seed=7)
    _changes(one, 40 * BLOCK)
    one.seek(20 * BLOCK)
    kept = one.snapshot()
    # Wander off, far enough to disturb everything a seek establishes.
    _changes(one, 60 * BLOCK)
    assert one.restore(kept) is True
    restored = _standing_at(one)

    # A second performer that only ever seeks, never restores.
    two = _performer(ARP, seed=7)
    _changes(two, 40 * BLOCK)
    two.seek(20 * BLOCK)
    _changes(two, 60 * BLOCK)
    two.seek(20 * BLOCK)
    assert restored == _standing_at(two)


def test_performing_on_from_a_restored_moment_matches():
    """Not just the state — what it goes on to play."""
    one = _performer(ARP, seed=7)
    _changes(one, 40 * BLOCK)
    one.seek(20 * BLOCK)
    kept = one.snapshot()
    _changes(one, 60 * BLOCK)
    one.restore(kept)
    after_restore = _changes(one, 40 * BLOCK)

    two = _performer(ARP, seed=7)
    _changes(two, 40 * BLOCK)
    two.seek(20 * BLOCK)
    _changes(two, 60 * BLOCK)
    two.seek(20 * BLOCK)
    after_seek = _changes(two, 40 * BLOCK)
    assert after_restore == after_seek


def test_a_moment_from_before_the_stream_grew_is_refused():
    """**Refused rather than forced.**  The replay walks `history`, so a
    snapshot taken before it grew would put back a past missing whatever
    arrived since — a performance quietly disagreeing with its score,
    which is far worse than the seek it saves."""
    p = _performer(ARP, seed=7)
    _changes(p, 20 * BLOCK)
    p.seek(10 * BLOCK)
    kept = p.snapshot()
    assert p.restore(kept) is True, "nothing has moved yet"
    _changes(p, 200 * BLOCK)           # forces the stream much further
    assert len(p.history) > kept["history"]
    assert p.restore(kept) is False


def test_an_allocator_keeps_and_refuses_a_moment():
    from gestate.audioalloc import Allocator

    # `channels` is [[channel per field] per voice], and the first few
    # fields are the allocator's own — so a voice that carries one
    # payload value needs `PAYLOAD + 1` names.
    from gestate.audioalloc import PAYLOAD

    names = lambda i: [f"v{i}f{f}" for f in range(PAYLOAD + 1)]
    a = Allocator([names(0), names(1)])
    a.note_on("a", [1.0], 100)
    kept = a.state()
    a.note_on("b", [2.0], 200)
    a.note_off("a", 300)
    assert a.state() != kept
    assert a.restore(kept) is True
    assert a.state() == kept
    # A state that does not fit these voices is refused, never stretched.
    assert a.restore(kept[:1]) is False
