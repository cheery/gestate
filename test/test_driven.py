"""`tools/driven.py` — the harness that has to say what it ran.

**Driving the real window is this project's best instrument and its
least labelled one.**  On 2026-08-18 it found about thirteen defects and
the suite found none of them; the same morning it produced three wrong
readings, because a driven run left behind photographs and nothing that
said which binary made them (`card:driven-runs.md`).

None of what is checked here needs a display, which is deliberate: the
bookkeeping is the part that was missing, and a harness whose
bookkeeping cannot be tested is the same shape of problem as the runs it
labels.  The X vocabulary is not tested here and cannot be — that is
what `test_editor_abi.py` and the driven tools themselves are for.
"""

from __future__ import annotations

import importlib.util
import re
from datetime import datetime, timedelta
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent

spec = importlib.util.spec_from_file_location("driven", ROOT / "tools" / "driven.py")
driven = importlib.util.module_from_spec(spec)
spec.loader.exec_module(driven)


NOW = datetime(2026, 8, 19, 16, 0)


def a_run(tmp_path, monkeypatch, *, stale=False, stray_at=None):
    """A `Run` with its facts supplied rather than measured.

    The binaries are stubbed present because these tests are about the
    bookkeeping and not about the preflight — the preflight has its own
    two tests below, and this machine really is missing `xdotool`
    (F170), which would otherwise refuse every run here for the right
    reason at the wrong time.
    """
    monkeypatch.setattr(driven.shutil, "which", lambda b: f"/usr/bin/{b}")
    monkeypatch.setenv("DISPLAY", ":0")
    monkeypatch.setattr(driven, "RUNS", tmp_path / "driven")
    run = driven.Run("scenario", why="a test")
    run.library = {"path": driven.LOADED, "exists": True, "mtime": NOW,
                   "md5": "aaaaaaaaaaaa", "stale": stale}
    run.strays = ([] if stray_at is None else
                  [{"path": Path("target/release/libgestate_editor.so"),
                    "mtime": stray_at, "md5": "bbbbbbbbbbbb"}])
    return run


def test_a_newer_stray_library_refuses_the_run(tmp_path, monkeypatch):
    """**The failure that cost four wrong readings, and it is not staleness.**

    `gestate/editor.py::_stale` already rebuilds when the crate moved,
    so a stale load heals itself.  What does not heal is that
    `cargo build -p gestate-editor --features capi` run from the
    workspace root writes `target/release/`, and the editor loads
    `shell/editor/target/release/`.  Both existed on 2026-08-19 with
    different md5s, five days apart.  Cargo says nothing; the run
    photographs code that was never in the process.
    """
    run = a_run(tmp_path, monkeypatch, stray_at=NOW + timedelta(minutes=5))
    with pytest.raises(driven.Refused) as caught:
        with run:
            pass
    said = str(caught.value)
    assert "newer" in said
    assert "target/release" in said, "it has to name the file that misled"
    assert "--manifest-path" in said, "and the command that fixes it"
    assert not (tmp_path / "driven").exists(), \
        "a refused run must leave no directory behind"


def test_an_older_stray_is_not_a_refusal(tmp_path, monkeypatch):
    """Refuse precisely.  Six older copies sit in this tree normally, and
    a harness that cried wolf about them would be turned off."""
    run = a_run(tmp_path, monkeypatch, stray_at=NOW - timedelta(days=1))
    with run:
        pass
    assert run.dir.exists()


def test_a_stale_library_refuses(tmp_path, monkeypatch):
    """Refuse, not warn — `card:driven-runs.md`'s second question.

    F113's rule is that a warning beats a gate when a person is at the
    keyboard; nobody is at the keyboard during a driven run, and the
    reader an hour later never sees a warning printed at the start.
    """
    run = a_run(tmp_path, monkeypatch, stale=True)
    with pytest.raises(driven.Refused):
        with run:
            pass


def test_each_run_owns_a_directory_and_never_reuses_one(tmp_path, monkeypatch):
    """Failure 2: a second run that dies early leaves the first run's
    image sitting there, and the next thing to read it is a session."""
    first = a_run(tmp_path, monkeypatch)
    with first:
        pass
    second = a_run(tmp_path, monkeypatch)
    second.started = first.started + timedelta(seconds=1)
    second.dir = driven.RUNS / f"{second.started:%Y%m%d-%H%M%S}-scenario"
    with second:
        pass
    assert first.dir != second.dir
    assert first.dir.exists() and second.dir.exists()


def test_the_report_stamps_what_would_make_a_quote_checkable(tmp_path, monkeypatch):
    """The card's postcondition: *a claim about what the window did can
    be checked by somebody who was not there, from what the run left
    behind.*  So the library's identity and the observations both land."""
    run = a_run(tmp_path, monkeypatch)
    with run:
        run.observe("does the caret follow?", "yes")
        run.observe("does the box scroll?", "no — F999")
        run.note("[walk] ended by the caret: 2 != 132")
    page = (run.dir / "report.md").read_text()
    assert "aaaaaaaaaaaa" in page, "the md5 of the library that ran"
    assert "2026-08-19 16:00" in page, "when it was built"
    assert "2 observation(s)" in page, "asking two questions in one run is the point"
    assert "F999" in page
    assert "ended by the caret" in page, "a trace beats a photograph"


def test_a_scenario_that_raises_still_leaves_its_stamp(tmp_path, monkeypatch):
    """A run that died is exactly the one somebody will read later."""
    run = a_run(tmp_path, monkeypatch)
    with pytest.raises(ValueError):
        with run:
            run.observe("did the window appear?", "no")
            raise ValueError("no window")
    page = (run.dir / "report.md").read_text()
    assert "ValueError" in page and "no window" in page


def test_an_identical_copy_is_not_reported_as_a_stray():
    """Cargo hardlinks the artifact into `deps/`, so half of what this
    listed at first was the loaded library under a second name — noise
    that teaches a reader to skim the row that matters."""
    if not driven.LOADED.exists():
        pytest.skip("the editor has never been built here")
    here = driven._digest(driven.LOADED)
    assert all(s["md5"] != here for s in driven.strays())


def test_a_missing_binary_refuses_before_it_can_look_like_a_defect(tmp_path, monkeypatch):
    """F170, and the reason the preflight is a refusal.

    `find_window` runs `xdotool search` with `capture_output=True`.  With
    no `xdotool` the search finds nothing, waits out thirty seconds of
    patience and returns `None` — a result every caller reads as *the
    window never appeared*.  That is a sentence about the editor
    produced by a missing package, which is this card's whole subject.
    """
    run = a_run(tmp_path, monkeypatch)          # stubs them present…
    monkeypatch.setattr(driven.shutil, "which",  # …and this takes one away
                        lambda b: None if b == "xdotool" else f"/usr/bin/{b}")
    with pytest.raises(driven.Refused) as caught:
        with run:
            pass
    said = str(caught.value)
    assert "xdotool" in said
    assert "apt" in said, "name the package, not just the binary"
    assert "returns None" in said, "say what the silent failure looks like"


def test_no_display_refuses_too(tmp_path, monkeypatch):
    run = a_run(tmp_path, monkeypatch)
    monkeypatch.delenv("DISPLAY", raising=False)
    with pytest.raises(driven.Refused, match="DISPLAY"):
        with run:
            pass


def test_this_machine_can_actually_drive_a_window_or_says_why_not():
    """**The roster, not a mock.**  Every other test here supplies the
    facts; this one asks the machine, and it is the only one that would
    have caught F170 — which sat unnoticed because nothing ever asked
    whether the tools a driven run shells out to were installed.

    It does not fail on a machine that cannot drive: `doc/install.md`'s
    posture is that a missing backend degrades politely.  It fails if
    the *reason* is unavailable, which is the actual defect.
    """
    gone = driven.missing_binaries()
    if gone:
        pytest.skip("cannot drive here: " + ", ".join(gone))
    assert True


def test_the_stamp_reports_the_environment_the_child_was_handed(tmp_path, monkeypatch):
    """Found by the first real run, which is the only way it could be.

    The stamp read `os.environ` — this process — and printed *nothing
    GESTATE_* set* while `driven()` had handed the child
    `GESTATE_PRESENCE=""`.  A stamp describing the wrong process is the
    same defect as a photograph of the wrong binary, one layer along.
    """
    monkeypatch.delenv("GESTATE_WALK_WHY", raising=False)
    run = a_run(tmp_path, monkeypatch)
    with run:
        run.env(GESTATE_WALK_WHY="1")
    page = (run.dir / "report.md").read_text()
    assert "GESTATE_PRESENCE=" in page, "driven() sets it and the stamp must say so"
    assert "GESTATE_WALK_WHY=1" in page, "and what the scenario added"


def test_a_run_that_started_no_child_says_so(tmp_path, monkeypatch):
    """Rather than reporting the parent's environment, which would be a
    neighbouring truth — the shape `dont-conclude-from-a-shallow-check`
    warns about, in a report."""
    monkeypatch.setenv("GESTATE_SO_CACHE", "0")
    run = a_run(tmp_path, monkeypatch)
    with run:
        pass
    page = (run.dir / "report.md").read_text()
    assert "no child was started" in page
    assert "GESTATE_SO_CACHE" not in page, "the parent's environment is not the run's"


def test_a_run_refuses_beside_somebody_elses_editor(tmp_path, monkeypatch):
    """**The file that is not a copy is the one already open.**

    Henri, 2026-08-19: *"How do I engage the driven-run now?  I have the
    user's version on my desktop that is not protected."*  Which found
    it: `find_window` returned `ids[-1]` — *a* gestate window — and XTEST
    does not aim at a window id at all, it sends the key to whatever has
    X focus.  `click_into` is what hands focus over.  So a run started
    beside an open editor could click into that window, open its command
    box and type into it; a scenario that presses Return would run a
    command there.  `a_copy_of` protects the file the run opens and does
    nothing at all for the file somebody was already editing.
    """
    run = a_run(tmp_path, monkeypatch)
    monkeypatch.setattr(driven, "windows", lambda title="gestate": [12345678])
    with pytest.raises(driven.Refused) as caught:
        with run:
            pass
    said = str(caught.value)
    assert "already open" in said
    assert "Xvfb" in said, "refusing has to say where to drive instead"
    assert not (tmp_path / "driven").exists()


def test_an_empty_display_is_fine(tmp_path, monkeypatch):
    """Refuse precisely: driving on :0 to *watch* is the instrument."""
    run = a_run(tmp_path, monkeypatch)
    monkeypatch.setattr(driven, "windows", lambda title="gestate": [])
    with run:
        pass
    assert run.dir.exists()


def test_find_window_skips_the_ones_that_were_already_there(monkeypatch):
    """The narrower case the refusal does not cover: a second window
    arriving mid-run.  `ids[-1]` is not the same as *ours*."""
    monkeypatch.setattr(driven, "windows", lambda title="gestate": [111, 222])
    assert driven.find_window(patience=0.1, exclude=[222]) == 111
    assert driven.find_window(patience=0.1, exclude=[111, 222]) is None


def test_every_tool_that_types_refuses_beside_an_open_editor():
    """**F171 was fixed in `Run`, and three tools that type have no `Run`.**

    `dialoglag.py`, `dragcheck.py` and `measure_editor.py` drive the
    real window with the same XTEST calls `lagcheck.py` uses, and until
    2026-08-19 the refusal lived only on the path that also kept a
    stamp — so the guard covered the tool that happened to be rewritten
    the day the defect was found, and not the shape of the hazard.
    Typing with XTEST *is* the hazard: the keystroke goes to whatever
    holds X focus, and a press aims at root coordinates.

    Checked by reading the sources rather than by driving, because
    driving is the one thing that cannot be done in a suite — and the
    hazard is at the *start* of a run, where a test that could reach it
    would already be typing into somebody's window.
    """
    types = ("tap(", "chord(", "click_into(", "press(", "_button(", "move(")
    unguarded = []
    for path in sorted((ROOT / "tools").glob("*.py")):
        if path.name == "driven.py":
            continue                        # it is the guard
        src = path.read_text()
        if "driven import" not in src and "import driven" not in src:
            continue
        if not any(call in src for call in types):
            continue
        if "refuse_if_the_run_cannot_happen" in src or "Run(" in src:
            continue
        unguarded.append(path.name)
    assert not unguarded, (
        "these drive a window with XTEST and would start beside somebody's "
        f"open editor: {', '.join(unguarded)} — F171")


def test_the_refusal_names_the_tool_that_was_refused(monkeypatch):
    """Because the sentence a person reads has to be one they can act on.

    The message ends in the line to type on the other display, and that
    line used to be `lagcheck.py`'s because `lagcheck.py` was the only
    caller.  Four tools share it now, and *"drive somewhere else: …
    lagcheck.py"* printed by `dragcheck` is an instruction to run the
    wrong scenario.
    """
    monkeypatch.setattr(driven.shutil, "which", lambda b: f"/usr/bin/{b}")
    monkeypatch.setenv("DISPLAY", ":0")
    monkeypatch.setattr(driven, "windows", lambda title="gestate": [12345678])
    with pytest.raises(driven.Refused) as caught:
        driven.refuse_if_the_run_cannot_happen("python tools/dragcheck.py")
    assert "tools/dragcheck.py" in str(caught.value)
    assert "Xvfb" in str(caught.value), "and where to drive instead"


def _facts(stale=False):
    """A library reading, supplied rather than measured — `a_run`'s
    trick, for the callers that have no `Run` to hang it on."""
    return {"path": driven.LOADED, "exists": True, "mtime": NOW,
            "md5": "aaaaaaaaaaaa", "stale": stale}


def _a_free_display(monkeypatch):
    monkeypatch.setattr(driven.shutil, "which", lambda b: f"/usr/bin/{b}")
    monkeypatch.setenv("DISPLAY", ":0")
    monkeypatch.setattr(driven, "windows", lambda title="gestate": [])


def test_a_tool_with_no_run_is_still_refused_a_stale_library(monkeypatch):
    """**Guards shared, bookkeeping not.**

    The stamp is a contract about a tool's output and belongs to
    whoever owns the tool; the library refusal is not.  A
    `measure_editor` number taken against a `libgestate_editor.so` that
    was never in the process is the 2026-08-18 failure itself — four
    wrong readings — and it is closed by the guard, not by keeping a
    directory.  So the preflight the three unstamped tools call runs
    this check too.
    """
    _a_free_display(monkeypatch)
    with pytest.raises(driven.Refused, match="old code"):
        driven.refuse_if_the_run_cannot_happen(
            "python tools/measure_editor.py <scenario> <file.ges>",
            lib=_facts(stale=True), other=[])


def test_the_preflight_refuses_for_the_callers_binaries_and_no_others(monkeypatch):
    """**Refuse precisely** — the reason `needs` is a parameter.

    `xwininfo` is F170 one binary along: `dragcheck.py` searches the
    window tree with it and `measure_editor.py` reads a corner with it,
    and without it the first waits out sixty seconds and says *no
    window appeared* while the second dies on a `KeyError` mid-scenario.
    Putting it in the shared roster would refuse `lagcheck.py`, which
    never calls it — and a gate that cries wolf is a gate that gets
    turned off.
    """
    _a_free_display(monkeypatch)
    monkeypatch.setattr(driven.shutil, "which",
                        lambda b: None if b == "xwininfo" else f"/usr/bin/{b}")
    driven.refuse_if_the_run_cannot_happen(lib=_facts(), other=[])
    with pytest.raises(driven.Refused) as caught:
        driven.refuse_if_the_run_cannot_happen(
            needs=(*driven.CORE, "xwininfo"), lib=_facts(), other=[])
    assert "xwininfo" in str(caught.value)
    assert "x11-utils" in str(caught.value), "name the package, not the binary"


def test_a_tool_that_shells_out_to_a_binary_declares_it():
    """The other half of `needs`: naming it at the call is only honest
    if the tools that call it do.

    Checked for the binaries outside `CORE` — exactly the ones nothing
    refuses on by default, so a tool that grows a dependency and says
    nothing fails here rather than thirty seconds into a scenario,
    sounding like a defect in the editor (F170).
    """
    optional = sorted(set(driven.BINARIES) - set(driven.CORE))
    undeclared = []
    for path in sorted((ROOT / "tools").glob("*.py")):
        if path.name == "driven.py":
            continue                        # it is the roster
        src = path.read_text()
        declared = re.findall(r"needs=\([^)]*\)", src)
        for binary in optional:
            if (f'"{binary}"' in src
                    and not any(f'"{binary}"' in d for d in declared)):
                undeclared.append(f"{path.name}: {binary}")
    assert not undeclared, (
        "shells out to a binary the preflight was not told about: "
        + ", ".join(undeclared))
