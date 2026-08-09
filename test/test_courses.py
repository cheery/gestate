"""The course examples — `doc/beginner.md` through `doc/super.md` — build.

`examples/README.md` promises that an example which stops working is a
failing test rather than a stale file, and the course directories joined
`examples/` after that promise was made.  Rendering all of them would cost
minutes; *building* them costs seconds and catches what actually breaks —
a parse error, a type error, a name the libraries renamed, a construct the
audio fragment refuses.  The renders themselves were listened to when the
guides were written, and a guide's `try:` edits keep re-listening to them.

`07-midifile.ges` is a music program (a `score` and no `sound`), so it is
laid out through the MIDI backend instead of extracted as a graph — the
same split `doc/ref/index.md`'s backend table describes.
"""

from pathlib import Path

import pytest

from gestate.audioperform import graph_of
from gestate.midi import perform

EXAMPLES = Path(__file__).resolve().parent.parent / "examples"
COURSES = ("beginner", "intermediate", "advanced", "super")

MUSIC_ONLY = {"07-midifile.ges"}


def _course_files() -> list:
    return [p for course in COURSES
            for p in sorted((EXAMPLES / course).glob("*.ges"))]


@pytest.mark.parametrize("path", _course_files(),
                         ids=lambda p: f"{p.parent.name}/{p.name}")
def test_course_example_builds(path):
    source = path.read_text()
    if path.name in MUSIC_ONLY:
        bpm, events = perform(source)
        assert bpm > 0 and events, "the piece laid out to nothing"
    else:
        graph = graph_of(source, rate=8000)
        assert graph.nodes, "the synth extracted to an empty graph"


def test_every_course_has_lessons():
    """A glob that matched nothing would make the sweep above vacuous."""
    for course in COURSES:
        assert list((EXAMPLES / course).glob("*.ges")), course
