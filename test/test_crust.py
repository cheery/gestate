"""`crust/` against `gmachine.py` — the mirror held to the reference.

Program for program: compile once in Python, run in both machines,
compare the canonical spelling of the forced result.  The programs are
chosen for the corners where a port quietly diverges — laziness and
sharing, floor division on negatives, case dispatch — and end on the
one that pays for the whole crate: the SplitMix64 seed arithmetic,
which is the future Rust score cursor's randomness, computed here to
the bit before that cursor exists.
"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest

from gestate.crust import canonical, serialize
from gestate.gmachine import run
from gestate.pipeline import compile as compile_program

CRUST = Path(__file__).resolve().parent.parent / "crust"

needs_cargo = pytest.mark.skipif(shutil.which("cargo") is None,
                                 reason="no cargo to build crust with")


@pytest.fixture(scope="module")
def crust_bin():
    # `--target-dir` because the crate is a workspace member now and
    # cargo would otherwise build into the workspace root's `target/`;
    # pinning it keeps this path true.
    subprocess.run(["cargo", "build", "--quiet", "--release",
                    "--target-dir", str(CRUST / "target")],
                   cwd=CRUST, check=True)
    return CRUST / "target" / "release" / "crust"


def _both(source: str, tmp_path, crust_bin) -> tuple:
    state = compile_program(source)
    text = serialize(state, "main")
    path = tmp_path / "program.crust"
    path.write_text(text)
    got = subprocess.run([crust_bin, path], capture_output=True, text=True,
                         check=True).stdout.strip()

    run(state)
    want = canonical(state.stack[0], state)
    return got, want


@needs_cargo
def test_arithmetic_and_recursion_agree(tmp_path, crust_bin):
    got, want = _both("""
fib : Int -> Int
fib n = case n < 2 of
    True -> n
    False -> fib (n - 1) + fib (n - 2)

main : Int
main = fib 15
""", tmp_path, crust_bin)
    assert got == want == "610"


@needs_cargo
def test_division_floors_like_the_reference(tmp_path, crust_bin):
    """`div_euclid` is not Python's `//` on a negative divisor — the
    exact quiet corner a parity suite exists for."""
    got, want = _both("""
main : (Int, Int, Int, Int)
main = ((0 - 7) / 2, (0 - 7) % 2, 7 / (0 - 2), 7 % (0 - 2))
""", tmp_path, crust_bin)
    assert got == want
    assert got.startswith("#") and "-4" in got and "-1" in got


@needs_cargo
def test_laziness_and_sharing_agree(tmp_path, crust_bin):
    """An endless list, taken from — `Update`'s sharing is what makes
    the second `head` free, and a port that copied instead of updating
    would still pass; one that mis-indexed the redex would not."""
    got, want = _both("""
from : Int -> List Int
from n = n :: from (n + 1)

grab : Int -> List Int -> List Int
grab n xs = case n < 1 of
    True -> []
    False -> case xs of
        [] -> []
        x :: rest -> x :: grab (n - 1) rest

main : List Int
main = grab 5 (map (x => x * x) (from 3))
""", tmp_path, crust_bin)
    assert got == want
    assert "9" in got and "49" in got


@needs_cargo
def test_the_seed_arithmetic_agrees_to_the_bit(tmp_path, crust_bin):
    """The one that pays for the crate: `music.ges`'s SplitMix64, in
    both machines, on seeds that force the 128-bit intermediates."""
    from gestate.audio import library_text

    music = library_text("music.ges")
    # The seed block's own words, sliced from the library so there is
    # one source of truth — up to `unit`, whose floats sit outside the
    # integer core this cut of crust carries.
    start = music.index("wrap64 : Int -> Int")
    stop = music.index("#: One uniform draw")
    seeds = music[start:stop]
    got, want = _both(seeds + """
main : (Int, Int, Int)
main = (mix64 (wrap64 42), mix64 (wrap64 9223372036854775825),
        prim_mod_int (mix64 (wrap64 123456789)) 97)
""", tmp_path, crust_bin)
    assert got == want

    M = (1 << 64) - 1

    def mix64(z):
        z &= M
        z ^= z >> 30
        z = (z * 0xBF58476D1CE4E5B9) & M
        z ^= z >> 27
        z = (z * 0x94D049BB133111EB) & M
        z ^= z >> 31
        return z

    assert str(mix64(42)) in got


@needs_cargo
def test_float_arithmetic_agrees_to_the_bit(tmp_path, crust_bin):
    """The float layer: promotions, CPython's own `%` and `//`, the
    coercions both ways.  Canonical floats print as IEEE bits, so
    equality here *is* bit equality — the parity floats are held to.
    """
    got, want = _both("""
main : (Float, Float, Float, Float, Int, Int, Float)
main = (1.5 + 0.25, 10.0 / 4.0, 7.5 % 2.0, (0.0 - 7.5) % 2.0,
        floor 2.9, floor (0.0 - 2.9), toFloat 3)
""", tmp_path, crust_bin)
    assert got == want
    import struct

    def bits(v):
        return f"f{struct.unpack('<Q', struct.pack('<d', v))[0]:016x}"

    assert bits(1.75) in got
    assert bits(-7.5 % 2.0) in got
    assert "-3" in got, "floor is floor, not truncation"


@needs_cargo
def test_the_transcendentals_agree_to_the_bit(tmp_path, crust_bin):
    """`sin`..`sqrt` through both machines — the same libm on the same
    box, which is the assumption `audiollvm` already stands on and
    `test_transcendental.py` measures."""
    got, want = _both("""
main : (Float, Float, Float, Float, Float)
main = (sqrt 2.0, sin 1.0, cos 0.5, exp 1.0, log 2.0)
""", tmp_path, crust_bin)
    assert got == want


@needs_cargo
def test_the_uniform_draw_crosses_the_seam(tmp_path, crust_bin):
    """`unit` — the top 53 bits of a mix as a draw in 0..1 — was the
    line the integer-only cut stopped short of.  With floats in, the
    whole seed block crosses: a crust score cursor's randomness is now
    the reference's to the bit, including the float at the end."""
    from gestate.audio import library_text

    music = library_text("music.ges")
    start = music.index("wrap64 : Int -> Int")
    stop = music.index("# ── The live walk")
    seeds = music[start:stop]
    got, want = _both(seeds + """
main : (Float, Float, Float)
main = (unit 42, unit 9223372036854775825, unit (mix64 123456789))
""", tmp_path, crust_bin)
    assert got == want

    M = (1 << 64) - 1

    def mix64(z):
        z &= M
        z ^= z >> 30
        z = (z * 0xBF58476D1CE4E5B9) & M
        z ^= z >> 27
        z = (z * 0x94D049BB133111EB) & M
        z ^= z >> 31
        return z

    import struct
    expect = mix64(42) // 2048 / 9007199254740992.0
    assert f"f{struct.unpack('<Q', struct.pack('<d', expect))[0]:016x}" \
        in got


# ── In-process: the cdylib over ctypes ──────────────────────────────────────


@needs_cargo
def test_the_library_answers_what_the_reference_answers(crust_bin):
    """`Native` — the cdylib loaded over ctypes — is the same machine
    as the binary, held in-process.  (`crust_bin` built it: one cargo
    invocation makes both.)"""
    from gestate.crust import Native

    state = compile_program("""
fib : Int -> Int
fib n = case n < 2 of
    True -> n
    False -> fib (n - 1) + fib (n - 2)

main : Int
main = fib 15
""")
    run(state)
    want = canonical(state.stack[0], state)
    with Native(serialize(state, "main")) as m:
        assert m.force("main") == want == "610"


@needs_cargo
def test_the_heap_persists_across_forces(crust_bin):
    """Two forces on one machine share what the first one computed —
    the point of holding the machine rather than spawning it."""
    from gestate.crust import Native

    state = compile_program("""
slow : Int
slow = 3 * 7

main : Int
main = slow + 1
""")
    with Native(serialize(state, "main")) as m:
        assert m.force("slow") == "21"
        assert m.force("main") == "22"
        assert m.force("main") == "22", "a second force answers again"


@needs_cargo
def test_a_refusal_raises_and_the_process_lives(crust_bin):
    """The machine's `fail` is a caught panic at the seam: a wrong
    entry is a `CrustError` with crust's own message, and the same
    machine still answers afterwards."""
    import pytest as _pytest

    from gestate.crust import CrustError, Native

    state = compile_program("main : Int\nmain = 42\n")
    with Native(serialize(state, "main")) as m:
        with _pytest.raises(CrustError, match="no entry global"):
            m.force("nothere")
        assert m.force("main") == "42"


# ── The forcing protocol — `ScoreStream`'s twin ─────────────────────────────


def _reference_stream(synth, piece, rate, seed=0, **kw):
    from gestate.audiodynamic import ScoreStream
    from gestate.audioscore import stream_root

    tempo, state, root, by_tag = stream_root(synth, piece, rate, seed)
    return ScoreStream(state, root, by_tag, **kw)


@needs_cargo
def test_the_stream_twin_agrees_pull_for_pull(crust_bin):
    """The stage-two parity clause crosses the seam: a lazy score
    forced by crust equals the same score forced by `gmachine.py`,
    event for event, seed for seed."""
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from test_dynamicscore import PIECE, RATE, SYNTH

    from gestate.crust import native_stream

    want = _reference_stream(SYNTH, PIECE, RATE, seed=3).pull(10_000)
    _tempo, native, stream, _by_tag = native_stream(SYNTH, PIECE, RATE,
                                                    seed=3)
    got = stream.pull(10_000)
    assert got == want and want, "the twin is not the reference"
    assert stream.done and not stream.stalled


@needs_cargo
def test_an_endless_stream_pulls_bounded(crust_bin):
    """A `cycle` of sown bars, pulled to a horizon: the events below
    it, the same draws as the reference, and no walk to an end that
    does not exist."""
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from test_dynamicscore import RATE, SYNTH

    from gestate.crust import native_stream

    piece = """
score : [: Void :]
score = cycle ((do s <- draw; '(Custom (random s) 60)) |* 2) >>= voices.lead

bpm : Int
bpm = 120
"""
    reference = _reference_stream(SYNTH, piece, RATE, seed=9)
    _tempo, native, stream, _by_tag = native_stream(SYNTH, piece, RATE,
                                                    seed=9)
    for horizon in (4 * 96, 8 * 96, 16 * 96):
        want = reference.pull(horizon)
        got = stream.pull(horizon)
        assert got == want, f"diverged below horizon {horizon}"
        assert stream.frontier == reference.frontier
    assert not stream.done


@needs_cargo
def test_a_blown_budget_stalls_and_resumes(crust_bin):
    """Fuel out mid-thought is a stall, not a loss: the parked forcing
    resumes on the next pull, and the sum of the instalments is the
    unbudgeted answer."""
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from test_dynamicscore import PIECE, RATE, SYNTH

    from gestate.crust import native_stream

    want = _reference_stream(SYNTH, PIECE, RATE, seed=5).pull(10_000)
    _tempo, native, stream, _by_tag = native_stream(SYNTH, PIECE, RATE,
                                                    seed=5, fuel=300)
    got: list = []
    stalls = 0
    for _ in range(10_000):
        got += stream.pull(10_000)
        if stream.done:
            break
        if stream.stalled:
            stalls += 1
    assert got == want
    assert stalls > 0, "the budget never blew — the test is empty"


@needs_cargo
def test_the_collector_keeps_an_endless_night_bounded(crust_bin):
    """Eight hundred bars of an endless seeded cycle, bar by bar: the
    heap is copied between pulls, the indices survive every copy —
    the events stay the reference's — and the night does not grow a
    heap the size of itself."""
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from test_dynamicscore import RATE, SYNTH

    from gestate.crust import native_stream

    piece = """
score : [: Void :]
score = cycle ((do s <- draw; '(Custom (random s) 60)) |* 2) >>= voices.lead

bpm : Int
bpm = 120
"""
    reference = _reference_stream(SYNTH, piece, RATE, seed=4)
    _tempo, native, stream, _by_tag = native_stream(SYNTH, piece, RATE,
                                                    seed=4)
    got: list = []
    peak = 0
    bars = 800
    for k in range(1, bars + 1):
        got += stream.pull(k * 2 * 96)
        peak = max(peak, stream.heap_words)
    want = reference.pull(bars * 2 * 96)
    assert got == want and len(got) == bars
    assert peak < 2_000_000, f"the heap peaked at {peak} nodes"


@needs_cargo
def test_a_lazy_performer_drives_the_twin_unchanged(crust_bin):
    """`LazyPerformer` over a `NativeStream`: the host machinery does
    not know which machine is forcing — `getattr(stream, "ask")` was
    already the only probe-shaped assumption, and a probe-free piece
    never reaches it.  Change for change against the same performer
    over the reference stream."""
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from test_dynamicscore import BLOCK, RATE, SYNTH

    from gestate.audioalloc import Allocator
    from gestate.audiodynamic import LazyPerformer, ScoreStream
    from gestate.audioscore import stream_root
    from gestate.audiovoices import banks_of, channels_of
    from gestate.crust import native_stream

    piece = """
score : [: Void :]
score = cycle ((do s <- draw; '(Custom (random s) 60)) |* 2) >>= voices.lead

bpm : Int
bpm = 120
"""

    def allocators():
        source = SYNTH + piece
        return {b.name: Allocator(channels_of(source, b))
                for b in banks_of(source)}

    tempo, state, root, by_tag = stream_root(SYNTH, piece, RATE, 6)
    reference = LazyPerformer(ScoreStream(state, root, by_tag), tempo,
                              RATE, allocators(), block=BLOCK)
    _tempo, native, stream, _tags = native_stream(SYNTH, piece, RATE,
                                                  seed=6)
    twin = LazyPerformer(stream, _tempo, RATE, allocators(), block=BLOCK)

    want: list = []
    got: list = []
    for t in range(0, 16_000, BLOCK):
        want += reference.advance(t)
        got += twin.advance(t)
    assert got == want and want, "the performer heard two different pieces"


@needs_cargo
def test_the_live_twin_listens_and_answers(crust_bin):
    """The listening half crosses: the arpeggiator scenario driven
    twice, once over `LiveStream`, once over the crust twin, with the
    same scripted hands — a question parked is not a stall, the answer
    splices the continuation, and the two performances are change for
    change the same, readings included."""
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from test_dynamicscore import BLOCK, RATE, SYNTH, _allocators
    from test_probescore import ARP
    from test_sownscore import BEAT

    from gestate.audiodynamic import LazyPerformer, LiveStream
    from gestate.audioscore import stream_root
    from gestate.crust import native_stream

    def drive(performer, held):
        changes = []
        for t in range(0, 8 * BEAT, BLOCK):
            if t >= 2 * BEAT:
                held[:] = [60, 64, 67]
            if t >= 6 * BEAT:
                held[:] = [62, 65]
            changes += performer.advance(t)
        readings = [e for e in performer.transcript
                    if e[0] == "reading"]
        return changes, readings, list(performer.history)

    held_a: list = []
    tempo, state, root, by_tag = stream_root(SYNTH, ARP, RATE, 4, 0,
                                             True)
    reference = LazyPerformer(
        LiveStream(state, root, by_tag), tempo, RATE, _allocators(),
        block=BLOCK, reader=lambda port: list(held_a))

    held_b: list = []
    tempo2, native, stream, _tags = native_stream(SYNTH, ARP, RATE,
                                                  seed=4, live=True)
    twin = LazyPerformer(stream, tempo2, RATE, _allocators(),
                         block=BLOCK, reader=lambda port: list(held_b))

    want = drive(reference, held_a)
    got = drive(twin, held_b)
    assert got == want
    assert want[1], "nothing was asked — the test is empty"
    assert any(bank == "lead" for _on, _off, bank, _p in want[2]), \
        "nothing arpeggiated — the test is empty"
