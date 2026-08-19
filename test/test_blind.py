"""`tools/blind.py` — the judging sheet, held to what it must not do.

**The sheet is the instrument that failed on 2026-08-19**, not the
experiment.  Three cold agents worked batch 1 of `card:ungated-fixes.md`
and Henri judged blind; the sheet rendered each arm's raw markdown, so
*one line versus paragraphs* was the loudest thing on the page and
accuracy was invisible.  He judged what was visible, form and accuracy
came apart, and the arm he would have committed had a wrong verdict.
His words: *"this judgement was hard for me.  next time, if we repeat
this test, I'd like more visual indication and some aid in judgement."*

So what is checked here is the **discipline**, not the rendering: that
the page never leaks which arm is which, that a mechanical check says
nothing about a file that is not there, and that agreement is computed
rather than left to the reader.  A sheet that looked good and leaked the
mapping would be worse than the one it replaces.
"""

from __future__ import annotations

import importlib.util
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent

spec = importlib.util.spec_from_file_location("blind", ROOT / "tools" / "blind.py")
blind = importlib.util.module_from_spec(spec)
spec.loader.exec_module(blind)


ENTRY = """### F999. **[fixed]** a made-up entry

Some prose about it.

gate: {}

More prose.
"""


def arm(tmp_path, name, gate):
    d = tmp_path / name
    d.mkdir()
    (d / "fixme.md").write_text(ENTRY.format(gate))
    return d


def test_a_verdict_is_read_down_to_its_kind_and_its_citations():
    """Coarse on purpose: two arms that both said *nothing can* agree at
    the level a reader cares about, and an agreement measure that
    compared prose would call every entry split."""
    kind, _said, cites = blind.verdict_of(
        ENTRY.format("`test/test_atlas.py::test_every_module_has_a_lane` covers it."))
    assert kind == "gated"
    assert cites == ["test/test_atlas.py::test_every_module_has_a_lane"]

    kind, _said, cites = blind.verdict_of(ENTRY.format("none — nothing can, the C host owns it."))
    assert kind == "none — nothing can"
    assert cites == []

    kind, _said, _c = blind.verdict_of("### F1. no gate line at all\n\nprose\n")
    assert kind == "missing"


def test_nothing_is_claimed_about_a_file_that_is_not_there(tmp_path):
    """**The bug this caught in its own first run.**  A cited path that
    did not exist was still reported `pytest · collected` — a true
    statement about the *shape* of the name, printed as a fact about a
    file, on a sheet whose whole job is separating facts from
    impressions.
    """
    out = blind.check("test/test_nosuchfile.py::test_invented", "F999", ROOT)
    assert out["exists"] is False
    assert out["member"] is None, "no claim about a member of a missing file"
    assert out["mentions"] is None, "and none about what it mentions"
    assert out["collected"] is False


def test_a_real_citation_is_checked_against_the_real_tree():
    """Facts a reader can re-run, which is what makes them safe to show
    before the judging rather than after."""
    out = blind.check(
        "test/test_carry.py::test_every_field_is_carried_or_deliberately_fresh",
        "F161", ROOT)
    assert out["exists"] is True
    assert out["member"] is True
    assert out["collected"] is True
    assert out["mentions"] is False, "test_carry.py does not name F161"


def test_the_sheet_never_names_an_arm(tmp_path, monkeypatch):
    """**The one failure that would void the whole exercise.**  Wall
    clock and token cost leak the model as surely as a name does, so
    neither is gathered at all — a number that must not be shown is
    safest never collected.
    """
    monkeypatch.setattr(blind, "SHEETS", tmp_path / "blind")
    monkeypatch.setattr(blind, "ROOT", ROOT)
    arms = [arm(tmp_path, "haiku-run", "`test/test_carry.py` holds it."),
            arm(tmp_path, "sonnet-run", "none — nothing can."),
            arm(tmp_path, "opus-run", "`test/test_carry.py` holds it.")]
    monkeypatch.setattr(blind, "batch_of", lambda _card, _n: ["F999"])
    blind.main(["--batch", "9", *[str(a) for a in arms]])
    page = next((tmp_path / "blind").glob("*/sheet.html")).read_text()
    for leak in ("haiku", "sonnet", "opus", "gpt", "claude", str(tmp_path)):
        assert leak.lower() not in page.lower(), f"the sheet leaks `{leak}`"
    assert "A" in page and "B" in page and "C" in page


def test_agreement_is_computed_before_the_reader_arrives(tmp_path, monkeypatch):
    """Three of five were unanimous on batch 1; he only had to judge
    two, and nothing told him so."""
    monkeypatch.setattr(blind, "SHEETS", tmp_path / "blind")
    monkeypatch.setattr(blind, "batch_of", lambda _card, _n: ["F999"])
    same = [arm(tmp_path, f"a{i}", "`test/test_carry.py` holds it.") for i in range(3)]
    blind.main(["--batch", "9", *[str(a) for a in same]])
    page = next((tmp_path / "blind").glob("*/sheet.html")).read_text()
    assert ">0</b><span>contradiction<" in page
    assert ">1</b><span>agreed<" in page


def test_the_batch_comes_from_the_card_and_is_not_retyped(tmp_path):
    """One home for the schedule.  A batch typed into a second place is
    a batch that drifts the first time the card is re-planned."""
    card = ROOT / "board" / "ungated-fixes.md"
    if not card.exists():
        card = ROOT / "board" / "done" / "ungated-fixes.md"
    assert blind.batch_of(card, 2) == ["F139", "F133", "F132", "F128", "F126"]
    with pytest.raises(SystemExit):
        blind.batch_of(card, 99)


def test_an_arm_that_produced_nothing_is_a_result_and_not_a_crash(tmp_path, monkeypatch, capsys):
    """A run that died is one of the things a comparison exists to
    notice.  A traceback here would lose the other two arms' work with
    it."""
    monkeypatch.setattr(blind, "SHEETS", tmp_path / "blind")
    monkeypatch.setattr(blind, "batch_of", lambda _card, _n: ["F999"])
    good = [arm(tmp_path, f"a{i}", "`test/test_carry.py` holds it.") for i in (1, 2)]
    dead = tmp_path / "dead"
    dead.mkdir()
    blind.main(["--batch", "9", str(good[0]), str(good[1]), str(dead)])
    page = next((tmp_path / "blind").glob("*/sheet.html")).read_text()
    assert "no gate: line" in page
    assert "contradiction" in page, \
        "two arms agreeing and one silent is not agreement"
    assert "wrote no fixme.md at all" in capsys.readouterr().out, \
        "and the run says so"


def test_the_two_kinds_of_disagreement_are_not_the_same_work():
    """Henri, 2026-08-19: *"they're not in agreement and I need to check
    the Fix and consider whether the record holds."*  True half the
    time — a **contradiction** has a wrong answer in it, and two arms
    naming **different gates** may both be right (F155 in this tree is
    cited by two).  Lumping them made a five-minute check look like the
    other kind.
    """
    assert blind._state({("gated", ("a.py",))}) == "agreed"
    assert blind._state({("gated", ("a.py",)), ("gated", ("b.py",))}) \
        == "different gate"
    assert blind._state({("gated", ("a.py",)), ("none — nothing can", ())}) \
        == "contradiction"


def test_three_silent_arms_are_never_reported_as_agreement():
    """**The defect this tool exists to prevent, found in itself.**  Run
    against three checkouts whose files had been cleaned up underneath
    it, every entry came back `missing` from every arm, the states all
    matched, and the sheet said *5 agreed* about a comparison that had
    not happened.
    """
    assert blind._state({("missing", ())}) == "no verdicts"
    assert blind._state({("missing", ()), ("gated", ("a.py",))}) == "contradiction"
