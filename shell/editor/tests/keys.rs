//! What a key means — checked without a window, which is the whole
//! reason `keys` is a module rather than an event handler.

use gestate_editor::document::Document;
use gestate_editor::font::LARGE;
use gestate_editor::keys::{click, press, scroll, Key, Mods};
use gestate_editor::view::View;

fn setup(text: &str, rows: usize) -> (Document, View) {
    // **Sized for the rows it wants, status line included.**  The
    // window is not all text: one row at the foot says what just
    // happened, so a test that asks for ten rows has to pay for it.
    let v = View { top: 0, left: 0, w: 600, h: 0, gutter: false,
                   aside: 0, scale: 1 };
    let h = rows as i32 * v.ch(&LARGE) + v.status_h(&LARGE);
    (Document::new(text), View { h, ..v })
}

fn tap(d: &mut Document, v: &mut View, k: Key) -> gestate_editor::keys::Did {
    press(d, v, &LARGE, k, Mods::default())
}

#[test]
fn typing_says_it_edited_and_moving_says_it_did_not() {
    let (mut d, mut v) = setup("ab", 10);
    let did = tap(&mut d, &mut v, Key::Char('x'));
    assert!(did.edited && did.drew);
    let did = tap(&mut d, &mut v, Key::Right);
    assert!(!did.edited && did.drew, "a motion is not an edit");
    assert_eq!(d.text(), "xab");
}

/// **A tab is a tab.**  Turning it into spaces on the way in is a
/// decision about somebody else's file that an editor should not make
/// quietly.
#[test]
fn tab_types_a_tab_and_the_view_expands_it() {
    let (mut d, mut v) = setup("", 10);
    tap(&mut d, &mut v, Key::Tab);
    tap(&mut d, &mut v, Key::Char('x'));
    assert_eq!(d.text(), "\tx");
    assert_eq!(d.cursor(), (0, 5), "one character, five columns");
}

#[test]
fn enter_opens_a_line() {
    let (mut d, mut v) = setup("ab", 10);
    d.seek(1);
    tap(&mut d, &mut v, Key::Enter);
    assert_eq!(d.text(), "a\nb");
    assert_eq!(d.cursor(), (1, 0));
    assert_eq!(d.rows(), 2);
}

/// **A page is a screen minus a line**, so one line of what you were
/// reading is still there afterwards.
#[test]
fn a_page_keeps_a_line_of_context() {
    let text: String = (0..200).map(|i| format!("row {i}\n")).collect();
    let (mut d, mut v) = setup(&text, 10);
    tap(&mut d, &mut v, Key::PageDown);
    assert_eq!(d.cursor().0, 9, "ten rows fit, so a page is nine");
    tap(&mut d, &mut v, Key::PageDown);
    assert_eq!(d.cursor().0, 18);
    tap(&mut d, &mut v, Key::PageUp);
    assert_eq!(d.cursor().0, 9);
    // And it keeps the column, the way an arrow does.
    d.seek_rowcol(50, 4);
    tap(&mut d, &mut v, Key::PageDown);
    assert_eq!(d.cursor(), (59, 4));
}

#[test]
fn the_ends_of_the_document_are_reachable() {
    let (mut d, mut v) = setup("one\ntwo\nthree", 2);
    tap(&mut d, &mut v, Key::Bottom);
    assert_eq!(d.pos(), d.len());
    assert!(v.top > 0, "the view followed to the end");
    tap(&mut d, &mut v, Key::Top);
    assert_eq!((d.pos(), v.top), (0, 0));
}

/// A motion must leave the caret where it can be seen, or it is a
/// motion whose result you cannot look at.
#[test]
fn every_key_leaves_the_caret_on_screen() {
    let text: String = (0..300).map(|i| format!("row {i}\n")).collect();
    let (mut d, mut v) = setup(&text, 12);
    for k in [Key::Bottom, Key::Top, Key::PageDown, Key::PageDown,
              Key::Up, Key::End, Key::Home, Key::Down, Key::Enter,
              Key::Backspace] {
        tap(&mut d, &mut v, k.clone());
        let (row, col) = d.cursor();
        assert!(row >= v.top && row < v.top + v.rows(&LARGE),
                "after {k:?}: row {row} is outside {}..{}",
                v.top, v.top + v.rows(&LARGE));
        assert!(col >= v.left, "after {k:?}: column {col} is left of the view");
    }
}

/// **Scrolling is not navigating.**  Looking somewhere else must not
/// lose your place.
#[test]
fn the_wheel_moves_the_view_and_not_the_caret() {
    let text: String = (0..100).map(|i| format!("row {i}\n")).collect();
    let (d, mut v) = setup(&text, 10);
    let was = d.pos();
    let did = scroll(&d, &mut v, &LARGE, 12);
    assert!(did.drew && !did.edited);
    assert_eq!(v.top, 12);
    assert_eq!(d.pos(), was, "the wheel dragged the caret");

    // It stops at the ends rather than running off.
    scroll(&d, &mut v, &LARGE, -500);
    assert_eq!(v.top, 0);
    scroll(&d, &mut v, &LARGE, 5000);
    assert_eq!(v.top, d.rows() - v.rows(&LARGE));
}

#[test]
fn a_click_puts_the_caret_where_the_pointer_is() {
    let (mut d, v) = setup("hello\nworld", 10);
    click(&mut d, &v, &LARGE, LARGE.w * 3 + 2, LARGE.h + 1);
    assert_eq!(d.cursor(), (1, 3));
    // Past the end of a line lands at its end, not on the next one.
    click(&mut d, &v, &LARGE, LARGE.w * 99, LARGE.h + 1);
    assert_eq!(d.cursor(), (1, 5));
}

#[test]
fn undo_and_redo_are_keys_like_any_other() {
    let (mut d, mut v) = setup("", 10);
    tap(&mut d, &mut v, Key::Char('a'));
    tap(&mut d, &mut v, Key::Char('b'));
    assert_eq!(d.text(), "ab");
    let did = tap(&mut d, &mut v, Key::Undo);
    assert!(did.edited, "an undo changes the text");
    assert_eq!(d.text(), "a");
    tap(&mut d, &mut v, Key::Redo);
    assert_eq!(d.text(), "ab");
    // Nothing to undo is not an error, and reports nothing happened.
    while tap(&mut d, &mut v, Key::Undo).edited {}
    let did = tap(&mut d, &mut v, Key::Undo);
    assert!(!did.edited && !did.drew);
}

/// Backspace at the very top and delete at the very bottom do nothing,
/// rather than failing — a held key must not be an error.
#[test]
fn the_edges_are_quiet() {
    let (mut d, mut v) = setup("x", 10);
    d.seek(0);
    for _ in 0..5 {
        assert!(!tap(&mut d, &mut v, Key::Backspace).edited);
    }
    d.seek(d.len());
    for _ in 0..5 {
        assert!(!tap(&mut d, &mut v, Key::Delete).edited);
    }
    assert_eq!(d.text(), "x");
}

/// Typing a lot is not quadratic — the thing that decides whether an
/// editor feels alive.
#[test]
fn typing_into_a_large_document_stays_cheap() {
    let text: String = (0..20_000).map(|i| format!("line {i}\n")).collect();
    let (mut d, mut v) = setup(&text, 40);
    d.seek_rowcol(10_000, 0);
    for c in "the quick brown fox jumps over the lazy dog".chars() {
        tap(&mut d, &mut v, Key::Char(c));
    }
    assert!(d.rope().is_sound(), "typing unbalanced the tree");
    assert!(d.line(10_000).starts_with("the quick brown fox"));
    assert_eq!(d.rows(), 20_001);
}

// ── Selection and the clipboard ──────────────────────────────────────────

use gestate_editor::keys::{press_with, Clipboard, Memory};

fn shift(d: &mut Document, v: &mut View, k: Key) -> gestate_editor::keys::Did {
    press(d, v, &LARGE, k, Mods { ctrl: false, shift: true })
}

fn with(d: &mut Document, v: &mut View, c: &mut Memory, k: Key)
    -> gestate_editor::keys::Did
{
    press_with(d, v, &LARGE, k, Mods::default(), c)
}

/// **Shift anchors where the caret was, not where it arrives.**
/// Deciding afterwards would anchor it at the destination and select
/// nothing.
#[test]
fn a_shifted_motion_selects_what_it_passed_over() {
    let (mut d, mut v) = setup("hello world", 10);
    d.seek(0);
    for _ in 0..5 {
        shift(&mut d, &mut v, Key::Right);
    }
    assert_eq!(d.selection(), Some((0, 5)));
    assert_eq!(d.selected(), "hello");
    // Growing and shrinking move the same end.
    shift(&mut d, &mut v, Key::Left);
    assert_eq!(d.selected(), "hell");
    // And an unshifted motion drops it.
    tap(&mut d, &mut v, Key::Right);
    assert_eq!(d.selection(), None);
}

#[test]
fn shift_and_the_row_keys_select_lines() {
    let (mut d, mut v) = setup("one\ntwo\nthree", 10);
    d.seek(0);
    shift(&mut d, &mut v, Key::Down);
    assert_eq!(d.selected(), "one\n");
    shift(&mut d, &mut v, Key::End);
    assert_eq!(d.selected(), "one\ntwo");
    shift(&mut d, &mut v, Key::Bottom);
    assert_eq!(d.selected(), "one\ntwo\nthree");
}

/// An anchor *at* the caret is not a selection — a shifted motion that
/// has not moved yet.
#[test]
fn shift_with_nowhere_to_go_selects_nothing() {
    let (mut d, mut v) = setup("x", 10);
    d.seek(0);
    shift(&mut d, &mut v, Key::Left);
    assert_eq!(d.selection(), None);
    assert_eq!(d.selected(), "");
}

/// **Typing over a selection replaces it, in one undo step.**  Two
/// steps would put the caret in a hole when you undid, with the text
/// gone and the selection not back.
#[test]
fn typing_over_a_selection_replaces_it() {
    let (mut d, mut v) = setup("hello world", 10);
    d.select(0, 5);
    tap(&mut d, &mut v, Key::Char('!'));
    assert_eq!(d.text(), "! world");
    assert_eq!(d.selection(), None);
    assert!(d.undo());
    assert_eq!(d.text(), "hello world", "one edit, one undo");
}

#[test]
fn backspace_and_delete_take_the_selection_when_there_is_one() {
    let (mut d, mut v) = setup("hello world", 10);
    d.select(0, 6);
    tap(&mut d, &mut v, Key::Backspace);
    assert_eq!(d.text(), "world");
    d.select(0, 2);
    tap(&mut d, &mut v, Key::Delete);
    assert_eq!(d.text(), "rld");
}

#[test]
fn copy_cut_and_paste() {
    let (mut d, mut v) = setup("hello world", 10);
    let mut c = Memory::default();

    d.select(0, 5);
    let did = with(&mut d, &mut v, &mut c, Key::Copy);
    assert!(!did.edited, "copying does not change the text");
    assert_eq!(c.get(), "hello");
    assert_eq!(d.text(), "hello world");

    d.select(6, 11);
    with(&mut d, &mut v, &mut c, Key::Cut);
    assert_eq!(c.get(), "world");
    assert_eq!(d.text(), "hello ");
    assert_eq!(d.pos(), 6);

    with(&mut d, &mut v, &mut c, Key::Paste);
    assert_eq!(d.text(), "hello world");
    assert_eq!(d.pos(), 11, "the caret lands after what was pasted");

    // Pasting over a selection replaces it.
    d.select(0, 5);
    with(&mut d, &mut v, &mut c, Key::Paste);
    assert_eq!(d.text(), "world world");
}

/// **Copying nothing leaves the clipboard alone.**  Ctrl-C with no
/// selection is a miss, and emptying what you copied a moment ago is
/// the worst possible answer to one.
#[test]
fn copying_nothing_does_not_empty_the_clipboard() {
    let (mut d, mut v) = setup("abc", 10);
    let mut c = Memory::default();
    c.set("kept");
    d.clear_anchor();
    with(&mut d, &mut v, &mut c, Key::Copy);
    assert_eq!(c.get(), "kept");
    with(&mut d, &mut v, &mut c, Key::Cut);
    assert_eq!(c.get(), "kept");
    assert_eq!(d.text(), "abc", "cutting nothing cuts nothing");
}

#[test]
fn select_all_and_replace() {
    let (mut d, mut v) = setup("one\ntwo\n", 10);
    tap(&mut d, &mut v, Key::SelectAll);
    assert_eq!(d.selected(), "one\ntwo\n");
    let mut c = Memory::default();
    with(&mut d, &mut v, &mut c, Key::Cut);
    assert_eq!(d.text(), "");
    assert_eq!(d.rows(), 1);
    with(&mut d, &mut v, &mut c, Key::Paste);
    assert_eq!(d.text(), "one\ntwo\n");
}

/// A click drops the selection; a drag extends from where the button
/// went down.
#[test]
fn dragging_selects_and_clicking_does_not() {
    use gestate_editor::keys::drag;
    let (mut d, v) = setup("hello world", 10);
    click(&mut d, &v, &LARGE, LARGE.w * 6, 1);
    assert_eq!(d.selection(), None);
    assert_eq!(d.pos(), 6);
    drag(&mut d, &v, &LARGE, LARGE.w * 11, 1);
    assert_eq!(d.selected(), "world");
    // A plain click afterwards puts it away again.
    click(&mut d, &v, &LARGE, 0, 1);
    assert_eq!(d.selection(), None);
}

/// Undo puts the text back and does not leave a selection pointing
/// into a document that no longer has those characters.
#[test]
fn undo_after_a_replacement_leaves_no_stale_selection() {
    let (mut d, mut v) = setup("abcdef", 10);
    d.select(1, 5);
    tap(&mut d, &mut v, Key::Char('X'));
    assert_eq!(d.text(), "aXf");
    assert!(d.undo());
    assert_eq!(d.text(), "abcdef");
    assert_eq!(d.selection(), None);
    assert!(d.pos() <= d.len());
}
