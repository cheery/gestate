# firstpiece.md — picking the language up, recorded

*An experience report, not a design.  Henri asked for an example
written by gestate's newest user — me, Claude, the assistant that had
spent the day inside the compiler but had never written a piece — and
for every friction hit along the way, written down.  The piece is
`examples/audio/undertow.ges`: two banks, a chancy score, a feedback
delay, a breathing filter, one knob.  This file is the diary.*

The method matters for reading it: I worked the way a person works.
I started at `doc/ref/index.md`, read the nearest examples, wrote the
piece, rendered it offline, and judged the result by numbers — peak,
RMS per stretch, zero-crossing rate — because I have no ears.  Every
verdict below says whether the thing helped *at the moment I needed
it*, which is the only test documentation can fail.

## What worked, and why

**The reference's front door answered my first two questions before I
asked them.**  `doc/ref/index.md` opens with two tables: which
libraries are in scope for which backend, and which declaration each
backend looks for.  Those are exactly a newcomer's first two
confusions — *why is this name undefined* and *why does the runner
not see my program* — and they are dispatched in the first screenful.

**One good specimen taught me more than the reference did.**
`test/sessions/F105-hello2.ges` — fifty lines, written by Henri in
anger — showed me the whole modern voice idiom at a glance: the
payload type, the `FromMIDI` instance, `sine (!pitchOf s) * adsr env
g * !velOf s`.  I wrote both of undertow's voices by imitating it and
neither needed a second draft.  A curated "smallest modern synth"
beside the courses would bottle this.

**`feedback`'s reference page is the model for what the prose should
do.**  It gives the `scan` analogy (`out[t] = f (out[t-n], s[t])`),
a one-line echo, and — before I could worry about it — the note that
`feedback (seconds 0.25)` folds to a constant.  My delay-length
question was answered in the past tense.  Pages that reach this bar
make the fragment's restrictions feel like physics instead of refusal.

**The score algebra is checkable by hand.**  Writing `barOf` I could
*prove* each case four beats wide by arithmetic — `1×4`, `2+2`,
`(1+1)×2` — and `long 4` says what the bar must add up to.  Chance
through `draw`/`below` took one reading of `moods.ges`.  Two seeds
rendered two different nights over the same bass floor, first try.

**The whole piece compiled and performed on the first render.**  A
hundred and twenty lines, two banks, `do` notation, a delay line, a
knob — zero errors, dynamic performer self-selected because of
`cycle`, and the offline `.wav` came out sounding like its own
comment.  That is not a small fact about a language this young.

## What cost me, each with the fix's shape

**The nearest example teaches the oldest idiom.**  `duet.ges` — the
obvious two-bank neighbour — hand-rolls its envelope as a five-stage
`case` chain and its pitch table from `8.1758`, because it predates
`adsr` and `keyHz`.  A newcomer imitating the nearest file writes
sixty lines where six now do; I only escaped because I had seen F105's
specimen the same day.  *Fix shape: modernize `duet.ges`'s voices, or
put one sentence at its head — "written before `adsr`; see X for the
short way".*

**`!` under uncertainty.**  I wanted the chime's second partial as
`sine (!(q => pitchOf q * 2.013) s)` and could not tell from the
manual whether a lambda is an atom `!` accepts.  I took the safe road
— a top-level `shineOf` — which reads fine, but the uncertainty is
the friction: I changed my program to avoid finding out.  *Fix shape:
one sentence and one example in the manual's `!` section stating the
lambda case, whichever way it is.*

**`below` is load-bearing and invisible.**  `moods.ges` uses it in
its one chancy line; it has no `#:` prose in `music.ges`, so the
reference has nothing to say about the standard way to turn a seed
into a bounded choice.  Three greps found it; `what below` in the
editor would have too, but the file a newcomer reads is the example,
and the example does not say.  *Fix shape: a doc comment on `below`,
and `draw`'s page mentioning it as the usual companion.*

**Offline knob semantics are folklore.**  My `depth = mkKnob 0.5` —
what does `audioperform -o` render it at?  The default, it turns out,
but I could not find that written anywhere, and an old note of my own
warned that *some* offline path sweeps controls with the sample
index.  I shipped the knob on faith and verified by the absence of an
explosion.  *Fix shape: one line in `audioperform`'s `--help` and in
the manual — "offline, a knob renders at its resting value".*

**Verification is mine to build every time.**  To trust the piece I
wrote a throwaway analyzer — peak, RMS per stretch, zero-crossings —
and iterated the mix against it (the first draft's chimes were
drowned; the numbers said so before any ear could).  Every author of
an example presumably rebuilds this same scaffold.  *Fix shape: an
`audioperform --report` printing peak and per-bar RMS after a render;
it is the ears a CI has, and it is most of the missing played-note
oracle from the roadmap's host-layer item.*

## The one-sentence verdict

The language kept every promise its specs make — the fragment never
surprised me, the score algebra did arithmetic I could check, and the
first render worked.  What friction there was came from the
*documentation gradient*: the newest, best idioms are the least
visible, and the oldest examples speak loudest.  A newcomer's hour is
spent not on the language but on discovering which decade of it to
imitate.
