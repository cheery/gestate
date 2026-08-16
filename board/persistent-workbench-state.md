# persistent-workbench-state — the editor opens where you left it

    status   open — not yet elaborated
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

## Not yet elaborated

Nothing has been looked at for this card.  When it is taken, the
elaboration owes at least:

- **What "state" is**, itemised rather than assumed — the open file, the
  caret, the scroll, the zoom, the transport, the seed, knob values, which
  boxes are standing, the piano's octave, the command list's last query.
  Each of those is a different kind of fact and some of them are already
  written down somewhere.  *"As if that state was a document in itself"*
  is the interesting phrase: it suggests the answer is a **file with a
  name**, not a hidden dot-directory, and a file with a name can be
  opened, diffed, committed and handed to somebody else.
- **Where it goes**, which is Henri's own hazard.  Beside the `.ges`
  file, in the project, or in the user's home?  Each answer implies a
  different thing about whether state is *yours* or *the piece's*.
- **Multiple workbenches**, his second hazard: two windows on one file,
  or one window reopened twice.  Last-writer-wins is the cheap answer and
  probably wrong; the transcript's approach — record what happened rather
  than snapshot where you are — is the other shape available.
- **What must not be restored.**  A playing transport that resumes on
  open would be a program making noise nobody asked for, which
  `spec/rocks.md` has an opinion about; a stale build that looks current
  is the same defect one floor up.

**And what already exists**: `gestate/sessionlog.py` records every
session in memory, always, and `transcript` writes it down —
`spec/verification.md` is its design.  That is the *history* half of this
card already built.  Whether reopening is "replay the transcript" or
"read a saved state" is the first real decision, and it is exactly the
kind that wants deciding before anything is built.
