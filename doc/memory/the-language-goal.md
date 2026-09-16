---
name: the-language-goal
description: "Henri's short-term goal, 2026-08-20, in his own notes: a language that compiles to wasm, is easy to model-check and to study, and is optimised for reading — with later tunings for UI code, concurrency, live coding and mathematical code; and since 2026-09-15 the direction beyond it, a general-purpose multi-staged language, where each stage is a moment more type information arrives — the capability, not an ecosystem"
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
   with *no caller yet*.  This direction is the caller, named; not yet
   pulled.  The precise research question: a stage's inferred types
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
