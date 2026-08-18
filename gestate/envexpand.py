"""`on <points> x`, rewritten into something the audio fragment accepts.

`audio.ges` defines `on : List Envelope -> Float -> Float` by walking a
cons list, which is the definition anybody should read and is the one an
interpreted program runs.  The static audio fragment refuses it — a list is
recursive and has no fixed size — so a synth could not use envelopes at
all, which is the gap `spec/liveaudio.md` describes:

    A constant list read per sample is a **lookup table**: the extractor
    lifts it to a constant array and indexes it, but only once it is
    written as one.

This is that lift, done a stage earlier and without a constant array.  When
the points are known at compile time — a literal list, or a name bound to
one — `on ps x` is replaced by a tree of comparisons over the breakpoints,
which is flat, first-order, non-allocating and total.  Everything else in
the compiler then treats it as ordinary arithmetic.

**Before the engines, deliberately.**  A node kind would have to be taught
to the extractor, the Python block engine and the LLVM back end
separately — three implementations of one rule, which is where a second
implementation of anything puts its bugs.  Rewriting the *expression*
instead means all three see the same thing and cannot disagree.

**Binary, not linear.**  The obvious expansion is a chain — `x < b₁` then
`x < b₂` then … — which is `n` comparisons per sample for `n` points and
runs at audio rate.  This splits at the median breakpoint instead, so a
32-point envelope costs 5 comparisons rather than 32, and the depth grows
with the logarithm of how detailed the curve is rather than with the curve.

**Each leaf is `a + b·x`.**  A `Ramp` segment is
`y₀ + (y₁-y₀)·(x-x₀)/(x₁-x₀)`, whose only variable is `x`; the rest is
constant folded here into one multiply and one add.  A `Step` segment
folds to a constant.
"""

from __future__ import annotations

from .expr import Alter, EAp, ECase, ECon, EGlobal, ELambda, ELet, ENum, EVar
from .expr import Expr, map_children


#: complaint  author, unplaced — fixme.md F158: an envelope in the piece, named by its points and not its line
class EnvelopeError(Exception):
    pass


#: The two names a program calls.  `audio.ges` is the one place either is
#: defined, and each has a readable recursive body there that this rewrite
#: is checked against.
ON = "on"
BEAT_OF = "beatOf"

#: What a `Float` literal looks like after elaboration.  **Both of them**:
#: `2.0` goes through `Floating`'s `fromFloat` and `2` through `Num`'s
#: `fromInteger`, and an integer literal at `Float` is an ordinary thing to
#: write — `Step 0 50` is a tempo mark anybody would type.  Reading only
#: the first meant the rewrite quietly declined on such a program, and the
#: report was the *list* error it exists to prevent.
_FROM_FLOAT = "__Floating_Float_fromFloat__"
_FROM_INT = "__Num_Float_fromInteger__"

_LT = "__Ord_Float_<__"
_ADD = "__Num_Float_+__"
_MUL = "__Num_Float_*__"


# ── Reading the points out of the tree ──────────────────────────────────────


def _float_of(e: Expr):
    """A `Float` literal, or `None` if this is not one.

    Elaboration wraps every fractional literal in a call to `Floating`'s
    `fromFloat`, so the bare `ENum` never appears on its own.
    """
    if isinstance(e, ENum):
        return float(e.n)
    if (isinstance(e, EAp) and isinstance(e.fn, EGlobal)
            and e.fn.name in (_FROM_FLOAT, _FROM_INT)
            and isinstance(e.arg, ENum)):
        return float(e.arg.n)
    return None


def _points_of(e: Expr, cons, globals_):
    """`[(at, is_ramp, value)]` from a constant list, or `None`.

    `None` rather than an error for anything it cannot read: an `on` whose
    points are computed is not a mistake, it is a program this rewrite has
    nothing to say about, and the fragment check will report it in terms of
    the list it actually is.
    """
    step = cons.get("Step")
    ramp = cons.get("Ramp")
    nil = cons.get("Nil")
    cell = cons.get("Cons")
    if None in (step, ramp, nil, cell):
        return None

    # A name bound to a list — `tempo`, `myCurve` — is followed once.  Not
    # recursively: a chain of aliases is not worth the cycle check, and one
    # hop covers every way anybody writes this.
    if isinstance(e, EGlobal):
        e = globals_.get(e.name)
        if e is None:
            return None

    out = []
    while True:
        if not isinstance(e, ECon):
            return None
        if e.tag == nil.tag:
            return out
        if e.tag != cell.tag or len(e.args) != 2:
            return None
        head, e = e.args[0], e.args[1]
        if not isinstance(head, ECon) or len(head.args) != 2:
            return None
        if head.tag not in (step.tag, ramp.tag):
            return None
        at, value = _float_of(head.args[0]), _float_of(head.args[1])
        if at is None or value is None:
            return None
        out.append((at, head.tag == ramp.tag, value))


# ── Building the tree ───────────────────────────────────────────────────────


def _lit(x: float) -> Expr:
    return EAp(EGlobal(_FROM_FLOAT), ENum(float(x)))


def _affine(a: float, b: float, var: str) -> Expr:
    """`a + b·x`, with `b == 0` folded to the constant it is."""
    if b == 0.0:
        return _lit(a)
    scaled = EAp(EAp(EGlobal(_MUL), _lit(b)), EVar(var))
    if a == 0.0:
        return scaled
    return EAp(EAp(EGlobal(_ADD), _lit(a)), scaled)


def _segment(points, i: int, var: str) -> Expr:
    """What the envelope reads on leaf `i`.

    There are **n+1 leaves for n points**, which is the thing to get right:
    the tree is an insertion search, so a value can land before the first
    breakpoint, between two of them, or past the last.

      * `i == 0` — before the first point; it holds the first value.
      * `0 < i < n` — between points `i-1` and `i`.  A `Ramp` interpolates
        across it; a `Step` holds the earlier value, because a step says
        what happens *at* its own point and nothing about the approach.
      * `i == n` — past the last point; it holds the last value.

    The clamped ends are not an edge case to tidy away.  This function's
    argument is nearly always a clock, and a clock runs past the end of
    every envelope written for it — without the `i == n` leaf the last
    segment's straight line simply continues, so an envelope that ended at
    1.0 reads 2.2 a few beats later.
    """
    if i == 0:
        return _lit(points[0][2])
    if i >= len(points):
        return _lit(points[-1][2])
    prev_at, _prev_ramp, prev_value = points[i - 1]
    at, is_ramp, value = points[i]
    if not is_ramp or at == prev_at:
        return _lit(prev_value)
    slope = (value - prev_value) / (at - prev_at)
    return _affine(prev_value - slope * prev_at, slope, var)


def _tree(points, lo: int, hi: int, var: str, cons) -> Expr:
    """A balanced search for which leaf `x` falls in, over `[lo, hi]`.

    Inclusive at both ends, and the leaf indices run `0..len(points)` — so
    the tree is over the `len(points)` breakpoints and answers with one of
    `len(points) + 1` outcomes, which is what a search for an insertion
    point does.

    `x < points[mid][0]` sends the search left.  **Strict**, so a point's
    own value is what is read at it: `Step 8 0.25` means the envelope is
    0.25 at exactly 8, which is what `tempo.value_on` does and what this is
    checked against.
    """
    if lo >= hi:
        return _segment(points, lo, var)
    mid = (lo + hi) // 2
    test = EAp(EAp(EGlobal(_LT), EVar(var)), _lit(points[mid][0]))
    return ECase(test, [
        Alter(cons["True"].tag, [], _tree(points, lo, mid, var, cons)),
        Alter(cons["False"].tag, [], _tree(points, mid + 1, hi, var, cons)),
    ])


def _quadratic(a: float, b: float, c: float, var: str) -> Expr:
    """`a + b·t + c·t²`, with the degenerate cases folded away."""
    if c == 0.0:
        return _affine(a, b, var)
    square = EAp(EAp(EGlobal(_MUL), EVar(var)), EVar(var))
    term = EAp(EAp(EGlobal(_MUL), _lit(c)), square)
    if b != 0.0:
        term = EAp(EAp(EGlobal(_ADD), term),
                   EAp(EAp(EGlobal(_MUL), _lit(b)), EVar(var)))
    if a == 0.0:
        return term
    return EAp(EAp(EGlobal(_ADD), _lit(a)), term)


def _beat_leaf(env, i: int, var: str) -> Expr:
    """The beat clock on segment `i`, as a polynomial in `t`.

    `beat = b₀ + s·(t-T) + d·(t-T)²` where `T` is where the segment starts,
    `s` the tempo in beats per second and `d` half its slope.  Expanded in
    `t` so the leaf is three constants and no subtraction: the shift by `T`
    is a compile-time fact and has no business in a per-sample loop.
    """
    T = env.ts[i]
    s = env.bpms[i] / 60.0
    d = env.ks[i] / 120.0
    return _quadratic(env.beats[i] - s * T + d * T * T, s - 2.0 * d * T, d, var)


def _beat_tree(env, lo: int, hi: int, var: str, cons) -> Expr:
    """Which segment `t` falls in, over `[lo, hi]` inclusive.

    The breakpoints are the segment *start times*, and segment `i` owns
    `ts[i] <= t < ts[i+1]`.  `ts[0]` is always 0 — `tempo.envelope` inserts
    a segment at the origin when the first tempo mark is not there — so
    there is no "before the envelope" leaf to write: segment 0 already
    covers everything below the first real mark, at the tempo held there.
    """
    if lo >= hi:
        return _beat_leaf(env, lo, var)
    mid = (lo + hi + 1) // 2
    test = EAp(EAp(EGlobal(_LT), EVar(var)), _lit(env.ts[mid]))
    return ECase(test, [
        Alter(cons["True"].tag, [], _beat_tree(env, lo, mid - 1, var, cons)),
        Alter(cons["False"].tag, [], _beat_tree(env, mid, hi, var, cons)),
    ])


def _expanded_beat(points, arg: Expr, cons, fresh) -> Expr:
    """`let t = <arg> in <tree>` for `beatOf`, or `None` to decline.

    The derivation — trapezoid segment durations, slopes, and where each
    segment starts in seconds — is `tempo.envelope`'s, reused rather than
    written twice.  It is the same function the *schedule* is built with,
    so a note's instant and the beat clock the synth reads cannot come from
    two different readings of one tempo.
    """
    from .tempo import TempoError, envelope

    try:
        env = envelope(points)
    except TempoError:
        return None                 # a tempo this cannot make sense of
    var = fresh()
    return ELet(False, [(var, arg)],
                _beat_tree(env, 0, len(env.ts) - 1, var, cons))


def _expanded(points, arg: Expr, cons, fresh) -> Expr:
    """`let x = <arg> in <tree>` — the whole rewrite for one call.

    **`let`, so the argument is evaluated once.**  It appears in every leaf
    of the tree, and a `beat` or an oscillator phase is not something to
    recompute per comparison.  Only one branch runs, so duplicating it
    would be correct and wasteful; binding it is neither.
    """
    if not points:
        return _lit(0.0)
    var = fresh()
    return ELet(False, [(var, arg)],
                _tree(points, 0, len(points), var, cons))


# ── The pass ────────────────────────────────────────────────────────────────


def expand(scs, cons):
    """Rewrite every readable `on ps x` in `scs`.  Returns new `scs`.

    Untouched when `on` is not defined, not applied to two arguments, or
    applied to points this cannot read — in every one of those cases the
    program means what it said, and the fragment check will say so about
    the list rather than about a rewrite that declined to happen.
    """
    if "Step" not in cons or "Cons" not in cons:
        return scs

    constants = {name: lam.body for name, arity, lam, _sig in scs
                 if arity == 0 and isinstance(lam, ELambda)}
    counter = [0]

    def fresh():
        counter[0] += 1
        return f"__on{counter[0]}__"

    def go(e: Expr) -> Expr:
        # `on ps x` is two applications deep: `EAp(EAp(on, ps), x)`.
        if (isinstance(e, EAp) and isinstance(e.fn, EAp)
                and isinstance(e.fn.fn, EGlobal)
                and e.fn.fn.name in (ON, BEAT_OF)):
            points = _points_of(e.fn.arg, cons, constants)
            if points is not None:
                if e.fn.fn.name == ON:
                    return _expanded(points, go(e.arg), cons, fresh)
                built = _expanded_beat(points, go(e.arg), cons, fresh)
                if built is not None:
                    return built
        return map_children(e, go)

    out = []
    for name, arity, lam, sig in scs:
        # `map_children` and not a hand-written rebuild: it is driven by
        # the dataclass fields, so it carries through the binder flavours
        # and type annotations inference left behind — which a rebuilder
        # naming only the fields it knows about would silently drop.
        out.append((name, arity, map_children(lam, go), sig))
    return out
