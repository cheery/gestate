"""Which supercombinators ϕ/δ transforms (`fixme.md` F9).

`spec/data.md` §0 scopes the pass to Datafun-typed subterms and exempts no
*definition*.  `main` was exempt anyway, so a `fix` in `main` ran the naïve
loop while the same `fix` one definition over ran the seminaïve one: two
code paths for one construct, and neither ⊥-propagation nor change
minimization reached the entry point.

Everything the user wrote is transformed now.  The compiler's own output —
generated helpers, and the `__`-named dictionaries and instance methods
elaboration emits — is not: it is already in the target language.
"""

from __future__ import annotations

from gestate.gmachine import step
from gestate.pipeline import compile, evaluate
from gestate.seminaive import _is_user_sc


def _steps(source: str) -> int:
    s = compile(source)
    n = 0
    while not s.isFinal:
        step(s)
        n += 1
    return n


QUERY = "fix Box (r => {1} \\/ (for (x in r) {x + 1}))"

IN_MAIN = f"main : Set (Cyclic 8)\nmain = {QUERY}\n"
IN_AN_SC = (f"reach : Set (Cyclic 8)\nreach = {QUERY}\n\n"
            f"main : Set (Cyclic 8)\nmain = reach\n")


# ── `main` is an ordinary supercombinator ────────────────────────────────────


def test_a_query_costs_the_same_wherever_it_is_written():
    """The point of the item: a definition boundary is not a strategy.

    `main` ran ~7% more G-machine steps than the identical query one
    definition over, because only the latter was seminaïve.  What is left
    between them is the indirection through `reach`.
    """
    assert abs(_steps(IN_MAIN) - _steps(IN_AN_SC)) < 32


def test_both_spellings_compute_the_same_set():
    assert evaluate(IN_MAIN) == evaluate(IN_AN_SC)


def test_main_gets_a_phi_and_needs_no_delta():
    """It holds the `fix`, so ϕ has work to do; nothing calls it, so δ
    has none (`fixme.md` F7)."""
    globals_ = compile(IN_MAIN).globals

    assert "main_phi" in globals_
    assert "main_delta" not in globals_
    # …and it keeps its own name, since the machine starts at `main`.
    assert "main" in globals_


def test_generated_code_is_left_alone():
    """Dictionaries and instance methods are the compiler's own output."""
    globals_ = compile("main : Set (Cyclic 8)\nmain = {1, 2}\n").globals

    # Lifted lambdas are keyed by integer id; only names can be checked.
    generated = [n for n in globals_
                 if isinstance(n, str) and n.startswith("__")]
    assert generated  # the program does use `Num (Cyclic 8)`
    assert not [n for n in generated if n.endswith(("_phi", "_delta"))]


# ── Renaming follows the set actually transformed ────────────────────────────


def test_a_user_name_starting_with_an_underscore_is_ordinary():
    """It was skipped as if it were generated, while every reference to it
    was still renamed — `unknown global '_base_phi'`."""
    assert evaluate("_base : Set (Cyclic 4)\n_base = {1}\n\n"
                    "main : Set (Cyclic 4)\n"
                    "main = for (x in _base) {x}\n").count(",2}") == 1


def test_a_primitive_the_transform_never_generated_is_not_renamed():
    """`chr` is a machine primitive and was in none of the exclusion
    lists, so ϕ renamed it to `chr_phi`, which does not exist.  Only
    `main` escaped it, by not being transformed."""
    assert evaluate("f : Set Char\nf = {chr 98, chr 97}\n\n"
                    "main : Set Char\nmain = f\n").count(",2}") == 2


def test_a_generated_helper_is_not_a_user_name_at_any_type():
    """`fixme.md` F8's third half: the exclusion is by *prefix*.

    It used to be a hardcoded list, and every name on it said
    `Set_Int` — so the moment a program used a set of anything else,
    `union_Set_Cyclic_8` looked like a user definition and ϕ renamed it
    to `union_Set_Cyclic_8_phi`, which does not exist.

    Narrowed back to that list, all 429 tests of the batch's set stayed
    green (`card:ungated-fixes.md`, batch 12, 2026-09-03).  Weakest
    point, and it is why this is a unit test: `transform` passes the set
    it is generating pairs for, so `_is_user_sc` is only the fallback for
    a direct call to `phi`/`delta` — 5 tests in the set reach it, and
    none of them names a helper at a type other than `Set Int`.
    """
    for name in ("eq_Set_Int", "union_Set_Cyclic_8", "bottom_Set_Char",
                 "join_Set_Float", "diff_Set_Cyclic_4", "dummy_Cyclic_8",
                 "fix_Set_Cyclic_8", "fixLoop_Set_Char", "for_Set_Float",
                 "semifix_Set_Cyclic_4", "semifixL_Set_Cyclic_4",
                 "subset_Set_Char"):
        assert not _is_user_sc(name), name
    assert _is_user_sc("path")     # and an ordinary definition still is


# ── Each half is generated only where it is needed (F7) ──────────────────────

MONOTONE_CALL = """g : Set (Cyclic 8) ~> Set (Cyclic 8)
g s = s

f : Set (Cyclic 8) ~> Set (Cyclic 8)
f s = g s

main : Set (Cyclic 8)
main = fix Box (r => {1} \\/ f r)
"""


def _halves(source: str) -> set[str]:
    return {n for n in compile(source).globals
            if isinstance(n, str) and n.endswith(("_phi", "_delta"))}


def test_a_supercombinator_with_no_datafun_in_it_is_left_alone():
    """The prelude's list functions have no set anywhere near them, and
    were doubled anyway — every SC in the program used to get both."""
    halves = _halves(IN_MAIN)

    assert halves == {"main_phi"}


def test_a_function_called_under_a_box_gets_a_derivative():
    """δ is a reachability question, not a syntactic one.

    `g s = s` mentions no semilattice, so ϕ would rebuild it unchanged
    and it gets no `_phi`.  It is still applied to the accumulator inside
    `fix [r ⇒ …]`, so `δ` needs `g_delta` — gating on "does the body
    mention a set" would have missed it.
    """
    halves = _halves(MONOTONE_CALL)

    assert "g_delta" in halves
    assert "g_phi" not in halves


def test_the_demand_for_a_derivative_is_transitive():
    """`f` calls `g`, and only `f` is under the box."""
    assert _halves(MONOTONE_CALL) == {"main_phi", "f_delta", "g_delta"}


def test_a_body_with_a_for_gets_both_halves():
    halves = _halves("""bump : Set (Cyclic 8) ~> Set (Cyclic 8)
bump s = for (x in s) {x + 1}

main : Set (Cyclic 8)
main = fix Box (r => {1} \\/ bump r)
""")

    assert halves == {"main_phi", "bump_phi", "bump_delta"}


def test_the_answers_do_not_change():
    assert evaluate(MONOTONE_CALL).count(",2}") == 1


# ── ϕ reaches inside a signal ────────────────────────────────────────────────


SIGNAL_FIX = """mkSig : ExL a -> ExL (Sig a)
mkSig d = (x => x ::: mkSig d) |> d

c : Chan (Set (Cyclic 8))
c = chan

main : Sig (Set (Cyclic 8))
main = (fix Box (r => {1} \\/ r)) ::: mkSig (wait c)
"""


def test_a_fix_inside_a_signal_is_seminaive():
    """`spec/data.md` §0: "a `fix` buried inside a signal's per-tick body
    gets seminaïved in place".

    It did not.  ϕ had no rule for the Rizzo formers and returned them
    *unrecursed*, so the `fix` under `:::` stayed an `EFix` and came out
    as the naïve `fix_Set_Cyclic_8`.  ϕ is structural now: a construct it
    has no rule for is rebuilt from its transformed children.
    """
    code = str(compile(SIGNAL_FIX).globals["main_phi"])

    assert "semifix_Set_Cyclic_8" in code
    assert "name='fix_Set" not in code
