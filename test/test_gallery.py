"""The picture, in a tab — `card:audiovisual-gallery.md`, day one.

Six pieces on the site declare a `substrate` and every one of them is
live there right now with its visual half dropped on the floor.  A
substrate is a **second program** (`spec/substrate.md`), interpreted at
frame rate, so a page that draws one needs a G-machine — and the tab had
none.

`shell/web` is the seam that gives it one: `crust` and the panel's walk
compiled for `wasm32`, offered to a page as a handful of C functions and
one flat `i32` buffer.  What this file measures is the thing a
measurement was owed for, and it is deliberately *end to end* — the
module built for the browser's own target, driven under `wasmtime`
through nothing but pointers into its linear memory, and its picture
compared with the one `gestate/gui.py` draws from the same program.

**Why against `gui.py` and not against a fixture.**  There is one
correct picture and `gui.py` is what makes it correct; a shell checked
against a recording of itself agrees with itself.  `shell/panel/tests/`
holds the frozen copies, `test_panel_fixtures.py` pins those to today's
exporter, and `shell/web/src/tests.rs` checks the wire natively.  This
is the last link: **the same walk, in the target a person's browser
runs**, so nothing between here and a page is untested but the page.

The wire's format is `shell/web/src/lib.rs` §"The wire".  It is read
here the way JavaScript will read it — one cursor, record lengths
implied by each kind — because a reader written from the writer's own
structs would not catch a layout the page cannot parse.
"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
#: Kept out of the workspace `target/` for the reason `test_crust.py`
#: gives, and separate from the native one so a wasm build does not
#: throw away the artifacts `cargo test` just made.
TARGET = ROOT / "shell" / "web" / "target"
TRIPLE = "wasm32-unknown-unknown"

needs_cargo = pytest.mark.skipif(shutil.which("cargo") is None,
                                 reason="no cargo to build the shell with")


def _has_target() -> bool:
    if shutil.which("rustup") is None:
        return False
    out = subprocess.run(["rustup", "target", "list", "--installed"],
                         capture_output=True, text=True)
    return TRIPLE in out.stdout


needs_wasm = pytest.mark.skipif(
    not _has_target(),
    reason=f"no {TRIPLE} target (`rustup target add {TRIPLE}`)")

wasmtime = pytest.importorskip("wasmtime", reason="no `wasmtime` in this "
                              "interpreter (`tools/toolbox.sh`)")


@pytest.fixture(scope="module")
def module_path() -> Path:
    subprocess.run(["cargo", "build", "--quiet", "--release",
                    "-p", "gestate-web", "--target", TRIPLE,
                    "--target-dir", str(TARGET)],
                   cwd=ROOT, check=True)
    return TARGET / TRIPLE / "release" / "gestate_web.wasm"


class Tab:
    """A page, near enough: one module, one memory, and pointers.

    Everything a browser would do in JavaScript is done here in Python
    against the same exports, so the shape of the seam is what is
    checked rather than the convenience of one language's bindings.
    """

    def __init__(self, path: Path):
        self.store = wasmtime.Store()
        module = wasmtime.Module.from_file(self.store.engine, str(path))
        # **No import object.**  The module imports nothing — `crust`'s
        # zero-dependency rule reaching the browser — so a page supplies
        # the machine nothing at all.
        self.inst = wasmtime.Instance(self.store, module, [])
        self.ex = self.inst.exports(self.store)
        self.mem = self.ex["memory"]
        self.owned: list[tuple[int, int]] = []

    def call(self, name: str, *args):
        return self.ex[name](self.store, *args)

    def put(self, data: bytes) -> tuple[int, int]:
        p = self.call("web_alloc", len(data))
        self.mem.write(self.store, data, p)
        self.owned.append((p, len(data)))
        return p, len(data)

    def put_i64(self, values) -> int:
        import struct
        return self.put(b"".join(struct.pack("<q", v) for v in values))[0]

    def put_f64(self, values) -> int:
        import struct
        return self.put(b"".join(struct.pack("<d", v) for v in values))[0]

    def i32_at(self, addr: int) -> int:
        import struct
        return struct.unpack_from("<i", self.mem.read(
            self.store, addr, addr + 4))[0]

    def f64_at(self, addr: int) -> float:
        import struct
        return struct.unpack_from("<d", self.mem.read(
            self.store, addr, addr + 8))[0]

    def text_at(self, addr: int) -> str:
        out = bytearray()
        while True:
            b = self.mem.read(self.store, addr, addr + 1)[0]
            if b == 0:
                break
            out.append(b)
            addr += 1
        return out.decode("utf-8", "replace")

    def open(self, sub: dict):
        text, text_len = self.put(sub["text"].encode())
        entry, entry_len = self.put(sub["entry"].encode())
        tags = self.put_i64(sub["tags"])
        chans = b"".join(n.encode() + b"\0" for n in sub["chans"])
        chan_p, chan_len = self.put(chans) if chans else (0, 0)
        self.w = self.call("web_open", text, text_len, entry, entry_len,
                           tags, chan_p, chan_len)
        assert self.w, f"web_open refused: {self.error()}"
        return self.w

    def error(self) -> str:
        return self.text_at(self.call("web_error", getattr(self, "w", 0)))

    def tick(self, writes=(), pulse=-1, cx=0, cy=0):
        if writes:
            flat = []
            for chan, value in writes:
                flat += [float(chan), float(value)]
            p, n = self.put_f64(flat), len(writes)
        else:
            p, n = 0, 0
        self.call("web_tick", self.w, p, n, pulse, cx, cy)

    def channel(self, name: str) -> int:
        p, n = self.put(name.encode())
        return self.call("web_channel", self.w, p, n)

    def display(self) -> list[str]:
        """The wire, back in the grammar `shell/panel/tests/*.display`
        and `_display_lines` both speak — so the comparison is between
        two pictures rather than between two encodings."""
        base = self.call("web_display", self.w)
        assert base, "no wire"
        items, hits = self.i32_at(base), self.i32_at(base + 4)
        at = lambda i: self.i32_at(base + 4 * i)  # noqa: E731
        c, lines = 2, []
        for _ in range(items):
            kind = at(c)
            if kind == 0:
                x, y, w, h, rgb = (at(c + i) for i in range(1, 6))
                lines.append(f"rect {x} {y} {w} {h} {_rgb(rgb)}")
                c += 6
            elif kind == 1:
                x, y, r, rgb = (at(c + i) for i in range(1, 5))
                lines.append(f"dot {x} {y} {r} {_rgb(rgb)}")
                c += 5
            elif kind == 2:
                x, y, scale, rgb, n = (at(c + i) for i in range(1, 6))
                s = "".join(chr(at(c + 6 + i)) for i in range(n))
                lines.append(f"text {x} {y} {scale} {_rgb(rgb)} {s}")
                c += 6 + n
            else:
                raise AssertionError(f"unknown record kind {kind}")
        for _ in range(hits):
            kind, axis, extra = at(c), at(c + 1), at(c + 2)
            assert kind == 3, "a substrate's attachments are channels"
            x0, y0, x1, y1 = (at(c + i) for i in range(3, 7))
            lines.append(
                f"hit {'xy'[axis]} {extra} {x0} {y0} {x1} {y1}")
            c += 7
        return lines


def _rgb(word: int) -> str:
    return f"{(word >> 16) & 255} {(word >> 8) & 255} {word & 255}"


# ── The pieces, and the reference they are held to ───────────────────────────

#: Every piece in `examples/audio/` that declares a substrate — the six
#: `card:audiovisual-gallery.md` counted, and the row it turns on.
PIECES = ["chopin.ges", "envelope.ges", "lantern.ges", "mirror.ges",
          "scoped.ges", "spectrum.ges", "substrate.ges"]


def _export(name: str) -> dict:
    """The payload as a plugin gets it — `test_panel_fixtures.py`'s
    `_export`, restated here rather than imported so neither file's
    helpers become the other's contract."""
    from gestate.export import (_BEAT_CHANS, bank_channels, host_graph,
                                substrate_of)

    source = (ROOT / "examples" / "audio" / name).read_text()
    graph = host_graph(source, 48000)
    banked = bank_channels(source)
    knobs = frozenset(n.chan for n in graph.control_sources()
                      if n.chan not in banked and n.chan not in _BEAT_CHANS)
    sub = substrate_of(source, 48000, graph, knobs)
    assert sub is not None, f"{name} declares a `substrate`"
    return sub


def _reference(name: str) -> list[str]:
    """What `gestate/gui.py` draws, from `cx = cy = 0`.

    **Through `gui.Substrate`, not through a walk assembled here**, and
    the difference is the one thing this comparison could have got
    quietly wrong.  A channel's id is allocation order, so one file has
    two correct readings: force the declarations first and `cutoff` is
    0, let the program reach it and `cutoff` is 2.  `Substrate` forces
    them, in declaration order, before anything runs — and so does
    `Canvas::open` on the other side, for the same stated reason.  A
    reference that made the other choice matched every rectangle and
    disagreed about every channel, which is what the first run of this
    file did.

    (`test_panel_fixtures.py` deliberately makes the *other* choice, and
    is right to: the Rust parity fixture it pins forces only `main`.)
    """
    from gestate.gui import Substrate, _attachments, _flatten

    source = (ROOT / "examples" / "audio" / name).read_text()
    canvas = Substrate(source, 48000)
    state, signal = canvas.state, canvas.signal
    lines = []
    for item in _flatten(signal.value, state):
        if item[0] == "rect":
            _, x, y, w, h, (r, g, b) = item
            lines.append(f"rect {x} {y} {w} {h} {r} {g} {b}")
        elif item[0] == "dot":
            _, x, y, rad, (r, g, b) = item
            lines.append(f"dot {x} {y} {rad} {r} {g} {b}")
        elif item[0] == "text":
            _, x, y, text, (r, g, b), scale = item
            lines.append(f"text {x} {y} {scale} {r} {g} {b} {text}")
        else:
            raise AssertionError(f"unknown item kind {item[0]!r}")
    for hit in _attachments(signal.value, state):
        x0, y0, x1, y1 = hit["region"]
        lines.append(f"hit {hit['axis']} {hit['chan']} {x0} {y0} {x1} {y1}")
    return lines


# ── The module itself ────────────────────────────────────────────────────────


@needs_cargo
@needs_wasm
def test_the_module_asks_the_page_for_nothing(module_path):
    """Zero imports is the property that makes a gallery cheap.

    A page supplies no host functions and no glue: `crust`'s
    zero-dependency rule, and the panel's pure half under `substrate`,
    reaching the browser intact.  For scale, `card:online.md` C1's
    Pyodide is 10 MB.
    """
    from gestate.audiowasm import imports_of

    assert imports_of(module_path) == []
    size = module_path.stat().st_size
    assert size < 512 * 1024, f"{size} bytes — the module got heavy"


@needs_cargo
@needs_wasm
@pytest.mark.parametrize("name", PIECES)
def test_every_piece_draws_in_wasm_what_the_reference_draws(module_path, name):
    """The row `card:audiovisual-gallery.md` turns on, executed.

    Six pieces declare a picture and the tab drops it on the floor.
    Here each one is walked by the module a browser would load, and the
    picture that comes back over the wire is compared line for line with
    the one `gui.py` draws — the definition of correct.
    """
    tab = Tab(module_path)
    tab.open(_export(name))
    tab.tick()
    assert tab.display() == _reference(name)


@needs_cargo
@needs_wasm
def test_a_declared_channel_keeps_the_id_the_program_sees(module_path):
    """Names cross, not ids.

    An id is allocated when a declaration is first forced, so it depends
    on what the host forces and in what order — which is why the payload
    carries names and the shell keeps whatever ids come back.  What must
    hold is that the id a page is told matches the one the *picture*
    carries, or a touch would write a channel nothing is listening on.
    """
    tab = Tab(module_path)
    sub = _export("substrate.ges")
    tab.open(sub)
    tab.tick()
    hit = [ln for ln in tab.display() if ln.startswith("hit ")]
    assert len(hit) == 1, hit
    assert int(hit[0].split()[2]) == tab.channel("cutoff")
    assert tab.channel("nosuchchannel") == -1


@needs_cargo
@needs_wasm
def test_an_arrival_moves_the_picture(module_path):
    """One fold, two readers — in a tab.

    A value arrives on the channel the program declared, the sweep
    advances every live signal by one instant, and the same fold the
    synth would read is the one the canvas redraws.  Without this a
    gallery is a recording you cannot stop, which is the sentence the
    card was written from.
    """
    tab = Tab(module_path)
    tab.open(_export("substrate.ges"))
    tab.tick()
    before = tab.display()

    chan = tab.channel("cutoff")
    tab.tick(writes=[(chan, 0.95)])
    after = tab.display()

    assert before != after, "the sweep ran and the picture stood still"
    assert len(before) == len(after), "the same elements, in the same order"
    assert [ln for ln in before if ln.startswith("hit ")] == \
           [ln for ln in after if ln.startswith("hit ")], \
        "and the fader listens over the box it declared, not what it painted"


@needs_cargo
@needs_wasm
def test_a_hand_reaches_the_program_through_the_wire(module_path):
    """A press finds the deepest attachment it lands on and writes
    **the channel that attachment carries** — nothing routed by name,
    nothing registered.  Then the next frame draws the consequence,
    which is the whole loop a controllable piece is."""
    tab = Tab(module_path)
    tab.open(_export("substrate.ges"))
    tab.tick()
    _, _, chan, x0, y0, x1, y1 = tab.display()[-1].split()
    # **Near the top of the element, not its middle.**  A fader's value
    # is a fraction of its own extent, and the middle is where
    # `substrate.ges` starts — a press there is a correct gesture that
    # moves nothing, which says nothing about whether the hand arrived.
    x = (int(x0) + int(x1)) // 2
    y = int(y0) + 2

    assert tab.call("web_grabbing", tab.w) == 0
    assert tab.call("web_press", tab.w, x, y) == 1
    assert tab.call("web_grabbing", tab.w) == 1

    out = tab.call("web_writes", tab.w)
    assert int(tab.f64_at(out)) == int(chan)
    value = tab.f64_at(out + 8)
    assert 0.0 <= value <= 1.0, value

    before = tab.display()
    tab.tick(writes=[(int(chan), value)])
    assert tab.display() != before, "the hand reached the program"

    tab.call("web_release", tab.w)
    assert tab.call("web_grabbing", tab.w) == 0


@needs_cargo
@needs_wasm
def test_a_program_that_is_not_a_picture_is_refused_with_a_sentence(
        module_path):
    """A gallery visits fifty pages.  One that cannot draw must say so
    and leave the tab standing — the page has a notice bar and a wasm
    trap has nothing."""
    tab = Tab(module_path)
    sub = dict(_export("substrate.ges"))
    sub["text"] = ("crust 1\nblock\nI PushInt 1\nI Update 0\nI Unwind\n"
                   "global main 0 0\nentry main\n")
    text, text_len = tab.put(sub["text"].encode())
    entry, entry_len = tab.put(b"main")
    tags = tab.put_i64(sub["tags"])
    assert tab.call("web_open", text, text_len, entry, entry_len,
                    tags, 0, 0) == 0
    assert "main" in tab.text_at(tab.call("web_error", 0))


@needs_cargo
@needs_wasm
def test_a_frame_is_not_the_risk(module_path):
    """The measurement `card:audiovisual-gallery.md` bounded and did not
    take: a frame, in the target that will actually run it.

    The card timed the *reference* — `gui.Substrate` in CPython, 8.74 ms
    for the heaviest piece against a 60 Hz budget of 16.7 ms — and
    marked the wasm number as a bound rather than a measurement.  This
    is the measurement.  The threshold is deliberately loose: what is
    being refused is an implementation that cannot draw at all, not a
    millisecond somebody has to defend on a different machine.
    """
    import time

    tab = Tab(module_path)
    tab.open(_export("envelope.ges"))
    tab.tick()                                  # the first frame builds
    start = time.perf_counter()
    for _ in range(20):
        tab.tick()
        tab.display()
    each = (time.perf_counter() - start) / 20 * 1000
    assert each < 16.7, f"{each:.2f} ms a frame — under a 60 Hz budget"
