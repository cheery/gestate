# The instruments — what a session has to work with

*Started 2026-08-18, at Henri's ask: "write down somewhere the
capabilities implemented so far, such that you find out that you have
gemba available when you wake up next time."*

**Read this early.**  A session that does not know an instrument exists
does the work the instrument was built to make unnecessary — asks a
person to look at something, reasons about the window instead of
photographing it, or reports a finding into a chat log nobody is reading
while it happens.  Every entry below was built because that had already
happened once.

`tools/toolbox.sh` is the neighbouring file and answers a different
question: what is *installed*.  This one is what has been *built*.

**Kept in two places on purpose.**  This page is the tree's copy and
outlives any session; a session's own memory carries a pointer to it, so
that waking up and finding out `gemba` exists does not depend on
happening to read `doc/`.  If you are adding an instrument, add it here
— the pointer will find it.

---

## The standing rule: build the missing one, now

**When a capability is missing, implement it the moment the need
arises — not after, and not as a card for later.**  Henri's, 2026-08-18,
and the tree already carries the argument for it twice over:

* `journal.md` §""Be my oracle" is a smell" —
  *when a session finds itself asking a person to listen, look, or judge,
  write down what the mechanical version would be, even if it is not
  built.*  This is that rule with the hedge taken out: usually it is
  fifteen lines, and the fifteen lines are cheaper than the second time
  you need them.
* `manifesto.md`'s third way an instrument fails is that it agrees with
  the implementation.  An instrument built *while the need is live* is
  built against a real question; one built later is built against a
  memory of one.

The cost of a missing instrument is never the instrument.  It is the
work done blind in its absence, and that work looks like progress while
it is happening — which is why waiting for a better moment does not work.

And when the instrument *is* there, the rule is Ohno's, in
`manifesto.md` §"Go and do it": **do something.**  A session that has a
hypothesis and declines to run the window has swapped an answer for an
opinion, and the opinion goes into a commit message looking like a
finding.

---

## Saying what you are doing, while you do it

### `gemba` — narrate into a running workbench

    python -m gestate.gemba say "reading board/gemba.md"
    python -m gestate.gemba clear

Put a bare `gemba` line anywhere in the file open in the workbench and a
box stands under it showing **one** thing at a time.  Held for as long
as that item takes to read; when the queue backs up, a mark under the
sentence grows with the depth — *he is going faster than you are
following*, which is the signal the box mostly exists for.

`board/done/gemba.md` is the card, `gestate/gemba.py` the module.
**Use it whenever Henri is at the desk while a session works.**  The
alternative is him reading commit messages afterwards, which is the
thing it was built to replace.

### `tools/andon.sh` — ring the sound card

    tools/andon.sh          # once
    tools/andon.sh 3        # three times, eight seconds apart

For reaching him when he is away from the desk and a decision is
expensive to get wrong and cheap to ask about.  **Capped at three by the
script**, on purpose: if three did not reach him he is not in the room.
Collect the questions first — `board/README.md` §"Working while he
rests".

---

## Seeing what the program actually did

### Driving and photographing the window — `tools/lagcheck.py`

    from lagcheck import driven, find_window, tap, chord, click_into, shot

`driven(**env)` is the environment a driven window runs in — it turns
the presence record off, so synthetic keystrokes do not land in
somebody's week.  `a_copy_of(path)` opens a *copy*, never the original
(F154).  `shot(win, path)` captures the window.

**This is the instrument that keeps finding what tests do not.**  Twice
on 2026-08-18: a caret read from a closed editor that would have filed
*line 1* forever, and a `gemba` ask-line that broke the program it was
narrating about while twenty-three tests passed.  Neither is visible
from the source.

Modifier names are X keysyms — `Control_L`, not `ctrl`.  And **`pkill`
does not run a `finally`**: to exercise a graceful close, quit through
the palette (`Ctrl-K`, `quit`, Return).

### `python -m gestate.pops <dump>` — did it click, and where

    GESTATE_HOST_TAP=88200 GESTATE_HOST_TAP_TO=/tmp/x.f32  python -m gestate.workbench piece.ges
    python -m gestate.pops /tmp/x.f32 --opening 10

A click is a **discontinuity**, so the reading is a ratio — this step
against the steps this program normally takes — which is what lets it
work on a drone and a snare without being told which it is.  And it
weighs the *opening* separately, because every defect it was built for
is at the start and a whole-file maximum says nothing about those.

**It found F147 and confirmed the fix**, both without a listener: the
first ten milliseconds running seven times faster than the settled tone,
and then worst equal to settled.  Its blind spot is that it cannot tell
you whether a click is *wrong* — a square wave is a discontinuity forty
times a second and is fine — so point it at a program that has no
business clicking.

### `tools/measure_editor.py`, `tools/dragcheck.py`, `tools/lagcheck.py --check`

Latency and gesture measurement, with `GESTATE_EDITOR_TIME` and
`GESTATE_LOOP_TIME` for where the time goes.

### `gestate.sessionlog` and `transcript`

Every session is recorded in memory, always; `transcript` writes it
down.  `test/sessions/` holds the ones that convicted a defect, named
for its F-number — a replay is *expected* to diff once the defect is
fixed, and the diff is the point.  `spec/verification.md` is the design.

---

## Knowing what the tree says about itself

### `python -m gestate.complaints` — every error message, with its verdict

`doc/complaints.md`.  Every `raise` in `gestate/`, with a verdict
written beside it saying **who is standing in front of it** — `author`,
`command`, `world`, `machine` — and whether it says where.  A new error
class with no verdict fails the suite gate.

Regenerate it after any edit that moves line numbers, which is most of
them.  `board/done/error-messages.md` is the card.

### `python -m gestate.reference` — `doc/ref/`

Every name the libraries define, generated from them, gated so it cannot
drift.

### `python -m gestate.atlas` — the five A3 sheets

`board/done/…`; the set is closed at five and a sixth needs a caller.

### `tools/suite.py` — the whole suite, gates first

The gates are seconds-long structural checks that a working session
breaks: the board's contract, the citations, the atlas, `doc/ref/`, the
complaints page, the example rosters.  **A full run is ~25 minutes and
the tree must be frozen while it runs** — editing under a run produces a
red that describes a moment rather than a defect, which has cost two
runs already.

---

## Keeping the work safe

### `tools/sandbox.sh --check` — the fence

Must say *the fence is up*.  The deny-list blocks a session's own `sudo`
and its own leash on purpose; those go to Henri.  `spec/sandbox.md`.

### `gestate.desk` — where the workbench was

`<piece>.desk` beside the file, and `~/.config/gestate/desk` for which
piece you were last in.  A bare `python -m gestate.workbench` reopens
it.  Nothing about the transport or a build is written down, so nothing
reopens playing.

---

## What is not built, and would be

Kept here rather than in a card, because the rule at the top says these
get built when the need next arises rather than queued:

* **`shot <path>` in the gemba channel** — a picture in the box.  The
  verb-first format costs nothing to extend and every other content box
  is already a picture; the argument is that every finding that moved a
  decision on 2026-08-17 was an image, and prose describing it had
  failed first.  This is the next one to build.
* ~~**A tap at `snd_pcm_writei`**~~ — **built 2026-08-18**, and it is
  `GESTATE_HOST_TAP` above.  The day it was named as missing is
  `journal.md` §"And the harder half: what a *live* oracle would have
  been"; the day it closed F147's pop was the next one.
* **Python and Rust colouring in the workbench** — `board/done/gemba.md`
  items 3–5, so that walking a `.py` or `.rs` file is readable.
* **A graceful-close driver** — no tool here has ever exercised one,
  because they all `terminate()`.
