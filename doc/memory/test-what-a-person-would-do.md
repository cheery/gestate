---
name: test-what-a-person-would-do
description: "Test the thing a person would naturally try, not the mechanism you just built — the gestate palette lesson"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 753ff05e-7489-4e11-b1c1-e5c873af5781
  modified: 2026-08-11T17:55:51.568Z
---

When a feature is finished, the first check must be **the obvious thing
a person would try**, not the protocol just written.

**Why:** the gestate command palette gained argument-asking, and every
test drove it as `find` → Return → `foo` → Return, because that was the
sequence just implemented. Henri typed `find foo`, which is what anyone
would type, and nothing happened. He spent a long, frustrating stretch
concluding the build was stale before working out the interaction rule
himself. The fix — a space does what Return does — took minutes. Finding
it took an afternoon of his time, and it was found by him, not by me.

It compounded with a second self-inflicted one: the status line was
showing the palette's `29 of 29` *after* each command's own sentence, so
every command he tried looked like it had done nothing. Two bugs whose
only symptom was "it doesn't respond".

**How to apply:**

- After building an interaction, use it once the naive way before
  declaring it done. Type the whole line. Click the obvious thing.
- A harness written from the implementation tests the implementation.
  It cannot find a missing affordance, only a broken one — the same
  trap as *"a stand-in written to suit the caller teaches the caller a
  wrong interface"*.
- When Henri says something "doesn't work" and the tests pass, suspect
  the *interface*, not the build. He asked twice whether he was running
  a stale version; that question is a signal the thing is doing nothing
  visible, which is itself the bug.
- Feedback the user can see is part of the feature. A command that
  works but says nothing is indistinguishable from one that failed.

See [[gestate-editor-latency]] for the same shape in a different key:
a burst of the *same* character could not reveal a one-behind bug.

**2026-09-12, the grid.** Twelve headless tests green, the suite green,
and the first `grid` typed in a window showed a head and no rows. Two
defects, neither reachable by a harness built from the model: `redraw`
given the wrong text, and a mailbox on the wire that lost a message to
the next one (`fixme.md` F226). What found the second was
`tools/driven.py` on `Xvfb :99` — the bench's own display, not his — so
*the driven run is his to call* was wrong: it is a session's to run
before saying *built*. And the run that was meant to *witness* the
repair found a third defect instead (F227), which is the same lesson
one turn deeper: a fix is not verified until the run that would show
it has actually run, and *compiled and loaded* is not *witnessed*.
