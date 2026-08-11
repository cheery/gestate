# The dynamic score — a performance that executes as it plays

*Written as a design; companion to `spec/export.md` (whose transport
made it thinkable) and `spec/verification.md` (whose oracles will keep
it honest).*

*Status, 2026-08-11: **stage two is abroad too, and an exported plugin
now performs its own unfolding score.**  `shell/clap` takes `crust` as
a dependency under a `dynscore` feature; `export.program_of` serializes
the compiled program into the descriptor when `score_events` has no
finite list to write, along with the entry, the seed, the constructor
tags and the `holds.<bank>` ports; and `shell/clap/src/dynscore.rs` is
`LazyPerformer` retold — the pending heap in `(sample, releases-first)`
order, the frontier gate, drop-and-report, and the question loop that
answers `hear` from the keys the player is holding.  Held against the
reference by `shell/clap/tests/dynscore_parity.rs`, event for event.
The sentence this file used to carry — "the plugin is the instrument
without its piece" — is retired: `moods`, `arpeggiator`, `ladder` and
`jazz` play as plugins.

Seek re-opens the stream at the target tick and lets `liveMain`'s own
second argument do the skipping, so a jump to bar 400 is a descent
rather than a walk through 399 bars; a listening piece re-asks its
questions afterwards rather than replaying answers, which is right
live, where the world is the player's hands and they are where they are
now.  Not yet: a transcript abroad, and the shapes and fermata the home
performer writes.*

*Status, 2026-08-10: stage one is built at home **and abroad** —
`audiodynamic.Performer`, held to the bake by `test_dynamicscore.py`,
with the seek/loop semantics pinned there before any second
implementation existed; and its Rust half, the CLAP cursor
(`shell/clap/src/score.rs`), which is that file's retelling with the
clock in the transport's hands: the exporter writes the piece's
events in *beats* into the descriptor (`export.score_events`, ticks
exact via the identity-tempo reuse of `timed_events`), and the cursor
performs them against `song_pos_beats` — a timeline jump is a seek, a
loop is a seek on a boundary, a host with no transport free-runs the
piece at its own tempo, and steady playback keeps the bake's exact
integers (`tick·60·rate // (bpm·TPB)`, in i128).  Held by the cursor's
own unit tests and by `test_export.py`'s ctypes host end to end:
pressing play performs the bake sample for sample, and playing from
the middle stands where playing from the top would stand.  Stage two
is built at home — `streamVoices` in
`music.ges` (an ordered lazy merge, so two endless branches of a `||`
interleave), `cycle` and `unfold`, `ScoreStream`/`LazyPerformer` under a
`StepLimit` budget with the stall-and-drop rules below, held by
`test_lazyscore.py`; abroad it waits on the G-machine port
(`spec/crust.md`).  Stage three is built at home — its surface was
settled 2026-08-10, is specified at the end of this file, and landed
the same day: `sown` and the seed algebra (SplitMix64 in `music.ges`
itself, bit-exact as the crust parity contract), `probe` as a cue
stream (`liveVoices` in CPS, an ask's continuation holding the rest of
the performance), `resumeAt` descent, and the transcript with its
improv-equals-replay oracle — held by `test_sownscore.py`,
`test_probescore.py` and `test_lazyscore.py`, with `jazz.ges` and the
arpeggiator as the acceptance pieces.  Abroad it waits with the rest.*

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

## Stage three, the surface — settled 2026-08-10

*Sketched in conversation the evening stages one and two landed at
home; recorded here so the build has a sheet to be checked against.
Nothing below is built.*

### The invariant everything else hangs from

**A listening score bends content, never time.**  Stage one moved when
a note is *delivered*, stage two moved when it is *forced*, and stage
three moves when it is *decided* — and none of the three moves the
timeline.  Every reactive leaf below is a leaf of the ordinary layout
algebra: one beat unless `|*` and `|/` say otherwise, its extent
declared in the text, only its *content* decided late.  So `durOf`
stays total, a seek still descends a tree whose spans are written
down, and no performance can accelerate its own structure — the Zeno
guard stays a budget, never a semantics.  Content a decision produces
beyond its declared span is clipped, and said so, in the drop rule's
own vocabulary: a section that outruns its box rejoins nothing.

### `probe` — reading the world

    probe : Chan b -> (b -> [: a :]) -> [: a :]

A one-beat leaf whose content is the continuation applied to **what
the channel reads at the leaf's own downbeat**.  The decision instant
is the leaf's position in the score — the layout algebra already
gives every node its offset, so nothing new says when — and the
performer answers the reading from exactly where the graph's control
node would read the same channel: one channel, two clocks, audio rate
for the graph and decision instants for the score.  Probing a
*channel* rather than a signal is the context contract enforced by
the type: what a score may hear is declared, nothing nominal, nothing
ambient.  `beat` needs no probe; a probe already knows where it
stands.

Responsiveness needs no policy on top: a probe cannot be forced
before its downbeat approaches, so the stream's frontier rides the
clock through listening sections — stage two's stall machinery *is*
the suspension mechanism, and the latency of a reactive figure is the
probe granularity its author wrote (`|/ 4` listens every sixteenth),
never the performer's horizon.

The note port arrives as a channel like everything else: the proposed
spelling is `holds.<bank>` — the currently-held keys of the bank a
`FromMIDI` instance plays, wired by the expander the way
`voices.<bank>` is.  The acceptance test for the whole stage is the
**arpeggiator**: `cycle (probe holds.lead step |/ 4) >>= voices.lead`
— held keys sampled each sixteenth, one planted note each, sample
accuracy carried by `gateAt` as always.

### `sown` — reading the seed

    sown  : (Seed -> [: a :]) -> [: a :]
    split : Seed -> (Seed, Seed)
    below : Int -> Seed -> Int              -- one draw in 0 .. n-1
    random : (Random a) => Seed -> a        -- one draw of a whole value
    sow   : Seed -> [: a :] -> [: a :]      -- re-root a subtree's seed

`probe` reads the world; `sown` reads the seed — the same leaf shape,
the same span discipline, and the pair is the whole of stage three's
input story.  **The seed rides the layout tree**: `++` and `||` each
split it, left and right, so every subtree owns a stream derived from
its place in the piece.  A draw at bar 33 is a descent's worth of
splits, not a night's worth of generator steps; two rolls under one
overlay are independent because they sit on different split paths;
each turn of a `cycle` is a fresh right-split, so a looped chance
breathes differently every bar — from one integer.

`Random` is a class so that a *value* is drawn the way a value is
built: `Random Float` is the unit interval, and an author's payload
draws whole — `sown (s => '(random s))` — its instance splitting the
seed it owns, one field each.  An instance receives its seed
outright; what it does not split it must not reuse.  `roll`, `chance`
and `pick` are library sugar over `sown` and `random`, not machinery.

`sow` re-roots: `sow (Seed 7) intro ++ improvisation` is fixed art
inside an improvisation, and a seed taken *from the world* is `probe`
composed with `sow` — no new event kind, and provenance holds by
composition because the probe was already logged.

**Two generators, one documented boundary.**  The audio fragment
keeps its LCG — its constants were chosen so every product fits an
i64, which is why the interpreter and the generated code agree to the
bit, and nothing may disturb that.  The score's splitter is
SplitMix64, because LCG streams split by nudging constants are
*correlated* — in a texture nobody hears it, in two "independent"
`chance` branches it is audibly the same choice twice.  Spelled with
an explicit modulus so the G-machine's integers, the bake, and the
Rust cursor compute identical draws — `python draws == rust draws` is
a parity test to be written, and exactly where a stage-10-style
silent defect would otherwise nest.  The LCG is a texture; SplitMix
is an index.

### Provenance

A program that writes `seed = Seed 7` is fixed art, replayable from
its text alone.  A program that reaches `sown` without writing a seed
gets the renderer's entropy — the OS's at instance creation, a
`--seed` flag or the clock offline — under the unbreakable rule: the
renderer records what it supplied, in the transcript, the take's
metadata, the plugin's state.  **The transcript records the world and
the seed; everything else is arithmetic.**  Probes are logged, beat
by beat, channel and value; draws are never logged, because they are
derivable — which is "one integer replays the whole night" held as a
theorem rather than a hope.

And because a draw is a pure function of seed and position, **chance
music stays bakeable**: once the seed is known, the eager layout can
evaluate `sown` exactly as the performer would, so `sown` does not
force the dynamic path and `unfolding_names` must not flag it.  The
parity clause extends: *a rolled score bakes and performs
identically, given the seed.*

### Seeds on the audio side

`Seed` is already an `Int` on purpose over there, and a seed is a
value, so the transports already exist; stage three adds no new one.

* **The noise family's seed parameter is promoted to `Sig Seed`** —
  `white : Sig Seed -> Sig Float`, `dust : Sig Seed -> Sig Float ->
  Sig Float` — with reseed-on-change semantics: a constant seed seeds
  once and means exactly what it means today; a seed that changes
  re-mixes the generator's state at the instant it changes.  No
  second name beside `white`: the promotion is the feature.
* **Per take**: `entropy : Seed` as a renderer's own name — the
  `sampleRate` pattern — substituted at instance creation and
  recorded where it was supplied.  `white (!(entropy + 1))` beside
  `white (!(entropy + 2))` is a stereo bed fresh every take and exact
  on every replay.
* **Per note**: a payload field is already a channel into the voice,
  so the score draws, the note carries, the voice re-seeds — the
  `Gate` trick a third time, values name and voices do the
  arithmetic.  A snare whose burst is decided per hit by the piece,
  improvised live, bit-exact on replay.
* **Per gesture**: any control channel can carry a `Seed`, because a
  `Seed` is an `Int` — a knob, a probe, an automation lane.

### `long` — the span, handed to the author

*(Added after the first rebuild measurement: resuming a 5-minute
performance cost 48 seconds of left-to-right forcing.)*  `long n s`
declares that a branch is `n` beats wide whatever its content does —
`Clip`, which every `sown` decision already wears, given a public
name.  The declaration pays twice: structure a reader can trust today,
and the box a resuming performer skips *without forcing what is
inside* tomorrow.  Two tracks close the resume question: declared
spans skipped by arithmetic (`resumeAt`, the in-language re-rooter,
runs on the sown tree so every seed keeps its position), and the
tree-walking performer for scores that declare nothing — which is the
same machine `probe` needs, and they land together.

### The order of work

The transcript format first — it is what keeps everything after it
honest, and stage two's `history` and `transcript` lists are its
embryo; *a live performance equals its own replay* is the oracle, and
it can be written before any input exists.  Then `sown` and the seed
algebra, whose bake-parity test needs no world at all.  Then `probe`
with a knob, the first logged reading end to end.  Then `holds` and
the arpeggiator, which is the stage's proof: one of everything,
almost all of it already built.
