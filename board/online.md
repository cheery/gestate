# online — gestate, the audio production tool, reachable in a browser

    status   doing — 2026-08-29, pieces A and B landed; question 8 is Henri's, §"Questions"
    because  "somebody who has never read this repository should be able
             to open a file, hear it, change it, and hear the change
             without being told anything first" (vision.md, 2026-08-16)
             — and today the only way to that first sound is an apt line
             on Ubuntu (doc/install.md): a person shown the tool at this
             desk cannot open it at home tonight
    asked    Michael, 2026-08-28, relayed by Henri — "Lets put gestate
             online, the audio production tool.  And Michael wants it."
    see      vision.md §"Ease of use and efficiency" — the `because`
             card:stranger-test.md — the person this waits on has arrived
             doc/memory/the-language-goal.md — wasm as a target, his own
             note of 2026-08-20; this card is the first thing in the tree
             that needs it
             doc/memory/lead-with-the-noun.md — the tool first, the method
             to whoever leans in
             doc/memory/the-tree-withers.md — a site with no source and no
             check rots; this must be generated from the tree and gated
             doc/consent.md — Michael's row

## The ask

Michael's idea, in Henri's words at this terminal, 2026-08-28:

> We could put your environment online, so that people can interact
> with you and experience it themselves..  Small models appear to work.

And the decision, an hour later, narrowed to the noun:

> Lets put gestate online, the audio production tool.  And Michael wants
> it.  But write a card for this.

**What was narrowed away, and why it is recorded.**  The first form of
the idea was a *session* online — a visitor talking to a character in
the tree.  That form is not this card: it needs a fence outside the
session's write access (`~/tend`'s three bounds, budget, grant,
lifecycle), a per-visitor ledger cap on a personally paid account, and
a sheet naming what a small model has already been shown to drop
(`doc/memory/smaller-models-and-the-tree.md`: structural rules survive,
judgment goes first).  It is a second card if anybody asks for it, and
its `because` would be a different sentence.  This one is the tool.

## Found by looking

* The stranger test has been run twice with a person at this desk and
  never with a person at their own.  Run two cost half its thirty
  minutes to *the way in* (`card:stranger-test.md`).  A browser tab is
  the way in with that cost removed.
* Everything a first sound needs is in the tree: `gestate.audioextract`
  builds the graph and `gestate.audiollvm` runs it native.  What is
  missing is a second backend for the same graph — wasm — which is the
  language goal's own target and nothing in the tree yet emits.
* `examples/audio/twinkle.ges`, added today, is the file such a page
  would open on: an instrument and a song, thirty lines, four words of
  vocabulary.
* The findability work of 2026-08-26 refused a homepage.  This is not a
  homepage — it is the tool — but the refusal's reason still binds:
  whatever is online must be built from the tree by a command and
  checked by a gate, or it describes a tree that no longer exists.

## Questions

*Half of these were answered in the room before Henri had to leave; the
rest are his, and the card is not taken until they are.*

**1. What must a stranger be able to do in the tab?**  Answered in the
`because`: open a file, hear it, change a number, hear the change.  Not
the workbench, not the canvas, not MIDI in — the vision's opening line
and nothing past it.  *Answered 2026-08-28, from vision.md.*

**2. Does the sound come from the browser or from a server?**  A server
is a session's problem all over again — a machine that must stay up, a
bill per visitor, a fence.  Henri, the same sitting: *"I need to move
soon and can't keep the laptop online."*  That is the answer: **the
browser computes the sound**, and the only server is a static file
host.  Which makes this card the wasm backend, and nothing less.
*Answered 2026-08-28, from his own constraint.*

**3. Where does it live, and who pays?**  `doc/memory/personal-and-personally-paid.md`:
personal, and the one mechanism that would break it is a per-visitor
cost.  A static page has none.  GitHub Pages from this repository is the
default with a trigger: if the page ever needs a process, this question
reopens.  *Answered 2026-08-29, Henri: "Q3: github pages voi olla
hyvä valinta."*  GitHub Pages from this repository, the trigger kept.

**4. What is the postcondition?**  The default: Michael, at his own
machine, opens the page, hears `twinkle.ges`, changes one number, and
hears the change — with nobody at his shoulder.  That is the stranger
test's run three, and this card is done when he reports it, in his own
words, into this file.  **Open — needs Michael's yes to being the
stranger, which is a separate ask from the one already in the
register.**  *Answered 2026-08-29, Henri: "Q4 on hyvä
postcondition."*  Whether Michael is asked to be the stranger is still
his to ask; the card is done on the report, whoever writes it.

**5. What does it *not* do?**  A refusal is the most durable decision
this project makes (`spec/author.md`).  The default: no accounts, no
saving on a server, no session, no chat.  A tab that closes loses the
edit, and that is correct for a first sound.  *Answered 2026-08-29, Henri: "Juu,
tallennus ilman palvelinta, käyttäjän omiin tiedostoihin jotka hän
valitsee itse."*  So: no accounts, no server, no session, no chat —
**and saving is in**, to a file the person picks on their own machine.
Not the URL, not the browser's storage: a file they chose.

**6. Is wasm the whole cost?**  **No — and the wasm half is the small
half.**  Measured 2026-08-29, by a session, kept as a command:
`python tools/wasmcheck.py examples/audio/twinkle.ges --seconds 4`.
The `.ll` text `audiollvm.emit` already writes compiles with `clang
--target=wasm32` unchanged; linked, `twinkle.ges` is a **3164-byte**
module that imports one function from outside (`exp`) and renders
**176400/176400 frames bit-identical** to the native `.so` on the same
control values.  `twoknobs.ges` is 1072 bytes, imports nothing, and
matches too.  The `-O2` object is bit-for-bit what the graph means,
which is the same no-fast-math argument `audiollvm.build` makes for the
native build.  What the machine lacked was the linker: clang 18 asks
for `wasm-ld-18` by name, Ubuntu does not ship it with clang, and
`tools/toolbox.sh` now names the package and `wasmtime` beside it.
*Answered 2026-08-29.  What is not the compiler is §"The pieces".*

**7. What does "change it" mean, for a stranger at this page?**  The
question the measurement turned up, and the one that decides the
card's size.  Three readings, each with what kills it, in §"The
pieces".  *Answered 2026-08-29, Henri: "juu, olet
ajan tasalla.  Voit aloittaa työn heti."*  The order in §"The pieces"
stands: A and B first, C2 on the surface, C1 measured before built.

**8. How does the page reach GitHub Pages?**  Pages serves a branch
root or `/docs`, and this tree's `doc/` is not that.  The default: a
GitHub Actions workflow that runs `python -m gestate.online` on push
and deploys the directory — `clang` and `lld` are one apt line on the
runner, nothing is committed twice, and the page can never be behind
the tree.  What it costs is a process outside the tree, which question
3's trigger names; it runs at build time, not per visitor, so the
`personal-and-personally-paid` mechanism is not touched.  The
alternative is committing the generated site under a directory Pages
can serve, with a gate that it is not behind the source, the way
`doc/atlas/` is kept.  **Open — his to pick; the session did not write
the workflow, because it is outward-facing.**

## The pieces

*Written 2026-08-29 by the session that measured question 6, after
Henri asked whether the card had been split: "Onko se jo jaettu
pienempiin paloihin?  Ajattelin että WASM-käännös on aika iso asia."
It had not been.  This is the split, and the parts are the session's
reading — marked so.*

**A. The graph as wasm — done as a measurement, not yet as a build.**
Question 6.  What is left is a `build`-shaped function beside
`audiollvm.build` that writes the `.wasm` instead of the `.so`, and a
gate that holds it to the native render across the example set — the
check `wasmcheck.py` makes by hand today, skipping where `wasm-ld` or
`wasmtime` is absent, the way the engine tests skip without `clang`.
Small, and the tree already has every piece of it.  *Landed the same sitting
(2026-08-29):* `gestate/audiowasm.py` — `build`,
`imports_of`, `run`, and `HOST`, the table of what a page supplies
from `Math`; `test/test_wasm.py` holds all 52 of `examples/audio/`
bit-identical to `run_native` at a tenth of a second each (2 min 24 s,
skipping with the tool named where `wasm-ld` or `wasmtime` is absent);
`tools/wasmcheck.py` is the one-file, any-length form.  A is done when
B needs nothing more of it — one commit for the card, so no `## Done`
yet.

**B. A page that plays it — open a file, hear it.**  An
`AudioWorklet` that loads the module, calls `render_block` per quantum
and hands the doubles to the output; `exp` and whatever else the
imports list names supplied from `Math`.  The score is *not* the
worklet's problem: `audioperform.scored` already bakes a piece into
control changes at sample indices, and that list, shipped as data
beside the module, is what the page writes into the slots.  No Python
runs in the browser for this piece.  Built from the tree by one command
and checked by a gate, as the `see` line demands.  With A, this is the
vision's first two verbs.  *Landed the same sitting (2026-08-29):*
`python -m gestate.online <file.ges> -o site/` writes five files a
static host serves as they are — the page, `player.js`, `worklet.js`,
the `.wasm` and a `.json` with the score baked to slot changes at the
worklet's 128-frame quantum; `test/test_online.py` opens the page in a
**headless Chrome**, has the same worklet render a second through an
`OfflineAudioContext`, and holds the frames to `run_native` after the
one rounding the browser owns (doubles to floats) — twinkle, twoknobs
and gyre (stereo), a second of audio each and 17 s for the three;
skips naming the tool without Chrome.
An unfolding score is refused with the reason (a performer in the
browser is C's question).  Twinkle's site is 15 KB.  Two things a
headless Chrome does *not* do, found the hard way and written into the
test: render an offline context under `--virtual-time-budget`, or stay
open without its own `--user-data-dir` while a desktop Chrome is up.
*Heard at the desk, 2026-08-29, Henri, after the two-line serve:*
**"Se toimii.  vieläpä oikein hyvin."**  The live path — the button,
`AudioContext({sampleRate})`, the speakers — which the gate does not
walk, walked by the one person who could.

**C. Change it, hear the change — the big thing, and it is not wasm.**
A change to the text means parse → typecheck → extract → emit →
compile, and every stage before the compiler is Python — pure Python,
measured: `gestate/` imports nothing outside the standard library on
that path (`mido`, `sounddevice`, `pygame`, `cairosvg` are the host's).
`graph_of` on twinkle is 1.2 s native.  Three readings:

* **C1 — the front end in the browser, and a direct wasm emitter.**
  Pyodide runs the Python front end (about 10 MB once, and Python
  under wasm is slower, so *suspected* four to six seconds per change
  until measured); the compiler cannot come along, so the graph would
  need a second emitter that writes wasm bytes directly instead of
  LLVM text.  The graph is scalar step functions, so that is
  plausible, and it is exactly the language goal's own target
  (`doc/memory/the-language-goal.md`) — but it is a second backend to
  keep, and *kept* is the cost that matters here.  **Killed if** the
  seconds per change are too many to feel like hearing a change; an
  afternoon with Pyodide measures that before anything is built.
* **C2 — every literal is a knob.**  No recompile: the page turns the
  numbers in the file into control slots and a change is a slot write,
  which A and B already do.  Cheapest by far.  **Killed if** "change
  it" means the *song* — and for `twinkle.ges` it does: its own header
  says *the song (bottom) is the part to play with*, and `n 60 ++ n 62`
  is the performer's business, which is Python.  A knob answers the
  instrument, not the tune.
* **C3 — a compile server.**  Already killed by question 2: a process,
  a bill, a fence, and a laptop that cannot stay online.

C is where the card's size lives, and picking between C1 and C2 is not
a session's call: C2 narrows the `because` ("change it") and C1 adds a
backend the tree keeps.  A and B are workable today, and together they
are worth having under either reading of C — a page that plays a file
and lets nobody change it is still the stranger test's *way in*, and it
is the half of run two that cost fifteen minutes.

## Done

*Nothing yet.*
