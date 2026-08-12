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

Gestate is a source tree you run **in place**.  There is no
`pip install gestate`, no packaging step and no build before the first
sound: the language, the type checker, the score layout, the offline
renderer and the documentation generator are pure Python and import
only the standard library.  Everything installed below buys a
*backend*, and each one states what it costs to go without.

### Ubuntu, from nothing

```sh
sudo apt install git python3 python3-venv python3-pip \
                 clang binutils pkg-config \
                 libasound2-dev libportaudio2 \
                 libx11-6 libxcb1 libxkbcommon0 libxkbcommon-x11-0 libgl1

curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh   # then: . "$HOME/.cargo/env"

git clone <this-repo> gestate && cd gestate
python3 -m venv .venv && . .venv/bin/activate
pip install pytest mido python-rtmidi sounddevice

python -m gestate.audioperform examples/super/dubgate.ges        # it should sound
```

**Rust comes from `rustup`, not from `apt`.**  `Cargo.lock` is version
4, which wants cargo 1.78 or newer, and Ubuntu's own package has been
older than that for the whole life of a release.  A too-old cargo fails
on the lock file rather than on anything you wrote, which is a confusing
first five minutes.

### What each piece buys, and what you lose without it

* **`clang`** — the native engine, and the difference is not
  subtle.  `audiollvm` emits LLVM IR as text and shells out to `clang`;
  there is no `llvmlite` and none is wanted.  Without it every render
  falls back to the reference interpreter, which is *bit-identical* and
  about a thousand times slower: `examples/audio/quartet.ges` is three
  minutes of music, under a minute of generated code, and roughly a day
  and a half of interpreter.  Nothing fails — it simply takes the long
  way, and real-time playback stops being possible.

* **`libasound2-dev`** — the C audio host, and **this is the one that
  degrades quietly**.  `gestate/host.c` is compiled at first use and
  looks for `alsa/asoundlib.h` on disk; finding it, the render loop runs
  in C with no Python in the audio path.  Missing it, the header is not
  there to compile against, `Host.has_device` is false, and the editor
  says *"no C audio host; using the Python driver"* and plays on through
  a pipe to `pw-play`.  You get sound either way.  You do not get the
  latency.

* **`libportaudio2`** — the PortAudio callback path, which is the right
  answer for latency when the host is not driving.  The `sounddevice`
  wheel does **not** bundle a library on Linux: it dlopens the system
  `libportaudio.so.2`, so pip alone is not enough.  Without it,
  `audiolive` falls back to a pipe to `pw-play`, `paplay` or `aplay` —
  whichever is on `PATH` — where the player's back-pressure is the
  clock.  That path needs no package at all and is why a bare machine
  still makes noise.

* **`cargo`** — the editor's window, the CLAP export and `crust`.  The
  window is Rust (`shell/editor`), loaded through `ctypes` as a
  `cdylib`, and **it builds itself on first launch**: the first
  `python -m gestate.workbench` spends a minute or two in `cargo build
  --release` and every later one starts instantly.  Without cargo the
  editor refuses with the command to run by hand; the players and the
  suite do not care.

* **The X11 runtime libraries** — `libx11-6`, `libxcb1`,
  `libxkbcommon0`, `libxkbcommon-x11-0`, `libgl1`.  These are the
  `.so`s `baseview` dlopens when the editor opens a window, and an
  Ubuntu *desktop* already has every one; a server or WSL image has
  none, which is the machine this list is written for.  No `-dev`
  packages are needed — they are opened at run time, not linked at
  build time.

* **`mido` and `python-rtmidi`** — a live MIDI keyboard and `.mid`
  writing.  `mido` alone has no way to open a port: the backend is
  `python-rtmidi`, and without it `audiomidi` reports no MIDI on this
  machine rather than failing.  `--midi` takes an index or a substring
  of a port name, and naming one that matches nothing prints the
  numbered list of what is plugged in.

* **`binutils`** (`ar`, `objcopy`) — used by `gestate.export` to build a
  `.clap`.  `build-essential` pulls it in, and so does almost anything
  else; it is listed because a minimal image genuinely lacks it.

**Neither `numpy` nor `pygame` is a dependency, and neither should be
carried across.**  Nothing in `gestate/` or `test/` imports numpy — the
tests that assert a filter's slope write their own DFT rather than take
it.  `pygame` is reached by one obsolete module and by nothing a new
installation needs: a program's canvas is drawn by the editor's canvas
tab and by the plugin's, both of which are Rust and want nothing from
it.

### Check that it worked

```sh
python -m pytest                    # everything: about half an hour
python -m pytest -m "not golden"    # without the 22 that are about this machine
```

The suite is around 2,150 tests and takes **about half an hour**.  Note
what the `golden` marker is and is not: it deselects 22 tests, so it is
not a way to make the run shorter.  Those 22 re-render a committed
buffer through the interpreter and compare it sample for sample, which
makes them the only part of the suite that is a claim about *one
machine* — bit-exactness through `sin` and `exp` holds where the buffer
was made, and each `.samples` file records the `libm` it was made
against.  If they are the only thing red on a new box, that is the
expected failure and not a broken install.

**Tests never open the sound card**: `test/conftest.py` makes both
routes to it raise and names the test that tried; `GESTATE_TEST_AUDIO=1`
opens them again.  Anything whose backend is missing skips rather than
fails, so a green run on a bare machine is a smaller claim than a green
run on a full one — if you want the engine checked, install `clang`
before reading the result.

Two more that ask for nothing at all, as a first proof of life:

```sh
python -m gestate.typecheck examples/closure.ges
python -m gestate.audioperform examples/audio/sine.ges --oracle -o sine.wav
```

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

The logo: an egg, and inside it a signal growing to full amplitude —
carried to term while already sounding.
