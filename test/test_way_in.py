"""The way in, held to what a stranger can actually carry out.

**Every test here was written because a person stopped at the thing it
checks.**  `board/stranger-test.md`'s run two, 2026-08-18: Janne cloned
the tree over chat and reached a Python traceback in six minutes, and
each stop he made is a check below.

The way in is the one part of this project its author cannot measure by
reading — the missing information is in his head, so his own walk of
`doc/install.md` on a fresh machine (2026-08-17) found three defects and
missed both of these.  See `fixme.md` F162 and F163.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent

#: The two files that are the way in.  `README.md` is what a reader
#: meets first and `doc/install.md` is the long form; they carry the
#: same block, so a fix to one that misses the other is the failure
#: this parametrisation exists to catch.
WAY_IN = ("README.md", "doc/install.md")


def blocks(name: str) -> list[str]:
    text = (ROOT / name).read_text(encoding="utf-8")
    return re.findall(r"```sh\n(.*?)```", text, re.S)


@pytest.mark.parametrize("name", WAY_IN)
def test_the_shell_that_installs_can_find_cargo(name: str):
    """**F163** — `rustup` installs `cargo` by editing a shell profile
    the running shell has already read, so the sourcing step is not an
    optional nicety: without it the next command that needs `cargo`
    fails, several steps later, in a Python traceback.

    It was there, as a **trailing comment** on the end of a long
    `curl … | sh` line — the weakest position a required step can
    occupy, and Janne walked straight past it.  So what is checked is
    that it stands as **its own line**: a comment can be missed, a line
    has to be run.
    """
    for block in blocks(name):
        if "sh.rustup.rs" not in block:
            continue
        lines = [ln.strip() for ln in block.splitlines()]
        assert any(ln.startswith('. "$HOME/.cargo/env"') for ln in lines), (
            f"{name}: the block that installs rust never sources "
            "`$HOME/.cargo/env` on a line of its own, so a reader who "
            "stays in the same shell has rustup installed and cargo "
            "invisible (fixme.md F163)")
        return
    pytest.fail(f"{name}: no shell block installs rust any more — "
                "this test is checking a way in that has moved")


def test_the_missing_cargo_is_not_told_to_run_cargo():
    """**F163's sharper half.**  The error a person actually reached
    said *"no cargo to build it — `cargo build --release --features
    capi` in `shell/editor/` makes one"*: an instruction that cannot be
    carried out **by definition**, since the reason it is printed is
    that `cargo` does not exist.

    `vision.md` — *"Gestate won't ever do anything unexpected
    silently"* — is about errors arriving; this is about the sentence
    they arrive with.  An error that advises the impossible is worse
    than a silent one, because the reader spends their time obeying it.

    Read out of the source rather than provoked, deliberately: making
    `shutil.which` lie would test the mock, and what is at stake here is
    the **words**, which is the thing that rotted.
    """
    text = (ROOT / "gestate" / "editor.py").read_text(encoding="utf-8")
    found = re.search(r"cargo` is not on PATH.*?again", text, re.S)
    assert found, (
        "gestate/editor.py no longer explains a missing cargo — the "
        "message a stranger reaches when the editor has to be built "
        "and cannot be (fixme.md F163)")
    said = found.group(0)
    assert "$HOME/.cargo/env" in said, (
        "the missing-cargo message does not name the sourcing step, "
        "which is the fix in the overwhelming majority of cases")
    assert "rustup.rs" in said, (
        "the missing-cargo message does not say where rust comes from "
        "for a reader who has none")


@pytest.mark.parametrize("name", WAY_IN)
def test_the_first_run_says_it_is_about_to_compile(name: str):
    """**F163's third finding**, and the one still open when the run
    reached it: the first `python -m gestate.workbench` spends a minute
    or two in `cargo build --release`, silently, and nothing a reader
    following `README.md` had seen said so.

    `doc/install.md` did say it — in the long-form list of what each
    dependency buys, which is not the file somebody is holding when
    they run the command.  **Information in the file he is not reading
    is not information he has**, and that is the general shape of it:
    both ways in have to carry it, so both are checked.

    Janne had to be told out loud, by the author, at 13:37
    (`board/stranger-test.md`).  A reader whose build *fails* now meets
    it in the error text; a reader whose build succeeds meets only the
    silence, and that is the commoner case.
    """
    text = (ROOT / name).read_text(encoding="utf-8")
    assert "gestate.workbench" in text, (
        f"{name} no longer shows how to open the workbench — this test "
        "is checking a way in that has moved")
    assert re.search(r"cargo\s+build", text), (
        f"{name} shows `python -m gestate.workbench` and never says the "
        "first run compiles the editor, so its silence has no "
        "explanation (fixme.md F163)")


def test_the_first_build_says_it_is_working():
    """**F163's fourth face.**  Measured on a stranger's machine the
    first build took *10–15 seconds* — nothing, by build standards — and
    he volunteered it anyway as *melko pitkä viive*, a fairly long
    delay, because the terminal said nothing at all.

    So the defect was never the duration, and making it faster would
    have fixed nothing.  `--quiet` plus `capture_output=True` means
    cargo cannot speak for itself here, which is correct — its output is
    wanted only when the build fails — and leaves exactly one line to
    write.
    """
    text = (ROOT / "gestate" / "editor.py").read_text(encoding="utf-8")
    build = text.index('"cargo", "build"')
    before = text[:build]
    assert "building the editor" in before, (
        "nothing is printed before the first `cargo build`, so a "
        "newcomer's first run of the workbench is a silent wait with no "
        "explanation (fixme.md F163)")


def test_the_starter_never_rides_in_the_tree():
    """**F164** — `untitled.desk` was committed by accident and lived in
    the repository root until somebody noticed.

    `untitled.ges` is what a bare `tools/gestate-editor` opens, in the
    **working directory**, which for anybody working here is this tree
    (F154 is the same trap catching a harness).  Neither it nor its
    `.desk` is a piece; the moment either is worth keeping, it gets a
    name.

    Checked against **git's index** rather than the filesystem, because
    the file being *present* is normal and expected — it is being
    *tracked* that is the defect.
    """
    import subprocess
    listed = subprocess.run(["git", "ls-files"], cwd=ROOT,
                            capture_output=True, text=True, check=True)
    stray = [f for f in listed.stdout.split()
             if Path(f).name in ("untitled.ges", "untitled.desk")]
    assert not stray, (
        "the starter's own files are tracked, and they belong to no "
        f"piece: {', '.join(stray)}.  `git rm --cached` them; "
        ".gitignore already refuses them (fixme.md F164)")
