"""The factory floor, walked — `board/done/gemba.md`.

*Genba*, 現場, "the actual place": the practice of going to where work
happens instead of reading a report about it.  Henri's ask, and the
inversion is the whole point — *"today I read sixteen commit messages
Claude wrote; I want to be where the work is while it happens."*

So: a session says what it is doing, and a box in the workbench shows
it, while it is happening.

## A file, because a file crosses the fence

The channel is **flat lines, tab-separated, verb first**, in a file the
session appends to and the loop reads — the fifth thing in this house
wearing that shape, after crust's program format, the furniture
description, the session trace and the presence record.  Four reasons it
is a file and not a socket, and only the last decided it:

1. No new thread and no socket lifetime, and lifetimes at this seam have
   a history (`Workbench.stop`'s daemon-thread segfault).
2. It survives either side dying.  A session can crash and the last
   thing it said is still on the screen.
3. `cat` debugs it.
4. **It is the only transport that crosses the fence for free.**
   `board/reviewing-by-running.md` puts the workbench inside
   `tools/sandbox.sh`, where the project directory is the one writable
   thing — so a file under it needs no new bind, while a socket or a
   fifo needs the fence widened to admit it.

## Paced to the reader, because neither end can own the pace

This is the card's real finding, and it came from Henri: *"In one hand
'what is happening now' would be great, but you're much faster than me.
I think the design should account for that.  Give me room that I need."*

A narration paced by the *writer* is unreadable when the writer is
faster than the reader.  A log paced by the *reader* is a report, which
is the thing this exists to replace.  So neither end paces it:

* the session appends whenever it likes;
* the box shows **one** item, and holds it for **as long as that item
  takes to read** — its own length, not a constant, because a paragraph
  and a three-word note do not want the same room (*Henri, 2026-08-18:
  "as long as it takes to read it"*);
* and when the queue backs up, **the depth is itself the reading** — the
  box says how far behind it is running.

That last part is the valuable one.  The rate mismatch stops being a
defect to engineer away and becomes the instrument's most useful signal:
*he is going faster than you are following*, which is `spec/author.md`'s
standing problem — the volume outrunning review — made visible while it
is happening instead of discovered in a commit log afterwards.

**As a mark and not a count** (*Henri, same day*), which is
`spec/rocks.md`'s own rule: a number a person has to read is a number a
person will not read.

## What a session writes

    say<TAB>one thing that just happened
    at<TAB>gestate/workbench.py<TAB>854<TAB>this is the line that crashed

**`at` is the walk actually walking**, and it is what the card is named
for.  *Henri, 2026-08-18, on the first version: "'not travelling in
code' means that the editor itself doesn't open a location, eg.
`gestate/workbench.py`, and plant the box after a line you want to
show."*  A `say` narrates from wherever the box happens to stand; an
`at` **takes you to the place** — the window opens that file and the box
stands under that line.  Going to where the work is instead of reading a
report about it is the whole of *genba*, and the first version had the
report half.

Verb first, so a kind this version does not carry costs nothing to add —
`shot <path>` for a picture is the next one, and the box already knows
how to draw pictures because every other content box is one.  A line
whose verb this version does not know is skipped, not refused: the
writer may be newer than the window.

## And it only travels for somebody who asked

**A session that can open files under your hands is a session that can
take the file you were typing in away from you.**  So travelling is
gated on being *subscribed* — the `gemba` command, or a `gemba` line in
the file you are looking at — and a window nobody has subscribed still
shows nothing and opens nothing.  `spec/rocks.md`'s instinct, one floor
over: a thing that acts on your behalf must be something you asked for.
"""

from __future__ import annotations

import os
import time
from dataclasses import dataclass
from pathlib import Path

#: What the file is called, under the project.
NAME = "gemba.tsv"

#: **How fast prose is read**, in words a second — deliberately slow.
#: Three a second is roughly half a comfortable silent-reading rate, and
#: the halving is the point: this is read *while doing something else*,
#: with the eyes coming back to it, not read the way a page is.
WORDS_A_SECOND = 3.0

#: The floor, so a three-word note is still catchable by somebody who
#: glanced away, and the ceiling, so nothing holds the box hostage.
LEAST, MOST = 3.0, 20.0


def project(start=None) -> Path:
    """The project a path belongs to — the directory its repository is in.

    **Both ends have to answer this the same way, and the first version
    did not.**  The workbench rooted the walk at *the file's own
    directory* and a session's `python -m gestate.gemba` wrote to *its
    working directory*, so the two only met when the file being edited
    happened to sit at the top of the tree.  Henri, 2026-08-18, on the
    first walk: **"I don't know how to subscribe to the gemba walk with
    my workbench."**  He could not, and no amount of knowing how would
    have helped.

    So *under the project* is made to mean one thing: the nearest
    ancestor holding a `.git`, or the starting directory when there is
    none.  `presence.py` roots itself the same way and for the same
    reason — the tree being worked on, not the shell it was launched
    from.
    """
    here = Path(start if start is not None else Path.cwd()).resolve()
    if here.is_file():
        here = here.parent
    for at in (here, *here.parents):
        if (at / ".git").exists():
            return at
    return here


def path_for(root=None) -> Path:
    """Where the file is.

    Under the project, for the fence's reason.  `GESTATE_GEMBA` names
    another, which is what a test uses and what a session working on a
    tree other than the one being watched would use.
    """
    told = os.environ.get("GESTATE_GEMBA")
    if told:
        return Path(told)
    return project(root) / NAME


def dwell(text: str) -> float:
    """How long this item stands before the next may replace it.

    **Its own length**, which is the whole of Henri's answer.  A
    constant would give a paragraph the same room as a word and force
    somebody to pick a number that is wrong for one of them; the text
    already knows which it is.
    """
    words = max(1, len(text.split()))
    return min(MOST, max(LEAST, words / WORDS_A_SECOND))


def at(path, line: int, text: str, root=None) -> None:
    """Say something **about a place**, and take the reader to it.

    `path` is written as it is given — a path relative to the project is
    what a session naturally types, and what reads well in the file.
    """
    line = max(1, int(line))
    said = " ".join(str(text).split())
    where = str(path).strip()
    if not said or not where:
        return
    target = path_for(root)
    try:
        target.parent.mkdir(parents=True, exist_ok=True)
        with open(target, "a", encoding="utf-8") as f:
            f.write(f"at\t{where}\t{line}\t{said}\n")
    except OSError:
        pass


def say(text: str, root=None) -> None:
    """Append one thing that just happened.

    **Appended, never rewritten.**  Two sessions may be walking at once
    and neither should have to lock anything: an append of one short
    line is atomic enough on every filesystem this runs on, and the
    worst a race costs is two lines interleaved rather than a file lost.
    """
    line = " ".join(str(text).split())
    if not line:
        return
    where = path_for(root)
    try:
        where.parent.mkdir(parents=True, exist_ok=True)
        with open(where, "a", encoding="utf-8") as f:
            f.write(f"say\t{line}\n")
    except OSError:
        pass


@dataclass
class Item:
    """One thing said, and how long it is owed."""

    kind: str
    text: str
    #: Where it is about — a path and a 1-based line — or `None`.
    #: **This is what makes it a walk rather than a feed.**
    where: tuple | None = None

    @property
    def dwell(self) -> float:
        return dwell(self.text)

    @property
    def path(self):
        return self.where[0] if self.where else None

    @property
    def line(self) -> int:
        return self.where[1] if self.where else 0


class Walk:
    """The queue as the window sees it — one item at a time.

    **The reader's clock, not the writer's.**  `read` takes whatever has
    been appended since last time; `showing` answers what should be on
    screen *now*, which is the same item until it has stood long enough,
    however much has arrived behind it.
    """

    def __init__(self, root=None, clock=time.monotonic):
        self.path = path_for(root)
        self.clock = clock
        #: How many lines of the file have been taken.  **Lines, not
        #: bytes**: a file being appended to while it is read gives a
        #: partial last line, and counting lines means the partial one
        #: is simply not there yet rather than corrupt.
        self.taken = 0
        self.queue: list = []
        self.now: Item | None = None
        self.since = 0.0
        #: The file's size when it was last read, so an unchanged file
        #: costs one `stat` — `Session._outside`'s own instinct.
        self._was = -1

    def read(self) -> int:
        """Take whatever has been said since last time.  Answers how many.

        **A file that shrank is a new walk.**  Deleting `gemba.tsv` is
        how you clear the board, and a session that starts a fresh one
        truncates it; either way the sensible reading is *start again*
        rather than *the numbers are wrong now*.
        """
        try:
            size = self.path.stat().st_size
        except OSError:
            return 0
        if size == self._was:
            return 0
        self._was = size
        try:
            lines = self.path.read_text(encoding="utf-8").splitlines()
        except OSError:
            return 0
        if len(lines) < self.taken:
            self.taken, self.queue, self.now = 0, [], None
        fresh = lines[self.taken:]
        # **A whole line or none.**  The last line of a file being
        # appended to may be half-written; leaving it for next time
        # costs one poll and cannot show half a sentence.
        if fresh and not self.path.read_text(
                encoding="utf-8").endswith("\n"):
            fresh = fresh[:-1]
        self.taken += len(fresh)
        got = 0
        for line in fresh:
            parts = line.split("\t")
            if len(parts) >= 2 and parts[0] == "say" and parts[1].strip():
                self.queue.append(Item("say", parts[1].strip()))
                got += 1
            elif len(parts) >= 4 and parts[0] == "at" and parts[3].strip():
                try:
                    where = (parts[1].strip(), max(1, int(parts[2])))
                except ValueError:
                    continue
                self.queue.append(Item("at", parts[3].strip(), where))
                got += 1
            # Any other verb is skipped rather than refused: the writer
            # may be newer than the window.
        return got

    def showing(self) -> Item | None:
        """What belongs on the screen now.

        The current item stands until its dwell is up; then the next
        takes its place.  **An empty queue does not clear the box** —
        the last thing said stays until there is something to say
        instead, because a box that empties itself is a box you have to
        watch rather than glance at.
        """
        at = self.clock()
        if self.now is None:
            if not self.queue:
                return None
            self.now, self.since = self.queue.pop(0), at
            return self.now
        if self.queue and at - self.since >= self.now.dwell:
            self.now, self.since = self.queue.pop(0), at
        return self.now

    @property
    def behind(self) -> int:
        """How many are waiting — what the mark is drawn from."""
        return len(self.queue)


def main(argv=None) -> int:
    """`python -m gestate.gemba say "…"` — what a session narrates with.

    A command line rather than an import, because the thing doing the
    narrating is usually not Python: it is a session running `git`,
    `pytest` and `cargo`, and the cheapest thing for it to reach for
    between two of those is one more command.
    """
    import argparse

    ap = argparse.ArgumentParser(
        prog="python -m gestate.gemba",
        description="say what you are doing, into a workbench's gemba box")
    ap.add_argument("verb", choices=("say", "at", "clear"),
                    help="`say` one thing, `at` a place, or `clear` the walk")
    ap.add_argument("words", nargs="*",
                    help="what to say — for `at`, `<path> <line> <words…>`")
    ap.add_argument("--root", default=None,
                    help="the project the box is watching (default: here)")
    args = ap.parse_args(argv)

    if args.verb == "clear":
        # **Deleting the file is how you clear the board**, and `Walk`
        # reads a file that shrank as a new walk rather than as an
        # error, so this needs no protocol of its own.
        try:
            path_for(args.root).unlink()
        except OSError:
            pass
        return 0
    if not args.words:
        ap.error("say what?")
    if args.verb == "at":
        if len(args.words) < 3:
            ap.error("at <path> <line> <what to say>")
        try:
            line = int(args.words[1])
        except ValueError:
            ap.error(f"`{args.words[1]}` is not a line number")
        at(args.words[0], line, " ".join(args.words[2:]), root=args.root)
        return 0
    say(" ".join(args.words), root=args.root)
    return 0


if __name__ == "__main__":
    import sys

    sys.exit(main())
