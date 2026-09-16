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

## The postcondition, before anything is built

*The rule that says what the zero change at a type is, is written in
the language and read by the compiler; and a type the rule cannot
answer is refused at compile time, at a line, rather than answered
with nothing.*

## What a session does now

Q1–Q4 are his, batched above; the reflector and its round-trip test
are common to every answer and are the first thing to build.  Then
the zero rule in `.ges` under Q2/Q3's answers, held to parity with
`changes.py` on `tic-tac-toe-facts.ges`'s 28 before the Python
decision is deleted.  Readers 2–6 wait on this one landing.
