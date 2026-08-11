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
/// The status line's ground.
pub const CHROME: Colour = Colour::rgb(0x1c, 0x1f, 0x25);

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

/// Where the window is looking, and how big it is.
#[derive(Clone, Copy, Debug)]
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
}

impl Default for View {
    fn default() -> Self {
        View { top: 0, left: 0, w: 800, h: 600, gutter: true, aside: 0,
               scale: 1 }
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

    /// How tall the status line is — one row, plus air.
    pub fn status_h(&self, font: &Font) -> i32 {
        self.ch(font) + 4
    }

    /// Rows of *text*, which is the window minus the status line.
    pub fn rows(&self, font: &Font) -> usize {
        (((self.h - self.status_h(font)) / self.ch(font)).max(1)) as usize
    }

    /// Scroll so the caret is visible, and return whether it moved.
    ///
    /// **Only far enough.**  Centring on the caret scrolls on every
    /// keystroke, which under a held arrow reads as the page tearing
    /// past; what a reader wants is for the view to stay still until
    /// the caret reaches an edge and then to follow it by a line.
    /// `audiopygame` learned this and the comment is kept.
    pub fn follow(&mut self, doc: &Document, font: &Font) -> bool {
        let (row, col) = doc.cursor();
        let was = (self.top, self.left);
        let rows = self.rows(font);
        if row < self.top {
            self.top = row;
        } else if row >= self.top + rows {
            self.top = row + 1 - rows;
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
        let rows = self.rows(font);
        let last = doc.rows().saturating_sub(rows.min(doc.rows()));
        self.top = self.top.min(last);
    }

    /// What a click at `(x, y)` means, as a row and a column.
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
        let (cw, ch) = (self.cw(font), self.ch(font));
        let left = self.w - self.aside as i32 * cw;
        if x < left {
            return None;
        }
        let line = self.top + (y / ch) as usize + 1;
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
        let row = self.top + (y.max(0) / self.ch(font)) as usize;
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

/// The same, with what the model had to say about the chrome.
pub fn frame_with(doc: &Document, view: &View, font: &Font,
                  chrome: &Furniture) -> Frame {
    let mut f = Frame::default();
    let rows = view.rows(font);
    let gutter = view.gutter_cols(doc);
    let (cw, ch) = (view.cw(font), view.ch(font));
    let text_x = gutter as i32 * cw;
    let cols = view.text_cols(font, doc);
    let (crow, ccol) = doc.cursor();

    f.items.push(Item::Rect { x: 0, y: 0, w: view.w, h: view.h, c: BG });

    for i in 0..rows {
        let row = view.top + i;
        if row >= doc.rows() {
            break;
        }
        let y = i as i32 * ch;

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
            f.items.push(Item::Run { x: text_x, y, s: shown, c: INK });
        }
    }

    // **A knob in the margin at the line that declares it**, and the
    // trouble at the line that caused it.  Both are drawn from the
    // description rather than from anything this side knows, which is
    // what keeps the model the only place a fact lives.
    for i in 0..rows {
        let row = view.top + i;
        if row >= doc.rows() {
            break;
        }
        let y = i as i32 * ch;
        let line_no = row + 1;

        if let Some(t) = chrome.trouble_at(line_no) {
            // A mark in the gutter, and the message after the text — a
            // status bar is one line and this is where the complaint
            // belongs, beside what caused it.
            f.items.push(Item::Rect { x: 0, y, w: cw / 2, h: ch, c: ANGRY });
            let after = text_x
                + (width_of(&doc.line(row)).saturating_sub(view.left) as i32
                   + 2) * cw;
            if after < view.w {
                f.items.push(Item::Run { x: after, y, s: t.message.clone(),
                                         c: ANGRY });
            }
        }

        if view.aside > 0 {
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
            }
        }
    }

    // The status line, at the foot — one sentence, which is what the
    // model says every command answers with.
    let sy = view.h - view.status_h(font);
    f.items.push(Item::Rect { x: 0, y: sy, w: view.w,
                              h: view.status_h(font), c: CHROME });
    if !chrome.status.is_empty() {
        f.items.push(Item::Run { x: 4, y: sy + 2, s: chrome.status.clone(),
                                 c: FAINT });
    }

    // **Where the music is, at the right of the same line.**  The
    // description has carried the transport since the wire was built and
    // nothing drew it, which made `seek` and `play` look like commands
    // that did nothing: they answered *"at bar 8"* and the window showed
    // exactly what it had before.  A command whose only evidence is its
    // own sentence is indistinguishable from one that failed.
    if chrome.has_transport {
    let beat = chrome.beat.max(0.0);
    let bar = (beat / 4.0).floor() as i64 + 1;
    let mut when = format!("{} {}.{}",
                           if chrome.playing { "\u{25b6}" } else { "\u{25a0}" },
                           bar, (beat as i64).rem_euclid(4) + 1);
    if let Some((from, to)) = chrome.looping {
        // Bars, because that is what `loop` is given and a readout in
        // other units than the command is a second thing to learn.
        // **The bars the command was given**, both ends the same way.
        // The end is exclusive — `loop 2 6` plays bars two to five —
        // and showing the bars *played* would mean the readout and the
        // command that made it disagree by one, which is a puzzle to
        // solve every time rather than a thing to read.
        when.push_str(&format!("  \u{21ba}{}-{}",
                               (from / 4.0).floor() as i64 + 1,
                               (to / 4.0).floor() as i64 + 1));
    }
    let at = view.w - 4 - width_of(&when) as i32 * cw;
    f.items.push(Item::Run { x: at, y: sy + 2, s: when,
                             c: if chrome.playing { LIVE } else { FAINT } });
    }

    // The caret last, so nothing is drawn over it.
    if crow >= view.top && crow < view.top + rows && ccol >= view.left {
        let x = text_x + (ccol - view.left) as i32 * cw;
        let y = (crow - view.top) as i32 * ch;
        if x < view.w {
            f.items.push(Item::Rect { x, y, w: 2.max(cw / 5), h: ch,
                                      c: CARET });
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
    (0..view.rows(font))
        .map(|i| view.top + i)
        .take_while(|r| *r < doc.rows())
        .map(|r| width_of(&doc.line(r)))
        .max()
        .unwrap_or(0)
}

/// Where the caret sits in pixels, for a host that wants to place an
/// input method or a tooltip.
pub fn caret_at(doc: &Document, view: &View, font: &Font) -> (i32, i32) {
    let (row, col) = doc.cursor();
    let gx = view.gutter_cols(doc) as i32 * view.cw(font);
    (gx + (col.saturating_sub(view.left)) as i32 * view.cw(font),
     (row.saturating_sub(view.top)) as i32 * view.ch(font))
}
