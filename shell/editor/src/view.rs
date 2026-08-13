//! A frame — **a pure function of the document, the caret and the
//! viewport**, and nothing else.
//!
//! The same split `shell/panel` keeps and for the same reason: a layout
//! is the one thing about a window that a test can check exactly, and a
//! layout that can only be reached through a window is a layout checked
//! by looking.  `frame()` takes a `Document` and a `View` and returns a
//! list of things to draw; `paint()` puts that list on a `Canvas`.
//! Neither mentions a window and both are tested without one.
//!
//! **Only the visible rows are read**, which is the whole reason the
//! document is a tree.  A million-line file costs the rows on screen:
//! `rope.rowpos` descends by the newline counts each node carries, so
//! finding row 400,000 is the depth of the tree and not a scan.  A view
//! that read the whole document to draw fifty lines would make the rope
//! decorative.

use gestate_panel::list::Colour;
use gestate_panel::paint::Canvas;

use crate::document::{column_of, width_of, Document};
use crate::furniture::Furniture;
use crate::font::Font;

// ── The palette ──────────────────────────────────────────────────────
//
// The panel's, shifted a shade: an editor and a plugin window sitting
// in one application should not look like two applications.

pub const BG: Colour = Colour::rgb(0x14, 0x16, 0x1a);
pub const INK: Colour = Colour::rgb(0xd8, 0xdc, 0xe4);
/// The gutter's numbers — present, and not competing with the code.
pub const FAINT: Colour = Colour::rgb(0x4a, 0x52, 0x60);
/// The line the caret is on.
pub const CURRENT: Colour = Colour::rgb(0x1b, 0x1e, 0x25);
pub const CARET: Colour = Colour::rgb(0x5c, 0xa8, 0xd8);
pub const SELECT: Colour = Colour::rgb(0x24, 0x3a, 0x4c);
/// A knob's trough, in the margin beside the line that declares it.
pub const TROUGH: Colour = Colour::rgb(0x24, 0x28, 0x30);
pub const FILL: Colour = Colour::rgb(0x5c, 0xa8, 0xd8);
/// The handle, which is the part you take hold of.
///
/// **A fader is a thing with a grip, not a line with a gradient.**  A
/// four-pixel rule reads as decoration and gives a pointer nothing to
/// aim at; a bar the height of its row reads as a control and is a
/// target you can hit without looking.  It is also what the hardware
/// this borrows from looks like, which is the point of borrowing.
pub const HANDLE: Colour = Colour::rgb(0xc8, 0xdc, 0xe8);
/// The transport readout while it is running.
pub const LIVE: Colour = Colour::rgb(0x7c, 0xc8, 0x94);
/// What the compiler had to say, and where.
pub const ANGRY: Colour = Colour::rgb(0xc0, 0x4c, 0x48);
/// A thing deliberately not sounding — a bank the mix dropped
/// ("disconnected"), a scored line MIDI has displaced ("away").
/// Warm rather than red, because both are usually a choice being
/// tried, not a fault; warmer than `FAINT`, because each answers a
/// question a person is already asking (why is this silent), and an
/// answer nobody notices is not one.
pub const AWAY: Colour = Colour::rgb(0xd8, 0xa0, 0x7c);
/// The status line's ground.
/// The drawn keyboard.  **Two palettes, and the dead one is the
/// point**: a bank only takes a note if its payload has a `FromMIDI`
/// instance and its switch is on, and a piano that plays nothing must
/// not look like a piano that plays.
pub const KEY_WHITE: Colour = Colour::rgb(0xd0, 0xd4, 0xdc);
pub const KEY_BLACK: Colour = Colour::rgb(0x22, 0x26, 0x2e);
pub const KEY_DEAD_WHITE: Colour = Colour::rgb(0x4e, 0x52, 0x58);
pub const KEY_DEAD_BLACK: Colour = Colour::rgb(0x2a, 0x2c, 0x30);
pub const KEY_DOWN: Colour = Colour::rgb(0x5c, 0xa8, 0xd8);
pub const KEY_EDGE: Colour = Colour::rgb(0x14, 0x16, 0x1a);

pub const CHROME: Colour = Colour::rgb(0x1c, 0x1f, 0x25);

// ── Syntax ───────────────────────────────────────────────────────────
//
// **Six, and they answer one question**: *which sort of thing is this?*
// A shade per token kind is a palette nobody can hold in their head, and
// the eye reads punctuation as punctuation whether it is a bracket or an
// operator.  All six sit at the ink's weight against the same ground, so
// none of them reads as more important than the code.

/// A comment — present, and not competing with what it explains.
pub const S_NOTE: Colour = Colour::rgb(0x5a, 0x64, 0x72);
/// A string literal.
pub const S_TEXT: Colour = Colour::rgb(0x9c, 0xc8, 0x8c);
/// A number.
pub const S_NUM: Colour = Colour::rgb(0xd8, 0xa0, 0x7c);
/// A constructor or a type — the same warm gold the palette tints a type
/// with, because it is the same fact in a different window.
pub const S_CON: Colour = Colour::rgb(0xd8, 0xb0, 0x7c);
/// A reserved word.
pub const S_WORD: Colour = Colour::rgb(0xa8, 0x8c, 0xd8);
/// Punctuation and operators.
pub const S_OP: Colour = Colour::rgb(0x8a, 0x94, 0xa4);

/// What colour a column is, or the ordinary ink.
fn tint(runs: &[crate::furniture::Run], col: usize) -> Colour {
    for r in runs {
        if col >= r.at && col < r.at + r.len {
            return match r.paint.as_str() {
                "note" => S_NOTE,
                "text" => S_TEXT,
                "num" => S_NUM,
                "con" => S_CON,
                "word" => S_WORD,
                "op" => S_OP,
                _ => INK,
            };
        }
    }
    INK
}

/// One thing to draw.
///
/// **Two, deliberately.**  The editor's vocabulary is not the
/// substrate's: a `Run` is text on the *cell grid*, in the bitmap font,
/// which `gestate_panel::Item::Text` is not — that one carries a scale
/// for the 3×5 chrome font and means something else.  Sharing a type
/// across two meanings is how a painter ends up with a flag argument.
#[derive(Clone, PartialEq, Debug)]
pub enum Item {
    Rect { x: i32, y: i32, w: i32, h: i32, c: Colour },
    /// Text with its **top-left** at `(x, y)`, one cell per character.
    Run { x: i32, y: i32, s: String, c: Colour },
}

#[derive(Clone, PartialEq, Debug, Default)]
pub struct Frame {
    pub items: Vec<Item>,
}

/// The most rows the status bar may stand — the spec's five
/// (`spec/workbench.md` §"The status bar may grow"): a cap, not a
/// target, and anything longer belongs to a box or the transcript.
pub const BAR_MOST: u16 = 5;

/// The most rows a content box may be granted — a complaint a hundred
/// lines long gets its first eight beside the code and the whole text
/// stays one command away, which is the rule the status bar already
/// kept.
pub const BOX_MOST: u16 = 8;

/// One visible row: where its text band sits, and the box under it.
///
/// **The row table `roadmap.md` §"Content boxes" names.**  A row is a
/// text band and then, sometimes, a content box — extra height the
/// view granted under the line.  Layout, scrolling and hit-testing all
/// read the same walk (`View::slots`), which is the one invariant that
/// keeps a click, the caret and `goto` agreeing once rows stop being
/// one height.
#[derive(Clone, Copy, PartialEq, Eq, Debug)]
pub struct Slot {
    /// The document row, counting from zero.
    pub row: usize,
    /// The top of the text band, in pixels from the window's top.
    pub y: i32,
    /// The content box under the text band, in pixels — zero for most
    /// rows.  The box spans `y + ch .. y + ch + box_h`.
    pub box_h: i32,
}

/// Where the window is looking, and how big it is.
#[derive(Clone, Debug)]
pub struct View {
    /// The first visible row.
    pub top: usize,
    /// The first visible column — horizontal scrolling, because a long
    /// line must be reachable and wrapping is a decision this does not
    /// make for the author.
    pub left: usize,
    pub w: i32,
    pub h: i32,
    /// Whether to draw line numbers.
    pub gutter: bool,
    /// Whether the drawn keyboard has the keys.
    pub focused: bool,
    /// Rows reserved at the foot for the drawn keyboard, or zero.
    ///
    /// Set from the description like `aside`, so a file that is not
    /// being performed loses no height to the possibility of it.
    pub piano: i32,
    /// Columns reserved on the right for knobs.
    ///
    /// **A margin, not a panel.**  `audiospans` says which line each
    /// control source was declared on, so a parameter is drawn beside
    /// its own declaration rather than in a list you have to read
    /// against the code.  Zero when nothing declares one, so a synth
    /// with no knobs loses no width to the possibility of them.
    pub aside: usize,
    /// How many screen pixels one font pixel becomes.
    ///
    /// **Zoom lives here rather than in the font**, because a `Font` is
    /// a static table shared by every window and a zoom is one
    /// reader's choice.  The ladder pairs it with a size
    /// (`font::LADDER`): the five native sizes first, then integer
    /// scaling above them.
    pub scale: i32,
    /// How many rows the status bar stands, 1–5.  Granted by `grant`
    /// like the boxes are: one row for the status sentence, plus one
    /// per complaint about line 0 — the complaints with no line to
    /// anchor a box under, which used to exist only as a truncated
    /// first line.  `BAR_MOST` caps it; the rest is one command away.
    pub foot_rows: u16,
    /// Extra height under a line — the content boxes, as
    /// `(line, rows)` with the line counting from **one** like the
    /// furniture, and the height in rows of the current cell so a zoom
    /// scales a box with the text it annotates.
    ///
    /// **Owned by the view, set from the description** — the same rule
    /// `piano` and `aside` follow: a furniture-derived layout fact the
    /// rope, the undo and the caret never learn of, because a box is
    /// never text.  Empty until something grants a box a height;
    /// nothing does yet, so a window without boxes pays nothing.
    pub boxes: Vec<(usize, u16)>,
    /// A word said in red beside the caret, or empty.
    ///
    /// **Transient, like the piano key's number**: the window sets it
    /// when the model sends `warn` (an `open` refused over unsaved
    /// changes) and clears it a couple of seconds later.  It lives on
    /// the view because the caret's position does — the drawing and
    /// the hit-testing read one table, and this reads it too.
    pub warning: String,
    /// Whether the `[+]` in the bar is in the hidden half of its
    /// flash.  Only ever true while `warning` is up; the toggle is the
    /// window's clock, the same-width blank is `bar_rows`'s, so the
    /// bar cannot re-wrap mid-blink.
    pub plus_hidden: bool,
}

impl Default for View {
    fn default() -> Self {
        View { top: 0, left: 0, w: 800, h: 600, gutter: true, aside: 0,
               piano: 0, focused: false,
               scale: 1, boxes: Vec::new(), foot_rows: 1, warning: String::new(), plus_hidden: false }
    }
}

impl View {
    /// The cell this view draws in — the font's, scaled.
    ///
    /// Everything about layout goes through these two, so a zoom is one
    /// number and not a sweep through the file looking for `font.w`.
    pub fn cw(&self, font: &Font) -> i32 {
        font.w * self.scale.max(1)
    }

    pub fn ch(&self, font: &Font) -> i32 {
        font.h * self.scale.max(1)
    }

    /// How wide the gutter is, in columns, for a document this long.
    ///
    /// Sized to the **document**, not to the visible rows, so it does
    /// not change width as you scroll past line 999 — a gutter that
    /// resizes shifts every line sideways and reads as the text
    /// jumping.
    pub fn gutter_cols(&self, doc: &Document) -> usize {
        if !self.gutter {
            return 0;
        }
        // The widest number, plus a space either side.
        doc.rows().to_string().len() + 2
    }

    /// Columns available to the text itself.
    pub fn text_cols(&self, font: &Font, doc: &Document) -> usize {
        let used = (self.gutter_cols(doc) + self.aside) as i32 * self.cw(font);
        (((self.w - used) / self.cw(font)).max(1)) as usize
    }

    /// How tall the status bar is — its granted rows, plus air.
    ///
    /// One row almost always.  It grows (`spec/workbench.md` §"The
    /// status bar may grow") for what has no line to anchor to: a
    /// complaint about line 0 has no box to live in, and one truncated
    /// sentence was all anybody ever saw of it.  `grant` decides the
    /// count; everything that lays out against the bar reads it here.
    pub fn status_h(&self, font: &Font) -> i32 {
        self.ch(font) * i32::from(self.foot_rows.max(1)) + 4
    }

    /// Rows of *text* that would fit if none of them had a box —
    /// the view's capacity, not its layout.
    ///
    /// **Layout reads `slots`, not this.**  This stays for the places
    /// that want a size before there is a document to walk — the
    /// window's initial mirror, a test sizing a view — and it equals
    /// `slots().len()` exactly when `boxes` is empty.
    pub fn rows(&self, font: &Font) -> usize {
        ((self.text_h(font) / self.ch(font)).max(1)) as usize
    }

    /// The text area's height: what the rows and their boxes share.
    fn text_h(&self, font: &Font) -> i32 {
        self.h - self.status_h(font) - self.piano
    }

    /// **Grant the boxes their heights, from the description.**
    ///
    /// The view says how tall, deterministically — the label
    /// precedent: the box is written down and the content fits it.
    /// Today's one box kind is the complaint (B1): a line's box is one
    /// row per `trouble` row sent about it, capped at `BOX_MOST` so a
    /// hundred lines of clang cannot eat the window.  Called where
    /// `aside` and `piano` are set, because it is the same kind of
    /// fact: furniture-derived layout, owned by the view.
    pub fn grant(&mut self, chrome: &Furniture, font: &Font) {
        // A complaint's rows are its lines *wrapped to the window* —
        // Henri watched a fragment refusal run off the right edge, cut
        // mid-word, and a box that cannot say its own content whole is
        // the status bar's old defect one floor up.
        let cols = self.bar_cols(font);
        let mut boxes: Vec<(usize, u16)> = Vec::new();
        for t in &chrome.trouble {
            if t.line == 0 || t.message.is_empty() {
                continue;                    // the bar's, below
            }
            let rows = wrap(&t.message, cols).len() as u16;
            match boxes.iter_mut().find(|(l, _)| *l == t.line) {
                Some((_, had)) => *had = (*had + rows).min(BOX_MOST),
                None => boxes.push((t.line, rows.min(BOX_MOST))),
            }
        }
        self.boxes = boxes;
        // **And the bar's rows** — the status wrapped to the window,
        // then the complaints about line 0: the ones with no line to
        // anchor a box under, which used to exist as one clipped
        // sentence.  The same rule in both directions makes the split
        // complete: an anchored complaint gets a box, an unanchored
        // one gets the bar, and nothing is homeless.  Width-dependent,
        // so the window re-grants on resize and zoom, not only on a
        // description.
        self.foot_rows = (bar_rows(chrome, self.bar_cols(font), false).len() as u16)
            .clamp(1, BAR_MOST);
    }

    /// The columns the bar wraps to.
    fn bar_cols(&self, font: &Font) -> usize {
        (((self.w - 8) / self.cw(font)).max(1)) as usize
    }

    /// Extra height under a row (counting from zero), in pixels.
    pub fn extra(&self, font: &Font, row: usize) -> i32 {
        let line = row + 1;
        self.boxes.iter().find(|(l, _)| *l == line)
            .map(|(_, rows)| *rows as i32 * self.ch(font))
            .unwrap_or(0)
    }

    /// **The row table: every visible row and where it sits.**
    ///
    /// One walk from `top`, accumulating each row's band — text plus
    /// its box — until the text area is spent.  `frame_with` draws
    /// from it, `hit` reads it back, and `follow`/`clamp` agree with it
    /// through `top_showing`; that they are all this one arithmetic is
    /// the content-box invariant, and the reason a box under line 12
    /// cannot make a click on line 13 land anywhere but line 13.
    ///
    /// A window shorter than one band still shows one row, as `rows`
    /// always has.
    pub fn slots(&self, doc: &Document, font: &Font) -> Vec<Slot> {
        let ch = self.ch(font);
        let tall = self.text_h(font);
        let mut out = Vec::new();
        let (mut row, mut y) = (self.top, 0);
        while row < doc.rows() && (y + ch <= tall || out.is_empty()) {
            let box_h = self.extra(font, row);
            out.push(Slot { row, y, box_h });
            y += ch + box_h;
            row += 1;
        }
        out
    }

    /// The smallest `top` that shows `row`'s text band whole.
    ///
    /// The walk `follow` and `clamp` scroll by: from `row` upward,
    /// taking rows while their bands still fit above it.  The row's
    /// *own* box may hang below the fold — what following the caret
    /// promises is the line you are typing on, not everything anchored
    /// to it.
    pub fn top_showing(&self, font: &Font, row: usize) -> usize {
        let ch = self.ch(font);
        let tall = self.text_h(font);
        let mut used = ch;
        let mut top = row;
        while top > 0 {
            let need = ch + self.extra(font, top - 1);
            if used + need > tall {
                break;
            }
            used += need;
            top -= 1;
        }
        top
    }

    /// The row whose **text band** is at `y`, or `None` inside a box.
    ///
    /// For the margin's furniture: a knob answers in the band of the
    /// line that declares it, and a pointer inside a content box must
    /// not turn a knob it happens to sit under.  Walks the same
    /// arithmetic as `slots` without needing the document — rows past
    /// the file carry no boxes, so the two agree wherever both answer.
    fn row_at(&self, font: &Font, y: i32) -> Option<usize> {
        let ch = self.ch(font);
        let (mut row, mut band_top) = (self.top, 0);
        loop {
            let box_h = self.extra(font, row);
            if y < band_top + ch {
                return Some(row);
            }
            if y < band_top + ch + box_h {
                return None;                     // inside the box
            }
            band_top += ch + box_h;
            row += 1;
        }
    }

    /// Where the drawn keyboard's band begins — its label's row.
    pub fn piano_y(&self, font: &Font) -> i32 {
        self.h - self.status_h(font) - self.piano
    }

    /// And where the keys themselves begin, and how tall they are.
    ///
    /// **The label is inside the band, not above it.**  Drawn a row
    /// higher it lands on the last line of the document, which is a
    /// caption sitting on somebody's code — the keyboard reserves the
    /// room it needs and everything it draws stays inside it.
    pub fn keys_y(&self, font: &Font) -> (i32, i32) {
        let ch = self.ch(font);
        (self.piano_y(font) + ch, (self.piano - ch).max(1))
    }

    /// **The white keys of two octaves**, as `(midi, x, width)`.
    ///
    /// Seven to an octave, and the black ones sit between them — which
    /// is the whole of a piano's geometry and the reason this is a
    /// table rather than a formula.
    pub fn white_keys(&self) -> Vec<(i32, i32, i32)> {
        const STEPS: [i32; 7] = [0, 2, 4, 5, 7, 9, 11];
        let n = 14;
        let w = (self.w / n).max(1);
        (0..n).map(|i| {
            let midi = 12 * (i / 7) + STEPS[(i % 7) as usize];
            (midi, i * w, w)
        }).collect()
    }

    /// And the black ones, which are drawn over them.
    pub fn black_keys(&self) -> Vec<(i32, i32, i32)> {
        // Where a black key sits, as an offset from its white one: after
        // the 1st, 2nd, 4th, 5th and 6th of each octave, and nowhere
        // else — the two gaps are what make a keyboard readable.
        const AFTER: [i32; 5] = [0, 1, 3, 4, 5];
        const STEPS: [i32; 5] = [1, 3, 6, 8, 10];
        let whites = self.white_keys();
        let w = whites.first().map(|k| k.2).unwrap_or(1);
        let bw = (w * 3 / 5).max(2);
        let mut out = Vec::new();
        for octave in 0..2 {
            for (i, after) in AFTER.iter().enumerate() {
                let at = (octave * 7 + after) as usize;
                if let Some((_m, x, _w)) = whites.get(at) {
                    out.push((12 * octave + STEPS[i], x + w - bw / 2, bw));
                }
            }
        }
        out
    }

    /// The note under the pointer, if the keyboard is showing.
    ///
    /// **Black keys first**, because they are drawn on top and half of
    /// each one overlaps a white key — asking in drawing order is what
    /// makes the answer agree with what somebody sees.
    pub fn key_at(&self, font: &Font, base: i32, x: i32, y: i32)
        -> Option<i32>
    {
        if self.piano == 0 {
            return None;
        }
        let (top, tall) = self.keys_y(font);
        if y < top || y >= top + tall {
            return None;
        }
        let black_h = tall * 3 / 5;
        if y < top + black_h {
            for (midi, kx, kw) in self.black_keys() {
                if x >= kx && x < kx + kw {
                    return Some(base + midi);
                }
            }
        }
        for (midi, kx, kw) in self.white_keys() {
            if x >= kx && x < kx + kw {
                return Some(base + midi);
            }
        }
        None
    }

    /// Scroll so the caret is visible, and return whether it moved.
    ///
    /// **Only far enough.**  Centring on the caret scrolls on every
    /// keystroke, which under a held arrow reads as the page tearing
    /// past; what a reader wants is for the view to stay still until
    /// the caret reaches an edge and then to follow it by a line.
    /// `audiopygame` learned this and the comment is kept.
    pub fn follow(&mut self, doc: &Document, font: &Font) -> bool {
        self.follow_past(doc, font, 0)
    }

    /// `follow`, with the top `clear` rows treated as covered.
    ///
    /// What an ordered edit uses while the list is open: the panel
    /// owns the top of the window, so a caret scrolled to row zero is
    /// a caret *behind* it — a template inserted at a caret above the
    /// view used to "appear" exactly there, invisibly.  The caret
    /// lands at the first row the panel does not cover; at the very
    /// top of the file there is nothing to scroll past, and the panel
    /// simply covers what it covers.
    pub fn follow_past(&mut self, doc: &Document, font: &Font,
                       clear: usize) -> bool {
        let (row, col) = doc.cursor();
        let was = (self.top, self.left);
        if row < self.top + clear {
            self.top = row.saturating_sub(clear);
        } else {
            // Down: the least scroll that fits the caret's band, box
            // heights and all.  With no boxes this is the old
            // `row + 1 - rows`, and the equivalence is tested.
            let fits = self.top_showing(font, row);
            if fits > self.top {
                self.top = fits;
            }
        }
        let cols = self.text_cols(font, doc);
        if col < self.left {
            self.left = col;
        } else if col >= self.left + cols {
            self.left = col + 1 - cols;
        }
        (self.top, self.left) != was
    }

    /// Clamp to a document that may have shrunk under us.
    pub fn clamp(&mut self, doc: &Document, font: &Font) {
        let last = doc.rows().saturating_sub(1);
        self.top = self.top.min(self.top_showing(font, last));
    }

    /// What a click at `(x, y)` means, as a row and a column.
    /// Where a bank's box goes: its left edge and its side.
    ///
    /// **Named once because two places need it.**  A box drawn by one
    /// arithmetic and pressed by another drifts apart the first time
    /// either moves, and a button that answers somewhere other than
    /// where it is drawn is worse than no button — the same reason
    /// `knob_hit` sits beside the trough it inverts.
    pub fn bank_box(&self, font: &Font) -> (i32, i32) {
        let (cw, ch) = (self.cw(font), self.ch(font));
        let side = (ch - 4).max(5);
        // Hard against the right edge, with the count to its left: the
        // reading is what you scan down a file, and the control sits
        // where it does not interrupt that.
        let _ = cw;
        (self.w - side - 2, side)
    }

    /// The bank whose box is under the pointer, and whether it is
    /// listening now — so a caller knows which way a click turns it.
    ///
    /// **The box only, not the whole row.**  The count beside it is a
    /// reading, and a reading you can press by accident is a control
    /// wearing a disguise.
    pub fn bank_hit(&self, font: &Font, chrome: &Furniture, x: i32, y: i32)
        -> Option<(String, bool)>
    {
        if self.aside == 0 || y < 0 || y >= self.h - self.status_h(font) {
            return None;
        }
        let (bx, side) = self.bank_box(font);
        if x < bx || x > bx + side {
            return None;
        }
        let line = self.row_at(font, y)? + 1;
        let b = chrome.bank_at(line)?;
        Some((b.name.clone(), b.listening))
    }

    /// The knob under the pointer, and the value that point means.
    ///
    /// **The inverse of what `frame_with` drew**, and deliberately in
    /// the same file: a trough drawn by one arithmetic and read by
    /// another drifts apart the first time either changes, and a fader
    /// that answers to a place it is not drawn is worse than no fader.
    ///
    /// `spec/workbench.md` acceptance 4 asks that turning a knob and
    /// typing the number be the same act. That is why this returns a
    /// *value in the knob's own range* rather than a fraction: what
    /// travels back is what would have been typed.
    pub fn knob_hit(&self, font: &Font, chrome: &Furniture, x: i32, y: i32)
        -> Option<(String, f64)>
    {
        if self.aside == 0 || y < 0 || y >= self.h - self.status_h(font) {
            return None;
        }
        let cw = self.cw(font);
        let left = self.w - self.aside as i32 * cw;
        if x < left {
            return None;
        }
        let line = self.row_at(font, y)? + 1;
        let k = chrome.knob_at(line)?;
        // The trough is one cell narrower than the margin — see the
        // `wide` that draws it.
        let wide = (self.aside as i32 * cw - cw).max(1);
        let along = ((x - left) as f64 / wide as f64).clamp(0.0, 1.0);
        Some((k.name.clone(), k.lo + along * (k.hi - k.lo)))
    }

    pub fn hit(&self, doc: &Document, font: &Font, x: i32, y: i32)
        -> (usize, usize)
    {
        // Through the same walk the frame drew from.  A click inside a
        // content box answers the box's own line — the box is anchored
        // there, and a caret has to land *somewhere* a person can see
        // the sense of.  Below everything visible, the old behaviour
        // is kept: rows keep counting past the fold, clamped to the
        // document's end.
        let ch = self.ch(font);
        let (mut row, mut band_top) = (self.top, 0);
        let y = y.max(0);
        loop {
            let band = ch + self.extra(font, row);
            if y < band_top + band {
                break;
            }
            band_top += band;
            row += 1;
        }
        let gx = self.gutter_cols(doc) as i32 * self.cw(font);
        let cw = self.cw(font);
        let col = self.left
            + (if x <= gx { 0 } else { (x - gx + cw / 2) / cw }) as usize;
        (row.min(doc.rows() - 1), col)
    }
}

/// Draw the document.  **Pure**: same document, same view, same list.
pub fn frame(doc: &Document, view: &View, font: &Font) -> Frame {
    frame_with(doc, view, font, &Furniture::default())
}

/// The chrome alone, for a window showing the canvas.
///
/// **Looking at a picture does not stop a command from answering**, and
/// an answer with nowhere to appear is an answer nobody reads — so the
/// status line and the transport survive the switch, and nothing else
/// does. The canvas is the program's own drawing and the window has no
/// business writing over it.
pub fn chrome_only(view: &View, font: &Font, chrome: &Furniture) -> Frame {
    let mut f = Frame::default();
    foot(&mut f, view, font, chrome);
    f
}

/// Greedy word wrap to a column count, chars being columns — which in
/// a bitmap font they are.
fn wrap(text: &str, cols: usize) -> Vec<String> {
    let cols = cols.max(1);
    let mut out = Vec::new();
    let mut line = String::new();
    for word in text.split(' ') {
        let need = word.chars().count();
        let have = line.chars().count();
        if have > 0 && have + 1 + need > cols {
            out.push(std::mem::take(&mut line));
        }
        if !line.is_empty() {
            line.push(' ');
        }
        // A single word wider than the window is cut, not looped over.
        if need > cols {
            line.extend(word.chars().take(cols));
        } else {
            line.push_str(word);
        }
    }
    if !line.is_empty() {
        out.push(line);
    }
    if out.is_empty() {
        out.push(String::new());
    }
    out
}

/// Everything the bar says, wrapped to the window, capped at
/// `BAR_MOST` rows: the file-and-status line first, then the
/// complaints about line 0 — the unanchorable ones, minus any row the
/// status already quotes.  The `bool` is whether a row is a complaint
/// (drawn in the warning colour).
///
/// **One function, two readers** — `grant` counts these rows and
/// `foot` draws them, and being the same list is what keeps the bar's
/// height and its content from disagreeing, which is the rule the
/// slots table already keeps for the boxes.
pub fn bar_rows(chrome: &Furniture, cols: usize,
                plus_hidden: bool) -> Vec<(String, bool)> {
    let mut head = String::new();
    if !chrome.file.is_empty() {
        head.push_str(&chrome.file);
        if chrome.unsaved {
            // The hidden half of the `[+]`'s flash is the same width,
            // so the bar cannot re-wrap mid-blink — a warning must
            // catch the eye, not shake the furniture.
            head.push_str(if plus_hidden { "    " } else { " [+]" });
        }
        head.push_str("  ");
    }
    head.push_str(&chrome.status);
    let mut out: Vec<(String, bool)> = wrap(&head, cols).into_iter()
        .map(|l| (l, false))
        .collect();
    for t in &chrome.trouble {
        if t.line != 0 || t.message.is_empty()
            || chrome.status.contains(&t.message) {
            continue;
        }
        out.extend(wrap(&t.message, cols).into_iter().map(|l| (l, true)));
    }
    out.truncate(usize::from(BAR_MOST));
    out
}

/// The status bar and the transport readout.
///
/// **Its own function because both frames want it.**  Looking at the
/// canvas does not stop a command from answering, and an answer with
/// nowhere to appear is an answer nobody reads.
fn foot(f: &mut Frame, view: &View, font: &Font, chrome: &Furniture) {
    let (cw, ch) = (view.cw(font), view.ch(font));
    let _ = ch;
    // The status line, at the foot — one sentence, which is what the
    // model says every command answers with.
    let sy = view.h - view.status_h(font);
    f.items.push(Item::Rect { x: 0, y: sy, w: view.w,
                              h: view.status_h(font), c: CHROME });
    // **The name, and whether it is written down.**  `[+]` is what every
    // editor with a modified flag uses, so it needs no explaining — and
    // without it an edit you have not saved looked exactly like one you
    // had, in a window whose whole premise is that saving is what you
    // press to hear the change.

    // **The bar's rows, wrapped to the window** — the same list
    // `grant` counted, so height and content cannot disagree.  The
    // status wraps rather than running off the right edge; under it,
    // the complaints about nowhere — a complaint that names a line has
    // a content box, one about line 0 has only this bar, and it used
    // to get one clipped sentence.  Drawn to the granted rows; the
    // whole text stays one command away, exactly as the boxes rule.
    let ch = view.ch(font);
    let granted = usize::from(view.foot_rows.max(1));
    for (i, (line, angry)) in bar_rows(chrome, view.bar_cols(font), view.plus_hidden)
        .into_iter().take(granted).enumerate()
    {
        if !line.is_empty() {
            f.items.push(Item::Run { x: 4, y: sy + 2 + ch * i as i32,
                                     s: line,
                                     c: if angry { ANGRY } else { FAINT } });
        }
    }

    // **Where the music is, at the right of the same line.**  The
    // description has carried the transport since the wire was built and
    // nothing drew it, which made `seek` and `play` look like commands
    // that did nothing: they answered *"at bar 8"* and the window showed
    // exactly what it had before.  A command whose only evidence is its
    // own sentence is indistinguishable from one that failed.
    if chrome.has_transport {
    // **Bars and beats count from zero**, like the ticks, the samples
    // and the voices — the readout used to add one to each, which is
    // what a score on paper does and is wrong in a programmatic editor:
    // an interface that alone said *bar 1* for the first bar made the
    // reader do arithmetic to cross between the program and the window.
    let beat = chrome.beat.max(0.0);
    let bar = (beat / 4.0).floor() as i64;
    let mut when = format!("{} {}.{}",
                           if chrome.playing { "\u{25b6}" } else { "\u{25a0}" },
                           bar, (beat as i64).rem_euclid(4));
    if let Some((from, to)) = chrome.looping {
        // Bars, because that is what `loop` is given and a readout in
        // other units than the command is a second thing to learn.
        // **The bars the command was given**, both ends the same way.
        // The end is exclusive — `loop 2 6` plays bars two to five —
        // and showing the bars *played* would mean the readout and the
        // command that made it disagree by one, which is a puzzle to
        // solve every time rather than a thing to read.
        when.push_str(&format!("  \u{21ba}{}-{}",
                               (from / 4.0).floor() as i64,
                               (to / 4.0).floor() as i64));
    }
    let at = view.w - 4 - width_of(&when) as i32 * cw;
    f.items.push(Item::Run { x: at, y: sy + 2, s: when,
                             c: if chrome.playing { LIVE } else { FAINT } });
    }

}


/// The same, with what the model had to say about the chrome.
pub fn frame_with(doc: &Document, view: &View, font: &Font,
                  chrome: &Furniture) -> Frame {
    let mut f = Frame::default();
    // **The one row table** — drawing reads the same walk `hit` and
    // `follow` answer from, which is the content-box invariant.
    let slots = view.slots(doc, font);
    let gutter = view.gutter_cols(doc);
    let (cw, ch) = (view.cw(font), view.ch(font));
    let text_x = gutter as i32 * cw;
    let cols = view.text_cols(font, doc);
    let (crow, ccol) = doc.cursor();

    f.items.push(Item::Rect { x: 0, y: 0, w: view.w, h: view.h, c: BG });

    for slot in &slots {
        let (row, y) = (slot.row, slot.y);

        // The caret's line, lit the whole width — a band rather than a
        // box, so it says *where you are* without competing with the
        // caret itself for saying *exactly* where.
        if row == crow {
            f.items.push(Item::Rect { x: 0, y, w: view.w, h: ch,
                                      c: CURRENT });
        }

        if gutter > 0 {
            let n = (row + 1).to_string();
            // Right-aligned against the gutter's inner edge.
            let x = (gutter - 1 - n.chars().count()) as i32 * cw;
            f.items.push(Item::Run { x, y, s: n, c: FAINT });
        }

        // **The selection, under the text and over the current-line
        // band.**  Drawn per row as one span, because a selection is a
        // *range of the document* and the rows it crosses are whatever
        // the line breaks made them — computing it per row is what
        // makes a three-line selection three rectangles instead of one
        // that has to be clipped.
        if let Some((a, b)) = doc.selection() {
            if let Ok((rs, re)) = doc.rope().row_range(row) {
                // The newline at a row's end is *in* the selection when
                // the range runs past it, and that is what makes a
                // whole-line selection look whole rather than stopping
                // at the last character.
                let over = b > re && b > rs;
                let (lo, hi) = (a.max(rs), b.min(re));
                if lo < hi || (over && a <= re) {
                    let line = doc.line(row);
                    let c0 = column_of(&line, lo.saturating_sub(rs));
                    let c1 = column_of(&line, hi.saturating_sub(rs));
                    let x0 = text_x + (c0.saturating_sub(view.left)) as i32 * cw;
                    // A selection running past the line's end is drawn a
                    // cell wider, standing for the newline it swallowed.
                    let extra = if over { 1 } else { 0 };
                    let x1 = text_x
                        + (c1.saturating_sub(view.left) as i32 + extra) * cw;
                    if x1 > x0 && c1 >= view.left {
                        f.items.push(Item::Rect { x: x0, y,
                                                  w: (x1 - x0).min(view.w - x0),
                                                  h: ch, c: SELECT });
                    }
                }
            }
        }

        // **The line, scrolled horizontally by columns and not by
        // characters.**  A tab is four columns and one character, so
        // cutting by characters would slide a line sideways depending
        // on how it was indented.
        let line = doc.line(row);
        let shown: String = visible(&line, view.left, cols);
        if !shown.is_empty() {
            // **One run per colour, and one run when there is no
            // colour.**  A line the model has not painted — off screen a
            // moment ago, or a file that is not gestate — draws exactly
            // as it did before any of this, which is what keeps
            // colouring an addition rather than a rewrite.
            match chrome.paint.get(&(row + 1)) {
                None => f.items.push(Item::Run { x: text_x, y,
                                                 s: shown, c: INK }),
                Some(runs) => {
                    let mut at = 0usize;              // column in `shown`
                    let mut piece = String::new();
                    let mut ink = INK;
                    for ch in shown.chars() {
                        let want = tint(runs, view.left + at);
                        if want != ink && !piece.is_empty() {
                            f.items.push(Item::Run {
                                x: text_x + (at - piece.chars().count())
                                    as i32 * cw,
                                y, s: std::mem::take(&mut piece), c: ink });
                        }
                        ink = want;
                        piece.push(ch);
                        at += 1;
                    }
                    if !piece.is_empty() {
                        f.items.push(Item::Run {
                            x: text_x + (at - piece.chars().count()) as i32 * cw,
                            y, s: piece, c: ink });
                    }
                }
            }
        }
    }

    // **A knob in the margin at the line that declares it**, and the
    // trouble at the line that caused it.  Both are drawn from the
    // description rather than from anything this side knows, which is
    // what keeps the model the only place a fact lives.
    for slot in &slots {
        let (row, y) = (slot.row, slot.y);
        let line_no = row + 1;

        if chrome.trouble_at(line_no).is_some() {
            // A mark in the gutter — still there when the box below is
            // scrolled half away, and the cheapest thing to scan for.
            f.items.push(Item::Rect { x: 0, y, w: cw / 2, h: ch, c: ANGRY });
        }

        // **The complaint, in the box under its line** (B1).  The rows
        // were granted by `grant` from the same description, so the
        // band and its content cannot disagree about the height; a
        // message longer than the window is cut at the edge, whole
        // text one command away, exactly as the status bar ruled.
        if slot.box_h > 0 {
            f.items.push(Item::Rect { x: 0, y: y + ch, w: view.w,
                                      h: slot.box_h, c: CHROME });
            // Wrapped to the same columns `grant` counted with, and
            // drawn from the window's own left edge rather than the
            // text's — a complaint is not code, and the full width is
            // what lets its rows and its granted height be one list.
            let cols = view.bar_cols(font);
            let granted = (slot.box_h / ch) as usize;
            let found = chrome.troubles_at(line_no);
            let rows = found.iter()
                .flat_map(|t| wrap(&t.message, cols))
                .take(granted);
            for (i, said) in rows.enumerate() {
                if !said.is_empty() {
                    f.items.push(Item::Run { x: 4,
                                             y: y + ch * (1 + i as i32),
                                             s: said, c: ANGRY });
                }
            }
        }

        // **And what every `_` on this line wants**, after the text, the
        // way the complaint is — a hole is a question about the line it
        // is on, and the answer belongs beside it rather than in a panel
        // you read against the code.
        //
        // Not where trouble is: a line that does not compile has no
        // inferred holes to show, so the two do not compete for the
        // room, and preferring the complaint when they somehow do is the
        // right way round — one is about the program being wrong, the
        // other about it being unfinished.
        if chrome.trouble_at(line_no).is_none() {
            if let Some(h) = chrome.hole_at(line_no) {
                let after = text_x
                    + (width_of(&doc.line(row)).saturating_sub(view.left)
                       as i32 + 2) * cw;
                if after < view.w {
                    f.items.push(Item::Run { x: after, y,
                                             s: h.says.clone(), c: FAINT });
                }
            }
        }

        // **A bank in the margin at the line that declares it**, the
        // same rule the knobs follow — a box saying whether it is
        // listening to the keyboard, and how many of its voices are
        // sounding out of how many it has.
        //
        // `held` is what makes it worth drawing: `voices 4` is in the
        // text already and a window that only repeated it would be
        // decoration.  What the text cannot say is that three of them
        // are down *now*.
        if view.aside > 0 {
            if let Some(b) = chrome.bank_at(line_no) {
                // **A bank the sound does not reach says so**, where
                // the count would be: "disconnected" is the fact that
                // explains keys played into silence, and the count of
                // a bank nobody can hear would be the margin telling
                // a smaller truth than it knows.  Same split as the
                // knob's cross: the text declares, the graph answers.
                let count = if b.wired {
                    format!("{}/{}", b.held, b.voices)
                } else {
                    "disconnected".to_string()
                };
                let (bx, side) = view.bank_box(font);
                let top = y + 2;
                // The reading first, then the button on its right —
                // what you scan down a file is the count, and the
                // control sits where it does not interrupt that.
                f.items.push(Item::Run {
                    x: bx - 4 - width_of(&count) as i32 * cw, y,
                    s: count,
                    c: if !b.wired { AWAY }
                       else if b.held > 0 { LIVE }
                       else { FAINT } });
                f.items.push(Item::Rect { x: bx, y: top, w: side, h: side,
                                          c: TROUGH });
                if b.listening {
                    // Filled, not ticked: a tick is glyph-shaped and
                    // this font is drawn at five pixels wide.
                    let inset = (side / 4).max(1);
                    f.items.push(Item::Rect { x: bx + inset, y: top + inset,
                                              w: side - 2 * inset,
                                              h: side - 2 * inset, c: FILL });
                }
            }
            // **The score's word, at the line itself.**  A bank whose
            // switch is on is MIDI's, so a score line writing
            // `voices.<bank>` is silently displaced — the person can
            // *see* the note that is not sounding, and "layered away"
            // beside it is the difference between a choice being tried
            // and an evening deciding the synth is broken.
            if let Some(words) = chrome.away_at(line_no) {
                let (bx, _side) = view.bank_box(font);
                f.items.push(Item::Run {
                    x: bx - 4 - width_of(words) as i32 * cw, y,
                    s: words.to_string(), c: AWAY });
            }
            if let Some(k) = chrome.knob_at(line_no) {
                let wide = view.aside as i32 * cw - cw;
                let x = view.w - view.aside as i32 * cw;
                // **As tall as its line**, with a pixel of air above and
                // below so two knobs on adjacent lines stay two knobs.
                let top = y + 1;
                let tall = (ch - 2).max(3);
                f.items.push(Item::Rect { x, y: top, w: wide, h: tall,
                                          c: TROUGH });
                let full = (wide as f64 * k.fraction()).round() as i32;
                if full > 0 {
                    f.items.push(Item::Rect { x, y: top, w: full, h: tall,
                                              c: FILL });
                }
                // The grip, kept inside the trough at both ends so it
                // never hangs off the edge it is reporting.
                let grip = (cw / 2).max(3);
                let at = (x + full - grip / 2)
                    .clamp(x, x + wide - grip);
                f.items.push(Item::Rect { x: at, y: top, w: grip, h: tall,
                                          c: HANDLE });
                // **A cross to its left when the sound never reads it.**
                // The knob is drawn either way — one that vanished would
                // read as the editor having lost the line — and the mark
                // is what stops a control that does nothing looking
                // exactly like one that works, which is the same rule
                // that greys a piano nobody is listening to.
                if !k.wired {
                    f.items.push(Item::Run { x: x - cw - 2, y,
                                             s: "\u{2717}".into(),
                                             c: ANGRY });
                }
            }
        }
    }

    // **The keyboard, when a note would do something.**  Above the
    // status line and below the text, so it takes the room it needs
    // from the document rather than covering it.
    //
    // Drawn dead — every key grey — when no bank is listening.  A bank
    // only takes a note if its payload has a `FromMIDI` instance *and*
    // its switch is on, and neither is visible in the text; a piano
    // that plays nothing and looks exactly like one that plays is how
    // an evening goes into deciding whether the synth is broken.
    if view.piano > 0 {
        let band = view.piano_y(font);
        let (py, tall) = view.keys_y(font);
        let live = !chrome.heard.is_empty();
        let base = (chrome.octave + 1) * 12;
        let (white, black) = if live {
            (KEY_WHITE, KEY_BLACK)
        } else {
            (KEY_DEAD_WHITE, KEY_DEAD_BLACK)
        };
        f.items.push(Item::Rect { x: 0, y: band, w: view.w, h: view.piano,
                                  c: KEY_EDGE });
        for (midi, x, kw) in view.white_keys() {
            let down = chrome.held.contains(&(base + midi));
            f.items.push(Item::Rect { x: x + 1, y: py + 1, w: kw - 2,
                                      h: tall - 2,
                                      c: if down { KEY_DOWN } else { white } });
        }
        let black_h = tall * 3 / 5;
        for (midi, x, kw) in view.black_keys() {
            let down = chrome.held.contains(&(base + midi));
            f.items.push(Item::Rect { x, y: py, w: kw, h: black_h,
                                      c: if down { KEY_DOWN } else { black } });
        }
        // **A held key says its number, on the key.**  The note that is
        // sounding is a fact you otherwise reconstruct by counting
        // octaves; grey on the pressed colour, and only while down, so
        // an idle keyboard stays a picture.  After both loops, because
        // black keys are drawn over white ones and a white key's number
        // must not go under its neighbour.
        for (keys, low) in [(view.white_keys(), py + tall - 1),
                            (view.black_keys(), py + black_h)] {
            for (midi, x, kw) in keys {
                let note = base + midi;
                if !chrome.held.contains(&note) {
                    continue;
                }
                let s = note.to_string();
                let nx = x + (kw - s.chars().count() as i32 * cw) / 2;
                f.items.push(Item::Run { x: nx.max(x),
                                         y: (low - ch - 1).max(py),
                                         s, c: FAINT });
            }
        }
        // What it would do, said in the corner: `on` plays, `step`
        // plays and writes the note into the text, and neither is
        // guessable from a picture of a piano.
        let mut said = chrome.performing.clone();
        if !live {
            said.push_str(" — nothing is listening");
        }
        if view.focused {
            // **Said, and shown.**  A focus is only not a mode because
            // you can see where it is.
            said.push_str("   [the keys play]");
            f.items.push(Item::Rect { x: 0, y: band, w: view.w, h: 2,
                                      c: KEY_DOWN });
        }
        f.items.push(Item::Run { x: 4, y: band, s: said, c: FAINT });
    }

    foot(&mut f, view, font, chrome);

    // The caret last, so nothing is drawn over it.
    if ccol >= view.left {
        if let Some(slot) = slots.iter().find(|s| s.row == crow) {
            let x = text_x + (ccol - view.left) as i32 * cw;
            if x < view.w {
                f.items.push(Item::Rect { x, y: slot.y, w: 2.max(cw / 5),
                                          h: ch, c: CARET });
            }
            // **The warning, beside the caret** — where the eye already
            // is, like the piano key's number: only while it happens,
            // gone when it is over.  Shifted left rather than clipped
            // when the caret sits near the right edge, because a
            // warning that reads "warni" warns about nothing.
            if !view.warning.is_empty() {
                let wide = view.warning.chars().count() as i32 * cw;
                let wx = (x + 2 * cw).min(view.w - wide - 2).max(0);
                f.items.push(Item::Run { x: wx, y: slot.y,
                                         s: view.warning.clone(),
                                         c: ANGRY });
            }
        }
    }
    f
}

/// The part of a line between two columns, tabs expanded to spaces.
///
/// **Expanded here and nowhere else.**  A tab is a character in the
/// document and a run of columns on the screen; turning it into spaces
/// at the last moment means the rope never sees them and an edit never
/// has to undo them.
fn visible(line: &str, from: usize, cols: usize) -> String {
    let mut out = String::new();
    let mut col = 0usize;
    for ch in line.chars() {
        let next = if ch == '\t' { col / crate::document::TAB
                                     * crate::document::TAB
                                     + crate::document::TAB } else { col + 1 };
        for c in col..next {
            if c >= from && c < from + cols {
                out.push(if ch == '\t' { ' ' } else { ch });
            }
        }
        col = next;
        if col >= from + cols {
            break;
        }
    }
    out
}

/// Put a frame on a canvas.
pub fn paint(c: &mut Canvas, f: &Frame, font: &Font, scale: i32) {
    for item in &f.items {
        match item {
            Item::Rect { x, y, w, h, c: col } => c.fill_rect(*x, *y, *w, *h, *col),
            Item::Run { x, y, s, c: col } => {
                font.draw_scaled(c, *x, *y, s, *col, scale);
            }
        }
    }
}

/// How wide the widest visible line is, in columns — what a horizontal
/// scrollbar would need.
pub fn widest(doc: &Document, view: &View, font: &Font) -> usize {
    view.slots(doc, font).iter()
        .map(|s| width_of(&doc.line(s.row)))
        .max()
        .unwrap_or(0)
}

/// Where the caret sits in pixels, for a host that wants to place an
/// input method or a tooltip.
pub fn caret_at(doc: &Document, view: &View, font: &Font) -> (i32, i32) {
    let (row, col) = doc.cursor();
    let gx = view.gutter_cols(doc) as i32 * view.cw(font);
    // From the row table when the caret is on screen; the old uniform
    // arithmetic when it is not, so an off-screen answer stays an
    // extrapolation rather than a panic.
    let y = view.slots(doc, font).iter()
        .find(|s| s.row == row)
        .map(|s| s.y)
        .unwrap_or((row.saturating_sub(view.top)) as i32 * view.ch(font));
    (gx + (col.saturating_sub(view.left)) as i32 * view.cw(font), y)
}
