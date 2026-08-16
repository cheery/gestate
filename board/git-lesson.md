# git-lesson — enough git to follow the changes Claude makes

    status   open — the page is written, the walkthrough is not
    because  auto mode is on, and nothing tells me whether what was done
             was right
    asked    Henri, 2026-08-16
    see      doc/reading-the-log.md (written 2026-08-16, 207 lines)
             journal.md §"The day the machines learned to stop themselves"

## The ask

> teach me git, well enough to follow the changes Claude makes.

## Found by looking, before it was taken

Not a build item, and it should not pretend to be one; it is a session
plus a page.  It is also the one with the most immediate return, because
**auto mode is on** and the deny-list plus the fence stop damage while
doing nothing to say whether what was done was *right*.  That is review,
and review is git.

What it covers, in the order it becomes useful: reading one commit
(`git show`), reading a range (`git log -p`, `git log --stat`),
comparing any two points (`git diff A..B`), finding when something
changed (`git log -S`, `git blame`), and — the part that matters most —
**undoing**: `git revert` for something already committed, `git restore`
for something not, and why neither of those is `reset --hard`, which is
denied to Claude and should be rare for Henri.

## What is done

`doc/reading-the-log.md`, written against *this project's own history*,
so every example is a real commit — several of them commits where Claude
was wrong, because those are the ones worth learning to spot.  Its one
idea: **a commit message is a claim, the diff is the evidence, and
reviewing is checking one against the other.**

## What is left

The live walkthrough: Henri drives, Claude answers.  An hour, whenever
there is one.  Reading a page about review and doing a review are not the
same skill, and the second is the one the card was asked for.

**It is also the card the [git-viewer](git-viewer.md) waits on** — that
viewer is meant to encode this workflow, and a workflow nobody has walked
through yet is not one to build a window around.
