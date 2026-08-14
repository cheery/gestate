# scorebox.md — the score box, read-only first

*B4's first slice (`roadmap.md` §"Content boxes"), specified before it
is built — the reverse of `spec/workbench.md` §"Content boxes", which
was written from the code.  This is deliberate too: the mechanism is
already standing, so what is left is decisions, and a decision written
down can be argued with before it hard-codes anything.*

The principle is already on the wall: **a widget is a view over a span
of source**.  The first score box only *reads* — it renders the score
expression under it, and the one gesture it owns is a click that jumps
to source.  Everything a rewrite gesture will need — the take, the
provenance, the height, the focus — is exercised by the read-only box,
and a person using it will find what is wrong with these decisions
before any rewrite has been built on top of them.

## The ask

A `notes <expr>` line, with `canvas <expr>`'s manners exactly: one
line, `sink`'s undo, rewritten to a hidden `__notes_<k>__` definition
in reading order, several at once, the blanked-door healing.  Nothing
new is designed here; B2/B3 built it and this reuses it.

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

- `notes score` in `chopin.ges` shows the ladder — three columns
  descending a rung a bar — readable enough to check against the
  comment that claims it.
- `notes score` in `undertow.ges` shows the ground bass as span ink
  and the chimes as take ink, seed in the label; `reroll` tells a
  different night and the label says which.
- Clicking any chord of chopin's bar five reveals its `barOf` line
  (JUMP_AIR); clicking an undertow chime reveals the do-block that
  drew it.
- The sauna specimen's silent chapter draws as an unmeasured band
  with its complaint, inside the budget, and the editor never hangs.
