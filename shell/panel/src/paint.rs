//! The painter — a display list to pixels, in software, with no
//! dependencies.
//!
//! `spec/panel.md` §"One painter, two sources": this is the one renderer
//! the chrome and the canvas share.  It takes `Item`s and nothing else,
//! so a `Sub` walked by the G-machine will reach it without the painter
//! learning anything new.
//!
//! **Software, and on purpose.**  A GL path would put a driver between
//! the display list and the pixels, which is the wrong property for
//! output that is supposed to be checkable against a committed image
//! (`spec/panel.md` acceptance 3).  The window is small, the vocabulary
//! is rects and dots, and a CPU rasterizer is the honest tool.

use crate::font;
use crate::list::{Colour, Display, Item};

/// A buffer of `0x00RRGGBB` words — the shape `softbuffer` presents and
/// the shape a test can hash.
pub struct Canvas {
    pub w: i32,
    pub h: i32,
    pub px: Vec<u32>,
    /// OR-ed into every pixel written.
    ///
    /// **Zero by default, and `0xFF00_0000` when a window wants it.**
    /// `Colour::word()` is `0x00RRGGBB` — three components, because
    /// that is what `gui.ges`'s `Colour` is — but an X11 window on a
    /// compositor may hold a 32-bit visual, where a zero top byte means
    /// *fully transparent*.  Both windows used to fix that with a pass
    /// over the finished buffer, which is a whole extra sweep of the
    /// screen: measured on the editor, **four milliseconds of a
    /// thirteen-millisecond frame**, spent setting one byte.  Folding
    /// it into the writes costs an `or` against a constant and lets the
    /// buffer be handed over with a `memcpy`.
    pub alpha: u32,
}

impl Canvas {
    pub fn new(w: i32, h: i32, bg: Colour) -> Self {
        let (w, h) = (w.max(0), h.max(0));
        Canvas { w, h, px: vec![bg.word(); (w * h) as usize], alpha: 0 }
    }

    /// The same, opaque — for a surface that reads the top byte.
    pub fn opaque(w: i32, h: i32, bg: Colour) -> Self {
        let mut c = Canvas::new(w, h, bg);
        c.alpha = 0xFF00_0000;
        c.px.fill(bg.word() | c.alpha);
        c
    }

    pub fn clear(&mut self, bg: Colour) {
        self.px.fill(bg.word() | self.alpha);
    }

    /// One pixel, clipped.  Every primitive below goes through here, so
    /// clipping is stated once — an item that runs off the window is a
    /// normal thing (a fader dragged to the edge, a note strip wider
    /// than the pane) and must not be able to corrupt a neighbour's row
    /// by wrapping.
    #[inline]
    pub fn put(&mut self, x: i32, y: i32, c: u32) {
        if x >= 0 && y >= 0 && x < self.w && y < self.h {
            self.px[(y * self.w + x) as usize] = c | self.alpha;
        }
    }

    pub fn get(&self, x: i32, y: i32) -> Option<u32> {
        if x >= 0 && y >= 0 && x < self.w && y < self.h {
            Some(self.px[(y * self.w + x) as usize])
        } else {
            None
        }
    }

    pub fn fill_rect(&mut self, x: i32, y: i32, w: i32, h: i32, c: Colour) {
        let word = c.word() | self.alpha;
        // Clamp the span before looping rather than testing per pixel:
        // a note strip is 128 cells and a redraw is every frame.
        let x0 = x.max(0);
        let y0 = y.max(0);
        let x1 = (x + w).min(self.w);
        let y1 = (y + h).min(self.h);
        if x1 <= x0 {
            return;
        }
        // **A memset per row, not a loop per pixel.**  The background is
        // one of these covering the whole window, and writing seven
        // hundred thousand pixels one indexed store at a time cost
        // thirty milliseconds a frame in a debug build — an editor you
        // could watch typing.  `fill` on a slice is the same code the
        // optimiser would have written and is fast unoptimised too,
        // which is what a debug build being usable depends on.
        for yy in y0..y1 {
            let row = (yy * self.w) as usize;
            self.px[row + x0 as usize..row + x1 as usize].fill(word);
        }
    }

    /// A filled circle by the squared-radius test.
    ///
    /// Aliased, matching `pygame.draw.circle`'s unantialiased form —
    /// the reference view draws the same shape, and a painter that
    /// smoothed its edges would make the two views disagree pixel for
    /// pixel for no gain the substrate asked for.
    pub fn fill_dot(&mut self, cx: i32, cy: i32, r: i32, c: Colour) {
        if r <= 0 {
            return;
        }
        let word = c.word() | self.alpha;
        let rr = r * r;
        for dy in -r..=r {
            let yy = cy + dy;
            if yy < 0 || yy >= self.h {
                continue;
            }
            for dx in -r..=r {
                if dx * dx + dy * dy <= rr {
                    let xx = cx + dx;
                    if xx >= 0 && xx < self.w {
                        self.px[(yy * self.w + xx) as usize] = word;
                    }
                }
            }
        }
    }

    /// A string at the top-left corner `(x, y)`, cells scaled by
    /// `scale`.  Chrome only — see `font`.
    pub fn text(&mut self, x: i32, y: i32, s: &str, c: Colour, scale: i32) {
        let scale = scale.max(1);
        let mut pen = x;
        for ch in s.chars() {
            let g = font::glyph(ch);
            for (row, bits) in g.iter().enumerate() {
                for col in 0..font::W {
                    // Bit 2 is the leftmost column.
                    if bits & (1 << (font::W - 1 - col)) != 0 {
                        self.fill_rect(
                            pen + col * scale,
                            y + row as i32 * scale,
                            scale,
                            scale,
                            c,
                        );
                    }
                }
            }
            pen += (font::W + font::GAP) * scale;
        }
    }
}

/// Paint a whole display list, in **painter's order** — earlier items
/// are underneath, which is `over a b` putting `b` on top and is the
/// order `gui.py` documents.
pub fn paint(canvas: &mut Canvas, d: &Display) {
    for item in &d.items {
        match item {
            Item::Rect { x, y, w, h, c } => canvas.fill_rect(*x, *y, *w, *h, *c),
            Item::Dot { cx, cy, r, c } => canvas.fill_dot(*cx, *cy, *r, *c),
            Item::Text { x, y, s, c, scale } => canvas.text(*x, *y, s, *c, *scale),
        }
    }
}
