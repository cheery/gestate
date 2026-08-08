The language and it's environment is designed for musical
expression. There are following primitives to achieve
it in practice:

1. Bounded integers
2. Cyclic integers
3. Integers
4. Abstract data types
5. Simple Tuples and records
6. Functions
7. Score -objects

Musical constructs:

1. Overlay `(a || b)`
2. Sequence `(a ++ b)`
3. *(withdrawn — stretch is an engraving concern, not a performance one;
   see "Why stretch is gone" below.)*
4. Offset `(at n a)` Places `a` `n` ticks from where it would otherwise
   sit.  `(|< a)` and `(a >|)` are sugar for one beat either way.
5. *(see 4 — the two shifts are one operation.)*
6. Unit rest `(r)`
7. Unit note `('x)`
8. Multiply by integer duration `(a |* n)`
9. Divide by integer duration `(a |/ n)`
10. *(withdrawn — instrument selection is `>>=`; see below.)*
11. Map over score's values: `(a >>= f)` Yes, score has a monad interface.

Example musical element:

    '1 ++ '2 ++ '3 |* 2 || '5 |* 6

This was originally read as

    (('1 ++ '2 ++ '3) |* 2) || ('5 |* 6)

with scaling looser than sequencing, so that it applied to the whole phrase
beside it.  **It does not any more**, and the change came from writing
music rather than from reasoning about it:

    ('1 ++ '2) |/ 2 ++ ('3 ++ '4) |/ 2

is what a bar of eighth notes actually looks like, and under the loose
reading the second `|/` took everything before it — silently, surfacing as
a type error about `Int` some definitions away.  Two scaled groups in a row
is the common case; scaling an unparenthesised phrase is not.  Every use in
`examples/music/` parenthesises its left operand already.

So duration scaling is `infixl 6`, tighter than sequencing, and the element
above reads

    (('1 ++ '2 ++ ('3 |* 2)) || ('5 |* 6))

Overlay stays `infixl 2` and sequencing `infixl 4`.  To scale a phrase,
parenthesise it — which is what one writes anyway.
`test/test_music_syntax.py`.


**Implemented.**  `gestate/music.ges` holds the `Score` data type and every
operator; `gestate/midi.py` is the MIDI backend.  A program supplies

    score : [: Void :]
    bpm   : Int

and the renderer supplies `main`.  `music.ges` is *not* part of the core
prelude: it declares eight constructors, and a constructor's tag is its
position, so merging it would renumber `Nil`/`Cons` for every program in
the language — and cost every non-musical program its compile time.  The
backend prepends it to a music program's source instead, which needs no
module system.

`++` means *music sequence* inside a music program, shadowing the core
prelude's list append; `append` remains for lists.  A class with two
instances would be the general answer and has no caller yet.

**Percussion** is a second `Rendered` constructor rather than a program
number, because it is a different *kind* of sound and not a choice of
instrument: `percussion : Int -> [: b :]` takes a General MIDI drum key and
needs no program, so it is itself the function `>>=` wants.  Which channel
carries it is the renderer's business — channel 9 in General MIDI, where
the channel *is* the kit and no program change is sent.

Worked examples are in `examples/music/`, rendered beside their sources.

When Score values are read, the musical notation
is being first layouted and then rendered.
Music layouting does basic box layout with
negative spaces shifted and stretch items counted and applied.

## What a Score value is

A `[: A :]` is a **box-layout tree**, not a list of events and not a set of
them.  The constructors are the musical constructs above: unit notes and
rests at the leaves, and the combinators building nodes.  It carries a payload
type `A` — the leaves hold `A`, and nothing in the layout inspects it.

`'` — the unit note — answers `errata.md` S4's objection that `Score` had no
constructors and so could not be inhabited.  A note is *one beat* by
construction and `|*` is how any other duration is reached, so duration lives
in the tree rather than in the leaves.  The operators are typed below.

**Layout** is the elimination form.  It resolves the tree into a flat,
time-stamped performance:

```
layout : [: Void :]  ->  [(Onset, Offset, R)]
```

Onsets are in the score's **own** coordinates and may be negative, since
`at` can place content before the origin.  Normalising is the *renderer's*
choice, not the language's: a grid view may well want to show that a fill
precedes bar 1, while a MIDI writer must not emit a negative timestamp.
One list, two policies.

`R` is the playable thing the renderer consumes — built in, and *not* the
score's payload parameter.  `[: Void :]` is a **performable** score: `[: a :]`
means "a score whose *unassigned* notes carry `a`", `Void` is uninhabited, so
a score at that type has none left.  This says at rank 1 what
`forall b. [: b :]` would say at rank 2, which gestate does not reach.

Layout is "basic box layout with negative spaces shifted and stretch items
counted and applied", and the resemblance to a UI layout pass is the intended
one: `++` is sequential packing, `||` is overlay in the same span, `at`
offsets a subtree within its container, and `|*`/`|/` scale a subtree's
duration.

### The operators

Ordinary types, once `[: a :]` is a layout tree over a payload.

```
(')     : a -> [: a :]                          -- unit note, one beat
r       : [: a :]                               -- unit rest, one beat
(++)    : [: a :] -> [: a :] -> [: a :]         -- sequence
(||)    : [: a :] -> [: a :] -> [: a :]         -- overlay
at      : Int -> [: a :] -> [: a :]             -- offset, in ticks
(|<_)   : [: a :] -> [: a :]                    -- `at (-beat)`
(_>|)   : [: a :] -> [: a :]                    -- `at beat`
(|*)    : [: a :] -> Int -> [: a :]             -- scale duration up
(|/)    : [: a :] -> Int -> [: a :]             -- scale duration down
(>>=)   : [: a :] -> (a -> [: b :]) -> [: b :]  -- substitute for each note
```

`|*` and `|/` take a plain `Int`, and conversion is **explicit**:

```
class ToInt a where
    toInt : a -> Int

x |* toInt i        -- rather than  x |* i
```

The tempting signature is `(ToInt b) => [: a :] -> b -> [: a :]`, and it is
the wrong one.  A numeric literal is already `Num`-polymorphic through
`fromInteger`, so `x |* 2` would constrain its argument by `Num b, ToInt b`
and nothing else — ambiguous, and resolvable only by defaulting.  Writing
`toInt` at the call site costs one word and keeps every duration's type
determined by what the program says rather than by a defaulting rule.

Note that `r` mentions `a` in the *result but not the argument*: a rest
carries no payload, so it is parametric and imposes no constraint on the
payload of a score it sits in.  That is what the next section turns on.

### Duration and extent are different things

A score has **two** measurements, and keeping them apart is what makes `at`
behave:

- its **duration** — how far `++` advances past it;
- its **extent** — the span its content actually occupies, `[start, end]`.

This is a font's *advance width* against its *bounding box*, and negative
side bearings are the same idea: content may sit outside the advance.

```
'x, r        duration = 1 beat            extent = [0, beat]
a ++ b       duration = dur a + dur b     b placed at dur a
                                          extent = ext a ∪ (ext b + dur a)
a || b       duration = max (dur a) (dur b)
                                          extent = ext a ∪ ext b
at n s       duration = dur s             extent = ext s + n
s |* k       everything scaled by k       (the offset scales too)
```

**`at` translates the extent and leaves the duration alone.**  That is the
whole rule, and both cases follow from it:

    a ++ at (-1) b        b's content starts one tick before `a` ends —
                          it overlaps — and whatever follows is unmoved,
                          because `++` still advanced by `b`'s duration.

    at (-4) x             alone, the origin is 0, so it sounds from -4.

Placing `b` "at `a`'s end" would have destroyed the first case: normalising
to the *start* of the extent cancels the very translation `at` applied.
`++` chains **origins**, not extents.

### Time is integer ticks

A beat is **96 ticks**.  `|/ n` has to divide exactly, and 96 is divisible
by 2, 3, 4, 6, 8, 12, 16, 24, 32 and 48 — which is why numbers of that shape
are traditional in MIDI files.  `|/ 5` is an **error**, not a rounding:
music silently retimed is the worst failure this could have.

Everything downstream is therefore integer arithmetic — no rationals, no
float drift, and a layout that is exactly testable.  `bpm` converts ticks to
real time once, at render, so no part of the tree knows about seconds.

### Why stretch is gone

`|~|`/`sp` was to "expand to fill on a loose sequence".  That is
**engraving**: justifying noteheads across a printed system.  A piano-roll
grid has linear time and no justification problem, and neither does MIDI —
so it has no caller in either output this design is aimed at.

It also carried the whole cost of the layout pass.  With stretch, layout is
two passes: natural width flowing *up*, then available width flowing *down*
so slack can be divided among the stretch items.  Without it, layout is a
single bottom-up fold computing duration and extent.  That is the difference
between a careful constrained pass and a fold.

If an engraver is ever written, stretch comes back then — and by then its
requirements will be known rather than guessed.

### Instruments, and why `[: Void :]` is reachable

An **instrument** is a function from a note's payload to a score:

```
a -> [: b :]
```

and applying one to every note is exactly `>>=`.  There is no separate
instrument-selection operator; `@` was withdrawn because this is its job.

What makes a score *performable* is that the instrument's result contains no
payload-carrying leaves — only committed, playable ones and structure.  A
score built that way is parametric in its payload, so it unifies at `Void`,
and the chain terminates:

```
score  : [: Note :]
inst   : Note -> [: b :]        -- committed leaves only, so `b` is free
score >>= inst  :  [: Void :]   -- b := Void
layout (score >>= inst)  :  [(Onset, Offset, R)]
```

This is why the payload can be erased without an erasing *operator*: `>>=`
does not remove a payload, but an instrument can decline to produce one, and
parametricity turns "produced none" into "performable" as a typing property
rather than a runtime check.  It also means a score still holding unassigned
notes simply will not type against `layout`.

It follows that the leaf a committed note becomes is **not** `'`: `'` is the
unassigned note, `' : a -> [: a :]`, and a committed leaf carries an `R` and
is parametric, `R -> [: a :]`.  That constructor is built in and is the one
thing in this design with no surface syntax yet.

### The algebra this implies

- `++` is **associative** with the empty score as identity, and *not*
  commutative — it is a monoid, and order is the whole point of a sequence.
- `||` is **associative and commutative** with the same identity, and
  **not idempotent**: `a || a` sounds two notes together and lays out to two
  events where `a` lays out to one.
- `Score` is therefore a **commutative monoid** under overlay, **not a
  semilattice.**  There is no join and no order for it to be a join of, so
  `Score` carries the trivial change structure `ΔScore = 1` like any other
  discretely ordered type (`data.md` §I.8), and `for` cannot eliminate into
  it.
- `>>=` substitutes a whole score for each leaf payload, which is the usual
  monad on temporal media; `layout` of the result concatenates the layouts of
  the substituted subtrees within each leaf's span.

### How a query becomes music

Because `for` eliminates only into a semilattice, a Datafun query **cannot
build a score directly**.  The connection runs the other way, and it is the
same shape as `empty?`/`holds` (`syntax.md`): a query is run to its fixed
point, its result is then *observed discretely* — a set is an unordered value,
so this needs an ordering-respecting `□{A} -> [A]`, which the generated
element comparators already support — and the resulting list is folded with
`++`/`||` into a score.

Seminaïve evaluation therefore applies to the query and stops at its boundary.
Nothing incremental crosses into layout, and that is a deliberate consequence
of `Score` not being a semilattice rather than an oversight.
