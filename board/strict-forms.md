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

## What a session does now

Run the kill test — the grid's tables into `.ges` over the `Kind`,
`tools/generated.py` before and after — and bring the number.  Then,
on his answer to Q5, the seam-1 slice A + B + C + D on
`tic-tac-toe-facts.ges`, held by `test_documents.py`'s nine and a
parity test against `with_documents`' text.  E waits on Q6, and Q6
waits on the number.  Henri: *"we should solve in a some neat way"* —
the neat part is his, and what the tree can offer him is the count.
