"""Live update — `spec/liveaudio.md` stage 5.

Editing a synth while it sounds, without stopping it.  The decision this
rests on was made back in stage 2: **migrate**, keyed on a node's `origin`
— the path of definitions it was inlined through — because that is the
identity an edit to a step function does not move.

The sharpest test here is the first one.  Swapping to an *identical* graph
must be **bit-identical** to never having swapped: if migration is right,
a no-op edit is a no-op in the sound, and if it is wrong that comparison
fails immediately rather than as a click somebody notices later.
"""

from __future__ import annotations

import shutil
import struct
import tempfile
import time
from pathlib import Path

import pytest

from gestate.audioengine import State, migrate, render_block, run, shape
from gestate.audioextract import extract
from gestate.audiolive import Live, SourceWatcher, play, watch

AUDIO_DIR = Path(__file__).resolve().parent.parent / "examples" / "audio"

needs_clang = pytest.mark.skipif(shutil.which("clang") is None,
                                 reason="no clang to build the engine with")


def _source(name: str = "blip.ges") -> str:
    return (AUDIO_DIR / name).read_text()


def _f32(samples) -> list:
    return [struct.unpack("<f", struct.pack("<f", max(-1.0, min(1.0, s))))[0]
            for s in samples]


# ── Migration, in the Python engine ─────────────────────────────────────────


def test_swapping_to_the_same_program_changes_nothing():
    """The property that makes migration checkable at all.

    Render, swap to a graph extracted from the same text, keep rendering:
    the result has to be what a single uninterrupted render produces, to
    the bit.  Any state a migration dropped or misplaced shows up here.
    """
    src = _source()
    graph = extract(src, rate=1000)
    state = State.initial(graph)
    first = render_block(graph, state, 20)

    again = extract(src, rate=1000)
    second = render_block(again, migrate(graph, state, again), 20)
    assert first + second == run(graph, 40)


def test_editing_a_step_function_keeps_every_node_running():
    """The case live coding exists for: change the sound, keep the phase."""
    src = _source()
    graph = extract(src, rate=1000)
    state = State.initial(graph)
    render_block(graph, state, 20)

    edited = extract(src.replace("decay v = v * v * v", "decay v = v * v"),
                     rate=1000)
    carried = migrate(graph, state, edited)
    assert carried.values == state.values, "nothing moved, so nothing resets"
    assert carried.t == state.t, "and time does not restart"


def test_editing_a_constant_keeps_the_oscillator_running():
    """Turning a knob is an edit to a literal inside a step function."""
    src = _source()
    graph = extract(src, rate=1000)
    state = State.initial(graph)
    render_block(graph, state, 20)

    edited = extract(src.replace("lowpass 0.25 raw", "lowpass 0.9 raw"),
                     rate=1000)
    carried = migrate(graph, state, edited)
    assert carried.values == state.values


def test_inserting_a_node_leaves_the_oscillator_alone():
    """A new stage in the chain must not restart what feeds it."""
    src = _source()
    graph = extract(src, rate=1000)
    state = State.initial(graph)
    render_block(graph, state, 20)

    edited = extract(src.replace("gain 0.6 (lowpass 0.25 raw)",
                                 "gain 0.6 (lowpass 0.25 (gain 0.9 raw))"),
                     rate=1000)
    carried = migrate(graph, state, edited)

    def at(g, values, origin):
        node = next(n for n in g.nodes if n.origin == origin)
        return values[node.id]

    assert at(edited, carried.values, "sound/raw/scan#0") == \
           at(graph, state.values, "sound/raw/scan#0"), "the phase survived"
    assert carried.t == state.t


def test_editing_a_lifted_literal_keeps_every_scan_running():
    """The migration half of the constant-folding guard.

    A literal standing where a `Sig Float` is wanted is lifted into a
    *node* — `Floating (Sig Float)`'s `fromFloat = constSig`, and
    `constSig v = mapSig (n => v) ticks`.  Editing that literal is
    therefore an edit to a `map`'s step today, and would be an edit to a
    folded constant inside its consumer's step after a folding pass.

    **Both spellings must keep the phases.**  What makes that safe is that
    a `map` and a `zip` carry no state at all: `render_block` computes each
    from `cur` alone, so their `State.values` slot is a write-only cache
    within the sample and `migrate` losing one costs nothing.  Only `scan`
    and `source` carry anything across an instant, and folding must never
    remove or re-kind one.

    So the assertion is on the `scan`s by origin, not on the value list as
    a whole: a fold *will* change the node set, and this has to survive
    that without being rewritten — otherwise it is a test of today's graph
    rather than of the property.
    """
    src = ("tone : Sig Float\ntone = sine 220.0\n\n"
           "sound : Sig Float\n"
           "sound = 0.25 * tone + 0.1 * lowpassSvf 900.0 0.4 (saw 110.0)\n")
    graph = extract(src, rate=1000)
    state = State.initial(graph)
    render_block(graph, state, 20)

    scans = [n.origin for n in graph.nodes if n.kind == "scan"]
    assert len(scans) == 3, "the fixture stopped having state to protect"

    edited = extract(src.replace("0.25 * tone", "0.5 * tone"), rate=1000)
    carried = migrate(graph, state, edited)

    def at(g, values, origin):
        return values[next(n for n in g.nodes if n.origin == origin).id]

    for origin in scans:
        assert at(edited, carried.values, origin) == at(graph, state.values,
                                                        origin), origin
    assert carried.t == state.t


def test_a_node_whose_state_changed_shape_starts_fresh():
    """Names are not layouts, and carrying bits across a layout is silent.

    `Voice Float Int` edited to `Voice Float Float` keeps the name `Voice`
    and changes what a value of it *is*.  Comparing names would reinterpret
    an integer as a double — inaudible as anything but a wrong noise, and
    invisible in every other test here.
    """
    src = _source()
    graph = extract(src, rate=1000)
    state = State.initial(graph)
    render_block(graph, state, 20)

    widened = src.replace("Voice := Voice Float Int", "Voice := Voice Float Float")
    widened = widened.replace("Voice p m -> Voice (wrap (p + noteAt n / sampleRate)) n",
                              "Voice p m -> Voice (wrap (p + noteAt n / sampleRate)) (toFloat n)")
    widened = widened.replace("Voice p n -> sawOf p * envAt n",
                              "Voice p n -> sawOf p * envAt (floor n)")
    edited = extract(widened, rate=1000)

    assert shape(graph, "Voice") != shape(edited, "Voice")
    carried = migrate(graph, state, edited)
    scan = next(n for n in edited.nodes if n.kind == "scan"
                and n.type_ == "Voice")
    assert carried.values[scan.id] == scan.init, "reset, not reinterpreted"


def test_a_brand_new_node_starts_at_its_init_not_at_zero():
    """`t` carries over, so the engine's "first instant" branch never fires.

    A new node therefore has to be *written* with its initial state; left
    empty it would start from whatever zero means for its type, which for
    a `scan` is not the same thing at all.
    """
    src = _source()
    graph = extract(src, rate=1000)
    state = State.initial(graph)
    render_block(graph, state, 20)

    edited = extract(src.replace("gain 0.6 (lowpass 0.25 raw)",
                                 "gain 0.6 (lowpass 0.25 (lowpass 0.5 raw))"),
                     rate=1000)
    carried = migrate(graph, state, edited)
    fresh = [n for n in edited.nodes
             if n.origin not in {m.origin for m in graph.nodes}]
    assert fresh, "the edit added a node"
    # The claim is about *state*: nodes with an `init` written.  A fresh
    # stateless node — `lowpass`'s zip stage, since its coefficient
    # became a signal — has `init = None` and its slot legitimately
    # holds its type's zero; a map is recomputed every block and never
    # reads it.
    stateful = [n for n in fresh if n.init is not None]
    assert stateful, "the edit added a stateful node"
    for node in stateful:
        assert carried.values[node.id] == node.init


# ── The running instrument ──────────────────────────────────────────────────


@needs_clang
def test_a_mid_stream_swap_is_the_migrated_engine_exactly():
    """The whole of stage 5, end to end and to the bit.

    Two blocks of the original reach the pipe, the edit is installed
    between blocks, and the rest is the new engine carrying the old state.
    The reference is computed independently through the Python engine.
    """
    src = _source()
    edited = src.replace("lowpass 0.25 raw", "lowpass 0.9 raw")
    directory = tempfile.mkdtemp()
    out = Path(directory) / "stream.raw"

    live = Live.start(src, 1000, directory, fade_ms=0)

    def progress(written):
        if written == 16 and live.generation == 0:
            live.compile(edited)

    play(None, seconds=40 / 1000, rate=1000, block=8,
         command=["sh", "-c", f"cat > {out}"], engine=live, progress=progress)
    assert live.generation == 1

    got = list(struct.unpack("<40f", out.read_bytes()))
    before = extract(src, rate=1000)
    state = State.initial(before)
    head = render_block(before, state, 16)
    after = extract(edited, rate=1000)
    tail = render_block(after, migrate(before, state, after), 24)
    assert got == _f32(head + tail)


@needs_clang
def test_a_swap_to_the_same_source_is_inaudible():
    """A save with no change must not click."""
    src = _source()
    directory = tempfile.mkdtemp()
    out = Path(directory) / "stream.raw"
    live = Live.start(src, 1000, directory, fade_ms=0)

    def progress(written):
        if written == 16 and live.generation == 0:
            live.compile(src)

    play(None, seconds=40 / 1000, rate=1000, block=8,
         command=["sh", "-c", f"cat > {out}"], engine=live, progress=progress)
    assert live.generation == 1
    got = list(struct.unpack("<40f", out.read_bytes()))
    assert got == _f32(run(extract(src, rate=1000), 40))


@needs_clang
def test_a_synth_that_does_not_compile_keeps_the_old_one_sounding():
    """A typo mid-phrase is the ordinary case, not an exceptional one."""
    src = _source()
    directory = tempfile.mkdtemp()
    out = Path(directory) / "stream.raw"
    live = Live.start(src, 1000, directory, fade_ms=0)

    def progress(written):
        if written == 16 and not live.errors:
            live.compile("sound : Sig Float\nsound = this is not a synth\n")

    play(None, seconds=40 / 1000, rate=1000, block=8,
         command=["sh", "-c", f"cat > {out}"], engine=live, progress=progress)

    assert live.generation == 0, "nothing was installed"
    assert live.errors, "and the reason was kept to be reported"
    got = list(struct.unpack("<40f", out.read_bytes()))
    assert got == _f32(run(extract(src, rate=1000), 40)), "the sound went on"


@needs_clang
def test_a_program_outside_the_fragment_is_refused_without_stopping():
    src = _source()
    directory = tempfile.mkdtemp()
    live = Live.start(src, 1000, directory, fade_ms=0)
    live.compile("sound : Sig Float\nsound = 0.0 ::: never\n")
    assert live.install() is False
    assert any("fragment" in e for e in live.errors)
    assert live.generation == 0


# ── Noticing the edit ───────────────────────────────────────────────────────


@needs_clang
def test_the_watcher_notices_a_save_and_rebuilds(tmp_path):
    """The half of `--watch` that is not `sleep`."""
    path = tmp_path / "synth.ges"
    path.write_text(_source())
    live = Live.start(path.read_text(), 1000, str(tmp_path))
    watcher = SourceWatcher(path, live)

    assert watcher.check() is False, "nothing has changed yet"

    path.write_text(_source().replace("lowpass 0.25 raw", "lowpass 0.8 raw"))
    assert watcher.check() is True
    assert live.pending is not None
    assert live.install() is True
    assert live.generation == 1

    assert watcher.check() is False, "and it does not fire twice"


def test_the_watcher_survives_a_file_being_written(tmp_path):
    """An editor's save is not atomic; a half-written read must not throw."""
    path = tmp_path / "synth.ges"
    path.write_text(_source())

    class Recording(Live):
        def __init__(self):
            self.compiled = []
            self.pending = None

        def compile(self, source):
            self.compiled.append(source)

    live = Recording()
    watcher = SourceWatcher(path, live)
    path.unlink()                        # the window an atomic replace opens
    assert watcher.check() is False
    assert live.compiled == []


@needs_clang
def test_watch_plays_and_reloads(tmp_path):
    """The whole loop, with a player that paces so the watcher can run.

    Sized against two real constraints rather than guessed at.  A pipe
    holds 64 KB, so a shorter render never blocks the writer and finishes
    before an edit could land — hence 192 KB.  And a rebuild takes ~400 ms,
    so the run has to outlast the edit *plus* that; the pacer stretches it
    to about two seconds of wall clock.
    """
    import sys
    import threading

    path = tmp_path / "synth.ges"
    path.write_text(_source())
    out = tmp_path / "stream.raw"
    pacer = [sys.executable, "-c",
             "import sys, time\n"
             "out = open(sys.argv[1], 'wb')\n"
             "while True:\n"
             "    chunk = sys.stdin.buffer.read(4096)\n"
             "    if not chunk: break\n"
             "    out.write(chunk); out.flush(); time.sleep(0.04)\n",
             str(out)]

    reports: list = []

    def edit_soon():
        time.sleep(0.3)
        path.write_text(_source().replace("lowpass 0.25 raw",
                                          "lowpass 0.95 raw"))

    threading.Thread(target=edit_soon, daemon=True).start()

    # **Stops on the thing it is asserting**, with a generous cap.  This
    # used to render for a fixed six seconds — about two of wall clock —
    # and check afterwards whether a rebuild had landed.  A build is
    # ~400 ms on an idle machine and much longer on a busy one, so under
    # load it failed three times out of three.  The stopwatch was the bug,
    # not the loop.
    def reloaded() -> bool:
        return any("reloaded" in r for r in reports)

    frames, _backend = watch(path, seconds=40.0, rate=8000, block=64,
                             command=pacer, report=reports.append,
                             interval=0.05, should_stop=reloaded)
    assert reloaded(), reports
    assert frames > 0, "it stopped before rendering anything"
    assert len(out.read_bytes()) == frames * 4
