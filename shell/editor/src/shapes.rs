//! The canvas, as shapes — `gestate/gui.py`'s display list, read here.
//!
//! **One painter, two sources.**  `shell/panel` already turns a
//! substrate into `gestate_panel::list::Item` and paints it for the
//! plugin; this reads the same three shapes off the wire so the editor
//! draws the same picture with the same code.  A second painter would
//! be a second set of rounding decisions, and the two windows would
//! disagree about somebody's artwork.
//!
//! Flat lines, tab-separated, a verb first — like everything else that
//! crosses here:
//!
//! ```text
//! rect  <x>  <y>  <w>  <h>  <r>  <g>  <b>
//! dot   <cx> <cy> <r>  <r>  <g>  <b>
//! text  <x>  <y>  <scale>  <r>  <g>  <b>  <string>
//! ```
//!
//! The string comes last because it is the only field that can contain
//! anything: everything before it is a number, so the split is
//! unambiguous however the text is written.

use gestate_panel::list::{Colour, Item};

fn num<T: std::str::FromStr + Default>(p: &[&str], i: usize) -> T {
    p.get(i).and_then(|v| v.parse().ok()).unwrap_or_default()
}

fn colour(p: &[&str], i: usize) -> Colour {
    Colour::rgb(num::<u8>(p, i), num::<u8>(p, i + 1), num::<u8>(p, i + 2))
}

/// Read a picture.  **Never fails** — a line it cannot make sense of is
/// dropped and the rest is drawn, for the reason `Furniture::read` does
/// the same: the failure this must not have is a canvas going blank
/// because a program drew something new.
pub fn read(text: &str) -> Vec<Item> {
    let mut out = Vec::new();
    for line in text.lines() {
        let p: Vec<&str> = line.split('\t').collect();
        match p.first().copied().unwrap_or("") {
            "rect" if p.len() >= 8 => out.push(Item::Rect {
                x: num(&p, 1), y: num(&p, 2),
                w: num(&p, 3), h: num(&p, 4), c: colour(&p, 5),
            }),
            "dot" if p.len() >= 7 => out.push(Item::Dot {
                cx: num(&p, 1), cy: num(&p, 2), r: num(&p, 3),
                c: colour(&p, 4),
            }),
            "text" if p.len() >= 8 => out.push(Item::Text {
                x: num(&p, 1), y: num(&p, 2),
                scale: num::<i32>(&p, 3).max(1),
                c: colour(&p, 4),
                s: p[7..].join("\t"),
            }),
            _ => {}
        }
    }
    out
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn the_three_shapes_read_back() {
        let got = read("rect\t1\t2\t30\t40\t255\t128\t0\n\
                        dot\t5\t6\t7\t10\t20\t30\n\
                        text\t8\t9\t2\t1\t2\t3\tHELLO");
        assert_eq!(got.len(), 3);
        assert!(matches!(got[0], Item::Rect { x: 1, y: 2, w: 30, h: 40, .. }));
        assert!(matches!(got[1], Item::Dot { cx: 5, cy: 6, r: 7, .. }));
        match &got[2] {
            Item::Text { x, y, scale, s, .. } => {
                assert_eq!((*x, *y, *scale), (8, 9, 2));
                assert_eq!(s, "HELLO");
            }
            other => panic!("expected text, got {other:?}"),
        }
    }

    /// The string is last because it is the only field that can contain
    /// anything — including a tab.
    #[test]
    fn a_label_may_contain_anything() {
        let got = read("text\t0\t0\t1\t0\t0\t0\tA\tB");
        match &got[0] {
            Item::Text { s, .. } => assert_eq!(s, "A\tB"),
            other => panic!("{other:?}"),
        }
    }

    /// A line this build cannot read is dropped, never fatal: a canvas
    /// must not go blank because a program drew something new.
    #[test]
    fn nonsense_is_skipped_and_the_rest_is_drawn() {
        let got = read("wobble\t1\t2\nrect\t0\t0\t1\t1\t0\t0\t0\nrect\tshort");
        assert_eq!(got.len(), 1);
    }
}
