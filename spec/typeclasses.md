# Well-Behaved Typeclasses

Description of typeclasses.
Assumes the `types.md` has been implemented precisely.
Covers decisions that determine whether typeclass system stays sane at a scale.

1. Typeclasses are dictionary passing by default.
2. Elaborated during type checking.
3. Resolved by restricted logic programming.
4. Compiled with a hybrid of specialization and dynamic dispatch.

Everything below is consequence of taking above seriously.

---

## 1. The core mechanism: dictionary passing

A typeclass constraint compiles to an implicit function argument.
Into a "dictionary" that carries the implementation's methods for a specific type.

    class Show a where
        show : a -> String

    # Compiles to:
    ShowDict a := ShowDict (a -> String)

    # And this...
    showTwice : Show a => a -> String
    showTwice x = show x ++ show x

    # elaborates to:
    showTwice : ShowDict a -> a -> String
    showTwice sd x = sd.0 x ++ sd.0 x

Instance declaration compiles to a dictionary values:

    instance Show Int where
        show = intToString

    # compiles to:
    __show__Int__ : ShowDict Int
    __show__Int__ = ShowDict intToString

Call site passes the right dictionary, resolved statically by the compiler:

    showTwice (5 : Int)
    # elaborates to
    showTwice __show__Int__ 5

This is the Wadler & Blott translation from 1989.

- It requires **no runtime type information**. Dictionaries are ordinary values
  lacking tags, reflection and runtime type dispatch machinery.
- It **composes with everything else in the language**.
  It's just function application.
- It gives a clean target for how dictionaries are resolved and how they're compiled.

This document is all about doing dictionary passing correctly.

---

## 2. Core IR: keep typeclasses out of it

The core typed IR doesn't need typeclass-awareness.
Elaborate typeclasses away entirely during the surface-to-core pass.
The G-machine must not see your implicit supercombinators.

    Surface:  Show a => a -> String
    Core:     ShowDict a -> a -> String     # just a function type

Every optimization pass, part of the backend and future feature interacts
with the core IR. Keep the typeclasses away from it and give all
"dictionary" values all the standard optimizations
(inlining, unboxing, worker/wrapper transforms).

Elaboration catches the complexity:

    elaborate : SurfaceExpr -> TypeEnv -> ConstraintSet -> CoreExpr

This single-responsibility boundary is what keeps the rest of the compiler neat.

---

## 3. Type inference: qualified types as a distinct phase

*A Theory of Qualified Types* -paper describes qualified types.
They're types of the form `C => t` where `C` is a set of constraints (predicates)
and `t` is an ordinary HM type.

    qualified-type ::= predicates '=>' type
    predicate      ::= class-name type-args...

Structure inference as two clearly separated phases. Don't interleave
constraint solving into unification.
The behavior of both systems stays sane and predictable.

### Phase 1: Constraint generation

Run ordinary unification but every
use of a class method emits a fresh predicate instead of failing.

```
    show x  # generates fresh type var 'a', predicate (Show a), type (a -> String)
```

### Phase 2: Constraint solving / context reduction

After generation, simplify the accumulated predicate set:

- **Instance resolution**: Replace `C t` with the constraints from the
  matching instance's context, recursively (Section 5)
- **Simplification**: Remove redundant predicates using superclass
  relationships (`(Ord a, Eq a)` simplifies to `(Ord a)` if `Ord` implies `Eq`.
- **Ambiguity check**: Ambiguous predicates left over at the top level,
  typically `(Num a => a)` or `(Num a => List a)`,
  if the value is not a function and type annotation doesn't resolve the type,
  then produce an error for this condition.
  Do not leave ambiguous constraints to the runtime.

Generalization then produces the qualified type:

```
generalize : ConstraintSet -> Type -> QualifiedType
-- e.g. (Show a, Eq a) => a -> Bool
```

Keep this phase separation even though it costs some inference power.
(Can't do bidirectional consraint-directed unification tricks)
The predictability is worth it.
Users need to be able to look at function and know the inferred constraints straight away.

---

## 4. Global coherence

Coherence means that for any type `T` and class `C`, there is at most
one instance of `C` for `T`, visible identically everywhere in the program.

Decision for this language is that there's one instance per `(Class, Type)`
pair for the entire compiled program.
Enforced at link/compile time via **orphan instance rules**:

> An instance `instance C T` is only allowed to be defined in the module
> that defines `C`, or the module that defines `T` (or defines the head
> type constructor, for `T = F X`). Instances defined anywhere else are
> "orphans" and are rejected (or require an explicit unsafe escape hatch).

It buys you the property that `show x` means the same thing instead of varying
over module configuration and linking.
This property makes dictionary passing safe to *specialize* and *cache* (Section 6).
Compiler can soundly memoize and globally specialize a dictionary
because ´Show Foo` is well-defined.

Enforce this as a **separate compilation-unit check**: when compiling a
module, verify that every instance it defines obeys the orphan rule against
its own imports; when linking, verify no two modules define conflicting
instances for the same pair (this can mostly be caught statically per-module
if the orphan rule is enforced strictly, since orphan-free instances by
construction can't collide).

Sometimes users want controlled flexibility like "I want to vary `Ord` over this call".
Give an explicit mechanism that doesn't do class resolution at all
and provide explicit dictionary passing.
Solve the actual use case without making a mess out of instance resolution.

---

## 5. Instance resolution as restricted Horn-clause resolution

Model instance declarations as Prolog-style Horn clauses and resolve
predicates by SLD resolution.

```
instance (Eq a) => Eq [a] where ...
```

is the clause:

```
Eq [a] :- Eq a.
```

Resolving a predicate `Eq [Int]` means finding a clause whose head unifies
with it, then recursively resolving its body:

```
Eq [Int]  matches  Eq [a] :- Eq a   with a := Int
       -> resolve Eq Int
       -> matches Eq Int (no body)
       -> done, dictionary = ListEqDict (dict_Eq_Int)
```

This is exactly logic programming, and it inherits logic programming's
failure mode: **it can loop forever or be exponential** without
restrictions. Two independent safeguards, both required:

### 5.1 Paterson conditions (statically enforced at instance-declaration time)

For every instance `context => C t1 .. tn`, and for every predicate `D s1 ..
sm` in `context`:

1. Each `si` must contain no more type constructors than `t1 .. tn`
   combined.
2. Every type variable in `si` must also occur in `t1 .. tn`.
3. Where a variable occurs multiple times in `si`, it should occur at least
   as many times in the head (prevents crafted infinite chains like
   `instance C [a] => C [[a]]` unless genuinely warranted).

These conditions guarantee the resolution *body* is always structurally
"smaller" than the *head*, which is what guarantees termination of SLD
resolution here (it's a decreasing measure argument, same idea as
termination checking in a total language). Reject any instance declaration
that violates them at the point it's declared — don't wait for a program
that triggers non-termination to surface the problem.

Some rare legitimate cases would require an escape hatch for this feature.
It should be considered whenever those features are delivered.

### 5.2 Depth cap as a backstop

Even Paterson-legal instance sets can be slow (not infinite, just large) in
pathological cases, and someone will eventually find a way around a static
check you didn't anticipate. Cap SLD resolution depth (e.g. 200, matching
GHC's default) and produce a real compiler error — "instance resolution
exceeded depth N, likely a missing base case in class `X`" — never a stack
overflow or hang. This is a backstop, not the primary defense; the Paterson
conditions should make it almost never trigger in ordinary programs.

### 5.3 Resolution order and overlap

With global coherence (Section 4), there should be **at most one matching
clause** for any concrete, fully-applied predicate — if two instances can
both match, that's an overlap error, caught at the point the second
conflicting instance is declared (within the orphan-rule-enforced set),
not at the ambiguous call site later. This is a direct payoff of the
coherence decision: resolution becomes deterministic by construction rather
than needing a priority/specificity ordering.

---

## 6. Associated types

For classes with more than one type parameter — `Collection c e` where `c`
is the collection type and `e` is its element type — you need a way to say
"the element type is determined by the collection type."

    class Collection c where
        type Elem c
        insert : Elem c -> c -> c

    instance Collection [a] where
        type Elem [a] = a
        insert = (::)

`Elem` is a genuine type-level function attached to the class, resolved by
the same instance-resolution machinery as methods (Section 5), and checked
by the same core type checker as ordinary type application — no separate
unification extension needed. This gives you:

- Better error messages: `Elem [Int]` reduces to `Int`, an ordinary type
  equality, rather than a fundep-satisfaction question.
- A basis for real type-level computation (associated type families with
  multiple equations, closed type families for exhaustiveness) if you want
  to grow the language in that direction later — fundeps don't extend this
  way at all.
- One resolution mechanism instead of two.

Implementation-wise: associated types are class members like methods, just
resolved to *types* instead of *values* during elaboration, using the same
Horn-clause search from Section 5. `type Elem c` in a class declaration
introduces a type-level projection function; each instance provides an
equation for it; the elaborator normalizes `Elem T` by instance lookup the
same way it looks up `show_` for a `Show T` dictionary.

The same feature could be implemented by functional dependencies,
but functional dependencies are more hacky. Don't do them.

---

## 7. Compilation strategy: hybrid

Eventually implement all these three features and let compiler choose over call site.

### 7.1 Dictionary passing (the default, always correct)

As in Section 1: pass dictionaries as ordinary implicit arguments, compile
class methods as ordinary record field selection. This is always available,
always correct, supports separate compilation (a module can be compiled
without knowing every instance that will ever exist for its classes), and
supports polymorphic recursion (a function that calls itself at a different,
more specific type than its own signature — monomorphization alone cannot
handle this, because there's no static bound on how many instantiations
exist).

Cost: an extra indirection per method call, and the dictionary itself may
need to be allocated if it's not statically known (e.g. built from other
dictionaries, as in the `Eq [a] :- Eq a` example).

### 7.2 Specialization at known call sites (the default optimization)

When a polymorphic function is called with a **statically known type
argument** — which is the overwhelming majority of real call sites — the
compiler should specialize: generate a monomorphic copy of the function
with the dictionary argument eliminated and its fields inlined directly.

    showTwice : Show a => a -> String     # generic version, always exists
    showTwice_Int : Int -> String         # specialized version, generated
                                          # because showTwice was called at Int
    showTwice_Int x = intToString x ++ intToString x

This is exactly what GHC's `SPECIALIZE` pragma plus its inliner do, made
automatic instead of opt-in.

**Bounded by `frp.md`'s β/η rule.**  Inlining is β, and β is not
equivalence-preserving across `head`, `delay`, `⊛`, `5` or a `Sig`-typed
subterm (`errata.md` R9).  A specializer that inlines through one of those
changes *when* a signal is read.  Any implementation of this section has to
fence that off first; `roadmap.md` closes specialization partly for this
reason.

The algorithm:

1. During or after inlining, find call sites of polymorphic functions where
   every constraint argument resolves to a statically known dictionary
   (this is common — most instances resolve fully at compile time thanks to
   Section 5's algorithm being purely static).
2. Generate a specialized copy, or reuse a cached one if this exact
   `(function, type)` pair was already specialized elsewhere.
3. Rewrite the call site to use the specialized version.
4. Let ordinary inlining then fully eliminate the dictionary indirection.

Coherence (Section 4) is what makes step 2's caching sound: because
the dictionary for ints denotes the *same value* everywhere in the program, a
specialized vealue generated in one module is safe to reuse from
any other module, which is exactly what you want for keeping compile times
and binary size down relative to Rust's unconditional monomorphization.

Bound this: specialize opportunistically, with a compiler flag for how
aggressively (module-local only vs. whole-program specialization at link
time), rather than unconditionally monomorphizing everything the way Rust
does. Unconditional monomorphization is what produces Rust's well-known
compile-time and binary-size blowup on generic-heavy code; opportunistic
specialization gets most of the runtime win without that cost, because you
fall back to dictionary passing (Section 7.1) for the long tail of call
sites where full specialization doesn't pay for itself (e.g. the function
is large and called at many distinct types).

### 7.3 Explicit dynamic dispatch as an opt-in escape hatch

Sometimes the type genuinely isn't known statically — heterogeneous
collections, plugin systems, values coming from serialized/dynamic input.
For this, expose **boxed/existential dictionaries** explicitly in the
surface language, rather than forcing users into either full
monomorphization (impossible — there's no static type) or implicit runtime
dispatch baked invisibly into every polymorphic call (Haskell doesn't have
this in the base language; people fake it with existential wrapper types).

    ShowBox := (Show a) => ShowBox a

    items : [ShowBox]
    items = [ShowBox (5 : Int), ShowBox "hello", ShowBox True]

    describe : ShowBox -> String
    describe (ShowBox x) = show x   # dictionary carried inside the box, used dynamically

Make this a first-class, ergonomic feature — sugar for existential types
paired with their dictionaries — rather than the awkward manual encoding
Haskell programmers currently reach for. The key design property: **the
cost of dynamic dispatch is visible in the type** (`ShowBox`, not just
`a`), so a reader of the code can tell, from the signature alone, whether a
given value carries runtime dispatch overhead or not. This is the opposite
of virtual-dispatch-by-default OO languages, where every method call pays
indirection cost invisibly.

### Why hybrid and not "just pick one"

- **Pure dictionary-passing everywhere** (naive Haskell semantics without
  aggressive specialization pragmas) leaves real performance on the table
  for the common case of statically-known instances, which is most code.
- **Pure monomorphization everywhere** (Rust's default) produces the
  well-documented cost of long compile times and large binaries on
  generic-heavy code, and cannot handle polymorphic recursion at all.
- **Mixing them, with specialization as an automatic optimization and
  dictionary-passing as the always-correct fallback, and dynamic dispatch
  as an explicit opt-in** gets you correctness in all cases, good
  performance in the common case, and bounded compile times/binary size,
  at the cost of a more complex compiler backend. That complexity is the
  compiler's problem to absorb, not the language user's.

---

## 8. Unify typeclasses with general implicit parameters

Scala 3's `given`/`using` mechanism is worth adopting independent of the
coherence decision (Section 4): treat "typeclass instance" as a special
case of a more general "implicitly-passed value resolved by type," rather
than typeclasses being a bolted-on, syntactically separate feature from
ordinary implicit parameter passing.

    maxOf : (ord Ordering t, test Int) => t -> t -> t
    maxOf (using ord) x y = ...

    given ord = ordInt
          test = 5
    in maxOf 4 5

Concretely, this means:

- One resolution algorithm (Section 5) serves both "find the `Show`
  instance for `Int`" and "find the ambient implicit `Config` value for
  this call," rather than maintaining two separate mechanisms in the
  compiler.
- Users get implicit-parameter-passing as a general tool (dependency
  injection of loggers, configs, capabilities) built on the exact same
  machinery as typeclasses, instead of a second, differently-behaved
  feature they have to learn separately.

Take Scala's mechanism-unification idea; reject Scala's coherence model
(Section 4). These are genuinely orthogonal — you can have `given`/`using`
as your single implicit-passing substrate while still enforcing global
coherence and orphan rules on top of it for anything declared as a class
instance specifically. The "given can be scoped locally" flexibility Scala
allows for *general* implicits doesn't need to extend to *typeclass*
implicits if you don't want the incoherence risk from Section 4.

---

## 9. Summary checklist

A well-behaved typeclass implementation should have:

1. **Dictionary-passing elaboration** into a typeclass-free core IR —
   nothing else in the compiler needs to know typeclasses exist.
2. **Qualified-type inference** as a distinct constraint-generation +
   constraint-solving phase, with explicit, closed, opt-in defaulting
   rules — never silent, never open-ended.
3. **Global coherence with orphan rules**, decided before anything else is
   built, because it's a prerequisite for sound caching/specialization and
   for deterministic resolution.
4. **Horn-clause instance resolution** bounded by statically-checked
   Paterson conditions plus a depth-cap backstop, with an explicit, loudly
   named escape hatch for the rare legitimate violations.
5. **Associated types**, not functional dependencies, for multi-parameter
   classes.
6. **Hybrid compilation**: dictionary-passing as the always-correct
   default, opportunistic specialization at statically-known call sites as
   the main optimization, explicit boxed/existential dispatch as an
   ergonomic, type-visible opt-in for genuine runtime polymorphism.
7. **One implicit-resolution substrate** (`given`/`using`-style) underlying
   both typeclasses and general implicit parameters, without weakening
   coherence for the typeclass case specifically.

Nothing here is exotic — every piece has shipped in a production language.
The actual work is refusing to cut corners on any single piece, because
they depend on each other: coherence is what makes specialization sound;
the Paterson conditions are what make Horn-clause resolution decidable;
the clean core-IR boundary is what keeps the rest of the compiler from
needing to understand typeclasses at all.
