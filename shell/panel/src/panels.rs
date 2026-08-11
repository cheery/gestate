//! The two panels: a `Model` to a `Display`, and nothing else.
//!
//! **A pure function, which is acceptance test 2.**  No window, no
//! clock, no host — the same model draws the same list every time, so
//! the layout is checkable the way a render is.

use crate::font;
use crate::list::{Axis, Colour, Display};
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

// ── Layout ───────────────────────────────────────────────────────────

const PAD: i32 = 12;
const TITLE_SCALE: i32 = 3;
const LABEL_SCALE: i32 = 2;
const SMALL_SCALE: i32 = 1;

const ROW_H: i32 = 24;
const NAME_W: i32 = 156;
const VALUE_W: i32 = 84;
const TRACK_H: i32 = 10;

const KEYS: i32 = 128;
const KEY_W: i32 = 2;
const STRIP_H: i32 = 14;
const BANK_H: i32 = 40;

/// The window this model wants, in pixels.
///
/// The size is a *function of the descriptor*, so a synth with two
/// knobs does not open a window sized for twelve.  CLAP asks through
/// `get_size` before the window exists, which is exactly why this has
/// to be computable without one.
pub fn size(m: &Model) -> (i32, i32) {
    let w = PAD + NAME_W + 260 + VALUE_W + PAD;
    let w = w.max(PAD * 2 + KEYS * KEY_W + NAME_W);
    let mut h = PAD + font::height(TITLE_SCALE) + PAD;
    if !m.knobs.is_empty() {
        h += font::height(SMALL_SCALE) + 6;
        h += m.knobs.len() as i32 * ROW_H;
        h += PAD;
    }
    if !m.banks.is_empty() {
        h += font::height(SMALL_SCALE) + 6;
        h += m.banks.len() as i32 * BANK_H;
        h += PAD;
    }
    (w, h.max(120))
}

/// Draw the model.  `hot` is the parameter currently being dragged, if
/// any — it is the only piece of interaction state the drawing knows
/// about, and it exists so a drag is visible on the thing being dragged
/// rather than only in the number.
pub fn view(m: &Model, w: i32, hot: Option<u32>) -> Display {
    let mut d = Display::new();
    let mut y = PAD;

    d.text(PAD, y, &m.title, INK, TITLE_SCALE);
    y += font::height(TITLE_SCALE) + PAD;

    if !m.knobs.is_empty() {
        d.text(PAD, y, "KNOBS", DIM, SMALL_SCALE);
        y += font::height(SMALL_SCALE) + 6;

        let track_x = PAD + NAME_W;
        let track_w = (w - PAD - VALUE_W - track_x).max(40);

        for k in &m.knobs {
            let mid = y + ROW_H / 2;
            let ty = mid - TRACK_H / 2;

            d.text(PAD, mid - font::height(LABEL_SCALE) / 2, &k.name, INK,
                   LABEL_SCALE);

            d.rect(track_x, ty, track_w, TRACK_H, TRACK);
            let filled = (track_w as f64 * k.fraction()).round() as i32;
            if filled > 0 {
                let c = if hot == Some(k.param) { HOT } else { FILL };
                d.rect(track_x, ty, filled, TRACK_H, c);
            }

            // The value, right-aligned against the window edge.  Width
            // comes from the font rather than a guess, so a long number
            // cannot walk off the pane.
            let label = k.label();
            let lw = font::width(&label, LABEL_SCALE);
            d.text(w - PAD - lw, mid - font::height(LABEL_SCALE) / 2, &label,
                   DIM, LABEL_SCALE);

            // **The whole track listens, not the filled part.**  A
            // press near the left of a nearly-empty fader is a request
            // for a small value, not a miss.
            d.hit(Axis::X, k.param, (track_x, y, track_x + track_w, y + ROW_H));

            y += ROW_H;
        }
        y += PAD;
    }

    if !m.banks.is_empty() {
        d.text(PAD, y, "NOTES", DIM, SMALL_SCALE);
        y += font::height(SMALL_SCALE) + 6;

        for b in &m.banks {
            d.text(PAD, y, &b.name, INK, LABEL_SCALE);
            let voices = format!("{} VOICES", b.voices);
            d.text(PAD + NAME_W - font::width(&voices, SMALL_SCALE) - 8,
                   y + font::height(LABEL_SCALE) - font::height(SMALL_SCALE),
                   &voices, DIM, SMALL_SCALE);

            let sx = PAD + NAME_W;
            let sy = y + font::height(LABEL_SCALE) + 6;

            match &b.accepts {
                // **Words, not a wall of one colour.**  A strip that is
                // uniformly "yes" looks like a rendering bug, and the
                // fact worth saying is which payload is in use.
                Accepts::Everything => {
                    d.text(sx, sy, "ALL KEYS - STRUCTURAL PAYLOAD", DIM,
                           LABEL_SCALE);
                }
                Accepts::Table { .. } => {
                    for key in 0..KEYS {
                        let (yes, total) = b.accepts.at(key as usize);
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
                        d.rect(sx + key * KEY_W, sy, KEY_W, STRIP_H, c);
                    }
                    // An octave line every 12 keys, cut through the
                    // band in the background colour so a player can
                    // count octaves without counting cells.
                    let mut key = 0;
                    while key < KEYS {
                        d.rect(sx + key * KEY_W, sy, 1, STRIP_H, BG);
                        d.rect(sx + key * KEY_W, sy + STRIP_H + 1, 1, 3, DIM);
                        key += 12;
                    }
                }
            }

            y += BANK_H;
        }
    }

    d
}
