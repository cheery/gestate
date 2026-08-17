"""The icon is one drawing — `gestate/icon.py`.

It was two.  The front page had an egg and the taskbar had a sine, for
a week, on two machines, and nobody saw it because the two drawings
never appear on the same screen: the SVG is read in a browser and the
`_NET_WM_ICON` is read in a dock.  That is the defect this file is
here to make impossible, and it is why the checks below are about
*sameness* rather than about pixels being pretty.

Same shape of guarantee as `test_atlas.py`, and the same sentence when
it breaks: **run `python -m gestate.icon`.**
"""

from __future__ import annotations

import struct
import zlib
from pathlib import Path

from gestate import icon

ROOT = Path(__file__).resolve().parent.parent
REDO = "run `python -m gestate.icon`"


def test_the_committed_artwork_is_what_the_source_renders():
    """`doc/gestate.svg` is generated, and this is what that is worth."""
    assert icon.svg() == (ROOT / "doc" / "gestate.svg").read_text(), REDO


def test_the_recovered_recipe_still_draws_the_committed_wave():
    """**The generator was lost, and this is what keeps it found.**

    `a3484ba` committed the SVG with no script beside it; the recipe in
    `icon.py` was fitted back out of the 121 points it left behind, and
    every one of them returns to the decimal it was written with.  A
    fit is only a claim about the numbers that were fitted, so the
    numbers are the test.
    """
    import re

    path = re.findall(r'd="([^"]+)"',
                      (ROOT / "doc" / "gestate.svg").read_text())[1]
    were = [(float(a), float(b))
            for a, b in re.findall(r"(-?[\d.]+),(-?[\d.]+)", path)]
    now = icon.wave()
    assert len(were) == len(now) == icon.STEPS + 1
    for (wx, wy), (nx, ny) in zip(were, now):
        assert (round(nx, 1), round(ny, 1)) == (wx, wy)


def test_the_window_wears_what_this_renders():
    """`doc/gestate.argb` is compiled into `shell/editor` — so if it is
    not what `icon.py` renders, the window is wearing an old face and
    the dock beside it is wearing the new one."""
    assert icon.face() == (ROOT / "doc" / "gestate.argb").read_bytes(), REDO


def test_the_crate_compiles_in_the_file_this_writes():
    """The other half of that: an `include_bytes!` pointed somewhere
    else would leave the check above passing and the window unchanged."""
    src = (ROOT / "shell" / "editor" / "src" / "window.rs").read_text()
    assert 'include_bytes!("../../../doc/gestate.argb")' in src, \
        "window.rs no longer compiles in the icon this file checks"


def test_editing_the_icon_rebuilds_the_window():
    """`editor._stale` decides whether the `.so` is rebuilt on a start,
    and it was written when every source of it was a `.rs` file.  The
    icon is a source now and is not one — so an icon change that does
    not appear in the running window would be the same silent failure
    that docstring is about, in a new place."""
    from gestate import editor

    crate = ROOT / "shell" / "editor"
    assert ROOT / "doc" / "gestate.argb" in editor._watched(crate)


def test_the_property_is_laid_out_the_way_x11_reads_it():
    """`_NET_WM_ICON` is width, height, then that many pixels, repeated
    — the file *is* the property, which is what lets the Rust widen it
    to `c_ulong` and hand it over without decoding anything."""
    data = icon.face()
    at, found = 0, []
    while at < len(data):
        w, h = struct.unpack_from("<II", data, at)
        found.append(w)
        assert w == h, "the icon is square at every size"
        at += 8 + w * h * 4
    assert at == len(data), "a size claims more pixels than are there"
    assert tuple(found) == icon.WINDOW


def test_every_size_is_a_transparent_egg_with_a_signal_in_it():
    """**What went wrong was that nobody looked**, so these are the
    three things a glance would have caught: the shell is there, the
    signal is there, and the ground shows through.

    Colours are counted rather than sampled at a point, because a
    stroke moves by a pixel between sizes and a sampled point would
    make this test about hinting instead of about the drawing.
    """
    for side in icon.HICOLOR:
        sheet = icon.sheet(side)
        shell = icon._rgb(icon.SHELL)
        signal = icon._rgb(icon.SIGNAL)

        def near(px, want, tol=40):
            return (px[3] > 0.5
                    and all(abs(px[i] - want[i]) <= tol for i in range(3)))

        teal = sum(1 for p in sheet.px if near(p, shell))
        amber = sum(1 for p in sheet.px if near(p, signal))
        clear = sum(1 for p in sheet.px if p[3] < 0.02)
        assert teal >= 8, f"no shell at {side} px"
        assert amber >= 4, f"no signal at {side} px"
        # The corners at least, and the whole ground the egg is not on.
        assert clear > side * side * 0.5, f"{side} px is not transparent"


def test_the_signal_never_touches_the_shell():
    """The reason `_inset` exists.  At 16 px both strokes are hinted
    thicker to stay visible, the shell grows inward while the signal
    grows outward, and where they meet the icon stops being an egg with
    something inside it and becomes a blob."""
    for side in icon.HICOLOR + icon.WINDOW:
        k = side / icon.SIDE
        h = icon._hint(side)
        cycles, _dot = icon.shown(side)
        shell = icon._Sheet(side)
        shell.stroke(icon.egg(), icon.SHELL_W * k * h, (0, 0, 0), k)
        signal = icon._Sheet(side)
        signal.stroke(icon.wave(cycles, icon._inset(side)),
                      icon.SIGNAL_W * k * h, (0, 0, 0), k)
        both = [1 for a, b in zip(shell.px, signal.px)
                if a[3] > 0.25 and b[3] > 0.25]
        assert not both, f"{side} px: the signal runs into the shell"


def test_a_small_icon_drops_what_it_cannot_draw():
    """Three cycles in six pixels is a smudge, so a small raster draws
    fewer — and the dot goes when it would land on the shell rather
    than beside it.  The artwork itself is never simplified."""
    assert icon.shown(16) == (1, False)
    assert icon.shown(256) == (icon.CYCLES, True)
    for side in icon.HICOLOR:
        cycles, _ = icon.shown(side)
        assert 1 <= cycles <= icon.CYCLES


def test_the_pngs_are_pngs():
    """Written by hand out of `zlib` and `struct`, so the header, the
    dimensions and the checksums are worth one look."""
    for side in (16, 256):
        data = icon.png(side)
        assert data[:8] == b"\x89PNG\r\n\x1a\n"
        w, h, depth, kind = struct.unpack_from(">IIBB", data, 16)
        assert (w, h, depth, kind) == (side, side, 8, 6), "8-bit RGBA"
        at = 8
        while at < len(data):
            length, tag = struct.unpack_from(">I4s", data, at)
            body = data[at + 4:at + 8 + length]
            assert zlib.crc32(body) == struct.unpack_from(
                ">I", data, at + 8 + length)[0], f"{tag!r} checksum"
            at += 12 + length
        assert at == len(data)
