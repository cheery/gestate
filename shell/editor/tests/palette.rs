//! The command list, checked without a window.
//!
//! `spec/workbench.md`: *there is one mode, you are typing*, and
//! everything else is a named command you can open, filter and read.
//! What is pinned here is the part the view owns — what is typed, what
//! is picked, and that choosing sends a name back.  **Not the ranking**:
//! which commands a query means is a decision with a home in
//! `gestate/session.py`, and a second one here would be two copies of
//! one rule.

use gestate_editor::keys::Key;
use gestate_editor::palette::{Asks, Entry, Palette};
use gestate_editor::view::Item;

fn entry(name: &str, key: &str) -> Entry {
    Entry { usage: name.into(), name: name.into(), args: Vec::new(),
            reverse: String::new(),
            summary: format!("what {name} does."), key: key.into() }
}

fn some() -> Vec<Entry> {
    vec![entry("apply", "Ctrl-S"), entry("audition", ""),
         entry("play", "Space"), entry("loop", "")]
}

fn opened() -> Palette {
    let mut p = Palette::default();
    assert_eq!(p.show(), Asks::Filter(String::new()));
    p.offer(some());
    p
}

#[test]
fn opening_asks_for_everything() {
    let p = opened();
    assert!(p.is_open());
    assert_eq!(p.query(), "");
    assert_eq!(p.entries().len(), 4);
    assert_eq!(p.selected().map(|e| e.name.as_str()), Some("apply"));
}

/// **The palette never ranks.**  It shows what it was handed, in the
/// order it was handed — the model's order, which is the order somebody
/// thought about the commands rather than one the alphabet chose.
#[test]
fn it_shows_what_it_is_given_in_the_order_it_is_given() {
    let mut p = opened();
    // A query the palette itself would have to rank, answered by the
    // model with a deliberately odd order.
    assert_eq!(p.key(Key::Char('a')), Asks::Filter("a".into()));
    p.offer(vec![entry("play", ""), entry("apply", "")]);
    assert_eq!(p.entries().iter().map(|e| e.name.as_str())
                 .collect::<Vec<_>>(), ["play", "apply"]);
}

#[test]
fn typing_asks_for_a_narrower_list() {
    let mut p = opened();
    assert_eq!(p.key(Key::Char('l')), Asks::Filter("l".into()));
    assert_eq!(p.key(Key::Char('o')), Asks::Filter("lo".into()));
    assert_eq!(p.query(), "lo");
    assert_eq!(p.key(Key::Backspace), Asks::Filter("l".into()));
}

/// **Backspace on an empty query closes it**, which is what the key
/// means everywhere else: undo the thing you just did, and the thing
/// you just did was open this.
#[test]
fn backspace_on_nothing_closes_it() {
    let mut p = opened();
    assert_eq!(p.key(Key::Backspace), Asks::Closed);
    assert!(!p.is_open());
    // And a key afterwards is nobody's business.
    assert_eq!(p.key(Key::Char('x')), Asks::Nothing);
}

#[test]
fn moving_and_choosing() {
    let mut p = opened();
    assert_eq!(p.key(Key::Down), Asks::Nothing);
    assert_eq!(p.selected().map(|e| e.name.as_str()), Some("audition"));
    assert_eq!(p.key(Key::Up), Asks::Nothing);
    assert_eq!(p.selected().map(|e| e.name.as_str()), Some("apply"));
    // The ends hold rather than wrapping: a list that wraps under a
    // held arrow takes you somewhere you were not going.
    for _ in 0..9 { p.key(Key::Up); }
    assert_eq!(p.selected().map(|e| e.name.as_str()), Some("apply"));
    for _ in 0..9 { p.key(Key::Down); }
    assert_eq!(p.selected().map(|e| e.name.as_str()), Some("loop"));

    assert_eq!(p.key(Key::Enter), Asks::Run("loop".into(), Vec::new()));
    assert!(!p.is_open(), "choosing closes it");
}

#[test]
fn escape_chooses_nothing() {
    let mut p = opened();
    p.key(Key::Down);
    assert_eq!(p.key(Key::Escape), Asks::Closed);
    assert!(!p.is_open());
}

#[test]
fn choosing_from_an_empty_list_does_nothing() {
    let mut p = opened();
    p.offer(Vec::new());
    assert_eq!(p.selected(), None);
    assert_eq!(p.key(Key::Enter), Asks::Nothing);
    assert!(p.is_open(), "a miss does not close it");
}

/// A longer query is a different question, so the best answer to it is
/// first — but a shorter list must not leave the pick past its end.
#[test]
fn the_pick_survives_the_list_changing() {
    let mut p = opened();
    p.key(Key::Down);
    p.key(Key::Down);
    assert_eq!(p.selected().map(|e| e.name.as_str()), Some("play"));
    // The model answers with fewer than the pick's index.
    p.offer(vec![entry("apply", "")]);
    assert_eq!(p.selected().map(|e| e.name.as_str()), Some("apply"),
               "the pick ran off the end of a shorter list");
    // And typing puts it back at the top.
    p.key(Key::Char('x'));
    p.offer(some());
    assert_eq!(p.selected().map(|e| e.name.as_str()), Some("apply"));
}

// ── What it draws ────────────────────────────────────────────────────────

fn runs(f: &gestate_editor::view::Frame) -> Vec<String> {
    f.items.iter().filter_map(|i| match i {
        Item::Run { s, .. } => Some(s.clone()),
        _ => None,
    }).collect()
}

#[test]
fn a_closed_palette_draws_nothing() {
    let p = Palette::default();
    assert!(p.frame(800, 600, 10, 20, "").items.is_empty());
}

#[test]
fn it_draws_the_query_the_commands_and_their_keys() {
    let mut p = opened();
    p.key(Key::Char('a'));
    p.offer(some());
    let said = runs(&p.frame(800, 600, 10, 20, ""));
    assert_eq!(said[0], "> a", "what has been typed, with a prompt");
    assert!(said.contains(&"apply".to_string()));
    assert!(said.contains(&"Ctrl-S".to_string()),
            "reading the name teaches the key");
    assert!(said.last().unwrap().starts_with("what apply does"),
            "the summary of what is picked, under the list: {said:?}");
}

/// A long list scrolls to keep the pick visible, rather than drawing
/// past the bottom of the window.
#[test]
fn a_long_list_follows_the_pick() {
    let mut p = Palette::default();
    p.show();
    p.offer((0..40).map(|i| entry(&format!("c{i}"), "")).collect());
    for _ in 0..30 { p.key(Key::Down); }
    let said = runs(&p.frame(400, 300, 10, 20, ""));
    assert!(said.iter().any(|s| s == "c30"),
            "the picked row was not drawn: {said:?}");
    // And the box stays inside the window it was given.
    for item in &p.frame(400, 300, 10, 20, "").items {
        if let Item::Rect { y, h, .. } = item {
            assert!(y + h <= 300, "{item:?} is below the window");
        }
    }
}

// ── Reaching a command with the pointer ──────────────────────────────────

/// A click is Enter somewhere else: two ways to reach a command that
/// behaved differently would be two vocabularies, which is the thing the
/// list exists to prevent.
#[test]
fn clicking_a_row_runs_it() {
    let mut p = Palette::default();
    p.show();
    p.offer(some());
    let (cw, ch) = (9, 15);
    // The second row of the list, in the middle of it: the panel starts
    // at `ch`, the query line takes the first row, and rows are `ch` tall.
    let y = ch + 4 + 2 * ch + ch / 2;
    let row = p.row_at(600, 400, cw, ch, 100, y);
    assert_eq!(row, Some(1));
    assert_eq!(p.click(row.unwrap()),
               Asks::Run("audition".into(), Vec::new()));
}

/// The query line is a row you can see and not one you can pick, and
/// outside the panel belongs to the document.
#[test]
fn the_query_line_and_the_page_are_not_rows() {
    let mut p = Palette::default();
    p.show();
    p.offer(some());
    let (cw, ch) = (9, 15);
    assert_eq!(p.row_at(600, 400, cw, ch, 100, ch + 6), None,
               "the query line picks nothing");
    assert_eq!(p.row_at(600, 400, cw, ch, 100, 390), None,
               "below the list is the document");
    assert_eq!(p.row_at(600, 400, cw, ch, 2, ch + 4 + ch + 2), None,
               "left of the panel is the document");
}

#[test]
fn a_closed_list_has_no_rows() {
    let p = Palette::default();
    assert_eq!(p.row_at(600, 400, 9, 15, 100, 40), None);
}
