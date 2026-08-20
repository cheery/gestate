---
name: gestate-testing-standard
description: "Testing standard — NOW WRITTEN IN THE TREE: spec/verification.md and manifesto.md's instrument table. The screen is an oracle; roster poka-yokes; run via tools/suite.py and freeze the tree while it runs"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: ced30813-dacb-48b2-af6d-0e15bf165020
  modified: 2026-08-16T15:25:14.969Z
---

**2026-08-17: this is in the tree now, and the tree is the authority.**
Henri asked for the lessons to be written *"somewhere where they are
remembered and seen by the next person/machine reading it"* — because
this standard had lived only in memory, where no collaborator and no
fresh session would ever meet it.  Read these first:

- `spec/verification.md` §"The screen is an oracle, and it is the one
  this tree lacked" — the fifteen-line Xvfb + `import` harness, the
  three defects it caught that 2,540 tests could not, and its two rules
  (**mute the run**; **`GESTATE_PRESENCE=` so it keeps no record**).
- `manifesto.md` §"The instruments, and what each cannot see" — the
  photographed window is a row in that table now, with its own blind
  spot stated: *a picture that looks right for the wrong reason still
  looks right.*
- `board/README.md` §"What the first full day of this taught" — freeze
  the tree while the suite runs; targeted per card, one full run per
  shift.
- `spec/verification.md` §"The defect is in the seam, and the test is in
  the module" — **added 2026-08-18 after four defects in one day**, all
  found by a driven window and none by a green suite.  The rule: when you
  add a *kind of thing* (a field on a long-lived object, a file the tree
  now holds, a word that may appear in a source line), go and read what
  already has an opinion about that kind of thing.  There is usually
  exactly one place and it usually says so out loud — `_carry`'s
  docstring is three paragraphs about which state survives an instrument
  swap, and the field was added without reading it.

**Roster poka-yokes** are the pattern worth copying:
`test_audio.py::test_every_audio_example_is_exercised_here` and the
`test_gui.py` twin assert a directory is *exactly* a listed set, so a new
file fails the suite until somebody writes its test.  That is what forced
out the `patchbay.ges` bug.

Henri said on 2026-08-12: *"I'm a bit gung-ho on getting things done and
not used to testing and quality engineering. But now I've seen testing..
Definitely lets test things from now on and properly."*  Treat that as a
standing instruction, not a mood.

**Why:** it is not that gestate is untested — 2,000+ tests, the LLVM
engine checked sample-for-sample against a reference interpreter, and
committed goldens.  It is that the tests are strong **where an oracle is
easy** and absent **where one is hard**, and every defect comes from the
second place.  `journal.md` on stage 10: nine defects, *"all in the
Python around the engine and none in the language, the fragment or code
generation… four of the nine were silent"*.  Then twelve more in the
editor session, then six more the session after — every one found by
Henri using it, none by a test, suites passing throughout.

**How to apply:**

- **Do not report a feature done on the strength of tests I wrote from
  my own implementation.**  That has failed repeatedly: the `Tab`
  binding was "verified" against a stale `.so`, and syntax colouring was
  "verified" by feeding the painter its own input by hand.  Both passed;
  both were broken for Henri.  See [[test-what-a-person-would-do]].
- **A hermetic fixture can also be a blind one.**  Every `gemba` test
  set `GESTATE_GEMBA` to a temp file — correct, since a test writing into
  somebody's open workbench types on their screen — and that is exactly
  what stopped any of them asking where the file goes when nobody says.
  The blindness is invisible from inside the file.
- **Drive the real thing.**  `tools/lagcheck.py` sends real X keys via
  XTEST and reads pixels back; `test_editor_abi.py` opens a real window.
  A regression test for anything the window does belongs there, because
  a double is primed by whatever the test hands it.
- **The named gap is the editor's session transcript** —
  `spec/verification.md` designs it and it is built only for the
  *plugin's* boundary, in Rust.  `Session.run(name, *args)` is a single
  choke point and every command already returns a sentence, so recording
  is cheap.  It would not have *found* any of the defects above; it
  would have kept each as a checked-in file instead of a test written
  afterwards from a description.
- **Run the full suite to completion before saying a batch is clean.**
  It takes over 40 minutes and has repeatedly been cut short by my own
  timeouts; report honestly when that happens rather than implying a
  clean run.
- **And run it as `python tools/suite.py`, never bare `pytest`.**  It
  fences the run, runs the two files the fence cannot host outside it,
  and writes `test/report.md` (what ran, when, which commit, whether
  the tree was clean, every failure by name).  A bare full `pytest`
  leaves nothing behind — I did it on 2026-08-16 and Henri caught it.
  Since then `test/conftest.py` refuses a run collecting ≥800 tests
  unless `GESTATE_SUITE=1` (which `suite.py` sets), so the mistake now
  fails loudly instead of quietly.  Targeted runs (a file, a `-k`) are
  untouched and are still the right tool while working.
- Measure before optimising and after changing anything hot: the poll
  budget is 2 ms, and `GESTATE_EDITOR_TIME=1` reports key-to-pixels.
  Measuring syntax colouring is what turned up `vocabulary()` re-parsing
  `command.ges` on every poll at 650 µs.

Related: [[gestate-verify-workflow]], [[henri-working-style]].
