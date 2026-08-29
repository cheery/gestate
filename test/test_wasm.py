"""The graph as wasm renders what the native build renders — `card:online.md`, piece A.

`gestate.audiowasm.build` compiles the **same** `.ll` text that
`audiollvm.build` compiles for the desk, so the claim is not "close":
it is bit-identical, every example, and the day it is not is the day
the browser plays something this desk never heard.  Skips, with the
tool named, where `clang`, `wasm-ld` or `wasmtime` is absent —
a green run on a bare machine is a smaller claim (`doc/install.md`).
"""

from __future__ import annotations

import math
import tempfile
from pathlib import Path

import pytest

from gestate import audiowasm

AUDIO_DIR = Path(__file__).resolve().parents[1] / "examples" / "audio"
RATE, BLOCK, FRAMES = 22050, 64, 2205          # a tenth of a second

needs_wasm = pytest.mark.skipif(audiowasm.missing() is not None,
                                reason=audiowasm.missing() or "")


def _names() -> list:
    return sorted(p.name for p in AUDIO_DIR.glob("*.ges"))


def _graph(name: str):
    from gestate.audioperform import graph_of

    return graph_of((AUDIO_DIR / name).read_text(), rate=RATE)


def _control(name: str, graph):
    """A fresh control function each call: a performer is a cursor, and
    the two renders must each start it from the top."""
    from gestate import audioperform
    from gestate.audioscore import unfolding_names

    src = (AUDIO_DIR / name).read_text()
    perf = audioperform.Performance(graph)
    total = FRAMES
    if audioperform.has_score(src):
        if unfolding_names(src):
            performer, _ = audioperform.dynamic(src, rate=RATE, block=BLOCK)
            perf.sources.append(audioperform.from_performer(performer))
        else:
            schedule, samples, _ = audioperform.scored(src, rate=RATE,
                                                       block=BLOCK)
            perf.sources.append(audioperform.from_schedule(schedule))
            total = min(total, samples)
    return perf.control(), total


def _same(a, b) -> bool:
    """Bit-identical, with NaN equal to NaN: a control the offline
    render drives past its range is `inf`/`nan` on both sides alike."""
    if isinstance(a, tuple):
        return all(_same(p, q) for p, q in zip(a, b))
    return a == b or (math.isnan(a) and math.isnan(b))


@needs_wasm
@pytest.mark.parametrize("name", _names())
def test_every_audio_example_links_imports_only_math_and_renders_bit_identical(name):
    """One test rather than two, because the build is the expensive
    half: link and imports are asserted first, and a machine without
    `wasmtime` skips *after* those have held, with the tool named."""
    from gestate.audiollvm import run_native

    graph = _graph(name)
    with tempfile.TemporaryDirectory() as d:
        wasm = audiowasm.build(graph, d)
        imports = audiowasm.imports_of(wasm)
        assert wasm.stat().st_size < 1 << 20, "a graph is kilobytes, not megabytes"
        for module, fn in imports:
            assert module == "env" and fn in audiowasm.HOST, \
                f"{name} imports {module}.{fn}, which no page supplies"
        pytest.importorskip("wasmtime",
                            reason="no wasmtime (`tools/toolbox.sh`)")
        control, total = _control(name, graph)
        got = audiowasm.run(wasm, graph, control, total, BLOCK)
        control, total = _control(name, graph)
        want = run_native(graph, d, total, block=BLOCK, control=control)
    assert len(got) == len(want) == total
    off = [i for i, (a, b) in enumerate(zip(want, got)) if not _same(a, b)]
    assert not off, f"{name}: first differing frame {off[0]} of {total}"


def test_the_examples_are_actually_being_found():
    assert "twinkle.ges" in _names()


def test_imports_of_reads_a_real_module():
    """The hand-written section parser against a module the linker
    made, and the one import twinkle is known to have."""
    if audiowasm.missing():
        pytest.skip(audiowasm.missing())
    graph = _graph("twinkle.ges")
    with tempfile.TemporaryDirectory() as d:
        assert audiowasm.imports_of(audiowasm.build(graph, d)) == [("env", "exp")]
