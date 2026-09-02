# audiovisual-gallery — a gallery of controllable audio-visual experiences

    status   open — 2026-09-02, off the shelf: the measurement his
             green light was conditional on came back green, §"The measurement"
    because  "people do not currently see with ease, without
             installation, what gestate can create.  And it's a bit sad
             situation there." — Henri, 2026-09-02, asked for the
             problem behind his own sentence.  What the tab shows is a
             smaller gestate than the one at this desk, and nobody
             chose the difference: six pieces already on the site
             declare a picture the tab drops on the floor, three more
             cannot be played there at all, and saving was answered
             *in* on 2026-08-29 and does not exist there.
    asked    Henri, 2026-09-02, at this terminal.  The idea arrived
             naming a mechanism — "What if we brought the wasm -side to
             match the features in clap plugins?  But put this into the
             later/ -directory if you record it." — and the goal came
             an hour later, when the card asked which of two readings
             it was: **"I think I'd like to provide a gallery of
             controllable audio-visual experiences.  It's a bit
             different goal than with clap, but same mechanism would
             fullfill it."**
    see      card:online.md §"The pieces" — B2's refusal of the three
             hands-only pieces, and C2's knobs; the fourth reading
             offered on 2026-09-01 and not picked was *a keyboard in
             the tab*, which is one row of the table below
             roadmap.md §"The substrate is built" — the plugin's second
             tab, the seed as a parameter, "one fold, two readers"
             spec/substrate.md — what a substrate is
             doc/manual.md §"clap/" — where the plugin shell lives

## What this is

**A gallery, and the pieces in it are controllable and seen as well as
heard.**  Not a plugin, not a port, not a homepage: fifty-odd pages
already exist at `cheery.github.io/gestate`, one per piece, and each
plays.  This card is what they are missing to be *experiences* rather
than recordings you cannot stop.

**The mechanism is already in the tree, on the other shell.**  That is
his own observation and it is what makes the card small rather than
large: `shell/clap/` — 5,346 lines of Rust across eight modules —
already answers every one of these questions for a DAW, because CLAP
asks them.  Parameters, notes in, saved state, and a window that draws
the piece's own canvas beside its knobs.  The goal is not CLAP.  CLAP
is simply where somebody already had to write down what a controllable
audio-visual thing needs, so the list does not have to be invented.

**One graph, two shells.**  `audiollvm.emit` writes the graph once; the
plugin and the page are two things built around that one text, and
neither knows about the other.  Every gap below is where one shell was
built and the other was not.

## Found by looking

Measured 2026-09-02, by a session, reading `shell/clap/src/*.rs`,
`gestate/online*.{py,js,html}` and `examples/audio/`:

| what CLAP asks | the plugin | the tab | pieces waiting |
|---|---|---|---|
| `clap.gui` — draw the piece | knobs **and the substrate**, second tab | a slider; no canvas | **6** |
| `clap.params` — turn it | host-automatable | a slider beside the declaring line | 5 |
| `clap.note-ports` — play it | notes in from the host | nothing | **3** |
| `clap.state` — keep it | save and load | nothing | all |
| `clap.audio-ports` — hear it | out, channels from `out_channels` | yes | — |

**The picture is the row this card turns on, and it is already
written.**  Six pieces in `examples/audio/` declare a substrate —
`chopin`, `envelope`, `lantern`, `scoped`, `spectrum`, `substrate` —
and none of them is one of the hands-only three, so **all six are live
on the site right now, playing their audio with their visual half
dropped on the floor.**  A substrate is a value (`substrate : Sig Sub`,
`spec/substrate.md`), built from smaller ones by ordinary functions and
interpreted at frame rate; `roadmap.md` calls the plugin's version *one
fold, two readers*.  The tab has the fold and one reader.

**And two rows are already written down as refusals rather than gaps**,
which is the difference between a wish and a defect:

* `clap.note-ports` — `online._control` refuses `arpeggiator`, `jazz`
  and `ladder` with *"this piece plays what your hands hold… a tab with
  no keyboard has nothing to play"* (`card:online.md` B2).
* `clap.state` — question 5 of `card:online.md`, answered by Henri
  2026-08-29: *"tallennus ilman palvelinta, käyttäjän omiin
  tiedostoihin jotka hän valitsee itse."*  Saving is in the answer and
  not in the page; `grep` for `save` or `download` across `online.js`
  and `online.html` returns nothing.

## Questions

**1. What is the problem?**  *Answered 2026-09-02, and the answer
replaced the fix the ask arrived as:* **"people do not currently see
with ease, without installation, what gestate can create.  And it's a
bit sad situation there."**

**1b. Which "what gestate can create" — the pieces, or the language?**
The card offered two readings: a *gallery* one (the site's index and
writing are what a stranger cannot read, and no shell work is needed)
and a *shell* one (the tab is a diminished gestate).  *Answered
2026-09-02, and it is neither exactly:* **"I think I'd like to provide
a gallery of controllable audio-visual experiences.  It's a bit
different goal than with clap, but same mechanism would fullfill it."**
A gallery, yes — and the thing on show is not the piece list but what a
piece *is* when you can turn it and watch it.  So the shell work is the
gallery work, and the two readings were a false split the card made.

**2. How much of the table?**  Still open, and it is the size question.
The rows are independent and each closes on its own; the pieces-waiting
column is the honest order — the canvas first at six, then notes at
three, then state.  *The session's default, marked as its own:* the
`clap.gui` row alone, because it is the largest count, it is the word
*visual* in his sentence, and it needs nothing from the person visiting
— unlike notes, which need a keyboard, and state, which needs a file
picker.  **Open — his.**

**3. Is a `.clap` whose DSP is the wasm module part of this?**  A
plugin loadable in a DAW without a Rust build.  *Not this card's
default:* it buys distribution rather than capability, the Rust build
exists and works, and a DAW is not where somebody who has installed
nothing is standing.  Recorded so it is refused rather than forgotten.
**Open — his.**

**4. What does a session do on day one?**  **A measurement, and it
needs no decision from him.**

*Corrected the same hour it was written.*  This section first said the
substrate is a value the graph already computes.  It is not, and the
difference decides the card's size: `spec/substrate.md`'s canvas is a
**second program**, serialized by `gestate.crust.serialize` and forced
on the *window's* thread while the audio graph runs on the audio one —
`shell/clap/src/engine.rs`, `struct Substrate`, *"a half of the file the
compiler does not fold into the graph, sent as machine code instead of
as a result."*  So a tab that draws a canvas needs a **G-machine in the
browser**, not a field off the module the page already has.

That is cheaper than it sounds and it must not be assumed: `crust` is
the G-machine's pure core in Rust — 2,416 lines, held against
`gmachine.py` as its reference — so this is an existing crate **built
for another target**, not a second implementation kept, which is the
cost `card:online.md` C1 was stood down for.  Rust's wasm target is one
`rustup target add wasm32-unknown-unknown` away and **is not installed
on this machine** (`rustup target list --installed`: `x86_64` only), and
toolchain installs are his.

So day one is: add the target, build `crust` for `wasm32`, force one of
the six substrates in a browser, and time a frame.  *Unmeasured, and
nothing below it should be believed until it is:* if it builds and a
frame is cheap, the row is a session's work and the six pieces are
their own test set — a fold drawn in the tab is checkable against the
plugin drawing the same fold on the same frame.  If it does not, the
row is dead and nobody had to decide anything to find out.

## The measurement

*Measured 2026-09-02, the same day the card was written.  Henri, giving
the word: "go."  The question is Q4's: does `crust` — the G-machine's
pure core in Rust — build for `wasm32`, and can a browser force a
substrate at frame rate?*

**It builds, first try, and it is small.**

    rustup target add wasm32-unknown-unknown     already cached, instant
    cargo build --release --target wasm32-unknown-unknown --lib
                                                 Finished in 1.59s
    crust.wasm                                   163,929 bytes, imports: none

Zero imports means the page supplies the machine *nothing* — no host
functions, no glue.  That is the crate's zero-dependency rule paying
out, and its own `Cargo.toml` predicted the day: *"the crate stays
buildable the day a plugin shell needs it."*  For scale, C1's Pyodide is
10 MB and this is 0.16 MB.

**All six pictures serialize, and they are small too.**
`export.substrate_of` already produces exactly the payload a page would
carry — the program text, the entry, the 14 `Sub` tags, the channels:

    scoped 4,289   substrate 9,184   spectrum 11,285
    lantern 14,783   chopin 15,770   envelope 17,436   bytes

So a page costs **164 KB once, plus 4–17 KB per piece**.

**And the module runs a real one.**  `crust_load` accepted `scoped`'s
program under `wasmtime` and `crust_force` reached `Machine::show`,
which then refused it — *"show: unexpected node Sig(1)"*.  That refusal
is correct and is the finding below: `substrate : Sig Sub` is a
**signal**, and `show` prints values.

**A frame is not the risk.**  Measured through `gui.Substrate`, which is
the *Python* G-machine — the slow reference `crust` is a Rust mirror of,
held equal by `test_crust.py`:

| piece | a frame, in CPython | shapes |
|---|---|---|
| scoped | 0.06 ms | 1 |
| substrate | 1.81 ms | 3 |
| spectrum | 5.97 ms | 16 |
| chopin | 6.12 ms | 10 |
| lantern | 6.22 ms | 17 |
| envelope | 8.74 ms | 43 |

A 60 Hz budget is 16.7 ms and the heaviest piece fits twice over **in
the slow implementation**.  *Marked as the session's, and as a bound
rather than a number:* `crust` in wasm was not timed per frame, for the
reason below — what is measured is that the work itself is small enough
that the implementation cannot be the problem.

### What is missing, and it is a task rather than a risk

**There is no C entry point that drives a picture.**  `crust_force`
forces and prints, and a substrate is a signal.  The stream seam
(`crust_stream_open`/`_pull`) is shaped for *scores* — it takes
`cons_tag`, `nil_tag`, `tuple3_tag` and yields events
(`spec/dynamicscore.md` stage two).  The plugin does not use either: it
links `crust` as a Rust crate and walks the `Sub` value with
`gestate_panel::substrate::SubTags`.

So a page needs a small Rust shim exposing *advance one frame, hand me
the shapes* — beside `crust`, compiled with it, the same walk
`shell/clap/src/gui.rs` already performs in its 574 lines.  That is
ordinary work in a language the tree already builds in, and it is **not
a second implementation kept**, which is the cost `card:online.md` C1
was stood down for.  Day one is that shim.

## How it came off the shelf

**It arrived shelved, was named as debt rather than sediment, and came
off the shelf the same day on a condition he set in advance** —
`board/README.md` §"The priority", *is this waiting on an event, or on
me?*

*People do not currently see with ease* was true yesterday and does not
resolve by waiting, so nothing about this card wakes on its own.  What
it waits on is Q2, and Q2 is his.  That makes it debt by this board's
own definition, and debt belongs in a decisions batch rather than in a
pile that is read past.

**And it became workable during the sitting it was written in**, then
he pulled it.  When the card arrived, day one needed a decision only he
could make.  With Q1 and Q1b answered and Q2 carrying a default, what
was left was a measurement — and asked whether that measurement needed
him anywhere, he answered, 2026-09-02:

> **"if the measurement looks green light, you can take the card from
> later/ shelf and work on it.  I give that green light as well then."**

**So this card waits on exactly one thing, and it is not a person.**
Build `crust` for `wasm32`, force one of the six substrates in a
browser, time a frame.  Green, and the card comes off the shelf without
asking again — that is the pull, given in advance, and the trigger is
the measurement rather than his attention.  Red, and it stays here with
the number that killed it written in, which is worth more than the card
was.

*One thing inside the measurement is still his and is named so it is
not taken by assumption:* `rustup target add wasm32-unknown-unknown` is
not installed on this machine, and toolchain installs have been his.
It needs no `sudo` and costs nothing; it is named because it is an
install and the rule is that installs are said out loud, not because it
is in doubt.

**Order, and it is the board's not the card's:** `card:ungated-fixes.md`
batch 11 is the day this was written on, and today's due work is
finished before a shelved card is pulled.
