# persistent-workbench-state — the editor opens where you left it

    status   done — 2026-08-18
    because  when the window is closed the data is lost; it causes
             possible data loss, and leads to forgetting where one was
             yesterday
    asked    Henri, 2026-08-16
    see      spec/workbench.md — the window's own conduct
             spec/verification.md, gestate/sessionlog.py — the transcript
             already records a session; this is the other half

## The ask

> I'd like that when the editor closes, it could open to about the same
> state where it was.  As if that state was a document in itself.

And the hazard he named with it:

> potential issue in this is that we would need to decide where the
> information is placed, and how do we handle multiple workbenches.

## The decisions, answered before anything was built

*2026-08-18.  Four questions put to Henri in one sitting, because each
of them changes what gets written and none of them can be recovered from
the code afterwards.  His answers, and what each one settles.*

**1. A saved position, not a replayed history.**  The card called this
"the first real decision" and it is: `sessionlog` already records every
session, so reopening *could* be a replay.  It should not be.  Replaying
re-executes — it makes sound, it writes files, and it costs what the
session cost.  **History and position are different jobs**, and
conflating them gives you a reopen that plays a piece nobody asked for,
which is the thing `spec/rocks.md` has an opinion about.  So `sessionlog`
stays what it is — history, for verification — and this is a small
declarative document that nothing executes.

**2. Beside the `.ges`, named after it.**  His own hazard, and the phrase
in his ask decides it: *"as if that state was a document in itself"* is a
file with a name, not a hidden dot-directory.  Beside the piece because
**most of the state is the piece's rather than the person's** — which
boxes stand, the seed, the loop span — so it travels with the piece, and
can be committed, diffed and handed to somebody else.  A file in `~` can
do none of those.

**3. Written on close, and it refuses to clobber.**  His second hazard,
two workbenches on one file.  Last-writer-wins was available and is
rejected: you would find out it was wrong *by losing yesterday's place*,
which is the exact thing this card exists to prevent.  So the window
writes when it closes, and a window that finds the document changed
since it opened **says so and leaves it alone** — the manners a text
editor already has about a file that moved underneath.

**4. What must not be restored** — still this card's to settle, and the
two named already: a transport that resumes playing (a program making
noise nobody asked for), and a build that looks current and is not.

## Closing them all, and opening them all again

*Henri, 2026-08-18, on the answer to hazard 3: "I think on the multiple
windows, then you close and open them all again, I'd believe that needs
some mechanism so that the postcondition holds and it's worthwhile to
write down."*

**He is right, and the gap was in the answer rather than in the
question.**  "Write on close; refuse to clobber" protects a document
from being overwritten.  It does not put your windows back.  Close three
windows on three pieces, start again, and every piece knows where you
were — while *nothing knows there were three*.  The postcondition as
first written says "the window", singular, and quietly assumed the case
that needed the mechanism away.

### The mechanism, and why it is two documents and not one

**There are two kinds of state here and only one of them is the
piece's.**  That is the whole finding, and it sharpens decision 2 rather
than contradicting it:

* **The piece's** — the caret, the zoom, the seed, the loop span, the
  knob values, which boxes stand.  All of it is about *this piece*, it
  is the same for anybody who opens it, and it belongs beside the
  `.ges`, committed, as decision 2 says.
* **The desk's** — which pieces were open at all, in what order, which
  one had your attention.  **This is about nobody's piece.**  It cannot
  live beside any one of them, because it is a fact about the set; and
  it should not be committed, because your window layout is not the
  project's.  It is yours, so it lives where your things live.

So: `<piece>.desk` beside each piece, and one desk record in the user's
own configuration.  The common case — one window, one piece — is
entirely in the committed file, and the personal, unshareable half stays
out of the repository.

### And nothing supervises the set

**One process is one window.**  `workbench.main` takes a single optional
file (`ap.add_argument("file", nargs="?")`), so three windows are three
processes with no parent between them.  Nothing is in a position to
write down "there were three" except the three themselves.

That makes the desk record a thing the windows maintain **as they come
and go** — a window adds itself when it opens and takes itself out when
it closes — rather than something written once at the end by whoever is
last.  Two consequences worth having in writing before anything is
built:

* **A window that dies leaves its entry behind.**  A crash, a `kill`, a
  machine that lost power.  The record is therefore *best-effort* and
  must read as a list of pieces worth reopening, not as a claim about
  what is running.  A stale entry then costs a window you did not want,
  which is recoverable; a design that treated the record as authoritative
  would cost something that is not.
* **Two windows on one piece both want to write `<piece>.desk`**, and
  decision 3 says the second one refuses.  That refusal is *safe* rather
  than lossy only because the desk record is where a second window's own
  position can go — which is the other reason the split earns its keep.
  **And they do keep separate places** (*Henri, 2026-08-18*): `.desk`
  holds the one shared, committable position, and a second window on the
  same piece keeps its own in the desk record.  Two views of a long
  piece each come back where they were, which is the only reason to have
  opened two.

### The postcondition, restated

The first version assumed one window, which is exactly the assumption
this correction is about:

> ~~Closing the window and opening it again puts you back where you
> were, and a second window open on the same piece cannot take that
> away from you.~~

> **Closing everything and opening it again puts you back where you
> were — the same pieces, each where you left it — and no window's
> closing takes another window's place away.**

Corrected once more by the launch answer above, because *"the same
pieces"* promises more than he asked for — a bare launch restores one
piece, not a screenful:

> **Opening a piece puts you back where you were in it; opening the
> workbench with nothing puts you back in the piece you were last
> working on; and no window's closing takes another window's place
> away.**

Three clauses because there are three ways to lose a day, and the third
is the one hazard 3 is about.

### What a launch does — answered, and not from the menu

**A bare launch is the first screen a stranger ever sees.**
`tools/gestate-editor` runs `gestate.workbench "${1:-untitled.ges}"`, so
opening gestate with no argument opens `untitled.ges` — the starter, and
`board/done/button.md` and `fixme.md` F150 are the account of how hard
that screen was to get right.

Put as a choice between *asked for* and *automatic*, and **Henri gave a
third answer**, 2026-08-18:

> I think the workbench `filename.ges` should land to that file, but
> without arguments workbench should restore the file it last worked on.

So:

* **`workbench foo.ges` opens `foo.ges`** — and lands *in it where you
  were*, from `foo.desk`.  Naming a file always means that file; a
  restore never overrides an argument.
* **`workbench` with no argument reopens the piece you last worked
  on** — one piece, not the whole set.  This is narrower than either
  menu option and is the better answer for it: the desk record is
  consulted for *one* fact, and nothing has to decide how many windows
  to throw at the screen.

**And the starter survives on the only person it is for.**  Somebody who
has never opened a file has no last file, so a bare launch still gives
`untitled.ges` — which is who F150's screen was built for.  What does
change is that a *returning* user stops meeting the starter on a bare
launch, and that is the trade, taken knowingly: it is the cost of the
one thing the card exists to buy.

## What is left to elaborate

The four above are answered.  What the elaboration still owes when the
card is taken:

- **What "state" is**, itemised rather than assumed — the open file, the
  caret, the scroll, the zoom, the transport, the seed, knob values, which
  boxes are standing, the piano's octave, the command list's last query.
  Each of those is a different kind of fact and some of them are already
  written down somewhere.  *"As if that state was a document in itself"*
  is the interesting phrase: it suggests the answer is a **file with a
  name**, not a hidden dot-directory, and a file with a name can be
  opened, diffed, committed and handed to somebody else.
- **What must not be restored.**  A playing transport that resumes on
  open would be a program making noise nobody asked for, which
  `spec/rocks.md` has an opinion about; a stale build that looks current
  is the same defect one floor up.

**And what already exists**: `gestate/sessionlog.py` records every
session in memory, always, and `transcript` writes it down —
`spec/verification.md` is its design.  That is the *history* half of
this card already built, and decision 1 says it stays that half.

**The postcondition** is above, in §"Closing them all, and opening them
all again" — written before anything was built, derived from the
`because` (*"it causes possible data loss, and leads to forgetting where
one was yesterday"*), and already corrected once by the person it is
for, which is the whole reason the rule asks for it early.

## Done

*2026-08-18.  `journal.md` §"Where you were, as a document" tells the
story; `gestate/desk.py` is the module and its own docstring is the
design.*

**Two documents, because there are two kinds of state.**  `<piece>.desk`
beside the `.ges` — the caret, the zoom, the seed, the loop, the octave,
the knob values — readable, committable, and the piece's.  And
`~/.config/gestate/desk`, which holds which piece you were last in and
which windows are open: a fact about the *set*, so it belongs to nobody's
piece and is not committed.

**What is never written down** is as much of the design as what is: there
is no `playing` field and no build.  A window that reopened playing would
be a program making noise nobody asked for, and having nowhere to say it
was is a stronger guarantee than remembering not to apply it —
`test_nothing_about_the_transport_or_the_build_is_written_down` asserts
the *absence*.

**Nothing supervises the set**, so a window adds itself to the record
when it opens and takes itself out when it closes, and a row is believed
only while its process is alive.  A crash therefore costs a stale row and
nothing else.

**Read while open, written after shut.**  `caret()` reads across the ABI,
so asking a closed editor answers zero — which would have filed *you were
at the top of the file* over wherever you actually were, every single
time.  `_place` and `_remember` are two functions for that reason and no
other.

**Verified on the real program, by doing what a person does.**  A driven
window under Xvfb: click in, arrow down five lines, `Ctrl-K`, `quit`,
Return — and `piece.desk` came back saying `line 6, column 5, zoom 4`.
Then launched again **with no argument**, focused without clicking (a
click would have moved the caret and told us nothing), quit the same way:
it opened the right piece and wrote back the same line it had been told.
Had the restore not happened it would have written line 1.  Twenty-six
tests hold the parts; that run is what holds the claim.

**Left for a later card, and named rather than implied:**

* **The scroll is not restored.**  Putting the caret back makes the view
  follow it, which is what *where you were* means to somebody looking at
  the screen — but a person who had scrolled *away* from their caret to
  read something else does not get that back.
* **Which boxes stand** is in the card's own list of what state is and is
  not in the document.  A `canvas <expr>` box is a thing you opened, and
  reopening it is a command with arguments rather than a number.
* **A second window's place is kept but not yet claimed.**  `keep`/`kept`
  hold it and are tested; what does not exist is a window *knowing* it is
  the second one at the moment it needs the answer — `opened` counts
  live rows, and two windows starting together can both read zero.
