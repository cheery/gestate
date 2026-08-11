//! What a key means — checked without a window, which is the whole
//! reason `keys` is a module rather than an event handler.

use gestate_editor::document::Document;
use gestate_editor::font::LARGE;
use gestate_editor::keys::{click, press, scroll, Key, Mods};
use gestate_editor::view::View;

fn setup(text: &str, rows: usize) -> (Document, View) {
    (Document::new(text),
     View { top: 0, left: 0, w: 600, h: rows as i32 * LARGE.h, gutter: false, scale: 1 })
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
