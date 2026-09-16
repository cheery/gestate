# types-in-the-host — six places Python reads a type the checker holds, and computes from it where the checker cannot see

    status   open
    because  Six type-directed programs live in the host: Python reads a
             type the compiler inferred or the author declared, and
             builds something from it — a zero change, a derived
             instance, a struct layout, a channel count, a flatness
             verdict, a reference page.  Each is a program the checker
             never sees, written in the one language here that the
             checker does not check; and where the type has variables,
             each decides for itself what to do.  *The session's reading,
             2026-09-16, which he made a card of at once; his own
             sentence for it is Q1.*
    asked    Henri, 2026-09-16 — "I thought we had some caller for it
             already, can you list some candidates?"  Then, on the six:
             "lets make it a card. then start working on changes.py".
    see      doc/memory/the-language-goal.md §"The callers — 2026-09-16, found in the tree at his ask"
                 — the six, and the theory this is the first arm of
             doc/memory/the-language-goal.md §"Read — 2026-09-16: the theory's two sources, at their page"
                 — Shields, Sheard & Peyton Jones (POPL '98); Jay & Palsberg (ICFP '11)
             card:strict-forms.md §"Built — 2026-09-14: seam 1 closed, the stage in the compiler"
                 — the reifier that exists: a `Type` value into the checker
             gestate/stage.py — stage one; `_type_val` is the reifier
             gestate/facts.ges §"A type, as a value" — the `Type` ADT, five constructors
             gestate/changes.py — the first slice: zero changes, `spec/data.md` §I.4
             doc/memory/declare-parity-derive.md — how a load-bearing mechanism moves

## What this is, what it is not, and when it runs

**The other half of the stage.**  Stage one, built on 2026-09-14, turns
a *value* into a *type*: `$(e)` in a type position, `document "kind"`.
Nothing turns a type back into a value.  This card is that direction,
pulled by callers that already exist rather than by the theory: six
pieces of Python that hold a compiler type in one hand and build a
program with the other.  It is **not** `@typeInfo` for its own sake,
not a quotation or `Decl` value (`card:strict-forms.md` Q6 stands),
and not the self-hosting of the compiler; it is one reflector, on the
ground fragment, and the six readers moved through it one at a time.

**When it runs:** at every compile, in the middle end — after inference
and before the machines — which is where all six sit today.

## The ask

Henri, 2026-09-16, on the session's *no caller yet*:

> I thought we had some caller for it already, can you list some
> candidates?

And on the list of six: *"lets make it a card. then start working on
changes.py"*.

## Found by looking — 2026-09-16

**The six, ordered by how squarely each is the theory's case:**

| | where | reads | computes | the type is |
|---|---|---|---|---|
| 1 | `changes.py` | the monomorphic types the specialiser reached | zero changes: `Δ(A×B)`, `Δ(A→B)`, `dummy_T` per ADT, `bottom_S` per set | **inferred**; a type with variables answers `()` silently |
| 2 | `deriving.py` | a type declaration | `Show`, `Eq`, `Ord` instances as surface AST, three classes fixed | declared |
| 3 | `audioextract._layout` | every ADT's constructor types | LLVM struct layouts — *the only place that still has the compiler's types* | declared |
| 4 | `audio._channels_out` | the type of `sound` | the frame's channel count, because the machine cannot tell `Int` from `Float` by value | **inferred** |
| 5 | `audiograph._settled`, `_monomorphise` | a signature with variables | *flat once settled*, each variable instantiated to a witness | declared, open |
| 6 | `reference.py`, `session.py` | the signature **as text** | reference pages, the editor's argument names | declared, read off the line |

**What exists.**  `stage._type_val` reads a `Type` value — `TyCon`,
`TyApp`, `TyFun`, `TyInt`, `TyTuple` — into type syntax.  Its inverse,
`types.Type` into a `Type` value, does not exist; and `Type` has no
variable constructor, so a scheme cannot be said in it at all.

**Measured, the first slice.**  A compile of `tic-tac-toe-facts.ges`
through the substrate asks for **28 zero changes at 6 ground types** —
`Int` 8, `()` 7, `String` 6, `(Int, String)` 5, `(Int, Int, Int)` 1,
`Char` 1 — generates one `dummy_List_Char`, and hits the free-variable
branch **0** times.  A scored audio piece (`moods.ges`, one second
through `audioperform -o`) asks for **none**: the zero rule serves the
Datafun half, which is the documents and the GUI.  *The command is the
session's scratch `zerocount2.py`, forty lines patching
`Changes.zero`; worth a `tools/` home if the number is taken again.*

**The cycle, located.**  A stage-one program compiles through the same
pipeline as any program (`stage.staged`, through `pipeline`'s cache),
and that pipeline runs the seminaïve transform, which asks
`changes.zero`.  So a zero rule written in `.ges` is asked for while
the file that defines it is being compiled.  The stack front is built
once and cached (`pipeline._stack_front`), so the cycle is one
bootstrap, not a loop — but a bootstrap it is, and Q3 is what breaks it.

**What the theory says, in one line each.**  A reflected type is a
scheme with its bound variables listed, and only a closed type survives
to a run (Shields et al.); reflection over *terms* costs HM and
reflection over *types as data* does not, and the price of keeping HM
is adequacy — a `Type` value need not be the reflection of any type
(Jay & Palsberg).  So: the reflector is total on the ground fragment,
refuses a variable at the line, and a `Type` that reifies to nothing
is a complaint, not a type.

## The first slice — changes.py, three shapes

*Each with what would kill it; the default is the session's.*

**(a) The rule as a typeclass.**  `class Change a` with derived
instances, the zero change as a method.  Haskell's way.  *Kill:* the
change *type* is a function of the type — `Δ(A→B) = □A → ΔA → ΔB` — and
the language has no type families; the stage would have to supply
`$(delta (typeof x))`, which is `typeof` on an inferred type of an
arbitrary expression, the widest form of the reflector, first.

**(b) The rule as a generator of code.**  `zeroAt : Type -> Expr` in
`.ges`, with an `Expr` ADT for core syntax.  *Kill:* that is a
quotation, Q6's `Decl` value, and Jay & Palsberg's bill for it; and the
transform runs on core after desugaring, where no splice lands.

**(c) The rule's decision in the language, its construction in the
host.**  A small ADT — the *shape* of a zero change: unit, bottom at a
set, a pair of shapes, a dummy at an ADT, a function's shape — and one
function `zeroShape : Type -> Shape` written in `.ges` beside `Type`.
`changes.py` reflects the compiler's type into a `Type` value, asks the
machine for its shape, and builds the `Expr` from the shape as it does
today.  The type-directed *decision* is in the language where the
checker sees it; the `Expr` stays in Python, which it has to until (b).
The free-variable branch becomes the reflector's refusal.  *Kill:* the
bootstrap — Q3 — and the cost of a machine call per zero change,
twenty-eight per compile of the game, to be measured against the
1.84 s the compile takes.  **Default.**

**What is common to all three, and can be built under any answer:**
the reflector `types.Type -> Type value` on the ground fragment, and
its test — reflect then reify is the identity on every type the
suite's programs infer, and a variable is refused with the line.  That
is the theory's soundness pair held by a test, and it is the slice's
first commit.

## Questions — shaped, 2026-09-16

**Q1 — the `because`, in his words.**  The header carries the session's
sentence.  *Default:* it stands as written, marked the session's.
*Trigger:* his sentence, when he has one.

**Q2 — the shape of the first slice.**  (a), (b) or (c) above.
*Default:* (c).  *Trigger:* a zero change whose *shape* cannot be said
without the value — there is one already, the sum's dummy, and (c)
carries it as a shape that names the ADT; if a second one needs the
value's *type* at run time, (c) is too small.

**Q3 — the bootstrap.**  A zero rule in `.ges` is asked for while its
own file compiles.  Three ways: keep the Python rule as the bootstrap
for the stack front only, held to parity with the language rule on
every type the suite compiles (`doc/memory/declare-parity-derive.md`);
or compile the file that defines the rule without the seminaïve
transform, which is the right thing if that file has no `fix` — and
`facts.ges` has none; or put `Type` and the rule in the prelude, which
is compiled first and cached.  *Default:* the second — no parity to
keep, and it makes the rule's home a file with no `fix` in it, which
is a property a test can hold.  *Trigger:* a `fix` arriving in that
file.

**Q4 — the free-variable branch.**  Today a type with variables answers
`()` silently, with a comment saying the places are the polymorphic
prelude's dead branches.  Under the reflector it is a refusal.
*Default:* refuse, and count how many programs in the suite trip it —
the game trips it zero times.  *Trigger:* one that does, in a branch
that is not dead.

### His answers — 2026-09-16, the same sitting

**Henri:** *"yea. it all seems ok."*  So every default stands: Q1 the
session's sentence, marked; Q2 shape (c); Q3 the rule's file compiled
without the transform; Q4 refuse.  And the postcondition below,
uncorrected.

**Q5 — `deriving`, and the binder.**  Reader 2 builds three instances
from a declaration *with its parameters open* — `(Show a, Show b) =>
Show (Pair a b)` — so it reads a scheme, and `Type` has no binder to
say one.  Moving it means two designs at once: a bound variable in
`Type`, and a declaration splice for the instance it writes, which is
Q6 of `card:strict-forms.md` and the quotation Jay & Palsberg price.
*Default:* it stays in Python, three classes, until both exist; the
card closes with reader 2 named as the one it did not move and why.
*Trigger:* a fourth derivable class asked for, or a program that
wants to derive something the compiler does not know.

## The postcondition, before anything is built

*The rule that says what the zero change at a type is, is written in
the language and read by the compiler; and a type the rule cannot
answer is refused at compile time, at a line, rather than answered
with nothing.*

## Built — 2026-09-16: the reflector

`stage.reflect`, the inverse of `_type_val` on the ground fragment,
and `test_stage.py` holds the pair: reflect then reify is the identity
on twelve closed types, the game's six among them; a variable and a
monotone arrow are refused.  The refusals name no line yet — `fixme.md`
F238, the first caller holds a type and no span — and the complaints
ledger prints them unplaced.  Nothing calls it yet; that is Q2's.

## Built — 2026-09-16: the zero rule in the language, shape (c)

**`gestate/rules.ges`**, compiled after `facts.ges`: `Zero := ZUnit |
ZBottom | ZPair (List Zero) | ZDummy | ZFun Zero` and `zeroShape : List
Text -> Type -> Zero`, forty lines with their reasons.  `changes.py`
reflects the inferred type (`stage.reflect`), asks the rule's machine
once per distinct type, and builds the expression the shape says,
walking the shape beside the type so the type still names the helper;
its own `case` over the compiler's types is gone.  The rule's file has
no `fix` and no set in it, so the transform that asks for zero changes
never runs over it — Q3 answered by `_uses_datafun`, which already
existed, and the card's "cycle" was a bootstrap that the pipeline's
own gate breaks.

| | before | after |
|---|---|---|
| the decision | `changes.py`, a `case` over `types.Type` | `rules.ges`, a `case` over `Type` |
| a type with a variable | `()`, silently | refused, naming the type (`stage.reflect`; the line is F238) |
| the game's compile, cold | 1.84 s | 2.11 s — the rule's own compile, 0.22 s, once per process; an ask is under a millisecond |
| asks, the game | 28, six types, counting the recursion | 15 at five types at the top, the same work inside |
| held by | `test_changes.py`, 21 | `test_changes.py`, 22: the same expressions as before, the refusal, and the lockless door |

**Found on the way, and fixed in the slice.**  The rule's machine was
first compiled through `pipeline.compile`, from inside a compile —
which holds the front end's lock, not reentrant — and the measurement
waited two minutes on itself.  The targeted tests had passed because
`test_changes.py` runs first and built the rule outside any compile.
The rule goes through the lockless door now, `pipeline._compile`, as
the stage does, and
`test_changes.py::test_the_rule_is_compiled_through_the_lockless_door`
builds it fresh with the locked door refusing.  Third time for this
seam — `doc/memory/a-run-silent-for-a-minute.md`.

**Not done here.**  `rules.ges` is not on the reference roster, since
it is the compiler's rule and not a library a program includes; F238
still owes the two refusals a line.

## Built — 2026-09-16: reader 4, and the second reflector

**The rule file is `gestate/rules.ges` now** — one file for what the
compiler decides over a type, a section per reader, one machine
(`stage.rules()`, through the lockless door, once per process) and one
door for asking it (`stage.ask`).  The zero rule moved in unchanged.

**The second reflector, `stage.reflect_data`:** the constructors of a
*ground* type as `rules.ges`' `List Con`, in declaration order, the
type's parameters filled in from the use — `Maybe Int`'s `Just` holds
an `Int`.  Ground on purpose: a declaration with its parameters open
is a scheme, and `Type` has no binder; the reader that needs one is
`deriving`, and that is the day the binder is designed.

**Reader 4, `audio._channels_out`:** `frameOf : Type -> List Con ->
Frame` in `rules.ges` decides what an output frame is — a `Float`, a
tuple of `Float`s, or one constructor of `Float`s — and answers a count
or *which part* is not a `Float`; `audio.frame_of` composes the English
the four refusals always said.  Its `case` over `TApp`, `TCon`,
`tuple_parts` and the constructor table is gone.  Nine tests in
`test_stage.py` hold the counts and the five refusals, which nothing
had pinned before; `test_audiovoices.py`'s end-to-end refusal holds as
it did.

## Built — 2026-09-16: reader 5, the flatness judge

**`is_flat` and `why_not_flat` keep their names and callers; the
decision is `rules.ges`' `flatness`.**  A number is flat, a variable
and a function are not, a tuple is flat when its components are, a
former in `notFlatFormers` is not, a base type in `flatBase` is, and a
declared type is flat when it is not recursive and every field is —
the two name tables moved into the language with the walk.  The answer
is *why not*, as data: which component, which field, which former,
recursion, or a name nothing declares; `types.py` composes the English
the tests pin, and the two tables' English stays there beside it.

**Two things the reader needed, said out loud.**

- **`TyVar Text` joined `Type`** — a *free* variable with its name, not
  a binder.  The judge's honest answer for a variable is *not flat: a
  variable*, so the reflector says one when asked (`variables=True`)
  and still refuses one by default; the reifier refuses a `TyVar` on
  the way back, because nothing binds it.  A scheme's binder is still
  not there.  The card's Q4 stands: the zero rule refuses.
- **The third reflector, `stage.reflect_closure`:** every declared type
  reachable from a type through constructor fields, each with its
  constructors at the instantiation first met, keyed by name the way
  recursion is detected.  A rule that walks structure gets the whole
  structure as one value.

**What stays in Python, and why.**  `audiograph._settled` and
`_monomorphise` — a signature's variables replaced by a witness before
the judge is asked — are the *scheme* decision, and they stay until
the binder exists; the card said reader 5 is where a scheme reaches
the reflector on purpose, and with the witness in front of it, it does
not.

| | before | after |
|---|---|---|
| the decision | `is_flat`, `_adt_flat`, `why_not_flat`, two tables — 70 lines of `types.py` | `flatness` and six helpers, 50 lines of `rules.ges`; 40 lines of English in `types.py` |
| a recursive user type, asked why | looped for ever composing the sentence | *a data type whose field `Tree` is recursive…* |
| `moods.ges`, one second through `audioperform` | 2.66 s | 2.74 s; the judge asked 194 times at 5 types, the first ask 0.32 s (the rule file's compile, once per process), the rest under a millisecond |
| held by | `test_audiofragment.py`'s two flatness tests, the phrases pinned | the same two unchanged, plus the closure and the recursive type in `test_stage.py` |

**Reader 6 is not a reader of what the checker cannot see.**  Looked
at before taking it: `reference.py` reads the *written* signature by
design — *a reference is what the library promises* — and the written
signature is exactly what the checker holds the body to, so the text
it reads is a checked thing.  What is unchecked there is argument
names, which are not types.  Struck from the list, with this sentence
as the reason.

## Built — 2026-09-16: reader 3, the layouts

`audioextract._layout` reads its constructors from `stage.reflect_data`
now — declaration order, parameters filled in from the use, every
field ground — and recurses through `stage.unreflect`, the reifier
made a function so the walk keeps the compiler's types for naming.
Its own walk over constructor types, the arrow-splitting and the
substitution, is gone; what it still decides is the one sentence it
always did, *a tuple is laid out like a one-constructor record*, and
that stays with the builder because it is about the machine's tags and
not about the type.  `reflect_data` is now the one place in the tree
that says what a declared type is made of at a use, and three readers
ask it.  Held by the extraction, graph, LLVM, live-update and fragment
tests as before, 170 green, and the round-trip test in `test_stage.py`
holds `unreflect` against `reflect`.

## What a session does now

Readers 1, 3, 4 and 5 are moved, 6 is struck, and F238 is resolved;
the postcondition holds and the tests say so.  Left is `deriving` (2),
the reader that needs the binder, which is a question for him and not
a slice — Q5 above.  His answer to it is what closes the card, either
way.
