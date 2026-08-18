# project-seed — the next project starts from nothing, the way this one did

    status   shelved — 2026-08-18
    because  "I feel that an unix operating system is not designed well
             for future times" — the next project already exists as
             notes and will be started once a milestone here lands, and
             on the day it starts it will have no way of working: the
             board, the ratchet, the suite-as-authority and the rule
             that a card states a problem would all be re-derived by
             hand or copied and pruned
    asked    Henri, 2026-08-18 (Claude wrote the card at his ask)
    see      card:working-standard.md — the half that has to exist first
             card:portable-package.md — the neighbouring card about
             people who do not exist yet, and why this one is different
             vision.md — "a lean vehicle to find out how to utilise AI well"

## The ask

> We need two cards that are interrelated. standardization effort of our
> work here, and a template for new projects.

And the project it is for:

> I think that when I complete a next milestone in this project, I will
> create a new one, these notes are the beginning of that project.

> I feel that an unix operating system is not designed well for future
> times.

**The notes themselves are outside this project and are not cited
anywhere on the board — Henri's instruction, and it holds.**  What is
recorded here is only what he said in conversation: a next project
exists, it is an operating system, and it starts after a milestone
lands here.

## Shelved, 2026-08-18

*Henri:* **"I want the cards made for this to go directly into the
board/later/ because they aren't current."**

The start condition is his own and it is not a date: *when I complete a
next milestone in this project.*  So this card waits on an event rather
than on a queue position, which is the cleanest kind of shelved card
there is — nothing about it rots while it sits.

## Found by looking

**This card is not the `card:portable-package.md` shape, and the
difference is worth writing down**, because the board's order demotes
that one explicitly for being *"for people who do not exist yet."*

Here the user exists, is named, and is the person who fills this board.
The second project is his, it has a start condition he stated, and its
subject — security, and a system that hardens under attack — is the same
problem that put `card:ungated-fixes.md` on the live board today.  A
method that has only ever worked in the repository it grew in has not
been shown to be a method; carrying it to a second project is the test
of it.

## The dependency, and which way it runs

Asked directly during elaboration: does the template fall out of
standardizing, or is the template the forcing function that reveals what
is general?

Both, and the order is: **`card:working-standard.md` first, this
second** — but the second is what makes the first falsifiable.  A
consolidated standard that nobody has tried to start a project with is
a guess about which parts were essential.

## Questions

*Open, for whenever it is unshelved.*

**1. What does a seeded project inherit on day one?**  The candidates,
in descending confidence: the `board/` discipline and its executable
contract; `fixme.md`'s numbering-as-addresses; `vision.md` as a dated
document that decides things; the rule that a `because` is a problem;
the suite as the only place rules are enforced.  Less clear: the andon,
the journal's length, the postcondition practice.

**2. Is it copied, or is it a tool?**  A directory somebody copies drifts
from its origin the moment it is copied, and that may be correct — a
standard that lives with us in two projects is two living copies, not
one authority.  Worth deciding rather than defaulting.

**3. What does the new project's subject change?**  This one's failures
are musical and visible.  A system designed to be attacked has failures
that are neither, and the instruments in `doc/instruments.md` — driving
the window, photographing it, listening to the output — may have no
counterpart there at all.
