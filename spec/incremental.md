# incremental.md — doing less on a small change

*Companion to `spec/liveaudio.md` (why there is a compiler at all) and
to `roadmap.md` §"The save cycle".  The ask is Henri's, 2026-08-16:
"the compile times are seconds and I don't think they should be, if
there's only one small change at a time."  Everything below is measured
on `examples/audio/quartet.ges` — 640 lines, four banks, the heaviest
example in the tree — on the machine this project is written on.*

## The vocabulary, since these things have names

* **Incremental compilation** — the family: recompile only what the
  change requires.
* **Separate compilation** — independent translation units compiled to
  object files and linked.  C's model.
* **Smart recompilation** (Tichy, 1986) — deciding what to recompile
  from real dependencies rather than from timestamps.
* **Early cutoff** — when a recomputed thing turns out equal to what
  was there, stop; the work downstream of it is not needed.  Named and
  classified in *Build Systems à la Carte*.
* **Query-based** or **demand-driven** compilation — the same idea as a
  memoised graph over every intermediate, rather than per phase.
  `rustc`'s query system and the `salsa` crate are the reference
  implementations.
* **Content-addressed build cache** — an artefact keyed by the hash of
  what produced it.  `ccache`, Bazel's action cache, and this project's
  `.so` store.
* **Unsound incrementality** — an under-approximated dependency graph:
  skipping something that did depend on the change.  **This is the
  enemy**, and everything below is shaped by it.

## The law

> **A wrong "unchanged" is silently the wrong music.**

A rebuild that skips too much does not crash; it plays yesterday's
score under today's synth, or today's score under a synth that no
longer exists.  Nothing catches that but an ear, and the ear is
listening to a piece it has heard fifty times.  So every decision here
is asked in the safe direction: **what cannot be proved unchanged is
rebuilt**, and a dependency this project cannot bound honestly is not
skipped at all.

The price is paid in seconds that were not strictly necessary, and that
is the right price.

## Where the seconds are

One constant changed inside one voice body — the smallest edit that
changes the sound — before any of this work:

| phase | | |
|---|---|---|
| `clang` | 1.53 s | the C really did change |
| `score` | 1.45 s | **the score was not touched** |
| front end | 1.32 s | the program half, re-analysed |
| `substrate` | 0.31 s | no canvas in the edit either |
| `extract` | 0.20 s ×2 | |
| `midi` | 0.19 s | |

and a **comment-only edit cost two seconds**, which is the finding in
one line: a comment cannot change anything.  The rebuild was not asking
what changed, it was redoing the file.

## What is built: early cutoff, per phase

`gestate/unchanged.py` answers, for each phase, *did anything you read
move?*  The score, substrate and MIDI phases keep what they built when
the answer is no.

**Textual, and measured before chosen.**  The obvious implementation
parses both texts and compares declarations.  Expanding this file costs
0.6 s and parsing it 0.16 — most of what the skipping would save — and
it needs the program to *parse*, which while somebody is typing it
often does not.  A top-level declaration in this language begins in
column zero, which a regular expression finds in under a millisecond,
on half-written text.

What makes it safe is the refusals:

* a `class`, `instance`, `data`, `type`, `voices` or fixity line that
  differs by a byte means **everything moved** — each can change what
  some other declaration *means*, and an instance is chosen by type
  rather than by a name anything reaches;
* a declaration appearing or vanishing means everything moved;
* reachability walks **identifiers**, not resolved references: it sees
  more than the real dependency graph, and a bigger reachable set
  means fewer skips;
* nothing normalises whitespace, because layout is meaning here;
* the phase whose inputs cannot be bounded honestly — the `FromMIDI`
  half — asks the strictest question there is, *did anything at all
  change*;
* the seed is asked about separately, since it is not in the text and
  decides every note a chancy score draws.

Result: **5.41 s → 3.74 s** for a constant in a voice body, and a
comment no longer walks the score.

## Separate compilation, measured and refused

The next idea was Henri's: *could clang write a patch rather than the
whole program* — one object file per declaration, cached by content,
relinked.  It is the right instinct and the measurement refuses it.

**What the emitted module is.**  For `quartet.ges`: 439 functions,
14,295 lines of LLVM IR.  Three of them — `render_block`,
`render_block_f32`, `render_block_mix_f32` — are 3,170 lines each, and
they are the graph flattened into a loop.  The other 436 are the
program's own declarations: `adsrOf`, `svfNext`, `hzOf`, the instance
methods.

**What a one-line edit changes.**  A constant inside `bassOsc` changes
**3 functions of 439, 15 lines of 14,295** — the three bass voices'
folded steps.  A note in the score changes **nothing at all** in the
IR, which is why the `.so` store already catches that case.

So far this argues *for* splitting.  Then:

**Where clang's time actually goes** (`-O2`, one module):

| | |
|---|---|
| the whole module | 2.14 s |
| the 436 declarations alone | **0.09 s** |
| one renderer + the declarations | 0.83 s |
| the whole module at `-O1` | 1.09 s |
| the whole module at `-O0` | 0.91 s |

**Ninety-six per cent of the compile is the three renderers**, about
0.68 s each.  The declarations — the very things a per-declaration
object file would let us skip — are four per cent.

And splitting them out would cost the sound.  `render_block` is a loop
that makes **563 calls to 357 distinct functions per sample**; at `-O2`
in one module LLVM inlines them, and that is where the render speed
comes from.  In separate objects each becomes a real call.  ThinLTO
would give the inlining back, but the function that changed gets
inlined *into the renderers*, so the renderers must be re-optimised
anyway — which is the 96 %.

> **Separate compilation is refused here, and the reason is a number:
> the units a declaration-shaped split would separate are 4 % of the
> cost, and separating them removes the inlining the audio path is
> built on.**

`-O1` is refused for the same family of reasons and was measured
earlier: bit-identical objects, and `lead.ges` at 16× realtime instead
of 30× (`roadmap.md`).

## What the measurement pointed at instead — built

**Emit only the renderers this build will call.**  The three variants
exist for three callers: `render_block` (double) is the offline render
and the oracle, `render_block_f32` is the live engine and the C host,
`render_block_mix_f32` is the crossfade that installs an edit under
the sound.  A session in the editor never calls the double one; an
offline render never calls the mixing one.

Each unused variant is ~0.68 s of every rebuild, for code nothing in
that process will ever enter.  `audiollvm.RENDERERS` names the three
and `emit(graph, wants)` writes the subset; the live engine asks for
the two `f32` loops, the offline render and the oracle ask for the
`double` one.

**Nothing else changes**, and that is the point: the loops that are
kept are emitted byte for byte as before, so the inlining — and the
render speed — is exactly what it was.  A test asserts that rather than
trusting it.

`load()` declares a prototype only for a loop that is present, because
naming a symbol through `ctypes` *binds* it: a build that left one out
would otherwise fail at load, two layers away from the decision.

### What it came to

    one constant inside one voice, on quartet.ges

    before anything          5.41 s
    after early cutoff       3.74 s     score, substrate, midi kept
    after the subset         2.73 s     clang 1.46 s → 0.86 s

The floor is now the front end (0.98 s), `clang` on the two loops that
did change (0.86 s), and `_place` (0.26 s), which cannot be skipped
even for a comment because a comment moves the lines its knobs are
drawn beside.

## Acceptance

1. A phase whose inputs did not move is kept, and one that cannot be
   proved unmoved is rebuilt.
2. A changed note rebuilds the score; a changed synth constant does
   not.  Held by `test_audioeditor.py`.
3. A build asked for a subset of renderers emits exactly that subset;
   the loops it keeps are emitted unchanged, so the sound is not part
   of this decision; and `load` binds only what is there.  Held by
   three tests in `test_audiollvm.py`.
4. The numbers above are reproducible with `GESTATE_BUILD_TIME=1`.

## What is deliberately not done

* **Per-declaration object files** — refused above, with the number.
* **ThinLTO** — the same argument: the renderers must be re-optimised
  whenever anything they inline changes, and that is the cost.
* **Hot-patching a running `.so`** — it would fight the migration
  design (`spec/liveaudio.md` stage 5), and a live audio process is the
  worst place in this project to be clever about memory.
* **A query-based front end** — the right answer to the front end's
  remaining 1.2 s, and a different project: it means every intermediate
  becomes a memoised query keyed by its inputs.  Worth reading `salsa`
  before anybody starts.
