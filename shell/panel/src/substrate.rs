//! The `Sub` walk — `gestate/gui.py`'s `_extent` and `_walk`, in Rust.
//!
//! `spec/substrate.md`: a substrate is a *value*, built from smaller
//! ones by ordinary functions, and the host walks the tree to draw it.
//! This is that walk, over `crust` instead of the reference machine,
//! producing the same `Display` panel one already produces — which is
//! the dividend from "one painter, two sources": the drawing end needed
//! nothing added.
//!
//! **`Sub` is data, not a function, and that is what keeps hit-testing
//! simple.**  The host accumulates the transform as it descends; when
//! it reaches an attachment it knows the region that attachment ended up
//! occupying, so a press lands, the host finds the deepest attachment
//! containing it, and writes the channel.  `moveXY` moves the picture
//! *and* the hit region because both are read off the same walk.
//!
//! The reference is `gui.py`.  Nothing here decides what a substrate
//! means; it re-walks the same compiled structure, and the two must
//! agree tree for tree.

use crust::{Machine, Node, Num};

use crate::list::{Axis, Colour, Display, Kind};

/// The constructor tags of `gui.ges`'s `Sub`, as this program compiled
/// them.
///
/// **They travel because a tag is a position.**  A tag is that
/// constructor's place in the program's own table, so a host cannot
/// derive one — and a host that guessed would draw a `Row` as whatever
/// happened to share its number.  Same reasoning as the score's cue
/// tags (`spec/dynamicscore.md` stage two).
#[derive(Clone, Copy, Debug)]
pub struct SubTags {
    pub rect: i64,
    pub circle: i64,
    pub gap: i64,
    pub over: i64,
    pub row: i64,
    pub column: i64,
    pub shift: i64,
    pub sized: i64,
    pub pad: i64,
    pub touch_x: i64,
    pub touch_y: i64,
    pub label: i64,
    /// `Cons` and `Nil` — **not `Sub` constructors**, and they are here
    /// because a `Label` carries a `String` and a `String` is
    /// `List Char`.  That is the whole cost of text crossing: no new
    /// node kind and no new instruction, just the two tags any list
    /// needs, which the score's wire already carries for its own
    /// reasons.
    pub cons: i64,
    pub nil: i64,
}

/// What the walk could not do.
#[derive(Debug)]
pub struct SubError(pub String);

type R<T> = Result<T, SubError>;

fn err<T>(what: impl Into<String>) -> R<T> {
    Err(SubError(what.into()))
}

/// Python's `//` — floors — where Rust's `/` truncates.
///
/// Sizes are never negative, so the two agree on every extent; a
/// *centre* can be, and a walk that rounded the other way on the left
/// half of the window would put a shape one pixel from where the
/// reference puts it.  One helper, so the question is asked once.
fn half(n: i32) -> i32 {
    n.div_euclid(2)
}

fn int_at(m: &mut Machine, node: usize) -> R<i32> {
    let n = m.force_node(node);
    match m.heap_at(n) {
        Node::Num(Num::I(v)) => Ok(*v as i32),
        other => err(format!("expected a number, got {other:?}")),
    }
}

/// The font's cell, in the units both hosts agree on.
const CELL_W: i32 = 3;
const CELL_H: i32 = 5;
const CELL_GAP: i32 = 1;

/// The whole scale a label of `n` characters is drawn at in `w`×`h`.
///
/// **A function of declared numbers only**, which is what lets two hosts
/// with different fonts agree without either measuring a glyph: the box
/// is the program's, the cell is the vocabulary's, and the arithmetic is
/// stated in `gui.ges` beside the constructor and mirrored in
/// `gui.py::_fit`.
///
/// Never below one — a label too small for its box is drawn at one and
/// overflows *visibly*, which is the failure an author can see.
pub fn fit(w: i32, h: i32, n: i32) -> i32 {
    if n <= 0 {
        return 1;
    }
    let across = w / (n * (CELL_W + CELL_GAP) - CELL_GAP);
    let down = h / CELL_H;
    across.min(down).max(1)
}

/// A `String` off the heap — `List Char`, and a `Char` is its code
/// point.
///
/// Bounded, because a walk that follows a cons spine is following
/// whatever the program built: an endless string would hang the frame
/// rather than fail it, and a picture is not the place to discover that
/// a list does not terminate.
fn string_at(m: &mut Machine, t: &SubTags, node: usize) -> R<String> {
    let mut out = String::new();
    let mut cell = m.force_node(node);
    for _ in 0..4096 {
        let (tag, args) = match m.heap_at(cell) {
            Node::Con(tag, args) => (*tag, args.clone()),
            other => return err(format!("expected a list cell, got {other:?}")),
        };
        if tag == t.nil {
            return Ok(out);
        }
        if tag != t.cons || args.len() != 2 {
            return err(format!("expected a list cell, got tag {tag}"));
        }
        let code = int_at(m, args[0])? as u32;
        out.push(char::from_u32(code).unwrap_or('?'));
        cell = m.force_node(args[1]);
    }
    err("a label's text did not end within 4096 characters")
}

fn colour_at(m: &mut Machine, node: usize) -> R<Colour> {
    let n = m.force_node(node);
    let args = match m.heap_at(n) {
        Node::Con(_, a) if a.len() == 3 => a.clone(),
        _ => return err("expected an RGB colour"),
    };
    let mut rgb = [0u8; 3];
    for (i, a) in args.iter().enumerate() {
        rgb[i] = int_at(m, *a)?.clamp(0, 255) as u8;
    }
    Ok(Colour::rgb(rgb[0], rgb[1], rgb[2]))
}

/// The channel a program put *inside* the structure, as the id to
/// write.
///
/// This is the whole attachment mechanism: a `Chan a` is first-class,
/// it may sit in a constructor field, and at run time it is a channel
/// node — so a host walking the tree to draw it finds the id it needs,
/// in its hand, at the node that named it.  Nobody refers to a channel
/// by position or by name.
fn chan_at(m: &mut Machine, node: usize) -> R<i64> {
    let n = m.force_node(node);
    match m.heap_at(n) {
        Node::Chan(id) => Ok(*id),
        other => err(format!("expected a channel, got {other:?}")),
    }
}

fn con_at(m: &mut Machine, node: usize) -> R<(i64, Vec<usize>)> {
    let n = m.force_node(node);
    match m.heap_at(n) {
        Node::Con(t, a) => Ok((*t, a.clone())),
        other => err(format!("expected a substrate, got {other:?}")),
    }
}

/// How much room a substrate occupies, in pixels.
///
/// **Declared, never measured.**  A leaf's extent is the number it was
/// built with and a combinator's is a rule over its children's —
/// nothing here looks at what got painted.  Inferring it from the
/// drawing would give `Gap` no size at all (it draws nothing and is
/// *entirely* size), and would make a layout shift when a colour
/// changed to the background's.
pub fn extent(m: &mut Machine, t: &SubTags, node: usize) -> R<(i32, i32)> {
    let (tag, args) = con_at(m, node)?;
    if tag == t.rect || tag == t.gap || tag == t.label {
        // A label's extent is **the box the program declared**, never
        // what the letters came out as.  That distinction is what makes
        // a label admissible where a text editor was not: an editor
        // needs to measure, and this reserves.
        Ok((int_at(m, args[0])?, int_at(m, args[1])?))
    } else if tag == t.circle {
        let r = int_at(m, args[0])?;
        Ok((2 * r, 2 * r))
    } else if tag == t.over {
        let (aw, ah) = extent(m, t, args[0])?;
        let (bw, bh) = extent(m, t, args[1])?;
        Ok((aw.max(bw), ah.max(bh)))
    } else if tag == t.row {
        let (aw, ah) = extent(m, t, args[0])?;
        let (bw, bh) = extent(m, t, args[1])?;
        Ok((aw + bw, ah.max(bh)))
    } else if tag == t.column {
        let (aw, ah) = extent(m, t, args[0])?;
        let (bw, bh) = extent(m, t, args[1])?;
        Ok((aw.max(bw), ah + bh))
    } else if tag == t.shift {
        // **Layout-neutral, and this is where that is decided.**  The
        // extent is the child's *unmoved*, so a handle sliding inside a
        // fader does not resize the fader and does not shuffle whatever
        // is in the row beside it.  A `moveXY` that grew the extent
        // would make every animation relayout the window.
        extent(m, t, args[2])
    } else if tag == t.sized {
        Ok((int_at(m, args[0])?, int_at(m, args[1])?))
    } else if tag == t.pad {
        let n = int_at(m, args[0])?;
        let (w, h) = extent(m, t, args[1])?;
        Ok((w + 2 * n, h + 2 * n))
    } else if tag == t.touch_x || tag == t.touch_y {
        extent(m, t, args[1])
    } else {
        err(format!("unknown substrate tag {tag}"))
    }
}

/// Draw a `Sub` and record what listens, in one descent.
///
/// `cx, cy` is where this element's **centre** goes.  Every element is
/// placed by its centre and every combinator lines its children up by
/// theirs, so there is no alignment argument anywhere — one agreed
/// point on each thing, and the arranging has nothing left to decide.
///
/// **Painter's order, left to right.**  `over a b` is `a` and then `b`,
/// so `b` is on top: the order is in the program rather than in the
/// file, because composition is the thing you are meant to be able to
/// read.
///
/// `hits` comes out **innermost first**, because an attachment is
/// recorded after the subtree it wraps — which is also the order a
/// press wants, since the deepest attachment containing a point is the
/// one that gets it.
pub fn walk(m: &mut Machine, t: &SubTags, node: usize,
            cx: i32, cy: i32, d: &mut Display) -> R<()> {
    let (tag, args) = con_at(m, node)?;
    if tag == t.rect {
        let (w, h) = (int_at(m, args[0])?, int_at(m, args[1])?);
        let c = colour_at(m, args[2])?;
        d.rect(cx - half(w), cy - half(h), w, h, c);
    } else if tag == t.circle {
        let r = int_at(m, args[0])?;
        let c = colour_at(m, args[1])?;
        d.dot(cx, cy, r, c);
    } else if tag == t.label {
        let (w, h) = (int_at(m, args[0])?, int_at(m, args[1])?);
        let text = string_at(m, t, args[2])?.to_uppercase();
        let c = colour_at(m, args[3])?;
        let n = text.chars().count() as i32;
        let s = fit(w, h, n);
        // Placed by its top-left, like a rect, and centred in its own
        // declared box — so the item says where the glyphs go and a
        // painter needs no second rule.
        let tw = if n == 0 { 0 } else { (n * (CELL_W + CELL_GAP) - CELL_GAP) * s };
        let th = CELL_H * s;
        d.text(cx - half(tw), cy - half(th), &text, c, s);
    } else if tag == t.gap {
        // Room, and nothing in it.
    } else if tag == t.over {
        walk(m, t, args[0], cx, cy, d)?;
        walk(m, t, args[1], cx, cy, d)?;
    } else if tag == t.row {
        let (aw, _) = extent(m, t, args[0])?;
        let (bw, _) = extent(m, t, args[1])?;
        let left = cx - half(aw + bw);
        walk(m, t, args[0], left + half(aw), cy, d)?;
        walk(m, t, args[1], left + aw + half(bw), cy, d)?;
    } else if tag == t.column {
        let (_, ah) = extent(m, t, args[0])?;
        let (_, bh) = extent(m, t, args[1])?;
        let top = cy - half(ah + bh);
        walk(m, t, args[0], cx, top + half(ah), d)?;
        walk(m, t, args[1], cx, top + ah + half(bh), d)?;
    } else if tag == t.shift {
        let (x, y) = (int_at(m, args[0])?, int_at(m, args[1])?);
        walk(m, t, args[2], cx + x, cy + y, d)?;
    } else if tag == t.sized {
        // The child keeps its own size and is centred in the declared
        // box.  Nothing here scales a picture: this says how much room
        // to reserve, which is a different question from how big to
        // draw.
        walk(m, t, args[2], cx, cy, d)?;
    } else if tag == t.pad {
        walk(m, t, args[1], cx, cy, d)?;
    } else if tag == t.touch_x || tag == t.touch_y {
        // **The region is the extent, not the drawing.**  It used to be
        // the bounding box of whatever the subtree painted, which made
        // an element's sensitive area depend on what it happened to be
        // showing — a fader whose handle sat at the top answered presses
        // only near the top, and got taller as you dragged it down.  The
        // extent is what the element *said* it was, so the area is the
        // same whatever is drawn in it.
        let (w, h) = extent(m, t, node)?;
        let (x0, y0) = (cx - half(w), cy - half(h));
        let chan = chan_at(m, args[0])?;
        walk(m, t, args[1], cx, cy, d)?;
        let axis = if tag == t.touch_x { Axis::X } else { Axis::Y };
        d.hit(Kind::Chan(axis, chan), crate::list::NO_PARAM,
              (x0, y0, x0 + w, y0 + h));
    } else {
        return err(format!("unknown substrate tag {tag}"));
    }
    Ok(())
}

/// Draw a whole substrate, centred in a window.
pub fn view(m: &mut Machine, t: &SubTags, root: usize, w: i32, h: i32)
    -> R<Display>
{
    view_at(m, t, root, half(w), half(h))
}

/// The same, centred wherever the caller says.
///
/// **Because a canvas rarely owns the whole window.**  A plugin puts a
/// toolbar over it, and the alternative to moving the centre is to
/// walk into the canvas's own coordinates and translate every item and
/// every region afterwards — two passes that must agree, which is
/// exactly the class of mistake that makes a picture and the thing
/// that listens to it drift apart.  The walk already places by a
/// centre it is handed; handing it a different one is free.
pub fn view_at(m: &mut Machine, t: &SubTags, root: usize, cx: i32, cy: i32)
    -> R<Display>
{
    let mut d = Display::new();
    walk(m, t, root, cx, cy, &mut d)?;
    Ok(d)
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::list::Item;
    use crust::{Machine, Node, Num};

    const T: SubTags = SubTags {
        rect: 10, circle: 11, gap: 12, over: 13, row: 14, column: 15,
        shift: 16, sized: 17, pad: 18, touch_x: 19, touch_y: 20,
        label: 21, cons: 1, nil: 0,
    };

    fn machine() -> Machine {
        let (m, _e) = Machine::from_text(
            "crust 1\nblock\nI Unwind\nglobal main 0 0\nentry main\n");
        m
    }

    fn int(m: &mut Machine, v: i32) -> usize {
        m.alloc(Node::Num(Num::I(v as i128)))
    }

    fn colour(m: &mut Machine, r: i32, g: i32, b: i32) -> usize {
        let args = vec![int(m, r), int(m, g), int(m, b)];
        m.alloc(Node::Con(99, args))
    }

    fn rect(m: &mut Machine, w: i32, h: i32) -> usize {
        let c = colour(m, 1, 2, 3);
        let args = vec![int(m, w), int(m, h), c];
        m.alloc(Node::Con(T.rect, args))
    }

    fn con(m: &mut Machine, tag: i64, args: Vec<usize>) -> usize {
        m.alloc(Node::Con(tag, args))
    }

    fn rects(d: &Display) -> Vec<(i32, i32, i32, i32)> {
        d.items.iter().filter_map(|i| match i {
            Item::Rect { x, y, w, h, .. } => Some((*x, *y, *w, *h)),
            _ => None,
        }).collect()
    }

    #[test]
    fn a_rect_is_placed_by_its_centre() {
        let mut m = machine();
        let r = rect(&mut m, 20, 10);
        let d = view(&mut m, &T, r, 100, 100).unwrap();
        assert_eq!(rects(&d), vec![(40, 45, 20, 10)]);
    }

    #[test]
    fn a_row_lines_its_children_up_by_their_centres() {
        let mut m = machine();
        let a = rect(&mut m, 20, 10);
        let b = rect(&mut m, 40, 10);
        let row = con(&mut m, T.row, vec![a, b]);
        assert_eq!(extent(&mut m, &T, row).unwrap(), (60, 10));
        let d = view(&mut m, &T, row, 100, 100).unwrap();
        // The pair is 60 wide, centred: 20..80.  `a` fills 20..40 and
        // `b` fills 40..80, so they touch and neither overlaps.
        assert_eq!(rects(&d), vec![(20, 45, 20, 10), (40, 45, 40, 10)]);
    }

    #[test]
    fn a_column_stacks_downward() {
        let mut m = machine();
        let a = rect(&mut m, 10, 20);
        let b = rect(&mut m, 10, 40);
        let col = con(&mut m, T.column, vec![a, b]);
        assert_eq!(extent(&mut m, &T, col).unwrap(), (10, 60));
        let d = view(&mut m, &T, col, 100, 100).unwrap();
        assert_eq!(rects(&d), vec![(45, 20, 10, 20), (45, 40, 10, 40)]);
    }

    #[test]
    fn over_is_painters_order() {
        let mut m = machine();
        let under = rect(&mut m, 40, 40);
        let onto = rect(&mut m, 10, 10);
        let o = con(&mut m, T.over, vec![under, onto]);
        assert_eq!(extent(&mut m, &T, o).unwrap(), (40, 40));
        let d = view(&mut m, &T, o, 100, 100).unwrap();
        // `over a b` draws `a` then `b`, so `b` is on top — the order is
        // in the program, not in the file.
        assert_eq!(rects(&d), vec![(30, 30, 40, 40), (45, 45, 10, 10)]);
    }

    #[test]
    fn shift_moves_the_picture_but_not_the_layout() {
        let mut m = machine();
        let r = rect(&mut m, 20, 10);
        let (dx, dy) = (int(&mut m, 7), int(&mut m, -3));
        let sh = con(&mut m, T.shift, vec![dx, dy, r]);
        // Layout-neutral: a handle sliding inside a fader must not
        // resize the fader.
        assert_eq!(extent(&mut m, &T, sh).unwrap(), (20, 10));
        let d = view(&mut m, &T, sh, 100, 100).unwrap();
        assert_eq!(rects(&d), vec![(47, 42, 20, 10)]);
    }

    #[test]
    fn pad_grows_the_extent_and_leaves_the_child_where_it_was() {
        let mut m = machine();
        let r = rect(&mut m, 20, 10);
        let n = int(&mut m, 5);
        let p = con(&mut m, T.pad, vec![n, r]);
        assert_eq!(extent(&mut m, &T, p).unwrap(), (30, 20));
        let d = view(&mut m, &T, p, 100, 100).unwrap();
        assert_eq!(rects(&d), vec![(40, 45, 20, 10)]);
    }

    #[test]
    fn sized_reserves_room_without_scaling_anything() {
        let mut m = machine();
        let r = rect(&mut m, 20, 10);
        let (bw, bh) = (int(&mut m, 80), int(&mut m, 60));
        let s = con(&mut m, T.sized, vec![bw, bh, r]);
        assert_eq!(extent(&mut m, &T, s).unwrap(), (80, 60));
        let d = view(&mut m, &T, s, 100, 100).unwrap();
        assert_eq!(rects(&d), vec![(40, 45, 20, 10)], "the child is unchanged");
    }

    #[test]
    fn a_gap_is_entirely_size() {
        let mut m = machine();
        let (gw, gh) = (int(&mut m, 30), int(&mut m, 40));
        let g = con(&mut m, T.gap, vec![gw, gh]);
        assert_eq!(extent(&mut m, &T, g).unwrap(), (30, 40));
        let d = view(&mut m, &T, g, 100, 100).unwrap();
        assert!(d.items.is_empty(), "room, and nothing in it");
    }

    #[test]
    fn a_circle_is_twice_its_radius() {
        let mut m = machine();
        let c = colour(&mut m, 9, 9, 9);
        let r6 = int(&mut m, 6);
        let circ = con(&mut m, T.circle, vec![r6, c]);
        assert_eq!(extent(&mut m, &T, circ).unwrap(), (12, 12));
        let d = view(&mut m, &T, circ, 100, 100).unwrap();
        assert!(matches!(d.items[0],
                         Item::Dot { cx: 50, cy: 50, r: 6, .. }));
    }

    #[test]
    fn an_attachment_listens_over_its_extent_not_its_drawing() {
        let mut m = machine();
        // A fader: a small handle inside a declared box.  The sensitive
        // area must be the box, or the fader answers presses only where
        // the handle happens to be.
        let handle = rect(&mut m, 12, 8);
        let (zx, zy) = (int(&mut m, 0), int(&mut m, -40));
        let shifted = con(&mut m, T.shift, vec![zx, zy, handle]);
        let (bw, bh) = (int(&mut m, 20), int(&mut m, 100));
        let boxed = con(&mut m, T.sized, vec![bw, bh, shifted]);
        let ch = m.alloc(Node::Chan(77));
        let touch = con(&mut m, T.touch_y, vec![ch, boxed]);

        let d = view(&mut m, &T, touch, 100, 200).unwrap();
        assert_eq!(d.hits.len(), 1);
        let hit = d.hits[0];
        assert_eq!(hit.kind, Kind::Chan(Axis::Y, 77));
        assert_eq!(hit.region, (40, 50, 60, 150), "the declared box");
        // And it grows upward, where screen y grows down.
        assert!(hit.fraction(50, 140) < hit.fraction(50, 60));
    }

    #[test]
    fn attachments_come_out_innermost_first() {
        let mut m = machine();
        let inner_rect = rect(&mut m, 10, 10);
        let ci = m.alloc(Node::Chan(2));
        let inner = con(&mut m, T.touch_x, vec![ci, inner_rect]);
        let co = m.alloc(Node::Chan(1));
        let outer = con(&mut m, T.touch_x, vec![co, inner]);

        let d = view(&mut m, &T, outer, 100, 100).unwrap();
        let chans: Vec<i64> = d.hits.iter().filter_map(|h| match h.kind {
            Kind::Chan(_, c) => Some(c),
            _ => None,
        }).collect();
        // The deepest attachment containing a point is the one that
        // gets it, and `pick` takes the first match.
        assert_eq!(chans, vec![2, 1]);
        assert_eq!(d.pick(50, 50).unwrap().kind, Kind::Chan(Axis::X, 2));
    }

    #[test]
    fn an_unknown_tag_is_refused_by_number() {
        let mut m = machine();
        let bogus = con(&mut m, 123, vec![]);
        let e = view(&mut m, &T, bogus, 10, 10).unwrap_err();
        assert!(e.0.contains("123"), "{}", e.0);
    }
}
