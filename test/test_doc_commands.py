"""The commands the documentation tells you to type — do they still work?

`test_manual.py` runs every gestate *snippet* in the manual and
`test_courses.py` builds every course *example*, so the language in the
prose cannot drift.  The **shell lines around them** had no such check,
and they drifted: the day `audiopygame` was retired, seven references to
it stayed in `doc/`, three of them the second command of a lesson.  Two
more CLIs were retired into a message and the guides went on teaching
them.  A reader following the intermediate course got
`No module named gestate.audiopygame` before they got a sound.

So a documented command is checked the way a documented snippet is: it
must **name a module that exists, and that module must have a command
line**.  The second half is the one that catches a retirement — a
retired CLI is still importable and still fails, so existence alone
would have passed `gestate.audio` while it printed "the CLI is retired"
at every reader of `doc/super.md`.

`--help` is the probe because it is the only flag every CLI here shares
and the only one that runs nothing: argparse answers it and exits 0
before a file is opened or a sound card is asked for.  A module whose
`main` returns instead of exiting is refusing, which is what the retired
ones do, and refusing is the failure being looked for.

What this deliberately does *not* do is run the commands for real.  That
is minutes of rendering to re-test what `test_courses.py` already builds
in seconds; the question here is narrower and was the one going
unasked — **is the reader being sent somewhere that is there?**
"""

from __future__ import annotations

import contextlib
import importlib
import importlib.util
import io
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent

#: Every file that tells somebody what to type.
#:
#: **`spec/` is in here, and was not.**  The specs are where a stage
#: announces itself — "**Built**", then the line you type — and being
#: read by their author rather than by a beginner is exactly why nobody
#: notices when the line stops working.  `spec/liveaudio.md` went on
#: offering `gestate.audioeditor` for two commits after the door became
#: `gestate.workbench`, and `spec/substrate.md` still taught
#: `gestate.audiopygame` after that module was deleted outright.  The
#: retirement note a spec keeps *around* a dead command is prose and is
#: welcome; the command in it has to be one that runs.
DOCS = (sorted(ROOT.glob("doc/*.md"))
        + sorted(ROOT.glob("spec/*.md"))
        + [ROOT / "README.md", ROOT / "examples" / "README.md"])

#: `python -m gestate.NAME`, and the rest of the line for its arguments.
_INVOCATION = re.compile(r"python -m (gestate\.[A-Za-z_][A-Za-z0-9_]*)(.*)")


class Command:
    """One documented invocation, and where it was found."""

    def __init__(self, module: str, rest: str, path: Path, line: int):
        self.module = module
        self.rest = rest
        self.path = path
        self.line = line

    @property
    def where(self) -> str:
        return f"{self.path.relative_to(ROOT)}:{self.line}"

    @property
    def flags(self) -> list:
        """The long options on the line — `--foo`, never `-o`.

        Short options are left alone deliberately: `-o` is a word in
        prose as often as it is a flag, and the long form is what the
        guides write anyway.
        """
        return [word.strip("`'\"),.;").split("=")[0]
                for word in self.rest.split()
                if word.startswith("--") and len(word.rstrip("`'\"),.;")) > 2]

    def __str__(self) -> str:
        return f"`python -m {self.module}` ({self.where})"


def _commands() -> list:
    found = []
    for path in DOCS:
        if not path.exists():
            continue
        for n, text in enumerate(path.read_text().splitlines(), 1):
            for match in _INVOCATION.finditer(text):
                found.append(Command(match.group(1), match.group(2), path, n))
    return found


COMMANDS = _commands()


def _first_of_each() -> list:
    """One case per module, at the first place it is documented.

    The same command is taught in several files, and a case per site
    would be one defect wearing five costumes.  Where it is *also*
    taught is in the failure message instead.
    """
    seen, out = set(), []
    for command in COMMANDS:
        if command.module not in seen:
            seen.add(command.module)
            out.append(command)
    return out


def _sites(module: str) -> str:
    return ", ".join(c.where for c in COMMANDS if c.module == module)


#: `--help` text per module, filled on first ask.
_HELP: dict = {}


def _help_of(module_name: str) -> str | None:
    """What the module's own parser says it takes, or `None` if it says nothing.

    Read once per module and kept, because several guides teach the same
    command and building an argument parser twelve times to ask it the
    same question is waste with no reader.
    """
    if module_name in _HELP:
        return _HELP[module_name]
    module = importlib.import_module(module_name)
    main = getattr(module, "main", None)
    text = None
    if main is not None:
        stream = io.StringIO()
        try:
            with contextlib.redirect_stdout(stream):
                main(["--help"])
        except SystemExit:
            text = stream.getvalue() or None
        except Exception:                                    # noqa: BLE001
            text = None
    _HELP[module_name] = text
    return text


def test_the_docs_do_tell_you_to_type_something():
    """The scan works — a silent regex is a green test that checks nothing."""
    assert len(COMMANDS) > 20, "no documented commands found; the regex moved"
    assert any(c.module == "gestate.audioperform" for c in COMMANDS)


@pytest.mark.parametrize("command", _first_of_each(), ids=lambda c: c.module)
def test_a_documented_command_exists(command):
    """The module the docs name is a module that is here."""
    assert importlib.util.find_spec(command.module) is not None, (
        f"{command} names a module that does not exist.\n"
        f"Taught at: {_sites(command.module)}")


@pytest.mark.parametrize("command", _first_of_each(), ids=lambda c: c.module)
def test_a_documented_command_has_a_command_line(command):
    """It answers `--help` — so it has a CLI, and the CLI is not retired.

    A retired CLI prints where to go instead and *returns*; a live one
    lets argparse exit.  A module with no `main` at all runs silently and
    does nothing, which is the worst of the three and reads as a hang.
    """
    if importlib.util.find_spec(command.module) is None:
        pytest.skip("reported by the existence test")
    module = importlib.import_module(command.module)
    main = getattr(module, "main", None)
    assert main is not None, (
        f"{command} has no `main`: `python -m {command.module}` runs "
        f"nothing and says nothing.\nTaught at: {_sites(command.module)}")
    try:
        code = main(["--help"])
    except SystemExit as exit:                  # argparse answered — a CLI.
        code = exit.code
    else:                                       # it returned: it refused.
        pytest.fail(
            f"{command} returned {code} from `--help` instead of printing "
            f"one — a retired CLI that the docs still send readers to.\n"
            f"Taught at: {_sites(command.module)}")
    assert code in (0, None), (
        f"{command} exited `--help` with {code}.\n"
        f"Taught at: {_sites(command.module)}")


@pytest.mark.parametrize(
    "command", [c for c in COMMANDS if c.flags],
    ids=lambda c: f"{c.path.name}:{c.line}")
def test_a_flag_a_command_passes_is_a_flag_it_has(command):
    """Every `--flag` on a documented line is one the CLI accepts.

    The module surviving a retirement is not enough — a flag can be
    retired on its own, and `--watch` was: it was `audiolive`'s
    live-reload, it moved into the editor with the rest of the live room,
    and four guides went on teaching it as *the* way to work through
    them.  Nothing failed, because nothing ran a command line.

    The parser's own `--help` is the list, which is why this is read out
    of the CLI rather than kept beside it.  A flag with no `--help` to
    check against is skipped rather than guessed at.
    """
    if importlib.util.find_spec(command.module) is None:
        pytest.skip("reported by the existence test")
    help_text = _help_of(command.module)
    if help_text is None:
        pytest.skip("no --help to read the flags out of")
    for flag in command.flags:
        assert flag in help_text, (
            f"{command.where} passes `{flag}`, which "
            f"`python -m {command.module} --help` does not list")


@pytest.mark.parametrize(
    "command", [c for c in COMMANDS if "examples/" in c.rest],
    ids=lambda c: f"{c.path.name}:{c.line}")
def test_a_file_a_command_names_is_there(command):
    """`examples/…` on a documented command line is a real file.

    Placeholders (`f.ges`, `<file>`, `song.ges`) are not checked — they
    are not paths and were never meant to resolve.  A path under
    `examples/` is, because `examples/README.md` promises that an example
    which stops working is a failing test rather than a stale file.

    The markdown around a command is stripped off the word first: a line
    that ends in a backtick would otherwise report a missing file whose
    only fault is being quoted.
    """
    for word in command.rest.split():
        word = word.strip("`'\"),.;")
        if word.startswith("examples/"):
            assert (ROOT / word).exists(), (
                f"{command.where} names `{word}`, which is not in the tree")
