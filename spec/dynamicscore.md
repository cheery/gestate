# The dynamic score — a performance that executes as it plays

*Written as a design; none of it is built.  Companion to
`spec/export.md` (whose transport made it thinkable) and
`spec/verification.md` (whose oracles will keep it honest).*

Today a `Score` is scheduled entirely at compile time: the layout
becomes events, the events become a `Schedule` of channel changes at
*sample indices*, and the performance is over — as a decision — before
the first sample renders.  That bought everything stage 10 promised:
`[: Void :]` proving every note assigned, a mis-routed note as a type
error, an offline render the goldens can hold.

But the codebase has been quietly stating the counter-thesis all
along, in `audioalloc`'s own docstring:

> **A note is the same thing either way; only *when it is decided*
> differs.**

The allocator emits changes, not sound; it already serves a Schedule
and a live keyboard with one body of code.  The schedule's events
live in *beats* before `samples_of` bakes them to samples.  And
`beat` is now the renderer's own, supplied by a DAW's transport as
readily as by a `bpm`.  Put those three facts in one room and the
static bake starts to look like what it is: an **optimization applied
too early to be escaped**.  This design escapes it, in three stages
that are separately shippable and separately honest.

## Stage one: static layout, dynamic execution

Keep the layout exactly as it is — combinators, types, `voices.bank`
assignment, the whole compile-time story — but stop baking it to
sample indices.  The performance becomes a **performer**: a cursor
over the beat-ordered event list, advanced by the running `beat`
clock, calling the allocator as each event's beat arrives, off the
audio thread the way `FromMidi` already runs.

What this buys, per context:

* **The DAW plays the piece.**  An exported plugin's score is today
  the one honest discard; with events in beats in the descriptor and
  the performer in the shell (it is a cursor and a comparison — Rust
  it holds gladly), *press play and the piece performs itself locked
  to the session's bars*.  Seek to bar 33 and it plays from bar 33.
  Loop eight bars and it loops.  Drag the tempo mid-phrase and the
  phrase bends, because its positions were never in seconds.
* **The editor's tempo is live.**  Change `bpm` while it sounds and
  today the schedule rebakes; a performer just keeps walking beats
  that now arrive at a different pace.
* **Nothing changes offline.**  A performer at a constant tempo must
  emit precisely the changes `schedule_of` bakes today — that
  equality is the stage's parity test, `verification.md`-shaped:
  *the dynamic performance of a static score is the static schedule,
  change for change, sample for sample.*

What it costs: the transport's questions get real answers instead of
table lookups — a seek must release what sounds and take the cursor
to the right beat (`all_off`, which exists, then a scan, which is
cheap); a loop is a seek on a boundary.  The `Assigned` guarantee is
untouched: assignment stays compile-time, only *delivery* moves.

## Stage two: lazy layout — the score as an unfolding value

A `[: a :]` is a cons structure and the G-machine is lazy.  A
performer that *forces the score incrementally* — enough cons cells
to cover the next few beats, no more — plays a score with no end:

    score = cycle (bar >>= voices.kit)          -- forever is a value
    score = unfold seed nextBar >>= voices.lead -- generative, seeded

Nothing new in the language: `cycle` and `unfold` are ordinary
functions the moment nobody demands the whole list before the
downbeat.  The performer becomes the demand: force to the horizon,
play what appeared, repeat.  A generative piece is then *seeded*
(`Seed` exists) and therefore replayable — the transcript records the
seed, not the surprise.

What it costs: the G-machine at performance time, which the home
contexts have and the exported plugin does not — this stage is where
`spec/substrate.md`'s Rust port of the G-machine stops being about
the GUI and starts being about the music.  Until the port, stage two
is editor-and-offline only, and stage one's descriptor carries a
*finite prefix* of an infinite score, honestly truncated.

## Stage three: the reactive score — a performance that listens

The score as a function of what arrives: chance conditioned on a
knob, a phrase answered when a key strikes, a canvas click that
plants a note where it lands.  `gateOn` was this idea's seed at the
signal level — *any condition is a note* — and stage three is the
same sentence at the score level: any arrival is a phrase.

This is the stage that must be designed slowly, because it bends the
claim the whole audio half rests on ("the graph is exactly what the
source says") from the graph to the *performance*: the graph stays
static; what walks it becomes a dialogue.  The shape that preserves
honesty: the performer's inputs are **arrivals on declared channels**
(the context contract again — nothing nominal, nothing ambient), its
decisions are a pure function of `(score, arrivals, seed, beat)`, and
therefore a transcript of arrivals replays the performance exactly.
Improvisation with provenance.

## What is deliberately not here

* **No live-coding text protocol.**  Editing the source *is* the live
  coding, and stage 5 already migrates the state; a second textual
  surface would be a second truth.
* **No inferred dynamism.**  A static score stays static — stage one
  changes when notes are *delivered*, never which notes exist.  The
  written-not-inferred rule kept oscillator phases safe across edits;
  it keeps performances safe across stages here.
* **No per-sample performing.**  The performer decides at control
  rate, like every note that ever arrived from a keyboard; what needs
  sample accuracy is carried by the values (`gateAt` names the exact
  onset), which is the encoding the bank has always used.

## The order of work

Stage one is mostly rearrangement: the beat-domain events exist, the
allocator exists, the Rust allocator exists, the transport rule
exists.  Its parity test can be written *before* it ("dynamic equals
baked") and should be.  Stage two waits on nothing at home and on the
G-machine port abroad.  Stage three waits on the transcript format —
a performance that listens must be a performance that can be replayed,
or the four silent defects of stage 10 get a stage of their own.
