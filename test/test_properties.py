"""Property tests — `fixme.md` F29.

Every other test in this suite is an example, and most were written against
a bug already known.  That leaves a characteristic blind spot, and this
session hit it twice: `for (x in a, y in b)` had never worked because
nothing exercised two generators, and a comprehension guard that was
*false* under a `fix` crashed because no example ever took that branch.
Both are cases a generator would have produced immediately.

Generation is seeded `random` rather than Hypothesis: the project has no
third-party dependencies, the input spaces here are small enough that a
failure is already near-minimal, and a fixed seed is what makes a failure
reproducible.  Shrinking is what Hypothesis would add; when a property
starts failing on inputs too big to read, that is when it earns the
dependency.

**Reading a set back** goes through membership rather than the printed
result.  `evaluate` prints unevaluated thunks — a `Cyclic 8` element can
come out as `((<global arity=2> 8) 2)`, an unforced `mod 8 2` — so the
printed form is not a value.  Probing `holds (for (x in S) guard (x == k))`
for each `k` forces to a `Bool`, uses only surface syntax, and determines
the set completely at a finite element type.
"""

from __future__ import annotations

import random

import pytest

from gestate.pipeline import evaluate

#: Element type for most properties.  Finite, so `fix` terminates, and
#: small because reading a set back costs one probe per possible element.
MOD = 6

#: How many random cases per property.  Each case is a full compile —
#: prelude included — so this trades coverage against a suite that stays
#: runnable.  Raise it when hunting something specific.
CASES = 6

#: Probes per generated program.  Each is one `append` deeper than the
#: last and the compiler recurses over that spine, so ~180 of them exceed
#: Python's stack while compiling.  Compile cost is also superlinear in
#: program size, so small batches beat large ones: measured over this file,
#: 12 probes per program runs in 20s against 28s at 60.
_MAX_PROBES = 12


def _members_many(exprs: list[str], preamble: str = "",
                  mod: int = MOD) -> list[set[int]]:
    """Membership of every expression in `exprs`, in **one** compile.

    Batched because a case costs a whole compile, prelude included.  One
    program per property instead of one per case is what keeps these
    affordable enough to keep and to grow.
    """
    ty = f"Cyclic {mod}"
    # One probe string is one `append` deeper than the last, and the
    # compiler recurses over the application spine, so a batch that is too
    # large dies of Python recursion rather than of anything to do with the
    # program.  Chunk rather than raise the limit.
    per_program = max(1, _MAX_PROBES // mod)

    flags: list[bool] = []
    for start in range(0, len(exprs), per_program):
        chunk = exprs[start:start + per_program]
        probes = [
            f'(show (holds (for (x in ({e} : {{{ty}}})) (guard (x == {k})))))'
            for e in chunk for k in range(mod)
        ]
        body = probes[0]
        for probe in probes[1:]:
            body = f"(append {body} {probe})"
        out = evaluate(f"{preamble}main : String\nmain = {body}\n")

        i = 0
        while i < len(out):
            if out.startswith("True", i):
                flags.append(True); i += 4
            elif out.startswith("False", i):
                flags.append(False); i += 5
            else:
                raise AssertionError(f"unreadable probe result: {out!r}")

    assert len(flags) == len(exprs) * mod, (
        f"expected {len(exprs) * mod} probes, got {len(flags)}")
    return [{k for k in range(mod) if flags[n * mod + k]}
            for n in range(len(exprs))]


def _members(set_expr: str, preamble: str = "", mod: int = MOD) -> set[int]:
    return _members_many([set_expr], preamble, mod)[0]


def _lit(xs) -> str:
    return "{" + ", ".join(str(x) for x in sorted(xs)) + "}" if xs else "{}"


def _rand_set(rng: random.Random, mod: int = MOD, hi: int = 5) -> set[int]:
    return {rng.randrange(mod) for _ in range(rng.randrange(hi + 1))}


# ── Set construction and the semilattice operations ──────────────────────────


def test_a_set_literal_denotes_its_python_set():
    """Deduplication and canonical ordering, over random literals.

    A literal used to be built as a bare cons chain in source order, so an
    unsorted one silently misbehaved in every later merge (`fixme.md` F11).
    """
    rng = random.Random(20240804)
    cases = [[rng.randrange(MOD) for _ in range(rng.randrange(7))]
             for _ in range(CASES)]
    lits = ["{" + ", ".join(str(x) for x in xs) + "}" if xs else "{}"
            for xs in cases]
    for xs, lit, got in zip(cases, lits, _members_many(lits)):
        assert got == set(xs), f"literal {lit}"


def test_join_is_union():
    rng = random.Random(20240805)
    cases = [(_rand_set(rng), _rand_set(rng)) for _ in range(CASES)]
    exprs = [f"{_lit(a)} \\/ {_lit(b)}" for a, b in cases]
    for (a, b), got in zip(cases, _members_many(exprs)):
        assert got == a | b, f"{a} \\/ {b}"


def test_join_is_idempotent_commutative_and_associative():
    rng = random.Random(20240806)
    cases = [(_rand_set(rng), _rand_set(rng), _rand_set(rng))
             for _ in range(CASES)]
    exprs = []
    for a, b, c in cases:
        exprs += [f"{_lit(a)} \\/ {_lit(a)}",
                  f"{_lit(a)} \\/ {_lit(b)}",
                  f"{_lit(b)} \\/ {_lit(a)}",
                  f"({_lit(a)} \\/ {_lit(b)}) \\/ {_lit(c)}",
                  f"{_lit(a)} \\/ ({_lit(b)} \\/ {_lit(c)})"]
    got = _members_many(exprs)
    for i, (a, _b, _c) in enumerate(cases):
        idem, ab, ba, lassoc, rassoc = got[5 * i:5 * i + 5]
        assert idem == a, "join is not idempotent"
        assert ab == ba, "join is not commutative"
        assert lassoc == rassoc, "join is not associative"


def test_bottom_is_the_unit_of_join():
    rng = random.Random(20240807)
    cases = [_rand_set(rng) for _ in range(CASES)]
    exprs = [f"{_lit(a)} \\/ {{}}" for a in cases]
    for a, got in zip(cases, _members_many(exprs)):
        assert got == a


# ── Comprehensions ───────────────────────────────────────────────────────────


def test_a_comprehension_over_a_set_is_the_identity():
    rng = random.Random(20240808)
    cases = [_rand_set(rng) for _ in range(CASES)]
    exprs = ["{x | x in " + _lit(a) + "}" for a in cases]
    for a, got in zip(cases, _members_many(exprs)):
        assert got == a


def test_a_guard_filters_like_python():
    rng = random.Random(20240809)
    cases = [(_rand_set(rng), rng.randrange(MOD)) for _ in range(CASES)]
    exprs = ["{x | x in " + _lit(a) + f", x < {k}}}" for a, k in cases]
    for (a, k), got in zip(cases, _members_many(exprs)):
        assert got == {x for x in a if x < k}, f"{a} filtered by < {k}"


def test_two_guards_conjoin_like_python():
    rng = random.Random(20240810)
    cases = [(_rand_set(rng), *sorted((rng.randrange(MOD), rng.randrange(MOD))))
             for _ in range(CASES)]
    exprs = ["{x | x in " + _lit(a) + f", x > {lo}, x < {hi}}}"
             for a, lo, hi in cases]
    for (a, lo, hi), got in zip(cases, _members_many(exprs)):
        assert got == {x for x in a if lo < x < hi}


def test_a_mapped_comprehension_agrees_with_python():
    rng = random.Random(20240811)
    cases = [(_rand_set(rng), rng.randrange(MOD)) for _ in range(CASES)]
    exprs = ["{x + " + str(k) + " | x in " + _lit(a) + "}" for a, k in cases]
    for (a, k), got in zip(cases, _members_many(exprs)):
        assert got == {(x + k) % MOD for x in a}


def test_two_generators_are_the_product():
    """The shape that had never worked.

    `desugar_expr` read `bindings[0]` and dropped every later clause, so
    `for (x in a, y in b)` compiled with `y` unbound — documented syntax
    that no example exercised.  A generator produces it on the first case.
    """
    rng = random.Random(20240813)
    cases = [(_rand_set(rng), _rand_set(rng)) for _ in range(CASES)]
    exprs = ["{x + y | x in " + _lit(a) + ", y in " + _lit(b) + "}"
             for a, b in cases]
    for (a, b), got in zip(cases, _members_many(exprs)):
        assert got == {(x + y) % MOD for x in a for y in b}, f"{a} x {b}"


def test_a_guard_across_two_generators():
    rng = random.Random(20240814)
    cases = [(_rand_set(rng), _rand_set(rng)) for _ in range(CASES)]
    exprs = ["{x | x in " + _lit(a) + ", y in " + _lit(b) + ", x == y}"
             for a, b in cases]
    for (a, b), got in zip(cases, _members_many(exprs)):
        assert got == (a & b), f"{a} & {b}"


def test_a_later_generator_may_mention_an_earlier_binder():
    rng = random.Random(20240815)
    cases = [_rand_set(rng) for _ in range(CASES)]
    exprs = ["{y | x in " + _lit(a) + ", y in {x}}" for a in cases]
    for a, got in zip(cases, _members_many(exprs)):
        assert got == a


# ── The fixed point, against a Python fixed point ────────────────────────────


def test_closure_under_successor_agrees_with_python():
    """`fix` over a whole seeded set, checked against the same fixpoint.

    This is the one that exercises ϕ/δ, `semifix`, ⊥-propagation and change
    minimization at once — a wrong derivative shows up as a wrong set.
    """
    rng = random.Random(20240812)
    cases = [(_rand_set(rng) or {0}, rng.randrange(1, MOD))
             for _ in range(CASES)]

    preamble = ""
    for i, (_seed, cap) in enumerate(cases):
        preamble += (
            f"f{i} : Box (Set (Cyclic {MOD})) -> Set (Cyclic {MOD})\n"
            f"f{i} (Box e) = fix r => e \\/ {{x + 1 | x in r, x < {cap}}}\n\n")
    exprs = [f"f{i} (Box {_lit(seed)})" for i, (seed, _cap) in enumerate(cases)]

    for (seed, cap), got in zip(cases, _members_many(exprs, preamble)):
        want = set(seed)
        while True:
            grown = want | {(x + 1) % MOD for x in want if x < cap}
            if grown == want:
                break
            want = grown
        assert got == want, f"seed={seed} cap={cap}"


# ── The pattern-match compiler, against a direct interpreter ─────────────────
#
# `fixme.md` F29 asks for exactly this: compile a random pattern matrix and
# check the tree agrees with a straightforward matcher.  The matrix is two
# columns of `Maybe Bool`, which is small enough to enumerate completely
# (nine value pairs) and still exercises what the compiler actually does —
# grouping a column by constructor, nesting a sub-pattern, and Wadler's
# mixture rule where a column holds patterns of different kinds.

#: Every `Maybe Bool` value, as (source, python) pairs.
_VALUES = [("Nothing", None), ("(Just True)", True), ("(Just False)", False)]

#: Every pattern over `Maybe Bool`, as (source, python) pairs.  The python
#: side is a predicate on the value.
_PATTERNS = [
    ("_",              lambda v: True),
    ("Nothing",        lambda v: v is None),
    ("(Just _)",       lambda v: v is not None),
    ("(Just True)",    lambda v: v is True),
    ("(Just False)",   lambda v: v is False),
]


def _first_match(rows, va, vb):
    """The index of the first row matching `(va, vb)`, or None."""
    for i, (pa, pb) in enumerate(rows):
        if pa[1](va) and pb[1](vb):
            return i
    return None


def _random_matrix(rng, height):
    return [(rng.choice(_PATTERNS), rng.choice(_PATTERNS))
            for _ in range(height)]


def test_the_match_compiler_agrees_with_a_direct_interpreter():
    """Random pattern matrices, checked at every value.

    A final catch-all row is always appended, so the matrix is exhaustive
    by construction and the compiler's own exhaustiveness check — which
    runs before desugaring — never fires.
    """
    from gestate.pipeline import ExhaustError

    rng = random.Random(20240816)
    checked = 0
    for _ in range(10):
        rows = _random_matrix(rng, rng.randrange(1, 5))
        rows.append((_PATTERNS[0], _PATTERNS[0]))     # catch-all

        eqns = "".join(
            f"f {pa[0]} {pb[0]} = {i}\n" for i, (pa, pb) in enumerate(rows))
        probes = [f"(show (f {sa} {sb}))"
                  for sa, _va in _VALUES for sb, _vb in _VALUES]
        body = probes[0]
        for probe in probes[1:]:
            body = f"(append {body} {probe})"
        src = (f"f : Maybe Bool -> Maybe Bool -> Int\n{eqns}\n"
               f"main : String\nmain = {body}\n")

        try:
            out = evaluate(src)
        except ExhaustError:
            # A redundant row.  Not a failure — but the compiler had better
            # be right about it, so check some row really is unreachable.
            reachable = {_first_match(rows, va, vb)
                         for _sa, va in _VALUES for _sb, vb in _VALUES}
            assert len(reachable) < len(rows), (
                f"rejected as redundant, but every row is reachable:\n{eqns}")
            continue

        got = [int(c) for c in out]
        want = [_first_match(rows, va, vb)
                for _sa, va in _VALUES for _sb, vb in _VALUES]
        assert got == want, f"matrix disagrees with the interpreter:\n{eqns}"
        checked += 1

    assert checked, "every generated matrix was rejected; generator is broken"


def test_a_redundant_row_is_rejected():
    """The converse: a row no value can reach is reported, not compiled."""
    from gestate.pipeline import ExhaustError

    src = ("f : Maybe Bool -> Int\n"
           "f Nothing = 0\n"
           "f (Just _) = 1\n"
           "f (Just True) = 2\n"
           "main : Int\nmain = f Nothing\n")
    with pytest.raises(ExhaustError):
        evaluate(src)
