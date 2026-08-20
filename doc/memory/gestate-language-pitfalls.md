---
name: gestate-language-pitfalls
description: Gestate surface-language pitfalls hit while writing examples (one still open)
metadata: 
  node_type: memory
  type: project
  originSessionId: a1462242-2c42-465a-b030-147d44823d59
  modified: 2026-08-14T12:17:34.096Z
---

Pitfalls hit writing gestate examples (2026-08-09):

- **FIXED 2026-08-09** (spec/comments.md): trailing/interior comments
  used to parse as application ARGUMENTS (`x = 5 # c` was `VApp(5,
  VComment)`, constructor arity lies). Now: comments are never atoms;
  parser collects in-declaration comments as trivia on
  `VModule.comments` (source order, spans); formatter reattaches them;
  top-level comments stay items. `descend` must carry the `comments`
  field when rebuilding VModule — it silently dropped it once.
- FIXED 2026-08-09: `!` now binds ONE atom (parse._marks_head), so
  `!(f x)` = constant of computed value, `!f x` = lift, `!(f x) y` =
  lift of computed head. `constSig` is renderer-internal
  (internals.RENDERER_PRIVATE) — author programs must spell it `!x` /
  `!(f x)`; naming constSig raises InternalError. History in
  spec/exclamation.md.
- The audio fragment is first-order: no function-valued parameters, no
  lists at audio rate (use `case` tables), one record type per
  instantiation, `on <points>` needs the points literal at the call site.
- Multiple `voices` banks must share ONE payload type (record layout is
  per-tag; two records collide in codegen).
- Signal-level `let` and sequential non-rec `let` scoping were fixed
  2026-08-09 (desugar.py, gmachine.py, audiograph.py, audioextract.py) —
  verify these still exist before citing.
- `limit` overshoots badly on transients; use `brickwall` for a true
  ceiling in examples.
- The prelude has `not` and `||` (which is ALSO music overlay) but no
  boolean `&&` — spell conjunction with nested `case`.
- **The `voices` spelling (2026-08-10, Henri's correction)**: current
  syntax is the INLINE form `voices <bank> <count> <voicefn> : <frame>`
  (e.g. `voices lead 4 pluck : Sig Float`) — the payload type comes from
  the voice fn's own signature.  The two-line form (`voices lead 4 :
  Tone -> Sig Float` + `lead = pluck`) is LEGACY: it still parses
  (back-compat), which is how I picked it up from test_audioassigned's
  old fixture and spread it into three pieces.  Every shipped example
  uses the inline form; write that.  (The test fixtures still carry the
  old form — arguably as its only coverage; retiring the syntax is
  Henri's call.)
- **`sown` clips to ONE beat** (2026-08-10, test_sownscore
  "test_sown_content_is_clipped_to_its_beat": content bends, time
  doesn't).  `sown (s => fourBeatPhrase s) |* 4` plays only the
  phrase's FIRST beat stretched ×4.  The idiom for a multi-beat
  decision: shrink the content into the decision's beat, stretch the
  box back — `sown (s => block s |/ 16) |* 16` (nightdrive.ges does
  this; ticks stay integral down to |/32 at 96 ticks/beat).  Henri's
  moods.ges `bar` has the un-shrunk form and audibly plays one note
  per bar — reported 2026-08-10, his call to fix.  Parallel parts
  (`||`) can never share a draw (Seq/Par split the seed); shared
  decisions must be drawn once in one `sown` ABOVE the `||`.
- **FIXED 2026-08-10**: an authored type/constructor colliding with a
  library one (`Note := Note Int` vs `Score a := Note a`) used to break
  SILENTLY at run time (`unknown global '>>='` when the score forced —
  the Monad Score instance dispatched on the wrong Note). Now
  `shadow_libraries` renames shadowed library TYPES/CONSTRUCTORS too:
  `_type_names` collects VTypeDecl/VCtor/VTypeAlias names,
  `library_shadowed_con(name)` = `Library_<name>__` (case must survive —
  the tokenizer reads case as namespace, so `__library_X__` would stop
  being a CONID), token loop moves WORD and CONID. The `'x` sugar is
  safe because `(') x = pure x` (prelude) reaches Note only through the
  instance inside library text. Host cons-by-name reads (Step/Ramp) need
  no indirection: a program shadowing Step can't type a library tempo at
  all. STILL OPEN one layer down: prelude constructors (Just/Cons/True…)
  shadowed by a program — `merge`'s question, unhandled.

**`!x` lifts a value into `Sig`** (Henri, 2026-08-11). A numeric
*literal* lifts on its own, but a named `Float` does not — `every
pulseHz` where `pulseHz : Float` is a type error and `every (!pulseHz)`
is right. Prefer keeping the constant a `Float` and lifting at the use
site, so arithmetic on it (`!(pulseHz / 2)`) happens once at the value
level rather than every sample. `!` is the same operator that lifts a
pure *function*: `triangle (!freq note)`.

**`Sig Float` has no `Div`.** `sig / 2` fails with `No instance for Div
(Sig Float)`; multiply by `0.5`, or do the division on the `Float` side
before lifting.

**No `where` and no `let`.** Every helper is a top-level definition,
which is what a supercombinator language means in practice — factor the
subexpression out and name it instead.

**`string` takes plain `Float`s**, not signals, so Karplus-Strong cannot
take a per-note pitch from a voice. Check the prelude signature before
reaching for an oscillator in a `voices` body: several take `Float`
where the neighbouring ones take `Sig Float`.

**A `voices` bank is a sum.** Eight voices of something that peaks at 1
peaks at 8 when the score is dense; scale inside the voice body rather
than in the mix, or the limiter ends up doing the mixing.

**OPEN (found 2026-08-14): `long n (cycle <all-rests>)` diverges the
stream walk** — specimens/sauna_specimen.ges (AI-written for Henri's
friend; playing version examples/long/sauna.ges) stalled on it.
Negative examples live in specimens/ at repo root — never swept by
the suite; a fixed specimen graduates into a test (README there).  `liveTo Rest` yields only `CueEnd`; `spliceEnd`
*consumes* CueEnds, so `cycle` of an event-free cell is a cue stream
with no head; `Clip`'s `cueBelow w` waits forever for a first cue to
compare against `w`.  Both machines agree (crust runs the same compiled
music.ges), so it's the meaning, not an engine bug.  Amplifier:
`LazyPerformer.advance` has no boundary early-out, so a stalled stream
burns fresh fuel (200k steps) per control-channel read per block, and
the parked walk roots an ever-growing live set → GC crawl + GBs of RSS.
5-line repro: `score = (long 8 (cycle (r |* 4)) ++ '(Key 60 100)) >>=
voices.sub`.  Author workaround: spell silence `r |* 200`, never
`cycle` a rest bar.  Candidate fix: push the clip bound *into* the walk
(a bounded `liveTo` twin cutting Seq splices at the box edge; same for
`streamVoicesAt`/`takeBelowV` parity) — one library fix heals both
engines.  Related: [[gestate-verify-workflow]].
