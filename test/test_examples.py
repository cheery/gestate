"""Every file in `examples/` runs — `fixme.md` F29.

An example that has quietly stopped working is worse than no example, so
these are executed rather than admired.  Each assertion is the *result* the
example's comments claim, not merely "it compiled".

Writing the examples is what found F70, F71, F72 and two defects in the
`typecheck` CLI: the suite had 653 tests and none of them wrote a program
the way someone reading the specs would.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from gestate.midi import perform
from gestate.pipeline import evaluate

EXAMPLES = Path(__file__).resolve().parent.parent / "examples"

#: Music programs define `score`/`bpm` and live in `examples/music/`.
MUSIC_DIR = EXAMPLES / "music"

LANGUAGE = {"closure.ges", "relations.ges", "signals.ges", "records.ges"}
MUSIC = {"scale.ges", "chords.ges", "canon.ges", "arpeggio.ges", "drums.ges",
         "nocturne.ges", "passacaglia.ges", "duetline.ges"}


def _source(name: str) -> str:
    root = MUSIC_DIR if name in MUSIC else EXAMPLES
    return (root / name).read_text()


def test_every_example_is_covered_by_this_file():
    """A new example must be exercised, not just added."""
    assert {p.name for p in EXAMPLES.glob("*.ges")} == LANGUAGE
    assert {p.name for p in MUSIC_DIR.glob("*.ges")} == MUSIC


# ── Datafun ─────────────────────────────────────────────────────────────────


def test_closure_computes_the_transitive_closure():
    """0→1→2→3 closes to the six ordered pairs i<j."""
    out = evaluate(_source("closure.ges"))
    assert out.count("Pack{1,2}") == 6
    assert out.startswith("Pack{1,2} (0, 1)")


def test_relations_runs_a_product_fixpoint_and_a_user_type_set():
    # `main` asks whether Red is in the set of colours below Blue.
    assert evaluate(_source("relations.ges")) == "True"


# ── FRP ─────────────────────────────────────────────────────────────────────


def test_signals_builds_a_signal_that_advances():
    from gestate.gmachine import NNum
    from gestate.pipeline import compile
    from gestate.reactive import init_program, react

    state = compile(_source("signals.ges"))
    reactive = init_program(state)
    doubled = state.now[-1]

    for value in (5, 7):
        react(reactive, [(0, value)])
        assert isinstance(doubled.value, NNum)
        assert doubled.value.n == value * 2


# ── Language surface ────────────────────────────────────────────────────────


def test_records_projects_and_derives():
    # `(norm (Point 3 4), (Point 1 2).1)` — 3² + 4², and the second field.
    assert evaluate(_source("records.ges")) == "(25, 2)"


# ── Music ───────────────────────────────────────────────────────────────────


def test_scale_is_eight_notes_one_beat_apart():
    bpm, events = perform(_source("scale.ges"))
    assert bpm == 120
    assert [e[3] for e in events] == [60, 62, 64, 65, 67, 69, 71, 72]
    assert [e[0] for e in events] == [96 * i for i in range(8)]


def test_chords_overlays_scales_and_offsets():
    """The three things `at` is for, in one score."""
    bpm, events = perform(_source("chords.ges"))
    assert bpm == 100

    onsets = sorted({e[0] for e in events})
    assert onsets == [0, 48, 192]

    # The opening triad shares a span …
    assert sorted(e[3] for e in events if e[0] == 0) == [60, 64, 67]
    # … the offset note starts *before* it ends, overlapping …
    grace = next(e for e in events if e[0] == 48)
    assert grace[1] > 96, "the grace note must overlap the chord"
    # … and the final chord is unmoved by that offset, because `at`
    # translates the extent and leaves the duration alone.
    final = [e for e in events if e[0] == 192]
    assert len(final) == 3
    assert all(e[1] - e[0] == 192 for e in final), "…and is scaled by |* 2"


def test_a_music_example_writes_a_file(tmp_path):
    mido = pytest.importorskip("mido")
    from gestate.midi import write

    out = tmp_path / "scale.mid"
    n, bpm = write(_source("scale.ges"), str(out))
    assert (n, bpm) == (8, 120)
    assert mido.MidiFile(str(out)).ticks_per_beat == 96


# ── The CLIs the examples tell you to use ───────────────────────────────────


def test_canon_is_one_theme_against_itself():
    """`at` and `||` together: the same score, entering two bars late."""
    _bpm, events = perform(_source("canon.ges"))
    voices = {}
    for on, _off, prog, key, _v in events:
        voices.setdefault(prog, []).append((on, key))
    assert len(voices) == 2, "each voice binds its own instrument"

    lead, follow = (sorted(v) for v in
                    sorted(voices.values(), key=lambda v: min(o for o, _ in v)))
    assert [k for _o, k in lead] == [k for _o, k in follow], "same theme"
    offset = min(o for o, _ in follow) - min(o for o, _ in lead)
    assert offset == 2 * 4 * 96, "two bars late"


def test_arpeggio_divides_a_beat_exactly():
    """`|/ 4` gives sixteenths of 24 ticks — 96 was chosen so it divides."""
    _bpm, events = perform(_source("arpeggio.ges"))
    figure = [e for e in events if e[2] == 11]
    assert all(e[1] - e[0] == 96 // 4 for e in figure)
    assert len({e[2] for e in events}) == 2, "figure and bass differ"


def test_drums_are_percussion_and_the_fill_is_early():
    """The case `at` exists for, end to end.

    Every event is percussion (no program number), the fill overlaps the
    groove that precedes it, and the crash after it is *unmoved* — because
    `at` translates the extent and leaves the duration alone.
    """
    _bpm, events = perform(_source("drums.ges"))
    assert all(e[2] is None for e in events), "all percussion"

    groove_end = 4 * 96
    # Four sixteenth snares, whose *origin* would have been `groove_end`
    # and which `at (-beat)` moved a beat earlier — so they overlap the
    # groove's final beat rather than following it.
    # (a *set*: the groove's own backbeat snare lands on 288 as well, and
    # coincides with the fill's first stroke.)
    fill = sorted({e[0] for e in events
                   if e[3] == 38 and e[0] >= groove_end - 96})
    assert fill == [groove_end - 96 + 24 * i for i in range(4)], fill
    assert fill[0] < groove_end, "the fill must start before the groove ends"

    crash = max(events, key=lambda e: e[0])
    assert crash[3] == 49
    assert crash[0] == groove_end + 96, "the crash is not dragged early"


def test_nocturne_is_a_full_arrangement_on_the_grid():
    """The long example: five voices, five sections, nothing off the beat.

    Its two bugs while being written are what this pins.  `grooveFill` was
    `groove ++ fill`, which made the drum phrase five beats — and since a
    section lasts as long as its longest voice, every later section started
    two beats late.  And the hats covered half a bar rather than all of it.
    Both are invisible in a note list and obvious in a grid check.
    """
    beat = 96
    bar = 4 * beat
    bpm, events = perform(_source("nocturne.ges"))
    assert bpm == 96

    by_program = {}
    for on, _off, prog, _key, _vel in events:
        by_program.setdefault(prog, []).append(on)
    # strings, bass, flute, piano, percussion — five channels' worth.
    assert len(by_program) == 5

    # Every voice starts on a bar line, and the piece is a whole number of
    # bars long.  A voice that drifts shows up here and nowhere else.
    for prog, onsets in by_program.items():
        assert min(onsets) % bar == 0, f"program {prog} enters off the grid"
    assert max(off for _on, off, _p, _k, _v in events) % bar == 0

    # The arrangement builds: harmony and bass alone for four bars, then
    # the tune and drums, then the piano.
    entries = {prog: min(ons) // bar for prog, ons in by_program.items()}
    assert entries[48] == 0 and entries[33] == 0, "strings and bass open"
    assert entries[73] == 4 and entries[None] == 4, "tune and kit at bar 4"
    assert entries[4] == 12, "piano at the middle section"

    # Eight hats to the bar, not four.
    hats = sorted(on for on, _o, prog, key, _v in events
                  if prog is None and key == 42)
    first_bar = [h for h in hats if bar * 4 <= h < bar * 5]
    assert len(first_bar) == 8, first_bar


def test_passacaglia_is_five_minutes_and_arrives_where_it_says():
    """The long one: 120 bars at 96 bpm, to the tick.

    A section is only as long as its longest voice, so one voice a beat out
    slides everything after it — the failure that is invisible in a note
    list and obvious in a grid.  This pins the total, the section entries,
    and the shape of the arrangement.
    """
    beat, bar = 96, 384
    bpm, events = perform(_source("passacaglia.ges"))
    assert bpm == 96
    end = max(off for _on, off, _p, _k, _v in events)
    assert end == 120 * bar, "not exactly 120 bars"
    assert end * 60 // (beat * bpm) == 300, "not exactly five minutes"

    at = {}
    for on, _off, prog, _key, _vel in events:
        at.setdefault(prog, []).append(on)
    for prog, onsets in at.items():
        assert min(onsets) % bar == 0, f"program {prog} enters off the grid"

    strings, bass, piano, harp, flute, drums = 48, 33, 4, 46, 73, None
    entries = {p: min(o) // bar for p, o in at.items()}
    assert entries[strings] == 0 and entries[bass] == 0
    assert entries[flute] == 8, "the tune arrives with the first verse"
    assert entries[piano] == 24
    assert entries[harp] == 56

    def voices(a, b):
        return {p for on, _o, p, _k, _v in events if a * bar <= on < b * bar}

    # The arrangement builds and thins: `quiet` is the only section without
    # drums, `finale` the only one with every voice.
    assert drums not in voices(72, 88), "the quiet section has drums"
    assert len(voices(88, 104)) == 6, "the finale is not the full band"
    assert len(voices(0, 8)) == 3, "the intro is not sparse"


# ── The rendered files are golden ───────────────────────────────────────────


@pytest.mark.parametrize("name", sorted(MUSIC))
def test_the_committed_midi_file_is_what_renders_today(name, tmp_path):
    """Rendering is byte-deterministic, so the `.mid` files are golden.

    A change to layout, tick arithmetic, event ordering or channel
    allocation shows up here as a diff in a file you can also listen to —
    which is a more useful golden artifact than the ASTs F29 asked for.
    """
    pytest.importorskip("mido")
    from gestate.midi import write

    fresh = tmp_path / name.replace(".ges", ".mid")
    write(_source(name), str(fresh))
    committed = MUSIC_DIR / name.replace(".ges", ".mid")
    assert committed.exists(), f"{committed.name} has not been rendered"
    assert fresh.read_bytes() == committed.read_bytes(), (
        f"{committed.name} is stale — re-render with "
        f"`python -m gestate.midi examples/music/{name}`"
    )


def test_percussion_lands_on_the_reserved_channel():
    """General MIDI puts the kit on channel 9; anywhere else is pitched."""
    mido = pytest.importorskip("mido")

    mid = mido.MidiFile(str(MUSIC_DIR / "drums.mid"))
    channels = {m.channel for m in mid.tracks[0] if hasattr(m, "channel")}
    assert channels == {9}
    assert not [m for m in mid.tracks[0] if m.type == "program_change"], (
        "the kit is selected by the channel, not by a program change")


def test_the_typecheck_cli_accepts_every_non_music_example():
    """`--check` exits 0 and prints nothing.

    It used to die with `NameError: check_scs`, and once that was fixed it
    reported `No instance for Eq a` on *every* program — it solved the
    constraints an SC's own context grants, which `pipeline.compile`
    filters.  The crash had been masking the false positive.
    """
    from gestate.typecheck import main as typecheck_main

    for name in sorted(LANGUAGE):
        assert typecheck_main([str(EXAMPLES / name), "--check"]) == 0, name


def test_the_midi_cli_renders_an_example(tmp_path, capsys):
    pytest.importorskip("mido")
    from gestate.midi import main as midi_main

    out = tmp_path / "out.mid"
    assert midi_main([str(MUSIC_DIR / "scale.ges"), "-o", str(out)]) == 0
    assert out.exists()
    assert "8 event(s) at 120 bpm" in capsys.readouterr().out


def test_the_midi_cli_reports_a_bad_program(tmp_path, capsys):
    from gestate.midi import main as midi_main

    bad = tmp_path / "bad.ges"
    bad.write_text("score : [: Void :]\nscore = '60\n\nbpm : Int\nbpm = 120\n")
    assert midi_main([str(bad)]) == 1
    assert "gestate:" in capsys.readouterr().err


# ── Every audio example compiles ────────────────────────────────────────────
#
# **The gap that let a broken example sit in the tree.**  This file covered
# `examples/*.ges` and `examples/music/*.ges`; `examples/audio/*.ges` was
# checked only where a golden buffer happened to exist, and `quartet.ges`
# has none — so when `synth.ges` gained a `chorus` effect and collided with
# that piece's `chorus` section, nothing said so.  Twenty-two files, one
# parse each, and the next collision is caught the moment it lands.

AUDIO_DIR = EXAMPLES / "audio"


def _audio_example_names() -> list:
    return sorted(p.name for p in AUDIO_DIR.glob("*.ges"))


CONTRIB = EXAMPLES / "contrib"


def _contrib_names() -> list:
    return sorted(p.name for p in CONTRIB.glob("*.ges"))


@pytest.mark.parametrize("name", _contrib_names())
def test_every_contributed_song_compiles(name):
    """**Compiled, not rendered**, and that is deliberate.

    These are minute-long pieces with two dozen voices each; rendering one
    is tens of seconds, and this suite already has three tests that are
    half of its runtime.  What breaks a contributed song is a change to the
    library or the assembly, and compiling catches every one of those — a
    render would catch the same faults and charge four minutes for it.
    """
    import re

    from gestate.audioscore import assemble_performance
    from gestate.pipeline import analyse

    source = (CONTRIB / name).read_text()
    # **Which assembly, decided by whether the song has instruments.**  A
    # song that declares `voices` is played by gestate and is assembled the
    # way `audioperform` assembles one; a song that has not been given
    # instruments yet is still a *MIDI* piece, and `assemble_performance`
    # would look for a `Voice` type the expander never generated for it.
    # Both are real states for a file in this directory to be in.
    if re.search(r"^voices\s", source, re.M):
        analyse(assemble_performance(source, "", 44100))
    else:
        from gestate.midi import perform

        perform(source)


@pytest.mark.parametrize("name", _audio_example_names())
def test_every_audio_example_compiles(name):
    """Through the assembly the *tools* use, which is the point: a program
    with a `score` is assembled with the music prelude and the voices
    machinery, and one without is not.  Checking them all the same way
    would be checking programs nobody runs."""
    from gestate.audio import assemble
    from gestate.audioperform import has_score
    from gestate.audioscore import assemble_performance
    from gestate.pipeline import analyse

    source = (AUDIO_DIR / name).read_text()
    text = (assemble_performance(source, "", 44100) if has_score(source)
            else assemble(source, 44100))
    analyse(text)


def test_the_audio_examples_are_actually_being_found():
    """A glob that matched nothing would make the test above vacuous and
    green, which is the failure mode a parametrised sweep has."""
    names = _audio_example_names()
    assert len(names) >= 20, names
    assert "quartet.ges" in names, "the example the sweep exists for"


# ── Every canvas example actually draws ─────────────────────────────────────
#
# **Compiling is not enough**, and that gap has now been fallen through
# twice.  `Workbench._load_substrate` builds the canvas inside a broad
# `except` — a canvas that will not compile must not stop the instrument —
# so a fault in the *editor* comes out as `"no canvas: …"`, a sentence that
# points at the author's file.  One misplaced line there left every
# substrate program in the tree drawing nothing while 162 tests passed.


def _canvas_example_names() -> list:
    from gestate.audio import has_substrate

    return sorted(p.name for p in AUDIO_DIR.glob("*.ges")
                  if has_substrate(p.read_text()))


@pytest.mark.parametrize("name", _canvas_example_names())
def test_every_canvas_example_builds_a_substrate(name, tmp_path):
    """Through the `Workbench`, not through `Substrate` directly: what
    broke was the editor's *setup* around it, which a direct construction
    would have skipped."""
    from gestate.audioeditor import Workbench

    source = (AUDIO_DIR / name).read_text()
    path = tmp_path / name
    path.write_text(source)
    bench = Workbench(path, rate=22050, block=256)
    bench._load_substrate(source)

    assert bench.substrate is not None, \
        f"the canvas was discarded: {bench.messages}"
    # The message is the other half: a canvas that loaded and complained is
    # a canvas that half-worked, and the complaint names the author's file.
    assert not [m for m in bench.messages if "canvas" in m], bench.messages


@pytest.mark.parametrize("name", _canvas_example_names())
def test_every_canvas_example_puts_something_on_screen(name, tmp_path):
    """A substrate that builds and draws nothing is the same to look at as
    one that did not build."""
    from gestate.audioeditor import Workbench

    source = (AUDIO_DIR / name).read_text()
    path = tmp_path / name
    path.write_text(source)
    bench = Workbench(path, rate=22050, block=256)
    bench._load_substrate(source)
    assert bench.substrate.picture(), "it drew nothing at all"


def test_the_canvas_examples_are_actually_being_found():
    """A glob that matched nothing would make both sweeps above vacuous
    and green, which is the failure mode a parametrised sweep has."""
    names = _canvas_example_names()
    assert "substrate.ges" in names and "spectrum.ges" in names, names


# ── Every long piece plays the whole way ────────────────────────────────────
#
# `examples/long/` holds the pieces too long for anything above to vouch
# for, and the defeat that named the directory's first resident is
# invisible to every sweep in this file: `sauna.ges`'s diverging twin
# (`specimens/sauna_specimen.ges`) compiles cleanly and then sits silent
# forever, the stream walk stalled on a clipped `cycle` of rests before
# its first cue.  Compiling is not playing.  So each piece here is
# *performed*, headless, through the portal `audioperform -o` uses — and
# the walk runs for exactly the length the file's own header tells a
# person to render (the `--seconds N` in its run line), because that is
# the promise the header makes.

LONG_DIR = EXAMPLES / "long"

#: Low and blocky: no audio is rendered, so the rate only paces the
#: clock, and the walk's work is the score's own size either way —
#: `sauna.ges`'s twenty minutes cost about ten seconds here.
LONG_RATE, LONG_BLOCK = 4000, 256


def _long_names() -> list:
    return sorted(p.name for p in LONG_DIR.glob("*.ges"))


def _stated_seconds(source: str, name: str) -> int:
    m = re.search(r"--seconds\s+(\d+)", source)
    assert m, (f"{name} has no `--seconds N` render line in its header — "
               f"the sweep plays exactly what the file tells a person to "
               f"render, so say it")
    return int(m.group(1))


@pytest.mark.parametrize("name", _long_names())
def test_every_long_piece_plays_the_whole_way(name):
    from gestate.audioperform import dynamic
    from gestate.midi import TICKS_PER_BEAT

    source = (LONG_DIR / name).read_text()
    seconds = _stated_seconds(source, name)
    performer, _allocators = dynamic(source, rate=LONG_RATE,
                                     block=LONG_BLOCK)

    samples = LONG_RATE * seconds
    seen = 0
    for t in range(0, samples + LONG_BLOCK, LONG_BLOCK):
        performer.advance(t)
        # At the *first* confession, not at the end: a stalled walk
        # burns its whole fuel budget every block from there on, so
        # riding one to the final bar would take minutes to say what
        # the first stall already said.
        if len(performer.transcript) > seen:
            fresh = performer.transcript[seen:]
            seen = len(performer.transcript)
            stall = next((e for e in fresh if e[0] == "stall"), None)
            assert stall is None, f"{name} stalls at beat {stall[1]:.1f}"

    assert performer.history, f"{name} played no events at all"
    # The same tally `audioperform -o` speaks after a render: a piece
    # that dropped notes or ran a bank dry played, but not the piece
    # its author shipped.
    assert performer.record.confessions() == {}, \
        performer.record.confessions()

    # And played *to the end*: a piece that goes quiet halfway is the
    # stall's defeat wearing a green suit.  The last tenth is grace for
    # an ending that rings out.
    final_beat = performer._tick_at(samples) / TICKS_PER_BEAT
    last_beat = max(e[0] for e in performer.history) / TICKS_PER_BEAT
    assert last_beat >= final_beat * 0.9, \
        (f"{name} fell silent at beat {last_beat:.1f} of "
         f"{final_beat:.1f}")


def test_the_long_pieces_are_actually_being_found():
    """The vacuity guard the other sweeps carry, for the same reason."""
    assert "sauna.ges" in _long_names(), _long_names()


# ── And keeps some headroom while it plays ──────────────────────────────────
#
# **Playing is not mixing**, which is the second thing `sauna.ges` had to
# teach: it played the whole way, said nothing, and sat with a fifth of
# every chapter pinned exactly against its own `brickwall` — the limiter
# doing the arranging, ten deliberately different chapters coming out at
# one loudness, distortion on every kick.  Nothing above could see it,
# because everything above asks whether notes arrive.
#
# A minute is enough to catch it: a mix with no headroom has none in its
# first minute either, and a minute costs seconds where the whole piece
# costs minutes.

#: What fraction of samples may sit against the ceiling before the
#: ceiling is doing the mixing.  Set where it separates the two states
#: it has to tell apart: `sauna.ges` measured 3.5% while broken and
#: under 0.2% once its master trim existed, and a piece that never
#: limits at all measures 0.
CEILING_SHARE = 0.01

#: The first minute, and the rate is the reference's own — cheap enough
#: to run every time, long enough to hold a chapter's worth of groove.
HEADROOM_SECONDS = 60
HEADROOM_RATE = 8000


@pytest.mark.parametrize("name", _long_names())
def test_every_long_piece_keeps_headroom(name):
    """Rendered, not walked — this is the one question in this file
    that is about the *sound*, so it has to make some."""
    import tempfile

    from gestate.audiollvm import native_blocks
    from gestate.audioperform import (Performance, dynamic, from_performer,
                                      graph_of)

    source = (LONG_DIR / name).read_text()
    ceiling = re.search(r"brickwall\s+([\d.]+)", source)
    if ceiling is None:
        pytest.skip(f"{name} declares no ceiling to sit against")
    limit = float(ceiling.group(1))

    graph = graph_of(source, "", rate=HEADROOM_RATE)
    performer, _allocators = dynamic(source, "", rate=HEADROOM_RATE,
                                     block=LONG_BLOCK, seed=0,
                                     patience=None)
    show = Performance(graph)
    show.sources.append(from_performer(performer))

    at_ceiling, total = 0, 0
    with tempfile.TemporaryDirectory() as where:
        for block in native_blocks(graph, where,
                                   HEADROOM_RATE * HEADROOM_SECONDS,
                                   block=LONG_BLOCK,
                                   control=show.control()):
            for x in block:
                if (-x if x < 0.0 else x) > limit - 1e-9:
                    at_ceiling += 1
            total += len(block)

    assert total, f"{name} rendered nothing"
    share = at_ceiling / total
    assert share < CEILING_SHARE, (
        f"{name} spends {100 * share:.1f}% of its first minute against "
        f"its own ceiling of {limit}: the limiter is doing the mixing, "
        f"not catching transients")
