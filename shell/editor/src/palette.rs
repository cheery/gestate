//! The command list, on screen — `spec/workbench.md`'s answer to modes.
//!
//! > There is one mode: you are typing.  Every other thing the editor
//! > can do is a command with a name, and there is a list of them you
//! > can open, filter and read.
//!
//! **It does not rank, and that is deliberate.**  Which commands a
//! query means — an exact name, then a prefix, then a substring, then
//! the summary — is a *decision*, and it already has a home in
//! `gestate/session.py`, lifted there from the reference browser that
//! went with `audiopygame`.  A second implementation here would be two
//! copies of one rule, which is the thing this project keeps refusing.
//! So the palette is handed its entries and shows them in the order it
//! was given.
//!
//! What it owns is the part that is genuinely the view's: what is
//! typed, what is selected, and where the list is drawn.

use gestate_panel::list::Colour;

use crate::keys::Key;
use crate::view::{Frame, Item};

/// One command, as the model describes it.
#[derive(Clone, PartialEq, Eq, Debug)]
pub struct Entry {
    /// With its arguments, ready to read — `loop <int> <int>`.
    pub usage: String,
    /// Just the name, which is what gets sent back.
    pub name: String,
    pub summary: String,
    /// The shortcut, or empty.
    pub key: String,
}

/// The palette's own colours — a panel over the text, not part of it.
pub const SHADE: Colour = Colour::rgb(0x0e, 0x10, 0x14);
pub const EDGE: Colour = Colour::rgb(0x2a, 0x30, 0x3a);
pub const INK: Colour = Colour::rgb(0xd8, 0xdc, 0xe4);
pub const FAINT: Colour = Colour::rgb(0x6a, 0x74, 0x84);
pub const PICKED: Colour = Colour::rgb(0x24, 0x3a, 0x4c);

/// What the palette wants next.
#[derive(Clone, PartialEq, Eq, Debug)]
pub enum Asks {
    /// Nothing — it is closed, or the key changed only what is shown.
    Nothing,
    /// The query changed; whoever supplies entries should re-filter.
    Filter(String),
    /// A command was chosen.
    Run(String),
    /// It closed without choosing.
    Closed,
}

#[derive(Default)]
pub struct Palette {
    open: bool,
    query: String,
    entries: Vec<Entry>,
    /// Which row is picked.  **Clamped rather than reset** when the
    /// list changes: typing one more letter usually narrows the list
    /// around what you were already looking at, and jumping the
    /// selection back to the top on every keystroke is how a filter
    /// becomes unusable.
    at: usize,
}

impl Palette {
    pub fn is_open(&self) -> bool {
        self.open
    }

    pub fn query(&self) -> &str {
        &self.query
    }

    pub fn entries(&self) -> &[Entry] {
        &self.entries
    }

    pub fn selected(&self) -> Option<&Entry> {
        self.entries.get(self.at)
    }

    /// Open it, empty — which shows everything, in the order the model
    /// declared them.  **Not alphabetically**: the file's order is the
    /// order somebody thought about them, which is a better order for
    /// learning than one the alphabet chose.
    pub fn show(&mut self) -> Asks {
        self.open = true;
        self.query.clear();
        self.at = 0;
        Asks::Filter(String::new())
    }

    pub fn hide(&mut self) -> Asks {
        self.open = false;
        self.query.clear();
        self.entries.clear();
        self.at = 0;
        Asks::Closed
    }

    /// The entries the model answered with.
    pub fn offer(&mut self, entries: Vec<Entry>) {
        self.entries = entries;
        self.at = self.at.min(self.entries.len().saturating_sub(1));
    }

    /// A key, while the palette is open.
    pub fn key(&mut self, key: Key) -> Asks {
        if !self.open {
            return Asks::Nothing;
        }
        match key {
            Key::Char(c) => {
                self.query.push(c);
                // Back to the top: a longer query is a different
                // question, and the best answer to it is first.
                self.at = 0;
                Asks::Filter(self.query.clone())
            }
            Key::Backspace => {
                if self.query.pop().is_none() {
                    // **Backspace on an empty query closes it**, which
                    // is what the key means everywhere else: undo the
                    // thing you just did, and the thing you just did
                    // was open this.
                    return self.hide();
                }
                self.at = 0;
                Asks::Filter(self.query.clone())
            }
            Key::Up => {
                self.at = self.at.saturating_sub(1);
                Asks::Nothing
            }
            Key::Down => {
                if self.at + 1 < self.entries.len() {
                    self.at += 1;
                }
                Asks::Nothing
            }
            Key::Enter => match self.selected() {
                None => Asks::Nothing,
                Some(e) => {
                    let name = e.name.clone();
                    self.hide();
                    Asks::Run(name)
                }
            },
            Key::Escape => self.hide(),
            _ => Asks::Nothing,
        }
    }

    /// How many rows to draw.
    fn rows(&self, h: i32, ch: i32) -> usize {
        (((h * 2 / 3) / ch.max(1)) as usize).clamp(1, 12)
    }

    /// The window the list is scrolled to, so the pick is always in it.
    fn window(&self, most: usize) -> usize {
        if self.at < most {
            0
        } else {
            self.at + 1 - most
        }
    }

    /// Draw it over whatever is behind.
    ///
    /// **Its own frame, painted after the text's**, rather than items
    /// appended to the text's frame — the palette is chrome over a
    /// document, and interleaving the two would make the document's
    /// layout depend on whether a list happened to be open.
    pub fn frame(&self, w: i32, h: i32, cw: i32, ch: i32) -> Frame {
        let mut f = Frame::default();
        if !self.open {
            return f;
        }
        let most = self.rows(h, ch);
        let shown = self.entries.len().min(most);
        let box_h = ch * (shown as i32 + 1) + 8;
        let box_w = (w - 2 * cw).max(cw);
        let (x, y) = (cw, ch);

        f.items.push(Item::Rect { x: x - 2, y: y - 2, w: box_w + 4,
                                  h: box_h + 4, c: EDGE });
        f.items.push(Item::Rect { x, y, w: box_w, h: box_h, c: SHADE });

        // What is typed, with a caret after it — the same shape the
        // seed field in the plugin panel uses, for the same reason: a
        // box you can type in should look like one.
        f.items.push(Item::Run { x: x + 4, y: y + 4,
                                 s: format!("> {}", self.query), c: INK });
        f.items.push(Item::Rect {
            x: x + 4 + (self.query.chars().count() as i32 + 2) * cw,
            y: y + 4, w: 2.max(cw / 5), h: ch, c: INK });

        let from = self.window(most);
        for (i, e) in self.entries.iter().skip(from).take(shown).enumerate() {
            let row = y + 4 + ch * (i as i32 + 1);
            if from + i == self.at {
                f.items.push(Item::Rect { x, y: row, w: box_w, h: ch,
                                          c: PICKED });
            }
            f.items.push(Item::Run { x: x + 4, y: row,
                                     s: e.usage.clone(), c: INK });
            // The key, hard against the right edge — reading the name
            // teaches the key and pressing the key teaches the name,
            // which only works if both are on the row.
            if !e.key.is_empty() {
                let at = x + box_w - 4 - e.key.chars().count() as i32 * cw;
                f.items.push(Item::Run { x: at, y: row, s: e.key.clone(),
                                         c: FAINT });
            }
        }

        // The summary of whatever is picked, under the list: one line,
        // because a list of twenty summaries is a wall and the one you
        // are looking at is the one you want.
        if let Some(e) = self.selected() {
            f.items.push(Item::Run { x: x + 4, y: y + box_h + 6,
                                     s: e.summary.clone(), c: FAINT });
        }
        f
    }
}
