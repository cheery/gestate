# The dynamic score — a performance that executes as it plays

*Written as a design; companion to `spec/export.md` (whose transport
made it thinkable) and `spec/verification.md` (whose oracles will keep
it honest).*

*Status, 2026-08-10: stage one is built at home — `audiodynamic.Performer`,
held to the bake by `test_dynamicscore.py`, with the seek/loop semantics
pinned there before any second implementation exists; its Rust half (the
CLAP cursor) is not.  Stage two is built at home — `streamVoices` in
`music.ges` (an ordered lazy merge, so two endless branches of a `||`
interleave), `cycle` and `unfold`, `ScoreStream`/`LazyPerformer` under a
`StepLimit` budget with the stall-and-drop rules below, held by
`test_lazyscore.py`; abroad it waits on the G-machine port
(`spec/crust.md`).  Stage three is not started.*

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

## Three questions, considered the evening this was written

**What happens when a lazy score hangs mid-piece?**  The performer
runs off the audio thread, like every note-deciding thing already
does — so the answer is structural before it is a policy: **a hang is
absence, never corruption.**  The engine keeps rendering; every
change already emitted plays out, note-offs included; what stops is
the future.  This is `audiolive`'s own rule one floor up — "a synth
that does not compile must not stop the one that is playing" — and
the fragment's totality guarantee was never claimed for the
interpreted half, whose discipline has always been budgets instead.
So the performer forces against a **beat-horizon budget**: events for
beat *B* must exist while *B* is still ahead.  A blown budget is a
*stall*, reported at the beat it happened (and recorded — a stall is
a transcript event); if production resumes, events whose beats have
passed are **dropped, and said so** — a section that lost its place
rejoins at the current bar, it does not play the missed bars fast.
Productivity is the piece's responsibility; audibility-as-absence,
naming the beat, and rejoining cleanly are the performer's.

**What does a responsive performance extract, and from where?**  The
context contract already answers, and stage three should refuse any
other source: **readings and arrivals on declared channels, sampled
at decision instants.**  The inventory is longer than it first looks,
and every entry exists today as a channel or an arrival: the
knobs (chance, density, a transposition dial); the note port (call
and answer — the keyboard as an input *to the score*); the analysis
channels (`peak`, `bands` — a score that thins when the mix is
thick); the canvas's clicks, once the substrate travels; and `beat`
itself, which is where the performer stands.  Decisions happen at
control rate — between blocks, like every note that ever arrived from
a keyboard — and the *values* carry exactness, as `gateAt` always
has.  What the performer read is what the transcript records; its
view of the world **is** the log, which is what makes stage three
replayable rather than anecdotal.

**Randomness — pseudorandom as ever, but seeded from the world?**
The mechanism already exists (`Seed`, the `Rng` machinery, every
`dust` in the tree) and it stays: randomness *within* a performance
is a PRNG walking from a seed.  The new question is only where the
seed comes from, and the contract answers again: **entropy is a
renderer's own name.**  A program that writes `Seed 7` is fixed art,
replayable from its text alone.  A program that names the renderer's
entropy gets *a seed nobody chose* — the OS's at instance creation
for a plugin or the editor, a `--seed` flag or the clock for an
offline render — under one unbreakable rule: **the renderer records
what it supplied**, in the transcript, the take's metadata, the
plugin's state.  Fresh surprise every performance, exact replay of
any performance somebody kept: improvisation with provenance, again,
because the provenance is one integer.  Re-seeding *mid*-piece is the
same rule at more instants — each draw from the renderer is a
recorded event — and the default should be the coarse one: seed at
the top, walk the PRNG, because one number replaying a whole night is
the property worth defending.

**And the parting question: does "seek and perform" change the score
format?**  Stage one, no: the events are beat-sorted, position is a
bisect, and the state at bar 33 is a *silent replay* of the allocator
over what came before — exactly the work `into_schedule` did at bake
time, now done on demand in microseconds; the parity gains a clause,
*seek-then-perform equals `value_at`*.  Stage two, yes — but the
change is a refusal: an unforced infinite list cannot be bisected,
and the repair is not a cleverer flat format, it is **keeping the
layout tree the flattening threw away**.  `++` and `||` already carry
duration algebra (`duration_of` is it); a tree annotated with its
spans seeks by *descent*, forcing only the branch holding the target
— and splittable seeds, one per section instead of one PRNG walked
end to end, make even an `unfold` jumpable without walking.  Seek is
about the time, and the tree already keeps it.

**And the envelopes — the half that already seeks.**  Stage 10 made
every envelope *arithmetic on the instant* (`adsrOf` carries no
state; `on` is random access in time), so the performer's seek
problem is only ever about discrete decisions — the continuous
material evaluates at whatever bar the clock lands on, free.  They
also point at what a performance delivers beyond notes: the `Gate`
trick — values name the instants, voices do the arithmetic — extends
to a **note of automation**: a fixed-size segment (from-beat,
to-beat, from, to, curve) delivered on a channel and evaluated
against `beat`, giving sample-accurate crescendos across bars from
control-rate delivery.  Fixed segments deliberately, not
`List Envelope`: runtime-delivered lists cannot ride `envexpand`'s
compile-time rewrite, and a segment chains the way notes chain.  And
dynamics over a *span* — a crescendo across a section — is an
annotation on exactly the layout subtree the seek design keeps: the
tree holds the time, the envelopes hold its shape, and a seek
descends past both together.
