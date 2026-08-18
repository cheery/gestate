"""The launcher — `workbench.install_desktop`, checked into a fake home.

**The first tier of `board/later/installation-test.md`**, and it exists
because the way in is the part of this project nothing checked.  A
fresh Ubuntu 26.04 laptop found three defects in it in one day, two of
which are pinned here: an `Exec` line that did nothing when the icon
was clicked, and an icon that was not the egg (`test_icon.py`, F148).

Nothing here touches the real `~/.local/share` — `HOME` is a `tmp_path`
for every test, which is the whole reason an installation *can* be
tested without a machine to throw away.
"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest

from gestate import icon, workbench

ROOT = Path(__file__).resolve().parent.parent


@pytest.fixture()
def installed(tmp_path, monkeypatch, capsys):
    """`--desktop`, run against a home directory nobody lives in."""
    monkeypatch.setenv("HOME", str(tmp_path))
    assert workbench.install_desktop() == 0
    capsys.readouterr()
    return tmp_path / ".local" / "share"


def entry(share) -> dict[str, str]:
    text = (share / "applications" / "gestate.desktop").read_text()
    return dict(line.split("=", 1) for line in text.splitlines()
                if "=" in line)


def test_a_bare_click_opens_an_editor(installed):
    """**The defect this file was written for.**

    `Exec` used to be `env PYTHONPATH=… python -m gestate.workbench %f`,
    which is right in every way but the one that matters: a dock click
    passes *no file*, so `%f` expands to nothing — and the module with
    no file answers `a file to edit (or --desktop)` and exits 2, into a
    journal nobody reads, because `Terminal=false`.  The icon did
    nothing.  Henri hit it on a fresh install, 2026-08-17.

    So the two halves are asserted together: the command a click runs,
    and the reason it cannot be the module directly.
    """
    exec_line = entry(installed)["Exec"]
    program = Path(exec_line.split()[0])
    assert program.is_file(), f"Exec names nothing that exists: {program}"
    assert program.name == "gestate-editor", (
        "Exec must be the wrapper — it is what handles a click with no "
        "file, finds the venv, and cds to the tree")
    assert program.stat().st_mode & 0o111, "Exec is not executable"

    # And the fact that makes the wrapper necessary rather than tidy.
    with pytest.raises(SystemExit) as fell:
        workbench.main([])
    assert fell.value.code == 2, (
        "the module still refuses to start without a file, so anything "
        "a click runs must supply one")


def test_the_wrapper_supplies_the_file_a_click_does_not(installed):
    """The other end of it: the wrapper's contract is that it opens
    *something*.  Read from the script, because a launcher pointed at a
    wrapper that stopped defaulting is the same defect again."""
    script = Path(entry(installed)["Exec"].split()[0]).read_text()
    assert "untitled.ges" in script, (
        "tools/gestate-editor no longer opens a scratch file when handed "
        "nothing — a bare click would print a usage line again")


def test_the_dock_can_match_the_window_to_this_entry(installed):
    """`StartupWMClass` and the `WM_CLASS` the window sets must be the
    same string, or GNOME shows a gear beside a window it cannot name —
    which is half of what `--desktop` is for at all."""
    rust = (ROOT / "shell" / "editor" / "src" / "window.rs").read_text()
    declared = entry(installed)["StartupWMClass"]
    assert f'b"{declared}\\0{declared}\\0"' in rust, (
        f"the window no longer declares WM_CLASS={declared}")


def test_the_icons_land_where_hicolor_looks(installed):
    """Every size the installer promises, plus the artwork itself."""
    for side in icon.HICOLOR:
        png = installed / "icons" / "hicolor" / f"{side}x{side}" / "apps"
        assert (png / "gestate.png").read_bytes() == icon.png(side)
    scalable = installed / "icons" / "hicolor" / "scalable" / "apps"
    assert (scalable / "gestate.svg").read_text() == icon.svg()


@pytest.mark.skipif(shutil.which("desktop-file-validate") is None,
                    reason="desktop-file-utils is not installed")
def test_the_entry_is_valid_by_the_specification(installed):
    """An oracle written by somebody else, which is the kind worth
    having.  Hints are allowed through: the live one says the three
    categories put gestate in more than one menu, and whether that is
    wanted is a decision, not a defect (`board/later/installation-test.md`)."""
    done = subprocess.run(
        ["desktop-file-validate",
         str(installed / "applications" / "gestate.desktop")],
        capture_output=True, text=True)
    assert "error:" not in (done.stdout + done.stderr).lower(), done.stdout
    assert done.returncode == 0, done.stdout
