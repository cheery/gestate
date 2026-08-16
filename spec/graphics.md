# graphics.md — the grammar of graphics, read against this project

*A reading, not a feature.*  `spec/frp_lesson.md` is the precedent:
somebody else's design set beside this one, and its worth measured by
the gaps it names rather than by anything it adds.  Wilkinson's *The
Grammar of Graphics* and Wickham's layered reading of it (ggplot2) are
the text; the question is the one this project is about to meet twice
— once for the substrate's vocabulary and once for the score box's:

> **What is the smallest set of parts that draws data, and where is the
> seam between the data, the mapping and the mark?**

Henri, 2026-08-16, setting the scope: *"What I want from it is what we
can collect as good ideas.  Remember that the spec is implemented when
there is a need for the feature.  We collect here the features that
might reach implementation some time.  Those ideas should be included
because grammar of graphics imo does something right."*

So this file **proposes nothing for the next commit.**  Every idea in
§"The collected ideas" is written with the caller it is waiting for.
That is the project's own rule (`roadmap.md` §"The rule"), applied to a
reading: a reading may not smuggle in work.

---

## What the grammar claims

The claim is narrow and strong: **a statistical graphic is not a chart
type.**  There is no "bar chart" object; there is a mapping from data to
a geometry, and a bar chart is one point in a space that also contains
things nobody has named.  Wilkinson's list, in his order and with the
names Wickham settled on:

| part | what it decides | example |
|---|---|---|
| **data** | what is being drawn | a table of rows |
| **trans / stat** | what is computed from it before drawing | count, bin, smooth, identity |
| **algebra** | how variables are combined | cross `*`, nest `/`, blend `+` |
| **scale** | how a variable's values become a drawable quantity | linear, log, ordinal, a colour ramp |
| **coord** | the space the marks live in | cartesian, polar, map projection |
| **geom** | the mark itself | point, line, bar, area, text |
| **aesthetic** | which channel of the mark a variable feeds | x, y, size, colour, shape |
| **guide** | how a reader inverts a mapping | axis, legend, tick, label |
| **facet** | how one graphic becomes many small ones | by a variable, in a grid |
| **position** | what to do when marks collide | stack, dodge, jitter |

Wickham's contribution on top of Wilkinson's is the **layer**: a graphic
is a list of layers, each of which is *(data, mapping, stat, geom,
position)*, over shared scales, one coord and one facet.  That is the
part that makes it compose rather than enumerate, and it is the part
worth stealing if any is.

**The three ideas that survive translation to anything**, stated
plainly, because these are what "does something right" means:

1. **A mark is not a chart.**  What varies is *which variable feeds
   which channel of the mark*, and the channels are named separately
   from the mark.  Every plotting library that grows a function per
   chart type is re-enumerating a product it could have factored.
2. **A scale is a first-class thing, not arithmetic in the drawing
   code.**  It is the pair (data value → drawable quantity, and its
   inverse for the guide).  Holding it as a value is what makes an axis
   and a legend *derivable* rather than drawn by hand beside the data.
   The inverse is what makes a picture answer a pointer.
3. **Layout is algebra, not coordinates.**  `x * y` is a cross, `x / y`
   is a nesting; a facet grid is that algebra given room.  Places are
   computed from structure rather than written down.

---

## Where this project already stands

Read against the two surfaces gestate actually has.  They are not one
thing, and a file that tried to cover both with one vocabulary would
cover neither (Henri's Question B, answered by looking).

### The substrate — `Sig Sub`, a picture that varies and can be touched

`spec/substrate.md`.  `Sub` is `Rect`, `Circle`, `Gap`, `Label`, and
the combinators `Over`, `Row`, `Column`, `Shift`, `Sized`, `Pad`,
`TouchX`, `TouchY`.  Against the table above:

- **geom** — present, and small: four marks.  Deliberately: a fifth
  needs a program that wants it (`roadmap.md`, the third-element rule).
- **coord** — present as one: pixels, origin at the centre, extents
  declared rather than measured.
- **algebra** — present, and it is *layout* algebra rather than
  variable algebra.  `Row`/`Column`/`Over` are exactly Wilkinson's
  cross and overlay read as composition, and `spec/substrate.md`
  §"Composition, and why it stays first-order" already argues why they
  are ordinary functions.
- **aesthetic** — **absent, and the reason is the interesting one.**
  There is no mapping layer because there is no *data* layer: a
  substrate is drawn from signals the program named, and a signal
  reaches a mark by being passed to a function that builds it.
  Wilkinson maps a *column of a table* to a channel; gestate applies a
  function to a signal.  The mapping is the program.
- **scale** — **half present, and unnamed.**  Every substrate example
  in the tree computes one by hand: a fraction to a pixel height, a
  hertz to a fader position, `clamp` at the boundary because an
  offline render drives a control with the sample index.  It is the
  same arithmetic in every file and it has no name.
- **guide** — absent.  `Label` places a word; nothing derives an axis
  or a legend from a scale, because there is no scale to derive from.
- **stat, facet, position** — absent, and no caller in sight.  This is
  a control surface, not a chart: there is nothing to bin and nothing
  to dodge.

**The seam this locates**: the substrate has marks and layout and *no
named mapping between a quantity and a channel*.  `TouchX`/`TouchY`
already carry half of one — they are an inverse mapping, pixels back to
a fraction on a channel — written for the hand rather than for the eye.

### The score box — a picture derived from text, which writes back

`spec/scorebox.md`, `spec/north_star.md`.  A roll: time across, pitch
up, one mark per note, ink for provenance, a hand per column.  Against
the table:

- **data** — present and *unusual*: the data is a program's own score
  expression, walked (`spreadTo`, `tagAll`), with provenance back to
  the byte range that wrote each note.
- **scale** — **present, named, and load-bearing**: `y_of` maps a key
  number to a row of the picture, and `key_at` inverts it.  The drag is
  built on the inverse being the *same* function — `spec/north_star.md`:
  *"the same function that drew it, inverted, so the picture and the
  arithmetic cannot disagree."*
- **aesthetic** — present as a fixed set: time→x, pitch→y, provenance→
  ink, take→ink.  Not a mapping a program may choose.
- **guide** — a label carrying the take's seed, and nothing else; no
  axis, no ruler.
- **coord** — one, and clipped on the tick axis by design.
- **stat / facet / position** — absent.

**The seam this locates**: the score box already has the grammar's
second idea *in full* — a scale held as a value with its inverse, which
is precisely what lets a picture answer a pointer — and it has it in
one place, hard-coded for one picture.  The substrate, which has many
pictures, does not have it at all.

**That asymmetry is the finding of this reading.**

---

## The collected ideas, each with the caller it waits for

Written so a later session meets a decision rather than a temptation.
None of these is scheduled.

1. **A scale as a value, with its inverse.**  `Scale a` as a pair of
   maps, drawn from and *pointed at* through the same value —
   `y_of`/`key_at` generalised out of the score box.  Its worth is not
   drawing (the arithmetic is three lines); it is that **hit-testing
   stops being a second implementation of layout**.  This project has
   already paid twice for that being two implementations, and
   `view::knob_hit` sits beside its trough for exactly this reason.
   *Caller: the second substrate element that wants to be dragged in
   its own units — a plotted signal, an envelope with grabbable
   breakpoints.*

2. **A guide derived from a scale.**  Given a scale, an axis with ticks
   and a legend are functions, not drawings.  It is `Label` plus
   arithmetic, and the reason to wait is that no substrate in the tree
   has yet wanted a numbered axis.
   *Caller: the first meter or plot somebody wants to read a value off
   rather than watch.*

3. **The layer, as an ordinary list.**  Wickham's layer is
   *(data, mapping, geom)*; in this language that is a function
   returning `Sub` and a `foldr over` — which is to say **gestate
   already has layers and calls them function application**.  Worth
   writing down precisely because it is a gap that is *already
   closed*: a reading that recommended adding a `Layer` type would be
   recommending a constructor tax for something composition does.

4. **Position adjustment as a combinator, not a flag.**  `Row`/`Column`
   are `dodge`; `Over` is `identity`; `stack` would be a fold that
   accumulates an offset.  If a caller ever wants stacking, it is a
   function over a list of `Sub`, and it must not become an argument on
   an existing constructor.
   *Caller: a stacked band meter, or a score box drawing several banks
   on one roll.*

5. **Faceting as `Row` over a list.**  The grammar's small-multiples
   are, here, `foldr Row` over a mapped list — again already available.
   The idea worth keeping is not the mechanism but the *discipline*:
   small multiples beat an overplotted axis, which is a claim about
   pictures that a spec can hold and a library cannot.

6. **The one thing to refuse: a `stat` layer.**  Binning, smoothing and
   counting inside the drawing are a second place where data is
   transformed, and this language's whole answer is that transformation
   is what functions are for.  `spec/substrate.md` §"What it is *not*"
   already refuses the neighbouring temptation.  Named here so the
   refusal is on the record with a reason rather than by omission.

---

## What this reading does *not* claim

- **That the substrate should become a plotting library.**  It is a
  control surface that happens to draw; the grammar is about
  *statistical* graphics, and most of it has no work to do here.
- **That the two surfaces should be unified.**  They differ in what
  they draw *from* — one from signals the program named, one from the
  author's own text — and the score box's write-back has no counterpart
  in Wilkinson at all.  A drag that edits the program that produced the
  mark is outside the grammar's world, and it is the more interesting
  half of what this project has.
- **That anything above is next.**  Item 1 of the list is the one with
  a plausible caller inside a month; the rest are recorded so that when
  a caller does arrive, the shape is already argued.
