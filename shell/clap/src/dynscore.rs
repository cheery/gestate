//! The piece, forced as it plays — `spec/dynamicscore.md` stage two,
//! abroad.
//!
//! A finite score exports as a list of instants and `score.rs` walks
//! it.  An **unfolding** one has no such list: `cycle (bar >>= …)` is a
//! stream, and the only thing that can produce its next event is the
//! G-machine.  So the plugin carries the *program* (`engine::Program`)
//! and this module forces it, one horizon at a time, on `crust`.
//!
//! **The reference is still `gmachine.py`.**  Nothing here decides what
//! the piece means; it re-runs the same compiled program the Python
//! side runs, and `spec/crust.md`'s parity rule is what makes that
//! claim checkable — same instructions in, same events out.

use std::panic::{catch_unwind, AssertUnwindSafe};

use crate::engine::Program;

/// One event off the wire: the piece's own note, in score ticks.
///
/// `onset` and `offset` are ticks, not samples — turning them into
/// samples needs the tempo, which belongs to the caller and not to the
/// stream.  `bank` is already resolved through `Program::bank_of`, so a
/// voice tag this program does not declare is refused here rather than
/// indexing something arbitrary downstream.
#[derive(Clone, Debug, PartialEq)]
pub struct Note {
    pub onset: i64,
    pub offset: i64,
    pub bank: usize,
    /// The author's payload, already reinterpreted to slot bits.
    pub payload: Vec<i64>,
}

/// The machine and the stream it is forcing.
pub struct Piece {
    machine: crust::Machine,
    stream: crust::Stream,
    /// The last thing that went wrong, if anything.  A piece that
    /// refuses goes quiet and *says so* rather than taking the process
    /// with it — see `guard`.
    pub failed: Option<String>,
}

/// Run something on the machine, catching a refusal.
///
/// **crust refuses by panicking** (`fail`, `panic_any`), which is the
/// right shape for a library with a Python landlord that catches at the
/// ctypes boundary.  A plugin has no such boundary: a panic crossing
/// into a DAW's audio thread takes the host down with it.  So every
/// entry into the machine goes through here, and a refusal becomes
/// silence with a message attached.
fn guard<T>(what: impl FnOnce() -> T) -> Result<T, String> {
    catch_unwind(AssertUnwindSafe(what)).map_err(|e| {
        if let Some(s) = e.downcast_ref::<String>() {
            s.clone()
        } else if let Some(s) = e.downcast_ref::<&str>() {
            (*s).to_string()
        } else {
            "the machine refused".to_string()
        }
    })
}

impl Piece {
    /// Load the program and open its stream at `tick`.
    ///
    /// `liveMain` is resume-aware in its own second argument, so a
    /// plugin that starts mid-timeline opens *there* rather than
    /// replaying from the top — the same descent the editor's rebuild
    /// uses.
    pub fn open(p: &Program, tick: i64) -> Result<Piece, String> {
        let (machine, stream) = guard(|| {
            let (mut m, _entry) = crust::Machine::from_text(p.text);
            let s = crust::Stream::open_live(
                &mut m, p.entry, p.seed, tick,
                p.cons_tag, p.nil_tag,
                p.cue_ev_tag, p.cue_ask_tag, p.cue_end_tag);
            (m, s)
        })?;
        Ok(Piece { machine, stream, failed: None })
    }

    pub fn done(&self) -> bool {
        self.stream.done
    }

    pub fn stalled(&self) -> bool {
        self.stream.stalled
    }

    /// How far the stream is known to have reached, in ticks.
    pub fn frontier(&self) -> i64 {
        self.stream.frontier
    }

    /// A question the piece is waiting on: `(tick, channel, key)`.
    ///
    /// **A question is not a stall.**  Nothing more of the performance
    /// exists until it is answered, and the answer is the world's —
    /// which in a plugin is the keys the player is holding.
    pub fn asking(&self) -> Option<(i64, i64, i64)> {
        self.stream.ask
    }

    /// Answer the question and walk on.
    pub fn answer(&mut self, reading: &[i64]) {
        let Piece { machine, stream, failed } = self;
        if let Err(e) = guard(|| stream.answer(machine, reading)) {
            *failed = Some(e);
        }
    }

    /// Every note whose onset lands before `horizon` ticks, budget
    /// permitting.
    ///
    /// A stall is not an error: the budget ran out and the same call
    /// again continues the walk. `spec/dynamicscore.md`'s rule is that
    /// **absence is the failure mode**, so a caller that sees `stalled`
    /// has to say so rather than treat the empty list as the piece
    /// falling silent.
    pub fn pull(&mut self, p: &Program, horizon: i64, fuel: i64,
                burst: usize) -> Vec<Note> {
        if self.failed.is_some() {
            return Vec::new();
        }
        let Piece { machine, stream, failed } = self;
        let words = match guard(|| {
            stream.pull(machine, horizon, fuel, burst).to_vec()
        }) {
            Ok(w) => w,
            Err(e) => {
                *failed = Some(e);
                return Vec::new();
            }
        };
        match decode(p, &words) {
            Ok(notes) => notes,
            Err(e) => {
                self.failed = Some(e);
                Vec::new()
            }
        }
    }
}

/// The flat wire back into notes.
///
/// `[count, (onset, offset, voice_tag, nwords, payload…) × count]` with
/// each payload entry a `(kind, value)` pair: kind 0 an integer, kind 1
/// a float's IEEE bits, kind 2 a constructor whose value is its child
/// count.
///
/// **`nwords` counts words, not fields**, and the distinction is the
/// whole reason nesting survives the wire: a constructor spends two
/// words of its own before its children spend theirs, so a field count
/// could not say how far the payload reaches.  Reading it as a field
/// count walks off the end of one event and into the next one's onset,
/// which decodes as a voice tag no program declares — the failure this
/// note exists to stop happening twice.
///
/// **Nested payloads are flattened here**, which is what the allocator
/// does with them anyway (`audioscore._flatten`): a constructor
/// contributes its children and nothing of itself, so a record and the
/// fields it holds reach the control slots identically.
fn decode(p: &Program, words: &[i64]) -> Result<Vec<Note>, String> {
    let mut out = Vec::new();
    let mut i = 1usize;
    let count = *words.first().unwrap_or(&0);
    for _ in 0..count {
        if i + 4 > words.len() {
            return Err("a truncated event on the score wire".into());
        }
        let (onset, offset, tag, nwords) =
            (words[i], words[i + 1], words[i + 2], words[i + 3] as usize);
        i += 4;
        let Some(bank) = p.bank_of(tag) else {
            return Err(format!(
                "a note assigned to a voice bank this program does not \
                 declare (constructor tag {tag})"));
        };
        let end = i + nwords;
        if end > words.len() {
            return Err("a truncated payload on the score wire".into());
        }
        let mut payload = Vec::new();
        while i + 2 <= end {
            let (kind, value) = (words[i], words[i + 1]);
            i += 2;
            // kind 2 opens a constructor: it carries no value of its
            // own, only the count of the children that follow, and the
            // children are already in the stream.
            if kind != 2 {
                payload.push(value);
            }
        }
        i = end;
        out.push(Note { onset, offset, bank, payload });
    }
    Ok(out)
}

#[cfg(test)]
mod tests {
    use super::*;

    /// A hand-written wire, to pin the decode without a machine.
    #[test]
    fn the_wire_decodes_to_notes() {
        static BANKS: &[(i64, usize)] = &[(59, 0), (60, 1)];
        let p = Program {
            text: "", entry: "liveMain", seed: 0,
            cons_tag: 1, nil_tag: 0,
            cue_ev_tag: 54, cue_ask_tag: 55, cue_end_tag: 56,
            voice_banks: BANKS,
        };
        // two events: one on bank 0 with two int fields, one on bank 1
        // with a constructor wrapping one field.
        let words = [2,
                     0, 96, 59, 4, 0, 60, 0, 100,
                     96, 192, 60, 4, 2, 1, 0, 64];
        let notes = decode(&p, &words).unwrap();
        assert_eq!(notes, vec![
            Note { onset: 0, offset: 96, bank: 0, payload: vec![60, 100] },
            // the constructor contributes nothing of itself
            Note { onset: 96, offset: 192, bank: 1, payload: vec![64] },
        ]);
    }

    #[test]
    fn an_undeclared_voice_tag_is_refused_by_name() {
        static BANKS: &[(i64, usize)] = &[(59, 0)];
        let p = Program {
            text: "", entry: "liveMain", seed: 0,
            cons_tag: 1, nil_tag: 0,
            cue_ev_tag: 54, cue_ask_tag: 55, cue_end_tag: 56,
            voice_banks: BANKS,
        };
        let err = decode(&p, &[1, 0, 96, 77, 0]).unwrap_err();
        assert!(err.contains("77"), "the refusal must name the tag: {err}");
    }

    #[test]
    fn a_truncated_wire_is_refused_rather_than_indexed() {
        static BANKS: &[(i64, usize)] = &[(59, 0)];
        let p = Program {
            text: "", entry: "liveMain", seed: 0,
            cons_tag: 1, nil_tag: 0,
            cue_ev_tag: 54, cue_ask_tag: 55, cue_end_tag: 56,
            voice_banks: BANKS,
        };
        assert!(decode(&p, &[1, 0, 96]).is_err());
        assert!(decode(&p, &[1, 0, 96, 59, 4, 0, 60]).is_err());
    }
}
