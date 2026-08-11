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
        holds: &[],
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

fn nd_fixture() -> Program {
    let text = include_str!("nd.program").to_string();
    let tags = include_str!("nd.tags");
    let mut lines = tags.lines();
    let head: Vec<&str> = lines.next().unwrap().split_whitespace().collect();
    let banks: Vec<(i64, usize)> = lines
        .filter(|l| !l.trim().is_empty())
        .map(|l| {
            let mut it = l.split_whitespace();
            (it.next().unwrap().parse().unwrap(),
             it.next().unwrap().parse().unwrap())
        }).collect();
    Program {
        text: Box::leak(text.into_boxed_str()),
        entry: Box::leak(head[0].to_string().into_boxed_str()),
        seed: head[1].parse().unwrap(),
        cons_tag: head[2].parse().unwrap(),
        nil_tag: head[3].parse().unwrap(),
        cue_ev_tag: head[4].parse().unwrap(),
        cue_ask_tag: head[5].parse().unwrap(),
        cue_end_tag: head[6].parse().unwrap(),
        voice_banks: Box::leak(banks.into_boxed_slice()),
        holds: &[],
    }
}

#[test]
fn the_frontier_keeps_up_with_a_blocks_budget() {
    let program = nd_fixture();
    let mut piece = Piece::open(&program, 0).expect("loaded");
    for block in 0..6 {
        let n = piece.pull(&program, 96 * 4, 2_000_000, 4096).len();
        eprintln!("  block {block}: {n} notes, frontier {}, stalled {}",
                  piece.frontier(), piece.stalled());
    }
}

/// The same parity, for a piece with **three** banks and a `Par`
/// across them — `moods` has two and no overlay, and a mapping that
/// worked there could still be wrong here.
#[test]
fn nightdrive_forces_what_the_reference_forces() {
    let text = include_str!("nd.program").to_string();
    let tags = include_str!("nd.tags");
    let mut lines = tags.lines();
    let head: Vec<&str> = lines.next().unwrap().split_whitespace().collect();
    let banks: Vec<(i64, usize)> = lines
        .filter(|l| !l.trim().is_empty())
        .map(|l| {
            let mut it = l.split_whitespace();
            (it.next().unwrap().parse().unwrap(),
             it.next().unwrap().parse().unwrap())
        }).collect();
    let program = Program {
        text: Box::leak(text.into_boxed_str()),
        entry: Box::leak(head[0].to_string().into_boxed_str()),
        seed: head[1].parse().unwrap(),
        cons_tag: head[2].parse().unwrap(),
        nil_tag: head[3].parse().unwrap(),
        cue_ev_tag: head[4].parse().unwrap(),
        cue_ask_tag: head[5].parse().unwrap(),
        cue_end_tag: head[6].parse().unwrap(),
        voice_banks: Box::leak(banks.into_boxed_slice()),
        holds: &[],
    };
    let want: Vec<(i64, i64, usize, Vec<i64>)> = include_str!("nd.events")
        .lines().filter(|l| !l.trim().is_empty())
        .map(|l| {
            let v: Vec<i64> =
                l.split_whitespace().map(|w| w.parse().unwrap()).collect();
            (v[0], v[1], v[2] as usize, v[4..].to_vec())
        }).collect();

    let mut piece = Piece::open(&program, 0).expect("loaded");
    let mut got = Vec::new();
    for _ in 0..64 {
        got.extend(piece.pull(&program, 96 * 8, 2_000_000, 4096));
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
                   (w.0, w.1, w.2, w.3.clone()), "event {i}");
    }
}

/// **Does the performer write anything at all?**
///
/// The parity tests above prove the *machine* forces the right events.
/// This one asks the next question — whether `Performer::advance` turns
/// them into control writes — with no plugin, no CLAP and no audio in
/// the way, so a silence here is the performer's and nowhere else.
#[test]
fn the_performer_writes_the_notes_it_forces() {
    use gestate_clap::dynscore::Performer;
    use gestate_clap::engine::{Bank, Control, Kind};
    use gestate_clap::score::{Tables, VoiceState, FRESH_VOICE};

    let (_t, program, want) = fixture();
    assert!(!want.is_empty(), "the fixture has events to look for");

    // Two banks, two voices each, four slots per voice: gate, off, and
    // two payload fields — `moods`' own shape.
    static B0V0: [usize; 4] = [0, 1, 2, 3];
    static B0V1: [usize; 4] = [4, 5, 6, 7];
    static B1V0: [usize; 4] = [8, 9, 10, 11];
    static B1V1: [usize; 4] = [12, 13, 14, 15];
    static B0: [&[usize]; 2] = [&B0V0, &B0V1];
    static B1: [&[usize]; 2] = [&B1V0, &B1V1];
    static BANKS: [Bank; 2] = [
        Bank { name: "lead", voices: &B0, table: None },
        Bank { name: "bass", voices: &B1, table: None },
    ];
    static CONTROLS: [Control; 0] = [];

    let plays = [true, true];
    let tb = Tables { events: &[], banks: &BANKS, controls: &CONTROLS,
                      plays: &plays, tpb: 96, rate: 44100 };
    let mut voices: Vec<Vec<VoiceState>> =
        vec![vec![FRESH_VOICE; 2], vec![FRESH_VOICE; 2]];
    let mut control = vec![0i64; 16];

    let mut perf = Performer::new(Piece::open(&program, 0).expect("open"));
    let held = |_b: usize| Vec::new();
    let block = 512i64;
    let mut wrote = 0;
    for b in 0..200 {
        let t = (b + 1) * block;
        perf.advance(&program, &tb, 120.0, &mut voices, &mut control,
                     t, block, &held);
        if control.iter().any(|c| *c != 0) {
            wrote = b;
            break;
        }
    }
    assert!(control.iter().any(|c| *c != 0),
            "200 blocks and the performer wrote no control slot at all; \
             failed={:?} stalled={} descending", perf.failed, perf.stalled());
    eprintln!("  first control write at block {wrote}: {control:?}");
}

/// **Does the worker ever answer?**
///
/// The performer works when nothing asks it to wait; the plugin asks it
/// to wait on every press of play, because `rose` is a seek.  If this
/// never returns a stream, `descending` never clears and the score is
/// silent for the rest of the session — which is exactly what a
/// self-playing piece looks like when it plays nothing.
#[test]
fn the_descent_worker_answers() {
    use gestate_clap::descend::Descender;
    use std::time::{Duration, Instant};

    let (_t, program, _w) = fixture();
    // `Descender` wants a `&'static Program`; the fixture leaks already.
    let program: &'static Program = Box::leak(Box::new(program));
    let mut d = Descender::new(program);
    // Prewarm, the way `activate` does.
    d.prewarm(Piece::open(program, 0).expect("spare"));

    assert!(d.request(0, 96), "the request could not be posted");
    assert!(d.awaiting());

    let started = Instant::now();
    let mut got = None;
    while started.elapsed() < Duration::from_secs(5) {
        if let Some(pair) = d.take() {
            got = Some(pair);
            break;
        }
        std::thread::sleep(Duration::from_millis(2));
    }
    let (tick, _piece, _notes) = got.expect(
        "the worker never answered a request for tick 0 in five seconds");
    assert_eq!(tick, 0);
    assert!(!d.awaiting(), "and the request is no longer outstanding");
    eprintln!("  worker answered in {:?}", started.elapsed());
}

/// **The plugin's own sequence**: press play, which is a seek.
///
/// `rose` fires a seek on every press of play, so the performer starts
/// out waiting for the worker.  The two pieces above each work alone;
/// this is them together, in the order `plugin_process` uses them, and
/// it is the last place the silence can be hiding.
#[test]
fn pressing_play_still_reaches_the_control_slots() {
    use gestate_clap::descend::Descender;
    use gestate_clap::dynscore::Performer;
    use gestate_clap::engine::{Bank, Control};
    use gestate_clap::score::{Tables, VoiceState, FRESH_VOICE};

    let (_t, program, _w) = fixture();
    let program: &'static Program = Box::leak(Box::new(program));

    static B0V0: [usize; 4] = [0, 1, 2, 3];
    static B0V1: [usize; 4] = [4, 5, 6, 7];
    static B1V0: [usize; 4] = [8, 9, 10, 11];
    static B1V1: [usize; 4] = [12, 13, 14, 15];
    static B0: [&[usize]; 2] = [&B0V0, &B0V1];
    static B1: [&[usize]; 2] = [&B1V0, &B1V1];
    static BANKS: [Bank; 2] = [
        Bank { name: "lead", voices: &B0, table: None },
        Bank { name: "bass", voices: &B1, table: None },
    ];
    static CONTROLS: [Control; 0] = [];
    let plays = [true, true];
    let tb = Tables { events: &[], banks: &BANKS, controls: &CONTROLS,
                      plays: &plays, tpb: 96, rate: 44100 };

    let mut voices: Vec<Vec<VoiceState>> =
        vec![vec![FRESH_VOICE; 2], vec![FRESH_VOICE; 2]];
    let mut control = vec![0i64; 16];
    let mut perf = Performer::new(Piece::open(program, 0).expect("open"));
    let mut d = Descender::new(program);
    d.prewarm(Piece::open(program, 0).expect("spare"));

    // Press play: `rose` seeks to the transport's position.
    perf.seek(program, &tb, 120.0, 0, 0, &mut voices, &mut control);

    let held = |_b: usize| Vec::new();
    let block = 512i64;
    let mut installed_at = None;
    for b in 0..400 {
        if let Some(tick) = perf.wanted() {
            if !d.awaiting() {
                d.request(tick, tb.tpb);
            }
        }
        if let Some((tick, piece, notes)) = d.take() {
            let old = perf.install(tick, piece, notes);
            d.give_back(old);
            installed_at = Some(b);
        }
        perf.advance(program, &tb, 120.0, &mut voices, &mut control,
                     (b + 1) * block, block, &held);
        if control.iter().any(|c| *c != 0) {
            eprintln!("  installed at block {installed_at:?}, \
                       first write at block {b}");
            return;
        }
        std::thread::sleep(std::time::Duration::from_millis(1));
    }
    panic!("400 blocks after pressing play and no control slot was ever \
            written.  installed_at={installed_at:?} failed={:?}",
           perf.failed);
}

#[test]
fn a_program_that_is_not_one_refuses_rather_than_panics() {
    static BANKS: &[(i64, usize)] = &[];
    let bad = Program {
        text: "not a crust program at all",
        entry: "liveMain", seed: 0, cons_tag: 1, nil_tag: 0,
        cue_ev_tag: 54, cue_ask_tag: 55, cue_end_tag: 56,
        voice_banks: BANKS, holds: &[],
    };
    // A panic here would take a DAW down with it.
    assert!(Piece::open(&bad, 0).is_err());
}
