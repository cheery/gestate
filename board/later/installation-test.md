# installation-test — the way in is the one thing here nobody checks

    status   shelved — 2026-08-18
    because  "the installation should be tested like how everything else
             here is" — a fresh 26.04 machine found three defects in a
             day, and every one of them was in the part a new person
             meets first
    asked    Henri, 2026-08-17 (Claude wrote the card at his ask)
    see      doc/install.md — the manual under test
             README.md §Ubuntu, from nothing — the same list, shorter
             tools/sandbox.sh — a bwrap fence that already exists
             tools/toolbox.sh — the bench's own "what is here, what is not"
             gestate/workbench.py — `install_desktop`
             fixme.md F148 — the icon, found by the same install

## Shelved, 2026-08-18

*Henri:* **"I find the installation test depend on podman, and I'm not
ready to install it."**

Which is the right call and worth reading as a finding rather than a
delay.  The card's own design argued `podman` in — rootless, no daemon,
and *"messing up the system is one `podman rmi` away"*, which answers
his original question.  What it did not weigh is that **the instrument
asks the machine under test to install something first**, and a card
about whether a fresh machine can run gestate that begins *"first,
install a container runtime"* has moved the problem rather than solved
it.

Nothing here is wrong and nothing is thrown away: the three defects one
fresh machine found in a day are still the argument, and the elaboration
below still holds.  It comes back the way it left — by him saying so —
and if it comes back wanting a lighter instrument than a container, that
is a real question this shelving has surfaced rather than buried.

**Event named, 2026-08-28, at the first fire.**  The pile pass found
this card waiting on him rather than on an event, and he named one:
*"when tend is matured a bit, we will use tend to do the installation
test."*  So the instrument is `~/tend`, not podman, and the card is
sediment until tend can carry a fresh machine — see
`doc/memory/tend-the-workspace-tree.md`.

## The ask

> I did install gestate to most recent ubuntu 26.04 LTS on worklaptop,
> because I'm also going to need it there. […] The .desktop file didn't
> work at first throw on that computer and had to summon AI to fix it,
> and libx11-dev should be written as dependency to installation manuals
> because it is. But I realised that the installation should be tested
> like how everything else here is. […] btw is that even possible to
> test without messing up the system?

## What one fresh machine found in a day

Three, and they are three different *kinds*, which is the argument for
the card:

| what | kind | how it was found |
|---|---|---|
| `libx11-dev` missing from both manuals | **the build does not start** | he hit the linker error |
| the `.desktop` file did not work first throw | **it installed, and did nothing when clicked** | he asked an AI to fix it; answered and fixed below |
| the taskbar drew a sine, not the egg (F148) | **it worked, and was wrong** | he looked at it |

The middle row is the one this card is most about — it is the one where
the software installed successfully and then did not work, and it was
fixed on his laptop before it was fixed in the tree. The first row is
the one that shows the mechanism by which a manual goes wrong.

**`libx11-dev` was true and went stale in one day.**  `doc/install.md`
said, of the X11 packages: *"No `-dev` packages are needed — they are
opened at run time, not linked at build time."*  Written 2026-08-12,
and correct: `baseview` dlopens them.  On 2026-08-13 the window grew its
exterior — `XChangeProperty` for the icon and name, then
`XkbSetDetectableAutoRepeat` for F106 — and two `#[link(name = "X11")]`
attributes made the linker want `libX11.so`, which only the `-dev`
package ships.  Nothing re-read the sentence, and no test could: **this
machine has `libx11-dev`, so the claim and the code disagreed here for
four days without a symptom.**  That is the whole shape of the problem.
An installation manual is a claim about a machine that is not this one.

## Found by looking, before it was taken

### Yes, it can be tested without touching the system

Three tiers, cheapest first.  They test different things and the card
should probably build the first two and stop.

**1. A fake `HOME`, for everything that writes to disk.**  Already
proven, today: `--desktop` was checked by running it with
`HOME=<tmpdir>` and looking at the six files it wrote.  Costs nothing,
runs in the ordinary suite, needs no privileges, and it covers exactly
the row above that nobody understands — the `.desktop` file, the
`hicolor` tree, `StartupWMClass`, `Exec` pinning the venv.  A
`desktop-file-validate` on the result is a real oracle, it is already
installed (`desktop-file-utils`), and **it is not vacuous** — pointed
at what `--desktop` writes today it answers:

```
hint: value "AudioVideo;Audio;Development;" for key "Categories"
      contains more than one main category; application might appear
      more than once in the application menu
```

which is a defect nobody had noticed, found by the first thing this
tier would do.  It exits zero, so the test has to decide whether hints
count.

**2. A container, for the apt line and the build.**  This is the honest
one: a base image has *nothing*, so the manual is executed rather than
read.  `podman` is the right tool — rootless, no daemon, and it stores
everything under `~/.local/share/containers`, so "messing up the
system" is one `podman rmi` away.

  Two frictions worth knowing before it is taken:

  * `podman` is **not installed here** (`apt install podman`, 4.9.3 on
    24.04).
  * `kernel.apparmor_restrict_unprivileged_userns = 1` on this machine,
    which is what `tools/apparmor-bwrap.profile` exists to work around
    for `bwrap`.  Ubuntu ships `/etc/apparmor.d/podman` for the same
    purpose, so rootless podman should work without loosening the
    sysctl — but **that is the thing to verify first**, because the
    failure mode is the one that profile's comment already warns about:
    it does not fail loudly, it fails as a fence that is not there.

**3. `tools/sandbox.sh` is *not* the tool for this**, and it is worth
writing down why, because it looks like it is.  It fences the project
off from the host while sharing the host's `/usr`; the whole point of
an installation test is a `/usr` that does not have anything yet.  It
is the right tool for running the *suite* safely and the wrong one for
this.

### The ceiling, stated up front

A container proves the apt line, the venv, `cargo build`, and every CLI
path — `audioperform`, the exporter, the suite.  It does not prove:

* **the window opens.**  `Xvfb` is installed here and `test_editor_abi`
  already knows how to skip without a display, so a headless window
  test in a container is reachable — but an Xvfb window is not a
  desktop.
* **the dock shows the egg.**  Nothing but a person sees that, which is
  the same shape of gap `unheard-output` is about.  F148 would *not*
  have been caught by any of this; it was caught by Henri looking.

So the card's honest promise is: **it catches the "does not start" and
"writes the wrong file" classes, and not the "it worked and was wrong"
class.**  Both of the first two happened this week.

### Where it would live

`test/` skips on a missing backend everywhere already (`needs_cargo`,
`needs_display`, `needs_toolchain`), so tier 1 is an ordinary test file
and tier 2 is one marked the way `golden` is — deselectable, run
deliberately, because it downloads a base image and takes minutes.
`pytest.ini` is where that marker is declared.

## Questions

**Q (Claude), the one that blocked the useful half.**  *What actually
went wrong with the `.desktop` file on the work laptop?*

**A (Henri, 2026-08-17).**  He sent the diff he had made there:

```diff
-        f"Exec=env PYTHONPATH={root} {sys.executable} "
-        "-m gestate.workbench %f\n"
+        f"Exec={root}/tools/gestate-editor %f\n"
```

**And it reproduces here in one line.**  A dock click passes *no file*,
so `%f` expands to nothing — and the module with no file is:

```
$ env PYTHONPATH=… .venv/bin/python3 -m gestate.workbench
usage: python -m gestate.workbench [-h] [--desktop] …
python -m gestate.workbench: error: a file to edit (or --desktop)
exit code: 2
```

`Terminal=false`, so that sentence goes into a journal nobody reads.
**The icon did nothing when clicked, silently.**

The bitter part: `tools/gestate-editor` was written for exactly this
and says so in its own comment — *"opening the file it was handed, or
the scratch file when it was handed nothing — a bare click on an icon
should open an editor, not print a usage line."*  It also finds the
venv and `cd`s to the tree.  `install_desktop` simply never pointed at
it, and the two lived a directory apart with nothing to notice.

**Q (Claude).**  Which Ubuntu does the manual claim to be about?  This
machine is 24.04.4; the work laptop is 26.04.  A container test has to
pick, and if it picks one the other is untested — or it takes both and
the suite grows a matrix.  *Two images is my recommendation only if the
manual means to promise both.*

**Q (Claude).**  Is `podman` allowed on this machine at all, or should
the container tier be written so it runs in CI or on the work laptop
and skips here?  It is an `apt install` and an AppArmor question, and this tree already
has the rule for it: `tools/sandbox.sh --check` exists because a fence
that is not there fails silently, and a container tier deserves the
same proof before anything is trusted to it.

## What landed already, 2026-08-17

**Tier 1 exists** — `test/test_desktop.py`, five tests, written the
moment the answer above arrived and therefore written against *what
failed* rather than against what the installer happens to do:

* the click regression: `Exec` names the wrapper, the wrapper exists
  and is executable, the wrapper still supplies a file, and `main([])`
  still exits 2 — the last one is what makes the first three matter,
  and it is asserted beside them so a reader sees why.
* `StartupWMClass` equals the `WM_CLASS` the Rust declares (the F148
  half: without it GNOME shows a gear).
* every `hicolor` size and the scalable copy are what `icon.py`
  renders.
* `desktop-file-validate`, skipped where it is not installed.

Checked by putting the old `Exec` line back: two of the five fail.  And
the fix itself was checked the way a person would — `gio launch` on the
installed entry with `XDG_DATA_HOME` pointed at a throwaway directory,
which opened a real editor (`.venv/bin/python3 -m gestate.workbench
untitled.ges`) and left no scratch file behind.

`fixme.md` F149 is the entry for the defect.

## What the work is

1. ~~Answer the `.desktop` question; write tier 1 against what actually
   failed.~~  Done, above.
2. Tier 2: a container that runs the README's own apt line and then the
   proof of life, from a base image, marked so it is opt-in.  **It must
   read the command out of the manual rather than repeat it**, or the
   test and the document drift exactly the way the code and the
   `-dev` sentence did.
3. Decide the `Categories` hint: three categories put gestate in more
   than one menu.  It may be wanted; it has never been chosen.
4. Say in `doc/install.md` that it is tested, and by what — a manual
   that is checked should say so, and one that is not should not
   pretend.
