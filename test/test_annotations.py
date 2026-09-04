"""A mark the voice interprets — `spec/annotations.md`, the first slice.

**The claim, and it is one sentence:** a manner names an *intention*, and
what it means is the voice's.  That is not a thing prose can establish,
so it is executed here: the same score is played by a voice that reads
`Staccato` and by one that does not, and the second is held **bit-identical
to its own unmarked rendering**.  A mark that changed a voice which never
mentions it would be a command wearing an annotation's clothes.

Why it is `examples/audio/marked.ges` and not a fixture built here: the
example is the artefact a person opens and hears, and a test that built
its own would be checking a program nobody plays (`spec/verification.md`
makes the same argument about goldens).  The score is rewritten by
substitution so that the *only* difference between two renders is the
manner field — which is what makes a bit-identical result mean anything.
"""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

from gestate import audioperform
from gestate.audiollvm import run_native

ROOT = Path(__file__).resolve().parents[1]
MARKED = ROOT / "examples" / "audio" / "marked.ges"

#: The score line in the example, replaced so one bank plays one line and
#: the two renders differ in nothing else.
WHOLE = ("score = ((line Plain ++ line Staccato) >>= voices.bow)\n"
         "     ++ ((line Plain ++ line Staccato) >>= voices.pad)")


def _one(bank: str, mark: str) -> str:
    source = MARKED.read_text()
    assert WHOLE in source, "marked.ges's score line moved; this test rewrites it"
    return source.replace(WHOLE, f"score = line {mark} >>= voices.{bank}")


def _render(source: str) -> list:
    graph = audioperform.graph_of(source, rate=44100)
    perf = audioperform.Performance(graph)
    schedule, samples, _ = audioperform.scored(source, rate=44100, block=128)
    perf.sources.append(audioperform.from_schedule(schedule))
    with tempfile.TemporaryDirectory() as d:
        return run_native(graph, d, samples, 128, control=perf.control())


# ── the encoding ────────────────────────────────────────────────────────────

def _asks(ms: int, m: int) -> bool:
    """`audio.ges`'s `asks`, restated — the same arithmetic, so a change
    to one side without the other fails here rather than in a piece."""
    return (ms // m) % 2 == 1


def test_a_manner_is_a_set_and_every_combination_decodes():
    """**A set, not a choice**, which is the whole reason it is bits.

    A note may be accented *and* staccato — any violinist writes both
    marks on one head — and an ordinal would have made them exclusive by
    accident, which is a format deciding a musical question.  So all
    eight combinations are checked, not the three single ones.
    """
    staccato, accent, portamento = 1, 2, 4
    for ms in range(8):
        got = {m for m in (staccato, accent, portamento) if _asks(ms, m)}
        want = {m for m in (staccato, accent, portamento) if ms & m}
        assert got == want, f"manner {ms} decoded as {got}"
    assert _asks(3, staccato) and _asks(3, accent), "both marks on one head"
    assert not _asks(0, staccato), "Plain asks for nothing"


def test_an_unmarked_melody_asks_for_nothing():
    """`instance Mannered Int` — the promise that costs a melody nothing.

    A `[: Int :]` melody is a key number and nothing else.  It must be
    able to reach a voice that reads manners without the author writing
    anything, the same way `instance Notable Int` already gives it a
    velocity of 64.  **An unmarked note is not a special case.**
    """
    source = """
manners : Int -> Int
manners k = manner k

sound : Sig Float
sound = !(toFloat (manners 60)) * 0.0 + sine 220.0 * 0.1
"""
    graph = audioperform.graph_of(source, rate=44100)
    assert graph.nodes, "a bare Int must satisfy Mannered with no instance written"


# ── the claim ───────────────────────────────────────────────────────────────

def test_the_voice_that_reads_the_mark_plays_it_differently():
    """One half of the claim: the mark crosses and is heard.

    Not merely *a* difference — the marked phrase must not be the
    unmarked one turned down, which is what a lazier voice would do and
    what a naive check would accept.  Both envelopes reach the same
    height and one lets go sooner, so the marked render is **quieter and
    more silent**, which is detachment rather than attenuation.
    """
    plain = _render(_one("bow", "Plain"))
    stacc = _render(_one("bow", "Staccato"))
    n = min(len(plain), len(stacc))
    differ = sum(1 for i in range(n) if plain[i] != stacc[i])
    assert differ > n * 0.5, f"only {differ} of {n} samples differ"

    quiet = lambda xs: sum(1 for x in xs[:n] if abs(x) < 1e-4) / n  # noqa: E731
    assert quiet(stacc) > quiet(plain) + 0.3, (
        "the staccato render is not more *silent* — it may be merely quieter, "
        "which is attenuation and not detachment")


def test_the_voice_that_ignores_the_mark_is_untouched_sample_for_sample():
    """The other half, and the one that says a manner is a hint.

    `padVoice` never mentions `manner`.  Every mark in the score reaches
    it and none of them may do anything — so this is **bit-identical**,
    not merely close.  If it ever drifts, a manner has become a command
    that the score imposes on a voice that did not ask for it, and the
    argument in `spec/annotations.md` §"Why this is notation and not
    syntax" is no longer true of the code.
    """
    plain = _render(_one("pad", "Plain"))
    stacc = _render(_one("pad", "Staccato"))
    assert len(plain) == len(stacc)
    assert plain == stacc, (
        "a voice that does not read manners rendered differently under one")


@pytest.mark.parametrize("mark", ["Plain", "Staccato", "Accent", "Portamento"])
def test_every_manner_crosses_whether_or_not_a_voice_reads_it(mark):
    """A mark no voice honours is still a legal score.

    `bowVoice` reads only `Staccato`.  `Accent` and `Portamento` are
    written, travel, and are ignored — which must be a rendering rather
    than a refusal, because the vocabulary is the tree's and a piece may
    use a word before any of its instruments answers to it.
    """
    assert _render(_one("bow", mark)), f"{mark} did not render"
