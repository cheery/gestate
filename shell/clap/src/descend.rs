//! Descending off the audio thread.
//!
//! Re-rooting a forced score is cheap; **walking to the target tick is
//! not**.  `resumeAt` descends by declared widths, which is far better
//! than forcing every bar — but it still costs more the deeper into the
//! piece it goes, and the collector that the walk's allocation triggers
//! is a semispace copy that cannot be interrupted once begun.  Measured
//! on `nightdrive`: 3 ms at the top, 18 ms eighteen seconds in, against
//! an 11.6 ms block.
//!
//! No budget fixes that, because the two costs are different in kind: a
//! step budget can slice the walk and cannot slice the copy.  So the
//! work moves to a thread where a twenty-millisecond pause is nobody's
//! problem, and the audio thread does what it is for.
//!
//! **What plays in the gap is the honest part.**  The score is silent
//! from the moment of the seek until the new stream is primed — the
//! signal half of an instrument keeps going, so a piece with drums in
//! its `sound` still has drums.  A late entry is a musical fault; an
//! overrun is a dropout in someone else's host, and this trades the
//! second for the first.
//!
//! **Two pieces, ping-ponged.**  The worker keeps a *warm* machine: the
//! one the audio thread just finished with comes back as scratch, so a
//! descent re-roots a heap whose globals are already forced rather than
//! parsing the program again.  Only the very first descent pays for a
//! cold one.

use std::sync::atomic::{AtomicBool, Ordering};
use std::sync::{Arc, Condvar, Mutex};
use std::thread::JoinHandle;

use crate::dynscore::Piece;
use crate::engine::Program;

/// How far ahead the worker forces before handing a stream over, in
/// beats.  Enough that the first blocks after a seek have notes without
/// asking the audio thread to find them.
const PRIME_BEATS: i64 = 12;

/// A descent that has been asked for and not yet collected.
struct Shared {
    /// The tick the audio thread wants, and a serial so a later request
    /// supersedes an earlier one rather than queueing behind it — a
    /// rewinding transport asks many times and only the last matters.
    want: Mutex<Option<(u64, i64, i64)>>,
    /// `(serial, tick, piece)` — primed and waiting to be taken.
    ready: Mutex<Option<(u64, i64, Piece)>>,
    /// Machines the audio thread has finished with.
    ///
    /// **A queue, not a slot, because dropping one here would be the
    /// bug this file exists to avoid.**  A `Piece` owns a whole
    /// G-machine heap — millions of nodes, each `Con` holding its own
    /// vector — so freeing one is tens of milliseconds of `free`.  The
    /// audio thread must never do it: every piece it finishes with goes
    /// back to the worker, and the worker (or the drop of the whole
    /// `Descender`, on the main thread) is what releases them.
    scratch: Mutex<Vec<Piece>>,
    wake: Condvar,
    stop: AtomicBool,
}

pub struct Descender {
    shared: Arc<Shared>,
    thread: Option<JoinHandle<()>>,
    /// The serial of the request in flight, if any.
    pending: Option<u64>,
    next: u64,
    /// Pieces waiting to be handed back, when the worker held the lock.
    ///
    /// They sit here rather than being dropped, and go over on a later
    /// block.  The vector itself is only dropped with the plugin, on
    /// the main thread, which is where freeing a heap belongs.
    holding: Vec<Piece>,
}

impl Descender {
    /// Start the worker.  `program` is `&'static`, so the thread needs
    /// no lifetime of its own.
    pub fn new(program: &'static Program) -> Descender {
        let shared = Arc::new(Shared {
            want: Mutex::new(None),
            ready: Mutex::new(None),
            scratch: Mutex::new(Vec::new()),
            wake: Condvar::new(),
            stop: AtomicBool::new(false),
        });
        let mine = shared.clone();
        let thread = std::thread::Builder::new()
            .name("gestate-descend".into())
            .spawn(move || worker(program, mine))
            .ok();
        Descender { shared, thread, pending: None, next: 1,
                    holding: Vec::new() }
    }

    /// Ask for the piece rooted at `tick`.  Never blocks.
    ///
    /// A request that cannot be posted because the worker holds the
    /// lock is simply skipped: the transport will ask again next block,
    /// and asking twice for the same place is free.
    pub fn request(&mut self, tick: i64, tpb: i64) -> bool {
        let serial = self.next;
        if let Ok(mut w) = self.shared.want.try_lock() {
            *w = Some((serial, tick, tpb));
            self.next += 1;
            self.pending = Some(serial);
            self.shared.wake.notify_one();
            true
        } else {
            false
        }
    }

    pub fn awaiting(&self) -> bool {
        self.pending.is_some()
    }

    /// Take a primed piece if one is ready **for the request in
    /// flight**.  Never blocks.
    ///
    /// An answer to a superseded request is dropped: during a rewind
    /// the transport asks for a dozen places and only the last one is
    /// where the playhead ended up.
    pub fn take(&mut self) -> Option<(i64, Piece)> {
        let want = self.pending?;
        let mut ready = self.shared.ready.try_lock().ok()?;
        let (serial, tick, piece) = ready.take()?;
        if serial != want {
            // Stale: give the machine back rather than dropping it,
            // so the next descent is still warm.
            drop(ready);
            self.give_back(piece);
            return None;
        }
        self.pending = None;
        Some((tick, piece))
    }

    /// Hand a machine back for the next descent to reuse.
    ///
    /// Never drops and never blocks: if the worker holds the lock the
    /// piece waits here and goes over later.
    pub fn give_back(&mut self, piece: Piece) {
        self.holding.push(piece);
        self.flush_holding();
    }

    /// Push anything waiting over to the worker, if the lock is free.
    pub fn flush_holding(&mut self) {
        if self.holding.is_empty() {
            return;
        }
        if let Ok(mut s) = self.shared.scratch.try_lock() {
            s.append(&mut self.holding);
        }
    }

    /// Give the worker a warm machine before it is asked for one, so
    /// even the first seek re-roots rather than parses.
    pub fn prewarm(&mut self, piece: Piece) {
        self.give_back(piece);
    }
}

impl Drop for Descender {
    fn drop(&mut self) {
        self.shared.stop.store(true, Ordering::Release);
        self.shared.wake.notify_all();
        if let Some(t) = self.thread.take() {
            let _ = t.join();
        }
    }
}

fn worker(program: &'static Program, shared: Arc<Shared>) {
    // The worker's own machine, kept warm across descents.
    let mut mine: Option<Piece> = None;
    loop {
        // Wait for something to do.
        let request = {
            let mut want = match shared.want.lock() {
                Ok(w) => w,
                Err(_) => return,
            };
            loop {
                if shared.stop.load(Ordering::Acquire) {
                    return;
                }
                if let Some(r) = want.take() {
                    break r;
                }
                want = match shared.wake.wait(want) {
                    Ok(w) => w,
                    Err(_) => return,
                };
            }
        };
        let (serial, tick, tpb) = request;

        // Take back whatever the audio thread finished with; failing
        // that, build one.  Only the first descent of a session pays
        // for a cold machine.
        if mine.is_none() {
            if let Ok(mut s) = shared.scratch.lock() {
                mine = s.pop();
            }
        }
        // Anything else handed back is freed here, on this thread.
        if let Ok(mut s) = shared.scratch.lock() {
            s.clear();
        }
        let mut piece = match mine.take() {
            Some(p) => p,
            None => match Piece::open(program, tick) {
                Ok(p) => p,
                Err(_) => continue,
            },
        };

        // Re-root and force ahead.  **Off the audio thread, so this may
        // take as long as it takes** — including a collection, which is
        // the cost no budget could slice.
        if piece.reopen(program, tick).is_err() {
            mine = Some(piece);
            continue;
        }
        let horizon = PRIME_BEATS * tpb;
        for _ in 0..4096 {
            piece.pull(program, horizon, 8_000_000, 4096);
            if piece.failed.is_some() || !piece.stalled()
                || piece.asking().is_some() || piece.done() {
                break;
            }
            // A later request has arrived: this one is already stale,
            // so stop forcing it and go round.
            if shared.want.try_lock().map(|w| w.is_some()).unwrap_or(false) {
                break;
            }
        }

        // **Settle every bill here.**  The spike this file exists to
        // remove turned out to be one block — the handover — where the
        // audio thread's first pull on the new stream paid for both the
        // heap the walk had built and whatever forcing was left.  So
        // the worker leaves the stream *compacted* (which also sets the
        // collector's watermark, so the next pull does not immediately
        // collect again) and forced well past the horizon the audio
        // thread will ask for.
        piece.compact();

        if let Ok(mut ready) = shared.ready.lock() {
            // Anything already sitting there was never collected; keep
            // its machine rather than dropping it.
            if let Some((_, _, old)) = ready.take() {
                mine = Some(old);
            }
            *ready = Some((serial, tick, piece));
        }
    }
}
