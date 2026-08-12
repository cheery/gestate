"""The snippets the editor pastes — do they still compile?

`gestate/templates/` is a list of the language's ideas, ready to insert
from the palette.  A template that has gone stale is worse than a stale
example: an example is read beside its lesson, and a template is *pasted
into somebody's file* by a person who reached for it because they did
not know how to write it themselves.  So the promise `examples/README.md`
makes — an example that stops working is a failing test rather than a
stale file — is made here too, and this is it.

**Built, not rendered.**  `test_courses.py`'s reasoning applies exactly:
rendering costs minutes and building costs seconds, and what actually
rots is a name the libraries renamed or a construct the fragment
refuses.

Each template is a *fragment*, so it is built against a skeleton — the
smallest program that gives it somewhere to be.  Two of them are halves
of one idea (`score` plays the bank `voices` declares), which the
template's own header says, and `NEEDS` is that sentence made runnable.
"""

from __future__ import annotations

import pytest

from gestate.audioperform import graph_of
from gestate.session import Snippet, templates

#: What a template with no `sound` of its own is built against.
SKELETON = "sound : Sig Float\nsound = 0.2 * sine 220.0\n"

#: A template that is half of an idea, and the half it needs.
NEEDS = {"score": ("voices",)}

#: A template that supplies its own `sound`, so the skeleton would be a
#: second declaration of one.
OWNS_SOUND: tuple = ()


def _program(snip: Snippet) -> str:
    parts = [templates_by_name()[n].body for n in NEEDS.get(snip.name, ())]
    parts.append(snip.body)
    if snip.name not in OWNS_SOUND:
        parts.append(SKELETON)
    return "\n".join(parts)


def templates_by_name() -> dict:
    return {s.name: s for s in templates()}


ALL = templates()


def test_there_are_templates():
    """A glob that matched nothing would make every sweep here vacuous."""
    assert ALL, "gestate/templates/ has no .ges in it"
    assert {"knob", "voices"} <= {s.name for s in ALL}


@pytest.mark.parametrize("snip", ALL, ids=lambda s: s.name)
def test_a_template_builds(snip):
    """What the palette pastes is a program the compiler accepts."""
    graph = graph_of(_program(snip), rate=8000)
    assert graph.nodes, f"`{snip.name}` extracted to an empty graph"


@pytest.mark.parametrize("snip", ALL, ids=lambda s: s.name)
def test_a_template_says_what_it_is(snip):
    """A template cannot exist without a sentence, because the list is
    the only way anybody meets it."""
    assert snip.summary, f"`{snip.name}` has no `#:` header"
    assert snip.summary.endswith("."), \
        f"`{snip.name}`'s summary is not a sentence: {snip.summary!r}"


@pytest.mark.parametrize("snip", ALL, ids=lambda s: s.name)
def test_a_template_pastes_no_prose(snip):
    """**The documentation stays behind**, which is the whole rule.

    Checked on the body rather than on the stripper, because the thing
    that matters is what lands in the file — a stripper that worked on
    every case but the one a template actually uses would pass a test
    written the other way round.
    """
    assert snip.body, f"`{snip.name}` is all prose and no program"
    for line in snip.body.splitlines():
        assert not line.lstrip().startswith("#"), \
            f"`{snip.name}` pastes a comment: {line!r}"
    assert "\n\n\n" not in snip.body, \
        f"`{snip.name}` pastes a drift of blank lines where a header was"
    assert not snip.body.startswith("\n"), \
        f"`{snip.name}` pastes a gap at the top"
    # **No tabs, and this is a wire fact rather than a style one.**  An
    # `insert` order is one tab-separated line (`furniture.rs`), so a tab
    # in a body would end the argument and paste half a template with
    # nothing said.  A truncation nobody is told about is worse than a
    # refusal, so it is refused here where it can be seen.
    assert "\t" not in snip.body, \
        f"`{snip.name}` has a tab, which the insert order would truncate at"


def test_a_trailing_comment_survives_because_deciding_needs_the_tokenizer():
    """The rule is *full-line* comments, and it is stated rather than fudged.

    A `#` part way along a line may be a comment or may be a character in
    a string, and telling them apart is the tokenizer's job — which a
    snippet is not worth.  `templates/README.md` says so, and this holds
    the behaviour that sentence describes.
    """
    from gestate.session import _uncommented

    kept = _uncommented(["#: a header", "", "x : Int", "x = 5  # kept"])
    assert kept == "x : Int\nx = 5  # kept\n"
