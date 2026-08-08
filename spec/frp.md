FRP primitives on the G-machine
================================

Source: Bahr, "Simple Modal Types for Functional Reactive Programming"
(arXiv:2512.09412). This extends `supercomb.md`'s G-machine, not
replaces it — ordinary functional code still compiles exactly as
specified there. The additions are (1) a handful of new node types
and instructions for the FRP primitives, and (2) a **reactive driver
loop that sits above `evaluate`**, because the paper's step semantics
(section 4.3) has no analogue in a batch graph-reducer.

Why this is a structural change, not a patch
---------------------------------------------

`evaluate` in `supercomb.md` runs `step` until `gmFinal`, i.e. until
code and dump are both empty. That is a **single, terminating**
reduction to WHNF. Rizzo's step semantics is a **sequence** of such
reductions, one per external input, over a heap that persists and
mutates between them (`⟨v;η/Δ⟩ κ↦→w =⇒ ⟨v;η′/Δ′⟩`, repeated
forever). So:

- `evaluate` becomes the thing you call to force *one* subterm to
  WHNF (its current job, unchanged). It is invoked many times per
  reactive step, not once per program run.
- A new top-level loop, `react`, owns the outer `κ↦→w =⇒` sequence.
  It is not expressible as G-code — it inspects and mutates the heap
  directly, and calls back into `evaluate` when (and only when) the
  paper's advance semantics needs to actually run user code.

Everything else — `map`, `filter`, `switch`, `sample`, `scan`,
`zip`, the GUI library — is ordinary Rizzo surface syntax that
desugars to `fix`/`delay`/pattern matching exactly as in section 2–3
of the paper, and compiles through `compileC` using nothing but the
primitives below plus the existing `compileC` clauses. You do not
need to special-case `map` or `sample`; you need to special-case the
eleven primitives (`::`, `head`, `tail`, `delay`, ``, `5`, `wait`,
`watch`, `sync`, `never`, `chan`) and `fix`.

New nodes
---------

    Node := ... (unchanged cases from supercomb.md) ...
           | NSig Addr Addr Bool   -- current value, delayed tail (⃝∃ Sig A), updated-this-step
           | NChan Int             -- channel identity

Everything else the FRP layer needs (`wait κ`, `watch l`, `sync v w`,
`never`, `tail l`, `v 5 w`) is representable with the **existing**
`NCon Tag [Addr]` node — the paper's evaluation semantics treats
these six forms exactly like strict data constructors ("they eagerly
evaluate their arguments to values and produce values of the form
..."), which is precisely what `Pack` already does (`compileC (ECon
t args)` never inserts `Eval` before packing — args are pushed as
graphs, forced only on demand). Reserve six tags:

    tagWait = 90, tagWatch = 91, tagSync = 92,
    tagNever = 93, tagTail = 94, tagExists5 = 95, tagDelay = 96

`NSig` is the one genuinely new *mutable* thing, but the machine
already knows how to mutate a heap cell in place — `Update n`
overwrites a cell with `NInd`. `NSig` just needs the same capability
for its own shape (see `SigNew`/`SigAdvance` below); nothing new is
required of the heap itself.

New instructions
-----------------

    Instruction := ... (unchanged from supercomb.md) ...
                 | Pack Tag Arity        -- already exists, reused for the six ⃝∃ ctors
                 | MkDelayAp             -- ⃝∀'s `` : combine two `delay _` values
                 | SigHead               -- `head`: project current value out of an NSig
                 | SigCons               -- `::`  : allocate a fresh NSig
                 | NewChan               -- `chan`: allocate a fresh NChan

Semantics of the four new ones:

    mkDelayAp s
        b := stack !! 0          -- NCon tagDelay [x]   (rightmost operand, t)
        a := stack !! 1          -- NCon tagDelay [f]    (leftmost operand, s)
        NCon _ [f] := heap ! a
        NCon _ [x] := heap ! b
        (apAddr, h) := hAlloc heap (NAp f x)
        (dAddr, h') := hAlloc h (NCon tagDelay [apAddr])
        s := putHeap h'; putStack (dAddr : drop 2 stack)

    sigHead s
        a := top of stack                 -- address of an NSig (result of Eval on a Sig-typed expr)
        NSig v _ _ := heap ! a
        s := putStack (v : drop 1 stack)

    sigCons s
        w := stack !! 0    -- delayed tail, an NCon-tagged ⃝∃ value or `never`
        v := stack !! 1    -- current value
        (l, h) := hAlloc heap (NSig v w False)
        registerSignal l s              -- append l to the *now* registry, see below
        s := putHeap h; putStack (l : drop 2 stack)

    newChan s
        k := freshChanId s
        (l, h) := hAlloc heap (NChan k)
        s := putHeap h; putStack (l : stack)

`compileC` for a `Sig A`-typed expression evaluates to the *address*
of its `NSig` cell, not to the value inside it — exactly as the
paper's evaluation semantics treats `⟨s ::_A t;ε⟩ ⇓ ⟨l;...⟩`. Only
`head` and `watch` reach inside the cell.

compileC extensions
--------------------

Reusing `supercomb.md`'s `env`/`Arg`/`Local` machinery unchanged;
these are just more `compileC` clauses.

    compileC (EDelay t)      env = compileC t env ++ [Pack tagDelay 1]

    compileC (EApp∀ s t)     env = compileC s env       ++ [Eval]
                               ++ compileC t (bump env)  ++ [Eval]
                               ++ [MkDelayAp]

    compileC (EApp∃ s t)     env = compileC s env       ++ [Eval]
                               ++ compileC t (bump env)  ++ [Eval]
                               ++ [Pack tagExists5 2]

    compileC (EWait t)       env = compileC t env ++ [Eval] ++ [Pack tagWait 1]
    compileC (EWatch t)      env = compileC t env ++ [Eval] ++ [Pack tagWatch 1]
    compileC (ESync s t)     env = compileC s env       ++ [Eval]
                               ++ compileC t (bump env)  ++ [Eval]
                               ++ [Pack tagSync 2]
    compileC ENever          env = [Pack tagNever 0]
    compileC (ETail t)       env = compileC t env ++ [Eval] ++ [Pack tagTail 1]
    compileC (EHead t)       env = compileC t env ++ [Eval] ++ [SigHead]
    compileC (ECons s t)     env = compileC s env       ++ [Eval]
                               ++ compileC t (bump env)  ++ [Eval]
                               ++ [SigCons]
    compileC EChan           env = [NewChan]

    -- guarded fixed point: fix x.t = t[delay(fix x.t)/x], the substituted
    -- term is a VALUE (never entered), so build it as a self-referential
    -- graph exactly the way compileLetrec builds mutually-recursive
    -- bindings — Alloc a placeholder, Update it to point at itself.
    compileC (EFix x t)      env
        = [Alloc 1]
       ++ [Push 0, Pack tagDelay 1, Update 0]   -- Local 0 := NInd (NCon tagDelay [Local 0])
       ++ compileC t env1
       ++ [Slide 1]
      where env1 = extendEnv x (Local 0) (mapEnv bump env)

The `Alloc`/`Push 0`/`Update 0` sequence produces a cyclic graph
(`p → NInd C`, `C = NCon tagDelay [p]`). That's intentional and
safe *only* because nothing in the evaluation semantics ever enters
a `delay`-tagged node's field without going through `advance`
first (section 4.1: "delay t is considered a value... does not
evaluate further"). Advancing it (via `` / `MkDelayAp` or the
scheduler, below) allocates a **fresh** `NAp`/`NCon` each time, so
the cycle is never walked — it's read once per unrolling, like a
lazy corecursive stream. If you ever add a G-machine optimization
that eagerly normalizes `NCon` fields, this breaks; flag it.

The reactive driver (outside the G-machine proper)
----------------------------------------------------

This is the part with no counterpart in `supercomb.md`. It is a
host-language loop (Python/Haskell, whatever `hAlloc`/`hUpdate` etc.
are implemented in), not G-code, because `ticked`/`advance` recurse
over the *shape* of `sync`-trees at the scheduler level — that's a
heap-inspecting predicate/interpreter, not straight-line bytecode.

The rules below are stated at the paper's κ — **one channel per step**.
gestate runs them at a *set* of arrivals; see §"Several arrivals in one
instant" at the end of this section for the generalisation, which changes
the type of `k` and nothing else about any rule here.

State it needs beyond plain `GmState`:

    GmReactive := GmState + { now :: [Addr]      -- NSig addrs, in allocation order
                             , earlier :: [Addr]  -- being processed this step
                             , chans :: Map Int Type }

    -- ticked, mirrors Fig. 10's `ticked^κ_η` exactly, reading tags off NCon:
    ticked :: Int -> Addr -> GmReactive -> Bool
    ticked k a s = case heap!a of
        NCon tagNever  []      -> False
        NCon tagExists5 [_,w]  -> ticked k w s
        NCon tagWait [chanAddr]-> chanAddr's NChan-id == k
        NCon tagWatch [l]      -> case heap!l of NSig (NCon 1{-inr-} _) _ True -> True; _ -> False
                                   -- "in1 v ⟨⊤⟩" i.e. current value is Just-shaped AND updated this step
        NCon tagTail [l]       -> case heap!l of NSig _ _ True -> True; _ -> False
        NCon tagSync [v,w]     -> ticked k v s || ticked k w s

    -- advance, mirrors the advance-semantics rules; the only case that
    -- re-enters the actual G-machine's evaluate is MkDelayAp's argument:
    advance :: Int -> Addr -> Value -> GmReactive -> (Addr, GmReactive)
    advance k a input s = case heap!a of
        NCon tagWait [_]        -> (input, s)                     -- w itself
        NCon tagWatch [l]       -> let NSig (NCon 1 [v]) _ _ = heap!l in (v, s)
        NCon tagTail [l]        -> (l, s)                          -- see ordering note below
        NCon tagExists5 [dAddr, vAddr] ->
            let (v', s')  = advance k vAddr input s
                NCon _ [f] = heap!dAddr
                s''        = putStack [f, v'] s' `then` [Mkap, Eval]  -- RE-ENTER evaluate here
                result     = top(stack(evaluate s''))
            in (result, s'' with stack popped)
        NCon tagSync [v,w]
          | ticked k v s && not (ticked k w s) ->
                let (v', s') = advance k v input s in (packLeft1 v', s')
          | ticked k w s && not (ticked k v s) ->
                let (w', s') = advance k w input s in (packLeft2 w', s')
          | otherwise ->  -- both ticked simultaneously
                let (v', s')  = advance k v input s
                    (w', s'') = advance k w input s'
                in (packBoth v' w', s'')

    -- one signal, one step of the earlier -> now sweep (Fig. 10, "update semantics")
    updateOne :: Int -> Value -> GmReactive -> GmReactive
    updateOne k input s =
        let (l : rest) = earlier s
            NSig v tailAddr _ = heap ! l
        in if not (ticked k tailAddr s)
           then s { heap = hUpdate l (NSig v tailAddr False), earlier = rest, now = now s ++ [l] }
           else let (l', s') = advance k tailAddr input s     -- l' is the NEW signal produced
                    NSig v' tail' _ = heap s' ! l'
                in s' { heap = hUpdate l (NSig v' tail' True), earlier = tail (earlier s'), now = now s' ++ [l] }

    -- ordering invariant this depends on: `now` is built LEFT TO RIGHT in
    -- the same order signals were allocated. `tail l` advancing to `l`
    -- itself is only correct because by the time anything downstream of
    -- l consults l, l has already been popped off `earlier` and updated
    -- in this same sweep — same invariant the paper states informally
    -- in section 4.3 ("relies on the fact that the advance semantics
    -- will evaluate tail l to l once the signal at l has already been
    -- updated"). If your scheduler processes signals out of allocation
    -- order, this breaks silently. Keep `now`/`earlier` as ordered lists,
    -- not sets.

    reactiveStep :: Int -> Value -> GmReactive -> GmReactive
    reactiveStep k input s0 =
        let s1 = s0 { earlier = now s0, now = [] }
        in until (null . earlier) (updateOne k input) s1

    react :: GmReactive -> Stream (Int, Value) -> Stream GmReactive
    react s0 inputs = scanl (\s (k,w) -> reactiveStep k w s) s0 inputs

`init`: run the program's initial term through the ordinary
`evaluate` once; every `SigCons` executed during that run appends to
`now` via `registerSignal` (a side channel on `GmState`, not part of
`GmCode` — the compiler doesn't know about it, `SigCons`'s
implementation does). That gives you `⟨t;Δ⟩ init =⇒ ⟨v;η0/Δ0⟩`.

Several arrivals in one instant
--------------------------------

The rules above thread `k :: Int` — the paper's κ, one channel per step.
gestate generalises it to a **map from channel id to value**:

    type Arrivals = Map Int Value          -- the channels that ticked, and what they carried

    ticked       :: Arrivals -> Addr -> GmReactive -> Bool
    advance      :: Arrivals -> Addr -> GmReactive -> (Addr, GmReactive)
    updateOne    :: Arrivals -> GmReactive -> GmReactive
    reactiveStep :: Arrivals -> GmReactive -> GmReactive

    reactInstant :: GmReactive -> [(Int, Value)] -> GmReactive
    reactInstant s = flip reactiveStep s . checkArrivals s

    react :: GmReactive -> Stream (Int, Value) -> Stream GmReactive
    react s0 = scanl (\s kw -> reactInstant s [kw]) s0     -- unchanged: one arrival, one instant

**This is a conservative extension, and the shape of the rules is why.**
Every rule asked exactly two questions of κ — *is this the channel that
ticked* (`ticked`'s `wait`, `cl`'s invariant) and *what did it carry*
(`advance`'s `wait`) — and both have per-channel answers. Set membership
replaces equality, and lookup replaces the single `input` handed down the
recursion. At one arrival the two coincide and every rule reads as the
paper writes it, which is what `react` above still does.

The one rule that *changes meaning* is `sync`, and only by becoming
reachable: `packBoth` was previously produced only when both sides of a
`sync` watched the same channel, so `SyncBoth` never came from the driver
at all. Two clocks ticking together is now the ordinary way to reach it.

**Why the extension is needed.** A block boundary is not a sequence of
events. An audio clock and a control clock tick *at the same instant*, and
running them one after the other advances everything downstream of the
control clock by a step no sample is taken at — invisible for a graph of
maps and zips, and a doubled accumulation for a `scan`. See
`spec/liveaudio.md` open question 3 for the program that showed it and the
number that pins it.

**What it must not do.** `advance` on `wait κ` must read κ's *own* value
out of the map rather than a single input threaded down the recursion —
otherwise a `sync` hands the control side the audio side's sample. And a
channel may carry at most one value per instant: two values on one channel
is two instants, and `checkArrivals` rejects it rather than letting the
second silently win.

The ordering invariant below is untouched. `now` is still built left to
right in allocation order, and the sweep is still one pass; an instant with
several arrivals is one sweep, not one per channel — which is the entire
point.

Worked check against the paper's own example
-----------------------------------------------

Section 4.5's `sample` trace allocates `l1, l2, l3` at init (three
`SigCons`), then on `κ1 ↦→ 1`: `l1` is `ticked` (its tail is `NCon
tagWait [κ1]`, matches), gets `advance`d via the `NCon tagWait`
case → pushes the literal input `1`, `SigCons`-equivalent rebuild
produces the new `l4`-shaped cell, folded into the same `l1` address
by `updateOne`'s `hUpdate l ...` (the paper's practical-considerations
note in 4.4 — write in place instead of allocating `l′` then
copying — is exactly what `updateOne` above does: `hUpdate l
(NSig v' tail' True)` instead of allocating a fresh `l4` and
pointing back). `l3` (the `sample`'s own signal) has tail `NCon
tagExists5 [delayed-map-closure, NCon tagTail [l1]]`; `ticked`
recurses into the `tagTail [l1]` case, which is true because `l1`
was just marked `True` in this same sweep, given ordering
`l1 < l3` in `earlier`/`now`. `advance` on the `tagExists5` node
hits the `Mkap, Eval` re-entry into the ordinary G-machine to run
`map (λx.(x, head l2))` against `l1`'s new head — this is the one
point where FRP scheduling and ordinary lazy graph reduction meet.
`l2` is untouched (its tail is `NCon tagWait [κ2]`, doesn't match
κ1), so `updateOne`'s first branch just clears its `updated` flag
and re-files it. That matches the paper's trace line for line.

The `filter` trace — the one that exercises `watch`
-----------------------------------------------------

`errata.md` R12: §4.5's `sample` trace is reproduced above, but the `filter`
trace is the one that exercises `watch`, and it is structurally different.

    filter p s = mkSig (watch (mapMaybe p s))

Init allocates three cells in this order: `l1 = xs`, `l2 = ms` (the partial
signal `map small xs`), `l3` (the filtered signal). Their clocks are **not**
all of the same kind:

    cl (tail l1) = {(chan, κ)}      -- driven by the channel
    cl (tail l2) = {(chan, κ)}      -- `map`, so it inherits l1's clock
    cl (tail l3) = {(sig,  l2)}     -- `watch l2`: driven by a *signal*

That third one is the point. `sample`'s clock is a channel clock inherited
through `tagTail`; `watch`'s is a **signal clock**, because whether `l3`
fires depends on the *value* `l2` holds this instant — `Just` fires, `Nothing`
does not. So `ticked` for `l3` has to read `l2` **after** `l2` has been
updated in this same sweep, which is exactly the allocation-order invariant
stated above for `tail l`: it holds for `watch l` too, and for the same
reason. Allocate the watcher before the signal it watches and it reads the
previous instant's value.

Per step, on inputs 3, 50, 7 with `small n = if n < 10 then Just n else Nothing`:

| input | `l1` | `l2` | `l3` | why |
|---|---|---|---|---|
| 3  | ticks | ticks → `Just 3`  | ticks, value 3 | `Just` fires the watcher |
| 50 | ticks | ticks → `Nothing` | **does not tick**, holds 3 | `Nothing` does not fire |
| 7  | ticks | ticks → `Just 7`  | ticks, value 7 | |

`l3` holding its value on the `Nothing` step is what makes this a *filter*
rather than a partial signal: the consumer sees a total signal that simply
stops changing. All three cells keep their identity throughout, as above.

`test/test_frp.py` asserts this against heap shapes rather than values.

β and η are not equivalence-preserving here
---------------------------------------------

`errata.md` R9.  §4.3 of the paper gives the counterexamples:
`(λx. delay x) (head xs)` differs from `delay (head xs)`, and
`f (head xs)` differs from `λx. f (head xs) x`.  Both are ordinary
β/η steps, and both change *when* a signal is read — which is the
entire content of a reactive program.

So this is a constraint on **every** optimizer in the pipeline, and it
belongs here rather than in any one of them:

> **No β or η rewriting across `head`, `delay`, `⊛`, `5`, or a
> `Sig`-typed subterm.**

Two passes in these specs would violate it if written naively.
`typeclasses.md` §7.2 specializes "during or after inlining" and then lets
"ordinary inlining fully eliminate the dictionary indirection" — inlining
is β.  `supercomb.md`'s lambda lifting floats lambda bodies to the top
level, which is safe only because it does not move anything *across* one of
the forms above.  `frp.md` already flags one instance of this ("if you ever
add a G-machine optimization that eagerly normalizes `NCon` fields, this
breaks"); the rule above is the general statement it is an instance of.

Nothing in gestate does β/η today, which is why the rule costs nothing to
adopt now and would be expensive to retrofit later — `roadmap.md` records
specialization as closed partly on these grounds.

Practical notes, not covered above
------------------------------------

- **Cost.** `reactiveStep` sweeps every live signal on every input,
  `O(#signals)` per event, matching the paper's own admission in
  §4.4 that it doesn't aim for an efficient strategy. §4.4's fix —
  single global heap, doubly-linked list instead of two separate
  heaps, ✓-pointer marking the now/earlier boundary, reference
  counting for GC — carries over directly: replace the `now`/
  `earlier :: [Addr]` lists with one linked list through the `NSig`
  nodes themselves (add a `next`/`prev` field) and a single "frontier"
  pointer, so `reactiveStep` doesn't allocate new lists every tick.
- **GC.** Reference counting, as the paper argues, not tracing:
  the type system rules out cyclic *signal* references (the `fix`
  self-cycle above is a `delay`-node cycle, never entered, and is
  local — it doesn't point through any `NSig`), so refcounting can't
  leak on real cycles.
- **`rec`/recursive types** (`μα.A`, `List`, trees-of-signals) are
  orthogonal to all of the above — they compile through the existing
  `ECon`/`ECase` clauses in `supercomb.md` unchanged; `rec`'s `fmap_F`
  desugars to a fold written in terms of those, no new nodes needed.
- **Type erasure**: none of this needs runtime types. `⃝∀` vs `⃝∃`
  and `Sync`'s three-way sum are enforced at Rizzo's type-checking
  stage only; by the time you're compiling to G-code there's no
  distinction the machine needs to preserve beyond the tags above.
