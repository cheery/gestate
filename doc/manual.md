# gestate — a manual

This is for someone who has just opened the repository.  It assumes you can
read a functional language and know what a type is.  It does not assume you
know Datafun, Rizzo, or what a "semilattice" is for.

Read it in order the first time.  §1–§3 get you writing programs; §4–§6 are
the three ideas the language is actually built on, and each has a *how to
think about it* section, because each one has a natural misreading that will
cost you an afternoon.

---

## 1. What this is

Gestate is a language for **musical expression** that has two unusual halves
bolted to a fairly ordinary functional core:

- **Datafun** — sets, comprehensions, and least fixed points.  You write a
  Datalog query as a comprehension and the compiler makes it incremental.
- **Rizzo** — functional reactive programming, where a signal is a heap
  cell that gets overwritten as time passes rather than a lazy stream that
  accumulates.

They coexist without interfering, and §6 explains the mechanism that keeps
them apart.  The music half sits on top of both.

The ordinary core is Hindley–Milner inference, algebraic data types,
pattern matching, type classes with dictionary passing, and a G-machine.
If you have written Haskell you will recognise most of the surface.

**What it is not.** There are no modules, no IO beyond the renderers, and
no separate compilation.  Programs are single files.

**The name.** *Gestate*: to carry something living, without interrupting it.
It also reads as **ges**ture + **state**. Neither meaning was planned — the
name came first and the language grew into it — but both are load-bearing
now. A signal is state folded over time, held in a cell that is overwritten
rather than extended (§6), so a running program *is* the state it carries;
and where this is going (`spec/liveaudio.md`) is a synth you edit while it
sounds, which keeps what it was holding rather than starting again. Soft
*g*, as in *gesture*: "jes-tate", and `.ges` is "jess".

---

## 2. Five minutes

There is nothing to install.  The compiler and the `.wav` renderer are pure
Python; the backends that touch the outside world want a package each —
`mido` for MIDI, `pygame` for the canvas and the editor — and the suite
skips what it cannot import.  `requirements.txt` says which is for what,
at length.

```
$ python -m gestate.typecheck examples/closure.ges     # infer and print types
$ python -m gestate.typecheck examples/closure.ges --check   # errors only
$ python -m gestate.midi examples/music/drums.ges --events   # lay out a score
$ python -m gestate.midi examples/music/drums.ges            # write drums.mid
$ python -m gestate.audioperform examples/audio/sine.ges -o sine.wav  # render a synth
$ python -m pytest test -q                                   # the suite
```

Start by reading `examples/`.  Every file there runs, and
`test/test_examples.py` asserts the result each one's comments claim — so
they cannot quietly go stale.

A program is a file of declarations.  `main` is the entry point:

```
double : Int -> Int
double n = n * 2

main : Int
main = double 21
```

Three kinds of program are shaped differently and have `main` supplied
for them.  A **music** program defines `score : [: Void :]` and
`bpm : Int` (§7).  A **synth** defines `sound : Sig Float` and is rendered
with `python -m gestate.audioperform` or played live (§6).  A **canvas** program
defines `substrate : Sig Sub` and is run with `python -m gestate.gui`
(§6).  A backend finds your program by these names — `doc/ref/index.md`
holds the full table of who looks for what, and what each puts in scope.

---

## 3. The surface

### Declarations

A signature and one or more equations.  Signatures are optional — inference
will find a type — but see §4 for why you usually want them.

```
length : List a -> Int
length xs = case xs of
    [] -> 0
    x :: rest -> 1 + length rest
```

Multiple equations with patterns work too:

```
fst : (a, b) -> a
fst (x, y) = x
```

### Layout

Indentation delimits blocks, as in Haskell.  A `case`'s alternatives are
indented under it; a `class`'s or `instance`'s members likewise.  A one-line
`case` is fine.  There is no `where`.

A definition may be **broken across lines**.  An indented line continues the
one above, rather than opening a block, when either:

```
melody : [: Int :]
melody = '69 ++ '71 ++ '72 ++ '76      -- it starts with an operator
      ++ '77 ++ '76 ++ '72 ++ '69

showFloat x = append (showNat (floor x))
                     (append "." (digits x))    -- or with `(`

f : Int -> Int
f x =                                  -- or the line above ends with `=`
    x + 1
```

Those are unambiguous.  Nothing that begins a new declaration, binding or
case alternative starts with an operator; nothing but a body can follow a
trailing `=`; and the two things that *can* start with `(` — a
tuple-pattern alternative, an operator class member — always come directly
after `of`, `where`, `let` or `given`, which never take a continuation.

A **bare operand** on its own line continues too — `f 1` with an indented
`2` under it — and the way it is told from a block item is that an item
*binds a name* and a continuation does not.  The line is scanned to its
end: a top-level `=` on it makes it an item, so `let x = 5` with `y = 6`
indented beneath still opens a block, exactly as before.

Inside brackets none of this applies: a list, a tuple or a parenthesised
expression may be spread over as many lines as it likes, with no rule to
learn.

```
windGain : List Envelope
windGain = [ Step 0.0 0.0, Ramp 6.0 0.55
           , Ramp 14.0 0.18, Ramp 22.0 0.70 ]
```

A block *opened* inside a bracket keeps the offside rule — `foldr (x b =>
case p x of` with its alternatives indented under it is how `all` and `any`
are written in the prelude — because what is suppressed is only a newline
deeper in brackets than the block it sits in.

### Data

`:=` declares a data type.

```
Colour := Red | Green | Blue deriving (Show, Eq, Ord)

Maybe a := Nothing | Just a
```

A **record is a data type with one constructor.**  There is no separate
record syntax:

```
Point := Point Int Int deriving (Show, Eq)

xOf : Point -> Int
xOf (Point x y) = x        -- by pattern
xOf' : Point -> Int
xOf' p = p.0               -- by projection
```

`deriving` understands `Show`, `Eq` and `Ord`.  Derived `Ord` compares
constructors by *declaration position* first, then fields left to right.

### Numbers

**A literal's form is its class.**  `1` is `Num a => a` and `1.5` is
`Floating a => a`, so both are as polymorphic as the instances a program
has — and neither is defaulted into the other: `main : Int ; main = 1.5`
is still a type error, now reported as the missing `Floating Int`, which
is what "1.5 is not an `Int`" is in the type system's own words.

The two mix without a coercion:

```
f : Float -> Float
f x = x * 2 + 1          -- `2` and `1` are `Num a => a`; `a` is `Float` here
```

That works because an integer literal carries a `Num` constraint that
`Num Float` discharges, so the answer is *derived* rather than guessed.

**A program can say what a literal means at its own type**, which is what
the two classes are for:

```
instance Floating (Sig Float) where
    fromFloat x = constSig x
```

is one line of `audio.ges`, and it is why a synth may write
`tone * (0.5 + wiggle * 0.25)` — arithmetic over signals, meaning exactly
the `zip` chain it looks like.  Left alone, a literal nothing pins down
defaults the way it always did: to `Int` for `Num`, and to `Float` when a
`Floating` constraint is on it, because `Floating Int` is not an instance
and should never be one.

`/` and `%` are `class Div`, with instances at `Int` and at `Float`.  At
`Int`, `/` **floors** — which is what `%` agreeing with it means, and it is
a footgun kept deliberately: `/` used to be at `Float` only, and the cost
was that `prim_div_int` — a name spelled like a compiler internal, because
it is one — appeared sixteen times across `examples/`.  Documented beats
hidden behind a spelling nobody would choose.

`toFloat : Int -> Float` goes one way; `floor` and `ceil : Float -> Int` go
the other, and `floor` really floors, so it agrees with `/` on negatives.

### Types you get for free

```
Int                 unbounded integers
Float               double precision
Cyclic 12           integers mod 12 — arithmetic wraps
0 .. 9              a bounded range
Char, String        `String` is an alias for `List Char`
Bool, ()            and `Void`, which nothing inhabits
(a, b)              tuples, up to 16 wide
[a] or List a       lists
{a} or Set a        sets — see §5
[: a :] or Score a  scores — see §7
```

### Operators

Operators are ordinary definitions with a fixity.  You can declare your own:

```
infixl 6 <+>

(<+>) : Int -> Int -> Int
(<+>) a b = a + b + 1
```

`->` and `~>` are the two you may *not* redeclare — they are type syntax.

The prelude defines one of its own, and it is the one worth knowing before
you need it: **`@` is composition**.  `(f @ g) x` is `f (g x)`, it reads
right to left, and at `infixr 9` it binds tighter than anything you would
write it beside — so `gain 0.5 @ softClip` is a function you can pass
around without a parenthesis in sight.

And the other direction: **any name in backticks is an operator**, so a
function whose two arguments read better on either side of it can be
written that way without being defined twice.

```
substrate = moveXY 60 80 fader `over` moveXY 140 80 meter
```

`` x `over` y `` *is* `over x y` — the same definition, applied the same
way — so a local, a constructor and an implicit's `using` all behave as
they do anywhere else.  Undeclared it binds tightly and to the left, like
any operator nobody has given a fixity; ``infixr 5 `pair` `` says
otherwise.

### Let

```
main : Int
main = let x = 5 in x + 1

main : Int
main = letrec f = (n => ...) in f 3      -- recursive
```

There is a third binder, `given`, which binds a name *and* makes it an
implicit parameter of everything in its body.  It has its own section —
§4, "Implicit parameters".

---

## 4. Types

Inference is Hindley–Milner with `let`-generalisation.  Two things about it
are worth knowing early.

### A signature is a promise, not a hint

When you write a signature, its type variables become **rigid**: they stand
for whatever the caller picks, and the body may not decide otherwise.

```
f : a -> Int
f x = x + 1        -- rejected: `a` is the caller's choice, not `Int`
```

Without the signature this would infer `Int -> Int` and be accepted.  So a
signature can turn a working definition into an error — that is the point,
and it is why signatures are worth writing.

### Classes

Ordinary single-parameter classes with superclasses, dictionary passing,
and associated types:

```
class Container c where
    type Elem c
    empty : c
    insert : Elem c -> c -> c
```

Instances may carry a context (`instance (Eq a) => Eq (List a)`).  Overlap
and the Paterson conditions are checked.  Multi-parameter classes are not
supported.

### The two arrows — the idea that matters

Gestate has **two** function arrows, and this is the single most important
thing to understand about it.

```
A -> B      the argument is used *discretely*
A ~> B      the argument is used *monotonically*
```

`A -> B` is the ordinary one.  Its argument may be used any way at all:
compared with `==`, put in a set, boxed, pattern-matched, duplicated,
ignored.

`A ~> B` promises something narrower: **if the argument grows, the result
grows.**  Nothing inside may inspect the argument in a way that could go
*down* when the argument goes up.

Most of the time you will not notice, because the two coincide at any type
whose order is equality — `Int`, `Char`, `Bool`, every data type.  At those
types "grows" means "is the same", and every function respects it.

The distinction bites exactly where a type has a real order, which in
practice means **sets** (ordered by inclusion) and products of them.  That
is §5.

**How to think about it.**  Read `~>` as "grows with", and `->` as "may do
anything".  Read `Box A` as *"a value of type `A` that I promise not to
vary"* — it is what lets a function be used discretely in a place that
otherwise demands monotonicity.  When the compiler tells you

> 'r' is a monotone variable and cannot be used in the argument of an
> ordinary (`->`) function

it means: you are inside a fixed point, `r` is the thing being grown, and
you tried to hand it to something that might not respect that growth.

### Implicit parameters

Some values are ambient.  A tick resolution, a tempo, a key signature, a
sample rate: every function in a whole layer of the program wants one, no
function in that layer has anything interesting to say about it, and
threading it by hand means adding a parameter to a dozen definitions that
only pass it along.

Three declarations, and they are the whole feature.  You name the implicit
once, a definition marks that it needs it, and a caller somewhere further
out supplies it.

```
implicit ppq : Int                    -- the name exists, and is an Int

quarter : Int
quarter (using ppq) = ppq

bar : Int
bar = quarter * 4

main : Int
main = given ppq = 96 in bar          -- 384
```

Read them as three:

* **`implicit ppq : Int`** at the top level means *"`ppq` is a name the
  program threads around, and it is an `Int`."*  Implicits are resolved by
  *name*, so a name's type is a fact about the program rather than about
  any one function; this is the one place it is written.
* **`(using ppq)`** on a definition means *"my body says `ppq`, and I am
  not going to tell you where it comes from."*
* **`given ppq = 96 in e`** means *"inside `e`, it comes from here."*

Notice what the signatures do *not* say.  `quarter : Int` — not
`Int -> Int` — even though `ppq` really does arrive as a hidden first
argument.  `bar : Int` likewise.  That is deliberate: a signature says what
a definition *is*, and the requirement is inferred, so putting it in the
signature would mean restating at every level something the compiler
already worked out.  Add a `(using …)` deep in a library and nothing above
it changes type.

The whole point is the middle line.  `bar` never writes `ppq` and its
signature never mentions it, yet `bar` works — because `bar` calls
`quarter`, and a caller of something that needs `ppq` needs `ppq` too.

**The rule: requirements travel up the call graph.**  The compiler computes,
for every definition, the implicits its body names *plus* the implicits
everything it calls needs, and keeps going until nothing changes.  So a
requirement introduced deep in a library surfaces at every caller
automatically, however many levels up that is.  You do not restate it, and
you cannot forget to.

`given` is where the travelling stops.  A name bound by a `given` is
supplied, so it is not passed further out:

```
inner : Int
inner = given n = 3 in double         -- `inner` needs nothing

main : Int
main = inner + 1                      -- so `main` needs nothing either
```

That is the difference between `given` and `let`.  A `let` binds a name for
the expressions that *mention* it; a `given` binds it for the expressions
that *reach* it, however indirectly.  In every other respect `given` is
`let` — it binds several names at once, the right-hand sides are evaluated
outside the scope it introduces, and an inner `given` shadows an outer one.

```
main = given w = 3, h = 4 in area           -- comma
main = given w = 3; h = 4 in area           -- or semicolon
main = given                                -- or a layout block
    w = 3
    h = 4
  in area
```

A definition that needs several writes them in one group, and may take
ordinary parameters after — the ordinary ones are the ones in the
signature:

```
implicit w : Int
implicit h : Int

scale : Int -> Int
scale (using w h) k = w * h * k
```

**You cannot leave one unfilled.**  If a requirement propagates all the way
to `main` and nothing supplied it, the program is rejected before it runs:

```
> unfilled implicit: `ppq` (required by `quarter`) reaches `main`, and
> nothing supplies it.  Bind it with `given ppq = … in …` somewhere the
> use is inside
```

There is no default and no runtime failure to discover later.  Either every
implicit is bound on every path that needs it, or the program does not
compile.  The symmetric mistake is caught too — a `(using ppq)` with no
`implicit ppq : …` above it is rejected at the definition rather than
becoming a fresh implicit that nothing could ever supply.

**How to think about it.**  An implicit is a parameter you did not write,
threaded by the compiler along the calls you did write.  That is exactly
what it costs, too: `given` is not dynamic scoping in the mutable sense —
nothing is looked up at run time, and there is no stack of bindings to
inspect.  The propagation happens once, during compilation, and what runs is
an ordinary function with an ordinary extra argument.

So `implicit ppq : Int` is not a second signature for `quarter`.  It is a
declaration about the *name* `ppq`, and it is what lets every signature in
the chain stay silent about a value all of them are quietly carrying.

---

## 5. Datafun: computing with sets

### Sets and comprehensions

```
main : Set Int
main = {1, 2, 3}

evens : Set Int
evens = {x | x in {1,2,3,4,5,6}, x > 0, x < 5}
```

A comprehension is sugar for `for`:

```
{e | C}     ≡     for (C) {e}
```

where a clause `C` is either a generator `p in e` or a **guard** — a bare
boolean expression.  Several clauses comma-separate, and later ones see
earlier binders.

`for` is not list-comprehension notation with a different bracket.  It is a
**big join**: it runs the body once per element and combines the results
with `∨`.  So `for` needs its result type to be a *semilattice* — something
with a least element and a join.  Sets are the obvious one; a product of
semilattices is another.  `Int` is not, which is why

```
for (x in s) 5      -- rejected: Int has no join
```

is an error rather than a list of fives.

### Fixed points

```
reach : Box (Set (Cyclic 8)) -> Set (Cyclic 8)
reach (Box e) = fix r => e \/ {x + 1 | x in r, x < 7}
```

`fix r => body` is a **least fixed point**: it starts `r` at ⊥ (the empty
set) and iterates until nothing changes.  `\/` is join — union, for sets.

Three restrictions, each for a reason:

- **The body must be monotone in `r`** (that is what `~>` was for).
  Otherwise the iteration may not converge on anything.
- **The type must be a *fixtype*** — a semilattice with no infinite
  ascending chains.  `Set (Cyclic 8)` is one: there are finitely many
  subsets, so the chain must stop.  `Set Int` is not, and `fix` at it is
  rejected, because it could run forever.  This is why the examples use
  `Cyclic n` where you expect `Int`.
- **The argument is boxed.**  `Box e` says `e` will not change during the
  iteration, which is what lets the compiler build the derivative it needs.

`fix` works at a product of semilattices too, which is how a query computes
two relations at once:

```
fix r => (e \/ {x + 1 | x in fstM r, x < 4}, {x + 1 | x in fstM r})
```

Note `fstM`, not `fst`: `fst` takes its argument discretely and so cannot
look at the variable `fix` binds.  A projection *is* monotone (a product is
ordered componentwise), so `fstM`/`sndM` are the same functions at the
arrow that says so.

### It is incremental, and you get that for free

The compiler derives your query and iterates using only what *changed* on
each round rather than recomputing the whole relation.  This is called
seminaïve evaluation and it is entirely automatic — there is nothing to
switch on and nothing in the surface language that mentions it.

### The two booleans

Gestate has both:

- **`Bool`** — the ordinary two-constructor type.  `==` returns it, `case`
  analyses it.  It is *discretely* ordered: `True` and `False` are simply
  different.
- **`Prop`** — Datafun's boolean, which is `{()}`: `{}` is false, `{()}` is
  true, `\/` is or.  It is a *semilattice*, so truth can **grow**.

Why both?  Because a predicate whose truth grows as a relation grows is
exactly what a Datalog query needs, and `Bool` cannot express it:

```
member : Box Int -> {Int} ~> Prop      -- monotone in the set
```

The same signature returning `Bool` would need the set discretely, and
would be unusable under `fix`.

A comprehension guard accepts either, through a one-method class `Guard`.
To go the other way — to *observe* a `Prop` — use `holds` (or the primitive
`empty?`).  Both take their argument discretely, so you cannot watch a
fixed point converge from inside it.

**How to think about it.**  `Bool` answers questions about data you already
have.  `Prop` answers questions about data still being derived.

### What you give up

Datafun-typed code is deliberately **monomorphic**.  Set operations are
generated per concrete element type, so a signature polymorphic in a set's
element type is rejected — with a message saying so:

```
f : {a} ~> {a}       -- rejected
```

Drop the signature and let the use site determine the type, or name a
concrete one.  Nothing else in the language is restricted this way.

---

## 6. FRP: computing over time

### The shape of it

```
c : Chan Int                 an input
c = chan

ticks : Sig Int              a signal — a value that changes over time
ticks = 0 ::: mkSig (wait c)
```

`head s` is the value *now*.  `tail s` is the signal *from the next instant
onward* — and here is the thing to get right:

> **A signal is not a stream.**  `tail s` is not "the rest of a list".  A
> `Sig A` is a heap cell holding the current value, and when time advances
> the cell is **overwritten in place**.  The old value becomes unreachable
> immediately.

That is the entire point of the design.  A stream-based FRP retains every
value it has ever produced unless you are careful; this one cannot, because
there is nowhere for old values to live.

### The two "later" modalities

Two types describe values that are not available yet:

```
FaL A   (written ⃝∀A in the paper)   available at *every* future instant
ExL A   (written ⃝∃A)                available at *some* future instant
```

`delay : A -> FaL A` makes a value that will be there next instant.
`wait c : ExL A` is a value that arrives when channel `c` fires.
`watch s : ExL A` fires when a partial signal `s` becomes `Just`.
`sync a b` waits for either.

The applicative operators pair them up: `<*>` applies a `FaL` function to a
`FaL` argument, `<@>` applies a `FaL` function to an `ExL` argument, and
`f |> x` is sugar for `delay f <@> x`.

### Guarded recursion

A signal defined in terms of itself must be *productive* — it must not need
its own value in order to produce it.  The rule is syntactic: **every
recursive call sits under a `delay`.**

```
map : (a -> b) -> Sig a -> Sig b
map = gfix q => (f s => f (head s) ::: (delay (q2 => q2 f) <*> q <@> tail s))
```

You will usually write this with `gfix` as above.  A plain recursive
definition whose calls are all under `delay` is rewritten into one
automatically.

### Clocks

Every signal has a **clock** — the set of channels (or signals) whose
firing makes it update.  `map f s` inherits `s`'s clock.  A signal built
with `watch` has a *signal* clock, because whether it fires depends on the
value the watched signal holds this instant.

This matters for one reason: the driver sweeps signals in allocation order,
so a signal must be allocated **after** anything it watches, or it reads
the previous instant's value.  If you build dataflow in the order it flows,
this happens naturally.

**How to think about it.**  Ask "what makes this update?" — that is the
clock.  Ask "what does this hold right now?" — that is `head`.  Never ask
"what did this hold before", because nothing does.

### Putting it on a screen

`gestate/gui.py` is a driver for the reactive half, built the same way the
MIDI backend is built for `Score`.  A GUI program supplies
`substrate : Sig Sub`; `gui.ges` is prepended and gives it `Event`, `Sub`
and the combinators.

```
substrate : Sig Sub
substrate = map draw (scan stepBall start events)
```

Fold the events into a state, then draw the state.  There is no callback
and no mutable variable anywhere in it.

A `Sub` is built from `rect`, `circle` and `gap`, composed with `over`,
`row` and `column`, sized with `sized` and `pad`, and placed with `moveXY`.
**Every element has an extent and is placed by its centre**, which is what
lets `row` and `column` arrange things without an alignment argument.
`onTouchX` and `onTouchY` attach a channel, and what arrives is a
**fraction of the element's own extent**, 0 to 1, clamped — so a fader
cannot be dragged off its own track and the number means the same thing
whatever size the picture is.  `examples/gui/bounce.ges` is a whole
application in about forty lines.

`scan` is the piece that makes this possible, and it is nothing but guarded
recursion:

```
scan : (b -> a -> b) -> b -> Sig a -> Sig b
scan = gfix q => (f z s => z ::: (delay (q2 => q2 f (f z (head s))) <*> q <@> tail s))
```

The recursive call sits under a `delay`, so the compiler knows the signal is
productive — it always has a next value and cannot deadlock waiting for its
own.  And because a signal is a cell overwritten in place, the ball's past
positions are not retained anywhere.  Those two properties together are the
thing FRP usually has to be careful about, and here they are the type
system's job.

### Putting it on a speaker

The other driver of the same half is sound.  A synth defines
`sound : Sig Float` — one sample per instant — and
`python -m gestate.audioperform` renders it to a `.wav`, while
`python -m gestate.workbench` plays it and reloads it while you edit.
The combinators (`sineOf`, `lowpass`, `adsr` and the rest) live in
`audio.ges` and `synth.ges`, and every one is in `doc/ref/`; how a
`Sig Float` becomes a flat graph and then machine code is
`spec/liveaudio.md`'s story, not this manual's.

### Why the two halves do not interfere

`Sig`, `Chan`, `FaL` and `ExL` are simply **not in** the grammars that
define what may be a set element, a joinable value, or a fixed-point type.
So `{someSignal}`, `signal \/ x` and `fix` at a signal type are rejected
with no special case anywhere — the restriction falls out of the type
grammar rather than being enforced by a check.

---

## 7. Music

A `[: A :]` (equivalently `Score A`) is a **box-layout tree** carrying a
payload of type `A`.  It is not a list of events; the list comes out at the
end.

```
'60                     a note carrying 60, one beat long
r                       a rest, one beat
a ++ b                  sequence
a || b                  overlay — both in the same span
at n s                  offset `s` by `n` ticks
|< s   /   s >|         sugar for `at (-ticksPerBeat)` / `at ticksPerBeat`
s |* k   /   s |/ k     scale the duration
reverse s               retrograde — the phrase backwards
s >>= f                 substitute a score for each unassigned note
```

A beat is **`ticksPerBeat` = 96 ticks**, chosen because it divides by 2, 3,
4, 6, 8, 12, 16, 24, 32 and 48 — so every division you are likely to write
is exact.

`'x` is `pure` — the same mark makes `[x]` at a list and `Just x` at a
`Maybe`; which one you get is whatever the surrounding signature asks for,
so **write the signature** on a phrase.

`>>=` and `'` are the two halves of the prelude's **`Monad`** class, and
the language carries `do` sugar over it (`spec/monad.md`):

```
walk : Maybe Int
walk = do
    x <- Just 4
    y <- Just 5
    '(x + y)
```

An item `p <- e` binds, `name = e` is a pure binding (a `let`, no monad
involved), a bare item's value is dropped, and the **last item is the
block's value** — there is no `return`, because `'` is already `pure`.
One line holds several items with `;`.  Over a score, remember that `do`
reads as *substitution* — "for each note" — not as time passing.

**`reverse` is retrograde**, and it reverses *time* rather than the tree:
an overlay is left-aligned, so `reverse (a || b)` gives you two voices that
now **end** together, which is what a retrograde of two unequal voices
means.

### Duration and extent

Every score has two measurements and they are not the same:

- its **duration** — how far `++` advances past it;
- its **extent** — where its content actually sits.

This is a font's *advance width* versus its *bounding box*.  `at` moves the
extent and leaves the duration alone, which is what makes an early drum
fill work:

```
groove ++ at (0 - ticksPerBeat) fill ++ crash
```

The fill starts a beat before the groove ends, overlapping it — and the
crash lands exactly where it would have without the offset.  The fill is
early; the grid is not.

### Instruments

An instrument is a function from a note's payload to a committed score, and
you apply it with `>>=`:

```
score : [: Void :]
score = melody >>= prog 0        -- General MIDI program 0
drums : [: Void :]
drums = pattern >>= percussion         -- the GM kit; needs no program
```

Why `[: Void :]`?  Because `[: a :]` means "a score whose *unassigned* notes
carry `a`", and an instrument's result has none left — so it is parametric,
and `Void`, which nothing inhabits, says "there are no unassigned notes
here".  **Performability is a typing property**: a score with notes you
forgot to instrument simply will not type against `layout`.

A second bind cannot touch an already-committed note, so "the instrument
already chosen wins" needs no runtime marker.

### Running it

```
score : [: Void :]
bpm   : Int
```

then `python -m gestate.midi song.ges`.  Onsets may be negative (`at` can
place content before the origin); the *renderer* normalises, because a grid
view might want to show that a fill precedes bar 1 while a MIDI file cannot
hold a negative timestamp.

A synth can perform a score too — `voices` banks stand as instruments, and
`python -m gestate.audioperform` plays the piece on them.  There the tempo
need not be a constant: `tempo : List Envelope` in place of `bpm` makes
the beat clock follow a curve, and stating a tempo either way puts
`beat : Sig Float` — what time it is in beats, at audio rate — in scope
for the synth to read.  `doc/ref/audio.md` has the details.

The music definitions live in `gestate/music.ges`, which the MIDI backend
prepends to your program.  They are deliberately not in the core prelude:
they declare eight constructors, and since a constructor's tag is its
position, merging them would renumber `Nil` and `Cons` for every program in
the language.

---

## 8. Finding your way around

```
gestate/          the compiler
  syntax/           tokenizer, parser, fixity resolution
  declarations.py   classify a module: types, classes, instances, aliases
  infer.py          Hindley–Milner; unify.py, constraint.py, elaborate.py
  seminaive.py      the ϕ/δ transform — Datafun's incrementality
  helpers.py        the per-type set operations it generates
  reactive.py       the FRP driver
  gmachine.py       the evaluator
  prelude.ges       the standard library
  music.ges         the music library (loaded only by the MIDI backend)
  midi.py           the MIDI renderer, and its CLI
  signal.ges        the signal combinators both reactive backends share
  synth.ges         the synthesis library — voices, adsr, the knobs
  envexpand.py      an `on` over known points becomes a comparison tree
  reference.py      generates doc/ref/ from the libraries' own prose
  gui.py            the GUI backend (pygame), with gui.ges
  audio.py          the offline synth renderer (.wav), with audio.ges
  audiograph.py     is this synth in the audio fragment? (liveaudio.md)
  audioir.py        the flat signal graph, and the IR inside its nodes
  audioextract.py   a Sig Float becomes that graph
  audioengine.py    runs a graph — the reference the engine is checked on
  audiollvm.py      the graph becomes LLVM IR — 593x real time
  audiomidi.py      MIDI CC as control-rate parameters, and notes
  audioschedule.py  control changes over time — what makes notes checkable
  audiovoices.py    `voices` — a bank of N copies of one voice
  audioalloc.py     which note goes to which voice
  audioscore.py     a Score, performed by gestate instruments
  audioperform.py   a score on one bank, your hands on another
  audiospans.py     which file and line a graph node was written on
  audiolive.py      the live engine — the sound card, the rebuild, and
                    `migrate` carrying the state across an edit
  audioeditor.py    the editor's model — an instrument, a rebuild worker,
                    a transport, parameters and a keyboard.  No toolkit
  command.ges       what the editor can be asked to do.  The palette is
                    derived from these declarations, so a capability
                    cannot exist without a name, a type and a sentence
  templates/        the language's ideas, ready to paste — one file per
                    idea, its header the description and its body what
                    you get, comments taken off on the way in
  session.py        a gesture becomes a transition and a sentence
  workbench.py      …and the wire to the window.  `python -m
                    gestate.workbench file.ges` is the editor
shell/            the foreign-language hosts — none of them opinionated
  editor/           the window: a persistent rope in Rust, its own loop
  panel/            a substrate becomes a display list, and one painter
                    draws it for both the editor and the plugin
  clap/             the CLAP plugin an exported instrument is
crust/            the G-machine in Rust — the reference is gmachine.py
spec/             the design documents — see below
doc/manual.md     this file
doc/audit.md      what the synth primitives *measure* as, against their
                  docs — the findings, and how to repeat the measurement
doc/ref/          the generated reference — every library name, with its
                  signature and prose; `python -m gestate.reference` remakes it
examples/         programs that run, exercised by the test suite
test/             ~2,075 tests
```

The `spec/` directory is unusually load-bearing, so it is worth knowing
what each file is *for*:

| file | what it answers |
|---|---|
| `syntax.md` | what the surface language is |
| `types.md` | inference, kinds, signatures |
| `typeclasses.md` | classes, instances, dictionary passing |
| `data.md` | Datafun and its compilation, in detail |
| `frp.md` | Rizzo, the driver, the machine |
| `music.md` | what a score is |
| `substrate.md` | the canvas behind the editor — what a `Sub` is |
| `liveaudio.md` | where the project is going: a synth you edit while it sounds |
| `workbench.md` | the editor: why there are no modes, and what a command is |
| `verification.md` | how the half without a sample-for-sample oracle is checked |
| `delaylines.md` | delay lines — the fifth audio node kind |
| `errata.md` | where the specs disagree with the papers, and what was decided — and, at the top, **which three papers those are**, by title and arXiv number |
| `supercomb.md` | the G-machine |

And two files that are not specs but are how the project is steered:

- **`fixme.md`** — every known divergence between implementation and spec,
  over a hundred entries, most resolved, each with the reasoning.  The
  table at the top lists what is still open.
- **`roadmap.md`** — what is left and *why in that order*, plus the rule the
  project is run by:

  > **Do not build what nothing needs.**

  A feature earns its place by having a caller — a program someone wants to
  write, an unmet spec obligation, or a defect it fixes.  "It is in the
  spec" is not a caller.  Several things that look missing are *closed*
  under that rule rather than pending, and say so.

---

## 9. Things that will surprise you

Collected from actually writing programs in it.

**`x.0.1` is not two projections.**  `0.1` lexes as a float, so write
`(x.0).1`.

**Projection needs to know the type.**  `x.N` is resolved from `x`'s type,
not through a class.  Inside a lambda passed to a polymorphic function the
type is not yet known, so destructure instead — the error says so.

**`|*` binds tighter than `++`.**  `a ++ b |* 2` scales `b` alone; to scale
a phrase, parenthesise it — `(a ++ b) |* 2`.  It reads the other way in
older notes and in `music.md`'s history, and was changed because two scaled
groups in a row (`(a) |/ 2 ++ (b) |/ 2` — a bar of eighths) is the common
case and the loose reading broke it silently.

**Lambda and comprehension patterns must be irrefutable** — a variable or a
tuple of them.  A constructor pattern that can fail has nowhere to fail
*to*, so use `case`.

**`fix` at `Set Int` is rejected.**  Use `Cyclic n`.  See §5.

**There is no `if`, and no `where`.**  Use `case` on a `Bool`.

**A music program has no `main`.**  It has `score` and `bpm`, and is read
with `python -m gestate.midi`, not `typecheck`.

**Ambiguous numeric types default to `Int` silently.**  Recorded as
`fixme.md` F32.

**An implicit parameter is invisible in the signature.**  `f (using n) = n`
has type `Int`, and so does every definition that calls it.  Nothing in a
signature tells you an implicit is being threaded — you find out from
`implicit n : …` at the top of the file, or from the error if you forget to
bind one.  That is the trade §4 explains.

---

## 10. Asking the compiler

Three questions, each answered about the program *as compiled* — the type
from inference, the position from the parser — so an editor showing them
cannot drift from what the compiler thinks.

```
python -m gestate.typecheck f.ges --query total   # type, place, and the prose
python -m gestate.typecheck f.ges --holes         # every `_`, typed and placed
python -m gestate.typecheck f.ges --fits "Int"    # what could stand there
```

**`--query NAME`** gives the type, the line it is declared on, and the
comment block immediately above that declaration — a blank line ends the
block, because a comment separated from a declaration is about something
else.  A name with no signature is answered from its definition, and the
reply says which of the two it read.  Constructors count as names.

**`--holes`** reports every `_`.  A hole takes whatever type its context
demands, so the program around it type-checks exactly as if it were filled,
and reading that type back is what says what belongs there.  Positions are
`line:column`, 1-based lines and 0-based columns.

A hole has no *value*, and the evaluator refuses it by name and by position
**when it is reached** — so a program with an unfinished definition runs
everything that does not depend on it.  A `substrate = _` is a file with no
canvas yet, and its synth plays and its piece is read meanwhile; only
drawing it asks the question nobody has answered.

**`--fits TYPE`** lists what in scope could stand where that type is wanted
— exactly, or after n arguments.  It is a separate tool because "what goes
here" is a question about a *type*, and a version of it that only worked
inside a `_` would be one you had to prepare for.  Names that fit
everything — `id`, `const`, `(@)` — are left out: they fit by being
unconstrained rather than by being right.

**And it is in the editor**, because the search has a half with no
command line in it: `typecheck.fits_in_source` takes the type and the
program as text, so the workbench answers about **what is in the window,
unsaved**, rather than about the last save.  `Tab` is the shortcut — the
one bare key the editor has, spent here because a tab is not text in a
language whose layout rule counts columns.  A file that has not got as
far as inference says so, which is the ordinary case while you are still
typing the line that needs the answer.

**`--audio`** puts `signal.ges`, `audio.ges` and `synth.ges` in front, so
`Sig`, `Adsr` and the rest are in scope, `--query adsr` reaches the
paragraph above it in the library, and hole positions are still the ones
your own file has.

---

## 11. Where to go next

If sound is what brought you here, there is a four-course path built for
that: `doc/beginner.md` (synthesis), `doc/intermediate.md` (instruments
and scores), `doc/advanced.md` (the toolkit's own construction) and
`doc/super.md` (a patch book), each with its lessons under `examples/`.

Read `examples/closure.ges` and `examples/music/drums.ges` — between them
they touch most of the language.  Then `spec/data.md` §I if you want to
know how the incrementality actually works, or `spec/frp.md` if you want
the driver.  To look a name up rather than learn in order,
`doc/ref/index.md` is the entrance.

For where the project is going rather than what it is: `spec/liveaudio.md`
states the live-audio architecture and the evidence behind it, and
`roadmap.md` §"Stage 7" says which part is being built next.

If you are going to change something, read the top of `fixme.md` first: it
will tell you whether what you are about to fix is already known, already
decided against, or genuinely open.
