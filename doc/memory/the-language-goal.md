---
name: the-language-goal
description: "Henri's short-term goal, 2026-08-20, in his own notes: a language that compiles to wasm, is easy to model-check and to study, and is optimised for reading — with later tunings for UI code, concurrency, live coding and mathematical code; and since 2026-09-15 the direction beyond it, a general-purpose multi-staged language, where each stage is a moment more type information arrives — the capability, not an ecosystem; the two-level papers read 2026-09-18"
metadata:
  type: project
---

**Stated in his own notes, 2026-08-20**, and not derivable from the
repository, which is why it is written here:

> *"Tavoite lyhyellä ajalla voisi olla että mulla olisi koossa kieli
> joka kääntyy wasmiin ja jota on helppo mallintarkistaa ja tutkia.
> Optimoitu lukemista varten."*

A short-term goal of **a language that compiles to wasm, is easy to
model-check and to examine, and is optimised for reading.**  Then, as
things that would be nice rather than needed: tunings for interface
code, for concurrency, for live coding, and for mathematical code.

**Why this is worth having written down:** three of its four properties
are already vision lines wearing other clothes — *optimised for reading*
is `vision.md`'s cognitive-weight argument, *easy to model-check* is
*won't ever be untested* pushed upstream into the language, and the four
tunings are the domains gestate already lives in.  What is **new** is
**wasm as the target**, which nothing in the tree says.

**And it sits against a deferral.**  `card:work-environment-ai.md`
defers the language deliberately — the environment needs none of it,
gestate already has a language, and the LP-IR paper it cites becomes
relevant only at an OS phase, if ever.  That deferral was written
without this goal on the table.  **Not a contradiction to resolve by
guessing**: the card defers *a new language for the environment*, and
this is a goal about *the* language.  Whether they are the same object
is Henri's to say.

**How to apply:** do not act on this — it is a stated direction, not a
card, and by [[capacity-is-not-a-caller]] a direction is not yet a
`because`.  Do notice it when the two touch: if the environment work
starts pulling a language after it, this note is the reason to stop and
ask rather than to design one.

## The direction beyond it — 2026-09-15, his words

Asked at the end of a rest day, before sleep, out of the staging work
on `card:strict-forms.md`:

> *"could gestate become a general purpose programming language?  This
> staging -thing has been making me to think... each stage is simply a
> moment when we discover more type information about the task at hand
> and benefit from that somehow.  There is perhaps no reason that a
> multi-staged type-principled language would lose to language like
> python is.  it's other way around although I see that is a research
> grade question."*

And on what is wanted from it:

> *"I don't want to write an ecosystem that pairs with python.  Instead
> what I want is the capability to go into that direction.  I trust
> that the ecosystem builds itself when there is the reason for it to
> do so."*

**What was said back, and he took as the shape of it.**  Three things
the direction decomposes into, and he wants all three, *"but I think
that right now"* — so only the third is done, and it is this section:

1. **The theory.**  His sentence needs more than MetaOCaml or Zig give:
   stage n+1 must be able to read the types stage n *inferred*, as
   values.  *Two sources read at their page 2026-09-16, §"Read"
   below.*  That is the reflection Kiselyov & Imai regret lacking, and
   the direction `card:strict-forms.md` §"Read — 2026-09-14" declined
   with *no caller yet*.  **That sentence was about the program; the
   host has callers already** — Henri asked for them on 2026-09-16 and
   the tree answered, §"The callers" below.  The precise research question: a stage's inferred types
   reified into the next stage's data, sound, and HM-inferable within
   each stage, the model-checker still seeing the last stage only.
   That last property is why this route is preferred over full
   dependent types for the goals above.
2. **The self-hosting test.**  *General purpose* is a test, not a
   property, and the tree holds one: ten Python files write `.ges`
   text in f-strings, because the host is Python.  The naive thing is
   to write one host — the reactive layer, or the score box — in
   gestate, and read off what it lacked as a list.  A guess, unmeasured:
   modules first (the card already notes the stage restriction has
   nowhere to land without them), then mutable state, then strings.
3. **The direction, written down** — here.

**What it is not.**  Not a card, and not a `because` — the rule of
§"How to apply" above stands unchanged.  Python is already multi-stage
(a JIT specialising, a dataframe typed when its file is read); what
this direction claims is only that stages an author *writes* can be
checked and stages that *happen* cannot.  Where staged languages have
lost is reading — a second syntax for the second stage — and
*optimised for reading* above is the ruler that decides it; the `$(e)`
splice already in the tree is the first bet.  Ecosystem is most of why
Python wins and is explicitly not to be built.

**How to apply, added:** when a language decision on a live card has
two answers and one of them keeps the general-purpose door open at no
cost to the three properties above, that is the tiebreak, and say so
on the card.  When it would cost one of them, it is his to weigh, and
this section is what to cite when putting it to him.

## Read — 2026-09-16: the theory's two sources, at their page

*The reading is the session's.*  Both from `~/misc/papers/`, fetched by
Henri after the session named them from memory the same morning.  One
of the two names was wrong, and the correction stands where it belongs.

**Mark Shields, Tim Sheard and Simon Peyton Jones.  "Dynamic Typing as
Staged Type Inference."  In *Proceedings of the 25th ACM SIGPLAN-SIGACT
Symposium on Principles of Programming Languages* (POPL '98), San
Diego, pages 289–302.  ACM, 1998.**

*What it is.*  λdyn, a call-by-value calculus with the Davies–Pfenning
and Taha–Sheard operators — defer `⟨t⟩`, splice `~t`, and `run(t, w)`
where `w` is an *exception expression* evaluated when the deferred code
turns out ill-typed.  Every deferred expression has the one type `⟨⟩`;
inference of its body is deferred to the stage that runs it, and §4
does that incrementally: at compile time each splice is annotated with
the most general type its context admits and each defer with the most
general type of its body, both open in type variables the defer binds;
at run time a splice unifies the two and a run unifies the body's type
with the run's context, and that residue is all the inference done
late.  *"Type information flows both ways across a splice"* (§4).
Syntactic soundness and subject reduction, Wright–Felleisen style
(§5.5, Theorems 3 and 4).

*Against the direction's sentence.*  It is the sentence's title and the
other half of the sentence.  Their stages are run-time stages, and what
arrives late is checked when it arrives — by `run`, with a failure
branch.  That is the case §"What it is not" above declines — *stages
that happen cannot be checked* — and this paper is the rigorous account
of what checking them anyway costs: one universal type `⟨⟩` for all
code, so no polymorphism shows at the type and it is hidden in run-time
annotations instead (§2, the first drawback they charge to `typecase`,
and §4, their fix); an exception expression on every `run`; and §6.1 —
a splice-full term may not be let-generalised, because a dependency
between a splice's type and what is spliced into it is higher-order
unification (Abadi, Cardelli, Pierce and Rémy's functor variables),
which they refuse syntactically.  Nothing in it reifies a type into a
value a program can read: the dynamic type scheme lives *inside* the
run-time value (§4) and is never data.

*What it gives the tree, three things.*

1. **The tree's cut is their `var` rule.**  A context carries a stage
   number per binding and a use needs `m ≤ n` (Figure 5, rule var): a
   later stage may use an earlier stage's binding without coercion —
   *cross-stage persistence*, §5.3 — and never the reverse.  Stage-two
   items mentioning stage-one definitions is the first; the refusal
   *a type computed from a value cannot be computed from itself*
   (`gestate/stage.py`) is the second, and now has a rule to cite.
2. **The free-variable answer.**  A closed deferred term with residual
   free type variables is run by instantiating each to the empty type
   `0`, because the term is parametric in them (§5.4.2, rule run).  For
   a reflector that would read an inferred scheme back into `Type`,
   that is the ground case done honestly: a variable that survives to
   a splice is either bound by the reflected scheme — which needs a
   binder constructor `Type` does not have — or refused at the line.
   Their annotated defer `⟨ᾱ:∗ ⊢ t : τ⟩` (Figure 2) is the data shape
   a reflected scheme would take: the bound variables listed beside
   the type.
3. **Why the on-demand cut is cheaper than theirs.**  Their §6.1
   trouble arises because a splice's expression may itself be open,
   spliced under a binder.  A `$(e)` here is closed at stage one by
   construction — the cut blanks everything that mentions the splice —
   so no unification crosses the boundary and there is no
   let-generalisation to restrict.  A property of the tree's design
   worth stating on the card the day a splice is allowed under a
   binder.

**Barry Jay and Jens Palsberg.  "Typed Self-Interpretation by Pattern
Matching."  In *Proceedings of the 16th ACM SIGPLAN International
Conference on Functional Programming* (ICFP '11), Tokyo, pages 247–258.
ACM, 2011.**

*The correction.*  The session named "Brown and Palsberg's typed
self-interpreters" from memory.  That is a later pair of papers by a
different first author (Matt Brown and Jens Palsberg, POPL 2016 and
POPL 2017 — from memory again, unread, and named only so the wrong name
is not carried forward).  What was fetched, and what the description
fit, is this one.

*What it is.*  The blocking factorisation calculus — combinators `Y K S
F E B`: `F` factorises a compound into its two parts, `E` decides
equality of operators, `B` blocks evaluation — with a quotation `'t`
that keeps the type: `'t : T` iff `t : T` (Theorem 7.5).  A typed
self-recogniser `unquote : ∀X. X → X` and a typed self-enactor `enact :
∀X. X → X` (Theorems 7.7, 7.8), System F types and no type:type rule,
checked by a partial inference algorithm.  Their own weakness (§7.5):
not *adequate* — a term of type `T` need not be a quotation, so the
type system does not tell a term from its representation.  Of Rendel,
Ostermann and Hofer's five properties they have representation,
self-interpretation and reflection, and not adequacy or first-class
interpretations (§9).

*Against the direction.*

1. **It answers a stronger test than the one set.**  Item 2 above is
   *write one host in gestate* — modules, state, strings — and this is
   *interpret gestate in gestate with the types kept*.  The two tests
   find different lacks: the first an ecosystem's, the second the type
   system's.  The direction's test stands; this is what the second one
   would cost, and it is not asked for.
2. **What reflection costs, precisely.**  `F`, which inspects a
   compound's structure, needs a rank-2 type — `∀Z.(Z → X) → Z → Y`,
   the `Z` standing for the unknown type of a compound's second half
   (§7.1) — and `E`, which compares operators, has *no principal type*
   (§7.1) and is kept out of every pattern by the "Sherlock Holmes"
   case of Figure 4.  So **an operator that reflects on a term's
   structure within its own stage costs HM.**  That is the direct hit
   on *HM-inferable within each stage*, and it is also the argument
   for the tree's route: `Type` at stage two is an ordinary ADT,
   matched by an ordinary `case`, and nothing at stage two inspects a
   stage-two term.  Reflection *across* the boundary is data;
   reflection *within* a stage is `F` and `E`.  What the route loses
   is what they lose, adequacy: a `Type` value need not be the
   reflection of any inferred type, and a `TyCon "Nonsense"` reifies
   to a refusal, not to a type.  They accept the loss and say so.
3. **No quotation here, so none of its bill.**  A stage-one value is a
   `Type`, never code; of their five properties only representation,
   and of types not terms, is in play.  The day a `Decl` value or a
   quote is proposed (`card:strict-forms.md` Q6), this paper is the
   price list.

**What the two say together, for the research question.**  The
question was: a stage's inferred types reified into the next stage's
data, sound, HM-inferable within each stage, the model-checker seeing
the last stage only.  Shields, Sheard and Peyton Jones give the shape a
reflected type must carry — a scheme with its bound variables listed —
and the ground-instantiation rule for what survives; Jay and Palsberg
show that HM is lost the moment reflection is over *terms* rather than
over *types as data*, and that adequacy is the price of keeping it.
Neither builds a `typeof`.  The narrowest form both readings leave
open: a stage-two form reading a stage-one definition's *closed*
inferred type as a `Type` value, a scheme refused at the line, HM
untouched on both sides, the checker seeing stage two only — the
reflector being the inverse of `gestate/stage.py`'s reifier on the
ground fragment.  Still no caller, and the direction is still not a
card.

## The callers — 2026-09-16, found in the tree at his ask

*"I thought we had some caller for it already"* — Henri.  He was right:
the card's *no caller yet* was carried forward without a grep, and the
grep finds six places where **Python reads a type the compiler holds**
and computes something from it.  Every one is a program that would be
written in the language, over a `Type` value, if a stage could read
the type.  In order of how squarely each is the theory's case:

| | where | reads | computes | declared or inferred |
|---|---|---|---|---|
| 1 | `changes.py` — `Changes.zero`, `_gen_dummy` | the monomorphic types the specialiser reached | `Δ(A×B)`, `Δ(A→B)`, `dummy_T` per ADT, `bottom_S` per set — a whole type-directed program | **inferred**; and `free_vars(t) → UNIT` is the scheme case of Shields et al., done by hand |
| 2 | `deriving.py` | a type declaration | `Show`, `Eq`, `Ord` instances as surface AST, three classes hard-coded | declared — Template Haskell's `reify`, and the card's item E |
| 3 | `audioextract._layout` | constructor types of every ADT the graph carries | the LLVM struct layouts — *the only place that still has the compiler's types* | declared — Kiselyov & Imai's caller, serialisation |
| 4 | `audio._channels_out` | the type of `sound` | how many channels the frame has, because the machine cannot tell `Int` from `Float` by value | **inferred** |
| 5 | `audiograph._settled`, `_monomorphise` | a signature's type with variables | *flat once settled*, by instantiating each variable to a witness | declared, open — the free-variable case again |
| 6 | `reference.py`, `session.py` §argument names | the signature **as text** | the reference pages and the editor's argument names | declared, and read off the line rather than off the checker — `[[declare-parity-derive]]` |

**What this changes.**  The theory's precise question stands, and its
first arm is now named: **1**, because it is a program computed from
*inferred* types, in the host, with the polymorphic case already
visible as a dead branch.  Writing `zero` and `dummy` in `.ges` over a
`Type` value read off the specialiser is the self-hosting test of item
2 and the reflector of item 1 in one slice, and it would be the first
stage-two program to need a type it did not write.  Still not a card —
the `because` would be that the host's six readers are six places the
checker cannot see, which is `[[declare-parity-derive]]`'s argument
and his to weigh.

## Read — 2026-09-18: the two-level papers, at their page

*The reading is the session's, at Henri's ask the same morning: "where
could we apply these papers in our work?  Right now we've got some
kind of staging, but how could we go further there?"  Both from
`~/misc/papers/`.  The work items the reading leaves are on the live
card, `card:strict-forms.md` §"Read — 2026-09-18: two-level type
theory, and seven places it reaches"; this section is what the papers
are and what they say about the stage the tree already has.*

**András Kovács.  "Staged Compilation with Two-Level Type Theory."
*Proc. ACM Program. Lang.* 6, ICFP, Article 110, 30 pages.  ACM,
2022.**  Two-level type theory, borrowed from synthetic homotopy
theory, read as a staged language: universes `U0` (runtime, the object
theory) and `U1` (compile time, the meta level); every type former
stays within one stage; lifting `⇑A : U1` for `A : U0`, quote `⟨t⟩ :
⇑A`, splice `∼t : A`, definitional inverses.  Staging is
evaluation in the presheaf model over the object theory's contexts
(§4), and it is a *strong conservativity* theorem: soundness `⌜Stage
t⌝ = t`, stability `Stage ⌜t⌝ = t`, strictness — no β-reduction in the
object theory, so the output is the program and not a normal form
(Definition 4.2).  Types may be staged, which no earlier system
allowed (§2.2, `Vec : Nat1 → ⇑U0 → ⇑U0`).  Binding-time improvement is
rewriting along the preservation isomorphisms of §2.3, and Danvy's
"trick" is *cofibrancy*: a function out of a finite meta type is a
finite product, so it serialises.  §2.4 varies the object language —
monomorphic, so *polymorphic functions cannot be stored inside
runtime data*; and representation-polymorphic, `Rep : U1` indexing
runtime types.  §6: intensional analysis of object terms is
incompatible with stability under substitution (the Yoneda argument);
stability under *weakening* only permits it and costs the object
theory its dependent and polymorphic types.  No effects at the meta
level; let-insertion, more stages and stage polymorphism are §8's
future work.

**Guillaume Allais.  "Scoped and Typed Staging by Evaluation."  In
*PEPM '24*, London, 11 pages.  ACM, 2024; arXiv:2310.13413v3.**  The
same calculus, minimal and intrinsically typed in Agda: terms indexed
by a *phase* (`src` before staging, `stg` after) and a *stage* (`sta`,
`dyn`), the static stage available only in the source phase, lifting
only at `sta`, quote and splice only at `src` — so a staged term
**cannot contain a static subterm, by construction** (§3).  Staging is
one evaluation (§4): static values are host values, dynamic values are
staged syntax, quote and splice are the identity in the model,
application is `$$` at the static stage and the syntax constructor at
the dynamic.  The two layers need not share features: §5 adds pairs at
the static stage only, and §6 makes the dynamic layer a circuit
language — `nand`, `par`, `seq`, `mix` — under a functional static
layer, which reads Quipper and EWire as two-level theories after the
fact (§7.3).  No let-insertion; purely generative.

### What the tree already is, in their words

| the tree | the papers' name for it |
|---|---|
| `Type` in `facts.ges`, five constructors and a free variable | Kovács §2.2, the deep embedding `Ty : U1` with `EvalTy : Ty → ⇑U0`; `stage._type_val` is `EvalTy` |
| `$(e)` in a type position | the splice `∼e`, restricted to types — the case Kovács says no earlier system had |
| the on-demand cut: an item mentioning a splice is stage two, transitively (`stage._names`, an over-approximation by name) | a name-walk standing in for what 2LTT decides by universe — anything typed at `U1` is staged away, and a `U1` value at `U0` is a type error, not a cycle refusal |
| one prelude serving both stages | Allais §3.2, constructors polymorphic in phase and stage; Kovács §8 calls it stage polymorphism and leaves it open |
| the audio fragment — first-order, flat types, no lists, `on` needs its points at the call site (`spec/liveaudio.md` §"Step functions", `[[gestate-language-pitfalls]]`) | Kovács §2.4.1 monomorphization and §2.4.2 representation polymorphism; *polymorphic functions cannot be stored inside runtime data types* is the fragment's first rule word for word, and the flatness judge decides a `Rep` |
| `!x`; a numeric literal lifts on its own and a named `Float` does not | the serialisation map `A1 → ⇑A0` (Sheard and Taha's "lifting"), and the coercive subtyping `A ≤ ⇑A` of §2.3.2 inserted at literals only |
| the integer `case` table of `spec/liveaudio.md`, and `roll.ges`' `rollNum` to sixty-four | the trick, §2.3: `Cyclic n`, `lo .. hi` and `Bounded` carry their size in the type, which is cofibrancy |
| `stage.reflect` then `_type_val` is the identity on twelve types (`test_stage.py`) | soundness and stability, Definition 4.2, held by a test for the type fragment |
| `rules.ges` deciding over `Type` *data* and never over a term | the §6 verdict, and Jay & Palsberg's above: reflection over types as data keeps stability and HM; over terms loses both |
| the machines and the model-checker see stage two only (item H of the card) | Allais's phase index — a `Term stg` has no quote or splice constructor — stated as a typing rule rather than a pipeline order |

So the stage sits on the sound side of every restriction the papers
draw, and got there by refusing the same things they refuse.

### What the papers do not answer

**The upward direction is in neither.**  2LTT computes object code
from meta values and nothing flows back.  `stage.reflect` and the four
readers in `rules.ges` read a type the checker *inferred* and compute
from it — the direction of Shields, Sheard and Peyton Jones above, a
compiler pass here and not a language stage, which is why it costs
nothing the papers warn about.  His sentence of 2026-09-15, each stage
a moment when more type information arrives, needs both directions at
once.  Kovács's nearest offer is §2.4.2: make the information you would
reflect an explicit meta-level *index* on the object type, a `Rep`,
computed by staging — for flatness, a signal's element type carrying
its representation.  The honest alternative to reflection, and much
larger.

**More than two stages is future work in both.**  An N-level theory
"appears straightforward" in syntax with "subtleties" in semantics
(Kovács §7), and stage polymorphism is unsolved.  The tree runs three
levels — the LLVM step functions, the G-machine substrate at frame
rate, the compile-time stage — with Python above them and one prelude
across the top two.  Allais's polymorphic indices are the nearest
account of that, and they are a workshop paper's device.

**Effects at stage one.**  The card's Q8 kept *in some cases the file
itself* for where `document` reads its schema — F#'s type provider
reading external data at compile time.  Kovács §7 has no meta-level
effects and suggests a monad.  The tree has the factoring already, in
`Act`: a program says what it wants done as data and the host
performs it.  The day stage one reads a file, a stage-one value that
*asks* for a schema and a host that answers is the same design a
second time, and stage one stays pure and cacheable.
