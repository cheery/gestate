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
    /// `Tick`'s constructor tag, when the program has one — the frame
    /// clock's own word.  A canvas folding over `events` stands still
    /// without it (F103-untitled.ges's report), so the walker pulses
    /// `input` with it once a frame, exactly as `Substrate.tick` does
    /// on the reference machine.
    pub tick: Option<i64>,
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
        let mut tick = None;
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
                "tick" => tick = p.get(1).and_then(|t| t.parse().ok()),
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
        Some(Walk { entry, tags, chans, program, tick })
    }

    /// Read a `box`-sectioned payload — every canvas the model can
    /// hand over, keyed (B2, multiple canvas): `box <key>` opens a
    /// section, `program <lines>` bounds its serialized text so
    /// sections may follow each other without a sentinel.  A payload
    /// with no `box` line is the old single format, keyed
    /// `substrate` — the model may learn the word before this window
    /// reads it, and the other way round.  A section this build
    /// cannot walk whole is dropped alone; the rest still walk.
    pub fn read_all(text: &str) -> Vec<(String, Walk)> {
        if !text.lines().any(|l| l.starts_with("box\t")) {
            return Walk::read(text)
                .map(|w| vec![("substrate".to_string(), w)])
                .unwrap_or_default();
        }
        let mut out = Vec::new();
        let mut lines = text.lines().peekable();
        while let Some(line) = lines.next() {
            let p: Vec<&str> = line.split('\t').collect();
            if p.first().copied() != Some("box") {
                continue;
            }
            let key: String = p.get(1).copied().unwrap_or("").into();
            let mut section: Vec<&str> = Vec::new();
            let mut took = None;
            for inner in lines.by_ref() {
                let q: Vec<&str> = inner.split('\t').collect();
                match q.first().copied().unwrap_or("") {
                    "program" => {
                        took = q.get(1).and_then(|n| n.parse::<usize>().ok());
                        break;
                    }
                    _ => section.push(inner),
                }
            }
            let Some(n) = took else { continue };
            section.push("program");
            let body: Vec<&str> =
                lines.by_ref().take(n).collect();
            let whole = section.join("\n") + "\n" + &body.join("\n");
            if let Some(w) = Walk::read(&whole) {
                if !key.is_empty() {
                    out.push((key, w));
                }
            }
        }
        out
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
    /// The frame clock's tag, pulsed into `input` once a frame.
    tick: Option<i64>,
    /// Where the wall clock is written, and when this canvas opened —
    /// `fixme.md` F134.  `now` reads real seconds off a channel the
    /// renderer declares, and a canvas walked *here* mints its own
    /// frames, so it has to write them here too: otherwise `now` would
    /// advance at home and stand still in a `canvas <expr>` box, which
    /// is the same defect one window over.
    ///
    /// `None` for a program that never mentions `now` — the payload
    /// carries the channel only when the program reaches it.
    wall: Option<i64>,
    began: std::time::Instant,
    /// Channel id → declared name, for naming a `touched`.
    names: Vec<(i64, String)>,
    /// What a hand wrote since the last frame — the arrivals for the
    /// next instant, because the picture and the value must move in
    /// the same step.
    pending: Vec<(i64, f64)>,
    /// Whole windows arriving beside the scalars — a scope's trace as
    /// the `List Float` its channel declared (`spec/scope.md`).
    pending_lists: Vec<(i64, Vec<f64>)>,
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
        let wall = canvas.channel("wallclock");
        Ok(Walker { canvas, tick: walk.tick, wall,
                    began: std::time::Instant::now(),
                    names, pending, pending_lists: Vec::new() })
    }

    /// One instant, one picture — everything a hand wrote since the
    /// last frame arrives now, and the display comes back placed at
    /// `(cx, cy)` in window coordinates, so a press needs no second
    /// transform.
    pub fn frame(&mut self, cx: i32, cy: i32) -> &Display {
        let mut writes = std::mem::take(&mut self.pending);
        let lists = std::mem::take(&mut self.pending_lists);
        // The wall clock rides with them, so `now` counts the seconds
        // this box has been open rather than the frames it has drawn.
        if let Some(ch) = self.wall {
            writes.push((ch, self.began.elapsed().as_secs_f64()));
        }
        // The frame's own Tick rides with the writes — one instant,
        // exactly what `Substrate.tick` mints per frame at home.
        self.canvas.advance(&writes, &lists, self.tick, cx, cy);
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
    /// was let go — and says *what* let go, when the thing it held
    /// had a name.
    ///
    /// **The full stop after a slide** (`spec/workbench.md` §"The
    /// canvas walks over crust").  A `touched` streams and coalesces
    /// to where the hand ended, which is everything a fader needs and
    /// nothing a gesture that must *commit* can use: a score box's
    /// drag is one text edit, one undo entry, one rebuild, and
    /// without this it cannot know when to make them.
    pub fn release(&mut self) -> Option<String> {
        let held = self.canvas.grabbed().and_then(|c| {
            self.names.iter().find(|(id, _)| *id == c)
                .map(|(_, n)| n.clone())
        });
        self.canvas.release();
        held
    }

    /// The instrument's fact arriving by name — `reading peak 0.53`,
    /// the other direction from a touch.  A name the program never
    /// declared is not written and not paid for, the same lenience
    /// `Substrate.write` keeps on the reference side.
    /// Answers whether this walk *has* that channel — so a caller can
    /// tell a reading that changes this picture from one that does
    /// not.  A score box does not know `peak`, and a frame drawn for
    /// it is a frame nobody asked for.
    pub fn hear(&mut self, name: &str, value: f64) -> bool {
        if let Some((id, _)) = self.names.iter().find(|(_, n)| n == name) {
            self.pending.push((*id, value));
            return true;
        }
        false
    }

    /// A whole window arriving by name — `trace post 0.1 0.2 …`, the
    /// scope's word (`spec/scope.md`).  Consecutive traces on one
    /// channel coalesce to the newest: a frame draws one window, and
    /// stacking the missed ones would replay the past at the wrong
    /// speed.
    pub fn hear_trace(&mut self, name: &str, points: Vec<f64>) {
        if let Some((id, _)) = self.names.iter().find(|(_, n)| n == name) {
            self.pending_lists.retain(|(c, _)| *c != *id);
            self.pending_lists.push((*id, points));
        }
    }

    pub fn is_grabbing(&self) -> bool {
        self.canvas.is_grabbing()
    }
}

/// `reading` lines to `(name, value)` pairs — the furniture's
/// lenience: a line that is not one loses that line, never the rest.
pub fn readings(text: &str) -> Vec<(String, f64)> {
    text.lines()
        .filter_map(|line| {
            let p: Vec<&str> = line.split('\t').collect();
            if p.first() != Some(&"reading") {
                return None;
            }
            Some((p.get(1)?.to_string(), p.get(2)?.parse().ok()?))
        })
        .collect()
}

/// `trace` lines to `(name, points)` — the same lenience: a point
/// that does not parse loses that point, a line that is not a trace
/// loses that line, never the rest.
pub fn traces(text: &str) -> Vec<(String, Vec<f64>)> {
    text.lines()
        .filter_map(|line| {
            let p: Vec<&str> = line.split('\t').collect();
            if p.first() != Some(&"trace") {
                return None;
            }
            Some((p.get(1)?.to_string(),
                  p[2..].iter().filter_map(|v| v.parse().ok()).collect()))
        })
        .collect()
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
        assert!(Walk::read_all("").is_empty());
    }

    #[test]
    fn box_sections_read_as_their_own_walks() {
        // Multiple canvas (B2): `box <key>` opens a section and
        // `program <lines>` bounds its text, so sections follow each
        // other without a sentinel.
        let two = "box\tsubstrate\n\
            entry\tmain\n\
            tags\t1 2 3 4 5 6 7 8 9 10 11 12 13 14\n\
            chan\tdragged\t0.75\n\
            program\t2\n\
            crust 1\n\
            I PushInt 3\n\
            box\t__canvas_0__\n\
            entry\tmain\n\
            tags\t1 2 3 4 5 6 7 8 9 10 11 12 13 14\n\
            program\t1\n\
            crust 1";
        let walks = Walk::read_all(two);
        assert_eq!(walks.len(), 2);
        assert_eq!(walks[0].0, "substrate");
        assert!(walks[0].1.program.ends_with("I PushInt 3"));
        assert_eq!(walks[1].0, "__canvas_0__");
        assert_eq!(walks[1].1.program, "crust 1");
    }

    #[test]
    fn the_old_single_payload_still_walks_as_the_substrate() {
        // A model that has not learned `box` hands the old format;
        // this window keys it `substrate` and walks it as ever.
        let walks = Walk::read_all(SOME);
        assert_eq!(walks.len(), 1);
        assert_eq!(walks[0].0, "substrate");
        assert_eq!(walks[0].1.entry, "main");
    }

    #[test]
    fn a_refusing_section_is_dropped_alone() {
        let mixed = "box\tsubstrate\n\
            entry\tmain\n\
            tags\t1 2 3\n\
            program\t1\n\
            crust 1\n\
            box\t__canvas_0__\n\
            entry\tmain\n\
            tags\t1 2 3 4 5 6 7 8 9 10 11 12 13 14\n\
            program\t1\n\
            crust 1";
        let walks = Walk::read_all(mixed);
        assert_eq!(walks.len(), 1);
        assert_eq!(walks[0].0, "__canvas_0__");
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
        // A channel this walk does not have is not this walk's news:
        // the boxes share one reading stream and a score box has no
        // `peak`, so `hear` says whether it took it.
        assert!(w.hear("dragged", 0.25), "it did not take its own channel");
        assert!(!w.hear("peak", 0.5), "it took a channel it does not have");
        // And the release says what let go, which is what a gesture
        // that has to commit waits for.
        assert_eq!(w.release(), Some("dragged".to_string()));
        assert!(!w.is_grabbing());
        assert_eq!(w.release(), None, "nothing was held the second time");
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

#[cfg(test)]
mod reading_tests {
    use super::*;

    #[test]
    fn a_reading_moves_the_picture_by_name() {
        let walk = Walk::read(include_str!("../tests/fader.walk"))
            .expect("reads");
        let mut w = Walker::open(&walk).expect("loads");
        let before = w.frame(100, 100).items.clone();
        w.hear("dragged", 0.95);
        let after = w.frame(100, 100).items.clone();
        assert_ne!(before, after, "the reading changed nothing");
        // A name the program never declared is not written.
        w.hear("nosuch", 0.5);
        let still = w.frame(100, 100).items.clone();
        assert_eq!(after, still);
    }

    #[test]
    fn reading_lines_read_leniently() {
        let text = "reading\tpeak\t0.53\n\
                    reading\tbroken\n\
                    noise\tignored\n\
                    reading\tposition\t120";
        assert_eq!(readings(text),
                   vec![("peak".into(), 0.53),
                        ("position".into(), 120.0)]);
    }
}

#[cfg(test)]
mod tick_tests {
    use super::*;

    /// `tests/ticker.walk` — a canvas folding over `events`
    /// (F103-untitled.ges's shape), written by the model the same way
    /// `fader.walk` was.
    const TICKER: &str = include_str!("../tests/ticker.walk");

    #[test]
    fn the_frame_clock_advances_the_fold() {
        let walk = Walk::read(TICKER).expect("reads");
        assert!(walk.tick.is_some(), "the payload lost the Tick tag");
        let mut w = Walker::open(&walk).expect("loads");
        let first = w.frame(100, 100).items.clone();
        let second = w.frame(100, 100).items.clone();
        assert_ne!(first, second,
                   "two frames drew the same — the event clock stood \
                    still, which is a canvas that does not animate");
    }

    #[test]
    fn a_payload_without_a_tick_still_walks() {
        // An old model that never learned the word: the canvas stands
        // still, and everything else works.
        let stripped: String = TICKER.lines()
            .filter(|l| !l.starts_with("tick\t"))
            .collect::<Vec<_>>()
            .join("\n");
        let walk = Walk::read(&stripped).expect("reads");
        assert_eq!(walk.tick, None);
        let mut w = Walker::open(&walk).expect("loads");
        let first = w.frame(100, 100).items.clone();
        let second = w.frame(100, 100).items.clone();
        assert_eq!(first, second, "still is what no clock means");
    }
}

#[cfg(test)]
mod trace_tests {
    use super::*;

    /// `tests/scoped.walk` — `examples/audio/scoped.ges`'s canvas,
    /// written by the model like the other fixtures.
    const SCOPED: &str = include_str!("../tests/scoped.walk");

    #[test]
    fn a_trace_arrives_as_the_list_its_channel_declared() {
        let walk = Walk::read(SCOPED).expect("reads");
        let mut w = Walker::open(&walk).expect("loads");
        let flat = w.frame(100, 100).items.clone();
        w.hear_trace("post", vec![0.15; 128]);
        let drawn = w.frame(100, 100).items.clone();
        assert_ne!(flat, drawn, "the trace changed nothing on screen");
        assert!(drawn.len() > flat.len(),
                "128 points should be 128 more marks, got {} over {}",
                drawn.len(), flat.len());
        // The newest window wins when frames fall behind.
        w.hear_trace("post", vec![0.1; 128]);
        w.hear_trace("post", vec![0.2; 128]);
        let last = w.frame(100, 100).items.clone();
        assert_ne!(drawn, last);
    }

    #[test]
    fn trace_lines_read_leniently() {
        let text = "reading\tpeak\t0.5\n\
                    trace\tpost\t0.1\t0.2\tnot-a-number\t0.3";
        assert_eq!(traces(text),
                   vec![("post".into(), vec![0.1, 0.2, 0.3])]);
        assert_eq!(readings(text), vec![("peak".into(), 0.5)]);
    }
}
