# portable-package — the way in is Ubuntu-shaped, and other distros translate it by hand

    status   open
    because  "The installation on ubuntu is fine, but I think we need to
             think that there are other distros as well" — the way in is
             written for one distro's package names, and anybody else
             translates them by hand before hearing anything
    asked    Henri, 2026-08-17 (Claude wrote the card at his ask)
    blocked  not formally — but see "What it needs first" below; there
             is no oracle for an install today, and a package is an
             install that cannot be inspected afterwards
    see      card:installation-test.md — the sibling, and the one to do first
             doc/install.md — what a package would have to replace
             vision.md — what "accessibility" is being measured against
             README.md §Ubuntu, from nothing

## The ask

> Also thinking, appimage/snap or similar for other distros could be
> easy next step to improve accessibility of the project.

The ask named a fix, so the problem behind it was asked for rather than
guessed — three readings were on offer: *someone not on Ubuntu cannot
follow the install*, *the install is too long even on Ubuntu*, or
*there is no way to hand somebody gestate to try*.

**A (Henri, 2026-08-17).**  *"The installation on ubuntu is fine, but I
think we need to think that there are other distros as well."*

So it is the first, and the other two are explicitly not the problem:
**the Ubuntu path is not to be shortened or replaced.**  That settles
more than it looks like it does — a package is an *addition* for people
this tree currently turns away, not a new front door for everybody, and
anything that would make the source-tree install worse in order to
package it is out of scope by his answer.

## Found by looking, before it was taken

### What gestate *is* fights the usual packaging model

`doc/install.md`'s first paragraph is the obstacle, and it is not an
accident:

> Gestate is a source tree you run **in place**.  There is no
> `pip install gestate`, no packaging step and no build before the first
> sound.

And the editor **builds itself on first launch** — `cargo build
--release` from `gestate/editor.py`, because the window is Rust.  So a
package has to answer a question that a normal application does not:

**Is the packaged thing a program, or a workshop?**

* **A program.** The editor and the players, prebuilt, opening `.ges`
  files.  This is what AppImage and Flatpak are good at, and it is
  honest for someone who wants to *hear* gestate.
* **A workshop.** The tree, its examples, its specs, and a toolchain
  that can rebuild the editor. This is what the project actually is —
  `vision.md`'s claim is that you open a file, hear it, change it and
  hear the change, and *change it* means the tree is present.

The second is a strange thing to put in an AppImage and a natural thing
to put in a container image or a `distrobox`.  **That choice is the
card**, and everything below only matters after it.

### What each format costs, briefly

| | fits | costs |
|---|---|---|
| **AppImage** | one file, runs anywhere, no install, no store account | must bundle glibc-compatible everything; the ALSA/PortAudio/X11 dance is exactly the fragile part; no `apt` inside it to fall back on |
| **Flatpak** | sandboxed, real audio story (PipeWire portal), works on every desktop distro | the sandbox is the problem — a workshop wants a compiler and the user's own files; needs a manifest and a build host |
| **Snap** | Ubuntu-native, which is the distro the project already targets | least useful for *other* distros, which is what the ask is about |
| **Container image** | the workshop, exactly, and it is what `installation-test` is about to build anyway | not a desktop application; audio and display need explicit plumbing |

**The container row is worth noticing**: if `installation-test` builds a
podman image that runs the manual from nothing, then a publishable image
is nearly a by-product, and it serves the workshop reading rather than
the program reading.

### The one technical unknown

**Audio out of a sandbox.**  Everything else here is packaging paperwork;
this is the part that can fail on somebody else's machine in a way
nobody can reproduce.  Gestate reaches the card four ways — the C host
over ALSA, PortAudio, a pipe to `pw-play`/`paplay`/`aplay`, and the
CLAP plugin in someone else's DAW — and a Flatpak or Snap sandbox
changes what each of those can see. The pipe fallback is the one most
likely to survive and the one with the worst latency, which would make
a packaged gestate feel worse than a built one for the exact reason
`doc/install.md` spends a page explaining.

## What it needs first

`installation-test`, and not as bureaucracy: **a package is an install
whose failures happen on a machine you cannot look at.**  Today there is
no oracle for "did the install work" at all — three defects reached a
fresh laptop this week — and shipping a binary to strangers before there
is one moves those failures somewhere they cannot be seen or reported.
The sibling card also produces the container tooling this one would
build on.

## What the work is

The problem is settled; **program-or-workshop is the open one**, and it
is the question to bring him next.

1. Decide program-or-workshop, in one line, in this card.
2. Pick one format and build one artifact for one distro that is not
   Ubuntu.  One, not a matrix — the value is in learning what breaks.
3. Get sound out of it on a machine that never had the tree, and write
   down which of the four paths survived.
4. Only then decide whether the second format is worth it.
