# Installing gestate, thoroughly

The README's install section is five commands and a proof of life;
this page is the reasoning behind them — what each package buys, what
degrades without it and how, and what a test run does and does not
claim.  Nothing here is required reading before the first sound.

Gestate is a source tree you run **in place**.  There is no
`pip install gestate`, no packaging step and no build before the first
sound: the language, the type checker, the score layout, the offline
renderer and the documentation generator are pure Python and import
only the standard library.  Everything installed below buys a
*backend*, and each one states what it costs to go without.

## Ubuntu, from nothing

```sh
sudo apt install git python3 python3-venv python3-pip \
                 clang binutils pkg-config \
                 libasound2-dev libportaudio2 libx11-dev \
                 libx11-6 libxcb1 libxkbcommon0 libxkbcommon-x11-0 libgl1

curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh   # then: . "$HOME/.cargo/env"

git clone <this-repo> gestate && cd gestate
python3 -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt

python -m gestate.audioperform examples/super/dubgate.ges        # it should sound
```

**The `.venv` lives in the tree and is the whole Python side of the
installation.**  `requirements.txt` is the list (four packages, each a
backend the suite skips without); `.gitignore` already ignores the
directory; `tools/gestate-editor` — and so the desktop icon — prefers
it automatically when it exists.  Delete the directory and the two
lines above remake it.  What a venv cannot hold is the system quarter:
`clang`, `cargo`, ALSA and PortAudio stay with `apt`, which is why the
one command block above has three layers.

**Rust comes from `rustup`, not from `apt`.**  `Cargo.lock` is version
4, which wants cargo 1.78 or newer, and Ubuntu's own package has been
older than that for the whole life of a release.  A too-old cargo fails
on the lock file rather than on anything you wrote, which is a confusing
first five minutes.

## What each piece buys, and what you lose without it

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

* **`libx11-dev`, and it is a build dependency.**  The editor calls two
  X11 functions directly — `XChangeProperty` for the window's icon and
  name, `XkbSetDetectableAutoRepeat` for the piano (F106) — and
  `#[link(name = "X11")]` makes the linker want `libX11.so`, the
  unversioned symlink that only the `-dev` package ships.  Without it
  `cargo build` fails outright: **no editor at all**, rather than an
  editor missing something.

  A desktop that has ever built anything against X tends to have it
  already, which is exactly why this line was missing for four days.
  Henri hit it on a fresh 26.04 install, 2026-08-17.

* **The X11 runtime libraries** — `libx11-6`, `libxcb1`,
  `libxkbcommon0`, `libxkbcommon-x11-0`, `libgl1`.  These are the
  `.so`s `baseview` dlopens when the editor opens a window, and an
  Ubuntu *desktop* already has every one; a server or WSL image has
  none, which is the machine this list is written for.  These are
  opened at run time and need no `-dev` package — **which is what this
  entry used to claim about X11 as a whole**, written 2026-08-12 and
  true for one day: the window grew its exterior on the 13th and linked
  against X11 to do it, and nothing re-read the sentence.

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

## A desktop icon

One command writes the launcher and the icons a desktop looks for:

```sh
python -m gestate.workbench --desktop
```

That puts `gestate.desktop` in `~/.local/share/applications` with
`StartupWMClass=gestate` — which is how GNOME's dock matches a running
window to its entry, and without which it shows a gear — and the egg
under `~/.local/share/icons/hicolor`, as PNGs at 16, 32, 48, 128 and
256 px and as the SVG itself.  **Run it again after moving the
repository or the venv**, because `Exec` pins both.

By hand is three lines, if you would rather point at the tree than
copy out of it.  `tools/gestate-editor` opens the editor from the
tree — the file it is handed, or `untitled.ges` when it is handed
nothing:

```
[Desktop Entry]
Type=Application
Name=Gestate
Exec=/path/to/gestate/tools/gestate-editor %f
Icon=/path/to/gestate/doc/gestate.svg
Terminal=false
Categories=AudioVideo;
StartupWMClass=gestate
```

Save it as `~/.local/share/applications/gestate.desktop`; for an icon
on the desktop itself, copy it there, `chmod +x` it, and mark it
trusted (`gio set <file> metadata::trusted true` on GNOME).

Either way you get the same egg, and so does the window itself: it
carries the icon in `_NET_WM_ICON` for the taskbar and alt-tab of a
desktop that never read a `.desktop` file at all.  All three come from
`gestate/icon.py` — see `fixme.md` F148 for the week they did not.

## Check that it worked

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

**Tests open real windows**, and on a workstation those windows land
over whatever you are typing.  `test/test_editor_abi.py` drives the
editor across its C boundary, which is a claim about a Rust-owned rope
and a Python orchestrator agreeing — a fake window would only test the
fake.  `tools/toolbox.sh` says whether this machine has the bench tools
that keep that out of your way, `--install` fetches them, and none of
them is needed to build a program or hear one.

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
