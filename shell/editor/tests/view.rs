//! What a frame promises, checked without a window.
//!
//! The layout is the one thing about an editor a test can pin exactly.
//! Whether it is *pleasant* is a thing a person has to look at; whether
//! the caret is on the character you typed, whether a click lands where
//! you clicked, and whether scrolling a million-line file costs the
//! rows on screen are not.

use gestate_editor::document::{char_of_column, column_of, width_of, Document};
use gestate_editor::font::LARGE;
use gestate_editor::view::{caret_at, frame, paint, Item, View, CARET};
use gestate_panel::list::Colour;
use gestate_panel::paint::Canvas;

fn doc(text: &str) -> Document {
    Document::new(text)
}

fn runs(f: &gestate_editor::view::Frame) -> Vec<String> {
    f.items.iter().filter_map(|i| match i {
        Item::Run { s, .. } => Some(s.clone()),
        _ => None,
    }).collect()
}

fn view(w: i32, h: i32) -> View {
    View { top: 0, left: 0, w, h, gutter: false, scale: 1 }
}

// ── The document ─────────────────────────────────────────────────────────

#[test]
fn typing_puts_the_caret_after_what_was_typed() {
    let mut d = doc("");
    d.insert("hello").unwrap();
    assert_eq!(d.text(), "hello");
    assert_eq!(d.pos(), 5);
    assert_eq!(d.cursor(), (0, 5));
    d.insert("\nworld").unwrap();
    assert_eq!(d.cursor(), (1, 5));
    assert_eq!(d.rows(), 2);
}

#[test]
fn backspace_and_delete_take_one_character_each_way() {
    let mut d = doc("abc");
    d.seek(2);
    d.backspace().unwrap();
    assert_eq!((d.text(), d.pos()), ("ac".to_string(), 1));
    d.delete().unwrap();
    assert_eq!((d.text(), d.pos()), ("a".to_string(), 1));
    // At the edges they do nothing rather than erroring — a held
    // backspace at the top of a file must not be a failure.
    d.seek(0);
    d.backspace().unwrap();
    assert_eq!(d.text(), "a");
    d.seek(d.len());
    d.delete().unwrap();
    assert_eq!(d.text(), "a");
}

/// **A short line must not eat the column.**  Going down from column 40
/// through a three-character line and on should arrive back at 40.
#[test]
fn a_vertical_motion_remembers_the_column_it_wanted() {
    let mut d = doc("0123456789\nab\n0123456789");
    d.seek(8);
    assert_eq!(d.cursor(), (0, 8));
    d.down();
    assert_eq!(d.cursor(), (1, 2), "clamped to the short line");
    d.down();
    assert_eq!(d.cursor(), (2, 8), "and back to the column it wanted");
    // A horizontal motion is about columns, so it forgets the goal.
    d.up();
    d.left();
    d.down();
    assert_eq!(d.cursor().1, 1, "the goal was cleared by moving sideways");
}

#[test]
fn home_and_end_and_the_edges() {
    let mut d = doc("  indented\nnext");
    d.seek(5);
    d.end();
    assert_eq!(d.cursor(), (0, 10));
    d.home();
    assert_eq!(d.cursor(), (0, 0));
    d.up();
    assert_eq!(d.cursor(), (0, 0), "up from the first row stays");
    d.seek(d.len());
    d.down();
    assert_eq!(d.cursor().0, 1, "down from the last row stays");
}

/// A tab is one character and four columns, and that is the only place
/// the two differ.
#[test]
fn tabs_are_columns_not_characters() {
    assert_eq!(column_of("\tx", 0), 0);
    assert_eq!(column_of("\tx", 1), 4, "past the tab");
    assert_eq!(column_of("\tx", 2), 5);
    assert_eq!(column_of("ab\tc", 3), 4, "the tab fills to the next stop");
    assert_eq!(width_of("\t\t"), 8);

    // A column inside a tab lands *on* the tab — clicking the middle of
    // an indent puts the caret at the indent, which is where a hand
    // meant.
    assert_eq!(char_of_column("\tx", 0), 0);
    assert_eq!(char_of_column("\tx", 2), 0);
    assert_eq!(char_of_column("\tx", 4), 1);
    assert_eq!(char_of_column("\tx", 99), 2, "clamped to the line");

    let mut d = doc("\thello");
    d.seek(1);
    assert_eq!(d.cursor(), (0, 4));
}

#[test]
fn undo_is_a_pointer_and_redo_ends_at_a_new_edit() {
    let mut d = doc("");
    d.insert("one").unwrap();
    d.insert(" two").unwrap();
    assert_eq!(d.text(), "one two");
    assert!(d.undo());
    assert_eq!(d.text(), "one");
    assert!(d.redo());
    assert_eq!(d.text(), "one two");
    assert!(d.undo());
    d.insert("!").unwrap();
    assert_eq!(d.text(), "one!");
    assert!(!d.can_redo(), "a new edit ends the branch that was undone");
    while d.undo() {}
    assert_eq!(d.text(), "");
    assert!(!d.can_undo());
}

// ── The frame ────────────────────────────────────────────────────────────

#[test]
fn a_frame_is_a_pure_function() {
    let d = doc("one\ntwo\nthree");
    let v = view(400, 200);
    assert_eq!(frame(&d, &v, &LARGE), frame(&d, &v, &LARGE));
}

/// **Only the visible rows are read**, which is the whole reason the
/// document is a tree.  A viewport that read the file to draw a screen
/// would make the rope decorative.
#[test]
fn a_tall_document_costs_only_the_rows_on_screen() {
    let text: String = (0..200_000).map(|i| format!("line {i}\n")).collect();
    let mut d = doc(&text);
    assert!(d.rows() > 200_000);

    // Ten rows fit; ten runs of text come out, however deep in we look.
    let mut v = View { top: 0, left: 0, w: 600, h: 10 * LARGE.h, gutter: false, scale: 1 };
    v.top = 180_000;
    d.seek_rowcol(180_003, 2);
    let f = frame(&d, &v, &LARGE);
    let lines = runs(&f);
    assert_eq!(lines.len(), 10, "drew {} runs for ten rows", lines.len());
    assert_eq!(lines[0], "line 180000");
    assert_eq!(lines[9], "line 180009");
}

#[test]
fn the_gutter_numbers_the_lines_and_does_not_resize_as_you_scroll() {
    let d = doc(&(0..1200).map(|i| format!("{i}\n")).collect::<String>());
    let mut v = View { gutter: true, w: 400, h: 3 * LARGE.h, ..View::default() };
    let a = v.gutter_cols(&d);
    v.top = 1100;
    assert_eq!(v.gutter_cols(&d), a,
               "the gutter changed width while scrolling");
    let f = frame(&d, &v, &LARGE);
    let nums: Vec<String> = runs(&f).into_iter().step_by(2).collect();
    assert_eq!(nums[0], "1101", "lines are numbered from one");
}

/// **Only far enough.**  Centring on the caret scrolls on every
/// keystroke, which under a held arrow reads as the page tearing past.
#[test]
fn scrolling_follows_the_caret_to_the_edge_and_no_further() {
    let d0 = doc(&(0..100).map(|i| format!("row {i}\n")).collect::<String>());
    let mut d = d0.clone();
    let mut v = View { top: 0, left: 0, w: 600, h: 10 * LARGE.h, gutter: false, scale: 1 };

    d.seek_rowcol(5, 0);
    assert!(!v.follow(&d, &LARGE), "the caret was already visible");
    assert_eq!(v.top, 0);

    d.seek_rowcol(10, 0);
    assert!(v.follow(&d, &LARGE));
    assert_eq!(v.top, 1, "one line, not a jump to the middle");

    d.seek_rowcol(0, 0);
    v.follow(&d, &LARGE);
    assert_eq!(v.top, 0, "back to the top");

    // Horizontally, the same rule.
    let mut wide = doc(&"x".repeat(500));
    let mut v = View { top: 0, left: 0, w: 20 * LARGE.w, h: 100, gutter: false, scale: 1 };
    wide.seek(300);
    v.follow(&wide, &LARGE);
    assert_eq!(v.left, 300 + 1 - 20);
}

#[test]
fn a_click_lands_where_it_was_clicked() {
    let d = doc("hello\nworld\nagain");
    let v = View { top: 1, left: 0, w: 400, h: 200, gutter: false, scale: 1 };
    // Second visible row (row 2), fourth column.
    let (row, col) = v.hit(&d, &LARGE, LARGE.w * 4 + 1, LARGE.h + 3);
    assert_eq!((row, col), (2, 4));
    // Past the end of the document clamps to its last row.
    let (row, _) = v.hit(&d, &LARGE, 0, LARGE.h * 40);
    assert_eq!(row, d.rows() - 1);

    let mut d2 = d.clone();
    d2.seek_rowcol(row, 99);
    assert_eq!(d2.cursor(), (2, 5), "clamped to the line's own width");
}

#[test]
fn the_caret_is_drawn_on_the_character_it_is_before() {
    let mut d = doc("abcdef");
    d.seek(3);
    let v = view(400, 200);
    let f = frame(&d, &v, &LARGE);
    let caret = f.items.iter().rev().find_map(|i| match i {
        Item::Rect { x, y, c, .. } if *c == CARET => Some((*x, *y)),
        _ => None,
    }).expect("a caret");
    assert_eq!(caret, (3 * LARGE.w, 0));
    assert_eq!(caret_at(&d, &v, &LARGE), caret);
    // It is the last item, so nothing is drawn over it.
    assert!(matches!(f.items.last(), Some(Item::Rect { c, .. }) if *c == CARET));
}

/// A line scrolled sideways is cut **by columns**, so an indented line
/// does not slide relative to its neighbour.
#[test]
fn horizontal_scrolling_cuts_by_columns() {
    let d = doc("\tabcdef\n    abcdef");
    let v = View { top: 0, left: 4, w: 100 * LARGE.w, h: 200, gutter: false, scale: 1 };
    let f = frame(&d, &v, &LARGE);
    let lines = runs(&f);
    assert_eq!(lines[0], lines[1],
               "a tab and four spaces scrolled differently");
    assert_eq!(lines[0], "abcdef");
}

#[test]
fn a_tab_is_drawn_as_the_blank_it_occupies() {
    let d = doc("\tx");
    let v = view(400, 200);
    let lines = runs(&frame(&d, &v, &LARGE));
    assert_eq!(lines[0], "    x", "the tab expanded at the last moment");
    assert_eq!(d.text(), "\tx", "and the document still holds a tab");
}

#[test]
fn painting_a_frame_puts_ink_on_the_canvas() {
    let mut d = doc("hello");
    d.seek(2);
    let v = view(200, 60);
    let mut c = Canvas::new(v.w, v.h, Colour::rgb(0, 0, 0));
    paint(&mut c, &frame(&d, &v, &LARGE), &LARGE, 1);
    let ink = gestate_editor::view::INK.word();
    let lit = (0..c.h).flat_map(|y| (0..c.w).map(move |x| (x, y)))
        .filter(|(x, y)| c.get(*x, *y) == Some(ink))
        .count();
    assert!(lit > 40, "only {lit} lit pixels — the text was not drawn");
    let carets = (0..c.h).flat_map(|y| (0..c.w).map(move |x| (x, y)))
        .filter(|(x, y)| c.get(*x, *y) == Some(CARET.word()))
        .count();
    assert!(carets > 0, "the caret was not drawn");
}

/// An empty document still has a line to sit on, and a frame to draw.
#[test]
fn the_empty_document_draws() {
    let d = doc("");
    let v = view(200, 60);
    let f = frame(&d, &v, &LARGE);
    assert_eq!(runs(&f), Vec::<String>::new(), "no text, and no crash");
    assert!(f.items.iter().any(|i| matches!(i, Item::Rect { c, .. } if *c == CARET)),
            "the caret is still somewhere");
    assert_eq!(d.cursor(), (0, 0));
}

/// A window too small to hold a line still draws the line the caret is
/// on, rather than dividing by zero somewhere.
#[test]
fn a_window_smaller_than_a_line_still_draws_one() {
    let d = doc("one\ntwo");
    let v = View { top: 0, left: 0, w: 1, h: 1, gutter: false, scale: 1 };
    assert_eq!(v.rows(&LARGE), 1);
    assert_eq!(v.text_cols(&LARGE, &d), 1);
    let f = frame(&d, &v, &LARGE);
    assert_eq!(runs(&f), vec!["o".to_string()]);
}

// ── Zoom ─────────────────────────────────────────────────────────────────

/// **Zoom is a cell size**, so everything that lays out in cells moves
/// together — the rows that fit, the columns, the gutter, the caret and
/// what a click means.  A zoom that moved the text and not the hit
/// testing would put the caret somewhere you did not press.
#[test]
fn zooming_moves_the_layout_and_the_hit_testing_together() {
    let d = doc("hello\nworld\nagain");
    let one = View { top: 0, left: 0, w: 400, h: 200, gutter: false, scale: 1 };
    let two = View { scale: 2, ..one };

    assert_eq!(two.cw(&LARGE), 2 * one.cw(&LARGE));
    assert_eq!(two.ch(&LARGE), 2 * one.ch(&LARGE));
    assert_eq!(two.rows(&LARGE) * 2, one.rows(&LARGE));

    // The same pixel is a different cell at a different zoom, and both
    // hit tests agree with their own geometry.
    let (r1, c1) = one.hit(&d, &LARGE, LARGE.w * 4 + 1, LARGE.h + 1);
    let (r2, c2) = two.hit(&d, &LARGE, 2 * (LARGE.w * 4 + 1), 2 * LARGE.h + 1);
    assert_eq!((r1, c1), (r2, c2), "a click on the same character");
}

/// The picture is the same picture, drawn bigger — same runs, same
/// order, only the coordinates scaled.
#[test]
fn the_zoomed_frame_says_the_same_thing() {
    let d = doc("one\ntwo\nthree");
    let one = View { top: 0, left: 0, w: 800, h: 400, gutter: true, scale: 1 };
    let two = View { scale: 2, ..one };
    assert_eq!(runs(&frame(&d, &one, &LARGE)), runs(&frame(&d, &two, &LARGE)));
}

/// Every rung of the ladder is a real, distinct size, and they climb.
#[test]
fn the_zoom_ladder_climbs() {
    use gestate_editor::font::{LADDER, LADDER_DEFAULT};
    let cell = |i: usize| {
        let (f, s) = LADDER[i];
        (f.w * s, f.h * s)
    };
    assert!(LADDER.len() >= 7, "only {} rungs", LADDER.len());
    for i in 1..LADDER.len() {
        let (pw, ph) = cell(i - 1);
        let (w, h) = cell(i);
        assert!(w >= pw && h >= ph && (w > pw || h > ph),
                "rung {i} is {w}x{h} after {pw}x{ph} — the ladder does not \
                 climb");
    }
    assert_eq!(cell(LADDER_DEFAULT), (10, 20), "it starts at 10x20");
    // Every rung draws letters, not blocks.
    for (f, _) in LADDER {
        assert!(f.has('A') && f.has('ä') && f.has('─'), "a rung is missing \
                the alphabet this project writes in");
    }
}

/// Scaling is by whole numbers, so a stroke keeps its width.
#[test]
fn a_scaled_glyph_is_the_same_glyph_in_bigger_pixels() {
    let ink = Colour::rgb(255, 255, 255);
    let mut a = Canvas::new(40, 40, Colour::rgb(0, 0, 0));
    let mut b = Canvas::new(80, 80, Colour::rgb(0, 0, 0));
    LARGE.draw_scaled(&mut a, 0, 0, "R", ink, 1);
    LARGE.draw_scaled(&mut b, 0, 0, "R", ink, 2);
    for y in 0..LARGE.h {
        for x in 0..LARGE.w {
            let lit = a.get(x, y) == Some(ink.word());
            for dy in 0..2 {
                for dx in 0..2 {
                    assert_eq!(b.get(x * 2 + dx, y * 2 + dy) == Some(ink.word()),
                               lit, "pixel ({x},{y}) did not become a 2×2 block");
                }
            }
        }
    }
}
