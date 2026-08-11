//! **The piece, forced inside the plugin, equals the piece forced at
//! home.**
//!
//! `spec/crust.md`'s rule, applied to stage two abroad: same compiled
//! instructions in, same events out.  The fixtures beside this file are
//! `examples/audio/moods.ges` — an endless seeded piece — as
//! `gestate.crust.serialize` writes it, and the events
//! `audiodynamic.LiveStream` yields for its first sixteen beats on the
//! *reference* machine.  If this test fails, the port has drifted from
//! the meaning, and `gmachine.py` is the one that is right.

#![cfg(feature = "dynscore")]

use gestate_clap::dynscore::Piece;
use gestate_clap::engine::Program;

fn fixture() -> (String, Program, Vec<(i64, i64, usize, Vec<i64>)>) {
    let text = include_str!("moods.program").to_string();
    let tags = include_str!("moods.tags");
    let mut lines = tags.lines();
    let head: Vec<&str> = lines.next().unwrap().split_whitespace().collect();
    let banks: Vec<(i64, usize)> = lines
        .filter(|l| !l.trim().is_empty())
        .map(|l| {
            let mut it = l.split_whitespace();
            (it.next().unwrap().parse().unwrap(),
             it.next().unwrap().parse().unwrap())
        })
        .collect();

    // `Program` holds `&'static` — the fixtures are leaked once, which
    // is what a test binary's lifetime makes honest.
    let program = Program {
        text: Box::leak(text.clone().into_boxed_str()),
        entry: Box::leak(head[0].to_string().into_boxed_str()),
        seed: head[1].parse().unwrap(),
        cons_tag: head[2].parse().unwrap(),
        nil_tag: head[3].parse().unwrap(),
        cue_ev_tag: head[4].parse().unwrap(),
        cue_ask_tag: head[5].parse().unwrap(),
        cue_end_tag: head[6].parse().unwrap(),
        voice_banks: Box::leak(banks.into_boxed_slice()),
    };

    let want = include_str!("moods.events")
        .lines()
        .filter(|l| !l.trim().is_empty())
        .map(|l| {
            let v: Vec<i64> =
                l.split_whitespace().map(|w| w.parse().unwrap()).collect();
            (v[0], v[1], v[2] as usize, v[4..].to_vec())
        })
        .collect();
    (text, program, want)
}

#[test]
fn the_plugin_forces_the_piece_the_reference_forces() {
    let (_text, program, want) = fixture();
    let mut piece = Piece::open(&program, 0).expect("the program loaded");

    // Sixteen beats, the horizon the fixture was taken at.  A stall is
    // the budget, not the end — pull again until the horizon is
    // covered, which is exactly what the host does per block.
    let mut got = Vec::new();
    for _ in 0..64 {
        let notes = piece.pull(&program, 96 * 16, 2_000_000, 4096);
        got.extend(notes);
        assert!(piece.failed.is_none(), "{:?}", piece.failed);
        if !piece.stalled() || piece.done() || piece.asking().is_some() {
            break;
        }
    }

    assert_eq!(got.len(), want.len(),
               "the port yielded {} events where the reference yields {}",
               got.len(), want.len());
    for (i, (n, w)) in got.iter().zip(&want).enumerate() {
        assert_eq!((n.onset, n.offset, n.bank, n.payload.clone()),
                   (w.0, w.1, w.2, w.3.clone()),
                   "event {i} differs from the reference");
    }
}

#[test]
fn an_endless_piece_is_bounded_by_its_horizon() {
    let (_t, program, _w) = fixture();
    let mut piece = Piece::open(&program, 0).expect("loaded");
    // `moods` is a `cycle`: it never ends.  Asking for four beats must
    // return four beats' worth and stop, not walk forever.
    let mut n = 0;
    for _ in 0..64 {
        n += piece.pull(&program, 96 * 4, 2_000_000, 4096).len();
        if !piece.stalled() { break; }
    }
    assert!(n > 0, "an endless piece still has a beginning");
    assert!(!piece.done(), "a cycle does not finish");
}

#[test]
fn a_program_that_is_not_one_refuses_rather_than_panics() {
    static BANKS: &[(i64, usize)] = &[];
    let bad = Program {
        text: "not a crust program at all",
        entry: "liveMain", seed: 0, cons_tag: 1, nil_tag: 0,
        cue_ev_tag: 54, cue_ask_tag: 55, cue_end_tag: 56,
        voice_banks: BANKS,
    };
    // A panic here would take a DAW down with it.
    assert!(Piece::open(&bad, 0).is_err());
}
