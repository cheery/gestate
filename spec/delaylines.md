# Delay lines — the fifth node kind

*A design, not an implementation.  Nothing in this file is built yet.*

`synth.ges` says, in the list of what is deliberately absent:

> **No delay line**, and therefore no chorus, flanger, echo or comb — a
> delay is a buffer, and the fragment admits no allocation and no unbounded
> indexing.  Karplus-Strong is out for the same reason.

That is still true, and it is the last thing standing between this
language and reverb, echo, chorus, flanging, plucked strings, waveguide
physical modelling and a brick-wall limiter.  This is what it would take.

---

## What the fragment actually forbids

Not buffers.  **Allocation** and **unbounded indexing**.  A delay line of a
length fixed at compile time is neither: it is a fixed-size array in the
state struct, indexed modulo its own length.  `voices keys 6` already
proves the language can take a count syntactically and lay out six copies
of a subgraph; a delay line is the same trick one level down.

So the restriction to lift is narrower than the sentence in `synth.ges`
suggests, and the design below stays inside every other rule the fragment
has: no heap, bounded time per sample, a state whose shape is known before
the program runs.

---

## The shape of the change

Today a graph has four node kinds (`audioir.Node.kind`):

| kind | state | output at instant *t* |
|---|---|---|
| `source` | one value | the clock, or the control value |
| `map` | none | `f(in[t])` |
| `zip` | none | `f(l[t], r[t])` |
| `scan` | one value | `f(out[t-1], in[t])` |

Add a fifth:

| kind | state | output at instant *t* |
|---|---|---|
| `line` | **N values and a cursor** | `buf[cursor - k]`, for a tap `k` |

`scan` is the special case at N = 1.  That is not a coincidence and it is
the reason this fits: **the engine already computes a node from last
instant's state and this instant's input**, and a delay line only makes
the memory longer.

### The four questions it raises

**1. Where does N come from?**  Compile time, like everything else the
state layout depends on.  `audioextract._fold_constants` already turns a
constant expression into a `Const`, so

    delay (seconds 0.25) s

works: `seconds 0.25` is `floor (0.25 * sampleRate)` and folds to an
integer before the graph exists.  A length that is *not* constant gets the
fragment's ordinary refusal, in the same voice as the others — *"a delay
line's length has to be known before the program runs, and this one is a
`Sig Int`"*.

**2. What does it read?**  Two forms, and the second subsumes the first:

    delay : Int -> Sig Float -> Sig Float
    tap   : Int -> Sig Float -> Sig Float -> Sig Float

`delay n s` is `s` n samples ago.  `tap n pos s` is a line of maximum
length `n` read at a **signal** position in samples, linearly interpolated
— which is what chorus, flanger, vibrato and a pitched Karplus-Strong all
need, because in each of them the read position moves.

`delay` is `tap` at a constant position, so `tap` is the primitive and
`delay` the face — the same relation `phase` and `sine` have.

**3. Feedback, which is the hard one.**  `y[t] = x[t] + g·y[t−N]` is a
**cycle**, and `audiograph._check_recursion` refuses those.

The delay node is what makes the cycle mean something, and the engine
already has the mechanism.  Look at `render_block`: a `scan` is computed
from `prev[i]` — its own state, from the previous instant — and
`cur[input]`, from this one.  A `line`'s output likewise depends on
**state alone**; its input is consumed at the end of the instant.  So the
evaluation splits into a read phase and a write phase:

    for node in nodes:                 # topological, line-input edges cut
        if node.kind == "line":
            cur[i] = buffer[i].read(pos)      # from state only
        …

    for node in lines:                 # after the pass
        buffer[i].write(cur[node.inputs[0]])

and `_check_recursion` relaxes from *no cycles* to **every cycle passes
through a `line` or a `scan`**.

That is not a new discipline.  It is the one `synth.ges`'s FM bank already
states in its own words — *"every operator reads the previous sample's
outputs … a cycle in the matrix would otherwise be a value defined in
terms of itself"* — promoted from a convention inside one component to a
rule the graph checks.

**4. How is a cycle *written*?**  This is the open question, and the one
worth settling before any code is written.  Three answers, in order of
how much they cost and how much they buy.

---

## The three answers

### (a) `feedback` — one new former, and it is `scan` with a longer arm

    feedback : Int -> (Float -> Float -> Float) -> Sig Float -> Sig Float

`feedback n f s` is `out[t] = f(out[t−n], s[t])`, and the output is also
what goes back into the line.  Beside its neighbour:

    scan       f z s :  out[t] = f(out[t−1], s[t])
    feedback n f   s :  out[t] = f(out[t−n], s[t])

The symmetry is the argument.  A reader who knows `scan` knows this, the
step function is an ordinary named function or written lambda exactly as
`scan`'s is, and no new syntax appears anywhere.

**Buys:** feedback comb (`feedback n (y x => x + g * y) s`), echo with
repeats, a Schroeder allpass with a second line, and therefore a plain
reverb.

**Does not buy:** anything that needs a *filter* inside the loop, because
the step function is pure and a filter has state.  That is Karplus-Strong,
and it is every waveguide.

### (b) `loop` — a signal function around the line

    loop : Int -> (Sig Float -> Sig Float) -> Sig Float -> Sig Float

`loop n f s` is `y` where `y = s + f (delay n y)`: the loop's contents are
a signal transformation, so anything that is one can go in it.

    pluck n s   = loop n (y => lowpassOnePole 3000.0 y) s
    string n s  = loop n (y => 0.5 * (y + delay 1 y)) s

**Buys:** everything.  Karplus-Strong, waveguides, damped strings, a tube
with a reflection filter, reverb with a lowpass in each comb — which is
what makes a reverb sound like a room rather than a bucket.

**Costs:** a function argument at signal level.  The fragment forbids
functions as values, and it is right to; but it already *inlines*
signal-level wrappers — that is why `lowpassSvf 800.0 0.4 s` works, and
why `fm`'s written lambda at a `scan` works.  The lambda here would be
inlined into the graph the same way, and the cycle it creates is exactly
the one (3) admits.  Bigger than (a), and the same kind of change.

### (c) Guarded recursion, which the language already has

`signal.ges` writes `scan` itself as

    scan = gfix q => (f z s => z ::: (delay (q2 => q2 f (f z (head s)))
                                      <*> q <@> tail s))

`gfix` is guarded recursion over Rizzo's later modality; the recursive
call sits under a `delay` and is productive by construction.  **That is
the same argument the whole of this file makes**, already in the type
system, and an N-sample delay line is `⃝` applied N times.

The honest observation is that the audio fragment does not admit `gfix` —
it recognises `scan` and `mkSig` by *name* as formers and refuses the
construct they are built from.  A design that let the fragment admit
guarded recursion directly would make delay lines a *consequence* rather
than a feature, and would be the most principled answer by some distance.

It is also the largest, and it would be a poor first step: (a) and (b) can
be built and heard while (c) is being thought about, and if (c) ever lands
they become library functions written in the language instead of formers.

**Recommendation: (a), then (b).  Keep (c) in view and do not design
against it.**

---

## What is built, and what (b) actually turned out to need

**(a) `feedback` and the `tap` beside it are done**, in all three engines
and bit-identical between them.  Two node kinds rather than one, because
they are different shapes:

| | reads | writes | breaks a cycle? |
|---|---|---|---|
| `feedback n f s` | the slot it is about to overwrite | the step's result | **no** — its value depends on `s[t]` |
| `tap n pos s` | wherever `pos` points, interpolated | its input, *after* the pass | **yes** — its value is a function of state |

That difference is the whole reason `tap` had to come first for `loop`:
only a node whose output does not depend on this instant's input can sit
in a feedback path.  `feedback` never needed it, because its loop is
inside the node.

### (b) was proposed with the wrong signature, and shipped with another

The proposal above takes a **signal function**:

    loop : Int -> (Sig Float -> Sig Float) -> Sig Float -> Sig Float

It was first thought to be blocked on a language question, and it is worth
recording what that looked like, because the evidence is real and points
somewhere else.  `loop n f s = y where y = s + f (tap n n y)` needs `y`
defined in terms of itself, and **the interpreter cannot run one**.
Measured, not assumed:

    y = scan (a b => a + 0.1) 0.0 y        -- step limit exceeded

even though a `scan`'s value at the first instant does not read its input
at all, so the knot *should* tie.  It does not, and `spec/frp.md` says
why: guardedness here is carried by **`gfix`**, which compiles to a
self-referential graph whose recursive occurrence sits under a
`delay`-tagged node that evaluation never enters.  A bare recursive
definition has no such node, so it unwinds.  The obvious rewrite does not
typecheck either — `gfix`'s binder is ⃝∀ and `:::` consumes ⃝∃:

    y = gfix q => zip (…) s (tap n (n-1) (0.0 ::: q))
    Type mismatch: expected 'ExL', got 'FaL'

**But the plumbing is not the real obstacle.**  Applying `f` to a signal
yields a whole signal, and there is no way to advance `f` by one instant:
`f (tail x)` is not `tail (f x)` unless `f` is causal, and nothing in the
type says it is.  A former whose oracle would need that fact is not a
former with a hard definition — it is the wrong primitive.

What a loop actually needs is a delay line **and a per-sample
accumulator**, and those collapse into one thing: let the ring hold whole
*states* rather than samples, and the accumulator is simply the slot
written last instant.

    loop : Int -> (b -> b -> Float -> b) -> b -> Sig Float -> Sig b

    scan       f z s :  st[t] = f          st[t-1]  s[t]
    feedback n f   s :  st[t] = f  st[t-n]          s[t]
    loop     n f z s :  st[t] = f  st[t-n] st[t-1]  s[t]

One ring, two arms, no cycle, and at `n = 1` the two arms are the same
slot and it degenerates to `feedback`.  Karplus-Strong is the case that
motivated it — it averages the two samples that left the line, and the
older of the pair is exactly what `feedback`'s step cannot reach:

    ksStep prev old x = case prev of
        Ks y p -> case old of
            Ks yn q -> Ks (x + 0.5 * (yn + p)) yn

**Buys:** what (b) was for — Karplus-Strong, waveguides, damped strings, a
reflection filter in a tube, a lowpass in each reverb comb.  The filter's
state rides in `b`.

**Costs:** the filter is written as a step over an explicit state rather
than as a signal function, so `lowpassOnePole 3000.0` cannot be dropped
in as-is; its recurrence has to be spelled into the step.  And the state
is `n` copies of `b` rather than `n` floats — a 32-sample string over a
three-word `Ks` is 96 words where a `feedback` would be 32.

That cost is the fragment's own rule showing through rather than an
accident of this design: a signal function at signal level is precisely
what is forbidden everywhere else here.

**The knot-tying extractor work was not needed and was not done.**  No
cycle is created, `_check_recursion` is untouched, and `tap` remains the
only node that can close one — which is still the route for a feedback
path that has to leave the node and come back.

---

## What has to change, file by file

For (a) and the `line` node.  Listed because the estimate is the argument.

| file | change |
|---|---|
| `audioir.py` | a `line` kind; `Node.length`; `words()` counts N + 1 for the slot |
| `audioengine.py` | read phase / write phase in `render_block`; `zero` and `migrate` for a buffer slot |
| `audiollvm.py` | a fixed array in the state struct, a cursor, and modulo indexing — the one place with real work |
| `audioextract.py` | recognise the former; require a constant length; cut `line`-input edges when ordering |
| `audiograph.py` | admit the former; relax `_check_recursion` to *every cycle crosses a line or a scan*; refuse a non-constant length |
| `changes.py` | a line keeps its buffer when `origin`, type **and length** all match — a changed length is a new line |
| `synth.ges` | `delay`, `tap`, `feedback`, and then `comb`, `allpass`, `echo`, `reverb`, `pluck` written in terms of them |

The migration rule deserves its own sentence: **a delay line whose length
changed cannot keep its buffer**, because the buffer's meaning is
positional.  Editing `delay 4410` to `delay 4400` while a sound is playing
restarts that line and nothing else — which is the right behaviour and is
the same rule `migrate` already applies when a `scan`'s type changes.

---

## What it unlocks, and what is already possible

The user-facing point of the whole exercise.

**Needs a delay line:**

| | needs |
|---|---|
| echo, slapback | (a) |
| feedforward comb, flanger, chorus | `tap` alone, no cycle |
| feedback comb, Schroeder allpass, plate/room reverb | (a) |
| Karplus-Strong, plucked string | `loop` — **done** |
| digital waveguide — string, tube, brass, flute | `loop` — **done**, with the reflection filter written as a step |
| brick-wall limiting by lookahead | `delay` alone |

**Already possible, and simply not written:**

| | built from |
|---|---|
| **modal synthesis** — bells, bars, membranes | a bank of `resonate`, excited by `dust`. `examples/audio/bell.ges`, `bar.ges`, `membrane.ges` |
| **mass–spring networks** | `scan`, which is exactly a per-sample state update |
| compression, limiting, ducking | `follow` and `compress` |
| coloured noise | `pink`, `brown`, `blue`, `violet` |
| sparse excitation | `dust` |

So "physical modelling" is not one feature.  **All three of its families
now work.**  The resonator family and the mass–spring family already did;
the waveguide family was the one blocked, because a waveguide *is* a delay
line with a filter in the loop — and that is what `loop` is.

*(The resonator family needed one thing after this was written, and it is
worth recording because the claim above was made too early.  Written
against `bandpassSvf` at maximum resonance, a bell **sounded like a
woodblock** — that filter's damping floor caps its ring at 0.503 s at
220 Hz, which is a marimba bar.  `resonate` takes a decay time in seconds
instead and rings for as long as it is asked.  The topology was right and
the available filter was not; a claim that something "already works"
should be made after hearing it.)*  That is worth knowing before anyone plans
a large piece of work: the thing to build is the delay line, and physical
modelling then follows from it rather than being a separate project.
