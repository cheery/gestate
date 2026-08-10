# Shapes, tempo, and the fermata — ariadne's last stage

*Written 2026-08-11 at Henri's request, to be shot at.  A proposal:
nothing here is built.  Companions: `spec/ariadne.md` (the surface
this completes), `spec/dynscore-constraints.md` (the walls), and
`roadmap.md`, which has argued this stage comes after paths — it
does, and paths are now built.*

The three constructs below arrived separately — envelopes in the
score, tempo written where it happens, and a fermata that takes a
channel — and they turn out to be **one family, distinguished by what
they bend**:

| | reads | bends |
|---|---|---|
| `hear` (built) | the world | **content** — what sounds |
| `shape` | a written envelope | **a value** — what a channel says |
| `tempoShape` | a written envelope | **time** — how fast the clock runs |
| `fermata` | the world | **time** — whether the clock runs at all |

So `fermata` is not an exception to be special-cased: it is `hear`'s
twin across the table, and `tempoShape`'s twin down it.  `hear` lets
the world choose *what*; `fermata` lets the world choose *when*.  That
symmetry is the argument for building all three together rather than
one at a time.

## `shape` — automation, written where it belongs

    shape : Chan Float -> List Envelope -> [: a :] -> [: a :]

    verse = shape swell [Step 0.0 0.2, Ramp 1.0 0.9] versePattern

Across the subtree's own span the named channel follows the envelope,
its breakpoints given in **fractions of the span**.  A crescendo
across a verse is a musical fact the score has never been able to
state: `bpm` is global and dynamics belong to the DAW's automation
lane.

**The envelope type already exists and must not be invented again.**
`audio.ges` declares `Envelope := Step Float Float | Ramp Float Float`
with `on : List Envelope -> Float -> Float` — "what the envelope reads
at `x`" — total at both ends, with `envexpand.py` already rewriting
`on` into the flat comparison tree the static fragment needs.  A first
draft of this file proposed an `Env` type and an `env [...]` builder;
that was reinvention, and the reason it is worth recording is that
`music.ges` had *already made this exact decision once*, out loud:
`type Tempo = Envelope`, because "declaring it twice would give a
scored program two `Step`s, and a constructor's name is the whole
program's."  A shape reads the same type at a fraction of its span.

(`Envelope` lives in `audio.ges`, so `shape` is audio-side — which is
right: what it writes is a channel, and a MIDI-only piece has none.)

**It is automation of a knob, and needs no new engine machinery.**
Gestate's control rate *is* once per block (`spec/liveaudio.md`), and
a knob is a channel written at block boundaries — so a shape is the
performer writing `values[chan]` per block, exactly as an allocator
writes a note's payload.  A player who wants it smoother than a block
smooths it in signal land, where `slew` and the filters already live;
the language should not grow a second answer to a question it has
answered.

*(The line trick — `(base, slope, anchor)` evaluated at `ticks`, which
is how `beat` is fed sample-smooth from block-rate updates — is
available if a shape ever needs audio-rate accuracy, at three channels
per shape.  It is deliberately **not** the first cut: three channels
per crescendo is a lot of machinery for something the ear cannot
distinguish from a block-stepped ramp under a `slew`.)*

**The laws come from ariadne's law** — route a constant through it and
the algebra must not notice:

- **it scales**: `shape c e s |* 2` stretches the envelope with the
  span, definitionally, because the breakpoints are fractions;
- **it reverses**: `reverse (shape c e s)` plays the shape backwards
  over the reversed content;
- **it commutes with bind**: `shape c e s >>= f` shapes the
  substituted content — the annotation rides the subtree and touches
  no event;
- **a flat envelope is a knob write**, indistinguishable from today's.

**A shape needs a measurable span**, and this is the constraint the
last session taught rather than a new one: fractions need a
denominator, and `durOf` of an unanswered question is 0.  So a shape
whose span holds a `hear` is refused by the same test that stops a
resume — `opaqueHead` — with the same cure in the message: declare
the width with `long n`.  That `long` is load-bearing was measured
last session; this is the second place it pays.

## `tempoShape` — the clock, bent locally

    tempoShape : Env -> [: a :] -> [: a :]

    rit s = tempoShape (env [(0.0, 1.0), (1.0, 0.5)]) s

The same construct pointed at the clock: across the span, the score's
own time runs at the written multiple of its tempo, so a ritardando
is written *where it happens* instead of in a global declaration.

**A piece already writes a tempo envelope**, and this is the second
thing a first draft of this file was about to reinvent:

    tempo : List Tempo
    tempo = [Step 0.0 120.0, Ramp 32.0 90.0, Step 48.0 120.0]

works today, end to end — `tempo.py`'s `TempoEnvelope`, the envelope
branch of `samples_of`, `beatOf` in the graph.  What is missing is not
tempo curves; it is saying one **where it happens** instead of at the
top of the file.

**And `music.ges` has already refused the design this file first
proposed.**  Its own words, about why tempo is an envelope over beats
rather than an arbitrary signal:

> An arbitrary `Sig Float` tempo has none of them — it can only be
> integrated forward from zero, so a seek is a replay.

The four things it would cost are named there: a schedule precomputed
into sample instants, seeking to a bar, a bar ruler, and looping
between bars.  An **integrating clock** — `tick += rate(tick)·Δt`,
which the first draft proposed — is exactly the rejected shape,
because beat stops inverting in closed form.  So it is out, and the
right design is the one the existing machinery already implies:

**`tempoShape env s` inserts breakpoints into the one global
envelope.**  The span's start and end in beats are computable
(measurable spans, the same requirement `shape` has), so a local
shape is a *rewrite of the piece's tempo envelope* at those two
beats — one envelope still, still linear in time, still quadratic in
beat, still invertible in closed form.  Nothing downstream changes:
`samples_of`'s envelope branch already does this arithmetic, the CLAP
cursor already carries a tempo, and seek, the bar ruler and looping
all survive because the property they rest on is untouched.

That makes `tempoShape` **far cheaper than advertised** — a
compile-time rewrite rather than a fifth clock — and it moves it from
"expensive, ship separately" to "the same weight as the other two".

## `fermata` — the world chooses when

    fermata : Chan a -> [: a :]

    cadence = '(Custom 1.0 72) ++ fermata holds.keys ++ resolution

A **zero-width leaf, like `mark`**, that holds the performer's clock
while the channel reads anything at all and releases it when the
channel reads empty.

**A hold is a wall-time offset, not a rate change** — which is what
keeps it out of the integrating trap above.  The map from wall time
to score time stays exactly what it is; the performer subtracts the
time it has spent holding: `tick = beat_at((t − heldSoFar)/rate)`.
Closed form intact, seek intact, parity intact, and a piece with no
fermata subtracts zero.  With `holds.keys` that is literally *the band waits
while your hands are down* — the jazz trio's waiting, which
`jazz.ges` currently fakes with a probe every bar, said once and
exactly.

Three things fall out rather than being built, which is the sign the
shape is right:

1. **The held chord sustains itself.**  Nothing special happens to the
   notes: their note-offs are scheduled at score ticks the clock has
   not reached, so the instrument simply holds them.  A fermata over a
   chord sustains the chord because that is what stopping the clock
   *means*.
2. **`durOf` is untouched.**  A fermata is zero beats wide in score
   time; what it bends is the map from wall time to score time, which
   is the tempo's job and not the layout's.  So the algebra does not
   notice it at all — no boxes, no measurability problem, and a
   fermata inside a `long` is still a skippable span.
3. **It is `hear`'s twin.**  Both are joints reading a declared
   channel;
   one lets the answer choose content, the other lets it choose when
   to continue.  Everything ariadne already built for joints — keys,
   the thread, replay — applies unchanged.

**The hold goes in the thread**, keyed by position like a reading,
because its *length* is world input: `("held", beat, chan, key,
samples)`.  That is what makes a fermata replayable — a take that
waited four seconds for your hands replays as four seconds, and
"improv equals replay" survives.  Without it the oracle breaks, so
this is not optional.

**It holds forever if nobody releases it** — Henri's call, and the
honest one: a fermata means *wait*, a player is right there, and a
transport can always seek.  No ceiling, no timeout, no policy.

**Abroad it is honest but different.**  Under a DAW the transport
owns time, so a plugin cannot stop the session clock; a fermata there
holds the *score's* clock while the timeline runs on, which means the
piece falls behind the bars deliberately.  That is what a fermata
musically *is*, and it is also exactly the promise `spec/export.md`
makes about being locked to session bars — so a fermata in an
exported piece should be **named at export time** rather than
discovered in a session.

## Channels — and why `Port` and `Sink` were a mistake

**There is no `Port` and no `Sink`.  A channel is a `Chan`.**  Stage
three introduced `type Port = Int` on a premise nobody checked — that
`Chan` "is not in `music.ges`'s standalone scope, the same dodge as
`Seed = Int`" — and the premise is false.  `Chan` is a **builtin type
name** (`types.py`) and `chan` a builtin expression, so both are in
scope in a MIDI-only program; measured, a piece with `listen : Chan
Int` and no audio backend at all compiles and performs.  `Chan (List
Int)` type-checks too, which is what a bank's held keys actually are.

And the identity was already there: `NChan` carries `chan_id`, *"an
integer, globally unique"* — so a channel **value** is exactly the
identity `Port` was faking, minus the fiction that it is an ordinary
number.  Written properly:

    hear    : Chan a -> [: a :]
    fermata : Chan a -> [: a :]
    shape   : Chan Float -> Env -> [: a :] -> [: a :]

This is strictly better than the alias in three ways.  The **context
contract** is enforced by the *type* rather than by convention: what a
score may hear is declared, and declared with what it carries.  A
**knob steers a score** with no bridge at all — the thing stage three
wanted and could not spell was never a bridge, it was this signature.
And `holds.<bank>` stops being a generated `Int` constant and becomes
a generated `Chan (List Int)`, which says what it holds.

The one asymmetry to keep: a channel a `shape` writes must not also be
driven by a `voices` expansion, for the reason the CLAP export refuses
automation into a bank's payload — *a note nobody played*.  The
expander knows which channels it generated, so the check exists
already.

### The one thing it costs: `NewChan` in crust

Measured, not guessed: `gestate.crust.serialize` refuses a program
that says `chan` — *"`NewChan` is outside crust's pure core"* — so
adopting `Chan` in the score would send every listening piece back to
the reference machine and give up the native path they have today.

The fix is the smallest possible widening, and it is worth stating
why it is small: a score **creates** channels and never **reads**
them — the host does the reading — so the score needs `NewChan` and
the `NChan` node and *nothing else* of the reactive half.  No
`SigCons`, no `SigHead`, no `MkDelayAp`; those are signal-land and
stay home until the substrate panel wants them (`spec/crust.md`).
`NewChan` is a counter and an allocation.

**The migration is done.**  crust learned `NewChan` (a counter and an
allocation, plus `Node::Chan`); `hear : Chan (List Int) -> [: List
Int :]` — monomorphic, because a bank's note port carries exactly
that and a `Score` has one type parameter to spend; the expander
generates `holdsLead : Chan (List Int) = chan` where it generated an
index; `CueAsk` carries the channel and both performers read
`chan_id` off it; and `ports_of` reads the ids back by forcing the
definitions.  The arpeggiator plays over channel identities, and the
crust twin still listens.

**It uncovered a real defect on the way**, which is the argument for
having done it: `gmachine._force` ran on a scratch machine with its
*own* `chanCounter`, so every channel forced separately came out
`NChan(0)` — the identity whose own docstring calls it "globally
unique" was not.  Nothing had noticed, because channels were only
ever named by their declaration; a score that *listens* to one names
it by id, and two banks collided immediately.  The counter travels
with the scratch state now.

## What this costs

- **`shape`**: a constructor and its arms, a per-block write in the
  performer, and the `opaqueHead` refusal for unmeasurable spans.  No
  engine change.  Cheap.
- **`fermata`**: a constructor and its arms, a clock hold in the
  performer, a thread entry, and the export-time naming.  Also cheap —
  and it is the one with the most musical return.
- **`tempoShape`**: a compile-time rewrite of the piece's tempo
  envelope at two computable beats.  Cheaper than this file first
  claimed, because the envelope machinery it needs is built and the
  integrating clock it feared is not wanted.

## Acceptance

1. **The constant law, three times**: a flat `shape` is a knob write;
   `tempoShape` at rate 1 changes no tick; a `fermata` on a channel
   that is always empty changes nothing at all.  The third is the
   sharpest: it says a fermata costs a piece nothing until it holds.
2. **The shape laws**: scales with `|*`, reverses, commutes with
   `>>=`.
3. **The unmeasurable refusal**: `shape` over a span holding a `hear`
   is refused by name, and the message says `long`.
4. **Sustain falls out**: a chord under a fermata is still sounding
   when the hold releases, with no note-off in between.
5. **Improv equals replay, with holds**: a take that waited replays
   with the same waits, from the thread.
6. **Unshaped parity**: every existing golden and every bit-parity
   suite passes untouched, which is the routing working.
