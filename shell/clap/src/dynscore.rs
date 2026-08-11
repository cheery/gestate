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
            voice_banks: BANKS, holds: &[],
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
            voice_banks: BANKS, holds: &[],
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
            voice_banks: BANKS, holds: &[],
        };
        assert!(decode(&p, &[1, 0, 96]).is_err());
        assert!(decode(&p, &[1, 0, 96, 59, 4, 0, 60]).is_err());
    }
}

// ── The performer ───────────────────────────────────────────────────────
//
// `audiodynamic.LazyPerformer`, retold.  The same two questions the
// baked cursor answers — advance to a sample, and what changed — plus
// the two only an unfolding score needs:
//
//   * **a stall is absence.**  Rendering never stops; the future waits.
//   * **a note whose beat has passed when it finally appears is
//     dropped.**  A section that lost its place rejoins at the current
//     bar; it does not play the missed bars fast.
//
// The pending heap is what absorbs the stream's small local disorder:
// notes are admitted as they appear but emitted in `(sample,
// releases-first)` order, and only up to the stream's frontier — the
// tick below which nothing new can appear — so nothing sounds that a
// later arrival could contradict.

use std::cmp::Reverse;
use std::collections::{BinaryHeap, HashSet};

use crate::score::{pick_voice, release_voice, score_samples, NoteKey,
                   VoiceState};

/// One end of a note, waiting for its instant.
///
/// The tuple order **is** the ordering: sample, then `order` with 0 for
/// a release and 1 for an onset, so two things at one instant let the
/// release go first and free the voice the onset may want.  `seq` is
/// admission order, which keeps the sort total and therefore
/// reproducible.
#[derive(PartialEq, Eq, PartialOrd, Ord)]
struct Entry {
    sample: i64,
    order: u8,
    seq: u64,
    key: u32,
    bank: usize,
    is_off: bool,
    payload: Vec<i64>,
}

pub struct Performer {
    piece: Piece,
    pending: BinaryHeap<Reverse<Entry>>,
    /// Keys handed out to notes, and the heap's tie-break.
    events: u32,
    seq: u64,
    /// Keys whose onset was dropped — their release is owed nothing.
    dropped: HashSet<u32>,
    /// Keys sounding, whose off is still owed.
    played: HashSet<u32>,
    /// The last sample advanced to; `-1` before the first block.
    position: i64,
    /// The engine sample the piece's tick zero falls at.
    ///
    /// **Samples, not ticks**, and the distinction is load-bearing:
    /// `audiodynamic.LazyPerformer.origin` is a *tick* offset (it
    /// rebases a resumed remainder), while `score::Performer.origin` is
    /// the engine sample score zero stands at.  This is the shell's
    /// meaning, because this performer lives beside the shell's cursor
    /// and shares its transport.  Assigning one to the other type-checks
    /// and is wrong everywhere except at zero — which is exactly where
    /// a plugin starts, so it looks fine until the transport has run.
    pub origin: i64,
    /// How many beats ahead of the clock the stream is forced.
    pub horizon_beats: f64,
    /// The last thing that went wrong.
    pub failed: Option<String>,
}

impl Performer {
    pub fn new(piece: Piece) -> Self {
        Performer {
            piece,
            pending: BinaryHeap::new(),
            events: 0,
            seq: 0,
            dropped: HashSet::new(),
            played: HashSet::new(),
            position: -1,
            origin: 0,
            horizon_beats: 4.0,
            failed: None,
        }
    }

    pub fn stalled(&self) -> bool {
        self.piece.stalled()
    }

    /// Admit one forced note: its two ends into the heap.
    ///
    /// A note whose onset already lies in a delivered block is dropped
    /// here rather than played late — the rejoin rule at its first
    /// gate, the other being in `advance`.
    fn admit(&mut self, n: &Note, tempo: f64, rate: u32, tpb: i64,
             block: i64) {
        let start = self.origin
            + score_samples(n.onset, tempo, rate, tpb);
        let end = (self.origin + score_samples(n.offset, tempo, rate, tpb))
            .max(start);
        if boundary(start, block) <= self.position {
            return;                     // its beat has passed
        }
        let key = self.events;
        self.events += 1;
        self.pending.push(Reverse(Entry {
            sample: start, order: 1, seq: self.seq, key,
            bank: n.bank, is_off: false, payload: n.payload.clone(),
        }));
        self.pending.push(Reverse(Entry {
            sample: end, order: 0, seq: self.seq + 1, key,
            bank: n.bank, is_off: true, payload: Vec::new(),
        }));
        self.seq += 2;
    }

    /// Force the stream to the horizon `t` implies, answering any
    /// question it stops on.
    ///
    /// `held` is what the world holds per bank — the keys the player
    /// has down — and is what `hear holds.<bank>` reads.
    fn pull(&mut self, p: &Program, t: i64, tempo: f64, rate: u32,
            tpb: i64, block: i64, held: &dyn Fn(usize) -> Vec<i64>) {
        // Where the piece's own clock stands: engine samples since its
        // tick zero, turned into ticks.
        let elapsed = (t - self.origin).max(0) as f64;
        let tick_now =
            (elapsed / rate as f64) * (tempo / 60.0) * tpb as f64;
        let horizon = (tick_now
                       + self.horizon_beats * tpb as f64) as i64 + 1;
        for _ in 0..64 {
            let notes = self.piece.pull(p, horizon.max(0), 2_000_000, 4096);
            for n in &notes {
                self.admit(n, tempo, rate, tpb, block);
            }
            if self.piece.failed.is_some() {
                self.failed = self.piece.failed.clone();
                return;
            }
            let Some((tick, chan, _key)) = self.piece.asking() else {
                break;
            };
            // **The reading, at the decision instant** — not before.
            // A question whose downbeat has not arrived stays open: the
            // world it asks about is the world at *its* instant, and
            // answering early would answer with a hand that has not
            // moved yet.
            let due = self.origin + score_samples(tick, tempo, rate, tpb);
            if boundary(due, block) > t {
                break;
            }
            let reading = match p.port_bank(chan) {
                // An unplugged port holds nothing, which is silence and
                // not an error.
                None => Vec::new(),
                Some(bank) => held(bank),
            };
            self.piece.answer(&reading);
            if self.piece.failed.is_some() {
                self.failed = self.piece.failed.clone();
                return;
            }
        }
    }

    /// Perform everything due at or before sample `t`.
    ///
    /// The mirror of `score::Performer::advance`, and deliberately the
    /// same shape: the caller cannot tell which kind of score it has.
    #[allow(clippy::too_many_arguments)]
    pub fn advance(&mut self, p: &Program, tb: &crate::score::Tables,
                   tempo: f64, voices: &mut [Vec<VoiceState>],
                   control: &mut [i64], t: i64, block: i64,
                   held: &dyn Fn(usize) -> Vec<i64>) {
        if self.failed.is_some() {
            return;
        }
        self.pull(p, t, tempo, tb.rate, tb.tpb, block, held);

        // Below this sample the heap is the whole truth; above it, a
        // later arrival could still come first.
        let covered = if self.piece.done() {
            None
        } else {
            Some(self.origin
                 + score_samples(self.piece.frontier(), tempo,
                                 tb.rate, tb.tpb))
        };

        let mut deferred = Vec::new();
        while let Some(Reverse(e)) = self.pending.pop() {
            let at = boundary(e.sample, block);
            if at > t {
                self.pending.push(Reverse(e));
                break;
            }
            // Beyond the frontier a later arrival could still precede
            // it — except a note-off of something already sounding,
            // which owes order to nobody and must play out however long
            // the stall.
            if let Some(c) = covered {
                if e.sample > c && !(e.is_off && self.played.contains(&e.key)) {
                    deferred.push(Reverse(e));
                    continue;
                }
            }
            if e.is_off && self.dropped.contains(&e.key) {
                self.dropped.remove(&e.key);
                continue;
            }
            if !e.is_off && at <= self.position {
                // Admitted in time, but gated behind a stall until its
                // beat had passed: the rejoin rule, at the other gate.
                self.dropped.insert(e.key);
                continue;
            }
            if e.is_off {
                self.played.remove(&e.key);
            } else {
                self.played.insert(e.key);
            }
            perform(tb, &e, self.origin_at(e.sample), voices, control);
        }
        for e in deferred {
            self.pending.push(e);
        }
        self.position = t;
    }

    /// An entry's sample is already the engine's: `admit` added
    /// `origin` when it turned ticks into samples, so there is one
    /// place the offset is applied and this is not it.
    fn origin_at(&self, sample: i64) -> i64 {
        sample
    }
}

fn boundary(at: i64, block: i64) -> i64 {
    (at / block.max(1)) * block.max(1)
}

/// One end of a note into the control slots — `score::Performer`'s own
/// `perform`, over a dynamic entry rather than a tabled one.
fn perform(tb: &crate::score::Tables, e: &Entry, at: i64,
           voices: &mut [Vec<VoiceState>], control: &mut [i64]) {
    // Switched off: the stream still advanced past this note, so
    // switching the score back on rejoins where the music is rather
    // than where it was left — the same rule the baked cursor keeps.
    if !tb.plays.get(e.bank).copied().unwrap_or(true) {
        return;
    }
    // **Every index checked.**  This runs on a host's audio thread, and
    // the bank came off a wire the program wrote: a descriptor that
    // disagreed with the graph would otherwise be a crash in someone
    // else's process rather than a note that does not sound.
    let Some(bank) = tb.banks.get(e.bank) else { return };
    let Some(bank_voices) = voices.get_mut(e.bank) else { return };
    let mut put = |slot: usize, value: i64, control: &mut [i64]| {
        if let Some(c) = control.get_mut(slot) {
            *c = value;
        }
    };
    if e.is_off {
        if let Some(i) = release_voice(bank_voices,
                                       NoteKey::Score(e.key), at) {
            if let Some(chans) = bank.voices.get(i) {
                if let Some(o) = chans.get(1) { put(*o, at + 1, control); }
            }
        }
    } else {
        let i = pick_voice(bank_voices);
        let Some(chans) = bank.voices.get(i) else { return };
        if let Some(v) = bank_voices.get_mut(i) {
            *v = VoiceState {
                key: Some(NoteKey::Score(e.key)),
                started: at,
                released: None,
            };
        }
        if let Some(g) = chans.first() { put(*g, at + 1, control); }
        if let Some(o) = chans.get(1) { put(*o, 0, control); }
        for (slot, value) in chans.iter().skip(2).zip(&e.payload) {
            put(*slot, *value, control);
        }
    }
}

impl Performer {
    /// Stand at score sample `target` as if the piece had been played
    /// from its top, releasing what sounds at engine sample `now`.
    ///
    /// **The descent does the work here, where a replay does it at
    /// home.**  `audiodynamic.LazyPerformer.seek` walks its own history
    /// and answers questions from the thread; a plugin has no thread —
    /// it is being played, not replayed — so it re-opens the stream at
    /// the target tick and lets `liveMain`'s own second argument do the
    /// skipping.  `resumeAt` descends by *declared* widths, so what
    /// stood left of the tick is stepped over rather than forced, which
    /// is why a jump to bar 400 is not a walk through 399 bars.
    ///
    /// The consequence worth stating: a piece that answers a channel
    /// re-asks its questions after a seek rather than replaying the
    /// answers it once gave.  Live, that is right — the world is the
    /// player's hands, and they are where they are now.
    #[allow(clippy::too_many_arguments)]
    pub fn seek(&mut self, p: &Program, tb: &crate::score::Tables,
                tempo: f64, target: i64, now: i64,
                voices: &mut [Vec<VoiceState>], control: &mut [i64]) {
        // **Only the score's own voices.**  A keyboard-held note
        // survives a loop seam because the piece never wrote there —
        // `score::Performer::seek`'s rule, kept.
        for (b, bank) in tb.banks.iter().enumerate() {
            if !tb.plays.get(b).copied().unwrap_or(true) {
                continue;
            }
            let Some(vs) = voices.get_mut(b) else { continue };
            for i in 0..vs.len() {
                if !matches!(vs[i].key, Some(NoteKey::Score(_))) {
                    continue;
                }
                vs[i].key = None;
                vs[i].released = Some(now);
                if let Some(off) = bank.voices.get(i).and_then(|c| c.get(1)) {
                    if let Some(slot) = control.get_mut(*off) {
                        *slot = now + 1;
                    }
                }
            }
        }

        self.pending.clear();
        self.dropped.clear();
        self.played.clear();
        self.position = -1;

        // Ticks the target stands at, and the stream re-rooted there.
        let ticks = if tempo > 0.0 && tb.rate > 0 {
            ((target as f64 / tb.rate as f64) * (tempo / 60.0)
             * tb.tpb as f64) as i64
        } else {
            0
        };
        match Piece::open(p, ticks.max(0)) {
            Ok(piece) => {
                self.piece = piece;
                self.failed = None;
            }
            // A piece that will not re-open goes quiet and says so,
            // rather than carrying on from the wrong place.
            Err(e) => self.failed = Some(e),
        }
    }
}
