# git-viewer — a git viewer in the workbench

    status   open — a proof of concept landed 2026-08-18
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

### What is left

* **"Show the whole file"** — the fourth view, and the one that needs a
  decision rather than a line: opening a file *at a commit* is a
  different thing from opening the file, and this window has one idea of
  what is open.
* **A repository with forty thousand commits.**  `MOST` is 200 and
  paging past it is unbuilt; `spec/rocks.md` is the argument for doing
  something rather than nothing.
* **"My friend could use it as well"** is still the part to keep in
  view, and is still untested — the card's own note, and it wants
  `card:stranger-test.md`'s instrument rather than another run of mine.
