"""The first screen, and the first thing behind the one button.

`fixme.md` F150, `board/button.md`.  Both facts here were true for a
week, in front of everybody, and neither was caught by a test because
neither is a behaviour — they are **what the window says**, and what it
said was a sentence naming a control deleted in `71b90af` and a menu
opening on the command that does nothing.

So these are assertions about *the words a stranger meets first*, which
is an odd thing to write a test about until you have watched somebody
fail on them.
"""

from __future__ import annotations

import re
from pathlib import Path

from gestate.audioeditor import STARTER
from gestate.session import vocabulary

ROOT = Path(__file__).resolve().parent.parent
EDITOR = ROOT / "shell" / "editor" / "src"


def test_the_starter_names_no_control_the_window_does_not_have():
    """**The defect, stated so it cannot come back in another word.**

    `[ref]` was the pygame editor's button.  The rule is not "do not
    say `[ref]`" — it is that a sentence on the first screen which
    names a *button* is a claim about the window, and the window has
    exactly one button.
    """
    assert "[ref]" not in STARTER, (
        "the starter names the pygame editor's button, which went with "
        "it in 71b90af")
    for word in ("button", "click", "press"):
        assert word not in STARTER.lower(), (
            f"the starter says {word!r} — if the first screen names a "
            "control, `view.rs` had better still draw it, and this test "
            "cannot check that for you (F150)")


def test_everything_the_starter_points_at_can_be_reached():
    """The other half: it may name *commands*, and those must exist.

    `what` and `fits` replaced the `[ref]` sentence, and they are only
    an improvement while `command.ges` still declares them.
    """
    named = set(re.findall(r"`(\w+)`", STARTER))
    verbs = {v.name for v in vocabulary()}
    # Types and identifiers from the code half of the file are not
    # commands; only check the words that are.
    for word in named & {"what", "fits", "apply", "audition", "play"}:
        assert word in verbs, f"the starter names `{word}`, which is gone"
    assert {"what", "fits"} <= named, (
        "the starter no longer says how to ask the compiler anything")


def test_the_starter_still_makes_a_sound():
    """It is the first screen *and* the first thing anybody hears —
    a bare click on the desktop icon opens on it, playing."""
    assert "sound : Sig Float" in STARTER
    assert "sine" in STARTER


def test_the_list_does_not_open_on_the_command_that_does_nothing():
    """**`command.ges`'s order is the palette's order** — `vocabulary`
    says so deliberately, *"the order somebody thought about them
    rather than alphabetically, which is a worse order for learning"*.

    Which makes the file's first line the first thing a stranger meets,
    and it was `skip`: *"Do nothing — the identity of `++`."*
    """
    verbs = vocabulary()
    assert verbs, "no commands at all"
    assert verbs[0].name != "skip", (
        "the command list opens on the command that does nothing — "
        "`skip` belongs at the foot of command.ges (F150)")
    assert verbs[-1].name == "skip", (
        "`skip` has moved off the end of command.ges; if that was "
        "deliberate, this test is the place to say what replaced it")


def test_the_first_command_is_the_one_the_stranger_needed():
    """He was not stuck at *open* or *hear it* — both had happened by
    themselves.  He was stuck at **hear the change**, which is `apply`.

    Asserting the name and not merely "not skip", because the point is
    not that the list was reordered; it is *what it now opens on*.
    """
    first = vocabulary()[0]
    assert first.name == "apply", (
        "the list no longer opens on `apply` — the move a stranger "
        "needs first is the one that makes an edit audible (F150)")
    assert first.key == "Ctrl-S", "apply has lost its key"
    assert first.summary, "apply has no sentence under it"


def test_the_window_still_has_exactly_one_button():
    """The premise the starter test above leans on.  If a second
    control ever appears, that test's rule needs rewriting rather than
    quietly passing."""
    view = (EDITOR / "view.rs").read_text()
    assert view.count("pub fn burger_box") == 1
    assert "burger_frame" in view
