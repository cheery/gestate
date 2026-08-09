"""One program that sounds and draws — `spec/substrate.md` S1.

The canvas behind the editor is written in gestate, so a file may hold a
`sound` and a `scene` at once.  Both `audio.ges` and `gui.ges` declare
constructors and a constructor's tag is its position, so such a file has to
be compiled with **one** prelude stack: two stacks is two numberings, and
two numberings is a `Rect` in one half and a `Dot` in the other.

The invariant this file exists for is the first line of the spec's S1, and
it is the one that catches everything else:

    **Adding a `scene` to a synth must not change one sample of its sound.**

Same graph, same node count, bit-identical render.  If the assembly
renumbers something it should not, or the scene's nodes leak into the audio
graph, that comparison says so before anything is drawn.
"""

from __future__ import annotations

import shutil

import pytest

from gestate.audio import has_substrate, has_sound, preludes
from gestate.audioengine import run
from gestate.audioextract import extract
from gestate.gui import scenes

needs_clang = pytest.mark.skipif(shutil.which("clang") is None,
                                 reason="no clang to build the engine with")

RATE = 8000

#: A synth, and nothing about drawing.
SOUND = """wiggle : Sig Float
wiggle = sine 3.0

sound : Sig Float
sound = sine 440.0 * (0.5 + wiggle * 0.25)
"""

#: The canvas half — a dot that follows the pointer.
SCENE = """
Ball := Ball Int Int

stepBall : Ball -> Event -> Ball
stepBall b e = case e of
    Move x y -> Ball x y
    _ -> b

drawBall : Ball -> Sub
drawBall b = case b of
    Ball x y -> Shift x y (Circle 20 (RGB 200 120 60))

substrate : Sig Sub
substrate = map drawBall (scan stepBall (Ball 100 100) events)
"""

BOTH = SOUND + SCENE


# ── Which vocabulary a program is compiled against ──────────────────────────


def test_a_program_says_which_halves_it_has():
    assert has_sound(SOUND) and not has_substrate(SOUND)
    assert has_substrate(SCENE) and not has_sound(SCENE)
    assert has_sound(BOTH) and has_substrate(BOTH)


def test_a_synth_that_draws_nothing_pays_nothing():
    """The rule `music.ges` already follows.

    Three constructors and their compile time are not something a program
    with no canvas should carry, so the combined stack is *conditional* —
    and a synth's assembly is the one it has always had.
    """
    # By what it *declares*, not by the file's name: `audio.ges` mentions
    # `gui.ges` in its own first paragraph, and prose is not a prelude.
    assert "Sub :=" not in preludes(SOUND)
    assert "Event :=" not in preludes(SOUND)
    assert "Sub :=" in preludes(BOTH)


def test_a_program_that_only_draws_gets_no_audio_vocabulary():
    """A *declaration*, not a mention — the same care the assertions above
    take, and for the same reason.  `signal.ges` is shared with the audio
    backend and its prose may name `sampleRate` while declaring nothing;
    matching the bare word made a doc comment a test failure."""
    assert "Sub :=" in preludes(SCENE)
    assert "sampleRate :" not in preludes(SCENE)
    assert "\nsine :" not in preludes(SCENE)


# ── The invariant ───────────────────────────────────────────────────────────


def test_adding_a_scene_changes_no_samples():
    """**The one that catches everything.**

    Bit-identical, through the oracle: the scene is compiled into the same
    program and reaches none of it.
    """
    quiet = extract(SOUND, rate=RATE)
    drawing = extract(BOTH, rate=RATE)

    assert len(drawing.nodes) == len(quiet.nodes), "the scene added nodes"
    samples = run(quiet, 400)
    assert run(drawing, 400) == samples
    assert any(x != 0.0 for x in samples), "silent: nothing was compared"


def test_adding_a_scene_changes_no_origins():
    """Node *origins* are what stage 5 migrates state by.

    A graph whose samples matched but whose origins had moved would reset
    every oscillator the first time a canvas was added to a file.
    """
    quiet = extract(SOUND, rate=RATE)
    drawing = extract(BOTH, rate=RATE)
    assert [n.origin for n in drawing.nodes] == [n.origin for n in quiet.nodes]


@needs_clang
def test_the_engine_agrees_with_the_oracle_for_a_program_that_draws():
    """The compiled half is compiled the same way, canvas or no canvas."""
    import tempfile

    from gestate.audiollvm import run_native

    graph = extract(BOTH, rate=RATE)
    with tempfile.TemporaryDirectory() as directory:
        assert run_native(graph, directory, 256, block=64) == \
            run(graph, 256, block=64)


# ── …and the drawing half still draws ───────────────────────────────────────


def test_the_scene_of_a_program_that_also_sounds(tmp_path):
    """Both halves of one file, from one compilation.

    The scene is *interpreted* — this is the G-machine folding events, at
    frame rate — while the sound above is compiled.  They meet nowhere yet;
    S3 is where the canvas gets to play the synth.
    """
    frames = scenes(BOTH, [("Move", 40, 60), ("Move", 90, 30)], rate=RATE)
    assert frames == [
        [("dot", 100, 100, 20, (200, 120, 60))],
        [("dot", 40, 60, 20, (200, 120, 60))],
        [("dot", 90, 30, 20, (200, 120, 60))],
    ]


def test_a_scene_alone_is_unaffected():
    """A GUI program is compiled with exactly what it always was."""
    frames = scenes(SCENE, [("Move", 12, 34)])
    assert frames[-1] == [("dot", 12, 34, 20, (200, 120, 60))]


def test_the_canvas_is_told_the_rate_its_synth_plays_at():
    """`sampleRate` is the renderer's business — and the canvas's too.

    The audio vocabulary is in front of a drawing program that also sounds,
    and it is written in terms of `sampleRate`, so every definition needs
    one to type-check.  Two different answers here and in `audio._entry`
    would be two programs again.
    """
    source = SOUND + SCENE.replace(
        "Ball x y -> Shift x y (Circle 20 (RGB 200 120 60))",
        "Ball x y -> Shift x (seconds 0.5) (Circle 20 (RGB 200 120 60))")
    frames = scenes(source, [("Move", 12, 34)], rate=1000)
    assert frames[-1] == [("dot", 12, 500, 20, (200, 120, 60))]


# ── S2: a substrate, composed and drawn ─────────────────────────────────────
#
# `substrate : Sig Sub`, built from smaller ones by ordinary functions.  Two
# spellings and one answer to what is drawn: a `scene : Sig Scene` is a
# substrate with nothing attached, and the host wraps one in `still`.

PICTURE = """
face : Sub
face = Circle 4 (RGB 200 30 30)

body : Sub
body = Rect 40 20 (RGB 30 30 200)

badge : Sub
badge = Shift 100 50 (Over body face)

substrate : Sig Sub
substrate = !badge
"""


def test_a_substrate_composes_and_is_drawn():
    """`over` layers, `moveXY` moves, and both are read off one walk."""
    # Both placed by their **centres** at (100, 50): the 40x20 body has its
    # top-left 20 left and 10 up of that, and the dot *is* its centre.
    assert scenes(PICTURE, [])[0] == [
        ("rect", 80, 40, 40, 20, (30, 30, 200)),
        ("dot", 100, 50, 4, (200, 30, 30)),
    ]


def test_over_puts_its_second_argument_on_top():
    """Painter's order, and it is in the program rather than the file.

    File order would be a second answer to what is in front of what, and an
    invisible one.  `over a b` is `a` and then `b`.
    """
    under = PICTURE + "\nflipped : Sub\nflipped = Over face body\n"
    drawn = scenes(under.replace("substrate = !badge",
                                 "substrate = !flipped"), [])[0]
    assert [s[0] for s in drawn] == ["dot", "rect"]


def test_a_transform_reaches_every_leaf_under_it():
    """`moveXY` moves a whole substrate, not the shape nearest to it.

    Compared against the same picture unshifted rather than against
    absolute numbers: what is being claimed is that *every* leaf moved by
    the same amount, and a bound like "all past 100" would also pass for a
    walk that moved only the outermost one.
    """
    here = scenes(PICTURE, [])[0]
    there = scenes(PICTURE.replace("Shift 100 50 ", ""), [])[0]
    assert [(a[1] - b[1], a[2] - b[2]) for a, b in zip(here, there)] == \
        [(100, 50), (100, 50)]


def test_a_substrate_may_follow_a_signal():
    """Three signals into one `moveXY`, which is what it now takes.

    `moveXY` *is* the lift — `!moveXYSub x y s` — so this is the same
    three-argument path it always was, with the marker inside the prelude
    instead of in the program.  Beyond two arguments the lift pairs them up
    through `signal.ges`'s `Both`, so this is also the program that
    exercises that path for something other than sound.
    """
    source = """
Where := Where Int Int

stepWhere : Where -> Event -> Where
stepWhere w e = case e of
    Move x y -> Where x y
    _ -> w

xOf : Where -> Int
xOf w = case w of
    Where x y -> x

yOf : Where -> Int
yOf w = case w of
    Where x y -> y

pointer : Sig Where
pointer = scan stepWhere (Where 0 0) events

dot : Sub
dot = Circle 6 (RGB 9 9 9)

substrate : Sig Sub
substrate = moveXY (!xOf pointer) (!yOf pointer) (!dot)
"""
    frames = scenes(source, [("Move", 30, 40), ("Move", 77, 12)])
    assert frames == [
        [("dot", 0, 0, 6, (9, 9, 9))],
        [("dot", 30, 40, 6, (9, 9, 9))],
        [("dot", 77, 12, 6, (9, 9, 9))],
    ]


def test_a_substrate_built_by_folding_the_events_draws():
    """What `world` used to spell, spelled out.

    `world step init draw` was `map draw (scan step init events)` and
    nothing else, so it is written here rather than named — a combinator
    whose body is shorter than its documentation was one name too many.
    """
    assert scenes(SCENE, [("Move", 12, 34)])[-1] == \
        [("dot", 12, 34, 20, (200, 120, 60))]


def test_a_leftover_scene_is_refused_by_name():
    """`scene : Sig Scene` is gone, and saying so is the whole of the fix.

    `Shape`, `Scene` and the `still` that lifted one were a second spelling
    of what `Sub` already did, which cost every reader the question of
    which of the two they were looking at.  A file still carrying one is
    told what to do about it — the alternative is `Unknown global 'scene'`
    from somewhere in a prelude the author did not write.
    """
    from gestate.gui import GuiError

    with pytest.raises(GuiError, match="no longer draws"):
        scenes("scene : Sig Scene\nscene = mkSig (wait input)\n", [])


def test_a_synth_with_a_substrate_still_sounds_the_same():
    """The S1 invariant, now with the thing S1 was for."""
    quiet = extract(SOUND, rate=RATE)
    drawing = extract(SOUND + PICTURE, rate=RATE)
    assert [n.origin for n in drawing.nodes] == [n.origin for n in quiet.nodes]
    assert run(drawing, 400) == run(quiet, 400)


def test_a_constant_signal_is_the_backends_own():
    """`!x` is `constSig x`, and what it is constant *over* is a clock.

    The audio renderer supplies one over `ticks` and the canvas one over
    `events`, the same way each supplies `sampleRate` — a signal has to
    advance on some clock, and which clock there is depends on who is
    running the program.
    """
    from gestate.audio import _entry

    assert "constSig v = mapSig (n => v) ticks" in _entry(RATE)
    # And the canvas half of the same file draws a constant fine.
    assert scenes(SOUND + PICTURE, [])[0][0][0] == "rect"


# ── S3: attachment, and the walk that finds it ──────────────────────────────
#
# The channel goes *in*.  A program declares one, hands it to an element,
# and reads it back with `:::` or `wait`; the host walks the tree to draw it
# and finds the channel at the node that named it.  Nothing is routed by
# name and nothing is registered — which is why `fixme.md` F90/F91's
# "channel identifiers are handed out in allocation order" stops applying
# rather than having to be worked around.

FADER = """
dragged : Chan Float
dragged = chan

level : Sig Float
level = 0.5 ::: mkSig (wait dragged)

#: The travel is the track's 120, centred, so -60…60 — which is what
#: `bimix` would be if the fraction were signed.  `Shift` is
#: layout-neutral, so sliding the handle does not resize the fader.
handle : Float -> Sub
handle v = Shift 0 (floor (mix (0.0 - 60.0) 60.0 v)) (Rect 12 8 (RGB 200 200 200))

#: Placed, because everything is centred on the origin otherwise and half
#: of it would be off the top-left of the canvas.
substrate : Sig Sub
substrate = moveXY 25 60 (onTouchY dragged
    (rect 12 120 (colour 40 40 40) `over` !handle level))
"""


def _handle(frame) -> tuple:
    """The light rectangle — the part that moves."""
    return next(s for s in frame if s[-1] == (200, 200, 200))


def test_a_press_reaches_the_channel_the_element_carries():
    from gestate.gui import touches

    # The fader's extent is the track's 12x120 centred at (25, 60), so it
    # spans y 0…120 and a press at 30 is a quarter of the way down.
    frames = touches(FADER, [("press", 25, 30)])
    assert _handle(frames[0])[2] == 56, "the initial half-way value"
    assert _handle(frames[-1])[2] == 26, "the press moved it to a quarter"


def test_a_drag_follows():
    from gestate.gui import touches

    frames = touches(FADER, [("press", 25, 30), ("drag", 25, 90)])
    assert _handle(frames[-1])[2] == 86, "three quarters down"


def test_a_press_grabs_so_a_drag_may_leave_the_element():
    """What a fader *is*.

    Hit-testing every drag afresh gives one that stops following your hand
    at its own edge, which is not a fader.
    """
    from gestate.gui import touches

    frames = touches(FADER, [("press", 25, 30), ("drag", 400, 95)])
    assert _handle(frames[-1])[2] == 91, "still following, 400 px away"


def test_a_touch_reads_in_the_elements_own_extent():
    """**The claim `Sub`-as-data is for.**

    `moveXY` moves the picture *and* what the element hears: the position
    is accumulated on the way down, so an element shifted down by 50 reads
    a press at 90 as a third of the way through *itself*, not as anything
    about where the canvas's top is.
    """
    from gestate.gui import touches

    shifted = FADER.replace("moveXY 25 60 (", "moveXY 25 110 (")
    frames = touches(shifted, [("press", 25, 90)])
    # Its extent now spans y 50…170, so 90 is a third down: the handle
    # sits a third along a travel of -60…60, at 110 - 20.
    assert _handle(frames[-1])[2] == 86


def test_a_release_leaves_the_value_where_it_was_let_go():
    """A fader stays where you left it, which is what a fader does.

    **There is no per-element press gate any more.**  `onPress` gave 1
    while held and 0 on release, and it went with `onDrag` and `Axis` when
    attachment became `onTouchX`/`onTouchY`.  Nothing has replaced it: a
    momentary button is not expressible today, and that is a known gap
    rather than an oversight — `button : Int -> Sig Bool` in the input
    half is about *mouse* buttons, not about an element being held.
    """
    from gestate.gui import touches

    frames = touches(FADER, [("press", 25, 30), ("release", 25, 30)])
    assert _handle(frames[-1])[2] == 26, "the release did not reset it"


def test_the_deepest_attachment_gets_the_press():
    """Innermost wins, which is the order the walk already produces."""
    from gestate.gui import touches

    source = """
outer : Chan Float
outer = chan

inner : Chan Float
inner = chan

a : Sig Float
a = 0.0 ::: mkSig (wait outer)

b : Sig Float
b = 0.0 ::: mkSig (wait inner)

draw : Float -> Float -> Sub
draw x y = Over (Rect 100 100 (RGB (floor (x * 100.0)) 0 0))
                (Rect 20 20 (RGB 0 (floor (y * 100.0)) 0))

substrate : Sig Sub
substrate = moveXY 50 50 (onTouchY outer (onTouchY inner (!draw a b)))
"""
    # The inner attachment wraps the 20x20 square, so its extent is 20 and
    # a press at its very middle is 0.5; the outer one spans the 100 and
    # never hears it, because the innermost containing attachment wins.
    frames = touches(source, [("press", 50, 50)])
    assert frames[-1][0][-1] == (0, 0, 0), "the outer one fired and should not"
    assert frames[-1][1][-1] == (0, 50, 0), "the inner one did not fire"


def test_a_press_on_nothing_writes_nothing():
    from gestate.gui import touches

    frames = touches(FADER, [("press", 300, 300)])
    assert _handle(frames[-1])[2] == 56, "untouched, still half way"


def test_one_declaration_two_readers():
    """The whole feature: the canvas draws what the synth hears.

    The audio graph has a control source named `cutoff`; the canvas has an
    attachment carrying that same channel.  Neither knows about the other,
    and the program said it once.
    """
    from gestate.gui import touches

    source = """
cutoff : Chan Float
cutoff = chan

level : Sig Float
level = 0.5 ::: mkSig (wait cutoff)

hzOf : Float -> Float
hzOf v = mix 200.0 1400.0 v

sound : Sig Float
sound = zip (x v => x * 0.4) (sine 220.0) (map hzOf level)

handle : Float -> Sub
handle v = Shift 0 (floor (mix (0.0 - 60.0) 60.0 v)) (Rect 12 8 (RGB 200 200 200))

substrate : Sig Sub
substrate = moveXY 25 60 (onTouchY cutoff
    (rect 12 120 (colour 40 40 40) `over` !handle level))
"""
    graph = extract(source, rate=RATE)
    assert [(n.chan, n.type_, n.init) for n in graph.control_sources()] == \
        [("cutoff", "Float", 0.5)]

    frames = touches(source, [("press", 25, 30)])
    assert _handle(frames[-1])[2] == 26


# ── The editor's half: one gesture, both halves ─────────────────────────────


PLAYS = """
cutoff : Chan Float
cutoff = chan

level : Sig Float
level = 0.5 ::: mkSig (wait cutoff)

hzOf : Float -> Float
hzOf v = mix 200.0 1400.0 v

sound : Sig Float
sound = zip (x v => x * 0.4) (sine 220.0) (map hzOf level)

handle : Float -> Sub
handle v = Shift 0 (floor (mix (0.0 - 60.0) 60.0 v)) (Rect 12 8 (RGB 200 200 200))

substrate : Sig Sub
substrate = moveXY 25 60 (onTouchY cutoff
    (rect 12 120 (colour 40 40 40) `over` !handle level))
"""


def test_a_gesture_moves_the_picture_and_the_sound(tmp_path):
    """The bridge, in one assertion each way.

    The canvas is written by id so the picture follows; the value is left
    under the channel's *name* so `Workbench.control` finds it for the
    engine.  The program said `cutoff` once.
    """
    from gestate.audioeditor import Workbench

    path = tmp_path / "plays.ges"
    path.write_text(PLAYS)
    bench = Workbench(path, rate=RATE, block=64)
    bench._load_substrate(PLAYS)

    assert bench.substrate is not None
    assert bench.substrate.by_name == {"cutoff": 0}

    bench.touch("press", 25, 30)
    assert bench.substrate.values == {"cutoff": 0.25}, "the sound's side"
    handle = next(s for s in bench.picture() if s[-1] == (200, 200, 200))
    assert handle[2] == 26, "the picture's side"


def test_a_file_with_no_canvas_has_none(tmp_path):
    from gestate.audioeditor import Workbench

    path = tmp_path / "quiet.ges"
    path.write_text(SOUND)
    bench = Workbench(path, rate=RATE, block=64)
    bench._load_substrate(SOUND)
    assert bench.substrate is None and bench.picture() == []
    bench.touch("press", 1, 1)          # and touching it is not an error


def test_a_canvas_that_does_not_build_does_not_stop_the_sound(tmp_path):
    """Best-effort, exactly as knob placement is."""
    from gestate.audioeditor import Workbench

    path = tmp_path / "broken.ges"
    path.write_text(SOUND + "\nsubstrate : Sig Sub\nsubstrate = nonsense\n")
    bench = Workbench(path, rate=RATE, block=64)
    bench._load_substrate(path.read_text())
    assert bench.substrate is None
    assert any("canvas did not build" in m for m in bench.messages)


# ── S5: the sound back ──────────────────────────────────────────────────────
#
# The other direction: not a hand reaching the program but the *instrument*
# reaching it.  Well-known channel names, the way `sound`, `substrate`,
# `score` and `bpm` are well-known — a program asks for a reading by
# declaring a channel with that name, and asks for nothing by not.

WATCHING = """
peak : Chan Float
peak = chan

position : Chan Int
position = chan

loud : Sig Float
loud = 0.0 ::: mkSig (wait peak)

now : Sig Int
now = 0 ::: mkSig (wait position)

sound : Sig Float
sound = sine 220.0 * 0.3

meter : Float -> Int -> Sub
meter v t = Over (Sized 20 100 (Rect 20 (floor (v * 100.0)) (RGB 60 200 90)))
                 (Shift 40 (prim_mod_int t 200) (Rect 60 2 (RGB 200 200 60)))

substrate : Sig Sub
substrate = !meter loud now
"""


def test_a_reading_written_by_name_reaches_the_picture():
    from gestate.gui import Substrate

    sub = Substrate(WATCHING, rate=RATE)
    assert set(sub.by_name) == {"peak", "position"}
    sub.write("peak", 0.5)
    sub.write("position", 120)
    bar, head = sub.picture()
    assert bar[4] == 50, "the meter is as tall as the sound was loud"
    assert head[2] == 120 - 1, "and the playhead is where the transport is"


def test_a_canvas_that_asks_for_nothing_is_written_nothing():
    from gestate.gui import Substrate

    sub = Substrate(PICTURE, rate=RATE)
    assert sub.write("peak", 0.5) is False
    assert sub.values == {}


def test_the_workbench_writes_what_the_instrument_is_doing(tmp_path):
    """`observe()` — once a frame, from the view, never the audio thread."""
    from gestate.audioeditor import Transport, Workbench

    path = tmp_path / "watch.ges"
    path.write_text(WATCHING)
    bench = Workbench(path, rate=RATE, block=64)
    bench._load_substrate(WATCHING)
    bench.transport = Transport(live=None, rate=RATE, block=64)
    bench.transport.position = 77
    bench.transport._peak = 0.25

    bench.observe()
    assert bench.substrate.values == {"peak": 0.25, "position": 77}


def test_a_peak_is_taken_rather_than_read():
    """A meter shows what has happened since it last looked.

    One that decayed on its own would be showing its own decay rather than
    the instrument.
    """
    from gestate.audioeditor import Transport

    transport = Transport(live=None, rate=RATE, block=64)
    transport._peak = 0.4
    assert transport.take_peak() == 0.4
    assert transport.take_peak() == 0.0


def test_the_peak_is_only_tracked_when_a_canvas_asks(tmp_path):
    """The one place in the program with no time to spare.

    A reading nobody looks at is a cost nobody agreed to, so the audio
    thread does no scanning for a file that declares no `peak`.
    """
    from gestate.audioeditor import Transport, Workbench

    path = tmp_path / "w.ges"
    path.write_text(SOUND + PICTURE)
    bench = Workbench(path, rate=RATE, block=64)
    bench.transport = Transport(live=None, rate=RATE, block=64)
    bench._load_substrate(SOUND + PICTURE)
    assert bench.transport.watch_peak is False

    path.write_text(WATCHING)
    bench._load_substrate(WATCHING)
    assert bench.transport.watch_peak is True


def test_the_example_is_a_synth_you_can_see_and_touch():
    """`examples/audio/substrate.ges` — both halves of one file.

    A fader that is moved by `moveXY` and still hears in its own
    coordinates, a meter the host writes, and a filter reading the signal
    the fader feeds.
    """
    from pathlib import Path

    from gestate.gui import Substrate

    source = (Path(__file__).resolve().parent.parent / "examples" / "audio"
              / "substrate.ges").read_text()
    assert [(n.chan, n.type_) for n in extract(source, rate=RATE)
            .control_sources()] == [("cutoff", "Float")]

    sub = Substrate(source, rate=RATE)
    assert set(sub.by_name) == {"cutoff", "peak"}
    # The fader's track is 200 tall centred at y=140, so it spans 40…240
    # and a press at 190 is three quarters of the way down it.
    sub.touch("press", 100, 190)
    sub.write("peak", 0.5)
    assert sub.values["cutoff"] == pytest.approx(0.75)
    meter = next(s for s in sub.picture() if s[-1] == (60, 200, 90))
    assert meter[4] == 90, "and the meter shows what the host wrote"


# ── A file that does both at once — `fixme.md` F98 ──────────────────────────


#: A piece, an instrument and a fader in one file: the thing a substrate
#: was built to make ordinary, and the cheapest program that fails when any
#: reader of a file assembles its own text instead of asking
#: `audio.preludes`.  Six of F98's seven defects are on this one source.
PLAYS_AND_DRAWS = """
Key := Key Int Int

voices lead 2 sineVoice : Sig Float

env : Adsr
env = Adsr 0.01 0.2 0.6 0.2

hzOfKey : Key -> Float
hzOfKey (Key k v) = keyHz k

sineVoice : Sig Gate -> Sig Key -> Sig Float
sineVoice g s = sine (!hzOfKey s) * adsr env g

bpm : Int
bpm = 96

tune : [: Key :]
tune = '(Key 60 100) ++ '(Key 64 100) || '(Key 67 100)

score : [: Void :]
score = tune >>= voices.lead

cutoff : Chan Float
cutoff = chan

level : Sig Float
level = 0.5 ::: mkSig (wait cutoff)

#: The fader is *heard*, which is the point of the file and is also what
#: puts a control source in the graph for the placement to place.
sound : Sig Float
sound = gain 0.4 (lead * (0.2 + level * 0.8))

handle : Float -> Sub
handle v = Shift 0 (floor (mix (0.0 - 60.0) 60.0 v)) (Rect 12 8 (RGB 200 200 200))

substrate : Sig Sub
substrate = moveXY 40 40 (onTouchY cutoff
    (rect 12 120 (colour 40 40 40) `over` !handle level))
"""


def test_a_file_may_play_a_piece_and_draw_a_fader(tmp_path):
    """One program, and every reader of it has to agree about that.

    `audio.preludes` is the single answer to what vocabulary a file is
    written in, and the score, the canvas, the placement and the line
    numbers each used to assemble their own text — which agreed with it for
    every file anyone had written until one file did two things at once.
    """
    from gestate.audioeditor import Workbench
    from gestate.gui import Substrate

    path = tmp_path / "both.ges"
    path.write_text(PLAYS_AND_DRAWS)
    bench = Workbench(path, rate=RATE, block=64)

    # The canvas: `gui.ges` *and* `music.ges` in front of it, and the bank
    # expanded — each of those was a separate way for this to fail.
    sub = Substrate(PLAYS_AND_DRAWS, rate=RATE)
    assert "cutoff" in sub.by_name
    assert sub.picture(), "a program that draws draws something"

    # The piece, which is read through a *different* entry point and so a
    # different assembly.
    bench._find_banks(PLAYS_AND_DRAWS)
    bench._load_score(PLAYS_AND_DRAWS)
    assert bench.schedule is not None and bench.bpm == 96

    # And the knob, placed on the line that declares it — the offset a
    # position is reported in has to count `gui.ges` too.
    bench._place(PLAYS_AND_DRAWS)
    line = next(s.line for s in bench.sites if s.name == "level")
    assert PLAYS_AND_DRAWS.splitlines()[line - 1].startswith("level = 0.5")


def test_a_hole_leaves_the_rest_of_the_file_running(tmp_path):
    """A hole is an absent declaration, not a broken program.

    `substrate = _` is a file with no canvas *yet*, and the honest thing to
    do about it is what this host does for a file with no canvas at all:
    nothing, quietly, while the piece and the instrument go on.
    """
    from gestate.audioeditor import Workbench

    source = PLAYS_AND_DRAWS.replace(
        "substrate = moveXY 40 40 (onTouchY cutoff\n"
        "    (rect 12 120 (colour 40 40 40) `over` !handle level))",
        "substrate = _")
    path = tmp_path / "half.ges"
    path.write_text(source)
    bench = Workbench(path, rate=RATE, block=64)

    bench._load_substrate(source)
    assert bench.substrate is None
    assert any(m.startswith("no canvas:") for m in bench.messages)
    # The line is the author's own, not one of an assembly they never wrote.
    assert f"half.ges:{source.splitlines().index('substrate = _') + 1}" \
        in bench.messages[-1]

    bench._find_banks(source)
    bench._load_score(source)
    assert bench.schedule is not None, "the piece has nothing to do with it"
