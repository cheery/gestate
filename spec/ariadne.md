# Ariadne — the score's reactive surface, redesigned

*Written 2026-08-10 at Henri's request, to be shot at — "let me see
whether it holds."  This is a proposal, not a record: nothing below
is built, and every decision marked **open** is his.  Companions:
`spec/dynscore-constraints.md` (the walls this must stand inside),
`spec/monad.md` (the syntax this stands on), `spec/sown.md` (the
autopsy of the surface this replaces).  The name is the design: the
score is a maze of possible performances, the **thread** is the
record of the path taken, and the guarantee is never that the maze is
small — it is that the walker can always retrace, resume, and name
where they are.*

## Where the old surface went wrong

Not in its names, and not in any single rule — in its **initial
framing**.  Stage three framed reactivity as a *threat to time*:
decisions might move downbeats, so every reactive construct was
issued a box (`sown` and `probe` clipped to a declared beat) and the
box was defended by law ("content bends, time doesn't").  The boxes
worked — every oracle held — but they were never *of* the algebra:

- the score monad is lawful **including time** — `('x ++ 'y) >>= f`
  equals `f x ++ f y` to the tick, measured — and the boxes are the
  only residents that break the homomorphism (route a constant draw
  through `sown` and the same bind comes out shifted);
- the whole grind-list of `dynscore-constraints.md` §D — the
  `|/ n … |* n` dance, N-draws-need-N-leaves, the probe box trap,
  take-entropy unable to seed a walk, the Clip/Mark duality — is the
  friction of the boxed shape against the lawful one.

The 1-beat rule was the scar, not the wound.  Ariadne removes the
frame instead of treating the scars.

## The law everything answers to

> **Route a constant through any reactive construct and the algebra
> must not notice.**

A `draw` whose seed is known behaves exactly as `'` of its value; a
`hear` whose answer is fixed behaves exactly as `'` of the reading —
event for event, tick for tick, with only the thread (the transcript)
knowing the difference.  This is the acceptance test the old surface
fails and every part of the new one must pass, and it is mechanical:
the experiment that falsified `sown` (2026-08-10) is the template.

## The interface

The score type stays `[: a :]`, and the whole written algebra stays:
`'x`, `++`, `||`, `at`, `|*`, `|/`, `reverse`, `>>=` — unchanged,
lawful, time-from-content.  The reactive surface becomes **two
zero-width leaves**, entering the monad as values:

    draw : [: Seed :]                 -- the seed at this position
    hear : Port -> [: List Int :]     -- the world at this instant

Zero width is what makes them lawful: like `mark`, they occupy no
time of their own, so `durOf` distributes past them and the
homomorphism holds by construction.  Their *values* are bound with
the `do` sugar that already parses:

    bar : [: Custom :]
    bar = do
        ks <- hear holds.keys
        s  <- draw
        '(Custom 0.8 (pick ks s))

`draw` is **not an effect** in the transcript's sense: its value is a
pure function of the take's seed and the leaf's position in the tree
— the SplitMix discipline unchanged, splitting at `++`/`||`, fresh
per `cycle` turn, and along a `do`-chain each successive bind is one
more split.  Only `hear` writes the thread.  `sow` survives as the
re-rooter it always was; `roll`, `chance`, `pick` survive as sugar
over `draw`.

### What this deletes, line by line (§D scorecard)

| §D grind | fate |
|---|---|
| 1. the `\|/ n … \|* n` compress–stretch dance | **gone** — content carries its own time; there is no box to fit |
| 2. N draws need N leaves | **gone** — N draws are N binds: `do a <- draw; b <- draw; …` |
| 3. the probe box trap (silent horns) | **gone** — `hear` has no box; the phrase it feeds has its written width |
| 4. take-entropy cannot seed a walk | **gone** — `do s <- draw; unfold (mix64 s) step` — the draw is first-class |
| 5. Clip/Mark duality | **replaced** — positions are paths (below); `long` survives only as an honest skip-width annotation, if at all (open) |
| 6. eager/lazy asymmetry | **gone** — one interpreter (below); "the bake" is its effect-free special case |
| 7. CPS wrap lemmas | **absorbed** — the continuation is ordinary `>>=`; the lemmas become the monad laws |
| 8. constructor tax | **shrinks** — Sown/Sow/Clip/Probe/Mark leave the walks; Draw/Hear/Section enter (net −2, and each new one is algebra-shaped) |
| 9. budget subtlety | **unchanged** — fuel/burst/patience are operational and stay |
| 10. two-bank law | **unchanged**, still convention (open: a type for it) |

## Time — linearized at the joints

The deliberate break with the old law, and the one place a register
is renegotiated rather than kept.  Since a joint's continuation is an
ordinary score, **its duration is its content's**, and content chosen
by a reading has the duration the reading chose.  Downbeats after a
`hear` may therefore depend on the world:

- **B7 restated**: *time is decided by the text on written spans, and
  pinned by the thread at joints.*  A performance remains a pure
  function of `(text, seed, readings)` — B1 and B2 survive intact,
  because the thread records what the world said and replay is exact.
- **`durOf` becomes stratified**, not partial-by-accident: total on
  any effect-free span (every static piece keeps every static
  privilege — the bake, the parity suites, arithmetic seek, the CLAP
  descriptor); across a joint, defined once the joint is answered —
  which is precisely the `frontier` the stream machinery has enforced
  operationally all along.  Ariadne makes the machinery's truth the
  language's truth instead of boxing it away.
- **Zeno stays a budget** (A8): joints are written in the text, so a
  performance still cannot manufacture unwritten structure; what a
  reading may do is choose among written durations, not accelerate
  the walker.

**Open (Henri's):** may a joint *wait* — a fermata, a downbeat that
holds until the world speaks — or must every `hear` be answerable at
its instant by sampling, as today?  The arpeggiator needs only
sampling; a conducted cue needs waiting; "a hang is absence" becomes
"a hang is a fermata" under the second reading.  Both fit the
design; the second moves more of register A1 into music.  Not decided
here.

## Position — paths, not ticks

A position is a **path through the tree**: which side of every
junction, which turn of every `cycle`, which bind of every chain —
derived automatically from structure, with one construct for saying
it in words:

    section : String -> [: a :] -> [: a :]

    piece = section "opening" intro
         ++ section "verse"   (cycle versePattern)
         ++ section "closing" coda

`opening`, `verse.3/bar.2` — the maze-walk string.  The precedent is
stage 5's proudest fact: graph nodes carry origin paths and live
migration works *because* identity is structural; ariadne applies the
same discipline to score positions.  Three properties paths have that
ticks do not:

1. they survive edits (a tick shifts when any earlier duration
   changes; a path names a place);
2. they survive joint-dependent time (a tick after a `hear` may be
   uncomputable before the answer; `closing` names its place
   regardless);
3. they key the thread: the transcript becomes a map from paths to
   readings, robust across takes and rebuilds.

Ticks remain as a *derived* coordinate wherever they are computable
(all effect-free prefixes), which is everything the DAW boundary
needs.  `mark`/`bar` are subsumed: an anonymous section is a bar
point.

## The thread

The transcript, schema 2: the take's seed, and readings keyed by
**path** (`verse.3/bar.2/hear#0 → [60, 64, 67]`).  Everything else
is arithmetic — draws never logged (derivable), positions never
logged (structural).  What the thread buys, now stated as the
design's core rather than a feature list:

- **Rewind**: the past of an improvisation is a fixed object; walking
  back is following the thread.  Live rewind = replay the thread to
  the target, go live past it — past from the log, future from the
  world.
- **Resume/seek**: descent by path.  Effect-free spans skip by
  arithmetic (the privilege retained); answered joints skip by
  replaying their recorded readings; the unanswered future is not a
  place, so there is nothing to skip to — which is the honest
  statement A4 always wanted.
- **Skip-what-is-identical**: a section's identity is
  `(its text, its seed slice, its readings slice)` — a checkable
  certificate that "this section is the same as the original," which
  is what makes rehearsal-style jumping sound rather than hopeful.

## What the machinery already provides (the credibility section)

Almost everything.  This is a *surface* redesign; the engine room was
built for it without knowing:

- **`CueAsk` is `hear`'s bind, reified** — the cue stream is already
  the free-monad interpreter this design needs, in Python and in
  crust, with the ask/answer wire tested end to end.  `draw` needs no
  cue at all (pure given seed and path).
- **The budgets, the frontier, "a question is not a stall"** — the
  operational answers stay word for word.
- **`sowScore`** becomes the path-and-seed annotator it mostly is,
  minus planting `Clip`s.
- **`resumeAt`** keeps its descent; the walk re-keys by path, and the
  arithmetic fast path survives on effect-free spans.
- **The bake, the parity suites, the CLAP cursor** — untouched for
  effect-free scores, which is exactly B2's jurisdiction.
- **`do`-notation** — shipped, tested, and waiting: the examples in
  this file parse today.

What does not survive: the old spellings.  `sown f` becomes
`do s <- draw; f s` *without* the box (a semantic change, not a
rename); `probe p k` becomes `do ks <- hear p; k ks` likewise;
`|/ n … |* n` around them simply comes off.  The pieces
(`nightdrive`, `moods`, `jazz`, `arpeggiator`, `ladder`) and the
fixtures migrate by that table, and old spellings should be refused
by name, the retirement rule.

## Acceptance tests, all on record

1. **The constant law** — replace `draw`/`hear` with `'` of a fixed
   value: identical events, identical ticks, only the thread differs.
2. **Homomorphism through joints** — `(a ++ b) >>= f` distributes
   when `a` contains a joint.
3. **Effect-free parity** — bake equals dynamic equals CLAP cursor,
   change for change (exists; must keep passing untouched).
4. **Improv equals replay** (exists; re-keyed by path).
5. **Rejoin by descent** — rebuild at minute fifteen rejoins in
   seconds by path (exists as ticks; re-keyed).
6. **The maze walk** — `seek "verse.3"` stands exactly where playing
   from the top stands, held against the thread.

## Open, and deliberately so

- The fermata question (may a joint wait?) — above, and the largest.
- `hear`'s port vocabulary: `holds.<bank>` today; knobs as ports
  (the `Chan -> Port` bridge) wants deciding here rather than bolted
  on later.
- Path spelling and the autolabel format (`verse.3/bar.2` is a
  sketch, not a decision).
- Whether `long` survives as a skip annotation or paths make it
  redundant.
- The plugin boundary: an exported ariadne piece under a DAW — the
  notes port answers `hear` (already true), the transport answers
  time; whether a fermata is expressible abroad at all.

*If this holds, the build order suggests itself: the constant law as
a failing test first, `draw` (pure, no machinery) second, `hear` on
the existing cue wire third, paths and the thread's re-keying fourth,
the old spellings' retirement last — each stage separately shippable
and separately honest.  But whether it holds is the present
question, and it is not mine to answer.*
