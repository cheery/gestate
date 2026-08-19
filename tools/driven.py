"""Driving the real window, and leaving behind something checkable.

    from driven import Run, a_copy_of, tap, chord, find_window

    with Run("caret-after-switch") as run:
        win = find_window()
        tap("a")
        run.shot(win, "after-a")
        run.observe("does the caret follow the letter?", "yes")

**Why this file exists, and why it is not `lagcheck.py`.**  Driving a
real window is the best instrument this project has — on 2026-08-18 it
found about thirteen defects and the suite found none of them.  The
problem is that a driven run was **unlabelled**, which is worse than a
weak instrument, because an unlabelled one comes back confidently green.
`card:driven-runs.md` names three failures in one morning: a stale
library read as two defects in new code, screenshots outliving the run
that made them, and six runs asking one question each.

`lagcheck.py` held the whole driven vocabulary while being named for one
latency scenario, which was a small lie in a filename.  The vocabulary
moved here and `lagcheck` imports it, the same split the card offered
and the honest half of it.

**Refuse rather than warn.**  `fixme.md` F113's rule is that a warning
beats a gate when a person is at the keyboard and knows what they are
doing — and nobody is at the keyboard during a driven run.  The reader
of the result is a session an hour later, and that reader never sees a
warning printed at the start.  So the checks below stop the run.

**The X handles are opened lazily**, unlike in the file this came from,
so that everything that does not touch the screen — the library check,
the stamp, the report — can be exercised without a display.  A harness
whose bookkeeping cannot be tested is the same shape of problem as the
runs it is here to label.
"""

from __future__ import annotations

import ctypes
import hashlib
import os
import shutil
import subprocess
import sys
import tempfile
import time
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
#: Every run gets a directory under here, named for itself, never reused.
RUNS = ROOT / "test" / "driven"

# ── the library the editor actually loads ────────────────────────────────
#
# **This is the failure that cost four wrong readings**, and it is not
# the one the card predicted.  `gestate/editor.py::_stale` already
# rebuilds when the crate has moved, so a stale load heals itself.  What
# does not heal is that there are **two** places a `libgestate_editor.so`
# can be:
#
#     shell/editor/target/release/   ← what the editor loads
#     target/release/                ← what `cargo build` from the root writes
#
# The editor builds with `--target-dir shell/editor/target`; a person
# running `cargo build -p gestate-editor --features capi` from the
# workspace root gets a successful build of the *other* file.  Measured
# 2026-08-19: both existed, with different md5s, five days apart.  Cargo
# says nothing, the editor says nothing, and the driven run photographs
# code that was never in the process.
LOADED = ROOT / "shell" / "editor" / "target" / "release" / "libgestate_editor.so"


def _rel(path: Path) -> Path:
    """`path` under the tree, or the path itself.

    **A run that finished must not lose its report to a formatting
    error.**  `RUNS` and `LOADED` are module-level and a caller may point
    them elsewhere; `Path.relative_to` raises rather than declining, and
    it is called *after* the scenario has cost two minutes of wall time
    and a share of the machine somebody is listening on.  Losing the
    stamp at that point is precisely the failure this file exists to
    end.
    """
    try:
        return path.relative_to(ROOT)
    except ValueError:
        return path


def _digest(path: Path) -> str:
    return hashlib.md5(path.read_bytes()).hexdigest()[:12]


def library() -> dict:
    """What is actually loaded, said out loud so a run can be checked."""
    if not LOADED.exists():
        return {"path": LOADED, "exists": False}
    sys.path.insert(0, str(ROOT))
    from gestate import editor                       # noqa: E402
    return {
        "path": LOADED,
        "exists": True,
        "mtime": datetime.fromtimestamp(LOADED.stat().st_mtime),
        "md5": _digest(LOADED),
        "stale": editor._stale(LOADED, ROOT / "shell" / "editor"),
    }


def strays() -> list[dict]:
    """Other copies of the library that the editor will never load.

    Only ever a warning's worth of information on its own — it becomes a
    refusal in `Run` when one of them is **newer** than the loaded one,
    because that is the exact moment somebody has just built the wrong
    file and is about to believe a photograph of the old one.
    """
    out = []
    here = _digest(LOADED) if LOADED.exists() else None
    for p in ROOT.rglob("libgestate_editor.so"):
        if p.resolve() == LOADED.resolve():
            continue
        # **Same bytes cannot mislead.**  Cargo hardlinks the artifact
        # into `deps/`, so half of what this used to list was the loaded
        # library under a second name — noise that would have taught a
        # reader to skim the row that matters.
        if here is not None and _digest(p) == here:
            continue
        out.append({"path": _rel(p),
                    "mtime": datetime.fromtimestamp(p.stat().st_mtime),
                    "md5": _digest(p)})
    return sorted(out, key=lambda d: d["mtime"], reverse=True)


#: What a driven run shells out to, and what it is for.  **Named here
#: because the failure of a missing one is silent and wears the costume
#: of a defect** — F170.  `find_window` runs `xdotool search` with
#: `capture_output=True`, so on a machine without it the search finds
#: nothing, waits out its thirty seconds of patience and returns `None`,
#: which every caller reads as *the window never appeared*.  That is a
#: sentence about the editor, produced by a missing package, and it was
#: true on this machine on 2026-08-19: `xdotool` appeared nowhere in the
#: tree except the two lines that call it, including not in
#: `doc/install.md`.
BINARIES = {
    "xdotool": "find the window and read its geometry (apt: xdotool)",
    "import": "photograph a window (apt: imagemagick)",
    "compare": "say whether two shots differ (apt: imagemagick)",
}


def missing_binaries() -> dict[str, str]:
    return {b: why for b, why in BINARIES.items() if shutil.which(b) is None}


class Refused(RuntimeError):
    """The run did not happen, and why — never a run that half-happened."""


# ── the run ──────────────────────────────────────────────────────────────


class Run:
    """One driven run: its own directory, its stamp, and its questions.

    **A run owns a fresh directory.**  Shots, traces and the report land
    in it and nothing is ever written to a path a previous run used, so
    a stale image cannot be picked up by the next reader — which is
    failure 2 in `card:driven-runs.md`, and the next reader was me.

    **Scenarios take a list of observations, not one.**  Each driven
    scenario costs about two minutes of wall time and costs the machine
    Henri is *listening on* (`board/README.md` §"And the machine is
    shared").  Asking one question per run made adding a second
    assertion feel like risk when it is a line; `observe()` is that
    line, and the report counts them.
    """

    def __init__(self, name: str, why: str = "", **env):
        self.name = name
        self.why = why
        self.extra_env = env
        self.started = datetime.now()
        self.dir = RUNS / f"{self.started:%Y%m%d-%H%M%S}-{name}"
        self.shots: list[tuple[str, Path]] = []
        self.notes: list[str] = []
        self.observations: list[tuple[str, str]] = []
        self.library = library()
        self.strays = strays()

    # -- refusing -------------------------------------------------------
    def _refuse_if_the_run_cannot_happen(self):
        gone = missing_binaries()
        if gone:
            raise Refused(
                "a driven run needs these and this machine has none of "
                "them:\n    "
                + "\n    ".join(f"{b} — {why}" for b, why in gone.items())
                + "\n  without them the search finds no window, waits out "
                  "its patience and returns None,\n  which reads as *the "
                  "editor never opened a window* and is not.")
        if not os.environ.get("DISPLAY"):
            raise Refused("no DISPLAY — a driven run needs a real or "
                          "virtual X server (`Xvfb :99` and DISPLAY=:99 "
                          "will do).")

    def _refuse_if_the_result_would_not_be_about_this_code(self):
        lib = self.library
        if not lib["exists"]:
            raise Refused(
                f"no library at {_rel(LOADED)} — the editor has "
                "never been built here.\n  start it once "
                "(`tools/gestate-editor`) and it builds itself.")
        if lib["stale"]:
            raise Refused(
                "the crate has moved since the library was built, so this "
                "run would photograph old code.\n  start the editor once — "
                "it rebuilds itself — then run again.")
        newer = [s for s in self.strays if s["mtime"] > lib["mtime"]]
        if newer:
            lines = "\n    ".join(
                f"{s['path']}  {s['mtime']:%Y-%m-%d %H:%M}  {s['md5']}"
                for s in newer)
            raise Refused(
                "a *different* copy of libgestate_editor.so is newer than "
                "the one the editor loads:\n    "
                f"{lines}\n  loaded: {_rel(LOADED)}  "
                f"{lib['mtime']:%Y-%m-%d %H:%M}  {lib['md5']}\n"
                "  `cargo build` from the workspace root writes the first "
                "one and the editor never reads it.\n"
                "  build the one that is loaded:  cargo build --release "
                "--features capi \\\n"
                "      --manifest-path shell/editor/Cargo.toml "
                "--target-dir shell/editor/target")

    # -- the run --------------------------------------------------------
    def __enter__(self):
        self._refuse_if_the_run_cannot_happen()
        self._refuse_if_the_result_would_not_be_about_this_code()
        self.dir.mkdir(parents=True, exist_ok=False)
        return self

    def env(self, **extra) -> dict:
        """The environment for the child, with the run's own on top."""
        return driven(**{**self.extra_env, **extra})

    def shot(self, win: int, label: str) -> Path:
        path = self.dir / f"{len(self.shots):02d}-{label}.png"
        shot(win, str(path))
        self.shots.append((label, path))
        return path

    def note(self, line: str) -> None:
        """A machine-readable trace line, which beats a photograph.

        The finding that cracked the gemba walk was
        `[walk] ended by the caret: 2 != 132` — a print statement, not a
        screenshot.  A shot proves what a person sees; a trace says why.
        """
        self.notes.append(line)

    def observe(self, question: str, answer: str) -> None:
        self.observations.append((question, answer))

    def __exit__(self, exc_type, exc, tb):
        self.write_report(failure=None if exc is None else repr(exc))
        return False

    # -- the stamp ------------------------------------------------------
    def write_report(self, failure: str | None = None) -> Path:
        """The stamp, beside the shots.

        **When a screenshot is quoted in a commit body or a card, this
        is what makes the quote checkable** — which is the card's
        postcondition: *a claim about what the window did can be checked
        by somebody who was not there, from what the run left behind.*
        """
        lib = self.library
        git = lambda *a: subprocess.run(["git", *a], cwd=ROOT, text=True,
                                        capture_output=True).stdout.strip()
        dirty = [l for l in git("status", "--porcelain").splitlines() if l.strip()]
        seen = {k: v for k, v in sorted(os.environ.items())
                if k.startswith("GESTATE_")}
        seen.update({k: str(v) for k, v in self.extra_env.items()})
        body = [
            f"# {self.name} — a driven run",
            "",
            f"*{self.why}*" if self.why else "",
            "",
            "| | |",
            "|---|---|",
            f"| Ran | {self.started:%Y-%m-%d %H:%M:%S} |",
            f"| Commit | `{git('log', '-1', '--format=%h %s') or '(none)'}` |",
            f"| Tree | {'clean' if not dirty else f'{len(dirty)} file(s) modified or untracked'} |",
            f"| Library | `{_rel(LOADED)}` |",
            f"| Built | {lib.get('mtime', '—')} |",
            f"| md5 | `{lib.get('md5', '—')}` |",
            f"| Other copies | {len(self.strays)}{' — none newer' if self.strays else ''} |",
            f"| Environment | {', '.join(f'{k}={v!r}' for k, v in seen.items()) or 'nothing GESTATE_* set'} |",
            f"| Wall | {int((datetime.now() - self.started).total_seconds())}s |",
            "",
        ]
        if failure:
            body += ["**The scenario raised**: `" + failure + "`", ""]
        body += [f"## {len(self.observations)} observation(s)", ""]
        body += [f"* **{q}** — {a}" for q, a in self.observations] or ["*None recorded.*"]
        body += ["", f"## {len(self.notes)} trace line(s)", ""]
        body += ["```", *self.notes, "```"] if self.notes else ["*None.*"]
        body += ["", f"## {len(self.shots)} shot(s)", ""]
        body += [f"* `{p.name}` — {label}" for label, p in self.shots] or ["*None.*"]
        body += [""]
        page = self.dir / "report.md"
        page.write_text("\n".join(body) + "\n")
        print(f"driven: {_rel(self.dir)}")
        return page


# ── the X vocabulary, moved here from lagcheck.py ────────────────────────
#
# Opened on first use rather than at import, so the bookkeeping above is
# importable on a machine with no display — including inside the fence,
# where `test_editor_abi.py` records that there is no X11 socket at all.

_X = None


def _x():
    global _X
    if _X is None:
        X = ctypes.CDLL("libX11.so.6")
        XTEST = ctypes.CDLL("libXtst.so.6")
        X.XOpenDisplay.restype = ctypes.c_void_p
        X.XOpenDisplay.argtypes = [ctypes.c_char_p]
        X.XStringToKeysym.restype = ctypes.c_ulong
        X.XStringToKeysym.argtypes = [ctypes.c_char_p]
        X.XKeysymToKeycode.restype = ctypes.c_ubyte
        X.XKeysymToKeycode.argtypes = [ctypes.c_void_p, ctypes.c_ulong]
        X.XFlush.argtypes = [ctypes.c_void_p]
        XTEST.XTestFakeKeyEvent.argtypes = [ctypes.c_void_p, ctypes.c_uint,
                                            ctypes.c_int, ctypes.c_ulong]
        XTEST.XTestFakeMotionEvent.argtypes = ([ctypes.c_void_p]
                                               + [ctypes.c_int] * 3
                                               + [ctypes.c_ulong])
        XTEST.XTestFakeButtonEvent.argtypes = [ctypes.c_void_p, ctypes.c_uint,
                                               ctypes.c_int, ctypes.c_ulong]
        _X = (X, XTEST, X.XOpenDisplay(None))
    return _X


def _code(name: str) -> int:
    X, _XTEST, dpy = _x()
    return X.XKeysymToKeycode(dpy, X.XStringToKeysym(name.encode()))


def tap(name: str) -> None:
    _X_, XTEST, dpy = _x()
    code = _code(name)
    XTEST.XTestFakeKeyEvent(dpy, code, 1, 0)
    XTEST.XTestFakeKeyEvent(dpy, code, 0, 0)
    _X_.XFlush(dpy)
    time.sleep(0.05)


def chord(modifier: str, name: str) -> None:
    X, XTEST, dpy = _x()
    mod, code = _code(modifier), _code(name)
    XTEST.XTestFakeKeyEvent(dpy, mod, 1, 0)
    XTEST.XTestFakeKeyEvent(dpy, code, 1, 0)
    XTEST.XTestFakeKeyEvent(dpy, code, 0, 0)
    XTEST.XTestFakeKeyEvent(dpy, mod, 0, 0)
    X.XFlush(dpy)
    time.sleep(0.15)


def find_window(title: str = "gestate", patience: float = 30.0):
    """The window id, once the window exists.  `None` if it never does."""
    until = time.time() + patience
    while time.time() < until:
        out = subprocess.run(["xdotool", "search", "--name", title],
                             capture_output=True, text=True)
        ids = [l for l in out.stdout.split() if l.strip()]
        if ids:
            return int(ids[-1])
        time.sleep(0.5)
    return None


def move(x: int, y: int) -> None:
    """The pointer, in root coordinates.

    Here rather than in each harness: `dragcheck.py` and
    `measure_editor.py` each carried their own `ctypes.CDLL` block and
    their own `XOpenDisplay`, which is three copies of the same six
    lines and three chances for one of them to open a second connection
    to the display the editor is drawing on.  Same argument `driven()`
    makes about itself — one funnel, so a sixth tool cannot forget.
    """
    X, XTEST, dpy = _x()
    XTEST.XTestFakeMotionEvent(dpy, -1, x, y, 0)
    X.XFlush(dpy)


def press(down: bool, button: int = 1) -> None:
    X, XTEST, dpy = _x()
    XTEST.XTestFakeButtonEvent(dpy, button, 1 if down else 0, 0)
    X.XFlush(dpy)


def click_into(win: int, dx: int = 300, dy: int = 60) -> None:
    X, XTEST, dpy = _x()
    geom = subprocess.run(["xdotool", "getwindowgeometry", "--shell", str(win)],
                          capture_output=True, text=True).stdout
    pos = dict(l.split("=", 1) for l in geom.splitlines() if "=" in l)
    XTEST.XTestFakeMotionEvent(dpy, -1, int(pos.get("X", 0)) + dx,
                               int(pos.get("Y", 0)) + dy, 0)
    X.XFlush(dpy)
    time.sleep(0.3)
    XTEST.XTestFakeButtonEvent(dpy, 1, 1, 0)
    XTEST.XTestFakeButtonEvent(dpy, 1, 0, 0)
    X.XFlush(dpy)
    time.sleep(1.0)


def driven(**extra) -> dict:
    """The environment a *driven* workbench runs in.

    **XTEST types with the same X events a hand does**, and
    `gestate.presence` cannot tell them apart — nothing can, which is
    the point of XTEST.  So a harness left running for an hour would put
    an hour into somebody's week and the one instrument that measures
    the person would be measuring the test suite.  `GESTATE_PRESENCE=`
    (empty) turns the record off for the child.

    Every tool here that opens a window goes through this, so a fifth
    one cannot forget.
    """
    return dict(os.environ, GESTATE_PRESENCE="", **extra)


def a_copy_of(path=None) -> str:
    """The file a driven window opens — **a copy, never the original.**

    **A harness that types is a harness that can save.**  XTEST sends
    the events a hand sends, so `Ctrl-S` in a scenario means what it
    means under a finger: the file on disk is rewritten.  Every tool
    here names a *committed example*, so one scenario reaching for that
    chord would edit the repository — and a harness that names no file
    at all opens `untitled.ges` in the working directory and leaves it
    there, which is how this was learned (2026-08-17: a driven
    reproduction saved a deliberately broken starter into the tree, and
    the *next* run opened it and measured the wrong thing).

    A fence does not help: the write is inside the project and is the
    program working correctly.  What helps is that the file handed over
    was never the one you care about.  Same basename, so anything that
    reads the name — a status bar, a complaint's `(at file:line)` —
    still reads the right one; `None` yields a path that does not
    exist, which is what a bare launch opens on and where its first
    save now lands.

    Goes with `driven` for the same reason it is written here: one
    funnel, so a sixth tool cannot forget.
    """
    where = tempfile.mkdtemp(prefix="gestate-driven-")
    if path is None:
        return os.path.join(where, "untitled.ges")
    copy = os.path.join(where, os.path.basename(path))
    shutil.copyfile(path, copy)
    return copy


def shot(win: int, path: str) -> None:
    subprocess.run(["import", "-window", str(win), path], capture_output=True)


def differs(a: str, b: str) -> bool:
    """Whether two screenshots show anything different at all."""
    out = subprocess.run(["compare", "-metric", "AE", a, b, "null:"],
                         capture_output=True, text=True)
    return (out.stderr.strip().split()[0] if out.stderr.strip() else "0") != "0"


def main(argv=None) -> int:
    """`python tools/driven.py` — say what a run would be about."""
    for b, why in missing_binaries().items():
        print(f"MISSING   {b} — {why}")
    lib = library()
    print(f"library   {_rel(LOADED)}")
    if not lib["exists"]:
        print("          not built — start the editor once"); return 1
    print(f"built     {lib['mtime']:%Y-%m-%d %H:%M}   md5 {lib['md5']}"
          f"   {'STALE' if lib['stale'] else 'fresh'}")
    for s in strays():
        flag = "NEWER — a run would be refused" if s["mtime"] > lib["mtime"] else "older"
        print(f"other     {s['path']}  {s['mtime']:%Y-%m-%d %H:%M}  "
              f"md5 {s['md5']}  ({flag})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
