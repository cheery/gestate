//! The score cursor — `spec/dynamicscore.md` stage one, the Rust half.
//!
//! `audiodynamic.Performer` is the reference, and this file is its
//! retelling with the clock in the transport's hands: a cursor over the
//! beat-ordered event list, performing each event as `song_pos_beats`
//! reaches it, through the same voice allocation the MIDI path already
//! mirrors from `audioalloc`.  The semantics were pinned in Python
//! first (`test/test_dynamicscore.py`) and nothing here may disagree
//! with them: releases sort before onsets at one instant (the export
//! wrote the list in that order and the cursor preserves it), `advance`
//! only moves forward so a beat asked about twice delivers nothing
//! twice, and a seek is `all_off`, fresh voices, then a silent replay
//! of everything before the target — the replay winning where the two
//! collide, entries at exactly the target belonging to the next
//! `advance` so a seek onto a downbeat plays the downbeat.
//!
//! Two clocks meet here and the words keep them apart.  **Score
//! samples** count from the piece's top at the current tempo — the
//! domain `timed_events` and the bake share.  **Engine samples** are
//! `Instance.t`, what the graph's `ticks` reads.  `origin` is the
//! engine sample score sample 0 falls at: 0 when play started at the
//! top, *negative* after a seek into the piece — which is how a note
//! held across the seek target resumes mid-envelope, its `gateAt`
//! naming an instant before the engine began.  (One stated slop: a
//! note whose onset maps to engine sample −1 stamps a `gateAt` of 0,
//! which reads as "never played" — a seek exactly one sample past an
//! onset loses that one note's tail.  The bake cannot express the
//! situation at all, so parity is unaffected.)

use super::engine::{Bank, Control, ScoreEvent};

/// What a voice is playing: a keyboard's `(channel, key)` or a score
/// event's own index — `timed_events`' rule, "a `Score` may hold the
/// same payload twice and each is its own note, where MIDI's key
/// doubles as an identity because a keyboard cannot press one key
/// twice".
#[derive(Clone, Copy, PartialEq, Eq, Debug)]
pub enum NoteKey {
    Midi(i16, i16),
    Score(u32),
}

/// `audioalloc.Voice`, in Rust — the semantics are that module's,
/// mirrored deliberately, and shared by the keyboard and the cursor
/// because the *bank* is shared: a scored bank a keyboard also plays
/// is one set of voices with two writers.
#[derive(Clone, Copy)]
pub struct VoiceState {
    pub key: Option<NoteKey>,
    pub started: i64,
    pub released: Option<i64>,
}

pub const FRESH_VOICE: VoiceState =
    VoiceState { key: None, started: -1, released: None };

/// `Allocator._pick`: a free voice released-longest-ago first — a
/// never-played voice counts as released at the beginning of time —
/// else steal the one sounding longest.
pub fn pick_voice(voices: &[VoiceState]) -> usize {
    voices.iter().enumerate()
        .filter(|(_, v)| v.key.is_none())
        .min_by_key(|(i, v)| (v.released.unwrap_or(i64::MIN), *i))
        .map(|(i, _)| i)
        .unwrap_or_else(|| {
            voices.iter().enumerate()
                .min_by_key(|(i, v)| (v.started, *i))
                .map(|(i, _)| i).unwrap()
        })
}

/// `Allocator.note_off`: the *oldest* voice on this key, so repeated
/// notes at one pitch release in the order they were struck.  `None`
/// for a key nothing is playing — a stolen note's release — which is
/// ordinary and silently nothing.
pub fn release_voice(voices: &mut [VoiceState], key: NoteKey, at: i64)
                     -> Option<usize> {
    let held = voices.iter().enumerate()
        .filter(|(_, v)| v.key == Some(key) && v.released.is_none())
        .min_by_key(|(i, v)| (v.started, *i))
        .map(|(i, _)| i)?;
    voices[held].released = Some(at);
    voices[held].key = None;
    Some(held)
}

/// `tempo.samples_of`, both branches: the exact integer path when the
/// tempo is a whole bpm — `tick * 60 * rate // (bpm * TPB)`, in i128
/// so nothing wraps — because that is what every committed schedule
/// was built with, and a one-sample disagreement between this cursor
/// and the bake is a parity failure.  A fractional tempo floors a
/// float, which is the branch Python's envelope path takes too.
pub fn score_samples(tick: i64, tempo: f64, rate: u32, tpb: i64) -> i64 {
    if tempo > 0.0 && tempo.fract() == 0.0 {
        let den = tempo as i128 * tpb as i128;
        (tick as i128 * 60 * rate as i128).div_euclid(den) as i64
    } else if tempo > 0.0 {
        ((tick as f64 / tpb as f64) * 60.0 / tempo * rate as f64)
            .floor() as i64
    } else {
        0
    }
}

/// The transport's own position as score samples — `song_pos_beats`
/// is CLAP fixed point, beats × 2³¹, kept integral through the same
/// division as `score_samples`.
pub fn beats_q31_samples(q31: i64, tempo: f64, rate: u32) -> i64 {
    if tempo > 0.0 && tempo.fract() == 0.0 {
        let den = (tempo as i128) << 31;
        (q31 as i128 * 60 * rate as i128).div_euclid(den) as i64
    } else if tempo > 0.0 {
        (q31 as f64 / (1i64 << 31) as f64 * 60.0 / tempo * rate as f64)
            .floor() as i64
    } else {
        0
    }
}

/// What the cursor reads, gathered so a call site names it once.
pub struct Tables<'a> {
    pub events: &'a [ScoreEvent],
    pub banks: &'a [Bank],
    pub controls: &'a [Control],
    /// Per bank, whether the **score** is allowed to play it.
    ///
    /// A bank is a set of voices, and two things can want them: the
    /// piece and the player's hands.  This is the piece's half of that
    /// switch — the routing matrix is the hands' half — so a player can
    /// take a bank over from the score, hand it back, or have both at
    /// once, without the plugin having to guess which they meant.
    pub plays: &'a [bool],
    pub tpb: i64,
    pub rate: u32,
}

impl Tables<'_> {
    /// Which banks the score writes — a seek resets and replays *these*
    /// and leaves a purely-keyboard bank alone, so a held key survives
    /// a loop seam on any bank the piece does not own.
    fn scored(&self) -> Vec<bool> {
        let mut out = vec![false; self.banks.len()];
        for ev in self.events {
            out[ev.bank] = true;
        }
        out
    }
}

/// `audiodynamic.Performer`: the cursor and its anchor.
pub struct Performer {
    /// The first event not yet performed.
    pub pos: usize,
    /// The engine sample score sample 0 falls at.
    pub origin: i64,
}

impl Performer {
    pub fn new() -> Self {
        Performer { pos: 0, origin: 0 }
    }

    pub fn reset(&mut self) {
        self.pos = 0;
        self.origin = 0;
    }

    /// One event through the shared allocation, stamped at engine
    /// sample `at`.  `touched` is the seek replay's memory of which
    /// slots it wrote — the replay wins over a release exactly there.
    fn perform(&self, tb: &Tables, ev: &ScoreEvent, at: i64,
               voices: &mut [Vec<VoiceState>], control: &mut [i64],
               mut touched: Option<&mut [bool]>) {
        // Switched off: the cursor still *moves* past this event — the
        // piece keeps its place, so switching the score back on rejoins
        // where the music is rather than where it was left.
        if !tb.plays.get(ev.bank).copied().unwrap_or(true) {
            return;
        }
        let bank = &tb.banks[ev.bank];
        let mut write = |slot: usize, value: i64, control: &mut [i64]| {
            control[slot] = value;
            if let Some(t) = touched.as_deref_mut() {
                t[slot] = true;
            }
        };
        if ev.is_off {
            if let Some(i) = release_voice(&mut voices[ev.bank],
                                           NoteKey::Score(ev.key), at) {
                write(bank.voices[i][1], at + 1, control);
            }
        } else {
            let i = pick_voice(&voices[ev.bank]);
            voices[ev.bank][i] = VoiceState {
                key: Some(NoteKey::Score(ev.key)),
                started: at,
                released: None,
            };
            let chans = bank.voices[i];
            write(chans[0], at + 1, control);
            write(chans[1], 0, control);
            for (slot, value) in chans[2..].iter().zip(ev.payload) {
                write(*slot, *value, control);
            }
        }
    }

    /// Perform everything whose instant lands before score sample
    /// `end` — one block's worth when called as
    /// `advance(t - origin + frames)`.  The cursor only moves forward,
    /// which is `advance`'s idempotency: a block asked about twice
    /// delivers nothing twice.
    pub fn advance(&mut self, tb: &Tables, tempo: f64,
                   voices: &mut [Vec<VoiceState>], control: &mut [i64],
                   end: i64) {
        while self.pos < tb.events.len() {
            let ev = &tb.events[self.pos];
            let at = score_samples(ev.tick, tempo, tb.rate, tb.tpb);
            if at >= end {
                break;
            }
            self.perform(tb, ev, self.origin + at, voices, control, None);
            self.pos += 1;
        }
    }

    /// `Performer.seek`, the spec's three moves in the spec's order:
    /// release what sounds (stamped at engine `now` — the audible
    /// part); fresh voices and every scored bank's channels back to
    /// "never played"; then a silent replay of every event before
    /// score sample `target`, the replay winning where the two collide.
    /// A pre-seek tail whose voice the replay re-occupies is cut, not
    /// rung out — the deliberate reading Python documents.
    ///
    /// Only *scored* banks are touched: a keyboard-only bank keeps its
    /// held notes through a loop seam, because the piece never wrote
    /// there and `value_at` parity says nothing about it.
    pub fn seek(&mut self, tb: &Tables, tempo: f64, target: i64, now: i64,
                voices: &mut [Vec<VoiceState>], control: &mut [i64]) {
        let scored = tb.scored();
        let mut off: Vec<usize> = Vec::new();
        for (b, bank) in tb.banks.iter().enumerate() {
            if !scored[b] {
                continue;
            }
            for (i, v) in voices[b].iter().enumerate() {
                if v.key.is_some() {
                    off.push(bank.voices[i][1]);
                }
            }
            for v in voices[b].iter_mut() {
                *v = FRESH_VOICE;
            }
            for chans in bank.voices.iter() {
                for slot in chans.iter() {
                    control[*slot] = tb.controls[*slot].init_bits;
                }
            }
        }
        let mut touched = vec![false; control.len()];
        self.origin = now - target;
        self.pos = 0;
        while self.pos < tb.events.len() {
            let ev = &tb.events[self.pos];
            let at = score_samples(ev.tick, tempo, tb.rate, tb.tpb);
            if at >= target {
                break;
            }
            self.perform(tb, ev, self.origin + at, voices, control,
                         Some(&mut touched));
            self.pos += 1;
        }
        for slot in off {
            if !touched[slot] {
                control[slot] = now + 1;
            }
        }
    }
}

#[cfg(test)]
mod tests {
    //! `test_dynamicscore.py`'s scenarios, at the change level: the
    //! Python suite pinned the semantics against the bake; these hold
    //! the Rust retelling to the same sentences with a hand-written
    //! list small enough to check by eye.
    //!
    //! The fixture: a two-voice bank, one payload field per voice,
    //! 96 ticks a beat, 1000 samples a second at 60 bpm — so one beat
    //! is exactly 1000 samples and the arithmetic is legible.  A
    //! legato pair shares its seam (the release sorts first, freeing
    //! the voice the next onset takes), and a third note overlaps so
    //! seeks land inside something sounding.

    use super::*;
    use crate::engine::Kind;

    static V0: [usize; 3] = [0, 1, 2];
    static V1: [usize; 3] = [3, 4, 5];
    static VOICES: [&[usize]; 2] = [&V0, &V1];
    static BANKS: [Bank; 1] =
        [Bank { name: "lead", voices: &VOICES, table: None }];
    const C: Control = Control { chan: "c", kind: Kind::Int, init_bits: 0,
                                 knob: false, min: 0.0, max: 0.0 };
    static CONTROLS: [Control; 6] = [C; 6];

    static P60: [i64; 1] = [60];
    static P64: [i64; 1] = [64];
    static P67: [i64; 1] = [67];
    /// Beat 0: key 60 (one beat) with key 67 under it (three beats).
    /// Beat 1: key 64 (one beat), legato after key 60 — its onset
    /// shares tick 96 with the release, which sorts first.
    static EVENTS: [ScoreEvent; 6] = [
        ScoreEvent { tick: 0, key: 0, bank: 0, is_off: false,
                     payload: &P60 },
        ScoreEvent { tick: 0, key: 2, bank: 0, is_off: false,
                     payload: &P67 },
        ScoreEvent { tick: 96, key: 0, bank: 0, is_off: true,
                     payload: &[] },
        ScoreEvent { tick: 96, key: 1, bank: 0, is_off: false,
                     payload: &P64 },
        ScoreEvent { tick: 192, key: 1, bank: 0, is_off: true,
                     payload: &[] },
        ScoreEvent { tick: 288, key: 2, bank: 0, is_off: true,
                     payload: &[] },
    ];

    const TEMPO: f64 = 60.0;
    const RATE: u32 = 1000;

    fn tables() -> Tables<'static> {
        Tables { events: &EVENTS, banks: &BANKS, plays: &[true; 8], controls: &CONTROLS,
                 tpb: 96, rate: RATE }
    }

    fn fresh() -> (Vec<Vec<VoiceState>>, Vec<i64>) {
        (vec![vec![FRESH_VOICE; 2]], vec![0i64; 6])
    }

    fn run_to(end: i64, step: i64) -> (Performer, Vec<Vec<VoiceState>>,
                                       Vec<i64>) {
        let tb = tables();
        let (mut voices, mut control) = fresh();
        let mut p = Performer::new();
        let mut t = 0;
        while t < end {
            let stop = (t + step).min(end);
            p.advance(&tb, TEMPO, &mut voices, &mut control, stop);
            t = stop;
        }
        (p, voices, control)
    }

    #[test]
    fn one_giant_advance_is_every_small_one() {
        let (_, _, blocks) = run_to(4000, 64);
        let (_, _, once) = run_to(4000, 4000);
        assert_eq!(blocks, once);
    }

    #[test]
    fn advance_is_idempotent() {
        let tb = tables();
        let (mut voices, mut control) = fresh();
        let mut p = Performer::new();
        p.advance(&tb, TEMPO, &mut voices, &mut control, 1500);
        let snap = control.clone();
        let pos = p.pos;
        p.advance(&tb, TEMPO, &mut voices, &mut control, 1500);
        assert_eq!(control, snap);
        assert_eq!(p.pos, pos);
    }

    #[test]
    fn the_legato_note_reuses_the_freed_voice() {
        // Both voices busy at beat 0; the seam at beat 1 releases key
        // 60 *first*, so key 64 lands on the freed voice rather than
        // stealing the held key 67 — releases-first is what a legato
        // line of one voice needs.
        let (_, voices, control) = run_to(1500, 64);
        // v1 holds key 67 untouched throughout.
        assert_eq!(control[5], 67);
        assert_eq!(control[3], 1);           // gate from beat 0
        assert_eq!(control[4], 0);           // never released
        // v0: key 64 took it at beat 1, gate restamped, off cleared.
        assert_eq!(control[0], 1001);
        assert_eq!(control[1], 0);
        assert_eq!(control[2], 64);
        assert!(voices[0][0].key == Some(NoteKey::Score(1)));
    }

    #[test]
    fn seek_into_a_held_note_resumes_it() {
        // Cold seek to 1500 — inside key 67's three-beat hold and key
        // 64's second beat.  The replay stands exactly where playing
        // from the top stood.
        let tb = tables();
        let (mut voices, mut control) = fresh();
        let mut p = Performer::new();
        p.seek(&tb, TEMPO, 1500, 0, &mut voices, &mut control);
        let (_, _, played) = run_to(1500, 64);
        // Every bank slot equal, except origin shifts stamps by
        // now - target = -1500: the note *began before the engine
        // did*, which is what resumes it mid-envelope.
        assert_eq!(p.origin, -1500);
        assert_eq!(control[3], 1 - 1500);
        assert_eq!(control[4], 0);
        assert_eq!(control[5], 67);
        assert_eq!(control[2], played[2]);
        // And the next advance carries on identically, rebased.
        p.advance(&tb, TEMPO, &mut voices, &mut control, 1500 + 600);
        let (_, _, on) = run_to(2100, 64);
        assert_eq!(control[1], on[1] - 1500);
    }

    #[test]
    fn a_seek_onto_a_downbeat_plays_the_downbeat() {
        // Entries at exactly the target belong to the next advance:
        // seek to beat 1 leaves the seam unplayed, and the first
        // advance performs release-then-onset in order.
        let tb = tables();
        let (mut voices, mut control) = fresh();
        let mut p = Performer::new();
        p.seek(&tb, TEMPO, 1000, 0, &mut voices, &mut control);
        assert_eq!(p.pos, 2, "the seam's release is still to come");
        assert_eq!(control[2], 60, "key 60 still holds v0");
        p.advance(&tb, TEMPO, &mut voices, &mut control, 1064);
        assert_eq!(control[2], 64, "the downbeat sounded");
    }

    #[test]
    fn a_hot_backward_seek_releases_into_silence() {
        // Play into the piece, then seek to the top: nothing has
        // history there, so gates read "never played" and what sounded
        // is released at the seek instant.
        let tb = tables();
        let (mut p, mut voices, mut control) = run_to(1500, 64);
        p.seek(&tb, TEMPO, 0, 1500, &mut voices, &mut control);
        assert_eq!(control[0], 0, "gate reads never-played");
        assert_eq!(control[3], 0);
        assert_eq!(control[1], 1501, "released at the seek instant");
        assert_eq!(control[4], 1501);
        assert_eq!(p.origin, 1500);
        assert!(voices[0].iter().all(|v| v.key.is_none()));
    }

    #[test]
    fn the_replay_wins_over_a_release() {
        // Hot seek from beat 1.5 to beat 2.5: key 67 sounds on both
        // sides, and the replay re-occupies its voice — so its off
        // channel reads the replay's 0, not a release, and the note
        // resumes rather than rings out cut.
        let tb = tables();
        let (mut p, mut voices, mut control) = run_to(1500, 64);
        p.seek(&tb, TEMPO, 2500, 1500, &mut voices, &mut control);
        assert_eq!(control[4], 0, "the replay's held note won");
        assert_eq!(control[5], 67);
        // Key 64 ended at beat 2, so v0 is silent at 2.5: its release
        // came from the *replay* (score sample 2000 → engine 1000).
        assert_eq!(control[1], 2000 - 1000 + 1);
        assert_eq!(voices[0][1].key, Some(NoteKey::Score(2)));
    }

    #[test]
    fn a_loop_replays_the_same_changes() {
        // Two beats, seek to the top, two beats again: the second pass
        // is the first, shifted by the loop length — `gateAt` names
        // score positions rebased through `origin`, not wall time.
        let tb = tables();
        let (mut p, mut voices, mut control) = run_to(2000, 64);
        let first = control.clone();
        p.seek(&tb, TEMPO, 0, 2000, &mut voices, &mut control);
        // The same drive as the first pass, clamped at the loop end —
        // both passes cover score samples [0, 2000) exactly.
        let mut t = 2000i64;
        while t < 4000 {
            let stop = (t + 64).min(4000);
            p.advance(&tb, TEMPO, &mut voices, &mut control,
                      stop - p.origin);
            t = stop;
        }
        for slot in [0usize, 1, 3, 4] {
            let shifted = if first[slot] == 0 { 0 }
                          else { first[slot] + 2000 };
            assert_eq!(control[slot], shifted, "slot {slot}");
        }
        assert_eq!(control[2], first[2]);
        assert_eq!(control[5], first[5]);
    }

    #[test]
    fn the_integer_path_is_pythons_integer_path() {
        // `tick * 60 * rate // (bpm * 96)` spot-checked against values
        // computed with Python's own `//` — including one that a naive
        // f64 division rounds differently.
        assert_eq!(score_samples(96, 120.0, 44100, 96), 22050);
        assert_eq!(score_samples(33, 120.0, 44100, 96), 7579);
        assert_eq!(score_samples(1, 97.0, 44100, 96), 284);
        assert_eq!(beats_q31_samples(8 << 31, 90.0, 48000), 256000);
    }
}
