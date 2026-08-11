//! `gestate-panel` — the plugin's own window.
//!
//! `spec/panel.md` is the design.  The shape of it:
//!
//! ```text
//!   descriptor  ──┐
//!                 ├─→  Display  ──→  paint  ──→  pixels
//!   Sub (later) ──┘
//! ```
//!
//! `list` is the vocabulary the substrate already speaks (`gui.py`'s
//! `_walk` emits exactly these), `paint` turns it into pixels in
//! software, `model` is what a panel draws, `panels` is the layout and
//! `interact` is pointer events to parameter changes.  All of that is
//! dependency-free and testable without a window.
//!
//! `window` — behind the feature of the same name — is the only place
//! `baseview` and `softbuffer` appear, so `shell/clap` without the
//! `gui` feature is the zero-dependency shell it has always been.

pub mod font;
pub mod interact;
pub mod list;
pub mod model;
pub mod paint;
pub mod panels;

#[cfg(feature = "window")]
pub mod window;

pub use interact::{Change, Interaction};
pub use list::{Axis, Colour, Display, Hit, Item, Kind};
pub use model::{Accepts, BankView, Knob, Model};
pub use paint::Canvas;

/// The panel as one object: a model, its layout, and the pointer state.
///
/// The shell holds one of these per open window and hands it events.
/// It keeps `Display` and `Interaction` together deliberately — a
/// gesture reads the regions the *current* layout produced, and letting
/// those two drift apart is how a resize turns a drag into a write to
/// whatever moved under the pointer.
pub struct Panel {
    pub model: Model,
    pub width: i32,
    pub height: i32,
    /// How big the text is, `panels::SCALE_MIN ..= SCALE_MAX`.
    ///
    /// **A view preference, not a parameter.**  It never reaches
    /// `out_events`: how large the letters are on your screen is not a
    /// property of the instrument, and a host that automated it would
    /// be automating your eyesight.
    scale: i32,
    /// How far down the content the window is looking.
    scroll: i32,
    /// Whether the scrollbar's thumb is being dragged.
    bar_drag: bool,
    display: Display,
    interaction: Interaction,
}

impl Panel {
    pub fn new(model: Model) -> Self {
        Panel::with_scale(model, panels::SCALE_DEFAULT)
    }

    pub fn with_scale(model: Model, scale: i32) -> Self {
        let scale = scale.clamp(panels::SCALE_MIN, panels::SCALE_MAX);
        let (width, height) = panels::size(&model, scale);
        let mut p = Panel {
            model,
            width,
            height,
            scale,
            scroll: 0,
            bar_drag: false,
            display: Display::new(),
            interaction: Interaction::new(),
        };
        p.relayout();
        p
    }

    fn relayout(&mut self) {
        // Clamp first: a scale or size change can leave the view
        // scrolled past the end, and a blank pane with content above it
        // reads as a crash.
        self.scroll = self.scroll.clamp(0, self.max_scroll());
        self.display = panels::view(&self.model, self.width,
                                    self.interaction.hot(), self.scale,
                                    self.scroll);
    }

    pub fn scale(&self) -> i32 {
        self.scale
    }

    pub fn scroll(&self) -> i32 {
        self.scroll
    }

    pub fn max_scroll(&self) -> i32 {
        panels::max_scroll(&self.model, self.scale, self.height)
    }

    /// The size this panel would like at its current scale — what the
    /// window should become when the text grows.
    pub fn wanted_size(&self) -> (i32, i32) {
        panels::size(&self.model, self.scale)
    }

    /// Set the zoom, as a percentage.  Returns whether it moved.
    ///
    /// **The window is not resized to match**, deliberately: how big
    /// the window is belongs to the host and the person dragging its
    /// corner, and a panel that grew itself every time you enlarged the
    /// text would fight both.  Content that no longer fits scrolls,
    /// which is what scrolling is for.
    pub fn set_scale(&mut self, scale: i32) -> bool {
        let scale = scale.clamp(panels::SCALE_MIN, panels::SCALE_MAX);
        if scale == self.scale {
            return false;
        }
        self.scale = scale;
        self.relayout();
        true
    }

    /// Scroll by a number of pixels, clamped to the content.  Returns
    /// whether the view moved — a wheel at the bottom of a short list
    /// should not cost a repaint.
    pub fn scroll_by(&mut self, dy: i32) -> bool {
        let next = (self.scroll + dy).clamp(0, self.max_scroll());
        if next == self.scroll {
            return false;
        }
        self.scroll = next;
        self.relayout();
        true
    }

    /// Replace the values a host reports, keeping the layout.
    ///
    /// **Values only** — the set of knobs comes from the descriptor and
    /// cannot change while a plugin is loaded, so a host telling us a
    /// value never needs to move a region.  A drag in flight keeps its
    /// own value: accepting the host's echo mid-gesture is how a fader
    /// fights the hand holding it.
    pub fn sync_values(&mut self, values: &[(u32, f64)]) {
        let dragging = self.interaction.hot();
        let mut touched = false;
        for (param, v) in values {
            if Some(*param) == dragging {
                continue;
            }
            touched |= Panel::set(&mut self.model, *param, *v);
        }
        if touched {
            self.relayout();
        }
    }

    pub fn resize(&mut self, w: i32, h: i32) {
        self.width = w.max(1);
        self.height = h.max(1);
        self.relayout();
    }

    /// A press.
    ///
    /// **Buttons are handled here and never reach the host.**  A
    /// `Kind::Button` carries a panel action, not a parameter id, so it
    /// cannot be turned into a `Change` even by accident — the type
    /// says so.
    pub fn press(&mut self, x: i32, y: i32) -> Vec<Change> {
        // **The bar is tested before anything else**, because it lies
        // over the content: a press in its channel is a scroll, not a
        // click on whatever the bar happens to be covering.
        if let Some((bx0, _, bx1, _)) = self.bar_rect() {
            if x >= bx0 && x < bx1 {
                self.bar_drag = true;
                self.scroll_to_thumb(y);
                return Vec::new();
            }
        }
        if let Some(hit) = self.display.pick(x, y) {
            if let Kind::Button(act) = hit.kind {
                match act {
                    panels::ACT_SMALLER =>
                        { self.set_scale(self.scale - panels::SCALE_STEP); }
                    panels::ACT_LARGER =>
                        { self.set_scale(self.scale + panels::SCALE_STEP); }
                    _ => {}
                }
                return Vec::new();
            }
        }
        let out = self.interaction.press(&self.display, &self.model, x, y);
        self.apply(&out);
        out
    }

    pub fn motion(&mut self, x: i32, y: i32) -> Vec<Change> {
        if self.bar_drag {
            self.scroll_to_thumb(y);
            return Vec::new();
        }
        let out = self.interaction.motion(&self.display, &self.model, x, y);
        self.apply(&out);
        out
    }

    pub fn release(&mut self) -> Vec<Change> {
        self.bar_drag = false;
        let out = self.interaction.release();
        self.relayout();
        out
    }

    /// The scrollbar's channel, or nothing when everything fits.
    pub fn bar_rect(&self) -> Option<(i32, i32, i32, i32)> {
        if self.max_scroll() == 0 {
            return None;
        }
        let k = panels::Metrics::new(self.scale);
        let x = self.width - k.bar_w();
        Some((x, 0, self.width, self.height))
    }

    /// Put the thumb's middle where the pointer is.
    ///
    /// Grabbing by the middle rather than by an offset means a press
    /// anywhere in the channel jumps there and a drag tracks the hand
    /// exactly — the offset version feels better only if you always
    /// grab the thumb, and here you often will not.
    fn scroll_to_thumb(&mut self, y: i32) {
        let max = self.max_scroll();
        if max == 0 {
            return;
        }
        let content = panels::content_height(&self.model, self.scale);
        let thumb = ((self.height as i64 * self.height as i64)
                     / content.max(1) as i64).max(16) as i32;
        let span = (self.height - thumb).max(1);
        let want = ((y - thumb / 2).clamp(0, span) as i64 * max as i64
                    / span as i64) as i32;
        if want != self.scroll {
            self.scroll = want;
            self.relayout();
        }
    }

    /// A gesture's own value goes into the model at once rather than
    /// waiting for the host to echo it back — a fader that only moved
    /// once the DAW answered would feel broken on every host that
    /// answers a block late.
    fn apply(&mut self, changes: &[Change]) {
        for c in changes {
            if let Change::Value(param, v) = c {
                Panel::set(&mut self.model, *param, *v);
            }
        }
        if !changes.is_empty() {
            self.relayout();
        }
    }

    /// One parameter into the model — a knob's value, or a routing
    /// cell's bit.
    ///
    /// **One place, because there is one numbering.**  A knob is its
    /// control slot and a routing cell is `controls.len() + bank*16 +
    /// channel`; the panel learns the base from the model rather than
    /// recomputing the shell's arithmetic, so the two cannot drift.
    fn set(model: &mut Model, param: u32, value: f64) -> bool {
        if let Some(k) = model.knobs.iter_mut().find(|k| k.param == param) {
            k.value = value;
            return true;
        }
        for b in model.banks.iter_mut() {
            let Some(c) = param.checked_sub(b.routing_param0) else {
                continue;
            };
            if c < 16 {
                let bit = 1u16 << c;
                if value >= 0.5 {
                    b.routing |= bit;
                } else {
                    b.routing &= !bit;
                }
                return true;
            }
        }
        false
    }

    pub fn display(&self) -> &Display {
        &self.display
    }

    /// Paint the current layout into a fresh canvas.
    pub fn render(&self) -> Canvas {
        let mut c = Canvas::new(self.width, self.height, panels::BG);
        paint::paint(&mut c, &self.display);
        // The bar is drawn over the content and outside the display
        // list, because it is a fact about the *window* rather than
        // about the model — nothing in a `Sub` will ever produce one.
        let mut bar = Display::new();
        panels::scrollbar(&mut bar, &self.model, self.width, self.height,
                          self.scale, self.scroll);
        paint::paint(&mut c, &bar);
        c
    }
}

#[cfg(test)]
mod tests;
