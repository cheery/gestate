//! **The rope answers what `balanced.py` answers.**
//!
//! Same discipline as `spec/crust.md`'s: the Python is the oracle, the
//! port is checked against it, and when they differ the Python is right
//! until somebody argues otherwise.
//!
//! The fixture is nine hundred edits at a fixed seed — biased to grow,
//! because a short document never rotates and rotation is the half of
//! an AVL that can be wrong without anything looking wrong — with the
//! oracle's own answers written down beside them.  Replaying it here
//! checks the two agree not merely at the end but at every point along
//! the way, which is what makes a disagreement findable: the first
//! failing line is the edit that broke it.

use gestate_editor::rope::Rope;

/// `\n`, `\t` and `\uXXXX` back to characters — Python's
/// `unicode_escape`, on the way in.
fn unescape(s: &str) -> String {
    let mut out = String::new();
    let mut it = s.chars();
    while let Some(c) = it.next() {
        if c != '\\' {
            out.push(c);
            continue;
        }
        match it.next() {
            Some('n') => out.push('\n'),
            Some('t') => out.push('\t'),
            Some('r') => out.push('\r'),
            Some('\\') => out.push('\\'),
            // Python's `unicode_escape` writes two hex digits after
            // `\x`, four after `\u` and eight after `\U`.
            Some(k @ ('x' | 'u' | 'U')) => {
                let n = match k { 'x' => 2, 'u' => 4, _ => 8 };
                let hex: String = (0..n).filter_map(|_| it.next()).collect();
                let code = u32::from_str_radix(&hex, 16)
                    .unwrap_or_else(|_| panic!("bad escape \\{k}{hex}"));
                out.push(char::from_u32(code).expect("a character"));
            }
            Some(other) => {
                out.push('\\');
                out.push(other);
            }
            None => out.push('\\'),
        }
    }
    out
}

/// The tail of a line, from field `n` on, with its spaces intact — a
/// document's own text may hold them and splitting would eat them.
fn tail(line: &str, n: usize) -> &str {
    let mut at = 0;
    for _ in 0..n {
        match line[at..].find(' ') {
            Some(i) => at += i + 1,
            None => return "",
        }
    }
    &line[at..]
}

#[test]
fn the_port_answers_what_the_oracle_answers() {
    let mut r = Rope::new();
    let mut edits = 0usize;
    let mut asked = 0usize;

    for (no, line) in include_str!("rope.edits").lines().enumerate() {
        let at = format!("line {}: {line}", no + 1);
        let f: Vec<&str> = line.split(' ').collect();
        match f[0] {
            "insert" => {
                let pos: usize = f[1].parse().unwrap();
                r = r.insert(pos, &unescape(tail(line, 2))).expect(&at);
                edits += 1;
            }
            "erase" => {
                let (a, b) = (f[1].parse().unwrap(), f[2].parse().unwrap());
                r = r.erase(a, b).expect(&at);
                edits += 1;
            }
            "?" => {
                asked += 1;
                match f[1] {
                    "len" => assert_eq!(r.len(), f[2].parse().unwrap(), "{at}"),
                    "newlines" =>
                        assert_eq!(r.newlines(), f[2].parse().unwrap(), "{at}"),
                    "row" => assert_eq!(r.row(f[2].parse().unwrap()).expect(&at),
                                        f[3].parse::<usize>().unwrap(), "{at}"),
                    "rowpos" =>
                        assert_eq!(r.rowpos(f[2].parse().unwrap()).expect(&at),
                                   f[3].parse::<usize>().unwrap(), "{at}"),
                    "read" => {
                        let (a, b) = (f[2].parse().unwrap(), f[3].parse().unwrap());
                        assert_eq!(r.read(a, b).expect(&at),
                                   unescape(tail(line, 4)), "{at}");
                    }
                    "text" => assert_eq!(r.text(), unescape(tail(line, 2)), "{at}"),
                    other => panic!("unknown question {other} at {at}"),
                }
                continue;
            }
            other => panic!("unknown fixture verb {other} at {at}"),
        }
        // **Every edit, not every tenth.**  The summaries are the only
        // reason the descents are fast, and a wrong one is a wrong
        // *answer* rather than a slow one — `row` would name the wrong
        // line and nothing would crash.  Checking them here is what
        // makes the first failing line the edit that broke it.
        assert!(r.is_sound(), "the tree lost its invariant at {at}");
    }
    assert!(edits > 800 && asked > 400, "{edits} edits, {asked} questions");
}

/// The document the fixture ends on is a **tree**, and a balanced one.
///
/// A parity test over something that never branched would be a parity
/// test over a linked list.  The bound moves with `SPLIT`: at the
/// reference's eight characters a segment this document was eleven
/// levels deep, at a hundred and twenty-eight it is a handful of nodes
/// — so what is asserted is the *shape law*, not a number that has to
/// be edited whenever the segment size is tuned.
#[test]
fn the_fixture_builds_a_real_tree() {
    let mut r = Rope::new();
    for line in include_str!("rope.edits").lines() {
        let f: Vec<&str> = line.split(' ').collect();
        match f[0] {
            "insert" => r = r.insert(f[1].parse().unwrap(),
                                     &unescape(tail(line, 2))).unwrap(),
            "erase" => r = r.erase(f[1].parse().unwrap(),
                                   f[2].parse().unwrap()).unwrap(),
            _ => {}
        }
    }
    assert!(r.len() > 2000, "only {} characters", r.len());
    assert!(r.rows() > 200, "only {} rows", r.rows());
    assert!(r.is_sound(), "the fixture left the tree unbalanced");
    assert!(r.depth() >= 3, "depth {} — this never branched", r.depth());
    // An AVL over k nodes is under 1.44·log2(k+2) deep.  This is the
    // bound that makes `row` cheap, so it is asserted rather than
    // assumed — and it is written against the node count so that
    // changing the segment size cannot silently invalidate it.
    let nodes = (r.len() as f64 / 128.0).max(1.0);
    let bound = (1.44 * (nodes + 2.0).log2()).ceil() as u32 + 2;
    assert!(r.depth() <= bound,
            "depth {} over ~{nodes:.0} nodes — the bound is {bound}",
            r.depth());
}
