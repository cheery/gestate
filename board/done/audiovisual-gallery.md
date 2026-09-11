# audiovisual-gallery — a gallery of controllable audio-visual experiences

    status   done — 2026-09-11
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

## Day one, and what it left

*2026-09-03.  Q4's answer was "day one is that shim", and this is the
shim: `shell/web`, a crate whose whole content is a C ABI over the
canvas driver the plugin's window already turns.*

**It keeps no walk of its own, and that was the point.**  The driver is
`gestate_panel::canvas::Canvas` and the walk under it is
`gestate_panel::substrate` — the same pair `shell/clap` uses, held to
`gestate/gui.py` tree for tree by `substrate_parity.rs`.  Under
`--features substrate` the panel's only dependency is `crust`, so the
whole stack crosses to `wasm32` with nothing added.  What the shim
supplies is the *seam*: a page cannot call a Rust method, so the loop —
one instant, one picture, one press — is offered as ten C functions and
one flat `i32` buffer.

**All six pieces draw in wasm exactly what the reference draws.**

| | a frame, in wasm | records | (the card's CPython bound) |
|---|---:|---:|---:|
| scoped | 0.18 ms | 1 | 0.06 ms |
| substrate | 0.26 ms | 4 | 1.81 ms |
| chopin | 0.48 ms | 10 | 6.12 ms |
| spectrum | 0.59 ms | 16 | 5.97 ms |
| lantern | 1.14 ms | 19 | 6.22 ms |
| envelope | 1.98 ms | 43 | 8.74 ms |

    gestate_web.wasm    221,228 bytes, imports: none

**So the bound the card marked as a bound is now a measurement**, and it
came in better than the thing it bounded: the heaviest piece is 1.98 ms
in the target that will actually run it against 8.74 ms in the reference
it was estimated from — eight times inside a 60 Hz budget.  The module
is 221 KB against `crust`'s 164 KB; the walk and the driver cost 57 KB.

`test/test_gallery.py` is the end-to-end: the module built for
`wasm32`, driven under `wasmtime` through nothing but pointers into its
linear memory, its picture compared line for line with what `gui.py`
draws.  Twelve tests — the six pieces, a channel keeping the id the
picture carries, an arrival moving the fold, a hand reaching the
program and back, a program that is not a picture refused with a
sentence, and the frame.  `shell/web/src/tests.rs` holds the wire
natively, against the fixtures `shell/panel/tests/` already carries.

**One correction, and it is worth keeping.**  The first run had four of
six matching and two disagreeing about *channel ids* while every
rectangle agreed.  Both readings were correct: the shell forces the
declarations before the program runs and the test's own reference did
not, which is the two-readings problem `export.substrate_of`'s
docstring is written about, arriving in a test rather than in a shell.
The fix was to make the reference `gui.Substrate` itself — the actual
reference host — rather than a walk assembled beside it.

### Day two, landed — 2026-09-04

**The page draws, and the meters came with it.**  *Henri, giving the
scope the same day the shelf question was asked:* **"I think that
meters should come with it.  The meters are cool."**  So this is the
`clap.gui` row plus the half of `clap.params` that runs the other way —
the instrument reaching the picture — and not the hand reaching the
sound, which is untouched.

**What landed.**

- `gestate/webshell.py` — builds `shell/web` for `wasm32` from Python,
  the way `audiowasm.build` builds the synth.  **One module for the
  whole gallery**, at the site root: the synth is the piece and every
  `.ges` compiles to its own, but the canvas driver is the same program
  for all of them and only the substrate it is handed differs.
- `online.canvas_of` — the payload a page opens the shell with, which
  is *the same one a plugin gets* (`export.substrate_of`), plus
  `meters`: what this file declared and therefore what it is charged
  for.
- `gestate/online-canvas.js` — the page's half of the seam.  It moves
  bytes across the C ABI and paints an `i32` array; **it keeps no walk
  of its own**, which is the whole reason day one was built the way it
  was.
- `gestate/online-worklet.js` — the meters, measured beside the samples
  because a picture *of* the sound needs the numbers on the thread the
  samples are on.  The filter bank is `gestate/host.c`'s, constant for
  constant: seven one-pole lowpasses at 110–11000 Hz, a 150 ms release,
  the peak sampled at sixteen points of a block.  Reported once every
  six quanta — 57 Hz against the quantum's 344, because the picture is
  redrawn on a frame anyway.
- `shell/web` gained **`web_list`**: a scope's trace is a `List Float`
  and the scalar wire carries `(chan, value)` doubles, so a window is
  staged and spent by the next `web_tick`.  `Canvas::advance` already
  took lists — the shim was the only thing dropping them — and it
  builds the list with the program's own `Cons` and `Nil`, so nothing
  new decides what a list is.
- `player.js` imports the canvas **dynamically**, and the generator
  writes `canvas.js` and the shared module only when something draws:
  45 of the 50 pages carry neither.

**All six draw in a real browser what `gui.py` draws.**
`test_online.py::test_the_page_draws_what_the_desk_draws` opens the
page a person opens in a headless Chrome and reads the picture back
over the wire.  `test_gallery.py` already held the *module* to the
reference under `wasmtime`; what sits between them and was checked
nowhere is **the payload this generator writes** — a tag off by one
draws a `Row` as whatever shares its number, a chan list out of order
gives a fader somebody else's channel, and both pass every test in that
file.

**And the meters move**, which a presence check would not have caught:
a bank wired to nothing reports zeros forever.  Held on a real offline
render through the real worklet — `spectrum`'s eight bands not all
silent, `substrate`'s peak above zero, `scoped`'s 128 points not flat.

| | measured |
|---|---|
| the whole site | **50 pages, 3.8 MB, 1 m 57 s** (was 2.9 MB) |
| pages that draw | 6 |
| the shared shell | 221 KB, no imports, fetched by those 6 |

**And a piece written for the gallery — `mirror.ges`, the same day.**
*Henri:* **"Lets make some nice demo that uses canvas for something
interesting and effective, then plug it to gh-pages.  Specifically
meant to show on those pages."**  So: the only file that carries all
three of the host's readings at once — a scope's trace, the eight
bands and a peak — where `lantern` had the peak, `spectrum` the bands
and `scoped` the trace and no file had ever had all three.  Which makes
it the piece where a broken feed shows.

**It has no faders, and that is the design.**  On a page a fader moves
the picture and not the sound, so a demo built around one would have
its centrepiece do nothing.  Every pixel of this face is something the
instrument said.  Both halves are gates: the three feeds are asserted
present, and so is the *absence* of any attachment, because adding a
control to it later would look like an improvement.

The sound is shaped for the face rather than the other way round — the
lead's filter opens with its own note, so a phrase climbing the scale
walks the bank instead of lighting one bar and holding it.  **Seven
pieces now declare a substrate**, against the six the table above
counted on 2026-09-02.

**What is still not wired, and it is the next row not an oversight.**
A touch on the canvas moves the *picture* and not the sound: the
gesture's writes go back in on the next tick, and `CanvasProgram`'s
`bridge` is still empty.  That is `clap.params` in the table, and Q2 is
still his.  F197's frame clock is also still uncrossed — `web_tick`
takes a pulse tag and the page passes none, so a substrate that moves
on `Tick` alone would stand still; no piece in `examples/audio/` is one,
which is the honest half day one already recorded.

**And one thing found on the way, which is `fixme.md` F197.**  The
canvas's frame clock does not cross.  `gui._crossing` sends `Tick`'s tag
and the `wallclock` channel; `export.substrate_of` sends neither, and no
host outside `gui.py` pulses at all — `Panel::tick_canvas` passes
`None`.  `web_tick` takes a pulse tag already and has nothing to pass
it.  *The honest half:* no piece in `examples/audio/` was found whose
picture moves on a bare frame clock — `lantern` folds over `events` and
`envelope` reads `now`, and **both stand still in the reference host
too** — so this is a seam with no demonstrated victim, and the first
thing to write is a substrate that moves on `Tick` alone.

**Q2 is answered, 2026-09-04, and it is not the gui row alone.**
*Henri, having opened `lantern.ges` on the live site:* **"Lets not close
the audiovisual-gallery.md … I think the page could use MIDI
support."**  So the card stays open and the next row is
`clap.note-ports`.

**And that row was recorded here as a refusal, which it no longer is.**
`online._control` refuses `arpeggiator`, `jazz` and `ladder` with *"a
tab with no keyboard has nothing to play"*, and B2 of `card:online.md`
turned down *a keyboard in the tab* on 2026-09-01 as the reading not
picked.  Both rest on the same premise — that a tab has no keyboard —
and **Web MIDI is the premise being false**: a browser can be handed a
real instrument.  Whether the answer is Web MIDI, keys drawn on the
page, or the computer keyboard is his; the three refused pieces are the
test set either way, and the refusal sentence will have to be rewritten
rather than deleted, because it is true of a tab with no MIDI device
attached.

**And one thing he found by using it, which is a defect this card
owns.**  *Henri, on `lantern.ges`:* **"I tried it in lantern and the
knobs appear to work.  Not certain if they do anything there."**  They
half do, and the half is the point:

| what he can touch on that page | writes | reaches |
|---|---|---|
| the **slider beside line 40**, `warmth` | control slot 4 | **the sound** — gated (`test_online.py`) |
| the **WARMTH fader in the picture** | canvas channel `warmthChan` | **the picture only** |

They are the *same declaration* — `warmth = 0.55 ::: mkSig (wait
warmthChan)`, which `lantern.ges`'s own header calls out as one channel
the fader writes and the filter reads — split across two controls that
each do half and do not move together.  On the desk and in the plugin
they are one thing.  **On the page a person meets two of them
disagreeing**, and nothing says which is which.  That is the
`clap.params` row stated as a user-visible fault rather than as a
missing feature, and it is the argument for doing that row before or
with the MIDI one.

## What done means, and how the tab gets played — 2026-09-11

**Henri, on the flow lamp's seven days:** *"I think the
audiovisual-gallery.md could be stated to be completed, or if it's not,
it could be worked on enough to become done."*  Put the three readings
with their prices, he took the largest: **the fader and MIDI, then
done.**  So his 2026-09-04 *"Lets not close … the page could use MIDI
support"* stands as binding, and the card closes when both rows are in.

**The split fader, priced 2026-09-11 by a session.**  Still live, and
the shape is one line: a canvas touch writes into the wasm shell's own
channel map (`online-canvas.js`, `this.pending`) and the page's slider
posts `{slot, value}` to the audio worklet — two paths for one
declaration, which is why `warmth` moves the picture and the filter
separately.  On the desk `Workbench.control` bridges them **by name**:
*"the graph calls it `cutoff` because the program did, and so does the
element that writes it."*  `online.canvas_of` already computes `knobs`,
the control sources' channel names, so the map from canvas channel to
control slot is derivable where the payload is built.

**And how a tab is played.**  Put with what would kill each, his
answer: **Web MIDI, with the computer keyboard as the fallback.**  That
is this card's own argument read forward — it says the refusal sentence
must be *rewritten rather than deleted* because *"a tab with no
keyboard has nothing to play"* stays true of a tab with no device
attached, and a fallback is exactly what makes it false.  Web MIDI is
Chrome and Edge only, so the fallback is the path most visitors meet
and is not a courtesy.  `arpeggiator`, `jazz` and `ladder` are the test
set.

### The fader and its slider are one declaration, built — 2026-09-11

`clap.params` closed as a fault rather than as a feature.
`online.canvas_of` hands the page a `slots` map — every canvas channel
the synth also reads, by the control slot the worklet turns — and the
name is the bridge, the same one `Workbench.control` has always used on
the desk.  On `lantern.ges` that is `warmthChan → 4` and `glowChan →
29`, and slot 4 is exactly what the slider beside line 40 already
carried.

**Both directions, because the fault was never one control being
deaf.**  A touch on the fader turns the slot *and* moves the slider and
its readout; a slider moved by hand writes the canvas channel, so the
fader follows.  `online.js`' `turn` gained a `fromPicture` flag so the
two owners of one number do not echo each other during a drag.

Held by `test_online.py::test_a_fader_and_its_slider_are_one_declaration`
— the two slot maps are computed independently, from `knobs` and from
`canvas_of`, and compared; red at an off-by-one, 4.9 s.

**Left for done:** `clap.note-ports`, as he answered it — Web MIDI with
the computer keyboard as the fallback.

### The MIDI row is not what this card said it was — 2026-09-11

**Counted before building, and the card's own sentence was wrong.**  It
said *"the three refused pieces are the test set either way"*.  They are
the one set that cannot be:

    pieces with a voices bank          34
    whose score reads `hear holds`      3   — arpeggiator, jazz, ladder

`hear holds.keys` is in their **score**, and the page does not run a
score: `online.bake` pulls `audioperform.dynamic` forward offline and
ships every control change as data, which the worklet replays.  A score
whose content depends on what a hand holds *now* cannot be baked.

**A session then called that the C row and it was wrong** — caught the
same hour by Henri, who did not believe it: *"I'm a bit surprised that
pyodide would be needed there.. I thought that clap plugins work same
way now, and it doesn't require python to work, or does it?"*  They do,
and it does not.  `shell/clap/src/dynscore.rs` carries the **program**
(`engine::Program`) and forces it on `crust`, a G-machine in Rust, with
no Python at run time; `descriptor.rs` is written by `python -m
gestate.export` at *build* time, which is exactly what
`online.generate` is to a page.

**And the G-machine is already in the tab.**  `shell/web` depends on
`crust` and builds for `wasm32` today — its own header says *"only a
G-machine could run it and the tab had none"*, past tense.

So the mistake was reading C1 as *any* score running in the browser.
C1 is **compiling `.ges` text** in the browser, which needs the front
end; forcing an already-compiled score's stream needs the machine and a
serialized program, and both are there.  What is actually missing is
smaller and is wiring rather than a backend: `crust` lives in the
**canvas** module and the sound lives in the **worklet**, so a score
forced in one has to reach control slots in the other.

**What is reachable today without any of that** is the larger half
anyway.  The other thirty-one have banks and do not read the hands, so
notes can be fed into a bank
*alongside* the running score — which is what `clap.note-ports` means
in CLAP: **notes in from the host**.  The worklet already runs the real
compiled synth with control slots, so a note is a free voice and three
slot writes; `turn(slot, value)` is the seam and it already exists.

**Henri, 2026-09-11**, given the three readings: **play along with the
running piece.**  Thirty-one pieces playable rather than three, and the
hands-only three keep a refusal — rewritten to name the real reason,
which is not *a tab with no keyboard* but *their score reads the hands
and this page bakes*.

### Notes in from the host, built — 2026-09-11

**`clap.note-ports`, as he answered it**, and the order was chosen for
what most visitors meet: the letter keys first, Web MIDI on top of the
same note path.

- **`online._banks`** hands the page each `voices` bank as the control
  slots its voices are made of, in `channels_of`'s order — which is the
  order `Allocator` numbers its own voices in, so a note let go finds
  the voice it began on.
- **The worklet owns the allocator**, because only it knows what sample
  it is on and `gateAt`/`offAt` are sample indices.  A free voice
  released-longest-ago first, `Allocator._pick`'s rule; **every voice
  busy refuses** rather than steals, so playing along cannot cut a note
  the score is holding.
- **A voice goes back to the score two seconds after its release** —
  not at the note-off, because the envelope reads `offAt` after the
  gate falls and handing the slots back then cuts the release off in
  the air.  Without it, one note played would take a voice off the
  piece for good.
- **The payload is what a keyboard can say**: key and velocity, the
  rest zero.  That is `spec/annotations.md`'s path 1, honest here for
  the reason it is dishonest there — a hand playing along has no marks
  to lose.
- **The tracker layout**, `audioeditor.Keyboard`'s own: `z…m` an
  octave with its black keys on the row above, `q…i` the octave up,
  Shift-Z and Shift-X to move.  Autorepeat is not a press; a note is
  not stolen from a text field; losing the page panics every voice.
- **Web MIDI is eight lines**, because it is an input and not a second
  mechanism — including a keyboard plugged in *after* the page opened,
  which otherwise plays nothing and says nothing about why.

Held by `test_online.py::test_a_bank_reaches_the_page_as_the_slots_its_voices_are_made_of`
— the voice order against `channels_of`, and the banks' slots against
the knobs' with no overlap, *a slider for a gate being a note nobody
played*.  8 s.

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

## Done — 2026-09-11

**All five CLAP rows answered, three built and two refused with their
reasons.**  `journal.md` §"The gallery's last two rows, and one of them
was not the row" tells the story.

| what CLAP asks | how it stands |
|---|---|
| `clap.audio-ports` | built, day one |
| `clap.gui` | built, day two — all six pieces draw, meters with them |
| `clap.params` | built 2026-09-11 — a fader and its slider are **one declaration** |
| `clap.note-ports` | built 2026-09-11 — notes into any bank, letter keys and Web MIDI |
| `clap.state` | **refused here**: saving is `card:online.md` question 5's answer and belongs to that card, not this one |

**And the `because` is met**, which is the test that matters: *"people
do not currently see with ease, without installation, what gestate can
create."*  Thirty-four pieces on the site draw their picture, are
turned by controls that agree with themselves, and can be played along
with from a laptop keyboard.

**What this card deliberately leaves**, each with somewhere to go:

* **The three hands-only pieces** — `card:hands-in-the-tab.md`, minted
  at his ask, with the obstacle measured and the wrong answer a session
  gave first written down beside the right one.
* **Saving** — `card:online.md` question 5, answered there and unbuilt
  there.
* **A substrate that moves on `Tick` alone** — the seam with no
  demonstrated victim, §"Day two, landed".
