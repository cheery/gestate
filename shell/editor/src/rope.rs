//! The rope — `gestate/balanced.py`, in Rust.
//!
//! A **persistent AVL tree of text segments**, where every node carries
//! its own summaries: how many characters are under it and how many
//! newlines.  Those two are the whole reason it is a tree rather than a
//! string: `row(pos)` and `rowpos(row)` descend by comparing against a
//! child's summary, so finding line four hundred costs the depth of the
//! tree rather than a scan.
//!
//! **Persistent, and that is a deliberate cost.**  Every edit returns a
//! new tree sharing all the structure it did not touch, so the old one
//! is still there and still valid.  An editor wants that: undo is a
//! stack of roots, a background rebuild can hold the version it started
//! from while you keep typing, and nothing has to be copied to be safe.
//! `Rc` rather than `Arc` because a document belongs to the thread
//! showing it — the audio thread never sees one.
//!
//! **Positions are characters, not bytes**, which is `balanced.py`'s
//! choice and is kept because that file is the oracle: the two must
//! answer alike or the port is not a port.  It is also the right unit
//! for the thing on top — a cursor moves by characters, and a column is
//! a count of them.  Segments are small (`SPLIT` characters), so the
//! byte offset of a character inside one is a short scan rather than a
//! second index to maintain.

use std::rc::Rc;

/// How long a segment is allowed to get before an insert splits it
/// instead of rewriting it.
///
/// **`balanced.py` used eight and this uses a hundred and twenty-eight,
/// which is the one number the port deliberately changed.**  Eight is a
/// toy's answer: a five-megabyte file is six hundred thousand nodes,
/// each an `Rc` with a `String` in it, and the tree costs more than the
/// text it holds.  At 128 the same file is forty thousand nodes, an
/// insert rewrites at most 128 characters (nothing), and a scan inside
/// a segment is 128 characters (nothing).
///
/// It is safe to change because **the parity fixture compares answers,
/// not shape** — `len`, `row`, `rowpos`, `read` and the text itself are
/// all facts about the document rather than about the tree, so the two
/// implementations agree while being shaped quite differently.  That
/// was stated when the fixture was written, and this is the change it
/// was stated for.
const SPLIT: usize = 128;

#[derive(Clone, Debug)]
struct Node {
    text: String,
    /// The segment's own length in **characters**, cached because every
    /// descent needs it and `str::chars().count()` is a walk.
    chars: usize,
    left: Rope,
    right: Rope,
    height: u32,
    /// Characters under this node, its own text included.
    length: usize,
    /// Newlines under this node, its own text included.
    newlines: usize,
}

/// A document, or a piece of one.  Cheap to clone: it is one pointer.
#[derive(Clone, Debug, Default)]
pub struct Rope(Option<Rc<Node>>);

/// **Same contents, however they were arrived at.**
///
/// Written rather than derived, for the fast path: two ropes that share
/// a root *are* the same text, and that is the common case the caller
/// cares about — undo restores the very root it took, so asking whether
/// the document is back where it was saved is one pointer comparison.
/// Different roots fall back to length and then to contents, which is
/// the honest answer for text retyped the same.
impl PartialEq for Rope {
    fn eq(&self, other: &Rope) -> bool {
        match (&self.0, &other.0) {
            (None, None) => true,
            (Some(a), Some(b)) if Rc::ptr_eq(a, b) => true,
            _ => self.len() == other.len() && self.text() == other.text(),
        }
    }
}

impl Eq for Rope {}

/// What went wrong, which for a rope is always the same thing.
#[derive(Clone, PartialEq, Eq, Debug)]
pub struct OutOfRange;

type R<T> = Result<T, OutOfRange>;

fn byte_of(text: &str, chars: usize) -> usize {
    text.char_indices().nth(chars).map(|(i, _)| i).unwrap_or(text.len())
}

fn slice(text: &str, from: usize, to: usize) -> &str {
    let a = byte_of(text, from);
    let b = byte_of(text, to);
    &text[a..b.max(a)]
}

impl Rope {
    pub fn new() -> Rope {
        Rope(None)
    }

    /// A whole document, as a **balanced tree built bottom-up**.
    ///
    /// The obvious thing is one segment holding everything, which
    /// `balanced.py` does and which is defensible on the argument that
    /// loading a file should cost one allocation and the tree can earn
    /// its shape as it is used.  Measured, that argument is wrong: a
    /// two-hundred-thousand-line file loaded as one segment made every
    /// `rowpos` a linear scan of five million characters, and drawing
    /// the fifty lines at row 199,000 took **1.5 seconds** — the rope
    /// was decorative until the file had been edited enough to break
    /// itself up.
    ///
    /// Chunking first costs one pass over the text and gives a tree
    /// that is balanced by construction, since a midpoint split always
    /// is.  The same frame then takes microseconds.
    pub fn from_str(text: &str) -> Rope {
        Rope::chunked(text)
    }

    /// Split into segments and build a balanced tree over them.
    fn chunked(text: &str) -> Rope {
        if text.is_empty() {
            return Rope::new();
        }
        let mut chunks: Vec<&str> = Vec::new();
        let mut start = 0;
        let mut n = 0;
        for (i, _) in text.char_indices() {
            if n == SPLIT {
                chunks.push(&text[start..i]);
                start = i;
                n = 0;
            }
            n += 1;
        }
        if start < text.len() {
            chunks.push(&text[start..]);
        }
        Rope::from_chunks(&chunks)
    }

    /// A balanced tree over a slice of segments — the midpoint becomes
    /// the root, so the two sides differ in height by at most one and
    /// no rotation is ever needed.
    fn from_chunks(chunks: &[&str]) -> Rope {
        if chunks.is_empty() {
            return Rope::new();
        }
        let mid = chunks.len() / 2;
        Rope::leaf(chunks[mid].to_string(),
                   Rope::from_chunks(&chunks[..mid]),
                   Rope::from_chunks(&chunks[mid + 1..]))
    }

    /// Two trees, end to end.
    pub fn concat(left: Rope, right: Rope) -> Rope {
        Rope::pluck(left, right)
    }

    fn leaf(text: String, left: Rope, right: Rope) -> Rope {
        let chars = text.chars().count();
        let newlines = text.bytes().filter(|b| *b == b'\n').count();
        Rope(Some(Rc::new(Node {
            chars,
            length: chars + left.len() + right.len(),
            newlines: newlines + left.newlines() + right.newlines(),
            height: 1 + left.height().max(right.height()),
            text,
            left,
            right,
        })))
    }

    /// This node's text, with different children — `retain` in the
    /// Python, and the reason a rotation costs one allocation per node
    /// it touches rather than a copy of the subtree.
    fn retain(&self, left: Rope, right: Rope) -> Rope {
        match &self.0 {
            None => Rope::new(),
            Some(n) => Rope::leaf(n.text.clone(), left, right),
        }
    }

    pub fn is_empty(&self) -> bool {
        self.0.is_none()
    }

    /// Length in characters.
    pub fn len(&self) -> usize {
        self.0.as_ref().map_or(0, |n| n.length)
    }

    pub fn newlines(&self) -> usize {
        self.0.as_ref().map_or(0, |n| n.newlines)
    }

    /// How many lines the document has — one more than its newlines,
    /// because the last line needs no terminator to exist.
    pub fn rows(&self) -> usize {
        self.newlines() + 1
    }

    fn height(&self) -> u32 {
        self.0.as_ref().map_or(0, |n| n.height)
    }

    fn balance(&self) -> i32 {
        match &self.0 {
            None => 0,
            Some(n) => n.left.height() as i32 - n.right.height() as i32,
        }
    }

    fn node(&self) -> &Node {
        self.0.as_ref().expect("an empty rope has no node")
    }

    // ── The AVL half, which knows nothing about text ─────────────────

    fn rebalance(self) -> Rope {
        let b = self.balance();
        if b > 1 {
            let n = self.node();
            if n.left.balance() >= 0 {
                return self.right_rotate();
            }
            let temp = self.retain(n.left.clone().left_rotate(), n.right.clone());
            return temp.right_rotate();
        }
        if b < -1 {
            let n = self.node();
            if n.right.balance() <= 0 {
                return self.left_rotate();
            }
            let temp = self.retain(n.left.clone(), n.right.clone().right_rotate());
            return temp.left_rotate();
        }
        self
    }

    fn right_rotate(self) -> Rope {
        let z = self.node();
        let x = z.left.clone();
        let y = x.node().right.clone();
        let lower = self.retain(y, z.right.clone());
        x.retain(x.node().left.clone(), lower)
    }

    fn left_rotate(self) -> Rope {
        let x = self.node();
        let z = x.right.clone();
        let y = z.node().left.clone();
        let lower = self.retain(x.left.clone(), y);
        z.retain(lower, z.node().right.clone())
    }

    /// Rebuild a node from a segment and two subtrees **of any
    /// heights** — the balanced-tree `join`.
    ///
    /// **This is where the port stopped being a port, and it is worth
    /// the paragraph.**  `balanced.py` reconstructs with `retain`
    /// followed by one `rebalance`, which is the textbook AVL move and
    /// is correct when an edit moves *one* node: a single insert or
    /// delete changes a subtree's height by at most one, so one
    /// rotation per level on the way out restores the invariant.
    ///
    /// A rope's edits are **bulk**.  One `erase` can take most of a
    /// subtree away and one `insert` can graft several levels on, so a
    /// node can come back with children five levels apart — and one
    /// rotation cannot fix that, it only moves the imbalance down to a
    /// child where nothing will look at it again.  Measured on the
    /// reference: four thousand random edits leave nodes at
    /// `|balance| = 4`, and the answers are all still *correct*, which
    /// is exactly why it went unnoticed — a rope that loses its balance
    /// does not give wrong text, it gives right text more slowly, and
    /// only a test that looks at the shape can tell.
    ///
    /// `join` descends the taller side's spine to a node of the right
    /// height and splices there, costing the difference in heights;
    /// every node it rebuilds is one level out at worst, so the single
    /// `rebalance` those need is the move that *is* enough.
    fn join(left: Rope, text: String, right: Rope) -> Rope {
        if left.height() > right.height() + 1 {
            let n = left.node();
            let lowered = Rope::join(n.right.clone(), text, right);
            return Rope::leaf(n.text.clone(), n.left.clone(), lowered)
                .rebalance();
        }
        if right.height() > left.height() + 1 {
            let n = right.node();
            let lowered = Rope::join(left, text, n.left.clone());
            return Rope::leaf(n.text.clone(), lowered, n.right.clone())
                .rebalance();
        }
        Rope::leaf(text, left, right)
    }

    /// The leftmost segment, and the rest of the tree without it.
    fn take_first(&self) -> (String, Rope) {
        let n = self.node();
        if n.left.is_empty() {
            return (n.text.clone(), n.right.clone());
        }
        let (text, rest) = n.left.take_first();
        (text, Rope::join(rest, n.text.clone(), n.right.clone()))
    }

    /// Join two trees with nothing between them — what erasing a whole
    /// segment leaves.  The successor becomes the new middle, and
    /// `join` puts it wherever the two heights say it belongs.
    fn pluck(left: Rope, right: Rope) -> Rope {
        if left.is_empty() {
            return right;
        }
        if right.is_empty() {
            return left;
        }
        let (text, rest) = right.take_first();
        Rope::join(left, text, rest)
    }

    // ── Reading ──────────────────────────────────────────────────────

    /// The text between two character positions, pushed onto `out` as
    /// the segments it is made of.
    ///
    /// Segments rather than a `String` because that is what the caller
    /// usually wants — drawing a line writes each piece straight into
    /// the frame — and joining them is the cheap direction.
    pub fn segments<'a>(&'a self, start: usize, stop: usize,
                        out: &mut Vec<&'a str>) -> R<()> {
        let Some(n) = &self.0 else {
            return if start == 0 && stop == 0 { Ok(()) } else { Err(OutOfRange) };
        };
        let ledge = n.left.len();
        let redge = ledge + n.chars;
        if start < ledge {
            n.left.segments(start, stop.min(ledge), out)?;
        }
        // **Only when the range reaches this node's own text.**  A read
        // lying entirely inside the left child must add nothing here;
        // `balanced.py` carries the same guard and the comment beside
        // it, having once handed back a trimmed copy of the segment
        // because the index it computed went negative.
        if start < redge && ledge < stop {
            let x = start.max(ledge) - ledge;
            let y = (stop.min(redge) - ledge).max(x);
            out.push(slice(&n.text, x, y));
        }
        if redge < stop {
            n.right.segments(start.saturating_sub(redge), stop - redge, out)?;
        }
        Ok(())
    }

    /// The whole text between two positions.
    pub fn read(&self, start: usize, stop: usize) -> R<String> {
        let mut parts = Vec::new();
        self.segments(start, stop, &mut parts)?;
        Ok(parts.concat())
    }

    pub fn text(&self) -> String {
        self.read(0, self.len()).expect("a full read is always in range")
    }

    /// Which row a character position falls on, counting from zero.
    pub fn row(&self, pos: usize) -> R<usize> {
        let Some(n) = &self.0 else {
            return if pos == 0 { Ok(0) } else { Err(OutOfRange) };
        };
        let ledge = n.left.len();
        if pos <= ledge {
            return n.left.row(pos);
        }
        let redge = ledge + n.chars;
        if redge < pos {
            let row = n.right.row(pos - redge)?;
            return Ok(row + n.newlines - n.right.newlines());
        }
        let cut = pos - ledge;
        let counted = slice(&n.text, 0, cut).bytes()
            .filter(|b| *b == b'\n').count();
        Ok(counted + n.left.newlines())
    }

    /// Where a row begins, as a character position.
    pub fn rowpos(&self, row: usize) -> R<usize> {
        let Some(n) = &self.0 else {
            return if row == 0 { Ok(0) } else { Err(OutOfRange) };
        };
        if row <= n.left.newlines() {
            return n.left.rowpos(row);
        }
        let redge = n.newlines - n.right.newlines();
        if row <= redge {
            let mut count = n.left.newlines();
            for (i, ch) in n.text.chars().enumerate() {
                if ch == '\n' {
                    count += 1;
                    if count == row {
                        return Ok(n.left.len() + i + 1);
                    }
                }
            }
        }
        let pos = n.right.rowpos(row - redge)?;
        Ok(pos + n.chars + n.left.len())
    }

    /// The character range of one row, its newline excluded.
    pub fn row_range(&self, row: usize) -> R<(usize, usize)> {
        let start = self.rowpos(row)?;
        let end = if row + 1 < self.rows() {
            self.rowpos(row + 1)?.saturating_sub(1)
        } else {
            self.len()
        };
        Ok((start, end.max(start)))
    }

    /// One row's text, without its newline.
    pub fn line(&self, row: usize) -> R<String> {
        let (a, b) = self.row_range(row)?;
        self.read(a, b)
    }

    // ── Writing ──────────────────────────────────────────────────────

    /// Insert text at a character position.
    pub fn insert(&self, pos: usize, text: &str) -> R<Rope> {
        if text.is_empty() {
            return Ok(self.clone());
        }
        let Some(n) = &self.0 else {
            return if pos == 0 {
                Ok(Rope::chunked(text))
            } else {
                Err(OutOfRange)
            };
        };
        let ledge = n.left.len();
        let redge = ledge + n.chars;
        // **Through `join`, not `retain`.**  Inserting a long string
        // into a child grafts a whole subtree onto it, so the child can
        // come back several levels taller than its sibling — see
        // `join`.
        let node = if pos < ledge {
            return Ok(Rope::join(n.left.insert(pos, text)?, n.text.clone(),
                                 n.right.clone()));
        } else if pos > redge {
            return Ok(Rope::join(n.left.clone(), n.text.clone(),
                                 n.right.insert(pos - redge, text)?));
        } else {
            let cut = pos - ledge;
            if n.chars + text.chars().count() > SPLIT {
                // **The segment splits and the new text goes between
                // the halves.**  Chunked, because a paste is an insert
                // too and a megabyte arriving as one segment is the
                // same fault `from_str` was measured on.
                let left = Rope::concat(n.left.clone(),
                                        Rope::chunked(slice(&n.text, 0, cut)));
                let right = Rope::concat(Rope::chunked(slice(&n.text, cut, n.chars)),
                                         n.right.clone());
                Rope::concat(Rope::concat(left, Rope::chunked(text)), right)
            } else {
                let mut joined = String::with_capacity(n.text.len() + text.len());
                joined.push_str(slice(&n.text, 0, cut));
                joined.push_str(text);
                joined.push_str(slice(&n.text, cut, n.chars));
                Rope::leaf(joined, n.left.clone(), n.right.clone())
            }
        };
        Ok(node.rebalance())
    }

    /// Erase a half-open character range.
    pub fn erase(&self, start: usize, stop: usize) -> R<Rope> {
        let Some(n) = &self.0 else {
            return if start == 0 && stop == 0 {
                Ok(Rope::new())
            } else {
                Err(OutOfRange)
            };
        };
        let ledge = n.left.len();
        let redge = ledge + n.chars;
        let left = if start < ledge {
            n.left.erase(start, stop.min(ledge))?
        } else {
            n.left.clone()
        };
        let right = if redge < stop {
            n.right.erase(start.saturating_sub(redge), stop - redge)?
        } else {
            n.right.clone()
        };
        let node = if start < redge && ledge < stop {
            let a = start.clamp(ledge, redge) - ledge;
            let b = stop.clamp(ledge, redge) - ledge;
            let mut kept = String::new();
            kept.push_str(slice(&n.text, 0, a));
            kept.push_str(slice(&n.text, b, n.chars));
            if kept.is_empty() {
                Rope::pluck(left, right)
            } else {
                Rope::join(left, kept, right)
            }
        } else {
            Rope::join(left, n.text.clone(), right)
        };
        Ok(node.rebalance())
    }

    // ── What a test wants to know ────────────────────────────────────

    /// The tree's depth, for the invariant check below.
    pub fn depth(&self) -> u32 {
        self.height()
    }

    /// Whether every node is balanced and every summary agrees with
    /// what is actually under it.
    ///
    /// **Checked rather than trusted**, because the summaries are the
    /// only reason the descents are fast and a wrong one is a wrong
    /// answer rather than a slow one — `row` would name the wrong line
    /// and nothing would crash.
    pub fn is_sound(&self) -> bool {
        let Some(n) = &self.0 else { return true };
        let chars = n.text.chars().count();
        let newlines = n.text.bytes().filter(|b| *b == b'\n').count();
        n.chars == chars
            && n.length == chars + n.left.len() + n.right.len()
            && n.newlines == newlines + n.left.newlines() + n.right.newlines()
            && n.height == 1 + n.left.height().max(n.right.height())
            && self.balance().abs() <= 1
            && n.left.is_sound()
            && n.right.is_sound()
    }
}

impl From<&str> for Rope {
    fn from(s: &str) -> Rope {
        Rope::from_str(s)
    }
}
