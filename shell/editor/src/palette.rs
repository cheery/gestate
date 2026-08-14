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
use crate::view::{Frame, Item, ANGRY};

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
    /// What sort of thing it is — `type`, `class`, `value`, `operator`.
    ///
    /// **A type is a different sort of answer from a function.**  You
    /// reach for one to say what something *is* and the other to say
    /// what it *does*, and a list that spelled them the same made the
    /// reader open each to find out which they had.  Empty for a row
    /// that is not a name at all — a path, a symbol, a yes.
    pub kind: String,
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
/// A type, a class or an alias, among the values.
///
/// Warm against the ink's cool grey, and readable at the same weight —
/// a *tint*, not a highlight: the point is to tell two kinds of answer
/// apart at a glance, not to say one of them matters more.
pub const TYPED: Colour = Colour::rgb(0xd8, 0xb0, 0x7c);

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
    /// Whether the panel sits in the window's lower half.
    ///
    /// **The panel moves so the text does not have to.**  A template
    /// inserted at the top of the file has nowhere to scroll past the
    /// panel — `follow_past` saturates at row zero — so when the caret
    /// stands where the top panel would cover it, the panel flips low
    /// and the edit is read where it landed (F121's second half).
    /// Set by the window each frame, because the caret is the
    /// window's; `panel_box` reads it, so drawing, hit-testing and the
    /// shadow flip together.
    pub low: bool,
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
    /// The query the choices on hand were answered for.
    ///
    /// **So a refresh can be told from a keystroke.**  The two arrive
    /// at `offer_choices` looking identical — a new list for the same
    /// palette — and they want opposite things: after a keystroke the
    /// ranking decides where the cursor goes, while a refresh must not
    /// move it at all.
    answered_for: String,
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
        // **The pick holds its own row when the list changes underneath
        // it.**  A directory listing refreshes while the dialog sits
        // open — a file arrives, and every row below it shifts down — and
        // an index kept through that is a cursor that quietly changes
        // what it means.  The Return you were about to press would open
        // the neighbour; for `steal`, it would overwrite it.
        //
        // Only when the query is the one these choices were last
        // answered for.  A keystroke re-ranks, and `requery` has already
        // put the cursor at the top for it — holding a name through
        // *that* would fight the filter.
        let held = if !fresh && self.asking.is_some()
            && self.query == self.answered_for {
            self.choices.get(self.at).map(|c| c.text.clone())
        } else {
            None
        };
        self.answered_for = self.query.clone();
        self.choices = choices;
        // Only on the way in, and only while nothing is typed: once a
        // query narrows the list, where the cursor goes is the
        // ranking's business.
        if fresh && self.query.is_empty() {
            if let Some(at) = self.choices.iter().position(|c| c.here) {
                self.at = at;
            }
        } else if let Some(name) = held {
            // Gone rather than moved — the file was deleted while you
            // were looking at it — leaves the index where it was and
            // `clamp` keeps it in range, which is the same thing every
            // other list does when its rows go away.
            if let Some(at) = self.choices.iter().position(|c| c.text == name) {
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
            //
            // *And except in `Path`* (`fixme.md` F111): a directory
            // listing opens with the cursor on a row nobody chose —
            // `../` at the top — and accept prefers the pick, so a
            // space "stepped" into the parent and a proposed path that
            // was one Return from being taken was wiped by the walk.
            // A space in a path box is content; taking the path is
            // Return's, and Tab completes.
            Key::Char(' ') if self.asking.is_none() => {
                match self.selected().cloned() {
                    Some(e) if !e.args.is_empty() => self.take(&e),
                    _ => Asks::Nothing,
                }
            }
            Key::Char(' ')
                if !matches!(self.asking.as_ref().map(|a| a.wants()),
                             Some("Text") | Some("Path"))
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
            // **Tab completes to the pick.**  What every shell taught a
            // hand in a path box: the row the cursor is on becomes the
            // text, a directory completes to its own walk and re-lists,
            // and nothing runs — taking the answer is still Return's.
            // Bound while any argument is asked, because completion is
            // never wrong; it simply has nothing to do when the model
            // offered no rows.
            Key::Tab if self.asking.is_some() => {
                match self.choices.get(self.at).cloned() {
                    Some(c) if !c.step.is_empty() => {
                        self.query = c.step.clone();
                        self.requery()
                    }
                    Some(c) if !c.text.is_empty() && c.can => {
                        // **Completion keeps the walk** (F130's
                        // spindle): rows carry names relative to the
                        // walk, and writing the bare name over
                        // `examples/audio/lan` left a query that
                        // *showed* `lantern.ges` and resolved at the
                        // root — a look-alike, one Return from a
                        // phantom.  The head is the query's own, the
                        // same split the model's `_listing` reads.
                        self.query = match self.query.rsplit_once('/') {
                            Some((head, _)) => format!("{head}/{}", c.text),
                            None => c.text.clone(),
                        };
                        self.requery()
                    }
                    _ => Asks::Nothing,
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

    /// The panel's own box — position, width, height.
    ///
    /// **One arithmetic for drawing and hit-testing alike**: `frame`
    /// paints this box and `covers` asks about it, so a click cannot
    /// land outside what is drawn while the code thinks it is inside.
    fn panel_box(&self, w: i32, h: i32, cw: i32, ch: i32)
        -> (i32, i32, i32, i32)
    {
        let most = self.rows(h, ch);
        let shown = self.shown_len().min(most);
        // **The summary is a row of the panel, not a line beside it**
        // (it used to be painted straight over the file), so it is
        // counted before the box is sized.  And **a grid is as tall as
        // its own lines**, not as tall as the list it replaced.
        let telling = self.asking.is_none() && self.selected().is_some();
        let box_w = (w - 2 * cw).max(cw);
        let grid = self.asking.as_ref().map(|a| a.wants()) == Some("Symbol");
        let rows = if grid {
            let per = Self::columns(box_w, cw);
            (self.choices.len() as i32 + per - 1) / per.max(1) + 1
        } else {
            shown as i32 + 1 + i32::from(telling)
        };
        let box_h = ch * rows + 8;
        // Low: bottom-anchored, above where the status bar stands —
        // the flip that keeps a top-of-file edit readable.
        let y = if self.low {
            (h - box_h - 2 * ch).max(ch)
        } else {
            ch
        };
        (cw, y, box_w, box_h)
    }

    /// How many text rows the panel covers from the window's top —
    /// zero when it is closed, and zero when it sits low.  What
    /// `follow_past` scrolls past, so an ordered edit lands where a
    /// person can see it rather than behind the list.
    pub fn shadow_rows(&self, w: i32, h: i32, cw: i32, ch: i32) -> usize {
        if !self.open || self.low {
            return 0;
        }
        self.shadow_rows_at_top(w, h, cw, ch)
    }

    /// The same count with the panel imagined at the top — what the
    /// window asks when deciding whether to *send* it low, which
    /// cannot read the answer it is about to change.
    pub fn shadow_rows_at_top(&self, w: i32, h: i32, cw: i32, ch: i32)
        -> usize
    {
        if !self.open {
            return 0;
        }
        let (_, _, _, bh) = self.panel_box(w, h, cw, ch);
        ((ch + bh + 2 + ch - 1) / ch.max(1)) as usize
    }

    /// Whether the pointer is over the panel at all — edge included.
    ///
    /// What lets a click *outside* the list mean "not this list": a
    /// press the panel does not cover closes it and then lands on
    /// whatever it was aimed at, instead of being eaten (a knob, a bank
    /// box or the text was unreachable while the list was open).
    pub fn covers(&self, w: i32, h: i32, cw: i32, ch: i32, x: i32, y: i32)
        -> bool
    {
        if !self.open {
            return false;
        }
        let (bx, by, bw, bh) = self.panel_box(w, h, cw, ch);
        x >= bx - 2 && x <= bx + bw + 2 && y >= by - 2 && y <= by + bh + 2
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
        // Through `panel_box`, so a panel that flipped low is clicked
        // where it is drawn.
        let (bx, by, box_w, _bh) = self.panel_box(w, h, cw, ch);
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
        // **Only a call that declared a walk gets one.**  `find` and
        // `findBack` are a pair, so the arrows mean the next match and
        // the one before.  A call with *no* reverse used to "simply
        // repeat", which read well in a comment and badly at the
        // keyboard: `seek 0`, then Up reaching for history, and the
        // transport jumps again — an arrow must never be an accidental
        // Return (`fixme.md` F107).  Repeating a finished call is
        // Enter's, deliberately.
        if a.reverse.is_empty() {
            return Asks::Nothing;
        }
        // **Chosen, not toggled.**  Swapping the pair would make a
        // second press of the same arrow go the other way, so holding
        // Up would walk back and forth over two matches for ever.  The
        // key names the direction; the pair names the two commands.
        let verb = if back {
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

    pub fn frame(&self, w: i32, h: i32, cw: i32, ch: i32,
                 warning: &str) -> Frame {
        let mut f = Frame::default();
        if !self.open {
            return f;
        }
        let most = self.rows(h, ch);
        let shown = self.shown_len().min(most);
        // The summary row, the grid's own height and the box they add
        // up to are `panel_box`'s — the one arithmetic `covers` reads
        // too, so the panel that is drawn and the panel that is hit
        // cannot disagree.
        let grid = self.asking.as_ref().map(|a| a.wants()) == Some("Symbol");
        let (x, y, box_w, box_h) = self.panel_box(w, h, cw, ch);

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
        let caret_x = x + 4
            + (lead.chars().count() + self.query.chars().count()) as i32
                * cw;
        f.items.push(Item::Run { x: x + 4, y: y + 4,
                                 s: format!("{lead}{}", self.query),
                                 c: INK });
        f.items.push(Item::Rect {
            x: caret_x, y: y + 4, w: 2.max(cw / 5), h: ch, c: INK });
        // **The warning, beside the caret that is active.**  While the
        // list is up the hand is here, not in the text — so a refusal
        // said beside the document's caret is a refusal said to an
        // empty chair.  Same red, same transience; shifted left rather
        // than clipped when the query runs long.
        if !warning.is_empty() {
            let wide = warning.chars().count() as i32 * cw;
            let wx = (caret_x + 2 * cw).min(x + box_w - wide - 4).max(x);
            f.items.push(Item::Run { x: wx, y: y + 4,
                                     s: warning.to_string(), c: ANGRY });
        }

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
            let tint = self.choices.get(from + i)
                .map(|c| matches!(c.kind.as_str(),
                                  "type" | "class" | "alias"))
                .unwrap_or(false);
            f.items.push(Item::Run {
                x: x + 4, y: row, s: elide(left, room),
                c: if dim.get(from + i).copied().unwrap_or(false) {
                    FAINT
                } else if tint {
                    TYPED
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

        // The page, beside the panel and in its own — as many lines
        // as it has room for, which is why it is not the summary's
        // single row.
        if !self.page.is_empty() {
            let room = (((box_w - 8) / cw.max(1)).max(4)) as usize;
            // **The page goes where the room is** (F133).  It always
            // hung below the panel, and the equator sends the panel
            // low when the caret is high — so `what scope` drew its
            // answer past the bottom of the window, pixels nobody
            // could see.  Below when below holds it, above when the
            // panel sits low, and when neither side holds the whole
            // page, as many lines as fit with the last row counting
            // the rest — the full page stays one `doc/ref/` away.
            let want = self.page.len() as i32;
            let below = ((h - (y + box_h + 6) - 12) / ch).max(0);
            let above = ((y - 12) / ch).max(0);
            let (fit, up) = if below >= want {
                (want, false)
            } else if above >= want {
                (want, true)
            } else if below >= above {
                (below.max(1), false)
            } else {
                (above.max(1), true)
            };
            let tall = ch * fit + 8;
            let py = if up { y - tall - 6 } else { y + box_h + 6 };
            f.items.push(Item::Rect { x: x - 2, y: py - 2, w: box_w + 4,
                                      h: tall + 4, c: EDGE });
            f.items.push(Item::Rect { x, y: py, w: box_w, h: tall,
                                      c: SHADE });
            for i in 0..fit as usize {
                let cut = fit < want && i as i32 + 1 == fit;
                let s = if cut {
                    format!("… {} more", want - fit + 1)
                } else {
                    elide(&self.page[i], room)
                };
                f.items.push(Item::Run {
                    x: x + 4, y: py + 4 + ch * i as i32, s,
                    c: if i == 0 && !cut { INK } else { FAINT } });
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

        /// **The page goes where the room is** (F133): the equator sends
    /// the panel low when the caret is high, and the page — which
    /// always hung below — drew past the window's bottom, pixels
    /// nobody could see.  Above the low panel, inside the window,
    /// and counted-elided when neither side holds it whole.
    #[test]
    fn a_page_stays_inside_the_window() {
        let (w, h, cw, ch) = (900, 600, 10, 20);
        let mut p = Palette::default();
        p.show();
        p.low = true;                     // the equator sent it low
        p.offer_page((0..12).map(|i| format!("line {i}")).collect());
        let f = p.frame(w, h, cw, ch, "");
        for item in &f.items {
            match item {
                Item::Rect { y, h: ih, .. } =>
                    assert!(y + ih <= h && *y >= 0,
                            "a rect left the window: y={y} h={ih}"),
                Item::Run { y, .. } =>
                    assert!(*y >= 0 && y + ch <= h,
                            "a row left the window: y={y}"),
            }
        }
        // And a window too small for the whole page says how much is
        // missing rather than hiding it.
        let mut q = Palette::default();
        q.show();
        q.low = true;
        q.offer_page((0..200).map(|i| format!("line {i}")).collect());
        let g = q.frame(w, 240, cw, ch, "");
        assert!(g.items.iter().any(|i| matches!(i,
            Item::Run { s, .. } if s.starts_with("… "))),
            "a cut page kept quiet about the rest");
    }

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
        let f = a_palette().frame(800, 600, cw, ch, "");
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

    /// The warning belongs to the caret that is active — while the list
    /// is up, that is the query box's, and a refusal said beside the
    /// document's caret would be said to an empty chair.
    #[test]
    fn a_warning_stands_beside_the_query_caret() {
        use crate::view::ANGRY;

        let (cw, ch) = (8, 16);
        let f = a_palette().frame(800, 600, cw, ch,
                                  "warning: unsaved changes");
        let warn = f.items.iter().find_map(|i| match i {
            Item::Run { c, s, y, .. } if *c == ANGRY =>
                Some((s.clone(), *y)),
            _ => None,
        });
        let (said, wy) = warn.expect("the warning is drawn");
        assert_eq!(said, "warning: unsaved changes");
        assert_eq!(wy, ch + 4, "on the query row, beside its caret");
        let quiet = a_palette().frame(800, 600, cw, ch, "");
        assert!(!quiet.items.iter().any(|i| matches!(i, Item::Run { c, .. }
                                                     if *c == ANGRY)));
    }

    /// The panel flips to the lower half when told to, and drawing,
    /// hit-testing and the shadow move together — one arithmetic.
    #[test]
    fn the_panel_flips_low_as_one_piece() {
        let (cw, ch) = (8, 16);
        let mut p = a_palette();
        p.low = true;
        let f = p.frame(800, 600, cw, ch, "");
        let (y, h) = match f.items[1] {
            Item::Rect { y, h, .. } => (y, h),
            ref other => panic!("expected the shade, got {other:?}"),
        };
        assert!(y > 300, "the shade sits in the lower half, got y={y}");
        assert!(y + h <= 600 - ch, "and above where the status stands");
        assert_eq!(p.shadow_rows(800, 600, cw, ch), 0,
                   "a low panel shades nothing at the top");
        assert!(p.shadow_rows_at_top(800, 600, cw, ch) > 0);
        // A click on the first row hits where it is drawn.
        assert!(p.row_at(800, 600, cw, ch, cw + 4, y + 4 + ch + 2)
                 .is_some());
        assert!(p.row_at(800, 600, cw, ch, cw + 4, ch + 4 + ch + 2)
                 .is_none(), "nothing answers at the abandoned top");
    }

    /// `covers` and the drawn panel are one box — the drawn shade's own
    /// rectangle answers yes, and one pixel past the border answers no,
    /// which is what lets a click outside the list close it and still
    /// land on what it was aimed at.
    #[test]
    fn covers_agrees_with_what_is_drawn() {
        let (cw, ch) = (8, 16);
        let p = a_palette();
        let f = p.frame(800, 600, cw, ch, "");
        let (x, y, w, h) = match f.items[0] {
            Item::Rect { x, y, w, h, .. } => (x, y, w, h),
            ref other => panic!("expected the panel's border, got {other:?}"),
        };
        assert!(p.covers(800, 600, cw, ch, x + w / 2, y + h / 2));
        assert!(p.covers(800, 600, cw, ch, x, y));
        assert!(!p.covers(800, 600, cw, ch, x + w + 1, y));
        assert!(!p.covers(800, 600, cw, ch, x, y + h + 1));
        // And a closed list covers nothing at all.
        let mut shut = a_palette();
        shut.hide();
        assert!(!shut.covers(800, 600, cw, ch, x + w / 2, y + h / 2));
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
        let f = a_grid().frame(800, 600, cw, ch, "");
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
        p.frame(800, 600, 8, 16, "");            // the layout sets the width
        let wide = p.wide.get() as usize;
        assert!(wide > 1, "the test window fits only one column");
        p.key(Key::Right);
        assert_eq!(p.at, 1, "right did not move a cell");
        p.key(Key::Left);
        assert_eq!(p.at, 0);
    }

    #[test]
    fn the_summary_of_the_picked_command_is_shown() {
        let f = a_palette().frame(800, 600, 8, 16, "");
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
            Choice { text: "cutoff".into(), note: "Chan Float".into(), here: false, can: true, step: String::new(), dim: false, kind: String::new() },
            Choice { text: "pitch".into(), note: "Chan Int".into(), here: false, can: true, step: String::new(), dim: false, kind: String::new() },
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

    /// A finished call with no declared reverse does not run again on
    /// an arrow — `seek 0`, then Up reaching for history, and the
    /// transport jumped (fixme.md F107).  The walk is the find pair's;
    /// repeating is Enter's, deliberately.
    #[test]
    fn an_arrow_is_not_an_accidental_return() {
        let mut p = Palette::default();
        p.show();
        p.offer(vec![Entry { usage: "seek <int>".into(),
                             name: "seek".into(),
                             summary: String::new(), key: String::new(),
                             args: vec!["Int".into()],
                             reverse: String::new() }]);
        p.at = 0;
        p.key(Key::Char(' '));
        p.key(Key::Char('0'));
        assert_eq!(p.key(Key::Enter),
                   Asks::Run("seek".into(), vec!["0".into()]));
        assert_eq!(p.key(Key::Up), Asks::Nothing);
        assert_eq!(p.key(Key::Down), Asks::Nothing);
        assert_eq!(p.key(Key::Enter),
                   Asks::Run("seek".into(), vec!["0".into()]),
                   "Enter still means again");
    }

    /// A palette asking `transcript` for a `Path`, with the proposal
    /// filled and a directory listing whose first row is `../` — the
    /// exact stage F111 was reported at.
    fn walking() -> Palette {
        let mut p = Palette::default();
        p.show();
        p.offer(vec![Entry { usage: "transcript <path>".into(),
                             name: "transcript".into(),
                             summary: String::new(), key: String::new(),
                             args: vec!["Path".into()],
                             reverse: String::new() }]);
        p.at = 0;
        p.key(Key::Char(' '));
        p.fill("demo-session.ges");
        p.offer_choices(vec![
            Choice { text: String::new(), note: "../".into(), can: true,
                     step: "..".into(), ..Default::default() },
            Choice { text: "demo.ges".into(), note: String::new(),
                     can: true, ..Default::default() },
        ]);
        p
    }

    /// Space in a path box is content, never a step into the row nobody
    /// chose — it must not eat a path somebody was about to accept
    /// (fixme.md F111).
    #[test]
    fn space_does_not_eat_a_proposed_path() {
        let mut p = walking();
        p.key(Key::Char(' '));
        assert_eq!(p.query(), "demo-session.ges ",
                   "the proposal stays, the space is typed");
        assert!(p.asking().is_some_and(|a| a.got.is_empty()),
                "nothing was accepted");
    }

    /// Tab completes to the pick, the way every shell taught: a plain
    /// row becomes the text, a directory becomes its own walk, and
    /// nothing runs.
    #[test]
    fn tab_completes_the_path_under_the_cursor() {
        let mut p = walking();
        p.at = 1;
        p.key(Key::Tab);
        assert_eq!(p.query(), "demo.ges");
        assert!(p.asking().is_some_and(|a| a.got.is_empty()),
                "completing is not taking");
        let mut q = walking();
        q.at = 0;
        assert!(matches!(q.key(Key::Tab), Asks::Wants(..)),
                "a directory re-lists");
        assert_eq!(q.query(), "..", "a directory completes to its walk");
    }

    /// **Completion keeps the walk** (F130's spindle): after walking
    /// to `examples/audio/`, Tab on the `lantern.ges` row must leave
    /// `examples/audio/lantern.ges` in the box.  Writing the bare
    /// name over the walk left a query that *showed* the right file
    /// and resolved at the root — a look-alike, one Return from a
    /// phantom.
    #[test]
    fn tab_keeps_the_walk_it_completes_under() {
        let mut p = walking();
        p.fill("examples/audio/lan");
        p.offer_choices(vec![
            Choice { text: "lantern.ges".into(), note: String::new(),
                     can: true, ..Default::default() },
        ]);
        p.at = 0;
        p.key(Key::Tab);
        assert_eq!(p.query(), "examples/audio/lantern.ges",
                   "the walk was wiped by its own completion");
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
                     here: false, can: true, step: String::new(), dim: false, kind: String::new() },
            Choice { text: "one.ges".into(), note: "2K".into(),
                     here: false, can: true, step: String::new(), dim: false, kind: String::new() },
            Choice { text: "two.ges".into(), note: "3K".into(),
                     here: true, can: true, step: String::new(), dim: false, kind: String::new() },
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
                     here: false, can: false, step: String::new(), dim: false, kind: String::new() },
        ]);
        assert_eq!(p.key(Key::Enter), Asks::Nothing);
        assert!(p.asking().is_some_and(|a| !a.done),
                "still asking, because nothing was given");
    }

    /// **A list that refreshes must not move the cursor off its row.**
    ///
    /// The directory listing re-reads while the dialog sits open, so a
    /// file arriving above the pick shifts every row below it down.  An
    /// index carried through that points at the neighbour, and the
    /// Return you were about to press opens the wrong file — which for
    /// `steal` is the one it overwrites.
    #[test]
    fn a_file_arriving_does_not_move_the_pick_off_its_row() {
        let row = |name: &str| Choice {
            text: name.into(), note: "2K".into(), here: false, can: true,
            step: String::new(), dim: false, kind: String::new(),
        };
        let mut p = naming("open");
        p.offer_choices(vec![row("beta.ges"), row("gamma.ges")]);
        p.at = 1;                                   // on `gamma.ges`

        // `alpha.ges` is moved into the directory and sorts first.
        p.offer_choices(vec![row("alpha.ges"), row("beta.ges"),
                             row("gamma.ges")]);
        assert_eq!(p.at, 2, "the pick followed its own name");
    }

    /// And the refresh still *shows* what arrived — holding the pick is
    /// not holding the list.
    #[test]
    fn a_refresh_still_brings_the_new_row_in() {
        let row = |name: &str| Choice {
            text: name.into(), note: "2K".into(), here: false, can: true,
            step: String::new(), dim: false, kind: String::new(),
        };
        let mut p = naming("open");
        p.offer_choices(vec![row("beta.ges")]);
        p.offer_choices(vec![row("alpha.ges"), row("beta.ges")]);
        assert_eq!(p.choices.len(), 2);
    }

    /// **Typing is the other case, and it must keep its old behaviour.**
    /// A keystroke re-ranks and `requery` puts the cursor at the top for
    /// it; holding a name through that would fight the filter.
    #[test]
    fn typing_still_lets_the_ranking_place_the_cursor() {
        let row = |name: &str| Choice {
            text: name.into(), note: "2K".into(), here: false, can: true,
            step: String::new(), dim: false, kind: String::new(),
        };
        let mut p = naming("open");
        p.offer_choices(vec![row("beta.ges"), row("gamma.ges")]);
        p.at = 1;
        p.key(Key::Char('g'));                       // the query changed
        p.offer_choices(vec![row("gamma.ges")]);
        assert_eq!(p.at, 0, "the filter decides, as it always did");
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
                     can: true, step: "../".into(), dim: false, kind: String::new() },
            Choice { text: "one.ges".into(), note: "2K".into(), here: false,
                     can: true, step: String::new(), dim: false, kind: String::new() },
        ]);
        // Up one: the query becomes the path, and it is still asking.
        assert_eq!(p.key(Key::Enter),
                   Asks::Wants("open".into(), 0, "../".into()));
        assert_eq!(p.query(), "../");
        assert!(p.asking().is_some_and(|a| !a.done));

        // And down into another: the steps compose.
        p.offer_choices(vec![
            Choice { text: "audio/".into(), note: "directory".into(),
                     here: false, can: true, step: "../audio/".into(), dim: false, kind: String::new() },
        ]);
        assert_eq!(p.key(Key::Enter),
                   Asks::Wants("open".into(), 0, "../audio/".into()));
        assert_eq!(p.query(), "../audio/");

        // A file is the answer, and ends the question.
        p.offer_choices(vec![
            Choice { text: "two.ges".into(), note: "3K".into(), here: false,
                     can: true, step: String::new(), dim: false, kind: String::new() },
        ]);
        assert_eq!(p.key(Key::Enter),
                   Asks::Run("open".into(), vec!["two.ges".into()]));
    }
}
