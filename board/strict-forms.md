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

## Decided — 2026-09-14: staging; and what the tree needs for it

**Henri, opening the sitting:** *"I've decided.  Lets start looking at
what we need in order to implement multiple stages/comptime/type
providers."*  So the lean of §"Where the session tips" is his
decision, and this section is the looking: what the tree already has
that a stage is made of, what the four sources say now that they have
been read rather than recalled, what the two generators actually
contain when counted, and the list of what is missing — each item
with the part that carries it today.  *Nothing is built; the
questions at the end are shaped for him.*

### Located — what a stage is already made of here

1. **A build-time evaluator, in the host.**  `charts.Terms` compiles a
   library, one file and a `main`, `declared` fetches a global,
   `read` forces a heap node into a Python term through the G-machine.
   `facts.Document` reads a program's `kinds` through it — a **second
   compile of the whole GUI program**, 0.3–0.5 s per edit, to obtain
   one value the first compile also had.  That is stage one, run by
   the host after the compiler instead of by the compiler during.
2. **A program computed as syntax, never as text.**  `deriving.py`
   builds `VSCEqn` trees for `deriving Eq | Ord | Show` from a type
   declaration and appends them to the module — a declaration splice,
   hard-coded to three classes.  The one in-tree instance of *computed
   but never patched*.
3. **Types as values, for one domain.**  `facts.ges`' `Kind`, `Field`,
   `Value` describe a relation's row; `facts._kind` reads them back
   and `facts.base_columns` is the row function — key, then required
   scalars — in Python.  The type it implies, `(Int, Text)` for
   `mark`, is written by hand in the program and checked by the host.
4. **A value already inside the type grammar.**  `TInt` — `Cyclic 12`
   — with kind `Int` beside `Type` (`spec/types.md` §5,
   `kindcheck.py`).  The grammar has admitted one kind of value once.
5. **The front end split at a declaration boundary.**  `_analyse_staged`
   and `StackFront`: the library stack parsed, desugared and inferred
   once, a program's items appended, inferred against the stack's
   exported schemes with the `Fresh` counter carried over.  *Staged*
   there means a cache seam, not a language stage — but it is exactly
   the door a stage's *output* would come in through, if it is
   declarations.
6. **A needs graph over definitions** — `desugar._implicit_needs`.
   Inference itself is one group: `infer_program` walks every SC
   together, no dependency ordering, so a stage's cut has nothing to
   reuse there and would be a walk of its own.
7. **The compiler runs on the desk.**  `online.py` and `webshell.py`
   ship compiled programs; nothing in the tab compiles.  Stage one runs
   where the compiler runs, and the two machines and the golden buffer
   see stage two only — which is the property the lean was chosen
   for.

### The four sources, read — 2026-09-14

*Each read at its own page this sitting; the table in §"The families"
was from memory and this replaces its first row.*

| | what it is | what it guarantees | what it cannot do | for this tree |
|---|---|---|---|---|
| **Zig `comptime`** (language reference) | `comptime` parameters and blocks run during semantic analysis; **`type` is a first-class value**; a function may return `type`; `@typeInfo` reflects a type into a value and `@Type` reifies one back; *comptime code is the same language as runtime code* | what comes out is an ordinary checked program; errors point at the source line | run anything that needs runtime memory | the only one of the four that does **both** things the seams want — a value becoming a type, and a program computed from a value — in one mechanism and one language |
| **F# type providers** (Microsoft Learn) | a compiler component that produces *provided types* from an **external schema** named by a static parameter — a file, a URL, a connection string; erased or generative; runs inside the compiler at design time | the program is checked against the schema as it is now | nothing runs in the program's own language; a provider is written in F# against a compiler API | **`document "mark"` is a type provider written as a regex** — the schema is the kinds, the provided type is the row, and `facts.with_documents` is the provider |
| **BER MetaOCaml** (Kiselyov) | `'a code`, brackets `.< >.` and escapes `.~`, `Runcode.run`; generators of generators; cross-stage persistence | *if the generator finishes, the generated code is well-typed and well-scoped* — errors in the generator, never in its output; the output can be printed and read | **cannot compute a type from a value**; purely generative, no reflection on code | the shape for the generators, and explicitly not for seam 1 |
| **Typed Template Haskell** (GHC user's guide) | typed quotes `[|| ||]` and splices `$$( )`, `Code`; `reify` reads a declaration; declaration splices at top level **break the file into declaration groups**, later ones seeing earlier ones | typed splices are checked; untyped ones accept unbound names | **the stage restriction**: a splice may only run code *imported from another module* | with no modules here the restriction has to be *declaration groups within one file* (TH) or *on demand with a cycle refusal* (Zig) — one of the questions below |

**One line from the reading:** Zig computes types from values and code
from values in the same language; MetaOCaml computes code and refuses
types; F# computes types from a schema and no code.  Seam 1 is the
Zig/F# half.  The generators are the MetaOCaml/TH half.  Whether this
tree needs the second half at all is what the census below is for.

### Measured — what the two generators actually write

`python tools/generated.py grid examples/audio/arc.notes` and `… roll
examples/audio/marked.ges`, written this sitting so the number can be
taken again after a table moves into the language.

| | non-blank lines | of which **data as `case`** | of which per-box **channels and entry** | of which derivable from the `Kind` value |
|---|---|---|---|---|
| grid box over `arc.notes` | 71, in 11 definitions | **53** — the word table 19, `show` 12, two domain tables 11 + 11 | 14 — four channels with their held signals, a picture, an entry | 57 — the 53 tables and `widths`, `heads` |
| score box over `marked.ges` | 126, in 42 definitions; longest line **1,111 chars** | the rows listing, one tuple literal per note, and ~20 per-roll constants (`lit`, `dim`, `member`, `shift` …) | 24 — twelve channels | not measured by kind; the rows are `roll.ges`' concern |

**So three quarters of the smaller generator is not a program.**  It
is a word list and two domain lists written out as `case` tables,
because a `List Text` could not cross to a program until `document`
did it this week — and `widths` and `heads` are functions of the
`Kind` the program can already hold as a value.  What is *irreducibly*
generated is fourteen lines, and every one of them exists because **a
channel is a declaration**: a second box needs a second `__ng_cell_1__`,
and the only way to get one is to write it.  That is seam 3 wearing
the generator's clothes, and it is smaller than seam 1.

### What is missing, by item — each with the part that carries it

| | needs | carried today by | missing |
|---|---|---|---|
| **A** | **stage-one evaluation inside the compiler**: run a closed set of the program's definitions, with its preludes, before the rest is checked | `charts.Terms` + the G-machine, after a whole compile, in the host | the **cut** — which definitions are stage one, found by a needs walk back from each splice, a cycle refused on the author's line — and its place in `_analyse`, between desugaring and inference |
| **B** | **a value that is a type**: the row of a kind as a type | `facts.base_columns`, Python | either `Row : Kind -> …` as **one** type-level function the compiler knows how to reify, or a `Type` ADT in the prelude mirroring `TCon/TApp/TFun/TInt` with a general reifier (Zig's `@Type`) — Q5 |
| **C** | **a splice in the type grammar**: `board : Sig (Set (Row markKind))` | nothing; `_parse_type` has one production per type form | one production, one kind rule (a splice has the kind its value reifies to), one call into A |
| **D** | **`document "mark"` as a form the parser knows** — the type provider made honest | `facts.documents` and `with_documents`, 45 lines of regex, the hand-written signature, the host checking the two agree | the form's type from `kinds` through A + B; the channel it stands on declared by the compiler rather than by appended text; the hand-written signature and the parity check gone — **derived, not declared** (`doc/memory/declare-parity-derive.md`) |
| **E** | **declaration splices**, for what the generators still write once the tables are functions | `deriving.py`, for three fixed classes; `gridbox.py`, `scorebox.py` as text | either quotes and a `Decl` value (MetaOCaml/TH), **or channels as values** allocated by an expression so a box is a function — Q6; the census says the demand is fourteen lines, and its cause is a channel's identity |
| **F** | **a stage-one failure lands as a complaint**: `kinds` names no `mark`, a stage-one definition diverges, a splice's value is not a type | `doc/complaints.md` is the ledger; `ChartError` from `Terms` today reads *"tic-tac-toe-facts.ges declares no `kinds`"* with no line | the line, the ledger row, and a step budget for stage one — Zig points at the source line; the tree's rule is the same |
| **G** | **parity while the door moves**: `with_documents`' text against the new path on `tic-tac-toe-facts.ges`, and `test_documents.py`'s nine | the nine tests, `test_facts`, `test_gui` | the parity test itself, and the census re-taken after the grid's tables are `.ges` |
| **H** | **what must not move**: the model-checker and the two machines see stage two only; the wire carries what it carries; wasm is untouched | already so | nothing — it is the reason for the choice, and G is what says it stayed true |

**Reading the list as an order.**  A, B narrow, C and D are one slice
and one seam: seam 1 closed, `with_documents` deleted, the program
saying `board : Sig (Set (Row markKind))` and nothing by hand — or
saying nothing at all, if `document "mark"` carries its own type.  E
is a different slice and, on the census, may not be a splice at all.
F rides in A.  G is the gate on both.

### The kill test, restated with a number

The card said: *if the code that generates the score box cannot be
written readably in the language itself, staging has only moved the
Python into a worse language.*  The census makes it concrete and
cheaper.  **Move the grid's four tables into `.ges` over the `Kind`
value** — a word table is `index words c`, a domain table is `index
(oneOf f) c`, a width is the same eight lines `gridbox.width_of` is —
and re-run the census.  If the generated text drops from 71 lines to
the fourteen channel lines, the language *can* say the tables and the
only thing left for a stage is E.  If it does not, the reason is a
thing the language cannot say, and that thing is the finding.  Nothing
in this test needs A–D; it is an afternoon, and it is the first thing
to do.

**Postcondition, the session's sentence, for the seam-1 slice,
uncorrected:** *a program that declares a document's kinds names its
rows' type nowhere by hand, and a kind edited in the program changes
what the checker accepts on the next compile, with no Python between.*

### Questions — shaped, 2026-09-14

**Q5 — how wide is "a value that is a type".**  One reifier, `Row :
Kind -> Type`, known to the compiler; or a `Type` ADT in the prelude
that any stage-one expression may build, with `@Type`'s generality.
*Default:* the narrow one — it is the only caller, it is a hundred
lines, and the wide one is a design he would want to see.  *Trigger:*
a second caller that is not a kind's row.

**Q6 — what the fourteen lines become.**  Declaration splices with a
`Decl` value and quotes, or a channel that is a value — `chan` as an
expression a function may evaluate, a box a function of its number.
*Default:* neither until the kill test has been run and the fourteen
counted again; then the lean is **channels as values**, because it
removes the cause and not the symptom, and because a `Decl` value is
the most syntax any family here adds.  *Trigger:* the count.

**Q7 — declaration groups or on demand.**  Template Haskell cuts the
file at each top-level splice and a splice sees only what is above it;
Zig analyses on demand and refuses a cycle.  *Default:* on demand — no
new line in the file, the needs graph exists, and a cycle is a
refusal with two names in it.  *Trigger:* a program whose stage-one
set a reader cannot find without a marker.

**Q8 — where `document` reads its schema.**  From the program's own
`kinds` (today; the declaration is the program's and the file is
checked against it), or from the `.board` file itself, as an F#
provider reads a sample (the schema is the data's, and two programs
over one file cannot disagree — `card:gui-is-difficult.md` §"Where a
kind is declared", kill 3).  *Default:* the program's `kinds`, because
a file with no program beside it is the case the kinds prelude was
chosen for, and because a schema read off data is a guess about the
data.  *Trigger:* the first document two programs declare differently.

### His answers — 2026-09-14, the same sitting

**Henri:** *"Q5: I don't know, which one is better?  Q6: default Q7:
on demand.  Q8: program's kinds now, in some cases the file itself.
Do the kill test."*

So **Q6** is the default — nothing until the kill test's count;
**Q7** is on demand, a needs walk and a cycle refusal, no marker in
the file; **Q8** is the program's `kinds`, with his qualification
kept: *in some cases the file itself* — the case is not named yet, and
the first document two programs declare differently is still the
trigger that would name it.

**Q5, answered with a recommendation, the session's:** the wide one,
kept minimal.  *Why.*  The narrow reifier makes the compiler know a
library's constructor by name — `Kind` is `facts.ges`', and a compiler
that reads `Kind "mark" Named …` has a library baked into it, which is
the coupling `charts.Terms` was written to avoid (*not
chart-specific*).  The wide one adds one ADT to the prelude, `Type`,
mirroring the compiler's own `TCon`, `TApp`, `TFun`, `TInt` and the
tuple — five constructors — and one reifier from that value to a
`types.Type`; then `rowType : Kind -> Type` is written **in
`facts.ges`, in the language, where a reader can see what a row is**,
and the compiler knows nothing about kinds at all.  That is the
reading goal served and the coupling refused, for perhaps forty more
lines than the narrow one.  *Kept minimal:* no `@typeInfo`, no
reflection from a type back to a value, until a caller wants it —
Zig's other half is not asked for by any seam.  *What would change
the recommendation:* if the `Type` ADT had to mirror classes and
constraints to say the row of a kind — it does not; a row is a tuple
of `Int` and `Text`.

### The kill test, run — 2026-09-14

**The language can say the tables.**  The grid's four generated
tables, its widths and its heads, written once in `.ges` over the
`Kind` value — `gridShow words (kindFields noteKind)`, `gridWidths`,
`gridHeads`, a `case` over `Value` where the Python had a `case` over
a Python domain — and the generated program's picture on the whole of
`arc.notes` reproduced **item for item, 5,257 of 5,257**.
`test/test_gridsheet.py::test_the_grids_tables_written_once_over_the_kind_draw_the_generated_picture`
holds it; the port text is in the test.

| | generated today | tables as `.ges` over the kind |
|---|---|---|
| written per file | **71** lines | **16** lines — fourteen of channels, picture and entry, two of the file's words as a list |
| written once | 0 | 63 lines of `.ges` |
| compile, reference machine | 0.60 s | 1.22 s — the declaration and the sixty-three lines sit in the program half, uncached; in the stack they would cost once |
| first picture, 5,257 items | 6.0 s | 7.2 s — a list walk where a `case` table was; the window walks in Rust and is not measured |

**So the lean survives its kill, and the finding is sharper than the
lean.**  Nothing in this test needed a stage.  What the generator was
doing three quarters of the time was writing *values* as *code*
because the program could not hold the values — and it can, and could
have since `facts.ges` made a kind a value on 2026-09-09.  What is
left, the fourteen lines, is one shape: `__ng_cell_0__ : Chan Float`,
`__ng_cell_0__ = chan`, for each of four channels, then a picture
lifted over two of them.  Q6's default stands and its count is in:
**fourteen**, all of them channel identity.  The two things the
finding changes: the census tool has a second column now, and the
port's home is a chain decision — `grid.ges` stands before
`facts.ges`, so `Field` is not in scope there; either `facts.ges`
moves forward in the chain or the grid-over-kind functions are a file
after it.  *Not decided, not built; the test carries the text.*

**And his question, mid-run — Henri, 2026-09-14:** *"Some kind of
staging has been missing for a long time now.  This language has lot
of examples where one would perhaps have needed staging.  Or am I
right?"*  *Answered from the tree, the session's.*  Right about the
missing thing, and the tree can count it: **ten Python files write
`.ges` text** with a signature in an f-string — `scorebox.py` 59
times, `audiovoices.py` 15, `gridbox.py` 12, `export.py` 5,
`reactive.py`, `gui.py`, `session.py`, `notes.py`, `facts.py`,
`audio.py` once or twice each (`grep -c 'f"[^"]* : \(Chan\|Sig\|Int\|List\|Float\|String\)' gestate/*.py`).
Each is a place a program was computed outside the checker.  But the
kill test says the demand splits three ways, and only one of them is
staging: **values written as code** — the grid's tables, the roll's
`rollNum` case table to sixty-four, the score box's rows as a
1,111-character tuple literal, `voices` banks expanded per program —
wanted a value the program could hold, and mostly can now; **channel
identity** — every `__x_k__ = chan` — wants a channel that is a value,
seam 3; and **a value that is a type** — `document`, the `on <points>`
literal that must stand at its call site (`doc/memory/gestate-language-pitfalls.md`),
`Voice` generated per program — is the staging demand proper, and it
is the smallest of the three by line count and the only one no other
mechanism answers.  So: yes, and the examples were mostly asking for
something cheaper than staging, which is why the stage is worth
building small.

### Built — 2026-09-14: seam 1 closed, the stage in the compiler

**Henri:** *"Q5: Then it's the wide one kept minimal.  Ok.  lets do the
seam-1 slice on the tic-tac-toe."*  Built the same sitting; the
postcondition above holds, and `test/test_documents.py` says so in
its own words: *the row type is computed from the kind and written
nowhere by hand*, and *a kind edited in the program changes what the
checker accepts* — a third required column makes a placing a triple
and the program's own `(c, m)` is refused at its first use, from the
kind alone, with no Python between.

**What landed, by the items of the list:**

- **B, the value that is a type** — `facts.ges` gains `Type := TyCon
  Text | TyApp Type Type | TyFun Type Type | TyInt Int | TyTuple (List
  Type)`, the compiler's own grammar as five constructors, and
  `kindRow : Kind -> Type` written beside it in the language: the key
  columns, then every required scalar field, a `Number` an `Int` and a
  word a `Text`, a `Headed` kind's bare name a `Text`.  `kindColumns`
  is held equal to `facts.base_columns` for every kind gestate ships
  and the game's (`test/test_stage.py`).  The compiler knows the five
  names and nothing about kinds.
- **A and C, the stage and the splice** — `gestate/stage.py`, 330
  lines, run in both analysis paths after the operators are resolved
  and before anything is classified.  `$(e)` in a type position is a
  site; so is `document "kind"`.  The items holding a site, and
  everything that mentions them transitively, are stage two: blanked
  line for line so every position holds, and what remains is compiled
  once — through the same cache every compile uses, and through the
  lockless door, because the front end's lock is not reentrant and the
  first run of this deadlocked exactly as `doc/memory/a-run-silent-for-a-minute.md`
  said it would.  Each splice's expression is appended as a `Type`
  global, evaluated on the G-machine, read back, and put into the type
  syntax where the author wrote it; aliases expand over it as over any
  type.  **On demand, Q7:** no marker; a splice that needs an item the
  splice types is refused with both names.
- **D, the door made honest** — `document "mark"` is a form the stage
  knows: its row from `documentRow kinds "mark"`, the read of its
  channel built by the parser and put in the expression's place, and
  `__doc_mark__ : Chan (List <row>)` declared **by the compiler**, as
  syntax, never as text.  `facts.with_documents` and the signature
  regex are deleted; `facts.documents` now answers only *which kinds*,
  which is what the host feeds; the substrate lists the compiler's
  channels beside the author's.  A kind the program does not declare
  is refused with the kinds it does, at the author's line through
  `audiospans.in_source` like every other complaint.
- **F, the complaints** — `StageError`, `author`, placed; one
  `machine` site.  On `doc/complaints.md`.
- **G, the parity** — the nine document tests unchanged and green, the
  bench pressing cells and reading the file as before; `test_stage.py`
  five, `test_documents.py` twelve; the gates 809.

**The program, after.**  `type Placing = $(kindRow markKind)` and
`type Board = Set Placing` are the two lines about the row; `board :
Sig Board`, `markAt : Board -> Int -> List Text`, `retractOne :
Placing -> Act`.  `(Int, Text)` is in no line of code.  The name
`Row` was the first choice and is `gui.ges`' picture constructor, which
the checker reported as *Unknown global 'Row'* at a use of the
constructor rather than as an alias clashing with a constructor —
`fixme.md` F231, found on the way and not this card's.

| | before | after |
|---|---|---|
| lines about the row, by hand | 1 signature, 8 more naming `(Int, Text)` | 0; one splice, one alias |
| the type checked against the kind by | the host, in Python, after the compile | the compiler, before the check |
| `facts.py` lines for the door | 45, a regex and a rewrite | 12, which kinds to feed |
| the game's build, `Substrate`, cold / warm | not measured on this path | 1.89 s / 0.30 s, two stage compiles inside the cold one |
| `facts.beside`, the host reading `kinds` | 0.3–0.5 s, a second compile | 0.22 s, unchanged — the next cut, not this one |

**Two spellings, one refused.**  The expression grammar reads `$`
between two things as an operator binding looser than `->`, so
`Set $(e) -> Int` would splice `e -> Int`; the stage refuses that
form with the spelling that works, `Set ($(e))`, and the idiom is the
alias anyway.  The splice is prefix-only.

**What this does not do.**  Nothing reflects a type back into a value.
E, the fourteen channel lines, is untouched.  `facts.Document` still
compiles the program a second time to read `kinds` where stage one now
has the value in hand.  The wire is untouched: a document program
stays on the reference machine as before.

### The next cut — 2026-09-14: the host reads `kinds` off stage one

**Henri:** *"to the next cut."*  Stage one already evaluates `kinds`
to type a `document`; it now reads the list itself while the machine
is warm and the analysis remembers it (`Analysis.stage`,
`pipeline.staged_value`).  `facts.Document` asks the cache first: a
program the substrate has built hands over its kinds as a dictionary
read, and a bare declaration or a program nobody has built compiles as
before — the two readings held equal by
`test_documents.py::test_a_built_programs_kinds_are_read_off_stage_one_and_not_compiled_again`.

| `facts.beside` after the substrate is built | before | after |
|---|---|---|
| | 0.22 s, a second compile of the whole program | **8 ms**, a dictionary read |

What it does not touch: `charts.Terms` and the bare-declaration road
are as they were, and a `Document` built *before* its program still
pays the compile once — the analysis it leaves behind is then the
substrate's front end, so the total is one front end either way.

### Moved — 2026-09-14: the tables into `grid.ges`, the chain reordered

**Henri:** *"facts.ges before grid.ges, move the tables."*  Done the
same sitting.  `audio._GUI_GRID` is now `gui.ges`, `roll.ges`,
**`facts.ges`, `notes.ges`, `grid.ges`** — the kind's vocabulary and
the `.notes` declaration in front of the grid, so the per-file program
names `noteKind` and `grid.ges` does the rest.  The four tables, the
widths and the heads are the library's — `gridShow`, `gridWidths`,
`gridHeads` and their helpers, the 63 lines the kill test wrote, under
their own heading with the reason beside them — and
`gridbox.grid_program` writes what the census said it would:

```
python tools/generated.py grid examples/audio/arc.notes
grid program over arc.notes: 16 non-blank lines, 6 definitions
```

Fourteen of channel identity and two of the file's words; no `case`
in the program, and `test_gridsheet.py` refuses one coming back.  The
picture on the whole of `arc.notes` is the one the 71-line generator
drew — the hit table, the labels and the presses aimed by the host's
arithmetic all hold in the same tests as before, 14 of 14 — and the
program stays byte-identical across a value edit.

**`notes.ges` in the chain is the session's addition**, said so
because he named only `facts.ges`: the tables are functions of a
`Kind`, and the `.notes` kind is declared in `notes.ges`, which was in
no chain — the choice was to put the declaration in front or to print
the kind back from Python into the program, and printing a value as
code is the thing this move removes.  A grid page therefore cannot
declare its own `kinds`; the day a grid is drawn over a document that
is not a `.notes`, that is the line to revisit.  Not on the reference
roster, since it is a declaration and not a library.

### Two more, at his word — 2026-09-14

**Henri:** *"fix F231 and give $ a fixity."*  `$` is `infixl 9` in
`descend.DEFAULT_INFIX`, the tightest infix operator and, like `->`
and `!`, one a program may not redeclare: `Set $(e) -> Int` is `(Set
$(e)) -> Int`, and both spellings of a splice are the same type.  The
refusal of the infix form is gone with its reason.  And an alias may
no longer wear a constructor's name: `_collect_aliases` refuses `type
Row = …` beside `Row Sub Sub` at the alias, in the shape of its two
neighbours — `fixme.md` F231, resolved.

### Read — 2026-09-14: Kiselyov & Imai, *Session Types without Sophistry*

**Henri:** *"Lets address the 'a meaning is a Float', what would we
need to change it?"* — then, on the existential answer, *"existential
constructor would be honest, but also change the language toward
not-type-inferable.  I have a suggestion, but it's a bit silly.  Lets
define something akin to 'IO' -monad.  Lets call it the 'Act'.. Hey I
might even have something for this:
https://okmij.org/ftp/meta-programming/sessions/description.pdf"*
Read in full, 22 pages, from his download.  *The reading is the
session's.*

**What the paper is.**  A system description of `<session>`, a
MetaOCaml library for binary session types (Yoshida & Vasconcelos'
liberal system), with choices, recursion and delegation.  Its one idea
is on page one: **type checking as staged computation** — the
generator runs ordinary OCaml, the DSL's type is ordinary data to it,
and a check that fails in the generator is a compile error from the
generated program's point of view.  The load-bearing move is §4.1:
factor the DSL into *communication* and *computation*, keep the
computations as quoted code, and make communication a **value** the
generator can inspect — their `comm` is a record of code plus an
annotation, and sequencing merges the annotations.  They say it
themselves: *"such a factoring is common: monadic IO in Haskell"*.

**What it changes here.**

- **Seam 2 is not solved by it.**  Their check runs in the generator,
  before the program does; the picture here is stage-two data, rebuilt
  every frame from the board, so nothing can walk a `Meaning` ahead of
  the program to learn what its channel carries.  The existential
  question stays where §"What a session does now" left it.
- **It names the decision of §"Decided — 2026-09-14"** and defends it
  from another tree: a stage in the compiler, a stage-one failure as a
  complaint, a `Type` value with a reifier — their `trep` and
  canonical structures, built independently.  Their one regret (§4.2,
  §6) is the direction this card declined: they want the compiler to
  reflect an inferred type back into a value, so the `trep`
  annotations go.  Their caller is serialisation, which the hosts here
  do by walking values, so the *no caller yet* reason holds.
- **Their factoring is his suggestion, made for another DSL.**  `Act`
  as data, performed by the host, is the standard move and not a
  silly one.

**Session types themselves — Henri:** *"session types are something
I've been wanting, but I understand there are some limitations they
bring and not all of it is good."*  What they would be about here is
not the picture but the **host protocol**: one arrival per channel per
instant (`reactive.py`), `acts` read only after a hand's write and
never between, a signal that must hold a value before any arrival —
three rules enforced at run time or by convention today, and the
sentinel is a type-state defect of exactly their kind.  What they cost:
linear endpoints, where a signal here is read many times; duality and
its inference; and the paper's own answer to *"errors reported too
late"* is the staging this card already has.  Not a proposal; a
reading of where the want would land.

### Q9 — what a press carries, shaped 2026-09-14

**Henri:** *"the solution to this problem might indeed be 'Act'."*

*Three forms.*  **(a)** `Meaning : Act -> Sub -> Sub`, `Act` a closed
command type — no existential, no parameter on `Sub`, inference
untouched; the picture is the dispatcher and the host performs, so
`sync`, the `SyncBoth` arm, `floor`, the sentinel and `acts` as a held
signal all go — both halves of the smell.  **(b)** the existential
constructor, honest and the language's first non-inferable form.
**(c)** stay.

*Default:* **(a)**, beside the `Float` meaning and not instead of it —
the roll's, the grid's and `onPress`'s meanings are values *into* the
program and stay on their channel.  *Its costs, counted:* `Act` and
`Fact` have to stand before `gui.ges` in the chain — `facts.ges` names
no `Sub`, so moving it in front of `gui.ges` is the cheap form, and the
prelude the other; `Fact` has to be one type, a kind's word over a
list of values, or computed from the program's `kinds`, which is a
stage-one *declaration* and E's door again; and the three walkers
carry a node where a float was, the browser's wire a serialised `Act`
per element — the cost §"What a session does now" already named.
*Trigger, the kill:* a press whose reaction is a change of the
program's own state with a message that is not a `Float` — a chart's
transition, a mode, a selection — which (a) cannot carry and (b) can.
Not built; his word first.

## What a session does now

Seam 1 is closed, its second compile is gone, and the grid's tables
are the library's.  What remains on this card is E — the fourteen
lines, every one of them `__x__ = chan` — which waits on a design for
a channel that is a value, his; seam 2, with Q9 shaped above and its
default an `Act` the picture carries, his; and the card's larger
question, how a program is composed from pieces, is his too.
