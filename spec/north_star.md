# north_star.md — the score box writes back

*B4's editing half (`roadmap.md` §"Content boxes"), specified before it
is built, the way `spec/scorebox.md` was.  The mechanism is standing —
the box draws, the provenance is carried, the press already jumps — so
what is left is decisions, and a decision written down can be argued
with before it hard-codes anything.  The three that were open are
answered here, in §"What is decided"; everything else is the contract
that follows from them.*

**The star, in one sentence:** a score object that reads the source
text and, when a hand moves it, writes it back.

**And the first slice, in one sentence:** a **vertical drag on span
ink, one note, byte-exact.**

---

## What is in the way

**No gesture in this editor writes text.**  That is the size of the
work, and it is easy to miss because the editor looks full of widgets.
The margin knob keeps a *channel* and deliberately so
(`spec/workbench.md`: *"the control-rate knob keeps its channel, and
every other widget goes through the text… a knob turned while a chord
rings must not recompile the graph under it"*).  The score box's one
gesture is a press that moves the caret.  So this slice builds the
**first gesture→text path in the project**, and whatever it does
becomes the precedent for every widget after it.

## The rule, and how it is extended

`spec/editor.md` states the law and it is load-bearing:

> **A widget is a view over a span of source.  Dragging it is a text
> edit.  There is nothing else.**
>
> **Widgets attach to declarations whose body is one literal, or one
> constructor of literals.  Everything else is text.**

`'(Key 60 100) ++ '(Key 64 100)` is neither, so the rule as written
refuses a score box.  It is extended rather than excepted, and the
extension is chosen to keep the *reason* the rule exists.  That reason
is stated in the same file: *"the moment a widget edits `220.0 + 2600.0
* env`, it must own an interpretation of the arithmetic, and the second
model is back with its drift."*  What is forbidden is a widget with a
**private interpretation** of source.

So:

> **A widget may edit a literal that something other than itself can
> point at.**

For the knob, the pointer is *the declaration's body* — the original
rule, unchanged, and it remains the whole rule for any widget with
nothing better.  For the score box, the pointer is **the descent**
(`spec/scorebox.md` §"Provenance, by syntactic descent"), which is not
the widget's private reading of the text: it is the same walk that drew
the picture, it is tested, it already refuses what it cannot descend
(opaque leaves lay out whole) and already labels what the file did not
write (take ink).  A gesture edits only what the descent pointed at,
and nothing else in the file moves.

The invariant that keeps this checkable, and it is worth stating as a
rule of its own:

> **A tier-one edit replaces one atom's byte range with a literal of
> the same kind.  No reflow, no reprint, no reparse-and-print.**

Everything that cannot be said that way is tier two, below, and is not
built yet.

## What is decided

**Tier one now, tier two later and gated.**

| tier | what | status |
|---|---|---|
| 1 | a literal in place — one atom's bytes | **this slice** |
| 2 | structural — split a `++`, insert a rest, move in time | later, and only where `fmt(decl) == decl` |
| 3 | refused — take ink, and the list in §"Refusals" | settled |

Tier two is gated on the declaration already being formatter-clean, so
a reprint can never destroy hand-formatting somebody chose.  That turns
*"is every musical gesture a span rewrite?"* from a question of
philosophy into a **per-declaration predicate the box can answer before
it offers the handle** — a gesture that cannot be written back is a
handle that is not drawn.

**Pointer-only.  There is no third focus.**  Text and the piano own the
keyboard; a box does not.  Every gesture stays a `touched`, which is
already the one canvas gesture a transcript can hold and replay with
slides coalesced (`session.touched`), and the vocabulary rule
(`spec/workbench.md`: a capability that is not in `command.ges` does
not exist) is satisfied by naming the **gesture** as a command.  The
first gesture that genuinely wants typing — entering a pitch as a
number rather than dragging to it — is the thing that should force the
keyboard question, and until then it costs nothing to leave unanswered.

**Vertical first.**  A vertical drag is one atom: transposition.
Horizontal movement is tier two wearing a costume — moving a note in
time means reordering a `++` or introducing a rest, which changes the
shape of the expression.

## The gesture

- **Press** on a note: unchanged, it jumps the caret to where the note
  is written (`spec/scorebox.md`).  A press that becomes a drag is a
  drag; a press that does not is a jump.
- **Drag vertically**: the note follows the hand in *semitones*,
  snapped, using the roll's own `y_of` — the same function that drew
  it, inverted, so the picture and the arithmetic cannot disagree.
- **Release** commits: one text edit, one undo entry, one rebuild.
  Nothing is written while the hand is moving.
- **Undo** is text undo, because the moment a widget keeps its own
  history the second model is back.

**What the commit does with the file** is the same answer `audition`
already gives: the drag rewrites the *buffer* and auditions, so the
sound follows the hand and the file on disk is untouched until
`Ctrl-S`.  A gesture that saved would make an experiment permanent; a
gesture that only edited the buffer would be silent until you saved,
which is the opposite of the room this editor is.

## What it edits, and how the atom is found

Today a leaf carries `Leaf(line, bank, chancy)` — a **line**, not a
span, because slicing by span was a trap (`spec/scorebox.md`
§"Hazards": a `VPrefix` carries a defaulted span, so `'(H 60 100)`
sliced from column zero and swallowed the file).  The line is taken
from *atoms*, which are the parts whose positions survive fixity
resolution.

That same fact is what makes this slice small: **the atom is where the
position is honest.**  `_leaf` has the parsed node in hand when it
builds a `Leaf`, and a pitch written down is a `VNum` with a real span.
So the leaf gains the atoms it names — each one's line, column, length
and value — taken from atoms for exactly the reason the line already
is.

**Which atom is the note's pitch was the interesting question, and it
was answered by measuring rather than by deciding.**  The obvious rule
— *the first number inside `'(Con …)`* — was written here first, and
then run against the tree:

| file | leaves whose text is `'(Con <num> …)` |
|---|---|
| `duet.ges` | 16 of 16 |
| `noted.ges` | 0 of 10 |
| `minute.ges` | 0 of 23 |
| `chopin.ges` | 0 of 28 |
| `polysaw.ges` | 0 of 4 |

Four files in five, refused.  And looking at what they say instead —
`low 38`, `holdBar 45`, `chord 45 60 64 67`, `barOf (stroke 55 59 64
…)` — the pitch is *right there* as a literal; it is an argument to the
author's own helper rather than a field of a library constructor, which
is the idiom every real piece here uses.  A rule that refused it would
be a rule about `music.ges`'s spelling, not about the file.

So the rule is:

> **The atom is the one numeric literal in the leaf's own text whose
> value is the note's key — when there is exactly one.**

The box already knows the key: it is in the event the walk produced.
Nothing is inferred about the surrounding expression, which keeps the
extension above intact — the descent points at the leaf, the event
names the number, and the two have to agree or nothing happens.  It is
also self-refusing in the cases that should refuse: `'(Key 60 60)` has
two atoms equal to 60 and is ambiguous, a doubled note in a chord is
ambiguous, and a pitch that is not written in the leaf at all has no
match.

Measured with that rule, per drawn note:

| file | draggable | ambiguous | no atom |
|---|---|---|---|
| `chopin.ges` | 140 of 140 (100%) | 0 | 0 |
| `minute.ges` | 174 of 211 (82%) | 0 | 37 |
| `noted.ges` | 16 of 23 (69%) | 0 | 7 |
| `undertow.ges` | 0 of 366 | 0 | 366 |

`noted.ges`'s seven are the dice's, which are take ink and refused
anyway.  `undertow.ges` is the honest zero and worth reading rather
than fixing: 110 of its notes are a `draw`, and the rest are `cycle
groundBar >>= (k => voicesBass (Key k 96))` — the pitch is a *bound
variable*, and the numbers it takes are written one definition away, in
`groundBar`.  Following a binder to the list it draws from is a real
extension and is not this slice; the box says "written elsewhere" and
declines.

## The hands — settled, and not the way this page guessed

The vocabulary needed nothing new: `gui.ges` has had `TouchY` beside
`TouchX` since the substrate was written, and both painters know it
(`gui.py`, `panel/src/list.rs`).

What was open was the shape of the hand, and it wanted contact rather
than argument.  The constraint stands: `TouchY c s` writes a fraction
of **the element's own box**, a note's box is `max(8, y1 - y0)` pixels
tall, and a roll spanning two octaves gives about four pixels to a
semitone — so a note-sized handle saturates before it has said
anything.  A drag must have room to express an interval, so a hand is
the full height of the roll.

**Full-height regions that overlap hide each other**, and that is what
decided it.  The substrate resolves a press to the innermost region
written first, so of two overlapping hands only one can ever be
pressed.  The leading candidate here — one column per *written place*
— was measured against the tree before it was built:

| file | written places | pairs sounding at once |
|---|---|---|
| `minute.ges` | 4 | 0 |
| `noted.ges` | 4 | 0 |
| `chopin.ges` | 28 | **17** |

Seventeen of chopin's twenty-eight would have been unreachable at any
height, while the two files anybody would have tested it on have no
overlap at all — a defect that passes every test and fails on the
piece you care about.

So the hands **tile the picture**: `scorebox.hands_of` cuts the roll
into equal columns, one hand each, full height, `TouchY`.  No two
overlap, so every note is under exactly one hand wherever it sounds,
and a long note can be taken hold of anywhere along its length rather
than only where it starts.  Bounded by `MAX_HANDS` for the reason the
leaves are bounded: the hands are nested `Over`s, and chopin's hundred
and forty overflowed the parser the day the *notes* were nested.

**Which note a gesture means is read off the height** —
`scorebox.note_under`, the nearest note sounding under that column.
That is aiming, in both directions at once, and it made the press
*more* precise than it was: a chord used to be one region that jumped
to its own line however you aimed at it, and its notes are now four
places to press.

**And the drag is relative.**  A column is the whole height of the
roll, so a press lands at some pitch and rarely the note's own; carried
absolutely, letting go without moving would transpose the note to
wherever you happened to grab it, and a press that does not become a
drag has to stay a jump.  So the note moves by the interval the *hand*
has travelled, from the pitch it took hold at.  `key_at` is `y_of`
inverted, out of `scale_of`, which the picture is drawn from — one
arithmetic, two readers, the law the panel box already keeps.

## Refusals, each with a sentence

A gesture that cannot be honest is refused *by name*, never guessed:

- **Take ink** — a note the dice drew.  Refused with the generator's
  line, because the edit it would ask for is `below 4 s`, and that is
  programming rather than a gesture (`spec/scorebox.md`, already
  decided).
- **A pitch that is not a literal** — `chord a b c d`, a variable, an
  expression.  The note draws and jumps; it does not drag.
- **A collapsed leaf** — past `MAX_LEAVES` the box folds the tail into
  one region, which still jumps somewhere true but no longer names one
  note.
- **A note written once and played many times** — `|*`, a `cycle`, a
  part used twice.  This one is *not* refused, it is **said**: the
  bytes are one atom, so moving it moves every voicing of it.  A box
  that let you move "this one" would be lying about the file.  The
  status line says how many the drag will move before it moves them.

## The vocabulary

`transpose` is a command in `command.ges`, so it appears in the list,
carries its own documentation, and a drag *records in the transcript as
a command* — which is how nearly every editor defect in this project
has actually been pinned.  A gesture with no command behind it is a
capability that does not exist.  It is the shape `set` already has for
the knob: the window says `turn`, the session runs `set`, and what the
recording holds is the command.

**It names the region, the key as written, and the key it becomes.**

```
transpose : Text -> Int -> Int -> Command
```

The first draft of this line said *"the touch channel and a number of
steps"*, and building it found that a channel is not enough to name a
note.  A region is a **leaf** — one written place — and a leaf can
sound several notes: `chord 45 60 64 67` is one region and four of
them.  So the note is named by what it *says*, which is the one thing
about it the file and the picture already agree on, and a leaf with two
notes at one pitch refuses for the same reason `pitch_atom` does.

Naming both keys rather than a step is what makes the recording
self-contained, which is the property the whole transcript rests on: a
step that said `+3` would mean a different note on the second reading,
and a replay is the one reader that cannot ask.

## Acceptance

The first four are the slice; the fifth is what today's oracles make
possible and is the one that matters.

1. **Byte-exact.**  Drag a note up a third and the file differs by
   exactly one atom's bytes — asserted as a diff of the whole text, not
   of the parsed tree, because "no reflow" is the promise.
2. **The picture follows.**  The box redraws with the note where it was
   dropped, at the same leaf, with the same ink.
3. **Undo is text undo.**  One `Ctrl-Z` puts back the byte and the
   picture together, because there is only one history.
4. **Refusals are sentences.**  Take ink, a non-literal pitch and a
   collapsed leaf each say why, and none of them writes.
5. **The sound moved with it.**  Drag a note up a third and
   `heard_note` hears a third higher (`test_playedsound.py`).  The
   gesture, the text, the picture and the sound, checked as one thing —
   which is the whole claim this editor makes.

## What waits behind this

Tier two, gated as above.  Typing a pitch, which is what will force the
keyboard question.  Horizontal movement, which is tier two.  And the
refinement `spec/scorebox.md` already parked: when ariadne's paths
land, a box that knows its position in the piece can show — and then
edit — the piece's own take of it.
