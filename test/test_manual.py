"""`doc/manual.md` tells the truth — checked, not asserted.

Every code snippet in the manual was run before it was written down.  This
file keeps them running, because a manual that has drifted teaches things
that are worse than nothing.

**§9 "Things that will surprise you" is the part that rots**, and it rots in
an unusual direction: each entry describes a *limitation*, so fixing the
limitation makes the manual wrong.  Those tests are written to fail loudly
when that happens, with a message saying to update the manual rather than
to restore the bug.
"""

from __future__ import annotations

from pathlib import Path

import pytest

import gestate.syntax as S
from gestate.midi import perform
from gestate.pipeline import compile, evaluate

MANUAL = Path(__file__).resolve().parent.parent / "doc" / "manual.md"
BPM = "\nbpm : Int\nbpm = 120\n"

MKSIG = ("mkSig : ExL a -> ExL (Sig a)\n"
         "mkSig = gfix q => (d => delay (q2 x => x ::: q2 d) <*> q <@> d)\n\n")


def test_the_manual_exists_and_covers_its_sections():
    text = MANUAL.read_text()
    for heading in ("## 1. What this is", "## 4. Types",
                    "## 5. Datafun", "## 6. FRP", "## 7. Music",
                    "## 9. Things that will surprise you"):
        assert heading in text, f"missing section: {heading}"


# ── §4: a signature is a promise ────────────────────────────────────────────


def test_a_signature_variable_is_the_callers_choice():
    from gestate.unify import UnifyError

    with pytest.raises(UnifyError):
        evaluate("f : a -> Int\nf x = x + 1\n\nmain : Int\nmain = f 1\n")
    # …and the same body without the signature is fine.
    assert evaluate("f x = x + 1\n\nmain : Int\nmain = f 1\n") == "2"


# ── §5: Datafun ─────────────────────────────────────────────────────────────


def test_for_eliminates_into_a_semilattice_only():
    from gestate.pipeline import SubgrammarError

    with pytest.raises(SubgrammarError, match="semilattice"):
        evaluate("main : Int\nmain = for (x in {1,2}) 5\n")


def test_fix_needs_a_fixtype():
    from gestate.pipeline import SubgrammarError

    with pytest.raises(SubgrammarError, match="fixtype"):
        evaluate("main : Set Int\nmain = fix r => {1} \\/ r\n")
    # `Cyclic n` is finite, so the same query terminates there.
    assert evaluate("main : Set (Cyclic 4)\n"
                    "main = fix r => {0} \\/ {x + 1 | x in r, x < 3}\n"
                    ).count("Pack{1,2}") == 4


def test_a_product_fixpoint_needs_the_monotone_projection():
    from gestate.pipeline import MonotoneError

    src = ("f : Box (Set (Cyclic 8)) -> (Set (Cyclic 8), Set (Cyclic 8))\n"
           "f (Box e) = fix r => (e \\/ {x + 1 | x in %s r, x < 4},"
           " {x + 1 | x in %s r})\n\n"
           "main : (Set (Cyclic 8), Set (Cyclic 8))\nmain = f (Box {0})\n")
    evaluate(src % ("fstM", "fstM"))
    with pytest.raises(MonotoneError):
        evaluate(src % ("fst", "fst"))


def test_a_polymorphic_set_signature_is_rejected():
    from gestate.pipeline import MonomorphizationError

    with pytest.raises(MonomorphizationError):
        evaluate("f : {a} ~> {a}\nf s = for (x in s) {x}\n\n"
                 "main : {Int}\nmain = f {1} \\/ f {2}\n")


# ── §6: the two halves do not interfere ─────────────────────────────────────


def test_a_signal_cannot_be_a_set_element():
    src = (MKSIG + "c : Chan Int\nc = chan\n\n"
           "main : Set (Sig Int)\nmain = {0 ::: mkSig (wait c)}\n")
    with pytest.raises(Exception):
        compile(src)


def test_the_manuals_map_definition_compiles():
    assert compile(
        MKSIG
        + "map : (a -> b) -> Sig a -> Sig b\n"
        "map = gfix q => (f s => f (head s) ::: (delay (q2 => q2 f) <*> q <@> tail s))\n\n"
        "c : Chan Int\nc = chan\n\n"
        "main : Sig Int\nmain = map (n => n * 2) (0 ::: mkSig (wait c))\n")


# ── §7: music ───────────────────────────────────────────────────────────────


def test_a_score_with_an_unassigned_note_does_not_type():
    """Performability is a typing property, as §7 claims."""
    with pytest.raises(Exception):
        perform("score : [: Void :]\nscore = '60\n" + BPM)


def test_at_moves_the_extent_not_the_duration():
    """§7's early-fill example, which is the whole point of `at`."""
    _bpm, events = perform(
        "score : [: Void :]\n"
        "score = ('60 ++ at (0 - 48) ('62) ++ '64) >>= prog 0\n" + BPM)
    assert [e[0] for e in events] == [0, 96 - 48, 2 * 96]


def test_scaling_binds_tighter_than_sequencing():
    """§9: `a ++ b |* 2` scales `b` alone; a phrase needs parentheses."""
    def spans(expr):
        _bpm, events = perform(f"score : [: Void :]\nscore = ({expr}) "
                               ">>= prog 0\n" + BPM)
        return [(e[0], e[1]) for e in events]

    assert spans("'60 ++ '62 |* 2") == [(0, 96), (96, 288)], _UPDATE
    assert spans("('60 ++ '62) |* 2") == [(0, 192), (192, 384)], _UPDATE


# ── §9: the entries that rot when a bug is fixed ────────────────────────────

_UPDATE = ("doc/manual.md §9 says this does not work.  If you have just made "
           "it work, delete the entry — do not restore the limitation.")


def test_manual_s9_nested_projection_needs_parentheses():
    src = "Q := Q (Int, Int)\n\nmain : Int\nmain = %s\n"
    with pytest.raises(Exception):
        evaluate(src % "(Q (5,6)).0.1")          # `0.1` lexes as a float
    assert evaluate(src % "((Q (5,6)).0).1") == "6", _UPDATE


def test_manual_s3_a_prefix_operator_may_stand_as_an_argument():
    """`at 4 '60` — no parentheses.  This used to be a §9 entry.

    `'` and `|<` are prefix and never infix, so a symbol from that set
    standing where an argument may stand cannot be an infix operator.  It
    reads as `at 4 ('60)`, which is the only sensible thing it could mean.
    """
    both = ["score : [: Void :]\nscore = (at 4 ('60)) >>= prog 0\n" + BPM,
            "score : [: Void :]\nscore = at 4 '60 >>= prog 0\n" + BPM]
    assert perform(both[0]) == perform(both[1])


def test_manual_s9_the_scaling_factor_does_not_swallow_what_follows():
    """The factor takes arithmetic and stops (§9).

    `|*` is `infixl 6`, so its right operand still absorbs `+` (7) and `*`
    (8) but stops before `++` (4) — the factor never reaches past itself.
    """
    import gestate.syntax as S

    def tree(expr):
        m = S.parse(f"main = {expr}\n")
        d = [i for i in m.items if type(i).__name__ == "VSCDecl"][0]
        def sh(v):
            n = type(v).__name__
            if n == "VInfix":  return f"({sh(v.left)} {v.op} {sh(v.right)})"
            if n == "VNum":    return str(v.value)
            return getattr(v, "value", n)
        return sh(d.equations[0].body)

    assert tree("a ++ b |* 2 ++ c") == "((a ++ (b |* 2)) ++ c)", _UPDATE
    assert tree("a |* 2 + 1") == "(a |* (2 + 1))", _UPDATE
    assert tree("a |/ 2 ++ b |/ 2") == "((a |/ 2) ++ (b |/ 2))", _UPDATE


def test_manual_s9_a_refutable_lambda_pattern_is_rejected():
    from gestate.desugar import DesugarError

    with pytest.raises(DesugarError, match="irrefutable"):
        evaluate("main : Int\nmain = sum (map ((Just x) => x) [Just 1])\n")


def test_manual_s9_there_is_no_if_and_no_where():
    with pytest.raises(Exception):
        evaluate("main : Int\nmain = if True then 1 else 2\n")
    with pytest.raises(Exception):
        S.parse("main = x\n  where x = 1\n")


def test_manual_s9_projection_needs_a_known_base_type():
    from gestate.infer import InferError

    with pytest.raises(InferError, match="not known here"):
        evaluate("f p = p.0\n\nmain : Int\nmain = f (1, 2)\n")


# ── §4 Implicit parameters ───────────────────────────────────────────────────

PPQ = "implicit ppq : Int\n\n"


def test_manual_s4_the_worked_implicit_example():
    assert evaluate(PPQ + "quarter : Int\nquarter (using ppq) = ppq\n\n"
                    "bar : Int\nbar = quarter * 4\n\n"
                    "main : Int\nmain = given ppq = 96 in bar\n") == "384"


def test_manual_s4_a_requirement_travels_up_the_call_graph():
    # `bar` never writes `ppq`, `report` does not even call something that
    # does directly, and neither signature mentions it.  Both still get it.
    assert evaluate(PPQ + "quarter : Int\nquarter (using ppq) = ppq\n\n"
                    "bar : Int\nbar = quarter * 4\n\n"
                    "report : Int\nreport = bar + 1\n\n"
                    "main : Int\nmain = given ppq = 96 in report\n") == "385"


def test_manual_s4_given_is_where_the_travelling_stops():
    assert evaluate("implicit n : Int\n\ndouble : Int\ndouble (using n) = n * 2\n\n"
                    "inner : Int\ninner = given n = 3 in double\n\n"
                    "main : Int\nmain = inner + 1\n") == "7"


def test_manual_s4_given_binds_several_three_ways():
    area = ("implicit w : Int\nimplicit h : Int\n\n"
            "area : Int\narea (using w h) = w * h\n\n")
    for binder in ("given w = 3, h = 4 in area",
                   "given w = 3; h = 4 in area",
                   "given\n    w = 3\n    h = 4\n  in area"):
        assert evaluate(f"{area}main : Int\nmain = {binder}\n") == "12"


def test_manual_s4_implicits_may_precede_ordinary_parameters():
    # Only the ordinary parameter is in the signature.
    assert evaluate("implicit w : Int\nimplicit h : Int\n\n"
                    "scale : Int -> Int\nscale (using w h) k = w * h * k\n\n"
                    "main : Int\nmain = given w = 3, h = 4 in scale 2\n") == "24"


def test_manual_s4_an_inner_given_shadows_an_outer_one():
    assert evaluate("implicit n : Int\n\ndouble : Int\ndouble (using n) = n * 2\n\n"
                    "main : Int\nmain = given n = 3 in (given n = 10 in double)\n") == "20"


def test_manual_s4_an_unfilled_implicit_is_a_compile_error():
    from gestate.desugar import DesugarError

    with pytest.raises(DesugarError, match="unfilled implicit") as exc:
        evaluate(PPQ + "quarter : Int\nquarter (using ppq) = ppq\n\n"
                 "main : Int\nmain = quarter\n")
    # The manual quotes this message; it names the culprit and the cure.
    assert "`ppq` (required by `quarter`) reaches `main`" in str(exc.value)
    assert "given ppq = " in str(exc.value)


def test_manual_s4_the_symmetric_mistake_is_caught_too():
    from gestate.desugar import DesugarError

    with pytest.raises(DesugarError, match="undeclared implicit"):
        evaluate("quarter : Int\nquarter (using ppq) = ppq\n\n"
                 "main : Int\nmain = given ppq = 96 in quarter\n")


def test_manual_s9_an_implicit_parameter_is_invisible_in_the_signature():
    # §9 says the signature stays silent.  If that changes, the entry is
    # wrong — rewrite it, do not restore the old arrow-counting.
    assert evaluate(PPQ + "f : Int\nf (using ppq) = ppq\n\n"
                    "g : Int\ng = f + 1\n\n"
                    "main : Int\nmain = given ppq = 1 in g\n") == "2", _UPDATE
