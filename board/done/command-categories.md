# command-categories — the command list wants categories

    status   done — 2026-08-18
    because  it's starting to be clear that we need them
    asked    Henri, 2026-08-16
    see      gestate/command.ges — the command table, and its headings
             gestate/session.py — `vocabulary`, `_sections`, `Verb.section`
             test/test_command_sections.py — the derivation, held
             spec/workbench.md §"The list, and the laws it keeps"
             board/button.md — a stranger opened this list and found names
             board/gemba.md — the second idea waits on this
             board/git-viewer.md — blocked by it

## The ask

> blocks the second idea on gemba
>
> We probably are starting to need categories for the commands.
> It's starting to be clear now that we do.

## Found by looking

**The categories were never missing.**  `command.ges` has been written
in labelled sections since it existed — eleven of them, by hand, in the
file that *is* the command list:

| section | commands |
|---|---:|
| The instrument | 5 |
| The loop | 3 |
| Parameters | 2 |
| Notes | 6 |
| Performing | 3 |
| Chance | 2 |
| The text | 18 |
| Laying it out | 4 |
| Leaving the workshop | 4 |
| The window | 5 |
| The algebra | 1 |

Nothing read them.  `_summaries` takes the `#:` doc comments and skips
plain `#` lines, so fifty-three names arrived at the palette flat, with
the grouping their author had already done thrown away one function
earlier.

**This is the third time today the same shape has turned up**: the
window's own order was already the file's (F150), a complaint's
position was already on the node (F152), and here the category was
already the heading.  In each, nothing needed inventing — it needed
carrying through.  Worth saying out loud as a habit to check for.

### What has landed, and why only this much

`Verb.section` is derived, `test_command_sections.py` holds it, and
**nothing in the window has changed.**  That split is deliberate: every
option below needs the fact, and none of them is settled, so by
`manifesto.md` §"Set-based, not point-based" rule 3 the fact ships and
the display waits.

It cost one thing immediately, which is the argument for deriving early:
a heading written that same morning read *"The algebra's identity, last
on purpose"* — a fine comment and a poor label, invisible as a defect
until something read it as a name.  A header is a label the moment
anything reads it, and the test now says so.

### The three answers the card owed

**How many, and how ordered.**  Fifty-three; 16 carry a key, 29 take
arguments.  The order is `command.ges`'s own, deliberately —
`vocabulary`: *"the order somebody thought about them rather than
alphabetically, which is a worse order for learning."*

**What the palette would do.**  The ranking is entirely model-side
(`Session.filtered`: exact 0, prefix 1, substring 2, no query 3,
summary 4, file order as tiebreak) and `palette.rs` opens by saying it
*"does not rank… it is handed its entries and shows them in the order it
was given."*  So any option here is a change to `session.py` plus, at
most, one to how a row is drawn — the window's law is untouched either
way.

**What the vocabulary rule says.**  *"A capability cannot exist without
a name, a type and a sentence — because that is what declaring one
is."*  A section has a name and a sentence's worth of meaning, and no
type.  Leaving the headings as comments and *reading* them keeps the
rule where it bites (a **command** is a declaration) without inventing a
second declared thing to maintain.

## The options, and what would eliminate each

**A. Group the rows under their headings.**  Same fifty-three, same
order, a dim heading before each run.  *Eliminated if* eleven extra rows
make the list worse to scroll than it is to read, or if a heading reads
as something choosable — which is the same mistake `skip` was.

**B. Let a category be something the query matches.**  Typing `notes`
ranks the six in *Notes* together.  One line in `Session.filtered`.
*Eliminated if* the words collide: `text`, `window` and `loop` are all
plausible queries **and** section names, and a query that means two
things is worse than one that means none.

**C. Two levels — pick a category, then a command.**  The `Step`
machinery already exists (a directory is a step, not an answer).
*Eliminated by* the cost falling on everybody who knows the name, which
is the common case: one extra keystroke on every command to help the
first week.

**D. A category shown per row** — a word or a mark in the margin of each
entry.  *Eliminated if* it is the same information as A in a weaker
channel, which is the suspicion: position groups better than a repeated
label.

**E. Nothing; the order is enough.**  The null, and it is not empty —
the order is already curated and already teaches.  *Eliminated by*
`git-viewer` landing a family of commands, which is what made the need
clear and is the card this one blocks.

**Decided 2026-08-18: A.**  *Henri, picking from the five.*

The argument that carried it is the one the options were written to
expose: **A is the only one that spends position**, which is the
strongest channel this list has and the one nothing uses — and that is
also what eliminates D, since a repeated label in a margin is the same
information through a weaker channel.  B stays out because `text`,
`window` and `loop` are section names *and* plausible queries, and a
query that means two things is worse than one that means none.  C taxes
everybody who already knows the name, forever, to help the first week.
E was defensible until `git-viewer` — a family of new commands arriving
is what made the need clear in the first place.

**And the caveat is kept rather than dropped**, because it is still
true: what *would* decide this is a person opening the list and looking
for something they cannot name, which is `board/stranger-test.md`'s
instrument.  A pick made from the armchair is a judgement, not
evidence.  The reason it is safe to make anyway is that **A is the
cheapest of the five to reverse** — eleven dim rows and no change to
what a command is, what it is called, or how it ranks.  If a stranger
finds the list no easier, nothing has to be unwound to try something
else.

## On icons — asked, and the honest answer is *not yet*

*Henri, 2026-08-17: "We could maybe also create small icons for
categories or commands. whichever appears better, or neither."*

**Neither, and here is what would change that.**

* The window is a **text grid** drawn from a 3×5 bitmap font.  An icon
  is a glyph, and a glyph in that grid is one character cell — the same
  budget as the burger, which is the one control in this window and
  which a stranger could not see at all (`button.md`: 24 lit pixels,
  2.3:1).  **The evidence that this window's symbol channel is weak is
  today's, and it is strong.**
* Per-*command* icons are fifty-three decisions and a maintenance
  surface, for rows that already carry a name and a sentence.
* Per-*category* icons only pay once categories are **visible as
  groups** — which is option A, undecided.  An icon for a category
  nobody can see is decoration.
* And the cheaper channel is untried: these rows have a name, a
  summary, and for sixteen of them a key, all in one weight of ink.
  Grouping, dimming, and column position are all free and all unspent.

So: **not neither-forever, but not first.**  What would make icons the
right answer is A landing and *something still being hard to find* —
which is a finding a person produces, not a design that can be argued
into existence.

## What the work is

1. ~~Derive the section from the file.~~  Done, 2026-08-17.
2. ~~Choose between A–E.~~  **A**, 2026-08-18 — see above.  What is
   left is the display: `Session.filtered` emits the heading rows in
   file order, and `palette.rs` draws a row it is told is a heading
   *dim and unpickable*.  The window's law is untouched — it is still
   handed entries and shows them in the order it was given.
3. Whatever is chosen, `git-viewer`'s family is the test of it: the
   card exists because a group of new commands is coming.
4. Icons, only if 2 lands and the list is still hard to read.

## Done

*2026-08-18.  `journal.md` §"The heading was already the heading" tells
the story.*

**A section per row, not heading rows on the wire.**  The card's own
sketch said `Session.filtered` would emit heading rows and the window
would draw them dim and unpickable.  What landed is better and smaller:
each `command` row carries the run of `command.ges` it was declared in,
and `palette.rs` draws a heading wherever that changes.  Nothing has to
agree about where a heading *goes*, the model sends the same commands in
the same order it always sent, and **a window that does not know the
field shows exactly the flat list it showed before** — which is the
degradation this wire keeps asking for and rarely gets for free.

**Empty while a query is up.**  Filtering re-ranks, so the runs break
into ones and twos and eleven headings become noise over a list somebody
has already narrowed.  A person who has typed something is looking for a
match, not for a taxonomy.  The model decides it, because the model is
what knows whether a filter is on.

**Two index spaces, kept apart.**  `at` is an *entry*, because that is
what a person picks and what `selected` returns; the drawn list is
longer.  So **a heading is unpickable by construction rather than by a
rule** — there is no value of `at` that names one, and nothing has to
refuse anything.  What that cost is one honest separation: every bound
on the cursor is against `pickable_len`, every bound on the scroll is
against `shown_len`, and a click arrives as a drawn row and is
translated.  Getting it backwards walked the pick off the end of the
entries by one step per heading above it — **caught by the test written
before the fix**, which is the only reason it is a paragraph here rather
than a defect later.

**Held by** six tests in `shell/editor/tests/palette.rs` (a heading
where the section changes, one per run and not per row, unpickable, dim,
a sectionless list drawing what it always drew, and the pick staying in
the window with headings above it) and three in
`test/test_command_sections.py` (every row carries its section, the
sections cross as contiguous runs, and a query sends none).

**Turned up and not this card's job:** `test_doc_commands.py` reads
every `python -m …` in `doc/*.md` and takes the words after it as flags,
so `doc/complaints.md`'s generated marker read `-->` as a flag nobody
has.  The marker closes on its own line now.  Worth knowing:
`doc/ref/index.md` has the same comment and escapes the check only
because it lives one directory further down.
