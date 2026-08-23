#: asked-by: unrecorded, 2026-08-11
"""Read an X11 PCF bitmap font — enough of it to lift the glyphs out.

`shell/editor` blits a bitmap font because that is what makes a
software-rendered editor cheap: no hinting, no antialiasing, no shaping,
no glyph cache, no rasterizer dependency.  A row of a glyph is a handful
of bits and drawing a line of text is a loop over bytes.

The font is the X11 **misc-fixed** family, which is on every machine
with X fonts installed and whose licence is, in full:

    font-misc-misc/COPYING:
        "Public domain font.  Share and enjoy."

No attribution, no reserved name, no licence to ship beside it — which
is the whole reason it was chosen over Terminus (OFL), Cozette (MIT) or
an outline font needing a rasterizer.

This is a **generator**, run once; its output is committed Rust and read
by looking at the letters.  PCF is a documented fixed binary format and
nothing here is clever: the fiddliness is paid at build time and never
by the editor.
"""

from __future__ import annotations

import gzip
import struct
from pathlib import Path

PCF_METRICS = 0x04
PCF_BITMAPS = 0x08
PCF_BDF_ENCODINGS = 0x20

PCF_GLYPH_PAD_MASK = 3
PCF_BYTE_MASK = 4
PCF_BIT_MASK = 8
PCF_COMPRESSED_METRICS = 0x100


class Reader:
    """A cursor over one table, in that table's own byte order."""

    def __init__(self, data: bytes, at: int, big: bool):
        self.d, self.at, self.e = data, at, ">" if big else "<"

    def u8(self) -> int:
        v = self.d[self.at]
        self.at += 1
        return v

    def u16(self) -> int:
        (v,) = struct.unpack_from(self.e + "H", self.d, self.at)
        self.at += 2
        return v

    def i16(self) -> int:
        (v,) = struct.unpack_from(self.e + "h", self.d, self.at)
        self.at += 2
        return v

    def u32(self) -> int:
        (v,) = struct.unpack_from(self.e + "I", self.d, self.at)
        self.at += 4
        return v


def _tables(data: bytes) -> dict:
    if data[:4] != b"\x01fcp":
        raise ValueError("not a PCF file")
    (count,) = struct.unpack_from("<I", data, 4)
    out = {}
    for i in range(count):
        kind, fmt, size, off = struct.unpack_from("<4I", data, 8 + i * 16)
        out[kind] = (fmt, size, off)
    return out


def read(path: Path) -> dict:
    """`{codepoint: (rows, width, height, ascent)}`, rows MSB-first.

    Every glyph is padded to the font's own box, so the caller gets a
    rectangular cell and the editor never asks how wide a letter is —
    the same rule the substrate's labels keep, for the same reason.
    """
    raw = path.read_bytes()
    data = gzip.decompress(raw) if path.suffix == ".gz" else raw
    tables = _tables(data)

    # ── metrics ──────────────────────────────────────────────────────
    fmt, _size, off = tables[PCF_METRICS]
    big = bool(fmt & PCF_BYTE_MASK)
    r = Reader(data, off + 4, big)
    metrics = []
    if fmt & PCF_COMPRESSED_METRICS:
        n = r.u16()
        for _ in range(n):
            lsb, rsb, w, asc, desc = (r.u8() - 0x80 for _ in range(5))
            metrics.append((lsb, rsb, w, asc, desc))
    else:
        n = r.u32()
        for _ in range(n):
            lsb, rsb, w, asc, desc = (r.i16() for _ in range(5))
            r.u16()                                   # attributes
            metrics.append((lsb, rsb, w, asc, desc))

    # ── bitmaps ──────────────────────────────────────────────────────
    fmt, _size, off = tables[PCF_BITMAPS]
    big = bool(fmt & PCF_BYTE_MASK)
    msb_first = bool(fmt & PCF_BIT_MASK)
    pad = 1 << (fmt & PCF_GLYPH_PAD_MASK)
    r = Reader(data, off + 4, big)
    count = r.u32()
    offsets = [r.u32() for _ in range(count)]
    sizes = [r.u32() for _ in range(4)]
    base = r.at
    blob = data[base:base + sizes[fmt & PCF_GLYPH_PAD_MASK]]

    # ── encodings ────────────────────────────────────────────────────
    fmt, _size, off = tables[PCF_BDF_ENCODINGS]
    big = bool(fmt & PCF_BYTE_MASK)
    r = Reader(data, off + 4, big)
    min2, max2, min1, max1, _default = (r.u16() for _ in range(5))
    glyphs = {}
    for b1 in range(min1, max1 + 1):
        for b2 in range(min2, max2 + 1):
            idx = r.u16()
            if idx == 0xFFFF:
                continue
            code = b2 if min1 == max1 == 0 else (b1 << 8) | b2
            glyphs[code] = idx

    # The font's box: the widest advance and the tallest ascent+descent,
    # which for a fixed font is every glyph's.
    width = max(m[2] for m in metrics)
    ascent = max(m[3] for m in metrics)
    descent = max(m[4] for m in metrics)
    height = ascent + descent

    out = {}
    for code, idx in glyphs.items():
        lsb, _rsb, _w, asc, desc = metrics[idx]
        gw = _rsb - lsb
        gh = asc + desc
        row_bytes = ((gw + 7) // 8 + pad - 1) // pad * pad
        start = offsets[idx]
        rows = [0] * height
        for y in range(gh):
            acc = 0
            for b in range(row_bytes):
                byte = blob[start + y * row_bytes + b]
                if not msb_first:
                    byte = int(f"{byte:08b}"[::-1], 2)
                acc = (acc << 8) | byte
            acc >>= row_bytes * 8 - gw if gw else 0
            # Into the cell: left bearing across, baseline down.
            shifted = acc << (width - gw - lsb) if width - gw - lsb >= 0 else acc
            y_in_cell = ascent - asc + y
            if 0 <= y_in_cell < height:
                rows[y_in_cell] = shifted
        out[code] = (rows, width, height, ascent)
    return out


def show(glyph, width: int) -> str:
    rows, w, _h, _a = glyph
    return "\n".join("".join("#" if r >> (w - 1 - x) & 1 else "."
                             for x in range(w)) for r in rows)


if __name__ == "__main__":
    import sys
    path = Path(sys.argv[1] if len(sys.argv) > 1
                else "/usr/share/fonts/X11/misc/6x13.pcf.gz")
    g = read(path)
    print(f"{path.name}: {len(g)} glyphs, cell {g[65][1]}x{g[65][2]}, "
          f"ascent {g[65][3]}")
    for ch in "Ag@_":
        print(f"--- {ch!r} ---")
        print(show(g[ord(ch)], g[ord(ch)][1]))


# ── Generating the editor's tables ───────────────────────────────────────

#: What to carry.  **Measured, not guessed**: every character in this
#: repository's sources, plus the blocks a person plausibly types.
#: Above this the font still has glyphs and the editor draws a filled
#: block, which is the same honest "unknown character" the 3×5 chrome
#: font already gives.
CEILING = 0x2C00


def emit(path: Path, name: str, out_dir: Path) -> tuple:
    """Write `<name>.bin` and `<name>.idx`, return `(cell, count)`.

    **Two binary files rather than a table of literals.**  Five
    thousand glyphs is two hundred kilobytes; as `0x..` in a `.rs` it
    would be a megabyte and a half of source for `rustc` to parse every
    build, for data that never changes.  `include_bytes!` costs nothing
    at compile time and nothing at run time.
    """
    g = read(path)
    codes = sorted(c for c in g if c < CEILING)
    _rows, w, h, ascent = g[codes[0]]
    stride = (w + 7) // 8
    blob = bytearray()
    idx = bytearray()
    for c in codes:
        rows, gw, gh, _a = g[c]
        assert (gw, gh) == (w, h), f"{name}: U+{c:04X} is {gw}x{gh}, not {w}x{h}"
        for r in rows:
            # MSB first, left pixel in the top bit — the order
            # `font.rs` blits in.
            v = r << (stride * 8 - w)
            for b in range(stride):
                blob.append((v >> (8 * (stride - 1 - b))) & 0xFF)
        idx += c.to_bytes(4, "little")
    (out_dir / f"{name}.bin").write_bytes(bytes(blob))
    (out_dir / f"{name}.idx").write_bytes(bytes(idx))
    return (w, h, ascent, stride, len(codes))
