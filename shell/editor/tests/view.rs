//! What a frame promises, checked without a window.
//!
//! The layout is the one thing about an editor a test can pin exactly.
//! Whether it is *pleasant* is a thing a person has to look at; whether
//! the caret is on the character you typed, whether a click lands where
//! you clicked, and whether scrolling a million-line file costs the
//! rows on screen are not.

use gestate_editor::document::{char_of_column, column_of, width_of, Document};
use gestate_editor::font::LARGE;
use gestate_editor::view::{caret_at, frame, paint, Item, View, CARET,
                          FAINT, INK};
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
    View { top: 0, left: 0, w, h, gutter: false, aside: 0, piano: 0, focused: false, scale: 1, boxes: vec![], foot_rows: 1, warning: String::new(), plus_hidden: false, hint: false }
}

/// A view that fits exactly `rows` rows of text, with the status line
/// paid for on top — the window is not all text.
fn rows_of(rows: usize, w: i32) -> View {
    let v = view(w, 0);
    View { h: rows as i32 * v.ch(&LARGE) + v.status_h(&LARGE), ..v }
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

/// **A different file is a different past** (fixme.md F113).  `set_text`
/// commits — a `fmt` is one undo away from the text you had — so a file
/// switch through it put the old file's whole content on the new file's
/// undo stack: one Ctrl-Z and A's text stood under B's name, one save
/// from overwriting B with A.  `load` is the other door.
#[test]
fn loading_a_file_clears_the_histories() {
    let mut d = doc("the old file");
    d.insert("!").unwrap();
    assert!(d.can_undo());
    d.load("the new file");
    assert_eq!(d.text(), "the new file");
    assert!(!d.can_undo(), "undo must not resurrect the old file");
    assert!(!d.can_redo());
    assert!(d.is_saved(), "what was loaded is what is written down — \
                           a file that exists must not wear the [+]");
    // And a file being *started* is not written down: the phantom that
    // wore lantern's name read as saved, and nothing anywhere told the
    // person the file under them was an empty starter.
    d.load_written("a starter", false);
    assert!(!d.is_saved(), "saving creates it — the [+] from birth");
    d.mark_saved();
    assert!(d.is_saved(), "and the first save settles it");
    // And set_text still commits, because fmt depends on it.
    d.set_text("formatted");
    assert!(d.can_undo());
    assert!(d.undo());
    assert_eq!(d.text(), "a starter");
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
    let mut v = rows_of(10, 600);
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
    let mut v = View { gutter: true, ..rows_of(3, 400) };
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
    let mut v = rows_of(10, 600);

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
    let mut v = View { top: 0, left: 0, w: 20 * LARGE.w, h: 100, gutter: false, aside: 0, piano: 0, focused: false, scale: 1, boxes: vec![], foot_rows: 1, warning: String::new(), plus_hidden: false, hint: false };
    wide.seek(300);
    v.follow(&wide, &LARGE);
    assert_eq!(v.left, 300 + 1 - 20);
}

#[test]
fn a_click_lands_where_it_was_clicked() {
    let d = doc("hello\nworld\nagain");
    let v = View { top: 1, left: 0, w: 400, h: 200, gutter: false, aside: 0, piano: 0, focused: false, scale: 1, boxes: vec![], foot_rows: 1, warning: String::new(), plus_hidden: false, hint: false };
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
    let v = View { top: 0, left: 4, w: 100 * LARGE.w, h: 200, gutter: false, aside: 0, piano: 0, focused: false, scale: 1, boxes: vec![], foot_rows: 1, warning: String::new(), plus_hidden: false, hint: false };
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
    let v = View { top: 0, left: 0, w: 1, h: 1, gutter: false, aside: 0, piano: 0, focused: false, scale: 1, boxes: vec![], foot_rows: 1, warning: String::new(), plus_hidden: false, hint: false };
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
    let one = View { top: 0, left: 0, w: 400, h: 200, gutter: false, aside: 0, piano: 0, focused: false, scale: 1, boxes: vec![], foot_rows: 1, warning: String::new(), plus_hidden: false, hint: false };
    let two = View { scale: 2, ..one.clone() };

    assert_eq!(two.cw(&LARGE), 2 * one.cw(&LARGE));
    assert_eq!(two.ch(&LARGE), 2 * one.ch(&LARGE));
    // **Fewer rows, and not exactly half.**  The status line is a row
    // at whatever the current cell is, so it grows with the zoom and
    // comes out of the same height — `(h - status) / ch` is not
    // `h / ch` halved, and asserting that it was would be asserting an
    // arithmetic accident rather than the behaviour.
    assert!(two.rows(&LARGE) < one.rows(&LARGE));
    assert!(two.rows(&LARGE) >= 1, "a zoom must not leave no text");

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
    let one = View { top: 0, left: 0, w: 800, h: 400, gutter: true, aside: 0, piano: 0, focused: false, scale: 1, boxes: vec![], foot_rows: 1, warning: String::new(), plus_hidden: false, hint: false };
    let two = View { scale: 2, ..one.clone() };
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

// ── What the model's description draws ───────────────────────────────────

use gestate_editor::furniture::Furniture;
use gestate_editor::view::{frame_with, ANGRY, FILL, TROUGH};

fn chrome() -> Furniture {
    Furniture::read("status\tapplied\n\
                     trouble\t2\texpected a type\n\
                     knob\tcutoff\t3\t0.25\t0\t1\tFloat")
}

/// **A knob is drawn beside the line that declares it**, which is the
/// thing `audiospans` exists for and the reason a parameter is not in a
/// panel you have to read against the code.
#[test]
fn a_knob_lands_in_the_margin_at_its_own_line() {
    let d = doc("one\ntwo\nthree\nfour");
    let v = View { aside: 8, ..rows_of(6, 600) };
    let f = frame_with(&d, &v, &LARGE, &chrome());

    let troughs: Vec<&Item> = f.items.iter()
        .filter(|i| matches!(i, Item::Rect { c, .. } if *c == TROUGH))
        .collect();
    assert_eq!(troughs.len(), 1, "one knob, one trough");
    let Item::Rect { x, y, h, .. } = troughs[0] else { unreachable!() };
    // Line 3 is the third row, and the trough sits centred in it
    // rather than at its top — a four-pixel bar on a twenty-pixel row.
    let row_top = 2 * v.ch(&LARGE);
    assert!(*y >= row_top && *y + *h <= row_top + v.ch(&LARGE),
            "the trough is at {y}, outside row {row_top}");
    assert!(*x > v.w - v.aside as i32 * v.cw(&LARGE) - 1, "not in the margin");

    // And the fill says where it is turned to.  **Found by where it
    // is, not by its colour**: a knob's fill and the caret are the same
    // accent on purpose, so a test that counted blue rectangles would
    // be counting the caret too.
    let edge = v.w - v.aside as i32 * v.cw(&LARGE);
    let fills: Vec<&Item> = f.items.iter()
        .filter(|i| matches!(i, Item::Rect { c, x, .. }
                             if *c == FILL && *x >= edge))
        .collect();
    assert_eq!(fills.len(), 1);
    let (Item::Rect { w: full, .. }, Item::Rect { w: whole, .. }) =
        (fills[0], troughs[0]) else { unreachable!() };
    assert!((*full as f64 / *whole as f64 - 0.25).abs() < 0.06,
            "{full} of {whole} is not a quarter");
}

#[test]
fn no_margin_means_no_knobs_and_no_width_lost() {
    let d = doc("one\ntwo\nthree");
    let wide = View { aside: 0, ..rows_of(6, 600) };
    let narrow = View { aside: 8, ..wide.clone() };
    assert!(wide.text_cols(&LARGE, &d) > narrow.text_cols(&LARGE, &d),
            "a margin costs columns");
    let f = frame_with(&d, &wide, &LARGE, &chrome());
    assert!(!f.items.iter().any(|i| matches!(i, Item::Rect { c, .. }
                                             if *c == TROUGH)),
            "a knob was drawn with no margin to draw it in");
}

/// **The complaint goes beside the line that caused it.**  A status bar
/// is one line; this is where it belongs.
#[test]
fn the_trouble_is_drawn_in_a_box_under_its_own_line() {
    let d = doc("one\ntwo\nthree");
    let mut v = View { aside: 0, ..rows_of(6, 900) };
    v.grant(&chrome(), &LARGE);
    let ch = v.ch(&LARGE);
    let f = frame_with(&d, &v, &LARGE, &chrome());

    // The message sits in the box's row, under line 2's band.
    let said: Vec<(&String, &i32)> = f.items.iter().filter_map(|i| match i {
        Item::Run { s, y, c, .. } if *c == ANGRY => Some((s, y)),
        _ => None,
    }).collect();
    assert_eq!(said.len(), 1);
    assert_eq!(said[0].0, "expected a type");
    assert_eq!(*said[0].1, 2 * ch, "the box's first row, under line 2");

    // Line 3 was pushed down past the box — the acceptance line.
    let three: Vec<&i32> = f.items.iter().filter_map(|i| match i {
        Item::Run { s, y, .. } if s == "three" => Some(y),
        _ => None,
    }).collect();
    assert_eq!(three, vec![&(3 * ch)], "line 3 starts after the box");
    // And a click there agrees with where it was drawn.
    assert_eq!(v.hit(&d, &LARGE, 0, 3 * ch + 1).0, 2);

    // And a mark in the gutter, so a scrolled-away message is still
    // findable by the line it belongs to.
    assert!(f.items.iter().any(|i| matches!(i, Item::Rect { x: 0, y, c, .. }
                                            if *c == ANGRY && *y == v.ch(&LARGE))));
}

/// **B1's acceptance, whole**: a two-line error under a line pushes the
/// next line down by two rows, and the view granted exactly what the
/// description said — capped, so a hundred lines of clang cannot eat
/// the window.
#[test]
fn a_two_line_error_is_a_two_row_box() {
    use gestate_editor::view::BOX_MOST;

    let d = doc("one\ntwo\nthree\nfour");
    let two = Furniture::read("trouble\t2\texpected a type\n\
                               trouble\t2\tbecause of this");
    let mut v = View { aside: 0, ..rows_of(8, 900) };
    v.grant(&two, &LARGE);
    assert_eq!(v.boxes, vec![(2, 2)]);
    let ch = v.ch(&LARGE);
    let f = frame_with(&d, &v, &LARGE, &two);

    let said: Vec<(&String, &i32)> = f.items.iter().filter_map(|i| match i {
        Item::Run { s, y, c, .. } if *c == ANGRY => Some((s, y)),
        _ => None,
    }).collect();
    assert_eq!(said.len(), 2);
    assert_eq!((said[0].0.as_str(), *said[0].1), ("expected a type", 2 * ch));
    assert_eq!((said[1].0.as_str(), *said[1].1), ("because of this", 3 * ch));
    // Line 3 lands two rows further down than it would have.
    assert_eq!(v.hit(&d, &LARGE, 0, 4 * ch + 1).0, 2);

    // The cap: a flood of rows is granted `BOX_MOST` and no more.
    let flood = Furniture::read(&(0..20)
        .map(|i| format!("trouble\t2\trow {i}"))
        .collect::<Vec<_>>()
        .join("\n"));
    let mut v = View { aside: 0, ..rows_of(8, 900) };
    v.grant(&flood, &LARGE);
    assert_eq!(v.boxes, vec![(2, BOX_MOST)]);

    // And a complaint about nowhere (line 0) gets no box at all.
    let nowhere = Furniture::read("trouble\t0\tno file");
    let mut v = View { aside: 0, ..rows_of(8, 900) };
    v.grant(&nowhere, &LARGE);
    assert!(v.boxes.is_empty());
}

#[test]
fn the_status_line_says_what_just_happened() {
    let d = doc("x");
    let v = rows_of(4, 400);
    let f = frame_with(&d, &v, &LARGE, &chrome());
    let said = runs(&f);
    assert!(said.contains(&"applied".to_string()), "{said:?}");
    // At the foot, and nothing *else* is drawn down there.
    let sy = v.h - v.status_h(&LARGE);
    for item in &f.items {
        if let Item::Run { y, s, .. } = item {
            assert!(*y < sy || s == "applied",
                    "{s:?} is in the status line's row");
        }
    }
}

/// A description with nothing in it draws a window with nothing extra —
/// the same frame `frame` gives.
#[test]
fn no_description_is_no_chrome() {
    let d = doc("one\ntwo");
    let v = rows_of(5, 400);
    assert_eq!(frame(&d, &v, &LARGE),
               frame_with(&d, &v, &LARGE, &Furniture::default()));
}

// ── The transport, at the foot ───────────────────────────────────────────
//
// The description carried `play` and `loop` from the day the wire was
// built and nothing drew them, which made `seek` and `play` look like
// commands that did nothing: they answered "at bar 8" and the window
// showed exactly what it had before.  A command whose only evidence is
// its own sentence cannot be told from one that failed.

fn transport(playing: bool, beat: f64) -> gestate_editor::furniture::Furniture {
    use gestate_editor::furniture::Furniture;
    Furniture { playing, beat, has_transport: true, ..Furniture::default() }
}

fn foot(f: &gestate_editor::furniture::Furniture) -> Vec<String> {
    let doc = Document::new("one\n");
    let view = view(600, 200);
    let frame = gestate_editor::view::frame_with(&doc, &view, &LARGE, f);
    let sy = view.h - view.status_h(&LARGE);
    frame.items.iter().filter_map(|i| match i {
        Item::Run { y, s, .. } if *y >= sy => Some(s.clone()),
        _ => None,
    }).collect()
}

#[test]
fn the_transport_is_shown_as_a_bar_and_a_beat() {
    // **Counting from zero**, because that is what `seek` and `loop` are
    // *given* — a readout in other units than the command takes is a
    // second thing to learn — and because everything else in this
    // language counts from zero.  It read from one for a while, which is
    // what a score on paper does and is wrong in a programmatic editor:
    // an interface that alone said *bar 1* for the first bar made the
    // reader do arithmetic to cross between the program and the window.
    let said = foot(&transport(true, 0.0));
    assert!(said.iter().any(|s| s.contains("0.0")), "{said:?}");
    let said = foot(&transport(true, 8.0));
    assert!(said.iter().any(|s| s.contains("2.0")), "bar 2 beat 0: {said:?}");
    let said = foot(&transport(true, 9.0));
    assert!(said.iter().any(|s| s.contains("2.1")), "bar 2 beat 1: {said:?}");
}

/// `loop 2 6` must read back as `2-6`.  The end is exclusive, so the
/// bars actually *played* are two to five — but a readout that
/// disagreed with the command that made it would be a puzzle to solve
/// every time rather than a thing to read.
#[test]
fn a_loop_is_shown_in_the_bars_it_was_given() {
    let mut f = transport(false, 0.0);
    f.looping = Some((4.0, 20.0));           // what `loop 1 5` sets
    let said = foot(&f);
    assert!(said.iter().any(|s| s.contains("1-5")), "{said:?}");
}

/// **A model that has said nothing about time has no position.**  A
/// readout invented for it would be a fact the window made up.
#[test]
fn nothing_is_shown_when_there_is_no_transport() {
    let said = foot(&gestate_editor::furniture::Furniture::default());
    assert!(said.iter().all(|s| !s.contains("0.0")), "{said:?}");
}

/// A bank the sound does not reach says "disconnected" where its
/// count would be, in the warm colour — the fact that explains keys
/// played into silence, drawn where the person is already looking.
#[test]
fn an_unconnected_bank_says_so() {
    use gestate_editor::furniture::{Bank, Furniture};
    use gestate_editor::view::AWAY;

    let d = doc("one\ntwo\n");
    let mut chrome = Furniture::default();
    chrome.banks.push(Bank { name: "lead".into(), line: 1, held: 0,
                             voices: 4, listening: false, wired: false });
    let v = View { w: 600, h: 300, aside: 10, ..view(600, 300) };
    let f = frame_with(&d, &v, &LARGE, &chrome);
    let said = f.items.iter().find_map(|i| match i {
        Item::Run { s, c, .. } if s == "disconnected" => Some(*c),
        _ => None,
    });
    assert_eq!(said, Some(AWAY), "the words, in the away colour");
    // And a wired bank keeps its count.
    chrome.banks[0].wired = true;
    let f = frame_with(&d, &v, &LARGE, &chrome);
    assert!(f.items.iter().any(|i| matches!(i, Item::Run { s, .. }
                                            if s == "0/4")));
}

/// A score line writing a bank MIDI has taken says "layered away" in
/// the margin at the line itself — the person can see the note that
/// is not sounding.
#[test]
fn a_layered_away_line_says_so_in_the_margin() {
    use gestate_editor::furniture::Furniture;
    use gestate_editor::view::AWAY;

    let d = doc("one\ntwo\nvoices.lead 60\nfour\n");
    let mut chrome = Furniture::default();
    chrome.aways.push((3, "away".into()));
    let v = View { w: 600, h: 300, aside: 10, ..view(600, 300) };
    let f = frame_with(&d, &v, &LARGE, &chrome);
    let hit = f.items.iter().find_map(|i| match i {
        Item::Run { s, c, y, .. } if s == "away" => Some((*c, *y)),
        _ => None,
    });
    let (c, y) = hit.expect("the words are drawn");
    assert_eq!(c, AWAY);
    assert_eq!(y, 2 * v.ch(&LARGE), "at the line the score wrote");
}

/// A bank's box is a button; the count beside it is a reading.
#[test]
fn only_the_box_of_a_bank_is_pressable() {
    use gestate_editor::furniture::{Bank, Furniture};
    let mut chrome = Furniture::default();
    chrome.banks.push(Bank { name: "pad".into(), line: 1, held: 4,
                             voices: 6, listening: false, wired: true });
    let v = View { w: 600, h: 300, aside: 10, ..view(600, 300) };
    let ch = v.ch(&LARGE);
    let (bx, side) = v.bank_box(&LARGE);
    assert_eq!(v.bank_hit(&LARGE, &chrome, bx + side / 2, ch / 2),
               Some(("pad".to_string(), false)));
    // Left of the box is the count, which is a reading, not a control.
    assert_eq!(v.bank_hit(&LARGE, &chrome, bx - 10, ch / 2), None);
    // And a line with no bank on it is nothing.
    assert_eq!(v.bank_hit(&LARGE, &chrome, bx + side / 2, ch * 3), None);
}

// ── The drawn keyboard ───────────────────────────────────────────────────

fn performing(mode: &str, heard: &[&str], held: &[i32])
    -> gestate_editor::furniture::Furniture
{
    use gestate_editor::furniture::Furniture;
    Furniture { performing: mode.into(),
                heard: heard.iter().map(|s| s.to_string()).collect(),
                held: held.to_vec(), octave: 4, ..Furniture::default() }
}

#[test]
fn a_keyboard_takes_its_room_from_the_document() {
    let d = doc(&"x\n".repeat(60));
    let mut v = view(600, 400);
    let without = v.rows(&LARGE);
    v.piano = LARGE.h * 4;
    assert!(v.rows(&LARGE) < without,
            "the keys must not be drawn over the text");
    assert_eq!(v.piano_y(&LARGE) + v.piano, v.h - v.status_h(&LARGE));
    let _ = d;
}

/// **The dead palette is the point.**  A bank only takes a note if its
/// payload has a `FromMIDI` instance and its switch is on, and neither
/// is visible in the text.
#[test]
fn a_keyboard_nobody_hears_is_drawn_dead() {
    use gestate_editor::view::{KEY_DEAD_WHITE, KEY_WHITE};

    let d = doc("x\n");
    let mut v = view(600, 400);
    v.piano = LARGE.h * 4;
    let colours = |f: &gestate_editor::furniture::Furniture| {
        frame_with(&d, &v, &LARGE, f).items.iter().filter_map(|i| match i {
            Item::Rect { c, .. } => Some(*c),
            _ => None,
        }).collect::<Vec<_>>()
    };
    assert!(colours(&performing("on", &["pad"], &[])).contains(&KEY_WHITE));
    let dead = colours(&performing("on", &[], &[]));
    assert!(dead.contains(&KEY_DEAD_WHITE));
    assert!(!dead.contains(&KEY_WHITE), "a piano that plays nothing must \
                                         not look like one that plays");
}

#[test]
fn a_held_note_is_drawn_down() {
    use gestate_editor::view::KEY_DOWN;

    let d = doc("x\n");
    let mut v = view(600, 400);
    v.piano = LARGE.h * 4;
    let f = frame_with(&d, &v, &LARGE, &performing("on", &["pad"], &[60]));
    assert!(f.items.iter().any(|i| matches!(i, Item::Rect { c, .. }
                                            if *c == KEY_DOWN)));
}

/// `follow_past` treats the top rows as covered: a caret above the
/// view lands below the panel's shadow, not behind it — and at the
/// very top of the file there is nothing to scroll past.
#[test]
fn follow_past_lands_below_the_shadow() {
    let d = doc(&"x\n".repeat(300));
    let mut v = view(400, 20 * LARGE.h);
    let mut d2 = d.clone();
    d2.seek_rowcol(50, 0);
    v.top = 200;
    v.follow_past(&d2, &LARGE, 6);
    assert_eq!(v.top, 44, "the caret stands at the first row past it");
    // Visible but covered still scrolls out from under.
    v.top = 48;
    v.follow_past(&d2, &LARGE, 6);
    assert_eq!(v.top, 44);
    // Row zero cannot go below anything.
    d2.seek_rowcol(0, 0);
    v.follow_past(&d2, &LARGE, 6);
    assert_eq!(v.top, 0);
    // And clear = 0 is exactly `follow`.
    let mut w = view(400, 20 * LARGE.h);
    w.top = 200;
    let mut d3 = d.clone();
    d3.seek_rowcol(50, 0);
    w.follow(&d3, &LARGE);
    assert_eq!(w.top, 50);
}

/// The refused `open`'s warning stands beside the caret in red, where
/// the eye already is — and an empty warning draws nothing at all.
#[test]
fn a_warning_stands_beside_the_caret() {
    use gestate_editor::view::ANGRY;

    let d = doc("sound : Sig Float\n");
    let mut v = view(600, 400);
    v.warning = "warning: unsaved changes".into();
    let f = frame_with(&d, &v, &LARGE, &Furniture::default());
    let said = f.items.iter().find_map(|i| match i {
        Item::Run { s, c, .. } if s == "warning: unsaved changes" =>
            Some(*c),
        _ => None,
    });
    assert_eq!(said, Some(ANGRY), "red, and present");
    v.warning.clear();
    let f = frame_with(&d, &v, &LARGE, &Furniture::default());
    assert!(!f.items.iter().any(|i| matches!(i, Item::Run { s, .. }
                                             if s.contains("warning"))));
}

/// The `[+]`'s flash hides it behind a blank of the same width, so the
/// bar cannot re-wrap mid-blink — a warning catches the eye without
/// shaking the furniture.
#[test]
fn the_plus_flash_keeps_the_bars_width() {
    use gestate_editor::view::bar_rows;

    let mut chrome = Furniture::default();
    chrome.file = "demo.ges".into();
    chrome.unsaved = true;
    let shown = bar_rows(&chrome, 60, false);
    let hidden = bar_rows(&chrome, 60, true);
    assert!(shown[0].0.contains("[+]"));
    assert!(!hidden[0].0.contains("[+]"));
    assert_eq!(shown[0].0.chars().count(), hidden[0].0.chars().count(),
               "the blank must be the marker's own width");
    assert_eq!(shown.len(), hidden.len());
}

/// The note that is sounding is a fact you otherwise reconstruct by
/// counting octaves — a held key says its number, and only while down.
#[test]
fn a_held_key_says_its_midi_number() {
    let d = doc("x\n");
    let mut v = view(600, 400);
    v.piano = LARGE.h * 4;
    let says = |held: &[i32], n: &str| {
        frame_with(&d, &v, &LARGE, &performing("on", &["pad"], held))
            .items.iter().any(|i| matches!(i, Item::Run { s, .. }
                                           if s == n))
    };
    assert!(says(&[60], "60"), "the white key's number, on the key");
    assert!(says(&[61], "61"), "and a black key's, on its own");
    assert!(!says(&[], "60"), "an idle keyboard stays a picture");
}

/// Black keys are asked about first, because they are drawn on top and
/// half of each overlaps a white one.
#[test]
fn the_pointer_finds_the_key_that_is_drawn_there() {
    let mut v = view(600, 400);
    v.piano = LARGE.h * 4;
    let (top, tall) = v.keys_y(&LARGE);
    let (midi, x, w) = v.black_keys()[0];        // C sharp
    assert_eq!(v.key_at(&LARGE, 60, x + w / 2, top + 2), Some(60 + midi));
    // **A black key straddles the boundary between its neighbours**, so
    // below its middle is the *next* white key — which is exactly what
    // a piano does, and why the black ones are asked about first.
    assert_eq!(v.key_at(&LARGE, 60, x + w / 2, top + tall - 2), Some(62));
    // Well inside the first white key, above or below, it is C.
    let (_c, cx, cw) = v.white_keys()[0];
    assert_eq!(v.key_at(&LARGE, 60, cx + cw / 5, top + tall - 2), Some(60));
    assert_eq!(v.key_at(&LARGE, 60, cx + cw / 5, top + 2), Some(60));
    // And above the keyboard is the document.
    assert_eq!(v.key_at(&LARGE, 60, x + w / 2, top - 5), None);
}

#[test]
fn there_is_no_keyboard_when_nothing_is_being_performed() {
    let v = view(600, 400);
    assert_eq!(v.piano, 0);
    assert_eq!(v.key_at(&LARGE, 60, 100, 300), None);
}

// ── Content boxes — the row table ────────────────────────────────────
//
// `roadmap.md` §"Content boxes": a box between lines is a per-row
// extra height, owned by the view, and the one invariant is that
// layout, scroll and hit-testing read the same table.  These tests
// are that invariant, mechanically; nothing grants a height in
// production yet, so they set `View::boxes` by hand.

/// With no boxes, the table is the uniform grid it replaced — the
/// refactor is invisible until something grants a height.
#[test]
fn without_boxes_the_slots_are_the_uniform_grid() {
    let d = doc(&["line"; 10].join("\n"));
    let v = rows_of(6, 400);
    let slots = v.slots(&d, &LARGE);
    assert_eq!(slots.len(), v.rows(&LARGE));
    for (i, s) in slots.iter().enumerate() {
        assert_eq!((s.row, s.y, s.box_h),
                   (v.top + i, i as i32 * v.ch(&LARGE), 0));
    }
}

/// A box under a line pushes every row below it down and costs the
/// window visible rows.
#[test]
fn a_box_pushes_the_rows_below_it_down() {
    let d = doc("one\ntwo\nthree\nfour\nfive\nsix\nseven\neight");
    let mut v = rows_of(6, 400);
    v.boxes = vec![(2, 2)];              // two rows of box under line 2
    let ch = v.ch(&LARGE);
    let slots = v.slots(&d, &LARGE);
    assert_eq!((slots[1].y, slots[1].box_h), (ch, 2 * ch));
    assert_eq!(slots[2].y, 4 * ch, "the next row starts after the box");
    assert_eq!(slots.len(), 4, "the box cost two visible rows");
}

/// A click below a box lands on the line it visibly touches, and a
/// click *inside* a box answers the line the box is anchored to.
#[test]
fn a_click_beside_a_box_lands_on_the_line_it_shows() {
    let d = doc("one\ntwo\nthree\nfour\nfive\nsix\nseven\neight");
    let mut v = rows_of(6, 400);
    v.boxes = vec![(2, 2)];
    let ch = v.ch(&LARGE);
    assert_eq!(v.hit(&d, &LARGE, 0, 4 * ch + 1).0, 2,
               "the row drawn after the box answers as itself");
    assert_eq!(v.hit(&d, &LARGE, 0, 2 * ch + 3).0, 1,
               "inside the box answers the line it is anchored to");
}

/// Following the caret counts box heights, so the caret's band really
/// is on screen after a motion.
#[test]
fn follow_scrolls_past_a_box_to_show_the_caret() {
    let mut d = doc("one\ntwo\nthree\nfour\nfive\nsix\nseven\neight");
    let mut v = rows_of(4, 400);
    v.boxes = vec![(2, 2)];
    // Row 3 fits a four-row window by the uniform arithmetic; the box
    // is what makes it not fit, and follow has to know.
    d.seek_rowcol(3, 0);
    assert!(v.follow(&d, &LARGE), "the view had to move");
    let shown: Vec<usize> = v.slots(&d, &LARGE).iter()
        .map(|s| s.row).collect();
    assert!(shown.contains(&3), "the caret's row is on screen: {shown:?}");
}

/// A jump lands with air past its target — `goto`, `line` and find
/// all reveal a few rows of consequence (and the target's own box)
/// instead of pinning the target at the fold.  The keystroke `follow`
/// stays minimal for its own stated reason.
#[test]
fn a_jump_reveals_air_past_its_target() {
    use gestate_editor::view::JUMP_AIR;

    let text = (1..=60).map(|k| k.to_string())
        .collect::<Vec<_>>().join("\n");
    let mut d = doc(&text);
    let mut v = rows_of(10, 400);

    // Jumping down: the rows past the target came along.
    d.seek_rowcol(29, 0);
    assert!(v.reveal(&d, &LARGE));
    let shown: Vec<usize> = v.slots(&d, &LARGE).iter()
        .map(|s| s.row).collect();
    assert!(shown.contains(&29), "the target shows: {shown:?}");
    assert!(shown.contains(&(29 + JUMP_AIR)),
            "the air past it shows: {shown:?}");

    // Jumping back up: air above, symmetrically.
    d.seek_rowcol(10, 0);
    assert!(v.reveal(&d, &LARGE));
    assert_eq!(v.top, 10 - JUMP_AIR);

    // Near the end there is less air than asked; the last row is
    // still never overshot.
    d.seek_rowcol(58, 0);
    v.reveal(&d, &LARGE);
    assert_eq!(v.top, v.top_showing(&LARGE, 59));
}

/// The wheel's clamp reads the same walk, so the last line can always
/// be reached and never overshot.
#[test]
fn scrolling_stops_where_the_last_line_shows() {
    use gestate_editor::keys::scroll;

    let d = doc("one\ntwo\nthree\nfour\nfive\nsix\nseven\neight");
    let mut v = rows_of(4, 400);
    v.boxes = vec![(6, 2)];
    scroll(&d, &mut v, &LARGE, 999);
    assert_eq!(v.top, v.top_showing(&LARGE, 7));
    assert!(v.slots(&d, &LARGE).iter().any(|s| s.row == 7),
            "the last row is reachable past the box");
}

/// A knob answers in its line's text band and not in the box below it
/// — a pointer inside a box must not turn a control it happens to sit
/// under.
#[test]
fn a_box_does_not_take_the_margin_with_it() {
    let d = doc("one\ntwo\nthree\nfour");
    let mut v = View { aside: 8, ..rows_of(8, 600) };
    v.boxes = vec![(3, 2)];              // a box under the knob's line
    let ch = v.ch(&LARGE);
    let x = v.w - 2;
    assert!(v.knob_hit(&LARGE, &chrome(), x, 2 * ch + 1).is_some(),
            "the knob's own band still answers");
    assert!(v.knob_hit(&LARGE, &chrome(), x, 3 * ch + 1).is_none(),
            "the box under line 3 is not the knob");
    // And the trough is drawn in the band the hit answers in.
    let f = frame_with(&d, &v, &LARGE, &chrome());
    let troughs: Vec<&Item> = f.items.iter()
        .filter(|i| matches!(i, Item::Rect { c, .. } if *c == TROUGH))
        .collect();
    assert_eq!(troughs.len(), 1, "one knob, one trough, box or no box");
    let Item::Rect { y, .. } = troughs[0] else { unreachable!() };
    assert!(*y >= 2 * ch && *y < 3 * ch, "drawn where the hit answers");
}

/// `caret_at` answers from the table too — a tooltip placed by it must
/// not float a box-height away from the caret.
#[test]
fn the_caret_position_counts_the_boxes_above_it() {
    let mut d = doc("one\ntwo\nthree\nfour");
    let mut v = rows_of(8, 400);
    v.boxes = vec![(1, 3)];
    d.seek_rowcol(2, 0);
    let (_x, y) = caret_at(&d, &v, &LARGE);
    assert_eq!(y, 5 * v.ch(&LARGE),
               "rows one and two, plus three rows of box");
}

// ── The status bar grows — for complaints about nowhere ──────────────

/// A complaint about line 0 has no box to live in; the bar grows a row
/// per such complaint and shows it whole, instead of the one truncated
/// sentence that used to be all anybody saw.
#[test]
fn an_unanchored_complaint_grows_the_bar() {
    use gestate_editor::view::ANGRY;

    let d = doc("one\ntwo\nthree");
    let chrome = Furniture::read(
        "status\tnot playing: boom\n\
         trouble\t0\tthe engine plays a fixed graph\n\
         trouble\t0\tand this file steps outside it");
    let mut v = rows_of(8, 900);
    let one_row = v.status_h(&LARGE);
    v.grant(&chrome, &LARGE);
    assert_eq!(v.foot_rows, 3, "a row per unanchored complaint");
    assert_eq!(v.status_h(&LARGE), one_row + 2 * v.ch(&LARGE));

    let f = frame_with(&d, &v, &LARGE, &chrome);
    let sy = v.h - v.status_h(&LARGE);
    let angry: Vec<(&String, &i32)> = f.items.iter().filter_map(|i| match i {
        Item::Run { s, y, c, .. } if *c == ANGRY && *y >= sy => Some((s, y)),
        _ => None,
    }).collect();
    assert_eq!(angry.len(), 2, "both rows drawn in the bar: {angry:?}");
    assert_eq!(angry[0].0, "the engine plays a fixed graph");
    assert!(angry[1].1 > angry[0].1, "stacked downward");
}

/// The bar does not repeat what the status already says, does not grow
/// for anchored complaints (they have boxes), and stops at five rows.
#[test]
fn the_bar_dedupes_ignores_anchored_and_caps_at_five() {
    use gestate_editor::view::BAR_MOST;

    // Deduped: the status quotes the complaint's line already.
    let quoted = Furniture::read(
        "status\tnot playing: no `sound` here\n\
         trouble\t0\tno `sound` here");
    let mut v = rows_of(8, 900);
    v.grant(&quoted, &LARGE);
    assert_eq!(v.foot_rows, 1, "growth without information");

    // Anchored complaints belong to their boxes, not the bar.
    let anchored = Furniture::read("trouble\t2\texpected a type");
    let mut v = rows_of(8, 900);
    v.grant(&anchored, &LARGE);
    assert_eq!(v.foot_rows, 1);
    assert_eq!(v.boxes, vec![(2, 1)]);

    // And a flood stands five rows, no further.
    let flood = Furniture::read(&(0..9)
        .map(|i| format!("trouble\t0\treason number {i}"))
        .collect::<Vec<_>>()
        .join("\n"));
    let mut v = rows_of(8, 900);
    v.grant(&flood, &LARGE);
    assert_eq!(v.foot_rows, BAR_MOST);
}

/// **Henri's report, 2026-08-13**: a long status ran off the right
/// edge and nothing multilined.  The bar wraps to the window's
/// columns now, and every run it draws fits.
#[test]
fn a_long_status_wraps_instead_of_running_off_the_right() {
    let words = "not playing: this program cannot be compiled for the \
                 sound card: the engine plays a fixed graph, so \
                 everything sound reaches must be decided once";
    let chrome = Furniture::read(&format!("status\t{words}"));
    let mut v = rows_of(8, 300);
    v.grant(&chrome, &LARGE);
    assert!(v.foot_rows > 1, "a long sentence grows the bar");

    let d = doc("one");
    let f = frame_with(&d, &v, &LARGE, &chrome);
    let sy = v.h - v.status_h(&LARGE);
    let mut in_bar = 0;
    for item in &f.items {
        if let Item::Run { x, y, s, .. } = item {
            if *y >= sy {
                in_bar += 1;
                assert!(x + s.chars().count() as i32 * v.cw(&LARGE) <= v.w,
                        "a bar row runs off the right: {s:?}");
            }
        }
    }
    assert!(in_bar >= 2, "the sentence is spread over rows");
}

// ── The burger ───────────────────────────────────────────────────────

/// The pixel that shows the burger is the pixel that answers to it:
/// everything `burger_frame` draws lies inside `burger_box`, which is
/// the same box the window's press reads — the one-arithmetic rule,
/// kept at the corner.
#[test]
fn the_burger_is_drawn_inside_the_box_the_press_reads() {
    use gestate_editor::view::{burger_frame, BURGER, INK};

    let v = rows_of(8, 900);
    let (bx, by, bw, bh) = v.burger_box(&LARGE);
    assert!(bx >= 0 && by >= 0 && bx + bw <= v.w,
            "the corner stands in the window");
    let f = burger_frame(&v, &LARGE, false);
    assert!(!f.items.is_empty());
    for item in &f.items {
        match item {
            Item::Rect { x, y, w, h, .. } => {
                assert!(*x >= bx && x + w <= bx + bw
                        && *y >= by && y + h <= by + bh,
                        "the ground spills out of the box");
            }
            Item::Run { x, y, s, c } => {
                // **The word, not the glyph.**  `afba696` made the
                // corner say `[command]` (F155) and this still asked
                // for the `≡` it replaced — so the test failed on
                // exactly the change it exists to protect.  Read from
                // `view::BURGER` now, which is the one place the word
                // lives and what `burger_box` sizes itself from.
                assert_eq!(s, BURGER);
                // **Ink, not `FAINT`** — and that is the whole of F155:
                // the resting colour *was* `FAINT`, measured at 2.3:1
                // against the ground, and a control painted in the
                // colour this window uses for *there, but not for you*
                // is a control nobody is being offered.
                assert_eq!(*c, INK, "at the ink's own weight when resting");
                assert!(*x >= bx
                        && x + BURGER.chars().count() as i32 * v.cw(&LARGE)
                           <= bx + bw
                        && *y >= by && y + v.ch(&LARGE) <= by + bh,
                        "the word spills out of the box");
            }
        }
    }
    // Lit while the list is up — a button that toggles has to say
    // which half of the toggle it is in.
    let open = burger_frame(&v, &LARGE, true);
    assert!(open.items.iter().any(|i| matches!(i,
        Item::Run { s, c, .. } if s == BURGER && *c == CARET)));
}

/// Pressing the burger writes `Ctrl-K` in the bar — the button
/// teaching the key it stands for — left of the transport, so the two
/// right-hand readouts cannot write over one another; and not at all
/// once the hint is down.
#[test]
fn the_bar_teaches_ctrl_k_while_the_burger_holds_the_list() {
    let d = doc("one");
    let chrome = Furniture::read("play\t1\t8.0");
    let mut v = rows_of(8, 900);
    v.hint = true;
    let f = frame_with(&d, &v, &LARGE, &chrome);
    let sy = v.h - v.status_h(&LARGE);
    let hint = f.items.iter().find_map(|i| match i {
        Item::Run { x, y, s, .. } if s == "Ctrl-K" && *y >= sy => Some(*x),
        _ => None,
    }).expect("the bar says Ctrl-K");
    let transport = f.items.iter().find_map(|i| match i {
        Item::Run { x, y, s, .. }
            if *y >= sy && s.contains('\u{25b6}') => Some(*x),
        _ => None,
    }).expect("the transport is drawn");
    assert!(hint + 6 * v.cw(&LARGE) <= transport,
            "the hint stands clear of the transport");

    v.hint = false;
    let quiet = frame_with(&d, &v, &LARGE, &chrome);
    assert!(!quiet.items.iter().any(|i| matches!(i,
        Item::Run { s, .. } if s == "Ctrl-K")));
}

/// A `.txt`/`.md` opens inert: the model sends `inert` instead of a
/// transport, and the window says `[inert]` where the transport would
/// stand — warm, because it is a mode being stated, not a fault.
#[test]
fn an_inert_file_wears_the_word_where_the_transport_stands() {
    use gestate_editor::view::AWAY;

    let d = doc("shopping list");
    let chrome = Furniture::read("status\tediting notes.md — inert\ninert\t1");
    let v = rows_of(8, 900);
    let f = frame_with(&d, &v, &LARGE, &chrome);
    let sy = v.h - v.status_h(&LARGE);
    let (x, c) = f.items.iter().find_map(|i| match i {
        Item::Run { x, y, s, c } if s == "[inert]" && *y >= sy =>
            Some((*x, *c)),
        _ => None,
    }).expect("the bar says [inert]");
    assert_eq!(c, AWAY, "warm, not red: a mode, not a fault");
    assert!(x + 7 * v.cw(&LARGE) <= v.w, "standing inside the window");
    // No transport was described, so none is drawn for it.
    assert!(!f.items.iter().any(|i| matches!(i, Item::Run { s, .. }
        if s.contains('\u{25b6}') || s.contains('\u{25a0}'))));
}

/// A scope grants a box under its declaration — the knob's placement
/// rule grown a height (`spec/scope.md`) — and the slots walk keeps
/// every reader agreeing about where the lines below it went.
#[test]
fn a_scope_grants_a_box_under_its_line() {
    use gestate_editor::view::SCOPE_ROWS;

    let chrome = Furniture::read("scope\tpost\t2");
    let mut v = rows_of(10, 900);
    v.grant(&chrome, &LARGE);
    assert_eq!(v.boxes, vec![(2, SCOPE_ROWS)]);
    // A trouble box on the same line wins — a complaint is news and a
    // trace is scenery.
    let both = Furniture::read("trouble\t2\tboom\nscope\tpost\t2");
    v.grant(&both, &LARGE);
    assert_eq!(v.boxes.len(), 1);
    assert_eq!(v.boxes[0].0, 2);
}

/// The walked canvas grants its box under the `substrate`
/// declaration (B2) — `canvas <line>` on the wire, the view saying
/// how tall, the same merge and cap as every other box kind.
#[test]
fn the_canvas_grants_a_box_under_its_declaration() {
    use gestate_editor::view::{BOX_MOST, CANVAS_ROWS};

    let chrome = Furniture::read("canvas\t3");
    let mut v = rows_of(12, 900);
    v.grant(&chrome, &LARGE);
    assert_eq!(v.boxes, vec![(3, CANVAS_ROWS)]);

    // A malformed or absent line draws no box and costs nothing.
    let none = Furniture::read("canvas\tnonsense");
    v.grant(&none, &LARGE);
    assert_eq!(v.boxes, vec![]);

    // Sharing a line with a scope merges under the one cap.
    let both = Furniture::read("canvas\t2\nscope\tpost\t2");
    v.grant(&both, &LARGE);
    assert_eq!(v.boxes.len(), 1);
    assert_eq!(v.boxes[0], (2, BOX_MOST));
}

/// Two scopes written on one line stack — one honest line, two
/// windows — each adding its rows to the same box, capped as ever.
#[test]
fn scopes_sharing_a_line_stack_their_rows() {
    use gestate_editor::view::{BOX_MOST, SCOPE_ROWS};

    let chrome = Furniture::read(
        "scope\tspec\t2\tspectro\nscope\tout\t2\tscope");
    let mut v = rows_of(12, 900);
    v.grant(&chrome, &LARGE);
    assert_eq!(v.boxes,
               vec![(2, (SCOPE_ROWS * 2).min(BOX_MOST))]);
}

/// A box on the last visible line hangs past the fold in the layout —
/// the caret's promise — and paints nothing there: past the fold is
/// the bar's ground (F132).
#[test]
fn a_box_at_the_fold_stops_at_the_fold() {
    use gestate_editor::view::CHROME;

    let d = doc("a\nb\nc\nd\ne\nf\ng\nh");
    let chrome = Furniture::read(
        "trouble\t6\tthis complaint is long enough that its wrapped \
         rows would spill well past the bottom of a six-row window \
         if nothing clipped the box it was granted");
    let mut v = rows_of(6, 400);
    v.grant(&chrome, &LARGE);
    let tall = v.h - v.status_h(&LARGE);
    let f = frame_with(&d, &v, &LARGE, &chrome);
    for item in &f.items {
        if let Item::Rect { y, h, c, .. } = item {
            if *c == CHROME {
                assert!(*y >= tall || y + h <= tall,
                        "a box painted across the fold: y={y} h={h} \
                         tall={tall}");
            }
        }
    }
}

/// **A scope crops at the fold; it does not squeeze into it.**
///
/// The fold rule the trouble box learned in F132, and the half it
/// never needed: a scope has a *picture* inside it, so shrinking the
/// drawing to whatever room is left redraws the wave flatter every row
/// it is scrolled.  Henri, who had seen this shape before: *"the scope
/// / spectro have the same clipping issue as canvas used to have."*
/// The canvas answered it by laying out at the band's full height and
/// blitting only the visible rows; this is that rule, in the other
/// painter.
#[test]
fn a_scope_at_the_fold_is_cropped_and_not_squashed() {
    use std::collections::HashMap;

    use gestate_editor::view::scope_frame;

    let d = doc("a\nb\nc\nd\ne\nf\ng\nh");
    let chrome = Furniture::read("scope\tpost\t7\tscope");
    let mut traces: HashMap<String, Vec<f64>> = HashMap::new();
    // A square wave at full scale: every point is at one edge of the
    // box or the other, so a rescaled one lands somewhere new and a
    // cropped one simply loses half its points.
    traces.insert("post".into(),
                  (0..64).map(|i| if i % 2 == 0 { 1.0 } else { -1.0 })
                      .collect());

    let points = |f: &gestate_editor::view::Frame| -> Vec<i32> {
        f.items.iter().filter_map(|i| match i {
            Item::Rect { y, w, .. } if *w == 2 => Some(*y),
            _ => None,
        }).collect()
    };
    let panel = |f: &gestate_editor::view::Frame| -> (i32, i32) {
        f.items.iter().find_map(|i| match i {
            Item::Rect { y, h, w, .. } if *w > 10 => Some((*y, *h)),
            _ => None,
        }).unwrap_or((0, 0))
    };

    let mut roomy = rows_of(30, 400);
    roomy.grant(&chrome, &LARGE);
    let whole = scope_frame(&d, &roomy, &LARGE, &chrome, &traces);
    let (_, full_h) = panel(&whole);
    assert!(!points(&whole).is_empty(), "nothing was drawn with room");

    for rows in [10usize, 9] {
        let mut v = rows_of(rows, 400);
        v.grant(&chrome, &LARGE);
        let tall = v.h - v.status_h(&LARGE);
        let f = scope_frame(&d, &v, &LARGE, &chrome, &traces);

        // The fold really bit — otherwise the rest proves nothing.
        let (_, h) = panel(&f);
        assert!(h < full_h, "the fold did not crop at {rows} rows");

        // Nothing is painted past it.
        for item in &f.items {
            if let Item::Rect { y, h, .. } = item {
                assert!(y + h <= tall,
                        "painted across the fold at {rows} rows: \
                         y={y} h={h} tall={tall}");
            }
        }

        // And what survives sits exactly where the roomy frame put it:
        // cropped, not rescaled.  A scope squeezed into the remaining
        // room puts its points somewhere new, which is the picture
        // telling a different story about the same sound.
        let mine = points(&f);
        assert!(!mine.is_empty(), "the whole wave was cropped away");
        for y in &mine {
            assert!(points(&whole).contains(y),
                    "at {rows} rows a point moved to {y}: the wave was \
                     rescaled to fit rather than cropped");
        }
    }
}

// ── The peep ─────────────────────────────────────────────────────────

use gestate_editor::view::{peep_frame, peep_hit, PEEP_ROWS};

/// A hundred lines, each naming itself, so a row can be recognised by
/// what it says rather than by counting rectangles.
fn hundred() -> Document {
    doc(&(0..100).map(|i| format!("line {i}"))
        .collect::<Vec<_>>().join("\n"))
}

/// **Nothing while the caret is on screen**, which is nearly always.
///
/// The peep is chrome that appears for a reason; one that stood there
/// permanently would be a second view of the file, which is the thing
/// §"Content boxes" says the editor is not.
#[test]
fn the_peep_is_absent_while_the_caret_is_visible() {
    let mut d = hundred();
    d.seek_rowcol(3, 0);
    let v = rows_of(10, 400);
    assert!(peep_frame(&d, &v, &LARGE).items.is_empty(),
            "a peep over a caret that is perfectly visible");
    assert_eq!(peep_hit(&d, &v, &LARGE, 20, 20), None);
}

/// Scroll away and the caret's own lines arrive: five of them, their
/// numbers, and the caret in the middle one.
#[test]
fn the_peep_shows_five_lines_their_numbers_and_the_caret() {
    let mut d = hundred();
    d.seek_rowcol(40, 3);
    let mut v = rows_of(10, 400);
    v.top = 0;                                 // scrolled far above it
    let f = peep_frame(&d, &v, &LARGE);
    let said = runs(&f);
    for row in 38..=42 {
        assert!(said.contains(&format!("line {row}")),
                "line {row} is not in the peep: {said:?}");
        assert!(said.contains(&format!("{}", row + 1)),
                "line {}'s number is not in the peep: {said:?}", row + 1);
    }
    assert!(!said.contains(&"line 43".to_string()),
            "the peep showed more than {PEEP_ROWS} lines: {said:?}");
    // The caret, in the caret's own colour and shape.
    assert!(f.items.iter().any(|i| matches!(i,
        Item::Rect { c, w, .. } if *c == CARET && *w <= 4)),
        "the peep drew no caret");
}

/// **Toward the caret, not away from it** — Henri's rule, and the
/// opposite of the palette panel's: the panel dodges the text you are
/// reading, the peep points at the text you are not.
#[test]
fn the_peep_goes_to_the_side_the_caret_is_on() {
    let ground = |d: &Document, v: &View| -> i32 {
        peep_frame(d, v, &LARGE).items.iter().find_map(|i| match i {
            Item::Rect { y, w, .. } if *w > 100 => Some(*y),
            _ => None,
        }).expect("no peep at all")
    };
    let mut v = rows_of(10, 400);
    v.top = 50;

    let mut above = hundred();
    above.seek_rowcol(2, 0);                   // far above the view
    let mut below = hundred();
    below.seek_rowcol(95, 0);                  // far below it

    let up = ground(&above, &v);
    let down = ground(&below, &v);
    assert!(up < down,
            "the peep did not follow the caret's side: {up} vs {down}");
    // And both stay inside the text area — above the status bar, and
    // above the drawn keyboard when there is one, which is the fold
    // `frame_with` clips a content box at.
    v.piano = 4 * LARGE.h;
    v.foot_rows = 3;
    let tall = v.h - v.status_h(&LARGE) - v.piano;
    // **Fewer lines, not none.**  There is no room for five here, and a
    // band hanging past the fold would write over the status the way
    // F132's boxes did.  Fewer still answer *where*.
    let cramped = gestate_editor::view::peep_box(&above, &v, &LARGE)
        .expect("the peep gave up instead of shrinking");
    assert!(cramped.rows >= 1 && cramped.rows < PEEP_ROWS,
            "a cramped window got {} rows", cramped.rows);
    for (d, name) in [(&above, "above"), (&below, "below")] {
        for item in peep_frame(d, &v, &LARGE).items {
            let (y, h) = match item {
                Item::Rect { y, h, .. } => (y, h),
                Item::Run { y, .. } => (y, LARGE.h),
            };
            assert!(y >= 0 && y + h <= tall,
                    "the {name} peep left the text area: y={y} h={h}");
        }
    }
}

/// **A click in it moves the real caret**, and answers the line it is
/// drawn on — `peep_hit` is `peep_frame`'s inverse from the same
/// numbers, the rule `knob_hit` keeps beside its trough.
#[test]
fn a_click_in_the_peep_lands_on_the_line_it_is_drawn_on() {
    let mut d = hundred();
    d.seek_rowcol(40, 0);
    let mut v = rows_of(10, 400);
    v.top = 0;
    let f = peep_frame(&d, &v, &LARGE);
    // Where each line was drawn, by the text it drew.
    let placed: Vec<(i32, String)> = f.items.iter().filter_map(|i| match i {
        Item::Run { x, y, s, .. } if s.starts_with("line ") =>
            Some((*y, s.clone())),
        _ => None,
    }).collect();
    assert_eq!(placed.len(), PEEP_ROWS);
    for (y, said) in placed {
        let (row, _col) = peep_hit(&d, &v, &LARGE, 100, y + 2)
            .expect("a click inside the peep answered nothing");
        assert_eq!(format!("line {row}"), said,
                   "a click at y={y} answered row {row}, drawn as {said:?}");
    }
    // Outside it, the peep keeps its hands off — the press falls
    // through to whatever it was aimed at.
    assert_eq!(peep_hit(&d, &v, &LARGE, 100, v.h - 4), None);
}

/// A caret past the right edge is still shown, because the peep scrolls
/// its own columns — `follow`'s horizontal rule, in a smaller window.
#[test]
fn the_peep_scrolls_sideways_to_its_caret() {
    let long = "x".repeat(300);
    let mut d = doc(&format!("a\nb\n{long}\nd\ne\nf\ng\nh\ni\nj\nk\nl"));
    d.seek_rowcol(2, 290);
    let mut v = rows_of(4, 400);
    v.top = 8;
    let f = peep_frame(&d, &v, &LARGE);
    let caret = f.items.iter().find_map(|i| match i {
        Item::Rect { x, c, w, .. } if *c == CARET && *w <= 4 => Some(*x),
        _ => None,
    }).expect("the peep drew no caret for an off-screen column");
    assert!(caret >= 0 && caret < v.w,
            "the caret was drawn at {caret} in a window {} wide", v.w);
}

// ── How long the day has been ────────────────────────────────────────────
//
// `spec/timer.md`.  The row itself is small; what it must not do is
// disappear on the day it exists to name.

/// The tally is a row of the bar, in its own ink — not part of the
/// status sentence, because the two answer different questions and
/// change on different clocks.
#[test]
fn the_days_tally_stands_in_its_own_ink() {
    use gestate_editor::view::{bar_rows, Ink, SPENT};

    let chrome = Furniture::read(
        "status\tapplied\ntally\tyou 6h12m \u{25c6} [\u{25aa}\u{25aa}\u{25c6}]\t1");
    let rows = bar_rows(&chrome, 60, false);
    assert_eq!(rows.len(), 2);
    assert_eq!(rows[0].1, Ink::Faint);
    assert!(rows[0].0.contains("applied"));
    assert_eq!(rows[1].1, Ink::Spent);
    assert!(rows[1].0.starts_with("you 6h12m"));

    let d = doc("x\n");
    let v = rows_of(6, 600);
    let f = frame_with(&d, &View { foot_rows: 2, ..v }, &LARGE, &chrome);
    assert!(f.items.iter().any(|i| matches!(i, Item::Run { s, c, .. }
                                           if s.starts_with("you 6h12m")
                                              && *c == SPENT)),
            "drawn, and in the quiet amber rather than the status grey");
}

/// **A day with no tally draws no row.**  The model sends it only when
/// a record is being kept, and every other reader of `Furniture` — the
/// tests, the panel, a window driven by a harness — has none.
#[test]
fn no_tally_is_no_row() {
    use gestate_editor::view::bar_rows;

    let chrome = Furniture::read("status\tapplied");
    assert_eq!(bar_rows(&chrome, 60, false).len(), 1);
}

/// **The complaints give up their last row, not the tally.**  The day
/// the bar is full of compiler noise is precisely the long day this row
/// exists to name, and an instrument that goes quiet under load is not
/// an instrument.
#[test]
fn a_full_bar_still_keeps_a_row_for_the_day() {
    use gestate_editor::view::{bar_rows, Ink, BAR_MOST};

    let mut said = String::from("status\tapplied");
    for i in 0..8 {
        said.push_str(&format!("\ntrouble\t0\tsomething is wrong, number {i}"));
    }
    said.push_str("\ntally\tyou 11h04m \u{25b2}\t1");

    let rows = bar_rows(&Furniture::read(&said), 60, false);
    assert_eq!(rows.len(), usize::from(BAR_MOST));
    assert_eq!(rows.last().unwrap().1, Ink::Spent);
    assert!(rows.last().unwrap().0.contains("11h04m"));
    assert!(rows[1..rows.len() - 1].iter().all(|r| r.1 == Ink::Angry));
}

/// **But the status sentence outranks the tally.**  A bar narrow enough
/// to wrap what the last command said over the whole bar is not a bar
/// that should be cutting the answer short to fit a clock.
#[test]
fn a_long_answer_is_not_cut_short_to_fit_the_clock() {
    use gestate_editor::view::{bar_rows, Ink, BAR_MOST};

    let words = "the render was refused because the file it would have \
                 written is already there and is bigger than the one you \
                 asked for, so nothing was done and nothing was lost";
    let chrome = Furniture::read(
        &format!("status\t{words}\ntally\tyou 11h04m \u{25b2}\t1"));
    let rows = bar_rows(&chrome, 24, false);
    assert_eq!(rows.len(), usize::from(BAR_MOST));
    assert!(rows.iter().all(|r| r.1 == Ink::Faint),
            "every row is the answer; the tally gave way");
}


/// **A calm week draws at the chrome's own weight.**  The row is always
/// on, and a colour that is always on is one nobody reads
/// (`spec/rocks.md`) — so the amber is kept for a week that earned it.
/// Henri, who asked for this after living with the other version:
/// *"a reward for not rushing or going breakneck speed."*
#[test]
fn a_calm_week_is_not_drawn_in_the_warning_colour() {
    use gestate_editor::view::{bar_rows, Ink};

    let calm = Furniture::read("status\tapplied\ntally\tyou 12m \u{25aa}\t0");
    let rows = bar_rows(&calm, 60, false);
    assert_eq!(rows.len(), 2);
    assert_eq!(rows[1].1, Ink::Faint, "quiet, and the glyphs still say it");

    // The same row, one hard week later.
    let hard = Furniture::read("status\tapplied\ntally\tyou 12m \u{25aa}\t1");
    assert_eq!(bar_rows(&hard, 60, false)[1].1, Ink::Spent);

    // **A build that predates the field draws it as it always did.**
    let old = Furniture::read("status\tapplied\ntally\tyou 12m \u{25aa}");
    assert!(!old.tally_warm, "no field is not a warm field");
}

// ── The factory floor ────────────────────────────────────────────────
//
// `board/done/gemba.md`.  A session narrates and a box shows one thing at a
// time; the window's whole job is to draw the thing it is handed and
// the mark for what is waiting.  **What is not the window's job** is
// deciding when to move on: the pace is the model's, because how long
// something has stood is a fact about the session and not about how
// often this happens to repaint.

fn walking(said: &str, behind: usize) -> Furniture {
    Furniture::read(&format!("gemba\t2\t{said}\t{behind}"))
}

#[test]
fn the_walk_is_drawn_in_a_box_under_the_line_that_asked() {
    let d = doc("one\ngemba\nthree");
    let chrome = walking("reading the card", 0);
    let mut v = View { aside: 0, ..rows_of(6, 900) };
    v.grant(&chrome, &LARGE);
    let ch = v.ch(&LARGE);
    let f = frame_with(&d, &v, &LARGE, &chrome);

    let said: Vec<(&String, &i32)> = f.items.iter().filter_map(|i| match i {
        Item::Run { s, y, c, .. } if s == "reading the card" => Some((s, y)),
        _ => None,
    }).collect();
    assert_eq!(said.len(), 1, "the narration is drawn once");
    assert_eq!(*said[0].1, 2 * ch, "in the box's first row, under line 2");
}

#[test]
fn a_narration_is_not_a_complaint() {
    // **The colour is the claim.**  A box drawn in the colour that
    // means *your program is wrong* would be saying something untrue
    // about work going perfectly well.
    let d = doc("one\ngemba\nthree");
    let chrome = walking("building the thing", 0);
    let mut v = View { aside: 0, ..rows_of(6, 900) };
    v.grant(&chrome, &LARGE);
    let f = frame_with(&d, &v, &LARGE, &chrome);
    let colour = f.items.iter().find_map(|i| match i {
        Item::Run { s, c, .. } if s == "building the thing" => Some(*c),
        _ => None,
    });
    assert_eq!(colour, Some(INK));
    assert!(!f.items.iter().any(|i| matches!(i, Item::Rect { x: 0, c, .. }
                                            if *c == ANGRY)),
            "and no complaint mark in the gutter");
}

#[test]
fn the_backlog_is_a_mark_and_not_a_number() {
    // `spec/rocks.md`: a number a person has to read is a number a
    // person will not read.  The depth is meant to be felt at a glance
    // while reading something else.
    let d = doc("one\ngemba\nthree");
    let deep = walking("one thing", 6);
    let mut v = View { aside: 0, ..rows_of(8, 900) };
    v.grant(&deep, &LARGE);
    let f = frame_with(&d, &v, &LARGE, &deep);
    assert!(!f.items.iter().any(|i| matches!(i, Item::Run { s, .. }
                                            if s.contains('6'))),
            "nothing says six");
    let bar = f.items.iter().find_map(|i| match i {
        Item::Rect { x: 4, w, c, .. } if *c == FAINT => Some(*w),
        _ => None,
    });
    assert!(bar.is_some(), "there is a mark");
    // And it grows with the backlog, which is the whole of its meaning.
    let shallow = walking("one thing", 2);
    let mut v2 = View { aside: 0, ..rows_of(8, 900) };
    v2.grant(&shallow, &LARGE);
    let f2 = frame_with(&d, &v2, &LARGE, &shallow);
    let small = f2.items.iter().find_map(|i| match i {
        Item::Rect { x: 4, w, c, .. } if *c == FAINT => Some(*w),
        _ => None,
    });
    assert!(small < bar, "a deeper backlog is a longer mark");
}

#[test]
fn nothing_waiting_draws_no_mark() {
    let d = doc("one\ngemba\nthree");
    let chrome = walking("all caught up", 0);
    let mut v = View { aside: 0, ..rows_of(6, 900) };
    v.grant(&chrome, &LARGE);
    let f = frame_with(&d, &v, &LARGE, &chrome);
    assert!(!f.items.iter().any(|i| matches!(i, Item::Rect { x: 4, c, .. }
                                            if *c == FAINT)));
}

#[test]
fn a_long_narration_is_wrapped_and_keeps_the_marks_row() {
    let d = doc("one\ngemba\nthree");
    let long: String = std::iter::repeat("word ").take(60).collect();
    let chrome = walking(long.trim(), 3);
    let mut v = View { aside: 0, ..rows_of(12, 900) };
    v.grant(&chrome, &LARGE);
    let f = frame_with(&d, &v, &LARGE, &chrome);
    let rows = f.items.iter().filter(|i| matches!(i, Item::Run { c, .. }
                                                 if *c == INK)).count();
    assert!(rows > 1, "wrapped rather than cut");
    assert!(f.items.iter().any(|i| matches!(i, Item::Rect { x: 4, c, .. }
                                           if *c == FAINT)),
            "and the mark still has its row");
}

#[test]
fn a_window_that_is_told_nothing_draws_no_box() {
    let d = doc("one\ngemba\nthree");
    let quiet = Furniture::read("status\tready");
    let mut v = View { aside: 0, ..rows_of(6, 900) };
    v.grant(&quiet, &LARGE);
    let ch = v.ch(&LARGE);
    let f = frame_with(&d, &v, &LARGE, &quiet);
    let three: Vec<&i32> = f.items.iter().filter_map(|i| match i {
        Item::Run { s, y, .. } if s == "three" => Some(y),
        _ => None,
    }).collect();
    assert_eq!(three, vec![&(2 * ch)], "line 3 was not pushed down");
}

// ── `[gemba]`, and a box only once there is something to say ─────────

#[test]
fn the_corner_says_gemba_while_a_session_is_leading_you() {
    // **A mode you cannot see is a mode you will be surprised by**, and
    // this one opens files.  `board/done/gemba-follow.md`.
    let d = doc("one\ntwo\nthree");
    let following = Furniture::read("gemba\t0\t\t0");
    let mut v = View { aside: 0, ..rows_of(6, 900) };
    v.grant(&following, &LARGE);
    let f = frame_with(&d, &v, &LARGE, &following);
    assert!(f.items.iter().any(|i| matches!(i, Item::Run { s, .. }
                                           if s == "[gemba]")),
            "the corner does not say it");
}

#[test]
fn a_walk_with_nothing_said_yet_draws_no_box() {
    // The word is true from the moment you subscribe; the box only
    // exists once something has been said.
    let d = doc("one\ntwo\nthree");
    let following = Furniture::read("gemba\t0\t\t0");
    let mut v = View { aside: 0, ..rows_of(6, 900) };
    v.grant(&following, &LARGE);
    let ch = v.ch(&LARGE);
    let f = frame_with(&d, &v, &LARGE, &following);
    let three: Vec<&i32> = f.items.iter().filter_map(|i| match i {
        Item::Run { s, y, .. } if s == "three" => Some(y),
        _ => None,
    }).collect();
    assert_eq!(three, vec![&(2 * ch)], "line 3 was pushed down by nothing");
}

#[test]
fn a_window_not_being_walked_says_nothing() {
    let d = doc("one\ntwo\nthree");
    let quiet = Furniture::read("status\tready");
    let mut v = View { aside: 0, ..rows_of(6, 900) };
    v.grant(&quiet, &LARGE);
    let f = frame_with(&d, &v, &LARGE, &quiet);
    assert!(!f.items.iter().any(|i| matches!(i, Item::Run { s, .. }
                                            if s == "[gemba]")));
}

// ── The flag that looks like a default and is a decision ────────────
//
// **F153's `hint`, and a correction worth keeping.**  The card asking
// for this work (`board/done/interface-oracle.md`) said the hint was one of
// three interface changes held by nothing.  It was wrong, and so was
// the session that believed it: `the_bar_teaches_ctrl_k_while_the_
// burger_holds_the_list` above already covers the bar in both
// directions, and it was missed because a grep was truncated and the
// absence was read as evidence.
//
// One thing genuinely had no assertion, and it is the fragile one: the
// **direction the flag starts in**.  It was a literal inside a
// constructor that needs a display, so nothing could reach it — and it
// is precisely the sort of flag a later session flips while tidying,
// because `false` is what a default usually looks like.

/// **A window opens teaching the key.**  F153: the bar says `Ctrl-K`
/// until `Ctrl-K` is used, because that is the one place that can know
/// you have used it, and the teaching is for people who have not.
#[test]
fn a_window_opens_teaching_the_key() {
    assert!(View::fresh(1000, 700, 1).hint,
            "somebody opening the editor has not used Ctrl-K yet, and \
             the bar is the only place that can tell them");
    assert!(!View::default().hint,
            "and a blank view is not somebody opening one — a test that \
             opted into the teaching would make the bar depend on which \
             constructor its caller reached for");
}
