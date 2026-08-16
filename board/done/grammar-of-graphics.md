# grammar-of-graphics — read it, and collect what it does right

    status   done — 2026-08-16
    because  grammar of graphics does something right and we have not
             said what
    asked    Henri, 2026-08-16
    see      spec/graphics.md
             journal.md §"Reading Wilkinson at the score box"
             roadmap.md §"The grammar of graphics"

## The ask

> Examine grammar of graphics and do specification work of your
> discoveries.  Either write a new or modify existing one.

## Found by looking, before it was taken

Reading and specification, not code, and its output is a `spec/` file
argued the way `spec/scorebox.md` was.  The reason it is not obvious
what to write is that gestate has *two* drawing surfaces with different
contracts — the **substrate** (`substrate : Sig Sub`, a value composed
by ordinary functions, interpreted at frame rate) and **score boxes** (a
picture derived from text, which now writes back).  Wilkinson's grammar
is about mapping data to marks, which is a third thing again.

## Questions

**Q (Claude).**  Which surface is the grammar of graphics *for* — the
substrate, score boxes, or a data-to-marks layer above both?  A spec
that tries to cover all three will cover none.

**Henri, 2026-08-16:**

> I haven't been familiar with score boxes.  I may be wrong about this,
> but some of it probably is implementable in both substrate and score
> boxes.  What I want from it is what we can collect as good ideas.
> Remember that the spec is implemented when there is a need for the
> feature.  We collect here the features that might reach implementation
> some time.  Those ideas should be included because grammar of graphics
> imo does something right.

## Done

`spec/graphics.md`, a reading in `spec/frp_lesson.md`'s tradition, its
worth measured by the gaps it names.

**The finding was not where the item pointed.**  The question was what
the *substrate* is missing; the answer is that the **score box already
holds the grammar's load-bearing idea and the substrate does not**.  A
scale — a map from a data value to a drawable quantity, kept as a value
*together with its inverse* — is what lets a picture answer a pointer,
and the north star's drag is built on `y_of` and `key_at` being one
function read both ways.  The substrate has many pictures and no scale
at all: every example computes fraction-to-pixels by hand, and
`TouchX`/`TouchY` carry half an inverse written for the hand rather than
for the eye.

The other half is what it refuses.  Layers and small multiples — the two
parts of ggplot2 anybody reaches for first — are **gaps already closed**:
a layer is function application, a facet grid is `foldr Row`, and
proposing types for them would be a constructor tax for what composition
does.  A `stat` layer is refused outright with its reason on the record.

Six ideas collected, each with the caller it waits for.  Nothing
scheduled, which is the shape asked for.
