<p align="center">
  <img src="doc/gestate.svg" width="200" alt="gestate — a signal carried to term">
</p>

<h1 align="center">gestate</h1>

<p align="center"><em>A language for programs that develop while they are already alive.</em></p>

Gestate is a small functional language for sound, music and moving
pictures.  A program is a handful of signal declarations; the compiler
checks them into a **static graph** — fixed memory, bounded work per
sample, no allocation after the first instant — and runs it native
through LLVM.  Because the graph is exactly what the source says, an
edit while the program plays **migrates the running state**: the
oscillator keeps its phase and the filter its memory while the sound
changes under your hands.  That is the logo, and the name.

```
env : Sig Float
env = perc 6.0 (gateOn (!(x => x < 0.5) (phase 2.0)))

sound : Sig Float
sound = 0.4 * sine 220.0 * env
```

`!` lifts an ordinary function over signals; everything else is
functions and values.  Scores, polyphonic voice banks, MIDI in, a tape
echo you can gate, and a canvas the same program draws on are all
library and language, documented down to the measured decibel.

## Install it

Gestate is a source tree you run **in place** — no `pip install`, no
packaging step, no build before the first sound.  On Ubuntu:

```sh
sudo apt install git python3 python3-venv python3-pip \
                 clang binutils pkg-config \
                 libasound2-dev libportaudio2 libx11-dev \
                 libx11-6 libxcb1 libxkbcommon0 libxkbcommon-x11-0 libgl1

curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
. "$HOME/.cargo/env"        # or open a new terminal; without this there is no cargo

git clone https://github.com/cheery/gestate.git gestate && cd gestate
python3 -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt

python -m gestate.audioperform examples/super/dubgate.ges        # it should sound
```

Two notes worth their lines: **Rust comes from `rustup`, not `apt`**
(Ubuntu's cargo is too old for the lock file, and fails on it rather
than on anything you wrote), and the core is pure Python — everything
`apt` installs above buys a *backend*, and missing ones degrade
politely rather than fail.  What each piece buys, what you lose
without it, a desktop icon, and what a test run does and does not
claim: **[doc/install.md](doc/install.md)**.

## Hear it

```sh
python -m gestate.audioperform examples/super/dubgate.ges      # play it
python -m gestate.audioperform examples/super/dubgate.ges -o dub.wav --seconds 16
python -m pytest                                            # the suite
```

Try `examples/audio/violin.ges` for a concert soloist lost in a sound
system, or anything under `examples/beginner/` beside its lesson.

## Edit it while it sounds

```sh
python -m gestate.workbench examples/super/dubgate.ges
```

**The first run of this builds the editor** — `cargo build --release`,
ten seconds to a couple of minutes depending on the machine — and every
later one starts instantly.  It says so while it works, and it needs
`cargo` on the `PATH` (see the install block above).

The workbench is the editor, and it is the room the language was built
for: the file, its knobs drawn **beside their own declarations**, a
piano, and the sound — all at once.  `Ctrl-S` applies an edit without
stopping the note that is ringing, because the graph is exactly what the
source says and the running state migrates across the change.

<p align="center">
  <img src="doc/workbench2.png" width="640"
       alt="a synth playing: a knob in the margin beside the declaration
            that makes it, a voice bank showing two of its four voices
            sounding, and the transport running in the status line">
</p>

Two things in that picture are facts the text cannot state. The slider
on line 18 is `volume`'s own channel, at `volume`'s own line — not a
panel you read against the code. And `2/4` beside the bank is how many
of its voices are sounding **now**: `voices example 4` is already in the
source, so a window that only repeated it would be decoration.

The eye gets the same seat the ear has.  `scope "post" s` passes its
signal through untouched and keeps the last window of it on screen;
`spectro` is the same node wearing a spectrum.  Written as `sink`, a
watch is one appended line that touches nothing it watches, and its
picture stands on that line:

<p align="center">
  <img src="doc/workbench4.png" width="640"
       alt="three sink lines in a playing score — two scopes and a
            spectro — each with its own picture in a box under its own
            line: the bass and the chord as waveforms, the top voice as
            a spectrum, with the bank counters in the margin beside the
            voices below">
</p>

The label is in the file, so the diagnosis you set up on Tuesday is
still on the screen on Wednesday — and deleting the line takes its
window with it, because it was never anywhere else.

A canvas is the same idea with no diagnosis in it.  `substrate : Sig
Sub` is a picture the program builds the way it builds a sound — a
value, out of ordinary functions — and the window walks it at frame
rate beside the score it belongs to:

 ![Op. 28 No. 4](doc/chopin.gif)

<p align="center"><sub><em>Op. 28 No. 4 on its own canvas.  The disc is
the output's peak breathing; the eight lamps below are the voice bank's
hammers, each brightening when its voice is struck and shrinking as the
note ages.  (<a href="doc/chopin.gif">doc/chopin.gif</a>)</em></sub></p>

Nothing there is a visualiser reading the audio from outside.  `peak`
and the voice ages are channels the program *declares*, the host writes
them the way it writes a knob, and `discOf` and `emberOf` are ordinary
functions of them — twelve lines of `chopin.ges`, above the score they
are watching.

And a picture can be **played backwards into the file**.  `notes
<expr>` stands a piano roll of that expression on its own line; take
hold of a note in it and it follows your hand, and where you let go is
where the file says it was all along:

 ![dragging a note](doc/editing.gif)

<p align="center"><sub><em>A note dragged in the roll on line 109, and
`holdBar 45` becoming `holdBar 42` on line 103 as it moves.  One
number changes — no reflow, no reprint — and the sound follows without
the file on disk being touched.  The status line says what it did and
how many voicings share the note.
(<a href="doc/editing.gif">doc/editing.gif</a>)</em></sub></p>

That is the rule the whole editor is built on and the only one it has
about widgets: **a widget is a view over a span of source, and dragging
it is a text edit.**  The knob rewrites its own declaration; the roll
rewrites one number of the phrase it draws; both are undone by
`Ctrl-Z`, because there is one document and it is the text.

There is **one mode, and it is typing**.  `Ctrl-K` opens the command
list, which is every other thing the editor can do, filterable, each with
its name and its key; a capability cannot exist without appearing there,
because the list is derived from `gestate/command.ges` the way the
reference is derived from the libraries.  A build that fails leaves the
sound playing and puts the compiler's complaint beside the line that
caused it.

<p align="center">
  <img src="doc/workbench.png" width="520"
       alt="the command list open over the source, each command with its
            arguments and its key, and a sentence under the selected one">
</p>

That list is not a menu the window maintains — it is
`gestate/command.ges` read back, so what you see is the vocabulary
itself: the argument types are what let it ask (`<int>`, `<path>`,
`<named>`), the key is the one the command publishes, and the sentence
under the selection is the declaration's own doc comment.  Adding a
capability is adding a declaration, and there is nowhere else to put one.

Two commands are the language answering about itself.  **`Tab`** asks
what fits — give it a type and it lists everything in scope that could
stand there, from inference over the text in the window rather than the
last save.  **`template`** pastes one of the language's ideas at the
cursor — a knob, a voice bank, a metronome, a tape echo, a canvas, a
piece — with its documentation left behind in the list where you read it
to choose.

## Play it

A gestate file exports as a **CLAP plugin** — one native graph, its
knobs as automatable parameters, its voice banks fed by MIDI, and its
score performed against the DAW's transport.

```sh
python -m gestate.export examples/audio/lantern.ges -o ~/.clap/lantern.clap --gui
```

<p align="center">
  <img src="doc/lantern.png" width="420"
       alt="the plugin window: CONTROLS and CANVAS tabs, a seed field, two faders and a meter">
</p>

That is `examples/audio/lantern.ges` — one file, three halves: a score
that unfolds, a synth that is compiled, and a canvas that is
interpreted.

The window has two sides and one painter.  **CONTROLS** is the
descriptor — faders, a note-routing matrix, a switch per bank for who
plays it.  **CANVAS** is the program's own picture: a file that declares
a `substrate : Sig Sub` draws it here, interpreted at frame rate.  The
blue fader above *is* the filter's cutoff — not a copy of it, the same
declaration — so dragging it moves the sound, and the DAW sees an
ordinary parameter change it can undo and automate.  The ladder beside
them is the instrument's own loudness, arriving from the audio thread.

**SEED** is the take.  A chancy piece — `lantern` draws a figure every
bar, `nightdrive` picks a road every four — is a family of performances,
and the seed says which one you are hearing.  Roll it, or type one in
and keep it: it is a plugin parameter, so the session remembers it, the
DAW can automate it, and writing the number down is enough to get the
night back.  A piece whose score is a decided list of events has no
entropy to reroll and is offered no seed.

`spec/panel.md` and `spec/substrate.md` are the design; the whole face
is software-rendered from a display list the language already speaks, so
there is no toolkit in the build.

## Read it

* **[The beginner course](doc/beginner.md)** — ten lessons from a sine
  to a piece; `doc/intermediate.md`, `doc/advanced.md` and
  `doc/super.md` continue it.
* **[The manual](doc/manual.md)** — the language, plainly.
* **[The reference](doc/ref/index.md)** — every name in every library,
  generated from the sources so it cannot drift.
* **[The specs](spec/)** — how each part is designed and why, costs
  stated; `journal.md` is the honest running account, `fixme.md` the
  defect ledger.
* **[The switches](doc/switches.md)** — every `GESTATE_*` the program
  reads.  Most are not settings: they are how it is asked where its
  time went, or made to do the slow thing on purpose so a measurement
  means something.
* **[The manifesto](manifesto.md)** — how this project is worked.  Two
  rules: do not build what nothing needs, and what is built must be
  able to say when it is wrong.

The logo: an egg, and inside it a signal growing to full amplitude —
carried to term while already sounding.
