"""What was done to the editor, written down — `spec/verification.md`.

    A session is a list of commands, so recording, replaying and testing
    stop being three mechanisms and become one.

That is `spec/workbench.md`'s claim about the command language, and this
is it built.  Every command goes through `Session.run`, which is one
choke point, and every command already returns a sentence — so a
recording is the names that went in and the sentences that came out, and
nothing had to be instrumented to get it.

**Why it exists.**  The editor's half of this project has no oracle, and
that is where every defect has come from: nine in the Python around the
engine (`journal.md`, stage 10, four of them silent), twelve in the
editor rewrite, six more the session after — all found by a person, none
by a test, with two thousand tests passing throughout.  A transcript
does not *find* any of those.  It **keeps** them: a bug found by playing
is captured by having been played, and the reproduction is checked in
beside the fix the way a `.samples` golden is.

**It is gestate syntax, and honestly not a gestate program.**
`spec/workbench.md` argues a recorded session should be a file you can
read, edit, diff and re-run in the language you were already editing,
and it reads exactly that way.  What it is not is something the compiler
would accept standing alone: `command.ges` says of `Named` that
*"nothing here constructs one — only the editor can, because only the
editor has the program being edited and its inferred types"*, so
`set cutoff 0.42` names a declaration that exists in a window and
nowhere else.  Replaying is therefore the editor's job, which is where
the names are.  Saying so is better than a format that looks
typecheckable and is not.

**The sentences ride along as comments.**  They are what a diff is
taken on — the whole value of a replay is that the answers come back the
same — and a comment is where a thing that is read but not run belongs.
The formatter keeps them now (`spec/comments.md`), which it did not
before this was worth writing.
"""

from __future__ import annotations

from dataclasses import dataclass, field

#: How many transitions a session keeps.  **A recording, not a record**:
#: what is wanted is the run-up to whatever just went wrong, and a
#: window of a few thousand is more than any hand produces in a sitting.
KEEP = 4000

#: What a replayed sentence is compared against, marker included, so the
#: file reads as a transcript rather than as a program with opinions.
SAID = "#="


@dataclass
class Step:
    """One transition: what was asked, and what it answered."""

    verb: str
    args: tuple = ()
    said: str = ""

    def line(self) -> str:
        """`    seek 4    #= at bar 4` — one command of a `do` block."""
        spoken = " ".join(_literal(a) for a in self.args)
        call = f"{self.verb} {spoken}".strip()
        return f"    {call:<38} {SAID} {self.said}".rstrip()


@dataclass
class Log:
    """A session, as it happens.

    Held in memory and written when asked for.  **Not streamed to disk**:
    a transcript is wanted after something has gone wrong, and a file
    growing under every keystroke of every session is a thing somebody
    has to clean up rather than a thing they reach for.
    """

    steps: list = field(default_factory=list)
    #: What was being edited when it started, for the header.
    path: str = ""

    def add(self, verb: str, args, said: str) -> None:
        self.steps.append(Step(verb, tuple(args), said))
        if len(self.steps) > KEEP:
            del self.steps[:len(self.steps) - KEEP]

    def text(self) -> str:
        """The whole session, as a file."""
        head = ["# A gestate editor session — replay it with",
                "#",
                "#     python -m gestate.sessionlog <this file>",
                "#"]
        if self.path:
            # **Machine-readable, because the replay needs it.**  A
            # transcript is only honest replayed against the program it
            # was recorded against — a fresh workbench on the same file
            # is the same starting state, and any other file is a
            # different session wearing these commands.
            head.append(f"#: editing {self.path}")
            head.append("#")
        head.append("# Each line is a command and what it answered.  The")
        head.append("# answers are the diff: a replay that says something")
        head.append("# else is the report.")
        body = [s.line() for s in self.steps] or ["    skip"]
        return "\n".join(head + ["", "do"] + body) + "\n"


def _literal(value) -> str:
    """One argument, as it would be typed.

    Text is quoted and numbers are not, which is the only distinction
    the reader back out has to make — and it makes it the same way,
    below.
    """
    if isinstance(value, bool):
        return "1" if value else "0"
    if isinstance(value, (int, float)):
        return repr(value)
    text = str(value)
    return '"' + text.replace("\\", "\\\\").replace('"', '\\"') + '"'


def _value(word: str):
    """And back — a quoted word is text, a bare one is a number if it
    looks like one and a name otherwise."""
    if word.startswith('"'):
        return word[1:-1].replace('\\"', '"').replace("\\\\", "\\")
    try:
        return int(word)
    except ValueError:
        pass
    try:
        return float(word)
    except ValueError:
        return word


def _words(rest: str) -> list:
    """Split arguments, keeping a quoted one whole."""
    out, held, quoted, escaped = [], [], False, False
    for ch in rest:
        if escaped:
            held.append(ch)
            escaped = False
        elif ch == "\\" and quoted:
            held.append(ch)
            escaped = True
        elif ch == '"':
            quoted = not quoted
            held.append(ch)
        elif ch.isspace() and not quoted:
            if held:
                out.append("".join(held))
                held = []
        else:
            held.append(ch)
    if held:
        out.append("".join(held))
    return out


def read(text: str) -> list:
    """The `Step`s a transcript holds, in order.

    **Lenient about everything but the call.**  A transcript is read
    long after it was written, by a build that may have moved on, and a
    line it cannot parse is one step lost rather than the recording
    refused — the same rule the furniture wire keeps, and for the same
    reason: what must not happen is losing the reproduction.
    """
    out = []
    for line in text.splitlines():
        body = line.strip()
        if not body or body.startswith("#") or body == "do":
            continue
        said = ""
        if SAID in body:
            body, _sep, said = body.partition(SAID)
            said = said.strip()
        words = _words(body.strip())
        if not words:
            continue
        out.append(Step(words[0], tuple(_value(w) for w in words[1:]), said))
    return out


def editing(text: str) -> str:
    """The file a transcript was recorded against, or `""`."""
    for line in text.splitlines():
        body = line.strip()
        if body.startswith("#: editing "):
            return body[len("#: editing "):].strip()
        if body and not body.startswith("#"):
            break
    return ""


def replay(session, steps) -> list:
    """Run them, and give back what changed.

    `(step, what it said this time)` for every step whose answer moved.
    **An empty list is the whole point**: a session that replays to the
    same sentences is one this build still behaves the way it did when
    somebody was sitting in front of it.
    """
    drifted = []
    for step in steps:
        now = session.run(step.verb, *step.args)
        if step.said and now != step.said:
            drifted.append((step, now))
    return drifted


def main(argv=None) -> int:
    """Replay a transcript with no window and report what moved."""
    import argparse
    import sys
    from pathlib import Path

    ap = argparse.ArgumentParser(
        prog="python -m gestate.sessionlog",
        description="Replay an editor session and report what it says now.")
    ap.add_argument("file", help="a transcript written by `transcript`")
    ap.add_argument("--against", default=None,
                    help="the .ges to replay against, if it has moved")
    ap.add_argument("--rate", type=int, default=8000,
                    help="sample rate for the workbench (default 8000)")
    args = ap.parse_args(argv)

    from .audioeditor import Workbench
    from .session import Detached, Session

    text = Path(args.file).read_text()
    steps = read(text)
    if not steps:
        print(f"{args.file}: nothing to replay", file=sys.stderr)
        return 1

    # **Against the program it was recorded against, or not at all.**
    # A fresh workbench on the same file is the same starting state; a
    # bare stand-in would refuse every transport command and report the
    # whole session as drift, which is a wall of noise where a report
    # should be.  Better to say what is missing.
    against = args.against or editing(text)
    if not against:
        print(f"{args.file}: says nothing about what it was recorded "
              f"against; give it with --against", file=sys.stderr)
        return 1
    if not Path(against).exists():
        print(f"{against}: not here, so there is nothing to replay "
              f"against (--against names another copy)", file=sys.stderr)
        return 1

    # No `start()`: the commands answer from the model, and a replay
    # that opened a sound card would be a replay you cannot run twice.
    bench = Workbench(Path(against), rate=args.rate, block=256)
    drifted = replay(Session(bench=bench, view=Detached()), steps)
    print(f"{len(steps)} steps replayed against {against}")
    for step, now in drifted:
        print(f"  {step.verb} {' '.join(map(str, step.args))}\n"
              f"      was: {step.said}\n      now: {now}")
    if not drifted:
        print("every answer is the one it gave before")
    return 1 if drifted else 0


if __name__ == "__main__":
    raise SystemExit(main())
