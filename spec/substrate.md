# substrate.md — a canvas behind the editor, written in gestate

Companion to `spec/liveaudio.md`, which says how a synth is compiled and
edited while it sounds.  This says what is *behind* the editor: a canvas
the same program draws on and reads from, in one window, on the other tab.

The whole of it rests on one claim, and it is the same one the audio half
rests on:

> **A substrate is a value, built from smaller ones by ordinary functions.**

    substrate : Sig Sub

One declaration at the top, the way a synth is one `sound` and a GUI
program is one `scene`.  Not a registry: nothing is visible because of the
type its declaration happens to have, and nothing is discovered by walking
the program.  What connects a thing to the canvas is that some expression
put it there, and that expression is in the file where you can read it.

An earlier draft of this document said the opposite — *a declaration whose
type is `Sub a` is a visible object*, found by walking the compiled program
the way `audiospans` finds knobs.  It is recorded in §"Three readings set
aside" with the argument that killed it, which is short: it could not say
where a dragged object's position lives.

---

## Why one window

Two windows is two focus rings, two places for the keyboard to go, and a
running instrument whose picture is somewhere else.  The proposal is a
tabbed view — the editor on one tab, the substrate behind it, `Esc` between
them — in `pygame`, because the substrate is drawing and `tkinter` is not
for drawing.

**The rewrite is a view, not a rewrite.**  `audioeditor.Workbench` imports
no toolkit: it owns the instrument, the rebuild thread, the knob values,
the transport and the keyboard, and it has its own headless tests.
`Editor` is a thin `tkinter` view over it.  A `pygame` view is a second
view against the same object, and the two can exist at once while one grows
up.  This is the reason to do it now rather than later: the seam is already
there and was put there for this.

**Text editing is not the obstacle it looks like.**  `balanced.py` has a
rope with `insert`, `erase`, `row` and `rowpos` — a document interface, in
Python, already written and already tested.  What `tkinter` was giving away
for free is a text widget; what it was charging for is everything else, and
`journal.md` records that a *timeline* — scrubbing, dragging loop
points, widgets between lines rather than beside them — is the thing tk
cannot do.

---

## What a `Sub` is

**A picture that varies, that you can touch.**  `Sig Sub`, and the `Sub` is
not parameterised — which is the first thing to explain, because the
obvious design gives it a parameter and the obvious design is wrong.

### The value is not in the type

`over : Sub a -> Sub b -> Sub ?` has no good answer.  Every attempt to give
it one — a semigroup on `a`, a tuple, a record of named channels — is worse
than the question, and the question is the wrong one.  On the audio side
nobody asks what the *value* of two summed oscillators is; they ask for the
sum, and a knob is a **leaf** of the signal algebra rather than a change to
it.

The resolution is that a value never has to travel through composition,
because the program has already named it:

    #: What you drag.  An ordinary fold over the pointer.
    cutoff : Sig Float
    cutoff = 0.5 ::: mkSig (wait pointerY)

    #: What it looks like.
    cutoffElem : Sig Sub
    cutoffElem = sub cutoff (fader (at 20 40) (size 12 120))

    #: What it does.  The synth reads the same signal the canvas draws.
    sound : Sig Float
    sound = lowpassSvf (!scaleHz cutoff) 0.2 osc

One fold, two readers.  **That is the whole feature** — a thing you can see
and a thing you can hear that are the same value — and it needs the value
to be a name rather than a type parameter.

### Attachment: the channel goes *in*

An element is bound to what it feeds by an ordinary combinator, and what it
feeds is a **channel the program declared**:

    cutoff : Chan Float
    cutoff = chan

    fader : Sig Sub
    fader = onTouchY cutoff (rect 40 200 grey)

    #: What the program reads back.  `:::` is hold; `wait` is the event.
    level : Sig Float
    level = 0.5 ::: mkSig (wait cutoff)

*(This example was written as `onDrag dragged (still …)` over a
`Chan Point`, and the built vocabulary is the one above — `onTouchX` and
`onTouchY`, each over a `Chan Float`.  Three things changed and each is
recorded where it was decided: `still` went with `Scene` (S2 below), a
`Point` became **one channel per axis** because a fader is one parameter
and a pad is honestly two (S3, and `gui.ges` beside the combinators), and
a raw position became a **fraction of the element's own extent** so that
motion is constrained by construction and the number means something
without knowing the size.  The mechanism the paragraphs below describe is
unchanged: the channel travels inside the structure.)*

**The channel travels as a value, inside the structure.**  That is the
whole mechanism and it exists today: a `Chan a` is first-class, it may sit
in a constructor field, and `case` reads it back out — checked, with the
host writing to it and the picture moving.  At run time it is an
`NChan(chan_id)`, so a host walking the tree to draw it finds the id it
needs to `react` on, in its hand, at the node that named it.

This is why **the naming problem does not exist** rather than being solved.
`gui.ges` has one `Event` channel because "channel identifiers are handed
out in allocation order, so several channels would be positional and
fragile" (`fixme.md` F90, F91) — a statement about referring to a channel
by *position* or by *name*.  Nobody does either here.  The program hands
the element the channel itself.

It is also why there is no `Sub a`.  An earlier draft had `sub : Sig a ->
Element -> Sub` and worried whether that argument should be a `Sig` or an
`ExL`, since the language has both and `ExL` *is* an event.  The question
was upstream of both: a `Chan a` is the **source** they are each derived
from — `x ::: mkSig (wait c)` for a behaviour, `wait c` for an event — so
the element takes the source and the program reads it whichever way it
wants.  One type at the leaf, both readings at the use.

### Composition, and why it stays first-order

    onTouchX : Chan Float -> Sub -> Sub
    onTouchY : Chan Float -> Sub -> Sub
    over     : Sub -> Sub -> Sub
    moveXY   : Int -> Int -> Sub -> Sub

*(As drafted this listed `still : Scene -> Sub` and a `Chan Point` pair,
`onPress`/`onDrag`.  `still` went with `Scene`; the pair became one
combinator per axis over a `Chan Float`; and press is not in the built
vocabulary at all — see §"Open questions" 1, which is about exactly this
and is still open.)*

Ordinary functions, lifted over time with `!` — `!over a b`,
`!moveXY x y a` — which is Fran's `lift2 over`, and is why today's `!` was
worth having before this was written.

(Written as the design was, before building it.  The lift turned out to
belong *in* these definitions rather than at each of their uses, so the
signatures above are the `…Sub` ones today and the plain names are their
lifts — see S2 below.  Nothing else about the design changed: the lift is
still written and still one character, and it is still `zipSig`.)

**`Sub` is data, not a function, and that is what keeps hit-testing
simple.**  The host walks the tree to draw it, accumulating the transform
as it descends; when it reaches an attachment it knows the region that
attachment ended up occupying and the inverse transform back.  A press
lands, the host finds the deepest attachment containing it, maps the point
into local coordinates, and writes the channel.  `moveXY` moves the picture
*and* the hit region, because both are read off the same walk.

An earlier draft made an element a signal function — `Sig Point -> ExL
Click -> Sig Scene` — so that a combinator could transform events going
*in* as it transformed shapes coming *out*.  That is the right answer when
an element is opaque to the host.  It is not opaque: it is a value the host
built and can read.  §"Three readings set aside" keeps the argument.

**Passive elements are the easy half.**  A meter, a plot, a grid, a label:
`still` over a `Scene` the program already computes, with nothing attached.
A decoration costs no interaction machinery.

### What it is *not*

**Not a widget toolkit.**  `Shape` is `Rect` and `Dot` and will stay small
until a program wants more, the way `signal.ges` was extracted at the third
combinator rather than designed at the first.  Two elements — a fader and
an XY pad — should be written before the combinator set is fixed.

**Not a patcher.**  Objects do not connect to each other on the canvas.
What connects them is the program text: `cutoff` appearing in a filter's
argument is the wire, and it is one you can read.

---

## How it reaches the sound

**It needs nothing from the engine**, and that is the point of specifying
it this way.

The signal a `sub` is bound to is an ordinary one, and a synth that reads
it reads it the way it reads a knob: through a **control channel**.  The
host writes one slot per block; the graph reads it once per block and holds
it across the samples in between.  `audiollvm.pack_control` already does
this, `audiolive` already calls it once per block, and the fragment already
admits as many control channels as a program declares (`journal.md`, "four files, and
the knob limit they turned up").  A substrate element is a knob with a face, and
the machinery underneath is the machinery that is there.

Which settles the rate question before it is asked.  The substrate is
**interpreted**, at frame rate: it runs on the G-machine, the way
`examples/gui/bounce.ges` runs now.  The synth is **compiled**, at sample
rate.  They meet at the block boundary, where the host already stands, and
the substrate never has anything audio-rate in it.  A `Sub` that wanted to
compute per sample would be asking to be a synth, and the answer is to
write it as one.

Three consequences worth stating:

- **What a synth reads is a control value** — `Int` or `Float` — for the
  reason a bank's payload fields are: a control value is one slot of the
  buffer the host fills.  An element may hold whatever state it likes; the
  *signal a synth reads off it* is one number.
- **State survives an edit by name.**  A knob's value does
  (`audioeditor.Workbench`: "parameters are keyed by name, not by node
  id"), and an element's fold is an ordinary signal, so stage 5's
  migration already covers it — the thing the substrate keeps across a
  `Ctrl-S` is the thing the graph keeps.  Rename it and it resets, which
  is the same bargain every knob makes.
- **A synth need not read anything at all.**  A substrate that only *shows*
  is a legitimate program: `still` over a meter driven by the engine's own
  state is S5, and nothing above it depends on that direction existing.

---

## The assembly problem — settled

This was the one piece of real work that had to happen first, and nothing
else in this document was blocked on anything.

`audio.py` assembled `signal.ges + audio.ges + synth.ges + source`.
`gui.py` assembled `signal.ges + gui.ges + source`.  **Both `audio.ges` and
`gui.ges` declare constructors**, and a constructor's tag is its position,
which is exactly why neither is in the core prelude.  A program that has
both a `sound` and a `scene` needs *one* assembly with *one* numbering.

`audio.preludes(source)` is that one place, and both backends ask it.
`gui.ges` goes in *front* of the audio vocabulary: nothing in it names
anything in `audio.ges`, and putting it first leaves the audio vocabulary's
own order — `audio.ges` then `synth.ges` — untouched, which is what keeps
a synth's graph identical whether or not the file also draws.
`signal.ges` sits in front of both and has one constructor of its own now
(`Both`, for `!`), so its position is already fixed rather than free.

Nothing about the fragment changes.  A `scene` is not in it and never was;
it is interpreted, like a `score` is laid out rather than compiled.

---

## Stages

Each is a thing that works when it is done, in the order that keeps the
next one honest.

**S1 — one assembly.**  **Done.**  `sound` and `scene` in one file, one
constructor numbering, no canvas yet.

`audio.preludes(source)` is the one place that decides, and it answers
three cases: a `sound` alone gets what it always had, a `scene` alone gets
what it always had, and a file with both gets `gui.ges` in front of the
audio vocabulary.  Conditional, so a synth that draws nothing carries none
of it.  `gui.py` asks the same function rather than assuming, and a drawing
program that also sounds is told the sample rate its synth plays at —
`audio.ges` and `synth.ges` are written in terms of `sampleRate`, and every
definition in a file has to type-check to compile any of it.

`test/test_substrate.py` holds the invariant: **adding a `scene` to a synth
changes no samples** — and no node count, and no *origins*, which is the
one that matters for stage 5, since a graph whose samples matched but whose
origins had moved would reset every oscillator the first time a canvas was
added to a file.

**S2 — `Sub`, composed and drawn.**  **Done.**

`Sub := Still Scene | Over Sub Sub | Shift Int Int Sub` in `gui.ges`, with
`still`, `over`, `moveXY` and `blank` as the functions anyone writes.
`Shift` rather than `Move` because `Event` already has a `Move` — the
pointer's — and a constructor's name is the whole program's.

Each of them comes twice, and **the plain name is the one over signals**:

    stillSub : Scene -> Sub          still  : Sig Scene -> Sig Sub
    overSub  : Sub -> Sub -> Sub     over   : Sig Sub -> Sig Sub -> Sig Sub
    moveXYSub: Int -> Int -> Sub -> Sub
                                     moveXY : Sig Int -> Sig Int
                                                       -> Sig Sub -> Sig Sub

A substrate that never changes is the rare case — what a canvas is *for* is
showing what the instrument is doing — so composing things that vary is
what an author is nearly always writing, and it used to cost a lift at
every join: `!over (!moveXY (!60) (!80) (!fader level)) …`, six markers in
one expression and none of them about the picture.  The `Sub` level stays
because the other half of the advice is unchanged: a helper built from
numbers it already has is an ordinary function, lifted once where it meets
a signal.  `!` is still what joins the two levels; there is simply no lift
left where nothing is being joined.  `Num (Sig Int)` comes with them, so a
coordinate may be written as the number it is.

`substrate : Sig Sub` is the entry point.  `scene : Sig Scene` is the older
spelling and still works: the host wraps one in `still`, so there are two
spellings and **one** answer to what is drawn.  A program declaring both is
refused by name rather than having one silently win.

`gui._flatten` is the walk — a `Sub` tree to the shapes to draw, in the
order to draw them, with the transform accumulated on the way down and
applied at the leaves.  Painter's order: `over a b` is `a` and then `b`.
This is the walk S3 hangs the hit table off, which is the whole reason
`Sub` is data.

One thing moved while doing it.  **`constSig` is the renderer's now**, like
`sampleRate`: `!x` with no arguments means "always this", and what a signal
is constant *over* is a clock — the audio renderer supplies one over
`ticks`, the canvas one over `events`.  It had been in `audio.ges`, which
made a canvas that wanted a constant depend on a synth being present.

**S3 — attachment, and the walk.**  **Done**, editor wiring included.

    TouchX   : Chan Float -> Sub -> Sub          # the constructor
    TouchY   : Chan Float -> Sub -> Sub
    onTouchX : Chan Float -> Sig Sub -> Sig Sub   # what a program writes
    onTouchY : Chan Float -> Sig Sub -> Sig Sub

The channel is not lifted: it is what the element *is* rather than
anything it shows, and a `Chan` cannot go inside a `Sig` in any case —
the subgrammar keeps channels out of what signals carry.  So only the
picture is lifted, with `map` rather than `!`, which would lift both.

*(This section was drafted with an `Axis` argument and an `Int` payload —
`onDrag : Axis -> Chan Int -> …`, `Axis := AxisX | AxisY`.  **The axis
became the name**, because an argument that is always a literal at every
call site is a constant the caller carries to say which of two functions
it meant; `onTouchX` and `onTouchY` say it in the name and one job per
name is the rule elsewhere in this file.  And the payload became a
`Float` fraction rather than an `Int` offset — §"Attachment" above says
why.  `onPress` was drafted here too and is not built: §"Open questions"
1 holds it.)*

`gui._walk` draws the tree and records what listens in one descent: an
attachment's **region** is the box of whatever it drew, and its **origin**
is the transform accumulated on the way down, so a press arrives in the
element's own coordinates.  `gui.touches(source, gestures)` is the pure
driver, in the same shape as `scenes`: press, drag, release in, pictures
out, no window.

Three decisions worth having on the record.

**One number per attachment**, because the extractor says so in as many
words: *a control value is one slot, and `P` is 3.  Several parameters are
several channels — each keeps its own value across an edit, which fields of
one record would not.*  So a fader is one `onTouchY`, and a pad is two on one
element, which is honest: a pad *is* two parameters and would be two knobs.

**A press grabs.**  Hit-testing every drag afresh gives a fader that stops
following your hand at its own edge, which is not a fader.

**Innermost wins**, and it falls out: an attachment is recorded after the
subtree it wraps, so the deepest is the first one written down.

The editor's half is done too.  `gui.Substrate` is one file's canvas with
a hand on it — `touch(kind, x, y)` and `picture()` — and `Workbench` holds
one, rebuilds it with the sound, and consults it in `control` **by channel
name**.  One gesture writes both halves: the interpreted channel by id, so
the picture follows, and the value under the channel's name, so the engine
reads it exactly where it reads a knob.

The name-to-id map is the one thing that needed care.  A channel is
allocated when its declaration is first *forced*, so `Substrate` forces
every `name : Chan …` in the file before the program runs — in that state,
sharing its counter — which gives each declared channel an id and keeps
that id the one the program itself will see.  A fresh machine allocates
from its own counter and hands back the same id for every channel, which is
the shape of `fixme.md` F90/F91 and is what this avoids.

A canvas that fails to compile does not stop the instrument, exactly as a
placement failure does not, and a file with no canvas pays nothing.

**S4 — the pygame view.**  **Done**, as a second view rather than a
rewrite: `gestate/audiopygame.py`, with `Workbench` untouched.

    python -m gestate.audiopygame examples/audio/polysine.ges
    python -m gestate.audiopygame file.ges --plain      # no modes
    python -m gestate.audiopygame file.ges --midi 1     # and a controller
    python -m gestate.audiopygame --midi-ls             # what is plugged in

`Document` is text and a cursor over `balanced.py`'s rope — `insert`,
`erase`, `row` and `rowpos` were already written and already tested, which
is the half of a text editor nobody wants to write twice.  What had to be
got right is the cursor, and one thing in it: a vertical move keeps the
column it **set out from**, so passing through a short line and out on to a
long one comes back where it went in.

`Pane` is what a key *means* — the mode, the edit, the gesture — and
neither it nor `Document` imports pygame, the same split `gui.py` makes.
The useful half is tested without a window, and the window is the only
thing that is not.

**Modal, and saying so is the point.**  The `tkinter` editor already is:
its space bar plays or types a space depending on where the focus happens
to be, and its piano takes letter keys from whatever had them.  A mode you
cannot see is worse than one you choose.  Three rules keep it from being
what people mean by "modal":

* **`Esc` goes outward and `Return` comes back** — text, command, canvas,
  and back again.  Two keys, two directions.  `Esc` alone left the canvas
  a room with a door in one wall, which is the sort of thing only running
  it turns up.
* **Insert mode is an ordinary editor.**  Arrows, Home/End, Ctrl-S,
  Backspace, all where they always were.  A modal editor that also breaks
  insert mode is where the reputation comes from.
* **The mode is a colour** — a border all the way round, thickening at the
  bottom to carry the status line — rather than a word in a corner.  The
  text is clipped to the inner rectangle, because a long line writing over
  the one thing that says where you are is the same invisible-mode problem
  in a new place.

`--plain` starts in text and never leaves: one setting, not a fork.

**A toolbar in every mode**, because one that came and went would be one
more thing to learn: the transport on the left, the piano on the right.
`p` opens it to play and `P` in **step** mode, which writes what it plays
at the cursor — `Keyboard.press_key` already returned the note whether or
not a bank took it, and its docstring already said that was for this.  The
window is resizable and the text is sizeable, and neither needed any state:
`Layout` is built from the window there is, once a frame, which is also
what makes a click testable without opening anything.

**The chrome was the only thing you could press, and that was the gap.**
`Layout.buttons` is five fixed rectangles, and `click` knew three regions:
the toolbar, the sidebar, and the text.  Everything placed by *content*
fell through to the third — so a knob drawn beside the line that declares
it was a label, the drawn keyboard was a picture of a keyboard, and
`Workbench.set_value`, which is the call that actually drives a parameter,
had no caller in this view at all.  The `tkinter` editor got this for free
by making each knob a real widget placed by `dlineinfo`; owning the layout
is the better arrangement but it has to pay for the hit test it replaced.

`Layout.knob_rect` and `Layout.piano_keys` are that hit test, and they are
**arithmetic for the same reason everything else here is**: the draw calls
them to find out where to paint and the click calls them to find out what
was hit, so the two cannot drift apart and both can be checked without a
window.  A knob is a trough you drag — absolute across it, which is what a
trough means — and right-click arms `Workbench.learn`, the same gesture and
the same toggle the `tkinter` view has.  Only a **wired** knob turns: the
grey label already says the parameter has no channel behind it, and a
trough you could drag would move a number the sound never hears.

**The loop takes its end from the piece.**  `end_sample` already reads the
schedule's horizon for `>`, so `o` loops from 0 to wherever the score ends
and nobody types a number the file could have told them; `[` and `]` then
put either end where the transport has reached, and `O` forgets them and
goes back to the whole thing.  A pair of adjustable points needs the way
back as much as it needs the points.

**A second bug came out of running it, and it was in the window.**  Under
SDL2 a `RESIZABLE` window is resized by the window manager and `VIDEORESIZE`
is the notification; answering it with a second `set_mode` — which pygame 1
required — is a *request* for a size, issued tens of times a second while
the pointer is still dragging the edge.  The manager is told one size by
the drag and another by us, and the window flickers between them and snaps
out from under the hand.  The surface is now re-read from `get_surface`
each frame instead.

**One bug came out of running it**, and it was not in the editor.
`balanced.py`'s `segments` appended its own text even when the range asked
for lay entirely in the left child — with a *negative* index, so
`text[0:-1]` handed back a trimmed copy of the segment rather than nothing.
Every reader until now joined the whole rope, and a full-range read never
takes that branch; the first caller to ask for one line found it, as a
corrupted screen on a backspace.  `test/test_rope.py` reads ranges against
a plain string over sequences of edits, which is what would have caught
it.

**Knobs are drawn rather than placed.**  The `tkinter` view hangs a widget
beside a declaration and asks the text widget where that line ended up;
here the view owns the layout, so a knob is a line, a name and a number,
and where it goes falls out of the same walk that drew the line.

**And a knob appears when it is *declared*.**  The placement comes out of
the extracted graph and a graph holds only what `sound` reaches, so
`k = mkKnob 5` was invisible until something used it — backwards from the
order anyone writes in.  The text is read for those as well, which costs a
regular expression instead of a front end and is still true of a program
that will not compile; a knob nothing has reached yet says so rather than
showing a value that drives nothing.

**Two keys ask the compiler**, both answered on a worker because each is a
whole front end: `?` is `--query` for the name under the cursor, and `Tab`
at a `_` is `--fits` for that hole's own type — the list of what could
stand there, scrolling, since it is regularly forty names.  `Tab` anywhere
else is the indent it has always been.

**S5 — the sound back.**  **Done.**  The other direction: not a hand
reaching the program but the *instrument* reaching it.

    peak     : Chan Float      -- the loudest sample since the last look
    position : Chan Int        -- where the transport has reached

**Well-known names**, the way `sound`, `substrate`, `score` and `bpm` are
well-known: a program asks for a reading by declaring a channel with that
name, and asks for nothing by not declaring one.  `Substrate.write` is
`touch`'s mirror — the host putting a number on a channel the program
named — and a canvas that declares neither is written nothing and pays for
nothing.

Three things decided while building it:

**Once a frame, from the view.**  Not per block and never from the audio
thread.  The engine's clock is far faster than anything anyone can watch,
so a meter updated per block would draw sixty of them a frame and show the
last.

**A peak is taken, not read.**  `take_peak` returns what has happened since
it was last asked and resets.  A meter that decayed on its own would be
showing its own decay rather than the instrument.

**And it is only tracked when asked.**  `Transport.watch_peak` is off
unless the file declares `peak`, and when it is on the block is *sampled* —
sixteen points — rather than scanned.  That loop is in the one place in the
program with no time to spare, and a reading nobody looks at is a cost
nobody agreed to.

---

## Open questions

1. **Which events a host delivers.**  Press, drag and release are in;
   wheel, key and hover are not, and whether an attachment names the one it
   wants (`onPress` beside `onTouchY`) or takes one channel of a sum should
   be settled by a third element rather than in advance.

   *(The third element arrived and it was `Label`, which needed no event
   at all — so it settled the other pending question instead, about text,
   and left this one exactly where it was.  That is the discipline
   working rather than failing: an element gets built when a program
   wants it, and no program has yet wanted a wheel.)*

2. **A `Chan` in a data structure is interpreted-only.**  It works because
   the substrate runs on the G-machine.  The audio fragment would refuse it
   — a channel in a state struct has no layout — and nothing should be
   written that tempts a reader to try.

3. **One element per voice?**  A `voices` bank is N copies of a voice; an
   element inside one would be N objects.  The first answer is no — a
   bank's channels are written by a scheduler, not by a hand — but "no"
   should be recorded rather than assumed.

4. **Hit-testing is a bounding box.**  A `Dot` answers presses in its
   corners.  Fine for faders and buttons; wrong the first time an element
   is round and next to another.

5. **A label's letters are host-drawn, and the cell is in the
   vocabulary.**  `Label w h s c` declares a *box*; how big the glyphs
   come out is `min(w / (4n - 1), h / 5)` on a 3×5 cell with one column
   between letters — arithmetic on declared numbers, stated in `gui.ges`
   beside the constructor and implemented twice (`gui.py::_fit`,
   `substrate::fit`).  Two hosts therefore agree without either
   measuring a glyph, which is what keeps *"the extent is declared,
   never measured"* true with text in the vocabulary.

   What is *not* settled is whether the cell should be the vocabulary's
   business at all.  A host with real fonts could draw better letters in
   the same box, and the price of letting it is that the two hosts stop
   agreeing about a picture they are both drawing from one tree.  The
   cell was chosen because that agreement is what the parity test is
   for; a canvas that wants typography rather than captions will want
   this reopened.

Two questions that were here are **gone rather than answered**, both to the
same insight — the channel travels inside the structure.  *Where does a
dragged position live* (in the program, as `moveXY`, fed by a fold) and
*how does the host name a channel* (it does not; it reads the `NChan` it
walks into).

---

## Three readings set aside

Each was held for a while, and each is the obvious thing to try again.

**A declaration whose type is `Sub a` is a visible object**, found by
walking the compiled program the way `audiospans` finds control sources.
Discoverable, needs no top-level `substrate`, and matches how knobs are
placed beside their declarations today.

Set aside because **it cannot say where a dragged position lives.**  Each
declaration is an island, layout is host state, and the honest answer was a
sidecar file keyed by declaration name.  In the compositional reading,
position is `moveXY 100 200 fader` — in the program, where you can read it
— and a drag is a fold that feeds it.  The question dissolves rather than
needing machinery, which is usually the sign.

The second reason is the one this project should be quickest to hear.  A
synth is not "every declaration of type `Sig Float` is a voice"; it is one
`sound` built from combinators.  A canvas that was a registry of specially
typed declarations would be re-introducing exactly the ceremony
`spec/frp_lesson.md` is about, in the same week it was removed from the
audio half.

**`Sig (Sub a)`, with the value in the type.**  Fran's `ImageB = Behavior
Image` is a picture that varies, and with `!` every static combinator lifts
over time for free — genuinely tempting, and the reason `Sub` is under a
`Sig` at all.

The parameter is what was dropped, for the reason §"The value is not in the
type" gives: `over : Sub a -> Sub b -> Sub ?` has no answer worth having,
and it does not need one, because a value is a name the program already
has.  What survives is the shape — `Sig Sub`, static things lifted with `!`
— and what did not is the idea that composition has to carry a value along
with the picture.

**An element as a signal function**, `Sig Point -> ExL Click -> Sig Scene`,
so that a combinator could transform events going *in* as it transformed
shapes coming *out*.  This is the right answer in general, it is what
Yampa's arrows are for, and it is admissible here — the substrate is
interpreted, so functions as values and closures are all fine, and the
fragment discipline that shaped `synth.ges` does not reach the canvas.

It is unnecessary because **the host is not looking at an opaque
function**.  `Sub` is a value the program built, the host walks it to draw
it anyway, and the transform it needs for hit-testing falls out of the same
descent.  A design that hides the structure has to reconstruct that
information; one that does not, does not.  If a future element wants to be
opaque — one whose picture is computed rather than composed — this is where
to start reading.

## Where the export pulls this  *(added 2026-08-09, the day the CLAP shell landed)*

The plugin work (`spec/export.md`, `shell/clap/`) proved something this
file should own, because the substrate is where it points.

**A gestate program composes with a foreign host through exactly three
things.**  Names the renderer supplies (`ticks`, `sampleRate`, the
clock a `constSig` is constant over); typed channels crossing in both
directions (knobs, a bank's notes, the editor's `peak` and `bands`
readings); and a descriptor of what only the compiler knew.  Nothing
of ours runs in the DAW — no Python, no interpreter, no runtime — and
none was missed.  The boundary was already this narrow; the export
merely walked through it.

**So the plugin GUI question and the substrate are the same
question.**  `spec/export.md` defers `clap.gui` as "a project rather
than an evening" — but the project it is, is *this file*.  A substrate
is a value a host walks to draw; the editor already hosts one file's
sound and face in one window; a plugin host offering a window is the
same request from a different landlord.  The synth that draws its own
panel — the routing matrix, the knobs, a meter breathing off the
`peak` channel — is not a new UI framework beside the substrate, it is
a substrate whose host happens to be a DAW.  When `clap.gui`'s day
comes, the panel is a `substrate` declaration in the same `.ges` file
as the `sound`, and the browser playground's canvas is the third
landlord for the identical value.

**The context contract**, stated once, because every piece of it
already exists and only the name was missing.  A `.ges` file works in
*every* context — editor, offline render, plugin, canvas, playground —
exactly when:

1. **Its needs are names the renderer supplies.**  One meaning, as
   many implementations as there are renderers: `constSig` is constant
   over whichever clock is asking, `sampleRate` is the file's or the
   device's, `beat` is the score's — or, in a DAW, the transport's own
   beats timeline, which is the supply that makes a scored program
   lock to the session's bars.  A context that cannot answer refuses
   **by name** (`Unknown global 'beat'`), never answers wrongly.
2. **Everything else crosses a typed channel**, and a channel is
   meaningful to the program alone — the host learns which channels
   exist and what they carry from the descriptor, not from what they
   are called.
3. **What only the compiler knows travels as a descriptor** — rates,
   layouts, banks, defaults — so a host needs no opinion about the
   language.

**And a confession the contract made unavoidable: `tempoChan` was
wrong — it is retired now, the same day it was confessed.**  It had
worked, in the sense that the shell fed the transport's tempo to a
Float channel spelled exactly `tempoChan`, and it was this project's
first and only *nominal convention*: meaning smuggled through a
channel's spelling, invisible to the compiler, impossible to refuse by
name, and honored in one context out of five.

Clause 1 said what the repair was and the repair is in: the host's
tempo belongs among **the renderer's own**.  A DAW supplies `beat`
from its beats timeline — three channels carrying a *line*
`(base, slope, anchor)`, evaluated at `ticks` by ordinary signal
arithmetic, with the slots declared in the descriptor rather than
spelled in the shell — and `beatRate` answers "how fast is this going"
in beats a second.  Where the program is its own conductor, both still
compile from `bpm` and the `tempo` envelope, as before.  That a
renderer's-own name compiles differently per renderer was never the
wrinkle; it is the whole pattern, and `constSig` has worked that way
from the start.  `journal.md` §"`beat` finds its conductor, and the
convention dies young" is the record, and `shell/clap/src/engine.rs`
keeps a one-line headstone where the convention briefly lived.

*(Since written: it has, and the host is running.  `crust` holds the
reactive half — signal cells in a stable arena, the sweep, the ✓
frontier — `shell/panel/src/substrate.rs` walks a `Sub` into the same
display list panel one produces, and `shell/panel/src/canvas.rs` turns
the loop: arrivals, `reactive_step`, `main`'s cell, walk, paint, once a
frame, on the plugin's window thread.  A file that declares a
`substrate` now exports one — `export.substrate_of` sends the program,
the constructor tags and the channel names — and it appears on the
window's second tab, beside the knobs, with the sound and the picture
reading one fold.  `examples/audio/substrate.ges` is the file that
proves it: drag the fader and the filter moves, because they are the
same `cutoff`.
 
The one thing S5 promised that is now real rather than argued: `peak`
is written by the audio thread every block and read by the canvas every
frame, so the meter in the picture is the instrument's own loudness.
The tabbed **editor** below is still not built; what exists is the
tabbed *plugin window*, which is the same argument at a smaller
scale.)*

**And the interpreter has to travel — the G-machine ports to Rust,
eventually.**  The compiled fragment crosses into foreign hosts today
because it is machine code with a two-symbol contract; everything the
*interpreted* half does stays home, because it is Python.  The export
has dodged that line once already: `FromMIDI` payloads are the
G-machine run at export time and tabled — a dodge that works for
notes because a keyboard's domain is 128 keys, and works for nothing
bigger.  A `clap.gui` panel is a `substrate`, and a substrate is
*interpreted by design* (§ above: closures and functions-as-values
are fine there precisely because the fragment discipline does not
reach the canvas) — so the panel needs the G-machine inside the
shell, and the browser playground's second cut (editing, not just
playing) needs it in WASM.  One Rust port serves both landlords, the
way one C ABI shell did for sound; `gmachine.py` stays the reference
the port is held against, sample-for-sample on `Sub` trees the way
the engines are held together on samples.  Not soon — the tabled
dodge and the parameter matrix cover the pack that exists — but the
line is drawn here so nobody mistakes the dodge for the design.
