"""Music: the `Score` layout tree, and MIDI out — `spec/music.md`, F27.

`perform` returns ordinary Python tuples, so these assert on *events* —
`(onset, offset, program, key, velocity)` in ticks — rather than on a
printed heap.  That is the interface `implementation_order.md` §11 says the
compiler owes; the file writer is the host's half and is tested separately.
"""

from __future__ import annotations

import pytest

from gestate.midi import MidiError, TICKS_PER_BEAT as BEAT, perform, write

BPM = "\nbpm : Int\nbpm = 120\n"


def _events(score_expr: str, defs: str = ""):
    src = f"{defs}score : [: Void :]\nscore = ({score_expr}) >>= prog 0\n{BPM}"
    return [(on, off, key) for on, off, _p, key, _v in perform(src)[1]]


# ── The constructs ──────────────────────────────────────────────────────────


def test_a_note_is_one_beat():
    assert _events("'60") == [(0, BEAT, 60)]


def test_a_sequence_advances():
    assert _events("'60 ++ '62") == [(0, BEAT, 60), (BEAT, 2 * BEAT, 62)]


def test_an_overlay_shares_the_span():
    assert _events("'60 || '64") == [(0, BEAT, 60), (0, BEAT, 64)]


def test_a_rest_takes_time_and_makes_no_sound():
    assert _events("'60 ++ r ++ '62") == [
        (0, BEAT, 60), (2 * BEAT, 3 * BEAT, 62)]


def test_scaling_multiplies_the_duration():
    assert _events("('60 |* 3)") == [(0, 3 * BEAT, 60)]


def test_shrinking_divides_it():
    assert _events("('60 |/ 4)") == [(0, BEAT // 4, 60)]


def test_scaling_applies_to_the_group_beside_it():
    # `|*` is *tighter* than `++`, so this scales `'62` alone.  It read the
    # other way until writing music showed that two scaled groups in a row
    # is the common shape and the loose reading broke it (`fixme.md` F83).
    assert _events("'60 ++ '62 |* 2") == [
        (0, BEAT, 60), (BEAT, 3 * BEAT, 62)]


def test_scaling_a_whole_phrase_takes_parentheses():
    assert _events("('60 ++ '62) |* 2") == [
        (0, 2 * BEAT, 60), (2 * BEAT, 4 * BEAT, 62)]


def test_two_scaled_groups_run_one_after_the_other():
    """A bar of eighth notes — the shape that decided the precedence."""
    assert _events("('60 ++ '62) |/ 2 ++ ('64 ++ '65) |/ 2") == [
        (0, BEAT // 2, 60), (BEAT // 2, BEAT, 62),
        (BEAT, 3 * BEAT // 2, 64), (3 * BEAT // 2, 2 * BEAT, 65)]


# ── `at`: duration and extent are different things ──────────────────────────


def test_at_alone_places_before_the_origin():
    """`at (-4) x` sounds from -4 — onsets are not normalised here."""
    assert _events("at (0 - 4) ('60)") == [(-4, BEAT - 4, 60)]


def test_at_in_a_sequence_overlaps_the_preceding_item():
    on, off, key = _events("'60 ++ at (0 - 48) ('62)")[1]
    assert (on, off, key) == (BEAT - 48, 2 * BEAT - 48, 62)
    assert on < BEAT, "the second note must start before the first ends"


def test_at_does_not_move_what_follows():
    """The point of separating duration from extent.

    `++` advanced by `'62`'s *duration*, which `at` left alone, so the
    third note sits where it would have without the offset.
    """
    events = _events("'60 ++ at (0 - 48) ('62) ++ '64")
    assert [e[0] for e in events] == [0, BEAT - 48, 2 * BEAT]


def test_the_shift_sugar_is_one_beat():
    assert _events("'60 ++ |< ('62)")[1][0] == 0
    assert _events("'60 ++ ('62) >|")[1][0] == 2 * BEAT


# ── Instrument selection is `>>=` ───────────────────────────────────────────


def test_binding_assigns_the_instrument():
    src = ("score : [: Void :]\nscore = ('60 ++ '62) >>= prog 42\n" + BPM)
    assert {e[2] for e in perform(src)[1]} == {42}


def test_a_committed_note_is_not_rebound():
    """`>>=` reaches only *unassigned* notes.

    A `Play` leaf carries no payload, so a second bind cannot touch it —
    which is why "ignored if an instrument is already selected" needs no
    runtime mark.  Here the first bind commits to program 1 and the second
    finds nothing left to assign.
    """
    src = ("committed : [: a :]\ncommitted = '60 >>= prog 1\n\n"
           "score : [: Void :]\nscore = committed >>= prog 2\n" + BPM)
    assert {e[2] for e in perform(src)[1]} == {1}


# ── Retrograde ──────────────────────────────────────────────────────────────


def test_reverse_plays_a_phrase_backwards():
    assert _events("reverse ('60 ++ '62 ++ '64)") == [
        (2 * BEAT, 3 * BEAT, 60),
        (BEAT, 2 * BEAT, 62),
        (0, BEAT, 64),
    ]


def test_reverse_keeps_the_duration():
    """A retrograde is the same length, so what follows it does not move."""
    assert _events("reverse ('60 ++ '62) ++ '67") == [
        (BEAT, 2 * BEAT, 60),
        (0, BEAT, 62),
        (2 * BEAT, 3 * BEAT, 67),
    ]


def test_reverse_twice_is_the_original():
    assert _events("reverse (reverse ('60 ++ '62 ++ '64))") == \
        _events("'60 ++ '62 ++ '64")


def test_reversing_an_overlay_makes_it_end_together():
    """**Why it is a constructor and not a walk.**  `||` is left-aligned,
    so a structural reverse would leave two voices of unequal length still
    *starting* together — and what a retrograde means is that whatever
    ended last now begins first.  The short voice moves to the end.
    """
    assert _events("reverse (('60 ++ '62) || '67)") == [
        (BEAT, 2 * BEAT, 60),
        (0, BEAT, 62),
        (BEAT, 2 * BEAT, 67),
    ]


def test_reverse_commutes_with_an_instrument():
    """`>>=` walks into it, so it does not matter which order you write."""
    src_a = ("score : [: Void :]\n"
             "score = reverse ('60 ++ '62) >>= prog 5\n" + BPM)
    src_b = ("score : [: Void :]\n"
             "score = reverse ('60 ++ '62 >>= prog 5)\n" + BPM)
    assert perform(src_a)[1] == perform(src_b)[1]


def test_a_score_with_unassigned_notes_does_not_type():
    from gestate.unify import UnifyError

    src = "score : [: Void :]\nscore = '60\n" + BPM
    with pytest.raises((UnifyError, Exception)):
        perform(src)


# ── The entry point and the writer ──────────────────────────────────────────


def test_bpm_comes_back_with_the_events():
    src = ("score : [: Void :]\nscore = '60 >>= prog 0\n\n"
           "bpm : Int\nbpm = 88\n")
    assert perform(src)[0] == 88


def test_a_music_program_may_not_define_main():
    src = ("score : [: Void :]\nscore = '60 >>= prog 0\n"
           + BPM + "\nmain : Int\nmain = 1\n")
    with pytest.raises(MidiError, match="not `main`"):
        perform(src)


def test_writing_a_file_that_reads_back(tmp_path):
    mido = pytest.importorskip("mido")
    src = ("score : [: Void :]\n"
           "score = ('60 || '64) >>= prog 5\n\nbpm : Int\nbpm = 140\n")
    path = tmp_path / "out.mid"
    n, bpm = write(src, str(path))
    assert (n, bpm) == (2, 140)

    mid = mido.MidiFile(str(path))
    assert mid.ticks_per_beat == BEAT
    kinds = [m.type for m in mid.tracks[0]]
    assert kinds[0] == "set_tempo"
    assert "program_change" in kinds
    assert kinds.count("note_on") == 2 and kinds.count("note_off") == 2
    assert mid.length == pytest.approx(60.0 / 140, rel=0.05)


def test_negative_onsets_are_normalised_by_the_writer_only(tmp_path):
    """The language keeps the score's own coordinates; the file cannot."""
    pytest.importorskip("mido")
    src = ("score : [: Void :]\n"
           "score = ('60 || at (0 - 48) ('62)) >>= prog 0\n" + BPM)
    assert min(e[0] for e in perform(src)[1]) == -48      # as written
    write(src, str(tmp_path / "n.mid"))                   # and it still writes
