# Surface syntax

This document defines the user-facing syntax of
a functional programming language.

There are syntax samples elsewhere in the specs that are exploratory.
This file defines the entire syntax.

The main goal is a simple, coherent and parseable surface syntax.

Other design goals:

1. Customizable infix/prefix/postfix operators.
   The user can define new operators themselves.
   This feature improves readability when new concepts emerge.
   It would seem to require hand-written tokenizers and parsers though.
2. Parseable by tree-sitter.
   Important for programming tool ecosystem and usability.
   It would seem to require that operator phrases are parsed flat,
   and the fixity is resolved on a post-pass.
3. Offside rule for top-level.
   Important for readability and avoiding excess notation.
   Would also seem to require manual parsing.
4. Comes with a formatter.
   Important for consistent style.
   Would seem to require that comments are preserved during parsing.


## Informal description

The syntax is informally but precisely described.
Anything that is not appearing here is not part of the syntax.

### Lexical format

Whitespaces are ignored.

Words consist of unicode letters or underscore,
followed by unicode letters, underscore and numbers.

    correct5
    Correct_10
    etc

Overall, words starting with uppercase are types or type constructors
while lowercase words are variable names or terms.

Numbers are grouped together, may contain underscore
for clarity (this means only within the number, never as leading or trailing), and
may be followed by decimals and exponential notation:

    100_000.43
    5.2e10
    41e-2
    41e+3

Exponent marker may be `e` or `E`.

A sign character (+ or -) is part of the exponent token if and only if
it directly follows e/E and is itself followed by at least one digit.
Otherwise it tokenizes as a separate symbol.
So 2e-2 is one number, while 2e - 2 is the number 2e minus 2.

`inf` and `nan` are treated as words.
They are ordinary lowercase identifiers (so they may be shadowed);
the standard library binds them to floating-point constants.

If the number starts with `0x`, it's a hexadecimal and may contain a,b,c,d,e,f as extra digits.
Hex digits are case insensitive.
Decimals and exponentials not allowed with hexadecimal syntax.

    0x54ab
    0xFFFF

Strings follow standard notation for strings:

    "string with newline\nfoo"
    "string with tab\t"
    "string with quote \" and backslash\\ and return symbol \r"
    "string with unicode \u0543"

We don't have string interpolation syntax for now.

Note that we don't have separate syntax for characters or bytes. They're resolved by numbers.

The single quote `'` is treated as a symbol.

Here are reserved characters:
```
(  )  [  ]  {  }  ,  ;  :  :: ::: . .. :=  =  ->  => |
```

Reserved words are:

    class instance case let letrec where in for of type kind gfix fix unbox given using
    deriving implicit Box internal do

Note that `=` and `|` may also appear as a part of a symbol.
Otherwise these are special characters and should be always separated.

Parenthesis are always grouped together.

Symbols are all the remaining characters except the `#`.
The symbols characters not separated by whitespace are always joined together.

There are no negative numeric literals. Unary operator eg. `(-5)` is parsed as
prefix `-` applied to literal `5`.

### Fixity declarations

Fixity is declared through mode followed by a number between 0 and 20, and symbol.
Negative fixities are not accepted.
Examples:

    infixl  4  ++                       # left-associative, precedence 4
    infixr  5  ::                       # right-associative, precedence 5
    infix   6  ==                       # non-associative, precedence 6
    prefix  9  '                        # prefix, precedence 9 (highest)
    postfix 7  >|                       # postfix, precedence 7
    infixl  3  6  <@                    # 3 on the left, 6 on the right

Higher precedence number binds tighter.

An infix declaration may give **two** precedences.  The first is how the
operator binds to its left, the second to its right; one number means the
same on both sides, which is what an ordinary operator wants.

They differ when the two operands are not the same kind of thing.  `|*`
scales a score by a number: on the left it should be loose, taking a whole
phrase, so that `a ++ b |* 2` scales the sequence; on the right it should be
tight, taking a factor and no more, so that `a ++ b |* 2 ++ c` does not
swallow `c` into the factor.  With one precedence you get one or the other.

`prefix` and `postfix` take one precedence: they have one operand.

Any operator — reserved, default-fixity,
or user-declared — may be parenthesized into a value.
Reserved operators used as values `((->), (:), (:=), (=), (|))`
are accepted only in parenthesized form; bare use of their
reserved characters follows the rules above.

Prefix/postfix operators are parenthesized
into a value through underscore: `(+_)` for prefix and `(_+)` for postfix

### Names used as operators

The mirror of the above: **any name in backticks is an infix operator**,
`x `over` y` for `over x y`.  The tokenizer reads `` `over` `` as the
symbol `over` and nothing downstream knows the difference, so a quoted
name picks up precedence climbing, sections, `infixl`/`infixr`
declarations and the formatter without a rule of its own.  Undeclared, it
binds like any unknown operator — tightly and to the left, which is the
`infixl 9` every other language gives them.

The name may be anything a name can be, including a constructor
(`` a `Cons` b ``) and a local (`` x `f` y `` where `f` is a parameter):
the desugarer builds the application `over x y` and lets every rule about
names apply to it exactly once.

### Default fixity declarations

`->` is the only operator that cannot be overrided, and a program that
declares a fixity for it is **rejected** rather than silently ignored.
`~>` goes with it: both are type syntax rather than expression operators.

`!` — the signal lift — is not in the table below because it is grammar
rather than a declarable operator: the parser binds it to the **next
atom**, in head position and argument position alike, and the
application around it supplies the lifted arguments.  So `!f x` lifts
`f` over `x`, `!(f x)` is the constant signal of the computed value
`f x`, and `!(f x) y` lifts the computed head — the parentheses mean
nothing in themselves; they change which atom follows the marker.
`spec/exclamation.md` records why this is parsed in the grammar and not
resolved by fixity.

| Fixity       | Op       | Meaning                                |
|--------------|----------|----------------------------------------|
| `infixr 5`   | `::`     | list cons                              |
| `infixl 4`   | `++`     | list append / music sequence           |
| `infixl 2`   | `\|\|`   | boolean or / music overlay             |
| `infixl 6`   | `==`, `/=`| equality / inequality (Eq class)      |
| `infixl 6`   | `<`, `>`, `<=`, `>=` | ordering (Ord class)       |
| `infixl 7`   | `+`, `-`  | numeric                               |
| `prefix 7`   | `+`, `-`  | numeric unary                         |
| `infixl 8`   | `*`, `/`, `%` | numeric — `%` is remainder        |
| `infixr 9`   | `^`       | power                                 |
| `infixr 9`   | `@`       | function composition (the prelude's `(@)`) |
| `infixr 0`   | `$`       | apply (lowest)                        |
| `infixl 1`   | `>>=`, `>>`| monadic bind (where applicable)      |
| `infixl 6`   | `|*`, `|/`| music duration multiply/divide — tighter than `++` |
| `prefix 6`   | `\|<`     | music offset, one beat earlier        |
| `postfix 6`  | `>\|`     | music offset, one beat later          |
| `prefix 9`   | `'`       | music unit note                       |
| `infixr 1`   | `~>`      | monotone function arrow (type space)  |
| `infixl 3`   | `\/`      | semilattice join (Datafun's `∨`)      |
| `infixr 5`   | `:::`     | Rizzo Sig-cons                        |
| `infixl 4`   | `<*>`     | Rizzo `⊛`, ⃝∀ applicative action       |
| `infixl 4`   | `<@>`     | Rizzo `5`, ⃝∀/⃝∃ applicative action    |
| `infixl 4`   | `\|>`     | Rizzo `▷`, sugar for `delay f <@> x`  |
| `infixl 7`   | `..`      | bounded-integer range (`4 .. 30`)     |

The three music-grouping operators sit where they do so that
`music.md`'s worked example groups as it says: overlay (2) is looser than
duration scaling (3), which is looser than sequencing (4).  `++` cannot
move up to make room — it would land on `::`/`:::` at 5, and an `infixl`
operator sharing a precedence with an `infixr` one is ambiguous.

By default there are no words with fixity.
Though fixity declarations can be also given to words,
one should be careful with them.

### Functions

Function type is described by an arrow:

    Int -> Bool

`->` has fixed `infixr 1` precedence in *type* space and is not
user-customizable (operators live in expression space; type-space
arrow is a single reserved form).

There is a second arrow, `~>`, at the same fixity:

    Set Int ~> Set Int

`A ~> B` is a **monotone** function: its argument is a monotone variable,
and the function must respect the ordering on `A`.  `A -> B` is the
ordinary **discrete** arrow — Datafun's `□A → B` — whose argument may be
used any way at all.  Both compile to the same thing; the difference is a
typing discipline.

Two consequences you will meet:

- `fix` takes `Box (L ~> L)`.  Monotonicity is why the least fixed point
  exists at all: the chain `⊥ ⩽ f ⊥ ⩽ f (f ⊥) ⩽ …` only ascends if `f`
  respects the order.
- A monotone variable may not be boxed, compared, put in a set literal,
  or passed to a `->` function — those are the *non-monotone* positions,
  and a monotone variable is not in scope inside one.  Bind it discretely
  first (`unbox`, or take it through `->`).

The distinction says nothing at a type whose order is equality — `Int`,
`Bool`, `Sig A`, `Chan A`, and anything built from them — because every
function out of a discrete order is monotone.  `{A}` is ordered by
inclusion, so sets are where it has teeth, and ordinary code never
notices it.

Functions are formed by variables (parsed as values),
separated by `=>` from the function body.

    x y => x

Function calls are formed from consecutive values:

    f 1 2 3

User may pattern match inside function arguments:

    (SomeRecord x) => x

### Type declarations and aliases

Record types and abstract datatypes use the same syntax.

Record type is declared when there's only one constructor.

    SomeRecord a := SomeRecord a a

Records are accessed through pattern matching.

    rec.0
    rec.1

How this works in practice? Each digit, up to 15, forms a type class that is filled by the record.
eg. The signature for digit attribute is `(Attr4 a) => a -> Attr4 a`

Projection rec.N desugars to application of the member (.)
of an AttrN class for the corresponding digit.
Each digit 0–15 forms a type class; projection rec.N requires (AttrN a). We define:

    class Attr4 a where
        type Attr4 a
        (.4) : a -> Attr4 a

ADT is declared when there are many constructors.
There are no ADTs with only one constructor.

    Maybe a := Nothing
             | Just a

ADTs are accessed through pattern matching and case statement:

    case x of
      Nothing -> 5
      Just y  -> y + 10

Type aliases are there for improving readability of code.
They're denoted like this:

    type Arity = Int

The ADT declaration also supports constraints to be supplied in type:

    ShowThis a := (Show a) => ShowThis a

### Builtin types

Integers are constructed with a number and processed by functions.
There are three types of integers. Bounded integer type is constructed as follows:

    4 .. 30
    10 .. 100

Cyclic integers, eg. modular numbers are described with:

    Cyclic 12
    Cyclic 7

Ordinary integers are described as `Int`

Tuples are commas within parentheses. Both type and term constructors use the same syntax:

    (Int, Int, Int)
    (x, y, z)

Tuples are deconstructed by pattern matching and projection:

    x.0
    x.1

Tuples use same AttrN mechanism as records do.
Therefore tuples may only go up to 16 slots through projection.

The zero-width tuple `()` is the unit type, fig. 2.1's `1`, in both type and
term space:

    ()          # the type with one value, and that value

There is no one-width tuple: `(A)` is just `A`.  Unit is an eqtype, a finite
eqtype, a semilattice and a fixtype, so `{()}` is a set that may be joined
and fixed — which is what the prelude alias

    type Prop = {()}

names.  `Prop` is Datafun's `bool`: `{}` is false, `{()}` is true, `\/` is
or, and `for (u in p) e` is the one-sided conditional.  It is a *different*
type from `Bool`, which is the ordinary two-constructor ADT that `==`
returns and `case` analyses; `errata.md` D5 records why gestate has both.

Lists are provided with special syntax, type constructors:

    [a]

They're constructed with following list syntax:

    []
    [1,2,3]
    [1,2|x]
    5 :: ys

And are accessed through pattern matching:

    case xs of
      [] -> 5
      x :: xs -> x

Score is a notation for musical data notation.
Score's type constructor is marked in special syntax as well:

    [: a :]

Score values are produced exclusively by user-defined functions
whose return type is `[: a :]`,
the built-in core supplies no Score constructors.

Although the syntax is similar, Score doesn't interact with Sig at all.


### Type constraints

Type constraints are formed from parenthesised list of value constraints
followed by `=>` followed by a value.

    (Ord a) => a
    (Ord a, Eq a) => a

### Kind annotation

Types may be annotated with kind declarations:

    kind Cyclic : Int -> Type
    kind Maybe : Type -> Type
    kind Either : Type -> Type -> Type

### Class and instance

'class', 'type', 'where' and 'instance' keywords are provided.
Examples tell more than enough:

    class Eq a where
      (==) : a -> a -> Bool
      (/=) : a -> a -> Bool
      x /= y = not (x == y)                  # default method
    
    instance Eq Int where
      x == y = intEq x y
    
    class Collection c where
      type Elem c                            # associated type
      insert : Elem c -> c -> c

    class Collection2 c where
      type Elem2 c : Type                    # associated type with kind annotation
      insert : Elem c -> c -> c
    
    instance Collection [a] where
      type Elem [a] = a
      insert = (::)

### Let and letrec and given

Also described by an example:

    let x = 5; y = 10 in this thing
    letrec x = 5; y = 10 in this thing
    given x = 5; y = 10 in this thing

    let x = 5
        y = 10
    in this thing

Mixed usage of semicolons and indentation not allowed.

### Continuation lines

An indented line normally opens a layout block.  Two shapes are read
instead as a continuation of the line above — one logical line, with no
block and no layout tokens:

* the line **begins with an operator** (a symbol, or `->`, `::`, `:::`,
  `..`), which nothing starting a new declaration, binding or alternative
  ever does;
* the line **begins with `(`**, the usual way a long application is broken;
* the previous line **ends with `=`**, which only a definition body can
  follow;
* the line **begins with a word, number or constructor and binds nothing**
  — no top-level `=` before its end.  That last clause is what separates a
  continuation from a block item, which one token of lookahead cannot do:
  `y = 6` under a `let` and `2` under a broken application both start with
  an ordinary token, and only the `=` tells them apart.

**Inside a bracket the offside rule is suspended entirely.**  A newline
deeper in brackets than the block it sits in is not a newline, so a list, a
tuple or a parenthesised expression spans as many lines as it needs.  The
comparison is against the bracket depth *the current block began at*, not
against zero, because a block may be opened inside a bracket — `foldr (x b
=> case p x of` — and inside that block the rule is in force again.

None of these applies directly after a **block opener** — `of`, `where`,
`let`, `letrec`, `given` — where the indented line is the block's first
item whatever it starts with.  That is what a `(` continuation needs: a
case alternative may be `(a, b) -> …` and a class member may be `(==) : …`,
and both would otherwise be indistinguishable from one.

        melody = '69 ++ '71
              ++ '72 ++ '74

        f x =
            x + 1

        showFloat x = append (showNat (floor x))
                             (append "." (digits x))

Anything else opens a block, which is what keeps a `let` whose first
binding is on the `let` line and whose later ones are indented beneath it
working: `y = 6` carries an `=`, so it is an item and still begins one.

A line indented *the same* as the one above is never a continuation, even
if it begins with an operator: it is the next item.

### Implicits: `implicit`, `using`, `given`

An implicit parameter is a value threaded along the call graph without
being written at any call site.  Three declarations make one:

    implicit ppq : Int              -- the name, and its type, once

    quarter : Int
    quarter (using ppq) = ppq       -- a definition that names it

    main : Int
    main = given ppq = 96 in bar    -- a caller that supplies it

`given` behaves like `let` — it binds several names at once, with commas,
semicolons or a layout block; the right-hand sides are outside the scope it
introduces; an inner `given` shadows an outer one — except that the names
it binds also become implicits.

**Requirements propagate.**  A definition needs the implicits its own body
names *plus* those of everything it calls, to a least fixed point.  So

    bar : Int
    bar = quarter * 4

needs `ppq` although it never writes it, and `bar`'s callers need it in
turn, until a `given` supplies it.  That propagation is what makes the
scope dynamic rather than a `let` with extra steps.

**Implicits do not appear in signatures.**  `quarter : Int`, not
`Int -> Int`, even though `ppq` arrives as a leading argument; `bar : Int`
likewise.  The requirement is inferred, so writing it into every signature
along the chain would restate what the compiler already derived, and would
make a `(using …)` added deep in a library change the type of everything
above it.  The type of an implicit is a fact about the *name*, which is
what `implicit n : τ` states.  An earlier draft of this section proposed a
context — `maxOf : (ord Ordering t, test Int) => t -> t -> t` — which is
the same information restated per definition; it was not adopted.

An `implicit` declaration may not carry a class context: a `given` passes a
value, not a dictionary, so there would be nowhere to discharge it.

**Two errors are possible, and both are compile-time.**  A `(using n)`
whose `n` has no `implicit n : τ` is rejected at the definition.  An
implicit that propagates as far as `main` with nothing supplying it is
rejected there — a program that leaves an implicit unfilled cannot be
constructed.

### Toplevel declarations

Toplevel consists of fixity declarations, supercombinator declarations and type declarations.

    x : Int
    x = 5

    choose5 : Maybe Int -> Int
    choose5 Nothing = 5
    choose5 (Just x) = x

 * Type declaration is a symbol followed by colon mark, and a value.
 * Supercombinator declaration is term, followed by sequence of patterns, followed by equal sign, and another sequence of values.
 * Fixity declaration is described earlier in this document.
 * Implicit declaration is the word `implicit`, a name, a colon mark, and a
   type; see "Implicits" above.  It declares a name, not a definition, so
   nothing else in the file refers to it by that shape.

Blank lines are disregarded in syntax, although
it is assumed they are used for clairity in places.

Syntax doesn't address whether supercombinators should be grouped or not.
But the layer coming after syntax will require that type declaration
for term comes first, and that supercombinators are grouped together.

There are no "module" or "import" declarations.
They would go to the top but they're not present.
This omission is because I may add them,
but not necessarily inside the source files themselves.

### Datafun-originated surface syntax

Datafun-style we provide set type constructors:

    {a}

and literals:

    {}
    {1}
    {1, 2, 3}

Also eq sets type and ordinary constructors are available:

    {: :}
    {: a :}
    {: a, c :}

Box introduction and elimination syntax.
It is a type constructor, a term constructor, and a **pattern**:

    Box type
    Box expr
    Box pat                 # box pattern — Datafun's `[p]`
    unbox pat = expr in expr

`Box p` is irrefutable (every `Box A` matches) and binds `p`'s variables
discretely, the same as `unbox`.  It exists because `unbox` is an
*expression* form and so cannot appear in a binder:

    closure (Box e) = ...   -- rather than  closure be = unbox e = be in ...

Datafun spells this `[p]`; gestate cannot, because `[p]` is already a
one-element list pattern.

For-comprehension.  A `for` takes one or more comma-separated **clauses**,
which are thesis fig. 2.2's `C ::= p ∈ e | e | C,D`:

    for (pat in expr) expr                   # a generator
    for (pat in expr, pat2 in expr2) expr    # two, nested left to right
    for (expr) expr                          # a guard: the one-sided conditional
    for (pat in expr, expr) expr             # both

`for (C, D) e` means `for (C) for (D) e`, so a later clause may mention an
earlier clause's binders.  A generator's pattern must be **irrefutable** —
a variable, or a tuple of them — because fig. 2.2 gives a failed match the
value ⊥ and ⊥ is type-directed, so there is nothing for the desugarer to
build.  Filter with a guard clause instead.

A **guard clause** is a bare expression, and it is the one-sided
conditional: the body contributes to the result when the guard holds and ⊥
when it does not.  A guard may be either boolean — `Bool` or `Prop` —
because it is passed through the class method `guard : a ~> Prop`, so
`x == y` and a `Prop`-valued predicate are both accepted (`errata.md` D5).

The **comprehension** is sugar for exactly that:

    {expr | C}        # ≡  for (C) {expr}

which is what lets a Datalog query read like one:

    closure be = unbox e = be in
        fix Box (r => e \/ {(x, w) | (x, y) in r, (z, w) in e, y == z})

Semilattice join and bottom:

    e \/ f          # Datafun's `e ∨ f`; both sides are the same semilattice
    {}              # ⊥ at a set type is the empty set literal

Observing a `Prop` — the non-monotone direction, out to `Bool`:

    empty? expr             # primitive: is this `Prop` false?
    holds expr              # prelude: `not (empty? p)`

Both take their argument at the plain `->`, which *is* `□A -> B`, so a
fixpoint variable cannot be observed while it converges.  `empty?` has to
be a primitive: `for` eliminates only into a semilattice and `Bool` is not
one, so no definition in the language reaches it.

A trailing `?` is part of an identifier, which is what lets `empty?` be one
name.  Only one, and only at the end — `empty??` is `empty?` then `?` — and
it binds greedily, so `a?b` reads as `a?` applied to `b` and an infix `?`
needs spaces.

Semilattice fixed point:

    fix expr
    fix pat => expr         # sugar for `fix Box (pat => expr)`

`fix` takes a `Box (L ~> L)` where `L` is a **fixtype**: a set of *finite*
eqtypes, or a tuple of those.  `{Int}` is not one — `Int` is an eqtype
but has infinitely many values, so the set has infinite ascending chains
and the iteration need not stabilise.  Use a bounded element type
(`Cyclic n`) and the same query terminates:

    reach : Box (Set (Cyclic 4)) -> Set (Cyclic 4)
    reach (Box s) = fix r => s \/ {x + 1 | x in r}

which is the same as, and was until the sugars landed spelled

    reach bs = unbox s = bs in fix Box (r => s \/ (for (x in r) {x + 1}))

Sets require an eqtype element, and `for` eliminates into a semilattice.
The FRP types are in none of those grammars, so `{someSignal}`,
`someSig \/ x` and `fix` at a signal type are all rejected — which is what
keeps the two halves of the language from interfering.

### Rizzo-originated surface syntax

We provide guarded recursion:

    gfix var => expr

And several FRP-related type constructors:

    Sig type       # signal
    Chan type      # channel
    FaL type       # forall-later modality  (⃝∀)
    ExL type       # exists-later modality  (⃝∃)

The two later modalities are distinct.  `FaL A` is available whenever
*any* clock ticks; `ExL A` fires on its own clock.  There is no coercion
between them — `<@>` is the only bridge, and it needs an `ExL` argument
to supply the clock.  Two further type constructors are built in because
the primitives below name them: `Maybe a` (`Nothing | Just a`), which
`watch` observes, and `Sync a b` (`SyncLeft a | SyncRight b | SyncBoth a
b`), which `sync` returns.  Neither may be redeclared.

The primitives, at Rizzo fig. 3's types:

    delay : a -> FaL a                 (<*>)  : FaL (a -> b) -> FaL a -> FaL b
    never : ExL a                      (<@>)  : FaL (a -> b) -> ExL a -> ExL b
    wait  : Chan a -> ExL a            (|>)   : (a -> b) -> ExL a -> ExL b
    watch : Sig (Maybe a) -> ExL a     head   : Sig a -> a
    chan  : Chan a                     tail   : Sig a -> ExL (Sig a)
    sync  : ExL a -> ExL b -> ExL (Sync a b)
    (:::) : a -> ExL (Sig a) -> Sig a

`f |> x` is sugar for `delay f <@> x`; `delay`, `head`, `tail`, `chan`
and the rest are ordinary functions.

`gfix x => t` binds `x : FaL A` in a body of type `A`, so a recursive
occurrence can only be consumed through `<*>`/`<@>` — which is exactly
the guard that makes the definition productive.

You rarely write it.  A definition whose recursive calls all sit under a
`delay` is desugared into one automatically (paper §2.4):

    f x₁ … xₙ = C[delay t₁, …, delay tₙ]          (f not free in C)
  ⇝ f = gfix r => (x₁ … xₙ => C[delay (r' => t₁[r'/f]) <*> r, …])

So `mkSig d = (x => x ::: mkSig d) |> d` compiles to the explicit fixed
point given below, and the recursive `mkSig` becomes the fixed point's own
binder.  The rule fires only when at least one recursive call is under a
`delay`, so ordinary recursion is untouched; if *some* calls are guarded
and some are not the definition is rejected, because it cannot be
productive.

A signal may also be taken apart by pattern:

    map f (x ::: xs) = f x ::: (map f |> xs)

`x ::: xs` is irrefutable — every `Sig A` matches — so it binds rather
than dispatches: `x = head s` and `xs = tail s`.  Note `xs : ExL (Sig A)`,
the *delayed* rest, which is what `|>` expects.  Both parts must be plain
variables; there is nothing to match further.

Small example of the syntax:

    # channel construction
    c : Chan Int
    c = chan

    # signal construction
    sig : Sig Int
    sig = x ::: t

    # current value
    v = head sig

    # a constant signal
    const : a -> Sig a
    const x = x ::: never

    # a signal driven by a delayed computation
    mkSig : ExL a -> ExL (Sig a)
    mkSig d = (x => x ::: mkSig d) |> d

    # ... which is sugar for the explicit guarded fixed point
    mkSig = gfix r => (d => delay (r2 x => x ::: r2 d) <*> r <@> d)

    counter : Sig Int
    counter = 0 ::: mkSig (wait c)

Note that `gfix self => 0 ::: delay self` does **not** type: `delay self`
is `FaL (FaL (Sig Int))` where `:::` wants `ExL (Sig Int)`.  A signal
that updates needs a clock, and only `wait`/`watch` introduce one.

### Layout

The offside rule: a block of declarations introduced
continue as long as subsequent lines (ignoring blank lines)
are indented at least as far as the first declaration's column.

The only productions that start layout blocks are:

    let     ... in          --> decl block
    letrec  ... in          --> decl block
    given   ... in          --> decl block
    case    ... of           --> alt block
    class   ... where        --> member block
    instance ... where        --> member block

A block ends at the first line indented less far than its first
declaration — or, if it was opened inside a bracket, at that bracket's
closer, whichever comes first:

    f n = g (case n < 3 of
        True -> 1
        False -> 2)

Indentation alone cannot end this block: the dedent would not arrive
until the following line, by which time the `)` has already been offered
to a parser still reading alternatives.  Only a bracket opened *before*
the block closes it, so a bracket used inside a block is ordinary:

    f x = case x of
        True -> g (1 + 2)
        False -> 3

The toplevel declarations require that their subsequent lines are
indented farther than the beginning line.
The following 4 declarations are separate:

    Color := Red | Green | Blue
    XOrY := X
          | Y
    test : Int
    test = 5

Block productions (let/letrec/case/class/instance): continuation
lines must be indented at least as far as the first declaration's column.
Toplevel declarations: continuation lines must be indented
strictly farther than the beginning line.

### Comments

Comments are single-lines and use the '#' -symbol until end of that line.

    # This is a comment

Comments are preserved within the parse and
consecutive comments are treated as a group.

Comments are parsed as values. To avoid confusion,
the comments are only allowed on beginning of a line
and they may be indented to participate inside expressions.

    some large expression # comment on that expression (disallowed)
      continues here      # another comment (disallowed)

Comments are supposed to go into a location where
they can be treated as part of the code:

    # comment on the following expression
    # another comment
    some large expression
      continues here

In that manner, they're more like python's docstrings in structure.

## Technical details worth mentioning

### Everything is a value

Everything is a value.
This makes the parser easier to use and implement.
Value's full meaning is decided by the next stage coming after parsing.

### Resolution algorithm

Resolution of operators is resolved through precedence climbing.

### Why flat parsing in tree-sitter

Tree-sitter grammars are fixed at generation time, but the fixity
table is per-file. Therefore the grammar
parses operator usage *opaquely* as a sequence and the host compiler
resolves it.  This keeps the grammar stable across user fixity
changes and keeps incremental re-parses cheap.  The tree-sitter
node `operator_phrase` carries enough structure (left-to-right
operand/operator alternating sequence, parenthesized sub-phrases,
applications) for the post-pass to reconstruct the intended tree.

### Testing strategy

- **Golden ASTs** for parse/fix/desugar on every example in
  `examples.md`.
- **Property tests** for unification totality (random `Type`s; never
  crashes, always returns `Either`).
- **Charney-style** G-machine tests: hand-rolled `Expr` inputs that
  match the worked examples in `supercomb.md`, checking heap shape
  after `evaluate`.
- **FRP trace tests**: re-enact the sec 4.5 `sample` trace from
  `frp.md` against `reactive.py` and assert per-step heap shapes.
- **Music regression**: parse `examples.md`'s music blocks, desugar,
  type-check, run `evaluate`, assert the produced `Score Int` value.

### Implementation

We are going to need an autoformatter, tree sitter support
and a (likely hand-written) parser.

Start from the parser, then provide the autoformatter that uses that parser.

Leave the tree sitter support unimplemented and supply it when it is requested.
