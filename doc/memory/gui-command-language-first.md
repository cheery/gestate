---
name: gui-command-language-first
description: "Henri, 2026-09-07: the command language and a clear model come before any GUI, and it must be stressed — every gesture has a command under it, the picture is never where the model lives"
metadata:
  type: feedback
---

**The command language and a clear model, before any picture.**
Henri, 2026-09-07, opening `card:gui-is-difficult.md`: *"One thing I
find important, that you already listed: it's the command language and
clear model before the GUI.  That's so important it must be stressed."*

**Why:** it is the one idea that makes the other GUI ideas testable.
A picture as a function of state needs a state; hit-testing needs
something to name what was hit; a photograph as a test needs a command
to have produced it; a window that inspects itself needs a model to
report.  Built picture-first, the model becomes whatever the widget
tree holds, and that is the bug.  It is also the reason a rewrite of
the roll's hands on 2026-09-06 cost the tests and not the commands:
`transpose`, `carry`, `select`, `bars`, `tempo` were what the drags ran
all along.  Working examples he and the tree already lean on: Tcl
before Tk, Blender's operators, Emacs, acme, AutoCAD, Reaper's
actions, his own oscillseq ([[henri-prior-tools]]).

**How to apply:** for any UI work, name the nouns and the verbs first,
make them run headless, and only then draw.  A gesture that has no
command under it is not finished.  When a UI design question comes up,
ask *what is the model* before *what does it look like*.  The card
holds the full list of ideas and his questions; the critical parts of
the framework are his to design, so a session asks and writes the
answers in rather than building ([[decisions-arrive-shaped]],
[[test-what-a-person-would-do]]).
