# The constraints on infinite, dynamic, resumable scores

*Written 2026-08-10, on request, as raw material for a redesign
attempt.  The stage-three machinery is built and green
(`spec/dynamicscore.md`), and its author's judgment on it stands:
**the solution is an eyesore**.  This file therefore does something
the other specs do not: it separates the *forces* from the *answers*,
so the problem can be attacked fresh without being argued back into
the current shapes.  Three registers, kept strictly apart: laws of
the problem, which no design escapes; commitments this project chose,
each renegotiable at a stated price; and the current solution's
specific answers, all of which are furniture.  A fourth section lists
where the current answer grinds — a redesign is good exactly insofar
as it dissolves that list while keeping register A and consciously
pricing register B.*

## A. Laws of the problem

No design escapes these; they can only be moved around.

**A1 — Causality.**  At a note's onset instant, the note must be
known.  Deciding takes time, and in general (a lazy language, a
user's continuation) unbounded time.  So every design must choose,
for each lateness, one of: decide early (lookahead), bound the
decision (budgets), or define what lateness *means* (drop, silence,
stall).  There is no fourth option; "it won't happen" is the silent
defect wearing a hat.

**A2 — The world arrives when it arrives.**  Input-dependent content
(a probe, a held chord, a knob) cannot be computed before the input
exists.  This puts lookahead and responsiveness in direct tension:
sample-accurate onsets want the decision *before* the sample; a
performance that listens wants it as late as possible.  Every
listening design has a latency, and that latency equals its decision
granularity — the only question is who states it, the author or an
accident.

**A3 — Infinity forbids totality.**  An endless score has no whole
layout, no total duration, no golden render.  Every operation on it
is an operation on a *prefix or window*, and any machinery that
secretly needs the whole thing (an eager fold, an accumulator
reversed at the end) is wrong by construction, not by bug.  Anything
that walks it must be able to stop mid-thought and continue —
resumable forcing is forced by the shape, not chosen.

**A4 — The random-access trilemma.**  Standing at time T inside a
lazily defined structure requires at least one of:

  1. **Force everything before T** — always correct, linear in T,
     unbounded for a rebuild mid-set (the measured 157 s).
  2. **Skip by structure** — some part of the tree's *shape* (widths,
     offsets) must be knowable without forcing its *content*.  This
     is where every "declared extent" idea comes from: skipping is
     exactly the privilege of not evaluating, so whatever is needed
     to navigate must be cheaper than what is being skipped.
  3. **Checkpoint** — snapshots or logs from a previous pass.  Costs
     storage and a prior pass; a *cold* resume (fresh process, edited
     text) needs the checkpoint to survive both, and an edit
     invalidates unknown amounts of it.

  Any solution is a point in this triangle.  The current one is
  mostly (2) with a little (1) at the leaves; a redesign may pick a
  different point, but it must pick.

**A5 — State at the cut.**  A performance mid-flight holds state in
layers: which voices sound (allocators), where each envelope stands,
filter and delay memories, the walk's own accumulators.  A resume
must reconstruct each layer or declare its loss.  Two facts are
unavoidable: a note *held across* T is recoverable by arithmetic (its
onset is a fact of the score), but a *tail* from before T — a release
still ringing — is information about the past; it can only be
replayed (cost), simulated (a second engine), or cut (audible).
There is no free option; only a chosen one.

**A6 — Two currencies of time.**  Beats are the score's time,
samples the engine's; tempo is the exchange rate and may itself
change mid-performance (a DAW drag).  Rounding is a decision: any two
independent spellings of beat→sample will eventually disagree by one
sample, and one sample is a real disagreement (bit-parity is the
project's own oracle).  So the conversion must have **one spelling,
owned in one place**, however many implementations perform it — this
is a law learned empirically (stage 10's defects all nested in a
second spelling of *when*).

**A7 — Order at shared instants.**  Distinct events land on the same
instant (a release and the onset that legato-reuses its voice; two
branches of `||`).  Their order is semantics, not bookkeeping — it
decides which voice a note lands on and therefore which sample plays.
The order must be defined, total, and shared by every implementation.

**A8 — Zeno.**  A combinator algebra that can shrink sections can
pile infinitely many events below a finite horizon.  A design either
excludes this structurally (widths bounded below), detects it
(budgets on count, not only depth), or hangs.  Related but distinct:
whether a performance can *reschedule its own future* (accelerate its
structure).  If it can, navigation (A4.2) collapses — shape becomes
run-dependent — so a design that wants skipping must forbid it
somewhere, and should say where.

## B. Commitments this project chose

Each is renegotiable.  The price is listed with it; a redesign that
drops one should do so out loud.

**B1 — Replay is a theorem, not a hope.**  A performance is a pure
function of `(text, seed, arrivals, beat)`; the transcript records
the world and the seed, and everything else is arithmetic.  *Price of
keeping it*: randomness must be derivable — either seeds are a
function of something stable (the current answer: position), or every
draw is logged (rejected as "recording the surprise").  *Price of
dropping it*: improvisation without provenance; the four silent
defects of stage 10 get a stage of their own.

**B2 — The dynamic performance of a static score is the bake.**
Change for change, sample for sample.  This is what lets the whole
dynamic tower ship without re-litigating stage 10's guarantees.
*Price of keeping it*: the shared ordering (A7) and the shared
arithmetic (A6) must be factored where every implementation —
Python eager, Python lazy, Rust cursor, and one day crust — can
reach them.  *Price of dropping it*: two truths about the same
piece; every golden becomes advisory.

**B3 — Refusal over hanging.**  A path that cannot work says so by
name before it runs (`unfolding_names`: "this score unfolds"), rather
than walking forever.  *Price*: a conservative syntactic scan with
false positives (which only cost routing).  A redesign with a richer
notion of "finite in this direction" could refuse less.

**B4 — A hang is absence, never corruption.**  The engine never
waits on a decision: what was emitted plays out; what is late is
dropped *and said*; what stops is the future.  Budgets are fuel,
count, and wall clock, because each guards a hang the others cannot
see.  *Price*: budget bookkeeping threaded through the forcing
protocol, and the subtle gates that came with it (a note-off of a
sounding note must bypass the gate, or a stall is a stuck note; a
pending question is not a stall).

**B5 — Rebuild rejoins; it does not replay.**  A live edit installs
a new score that *continues from the transport's now* — state
migrates by identity, the past is not re-performed audibly.  *Price*:
this is what makes A4 bite at all (rejoin at minute 15 is random
access), and what makes the answer's cost a UX fact (48 s is an
unusable instrument; 1 s is an instrument).

**B6 — Many hosts, one semantics.**  Editor, offline CLI, pygame
bench, exported CLAP plugin — and the semantics may not vary by host.
*Price*: the score must either serialize into a host (the
descriptor's beat-domain events) or be forced by a machine the host
contains (crust); and the reference implementation plus parity suites
are the only thing keeping N hosts honest.  Any redesign multiplies
by N.

**B7 — Declaredness ("written, not inferred").**  What a piece does
is visible in its text: extents, banks, tempo, listening points.
This is the project's oldest commitment (it kept oscillator phases
safe across edits) and the deepest root of the current 1-beat rule —
see `spec/sown.md` for the full five-whys chain.  *Price*: ceremony
at exactly the places an author wants freedom, which is most of
section D.  *Price of dropping it*: shapes become run-dependent and
A4.2 collapses to A4.1 or A4.3.

## C. The current solution's answers (all furniture)

Listed so the redesign knows what is *removable* — each is one answer
to the constraint named, never the constraint itself.

- **Declared-width leaves** (`sown`/`probe` one beat, `|*`/`|/`
  spans, clip-and-report) — answers A4.2 + B7.  Consequence found
  today and recorded in `spec/sown.md`: a bound score's *extent* may
  overhang the box (rings past the barline); only placement is
  pinned.
- **Seeds ride positions** (SplitMix64 split at `++`/`||`, fresh
  right-split per `cycle` turn, `sow` re-roots) — answers B1 without
  logging draws; makes a draw at bar 33 a descent, not a night of
  generator steps.  Known gap: take-entropy cannot reach an
  `unfold`'s state (the seed enters only through the tree).
- **`Clip`/`Mark`/`resumeAt`** — the A4.2 navigation: skip whole
  boxes by arithmetic, enumerate re-entry points without touching a
  note.  Known slops, documented in `resumeAt`: `Scale` cuts floor
  to k, `Retro` resumes whole, the *eager* bake still lays a clip's
  content whole (the eager/lazy asymmetry).
- **The cue stream** (`liveVoices` in CPS; `CueAsk`'s continuation
  holds the rest of the performance; three wrap lemmas push bounds
  and context into k) — answers A2 inside a flat event stream
  without host-side tree walking.  Retro cannot listen, documented.
- **`ScoreStream`/`LazyPerformer`** (fuel/burst/patience, frontier,
  stall transcript, drop-and-report) — answers A1/A8/B4.
- **`timed_events` + `samples_of`** (one ordering: releases first;
  one arithmetic: the integer path) — answers A6/A7; the CLAP cursor
  and the bake both cite it, and the identity-tempo trick
  (`timed_events(events, 60, TICKS_PER_BEAT)`) exists purely so the
  descriptor reuses the one sort.
- **`unfolding_names`** — answers B3 by syntactic scan.
- **Transcript** (source hash, rate, block, seed, readings) —
  answers B1's storage half; replay answers probes from the log.

## D. Where it grinds — the eyesore, itemised

The symptoms a redesign should be judged against.  Each traces to a
register-A law refracted through register-B choices; none of them is
anyone misusing the system.

1. **The compress–stretch dance.**  Sixteen beats of content in a
   one-beat box spelled `(… |/ 16) |* 16` — the author writes a
   no-op (divide by n, multiply by n) as ceremony to satisfy B7.
   nightdrive does this twice per line.
2. **N draws need N leaves.**  `++` inside one `sown` silently clips
   to the first beat.  Bitten twice on separate days (the
   silent-horns evening; a test fixture here), recorded at the end
   of `spec/sown.md`.  Clip-and-report evidently reports where
   nobody looks.
3. **The probe box repeats the same trap** — a probe is a one-beat
   leaf; hand it four beats and three are gone.  Same law, same
   surprise, second spelling.
4. **Take-entropy cannot seed a walk.**  An endless `unfold` whose
   *state* consumes draws can only be seeded by a literal — fixed
   art — because the seed travels positionally and a box cannot hand
   a value out.  The nearest spelling is a giant box around a seeded
   walk, which is exactly the ceremony of (1) at its worst.
5. **Two overlapping mechanisms for one idea.**  `Clip` (widths, for
   skipping) and `Mark` (points, for naming) both exist because
   neither alone answered resume; "clips are the mechanism, marks
   are the map" is a sentence that has to be *taught*.
6. **The eager/lazy asymmetry.**  `cycle` under `long` is
   dynamic-only because the eager bake lays clip content whole — two
   walks with different strengths over one algebra, patched by
   routing (B3) rather than unified.
7. **CPS wrap lemmas.**  The cue stream is correct because three
   lemmas push bounds into continuations — the `streamMarksTo`
   bound-must-ride-the-spine lesson generalized.  It works and it is
   pinned by tests, but it is the kind of correctness that lives in
   three places at once; the same lesson had to be learned twice.
8. **Constructor tax.**  Every new score constructor (`Sown`, `Sow`,
   `Clip`, `Mark`, `Probe`) must be added to *every* walk — nine
   arms at last count — with exhaustiveness as the only guard.
9. **Budget subtlety.**  Fuel, burst, patience, `_begun`,
   frontier-bypass for note-offs, ask-is-not-a-stall: each is a
   correct answer to a real hang, and together they are a lot of
   machinery whose interactions only the suites understand.
10. **The two-bank law** (a listener cannot probe the bank it
    writes) — a real constraint (feedback through the note port),
    currently enforced by convention and one error's worth of
    documentation rather than by types.

## What a redesign owes

To beat the current solution, a proposal must: satisfy A1–A8; state
its position on each of B1–B7 (keep, or drop with the price paid out
loud); and then show which lines of section D it deletes.  Deleting
D-lines by weakening register B is not winning — that trade was
always available and was refused on purpose.  The prize is real: a
spelling where an author writes chance, listening, and endlessness
without the boxes showing — where the ceremony of (1)–(4) dissolves
into the algebra instead of sitting on top of it.
