# Language audit — the features nobody has called

*2026-08-17.  `board/done/older-features.md` is the ask, and it is
Henri's: "using/given has never been used anywhere yet… Note that I
contradict project's rules there because it had no imminent use.  Let's
allow it to be, but I want to know where it works currently."  And:
"the whole Datafun implementation.  We went to FRP so hard that we
forgot about these features!  Do not remove them, but analyse where they
work right now."*

*Four questions per feature — does it typecheck, does it run, is it
reachable from the workbench, what is the smallest program that
exercises it — answered by running them rather than by reading them.
**Nothing was removed.**  Two examples were added, which is the caller
arriving late.*

## The measurement that started it

    grep -rn "(using \|given " examples/ specimens/ gestate/*.ges

Every hit is the English word in prose.  **In the whole tree, across
every example, specimen and library file, neither `using` nor `given`
nor a `Set` appears in a single `.ges` program.**  Both surfaces are
exercised only by `test/*.py` calling `evaluate()` directly — which is
the shape the roadmap warned about: *a feature that only its own tests
exercise is a feature nobody has run in a year.*

## `using` / `given` — works, everywhere it was tried

| question | answer |
|---|---|
| typechecks | yes |
| runs | yes, through the interpreter **and through the LLVM audio engine** |
| reachable from the workbench | yes — an ordinary `.ges` file plays |
| smallest program | six lines, below |

```
implicit hz : Float

tone : Sig Float
tone (using hz) = 0.2 * sine (!hz)

sound : Sig Float
sound = given hz = 220.0 in tone
```

Rendered: peak 0.200, RMS 0.141 — which is 0.2/√2 exactly, so the
implicit arrived with the value it was given and not with a default.

**The propagation works across depth**, which is the whole point of the
feature and the part a one-level test would not show.  In
`examples/audio/tuning.ges` the implicit is required by `step`, which is
called by `partial`, which is summed by `drone`; neither `partial` nor
`drone` mentions `concert`, and only `sound` supplies it.

**The two error messages are excellent** and were checked on purpose,
because a feature nobody uses is a feature whose diagnostics nobody has
read:

    unfilled implicit: `n` (required by `f`) reaches `main`, and nothing
    supplies it.  Bind it with `given n = … in …` somewhere the use is inside

    `f` uses an undeclared implicit `n`.  Declare its type at the top
    level: `implicit n : …`

### What is worth knowing before using it

- **A `given` that binds nothing is accepted in silence.**  The
  symmetric mistake — a `(using n)` with no `implicit n : …` — is
  caught; a `given n = 1 in 2` where nothing downstream wants `n` is a
  dead binding and nothing says so.  Harmless, and worth one line of
  documentation rather than a check.
- **The implicit shows in a query without its name** — `fixme.md` F144.

## Datafun — works, and had nowhere to be seen

| question | answer |
|---|---|
| typechecks | yes |
| runs | yes, through the interpreter |
| reachable from the workbench | **yes, through the canvas — and only there** |
| smallest program | four lines, below |

```
type Node = Cyclic 8

edge : Set (Node, Node)
edge = {(1, 2), (2, 3), (3, 4)}

reach : Set (Node, Node)
reach = fix r => edge \/ for ((a, b) in r, (c, d) in edge, b == c) {(a, d)}
```

Transitive closure, and it gives the right six pairs.

**The finding is that there was no way to look at it.**  Three separate
gaps, and together they are why this surface has no callers:

1. **`Set` has no `Show` instance.**  `show ({1,2} : Set Int)` is
   *"No instance for Show {Int}"*.
2. **Nothing prints a value.**  There is no CLI that runs a `main`, and
   each of the ones that exist says so in its own way:

       $ python -m gestate.midi m.ges
       a music program defines `score` and `bpm`, not `main` —
       `main` is supplied by the renderer

       $ python -m gestate.gui m.ges
       DeclError: Duplicate type signature for 'main'

   (`midi`'s message is the one to copy; `gui`'s is the compiler's
   internal complaint about a `main` the *backend* generated, leaking
   out at a person who wrote a perfectly ordinary program.)
3. **No workbench command shows a value either.**  `what`, `infer`,
   `fits` answer with *types*; `notes`, `scope`, `spectro` and `canvas`
   show live *signals*.  A `Set` is neither.

The evidence that this is old: `test/test_relations.py` counts
`evaluate(src).count("Pack{1,2}")` — it counts the *internal cons tag*,
because there has never been a readable form to assert against.

### The trap a fresh reader falls into

Writing the example produced one, and it is worth recording because it
is the *quiet* kind:

    audible = for ((a, b) in reaches, b == out) {a} \/ {out}

**A comprehension's body runs to the end of the expression**, so the
`\/ {out}` is inside the loop rather than beside it.  Nothing complains
— it typechecks, it runs — and the answer is right whenever anything
reaches the output and empty when nothing does.  A wrong answer that is
usually right is the hardest sort to see, and the only reason this one
was seen is that a test changed the cabling and watched the picture
follow.

`doc/manual.md` writes every comprehension with the braces hard against
the `for`, so the shape never comes up; `noted.ges` carries the same
warning one operator along, about `>>=` binding looser than `||`.  The
rule is the same both times: **parenthesise both halves.**

### The audio fragment refuses it, and says so beautifully

    gestate: this program cannot be compiled for the sound card: the engine
    plays a fixed graph, so everything `sound` reaches must be either a signal
    or a per-sample value, decided once at compile time.  What stopped it:
    `linked` uses `for` in audio-rate code.  Datafun's forms build sets, which
    allocate
    `holds` takes a parameter of type {Tuple0}, which is a set, which is a heap
    structure of unbounded size

Correct, and needs nothing.

### But the canvas takes it, and that is the caller

The canvas is interpreted at frame rate rather than compiled into the
engine, so **a Datafun query can drive a picture**.
`examples/gui/patchbay.ges` is a patch bay: five modules, three cables,
a transitive closure, and each module lit by whether its signal reaches
the output.  `spare` is cabled to nothing and stays dark.

That is a Datalog query drawn on the workbench canvas, and as far as
this tree goes it is the first caller Datafun has ever had.

## What the audit produced

| | |
|---|---|
| `fixme.md` F142 | a canvas-only file cannot be opened in the workbench at all |
| `fixme.md` F143 | an error inside `fix` cascades into spurious prelude errors under `typecheck --check` |
| `fixme.md` F144 | an implicit parameter shows in a query without its name |
| `examples/audio/tuning.ges` | `using`/`given`, propagating across three levels |
| `examples/gui/patchbay.ges` | a transitive closure lighting a canvas |

**Nothing was removed**, which was the ask.  Both features work; one of
them had no window to be seen through, and now has one.
