//! The walked canvas's payload, read — not yet walked.
//!
//! `spec/workbench.md` §"The canvas walks over crust": the model hands
//! this window a compiled substrate to animate for itself — the
//! serialized G-machine program, the entry to force, the `Sub`
//! constructor tags (a tag is a position in that program's own table,
//! so it cannot be derived, only carried), and the declared channels
//! with the values as they stand.  This module is the reading of it,
//! and only the reading: what walks it comes later, and keeping the
//! two apart is what lets the reading be tested without a machine.
//!
//! **Lenient about everything but what makes walking possible** — the
//! furniture's rule, for the furniture's reason: this is a place two
//! languages meet, and the failure it must not have is the window
//! going blank because the model said something new.  An unknown
//! header verb is skipped, so the model may learn a word before this
//! window reads it; but a payload with no program, no entry or a tag
//! table of the wrong size refuses whole, because walking half a
//! canvas draws somebody's artwork wrong rather than not at all.

/// How many constructor tags the walk needs: `gestate_panel`'s
/// `SubTags` twelve, then `Cons` and `Nil` — not `Sub` constructors,
/// but what a `Label`'s `String` is made of.  The same fourteen
/// `export._SUB_CONS` counts, in the same order, and the count is the
/// check: a table of another size is another program's idea of `Sub`.
pub const TAGS: usize = 14;

/// A canvas this window has been handed to walk.
#[derive(Clone, PartialEq, Debug)]
pub struct Walk {
    /// The global to force — `main`, bound to the file's `substrate`.
    pub entry: String,
    /// The constructor tags, `TAGS` of them, `SubTags` order.
    pub tags: Vec<i64>,
    /// Every declared channel in declaration order, with the value it
    /// currently holds when one has been written — so a rebuild does
    /// not snap a fader back to its default.
    pub chans: Vec<(String, Option<f64>)>,
    /// The serialized program, verbatim — `crust.serialize`'s text.
    pub program: String,
}

impl Walk {
    /// Read a payload, or decide there is nothing to walk.
    ///
    /// `None` for the empty payload — the model taking the canvas
    /// back — and for one this build cannot walk whole.  The caller
    /// treats both the same way: nothing walks, and the window is
    /// still a window.
    pub fn read(text: &str) -> Option<Walk> {
        let mut entry = String::new();
        let mut tags: Vec<i64> = Vec::new();
        let mut chans: Vec<(String, Option<f64>)> = Vec::new();
        let mut lines = text.lines();
        for line in lines.by_ref() {
            let p: Vec<&str> = line.split('\t').collect();
            match p.first().copied().unwrap_or("") {
                "entry" => entry = p.get(1).copied().unwrap_or("").into(),
                "tags" => {
                    tags = p.get(1).copied().unwrap_or("")
                        .split_whitespace()
                        .filter_map(|t| t.parse().ok())
                        .collect();
                }
                "chan" => {
                    let Some(name) = p.get(1) else { continue };
                    if name.is_empty() {
                        continue;
                    }
                    chans.push(((*name).into(),
                                p.get(2).and_then(|v| v.parse().ok())));
                }
                // The program is everything after this line, verbatim
                // — it is another format's text, and reading it is the
                // machine's business, not this parser's.
                "program" => break,
                // An unknown verb is skipped, not refused: the model
                // may learn a word before this window reads it.
                _ => {}
            }
        }
        let program: String = lines.collect::<Vec<_>>().join("\n");
        if entry.is_empty() || tags.len() != TAGS || program.is_empty() {
            return None;
        }
        Some(Walk { entry, tags, chans, program })
    }
}

use gestate_panel::canvas::{Canvas, CanvasProgram};
use gestate_panel::list::Display;
use gestate_panel::substrate::SubTags;

/// A walk, walking: the machine loaded, the channels forced, the
/// carried values written, and a hand's writes queued for the next
/// frame.
///
/// This is the editor's use of `gestate_panel::canvas::Canvas`, which
/// the CLAP plugin already drives — one driver, two windows, the same
/// argument as one painter.  What this adds is the workbench's side of
/// the vocabulary: a write is *named* on the way out, because
/// `touched <name> <value>` is what crosses to the model
/// (`spec/workbench.md` §"The canvas walks over crust").
pub struct Walker {
    canvas: Canvas,
    /// Channel id → declared name, for naming a `touched`.
    names: Vec<(i64, String)>,
    /// What a hand wrote since the last frame — the arrivals for the
    /// next instant, because the picture and the value must move in
    /// the same step.
    pending: Vec<(i64, f64)>,
}

fn subtags(t: &[i64]) -> SubTags {
    SubTags { rect: t[0], circle: t[1], gap: t[2], over: t[3], row: t[4],
              column: t[5], shift: t[6], sized: t[7], pad: t[8],
              touch_x: t[9], touch_y: t[10], label: t[11],
              cons: t[12], nil: t[13] }
}

impl Walker {
    /// Load a payload and stand ready to draw it.
    ///
    /// A refusal is a sentence, never a panic — `Canvas::open` keeps
    /// that promise and this passes it on.  The carried values go in
    /// as the first frame's arrivals, so a rebuilt canvas opens with
    /// its faders where the hand left them.
    pub fn open(walk: &Walk) -> Result<Walker, String> {
        let canvas = Canvas::open(CanvasProgram {
            text: walk.program.clone(),
            entry: walk.entry.clone(),
            tags: subtags(&walk.tags),
            chans: walk.chans.iter().map(|(n, _)| n.clone()).collect(),
            // No bridge: the editor routes a touch by name, and has no
            // DAW to hand a parameter to.
            bridge: Vec::new(),
        })?;
        let names = walk.chans.iter()
            .filter_map(|(n, _)| Some((canvas.channel(n)?, n.clone())))
            .collect();
        let pending = walk.chans.iter()
            .filter_map(|(n, v)| Some((canvas.channel(n)?, (*v)?)))
            .collect();
        Ok(Walker { canvas, names, pending })
    }

    /// One instant, one picture — everything a hand wrote since the
    /// last frame arrives now, and the display comes back placed at
    /// `(cx, cy)` in window coordinates, so a press needs no second
    /// transform.
    pub fn frame(&mut self, cx: i32, cy: i32) -> &Display {
        let writes = std::mem::take(&mut self.pending);
        self.canvas.tick(&writes, cx, cy);
        self.canvas.display()
    }

    /// What the canvas could not do, as a sentence.
    pub fn fault(&self) -> Option<&str> {
        self.canvas.fault()
    }

    fn spoken(&mut self, writes: Vec<(i64, f64)>) -> Vec<(String, f64)> {
        let mut out = Vec::new();
        for (chan, value) in writes {
            if let Some((_, name)) =
                self.names.iter().find(|(id, _)| *id == chan)
            {
                out.push((name.clone(), value));
            }
            self.pending.push((chan, value));
        }
        out
    }

    /// A press.  What comes back is what crosses the wire: the writes,
    /// *named* — an anonymous channel still moves the picture, but has
    /// no name to be recorded or heard by.
    pub fn press(&mut self, x: i32, y: i32) -> Vec<(String, f64)> {
        let writes = self.canvas.press(x, y);
        self.spoken(writes)
    }

    /// A motion, while the press's grab holds.
    pub fn motion(&mut self, x: i32, y: i32) -> Vec<(String, f64)> {
        let writes = self.canvas.motion(x, y);
        self.spoken(writes)
    }

    /// A release lets go and writes nothing — a fader stays where it
    /// was let go.
    pub fn release(&mut self) {
        self.canvas.release();
    }

    pub fn is_grabbing(&self) -> bool {
        self.canvas.is_grabbing()
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    const SOME: &str = "entry\tmain\n\
        tags\t1 2 3 4 5 6 7 8 9 10 11 12 13 14\n\
        chan\tdragged\t0.75\n\
        chan\tuntouched\n\
        program\n\
        crust 1\n\
        block\n\
        I PushInt 3";

    #[test]
    fn a_payload_reads_back_as_what_was_said() {
        let w = Walk::read(SOME).expect("a canvas to walk");
        assert_eq!(w.entry, "main");
        assert_eq!(w.tags.len(), TAGS);
        assert_eq!(w.chans,
                   vec![("dragged".into(), Some(0.75)),
                        ("untouched".into(), None)]);
        assert!(w.program.starts_with("crust 1"));
        assert!(w.program.ends_with("I PushInt 3"),
                "the program did not cross verbatim");
    }

    #[test]
    fn an_empty_payload_is_the_canvas_taken_back() {
        assert_eq!(Walk::read(""), None);
    }

    #[test]
    fn half_a_canvas_refuses_whole() {
        // Walking with a truncated tag table would draw the artwork
        // wrong rather than not at all.
        let short = SOME.replace("tags\t1 2 3 4 5 6 7 8 9 10 11 12 13 14",
                                 "tags\t1 2 3");
        assert_eq!(Walk::read(&short), None);
        // And no program is nothing to walk, whatever the header says.
        let headless = "entry\tmain\n\
            tags\t1 2 3 4 5 6 7 8 9 10 11 12 13 14\nprogram\n";
        assert_eq!(Walk::read(headless), None);
    }

    #[test]
    fn an_unknown_verb_loses_a_word_and_not_the_canvas() {
        let extra = SOME.replace("chan\tdragged\t0.75",
                                 "reading\tpeak\t0.5\nchan\tdragged\t0.75");
        let w = Walk::read(&extra).expect("still walks");
        assert_eq!(w.chans.len(), 2);
    }
}

#[cfg(test)]
mod walker_tests {
    use super::*;

    /// `tests/fader.walk` — a real payload, written by the model:
    /// `gui.Substrate(FADER).payload()` with `dragged` at 0.25, the
    /// FADER program `test_substrate.py` walks in Python.  Committed
    /// rather than generated so `cargo test` needs no Python; if the
    /// payload format moves, regenerate it the same way.
    const FADER: &str = include_str!("../tests/fader.walk");

    #[test]
    fn a_real_payload_opens_and_draws() {
        let walk = Walk::read(FADER).expect("the payload reads");
        let mut w = Walker::open(&walk).expect("the program loads");
        let d = w.frame(100, 100);
        assert!(!d.items.is_empty(), "nothing was drawn");
        assert!(!d.hits.is_empty(), "the fader lost its hands");
        assert_eq!(w.fault(), None);
    }

    #[test]
    fn a_carried_value_stands_in_the_first_frame() {
        // The payload carries `dragged` at 0.25; the handle must open
        // there, not at the program's own 0.5 — a rebuild does not
        // snap a fader back to its default.
        let walk = Walk::read(FADER).expect("reads");
        let mut carried = Walker::open(&walk).expect("loads");
        let with = carried.frame(100, 100).items.clone();

        let mut bare = Walk::read(FADER).expect("reads");
        for (_, v) in bare.chans.iter_mut() {
            *v = None;
        }
        let mut fresh = Walker::open(&bare).expect("loads");
        let without = fresh.frame(100, 100).items.clone();
        assert_ne!(with, without,
                   "the carried value changed nothing on screen");
    }

    #[test]
    fn a_press_names_the_channel_it_writes() {
        let walk = Walk::read(FADER).expect("reads");
        let mut w = Walker::open(&walk).expect("loads");
        w.frame(100, 100);
        // The track is 120 tall centred at the program's (25, 60) from
        // the origin at (100, 100): press mid-track.
        let said = w.press(125, 160);
        assert_eq!(said.len(), 1, "the press missed the fader");
        assert_eq!(said[0].0, "dragged");
        assert!((said[0].1 - 0.5).abs() < 0.1,
                "mid-track should be near a half, got {}", said[0].1);
        assert!(w.is_grabbing());
        // The write lands on the next frame, and the picture moves.
        let before = w.frame(100, 100).items.clone();
        let dragged = w.motion(125, 200);
        assert_eq!(dragged[0].0, "dragged");
        assert!(dragged[0].1 > said[0].1, "downward is more");
        let after = w.frame(100, 100).items.clone();
        assert_ne!(before, after, "the handle did not follow the hand");
        w.release();
        assert!(!w.is_grabbing());
    }

    #[test]
    fn a_press_on_nothing_crosses_as_nothing() {
        let walk = Walk::read(FADER).expect("reads");
        let mut w = Walker::open(&walk).expect("loads");
        w.frame(100, 100);
        assert!(w.press(500, 500).is_empty());
        assert!(!w.is_grabbing());
    }
}
