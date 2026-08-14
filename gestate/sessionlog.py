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

import difflib
from dataclasses import dataclass, field

#: How many transitions a session keeps.  **A recording, not a record**:
#: what is wanted is the run-up to whatever just went wrong, and a
#: window of a few thousand is more than any hand produces in a sitting.
KEEP = 4000

#: What a replayed sentence is compared against, marker included, so the
#: file reads as a transcript rather than as a program with opinions.
SAID = "#="


#: The step that stands for typing.  **Not a command**, and deliberately
#: not declared in `command.ges`: nobody picks "edit" out of a palette,
#: and a verb in the list that cannot be chosen would be the list ceasing
#: to be the answer to *what can this do*.  The replayer knows it; the
#: editor never offers it.
EDIT = "edit"

#: The step that stands for a question the editor asked.
#:
#: **The verbs were recorded and the questions were not**, and the
#: questions are where the defects have been.  `Session.run` is one
#: choke point and everything through it was kept; `Session.choices` is
#: the other and nothing through it was, so a dialog that offered the
#: wrong rows replayed as a session that said all the right sentences.
#: The first bug a user of this editor reported lived exactly there.
#:
#: Same rule as `edit`: not in `command.ges`, because nobody picks
#: "ask" out of a palette.
ASK = "ask"

#: A message the model volunteered — recorded for the reader, skipped by
#: the replay.  Spelled as a comment marker so a transcript needs no new
#: grammar: `read` already ignores it.
NOTE = "#!"

#: The argument types whose answer is about the **world** and not about
#: the program in the window.
#:
#: A directory can change under a dialog and a MIDI socket can be
#: unplugged, so a replay of one of these is expected to drift — the
#: world moved, and it moving is not the build misbehaving.  Everything
#: else — `what`'s names, the templates, the symbols — is a function of
#: the text being edited and must come back identical.
#:
#: **The distinction is the difference between a report somebody reads
#: and one they learn to ignore.**  Without it a replay returns "these
#: eleven things drifted" on any machine whose `examples/` has gained a
#: file, and the eleventh, which mattered, is read as noise like the
#: other ten.
OUTSIDE = ("Path", "Device")


def digest(rows) -> str:
    """What was on offer, in sixteen characters.

    **Hashed rather than kept, which is the whole budget.**  A listing
    of `examples/audio` is 63 rows and about 1.9 KB written out, against
    48 bytes for the question and this — forty to one, and a transcript
    is held in memory for the length of a session.  The engine half
    already settled this argument: `spec/verification.md` records "a
    hash of every rendered block", and hashing is what makes an oracle
    total instead of a handful of spot checks.

    **The names, and only the names.**  A row also carries what it is —
    a size for a file, `listening` for a port — and folding that in
    would move the digest every time a file being written grew a
    kilobyte, which is a question nobody asked.  What was offered is the
    names.
    """
    import hashlib

    joined = "|".join(str(row[0]) for row in rows)
    return hashlib.blake2b(joined.encode("utf-8", "replace"),
                           digest_size=8).hexdigest()


def answer(rows) -> str:
    """`63 rows 4f2a1b2c3d4e5f60` — an ask step's `said`.

    The count is for the person reading the transcript, who wants to
    know whether the list was empty without running anything; the digest
    is for the diff.
    """
    n = len(rows)
    return f"{n} row{'s' if n != 1 else ''} {digest(rows)}"


def fingerprint(lines) -> str:
    """The text a session began on, in sixteen characters.

    The same budget argument as `digest`, one floor up: the header
    wants to say *which* text the recording started from, and carrying
    the file would make every transcript that session's file over
    again.  Over the lines joined, so the trailing-newline question —
    which editors answer differently — is no part of the identity.
    """
    import hashlib

    joined = "\n".join(lines)
    return hashlib.blake2b(joined.encode("utf-8", "replace"),
                           digest_size=8).hexdigest()


def world_dependent(step) -> bool:
    """Is this a question whose answer the world can move?

    The recorded kind decides, rather than a list of verbs kept here: a
    command that grows a `Path` argument tomorrow is classified by the
    same rule with nothing edited.
    """
    return step.verb == ASK and len(step.args) > 2 and step.args[2] in OUTSIDE


@dataclass
class Step:
    """One transition: what was asked, and what it answered."""

    verb: str
    args: tuple = ()
    said: str = ""
    #: For an `edit`, the diff to read — the ops are for replaying and
    #: this is for the person the recording is *for*.
    shown: tuple = ()

    def line(self) -> str:
        """`    seek 4    #= at bar 4` — one command of a `do` block."""
        if self.verb == NOTE:
            # What the model said unasked, kept as a comment: readable
            # in place, skipped by `read`, demanded of no replay.
            return f"    {NOTE} {self.said}".rstrip()
        spoken = " ".join(_literal(a) for a in self.args)
        call = f"{self.verb} {spoken}".strip()
        return f"    {call:<38} {SAID} {self.said}".rstrip()

    def lines(self) -> list:
        """The step, with the typing shown above it when there was any."""
        return [f"    # {line}" for line in self.shown] + [self.line()]


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

    #: The text as of the last step recorded, so typing can be a diff.
    was: tuple = ()

    #: The text the recording began on — `was` as first seeded — and
    #: whether it was on disk then.  The header carries the
    #: fingerprint always, and the text itself when the file was
    #: unwritten: a session on an unsaved `untitled.ges` used to
    #: replay against nothing, because the recording named a file that
    #: never existed.
    base: tuple | None = None
    unwritten: bool = False

    def typed(self, lines) -> None:
        """Record the typing since the last step, if there was any.

        **Between commands, not per keystroke.**  A step per character
        would bury the six things somebody actually did under four
        hundred they did not think of as doing anything — and the window
        does not send the text with `edited` anyway, by design: shipping
        the document on every keystroke is the cost the ABI exists to
        avoid.  What matters for a reproduction is that the text is right
        *when a command runs*, and this is that.

        Kept as edit operations rather than as the whole file: a
        transcript of a long session would otherwise be that session's
        file over and over, and the thing worth reading — *what changed*
        — would be the part you had to work out.
        """
        after = tuple(lines)
        if after == self.was:
            return
        ops = _ops(self.was, after)
        if ops:
            self.steps.append(Step(EDIT, ops, _counted(self.was, after),
                                   _shown(self.was, after)))
        self.was = after

    def add(self, verb: str, args, said: str) -> None:
        self.steps.append(Step(verb, tuple(args), said))
        if len(self.steps) > KEEP:
            del self.steps[:len(self.steps) - KEEP]

    def slid(self, verb: str, args: tuple) -> None:
        """A continuous gesture's step — consecutive steps of one verb
        on one target coalesce to where the slide ended.

        The dialog's rule (`Session._asked_about`), for the same
        reason: a fader ride is thirty motion events a second, and a
        step per event would push the run-up to the bug off the top of
        the `KEEP` window the recording exists to hold.  What a
        reproduction needs is where the hand left it.
        """
        args = tuple(args)
        if self.steps and self.steps[-1].verb == verb \
                and self.steps[-1].args[:1] == args[:1]:
            self.steps[-1] = Step(verb, args, "")
            return
        self.add(verb, args, "")

    def note(self, message: str) -> None:
        """A sentence the user was shown that no command asked for.

        A rebuild finishing, a canvas refusing, a worker landing — the
        model says these on its own schedule, they cross the status
        line, and until now they left no mark here.  So a transcript
        could hold a session whose visible story was *"errors
        everywhere"* and read as if nothing happened — which is exactly
        the transcript that was reached for when untitled.ges's canvas
        would not build (2026-08-12), and it did not contain the one
        sentence that explained everything.

        **Written as a comment, deliberately.**  `read` skips `#` lines
        and `replay` skips `NOTE` steps, so a note is evidence for the
        person reading, never an instruction for the machine: what the
        model volunteers depends on threads and clocks, and a replay
        that demanded the same weather would drift on every run.
        """
        self.steps.append(Step(NOTE, (), message))
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
            if self.base is not None:
                # Which *text* that was, not only which name: the file
                # can move on under the name, and a replay against the
                # moved file is a different session wearing these
                # commands — the fingerprint is what lets the replay
                # say so instead of drifting mysteriously.
                head.append(f"#: began {fingerprint(self.base)}")
            head.append("#")
        if self.base is not None and self.unwritten:
            # The file was never on disk, so the name above points at
            # nothing — the text itself rides here and the replay
            # starts from it.  Only then: an ordinary session's file is
            # already the better copy of this.
            head.append("# The file was not written when this began; its")
            head.append("# text rides below and the replay starts from it.")
            head.extend(f"#. {line}" for line in self.base)
            head.append("#")
        head.append("# Each line is a command and what it answered.  The")
        head.append("# answers are the diff: a replay that says something")
        head.append("# else is the report.")
        body = [line for s in self.steps for line in s.lines()] \
            or ["    skip"]
        return "\n".join(head + ["", "do"] + body) + "\n"


def _ops(before, after) -> tuple:
    """The edits between two files, one `at:removed:added` per argument.

    Exact rather than a unified diff, because the replay has to
    reconstruct the text and not merely describe it — and because a patch
    applier is a second thing to get right where `difflib` has already
    worked out the answer.

    **One op per argument, and newlines escaped.**  The first spelling
    packed them into a single string with `\x1f` and `\x1e` between,
    which is invisible in a file whose whole promise is that you can read
    it, edit it and diff it.  Arguments the reader already knows how to
    split cost nothing and are legible.
    """
    out = []
    for tag, i1, i2, j1, j2 in _blocks(before, after):
        if tag == "equal":
            continue
        out.append(f"{i1}:{i2 - i1}:" + "\n".join(after[j1:j2]))
    return tuple(out)


def _blocks(before, after) -> list:
    return difflib.SequenceMatcher(a=list(before), b=list(after),
                                   autojunk=False).get_opcodes()


def _apply(before, ops) -> tuple:
    """`before` with those edits made — the other half of `_ops`."""
    lines = list(before)
    # Back to front, so an earlier edit does not move a later one.
    for group in reversed([str(g) for g in ops if str(g)]):
        at, gone, added = group.split(":", 2)
        at, gone = int(at), int(gone)
        lines[at:at + gone] = added.split("\n") if added else []
    return tuple(lines)


def _counted(before, after) -> str:
    """*3 lines changed* — what the step says it did."""
    changed = sum(max(i2 - i1, j2 - j1)
                  for tag, i1, i2, j1, j2 in _blocks(before, after)
                  if tag != "equal")
    return f"{changed} line{'s' if changed != 1 else ''} changed"


#: How many lines of typing a transcript shows before it stops.  A
#: pasted template is thirty lines nobody needs to read back.
SHOWN = 12


def _shown(before, after) -> tuple:
    """The typing, to read — `-` what went and `+` what came.

    This is the half Henri had to write by hand: a transcript that
    recorded `audition` and not the line he had just changed was a
    reproduction you had to annotate before anybody could use it.
    """
    out = []
    for tag, i1, i2, j1, j2 in _blocks(before, after):
        if tag == "equal":
            continue
        for n, line in enumerate(before[i1:i2], start=i1 + 1):
            out.append(f"-{n:>4} {line}")
        for n, line in enumerate(after[j1:j2], start=j1 + 1):
            out.append(f"+{n:>4} {line}")
    if len(out) > SHOWN:
        out = out[:SHOWN] + [f"… and {len(out) - SHOWN} more"]
    return tuple(out)


class Bare(str):
    """A word that is written **unquoted**, because it is not text.

    `set "cutoff" 70` quotes its first argument and is right to: a
    parameter is a `Named a`, and `command.ges` carries a name as
    `Text`.  But an `ask` step names a *command* and a *type* — `open`
    is `open : Path -> Command` and `Path` is a type — and gestate
    writes neither in quotes.  Spelled `ask "open" 0 "Path" "drums"` the
    line parses, replays, and quietly says the wrong thing about the
    language it is written in; spelled `ask open 0 Path "drums"` every
    token means in the transcript what it means in `command.ges`.

    A `str` at every other moment, so nothing downstream has to know:
    `read` hands back plain strings and the comparisons still hold.
    """


def _literal(value) -> str:
    """One argument, as it would be typed.

    Text is quoted and numbers are not, which is the only distinction
    the reader back out has to make — and it makes it the same way,
    below.  `Bare` is the third case and costs the reader nothing: an
    unquoted word already reads back as itself.
    """
    if isinstance(value, Bare):
        return str(value)
    if isinstance(value, bool):
        return "1" if value else "0"
    if isinstance(value, (int, float)):
        return repr(value)
    text = str(value)
    # Newlines are escaped because a transcript is a file of lines: one
    # inside an argument would end the step half way through it.
    return ('"' + text.replace("\\", "\\\\").replace('"', '\\"')
            .replace("\n", "\\n") + '"')


def _value(word: str):
    """And back — a quoted word is text, a bare one is a number if it
    looks like one and a name otherwise."""
    if word.startswith('"'):
        return (word[1:-1].replace("\\n", "\n").replace('\\"', '"')
                .replace("\\\\", "\\"))
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


def began(text: str) -> str:
    """The fingerprint of the text it began on, or `""` for a
    transcript from before the header carried one."""
    for line in text.splitlines():
        body = line.strip()
        if body.startswith("#: began "):
            return body[len("#: began "):].strip()
        if body and not body.startswith("#"):
            break
    return ""


def carried(text: str) -> tuple | None:
    """The base text a transcript carries, or `None` when it carries
    none — the file was on disk, and the disk is the better copy.

    `#.` rather than `#. ` on the empty line, because editors strip
    trailing whitespace and a base text must survive being opened.
    """
    lines, seen = [], False
    for line in text.splitlines():
        if line.startswith("#."):
            seen = True
            lines.append(line[3:] if line.startswith("#. ") else "")
        elif line.strip() and not line.strip().startswith("#"):
            break
    return tuple(lines) if seen else None


def replay(session, steps, typing=None) -> list:
    """Run them, and give back what changed.

    `(step, what it said this time)` for every step whose answer moved.
    **An empty list is the whole point**: a session that replays to the
    same sentences is one this build still behaves the way it did when
    somebody was sitting in front of it.

    `typing` is a buffer the `edit` steps write into — a view that holds
    text, so the commands after one see what was typed.  Without it the
    typing is read and not done, which would make a transcript describe a
    reproduction it could not perform.
    """
    drifted = []
    for step in steps:
        if step.verb == NOTE:
            # The model's own weather, recorded for the reader; a replay
            # that demanded it would drift on every thread schedule.
            continue
        if step.verb == EDIT:
            if typing is not None:
                typing.retype(_apply(tuple(typing.lines()), step.args))
            continue
        if step.verb == ASK:
            now = _reask(session, step)
            if step.said and now != step.said:
                drifted.append((step, now))
            continue
        if step.verb == "touched":
            # A canvas write, by name — replayed against the reference
            # machine exactly the way the live editor keeps it in step.
            # Not a command, so not through `run`: the window walked
            # for the person; the recorded meaning walks for nobody.
            doing = getattr(session, "touched", None)
            if doing is not None and len(step.args) >= 2:
                doing(step.args[0], step.args[1])
            continue
        now = session.run(step.verb, *step.args)
        if step.said and now != step.said:
            drifted.append((step, now))
    return drifted


def _reask(session, step) -> str:
    """Ask the recorded question again and describe what comes back.

    **The question is put back, not the answer.**  A transcript keeps a
    digest, so the only way to compare is to make the editor work the
    listing out a second time — which is the same shape as replaying a
    command and reading its sentence, and is why a question could be
    recorded as a step at all.

    **The question is left standing**, because that is the live state:
    the palette holds its question until the list closes, and the
    command recorded after an ask ran *against* that question — its
    path resolved under the walk the ask had reached (F123 is the
    receipt: this used to restore `asking = None`, so a replayed `open`
    resolved from a different directory than the session it was
    reproducing).  A later ask overwrites; a command of another verb
    ignores a question that is not its own (`_where`'s verb guard).
    """
    verb, at = step.args[0], step.args[1]
    query = step.args[3] if len(step.args) > 3 else ""
    try:
        session.asking = (str(verb), int(at), str(query))
        return answer(session.choices())
    except Exception as exc:                             # noqa: BLE001
        # A question this build no longer understands is one step lost,
        # not a refused transcript — `read` keeps that rule and so does
        # this, for the same reason: what must not happen is losing the
        # reproduction.
        return f"could not ask: {exc}"


class Typing:
    """A view that is only a text buffer — what a replay types into.

    **Not a stand-in for the window.**  It answers the one thing the
    commands need to see change between steps, and refuses everything
    else the way `Detached` does, so a replayed command that wanted a
    window says so instead of being quietly satisfied.
    """

    def __init__(self, text: str = "", under=None):
        self._lines = tuple(text.splitlines())
        self._under = under

    def lines(self) -> list:
        return list(self._lines)

    def retype(self, lines) -> None:
        self._lines = tuple(lines)

    def text(self) -> str:
        return "\n".join(self._lines) + ("\n" if self._lines else "")

    def show(self, what: str) -> bool:
        """The one window question a replay answers as a window would.

        `canvas` gives three answers — about the file, about the clock,
        about the window — and only the first two are the program's to
        keep.  A replay has no window, so refusing here made every
        recorded `canvas` drift to *"this window shows the source
        only"*: a harness artifact wearing a report, and it wore one on
        the day a real canvas defect was being hunted (untitled.ges,
        2026-08-12).  Saying yes keeps the comparison on the answers the
        program owns.
        """
        if what not in ("canvas", "source"):
            return False
        self.showing = what
        return True

    def __getattr__(self, name):
        return getattr(self._under, name)


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
    base = carried(text)
    if not Path(against).exists() and base is None:
        print(f"{against}: not here, so there is nothing to replay "
              f"against (--against names another copy)", file=sys.stderr)
        return 1

    # No `start()`: the commands answer from the model, and a replay
    # that opened a sound card would be a replay you cannot run twice.
    bench = Workbench(Path(against), rate=args.rate, block=256)
    # The text as it was when the recording began, so the first `edit`
    # types onto the same thing the recording did.  The carried base
    # wins when there is one — the file it names was never written, or
    # has been written *since*, and either way the recording began on
    # the carried text and its edits diff from exactly that.
    if base is not None:
        start = "\n".join(base) + ("\n" if base else "")
        if not Path(against).exists():
            print(f"{against} is not here; replaying from the text "
                  f"the transcript carried")
    else:
        start = Path(against).read_text()
        opened = began(text)
        if opened and fingerprint(tuple(start.splitlines())) != opened:
            # A warning and not a refusal: the person holding an old
            # copy may know exactly what moved — but a drift report
            # against a moved file is noise wearing a report, and it
            # must say which it is.
            print(f"note: {against} is not the text the recording "
                  f"began on — the file has moved; --against can name "
                  f"a copy as it was")
    typing = Typing(start, under=Detached())
    drifted = replay(Session(bench=bench, view=typing), steps, typing)
    print(f"{len(steps)} steps replayed against {against}")

    # **Two reports, because they are two different pieces of news.**  A
    # `Path` question re-asked on a machine whose directory has gained a
    # file *must* drift, and printing that beside a real one teaches the
    # reader to skim both.  The exit code follows the same split: a
    # replay whose only movement is the world's is a replay that agreed.
    def _say(pairs):
        for step, now in pairs:
            print(f"  {step.verb} {' '.join(map(str, step.args))}\n"
                  f"      was: {step.said}\n      now: {now}")

    moved = [p for p in drifted if not world_dependent(p[0])]
    outside = [p for p in drifted if world_dependent(p[0])]
    if moved:
        _say(moved)
    if outside:
        print(f"and {len(outside)} question(s) about the world outside "
              f"the program, which the world is allowed to have moved:")
        _say(outside)
    if not drifted:
        print("every answer is the one it gave before")
    elif not moved:
        print("every answer the program owns is the one it gave before")
    return 1 if moved else 0


if __name__ == "__main__":
    raise SystemExit(main())
