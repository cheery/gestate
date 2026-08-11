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

/// Whether a seek's descent is handed to the worker thread.
///
/// **A switch, because the two failure modes are different and both are
/// real.**  Off the thread, a deep seek costs a *wait* while the worker
/// walks — and if the host gives that worker little CPU, the wait is
/// what a player hears.  On this thread, it costs one long *block*,
/// which a host may or may not forgive.  Flipping this is how the two
/// are told apart on a machine that is not mine.
pub const DESCEND_OFF_THREAD: bool = true;

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
    ///
    /// **The seed is an argument, not `Program.seed`.**  Export bakes
    /// the seed the file was written with; a player turning the RNG
    /// wants a different night out of the same program, and a piece
    /// re-rooted with the exported seed would ignore them.  So the
    /// caller says which seed, every time, and `Program.seed` is only
    /// the default it starts from.
    pub fn open(p: &Program, seed: i64, tick: i64) -> Result<Piece, String> {
        let (machine, stream) = guard(|| {
            let (mut m, _entry) = crust::Machine::from_text(p.text);
            let s = crust::Stream::open_live(
                &mut m, p.entry, seed, tick,
                p.cons_tag, p.nil_tag,
                p.cue_ev_tag, p.cue_ask_tag, p.cue_end_tag);
            (m, s)
        })?;
        Ok(Piece { machine, stream, failed: None })
    }

    /// Re-root the stream at `tick`, **keeping the machine**.
    ///
    /// **Not `open` again**, and the difference is the whole reason
    /// this exists: `open` parses the program and starts a fresh heap,
    /// so every thunk the piece had already forced is thrown away and
    /// paid for again.  A DAW rewinding to the top does not send one
    /// seek — it *revs*, a jump per block — and re-parsing fifty
    /// kilobytes on the audio thread once per block is silence while it
    /// scrubs, then whatever the allocator does about it.
    ///
    /// Re-rooting is a pointer: the heap stays, its forced work stays,
    /// and the collector reclaims the old stream's nodes on the next
    /// pull because nothing roots them any more.
    pub fn reopen(&mut self, p: &Program, seed: i64, tick: i64)
        -> Result<(), String>
    {
        let Piece { machine, stream, failed } = self;
        let fresh = guard(|| {
            crust::Stream::open_live(
                machine, p.entry, seed, tick,
                p.cons_tag, p.nil_tag,
                p.cue_ev_tag, p.cue_ask_tag, p.cue_end_tag)
        })?;
        *stream = fresh;
        *failed = None;
        Ok(())
    }

    /// Compact the heap now — see `crust::Stream::compact`.
    ///
    /// Called by the descent worker before a stream changes hands, so
    /// the audio thread inherits a small heap rather than the bill for
    /// the walk that built it.
    pub fn compact(&mut self) {
        let Piece { machine, stream, failed } = self;
        if let Err(e) = guard(|| stream.compact(machine)) {
            *failed = Some(e);
        }
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
    /// The engine sample the **stream's** tick zero falls at.
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
    /// The descent in flight, if any — a seek asks for a stream and
    /// the audio thread carries on without one until it arrives.
    ///
    /// **The score is silent while this is `Some`.**  That is the
    /// trade: a late entry rather than an overrun, and the signal half
    /// of an instrument keeps playing throughout, so a piece with drums
    /// in its `sound` still has drums (`descend.rs`).
    pub descending: bool,
    /// True until the first pull after a re-root has caught up.
    ///
    /// **A seek is allowed one expensive block.**  Re-rooting is cheap
    /// but the score's own spine is walked again, and four beats of it
    /// under an ordinary per-block budget can take many blocks to
    /// force — during which the piece has no notes and the signal half
    /// of an instrument plays alone.  A transport jump already
    /// interrupts the audio, so spending the work *there* is the right
    /// trade; spreading it over the next thirty blocks is not.
    priming: bool,
    /// How many blocks running the stream has failed to reach its
    /// horizon — what the panel reports when a piece cannot keep up.
    behind: u32,
    /// A seek's target, until a primed stream for it arrives.
    wanted: Option<i64>,
    /// Notes the worker forced while priming, waiting to be admitted.
    primed: Vec<Note>,
    /// Note-ons performed and notes dropped since the counters were
    /// last read.
    ///
    /// **The column that tells three bugs apart.**  `pending` says
    /// notes are waiting; it cannot say whether any were *played*.  A
    /// silent stretch with nothing performed and nothing dropped is a
    /// performer with nothing due; with drops, it is the rejoin rule
    /// throwing away notes whose instant had passed; with performances,
    /// the notes played and the silence is somewhere else entirely.
    played_count: u32,
    dropped_count: u32,
    /// The tick the stream was last rooted at **and has not moved
    /// from**, so a repeated seek to the same place costs nothing.
    ///
    /// Cleared by the first pull, because after that the stream is no
    /// longer *at* that tick — it has walked on.  Recording the root
    /// and not the walking made a seek back to the top look like a
    /// seek to where we already were, so it was skipped and the piece
    /// carried on from wherever it had got to: the transport moved and
    /// the music did not.
    opened_at: Option<i64>,
    /// The seed this performance is running on.
    ///
    /// **Held here because a re-root needs it and the audio thread is
    /// where re-roots are decided.**  The instance owns the number (it
    /// is a parameter, so the host owns it really); this is the copy
    /// the piece was last opened with, and `set_seed` is what notices
    /// the two have parted.
    seed: i64,
}

impl Performer {
    pub fn new(piece: Piece, seed: i64) -> Self {
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
            descending: false,
            priming: true,
            behind: 0,
            wanted: None,
            primed: Vec::new(),
            played_count: 0,
            dropped_count: 0,
            opened_at: Some(0),
            seed,
        }
    }

    pub fn seed(&self) -> i64 {
        self.seed
    }

    /// Take a new seed.  Returns whether it actually changed — a
    /// caller that re-rooted on every block would restart the piece
    /// sixty times a second.
    ///
    /// **Nothing is re-rooted here.**  Changing the seed changes what
    /// the piece *is* from its first instant, so the stream has to be
    /// opened again at wherever the transport stands — which is a
    /// seek, and seeks belong to the block that knows the transport.
    /// This only records the number and says that something must
    /// happen; `lib.rs` turns that into the seek.
    pub fn set_seed(&mut self, seed: i64) -> bool {
        if self.seed == seed {
            return false;
        }
        self.seed = seed;
        true
    }

    pub fn stalled(&self) -> bool {
        self.piece.stalled()
    }

    /// What the instrument needs to say, if anything.
    pub fn complaint(&self) -> Option<String> {
        if let Some(e) = &self.failed {
            return Some(format!("THE PIECE STOPPED: {e}"));
        }
        // A few blocks behind is the budget doing its job; a hundred is
        // a piece this machine cannot force in time.
        if self.descending {
            return None;    // waiting is not a fault
        }
        if self.behind > 100 {
            return Some("THE PIECE IS BEHIND - IT CANNOT BE FORCED IN TIME"
                        .to_string());
        }
        None
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
            self.dropped_count = self.dropped_count.saturating_add(1);
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
        // **The deadline is the budget, not a step count.**
        //
        // Re-rooting is cheap but the *descent* is not: `resumeAt` walks
        // to the target tick, and that walk costs more the deeper into
        // the piece it goes — measured on `nightdrive`, 3 ms at the top
        // and 22 ms eighteen seconds in, against an 11.6 ms block.  A
        // step budget cannot express "and stop before the deadline",
        // because the cost per step is the piece's, not ours.
        //
        // So the priming block watches the clock.  It takes what it can
        // and leaves the rest to the next block: a deep seek starts a
        // little late, which is a musical fault, where an overrun is a
        // dropout in someone else's host.  The real cure is to descend
        // off this thread entirely, and that is a design change rather
        // than a number.
        let started = std::time::Instant::now();
        // A seek's block may spend more of itself catching up than an
        // ordinary one, because it has further to come.
        let share = if self.priming { 0.4 } else { 0.25 };
        let slice = if rate > 0 {
            std::time::Duration::from_secs_f64(
                (block as f64 / rate as f64) * share)
        } else {
            std::time::Duration::from_millis(3)
        };
        // Where the piece's own clock stands: engine samples since its
        // tick zero, turned into ticks.
        let elapsed = (t - self.origin).max(0) as f64;
        let tick_now =
            (elapsed / rate as f64) * (tempo / 60.0) * tpb as f64;
        let horizon = (tick_now
                       + self.horizon_beats * tpb as f64) as i64 + 1;
        // **Small slices while priming, because the clock is only
        // read between pulls.**  A single pull runs to its fuel before
        // it returns, so a large budget makes the deadline check
        // useless — the first pull already overran it.  Priming asks
        // for a little at a time and keeps asking until its slice is
        // spent; an ordinary block asks once, generously, because it
        // is not trying to catch up.
        // **Spend the block's headroom, not a step count.**
        //
        // A fixed budget was the wrong unit: on a stall the stream's
        // frontier stops moving, `advance` defers every note past it,
        // their instants pass while they wait, and the rejoin rule
        // drops them — so the score played in bursts with holes
        // between, while the audio thread sat at three milliseconds of
        // a ten-millisecond block.  There was time; there were no
        // steps left.  Both cases now take small slices and keep
        // asking until the stream is caught up or the slice is gone.
        let fuel = 250_000i64;
        let rounds = 4096;
        for _ in 0..rounds {
            let notes = self.piece.pull(p, horizon.max(0), fuel, 4096);
            for n in &notes {
                self.admit(n, tempo, rate, tpb, block);
            }
            if self.piece.failed.is_some() {
                self.failed = self.piece.failed.clone();
                return;
            }
            // The stream has walked: it is no longer standing where it
            // was rooted, so a later seek back there is a real move.
            self.opened_at = None;
            if self.piece.stalled() {
                if started.elapsed() < slice {
                    continue;   // there is time left in this block
                }
                break;          // and the rest is the next block's
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
        if self.descending {
            // The stream under us is the *old* place.  Forcing it would
            // deliver notes from where the playhead used to be, which
            // is worse than the silence of waiting.
            self.position = t;
            return;
        }
        // The worker's forcing, admitted before this block's own.
        if !self.primed.is_empty() {
            for n in std::mem::take(&mut self.primed) {
                self.admit(&n, tempo, tb.rate, tb.tpb, block);
            }
        }
        self.pull(p, t, tempo, tb.rate, tb.tpb, block, held);
        self.priming = false;
        // A piece that keeps missing its horizon is not silent by
        // choice — `spec/dynamicscore.md`'s rule is that absence is the
        // failure mode, so it has to be reportable.
        if self.piece.stalled() {
            self.behind = self.behind.saturating_add(1);
        } else {
            self.behind = 0;
        }

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
                self.dropped_count = self.dropped_count.saturating_add(1);
                continue;
            }
            if e.is_off {
                self.played.remove(&e.key);
            } else {
                self.played.insert(e.key);
                self.played_count = self.played_count.saturating_add(1);
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
    /// Back to the top, **without rebuilding the machine**.
    ///
    /// What `rose` used to do was construct a whole new `Piece`: parse
    /// the program again and start a cold heap, so every global the
    /// piece had already forced was paid for a second time — under a
    /// per-block fuel budget, which turns into a few hundred
    /// milliseconds of the score not existing yet.  The signals half of
    /// an instrument keeps sounding through that, so it reads as
    /// "pressing play takes a moment, and only the drums come in".
    ///
    /// Re-rooting keeps the heap and its forced work; only the score's
    /// own spine is walked again.
    pub fn restart(&mut self, p: &Program) {
        self.origin = 0;    // `rewind` put the engine clock back to zero
        self.pending.clear();
        self.dropped.clear();
        self.played.clear();
        self.position = -1;
        self.priming = true;
        // **The top is cheap enough to do here.**  A descent to tick
        // zero is no descent at all — `liveMain seed 0` is the piece
        // from its start — so pressing play does not have to wait for a
        // worker, and two plays stay one performance.
        match self.piece.reopen(p, self.seed, 0) {
            Ok(()) => {
                self.opened_at = Some(0);
                self.wanted = None;
                self.descending = false;
                self.failed = None;
            }
            Err(e) => self.failed = Some(e),
        }
    }

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
        self.priming = true;

        // Ticks the target stands at.
        let ticks = if tempo > 0.0 && tb.rate > 0 {
            ((target as f64 / tb.rate as f64) * (tempo / 60.0)
             * tb.tpb as f64) as i64
        } else {
            0
        };
        // The rebased stream's zero is *here*: the engine sample the
        // transport is standing on as it jumps.
        self.origin = now;
        let ticks = ticks.max(0);

        // **The top goes to the worker like everywhere else.**
        //
        // It once did not: `resumeAt 0` is the identity, so a seek to
        // the beginning has no walk in front of it and taking a
        // round-trip for it looked like pure waste.  That reasoning was
        // about the *descent*, and the descent is the cheap half.  The
        // expensive half is the **priming** — forcing the first beats of
        // music — and the worker is what does that.  Routing the top
        // inline made the beginning the one seek that primed on the
        // audio thread, in forty-percent slices of a block, which is a
        // second of drums before the band arrives.  Every other jump
        // was instant, and only this one was not, which is exactly what
        // made it look like nonsense.
        if !DESCEND_OFF_THREAD {
            // **At `ticks`, not at zero.**  This branch was written for
            // the top, where the two are the same; widening it to every
            // target left the `0` behind, so every seek re-rooted the
            // piece at its beginning and played from there — the
            // transport moved and the music started over.
            match self.piece.reopen(p, self.seed, ticks) {
                Ok(()) => {
                    self.opened_at = Some(ticks);
                    self.wanted = None;
                    self.descending = false;
                    self.failed = None;
                }
                Err(e) => self.failed = Some(e),
            }
            return;
        }
        self.wanted = Some(ticks);
        self.descending = true;
    }

    /// Note-ons performed and notes dropped since this was last called.
    pub fn take_counts(&mut self) -> (u32, u32) {
        let out = (self.played_count, self.dropped_count);
        self.played_count = 0;
        self.dropped_count = 0;
        out
    }

    /// How many note-ends are waiting for their instant — the number
    /// that says whether a silent stretch is "nothing forced" or
    /// "forced and not yet due".
    pub fn pending_len(&self) -> usize {
        self.pending.len()
    }

    /// Slide the stream's zero by `by` samples.
    ///
    /// The transport crept away from where the anchor said it would be;
    /// this puts the music back on it without re-rooting anything.  The
    /// stream is untouched — only where its ticks land in engine time
    /// moves.
    pub fn nudge_origin(&mut self, by: i64) {
        self.origin += by;
    }

    /// The host reset the processing state — put the clock back with
    /// it.
    ///
    /// **`clap_plugin.reset()` is a jump the transport does not
    /// announce.**  A host calls it when the timeline moves, and
    /// `Instance::reset` obeys by zeroing the engine and putting `t`
    /// back to zero.  This performer measures its notes against that
    /// clock — `origin + score_samples(onset)` — so an origin left over
    /// from before the reset put every note as far in the *future* as
    /// the session had been long, and they sat in the heap waiting for
    /// a clock that had gone back to the start.  The gap was exactly as
    /// long as the playing that preceded it, which is why it felt
    /// random.
    pub fn reset_clock(&mut self) {
        self.origin = 0;
        self.position = -1;
        self.pending.clear();
        self.dropped.clear();
        self.played.clear();
        self.primed.clear();
        self.priming = true;
    }

    /// Ask for a primed stream at `tick` without a transport doing it.
    ///
    /// Used at `activate`, so the very first block does not force the
    /// opening of the piece itself — the only other place a block ever
    /// went over budget in a recorded session.
    pub fn prime_at(&mut self, tick: i64) {
        self.wanted = Some(tick.max(0));
        self.descending = true;
    }

    /// The tick a seek asked for and has not been given yet.
    pub fn wanted(&self) -> Option<i64> {
        self.wanted
    }

    /// Install a stream the worker primed.
    ///
    /// Returns the piece it replaces, so the caller can hand the
    /// machine back for the next descent to reuse — a warm heap is the
    /// difference between re-rooting and re-parsing.
    /// Install a stream the worker primed, **with the notes it forced
    /// on the way**.
    ///
    /// Forcing consumes: the events the worker pulled are gone from the
    /// stream, so they have to arrive by this door or not at all.  They
    /// are admitted on the next `advance`, where the tempo and the rate
    /// are known.
    pub fn install(&mut self, tick: i64, piece: Piece, notes: Vec<Note>)
        -> Piece
    {
        let old = std::mem::replace(&mut self.piece, piece);
        self.opened_at = Some(tick);
        self.wanted = None;
        self.descending = false;
        self.priming = false;
        self.failed = None;
        self.pending.clear();
        self.dropped.clear();
        self.played.clear();
        self.position = -1;
        self.primed = notes;
        old
    }
}
