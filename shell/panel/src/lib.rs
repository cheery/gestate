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
pub use list::{Axis, Colour, Display, Hit, Item};
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
    display: Display,
    interaction: Interaction,
}

impl Panel {
    pub fn new(model: Model) -> Self {
        let (width, height) = panels::size(&model);
        let mut p = Panel {
            model,
            width,
            height,
            display: Display::new(),
            interaction: Interaction::new(),
        };
        p.relayout();
        p
    }

    fn relayout(&mut self) {
        self.display = panels::view(&self.model, self.width,
                                    self.interaction.hot());
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
            if let Some(k) = self.model.knobs.iter_mut()
                .find(|k| k.param == *param)
            {
                if k.value != *v {
                    k.value = *v;
                    touched = true;
                }
            }
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

    pub fn press(&mut self, x: i32, y: i32) -> Vec<Change> {
        let out = self.interaction.press(&self.display, &self.model, x, y);
        self.apply(&out);
        out
    }

    pub fn motion(&mut self, x: i32, y: i32) -> Vec<Change> {
        let out = self.interaction.motion(&self.display, &self.model, x, y);
        self.apply(&out);
        out
    }

    pub fn release(&mut self) -> Vec<Change> {
        let out = self.interaction.release();
        self.relayout();
        out
    }

    /// A gesture's own value goes into the model at once rather than
    /// waiting for the host to echo it back — a fader that only moved
    /// once the DAW answered would feel broken on every host that
    /// answers a block late.
    fn apply(&mut self, changes: &[Change]) {
        let mut touched = false;
        for c in changes {
            if let Change::Value(param, v) = c {
                if let Some(k) = self.model.knobs.iter_mut()
                    .find(|k| k.param == *param)
                {
                    k.value = *v;
                    touched = true;
                }
            }
        }
        if touched || !changes.is_empty() {
            self.relayout();
        }
    }

    pub fn display(&self) -> &Display {
        &self.display
    }

    /// Paint the current layout into a fresh canvas.
    pub fn render(&self) -> Canvas {
        let mut c = Canvas::new(self.width, self.height, panels::BG);
        paint::paint(&mut c, &self.display);
        c
    }
}

#[cfg(test)]
mod tests;
