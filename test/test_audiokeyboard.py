"""The on-screen keyboard — `audioeditor.Keyboard`.

Headless, and that is the design rather than a convenience.  The half worth
testing is *what a key means*: which note a typed character plays, which are
held, whether a bank will take one, and what happens to a note nobody
released.  None of that is a rectangle, so none of it needs a window — the
`Canvas` in `Editor` is rectangles and event plumbing over this.

**What it must not have is a path of its own.**  A virtual key goes to
`audiomidi.Notes.feed`, the same method a real one goes to, and the engine
cannot tell them apart.  That is the claim `duet.ges` makes from the other
direction — a note is the same thing whether a schedule or a hand decided
it — so the tests below feed a keyboard and assert against the *allocator*,
which is what a score writes to as well.
"""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest

from gestate.audioeditor import Keyboard, Workbench

AUDIO_DIR = Path(__file__).resolve().parent.parent / "examples" / "audio"

needs_clang = pytest.mark.skipif(shutil.which("clang") is None,
                                 reason="no clang to build the engine with")


class _Bench:
    """Just enough `Workbench` for a keyboard: a `notes`, or nothing."""

    def __init__(self, notes=None):
        self.notes = notes


def _notes(banks: dict):
    """A `Notes` over one allocator per named bank, with no port anywhere."""
    from gestate.audioalloc import Allocator
    from gestate.audiomidi import Notes

    return Notes({name: Allocator(chans) for name, chans in banks.items()})


#: Three voices of two fields each — `gateAt`/`offAt` plus a pitch, which is
#: the shape `channels_of` produces for a one-field payload.
ONE_BANK = {"lead": [[f"leadGate{i}", f"leadOff{i}", f"leadPitch{i}"]
                     for i in range(3)]}


# ── What a key means ────────────────────────────────────────────────────────


def test_the_home_row_is_an_octave_from_middle_c():
    """`z` is middle C, and the row walks up a semitone at a time."""
    board = Keyboard(_Bench())
    assert board.key_for("z") == 60
    assert [board.key_for(c) for c in board.LOWER] == list(range(60, 73))


def test_the_upper_row_is_the_same_octave_higher():
    board = Keyboard(_Bench())
    assert [board.key_for(c) for c in board.UPPER] == list(range(72, 85))


def test_a_character_that_is_not_a_key_plays_nothing():
    board = Keyboard(_Bench())
    for char in ("", " ", "1", "/", "\n", None):
        assert board.key_for(char) is None


def test_the_layout_is_case_insensitive():
    """Caps lock is not a transposition."""
    board = Keyboard(_Bench())
    assert board.key_for("Z") == board.key_for("z")


def test_the_octave_control_moves_the_whole_layout():
    board = Keyboard(_Bench())
    assert board.transpose(1) == 5
    assert board.key_for("z") == 72
    assert board.transpose(-2) == 3
    assert board.key_for("z") == 48


def test_the_octave_control_stops_at_the_ends_of_midi():
    """A key number below 0 or above 127 is not a note anything can play."""
    board = Keyboard(_Bench())
    for _ in range(20):
        board.transpose(-1)
    assert board.octave == 0 and board.key_for("z") == 12
    for _ in range(40):
        board.transpose(1)
    assert board.octave == 9 and board.key_for("z") == 120


# ── Playing ─────────────────────────────────────────────────────────────────


def test_a_press_reaches_the_allocator_and_a_release_hands_it_back():
    notes = _notes(ONE_BANK)
    board = Keyboard(_Bench(notes))

    assert board.press(60) is True
    assert notes.sounding_on("lead") == [60]
    assert board.release(60) is True
    assert notes.sounding_on("lead") == []


def test_several_keys_at_once_take_several_voices():
    """Which is the whole point of playing one rather than a score."""
    notes = _notes(ONE_BANK)
    board = Keyboard(_Bench(notes))
    for note in (60, 64, 67):
        board.press(note)
    assert notes.sounding_on("lead") == [60, 64, 67]
    assert board.sounding() == {60, 64, 67}


def test_auto_repeat_does_not_retrigger_a_held_key():
    """**The reason `held` exists.**

    X11 sends `KeyPress`/`KeyRelease` pairs while a key is down, so a
    keyboard that forwarded events raw would start the same note dozens of
    times a second and spend every voice in the bank on one finger.
    """
    notes = _notes(ONE_BANK)
    board = Keyboard(_Bench(notes))

    assert board.press(60) is True
    for _ in range(50):
        assert board.press(60) is False, "a repeat was treated as a new press"
    assert notes.sounding_on("lead") == [60], "one key took several voices"
    assert notes.notes == 1, "the note was fed more than once"


def test_releasing_a_key_that_was_never_down_does_nothing():
    notes = _notes(ONE_BANK)
    board = Keyboard(_Bench(notes))
    assert board.release(60) is False
    assert notes.notes == 0


def test_all_off_releases_everything_and_forgets_it():
    """What a window losing focus has to do.

    A `KeyRelease` goes to whatever has focus *now*, so a note held across
    a click away would never be released and its voice never handed back.
    """
    notes = _notes(ONE_BANK)
    board = Keyboard(_Bench(notes))
    for note in (60, 64, 67):
        board.press(note)

    board.all_off()
    assert board.sounding() == set()
    assert notes.sounding_on("lead") == []


def test_transposing_releases_what_is_held():
    """The key that would end the note has just changed pitch.

    Carried across a transpose, a note would have no key left to release
    it — which is the same hanging voice `all_off` exists to prevent, one
    layer up.
    """
    notes = _notes(ONE_BANK)
    board = Keyboard(_Bench(notes))
    board.press(60)
    board.transpose(1)
    assert notes.sounding_on("lead") == [], "the note was left hanging"
    assert board.sounding() == set()


# ── By physical key — where the sticking bug lived ──────────────────────────


def test_a_key_releases_the_note_it_started():
    notes = _notes(ONE_BANK)
    board = Keyboard(_Bench(notes))

    assert board.press_key("z", "z") == 60
    assert notes.sounding_on("lead") == [60]
    assert board.release_key("z") == 60
    assert notes.sounding_on("lead") == []


def test_a_release_with_no_character_still_ends_the_note():
    """**The bug that made keys stick.**

    X11 delivers `KeyRelease` with an empty `char` often enough to matter,
    and the note used to be recomputed from that character — so the release
    resolved to no note at all and the voice was never handed back.  The
    keysym is the same string on both events, so it is what is remembered.
    """
    notes = _notes(ONE_BANK)
    board = Keyboard(_Bench(notes))
    board.press_key("z", "z")

    assert board.release_key("z", char="") == 60, "the note did not release"
    assert notes.sounding_on("lead") == []
    assert board.sounding() == set()


def test_a_key_held_across_an_octave_change_does_not_stick():
    """The other half of the same bug.

    Recomputed from the character, `z` after `transpose(1)` is note 72 —
    so releasing it would have ended a note that was never playing and
    left note 60 sounding for ever.
    """
    notes = _notes(ONE_BANK)
    board = Keyboard(_Bench(notes))
    board.press_key("z", "z")
    board.transpose(1)

    assert notes.sounding_on("lead") == [], "transposing left it hanging"
    assert board.release_key("z") is None, "it was already released"
    assert notes.sounding_on("lead") == []


def test_shift_does_not_orphan_a_held_key():
    """A modifier pressed mid-note changes `char` but not `keysym`."""
    notes = _notes(ONE_BANK)
    board = Keyboard(_Bench(notes))
    board.press_key("z", "z")
    assert board.release_key("z", char="Z") == 60
    assert notes.sounding_on("lead") == []


def test_pressing_a_key_that_is_already_down_is_ignored():
    """Auto-repeat at this level: the same keysym twice is one note."""
    notes = _notes(ONE_BANK)
    board = Keyboard(_Bench(notes))
    assert board.press_key("z", "z") == 60
    assert board.press_key("z", "z") is None
    assert notes.notes == 1
    assert notes.sounding_on("lead") == [60]


def test_a_key_that_plays_nothing_is_not_remembered():
    """Otherwise `is_down` would be true for every key on the keyboard."""
    board = Keyboard(_Bench(_notes(ONE_BANK)))
    assert board.press_key("1", "1") is None
    assert not board.is_down("1")
    assert board.release_key("1") is None


def test_a_key_nothing_played_is_still_a_key_that_is_down():
    """`_by_key` is a fact about the hand, not about the synth.

    A bank switched off takes no note, but the finger is still on the key —
    and step mode writes what you played whether or not it sounded, so the
    note comes back either way.  Forgetting the key here would also leave
    the *release* unmatched, and the next press of it would be read as a
    repeat.
    """
    notes = _notes(ONE_BANK)
    notes.listening["lead"] = False
    board = Keyboard(_Bench(notes))

    assert board.press_key("z", "z") == 60, "step mode has nothing to write"
    assert board.is_down("z")
    assert board.sounding() == set(), "it sounded after all"
    assert board.press_key("z", "z") is None, "a repeat was read as a press"
    assert board.release_key("z") == 60


def test_all_off_forgets_the_physical_keys_too():
    """Or a later `KeyRelease` would release a note somebody else started."""
    notes = _notes(ONE_BANK)
    board = Keyboard(_Bench(notes))
    board.press_key("z", "z")
    board.all_off()

    assert not board.is_down("z")
    assert board.release_key("z") is None


def test_a_keyboard_with_no_banks_is_silent_rather_than_an_error():
    """A synth with no `voices` has nothing to play, and says so by
    refusing the note rather than by raising in an event handler."""
    board = Keyboard(_Bench(None))
    assert board.press(60) is False
    assert board.sounding() == set()
    assert board.release(60) is False


def test_the_velocity_is_what_reaches_the_payload():
    """A bank whose payload carries velocity gets the one that was set."""
    from gestate.audioalloc import Allocator
    from gestate.audiomidi import Notes

    banks = {"lead": [[f"g{i}", f"o{i}", f"p{i}", f"v{i}"] for i in range(2)]}
    notes = Notes({n: Allocator(c) for n, c in banks.items()})
    board = Keyboard(_Bench(notes), velocity=42)
    board.press(60)
    assert notes.values["p0"] == 60
    assert notes.values["v0"] == 42


def test_the_midi_channel_is_what_routes_between_banks():
    """Two banks and no `FromMIDI` means `by_midi_channel` decides.

    The channel is a real setting rather than a formality: it is what
    chooses which bank an on-screen key plays.
    """
    notes = _notes({"lead": [["lg0", "lo0", "lp0"]],
                    "bass": [["bg0", "bo0", "bp0"]]})
    Keyboard(_Bench(notes), channel=1).press(60)
    assert notes.sounding_on("bass") == [60]
    assert notes.sounding_on("lead") == []


# ── The switch is still authoritative ───────────────────────────────────────


def test_a_bank_switched_off_takes_no_keys():
    """The on-screen keyboard is the same writer as the MIDI one.

    Two writers on one set of channels is a fight, which is what the
    switch exists to settle — and a keyboard that went around it would
    reopen exactly that.
    """
    notes = _notes(ONE_BANK)
    notes.listening["lead"] = False
    board = Keyboard(_Bench(notes))

    assert board.press(60) is False
    assert notes.sounding_on("lead") == []
    assert board.sounding() == set(), "it counted a note nothing took"


# ── Against a real workbench ────────────────────────────────────────────────


def _bench(tmp_path, name: str) -> Workbench:
    """A workbench with its program *read* but nothing playing.

    `start()` compiles an engine and opens a player, and none of that is
    needed to answer what a key does — but the four steps below are, and
    in this order: `_place` fills `banks`, which `_load_from_midi` needs to
    know which banks have a `FromMIDI` instance, which `_start_notes` needs
    to decide whether a bank can take a note at all.
    """
    path = tmp_path / name
    path.write_text((AUDIO_DIR / name).read_text())
    bench = Workbench(path, rate=8000, block=64, command=["cat"])
    text = path.read_text()
    bench._place(text)
    bench._load_score(text)
    bench._load_from_midi(text)
    bench._start_notes()
    return bench


def test_the_note_plumbing_exists_without_a_midi_port(tmp_path):
    """**The change that made the keyboard possible.**

    `Notes` and the allocators used to be built inside the `try` that opens
    a MIDI port, and only when `--midi` was passed — so an ordinary editor
    session had no allocators and a key press had nothing to reach.
    """
    bench = _bench(tmp_path, "duet.ges")

    assert bench.notes is not None
    assert set(bench.notes.allocators) == {"lead", "bass"}
    assert bench.listener is None, "it opened a port after all"


def test_a_scored_bank_still_starts_switched_off(tmp_path):
    """Seeding moved into `start`, and must still mean what it meant.

    `duet.ges`'s `bass` is driven by its own score, so the keyboard does
    not get it until you say so.
    """
    bench = _bench(tmp_path, "duet.ges")

    assert bench.listening("lead"), "the unscored bank should start on"
    assert not bench.listening("bass"), "the scored bank should start off"


def test_playing_a_library_example_from_the_keyboard(tmp_path):
    """`polysaw.ges`, played by hand rather than by its score.

    Eight voices and a `FromMIDI` instance, so this exercises the whole
    path a person actually uses: press three keys, three voices sound.
    """
    bench = _bench(tmp_path, "polysaw.ges")
    bench.listen("poly", True)              # its own score drives it otherwise

    for note in (60, 64, 67):
        assert bench.keyboard.press(note) is True
    assert bench.notes.sounding_on("poly") == [60, 64, 67]

    bench.keyboard.all_off()
    assert bench.notes.sounding_on("poly") == []
