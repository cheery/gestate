"""The icon — an egg with a signal growing inside it.  `fixme.md` F148.

    python -m gestate.icon      # rewrite doc/gestate.svg, doc/gestate.argb

**One drawing, and everybody is handed it.**  The shape is the
constants below.  From them this writes the two committed files, and
everything that shows the icon reads one of those:

* `doc/gestate.svg` — the artwork.  The README's header, the scalable
  icon `--desktop` installs, and any launcher pointed at the tree.
* `doc/gestate.argb` — the same drawing rasterised into what
  `_NET_WM_ICON` wants, which `shell/editor` compiles in with
  `include_bytes!`.  That is the icon a taskbar and an alt-tab read.
* `png`, for the sizes a desktop's `hicolor` directory wants on disk.

**Why that is worth a module.**  The window used to draw its own icon —
one period of a sine in the caret's blue, eight lines, no asset to go
missing — and `workbench` drew the same sine again in Python for the
`hicolor` PNGs.  Good rule, wrong picture: the front page had an egg
and the taskbar had a sine, and it took a fresh install on a second
laptop to put the two on one desk, because **two drawings of one icon
never appear on the same screen**.  The load-bearing half of that rule
is untouched here — the crate decodes nothing and reads nothing from
disk at run time — and the half that let them drift is gone.

**The recovered recipe.**  The original generator was never committed
(`a3484ba` added the SVG alone).  It is back, fitted from the 121
points it left behind: three cycles, an amplitude that starts almost
still and grows as `t ** 1.35`.  Every point of the committed path
comes back to the decimal it was written with, which is
`test_icon.py`'s business and the reason the fit can be believed.
"""

from __future__ import annotations

import math
import struct
import zlib
from pathlib import Path

#: The drawing's own square.  Everything below is in these units, and a
#: raster is this scaled by `side / SIDE`.
SIDE = 256

#: The shell: four cubics, clockwise from the point.  Narrow at the top
#: and round at the bottom, which is what makes it an egg and not an
#: ellipse — the widest line is at y=142, below the middle.
EGG: tuple[tuple[float, ...], ...] = (
    (128, 26, 170, 26, 200, 84, 200, 142),
    (200, 142, 200, 192, 168, 228, 128, 228),
    (128, 228, 88, 228, 56, 192, 56, 142),
    (56, 142, 56, 84, 86, 26, 128, 26),
)

#: The signal, as the arithmetic that draws it:
#:
#:     x = X0 + (X1 - X0) * t
#:     y = MID - (STILL + GAIN * t ** CURVE) * sin(tau * CYCLES * t)
#:
#: over `t = i / STEPS`.  `STILL` is the whole point of the picture and
#: the reason the amplitude does not start at zero: a program that is
#: already alive is never silent, it develops.
X0, X1 = 70.0, 174.0
MID = 132.0
STEPS = 120
CYCLES = 3
STILL, GAIN, CURVE = 3.0, 26.0, 1.35

#: Where the signal is going, which is out of the picture.
DOT = (184.0, 132.0, 8.0)

SHELL = "#2b7a78"      #: the egg
SIGNAL = "#e8a13d"     #: the wave, and the dot
SHELL_W = 11.0
SIGNAL_W = 7.5

#: A stroke thinner than this, in device pixels, is a grey suggestion
#: rather than a line — at 16 px the shell would be 0.7 px wide.  Both
#: widths are lifted by one factor when the thinner one falls under it,
#: so the drawing thickens without changing its proportions.
MIN_INK = 1.15


def wave(cycles: int = CYCLES,
         inset: float = 0.0) -> list[tuple[float, float]]:
    """The signal's points — `STEPS + 1` of them, evenly spaced in x.

    Neither argument is a knob anybody turns by hand.  `cycles` is three,
    and a small raster asks for fewer because three of them do not fit in
    six pixels; `inset` pulls the ends in by whatever a thickened stroke
    added to them, so a hinted wave stops where the artwork's wave stops
    instead of growing into the shell (`shown`, `_hint`).  The envelope
    is untouched either way: the signal still starts almost still and
    still ends at full amplitude.
    """
    out = []
    for i in range(STEPS + 1):
        t = i / STEPS
        amp = STILL + GAIN * t ** CURVE
        out.append((X0 + inset + (X1 - X0 - 2 * inset) * t,
                    MID - amp * math.sin(math.tau * cycles * t)))
    return out


def _shell_path() -> str:
    """`EGG` as SVG, wrapped where the committed file wraps it.

    Written out rather than kept as a string beside the numbers,
    because a path and a copy of the same path in another notation is
    the arrangement this whole file exists to stop repeating.
    """
    curves = [" ".join(f"{seg[i]:g},{seg[i + 1]:g}" for i in (2, 4, 6))
              for seg in EGG]
    head = f"M{EGG[0][0]:g},{EGG[0][1]:g} C" + " C".join(curves[:2])
    tail = "C" + " C".join(curves[2:]) + " Z"
    return f'{head}\n           {tail}'


def svg() -> str:
    """`doc/gestate.svg`, rendered from the constants above."""
    d = " ".join(f"{'M' if i == 0 else 'L'}{x:.1f},{y:.1f}"
                 for i, (x, y) in enumerate(wave()))
    cx, cy, r = DOT
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {SIDE} {SIDE}"'
        f' width="{SIDE}" height="{SIDE}">\n'
        '  <!-- gestate: a signal carried to term.  The egg is the program;'
        ' the\n'
        '       wave inside starts almost still and grows to full amplitude'
        ' -\n'
        '       live update means it develops while it is already alive.'
        ' -->\n'
        f'  <path d="{_shell_path()}"\n'
        f'        fill="none" stroke="{SHELL}" stroke-width="{SHELL_W:g}"\n'
        '        stroke-linecap="round"/>\n'
        f'  <path d="{d}"\n'
        f'        fill="none" stroke="{SIGNAL}" stroke-width="{SIGNAL_W:g}"\n'
        '        stroke-linecap="round" stroke-linejoin="round"/>\n'
        f'  <circle cx="{cx:.1f}" cy="{cy:.1f}" r="{r:g}"'
        f' fill="{SIGNAL}"/>\n'
        '</svg>\n')


# ── The rasteriser, of which there is one ───────────────────────────────────
#
# Everything raster comes through here: the `hicolor` PNGs a desktop reads
# and the `_NET_WM_ICON` bytes the window carries.  A stroke is a polyline —
# for each segment, walk the pixels its neighbourhood covers and keep the
# nearest distance; ink where that distance is inside half the width, faded
# over the last pixel so a curve at 16 px is a curve and not a staircase.
#
# Pure Python and quadratic in the stroke's neighbourhood, which is fine
# for what this is: a sixth of a second for the 256, and it runs when
# somebody changes the icon rather than when somebody opens the editor.

#: How finely a cubic becomes a polyline.  Sixteen is past the point where
#: another point would move a pixel at 256.
FLATTEN = 16


def _cubic(seg: tuple[float, ...]) -> list[tuple[float, float]]:
    x0, y0, x1, y1, x2, y2, x3, y3 = seg
    out = []
    for i in range(FLATTEN + 1):
        t = i / FLATTEN
        u = 1.0 - t
        out.append((u * u * u * x0 + 3 * u * u * t * x1
                    + 3 * u * t * t * x2 + t * t * t * x3,
                    u * u * u * y0 + 3 * u * u * t * y1
                    + 3 * u * t * t * y2 + t * t * t * y3))
    return out


def egg() -> list[tuple[float, float]]:
    """The shell as one closed polyline, the way it is rasterised."""
    out: list[tuple[float, float]] = []
    for seg in EGG:
        pts = _cubic(seg)
        out.extend(pts[1:] if out else pts)
    return out


#: Clearance in device pixels between signal and shell, on top of what
#: the thickening already accounts for.  A quarter of a pixel, which is
#: the whole difference between one touching pixel at 16 px and none.
CLEAR = 0.25


def _hint(side: int) -> float:
    """The one factor that keeps a small icon from fading out."""
    thin = SIGNAL_W * side / SIDE
    return max(1.0, MIN_INK / thin) if thin > 0 else 1.0


def _inset(side: int) -> float:
    """How far the signal's ends come in when the strokes are hinted.

    A hinted stroke grows both ways, so at 16 px the shell thickens
    *inward* by as much as the signal thickens outward — pull the signal
    in by both, or the two meet and the icon is a smear.  At a size that
    needs no hinting this is zero, so the big raster is the artwork.
    """
    h = _hint(side)
    return (h - 1.0) * ((SHELL_W + SIGNAL_W) / 2.0 + CLEAR * SIDE / side)


def _rgb(text: str) -> tuple[int, int, int]:
    return (int(text[1:3], 16), int(text[3:5], 16), int(text[5:7], 16))


class _Sheet:
    """A square of straight-alpha RGBA, painted source-over."""

    def __init__(self, side: int) -> None:
        self.side = side
        self.px = [[0.0, 0.0, 0.0, 0.0] for _ in range(side * side)]

    def _ink(self, x: int, y: int, cover: float,
             rgb: tuple[int, int, int]) -> None:
        if cover <= 0.0:
            return
        cell = self.px[y * self.side + x]
        a = cell[3] * (1.0 - cover)
        total = cover + a
        if total <= 0.0:
            return
        for c in range(3):
            cell[c] = (rgb[c] * cover + cell[c] * a) / total
        cell[3] = total

    def stroke(self, points: list[tuple[float, float]], width: float,
               rgb: tuple[int, int, int], scale: float) -> None:
        half = width / 2.0
        reach = half + 1.0
        for (ax, ay), (bx, by) in zip(points, points[1:]):
            ax, ay, bx, by = ax * scale, ay * scale, bx * scale, by * scale
            dx, dy = bx - ax, by - ay
            span = dx * dx + dy * dy
            lo_x = max(0, int(math.floor(min(ax, bx) - reach)))
            hi_x = min(self.side - 1, int(math.ceil(max(ax, bx) + reach)))
            lo_y = max(0, int(math.floor(min(ay, by) - reach)))
            hi_y = min(self.side - 1, int(math.ceil(max(ay, by) + reach)))
            for y in range(lo_y, hi_y + 1):
                for x in range(lo_x, hi_x + 1):
                    px, py = x + 0.5, y + 0.5
                    if span > 0.0:
                        t = ((px - ax) * dx + (py - ay) * dy) / span
                        t = 0.0 if t < 0.0 else (1.0 if t > 1.0 else t)
                    else:
                        t = 0.0
                    ex, ey = px - (ax + t * dx), py - (ay + t * dy)
                    d = math.hypot(ex, ey)
                    # The round cap and join come for free: a segment's
                    # distance field is already a capsule, and painting
                    # each one over the last joins them roundly.
                    self._ink(x, y, min(1.0, max(0.0, half + 0.5 - d)), rgb)

    def disc(self, cx: float, cy: float, r: float,
             rgb: tuple[int, int, int]) -> None:
        lo_x = max(0, int(math.floor(cx - r - 1)))
        hi_x = min(self.side - 1, int(math.ceil(cx + r + 1)))
        lo_y = max(0, int(math.floor(cy - r - 1)))
        hi_y = min(self.side - 1, int(math.ceil(cy + r + 1)))
        for y in range(lo_y, hi_y + 1):
            for x in range(lo_x, hi_x + 1):
                d = math.hypot(x + 0.5 - cx, y + 0.5 - cy)
                self._ink(x, y, min(1.0, max(0.0, r + 0.5 - d)), rgb)

    def rgba(self) -> bytes:
        out = bytearray()
        for r, g, b, a in self.px:
            out += bytes((int(r + 0.5), int(g + 0.5), int(b + 0.5),
                          int(a * 255.0 + 0.5)))
        return bytes(out)


#: A cycle needs about this many pixels of width to be a cycle rather
#: than a wobble in a smear.  Below it the signal is drawn as one.
PER_CYCLE = 4.0

#: And the dot is only worth drawing while it is clearly *beside* the
#: shell: it sits 2.5 units short of the stroke in a 256-unit drawing,
#: so under a pixel of that gap it stops being a full stop and becomes
#: a lump on the egg.
GAP = (EGG[0][6] - SHELL_W / 2.0) - (DOT[0] + DOT[2])


def shown(side: int) -> tuple[int, bool]:
    """How much of the signal fits at `side` px: cycles, and the dot."""
    k = side / SIDE
    room = int((X1 - X0) * k / PER_CYCLE)
    return max(1, min(CYCLES, room)), GAP * k >= 1.0


def sheet(side: int) -> _Sheet:
    """The icon at `side` pixels, drawn — shell, then signal, then dot."""
    s = _Sheet(side)
    k = side / SIDE
    h = _hint(side)
    cycles, dot = shown(side)
    cx, cy, r = DOT
    s.stroke(egg(), SHELL_W * k * h, _rgb(SHELL), k)
    s.stroke(wave(cycles, _inset(side)), SIGNAL_W * k * h, _rgb(SIGNAL), k)
    if dot:
        s.disc(cx * k, cy * k, r * k, _rgb(SIGNAL))
    return s


#: The sizes a desktop's `hicolor` directory wants on disk, beside the
#: scalable copy — `workbench.install_desktop` writes these.
HICOLOR = (16, 32, 48, 128, 256)

#: The sizes the window carries itself, for the taskbar and alt-tab of a
#: desktop that never saw a `.desktop` file.  Small, because this rides
#: in an X property and is paid for on every window it is set on.
WINDOW = (16, 32, 48, 64)


def face() -> bytes:
    """`doc/gestate.argb` — the icon as `shell/editor` compiles it in.

    **Why the window is handed pixels instead of drawing its own.**  It
    used to draw its own, and that is the whole bug this file exists to
    close: a second drawing in a second language is a second icon, and
    the two only ever appear on different screens, so nothing catches
    the drift.  There is one rasteriser now — the one above — and the
    window gets what it renders.

    The bytes are exactly what `_NET_WM_ICON` wants, little-endian:
    width, height, then straight-alpha ARGB rows, once per size.  So
    `window.rs` widens each `u32` to a `c_ulong` and hands the lot to
    `XChangeProperty` — no decoder, and nothing to go missing at run
    time, which were the two good reasons the drawing was in the crate.
    """
    out = bytearray()
    for side in WINDOW:
        out += struct.pack("<II", side, side)
        rgba = sheet(side).rgba()
        for i in range(0, len(rgba), 4):
            r, g, b, a = rgba[i:i + 4]
            out += struct.pack("<I", (a << 24) | (r << 16) | (g << 8) | b)
    return bytes(out)


def png(side: int) -> bytes:
    """The icon at `side` pixels, as a PNG — stdlib only, no encoder."""
    rgba = sheet(side).rgba()
    raw = bytearray()
    for y in range(side):
        raw.append(0)                                    # filter: none
        raw += rgba[y * side * 4:(y + 1) * side * 4]

    def chunk(tag: bytes, data: bytes) -> bytes:
        body = tag + data
        return (struct.pack(">I", len(data)) + body
                + struct.pack(">I", zlib.crc32(body)))

    return (b"\x89PNG\r\n\x1a\n"
            + chunk(b"IHDR", struct.pack(">IIBBBBB", side, side,
                                         8, 6, 0, 0, 0))
            + chunk(b"IDAT", zlib.compress(bytes(raw)))
            + chunk(b"IEND", b""))


def main(argv=None) -> int:
    """Rewrite the two committed files, which `test_icon.py` checks.

    Deterministic on purpose, the same way `atlas` is: no timestamp, no
    hash, so a generated file that changes when nothing changed cannot
    train anybody to stop regenerating it.
    """
    doc = Path(__file__).resolve().parent.parent / "doc"
    wrote = False
    for name, made in (("gestate.svg", svg().encode()),
                       ("gestate.argb", face())):
        where = doc / name
        if where.exists() and where.read_bytes() == made:
            print(f"{where} is already what the source renders")
            continue
        where.write_bytes(made)
        print(f"wrote {where}")
        wrote = True
    if wrote:
        print("the crate compiles gestate.argb in — `cargo build` to "
              "put it in the window")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
