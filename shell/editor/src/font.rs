//! A bitmap font, blitted — no rasterizer, no cache, no dependency.
//!
//! **The X11 misc-fixed family**, whose licence is, in full:
//!
//! > `font-misc-misc/COPYING`: *"Public domain font.  Share and enjoy."*
//!
//! No attribution, no reserved font name, no licence to ship beside it,
//! nothing to reason about.  That is why it was chosen over Terminus
//! (OFL), Cozette (MIT) or an outline font — and the *second* reason is
//! the one that matters at run time: it is already a bitmap.  A glyph
//! is a handful of bits, so drawing a screenful of text is a loop over
//! bytes with no hinting, no antialiasing, no shaping, no glyph cache
//! and no per-size atlas to invalidate.  It is the cheapest a character
//! can be put on a screen.
//!
//! Two sizes, both carried: `SMALL` (6×13) for dense views and `LARGE`
//! (10×20) for reading.  Coverage was **measured rather than guessed** —
//! every character in this repository's own sources, `─ — δ ϕ ⊥ ⃝ ∃ ∀ λ`
//! and the Finnish alphabet included, is in both; across three million
//! characters of `.ges`, `.py` and `.md`, seven distinct characters are
//! missing from 10×20 and they occur forty-eight times between them.
//! Those draw as a **filled block**, so an unknown character is visibly
//! unknown rather than a gap that reads as a spacing bug — the same rule
//! the 3×5 chrome font in `gestate-panel` already keeps.
//!
//! The tables are `include_bytes!` rather than arrays of literals:
//! five thousand glyphs is two hundred kilobytes, which as `0x..` in a
//! source file would be a megabyte and a half for `rustc` to parse
//! every build, for data that never changes.
//!
//! `tools/pcf.py` is the generator.  It runs once; what is committed is
//! its output, checked by looking at the letters.

/// One size of the font.
pub struct Font {
    /// Cell width and height in pixels — **every glyph is the same
    /// box**, which is what makes a monospaced grid a grid and means
    /// nothing here ever measures a string.
    pub w: i32,
    pub h: i32,
    /// Pixels from the top of the cell to the baseline.  Carried
    /// because a caret and an underline want it, not because drawing
    /// does.
    pub ascent: i32,
    /// Bytes per row.
    stride: usize,
    /// Codepoints, sorted, four bytes each, parallel to `bits`.
    index: &'static [u8],
    bits: &'static [u8],
}

/// **The zoom ladder.**  Five native sizes, and integer scaling above
/// them.
///
/// A bitmap font cannot be resized — that is the whole reason it is
/// cheap — so zooming is *choosing a different font*, and misc-fixed
/// happens to ship a ladder: 6×13 through 10×20 in five steps, each
/// hand-drawn at its own size rather than sampled from a curve.  Above
/// the largest, a pixel becomes an N×N block, which is chunky and
/// perfectly crisp and is exactly what the panel's 3×5 chrome font
/// already does.
///
/// `(font, scale)`, smallest first.
pub static LADDER: &[(&Font, i32)] = &[
    (&SMALL, 1), (&F7X13, 1), (&F8X13, 1), (&F9X15, 1), (&LARGE, 1),
    (&F9X15, 2), (&LARGE, 2), (&F9X15, 3), (&LARGE, 3),
];

/// Where the ladder starts — 10×20 at one, the size to read code in.
pub const LADDER_DEFAULT: usize = 4;

pub static F7X13: Font = Font {
    w: 7,
    h: 13,
    ascent: 11,
    stride: 1,
    index: include_bytes!("font/7x13.idx"),
    bits: include_bytes!("font/7x13.bin"),
};

pub static F8X13: Font = Font {
    w: 8,
    h: 13,
    ascent: 11,
    stride: 1,
    index: include_bytes!("font/8x13.idx"),
    bits: include_bytes!("font/8x13.bin"),
};

pub static F9X15: Font = Font {
    w: 9,
    h: 15,
    ascent: 12,
    stride: 2,
    index: include_bytes!("font/9x15.idx"),
    bits: include_bytes!("font/9x15.bin"),
};

/// 6×13 — dense, for when the whole file matters more than the line.
pub static SMALL: Font = Font {
    w: 6,
    h: 13,
    ascent: 11,
    stride: 1,
    index: include_bytes!("font/6x13.idx"),
    bits: include_bytes!("font/6x13.bin"),
};

/// 10×20 — the default, and the one to read code in.
pub static LARGE: Font = Font {
    w: 10,
    h: 20,
    ascent: 16,
    stride: 2,
    index: include_bytes!("font/10x20.idx"),
    bits: include_bytes!("font/10x20.bin"),
};

impl Font {
    pub fn count(&self) -> usize {
        self.index.len() / 4
    }

    fn code_at(&self, i: usize) -> u32 {
        let b = &self.index[i * 4..i * 4 + 4];
        u32::from_le_bytes([b[0], b[1], b[2], b[3]])
    }

    /// Where a character's rows are, or `None` if the font lacks it.
    ///
    /// **Binary search, and ASCII gets no special case.**  Thirteen
    /// comparisons for four thousand glyphs, four thousand times a
    /// frame, is under a microsecond in total — measurably less than
    /// the blit that follows it, so a fast path would be complexity
    /// bought with nothing.
    fn find(&self, ch: char) -> Option<usize> {
        let want = ch as u32;
        let (mut lo, mut hi) = (0usize, self.count());
        while lo < hi {
            let mid = (lo + hi) / 2;
            match self.code_at(mid).cmp(&want) {
                std::cmp::Ordering::Less => lo = mid + 1,
                std::cmp::Ordering::Greater => hi = mid,
                std::cmp::Ordering::Equal => return Some(mid),
            }
        }
        None
    }

    /// One glyph's rows, MSB first, the leftmost pixel in the top bit.
    ///
    /// A character the font does not carry comes back as a filled
    /// block, so it is *visibly* unknown.  Returning nothing would draw
    /// a space, and a missing character that looks like a space is a
    /// bug report nobody can write.
    pub fn glyph(&self, ch: char) -> Glyph<'_> {
        match self.find(ch) {
            Some(i) => {
                let n = self.stride * self.h as usize;
                Glyph { rows: &self.bits[i * n..(i + 1) * n],
                        stride: self.stride, w: self.w }
            }
            None => Glyph { rows: &[], stride: self.stride, w: self.w },
        }
    }

    /// Whether the font really has this character, for a caller that
    /// wants to know rather than to draw.
    pub fn has(&self, ch: char) -> bool {
        self.find(ch).is_some()
    }
}

/// One glyph's bits, and how to read them.
pub struct Glyph<'a> {
    rows: &'a [u8],
    stride: usize,
    w: i32,
}

impl Glyph<'_> {
    /// One row of the cell, packed — bit `w-1` is the leftmost pixel.
    ///
    /// **The unit the blit works in.**  Drawing a glyph pixel by pixel
    /// through a bounds-checked accessor cost forty-eight milliseconds
    /// a frame in a debug build, which is an editor you can watch
    /// typing; a row at a time, with the empty ones skipped, is two.
    /// Most rows of most glyphs *are* empty — a cell is twenty tall and
    /// a letter is ten — so the skip is not a micro-optimisation, it is
    /// half the work.
    #[inline]
    pub fn row(&self, y: i32) -> u32 {
        if self.rows.is_empty() {
            // The unknown block: filled, inset by a pixel, so it reads
            // as a box rather than a smear when several land in a row.
            return (((1u32 << (self.w - 2)) - 1) << 1) & self.mask();
        }
        if y < 0 {
            return 0;
        }
        let at = y as usize * self.stride;
        let mut v = 0u32;
        for b in 0..self.stride {
            v = (v << 8) | self.rows.get(at + b).copied().unwrap_or(0) as u32;
        }
        v >> (self.stride * 8 - self.w as usize)
    }

    #[inline]
    fn mask(&self) -> u32 {
        (1u32 << self.w) - 1
    }

    /// Whether the pixel at `(x, y)` inside the cell is set.
    #[inline]
    pub fn on(&self, x: i32, y: i32) -> bool {
        if x < 0 || x >= self.w {
            return false;
        }
        self.row(y) >> (self.w - 1 - x) & 1 == 1
    }

    pub fn missing(&self) -> bool {
        self.rows.is_empty()
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use gestate_panel::list::Colour;
    use gestate_panel::paint::Canvas;

    /// The letters are the letters.  Rendered as text, because a table
    /// of bits proves nothing to a reader and this proves it to anyone.
    fn art(f: &Font, ch: char) -> String {
        let g = f.glyph(ch);
        (0..f.h).map(|y| {
            (0..f.w).map(|x| if g.on(x, y) { '#' } else { '.' })
                .collect::<String>()
        }).collect::<Vec<_>>().join("\n")
    }

    #[test]
    fn the_tables_loaded() {
        assert!(SMALL.count() > 3000, "{} glyphs", SMALL.count());
        assert!(LARGE.count() > 4000, "{} glyphs", LARGE.count());
        assert_eq!(SMALL.bits.len(), SMALL.count() * SMALL.stride * 13);
        assert_eq!(LARGE.bits.len(), LARGE.count() * LARGE.stride * 20);
    }

    #[test]
    fn the_index_is_sorted_or_the_search_is_a_lie() {
        for f in [&SMALL, &LARGE] {
            for i in 1..f.count() {
                assert!(f.code_at(i - 1) < f.code_at(i),
                        "the index is out of order at {i}");
            }
        }
    }

    #[test]
    fn an_a_looks_like_an_a() {
        let a = art(&SMALL, 'A');
        assert!(a.contains("#...#"), "no stems:\n{a}");
        // The crossbar: the one row of an `A` that is nearly solid.
        assert!(a.lines().any(|r| r.matches('#').count() >= 5),
                "no crossbar:\n{a}");
        // And it is not the unknown block.
        assert!(!SMALL.glyph('A').missing());
    }

    /// A descender goes **below** the baseline, which is the whole
    /// reason the cell is taller than the letters and the reason
    /// `ascent` is carried.
    #[test]
    fn a_g_hangs_below_the_baseline() {
        let f = &LARGE;
        let g = f.glyph('g');
        let below = (f.ascent..f.h).any(|y| (0..f.w).any(|x| g.on(x, y)));
        assert!(below, "`g` sits entirely above the baseline:\n{}",
                art(f, 'g'));
        let n = f.glyph('n');
        let n_below = (f.ascent..f.h).any(|y| (0..f.w).any(|x| n.on(x, y)));
        assert!(!n_below, "`n` hangs below the baseline:\n{}", art(f, 'n'));
    }

    /// **What this project actually types.**  Measured from its own
    /// sources, so a font that lost the box-drawing character every
    /// section header is made of would fail here rather than in a
    /// screenshot.
    #[test]
    fn the_alphabet_this_project_writes_in_is_carried() {
        for ch in "abcXYZ0189 !@#$%^&*()[]{}<>|/\\-_=+.,:;'\"`~?".chars() {
            assert!(LARGE.has(ch), "ASCII {ch:?} is missing");
            assert!(SMALL.has(ch), "ASCII {ch:?} is missing from 6x13");
        }
        // Finnish, the box-drawing the section headers use, the arrows
        // and the Greek the specs are written in.
        for ch in "åäöÅÄÖ─═│┌┐└┘—–…§×→←↦⊥□∃∀∈∨∧λδϕκΓΔΦ".chars() {
            assert!(LARGE.has(ch), "U+{:04X} {ch:?} is missing", ch as u32);
        }
    }

    /// An unknown character is *visibly* unknown.
    #[test]
    fn what_the_font_lacks_is_drawn_as_a_block() {
        // Well past the ceiling the generator carried.
        let ch = '\u{1F600}';
        assert!(!LARGE.has(ch));
        let g = LARGE.glyph(ch);
        assert!(g.missing());
        assert!(g.on(1, 0) && g.on(LARGE.w - 2, LARGE.h - 1),
                "the unknown block is not filled");
        assert!(!g.on(0, 0), "it should be inset by a pixel");
    }

    /// Ink lands where the grid says, and nowhere else.
    #[test]
    fn a_drawn_line_stays_in_its_cells() {
        let f = &LARGE;
        let ink = Colour::rgb(255, 255, 255);
        let mut c = Canvas::new(200, 40, Colour::rgb(0, 0, 0));
        let end = f.draw(&mut c, 10, 5, "Hi", ink);
        assert_eq!(end, 10 + 2 * f.w, "the advance is arithmetic");
        let lit: Vec<(i32, i32)> = (0..c.h).flat_map(|y| (0..c.w).map(move |x| (x, y)))
            .filter(|(x, y)| c.get(*x, *y) == Some(ink.word()))
            .collect();
        assert!(!lit.is_empty(), "nothing was drawn");
        for (x, y) in &lit {
            assert!(*x >= 10 && *x < 10 + 2 * f.w, "ink at x={x} is outside");
            assert!(*y >= 5 && *y < 5 + f.h, "ink at y={y} is outside");
        }
    }

    /// **Clipped, not skipped.**  A glyph half off the edge draws its
    /// half; dropping it is how a viewport gets a ragged margin.
    #[test]
    fn a_glyph_crossing_the_edge_still_draws() {
        let f = &LARGE;
        let ink = Colour::rgb(255, 255, 255);
        let mut c = Canvas::new(f.w / 2, f.h, Colour::rgb(0, 0, 0));
        f.draw(&mut c, 0, 0, "M", ink);
        let any = (0..c.h).any(|y| (0..c.w).any(|x| c.get(x, y) == Some(ink.word())));
        assert!(any, "a half-visible glyph drew nothing");
    }

    /// Clicking the right half of a character puts the caret after it.
    #[test]
    fn a_click_lands_on_the_nearer_gap() {
        let f = &LARGE;
        assert_eq!(f.column_at(0, 0), 0);
        assert_eq!(f.column_at(f.w / 2 - 1, 0), 0, "left half");
        assert_eq!(f.column_at(f.w / 2 + 1, 0), 1, "right half");
        assert_eq!(f.column_at(f.w * 3 + 1, 0), 3);
        assert_eq!(f.column_at(-50, 0), 0, "before the first column");
        assert_eq!(f.column(20, 4), 20 + 4 * f.w);
    }

    /// Every cell is the same box, which is what makes the grid a grid.
    #[test]
    fn no_glyph_leaves_its_cell() {
        for f in [&SMALL, &LARGE] {
            for ch in "AWjgq_|─日".chars() {
                let g = f.glyph(ch);
                assert!(!g.on(-1, 0) && !g.on(f.w, 0),
                        "{ch:?} draws outside its cell");
            }
        }
    }
}

// ── Putting it on a screen ───────────────────────────────────────────────

use gestate_panel::list::Colour;
use gestate_panel::paint::Canvas;

impl Font {
    /// Draw one line of text with its **top-left** at `(x, y)`.
    ///
    /// Returns where the next character would go, so a caller drawing
    /// runs of different colours does not have to re-measure — and
    /// there is nothing to measure anyway: every cell is `w` wide, so
    /// the answer is arithmetic.
    ///
    /// **Clipped, not skipped.**  A line scrolled half off the top must
    /// draw its visible half; dropping any glyph whose cell crosses an
    /// edge is how a viewport comes to have a ragged margin.
    pub fn draw(&self, c: &mut Canvas, x: i32, y: i32, s: &str,
                ink: Colour) -> i32 {
        self.draw_scaled(c, x, y, s, ink, 1)
    }

    /// The same, with each pixel drawn as a `scale`×`scale` block.
    ///
    /// **Whole numbers only.**  A bitmap enlarged by a fraction has to
    /// guess which source pixel a destination one came from, and the
    /// guess shows as letters whose stems are one pixel here and two
    /// there.  Integers keep every stroke the width it was drawn, which
    /// is the whole reason a hand-drawn font is worth carrying.
    pub fn draw_scaled(&self, c: &mut Canvas, x: i32, y: i32, s: &str,
                       ink: Colour, scale: i32) -> i32 {
        let scale = scale.max(1);
        let word = ink.word() | c.alpha;
        let (cw, cell) = (c.w, self.w * scale);
        let mut at = x;
        for ch in s.chars() {
            // Whole cells outside the canvas cost nothing but the
            // advance — the common case when a long line runs past the
            // right edge.
            if at >= cw || at + cell <= 0 || y >= c.h || y + self.h * scale <= 0
            {
                at += cell;
                continue;
            }
            let g = self.glyph(ch);
            for gy in 0..self.h {
                let bits = g.row(gy);
                // **Most rows are blank** — a cell is twenty tall and a
                // letter is ten — so this branch skips about half the
                // work before touching a pixel.
                if bits == 0 {
                    continue;
                }
                for sy in 0..scale {
                    let py = y + gy * scale + sy;
                    if py < 0 || py >= c.h {
                        continue;
                    }
                    let base = py as usize * cw as usize;
                    for gx in 0..self.w {
                        if bits >> (self.w - 1 - gx) & 1 == 0 {
                            continue;
                        }
                        let px0 = at + gx * scale;
                        for sx in 0..scale {
                            let px = px0 + sx;
                            if px >= 0 && px < cw {
                                c.px[base + px as usize] = word;
                            }
                        }
                    }
                }
            }
            at += cell;
        }
        at
    }

    /// Where a column sits, and how wide it is — the whole of layout
    /// for a monospaced grid, stated once so nobody re-derives it.
    pub fn column(&self, x: i32, col: i32) -> i32 {
        x + col * self.w
    }

    /// Which column an x falls in, rounded to the nearest gap — what a
    /// click means.  **Nearest rather than containing**, because
    /// clicking the right half of a character puts the caret after it,
    /// which is what every editor does and what a hand expects.
    pub fn column_at(&self, x: i32, origin: i32) -> i32 {
        let d = x - origin;
        if d < 0 { 0 } else { (d + self.w / 2) / self.w }
    }
}
