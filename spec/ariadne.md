# Ariadne — the score's reactive surface, redesigned

*Written 2026-08-10 at Henri's request, to be shot at — "let me see
whether it holds."  Held, and **stages one to three are built the
same night**: `Draw` and `Hear` live in `music.ges` beside the old
surface (which is untouched until its retirement stage), the sower
eliminates every `Draw` in one arm, `Hear` reaches the performer as
the `CueAsk` it always secretly was — the crust twin listens with
zero new machinery — and `test/test_ariadne.py` holds the constant
law both ways: a constant draw is invisible to the bake at any seed,
a constant answer equals its own splice to the tick, and the same
written coda starts at three different ticks under three different
worlds, which is B7-restated, measured.  The take-entropy gap (§D4)
is closed: `do s <- draw; unfold s step` streams, replayable from
its seed.

**The retirement is done, and it taught the interpreter its final
shape.**  Live testing jammed the pygame bench on the first cut of
`hear` — a `placeCues` wrapper per answer piled onto the endless
tail, quadratic in questions asked — and the revision is the one this
spec should have started with: **self-terminated cue streams**.
Every stream ends with `CueEnd e`, the tick its subtree *actually*
reached, answers included; `Seq` is `spliceEnd` (continue where the
left really ended) and `durOf` appears nowhere in the live walk;
`Par` joins at the larger reported end, so the constant law holds
through overlays too; `Scale` and `Shrink` scale the end, which makes
a listener under `|/ 4` lawful.  All six pieces perform in fractions
of a second where they jammed.  `sown` and `probe` are gone —
constructors, boxes, and all — refused by name with the rewrite in
the message; `roll`/`chance` are sugar over `draw`; a draw's value is
the position's own seed (the SplitMix bit contract unchanged, so
takes replay across the retirement) with the continuation re-seeded
by the right split; and every piece and fixture in the tree speaks
the new surface.  **The thread is keyed by position now**: the sower stamps each
question with the seed of the place it stands (narrowed to a signed
slot, since the key travels through crust too), the cue carries it,
and `Transcript.reader_of` answers by it — so a rebuild mid-piece
lands on the answers the take actually gave, where arrival-order
keying handed it the take's opening ones.  Held by
`test_ariadne.py`, counter-proof included: the same rejoin answered
in arrival order drifts.

That work turned up one honest limit and then closed the bad half of
it.  **A joint of undeclared width cannot be skipped by arithmetic**:
`durOf` of an unanswered question is 0, so `Seq` has nothing to step
over.  Stepping over it anyway advanced nothing and fell *silent* —
so `resumeSeq` asks `opaqueHead` first and stops there instead: the
phrase **restarts at the joint**, audible and answered from the
thread by key, rather than the piece going quiet.  Declaring the
width is the cure and the idiom (`cycle (long 1 (do ks <- hear p;
…))`), which is why `long` turns out to be load-bearing rather than
optional.  `opaqueHead` terminates where the naive walk does not, and
for a reason worth stating: it descends into a right sibling only
when the left is measured-as-zero *and* not itself a question — a
chain of `mark`s, finite in any piece — and a `long` answers `False`
at once.

**A thread that runs dry is a fact, not just a silence** (Henri's
call, and the bug asking the question found): past the end of a take
— or in a bar it never reached — a question the log has no record of
plays as nothing, which is right, and the queue must *not* answer for
it, which it used to, serving stale readings from the take: a replay
inventing a world it never had.  The reader answers `None` there
rather than `[]`, the performer plays the silence and writes
`("dry", beat, port, key)` beside the stalls and the drops, and both
hosts say so — the CLI names the confessions where it once counted
events, the editor speaks them from its housekeeping loop under a
doubling rule (said once, then only when the count has doubled, so a
steady stall is mentioned rather than repeated).  An empty world and
a dry thread sound identical and read apart, which is the whole
point: *silence is what it plays; which silence is what it knows.*

Still ahead: the label half of paths (sections as bound payloads,
with `section` as the small arm the label lands on — the author's own
function receives the label, which is what reconciles the payload
spelling with a mechanism), shapes and `tempoShape`.  Every decision marked
**open** remains his.  Companions:
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
| 5. Clip/Mark duality | **replaced** — positions are paths (below); and `long` is now known to be *load-bearing* rather than optional: a declared width is what lets a resume skip a listening bar by arithmetic |
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

A position is a **path through the tree**, and — Henri's own
spelling, which is now the design — the sections that name it are not
a combinator but *payloads, bound in*:

    piece = ('"opening" ++ '"verse" ++ '"closing") >>= scoreParts

**This runs today and equals the piece written out, to the tick**
(measured 2026-08-10, string payloads through the plain algebra) —
which is the whole point: sections arise from `>>=` exactly as
instruments do, so the labeling construct is the algebra itself and
the constructor tax on `Section` is zero.  A first draft of this file
proposed `section : String -> [: a :] -> [: a :]`; that was
constructor-thinking surviving into the redesign, and the label-bind
spelling replaces it (a wrapper can return as sugar if wanted — it
would desugar to `'"name" >>= (_ => body)`-shaped provenance, not to
a node).

The path, then, is **bind provenance**: a position is named by the
labels of the binds above it plus the structural turns between them —
`verse/3/2` for the second bar of the third cycle turn bound from
`"verse"`.  The precedent is stage 5's proudest fact: graph nodes
carry origin paths and live migration works *because* identity is
structural; ariadne applies the same discipline to score positions.
**Open (mechanics):** how the interpreter records which label a
subtree was bound from — an annotation the walk threads, or a
provenance the sower stamps; either is invisible to the algebra.
Three properties paths have that ticks do not:

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

## Envelopes in the score, connected to channels

The second half of the proposal (Henri, same evening): tempo
envelopes, and envelopes in general, have always lived *outside* the
score — `bpm`/`tempo` as global declarations, dynamics as knob
automation a DAW owns, `Envelope` as signal-land machinery read
against `elapsed`.  A crescendo across a verse is a musical fact and
the score cannot say it.  `spec/dynamicscore.md` anticipated the
shape in one line — *"the tree holds the time, the envelopes hold its
shape"* — and ariadne gives it the algebra-lawful form:

    shape : Chan Float -> Env -> [: a :] -> [: a :]

    verse = shape swellChan (env [(0.0, 0.2), (1.0, 0.9)]) versePattern

An annotation over a subtree: across the subtree's own extent, the
named channel follows the envelope, its breakpoints given in
**fractions of the span** so the shape is the subtree's the way a
slur is a phrase's.  The laws come from the law:

- **it scales**: `shape c e s |* 2` stretches the envelope with the
  span — fractions make this definitional;
- **it reverses**: `reverse (shape c e s)` plays the shape backwards
  over the reversed content;
- **it commutes with bind**: `shape c e s >>= f` shapes the
  substituted content — the annotation rides the subtree, touching no
  event, so the homomorphism is undisturbed;
- **route a constant through it**: an envelope that is one flat value
  is a channel set once — indistinguishable from today's knob write.

**Delivery is a solved problem wearing a new name.**  The host clock
already drives `beat` sample-smooth from block-rate updates by
sending a *line* — `(base, slope, anchor)` — that the graph evaluates
at `ticks`.  A score envelope is that pattern generalized: the
performer delivers one line segment per breakpoint interval, at block
boundaries, through the channel machinery that exists; the synth
reads the channel as it reads any knob, sample-smooth for free.  No
new engine capability, no new wire — the beat channels were the
prototype all along.

**Tempo is the same construct pointed at the clock**:

    rit : [: a :] -> [: a :]
    rit s = tempoShape (env [(0.0, 1.0), (1.0, 0.5)]) s

a local reparameterization of the span's own time — a ritardando
written where it happens, not in a global declaration.  This opens
the A6 door deliberately: the one beats→samples conversion becomes a
*composition* of per-span maps along the path, which stays a single
owned spelling (the composition is associative and written in the
tree) but is real new arithmetic in `samples_of`, the cursor, and the
descriptor.  **Open (Henri's):** whether `tempoShape` under `||`
means polytempo — two branches walking their own clocks between
joins — or is refused there in v1; polytempo is the honest end of
this road and the most expensive register renegotiation on the page.

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
7. **The label-bind sentence** —
   `('"opening" ++ '"verse" ++ '"closing") >>= scoreParts` equals the
   piece written out, to the tick.  Already passing on the plain
   algebra (measured 2026-08-10); ariadne must keep it passing with
   joints and shapes inside the parts.
8. **The shape laws** — a `shape` scales with `|*`, reverses with
   `reverse`, commutes with `>>=`, and a constant envelope is a knob
   write.

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
