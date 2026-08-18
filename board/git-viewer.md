# git-viewer — a git viewer in the workbench

    status   blocked
    blocked  board/done/command-categories.md — it would add a family of
             commands, and that is what made the categories necessary
    because  a gemba walk through the log should be ergonomic, and my
             friend could use it as well
    asked    Henri, 2026-08-16
    see      board/done/gemba.md — this is gemba's second idea
             board/git-lesson.md — the workflow it would encode
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
