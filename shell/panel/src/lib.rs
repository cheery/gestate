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

#[cfg(feature = "substrate")]
pub mod canvas;

#[cfg(feature = "substrate")]
pub mod substrate;

#[cfg(feature = "window")]
pub mod window;

pub use interact::{Change, Interaction, Key};
pub use list::{Axis, Colour, Display, Hit, Item, Kind};
pub use model::{Accepts, BankView, Knob, Model, SeedView, Tab};
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
    /// The toolbar, laid out separately because it does not scroll.
    ///
    /// **Two lists, not one, and the split is the same one the
    /// scrollbar already made**: content is a function of the model and
    /// the scroll, chrome is a function of the model and the window.
    /// Keeping them apart is what lets a press be tested against the
    /// chrome *first*, so a tab under which the content happens to have
    /// scrolled a fader is still a tab.
    chrome: Display,
    tab: Tab,
    /// The stream a press on `RNG` draws its next seed from.
    ///
    /// **Seeded to a constant, and stirred by the host.**  A panel is
    /// a pure function of its model everywhere else, and reading a
    /// clock in here would make the one interesting button in the
    /// window untestable.  So the sequence is deterministic and
    /// `stir` is how a real window gets a different one each time it
    /// opens — the shell has a clock and this does not.
    rng: u64,
    /// The digits typed into the seed field, while one is being typed.
    ///
    /// **`None` is not editing, and that distinction owns the
    /// keyboard.**  `spec/panel.md`'s rule is that a DAW lets you play
    /// the piano keys while a plugin window has focus, so the panel
    /// passes key events back — and it must keep doing that, or an open
    /// window takes the instrument's keyboard away.  The exception is a
    /// person deliberately typing into a five-character box, and it
    /// lasts exactly as long as they are.
    editing: Option<String>,
    /// The program's own picture, when this plugin carries one.
    ///
    /// **The second source, and it lives here rather than beside the
    /// panel** because the two share everything downstream of the
    /// display list: one painter, one scrollbar, one window, one set of
    /// pointer events.  `spec/panel.md` §"One painter, two sources" is
    /// the design; this field is the sentence where it stops being a
    /// diagram.
    #[cfg(feature = "substrate")]
    canvas: Option<canvas::Canvas>,
    interaction: Interaction,
}

/// splitmix64 — one multiply-xor round, which is all a button that
/// picks a five-digit number needs.
fn next_rand(state: &mut u64) -> u64 {
    *state = state.wrapping_add(0x9E37_79B9_7F4A_7C15);
    let mut z = *state;
    z = (z ^ (z >> 30)).wrapping_mul(0xBF58_476D_1CE4_E5B9);
    z = (z ^ (z >> 27)).wrapping_mul(0x94D0_49BB_1331_11EB);
    z ^ (z >> 31)
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
            chrome: Display::new(),
            tab: Tab::default(),
            rng: 0x5EED_5EED_5EED_5EED,
            editing: None,
            #[cfg(feature = "substrate")]
            canvas: None,
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
        self.chrome = Display::new();
        panels::toolbar_editing(&mut self.chrome, &self.model, self.width,
                                self.scale, self.tab,
                                self.editing.as_deref());
    }

    pub fn tab(&self) -> Tab {
        self.tab
    }

    /// Give this panel the program's own canvas.
    ///
    /// The second tab appears because there is now something behind
    /// it, which is the only reason a tab should ever appear.
    #[cfg(feature = "substrate")]
    pub fn attach_canvas(&mut self, c: canvas::Canvas) {
        self.canvas = Some(c);
        self.model.has_canvas = true;
        self.relayout();
    }

    #[cfg(feature = "substrate")]
    pub fn canvas(&self) -> Option<&canvas::Canvas> {
        self.canvas.as_ref()
    }

    /// The point the canvas's own origin lands on.
    ///
    /// **The top-left of what the toolbar leaves, not the middle**, and
    /// that is the reference's convention rather than a choice made
    /// here: `gui.py`'s `_flatten` walks from `cx = cy = 0`, so a
    /// program's centre sits at the window's corner and the program
    /// places itself — `substrate.ges` opens with `moveXY 120 140` for
    /// exactly that reason.
    ///
    /// Centring here instead looked more sensible and was wrong: it
    /// added half a window to an offset the program had already
    /// applied, and every existing canvas came out down and to the
    /// right of where its author put it.  The rule for this module is
    /// that the two hosts agree tree for tree, and the origin is part
    /// of the tree's meaning.
    #[cfg(feature = "substrate")]
    fn canvas_origin(&self) -> (i32, i32) {
        (0, panels::toolbar_h(&self.model, self.scale))
    }

    /// One instant of the canvas, and the picture that follows it.
    ///
    /// Called once a frame by whatever owns the window.  **Even on the
    /// tab you are not looking at**: a substrate is a fold over time,
    /// and one that stopped folding while hidden would come back
    /// showing a stale world and then jump — which is worse than
    /// paying for a walk nobody sees.  A program that draws nothing
    /// pays nothing, because there is no canvas to tick.
    #[cfg(feature = "substrate")]
    pub fn tick_canvas(&mut self, writes: &[(i64, f64)]) {
        let (cx, cy) = self.canvas_origin();
        let Some(c) = self.canvas.as_mut() else { return };
        c.tick(writes, cx, cy);
        let fault = c.fault().map(|f| f.to_string());
        if let Some(f) = fault {
            self.set_notice(Some(f));
        }
    }

    /// Write a named channel the program declared — the *instrument*
    /// reaching the canvas, where a touch is a hand reaching it.
    ///
    /// `peak` is the one this exists for: the host says how loud the
    /// last block was and a meter in the picture moves.  A program
    /// that declares no such channel is not written to and does not pay
    /// for the reading.
    #[cfg(feature = "substrate")]
    pub fn canvas_channel(&self, name: &str) -> Option<i64> {
        self.canvas.as_ref().and_then(|c| c.channel(name))
    }

    /// The canvas channel a host parameter also is, if any.
    #[cfg(feature = "substrate")]
    pub fn canvas_channel_of_param(&self, param: u32) -> Option<i64> {
        self.canvas.as_ref().and_then(|c| c.chan_of_param(param))
    }

    /// Show the other source.  Returns whether it moved.
    pub fn set_tab(&mut self, tab: Tab) -> bool {
        if self.tab == tab || (tab == Tab::Canvas && !self.model.has_canvas) {
            return false;
        }
        self.tab = tab;
        self.relayout();
        true
    }

    /// Give the reroll button a different stream to draw from.
    ///
    /// The shell calls this once, with a clock, when it opens a
    /// window.  Nothing else in the panel reads entropy.
    pub fn stir(&mut self, entropy: u64) {
        self.rng ^= entropy;
    }

    /// The chrome — the toolbar, which does not scroll.
    pub fn chrome(&self) -> &Display {
        &self.chrome
    }

    /// Whether the panel is typing.
    ///
    /// **The window asks this to decide who owns the keyboard.**  While
    /// it is false every key goes back to the host, which is how a DAW
    /// keeps its piano; while it is true the panel takes them, which is
    /// what typing means.
    pub fn is_editing(&self) -> bool {
        self.editing.is_some()
    }

    /// What is in the seed field right now, if one is open.
    pub fn editing(&self) -> Option<&str> {
        self.editing.as_deref()
    }

    /// A key, while the seed field is open.  Silent otherwise.
    ///
    /// The whole editor, and it is small on purpose: a seed is digits.
    /// Nothing here is a text widget — no selection, no cursor to move,
    /// no clipboard — because the field holds at most five characters
    /// and every one of those would be a thing to get right for no one.
    pub fn key(&mut self, key: Key) -> Vec<Change> {
        let Some(buf) = self.editing.as_mut() else {
            return Vec::new();
        };
        let digits = Panel::max_digits(&self.model);
        match key {
            Key::Digit(d) if buf.len() < digits => {
                // A leading zero is dropped rather than refused, so
                // typing `007` gives `7` and nobody has to know.
                if buf == "0" {
                    buf.clear();
                }
                buf.push((b'0' + d.min(9)) as char);
            }
            Key::Digit(_) => {}
            Key::Backspace => {
                buf.pop();
            }
            Key::Enter => return self.commit(),
            Key::Escape => {
                self.editing = None;
                self.relayout();
                return Vec::new();
            }
        }
        self.relayout();
        Vec::new()
    }

    /// How many digits the seed's own range allows.
    fn max_digits(model: &Model) -> usize {
        model.seed.as_ref()
            .map(|s| s.max.max(1).to_string().len())
            .unwrap_or(1)
    }

    /// Open the field, showing what is in it.
    fn begin_edit(&mut self) {
        let Some(seed) = self.model.seed.as_ref() else { return };
        self.editing = Some(seed.value.to_string());
        self.relayout();
    }

    /// Close the field, and tell the host if the number moved.
    ///
    /// **An empty field commits nothing**, which is what backspacing
    /// everything and pressing Enter should mean — the alternative is
    /// that clearing a field silently sets the seed to zero, which is
    /// a real take and not the one anybody asked for.
    fn commit(&mut self) -> Vec<Change> {
        let Some(buf) = self.editing.take() else { return Vec::new() };
        self.relayout();
        let Some(seed) = self.model.seed.as_ref() else { return Vec::new() };
        let (param, max, was) = (seed.param, seed.max, seed.value);
        let Ok(v) = buf.parse::<i64>() else { return Vec::new() };
        let v = v.clamp(0, max);
        if v == was {
            return Vec::new();
        }
        if let Some(s) = self.model.seed.as_mut() {
            s.value = v;
        }
        self.relayout();
        vec![Change::Begin(param),
             Change::Value(param, v as f64),
             Change::End(param)]
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

    /// Say something, or stop saying it.  Relays only on a change, so
    /// a steady message costs no repaints.
    pub fn set_notice(&mut self, notice: Option<String>) {
        if self.model.notice != notice {
            self.model.notice = notice;
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
        // **The toolbar is tested before the content**, for the same
        // reason the bar is: it lies over whatever has scrolled beneath
        // it, and a press on `RNG` must be a reroll rather than a
        // gesture on the fader that happens to be underneath.
        // **A press elsewhere commits.**  Typing a number and then
        // reaching for a fader means the number; throwing it away
        // because the next click was somewhere else is a field that
        // loses your work quietly, which is the worst way to lose it.
        let elsewhere = !matches!(
            self.chrome.pick(x, y),
            Some(Hit { kind: Kind::Button(panels::ACT_SEED_EDIT), .. }));
        let mut out = Vec::new();
        if self.editing.is_some() && elsewhere {
            out = self.commit();
        }
        if let Some(hit) = self.chrome.pick(x, y) {
            if let Kind::Button(act) = hit.kind {
                out.extend(self.act(act));
            }
            return out;
        }
        if !out.is_empty() {
            // The commit was the gesture; the press that caused it is
            // not also a drag on whatever it landed on.
            return out;
        }
        // **On the canvas the program owns the pointer.**  Its
        // attachments are its own and nothing here knows what they
        // mean; what comes back is a channel and a fraction, and the
        // only ones that reach the host are those the export paired
        // with a control.
        #[cfg(feature = "substrate")]
        if self.tab == Tab::Canvas {
            if let Some(c) = self.canvas.as_mut() {
                let writes = c.press(x, y);
                let out = c.changes(&writes, true);
                self.apply_canvas(&writes);
                self.apply(&out);
                return out;
            }
        }
        if let Some(hit) = self.display.pick(x, y) {
            if let Kind::Button(act) = hit.kind {
                return self.act(act);
            }
        }
        let out = self.interaction.press(&self.display, &self.model, x, y);
        self.apply(&out);
        out
    }

    /// A canvas write, applied at once so the picture follows the hand
    /// rather than waiting for the next frame.
    #[cfg(feature = "substrate")]
    fn apply_canvas(&mut self, writes: &[(i64, f64)]) {
        if writes.is_empty() {
            return;
        }
        self.tick_canvas(writes);
    }

    /// What a button does.
    ///
    /// **Every one of these is panel-local except the reroll**, and
    /// the reroll is not an exception to the rule so much as proof of
    /// it: it does not touch a seed, it asks the host to change a
    /// *parameter*, in one whole gesture, exactly as a fader does.  The
    /// panel still cannot reach the engine.
    fn act(&mut self, act: u32) -> Vec<Change> {
        match act {
            panels::ACT_SMALLER => {
                self.set_scale(self.scale - panels::SCALE_STEP);
            }
            panels::ACT_LARGER => {
                self.set_scale(self.scale + panels::SCALE_STEP);
            }
            panels::ACT_CONTROLS => { self.set_tab(Tab::Controls); }
            panels::ACT_CANVAS => { self.set_tab(Tab::Canvas); }
            panels::ACT_RESEED => return self.reseed(),
            panels::ACT_SEED_EDIT => {
                if self.editing.is_none() {
                    self.begin_edit();
                }
                return Vec::new();
            }
            _ => {}
        }
        Vec::new()
    }

    /// Roll a new take.
    ///
    /// The new seed is **never the old one** — a randomize button that
    /// can land on the number it started from is one that sometimes
    /// appears broken, and at one chance in a hundred thousand it would
    /// be a bug nobody could reproduce.
    fn reseed(&mut self) -> Vec<Change> {
        // Rolling and typing are two ways of saying the same thing, so
        // one abandons the other rather than leaving a stale caret
        // blinking over a number it no longer describes.
        self.editing = None;
        let Some(seed) = self.model.seed.as_ref() else {
            return Vec::new();
        };
        let (param, max, was) = (seed.param, seed.max.max(1), seed.value);
        let mut next = was;
        for _ in 0..8 {
            next = (next_rand(&mut self.rng) % (max as u64 + 1)) as i64;
            if next != was {
                break;
            }
        }
        if let Some(s) = self.model.seed.as_mut() {
            s.value = next;
        }
        self.relayout();
        vec![Change::Begin(param),
             Change::Value(param, next as f64),
             Change::End(param)]
    }

    pub fn motion(&mut self, x: i32, y: i32) -> Vec<Change> {
        if self.bar_drag {
            self.scroll_to_thumb(y);
            return Vec::new();
        }
        #[cfg(feature = "substrate")]
        if self.tab == Tab::Canvas {
            if let Some(c) = self.canvas.as_mut() {
                if !c.is_grabbing() {
                    return Vec::new();
                }
                let writes = c.motion(x, y);
                let out = c.changes(&writes, false);
                self.apply_canvas(&writes);
                self.apply(&out);
                return out;
            }
        }
        let out = self.interaction.motion(&self.display, &self.model, x, y);
        self.apply(&out);
        out
    }

    pub fn release(&mut self) -> Vec<Change> {
        self.bar_drag = false;
        #[cfg(feature = "substrate")]
        if self.tab == Tab::Canvas {
            if let Some(c) = self.canvas.as_mut() {
                // Close the gesture on whatever was grabbed, exactly
                // once — an unmatched `Begin` leaves the host in a
                // gesture forever.
                let out: Vec<Change> = c.grabbed()
                    .and_then(|ch| c.param_of(ch))
                    .map(Change::End)
                    .into_iter()
                    .collect();
                c.release();
                return out;
            }
        }
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
        if let Some(s) = model.seed.as_mut() {
            if s.param == param {
                s.value = (value.round() as i64).clamp(0, s.max);
                return true;
            }
        }
        for b in model.banks.iter_mut() {
            if param == b.score_param {
                b.plays_score = value >= 0.5;
                return true;
            }
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
        self.render_into(Canvas::new(self.width, self.height, panels::BG))
    }

    /// The same, onto a canvas the caller owns — so a window can keep
    /// one between frames and let it carry the alpha its surface wants.
    pub fn render_into(&self, mut c: Canvas) -> Canvas {
        c.clear(panels::BG);
        #[cfg(feature = "substrate")]
        if self.tab == Tab::Canvas {
            if let Some(cv) = self.canvas.as_ref() {
                paint::paint(&mut c, cv.display());
                paint::paint(&mut c, &self.chrome);
                return c;
            }
        }
        paint::paint(&mut c, &self.display);
        // The bar is drawn over the content and outside the display
        // list, because it is a fact about the *window* rather than
        // about the model — nothing in a `Sub` will ever produce one.
        // The toolbar over the content, so whatever has scrolled
        // under it is covered rather than showing through.
        paint::paint(&mut c, &self.chrome);
        let mut bar = Display::new();
        panels::scrollbar(&mut bar, &self.model, self.width, self.height,
                          self.scale, self.scroll);
        paint::paint(&mut c, &bar);
        c
    }
}

#[cfg(test)]
mod tests;
