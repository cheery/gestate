# Verification — an oracle for the other half

*Written as a design; the differential oracles are built now
(`test/test_verification.py`: the identity edit, block-size
invariance, determinism, and live-quiescent = offline — all passing
on first contact).  The transcript format is not yet.  The problem
statement is `journal.md`'s, recorded the day stage 10 landed.*

The engine half of this project is verified the strong way: the LLVM
output is checked sample-for-sample against a reference interpreter,
and both are checked against committed goldens.  The journal's stage-10
entry says what that bought, in the plainest sentence in the file:

> `fixme.md` F97 records nine, all in the Python *around* the engine
> and none in the language, the fragment or code generation.  That
> half is checked sample-for-sample and turned up almost nothing;
> **this half has no oracle, and four of the nine were silent** — the
> synth played and every indicator said it worked.

The defects live where the checking is weakest.  This design gives the
Python half — assembly, host, transport, editor plumbing, migration —
the same shape of oracle the engine has: **a recorded truth, replayed
and diffed**, rather than assertions somebody thought to write.

## The session transcript

Everything the Python half does is driven across one narrow boundary:
blocks are requested, control values arrive, notes arrive, the
transport is told to play/stop/seek/loop, and a source edit triggers
assemble → extract → `migrate`.  A **session transcript** is that
boundary written down — one JSONL event per crossing, timestamped in
blocks, nothing internal:

    {"t": 0,    "ev": "publish", "source_hash": "…"}
    {"t": 128,  "ev": "control", "chan": "cutoff", "value": 0.4}
    {"t": 256,  "ev": "note_on", "key": 60, "vel": 100}
    {"t": 512,  "ev": "edit",    "source_hash": "…"}
    {"t": 1024, "ev": "seek",    "to": 0}

Two modes, one format:

* **Record**: `audiolive`/`audiohost` append events as they happen.
  A bug found by playing is *captured by having been played* — the
  transcript is the reproduction, checked in beside the fix the way a
  `.samples` golden is.
* **Replay**: `python -m gestate.replay session.jsonl` re-drives the
  same boundary with no UI, no clock and no sound card, and emits the
  things worth diffing: a hash of every rendered block, the `State`
  snapshot after every edit, and the graph shape after every
  assembly.  Committed, those are goldens for the half that had none.

Silence was the failure mode, so the replay's output is deliberately
*total*: every block hashed, not spot checks.  A transport that drops
one block on seek, a migration that zeroes one filter, a control that
lands one block late — each moves a hash, and four-of-nine silent
becomes zero-of-nine silent for anything a transcript covers.

## The differential oracles

Recorded goldens catch regressions; differential checks catch bugs on
day one, because two independent routes to the same answer already
exist and are not yet held together:

* **Live-quiescent = offline.**  A session that publishes a scored
  program, presses play, and touches nothing must render, block for
  block, what `audioperform` renders offline.  One equality, and it
  pins the transport, the scheduler and the host buffer plumbing to
  the offline path that the golden tests already trust.
* **The identity edit is the identity.**  Republishing unchanged
  source must give `migrate(g, s, g) == s` and identical blocks
  after.  This is the property four silent defects would have tripped
  — an edit that subtly moved state moved it just as much when the
  edit changed nothing.
* **Edit now = edit later.**  Migrating at block `n` and rendering
  on, versus rendering the old program to `n` and the new from its
  own start, must agree wherever no state was carried — the halves
  that *should* be indifferent to when the edit happened are checked
  for it.
* **Record of a replay = the replay.**  Running the recorder over a
  replayed session must reproduce the transcript.  The harness is in
  the loop too; this is the check on the check.

## What this is not

* Not a UI test.  The transcript starts below pygame: what the editor
  *asked for*, never what it drew.  The widget layer earns its own
  oracle in `spec/editor.md`'s terms — by being a view over spans,
  it is testable as text edits, which this file already covers via
  the `edit` event.
* Not a fuzzer, though it feeds one: transcripts compose, so a
  generator that shuffles recorded events inside their invariants is
  cheap to add once replay exists.  Replay comes first; recorded
  truth beats generated suspicion.

## Costs, stated

* Determinism debts come due.  Replay only works if the Python half
  is a function of the transcript — every wall-clock read, dict-order
  dependence and cache hit that leaks into behaviour is about to be
  found, which is the point, and is work.
* The transcript format is an interface now: versioned, with the
  same discipline `State` snapshots get in `spec/export.md`.
* Recorded sessions rot when the boundary changes shape.  Kept small
  (events, not state), they rot slowly, and the diff names the event
  kind that no longer replays — a rotted transcript is itself a
  report that the boundary moved.
