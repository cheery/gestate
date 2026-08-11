//! What a key *means* — pointer and keyboard events to edits, with no
//! window in sight.
//!
//! `audiopygame`'s split, kept: `Document` is text and a caret, `Pane`
//! is what a key means, and neither imports a toolkit.  The value of
//! separating them is that "does Home go to the start of the line"
//! becomes a test instead of a thing you check by pressing Home.
//!
//! **A small alphabet, named here rather than taken from a toolkit.**
//! `baseview` hands over `keyboard_types::KeyboardEvent`; the
//! translation happens in `window`, which is the only module allowed to
//! know that crate exists — the same rule the display list keeps for
//! drawing.

use crate::document::Document;
use crate::font::Font;
use crate::view::View;

/// A key, as the editor understands it.
#[derive(Clone, PartialEq, Eq, Debug)]
pub enum Key {
    /// A character to type.  Already filtered: control codes never
    /// arrive here, so nothing downstream has to ask.
    Char(char),
    Enter,
    Tab,
    Backspace,
    Delete,
    Left,
    Right,
    Up,
    Down,
    Home,
    End,
    PageUp,
    PageDown,
    /// The whole document.
    Top,
    Bottom,
    Undo,
    Redo,
    Copy,
    Cut,
    Paste,
    SelectAll,
}

impl Key {
    /// Whether this key moves the caret rather than changing the text.
    ///
    /// **The one question shift changes the answer to.**  A shifted
    /// motion extends the selection; an unshifted one drops it; and an
    /// *edit* does neither, because typing over a selection replaces it
    /// and the shift key was only how you got the capital letter.
    pub fn is_motion(&self) -> bool {
        matches!(self, Key::Left | Key::Right | Key::Up | Key::Down
                     | Key::Home | Key::End | Key::PageUp | Key::PageDown
                     | Key::Top | Key::Bottom)
    }
}

/// Where cut and copy put things, and where paste takes them from.
///
/// **A trait, because there are two answers and only one of them is
/// this crate's.**  Within the editor a `Memory` clipboard is complete
/// and costs nothing.  The *system* clipboard is a platform
/// negotiation — on X11 it is selection ownership and the INCR
/// protocol, and `baseview` 0.3's `copy_to_clipboard` is a stub that
/// ignores its argument — so it belongs to whoever embeds the editor
/// and already owns a connection.  The seam is here so that one can be
/// handed in without any of the code above changing.
pub trait Clipboard {
    fn get(&self) -> String;
    fn set(&mut self, text: &str);
}

/// The editor's own, which does not leave the process.
#[derive(Default)]
pub struct Memory(String);

impl Clipboard for Memory {
    fn get(&self) -> String {
        self.0.clone()
    }

    fn set(&mut self, text: &str) {
        self.0 = text.to_string();
    }
}

/// Which modifiers were down.  Only the two that change meaning here.
#[derive(Clone, Copy, PartialEq, Eq, Debug, Default)]
pub struct Mods {
    pub ctrl: bool,
    pub shift: bool,
}

/// What the editor did about a key, so a caller knows whether to
/// redraw, and whether the *text* changed.
///
/// **Two flags rather than one**, because they have different readers:
/// a window redraws on either, and a host that owns the document —
/// Python, once the ABI lands — only wants telling when the text moved.
#[derive(Clone, Copy, PartialEq, Eq, Debug, Default)]
pub struct Did {
    pub drew: bool,
    pub edited: bool,
}

impl Did {
    pub fn nothing() -> Did {
        Did::default()
    }

    fn moved() -> Did {
        Did { drew: true, edited: false }
    }

    fn wrote() -> Did {
        Did { drew: true, edited: true }
    }
}

/// An edit's answer as a `Did`: it drew and edited only if it really
/// changed the text.  A refusal is silence, not a redraw.
fn wrote(r: Result<bool, crate::rope::OutOfRange>) -> Did {
    match r {
        Ok(true) => Did::wrote(),
        Ok(false) | Err(_) => Did::nothing(),
    }
}

/// Apply one key.
///
/// The view is scrolled to follow the caret afterwards — **always**,
/// and that is deliberate: a motion that left the caret off screen
/// would be a motion you could not see the result of, and every caller
/// would have to remember to call `follow` for itself.
pub fn press(doc: &mut Document, view: &mut View, font: &Font,
             key: Key, mods: Mods) -> Did
{
    press_with(doc, view, font, key, mods, &mut Memory::default())
}

/// The same, with somewhere for cut and paste to go.
pub fn press_with(doc: &mut Document, view: &mut View, font: &Font,
                  key: Key, mods: Mods, clip: &mut dyn Clipboard) -> Did
{
    let rows = view.rows(font);
    // **Before the motion, not after.**  Shift means "keep the end I
    // am not moving", so the anchor has to be put down where the caret
    // *was*; deciding afterwards would anchor it where it arrived and
    // select nothing.
    if key.is_motion() {
        if mods.shift {
            doc.begin_extend();
        } else {
            doc.clear_anchor();
        }
    }
    let did = match key {
        Key::Char(c) => {
            let mut b = [0u8; 4];
            wrote(doc.insert(c.encode_utf8(&mut b)))
        }
        Key::Enter => wrote(doc.insert("\n")),
        // **A tab is a tab**, stored as one character.  Turning it into
        // spaces on the way in is a decision about somebody else's file
        // that an editor should not make quietly; what a tab *looks*
        // like is `document::TAB` and is a view's business.
        Key::Tab => wrote(doc.insert("\t")),
        Key::Backspace => wrote(doc.backspace()),
        Key::Delete => wrote(doc.delete()),
        Key::Left => { doc.left(); Did::moved() }
        Key::Right => { doc.right(); Did::moved() }
        Key::Up => { doc.up(); Did::moved() }
        Key::Down => { doc.down(); Did::moved() }
        Key::Home => { doc.home(); Did::moved() }
        Key::End => { doc.end(); Did::moved() }
        Key::PageUp | Key::PageDown => {
            // **A page is a screen minus a line**, so one line of what
            // you were reading is still there afterwards.  Losing every
            // line you had just read is how a page key makes you scroll
            // back up.
            let step = rows.saturating_sub(1).max(1);
            let (row, col) = doc.cursor();
            let next = if key == Key::PageUp {
                row.saturating_sub(step)
            } else {
                (row + step).min(doc.rows() - 1)
            };
            // Through `seek_rowcol`, so a page keeps the column the way
            // an arrow does.
            doc.seek_rowcol(next, col);
            Did::moved()
        }
        Key::Top => { doc.seek(0); Did::moved() }
        Key::Bottom => { doc.seek(doc.len()); Did::moved() }
        Key::Undo => if doc.undo() { Did::wrote() } else { Did::nothing() },
        Key::Redo => if doc.redo() { Did::wrote() } else { Did::nothing() },
        Key::SelectAll => { doc.select_all(); Did::moved() }
        Key::Copy => {
            // **Copying nothing leaves the clipboard alone.**  Ctrl-C
            // with no selection is a miss, and emptying what you had
            // copied a moment ago is the worst possible answer to one.
            match doc.selection() {
                None => Did::nothing(),
                Some(_) => {
                    clip.set(&doc.selected());
                    Did::nothing()
                }
            }
        }
        Key::Cut => match doc.selection() {
            None => Did::nothing(),
            Some(_) => {
                clip.set(&doc.selected());
                wrote(doc.delete_selection())
            }
        },
        Key::Paste => {
            let text = clip.get();
            if text.is_empty() && doc.selection().is_none() {
                Did::nothing()
            } else {
                wrote(doc.insert(&text))
            }
        }
    };
    if did.drew {
        view.clamp(doc, font);
        view.follow(doc, font);
    }
    did
}

/// A click: put the caret where the pointer is, dropping any
/// selection.
pub fn click(doc: &mut Document, view: &View, font: &Font, x: i32, y: i32)
    -> Did
{
    let (row, col) = view.hit(doc, font, x, y);
    doc.clear_anchor();
    doc.seek_rowcol(row, col);
    Did::moved()
}

/// A drag: the same, extending from wherever the press landed.
pub fn drag(doc: &mut Document, view: &View, font: &Font, x: i32, y: i32)
    -> Did
{
    let (row, col) = view.hit(doc, font, x, y);
    doc.begin_extend();
    let was = doc.pos();
    doc.seek_rowcol(row, col);
    Did { drew: doc.pos() != was, edited: false }
}

/// A wheel, in lines.  Positive is down the document.
///
/// **The caret does not move**, which is the whole difference between
/// scrolling and navigating: looking somewhere else must not lose your
/// place, and an editor that dragged the caret along with the wheel
/// would make reading destructive.
pub fn scroll(doc: &Document, view: &mut View, font: &Font, lines: i32)
    -> Did
{
    let was = view.top;
    let next = view.top as i64 + lines as i64;
    let rows = view.rows(font) as i64;
    let last = (doc.rows() as i64 - rows).max(0);
    view.top = next.clamp(0, last) as usize;
    Did { drew: view.top != was, edited: false }
}
