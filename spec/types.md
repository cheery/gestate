# Well-Behaved, Simple Types and Type Inference

Description of a design for a type system
and inference engine for a pure functional language.
The goal is a system that infers or checks good types
even with no annotations, and gives comprehensible errors when it fails.

Every recommendation is given to keep the inference algorithm simple.
Even at the cost of expressiveness.

Summary: **we use bidirectional Hindley-Milner as the spine,
generalize only at `let`, keep unification syntactic and total,
and treat extra features as something bolted onto that spine
rather than something that changes how the spine works.**

---

## 1. The spine: Hindley-Milner, implemented bidirectionally

Implement **bidirectional type checking with local inference**,
compute same principal types as Algorithm W for the HM fragment
but produce far better error messages and localized failures.
Distinguishing "checking a term against an expected type"
from "synthesizing a term's type from scratch."

Two mutually recursive judgments instead of one:

```
infer :: Env -> Expr -> (Type, Substitution)     # synthesis: "what type is this?"
check  :: Env -> Expr -> Type -> Substitution    # checking: "does this have this type?"
```

Rule of thumb for which mode to use where:

- Variables, literals, function application, and anything with an
  explicit annotation: **infer** (synthesize a type bottom-up).
- Lambdas, `case` branches, and anything whose type comes from
  *context* rather than its own shape: **check** against the type flowing
  in from outside.

```
infer(Γ, x)                = Γ(x)                                 # lookup
infer(Γ, e1 e2)            = let (t1, σ1) = infer(Γ, e1)
                                 t2 = check(Γ, e2, argOf(t1))
                             in resultOf(t1)
check(Γ, λx. e, t1 -> t2)  = check(Γ, x:t1, e, t2)
check(Γ, e, t)             = let (t', σ) = infer(Γ, e)
                             in unify(t, t')                      # fallback
```

Rationale for this choice:

- **Error locality.** In Algorithm W, a type error in one branch of a
  program can surface as a unification failure somewhere far away.
  Bidirectional checking pushes *expected* types inward from annotations
  and context, catches most errors at the actual site of the mistake.
- **The natural place to add extensions.**
  Most extensions require "sometimes I already know the type I'm expecting"
  and `check` mode gives this for free.
- **It matches what programmers expect.** 
  Function's parameter types flowing from call sites,
  and case expressions branches all need to agree with expected result type.
  Bidirectional typing makes that explicit in the algorithm.

Keep Algorithm W's **unification-based core** underneath both judgments.
Bidirectional typing is a control-flow discipline ton top of standard unification
rather than a replacement.

---

## 2. Unification: syntactic, total, with a mandatory occurs check

Implement unification as ordinary first-order syntactic unification
over type terms, with substitutions represented as an immutable,
composable finite map (or mutable union-find over type metavariables).

```
unify :: Type -> Type -> Either TypeError Substitution

unify (TVar a)   t              = bind a t          # with occurs check
unify t          (TVar a)       = bind a t
unify (TCon c ts) (TCon c' ts')
  | c == c', length ts == length ts' = unifyAll ts ts'
  | otherwise                        = Left (TypeMismatch ...)
unify (TFun a b) (TFun a' b')  = unify a a' >> unify b b'
unify t1 t2                     = Left (TypeMismatch t1 t2)
```

Properties we demand:

- **Mandatory occurs check.** `bind a t` must fail if `a` occurs free in
  `t` (e.g. unifying `a` = `List a`).
  Leaving occurs check away is not an acceptable speed hack.
  There is no scenario in a language without genuine recursive types
  such that skipping occurs check is safe.
- **Totality.** `unify` must terminate on all inputs and never crash.
  Every failure path yields a `TypeError` *value* — never a pattern-match
  failure or an internal crash.

  In the implementation that value is carried by a raised `UnifyError`
  rather than returned in an `Either` (`fixme.md` F30).  The distinction the
  rule exists to enforce is that a failure cannot be silently ignored, and a
  Python exception already cannot be; `Either` is how Haskell gets that
  property, not the property itself.  **The argument order is part of the
  interface** — `unify(actual, expected)` — because the message reads
  "expected …, got …" and calling it the other way round swaps the two
  roles in every error a user sees.
- **Rigid variables are not bound.** `bind a t` must fail if `a` is a
  signature's variable being checked against (§3.1).  The pseudocode's
  first two lines therefore read "if `a` is a metavariable"; a rigid one
  falls through to `TypeMismatch`, with a message that says so rather
  than reporting two mismatched type constructors.

We also need some type-level computation,
it is introduced by the `typeclasses.md`.

---

## 3. Generalization: only at `let`, nowhere else

Types are only generalized at `let`-bindings and top-level declarations,
never at lambda arguments, and never implicitly anywhere else.
This decision keeps HM-style inference decidable.

```
generalize :: Env -> Type -> Scheme
generalize env t = Forall (freeVars(t) - freeVars(env)) t
```

```
let id = λx. x        -- id generalized to: forall a. a -> a
in (id 5, id True)    -- both instantiations well-typed
```

But:

```
λid. (id 5, id True)  -- ERROR: id used at two different types
                       -- without being let-generalized first.
                       -- This is correct rejection, not a bug —
                       -- lambda-bound variables are monomorphic.
```

You could have unrestricted polymorphism everywhere if you'd allow
type annotations at every polymorphic use.
However we want that inference always works for this language.

### 3.1 A declared signature is checked against *rigid* variables

Generalization is one half of the contract; the other is what happens when
the programmer writes the scheme down instead of having it inferred.

```
f : a -> Int
f x = x + 1           -- ERROR: `a` is the caller's choice, not `Int`
```

A signature's type variables are **rigid** (skolems) while its own body is
checked.  Nothing the body does may decide one:

- `unify` refuses to bind a rigid variable.  The other direction still
  binds — a metavariable *may* be bound to a skolem, which is what makes
  the body checkable at all — so the asymmetry is deliberate: a rigid
  variable is a constant that happens to be unknown.
- Instance resolution refuses to pick a dictionary for one.  A predicate
  on a rigid variable is not *ambiguous* (§`typeclasses.md`'s defaulting
  does not apply); it is decided by the caller, so only the signature's
  declared context can discharge it.  `f : a -> a ; f x = x + 1` needs
  `(Num a) =>` and is otherwise an error, not a default to `Int`.

Rigidity is confined to that body.  A *use* site instantiates the scheme
the ordinary way, into fresh metavariables, so `f : a -> a` is used at as
many types as the caller likes.

This is checking, not inference, and it is the reason the two judgements
of §1 are kept apart: `check` has the declared type in hand, which is
exactly the information "the caller chooses `a`" needs.

### 3.2 The value restriction (needed once you have mutable state or effects)

This feature won't be implemented into this system.
Mutable state and effects are not exposed such that we'd need this.

If your language is pure with no mutable references and no ambient effects
threaded through evaluation, you can skip this subsection — it doesn't
apply. If you have references, arrays, or any single-threaded mutable
state (`Ref`, `Array`, an effect system with mutation), you need the
**value restriction**: only generalize a `let`-binding if its right-hand
side is a *syntactic value* (a variable, literal, lambda, or constructor
application to values) — not an arbitrary expression.

```
let r = ref []          -- NOT generalized: `ref []` is not a syntactic value
                         -- (it's a function application)
                         -- r : Ref [a] with 'a' left as a genuinely fixed,
                         -- fresh monomorphic variable, not polymorphic
```

Without this restriction, polymorphic references are unsound: you can
store an `Int` into a supposedly-`forall a. Ref [a]` reference and read it
back out as a `String`, silently corrupting the type system's guarantees.
This is a real historical bug class (ML languages hit it before the value
restriction was standardized) — implement it from day one if you have any
mutation at all, rather than adding it later once someone finds the hole.

---

## 4. Algebraic data types: as ordinary constructors with ordinary types

ADTs do not have special-cased typing rules.
Each constructor is just a function with a type,
entered into the same environment as everything else.
Pattern matching is a separate `case` analysis compiled against those
constructor types.

Don't give ADTs special-cased typing rules. Each constructor is just a
function with a type, entered into the same environment as everything
else, and pattern matching is just `case` analysis compiled against those
constructor types.

```
Maybe a := Nothing | Just a

# registers in the environment:
Nothing : Maybe a
Just    : a -> Maybe a
```

Type-checking a `case` expression: infer the scrutinee's type,
then `check` each branch's pattern against that type and each branch's body
agains the (shared, unified) result type.

```
check(Γ, case e of { p1 -> e1; ... }, tResult) =
  let (tScrut, _) = infer(Γ, e)
  in for each (pi, ei):
       Γ' = checkPattern(Γ, pi, tScrut)   -- binds pattern variables
       check(Γ', ei, tResult)
```

**Exhaustiveness and redundancy checking** are separate passes
after type checking. They're treated as static analysis voer
the constructor set of the scrutinee's type, throwing an error
on missing constructors and unreachable branches. Keeping it separate
from the core type checker keeps both simpler and independently testable.

Recursive ADTs (`data List a = Nil | Cons a (List a)`) need no special
handling at all and fall out for free because `TCon` type constructors
are allowed to mention themselves in their own definition.
Nothing in the unification or inference rules assume finite unfolding.

---

## 5. Kinds: a minimal system, checked, not inferred with anything fancy

Once you have type constructors with parameters (`Maybe`, `List`, `Either`),
you need a kind system to reject nonsense like `Maybe Maybe` or applying a
type constructor to the wrong number of arguments. Keep this as simple as
possible:

```
kind ::= Type          # the kind of ordinary (inhabited) types, e.g. Int, Bool
       | Int           # needed for bounded and cyclic integer types.
       | kind -> kind  # the kind of type constructors, e.g. kind Maybe : Type -> Type
```

Kind checking is a second, much smaller HM-style inference pass
run over type expressions before value-level inference.
It uses the exact same unification machinery from Section 2 specialized
to kind terms instead of type terms.

```
kindCheck :: KindEnv -> TypeExpr -> Kind
kindCheck env (TCon "Maybe") = * -> *
kindCheck env (TApp f a)     = let (k1 -> k2) = kindCheck env f
                                   k1'        = kindCheck env a
                               in unifyKind(k1, k1') >> k2
```

Run this pass once, at the point each type declaration is processed, and
reuse the results everywhere; don't re-derive kinds during ordinary value
type checking.

---

## 6. Recursive types: only through named data declarations

Types can be recursive only through abstract data type declarations.
Do not allow type aliases types to recurse. eg. `type T = List T` not accepted.
Do not allow unification without occurs check.

- recursive types are always with a new, distinct named type.
- Expand type aliases `type Name = String` eagerly before they reach the unifier.
- Reject type aliases that are self-referential directly or transitively.

---

## 7. Higher-rank types: opt-in via annotations, not inferred

It is unlikely that the language gets higher-rank types, eg.
`forall` that appears somewhere inside the type rather than at the top.

Once `forall` can nest, the type inference ceases working reliably.
See *Practical type inference for arbitrary-rank types* for more information on this.

We would require an explicit type annotation whenever a higher-rank type is introduced.
This is the cleanest teachable boundary and doing otherwise makes the inference unpredictable.

However higher-rank types won't be implemented in near future.

---

## 8. Staging: two phases, two stages, three crossings

*2026-09-18, `card:strict-forms.md` §"Read — 2026-09-18", item 7 — the
formal statement, small.  The compiler's stage (`gestate/stage.py`,
built 2026-09-14) written the way Allais writes his calculus, with
Kovács's three properties each naming the test that holds it.  Guillaume
Allais, "Scoped and Typed Staging by Evaluation", PEPM '24; András
Kovács, "Staged Compilation with Two-Level Type Theory", ICFP 2022 —
both read at their page, `doc/memory/the-language-goal.md` §"Read —
2026-09-18".*

**Two phases.**  `src` is the program as written: a type position may
hold a splice `$(e)`, an expression may hold `document "k"`.  `stg` is
the program after `stage.staged`: the same items with every site
replaced, and **no site remains** — every later pass (classify,
exhaustiveness, desugaring, kinds, inference, the monotone and subgrammar
checks, both machines, the model-checker) reads `stg` only.  Allais
gets this by indexing terms with the phase so that a `stg` term has no
quote or splice constructor; the tree gets it by a refusal at the end of
`staged` and a test.  `$` is `infixl 9`, the tightest infix operator, and
a program may not redeclare it (`spec/syntax.md`).

**Two stages.**  Stage one is the prelude and every item a site's
expression needs, transitively — the cut, by name, on demand, no marker
in the file.  It is evaluated once on the G-machine, through the running
front end's own door: items, never text, no seam, no lock.  Stage two is
every item that holds a site or mentions one, transitively, and `main`.
A stage-one item may not mention a stage-two one: *a type computed from
a value cannot be computed from itself*, refused with both names.  That
is Kovács's stability under substitution read as a scoping rule — what
stage one computes cannot depend on what its answer types.

**One language, three crossings.**  There is no `⇑A` and no second
universe: the same definitions serve both stages, which Allais writes as
constructors polymorphic in phase and stage and Kovács leaves open as
stage polymorphism.  What crosses from stage one into stage two is a
*value*, spliced into `stg` syntax at one of three positions — each its
own `∼`:

| position | the stage-one value | how it becomes `stg` syntax | since |
|---|---|---|---|
| a type position: `$(e)`, `document "k"` | a `Type` — `facts.ges`' six constructors | `stage._type_val`, into the type the checker reads | 2026-09-14 |
| a scalar definition of one finite parameter, in the audio fragment | its answer at each value of `Cyclic n` or `lo .. hi` | `audioextract._table`, into the `prim_eq_int` cascade a hand-written `case` becomes (`spec/liveaudio.md` §"Step functions") | 2026-09-18 |
| a static position: an envelope's points | a `List Envelope`, closed over stage-one globals and static parameters | `audioextract._points`, into the tree `envexpand` builds for a literal | 2026-09-18 |

The second and third are Kovács's cofibrancy and his `A ≤ ⇑A`
coercion, and the stage of a parameter in the third is *inferred and
never written* (`spec/liveaudio.md` §"Step functions").  The reverse
direction — a type the checker inferred, read as a `Type` value by
`stage.reflect` and decided over in `gestate/rules.ges` — is a compiler
pass over types as data and stands outside this calculus: neither paper
has it; Shields, Sheard and Peyton Jones is its reference.

**Three properties, Kovács's Definition 4.2, and the test that holds
each.**

| property | what it says here | held by |
|---|---|---|
| **stability** — `Stage ⌜t⌝ = t` | a program with no site is untouched: `staged` answers the very list it was given, and in a sited program every unsited item is the same object | `test_stage.py::test_a_program_with_neither_form_pays_a_substring_test`, `::test_staging_swaps_the_sites_and_touches_nothing_else` |
| **soundness** — `⌜Stage t⌝ = t` | what the stage puts in is what the author would have written | reflect then reify is the identity on twelve types, `::test_a_ground_type_reflected_then_reified_is_itself`; the table renders the golden pinned to the hand table, `test_audiograph.py::test_a_tune_written_as_a_list_over_a_finite_type_renders_the_golden`; the points render the literal, `::test_an_envelopes_points_are_a_static_position_however_they_are_spelt` |
| **strictness** — staging computes nothing in the object theory | the stage swaps sites and performs no β, no inlining, no normalisation of stage two; a table is the *same shape* a hand `case` has, not a folded constant | the swap test above; the seven-comparison chain in the tune test |

**The negative space, which is most of the calculus.**  No intensional
analysis of a stage-two term: `rules.ges` decides over `Type` as data,
which is the only reflection Kovács §6 admits under stability under
substitution and the only one Jay and Palsberg leave HM-inferable.  No
scheme in `Type`: a `TyVar` reaching a splice is refused, because nothing
binds it; a binder is the day `deriving` moves.  No effects at stage
one: `document` reads the program's own `model`, and the day a stage
reads a file it asks as data and the host answers, `Act`'s factoring a
second time.  No terms as values: no quotation, no `Decl`; the day one
is proposed, Jay and Palsberg is the price list.  Every one of these is
a refusal at a line, not a silent hole.

**What it is not.**  Not a proof: Allais's is checked in Agda, Kovács's
in a presheaf model, and this is a page that names which test stands
where a lemma would.  A test is a witness, not a boundary
(`doc/memory/declare-parity-derive.md`) — the day the language grows a
second universe or a quote, this section is the first thing that is
wrong.

---

## 9. Error messages: treat as a first-class output of the algorithm, not an afterthought

Type checker should be well-behaving were it to succeed or fail.
It it achieved by the following rules:

- **Track source locations through unification.**
  Every type and metavariable carries the source span it originated from.
  When `unify` fails, report original source locations.
  This should also consider the generated type aliases.
- **Report errors at the `check` call not at the `infer`.**
  Mismatch at `check` means we know the expected type from context.
  It allows writing "We expected type `T` because of X, but it has type `U`.

Thread source spans through `Type` and `Kind` representation from the beginning.
Rest should come out naturally from the bidirectional type checking algorithm in Section 1.

---

## 10. Summary checklist

1. **Bidirectional infer/check** as the algorithm's spine.
2. **Syntactic unification with mandatory occurs check.**
3. **Generalization only at `let`.**
4. **ADTs as ordinary constructor functions.**
5. **Minimal kind system.** Checked via the same unification machinery.
6. **Non-recursive type alias expansion and nominal data types.**
7. **Source-location-aware, check-mode-aware error reporting.**

Important detail: Every extension reuses the same unification core
and is never a new orthogonal mechanism.
Every feature you do support is explainable as a small local extension
to the same core idea instead of being a separate special case
the rest of the compiler has to know about.
