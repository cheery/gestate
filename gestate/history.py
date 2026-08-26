"""The repository, read — `card:git-viewer.md`.

*Henri's ask: "I think we could design a git-viewer into gestate
workbench.  The viewer would encode the workflow that you taught me…
This would suit gemba walks by being more ergonomic and the bonus would
be that my friend could use it as well."*

**A proof of concept, deliberately.**  He asked for the smallest viable
one — *"we commit to the try-something approach"* — so this reads the
log and nothing else, and what it is missing is meant to be found by
reading a real log in it rather than by designing one first.

## `git`, as a subprocess

Rather than a library, and for the reason the card gives: the workflow
being encoded was taught in `git`'s own output (`doc/reading-the-log.md`
is that workflow written down), so a library would be a second opinion
about what a log looks like — and the first thing anybody would do with
a disagreement is check it against `git`.

It is also what makes this small: no dependency, no object model, and
the failure mode of a repository that is not there is a sentence.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

#: How much of the log to read at once.  **A number, because
#: `spec/rocks.md` says a window must not be handed something it cannot
#: draw** — a repository with forty thousand commits is not a reason for
#: the editor to stop responding.
#:
#: **And a page, since 2026-08-26**, because this repository passed the
#: number without anybody being told: 496 commits, and the viewer showed
#: the newest 200 with nothing at the bottom to say so — a query typed
#: into the box searched those 200 and answered *nothing* for a commit
#: that was there.  `commits` takes a `skip`, `count` says what a page
#: is a page of, and `grep` searches the whole log rather than the page.
MOST = 200

#: How wide `git` may draw its `+++---` bar.
#:
#: **Narrow, because the bar is a *note* on a row and the row has a
#: name on it.**  At `--stat=200` a hundred-line change drew eighty-odd
#: plus signs and elided the filename it belonged to, which is the one
#: thing you were reading the row for.  Seen in the window on the first
#: walk through a real log.
_STAT = 60


def root(near=None) -> Path:
    """The repository a path is in, or the working directory's."""
    here = Path(near) if near else Path.cwd()
    here = here.resolve()
    if here.is_file():
        here = here.parent
    for at in (here, *here.parents):
        if (at / ".git").exists():
            return at
    return here


def _git(where: Path, *args: str) -> list:
    """Run `git` there and answer its lines.

    **A refusal is an exception with `git`'s own words in it.**  This is
    a thin thing over a program that already explains itself well, and
    paraphrasing *"not a git repository"* would be inventing a second
    vocabulary for a message somebody may have seen before.
    """
    done = subprocess.run(("git", *args), cwd=str(where),
                          capture_output=True, text=True, timeout=20)
    if done.returncode != 0:
        raise OSError(done.stderr.strip().splitlines()[0]
                      if done.stderr.strip() else "git said nothing")
    return done.stdout.splitlines()


def log(near=None, most: int = MOST) -> list:
    """`git log --oneline`, newest first."""
    return _git(root(near), "log", "--oneline", f"-{max(1, most)}")


def count(near=None) -> int:
    """How many commits there are — what a page is a page *of*.

    A page that does not say how much lies past it is the cut-off
    `spec/rocks.md` refuses: *200 of 496* is a fact, *200* is a list
    that happens to end.
    """
    lines = _git(root(near), "rev-list", "--count", "HEAD")
    return int(lines[0]) if lines else 0


def commits(near=None, most: int = MOST, skip: int = 0, grep: str = "",
            ref: str = "HEAD") -> list:
    """`(sha, subject)` newest first — the `--oneline` view, split.

    Split rather than handed over as one string, because the window
    draws a row as *a thing on the left and a note on the right*, and
    the sha is the thing you pick while the subject is what tells you
    which one to.

    `skip` is the page: the `most` commits after that many.  `grep` is
    `git`'s own `--grep`, case-folded, over the *whole* log — a search
    limited to the page on screen finds nothing for a commit that is
    there, which is the silent kind of nothing.  `ref` is what to read
    back from; a sha prefix and `most=1` is how a typed sha is looked
    up, and a prefix `git` cannot resolve is its own sentence.
    """
    args = ["log", "--oneline", f"-{max(1, most)}"]
    if skip > 0:
        args.append(f"--skip={skip}")
    if grep:
        args += ["-i", f"--grep={grep}"]
    args.append(ref)
    out = []
    for line in _git(root(near), *args):
        sha, _, said = line.partition(" ")
        out.append((sha, said))
    return out


def touched(near=None, sha: str = "HEAD") -> list:
    """`(path, what changed)` for one commit — its `--stat`, split.

    The note is `git`'s own count, kept verbatim: *"12 +++++---"* says
    how big a change is at a glance, which is the whole reason `--stat`
    is the view the workflow was taught in.
    """
    where = root(near)
    lines = _git(where, "show", f"--stat={_STAT}", "--format=", sha)
    out = []
    for line in lines:
        if "|" not in line:
            continue                       # the summary line at the end
        name, _, note = line.partition("|")
        out.append((name.strip(), " ".join(note.split())))
    return out


def show(near=None, sha: str = "HEAD") -> list:
    """A commit's message and what it touched — the second view."""
    return _git(root(near), "show", f"--stat={_STAT}", "--no-patch",
                "--format=%H%n%an, %ad%n%n%B", sha) or [f"{sha}: nothing"]


def diff(near=None, sha: str = "HEAD", name: str = "") -> list:
    """One file's diff inside one commit — the third view.

    **Text, so the window's own machinery draws it.**  A diff is lines
    with a leading character, which is what this editor is already a
    view over; making it a picture would be building a second way to
    show text in a window that has one.
    """
    where = root(near)
    return _git(where, "show", "--format=", sha, "--", name) or \
        [f"{name}: no change in {sha}"]


def at(near=None, sha: str = "HEAD", name: str = "") -> list:
    """A file's lines at one commit, bare — `[]` when it is empty there.

    `whole` is the page and says so when there is nothing to show; this
    is the reading the diff over the file compares against
    (`card:git-viewer.md`), where a sentence standing in for an empty
    file would be one removed line that never existed.  `git`'s own
    refusal for a commit or a path that is not there, as everywhere here.
    """
    return _git(root(near), "show", f"{sha}:{name}")


def whole(near=None, sha: str = "HEAD", name: str = "") -> list:
    """A file as it *was*, at one commit — the fourth view.

    **Shown, not opened.**  Opening it would be the decision the card
    warned about: this window has one idea of what is open, and putting
    a historical file into it means either losing what you were editing
    or growing a second notion of *the file*.  A page costs neither, and
    reading is what the view is for — `doc/reading-the-log.md` teaches
    the log as something you read, not something you check out.
    """
    return _git(root(near), "show", f"{sha}:{name}") or \
        [f"{name}: empty at {sha}"]
