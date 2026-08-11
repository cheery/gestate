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
    /// What it takes, as declared — `["Int", "Int"]` for `loop`.
    ///
    /// **The types are how the view knows to ask.**  A command with
    /// arguments cannot simply be run when it is picked; it has to
    /// collect them first, and how many and of what kind is a fact
    /// about the signature, not something to read out of a usage line.
    pub args: Vec<String>,
}

/// One thing an argument could be, as the model offers it.
#[derive(Clone, PartialEq, Eq, Debug, Default)]
pub struct Choice {
    pub text: String,
    /// What it is — `Chan Float`, `4 voices`.  Shown, never sent.
    pub note: String,
}

/// A command picked, waiting for what it takes.
#[derive(Clone, PartialEq, Eq, Debug, Default)]
pub struct Asking {
    pub verb: String,
    /// The declared types, so the prompt can say what it wants.
    pub types: Vec<String>,
    /// What has been collected so far.
    pub got: Vec<String>,
}

impl Asking {
    /// The type of the argument being collected.
    pub fn wants(&self) -> &str {
        self.types.get(self.got.len()).map(String::as_str).unwrap_or("")
    }

    /// `find <text>` with the part being typed marked.
    pub fn prompt(&self) -> String {
        let mut out = self.verb.clone();
        for (i, t) in self.types.iter().enumerate() {
            out.push(' ');
            if i < self.got.len() {
                out.push_str(&self.got[i]);
            } else {
                out.push_str(&format!("<{}>", t.to_lowercase()));
            }
        }
        out
    }
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
    /// A command was chosen, with everything it takes.
    Run(String, Vec<String>),
    /// A command was picked that takes arguments; this is the query so
    /// far for the one being collected.
    Wants(String, usize, String),
    /// It closed without choosing.
    Closed,
}

#[derive(Default)]
pub struct Palette {
    open: bool,
    query: String,
    entries: Vec<Entry>,
    /// The command whose arguments are being collected, if any.
    asking: Option<Asking>,
    /// What the model says this argument could be.
    choices: Vec<Choice>,
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
        self.choices.clear();
        self.asking = None;
        self.at = 0;
        Asks::Closed
    }

    /// Whether it is collecting a command's arguments.
    pub fn asking(&self) -> Option<&Asking> {
        self.asking.as_ref()
    }

    /// What the model says the argument being asked for could be.
    pub fn offer_choices(&mut self, choices: Vec<Choice>) {
        self.choices = choices;
        self.at = self.at.min(self.choices.len().saturating_sub(1));
    }

    /// Start collecting for the picked command, or run it now.
    fn take(&mut self, e: &Entry) -> Asks {
        if e.args.is_empty() {
            let name = e.name.clone();
            self.hide();
            return Asks::Run(name, Vec::new());
        }
        // **Picked is not run.**  A command that takes something has to
        // be given it, so picking one turns the list into a question
        // about its first argument rather than doing anything.
        self.asking = Some(Asking { verb: e.name.clone(),
                                    types: e.args.clone(),
                                    got: Vec::new() });
        self.query.clear();
        self.choices.clear();
        self.at = 0;
        Asks::Wants(e.name.clone(), 0, String::new())
    }

    /// Take what is typed or picked as the next argument.
    fn accept(&mut self) -> Asks {
        let Some(mut asking) = self.asking.take() else {
            return Asks::Nothing;
        };
        // A picked name beats what is typed, because picking one is how
        // you avoid typing it; an empty list means typing is all there
        // is, which is what a number or a piece of text always is.
        let given = match self.choices.get(self.at) {
            Some(c) if !c.text.is_empty() => c.text.clone(),
            _ => self.query.clone(),
        };
        if given.is_empty() {
            self.asking = Some(asking);
            return Asks::Nothing;
        }
        asking.got.push(given);
        if asking.got.len() >= asking.types.len() {
            let (verb, args) = (asking.verb.clone(), asking.got.clone());
            self.hide();
            return Asks::Run(verb, args);
        }
        let (verb, at) = (asking.verb.clone(), asking.got.len());
        self.asking = Some(asking);
        self.query.clear();
        self.choices.clear();
        self.at = 0;
        Asks::Wants(verb, at, String::new())
    }

    /// Step back one argument, or out of the question entirely.
    fn back(&mut self) -> Asks {
        let Some(mut asking) = self.asking.take() else {
            return self.hide();
        };
        self.query.clear();
        self.choices.clear();
        self.at = 0;
        match asking.got.pop() {
            None => {
                // **Back out of the question, not out of the list.**
                // Picking the wrong command is the ordinary mistake
                // here, and the fix for it is the list you came from.
                Asks::Filter(String::new())
            }
            Some(_) => {
                let (verb, at) = (asking.verb.clone(), asking.got.len());
                self.asking = Some(asking);
                Asks::Wants(verb, at, String::new())
            }
        }
    }

    /// The entries the model answered with.
    pub fn offer(&mut self, entries: Vec<Entry>) {
        self.entries = entries;
        self.at = self.at.min(self.entries.len().saturating_sub(1));
    }

    /// How many rows the list has, whichever list it is.
    fn shown_len(&self) -> usize {
        if self.asking.is_some() {
            self.choices.len()
        } else {
            self.entries.len()
        }
    }

    /// What a changed query means, in whichever mode.
    fn requery(&mut self) -> Asks {
        self.at = 0;
        match &self.asking {
            None => Asks::Filter(self.query.clone()),
            Some(a) => Asks::Wants(a.verb.clone(), a.got.len(),
                                   self.query.clone()),
        }
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
                self.requery()
            }
            Key::Backspace => {
                if self.query.pop().is_none() {
                    // **Backspace on an empty query goes back one
                    // step**, which is what the key means everywhere
                    // else: undo the thing you just did.  Collecting an
                    // argument, that is the argument before it; in the
                    // list, it is having opened the list.
                    return self.back();
                }
                self.requery()
            }
            Key::Up => {
                self.at = self.at.saturating_sub(1);
                Asks::Nothing
            }
            Key::Down => {
                if self.at + 1 < self.shown_len() {
                    self.at += 1;
                }
                Asks::Nothing
            }
            Key::Enter => {
                if self.asking.is_some() {
                    return self.accept();
                }
                match self.selected().cloned() {
                    None => Asks::Nothing,
                    Some(e) => self.take(&e),
                }
            }
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
        let shown = self.shown_len().min(most);
        // **The summary is a row of the panel, not a line beside it.**
        // It used to be drawn below the box, where there is no
        // background — so a sentence about the picked command was
        // painted straight over the file, two texts sharing one set of
        // pixels and neither readable.  A panel over a document has to
        // own every pixel it writes on, which means counting the
        // summary's row before the box is sized.
        let telling = self.asking.is_none() && self.selected().is_some();
        let rows = shown as i32 + 1 + i32::from(telling);
        let box_h = ch * rows + 8;
        let box_w = (w - 2 * cw).max(cw);
        let (x, y) = (cw, ch);

        f.items.push(Item::Rect { x: x - 2, y: y - 2, w: box_w + 4,
                                  h: box_h + 4, c: EDGE });
        f.items.push(Item::Rect { x, y, w: box_w, h: box_h, c: SHADE });

        // What is typed, with a caret after it — the same shape the
        // seed field in the plugin panel uses, for the same reason: a
        // box you can type in should look like one.
        //
        // **While an argument is being collected the prompt says which
        // one**, with what has already been given standing where its
        // placeholder was: `loop 4 <int>` is a better question than a
        // bare caret, and it is the same words the list showed.
        let lead = match &self.asking {
            None => "> ".to_string(),
            Some(a) => format!("{} ", a.prompt()),
        };
        f.items.push(Item::Run { x: x + 4, y: y + 4,
                                 s: format!("{lead}{}", self.query),
                                 c: INK });
        f.items.push(Item::Rect {
            x: x + 4
                + (lead.chars().count() + self.query.chars().count()) as i32
                    * cw,
            y: y + 4, w: 2.max(cw / 5), h: ch, c: INK });

        // One row shape, two lists: a command with its shortcut, or a
        // name with what it is.  Both are "a thing on the left and a
        // note on the right", so they are drawn by the same code.
        let rows: Vec<(String, String)> = match &self.asking {
            None => self.entries.iter()
                .map(|e| (e.usage.clone(), e.key.clone())).collect(),
            Some(_) => self.choices.iter()
                .map(|c| (c.text.clone(), c.note.clone())).collect(),
        };
        let from = self.window(most);
        for (i, (left, right)) in
            rows.iter().skip(from).take(shown).enumerate()
        {
            let row = y + 4 + ch * (i as i32 + 1);
            if from + i == self.at {
                f.items.push(Item::Rect { x, y: row, w: box_w, h: ch,
                                          c: PICKED });
            }
            let room = (((box_w - 8) / cw.max(1)) as usize)
                .saturating_sub(right.chars().count() + 2).max(4);
            f.items.push(Item::Run { x: x + 4, y: row,
                                     s: elide(left, room), c: INK });
            // The note, hard against the right edge — reading the name
            // teaches the key and pressing the key teaches the name,
            // which only works if both are on the row.
            if !right.is_empty() {
                let at = x + box_w - 4 - right.chars().count() as i32 * cw;
                f.items.push(Item::Run { x: at, y: row, s: right.clone(),
                                         c: FAINT });
            }
        }

        // The summary of whatever is picked, on the last row: one line,
        // because a list of twenty summaries is a wall and the one you
        // are looking at is the one you want.
        if let (None, Some(e)) = (&self.asking, self.selected()) {
            // **Elided to the room there is**, and here rather than in
            // the model: how much fits is a fact about this window's
            // width, which the model has no business knowing.
            let room = (((box_w - 8) / cw.max(1)).max(4)) as usize;
            let row = y + 4 + ch * (shown as i32 + 1);
            f.items.push(Item::Run { x: x + 4, y: row,
                                     s: elide(&e.summary, room), c: FAINT });
        }
        f
    }
}

/// Cut to `most` characters, with an ellipsis when something was cut.
///
/// A row that runs under the one beside it is worse than a row that
/// says it has more to say.
fn elide(text: &str, most: usize) -> String {
    if text.chars().count() <= most {
        return text.to_string();
    }
    text.chars().take(most.saturating_sub(1)).collect::<String>() + "…"
}

#[cfg(test)]
mod paint_tests {
    use super::*;
    use crate::view::Item;

    fn a_palette() -> Palette {
        let mut p = Palette::default();
        p.show();
        p.offer(vec![
            Entry { usage: "loop <int> <int>".into(), name: "loop".into(),
                    summary: "Play a stretch of bars over and over.".into(),
                    key: String::new(),
                    args: vec!["Int".into(), "Int".into()] },
            Entry { usage: "stop".into(), name: "stop".into(),
                    summary: "Stop the transport where it is.".into(),
                    key: "^.".into(), args: Vec::new() },
        ]);
        p
    }

    /// Every glyph the palette draws must have palette behind it.
    ///
    /// The summary used to be drawn *below* the panel, over the file —
    /// two texts in one set of pixels, and neither readable.  A panel
    /// over a document owns every pixel it writes on.
    #[test]
    fn nothing_is_drawn_outside_the_panel() {
        let (cw, ch) = (8, 16);
        let f = a_palette().frame(800, 600, cw, ch);
        // The shade is the second item; the border is the first.
        let (top, bottom) = match f.items[1] {
            Item::Rect { y, h, .. } => (y, y + h),
            ref other => panic!("expected the panel's shade, got {other:?}"),
        };
        for item in &f.items {
            if let Item::Run { y, s, .. } = item {
                assert!(*y >= top && *y + ch <= bottom,
                        "{s:?} is drawn at {y}, outside the panel \
                         ({top}..{bottom})");
            }
        }
    }

    #[test]
    fn the_summary_of_the_picked_command_is_shown() {
        let f = a_palette().frame(800, 600, 8, 16);
        let said: Vec<&String> = f.items.iter().filter_map(|i| match i {
            Item::Run { s, .. } => Some(s),
            _ => None,
        }).collect();
        assert!(said.iter().any(|s| s.starts_with("Play a stretch")),
                "no summary among {said:?}");
    }
}

#[cfg(test)]
mod asking_tests {
    use super::*;

    fn listed() -> Palette {
        let mut p = Palette::default();
        p.show();
        p.offer(vec![
            Entry { usage: "stop".into(), name: "stop".into(),
                    summary: "Stop.".into(), key: String::new(),
                    args: Vec::new() },
            Entry { usage: "loop <int> <int>".into(), name: "loop".into(),
                    summary: "Loop.".into(), key: String::new(),
                    args: vec!["Int".into(), "Int".into()] },
            Entry { usage: "listen <named>".into(), name: "listen".into(),
                    summary: "Listen.".into(), key: String::new(),
                    args: vec!["Named".into()] },
        ]);
        p
    }

    fn pick(p: &mut Palette, row: usize) -> Asks {
        p.at = row;
        p.key(Key::Enter)
    }

    #[test]
    fn a_command_that_takes_nothing_runs_when_picked() {
        let mut p = listed();
        assert_eq!(pick(&mut p, 0), Asks::Run("stop".into(), Vec::new()));
        assert!(!p.is_open());
    }

    /// **Picked is not run.**  A command with arguments turns the list
    /// into a question about the first of them.
    #[test]
    fn a_command_that_takes_arguments_asks_for_them() {
        let mut p = listed();
        assert_eq!(pick(&mut p, 1), Asks::Wants("loop".into(), 0, "".into()));
        assert!(p.is_open());
        assert_eq!(p.asking().unwrap().prompt(), "loop <int> <int>");

        for c in "4".chars() {
            assert_eq!(p.key(Key::Char(c)),
                       Asks::Wants("loop".into(), 0, "4".into()));
        }
        // The first argument taken, the prompt now shows it in place.
        assert_eq!(p.key(Key::Enter), Asks::Wants("loop".into(), 1, "".into()));
        assert_eq!(p.asking().unwrap().prompt(), "loop 4 <int>");
        p.key(Key::Char('8'));
        assert_eq!(p.key(Key::Enter),
                   Asks::Run("loop".into(), vec!["4".into(), "8".into()]));
        assert!(!p.is_open(), "running it closes the list");
    }

    /// A name is *picked*, which is the point of offering names at all.
    #[test]
    fn a_named_argument_can_be_chosen_from_the_list() {
        let mut p = listed();
        pick(&mut p, 2);
        p.offer_choices(vec![
            Choice { text: "cutoff".into(), note: "Chan Float".into() },
            Choice { text: "pitch".into(), note: "Chan Int".into() },
        ]);
        p.at = 1;
        assert_eq!(p.key(Key::Enter),
                   Asks::Run("listen".into(), vec!["pitch".into()]));
    }

    /// Typed beats nothing offered — a number has no list to pick from.
    #[test]
    fn nothing_offered_means_what_was_typed() {
        let mut p = listed();
        pick(&mut p, 1);
        p.key(Key::Char('2'));
        assert_eq!(p.key(Key::Enter), Asks::Wants("loop".into(), 1, "".into()));
        assert_eq!(p.asking().unwrap().got, vec!["2".to_string()]);
    }

    /// Enter with nothing to give asks again rather than running a
    /// command with a blank where an argument goes.
    #[test]
    fn an_empty_argument_is_not_taken() {
        let mut p = listed();
        pick(&mut p, 1);
        assert_eq!(p.key(Key::Enter), Asks::Nothing);
        assert!(p.asking().is_some());
    }

    /// Backspace steps back through the question, then out of it — the
    /// ordinary mistake is picking the wrong command, and the fix for
    /// it is the list you came from.
    #[test]
    fn backspace_walks_back_out_of_the_question() {
        let mut p = listed();
        pick(&mut p, 1);
        p.key(Key::Char('4'));
        p.key(Key::Enter);
        assert_eq!(p.asking().unwrap().got.len(), 1);
        assert_eq!(p.key(Key::Backspace),
                   Asks::Wants("loop".into(), 0, "".into()));
        assert_eq!(p.asking().unwrap().got.len(), 0);
        assert_eq!(p.key(Key::Backspace), Asks::Filter(String::new()));
        assert!(p.asking().is_none());
        assert!(p.is_open(), "back to the list, not out of it");
    }
}
