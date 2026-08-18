"""The sweep, held to itself — `board/done/error-messages.md`.

**The last sweep left no receipt, and that is the defect this file is
for.**  `journal.md` Part I item 13 records an "every error message"
pass that was in fact scoped to type errors; nothing wrote down what it
had decided or what it had not looked at, so a checker written
afterwards could raise five messages with no position at all and nobody
knew until Henri broke a type on purpose a year later (`fixme.md`
F152).

So the deliverable of this card is not "the messages are fixed" — it is
the list, `doc/complaints.md`, generated from verdicts written beside
the raises themselves.  These tests are what make the list true:

* every complaint has a verdict, so a new error class cannot arrive
  unexamined;
* every `author` complaint says where, or says why it does not, or
  names the defect that owes it a place;
* the page on disk is not behind the source it is derived from.

The last one is the same class of check as `doc/ref/` and the atlas —
a generated file behind its source — and belongs with them in
`tools/suite.py`'s gates for the same reason: a session breaks it by
editing the tree, and it costs a fraction of a second to find out.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from gestate.complaints import (
    WHO, Complaint, read, render, stale, unexplained, unowned,
    unverdicted, owing_a_place, _place_in, _verdict,
)

ROOT = Path(__file__).resolve().parent.parent


# ── The gate ────────────────────────────────────────────────────────────────


@pytest.fixture(scope="module")
def complaints():
    return read(ROOT)


def test_every_complaint_has_a_verdict(complaints):
    """**A new error class arrives unexamined, and this is what says so.**

    The verdict goes beside the raise — on the site, the function, the
    file or the error class — and there is no default: a `raise` this
    file cannot account for is one nobody has decided about.
    """
    missing = unverdicted(complaints)
    assert not missing, "no verdict for:\n" + "\n".join(
        f"  {c.file}:{c.line}  {c.error}  {c.message[:70]}" for c in missing)


def test_every_author_complaint_says_where(complaints):
    """F152, stated as a rule rather than as one fixed message.

    A complaint a person provokes from their own file is drawn under
    the line they wrote it on, and the line is read out of the message
    text — so a message with no position in it lands in the status bar
    instead, which is where a `Sig Floa` went for a year.
    """
    owed = owing_a_place(complaints)
    assert not owed, (
        "an `author` complaint must say where, or say `nowhere` and why, "
        "or say `unplaced` and which defect owes it:\n" + "\n".join(
            f"  {c.file}:{c.line}  {c.message[:70]}" for c in owed))


def test_a_deliberate_silence_gives_its_reason(complaints):
    """`nowhere` without a reason is the oversight it claims not to be."""
    quiet = unexplained(complaints)
    assert not quiet, "\n".join(f"  {c.file}:{c.line}" for c in quiet)


def test_a_debt_names_the_defect_that_owns_it(complaints):
    """`unplaced` is the honest third state and the softest of the three.

    Without an F-number it becomes the place everything drifts to,
    which is the failure mode of every "known issues" list ever kept.
    """
    loose = unowned(complaints)
    assert not loose, "\n".join(f"  {c.file}:{c.line}  {c.why}" for c in loose)


def test_the_page_is_not_behind_the_source():
    """The same check `doc/ref/` gets, for the same reason: a generated
    file nothing compares is a generated file that drifts."""
    assert not stale(ROOT), (
        "doc/complaints.md is behind gestate/ — "
        "run `python -m gestate.complaints`")


# ── That the reading is a reading, and not a wish ───────────────────────────


def test_the_place_a_message_carries_is_read_the_way_the_editor_reads_it():
    """**Both spellings, because the tree really has two.**

    `(at 12:8)` counts from the top of the *assembled* program and is
    re-based by `audiospans.in_source`; `at line 4:0` counts from the
    top of the author's own file and is left alone, which is what
    `internals.py` and `audiovoices.py` need — they read the source
    before anything is prepended to it.  Both are read by
    `session._line_of`, and a third spelling would be a position that
    exists and is never used.
    """
    assert _place_in('f"broken (at {line}:{col})"')
    assert _place_in('f"broken (at line {n}:0)"')
    assert not _place_in('f"broken on line {n}"')
    assert not _place_in('f"{path}: broken"')


def test_a_placer_is_recognised_by_name():
    """The helpers whose whole job is to write the position out."""
    assert _place_in("f'Unknown type constructor: {name}' + _where(texpr)")
    assert _place_in("f'Unbound variable: {expr.name!r}{at(expr)}'")
    assert _place_in("f'mismatch{_span_str(a)}'")


def test_a_wrapped_complaint_carries_what_it_wrapped():
    """`raise FitsError(str(exc))` is a rename, not a message.

    Whatever place the complaint it wraps had, this one has — reporting
    it as placeless would be false, and this is the one loophole the
    gate leaves open on purpose (the wrapped complaint is a row of its
    own further up the same list).
    """
    assert _place_in("str(exc)") == "carried from `exc`"
    assert _place_in("'\\n'.join(exhaust_errors)")
    #: A *node* being shown is not a complaint being carried.
    assert not _place_in("f'compileC: unknown expr {e!r}'")


def test_a_verdict_is_read_off_the_marker():
    got = _verdict("#: complaint  author — a type as written")
    assert (got.who, got.nowhere, got.unplaced) == ("author", False, False)
    got = _verdict("#: complaint  author, nowhere — an absence has no line")
    assert got.nowhere and got.why == "an absence has no line"
    got = _verdict("#: complaint  author, unplaced — fixme.md F159")
    assert got.unplaced and "F159" in got.why
    assert _verdict("#: an ordinary comment") is None


def test_the_vocabulary_is_closed(complaints):
    """Four words.  A fifth would be one nobody had agreed to."""
    assert {c.who for c in complaints} <= set(WHO)


# ── What the sweep found, kept in sight ─────────────────────────────────────


def _at(complaints, name: str, needle: str) -> Complaint:
    hits = [c for c in complaints if c.file == name and needle in c.message]
    assert len(hits) == 1, f"{len(hits)} complaints match {needle!r}"
    return hits[0]


def test_the_two_files_that_count_in_the_authors_coordinates(complaints):
    """`internals.py` and `audiovoices.py` read the author's own text.

    Every other complaint counts from the top of the assembled program
    and is translated on the way out; these two are already in the
    author's file, so they use the `at line N:C` spelling that
    `in_source` leaves alone.  Both said `line N:` before this card,
    which is a number nothing reads.
    """
    assert _at(complaints, "internals.py", "reference").placed
    assert _at(complaints, "audiovoices.py", "a bank needs at least one").placed


def test_the_evaluators_runtime_complaints_are_owned_by_a_defect(complaints):
    """Dividing by zero is the author's mistake and lands nowhere.

    It could carry a span the way `Hole` does — that is `fixme.md`
    F159, and the row is here so that closing F159 is visibly a change
    to this list rather than an edit nobody sees.
    """
    zero = _at(complaints, "gmachine.py", "DivInt: division by zero")
    assert zero.who == "author" and zero.unplaced and "F159" in zero.why


def test_a_hole_is_the_one_runtime_complaint_that_says_where(complaints):
    hole = _at(complaints, "gmachine.py", "a hole (`_`)")
    assert hole.who == "author" and hole.placed
