# `do` — the monad's sugar

*Agreed 2026-08-10, in conversation, as the first brick of the
dynamic-score redesign (`spec/dynscore-constraints.md` is the sheet
that redesign answers to; this file is deliberately smaller than
that).  The shape was chosen for two properties named up front:
**neatness**, and **ease of parsing** — and the second is measured
against this grammar's own machinery, not against a parser we do not
have.  Implemented the same day — `_parse_do` in
`gestate/syntax/parse.py`, held by `test/test_do.py` — and
implementation corrected one claim, marked below: the design assumed
the `Monad` class was future, and the prelude already had it.*

## What the language already gives

Three facts of `spec/syntax.md` make the sugar nearly free:

1. **The block machinery exists.**  `of`, `where`, `let`, `letrec`,
   `given` open layout blocks; items sit at one column or split on
   `;`; the continuation rules (operator-start, paren-start,
   ends-with-`=`, binds-nothing) already handle a long item.  `do`
   joins the opener set and inherits all of it — including the
   bracket rule, so a `do` inside parentheses re-enables layout the
   way `case … of` does.
2. **`<-` costs the lexer nothing.**  Symbol characters not separated
   by whitespace always join, so `<-` is one token already; and since
   there are no negative literals (`-5` is prefix `-` on `5`),
   `x < -e` needs its spaces anyway.  No lookahead, no new lexing.
3. **The disambiguation is a trick the parser already performs.**
   The continuation rule scans a line for a top-level `=` to tell a
   `let` item from a broken application; `_parse_clause` decides
   `p in e` against a bare guard by attempting the pattern and
   backtracking, which is free because the token list is
   materialised.  A `do` item is the same two moves with one new
   token: **`<-` is to `do` what `=` is to `let`.**

## The surface

    follow : List Int -> [: Custom :]
    follow ks = do
        k <- pickOf ks
        v <- veloFor k
        '(Custom v k)

Three item forms, decided by the scan:

- `pat <- expr` — a bind.  The pattern is a lambda parameter, so
  whatever a lambda accepts, a bind accepts (a name, `_`, a tuple).
- `name = expr` — a pure binding: a `let` inside the block, no monad
  involved, decided by two tokens of lookahead (`word`, `=`).
- `expr` — an effect whose value is dropped — except the **last**
  item, which is the block's value and must be an expression; a block
  ending in a binding is refused by name.

One line holds several items with `;`, the block openers' own
convention: `do x <- roll; '(Custom 0.8 x)`.

## The desugaring — one name, no class

    do { p <- e; rest }   ⇢   e >>= (p => do { rest })
    do { x = e;  rest }   ⇢   let x = e in do { rest }
    do { e; rest }        ⇢   e >>= (_ => do { rest })
    do { e }              ⇢   e

The sugar needs exactly one name in scope: **`>>=`**, whatever it
means at that type.  There is no `return` and no `pure` in the
translation — the last item is an ordinary expression, and an author
who wants to end on a wrapped value writes the wrapping themselves.

**The class was already there — the design just hadn't looked.**
This section originally argued "sugar first, class at the second
customer"; implementation found `class Monad m` sitting in the
prelude with `pure` and `(>>=)`, instances for `List`, `Maybe` and
`Score`, and — the part that completes the surface — **`'` already
defined as `pure` written as syntax** (`(') x = pure x`).  So the
symmetry is exact and nobody planned it: a `do` block needs no
`return` because the language already spells `pure` as `'`, at every
monad — `'(z + 1)` closes a `Maybe` block and a score block alike.
The one-name desugaring stands unchanged; the name simply resolves
through a class that was waiting for it.

**Desugared in the parser, and gone.**  No `VDo` node exists: a `do`
block leaves `_parse_do` as the `>>=` chain it means, so the renamer,
the type checker, every backend and every walk stay ignorant of it —
the constructor tax (`spec/dynscore-constraints.md` §D8) is paid by
nobody.  The cost of the whole feature: one reserved word, one entry
in the opener set, one item scan, ~a hundred lines of parser.

## Two honest notes

**Do over `[: a :]` reads as substitution, not sequence.**  The
score's `>>=` replaces each event with a score, so
`do { k <- melody; harmonize k }` means *for every note of the
melody* — list-monad flavour, not "then".

**And the laws hold, time included — on the plain algebra.**  This
note originally claimed left identity bends on durations; measured,
it does not: `('1 ++ '2) >>= f` equals `f 1 ++ f 2` to the event and
the tick, because bind distributes over every structural operator and
duration comes from content.  What bends is the *reactive* graft:
`sowScore` wraps a sown decision in `Clip`, `Clip` does not
distribute, and the same experiment routed through `sown` with a
constant draw comes out shifted.  The monad is lawful; the boxes are
not of its algebra — which is the redesign's true target, recorded
the day it was found (2026-08-10, the "route a constant through it
and the algebra must not notice" test).

**The machinery already speaks monad; this is its missing surface.**
`CueAsk Int Int (List Int -> List Cue)` is a reified bind — an
effect and a continuation holding the entire rest of the
performance — and the cue stream is a free-monad interpreter that
never had syntax.  A `Perform`-flavoured monad where listening and
drawing are effects —

    bar = do
        ks <- hear holds.keys
        s  <- draw
        '(Custom 0.8 (pick ks s))

— is where this sugar pays: eyesore items 2, 3 and 4 (N draws need N
leaves; the probe box trap; take-entropy unable to seed a walk)
dissolve into linear text, with crust and the Python machinery
unchanged underneath, because the continuation they interpret is
already there.

## Ruled out, and why

- **Bang-notation** (`!e` inline binds, Idris/Lean) — the neatest
  surface for the score case, and dead on arrival: `!` is the signal
  lift, the language's most idiomatic symbol, and it will not carry
  two meanings.
- **Reusing `for`/`in`** — both reserved already, so it parses free,
  but it dresses substitution as a loop, and the substitution reading
  needs no extra disguise.
- **`pure`/`return` in the translation** — a second name the sugar
  would demand of every monad, bought back by letting the last item
  be an expression.
