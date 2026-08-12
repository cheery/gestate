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
    /// The command that runs it the other way, or empty.
    ///
    /// **Read, never decided.**  That `find` runs backwards as
    /// `findBack` is a fact about what those two do, and it is handed
    /// over with the key and the argument types — a view that knew it
    /// would be a second vocabulary, which is the thing the list exists
    /// to prevent.
    pub reverse: String,
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
    /// **What choosing it makes the query, if it is a step.**
    ///
    /// A directory is a step, not an answer: picking one moves the
    /// query into it and asks again — which is what a file dialog does,
    /// and what makes walking down and back up feel like walking.
    /// Empty for a row that *is* the answer.
    ///
    /// The whole query, computed by the model, because it is path
    /// arithmetic and the view has no business doing any.
    pub step: String,
    /// **Whether it may be chosen at all.**
    ///
    /// A name already taken is shown and not offered: you cannot choose
    /// what you cannot have, and hiding it would be worse — the reason
    /// the name is refused is that it is *there*, so it has to be
    /// visible for the refusal to read.
    pub can: bool,
    /// **Whether it is drawn faint** — which is not the same question.
    ///
    /// `steal` refuses a taken name and greys it, so the two moved
    /// together and one flag served both.  An export overwrites: the
    /// name being taken is still worth *seeing* — it is the difference
    /// between writing a new file and replacing one — but it is no
    /// longer a refusal.  So the look and the refusal are two fields,
    /// and a row can be one without the other.
    pub dim: bool,
    /// **The one you are already on**, if any.
    ///
    /// Marked rather than selected: the cursor goes there and the query
    /// stays blank, so the list opens showing where you are and the
    /// first letter you type is a new name rather than an edit of the
    /// old one.
    pub here: bool,
}

/// A command picked, waiting for what it takes.
#[derive(Clone, PartialEq, Eq, Debug, Default)]
pub struct Asking {
    pub verb: String,
    /// The declared types, so the prompt can say what it wants.
    pub types: Vec<String>,
    /// What has been collected so far.
    pub got: Vec<String>,
    /// The command that runs it the other way, or empty.
    pub reverse: String,
    /// Whether it has everything and has already run once.
    ///
    /// **So that Return means *again*.**  `find foo` is not one act but
    /// a walk: you press Return to reach the next one, and if the list
    /// had closed on the first match, Return would be a newline in the
    /// document instead.  Keeping the question open is what gives the
    /// key somewhere to land — and typing takes the argument back, so
    /// leaving is exactly as easy as staying.
    pub done: bool,
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
    /// A page to read, under the list.
    page: Vec<String>,
    /// Which row is picked.  **Clamped rather than reset** when the
    /// list changes: typing one more letter usually narrows the list
    /// around what you were already looking at, and jumping the
    /// selection back to the top on every keystroke is how a filter
    /// becomes unusable.
    at: usize,
    /// How many cells the symbol grid last drew across.
    ///
    /// **Set by the layout, read by the arrows.**  `Down` means *a row
    /// down* and a row is however many cells fitted, which only the
    /// drawing knows — so it leaves the number here rather than the keys
    /// guessing at a shape they cannot see.
    wide: std::cell::Cell<i32>,
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
        // **And nothing of the last question survives it.**  Opening
        // the list without clearing this left it still holding a
        // finished call — so it looked like a list of commands while
        // Backspace and the arrows still meant *search backwards*, and
        // backspace stopped backspacing.  `hide` cleared all of it and
        // `show` cleared none, which is one of those pairs that has to
        // be read together to notice.
        self.asking = None;
        self.choices.clear();
        self.page.clear();
        self.at = 0;
        Asks::Filter(String::new())
    }

    /// Put `text` in the question being asked, as if it had been typed.
    ///
    /// **Only while something is being asked**, and only into the
    /// argument still open: filling the *command* filter would move the
    /// selection under a hand that was choosing, and filling a finished
    /// call would be answering a question nobody asked.  `Asks::Nothing`
    /// when there is no question, so the caller can say so.
    pub fn fill(&mut self, text: &str) -> Asks {
        let Some(asking) = self.asking.as_ref() else {
            return Asks::Nothing;
        };
        if asking.done {
            return Asks::Nothing;
        }
        let (verb, at) = (asking.verb.clone(), asking.got.len());
        self.query = text.to_string();
        self.choices.clear();
        self.at = 0;
        Asks::Wants(verb, at, self.query.clone())
    }

    pub fn hide(&mut self) -> Asks {
        self.open = false;
        self.query.clear();
        self.entries.clear();
        self.choices.clear();
        self.page.clear();
        self.asking = None;
        self.at = 0;
        Asks::Closed
    }

    /// Whether it is collecting a command's arguments.
    pub fn asking(&self) -> Option<&Asking> {
        self.asking.as_ref()
    }

    /// What the model says the argument being asked for could be.
    /// A page the model wants read — `what`'s answer, in full.
    ///
    /// **Under the list, not in the status line.**  One sentence is the
    /// right size for *what just happened*; a signature, where it comes
    /// from and what it is for is a paragraph, and folding that into
    /// the foot of the window is the same as hiding it.
    pub fn offer_page(&mut self, page: Vec<String>) {
        self.page = page;
    }

    pub fn offer_choices(&mut self, choices: Vec<Choice>) {
        let fresh = self.choices.is_empty() && !choices.is_empty();
        self.choices = choices;
        // Only on the way in, and only while nothing is typed: once a
        // query narrows the list, where the cursor goes is the
        // ranking's business.
        if fresh && self.query.is_empty() {
            if let Some(at) = self.choices.iter().position(|c| c.here) {
                self.at = at;
            }
        }
        self.clamp();
    }

    /// Keep the pick inside **the list being shown**.
    ///
    /// Against `shown_len`, never against one of the two lists on its
    /// own.  Clamping the pick to the *choices* while the commands are
    /// what is on screen pins it to zero — there are no choices unless
    /// an argument is being asked for — and because the description
    /// arrives many times a second while the transport runs, the effect
    /// was a list you could not move down: every arrow key was undone
    /// before the next frame.
    fn clamp(&mut self) {
        let n = self.shown_len();
        self.at = if n == 0 { 0 } else { self.at.min(n - 1) };
    }

    /// Start collecting for a command, or run it now — from a shortcut
    /// as well as from the list, so both reach it the same way.
    pub fn begin(&mut self, e: &Entry) -> Asks {
        if !e.args.is_empty() {
            self.open = true;
        }
        self.take(e)
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
                                    reverse: e.reverse.clone(),
                                    got: Vec::new(), done: false });
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
            // A row that may not be chosen is not chosen, and Enter
            // does nothing rather than quietly taking what was typed —
            // which would be the refusal failing open.
            Some(c) if !c.can => {
                self.asking = Some(asking);
                return Asks::Nothing;
            }
            // A step moves the question along instead of answering it.
            Some(c) if !c.step.is_empty() => {
                let (verb, at) = (asking.verb.clone(), asking.got.len());
                self.query = c.step.clone();
                self.choices.clear();
                self.at = 0;
                self.asking = Some(asking);
                return Asks::Wants(verb, at, self.query.clone());
            }
            Some(c) if !c.text.is_empty() => c.text.clone(),
            _ => self.query.clone(),
        };
        if given.is_empty() {
            self.asking = Some(asking);
            return Asks::Nothing;
        }
        asking.got.push(given);
        if asking.got.len() >= asking.types.len() {
            // **Complete, and still open.**  See `Asking::done`.
            let (verb, args) = (asking.verb.clone(), asking.got.clone());
            asking.done = true;
            self.asking = Some(asking);
            self.query.clear();
            self.choices.clear();
            self.at = 0;
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
        if asking.done {
            asking.done = false;
        }
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
        self.clamp();
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
            // **A space moves on, because that is how a command line
            // reads.**  `find foo` is what a person types; making them
            // press Return between the name and the argument is asking
            // them to know a rule the line does not show.  So a space
            // does what Return does — picks the command, or takes the
            // argument and asks for the next.
            //
            // *Except in `Text`*, where a space is content: `find foo
            // bar` has to be able to look for two words.  A command
            // name never contains one, so nothing is lost in the list.
            Key::Char(' ') if self.asking.is_none() => {
                match self.selected().cloned() {
                    Some(e) if !e.args.is_empty() => self.take(&e),
                    _ => Asks::Nothing,
                }
            }
            Key::Char(' ')
                if self.asking.as_ref().map(|a| a.wants()) != Some("Text")
                    && !self.query.is_empty() =>
            {
                self.accept()
            }
            Key::Char(c) => {
                // **Typing takes the last argument back.**  It is how a
                // finished call is left: you are asking a new question
                // of the same command, which is what typing over an
                // answer means everywhere else.
                if self.asking.as_ref().is_some_and(|a| a.done) {
                    if let Some(a) = self.asking.as_mut() {
                        a.done = false;
                        a.got.pop();
                    }
                    self.query.clear();
                    self.choices.clear();
                    self.at = 0;
                }
                self.query.push(c);
                // Back to the top: a longer query is a different
                // question, and the best answer to it is first.
                self.requery()
            }
            // **The arrows walk a finished call.**  A search is a walk
            // in two directions and the keys for "the next one" and
            // "the one before" are the same everywhere; while a call is
            // live they mean that, and there is no list to move in
            // anyway.
            //
            // **Backspace is not one of them.**  It was, briefly, and
            // it was wrong: backspace means *undo the last keystroke*
            // everywhere in this editor, and a key that deletes in one
            // breath and searches in the next is a key you have to stop
            // and think about. So it goes back to editing the argument,
            // which is what it does in every other state of this list.
            Key::Up if self.asking.as_ref().is_some_and(|a| a.done) => {
                self.step(true)
            }
            Key::Down if self.asking.as_ref().is_some_and(|a| a.done) => {
                self.step(false)
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
            // **Up and down mean a row, and in a grid a row is wide.**
            // Stepping one cell would make the arrows agree with the
            // sequence and disagree with the picture, which is the one
            // thing a table must not do.
            Key::Up => {
                self.at = self.at.saturating_sub(self.stride());
                Asks::Nothing
            }
            Key::Down => {
                let to = self.at + self.stride();
                if to < self.shown_len() {
                    self.at = to;
                }
                Asks::Nothing
            }
            // And left and right are the cells themselves — bound only
            // where there is a grid, so a list keeps them for whatever
            // else may want them.
            Key::Left if self.is_grid() => {
                self.at = self.at.saturating_sub(1);
                Asks::Nothing
            }
            Key::Right if self.is_grid() => {
                if self.at + 1 < self.shown_len() {
                    self.at += 1;
                }
                Asks::Nothing
            }
            Key::Enter => {
                if let Some(a) = &self.asking {
                    if a.done {
                        // Again — the next match, the next take.
                        return Asks::Run(a.verb.clone(), a.got.clone());
                    }
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

    /// Which row the pointer is over, if it is over one.
    ///
    /// **The inverse of `frame`, in the same file and from the same
    /// numbers** — a list drawn by one arithmetic and clicked by
    /// another answers somewhere other than where it is drawn, which is
    /// the bug that makes a menu feel haunted.  `view::knob_hit` sits
    /// beside its trough for the same reason.
    pub fn row_at(&self, w: i32, h: i32, cw: i32, ch: i32, x: i32, y: i32)
        -> Option<usize>
    {
        if !self.open {
            return None;
        }
        let most = self.rows(h, ch);
        let shown = self.shown_len().min(most);
        let box_w = (w - 2 * cw).max(cw);
        let (bx, by) = (cw, ch);
        if x < bx || x > bx + box_w {
            return None;
        }
        // The query is the first row and picks nothing; the list starts
        // below it.
        let from = self.window(most);
        let top = by + 4 + ch;
        if y < top {
            return None;
        }
        let row = ((y - top) / ch.max(1)) as usize;
        if row >= shown {
            return None;
        }
        Some(from + row)
    }

    /// Pick the row the pointer is over, and do what Enter does to it.
    ///
    /// **A click is Enter somewhere else.**  Two ways to reach a
    /// command that behaved differently would be two vocabularies, and
    /// the list exists to prevent exactly that — so this moves the pick
    /// and then takes the same path.
    pub fn click(&mut self, at: usize) -> Asks {
        if at >= self.shown_len() {
            return Asks::Nothing;
        }
        self.at = at;
        if self.asking.is_some() {
            return self.accept();
        }
        match self.selected().cloned() {
            None => Asks::Nothing,
            Some(e) => self.take(&e),
        }
    }

    /// Run a finished call again, forwards or back.
    ///
    /// Backwards is a *different command* — the model said which — so
    /// the question becomes that command's, and the arrows keep walking
    /// from wherever they leave you.  A call with no reverse simply
    /// repeats, which is what one direction means.
    fn step(&self, back: bool) -> Asks {
        let Some(a) = self.asking.as_ref() else {
            return Asks::Nothing;
        };
        // **Chosen, not toggled.**  Swapping the pair would make a
        // second press of the same arrow go the other way, so holding
        // Up would walk back and forth over two matches for ever.  The
        // key names the direction; the pair names the two commands.
        let verb = if back && !a.reverse.is_empty() {
            a.reverse.clone()
        } else {
            a.verb.clone()
        };
        Asks::Run(verb, a.got.clone())
    }

    /// Scroll the list by whole rows.
    pub fn scroll(&mut self, by: i32) {
        let n = self.shown_len();
        if n == 0 {
            return;
        }
        let at = (self.at as i32 + by).clamp(0, n as i32 - 1);
        self.at = at as usize;
    }

    /// Draw it over whatever is behind.
    ///
    /// **Its own frame, painted after the text's**, rather than items
    /// appended to the text's frame — the palette is chrome over a
    /// document, and interleaving the two would make the document's
    /// layout depend on whether a list happened to be open.
    /// The symbol table, as a table.
    ///
    /// **Cells across, not rows down.**  Each is `a >` — the key that
    /// reaches it and the character it types — so reading the grid
    /// teaches the keys and pressing one teaches the grid.  The
    /// selection is drawn on the cell rather than the row, which is what
    /// makes the arrows mean left and right as well as up and down.
    ///
    /// Laid out by the width there is: one column per `CELL` characters,
    /// at least one, so a narrow window degenerates to the column this
    /// replaced rather than to nothing.
    /// How many cells fit across — **one rule, two readers.**  The
    /// layout and the arrow keys have to agree about the shape of the
    /// grid or `Down` moves somewhere other than down.
    /// Whether what is being asked for is drawn as a table.
    fn is_grid(&self) -> bool {
        self.asking.as_ref().map(|a| a.wants()) == Some("Symbol")
    }

    /// How far `Down` moves — a whole row in a grid, one row in a list.
    fn stride(&self) -> usize {
        if self.is_grid() {
            self.wide.get().max(1) as usize
        } else {
            1
        }
    }

    fn columns(box_w: i32, cw: i32) -> i32 {
        const CELL: i32 = 6;                    // "a >  " and air
        ((box_w - 8) / (CELL * cw).max(1)).max(1)
    }

    fn grid(&self, f: &mut Frame, rows: &[(String, String)],
            x: i32, y: i32, cw: i32, ch: i32, box_w: i32) {
        const CELL: i32 = 6;
        let per = Self::columns(box_w, cw);
        self.wide.set(per);
        for (i, (letter, glyph)) in rows.iter().enumerate() {
            let (col, line) = (i as i32 % per, i as i32 / per);
            let cx = x + 4 + col * CELL * cw;
            let cy = y + 4 + ch * (line + 1);
            if i == self.at {
                f.items.push(Item::Rect { x: cx - 2, y: cy,
                                          w: CELL * cw, h: ch, c: PICKED });
            }
            f.items.push(Item::Run { x: cx, y: cy, s: letter.clone(),
                                     c: FAINT });
            f.items.push(Item::Run {
                x: cx + 2 * cw, y: cy, s: glyph.clone(), c: INK });
        }
    }

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
        let box_w = (w - 2 * cw).max(cw);
        // **A grid is as tall as its own lines**, not as tall as the
        // list it replaced: a table of twenty-two symbols four rows deep
        // in a panel sized for twelve rows is ten rows of nothing over
        // somebody's file.
        let grid = self.asking.as_ref().map(|a| a.wants()) == Some("Symbol");
        let rows = if grid {
            let per = Self::columns(box_w, cw);
            (self.choices.len() as i32 + per - 1) / per.max(1) + 1
        } else {
            shown as i32 + 1 + i32::from(telling)
        };
        let box_h = ch * rows + 8;
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
        // Which of those rows are only to be read.
        let dim: Vec<bool> = match &self.asking {
            None => vec![false; rows.len()],
            Some(_) => self.choices.iter().map(|c| c.dim || !c.can).collect(),
        };
        // **A keyboard is a grid, and so is this.**  A symbol table read
        // as one column is a column you scroll, which is exactly the
        // thing a person reaches for it to avoid — and the letters only
        // pay for themselves when you can see where each one lands.
        if grid {
            self.grid(&mut f, &rows, x, y, cw, ch, box_w);
            return f;
        }
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
            f.items.push(Item::Run {
                x: x + 4, y: row, s: elide(left, room),
                c: if dim.get(from + i).copied().unwrap_or(false) {
                    FAINT
                } else {
                    INK
                } });
            // The note, hard against the right edge — reading the name
            // teaches the key and pressing the key teaches the name,
            // which only works if both are on the row.
            if !right.is_empty() {
                let at = x + box_w - 4 - right.chars().count() as i32 * cw;
                f.items.push(Item::Run { x: at, y: row, s: right.clone(),
                                         c: FAINT });
            }
        }

        // The page, under the panel and in its own — as many lines as
        // it has, which is why it is not the summary's single row.
        if !self.page.is_empty() {
            let room = (((box_w - 8) / cw.max(1)).max(4)) as usize;
            let tall = ch * self.page.len() as i32 + 8;
            let py = y + box_h + 6;
            f.items.push(Item::Rect { x: x - 2, y: py - 2, w: box_w + 4,
                                      h: tall + 4, c: EDGE });
            f.items.push(Item::Rect { x, y: py, w: box_w, h: tall,
                                      c: SHADE });
            for (i, line) in self.page.iter().enumerate() {
                f.items.push(Item::Run {
                    x: x + 4, y: py + 4 + ch * i as i32,
                    s: elide(line, room),
                    c: if i == 0 { INK } else { FAINT } });
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
                    args: vec!["Int".into(), "Int".into()], reverse: String::new() },
            Entry { usage: "stop".into(), name: "stop".into(),
                    summary: "Stop the transport where it is.".into(),
                    key: "^.".into(), args: Vec::new(), reverse: String::new() },
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

    /// A palette part-way through asking for a `Symbol`.
    fn a_grid() -> Palette {
        let mut p = Palette::default();
        p.show();
        p.asking = Some(Asking {
            verb: "symbol".into(), types: vec!["Symbol".into()],
            got: vec![], reverse: String::new(), done: false,
        });
        p.offer_choices(vec![
            Choice { text: "a".into(), note: ">".into(), can: true,
                     ..Default::default() },
            Choice { text: "b".into(), note: "<".into(), can: true,
                     ..Default::default() },
            Choice { text: "c".into(), note: "|".into(), can: true,
                     ..Default::default() },
            Choice { text: "d".into(), note: "\\".into(), can: true,
                     ..Default::default() },
        ]);
        p
    }

    /// **A keyboard is a grid, and so is this.**  Cells go across before
    /// they go down — a symbol table read as one column is the column
    /// somebody opened it to avoid.
    #[test]
    fn the_symbol_table_is_laid_out_across() {
        let (cw, ch) = (8, 16);
        let f = a_grid().frame(800, 600, cw, ch);
        let glyphs: Vec<(i32, i32, &str)> = f.items.iter().filter_map(|i| {
            match i {
                Item::Run { x, y, s, .. } if s.len() <= 2 && s != "a"
                    && s != "b" && s != "c" && s != "d" =>
                    Some((*x, *y, s.as_str())),
                _ => None,
            }
        }).collect();
        assert!(glyphs.len() >= 4, "not every cell drew: {glyphs:?}");
        // All four on one line, at rising x — across, not down.
        let row = glyphs[0].1;
        assert!(glyphs.iter().all(|g| g.1 == row),
                "cells wrapped when they had room: {glyphs:?}");
        for pair in glyphs.windows(2) {
            assert!(pair[1].0 > pair[0].0, "cells not left to right");
        }
    }

    /// **Down means a row, and in a grid a row is wide.**  Stepping one
    /// cell would make the arrows agree with the sequence and disagree
    /// with the picture, which is the one thing a table must not do.
    #[test]
    fn down_in_a_grid_moves_a_whole_row() {
        let mut p = a_grid();
        p.frame(800, 600, 8, 16);            // the layout sets the width
        let wide = p.wide.get() as usize;
        assert!(wide > 1, "the test window fits only one column");
        p.key(Key::Right);
        assert_eq!(p.at, 1, "right did not move a cell");
        p.key(Key::Left);
        assert_eq!(p.at, 0);
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
                    args: Vec::new(), reverse: String::new() },
            Entry { usage: "loop <int> <int>".into(), name: "loop".into(),
                    summary: "Loop.".into(), key: String::new(),
                    args: vec!["Int".into(), "Int".into()], reverse: String::new() },
            Entry { usage: "listen <named>".into(), name: "listen".into(),
                    summary: "Listen.".into(), key: String::new(),
                    args: vec!["Named".into()], reverse: String::new() },
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
        // **It stays open, holding the finished call.**  Return means
        // *again* from here — see `Asking::done`.  Escape is the way
        // out, and typing is the way to ask a new one.
        assert!(p.is_open());
        assert!(p.asking().is_some_and(|a| a.done));
        assert_eq!(p.asking().unwrap().prompt(), "loop 4 8");
    }

    /// A name is *picked*, which is the point of offering names at all.
    #[test]
    fn a_named_argument_can_be_chosen_from_the_list() {
        let mut p = listed();
        pick(&mut p, 2);
        p.offer_choices(vec![
            Choice { text: "cutoff".into(), note: "Chan Float".into(), here: false, can: true, step: String::new(), dim: false },
            Choice { text: "pitch".into(), note: "Chan Int".into(), here: false, can: true, step: String::new(), dim: false },
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

#[cfg(test)]
mod space_tests {
    use super::*;

    fn listed() -> Palette {
        let mut p = Palette::default();
        p.show();
        p.offer(vec![
            Entry { usage: "find <text>".into(), name: "find".into(),
                    summary: "Find.".into(), key: String::new(),
                    args: vec!["Text".into()], reverse: String::new() },
            Entry { usage: "loop <int> <int>".into(), name: "loop".into(),
                    summary: "Loop.".into(), key: String::new(),
                    args: vec!["Int".into(), "Int".into()], reverse: String::new() },
            Entry { usage: "stop".into(), name: "stop".into(),
                    summary: "Stop.".into(), key: String::new(),
                    args: Vec::new(), reverse: String::new() },
        ]);
        p
    }

    fn typing(p: &mut Palette, text: &str) -> Asks {
        let mut last = Asks::Nothing;
        for c in text.chars() {
            last = p.key(Key::Char(c));
        }
        last
    }

    /// `find foo` then Return — one line, the way a command line reads.
    #[test]
    fn a_space_moves_from_the_name_to_the_argument() {
        let mut p = listed();
        p.at = 0;
        typing(&mut p, " ");
        assert_eq!(p.asking().map(|a| a.verb.as_str()), Some("find"));
        typing(&mut p, "foo");
        assert_eq!(p.key(Key::Enter),
                   Asks::Run("find".into(), vec!["foo".into()]));
    }

    /// `loop 2 6` in one line: a space between each.
    #[test]
    fn spaces_walk_through_several_arguments() {
        let mut p = listed();
        p.at = 1;
        typing(&mut p, " 2 6");
        assert_eq!(p.asking().unwrap().got, vec!["2".to_string()]);
        assert_eq!(p.key(Key::Enter),
                   Asks::Run("loop".into(), vec!["2".into(), "6".into()]));
    }

    /// **A space is content in `Text`.**  `find foo bar` must be able to
    /// look for two words.
    #[test]
    fn a_space_inside_text_is_typed_not_obeyed() {
        let mut p = listed();
        p.at = 0;
        typing(&mut p, " foo bar");
        assert_eq!(p.query(), "foo bar");
        assert_eq!(p.key(Key::Enter),
                   Asks::Run("find".into(), vec!["foo bar".into()]));
    }

    /// A command name never contains a space, so one in the list means
    /// nothing rather than filtering to nothing.
    #[test]
    fn a_space_does_nothing_for_a_command_that_takes_nothing() {
        let mut p = listed();
        p.at = 2;
        assert_eq!(p.key(Key::Char(' ')), Asks::Nothing);
        assert_eq!(p.query(), "");
        assert!(p.asking().is_none());
    }
}

#[cfg(test)]
mod picking_tests {
    use super::*;

    fn listed() -> Palette {
        let mut p = Palette::default();
        p.show();
        p.offer(vec![
            Entry { usage: "one".into(), name: "one".into(),
                    summary: String::new(), key: String::new(),
                    args: Vec::new(), reverse: String::new() },
            Entry { usage: "two".into(), name: "two".into(),
                    summary: String::new(), key: String::new(),
                    args: Vec::new(), reverse: String::new() },
            Entry { usage: "three".into(), name: "three".into(),
                    summary: String::new(), key: String::new(),
                    args: Vec::new(), reverse: String::new() },
        ]);
        p
    }

    /// **The pick survives a description.**  One arrives many times a
    /// second while the transport runs — the beat is in it — so a pick
    /// that did not survive one could not be moved at all: every arrow
    /// key was undone before the next frame.
    #[test]
    fn moving_down_the_list_survives_the_model_talking() {
        let mut p = listed();
        p.key(Key::Down);
        p.key(Key::Down);
        assert_eq!(p.at, 2);
        p.offer_choices(Vec::new());          // no argument is being asked
        assert_eq!(p.at, 2, "the pick was dragged back to the top");
        p.offer(p.entries().to_vec());        // the same list again
        assert_eq!(p.at, 2);
    }

    #[test]
    fn the_pick_stays_inside_a_list_that_shrank() {
        let mut p = listed();
        p.key(Key::Down);
        p.key(Key::Down);
        p.offer(vec![Entry { usage: "one".into(), name: "one".into(),
                             summary: String::new(), key: String::new(),
                             args: Vec::new(), reverse: String::new() }]);
        assert_eq!(p.at, 0);
    }
}

#[cfg(test)]
mod again_tests {
    use super::*;

    fn finding() -> Palette {
        let mut p = Palette::default();
        p.show();
        p.offer(vec![
            Entry { usage: "find <text>".into(), name: "find".into(),
                    summary: "Find.".into(), key: "Ctrl-F".into(),
                    args: vec!["Text".into()],
                    reverse: "findBack".into() },
        ]);
        p.at = 0;
        p.key(Key::Char(' '));                 // into the argument
        for c in "foo".chars() { p.key(Key::Char(c)); }
        p
    }

    /// **Return means again.**  `find foo` is a walk, not one act — and
    /// if the list closed on the first match, Return would be a newline
    /// in the document instead of the next one.
    #[test]
    fn return_repeats_a_finished_call() {
        let mut p = finding();
        assert_eq!(p.key(Key::Enter),
                   Asks::Run("find".into(), vec!["foo".into()]));
        assert!(p.is_open(), "the list holds the key that means again");
        assert_eq!(p.key(Key::Enter),
                   Asks::Run("find".into(), vec!["foo".into()]));
        assert_eq!(p.key(Key::Enter),
                   Asks::Run("find".into(), vec!["foo".into()]));
    }

    /// Typing takes the argument back: a new question of the same
    /// command, which is what typing over an answer means everywhere.
    #[test]
    fn typing_starts_the_search_over() {
        let mut p = finding();
        p.key(Key::Enter);
        p.key(Key::Char('b'));
        assert_eq!(p.query(), "b");
        assert!(p.asking().is_some_and(|a| !a.done && a.got.is_empty()));
        p.key(Key::Char('z'));
        assert_eq!(p.key(Key::Enter),
                   Asks::Run("find".into(), vec!["bz".into()]));
    }

    /// **Backspace edits, it does not search.**  It means *undo the
    /// last keystroke* everywhere else in this editor, and a key that
    /// deletes in one breath and searches in the next is one you have
    /// to stop and think about.
    #[test]
    fn backspace_goes_back_to_the_argument() {
        let mut p = finding();
        p.key(Key::Enter);
        assert!(p.asking().is_some_and(|a| a.done));
        p.key(Key::Backspace);
        assert!(p.asking().is_some_and(|a| !a.done),
                "back to editing what was searched for");
        assert!(p.is_open());
    }

    /// The arrows are the walk: down is the next, up is the one before.
    #[test]
    fn the_arrows_walk_forwards_and_back() {
        let mut p = finding();
        p.key(Key::Enter);
        assert_eq!(p.key(Key::Down),
                   Asks::Run("find".into(), vec!["foo".into()]));
        assert_eq!(p.key(Key::Up),
                   Asks::Run("findBack".into(), vec!["foo".into()]));
        assert_eq!(p.key(Key::Up),
                   Asks::Run("findBack".into(), vec!["foo".into()]),
                   "chosen by the key, never toggled");
        assert_eq!(p.key(Key::Down),
                   Asks::Run("find".into(), vec!["foo".into()]));
    }

    /// And Escape leaves, which is the other way out.
    #[test]
    fn escape_leaves_a_finished_call() {
        let mut p = finding();
        p.key(Key::Enter);
        assert_eq!(p.key(Key::Escape), Asks::Closed);
        assert!(!p.is_open());
        assert!(p.asking().is_none());
    }

    /// A command that takes nothing is done when it runs, as before —
    /// there is no argument to ask again with.
    #[test]
    fn a_command_without_arguments_still_closes() {
        let mut p = Palette::default();
        p.show();
        p.offer(vec![Entry { usage: "stop".into(), name: "stop".into(),
                             summary: String::new(), key: String::new(),
                             args: Vec::new(), reverse: String::new() }]);
        assert_eq!(p.key(Key::Enter), Asks::Run("stop".into(), Vec::new()));
        assert!(!p.is_open());
    }
}

#[cfg(test)]
mod reopening_tests {
    use super::*;

    /// **Opening the list must start a new question.**  It used to keep
    /// the last finished call, so the list looked ordinary while
    /// Backspace and the arrows still meant *search backwards* — and
    /// backspace stopped backspacing.
    #[test]
    fn opening_the_list_forgets_the_last_call() {
        let mut p = Palette::default();
        p.show();
        p.offer(vec![
            Entry { usage: "find <text>".into(), name: "find".into(),
                    summary: String::new(), key: String::new(),
                    args: vec!["Text".into()], reverse: "findBack".into() },
        ]);
        p.at = 0;
        p.key(Key::Char(' '));
        for c in "foo".chars() { p.key(Key::Char(c)); }
        p.key(Key::Enter);
        assert!(p.asking().is_some_and(|a| a.done));

        p.show();
        assert!(p.asking().is_none(), "a new question, not the old one");
        // And Backspace edits the query again, which is what it is for.
        for c in "loo".chars() { p.key(Key::Char(c)); }
        assert_eq!(p.key(Key::Backspace), Asks::Filter("lo".into()));
        assert_eq!(p.query(), "lo");
    }

    /// Backspace has always edited the query while a list is being
    /// filtered; only a *finished call* changes what it means.
    #[test]
    fn backspace_edits_the_query_while_filtering() {
        let mut p = Palette::default();
        p.show();
        p.offer(vec![
            Entry { usage: "loop".into(), name: "loop".into(),
                    summary: String::new(), key: String::new(),
                    args: Vec::new(), reverse: String::new() },
        ]);
        for c in "loop".chars() { p.key(Key::Char(c)); }
        assert_eq!(p.key(Key::Backspace), Asks::Filter("loo".into()));
        assert_eq!(p.key(Key::Backspace), Asks::Filter("lo".into()));
        assert_eq!(p.query(), "lo");
    }
}

#[cfg(test)]
mod choosing_tests {
    use super::*;

    fn naming(verb: &str) -> Palette {
        let mut p = Palette::default();
        p.show();
        p.offer(vec![
            Entry { usage: format!("{verb} <path>"), name: verb.into(),
                    summary: String::new(), key: String::new(),
                    args: vec!["Path".into()], reverse: String::new() },
        ]);
        p.at = 0;
        p.key(Key::Enter);
        p
    }

    /// **The one you are on is marked, not selected.**  The cursor goes
    /// there and the query stays blank, so the list opens showing where
    /// you are and the first letter typed is a new name rather than an
    /// edit of the old one.
    #[test]
    fn the_file_you_are_in_is_where_the_cursor_starts() {
        let mut p = naming("open");
        p.offer_choices(vec![
            Choice { text: "..".into(), note: String::new(),
                     here: false, can: true, step: String::new(), dim: false },
            Choice { text: "one.ges".into(), note: "2K".into(),
                     here: false, can: true, step: String::new(), dim: false },
            Choice { text: "two.ges".into(), note: "3K".into(),
                     here: true, can: true, step: String::new(), dim: false },
        ]);
        assert_eq!(p.at, 2);
        assert_eq!(p.query(), "", "and nothing is typed for you");
    }

    /// A name already taken cannot be chosen — and Enter does *nothing*
    /// rather than quietly taking what was typed, which would be the
    /// refusal failing open.
    #[test]
    fn a_taken_name_cannot_be_picked() {
        let mut p = naming("steal");
        for c in "one".chars() { p.key(Key::Char(c)); }
        p.offer_choices(vec![
            Choice { text: "one.ges".into(), note: "taken".into(),
                     here: false, can: false, step: String::new(), dim: false },
        ]);
        assert_eq!(p.key(Key::Enter), Asks::Nothing);
        assert!(p.asking().is_some_and(|a| !a.done),
                "still asking, because nothing was given");
    }

    /// And a free one can.
    #[test]
    fn a_free_name_is_taken_as_typed() {
        let mut p = naming("steal");
        for c in "new.ges".chars() { p.key(Key::Char(c)); }
        p.offer_choices(Vec::new());
        assert_eq!(p.key(Key::Enter),
                   Asks::Run("steal".into(), vec!["new.ges".into()]));
    }
}

#[cfg(test)]
mod walking_tests {
    use super::*;

    /// **A directory is a step, not an answer.**  Picking one moves the
    /// query into it and asks again — which is what a file dialog does,
    /// and what makes going up and then down into another directory
    /// feel like walking rather than like starting over.
    #[test]
    fn choosing_a_directory_walks_into_it() {
        let mut p = Palette::default();
        p.show();
        p.offer(vec![
            Entry { usage: "open <path>".into(), name: "open".into(),
                    summary: String::new(), key: String::new(),
                    args: vec!["Path".into()], reverse: String::new() },
        ]);
        p.at = 0;
        p.key(Key::Enter);
        p.offer_choices(vec![
            Choice { text: "../".into(), note: String::new(), here: false,
                     can: true, step: "../".into(), dim: false },
            Choice { text: "one.ges".into(), note: "2K".into(), here: false,
                     can: true, step: String::new(), dim: false },
        ]);
        // Up one: the query becomes the path, and it is still asking.
        assert_eq!(p.key(Key::Enter),
                   Asks::Wants("open".into(), 0, "../".into()));
        assert_eq!(p.query(), "../");
        assert!(p.asking().is_some_and(|a| !a.done));

        // And down into another: the steps compose.
        p.offer_choices(vec![
            Choice { text: "audio/".into(), note: "directory".into(),
                     here: false, can: true, step: "../audio/".into(), dim: false },
        ]);
        assert_eq!(p.key(Key::Enter),
                   Asks::Wants("open".into(), 0, "../audio/".into()));
        assert_eq!(p.query(), "../audio/");

        // A file is the answer, and ends the question.
        p.offer_choices(vec![
            Choice { text: "two.ges".into(), note: "3K".into(), here: false,
                     can: true, step: String::new(), dim: false },
        ]);
        assert_eq!(p.key(Key::Enter),
                   Asks::Run("open".into(), vec!["two.ges".into()]));
    }
}
