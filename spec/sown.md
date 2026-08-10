# The 1-beat rule — a root cause analysis of `sown`'s box

*Written 2026-08-10, as a five-whys chain asked for after the rule bit
twice (see the end).  Nothing here proposes a change; it records *why*
the restriction exists, level by level, so the next person who trips
on it can read the price and the purchase in one place.  Companion to
`spec/dynamicscore.md` §"Stage three, the surface", where the rule is
stated; this file is why it is stated.*

The question at the top: **why does `sown` restrict its internals to a
fixed length — content clipped to one beat, span controlled only from
outside by `|*` and `|/`?**

## Why 1 — why does `sown` clip its content to one beat?

Because it is an instance of stage three's stated invariant: **a
listening score bends content, never time.**  Every reactive leaf —
`sown` and `probe` share the shape — is an ordinary leaf of the layout
algebra: one beat unless `|*` and `|/` say otherwise, its extent
declared in the text, only its *content* decided late.  Content beyond
the declared span is clipped, and said so, in the drop rule's own
vocabulary: a section that outruns its box rejoins nothing.

## Why 2 — why must the extent be declared in the text rather than taken from what the decision produces?

Because `durOf` must stay total.  `Seq` places its right sibling at
the left sibling's `durOf`; if a `sown`'s length depended on its draw,
no position after it could be known without evaluating the draw.  For
`probe` it is worse than expensive — it is impossible in principle:
the content depends on a *reading* that does not exist until the
leaf's downbeat arrives.  A run-dependent width makes time a function
of the performance.

## Why 3 — why can time not be a function of the performance?

Because three load-bearing mechanisms all do arithmetic on written
widths, and each collapses if widths depend on decisions:

- **Resume skips by arithmetic.**  `resumeAt` never descends a `Clip`
  whose width lies behind the cut — that is the measured 157 s → 1–4 s
  rejoin, flat in elapsed time.  Run-dependent widths mean a resume
  must evaluate everything it skips: back to left-to-right forcing.
- **Seeds ride position.**  A draw is a pure function of seed and
  position in the tree — a draw at bar 33 is a descent's worth of
  splits, not a night's worth of generator steps.  If draws could move
  durations, position would depend on earlier draws, entangling the
  two; "one integer replays the whole night" stops being a theorem.
- **Bakeability.**  Because widths are fixed, the eager layout can
  evaluate `sown` exactly as the performer would, so `sown` does not
  force the dynamic path (`unfolding_names` must not flag it) and the
  parity clause extends: *a rolled score bakes and performs
  identically, given the seed.*  A variable-width `sown` would have to
  be refused by name the way `cycle` is.

## Why 4 — why is the system built so those three must hold, rather than logging everything and replaying the log?

Because of the honesty claim the whole audio half rests on — "the
graph is exactly what the source says" — which stage three bends
deliberately *only as far as the performance*: a performance must be a
pure function of `(score, arrivals, seed, beat)`, so the transcript
stays minimal (probes logged, draws never — they are derivable) and
replay is exact.  And because stage 10's lesson is written into stage
one: silent note defects live exactly where two implementations decide
when-a-note-happens, so *when* is decided once (`timed_events`,
`samples_of`) and every implementation — the bake, `Performer`,
`LazyPerformer`, the CLAP cursor — is held to it change for change.  A
timeline computed from written widths is the one spelling of time a
parity suite can hold.  It is also what keeps the Zeno guard a
*budget* rather than a semantics: a stalled decision produces absence,
never a shifted downbeat — "a hang is absence, never corruption" only
works if a hang cannot move time.

## Why 5 — why is the project committed to one verifiable spelling of time in the first place?

Because in this domain, being wrong is *silent*.  A wrong duration
does not crash — it plays, slightly off, unfalsifiably; stage 10's
defects were found by a person at a keyboard, not by tests, and the
roadmap names finding oracles as worth more than more care.  The whole
method — the rule, `spec/verification.md`, the goldens — is a response
to that: every claim gets an oracle, and any design that would make
its own oracle impossible is refused at the *design* level rather than
patched at the implementation level.  The 1-beat rule is that refusal
expressed at the leaf: the smallest declared-width box inside which a
decision may do anything it likes, because outside it nothing can
move.

## The root cause, in one sentence

The 1-beat rule is not an implementation limitation; it is the surface
form of the foundational commitment that **time is decided by the
text** — and its price and purchase are both known.  The price: N
draws need N sown leaves, because `++` inside one `sown` silently
clips to the first beat.  The purchase: `durOf` totality, seek by
arithmetic, seed–position purity, bakeability, and a transcript that
is just the world and the seed.

## The probe that sharpened it: a draw-dependent width under `>>=`

Asked the day this was written: what of
`sown (x => 'below 4 x) >>= (y => 'Note |* (y + 1))` — the draw is
boxed, but the *bind* hands its value to a score whose width depends
on it?  Checked empirically (bake, stream, and `resumeAt`, several
seeds): **the draw stretches the note's extent, never the timeline.**
Two such chunks in sequence start one declared beat apart whatever was
drawn; the bound note *sounds* `y + 1` beats while *occupying* one —
it rings past the barline the way a tied note does, and the way `at`
translates extent, not duration.  The box pins duration (what `Seq`
places by) and clips onsets past it; an extent is free to overhang
because nothing downstream reads it for placement.  Resumes into the
overhang keep the ringing note with every position unmoved.  So the
invariant survives the bind unweakened: what a decision may enlarge
is exactly what placement never reads.

## The observation that prompted writing this down

The price recurs.  The clip has now bitten a person (four beats of
content handed to a one-beat probe — the silent-horns evening) and a
model (a `++` inside `sown` in a test fixture, caught only on
re-reading), on separate days.  The clip *is* reported — clip-and-
report is the rule — but evidently not loudly enough where authors
look.  If a fix is ever wanted, the shape that keeps the rule and
removes the surprise is a compiler query in the `--holes` family, or
an editor gutter mark: *this leaf's content exceeds its box*.  Two
independent trippings are a caller, in the rule's sense, if one is
wanted.
