//! The two panels: a `Model` to a `Display`, and nothing else.
//!
//! **A pure function, which is acceptance test 2.**  No window, no
//! clock, no host — the same model, at the same size, scale and scroll,
//! draws the same list every time, so the layout is checkable the way a
//! render is.

use crate::font;
use crate::list::{Axis, Colour, Display, Kind};
use crate::model::{Accepts, Model};

// ── The palette ──────────────────────────────────────────────────────
//
// Dark, because a plugin window sits inside a host that is usually
// dark, and a bright panel in a dark DAW is the thing that makes people
// close it.

pub const BG: Colour = Colour::rgb(0x14, 0x16, 0x1a);
pub const INK: Colour = Colour::rgb(0xd8, 0xdc, 0xe4);
pub const DIM: Colour = Colour::rgb(0x6a, 0x72, 0x80);
pub const TRACK: Colour = Colour::rgb(0x24, 0x28, 0x30);
pub const FILL: Colour = Colour::rgb(0x5c, 0xa8, 0xd8);
pub const HOT: Colour = Colour::rgb(0x8f, 0xd0, 0xf0);
/// A key the bank answers at every velocity.
pub const NOTE_ALL: Colour = Colour::rgb(0x5c, 0xd8, 0x9a);
/// A key it answers at some velocities and not others.
pub const NOTE_SOME: Colour = Colour::rgb(0xd8, 0xb4, 0x5c);
/// A key it declines outright — the silence this panel exists to show.
pub const NOTE_NONE: Colour = Colour::rgb(0x2c, 0x30, 0x38);
/// A routing cell that is on — this bank hears this MIDI channel.
pub const CELL_ON: Colour = Colour::rgb(0x5c, 0xa8, 0xd8);
/// A routing cell that is off.
pub const CELL_OFF: Colour = Colour::rgb(0x24, 0x28, 0x30);
/// The scrollbar's thumb, when there is more than fits.
pub const BAR: Colour = Colour::rgb(0x6a, 0x74, 0x84);

// ── Button actions ───────────────────────────────────────────────────

/// Make the text one step smaller.
pub const ACT_SMALLER: u32 = 0;
/// Make the text one step larger.
pub const ACT_LARGER: u32 = 1;

/// Zoom, as a **percentage**, in steps of `SCALE_STEP`.
///
/// **Percent rather than a whole multiplier**, because doubling is too
/// coarse a thing to offer as the only step: going from readable to
/// twice-readable skips every size a person actually wants.  The layout
/// scales smoothly with the percentage; the *font* still lands on whole
/// cells, because it is a bitmap and a fractional glyph would blur the
/// one thing this painter does exactly — so text climbs in its own
/// steps inside a continuously growing frame.
pub const SCALE_MIN: i32 = 75;
pub const SCALE_MAX: i32 = 300;
pub const SCALE_STEP: i32 = 25;
/// **150, not 100.**  At 100 the small captions are three pixels tall,
/// which is a diagram of text rather than text; the panel opens where
/// it can be read and lets a person go down if they want density.
pub const SCALE_DEFAULT: i32 = 150;

const KEYS: i32 = 128;
/// The routing matrix: sixteen cells, one per MIDI channel.
const CELLS: i32 = 16;

// ── Layout, as a function of the scale ───────────────────────────────

/// Every dimension the layout uses, derived from one number.
///
/// **The point of gathering them is that they must move together.**
/// Making the text bigger without making the boxes bigger is how a
/// label ends up on top of a number; deriving both from `s` means the
/// only way to get that wrong is to write a constant that ignores it.
#[derive(Clone, Copy)]
pub struct Metrics {
    /// The zoom percentage, `SCALE_MIN ..= SCALE_MAX`.
    pub z: i32,
}

impl Metrics {
    pub fn new(z: i32) -> Self {
        Metrics { z: z.clamp(SCALE_MIN, SCALE_MAX) }
    }

    /// A length at this zoom.
    pub fn px(&self, base: i32) -> i32 {
        ((base * self.z) / 100).max(1)
    }

    /// A font cell scale at this zoom — rounded to whole cells, never
    /// below one.
    pub fn fs(&self, base: i32) -> i32 {
        ((base * self.z + 50) / 100).max(1)
    }

    /// Kept as `s` for the many small paddings written in terms of it;
    /// it is the zoom rendered as an approximate whole multiplier.
    pub fn s(&self) -> i32 { (self.z / 100).max(1) }

    pub fn pad(&self) -> i32 { self.px(12) }
    pub fn title_scale(&self) -> i32 { self.fs(3) }
    pub fn label_scale(&self) -> i32 { self.fs(2) }
    pub fn small_scale(&self) -> i32 { self.fs(1) }
    pub fn row_h(&self) -> i32 { self.px(24) }
    pub fn value_w(&self) -> i32 { self.px(84) }
    pub fn track_h(&self) -> i32 { self.px(10) }
    pub fn strip_h(&self) -> i32 { self.px(14) }
    pub fn bank_h(&self) -> i32 { self.px(76) }
    pub fn cell_w(&self) -> i32 { self.px(15) }
    pub fn cell_h(&self) -> i32 { self.px(15) }
    pub fn cell_gap(&self) -> i32 { self.px(2) }
    /// A key's width in the window the panel *asks* for.
    ///
    /// **This one does not scale with the text**, and it is the
    /// exception that proves the rule above: a hundred and twenty-eight
    /// keys is a picture, not a label.  Tying it to the font would
    /// double the window's width to make the letters bigger, which is
    /// not what anyone asking for bigger letters means.
    pub fn key_w_preferred(&self) -> i32 { 5 }
    pub fn button(&self) -> i32 { self.px(18) }
    /// **Wide enough to grab.**  A four-pixel bar is a decoration you
    /// have to aim at; this one is a target.
    pub fn bar_w(&self) -> i32 { self.px(10) }

    /// The narrowest window that still draws everything without
    /// overlap: the strip can squeeze to a pixel a key, the sixteen
    /// routing cells cannot squeeze at all.
    pub fn min_width(&self, name_w: i32) -> i32 {
        self.pad() + name_w
            + CELLS * (self.cell_w() + self.cell_gap())
            + self.pad() + self.bar_w()
    }

    /// **Not the content's height.**  A window may be shorter than what
    /// it holds — that is what scrolling is for — so the floor is only
    /// what makes a window worth opening.
    pub fn min_height(&self) -> i32 { self.px(90) }

    /// Where a bank's strip and matrix begin, and how much room they
    /// get.  The scrollbar's channel is reserved whether or not a
    /// thumb is in it, so content does not reflow the moment it
    /// overflows.
    pub fn strip_span(&self, w: i32, name_w: i32) -> (i32, i32) {
        let sx = self.pad() + name_w;
        (sx, (w - self.pad() - self.bar_w() - sx).max(KEYS))
    }
}

/// How wide the left column has to be, **measured rather than
/// declared**.
///
/// A fixed column scaled by the font is how a window ends up twice as
/// wide as its content: `warmdrone` has two six-letter names and does
/// not need the room `lowpassResonance` would. Everything drawn in this
/// column is measured through the same `font::width` the painter uses,
/// so the column is exactly as wide as the widest thing in it.
pub fn name_column(m: &Model, k: &Metrics) -> i32 {
    let mut w = 24 * k.s();
    for knob in &m.knobs {
        w = w.max(font::width(&knob.name, k.label_scale()));
    }
    for b in &m.banks {
        w = w.max(font::width(&b.name, k.label_scale()));
        let voices = format!("{} VOICES", b.voices);
        w = w.max(font::width(&voices, k.small_scale()) + 8 * k.s());
        let caption = match (&b.accepts, b.accepts.span()) {
            (Accepts::Everything, _) | (_, Some((_, _, true))) =>
                "ACCEPTS ANY KEY".to_string(),
            (_, None) => "ACCEPTS NO KEY".to_string(),
            (_, Some((lo, hi, _))) => format!("KEYS {lo}-{hi}"),
        };
        w = w.max(font::width(&caption, k.small_scale()));
    }
    w + 16 * k.s()
}

/// How tall this model is at this scale and width — what a window would
/// have to be to show all of it at once.
pub fn content_height(m: &Model, scale: i32) -> i32 {
    let k = Metrics::new(scale);
    let b = k.button();
    let mut h = k.pad() + font::height(k.title_scale()).max(b) + k.pad();
    if !m.knobs.is_empty() {
        h += font::height(k.small_scale()) + 6 * k.s();
        h += m.knobs.len() as i32 * k.row_h();
        h += k.pad();
    }
    if !m.banks.is_empty() {
        h += font::height(k.small_scale()) + 6 * k.s();
        h += m.banks.len() as i32 * k.bank_h();
        h += k.pad();
    }
    h
}

/// The window this model wants, in pixels, at this scale.
///
/// The size is a *function of the descriptor*, so a synth with two
/// knobs does not open a window sized for twelve.  CLAP asks through
/// `get_size` before the window exists, which is exactly why this has
/// to be computable without one.
pub fn size(m: &Model, scale: i32) -> (i32, i32) {
    let k = Metrics::new(scale);
    let name_w = name_column(m, &k);
    let w = k.pad() + name_w + k.px(200) + k.value_w() + k.pad();
    // A window with banks in it opens wide enough for a legible strip;
    // one without stays as narrow as the faders need.
    let w = if m.banks.is_empty() {
        w
    } else {
        w.max(k.pad() + name_w + KEYS * k.key_w_preferred()
              + k.pad() + k.bar_w())
    };
    (w.max(k.min_width(name_w)),
     content_height(m, scale).max(k.min_height()))
}

/// The narrowest window this model can be drawn in at this zoom.
///
/// A convenience over `Metrics::min_width` for callers that have the
/// model but no reason to know the name column exists — which is every
/// caller outside this file.
pub fn min_size(m: &Model, scale: i32) -> (i32, i32) {
    let k = Metrics::new(scale);
    (k.min_width(name_column(m, &k)), k.min_height())
}

/// The furthest the view may be scrolled: zero when everything fits.
pub fn max_scroll(m: &Model, scale: i32, window_h: i32) -> i32 {
    (content_height(m, scale) - window_h).max(0)
}

/// Draw the model.
///
/// `hot` is the parameter currently being dragged; `scroll` is how far
/// down the content the window is looking.
///
/// **Scrolling is an offset on the layout, not a second pass.**  Every
/// item and every hit region is placed from the same running `y`, so
/// subtracting the scroll once at the top moves the picture and what
/// listens by exactly the same amount.  A hit test that forgot the
/// offset would write the parameter belonging to whatever used to be
/// under the pointer, which is the classic scrolling-UI defect and is
/// unreachable when there is only one `y` to be wrong about.
pub fn view(m: &Model, w: i32, hot: Option<u32>, scale: i32, scroll: i32)
    -> Display
{
    let k = Metrics::new(scale);
    let name_w = name_column(m, &k);
    let mut d = Display::new();
    let mut y = k.pad() - scroll;

    d.text(k.pad(), y, &m.title, INK, k.title_scale());

    // **The size buttons, top right.**  Panel-local: pressing one
    // changes how big the text is and tells the host nothing, because
    // how big the text is on your screen is not a property of the
    // instrument (`list::Kind::Button`).
    let b = k.button();
    let right = w - k.pad() - k.bar_w();
    for (i, (label, act)) in
        [("-", ACT_SMALLER), ("+", ACT_LARGER)].iter().enumerate()
    {
        let x = right - b - (1 - i as i32) * (b + 4 * k.s());
        // Compared against the *zoom*, not the rounded multiplier — a
        // percentage and a whole-number scale are different units, and
        // mixing them left both buttons permanently live.
        let live = if *act == ACT_SMALLER { k.z > SCALE_MIN }
                   else { k.z < SCALE_MAX };
        d.rect(x, y, b, b, if live { TRACK } else { BG });
        let lw = font::width(label, k.label_scale());
        d.text(x + (b - lw) / 2, y + (b - font::height(k.label_scale())) / 2,
               label, if live { INK } else { DIM }, k.label_scale());
        if live {
            d.hit(Kind::Button(*act), crate::list::NO_PARAM,
                  (x, y, x + b, y + b));
        }
    }
    let tw = font::width("TEXT", k.small_scale());
    d.text(right - 2 * b - 4 * k.s() - 6 * k.s() - tw,
           y + (b - font::height(k.small_scale())) / 2,
           "TEXT", DIM, k.small_scale());

    y += font::height(k.title_scale()).max(b) + k.pad();

    if !m.knobs.is_empty() {
        d.text(k.pad(), y, "KNOBS", DIM, k.small_scale());
        y += font::height(k.small_scale()) + 6 * k.s();

        let track_x = k.pad() + name_w;
        let track_w = (right - k.value_w() - track_x).max(40 * k.s());

        for knob in &m.knobs {
            let mid = y + k.row_h() / 2;
            let ty = mid - k.track_h() / 2;

            d.text(k.pad(), mid - font::height(k.label_scale()) / 2,
                   &knob.name, INK, k.label_scale());

            d.rect(track_x, ty, track_w, k.track_h(), TRACK);
            let filled = (track_w as f64 * knob.fraction()).round() as i32;
            if filled > 0 {
                let c = if hot == Some(knob.param) { HOT } else { FILL };
                d.rect(track_x, ty, filled, k.track_h(), c);
            }

            // The value, right-aligned against the pane's edge.  Width
            // comes from the font rather than a guess, so a long number
            // cannot walk off the panel.
            let label = knob.label();
            let lw = font::width(&label, k.label_scale());
            d.text(right - lw, mid - font::height(k.label_scale()) / 2,
                   &label, DIM, k.label_scale());

            // **The whole track listens, not the filled part.**  A
            // press near the left of a nearly-empty fader is a request
            // for a small value, not a miss.
            d.hit(Kind::Fader(Axis::X), knob.param,
                  (track_x, y, track_x + track_w, y + k.row_h()));

            y += k.row_h();
        }
        y += k.pad();
    }

    if !m.banks.is_empty() {
        d.text(k.pad(), y, "NOTES", DIM, k.small_scale());
        y += font::height(k.small_scale()) + 6 * k.s();

        for bank in &m.banks {
            d.text(k.pad(), y, &bank.name, INK, k.label_scale());
            let voices = format!("{} VOICES", bank.voices);
            d.text(k.pad() + name_w
                       - font::width(&voices, k.small_scale()) - 8 * k.s(),
                   y + font::height(k.label_scale())
                       - font::height(k.small_scale()),
                   &voices, DIM, k.small_scale());

            // What the strip is, said in words beside it — a bare bar of
            // colour is not self-describing, and the first question
            // anyone asks of one is "what am I looking at".
            let caption = match (&bank.accepts, bank.accepts.span()) {
                (Accepts::Everything, _) => "ACCEPTS ANY KEY".to_string(),
                (_, None) => "ACCEPTS NO KEY".to_string(),
                (_, Some((_, _, true))) => "ACCEPTS ANY KEY".to_string(),
                (_, Some((lo, hi, _))) => format!("KEYS {lo}-{hi}"),
            };
            d.text(k.pad(), y + font::height(k.label_scale()) + 5 * k.s(),
                   &caption, DIM, k.small_scale());

            let (sx, avail) = k.strip_span(w, name_w);
            let sy = y + font::height(k.label_scale()) + 6 * k.s();

            match (&bank.accepts, bank.accepts.span()) {
                // **Words wherever the strip would be one colour.**
                // `Everything` is the structural payload; a table that
                // accepts every key at every velocity is the same
                // picture arrived at differently, and both are facts a
                // sentence states better than a bar.
                (Accepts::Everything, _) => {
                    d.text(sx, sy, "ALL KEYS - STRUCTURAL PAYLOAD", DIM,
                           k.label_scale());
                }
                (_, Some((_, _, true))) => {
                    d.text(sx, sy, "ALL KEYS - THIS BANK'S OWN PAYLOAD",
                           DIM, k.small_scale());
                }
                (_, None) => {
                    d.text(sx, sy, "NO KEY REACHES THIS BANK", NOTE_SOME,
                           k.label_scale());
                }
                (Accepts::Table { .. }, _) => {
                    // **The strip scales to the window.**  Each key's
                    // edges come from the proportion rather than from a
                    // fixed cell width, so the band always ends exactly
                    // where the pane does — no overflow when the host
                    // narrows us, no gutter when it widens us, and no
                    // rounding crumbs between cells because each key
                    // starts where the last one ended.
                    for key in 0..KEYS {
                        let x0 = sx + avail * key / KEYS;
                        let x1 = sx + avail * (key + 1) / KEYS;
                        let (yes, total) = bank.accepts.at(key as usize);
                        let c = if yes == 0 {
                            NOTE_NONE
                        } else if yes >= total {
                            NOTE_ALL
                        } else {
                            NOTE_SOME
                        };
                        // **Cells touch.**  A gap between them combs a
                        // working range into stripes, and the fact
                        // being read here is "this stretch answers" —
                        // a band, not a picket fence.
                        d.rect(x0, sy, x1 - x0, k.strip_h(), c);
                    }
                    // **The octave marks carry numbers.**  Keys of the
                    // same state merge into one band — which is the
                    // right way to read "this stretch answers" — but it
                    // leaves a thin key invisible inside a wide block,
                    // so the picture says nothing about its own scale.
                    // A reader counting blocks counts octaves and
                    // concludes there are eleven keys.  The MIDI number
                    // under each mark is what makes it a ruler.
                    let mut key = 0;
                    while key < KEYS {
                        let x = sx + avail * key / KEYS;
                        d.rect(x, sy, k.s(), k.strip_h(), BG);
                        d.rect(x, sy + k.strip_h() + k.s(), k.s(), 3 * k.s(), DIM);
                        d.text(x + 2 * k.s(), sy + k.strip_h() + 6 * k.s(),
                               &format!("{key}"), DIM, k.small_scale());
                        key += 12;
                    }
                }
            }

            // **The routing matrix, and it reacts.**  Which MIDI
            // channel feeds this bank is a real stepped parameter the
            // plugin already declares — `Instance.routing`, one cell
            // per (bank × channel) — so the cells are `Toggle` hits
            // writing those ids.  This is the one thing on the panel a
            // player can *change* about notes; which keys a bank
            // accepts stays the program's to say.
            let ry = sy + k.strip_h() + 18 * k.s();
            for c in 0..CELLS {
                let cx = sx + c * (k.cell_w() + k.cell_gap());
                let on = bank.listens_on(c as usize);
                d.rect(cx, ry, k.cell_w(), k.cell_h(),
                       if on { CELL_ON } else { CELL_OFF });
                // The channel number, 1-based the way every DAW counts
                // them, centred in its cell.
                let label = format!("{}", c + 1);
                let lw = font::width(&label, k.small_scale());
                d.text(cx + (k.cell_w() - lw) / 2,
                       ry + (k.cell_h() - font::height(k.small_scale())) / 2,
                       &label, if on { BG } else { DIM }, k.small_scale());
                d.hit(Kind::Toggle, bank.routing_param0 + c as u32,
                      (cx, ry, cx + k.cell_w(), ry + k.cell_h()));
            }

            y += k.bank_h();
        }
    }

    d
}

/// The scrollbar, drawn last so it sits over the content, and only when
/// there is something to scroll.
///
/// It is **indication, not a control**: the wheel scrolls, and a thumb
/// you cannot drag is still worth drawing because otherwise nothing on
/// screen says there is more below.
pub fn scrollbar(d: &mut Display, m: &Model, w: i32, h: i32, scale: i32,
                 scroll: i32) {
    let k = Metrics::new(scale);
    let content = content_height(m, scale);
    if content <= h {
        return;
    }
    let x = w - k.bar_w();
    d.rect(x, 0, k.bar_w(), h, TRACK);
    let thumb = ((h as i64 * h as i64) / content as i64).max(16) as i32;
    let span = h - thumb;
    let max = (content - h).max(1);
    let top = (span as i64 * scroll.clamp(0, max) as i64 / max as i64) as i32;
    d.rect(x, top, k.bar_w(), thumb, BAR);
}
