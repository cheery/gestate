"""`deriving Ord` and `fix` at a product — roadmap 2.2 and 2.3.

Two gaps that had nothing to do with each other except that both kept
ordinary programs unwritable: a set could not hold a user data type, and a
fixed point could compute only one relation.
"""

from __future__ import annotations

import re

import pytest

from gestate.pipeline import evaluate

#: `Cons` is not always tag 1 — user constructors are numbered first, so a
#: program declaring three of them pushes `Nil`/`Cons` to 3/4.  Read the
#: elements by matching whatever cons cell the result actually uses.
def _tags(source: str) -> list[str]:
    out = evaluate(source)
    m = re.search(r"Pack\{(\d+),2\}", out)
    if m is None:
        return []
    return re.findall(rf"Pack\{{{m.group(1)},2\}} Pack\{{(\d+),0\}}", out)


COLOUR = "C := R | G | B deriving (Eq, Ord)\n\n"


def _members(set_expr: str) -> list[str]:
    """Which of R, G, B are in `set_expr`, by asking the program.

    A printed result is not a value: a duplicate that has not been forced
    yet still shows as a cons cell inside an unevaluated union thunk.
    Membership forces to a `Bool` and uses only surface syntax.
    """
    probes = [f'(show (holds (for (x in ({set_expr} : Set C)) (guard (x == {c})))))'
              for c in "RGB"]
    body = probes[0]
    for probe in probes[1:]:
        body = f"(append {body} {probe})"
    out = evaluate(COLOUR + f"main : String\nmain = {body}\n")
    flags, i = [], 0
    while i < len(out):
        if out.startswith("True", i):
            flags.append(True); i += 4
        else:
            flags.append(False); i += 5
    return [c for c, f in zip("RGB", flags) if f]


# ── 2.3 — deriving Ord, and sets of user data types ─────────────────────────


def test_deriving_ord_orders_by_constructor_position():
    """Haskell's rule: earlier constructors are less.

    This was thought to need a primitive, because a constructor's tag
    cannot be named in the surface language.  It does not: enumerating both
    scrutinees puts the answer in the *order the alternatives are written*,
    which is the same information.
    """
    src = COLOUR + "main : String\nmain = %s\n"
    def lt(a, b):
        return evaluate(src % f"show ({a} < {b})")
    assert [lt(a, b) for a in "RGB" for b in "RGB"] == [
        "False", "True",  "True",     # R < R, R < G, R < B
        "False", "False", "True",     # G < …
        "False", "False", "False",    # B < …
    ]


def test_the_other_three_comparisons_follow():
    src = COLOUR + "main : String\nmain = %s\n"
    assert evaluate(src % "show (G <= G)") == "True"
    assert evaluate(src % "show (B > R)") == "True"
    assert evaluate(src % "show (R >= G)") == "False"


def test_deriving_ord_on_a_constructor_with_fields():
    src = ("P := P Int Int deriving (Eq, Ord)\n\n"
           "main : String\nmain = %s\n")
    assert evaluate(src % "show (P 1 2 < P 1 3)") == "True"   # second field
    assert evaluate(src % "show (P 1 9 < P 2 0)") == "True"   # first decides
    assert evaluate(src % "show (P 2 0 < P 1 9)") == "False"


def test_a_user_data_type_can_be_a_set_element():
    """The point of 2.3, and it needed two fixes, not one.

    `deriving Ord` is the surface half.  The other was that `is_eqtype`
    never consulted the constructor table for a *parameterless* data type —
    a bare `TCon` short-circuited before the ADT case — so `C := R | G | B`
    was reported "not an eqtype" however simple it was.  `Maybe Bool`
    escaped only by being a type *application*.
    """
    assert _tags(COLOUR + "main : Set C\nmain = {G, R, B, R}\n") == ["0", "1", "2"]


def test_a_set_of_a_user_type_dedups():
    assert _members("{B, R, B}") == ["R", "B"]


def test_a_set_of_a_user_type_joins():
    assert _members("{B} \\/ {R}") == ["R", "B"]


def test_a_comprehension_guard_over_a_user_type():
    assert _members("{x | x in {R, G, B}, x < B}") == ["R", "G"]


def test_a_fixed_point_over_a_set_of_a_user_type():
    src = ("f : Box (Set C) -> Set C\n"
           "f (Box e) = fix r => e \\/ {x | x in r}\n\n")
    probes = [f'(show (holds (for (x in (f (Box {{G, R}}) : Set C)) (guard (x == {c})))))'
              for c in "RGB"]
    body = probes[0]
    for probe in probes[1:]:
        body = f"(append {body} {probe})"
    out = evaluate(COLOUR + src + f"main : String\nmain = {body}\n")
    assert out == "TrueTrueFalse", out


# ── 2.2 — `fix` at a semilattice other than `Set a` ─────────────────────────


def _pair(source: str) -> tuple[list[str], list[str]]:
    """The two components of a `(Set, Set)` result."""
    left, right = evaluate(source).split(", Pack", 1)
    each = [left, "Pack" + right]
    return tuple(re.findall(r"Pack\{1,2\} (\d+)", part) for part in each)


def test_fix_at_a_product_of_semilattices():
    """The standard Datalog idiom: two relations in one fixed point.

    `is_semilattice`/`is_fixtype` already accepted `L × M`; only the
    inferencer's `EFix` rule pinned the type to `Set a`, answering
    `subgrammar.py`'s question too early and answering it wrong.
    """
    src = ("f : Box (Set (Cyclic 8)) -> (Set (Cyclic 8), Set (Cyclic 8))\n"
           "f (Box e) = fix r => (e \\/ {x + 1 | x in fstM r, x < 3},"
           " {x + 1 | x in fstM r})\n\n"
           "main : (Set (Cyclic 8), Set (Cyclic 8))\nmain = f (Box {0})\n")
    left, right = _pair(src)
    assert left == ["0", "1", "2", "3"]
    assert right == ["1", "2", "3", "4"], "the second relation tracks the first"


def test_a_product_fixpoint_needs_a_monotone_projection():
    """`fst` takes its argument discretely, so it cannot see a `fix` binder.

    A projection *is* monotone — a product is ordered componentwise — so
    the prelude supplies `fstM`/`sndM` at the arrow that says so.  Using the
    discrete one is a monotone-discipline error, not a type error, and the
    message should say which.
    """
    from gestate.pipeline import MonotoneError

    src = ("f : Box (Set (Cyclic 4)) -> (Set (Cyclic 4), Set (Cyclic 4))\n"
           "f (Box e) = fix r => (e \\/ {x + 1 | x in fst r}, fst r)\n\n"
           "main : (Set (Cyclic 4), Set (Cyclic 4))\nmain = f (Box {0})\n")
    with pytest.raises(MonotoneError, match="monotone variable"):
        evaluate(src)


def test_fix_at_a_plain_set_is_unchanged():
    assert re.findall(r"Pack\{1,2\} (\d+)", evaluate(
        "main : Set (Cyclic 4)\nmain = fix r => {0} \\/ {x + 1 | x in r}\n"
    )) == ["0", "1", "2", "3"]


def test_fix_at_a_non_semilattice_is_still_rejected():
    """Relaxing the inferencer must not relax the subgrammar."""
    from gestate.pipeline import SubgrammarError

    with pytest.raises((SubgrammarError, Exception)):
        evaluate("main : Int\nmain = fix r => r + 1\n")
