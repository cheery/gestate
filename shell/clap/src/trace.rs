//! What the host actually did — `spec/verification.md`'s session
//! transcript, at the CLAP boundary.
//!
//! Every discrepancy this project has chased between a test and a real
//! DAW came down to the same thing: **the harness did not do what the
//! host does.**  A mono buffer for a stereo plugin, a transport that
//! never stopped, a play that never started from a cursor.  Guessing at
//! the difference has cost more than writing it down would have.
//!
//! So the plugin records its own boundary: one row per `process`, with
//! what the host handed it and what it did about it.  A replay driver
//! then feeds those rows to the same code with no audio device in the
//! room, and a bug that only happens in Reaper becomes a bug that
//! happens in a test.
//!
//! **Real-time safe by construction.**  The rows are preallocated at
//! `activate` — on the main thread, where allocating is allowed — and
//! the audio thread only writes into a slot it already owns.  Nothing
//! here allocates, locks, or touches a file while audio is running; the
//! file is written at `deactivate`, which is the main thread's.
//!
//! Off unless asked for.  Set `GESTATE_TRACE` to a path and the next
//! `activate` starts recording:
//!
//! ```text
//! GESTATE_TRACE=/tmp/nightdrive.trace reaper
//! ```

/// One `process` call, as the host presented it.
#[derive(Clone, Copy, Default)]
pub struct Row {
    /// The host's own clock for this block.
    pub steady_time: i64,
    pub frames: u32,
    /// `0` when the host passed no transport at all — which is a fact
    /// worth recording, because a free-running host is a different
    /// program from a stopped one.
    pub has_transport: u8,
    pub flags: u32,
    pub tempo: f64,
    pub song_pos_beats: i64,
    /// How many events arrived, and how many were notes.
    pub events: u32,
    pub notes: u32,
    /// What the plugin made of it.
    pub engine_t: i64,
    pub descending: u8,
    pub wanted: i64,
    pub pending: u32,
    /// How long this block took, in microseconds — the number that
    /// turns "it stutters sometimes" into a row you can point at.
    pub micros: u32,
}

pub struct Trace {
    path: String,
    rows: Vec<Row>,
    /// How many rows are filled.  Recording stops when the buffer is
    /// full rather than growing it: a fixed cost is the point.
    used: usize,
}

impl Trace {
    /// Start recording if `GESTATE_TRACE` names a path.
    ///
    /// Called from `activate`, so the allocation happens where
    /// allocation is allowed.
    pub fn open(blocks: usize) -> Option<Trace> {
        let path = std::env::var("GESTATE_TRACE").ok()?;
        Some(Trace { path, rows: vec![Row::default(); blocks], used: 0 })
    }

    /// Room for about ten minutes at 512 frames and 48 kHz.
    pub const DEFAULT_BLOCKS: usize = 60_000;

    #[inline]
    pub fn push(&mut self, row: Row) {
        if self.used < self.rows.len() {
            self.rows[self.used] = row;
            self.used += 1;
        }
    }

    pub fn len(&self) -> usize {
        self.used
    }

    pub fn is_empty(&self) -> bool {
        self.used == 0
    }

    /// Write what was recorded.  **Main thread only** — this opens a
    /// file.
    pub fn write(&self) {
        use std::io::Write;
        let Ok(file) = std::fs::File::create(&self.path) else { return };
        let mut out = std::io::BufWriter::new(file);
        let _ = writeln!(out, "gestate-trace 1");
        let _ = writeln!(out, "# steady frames tr flags tempo pos events \
                              notes engine_t descending wanted pending us");
        for r in &self.rows[..self.used] {
            let _ = writeln!(
                out,
                "{} {} {} {} {} {} {} {} {} {} {} {} {}",
                r.steady_time, r.frames, r.has_transport, r.flags, r.tempo,
                r.song_pos_beats, r.events, r.notes, r.engine_t,
                r.descending, r.wanted, r.pending, r.micros);
        }
        let _ = out.flush();
    }
}
