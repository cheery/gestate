# git-viewer — a git viewer in the workbench

    status   open — three views 2026-08-18, the fourth 2026-08-19, paging and the diff over the file 2026-08-26; a stranger is what is left
    because  a gemba walk through the log should be ergonomic, and my
             friend could use it as well
    asked    Henri, 2026-08-16
    see      card:gemba.md — this is gemba's second idea
             card:git-lesson.md — the workflow it would encode
             doc/reading-the-log.md — that workflow, written down

## The ask

> gemba: I think we could design a git-viewer into gestate workbench.
> the viewer would encode the workflow that you taught me.
> It'd have "git log --oneline" view.
> It'd be able to go into commit message and it's --stat view.
> It'd be able to unfold a file for diff viewing, and be able to show the
> whole file.
> This would suit "gemba walks" by being more ergonomic and the bonus
> would be that my friend could use it as well.

## Not yet elaborated

Nothing has been looked at for this card, and it is blocked twice over —
once on `command-categories`, and once in the softer sense that the
workflow it would encode has been *written* (`doc/reading-the-log.md`)
but not yet *walked* (`git-lesson`).  Encoding a workflow into a window
before anybody has used it is how a window ends up shaped like the
document rather than like the work.

When it is taken, the elaboration owes: which of the four views are
rows in a content box and which are their own view, whether a diff is
text (so the editor's own machinery draws it) or a picture, what reads
the repository — a `git` subprocess or a library — and what happens when
the answer is thousands of lines, which `spec/rocks.md` already has an
opinion about.

**"My friend could use it as well" is the part to keep in view.**  It is
the first ask in this project aimed at somebody who is not Henri, and
that changes what "ergonomic" has to mean.

## The proof of concept, 2026-08-18

*Henri: "we take git-viewer to our teeth because it's similar to gemba,
very important for working together.  This time we commit to the
try-something approach.  Implement the smallest viable proof-of-concept
program."*

**Three of the four views, walked in the real window.**  `log` opens the
question; a commit is a *step* into its message and `--stat`; a file
inside it is the answer, and its diff is the page.

`gestate/history.py` is the whole reader — `git` as a subprocess,
because the workflow being encoded was taught in `git`'s own output and
a library would be a second opinion about what a log looks like.

### What the running window said that reading did not

**A page is drawn beside the list, so a command that closes the list has
nowhere to put one.**  The first version answered *"200 commits"* into
the status bar and showed nothing at all.  One run.

**And stepping is the palette's own mechanism.**  The second version
hand-rolled it in the model — set the page, re-ask — which worked
*perfectly headlessly* and did nothing in the window, because the
palette had already finished its call.  A commit row carries a `step`
now, and the model hears it as `wants`, which is the one hook that sees
a step happen and is therefore where the message is read.

**The bar is a note on a row and the row has a name on it.**
`--stat=200` drew eighty-odd plus signs and elided the filename it
belonged to — the one thing you were reading the row for.

### The first pull, and it names the diff view — 2026-08-20

*Henri, at the end of a day whose last job was reading five commits:*

> *"this brings the first pull request on git viewer for a little
> while.. I'd like if the diff would be shown to me with content boxed
> overlayed over the original file.  Or some other similar solution.
> The gist is, I'd like to see which lines go away which come in, within
> the editor."*

**Note where it came from.**  The card was written 2026-08-16 and has
sat since; `spec/author.md`'s triage question 2 is *have I wanted this
while working, in the last week*, and until tonight the honest answer
was no.  This is the first time the want arrived from work rather than
from an idea, which is the thing that distinguishes a card from a
`later/`.

**And it answers one of the elaboration's own open questions** —
*"whether a diff is text (so the editor's own machinery draws it) or a
picture"*.  His answer is neither and both: the *file* is text, and the
diff is furniture hung on it.

**The mechanism is suspected, not established** — a session's guess, and
by the elaboration rule the part a reader trusts most and the part most
likely to be wrong.  It looks like the box machinery this window already
has: `View::slots` grants a band under a line, `frame_with` paints into
it, and the fold rule is settled (F132, F139).  A **removed** line has
no home in the document — it is not in the file any more — which is
exactly the shape a box exists for, the same as a trouble or a scope.
An **added** line is already in the text and wants a mark, not a box.
If that holds, the view costs a `Furniture` reader over `git diff` and
almost no new drawing; if it does not, this paragraph is the thing to
throw away first.

**Both of the session's open questions were answered within the hour, and
one of them was a bad question.**

*Forty removed lines:* **"box grows or there are multiple boxes."**
Settled, and it needed one line because the box machinery already grants
per-line bands and `BOX_MOST` already caps them.

*Whether an overlay is a mode:* **"we already have gemba as a mode.
There comes a green box into it."**  Correct, and the tree says so in its
own code — `view.rs` draws `[gemba]` in the bar in `LIVE` green because
*"a mode you cannot see is a mode you will be surprised by, and this one
opens files."*  So `vision.md`'s *"gestate won't grow modes"* was never
a prohibition on states; the implemented rule is that **a mode must
announce itself**, and `[gemba]` is the worked example.

**And the vision line means modal *input*, which was tried and
rejected:** *"we did try vim idea and discarded it."*  That is what the
promise forbids — a window where the same key does two things depending
on a state — not furniture drawn over a file.

**His frame, which is the useful one:** *"these are extensive, not
particularly in the lifeblood of the editor itself."*  The diff overlay
and the gemba box are **additions** — they hang on the document and
change nothing about what typing does.  A feature that touches the
editing model is a different class of change from one that draws on top
of it, and only the first is what *"won't grow modes"* was written
against.  Worth carrying past this card.

### What is left

* **"My friend could use it as well"** is still the part to keep in
  view, and is still untested — the card's own note, and it wants
  `card:stranger-test.md`'s instrument rather than another run of mine.
* **The diff in the `log` walk.**  `diff <commit>` reads whichever file
  is open against that commit; it does not yet hang off a commit's file
  row in the walk, which is where reading a session's commits would
  want it.  Not asked for yet — the card's own rule about wants that
  arrive from work.

**Shaped and answered, 2026-08-26.**  Three choices were put to him with
defaults; his line back: *"open file versus HEAD, first that.  I think it
could be entered by 'diff commit-to-compare-with'.  removed lines just
like you describe.  Removed lines should appear where they were removed
from."*  So: the open file against a commit, `HEAD` when none is named;
`diff <commit>` enters it; a removed line is boxed at the place it left,
an added one is marked.

### Landed since, and the list above had not been told

* **The diff over the file — 2026-08-26**, the same day the shape was
  answered.  `diff <commit>` (`HEAD` when none is named) reads the
  *buffer* against `git show <commit>:<path>`; each line the commit had
  and the text has not crosses as a `gone` row and is **boxed under the
  line it was removed from** — a run deleted between two lines under
  the line before the gap, a run replaced under the last of the lines
  that took its place, a run cut from the top under line one — one row
  each, in `AWAY`, at the text's own left edge; each line the commit
  had not crosses as `added` and gets the gutter's mark in `LIVE`; and
  the bar says `[diff HEAD]` while it stands, because furniture hung on
  the file is a state and `[gemba]`'s rule is that a state says so.
  The same command again clears it.  The guess above held: it cost a
  `difflib` reading on the model side, three verbs on the wire, and the
  box machinery already there — nothing about typing changed.
  `test/test_diffview.py` holds the rows, `tests/view.rs` the drawing,
  and it was walked in the real window on Xvfb against a scratch commit
  with three lines cut and one added:
  `test/driven/20260826-063711-diff-view/`, four shots — the three
  stand under line 6, where they left.
* **`change` and `changeBack` — the same afternoon.**  Henri, on
  seeing the diff: *"the diff could use a sibling command that allows
  to jump into the next/previous change."*  `find`/`findBack`'s pair,
  on `goto`'s rule — from the caret, wrapping, so again means *next* —
  and **one change is one hunk**: the caret lands on the first line of
  a run that came, or on the line a run went from, never once per line.
  The sentence counts them: *line 6 — change 2 of 3*.  Held in
  `test/test_diffview.py`; not driven, because the jump is the `goto`
  order the window already obeys and nothing new is drawn.

* **"Show the whole file"** — `whole`, in `6f5197d` (2026-08-19),
  *shown, not opened*: a page, so the window keeps its one idea of what
  is open.  The decision this list said it needed was taken there.
* **Paging — 2026-08-26.**  The want was measured before it was built:
  this repository had **496 commits** and `MOST` is 200, so the viewer
  showed the newest 200 with nothing at the foot to say so, and a word
  typed into the box searched those 200 and answered *nothing* for a
  commit that was there — the silent kind of nothing `vision.md`
  refuses.  Now the first page ends in an `older` row and every later
  page opens with a `newer` one, both **steps** — Return turns the page
  the way it steps into a commit, so the palette learned nothing new —
  and the note carries the count, *50 more of 250*, because a list that
  stops is not a fact and *200 of 496* is.  A word searches the whole
  log through `git`'s own `--grep`, and a typed sha is looked up as
  itself first.  `test/test_history.py` §"Paging" holds it, and it was
  walked in the real window on Xvfb against a scratch log of 250:
  `test/driven/20260826-062028-log-paging/`, four shots.  **Two things
  the photographs said that the tests did not:** the bar counts the step
  rows among the names (*201 name(s)* for 200 commits), which is the
  same count `open` gives with its directories and is left alone; and
  the box reads `@0` after coming back to the top, because the page is
  the query — honest, and a person can clear it.
