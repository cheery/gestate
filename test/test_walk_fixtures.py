"""The window's half of the canvas seam — are the fixtures today's payload?

`test_panel_fixtures.py` is this file's twin, and its argument is this
file's argument: `shell/editor/src/walk.rs`'s tests run against
**checked-in copies** of `Substrate.payload()` — `fader.walk`,
`ticker.walk`, `scoped.walk` — and until this file nothing compared them
with the living model.  The payload could move, `cargo test` would stay
green against the stale bytes, and the first red thing would be
somebody's workbench.

It moved.  On 2026-09-09 the workbench would not start: `Meaning` had
joined `export._SUB_CONS` and the three fixtures still carried the
fourteen-tag table from before it, `walk.rs`'s `TAGS` still said
fourteen, and `ticker.walk`'s program had drifted from its own source
some time earlier with nothing to say so.  Every one of those is a copy
left behind by an edit to the thing it copies, which is the shape
`test_panel_fixtures.py` was written about — on the other side of the
same seam.

So: regenerate each fixture from the source its `walk.rs` comment names,
and require equality.  When one of these fails, the payload moved.  That
is not a defect in this test — it is the seam saying so.  Regenerate the
fixture, run

    cargo test -p gestate-editor

and commit the two sides together.

**`TAGS` itself is held next door**, by
`test_panel_fixtures.py::test_every_shell_counts_the_constructor_table_the_same`
— together with the plugin's `[i64; N]` and the page shell's
`from_raw_parts`, because all three are one copy of `len(_SUB_CONS)`
written in another language and they go stale on the same day.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "shell" / "editor" / "tests"

sys.path.insert(0, str(Path(__file__).resolve().parent))

MOVED = ("the payload moved: regenerate shell/editor/tests/%s and run "
         "`cargo test -p gestate-editor` — the two sides ship together")


def _sources() -> dict[str, tuple[str, tuple[tuple[str, float], ...]]]:
    """Each fixture, with the program it is a payload of.

    **Imported, never copied.**  The sources live where they are already
    under test — `walk.rs`'s comments name them — and a second copy here
    would be one more thing to fall behind, which is the whole subject of
    this file.
    """
    from test_audioeditor import TICKING
    from test_substrate import FADER

    return {
        # `walk.rs` mod walker_tests: "`gui.Substrate(FADER).payload()`
        # with `dragged` at 0.25".
        "fader.walk": (FADER, (("dragged", 0.25),)),
        # mod tick_tests: a canvas folding over `events`.
        "ticker.walk": (TICKING, ()),
        # mod trace_tests: `examples/audio/scoped.ges`'s canvas.
        "scoped.walk": ((ROOT / "examples" / "audio" / "scoped.ges")
                        .read_text(), ()),
    }


def _payload(source: str, writes) -> str:
    from gestate.gui import Substrate

    sub = Substrate(source, rate=8000)
    for name, value in writes:
        sub.write(name, value)
    text = sub.payload()
    assert text is not None, "this program has a canvas that crosses"
    return text.rstrip("\n")


def test_the_walk_fixtures_are_todays_payload():
    """What `Substrate.payload()` writes is what the window reads."""
    for name, (source, writes) in _sources().items():
        want = (FIXTURES / name).read_text().rstrip("\n")
        assert _payload(source, writes) == want, MOVED % name
