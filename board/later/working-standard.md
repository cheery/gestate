# working-standard — the way we work exists only as prose that grew around a music program

    status   shelved — 2026-08-18
    because  "standardization effort of our work here" — the method that
             runs this project is spread over five documents and some
             1,550 lines, with one rule stated three times inside a single
             file, and nothing states it apart from gestate; a second
             project would re-derive it by hand or copy this repository
             and delete the parts that do not apply
    asked    Henri, 2026-08-18 (Claude wrote the card at his ask)
    see      board/later/project-seed.md — what this exists for
             board/README.md — the largest single piece of the method
             spec/author.md — what the author spends attention on
             doc/instruments.md — what a session already has to work with
             manifesto.md — how an instrument fails
             vision.md — what any of it is for
             board/interface-oracle.md, board/carried-state.md,
             board/driven-runs.md, board/cheap-gates.md — the four
             workflow cards; the raw material, not absorbed

## The ask

> We need two cards that are interrelated. standardization effort of our
> work here, and a template for new projects.

And, once the scope had been argued:

> I wonder if working-standard also involves fixing all the issues we
> have right now, and reorganizing our current resources into that
> living standard it needs to be, which then lives with us.

## Shelved, 2026-08-18

*Henri:* **"I want the cards made for this to go directly into the
board/later/ because they aren't current."**

And a second reason, found while elaborating and worth more than the
first: **the method is still moving.**  In the three days before this
card was written, the board changed its own rules three times — a
session may mint a card (2026-08-18), `later/` was invented for
displaced cards (2026-08-17), and commit titles stopped being Henri's to
give (2026-08-17).  Writing the standard this week would standardize a
draft, and a standard is expensive to change precisely because other
things start depending on it.

It comes back when the method stops changing, or when
`board/later/project-seed.md` forces the question — whichever happens
first.

## Found by looking

**Five documents, 1,554 lines** *(measured 2026-08-18)*, not counting
`roadmap.md`, which is the argument rather than the method:

| file | lines |
|---|---|
| `board/README.md` | 483 |
| `manifesto.md` | 408 |
| `spec/author.md` | 379 |
| `doc/instruments.md` | 210 |
| `vision.md` | 74 |

**And the duplication is real, not aesthetic.**  The two-writers rule —
*two writers never touch the same file* — is stated three times inside
`board/README.md` alone — deliberately, each time arguing for a
different rule, which is exactly how three statements of one rule come
to exist and is why no line numbers are given here: they rot, and this
paragraph rotted its own within the hour it was written.  The andon is
explained in five separate documents.  A rule stated three times is
three things that can drift apart, and nothing in the suite compares
them.

That is the concrete target behind *"reorganizing our current
resources"*: one rule, one place, and the other places citing it.

## The scope, as far as it was settled

Three readings were put to Henri with what would kill each; he took the
second.

1. **Consolidate and make executable.**  One rule, one place, enforced
   by the suite the way `test/test_board.py` already enforces the
   board's own contract.  Bounded and finishable.
2. **Consolidate, plus fix the method's known defects.**  Chosen.  The
   four workflow cards above *are* the issues in how the work is made,
   and they were already on the board when this was written.
3. **Fix all the issues.**  Rejected: twenty open F-numbers and the
   whole live board.  A card that contains the board is the board, and
   it could never be finished, so it could never leave `later/`.

**The four cards are named, not absorbed.**  Merging them into this one
would save four lines on the board and cost four ids that are already
cited from tests and other cards — and `board/README.md` is explicit
that the filename is the id and a citation must keep resolving.  So they
stay as the units of work; this card is what they add up to.  Reversing
that is one line, and it is Henri's line to write.

## The word doing the most work

*"which then lives with us."*

A standard that is written and not enforced becomes the sixth document,
which is the failure this project already knows and has already
designed against: a rule that lives in the window holds only for people
using the window — not for a collaborator with a different editor, and
not for a session that writes files with tools.  So whatever this card
ends up covering, **the test of it is that the suite can fail on it.**

## Questions

*Open, for whenever it is unshelved.*

**1. Is the standard a document, or a directory?**  A document is read
once and drifts.  A directory a new project copies — a `board/` skeleton,
a `test_board.py`, an empty `fixme.md` with its legend, a `vision.md`
with nothing but its own instructions — is a thing that starts working
on day one.  This is the question `board/later/project-seed.md` is
really about, which is why the two cards are one decision.

**2. Does it absorb the four workflow cards?**  Written as *no*, above.

**3. Does the questioning survive the move?**  `board/README.md`
§"Question it into existence" was added on 2026-08-18 at Henri's ask —
*every* card questioned before it is written — and it is the piece of
this method most likely to be dropped when somebody is in a hurry in a
new repository, because it costs a conversation and produces nothing
visible until the card is better than it would have been.  It is also
the piece that most changed what got built here.  Whatever a seeded
project inherits, this is the part to check for.

**4. What is deliberately gestate-shaped and must not travel?**  The
music, obviously.  But also, probably, the F-number scheme's history,
the specific instruments in `doc/instruments.md`, and the parts of the
manifesto that argue about audio oracles.  Separating those is most of
the work, and it cannot be done by a session guessing.
