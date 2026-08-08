"""Placing a graph node in the file it was written in.

`gestate/audiospans.py` joins two facts the pipeline deliberately keeps
apart: `Node.origin` identifies a node *stably across recompiles* and is
therefore not a position, and the front end knows positions but not which
node they became.  An environment that draws a knob beside the line
declaring it needs both.

The tests that matter here are the ones about **which file**.  A synth is
assembled from four, combined two different ways, and only one of the two
preserves line numbers — so every assertion below reads the line back out
of the file the site names and checks it is the definition it claims.  A
join that is wrong by one line, or right in the author's file and wrong in
`audio.ges`, would otherwise pass anything weaker.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from gestate.audio import assemble
from gestate.audiospans import (Site, controls, declaration_sites, locate,
                                main, prelude_lines, sites)
from gestate.audioextract import extract_analysis
from gestate.pipeline import analyse

AUDIO_DIR = Path(__file__).resolve().parent.parent / "examples" / "audio"
EXAMPLES = ["blip.ges", "drums.ges", "knob.ges", "fm.ges", "pluck.ges"]

#: Low, because nothing here depends on the rate and the front end is what
#: costs.
RATE = 8000


def _source(name: str) -> str:
    return (AUDIO_DIR / name).read_text()


def _line_of(site: Site, source: str) -> str:
    """The line the site names, read out of the file it names."""
    text = (site.path.read_text() if site.path else source).splitlines()
    return text[site.line - 1]


# ── Every site names a real definition ──────────────────────────────────────


@pytest.mark.parametrize("name", EXAMPLES)
def test_every_site_lands_on_its_own_definition(name):
    """The whole claim, checked against the files rather than a table.

    A site says "`lowpass`, `audio.ges` line 80"; this reads line 80 of
    `audio.ges` and requires it to be defining `lowpass`.  Nothing weaker
    would catch the failure this module exists to avoid — an off-by-one
    from the prelude offset, which is silently plausible in every direction.
    """
    source = _source(name)
    found = locate(source, rate=RATE, path=name)
    assert found, f"{name} produced no sites at all"

    for site in found:
        line = _line_of(site, source)
        assert line.split()[0:1] == [site.name] or line.startswith(site.name), (
            f"{site.file}:{site.line} is {line!r}, "
            f"which does not define `{site.name}`")


@pytest.mark.parametrize("name", EXAMPLES)
def test_every_node_of_the_graph_is_placed(name):
    """No node falls through.

    Not guaranteed by construction — a node whose origin names nothing
    placeable is dropped rather than guessed — so the examples are checked
    to have no such node.  If a future one does, this fails and says so
    rather than the environment quietly missing a control.
    """
    source = _source(name)
    analysis = analyse(assemble(source, RATE))
    graph = extract_analysis(analysis, entry="sound", rate=RATE)
    placed = {s.node for s in sites(graph, analysis, source, name)}
    assert placed == {n.id for n in graph.nodes}


# ── The four files ──────────────────────────────────────────────────────────


def test_all_four_files_are_reachable():
    """The point of the module, and the case a single offset cannot do.

    `knob.ges` reaches its own source, `audio.ges` (`ticks`, `lowpass`) and
    `signal.ges` (`gain`) through its graph; `prelude.ges` is reached
    through the declaration table, since nothing in it is signal-valued and
    so nothing in it becomes a node.
    """
    source = _source("knob.ges")
    files = {s.file for s in locate(source, rate=RATE, path="knob.ges")}
    assert files == {"knob.ges", "audio.ges", "signal.ges"}

    analysis = analyse(assemble(source, RATE))
    known = declaration_sites(analysis, source, "knob.ges")
    assert {v[0] for v in known.values()} == {
        "knob.ges", "audio.ges", "signal.ges", "prelude.ges"}


@pytest.mark.parametrize("name,file,starts", [
    ("knob", "knob.ges", "knob ="),
    ("ticks", "audio.ges", "ticks ="),
    ("lowpass", "audio.ges", "lowpass k s ="),
    ("gain", "signal.ges", "gain g s ="),
    ("floor", "prelude.ges", "floor x ="),
    ("sin", "prelude.ges", "sin x ="),
])
def test_a_definition_from_each_file_is_placed_exactly(name, file, starts):
    """One from each, read back.

    `prelude.ges` is the one that cannot be placed by arithmetic at all:
    it is merged as a *module*, so its spans are in its own coordinates and
    a line test against the assembled program would put `floor` in the
    middle of whatever the author happens to be writing.
    """
    source = _source("knob.ges")
    analysis = analyse(assemble(source, RATE))
    known = declaration_sites(analysis, source, "knob.ges")

    assert name in known, f"`{name}` was not placed"
    got_file, path, line, _col, _el, _ec = known[name]
    assert got_file == file
    text = (path.read_text() if path else source).splitlines()
    assert text[line - 1].startswith(starts)


def test_the_authors_file_has_no_path_and_the_preludes_do():
    """An editor opens a prelude by path; the author's file it already has.

    Which is also the honest division of knowledge: this module is given
    source *text*, so it cannot know where that text came from, and saying
    so beats inventing a path.
    """
    source = _source("knob.ges")
    for site in locate(source, rate=RATE, path="knob.ges"):
        if site.file == "knob.ges":
            assert site.path is None and not site.is_prelude
        else:
            assert site.path is not None and site.is_prelude
            assert site.path.exists()


def test_the_file_name_defaults_to_a_placeholder():
    """`path` is optional, and its absence must not look like a real file."""
    source = _source("blip.ges")
    files = {s.file for s in locate(source, rate=RATE)}
    assert "<source>" in files


# ── Control-rate placement, which is what this is for ───────────────────────


def test_the_knob_is_placed_at_the_line_that_declares_it():
    """The feature the join exists for.

    `knob.ges` has exactly one control-rate source, and it should resolve to
    `knob` — not to `sound`, which is where the chain ends, and not to
    `driven`, which is where the two clocks meet.  The innermost definition
    of the origin path is the one that introduced the parameter.
    """
    source = _source("knob.ges")
    found = controls(source, rate=RATE, path="knob.ges")

    assert len(found) == 1
    site = found[0]
    assert site.name == "knob"
    assert site.file == "knob.ges"
    assert site.is_control and site.kind == "source"
    assert _line_of(site, source).startswith("knob =")


@pytest.mark.parametrize("name", ["blip.ges", "drums.ges", "fm.ges",
                                  "pluck.ges"])
def test_a_synth_with_no_second_clock_offers_no_controls(name):
    """The audio clock is not a knob.

    Every synth has a `ticks` source, and it is control-rate in none of
    them — so an environment that offered a slider per source would offer
    one for the sample counter.
    """
    assert controls(_source(name), rate=RATE, path=name) == []


def test_several_knobs_are_placed_at_their_own_declarations():
    """One site per parameter, which is the point of one channel each.

    This test used to assert the opposite — that a second control channel
    was *rejected* — and the rule behind it conflated two rates with two
    channels.  Now each knob is its own source, with its own origin and its
    own line, which is exactly what an environment drawing a control beside
    its declaration needs.
    """
    source = """
ca : Chan Int
ca = chan

cb : Chan Int
cb = chan

first : Sig Int
first = 0 ::: mkSig (wait ca)

second : Sig Int
second = 0 ::: mkSig (wait cb)

addUp : Int -> Int -> Int
addUp a b = a + b

blend : Int -> Int -> Float
blend n k = toFloat k * 0.001

sound : Sig Float
sound = zip blend ticks (zip addUp first second)
"""
    found = controls(source, rate=RATE, path="two.ges")
    assert [s.name for s in found] == ["first", "second"]
    assert all(s.file == "two.ges" and s.kind == "source" for s in found)
    # Reading order, since the caller is about to lay them down a page.
    assert [s.line for s in found] == sorted(s.line for s in found)
    lines = source.splitlines()
    assert lines[found[0].line - 1].startswith("first =")
    assert lines[found[1].line - 1].startswith("second =")


def test_only_a_source_is_offered_as_a_control():
    """`clock` means nothing on any other node — `fixme.md` F93.

    A `map` over a control-rate source keeps the default `"audio"`, and no
    reader of the graph consults it, so selecting on `clock` alone would be
    reading a field that has no answer.  `scaled` below is exactly that
    node; it must not be offered as a knob, and `knob` must.
    """
    source = """
kc : Chan Int
kc = chan

knob : Sig Int
knob = 40 ::: mkSig (wait kc)

scaled : Sig Int
scaled = map (k => k * 2) knob

blend : Int -> Int -> Float
blend n k = toFloat k * 0.001

sound : Sig Float
sound = zip blend ticks scaled
"""
    found = controls(source, rate=RATE, path="one.ges")
    assert [s.name for s in found] == ["knob"]
    assert found[0].kind == "source"

    placed = {s.name: s for s in locate(source, rate=RATE, path="one.ges")}
    assert not placed["scaled"].is_control, "a map is not a knob"


# ── The offset itself ───────────────────────────────────────────────────────


def test_the_prelude_offset_is_where_the_authors_first_line_lands():
    """Checked against `assemble` rather than recomputed.

    The offset is the one number everything here depends on, and it is
    derived from the same strings `assemble` concatenates so that adding a
    line to `audio.ges` cannot move the two apart.  This asserts they did
    not.
    """
    source = "# first line of the author's file\n" + _source("blip.ges")
    assembled = assemble(source, RATE).splitlines()
    assert assembled[prelude_lines()] == "# first line of the author's file"


# ── The CLI ─────────────────────────────────────────────────────────────────


def test_the_cli_prints_the_placement(capsys):
    assert main([str(AUDIO_DIR / "knob.ges"), "--rate", str(RATE),
                 "--source"]) == 0
    out = capsys.readouterr().out
    assert "knob.ges:" in out and "audio.ges:" in out
    assert "knob = 40 ::: mkSig (wait knobChan)" in out


def test_the_cli_reports_a_program_it_cannot_place(tmp_path, capsys):
    bad = tmp_path / "bad.ges"
    bad.write_text("sound : Int\nsound = 1\n")
    assert main([str(bad)]) == 1
    assert "gestate:" in capsys.readouterr().err


# ── Error messages, in the author's coordinates ─────────────────────────────
#
# `audio.assemble` hands the compiler one text with every prelude on the
# front, so a position in an error counts from the top of *that* — which is
# 869 lines above the author's first line and names no file.  It read as
# "weird line numbers", and it got worse rather than started when
# `synth.ges` was prepended: the offset was 182 before it.


def test_an_error_position_is_moved_into_the_authors_file():
    from gestate.audiospans import in_source

    source = "sound : Sig Float\nsound = map (n =>\n"
    offset = prelude_lines(source)
    # `Pos` counts lines from 0 and this counts from 1, because a gutter
    # does — so the author's line 2 is assembled line `offset + 1`.
    message = f"expected atom, got T(NEWLINE,'\\n',Pos({offset + 1},17))"
    assert in_source(message, source, "mysynth.ges") == \
        "expected atom, got T(NEWLINE,'\\n',mysynth.ges:2:17)"


def test_a_span_range_moves_at_both_ends():
    from gestate.audiospans import in_source

    source = "sound : Sig Float\nsound = 1\n"
    offset = prelude_lines(source)
    message = (f"Type mismatch: expected 'Float' (at {offset}:8–{offset}:17), "
               f"got 'Int' (at {offset + 1}:8–{offset + 1}:9)")
    assert in_source(message, source, "s.ges") == (
        "Type mismatch: expected 'Float' (at s.ges:1:8–s.ges:1:17), "
        "got 'Int' (at s.ges:2:8–s.ges:2:9)")


def test_a_position_inside_a_prelude_says_so_rather_than_going_negative():
    """It means the error is in `synth.ges` or `audio.ges`, not in yours.

    Disguising it as a line of the author's file — or as a negative one —
    would send somebody looking in the wrong place.
    """
    from gestate.audiospans import in_source

    assert "prelude line 90" in in_source("boom (at 89:12)", "", "s.ges")


def test_a_message_with_no_positions_is_left_alone():
    from gestate.audiospans import in_source

    message = "Unknown global 'nosuchthing' (not defined as a supercombinator)"
    assert in_source(message, "sound = 1\n", "s.ges") == message


def test_a_scored_program_uses_the_bigger_offset():
    """A performance is assembled with `music.ges` too, so its author's
    first line is further down — and an error in it must not be reported
    nine lines early."""
    from gestate.audiospans import in_source

    scored = "score : [: Void :]\nscore = r >>= voices.lead\n"
    plain = "sound : Sig Float\nsound = map (n => 0.0) ticks\n"
    assert prelude_lines(scored) > prelude_lines(plain)
    at = prelude_lines(scored)
    assert in_source(f"boom (at {at}:0)", scored, "p.ges") == \
        "boom (at p.ges:1:0)"


# ── `mkKnob` — a parameter in one line ──────────────────────────────────────


#: Two parameters declared the short way.  The long form is a `Chan` and a
#: `:::`; this is the same graph without a channel anyone has to name.
TWO_KNOBS = """level : Sig Float
level = mkKnob 0.6

depth : Sig Float
depth = mkKnob 0.25

Pair := Pair Float Float

pairOf : Float -> Float -> Pair
pairOf a b = Pair a b

outPair : Pair -> Float
outPair p = case p of
    Pair tone d -> tone * d

sound : Sig Float
sound = map outPair (zip pairOf (sine 220.0) depth) * level
"""


def test_two_short_knobs_are_two_separate_channels():
    """`mkKnob` makes an *anonymous* channel, so two uses must not share one.

    The extractor keys a clock by the name of the global it came from, and
    falls back to the node's origin path when there is none — which is what
    keeps two uses of one helper apart.
    """
    from gestate.audioextract import extract

    graph = extract(TWO_KNOBS, rate=RATE)
    sources = graph.control_sources()
    assert len(sources) == 2, "the two knobs collapsed into one channel"
    assert sorted(n.init for n in sources) == [0.25, 0.6]
    assert all(n.type_ == "Float" for n in sources)


def test_a_short_knob_is_placed_at_the_authors_declaration():
    """**Not at `mkKnob`'s own line in `audio.ges`.**

    The origin is `sound/level/mkKnob/source#0`, whose innermost placeable
    component is `mkKnob` — a prelude definition.  Left there, both knobs
    would be called `mkKnob`, sit on the same prelude line, and share one
    slider, because an editor keys a parameter's value by name.
    """
    found = {s.name: s for s in locate(TWO_KNOBS, rate=RATE, path="two.ges")
             if s.is_control}
    assert set(found) == {"level", "depth"}
    for site in found.values():
        assert site.file == "two.ges", f"placed in {site.file}"
        assert not site.is_prelude
    assert found["level"].line < found["depth"].line


def test_the_long_form_is_still_placed_where_it_was():
    """`twoknobs.ges` names its channels, and must not have moved."""
    found = {s.name: s for s in locate(_source("twoknobs.ges"), rate=RATE,
                                       path="twoknobs.ges") if s.is_control}
    assert set(found) == {"pitch", "cutoff"}
    assert all(s.file == "twoknobs.ges" for s in found.values())


def test_a_program_may_still_call_its_own_parameter_knob():
    """Which is why the helper is `mkKnob`.

    The audio prelude is prepended as *text*, so there is no shadowing to
    fall back on the way `prelude.ges` has: a prelude definition called
    `knob` would have made `examples/audio/knob.ges` a duplicate signature.
    """
    found = [s for s in locate(_source("knob.ges"), rate=RATE,
                               path="knob.ges") if s.is_control]
    assert [s.name for s in found] == ["knob"]
    assert found[0].file == "knob.ges"
