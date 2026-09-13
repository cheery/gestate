# strict-forms — the language refuses what Python allows, and the cost is paid in Python

    status   open
    because  "The functional language is excellent the way we use it, but
             we cannot escape from the strict forms it comes with.  It's
             basically the difference between this language and python:
             python allows everything to happen, gestate's language
             doesn't, but it's also deprived of python's power." — Henri,
             2026-09-13, the evening the facts tic-tac-toe landed and
             three of its seams had to be written in Python because the
             language could not say them.
    asked    Henri, 2026-09-13 — "Write it into a new card.  I think this
             is a kind of a separate issue that we should solve in a some
             neat way."
    see      card:gui-is-difficult.md §"Built — 2026-09-13: tic-tac-toe,
                 its board a document" — the three seams, measured
             card:gui-is-difficult.md §"The mashup, asked" — the four
                 forms, and his direction: compositionality
             doc/memory/the-language-goal.md — wasm, model-checkable,
                 optimised for reading: the three properties any answer
                 here is measured against
             spec/data.md — Datafun ∪ Rizzo, the language as it stands
             card:work-environment-ai.md — where *a* language was
                 deferred on purpose; this is about *the* language
             doc/memory/henri-prior-tools.md — mide's UI as datalog, the
                 last time he left a language for a different power

## What this is, what it is not, and when it runs

**A reading of the language's rigidity as a problem with a shape**, and
the families of statically typed languages that have attacked that
shape — each with what it would cost the three properties the language
goal names.  It is **not** a proposal to adopt a language, add gradual
typing, or write a module system; it is not the GUI card, though the
GUI card is where the problem was measured; and it decides nothing.
Its day one is a reading, the way Eve's and DBSP's were read for
`card:gui-is-difficult.md`, source first, what it changes written
here.

**When it runs:** every time a session reaches for Python because the
language cannot say the thing — a textual rewrite in front of the
compiler, a host seam, a generated program.  `scorebox.py`'s 2,232
lines, `gridbox.py`, `facts.with_documents` and `notes.expanded` are
where it has run so far.

## The ask

Henri, 2026-09-13:

> I think we're missing something.  The functional language is
> excellent the way we use it, but we cannot escape from the strict
> forms it comes with.  Do you understand what I mean?  It's basically
> the difference between this language and python: python allows
> everything to happen, gestate's language doesn't, but it's also
> deprived of python's power.  Are there programming languages
> (experimental or not) that address these limitations in statically
> typed languages?

Then, on the answer below: *"Write it into a new card.  I think this is
a kind of a separate issue that we should solve in a some neat way."*

## Measured against the tree — 2026-09-13, the session's

**Three places one slice reached for Python because the language could
not say the thing**, all in `card:gui-is-difficult.md` §"Built —
2026-09-13":

1. **A value cannot become a type.**  `markKind : Kind` says the row of
   a `mark` is a cell and a word, and the program still has to write
   `board : Sig (Set (Int, Text))` by hand for `document "mark"` to
   have a type — a kind is a value, and there is no step from a value
   to a type, so the door is a textual rewrite (`facts.with_documents`)
   and the host checks the two agree.
2. **A meaning is a `Float`.**  `Meaning (Chan Float) Float Sub` — an
   element speaks one fixed word, so a cell cannot carry `Play 4` and
   the foot `Clear`, and the program merges two number channels with a
   clock combinator and a sentinel to tell them apart (his *"bit
   smelly"*).
3. **A file is the program and a channel is a declaration.**  No
   imports; a channel's identity is where it is written; a second file
   cannot name the first's `Act`.  Two pieces that work alone cannot
   be composed without a rename — his *"compositionality would be the
   name of the game"*.

**And the older instances**, so the shape is not mistaken for one
day's: the score box generates its program as text (`scorebox.py`),
the grid generates its (`gridbox.py`), `include` is a regex, the roll's
`Shift` sums are arithmetic the layout algebra could not compose, and
`sync` stands in for a merge of hand events because the language has
no other way to say *either*.

**What the strictness buys, said as plainly**, because the card's
`because` names a trade and not a defect: a fixpoint over a finite key
converges; a monotone `for` is incremental by a source transform; a
golden buffer is bit-exact; `Sub` walks the same in two machines
because its tags are fixed; and the checker refuses a missing arm.
Every one of those is a property Python does not have and this tree
has paid for.  The problem is real and so is the price of any answer.

## The families — from memory, unchecked against their sources

*The session's, 2026-09-13.  Every claim about a system below is a
recollection to be read against the source, the standing the Eve list
had before it was read.  Each carries the tree's analogue and what it
would cost the language goal: wasm, model-checkable, optimised for
reading.*

| family | the idea | its instance here | what it costs the goal |
|---|---|---|---|
| **types computed from values** — Zig comptime, F# type providers, MetaOCaml, typed Template Haskell | any code may run before the program does; types are values there; what comes out is still checked | `document "mark"` typed from `markKind` with nothing written by hand; the score box and the grid as *typed* generators rather than text | two stages to read and check; the model-checker sees only the second |
| **composition without a shared declaration** — OCaml polymorphic variants and row polymorphism, PureScript and Koka records, Elm records | a message type `[> Play of int \| Clear]` composes across files with nothing declared in common | the `Or`-at-the-seam problem dissolved; Eve's *attributes, not positions*, typed | inferred types grow wide and errors long — the reading goal paying |
| **effects, typed** — Koka, Eff, OCaml 5, Frank, Unison abilities | the program performs, the type says it may, the host handles | `Act` with the compiler holding the contract instead of a convention; his own association under Q-b | a new kind of type to read; a runtime wasm has to carry |
| **no files** — Unison | a definition is its content hash, names are metadata, no imports; every piece composes by name resolution | identity-is-the-key applied to code; the most direct answer to *compose from smaller pieces that work individually* | the whole tooling is the language's own, against *plain files you can read without it* |
| **Datalog as a first-class value** — Flix | statically typed, functional, constraints as values composed with an operator and solved where you like, plus effects | the nearest one language to Datafun ∪ facts ∪ acts; composes *rules* the way he wants to compose programs | the JVM; not optimised for reading |
| **the escape hatch** — gradual typing (Siek & Taha), blame (Wadler & Findler); TypeScript, Typed Racket, Hack | `dyn` where you want Python, a type where you want the checker, blame naming the side that broke | Python's power, on demand, inside the file | the boundary is where model-checking stops, and every project that adopted it drifted dynamic |
| **holes that run** — Hazel (Omar et al.) | a program with a typed hole still evaluates; the hole is a value | live coding under a strict checker: the instrument keeps playing through an unfinished edit | not a general escape; already on the GUI card for livelits |
| **a language per model** — Racket's `#lang`, Typed Racket | a small language built for each model, macros as the extension mechanism | *successes are relative to a model*: the roll's, the sheet's, the game's, each its own vocabulary over one core | macros are the hardest thing to read; two-machine parity would have to hold per language |

**The session's order to read, his to reorder:** Flix and Unison
first, because each is one whole design aimed at his sentence; Zig's
comptime and F# type providers next, for the value-to-type step, the
smallest thing that would have removed seam 1; row polymorphism after,
being the mechanism under seam 3; gradual typing last, because it
answers the complaint and pays with the goal.  Each read the way Kale,
Eve and DBSP were: source first, what it changes written here.

## Where the session tips — 2026-09-13, night, at his ask

**Henri:** *"Based on today's issues and difficulties, where would you
currently tip towards?  …  But what could we do without losing the
things we bought with strictness?"*  *The session's lean, marked as its
own; nothing here is decided.*

**Staging, not an escape hatch.**  Keep the checked language as it is
and make the stage *before* it a language thing instead of a Python
thing.  The three seams have one shape: Python computing something
from values the language already holds — a row type from a `Kind`, a
channel from a signature, a program from a file — and pasting the
result in as text, outside the checker.  Zig's comptime and F#'s type
providers are the disciplined form of that stage: the code that runs
before the program is ordinary code over ordinary values, and what it
produces is an ordinary program with every guarantee intact.  Nothing
dynamic reaches the golden buffer, the fixpoint or the two machines,
because those only ever see stage two.  **The rule, in one line: a
program may be computed but never patched.**

*Why this over the others.*  Gradual typing buys Python's power by
giving up model-checking at the boundary — the property he named
first.  Unison and Flix are whole languages, against plain files and
against reading.  Row polymorphism and typed effects keep the
guarantees and would be taken later; neither removes a seam met today.
Staging removes seam 1 outright, and it is where `scorebox.py`'s two
thousand generated lines would go if they went anywhere.

*What it does not touch.*  Seam 2, a meaning being a float, is a
substrate word and a wire decision, not a family.  Seam 3, composition
across files, is modules — the largest change to a language optimised
for reading — so: measured by hand first, designed last.

*What kills the lean.*  If the code that generates the score box
cannot be written readably in the language itself, staging has only
moved the Python into a worse language.  Zig's own answer is that
comptime code is the same language with the same reading; the claim to
test is that, on the smallest generator in the tree — the grid's,
`gridbox.py` — before any larger one.

## Questions

Each shaped with a default and a trigger — `doc/memory/decisions-arrive-shaped.md`.
None answered.

**Q1 — which seam first.**  Of the three measured, which is the one to
design against: a value becoming a type, a typed meaning, or
composition across files?  *Default:* the first — it is the smallest,
it is where a kind being a value already stands, and the other two
each touch a substrate word or the language's unit.  *Trigger:* the
gex sheet's first formula, which needs a cell's type from a kind.

**Q2 — reading or trying.**  Is day one a reading of the families, or
a small program in one of them — the facts tic-tac-toe rewritten in
Flix or Koka, to see what a language with the feature makes of the
same four forms?  *Default:* the reading, then one program in the
language the reading picks, the way the model languages were tried on
the transport first.  *Trigger:* his word.

**Q3 — the goal's three properties.**  Does an answer here have to
keep all three — wasm, model-checkable, optimised for reading — or may
one give?  *Default:* all three; a reading that costs one says so in
its row above and is not disqualified for it.  *Trigger:* the first
family that keeps two and the third looks worth it.

**Q4 — where a neat solution would live.**  In the language (a former,
a type-level step), in the substrate (a typed meaning), or in the
tooling (a module convention with no language change)?  *Default:*
unanswered until Q1; the three seams land in three different places
and that is the finding.  *Trigger:* Q1.

## What a session does now

Nothing but the reading, when he asks for it.  Henri: *"we should
solve in a some neat way"* — a neat solution is a design, and designs
here are his; a session's part is to read the sources, measure the
tree, and shape the decision.
