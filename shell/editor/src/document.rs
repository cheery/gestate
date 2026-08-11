//! A document: the rope, and a cursor over it.
//!
//! `audiopygame.Document` in Rust — text and a place in it, with the
//! motions and edits a keyboard means.  Nothing here draws and nothing
//! here knows a window exists, which is the same split
//! `audioeditor.Workbench` already keeps from its view.
//!
//! **Every edit returns; nothing is edited in place.**  The rope is
//! persistent, so `Document` holds a root and replacing it is a pointer
//! — which is what makes undo a stack rather than a diff, and lets a
//! background rebuild hold the version it started from while you keep
//! typing.

use crate::rope::{OutOfRange, Rope};

/// How wide a tab is, in columns.
///
/// **A column is not a character**, and this is the one place that is
/// true.  Everywhere else a position is a character offset, because
/// that is what the rope indexes and what an edit means; a *column* is
/// a screen fact, and a tab is the character that makes the two differ.
/// Keeping the conversion in `column_of`/`char_of_column` means nothing
/// else has to know.
pub const TAB: usize = 4;

#[derive(Clone, Debug)]
pub struct Document {
    text: Rope,
    /// Where the caret is, as a character offset.
    pos: usize,
    /// The column an up/down motion is *aiming* for.
    ///
    /// **Because a short line must not eat the column.**  Going down
    /// from column 40 through a three-character line and on should
    /// arrive back at 40, not at 3 — so the goal is remembered until a
    /// motion that is about columns rather than rows clears it.  Every
    /// editor does this and every one that does not is immediately
    /// annoying.
    goal: Option<usize>,
    /// Roots this document used to have, newest last.
    undo: Vec<(Rope, usize)>,
    redo: Vec<(Rope, usize)>,
}

impl Default for Document {
    fn default() -> Self {
        Document::new("")
    }
}

impl Document {
    pub fn new(text: &str) -> Document {
        Document { text: Rope::from_str(text), pos: 0, goal: None,
                   undo: Vec::new(), redo: Vec::new() }
    }

    pub fn rope(&self) -> &Rope {
        &self.text
    }

    pub fn len(&self) -> usize {
        self.text.len()
    }

    pub fn is_empty(&self) -> bool {
        self.text.len() == 0
    }

    pub fn rows(&self) -> usize {
        self.text.rows()
    }

    pub fn text(&self) -> String {
        self.text.text()
    }

    pub fn pos(&self) -> usize {
        self.pos
    }

    pub fn line(&self, row: usize) -> String {
        self.text.line(row).unwrap_or_default()
    }

    /// The caret's row and column.
    pub fn cursor(&self) -> (usize, usize) {
        let row = self.text.row(self.pos).unwrap_or(0);
        let start = self.text.rowpos(row).unwrap_or(0);
        let line = self.line(row);
        (row, column_of(&line, self.pos - start))
    }

    // ── Moving ───────────────────────────────────────────────────────

    /// Put the caret at a character offset, clamped to the document.
    pub fn seek(&mut self, pos: usize) {
        self.pos = pos.min(self.text.len());
        self.goal = None;
    }

    /// Put it at a row and column, clamped — what a click means.
    pub fn seek_rowcol(&mut self, row: usize, col: usize) {
        let row = row.min(self.rows() - 1);
        let start = self.text.rowpos(row).unwrap_or(0);
        let line = self.line(row);
        self.pos = start + char_of_column(&line, col);
        self.goal = None;
    }

    pub fn left(&mut self) {
        self.pos = self.pos.saturating_sub(1);
        self.goal = None;
    }

    pub fn right(&mut self) {
        self.pos = (self.pos + 1).min(self.text.len());
        self.goal = None;
    }

    pub fn up(&mut self) {
        self.vertical(-1);
    }

    pub fn down(&mut self) {
        self.vertical(1);
    }

    fn vertical(&mut self, by: i64) {
        let (row, col) = self.cursor();
        let goal = self.goal.unwrap_or(col);
        let next = (row as i64 + by).clamp(0, self.rows() as i64 - 1) as usize;
        let start = self.text.rowpos(next).unwrap_or(0);
        let line = self.line(next);
        self.pos = start + char_of_column(&line, goal);
        // Set *after* moving: `cursor()` above needed the old one.
        self.goal = Some(goal);
    }

    pub fn home(&mut self) {
        let (row, _) = self.cursor();
        self.pos = self.text.rowpos(row).unwrap_or(0);
        self.goal = None;
    }

    pub fn end(&mut self) {
        let (row, _) = self.cursor();
        self.pos = self.text.row_range(row).map(|(_, b)| b).unwrap_or(self.pos);
        self.goal = None;
    }

    // ── Editing ──────────────────────────────────────────────────────

    fn commit(&mut self, next: Rope, pos: usize) {
        self.undo.push((self.text.clone(), self.pos));
        // **A new edit ends the redo branch**, which is what every
        // editor does: once you have typed something else, the future
        // you undid is not reachable any more and pretending otherwise
        // would let a redo paste it into a document it never came from.
        self.redo.clear();
        self.text = next;
        self.pos = pos;
        self.goal = None;
    }

    // **Every edit reports whether it changed anything**, and that is
    // not decoration.  A backspace at the top of a file and a delete at
    // the bottom are the two keys people hold down; returning `Ok(())`
    // for "I did nothing" made them indistinguishable from a real edit,
    // so a host owning the file would re-read and re-save on every one.
    // Found by a test asking exactly that, which is the reason the key
    // layer is a module and not an event handler.

    /// Type something at the caret.  `false` if there was nothing to
    /// type.
    pub fn insert(&mut self, s: &str) -> Result<bool, OutOfRange> {
        if s.is_empty() {
            return Ok(false);
        }
        let next = self.text.insert(self.pos, s)?;
        self.commit(next, self.pos + s.chars().count());
        Ok(true)
    }

    /// Backspace: the character before the caret.  `false` at the top.
    pub fn backspace(&mut self) -> Result<bool, OutOfRange> {
        if self.pos == 0 {
            return Ok(false);
        }
        let next = self.text.erase(self.pos - 1, self.pos)?;
        self.commit(next, self.pos - 1);
        Ok(true)
    }

    /// Delete: the character after it.  `false` at the end.
    pub fn delete(&mut self) -> Result<bool, OutOfRange> {
        if self.pos >= self.text.len() {
            return Ok(false);
        }
        let next = self.text.erase(self.pos, self.pos + 1)?;
        self.commit(next, self.pos);
        Ok(true)
    }

    /// Erase a range, and put the caret at its start.
    pub fn erase(&mut self, start: usize, stop: usize)
        -> Result<bool, OutOfRange>
    {
        let (a, b) = (start.min(stop), start.max(stop));
        if a == b {
            return Ok(false);
        }
        let next = self.text.erase(a, b)?;
        self.commit(next, a);
        Ok(true)
    }

    /// Replace the whole document, keeping the caret where it can be.
    ///
    /// What a rebuild or a file reload does.  The caret is clamped
    /// rather than reset, because losing your place on every save is
    /// the thing that makes an editor feel like a form.
    pub fn set_text(&mut self, text: &str) {
        let pos = self.pos.min(text.chars().count());
        self.commit(Rope::from_str(text), pos);
    }

    /// Whether there is anything to undo.
    pub fn can_undo(&self) -> bool {
        !self.undo.is_empty()
    }

    pub fn can_redo(&self) -> bool {
        !self.redo.is_empty()
    }

    /// **Undo is a pointer**, which is the dividend from persistence:
    /// no diff to invert, no journal to replay, and the old document is
    /// not a reconstruction of the old document — it *is* it.
    pub fn undo(&mut self) -> bool {
        match self.undo.pop() {
            None => false,
            Some((text, pos)) => {
                self.redo.push((self.text.clone(), self.pos));
                self.text = text;
                self.pos = pos.min(self.text.len());
                self.goal = None;
                true
            }
        }
    }

    pub fn redo(&mut self) -> bool {
        match self.redo.pop() {
            None => false,
            Some((text, pos)) => {
                self.undo.push((self.text.clone(), self.pos));
                self.text = text;
                self.pos = pos.min(self.text.len());
                self.goal = None;
                true
            }
        }
    }
}

/// Which column a character offset in a line falls on.
///
/// A tab advances to the next multiple of `TAB`; everything else is one
/// column.  **Not a width in pixels** — the grid is monospaced, so a
/// column *is* the unit, and this is the only place a character and a
/// column are allowed to differ.
pub fn column_of(line: &str, at: usize) -> usize {
    let mut col = 0;
    for ch in line.chars().take(at) {
        col = if ch == '\t' { col / TAB * TAB + TAB } else { col + 1 };
    }
    col
}

/// And back: which character a column lands on, clamped to the line.
///
/// A column *inside* a tab lands on the tab, not after it — clicking
/// the middle of an indent puts the caret at the indent, which is
/// where a hand meant.
pub fn char_of_column(line: &str, col: usize) -> usize {
    let mut at = 0;
    let mut c = 0;
    for ch in line.chars() {
        if c >= col {
            return at;
        }
        let next = if ch == '\t' { c / TAB * TAB + TAB } else { c + 1 };
        if next > col {
            return at;
        }
        c = next;
        at += 1;
    }
    at
}

/// How many columns a whole line occupies.
pub fn width_of(line: &str) -> usize {
    column_of(line, line.chars().count())
}
