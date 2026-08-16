# scorebox.md — the score box, read-only first

*B4's first slice (`roadmap.md` §"Content boxes"), specified before it
is built — the reverse of `spec/workbench.md` §"Content boxes", which
was written from the code.  This is deliberate too: the mechanism is
already standing, so what is left is decisions, and a decision written
down can be argued with before it hard-codes anything.*

**Built 2026-08-14, and the file was revised from the code afterward.**
`gestate/scorebox.py` is the box's mind, `music.ges` gained the two
walks it needs, and `test/test_scorebox.py` holds the acceptance below.
Four things the building taught are folded in where they belong, each
marked ***as built***; the rest of the file stood.

The principle is already on the wall: **a widget is a view over a span
of source**.  The first score box only *reads* — it renders the score
expression under it, and the one gesture it owns is a click that jumps
to source.  Everything a rewrite gesture will need — the take, the
provenance, the height, the focus — is exercised by the read-only box,
and a person using it will find what is wrong with these decisions
before any rewrite has been built on top of them.

## The ask

A `notes <expr>` line, with `canvas <expr>`'s manners exactly: one
line, `sink`'s undo, several at once, the blanked-door healing.
Nothing new is designed here; B2/B3 built it and this reuses it.

***As built***: the ask rewrites to a **comment**, not to a hidden
definition — the bare `canvas` line's manner rather than `canvas
<expr>`'s, and for a reason the design missed.  A `canvas <expr>`
names a picture *the program* must build, so the expression has to
reach the compiler; a `notes <expr>` names score the box reads out of
the author's own text for itself, and the compiler has no use for it.
The rewrite happens at `audiovoices._sinks`, the door every assembly
already passes.

(*`notes`, decided.  `roll` read best but collides with the chance
word `roll` in `music.ges` — an ask keyword is its own grammar so
nothing would break, but a newcomer greps.  `notes` collides with
nothing.*)

**The view grants height and the content fits** — the label precedent,
and the box already is the window's walk clipped to a band.  A piece
is longer than any box whatever rule is chosen, so clipping on the
tick axis is inherent; the box scrolls along it and an accordion that
grows under the hands would move the text being edited under the
cursor, which the latency work exists to prevent.

## The take

A chancy score has no notes, it has takes; a *seed* makes "one take"
well-defined, and the renderer, the plugin and the `seed`/`reroll`
commands already treat the seed as the name of a performance.  So:

- The box renders **the take the session's seed names** — the score
  sown with that seed, exactly as `audioperform --seed` would play it.
  The box's label carries the seed whenever the expression draws;
  a deterministic score shows no seed, because there is nothing to
  say.
- `reroll` re-renders the box along with everything else the seed
  names.  No new command; the vocabulary rule is satisfied by the
  vocabulary that exists.
- **A box on a sub-expression is its own take.**  Seeds split by
  position from the root (`spec/ariadne.md`), so `notes chimeBar`
  sown alone does not draw what the piece draws at bar 33.  Stated
  rather than hidden: a box on `score` shows the piece's take; a box
  on a part shows *a* take of that part.  When ariadne's paths land,
  a box that knows its position in the piece can show the piece's
  own take of it — that refinement waits for paths and blocks
  nothing here.

## The two kinds of ink

A note that traces to bytes in the file is **span ink**: it wears a
source span, a click on it jumps there, and the future rewrite
gestures apply to it.  A note that exists only in this take — it came
out of a `sown` or a `draw` — is **take ink**: it wears the span of
the *generator* that drew it, is drawn distinguishably (dimmer is
enough), and a click on it jumps to the generator's line.  The
read-only box makes this pure labeling; later it becomes the refusal
rule — a drag on take ink is asked to rewrite `below 4 s`, which is
programming, not a gesture, and is refused with a sentence naming the
generator's line.

## Provenance, by syntactic descent

Nothing threads spans through the engines, and nothing should: the
event tuple is the currency of two machines held in parity, and only
a picture wants spans.  The box's own walk carries them instead.

Every parsed node has a `Span` (`syntax/ast.py`), so the box descends
the viewed expression's **own source tree**:

- Nodes that are *literally* score syntax descend with their spans:
  `a ++ b` lays out `a`, then `b` shifted by `durOf a`; `a || b` lays
  both from the same tick; `|*` and `|/` scale; `long` clips; `'x` is
  a leaf wearing its own span; `e >>= voices.b` descends into `e` and
  reads the *bank* off the right-hand side — the bank is the note's
  hue, which is how two parts stay two colours in one box.
- Anything else — a call like `barOf s`, a name, a `sown`, a
  do-block with a `draw` in it — is **opaque**: the whole subterm is
  laid out by the ordinary machinery and every event it yields wears
  the subterm's span.  A `sown` is opaque by construction, which is
  what makes its notes take ink without any second mechanism.

***As built***, two things the descent had to learn:

- **A leaf is printed, not sliced.**  Cutting the text out between a
  span's ends looked obvious and is a trap: a `VPrefix` carries a
  defaulted span, so `'(H 60 100)` sliced from column zero and
  swallowed the file down to itself.  The formatter already turns a
  parsed node back into text and is idempotent, so what it prints
  re-parses to the same tree.  Spans are then used for one thing
  only — the *line* — and taken from the node's **atoms**, which are
  the parts whose positions survive fixity resolution.
- **An assigned part is un-assigned first.**  `voices.bass (Key k 96)`
  is a `[: Void :]`: the note went into the bank and there is no
  payload left to read.  Chopin gets away with a top-level `>>=
  voices.piano` the descent simply drops, but the modern idiom
  assigns *inside* the part (undertow's do-block, and two calls down
  for its chimes), and refusing that would be refusing the idiom the
  newest examples teach.  So the box generates an **unassigned twin**
  of every declaration that assigns, transitively — `voices.B e`
  becomes `' e`, the same music one step before it was committed —
  and reads the twin.  This is where a leaf's bank comes from when
  the drop above never saw one.

The finest span a note can wear is therefore the finest expression
*written in the text the box views* — which is also exactly where a
person would want to land.  Clicking a chord in bar five of chopin
jumps to `barOf (stroke 53 57 62)`, not into `quiet`'s body; the
descent never enters a function, so the answer is always a line of
the piece, never a line of its helpers.

Widths come from the same layouts (`durOf` is the algebra's own
word), so the descent needs no arithmetic of its own.

## What the box draws, and `Notable`

The walk yields `(onset, offset, bank, payload)` where the payload is
**a tuple of the author's own record's fields** — deliberately opaque,
"so nothing downstream has to know what either means"
(`audioscore.perform_voices`).  The shipped examples happen to write
their fields in `(key, velocity)` order, but that order is a
convention the type checker never sees, and a payload like
`Tone (toFloat v / 127.0) n` breaks it silently — the box would draw
levels as pitches.  So the box asks the program instead, through a
class declared beside `FromMIDI`:

    class Notable a where
        noteKey : a -> Int
        noteVel : a -> Int

`FromMIDI` is how a MIDI note becomes a payload; `Notable` is the
other road's half-inverse — not the note back, just what a reader
needs from it: where it sits and how hard it was struck.  Velocity is
in from the first day because adding a method later breaks every
instance already written, and it is the tune-versus-chords contrast a
roll wants anyway.  (`noteKey`/`noteVel` rather than the obvious
`pitchOf`/`velOf`, which the shipped pieces already define as their
own helpers — a class must not collide with the names its authors
were taught to write.)

The box evaluates the methods through the program's own instances, by
the road `gui.Substrate._force` already walks.  The library instances
its own bare note — `instance Notable Int`, the key itself and the 64
that `prog` assigns — so every MIDI-shaped piece draws unasked.  An
author's record costs two lines, and a payload with no instance is
refused with the canvas's manners: a sentence naming the type and the
class, never a wrong picture.

Key is the vertical axis, ticks the horizontal, bank the hue,
velocity the brightness; the roll is a fold into rects the way
`scoped.ges` folds its trace.

***As built***, the roll is a *generated substrate program* — the box
is handed to the window as a canvas like any other, so the payload
path, the walk and the band all carry it with nothing new to learn.
Three things that shaped the generated text, each found by it
failing: the notes travel as a **list** folded by a small recursion
(`scoped.ges`'s own shape), because one `Over` per note is one
parenthesis per note and chopin's hundred and forty overflowed the
parser; a coordinate left of centre is written `(0 - 192)`, because
there is no unary minus and `-192` reads as a section; and the
picture is `!(…)`, a constant signal, because the canvas entry is a
`Sig Sub` and a take does not move.

## The hazards, named now

- **The endless walk must carry a bound.**  A `cycle` is welcome — the
  box clips to a window and walks below it — but the sauna specimen's
  defeat (`long n (cycle <all-rests>)` never yields a first cue)
  would hang the *editor* here, not a render.  The box's walk gets a
  step budget, and a region that exhausts it draws as an unmeasured
  band with a complaint naming the line — the same manners as a
  canvas that will not compile.  The language-level fix (the clip
  bound pushed into the walk) heals this for good; the budget is the
  box not waiting for it.
- **Ticks are score time.**  The box draws in ticks and says nothing
  about seconds; tempo, fermatas and `hear` are the performer's
  business, and a picture that tried to draw wall time would need
  answers (`spec/ariadne.md`'s joints) that do not exist yet.

## Acceptance

Building this adds the two-line `Notable` instance to each piece named
below; a `voices` piece without one is the refusal case, also checked.
**All of this is `test/test_scorebox.py`**, fourteen tests.

- `notes score` in `chopin.ges` shows the ladder — three columns
  descending a rung a bar — readable enough to check against the
  comment that claims it.  *Held as: the opening stroke is 55/59/64
  at the `quiet` velocity with the tune's B over it, and the piece is
  eleven bars long.*
- `notes score` in `undertow.ges` shows the ground bass as span ink
  and the chimes as take ink, seed in the label; `reroll` tells a
  different night and the label says which.  *Held as: one seed twice
  is one picture, another seed moves the chimes and leaves the bass
  where it was.*
- Clicking any chord of chopin's bar five takes the caret to its
  `barOf` line; clicking an undertow chime takes it to the do-block
  that drew it.  *Held as: every leaf's line is a line that writes
  notes, the first chord's is its own `stroke 55 59 64`, and a press
  through the session moves the caret and writes nothing.*

  **The view does not travel with it** while the hand is still down
  (`spec/workbench.md` §"The window's own conduct"): the box would go
  out from under the finger that was pressing it, which is what
  happened for as long as this said JUMP_AIR.  The peep shows the
  place instead.  Strictly this holds because the press's `goto`
  reaches the window a frame or two after the press and the button is
  still down — true of every hand there is, and the day something
  clicks faster than a frame the fix is the model saying *mark* rather
  than *goto*, not a second rule in the window.
- The sauna specimen's silent chapter draws as an unmeasured band
  with its complaint, inside the budget, and the editor never hangs.
  *Held as two tests, because the specimen turned out to fail
  earlier and more usefully than expected: it has no `Notable`
  instance, so it is refused by name in seconds — the refusal case
  itself — and the fuel bound is held instead against a `cycle` of
  something zero beats wide, which says it was cut rather than
  hanging.*
