# Verification — an oracle for the other half

*Written as a design; the differential oracles are built now
(`test/test_verification.py`: the identity edit, block-size
invariance, determinism, and live-quiescent = offline — all passing
on first contact).  The problem statement is `journal.md`'s, recorded
the day stage 10 landed.*

*Status, 2026-08-11: **the transcript is built, and not where this file
expected it.**  The design below records the *editor's* boundary in
Python.  What got written first records the **plugin's** boundary in
Rust — one row per `clap_plugin.process`, written by the instrument
while a real DAW drives it — because that is where the unanswerable
bugs were.  §"Recording a host" is the built thing; the design below it
still stands for the editor and is still unbuilt there.*

*It paid for itself the day it landed.  Three defects had survived a
long afternoon of reasoning, and all three were invisible to every test
harness in this repository because **the harness did not do what the
host does**.  A transcript found each of them within minutes of
existing: a `clap_plugin.reset()` no test had ever called, a reset that
hides its own transport jump, and a steady clock drift being mistaken
for a seek.  The lesson is the one this file was written to argue, in
sharper form than the argument: **a harness is a guess about the host,
and a guess is what the recording replaces.***

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
* **Replay**: re-drive the same boundary with no UI, no clock and no
  sound card, and emit the things worth diffing: a hash of every
  rendered block, the `State` snapshot after every edit, and the graph
  shape after every assembly.  Committed, those are goldens for the
  half that had none.

  The editor's half of this landed as **`gestate/sessionlog.py`**, and
  the shape it took is worth the correction: a session is a list of
  *commands*, so the recording is the names that went in and the
  sentences that came out, and what a replay diffs is the sentences.

      python -m gestate.sessionlog session.ges [--against file.ges]

  Cheaper than the JSONL sketched above and it needed no instrument —
  `Session.run` is one choke point and every command already answered
  in words. The block-hash oracle described here is still the right
  thing for the *engine* boundary and is still unbuilt there.

Silence was the failure mode, so the replay's output is deliberately
*total*: every block hashed, not spot checks.  A transport that drops
one block on seek, a migration that zeroes one filter, a control that
lands one block late — each moves a hash, and four-of-nine silent
becomes zero-of-nine silent for anything a transcript covers.

## Recording a host — built

The plugin records its own boundary.  Every discrepancy chased between
a test and a DAW came down to the harness guessing wrong about the
host: a mono buffer handed to a stereo plugin, a transport that never
stopped, a play that never started from a cursor, a `reset()` nobody
called.  Guessing cost more than writing it down.

**One row per `process`** (`shell/clap/src/trace.rs`): what the host
handed the plugin — block size, transport flags, tempo,
`song_pos_beats`, event counts — and what the plugin made of it —
engine time, whether it was waiting for a descent, the seek target it
wanted, notes pending, notes performed and dropped, and the
microseconds the block took.

**Real-time safe by construction.**  Rows are preallocated at
`activate`, on the main thread where allocating is allowed; the audio
thread only fills a slot it already owns; the file is written at
`deactivate`.  Nothing allocates, locks or touches disk while audio
runs.  Off entirely unless `GESTATE_TRACE` names a path.

### Doing it

Record — set the variable for the host process, provoke the fault,
then quit or remove the plugin (the file is written on deactivate):

    GESTATE_TRACE=/tmp/nd.trace reaper

Replay — the third argument is the host's sample rate, and **it must
be the rate the recording was made at**, or the replayed transport
drifts against the plugin's own clock and invents a fault that was not
there:

    python test/replay_trace.py /tmp/nd.trace ~/.clap/nightdrive.clap 48000

Replaying with tracing on records the replay, which is how a trace
taken on the old build is compared against the new one:

    GESTATE_TRACE=/tmp/re.trace python test/replay_trace.py /tmp/nd.trace …

### Reading it

The replayer prints what the host did — block sizes, transport edges,
position jumps, host resets — then the cost in both places, then every
silent stretch over 150 ms with what the plugin was doing through it.
That last line is the diagnostic, and its columns separate faults that
sound identical:

| what the gap shows | what it is |
|---|---|
| `descending` covers most of it | waiting for a stream: the worker, or `PRIME_BEATS` |
| `dropped` climbing | the rejoin rule discarding notes whose instant passed |
| `pending` high, `played` zero, `descending` zero | notes admitted and never due — a clock or frontier fault |
| all three zero | nothing was forced at all — the machine, or the program |

And the two cost columns answer the question a single machine cannot:
**slow in the host and fast on replay is scheduling; slow in both is
the code.**

### Two rules learned the hard way

* **Ask the plugin how many channels it wants.**  A stereo program
  handed a one-channel buffer writes its second channel into nothing,
  and every measurement taken through it is noise that looks like data.
  `channels_of` reads `clap.audio-ports`; nothing should assume.
* **Never measure a mix by its peak.**  A brickwall pins the peak at
  its limit, so a single click and a full arrangement read the same.
  RMS, or a difference against the same render with the part switched
  off.

A companion trick worth keeping: **a variant with the always-on parts
removed.**  `nightdrive`'s drums are signals, so they play whether or
not the score does, and "only the drums" is indistinguishable from
"everything" by level alone.  A copy with kick, snare and hats deleted
makes any silence unambiguously the score's.

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

## The screen is an oracle, and it is the one this tree lacked

*2026-08-17.  Four real defects landed that day.  **Three were invisible
to 2,540 passing tests and every one of them was found by photographing
a running window.***

`manifesto.md` §"The instruments, and what each cannot see" gives
`tools/lagcheck.py` the blind spot *"correctness of what is drawn"*.
That column was accurate and it was the whole problem: the tree could
drive a real window and read whether a pixel *changed*, and had nothing
that could read whether the pixels were **right**.

The three:

- **`you 0m` on a day the record said was eight hours old.**  The status
  row took its figure from the day the first *gesture* made, so a
  workbench opened onto a day already underway reported that nothing had
  happened on the very day its own file said the most had.  Every unit
  test passed, because every unit test typed first.  A test cannot reach
  for a state it never thought to be in; a window opened at two in the
  afternoon is in it by default.
- **A rest day drawn as `·`, one pixel a side from `▪`.**  The string was
  correct and every assertion about it passed.  On the screen, at the
  size it is actually read at, *a day of rest looked exactly like a light
  day of work* — the one mark the instrument existed to show was the one
  that could not be read.  No assertion about a string can catch this,
  because the defect is not in the string.
- **A comprehension body swallowing its own union.**  `for (C) {a} \/ {b}`
  puts the `\/` *inside* the loop, so the answer was right whenever the
  generator was non-empty and empty when it was not.  It typechecked, it
  ran, and it was looked at in a real window and looked fine — because
  the picture it produced was the correct one for the data it had.

### The harness, which is small

A virtual display, the program, and a photograph:

```sh
Xvfb :77 -screen 0 1200x800x24 &
DISPLAY=:77 python -m gestate.workbench <file> &
import -window <id> shot.png          # ImageMagick
```

`tools/lagcheck.py` already owns the difficult half — `find_window`,
`click_into`, `shot`, and XTEST typing — so the whole of a new visual
check is those four calls and a crop.  **It costs about fifteen lines
and it out-found the suite on the day it was written.**

### Two rules it comes with

**A verification run must mute itself.**  The first one opened
`twoknobs.ges` in a real workbench, which takes the real sound card, and
played into a room somebody was resting in.  A throwaway `$HOME` holding
an `.asoundrc` that maps `pcm.!default` to ALSA's null device fixes it —
and note that the same throwaway `$HOME` hides `~/.rustup`, so the
editor's own `_stale` rebuild then fails with *"rustup could not choose
a version of cargo"*; symlink `.rustup` and `.cargo` into it.

**And it must keep no record of the day.**  XTEST types with the same X
events a hand does and nothing can tell them apart, so
`tools/lagcheck.py::driven` sets `GESTATE_PRESENCE=` for every harness
that opens a window — otherwise the one instrument that measures the
person would be measuring the test suite.

### The pattern that forced the fourth one out

The fourth defect was not found by looking; it was found because the
suite **refused to let the example exist unexamined**.
`test_audio.py::test_every_audio_example_is_exercised_here` and
`test_gui.py::test_every_gui_example_is_exercised_here` each assert that
their example directory is *exactly* a listed set.  Adding a file makes
the suite fail until somebody writes the test for it — and writing that
test is what surfaced the comprehension bug, because the assertion worth
writing was not *"the picture is four lit and one dark"* (which the bug
satisfied) but *"pull a cable and the lamps follow"* (which it did not).

**A directory that is a contract should say so with a roster.**  Two of
these exist.  The pattern generalises to anywhere the tree's shape is
part of its meaning, and its value is not the assertion — it is that it
makes a person write the test they were about to skip.

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
  same discipline `State` snapshots get in `spec/export.md`.  The
  plugin's own format carries its version in the first line
  (`gestate-trace 1`) and the replayer accepts a short row from before
  a column existed, reporting zero for what it could not know — a
  recording of a fault should outlive the build that made it.
* Recorded sessions rot when the boundary changes shape.  Kept small
  (events, not state), they rot slowly, and the diff names the event
  kind that no longer replays — a rotted transcript is itself a
  report that the boundary moved.
