# error-messages — go through every complaint and make sure it works

    status   done — 2026-08-18
    because  "we maybe need to arrange a session where we examine
             meticulously every error message and ensure they work. We
             already did that once and it needs to be done again"
    asked    Henri, 2026-08-17 (Claude wrote the card at his ask)
    see      test/test_error_places.py — started, one test per message
             fixme.md F152 — the finding that prompted it
             fixme.md F141 — the same defect, one message, found by a person
             gestate/audiospans.py — `in_source`, what turns a raw span
               into the author's own file and line
             board/button.md — the neighbouring lesson: a first screen is
               an interface, and so is a complaint

## The ask

> we maybe need to arrange a session where we examine meticulously
> every error message and ensure they work. We already did that once
> and it needs to be done again.

## Found by looking, before it was taken

**The prompt was one message, and the shape of it generalises.**  Henri,
typing into the new automatic audition: *"The error messages no longer
interleave into their places.  Just try take `Sig Floa` and see how the
message doesn't land."*

The message was `Unknown type constructor: Floa`, and it carried **no
position**, so the editor had no line to draw it under: a complaint with
a place gets a red content box interleaved into the code, and one
without gets a single sentence in the status bar.  Same seriousness,
different treatment, and the difference was invisible from the source —
`kindcheck.py` had the position arithmetic already, written for
`foo : int` (F141) and used *only there*, because that is the one
message somebody had hit.

**That is the pattern this card exists for.**  Not "some messages are
badly worded" — the messages here are unusually good — but that the
qualities a message needs are per-message, added when somebody
stumbles, and there is no list.  Five kind errors were given their
place on 08-17 in about ten minutes; nobody knows what the rest of the
tree looks like.

### What "works" means for a message — the proposed checklist

Written down so the audit is a sweep and not a browse.  Each is a
property that has already gone wrong somewhere in this project, with
the receipt:

| | property | the defect that paid for it |
|---|---|---|
| 1 | **says where** — a raw `line:col` the editor can place | F152, the whole of it |
| 2 | **says what**, not only where | asserted in `test_error_places.py`, because appending a span is exactly how the sentence gets lost |
| 3 | **survives formatting** — `_first_line` used to drop everything after the first line, so the half of a type error that says *what was expected where* existed only until it was shown | `audioeditor._first_line`'s own docstring |
| 4 | **is in the vocabulary of what you were doing** | F141: a lowercase signature produced a complaint about a *class*, in the vocabulary of a feature the person was not using |
| 5 | **reaches the person at all** | F140: the render refused and the reason stayed in a terminal nobody was reading |
| 6 | **does not fire when nobody asked** | F151's may-not-complain rule — the newest one, and the reason a complaint's *timing* is now part of whether it works |

### Where the messages are

A count worth having before the sweep is designed, and it is only a
`grep` away — `raise \w*Error(`, plus the `say(` family for the ones
that never raise.  The known homes:

* `kindcheck.py` — `KindError`; **five given their place, 08-17**, and
  the file is small enough to have been finished then.
* `unify.py`, `infer.py`, `typecheck.py`, `constraint.py` — the type
  errors, which are the ones that already carry spans (`_span_str`).
* `declarations.py` — `DeclError`, and the desugar-time complaints.
* `exhaust.py`, `coherence.py`, `monotone.py` — the checkers that speak
  about a whole program rather than a point in it, where "says where"
  may honestly not apply, and the card should record *that* rather than
  force a position into it.
* `audioextract.py`, `audiollvm.py` — the backend, where a message may
  be a `clang` transcript and the question is what a person can do with
  it.
* `session.py` — the sentences a command answers with, which are not
  errors and are held to the same bar for a different reason.

## Questions

1. ~~**How is "we already did that once" recorded?**~~  **Found, and it
   is the best evidence on this card.**

   *Henri, 2026-08-17: "It may be written somewhere.  That's true.  It
   should leave a paper trail."*  It is: `journal.md` Part I, item 13 —
   **"(implemented) Better error messages — source spans in type
   errors"**:

   > Per `spec/types.md` §9, type errors should carry source locations
   > from the original expression. […] Thread `Span` information from
   > the parser through `Type` metavariables and predicates.  When
   > `unify` fails, report the original source locations of both types.
   > **This is mostly plumbing — the data is available from the parser,
   > it just needs to be carried through inference.**

   So the sweep happened, was implemented, and was scoped to *type
   errors* — which is exactly why `unify` has `_span_str` and
   `kindcheck` had the same arithmetic written out by hand for one
   message.  **Nothing drifted.  The scope was narrower than the
   sentence "every error message", and nothing recorded the gap.**

   That is the finding to carry into this card's design: the deliverable
   is not "fix the messages", it is **the list of every complaint with
   its verdict**, so the next sweep starts from what the last one
   decided rather than from the code again.  And the last line of that
   journal entry is the one to remember while sweeping — *the data is
   available, it just needs to be carried through*.  It was still true
   ten thousand lines later, in a different checker (F152).

2. ~~**Is a position required, or is it a default with exceptions?**~~
   **A default, with the exceptions recorded.**  *Henri, 2026-08-18:*
   a message says where unless it is honestly about a whole program —
   and then the list carries **"no place, on purpose"** with the
   reason, so a later reader cannot read it as an oversight.

   He turned down both alternatives, and each for the reason the card
   suspected: forcing a position everywhere gives exhaustiveness and
   coherence a line number that means nothing, and adding places
   message-by-message as people hit them *is the status quo, and it is
   what produced F152.*

3. **Does the audit want a person in front of it?**  Every finding on
   this card so far arrived because somebody typed something wrong by
   accident — F141 from a friend's signature, F152 from Henri breaking
   a type on purpose to see what happened.  A sweep by reading may be
   the wrong instrument for the same reason reading the window was:
   `board/stranger-test.md`'s rules apply, and a stranger's mistakes
   are a *free* source of real messages nobody would think to write.

   **Left standing on purpose, and it belongs to the other card.**  The
   sweep produces the list; a person produces the messages nobody would
   think to write.  They are different instruments and the second one
   spends a scarce person, which is why `stranger-test` is ranked where
   it is.

4. ~~**How much of the tree is in scope?**~~  **Everything a person's own
   file can reach, in full; the rest recorded in one line each.**
   *Henri, 2026-08-18.*  392 `raise …Error(` sites across 48 error
   classes is more than a session, and the two ways of cutting it are
   not equal: auditing only the front end *is the same narrowing that
   made the last sweep leave a gap nobody recorded* (question 1).  So
   nothing is left out of the **list** — a complaint a person cannot
   provoke gets the verdict `machine` and is done with in a row, and
   the gap is written down rather than implied.

5. ~~**Where does the list live?**~~  **Generated, and gated in the
   suite.**  *Henri, 2026-08-18.*  A hand-written audit "goes stale the
   first time somebody adds a raise, exactly like the last sweep did";
   tests alone "record the passes and not the deliberate noes".  So the
   verdict lives **beside the raise, in the source**, and a tool walks
   the tree and emits the list — with the gate being that a complaint
   with no verdict fails the suite.

## The postcondition

*Written 2026-08-18, before anything was built, per this board's rule.*

> **A mistake a person makes in their own file is answered under the
> line they wrote it on, in the words of what they were doing — and
> where that is impossible, the list says why rather than leaving a
> gap.**

## What the work is

1. Enumerate: every `raise …Error(` and every complaint path, into a
   list that outlives the session.
2. Check each against the six above, and record the answer per message
   — including the deliberate noes.
3. Fix what is cheap while sweeping (the five kind errors took ten
   minutes); file the rest with the list as the receipt.
4. `test/test_error_places.py` grows one test per message that must
   name a place, which is what stops the next one from rotting quietly.

## Done

*2026-08-18.  `journal.md` §"Every complaint, and who is standing in
front of it" tells the story; this is what landed.*

**The list.**  `doc/complaints.md` — 390 complaints, every one with a
verdict, generated by `python -m gestate.complaints` from a marker
written beside the raise.  Four words for who meets a message
(`author`, `command`, `world`, `machine`), and two ways for an `author`
complaint to have no line: `nowhere`, a decision, and `unplaced`, a
debt that must name the defect owning it.  **That second word is the
one this card did not foresee and could not have done without** —
without it every debt would have been filed as a design.

**The gate.**  `test/test_complaints.py`, in `tools/suite.py`'s gates
beside `doc/ref/` and the atlas: a new error class with no verdict
fails; an `author` complaint that says neither where nor why not fails;
a `nowhere` with no reason and an `unplaced` with no F-number fail; and
the page is compared against the source it is derived from.

**What was fixed while sweeping.**  The placer existed three times and
is now one (`syntax.ast.at`).  Places carried through where the span
was already in the room: all 25 declaration complaints, eight in the
desugarer, the projection family, both of `unify`'s placeless
mismatches, the kind expressions, and exhaustiveness.  **20 of 390
complaints said where when this card was taken; 111 do now.**

**And three sites were counting in the author's coordinates while
spelling the position `line 4:`** — a number `session._line_of` does
not read, so the box was never drawn.  `internals.py`,
`audiovoices.py` and `audioscore._refuse_retired`, all now `at line
4:0`, the one spelling `audiospans.in_source` leaves alone.

**Filed, not fixed:** `fixme.md` F156 (the audio backend names a
definition, never a line), F157 (the type machinery's later stages let
go of the span), F158 (a piece's complaints name a beat), F159 (the
evaluator's runtime complaints carry no position).  56 rows across the
four, each entry saying how many it owns.

**The postcondition, tested as written:** seven mistakes somebody
actually makes, compiled the way the workbench compiles them and read
back the way the workbench reads them — `test_error_places.py`.  That
is the whole path, not the message, and the difference is where all
three `line 4:` defects were hiding.

**Turned up and not this card's job:** `midi.py` and `audiomidi.py`
both declare a `MidiError`, and the first version of the reader let one
file's verdict answer for the other's raises.  Fixed in
`gestate/complaints.py`, and worth knowing about the tree: two error
classes share a name.
