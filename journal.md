# journal.md — what was built, in order, and what it taught

**Past tense, and that is the whole distinction.**  `roadmap.md` says what
is left and why in that order; this says what happened.  The two were three
files for a while — Part I, Part II, and the completed
two thirds of `roadmap.md` — which were the same artifact written at three
different moments, and telling them apart cost more than reading them did.

**What is *not* here.**  Two registers, and they stay where they are because
their numbers are addresses that `gestate/*.py` cites:

* `fixme.md` — where the implementation disagrees with the specs.  Fifty-six
  distinct `F` numbers appear in source comments.
* `spec/errata.md` — where the specs disagree with the papers.  `D` numbers,
  cited the same way.

An entry in either is closed by marking it resolved, never by deleting it.
This file has no such contract: it is a narrative, and the way to use it is
to search it.

The three parts are chronological.  **I** is the language, built as
increments; **II** is making it usable by a person, built as phases; **III**
is the staged plan the roadmap carried until each stage was done.  Item
numbers are kept exactly as they were written, because `roadmap 2.1`,
`roadmap 2.3` and `stage 3` are cited from the test suite and from
`gestate/audiovoices.py`.

---

## Part I — Building the language

*Was Part I.*  Each increment produced an
end-to-end working pipeline; modules co-evolved rather than being
built in isolation.  All increments through 12 are complete.

---

### The rule

> **Do not build what nothing needs.**

A feature earns its place by having a caller — a program someone wants to
write, a spec obligation that is otherwise unmet, or a defect it is the fix
for.  "It is in the spec", "it would be useful", and "the paper has one" are
not callers by themselves.

This is the discipline Lean's library keeps, and the reason for it is the
same: every definition that exists must be maintained, kept consistent with
everything around it, and re-checked whenever anything it touches moves.  An
unused one costs all of that and returns nothing.  Worse, it *looks* like a
commitment — later work routes around it, or relies on it, before anyone has
established it was wanted.

Three consequences worth stating, because they are easy to get backwards:

- **A spec section is not a work item.**  `typeclasses.md` §7.3 describes
  existential dictionaries completely and well.  That is a design held in
  reserve, not a debt.  It becomes work the day a program needs one.
- **Recording an absence is doing the work.**  Where a paper or a spec
  asks for something nothing needs, the deliverable is the entry in
  `fixme.md` or `errata.md` saying so and why — not the feature.
- **A defect is always a caller.**  This rule never argues against fixing
  something that is wrong.  It argues against building something that is
  merely missing.

Applied, this closes all of stage 4 (`roadmap.md`) without implementing any
of it, and it is why several `fixme.md` entries are marked missing rather
than scheduled.

---

### Completed

| # | Feature | Key modules | Milestone |
|---|---------|-------------|-----------|
| 1 | Wire the pipeline | `declarations.py`, `desugar.py`, `pipeline.py` | Simple programs run |
| 2 | Monomorphic types | `types.py`, `unify.py`, `infer.py` | Int/functions type-checked |
| 3 | ADTs | Extended `infer.py`/`desugar.py`/`declarations.py` | `Maybe`, `Color` work |
| 4 | Polymorphism | `Scheme`, `generalize`/`instantiate` in `infer.py` | `let`-poly, SC-level poly |
| 5 | Kind checking | `kindcheck.py` | Rejects `Maybe Maybe` |
| 6 | Typeclasses | `constraint.py`, `elaborate.py` | `Show Int` works |
| 7 | Associated types | Extended `constraint.py`, `infer.py` | `Elem Int = String` resolves |
| 8 | Implicit params | Extended `desugar.py` | `given`/`using` works |
| 9a | FRP surface syntax + Expr nodes | `ESigCons`, `ESigHead`, `EDelay`, … (9 new nodes) | Parse + type-check FRP |
| 9b | G-machine `NSig`, `NChan` nodes | Reserved tags 90–96 | Heap nodes evaluate as WHNF |
| 9c | `SigCons`, `SigHead`, `NewChan`, `MkDelayAp` instructions | `compileC` extensions | `head (5 ::: never)` → `5` |
| 9d | Reactive driver | `reactive.py` (`ticked`, `advance`, `reactiveStep`) | Signal chains advance per input |
| 9e | `gfix` + reactive integration | `EGFix` as a letrec over `delay` | Guarded recursion unrolls per step |
| 9f | Rizzo's two later modalities + `⊛`/`5` | `FaL`/`ExL`/`Maybe`/`Sync` types; `EAppFa`/`EAppEx`; `<*>`/`<@>`/`\|>` | `map`, `mkSig`, `filter`, `sync` run (§20) |
| 9g | Clocks, ✓ frontier, Δ, surface guarded recursion | `cl`; `NSig.current`; `GmState.chans`; `_guard_recursion`, `:::` patterns | Combinators read as the paper writes them (§21) |
| 10a | Datafun type formers + surface syntax | `ESet`, `EFix`, `EFor`, `EBox`, `EUnbox` | `{1,2,3}`, `for`, `fix`, `Box`, `unbox` |
| 10b | Monomorphization + helpers | `helpers.py` (`eqA`, `unionA`, `bottomL`, `joinL`), `EqInt`/`LtInt` instructions | Per-type set operations work |
| 10c | Naïve `fix` and `for` | `fixLoop`, `forLoop` in `helpers.py`; Datafun desugaring in pipeline | `for (x in {1,2,3}) {x}` → `{1,2,3}` |
| 10d | Box intro/elimination | `VBox` in `desugar_type`; □ erasure at runtime | `Box Int` type-checks; `Box 5` → `5` |
| 10e | ϕ/δ seminaïve transform | `seminaive.py` (`phi`, `delta`, `transform`), `semifixL` | `f_phi`/`f_delta` generated where needed (`Plan`) |
| 10f | Boxes as pairs + the □ stripping rule | `monotone.py`; `_unpack_box`; bracket-aware layout | A signal can carry a Datafun fixed point (§22) |
| 10g | Monotone and discrete arrows | `~>`; `TFun.mono`; `has_nontrivial_order`; binder flavours | A signal's value can feed a Datafun query (§23) |
| 10h | Type subgrammars + monomorphization | `subgrammar.py`; `is_eqtype`/`is_fixtype`; per-type helpers | `fix` terminates by construction (§24) |
| 10i | Semilattice join | `\\/` operator; `EJoin`; `subset_L` convergence test | A Datalog query runs (§25) |
| 11 | ADT sugar | Skipped — `:=` syntax from inc. 3 already covers Part III |
| 12 | Musical primitives | `Cyclic`, `Bounded`, `Score` types; `TInt` type-level integers; `..` infix | Types parse + kind-check |
| — | `Num` typeclass | `fromInteger` desugaring; `ModInt` instruction; generic `Num (Cyclic n)` with `using n`; type-aware elaboration; per-SC constraint tracking | `main : (Num a) => a` |
| — | CLI type inference | `gestate/typecheck.py`; `gestate/show.py`; interleaved sig+source; canonicalized TVar names | `python -m gestate.typecheck file.ges` |

---

### Pipeline flow (current)

```
source
  → parse (syntax/)                    → VModule
      └ resolve fixities (descend.py)  → VInfix/VPrefix/VPostfix
  → classify (declarations.py)         → Program + class/instance/adt tables
      ├ expand type aliases            → cycle-free, alias-free types
      └ check coherence (coherence.py) → instance overlap + Paterson
  → exhaustiveness (exhaust.py)        → on *surface* patterns, before desugar
  → desugar (desugar.py)               → Expr; match compiler (match.py)
  → kind-check (kindcheck.py)          → validate type constructor kinds
  → infer (infer.py)                   → typed Expr + per-SC constraints
  → monotone check (monotone.py)       → Datafun's monotone/discrete discipline
  → subgrammar check (subgrammar.py)   → eqtype/semilattice/fixtype rules
  → solve (constraint.py)              → resolved instances
  → elaborate (elaborate.py)           → dictionary passing
  → resolve static methods (elaborate) → πᵢ of a known dictionary → the method
  ┌ Datafun programs only ────────────────────────────────────────────────┐
  │ → generate helpers (helpers.py)    → eq/union/bottom/join/… per set type│
  │ → ϕ/δ transform (seminaive.py)     → seminaïve-optimized Expr           │
  │ → change structures (changes.py)   → dummy_X/bottom_X δ asked for       │
  │ → ⊥-propagation (bottoms.py)       → the pass the speed-up depends on   │
  │ → Datafun desugar (pipeline.py)    → EFix/EFor/ESet → helper calls      │
  └────────────────────────────────────────────────────────────────────────┘
  → lambda lift (lift.py)              → closed supercombinators
  → G-machine compile (gmachine.py)    → instructions + heap
  → reactive driver (reactive.py)      → evaluate + react [FRP programs]
  → result
```

Order is load-bearing in three places.  **Exhaustiveness before desugar**:
the match compiler writes an alternative for every constructor, so a core
`ECase` is complete by construction and there would be nothing left to
check.  **Monotone check before elaboration**: elaboration rebuilds the
lambdas to insert dictionary parameters, and the binder flavours would not
survive it.  **ϕ/δ before Datafun desugar**: ϕ/δ works on `EFix`/`EFor`
nodes, which desugaring destroys (`data.md` §0).

---

### Potential fixes, features, and upgrades

#### 1. (implemented) Constraint TVar unification — propagate substitution through constraints

**What**: When `fromInteger 5` (constraint `Num b`) flows through `f` (which
unifies its param with `b`), the constraint's TVar and the result's TVar can
diverge (different internal ids) if the substitution isn't applied to
constraints at every inference step.

**Current state**: The env-update fix in `infer_program` (applying `s` to all
env types after each SC) resolved the cross-SC propagation.  Constraints are
now applied with the final substitution, and the CLI canonicalizes TVar names.

**Current state (2)**: constraints are no longer an anonymous log —
`Predicate.site` records the `EGlobal` occurrence that emitted it (§18), so
elaboration routes each *occurrence* to its own instance.  `show 1 + show True`
in one SC now works; before, the by-name map held one entry per method and the
last constraint won.

**Remaining**: the reported *signature* of an SC can still name the wrong TVar
(`(Num b) => c` where `(Num a) => a` is meant) when a constraint's variable is
unified later in the same SC.  The predicates elaboration consumes are correct
— this is about what the CLI prints.

#### 2. (implemented) `for` and `case` in ϕ/δ — complete the seminaïve transform

**What**: The current ϕ/δ handles variables, lambdas, applications, `fix`,
box/unbox, and globals.  The `for` (set comprehension) and `case` (sum
dispatch) cases from `spec/data.md` §I.4.1–I.4.2 are simplified (pass-through
or bottom).

**Why**: `for` requires generating *two* fold loops (over δ-set and over
old∪δ-set) and joining results — a correctness-critical optimization: if the
subexpressions are not shared via `ELet`, the program silently regresses to
naïve evaluation.  `case` requires `split` expansion and `dummyA` dead-branch
codegen.

**Effort**: Medium — purely `Expr`-level code generation, no G-machine changes.

**Current state**: both are in, and so is the `dummyA` this entry asks for —
`gestate/changes.py` builds a zero change at whatever type it is needed at,
and generates a per-type `dummy_X` for the one case that cannot be folded to
a constant, a sum (`fixme.md` F3/F4).  `split` is not named: □ is erased, so
the outer `case ϕe` is the split.

#### 3. (skipped) Pattern-matching case alternatives — bare variable patterns

**What**: `case x of y -> y` (a catch-all variable pattern) is not supported.
The G-machine's `CaseJump` dispatches on tags only — it has no default/wildcard
case.  A bare `PVar` at the top level of a case alternative is currently
rejected by the desugarer.

**Fix**: Either (a) add a "default" marker to `CaseJump` that matches any tag,
or (b) desugar bare `PVar` alts by generating a match for every known
constructor (exhaustive expansion).  Option (b) is simpler and doesn't require
G-machine changes.

#### 4. (implemented) Exhaustiveness and redundancy checking for `case`

**What**: Per `spec/types.md` §4, exhaustiveness checking is a separate pass
after type checking.  Currently, an incomplete `case` silently crashes at
runtime with "CaseJump: no alt for tag N".

**Fix**: Walk each `ECase` over an ADT's constructor set; emit a warning/error
for missing constructors and unreachable branches.  This is a pure static
analysis pass — no runtime changes.

#### 5. (not yet) Float literals and fractional types

**What**: `VNum` only handles integers.  The parser produces `float` for
decimal/exponential literals (`3.14`, `1e10`), but the desugarer rejects them.

**Fix**: Add `EFloat`/`ENum(floor/float)` handling, or add a `Fractional`
typeclass analogous to `Num` with `fromRational`.  The G-machine would need a
`NFloat` node (or encoding floats as tagged integers).

#### 6. (implemented) Operator desugaring — integrate with the type system

**What**: Infix operators like `+`, `*`, `==` desugar to `EAp(EAp(EGlobal("+"),
left), right)` without typeclass constraints.  They should emit `Num`/`Eq`
constraints like `fromInteger` does.

**Fix**: Add `(+) : Num a => a -> a -> a` as a method of `Num` (and similarly
for other overloaded operators).  Desugar `x + y` to `EAp(EAp(EGlobal("+"), x),
y)` — since `+` is a class method, the existing constraint-generation
machinery handles the rest.  The G-machine needs no built-in `+` — instance
bodies provide per-type implementations.

#### 7. (implemented) Recursive type aliases — eager expansion and cycle detection

**What**: `type T = List T` was not supported.  `desugar_type` didn't handle
`VTypeAlias` at all.  Per `spec/types.md` §6, type aliases must be expanded
eagerly and self-referential aliases rejected.

**Current state**: `classify()` collects every `VTypeAlias` up front (so an
alias may be used before its declaration), resolves bodies dependency-first,
and stores them in `Program.aliases` as `AliasInfo` (params, param TVars,
alias-free body).  `desugar_type` takes the alias table and expands an alias
at each use site by substituting its parameters; the expansion is re-spanned
to the use site so type errors blame the occurrence, not the declaration.
Because alias bodies are themselves expanded while the table is built, no
alias name ever reaches the unifier or the kind checker.

Rejected at classification time: direct and transitive cycles (`type A = List
B; type B = Set A`), partially applied aliases, duplicate declarations,
duplicate parameters, and names that clash with a data type or a built-in
type.  Tests: `test/test_type_alias.py`.

#### 8. (superclasses done; multi-parameter closed — no caller) Typeclass extensions

**What**: Currently only single-parameter classes are supported.  Superclass
relationships (`class Ord a where …` implying `Eq a`) are not generated.
Multi-parameter classes (`class Collection c e where …`) are not supported.

**Fix**: Extend `ClassInfo` with `superclasses: list[Predicate]`.  During
constraint generation, emit superclass predicates automatically.  During
simplification, remove redundant predicates (e.g., `(Ord a, Eq a)` → `Ord a`
if `Ord` implies `Eq`).  For multi-parameter classes: extend the instance
matching to handle multiple type arguments.

#### 9. (implemented) Instance overlap checking and Paterson conditions

**What**: *Overlap* (two instances matching the same concrete predicate) was
not checked, and Paterson conditions (the structural recursion guard for
instance resolution) were not validated — instance contexts could not even be
written: `_parse_instance` read a bare `C t` head of atomic types only.

**Current state**: `gestate/coherence.py` runs from `classify()`, so a conflict
is reported where the offending instance is written rather than at an ambiguous
call site later (`spec/typeclasses.md` §5.3).  It checks:

- **Overlap** — two instances of one class whose heads *unify* are rejected,
  including against the built-in `Num`/`Eq`/`Ord Int` instances (the message
  marks those "(built-in)").  Contexts deliberately don't excuse an overlap:
  a context restricts when an instance applies, not which predicates it matches.
- **Paterson conditions** (§5.1), all three: a context predicate may not have
  more type constructors than the head, may not mention a type variable absent
  from the head, and may not repeat a variable more often than the head does.
- **Unknown classes**, in the instance head or in its context.

Enabling work: instance declarations now parse `(P1, P2) => C t` and `P => C t`
contexts and applied heads (`instance Show (List a)`, `instance Show [a]`);
`VInstance` carries `context`, and `InstanceInfo` carries `context`, `builtin`,
and `span`.  Instance type variables desugar to real `TVar`s shared between
head and context (they used to become `TCon("a")`).

Resolution follows §5: `solve_predicate` matches a head one-way, then solves
that instance's context recursively, with the §5.2 depth cap (200) and the
spec's error message as the backstop.  `show.py` grew `name_vars`/
`show_predicate` and precedence-aware parenthesisation so these messages read
as surface syntax (`(Show a) => Show (List a)`, not `Show (List a-2)`).

Tests: `test/test_coherence.py`.  Two adjacent bugs fixed on the way: the
formatter dropped parentheses around applied arguments (`f (g x)` reformatted
to `f g x`, changing the program), and `show_type` never parenthesised nested
applications (`Maybe List Int`).

**Remaining**: see §18 — a context-carrying instance is checked and resolved,
but cannot yet be *elaborated*.

#### 18. (implemented) Dictionary passing for instance contexts

**What**: elaboration was name-based — each instance method became one SC
(`__Show_Int_show__`) and call sites were rewritten to it per-SC.  An instance
like `(Show a) => Show (List a)` needs its element dictionary at run time, and
a monomorphic SC had nowhere to put it.

**Current state**: every instance is now a **dictionary** — a tuple of its
method closures, built by a generated SC whose parameters are the dictionaries
of its context:

```
__dict_Sum_Int__      = (__Sum_Int_total__)
__dict_Sum_List_a__ d = (__Sum_List_a_total__ d)
```

A call site becomes a projection out of a dictionary *expression*:
`total` at `Sum (List (List Int))` elaborates to
`#0 (__dict_Sum_List_a__ (__dict_Sum_List_a__ __dict_Sum_Int__))`.  One generic
instance therefore serves lists of every depth — no per-element-type copies.

Three pieces made it work:

- **Per-occurrence constraints.**  `Predicate.site` (excluded from comparison)
  records the `EGlobal` occurrence that emitted the constraint, so `total h`
  and `total t` in one body route to different dictionaries.  This also fixes
  the by-name collision described in §1.
- **Inference for instance bodies.**  `infer_instance_method` checks a body
  against the class method's type with the class parameter replaced by the
  instance head (`total : a -> Int` becomes `List a -> Int`), and returns the
  instance context under the same substitution — a body constraint and the
  context predicate that discharges it are only recognisable as the same
  constraint once both are substituted.
- **Assumptions in dictionary construction.**  Inside an instance method the
  context predicates are satisfied by the dictionary *parameters*, so
  `dict_expr` checks assumptions before instances.  That is what makes
  recursion terminate: inside `Sum (List a)`, the dictionary for `Sum (List a)`
  is `__dict_Sum_List_a__ _d0`, not an infinite regress.

Fixed on the way: `match_head` returned early when the *target* was a
metavariable, so a head variable was never bound against one — an instance
context then came back mentioning the head's own variable and matched nothing.

Bodies that inference cannot check fall back to the previous by-name routing
(a method of a context class goes to that context's dictionary), with
`Num`/`Eq`/`Ord` defaulting to `Int` the way Haskell defaults an ambiguous
`Num`, and a precise `ElaborateError` where the by-name choice would be a
guess.  Tests: `test/test_dictionaries.py`.

**Remaining**: `_method_sc_name` stringifies the head type
(`__Sum_List_a-2_total__`), which leaks an internal TVar id into the generated
name.  Constrained user SCs are §19.

#### 19. (implemented) Class contexts on user supercombinators

**What**: `f : (Show a) => a -> Int` was rejected in `desugar_type` ("Type
constraints are not supported yet"), so every constraint in a program had to
resolve to a concrete instance.  Polymorphic signatures did not work either:
`id : a -> a` desugared `a` to a type *constructor* and died in the kind
checker with "Unknown type constructor: a".

**Current state**: a signature is split into its context and its type by
`desugar_signature`.  `=>` is the lambda arrow, so `(Show a, Eq a) => a -> Int`
parses as a `VFunc` whose *parameter patterns* are the constraints — the
context is read out of those patterns, and lowercase names anywhere in the
signature become type variables shared between the context and the type (alias
names excepted).

The context is *given*: `infer_program` puts it on the SC's scheme, so the body
may assume it and every use site instantiates it as constraints to satisfy.
The pipeline drops the given-discharged predicates before instance resolution
— a constraint the SC's own context grants is discharged by a dictionary
parameter, not by an instance.  Elaboration then gives the SC one leading
parameter per constraint and passes them as assumptions, exactly as for an
instance context, and rewrites each call site to apply the dictionaries in
declared order (`Scheme.constraints` became an ordered tuple for this).

So a constrained SC can call class methods, call another constrained SC
(passing its own dictionary through), recurse, and be used at several types in
one caller.  `main` may not have a context — nothing calls it, so no caller can
supply the dictionary; that is a targeted error.  Tests:
`test/test_contexts.py`.

A signature's type variables are **rigid** in the body it declares.
`desugar_signature` marks them (`TVar.rigid`, carrying the name they were
written with), `unify` refuses to bind one — a metavariable may still be bound
*to* a skolem, which is what makes a signed body checkable — and resolution
refuses to pick an instance for one, so `f : a -> a; f x = x + 1` is a missing
`Num a` rather than a silent default to `Int`.  A use site instantiates the
scheme into fresh metavariables, so rigidity never leaves the body.  Tests:
`test/test_skolems.py`.

**Remaining**: class *method* signatures still cannot carry their own context
(`m : (Eq b) => a -> b -> Int` inside a class); that needs a dictionary
parameter per method rather than per instance.  Instance method bodies are
checked against the *instance head's* variables, which are not rigid — the
same gap one level down.

#### 10. (closed — no caller) Dynamic dispatch / existential boxes (`ShowBox`)

**What**: Per `spec/typeclasses.md` §7.3, heterogeneous collections of
dictionary-carrying values (`[ShowBox]`) are not implemented.  The syntax
`ShowBox := (Show a) => ShowBox a` would need parser and type-checker support.

**Fix**: Add `VBox`-like syntax for existential packing.  During elaboration,
generate a record type carrying the dictionary and the value.  During pattern
matching, open the existential and bring the dictionary into scope.

#### 11. (implemented) Score rendering and music semantics

**What**: `Score a` is a type constructor with no runtime constructors or
operations.  Musical operators (`||`, `++`, `|~|`, etc.) are declared with
fixities but have no type signatures or evaluation semantics.

**Fix**: Add `Score` as a built-in ADT (or opaque) with monadic bind (`>>=`).
Define the musical operators as ordinary functions in a standard library,
compiled through the existing pipeline.  Score rendering (box layout, staff
notation) is a separate host-language concern, not a compiler concern.

#### 12. (implemented) Standard library (Prelude)

**What**: There is no standard library.  Built-in types (`Int`, `Bool`,
`String`, `List`, `Set`, `Score`) and primitives (`prim_eq_int`, `prim_lt_int`,
`prim_mod_int`) are wired directly into the compiler.  A user cannot define
`map`, `filter`, `fold`, or any musical operations without reimplementing them.

**Fix**: Create a `prelude.ges` file with standard definitions.  The pipeline
can prepend it to user source before compilation.  This is the natural place
for `(+)`, `(*)`, `(==)`, `show`, `map`, `filter`, musical operators, etc.

#### 13. (implemented) Better error messages — source spans in type errors

**What**: Per `spec/types.md` §9, type errors should carry source locations
from the original expression.  Currently, `TypeError` exceptions include the
types but not the source position that caused the mismatch.

**Fix**: Thread `Span` information from the parser through `Type` metavariables
and predicates.  When `unify` fails, report the original source locations of
both types.  This is mostly plumbing — the data is available from the parser,
it just needs to be carried through inference.

#### 14. (implemented) Standalone checker — return non-zero on type error

**What**: `gestate.typecheck` currently returns 0 even when type inference
produces results with unresolved constraints or type mismatches (it raises
exceptions only on hard errors like unknown globals).  A `--check` flag should
exit with code 1 on type errors.

**Fix**: Catch `InferError`/`UnifyError`/`ConstraintError` in the CLI and
print them to stderr with source locations, then exit 1.

#### 15. (implemented) Strict integer primitives — evaluate arguments for real

**What**: `prim_add_int` and friends used to read the spine `NAp` nodes
directly (`s.stack[1]`, `s.stack[2]`) and "force" each argument with a
`_force_num` helper.  That helper could only handle an `NNum` or an
`NAp` whose head global *looked like* `fromInteger` (code starting with
`PushArg 0` and ending with `Unwind`) — a pattern that matches many
ordinary functions.  Anything else pushed the thunk, prepended an `Eval`,
and raised `_ForcePending`, which the handler caught and retried after a
single `step()` — by which time the spine it had indexed was gone.

Consequences: `inc (inc 5)` returned `6` (the outer call was silently
dropped by the `fromInteger` look-alike test), and `(5 + 1) + 1` crashed
with `IndexError`.  Recursive arithmetic (`fact`, `fib`) was unusable.

**Current state**: the six primitives are ordinary strict globals compiled
as `PushArg 1, Eval, PushArg 1, Eval, <op>, Update 2, Pop 2, Unwind`
(`_prim_binop_code`).  Arguments are reduced by the same `Eval`/`Unwind`/
dump machinery as everything else, the instruction consumes two WHNF
values from the top of the stack, and `Update 2` overwrites the redex root
so the work is shared.  `_force_num`, `_ForcePending`, and `_do_binop` are
gone.  Laziness is unaffected — an unused argument is still never forced.
Tests: `test/test_arith.py`.

#### 16. (implemented) Datafun `fix` — typing rule and `semifix` calling convention

**What**: `fix` parsed fine, but `main : Set Int; main = fix Box (x => {1})`
failed with `expected (Set Int), got (a0 -> (Set a1))`.  The `EFix` case in
`infer.py` was a stub that returned *the type of its argument* ("For now:
treat as producing the same type as its body"), so `fix` was indistinguishable
from its own function.  Two further bugs sat behind it: `ϕ(fix e) = semifix ϕe`
passes the `(ϕe, δe)` **pair** ϕ builds for a box, but `semifix_Set_Int` was
generated with arity 2 (`λf f'. …`), so the application was partial — the
G-machine reported `Unwinding global with too few args`; and `semifixL`'s
recursive call passed `f'` where the loop expects `f`.

**Current state**: the rule from `spec/data.md` §I.5 is implemented —
`e : □(L → L) ⊢ fix e : L`, with `L` unified against `Set a`, the only
semilattice the generated helpers cover.  An unboxed function now gets a
targeted error ("fix expects a boxed set function …; write `fix Box (x =>
...)`") rather than a confusing mismatch.  `semifix_Set_Int` takes the pair
and projects it (arity 1), and `semifixL` carries `f` correctly.  A `fix` runs
`semifix` wherever it is written: `main` is ϕ/δ-transformed like any other
supercombinator (`fixme.md` F9), so the naïve `fix_X` loop is now reached
only from the compiler's own `__`-named output — where a `fix` does not
compile anyway (F58).  Tests: `test/test_datafun_fix.py`,
`test/test_transform_scope.py`.

**Remaining**: see §17 — `fix`/`for` still resolve to the `Set Int` helpers
whatever the element type, and boxes have two incompatible representations.

#### 17. (not yet) Datafun monomorphization — pick helpers from the inferred type

**What**: `_desugar_datafun` rewrites `EFix`/`EFor` to `fix_Set_Int` and
`for_Set_Int` regardless of the element type ("We need the type.  For now,
use a default."), while `generate_all_helpers` emits helpers named after the
set types actually collected from signatures.  The two disagree as soon as a
program uses anything but `Set Int`: `fix Box (x => {True})` with
`main : Set Bool` fails with `unknown global 'fix_Set_Int'`.  `_collect_set_types`
only scans *signatures*, so a set type appearing solely inside a body is
missed as well.

**Fix**: carry the inferred type of each `EFix`/`EFor` node out of inference
(annotate the node, or run the Datafun desugaring over the typed tree) and use
`_type_suffix` on it to select the helper.  `_gen_eq` also needs the element
type: it compares elements with `prim_eq_int` unconditionally, so sets of
anything but `Int` are wrong even when the right helper is selected — element
comparison should dispatch through `Eq` like ordinary code.

A second, deeper mismatch: the ϕ/δ transform represents a boxed value as a
pair `(ϕe, δe)`, while the naïve path erases `Box` to the identity.  Only a
box written *syntactically at the fix site* works today; `fix f` where
`f : Box (Set Int -> Set Int)` is a variable would disagree across the two
representations.  Settling on one boxed-value representation (probably the
pair, with the naïve path packing a zero change) is a prerequisite for
`fix` over abstracted functions.

#### 20. (implemented) Rizzo's two later modalities, and `⊛`/`5`

**What**: every FRP primitive was typed `Sig`-to-`Sig` — `⃝∀` and `⃝∃` did
not exist (`fixme.md` F39).  With no modality to type them at, `⊛` and `5`
had no `Expr` node, no surface syntax and no `compileC` clause, so the
`MkDelayAp` instruction and `TAG_EXISTS5` tag were dead and `advance`'s
branch for them unreachable (F14).  Since `▷ = delay f 5 x` is the only way
to move a function across `⃝∃`, **no program could build a signal whose
value is computed from another signal**: `wait`-driven leaves were the whole
language.  `map`, `mkSig`, `sample`, `switch`, `zip`, `scan` and `filter`
were all out of reach.

**Current state**: `FaL` (⃝∀) and `ExL` (⃝∃) are distinct type constructors
and the interface is Rizzo fig. 3 (`spec/errata.md` R1, reproduced in
`spec/syntax.md`).  `⊛`, `5` and `▷` are `<*>`, `<@>` and `|>`, all
`infixl 4`, with `f |> x` sugar for `delay f <@> x`.  `<*>` compiles to
`MkDelayAp` (`delay f <*> delay x ⇝ delay (f x)` — no clock is consulted);
`<@>` compiles to `Pack(TAG_EXISTS5, 2)` and is performed by the reactive
driver when the argument's clock fires.

Keeping the modalities apart is what pays for the rest:

- `gfix x => t` binds `x : FaL A`, so a recursive occurrence can only be
  consumed through `<*>`/`<@>` — the productivity guard.  It compiles to
  `letrec x = delay v ; v = t in v`, not to a self-referential delay node,
  so `x` wraps the fixed point's *value* and advancing it unrolls the
  recursion.  The old cyclic node needed a `ticked` case for `delay` and a
  matching `gfix cycle` branch in `_update_one`, both of which made an
  empty clock behave like a universal one; both are gone (F15).
- `Maybe a` and `Sync a b` are built-in data types at reserved constructor
  tags, because `watch` and `sync` name them and the driver must recognise
  them without a constructor table.  That settles the in1/in2 question
  (`errata.md` R4) and makes `advance` on `sync` return a value user code
  can `case` on (R6/F16).
- `advance`'s re-entry into the evaluator runs on a scratch `GmState`
  sharing the heap rather than splicing frames into the live machine
  (F20), and `ticked`/`advance`/`MkDelayAp` dereference their operands
  (F21).

Three bugs fixed on the way:

- **The lifter treated `gfix`/`for`/`unbox` binders as free.**  Their
  binders went into the scope list but never into `_decl`, so the enclosing
  SC gained a spurious parameter as soon as a lifted lambda mentioned one.
- **`Lifter._decl` was a global name→Func map**, last-writer-wins, so two
  Funcs binding the same name interfered — and the ϕ/δ transform emits two
  copies of every SC body.  It is now keyed by Func.
- **`advance` registered a duplicate signal per step.**  `SigCons` puts
  every allocated `NSig` on the now heap, including the one `advance`
  returns, which is then folded into the existing cell in place; the now
  heap doubled each step.  Signals genuinely allocated by user code during
  a sweep are still kept.

The Datafun block is now gated on a program actually containing a Datafun
form, so an FRP program no longer gets a phantom `Set Int` and a
`f_phi`/`f_delta` pair per SC (F41, and the unconditional half of F7).
Inside a Datafun program the gate is per definition and per half as well:
a `_phi` where ϕ has something to rewrite, a `_delta` where something
differentiates a call (`seminaive.Plan`, F7).

Tests: `test/test_frp.py` — the typing rules, the rejections that
distinguish the modalities (including the old ill-typed `gfix self => 0 :::
delay self`), and runtime traces for a `wait`-driven signal's clock, `map`,
`watch`/`filter` and `sync`.

**Remaining**: see §21, which closes F17/F18/F19 and R5.

#### 21. (implemented) Clocks, the now/earlier frontier, Δ, and surface guarded recursion

**What**: four gaps that all come from the reactive driver being written
as an interpreter of `ticked` alone.  Fig. 10 defines `ticked` *and* `cl`,
and ties them together with an invariant; the paper's `head` rule is
stated only for the now heap; `chan_A` extends a channel context the
driver never had; and §2.4's desugaring scheme was missing, so every
combinator had to be hand-written in core form.

**Current state**:

- **`cl` and the ticked/cl invariant** (F17, `errata.md` R7).
  `reactive.cl` implements the six rules; a clock is a set of *sources*,
  `("chan", id)` and `("sig", cell)`, because the invariant quantifies
  over both.  The reading that matters is that `cl` is taken against the
  heap from *before* the step, so `reactive_step` snapshots every
  earlier-heap signal's clock before touching a cell and `_update_one`
  checks each `ticked` answer against it.  A driver that recomputed
  clocks mid-sweep — the mistake the errata says nothing could catch —
  now raises.  On by default via `GmReactive.check_clocks`.

- **The ✓ frontier** (F18, R8).  `NSig.current` marks a cell as being on
  the now heap.  `SigHead` raises on a signal the sweep has not reached,
  and `ticked`/`advance` do the same for `watch l` and `tail l`, whose
  rules are also stated against η_N.  Running one heap with in-place
  update turns the paper's stuck state into a silently stale read, so the
  mark is what keeps a scheduler-ordering bug an *error*.  `data.md` §II.5
  is right that the split is a proof device for performance and wrong
  that it can be dropped wholesale.

- **The channel context Δ** (F19, R11).  `GmState.chans` maps channel id
  to element type, exposed as `GmReactive.chans`.  Inference records the
  type on the `EChan` node (there is nowhere else to learn it — the heap
  is untyped and a channel can be minted at run time), `NewChan` extends
  Δ, and `advance`'s sub-evaluation shares the dict so a channel created
  during a sweep registers.  `react` rejects input on a channel that was
  never allocated, which is the theorem's `κ : Chan B ∈ Δ_n` premise.
  Note Δ is a runtime context: an unforced `c = chan` is not in it.

- **Surface guarded recursion** (R5).  `desugar._guard_recursion`
  implements §2.4: a definition whose recursive calls all sit under a
  `delay` becomes `gfix r => (x₁…xₙ => C[delay (r' => t[r'/f]) <*> r])`.
  The rule fires only when at least one call is guarded, which keeps
  ordinary recursion out of it; a partly guarded definition is rejected,
  since it cannot be productive.  Signal patterns come with it: `x ::: xs`
  is irrefutable, so it binds `head`/`tail` rather than dispatching, and
  `xs` is the *delayed* rest at `ExL (Sig a)`.  `mkSig`, `map`, `const`,
  `filter` and `switch` now read as the paper writes them:

  ```
  mkSig d = (x => x ::: mkSig d) |> d
  map f (x ::: xs) = f x ::: (map f |> xs)
  ```

Three pre-existing bugs fixed on the way: constructor sub-patterns were
parsed with `_parse_pat`, so `f (Just x :: xs)` silently meant `Just (x ::
xs)` (F44); `EChan` was rebuilt by the lifter, which would have discarded
the type annotation; and the formatter dropped parentheses that carry
meaning — around a trailing operand, around a left-nested `->`, and around
a cons pattern in parameter position (F46).

Tests: `test/test_frp.py` grew the `sample` trace (data dependency
without timing dependency), `switch` (dynamic dataflow, asserted through
`cl` before and after the switch), the Δ tests, the frontier tests, and
the surface-syntax forms — including a check that the desugared `map` has
the same shape as the hand-written fixed point.

**Remaining**: recursion over `μα.A` via `rec(x.s, t)` needs a `μ` type
former gestate does not have; mutual guarded recursion is outside §2.4's
scheme, so `switch`/`cont` compile as ordinary mutually recursive SCs; and
a multi-line `case` inside parentheses still does not parse (F45), which
is what forces `cont` to the top level.

#### 22. (implemented) Boxes, the □ stripping rule, and layout in brackets

**What**: four things that between them decide whether Datafun and FRP can
share a program, plus the two bugs that were hiding underneath.

- **`ϕ(unbox)` was broken** (`fixme.md` F1): the `EUnbox` branch of `phi`
  had a live wrong `return` in front of a dead correct one, so any use of
  `unbox` died in the lifter.  Since `unbox` is the *only* way to bring a
  value into a box's scope, this made `fix` usable only over a closed
  body — and `fix` over a closed body is not Datafun.

- **One box representation** (§17's second half).  Fixing F1 exposed the
  split: ϕ/δ builds a box as the pair `(ϕe, δe)` while the naive path
  erased it to the identity, so `main = f (Box 5)` handed a transformed
  `f` something it could not project.  A box is now the pair everywhere;
  code outside the transform packs a zero change, and the naive
  `fix_X` projects the base point like `semifix_X` already did.

- **The □ stripping rule** (`gestate/monotone.py`, part of F38).
  `⌈Γ⌉ ⊢ e : A ⟹ Γ ⊢ [e] : □A` — a box may not close over a monotone
  variable.  This is not decoration: `ϕ(λX. e) = λX. ϕe` gives a lambda no
  change parameters, so a box capturing a lambda-bound variable asks δ for
  a `DX` nothing bound.  `close s = fix Box (r => s)` used to crash in the
  lifter with `unbound EVar 'ds'`; it is now an error that names `s` and
  points at `unbox`.

- **Layout in brackets** (F45).  A block opened inside a bracket now ends
  at that bracket.  The tokenizer records the bracket depth each layout
  level was opened at and emits the `DEDENT` just before the closer; the
  parser steps over it when it wants the bracket.  This is what lets the
  paper's `switch` be written with `cont` as a local lambda rather than a
  top-level helper.

One more pre-existing bug, found immediately after: `Subst.compose`
produced `α ↦ α` when both substitutions unified the same pair of
variables from opposite sides, and `apply` chased it forever (F47).  The
occurs check never sees such a binding — composition creates it.

**Where this leaves the union.**  A signal *can* now carry a Datafun fixed
point: `main = close (Box {1,2}) ::: mkSig (wait c)` compiles and runs,
which answers §II.2's open question (`errata.md` R13) in the affirmative.
What does not work is feeding the query a value the signal produced —
`map (n => close (Box {n})) xs` is rejected, correctly, because `n` is
lambda-bound and therefore monotone.  That is not a bug to fix but a
missing type-system feature: gestate has `Box` as a type former but only
one arrow, so a function cannot *ask* for a discrete argument the way
Datafun's `□A → B` does.  `errata.md` R14 sets out the two ways forward
and is now the blocking item for the union.  It also records why §II.2's
"every Rizzo construct is non-monotone" cannot be adopted as written: it
rejects the paper's own `map`.

Tests: `test/test_monotone.py`, `test/test_layout.py`, `test/test_types.py`.

**Remaining** on this path, in the order they block each other: the
monotone/discrete arrows (R14), then the four type subgrammars (D1/F38)
— `{someSignal}` is still accepted, which §II.1 calls the one edit that
makes the union sound — then `fix` at a fixtype rather than at `Set a`
(F37), and per-element-type set helpers (F11, §17's first half).

#### 23. (implemented) Monotone and discrete arrows

**What**: Datafun has one arrow, and it is the *monotone* one; a function
that wants a discrete argument writes `□A → B` and its callers box.  That
works in Datafun, where every value is set-shaped, and fails in a language
that also has signals: values arriving from the FRP side are lambda-bound,
hence monotone, and a monotone variable can never be boxed.  §22 left the
union able to run a *closed* Datafun query inside a signal but not to feed
one a signal's value — `errata.md` R14.

**Current state**: two arrows.

```
A ~> B      -- monotone: the argument is a monotone variable, and the
               function must respect the ordering on A.  Datafun's A → B.
A -> B      -- discrete: the argument may be used any way at all.
               Datafun's □A → B.  The default, and what all existing
               code already means.
```

Both compile to the same thing — §I.3 notes the split is "purely a
compile-time typing discipline, invisible past ϕ/δ".  What changed:

- **Binder flavours come from the arrow.**  `check(ELambda, …)` walks the
  parameter list against the arrow spine and records which binders are
  monotone on the node; `case` binds monotone (fig. 2.3), `for` binds
  **discrete** (`Γ, x :: A_eq ⊢ f : L` — this is what lets fig. 2.2
  desugar a pattern clause to an equality test), `unbox` binds discrete.

- **`fix : □(L ~> L) -> L`.**  Monotonicity is why the least fixed point
  exists; gestate previously accepted any function at all.  `fix`'s
  argument is now *checked* rather than inferred so the lambda inside it
  meets the monotone arrow — which needed `check` to see through `Box`.

- **The stripped positions** are `[e]`, a set literal (`⌈Γ⌉ ⊢ eᵢ : A_eq`),
  and the argument of a `->` (because `□A → B`'s argument goes under a
  box).  `monotone.py` walks these; the last needs inference to record
  each application's arrow flavour, since the two arrows do not unify.

- **The discipline is silent at a discrete order.**  `x ⩽ y ⟺ x = y`
  makes every function out of a type monotone, so the flavours coincide
  there.  `types.has_nontrivial_order` decides it, and only `{A}` and
  things built from it qualify — so `Int`, `Bool`, `Sig A`, `Chan A` and
  every FRP combinator are untouched by this pass.

- **ϕ/δ: a box's free variables have a zero change.**  `ϕ[e] = [(ϕe, δe)]`
  is the only place ϕ calls δ, and that δ is consumed by `semifix`, which
  varies only its own accumulator — everything the box closes over is
  constant for the iteration.  `SeminaiveCtx` tracks □-depth and returns a
  zero change for anything bound outside the box.  Without it a discretely
  bound parameter under a `fix` asked for a `dx` that `ϕ(λX. e) = λX. ϕe`
  never bound, and the reference escaped to the lambda lifter.  That zero
  is taken at the variable's own type — inference records it on the `EVar`
  occurrence — since `f s = fix [r ⇒ s ∨ step r]` is the shape every
  Datalog query has and `s` is rarely a set of integers (`fixme.md` F3).

**Where this leaves the union.**  Both directions now work:

```
close (Box {1,2}) ::: mkSig (wait c)          -- a signal of a fixed point
map (n => close (Box {n})) xs                  -- a query fed by a signal
```

One judgement the papers do not force, recorded in R14: a type *variable*
answers "order not known" and is treated as discrete.  The strict reading
marks every `case` binder in polymorphic code monotone and rejects
ordinary programs, while a body polymorphic in `a` cannot do anything
order-sensitive with an `a` anyway.  Worth revisiting alongside the
eqtype subgrammar.

Tests: `test/test_monotone.py`.

**Remaining** on the union path: the four type subgrammars (D1/F38) —
`{someSignal}` is still accepted, and §II.1 calls that the one edit that
makes the union sound — then `fix` at a fixtype rather than at `Set a`
(F37), and per-element-type set helpers (F11).

#### 24. (implemented) The type subgrammars, and monomorphization

**What**: Datafun's four subgrammars (fig. 2.1) and the rules of fig. 2.3
that use them.  `spec/data.md` §II.1 calls not extending them with the
Rizzo formers "the one edit that makes the union sound"; until now they
existed only in prose, so `{someSignal}` compiled, `for` into `Int`
type-checked and then died in the G-machine, and `fix` accepted anything
set-shaped.

```
eqtypes         A, B ::= {A}_eq | 1 | A×B | A+B
semilattices    L, M ::= {A}_eq | 1 | L×M
finite eqtypes  A, B ::= {A}_fin | 1 | A×B | A+B
fixtypes        L, M ::= {A}_fin | 1 | L×M
```

`types.py` decides them and `subgrammar.py` enforces them at `set`, `for`
and `fix`.  A data type inherits from its fields *at the use*, so `Maybe
(Sig Int)` is not an eqtype even though `Maybe a`'s field says nothing;
a recursive one is never finite (`List Bool` has infinitely many values).
Unknowns are allowed, the same permissive over-approximation as
`has_nontrivial_order`, and for the same reason.

**The `fix` rule is the one users notice.**  `Int` is an eqtype but not a
finite one, so `{Int}` is not a fixtype: every Datafun example in the
literature is written over `{Int}` and now has to name a bounded element
type.  `errata.md` D1 asked for that restriction to be either stated or
explicitly dropped, and it is stated — because it is real.  A fixed point
closing a set under `+1` terminates at `Cyclic 4` and does not at `Int`,
and the error message says so and names the finite types gestate has.

**That forced §17.**  Once `{Int}` stops being the only fix-able type,
the helpers cannot be hardcoded to it.  `ESet`/`EFix`/`EFor` now carry
their inferred type, `_desugar_datafun` and ϕ/δ select `fix`/`for`/
`semifix`/`bottom`/`join`/`union` from it, and `semifix` is generated per
type.  Closes F8 and the dispatch half of F11; the body half is now
*reported* rather than silent — a set whose elements are not
integer-represented says the implementation cannot build it, instead of
miscomparing at run time.

Three things fixed on the way:

- **`elaborate._rewrite` was a hand-written rebuilder.**  It dropped the
  annotations inference leaves on the tree and silently skipped
  `EAppFa`/`EAppEx`, so a class method inside `<*>`/`<@>` was never
  elaborated.  It now goes through the shared `map_children`, which is
  driven by the dataclass fields and so is total by construction.
- **`generate_helpers` (F12), a stale dead copy**, deleted — it had
  already diverged, absorbing a guard meant for the live generator.
- **A `let`-bound fixed point is not generalized** when its type has a
  non-trivial order.  Datafun is a monomorphic sublanguage (`errata.md`
  D9): generalizing leaves the element type a variable and no helper to
  call, so `let s = fix … in s` used to compile to `fix_Set_a0`.

Tests: `test/test_subgrammar.py`.

#### 25. (implemented) The join operator — and the first query that runs

**What**: the subgrammars say what a semilattice *is*; nothing said how
to use one.  `spec/syntax.md` had no join at all, and ⊥ only incidentally
(the empty set literal).  Every Datalog query has the shape
`fix (r => base ∨ step r)`, so **no non-trivial fixed point was
writable** — a `fix` could only be the identity on its seed.

`\/` is fig. 2.3's `join`, `infixl 3`.  ϕ and δ both distribute over it
(§I.4's table), and `subgrammar.py` checks the operand type.  With it:

```
reach : Box (Set (Cyclic 4)) -> Set (Cyclic 4)
reach bs = unbox s = bs in fix Box (r => s \/ (for (x in r) {x + 1}))
```

closes `{1}` under `+1` and returns `{0,1,2,3}`.

Writing it immediately found three bugs, in the order they surfaced:

- **`semifix` hung** (`errata.md` D2).  The convergence test was
  `dx = ⊥`, and `δ(e ∨ f) = δe ∨ δf` is a deliberate overapproximation,
  so a delta routinely contains elements already known: `x` stops growing
  while `dx` never empties.  The test is now `dx ⊑ x` (fig. 4.2), via a
  generated `subset_L` computed as `eq (union a b) b`.  Nothing could
  have exercised this before, because nothing could produce a join.

- **Every arithmetic operation at `Cyclic n` returned `0`** (F48).  The
  synthetic `Num` instance defined only `fromInteger`, and `elaborate`
  filled a missing method's dictionary slot with `ENum(0)` on the theory
  that "a well-typed program never projects the slot".  `Unwind` on a
  number ignores the spine, so `x + y` quietly *became* the placeholder.
  The slot is now an undefined global — it fails if projected, and is
  inert otherwise.

- **`Cyclic n` did not wrap** (F49).  Only `fromInteger` reduced mod `n`.
  That is not just wrong arithmetic: the fixtype rule takes `Cyclic n`
  for a finite type, so a `Cyclic 4` holding 6 would make `fix` promise a
  termination it could not deliver.  `Bounded lo hi` has the same problem
  and is not yet fixed, so it is deliberately *not* counted as finite.

One more, found by the test that checks it: `_adt_in_grammar` treated an
unknown type constructor as a data type with no constructors and so
passed it vacuously.

Tests: `test/test_subgrammar.py`, `test/test_arith.py`,
`test/test_datafun_fix.py`.

**Remaining** on this path: `⌈Γ⌉` at `e = f` and `empty?`/`split`, which
gestate does not have (D5/D6); `fix` at a tuple of semilattices rather
than only a set (F37); element comparison dispatching through `Eq`/`Ord`
so `{Bool}` and data-typed sets can run (F11); `Bounded` normalising its
values so it can count as finite (F49); and the two remaining seminaive
items — change minimization (D4) and ⊥-propagation (D3), which is where
the asymptotic speedup actually lives.

#### 26. (implemented) The front end: patterns, scoping, tuples, strings, classes

A block of work aimed at the two things the language was furthest from —
looking like Haskell, and having a front end separate from the core.

- **A pattern-match compiler** (`gestate/match.py`), Augustsson's algorithm
  over a pattern matrix, lowering to the *existing* one-level `ECase`.
  Core did not change, so `infer`/`lift`/`gmachine` were untouched, while
  nested patterns, `[x]`/`[x, y]`, literals, tuples, wildcards and
  multi-argument equations all became writable.  It replaced
  `_desugar_pattern`, `_desugar_pattern_sc` and `_bind_params`, including
  the separate signal-cons path — FRP and ordinary patterns now share one
  route.  The parser gained Haskell's `apat`/`pat10` split.

- **Exhaustiveness** (`gestate/exhaust.py`) rewritten as Maranget's
  usefulness algorithm over *surface* patterns.  This became mandatory:
  the match compiler emits an alternative for every constructor, so the
  old core-level tag count could never fire again.  Errors carry a
  counterexample.

- **Scoping** (`gestate/prelude.py`): a user definition shadows a prelude
  name, and the prelude's binding is *renamed* rather than dropped, so
  `concat` keeps calling the prelude's `append` when the user redefines
  `append`.  Non-adjacent equations and duplicate signatures are rejected.

- **Tuple types**: `(A, B)` is an ordinary applied `TupleN` constructor, so
  unification, kinds, `show` and both Datafun subgrammars (`A×B`, `L×M`)
  needed no special case.

- **Superclasses**: `class Eq a => Ord a`, discharged by *closing* every
  context under its superclasses rather than nesting dictionaries, so the
  dictionary layout is unchanged.

- **Strings and `Show`**: `Char` is an integer-represented built-in and
  `String` is an alias for `List Char`, so the list machinery covers both.
  `Show` is a prelude class; `deriving (Show, Eq)` synthesizes instances as
  surface AST.

- **Structural `Eq`**: `Eq Bool`, `Ord Bool`, `Eq (List a)`, `Eq (Maybe a)`,
  `Eq (a, b)` and `elem` are ordinary prelude code.

Bugs found and fixed on the way, all recorded in `fixme.md`: δ of a `let`
never bound its change variable (F51); a block inside a `class`/`instance`
body or a `case` alternative ended the enclosing block (F52); nested
`case`s shared subject names (F53); ambiguity was resolved one predicate at
a time (F55); and a declared signature drifted when a use site bound its
variables, monomorphising it for the whole program (F56).

**Remaining** on this path: `showsPrec`, so nested constructor arguments
are parenthesised; `deriving Ord`; and an ambiguous constraint with no
defaultable class still commits to the first matching instance rather than
being reported.

---

#### 27. (implemented) Relations, ⊥-propagation, and change minimization

`spec/errata.md` D3 and D4 — the two passes the thesis measures as the
difference between "roughly 20%" and an asymptotic win.  Three pieces of
groundwork came first, and they turned out to matter more than the passes.

- **Element comparators** (F11).  Set operations compared elements with
  `prim_eq_int` whatever the element type, so a set of *pairs* — which is
  what a Datalog relation is — could not be built.  `eqE_X`/`ltE_X` are now
  generated structurally per element type: integer-represented types,
  `Bool`, tuples (lexicographic) and nested sets.
- **Canonical set literals.**  `{e₁, …, eₙ}` built a cons chain in source
  order, so `{(1,2), (0,1)}` was an unsorted "set" and every merge over it
  misbehaved.  A literal is now built with `union` over singletons.
- **δ's parameter order** (F2).  `f_delta` bound its base points and
  changes grouped while `δ(e f) = δe [ϕf] δf` supplies them interleaved.
  The two coincide at arity 1, which is why nothing caught it; at arity ≥ 2
  every multi-argument Datafun helper miscompiled.

With those, **the first relational query runs**:

```
closure be = unbox e = be in
    fix Box (r => e \/ (for (p in r) (for (q in e) (compose p q))))
```

`{(0,1), (1,2)}` closes to `{(0,1), (0,2), (1,2)}`, a 3-cycle closes to all
nine pairs.

Then the passes themselves: `gestate/bottoms.py` rewrites fig. 4.1 between
ϕ/δ and Datafun desugaring, and `semifixL` minimizes the next delta with a
generated `diff_L`.

**Measured** in G-machine steps: ⊥-propagation takes ~28% off `reach`
(68,983 → 49,725 at `Cyclic 16`) and ~2% off transitive closure; change
minimization *costs* 10-12% everywhere, shrinking with size (12.1% → 9.8%
from 6 to 12 nodes) without crossing over.  The thesis's crossover is at
400 nodes, which this evaluator cannot reach.  D4 is therefore implemented
to spec with its benefit **unmeasured**, not demonstrated.

---

### Architecture diagram

```
                    ┌──────────┐
                    │  source  │
                    └────┬─────┘
                         │
                    ┌────▼─────┐     ┌──────────────────────────────┐
                    │  parse   │     │  gestate/syntax/             │
                    │ syntax/  │     │  tokenize → parse → descend  │
                    └────┬─────┘     └──────────────────────────────┘
                         │ VModule
                    ┌────▼─────────┐
                    │  classify    │  declarations.py
                    │              │  ADTs, classes, instances, kinds
                    └────┬─────────┘
                         │ Program
                    ┌────▼─────────┐
                    │  desugar     │  desugar.py
                    │              │  VVal → Expr (with FRP/Datafun nodes)
                    └────┬─────────┘
                         │ Expr
                    ┌────▼─────────┐
                    │  kind-check  │  kindcheck.py
                    └────┬─────────┘
                         │
                    ┌────▼─────────┐
                    │  infer       │  infer.py  (bidirectional HM)
                    │              │  constraint generation
                    └────┬─────────┘
                         │ typed Expr + constraints
                    ┌────▼─────────┐
                    │  solve       │  constraint.py  (instance resolution)
                    └────┬─────────┘
                         │ resolved instances
                    ┌────▼─────────┐
                    │  elaborate   │  elaborate.py  (dictionary passing)
                    │              │  method calls → instance SC calls
                    └────┬─────────┘
                         │ typeclass-free Expr
              ┌──────────┴──────────┐
              │                     │
         ┌────▼─────────┐    ┌─────▼────────┐
         │ Datafun       │    │ ϕ/δ seminaïve │  seminaive.py
         │ desugar       │    │ transform     │
         └────┬─────────┘    └─────┬────────┘
              │                     │
              └──────────┬──────────┘
                         │ final Expr
                    ┌────▼─────────┐
                    │  lambda-lift │  lift.py
                    └────┬─────────┘
                         │ closed supercombinators
                    ┌────▼─────────┐
                    │  compile     │  gmachine.py  (compileC → instructions)
                    └────┬─────────┘
                         │ GmState
                    ┌────▼─────────┐     ┌──────────────────────┐
                    │  evaluate    │     │  reactive driver     │
                    │  gmachine.py │     │  reactive.py [FRP]   │
                    └────┬─────────┘     └──────────────────────┘
                         │
                         ▼
                      result
```

---

## Part II — Making it usable by a person

*Was Part II.*  The goal, in the words it was given in: **low mental strain, not forced to
learn too many things, good `.md` documentation about builtin values and
constructors and functions.**

**Read the revised mandate first** — it is near the bottom and it
supersedes the caution in the original five-phase plan.  Phase 1 is done;
Phases 2 and 3 are the live work.  "State, for picking this up cold" at the
very bottom is the place to resume from.

---

### What I found

I counted the surface a person has to hold in their head before they can
write a synth.

| library | in scope when | definitions | data types | classes/instances |
|---|---|---|---|---|
| `prelude.ges` | always | 42 | 0 | 19 |
| `signal.ges` | any reactive backend | 8 | 1 | 0 |
| `audio.ges` | `--audio` | 14 | 1 | 3 |
| `synth.ges` | `--audio` | 118 | 13 | 0 |
| `music.ges` | MIDI/score backends | 16 | 1 | 0 |
| `gui.ges` | canvas programs | 20 | 5 | 1 |
| **total** | | **218** | **21** | **23** |

Against those 218 definitions there is:

- `doc/manual.md` — 927 lines, and it is a **narrative**: ten chapters that
  teach the ideas in order.  Excellent for the first day and useless on the
  second, because you cannot look anything up in it.
- `spec/*.md` — eleven files, all of them **rationale**.  They answer "why
  is it like this", never "what is there".
- `typecheck --query NAME` — the right answer to the wrong question.  It
  requires you to already know the name.
- `typecheck --fits TYPE` — genuinely good, and undiscoverable.

**There is no reference documentation.**  The only way to find out that
`sineFrom` exists is to grep for it, or to read all 745 lines of
`synth.ges`.  That is the single largest source of strain and everything
below is downstream of it.

Four smaller findings:

1. **Which library you get depends on the backend, and nothing says so.**
   `keyHz` is in scope for a synth and not for a music program.  A reader
   has to know which of six files is loaded before they can trust anything
   they read in it.

2. **`synth.ges` mixes the vocabulary with the machinery.**  Of its 118
   definitions, roughly 25 are what a person writes (`sineAt`, `sineFrom`,
   `adsrFrom`, `keyHz`, `gain`, `lowpassAt`, `panSig`, …).  The other ~93
   are `svfSolve`, `ladderTail`, `fmPhasesWith`, `quadDotWith` — the insides
   of four filters and an FM engine.  Nothing marks the difference, so the
   file reads as 118 things to learn.

3. **The examples teach two different languages.**  `polysine.ges` writes a
   voice as composed values, in four lines.  `duet.ges`, `polysaw.ges`,
   `fmpoly.ges` and `quartet.ges` write theirs as hand-rolled state records
   with a `scan` and five destructuring helpers — seventy lines for the
   same sound.  The second way is *older*, and only `polysine.ges` says so.
   A newcomer reading in directory order learns the hard way first.

4. **`manual.md` §9 "Things that will surprise you"** is nine documented
   papercuts.  A list of surprises is a good faith effort, but every entry
   on it is strain that was written down instead of removed.

---

### The plan as first written

*Kept for the findings in it.  **Phase 1 is done**; the numbering below is
superseded by "Revised mandate" and the Phase 2/3 that follow it.*

#### Phase 1 — a generated reference  *(the one that matters)*

`doc/ref/*.md`, one page per library, listing **every** name with its
signature and its doc comment, grouped by the `# ── … ──` section headers
the prelude files already carry.

**Generated, not written.**  The compiler already has every piece: `--sigs`
prints signatures, `typecheck._doc_above` extracts the `#:` block above a
declaration, `_declared_at` finds it.  A hand-written reference for 218
names goes stale in a month; a generated one cannot, and a test that
regenerates it and diffs is four lines.

So: `python -m gestate.reference` writes `doc/ref/`, and
`test/test_reference.py` fails if the checked-in copy is behind.

Output per entry:

```
### sineFrom

    sineFrom : Sig Float -> Sig Float

A sine that follows a frequency signal.
```

This is the phase I would do first and the one I would do even if you
picked nothing else.

#### Phase 2 — mark the public surface

Split each library page into **Vocabulary** (what you write) and
**Internals** (what makes it work), so `synth.ges` reads as ~25 things
rather than 118.

The mechanism should be cheap and local.  My recommendation: **the `#:`
doc comment is the marker** — a definition with one is public, a definition
without one is internal, and the generator sorts on that.  That is already
almost true by accident in `synth.ges`, it needs no new syntax, and it puts
the decision next to the definition where it will be maintained.

The alternative is an explicit `#: @internal` tag or an export list per
file.  Both are more precise and both are a new thing to learn, which is
the thing we are trying to reduce.

#### Phase 3 — one page: what is in scope when

`doc/ref/index.md`, a single table mapping **what you are writing** to
**what you may call**:

| you are writing | command | libraries in scope |
|---|---|---|
| a synth | `audioperform`, `audioeditor`, `audiopygame` | prelude, signal, audio, synth |
| a piece for MIDI | `python -m gestate.midi` | prelude, music |
| a synth with a piece | `audioperform` | prelude, signal, audio, synth, music |
| a canvas | `gui` / the pygame editor's canvas tab | prelude, signal, gui |
| plain code | `typecheck` | prelude |

Half a page, and it removes a whole class of "why is `keyHz` not defined".

#### Phase 4 — the twenty things

`doc/cheatsheet.md`: one page, no prose, the vocabulary that covers most
programs.  A polyphonic synth needs about twelve names; a piece needs about
eight.  **Low strain is a short list, not a complete one** — the complete
one is Phase 1 and it is there when you need it.

This is the page I would print and keep next to the keyboard, and it is
where I would point someone on their second day.

#### Phase 5 — remove surprises rather than document them

Going through `manual.md` §9 honestly, they are not one kind of thing:

| surprise | what it actually is |
|---|---|
| `x.0.1` lexes wrong | a lexer fix, small |
| ambiguous numerics default to `Int` silently | a warning, small — already `fixme.md` F32 |
| `\|*` binds tighter than `++` | correct as designed; belongs on the cheatsheet, not in a surprise list |
| projection needs a known type | a real limitation; the error already says what to do |
| patterns must be irrefutable | same |
| no `if`, no `where` | a language decision, out of scope for a docs pass |
| implicits are invisible in signatures | the deliberate trade §4 explains |

So Phase 5 is **two small fixes and a re-filing**, not a campaign.  I would
not touch the language itself under a usability heading without a separate
conversation.

#### Also: the examples (Phase 2½, cheap)

`polysine.ges` and the new `pachelbel.ges` write voices as composed values.
Four older examples write them as hand-rolled state machines and predate
`sineFrom`/`adsrFrom`/`Num (Sig Float)`.  Two options:

- **Label them** — a line at the top of each old one saying it is the long
  way and pointing at the short one.  Half an hour, zero risk.
- **Rewrite them** — genuinely better, and it is four files of real synth
  code with sound to preserve.  I would want to hear each one before and
  after, which needs the live engine rather than the `-o` renderer.

I recommend labelling now and rewriting only if you want it.

---

---

### Phase 1: done, and one blocker found

**Done and tested** (126 tests in `test_reference.py` + `test_audiopygame.py`):

- **`internal` is a keyword.** Tokenizer, `VInternal` in the AST, parser,
  and `classify` ignores it. A file carrying it compiles; no program used
  the word as an identifier.
- **`python -m gestate.reference`** writes `doc/ref/` — seven pages, 2,530
  lines, generated from the `.ges` sources. `--check` fails when they are
  behind, and a test runs it.
- **`[ref]` in the editor**, top right. A mode, not a dialog: type to
  search, arrows to move, `Tab` toggles internals, `Esc` returns you to
  whatever you were doing. Search is *ranked* — exact name, prefix,
  substring, signature, prose. Internals draw in a different colour and
  there is a `[ ] show internals` switch you can click.

**But `internal` currently marks nothing, and the reason is the blocker.**

A trailing marker only works on a file organised vocabulary-first. Measured
across the libraries, the trailing run of genuinely-private names is 3, 0,
0, 4 and 3 declarations. Internals are interleaved throughout, so the
marker as specified would capture almost none of them.

The deeper cause is worse, and it is the answer to "do the internals leak
into the examples": **yes, comprehensively.** Every state machine in
`synth.ges` has a public signal-level face, and eight examples bypass the
face and drive the machinery by hand:

| machinery in `synth.ges` | the public face it has | reached into by |
|---|---|---|
| ADSR chain | `adsrFrom` | fmpoly, polysaw, quartet, sine, stereopad |
| perc chain | `percFrom` | quartet |
| raw `Phase` | `sineFrom`, `sawFrom` | blip, fm, stereo |
| SVF | `lowpassSvf`, `sweepSvf`, … | quartet, stereopad |
| ladder | `lowpassLadder` | polysaw, quartet |
| FM engine | `fmStack`, `fmBell`, … | fmpoly, quartet |
| RNG | `noiseFrom` | quartet |

`quartet.ges` alone names **25** would-be-internal functions; fmpoly 9,
polysaw 6, stereopad 6.

This is the same finding as "the examples teach two languages", arriving
from the other side. Those examples predate `sineFrom`/`adsrFrom` and reach
into the guts *because the guts were all there was*. So the ordering is
forced:

1. **Rewrite the old examples** in the composed style — they then call the
   public faces, which is what those faces are for.
2. The machinery becomes genuinely unreferenced.
3. **Then** `synth.ges` can be reorganised vocabulary-first and marked, and
   the reference's Internals section stops being empty.
4. **Then** enforcement is worth building, because there is something true
   to enforce.

Enforcement is deliberately *not* built yet, and `reference.py` says so in
its docstring rather than implying otherwise.

#### The one design question this raises

A trailing marker suits a file that has been organised for it. An
alternative that fits the files **as they are** is to let `internal` run
**until the next `# ── … ──` section header** — the libraries are already
sectioned, and it needs no reorganisation and no second keyword. Measured,
that captures 14 of `synth.ges`'s 70 internals as the file stands today,
so it is not sufficient on its own either; it becomes good only after the
same reorganisation. I mention it because it is cheaper to change now than
later.

---

### Revised mandate (supersedes the caution above)

Decided after Phase 1, and it changes the shape of the rest:

1. **Stop optimising for zero risk.** An example may change how it sounds,
   so long as the change is not noticeable. "I would want to hear each one
   before and after" was the wrong bar and it stalled the work.
2. **Enforce `internal` early, and let things break.** Tests and example
   programs may be red *in the middle* of the work. They must be green at
   the end. Breakage is how the leak gets found; deferring enforcement
   until nothing could break means never doing it.
3. **Every user-visible name gets a friendly version.** Not a sampling, not
   the obvious ones — all of them, one feature at a time, with the author
   reviewing each feature as it goes past.

The dependency chain in "Phase 1: done, and one blocker found" is still the
right *order*. What changes is that it is no longer gated on approval at
each step.

---

### Phase 2 — enforce `internal` — **done**

Done in the order the plan gave, and the fallout was smaller than the
blocker section predicted, for a reason worth writing down.

1. **`gestate/internals.py`** — the check.  Regions are the library files;
   the author's text is read after `voices` expansion and before the
   preludes go on, which is the last line at which there are still files in
   the program at all.  A violation names both sides and points at **the
   public definition that calls the private one** — `svfLow` → `lowpassSvf`,
   `adsrAt` → `adsrFrom` — read out of the library rather than declared
   anywhere, so nobody maintains a table of faces.
2. **Turned on** in `audio.assemble`, `audioscore.assemble_performance`,
   `gui._program` and `midi.perform`.  Every path that puts a prelude in
   front of an author's file now asks first.
3. **`synth.ges` reorganised vocabulary-first**, 118 definitions re-emitted
   by script so none could change on the way, with `internal` between the
   halves: **63 public, 55 internal**.

   Three things came *back* above the line while doing it, and each was a
   sign the first classification was wrong rather than a concession:

   - **`adsrAt` / `percAt`** — the envelope as a pure function of the
     instant.  `sine.ges` exists to teach that an envelope carries no
     state; marking it internal would have amputated the lesson.
     `adsrFrom` is the convenience, not the only door.
   - **`phaseNext`** — a `Phase` you can hold and read but not advance is
     half a component, and `test_synthlib.py` compares the composed voice
     against the hand-rolled one, which is the test that justifies all of
     this.
   - Marking machinery private **removed reachable behaviour**, so five
     public faces were added to put it back: `notchSvf`, `sweepLadder`,
     and the missing half of the oscillator grid — `squareAt`,
     `triangleAt`, `pulseAt`, `squareFrom`, `triangleFrom`, `pulseFrom`.
     A marker that takes a capability away is a marker in the wrong place.
4. **The examples rewritten** onto the public faces — `stereopad.ges`,
   `polysaw.ges` and all four voices of `quartet.ges`.  Each was a state
   record holding phases, a filter and a sample counter, with five or six
   functions to take it apart; each is now three or four lines of
   arithmetic.  `quartet.ges`'s kit lost its per-voice RNG for the shared
   `noiseFrom` — the four generators had the same seed and produced the
   same sequence, so it was four copies of one signal.
5. **Green**, and `doc/ref/synth.md` has an Internals section with 55
   entries in it.

`python -m gestate.internals <file>…` reports without compiling, and
`--count` gives one line per file — which is how the fallout above was
measured.  **Every example in the tree is now at zero.**

The trailing marker was enough after the reorganisation, exactly as the
plan guessed; the "until the next section header" alternative is dropped.

#### Also fixed on the way

**The test suite played audio out of the speakers**, which is how this
was noticed at all — reported from the room, mid-run.

`audiolive.play` reaches the sound card whenever it is given no `command`,
and it has **two doors**: `sounddevice` (PortAudio), tried first and
skipped only if the import fails, and otherwise `player_command()`, which
finds `pw-play`, `paplay` or `aplay`.  Nine tests in `test_audioeditor.py`
built a `Workbench` without a `command` and started it.

Fixing it took two passes, and the first one was wrong in an instructive
way: guarding `player_command` alone changed nothing, because on a machine
with `sounddevice` installed that branch is never reached.  What is there
now is `test/conftest.py`, an autouse fixture that makes **both** raise,
naming the test that did it — so the next one is a failure rather than a
noise somebody has to be in the room to hear.  `GESTATE_TEST_AUDIO=1` puts
them back.  The nine tests now take the `_pacer` the file's own helper
uses, and `audiolive.play`'s docstring says that saying nothing about a
command is a request for the sound card.

`examples/audio/pachelbel.ges` was also never added to `test_audio.py`'s
`EXAMPLES`, which had left the suite red since the last session.

---

### Phase 3 — a friendly version of every user-visible name

**The core of the usability work, and the largest piece.** For each name a
person actually writes, there should be a version that is pleasant to use
rather than merely correct: sensible argument order, a name that says what
it does, defaults where there is an obvious one, and prose that answers
"when would I reach for this".

**Method.** Go **feature by feature**, not name by name — a feature is a
section of a library (`Oscillators`, `Envelopes`, `Filters`, `Stereo`,
`FM`, `Score`, `Canvas`, the Prelude's groups). For each:

1. List its user-visible names with today's signature.
2. Propose the friendly version of each — rename, reorder, merge, add a
   default, or leave alone with a reason.
3. **Show the author the proposal for that feature and get feedback before
   moving on.** This is the one place to stop and ask; the rest of the plan
   does not need permission.
4. Apply, update callers and examples, regenerate `doc/ref/`, keep green.

Prefer adding the friendly name beside the exact one over breaking the
exact one, and mark the old one `internal` when nothing outside needs it —
which is now possible, and is what the marker is *for*.

Inventory to work through (~90 user-visible names):

| feature | file | names |
|---|---|---|
| Small arithmetic | synth | 6 |
| Oscillators (fixed + signal) | synth | 11 |
| Note timing | synth | 3 |
| Noise | synth | 4 |
| Envelopes | synth | ~5 public |
| Filters | synth | ~10 public |
| Saturation | synth | 5 |
| Stereo | synth | ~13 |
| FM | synth | ~8 public |
| Signals | signal | 9 |
| Audio | audio | 17 |
| Score | music | ~15 |
| Canvas | gui | ~15 |
| Prelude | prelude | ~33 |

---

### Phase 4 — the rest of the docs

Unchanged from the original plan, and cheap once Phases 2-3 land:
`doc/ref/index.md`'s scope table (done), the twenty-name cheatsheet, and
re-filing `manual.md` §9 — two small fixes (the `x.0.1` lexing, the silent
`Int` default) and moving the rest onto the cheatsheet.

---

### Phase 3 — the prelude pass, and what it settled

Done in one sitting with the author, and it turned into compiler work
rather than naming work.  **Two of the five were live bugs, not untidiness.**

#### The classes now in the prelude

| | was | is |
|---|---|---|
| `++` | a `List` function, **shadowed** by `music.ges` | `class Semigroup`, instances at `List` and `Score` |
| `concat`, `>>=`, `single` | three names, two files, no class | `class Monad` — `pure`, `>>=`, and `join`; `List`, `Maybe`, `Score` |
| `length`, `foldr`, `foldl`, `sum`, `product`, `null`, `all`, `any`, `elem` | `List`-only | `class Foldable` — `List`, `Maybe`; the rest derived |
| `filter` | `List`-only | `class Filterable`, separate from `Foldable` because it *rebuilds* |
| `/`, `%` | `/` at `Float` only, `%` nowhere | `class Div` at `Int` and `Float` |
| `negate`, `abs` | `negateFloat`, `absFloat` | `class Signed` — **not** `Num`, because `abs` is meaningless at `Cyclic n` |

`reverseOnto`, `showNat` and `pad3`/`showFloat` are below `prelude.ges`'s
first-ever `internal` marker.  `showItemsWith` deliberately is **not**:
it is what somebody writing `Show` for their own container reaches for.

#### The two bugs

1. **`++` was unreachable in half the language.**  `music.ges` defined its
   own, and `prelude.merge` hides the prelude's when a program redefines a
   name — so inside any program with a `score`, `[1,2] ++ [3]` failed with
   `expected 'Score', got 'List'`.  `append` still worked, which is why it
   went unnoticed.  `music.ges` had recorded the blocker — "a class would
   have left both in scope and clashing" — and it was true of adding a
   class *beside* a plain `++`, not of making the plain one the method.

2. **A blank line between two instance methods silently ended the block.**
   The second method fell out to the top level, and the report was
   `Signature variable 'm' is rigid … as 'Score'` followed by *nine*
   errors about `reverse`, `sum`, `showNat` and `showFloat` — none within
   thirty lines of the cause, the first naming a variable from a class the
   author may never have written.  Fixed in `syntax/tokenize.py`:
   `line_indent` now skips blank lines exactly as it already skipped
   comment-only ones.  (`is_blank_line` had been sitting there unused —
   somebody had started this.)

#### Compiler changes it needed

- **`prim_mod_float`** — new G-machine instruction, and `frem` plus a
  floor correction in `audiollvm.py`, because LLVM truncates and Python
  floors.  Verified oracle-against-native over 200 samples with 158
  negative dividends: **exact match**.
- **Method-level type variables.**  A class method could not carry type
  variables of its own — `class C a where m : (a -> b) -> a -> b` leaked
  `b` into globally-interned rigid variables and produced nine spurious
  errors about the prelude.  `Functor`/`Monad` are impossible without it.
  Higher-kindedness itself already worked and was never the blocker.
- **`check_kind` accepts a variable at the head of an application.**
  Every `TVar` had kind `Type`, so `join : (Monad m) => m (m a) -> m a`
  was rejected — declaring a higher-kinded class worked and the first
  ordinary function written against one did not.
- **`internals.py` reads instance bodies for faces**, so `showNat` suggests
  `show` rather than the section's nearest neighbour.

---

### Phase 3¼ — the other libraries, audited against the convention

Done after the prelude, and the audit was mostly *subtraction*.

#### `music.ges` — a third of it was the backend's

Seven names with **zero users anywhere** — not in `examples/`, not in the
Python backends: `maxInt`, `placeScaled`, `placeShrunk`, `layOnto`,
`layVoicesOnto`, `placeScaledV`, `placeShrunkV`.  All below `internal`.
`lay`, `layout` and `layVoices` stay public because the *generated* entry
point names them (`main = (bpm, layout score)`), which is the seam between
a piece and whatever plays it.

A composer's vocabulary is now 14 names: `beat ' r || ++ at |< >| |* |/
instrument percussion` plus the two entry points.

#### `signal.ges` — `addSig`/`mulSig`/`subSig` were the implementation

`audio.ges` defines `instance Num (Sig Float)` *in terms of them*, so `+`,
`-` and `*` were already their public face.  Below `internal`.
`duet.ges` was the one hand-written user and now reads
`0.8 * (0.7 * lead + bass)` — verified bit-identical against the oracle.

#### A bug the audit found in the checker itself

Marking `addSig` internal broke **every scored example**, reported at line
240 of a 100-line file.  `voices` expansion appends a generated summing
fold that uses it — the library writing, not the author.  `internals.py`
now checks **only the author's own lines**, which is what its docstring
already claimed.  Sound because expansion blanks declarations *in place*
and appends, so authored line numbers never move.

#### `gui.ges` had already invented the convention

Six exact pairs — `stillSub`/`still`, `overSub`/`over`,
`moveXYSub`/`moveXY`, `blankSub`/`blank`, `onDragSub`/`onDrag`,
`onPressSub`/`onPress`: the plain word for signals, a suffix for the
plain-value form.  Independently arrived at, which is the best evidence
the rule is the natural one here.  Open: whether `…Sub` becomes `…Of`.

#### The convention, settled — it is three-way, not two

| form | means | examples |
|---|---|---|
| plain verb | a **transformation**, at whatever type | `wrap`, `clip`, `gain`, `drive`, `unipolar` |
| **`…Of`** | *the X of* a value — a **reading** | `sinOf`, `panOf`, `phaseOf` |
| plain (signals) vs suffixed (values) | when both forms exist | `still` / `stillSub` |

This is what resolves `wrap`/`clip`, which are plain words *and* plain-value
functions: they are transformations, and a transformation keeps its verb.

#### The surface, measured — callable names, public only

| you are writing | now | before today |
|---|---|---|
| a synth | **112** | 172 |
| a piece for MIDI | **48** | 59 |
| a canvas | **54** | 61 |

`synth.ges` alone: 113 callable names → 60.

#### Still to do here

- `sampleRateF`, `maxInt`, `sinOf` — type-tagged names, the family
  `Signed` just fixed for `negateFloat`/`absFloat`.
- `mkKnob` — the only `mk` prefix in the language; `knob` is free.
- **`instrument` occupies a very common word** and collides with a
  composer's own naming.  Hit by accident while writing a throwaway test.

---

### Phase 3⅜ — constant folding, **done**

The pass the `…At`/`…From` question was blocked on.  `audioextract._fold_constants`.

**The rule**, and it is the whole of it:

> Fold into `map` and `zip` steps.  Never remove or re-kind a `scan` or a
> `source`.

Sound because `render_block` computes `map` and `zip` from `cur` alone —
neither reads `prev`, neither has an `init` — so their slot in
`State.values` is a write-only cache within the sample and `migrate` has
nothing to lose when one disappears.

**What it does.**  A `zip` with one constant operand becomes a `map` over
the other, with the constant substituted into a *new* step function (new,
not edited: a step named for a global definition is shared, and narrowing
it in place would fold this node's constant into somebody else's step).
Orphaned nodes are then dropped and renumbered.

**Measured**, on the examples that have lifted literals:

| | nodes |
|---|---|
| `quartet.ges` | 645 → 635 |
| `pachelbel.ges` | 336 → 330 |
| `duet.ges` | 121 → 119 |
| `polysaw.ges`, `stereopad.ges` | −1 each |

#### Two things it got wrong first, and how they were found

1. **The test was "is the body a `Const`"**, which folded mono and left
   stereo untouched — `constSig (Stereo x x)` has a `Con` body.  The right
   test is **"does the step mention its parameter"**: a step's only way in
   is its parameters, so a body that never names them is constant whatever
   shape it has.  Found by reviewing the Stereo interface, not by a test.

2. **`_drop_unreachable` deleted control sources.**  The rule above was
   written correctly and then broken in the implementation: a voice whose
   output happens to be constant has its payload channels folded out of
   the computation, and sweeping them away removed *the channels a host
   writes to* — `chan` names the slot a schedule and a knob address.  A
   bank went from six control sources to one.  `test_audiovoices.py`
   caught it in five places.  Every `source` and every `scan` is now a
   root, reachable or not, which costs nothing: the savings above are
   unchanged.

#### Written before the pass

- `test_audiolive.py::test_a_literal_used_as_a_signal_agrees_across_all_three_engines`
  — values through interpreter, block renderer and generated code.
- `test_audiolive.py::test_the_literal_fixture_really_contains_a_lifted_constant`
  — so the above cannot pass by testing nothing.
- `test_liveupdate.py::test_editing_a_lifted_literal_keeps_every_scan_running`
  — asserted on `scan` origins, not the value list, so it survives the node
  set changing.

Both guards were mutation-tested: rewriting the fixture with `gain` fails
the fixture guard, and moving a `scan`'s origin fails the migration guard.

**What this unblocks:** a literal used as a `Sig Float` now costs nothing,
so the objections to merging `…At` into `…From` — including `tan` per
sample — are gone.  The *namespace* objection remains and is unaffected.

---

### Phase 3½ — the oscillators, filters and stereo: **done**

The author's cut, applied.  `synth.ges` went from **113 callable names to
48**, in eight sections, with **no exceptions left to the convention**.

#### The convention, final

| form | means | examples |
|---|---|---|
| plain verb | a **transformation**, at whatever type | `wrap`, `clip`, `gain`, `drive`, `unipolar` |
| plain word | signals in, signal out | `sine`, `adsr`, `pan`, `lowpassSvf` |
| **`…Of`** | *the X of* a value — plain numbers, no signals | `sineOf`, `panOf`, `adsrOf` |

Two rules and a reading.  `…At` and `…From` are **gone** — a literal is
already a constant signal (`Floating (Sig Float)`) and the fold makes it
free, so the fixed and following forms are one function.

#### What each section became

| section | | names |
|---|---|---|
| Small arithmetic | 7 | `clampF mixF dbGain keyHz centsHz secondsSince nyquistF` |
| Oscillators | 9 | `phase sine saw square triangle pulse pulseOf unipolar bipolar` |
| Noise | 1 | `noise` |
| Envelopes | 6 | `adsrOf percOf adsr perc onset slew` |
| Filters | 8 | `lowpassOnePole highpassOnePole dcBlock lowpassSvf bandpassSvf highpassSvf notchSvf lowpassLadder` |
| Saturation | 4 | `softClip driveOf drive wrapFold` |
| Stereo | 6 | `panOf widenOf monoOf pan widen pair` |
| FM | 7 | `fmZero fmNext fmOut fmSilentWiring fmStack fmBell fmFeedback` — *superseded by Phase 5* |

#### The decisions inside it

- **`Phase` is gone.**  A phase is a `Float` in turns; the newtype bought a
  graph node per oscillator and nothing else.  `phaseOf`, `phaseNext`,
  `phaseAt`, `phaseFrom` went with it; `phase : Sig Float -> Sig Float`
  is what remains.
- **Filters are named for their circuit**, not for a convention:
  `…OnePole` (6 dB), `…Svf` (12 dB), `…Ladder` (24 dB).  `audio.ges`'s
  `lowpass` keeps the plain name — it takes a raw *coefficient*, and 21
  files spell it that way.  `sweepSvf`/`sweepLadder` are gone: the cutoff
  is a `Sig Float` and a number is one.
- **Stereo is arithmetic.**  `instance Num Stereo`, `Floating Stereo`,
  `Num (Sig Stereo)`, `Floating (Sig Stereo)` replace `stereoAdd`,
  `stereoScale`, `mixStereo`, `gainStereo`.  `quartet.ges`'s mix is now

      sound = 0.85 * (padMix + bassMix + leadMix + kitMix)

  where it was `gainStereo 0.85 (mixStereo (mixStereo …) (mixStereo …))`.
  `*` at `Stereo` is **componentwise** — right for a fader, not a
  meaningful "multiply two stereo signals", and the doc comment says so.
- **`slew`** is the stateful envelope: `slew rate target`, both signals,
  output bounded by `k` per sample so it cannot click.  `adsr`/`perc` stay
  as the cheap exact ones.  A portamento is `slew rate (!hzOf s)`.

#### Two costs of the merge that were **not** free — found by the suite

**1. A `Float` expression needs the `!` lift — and that is all.**

    lowpassSvf 800.0 0.4 s      works — a literal is already a signal
    lowpassSvf cut 0.4 s        FAILS, for `cut : Float`
    lowpassSvf (!cut) 0.4 s     works

`Floating (Sig Float)`'s `fromFloat` coerces **literals**, not `Float`-typed
expressions.  I first wrote this up as a real cost of the merge, reaching
for `constSig` — the author pointed out `!`, which is the same
one-character lift every voice already uses on its payload (`!hzOf s`), and
is the idiomatic answer.

**Measured: all three spellings give an identical graph — 7 nodes — and
identical samples.**  The constant folds out however it is written, so the
merge really is free and the earlier entry claiming otherwise was wrong.

(`constSig` also works but is generated by `audio._entry` rather than
declared in a `.ges` file, so it appears in no `doc/ref/` page.  Worth
fixing on its own account, not because anything needs it.)

**2. `Both` cannot be used at two instantiations in one graph.**  I wrote
`lowpassOnePole` and `slew` with `!Both …`, giving `Both Float Float` — and
`fmpoly.ges`'s voice has `Both Gate Key`.  A constructor's layout is chosen
by **tag**, so one tag with two shapes broke code generation:

    insertvalue operand and field disagree in type:
    'double' instead of '%Gate = type { i64, i64, i64 }'

This is the defect `quartet.ges` already records about two `Played`s, and
it is **why `SvfIn` and `LadderIn` are their own types rather than pairs**.
Both now have their own records (`OnePoleIn`, `SlewIn`), which is the
pattern the file was already following and which I did not read closely
enough before reusing `Both`.

The lesson generalises: **a polymorphic record in a library is a landmine**
for any program that instantiates it differently.  `Both` in `signal.ges`
is public and documented as the way to lift over more than two signals —
so this is reachable by an author, not only by me.

#### What the convention cost, measured

**Three collisions from four generic names taken.**  `phase` broke
`knob.ges` and `twoknobs.ges` (renamed to `turning`); `noise` broke
`quartet.ges` (renamed to `hiss`).  `audio.ges` and `synth.ges` are
prepended as *text*, so there is no shadowing — a collision is a
`Duplicate type signature` naming the author's own definition, with
nothing pointing at the library.  This is what `mkKnob` exists to dodge,
and it is the price of the plain names.

---

### Phase 3¾ — `compose` is `@`

One rename, and three things it found.

`prelude.ges`'s `compose : (b -> c) -> (a -> b) -> a -> c` is now `(@)`,
at `infixr 9` in `descend.DEFAULT_INFIX` — Haskell's precedence for
Haskell's reason.  Composition is associative, so the associativity is
unobservable in an answer and the precedence is the whole point: `f @ g`
groups before whatever is done with it.  There were **no call sites** —
not one `.ges` file in the tree used `compose` — so this is a rename and
not a deprecation, and nothing is left below `internal` to mark.

`$` has a fixity and **no definition**.  Found by writing `f @ g $ x` in
the doc comment and having it fail with `Unknown global '$'`; the example
was rewritten to one that runs.  Worth knowing before somebody documents
it a second time.

#### Two things in the tooling that `@` was the first name to reach

1. **The reference index linked every operator to the top of the page.**
   `_anchor` strips punctuation to build a GitHub slug, which leaves an
   operator with the empty string — and its docstring said an operator is
   "anchored on its *position*, which is unlovely and unique", describing
   code that was not there.  `'`, `>|`, `||`, `|<`, `|*` and `|/` all
   pointed at `#`, so they pointed at each other.  Now spelled by code
   point (`op-64` for `@`, `op-62-124` for `>|`) with a matching
   `<a id=…>` on the heading, which is stable under reordering where a
   position is not.  The same shape as `_drop_unreachable`: a docstring
   that reads as correct beside code that is not.

2. **The formatter could not write an operator declaration.**  `(@) : …`
   came back as `@ : …` and `(@) f g x = …` as `@ f g x = …`, neither of
   which is a declaration — `parse` rejects the formatter's own output
   with `expected declaration, got '@'`.  Three sites were writing a
   name where a declaration head belongs, and a fourth, `_format_class_
   member`, consulted a **hand-kept list of operator names** to decide;
   that list is gone for `_is_operator`.  The top-level infix form
   `x <+> y = …` is gone too: the parser has no infix definition form
   outside an instance, so the formatter was emitting it into the one
   place it cannot be read.

   Formatting a library still does not round-trip, and that is older and
   larger: `_format_instance_member` does not indent a `case` inside an
   instance method, so `instance Foldable List` comes back with its
   alternatives at the member's own column.  Not touched here.

---

### Phase 3⅞ — `clamp`, `mix`, `nyquist`, and the pass they needed

The author's three: **`clampF` and `mixF` should be one function at more
than one type, and `nyquistF` should just be `nyquist`.**  The rename is
four characters.  The first two were a compiler change.

#### The wall

`clamp : (Ord a) => a -> a -> a -> a` typechecks, evaluates, and **cannot
be used by a synth**:

    adsrFall: needs the dictionary `__dict_Num_Float__`, so it is
    polymorphic.  The fragment is monomorphic: a dictionary is a record
    of functions
    clamp: is polymorphic: it takes a class dictionary

`elaborate` gives a constrained SC one parameter per constraint and makes
every call site pass a dictionary; `audiograph` refuses any definition
that so much as mentions one.  So `clampF` was written at `Float` and
named for it — the `F` was not a naming habit, it was the fragment showing
through into the vocabulary.

**A class of its own does not help.**  Tried first, on the reasoning that a
method at a known type resolves statically: it does not.  `class Clamp a`
with `instance Clamp Float` produces the same dictionary-taking method
`clamp`, and the same refusal.

#### `gestate/specialise.py`

A call whose dictionary arguments are all constant dictionary *globals*
has exactly one possible callee, so it gets a copy with them substituted:

    clamp#Ord_Float#Eq_Float lo hi x = …
    cut x = clamp#Ord_Float#Eq_Float 0.0 1.0 x

`resolve_static_methods` then finishes it — the copy projects methods out
of a global dictionary rather than out of a parameter, which is the shape
it already knew — so a constrained definition compiles to the code the
hand-monomorphised one did.  Runs for every backend; the original stays
for callers that are genuinely polymorphic.

Three things it needed that were not obvious:

1. **`unify` is the wrong tool for the copy's type.**  A signature's
   variables are *rigid* and `unify` refuses to bind one — correctly: a
   body may not decide what its caller's `a` is.  Here the caller has
   already decided and the dictionary *is* that decision, so `_match`
   reads it off one-way instead.  Until this was right every copy was
   silently skipped and the pass looked like a no-op.
2. **`Num Float` is in no instance list.**  It is manufactured during
   constraint solving (`constraint._num_instance`), so
   `program.instances` does not know what `__dict_Num_Float__` stands
   for and `mix` went unspecialised while `clamp` worked.  The pass is
   given `resolved.values()` too.
3. **Not everything is a constant.**  `__dict_Eq_List__ __dict_Eq_Int__`
   is an application and a dictionary passed through from the caller's
   own context is a variable; neither has one answer, both are left
   alone, and the fragment still refuses them.  `test_specialise.py`
   pins that.

`clamp` is now used at `Int` and at `Float` **in the same synth**, which
is the thing that was impossible.  `mix` is one function over `Float`,
`Stereo` and `Sig Float` — where a varying `t` is a crossfade rather than
a constant blend, which the `Float`-only version could not express at all.

#### The doc comments that named variables the reader cannot see

Reported from the editor: `[ref]` shows a signature, not parameter names,
so `` `t = 0.0` is `a` `` is prose about three names that appear nowhere
on the page.  Twenty-odd entries across five libraries.

Rewritten so each reads standalone — most by naming the thing rather than
the variable (`` `k` near 0 `` → "a coefficient near 0"), and where the
*order* is the content, by leading with the call form:

    #: `secondsSince n from` — how long, in seconds, instant `n` is after…

which introduces the names it then uses.  The alternative — teaching the
reference to print `mix a b t` — was the author's second choice and is
still available; this way the source reads correctly too.

`gui.ges` had already been writing them the second way (`` `over a b`
draws `a` and then `b` ``), which is the third time that file turns out
to have got there first.

---

### Phase 4 — eleven names the author read off the reference

All of them from one pass over `doc/ref/`, which is the first evidence
that generating it was worth doing: every item below is something the
pages made visible.

| was | is | why |
|---|---|---|
| `append` public | below `internal` | `++` **is** its public face — `instance Semigroup (List b)` is one line and this is that line's body |
| `floor` alone | `floor` and `ceil` | `negate (floor (negate x))` exactly, so no sixth primitive to keep in agreement |
| `sampleRateF : Float` + `sampleRate : Int` | one `sampleRate : Float` | the `Int` was the renderer's and the `F` was the type in the name; the four examples that said `prim_div_int sampleRate speed` say arithmetic now |
| `instrument` | `prog` | a composer wants that word for their own four voices, and this file is prepended as *text*, so it would have collided rather than shadowed |
| `beat : Int` = 96 | `ticksPerBeat` | see below |
| `clip`, `wrap` at `Float` | `class Clip`, `class Wrap` | the settled convention says a plain verb is a transformation *at whatever type*; four instances each — `Float`, `Sig Float`, `Stereo`, `Sig Stereo` |
| `zipSig` | `class Zip`, `zip` | exactly `Functor Sig`'s arrangement, down to `__Zip_Sig_zip__` in `audiograph.FORMERS` |
| `reverse : List a -> List a` | `class Reversible` | so a score's retrograde is `reverse` and not a synonym |
| `(') : a -> [: a :]` | `(') : (Monad m) => a -> m a` | it was `pure` pinned to one instance |
| `Guard`, `Prop`, `holds` with `#` comments | `#:` prose | they were rationale, so the reference showed the names and nothing else |

#### `reverse` at a score is a **constructor**, and `||` is why

`Score` gains `Retro (Score a)`; `instance Reversible Score` is
`reverse s = Retro s`, and `layOnto` mirrors the subtree's events inside
its own duration — `a .. b` of a subtree lasting `dt` becomes
`dt - b .. dt - a`.

A structural walk would have been wrong, not merely harder.  **An overlay
is left-aligned**, so reversing `('60 ++ '62) || '67` by turning the tree
inside out leaves two voices of unequal length still *starting* together,
when what a retrograde means is that whatever ended last now begins first.
The duration is not known until the subtree is laid out, so the mirror has
to happen where the duration is.  `test_music.py` pins the overlay case
and the `reverse . reverse = id` one.

#### `beat` is the renderer's, because a tempo is a piece's

`beat : Sig Float` — what time it is in beats, at audio rate — is
generated by `audioscore.assemble_performance` beside the entry point,
where the author's `bpm` is in scope.  It is therefore in scope in a
**scored** synth and nowhere else; an unscored one that names it gets
`Unknown global 'beat'`, which is the truth rather than a gap.  Measured
against the engine: at 120 bpm and 8 kHz, sample 4000 is beat 1.0 and
sample 6000 is beat 1.5, exactly.

`doc/ref/index.md` gained a **"Names no page lists"** table for the three
of these — `sampleRate`, `constSig`, `beat` — since a generated name
appears in no `.ges` file and so on no generated page.

#### The bug `'` = `pure` uncovered, and did not cause

    melody = pure 60 ++ pure 62          -- no signature
    score  = melody >>= prog 0

compiles `melody` with `__Monad_List_pure__` and `__Semigroup_List_++__`,
and `score` with `__Monad_Score_>>=__`.  **Two instances for one value,
silently**, and then `CaseJump: no alt for tag 13` at run time.  An
unsigned SC's constraints are resolved *locally*, picking the first
matching instance, rather than being generalised into dictionary
parameters or reported as ambiguous.

It is reachable today through `pure`, is not caused by `specialise.py`
(verified with the pass disabled), and every music example carries a
signature so none of them is affected.  Written down here because the
`'` generalisation makes it easier to reach, and because "an ill-typed
program accepted, and wrong at run time" is the worst class of defect
this repository has open.

#### What the fragment now says about `elem`

`test_audiofragment.py`'s "a polymorphic helper" case changed reason and
kept its verdict: `elem` was refused for taking an `Eq Int` dictionary,
and is now refused for walking a cons list per sample.  That is
`spec/liveaudio.md`'s own prediction arriving — it said specialising and
erasing the dictionary "is a great deal more than emitting a constant
array", and half of it has now happened.

#### Collisions, running total

Plain words taken from a program's own namespace: `phase`, `noise`,
`mix`, `zip`, `clip`, `wrap`, `beat`, `prog`, `reverse`.  Two more turned
up in test fixtures this pass (`mix` in `test_audioeditor.py`, `mix` in
`test_audiospans.py`) and one in the library itself (`beat`).  The audio
preludes are prepended as **text**, so a collision is a `Duplicate type
signature` naming the author's own line with nothing pointing at the
library — which remains the price of the plain names and the thing to
watch.

---

### Phase 5 — FM, the last section without a face

Two changes, both measured before they were made.

#### `fm : Patch -> Sig Drive -> Sig Float`

The FM bank was the one component in `synth.ges` that Phase 3½ never gave
a signal-level face, so every program that used it wrote the same eight
lines.  `quartet.ges` was:

    stepLead : Fm -> Drive -> Fm
    stepLead st d = fmNext bellPatch st d

    leadVoice g s = map (bank => fmOut bellPatch bank)
                        (scan stepLead fmZero (leadDrive g s))
                  * !velOf s * 0.6

and is now

    leadVoice g s = fm bellPatch (leadDrive g s) * !velOf s * 0.6

The face works for the reason `lowpassSvf`'s captured cutoff does: the
lambda closing over the patch is written *at* the `scan`, which is what
the fragment allows and what the extractor inlines.  **Measured on
`quartet.ges`: 639 nodes → 639 nodes, bit-identical through the native
engine.**  `Fm`, `fmZero`, `fmNext` and `fmOut` are below `internal`, and
the check's suggestion — read out of the library, not from a table — is
`reach for one of these instead: fm`.

It also closes a hazard: the patch went to `fmNext` *and* to `fmOut`, so
two **different** patches in the two places typechecked and made a sound
belonging to neither.  One argument now.

#### `modulates src dst amount`, and `noWiring`

Sixteen numbers of which three are usually non-zero.  `fmpoly.ges` had to
redraw the matrix in a comment, one line per row, to say which number was
which — a data structure telling you it is wrong for *writing*.

    piano = Patch (Quad 1.0 1.0 1.0 14.0)
                  (modulates 2 1 1.1 (modulates 2 2 0.18
                      (modulates 4 3 0.55 noWiring)))
                  (Quad 0.85 0.0 0.35 0.0)

`modulates 2 2 0.18` says feedback without the reader having to know the
diagonal convention.  A patch is a constant, so `_fold_constants` folds
the whole construction away — **bit-identical against the literal**, and
`fmStack`/`fmBell`/`fmFeedback` are written this way now, so the library
demonstrates its own interface.

**They nest rather than compose.**  `modulates 2 1 1.1 @ modulates 4 3 0.5`
is rejected with *"a function has no layout in a state struct"* — the
fragment judges every reachable definition **before** constants are
folded, so patch-construction code is held to audio-rate rules even
though it runs once.  That is the fix worth making one day and it is
larger than this was.

#### `fmpoly.ges` lost its state machine, and gained nodes

Its voice was a `Tine Fm Int` record with a `stepTine`, three functions to
take the pair apart, and a `zip` of the output back against the input.  It
is now four lines.  The per-voice counter became `ticks`, which is sound
because **a voice's own per-sample counter *is* `ticks`** — measured
directly, max difference 0.0 over 3000 samples across a two-voice bank.

Honest cost: **79 nodes → 97**, about three per voice, because the counter
that used to ride in the voice's state is now a `zip` against a shared
`ticks`.  `quartet.ges` paid nothing because its lead already read `ticks`.

#### What is left in the FM interface, and why

`Quad` is one type used four ways — ratios, a matrix row, the levels, the
amounts — so swapping ratios and amps typechecks.  Four wrapper types
would restore the checking and cost the `quadDot` sharing the whole
internal section is built on; the error is also instantly audible rather
than silent.  Left alone deliberately.

---

### Phase 6 — what the library was missing, and what it cannot have yet

Four things asked for at once.  **Three needed no new machinery and are
built; one needs a new node kind and is designed rather than built.**

#### `white`, and `dust`

`noise` is **`white`** — named for its colour rather than for being noise,
now that there are five of those.  `white 1` beside `pink (white 1)` reads
as one family.

`dust` is SuperCollider's `Dust`: random impulses at an average rate, one
draw deciding both whether an impulse happens and how tall it is.  Where
white noise is a texture, this is *events* — multiply it into a percussive
envelope, or ring a resonant filter with it.

**`dust : Sig Float -> Sig Float`**, so the density is a signal and can
move: `dust (5.0 + 40.0 * unipolar (sine 0.2))` thickens and thins over
five seconds.  The generator is folded over the density signal itself,
which is the signal it has to run on.

Two costs, and both are written down where they happen:

1. **No seed.**  Two `dust 20.0` in one program are the *same* impulses,
   where `white 1` and `white 2` are independent.  It is the price of the
   one-argument shape, and the seeded form comes back on request.
2. **The generator's low bits were biased and the threshold test found
   it.**  `dust 200.0` fired 115 times in half a second where it should
   have fired 100, and every density was high by the same 15%.  An LCG's
   low bits cycle with short periods — a *spectrum* does not notice, which
   is why `white` measured flat all along, and a *threshold* very much
   does.  `rngUnit` takes bits 15 upward now: 98 of 100, 407 of 400, 752
   of 800, within the Poisson noise of the counts.

#### The four colours

`pink`, `brown`, `blue`, `violet` — **filters, not generators**, so
`pink (noise 1)` is pink noise and `brown (dust 40.0 2)` is a perfectly
good thing to want.  Measured, at three sample rates:

| | slope wanted | measured (8 k / 22 k / 44 k) |
|---|---|---|
| `noise` | 0 | −0.35 / +0.30 / −0.05 |
| `pink` | −3 | −3.61 / −2.89 / −3.13 |
| `brown` | −6 | −5.85 / −5.70 / −6.06 |
| `blue` | +3 | +1.81 / +3.11 / +2.87 |
| `violet` | +6 | +5.01 / +6.32 / +5.94 |

All five sit at rms 0.24–0.33 and peak ≤ 1.0, so swapping `noise` for a
colour is not a volume jump.

`brown` is written as **`lowpassOnePole 20.0` scaled by √rate**, not as a
hand-picked leak coefficient — a leak of `0.998` is a different time
constant at every rate, so the colour would have drifted with the
renderer.  `blue` is `violet (pink s)`: differentiating adds six decibels
an octave to pink's minus three, and that is the whole implementation.

#### `follow`, `compress`, `limit`

A peak envelope follower with asymmetric ballistics, and a hard-knee
feed-forward compressor around it.  `Comp threshold ratio attack release`
is one value for the reason `Adsr` and `Patch` are.

Measured, `Comp 0.3 4.0`: 0.1 → 0.1 and 0.3 → 0.3 untouched; 0.6 → 0.391
against an ideal of 0.375, and 0.9 → 0.466 against 0.450.

**`limit` is documented as approximate, and the number is in the prose.**
0.5 ceiling: four times over comes out at 0.541, ten times over at 0.571.
Two causes, both topology rather than tuning — a finite ratio always lets
a little through, and a peak detector's envelope sags between the peaks of
a low note.  Faster ballistics do not fix the second; measured across
three settings the overshoot did not move.  A brick wall needs
**lookahead**, which is a delay line, so the prose says so and points at
`clip`.

One shape the fragment forbade and the fix: `compEnv c s = case c of …`
is a **`case` at signal level**, which is not a signal expression.  The
settings are taken apart by ordinary scalar functions the extractor folds
away instead.

#### `spec/delaylines.md` — the design for the rest

Echo, comb, allpass, reverb, chorus, flanger, Karplus-Strong and waveguide
physical modelling all want one thing: **a delay line**, which is a fifth
node kind whose state is N values and a cursor rather than one value.

The file works through where N comes from (compile time, as `voices`
already does), what it reads (`tap`, with `delay` as its constant face),
how a *cycle* through it is admitted (the engine already computes a `scan`
from last instant's state — a line is the same thing with a longer
memory, so `_check_recursion` relaxes from *no cycles* to *every cycle
crosses a line or a scan*), and three ways to write the cycle:
`feedback n f s` — which is `scan` with a longer arm — then a `loop`
taking a signal function, and finally guarded recursion, which the
language already has in `gfix` and the audio fragment simply refuses.

**Recommendation: `feedback` first, then `loop`.  Do not design against
`gfix`.**

#### Physical modelling is not one feature

Worth stating, because it changes what to plan.  **Two of its three
families already work:**

- **modal** — bells, bars, membranes: a bank of resonant `bandpassSvf`
  excited by `dust`.  Verified rather than claimed: a four-partial
  tubular bell at 1 : 2.76 : 5.40 : 8.93 × 220 Hz extracts to 23 nodes
  and rings at **216, 608, 1188 and 1966 Hz**.
- **mass–spring** — `scan` *is* a per-sample state update.
- **waveguide** — strings, tubes, brass, flute.  Blocked, because a
  waveguide is a delay line with a filter in the loop.

So the thing to build is the delay line; physical modelling follows from
it rather than being a separate project.

#### A silent failure found on the way

`internals.libraries_in_scope` decided whether `synth.ges` was in scope by
**re-reading the file** and asking whether that text appeared in what
`audio.preludes` returned — and `preludes` answers from a constant
captured at *import*.  When the two disagree the library is judged out of
scope and **enforcement silently switches off**.

Found because a test run overlapped an edit to `synth.ges`, which is not
reachable in a batch compile — but the editor holds that module for hours,
and a library edited on disk underneath it is exactly the divergence.
`audio.library_text` is now the one reader, and `internals` uses it in
both places.

---

### Phase 6½ — `resonate`, and the ear that found it

The author listened to `bell.ges` and said it **sounded like a wooden
block**, with background noise behind it.  Both halves were right and only
one of them was a matter of taste.

#### The background noise was mine, and it is gone

`room = 0.03 * brown (white 3)` — put under the bell "because a room is
never silent", and really to show the new colours off.  Wrong in a file
whose subject is the bell.  Removed, and not repeated in `bar.ges` or
`membrane.ges`.

#### The woodblock was a defect, and it was measurable

    bandpassSvf 220 Hz at res 1.0 — the maximum the interface allows:
      peak 0.1688; last sample above −60 dB: 0.503 s
        at   0 ms  0.168788
        at  50 ms  0.086435
        at 200 ms  0.010982
        at 400 ms  0.000701

`svfK` floors its damping at 0.02 so the filter cannot oscillate on its
own, and **that floor caps the ring at half a second at 220 Hz** however
hard resonance is pushed.  Half a second is a marimba bar.  A tubular bell
is three to ten seconds.  So the filter could not make the sound the
example claimed, and Phase 6's "modal synthesis already works" was too
strong: the *topology* worked and the available filter did not.

#### `resonate hz decay s`

Two poles, no zeros, and **the decay is in seconds to −60 dB** — the unit
a struck object's ring is actually quoted in.  Every other filter here
takes a resonance in 0.0 .. 1.0, which is the right dial for something you
sweep and the wrong one for a bell: turning a 0..1 knob until it sounds
right is not a design, it is a search.

Measured, asked against got: 0.05 → 0.052, 0.20 → 0.202, 0.50 → 0.502,
3.00 → 3.002, 8.00 → 8.002.

**The normalisation was wrong first, and the second measurement caught
it.**  With the input scaled by `1 - r` the impulse peak *falls* as the
decay lengthens — 0.087 at 0.05 s down to 0.0006 at 8 s, a factor of 140 —
because the peak of `g·rⁿ·sin((n+1)w)/sin w` is `g / sin w`.  So a mode's
`level` multiplier would have meant nothing.  Scaling by `sin w` instead
makes the peak 1 whatever the decay, and `0.7 * resonate …` is a mode at
0.7.

#### Three modal examples, in physical units

`bell.ges`, `bar.ges` and `membrane.ges` are the same four lines with
different numbers, and **the numbers are the instrument**:

| | ratios | decays |
|---|---|---|
| tubular bell | 1 : 2.76 : 5.40 : 8.93 | 6.0 / 4.5 / 2.5 / 1.2 s |
| marimba bar | 1 : **4** : 9.2 | 0.60 / 0.22 / 0.09 s |
| drum head | 1 : 1.593 : 2.135 : 2.295 : 2.653 : 2.917 | 0.55 … 0.11 s |

`bar.ges` is about the **tuning**: a free bar rings at 1 : 2.756 : 5.404
and has no pitch, and a maker undercuts the underside until the first
overtone lands on 4 : 1 — two octaves, a harmonic, which the ear fuses.
Three numbers are the difference between a marimba and a glockenspiel, and
3 : 1 instead of 4 : 1 is a xylophone.

`membrane.ges` is the same lesson at a drum: the Bessel ratios have
nothing to fuse, and a timpano's kettle of air pulls the first four to
1 : 1.5 : 2 : 2.5, which is why that one can be tuned and a tom cannot.
Excited by a noise *burst* rather than an impulse, because a stick has
width.

#### One more collision

`membrane.ges` wanted to call its function `head` — which is **Rizzo's**,
the value a signal holds now.  The report was `No instance for Floating
(Sig (Sig Float -> Sig Float))`, naming neither the word nor the line.
Renamed `skin`, with the reason recorded in the file.  That is the fourth
plain word taken this session and the first one that was already the
language's rather than a library's.

---

### Phase 6¾ — a traceback where a sentence belonged

Reported from the room:

    $ python -m gestate.audiopygame a.ges
    Traceback (most recent call last):
      ...
      File "gestate/audiopygame.py", line 485, in open
        text = bench.path.read_text()
    FileNotFoundError: [Errno 2] No such file or directory: 'a.ges'

#### The editor opens a new file, and writes nothing until `Ctrl-S`

Naming a file that does not exist is how every editor is asked to start a
new one.  `Workbench.pending` holds a starter synth and **`Workbench.
source()` is the one reader everything goes through** — compiling,
placing knobs, finding banks, sizing the prelude — which is what lets the
engine play a program that has never been written.

The first save creates the file *and its parent*, so `audiopygame
sketches/a.ges` works before `sketches` does.  Held in memory rather than
written on open because that is what every other editor does: **a name
typed by mistake leaves nothing behind.**  (Written on open first; the
author said so, and they were right.)

The starter is not an empty file.  An empty one has no `sound`, so the
editor would open on a compile error — a poor first second in a tool whose
whole point is that the program is running while you type.  It is the
smallest program that plays, and it renders at peak 0.200.

#### The traceback was not alone

All nine entry points were tried with a name that is not there:

| | was | is |
|---|---|---|
| `audiopygame` | traceback | opens a new file |
| `audioeditor` | `no window to open (…)` — blamed the window | opens a new file |
| `gui` | traceback | a sentence |
| `typecheck` | traceback | a sentence |
| `internals` | traceback, **and it ended the whole run** | reports and continues |
| `audioperform` | traceback | a sentence |
| `audio`, `midi`, `fmt` | already a sentence | unchanged |

Two are worth keeping:

1. **`audioperform`'s error path had never once run.**  Three handlers
   said `cli_error(exc, args.file)` and its argument is `args.synth`, so
   every `FileNotFoundError`, `ExtractError`, `LLVMError`, `LiveError` and
   `PerformError` it caught came out as `AttributeError: 'Namespace'
   object has no attribute 'file'`.  The message it built was never
   printed, under any circumstance.
2. **`gui` and `internals` read the file *outside* the `try` meant to
   catch it.**  In `gui` that made a missing file the one error its
   boundary could not report.  In `internals`, which takes a *list*, one
   missing name ended the run and took the report on every later file with
   it.

---

### Phase 7 — the unsigned-definition bug, and `feedback`

#### The bug was one line, and inference was already right

`infer._infer_program` ended with

    givens = [[apply_to_pred(g) for g in sc_constraints.get(name, ())] …]

— **only declared contexts became dictionary parameters.**  Inference had
been doing the right thing all along: `_attach_sc_constraints` generalises
an unsigned SC over its residual constraints and every use site duly emits
them.  What was missing is that `elaborate` gave it no parameters to
receive them in, so `solve_constraints` discharged them *where the
definition sat*, by picking the first instance that matched an unsolved
variable.

Now an unsigned SC takes a dictionary per constraint still standing on a
type variable, and one unsigned definition serves two instantiations:

    phrase = pure 60 ++ pure 62      -- no signature

    asNotes : [: Int :]              -- used at Score…
    asKeys  : List Int               -- …and at List, in one program

Both correct.  Before, `melody >>= prog 0` was `CaseJump: no alt for tag
13` — an ill-typed program accepted and wrong at run time.

**`test_skolems.py` caught the first attempt over-reaching.**  It also
inferred givens for an SC that *has* a signature declaring no context,
which silently granted `f : a -> String ; f x = show x` the `Show a` the
author must be told to write — turning three deliberate errors into
accepted programs.  A written signature is taken at its word; inference
fills in only where the author wrote nothing at all.

#### `feedback` — the fifth node kind

    scan       f z s :  out[t] = f (out[t-1], s[t])
    feedback n f   s :  out[t] = f (out[t-n], s[t])

**The loop is inside the node**, so the graph stays acyclic and
`_check_recursion` needed no relaxation at all.  That is a sharper reason
for doing this first than `spec/delaylines.md` had: the hard half of the
design is untouched and echo, comb, allpass and reverb fall out of the
easy half.

`Node.kind == "line"`, `Node.length`, and a ring whose **cursor is the
instant number** — `out[t-n]` lives exactly where `out[t]` is about to go,
since `(t-n) mod n` is `t mod n`, so one index serves the read and the
write and nothing stores a cursor.

**Three engines, bit-identical**: the oracle (`signal.ges`'s definition,
carrying the line as an ordinary *list* — a thing the interpreter can do
and the engine cannot, which is the whole reason the engine has a node
kind instead), the Python block engine, and the generated LLVM.

Three things it turned up:

1. **The first instant is silent, and that is `scan`'s own shape.**  `scan`
   reads its input from inside a `delay`, so `s[0]` never reaches a fold —
   `scan f z s` never uses `s[0]` either.  A `feedback` that fired at
   `t = 0` would be a second convention in one file; the oracle settled it,
   because a definition that cannot be written is not a specification.
2. **A segfault.**  `_slots` returned a node's *value* size, and a line's
   value is one sample where its state is `length` of them — so the host
   allocated a buffer shorter than the struct the generated code writes
   through.  The ring read uninitialised memory (`3.98e-310`) until the
   overflow took the process down.  `test_delayline.py` asserts the state
   size now.
3. **A line's length is part of its identity for migration.**  A ring's
   meaning is positional, so editing `feedback 4410` to `4400` while a
   sound plays restarts that line and nothing else — the same rule
   `migrate` already applies when a `scan`'s type changes.

Also: `Engine.snapshot` returns `(values, t, lines)` now, and both callers
carry the rings — the live update *and* the transport's seek, because a
delay line's buffer is as much the instrument's shape as an oscillator's
phase is.

#### Built on it

`echo time feedback` and `comb hz feedback`.  Measured: `echo 0.01 0.5` at
8 kHz repeats at exactly 80 samples, halving each time; `comb 250.0`
resonates on the harmonics of 250 Hz against the frequencies between them.

#### What `spec/delaylines.md` still wants

`tap`, read at a **moving** position — chorus, flanger, vibrato — and
`loop`, with a *filter* inside the line, which is what Karplus-Strong and
every waveguide need and what would make `comb` a string.

---

### Phase 7¼ — `Drive` was the odd one out

Noticed by the author: **`Sig Drive` is produced by nothing.**  It was
true, and the reason it was true is the interesting part.

`fm` took a `Sig Drive`, and a `Drive` is a note's frequency paired with
four operator levels.  Nothing in the library made one, so both examples
that used FM built theirs by hand — `zip Drive (!hzOf s) (leadLevels g)`
in `quartet.ges`, and the same pairing folded into a step in `fmpoly.ges`.

**It exists because a `scan` takes one signal**, which is the same reason
`SvfIn` exists — and `SvfIn` is *internal*, with a doc comment that says
so, while `lowpassSvf hz res s` takes its arguments apart and pairs them
itself.  `OnePoleIn`, `SlewIn` and `LadderIn` are the same.  `Drive` was
the one step-record on the public side of the line, so `fm` was the one
component that made its caller assemble the step's argument.

    fm : Patch -> Sig Float -> Sig Quad -> Sig Float

`Drive` is below `internal` now.  `quartet.ges` loses `leadDrive`
entirely; `fmpoly.ges`'s `tineDrive` splits into the pitch and the four
envelopes, which is what it already was with a constructor in the middle.

Two measurements worth keeping:

- **`quartet.ges` is unchanged at 639 nodes.**  The `zip` moved from the
  author's file into the library and is the same node.
- **`fmpoly.ges` went 97 → 109**, twelve nodes across a six-voice bank,
  because the pitch and the levels are two signals where they were one.
  Written first with `tineHz : Both Gate Key -> Float`, which cost
  *eighteen* — the payload pair had to be built a second time — and was
  six extra nodes spent saying something untrue: a note's pitch does not
  depend on when it started.  `tineHz : Key -> Float` reads the payload
  alone.

#### And a cost I inflicted on the suite

The three modal goldens were made at **two seconds, 12,000 samples** —
against the 600 to 1,200 every other golden holds — and each is
re-rendered *twice* by the tests, through the interpreter.  One process at
99% CPU for twenty minutes and the run was six percent done: fourteen
minutes became over an hour.

Half a second now.  **A golden is an oracle, not a recording**: long
enough to contain the sound and no longer.

---

### Phase 7½ — FM was already compositional, and one decision is why

The author asked whether the FM design would change for "a more modern
kit", then sharpened it: **an FM module that composes into anything, not a
DX7 operator bank.**

The answer turned out to be that it already does, and the enabling
decision was made in Phase 3½ when the `Phase` newtype was deleted —
*"a phase is a `Float` in turns, not a type of its own."*  That is what
makes this legal with nothing added:

    map sineOf (phase 440.0 + 2.0 * sine 880.0)
    map sineOf (phase 440.0 + 1.2 * saw 110.0)
    map sineOf (phase 440.0 + 0.4 * pink (white 1))
    feedback 1 (y x => sineOf (x + 0.5 * y)) (phase 220.0)

All four extract.  Phase modulation is a sine read at a phase you did
arithmetic on, `+` already works on `Sig Float`, and the modulator can be
anything the library produces.  Self-feedback — the one part that needs a
*cycle* — is `feedback 1`, which landed the same day.

Measured brightness at 250 Hz: a plain sine 0.1249, self-fed at 0.0
**bit-identical** to it, self-fed at 0.5 → 0.6248, two-operator at a depth
of 1.0 turn → 0.4698.

#### So the bank is not the interface

    pm     : Sig Float -> Sig Float -> Sig Float
    pmSelf : Sig Float -> Float -> Sig Float

Two functions, one `map` and one `feedback` between them, added for the
*name* rather than for the work.  The operator bank stays and is now
described as what it is: **an optimisation** — four operators in one node
with one state record, and a `Patch` you can store and pass around.  Reach
for the bank when you want a bank; reach for `pm` when you want FM woven
into something else.

**The depth is in turns and every FM tutorial quotes radians**, so the doc
carries the bridge: an index of 2π ≈ 6.3 is a depth of 1.0, and the useful
indices 1 to 8 are depths of about 0.15 to 1.3.  The turns convention is
`audio.ges`'s "one place for 2π" and is not worth breaking for this.

#### What it does to the "modern FM" feature list

Most of it stops being a feature: a per-operator waveform is *any signal*,
a fixed-frequency operator is a literal, detune is `centsHz`, a
per-operator envelope is a multiplication, more operators is more terms,
and a filter inside the algorithm is a filter you put there.  What does
**not** fall out is key scaling and velocity-to-index, which are per-patch
policies rather than structure.

#### The `Sig Quad` gap, found by reading the signature

Changing `fm` to take `Sig Float -> Sig Quad` removed `Drive`, and with it
the one place that said what those four floats *were*.  `Quad`'s own doc
listed its four uses and said nothing about what a number means in any of
them.  It now carries a table — ratios, a matrix row, levels, amps, with
ranges — and states the thing none of it said:

> **A level does two jobs.**  It multiplies an operator's sine *before*
> anything reads it, and both the wiring and the output mix read the
> result — so on a modulator the level is brightness and on a carrier the
> same number is loudness.

Kept rather than removed, at the author's call: *"I feel like Quad/fm
won't be needed, but let's keep it in there and let time decide."*

#### The failure the run found, and it was in the test

Three `F`s, and I had guessed the sample comparison and guessed wrong: it
was `test_the_golden_window_is_not_just_silence`, whose branch chain ends

    elif name == "stereo.ges":  …
    else:
        # Five sixteenths at 96bpm: kick, silence, hat, silence, snare.

**The `else` was `drums.ges`.**  Adding three examples to `GOLDEN` asked
each of them to contain a kick, a hat and a snare at sixteenths of 96 bpm,
and a bell does not.

The modal three have their own branch now — *struck, and then ringing*:
silence before the first sound, the peak not at the very end, and
something still sounding a twentieth of a second after it.  That is what
modal synthesis *is*, and what `resonate` gives that `bandpassSvf` could
not.

And the `else` is gone.  `drums.ges` is named, and anything else in
`GOLDEN` with no branch now fails saying so:

    bell.ges is in GOLDEN with nothing said about what its window is
    supposed to contain — add a branch above

A golden with no claim about what its window holds pins only its own
length.  The old shape did not fail loudly when a case was missing; it
applied someone else's.

#### Two examples fixed on the way

`bell.ges`'s golden was **3000 samples of silence** — at about two strikes
a second, none landed in the half-second window.  Seed 23 does.

`bar.ges` peaked at **1.2146**, over full scale and a click in the file.
It now takes the `clip` that `limit`'s own prose recommends for a hard
bound, and peaks at exactly 1.0.

---

### Phase 8 — `tap`, and making the suite portable

#### `tap` — the node that can break a cycle

    tap : Int -> Sig Float -> Sig Float -> Sig Float

`s` in, `pos` samples back, `n` the furthest it reaches.  The position is a
**signal** and may be fractional; the read is interpolated.  Measured: an
impulse at 20.0 comes out 20 samples later, at **20.5** it splits 0.5/0.5
across two, and a moving position bends the pitch.  All three engines
bit-identical, as `feedback` is.

Two node kinds rather than one, and the difference is the point:

| | reads | writes | breaks a cycle? |
|---|---|---|---|
| `feedback n f s` | the slot it is about to overwrite | the step's result | **no** — its value depends on `s[t]` |
| `tap n pos s` | wherever `pos` points | its input, **after** the pass | **yes** |

The position is clamped to ≥ 1 sample.  Not fussiness: a tap that could
hand back the sample it was given this instant would let a cycle close
with nothing in it, and reading at least one back is exactly what makes
this node's value a function of its *state*.

Two bugs, both mine.  The length was computed and dropped — `length if
kind == "line" else 0` — so every tap silently got a one-slot ring and a
one-sample delay.  And a tap's read and write are **different slots**
where `feedback`'s are the same, so the native emitter needed its write
moved out of the pass entirely.

#### `loop` — and a design that had to change first

`loop` was specified as taking a **signal function**, and the first attempt
to build it stalled on FRP plumbing: a recursive signal definition does not
run (`y = scan f 0.0 y` exceeds the step limit, because guardedness here is
carried by `gfix`, which puts the recursive occurrence under a `delay` node
evaluation never enters), and the `gfix` rewrite does not typecheck either —
`gfix`'s binder is ⃝∀ and `:::` consumes ⃝∃.

**The plumbing was not the real obstacle.**  Applying `f` to a signal
yields a whole signal, and there is no way to advance `f` by one instant:
`f (tail x)` is not `tail (f x)` unless `f` is causal, and nothing in the
type says so.  A former whose oracle needs that fact is the wrong
primitive, not a hard one.

What a loop needs is a delay line **and a per-sample accumulator**, and
those collapse: let the ring hold whole *states* instead of samples, and
the accumulator is the slot written last instant.

    loop : Int -> (b -> b -> Float -> b) -> b -> Sig Float -> Sig b

    scan       f z s :  st[t] = f          st[t-1]  s[t]
    feedback n f   s :  st[t] = f  st[t-n]          s[t]
    loop     n f z s :  st[t] = f  st[t-n] st[t-1]  s[t]

One ring, two arms, **no cycle** — `_check_recursion` is untouched and the
knot-tying extractor work was never needed.  At `n = 1` both arms land on
the same slot and it degenerates to `feedback`, which is a test.  All three
engines bit-identical, as `feedback` and `tap` are.

`Ks` is three words, so a 32-sample string is 96 where a `feedback` of the
same length is 32 — `_slots` had to count `width × length`, which is the
segfault `tap` already taught once.

#### The library got `string`, and measuring it moved the interface

`string hz decay s` is Karplus-Strong: `comb` with an averaging filter in
the loop.  It was written **without** a decay parameter, on the argument
that the length and the filter already decide how long it rings.  That was
wrong, and the measurement is worth keeping:

* The averaging filter has gain **1 at zero frequency**.  Whatever DC the
  excitation carried circulates undamped — at 880 Hz the audible part was
  gone within a third of a second and a **−0.137 offset stayed put**.
  Inaudible alone; it stacks across voices and eats headroom until it
  clips.  A loop gain below 1 damps it with everything else, and the rest
  of the library already takes that parameter (`resonate hz decay`,
  `echo`/`comb`'s clamped feedback).
* The gain is applied once per **round trip**, of which there are `hz` a
  second — so the exponent divides by the length again.  Without that, one
  number would mean eight different decays across three octaves.
* The pitch is quantised to whole samples: 220 Hz at 8 kHz asks for 36.4,
  gets 36, plays 222.2.  At 44100 the same note is four cents sharp.  The
  cure is a fractional delay, which is `tap`, not `loop`.

So all three families of physical modelling now work — resonator
(`resonate`), mass–spring (`scan`), and waveguide (`loop`).  The claim in
`synth.ges` that a delay line and Karplus-Strong were out of the fragment
is deleted rather than amended.

#### Moving the suite to a second machine found three things

Worth recording as a group, because all three were **claims made from
reading that measuring overturned**.

1. **The goldens are not portable.**  `pluck.ges`, the only one built on
   `exp`, differed in **3 samples of 1200 by 2.22e-16** — one place in the
   last.  Both machines report **glibc 2.39**: same version, different
   dispatch.  So `audio.libm_fingerprint` hashes what `sin`/`cos`/`exp`/
   `log`/`sqrt` actually return, every `.samples` header carries it, and a
   golden that differs **and** was made under a different fingerprint
   **and** differs by ≤ 4 ulps is *skipped* rather than failed.  All three
   conditions are needed — drop any one and either a real regression is
   excused or every golden stops being compared.

2. **`clang` was not optional.**  Hiding it from `PATH`: **32 failures**,
   all in `test_audioeditor.py`, which builds a `Workbench` and `start`s
   it — that compiles, and none of them carried the guard.  The claim had
   been made by reading the files that *did*.  Now 0 failures without
   clang and **0 skips with it**, which is the second half worth checking:
   a blanket guard would have quietly stopped running them everywhere.

3. **The slow half is now separable.**  `pytest -m "not golden"` leaves out
   the 22 buffer tests — the only part of the suite that is a claim about
   one machine, and the part that renders through the interpreter.

`requirements.txt` and `pytest.ini` are new.  Four third-party imports in
the whole repository — `pytest`, `mido`, `pygame`, `sounddevice` — and the
compiler itself needs none of them.  numpy is **not** a dependency and
should not be carried across; the tests that assert a filter's slope write
their own DFT.

**Full suite: 1618 passed, 0 failed, 0 skipped, 20:50.**

---

### Phase 9 — `loop`, a library on top of it, and four things measurement overturned

`tap` and `loop` were asked for together; Phase 8 built the first.  `loop`
took a design change before it could be built at all, and the library that
went on top of it found more bugs than the node did.

#### `loop` was specified with the wrong signature

The spec asked for `loop : Int -> (Sig Float -> Sig Float) -> Sig Float ->
Sig Float` — a signal function around a delay line.  The first attempt
stalled on FRP plumbing (a recursive signal definition does not run; the
`gfix` rewrite does not typecheck, ⃝∀ against ⃝∃), and that looked like the
obstacle.  **It was not.**  Applying `f` to a signal yields a whole signal,
and there is no way to advance `f` by one instant: `f (tail x)` is not
`tail (f x)` unless `f` is causal, and nothing in the type says so.  A
former whose oracle needs that fact is the wrong primitive, not a hard one.

What a loop needs is a delay line **and a per-sample accumulator**, and
those collapse: let the ring hold whole *states* rather than samples, and
the accumulator is the slot written last instant.

    scan       f z s :  st[t] = f          st[t-1]  s[t]
    feedback n f   s :  st[t] = f  st[t-n]          s[t]
    loop     n f z s :  st[t] = f  st[t-n] st[t-1]  s[t]

One ring, two arms, no cycle — `_check_recursion` untouched, and the
knot-tying extractor work was never needed.  At `n` of 1 both arms land on
the same slot and it degenerates to `feedback`, which is a test.

#### Four measurements that contradicted a plausible setting

Each of these was written to look right and was wrong:

* **`brickwall` did not hold its ceiling.**  Tested against a 220 Hz sine —
  slow — it looked perfect; the first real music through it went **2.71 in,
  1.93 out**.  A peak follower reaches 63% of a step in one time constant,
  so an attack as long as the lookahead has not arrived when the delayed
  peak does; and a *finite* ratio divides the excess rather than removing
  it.  It ends in `clip` now: the limiter's job is to make the clip rare,
  the clip's job is to make the ceiling true.
* **`dust` was broken at every real sample rate.**  `p = density /
  sampleRate` at 44100 is smaller than a 16-bit draw's smallest nonzero
  value, so only the draw *zero* cleared the threshold — and its height is
  `0 / p`, which is zero.  Measured: silent below 0.673 events a second,
  and 0.673, 0.7 and 1.0 all firing 0.67.  **The tests missed it because
  they run at 6–8 kHz**, where `p` is five to seven times larger.  A
  parameter that works at test rates and not at the rate anybody listens at
  is the worst kind.  `rngUnit` takes 24 bits now; three goldens were
  re-baselined for it.
* **`resonate` on a burst is not `resonate` on an impulse.**  It is
  normalised so an impulse returns about 1; a snare handed it thirty
  milliseconds of noise and the line peaked at **10.2**.
* **A kick is inaudible on a laptop.**  97.5% of its energy sits below 200
  Hz and there is none above 500.  A four-millisecond broadband click — the
  beater, which a real drum has — doubled the kit through a modelled laptop
  speaker for 9% more full-band level.

#### The output stage had a real safety defect

IEEE `minNum`/`maxNum` return the operand that is *not* NaN, so the obvious
clamp does not reject a NaN — it passes it through as its own bound.
Measured, `max(-1.0, min(1.0, nan))` is **1.0**: one divide by zero
anywhere in a synth left as sustained full-scale DC, which is maximum power
into a voice coil that is not moving and so is not being cooled by moving.
And the language's own protection did not reach it — the *interpreter*
refuses to divide by zero, while the generated code has no such scruple, so
the compiled engine is exactly the one that can produce a NaN and exactly
the one that drives the sound card.  `fcmp ord` before the clamp, two
instructions and no branch.

#### The libraries had no shadowing, and a composition found it

`prelude.ges` is merged as a *module*, so a user definition of a prelude
name has always been renamed out of the way.  The audio libraries are
concatenated as **text** by `audio.assemble`, so they had none — and
`synth.ges` gaining a `chorus` effect collided with `quartet.ges`'s chorus
*section* and stopped it compiling.  `shadow_libraries` renames rather than
drops, because dropping would repoint every library call at the program's
definition: `synth.ges` calls `clamp` in eight places, so a program with
its own `clamp` would rewire every filter cutoff with no error and no
warning.  Driven by the tokenizer, so a name in a comment or a string
literal is left alone.

Two test gaps behind it: `examples/audio/*.ges` was checked for *listing*
but never *compiled*, and `quartet.ges` has no golden.  Both closed.

#### The editor

* **Search** — `/`, `n`, `N`, vim's keys, because `hjkl` beside the arrows
  already promised them.  Incremental, smart case, plain text rather than a
  regular expression (`spec/` is full of `[:` and `⃝`).  A prompt and not a
  mode: it needed no view changes, because every `Pane` method already
  returns the status string.
* **Errors between the lines.**  A compiler error is a paragraph and a
  status bar is a line; it was being handed the paragraph, and `_first_line`
  threw the rest away permanently.  Diagnostics are interleaved under the
  line they name, wrapped to the width; an error in a library becomes a
  banner at the top with its location kept.  The interleave moves every
  line below it, so `laid_out` is the *one* place it is decided and the
  click reads back what the draw recorded — two answers to "how many rows
  did the diagnostics take" would put the cursor a line above the pointer.

#### This file

`implementation_order.md`, `plan.md` and the completed two thirds of
`roadmap.md` were merged here.  `fixme.md` and `spec/errata.md` were left
alone: their numbers are addresses that `gestate/*.py` cites in fifty-six
places, which is what distinguishes a register from a plan.

### Phase 10 — the editor's three complaints, and a measurement each

Three things reported from actually using it, and none of them was what it
looked like from the description.

#### "The errors do not disappear when the program starts running"

`trouble` was cleared in exactly one place — `_progress`, which the driver
calls *between blocks*.  So it only cleared while something was **playing**,
and only once the generation advanced: a build that succeeded while stopped
never cleared it, and a program that started clean still showed the error
that had stopped it starting last time.  Cleared where the good news is
*known* now, rather than where it is next heard.

#### "Popping and clicks when changing the program"

There was **no crossfade at all** — the swap was instantaneous, which is
why it also read as "the crossfade is too fast".

That was not an oversight.  `spec/liveaudio.md` weighed *Crossfade* against
*Migrate* and chose Migrate, and `audioengine.migrate` says so: "Not a
crossfade.  A crossfade is always safe and restarts every envelope, which
is the difference between editing an instrument and replacing it."  The
reasoning is right and is kept.

But migration smooths the **state**, not the **output**.  A changed
coefficient, or a node that is new and starts at its `init`, leaves the two
engines disagreeing at the seam; the waveform steps, and a step is a click.
So the state migrates *and* the old engine is kept running underneath while
its output fades out from under the new one — which is **not** the option
the spec rejected, because that one instantiates the new graph fresh.

Built in Python first, with an apology in the comment about per-sample work
in the audio callback.  That was the wrong trade to accept, and the author
said so.  `audiollvm` emits a third entry point, `render_block_mix_f32` —
the same body, two extra arguments, and a different last instruction:
multiply by a gain ramping `g0`→`g1` and **add** into the buffer rather than
store.  Two calls mix two programs sample for sample in C.  Measured,
complementary ramps over a constant come back flat: unity gain, no dip.

Linear rather than equal-power, because the two are one program and an edit
of it — for correlated sources an equal-power law adds 3 dB in the middle,
a bump where the point was for nothing to happen.  One gain per *frame*, so
a stereo pair cannot drift apart during the fade.

#### "It pops and crackles *while compiling*"

A different bug, and the interesting one.

The GIL half was **already fixed** — `PLAYING_SWITCH_INTERVAL`, with its own
measurements — and nearly got fixed twice.  Shortening the slice cures
*contention* and leaves *pauses*: a collection is not preemptible, so it
stops the thread that has 5.3 ms to fill a buffer.  A rebuild is where the
garbage comes from; refcounting frees the acyclic majority at once and the
cycles pile up for the collector to find later, at a moment nobody chose.

On two cores, a different edit each rebuild, 750 blocks of 5.33 ms:

| | worst | p99 | late |
|---|---|---|---|
| as it was | 105 ms | 79.6 ms | 51 |
| `freeze()` alone | 54.5 ms | 17.5 ms | 15 |
| **frozen + raised** | **13.3 ms** | **0.00 ms** | **7** |
| collector off | 0.0 ms | 0.0 ms | 0 |

Off is perfect and not an option — twelve edits leaked 44 MB and left
368,245 cyclic objects.  `deadline_scheduling` freezes the heap and raises
the thresholds, and puts both back on the way out.  `freeze` first, because
what is alive when playback starts is the part that never dies (the
preludes' syntax trees, the analysis cache), and every full collection was
walking all of it to prove none of it was garbage.

**Two measurements that stopped a plausible answer being shipped.**  `nice`
on the compile looked obviously right and moved the worst gap 65.9 → 53.5
ms, which is nothing: priority was not the lever.  And the first benchmark
showed *zero* late blocks, because recompiling identical text hits
`pipeline.analyse`'s cache and allocates almost nothing — a benchmark of the
cache.  Varying the text each rebuild, which is what editing is, is what
exposed the 99 ms pauses.

#### Errors, and where they land

The editor drew a compiler error right-aligned on the line it was about —
fine for `hole` and `bank`, three words each, and hopeless for a sentence,
which starts at a negative x and is drawn through the code and the gutter.
Diagnostics are interleaved under the line they name now, wrapped to the
width, with an error that names a library hoisted to a banner at the top.
`laid_out` is the one place the interleaving is decided and the click reads
back what the draw recorded — two answers to "how many rows did the
diagnostics take" would put the cursor a line above the pointer.

Then: **where do they actually land?**  Ten kinds of error through the real
pipeline, and only two reached a line.  Three bugs behind that:

* `expand` and `enforce` parse the author's text *alone*, so a `ParseError`
  from either carries author coordinates — and `in_source` subtracted a
  2,394-line prelude from it.  A mistake in the file you are looking at,
  reported as being in a library you are not, on a line you did not type.
* The core `Expr` tree had **no positions**: `EHole` was the only node that
  carried one, so `UnresolvedName` could not say where.  `EGlobal` and
  `EVar` carry a span now, set at the single desugar site where a name the
  author typed becomes a core node.
* A position can fall *after* the author's file too — `_entry` generates
  `main = sound`, so a program with no `sound` failed at line 11 of a
  two-line program.  Named as `entry`, the way the prelude is.

Two of ten became five.  What is still a banner is `UnifyError`, whose
spans point at where the two *types* were declared rather than at the
expression that failed to unify.

**A wrong line is worse than no line**, learned the direct way: a heuristic
that anchored on any quoted word matched the `Float` in `sound : Sig Float`
and put every type error on line 1.

### State, for picking this up cold

**A `zip -r` backup exists; not a git repo yet, by the author's choice —
reviewing before committing to a history.**

#### Where the surface ended up

| you are writing | callable names | this morning |
|---|---|---|
| a synth | **~95** | 172 |
| a piece for MIDI | **48** | 59 |
| a canvas | **54** | 61 |

`synth.ges` alone: **113 → 48**, in eight sections, no convention
exceptions.  Every library now has an `internal` marker except `audio.ges`
and `gui.ges`, and those two are correct as they are — `audio.ges` is
thirteen primitives of the medium, `gui.ges` is already split by its own
`…Sub` convention.

#### Done today, all green

*Phase 2 — `internal`, enforced.*  `gestate/internals.py`, wired into
`audio.assemble`, `audioscore.assemble_performance`, `gui._program`,
`midi.perform`.  Faces are read out of the library — including instance
bodies — so nothing maintains a table.  Checks **only the author's own
lines**: `voices` expansion appends generated code that reaches for
machinery quite properly.

*Phase 3 — the prelude.*  `Semigroup`, `Monad`, `Foldable`, `Filterable`,
`Div`, `Signed`.  `prelude.ges` 65 public / 4 internal.

*Phase 3¼ — the other libraries.*  `music.ges` 14/7, `signal.ges` 6/3.

*Phase 3⅜ — constant folding.*  `audioextract._fold_constants`.

*Phase 3½ — oscillators, filters, stereo.*  Above.

#### Compiler changes today

- `prim_mod_float` — new G-machine instruction, `frem` + floor correction
  in LLVM.  Verified exact against the oracle over 200 samples, 158 of
  them with negative dividends.
- **Method-level type variables** — a class method could not carry type
  variables of its own.  `Functor`/`Monad` are impossible without it.
- **`check_kind` accepts a variable at the head of an application** —
  higher-kinded *signatures*.  Declaring such a class already worked.
- **Layout blocks survive blank lines** (`syntax/tokenize.py`).
- **`UnresolvedName`** — one unknown global produced 45 misleading errors
  about the prelude; now 1.
- **Assembly errors print as answers** — `VoicesError` and `InternalError`
  escaped `typecheck --audio` as tracebacks.

#### Three live bugs fixed, none of them on the plan

1. **`++` was unreachable in half the language.**  `music.ges` shadowed the
   prelude's, so `[1,2] ++ [3]` failed inside any program with a `score`.
2. **A blank line between two instance methods silently ended the block**,
   reporting nine errors about the prelude and none about the blank line.
3. **The test suite played audio out of the speakers.**  `test/conftest.py`
   now shuts both doors (`sounddevice` *and* `player_command`) and names
   the offending test.  `GESTATE_TEST_AUDIO=1` reopens them.

#### Also done, in the sessions after

*Phase 3¾ — `compose` is `@`.*  With the reference index's operator
anchors and the formatter's operator declaration heads, both of which it
was the first name to reach.

*Phase 3⅞ — `clamp`, `mix`, `nyquist`, and `gestate/specialise.py`.*  A
constrained definition is usable in a synth, which retires the `F` from
two names and is the first time the audio fragment has admitted one.
`mix` and `phase`/`noise` are now three plain words a program cannot use
for itself — `test_audioeditor.py` and `test_audiospans.py` both had a
`mix` and both had to be renamed.  **`mix` is the most collidable name
taken so far**, and worth revisiting if a fourth collision turns up.

#### What is left

**Phase 4, unstarted:** the twenty-name cheatsheet, and re-filing
`manual.md` §9 — which is now shorter than it was, since the `x.0.1`
lexing and the silent `Int` default are the only entries left that are
neither fixed nor a documented trade.

**Parked by choice:**

- **`'x` generalised to `pure`** — it is `pure` with syntax, pinned to
  `Score`.  Generalising changes what `'60` means in every music example
  (same result, wider meaning).  Wants a decision, not a guess.
- **`fst`/`snd` vs `.0`/`.1` — three questions, not one rename.**
  `x.0` works today (`p.0 + p.1` is 16).  But:
  1. **`x.0.1` lexes as `x` `.` `0.1`** — a float token.  A lexer fix, and
     what nested projection needs.
  2. **`fst` is the *discrete* projection.**  `test_stage2.py::
     test_a_product_fixpoint_needs_a_monotone_projection` exists to check
     that it *cannot* see a `fix` binder; deleting `fst` removes that
     test's subject.  `fstM`/`sndM` stay regardless — they are the
     monotone-arrow forms `fix` needs.
  3. **Whether `.0` is monotone or discrete is unresolved.**  Substituting
     it into that test hits the *projection needs a known type*
     limitation (`manual.md` §9) rather than giving an answer, so the
     question is open and it is the one that decides the rename.

  Two real call sites remain, both `snd` in `music.ges`.
- **`Both` and `Stereo` could be tuples** — `fixme.md` F95 is now marked
  fixed, and two comments still cite it as their reason.  Taste, not
  necessity, since a named record documents its fields.
- **`voices` generated names share the author's namespace.**  A collision
  is now *reported* clearly, but not prevented: `leadChan0f2` and
  `leadFromMidi` are host-facing (`audioschedule.py`: "`Node.chan` is the
  one name both can resolve") and cannot be renamed.
- **`gui.ges` unreviewed** — 15 callable names, `world`/`Event`/`Axis`,
  and the open question of whether `…Sub` becomes `…Of`.

**Not verified by ear.**  `stereopad.ges`, `polysaw.ges` and
`quartet.ges` were rewritten composed and then renamed twice.  They
typecheck, extract, and pass the fragment and bit-exact suites; nobody has
listened to them.  `quartet.ges`'s kit is the one place the rewrite is not
sample-identical by construction — the four drums are summed with a zero
multiplier rather than selected by a `case`.

#### Two things shipped half-done, and nothing failed either time

**`Signed`.**  The class was added in the morning with `negate`/`abs`
working at both types, and its whole point was to retire `negateFloat`/
`absFloat`.  The call sites were never moved — so the class existed, the
papercut it was built to remove stayed in **18 files** including every
example a person reads, and every full-suite run that day was green.

**`Functor`.**  Worse: the *mechanism* was proved with a scratch file
(`sum (map (*2) [1,2,3]) + unwrap (map (+1) (Just 41))` = 54), reported as
"unblocked", and then the class was **never added at all**.  `map` stayed
`List`-only for the rest of the day.  Caught by the author asking where it
was, not by anything in the suite.

Both are finished now, and verified against the compiler's own registry
rather than by grep — which matters, because grepping `.ges` for
`class Div ` finds a *comment*:

    Functor YES map          Semigroup YES ++        Monad YES >>= pure
    Foldable YES foldl foldr Filterable YES filter
    Div YES % /              Signed YES abs negate

**The lesson is about the evidence.**  A green suite says nothing about
whether a change is *complete*: the thing being retired still works, so
nothing fails, and "1538 passed" was true all day with two jobs half done.
Ask the compiler what it has — `classify(merge(...)).classes` — and grep
for the old name's *definition*.  A test run cannot tell you about work
that was never started.

#### Two things worth re-reading with fresh eyes

**`audioextract._drop_unreachable`.**  The folding rule — *fold into `map`
and `zip`; never remove or re-kind a `scan` or a `source`* — was written
correctly and then broken in the implementation within the hour: the sweep
deleted control sources, which are *interface* rather than arithmetic.
`test_audiovoices.py` caught it in five places.  That is exactly the kind
of divergence between a docstring and its code that reads as correct.

**The oscillator merge was argued three ways before it was right**: free
(wrong — two changes cancelling), costs nodes (right but incomplete), cost
removed by folding (right).  The namespace objection survived all three
and turned out to be the real one, at three collisions.  All three
readings are recorded above so nobody repeats the first two.

---

## Part III — The staged plan, as each stage closed

*Was the bulk of `roadmap.md`.*  Stages 0 through 10: the language
(0–6) and then the live audio environment (7–10).  All of them
are done — what is left is in `roadmap.md` under "What is left
after stage 10".

### Stage 0 — Correct what is silently wrong

These are ordered first because each one lets the compiler accept, or
quietly miscompile, a program.  Nothing else on this list has that
property.  All four were small, and all four are done.

#### 0.1 Signature variables are not skolems (`fixme.md` F36) — **done**

```
f : a -> Int
f x = x + 1        -- was accepted; `a` was unified with Int
```

A signature's variables are now rigid in the body they declare: `unify`
refuses to bind one (a metavariable may still be bound *to* one, which is
what keeps a signed body checkable), and instance resolution refuses to
pick a dictionary for one — the second half mattered more than expected,
since without it `f : a -> a ; f x = x + 1` still passed by defaulting to
`Int` and `show` at a skolem silently took the first `Show` instance.
Errors name the variable as written and say which context would grant the
constraint.  `test/test_skolems.py`; details in `fixme.md` F36.

One consequence worth noting for later stages: instance *method* bodies
are still checked against the instance head's variables, which are not
rigid.  Same gap, one level down, and not on this list.

#### 0.2 δ's deviations: `dummy`, `split`, and the unit change (F3, F4, F5; `errata.md` D7) — **done**

Three entries, one root: δ had no `dummyA`, so `δ[e]` returned an empty set
where the thesis returns unit, and `δ(case …)` filled its dead branches
with ⊥ instead of `dummy`.

`gestate/changes.py` now builds every zero change at its own type — `()`
where `ΔA = 1`, `⊥` at a set, componentwise at a product, and a generated
`dummy_X` at a sum, where the tag has to be reproduced from the value.
Two things worth carrying forward:

- **The D3 optimization survives**, and not by luck: at a *set* element
  type `dummy` **is** ⊥, so `for (x ∈ e) ⊥ ⇝ ⊥` still fires wherever it
  did.  Where the zero changed — `((), ())` at a relation's element — it
  was never a ⊥-rule operand.
- **One more untyped zero turned up and is fixed too**: a variable a box
  closes over, which is `s` in `f s = fix [r ⇒ s ∨ step r]`, the shape
  every Datalog query has.  `EVar` now carries its type.

Two neighbours came out of it.  `δ(πᵢ e)` was building `πᵢ ϕe δe`, a
projection applied to two arguments (`fixme.md` F57, new).  And δ's dead
branches bound one field whatever the constructor's arity.

What is *not* done: `split` is not named — □ is erased, so the outer
`case ϕe` is the split, and D7's type mismatch has no runtime witness to
fix; and the derivative of a primitive *function* is still unrepresented,
which is 1.2's contract to state.  `errata.md` D8 now records the change
structure the implementation assumes, so that decision has something
concrete to confirm or overrule.

#### 0.3 `transform` skips `main` (F9) — **done**

Picked the first option: `main` is transformed like anything else.  It
keeps its name (every transformed SC is already kept as an alias for its
`_phi`, which is what `PushGlobal("main")` finds), so the entry point is
undisturbed, and ⊥-propagation and change minimization now reach it — the
same query costs 12,652 G-machine steps in `main` where it cost 13,519,
against 12,657 one definition over.

**Why it was skipped**: no reason is recorded, and `data.md` §0 exempts
nothing.  What actually stood in the way was a different bug — ϕ renamed
a global to `name_phi` whenever `_is_user_sc` *guessed* it was a user
definition, and that guess was wrong for `chr`/`ord` (machine primitives
in none of the lists) and for any user name starting with a single `_`
(skipped by the transform, renamed at every call site).  Both crash with
`unknown global`, in any supercombinator; `main` escaped only by not
being transformed.  The skip was masking, not preventing.  Renaming now
follows the set of names the transform is actually generating pairs for,
which is what **0.4 needs too**: once ϕ/δ is gated per SC, "which names
have a `_phi`" stops being guessable from the name.

Two things to carry forward.  The naïve `fix_X` loop is now unreachable
from user code — only `__`-generated supercombinators are still skipped —
so it stays as `_desugar_datafun`'s fallback and as what §I.5 defines
`semifix` against, but nothing exercises it.  And a `fix` written inside
an instance method does not compile at all, for an unrelated reason
(`fixme.md` F58, new): those bodies never get the final substitution
pushed back through their type annotations, so the helper name comes out
as `fix_Set_a0`.

#### 0.4 ϕ/δ is applied to every supercombinator (F7) — **done**

Gated per supercombinator and per *half*, because the two are needed for
different reasons.  ϕ is a syntactic question — does this body contain a
`fix`, a box, a `for`? — and δ is not: **the proposed criterion, "does
the body mention a semilattice", is unsound for δ.**  `id` mentions none
and `fix [r ⇒ id r]` still needs `id_delta`.  ϕ calls δ at exactly one
place (`ϕ[e] = (ϕe, δe)`), so the demand starts at the globals under a
box and closes over the call graph.

On the transitive-closure query: 138 generated supercombinators down to
90, ϕ/δ halves 54 down to 6, compilation ~25% faster; the whole test
suite runs ~4s faster.  The six halves are exactly the ones the query
needs, including `fst_delta`/`snd_delta` — no Datafun in them at all,
but applied inside the box.  A wrong gate would surface as a missing
global at run time, so δ raises a targeted compiler error instead if it
is ever asked for a derivative the plan did not schedule.

**ϕ became structural while doing this**, which was not planned: it had
no rule for the Rizzo formers and returned them *unrecursed*, so a `fix`
under a `:::` compiled to the naïve loop — against `data.md` §0's "a
`fix` buried inside a signal's per-tick body gets seminaïved in place",
and the same defect as 0.3 one level down.

Stage 0 is done.

---

### Stage 1 — Settle the specification decisions

No implementation should start until these are answered, because each one
determines what the implementation should be.  They are cheap in effort and
expensive in consequence.

#### 1.1 Is `Bool` Datafun's `{1}` or an ADT? (`errata.md` D5) — **answered: both**

Answered (b), with a name: `Bool` stays the discrete two-constructor ADT,
and Datafun's `{1}` is added as **`Prop = {()}`**.  They are not two
encodings of one concept but two concepts — `Bool` answers questions about
data you have, `Prop` about data still being derived — and the deciding
case is a predicate that must be monotone in a set, `member : Box Int ->
{Int} ~> Prop`, which answer (a) cannot type under a `fix` at all.

The tax the item worried about is smaller than it looks, for one reason:
**`Prop` is an alias, not a new type constructor.**  ⊥, ∨, the eliminator,
the change structure and the fixpoint are all the set structure, so nothing
new was implemented for any of them — the whole change was three repairs to
the unit type (`()` was a value but not a type or an instance head;
`Tuple0` had no kind; `is_eqtype(Tuple0)` was `False`, so `{()}` was
neither a semilattice nor a fixtype), plus `Eq`/`Ord`/`Show ()` and the
alias in the prelude.  `test/test_prop.py`, 16 tests; the full suite is 506.

`==` keeps returning `Bool`.  **What is deliberately still open is the
coercion**, and it belongs to 2.1 rather than here: the guard clause `| e`,
`empty?`, and how a `Bool` reaches a guard position.  D5 recommends a
one-method `class Guard a where guard : a ~> Prop` with instances at both,
so the desugaring need not be type-directed — which matters, because
desugaring runs before inference.

The original question:

#### 1.1 (original) Is `Bool` Datafun's `{1}` or an ADT?

The pivotal question.  Thesis §2.2 makes `bool = {1}` load-bearing:
`for (e) f` is the one-sided conditional, which is how comprehension guards
desugar (fig. 2.2), `empty?` is the only way to case-analyse a boolean, and
`P : A → bool` is a *monotone* predicate.  Gestate has committed the other
way — `Bool` is a two-constructor ADT with `==` returning it — and
`data.md` §III.1 says so while acknowledging the encoding it does not
specify.

Three coherent answers, in my order of preference:

- **(a) Keep the ADT, re-derive the guard.**  Gestate is not Datafun; it
  has typeclasses, `Char`, `Int` and an FRP half.  Write the guard
  desugaring against `case`, drop `empty?`, and record in `data.md` that
  monotone predicates are lost.  Cheapest, and consistent with every
  choice already made.
- **(b) Add `{1}` alongside `Bool`** as the type comprehension guards use,
  with `empty?` and a coercion.  Faithful, but two boolean types is a tax
  on every user forever.
- **(c) Switch `Bool` to `{1}`.**  Faithful and coherent, but it rewrites
  `Eq`, the prelude, `deriving`, the FRP `Maybe`/`Sync` types and every
  `case` in the test suite.

Whichever is chosen, **write it down before stage 2.1**, which is the work
it gates.  *(Chosen: (b).  See above.)*

#### 1.2 State the change-structure interface (`errata.md` D8) — **partly done**

**This item was not bookkeeping.**  Examining it found that its one
knowingly-open question — the derivative of a primitive function — had
stopped being hypothetical the moment 2.1's guards landed, and was crashing
`{x | x in r, x < 3}` under a `fix`: the most ordinary Datalog query there
is.  δ emitted the discrete `()` and applied it, and because `UNIT` is
`ENum(0)` and `Unwind` on a number ignores the spine, the failure surfaced
far away as `CaseJump on non-constructor`.

Implemented (D8 has the rule and the reasoning):

- **A saturated primitive application is discrete**: its δ is the zero
  change at the *result* type, not `δp` applied to arguments.
- `πᵢ __dict_C_T__` is resolved to the method global at compile time, so
  ϕ/δ never meets a projection out of a discrete value.
- **Instance methods are transformed** — they were skipped for sharing the
  `__` prefix with dictionaries.  Dictionaries stay skipped; they really
  are discrete data.
- δ **refuses** to apply a unit, naming D8, instead of emitting code that
  dies later as a G-machine fault.

**Written down**: `data.md` **§I.8** now states Definitions 14–16 — the
three change-structure properties, the derivative law and the `□` on its
base point, the set and semilattice instances, `ΔPoset`'s composability
(which is *why* δ can be structural), the change table, and Rules 1 and 2
as the obligations gestate discharges as a plugin.  Cai et al. is cited
from §I.1 and used in §I.8, closing `errata.md` §3; the plugin
discipline and Theorem 2.9 are attributed where they are used.

Still open in substance, but with **no claimant**: a primitive over a
*semilattice*, whose argument may genuinely change.  Rules 1 and 2 cover
every primitive gestate has, because all of them take discretely-ordered
arguments.  `Score` looked like the obvious future claimant and is not
one — a score lays out to a *list* of timed events, so overlay is not
idempotent and `Score` is a commutative monoid, not a semilattice.  §I.8
states the obligation anyway, so that a future proposal meets a written
contract rather than discovering one afterwards.

Two things to carry forward.  **The suite went from 34s to ~58s** with
these changes and I could not attribute the difference: per-program ϕ/δ
counts are unchanged (the closure query still generates 3 halves, as 0.4
left it), and profiling shows inference, not the new passes, in the hot
path.  Worth a look before it is assumed to be the price of correctness.
And `{x + 1 | x in r, x < 3}` — a guard *and* arithmetic in the head —
still fails, now as `unknown global 'bottom_Set_a1'`.  That is `fixme.md`
F58's family (instance-method bodies never get the final substitution
pushed back through their annotations) and it became reachable for the
same reason: those bodies are now transformed.

The original item:

#### 1.2 (original) State the change-structure interface

Gestate has base types and primitives Datafun does not — `Int`, `Char`,
`+`, `*`, comparison, `Cyclic n` — and δ has no case for any of them; they
fall through to a zero change that happens to be right.  Nobody adding a
semilattice or a primitive has a contract to satisfy.  Write Definitions
14/15 and the rule "every non-set base type carries the trivial change
structure `ΔA = 1`, every primitive over it is discrete".

Cite Cai, Giarrusso, Rendel and Ostermann, *A Theory of Changes for
Higher-Order Languages* (arXiv:1312.0658), which no spec file references.

Do this *before* music (stage 3): `Score`'s algebra has to be stated
against *some* contract, and without one it gets settled by accident.
(It has since been stated, and `Score` is **not** a semilattice — see the
answer above and stage 3.1.)

#### 1.3 Resolve the monomorphization contradiction (`errata.md` D9)

`data.md` §I.4.3 justifies per-type helper generation with "Datafun has no
polymorphism"; `types.md` §3 and `typeclasses.md` §7.1 specify
let-generalization and dictionary passing precisely so that whole-program
monomorphization is *not* required.  Both are in the repository and they
contradict.

The implementation has effectively chosen option (a) — a monomorphic
Datafun sublanguage, with `_generalize_let` refusing to generalize at a
non-trivially-ordered type and helpers generated per concrete type.  Say
so, and say where the boundary is and how it is enforced.  Option (b) — a
`class Semilat` resolved by the ordinary dictionary machinery — is now
*feasible* in a way it was not before (structural comparators exist,
superclasses exist), and would delete `_collect_set_types` entirely.  It is
worth an explicit "considered and declined", with the reason.

---

### Stage 2 — The Datafun surface that stage 1 unblocks

#### 2.1 Comprehension guards (`errata.md` D6) — **done**

`{e | C}`, the full clause grammar `C ::= p ∈ e | e | C,D`, and the guard
clause are implemented and specified.  The query below now compiles as
written, and transitive closure is one line with no helper
supercombinator — which is what this item existed for.  `Guard` dispatches
the coercion so a guard accepts either boolean; `_` already worked.

The stage turned up a defect worth recording: **`for (x in a, y in b) e`
had never worked.**  `desugar_expr` used `bindings[0]` and dropped the
rest, so the form `syntax.md` documents compiled with `y` unbound.  Stage 0
was about programs the compiler silently miscompiles, and this was one; it
was missed because nothing exercised the syntax.  Stage 5's F29 is the
answer to that, and it is now more clearly the right next investment.

The rest of D6's sugars are done as well, at three spellings that had to be
chosen because Datafun's collide with syntax gestate already had: `empty?`
(a trailing `?` now joins an identifier; it is a primitive, since `for`
eliminates only into a semilattice), `fix r => e` (rather than reserving
`is`), and `Box p` (rather than `[p]`, which is a one-element list
pattern).  The query this stage existed for:

```
closure : Box (Set (Cyclic 8, Cyclic 8)) -> Set (Cyclic 8, Cyclic 8)
closure (Box e) = fix r => e \/ {(x, w) | (x, y) in r, (z, w) in e, y == z}
```

**Still open**: `!e`, and `split` (0.2 records why that one has nothing to
fix).  `!e` got cheap as a side effect — compile each `!e` sub-pattern to a
fresh binder plus an appended equality guard, which the clause grammar now
supports, and `(!y, w) in e` *is* `(z, w) in e, y == z`.

The original item:

#### 2.1 (original) Comprehension guards (`errata.md` D6)

```
{ (fst p, snd q) | p in r, q in e, snd p == fst q }
```

Today that query needs a two-argument helper supercombinator returning
`{…}` or `{}` — which is how `test/test_relations.py` writes transitive
closure, and it is unreadable.  The guard clause `C ::= p ∈ e | e | C,D`
is what makes Datalog queries look like Datalog queries.  **Unblocked**:
1.1 answered the boolean question, so `| e` desugars to
`for (() in guard e) …` with `guard` a one-method class dispatched at
`Bool` and `Prop` — see D5 for why a class rather than a type-directed
rule, and for the one thing to verify when writing it.  `empty?` and the
`Prop → Bool` direction come with it.

While there: `!e` (the equality-check pattern), `_` in comprehensions, box
patterns `[p]`, and `fix X is e` — all listed in D6, all sugar, all cheap
once the framework is there.

#### 2.2 `fix` at a semilattice other than `Set A` (`fixme.md` F37) — **done**

`is_semilattice` and `is_fixtype` already accept `L×M`; only the
inferencer's `EFix` rule pins the type to `Set a`.  Products of
semilattices are what lets a query compute two relations at once — the
standard Datalog idiom.  Requires 0.2 to be done first, for the reason
given there.


The inferencer now takes a fresh variable and lets `subgrammar.py` ask
*which* semilattice once the substitution has settled; codegen grew a
componentwise product family.  `Int` is still refused, with the fixtype
message rather than a type error.

One consequence worth knowing: `fst`/`snd` are discrete (`□A → B`), so they
cannot see the monotone variable `fix` binds.  A projection *is* monotone,
so the prelude supplies `fstM`/`sndM`, and two relations converge in one
fixed point.

#### 2.3 `deriving Ord`, and sets of user data types — **done**

The comparator generator covers integer-like types, `Bool`, tuples and
sets; a user ADT has no total order, so `Set C` is rejected.  Deriving one
(compare constructor position, then fields) closes the last gap in "which
types can be set elements" and finishes what stage 2 starts.


`deriving Ord` compares constructor position first, then fields
lexicographically.  This was thought to need a primitive — a constructor's
tag cannot be named in the surface language — and it does not: enumerating
both scrutinees puts the answer in the *order the alternatives are written*,
which carries the same information.

It needed two more fixes to make `Set C` actually work.  **`is_eqtype` never
consulted the constructor table for a parameterless data type**: a bare
`TCon` short-circuited before the ADT case, so `C := R | G | B` was reported
"not an eqtype" however simple it was, while `Maybe Bool` escaped only by
being a type *application*.  And the set helpers needed a structural
comparator for data types, generated the same way — position, then fields.

**And it found a bug I had introduced earlier in `empty?`** (F68): its
G-machine code hardcoded `Nil`/`Cons` as tags 0 and 1, but user
constructors are numbered first.  So *any* program with both a data
declaration and a comprehension guard died as `CaseJump: no alt for tag 4`.
Every guard test until then had declared no data type.

---

### Stage 3 — Music: the stated purpose

`spec/music.md` is 40 lines describing a complete musical language.  None
of it exists.  This is the largest remaining body of work in the project
and the only stage that is about what the project is *for*.

`errata.md` S4 records that music.md has no semantics; `fixme.md` F26 and
F27 record the two syntactic stubs.  Suggested order:

1. **Give `Score` a semantics** — **answered, and it is both**.  A
   `[: A :]` is a box-layout tree; the *list of timed events* is what
   `layout : [: A :] -> [(Onset, Offset, A, Instrument)]` produces from
   it, and the payload `A` is opaque to layout and interpreted by the
   instrument it is handed to (`music.md`, `errata.md` S4).

   Two consequences are already settled by it.  **`Score` is not a
   semilattice**: overlay is associative and commutative but not
   idempotent, since `a || a` lays out to two events, so it is a
   commutative monoid, `ΔScore = 1`, and `for` cannot eliminate into it.
   And therefore **a query cannot build a score directly** — the bridge is
   to run the query to its fixed point, observe the result discretely
   (`□{A} -> [A]`, which the generated comparators already support), and
   fold that list with `++`/`||`.  Seminaïve evaluation stops at that
   boundary by design.

   The constructors are settled too: `(') : a -> [: a :]` is the unit note
   (one beat; `|*` reaches every other duration) and `r` the unit rest, so
   S4's "uninhabited as declared" is retired.  No existential is needed, so
   **stage 4's F35 is not a prerequisite**.

   All three of the implementation gaps this uncovered are **fixed**:
   `fixme.md` F59 (prefix operators away from the start of a phrase, so
   `'a ++ 'b` — any sequence of notes — resolves correctly), F60 (`Void` is
   a builtin type; `:=` still requires a constructor), F61 (`[: a :]` parses
   in a signature and means `Score a`).  `test/test_music_syntax.py`.

Two more fell out of it and are fixed too.  The **fixity table** now
   gives `music.md`'s stated grouping — overlay 2, duration scaling 3,
   sequencing 4, so scaling applies to the sequence beside it rather than
   its last note.  (`++` could not move up instead: it would land on
   `::`/`:::` at 5, and an `infixl` sharing a precedence with an `infixr`
   is ambiguous.)  And **F62** — `[a]`, the list type `syntax.md`
   documents, was not a type; it needed a `VList` case in `desugar_type`
   *and* one in `_signature_tyvars`, without which the `a` in `[a]` was
   never collected as a signature variable.

   **Step 2 is done as spec work**: `music.md` types every operator.  `@` is
   withdrawn — `>>=` is instrument selection — and `|*`/`|/` take a plain
   `Int`, with `ToInt`'s `toInt` written explicitly at the call site, since
   the constrained form would make `x |* 2` ambiguous between `Num` and
   `ToInt` and hand it to defaulting.  What is left is *bodies*: no operator
   has an implementation, and `ToInt` is not in the prelude.

   `[: Void :]` survives `@`'s withdrawal after all: an instrument is
   `a -> [: b :]` applied by `>>=`, and one whose result holds only
   committed leaves is parametric in `b`, so it unifies with `Void`.  No
   erasing *operator* is needed — parametricity does it — and `Void` (F60)
   keeps the use that motivated it.  Stretch became a value, `sp : [: a :]`,
   so `|~|` is out of the fixity table with `@`.

   The one piece with no surface syntax is the committed leaf: `'` makes an
   *unassigned* note (`a -> [: a :]`), and its counterpart carrying a
   playable `R` (`R -> [: a :]`, parametric) is what an instrument returns.
2. **Type the eleven operators.**  `||`, `++`, `|~|`, `|<`, `>|`, `r`,
   `'x`, `|*`, `|/`, `@`, `>>=` have fixities in `descend.py` and nothing
   else — no types, no instances, no bodies.  Most can be ordinary prelude
   functions once `Score` is a real type.
**Steps 1–4 are done, and step 5 with them.**  `gestate/music.ges` declares
`Score a` and every operator, `gestate/midi.py` reads the layout out of the
heap and writes a Standard MIDI File, and `test/test_music.py` asserts on
event tuples.  A program supplies `score : [: Void :]` and `bpm : Int`.

The one structural decision worth recording: **music is not in the core
prelude.**  It declares eight constructors, a tag is a position, so merging
it renumbered `Nil`/`Cons` for every program — 61 tests failed exactly that
way — and every non-musical program paid its compile time (the suite went
98s to 230s).  The backend prepends it to a music program's source, which
needs no module system and is what `errata.md` S1's "the interface is the
deliverable" implies anyway.

The original plan:

3. **`Score` as a monad** (`>>=`).  Needs either a `Monad` class — which
   needs higher-kinded type variables, currently absent from the kind
   checker — or a monomorphic `bindScore`.  Decide which; the former is a
   real type-system extension, the latter is an afternoon.
4. **Records — done** (F28).  Records were never missing: `syntax.md`
   says a record *is* a one-constructor data type, and pattern matching on
   one always worked.  What was missing is `x.N`, and it now works for
   tuples and records alike, **resolved from the base's type** rather than
   through `syntax.md`'s sixteen `AttrN` classes — those would buy
   record-polymorphism nothing has asked for at the cost of ~120 generated
   instances, and D9 already settled that this language is monomorphic
   where it matters.  The one case given up is an unannotated `f p = p.0`,
   and the error says so.

   `{: … :}` (F26) is unrelated — it is the *eq-set* literal syntax, and
   is still unimplemented.
5. **Rendering.**  Layout and notation output.  Arguably a host-language
   concern rather than a compiler one — Part I §11 says
   so — but then it needs an interface, and that interface is the
   deliverable.

**This stage should be estimated honestly before it is started.**  It is
larger than stages 0–2 combined, and unlike them it has no reference
implementation to check against.

---

### Stage 4 — Type-system completions — **closed, none of it needed**

Closed under Part I's rule: **do not build what nothing
needs.**  Every item here was assessed and every one of them fails it — not
"deferred", *closed*, and to be reopened only by a caller appearing.

- **Multi-parameter classes** (F33's remaining half).  `class C a b` parses;
  `instance C Int Int` is rejected.  No caller, and it is not cheap:
  `Predicate` carries one `type_`, and `head_type` is singular across
  `declarations.py`, `constraint.py`, `coherence.py` and `elaborate.py` — 23
  sites — with predicate matching, coherence overlap, the solver and
  dictionary naming (`__dict_C_T__` has nowhere for a second type) all
  assuming arity one.  A structural change to the class system for a
  `Collection c e` nobody has asked to write.
- **Orphan-instance rule** (F34).  **Vacuous, not missing.**  An orphan is
  an instance in a compilation unit owning neither the class nor the type;
  with one compilation unit there is no such thing.  F34's own text says so
  and asks to be *recorded* as blocked on modules, which it is.  There is no
  work here — only the appearance of some.
- **Existential dictionaries / `ShowBox`** (F35, `typeclasses.md` §7.3).
  This was the one with a caller, and it lost it: the music design needs no
  existential, because an instrument's result holds no payload-carrying
  leaves and *parametricity* reaches `[: Void :]` on its own (stage 3.1).
  What remains is heterogeneous collections, which nothing wants.  The
  blocker, when a caller appears, is one error: the kind checker rejects a
  constructor-field type variable the ADT head does not bind (F63).
- **Specialization** (F35's other half).  A performance concern with no
  measurement demanding it — and **unsound as specified**.  §7.2 prescribes
  "during or after inlining"; `errata.md` R9 records that β/η is not
  equivalence-preserving across `head`, `delay`, `⊛`, `5` or a `Sig`-typed
  subterm, and no rule fences it off.  R9 states the rule; it would have to
  be written into the spec before any inlining pass exists.

  Note what is *not* precedent for this: `resolve_static_methods` (stage
  1.2) folds a projection over a known tuple constructor.  No lambda is
  reduced and nothing moves across a `delay`, so it does not license the
  inlining half.

### Stage 5 — Confidence

Nothing here changes behaviour; all of it changes how much the behaviour
can be trusted.

- **F29 — property tests: done.**  Both the ones this item named are in
  `test/test_properties.py`: a random pattern matrix checked against a
  direct interpreter (including that an unreachable row is *rejected*), and
  the set operations — literals, join laws, comprehensions, guards,
  two-generator products, `fix` closure — checked against the same
  computation in Python.  Seeded `random` rather than Hypothesis: no
  third-party dependency, and the spaces are small enough that a failure is
  already near-minimal.

  They found nothing, which is the honest result and not a wasted exercise:
  both bugs this stage was motivated by — the dropped second generator and
  the false-guard-under-`fix` crash — are now covered by properties that
  would have produced them on the first case, and they had already been
  fixed by the time these were written.

  **`examples/` is there too** — nine runnable programs, four of the
  language and five of music, executed by `test/test_examples.py` against
  the results their own comments claim.  Writing them found five defects
  653 tests had not: three parse bugs and two in the `typecheck` CLI.

  The rendered `examples/music/*.mid` are **golden**: rendering is
  byte-deterministic, so a change to layout, tick arithmetic, event
  ordering or channel allocation is a diff in a file you can listen to.
  Still missing from F29: golden ASTs and heap-shape tests.
- **F42 — sharing: done, and §I.7's proposed test was wrong.**
  `test/test_sharing.py` asserts the *shape* — δ of a `for` binds `ϕe` and
  `δe` once each — verified by breaking the sharing deliberately and
  confirming the tests fail.

  §I.7 suggested measuring the query for Θ(n²) instead.  That cannot detect
  it: with sharing removed the step counts are indistinguishable, because a
  `for`'s source is almost always a *variable*, and duplicating a variable
  reference is free.  The asymptotic penalty it warns about needs
  `for (x ∈ <computed expression>)`, which neither paper writes.  `data.md`
  §I.7 is corrected in place.
- **F22 — FRP heap-shape traces: done**, with R12's `filter` trace written
  into `frp.md`.  Per-step *values* were the weaker claim — a driver that
  reallocated a cell per update would pass every value test in the file —
  so §4.5's `sample` is now asserted against cell identity, live-set size
  and clock sets.  The `filter` trace earned its own section: `watch l`'s
  clock is `{(sig, l)}`, a *signal* clock rather than the channel clock
  `sample` inherits, which is why allocation order is load-bearing there.
- **F30, F31 — error quality: done.**  Substitution dropped the `span` when
  rebuilding a `TApp`, severing the location plumbing at the first
  substitution (F31) — one line.

  F30 asked for `unify` to return `Either` rather than raise.  **Declined
  and recorded**: that is Haskell's way of making a failure impossible to
  ignore, and a Python exception already is; converting would touch 28 call
  sites, and the three that catch were checked — one asks a genuine yes/no
  question in a two-line `try`, two catch to *enrich* the message.
  `types.md` §2 is amended to say so.

  What was actually wrong here is fixed: `unify` is symmetric but its
  message is not, and the application rule called it `(expected, actual)`,
  so `f : List Int -> Int` applied to `True` reported "expected Bool, got
  List Int" — the roles swapped, in the most common type error there is.
  The argument order is now part of `unify`'s documented interface.

### Stage 6 — Spec hygiene

Bookkeeping.  Cheap, and the file that most needs it is the one people read
first.

**Done.**  Of the 28 `errata.md` entries, 26 are now resolved or answered.

- **S2, F40** — both pipeline diagrams rewritten against the real one, with
  the four places where **order is load-bearing** stated and why each is.
  §0 also settles the scope question it left ambiguous: ϕ/δ is applied per
  supercombinator *and per half*.
- **S1** — `data.md` §II.4 now *points at* `frp.md` rather than restating a
  different machine, keeping only what is unique to it (why the machine must
  change at all) plus a table mapping the old names to the real ones.
- **S3, F23–F25** — `Box` and `deriving` added to the reserved-word list,
  `..` added to the fixity table, `music.md`'s `(|< a)` typo corrected.
  `->`'s un-overridability is now **enforced** as well as stated: a user
  `infixl 9 ->` silently replaced the built-in `infixr 1` and re-associated
  every function type in the program.
- **D7** — the missing ϕ/δ rules are in, including §I.4.4 giving `ϕ(split e)`
  *and* the reason it has that shape (Φ does not commute with □ over a sum),
  both marked as not reached in gestate since □ is erased.  One row is new:
  `empty?` exists now, and its δ is a zero change because its argument is
  discrete — §I.8's Rule 2 and the `□Prop → Bool` arrow agreeing.
- **D10, R10** — the reasons behind the rules, now stated: why `fix` takes a
  *boxed* function (a zero change to a function is a derivative for it), that
  `for` is a big *join*, and the asymmetric type-formation premises that make
  `μα. A + Sig (A × α × A)` legal and `μα. 1 + (α → α)` not.
- **R9** — the β/η rule is written into `frp.md` as a constraint on *every*
  optimizer: no β or η rewriting across `head`, `delay`, `⊛`, `5` or a
  `Sig`-typed subterm.  `typeclasses.md` §7.2 now records that its
  specializer is bounded by it, since inlining is β.

Two things deliberately left open.  `examples.md` still does not exist
(S3, F29), and the `d`-prefix namespace constraint is recorded as an
*unenforced assumption* rather than a bug (F67): a program written to
collide produces the right answer anyway, so the hazard is unproven and a
check would have to be shown necessary first.

---

### Stage 7 — The live audio environment

**This is where the work was.**  The full argument, the evidence and the
per-stage failure modes are in `spec/liveaudio.md`; this section says what
order it happens in and what each part is waiting on.  All of 7.0 to 7.6
are built.  **A gestate synth compiles to machine code, plays at 593x real
time, and can be edited in a window while it sounds.**  It turned up two
things that were not stages of it: the control-clock disagreement (open
question 3), which is **stage 8 below and is done**, and an editor written
*in* gestate rather than hosting it, which is not.

The end goal: you edit a synth while it is sounding, and the sound changes.

The structure is `spec/liveaudio.md`'s six stages, and they differ from
stages 0–6 in one way worth stating: **each one is verified against the one
before it, sample-for-sample, and no stage begins before the previous one
verifies.**  The offline renderer stops being the product and becomes the
oracle.  That is a better position to build an engine from than most
projects get, and it is why `render()`, the committed `.wav` files and the
`.samples` buffers beside them never go away.

| | deliverable | checked by |
|---|---|---|
| 7.0 | golden sample buffers for the audio examples — **done** | *is* the check |
| 7.1 | the static signal fragment, defined and enforced — **done** | programs that must be **rejected**, by name |
| 7.2 | graph extraction: `Sig Float` → flat node list — **done** | bit-identical to `render()` |
| 7.3 | `render_block`, still in Python — **done** | identical at block size 1, 2, 64, 1024 |
| 7.4 | codegen to **LLVM IR**, driven by a real device — **done** | bit-identical to 7.3, offline, *before* any callback |
| 7.5 | live update: recompile, re-extract, hand to the engine — **done** | an identity swap must be bit-identical |
| 7.6 | the environment: a window to edit a synth in — **done** (a scaffold) | it plays, applies and reports |

**7.0 is done**, and it earned its afternoon twice over.
`examples/audio/*.samples` are the committed `float64` buffers — 600 samples
of `blip` and 800 of `drums`, each file carrying the rate and duration it was
made at so that regenerating it cannot move them, checked exactly by
`test/test_audio.py` and rewritten by `python -m gestate.audio <file>
--golden`.

It also found the first stage-7.4 hazard, which is the return on doing it
first: **the oracle emits subnormals routinely.**  A one-pole filter under
silence decays geometrically and never arrives at zero — ~440 samples to the
subnormal range, against a 3,445-sample silent sixteenth at 22,050 Hz — and
an engine with FTZ/DAZ or `-ffast-math` will produce exact zero there.  The
bit-identical comparison would fail at samples nobody can hear.
`spec/liveaudio.md` stage 4 states the options and says to choose one before
the comparison fails, not after.

**7.1 is done**, and it behaved like the real design work it was billed as.
A flat graph can only be extracted from a *static* one, so the audio
compiler accepts a sublanguage — first-order step functions over flat
types, non-allocating, exactly two clocks — and the checker says *which
definition* leaves it and *why*.  This is the third time this project has
drawn such a boundary (the monomorphic Datafun sublanguage, D9;
`[: Void :]` as what the MIDI backend accepts), and it reads like
`subgrammar.py` on purpose.

Three findings, in order of what they cost:

* **`drums.ges` was not in the fragment**, though `spec/liveaudio.md`
  promised it would be.  Same cause as `blip.ges` — a constant list read
  per sample — and worse: `elem` is polymorphic, so after elaboration it
  carries an `Eq Int` dictionary.  Both examples now write the table out as
  a `case`, and **the sound did not change**: identical to the stage-7.0
  goldens and to the committed `.wav` files, byte for byte.  An earlier
  stage checking a later one is this plan's method working as designed.
* **The flat types are a fifth subgrammar.**  Reaching for
  `is_finite_eqtype` is the obvious move and is wrong twice: it excludes
  `Float`, and every eqtype admits `Set`.  And unlike Datafun's four, an
  unknown type is a *rejection* here — which is what makes the fragment
  monomorphic without a second rule.
* **Automatic list lifting is deferred, not dropped.**  `liveaudio.md`
  assumed the extractor would lift a constant list to an array; for `elem`
  that means specialising a recursive function and erasing its dictionary.
  A source-level table is what such a lifting would produce anyway, so
  writing it by hand costs the author a little and stage 2 nothing.

**7.2 is done**, and it is the stage that proves the method.
`gestate/audioir.py` is the graph and its eight-form IR,
`gestate/audioextract.py` flattens a `Sig Float` into it, and
`gestate/audioengine.py` runs it one sample at a time.  `blip.ges` is five
nodes; `gain` and `lowpass` stop being definitions and become the last two,
with their arguments folded in as literals.

**The bit-identical check caught a real bug on its first run**, which is
what it was built for.  `scan`'s recurrence is

    out[t] = f(out[t-1], in[t])

— own state from the previous instant, **input from this one** — and the
obvious reading, written first, used `in[t-1]`.  The reason the obvious
reading is wrong is the property this project keeps returning to: `f z
(head s)` sits inside `scan`'s `delay`, so it runs an instant later, and by
then `s` has been overwritten in place.  A signal is a cell, not a stream.
Nothing but a sample-for-sample comparison finds this: the sound is
plausible either way.

Two more results:

* **Node identity is decided**, as 7.2 was required to: **migrate**, keyed
  on a path of the definitions a node was inlined through
  (`sound/lowpass/scan#0`).  Editing a step function, editing a folded-in
  constant, and inserting a node downstream all leave earlier origins
  untouched — all tested.  A second call to the same definition on the same
  path does renumber the first, and that is recorded rather than hidden.
* **Open question 3 moved to 7.3, with a reason.**  `zipSig` on one clock
  extracts and is bit-identical.  Two clocks cannot be settled here at all:
  `render()` drives `min(reactive.chans)` and only that one, so a two-clock
  program has **no oracle to be identical to** — and "held across a block"
  has no meaning before blocks exist.  Extraction refuses a second clock
  and says both.

**7.3 is done**, and it did two things beyond its deliverable.

`render_block(graph, state, n)` fills a buffer and carries a `State`
between calls, the way a callback does.  Both examples are identical at
every block size — 1, 2, 3, 64, 1024, and an uneven sequence of them — and
identical to the naive per-sample reference and to the oracle.

* **The invariant needed correcting.**  "Block size must not be audible" is
  right for an audio-rate graph and backwards for a control-rate one: a
  control node is *defined* as updating once per block, so the block size
  is part of the instrument once a parameter exists.  Both facts are now
  asserted, so neither can be mistaken for the other.
* **Open question 3 is answered.**  The clocks are partitioned by *name*
  (`clock` is audio rate; any other channel is control), the oracle learned
  to drive a control clock (`render(control_every=n)`), and a `zipSig`
  across the two is bit-identical at block sizes 4, 8 and 16.  The control
  value is held, not interpolated, and a test says so because the spec
  names interpolation as a later refinement.
* **It found a bug in the oracle** — `fixme.md` F91.  `render()` took the
  audio clock to be `min(reactive.chans)`, and ids are handed out in
  evaluation order, so the first two-clock program written had `clock` at
  1 and the new channel at 0: the renderer advanced the user's channel
  every sample and never ticked the clock.  Resolved by name now.

**7.4's target is decided: LLVM IR, emitted as text from pure Python.**  The
argument is in `spec/liveaudio.md` and turns on the criterion this whole
plan is built around — a C compiler contracts `a * b + c` into an `fma` by
default, which changes exactly the expressions a synth is made of, so
bit-identity from C depends on remembering a flag on every compiler
forever.  In IR the question does not arise.  The generator imports
nothing; `llvmlite` is optional and buys the in-process JIT that makes
stage 5's recompile a millisecond.  Two hazards are already named: `Int`
becomes `i64` (measured: `drums` reaches 25.7% of its range), and Python's
floor division is not LLVM's truncating `sdiv`.

**7.4's code generation is done, and the gap is closed.**
`gestate/audiollvm.py` emits textual LLVM IR and imports nothing;
`build`/`run_native` shell out to `clang` where there is one, and the tests
skip without it the way the MIDI tests skip without `mido`.  The generated
code is bit-identical to stage 3 over both committed golden windows, at
block sizes 1/7/64, with a control clock, and at `-O0` as well as `-O2`.

**Measured**: `blip` at **28.4 M samples/sec** and `drums` at 17.2 M —
593× and 359× real time at 48 kHz, under 0.3% of one core.  The
interpreter does ~1,400 samples/sec.  Four orders of magnitude, from the
same source text, with the language never entering the callback, which is
the entire architecture in one number.

Two bugs, and **both were invisible at `-O2` and fatal at `-O0`** — which
is why both are built and compared:

* **A generated function collided with libm.**  `audio.ges` defines
  `floor`; at `-O0` LLVM lowers `llvm.floor.f64` to a *call* to `floor`,
  which bound to the generated one, and `wrap` recursed half a million
  frames.  At `-O2` the intrinsic is an SSE instruction and nothing
  happens.  Generated symbols are `gestate.`-prefixed now.
* **A primitive's name is not its type.**  The G-machine shares one
  instruction between `Int` and `Float` wherever Python's operator is
  right on both, so `helpers.py` and `elaborate.py` emit `prim_lt_int` for
  a `Float` comparison *deliberately*.  The instruction is chosen from the
  operand type as emitted, never from the name.

The floor-division correction was needed, and is tested at negative
operands specifically — an example that only divided positives would pass
without it.  The `i64` narrowing has not bitten and is not checked; it is
the open hazard.

**And it can be heard.**  `gestate/audiolive.py`:

    python -m gestate.audiolive examples/audio/drums.ges --seconds 5

**Python is not in the audio path.**  One call per block —
`render_block_f32`, a second entry point the generator emits — fills the
device's buffer in the device's format, clamping as `audio.write()` does.
Putting that conversion in Python would have been easier and would have put
a garbage collector between the engine and a deadline.  Backends:
`sounddevice` when installed (a real PortAudio callback, and untested here
because it is not installed), otherwise a pipe to `pw-play`/`paplay`/
`aplay` — no third-party package at all, and the pipe's back-pressure is
the clock.  Three seconds of audio costs 0.7 s of CPU including compiling.

A sound card cannot be asserted on, so the test puts `cat` where the player
goes and compares **the bytes that would reach it** against the oracle's
samples.  It found a defect at once: a `memoryview` of a ctypes array is
*typed*, so slicing it by bytes re-sent stale frames — a stutter at the end
of every finite render.

**Compilation is 400 ms** (206 front end and extraction, 2 emitting IR, 190
`clang -O2`).  Interactive, but slow enough that 7.5 should keep the old
engine sounding while the new one builds rather than pausing — which
crossfade-or-migrate needed anyway.

**7.5 is done: a synth can be edited while it sounds.**

    python -m gestate.audiolive examples/audio/blip.ges --watch

Save the file in any editor and the sound changes without stopping.  The
decision 7.2 was required to make is what pays here: a node keeps its state
when its **origin** survives the edit, so rewriting a step function or
turning a folded-in constant leaves the oscillator's phase alone.

**How it is caught being wrong**: swapping to a graph extracted from the
*same text* must be bit-identical to never having swapped.  That is the
whole of migration's correctness in one comparison, and a mid-stream swap
is checked the same way against a reference computed through the Python
engine.

Two rates, kept apart — this is the design:

* **Building** (~400 ms: front end, extraction, `clang`) runs on a worker
  thread while the old engine keeps sounding.  A *failed* build does not
  interrupt it either: a typo mid-phrase is ordinary, so the error is
  reported and the instrument plays on.
* **Installing** — read the state out, migrate, write it in, swap — is
  microseconds and happens between blocks, on the thread filling them.

Two findings, both from building it:

* **A type's name is not its layout.**  Editing `Voice Float Int` to
  `Voice Float Float` keeps the name and changes what a value *is*;
  carrying the slot across would reinterpret an integer as a double —
  silent, and audible only as a wrong noise.  Migration compares the
  **shape**: origin, kind, and the constructors resolved through.
* **The watcher's baseline must be taken before the first build.**  A build
  is 400 ms and a save inside that window was folded into the starting
  stamp and lost — save twice quickly and the second vanished.  Taking it
  early costs at most one redundant rebuild, which is the right way round.

**7.6 is done, as a scaffold.**  `gestate/audioeditor.py`:

    python -m gestate.audioeditor examples/audio/knob.ges

A window with the synth in it, playing.  Edit, Ctrl-S, and the sound
changes without stopping; a broken edit is reported in the status line and
the instrument plays on.  The slider drives the control-rate parameter, so
`examples/audio/knob.ges` is a tone you can bend with the mouse while
rewriting the code underneath it.

`Workbench` owns the instrument, the rebuild worker and the knob and
imports no toolkit — it is what the tests drive; `Editor` is a `tkinter`
view.  **It is not what the spec's stage 6 describes**, which is an editor
*written in* the signal vocabulary, with `balanced.py`'s rope as its
document.  This one hosts a gestate synth in a Python window instead.  The
split keeps that a replacement of one file rather than a rewrite.

**And it reopened open question 3** — which **stage 8 below then closed**.
What 7.6 found, and why it needed a stage of its own, is worth keeping as
written; the last paragraph of it is the part stage 8 overturned.

Writing `knob.ges` — a third example,
so the slider would have something to turn — showed that the interpreter
and the engine do not mean the same thing by a control tick.
`react(reactive, inputs)` runs a full instant *per input*, so two channels
are two instants: `sync` never sees `SyncBoth` from the driver, and
everything downstream of the control clock takes an extra step that
produces no sample.  The engine simply holds the value across the block.

For maps and zips the two agree, which is why 7.3's test passed and why
that claim has now been narrowed to what it actually tested.  Put a `scan`
under the control clock and the interpreter accumulates twice per boundary
— with a knob at 40 and 8 arriving it adds 48 in one sample, a number
`test_audiograph.py` now pins.  The engine's semantics is the right one for
an audio engine and the language cannot currently express it; the fix is to
let the driver take several arrivals as one instant, which is FRP-core
surgery and wants its own stage.  `knob.ges` therefore has **no golden
buffer**: a golden would freeze one of the two answers.

*(Stage 8 built exactly that fix.  The number is 8 in both now, and
`knob.ges` has a golden buffer.)*

**Two decisions were already made, and the third — state — is now made.**

- **Step functions are compiled, not restricted to a UGen set.**  The
  cheaper option turns gestate into a wiring DSL and throws away the one
  thing the audio experiment established.  The restriction that makes
  compilation tractable is checkable, and is the same shape this project
  already imposes twice.
- **Two clocks, and exactly two.**  `sync` across clocks *is* control rate
  versus audio rate, arrived at honestly rather than by imitation; a
  GUI-driven parameter is a control-rate source, and that is how the
  environment reaches into a running sound.
- **State across a recompile: migrate**, keyed on the origin path 7.2
  gives every node.  Decided there rather than in 7.5 because migration
  needs stable identity across compilations and an extractor cannot be
  retrofitted with it.  Migration is what makes an edit feel like editing
  rather than restarting.

**What must not change**, because the engine's guarantees rest on them:
guarded recursion and in-place signals (productivity and bounded memory are
what make a signal safe in an audio callback at all), and `scan` as the way
state is written.

**The open questions are in `spec/liveaudio.md`** — how much the fragment
rejects, where `sin`/`exp`/`sqrt` come from given that offline and generated
must agree bit-for-bit, whether `zipSig` across two clocks survives
extraction, and what node identity is made of.  All four are settled by
writing programs and by 7.2's bit-identical check, which is the argument for
doing 7.2 before any code generation.

---

### Stage 8 — one instant, several arrivals — **done**

Stage 7 ended with the oracle and the engine computing **different sounds
for the same program**, and that is the only kind of item this project puts
first.  `spec/liveaudio.md`'s open question 3 has the argument; this is what
was built.

`react(reactive, inputs)` ran a full instant *per input*, so a block
boundary — an audio clock and a control clock ticking together — arrived as
two instants rather than one.  Everything downstream of the control clock
took an extra step that produced no sample.  For maps and zips that is
invisible, which is why 7.3's test passed; put a `scan` under the control
clock and the interpreter added the held 40 *and* the arriving 8 in one
sample where the engine added 8.

**An instant is now a set of arrivals.**  `Arrivals = {channel id: value}`
is threaded through `ticked`, `advance`, `_update_one` and `reactive_step`,
and `react_instant` runs one instant on several channels.  `react` is
unchanged — one arrival, one instant, the paper's rule, and what every FRP
test in the suite exercises.

**It is a conservative extension, and the shape of the rules is why.**
Every rule asked exactly two questions of κ — *is this the channel that
ticked*, and *what did it carry* — and both have per-channel answers.  Set
membership replaces equality; a lookup replaces the single input threaded
down the recursion.  That second half is not bookkeeping: `advance` on
`wait κ` has to read **κ's own** value, or a `sync` hands the control side
the audio side's sample.  `spec/frp.md` §"Several arrivals in one instant"
states it against the paper's rules.

**One rule changed meaning, by becoming reachable.**  `sync` reported
`SyncBoth` only when both sides watched the same channel, so it never came
from the driver at all.  Two clocks ticking together is the ordinary way to
reach it now — and a `.kr → .ar` boundary is exactly what `sync` was for,
which `spec/liveaudio.md` §"Two clocks" claimed before there was an engine
to want it.

**What it is checked by** is the thing stage 7 could not have:
`examples/audio/knob.ges` has a golden buffer.  It had none on purpose,
because a golden would have frozen one of two answers.  600 samples at
2 kHz, with `control_every: 64` in the header — a control-rate buffer is
only defined against the block schedule it was rendered at, so the golden
format carries one now.  The whole chain is bit-identical on it: oracle,
extracted graph, block renderer, and generated LLVM through `clang` at
`-O0` and `-O2`.  The oracle is the oracle for **every** program again,
not only for the ones that declare no second channel.

Two smaller things fell out of it:

- **Two values on one channel in one instant is refused**, rather than the
  second silently winning.  That is two instants, and saying so keeps the
  caller honest about which it meant.
- **`advance` on a `wait` whose channel did not arrive is an error.**
  `ticked` gates every call, so it is unreachable from the sweep; it is
  there because the two must not be able to drift apart quietly, which is
  the same reason δ raises rather than emitting a derivative it did not
  schedule (stage 0.4).

What this does **not** do is interpolate.  A control value is held across
the block, which is what `spec/liveaudio.md` says it is; linear
interpolation stays the later refinement it was always described as.

### Stage 9 — Transcendentals, and two synths to call for them — **done**

`spec/liveaudio.md`'s open questions 1 and 2, closed together because each
was the other's evidence: the functions needed a caller, and the synths
worth writing needed the functions.

**The reframing is the result.**  Open question 2 asked how offline and
generated `sin` could agree bit-for-bit, and treated it as a question about
*accuracy*.  It is not — `sin` is not correctly rounded, so two libraries
may differ in the last bits and both be right, and no amount of precision
would make the comparison exact.  What makes it exact is **identity**: the
interpreter's `math.sin` and the generated `llvm.sin.f64` reach the same
libm on the same machine, and LLVM's constant folder uses the host libm
too.

That was measured before anything was built, which is the only sensible
order: had it come out the other way, the answer would have been polynomial
approximations written in gestate, and the primitives would have been a
mistake to have added first.  `sin`, `cos`, `exp`, `log`, `sqrt` are
primitives; **`tan` and `pow` are written in the language**, because an
identity in gestate is the same expression on both sides and is
bit-identical by construction rather than by libm agreeing about one more
function.

`test/test_transcendental.py` is the measurement, and its sharpest case is
the one a runtime comparison cannot see: **constant folding**.  A synth
folds constants into its nodes, so `sin <literal>` is a shape the extractor
really produces, and at `-O2` LLVM computes it during compilation rather
than calling libm at all.  The test asserts the fold *happened*, so it
cannot pass vacuously.

**The two synths**, and what each is the caller for:

- **`fm.ges`** — the one instrument that cannot be written without a real
  sine.  FM's character is entirely in the sidebands a *sinusoidal*
  modulator creates; modulate with a sawtooth and the result is noise.  It
  also has two envelopes, one of them on the modulation index rather than
  on volume, so the timbre changes across a note.
- **`pluck.ges`** — three harmonics, each with its own `exp` decay, steeper
  the higher the partial.  That is what makes a pluck sound plucked, and it
  is physics rather than an effect.  Additive rather than Karplus-Strong
  because a delay line is a *buffer*, and the fragment admits no allocation.

**Open question 1 got its answer too, and the answer is "nothing".**  Both
extract to five nodes and were bit-identical through the block renderer and
generated code at `-O0` and `-O2` on the first run.  That is the honest
result and worth as much as a finding: the fragment was drawn in stage 7.1
against two examples, and two more written *for an unrelated purpose* fit
inside it without adjustment.  `pluck.ges` also tests a claim
`spec/liveaudio.md` had only asserted — several oscillators in one graph is
a graph the extractor already handles — which it used to argue that dynamic
voice allocation should wait, and which nothing had exercised.

One thing did bite, and it is neither the fragment nor a defect: a
continuation line inside a `case` alternative may not begin with a bare
identifier, so a constructor application broken across lines with a
trailing plain argument is rejected.  `syntax.md` §"Continuation lines"
states that rule and the tokenizer matches it exactly — a documented
limitation meeting a real program, not a disagreement.  Naming a helper is
the fix at the call site and it read better, which is the usual outcome.

### Stage 10 — Notes, a score its instruments play, and a place to play it

The stage that joined the two backends.  `spec/liveaudio.md` has the design;
this is what it amounts to and what it cost.

**A note does not need an event list**, which the previous stage said it
would.  A note becomes *values* — `gateAt`, `offAt`, and the program's own
payload — and `gateAt` names **the sample the note begins at**, so the voice
compares it against its own `ticks` per sample and a note delivered at a
block boundary still begins partway through the block.  No allocation, no
change to the fragment, and the thing named as the eventual fight turned out
not to be one.

- **`voices lead 8 : Custom -> Sig Float`** — a bank of N copies of one
  voice, expanded to ordinary declarations before `classify`.  Polyphony is
  the one thing the static fragment cannot express; a *fixed* bank is not.
- **`Played a`** — timing beside the payload.  A note's times come from the
  layout that placed it or the key that was pressed, and asking an author to
  carry them inside their own record was asking them to model MIDI.
- **`Assigned Voice`**, beside `Play Rendered`.  Parametric in `a` exactly
  as `Play` is, so `[: Void :]` goes on proving every note was assigned —
  which is why `Score` needed **no second type parameter**, the first design
  and the wrong one.  The guarantee came out *stronger*: a payload type ties
  a note to a bank that takes it, so a mis-routed note is a type error.
- **`FromMIDI`** — `noteOn ch p v = Maybe a`.  The instance says a payload
  can come from MIDI; `Nothing` declines a note; a switch per bank says who
  listens.  All three are needed: two banks may share a payload type and
  nothing in the type can tell them apart.
- **A transport** — play, stop, seek, loop — between the driver and the
  engine, where all four are one comparison between blocks.

**Where the defects were is the finding.**  `fixme.md` F97 records nine, all
in the Python *around* the engine and none in the language, the fragment or
code generation.  That half is checked sample-for-sample and turned up
almost nothing; this half has no oracle, and four of the nine were silent —
the synth played and every indicator said it worked.

### `!` binds one atom, and `constSig` goes inside

`!(f x)` used to be the same lift as `!f x`, and the codebase asserted the
conflation was *necessary* — "application folds into an atom before fixity
resolution, so the two spellings are one tree by the time anything can
look."  That was true of the routing and false of the grammar, and the
counterexample was already in the parser: in argument position `g !f x`
binds the marker to one atom (`_PREFIX_ONLY_OPS`).  Doing the same at head
position (`parse._marks_head`) separates the trees with no paren node
anywhere — the parentheses carry no meaning of their own, they change which
atom follows the marker, exactly as they change which atom follows `f` in
`f (g x)`.  `spec/exclamation.md` walks the whole argument.

The rule is now uniform: **`!` takes the next atom as the head, and the
application around it supplies the lifted arguments.**  `!x` and `!f x y`
mean what they meant; `!(f x)` is the constant signal of the computed value
— the reading both guides wrote and the old parse silently turned into a
lift; `!(f x) y` lifts a computed head, and the fragment refuses it for the
closure it is, with the same message the hand-written `map` draws.  The old
sharp edge — `!(a * b)` a constant but `!(f x)` a lift — is simply gone.

With the parenthesised constant writable, `constSig` had no job left in a
program, so it is the renderer's machinery now in the enforced sense:
`internals.RENDERER_PRIVATE`, refused from author text with "reach for `!`
instead".  The renderer still defines it — it is the node the marker
builds, over whichever clock is running — and the `Floating`/`Num`
instances still build on it.  Every `constSig` in `examples/` and the
tests now spells its constant with the marker, and the one test that
enshrined the old necessity is replaced by two that state the new rule.

### Every filter dial is a signal now

`lowpassSvf`, `bandpassSvf`, `highpassSvf`, `notchSvf` and
`lowpassLadder` take their **resonance** as a `Sig Float`; `resonate`
takes its **decay** as one; `audio.ges`'s `lowpass` takes its
**coefficient** as one.  The engine had paid for this all along — every
step function reads its dials per sample out of its `In` record, and the
`Float` in the signatures was only the interface being narrower than the
machine under it.  The promotion is the sweep-merge argument finished:
a literal is a constant signal, the constant folds back into the step,
and the fixed form costs what a fixed form should — so the narrow types
bought nothing but the inability to move a dial.

One shared internal record carries each filter's control pair
(`CtlIn := CtlIn Float Float` — one tag, one shape, any number of
graphs; it is one tag with *two* shapes that collides).  `audio.ges`
grew `LowpassIn` for the same job at its level.  Six author-side sites
needed the lift for a `Float`-typed dial — `(!filtQ)`, `(!bassQ)`,
`(!seconds)` in the three modal instruments, `(!ring)` in `gamelan` —
and every other caller was already a literal.

### Comments are trivia now, and none are lost

The `spec/comments.md` repair landed, aimed at three goals at once:
comments must never change what a program means, must be easy for a
tool to reach, and must survive the formatter.  A comment is no longer
an atom — `x = 5  # gain` is `x = 5`, and the constructor-arity lies
are gone — and no skip site drops one either: the parser collects every
in-declaration comment onto `VModule.comments` in source order with
spans, the formatter reattaches each beside its declaration, and the
documentation tools keep reading the raw text they always read.  The
near-miss worth remembering: `descend` rebuilds the `VModule`, and the
first draft of the fix lost the new field right there — the same
one-representation-two-consumers trap, one layer up.

### The other half gets its first oracles

`spec/verification.md`'s differential checks are in
(`test/test_verification.py`), and all four passed on first contact —
which, for once, is the headline: the engine's reputation extends
further into the Python around it than the stage-10 postmortem feared.
The identity edit moves nothing (`migrate(g, s, g') ≡ s` for unchanged
source, delay-line rings included); 512 samples diced as 1×512, 8×64
and a ragged mix are the same samples and the same final state; two
copies of one mid-flight state render the same sound to the last slot;
and **a quiescent scored session through the C host is the offline
render** — one `schedule.control_for` feeding both `run_native` and
`Host.fill` with controls pushed at exact block boundaries, which is
the seam `audioeditor._push_controls` documents having shipped two
silent defects across while the suite drove only the Python path.
Every assertion is total — whole vectors, whole runs — because silence
was the failure mode being closed.  The transcript format is still to
come; these are the checks that needed no format to exist.

### The instrument leaves the workshop

`spec/export.md` stopped being a design in one long evening: `shell/`
holds a CLAP shell in Rust (a hand-declared ABI subset, no
dependencies, an empty well-formed factory until a graph arrives), and
`python -m gestate.export` turns a `.ges` into a `.clap` — the graph's
IR as a static archive, a generated `descriptor.rs` carrying what only
the compiler knows, cargo around both.  The fact that made the shell
thin: the engine's state starts as zeroes, because the generated
code's first-instant branch seeds every `init` itself — so no state
image travels, and *rewind is free*, which became the transport rule
(stop is silence, play is the piece from its top, two plays are one
performance).  Knobs are CLAP parameters — a channel is a knob unless
the `voices` expansion made it — and notes play the first bank through
a Rust mirror of `audioalloc`, with payloads from the program's own
`noteOn` run through the G-machine at export time and tabled.

Every step shipped with its parity, each a miniature ctypes CLAP host
in `test/test_export.py`: the plugin renders what `run_native`
renders; the replay after stop is byte-identical to the first play; a
turned knob is the engine at that value; **a played note is the
scheduled note**, the Rust allocator against the Python one through
the samples.  The near-misses worth remembering: the audio-ports
extension, whose absence a home-made host cannot see and a real DAW
punishes with silence; and `fmpoly`'s demo score, which made plain
`assemble` the wrong assembly and taught the test to choose the way
`note_bank` does.  Six plugins in `~/.clap` tonight, next to Dexed
and Surge, at a sixtieth of their size.

### Multi-rate, host tempo, and the pack closes

The last two items on the CLAP list.  **Multi-rate** is what "a
constant folded through the program" costs when the host disagrees:
one whole graph per rate, the entry symbols suffixed in the IR text
(`\b` in the rename, learned when `@render_block` ate its own longer
siblings' prefixes), `objcopy` localising the shared helper names so
two graphs link into one library, and `activate` picking by rate.
**Tempo** cost nothing but a convention: a Float channel spelled
`tempoChan` is the transport's, not a parameter — the program reads
the DAW's tempo as an ordinary signal.  The one finding on the way:
the "bug" where the tempo landed a block late was the engine's own
control-rate semantics (`:::`'s initial plays the first block),
verified against `run_native` before the shell was blamed — the
differential habit paying for itself on the first suspicious block.

Seven parity tests now walk the plugin as a host would, and the pack
in `~/.clap` — a dub track, a violin joke, a drone with Float dials, a
duet with a routing matrix, an FM piano — sits beside Dexed and Surge
at a fiftieth of their size, remembering its knobs, following the
timeline, answering a keyboard at any of its rates.  Where this pulls
the substrate is the question the next session inherits.

### `beat` finds its conductor, and the convention dies young

`tempoChan` lived one day.  The context contract said why it was wrong
(a channel's spelling carrying meaning the compiler cannot see), and
the repair is in: both assemblies grew a `clock_text` seam, the
exporter passes a host-fed `beat` — three channels carrying a *line*,
evaluated at `ticks` by ordinary signal arithmetic, slots declared in
the descriptor rather than spelled in the shell — and `beatRate`
answers "how fast is this going" in beats a second.  The design
questions resolved on the way: a program's `bpm` and `tempo` are not
discarded in a DAW, they are how gestate-as-its-own-renderer answers
`beat` and the free-running default besides; `bpm : Int` stays a
declaration because the schedule is compiled from it, and the runtime
rate is `beatRate`'s to carry; the unused clock prunes with
reachability, which is all "discarded when not needed" ever needed to
mean.  One measurement corrected a belief: control writes land on
their *own* block — the one-block lag the tempo test recorded was the
`:::` initial masking the first write, nothing more.

### The editor is not written in gestate, and the canvas behind it is

The largest item on the post-stage-10 list was **withdrawn** rather than
built.  `spec/liveaudio.md` §"Why the editor is not written in gestate"
has the argument, and the decisive fact is small: the language cannot
measure text, so it cannot lay it out, and an editor written in it would
ask the host for every position it draws.  `balanced.py`'s rope is already
an editor's document interface, in Python; moving it into a language whose
`String` is `List Char` would rebuild it on a worse substrate.

**What replaced it was nothing, deliberately** — not a Python editor as a
*stage*.  The environment is a scaffold and may stay one until a feature
wants better.  `Rect`-and-`Dot` proved the reactive half; what a GUI
vocabulary should be after that is a thing to grow from programs that want
it, the way `signal.ges` was extracted at the third combinator rather than
designed at the first.  Specifying it in advance was what the item was
doing wrong.

**The interface question was what reopened it.**  `tkinter` holds the text
well and its widgets are clunky; a *timeline* — scrubbing, dragging loop
points, widgets between lines rather than beside them — is what tk cannot
do, and is the point at which `balanced.py`'s rope earns its place.

Then a program wanted it, and `spec/substrate.md` is the answer — **which
does not undo the withdrawal.**  The editor is still Python and the
language still cannot measure text.  What the spec adds is the *other half
of the window*: a canvas behind the editor, in the same window, drawn by
the same program, and composed the way the synth above it is — one
`substrate : Sig Sub` built from smaller ones with `over`, `moveXY` and
`still`, lifted over time with `!`.  A leaf attaches a channel
(`onDrag c (still …)`) and the synth reads **the same signal the canvas
draws**, which is the whole feature.

Three readings were tried and set aside, each recorded in the spec: a
registry of `Sub a` declarations (could not say where a dragged position
lives), a value in the type (gave `over` a question with no good answer),
and elements as signal functions (unnecessary once `Sub` is data the host
walks — the transform for hit-testing falls out of the draw).

Three things made it cheap rather than a second system.  **`Workbench`
imports no toolkit**, so a `pygame` view is a second view against the
object that already has the instrument, the rebuild thread and the tests —
the seam was put there for this.  **The engine needed nothing**: a `Sub`
opens a control channel, and one slot per block is machinery that has been
there since the knobs were lifted.  And **the rope was already a document
interface**, which is the half of a text editor nobody wants to write
twice.

S1 to S4: the assembly (`audio.preludes` decides conditionally, so a synth
with no canvas carries none of it, and `test/test_substrate.py` holds the
invariant that adding a canvas changes no samples, no node count and no
node *origins*); `Sub` with `still`/`over`/`moveXY` and one walk that draws
it; attachment, where the walk that draws also says what listens and where,
so a press reaches an element in *its own* coordinates and writes a channel
the program named; and the window — `gestate/audiopygame.py`, `Workbench`
untouched, the rope as the document, `Esc` outward through text, command
and canvas, `--plain` for anyone who wants none of that.

S5 is the reverse direction: `peak : Chan Float` and `position : Chan Int`
are well-known names a canvas declares to be *told what the instrument is
doing*, written once a frame from the view and never from the audio thread.
A peak is **taken** rather than read — a meter shows what has happened
since it last looked — and it is only tracked, by sampling sixteen points
of a block, when a file asks for it.

Audio stays compiled and the substrate stays interpreted, meeting at the
block boundary where the host already stands.  A `Sub` that wanted to
compute per sample would be asking to be a synth, and the answer is to
write it as one.

### Four files, and the knob limit they turned up

**Source spans for graph nodes.**  `gestate/audiospans.py` joins a node's
origin path to the file and line the definition was written on, and
`python -m gestate.audiospans <file> --source` prints the placement so a
person can check it against the files.

**Four files, not one**, which is where the work was.  A synth is assembled
from `prelude.ges`, `signal.ges`, `audio.ges` and the author's source, and
an editor may want to open any of them — `lowpass` is as editable as
`sound` is.  The first three are combined two different ways and **only one
preserves coordinates**: `signal.ges` and `audio.ges` are prepended as
*text*, so a line range identifies them exactly, while `prelude.ges` is
merged as a *module* and its spans start again at 1.  A line test alone
would have placed `floor` in the middle of whatever the author happened to
be writing, so names decide that one.

Two things it turned up.  **`Node.clock` is not inherited** (`fixme.md`
F93) — the docstring said it was, no reader consults it off a source, and
believing it would have offered a knob for a `mapSig` over a knob.  And **a
synth had at most one control-rate source**, which the next item lifted.

**One knob per synth — lifted.**  The fragment was rejecting a third
*clock*, conflating two rates with two channels; N control channels tick at
the same rate and need no third one.  Separate channels rather than a
record on one, for a live-coding reason: stage 5 migrates by shape, so
adding a field would reset every knob, where adding a channel leaves the
others sounding.  `render_block`'s control argument became a pointer to one
slot per source, and `examples/audio/twoknobs.ges` is bit-identical across
all three engines.  It turned up `fixme.md` F94 on the way — a former
nested directly inside another lost its element type, which a step
function's own type answers.

### The environment, and a controller is a value

**The environment**: knobs placed beside their declarations, `Ctrl-S` to
save and apply, `Ctrl-Return` to audition without writing the file, and
right-click MIDI learn on any knob.  Written in Python, which is now the
design rather than a shortfall.

**MIDI CC**: `gestate/audiomidi.py`, and `--midi` on the player.  A
controller is a *value*, so sampling it once per block loses nothing
audible — the same reasoning that lets a note arrive at a block boundary
and still begin partway through it.

### Stereo, and the ceiling that was `main`

The estimate held: the graph already did n-channel, and what was left was
the output plumbing.  `sound : Sig Stereo` for a program's own record of
`Float`s renders to a two-channel `.wav`, extracts unchanged, and comes out
of the generated engine bit-identical to the oracle —
`examples/audio/stereo.ges` is the example and its golden is *frames*
rather than floats.  The count is `Graph.channels`, read off the output
node's type in one place, and the five it reaches are `audio.py`'s reader
and writer, `audiollvm`'s output store, `audiolive`'s two drivers and the
player's `--channels`.

Two things it turned up.  **`main : Sig Float` was the real ceiling** — the
entry point the renderer appends fixed the channel count where no program
could argue with it, so a stereo `sound` failed to unify against a line its
author never wrote.  It carries no signature now and the shape is checked
where it is read.  And **the count has to come from the type**, because the
G-machine spells an `Int` and a `Float` with the same `NNum`: read off the
value, a `Frame Float Int` renders its integer as a sample and nothing says
otherwise.

Left undone on purpose: **changing the channel count in a running
instrument.**  The driver's buffer and the player process are fixed when
playback starts, so an edit from mono to stereo installs a graph the driver
is still filling one channel at a time.  Stage 5 migrates state by shape
and has nothing to say about the buffer around it.

### Tuples reach the engine

`fixme.md` F95 is **fixed**, and it was the expensive branch of the fork
taken rather than the cheap one: the IR grew tuples instead of the grammar
being tightened to forbid what `is_flat` already admitted.

The entry's own representation objection is what made it look expensive.  A
tuple is an `NTuple`, which the G-machine deliberately gives *no tag* and
never matches with `CaseJump` — field access goes through `Proj` — while
every other flat value in the audio IR is an `NCon` with a tag word, which
`Graph.layouts`, `audiollvm`'s struct emission and `unpack_state` are all
written against.  **The objection was answered rather than routed around**:
a tuple now reaches the engine tagged like any other product (the block
renderer hands back `(202, (l, r))`), so none of those three needed a
tagless case, and `sound : Sig (Float, Float)` renders identically through
the oracle, the block renderer and the generated code.

What it leaves behind is three comments standing on a dead constraint —
`signal.ges`'s `Both`, a `voices` bank's generated `Part` records, and
`audio.ges`'s `LowpassIn` ("a zip needs a carrier and a tuple has no layout
in the fragment").  None is *wrong*, since a named record documents what
its fields mean and a tuple does not, but the necessity is gone and only
the taste remains.

### The compiler answers questions

`--query NAME`, `--holes` and `--fits TYPE` on `gestate.typecheck`, with
`--audio` to put the synth preludes in scope (`doc/manual.md` §"Asking the
compiler").  Each answers about the program **as compiled** — the type from
inference, the position from the parser — so an editor showing them cannot
drift from what the compiler thinks, which is the whole reason to ask the
compiler rather than to re-parse beside it.

### Ariadne — chance and listening become leaves of the score

`spec/ariadne.md` is the design and `spec/dynscore-constraints.md` is the
sheet it answers to.  The redesign of the score's reactive surface: chance
and listening as lawful **zero-width leaves of the score monad** rather
than boxed constructs beside it, bound with the `do` sugar
(`spec/monad.md`).

Stages one to three: `draw` and `hear` are leaves, the boxes are gone,
`sown` and `probe` are retired by name, and the interpreter walks
self-terminated cue streams (`CueEnd`) so **a decision's width is a fact
its own stream reports** rather than a number the caller had to know.

**Paths — the machine half.**  The sower stamps each question with the seed
of the place it stands, the cue carries it, and `Transcript.reader_of`
answers *by it*, so a rebuild mid-piece lands on the answers the take gave
rather than on its opening ones.  That closed the defect the stage was
ordered for, and `test_ariadne.py` holds it with a counter-proof — the same
rejoin answered in arrival order drifts.

**The label half.**  A section is a *point*, not a wrapper: `Mark` carries
a `String` and `section name s` is `Mark name ++ s`, so the existing marks
stream became the piece's map with no second walk.  `marks_of` reads it (a
prefix, for an endless form), `tick_of_mark` counts occurrences left to
right, and **naming a part costs no event and no tick.**  It forced a
language change worth having on the way: **`case` matches string
literals**, so `case name of "verse" -> …` is writable at last.

**A joint of undeclared width** is now *defined* rather than silent.
`durOf` of an unanswered question is 0, so `Seq` has nothing to step over;
`resumeSeq` asks `opaqueHead` and stops at the joint, so the phrase
restarts there — audible, answered from the thread — instead of the walk
never advancing and falling quiet.  The cure for wanting the skip is one
word, `long n`, which is why it is load-bearing.

### `shape`, `fermata` and `tempoShape` — one family, and a channel-id defect

**Designed in `spec/shape.md`, and all three built.**  They turn out to be
one family distinguished by what they bend: `hear` bends content, `shape`
bends a value, `tempoShape` bends time, and **`fermata` bends whether time
runs at all** — Henri's channel-taking fermata, which is `hear`'s twin
across the table.

`shape` is an annotation over a subtree: across the subtree's own extent a
named channel follows an envelope, its breakpoints in **fractions of the
span**.  A crescendo across a verse is a musical fact the score had never
been able to state — `bpm`/`tempo` are global, dynamics are the DAW's
automation, and `Envelope` lives in signal land against `elapsed`.

**The laws come from the law** (route a constant through it and the algebra
must not notice): fractions make it scale with `|*` and reverse with
`reverse` definitionally; riding the subtree rather than the events makes
it commute with `>>=`; and a flat envelope is a channel written once,
indistinguishable from a knob.  **Delivery was solved machinery under a new
name** — the host clock already drives `beat` sample-smooth by sending a
*line* `(base, slope, anchor)` that the graph evaluates at `ticks`, and a
score envelope is that pattern generalised to one line segment per
breakpoint interval.  No new engine capability, no new wire.

It also **dissolved the `Chan -> Port` bridge rather than building it.**
`Port` had been introduced on a premise nobody checked — that `Chan` is out
of scope in `music.ges` — and the premise is false: `Chan` is a builtin and
`NChan` already carries a unique id, so the signatures take channels
directly and the bridge stopped being a thing that needed crossing.  Its
one cost was measured and then paid: **`crust` learned `NewChan`**, the
smallest widening of the pure core — a counter and an allocation — so
listening pieces keep the native path.

The migration turned up a real defect: **`_force` minted channel ids from a
scratch counter**, so separately forced channels all came out `NChan(0)`.

## The plugin grows a face with two sides, and a seed you can turn

Two features that turned out to be one piece of work, because both of
them needed somewhere in the window to live.

**A seed is a parameter now.**  A chancy piece is a *family* of
performances — `nightdrive` picks a road every four bars, `arpeggiator`
picks a held key every sixteenth — and the seed says which one.  Export
baked the number the file was written with and that was the end of it:
a plugin played one night, forever, and the only way to hear another was
to edit the source and export again.  Making it a **parameter** rather
than a setting decided everything else: the host saves it with the
session, automates it, shows it in its own generic UI, and a player who
found a take they like keeps it by doing nothing.

The mechanism cost almost nothing, which is the sign the machinery was
already right.  A new seed is a new piece from its first instant, so
there is nothing to patch and no way to fade between two — the stream
has to be opened again *where the transport stands*, which is exactly
what a timeline jump does.  So a re-seed sets `needs_seek` and borrows
the seek path whole; the two cannot drift apart because they are one
path.  `Piece::open`/`reopen` take the seed as an argument instead of
reading `Program.seed`, the descent worker's request carries it (a
worker descending on the *exported* seed would hand back the wrong
piece), and the saved state gained one optional field on the end — no
version bump, so sessions written before the RNG existed still open, on
the seed they were always playing.

**And the canvas arrived.**  `spec/substrate.md`'s other half has been
runnable at home since `gestate.gui` and unreachable from a plugin;
it now exports.  `export.substrate_of` sends the serialized program,
the eleven `Sub` constructor tags, the declared channel **names**, and
the *bridge*; `shell/panel/src/canvas.rs` turns the loop once a frame —
arrivals, `reactive_step`, `main`'s cell, walk, paint — on the window's
own thread, so the picture and the score are forced by different
threads and neither waits for the other.

The **bridge** is the piece worth naming.  A channel the canvas writes
may be a channel the compiled graph reads — that is "one fold, two
readers" — so the export pairs each such channel with the control slot
the graph reads it from, and a knob's slot *is* its parameter id.  A
touch on a canvas fader therefore produces two things: the channel
write that moves the picture, and the `Change` that moves the sound,
as one gesture, so the DAW gets one undo step.  The reverse direction
matters as much and was nearly missed — a host moving a bridged
parameter has to write the channel too, or the canvas is a display
that is right only while you are the one touching it.

Three mistakes paid for, and the first two are about **what a host is
allowed to assume about a program**:

*Channel ids are not a property of the program.*  An id is allocated
when a declaration is first forced, so it depends on what the host
forces and in what order — forcing the declarations first gives
`cutoff` id 0, letting the program reach it gives id 2, and both are
correct readings of one file.  Sending ids meant two languages had to
make the same choice with nothing checking, and they did not.  Names
cross instead; the shell forces them in the order given and keeps
whatever it is handed.  Nothing has to agree because nothing is being
guessed.

*A knob is not any control source.*  The bridge first paired every
declared channel the graph read, and `envelope.ges` showed what that
meant: its graph reads sixteen `keysChan…` slots, one per voice of a
bank, and those are not parameters — the plugin publishes only the
controls with `knob` set.  Pairing a channel with an unpublished slot
hands the host an id belonging to somebody else's parameter, so a touch
on the canvas would have moved an unrelated knob.  The set of ids a
shell may be handed is exactly the set it publishes.

*The origin is part of the tree's meaning.*  `gui.py` walks from
`cx = cy = 0`, so a substrate's centre sits at the window's **corner**
and the program places itself — `substrate.ges` opens with
`moveXY 120 140` for that reason.  Centring the picture in the pane
looked more sensible and added half a window to an offset the program
had already applied; the first screenshot had the fader in the
bottom-right corner.  The parity fixture is now taken at the
reference's own origin, so the test pins the convention rather than
only the arithmetic.

**The toolbar** is what made room for both: `CONTROLS | CANVAS` on the
left, `SEED 01234 [RNG]` on the right, fixed chrome that does not
scroll and is hit-tested before the content it lies over.  The names
are `spec/panel.md`'s own — it already called the two sources the
controls and the canvas — rather than naming where they sit, because
where they sit is the part most likely to change.  `RNG` is a button
and deliberately not a fader: every value a drag passed through would
be a different piece, so a one-second drag would ask for sixty
re-roots and throw away fifty-nine.  One press, one take.

A strip that would be empty is not drawn, and a seed that governs
nothing is not offered: a synth with a baked event list has no entropy
to reroll, and a button that changes a number you cannot hear is worse
than no button — it is one that lies.

**And then a file that does both.**  `examples/audio/lantern.ges` is
the example the window had been missing: an unfolding score *and* a
canvas, so both halves of the toolbar are lit at once.  Writing it
turned up three defects that no existing file could reach, which is
what the example was for.

*The canvas assembly never shadowed its preludes.*  `audio.assemble`
and `audioscore.assemble_performance` both put the author's text
through `prelude.shadow_libraries`, so a program may name whatever it
likes and the library definition it hides steps aside.  The canvas
assembly did not, and nothing noticed for as long as no file both drew
and played: a canvas alone never sees `music.ges`, and a piece alone
never comes through `gui.py`.  `lantern` called one of its definitions
`bar`, which `music.ges` also defines; the audio half compiled it and
the canvas half refused with *"Duplicate type signature for 'bar'"*,
about a name the author had every right to.  Three assemblies, three
readings of one file, and they have to make the same promises about
the author's namespace.

*A comment could hang the host.*  `shape_plan`'s guard was `if "shape"
not in source` — a raw substring scan, because walking an endless score
for annotations it does not have never ends.  `lantern` wrote "they
share a shape" in a sentence about its figures, and the offline render
sat there until the step limit fired with nothing in the message to
connect the two.  The guard now reads the *parsed* program, so the word
has to be used rather than merely written, and falls back to the text
scan only when the file will not parse — which is a file with a real
error to report anyway.

*The faders ran backwards.*  `onTouchY` reports 0 at the **top** edge:
that is what the host measures and there is nowhere else for it to come
from.  A fader drawn to fill from the bottom looks perfectly correct
standing still and runs the wrong way the moment you drag it — the
handle leaves your finger and climbs as you pull down.  The picture is
the program's to compose, so nothing but a hand could have caught it,
and the fix is the rule: **the handle goes where the finger is**, and
what "more" means is chosen afterwards to suit.  `substrate_parity.rs`
now presses top, middle and bottom and checks both the value *and*
where the bright handle was drawn, because those two are produced by
different halves of the system and can disagree.

**The number is also a field you can type in**, which is the one place
this panel takes the keyboard — and the rule it seemed to break is the
rule it keeps.  Keys go back to the host, always, because a DAW lets you
play the piano while a plugin window has focus; the exception lasts
exactly as long as somebody is typing into a five-character box, and
every key the field does not want goes back even while it is open.  The
editor is digits, backspace, enter, escape and a caret: no selection, no
cursor to move, no clipboard, because the field holds five characters
and each of those would be a thing to get right for nobody.  What it
does have is three ways of not losing your work quietly — a press
elsewhere commits rather than discards, an empty field commits nothing
rather than selecting take zero, and `RNG` closes the field rather than
leaving a caret over a number it no longer describes.

## Words in a declared box

`Sub` can say what its faders are.  `Label Int Int String Colour`, and
the whole design is in which of those four arguments is not there: **no
scale.**

The canvas has been able to draw a fader and not able to name it, so
`lantern.ges` shipped with a comment saying its colours were the only
labels a picture could carry.  That is a workaround being documented as
a feature, and `spec/panel.md` had already done the thinking: text
*layout* is what withdrew the editor — a cursor position, a wrap point,
a hit between two characters all need to know how wide a glyph came out,
and that is the host's secret — but a **label needs a box**, which the
program can simply write down.  `gui.ges`'s law survives intact: the
extent is declared, never measured.

So the box is on the constructor, exactly as `Rect Int Int Colour`
declares its own, and every leaf states its extent where it is written.
An earlier reading had the box borrowed from an enclosing `Sized`, which
would have made the walk carry "the box I am inside" — state threaded
through a descent that has managed without any.

**How big the letters come out is then a consequence rather than a
choice**, and that is the interesting part.  The host fits the largest
whole cell into the declared box: `min(w / (4n - 1), h / 5)` on a 3×5
cell with one column between letters.  Arithmetic on numbers the
*program* wrote — so `gui.py` and the Rust walk reach the same answer
without either measuring a glyph, and the parity test holds them equal
item for item on a real file.  Sizing a caption *is* setting its type
size, which is what the law costs; a box a few pixels narrow draws at
one and overflows visibly, which is the failure an author can see.

**It crosses without widening the core.**  A `String` is `List Char` and
a `Char` is its code point, so a label on the wire is a cons list of
numbers `crust` already has: no new node kind, no new instruction, only
`Cons` and `Nil` joining the tags a substrate carries — which the
score's own wire has carried all along.

Two things fell out of the vocabulary growing, both of the same shape —
*a reader that assumed what it would be handed*:

`audiopygame._canvas` matched `rect` and then had an `else` that
unpacked five fields, so the editor stopped opening with a `ValueError`
about a tuple the day a third item existed.  An `else` that assumes what
is left is a defect waiting for the vocabulary to grow, and this
vocabulary is *designed* to grow; it matches by name now.

And `gui.run` — the command the module's own docstring advertises, in
`doc/manual.md` and `examples/README.md` too — had been calling an
undefined `_shape` over a *list*, from when a program supplied
`scene : Sig Scene` and a `Scene` was a list of shapes.  That spelling
was retired with `Scene` and this was not, so the reference host had
been raising `NameError` for however long: nothing calls `run` from the
suite, because a window is the one thing the tests deliberately never
open.  It draws through `_flatten` now, with the same 3×5 cells rather
than a system font — the cell is part of the vocabulary, so the
reference draws it.

**And the reconcile that `Label` was predicted to force.**
`spec/panel.md` said `TouchX`/`TouchY` versus the spec's `onDrag`
"should be reconciled before a third element arrives and picks one by
accident"; the third element arrived, so `spec/substrate.md` now shows
what was built and keeps the drafts beside them with the reason each
changed — `still` went with `Scene`, a `Chan Point` became one channel
per axis because a fader is one parameter and a pad is honestly two, an
`Axis` argument became the name because an argument that is a literal at
every call site is the caller saying which of two functions it meant,
and a pixel offset became a fraction of the element's own extent so
motion is constrained by construction.  `onPress` is in neither the
built vocabulary nor the bin: open question 1 still holds it, and
`Label` left it exactly where it was, needing no event at all.

## The editor moves to Rust

`shell/editor/` — a rope, a public-domain bitmap font, a window that
owns its own event loop, and a C ABI Python drives it through.  The
reason is one Henri stated plainly: pygame is ugly by default, and the
GUI should live in one place.  The reason it was *worth* doing is
narrower and was already on the record — three painters had drifted
apart, one of them (`gui.run`) had been raising `NameError` for months
because a window is the one thing the tests never open, and the glyph
tables of the other two were four characters apart within an hour of
being written.

**The font question had a good answer sitting on the machine.**
`/usr/share/doc/xfonts-base/copyright` says, of `font-misc-misc`:
*"Public domain font.  Share and enjoy."*  No attribution, no reserved
name, no licence to ship — and, more to the point, it is already a
bitmap, so there is no rasterizer, no hinting, no glyph cache and no
per-size atlas.  Coverage was measured rather than guessed: across
three million characters of this repository's own `.ges`, `.py` and
`.md`, 10×20 misses seven distinct characters, forty-eight occurrences
between them.  `tools/pcf.py` lifts the glyphs out; what is committed is
its output, checked by looking at the letters.

**The rope's bug was real and had been there all along.**  Porting
`balanced.py` against a replayed-edit fixture failed at edit 348 — and
the *oracle* failed there too: measured over four thousand random
edits, nodes reach `|balance| = 4`.  The text is always correct, which
is why it never showed; the tree just quietly loses its logarithmic
bound.  `retain` plus one `rebalance` is the textbook AVL move and is
right when an edit moves *one* node, because then a subtree's height
changes by at most one.  A rope's edits are **bulk**: one `erase` takes
most of a subtree away, one `insert` grafts several levels on, and a
single rotation only pushes the imbalance down to a child nothing will
look at again.  The port uses `join` — descend the taller spine to a
node of matching height and splice.  Six thousand randomized sessions
agree, checking text, summaries *and shape* after every edit.

**And a second rope fault that only measurement finds.**  Loading a
file as one segment is defensible on paper — one allocation, and the
tree earns its shape as it is edited — and is wrong: every `rowpos`
became a scan of five million characters, and drawing fifty lines at
row 199,000 took **1.5 seconds**.  Chunked and built bottom-up it is
118 µs.  `SPLIT` went from eight to a hundred and twenty-eight at the
same time, which was safe precisely because the parity fixture compares
*answers* and not shape — stated when the fixture was written, and this
is the change it was stated for.

**"It feels slow" is not a measurement, and three separate things were
wrong.**  The blit went per-pixel through a bounds-checked accessor,
including the blank rows — and most rows of most glyphs are blank, so
half the work was writing nothing.  `fill_rect` wrote the background
one indexed store at a time: seven hundred thousand of them.  And every
keystroke rebuilt the whole document as a `String` for a callback that
ignored it.  Underneath all three: a software rasterizer without an
optimiser is twenty times slower, so `[profile.dev] opt-level = 1` is
now in the workspace — debug assertions kept, and a repaint at 3.6 ms
instead of 48.

The instrumentation is what settled it, and is kept:
`GESTATE_EDITOR_TIME` prints where a frame goes,
`GESTATE_EDITOR_STRESS` never lets the picture go clean so the
*platform's* half can be measured without a hand on the keyboard.  It
answered the question that mattered — **`present` costs 0.02 ms**, so
softbuffer's MIT-SHM path through XWayland was never the problem and no
amount of tuning it would have helped.  It also found four milliseconds
a frame spent OR-ing an alpha byte over the whole screen; `Canvas` now
carries the alpha into its writes and the buffer is handed over with a
`memcpy`.  The plugin panel had the identical waste and shares the fix.

**The boundary is a version, not a document.**  A keystroke never
crosses it: the rope is Rust's, the window loop is Rust's, and Python
polls `ged_version` — one atomic read — fetching the text only when it
has moved.  `Workbench` stays the model and decides what the file is,
when to rebuild and when to save; the editor never learns any of that
and by construction cannot.  The ABI is hand-declared on both sides,
like `crust.py`'s and like `shell/clap/src/abi.rs`, for the reason that
file states.

Two mistakes worth keeping.  Folding "type over a selection" into one
undo step depends on *which* entry you drop: the erase pushes the
original document and the insert pushes the half-done one, so what must
go is the second — dropping the first is the obvious way round and
makes undo stop at the hole, with the selection gone and the
replacement gone too.  And loading text from the host has to go through
the same "the document changed" path as a keystroke: the window is the
authority on what the document holds, and a load that quietly skipped
the notification left `ged_text` handing back the text the caller had
just replaced.

## The editor becomes the editor

The rope and the window were the easy half.  What made it an editor was
a day of Henri using it and saying what was wrong — twelve separate
reports, of which **not one was found by a test**.  Two thousand of them
passed throughout.

**The command language is gestate, restricted.**  `gestate/command.ges`
declares every verb with a type and a sentence; `gestate/session.py`
reads that file and *is* the palette.  A capability therefore cannot
exist without appearing in the list, because appearing in the list is
what declaring one is — the same argument `doc/ref/` already makes about
the libraries.  `Named a` is a phantom type, `FromCC` sits beside
`FromMIDI`, and the restriction that makes a command language out of a
programming one is the one this project keeps reaching for: no
conditionals, no loops, no variables, reached by *taking away* rather
than by inventing a second syntax.

**The types are what let the view ask.**  Eleven of the thirty-two verbs
take arguments and none of them were reachable until the list could
collect them; the signature says how many and of what kind, so picking
`loop` opens a question rather than running anything.  A `Named` gets
the names ranked by the model, a `Path` gets what is in the directory,
an `Int` is typed — offering a list of numbers would be a menu of
guesses.  The ranking lives in exactly one place and the window asks for
it, which is why `shell/editor/src/palette.rs` deliberately does not
sort.

### Three bugs that measurement found and reasoning did not

**One keystroke behind.**  Typing showed the *previous* character, and
only after the transport stopped.  Six guesses were wrong.  What is
true: `baseview` waits on the X connection's file descriptor, and
`softbuffer` was handed the *same* connection — its round trips read
that socket, moving queued events into XCB's own queue where they are no
longer bytes on a descriptor and no longer wake the loop.  A keystroke
landing there waited for the next keystroke's bytes.  While the
transport ran it was invisible, because the beat redrew the window sixty
times a second and every present drained the queue; `stop` took the
mask away.  **So a clean frame is presented anyway** — skipping the
expensive half, keeping the copy and the present, half a millisecond for
a connection drained on a schedule instead of whenever somebody types.
`GESTATE_EDITOR_STRESS` was the decisive experiment: forcing every frame
made the lag vanish, which pinned the mechanism in one run after an
afternoon of theory.

**A segfault on quit, and it was two bugs.**  `Workbench.stop` called
`host.close()` immediately after `join(timeout)` — *whether or not the
thread had stopped* — and only then said "closing now may crash".  That
is not a risk of a crash, it is the crash: the workspace freed under a
live audio thread.  Underneath it, the device loop could only exit on
`h->stop && h->gain <= 0.0`, waiting for the fade-out to *arrive*, which
is what keeps a quit from popping — and that waiting assumes the card is
consuming frames.  With another program holding it, `snd_pcm_writei`
blocks, the fade never advances, the loop never leaves.  So `host.c` has
two stops now: `halt` breaks unconditionally, `snd_pcm_drop`s instead of
`drain`ing, and — because a flag cannot reach a thread blocked inside
`writei` — calls the drop *from the stopping thread* to end the wait.  A
click on the way out is the right trade against a core file.  Quitting
at ten moments of startup went from eight crashes in ten to none.

**A loop that dragged its voices.**  The C engine closes its own loop
between blocks: it moves `position` back and tells Python nothing, so
`on_seek` never fired and the `LazyPerformer` — which only ever goes
forward — went on answering with the values from the *end* of the loop
for the whole next pass.  The clock going backwards is the only
announcement there is, and the housekeeping thread now watches for it.
That fix cost what it fixed: a seek replays the score silently from the
top, measured at 19 ms at bar sixty-five, and a loop paid it every wrap.
But a seek is a pure function of the past, so its answer can be kept —
`LazyPerformer.snapshot`/`restore`, refused whenever the stream has
grown since, because a performance quietly disagreeing with its own
score is far worse than the seek it saves.  Wraps went from ~9 ms to
0.06.  The test that matters does not measure: it drives two performers
identically, one restoring and one seeking, and requires the same state
*and the same subsequent changes*.

### What the reports were actually about

Six of the twelve were **a refusal naming the wrong reason**, and each
looked like a broken editor:

* `listen` reported success while `Workbench.listen` silently declined —
  a bank whose payload has no `FromMIDI` instance cannot be handed a
  note however much you want it to be.  No sound, and no reason.
* `canvas` said *"this file draws nothing"* about a file that draws a
  lantern, when the truth was that the window could not show one yet.
  It now tells three cases apart, because a canvas still compiling is a
  fact about the clock and not about the program.
* The status line showed the palette's *"29 of 29"* after every command,
  hiding its answer.  You pressed `seek`, it worked, and the line said
  nothing had happened.
* `play` was advertised as `Space` in a text editor, which is either a
  shortcut that never fires or an editor you cannot type a space into.
  Eleven shortcuts were advertised and two implemented; they are matched
  against the key each command *publishes* now, so the list cannot
  advertise one that does nothing.

**And one was a design error, not a bug.**  `find foo` is what a person
types; the palette wanted `find`, Return, `foo`, Return.  Henri worked
the rule out himself after a long, frustrating stretch of concluding the
build was stale — and the fix was one line: a space does what Return
does, except inside a `Text`, where `find foo bar` has to be able to
look for two words.  Every test drove the protocol that had just been
written, which is exactly why none of them found it.  A harness built
from an implementation can only find broken things, never missing ones.

**Two pairs had to be read together.**  `hide` clears every scrap of the
last question and `show` cleared none of it — once inside the palette,
where backspace stopped backspacing, and once across the wire, where a
reopened `open` was handed the directory you had walked into instead of
the one you are in.  Both were written weeks apart from their partners
and neither is wrong on its own line.

### The window earns the widgets

Margin knobs drag, and a click at 25% of a fader gives 24 of 0…100 —
turning it and typing the number are the same act, which was acceptance
clause 4.  Banks draw a box and `held/voices`: `voices 6` is in the text
already and a window repeating it would be decoration, but that four of
them are sounding *now* is what the text cannot say.  A piano appears
only when asked for, takes the keyboard when drawn or clicked, and is
drawn **grey when nothing will hear it** — a control that does nothing
and looks exactly like one that works is how an evening goes into
deciding whether the synth is broken.

`open` and `steal` share a file dialog whose whole design fell out of
three corrections: a directory is a *step* and a file is the answer;
`..` reads `../` at every depth while the query it makes is what stacks;
and the file you are in is *marked*, not selected, so the list shows
where you are and the first letter typed is a new name.  `steal` greys
what is taken and refuses it — overwriting is not something a name box
should do by accident, and one that could would be a delete wearing a
friendlier word.  The greying is a courtesy; the check is the guarantee.

**The canvas came last and cost almost nothing**, which is the point.
`gestate-panel` already turns a substrate into a display list and paints
it for the plugin; the editor reads the same three shapes off a channel
of its own and calls the same painter.  A second painter would be a
second set of rounding decisions and the two windows would disagree
about somebody's artwork.  It has its own channel because a substrate
animates while the furniture beside it changes when a command runs —
carrying them together would push every knob across the boundary sixty
times a second to move one dot.

### Retirement

`audiopygame.py` went first, with its 151 tests.  The `tkinter` `Editor`
followed — 640 lines, its `main`, and five smoke tests — the day
`shell/editor` did all four of the things it did.  What made that cost
nothing was decided long before either existed: **two halves, and only
one of them is a GUI.**  Nothing above the window ever imported a
toolkit, so replacing the window changed not one line of the half that
is tested.  `audioeditor.py` is the model now, and `python -m
gestate.workbench` is the way in.

The lesson worth carrying is the cheapest one: **use the thing the naive
way before calling it done.**  Type the whole line.  Click the obvious
place.  Every defect above was one honest sentence or one keystroke away
from obvious, and a person found all of them.

## The editor grows a vocabulary, and gets a colour

A day of Henri asking for one thing after another, and the pattern from
the last entry held exactly: **every defect in this session was found by
a person using the editor, and not one by a test.**  The suites went on
passing through all of them.

`command.ges` went from twenty-nine verbs to forty-five.  `fits` asks
what could stand where a type is wanted; `template` pastes one of the
language's ideas; `symbol` opens a lettered grid for the punctuation a
Finnish layout hides; `fmtAll`/`fmt`, `inferAll`/`infer`, `exportClap`,
`exportWav`, `exportWavAt`, `midiOn`/`midiOff`, `overwrite`.  Each is a
declaration with a type and a sentence, so each appeared in the list by
being written — which is the property that made adding twelve of them
cost nothing but the work itself.

**Four argument types were added and each earned its place the same
way.**  `Template`, `Device`, `Symbol` and `Answer` exist so that a list
can appear: the rule `Named` and `Path` already followed, which is that
the *type* is what lets the view ask.  A type qualifies when there is a
small knowable set of its inhabitants and the model is the one that can
name them.

### What a person found that two thousand tests did not

* **`Tab` was still a tab**, for seven hours.  `gestate/editor.py` built
  the `cdylib` only `if not so.exists()` — so every Rust edit since the
  library was last deleted had been invisible, and the binding I had
  "verified" was verified against source nobody was running.  The worst
  shape a defect can have: everything works, nothing is reported, and
  the thing you just changed is not in the room.  `_stale` now compares
  the library's mtime against every `.rs` and `Cargo.toml` under
  `shell/editor` and `shell/panel`.
* **`exportWav` refused to backspace.**  The name proposal fired on
  every `wants` with an empty query, so backspace emptied the box and
  the model filled it straight back in — and backspace-on-empty is how
  you step *out* of a question.  Fixed twice: once by proposing only
  once per question, and then properly by not typing into the box at
  all.  A proposal is a row in the list, marked the way `open` marks
  the file you are in.
* **`template` pasted twice** on a second Return, because Return on a
  finished call means *again* — right for `find`, and for a paste it is
  a second copy under the first.  Commands can now say they are
  finished, and a cancel of any kind takes the paste back.
* **The colours did not show.**  `Editor.changed()` answers *has it
  moved since I last asked*, which on a freshly opened file is `False`:
  the text arrived before anyone asked.  The line cache filled only on
  a change, so it stayed empty until the first keystroke and the file
  drew in plain ink.  Colouring that appears only once you type reads as
  colouring that is broken.
* **A knob the sound never reaches was drawn as nothing at all**, which
  reads as the editor having lost the line rather than the program
  having ignored it.  Now drawn with a red ✗.
* **A malformed file could not be saved.**  `apply` raised *before*
  writing when nothing was playing, so you could fix the syntax error,
  press Ctrl-S, and watch the fix go nowhere.  An editor that will not
  save is not an editor, whatever else is wrong.

The first and the last of those are the same lesson from two directions:
I verified the Tab binding against a stale artifact, and I verified the
colouring by feeding the painter its own input by hand.  Both times the
harness was built from the implementation, so it could only find broken
things and never missing ones.

### Bars count from zero

They counted from one, which is what a score on paper does and is
defensible in a tool for players.  It is wrong in this one: gestate
counts ticks, samples, voices and list indices from zero, and an
interface that alone said *bar 1* for the first bar made the reader do
arithmetic to cross between the program and the window.  Henri's
sentence was that he had built the whole program to one rule and found
the interface breaking it.

Lines stay 1-based and that is not an inconsistency.  They are a *text*
coordinate, every editor and every compiler message counts them from
one, and matching the outside world matters more there than matching
the inside.

### Syntax colouring, and the measurement that paid for it

`spec/workbench.md` deferred it because it "needs the parser to survive
a broken file".  It needs the **lexer**, and that has always been total:
`sound = ((` and an unterminated string both tokenize.  The blocker was
real about the wrong component.

**Colouring here is line-local, and that is checkable rather than
assumed.**  Tokenising `lantern.ges` whole and line by line gives the
same 996 tokens; the only cross-line state is `INDENT`/`DEDENT`, and
layout carries no colour.  So the cache is keyed on a line's own text, a
keystroke re-lexes one line at 37µs, and a scroll is cache hits.  Only
the visible rows are painted and only they cross the wire — the same
argument `view.rs` opens with about the rope.

**One lexer, one truth.**  A lexer in Rust would have been faster and
would have been a second front end that could disagree with the
compiler, which is the root cause `spec/comments.md` is written about.
The model tokenises with `syntax.tokenize` and sends `paint` rows; the
window reads runs and never decides what anything is.

And measuring it turned up something nine times larger than itself:
**`vocabulary()` re-parsed `command.ges` on every poll** — 650µs of a
two-millisecond budget, spent re-deriving a file that cannot change
while the process runs.  Its docstring said this was cheap.  It is
keyed on the file's mtime now, so *derived, never maintained* stays
true — touch the file and the next poll re-reads it — and the steady
poll went from 781µs before colouring existed to 99µs with it.

### The formatter stopped editing comments

Two defects, both found by using `fmt`.  The tokenizer stripped both
ends of a comment body, so `# like this` came back as `#like this`: a
formatter may move a comment, it may not edit one.  And blank lines
between declarations were dropped entirely, which rewrote every file
into one wall — the grouping is a decision somebody made about their
own program and nothing in the tree could reconstruct it.  One blank
survives wherever one or more was left, measured from source spans, and
the result is idempotent.

### Documentation rot, and a test for it

`test_manual.py` runs every gestate *snippet* and `test_courses.py`
builds every *example*, so the language in the prose cannot drift.  The
shell lines around them had no such check and had drifted badly: seven
references to `gestate.audiopygame`, a module deleted with the pygame
editor, three of them the second command of a lesson; two more CLIs
retired into a message that the guides went on teaching; and `--watch`,
the working method all four course guides describe, existing on nothing.

`test/test_doc_commands.py` checks every `python -m gestate.X` in
`doc/` and both READMEs: the module exists, it has a command line that
is not retired, every long flag it passes is one `--help` lists, and
every `examples/…` path is really there.  Fifty-five cases in half a
second, because it imports and asks for help rather than rendering
anything.


## The canvas lost its hands — a post-mortem

The canvas stopped answering to a drag, and it took a day and a half for
anyone to notice.  `lantern.ges` draws two faders and promises that
pulling one opens the filter; pulling one moved the caret in the text
hidden behind the picture.  The feature had worked since the initial
commit.  This entry is the archaeology, the five whys, and what the
answer says about how this project is led — because the interesting
failure is not in the code.  Registered as fixme.md **F101**; fixed the
day it was found.

### What happened, mechanically

Commit `71b90af` ("vastly improved editor coming") deleted
`audiopygame.py`, 3458 lines, and `test_audiopygame.py`, 2305 lines.
Three lines of the deleted event loop were the entire implementation of
canvas input: a click in canvas mode became `touch("press", …)`, motion
with the button down `"drag"`, release `"release"`.  The Rust shell
that replaced the window was built to `spec/workbench.md` — written in
the same commit — and implemented its gesture list faithfully:
`command`, `filter`, `wants`, `asked`, `turn`, `note`, `edited`,
`state`.  Eight verbs, flat and few, and no `touch`.  Everything below
the seam survived intact: `Workbench.touch` waited in
`audioeditor.py`, `Substrate.touch` in `gui.py` still grabbed on press
and clamped to the element's extent, and thirty-six tests in
`test_substrate.py` kept passing.  The suite was green the whole time
the feature was gone.

### Five whys

1. *Why doesn't the canvas respond?*  Nothing translates the shell's
   mouse events into touch gestures — no canvas branch in the mouse
   handling, no `Touch` variant, no `touch` verb in `session.act`.
2. *Why is the wiring missing?*  The only copy of it lived in
   `audiopygame.py`'s event loop, and the rewrite deleted the file and
   built to a spec instead.
3. *Why did the spec omit canvas input?*  Its inventory was drawn from
   what the model **publishes** — knobs, banks, transport, commands —
   and each of those got its verb.  A touch target is not published
   furniture: it is declared *inside the program on the canvas*
   (`onTouchY cutoff (rect …)`).  Walking the model's surface can never
   find it.
4. *Why did nothing object?*  The only tests of the wiring were in
   `test_audiopygame.py` and died in the same commit as the wiring.
   The surviving tests exercise the component below the seam.  And
   nobody dragged a canvas fader for a day — editor development
   exercises text, commands, knobs, piano, which is why exactly those
   got their verbs.
5. *Why could a feature fall out of a rewrite with no artifact
   objecting?*  **Knowledge of the feature existed in one copy — the
   implementation being deleted.**  The rewrite's method was: spec the
   new boundary, build to it, delete the old code with its tests.  No
   implementation-independent statement of the old view's obligations
   existed for the deletion to be checked against.

### Where the conventions failed, and where they held

This registry system — `fixme.md` for code against spec, `errata.md`
for spec against paper — assumes a defect is a *disagreement between
two artifacts*.  Here the two artifacts agreed: the new spec omitted
touch and the new code omitted touch, in perfect accord.  **When spec
and implementation agree in an omission, neither register fires.**  The
disagreement that did exist was between two specs — `substrate.md`
promises `onTouchX`/`onTouchY`, `workbench.md`'s boundary could not
carry a touch — and no register watches that seam.

The journal itself failed more quietly.  The lesson was *already in
this file*, twice: "the harness was built from the implementation, so
it could only find broken things and never missing ones", written about
the Tab binding; "what a person found that two thousand tests did not".
Recording a lesson as narrative does not change behaviour.  The one
lesson in this file that stuck is the one that became a test
(`test_doc_commands.py`).  **A lesson is closed by a mechanism, not a
paragraph.**

And the project's founding rule — *do not build what nothing needs* —
has a blind spot at replacement time.  Canvas touch **had** callers:
every `onTouchY` in `examples/audio`.  But they are programs, not
call sites in the tree; an inventory shaped like "who calls this?"
greps past them.  A language feature is a contract on every host that
runs the language, and the examples are its callers.

### What enforces it now

* `touch(kind, x, y)` is in `spec/workbench.md`'s gesture list, so the
  contract stopped being wrong.
* Seam tests at the verb protocol: `test_session.py` proves the verb
  reaches the bench, `test_audioeditor.py` proves a touch on a real
  substrate moves the channel it names.  The verb protocol is the
  boundary contract, so these survive any future rewrite of the view —
  they are the conformance suite the next frontend must pass.
* The deletion protocol, stated here as the rule it should have been:
  **a deleted file's tests are a checklist.**  Each one either moves up
  to a test at a surviving seam or is retired on purpose, in the commit
  that deletes it.  `71b90af` retired 2305 lines of tests silently; two
  of them were the only guard this feature had.

The general form, for the record: the danger of a rewrite is not the
code you rewrite, it is the obligations recorded nowhere but in the
code you delete.  Inventory a boundary from *both* sides — what the
model publishes, and what programs demand of the view — because the
second list is the one a model-side spec cannot see.


## The canvas found its centre

A substrate's origin now lands **in the middle of the pane**, in both
hosts.  The walk was always origin-relative — `_flatten` from `cx = cy
= 0`, every element placed by its centre — and where the origin lands
was the host's to say; both hosts said *the corner*, so a beginner's
first `rect 40 40 c` showed its bottom-right quarter and every shipped
example opened with a compensating `moveXY 150 150`.  The first user
gestate ever had met that on their first canvas, which is what promoted
it from wart to defect.

**The move is one decision in five places, taken together**: the
editor shell offsets the painted shapes by half the window and
subtracts the same offset from every touch (one number, two
directions, so the picture and the hand cannot disagree);
`Panel::canvas_origin` answers the middle of what the toolbar leaves;
seven examples lost their compensation — five dropped a root `moveXY`,
and `bounce`/`chain` had their *worlds* recentred, which made them
shorter (a centred backdrop is a bare `Rect`).  The reference walk and
`touches` stay at the origin: the fixtures pin the tree's own geometry
with no host in the room, and now read as what they are — items
straddling zero, a picture placed by its centre awaiting a host to say
where the centre is.

Trying this in one place instead of five was already a recorded
mistake: centring a host over programs that still carried their
`moveXY` double-counted the move.  What made the coordinated form safe
is a day old: `test_panel_fixtures.py` regenerates what the Rust suite
reads, so the fixtures could not stay behind, and the parity tests
held both hosts to the same reading throughout.  The change never had
a moment where green lied.

Found while converting `bounce` and `chain`: **their pointer half is
orphaned.**  They fold over raw `Press`/`Move` events, and nothing in
the editor injects one — `Substrate.tick` sends `Tick` and a touch
writes an attachment's channel; the raw-event vocabulary's only living
callers are `test_gui.py`'s headless `scenes`.  That is F101's shape
(an affordance whose host was deleted with pygame), and it reopens the
question of whether the raw-event canvas belongs to the language at
all now that the built vocabulary is attachments.  Not decided here;
recorded so it is a decision rather than a discovery.

## The day the transcripts earned their keep

2026-08-13, one day, and the longest entry-per-hour stretch this
project has had: `fixme.md` F104 through F127 were filed and all but
three resolved, nearly every one found by Henri playing the workbench
and pinned by a session transcript.  The full stories are in the
entries; what belongs here is what the day *taught*.

**The transcript is the oracle the host layer was missing** — in
practice, if not in the spec's sense.  F115 was diagnosed from a `#!`
note two lines above the failing answer; F122 was caught in the
margins of a transcript recorded to verify F121; F126 — a real
crossfade crash in the engine — fell out of a jog session recorded to
test a margin word.  The pattern held so well that `doc/manual.md`
grew §11 teaching users to reach for `transcript` first, and the
replay (`gestate.sessionlog`) became the regression test for two of
the fixes.  Its known limits are recorded where they bit: the
recording restarts on a file switch (the steps that *led* to a switch
are exactly what a reproduction loses), it cannot drive bank switches
(no live instrument under replay), and it cannot see the margin.

**Channel counts stopped being a restart-shaped hole.**  The F109
retirement machinery — the switch is immediate, the teardown is a
reaper thread, the new start waits for the sound card off-loop — is
also what closed the old roadmap item about changing the channel
count in a running instrument: the driver restarts when the output
frame or the control block outgrows the player, and F126 fixed the
crossfade for the shrinking case (the leaving engine's node ids now
translate by channel name, the identity a control actually has).

**The margin learned two words for silence**, both Henri's:
"disconnected" (the graph's answer beside the text's declaration —
the knob-cross split, applied to banks) and "away" (a scored line
MIDI has displaced).  The extractor's own pruning is what makes the
first honest: a bank `sound` does not reach has no channels in the
graph at all.

**And the editor got its exterior**: `WM_CLASS=gestate`, a drawn
`_NET_WM_ICON`, and `--desktop` writing the entry GNOME needs —
plus detectable autorepeat, the undo barrier with the unsaved-changes
warning, the equator-and-span panel flip, and the say-when-you-are-
done family.  `spec/workbench.md` was rewritten the same day, every
law with the defect that paid for it as its receipt.

## The canvas walks over crust — and the clock wore three masks

2026-08-14, one day, fourteen commits, and the roadmap's "a session of
its own, not an evening" estimate was wrong in the right direction:
the whole move landed the same afternoon it was designed.  What
belongs here is the story the commits tell in pieces, and what the
day taught.

**The morning was small and deliberate.**  A hamburger — one cell,
one glyph, half a cell of air, no ground — whose whole job is to be
the door a stranger can find into the palette, teaching `Ctrl-K` in
the bar while it holds the list open.  Inert mode: `.txt` and `.md`
open as notes beside the music, nothing compiles, saving is all
applying means, and the window wears **[inert]** in the warm colour
so the quiet reads as a mode rather than as breakage.  And the two
transcript survivals: the recording now crosses a file switch
(`_carry` hands the log over, the swap rides as one edit step), and
the header carries the text it began on — `#: began <fingerprint>`
always, the full text as `#.` rows when the file was never written.
Both paid for themselves before dark; see below.

**Then the lagcheck, and the week's one performance sentence.**  The
lantern canvas measured exactly as predicted headless (9.41 ms
against the recorded 9.40) and *nothing like it* in the editor — and
the cause unmasked three times before it stood still.  First mask:
the gesture loop napped between cheap passes, the core fell to
0.7 GHz, and every Python cost tripled — `furniture`, unrelated code,
moved 3.4 → 1.2 ms in the same runs, which was the tell.  Second: the
canvas throttle's rest after each walk was where the core cooled, so
the throttle *bought its own cost* — `CANVAS_SHARE` went 2 → 1 and
the lantern went 5.8 → ~38 Hz.  Third, days of fixes later: with the
model's walk retired the process was so light the cores parked at
500–600 MHz, below the idle baseline, and F103's swinging labels
juddered while lantern looked excellent — same numbers, different
animation.  The claim `uclamp_min` makes is correct and, on this
machine, inert: `intel_pstate` in active mode never consults the
scheduler, and the real owner of the clock turned out to be
`power-profiles-daemon`'s EPP, idling on `balance_power`.  One
`powerprofilesctl set performance` later the mask came off for good.
**On this governor, the cost of the work is set by how much other
work there is** — three defects, one sentence, and
`spec/performance.md` §4 holds every number.

**The move itself went in the order F101 demands, and that order paid
twice.**  The vocabulary first, in the spec, before any window
learned a verb: coordinates never cross the wire; meanings do.
`touched <name> <value>` out, `reading <name> <value>` back, and the
payload — serialized program, entry, the fourteen carried tags, the
channels with their values — through a door of its own that moves on
rebuild, never on keystrokes.  The first dividend: `boxtouch`,
reserved in B3 before any window spoke it, was *retired unspoken* — a
box under crust is more of the same walk in the same namespace.
Reserving before speaking made the retirement free.  The second: the
transcript can finally hold a canvas gesture, because a named write
replays against the reference machine and a coordinate never could.

**One driver, two windows.**  The Walker is
`gestate_panel::canvas::Canvas` — the CLAP plugin's own machinery,
parity-pinned against `gui.py` on lantern itself — wearing the
workbench's vocabulary.  The window animates at its own frame rate
(240 drawn, 0 idle, where the loop's best had been 38 Hz), the
gesture loop's whole canvas frame is now one `observe` and a string
compare, and Henri's verdict landed the same hour: *faster than the
plugin*.  Two seams surfaced within minutes of a person using it,
both foreseen in shape: the walked machine had no frame clock (the
payload now carries `Tick`'s tag and the Canvas grew `step(pulse)` —
the CLAP plugin has the same gap, its adoption ready), and `observe`
run at loop pace made the meter flicker (`READ_EVERY = 1/30`: the
read rate *is* the meter's window).

**The transcripts earned their keep again, one survival deep.**
Henri could not open lantern from a fresh untitled — and
`lantern-session.ges`, recorded on an unwritten file, replayable only
because of the morning's base-text header, showed the whole failure
in three steps: `ask open` answering 0 rows, the typed name resolving
to a phantom, three times.  With his Tab observation ("it spindles
the path into something that only looks like lantern.ges") the
diagnosis was complete: completion wrote a row's bare name over the
walk, and the listing could not see past one directory.  Both fixed
the same evening — Tab keeps the query's own head, and `_below`
finds beneath the walk, breadth-first, bounded, build-droppings
skipped, deep rows wearing their path so what is picked is what is
shown.  An exactly-named directory now outranks a fuzzy file, which
was F129.  And the chase flushed a third thing out of the grass:
F124's "flake under load" fails *deterministically* in a full suite
run on a quiet machine and passes alone — an order-dependence, not a
margin, finally a specimen that holds still.

What is deliberately left: the model still compiles the substrate on
the reference machine (headless runs, tests and canvases outside
crust's pure core keep the shapes wire); `pace`'s BUSY-while-showing
is vestigial now that the loop has nothing to warm, undecided; and B2
content boxes land next on a floor where a picture costs the gesture
loop nothing.

## The scope arc — the workbench learns to see

2026-08-14, the day's second act (the first is the entry above), and
the roadmap's oldest standing wish: *you can hear that a filter is
wrong and you cannot see where it went wrong.*  By evening you can
see.

**The buffer was already built, which the design study was for.**  The
probe section had planned a new block-of-samples slot with three
callers; the study found the slot living in `spec/delaylines.md` all
along — a scope is a delay line's ring the host may read.  So the
vertical reused the line's answer at every stop: the oracle body in
`signal.ges`, the ring in `%State`, `zero`/`migrate`/pack/unpack, and
one new thing only — publication, a generated `read_scope_<i>` per
scope so no offsets cross the boundary.  The native window read back
bit-exact against the oracle on the first run.

**Two readers, one node.**  `scope` downsamples the window by time,
max-absolute per bucket, because a scope that averages away a click
lies; `spectro` transforms it by frequency — a hand-rolled Hann
radix-2 FFT, ~3 ms, pure function, tested by putting a sine in its
bin — into 64 log-spaced bars.  The flavor rides third on the
furniture verb, so an old window draws every window as a scope.

**The display went where Henri pointed: the content box.**  The trace
stands under its own declaration — the knob's placement rule grown a
height — through the same slots walk the trouble boxes ride, dots in
the caret's blue, bars in the sound's green, stacked when two scopes
share a line.  The box follows the *text* (moves at the keystroke,
dies at the keystroke, stands before any save) while the trace
follows the *engine* — each honest about which truth it carries,
learned the hard way when the first cut read the disk and an
audition could not raise its own scope.

**And the drop became one word.**  Henri weighed `cover` (a covering
definition — name-shadowing wearing a convenience) against `sink`
and picked `sink`: one meaning the graph did not have and needed,
*keep this alive beside the sound*.  `audiovoices._sinks` rewrites
the line 1:1 so positions never move — `_blank`'s own promise —
extraction roots every sink beside `sound`, and the box stands on
the `sink` line, because where the question was written is where the
answer belongs.  The probing loop now reads: hear something wrong,
append `sink scope "x" suspect`, Ctrl-S, look, delete the line.

**What the flashlight found.**  Probing nightdrive, the pad kept
dying — and the scope was innocent: measured through the pad's own
window, *every* apply drops the notes it crosses, a comment-only
edit included.  Long holds die audibly, short notes re-onset before
anyone hears the hole, and probing is applying over and over.  That
is F131, the resumed performer re-emitting no gate for a note
sounding across the seam, and it was invisible until nightdrive —
written that same morning — became the first piece with bar-long
holds.  A diagnostic instrument's first catch was the environment
itself.

Around the arc, the day also swept: the dialog finds what you can
name (F129/F130, with Tab no longer wiping the walk), F124's
"flake" caught as the kernel's coarse clock and fixed with the
racily-clean rule, F127's constraint refusals learning the author's
language and their own line, boxes clipped at the fold and the
palette's page going where the room is (F132/F133), and `line 250`
— the fiftieth verb — taking the margin's own coordinate back.

## The box arc — a picture with a row for an anchor

2026-08-14, the day's third act.  B2 stood in the roadmap as a
display list crossing on its own channel; the crust move had already
made that design obsolete, and what shipped is simpler than what was
written: **the box is the window's own walk**, laid out in the box's
granted height, blitted with the band's edges as the clip, and the
wire owes one verb — `canvas <line> <key>` — because the picture
never crosses at all.  B3 followed the same afternoon for the price
the retired vocabulary predicted: a touch in a box is a `touched`
like any other, no id, no coordinates, and the grab remembers which
band took it.

**The ask was revised three times in one day, each time by Henri
using it within the hour.**  Always-on under the declaration lasted
until sad_lantern.png showed the picture severing its own
declaration from its body.  The `canvas` line with `sink`'s manners
replaced it — the box stands where the question is written, deleting
the line takes it — and `canvas <expr>` first rewrote to
`substrate = <expr>`, which chopin-session.ges caught refusing its
very first real use with a duplicate-declaration complaint about a
name the author never wrote twice.  Now every expression ask is its
own hidden `__canvas_<k>__`, compiled as one more substrate with its
entry pointed at the hidden name (tried as `Sig Sub`, then under
`constSig`, so a still picture asks with no lift written); the
payload grew `box` sections, the window keeps a walker per key, and
readings broadcast to all of them.  Multiple canvas — sink's
semantics, where several asks are normal, which is the model
Henri's hands assumed before the code did.

**What the arc taught, in defects.**  Readings gated on the canvas
view froze every fader in the box — the traces' whatever-shows
clause was the answer, for the traces' own reason.  Centring the
walk in the fold-clipped remainder slid chopin's disc as the box
crossed the fold — the layout is the box's full height, the fold
crops only the blit.  Centring in the text area sat the picture off
the full-width band the eye sees — a picture is not code either.
And the `canvas` line reaching a raw parser cost lantern its knobs
("no parameters"), which turned out to be `sink`'s bug too, standing
since it shipped, unnoticed because every sinked example had no
knobs to lose: `blanked` now rewrites both words first, its stated
job all along.  Jumps learned to land with air (`JUMP_AIR`) after
`line 272` twice answered with the target's box exactly out of
sight.

**examples/audio/chopin.ges is the demo** — the E minor prelude
simplified, chords sinking a semitone at a time under the sighing
line, a disc breathing the output's peak and eight hammer lamps on
the probes.  The same day closed F103 with the reproduction its
entry demanded (`_unifies` entering `unifying()` outside
`_FRONT_END` against the old shared store — 7 failures on demand,
zero under `threading.local`), narrowed the loop's fast pace to the
canvas it still animates, and pinned the spectrograms to the README.

## The notes arc — a take, and the line that wrote it

2026-08-14, the day's fourth act, and the first slice of B4.  The
roadmap's score editor was always "the star", and the star is a
rewriting instrument: drag a note and the text changes.  What shipped
is the half before that — a box that only *reads* — and the reason is
the one the arc kept proving all day: every affordance in this editor
has been fixed by Henri using it within the hour, and there is nothing
to use until something draws.  A read-only roll exercises the take,
the provenance, the height and the focus, and it can be looked at.

**The spec was written first and revised from the code after**, which
is the reverse of `spec/workbench.md`'s order and was deliberate both
times: the mechanism was already standing, so what remained were
decisions, and a decision written down can be argued with before it
hard-codes anything.  Four passages carry an ***as built*** mark where
the building disagreed with the design.

**What it decided.**  A chancy score has no notes, it has takes, so
the box renders the take the session's seed names and says which in
its label — `seed` and `reroll` already existed and no new vocabulary
was needed.  A note that traces to bytes is *span ink*: bright,
clickable, and what a future drag will apply to.  A note that exists
only in this take is *take ink*: it wears the span of the generator
that drew it, draws dimmer, and its future drag will be refused with
a sentence naming the generator's line, because dragging it would be
asking a gesture to do programming.  A box on a sub-expression is its
own take — seeds split by position — which is stated plainly rather
than hidden, and waits on ariadne's paths to become the piece's.

**Provenance lives in the view, and that is the whole design.**  The
event tuple is the currency of two machines held in parity and only a
picture wants spans, so nothing was threaded through either engine.
The box descends the viewed expression's own parse tree, wrapping
each written leaf in `tagAll`, and one `spreadTo` of the rebuild
yields every event carrying the leaf that made it.  Both walks are
new in `music.ges`; `spreadTo` is bounded by fuel and a window, so an
endless `cycle` is welcome and a zero-width one says it was cut
instead of hanging the window that asked — the sauna specimen's
lesson spent as a bound rather than relearned.  `Notable`
(`noteKey`/`noteVel`, beside `FromMIDI`) is how a payload is read,
because the field order the obvious reading trusts is a convention
the type checker never sees.

**Four traps, each found by it failing.**  Slicing a leaf's text out
between its span's ends looked obvious and swallowed the file: a
`VPrefix` carries a defaulted span, so `'(H 60 100)` sliced from
column zero.  The formatter prints a node back and is idempotent, so
spans were demoted to one job — the *line*, taken from atoms, which
are the parts whose positions survive fixity resolution.  `>>=`, `'`
and `++` are class methods, so an unannotated generated definition
collects dictionaries, becomes arity two, and dies at run time with
"too few args" — hence a signed `tagAll` and an `at 0` anchor.  An
assigned part is a `[: Void :]` with no payload left to read, and the
modern idiom assigns *inside* the part, so the box generates
unassigned twins (`voices.B e` is `' e`) transitively; refusing that
would have been refusing the idiom the newest examples teach.  And a
generated picture is not free-form: no unary minus, so a coordinate
left of centre is `(0 - 192)`; one `Over` per note is one parenthesis
per note, so chopin's hundred and forty overflowed the *parser* and
the notes travel as a list folded by a small recursion, `scoped.ges`'s
own shape.

**F136 came out of it**, and is the kind this project collects: a
lambda whose parameter is a tuple pattern dispatches a constrained
call against the wrong instance, silently.  `noteKey` picked `Notable
Int` off the tuple's first field and every note drew as its own
payload while the checker reported the right types throughout.  Four
lines reproduce it; the box takes the event whole and opens it with
`case`, and the comment names the entry so the workaround dies with
the bug.

**Two of the roadmap's four open questions are answered by it.**  What
a chancy score shows: the take, labelled with its seed — the lean the
roadmap already had, now built and lived with.  Who says how tall: the
view grants and the content fits, which `spec/workbench.md` had
decided when the row table shipped and the roadmap had simply never
been told.  The other two stay open and belong to the editing half —
whether every musical gesture is a span rewrite, and what owns the
keyboard when a box can be typed into.  The read-only box needed no
answer to either: its one gesture is a press that moves the caret,
and it writes nothing.

**Two examples show it.**  `noted.ges` is four bars where you can
count the notes — a written left hand, a right hand that rolls one
die a bar, and three asks reading each hand and the piece.
`minute.ges` is the same box on a whole arrangement: twenty-four bars
at 96 bpm, sixty seconds exactly, four parts entering and leaving, so
what the roll shows is *shape* — and `--report`, built the same day
for `spec/firstpiece.md`'s missing ears, reads the same form back as
numbers.  The picture and the meter agree about the same minute,
which is a good day's proof that both of them work.

## The day the save cycle was measured

2026-08-15.  Henri said *"compiling times are taking their toll"* and
the roadmap had nothing to say about it.  What follows is the whole of
that day, and its shape is one sentence: **nothing here was broken, and
nothing was watching.**

**Twelve seconds.**  `journal.md` records a rebuild at 400 ms when
stage 7.5 shipped — a real number, taken on `blip.ges`, still about
right for `blip.ges` today.  The pieces then grew fifteen times and
nobody measured again.  One save of `examples/audio/quartet.ges` in the
workbench, with every cache warm:

| phase | cost |
|---|---|
| `graph_of` → `pipeline.analyse` | 4.6 s |
| `graph_of` → assemble and extract | 1.1 s |
| `_place` → `_find_holes` | 2.4 s |
| `_load_substrate` | 0.5 s |
| `_load_from_midi` | 0.3 s |
| `clang -O2`, when the IR changed | ~3 s |
| **one save** | **~12 s** |

Every entry below came out of that table, or out of the instrument
built to keep it.

**Holes nobody wrote — 2.4 s.**  `typecheck.holes_in_source` ran its
own `_merge_prelude`, `desugar_program` and `infer_program`: no
analysis cache, no staged path, every prelude re-inferred — and
`_place` called it on every rebuild whether or not the file contained a
single `_`.  It asks `pipeline.analysed` now, a door beside `analyse`
that recalls and **never computes**, for a caller that wants the answer
only if it is free.  What lets it read a kept analysis is that a hole
survives elaboration and specialisation *carrying its type*, which
nothing had relied on before, so `test_pipeline.py` holds it two ways:
the cached answer equals the cold one, and `_analyse` replaced by
something that raises leaves the scan passing.  `fits_in_source` and
`signatures_in_source` had the same defect on the `?`/`Tab` path — 0.86
s → 0.03 and 0.21 → 0.004 — and the second is why `Analysis` grew a
`constraints` field: a signature offered without the context inference
put on it is one that would not compile if you accepted it.

**The seam that was never cut.**  The roadmap said the front end was
staged — the stack front holding the libraries' parse and inference,
a rebuild inferring only what the author wrote.  For the files anybody
works on it was not: `_analyse_staged` returned `None` in thirteen
microseconds for `quartet.ges`, `noted.ges` and `blip.ges`.  One
shadowed name turned the whole cache off, and all three assemblers
spelled the test the same wrong way — `if shadowed is prelude`.  Nine
of the forty-five examples paid it, over `bar` (four of them),
`chorus`, the type `Note`, `gain`, `pair`, `envAt`.  **The words a
piece is made of.**

The question is whether the head still *stands alone*, and renaming
does not decide it: a library name the program takes over moves on both
sides at once, binding and references together, so the head goes on
referring only to names it defines.  A `prelude.ges` name does not —
the head is left calling `__prelude_envAt__`, which nothing defines
until `merge` puts the program in front of it.  `prelude.stands_alone`
asks that.  Eight of the nine are staged now and `blip.ges` refuses for
a reason it can state; with the fronts warm, `noted.ges` 2.40 s → 1.24,
`spiral.ges` 2.35 → 1.27, `quartet.ges` 3.36 → 2.65.  The acceptance is
the staged path's own — same SC names, same types, same case tags —
now also held against a shadowing program, and `lantern.ges`, which
shadows `bar` and is therefore newly staged, exports byte-identically
to before.  That last check is the "two numberings in one program"
hazard asked on the artifact where it would show.

**`GESTATE_BUILD_TIME`, and being wrong in public.**  The frame side
has a stopwatch and two lag tools and consequently does not rot; the
build side had neither, which is exactly how 400 ms became twelve
seconds with two thousand tests passing.  `gestate/buildtime.py` is the
table above printed per rebuild — and it was wrong the day it was
switched on, which is the argument for it.  `substrate` read as the
largest phase of a start, 7.8 s on `chopin.ges`, and it was not: own
time comes off a per-thread stack, `pipeline._deep_stack` hands the
front end to a worker and joins it, so the analysis `_load_substrate`
was *waiting for* was counted twice — on its own line and inside the
phase waiting for it.  `lending`/`borrowing` carries the open phases
across the hand-off, and the same fact fixed `‖`, which was reading a
hand-off as concurrency.  A stopwatch that has never been wrong is a
stopwatch nobody has read.

**Then it found the rest by itself**, on one line of output:
`noted.ges` reported **eight** front ends for one start.

* The eighth re-analysed the text the first had.  `_KEEP_ANALYSED` was
  four — sized when a file had three assemblies — and score boxes had
  quietly made it eight, so the cache was evicting the file it was
  caching.  1.06 s to answer a question already answered.  Eight now,
  with the arithmetic written down and the cost measured rather than
  guessed: an `Analysis` of `quartet.ges` is 7.7 MB.
* Three more were one per `notes` ask: each roll spliced its own
  `__nb_*` definitions into the author's file and assembled a fresh
  200,000-character performance.  `scorebox.build_rolls` numbers them
  into one program, which is the shape `canvas <expr>` asks always had.
* Three more were one gui program per box.  `page_program` merges those
  too and `Substrate.several` compiles once, giving a view per entry
  over one machine — `serialize` crosses only what an entry reaches, so
  a box's payload stays the box's.

Both merges turn on the same hazard and it is worth naming twice: a
generated name reached from two asks is **not one definition**.
`_Descent.rebuild` carries the bank in force at the *reference*, so
`ground` reached from its own ask and from `score` are two bodies
wanting one `__nbd_ground__`; a box's hue table is its own roll's
banks.  Every generated name wears its box, and the acceptance is
equality — every box of `noted.ges` built together is the box built
alone, event for event and leaf for leaf, on the file whose asks
overlap.  A page also refuses per box: one ask that will not compile is
retried alone rather than blanking the page.

**Two more, once the question became "what else is doing nothing?"**

* **`SLPVectorizerPass` was 56% of the optimiser** — 1.0 s of 1.8 on
  `quartet.ges`, by `-ftime-report` — and `-fno-slp-vectorize` gives a
  **bit-identical** object.  That is not luck: this emitter writes no
  fast-math flags, so nothing may reorder a floating-point sum, and
  superword parallelism across a graph of scalar step functions is
  allowed almost nothing.  It spent a second looking.  quartet 2.7 s →
  1.7, chopin 0.53 → 0.41, the small files unchanged, render speed
  unchanged within the noise of repeated runs.
* **The library was being renamed on every keystroke.**  A program that
  takes over a library name has that binding moved aside
  (`shadow_libraries`), which is a token walk over the *library* — 188
  thousand characters for a piece, 0.54 s — and it ran again on every
  save.  The program changes every keystroke; the *renaming* changes
  about once a session, so it is now keyed on `(library, renames)` and
  hits.  `assemble_performance` on a changed `quartet.ges`: **1.22 s →
  0.44 s.**

Both are the same shape as everything above, which is why they are in
this entry rather than a later one: work done again for an answer that
had not changed, and work done at all for an answer that could not
change anything.

**Where it ended.**

| | start of day | end of day |
|---|---|---|
| a `quartet.ges` save | 12.0 s | ~2 s |
| a `noted.ges` start | 14.1 s | 4.6 s |
| front ends per `noted.ges` start | 8 | 3 |
| `clang` on `quartet.ges` | 3.0 s | 1.7 s |
| assembling `quartet.ges` | 1.2 s | 0.44 s |
| `Tab` — what fits here | 0.86 s | 0.03 s |
| `?` — the signature nobody wrote | 0.21 s | 0.004 s |

Thirteen commits, and not one of them made anything faster by making
it cleverer: every line of that table is work that was being done twice,
or done for a file that had not asked for it, or done again because
somebody had thrown the answer away.

**Measured and rejected: `clang -O1`.**  It looked like a free 1.3 s,
and the objects are bit-identical to `-O2` — no fast-math flags, so
LLVM will not reassociate.  It costs render speed instead: `lead.ges`
30× realtime → 16×, and `quartet` already renders at under 2×.  The
content-addressed `.so` store is the right answer on that side, and
the payload it compiles is already only what `sound` reaches: 656 nodes
and 436 functions of a 232,000-character program, emitted on demand
from the graph's nodes.

**What is left is in the roadmap**, and it is smaller than it looks:
about 0.2 s a front end of whole-module work that wants the seam moved
rather than tuned, and the fact that a file with a canvas is analysed
twice per save because the sound and the picture are different
assemblies.  The tuning half is spent — `expr._field_names` was worth
5%, not the 10% guessed, and it was measured by swapping the cache for
the old call in one process rather than by comparing two runs.

**The method, stated because it was the whole day**: every fix here was
found by an instrument, not by reading code — and the instrument was
found to be lying twice before it was believed.  "It feels slow" is not
a measurement; neither is a number nobody has checked the arithmetic
of.

## The day the oracles arrived

2026-08-15, second half.  The morning was spent making the save cycle
fast; the afternoon was spent on the thing that made the morning
possible, which is that **something could measure**.  Four instruments
came out of it, and every one of them found something on its first use.

### A played key, against the sound that comes out

The roadmap has carried this since stage 10: *"there is no obvious
oracle for 'a key was pressed and a sound came out'; finding one is
worth more than more care."*  Every defect in the live half had been
found by Henri playing a keyboard while two thousand tests passed, and
the reason was visible in the test files themselves —
`test_audiokeyboard.py` follows a keystroke as far as the *allocator*
and stops one step before sound; `test_audioeditor.py` follows the
bytes as far as the player and never asks what they say.

`test_playedsound.py` joins the two ends.  It drives the real
`Workbench` with a fake player, reads the float32 the driver wrote, and
asks the question nothing here could ask: **which note is that?**  The
ear is `audioperform.heard_note` — a Goertzel per candidate note, ten
lines and no dependency, beside the `_Meter` that hears *how loud* for
`--report`.  Its candidates are equal temperament from A440, and that
is the whole design: asking `keyHz` what it thinks 60 is would make the
oracle agree with the thing it is checking.  The strongest assertion in
the file needs no frequency at all — *an octave up is an octave up*.

**Checked against a broken instrument before it was believed**, because
an oracle that has never failed is a claim, not a test.  A
`Keyboard.press` a semitone out is heard as 61; a `Workbench.control`
answering 0.0 makes the capture silent.  Both fail, which are the two
defects it exists for: the wrong note, and no note.

### The schedule and the hand, and the first bite

`duet.ges` has claimed in its header since it was written that **a note
is the same thing whether a schedule or a hand decided it** — only
*when it is decided* differs.  The engine cannot tell; until now
neither could anything else, because the claim was checked at the
allocator, where it is nearly a tautology.

Checked as sound it was 0.084 apart and drifting, so the notes were
measured rather than argued about:

    scheduled  +0ms rms 0.0983 … +350ms rms 0.0294   decay 3.45/s
    hand       +0ms rms 0.1098 … +350ms rms 0.0621   decay 1.63/s

Same pitch in every window, different decay.  The envelope is
`exp(-rate·t)` while held and the bass is written at 3.5, which the
scheduled note reads back as 3.45 — but **1.63 is not a rate that
envelope can produce, and a sum of two of them is.**  The reed is the
other voice in that file and its rate is 0.6.  A keyboard plays every
bank that listens and `listening.get(bank, True)` means a bank nobody
has spoken about listens by default, so the hand was playing the reed
as well as the pluck.  With `lead` switched off: **0.000 apart, 3.45
per second.**

So the file's prose is true and now checked to three decimal places —
and the oracle's first catch was a wrong assumption in its own setup,
which is the sort of thing an ear is for.  The decay assertion has its
own line because the harmonic profile is normalised: the same note
through the same voice with a stale `gateAt` would sail past a
comparison of ratios and not past that one.

### The C host, and the seam that was nobody's

Writing the above turned up a gap worth naming: a fake player means
`_open_host` finds no card, so the *Python* driver renders and the C
loop — what a machine with a sound card actually runs — was on nobody's
path.  `test_audiohost.py` proves the C host renders what the engine
renders for a synth with no parameters; a key is the case it cannot
make, because a key arrives through the **control block**.

Both drivers now play the same key, sample for sample under 1e-6, with
`fade_in=False` — a session starting with the fader down so the card
does not pop is the one difference between them, and it is written down
now.  The mutation that says this covers new ground: with
`_push_controls` made a no-op the C host plays *nothing* and the join
fails, while the same mutation sails past every Python-driver section,
where the driver pulls its own controls.

### Sauna's six seconds

Henri's own observation — `examples/long/sauna.ges` spends six seconds
of its start in the score — and it came apart into three answers.

**A quadratic in the G-machine compiler, fixed.**
`_apply_n_bump_env(i, env)` rebuilt the whole environment i times, and
its callers bump by the number of arguments pushed so far, so a call of
k arguments asked for 0 + 1 + … + k rebuilds.  Bumping i times adds i.
`pipeline.compile` on sauna: **0.49 s → 0.25 s**, and every compile in
the project pays it.

**The same assembly is compiled twice a rebuild**, because
`pipeline.compile` has no cache the way `analyse` does — the score's
stream and the `FromMIDI` interpreter each ask and neither knows about
the other.  Sharing wants the distinction `Substrate.several` made
hours earlier: a `GmState` is a machine with a heap the caller runs, so
what two readers can share is the compiled code, not the state.

**And most of the six seconds is the GIL.**  `stream_root` is 1.31 s
warm on an idle machine.  Inside a start it reads six, because the
canvas, the score and the `FromMIDI` instances run on a side thread
while the main one runs the front end and the extraction — three
CPU-bound Python threads taking turns.  `GESTATE_BUILD_TIME` had been
saying so all along and nobody had read it that way: the phases sum to
14.7 s inside an 8.15 s start, and every one of them is marked `‖`.
The side thread wins only across `clang`, which releases the GIL.

### The `i64` hazard, met

Open since stage 7.4, with the measurement that made it worrying:
`drums` reaches 25.7% of the range.  It was real.  A counter of
`n * 3 + 1` leaves `i64` in forty samples, and the reference and the
engine then say **0.201 and 0.585** about the same program with nothing
anywhere to say why.

The check is in the *reference* and nowhere else, and that placement is
the design: the audio path may not pay a branch per integer operation,
while the reference is already a thousandth of real time and is the
definition of what a graph means.  So an overflowing program says so by
name at the instant it happens, rather than diverging by 2⁶⁴ and
arriving as a golden mismatch nobody can read.  It costs the reference
4%, it fires at **exactly the instant the two engines part company**,
and `drums` at 25.7% still renders — because a check that cried wolf is
one nobody leaves switched on.  What it cannot see is a program nobody
renders through the reference, and the docstring says so: an oracle,
not a guarantee.

### What the day was actually about

Every fix in the morning was found by an instrument rather than by
reading code, and twice the instrument was itself wrong and had to be
caught.  Every oracle in the afternoon found something on its first
use, and one of them found *itself*.  Between them that is the whole
method this project keeps writing down, arrived at again from both
ends: **being wrong has to be visible, and the thing that makes it
visible has to be checked against being wrong.**

## The evening the picture learned to be dragged

2026-08-15, third part.  The morning made the save cycle fast, the
afternoon recruited oracles, and the evening spent both on the thing
they were for: **the north star** — `spec/north_star.md`, a vertical
drag on span ink, one note, byte-exact — with two squirrels chased on
the way and one still loose at the end.

### The completion, which was meant to be a detour

`Tab` at a hole answered *what fits*.  Henri asked for it to write the
answer down as well, and to keep going: pick a name, get `sine _` with
the caret on the next hole, until nothing is near.  Five lines of
range, which is what a wrapped declaration takes.

The interesting part was not the writing but the four things the
writing was wrong about, and all four were found by *watching him use
it* — three recordings, read frame by frame.

**The text landed after the orders that talked about it.**  A
completion sends the document one way (`ged_set_text`) and the caret
another (an order), and the window collected the orders first — so
column 14 was measured against `foo = _`, clamped back to 7, and the
new text kept the wrong place.  That is the whole of `foo = (|length
_)` in the screenshot: an off-by-one in *time*, not in arithmetic.  The
oracle for it drives a real window and reports the caret at 17 instead
of 24, which is the same defect arrived at from the other side.

**What is typed now stands in the slot it fills.**  The prompt drew a
placeholder for every argument not yet taken *and* the query after all
of them: `complete <text> <filler> Int`, three fields for a command
that takes two.

**A jump moves the panel.**  F121's rule was asked when the list opened
and never again, so `goto` sent the caret under the equator and the
panel stayed on top of it.

**And the holes follow the text.**  They are found where the program
last *compiled*, and nothing carried them across an edit — press Return
above one and the margin says `_ : Int` beside a blank row while
`complete` answers "not on a hole" with the cursor on one.  They are
carried now the way an editor carries any marker, and found by halving:
1.9 ms on a hundred thousand characters with eighty holes, and it only
runs when a file has holes at all.

**The one that looked like a wrong filter was a slow one.**
`fillers_in_source` is a whole run of inference — **930 ms on
`minute.ges`** — and it was being paid for every keystroke, so the rows
on screen always answered the letter before the one in front of you.
On a recording that is indistinguishable from a filter that does not
filter.  The query does not change *what fits*, only what is worth
showing first: the file decides once, the ranking is per keystroke, and
930 ms becomes 0.1.  The refusal is cached with the answers and
deliberately — mid-line the program is in pieces, which is exactly when
holes are filled, and learning that again at a second a letter is the
same defect wearing its other face.

A new wire word came out of it, `ask`: `fill` puts text in the question
being asked, `ask` says *which* question and which of its parts are
already answered.  Tab arrives with the hole's type taken; a completion
that lands on another hole re-asks with the new type, which is what
empties the field and stops the box saying `Int` over a `Float` hole.
And `wants` now carries the arguments already given, so a type typed
over the offered one re-ranks the list — a hole inferred as `t a` says
almost nothing, and narrowing it by hand is a person telling the
compiler what they are about to write.

### The star, and the hands that were measured rather than chosen

The model half went in the order the house asks: the verb before the
window learns it.  `transpose : Text -> Int -> Int -> Command` — the
region, the key it says now, the key it becomes.  The spec's first
draft said "the channel and a number of steps", and building it found
that a channel cannot name a note (a chord is one written place and
four of them) and that a recorded `+3` means a different note the
second time it is read.

**The hands are the part the spec got wrong, and measuring said so
before anything was built.**  A hand must be the full height of the
roll or a drag saturates — four pixels to a semitone — and full-height
regions that overlap hide each other, because the substrate resolves a
press to the innermost region written first.  One hand per *written
place* was the leading candidate:

| file | written places | pairs sounding at once |
|---|---|---|
| `minute.ges` | 4 | 0 |
| `noted.ges` | 4 | 0 |
| `chopin.ges` | 28 | **17** |

Seventeen of chopin's would have been unpressable at any height, while
the two files anybody would have tested on have no overlap at all.  So
the hands **tile the picture** instead: equal full-height columns, no
two overlapping, every note under exactly one wherever it sounds — and
*which* note a gesture means is read off the height, which is aiming in
both directions and made the press more precise than it was.  A chord
used to be one region that jumped to its own line however you aimed at
it; its notes are four places now.

Two more decisions the building forced.  **The drag is relative** — a
column is the whole height, so a press lands at some pitch and rarely
the note's own, and carried absolutely, letting go without moving would
transpose the note to wherever you happened to grab it.  And **the hand
is taller than the picture**: `TouchY` writes a fraction of its own
element and is clamped there, the law that makes every gesture bounded
by construction, so a hand the size of the roll could only ever name a
pitch the piece already plays.  Henri: *"the drag appears to stop to the
canvas borders."*  The answer is not to unclamp it — that puts the
bound in every program's hands — but to hand out a taller element: two
octaves each way at the roll's own pixels-per-semitone, off the top and
bottom of the band where the clip hides it.

Acceptance was five things and the fifth is the one that matters: drag
a note up a third in `duet.ges`, render, and **hear** 49.  Checked at
two intervals, so the test is not agreeing with itself.

### And then it had to feel like a gesture

Two complaints, both fair, and the first was a regression of my own
making: *"audio stutters when I move the notes"* and *"notes are frozen
in their places when dragged — the message in the bottom is the only
sign they're responding."*

The frozen note was the deeper one.  A roll is redrawn by a build and a
build is half a second at best, so the whole gesture happened with the
picture standing still.  **The picture reacts now instead of being
rebuilt**: the roll's program grew two channels — which note is held,
how far it has been carried — and became a *signal* over them, so one
note moves and the others do not.  The model writes them as
**readings**, the way `peak` travels; the roll is the one canvas whose
facts are the editor's rather than the instrument's.

That fix contained the next defect.  Boxes in the source view had no
reason to redraw between keystrokes, so the preview froze the instant
the hand stopped — a motion event was the only thing still dirtying the
frame.  Dirtying on *every* reading fixed it and cost far too much:
`peak` and `position` move thirty times a second whenever anything
plays, so any file with a box repainted continuously, walking every
picture, on a machine that was also compiling.  A walk now says whether
it *has* the channel a reading names: a score box does not know `peak`,
and a frame drawn for it is a frame nobody asked for.

The sound follows too, and waits for the hand: `audition_soon` turns a
string of drops into one build of the last text, because each rebuild
is a compile racing the render loop.  Which surfaced a hazard worth its
own commit — two builds in flight wrote into **one** `pending` engine
slot, so an older one finishing last would put the sound back an edit
while the text stayed right.  `Newest` — one worker, newest ask —
serialises them, and ordering follows from serialising.

### The instruments, again

Three came out of the evening, and the pattern is the same one the
afternoon found: *the thing that cannot say when it is wrong is the
thing to fix first.*

**A bench of tools** — `tools/toolbox.sh`, which reports what a machine
has and fetches what it lacks.  Xvfb so the window tests stop landing
on the desk of whoever is typing; `python-xlib` for XTEST and for
reading a window's pixels back.  It earned itself the same day: the
"list ignores the query" defect was diagnosed by driving a real window
and typing `cos` into it, which proved the wire innocent in one run.
F138 was *reproduced* the same way — a space in a filler field runs the
command on half the answer and writes `[1,` into the file.

**The card counts what it could not play.**  An underrun was recovered
from silently — right for a player, and it meant a crackle could be
argued about and not measured, which is the one thing this project
lets nothing else get away with.  Two numbers now ride under each build
report: how many blocks the card ran dry for while that build ran, and
the longest a single render took against the period it had to fit in.

    [audio] card ran dry 3× · worst block 41.2 ms of 5.8 ms

Most of their value is in reading *zero*: a stutter you can hear beside
`0× · 1.1 ms of 5.8 ms` says the rebuild is innocent and the search is
somewhere else.

**And a recording can ask for the card.**  A transcript is the one
reproduction of a stutter there is — the same edits and auditions in
the same order — so `--play` starts the instrument for the length of a
replay and `--dry-max` turns the account into an exit code:

    git bisect start && git bisect bad && git bisect good <commit>
    git bisect run python -m gestate.sessionlog <session>.ges \
        --play --rate 44100 --dry-max 0

Three steps and nobody listening to twenty builds.  It stays a *flag*,
because the comment it is written under still holds: a replay that
opened a sound card by default would be a replay you cannot run twice.

### What is still open

**The stutter.**  Not found.  The repaint storm was real and was mine,
and fixing it did not make the sound clean, so something older is in
there.  What exists now that did not this morning is the means to
answer it: the counters say whether a rebuild starved the card, and a
recorded session says it the same way twice.  What is *known*: a
rebuild of `Real_World_One.ges` is 3.15 s, of which `clang` is 1.28 s
of subprocess with no GIL held, and the loaders that could overlap it
come to about half a second — so a side thread there has a ceiling of a
seventh and would buy it out of the one stretch in which the audio
thread has Python to itself.  A rebuild that stutters is worse than a
rebuild that is slow.

**F138**, filed with its repro and not fixed: the window is told what an
argument's type is *called* and not what it *is*, and `Filler` is a
`Text` alias.

**Tier two** of the star — structural edits, gated on a declaration
already being formatter-clean — and typing a pitch instead of dragging
to it, which is what will finally force the keyboard question.

### What the evening was about

The morning's lesson was that being wrong has to be visible.  The
evening's is narrower and was learned four times: **a gesture is a
claim about time.**  The caret landing in the old document, the list
answering the previous keystroke, the panel deciding once and never
again, the note standing still while the hand moved — each of those is
correct code arriving at the wrong moment, and not one of them was
visible in a test that asked whether the answer was right.  What found
all four was somebody using the thing and a recording of it, read frame
by frame.

## The morning the messages arrived in time

2026-08-16.  A morning of small things with one shape between them:
**a machine that knows something says it at the moment a person can
still act on it.**  A size before the render rather than after it, a
refusal's reason instead of its exit code, a typo named at the
signature instead of complained about three definitions later.  None of
the three is a feature; all three are the difference between a tool
that works and a tool somebody trusts.

It began with `incoming.txt` — Henri's leftovers from the night before
and the notes that arrived before sleep — and ended with two defects
from real use, one of them the first ever reported by somebody who did
not build this.

### The night's notes, placed

Nine points, two of them in Finnish, none of them a task list.  They
went into `roadmap.md` where each argues rather than into a heap at the
end, and the placing was most of the thinking:

* **The grammar of graphics** goes beside the substrate, the way
  `spec/frp_lesson.md` stands beside the signal half.  `Label` turned up
  one drawing rule the hard way; reading what somebody else paid for is
  cheaper than turning them up one element at a time.
* **Naming the datatypes** — `type Duration = Float`, `type Pitch = Int`
  — is sequenced *after* F138, because an alias is a name the window is
  handed instead of what it aliases to, which is that defect exactly.
  Minting more aliases first would spread the bug rather than the
  documentation.
* **`rocks.md` on representing nodes** folded into the cost meter: a
  node count in a margin is the same *a bare number is noise* problem
  the marks already answer, and doing it that way tests rocks.md's claim
  to be a vocabulary rather than a trick that worked once on bytes.
* **A drawing of the whole project** carries its own hard question —
  how would it stay true? — and the cheaper of the two honest answers
  has the shape `test_manual.py` already uses: let the nouns be checked
  and leave the arrows to taste.
* **Product safety wants a process, not a promise.**  The guards exist;
  nobody has written down the list or when it is checked.

`spec/firstpiece.md` said at its head what its parentheses had been
saying one by one since 2026-08-14: all five fix-shapes are done.  What
is *not* done is its verdict — closing five frictions does not flatten
the documentation gradient that produced them, and the next newcomer
finds the next five.

And the README swapped its picture.  `doc/workbench4.png` had ridden in
with a song's commit and nothing referenced it; the paragraph it now
stands under says *"`spectro` is the same node wearing a spectrum"*,
and the picture that had been there showed two spectros — the one thing
that sentence needs a picture to contradict.

### Weighing what is about to be written

`spec/rocks.md` shipped the mark the night before and recorded its own
first omission: **it weighed what existed and not what was about to.**
A forty-minute render is knowable before a sample of it is made, so the
export now asks

    about 402.8M ▲, render it? [y/n]

Three rules make it worth having rather than worth muting:

**At `▲` only.**  A question at every export is a question nobody
reads, which is rocks.md's own argument for three marks rather than a
number.  Under the threshold, `wrote piece.wav — 31.7M ▪` is the whole
of what there is to say.

**Known, never guessed.**  The length is the stated bars or the score
the bench has already laid out, the channels are the instrument that is
playing, the rate is the renderer's own default because that is what
the export will use.  Missing any of the three it says nothing: a wolf
cried over an invented number teaches the person to answer `y` without
reading, which is worse than never asking.

**A bar range is weighed by what it writes.**  `exportWavAt 900 901`
renders from the top and cuts the front off, so the honest number is
the quarter of an hour that reaches the disk and not the one bar that
survives — and a typo in the first number is exactly the mistake the
question exists to catch.

One question and one yes: a heavy render over an existing file says
both facts in one sentence, and `overwrite` answers both, because a
second verb for *go ahead* would be a second word for the same act.

### A render refused and would not say why

Henri's transcript, four lines long and a complete bug report:

```
exportWav "sauna.wav"                  #= exporting sauna.wav…
#! sauna.wav: the render refused (exit 1)
```

*"I wonder why.  Either there's a bug or the information I get is too
light."*  The second.  Run by hand, the same export says exactly what
is wrong — sauna's parts are `long 200 (cycle …)`, so it is performed
dynamically, and a dynamic performance has no end to render to.  The
renderer had a whole sentence.  `_export_wav` redirected **stdout** and
left stderr alone, so the sentence went to the terminal the workbench
was launched from, which the person in the window never sees.

Fixed by catching stderr too and carrying what the program blamed
itself for — the last `gestate:` line, since progress is not a
complaint — with the exit code kept only for a refusal that says
nothing.

The second half of it was subtler and is the more useful lesson.  The
sentence named `--seconds`, which is a flag, and the person reading it
was in a window that cannot pass flags.  **A message read in two places
must name the door each reader has**, so it now names both:
`--seconds` from the terminal, `exportWavAt first last` in the
workbench — checked, because advice towards a door that does not open
is worse than no advice: five seconds of sauna renders through that
path.

`fixme.md` F140, with Henri's own transcript kept as the specimen.

### The type that was wearing the wrong case

The other defect came from **gestate's first outside user**, who wrote

```
foo : int
```

and could not see why it did not work.  Nothing was broken, which is
the whole difficulty: a name beginning with a lowercase letter *is* a
type variable, so that is a legal polymorphic signature over a variable
spelled like a type, and the file analyses without a word about `int`.

What made it worse than silence is what the compiler said next.  The
complaint surfaced wherever the variable failed to satisfy a class:

```
No instance for Num int — 'int' is a signature variable, standing for
whatever type the caller chooses; write '(Num int) => …' in the
signature to require it of the caller
```

Every word true of the program that was written, and **advice towards
the wrong fix** — take it and the mistake becomes permanent.  With
`main` untyped it was worse still: `'main' cannot have a class context`,
naming neither the line nor the mistake.

It is caught now in the kind checker, which is the pass that already
knows the type vocabulary and already refuses `Intt`:

```
`float` is a type variable, not the type `Float` (at typo.ges:1:8) —
a name in lowercase stands for whatever type the caller picks.
```

Two things came with it.  **A signature variable had no position at
all** — it is minted in `desugar_signature` rather than desugared from
a node, so its errors landed on whatever failed to unify with it, half
a file away; it carries the span it was written at now, and every
message about one is the better for it.  And **the match is exact but
for case**, which is what makes this a typo rather than a guess: `a`,
`m` and `k` name nothing, `int` names `Int`, and the vocabulary is the
program's own kind environment, so a type the file declares protects
its own name too.

The price is that a variable genuinely wanted under such a name has to
be spelled differently.  It was measured before it was chosen: across
every `.ges` in this repository, against all 94 type names the project
declares, there are **no** such variables — and the 92 example programs
still pass.  `doc/manual.md` §4 states the rule now, since the case
convention was written down nowhere a newcomer would look.

`fixme.md` F141.  What it does *not* catch is a name matching a type
**alias**, because aliases are expanded before the kind environment
exists — filed there and in the roadmap beside the naming pass, which
is the work that would make such collisions likely in the first place.

### Three tests that had fallen behind

Henri ran the full suite — 2,397 passing, three red, all of them the
suite telling the truth about work that had moved past it:

* `doc/ref/commands.md` was behind by five commands the editor had
  grown (`transpose`, `complete`, `col`, `Filler`, `Wanted`).  It is
  generated; regenerating it is the fix, and the test exists precisely
  so that nobody has to notice by reading.
* The transcript's sentence was asserted to end in `"steps"`, and since
  rocks.md it ends in what the file weighs.  The assertion now checks
  the law rather than the old spelling.
* `moon_sonata.ges` had arrived without a line in `test_audio.py`'s
  roster, which is the list that makes *every* audio example accounted
  for and each absence of a golden argued.  Three parts on three grids
  at once — the polyphony argument made where the parts disagree about
  the beat.

None was a defect in the program, and all three were worth failing: a
suite that only fails on broken code cannot tell you that a document
has drifted.

### What the morning was about

Every piece of it was a sentence, and every sentence was about *when*.
The size is a fact the machine has had all along — it just said it
after the render.  The refusal's reason existed — it went to a terminal
nobody was reading.  The typo was knowable at the signature — it was
reported three definitions later, in the vocabulary of a feature the
person was not using.

Which is the same lesson the star's evening reached from the other
side: **a message, like a gesture, is a claim about time.**  Being
right is not enough; it has to arrive where the person can still do
something about it.

## The sheet that draws itself

2026-08-16, afternoon.  Henri asked for an A3 or two mapping the
architecture, *"such that it stands time and updates along the
project"* — which is the whole question, and it had been sitting in
the roadmap since the morning with two candidate answers.

Both turned out to be one answer.

**An architecture drawing is a claim about a tree that keeps moving.**
The morning's entry had it filed as a choice: generate the picture from
what the machine can see, or draw it by hand and give it an oracle over
the nouns.  Writing it made the choice dissolve — the machine has the
nouns *and* can check the verbs, because an arrow between two parts of
a Python program is an import, and an import is a fact.  What the
machine cannot know is which lane a module belongs to and what that
lane is *for*, and that is exactly what a person should be writing.

So `gestate/atlas.py` has two hand-written tables and everything else is
read from the tree:

* **`WHERE`** — module → lane.  Every module must be in it.  A new
  module fails `test_atlas.py` by name rather than quietly going
  missing from the picture, which is the drift the whole arrangement
  exists to prevent.
* **`SPINE`** — the arrows worth drawing, each carrying the import that
  proves it: `("core", "sound", "the graph", ("audioextract",
  "gmachine"))`.  One crossing is not a Python call at all — the model
  sends the window its furniture down a pipe — and that one names a
  file instead.

Everything else — fifty-nine modules, the seven libraries, the four
crates and `host.c` — is discovered, and the sheet is `doc/atlas/whole.svg`,
A3 in millimetres because it is meant to be printed.

**The guarantee is `doc/ref/`'s, and deliberately the same sentence.**
`test_atlas.py` fails when a module has no lane, when a lane names
something gone, when an arrow has nothing behind it, when a named
library or crate is missing, and when the committed sheet is not what
today's source renders — *run `python -m gestate.atlas`*.  Rendering
twice must give the same bytes, which is why there is no timestamp and
no commit hash on the page: a generated file that changes when nothing
changed is a generated file people stop regenerating, and then the
picture is a hand-drawn one again with extra steps.

Two things the drawing itself taught, both about time rather than
architecture:

**A lane is as tall as what is in it.**  The first version fixed the
heights and the sheet was mostly air with the module names crammed into
the top of each box.  Sizing a lane by its content means a lane that
gains a module grows, and the sheet stays legible without anybody
adjusting a number — the same reason the editor's rows have varying
height.

**An arrow drawn between rows must go round, not through.**  Straight
lines from the core lane to the three backends crossed two lane titles
and read as a scribble; a bus under the core with three drops off it
reads as a route.  The sideways arrows moved *below* the text they
pass, which the lane's own measured height is what makes possible.

**And it leaves a `.png` beside the sheet**, which is Henri's ask an
hour later: *"so you won't have to reach inkscape every time — would
there be a lighter tool?"*  There is.  `cairosvg` is a `pip install`
into the interpreter the suite already runs under, renders this sheet
identically — CSS classes, mono spans, arrowheads and all — and takes
a second where Inkscape, being a whole editor asked to convert a file,
takes two and a half.  `rsvg-convert`, `resvg` and Inkscape are tried
after it, so a machine with any of them can still look at the picture,
and a machine with none of them still *writes* it: the `.svg` is the
artefact and the raster is a convenience, and a build that failed for
want of a convenience would be the tail wagging the dog.

The raster is **not committed**, and the reason is the same one the
whole file is built on: `test_atlas.py` can check that a committed
sheet is what the source renders only because the sheet is text.
Raster bytes differ between rasterisers and between versions of one, so
a committed `.png` would be the one generated artefact here with no
guarantee behind it — which is the drift this was built to prevent,
wearing a different suffix.  `.gitignore` carries that sentence, where
somebody would look for it.

What is left is more sheets, and the rule the rest of this project runs
on applies: draw the one somebody wants to read.  The generator returns
a page per name, so the front end pass by pass, the sound path, and the
window are each an afternoon whenever the overview stops saying enough.
