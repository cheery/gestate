"""Nothing in the suite may reach the sound card.

**This is a real bug, and it has three doors.**  `audiolive.play` with no
`command` reaches the card **either** through `sounddevice` — PortAudio,
tried first and silently skipped only when the import fails — **or**, when
that is not installed, by falling through to `player_command()`, which finds
`pw-play`, `paplay` or `aplay` and pipes the synth into the speakers.  Nine
tests in `test_audioeditor.py` built a `Workbench` without a `command` and
then started it, so a full run played several seconds of `twoknobs.ges` and
`duet.ges` out loud — into whatever room the run was happening in.

**The third door was cut later and went straight through this guard.**
`gestate/host.c` opens ALSA *itself* — that is the whole point of it, and
it is why the crackle went away — so `Workbench._open_host` reaches a sound
card without passing either of the two functions patched below.  A suite
run played a sine into the room for an hour before anybody was in it.  The
lesson is the one this file already recorded and did not generalise: a
guard on the doors you know about is a guard on the doors you know about.

All three are shut here, and shutting only one is why the noise survived
the first fix: on a machine with `sounddevice` installed the pipe backend is
never reached, so a guard on `player_command` alone sees nothing.

It is not only noise.  A test that reaches a sound card is a test that fails
on a machine with no player installed, passes or fails depending on whether
something else holds the device, and takes real time because the pipe *is*
the clock: the player drains at the sample rate, so a "two second" render
blocks for two seconds.

So the fallback is removed for the duration of the suite, and reaching it is
an error naming the test that did.  A test that means to exercise the live
path passes its own `command` — `["cat"]`, a `dd`, or `test_audioeditor`'s
`_pacer` — which is the real path in everything except the last hop, and the
last hop is the only part that cannot be asserted about anyway.

Set `GESTATE_TEST_AUDIO=1` to put the fallback back, for the rare case of
checking by ear that the live path still makes a sound.
"""

from __future__ import annotations

import os

import pytest


def pytest_configure(config):
    config.addinivalue_line(
        "markers",
        "own_audio_backend: drives a backend with a fake device of its own, "
        "so the sound-card guard must stand aside")


@pytest.fixture(autouse=True)
def _no_sound_card(request, monkeypatch):
    """Both routes out of `audiolive.play`, closed."""
    if os.environ.get("GESTATE_TEST_AUDIO"):
        return
    # A test that supplies its own `sounddevice` is testing the backend, not
    # reaching a device with it — the guard would be blocking the very call
    # it exists to make safe.  Marked rather than name-matched, so the
    # exemption is written where the fake is.
    if request.node.get_closest_marker("own_audio_backend"):
        return

    from gestate import audiolive

    def refuse(door):
        def blocked(*args, **kwargs):
            raise AssertionError(
                f"{request.node.nodeid} reached the sound card via {door}.\n"
                "`audiolive.play` was called with no `command`.  Pass one — "
                "`[\"cat\"]`, a `dd`, or `test_audioeditor._pacer` — so the "
                "test plays into a file rather than into the room.  "
                "See test/conftest.py.")
        return blocked

    monkeypatch.setattr(audiolive, "player_command", refuse("a system player"))
    monkeypatch.setattr(audiolive, "play_through_sounddevice",
                        refuse("sounddevice"))

    # The third door: `host.c` opens the card itself.  Both the opening and
    # the loop are shut, because either alone would leave the other able to
    # make a noise — `run_device` on a host somebody opened earlier, or an
    # open that no test happens to render through *yet*.
    #
    # `Workbench._open_host` catches everything and falls back to the Python
    # driver, so a test that gets here still fails — on one of the two
    # guards above, naming itself.  What it will not do is play.
    from gestate import audiohost

    monkeypatch.setattr(audiohost.Host, "open", refuse("the C audio host"))
    monkeypatch.setattr(audiohost.Host, "run_device",
                        refuse("the C audio host's device loop"))
