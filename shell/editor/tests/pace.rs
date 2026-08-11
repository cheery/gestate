//! Typing must not get slower the longer you type.
//!
//! A persistent rope built by splitting leaves can *fragment*: every
//! single-character insert at one spot cuts a leaf in two, and if
//! nothing ever coalesces them, a long session leaves a tree of tiny
//! pieces.  The editor would start crisp and degrade — which is exactly
//! the complaint that is hardest to reproduce and easiest to dismiss.
//!
//! So the bound here is deliberately **loose**.  It is not a benchmark
//! and must not fail because a machine was busy; it fails when the cost
//! per keystroke has a *shape*, growing with how much has been typed.

use gestate_editor::document::Document;
use std::time::Instant;

/// Type `n` characters in the middle, and say what one cost.
fn cost_per_keystroke(doc: &mut Document, n: usize) -> f64 {
    let t = Instant::now();
    for _ in 0..n {
        doc.insert("x").unwrap();
    }
    t.elapsed().as_nanos() as f64 / n as f64
}

#[test]
fn typing_does_not_slow_down() {
    let base = "the quick brown fox jumps over the lazy dog\n".repeat(6000);
    let mut doc = Document::new(&base);
    doc.seek(base.chars().count() / 2);

    let first = cost_per_keystroke(&mut doc, 500);
    for _ in 0..18 {
        cost_per_keystroke(&mut doc, 500);
    }
    let last = cost_per_keystroke(&mut doc, 500);

    // Ten thousand keystrokes later, a keystroke costs what it did.
    // Five times is far more headroom than a scheduler can eat and far
    // less than fragmentation would take.
    assert!(last < first * 5.0 + 1_000.0,
            "typing got slower: {first:.0} ns/key at the start, \
             {last:.0} ns/key after 10k characters");
}
